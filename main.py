from utils.paths import *
from utils.dataset import *
from utils.plot_utils import *

from pkg_resources import get_platform

import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output

gps_coords = 45.98984, 7.69898
peaks_df, observer_height = get_mtn_geometry(gps_coords)

# global mdf_list, tdf_list, amdf_list 
mdf_list, tdf_list, amdf_list  = [], [], []
for month in np.arange(1,13):
    # td = datetime.timedelta(days = interval)
    # final_date = start_date + n_intervals * td
    year = 2021
    day = 1
    date = {'year':year,'month':month,'day':day}
    date = datetime.date(year = date['year'], month = date['month'], day = date['day'])
    mdf_,tdf_,amdf_  = get_data(gps_coords, observer_height, peaks_df, date)
    mdf_list.append(mdf_)
    tdf_list.append(tdf_)
    amdf_list.append(amdf_)

app = dash.Dash(__name__)
server = app.server

month = 1

month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

app.layout = html.Div([
        dcc.Graph(
            id='plot1', 
        ),
        dcc.Slider(
            id='month_slider',
            min=0,
            max=11,
            marks = { i:{'label':month_names[i]} for i in range(12) },
            value = 6,
            tooltip=dict(always_visible = True, placement = 'bottom')
        ),
        # dcc.Dropdown(id='date-select', 
        # options=[ {'label': month_names[i], 'value': i} for i in np.arange(12)],
        #                     # style={'width': '140px', 'align-items': 'center'}
        #                     # style = {'width':'100%', 'display': 'flex', 'align-items': 'center', 'justify-content': 'center'}                        
        # ),
        ])


@app.callback(
    Output('plot1', 'figure'),
    Input('month_slider', 'value'))    
def make_solmap(month):
    mdf = mdf_list[month]
    tdf = tdf_list[month]

    peak_lines = dict(
                    type = 'scatter',
                    x = mdf.bearing,
                    y = mdf.peak_angle,
                    line = dict(color = 'gold'),
                    mode = 'none',
                    stackgroup = 'sun',
                    fillcolor = 'black'
                    # fill = 'tozeroy'
                    )

    diff_lines = dict(
                    type = 'scatter',
                    x = mdf.bearing,
                    y = mdf.el_diff,
                    line = dict(color = 'gold'),
                    mode = 'none',
                    stackgroup = 'sun',
                    fillcolor = 'gold'
                    # fill = 'tozeroy'
                    )

    sun_line = dict(
                    type = 'scatter',
                    x = mdf.loc[ mdf.daylight == 'day' ].bearing,
                    y = mdf.loc[ mdf.daylight == 'day' ].elevation,
                    line = dict(
                        color = 'white',
                        width = 0.5),
                )

    pio.templates.default = "simple_white"

    fig = go.Figure()

    fig.add_traces([
        peak_lines,
        diff_lines,
        sun_line
    ])

    annotations = []
    gdf = tdf.loc[tdf.elevation > 0].groupby('time')
    for hour, df in gdf:
        df = df.sort_values('date').reset_index()
        # print(df.head)
        x = float( df['azimuth' ] )
        y = float( df['elevation' ] )
        text = hour
        grad = float( df.grad )
        fig.add_trace(
            go.Scatter(
                x=[ x, x + 2 * grad],
                y=[ y, y - 2] ,
                line = dict( color="white", width=1), 
                # fill = 'toself',
                marker = None,
                mode = 'lines',
                showlegend = False
            )
        )
        # markers.append(make_marker_dict(x,y,hour))
        annotations.append( dict(
            text = str(text) + ':00',
            x = x,
            y = y,
            xanchor = 'center',
            yanchor = 'middle',
            xshift = 10 * grad,
            yshift = -20,
            showarrow = False,
            font = dict(color = 'white'),
            opacity = 1
        )    )

    fig.update_layout( 
        annotations = annotations,
        xaxis = dict(
            tickmode = 'array',
            tickvals = [0, 22.5, 45.0, 67.5, 90.0, 112.5, 135.0, 157.5, 180.0, 202.5, 225.0, 247.5, 270.0, 292.5, 315, 337.5] ,
            ticktext = ['N', 'ENE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NWN'],
            range = [90, 270],
        ),
        yaxis = dict(
            range = [0, 60],
            anchor = 'free',
            position = 0.5,
            visible = False
        ),
        showlegend=False,
        autosize=False,
        width=1500,
        height=800,
        # margin=dict(
        #     l=50,
        #     r=50,
        #     b=100,
        #     t=100,
        #     pad=4
        # ),
    paper_bgcolor="white",
    )
    return fig

if __name__ == '__main__':
    app.run_server(port = 5000)
