"""Central configuration and helpers for badge seasons.

This module is the single source of truth for season metadata: which years
exist, what mode each uses, where its rules live, and which data file backs it.
Adding a new season is a single entry in :data:`SEASONS`.

Season years are named by the year the season *ends*, matching the UI: season
``2026`` runs from July 1, 2025 through June 30, 2026.
"""
from __future__ import annotations

import datetime
import logging
import os
from typing import List, Optional, Tuple

import util.data
import util.normalize

logger = logging.getLogger(__name__)

_SRC_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_RULES_DIR = os.path.join(_SRC_DIR, 'rules')

# ---------------------------------------------------------------------------
# Season configuration
# ---------------------------------------------------------------------------
# Per season:
#   mode      -- 'badges' (one badge per line) or 'events' (one event per line,
#                badges derived from standings; see util.normalize).
#   rules     -- markdown filename under src/rules/ for that season's rules.
#   data_file -- backing JSONL, relative to src/. None uses the default file
#                (``util.data.FILENAME``, controlled by the TH_BL_FILE env var).
SEASONS = {
    2026: {
        'mode': 'badges',
        'rules': '2026.md',
        'data_file': None,
    },
    2027: {
        'mode': 'events',
        'rules': '2026.md',  # TODO: add rules/2027.md when the ruleset is finalized
        'data_file': 'events_2027.jsonl',
    },
}

# Config used when a season year is requested but not declared above.
_DEFAULT_SEASON_CONFIG = {'mode': 'badges', 'rules': None, 'data_file': None}

# Sentinel for the cross-season "all-time" view (used by aggregate/gallery pages;
# season-only pages fall back to the current season instead).
OVERALL = 'overall'


def is_overall(value) -> bool:
    """Return True when a selector value means the all-time / all-seasons view."""
    return value is None or (isinstance(value, str) and value.lower() == OVERALL)


# ---------------------------------------------------------------------------
# Season math
# ---------------------------------------------------------------------------
def season_start(date: datetime.date) -> datetime.date:
    """Return the first day (July 1) of the season containing ``date``."""
    if date.month >= 7:
        return datetime.date(date.year, 7, 1)
    return datetime.date(date.year - 1, 7, 1)


def season_year_for_date(date: datetime.date) -> int:
    """Return the season year (ending year) for a given date."""
    return season_start(date).year + 1


def season_bounds(season_year: int) -> Tuple[datetime.date, datetime.date]:
    """Return the inclusive start and exclusive end date for a season."""
    start = datetime.date(season_year - 1, 7, 1)
    end = datetime.date(season_year, 7, 1)
    return start, end


# ---------------------------------------------------------------------------
# Config lookups
# ---------------------------------------------------------------------------
def available_seasons() -> List[int]:
    """Return configured season years, most recent first."""
    return sorted(SEASONS, reverse=True)


def nav_season_options() -> List[dict]:
    """Dropdown options for the global season selector: Overall + each season."""
    return [{'label': 'Overall', 'value': OVERALL}] + [
        {'label': f'{y} Season', 'value': y} for y in available_seasons()
    ]


def season_label(value) -> str:
    """Human label for a selector value ('Overall' or 'YYYY Season')."""
    if is_overall(value):
        return 'Overall'
    return f'{resolve_season(value)} Season'


def season_has_data(season_year: int) -> bool:
    """Return True if a season has any recorded data (events or badges)."""
    if mode_for(season_year) == 'events':
        return bool(read_events(season_year))
    return bool(read_badges(season_year))


def current_season() -> int:
    """Return the latest season that has data, so the site defaults to the
    active season rather than a newly-configured-but-empty one.

    Falls back to the latest configured season (then the calendar season).
    """
    for year in available_seasons():  # newest first
        if season_has_data(year):
            return year
    return max(SEASONS) if SEASONS else season_year_for_date(datetime.date.today())


