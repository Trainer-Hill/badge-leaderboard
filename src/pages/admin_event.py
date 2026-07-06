"""Admin page for entering an event and its standings.

Saving appends one event record to the events-mode season's data file. Badges
are derived from standings flagged ``earned_badge`` (see util.normalize), and
Discord pings go out to badge earners only.

Store, format, and per-player trainer are select-or-add-new controls populated
from existing data (same pattern as the badge admin). Pronouns, color,
background, and an optional Discord ID are only collected for badge earners.
"""
import random

import dash
import dash_auth
import dash_bootstrap_components as dbc
import datetime
import th_helpers.utils.pokemon
from dash import html, dcc, Output, Input, State, ALL, MATCH, Patch, clientside_callback, ClientsideFunction

import components.CustomRadioInputAIO
import components.deck_label
import components.layout_access_control
import util.auth
import util.badges
import util.data
import util.discord
import util.seasons

CRI = components.CustomRadioInputAIO.CustomRadioInputAIO

ROLES = ['admin']

dash.register_page(__name__, path='/admin/event')

PREFIX = 'evt'
# Event-level ids
store_aio = f'{PREFIX}-store-aio'
format_aio = f'{PREFIX}-format-aio'
date_input = f'{PREFIX}-date'
players_input = f'{PREFIX}-players'
tier_input = f'{PREFIX}-tier'
# Deck builder
deck_store = f'{PREFIX}-deck-store'
deck_icons = f'{PREFIX}-deck-icons'
deck_name = f'{PREFIX}-deck-name'
deck_add = f'{PREFIX}-deck-add'
# Standings
standings_container = f'{PREFIX}-standings'
next_index_store = f'{PREFIX}-next-index'
add_player = f'{PREFIX}-add-player'
badge_hint = f'{PREFIX}-badge-hint'
save = f'{PREFIX}-save'
status = f'{PREFIX}-status'
# Editing an existing event
event_select = f'{PREFIX}-event-select'
edit_index = f'{PREFIX}-edit-index'

BACKGROUNDS = ['Grass', 'Fire', 'Water', 'Lightning', 'Psychic',
               'Fighting', 'Dark', 'Metal', 'Dragon', 'Fairy', 'Colorless']
TIERS = ['Locals', 'Online', 'League Challenge', 'League Cup',
         'Regionals', 'Internationals', 'Worlds']


def _events_season():
    """Return the (latest) events-mode season year, or None if unconfigured."""
    events_seasons = [
        y for y in util.seasons.available_seasons()
        if util.seasons.mode_for(y) == 'events'
    ]
    return max(events_seasons) if events_seasons else None


def _event_options(season):
    """Dropdown options for editing an existing event (value = file line)."""
    options = []
    for e in util.seasons.read_events(season):
        date = e.get('date')
        date_str = date.isoformat() if hasattr(date, 'isoformat') else (date or '?')
        players = e.get('players')
        label = f"{e.get('store', '?')} — {date_str}"
        if players:
            label += f" — {players}p"
        options.append({'label': label, 'value': e.get('_line')})
    return options


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


def _deck_options(store):
    if not store:
        return []
    return [
        {'label': components.deck_label.create_label(deck), 'value': deck['id']}
        for deck in store.values()
    ]


def _trainer_select(index, options, value=None):
    """Select-or-add-new trainer control with pattern-matched ids."""
    return html.Div([
        dcc.Dropdown(
            id={'type': f'{PREFIX}-trainer-dd', 'index': index},
            options=options, value=value, placeholder='Trainer',
        ),
        dbc.InputGroup([
            dbc.Input(id={'type': f'{PREFIX}-trainer-in', 'index': index},
                      placeholder='New trainer', value=''),
            dbc.Button(html.I(className='fas fa-plus'),
                       id={'type': f'{PREFIX}-trainer-add', 'index': index}, disabled=True),
        ], size='sm', class_name='mt-1'),
    ])


