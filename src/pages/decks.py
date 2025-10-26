import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, callback, clientside_callback, ClientsideFunction, Output, Input, State

import components.badge
import components.deck_label
import util.data
import util.grouping

dash.register_page(__name__, path='/decks')


def _deck_name_from_badges(deck_badges):
    if not deck_badges:
        return None
    deck = deck_badges[0].get('deck') or {}
    return deck.get('name') or deck.get('id')


def layout():
    """Layout for the deck profile page."""
    badges = util.data.read_data()
    grouped = util.grouping.group_badges(
        badges,
        lambda b: (b.get('deck') or {}).get('id'),
    )
    sorted_decks = util.grouping.sort_group_items(
        grouped,
        sort_key=lambda item: (
            -len(item[1]),
            (_deck_name_from_badges(item[1]) or item[0] or ''),
        ),
    )
    deck_options = util.grouping.dropdown_options(
        sorted_decks,
        lambda deck_id, deck_badges: f"{_deck_name_from_badges(deck_badges) or deck_id} ({len(deck_badges)})",
    )

    return dbc.Container([
        html.Div([
            html.H2('Deck Profiles', className='d-flex me-1'),
            dbc.Button(html.I(className='fas fa-download'), title='Download Deck Profile', id='download-deck-profile'),
        ], className='d-flex align-items-center'),
        html.P('Select a deck to view all trainers who have earned badges with it.'),
        dcc.Dropdown(
            options=deck_options,
            value=deck_options[0]['value'] if deck_options else None,
            id='deck-dropdown',
            clearable=False,
            className='mb-3'
        ),
        html.Div(id='deck-badges'),
        dbc.Input(value='deck-badges', class_name='d-none', id='deck-profile')
    ], fluid=True)


clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='downloadDomAsImage'),
    Output('download-deck-profile', 'className'),
    Input('download-deck-profile', 'n_clicks'),
    State('deck-profile', 'value'),
)


@callback(
    Output('deck-badges', 'children'),
    Input('deck-dropdown', 'value')
)
def render_deck_badges(deck_id):
    """Render all badges for the selected deck."""
    if not deck_id:
        return dash.no_update
    badges = util.data.read_data()
    deck_badges = [
        b for b in badges
        if (b.get('deck') or {}).get('id') == deck_id
    ]
    if not deck_badges:
        return html.P('No badges found for this deck yet.')

    deck_name = _deck_name_from_badges(deck_badges) or deck_id
    deck_label = components.deck_label.create_label(deck_badges[0].get('deck'))
    badge_cols = [
        dbc.Col(
            components.badge.create_badge_component(b, i),
            xs=12, md=6, lg=4,
            class_name='mb-2'
        )
        for i, b in enumerate(deck_badges)
    ]
    header_children = [
        html.H3(f"{deck_name} - {len(deck_badges)} trainer{'s' if len(deck_badges) != 1 else ''}")
    ]
    if deck_label:
        header_children.insert(0, html.Div(deck_label, className='d-flex justify-content-center mb-2'))
    return html.Div([
        *header_children,
        dbc.Row(badge_cols, justify='around')
    ])
