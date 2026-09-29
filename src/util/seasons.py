"""Central configuration and helpers for badge seasons.

This module is the single source of truth for season metadata: which years
exist, what mode each uses, where its rules live, which data file backs it,
and its date bounds. Adding a new season is a single entry in :data:`SEASONS`.

Season keys are normally named by the year the season *ends*, matching the UI:
season ``2026`` runs from July 1, 2025 through June 30, 2026. Pokemon moved to
a September-August season structure starting with the 2027 season, with a
three-month "off" quarter (roughly June-August) for NAIC/Worlds built into the
end of each season. A key may also be a short string (e.g. a stub season
covering a gap between two boundary conventions) -- anything hashable works, as
long as its config carries an explicit ``label``.
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
#   start/end -- inclusive/exclusive date bounds. Badges are scoped to these
#                (even for a dedicated data_file) unless the scope is OVERALL.
#   label     -- display label for the season selector, rules heading, etc.
SEASONS = {
    2026: {
        'mode': 'badges',
        'rules': '2026.md',
        'data_file': None,
        'start': datetime.date(2025, 7, 1),
        'end': datetime.date(2026, 7, 1),
        'label': '2026 Season',
    },
    # Gap between the legacy July-June boundary (2026 and earlier) and the new
    # September-August boundary (2027 and later): Pokemon's new quarter
    # structure doesn't cover July-August 2026, so it's its own short season
    # rather than silently folded into either neighbor. Shares the events-mode
    # 2027 data file -- events recorded July-August 2026 already live there.
    '2026-offseason': {
        'mode': 'events',
        'rules': None,
        'data_file': 'events_2027.jsonl',
        'start': datetime.date(2026, 7, 1),
        'end': datetime.date(2026, 9, 1),
        'label': 'Offseason 2026',
    },
    2027: {
        'mode': 'events',
        'rules': '2027.md',
        'data_file': 'events_2027.jsonl',
        'start': datetime.date(2026, 9, 1),
        'end': datetime.date(2027, 9, 1),
        'label': '2027 Season',
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
    """Return the first day (July 1) of the legacy-boundary season containing
    ``date``. Only used as a last-resort fallback -- see :func:`season_bounds`
    for the per-season-configured bounds actually used by the app.
    """
    if date.month >= 7:
        return datetime.date(date.year, 7, 1)
    return datetime.date(date.year - 1, 7, 1)


def season_year_for_date(date: datetime.date) -> int:
    """Return the legacy-boundary season year (ending year) for a given date."""
    return season_start(date).year + 1


def season_bounds(season_year) -> Tuple[datetime.date, datetime.date]:
    """Return the inclusive start and exclusive end date for a season.

    Configured seasons use their own ``start``/``end``. An unconfigured
    (integer) season year falls back to the legacy July-June boundary.
    """
    cfg = SEASONS.get(season_year)
    if cfg is not None:
        return cfg['start'], cfg['end']
    return datetime.date(season_year - 1, 7, 1), datetime.date(season_year, 7, 1)


def quarter_start(date: datetime.date, anchor_month: int) -> datetime.date:
    """Return the start of the 3-month quarter block containing ``date``,
    where quarters begin at ``anchor_month`` and repeat every 3 months.
    """
    date_index = date.year * 12 + (date.month - 1)
    anchor_index_this_cycle = date.year * 12 + (anchor_month - 1)
    months_since_anchor = (date_index - anchor_index_this_cycle) % 12
    quarter_index = date_index - months_since_anchor + (months_since_anchor // 3) * 3
    return datetime.date(quarter_index // 12, quarter_index % 12 + 1, 1)


def next_quarter_start(date: datetime.date, anchor_month: int) -> datetime.date:
    """Return the start date of the quarter following ``date``'s quarter."""
    qs = quarter_start(date, anchor_month)
    next_index = qs.year * 12 + (qs.month - 1) + 3
    return datetime.date(next_index // 12, next_index % 12 + 1, 1)


def quarter_anchor_month(season_year) -> int:
    """Return the month a season's quarters are anchored to (its start month)."""
    start, _ = season_bounds(season_year)
    return start.month


def quarter_label(season_year, start: datetime.date) -> str:
    """Return a human readable label for a quarter, e.g. '2026 July - September'."""
    anchor_month = quarter_anchor_month(season_year)
    end = next_quarter_start(start, anchor_month) - datetime.timedelta(days=1)
    _, season_end = season_bounds(season_year)
    season_last_day = season_end - datetime.timedelta(days=1)
    if season_last_day < end:
        # A short season (e.g. a gap season) can end mid-quarter -- don't
        # claim months it doesn't actually cover.
        end = season_last_day
    prefix = season_year if isinstance(season_year, int) else season_label(season_year)
    return f"{prefix} {start.strftime('%B')} - {end.strftime('%B')}"


# ---------------------------------------------------------------------------
# Config lookups
# ---------------------------------------------------------------------------
def available_seasons() -> List:
    """Return configured season keys, most recent first (by season start date)."""
    return sorted(SEASONS, key=lambda y: SEASONS[y]['start'], reverse=True)


def nav_season_options() -> List[dict]:
    """Dropdown options for the global season selector: Overall + each season."""
    return [{'label': 'Overall', 'value': OVERALL}] + [
        {'label': get_season(y).get('label') or f'{y} Season', 'value': y}
        for y in available_seasons()
    ]


def season_label(value) -> str:
    """Human label for a selector value ('Overall' or a season's configured label)."""
    if is_overall(value):
        return 'Overall'
    resolved = resolve_season(value)
    return get_season(resolved).get('label') or f'{resolved} Season'


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
    seasons = available_seasons()  # newest first
    for year in seasons:
        if season_has_data(year):
            return year
    return seasons[0] if seasons else season_year_for_date(datetime.date.today())


def resolve_season(value):
    """Coerce a query-string/param value to a valid configured season key.

    Falls back to the current season for missing or unknown values. Season
    keys aren't always integers (e.g. a gap season may use a string key), so
    this matches by value first, then by string form (query-string params
    always arrive as strings).
    """
    if value in SEASONS:
        return value
    for key in SEASONS:
        if str(key) == str(value):
            return key
    return current_season()


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
    """Return the backing data file path for a season (falls back to the default).

    A season's configured ``data_file`` is a bare filename; resolve it against the
    data directory so it lands alongside the default file (see util.data.DATA_DIR).
    """
    configured = get_season(season_year).get('data_file')
    return util.data.data_path(configured) if configured else util.data.FILENAME


def rules_path_for(season_year: int) -> Optional[str]:
    """Return the absolute path to a season's rules markdown, if it exists."""
    rules = get_season(season_year).get('rules')
    if not rules:
        return None
    path = os.path.join(_RULES_DIR, rules)
    return path if os.path.exists(path) else None


def data_files() -> dict:
    """Return ``{filename: mode}`` for every distinct data file in play.

    Single source of truth for anything that needs to touch every season's
    file -- the overall (all-time) read below, and the admin mass-edit tool
    (:mod:`util.mass_edit`), which has to find every raw record mentioning a
    trainer or deck no matter which file/mode it lives in.
    """
    files: dict = {}
    for year in SEASONS:
        files.setdefault(data_file_for(year), mode_for(year))
    files.setdefault(util.data.FILENAME, 'badges')
    return files


def exportable_files() -> List[dict]:
    """Every distinct data file this app is willing to serve/export, labeled.

    Single source of truth for the downloads admin page and the
    ``/api/export-badges`` allowlist (see app.py) -- a newly configured
    season's data file becomes downloadable automatically.
    """
    seen = set()
    out = []
    for year in available_seasons():
        path = data_file_for(year)
        name = os.path.basename(path)
        if name in seen:
            continue
        seen.add(name)
        out.append({'label': season_label(year), 'filename': name, 'path': path})
    default_name = os.path.basename(util.data.FILENAME)
    if default_name not in seen:
        out.append({'label': 'Default badges file', 'filename': default_name, 'path': util.data.FILENAME})
    return out


# ---------------------------------------------------------------------------
# Season-aware reads
# ---------------------------------------------------------------------------
def _read_normalized(filename: str, mode: str, earned_only: bool = True) -> List[dict]:
    """Read a data file and normalize its records to badge dicts."""
    records = util.data.read_data_from_file(filename)
    badges, warnings = util.normalize.normalize_records(records, mode, earned_only=earned_only)
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


def _read_season(season, earned_only: bool) -> List[dict]:
    """Shared read for :func:`read_badges` and :func:`read_participants`."""
    if is_overall(season):
        # Read each distinct data file once, using that file's season mode.
        badges: List[dict] = []
        for filename, mode in data_files().items():
            badges.extend(_read_normalized(filename, mode, earned_only))
        return _sort_badges(badges)

    season_year = resolve_season(season)
    badges = _read_normalized(data_file_for(season_year), mode_for(season_year), earned_only)
    # Isolate by date even for a dedicated data_file: a file can carry records
    # (e.g. dev/test data) outside its season's configured bounds, and those
    # shouldn't count toward that season.
    start, end = season_bounds(season_year)
    badges = [b for b in badges if b.get('date') and start <= b['date'] < end]
    return _sort_badges(badges)


def read_badges(season: Optional[int] = None) -> List[dict]:
    """Return normalized badges.

    With no ``season`` (or ``OVERALL``), returns badges across every configured
    season -- the all-time view. With a specific ``season``, returns just that
    season's badges, filtered to its configured date bounds.
    """
    return _read_season(season, earned_only=True)


def read_participants(season: Optional[int] = None) -> List[dict]:
    """Return badge-shaped records for *everyone* who played, badge or not.

    Same scoping as :func:`read_badges`, but events-mode standings contribute
    every finisher instead of only badge earners (each record keeps its
    ``placement`` and ``earned_badge``). Use this to populate admin pickers so a
    trainer or deck first seen in a non-badge finish is suggested next time;
    use :func:`read_badges` for anything that counts or displays badges.
    """
    return _read_season(season, earned_only=False)


def read_events(season: Optional[int] = None) -> List[dict]:
    """Return raw event records (with standings) for events-mode seasons.

    Powers the event admin flow (which wants every event in the active
    events-mode file, not just ones within a particular season's date bounds,
    so a past event stays editable) and the home recap card (which the caller
    should further filter to its season's bounds -- see
    :func:`season_bounds` -- since multiple events-mode seasons can share one
    data file). Badges-mode seasons have no events, so they contribute
    nothing. With ``OVERALL``/``None`` this unions events across every
    distinct events-mode data file (deduplicated, since seasons can share one).
    """
    if is_overall(season):
        events: List[dict] = []
        for filename, mode in data_files().items():
            if mode == 'events':
                events.extend(util.data.read_data_from_file(filename))
        return _sort_badges(events)

    season_year = resolve_season(season)
    if mode_for(season_year) != 'events':
        return []
    return util.data.read_data_from_file(data_file_for(season_year))
