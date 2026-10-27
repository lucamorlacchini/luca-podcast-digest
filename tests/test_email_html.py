from podcast_digest.email_html import to_html

SAMPLE = """⚠️ La chiave Groq scade domani.
Trascrizioni: 2 su 2 episodi

=== Black Box ===

ANT, il giorno della formica

Guido Brera commenta l'S-1
depositato da Anthropic. Punti:
- L'IPO punta a raccogliere fino a 100 miliardi
di dollari.
- S&amp;P 500 sotto pressione.
Ascolta su Spotify:
https://open.spotify.com/search/ANT

=== Stories ===

L'unica alleanza
che sconfigge Netanyahu

(nessun contenuto disponibile: download fallito)
Ascolta su Spotify: https://open.spotify.com/search/Stories
"""


def test_hard_wrapped_lines_are_joined_into_paragraphs_and_bullets():
    out = to_html(SAMPLE)
    assert "Guido Brera commenta l'S-1 depositato da Anthropic. Punti:</p>" in out
    assert "fino a 100 miliardi di dollari.</li>" in out
    assert out.count("<li") == 2


def test_structure_headers_titles_links_and_warnings():
    out = to_html(SAMPLE)
    assert ">Black Box</h2>" in out and ">Stories</h2>" in out
    assert ">ANT, il giorno della formica</h3>" in out
    assert ">L'unica alleanza che sconfigge Netanyahu</h3>" in out
    assert 'href="https://open.spotify.com/search/ANT"' in out
    assert 'href="https://open.spotify.com/search/Stories"' in out
    assert "#FFF4E5" in out  # warning box
    assert "Trascrizioni: 2 su 2 episodi" in out


def test_mobile_and_justified_layout():
    out = to_html(SAMPLE)
    assert 'name="viewport"' in out
    assert "max-width:680px" in out
    assert "text-align:justify" in out


def test_entities_are_not_double_escaped():
    out = to_html(SAMPLE)
    assert "S&amp;P 500" in out and "&amp;amp;" not in out


def test_error_email_renders_as_plain_paragraph():
    out = to_html("Il controllo giornaliero è fallito:\nTimeoutError")
    assert "Il controllo giornaliero è fallito: TimeoutError</p>" in out
