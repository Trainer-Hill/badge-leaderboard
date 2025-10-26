import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, callback, clientside_callback, ClientsideFunction, Output, Input, State

import components.badge
import util.data
import util.grouping

dash.register_page(__name__, path='/players')


def layout():
    """Layout for the player profile page."""
    badges = util.data.read_data()
    grouped = util.grouping.group_badges(badges, lambda b: b.get('trainer'))
    sorted_players = util.grouping.sort_group_items(grouped)
    player_options = util.grouping.dropdown_options(
        sorted_players,
        lambda name, player_badges: f"{name} ({len(player_badges)})"
    )

    return dbc.Container([
        html.Div([
            html.H2('Player Profiles', className='d-flex me-1'),
            dbc.Button(html.I(className='fas fa-download'), title='Download Player Profile', id='download-profile'),
        ], className='d-flex align-items-center'),
        html.P('Select a player to view all badges they have earned.'),
        dcc.Dropdown(
            options=player_options,
            value=player_options[0]['value'] if player_options else None,
            id='player-dropdown',
            clearable=False,
            className='mb-3'
        ),
        html.Div(id='player-badges'),
        dbc.Input(value='player-badges', class_name='d-none', id='player-profile')
    ], fluid=True)


clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='downloadDomAsImage'),
    Output('download-profile', 'className'),
    Input('download-profile', 'n_clicks'),
    State('player-profile', 'value'),
)


@callback(
    Output('player-badges', 'children'),
    Input('player-dropdown', 'value')
)
def render_player_badges(player):
    """Render all badges for the selected player."""
    if not player:
        return dash.no_update
    badges = util.data.read_data()
    player_badges = [b for b in badges if b.get('trainer') == player]
    badge_cols = [
        dbc.Col(
            components.badge.create_badge_component(b, i),
            xs=12, md=6, lg=4,
            class_name='mb-2'
        )
        for i, b in enumerate(player_badges)
    ]
    header = html.H3(f"{player} - {len(player_badges)} badge{'s' if len(player_badges) != 1 else ''}")
    return html.Div([
        header,
        dbc.Row(badge_cols, justify='around')
    ])
