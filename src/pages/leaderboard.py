import datetime
from collections import Counter, defaultdict

import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, callback, clientside_callback, ClientsideFunction, Output, Input, State, MATCH

import components.deck_label
import util.names
import util.seasons
import util.leaderboard

dash.register_page(__name__, path='/leaderboard', name='Rankings')

PREFIX = 'rankings'

_RANK_ICONS = {1: 'crown', 2: 'trophy', 3: 'medal'}


def _create_deck_map(badges):
    deck_map = {}
    for b in badges:
        deck = b.get('deck')
        if isinstance(deck, dict):
            name = deck.get('name')
            if name and name not in deck_map:
                deck_map[name] = deck
    return deck_map


def _summarize_badges(badges, primary_key, secondary_key):
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


def _format_detail_list(details, use_deck_label=False, deck_map=None):
    items = []
    for name, tiers in details.items():
        tier_badges = [
            dbc.Badge(f"{t} {c}x" if c > 1 else t, class_name='ms-1')
            for t, c in tiers.items()
        ]
        if use_deck_label:
            deck = deck_map.get(name, {'name': name}) if deck_map else {'name': name}
            label = components.deck_label.create_label(deck)
        else:
            label = util.names.public_name(name)
        items.append(html.Li(
            html.Div([html.Span('-', className='mx-1'), label, *tier_badges], className='d-flex align-items-center mb-1')
        ))
    return html.Ul(items, className='mb-0 list-unstyled')


def _leaderboard_table(title, data, summaries, row_type, deck_rows=False, deck_map=None, extras=None):
    show_extras = extras is not None and not deck_rows
    col_span = 6 if show_extras else 4
    rows = []
    prev_score = None
    rank = 0
    num_same = 1
    for i, (name, count, points) in enumerate(data):
        idx = f"{row_type}-{i}-{name}".lower().replace(' ', '')
        toggle_id = {'type': f'{PREFIX}-toggle', 'index': idx}
        collapse_id = {'type': f'{PREFIX}-collapse', 'index': idx}

        if deck_rows:
            deck = deck_map.get(name, {'name': name}) if deck_map else {'name': name}
            label = components.deck_label.create_label(deck)
        else:
            label = util.names.public_name(name)

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
        cells = [
            html.Td(rank_display, className='text-center align-middle w-0 text-dark'),
            html.Td(html.A(label, id=toggle_id, n_clicks=0), className='align-middle deck'),
            html.Td(count, className='text-center align-middle'),
            html.Td(points, className='text-center align-middle'),
        ]
        if show_extras:
            avg, diversity = extras.get(name, (0.0, 0.0))
            cells += [
                html.Td(f'{avg:.2f}', className='text-center align-middle'),
                html.Td(f'{diversity:.2f}', className='text-center align-middle'),
            ]
        rows.append(html.Tr(cells))
        detail = _format_detail_list(
            summaries.get(name, {}),
            use_deck_label=not deck_rows,
            deck_map=deck_map,
        )
        rows.append(html.Tr([
            html.Td(dbc.Collapse(detail, id=collapse_id, is_open=False), colSpan=col_span, className='p-0')
        ], className='tr-collapse'))

    extra_headers = [
        html.Td('Avg Pts', className='w-0'),
        html.Td('Diversity', className='w-0'),
    ] if show_extras else []

    return dbc.Table([
        html.Thead(html.Tr([
            html.Th(title, colSpan=2),
            html.Td('Badges', className='w-0'),
            html.Td('Points', className='w-0'),
            *extra_headers,
        ])),
        html.Tbody(rows),
    ], bordered=True, size='sm', class_name='mb-2 leaderboard', responsive=True)


def _rankings_section(badges):
    deck_map = _create_deck_map(badges)
    trainer_lb = util.leaderboard.weighted_leaderboard(badges, 'trainer')
    deck_lb = util.leaderboard.weighted_leaderboard(badges, 'deck')
    trainer_summary = _summarize_badges(badges, 'trainer', 'deck')
    deck_summary = _summarize_badges(badges, 'deck', 'trainer')
    extras = util.leaderboard.trainer_extras(badges)
    return dbc.Row([
        dbc.Col(
            _leaderboard_table('Trainer', trainer_lb, trainer_summary, 'trainer', deck_map=deck_map, extras=extras),
            md=6,
        ),
        dbc.Col(
            _leaderboard_table('Deck', deck_lb, deck_summary, 'deck', deck_rows=True, deck_map=deck_map),
            md=6,
        ),
    ])


def layout(season=None, **kwargs):
    scope = util.seasons.resolve_scope(season)
    badges = util.seasons.read_badges(scope)
    content = (
        _rankings_section(badges) if badges
        else html.P('No badges found for the selected season.')
    )
    return dbc.Container([
        html.H2('Rankings'),
        html.P([
            'Full leaderboard of all badge earners for ',
            html.Strong(util.seasons.season_label(scope)),
            '. Click a trainer or deck name to see detail.',
        ]),
        content,
    ], fluid=True)


clientside_callback(
    ClientsideFunction('clientside', 'toggleWithButton'),
    Output({'type': f'{PREFIX}-collapse', 'index': MATCH}, 'is_open'),
    Input({'type': f'{PREFIX}-toggle', 'index': MATCH}, 'n_clicks'),
    State({'type': f'{PREFIX}-collapse', 'index': MATCH}, 'is_open'),
)
