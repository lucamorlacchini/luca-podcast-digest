import html
import re

# The routine agent writes email_body.txt as plain text, hard-wrapped at ~70
# characters. Sent as text/plain that shows up as a narrow column on the left of
# the screen, so this rebuilds the paragraphs and sends a justified HTML version
# that reflows to the width of the phone.

HEADER_RE = re.compile(r"^===\s*(.+?)\s*===$")
SPOTIFY_RE = re.compile(r"Ascolta su Spotify:\s*(\S*)")
META_PREFIXES = ("⚠️", "Trascrizioni:", "Podcast non controllati")

FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif"
TEXT = ("margin:0 0 12px 0;text-align:justify;-webkit-hyphens:auto;hyphens:auto;"
        "word-wrap:break-word;overflow-wrap:break-word")


def _esc(text: str) -> str:
    # The agent sometimes writes entities itself ("S&amp;P"): normalise before escaping.
    return html.escape(html.unescape(text), quote=False)


def _blocks(text: str) -> list[list[str]]:
    blocks, current = [], []
    for line in text.replace("\r\n", "\n").split("\n"):
        line = line.strip()
        if line:
            current.append(line)
        elif current:
            blocks.append(current)
            current = []
    if current:
        blocks.append(current)
    return blocks


def _spotify_url(block: list[str]) -> str | None:
    joined = " ".join(block)
    match = SPOTIFY_RE.search(joined)
    return match.group(1) if match else None


def _render_summary(block: list[str]) -> str:
    paragraphs, bullets, url = [], [], None
    lines = iter(block)
    for line in lines:
        if line.startswith("Ascolta su Spotify:"):
            url = line.split(":", 1)[1].strip() or next(lines, "").strip()
        elif line.startswith("- "):
            bullets.append(line[2:])
        elif bullets:
            bullets[-1] += " " + line
        elif paragraphs:
            paragraphs[-1] += " " + line
        else:
            paragraphs.append(line)
    parts = [f'<p style="{TEXT}">{_esc(p)}</p>' for p in paragraphs]
    if bullets:
        items = "".join(f'<li style="{TEXT};margin-bottom:8px">{_esc(b)}</li>' for b in bullets)
        parts.append(f'<ul style="margin:0 0 12px 0;padding-left:20px">{items}</ul>')
    if url:
        parts.append(f'<p style="margin:0 0 4px 0"><a href="{html.escape(url)}" '
                     'style="color:#1DB954;font-weight:600;text-decoration:none">'
                     '▶ Ascolta su Spotify</a></p>')
    return "".join(parts)


def _render_meta(block: list[str]) -> str:
    paragraphs = []
    for line in block:
        if not paragraphs or line.startswith(META_PREFIXES):
            paragraphs.append(line)
        else:
            paragraphs[-1] += " " + line
    out = []
    for p in paragraphs:
        if p.startswith("⚠️"):
            out.append('<p style="margin:0 0 12px 0;padding:10px 12px;background:#FFF4E5;'
                       f'border-left:4px solid #F5A623;border-radius:4px">{_esc(p)}</p>')
        else:
            out.append(f'<p style="{TEXT};color:#555555;font-size:14px">{_esc(p)}</p>')
    return "".join(out)


def to_html(text: str) -> str:
    blocks = _blocks(text)
    parts = []
    for i, block in enumerate(blocks):
        header = HEADER_RE.match(block[0]) if len(block) == 1 else None
        next_is_summary = i + 1 < len(blocks) and _spotify_url(blocks[i + 1]) is not None
        if header:
            parts.append('<h2 style="margin:28px 0 8px 0;padding-bottom:6px;font-size:19px;'
                         'line-height:1.3;color:#1A1A1A;text-align:left;border-bottom:2px solid #E5E5E5">'
                         f'{_esc(header.group(1))}</h2>')
        elif _spotify_url(block) is not None:
            parts.append(_render_summary(block))
        elif next_is_summary and parts:
            parts.append('<h3 style="margin:20px 0 8px 0;font-size:16px;line-height:1.35;'
                         f'color:#1A1A1A;text-align:left">{_esc(" ".join(block))}</h3>')
        else:
            parts.append(_render_meta(block))
    body = "".join(parts)
    return (
        '<!DOCTYPE html><html lang="it"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<meta name="x-apple-disable-message-reformatting"></head>'
        '<body style="margin:0;padding:0;background:#FFFFFF">'
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">'
        '<tr><td align="center" style="padding:16px 14px">'
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" '
        'style="max-width:680px">'
        f'<tr><td lang="it" style="font-family:{FONT};font-size:16px;line-height:1.55;'
        f'color:#222222;text-align:justify">{body}</td></tr>'
        '</table></td></tr></table></body></html>'
    )
