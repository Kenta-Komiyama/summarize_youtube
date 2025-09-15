import re
from googleapiclient.discovery import build

def build_yt(api_key: str):
    return build("youtube", "v3", developerKey=api_key)

def _extract_channel_id_from_url(url: str):
    m = re.search(r"youtube\.com\/channel\/([A-Za-z0-9_\-]+)", url)
    return m.group(1) if m else None

def resolve_channel_id(youtube, handle_or_url_or_id: str) -> str:
    if isinstance(handle_or_url_or_id, str) and handle_or_url_or_id.startswith("http"):
        cid = _extract_channel_id_from_url(handle_or_url_or_id)
        if cid: return cid
    # UC... 直指定
    if re.fullmatch(r"UC[0-9A-Za-z_\-]{22}", handle_or_url_or_id or ""):
        return handle_or_url_or_id
    # 検索で解決
    q = handle_or_url_or_id
    if isinstance(handle_or_url_or_id, str) and handle_or_url_or_id.startswith("http"):
        m = re.search(r"youtube\.com/(?:@|c/|user/)?([^/?#&]+)", handle_or_url_or_id)
        if m: q = m.group(1)
    resp = youtube.search().list(part="snippet", q=q, type="channel", maxResults=1).execute()
    items = resp.get("items", [])
    if not items:
        raise ValueError(f"チャンネル特定不可: {handle_or_url_or_id}")
    return items[0]["snippet"]["channelId"]

def get_uploads_playlist_id(youtube, channel_id: str) -> str:
    resp = youtube.channels().list(part="contentDetails", id=channel_id).execute()
    items = resp.get("items", [])
    if not items:
        raise ValueError(f"チャンネルが見つかりません: {channel_id}")
    return items[0]["contentDetails"]["relatedPlaylists"]["uploads"]

def list_recent_videos(youtube, uploads_playlist_id: str, max_results=10):
    resp = youtube.playlistItems().list(
        part="snippet,contentDetails",
        playlistId=uploads_playlist_id,
        maxResults=max_results
    ).execute()
    videos = []
    for it in resp.get("items", []):
        snip = it["snippet"]; content = it["contentDetails"]
        videos.append({
            "video_id": content["videoId"],
            "title": snip["title"],
            "channel_title": snip["channelTitle"],
            "published_at": snip["publishedAt"]
        })
    videos.sort(key=lambda x: x["published_at"], reverse=True)
    return videos