def _standing_row(index, placement, earned, deck_options, trainer_options, standing=None):
    """Build a single standings row with pattern-matching ids.

    When ``standing`` (an existing standing dict) is given, its trainer, deck,
    pronouns, color, and background prefill the row -- used when editing an event.
    """
    standing = standing or {}
    trainer_value = standing.get('trainer')
    deck = standing.get('deck')
    deck_value = deck.get('id') if isinstance(deck, dict) else deck
    pronoun_value = standing.get('pronouns', 'their')
    color_value = standing.get('color', '#ffffff')
    background_value = standing.get('background')

    badge_style = {} if earned else {'display': 'none'}
    return dbc.Card(dbc.CardBody(dbc.Row([
        dbc.Col(dbc.Input(
            id={'type': f'{PREFIX}-placement', 'index': index},
            type='number', min=1, value=placement, size='sm',
        ), xs=4, md=1),
        dbc.Col(_trainer_select(index, trainer_options, trainer_value), xs=8, md=4),
        dbc.Col(dcc.Dropdown(
            id={'type': f'{PREFIX}-deck', 'index': index},
            options=deck_options, value=deck_value, placeholder='Deck',
        ), xs=6, md=3),
        dbc.Col(dbc.Switch(
            id={'type': f'{PREFIX}-earned', 'index': index},
            label='Badge', value=earned,
        ), xs=4, md=3),
        dbc.Col(dbc.Button(
            html.I(className='fas fa-trash'),
            id={'type': f'{PREFIX}-delete', 'index': index},
            color='link', size='sm', class_name='text-danger p-0',
            title='Remove player',
        ), xs=2, md=1, class_name='text-end'),
        dbc.Col(dbc.Row([
            dbc.Col([
                dbc.Label('Pronouns', size='sm', class_name='mb-0'),
                dcc.Dropdown(
                    id={'type': f'{PREFIX}-pronouns', 'index': index},
                    options=['their', 'her', 'his'], value=pronoun_value, clearable=False,
                ),
            ], xs=6, md=3),
            dbc.Col([
                dbc.Label('Color', size='sm', class_name='mb-0'),
                dbc.Input(id={'type': f'{PREFIX}-color', 'index': index},
                          type='color', value=color_value, size='sm'),
            ], xs=6, md=2),
            dbc.Col([
                dbc.Label('Background', size='sm', class_name='mb-0'),
                dcc.Dropdown(id={'type': f'{PREFIX}-background', 'index': index},
                             options=BACKGROUNDS, value=background_value, placeholder='Background'),
            ], xs=6, md=3),
            dbc.Col([
                # Shown when we already have a Discord ID for the picked trainer.
                html.Small(id={'type': f'{PREFIX}-discord-status', 'index': index},
                           className='text-success d-block'),
                # Hidden once a ping is already on file (no ID needed then).
                html.Div([
                    dbc.Label('Discord ID (if new)', size='sm', class_name='mb-0'),
                    dbc.Input(id={'type': f'{PREFIX}-discord', 'index': index},
                              placeholder='optional', size='sm'),
                ], id={'type': f'{PREFIX}-discord-wrap', 'index': index}),
            ], xs=6, md=4),
        ], class_name='g-2'),
            id={'type': f'{PREFIX}-badge-fields', 'index': index},
            style=badge_style, xs=12),
    ], class_name='g-2 align-items-start')), class_name='mb-2')


