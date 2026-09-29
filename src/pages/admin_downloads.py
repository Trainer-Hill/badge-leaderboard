"""Admin page listing every data file available for download.

Just a friendlier front end for the existing /api/export-badges endpoint
(see app.py) -- that endpoint already validates the filename against the same
util.seasons.exportable_files() allowlist this page lists from.
"""
import dash
import dash_bootstrap_components as dbc
from dash import html

import components.layout_access_control
import util.seasons

ROLES = ['admin']

dash.register_page(
    __name__,
    path='/admin/downloads',
    name='Downloads',
)


def _row(entry):
    return html.Tr([
        html.Td(entry['label']),
        html.Td(html.Code(entry['filename'])),
        html.Td(
            dbc.Button(
                [html.I(className='fas fa-download me-1'), 'Download'],
                href=f"/api/export-badges?file={entry['filename']}",
                size='sm', color='primary', outline=True,
                external_link=True,
            ),
            className='text-end',
        ),
    ])


@components.layout_access_control.enforce_roles(ROLES)
def layout(**kwargs):
    files = util.seasons.exportable_files()
    table = dbc.Table(
        [html.Tbody([_row(f) for f in files])],
        bordered=False, hover=True, responsive=True, class_name='align-middle',
    )
    return dbc.Container([
        html.H2('Downloads'),
        html.P('Raw newline-delimited JSON, one file per season data source.',
               className='text-muted'),
        table,
    ], fluid=True)
