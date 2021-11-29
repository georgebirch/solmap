from utils.paths import *
from utils.dataset import *
from utils.plot_utils import *

from pkg_resources import get_platform

import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output

gps_coords = 46.58724, 7.99614
radius = 1

def main():
    global mdf_list, tdf_list, amdf_list 
    mdf_list, tdf_list, amdf_list = get_df_lists(gps_coords, radius)

    app = dash.Dash(__name__)
    server = app.server

    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    app.layout = html.Div(children=[
        html.Div(className='row',  # Define the row element
            children=[
                html.Div(className='twelve columns div-for-chart center',
                children = [
                    dcc.Graph(
                        id='plot1',
                    )
                ]),  # Define the left element
            ]),
        html.Div(className='row',
            children=[
                # html.Div(className='10 columns center'),
                html.Div(
                    className='div-for-slider center',
                    style = {'color': 'blue', 'fontSize': 14, 'fontFamily':'Arial'},
                    children = [
                        dcc.Slider(
                            id='month_slider',
                            min=1,
                            max=12,
                            # marks = { i+1:{'label':month_names[i], 'style':{'color':'red', 'font':{'family':'Verdana','size':22} } } for i in range(12) },
                            marks = { i+1:{'label':month_names[i] } for i in range(12)},

                            value = 6,
                            # tooltip=dict(always_visible = True, placement = 'bottom')
                        ),
                    ]
                )
            ]
        ),
        html.Div(className='row',  # Define the row element
            children=[
                html.Div(className = 'logo',
                    children=[
                        html.Img(src=app.get_asset_url('sunmap.png'), width=500),  # Define the left element
                    ]
                )
            ]),       
    ])

    @app.callback(
        Output('plot1', 'figure'),
        Input('month_slider', 'value'))    
    def update_figure(month):
        fig = make_solmap(month)
        return fig
        
    app.run_server(port = 5000)

def get_df_lists(gps_coords, radius):
    peaks_df, observer_height = get_mtn_geometry(gps_coords, radius)
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
    return mdf_list, tdf_list, amdf_list 

def make_solmap(month): 
    mdf = mdf_list[month-1]
    tdf = tdf_list[month-1]

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
    
    ticks, annotations = get_annotations(tdf)

    pio.templates.default = "simple_white"

    fig = go.Figure()

    fig.add_traces([
        peak_lines,
        diff_lines,
        sun_line,
    ])
    fig.add_traces(
        ticks
    )
    max_y = max( [ max( [mdf_.elevation.max(), mdf_.peak_angle.max()] ) for mdf_ in mdf_list ] )

    fig.update_layout( 
        annotations = annotations,
        xaxis = dict(
            tickmode = 'array',
            tickvals = [0, 22.5, 45.0, 67.5, 90.0, 112.5, 135.0, 157.5, 180.0, 202.5, 225.0, 247.5, 270.0, 292.5, 315, 337.5, 360] ,
            ticktext = ['N', 'ENE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NWN', 'N'],
            range = [45, 315],
        ),
        yaxis = dict(
            range = [0, max_y],
            anchor = 'free',
            position = 0.5,
            visible = False,
            scaleanchor = 'x',
            scaleratio = 0.6
        ),
        showlegend=False,
        autosize=True,
        height=600,
        # margin={'t': 50},
        # margin=dict(
        #     l=50,
        #     r=50,
        #     b=100,
        #     t=100,
        #     pad=4
        # ),
        paper_bgcolor="white",
        font = dict( family = 'verdana', size = 12 )

    )
    return fig

def get_annotations(tdf):
    annotations = []
    ticks = []
    gdf = tdf.loc[tdf.elevation > 0].groupby('time')
    for hour, df in gdf:
        df = df.sort_values('date').reset_index()
        # print(df.head)
        x = float( df['azimuth' ] )
        y = float( df['elevation' ] )
        text = hour
        grad = float( df.grad )
        ticks.append(dict(
            type = 'scatter',
            x=[ x, x + 2 * grad],
            y=[ y, y - 2] ,
            line = dict( color="white", width=1), 
            # fill = 'toself',
            marker = None,
            mode = 'lines',
        ))
        
        # markers.append(make_marker_dict(x,y,hour))
        annotations.append( dict(
            text = str(text) + ':00',
            x = x,
            y = y,
            xanchor = 'center',
            yanchor = 'middle',
            xshift = 15 * grad,
            yshift = -20,
            showarrow = False,
            font = dict(color = 'white'),
            opacity = 1
        )    )
    return ticks, annotations

if __name__ == '__main__':
    main()