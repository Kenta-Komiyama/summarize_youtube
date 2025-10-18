# main.py — 直近24hの新着を対象。字幕が取れなければ Whisper にフォールバック。
# - フォーマット未提供やBot判定による失敗に強い
# - mp3未生成時は実ファイルを検出して ffmpeg で手動変換
# 前提:
#   - OPENAI_API_KEY, YOUTUBE_API_KEY を環境変数で設定
#   - GitHub Actions 等では 'sudo apt-get install -y ffmpeg' を実行しておく
#   - cookies.txt (任意) があればルート直下に置くと自動使用

import os, json, time, yaml, tempfile, traceback
from datetime import datetime, timezone, timedelta
from pathlib import Path

from yt_api import build_yt, resolve_channel_id, get_uploads_playlist_id, list_recent_videos
from subs import fetch_subtitles_via_ytdlp_robust
from summarize import summarize
from mailer import send_mail

CONFIG = yaml.safe_load(Path("config.yaml").read_text(encoding="utf-8"))
LANG   = CONFIG.get("lang", "ja")
STRICT = bool(CONFIG.get("strict_captions_only", False))       # Trueだと字幕なしはスキップ
CHANNELS = CONFIG["channels"]
IGNORE_STATE_24H = bool(CONFIG.get("ignore_state_within_24h", False))  # Trueなら24h内はstate無視で再処理

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

# ---------- Whisper用: 音声DL（堅牢版） ----------
def download_audio_for_whisper(video_id: str, out_dir: str) -> str:
    """
    YouTubeから音声を取得して mp3 を返す。
    - まず yt_dlp + FFmpegExtractAudio で mp3化を試みる
    - mp3ができなければ、落ちた実ファイルを検出して ffmpeg で手動変換
    - それでも無ければ FileNotFoundError
    """
    from pathlib import Path
    import subprocess, yt_dlp

    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    url = f"https://www.youtube.com/watch?v={video_id}"
    base_tmpl = str(out_path / f"{video_id}.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": base_tmpl,                 # まずは元拡張子で保存
        "quiet": True,
        "noplaylist": True,
        "ignore_no_formats_error": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    }
    if Path("cookies.txt").exists():
        ydl_opts["cookiefile"] = "cookies.txt"

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except yt_dlp.utils.DownloadError as e:
        print(f"[WARN] yt_dlp download error: {e}")

    # 2) mp3 ができていれば返す
    mp3_path = out_path / f"{video_id}.mp3"
    if mp3_path.exists() and mp3_path.stat().st_size > 0:
        return str(mp3_path)

    # 3) 代替: 落ちた実ファイルを検出して手動で mp3 変換
    cand = None
    for ext in ("webm", "m4a", "mp4", "opus", "wav"):
        p = out_path / f"{video_id}.{ext}"
        if p.exists() and p.stat().st_size > 0:
            cand = p
            break
    if not cand:
        files = sorted(out_path.glob(f"{video_id}.*"), key=lambda x: x.stat().st_mtime, reverse=True)
        if files:
            cand = files[0]

    if cand:
        mp3_tmp = out_path / f"{video_id}.mp3"
        try:
            subprocess.run(
                ["ffmpeg", "-y", "-i", str(cand), "-vn", "-acodec", "libmp3lame", "-ab", "192k", str(mp3_tmp)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            if mp3_tmp.exists() and mp3_tmp.stat().st_size > 0:
                return str(mp3_tmp)
        except FileNotFoundError:
            raise RuntimeError("ffmpeg が見つかりません。CIでは apt-get install -y ffmpeg を追加してください。")
        except subprocess.CalledProcessError as e:
            print(f"[WARN] ffmpeg transcode failed: {e}")

    # 4) ここまでで無理なら音声取得失敗
    raise FileNotFoundError(
        f"音声取得/変換に失敗（video_id={video_id}）。cookies.txtの適用、Bot判定、地域/年齢制限、フォーマット提供状況を確認してください。"
    )

def transcribe_with_whisper(video_id: str) -> str:
    """
    音声をダウンロードして Whisper API で文字起こし。
    OPENAI_API_KEY 必須。返り値はプレーンテキスト。
    """
    from openai import OpenAI

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY が設定されていません。Whisperを使うには必須です。")

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

# --------------- メイン処理 ---------------
def main():
    yt = build_yt(os.environ["YOUTUBE_API_KEY"])
    state = load_state()
    processed = set(state.get("processed", []))
    all_candidates = []

    print(f"[INFO] STRICT_CAPTIONS_ONLY={STRICT}  IGNORE_STATE_24H={IGNORE_STATE_24H}")
    print(f"[INFO] processed(len) in state.json = {len(processed)}")

    # 1) チャンネル解決（可能なら UC… で config.yaml に固定して search.list を避ける）
    channel_ids = []
    for ch in CHANNELS:
        try:
            cid = resolve_channel_id(yt, ch)
            channel_ids.append(cid)
        except Exception as e:
            print(f"[WARN] resolve failed: {ch} -> {e}")

    # 2) 候補収集（各ch 最大50件）
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

    # 4) 直近24hフィルタ（UTC）
    now_utc = datetime.now(timezone.utc)
    cutoff = now_utc - timedelta(hours=24)
    videos = [v for v in videos if parse_rfc3339(v["published_at"]) >= cutoff]
    print(f"[INFO] Filtering to last 24h. cutoff(UTC)={cutoff.isoformat()}  candidates={len(videos)}")

    created_files = []

    # 5) 各動画処理
    for v in videos:
        vid = v["video_id"]
        pub = v["published_at"]

        # state の扱い
        if (not IGNORE_STATE_24H) and vid in processed:
            print(f"[SKIP] already processed (state.json): {vid}  {v['title']}")
            continue
        if IGNORE_STATE_24H and vid in processed:
            print(f"[INFO] ignoring state (24h mode): will reprocess {vid}")

        print(f"\n[INFO] Processing: {v['title']} ({vid}) publishedAt={pub}")

        try:
            # 5-1) 字幕（yt_dlpを多段で試行する実装を subs.py に委譲）
            segs = fetch_subtitles_via_ytdlp_robust(vid, langs=['ja','en'])
            if segs and any(s.get('text') for s in segs):
                transcript_text = "\n".join(s.get("text","") for s in segs if s.get("text"))
                print(f"[OK] subtitles collected: chars={len(transcript_text)}")
            else:
                print(f"[INFO] no subtitles via yt_dlp")
                if STRICT:
                    print("[SKIP] STRICT_CAPTIONS_ONLY=True → whisper未使用でスキップ")
                    continue
                print("[INFO] fallback to Whisper…")
                transcript_text = transcribe_with_whisper(vid)
                print(f"[OK] whisper transcript: chars={len(transcript_text)}")

            # 5-2) 要約生成
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
