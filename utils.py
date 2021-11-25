import csv, sys
import requests
import urllib.request
import os
import pandas as pd
import numpy as np

import rasterio as rio
from rasterio.plot import show
from rasterio import merge
from matplotlib import pyplot as plt
import seaborn as sns
from pyproj import Transformer
# from matplotlib import pyplot as plt

from scipy.interpolate import interpn

import datetime as datetime
from astropy.coordinates import get_sun, AltAz, EarthLocation
from astropy.time import Time , TimeDelta, TimezoneInfo
import astropy.units as u

def get_mtn_sun_times(mdf):
    
    mdf['daylight'] = mdf.loc[mdf.sunlight == 'day'].sunlight
    night = mdf.loc[mdf.sunlight != 'day'].sunlight
    mdf.loc[night.index, 'daylight'] = 'night'    

    mdf['angle_delta'] =  mdf.elevation - mdf.peak_angle

    posneg = 1
    epoch = 0
    for i in mdf.index:
        if mdf.loc[i, 'angle_delta'] * posneg < 0:
            mdf.loc[i, 'epoch'] = epoch
        else:
            epoch+=1
            posneg*=-1
            mdf.loc[i, 'epoch'] = epoch

    return mdf

def get_sun_path (lat, lon, height, date = None ): 

    CET = TimezoneInfo(utc_offset = 1*u.hour)

    if date == None:
        dt = Time.now().to_value( format = 'ymdhms' )
        year = dt['year']
        month = dt['month']
        day = dt['day']
    else:
        year = date.year
        month = date.month
        day = date.day

    midnight_this_morning = datetime.datetime(year,month,day, 0,0,0 , tzinfo = CET)

    time_since_midnight = np.linspace(4*60, 21*60 + 59, 500) * u.min
    time = ( Time(midnight_this_morning) + time_since_midnight )
    time = time.to_datetime(timezone=CET)

    loc = EarthLocation.from_geodetic(lon, lat, height = height, ellipsoid = 'WGS84')
    altaz = AltAz(obstime=time, location=loc )
    zen_ang = get_sun(Time(time)).transform_to(altaz)

    elevation = np.array ( zen_ang.alt )
    azimuth= np.array( zen_ang.az )

    dict = {'time' : time, 'time_since_midnight' : time_since_midnight, 'azimuth' : azimuth, 'elevation' : elevation}
    df = pd.DataFrame.from_dict(dict)

    night = df.loc[ df.elevation < 0 ] 
    df.loc[night.index, 'sunlight' ] = 'night'

    day = df.loc[ df.elevation > 0 ]
    df.loc[day.index, 'sunlight' ] = 'day'

    morning_twighlight = df.loc[ (df.elevation < 0) & (df.elevation > -18) & (df.azimuth < 180) ]
    df.loc[morning_twighlight.index, 'sunlight' ] = 'morning_twighlight'

    evening_twighlight = df.loc[ (df.elevation < 0) & (df.elevation > -18) & (df.azimuth > 180) ]
    df.loc[evening_twighlight.index, 'sunlight' ] = 'evening_twighlight'
    # dawn = daytime.head(1).time - TimeDelta( 30 * u.min ).to_datetime()
    # dusk = daytime.tail(1).time + TimeDelta( 30 * u.min ).to_datetime()
    return df


def get_observer_position( array, blank_array, lat, lon ):
    
    observer_pixel = blank_array.index(lon, lat)
    observer_height = array[0, observer_pixel[0] , observer_pixel[1]] + 2
    return observer_pixel, observer_height

def get_peaks( array, observer_pixel, observer_height, grid_size ):
    
    nrows,ncols = array.shape[1:]
    rows = np.arange(nrows)
    cols = np.arange(ncols)
    points = ( cols, rows )
    array_for_interp = array.T

    angular_resolution = 1000 # / 360 deg
    radius = 6000 # m
    n_steps = int( radius * 1.5 / grid_size) 
    peak = []
    bearing = np.linspace(0, np.pi * 2 , angular_resolution)

    for i, bearing_ in enumerate( bearing ):
        step = np.linspace(1, radius/grid_size, n_steps)
        x_sample =  observer_pixel[1] + np.array( step * np.sin(bearing_) )
        y_sample =  observer_pixel[0] - np.array( step * np.cos(bearing_) )

        inter_points = np.array([ x_sample, y_sample ]).T

        heights = interpn(points, array_for_interp, inter_points, \
                    method = 'linear', bounds_error = False, fill_value = observer_height )[:,0]   \
                     - observer_height
        distances = step * grid_size
        peak_angle = max (  heights / distances )
        peak.append(peak_angle)

    df = pd.DataFrame()
    df['bearing'] = bearing
    df['bearing_deg'] = bearing * 180/np.pi
    df['peak_angle'] = np.array(peak) * 180/np.pi

    df['horizon'] = 0
    
    return df

def get_tiles(target_tiles):
    src_list = []
    for i, tile_path in enumerate( target_tiles.tile ):
        print('Opening tile number ', i, ' of ', target_tiles.tile.size)
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
        height=array.shape[0], \
        width=array.shape[1], \
        count=1, \
        crs=src_list[0].crs, \
        transform=transform, \
        dtype = array.dtype)
    return array, blank_array

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

def get_suntimes (peaks_df, sun_df, date = 'Today', print_times = False):
    peaks_df = peaks_df.copy()
    sun_df = sun_df.copy()
    peaks_df.set_index('bearing_deg', inplace = True)
    peaks_df.drop(columns='bearing', inplace = True)
    peaks_df.index = peaks_df.index.rename('bearing')

    sun_df.index = sun_df.azimuth.copy().rename('bearing')

    mdf = pd.merge(peaks_df, sun_df, how = 'outer', left_index = True , right_index = True)
    mdf.peak_angle = mdf.peak_angle.interpolate('linear')
    mdf.dropna(subset = ['azimuth'], inplace = True)
    mdf.horizon = 0
    mdf.reset_index(inplace = True)

    # mtn_sunrise = Time( mdf.loc[mdf.peak_angle < mdf.elevation].time.min() ).to_value( format = 'ymdhms' )[[ 'hour', 'minute', 'second'] ] 
    # mtn_sunset = Time( mdf.loc[mdf.peak_angle < mdf.elevation].time.max() ).to_value( format = 'ymdhms' )[[ 'hour', 'minute', 'second'] ] 

    mtn_sunrise = [ mdf.loc[mdf.peak_angle < mdf.elevation].time.min() ][0]
    mtn_sunset = [ mdf.loc[mdf.peak_angle < mdf.elevation].time.max() ][0]

    if print_times:
        print(date)
        print('Sunrise at ', mtn_sunrise.hour, ':', mtn_sunrise.minute)
        print('Sunset at ', mtn_sunset.hour, ':', mtn_sunset.minute)
    return mdf

def get_tile_metadata(filename):
    df = pd.read_csv(filename, names = ['tile'])
    df['left_bound'] = [ int( tile.partition('3d_')[2][5:9] ) * 1000 for tile in df.tile ]
    df['bottom_bound'] = [ int( tile.partition('3d_')[2][10:14] ) * 1000 for tile in df.tile ]
#     df[['left_bound', 'bottom_bound']] = df[['left_bound', 'bottom_bound']].astype(int)

    df['right_bound'] = df['left_bound'] + 1000
    df['top_bound'] = df['bottom_bound'] + 1000

    df['tile_info'] = [tile.partition('3d_')[2].partition('3d_')[2].partition('.tif')[0][-9:] for tile in df.tile]

    return df