@components.layout_access_control.enforce_roles(ROLES)
def layout(**kwargs):
    season = _events_season()
    if season is None:
        return dbc.Container([
            html.H2('Enter Event'),
            dbc.Alert('No events-mode season is configured.', color='warning'),
        ], fluid=True)

    badges = util.seasons.read_badges()
    stores = sorted({b.get('store') for b in badges if b.get('store')})
    formats = sorted({b.get('format') for b in badges if b.get('format')} | {'Standard'})
    trainers = sorted({b.get('trainer') for b in badges if b.get('trainer')})
    decks = {}
    for b in badges:
        deck = b.get('deck')
        if isinstance(deck, dict) and deck.get('id') and deck['id'] not in decks:
            decks[deck['id']] = deck

    deck_options = _deck_options(decks)

    event_fields = dbc.Row([
        dbc.Col([
            dbc.Label('Store'),
            CRI(aio_id=store_aio, options=stores),
        ], md=4),
        dbc.Col([
            dbc.Label('Date', html_for=date_input),
            html.Div(dcc.DatePickerSingle(id=date_input, date=datetime.date.today())),
        ], md=2),
        dbc.Col([
            dbc.Label('Total Players', html_for=players_input),
            dbc.Input(id=players_input, type='number', min=0, placeholder='e.g. 42',
                      debounce=True),
            dbc.FormText('Sets up standings rows automatically.'),
        ], md=2),
        dbc.Col([
            dbc.Label('Tier', html_for=tier_input),
            dcc.Dropdown(id=tier_input, options=TIERS, value='Locals', clearable=False),
        ], md=4),
        dbc.Col([
            dbc.Label('Format'),
            CRI(aio_id=format_aio, options=formats, value='Standard'),
        ], md=4),
    ], class_name='g-2 mb-3')

    deck_builder = dbc.Row([
        dbc.Col(dcc.Dropdown(id=deck_icons, multi=True, placeholder='Icons',
                             options=_create_pokemon_options()), md=5),
        dbc.Col(dbc.InputGroup([
            dbc.Input(id=deck_name, placeholder='New deck name', value=''),
            dbc.Button(html.I(className='fas fa-plus'), id=deck_add, n_clicks=0, disabled=True),
        ]), md=5),
    ], class_name='g-2 mb-3')

    edit_section = dbc.Row(dbc.Col([
        dbc.Label('Edit existing event', html_for=event_select),
        dcc.Dropdown(id=event_select, options=_event_options(season),
                     placeholder='Select an event to edit…', clearable=True),
    ], md=6), class_name='mb-3')

    return dbc.Container([
        html.H2(f'Enter Event — {season} Season'),
        html.P('Record an event and its standings. Toggle "Badge" for each trainer '
               'who earned one; 1st place is on by default. Pronouns/color/background '
               'and Discord pings apply to badge earners only.'),
        edit_section,
        html.Hr(),
        event_fields,
        html.Hr(),
        html.H5('Add a deck'),
        html.P('Create decks here, then pick them per player below.', className='text-muted small'),
        deck_builder,
        html.Hr(),
        html.H5('Standings'),
        html.Div(html.Span(id=badge_hint, className='text-muted small'), className='mb-2'),
        html.Div([_standing_row(0, 1, True, deck_options, trainers)], id=standings_container),
        dbc.Button([html.I(className='fas fa-plus me-1'), 'Add Player'],
                   id=add_player, color='secondary', outline=True, n_clicks=0,
                   class_name='mt-1'),
        html.Hr(),
        html.Div(id=status, className='mb-2'),
        dbc.Button([html.I(className='fas fa-save me-1'), 'Save Event'],
                   id=save, color='primary', n_clicks=0),
        dcc.Store(id=deck_store, data=decks),
        dcc.Store(id=next_index_store, data=1),
        dcc.Store(id=edit_index, data=None),
        html.Div(style={'marginBottom': '256px'}),
    ], fluid=True)


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
    Output({'type': f'{PREFIX}-deck', 'index': ALL}, 'options'),
    Input(deck_store, 'data'),
    State({'type': f'{PREFIX}-deck', 'index': ALL}, 'options'),
    groups=ROLES,
)
def _sync_deck_options(store, existing):
    options = _deck_options(store)
    return [options for _ in existing]


def _latest_pronoun(trainer):
    """Return the trainer's most recently recorded pronoun (default 'their')."""
    if not trainer:
        return 'their'
    # read_badges() is sorted newest-first, so the first match wins.
    for b in util.seasons.read_badges():
        if b.get('trainer') == trainer and b.get('pronouns'):
            return b['pronouns']
    return 'their'


@dash_auth.protected_callback(
    Output({'type': f'{PREFIX}-discord-status', 'index': MATCH}, 'children'),
    Output({'type': f'{PREFIX}-discord-wrap', 'index': MATCH}, 'style'),
    Output({'type': f'{PREFIX}-pronouns', 'index': MATCH}, 'value'),
    Input({'type': f'{PREFIX}-trainer-dd', 'index': MATCH}, 'value'),
    groups=ROLES,
)
def _on_trainer_selected(trainer):
    """When a trainer is picked, prefill their last-used pronoun and flag whether
    a Discord ping is already on file (hiding the "Discord ID" input if so)."""
    pronoun = _latest_pronoun(trainer)
    if trainer and trainer in util.discord._load_discord_ids():
        return (
            html.Span([html.I(className='fas fa-circle-check me-1'),
                       'Ping ready for this trainer']),
            {'display': 'none'},
            pronoun,
        )
    return '', {}, pronoun


