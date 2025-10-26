"""Utility helpers for badge calculations and metadata."""
from __future__ import annotations

import datetime
from typing import Optional

TIER_WEIGHTS = {
    'locals': 1,
    'online': 1,
    'league challenge': 2,
    'league cup': 3,
    'regionals': 5,
    'internationals': 5,
    'worlds': 5,
}


def season_start(date: datetime.date) -> datetime.date:
    """Return the first day of the season that contains ``date``."""
    if date.month >= 7:
        return datetime.date(date.year, 7, 1)
    return datetime.date(date.year - 1, 7, 1)


def season_bounds(season_year: int) -> tuple[datetime.date, datetime.date]:
    """Return the inclusive start and exclusive end date for a season.

    ``season_year`` is the year the season ends, matching the UI (e.g. ``2024``
    represents the season that runs from July 1, 2023 through June 30, 2024).
    """
    start = datetime.date(season_year - 1, 7, 1)
    end = datetime.date(season_year, 7, 1)
    return start, end


def tier_points(tier: Optional[str]) -> int:
    """Return the point value for a tier name."""
    if not tier:
        return 0
    return TIER_WEIGHTS.get(tier.lower(), 0)
