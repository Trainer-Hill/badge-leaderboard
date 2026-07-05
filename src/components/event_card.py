"""Recap card for a single event: details + full standings.

Badge earners are marked with a check. Used by the home page "Recent Events"
row and can back an event recap elsewhere.
"""
import datetime

import dash_bootstrap_components as dbc
from dash import html

import components.deck_label


def _format_date(value) -> str:
    if not value:
        return ''
    if not hasattr(value, 'strftime'):
        try:
            value = datetime.date.fromisoformat(str(value))
        except ValueError:
            return str(value)
    return value.strftime('%B %-d, %Y')


def _sorted_standings(event):
    standings = [s for s in (event.get('standings') or []) if isinstance(s, dict)]
    return sorted(
        standings,
        key=lambda s: s['placement'] if isinstance(s.get('placement'), int) else 9999,
    )


def create_event_card(event, index=None):
    """Render an event as a recap card."""
    store = event.get('store') or 'Event'
    tier = event.get('tier')
    fmt = event.get('format')
    players = event.get('players')

    meta_badges = []
    if tier:
        meta_badges.append(dbc.Badge(str(tier).title(), class_name='me-1'))
    if fmt:
        meta_badges.append(dbc.Badge(str(fmt), color='secondary', class_name='me-1'))
    if players:
        meta_badges.append(dbc.Badge(f'{players} players', color='info'))

    rows = []
    for standing in _sorted_standings(event):
        earned = bool(standing.get('earned_badge'))
        deck = standing.get('deck')
        check = (
            html.I(className='fas fa-circle-check text-success', title='Earned a badge')
            if earned else ''
        )
        rows.append(html.Tr([
            html.Td(standing.get('placement'), className='text-center align-middle w-0'),
            html.Td(
                standing.get('trainer', ''),
                className='align-middle fw-semibold' if earned else 'align-middle',
            ),
            html.Td(
                components.deck_label.create_label(deck) if deck else '',
                className='align-middle',
            ),
            html.Td(check, className='text-center align-middle w-0'),
        ]))

    table = dbc.Table([
        html.Thead(html.Tr([
            html.Th('#', className='w-0'),
            html.Th('Trainer'),
            html.Th('Deck'),
            html.Th(html.I(className='fas fa-circle-check'), className='w-0 text-center', title='Badge'),
        ])),
        html.Tbody(rows),
    ], size='sm', hover=True, class_name='mb-0')

    return dbc.Card([
        dbc.CardHeader([
            html.Div(store, className='h5 mb-1'),
            html.Div(_format_date(event.get('date')), className='text-muted small mb-2'),
            html.Div(meta_badges),
        ]),
        dbc.CardBody(table, class_name='p-0'),
    ], class_name='event-card overflow-hidden')
