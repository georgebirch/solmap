from pkg_resources import get_platform
from utils import *
from plot_utils import *

import plotly as py
import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output

app = dash.Dash(__name__)
server = app.server

month = 1

months = np.arange(1,12)

app.layout = html.Div([
    html.Div( [dcc.Dropdown(id='date-select', options=[ {'label': i, 'value': i} for i in months],
                             style={'width': '140px'})] ), \
    dcc.Graph(id='plot1' )
    ])

@app.callback(
    Output('plot1', 'figure'),
    Input('date-select', 'value'))    
def update_graph(month):
    return get_py_fig(month)

# if __name__ == '__main__':
#     app.run_server(debug=False)
app.server.run(debug=True)
