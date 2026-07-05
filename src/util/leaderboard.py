"""Utilities for leaderboard calculations and rankings."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Dict, List, Sequence, Tuple

# Single source of truth for tier point values (used as a tie breaker when
# players have the same number of badges). Re-exported for existing importers.
from util.badges import TIER_WEIGHTS


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


def _collect_trainer_stats(badges: Sequence[dict]):
    """Single-pass accumulator returning (counts, points, decks_by_trainer)."""
    counts: Counter = Counter()
    points: Counter = Counter()
    decks: defaultdict = defaultdict(set)
    for b in badges:
        trainer = b.get('trainer')
        if not trainer:
            continue
        counts[trainer] += 1
        points[trainer] += badge_points(b)
        deck = b.get('deck')
        deck_id = deck.get('id') or deck.get('name') if isinstance(deck, dict) else deck
        if deck_id:
            decks[trainer].add(deck_id)
    return counts, points, decks


def avg_points_per_badge(badges: Sequence[dict]) -> Dict[str, float]:
    """Return per-trainer average points per badge."""
    counts, points, _ = _collect_trainer_stats(badges)
    return {t: points[t] / counts[t] for t in counts}


def deck_diversity_score(badges: Sequence[dict]) -> Dict[str, float]:
    """Return per-trainer deck diversity score (unique_decks² / total_badges).

    Rewards breadth and penalizes playing the same deck repeatedly.
    """
    counts, _, decks = _collect_trainer_stats(badges)
    return {t: len(decks[t]) ** 2 / counts[t] for t in counts}


def trainer_extras(badges: Sequence[dict]) -> Dict[str, Tuple[float, float]]:
    """Return per-trainer (avg_pts_per_badge, deck_diversity_score) in one pass."""
    counts, points, decks = _collect_trainer_stats(badges)
    return {
        t: (points[t] / counts[t], len(decks[t]) ** 2 / counts[t])
        for t in counts
    }


__all__ = [
    'TIER_WEIGHTS', 'normalize_value', 'badge_points', 'weighted_leaderboard',
    'avg_points_per_badge', 'deck_diversity_score', 'trainer_extras',
]
