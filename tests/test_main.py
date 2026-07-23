from unittest.mock import patch
from youtube_digest.main import build_video_entry, run

VIDEO = {
    "video_id": "abc123",
    "title": "Video Title",
    "published_at": "2026-07-23T10:00:00Z",
    "description": "Official description here.",
}


def test_build_video_entry_uses_transcript_when_available():
    with patch("youtube_digest.main.fetch_transcript", return_value="contenuto trascritto reale"):
        entry = build_video_entry("My Channel", VIDEO)

    assert entry["content_source"] == "transcript"
    assert entry["content_text"] == "contenuto trascritto reale"
    assert entry["channel_title"] == "My Channel"
    assert entry["video_url"] == "https://www.youtube.com/watch?v=abc123"


def test_build_video_entry_falls_back_when_no_transcript():
    with patch("youtube_digest.main.fetch_transcript", return_value=None):
        entry = build_video_entry("My Channel", VIDEO)

    assert entry["content_source"] == "description_fallback"
    assert entry["content_text"] == "Official description here."


def test_run_assembles_entries_across_channels():
    config = {
        "google_client_id": "id",
        "google_client_secret": "secret",
        "google_refresh_token": "refresh",
    }
    channels = [{"channel_id": "c1", "title": "Channel One"}]
    with patch("youtube_digest.main.load_config", return_value=config), \
         patch("youtube_digest.main.refresh_access_token", return_value="token"), \
         patch("youtube_digest.main.get_subscribed_channels", return_value=channels), \
         patch("youtube_digest.main.get_uploads_playlist_id", return_value="playlist-id"), \
         patch("youtube_digest.main.get_todays_videos", return_value=[VIDEO]), \
         patch("youtube_digest.main.fetch_transcript", return_value=None):
        result = run("config.json", today_iso="2026-07-23")

    assert len(result) == 1
    assert result[0]["channel_title"] == "Channel One"
