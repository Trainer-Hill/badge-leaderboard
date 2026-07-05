import dash
import dash_bootstrap_components as dbc
from dash import html, dcc

import util.seasons


dash.register_page(__name__, path='/rules')


def _load_rules(season_year: int) -> str:
    """Return the markdown rules text for a season, or a fallback message."""
    path = util.seasons.rules_path_for(season_year)
    if not path:
        return f'*Rules for the {season_year} season are not available.*'
    with open(path, 'r') as f:
        return f.read()


def layout(season=None, **kwargs):
    """Render the rules page for the selected season."""
    season_year = util.seasons.resolve_season(season)
    return dbc.Container([
        html.H2(f'{season_year} Season Rules', className='mb-3'),
        dcc.Markdown(
            _load_rules(season_year),
            id='rules-markdown'
        )
    ], fluid=True)
