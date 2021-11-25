from utils import *
from plot_utils import *

google_lat, google_lon = 46.500458, 8.052669


year = 2020
month = 1
day = 1

interval = 30
n_intervals = 0

start_date = datetime.date(year = year, month = month, day = day)
start_date = datetime.datetime.now().date()

td = datetime.timedelta(days = interval)
final_date = start_date + n_intervals * td

metadata_links = {'2m' : '/Users/george-birchenough/Downloads/ch.swisstopo.swissalti3d-fGQ3d2A6.csv' , \
                  '0.5m' : 'https://ogd.swisstopo.admin.ch/resources/ch.swisstopo.swissalti3d-3TuKAiHo.csv' }

transformer = Transformer.from_crs( 'epsg:4326', 'epsg:2056' )
observer_lon, observer_lat = transformer.transform( google_lat, google_lon)

filename = metadata_links['2m']
grid_size = 2
radius = 1
tile_meta_df = get_tile_metadata(filename)
target_tiles = get_targets(observer_lat, observer_lon, tile_meta_df, radius)
plot_tile_corners(target_tiles)

array, blank_array = get_tiles(target_tiles)

observer_pixel, observer_height = get_observer_position(array, blank_array, observer_lat, observer_lon )
peaks_df = get_peaks( array, observer_pixel, observer_height, grid_size)

plot_main(google_lat, google_lon, observer_height, peaks_df, start_date, final_date, td )