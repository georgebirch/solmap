from utils import *
import seaborn as sns
import matplotlib.pyplot as plt

def plot_timelines(tdf):
    min_date = tdf.loc[tdf.midday_elev.idxmin(), 'date'  ]
    x = np.array( tdf.loc[ tdf.date == min_date ].azimuth )
    y = np.array( tdf.loc[ tdf.date == min_date ].elevation)
    t = tdf.loc[ tdf.date == min_date ].time
    grad = np.array( tdf.loc[ tdf.date == min_date ].grad)

    for i, time_ in enumerate(t):
        time = datetime.time(hour = time_ )
        label = str(time)[0:5]
        plt.scatter(x[i],y[i], color='k', marker = [ [0,0], [grad[i],-1] ] )
        plt.annotate(label, (x[i], y[i]), \
            textcoords='offset points', \
                xytext = (20*grad[i], -25), \
                    ha='center', \
                        fontsize=15)


def plot_sun_paths(mdf):

    x = mdf.loc[ mdf.daylight == 'day' ].bearing
    y = mdf.loc[ mdf.daylight == 'day' ].elevation
    f = sns.lineplot(x = x, y = y , color = 'gold', linewidth=1)

    # x = mdf.loc[ mdf.daylight == 'day' ].bearing
    # y = mdf.loc[ mdf.daylight == 'day' ].elevation
    # f = sns.lineplot(x = x, y = y , color = 'gold', linewidth=4)

    x = mdf.loc[ mdf.sunlight == 'morning_twighlight' ].azimuth
    y = mdf.loc[ mdf.sunlight == 'morning_twighlight' ].elevation
    sns.lineplot(x = x, y = y , color = 'royalblue', linewidth=1)

    x = mdf.loc[ mdf.sunlight == 'evening_twighlight' ].azimuth
    y = mdf.loc[ mdf.sunlight == 'evening_twighlight' ].elevation
    sns.lineplot(x = x, y = y , color = 'royalblue', linewidth=1)

    for epoch in mdf.epoch.unique():
        if epoch%2 == 1:
            x = mdf.loc[ mdf.epoch == epoch ].azimuth
            y = mdf.loc[ mdf.epoch == epoch ].elevation
            sns.lineplot(x = x, y = y , color = 'gold', linewidth=4)

    # ax.set_aspect(2, adjustable = 'datalim')
    # x = mdf.loc[ mdf.sunlight == 'mountain_day' ].bearing
    # y = mdf.loc[ mdf.sunlight == 'mountain_day' ].elevation
    # sns.lineplot(x = x, y = y , color = 'gold', linewidth=4)

    # x  = mdf.loc[mdf.sun_is_out == False, 'bearing']
    # y = mdf.loc[mdf.sun_is_out == False, 'elevation']
    # sns.lineplot(x = x, y = y , color = 'b', linewidth=2)


    # x1 = mdf.loc[ mdf.sunlight == 'mountain_dawn' ].bearing
    # y1 = mdf.loc[ mdf.sunlight == 'mountain_dawn' ].elevation
    # sns.lineplot(x = x1, y = y1 , color = 'gold', linewidth=1)

    # x1 = mdf.loc[ mdf.sunlight == 'mountain_dusk' ].bearing
    # y1 = mdf.loc[ mdf.sunlight == 'mountain_dusk' ].elevation
    # sns.lineplot(x = x1, y = y1 , color = 'gold', linewidth=1)

#     ax.set_ylim(-10)

def plot_tile_corners(target_tiles):
    x1 = target_tiles.left_bound
    y1 = target_tiles.top_bound
    x2 = target_tiles.right_bound
    y2 = target_tiles.bottom_bound

    x = np.array( [x1, x1, x2, x2, x1] )
    y = np.array( [y1, y2, y2, y1, y1] )

    fig = sns.set_theme(style="white", font_scale = 1)

    fig, ax = plt.subplots(figsize = [10,10])
    fig = plt.plot(x,y)
    ax.set_aspect('equal')

