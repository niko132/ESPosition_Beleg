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


plotter = RealtimePlotter(anchors)

localization_algorithms = {
    'tlsl': TrilaterationLeastSquaresLocalization(anchors, plotter=plotter),
    'twcl': TrilaterationWeightedCentroidLocalization(anchors, plotter=plotter),
    'fpl': FingerprintingLocalization("./fingerprint_maps/2024_11_06_22_12_16.csv", plotter.background.size, plotter=plotter)
}

localization_dict = defaultdict(dict)

def localization_update():
    df = pd.read_csv("./fingerprint_maps/2024_11_06_22_12_16.csv", index_col=False)
    df_mean = df.groupby(['monitor_mac', 'target_position_x', 'target_position_y', 'anchor_position_x', 'anchor_position_y'], as_index=False).agg({'rssi':['median']})
    df_mean.columns = ['monitor_mac', 'target_position_x', 'target_position_y', 'anchor_position_x', 'anchor_position_y', 'rssi_median']
    df_mean['target_position'] = df_mean[['target_position_x', 'target_position_y']].apply(tuple, axis=1)
    
    print(df_mean)
    
    target_positions = df_mean['target_position'].unique()
    target_mac = df['target_mac'].unique()[0]
    
    error_dict = {algorithm_name: [] for algorithm_name in localization_algorithms}
    
    for target_position in target_positions:
        rows = df_mean[df_mean['target_position'] == target_position]
        rssis = {row['monitor_mac']: row['rssi_median'] for _, row in rows.iterrows()}
        
        print(target_position)
        print(rssis)
        
        plotter.target_position = [target_position]
        
        target_position_np = np.array(target_position)
        
        print('==========================================')
        
        for algorithm_name, algorithm in localization_algorithms.items():
            localization_data = algorithm.localize(rssis)
            localization_dict[target_mac][algorithm_name] = localization_data
            
            position_estimation = localization_data['position']
            err = np.linalg.norm(np.array(position_estimation) - target_position_np)
            error_dict[algorithm_name].append(err)
            
            print(algorithm_name + ': ' + str(err))
        
        print('==========================================')
        
        plotter.set_data(localization_dict)        
        plotter.start_plotting(False)
    
    error_dict = {algorithm_name: np.array(error_dict[algorithm_name]) for algorithm_name in error_dict}
    
    print('++++++++++++++++++++++++++++++++++++++++++')
    for algorithm_name in error_dict:
        print(algorithm_name + ': ' + str(error_dict[algorithm_name].sum()))
    print('++++++++++++++++++++++++++++++++++++++++++')
    
    print('++++++++++++++++++++++++++++++++++++++++++')
    for algorithm_name in error_dict:
        print(algorithm_name + ': ' + str(error_dict[algorithm_name].mean()))
    print('++++++++++++++++++++++++++++++++++++++++++')
    
    
    N = len(target_positions)
    y = np.arange(N) / float(N)
    
    # plotting 
    plt.xlabel('Distance error (cm)') 
    plt.ylabel('CDF')
    
    for algorithm_name in error_dict:
        sorted_errors = np.sort(error_dict[algorithm_name])
        plt.plot(sorted_errors, y, marker='o', label=algorithm_name)
    
    plt.legend()
    plt.show()

localization_update()