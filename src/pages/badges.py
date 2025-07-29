import dash
import dash_bootstrap_components as dbc
from dash import html

import components.badge
import util.data

# Register the page so dash picks it up
# This will be available at `/badges`
dash.register_page(__name__, path='/badges')


def layout():
    """Display all earned badges."""
    badges = util.data.read_data('badges.jsonl')

    badge_rows = [
        dbc.Col(
            components.badge.create_badge_component(b, i),
            xs=12,
            md=6,
            xl=4,
            class_name='mb-2'
        )
        for i, b in enumerate(badges)
    ]

    return dbc.Container(
        [
            html.H2('All Badges'),
            html.P('A complete list of all badges that have been earned.'),
            dbc.Row(badge_rows)
        ],
        fluid=True
    )
