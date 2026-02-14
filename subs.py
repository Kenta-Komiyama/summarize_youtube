# subs.py
# 強化版: 429/取りこぼし対策・クライアント/UA/フォーマット/モードを多段で切替
# 変更点:
# - 保存字幕ファイルの探索を「glob固定」から「ディレクトリ全探索」に変更（拡張子揺れに強い）
# - cookies.txt に加え cookies-from-browser を環境変数で使用可能に
# - retries / backoff / 安全なsleep を整理
# - auto/manual の書き出し指定を明確化（writesubtitles + writeautomaticsub）
# - .part を除外

import os
import re
import time
import random
import tempfile
from pathlib import Path
import yt_dlp

# まずは日本語→英語系を優先。必要なら追加してOK
SUB_LANGS_ORDERED = ["ja", "ja-JP", "en", "en-US", "en-GB"]

# 代表的な UA をローテーション（やりすぎると逆効果の環境もあるので 3つ程度に留める）
_UA_POOL = [
    # Android Chrome
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Mobile Safari/537.36",
    # Windows Chrome
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    # iPhone Safari
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
]

# YouTube の内部クライアント指定を切替（yt-dlp の extractor_args）
_CLIENT_CANDIDATES = [
    ["android"],  # まず android
    ["web"],      # ダメなら web
    ["ios"],      # さらに ios
]

# 429 に強い指数バックオフ
def _sleep_backoff(base: float, attempt: int):
    wait = base * (2 ** attempt) + random.uniform(0.0, 1.2)
    wait = min(wait, 20.0)
    time.sleep(wait)

def _vtt_to_segments(vtt_path: Path):
    lines = vtt_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    segs, buf, start, dur = [], [], 0.0, 0.0
    ts_re = re.compile(r"(\d+:\d{2}:\d{2}\.\d{3})\s-->\s(\d+:\d{2}:\d{2}\.\d{3})")

    def to_sec(ts):
        h, m, s = ts.split(":")
        return int(h) * 3600 + int(m) * 60 + float(s)

    for ln in lines:
        m = ts_re.search(ln)
        if m:
            if buf:
                segs.append({"text": " ".join(buf).strip(), "start": start, "duration": dur})
                buf = []
            start = to_sec(m.group(1))
            end = to_sec(m.group(2))
            dur = max(0.0, end - start)
        else:
            if ln and not ln.startswith(("WEBVTT", "NOTE")):
                txt = re.sub(r"<[^>]+>", "", ln)
                if txt.strip():
                    buf.append(txt.strip())

    if buf:
        segs.append({"text": " ".join(buf).strip(), "start": start, "duration": dur})
    return segs

def _json3_to_segments(json_path: Path):
    # json3/srv3 は JSON 構造が揺れるので保守的に吸い上げる
    import json
    data = json.loads(json_path.read_text(encoding="utf-8", errors="ignore"))
    segs = []

    events = data.get("events") or []
    for ev in events:
        if not ev:
            continue

        text = ""
        if "segs" in ev:
            text = "".join(seg.get("utf8", "") for seg in ev["segs"] if seg.get("utf8"))
        elif "runs" in ev:
            text = "".join(run.get("utf8", "") for run in ev["runs"] if run.get("utf8"))
        else:
            text = ev.get("utf8", "") or ""

        text = re.sub(r"<[^>]+>", "", text).strip()
        if not text:
            continue

        start = (ev.get("tStartMs") or 0) / 1000.0
        dur = (ev.get("dDurationMs") or 0) / 1000.0
        segs.append({"text": text, "start": start, "duration": max(0.0, dur)})

    return segs

def _pick_subtitle_files(td: Path, video_id: str, lang: str):
    """
    yt-dlp が吐く字幕ファイルの拡張子は環境や指定で揺れるため、
    tempdir 内を総当たりで拾う。
    - .vtt
    - .json / .json3 / .srv3 など（中身が JSON なら json3として扱う）
    """
    files = []
    for p in td.glob("*"):
        if not p.is_file():
            continue
        if str(p).endswith(".part"):
            continue
        name = p.name

        # ざっくり言語と video_id を含むものだけに絞る（outtmplに依存しない）
        if video_id not in name:
            continue
        if lang not in name:
            continue

        suf = p.suffix.lower()
        if suf in [".vtt", ".json", ".json3", ".srv3"]:
            files.append(p)

    # 新しいもの優先
    files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    return files

