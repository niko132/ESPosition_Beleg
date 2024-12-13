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

plot_init()

'''
try:
    nodeSerial = serial.Serial('COM6', 115200, timeout=1)
except:
    print("Error opening serial port")
'''


'''
anchors = {
    "24a1602ccfab": (38.18080724876424, 746.8789126853377), # Schlafzimmer ESP8266
    "2462abfb15a8": (38.18080724876424, 746.8789126853377), # Schlafzimmer ESP32
    "a4cf12fdaea9": (755.9783772652386, 810.2518533772651), # Küche ESP8266
    "f8b3b734347c": (755.9783772652386, 810.2518533772651), # Küche ESP32
    "d8bfc0117c7d": (38.18080724876424, 30.0), # Wohnzimmer ESP8266
    "f8b3b7329214": (38.18080724876424, 30.0), # Wohnzimmer ESP32
    "483fda467e7a": (580.0, 500.0), # Flur ESP8266
}
'''

anchors = {
    # ESP8266
    "483fda467e7a": (1461, 241),
    "d8bfc0117c7d": (107, 884),
    "24a1602ccfab": (2048, 884),
    "a4cf12fdaea9": (861, 580),

    # ESP32
    "a0a3b3ff35c0": (2048, 884),
    "f8b3b734347c": (1047, 884),
    "a0a3b3ff66b4": (107, 884),
    "08a6f7a1e5c8": (884, 45),
    "f8b3b732fb6c": (1461, 241),
    "f8b3b73303e8": (861, 580),
}


# anchors = get_test_anchors()

# sim_target_position = (1.0, 1.0)
# simulator = ESPositionMainNodeSimulator(anchors, "100000000000", sim_target_position, True, True, 100, True)

playback = ESPositionMainNodePlayback("d81c79de34e1", "./fingerprint_maps/12_12_24/2024_12_12_13_19_04_iPhone_path_yt_filtered.csv")
# anchors = playback.get_anchors()

# plot_monitors(anchors.values())

'''
target_position_in_px = (0, 200)
target_position_in_m = (env_to_m(target_position_in_px[0]), env_to_m(target_position_in_px[1]))

anchor_positions_in_m = [(env_to_m(x), env_to_m(y)) for (x, y) in anchors.values()]
distances_in_m = [dist(target_position_in_m, anchor_position) for anchor_position in anchor_positions_in_m]
rssis = [path_loss_model(distance) for distance in distances_in_m]
print(distances_in_m)
print(rssis)

plot_results([(env_to_m(x), env_to_m(y)) for (x, y) in anchors.values()], distances_in_m, target_position_in_m)
'''

pattern = re.compile("^([0-9A-Fa-f]{12})_([0-9A-Fa-f]{12}):(-?[0-9]+\.?[0-9]*)$")

monitor_dict = defaultdict(dict)


import time
import datetime as dt


def message_handler_func():    
    while True:
        #read data from serial port
        # line = nodeSerial.readline()
        # print(nodeSerial.in_waiting)
        # line = simulator.readline()
        line = playback.readline()

        #if there is smth do smth
        if len(line) >= 1:
            try:
                timestamp = time.time()
                line_decoded = line.decode("utf-8")
                # print(line_decoded)
                match = pattern.match(line_decoded)
                if match:
                    monitor_mac = match.group(1)
                    target_mac = match.group(2)
                    rssi = float(match.group(3))
                    # print("Received: " + str(monitor_mac) + " "  + str(target_mac) + " "  + str(rssi))
                    
                    item = PacketItem(0, timestamp, rssi)
                    
                    try:
                        _ = monitor_dict[target_mac][monitor_mac]
                    except KeyError:
                        monitor_dict[target_mac][monitor_mac] = MedianPacketAggregation(50)
                    
                    monitor_dict[target_mac][monitor_mac].add_packet(item)
                    
                    # plot_graph(monitor_mac, rssi)
                    # plot_graph(monitor_mac + "_filtered", monitor_dict[target_mac][monitor_mac].get_packet().rssi)
                    
                    # print(monitor_dict)
                else:
                    print("No match")
            except Exception as e: 
                print(e)
                print("could not decode")

message_thread = threading.Thread(target=message_handler_func, daemon=True)
message_thread.start()



plotter = RealtimePlotter(anchors)

localization_algorithms = {
    'tlsl': TrilaterationLeastSquaresLocalization(anchors, plotter=plotter),
    'twcl': TrilaterationWeightedCentroidLocalization(anchors, plotter=plotter),
    'fpl': FingerprintingLocalization("./fingerprint_maps/12_12_24/2024_12_12_10_17_51_iPhone_3_filtered.csv", plotter.background.size, plotter=plotter)
}

localization_dict = defaultdict(dict)

from copy import deepcopy

def localization_update():
    while True:
        # to prevent starvation of the message thread
        # python threading is weird
        # while nodeSerial.in_waiting > 0:
        #    time.sleep(0.01)
        
        monitor_dict1 = deepcopy(monitor_dict)
    
        for target_mac in monitor_dict1:
            if len(monitor_dict1[target_mac].keys()) < 3: # TODO: 3
                continue
            
            rssis = {monitor_mac: monitor_dict1[target_mac][monitor_mac].get_packet().rssi for monitor_mac in monitor_dict1[target_mac].keys()}
            
            for algorithm_name, algorithm in localization_algorithms.items():
                localization_data = algorithm.localize(rssis)
                localization_dict[target_mac][algorithm_name] = localization_data
        
        plotter.set_data(localization_dict)

localization_thread = threading.Thread(target=localization_update, daemon=True)
localization_thread.start()

# fpl.start_plot()
plotter.start_plotting()