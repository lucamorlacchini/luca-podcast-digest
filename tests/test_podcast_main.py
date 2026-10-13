import json
from datetime import date, datetime, timezone
from unittest.mock import patch

import pytest

from podcast_digest import main
from podcast_digest.main import expiry_warning, run
from podcast_digest.transcribe import TranscriptionError

EPISODE = {
    "title": "Episode One",
    "published_at": datetime(2026, 10, 13, 6, 0, tzinfo=timezone.utc),
    "audio_url": "https://cdn.example.com/one.mp3",
    "description": "Official show notes.",
}


@pytest.fixture
def setup(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config = {"groq_api_key": "gsk_fake", "start_date": "2026-10-13"}
    (tmp_path / "config.json").write_text(json.dumps(config), encoding="utf-8")
    podcasts = [{"name": "Pod A", "feed_url": "https://a.example/feed"},
                {"name": "Pod B", "feed_url": "https://b.example/feed"}]
    (tmp_path / "podcasts.json").write_text(json.dumps(podcasts), encoding="utf-8")
    return tmp_path


def test_run_writes_transcript_to_file(setup):
    with patch.object(main, "fetch_feed", return_value=b""), \
         patch.object(main, "parse_episodes", side_effect=[[EPISODE], []]), \
         patch.object(main, "transcribe_episode", return_value="testo trascritto reale"):
        result = run("config.json", "podcasts.json", "2026-10-13")

    assert result["status"] == "ok"
    [entry] = result["episodes"]
    assert entry["podcast"] == "Pod A"
    assert entry["content_source"] == "transcript"
    assert (setup / entry["content_file"]).read_text(encoding="utf-8") == "testo trascritto reale"


def test_run_falls_back_to_show_notes_with_reason(setup):
    with patch.object(main, "fetch_feed", return_value=b""), \
         patch.object(main, "parse_episodes", side_effect=[[EPISODE], []]), \
         patch.object(main, "transcribe_episode", side_effect=TranscriptionError("chiave Groq non valida o scaduta")):
        result = run("config.json", "podcasts.json", "2026-10-13")

    [entry] = result["episodes"]
    assert entry["content_source"] == "description_fallback"
    assert entry["fallback_reason"] == "chiave Groq non valida o scaduta"
    assert (setup / entry["content_file"]).read_text(encoding="utf-8") == "Official show notes."


def test_run_marks_empty_fallback_as_none(setup):
    silent = dict(EPISODE, description="")
    with patch.object(main, "fetch_feed", return_value=b""), \
         patch.object(main, "parse_episodes", side_effect=[[silent], []]), \
         patch.object(main, "transcribe_episode", side_effect=TranscriptionError("x")):
        result = run("config.json", "podcasts.json", "2026-10-13")

    assert result["episodes"][0]["content_source"] == "none"


def test_run_keeps_going_when_one_feed_fails(setup):
    with patch.object(main, "fetch_feed", side_effect=[ConnectionError("down"), b""]), \
         patch.object(main, "parse_episodes", return_value=[EPISODE]), \
         patch.object(main, "transcribe_episode", return_value="testo"):
        result = run("config.json", "podcasts.json", "2026-10-13")

    assert result["feed_errors"] == [{"podcast": "Pod A", "error": "ConnectionError"}]
    assert [e["podcast"] for e in result["episodes"]] == ["Pod B"]


def test_run_skips_days_before_start_date(setup):
    with patch.object(main, "fetch_feed") as mock_fetch, \
         patch.object(main, "transcribe_episode") as mock_transcribe:
        result = run("config.json", "podcasts.json", "2026-10-12")

    assert result["episodes"] == []
    mock_fetch.assert_not_called()
    mock_transcribe.assert_not_called()


@pytest.mark.parametrize("today, expected", [
    (date(2026, 11, 9), None),
    (date(2026, 11, 10), "tra 2 giorni"),
    (date(2026, 11, 11), "domani"),
    (date(2026, 11, 12), "è scaduta"),
])
def test_expiry_warning_two_days_and_one_day_before(today, expected):
    warning = expiry_warning("2026-11-12", today)

    if expected is None:
        assert warning is None
    else:
        assert expected in warning
