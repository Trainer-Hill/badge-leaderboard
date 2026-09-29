"""Admin tool for mass-editing trainer names and decks.

Fixes two recurring data-entry problems after the fact, across every season's
data file (badges-mode and events-mode alike -- see util.mass_edit):

- A trainer recorded under a placeholder/abbreviated name (e.g. a lower
  division "John D.") who's since started earning badges under their real
  name ("John Doe") -- rename folds every past record onto the new name,
  with an optional pronoun update along for the ride.
- A deck recorded with a placeholder/sample Pokemon before the real sprite
  was available (e.g. plain "Excadrill" standing in for "Mega Excadrill") --
  merge repoints every past record at the real deck.

Picking an existing trainer/deck as the target merges identities together;
naming a brand-new one is just a rename.
"""
import random

import dash
import dash_auth
import dash_bootstrap_components as dbc
import th_helpers.utils.pokemon
from dash import html, dcc, Output, Input, State, clientside_callback, ClientsideFunction

import components.CustomRadioInputAIO
import components.deck_label
import components.layout_access_control
import util.discord
import util.mass_edit

CRI = components.CustomRadioInputAIO.CustomRadioInputAIO

ROLES = ['admin']

dash.register_page(
    __name__,
    path='/admin/edit',
    name='Mass Edit',
)

PREFIX = 'edit'
rename_from = f'{PREFIX}-rename-from'
rename_to_aio = f'{PREFIX}-rename-to'
rename_save = f'{PREFIX}-rename-save'
rename_status = f'{PREFIX}-rename-status'

pronoun_value = f'{PREFIX}-pronoun-value'

merge_from_decks = f'{PREFIX}-merge-from'
merge_target = f'{PREFIX}-merge-target'
merge_save = f'{PREFIX}-merge-save'
merge_status = f'{PREFIX}-merge-status'
deck_store = f'{PREFIX}-merge-deck-store'
deck_icons = f'{PREFIX}-merge-deck-icons'
deck_name = f'{PREFIX}-merge-deck-name'
deck_add = f'{PREFIX}-merge-deck-add'


def _create_pokemon_options():
    decks = th_helpers.utils.pokemon.pokemon_as_decks
    if not decks:
        return []
    random.shuffle(decks)
    return [{
        'label': components.deck_label.create_label(deck),
        'value': deck['id'],
        'search': deck['name'],
    } for deck in decks]


def _trainer_options(counts):
    return [
        {'label': f'{name} ({count})', 'value': name}
        for name, count in sorted(counts.items(), key=lambda kv: kv[0].lower())
    ]


def _deck_from_options(deck_entries):
    items = sorted(
        deck_entries.items(),
        key=lambda kv: (-kv[1]['count'], (kv[1]['deck'].get('name') or '').lower()),
    )
    return [
        {
            'label': html.Span([
                components.deck_label.create_label(entry['deck']),
                html.Span(f" — {entry['count']}", className='text-muted ms-1'),
            ], className='d-flex align-items-center'),
            'value': deck_id,
            'search': entry['deck'].get('name') or deck_id,
        }
        for deck_id, entry in items
    ]


def _deck_target_options(decks_by_id):
    items = sorted(decks_by_id.items(), key=lambda kv: (kv[1].get('name') or '').lower())
    return [
        {'label': components.deck_label.create_label(deck), 'value': deck_id}
        for deck_id, deck in items
    ]


@components.layout_access_control.enforce_roles(ROLES)
def layout(**kwargs):
    trainer_counts = util.mass_edit.trainer_counts()
    deck_entries = util.mass_edit.deck_counts()
    decks_by_id = {deck_id: entry['deck'] for deck_id, entry in deck_entries.items()}

    trainer_tab = dbc.Card(dbc.CardBody([
        html.P(
            'Pick one or more names to fold into a correct one. Picking an '
            'existing name as the target merges those trainers together; '
            'typing a new name just corrects the spelling. Optionally set '
            'their pronouns at the same time.',
            className='text-muted small',
        ),
        dbc.Label('Trainer(s) to rename', html_for=rename_from),
        dcc.Dropdown(id=rename_from, options=_trainer_options(trainer_counts),
                     multi=True, placeholder='Select trainer(s)…'),
        dbc.Label('Correct name', html_for=CRI.ids.dropdown(rename_to_aio), class_name='mt-3'),
        CRI(aio_id=rename_to_aio, options=sorted(trainer_counts, key=str.lower)),
        dbc.Label('Pronouns (optional)', html_for=pronoun_value, class_name='mt-3'),
        dcc.Dropdown(id=pronoun_value, options=['their', 'her', 'his'],
                     placeholder='Leave existing pronouns…'),
        dbc.Button([html.I(className='fas fa-check me-1'), 'Apply Rename'],
                   id=rename_save, color='primary', class_name='mt-3', disabled=True),
        html.Div(id=rename_status, className='mt-3'),
    ]))

    deck_tab = dbc.Card(dbc.CardBody([
        html.P(
            'Pick one or more decks (e.g. a sample placeholder) to merge, '
            'then the deck they should become everywhere they were used.',
            className='text-muted small',
        ),
        dbc.Label('Deck(s) to merge', html_for=merge_from_decks),
        dcc.Dropdown(id=merge_from_decks, options=_deck_from_options(deck_entries),
                     multi=True, placeholder='Select deck(s)…'),
        dbc.Label('Target deck', html_for=merge_target, class_name='mt-3'),
        dcc.Dropdown(id=merge_target, options=_deck_target_options(decks_by_id),
                     placeholder='Select the deck to merge into…'),
        html.Div([
            dbc.Label('…or create a new target deck', class_name='mt-3'),
            dcc.Dropdown(id=deck_icons, multi=True, placeholder='Icons',
                         options=_create_pokemon_options()),
            dbc.InputGroup([
                dbc.Input(id=deck_name, placeholder='New deck name', value=''),
                dbc.Button(html.I(className='fas fa-plus'), id=deck_add, n_clicks=0, disabled=True),
            ], class_name='mt-1'),
        ]),
        dbc.Button([html.I(className='fas fa-check me-1'), 'Apply Merge'],
                   id=merge_save, color='primary', class_name='mt-3', disabled=True),
        html.Div(id=merge_status, className='mt-3'),
        dcc.Store(id=deck_store, data=decks_by_id),
    ]))

    return dbc.Container([
        html.H2('Mass Edit'),
        dbc.Tabs([
            dbc.Tab(trainer_tab, label='Rename / Merge Trainer'),
            dbc.Tab(deck_tab, label='Merge Decks'),
        ]),
        html.Div(style={'marginBottom': '256px'}),
    ], fluid=True)


