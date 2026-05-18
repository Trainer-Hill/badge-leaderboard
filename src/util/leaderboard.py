"""Utilities for leaderboard calculations and rankings."""

from __future__ import annotations

from collections import Counter
from typing import List, Sequence, Tuple

# Badge tiers mapped to their point values. These points are used as a tie breaker
# when players have the same number of badges.
TIER_WEIGHTS = {
    'locals': 1,
    'online': 1,
    'league challenge': 2,
    'league cup': 3,
    'regionals': 5,
    'internationals': 5,
    'worlds': 5,
}


def normalize_value(value):
    """Return a comparable label from raw badge data values."""
    if isinstance(value, dict):
        return value.get('name') or value.get('id')
    return value


def badge_points(badge: dict) -> int:
    """Return the point value for a single badge based on its tier."""
    tier = (badge.get('tier') or '').lower()
    return TIER_WEIGHTS.get(tier, 0)


def weighted_leaderboard(badges: Sequence[dict], key: str) -> List[Tuple[str, int, int]]:
    """Return leaderboard tuples sorted by badge count and tie-broken by points."""
    counts: Counter[str] = Counter()
    weights: Counter[str] = Counter()

    for badge in badges:
        value = normalize_value(badge.get(key))
        if not value:
            continue
        counts[value] += 1
        weights[value] += badge_points(badge)

    leaderboard = [
        (value, counts[value], weights[value])
        for value in counts
    ]

    leaderboard.sort(
        key=lambda item: (item[1], item[2], str(item[0]).lower()),
        reverse=True,
    )
    return leaderboard


__all__ = ['TIER_WEIGHTS', 'normalize_value', 'badge_points', 'weighted_leaderboard']