@dash_auth.protected_callback(
    Output(standings_container, 'children'),
    Output(next_index_store, 'data'),
    Input(add_player, 'n_clicks'),
    State(next_index_store, 'data'),
    State(players_input, 'value'),
    State(deck_store, 'data'),
    State({'type': f'{PREFIX}-placement', 'index': ALL}, 'id'),
    State({'type': f'{PREFIX}-trainer-dd', 'index': ALL}, 'options'),
    groups=ROLES,
    prevent_initial_call=True,
)
def _add_player(n_clicks, next_index, players, store, placement_ids, trainer_option_lists):
    if not n_clicks:
        raise dash.exceptions.PreventUpdate
    # next_index is a monotonic unique row id; placement follows the current row
    # count. Patch appends without disturbing values already entered.
    trainer_options = trainer_option_lists[0] if trainer_option_lists else []
    placement = len(placement_ids) + 1
    patched = Patch()
    patched.append(_standing_row(next_index, placement,
                                 util.badges.earns_badge(players, placement),
                                 _deck_options(store), trainer_options))
    return patched, next_index + 1


@dash_auth.protected_callback(
    Output(standings_container, 'children', allow_duplicate=True),
    Output(next_index_store, 'data', allow_duplicate=True),
    Input(players_input, 'value'),
    State(next_index_store, 'data'),
    State(deck_store, 'data'),
    State({'type': f'{PREFIX}-placement', 'index': ALL}, 'id'),
    State({'type': f'{PREFIX}-trainer-dd', 'index': ALL}, 'options'),
    State(edit_index, 'data'),
    groups=ROLES,
    prevent_initial_call=True,
)
def _ensure_rows(players, next_index, store, placement_ids, trainer_option_lists, editing):
    """Top up the standings to the suggested record count when players is set.

    Only appends (never removes) so entered rows are preserved; extras can be
    removed with the per-row delete button. Each new row's Badge toggle is
    pre-checked from its placement + the field size. Disabled while editing an
    existing event, whose standings are loaded verbatim.
    """
    if editing is not None:
        raise dash.exceptions.PreventUpdate
    target = util.badges.suggested_record_count(players)
    current = len(placement_ids)
    if not target or target <= current:
        raise dash.exceptions.PreventUpdate
    trainer_options = trainer_option_lists[0] if trainer_option_lists else []
    deck_opts = _deck_options(store)
    patched = Patch()
    idx = next_index
    for placement in range(current + 1, target + 1):
        patched.append(_standing_row(idx, placement,
                                     util.badges.earns_badge(players, placement),
                                     deck_opts, trainer_options))
        idx += 1
    return patched, idx


@dash_auth.protected_callback(
    Output(standings_container, 'children', allow_duplicate=True),
    Input({'type': f'{PREFIX}-delete', 'index': ALL}, 'n_clicks'),
    State({'type': f'{PREFIX}-placement', 'index': ALL}, 'id'),
    groups=ROLES,
    prevent_initial_call=True,
)
def _delete_row(clicks, placement_ids):
    """Remove the row whose delete button was clicked."""
    triggered = dash.callback_context.triggered
    if not triggered or not triggered[0].get('value'):
        # Fired from rows being added (new buttons), not an actual click.
        raise dash.exceptions.PreventUpdate
    deleted = dash.callback_context.triggered_id['index']
    positions = [i for i, id_ in enumerate(placement_ids) if id_['index'] == deleted]
    if not positions:
        raise dash.exceptions.PreventUpdate
    patched = Patch()
    del patched[positions[0]]
    return patched


