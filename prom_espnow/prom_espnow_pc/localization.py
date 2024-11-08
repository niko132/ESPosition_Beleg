from abc import ABC, abstractmethod
import numpy as np
import pandas as pd
from scipy.interpolate import Rbf
from util import *

class AbstractLocalization(ABC):

    def __init__(self):
        self.position = np.array((0.0, 0.0))
        self.smooth = True

    @abstractmethod
    def localize(self, rssis):
        pass
    
    def set_position(self, position):
        if self.smooth:
            self.position = 0.99 * self.position + 0.01 * np.array(position)
        return self.position

class TrilaterationLeastSquaresLocalization(AbstractLocalization):
    def __init__(self, anchor_positions, plotter=None):
        super().__init__()
        
        self.anchor_positions = anchor_positions
        self.plotter = plotter
    
    def localize(self, rssis):
        monitor_macs_intersec = self.anchor_positions.keys() & rssis.keys()
        anchor_positions_intersec = [self.anchor_positions[monitor_mac] for monitor_mac in monitor_macs_intersec]
        rssis_intersec = [rssis[monitor_mac] for monitor_mac in monitor_macs_intersec]
        
        positions = anchor_positions_intersec
        distances = [inverse_path_loss_model(rssi) * 100.0 for rssi in rssis_intersec] # m to cm
        
        
        # Number of known positions
        n = len(positions)
        
        # Build the A matrix and b vector
        A = []
        b = []
        
        x_n, y_n = positions[n-1]
        d_n = distances[n-1]
        for i in range(n - 1):
            x_i, y_i = positions[i]
            d_i = distances[i]
            A.append([2*(x_i - x_n), 2*(y_i - y_n)])
            b.append(x_i**2 + y_i**2 - x_n**2 - y_n**2 - d_i**2 + d_n**2)
        A = np.array(A)
        b = np.array(b)

        # Compute the least squares solution using the normal equation: x = (A^T A)^(-1) A^T b
        x, residuals, rank, s = np.linalg.lstsq(A, b, rcond=None)
        
        super().set_position(x)
        
        if self.plotter is not None:
            self.plotter.target_estimation["trilateration_ls"] = self.position
            self.plotter.anchor_positions = positions
            self.plotter.anchor_distances = distances
            self.plotter.new_data_available = True
        
        return self.position

class TrilaterationWeightedCentroidLocalization(AbstractLocalization):
    def __init__(self, anchor_positions, plotter=None):
        super().__init__()
        
        self.anchor_positions = anchor_positions
        self.plotter = plotter
    
    def localize(self, rssis):
        monitor_macs_intersec = self.anchor_positions.keys() & rssis.keys()
        anchor_positions_intersec = [self.anchor_positions[monitor_mac] for monitor_mac in monitor_macs_intersec]
        rssis_intersec = [rssis[monitor_mac] for monitor_mac in monitor_macs_intersec]
        
        positions = anchor_positions_intersec
        distances = [inverse_path_loss_model(rssi) * 100.0 for rssi in rssis_intersec] # m to cm
        
        positions_np = np.array(positions)
        distances_np = np.array(distances)
        
        # Calculate the weights as the inverse of the distances
        weights = 1.0 / distances_np
        
        # Normalize the weights so they sum up to 1
        weights /= np.sum(weights)
        
        # Weighted sum of positions
        x = np.sum([w * pos[0] for w, pos in zip(weights, positions_np)])
        y = np.sum([w * pos[1] for w, pos in zip(weights, positions_np)])
        
        super().set_position((x, y))
        
        if self.plotter is not None:
            self.plotter.target_estimation["trilateration_wcl"] = self.position
            self.plotter.anchor_positions = positions
            self.plotter.anchor_distances = distances
            self.plotter.new_data_available = True
        
        return self.position

class FingerprintingLocalization(AbstractLocalization):
    def __init__(self, fingerprints_file_path, background_size, heatmap_resolution=5.0, plotter=None): # every 5cm
        super().__init__()
        
        self.plotter = plotter
        
        x = np.arange(0, background_size[0], heatmap_resolution)
        y = np.arange(0, background_size[1], heatmap_resolution)
        self.pos_lookup_x = np.append(x, background_size[0]) # include boundary
        self.pos_lookup_y = np.append(y, background_size[1])
        num_x = len(self.pos_lookup_x)
        num_y = len(self.pos_lookup_y)
            
        gx, gy = np.meshgrid(self.pos_lookup_x, self.pos_lookup_y)
        gx, gy = gx.flatten(), gy.flatten()
        
        
        df = pd.read_csv(fingerprints_file_path, index_col=False)
        df_mean = df.groupby(['monitor_mac', 'target_position_x', 'target_position_y', 'anchor_position_x', 'anchor_position_y'], as_index=False).agg({'rssi':['median']})
        df_mean.columns = ['monitor_mac', 'target_position_x', 'target_position_y', 'anchor_position_x', 'anchor_position_y', 'rssi_median']
        
        def generate_interpolated_fingerprint_map(monitor_mac):
            monitor_rows = df_mean[df_mean['monitor_mac'] == monitor_mac]
            
            target_positions_x = monitor_rows['target_position_x'].to_list()
            target_positions_y = monitor_rows['target_position_y'].to_list()
            rssi_medians = monitor_rows['rssi_median'].to_list()
            
            
            # from https://github.com/jantman/python-wifi-survey-heatmap/blob/master/wifi_survey_heatmap/heatmap.py
            
            rbf = Rbf(target_positions_x, target_positions_y, rssi_medians, function='linear')
            z = rbf(gx, gy)
            z = z.reshape((num_y, num_x))
            
            return z
        
        monitor_macs = df_mean['monitor_mac'].unique()
        self.interpolated_fingerprints = {monitor_mac: generate_interpolated_fingerprint_map(monitor_mac) for monitor_mac in monitor_macs}
    
    def localize(self, rssis):
        monitor_macs_intersection = self.interpolated_fingerprints.keys() & rssis.keys()
        interpolated_fingerprints_intersection = np.array([self.interpolated_fingerprints[monitor_mac] for monitor_mac in monitor_macs_intersection])
        rssis_intersection = np.array([rssis[monitor_mac] for monitor_mac in monitor_macs_intersection])
        
        diff = np.moveaxis(interpolated_fingerprints_intersection, 0, -1) - rssis_intersection
        norm = np.linalg.norm(diff, axis=2)
        min_pos_heatmap = np.unravel_index(np.argmin(norm, axis=None), norm.shape)        
        min_pos = (self.pos_lookup_x[min_pos_heatmap[1]], self.pos_lookup_y[min_pos_heatmap[0]])
        
        super().set_position(min_pos)
        
        if self.plotter is not None:
            self.plotter.heatmap = norm
            self.plotter.target_estimation["fingerprint"] = self.position
            self.plotter.new_data_available = True
        
        return self.position