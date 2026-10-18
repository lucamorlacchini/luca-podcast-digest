import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta

from podcast_digest.feeds import ROME_TZ, episodes_on, fetch_feed, parse_episodes, spotify_search_url
from podcast_digest.transcribe import TranscriptionError, transcribe_episode

OUTPUT_DIR = "out"
TRANSCRIBE_WORKERS = 4
INVALID_KEY_REASON = "chiave Groq non valida o scaduta"
INVALID_KEY_WARNING = ("La chiave Groq non è valida (revocata o scaduta): nessun episodio è stato trascritto. "
                       "Creane una nuova su console.groq.com e aggiorna la variabile GROQ_API_KEY "
                       "nell'ambiente della routine.")


def groq_api_key(config: dict) -> str:
    # The key lives in the routine environment, not in the repo: a key committed to
    # GitHub gets flagged as exposed and revoked (that is what broke 17 Oct 2026).
    return os.environ.get("GROQ_API_KEY") or config.get("groq_api_key", "")


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
    to_transcribe, feed_errors = [], []
    for podcast in load_json(podcasts_path):
        try:
            found = episodes_on(parse_episodes(fetch_feed(podcast["feed_url"])), target_date)
        except Exception as exc:
            # One broken feed must not cost Luca the whole digest.
            feed_errors.append({"podcast": podcast["name"], "error": type(exc).__name__})
            continue
        to_transcribe.extend((podcast["name"], episode) for episode in found)

    # Download + compress + transcribe is mostly waiting on the network, so a few
    # episodes in parallel keep a ~14-episode day well under the 10-minute mark.
    api_key = groq_api_key(config)
    with ThreadPoolExecutor(max_workers=TRANSCRIBE_WORKERS) as pool:
        episodes = list(pool.map(
            lambda job: build_entry(job[1][0], job[1][1], api_key, job[0]),
            enumerate(to_transcribe, start=1),
        ))
    # A dead key silently turns every summary into show notes; say so at the top of the email.
    if any(e.get("fallback_reason") == INVALID_KEY_REASON for e in episodes):
        warnings.append(INVALID_KEY_WARNING)

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
