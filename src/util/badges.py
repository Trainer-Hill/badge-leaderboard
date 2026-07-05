"""Utility helpers for badge calculations and metadata.

Season date math lives in :mod:`util.seasons` and is re-exported here for
backwards compatibility with existing imports. Tier weights are defined here as
the single source of truth (imported by :mod:`util.leaderboard`).
"""
from __future__ import annotations

from typing import Optional

# Re-exported so existing ``from util.badges import season_bounds`` keeps working.
from util.seasons import season_bounds, season_start, season_year_for_date  # noqa: F401

# Badge tiers mapped to their point values, used to break leaderboard ties.
# Global for now; a per-season override can move into util.seasons.SEASONS later.
TIER_WEIGHTS = {
    'locals': 1,
    'online': 1,
    'league challenge': 2,
    'league cup': 3,
    'regionals': 5,
    'internationals': 5,
    'worlds': 5,
}


def tier_points(tier: Optional[str]) -> int:
    """Return the point value for a tier name."""
    if not tier:
        return 0
    return TIER_WEIGHTS.get(tier.lower(), 0)
