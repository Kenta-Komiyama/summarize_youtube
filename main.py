# main.py
# - 直近24時間以内に公開された動画すべてを要約（本数制限なし）
# - 字幕は yt_dlp で取得。無ければ Whisper にフォールバック
# - 要約は gpt-5-mini
# - 生成MDを out/ に保存し、今回分をZIP添付してGmail送信
# - 処理済み videoId は state.json に記録（重複防止）

import os
import json
import time
import yaml
import tempfile
import traceback
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path

from yt_api import build_yt, resolve_channel_id, get_uploads_playlist_id, list_recent_videos
from subs import fetch_subtitles_via_ytdlp_robust
from summarize import summarize
from mailer import send_mail

OPENAI_API_KEY  = os.environ["OPENAI_API_KEY"]
YOUTUBE_API_KEY = os.environ["YOUTUBE_API_KEY"]

CONFIG = yaml.safe_load(Path("config.yaml").read_text(encoding="utf-8"))
LANG   = CONFIG.get("lang", "ja")
STRICT = bool(CONFIG.get("strict_captions_only", False))
CHANNELS = CONFIG["channels"]

STATE_PATH = Path("state.json")
OUT_DIR = Path("out")
OUT_DIR.mkdir(exist_ok=True)

def load_state():
    if not STATE_PATH.exists():
        return {"processed": []}
    return json.loads(STATE_PATH.read_text(encoding="utf-8"))

def save_state(state):
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

def parse_rfc3339(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))

def transcribe_with_whisper(video_id: str) -> str:
    from subs import Path as _Path, yt_dlp
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)

    def download_audio_for_whisper(video_id: str, out_dir: str) -> str:
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": str(_Path(out_dir)/f"{video_id}.%(ext)s"),
            "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "128"}],
            "quiet": True, "no_warnings": True,
        }
        url = f"https://www.youtube.com/watch?v={video_id}"
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(url, download=True)
        return str(_Path(out_dir)/f"{video_id}.mp3")

    with tempfile.TemporaryDirectory() as td:
        mp3 = download_audio_for_whisper(video_id, td)
        with open(mp3, "rb") as f:
            tr = client.audio.transcriptions.create(model="whisper-1", file=f, response_format="text")
        return tr if isinstance(tr, str) else str(tr)

def main():
    yt = build_yt(YOUTUBE_API_KEY)
    state = load_state()
    processed = set(state.get("processed", []))
    all_candidates = []

    # 1) チャンネル解決
    channel_ids = []
    for ch in CHANNELS:
        try:
            cid = resolve_channel_id(yt, ch)
            channel_ids.append(cid)
        except Exception as e:
            print(f"[WARN] resolve failed: {ch} -> {e}")

    # 2) 新着候補収集（件数制限なし、最大50件）
    for cid in channel_ids:
        try:
            uploads = get_uploads_playlist_id(yt, cid)
            vids = list_recent_videos(yt, uploads, max_results=50)
            all_candidates.extend(vids)
            time.sleep(0.2)
        except Exception as e:
            print(f"[WARN] list videos failed for {cid}: {e}")

    # 3) 重複除去 & 公開日の新しい順
    uniq = {v["video_id"]: v for v in all_candidates}
    videos = sorted(uniq.values(), key=lambda x: x["published_at"], reverse=True)

    # 4) 直近24時間フィルタ
    now_utc = datetime.now(timezone.utc)
    cutoff = now_utc - timedelta(hours=24)
    videos = [v for v in videos if parse_rfc3339(v["published_at"]) >= cutoff]
    print(f"[INFO] Filtering to last 24h. cutoff(UTC)={cutoff.isoformat()}  candidates={len(videos)}")

    # 5) 処理ループ（制限なし）
    created_files: list[Path] = []

    for v in videos:
        vid = v["video_id"]
        if vid in processed:
            continue

        print(f"\n[INFO] Processing: {v['title']} ({vid}) publishedAt={v['published_at']}")
        try:
            segs = fetch_subtitles_via_ytdlp_robust(vid, langs=['ja','en'])
            if segs:
                transcript_text = "\n".join(s.get("text","") for s in segs if s.get("text"))
            else:
                if STRICT:
                    print("[SKIP] no captions & STRICT_CAPTIONS_ONLY=True")
                    processed.add(vid)
                    continue
                transcript_text = transcribe_with_whisper(vid)

            summary_md = summarize(v, transcript_text, lang=LANG)

            safe_title = "".join(c for c in v["title"] if c not in '\\/:*?"<>|').strip()[:80]
            out_path = OUT_DIR / f"{v['published_at'][:10]}_{safe_title}_{vid}.md"
            out_md = (
                f"# {v['title']}\n\n"
                f"- Channel: {v['channel_title']}\n"
                f"- Published: {v['published_at']}\n"
                f"- URL: https://www.youtube.com/watch?v={vid}\n\n"
                f"---\n\n{summary_md}\n"
            )
            out_path.write_text(out_md, encoding="utf-8")
            created_files.append(out_path)

            processed.add(vid)
            time.sleep(1.0)

        except Exception as e:
            print(f"[WARN] failed: {vid} -> {e}")
            traceback.print_exc()
            continue

    state["processed"] = sorted(processed)
    save_state(state)

    # 6) メール送信
    subject = f"[YouTube要約] 24h内 {len(created_files)}件更新"
    if not created_files:
        body = "直近24時間に新規で要約対象となる動画はありませんでした。"
        send_mail(subject, body_text=body, attachments=None)
    else:
        tmp_zip = Path("out_latest_run.zip")
        with tempfile.TemporaryDirectory() as td:
            staging = Path(td) / "latest"
            staging.mkdir(parents=True, exist_ok=True)
            for p in created_files:
                shutil.copy2(p, staging / p.name)
            shutil.make_archive(base_name=tmp_zip.stem, format="zip", root_dir=td, base_dir="latest")

        lines = [f"- {p.stem}  https://www.youtube.com/watch?v={p.stem.split('_')[-1]}" for p in created_files]
        body = "今回（直近24時間）生成した要約ファイル一覧:\n\n" + "\n".join(lines)

        send_mail(subject, body_text=body, attachments=[str(tmp_zip)])

    print(f"\n[DONE] summarized {len(created_files)} video(s) within last 24h. Email sent.")

if __name__ == "__main__":
    main()
