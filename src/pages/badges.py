import dash
import dash_bootstrap_components as dbc
import datetime
from collections import defaultdict
from dash import html, callback, clientside_callback, ClientsideFunction, Output, Input, State, MATCH

import components.badge
import util.data

dash.register_page(__name__, path='/badges')


def layout():
    """Display all earned badges."""
    badges = util.data.read_data()
    month_map = defaultdict(list)
    for i, b in enumerate(badges):
        date_obj = b.get('date')
        month_start = datetime.date(date_obj.year, date_obj.month, 1)
        month_map[month_start].append((i, b))

    month_components = []
    for idx, month_start in enumerate(sorted(month_map.keys(), reverse=True)):
        # month_badges = month_map[month_start]
        # badge_rows = [
        #     dbc.Col(
        #         components.badge.create_badge_component(b, i),
        #         xs=12,
        #         md=6,
        #         lg=4,
        #         # xl=3,
        #         class_name='mb-2'
        #     )
        #     for i, b in month_badges
        # ]
        toggle_id = {'type': 'month-toggle', 'index': month_start.isoformat()}
        collapse_id = {'type': 'month-collapse', 'index': month_start.isoformat()}
        content_id = {'type': 'month-content', 'index': month_start.isoformat()}
        month_components.append(
            html.Div([
                html.H3(
                    f"{month_start.strftime('%Y %B')} ({len(month_map[month_start])})",
                    id=toggle_id,
                    n_clicks=0,
                    className='mt-2'
                ),
                dbc.Collapse(
                    html.Div(id=content_id),
                    id=collapse_id,
                    is_open=(idx == 0)
                )
            ], className='me-1')
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

def _next_month(date: datetime.date) -> datetime.date:
    if date.month == 12:
        return datetime.date(date.year + 1, 1, 1)
    return datetime.date(date.year, date.month + 1, 1)


@callback(
    Output({'type': 'month-content', 'index': MATCH}, 'children'),
    Input({'type': 'month-collapse', 'index': MATCH}, 'is_open'),
    State({'type': 'month-content', 'index': MATCH}, 'children'),
    State({'type': 'month-collapse', 'index': MATCH}, 'id'),
)
def load_month_badges(is_open, children, collapse_id):
    if not is_open or children:
        return dash.no_update
    month_start = datetime.date.fromisoformat(collapse_id['index'])
    month_end = _next_month(month_start)
    badges = util.data.read_data()
    filtered = [
        b for b in badges
        if b.get('date') and month_start <= b['date'] < month_end
    ]
    badge_rows = [
        dbc.Col(
            components.badge.create_badge_component(b, i),
            xs=12, md=6, lg=4,
            class_name='mb-2'
        )
        for i, b in enumerate(filtered)
    ]
    return dbc.Row(badge_rows, justify='around')
