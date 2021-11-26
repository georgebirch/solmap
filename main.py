from utils import *

from pkg_resources import get_platform

import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output

gps_coords = 45.98984, 7.69898
gps_lat, gps_lon = gps_coords

interval = 30
n_intervals = 1

metadata_links = {'2m' : '/Users/george-birchenough/Downloads/ch.swisstopo.swissalti3d-fGQ3d2A6.csv' , \
                '0.5m' : 'https://ogd.swisstopo.admin.ch/resources/ch.swisstopo.swissalti3d-3TuKAiHo.csv' }

transformer = Transformer.from_crs( 'epsg:4326', 'epsg:2056' )
swiss_topo_lon, swiss_topo_lat = transformer.transform( gps_lat, gps_lon)

filename = metadata_links['2m']
grid_size = 2
radius = 3
tile_meta_df = get_tile_metadata(filename)
target_tiles = get_targets(swiss_topo_lat, swiss_topo_lon, tile_meta_df, radius)
# plot_tile_corners(target_tiles)

array, blank_array = get_tiles(target_tiles)

observer_pixel, observer_height = get_observer_position(array, blank_array, swiss_topo_lat, swiss_topo_lon )
peaks_df = get_peaks( array, observer_pixel, observer_height, grid_size)

global mdf_list, tdf_list, amdf_list 
mdf_list, tdf_list, amdf_list  = [], [], []

for month in np.arange(1,13):
    # td = datetime.timedelta(days = interval)
    # final_date = start_date + n_intervals * td
    year = 2021
    day = 1
    date = {'year':year,'month':month,'day':day}
    start_date = datetime.date(year = date['year'], month = date['month'], day = date['day'])
    mdf_,tdf_,amdf_  = get_data(gps_coords, observer_height, peaks_df, start_date)
    mdf_list.append(mdf_)
    tdf_list.append(tdf_)
    amdf_list.append(amdf_)

app = dash.Dash(__name__)
server = app.server

month = 1

month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

app.layout = html.Div([
    html.Div( [dcc.Dropdown(id='date-select', options=[ {'label': month_names[i], 'value': i} for i in np.arange(12)],
                            style={'width': '140px', 'align-items': 'center'}
                            # style = {'width':'100%', 'display': 'flex', 'align-items': 'center', 'justify-content': 'center'}
                            )] ), \
    dcc.Graph(id='plot1', style={'width': '90vh', 'height': '90vh'} )
    ])


@app.callback(
    Output('plot1', 'figure'),
    Input('date-select', 'value'))    
def make_solmap(month):
    mdf = mdf_list[month]
    tdf = tdf_list[month]
    peak_lines = make_line_dict(mdf.bearing, mdf.peak_angle, color='black', width = 0.5)

    pio.templates.default = "simple_white"

    fig = go.Figure(
        data=peak_lines,
    )

    annotations = []
    gdf = tdf.groupby('time')
    for hour, df in gdf:
        df = df.sort_values('date').reset_index()
        # print(df.head)
        x = float( df.azimuth )
        y = float( df.elevation )
        text = hour
        grad = float( df.grad )
        fig.add_trace(
            go.Scatter(
                x=[ x, x + 2 * grad],
                y=[ y, y - 5] ,
                line = dict( color="black", width=.1), 
                marker = None,
                mode = 'lines',
                showlegend = False
            )
        )
        # markers.append(make_marker_dict(x,y,hour))
        annotations.append( make_annotation_dict(x, y, text, grad) )

    # fig.update_annotations(annotations)
    fig.add_traces(
        get_sun_lines(mdf)
    )

    fig.update_layout( 
        annotations = annotations,
        xaxis = dict(
            tickmode = 'array',
            tickvals = [45.0, 67.5, 90.0, 112.5, 135.0, 157.5, 180.0, 202.5, 225.0, 247.5, 270.0] ,
            ticktext = ['NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W'] ),
        yaxis = dict(
            range = [-10, 80]
        ) )
    # fig.write_image("name.eps", width=1920, height=1080)
    return fig

if __name__ == '__main__':
    app.run_server(debug=True, port=5000 )