from unittest.mock import patch
from youtube_digest.transcript import fetch_transcript


def test_fetch_transcript_joins_text_segments():
    with patch(
        "youtube_digest.transcript.YouTubeTranscriptApi.get_transcript",
        return_value=[
            {"text": "ciao a tutti"},
            {"text": "oggi parliamo di X"},
        ],
    ):
        result = fetch_transcript("video123")

    assert result == "ciao a tutti oggi parliamo di X"


def test_fetch_transcript_returns_none_on_any_error():
    with patch(
        "youtube_digest.transcript.YouTubeTranscriptApi.get_transcript",
        side_effect=Exception("blocked or no captions"),
    ):
        result = fetch_transcript("video123")

    assert result is None
