from unittest.mock import MagicMock, patch

import pytest

from podcast_digest import transcribe
from podcast_digest.transcribe import TranscriptionError, transcribe_file


def response(status, text="", headers=None):
    r = MagicMock()
    r.status_code = status
    r.text = text
    r.headers = headers or {}
    return r


@pytest.fixture
def audio(tmp_path):
    path = tmp_path / "episode.ogg"
    path.write_bytes(b"fake audio")
    return str(path)


def test_transcribe_file_returns_text(audio):
    with patch.object(transcribe.requests, "post", return_value=response(200, " ciao mondo \n")) as mock_post:
        assert transcribe_file(audio, "gsk_fake") == "ciao mondo"

    kwargs = mock_post.call_args.kwargs
    assert kwargs["headers"] == {"Authorization": "Bearer gsk_fake"}
    assert kwargs["data"]["model"] == "whisper-large-v3-turbo"


def test_transcribe_file_waits_out_short_rate_limit(audio):
    responses = [response(429, headers={"retry-after": "1"}), response(200, "ok")]
    with patch.object(transcribe.requests, "post", side_effect=responses), \
         patch.object(transcribe.time, "sleep") as mock_sleep:
        assert transcribe_file(audio, "gsk_fake") == "ok"

    mock_sleep.assert_called_once_with(1.0)


def test_transcribe_file_gives_up_on_long_rate_limit(audio):
    with patch.object(transcribe.requests, "post", return_value=response(429, headers={"retry-after": "3600"})):
        with pytest.raises(TranscriptionError, match="limite"):
            transcribe_file(audio, "gsk_fake")


def test_transcribe_file_reports_expired_key(audio):
    with patch.object(transcribe.requests, "post", return_value=response(401)):
        with pytest.raises(TranscriptionError, match="scaduta"):
            transcribe_file(audio, "gsk_fake")
