import dash
import dash_auth
import dash_bootstrap_components as dbc
import random
import th_helpers.components.deck_label
import th_helpers.utils.pokemon

from dash import html, dcc, Output, Input

import components.badge
import components.CustomRadioInputAIO
import components.layout_access_control
import util.data

ROLES = ['admin']

dash.register_page(
    __name__,
    path='/admin',
)

PREFIX = 'admin'
badge_id = f'{PREFIX}-badge'
# inputs
inputs_ids = f'{PREFIX}-inputs'
trainer_input = f'{inputs_ids}-trainer'
pronoun_input = f'{inputs_ids}-pronoun'
deck_input = f'{inputs_ids}-deck'
deck_icons = f'{deck_input}-icons'
deck_name = f'{deck_input}-name'
deck_add = f'{deck_input}-add'
store_input = f'{inputs_ids}-store'
date_input = f'{inputs_ids}-date'

# inputs for store should be similar to our tag system where we can add items/its based on what we got currently
# deck should be saved as object of icons to recreate
# maybe this should be how all the inputs work and we always manually create decks? that doesn't sound so bad


def _create_pokemon_options():
    decks = th_helpers.utils.pokemon.pokemon_as_decks
    if not decks:
        return []
    random.shuffle(decks)
    for d in decks:
        d['icons'] = [th_helpers.components.deck_label.get_pokemon_icon(icon) for icon in d['icons']]
    options = [{
        'label': th_helpers.components.deck_label.format_label(deck),
        'value': deck['id'],
        'search': deck['name'],
    } for deck in decks]
    return options


@components.layout_access_control.enforce_roles(ROLES)
def layout():
    data = util.data.read_data('badge_dump.jsonl')

    trainers = []
    stores = []
    decks = []
    for badge in data:
        if badge.get('trainer'): trainers.append(badge.get('trainer'))
        if badge.get('store'): stores.append(badge.get('store'))

    inputs = html.Div([
        dbc.Label('Trainer', html_for=trainer_input),
        components.CustomRadioInputAIO.CustomRadioInputAIO(aio_id=trainer_input, options=trainers),

        dbc.Label('Pronouns', html_for=pronoun_input),
        dcc.Dropdown(id=pronoun_input, options=['their', 'her', 'his'], value='their', clearable=False),

        dbc.Label('Deck', html_for=deck_input),
        dcc.Dropdown(id=deck_input),
        dcc.Dropdown(id=deck_icons, multi=True, placeholder='Icons', options=_create_pokemon_options()),
        dbc.InputGroup([
            dbc.Input(id=deck_name, placeholder='Enter custom name', value=''),
            dbc.Button(html.I(className='fas fa-plus'), id=deck_add, n_clicks=0, disabled=True)
        ]),

        dbc.Label('Store', html_for=store_input),
        components.CustomRadioInputAIO.CustomRadioInputAIO(aio_id=store_input, options=stores),

        dbc.Label('Date', html_for=date_input),
        dcc.DatePickerSingle(id=date_input),
    ])

    component = html.Div([
        'Admin',
        inputs,
        components.badge.create_badge_component(index=badge_id),
        html.Button([
            html.I(className='fas fas-plus me-1'),
            'Inc'
        ], id='add'),
        html.Div(id='out')
    ])
    return component


@dash_auth.protected_callback(
    Output('out', 'children'),
    Input('add', 'n_clicks'),
    groups=ROLES
)
def _update_clicks(n_clicks):
    if not n_clicks:
        return 'No clicks yet'    # perhaps we do a file per year

    util.data.append_datafile('badge_dump.jsonl', {'clicks': n_clicks})
    return n_clicks
