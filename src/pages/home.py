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
    return f"{season.year + 1} {start.strftime('%B')} - {end.strftime('%B')}"


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


def _leaderboard_section(badges, label, prefix, deck_map=None):
    """Return the basic leaderboard section with trainer and deck tables."""
    trainer_lb = _weighted_leaderboard(badges, 'trainer')[:10]
    deck_lb = _weighted_leaderboard(badges, 'deck')[:10]

    trainer_summary = _summarize_badges(badges, 'trainer', 'deck')
    deck_summary = _summarize_badges(badges, 'deck', 'trainer')

    return dbc.Row([
        dbc.Col([
            _leaderboard_table(label, trainer_lb, trainer_summary, f'{prefix}-trainer', deck_map=deck_map),
        ], md=6),
        dbc.Col([
            _leaderboard_table(label, deck_lb, deck_summary, f'{prefix}-deck', deck_rows=True, deck_map=deck_map),
        ], md=6),
    ])


def _filter_badges(badges, start: datetime.date, end: datetime.date):
    return [b for b in badges if b.get('date') and start <= b['date'] < end]


def _next_month(date: datetime.date) -> datetime.date:
    if date.month == 12:
        return datetime.date(date.year + 1, 1, 1)
    return datetime.date(date.year, date.month + 1, 1)


def layout():
    badges = _parse_badges()

    recent_components = []
    for i, b in enumerate(badges[:10]):
        component = components.badge.create_badge_component(b, i)
        recent_components.append(component)

    seasons = sorted({
        _season_start(b['date']).year + 1
        for b in badges if b.get('date')
    }, reverse=True)

    deck_map = _create_deck_map(badges)

    year_tabs = []
    for season_year in seasons:
        season_start = datetime.date(season_year - 1, 7, 1)
        season_end = datetime.date(season_year, 7, 1)
        season_badges = _filter_badges(badges, season_start, season_end)

        quarter_starts = sorted({
            _quarter_start(b['date'])
            for b in season_badges if b.get('date')
        }, reverse=True)

        quarter_tabs = []
        for qs in quarter_starts:
            qe = _next_quarter_start(qs)
            quarter_badges = _filter_badges(season_badges, qs, qe)

            month_tabs = []
            month_start = qs
            for _ in range(3):
                me = _next_month(month_start)
                month_badges = _filter_badges(season_badges, month_start, me)
                if len(month_badges) == 0:
                    month_start = me
                    continue
                month_tabs.append(
                    dbc.Tab(
                        _leaderboard_section(month_badges, month_start.strftime('%B %Y'), f'month-{month_start.isoformat()}', deck_map=deck_map),
                        label=month_start.strftime('%B %Y'),
                        active_tab_style={'fontWeight': 'bold'}
                    )
                )
                month_start = me
            month_tabs.reverse()
            quarter_tabs.append(
                dbc.Tab(
                    html.Div([
                        _leaderboard_section(quarter_badges, _quarter_label(qs), f'quarter-{qs.isoformat()}', deck_map=deck_map),
                        html.H3('Month'),
                        dbc.Tabs(month_tabs, class_name='mt-2')
                    ]),
                    label=_quarter_label(qs),
                    active_tab_style={'fontWeight': 'bold'}
                )
            )
        quarter_starts.reverse()
        year_tabs.append(
            dbc.Tab(
                html.Div([
                    _leaderboard_section(season_badges, f'{season_year} Season', f'season-{season_year}', deck_map=deck_map),
                    html.H3('Quarter'),
                    dbc.Tabs(quarter_tabs, class_name='mt-2')
                ]),
                label=f'{str(season_year)} Season',
                active_tab_style={'fontWeight': 'bold'}
            )
        )


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
        html.H3('Season'),
        dbc.Tabs(year_tabs),
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