def fetch_subtitles_via_ytdlp_robust(
    video_id: str,
    langs=SUB_LANGS_ORDERED,
    max_retries: int = 5,
    base_sleep: float = 2.0,
):
    """
    取得できたら [{'text','start','duration'}, ...] を返す。ダメなら None。
    戦略:
      - 言語 × クライアント × フォーマット × 自動/手動
      - 429/HTTPエラーは指数バックオフで粘る
      - cookies.txt と cookies-from-browser を自動使用（ローカル救済）
      - HTTP(S)_PROXY があれば proxy 使用
    """

    cookies_path = "cookies.txt" if Path("cookies.txt").exists() else None
    http_proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy") or os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy")

    # cookies-from-browser（任意）: chrome / edge など
    cookies_from_browser = os.environ.get("YTDLP_COOKIES_FROM_BROWSER")

    # 字幕フォーマット候補（指定しても実際は別拡張子で出ることがある）
    fmt_candidates = ["vtt", "json3"]
    # 自動字幕→手動→自動（揺らぎ対策）
    auto_modes = [True, False, True]

    url = f"https://www.youtube.com/watch?v={video_id}"

    for lang in langs:
        for clients in _CLIENT_CANDIDATES:
            for fmt in fmt_candidates:
                for auto in auto_modes:
                    attempt = 0
                    while attempt <= max_retries:
                        ua = random.choice(_UA_POOL)
                        try:
                            with tempfile.TemporaryDirectory() as td_str:
                                td = Path(td_str)

                                # outtmpl は “とにかく tempdir に落ちればOK” なので単純に
                                # ※ yt-dlp が内部で言語やフォーマットを付け足すことがある
                                out_tmpl = str(td / f"{video_id}.%(ext)s")

                                ydl_opts = {
                                    "skip_download": True,
                                    "quiet": True,
                                    "no_warnings": True,
                                    "noplaylist": True,

                                    # 手動字幕は writesubtitles、自動字幕は writeautomaticsub が主
                                    "writesubtitles": True,
                                    "writeautomaticsub": auto,

                                    # 1言語ずつトライ
                                    "subtitleslangs": [lang],
                                    "subtitlesformat": "vtt" if fmt == "vtt" else "json3",

                                    "outtmpl": out_tmpl,

                                    # ネットワークまわり（大人しく）
                                    "retries": 5,
                                    "fragment_retries": 5,
                                    "concurrent_fragment_downloads": 1,
                                    "sleep_interval": 1,
                                    "max_sleep_interval": 5,

                                    "http_headers": {
                                        "User-Agent": ua,
                                        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
                                    },

                                    "extractor_args": {
                                        "youtube": {
                                            "player_client": clients
                                        }
                                    },
                                }

                                if cookies_path:
                                    ydl_opts["cookiefile"] = cookies_path
                                elif cookies_from_browser:
                                    ydl_opts["cookiesfrombrowser"] = (cookies_from_browser,)

                                if http_proxy:
                                    ydl_opts["proxy"] = http_proxy

                                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                                    ydl.extract_info(url, download=True)

                                # === 保存された字幕ファイルを総当たりで拾う ===
                                files = _pick_subtitle_files(td, video_id, lang)
                                if not files:
                                    # この組合せでは無さそう → 次へ
                                    # print(f"[DBG] no files: lang={lang} client={clients} fmt={fmt} auto={auto}")
                                    break

                                segs_all = []
                                for p in files:
                                    suf = p.suffix.lower()
                                    try:
                                        if suf == ".vtt":
                                            segs_all.extend(_vtt_to_segments(p))
                                        else:
                                            segs_all.extend(_json3_to_segments(p))
                                    except Exception:
                                        # 壊れた字幕が混ざることもあるのでスキップ
                                        continue

                                if segs_all:
                                    time.sleep(random.uniform(0.8, 1.6))
                                    print(f"[OK] subtitles: lang={lang} client={clients} fmt={fmt} auto={auto} segs={len(segs_all)}")
                                    return segs_all

                                # 空なら次の組合せへ
                                break

                        except yt_dlp.utils.DownloadError as e:
                            msg = str(e)

                            if ("429" in msg) or ("Too Many Requests" in msg):
                                print(f"[429] lang={lang} client={clients} fmt={fmt} auto={auto} attempt={attempt+1}/{max_retries}")
                                _sleep_backoff(base_sleep, attempt)
                                attempt += 1
                                continue

                            if any(k in msg for k in ["HTTP Error 403", "HTTP Error 401", "Sign in to confirm"]):
                                print(f"[AUTH?] {msg[:140]} ... backoff retry")
                                _sleep_backoff(base_sleep, attempt)
                                attempt += 1
                                continue

                            # それ以外はこの組合せは諦める
                            print(f"[WARN] yt_dlp failed: lang={lang} client={clients} fmt={fmt} auto={auto} -> {msg[:160]}")
                            break

                        except Exception as e:
                            print(f"[WARN] unexpected: lang={lang} client={clients} fmt={fmt} auto={auto} -> {e}")
                            break

    print("[INFO] subtitles not found via yt_dlp (all strategies tried).")
    return None
