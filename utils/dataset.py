
import rasterio as rio
from rasterio.plot import show
from rasterio import merge
import pandas as pd
import numpy as np

import urllib.request


def get_tiles(target_tiles, source = 'local'):
    target_tiles['source'] = target_tiles['local_tile'] if source == 'local' else target_tiles['tile']

    src_list = []
    for i, tile_path in enumerate( target_tiles.source ):
        print('Opening tile number ', i, ' of ', target_tiles.source.size)
        src_list.append(rio.open(tile_path, mode='r'))
    print('Done.')
    print('Merging ... ')
    array, transform = rio.merge.merge(src_list)
    print('Done.')
    src = src_list[0]
    blank_array = rio.open( \
        '/tmp/new.tif', \
        'w', \
        driver='GTiff', \
        height=array.shape[1], \
        width=array.shape[2], \
        count=1, \
        crs=src_list[0].crs, \
        transform=transform, \
        dtype = array.dtype)
    return array, blank_array, transform

def save_tiles(target_tiles):
    base = '/Users/george-birchenough/Documents/SwissAlti3D_temp/'
    for i, tile_path in enumerate( target_tiles.tile ):
        out_path = base + str(target_tiles.index[i]) + '.tif'
        print(out_path)
        urllib.request.urlretrieve(tile_path, out_path)


def get_targets(observer_lat, observer_lon, tile_meta_df, radius):
    df = tile_meta_df
    target_tiles = pd.DataFrame()
    for y in np.linspace(0, radius , radius + 1 ):
        x = (radius**2 - y**2 ) ** 0.5
        for i in np.linspace(-x, x, 2 * radius + 1 ):
            lon = observer_lon + 1000 * i
            lat = observer_lat - 1000 * y
            tile = df.loc[ (df.left_bound < lon) & (df.right_bound > lon) \
                          & (df.bottom_bound < lat) & (df.top_bound > lat) ]
            target_tiles = target_tiles.append(tile)
    target_tiles.drop_duplicates(inplace = True)
    target_tiles.reset_index(inplace = True)
    return target_tiles

def get_tile_metadata(filename, local_data_dir):
    df = pd.read_csv(filename, names = ['tile'])
    df['local_tile'] =  [ local_data_dir + '/' + tile.partition('3d_')[2].partition('3d_')[2] for tile in df.tile]

    df['left_bound'] = [ int( tile.partition('3d_')[2][5:9] ) * 1000 for tile in df.tile ]
    df['bottom_bound'] = [ int( tile.partition('3d_')[2][10:14] ) * 1000 for tile in df.tile ]
    # df[['left_bound', 'bottom_bound']] = df[['left_bound', 'bottom_bound']].astype(int)

    df['right_bound'] = df['left_bound'] + 1000
    df['top_bound'] = df['bottom_bound'] + 1000

    df['tile_info'] = [tile.partition('3d_')[2].partition('3d_')[2].partition('.tif')[0][-9:] for tile in df.tile]

    return df
