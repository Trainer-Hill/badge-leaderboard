import dash_bootstrap_components as dbc
import uuid

from dash import html, dcc, clientside_callback, ClientsideFunction, Output, Input, State, MATCH


class CustomRadioInputAIO(html.Div):

    class ids:
        dropdown = lambda aio_id: {
            'component': 'CustomRadioInputAIO',
            'subcomponent': 'dropdown',
            'aio_id': aio_id
        }
        input = lambda aio_id: {
            'component': 'CustomRadioInputAIO',
            'subcomponent': 'input',
            'aio_id': aio_id
        }
        add = lambda aio_id: {
            'component': 'CustomRadioInputAIO',
            'subcomponent': 'add',
            'aio_id': aio_id
        }

    ids = ids

    def __init__(
        self,
        options=None,
        aio_id=None
    ):
        if aio_id is None:
            aio_id = str(uuid.uuid4())

        if options is None:
            options = []

        component = [
            dcc.Dropdown(options=options, id=self.ids.dropdown(aio_id)),
            dbc.InputGroup([
                dbc.Input(id=self.ids.input(aio_id), placeholder='Enter custom name', value=''),
                dbc.Button(html.I(className='fas fa-plus'), id=self.ids.add(aio_id), disabled=True)
            ])
        ]
        super().__init__(component)

    clientside_callback(
        ClientsideFunction(namespace='clientside', function_name='customRadioEnableAdd'),
        Output(ids.add(MATCH), 'disabled'),
        Input(ids.input(MATCH), 'value'),
        Input(ids.dropdown(MATCH), 'options'),
    )
    clientside_callback(
        ClientsideFunction(namespace='clientside', function_name='addToOptionsAndSelect'),
        Output(ids.dropdown(MATCH), 'options'),
        Output(ids.dropdown(MATCH), 'value'),
        Input(ids.add(MATCH), 'n_clicks'),
        State(ids.input(MATCH), 'value'),
        State(ids.dropdown(MATCH), 'options'),
    )
