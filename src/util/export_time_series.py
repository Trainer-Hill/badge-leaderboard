"""Convert badge JSONL data into time-series CSV exports."""
from __future__ import annotations

import argparse
import csv
import datetime
import json
from collections import defaultdict
from itertools import groupby
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import th_helpers.components.deck_label

from util.badges import season_bounds, tier_points
from util.data import FILENAME as DEFAULT_DATA_FILE, read_data_from_file

GROUP_BY_CHOICES: Sequence[str] = ('trainer', 'deck')

# Score weighting constant - makes it explicit what the magic number means
POINTS_WEIGHT = 0.001


def _default_input_path() -> Path:
    """Get default input path, checking working dir first, then project root."""
    candidate = Path(DEFAULT_DATA_FILE)
    if candidate.exists():
        return candidate
    project_root_example = Path(__file__).resolve().parent.parent / DEFAULT_DATA_FILE
    return project_root_example


def _parse_date(value: Optional[str]) -> Optional[datetime.date]:
    """Parse ISO date string for argparse."""
    if not value:
        return None
    try:
        return datetime.date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f'invalid date: {value}') from exc


def _badge_entity(badge: Dict[str, Any], group_by: str) -> Optional[str]:
    """Extract entity identifier from badge based on grouping strategy."""
    if group_by == 'trainer':
        return badge.get('trainer')
    if group_by == 'deck':
        deck = badge.get('deck')
        if isinstance(deck, dict):
            return deck.get('name') or deck.get('id')
        return deck
    raise ValueError(f'unsupported group-by value: {group_by}')


def _badge_date(badge: Dict[str, Any]) -> Optional[datetime.date]:
    """Extract and normalize date from badge."""
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
    badges: Iterable[Dict[str, Any]],
    *,
    start: Optional[datetime.date] = None,
    end: Optional[datetime.date] = None,
) -> List[Dict[str, Any]]:
    """Filter badges by date range, normalizing dates to date objects."""
    filtered: List[Dict[str, Any]] = []
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


def _score_value(badges: int, points: int) -> float:
    """Return a sortable score that respects badge counts then points.

    Each badge contributes 1.0 to the score so badge totals always outrank 
    points. Points are weighted minimally to break ties between entities 
    with the same number of badges.
    """
    return badges + points * POINTS_WEIGHT


def _icon_to_url(icon: Any) -> Optional[str]:
    """Convert icon identifier to full URL."""
    if not isinstance(icon, str):
        return None
    icon_value = icon.strip()
    if not icon_value:
        return None
    if icon_value.startswith(('http://', 'https://')):
        return icon_value
    return th_helpers.components.deck_label.get_pokemon_icon(icon_value)


def _resolve_deck_image_url(
    badge: Dict[str, Any],
    entity: str,
    image_map: Optional[Dict[str, str]] = None,
) -> Optional[str]:
    """Resolve deck image URL from badge, entity, or image map."""
    deck = badge.get('deck') if isinstance(badge.get('deck'), dict) else None
    identifiers: List[str] = [entity]
    if deck:
        deck_name = deck.get('name')
        deck_id = deck.get('id')
        if deck_name:
            identifiers.append(str(deck_name))
        if deck_id:
            identifiers.append(str(deck_id))

    # Check image map first
    if image_map:
        for identifier in identifiers:
            if identifier in image_map:
                mapped = image_map[identifier]
                if mapped:
                    return mapped

    # Fall back to deck icons
    if deck:
        for icon in deck.get('icons') or []:
            url = _icon_to_url(icon)
            if url:
                return url
    
    return None


