import pandas as pd
import numpy as np

def get_azimuth_vector(azimuth):
    opp = abs( np.sin( (90 - azimuth) * np.pi / 180 ) )
    adj = (1 - opp**2)**0.5
    if azimuth < 90:
        return adj, opp
    elif azimuth < 180:
        return adj, -1*opp
    elif azimuth < 270:
        return -1*adj, -1*opp
    elif azimuth < 360:
        return -1*adj, opp

def get_shadows(slice, inter_points, el_vector, grid_size = 2):
    dict = {'x':inter_points[:,0], 'y':inter_points[:,1], 'z':slice}
    df = pd.DataFrame.from_dict(dict)

    for index in df.index:
        difs = df.loc[index::, 'z'] - df.loc[index,'z']
        dists = df.index[index::] * grid_size
        if any(difs / dists > el_vector):
            df.loc[index, 'shadow'] = True
    return df