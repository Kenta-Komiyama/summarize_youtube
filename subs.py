import os, re, time, random, tempfile
from pathlib import Path
import yt_dlp

SUB_LANGS_ORDERED = ['ja','ja-JP','en']  # まずは少なめが吉

def _vtt_to_segments(vtt_path: Path):
    lines = vtt_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    segs, buf, start, dur = [], [], 0.0, 0.0
    ts_re = re.compile(r"(\d+:\d{2}:\d{2}\.\d{3})\s-->\s(\d+:\d{2}:\d{2}\.\d{3})")
    def to_sec(ts):
        h,m,s = ts.split(":"); return int(h)*3600 + int(m)*60 + float(s)
    for ln in lines:
        m = ts_re.search(ln)
        if m:
            if buf:
                segs.append({"text":" ".join(buf).strip(),"start":start,"duration":dur}); buf=[]
            start = to_sec(m.group(1)); end = to_sec(m.group(2)); dur = max(0.0, end-start)
        else:
            if ln and not ln.startswith(("WEBVTT","NOTE")):
                txt = re.sub(r"<[^>]+>", "", ln)
                if txt.strip(): buf.append(txt.strip())
    if buf:
        segs.append({"text":" ".join(buf).strip(),"start":start,"duration":dur})
    return segs

def fetch_subtitles_via_ytdlp_robust(video_id: str,
                                     langs=SUB_LANGS_ORDERED,
                                     max_retries=4,
                                     base_sleep=2.0):
    cookies_path = "cookies.txt" if Path("cookies.txt").exists() else None
    http_proxy = os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy")
    for lang in langs:
        attempt = 0
        while attempt <= max_retries:
            try:
                with tempfile.TemporaryDirectory() as td:
                    out_tmpl = str(Path(td)/f"{video_id}.{lang}.%(ext)s")
                    ydl_opts = {
                        "skip_download": True,
                        "writesubtitles": True,
                        "writeautomaticsub": True,
                        "subtitleslangs": [lang],
                        "subtitlesformat": "vtt",
                        "outtmpl": out_tmpl,
                        "quiet": True,
                        "no_warnings": True,
                        "ratelimit": 5_000_000,
                        "throttledratelimit": 1_000_000,
                        "retries": 3,
                        "fragment_retries": 3,
                        "extractor_args": {"youtube": {"player_client": ["android"]}},
                        "http_headers": {"User-Agent": "Mozilla/5.0 (Linux; Android 10; Pixel 3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Mobile Safari/537.36"},
                    }
                    if cookies_path:
                        ydl_opts["cookiefile"] = cookies_path
                    if http_proxy:
                        ydl_opts["proxy"] = http_proxy

                    url = f"https://www.youtube.com/watch?v={video_id}"
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.extract_info(url, download=True)

                    vtts = list(Path(td).glob(f"{video_id}.{lang}*.vtt"))
                    if not vtts:
                        break

                    segs_all = []
                    for p in sorted(vtts):
                        segs_all.extend(_vtt_to_segments(p))
                    if segs_all:
                        time.sleep(random.uniform(1.0, 2.5))
                        return segs_all
                    break

            except yt_dlp.utils.DownloadError as e:
                msg = str(e)
                if "429" in msg or "Too Many Requests" in msg:
                    wait = base_sleep * (2 ** attempt) + random.uniform(0, 1.0)
                    print(f"[429] lang={lang} retry in {wait:.1f}s (attempt {attempt+1}/{max_retries})")
                    time.sleep(wait)
                    attempt += 1
                    continue
                else:
                    print(f"[WARN] yt_dlp failed for lang={lang}: {e}")
                    break
            except Exception as e:
                print(f"[WARN] unexpected error for lang={lang}: {e}")
                break
    return None
