import dash
import dash_auth
import dash_bootstrap_components as dbc
import datetime
import random
import th_helpers.utils.pokemon

from dash import html, dcc, Output, Input, State, clientside_callback, ClientsideFunction

import components.CustomRadioInputAIO
import components.deck_label
import components.layout_access_control
import util.data
import util.discord

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
tier_input = f'{inputs_ids}-tier'
format_input = f'{inputs_ids}-format'
color_input = f'{inputs_ids}-color'
background_input = f'{inputs_ids}-background'
discord_id_input = f'{inputs_ids}-discord-id'
discord_id_container = f'{inputs_ids}-discord-id-container'
save = f'{PREFIX}-save'
edit_select = f'{PREFIX}-edit-select'
edit_index = f'{PREFIX}-edit-index'


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
    data = util.data.read_data()

    trainers = set()
    stores = set()
    formats = set()
    decks = {}
    for badge in data:
        if badge.get('trainer'): trainers.add(badge.get('trainer'))
        if badge.get('store'): stores.add(badge.get('store'))
        if badge.get('format'): formats.add(badge.get('format'))
        if badge.get('deck'):
            if badge['deck']['id'] in decks:
                continue
            decks[badge['deck']['id']] = badge['deck']

    inputs = dbc.Form([
        dbc.Label('Trainer', html_for=trainer_input),
        components.CustomRadioInputAIO.CustomRadioInputAIO(aio_id=trainer_input, options=list(trainers)),

        html.Div([
            dbc.Label('Discord ID', html_for=discord_id_input),
            dbc.Input(id=discord_id_input, placeholder='e.g. 123456789012345678', type='text'),
            dbc.FormText('Enable Developer Mode in Discord → right-click your username → Copy User ID'),
        ], id=discord_id_container, style={'display': 'none'}),

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

        dbc.Label('Color', html_for=color_input),
        dbc.Input(id=color_input, type='color', value='#ffffff'),

        dbc.Label('Background', html_for=background_input),
        dcc.Dropdown(id=background_input,
                     options=['Grass', 'Fire', 'Water', 'Lightning',
                              'Psychic', 'Fighting', 'Dark', 'Metal',
                              'Dragon', 'Fairy', 'Colorless'],
                     value=None),

        dbc.Label('Store', html_for=store_input),
        components.CustomRadioInputAIO.CustomRadioInputAIO(aio_id=store_input, options=list(stores)),

        dbc.Label('Date', html_for=date_input),
        html.Div(dcc.DatePickerSingle(id=date_input, date=datetime.date.today())),

        dbc.Label('Tournament Tier', html_for=tier_input),
        dcc.Dropdown(id=tier_input, options=['League Challenge', 'League Cup', 'Regionals', 'Internationals', 'Locals', 'Online'],
                     value='Locals', clearable=False),

        dbc.Label('Format', html_for=format_input),
        components.CustomRadioInputAIO.CustomRadioInputAIO(aio_id=format_input, options=list(formats)),
    ])

    edit_options = []
    for badge in data:
        trainer = badge.get('trainer', '?')
        store_name = badge.get('store', '?')
        date = badge.get('date')
        date_str = date.isoformat() if date else '?'
        tier = badge.get('tier', '')
        edit_options.append({
            'label': f'{trainer} — {store_name} — {date_str} ({tier})',
            'value': badge.get('_line'),
        })

    edit_section = html.Div([
        dbc.Label('Edit Existing Badge'),
        dcc.Dropdown(
            id=edit_select,
            options=edit_options,
            placeholder='Select a badge to edit...',
            clearable=True,
        ),
        html.Hr(),
    ])

    component = html.Div([
        edit_section,
        inputs,
        dbc.Button([
            html.I(className='fas fa-plus me-1'),
            'Save Badge'
        ], id=save, class_name='float-end'),
        dcc.Store(id=edit_index, data=None),
        dcc.Store(id=deck_store, data=decks),
        html.Div(style={'marginBottom': '256px'})
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
    Output(components.CustomRadioInputAIO.CustomRadioInputAIO.ids.dropdown(trainer_input), 'value', allow_duplicate=True),
    Output(pronoun_input, 'value'),
    Output(deck_input, 'value'),
    Output(components.CustomRadioInputAIO.CustomRadioInputAIO.ids.dropdown(store_input), 'value', allow_duplicate=True),
    Output(date_input, 'date'),
    Output(color_input, 'value'),
    Output(background_input, 'value'),
    Output(tier_input, 'value'),
    Output(components.CustomRadioInputAIO.CustomRadioInputAIO.ids.dropdown(format_input), 'value', allow_duplicate=True),
    Output(edit_index, 'data'),
    Input(edit_select, 'value'),
    groups=ROLES,
    prevent_initial_call=True,
)
def _load_edit_badge(line):
    if line is None:
        return None, 'their', None, None, datetime.date.today().isoformat(), '#ffffff', None, 'Locals', None, None
    badges = util.data.read_data()
    badge = next((b for b in badges if b.get('_line') == line), None)
    if badge is None:
        raise dash.exceptions.PreventUpdate
    date = badge.get('date')
    deck = badge.get('deck') or {}
    return (
        badge.get('trainer'),
        badge.get('pronouns', 'their'),
        deck.get('id'),
        badge.get('store'),
        date.isoformat() if date else None,
        badge.get('color', '#ffffff'),
        badge.get('background'),
        badge.get('tier', 'Locals'),
        badge.get('format'),
        line,
    )


@dash_auth.protected_callback(
    Output(save, 'children'),
    Input(edit_index, 'data'),
    groups=ROLES,
)
def _update_save_label(edit_line):
    if edit_line is not None:
        return [html.I(className='fas fa-save me-1'), 'Update Badge']
    return [html.I(className='fas fa-plus me-1'), 'Save Badge']


@dash_auth.protected_callback(
    Output(discord_id_container, 'style'),
    Output(discord_id_input, 'value'),
    Input(components.CustomRadioInputAIO.CustomRadioInputAIO.ids.dropdown(trainer_input), 'value'),
    groups=ROLES,
    prevent_initial_call=True,
)
def _toggle_discord_id(trainer):
    if not trainer or trainer in util.discord._load_discord_ids():
        return {'display': 'none'}, ''
    return {'display': 'block'}, ''


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
    Output('_pages_location', 'pathname', allow_duplicate=True),
    Input(save, 'n_clicks'),
    State(components.CustomRadioInputAIO.CustomRadioInputAIO.ids.dropdown(trainer_input), 'value'),
    State(pronoun_input, 'value'),
    State(deck_input, 'value'),
    State(components.CustomRadioInputAIO.CustomRadioInputAIO.ids.dropdown(store_input), 'value'),
    State(date_input, 'date'),
    State(deck_store, 'data'),
    State(color_input, 'value'),
    State(background_input, 'value'),
    State(tier_input, 'value'),
    State(components.CustomRadioInputAIO.CustomRadioInputAIO.ids.dropdown(format_input), 'value'),
    State(discord_id_input, 'value'),
    State(edit_index, 'data'),
    groups=ROLES,
    prevent_initial_call=True
)
def _add_badge(n_clicks, trainer, pronouns, deck_id, store, date, decks, color, background, tier, format_type, discord_id, edit_line):
    if not n_clicks:
        raise dash.exceptions.PreventUpdate

    deck = decks.get(deck_id, {})
    badge = {
        'trainer': trainer,
        'pronouns': pronouns,
        'deck': deck,
        'store': store,
        'date': date,
        'color': color,
        'background': background,
        'tier': tier,
        'format': format_type
    }
    if edit_line is not None:
        util.data.update_data(line_index=edit_line, contents=badge)
    else:
        if discord_id:
            util.discord.save_discord_id(trainer, discord_id.strip())
        util.data.append_data(contents=badge)
        util.discord.post_badge(badge)
    return '/'


clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='disableAddButton'),
    Output(save, 'disabled'),
    Input(components.CustomRadioInputAIO.CustomRadioInputAIO.ids.dropdown(trainer_input), 'value'),
    Input(pronoun_input, 'value'),
    Input(deck_input, 'value'),
    Input(components.CustomRadioInputAIO.CustomRadioInputAIO.ids.dropdown(store_input), 'value'),
    Input(date_input, 'date'),
    Input(color_input, 'value'),
    Input(background_input, 'value'),
    Input(tier_input, 'value'),
    Input(components.CustomRadioInputAIO.CustomRadioInputAIO.ids.dropdown(format_input), 'value'),
)

clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='disableDeckAdd'),
    Output(deck_add, 'disabled'),
    Input(deck_name, 'value'),
    Input(deck_icons, 'value'),
    Input(deck_store, 'data')
)
