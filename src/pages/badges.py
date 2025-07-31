import dash
import dash_bootstrap_components as dbc
import datetime
from collections import defaultdict
from dash import html, clientside_callback, ClientsideFunction, Output, Input, State, MATCH

import components.badge
import util.data

dash.register_page(__name__, path='/badges')


def layout():
    """Display all earned badges."""
    badges = util.data.read_data('badges.jsonl')
    # Group badges by month
    month_map = defaultdict(list)
    for i, b in enumerate(badges):
        date_str = b.get('date')
        try:
            date_obj = datetime.date.fromisoformat(date_str)
        except Exception:
            continue
        month_start = datetime.date(date_obj.year, date_obj.month, 1)
        month_map[month_start].append((i, b))

    month_components = []
    for idx, month_start in enumerate(sorted(month_map.keys(), reverse=True)):
        month_badges = month_map[month_start]
        badge_rows = [
            dbc.Col(
                components.badge.create_badge_component(b, i),
                xs=12,
                md=6,
                xl=4,
                class_name='mb-2'
            )
            for i, b in month_badges
        ]
        toggle_id = {'type': 'month-toggle', 'index': month_start.isoformat()}
        collapse_id = {'type': 'month-collapse', 'index': month_start.isoformat()}
        month_components.append(
            html.Div([
                html.H3(
                    f"{month_start.strftime('%Y %B')} ({len(month_badges)})",
                    id=toggle_id,
                    n_clicks=0,
                    className='mt-2'
                ),
                dbc.Collapse(
                    dbc.Row(badge_rows),
                    id=collapse_id,
                    is_open=(idx == 0)
                )
            ])
        )

    return dbc.Container(
        [
            html.H2('All Badges'),
            html.P('A complete list of all badges that have been earned.'),
            *month_components
        ],
        fluid=True
    )


clientside_callback(
    ClientsideFunction('clientside', 'toggleWithButton'),
    Output({'type': 'month-collapse', 'index': MATCH}, 'is_open'),
    Input({'type': 'month-toggle', 'index': MATCH}, 'n_clicks'),
    State({'type': 'month-collapse', 'index': MATCH}, 'is_open'),
)