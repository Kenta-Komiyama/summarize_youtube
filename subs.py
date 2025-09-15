# subs.py
# 強化版: 429/取りこぼし対策・クライアント/UA/フォーマット/モードを多段で切替

import os
import re
import time
import random
import tempfile
from pathlib import Path
import yt_dlp

# まずは日本語→英語系を優先。必要なら追加してOK
SUB_LANGS_ORDERED = ['ja', 'ja-JP', 'en', 'en-US', 'en-GB']

# 代表的な UA をローテーション
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
    ["android"],   # まず android
    ["web"],       # ダメなら web
    ["ios"],       # さらに ios
]

# 429 に強い指数バックオフ
def _sleep_backoff(base: float, attempt: int):
    wait = base * (2 ** attempt) + random.uniform(0.0, 1.2)
    wait = min(wait, 20.0)  # 上限
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
                segs.append({"text": " ".join(buf).strip(), "start": start, "duration": dur}); buf = []
            start = to_sec(m.group(1))
            end = to_sec(m.group(2))
            dur = max(0.0, end - start)
        else:
            if ln and not ln.startswith(("WEBVTT", "NOTE")):
                txt = re.sub(r"<[^>]+>", "", ln)
                if txt.strip(): buf.append(txt.strip())
    if buf:
        segs.append({"text": " ".join(buf).strip(), "start": start, "duration": dur})
    return segs

def _json3_to_segments(json3_path: Path):
    # json3(srv3) は 1行1チャンクの JSON。yt-dlp は .json で出力する
    import json
    data = json.loads(json3_path.read_text(encoding="utf-8", errors="ignore"))
    segs = []
    # srv3 はイベントに runs/utf8 と tStartMs/dDurationMs が入っていることが多い
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
            # 互換: 予期せぬ構造
            text = ev.get("utf8", "") or ""
        text = re.sub(r"<[^>]+>", "", text).strip()
        if not text:
            continue
        start = (ev.get("tStartMs") or 0) / 1000.0
        dur = (ev.get("dDurationMs") or 0) / 1000.0
        segs.append({"text": text, "start": start, "duration": max(0.0, dur)})
    return segs

def fetch_subtitles_via_ytdlp_robust(
    video_id: str,
    langs = SUB_LANGS_ORDERED,
    max_retries: int = 5,
    base_sleep: float = 2.0,
):
    """
    取得できたら [{'text','start','duration'}, ...] を返す。ダメなら None。
    戦略:
      - 言語 × クライアント × フォーマット × 自動/手動
      - 429/HTTPエラーは指数バックオフで粘る
      - cookies.txt と HTTP_PROXY を自動使用
    """
    cookies_path = "cookies.txt" if Path("cookies.txt").exists() else None
    http_proxy = os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy")

    # 試行の順番を列挙
    fmt_candidates = ["vtt", "json3"]      # json3 は srv3（YouTubeのJSON字幕）
    auto_modes = [True, False, True]       # 自動字幕あり → なし → 再びあり（揺らぎ対策）

    for lang in langs:
        for clients in _CLIENT_CANDIDATES:
            for fmt in fmt_candidates:
                for auto in auto_modes:
                    attempt = 0
                    while attempt <= max_retries:
                        ua = random.choice(_UA_POOL)
                        try:
                            with tempfile.TemporaryDirectory() as td:
                                out_tmpl = str(Path(td) / f"{video_id}.{lang}.{fmt}.%(ext)s")

                                ydl_opts = {
                                    "skip_download": True,
                                    "writesubtitles": True,
                                    "writeautomaticsub": auto,       # 自動字幕の可否
                                    "subtitleslangs": [lang],        # 1言語ずつ
                                    "subtitlesformat": "vtt" if fmt == "vtt" else "json3",
                                    "outtmpl": out_tmpl,
                                    "quiet": True,
                                    "no_warnings": True,
                                    "noplaylist": True,
                                    # ネットワークまわり
                                    "ratelimit": 5_000_000,
                                    "throttledratelimit": 1_000_000,
                                    "retries": 3,
                                    "fragment_retries": 3,
                                    "http_headers": {
                                        "User-Agent": ua,
                                        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
                                    },
                                    "extractor_args": {
                                        "youtube": {
                                            # 内部クライアントの切替
                                            "player_client": clients
                                        }
                                    },
                                }
                                if cookies_path:
                                    ydl_opts["cookiefile"] = cookies_path
                                if http_proxy:
                                    ydl_opts["proxy"] = http_proxy

                                url = f"https://www.youtube.com/watch?v={video_id}"
                                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                                    ydl.extract_info(url, download=True)

                                # 保存された字幕ファイルを拾う
                                ext_glob = "*.vtt" if fmt == "vtt" else "*.json"
                                files = list(Path(td).glob(f"{video_id}.{lang}.{fmt}.{ext_glob}"))
                                if not files:
                                    # 取得失敗（この組合せでは無さそう）→ 次の組合せへ
                                    print(f"[DBG] no files: lang={lang} client={clients} fmt={fmt} auto={auto}")
                                    break

                                segs_all = []
                                for p in sorted(files):
                                    if fmt == "vtt":
                                        segs_all.extend(_vtt_to_segments(p))
                                    else:
                                        segs_all.extend(_json3_to_segments(p))

                                if segs_all:
                                    # 小休止（連続叩き防止）
                                    time.sleep(random.uniform(0.8, 1.6))
                                    print(f"[OK] subtitles: lang={lang} client={clients} fmt={fmt} auto={auto} segs={len(segs_all)}")
                                    return segs_all
                                else:
                                    print(f"[DBG] empty segs: lang={lang} client={clients} fmt={fmt} auto={auto}")
                                    break

                        except yt_dlp.utils.DownloadError as e:
                            msg = str(e)
                            # 429 or Too Many Requests
                            if "429" in msg or "Too Many Requests" in msg:
                                print(f"[429] lang={lang} client={clients} fmt={fmt} auto={auto} attempt={attempt+1}/{max_retries}")
                                _sleep_backoff(base_sleep, attempt)
                                attempt += 1
                                continue
                            # 403/401 等で弾かれる場合もバックオフ（cookieやproxyが有効なこと多い）
                            if any(code in msg for code in ["HTTP Error 403", "HTTP Error 401", "Sign in to confirm"]):
                                print(f"[AUTH?] {msg[:120]} ...  retry with backoff")
                                _sleep_backoff(base_sleep, attempt)
                                attempt += 1
                                continue
                            print(f"[WARN] yt_dlp failed: lang={lang} client={clients} fmt={fmt} auto={auto} -> {e}")
                            break
                        except Exception as e:
                            print(f"[WARN] unexpected: lang={lang} client={clients} fmt={fmt} auto={auto} -> {e}")
                            break
                    # 次の組み合わせへ
    # すべて失敗
    print("[INFO] subtitles not found via yt_dlp (all strategies tried).")
    return None