@dash_auth.protected_callback(
    Output(CRI.ids.dropdown(store_aio), 'value', allow_duplicate=True),
    Output(date_input, 'date'),
    Output(players_input, 'value'),
    Output(tier_input, 'value'),
    Output(CRI.ids.dropdown(format_aio), 'value', allow_duplicate=True),
    Output(standings_container, 'children', allow_duplicate=True),
    Output(next_index_store, 'data', allow_duplicate=True),
    Output(edit_index, 'data'),
    Input(event_select, 'value'),
    State(deck_store, 'data'),
    groups=ROLES,
    prevent_initial_call=True,
)
def _load_event(line, deck_store_data):
    """Load an existing event into the form for editing, or reset when cleared."""
    trainer_options = sorted({
        b.get('trainer') for b in util.seasons.read_badges() if b.get('trainer')
    })
    deck_opts = _deck_options(deck_store_data or {})

    if line is None:
        # Cleared -> reset to a blank new-event form.
        return (None, datetime.date.today().isoformat(), None, 'Locals', 'Standard',
                [_standing_row(0, 1, True, deck_opts, trainer_options)], 1, None)

    event = next((e for e in util.seasons.read_events(_events_season())
                  if e.get('_line') == line), None)
    if event is None:
        raise dash.exceptions.PreventUpdate

    standings = event.get('standings') or []
    rows = [
        _standing_row(i, s.get('placement', i + 1), bool(s.get('earned_badge')),
                      deck_opts, trainer_options, standing=s)
        for i, s in enumerate(standings)
    ] or [_standing_row(0, 1, False, deck_opts, trainer_options)]

    date = event.get('date')
    date_value = date.isoformat() if hasattr(date, 'isoformat') else date
    return (
        event.get('store'),
        date_value,
        event.get('players'),
        event.get('tier', 'Locals'),
        event.get('format', 'Standard'),
        rows,
        len(rows),
        line,
    )


@dash_auth.protected_callback(
    Output(save, 'children'),
    Input(edit_index, 'data'),
    groups=ROLES,
)
def _save_label(editing):
    label = 'Update Event' if editing is not None else 'Save Event'
    return [html.I(className='fas fa-save me-1'), label]


@dash_auth.protected_callback(
    Output(badge_hint, 'children'),
    Input(players_input, 'value'),
    groups=ROLES,
)
def _badge_hint(players):
    """Show which placements earn a badge, and roughly how many to record."""
    cutoff = util.badges.badge_cutoff(players)
    who = '1st place earns a badge' if cutoff == 1 else f'Top {cutoff} earn a badge'
    if cutoff >= util.badges.BADGE_CUTOFF_CAP:
        who += ' (plus ties with 8th / the full cut — toggle manually)'
    count = util.badges.suggested_record_count(players)
    if not count:
        return f'{who}.'
    threshold = util.badges.suggested_record_threshold(players)
    base = f'anyone at {threshold} or better (one loss)' if threshold else 'the notable finishers'
    msg = f'{who}. Record ~{count} — {base}'
    # A single-elim cut can pull in two-loss players below the one-loss line, so
    # flag it only when the cut would go deeper than the Swiss-only suggestion.
    cut = util.badges.top_cut_size(players)
    if cut > count:
        msg += f'; if a Top {cut} cut was run, record the whole cut (incl. two-loss players)'
    return f'{msg}.'


