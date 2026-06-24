import base64
import os

import th_helpers.utils.colors

_ASSETS_DIR = os.path.join(os.path.dirname(__file__), '..', 'assets')


def _svg_data_uri(background):
    if not background:
        return None
    svg_path = os.path.join(_ASSETS_DIR, 'energy_types', f'{background.lower()}.svg')
    try:
        with open(svg_path, 'rb') as f:
            data = base64.b64encode(f.read()).decode()
        return f'data:image/svg+xml;base64,{data}'
    except FileNotFoundError:
        return None


def _sprite_data_uri(icon):
    import requests
    if not icon or not isinstance(icon, str):
        return None
    url = icon if icon.startswith('https') else f'https://raw.githubusercontent.com/bradley-erickson/pokesprite/master/pokemon/regular/{icon}.png'
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = base64.b64encode(resp.content).decode()
        return f'data:image/png;base64,{data}'
    except Exception:
        return None


def _build_badge_html(badge):
    color = badge.get('color', '#ffffff')
    text_color = th_helpers.utils.colors.text_color_for_background(color)

    background = badge.get('background')
    bg_uri = _svg_data_uri(background)
    bg_style = f"background-image: url('{bg_uri}')" if bg_uri else ''

    trainer = badge.get('trainer', '')
    pronouns = badge.get('pronouns', 'their')

    deck = badge.get('deck') or {}
    deck_name = deck.get('name', '')
    icons = deck.get('icons') or []
    sprite_imgs = ''.join(
        f'<img src="{uri}" style="height:90px;width:auto">'
        for icon in icons if icon
        for uri in [_sprite_data_uri(icon)] if uri
    )
    deck_label = f'''
      <div class="d-flex flex-row align-items-center" title="{deck_name}">
        {sprite_imgs}
        <span class="ms-1">{deck_name}</span>
      </div>'''

    store = badge.get('store', '')
    date = badge.get('date', '')
    if hasattr(date, 'isoformat'):
        date = date.isoformat()

    tier = badge.get('tier', '')
    fmt = badge.get('format', '')
    tier_badge = f'<span class="badge bg-secondary me-1">{tier}</span>' if tier else ''
    format_badge = f'<span class="badge bg-secondary">{fmt}</span>' if fmt else ''

    return f'''<!DOCTYPE html>
<html>
<head>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    html {{ font-size: 32px; }}
    body {{ margin: 0; padding: 0; background: transparent; }}
    .gym-badge-bg {{
      position: absolute;
      width: 150%; height: 250%;
      left: -40%; top: -25%;
      background-repeat: space;
      background-size: 216px 144px;
      background-position: center;
      transform: rotate(-30deg);
      z-index: 0;
    }}
    .gym-badge {{ position: relative; overflow: hidden; }}
    .card-body > *:not(.gym-badge-bg) {{ position: relative; z-index: 1; }}
  </style>
</head>
<body>
  <div class="card text-center gym-badge" style="background-color:{color};color:{text_color};width:100%;">
    <div class="card-body">
      <div class="gym-badge-bg" style="{bg_style}"></div>
      <h4>{trainer}</h4>
      <div class="mb-2">earned <span>{pronouns}</span></div>
      <h4 class="d-flex justify-content-around">{deck_label}</h4>
      <div>badge at <strong>{store}</strong></div>
      <div>on <span>{date}</span></div>
      <div>{tier_badge}{format_badge}</div>
    </div>
  </div>
</body>
</html>'''


def badge_to_bytes(badge):
    """Render badge HTML to PNG bytes via headless Chromium (Playwright)."""
    from playwright.sync_api import sync_playwright

    html = _build_badge_html(badge)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={'width': 816, 'height': 600})
        page.set_content(html, wait_until='networkidle')
        card = page.locator('.card')
        png = card.screenshot()
        browser.close()
    return png


if __name__ == '__main__':
    import json, sys
    badge = json.loads(sys.stdin.read())
    sys.stdout.buffer.write(badge_to_bytes(badge))
