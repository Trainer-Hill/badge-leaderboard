import dash
import dash_bootstrap_components as dbc
import datetime
from collections import Counter, defaultdict
from dash import html, callback, clientside_callback, ClientsideFunction, Output, Input, State, MATCH

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
    badges = util.data.read_data()
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


def _most_unique(badges, primary_key, secondary_key):
    """Return list of items with the most unique secondary values."""
    uniques = defaultdict(set)
    for b in badges:
        primary = b.get(primary_key)
        secondary = b.get(secondary_key)
        if not primary or not secondary:
            continue
        if isinstance(primary, dict):
            primary = primary.get('name') or primary.get('id')
        if isinstance(secondary, dict):
            secondary = secondary.get('name') or secondary.get('id')
        uniques[primary].add(secondary)
    if not uniques:
        return []
    counts = [(p, len(s)) for p, s in uniques.items()]
    max_count = max(c for _, c in counts)
    return [(p, c) for p, c in counts if c == max_count]


TIER_WEIGHTS = {
    'locals': 1,
    'online': 1,
    'league challenge': 2,
    'league cup': 3,
    'regionals': 5,
    'internationals': 5,
    'worlds': 5
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


def _season_awards(badges, deck_map=None):
    """Return award badges for season-wide stats."""
    trainer_unique = _most_unique(badges, 'trainer', 'deck')
    deck_unique = _most_unique(badges, 'deck', 'trainer')

    trainer_lb = _weighted_leaderboard(badges, 'trainer')
    trainer_points = []
    if trainer_lb:
        max_tp = max(item[2] for item in trainer_lb)
        trainer_points = [(name, f'{pts} pts') for name, _, pts in trainer_lb if pts == max_tp]

    deck_lb = _weighted_leaderboard(badges, 'deck')
    deck_points = []
    if deck_lb:
        max_dp = max(item[2] for item in deck_lb)
        deck_points = [(name, f'{pts} pts') for name, _, pts in deck_lb if pts == max_dp]

    def _award_col(title, items, use_deck=False):
        if not items:
            return None
        entries = []
        for name, value in items:
            label = name
            if use_deck:
                deck = deck_map.get(name, {'name': name}) if deck_map else {'name': name}
                label = components.deck_label.create_label(deck)
            entries.append(
                html.Div([
                    label,
                    html.Span(f'({value})', className='ms-1'),
                ], className='d-flex justify-content-center align-items-center flex-wrap')
            )
        return dbc.Col(
            dbc.Card([
                dbc.CardHeader(title),
                dbc.CardBody(entries)
            ], class_name='text-center mb-2'),
            md=6, lg=3
        )

    awards = [
        _award_col('Most Unique Decks', trainer_unique),
        _award_col('Most Points', trainer_points),
        _award_col('Most Unique Trainers', deck_unique, True),
        _award_col('Most Points', deck_points, True),
    ]
    awards = [a for a in awards if a]
    return dbc.Row(awards, class_name='mb-4 g-2')


def _filter_badges(badges, start: datetime.date, end: datetime.date):
    return [b for b in badges if b.get('date') and start <= b['date'] < end]


def _next_month(date: datetime.date) -> datetime.date:
    if date.month == 12:
        return datetime.date(date.year + 1, 1, 1)
    return datetime.date(date.year, date.month + 1, 1)


def layout():
    badges = _parse_badges()

    recent_components = [
        components.badge.create_badge_component(b, i)
        for i, b in enumerate(badges[:10])
    ]

    seasons = sorted({
        _season_start(b['date']).year + 1
        for b in badges if b.get('date')
    }, reverse=True)

    badge_cols = [
        dbc.Col(rc, xs=12, md=6, xl=4, class_name='bg-transparent')
        for i, rc in enumerate(recent_components)
    ]

    season_tabs = [
        dbc.Tab(label=f'{season} Season', tab_id=str(season), active_tab_style={'fontWeight': 'bold'})
        for season in seasons
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
            'View the top badge earners by season, quarter, and month. Ranked by total badges. Tiebreakers are determined based on points earned.',
            th_helpers.components.help_icon.create_help_icon('points-help', TIER_WEIGHT_HELP, 'ms-1')
        ]),
        html.H3('Season'),
        dbc.Tabs(season_tabs, id='season-tabs', active_tab=str(seasons[0]) if seasons else None),
        html.Div(id='season-content'),
    ], fluid=True)


