from datetime import date

from podcast_digest.feeds import episodes_on, parse_episodes, spotify_search_url

FEED = b"""<?xml version="1.0"?>
<rss xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" xmlns:content="http://purl.org/rss/1.0/modules/content/">
<channel>
  <item>
    <title> Late evening episode </title>
    <pubDate>Mon, 12 Oct 2026 22:30:00 +0000</pubDate>
    <enclosure url="https://cdn.example.com/late.mp3" type="audio/mpeg"/>
    <description>&lt;p&gt;Plain &amp;amp; simple&lt;/p&gt;</description>
  </item>
  <item>
    <title>Morning episode</title>
    <pubDate>Mon, 12 Oct 2026 06:00:00 +0200</pubDate>
    <enclosure url="https://cdn.example.com/morning.mp3" type="audio/mpeg"/>
    <content:encoded><![CDATA[<p>Rich <b>notes</b></p>]]></content:encoded>
    <description>short</description>
  </item>
  <item>
    <title>No audio, skipped</title>
    <pubDate>Mon, 12 Oct 2026 08:00:00 +0200</pubDate>
  </item>
  <item>
    <title>Bad date, skipped</title>
    <pubDate>not a date</pubDate>
    <enclosure url="https://cdn.example.com/bad.mp3"/>
  </item>
</channel>
</rss>"""


def test_parse_episodes_skips_items_without_audio_or_date():
    episodes = parse_episodes(FEED)

    assert [e["title"] for e in episodes] == ["Late evening episode", "Morning episode"]
    assert episodes[0]["audio_url"] == "https://cdn.example.com/late.mp3"


def test_parse_episodes_prefers_full_show_notes_and_strips_html():
    episodes = parse_episodes(FEED)

    assert episodes[0]["description"] == "Plain & simple"
    assert episodes[1]["description"] == "Rich notes"


def test_episodes_on_uses_italian_calendar_day():
    episodes = parse_episodes(FEED)

    # 22:30 UTC on 12 Oct is 00:30 on 13 Oct in Rome.
    assert [e["title"] for e in episodes_on(episodes, date(2026, 10, 12))] == ["Morning episode"]
    assert [e["title"] for e in episodes_on(episodes, date(2026, 10, 13))] == ["Late evening episode"]


def test_spotify_search_url_encodes_title_and_podcast():
    url = spotify_search_url("Black Box", "Tassi & mercati")

    assert url == "https://open.spotify.com/search/Tassi%20%26%20mercati%20Black%20Box"
