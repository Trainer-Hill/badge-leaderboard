import json
import logging
import os

import requests

logger = logging.getLogger(__name__)

_DISCORD_IDS_FILE = os.path.join(os.path.dirname(__file__), '..', 'discord_ids.json')
_WEBHOOK_URL = os.getenv('TH_BL_DISCORD_WEBHOOK')


def _load_discord_ids():
    try:
        with open(_DISCORD_IDS_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_discord_id(trainer, discord_id):
    ids = _load_discord_ids()
    ids[trainer] = discord_id
    with open(_DISCORD_IDS_FILE, 'w') as f:
        json.dump(ids, f, indent=2)


def _mention(trainer):
    discord_id = _load_discord_ids().get(trainer)
    if discord_id:
        return f'<@{discord_id}>'
    return trainer


def _color_int(hex_color):
    try:
        return int((hex_color or '#ffffff').lstrip('#'), 16)
    except ValueError:
        return 0xffffff


def post_badge(badge):
    """Post a new badge announcement to Discord via webhook."""
    if not _WEBHOOK_URL:
        return

    image_bytes = None
    try:
        from util.discord_image import badge_to_bytes
        image_bytes = badge_to_bytes(badge)
    except Exception as e:
        logger.warning('Failed to generate badge image: %s', e)

    mention = _mention(badge.get('trainer', 'Someone'))
    embed = {
        'description': f'Congrats to {mention} on earning their badge!',
        'color': _color_int(badge.get('color')),
    }

    try:
        if image_bytes:
            embed['image'] = {'url': 'attachment://badge.png'}
            requests.post(
                _WEBHOOK_URL,
                data={'payload_json': json.dumps({'embeds': [embed]})},
                files={'file': ('badge.png', image_bytes, 'image/png')},
                timeout=10,
            )
        else:
            requests.post(_WEBHOOK_URL, json={'embeds': [embed]}, timeout=10)
    except Exception as e:
        logger.error('Failed to post badge to Discord: %s', e)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    sample = {
        'trainer': 'Test Trainer',
        'pronouns': 'their',
        'deck': {'id': 'charizard', 'name': 'Charizard ex', 'icons': ['charizard']},
        'store': 'Area Zero TCG',
        'date': '2025-01-01',
        'color': '#e25822',
        'background': 'Fire',
        'tier': 'League Cup',
        'format': 'standard',
    }

    post_badge(sample)
    print('Done')