def plot_main(google_lat, google_lon, observer_height, peaks_df, start_date, final_date, td ):
    fig, ax = plt.subplots(figsize=(30, 10))
    sns.lineplot(x = peaks_df.bearing_deg, y = peaks_df.peak_angle  , color="k", linewidth=1)

    hour = np.arange(4, 22)
    tdf_ = pd.DataFrame(columns = ['date', 'time', 'azimuth', 'elevation'])
    tdf = tdf_.copy()
    date = start_date
    amdf = pd.DataFrame()
    while date <= final_date:
        sun_df = get_sun_path(google_lat, google_lon, observer_height, date)
        mdf = get_mtn_sun_times(get_suntimes (peaks_df, sun_df))
        mdf['date'] = date
        # time_df.index = ['azimuth', 'elevation']
        for i in hour:
            ind = mdf.time_since_midnight.sub( i*60 ).abs().idxmin()
            tdf_.loc[i, 'azimuth'] = mdf.loc[ind, 'azimuth']
            tdf_.loc[i, 'elevation'] = mdf.loc[ind, 'elevation'] 
        tdf_['grad'] = np.gradient(tdf_.elevation, tdf_.azimuth)
        tdf_['date'] = date
        tdf_['time'] = hour
        tdf_['midday_elev'] = max(mdf.elevation)
        tdf = pd.concat([tdf, tdf_])
        tdf.reset_index(drop = True, inplace = True)
        amdf = pd.concat([amdf, mdf])
        date = date+td

        plot_sun_paths(mdf)

    # gdf = tdf.groupby('time')
    # for hour, df in gdf:
    #     df = df.sort_values('date').reset_index()
    #     # print(df.head)
    #     x = df.azimuth
    #     y = df.elevation
    #     m = df.grad
    #     verts = list( zip( list( np.ones(len(m))),  list(m) ) )    
    #     sns.lineplot(x=x, y=y, sort=False, color='k', linewidth=0.5)
    #     # plt.scatter(x=x,y=y,color='k' \
    #     # , marker = verts \
    #     # )
    plot_timelines(tdf)

    sns.set_theme(style="whitegrid", font_scale = 1)
    ax.set_xticks( np.arange(0,360,30) ) 
    ax.set_xlim(50, 310 )
    ax.set_ylim(-10)
    plt.xlabel( 'Compass Bearing from North')
    plt.ylabel( 'Elevation Angle from Horizon')
    # plt.show()
    fig.savefig('/Users/george-birchenough/Documents/Plots/vectorplot.eps', format='eps')
    return fig



def get_figure(gps_loc, date):

    lat, lon = gps_loc

    interval = 30
    n_intervals = 0

    # start_date = datetime.datetime.now().date()

    start_date = datetime.date(year = date['year'], month = date['month'], day = date['day'])

    td = datetime.timedelta(days = interval)
    final_date = start_date + n_intervals * td

    metadata_links = {'2m' : '/Users/george-birchenough/Downloads/ch.swisstopo.swissalti3d-fGQ3d2A6.csv' , \
                    '0.5m' : 'https://ogd.swisstopo.admin.ch/resources/ch.swisstopo.swissalti3d-3TuKAiHo.csv' }

    transformer = Transformer.from_crs( 'epsg:4326', 'epsg:2056' )
    swiss_topo_lon, swiss_topo_lat = transformer.transform( lat, lon)

    filename = metadata_links['2m']
    grid_size = 2
    radius = 1
    tile_meta_df = get_tile_metadata(filename)
    target_tiles = get_targets(swiss_topo_lat, swiss_topo_lon, tile_meta_df, radius)
    plot_tile_corners(target_tiles)

    array, blank_array = get_tiles(target_tiles)

    observer_pixel, observer_height = get_observer_position(array, blank_array, swiss_topo_lat, swiss_topo_lon )
    peaks_df = get_peaks( array, observer_pixel, observer_height, grid_size)


    fig = plot_main(lat, lon, observer_height, peaks_df, start_date, final_date, td )
    return fig
