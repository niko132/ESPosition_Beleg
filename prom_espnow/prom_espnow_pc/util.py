from config import *
import numpy as np

def sq_dist(a, b):
	return ((a[0] - b[0])**2 + (a[1] - b[1])**2)

def dist(a, b):
	return sq_dist(a, b)**0.5

def path_loss_model(distance):
    rssi = PATH_LOSS_L0 - 10.0 * PATH_LOSS_EXP * np.log10(distance)
    return rssi

def inverse_path_loss_model(rssi):
    distance = pow(10, ((PATH_LOSS_L0 - rssi) / (10.0 * PATH_LOSS_EXP)))
    return distance