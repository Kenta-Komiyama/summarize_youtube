# main.py — 24h内を対象、必要に応じてstate無視、スキップ理由を詳細ログ
import os, json, time, yaml, tempfile, traceback, shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path

from yt_api import build_yt, resolve_channel_id, get_uploads_playlist_id, list_recent_videos
from subs import fetch_subtitles_via_ytdlp_robust
from summarize import summarize
from mailer import send_mail

CONFIG = yaml.safe_load(Path("config.yaml").read_text(encoding="utf-8"))
LANG   = CONFIG.get("lang", "ja")
STRICT = bool(CONFIG.get("strict_captions_only", False))
CHANNELS = CONFIG["channels"]
IGNORE_STATE_24H = bool(CONFIG.get("ignore_state_within_24h", False))

STATE_PATH = Path("state.json")
OUT_DIR = Path("out"); OUT_DIR.mkdir(exist_ok=True)

def load_state():
    if not STATE_PATH.exists():
        return {"processed": []}
    return json.loads(STATE_PATH.read_text(encoding="utf-8"))

def save_state(state):
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

def parse_rfc3339(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))

def transcribe_with_whisper(video_id: str) -> str:
    # 音声DL→Whisper
    from subs import Path as _Path, yt_dlp
    from openai import OpenAI
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    def download_audio_for_whisper(video_id: str, out_dir: str) -> str:
        ydl_opts = {
            "skip_download": True,                 # 本体は落とさない
            "writesubtitles": True,
            "writeautomaticsub": auto,             # ここは既存ロジックの変数
            "subtitleslangs": [lang],              # 1言語ずつ
            "subtitlesformat": "vtt" if fmt == "vtt" else "json3",
        
            # 🔧 フォーマット解決まわり（ここが重要）
            "format": "best[ext=mp4]/best/bestaudio/bestvideo",  # なるべく何か1つ見つかればOK
            "ignore_no_formats_error": True,       # ← フォーマットが見つからなくても処理を続行
            "simulate": True,                      # 実DLはしない（メタと字幕取得に集中）
            "noplaylist": True,
        
            # ネットワーク/リトライ
            "retries": 3,
            "fragment_retries": 3,
            "ratelimit": 5_000_000,
            "throttledratelimit": 1_000_000,
        
            # ヘッダ/クライアント
            "http_headers": {
                "User-Agent": ua,
                "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
            },
            "extractor_args": {
                "youtube": {
                    "player_client": clients  # ["android"] / ["web"] / ["ios"]
                }
            },
        
            # ログ抑制
            "quiet": True,
            "no_warnings": True,
        }
        if cookies_path:
            ydl_opts["cookiefile"] = cookies_path
        if http_proxy:
            ydl_opts["proxy"] = http_proxy
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
    yt = build_yt(os.environ["YOUTUBE_API_KEY"])
    state = load_state()
    processed = set(state.get("processed", []))
    all_candidates = []

    print(f"[INFO] STRICT_CAPTIONS_ONLY={STRICT}  IGNORE_STATE_24H={IGNORE_STATE_24H}")
    print(f"[INFO] processed(len) in state.json = {len(processed)}")

    # 1) チャンネル解決
    channel_ids = []
    for ch in CHANNELS:
        try:
            cid = resolve_channel_id(yt, ch); channel_ids.append(cid)
        except Exception as e:
            print(f"[WARN] resolve failed: {ch} -> {e}")

    # 2) 候補収集（各ch最大50件）
    for cid in channel_ids:
        try:
            uploads = get_uploads_playlist_id(yt, cid)
            vids = list_recent_videos(yt, uploads, max_results=50)
            all_candidates.extend(vids)
            time.sleep(0.2)
        except Exception as e:
            print(f"[WARN] list videos failed for {cid}: {e}")

    # 3) 重複除去 & 新しい順
    uniq = {v["video_id"]: v for v in all_candidates}
    videos = sorted(uniq.values(), key=lambda x: x["published_at"], reverse=True)

    # 4) 24hフィルタ（UTC）
    now_utc = datetime.now(timezone.utc)
    cutoff = now_utc - timedelta(hours=24)
    videos = [v for v in videos if parse_rfc3339(v["published_at"]) >= cutoff]
    print(f"[INFO] Filtering to last 24h. cutoff(UTC)={cutoff.isoformat()}  candidates={len(videos)}")

    created_files = []

    for v in videos:
        vid = v["video_id"]
        pub = v["published_at"]

        # stateの扱い
        if (not IGNORE_STATE_24H) and vid in processed:
            print(f"[SKIP] already processed (state.json): {vid}  {v['title']}")
            continue
        if IGNORE_STATE_24H and vid in processed:
            print(f"[INFO] ignoring state (24h mode): will reprocess {vid}")

        print(f"\n[INFO] Processing: {v['title']} ({vid}) publishedAt={pub}")

        try:
            # 5-1) 字幕（強化版）
            segs = fetch_subtitles_via_ytdlp_robust(vid, langs=['ja','en'])
            if segs and any(s.get('text') for s in segs):
                transcript_text = "\n".join(s.get("text","") for s in segs if s.get("text"))
                print(f"[OK] subtitles collected: chars={len(transcript_text)}")
            else:
                print(f"[INFO] no subtitles via yt_dlp")
                if STRICT:
                    print("[SKIP] STRICT_CAPTIONS_ONLY=True → whisper未使用でスキップ")
                    # STRICTのときも敢えて既読にしない方がデバッグしやすい
                    # processed.add(vid)  # ←必要なら有効化
                    continue
                print("[INFO] fallback to Whisper…")
                transcript_text = transcribe_with_whisper(vid)
                print(f"[OK] whisper transcript: chars={len(transcript_text)}")

            # 5-2) 要約
            summary_md = summarize(v, transcript_text, lang=LANG)

            # 5-3) 保存
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
            time.sleep(0.8)

        except Exception as e:
            print(f"[WARN] failed: {vid} -> {e}")
            traceback.print_exc()
            # 失敗時は processed に入れない（次回再挑戦）
            continue

    # 6) state保存
    state["processed"] = sorted(processed)
    save_state(state)

    # 7) メール送信
    from zipfile import ZipFile
    subject = f"[YouTube要約] 24h内 {len(created_files)}件更新"
    if not created_files:
        send_mail(subject, body_text="直近24時間の新規要約はありませんでした。", attachments=None)
    else:
        tmp_zip = Path("out_latest_run.zip")
        with ZipFile(tmp_zip, "w") as z:
            for p in created_files:
                z.write(p, arcname=p.name)
        lines = [f"- {p.stem}  https://www.youtube.com/watch?v={p.stem.split('_')[-1]}" for p in created_files]
        body = "今回（直近24時間）生成した要約ファイル一覧:\n\n" + "\n".join(lines)
        send_mail(subject, body_text=body, attachments=[str(tmp_zip)])

    print(f"\n[DONE] summarized {len(created_files)} video(s) within last 24h. Email sent.")

if __name__ == "__main__":
    main()