@dash_auth.protected_callback(
    Output('_pages_location', 'pathname', allow_duplicate=True),
    Output(status, 'children'),
    Input(save, 'n_clicks'),
    State(CRI.ids.dropdown(store_aio), 'value'),
    State(date_input, 'date'),
    State(players_input, 'value'),
    State(tier_input, 'value'),
    State(CRI.ids.dropdown(format_aio), 'value'),
    State({'type': f'{PREFIX}-placement', 'index': ALL}, 'value'),
    State({'type': f'{PREFIX}-trainer-dd', 'index': ALL}, 'value'),
    State({'type': f'{PREFIX}-deck', 'index': ALL}, 'value'),
    State({'type': f'{PREFIX}-earned', 'index': ALL}, 'value'),
    State({'type': f'{PREFIX}-pronouns', 'index': ALL}, 'value'),
    State({'type': f'{PREFIX}-color', 'index': ALL}, 'value'),
    State({'type': f'{PREFIX}-background', 'index': ALL}, 'value'),
    State({'type': f'{PREFIX}-discord', 'index': ALL}, 'value'),
    State(deck_store, 'data'),
    State(edit_index, 'data'),
    groups=ROLES,
    prevent_initial_call=True,
)
def _save_event(n_clicks, store_name, date, players, tier, fmt,
                placements, trainers, deck_ids, earned_flags,
                pronouns, colors, backgrounds, discord_ids, deck_store_data, edit_line):
    if not n_clicks:
        raise dash.exceptions.PreventUpdate

    season = _events_season()
    if season is None:
        return dash.no_update, dbc.Alert('No events-mode season configured.', color='danger')
    if not store_name or not date:
        return dash.no_update, dbc.Alert('Store and date are required.', color='danger')

    deck_store_data = deck_store_data or {}
    standings = []
    pending_discord = []
    for i, trainer in enumerate(trainers):
        trainer = (trainer or '').strip()
        if not trainer:
            continue
        earned = bool(earned_flags[i])
        deck_id = deck_ids[i]
        standing = {
            'placement': _to_int(placements[i], i + 1),
            'trainer': trainer,
            'deck': deck_store_data.get(deck_id) if deck_id else None,
            'earned_badge': earned,
        }
        if earned:
            standing['pronouns'] = pronouns[i] or 'their'
            standing['color'] = colors[i] or '#ffffff'
            standing['background'] = backgrounds[i]
            discord_id = (discord_ids[i] or '').strip()
            if discord_id:
                pending_discord.append((trainer, discord_id))
        standings.append(standing)

    if not standings:
        return dash.no_update, dbc.Alert('Add at least one player.', color='danger')

    event = {
        'id': _event_id(store_name, date),
        'store': store_name,
        'date': date,
        'players': _to_int(players, None),
        'tier': tier,
        'format': fmt,
        'author': util.auth.current_username(),
        'standings': standings,
    }

    # Persist Discord IDs first so the badge pings can mention new trainers.
    for trainer, discord_id in pending_discord:
        util.discord.save_discord_id(trainer, discord_id)

    filename = util.seasons.data_file_for(season)

    if edit_line is not None:
        # Editing: overwrite the event in place, keeping its original id/author,
        # and don't re-post badges (avoids duplicate Discord pings).
        existing = next((e for e in util.seasons.read_events(season)
                         if e.get('_line') == edit_line), None)
        if existing:
            event['id'] = existing.get('id', event['id'])
            event['author'] = existing.get('author') or event['author']
        util.data.update_data_in_file(filename=filename, line_index=edit_line, contents=event)
        return '/', dash.no_update

    util.data.append_data_to_file(filename=filename, contents=event)

    for standing in standings:
        if standing.get('earned_badge'):
            util.discord.post_badge({
                'store': store_name,
                'date': date,
                'tier': tier,
                'format': fmt,
                'trainer': standing['trainer'],
                'pronouns': standing.get('pronouns', 'their'),
                'deck': standing.get('deck'),
                'color': standing.get('color'),
                'background': standing.get('background'),
            })

    return '/', dash.no_update


def _to_int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _event_id(store, date):
    slug = ''.join(c.lower() if c.isalnum() else '-' for c in (store or 'event')).strip('-')
    return f'evt_{date}_{slug}'


# Per-row trainer select-or-add (reuses the CustomRadioInput clientside helpers).
clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='customRadioEnableAdd'),
    Output({'type': f'{PREFIX}-trainer-add', 'index': MATCH}, 'disabled'),
    Input({'type': f'{PREFIX}-trainer-in', 'index': MATCH}, 'value'),
    Input({'type': f'{PREFIX}-trainer-dd', 'index': MATCH}, 'options'),
)

clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='addToOptionsAndSelect'),
    Output({'type': f'{PREFIX}-trainer-dd', 'index': MATCH}, 'options'),
    Output({'type': f'{PREFIX}-trainer-dd', 'index': MATCH}, 'value'),
    Input({'type': f'{PREFIX}-trainer-add', 'index': MATCH}, 'n_clicks'),
    State({'type': f'{PREFIX}-trainer-in', 'index': MATCH}, 'value'),
    State({'type': f'{PREFIX}-trainer-dd', 'index': MATCH}, 'options'),
)

clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='toggleBadgeFields'),
    Output({'type': f'{PREFIX}-badge-fields', 'index': MATCH}, 'style'),
    Input({'type': f'{PREFIX}-earned', 'index': MATCH}, 'value'),
)

clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='disableDeckAdd'),
    Output(deck_add, 'disabled'),
    Input(deck_name, 'value'),
    Input(deck_icons, 'value'),
    Input(deck_store, 'data'),
)
