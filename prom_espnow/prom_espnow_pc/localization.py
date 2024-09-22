import numpy as np
from scipy.optimize import minimize
from util import *

def trilaterate(positions, rssis):
    distances = [inverse_path_loss_model(rssi) for rssi in rssis]

    def loss(e):
        return sum([ ( dist(e, position) - distance )**2 for (position, distance) in zip(positions, distances)])
    
    res = minimize(loss, np.mean(positions, axis=0))
    position = res.x
    success = res.success
    
    return position

def weighted_centroid_localization(positions, rssis):
    distances = np.array([inverse_path_loss_model(rssi) for rssi in rssis])
    
    # Calculate the weights as the inverse of the distances
    weights = 1.0 / distances
    
    # Normalize the weights so they sum up to 1
    weights /= np.sum(weights)
    
    # Weighted sum of positions
    x = np.sum([w * pos[0] for w, pos in zip(weights, positions)])
    y = np.sum([w * pos[1] for w, pos in zip(weights, positions)])
    
    return (x, y)