def _timeline_rows(
    badges: List[Dict[str, Any]],
    group_by: str,
    *,
    image_map: Optional[Dict[str, str]] = None,
) -> List[Dict[str, Any]]:
    """Generate timeline records with cumulative badge counts and rankings."""
    records: List[Dict[str, Any]] = []
    counts: Dict[str, int] = defaultdict(int)
    points: Dict[str, int] = defaultdict(int)
    
    sorted_badges = sorted(
        badges,
        key=lambda b: (b['date'], _badge_entity(b, group_by) or ''),
    )
    
    deck_image_urls: Optional[Dict[str, Optional[str]]] = (
        {} if group_by == 'deck' else None
    )

    for badge_date, date_group in groupby(sorted_badges, key=lambda b: b['date']):
        updated_entities: set[str] = set()
        
        # Process all badges for this date
        for badge in date_group:
            entity = _badge_entity(badge, group_by)
            if not entity:
                continue
            counts[entity] += 1
            points[entity] += tier_points(badge.get('tier'))
            updated_entities.add(entity)

            # Cache deck image URLs
            if deck_image_urls is not None and entity not in deck_image_urls:
                deck_image_urls[entity] = _resolve_deck_image_url(
                    badge, entity, image_map=image_map
                )

        if not counts:
            continue

        # Rank entities by badges (desc), points (desc), then name (asc)
        ranking = sorted(
            counts,
            key=lambda entity: (-counts[entity], -points[entity], str(entity).lower()),
        )

        # Create record for each entity
        for rank, entity in enumerate(ranking, start=1):
            record: Dict[str, Any] = {
                'date': badge_date.isoformat(),
                'entity': entity,
                'badges': counts[entity],
                'points': points[entity],
                'score': _score_value(counts[entity], points[entity]),
                'rank': rank,
                'updated': entity in updated_entities,
            }
            if deck_image_urls is not None:
                record['image_url'] = deck_image_urls.get(entity)
            records.append(record)

    return records


