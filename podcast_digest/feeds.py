import html
import re
import xml.etree.ElementTree as ET
from datetime import date, datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import quote
from zoneinfo import ZoneInfo

import requests

ROME_TZ = ZoneInfo("Europe/Rome")
ITUNES_NS = "{http://www.itunes.com/dtds/podcast-1.0.dtd}"
CONTENT_NS = "{http://purl.org/rss/1.0/modules/content/}"
# Some podcast hosts reject the default python-requests user agent.
HEADERS = {"User-Agent": "Mozilla/5.0 (podcast-digest)"}


def fetch_feed(feed_url: str) -> bytes:
    response = requests.get(feed_url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.content


def strip_html(text: str) -> str:
    text = re.sub(r"<br\s*/?>|</p>", "\n", text or "")
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\n\s*\n+", "\n\n", html.unescape(text)).strip()


def parse_episodes(feed_xml: bytes) -> list[dict]:
    episodes = []
    for item in ET.fromstring(feed_xml).findall("./channel/item"):
        enclosure = item.find("enclosure")
        pub_date = item.findtext("pubDate")
        if enclosure is None or not enclosure.get("url") or not pub_date:
            continue
        try:
            published = parsedate_to_datetime(pub_date)
        except (TypeError, ValueError):
            continue
        if published.tzinfo is None:
            published = published.replace(tzinfo=timezone.utc)
        description = (
            item.findtext(CONTENT_NS + "encoded")
            or item.findtext("description")
            or item.findtext(ITUNES_NS + "summary")
            or ""
        )
        episodes.append({
            "title": (item.findtext("title") or "").strip(),
            "published_at": published,
            "audio_url": enclosure.get("url"),
            "description": strip_html(description),
        })
    return episodes


def episodes_on(episodes: list[dict], target_date: date) -> list[dict]:
    """Episodes whose release date, in Italian time, is target_date."""
    return [e for e in episodes if e["published_at"].astimezone(ROME_TZ).date() == target_date]


def spotify_search_url(podcast_name: str, episode_title: str) -> str:
    # Feeds carry no Spotify ids; a search link opens the episode in Spotify in one tap.
    return "https://open.spotify.com/search/" + quote(f"{episode_title} {podcast_name}")