@dash_auth.protected_callback(
    Output(rename_status, 'children'),
    Output(rename_from, 'options'),
    Output(rename_from, 'value'),
    Output(CRI.ids.dropdown(rename_to_aio), 'options', allow_duplicate=True),
    Output(CRI.ids.dropdown(rename_to_aio), 'value', allow_duplicate=True),
    Output(pronoun_value, 'value'),
    Input(rename_save, 'n_clicks'),
    State(rename_from, 'value'),
    State(CRI.ids.dropdown(rename_to_aio), 'value'),
    State(pronoun_value, 'value'),
    groups=ROLES,
    prevent_initial_call=True,
)
def _apply_rename(n_clicks, from_trainers, to_trainer, pronoun):
    if not n_clicks:
        raise dash.exceptions.PreventUpdate
    from_trainers = [t for t in (from_trainers or []) if t]
    to_trainer = (to_trainer or '').strip()
    if not from_trainers or not to_trainer:
        return (dbc.Alert('Pick at least one trainer and a correct name.', color='danger'),
                dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update)

    total = 0
    for name in from_trainers:
        total += util.mass_edit.rename_trainer(name, to_trainer)
        if name != to_trainer:
            util.discord.rename_trainer(name, to_trainer)

    pronoun_note = ''
    if pronoun:
        pronoun_touched = util.mass_edit.update_pronouns(to_trainer, pronoun)
        pronoun_note = f' Set pronouns to "{pronoun}" on {pronoun_touched} record(s).'

    counts = util.mass_edit.trainer_counts()
    options = _trainer_options(counts)
    status = dbc.Alert(
        f'Updated {total} record(s): {", ".join(from_trainers)} → {to_trainer}.{pronoun_note}',
        color='success',
    )
    return status, options, [], options, None, None


@dash_auth.protected_callback(
    Output(deck_store, 'data'),
    Input(deck_add, 'n_clicks'),
    State(deck_name, 'value'),
    State(deck_icons, 'value'),
    State(deck_store, 'data'),
    groups=ROLES,
    prevent_initial_call=True,
)
def _add_deck(n_clicks, name, icons, store):
    if not n_clicks or not name:
        return store or {}
    store = store or {}
    deck_id = name.lower().replace(' ', '')
    store[deck_id] = {'id': deck_id, 'name': name, 'icons': icons or []}
    return store


@dash_auth.protected_callback(
    Output(merge_target, 'options'),
    Input(deck_store, 'data'),
    groups=ROLES,
)
def _sync_target_options(store):
    return _deck_target_options(store or {})


@dash_auth.protected_callback(
    Output(merge_target, 'value', allow_duplicate=True),
    Input(deck_add, 'n_clicks'),
    State(deck_name, 'value'),
    groups=ROLES,
    prevent_initial_call=True,
)
def _select_new_target(n_clicks, name):
    if not n_clicks or not name:
        raise dash.exceptions.PreventUpdate
    return name.lower().replace(' ', '')


@dash_auth.protected_callback(
    Output(merge_status, 'children'),
    Output(merge_from_decks, 'options'),
    Output(merge_from_decks, 'value'),
    Input(merge_save, 'n_clicks'),
    State(merge_from_decks, 'value'),
    State(merge_target, 'value'),
    State(deck_store, 'data'),
    groups=ROLES,
    prevent_initial_call=True,
)
def _apply_merge(n_clicks, from_ids, target_id, store):
    if not n_clicks:
        raise dash.exceptions.PreventUpdate
    from_ids = [i for i in (from_ids or []) if i]
    target_deck = (store or {}).get(target_id)
    if not from_ids or not target_deck:
        return (dbc.Alert('Pick at least one deck and a target deck.', color='danger'),
                dash.no_update, dash.no_update)

    total = util.mass_edit.replace_deck(from_ids, target_deck)
    counts = util.mass_edit.deck_counts()
    status = dbc.Alert(
        f"Updated {total} record(s) to use {target_deck.get('name')}.",
        color='success',
    )
    return status, _deck_from_options(counts), []


clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='disableRenameSave'),
    Output(rename_save, 'disabled'),
    Input(rename_from, 'value'),
    Input(CRI.ids.dropdown(rename_to_aio), 'value'),
)

clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='disableDeckMergeSave'),
    Output(merge_save, 'disabled'),
    Input(merge_from_decks, 'value'),
    Input(merge_target, 'value'),
)

clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='disableDeckAdd'),
    Output(deck_add, 'disabled'),
    Input(deck_name, 'value'),
    Input(deck_icons, 'value'),
    Input(deck_store, 'data'),
)