def _cumulative_table(
    records: List[Dict[str, Any]],
    *,
    value_field: str = 'score',
    group_by: str,
    image_map: Optional[Dict[str, str]] = None,
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Pivot long-form timeline records into cumulative entity rows (wide format).

    Returns:
        Tuple of (rows, fieldnames) where each row represents an entity with 
        their values across all dates.
    """
    if not records:
        base_fields = ['entity']
        if group_by == 'deck' or image_map:
            base_fields.append('image_url')
        return [], base_fields

    include_image_urls = group_by == 'deck' or bool(image_map)
    seen_entities: List[str] = []
    seen_dates: List[str] = []
    data_by_entity: Dict[str, Dict[str, Any]] = {}
    image_urls: Dict[str, Optional[str]] = {}

    # Collect all entities, dates, and values
    for record in records:
        entity = str(record['entity'])
        date = str(record['date'])
        
        if entity not in seen_entities:
            seen_entities.append(entity)
        if date not in seen_dates:
            seen_dates.append(date)
        
        if entity not in data_by_entity:
            data_by_entity[entity] = {}
        
        # Get value from specified field, fallback to badges
        data_by_entity[entity][date] = record.get(value_field, record.get('badges', 0))
        
        # Cache image URLs
        if include_image_urls and entity not in image_urls:
            image_value = record.get('image_url')
            if not image_value and image_map:
                image_value = image_map.get(entity)
            image_urls[entity] = image_value

    # Sort dates chronologically
    seen_dates.sort()
    
    # Build fieldnames
    fieldnames: List[str] = ['entity']
    if include_image_urls:
        fieldnames.append('image_url')
    fieldnames.extend(seen_dates)
    
    # Build rows: one per entity with cumulative values
    rows: List[Dict[str, Any]] = []
    for entity in seen_entities:
        row: Dict[str, Any] = {'entity': entity}
        
        if include_image_urls:
            row['image_url'] = image_urls.get(entity, '')
        
        # Forward-fill values across dates
        last_value: Any = 0
        for date in seen_dates:
            if date in data_by_entity[entity]:
                last_value = data_by_entity[entity][date]
            row[date] = last_value
        
        rows.append(row)

    return rows, fieldnames


def _resolve_date_filters(
    args: argparse.Namespace
) -> Tuple[Optional[datetime.date], Optional[datetime.date]]:
    """Resolve date filters from CLI args, incorporating season bounds if specified."""
    start = args.start_date
    end = args.end_date
    
    if args.season:
        season_start, season_end = season_bounds(args.season)
        start = max(start, season_start) if start else season_start
        end = min(end, season_end) if end else season_end
    
    return start, end


def parse_arguments(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Export badge data as time series CSV.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        'output',
        type=Path,
        help='Destination CSV file.',
    )
    parser.add_argument(
        '-i', '--input',
        type=Path,
        default=_default_input_path(),
        help='Source JSONL file (defaults to TH_BL_FILE or example data).',
    )
    parser.add_argument(
        '--group-by',
        choices=GROUP_BY_CHOICES,
        default='trainer',
        help='Group badges by trainer or deck (default: trainer).',
    )
    parser.add_argument(
        '--season',
        type=int,
        help='Limit results to a season year (e.g. 2024 for July 2023-June 2024).',
    )
    parser.add_argument(
        '--start-date',
        type=_parse_date,
        help='Filter badges on or after this ISO date (YYYY-MM-DD).',
    )
    parser.add_argument(
        '--end-date',
        type=_parse_date,
        help='Filter badges before this ISO date (YYYY-MM-DD).',
    )
    parser.add_argument(
        '--cumulative',
        action='store_true',
        help='Pivot output into cumulative date columns (wide format).',
    )
    parser.add_argument(
        '--image-map',
        type=Path,
        help='Optional JSON file mapping entities to image URLs.',
    )
    return parser.parse_args(list(argv) if argv is not None else None)


def load_badges(path: Path) -> List[Dict[str, Any]]:
    """Load badge data from JSONL file."""
    return read_data_from_file(str(path))


def _load_image_map(path: Optional[Path]) -> Dict[str, str]:
    """Load and normalize image map from JSON file."""
    if not path:
        return {}
    
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f'Failed to load image map from {path}: {exc}') from exc
    
    if not isinstance(data, dict):
        raise ValueError('image map must be a JSON object mapping entities to URLs')
    
    image_map: Dict[str, str] = {}
    for key, value in data.items():
        key_str = str(key) if not isinstance(key, str) else key
        url: Optional[str] = None
        
        # Handle various value formats
        if isinstance(value, str):
            url = value
        elif isinstance(value, (list, tuple)):
            # Find first non-empty string
            for candidate in value:
                if isinstance(candidate, str) and candidate.strip():
                    url = candidate.strip()
                    break
        elif isinstance(value, dict):
            # Extract from common image field names
            image_value = value.get('image') or value.get('image_url') or value.get('url')
            if isinstance(image_value, str):
                url = image_value
        
        if url and url.strip():
            image_map[key_str] = url.strip()
    
    return image_map


def export_time_series(
    args: argparse.Namespace
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Generate time series data from badges based on CLI arguments.
    
    Returns:
        Tuple of (rows, fieldnames) for CSV output.
    """
    badges = load_badges(args.input)
    image_map = _load_image_map(getattr(args, 'image_map', None))
    
    # Define base fieldnames for non-cumulative output
    base_fieldnames: List[str] = ['date', 'entity']
    if args.group_by == 'deck' or image_map:
        base_fieldnames.append('image_url')
    base_fieldnames.extend(['badges', 'points', 'score', 'rank', 'updated'])
    
    if not badges:
        return [], (['entity', 'image_url'] if args.cumulative and (args.group_by == 'deck' or image_map) 
                   else ['entity'] if args.cumulative 
                   else base_fieldnames)

    # Filter and process badges
    start, end = _resolve_date_filters(args)
    filtered = _filter_badges(badges, start=start, end=end)
    records = _timeline_rows(filtered, args.group_by, image_map=image_map)
    
    if args.cumulative:
        return _cumulative_table(records, group_by=args.group_by, image_map=image_map)
    
    return records, base_fieldnames


def write_csv(
    rows: List[Dict[str, Any]],
    path: Path,
    fieldnames: Sequence[str]
) -> None:
    """Write rows to CSV file with specified fieldnames."""
    with path.open('w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main(argv: Optional[Iterable[str]] = None) -> None:
    """Main entry point."""
    args = parse_arguments(argv)
    rows, fieldnames = export_time_series(args)
    write_csv(rows, args.output, fieldnames)
    print(f"Exported {len(rows)} rows to {args.output}")


if __name__ == '__main__':
    main()
