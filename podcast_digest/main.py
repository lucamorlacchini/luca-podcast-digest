import json
import os
import sys
from datetime import date, datetime, timedelta

from podcast_digest.feeds import ROME_TZ, episodes_on, fetch_feed, parse_episodes, spotify_search_url
from podcast_digest.transcribe import TranscriptionError, transcribe_episode

OUTPUT_DIR = "out"


def load_json(path: str):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def expiry_warning(expires_iso: str | None, today: date) -> str | None:
    # Luca asked for a reminder 2 days and 1 day before the 30-day Groq key expires.
    if not expires_iso:
        return None
    days_left = (date.fromisoformat(expires_iso) - today).days
    if days_left in (1, 2):
        when = "domani" if days_left == 1 else "tra 2 giorni"
        return (f"La chiave Groq usata per le trascrizioni scade {when} ({expires_iso}). "
                "Se il digest ti è utile, creane una nuova su console.groq.com e aggiornala in config.json.")
    if days_left <= 0:
        return f"La chiave Groq è scaduta il {expires_iso}: le trascrizioni non funzionano finché non viene sostituita."
    return None


def build_entry(podcast_name: str, episode: dict, api_key: str, index: int) -> dict:
    entry = {
        "podcast": podcast_name,
        "episode_title": episode["title"],
        "published_at": episode["published_at"].isoformat(),
        "spotify_url": spotify_search_url(podcast_name, episode["title"]),
    }
    try:
        text = transcribe_episode(episode["audio_url"], api_key)
        entry["content_source"] = "transcript"
    except TranscriptionError as exc:
        text = episode["description"]
        entry["content_source"] = "description_fallback" if text else "none"
        entry["fallback_reason"] = str(exc)
    # Full transcripts are long (~8,000 words per hour), so they go to files the
    # routine agent reads one at a time instead of one giant stdout JSON.
    content_file = os.path.join(OUTPUT_DIR, f"{index:02d}.txt")
    with open(content_file, "w", encoding="utf-8") as f:
        f.write(text)
    entry["content_file"] = content_file
    entry["content_words"] = len(text.split())
    return entry


def run(config_path: str, podcasts_path: str, target_iso: str | None = None) -> dict:
    config = load_json(config_path)
    today = datetime.now(ROME_TZ).date()
    # The routine runs early each morning, so target the full previous day.
    target_date = date.fromisoformat(target_iso) if target_iso else today - timedelta(days=1)
    warnings = [w for w in [expiry_warning(config.get("groq_key_expires"), today)] if w]
    start_date = config.get("start_date")
    if start_date and target_date < date.fromisoformat(start_date):
        # Never transcribe (and pay for) episodes released before the digest was switched on.
        return {"status": "ok", "target_date": target_date.isoformat(), "episodes": [],
                "feed_errors": [], "warnings": warnings}

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    episodes, feed_errors = [], []
    for podcast in load_json(podcasts_path):
        try:
            found = episodes_on(parse_episodes(fetch_feed(podcast["feed_url"])), target_date)
        except Exception as exc:
            # One broken feed must not cost Luca the whole digest.
            feed_errors.append({"podcast": podcast["name"], "error": type(exc).__name__})
            continue
        for episode in found:
            episodes.append(build_entry(podcast["name"], episode, config["groq_api_key"], len(episodes) + 1))

    return {"status": "ok", "target_date": target_date.isoformat(), "episodes": episodes,
            "feed_errors": feed_errors, "warnings": warnings}


if __name__ == "__main__":
    config_path = sys.argv[1] if len(sys.argv) > 1 else "config.json"
    target_iso = sys.argv[2] if len(sys.argv) > 2 else None
    try:
        result = run(config_path, "podcasts.json", target_iso)
    except Exception as exc:
        result = {"status": "error", "message": f"{type(exc).__name__}: {exc}"}
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
