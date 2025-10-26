"""Convert badge JSONL data into time-series CSV exports."""
from __future__ import annotations

import argparse
import csv
import datetime
from collections import defaultdict
from itertools import groupby
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence

from util.badges import season_bounds, tier_points

from util.data import FILENAME as DEFAULT_DATA_FILE, read_data_from_file

GROUP_BY_CHOICES: Sequence[str] = ('trainer', 'deck')


def _default_input_path() -> Path:
    candidate = Path(DEFAULT_DATA_FILE)
    if candidate.exists():
        return candidate
    project_root_example = Path(__file__).resolve().parent.parent / DEFAULT_DATA_FILE
    return project_root_example


def _parse_date(value: Optional[str]) -> Optional[datetime.date]:
    if not value:
        return None
    try:
        return datetime.date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f'invalid date: {value}') from exc


def _badge_entity(badge: Dict, group_by: str) -> Optional[str]:
    if group_by == 'trainer':
        return badge.get('trainer')
    if group_by == 'deck':
        deck = badge.get('deck')
        if isinstance(deck, dict):
            return deck.get('name') or deck.get('id')
        return deck
    raise ValueError(f'unsupported group-by value: {group_by}')


def _badge_date(badge: Dict) -> Optional[datetime.date]:
    date_value = badge.get('date')
    if isinstance(date_value, datetime.date):
        return date_value
    if isinstance(date_value, str):
        try:
            return datetime.date.fromisoformat(date_value)
        except ValueError:
            return None
    return None


def _filter_badges(
    badges: Iterable[Dict],
    *,
    start: Optional[datetime.date] = None,
    end: Optional[datetime.date] = None,
) -> List[Dict]:
    filtered: List[Dict] = []
    for badge in badges:
        badge_date = _badge_date(badge)
        if not badge_date:
            continue
        if start and badge_date < start:
            continue
        if end and badge_date >= end:
            continue
        filtered.append({**badge, 'date': badge_date})
    return filtered


def _score_value(badges: int, points: int) -> int:
    """Return a sortable score that respects badge counts then points.

    Each badge contributes ``SCORE_BADGE_WEIGHT`` to the score so badge totals
    always outrank points. Points are added directly to break ties between
    entities with the same number of badges.
    """

    return badges + points*0.001


def _timeline_rows(
    badges: List[Dict],
    group_by: str,
) -> List[Dict[str, object]]:
    records: List[Dict[str, object]] = []
    counts: Dict[str, int] = defaultdict(int)
    points: Dict[str, int] = defaultdict(int)
    sorted_badges = sorted(
        badges,
        key=lambda b: (
            b['date'],
            _badge_entity(b, group_by) or '',
        ),
    )

    for badge_date, date_group in groupby(sorted_badges, key=lambda b: b['date']):
        updated_entities = set()
        for badge in date_group:
            entity = _badge_entity(badge, group_by)
            if not entity:
                continue
            counts[entity] += 1
            points[entity] += tier_points(badge.get('tier'))
            updated_entities.add(entity)

        if not counts:
            continue

        ranking = sorted(
            counts,
            key=lambda entity: (
                -counts[entity],
                -points[entity],
                str(entity).lower(),
            ),
        )

        for rank, entity in enumerate(ranking, start=1):
            records.append(
                {
                    'date': badge_date.isoformat(),
                    'entity': entity,
                    'badges': counts[entity],
                    'points': points[entity],
                    'score': _score_value(counts[entity], points[entity]),
                    'rank': rank,
                    'updated': entity in updated_entities,
                }
            )

    return records


def _cumulative_table(
    records: List[Dict[str, object]],
    *,
    value_field: str = 'score',
) -> tuple[List[Dict[str, object]], List[str]]:
    """Pivot long-form timeline records into cumulative date rows.

    The returned fieldnames always include ``date`` followed by one column per
    entity ordered by when the entity first appeared in the ranking.
    """

    if not records:
        return [], ['date']

    seen_entities: List[str] = []
    rows_by_date: Dict[str, Dict[str, object]] = {}

    for record in records:
        entity = str(record['entity'])
        if entity not in seen_entities:
            seen_entities.append(entity)

        date = str(record['date'])
        row = rows_by_date.setdefault(date, {'date': date})
        row[entity] = record.get(value_field, record.get('badges'))

    fieldnames = ['date', *seen_entities]
    sorted_dates = sorted(rows_by_date)
    rows: List[Dict[str, object]] = []

    last_values: Dict[str, object] = {entity: 0 for entity in seen_entities}
    for date in sorted_dates:
        row = rows_by_date[date]
        output_row: Dict[str, object] = {'date': row['date']}
        for entity in seen_entities:
            value = row.get(entity, last_values[entity])
            last_values[entity] = value
            output_row[entity] = value
        rows.append(output_row)

    return rows, fieldnames


def _resolve_date_filters(args: argparse.Namespace) -> tuple[Optional[datetime.date], Optional[datetime.date]]:
    start = args.start_date
    end = args.end_date
    if args.season:
        season_start, season_end = season_bounds(args.season)
        start = max(start, season_start) if start else season_start
        end = min(end, season_end) if end else season_end
    return start, end


def parse_arguments(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Export badge data as time series CSV.')
    parser.add_argument('output', type=Path, help='Destination CSV file.')
    parser.add_argument('-i', '--input', type=Path, default=_default_input_path(), help='Source JSONL file (defaults to TH_BL_FILE or example data).')
    parser.add_argument('--group-by', choices=GROUP_BY_CHOICES, default='trainer', help='Group badges by trainer or deck.')
    parser.add_argument('--season', type=int, help='Limit results to a season year (e.g. 2024 for July 2023-June 2024).')
    parser.add_argument('--start-date', type=_parse_date, help='Filter badges on or after this ISO date (YYYY-MM-DD).')
    parser.add_argument('--end-date', type=_parse_date, help='Filter badges before this ISO date (YYYY-MM-DD).')
    parser.add_argument('--cumulative', action='store_true', help='Pivot output into cumulative date rows (wide format).')
    return parser.parse_args(list(argv) if argv is not None else None)


def load_badges(path: Path) -> List[Dict]:
    return read_data_from_file(str(path))


def export_time_series(args: argparse.Namespace) -> tuple[List[Dict[str, object]], List[str]]:
    badges = load_badges(args.input)
    if not badges:
        if args.cumulative:
            return [], ['date']
        return [], ['date', 'entity', 'badges', 'points', 'score', 'rank', 'updated']

    start, end = _resolve_date_filters(args)
    filtered = _filter_badges(badges, start=start, end=end)
    records = _timeline_rows(filtered, args.group_by)
    if args.cumulative:
        return _cumulative_table(records)
    return records, ['date', 'entity', 'badges', 'points', 'score', 'rank', 'updated']


def write_csv(rows: List[Dict[str, object]], path: Path, fieldnames: Sequence[str]) -> None:
    with path.open('w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main(argv: Optional[Iterable[str]] = None) -> None:
    args = parse_arguments(argv)
    rows, fieldnames = export_time_series(args)
    write_csv(rows, args.output, fieldnames)


if __name__ == '__main__':
    main()
