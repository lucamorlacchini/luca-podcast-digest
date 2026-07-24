from unittest.mock import patch, MagicMock

from youtube_digest.transcript import fetch_transcript


def test_fetch_transcript_joins_text_segments():
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "video_id": "video123",
        "language": "it",
        "transcript": [
            {"text": "ciao a tutti", "start": 0.0, "duration": 2.0},
            {"text": "oggi parliamo di X", "start": 2.0, "duration": 3.0},
        ],
    }

    with patch("youtube_digest.transcript.requests.get", return_value=response) as mock_get:
        result = fetch_transcript("video123", "fake-api-key")

    assert result == "ciao a tutti oggi parliamo di X"
    args, kwargs = mock_get.call_args
    assert args[0] == "https://transcriptapi.com/api/v2/youtube/transcript"
    assert kwargs["headers"] == {"Authorization": "Bearer fake-api-key"}
    assert kwargs["params"] == {"video_url": "video123"}


def test_fetch_transcript_returns_none_on_any_error():
    with patch("youtube_digest.transcript.requests.get", side_effect=Exception("blocked or no captions")):
        result = fetch_transcript("video123", "fake-api-key")

    assert result is None


def test_fetch_transcript_returns_none_on_empty_transcript():
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"video_id": "video123", "language": "it", "transcript": []}

    with patch("youtube_digest.transcript.requests.get", return_value=response):
        result = fetch_transcript("video123", "fake-api-key")

    assert result is None
