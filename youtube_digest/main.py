import json
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from youtube_digest.youtube_client import (
    refresh_access_token,
    get_subscribed_channels,
    get_uploads_playlist_id,
    get_todays_videos,
)
from youtube_digest.transcript import fetch_transcript

ROME_TZ = ZoneInfo("Europe/Rome")


def load_config(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def build_video_entry(channel_title: str, video: dict, transcript_api_key: str) -> dict:
    transcript = fetch_transcript(video["video_id"], transcript_api_key)
    if transcript:
        content_source = "transcript"
        content_text = transcript
    else:
        content_source = "description_fallback"
        content_text = video.get("description", "")
    return {
        "channel_title": channel_title,
        "video_title": video["title"],
        "published_at": video["published_at"],
        "video_url": f"https://www.youtube.com/watch?v={video['video_id']}",
        "content_source": content_source,
        "content_text": content_text,
    }


def run(config_path: str, today_iso: str | None = None) -> list[dict]:
    config = load_config(config_path)
    access_token = refresh_access_token(
        config["google_client_id"],
        config["google_client_secret"],
        config["google_refresh_token"],
    )
    # The routine runs early each morning, so "today" would only cover the few
    # hours since midnight. Default to yesterday's date to capture the full
    # previous day's uploads instead — the reason a daily digest exists at all.
    target_date = today_iso or (datetime.now(ROME_TZ).date() - timedelta(days=1)).isoformat()
    entries = []
    for channel in get_subscribed_channels(access_token):
        uploads_playlist_id = get_uploads_playlist_id(access_token, channel["channel_id"])
        for video in get_todays_videos(access_token, uploads_playlist_id, target_date):
            entries.append(build_video_entry(channel["title"], video, config["transcript_api_key"]))
    return entries


if __name__ == "__main__":
    config_path = sys.argv[1] if len(sys.argv) > 1 else "config.json"
    try:
        videos = run(config_path)
        print(json.dumps({"status": "ok", "videos": videos}))
    except Exception as exc:
        print(json.dumps({"status": "error", "message": str(exc)}))
