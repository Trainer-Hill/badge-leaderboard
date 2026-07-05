import datetime
import itertools
from collections import defaultdict
from datetime import date

import dash
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash import dcc, html
from plotly.express.colors import qualitative
import plotly.graph_objects as go

import util.seasons
from util.leaderboard import badge_points, normalize_value


dash.register_page(__name__, path='/race', name='Race to #1')


_LEADERBOARD_LIMIT = 20
_SEASON_START_MONTH = 7


def _season_end(start: date) -> date:
    return date(start.year + 1, _SEASON_START_MONTH, 1)


def _season_window_label(start: date) -> str:
    end = _season_end(start) - datetime.timedelta(days=1)
    return f"Season window: {start.strftime('%b %d, %Y')} - {end.strftime('%b %d, %Y')}"


def _format_date_label(value: date) -> str:
    return value.strftime('%b %d, %Y')


def _empty_figure(title: str, message: str) -> go.Figure:
    fig = go.Figure()
    fig.update_layout(
        title=title,
        xaxis={'visible': False},
        yaxis={'visible': False},
        annotations=[
            {
                'text': message,
                'xref': 'paper',
                'yref': 'paper',
                'x': 0.5,
                'y': 0.5,
                'showarrow': False,
                'align': 'center',
            }
        ],
        margin={'l': 60, 'r': 60, 't': 80, 'b': 80},
    )
    return fig


def _badge_events(badges):
    events = []
    for order, badge in enumerate(badges):
        trainer = normalize_value(badge.get('trainer'))
        badge_date = badge.get('date')
        if not trainer or not badge_date:
            continue
        events.append({
            'date': badge_date,
            'order': order,
            'trainer': trainer,
            'points': badge_points(badge),
        })
    events.sort(key=lambda entry: (entry['date'], entry['order']))
    return events


def _top_n(counts, points, limit=_LEADERBOARD_LIMIT):
    leaderboard = [
        (trainer, count, points[trainer])
        for trainer, count in counts.items()
    ]
    leaderboard.sort(key=lambda item: (-item[1], -item[2], item[0].lower()))
    return leaderboard[:limit]


def _build_timeline(badges, limit=_LEADERBOARD_LIMIT):
    events = _badge_events(badges)
    if not events:
        return []

    counts = defaultdict(int)
    points = defaultdict(int)
    timeline = []

    for current_date, group in itertools.groupby(events, key=lambda event: event['date']):
        for event in group:
            counts[event['trainer']] += 1
            points[event['trainer']] += event['points']
        timeline.append((current_date, _top_n(counts, points, limit=limit)))

    return timeline


def _color_map(timeline):
    palette = (
        qualitative.Plotly
        + qualitative.D3
        + qualitative.G10
        + qualitative.Safe
        + qualitative.Dark24
    )
    seen = set()
    order = []
    for _, leaderboard in timeline:
        for name, _, _ in leaderboard:
            if name not in seen:
                seen.add(name)
                order.append(name)
    colors = {}
    if palette:
        for index, name in enumerate(order):
            colors[name] = palette[index % len(palette)]
    return colors


