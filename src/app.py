import base64
import dash
import dash_auth
import dash_bootstrap_components as dbc
import dotenv
import hashlib
import hmac
import os

dotenv.load_dotenv(override=True)

if os.environ.get('FLASK_ENV', 'production'):
    print('Monkey patching for Gevent')
    from gevent import monkey
    monkey.patch_all()

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

# Parameters for PBKDF2
HASH_NAME = "sha256"
ITERATIONS = 100_000
SALT_SIZE = 16  # bytes
KEY_LENGTH = 32  # bytes


def hash_password(password: str) -> str:
    salt = os.urandom(SALT_SIZE)
    key = hashlib.pbkdf2_hmac(HASH_NAME, password.encode(), salt, ITERATIONS, dklen=KEY_LENGTH)
    return base64.b64encode(salt + key).decode()  # Store both salt and key together


def verify_password(password: str, stored_hash: str) -> bool:
    decoded = base64.b64decode(stored_hash.encode())
    salt = decoded[:SALT_SIZE]
    original_key = decoded[SALT_SIZE:]
    new_key = hashlib.pbkdf2_hmac(HASH_NAME, password.encode(), salt, ITERATIONS, dklen=KEY_LENGTH)
    return hmac.compare_digest(new_key, original_key)


def check_user(username, password):
    expected_user = os.getenv("TH_BL_USER")
    if expected_user is None or username != expected_user:
        return False

    expected_hash = os.getenv("TH_BL_PASSWORD_HASH")
    if expected_hash:
        return verify_password(password, expected_hash)
    return False


def get_user_groups(user):
    if user == os.getenv('TH_BL_USER'):
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
                )
            ]), color='dark', dark=True),
            dbc.Container([
                dash.page_container,
            ], class_name='page-container my-1')
        ],
        className='dbc app'
    )


app.layout = serve_layout
server = app.server


@server.get('/health')
def check_health():
    return 'ok', 200


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8080)
