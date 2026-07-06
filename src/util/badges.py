"""Utility helpers for badge calculations and metadata.

Season date math lives in :mod:`util.seasons` and is re-exported here for
backwards compatibility with existing imports. Tier weights are defined here as
the single source of truth (imported by :mod:`util.leaderboard`).
"""
from __future__ import annotations

import math
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


# ---------------------------------------------------------------------------
# Placement-based badge breakpoints (2027+ event seasons)
# ---------------------------------------------------------------------------
# How far down the final standings a badge reaches, scaling with attendance.
# ``(max_players, top_n)`` rows, checked in order: the first row whose
# ``max_players`` covers the field size gives the cutoff. Fields larger than the
# last row use ``BADGE_CUTOFF_CAP``. This is the single place to tune the curve.
#
# See rules/2027.md. The 65+ tier is capped at Top 8; players sharing 8th
# place's record / the full asymmetrical cut are a manual call the admin makes,
# since we don't record match results.
BADGE_BREAKPOINTS = [
    (16, 1),   # up to 16 players -> 1st only
    (32, 2),   # 17-32 -> Top 2
    (64, 4),   # 33-64 -> Top 4
]
BADGE_CUTOFF_CAP = 8   # 65+ players -> Top 8


def badge_cutoff(players) -> int:
    """Return the top-N placement that earns a badge for a field of ``players``.

    Falls back to 1st-only when the player count is missing or unparseable.
    """
    try:
        n = int(players)
    except (TypeError, ValueError):
        n = 0
    for max_players, top_n in BADGE_BREAKPOINTS:
        if n <= max_players:
            return top_n
    return BADGE_CUTOFF_CAP


def earns_badge(players, placement) -> bool:
    """Return True if ``placement`` earns a badge for a field of ``players``."""
    try:
        place = int(placement)
    except (TypeError, ValueError):
        return False
    return 1 <= place <= badge_cutoff(players)


# ---------------------------------------------------------------------------
# How much of the standings to record
# ---------------------------------------------------------------------------
# We record every badge earner plus a few notable non-earners. Two anchors, and
# we record to the deeper of them so the extra data-entry stays small:
#   * "one loss or better" ~= rounds + 1 players. From the binomial: players at
#     exactly k losses after R rounds ~= C(R, k) (since a full bracket has
#     N ~= 2**R), so <=1 loss ~= C(R,0) + C(R,1) = 1 + R. Going to two losses
#     balloons (C(R,2) = R(R-1)/2), so we don't -- except for...
#   * the top cut. When a cut is run, its bottom seed can be a two-loss record
#     (e.g. 4-2), and those should be recorded even though they miss the one-loss
#     line. The cut size bounds this to a handful.

# Typical single-elimination top-cut size by field, matching rules/2027.md.
_TOP_CUT_BREAKPOINTS = [
    (12, 0),   # < 13 players: usually no cut
    (20, 4),   # 13-20: Top 4
]
_TOP_CUT_CAP = 8   # 21+ players: Top 8


def swiss_rounds(players) -> int:
    """Number of Swiss rounds for a field of ``players`` (``ceil(log2 n)``)."""
    try:
        n = int(players)
    except (TypeError, ValueError):
        return 0
    if n < 2:
        return 0
    return math.ceil(math.log2(n))


def top_cut_size(players) -> int:
    """Typical top-cut size for a field of ``players`` (0 when no cut is run)."""
    try:
        n = int(players)
    except (TypeError, ValueError):
        return 0
    for max_players, size in _TOP_CUT_BREAKPOINTS:
        if n <= max_players:
            return size
    return _TOP_CUT_CAP


def suggested_record_count(players) -> int:
    """Roughly how many finishers to record for a Swiss-only event: badge earners
    plus the other "one loss or better" finishers (``rounds + 1``), floored at the
    badge cutoff so earners are always covered. 0 when unknown.

    Events that run a single-elimination top cut want the full cut instead (see
    :func:`top_cut_size`); that's surfaced as guidance rather than baked in here,
    since whether a cut was run can't be inferred from the field size.
    """
    rounds = swiss_rounds(players)
    if rounds < 1:
        return 0
    return max(badge_cutoff(players), rounds + 1)


def suggested_record_threshold(players) -> Optional[str]:
    """A human 'record to beat' (one loss), e.g. ``'4-1'`` for a 5-round event."""
    rounds = swiss_rounds(players)
    if rounds < 2:
        return None
    return f'{rounds - 1}-1'
