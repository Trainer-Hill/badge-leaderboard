import dash
import dash_auth
import dash_bootstrap_components as dbc

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
        'https://use.fontawesome.com/releases/v6.7.2/css/all.css',
    ],
    meta_tags=[
        {'name': 'viewport', 'content': 'width=device-width, initial-scale=1'}
    ],
    suppress_callback_exceptions=True,
    title=TITLE,
)


# TODO figure out the proper way to do this
def check_user(username, password):
    if username == "user1" and password == "password":
        return True
    if username == "user2" and password == "admin":
        return True
    return False


# TODO figure out the proper way to do this
def get_user_groups(user):
    if user == "user1":
        return ["group1", "group2"]
    elif user == "user2":
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
            ])),
            dbc.Container([
                dash.page_container,
            ], class_name='page-container my-1')
        ],
        className='dbc app'
    )


app.layout = serve_layout
server = app.server

if __name__ == '__main__':
    app.run(debug=True)
