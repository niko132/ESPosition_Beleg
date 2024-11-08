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

try:
    nodeSerial = serial.Serial('COM5', 115200, timeout=1)
except:
    print("Error opening serial port")


anchors = {
    "24a1602ccfab": (38.18080724876424, 746.8789126853377),
    "a4cf12fdaea9": (755.9783772652386, 810.2518533772651),
    "d8bfc0117c7d": (38.18080724876424, 30.0),
    "483fda467e7a": (580.0, 500.0),
}


# anchors = get_test_anchors()

# sim_target_position = (1.0, 1.0)
# simulator = ESPositionMainNodeSimulator(anchors, "100000000000", sim_target_position, True, True, 100, True)

# playback = ESPositionMainNodePlayback("342eb61ec446", "./recordings/2024_09_05_17_50_22_walk_through_flat.csv")
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
        line = nodeSerial.readline()
        print(nodeSerial.in_waiting)
        # line = simulator.readline()
        # line = playback.readline()

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



plotter = RealtimePlotter()

tlsl = TrilaterationLeastSquaresLocalization(anchors, plotter=plotter)
twcl = TrilaterationWeightedCentroidLocalization(anchors, plotter=plotter)
fpl = FingerprintingLocalization("./fingerprint_maps/2024_11_06_22_12_16.csv", plotter.background.size, plotter=plotter)

def localization_update():
    while True:
        # to prevent starvation of the message thread
        # python threading is weird
        while nodeSerial.in_waiting > 0:
            time.sleep(0.01)
    
        for target_mac in monitor_dict:
            if len(monitor_dict[target_mac].keys()) < 4: # TODO: 3
                continue
            
            rssis = {monitor_mac: monitor_dict[target_mac][monitor_mac].get_packet().rssi for monitor_mac in monitor_dict[target_mac].keys()}
            
            tlsl.localize(rssis)
            twcl.localize(rssis)
            fpl.localize(rssis)

localization_thread = threading.Thread(target=localization_update, daemon=True)
localization_thread.start()

# fpl.start_plot()
plotter.start_plotting()