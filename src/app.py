import dotenv
import os

dotenv.load_dotenv(override=True)
IS_PROD = os.environ.get('FLASK_ENV', 'production') == 'production'
if IS_PROD:
    print('Monkey patching for Gevent')
    from gevent import monkey
    monkey.patch_all()

import dash
import dash_auth
import dash_bootstrap_components as dbc
import json

import util.seasons
from util.passwords import hash_password, verify_password

# Grab logo
THEME = None or dbc.themes.BOOTSTRAP
TITLE = None or 'Badge Leaderboard'

dbc_css = 'https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates@V1.0.2/dbc.min.css'
app = dash.Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[
        dbc_css,
        THEME,
        'https://use.fontawesome.com/releases/v6.7.2/css/all.css'
    ],
    external_scripts=[
        {'src': 'https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js'}
    ],
    meta_tags=[
        {'name': 'viewport', 'content': 'width=device-width, initial-scale=1'}
    ],
    suppress_callback_exceptions=True,
    title=TITLE,
)

# Password hashing (hash_password / verify_password) lives in util.passwords so
# it can be run standalone to mint hashes; imported above.


def load_admins():
    """Return {username: password_hash} for every configured admin.

    Two sources, merged (we expect fewer than ~5 accounts, so this stays simple):
      * ``TH_BL_USERS`` -- a JSON object of ``{"username": "<hash>"}``.
      * ``TH_BL_USER`` + ``TH_BL_PASSWORD_HASH`` -- the legacy single-account
        pair, kept for backward compatibility.
    Generate hashes with ``hash_password()``.
    """
    admins = {}
    raw = os.getenv('TH_BL_USERS')
    if raw:
        try:
            parsed = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            print('TH_BL_USERS is not valid JSON; ignoring it')
            parsed = None
        if isinstance(parsed, dict):
            admins.update({str(u): str(h) for u, h in parsed.items()})

    legacy_user = os.getenv('TH_BL_USER')
    legacy_hash = os.getenv('TH_BL_PASSWORD_HASH')
    if legacy_user and legacy_hash:
        admins.setdefault(legacy_user, legacy_hash)

    return admins


def check_user(username, password):
    stored_hash = load_admins().get(username)
    if not stored_hash:
        return False
    return verify_password(password, stored_hash)


def get_user_groups(user):
    if user in load_admins():
        return ["admin"]
    return []


assets = [f'/assets/energy_types/{t.lower()}.svg' for t in [
    'Grass', 'Fire', 'Water', 'Lightning',
    'Psychic', 'Fighting', 'Dark', 'Metal',
    'Dragon', 'Fairy', 'Colorless']
]


dash_auth.BasicAuth(
    app=app,
    public_routes=[
        '/',  # Public root route
        '/badges',
        '/health',
        '/players',
        '/decks',
        '/leaderboard',
        '/locations',
        '/rules',
        '/login',  # Example public login page (if needed)
        '/_favicon.ico',  # Favicon (avoids auth for icon requests)
        '/_dash-layout',  # Required for initial page layout
        '/_dash-dependencies',  # Required for callback dependencies
        '/_dash-update-component',  # Required for callbacks
        '/_dash-component-suites/*',  # Wildcard for Dash component resources (JS/CSS)
        '/_config',  # Dash config endpoint (optional)
        '/_reload-hash',  # Hot-reload in debug mode (optional)
    ] + assets,
    auth_func=check_user,
    user_groups=get_user_groups,
    secret_key='TODO GENERATE A SECURE KEY HERE BOI',
)


def serve_layout():
    return dash.html.Div(
        [
            # TODO create navbar with logo
            # components.navbar.navbar(),
            dbc.Navbar(dbc.Container([
                dbc.NavbarBrand(
                    TITLE,
                    # html.Img(
                    #     height='40px',
                    #     id=image
                    # ),
                    href='/'
                ),
                dash.html.Div(
                    dash.dcc.Dropdown(
                        id='season-select',
                        options=util.seasons.nav_season_options(),
                        value=util.seasons.current_season(),
                        clearable=False,
                        searchable=False,
                        style={'minWidth': '160px'},
                    ),
                    className='ms-auto',
                ),
            ]), color='dark', dark=True),
            dash.dcc.Store(id='season-nav-noop'),
            dash.dcc.Store(id='season-link-noop'),
            dbc.Container([
                dash.page_container,
            ], class_name='my-1', id='page_container')
        ],
        className='dbc app'
    )


app.layout = serve_layout
server = app.server

dash.clientside_callback(
    dash.ClientsideFunction(namespace='clientside', function_name='updatePageFluidity'),
    dash.Output('page_container', 'fluid'),
    dash.Input('_pages_location', 'pathname'),
)

# Season selector: navigate to ?season=<year> on change (full reload so every
# page's layout(season=...) honors it), and sync the dropdown from the URL.
dash.clientside_callback(
    dash.ClientsideFunction(namespace='clientside', function_name='navigateSeason'),
    dash.Output('season-nav-noop', 'data'),
    dash.Input('season-select', 'value'),
    prevent_initial_call=True,
)

dash.clientside_callback(
    dash.ClientsideFunction(namespace='clientside', function_name='initSeasonSelect'),
    dash.Output('season-select', 'value'),
    dash.Input('_pages_location', 'pathname'),
)

# Install (once) a delegated click handler that carries the active season
# across internal navigation.
dash.clientside_callback(
    dash.ClientsideFunction(namespace='clientside', function_name='installSeasonLinkPersistence'),
    dash.Output('season-link-noop', 'data'),
    dash.Input('_pages_location', 'pathname'),
)


@server.get('/health')
def check_health():
    return 'ok', 200


def _exportable_files():
    """Map basename -> path for every data file we're willing to serve.

    Restricting to files declared in the season config (plus the default badge
    file) keeps this endpoint from being an arbitrary-file read.
    """
    import util.data
    files = {os.path.basename(util.data.FILENAME): util.data.FILENAME}
    for year in util.seasons.SEASONS:
        path = util.seasons.data_file_for(year)
        files[os.path.basename(path)] = path
    return files


@server.get('/api/export-badges')
def export_badges():
    """Download a season's raw JSONL.

    Selection (first match wins), all validated against an allowlist:
      * ``?file=events_2027.jsonl`` -- by filename.
      * ``?season=2027`` -- by season year (resolved to its data file).
      * neither -- the default badge file (badges.jsonl).
    """
    import util.data
    from flask import request, Response

    files = _exportable_files()
    requested = request.args.get('file')
    season = request.args.get('season')

    if requested:
        path = files.get(os.path.basename(requested))
        if path is None:
            return 'Unknown file', 404
    elif season:
        path = util.seasons.data_file_for(util.seasons.resolve_season(season))
    else:
        path = util.data.FILENAME

    try:
        with open(path, 'rb') as f:
            data = f.read()
    except OSError:
        return 'File not found', 404

    basename = os.path.basename(path)
    return Response(
        data,
        mimetype='application/x-ndjson',
        headers={'Content-Disposition': f'attachment; filename="{basename}"'},
    )


if __name__ == '__main__':
    app.run(debug=not IS_PROD, host='0.0.0.0', port=8080)
