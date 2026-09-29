"""Admin index -- links out to every admin tool.

Kept deliberately dumb (no data reads, no callbacks) so it never breaks; each
tool lives on its own page/route.
"""
import dash
import dash_bootstrap_components as dbc
from dash import html

import components.layout_access_control

ROLES = ['admin']

dash.register_page(
    __name__,
    path='/admin',
    name='Admin',
)

TOOLS = [
    {
        'title': 'Mass Edit',
        'icon': 'fa-solid fa-arrows-turn-to-dots',
        'href': '/admin/edit',
        'description': (
            'Rename or merge a trainer across every badge/event they appear '
            'in, or repoint a placeholder deck (e.g. a sample icon) at the '
            'real one everywhere it was used.'
        ),
    },
    {
        'title': 'Downloads',
        'icon': 'fa-solid fa-download',
        'href': '/admin/downloads',
        'description': 'Download the raw JSONL for any season\'s data file.',
    },
    {
        'title': 'Add Event',
        'icon': 'fa-solid fa-calendar-plus',
        'href': '/admin/event',
        'description': 'Record an event and its standings for the current (events-mode) season.',
    },
    {
        'title': 'Add Badge',
        'icon': 'fa-solid fa-plus',
        'href': '/admin/badge',
        'description': 'Add or edit a single badge directly. Legacy -- only applies to badges-mode seasons.',
        'muted': True,
    },
]


def _tool_card(tool):
    header = html.Span([
        html.I(className=f"{tool['icon']} me-2"),
        tool['title'],
    ])
    return dbc.Col(
        dbc.Card(
            dbc.CardBody([
                html.H5(header, className='card-title'),
                html.P(tool['description'], className='card-text text-muted small'),
                dbc.Button('Open', href=tool['href'], color='secondary' if tool.get('muted') else 'primary',
                           outline=tool.get('muted', False), size='sm'),
            ]),
            class_name='h-100',
        ),
        md=6, lg=4, class_name='mb-3',
    )


@components.layout_access_control.enforce_roles(ROLES)
def layout(**kwargs):
    return dbc.Container([
        html.H2('Admin', className='mb-3'),
        dbc.Row([_tool_card(tool) for tool in TOOLS]),
    ], fluid=True)
