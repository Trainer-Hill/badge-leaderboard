import dash
from dash import html
import json

import components.badge
import util.data

dash.register_page(
    __name__,
    path='/'
)

def create_component(data_entry):
    '''Convert a data entry into a Dash component'''
    return html.Div([
        html.H3(data_entry.get('title', 'Untitled')),
        html.P(data_entry.get('clicks', 'No clicks')),
    ])


def layout():
    '''Main layout function that generates components from data'''
    # maybe we should be pulling this information from a different year - one file per year?
    data = util.data.read_data('badge_dump.jsonl')
    data.reverse()
    return html.Div([
        html.H1('Home Page'),
        html.Div([components.badge.create_badge_component(badge, i) for i, badge in enumerate(data)])
    ])


# layout ideas
# breakdown of year
# breakdown of quarter
# highlight which decks/players have the most badges
# maybe some other charts of when people earned their badges would be cool
