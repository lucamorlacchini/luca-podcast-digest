from unittest.mock import patch, MagicMock
from youtube_digest.transcript import fetch_transcript


def test_fetch_transcript_joins_text_segments():
    fake_api = MagicMock()
    fake_api.fetch.return_value = [
        {"text": "ciao a tutti"},
        {"text": "oggi parliamo di X"},
    ]

    with patch("youtube_digest.transcript.YouTubeTranscriptApi", return_value=fake_api):
        result = fetch_transcript("video123")

    assert result == "ciao a tutti oggi parliamo di X"


def test_fetch_transcript_returns_none_on_any_error():
    fake_api = MagicMock()
    fake_api.fetch.side_effect = Exception("blocked or no captions")

    with patch("youtube_digest.transcript.YouTubeTranscriptApi", return_value=fake_api):
        result = fetch_transcript("video123")

    assert result is None
