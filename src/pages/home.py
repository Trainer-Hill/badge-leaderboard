import dash
import dash_bootstrap_components as dbc
import datetime
from collections import Counter
from dash import html

import components.badge
import util.data

dash.register_page(
    __name__,
    path='/'
)

def _season_start(date: datetime.date) -> datetime.date:
    """Return the start of the season for a given date."""
    if date.month >= 7:
        return datetime.date(date.year, 7, 1)
    return datetime.date(date.year - 1, 7, 1)


def _quarter_start(date: datetime.date) -> datetime.date:
    """Return the beginning of the quarter for a given date."""
    m = date.month
    y = date.year
    if 7 <= m <= 9:
        return datetime.date(y, 7, 1)
    if 10 <= m <= 12:
        return datetime.date(y, 10, 1)
    if 1 <= m <= 3:
        return datetime.date(y, 1, 1)
    return datetime.date(y, 4, 1)


def _next_quarter_start(date: datetime.date) -> datetime.date:
    """Return the start date of the following quarter."""
    qs = _quarter_start(date)
    m = qs.month
    y = qs.year
    if m == 7:
        return datetime.date(y, 10, 1)
    if m == 10:
        return datetime.date(y + 1, 1, 1)
    if m == 1:
        return datetime.date(y, 4, 1)
    return datetime.date(y, 7, 1)


def _quarter_label(start: datetime.date) -> str:
    """Return a human readable label for a quarter."""
    end = _next_quarter_start(start) - datetime.timedelta(days=1)
    return f"{start.strftime('%b')} - {end.strftime('%b %Y')}"


def _parse_badges():
    badges = util.data.read_data('badges.jsonl')
    for b in badges:
        try:
            b['date'] = datetime.date.fromisoformat(b.get('date'))
        except Exception:
            b['date'] = None
    return badges


def _count_leaderboard(badges, key):
    counter = Counter()
    for b in badges:
        value = b.get(key)
        if not value:
            continue
        if isinstance(value, dict):
            value = value.get('name') or value.get('id')
        counter[value] += 1
    return counter


TIER_WEIGHTS = {
    'locals': 1,
    'online': 1,
    'league challenge': 2,
    'league cup': 3,
    'regionals': 5,
    'internationals': 6
}


def _weighted_leaderboard(badges, key):
    """Return sorted leaderboard accounting for tier weights, including counts and weights."""
    counts = Counter()
    weights = Counter()
    for b in badges:
        value = b.get(key)
        if not value:
            continue
        if isinstance(value, dict):
            value = value.get('name') or value.get('id')
        counts[value] += 1
        tier = (b.get('tier') or '').lower()
        weights[value] += TIER_WEIGHTS.get(tier, 0)

    leaderboard = [
        (value, counts[value], weights[value])
        for value in counts
    ]

    return sorted(
        leaderboard,
        key=lambda item: (item[1], item[2]),
        reverse=True
    )


def _leaderboard_table(title, data_counter):
    rows = [
        html.Tr([
            html.Td(name), html.Td(count, className='text-center'), html.Td(points, className='text-center')
        ]) for name, count, points in data_counter]
    table = dbc.Table([
        html.Thead(html.Tr([html.Th(title), html.Td('Badges', className='w-0'), html.Td('Points', className='w-0')])),
        html.Tbody(rows)
    ], bordered=True, size='sm', class_name='mb-2')
    return table


def _counts_table(title, season_counts, quarter_counts):
    keys = set(season_counts.keys()) | set(quarter_counts.keys())
    rows = [
        html.Tr([
            html.Td(k),
            html.Td(season_counts.get(k, 0), className='text-center'),
            html.Td(quarter_counts.get(k, 0), className='text-center'),
        ]) for k in sorted(keys)
    ]
    table = dbc.Table([
        html.Thead(html.Tr([html.Th(title), html.Td('Season', className='w-0'), html.Td('Quarter', className='w-0')])),
        html.Tbody(rows)
    ], bordered=True, size='sm', class_name='mb-4')
    return table


def _quarter_row(badges, quarter_start: datetime.date):
    """Create leaderboard row for a given quarter."""
    quarter_end = _next_quarter_start(quarter_start)
    today = datetime.date.today()
    end_date = min(quarter_end, today + datetime.timedelta(days=1))

    season_start = _season_start(quarter_start)

    season_badges = [
        b for b in badges if b.get('date') and season_start <= b['date'] < end_date
    ]
    quarter_badges = [
        b for b in badges if b.get('date') and quarter_start <= b['date'] < end_date
    ]

    trainer_season = _weighted_leaderboard(season_badges, 'trainer')[:10]
    trainer_quarter = _weighted_leaderboard(quarter_badges, 'trainer')[:10]
    deck_season = _weighted_leaderboard(season_badges, 'deck')[:10]
    deck_quarter = _weighted_leaderboard(quarter_badges, 'deck')[:10]

    season = season_start.year + 1
    quarter_label = _quarter_label(quarter_start)

    store_counts_season = _count_leaderboard(season_badges, 'store')
    store_counts_quarter = _count_leaderboard(quarter_badges, 'store')
    top_stores = store_counts_season.most_common(5)
    top_store_names = [name for name, _ in top_stores]
    store_season_top = {name: store_counts_season[name] for name in top_store_names}
    store_quarter_top = {name: store_counts_quarter.get(name, 0) for name in top_store_names}

    tier_season = _count_leaderboard(season_badges, 'tier')
    tier_quarter = _count_leaderboard(quarter_badges, 'tier')

    format_season = _count_leaderboard(season_badges, 'format')
    format_quarter = _count_leaderboard(quarter_badges, 'format')

    store_table = _counts_table('Store', store_season_top, store_quarter_top)
    tier_table = _counts_table('Tier', tier_season, tier_quarter)
    format_table = _counts_table('Format', format_season, format_quarter)

    leaderboard = dbc.Row([
        dbc.Col([
            html.H4('Trainers'),
            _leaderboard_table(f'{season} Season', trainer_season),
            _leaderboard_table(quarter_label, trainer_quarter),
        ], md=6),
        dbc.Col([
            html.H4('Decks'),
            _leaderboard_table(f'{season} Season', deck_season),
            _leaderboard_table(quarter_label, deck_quarter),
        ], md=6)
    ])

    stats = dbc.Row([
        dbc.Col(store_table, lg=4, md=6),
        dbc.Col(tier_table, lg=4, md=6),
        dbc.Col(format_table, lg=4, md=6),
    ])

    return html.Div([leaderboard, html.H4('Badge Stats'), stats])


def layout():
    badges = _parse_badges()

    today = datetime.date.today()

    recent_components = []
    for i, b in enumerate(badges[:10]):
        component = components.badge.create_badge_component(b, i)
        recent_components.append(component)

    quarter_starts = sorted({
        _quarter_start(b['date'])
        for b in badges if b.get('date')
    }, reverse=True)

    tabs = [
        dbc.Tab(_quarter_row(badges, qs), label=_quarter_label(qs))
        for qs in quarter_starts
    ]

    badge_cols = [
        dbc.Col(rc, xs=12, md=6, xl=4)
        for rc in recent_components
    ]

    return dbc.Container([
        html.H2('Recent Badges'),
        dbc.Row(badge_cols, class_name='overflow-auto flex-nowrap mb-3 pb-2'),
        html.H2('Leaderboards'),
        dbc.Tabs(tabs),
    ], fluid=True)
