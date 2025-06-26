import dash
import dash_auth
import dash_bootstrap_components as dbc
import datetime
import random
import th_helpers.utils.pokemon

from dash import html, dcc, Output, Input, State, clientside_callback, ClientsideFunction

import components.badge
import components.CustomRadioInputAIO
import components.deck_label
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
deck_store = f'{inputs_ids}-deck-store'
# TODO color and background and tournament tier
save = f'{PREFIX}-save'


def _create_pokemon_options():
    decks = th_helpers.utils.pokemon.pokemon_as_decks
    if not decks:
        return []
    random.shuffle(decks)
    options = [{
        'label': components.deck_label.create_label(deck),
        'value': deck['id'],
        'search': deck['name'],
    } for deck in decks]
    return options


@components.layout_access_control.enforce_roles(ROLES)
def layout():
    data = util.data.read_data('badges.jsonl')

    trainers = set()
    stores = set()
    decks = {}
    for badge in data:
        if badge.get('trainer'): trainers.add(badge.get('trainer'))
        if badge.get('store'): stores.add(badge.get('store'))
        if badge.get('deck'):
            if badge['deck']['id'] in decks:
                continue
            decks[badge['deck']['id']] = badge['deck']

    inputs = html.Div([
        dbc.Label('Trainer', html_for=trainer_input),
        components.CustomRadioInputAIO.CustomRadioInputAIO(aio_id=trainer_input, options=list(trainers)),

        dbc.Label('Pronouns', html_for=pronoun_input),
        dcc.Dropdown(id=pronoun_input, options=['their', 'her', 'his'], value='their', clearable=False),

        dbc.Label('Deck', html_for=deck_input),
        dcc.Dropdown(id=deck_input),
        dbc.Label('Add Deck', html_for=deck_name),
        dcc.Dropdown(id=deck_icons, multi=True, placeholder='Icons', options=_create_pokemon_options()),
        dbc.InputGroup([
            dbc.Input(id=deck_name, placeholder='Enter custom name', value=''),
            dbc.Button(html.I(className='fas fa-plus'), id=deck_add, n_clicks=0, disabled=True)
        ]),

        dbc.Label('Store', html_for=store_input),
        components.CustomRadioInputAIO.CustomRadioInputAIO(aio_id=store_input, options=list(stores)),

        dbc.Label('Date', html_for=date_input),
        html.Div(dcc.DatePickerSingle(id=date_input, date=datetime.date.today())),
    ])

    component = html.Div([
        'Admin',
        inputs,
        components.badge.create_badge_component(index=badge_id),
        dbc.Button([
            html.I(className='fas fa-plus me-1'),
            'Save Badge'
        ], id=save, class_name='float-end'),
        dcc.Store(id=deck_store, data=decks),
        html.Div(id='out')
    ])
    return component


@dash_auth.protected_callback(
    Output(deck_input, 'options'),
    Input(deck_store, 'data'),
    groups=ROLES
)
def _init_deck_options(store):
    """Initialize deck dropdown options from stored decks"""
    if not store:
        return []
    return [{'label': components.deck_label.create_label(deck), 'value': deck['id']} for deck in store.values()]


@dash_auth.protected_callback(
    Output(deck_store, 'data'),
    Input(deck_add, 'n_clicks'),
    State(deck_name, 'value'),
    State(deck_icons, 'value'),
    State(deck_store, 'data'),
    groups=ROLES,
)
def _add_deck(n_clicks, name, icons, store):
    """Store a newly created deck"""
    if not n_clicks:
        return store
    if store is None:
        store = []
    deck_id = name.lower().replace(' ', '')
    store[deck_id] = {'id': deck_id, 'name': name, 'icons': icons or []}
    return store


@dash_auth.protected_callback(
    Output(save, 'disabled', allow_duplicate=True),
    Input(save, 'n_clicks'),
    State(components.CustomRadioInputAIO.CustomRadioInputAIO.ids.dropdown(trainer_input), 'value'),
    State(pronoun_input, 'value'),
    State(deck_input, 'value'),
    State(components.CustomRadioInputAIO.CustomRadioInputAIO.ids.dropdown(store_input), 'value'),
    State(date_input, 'date'),
    State(deck_store, 'data'),
    groups=ROLES,
    prevent_initial_call=True
)
def _add_badge(n_clicks, trainer, pronouns, deck_id, store, date, decks):
    """Append a badge to the badges file"""
    if not n_clicks:
        raise dash.exceptions.PreventUpdate

    deck = decks.get(deck_id, {})
    badge = {
        'trainer': trainer,
        'pronouns': pronouns,
        'deck': deck,
        'store': store,
        'date': date,
    }
    util.data.append_datafile('badges.jsonl', badge)
    return True


clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='disableAddButton'),
    Output(save, 'disabled'),
    Input(components.CustomRadioInputAIO.CustomRadioInputAIO.ids.dropdown(trainer_input), 'value'),
    Input(pronoun_input, 'value'),
    Input(deck_input, 'value'),
    Input(components.CustomRadioInputAIO.CustomRadioInputAIO.ids.dropdown(store_input), 'value'),
    Input(date_input, 'date'),
)

clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='disableDeckAdd'),
    Output(deck_add, 'disabled'),
    Input(deck_name, 'value'),
    Input(deck_icons, 'value'),
    Input(deck_store, 'data')
)
