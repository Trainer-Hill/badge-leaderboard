"""Print seasonal insights from badge JSONL data to the terminal."""
from __future__ import annotations

import argparse
import datetime
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from util.badges import TIER_WEIGHTS, season_bounds, tier_points
from util.data import FILENAME as DEFAULT_DATA_FILE, read_data_from_file

TIER_ORDER = ['locals', 'online', 'league challenge', 'league cup', 'regionals', 'internationals', 'worlds']
TIER_ABBREV = {
    'locals': 'Local',
    'online': 'Online',
    'league challenge': 'LC',
    'league cup': 'Cup',
    'regionals': 'Rgls',
    'internationals': 'Intl',
    'worlds': 'Wrld',
}
LOCAL_MAX_PTS = 3  # tiers with <= this many points are "local" (includes cups)
DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']


def _is_local(tier: Optional[str]) -> bool:
    return tier_points(tier) <= LOCAL_MAX_PTS


def _badge_date(badge: Dict[str, Any]) -> Optional[datetime.date]:
    d = badge.get('date')
    if isinstance(d, datetime.date):
        return d
    if isinstance(d, str):
        try:
            return datetime.date.fromisoformat(d)
        except ValueError:
            return None
    return None


def _filter_badges(
    badges: List[Dict[str, Any]],
    *,
    start: Optional[datetime.date] = None,
    end: Optional[datetime.date] = None,
) -> List[Dict[str, Any]]:
    out = []
    for b in badges:
        d = _badge_date(b)
        if not d:
            continue
        if start and d < start:
            continue
        if end and d >= end:
            continue
        out.append({**b, 'date': d})
    return out


def _bar(count: int, total: int, width: int = 20) -> str:
    if not total:
        return '░' * width
    filled = round(count / total * width)
    return '█' * filled + '░' * (width - filled)


def _sep(width: int = 58) -> str:
    return '  ' + '─' * width


def run_insights(badges: List[Dict[str, Any]], title: str) -> None:
    if not badges:
        print("No badges found.")
        return

    dates = [b['date'] for b in badges if b.get('date')]
    min_date = min(dates)
    max_date = max(dates)

    trainers = {b.get('trainer') for b in badges if b.get('trainer')}
    stores = {b.get('store') for b in badges if b.get('store')}
    formats = Counter(str(b.get('format', 'unknown')).lower() for b in badges)
    tiers = Counter(str(b.get('tier', 'unknown')).lower() for b in badges)

    total = len(badges)
    local_count = sum(c for t, c in tiers.items() if _is_local(t))
    premier_count = total - local_count

    # ── Header ──────────────────────────────────────────────────────────────
    print()
    print('━' * 62)
    print(f'  {title}')
    print('━' * 62)
    print(f'  Badges:   {total:<6}  Date range: {min_date} → {max_date}')
    print(f'  Trainers: {len(trainers):<6}  Stores:     {len(stores)}')
    fmt_str = '  '.join(f'{fmt.title()} {cnt}' for fmt, cnt in sorted(formats.items()))
    print(f'  Formats:  {fmt_str}')

    # ── Tier breakdown ───────────────────────────────────────────────────────
    print()
    print('  TIER BREAKDOWN')
    print(_sep())
    for tier in TIER_ORDER:
        count = tiers.get(tier, 0)
        pct = count / total * 100 if total else 0
        bar = _bar(count, total, 18)
        tag = '  [local]' if _is_local(tier) else ''
        print(f'  {tier:<22} {count:>4}  ({pct:5.1f}%)  {bar}{tag}')
    unknown_tiers = {t for t in tiers if t not in TIER_ORDER}
    if unknown_tiers:
        unk_count = sum(tiers[t] for t in unknown_tiers)
        print(f'  {"(other)":<22} {unk_count:>4}')
    print()
    lp = local_count / total * 100 if total else 0
    pp = premier_count / total * 100 if total else 0
    print(f'  Local  (<3 pts):   {local_count:>4}  ({lp:.1f}%)')
    print(f'  Premier (3+ pts):  {premier_count:>4}  ({pp:.1f}%)')

    # ── Tier activity by month ───────────────────────────────────────────────
    monthly: Dict[str, Counter] = defaultdict(Counter)
    for b in badges:
        d = b['date']
        if not d:
            continue
        key = d.strftime('%Y-%m')
        tier = str(b.get('tier', 'unknown')).lower()
        monthly[key][tier] += 1

    print()
    print('  TIER ACTIVITY BY MONTH')
    print(_sep(62))
    abbrevs = [TIER_ABBREV[t] for t in TIER_ORDER]
    header_row = f"  {'Month':<9}" + ''.join(f'{a:>7}' for a in abbrevs) + f"{'Total':>7}"
    print(header_row)
    print(_sep(len(header_row) - 2))
    for month in sorted(monthly):
        counts = monthly[month]
        month_total = sum(counts.values())
        row = f"  {month:<9}"
        for tier in TIER_ORDER:
            c = counts.get(tier, 0)
            row += f'{c:>7}' if c else '      ·'
        row += f'{month_total:>7}'
        print(row)

    # ── Store popularity ─────────────────────────────────────────────────────
    store_total: Counter = Counter()
    store_local: Counter = Counter()
    store_premier: Counter = Counter()
    store_tiers: Dict[str, Counter] = defaultdict(Counter)

    for b in badges:
        store = b.get('store') or '(unknown)'
        tier = str(b.get('tier', 'unknown')).lower()
        store_total[store] += 1
        if _is_local(tier):
            store_local[store] += 1
        else:
            store_premier[store] += 1
        store_tiers[store][tier] += 1

    print()
    print('  STORE POPULARITY  (top 20)')
    name_col = min(max((len(s) for s in store_total), default=10), 35)
    print(_sep(name_col + 40))
    print(f"  {'Store':<{name_col}}  {'Total':>5}  {'Local':>5}  {'Premier':>7}  Top tier")
    print(_sep(name_col + 40))
    for store, count in store_total.most_common(20):
        top_tier = store_tiers[store].most_common(1)[0][0] if store_tiers[store] else '—'
        local = store_local.get(store, 0)
        premier = store_premier.get(store, 0)
        print(f"  {store[:name_col]:<{name_col}}  {count:>5}  {local:>5}  {premier:>7}  {top_tier}")

    # ── Day-of-week distribution ─────────────────────────────────────────────
    dow_local: Counter = Counter()
    dow_premier: Counter = Counter()
    for b in badges:
        d = b['date']
        if not d:
            continue
        tier = str(b.get('tier', '')).lower()
        if _is_local(tier):
            dow_local[d.weekday()] += 1
        else:
            dow_premier[d.weekday()] += 1

    print()
    print('  DAY-OF-WEEK  (local events)')
    print(_sep())
    local_max = max(dow_local.values()) if dow_local else 1
    for i, day in enumerate(DAYS):
        count = dow_local.get(i, 0)
        bar = _bar(count, local_max, 28)
        print(f'  {day}  {bar}  {count}')

    print()
    print('  DAY-OF-WEEK  (premier events)')
    print(_sep())
    premier_max = max(dow_premier.values()) if dow_premier else 1
    for i, day in enumerate(DAYS):
        count = dow_premier.get(i, 0)
        bar = _bar(count, premier_max, 28)
        print(f'  {day}  {bar}  {count}')

    print()


