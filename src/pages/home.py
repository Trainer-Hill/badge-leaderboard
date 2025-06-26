import dash
import dash_bootstrap_components as dbc
import datetime
from collections import Counter
from dash import html

import components.badge
import util.data

dash.register_page(
    __name__,
    path='/'
)

def _season_start(date: datetime.date) -> datetime.date:
    """Return the start of the season for a given date."""
    if date.month >= 7:
        return datetime.date(date.year, 7, 1)
    return datetime.date(date.year - 1, 7, 1)


def _quarter_start(date: datetime.date) -> datetime.date:
    """Return the beginning of the quarter for a given date."""
    m = date.month
    y = date.year
    if 7 <= m <= 9:
        return datetime.date(y, 7, 1)
    if 10 <= m <= 12:
        return datetime.date(y, 10, 1)
    if 1 <= m <= 3:
        return datetime.date(y, 1, 1)
    return datetime.date(y, 4, 1)


def _parse_badges():
    badges = util.data.read_data('badges.jsonl')
    for b in badges:
        try:
            b['date'] = datetime.date.fromisoformat(b.get('date'))
        except Exception:
            b['date'] = None
    return badges


def _leaderboard(badges, key):
    counter = Counter()
    for b in badges:
        value = b.get(key)
        if not value:
            continue
        if isinstance(value, dict):
            value = value.get('name') or value.get('id')
        counter[value] += 1
    return counter


def _leaderboard_table(title, data_counter):
    rows = [html.Tr([html.Td(name), html.Td(count)]) for name, count in data_counter]
    table = dbc.Table([
        html.Thead(html.Tr([html.Th(title, colSpan=2)])),
        html.Tbody(rows)
    ], bordered=True, size='sm', class_name='mb-2')
    return table


def layout():
    badges = _parse_badges()

    today = datetime.date.today()
    season_start = _season_start(today)
    quarter_start = _quarter_start(today)

    season_badges = [b for b in badges if b.get('date') and b['date'] >= season_start]
    quarter_badges = [b for b in badges if b.get('date') and b['date'] >= quarter_start]

    trainer_season = _leaderboard(season_badges, 'trainer')
    trainer_quarter = _leaderboard(quarter_badges, 'trainer')
    deck_season = _leaderboard(season_badges, 'deck')
    deck_quarter = _leaderboard(quarter_badges, 'deck')

    # TODO how do we factor in tie breakers?
    trainer_season = trainer_season.most_common(10)
    trainer_quarter = trainer_quarter.most_common(10)
    deck_season = deck_season.most_common(10)
    deck_quarter = deck_quarter.most_common(10)

    store_counts = _leaderboard(season_badges, 'store').most_common(5)

    recent_components = []
    for i, b in enumerate(badges[:10]):
        component = components.badge.create_badge_component(b, i)
        recent_components.append(component)

    return dbc.Container([
        html.H1('Badge Leaderboard', className='mb-4'),
        dbc.Row([
            dbc.Col([
                _leaderboard_table('Season Trainers', trainer_season),
                _leaderboard_table('Current Quarter Trainers', trainer_quarter),
            ], md=6),
            dbc.Col([
                _leaderboard_table('Season Decks', deck_season),
                _leaderboard_table('Current Quarter Decks', deck_quarter),
            ], md=6)
        ]),
        html.H2('Recent Badges'),
        dbc.Row([dbc.Col(rc, md=6) for rc in recent_components]),
        html.H2('Top Stores'),
        dbc.Table([
            html.Thead(html.Tr([html.Th('Store'), html.Th('Badges')])),
            html.Tbody([html.Tr([html.Td(name), html.Td(count)]) for name, count in store_counts])
        ], bordered=True, size='sm', class_name='mb-4')
    ], fluid=True)
