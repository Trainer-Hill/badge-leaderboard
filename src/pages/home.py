import dash
import dash_bootstrap_components as dbc
import datetime
from collections import Counter, defaultdict
from dash import html, clientside_callback, ClientsideFunction, Output, Input, State, MATCH

import th_helpers.components.help_icon
import components.badge
import components.deck_label
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
    season = _season_start(start)
    end = _next_quarter_start(start) - datetime.timedelta(days=1)
    return f"s{season.year + 1 - 2000} {start.strftime('%b')} - {end.strftime('%b')}"


def _parse_badges():
    badges = util.data.read_data('badges.jsonl')
    for b in badges:
        try:
            b['date'] = datetime.date.fromisoformat(b.get('date'))
        except Exception:
            b['date'] = None
    return badges


def _create_deck_map(badges):
    """Return mapping of deck name to full deck data."""
    deck_map = {}
    for b in badges:
        deck = b.get('deck')
        if isinstance(deck, dict):
            name = deck.get('name')
            if name and name not in deck_map:
                deck_map[name] = deck
    return deck_map


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


def _summarize_badges(badges, primary_key, secondary_key):
    """Return mapping of primary -> secondary -> tier counts."""
    summary = defaultdict(lambda: defaultdict(Counter))
    for b in badges:
        primary = b.get(primary_key)
        secondary = b.get(secondary_key)
        if not primary or not secondary:
            continue
        if isinstance(primary, dict):
            primary = primary.get('name') or primary.get('id')
        if isinstance(secondary, dict):
            secondary = secondary.get('name') or secondary.get('id')
        tier = (b.get('tier') or '').title()
        summary[primary][secondary][tier] += 1
    return summary


TIER_WEIGHTS = {
    'locals': 1,
    'online': 1,
    'league challenge': 2,
    'league cup': 3,
    'regionals': 5,
    'internationals': 5
}
TIER_WEIGHT_HELP = [html.Div(f'{k.title()} - {v}pt{"s" if v > 1 else ""}') for k, v in TIER_WEIGHTS.items()]


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


def _format_detail_list(details, use_deck_label=False, deck_map=None):
    items = []
    for name, tiers in details.items():
        badges = [
            dbc.Badge(f"{t} {c}x" if c > 1 else t, class_name='ms-1')
            for t, c in tiers.items()
        ]
        if use_deck_label:
            deck = deck_map.get(name, {'name': name}) if deck_map else {'name': name}
            label = components.deck_label.create_label(deck)
        else:
            label = name
        items.append(html.Li(html.Div([html.Span('-', className='mx-1'), label, *badges], className='d-flex align-items-center mb-1')))
    return html.Ul(items, className='mb-0 list-unstyled')


_RANK_ICONS = {
    1: 'crown', 2: 'trophy', 3: 'medal'
}


def _leaderboard_table(title, data_counter, summaries, row_type, deck_rows=False, deck_map=None):
    rows = []
    prev_rank = None
    rank = 0
    num_same = 1
    for i, (name, count, points) in enumerate(data_counter):
        idx = f"{row_type}-{title}-{i}-{name}".lower().replace(' ', '')
        toggle_id = {'type': f'lb-toggle', 'index': idx}
        collapse_id = {'type': f'lb-collapse', 'index': idx}
        if deck_rows:
            deck = deck_map.get(name, {'name': name}) if deck_map else {'name': name}
            label = components.deck_label.create_label(deck)
        else:
            label = name

        if prev_rank and (count, points) == prev_rank:
            num_same += 1
        else:
            rank += num_same
            num_same = 1
        prev_rank = (count, points)

        rank_display = html.I(className=f'fas fa-{_RANK_ICONS[rank]}', title=f'Rank {rank}') if rank in _RANK_ICONS else rank
        rows.append(html.Tr([
            html.Td(rank_display, className='text-center align-middle w-0 text-dark'),
            html.Td(html.A(label, id=toggle_id, n_clicks=0), className='align-middle deck'),
            html.Td(count, className='text-center align-middle'),
            html.Td(points, className='text-center align-middle'),
        ]))
        detail_component = _format_detail_list(summaries.get(name, {}), use_deck_label=not deck_rows, deck_map=deck_map)
        rows.append(html.Tr([
            html.Td(
                dbc.Collapse(detail_component, id=collapse_id, is_open=False),
                colSpan=4, className='p-0'
            )
        ], className='tr-collapse'))
    table = dbc.Table([
        html.Thead(html.Tr([html.Th(title, colSpan=2), html.Td('Badges', className='w-0'), html.Td('Points', className='w-0')])),
        html.Tbody(rows)
    ], bordered=True, size='sm', class_name='mb-2 leaderboard')
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