def _default_input_path() -> Path:
    candidate = Path(DEFAULT_DATA_FILE)
    if candidate.exists():
        return candidate
    return Path(__file__).resolve().parent.parent / DEFAULT_DATA_FILE


def _parse_date(value: str) -> datetime.date:
    try:
        return datetime.date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f'invalid date: {value}') from exc


def parse_arguments(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Print seasonal insights from badge JSONL data.',
    )
    parser.add_argument(
        'input',
        nargs='?',
        type=Path,
        default=_default_input_path(),
        help='Source JSONL file (defaults to TH_BL_FILE or example data).',
    )
    parser.add_argument(
        '--season',
        type=int,
        help='Limit to a season year (e.g. 2025 = Jul 2024–Jun 2025).',
    )
    parser.add_argument(
        '--start-date',
        type=_parse_date,
        help='Filter badges on or after this date (YYYY-MM-DD).',
    )
    parser.add_argument(
        '--end-date',
        type=_parse_date,
        help='Filter badges before this date (YYYY-MM-DD).',
    )
    return parser.parse_args(list(argv) if argv is not None else None)


def main(argv: Optional[Iterable[str]] = None) -> None:
    args = parse_arguments(argv)
    badges = read_data_from_file(str(args.input))

    start: Optional[datetime.date] = args.start_date
    end: Optional[datetime.date] = args.end_date

    if args.season:
        season_start, season_end = season_bounds(args.season)
        start = max(start, season_start) if start else season_start
        end = min(end, season_end) if end else season_end

    filtered = _filter_badges(badges, start=start, end=end)

    if args.season:
        title = f'INSIGHTS — Season {args.season}  ({start} → {end})'
    elif start or end:
        s = str(start) if start else '…'
        e = str(end) if end else '…'
        title = f'INSIGHTS — {s} → {e}'
    else:
        title = f'INSIGHTS — All time  ({args.input.name})'

    run_insights(filtered, title)


if __name__ == '__main__':
    main()
