from collections import Counter, defaultdict

import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, callback, clientside_callback, ClientsideFunction, Output, Input, State, MATCH

import util.seasons
import util.leaderboard

dash.register_page(__name__, path='/locations', name='Locations')

PREFIX = 'locations'
_RANK_ICONS = {1: 'crown', 2: 'trophy', 3: 'medal'}


def _summarize_store_trainers(badges):
    """Return mapping of store -> trainer -> tier counts."""
    summary = defaultdict(lambda: defaultdict(Counter))
    for b in badges:
        store = b.get('store')
        trainer = b.get('trainer')
        if not store or not trainer:
            continue
        tier = (b.get('tier') or '').title()
        summary[store][trainer][tier] += 1
    return summary


def _unique_trainers_per_store(badges):
    trainers = defaultdict(set)
    for b in badges:
        store = b.get('store')
        trainer = b.get('trainer')
        if store and trainer:
            trainers[store].add(trainer)
    return {store: len(t) for store, t in trainers.items()}


def _format_detail_list(details):
    items = []
    for name, tiers in details.items():
        tier_badges = [
            dbc.Badge(f"{t} {c}x" if c > 1 else t, class_name='ms-1')
            for t, c in tiers.items()
        ]
        items.append(html.Li(
            html.Div(
                [html.Span('-', className='mx-1'), name, *tier_badges],
                className='d-flex align-items-center mb-1'
            )
        ))
    return html.Ul(items, className='mb-0 list-unstyled')


def _locations_table(data, summaries, unique_trainers):
    rows = []
    prev_score = None
    rank = 0
    num_same = 1
    for i, (store, count, points) in enumerate(data):
        idx = f"loc-{i}-{store}".lower().replace(' ', '')
        toggle_id = {'type': f'{PREFIX}-toggle', 'index': idx}
        collapse_id = {'type': f'{PREFIX}-collapse', 'index': idx}

        if prev_score and (count, points) == prev_score:
            num_same += 1
        else:
            rank += num_same
            num_same = 1
        prev_score = (count, points)

        rank_display = (
            html.I(className=f'fas fa-{_RANK_ICONS[rank]}', title=f'Rank {rank}')
            if rank in _RANK_ICONS else rank
        )
        trainer_count = unique_trainers.get(store, 0)
        rows.append(html.Tr([
            html.Td(rank_display, className='text-center align-middle w-0 text-dark'),
            html.Td(html.A(store, id=toggle_id, n_clicks=0), className='align-middle'),
            html.Td(count, className='text-center align-middle'),
            html.Td(points, className='text-center align-middle'),
            html.Td(trainer_count, className='text-center align-middle'),
        ]))
        detail = _format_detail_list(summaries.get(store, {}))
        rows.append(html.Tr([
            html.Td(dbc.Collapse(detail, id=collapse_id, is_open=False), colSpan=5, className='p-0')
        ], className='tr-collapse'))

    return dbc.Table([
        html.Thead(html.Tr([
            html.Th('Store', colSpan=2),
            html.Td('Badges', className='w-0'),
            html.Td('Points', className='w-0'),
            html.Td('Trainers', className='w-0'),
        ])),
        html.Tbody(rows),
    ], bordered=True, size='sm', class_name='mb-2 leaderboard', responsive=True)


def _totals(badges):
    unique_stores = {b.get('store') for b in badges if b.get('store')}
    unique_trainers = {b.get('trainer') for b in badges if b.get('trainer')}
    metrics = [
        ('Total Badges', len(badges)),
        ('Unique Locations', len(unique_stores)),
        ('Unique Trainers', len(unique_trainers)),
    ]
    return dbc.Row(
        [
            dbc.Col(
                dbc.Card(
                    dbc.CardBody([
                        html.Div(label, className='text-muted'),
                        html.H4(str(value), className='mb-0'),
                    ]),
                    class_name='text-center h-100'
                ),
                xs=12, md=4, class_name='mb-1'
            )
            for label, value in metrics
        ],
        class_name='g-2 mb-3'
    )


def layout(season=None, **kwargs):
    scope = util.seasons.resolve_scope(season)
    badges = util.seasons.read_badges(scope)
    if not badges:
        content = html.P('No badges found for the selected season.')
    else:
        store_lb = util.leaderboard.weighted_leaderboard(badges, 'store')
        summaries = _summarize_store_trainers(badges)
        unique_trainers = _unique_trainers_per_store(badges)
        content = html.Div([
            _totals(badges),
            _locations_table(store_lb, summaries, unique_trainers),
        ])
    return dbc.Container([
        html.H2('Locations'),
        html.P([
            'Breakdown of badge activity by store for ',
            html.Strong(util.seasons.season_label(scope)),
            '. Click a store name to see which trainers earned badges there.',
        ]),
        content,
    ], fluid=True)


clientside_callback(
    ClientsideFunction('clientside', 'toggleWithButton'),
    Output({'type': f'{PREFIX}-collapse', 'index': MATCH}, 'is_open'),
    Input({'type': f'{PREFIX}-toggle', 'index': MATCH}, 'n_clicks'),
    State({'type': f'{PREFIX}-collapse', 'index': MATCH}, 'is_open'),
)
