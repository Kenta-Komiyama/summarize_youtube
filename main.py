# main.py — 直近24hの新着を対象。字幕が取れなければ Whisper にフォールバック。
# Bot判定 / フォーマット未提供 / 字幕失敗 に強化版

import os, json, time, yaml, tempfile, traceback
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

# =========================
# 共通 yt_dlp 強化設定
# =========================
def _pick_cookies_from_browser():
    env_browser = os.environ.get("YTDLP_COOKIES_FROM_BROWSER")
    if env_browser:
        return (env_browser,)

    # ローカル実行時の救済: 明示指定がなくても主要ブラウザを順に試す
    for browser in ("chrome", "edge", "firefox", "safari"):
        try:
            import yt_dlp
            with yt_dlp.YoutubeDL({"quiet": True, "cookiesfrombrowser": (browser,)}) as ydl:
                ydl.cookiejar  # 読み込みトリガー
            return (browser,)
        except Exception:
            continue

    return None


def build_ydl_opts(base_opts=None):
    opts = base_opts.copy() if base_opts else {}

    opts.update({
        "retries": 5,
        "fragment_retries": 5,
        "sleep_interval": 1,
        "max_sleep_interval": 5,
        "concurrent_fragment_downloads": 1,
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            )
        },
        "extractor_args": {
            "youtube": {
                "player_client": ["tv_embedded", "android", "ios"]
            }
        }
    })

    if Path("cookies.txt").exists():
        opts["cookiefile"] = "cookies.txt"
    else:
        browser_tuple = _pick_cookies_from_browser()
        if browser_tuple:
            opts["cookiesfrombrowser"] = browser_tuple

    return opts


def load_state():
    if not STATE_PATH.exists():
        return {"processed": []}
    return json.loads(STATE_PATH.read_text(encoding="utf-8"))

def save_state(state):
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

def parse_rfc3339(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))

# =========================
# Whisper用 音声DL（強化版）
# =========================
def download_audio_for_whisper(video_id: str, out_dir: str) -> str:
    import subprocess, yt_dlp

    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    url = f"https://www.youtube.com/watch?v={video_id}"
    base_tmpl = str(out_path / f"{video_id}.%(ext)s")

    ydl_opts = build_ydl_opts({
        "format": "bestaudio/best",
        "outtmpl": base_tmpl,
        "quiet": True,
        "noplaylist": True,
        "ignore_no_formats_error": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    })

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        print(f"[WARN] yt_dlp error: {e}")

    mp3_path = out_path / f"{video_id}.mp3"
    if mp3_path.exists() and mp3_path.stat().st_size > 0:
        return str(mp3_path)

    # 代替ファイル探索（.part除外）
    cand = None
    files = [p for p in out_path.glob(f"{video_id}.*") if not str(p).endswith(".part")]
    files = sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)

    for p in files:
        if p.suffix.lower() in (".webm", ".m4a", ".mp4", ".opus", ".wav"):
            cand = p
            break

    if cand:
        mp3_tmp = out_path / f"{video_id}.mp3"
        try:
            subprocess.run(
                ["ffmpeg", "-y", "-i", str(cand), "-vn",
                 "-acodec", "libmp3lame", "-ab", "192k", str(mp3_tmp)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            if mp3_tmp.exists() and mp3_tmp.stat().st_size > 0:
                return str(mp3_tmp)
        except Exception as e:
            print(f"[WARN] ffmpeg transcode failed: {e}")

    raise FileNotFoundError(
        f"音声取得失敗（video_id={video_id}）。Bot判定・Cookie・地域/年齢制限を確認してください。"
    )


def transcribe_with_whisper(video_id: str) -> str:
    from openai import OpenAI

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY 未設定")

    client = OpenAI(api_key=api_key)

    with tempfile.TemporaryDirectory() as td:
        mp3_path = download_audio_for_whisper(video_id, td)
        with open(mp3_path, "rb") as f:
            tr = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                response_format="text",
            )
        return tr if isinstance(tr, str) else str(tr)


# =========================
# メイン処理
# =========================
def main():
    yt = build_yt(os.environ["YOUTUBE_API_KEY"])
    state = load_state()
    processed = set(state.get("processed", []))
    all_candidates = []

    print(f"[INFO] STRICT={STRICT} IGNORE_STATE_24H={IGNORE_STATE_24H}")

    channel_ids = []
    for ch in CHANNELS:
        try:
            cid = resolve_channel_id(yt, ch)
            channel_ids.append(cid)
        except Exception as e:
            print(f"[WARN] resolve failed: {ch} -> {e}")

    for cid in channel_ids:
        try:
            uploads = get_uploads_playlist_id(yt, cid)
            vids = list_recent_videos(yt, uploads, max_results=50)
            all_candidates.extend(vids)
            time.sleep(0.2)
        except Exception as e:
            print(f"[WARN] list videos failed for {cid}: {e}")

    uniq = {v["video_id"]: v for v in all_candidates}
    videos = sorted(uniq.values(), key=lambda x: x["published_at"], reverse=True)

    now_utc = datetime.now(timezone.utc)
    cutoff = now_utc - timedelta(hours=24)
    videos = [v for v in videos if parse_rfc3339(v["published_at"]) >= cutoff]

    created_files = []

    for v in videos:
        vid = v["video_id"]

        if (not IGNORE_STATE_24H) and vid in processed:
            continue

        print(f"\n[INFO] Processing: {v['title']} ({vid})")

        try:
            segs = fetch_subtitles_via_ytdlp_robust(vid, langs=['ja','en'])
            if segs and any(s.get('text') for s in segs):
                transcript_text = "\n".join(s.get("text","") for s in segs if s.get("text"))
            else:
                if STRICT:
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

            time.sleep(0.8)

        except Exception as e:
            print(f"[WARN] failed: {vid} -> {e}")
            traceback.print_exc()
            continue

    state["processed"] = sorted(processed)
    save_state(state)

    from zipfile import ZipFile
    subject = f"[YouTube要約] 24h内 {len(created_files)}件更新"

    if not created_files:
        send_mail(subject, body_text="直近24時間の新規要約はありませんでした。", attachments=None)
    else:
        tmp_zip = Path("out_latest_run.zip")
        with ZipFile(tmp_zip, "w") as z:
            for p in created_files:
                z.write(p, arcname=p.name)

        lines = [f"- {p.stem}" for p in created_files]
        body = "今回生成した要約:\n\n" + "\n".join(lines)

        send_mail(subject, body_text=body, attachments=[str(tmp_zip)])

    print(f"\n[DONE] summarized {len(created_files)} video(s).")


if __name__ == "__main__":
    main()
