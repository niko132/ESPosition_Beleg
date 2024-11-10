import serial
import re
import time
from collections import defaultdict
import numpy as np
from plot import *
from util import *
from simulation import *
from localization import *
from aggregation import *

import matplotlib.style as mplstyle
mplstyle.use('fast')


import scipy


anchors = {
    "24a1602ccfab": (38.18080724876424, 746.8789126853377),
    "a4cf12fdaea9": (755.9783772652386, 810.2518533772651),
    "d8bfc0117c7d": (38.18080724876424, 30.0),
    "483fda467e7a": (580.0, 500.0),
}


plotter = RealtimePlotter()

tlsl = TrilaterationLeastSquaresLocalization(anchors, smooth=False, plotter=plotter)
twcl = TrilaterationWeightedCentroidLocalization(anchors, smooth=False, plotter=plotter)
fpl = FingerprintingLocalization("./fingerprint_maps/2024_11_06_22_12_16.csv", plotter.background.size, smooth=False, plotter=plotter)

def localization_update():
    df = pd.read_csv("./fingerprint_maps/2024_11_06_22_12_16.csv", index_col=False)
    df_mean = df.groupby(['monitor_mac', 'target_position_x', 'target_position_y', 'anchor_position_x', 'anchor_position_y'], as_index=False).agg({'rssi':['median']})
    df_mean.columns = ['monitor_mac', 'target_position_x', 'target_position_y', 'anchor_position_x', 'anchor_position_y', 'rssi_median']
    df_mean['target_position'] = df_mean[['target_position_x', 'target_position_y']].apply(tuple, axis=1)
    
    target_positions = df_mean['target_position'].unique()
    
    tlsl_errors = []
    twcl_errors = []
    fpl_errors = []
    
    for target_position in target_positions:
        rows = df_mean[df_mean['target_position'] == target_position]
        rssis = {row['monitor_mac']: row['rssi_median'] for _, row in rows.iterrows()}
        
        print(target_position)
        print(rssis)
        
        plotter.target_position = [target_position]
        
        target_position_np = np.array(target_position)
        
        tlsl_est = tlsl.localize(rssis)
        twcl_est = twcl.localize(rssis)
        fpl_est = fpl.localize(rssis)
        
        tlsl_err = np.linalg.norm(np.array(tlsl_est) - target_position_np)
        twcl_err = np.linalg.norm(np.array(twcl_est) - target_position_np)
        fpl_err = np.linalg.norm(np.array(fpl_est) - target_position_np)
        
        tlsl_errors.append(tlsl_err)
        twcl_errors.append(twcl_err)
        fpl_errors.append(fpl_err)
        
        print('==========================================')
        print('tlsl: ' + str(tlsl_err))
        print('twcl: ' + str(twcl_err))
        print('fpl: ' + str(fpl_err))
        print('==========================================')
        
        plotter.plot()
    
    tlsl_errors = np.array(tlsl_errors)
    twcl_errors = np.array(twcl_errors)
    fpl_errors = np.array(fpl_errors)
    
    print('++++++++++++++++++++++++++++++++++++++++++')
    print('tlsl: ' + str(tlsl_errors.sum()))
    print('twcl: ' + str(twcl_errors.sum()))
    print('fpl: ' + str(fpl_errors.sum()))
    print('++++++++++++++++++++++++++++++++++++++++++')
    
    print('******************************************')
    print('tlsl: ' + str(tlsl_errors.mean()))
    print('twcl: ' + str(twcl_errors.mean()))
    print('fpl: ' + str(fpl_errors.mean()))
    print('******************************************')
    
    
    N = len(tlsl_errors)
    y = np.arange(N) / float(N)
    tlsl_errors_sorted = np.sort(tlsl_errors)
    twcl_errors_sorted = np.sort(twcl_errors)
    fpl_errors_sorted = np.sort(fpl_errors)
    
    # plotting 
    plt.xlabel('Distance error (cm)') 
    plt.ylabel('CDF')
      
    plt.plot(tlsl_errors_sorted, y, marker='o', label='tlsl')
    plt.plot(twcl_errors_sorted, y, marker='o', label='twcl')
    plt.plot(fpl_errors_sorted, y, marker='o', label='fpl')
    plt.legend()
    plt.show()

localization_update()