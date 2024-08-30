import numpy as np
from scipy.optimize import minimize
from util import *

def trilaterate(positions, distances):
    def loss(e):
        return sum([ ( dist(e, position) - distance )**2 for (position, distance) in zip(positions, distances) ])
        
    print("Mean:")
    print(positions)
    print(np.mean(positions, axis=0))
    
    res = minimize(loss, np.mean(positions, axis=0))
    position = res.x
    success = res.success
    
    print("Position: " + str(position) + " Success: " + str(success))
    
    return position