@callback(
    Output('season-content', 'children'),
    Input('season-tabs', 'active_tab'),
)
def render_season(active_season):
    if not active_season:
        return dash.no_update
    badges = _parse_badges()
    deck_map = _create_deck_map(badges)
    season_year = int(active_season)
    season_start = datetime.date(season_year-1, 7, 1)
    season_end = datetime.date(season_start.year+1, 7, 1)
    season_badges = _filter_badges(badges, season_start, season_end)
    quarter_starts = sorted({
        _quarter_start(b['date'])
        for b in season_badges if b.get('date')
    }, reverse=True)
    quarter_tabs = [
        dbc.Tab(label=_quarter_label(qs), tab_id=qs.isoformat(), active_tab_style={'fontWeight': 'bold'})
        for qs in quarter_starts
    ]
    return html.Div([
        _leaderboard_section(season_badges, f'{season_year} Season', f'season-{season_year}', deck_map=deck_map),
        _season_awards(season_badges, deck_map=deck_map),
        html.H3('Quarter'),
        dbc.Tabs(
            quarter_tabs,
            id={'type': 'quarter-tabs', 'index': season_year},
            active_tab=quarter_tabs[0].tab_id if quarter_tabs else None
        ),
        html.Div(id={'type': 'quarter-content', 'index': season_year})
    ])


@callback(
    Output({'type': 'quarter-content', 'index': MATCH}, 'children'),
    Input({'type': 'quarter-tabs', 'index': MATCH}, 'active_tab')
)
def render_quarter(active_quarter):
    if not active_quarter:
        return dash.no_update
    season_year = int(dash.ctx.triggered_id['index'] if dash.ctx.triggered_id else active_quarter.split('-')[0])
    badges = _parse_badges()
    season_start = _season_start(datetime.datetime.strptime(active_quarter, "%Y-%m-%d").date())
    season_end = datetime.date(season_year+1, 7, 1)
    season_badges = _filter_badges(badges, season_start, season_end)
    qs = datetime.date.fromisoformat(active_quarter)
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
                label=month_start.strftime('%B %Y'),
                tab_id=month_start.isoformat(),
                active_tab_style={'fontWeight': 'bold'}
            )
        )
        month_start = me
    month_tabs.reverse()
    deck_map = _create_deck_map(season_badges)
    return html.Div([
        _leaderboard_section(quarter_badges, _quarter_label(qs), f'quarter-{qs.isoformat()}', deck_map=deck_map),
        html.H3('Month'),
        dbc.Tabs(
            month_tabs,
            id={'type': 'month-tabs', 'index': qs.isoformat()},
            active_tab=month_tabs[0].tab_id if month_tabs else None
        ),
        html.Div(id={'type': 'home-month-content', 'index': qs.isoformat()})
    ])


@callback(
    Output({'type': 'home-month-content', 'index': MATCH}, 'children'),
    Input({'type': 'month-tabs', 'index': MATCH}, 'active_tab'),
)
def render_month(active_month):
    if not active_month:
        return dash.no_update
    month_start = datetime.date.fromisoformat(active_month)
    month_end = _next_month(month_start)
    badges = _parse_badges()
    month_badges = _filter_badges(badges, month_start, month_end)
    deck_map = _create_deck_map(badges)
    return _leaderboard_section(month_badges, month_start.strftime('%B %Y'), f'month-{month_start.isoformat()}', deck_map=deck_map)


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
