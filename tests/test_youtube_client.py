from unittest.mock import patch, MagicMock
from youtube_digest.youtube_client import (
    refresh_access_token,
    get_subscribed_channels,
    get_uploads_playlist_id,
    get_todays_videos,
)


def test_refresh_access_token():
    response = MagicMock()
    response.json.return_value = {"access_token": "new-token"}
    response.raise_for_status.return_value = None

    with patch("youtube_digest.youtube_client.requests.post", return_value=response):
        token = refresh_access_token("client-id", "client-secret", "refresh-token")

    assert token == "new-token"


def test_get_subscribed_channels_paginates():
    page1 = MagicMock()
    page1.json.return_value = {
        "items": [{"snippet": {"resourceId": {"channelId": "c1"}, "title": "Channel One"}}],
        "nextPageToken": "TOKEN2",
    }
    page1.raise_for_status.return_value = None
    page2 = MagicMock()
    page2.json.return_value = {
        "items": [{"snippet": {"resourceId": {"channelId": "c2"}, "title": "Channel Two"}}],
    }
    page2.raise_for_status.return_value = None

    with patch("youtube_digest.youtube_client.requests.get", side_effect=[page1, page2]) as mock_get:
        result = get_subscribed_channels("fake-token")

    assert result == [
        {"channel_id": "c1", "title": "Channel One"},
        {"channel_id": "c2", "title": "Channel Two"},
    ]
    assert mock_get.call_count == 2


def test_get_uploads_playlist_id():
    response = MagicMock()
    response.json.return_value = {
        "items": [{"contentDetails": {"relatedPlaylists": {"uploads": "UUxxxx"}}}]
    }
    response.raise_for_status.return_value = None

    with patch("youtube_digest.youtube_client.requests.get", return_value=response):
        result = get_uploads_playlist_id("fake-token", "channel-id")

    assert result == "UUxxxx"


def test_get_todays_videos_filters_by_date():
    response = MagicMock()
    response.json.return_value = {
        "items": [
            {
                "snippet": {
                    "resourceId": {"videoId": "v1"},
                    "title": "Video Today",
                    "publishedAt": "2026-07-23T10:00:00Z",
                    "description": "desc 1",
                }
            },
            {
                "snippet": {
                    "resourceId": {"videoId": "v2"},
                    "title": "Video Yesterday",
                    "publishedAt": "2026-07-22T10:00:00Z",
                    "description": "desc 2",
                }
            },
        ]
    }
    response.raise_for_status.return_value = None

    with patch("youtube_digest.youtube_client.requests.get", return_value=response):
        result = get_todays_videos("fake-token", "playlist-id", "2026-07-23")

    assert result == [
        {
            "video_id": "v1",
            "title": "Video Today",
            "published_at": "2026-07-23T10:00:00Z",
            "description": "desc 1",
        }
    ]