def resolve_season(value) -> int:
    """Coerce a query-string/param value to a valid configured season year.

    Falls back to the current season for missing or unknown values.
    """
    try:
        year = int(value)
    except (TypeError, ValueError):
        return current_season()
    return year if year in SEASONS else current_season()


def resolve_scope(value):
    """Resolve a page's season scope from a selector/query value.

    An **absent** value (``None``) defaults to the current season -- a fresh
    visit lands on the active season, not all-time. An explicit ``'overall'``
    selects the all-time view; anything else resolves to a valid season year.
    """
    if value is None:
        return current_season()
    if is_overall(value):
        return OVERALL
    return resolve_season(value)


def get_season(season_year: int) -> dict:
    """Return the config dict for a season, or a badges-mode default."""
    return SEASONS.get(season_year, _DEFAULT_SEASON_CONFIG)


def mode_for(season_year: int) -> str:
    return get_season(season_year).get('mode', 'badges')


def data_file_for(season_year: int) -> str:
    """Return the backing data file for a season (falls back to the default)."""
    return get_season(season_year).get('data_file') or util.data.FILENAME


def rules_path_for(season_year: int) -> Optional[str]:
    """Return the absolute path to a season's rules markdown, if it exists."""
    rules = get_season(season_year).get('rules')
    if not rules:
        return None
    path = os.path.join(_RULES_DIR, rules)
    return path if os.path.exists(path) else None


# ---------------------------------------------------------------------------
# Season-aware reads
# ---------------------------------------------------------------------------
def _read_normalized(filename: str, mode: str) -> List[dict]:
    """Read a data file and normalize its records to badge dicts."""
    records = util.data.read_data_from_file(filename)
    badges, warnings = util.normalize.normalize_records(records, mode)
    for warning in warnings:
        logger.warning('%s: %s', filename, warning)
    return badges


def _sort_badges(badges: List[dict]) -> List[dict]:
    """Sort badges by date descending, mirroring util.data.read_data ordering."""
    return sorted(
        badges,
        key=lambda b: (b.get('date') or datetime.date.min, b.get('_line', 0)),
        reverse=True,
    )


def read_badges(season: Optional[int] = None) -> List[dict]:
    """Return normalized badges.

    With no ``season`` (or ``OVERALL``), returns badges across every configured
    season -- the all-time view. With a specific ``season``, returns just that
    season's badges -- filtered to the season's date bounds when it shares the
    default data file, or the whole file when the season has a dedicated one.
    """
    if is_overall(season):
        # Read each distinct data file once, using that file's season mode.
        files: dict = {}
        for year in SEASONS:
            files.setdefault(data_file_for(year), mode_for(year))
        files.setdefault(util.data.FILENAME, 'badges')
        badges: List[dict] = []
        for filename, mode in files.items():
            badges.extend(_read_normalized(filename, mode))
        return _sort_badges(badges)

    season_year = resolve_season(season)
    badges = _read_normalized(data_file_for(season_year), mode_for(season_year))
    if get_season(season_year).get('data_file') is None:
        # Shared default file: isolate this season by date.
        start, end = season_bounds(season_year)
        badges = [b for b in badges if b.get('date') and start <= b['date'] < end]
    return _sort_badges(badges)


def read_events(season: Optional[int] = None) -> List[dict]:
    """Return raw event records (with standings) for events-mode seasons.

    Powers the home recap card and the event admin flow. Badges-mode seasons
    have no events, so they contribute nothing. With ``OVERALL``/``None`` this
    unions events across every events-mode season.
    """
    if is_overall(season):
        events: List[dict] = []
        for year in SEASONS:
            if mode_for(year) == 'events':
                events.extend(util.data.read_data_from_file(data_file_for(year)))
        return _sort_badges(events)

    season_year = resolve_season(season)
    if mode_for(season_year) != 'events':
        return []
    return util.data.read_data_from_file(data_file_for(season_year))