def _quarter_row(badges, quarter_start: datetime.date, deck_map=None):
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

    trainer_season_summary = _summarize_badges(season_badges, 'trainer', 'deck')
    trainer_quarter_summary = _summarize_badges(quarter_badges, 'trainer', 'deck')
    deck_season_summary = _summarize_badges(season_badges, 'deck', 'trainer')
    deck_quarter_summary = _summarize_badges(quarter_badges, 'deck', 'trainer')

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
            _leaderboard_table(quarter_label, trainer_quarter, trainer_quarter_summary, 'trainer-quart', deck_map=deck_map),
            _leaderboard_table(f'{season} Season', trainer_season, trainer_season_summary, f'trainer-season-{quarter_label}', deck_map=deck_map),
        ], md=6),
        dbc.Col([
            html.H4('Decks'),
            _leaderboard_table(quarter_label, deck_quarter, deck_quarter_summary, 'deck-quart', deck_rows=True, deck_map=deck_map),
            _leaderboard_table(f'{season} Season', deck_season, deck_season_summary, f'deck-season-{quarter_label}', deck_rows=True, deck_map=deck_map),
        ], md=6)
    ])

    stats = dbc.Row([
        dbc.Col(store_table, lg=4, md=6),
        dbc.Col(tier_table, lg=4, md=6),
        dbc.Col(format_table, lg=4, md=6),
    ])

    return html.Div([
        leaderboard,
        html.H4('Badge Stats'),
        html.P('Additional information about the acquired badges.'),
        stats
    ])


def layout():
    badges = _parse_badges()

    recent_components = []
    for i, b in enumerate(badges[:10]):
        component = components.badge.create_badge_component(b, i)
        recent_components.append(component)

    quarter_starts = sorted({
        _quarter_start(b['date'])
        for b in badges if b.get('date')
    }, reverse=True)

    deck_map = _create_deck_map(badges)

    tabs = [
        dbc.Tab(_quarter_row(badges, qs, deck_map=deck_map), label=_quarter_label(qs), active_tab_style={'fontWeight': 'bold'})
        for qs in quarter_starts
    ]

    badge_cols = [
        dbc.Col(rc, xs=12, md=6, xl=4, class_name='bg-transparent')
        for i, rc in enumerate(recent_components)
    ]

    return dbc.Container([
        dbc.Alert(
            'Welcome to the Badge Leaderboard!',
            color='info',
            class_name='mb-1'
        ),
        html.Div([
            html.H2('Recent Badges', className='d-flex mb-0 me-1'),
            dbc.Button(html.I(className='fas fa-download'), title='Download recent badge', id='download'),
            dbc.Input(value='recent-0', class_name='d-none', id='recent')
        ], className='d-flex align-items-center g-1'),
        html.P('Keep up with the latest badges.'),
        dbc.Row(badge_cols, class_name='overflow-auto flex-nowrap mb-2 pb-3'),
        html.H2('Leaderboards'),
        html.Div([
            'View the top badge earners by quarter. Ranked by total badges. Tiebreakers are determined based on points earned.',
            th_helpers.components.help_icon.create_help_icon('points-help', TIER_WEIGHT_HELP, 'ms-1')
        ]),
        dbc.Tabs(tabs, class_name='mb-1'),
    ], fluid=True)


clientside_callback(
    ClientsideFunction('clientside', 'toggleWithButton'),
    Output({'type': 'lb-collapse', 'index': MATCH}, 'is_open'),
    Input({'type': 'lb-toggle', 'index': MATCH}, 'n_clicks'),
    State({'type': 'lb-collapse', 'index': MATCH}, 'is_open'),
)

clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='downloadDomAsImage'),
    Output('download', 'className'),
    Input('download', 'n_clicks'),
    State('recent', 'value'),
)
