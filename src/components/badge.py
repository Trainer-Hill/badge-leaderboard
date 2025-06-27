import dash_bootstrap_components as dbc
from dash import html

import components.deck_label

PREFIX = 'badge'
trainer_id = f'{PREFIX}-trainer'
pronoun_id = f'{PREFIX}-pronoun'
deck_id = f'{PREFIX}-deck'
store_id = f'{PREFIX}-store'
date_id = f'{PREFIX}-date'


def create_badge_component(data=None, index=None):
    if data is None:
        data = {}
    background_color = data.get('color')
    style = {'backgroundColor': background_color} if background_color else {}
    header = html.H4(data.get('trainer', ''), id={'type': trainer_id, 'index': index})
    background = data.get('background')
    tier = data.get('tier')
    tier_comp = dbc.Badge(tier, class_name='me-1') if tier else None
    component = dbc.Card([
        html.Div(style={
            'backgroundImage': f"url('/assets/energy_types/{background.lower()}.svg')" if background else 'none'
        }, className='gym-badge-bg'),
        header,
        html.Div([
            'earned ',
            html.Span(data.get('pronouns', 'their'), id={'type': pronoun_id, 'index': index})],
            className='mb-2'),
        html.H4(
            components.deck_label.create_label(data.get('deck')),
            id={'type': deck_id, 'index': index},
            className='d-flex justify-content-around'),
        html.Div([
            tier_comp,
            'badge at ',
            html.Strong(data.get('store'), id={'type': store_id, 'index': index})]),
        html.Div([
            ' on ',
            html.Span(data.get('date'), id={'type': date_id, 'index': index})]),
    ], class_name='text-center gym-badge', body=True, style=style)
    return component