def _figure_from_timeline(timeline, top_k=_LEADERBOARD_LIMIT):

    # Collect unique trainers that ever appear in Top-K (keeps trace count reasonable)
    def topk_for_board(board):
        return sorted(board, key=lambda r: (-r[1], -r[2], r[0]))[:top_k]
    ever_topk = []
    seen = set()
    for _, board in timeline:
        for name, _, _ in topk_for_board(board):
            if name not in seen:
                seen.add(name)
                ever_topk.append(name)

    # Stable color map
    colors = _color_map(timeline)
    def color_for(n): return colors.get(n, '#636EFA')

    # X range
    max_badges = max((b for _, board in timeline for _, b, _ in board), default=0)
    x_max = max(1, max_badges + 1)

    # One trace per (ever-topk) trainer so Plotly can interpolate positions
    # Start everyone hidden
    data = []
    for name in ever_topk:
        data.append(go.Bar(
            x=[0],
            y=[top_k],  # arbitrary slot
            orientation='h',
            name=name,
            marker_color=color_for(name),
            text=[""],
            textposition="outside",
            hovertemplate='<b>%{customdata[0]}</b><br>Badges: %{x}<br>Points: %{customdata[1]}<br>Rank: %{customdata[2]}<extra></extra>',
            customdata=[["", 0, ""]],
            visible=False,
        ))

    # Build frames and inject live date into each frame's layout.title
    frames = []
    for current_date, board in timeline:
        # Compute dynamic Top-K for this frame
        sorted_board = sorted(board, key=lambda r: (-r[1], -r[2], r[0]))[:top_k]
        rank_by_name = {name: i+1 for i, (name, _, _) in enumerate(sorted_board)}
        badges_by_name = {name: b for name, b, _ in sorted_board}
        points_by_name = {name: p for name, _, p in sorted_board}

        # Prepare y-axis tick labels as the current leaderboard
        tickvals = list(range(1, top_k+1))

        # Frame traces in the SAME ORDER as in `data`
        frame_traces = []
        for name in ever_topk:
            if name in rank_by_name:
                r = rank_by_name[name]
                b = badges_by_name[name]
                p = points_by_name[name]
                frame_traces.append(go.Bar(
                    x=[b],
                    y=[r],                   # numeric rank position -> smooth movement
                    text=[f"{name} • {b} badge{'s' if b!=1 else ''} • {p} pt{'s' if p!=1 else ''}"],
                    customdata=[[name, p, r]],
                    visible=True,
                    marker_color=color_for(name),
                    orientation='h',
                    textposition='outside',
                ))
            else:
                frame_traces.append(go.Bar(x=[None], y=[None], visible=False))

        label = _format_date_label(current_date)
        frames.append(go.Frame(
            data=frame_traces,
            name=label,
            layout={
                'yaxis': {'tickvals': tickvals},
                'title': {'text': f"Race to #1 — {label}"},
            },
        ))

    # Figure with initial (first frame) state applied
    fig = go.Figure(data=data, frames=frames)
    if frames:
        # Apply first frame's data so the first render shows bars and title with date
        for i, tr in enumerate(frames[0].data):
            fig.data[i].update(tr)

    # Smooth, readable pacing
    FRAME_MS = 900
    TRANSITION_MS = 500

    slider_steps = [{
        'args': [[fr.name], {
            'frame': {'duration': FRAME_MS, 'redraw': True},
            'mode': 'immediate',
            'transition': {'duration': TRANSITION_MS, 'easing': 'cubic-in-out'},
        }],
        'label': fr.name,
        'method': 'animate',
    } for fr in frames]

    # Initial title uses the first frame's date, so the date is visible even before Play
    initial_label = frames[0].name if frames else ""

    fig.update_layout(
        title=f"Race to #1 — {initial_label}",
        xaxis={'title': 'Badges Earned', 'range': [0, x_max], 'fixedrange': True},
        yaxis={
            'title': 'Rank',
            'range': [top_k + 0.5, 0.5],
            'autorange': False,
            'tickmode': 'array',
            'tickvals': list(range(1, top_k+1)),
            'ticktext': [],  # filled by frames
        },
        margin={'l': 160, 'r': 60, 't': 80, 'b': 140},
        showlegend=False,
        hovermode='closest',
        height=750,
        updatemenus=[{
            'type': 'buttons',
            'showactive': False,
            'direction': 'left',
            'x': 0,
            'y': -0.05,
            'xanchor': 'left',
            'yanchor': 'top',
            'pad': {'r': 10, 't': 0, 'b': 0},
            'buttons': [
                {
                    'label': 'Play',
                    'method': 'animate',
                    'args': [None, {
                        'frame': {'duration': FRAME_MS, 'redraw': True},
                        'fromcurrent': True,
                        'mode': 'immediate',
                        'transition': {'duration': TRANSITION_MS, 'easing': 'cubic-in-out'},
                    }],
                },
                {
                    'label': 'Pause',
                    'method': 'animate',
                    'args': [None, {  # important: None (not [[None]])
                        'frame': {'duration': 0, 'redraw': False},
                        'mode': 'immediate',
                        'transition': {'duration': 0},
                    }],
                },
            ],
        }],
        sliders=[{
            'active': 0,
            'y': -0.06,
            'x': 0.1,
            'len': 0.8,
            'xanchor': 'left',
            'pad': {'t': 40, 'b': 0},
            'transition': {'duration': TRANSITION_MS, 'easing': 'cubic-in-out'},
            'steps': slider_steps,
        }],
    )

    # Avoid clipping labels
    fig.update_traces(cliponaxis=False)

    return fig


def layout(season=None, **kwargs):
    # A race is inherently per-season; the "Overall" selection falls back to the
    # current season (resolve_season maps Overall/None -> current).
    season_year = util.seasons.resolve_season(season)
    badges = util.seasons.read_badges(season_year)
    if not badges:
        return dbc.Container([
            html.H2('Race to #1'),
            html.P(
                'Track how trainers climb the leaderboard across each season once badge data is available.'
            ),
            dbc.Alert(
                f'Not enough badge data yet to build the race chart for the {season_year} season.',
                color='warning',
            ),
        ], fluid=True)

    timeline = _build_timeline(badges)
    figure = (
        _figure_from_timeline(timeline)
        if timeline
        else _empty_figure(
            'Race to #1',
            'Not enough badge data yet to build the race chart for this season.',
        )
    )

    season_start, _ = util.seasons.season_bounds(season_year)

    return dbc.Container([
        html.H2(f'Race to #1 — {season_year} Season'),
        html.P(
            'Watch the animated bar chart to see how the top players battle for first place. '
            'Only the top ten players at each point in time are shown. Rankings are determined '
            'by total badges earned with tier points used as the tie breaker.'
        ),
        html.Div(
            _season_window_label(season_start),
            className='text-muted mb-3',
        ),
        dcc.Graph(
            id='race-to-one-graph',
            figure=figure,
            config={'displayModeBar': False},
            className='mb-4',
        ),
        html.P(
            'Use the Play button to animate the race or drag the slider to inspect any date in the season.'
        ),
    ], fluid=True)
