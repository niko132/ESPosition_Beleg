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

plot_init()

try:
    nodeSerial = serial.Serial('COM5', 115200, timeout=1)
except:
    print("Error opening serial port")

'''
anchor = { # 715 height
    "000000000001": (30, 560), # ´(30, 560)
    "000000000004": (550, 600), # ´(550, 600)
    "000000000005": (60, 30), # ´(60, 30)
}
'''
# anchors = get_test_anchors()

# sim_target_position = (1.0, 1.0)
# simulator = ESPositionMainNodeSimulator(anchors, "100000000000", sim_target_position, True, True, 100, True)

playback = ESPositionMainNodePlayback("342eb61ec446", "./recordings/2024_09_05_17_50_22_walk_through_flat.csv")
anchors = playback.get_anchors()

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

def message_handler_func():
    while True:
        #read data from serial port
        # line = nodeSerial.readline()
        # line = simulator.readline()
        line = playback.readline()

        #if there is smth do smth
        if len(line) >= 1:
            try:
                timestamp = time.time()
                line_decoded = line.decode("utf-8")
                print(line_decoded)
                match = pattern.match(line_decoded)
                if match:
                    monitor_mac = match.group(1)
                    target_mac = match.group(2)
                    rssi = float(match.group(3))
                    print("Received: " + str(monitor_mac) + " "  + str(target_mac) + " "  + str(rssi))
                    
                    item = PacketItem(0, timestamp, rssi)
                    
                    try:
                        _ = monitor_dict[target_mac][monitor_mac]
                    except KeyError:
                        monitor_dict[target_mac][monitor_mac] = KalmanFilterPacketAggregation()
                    
                    monitor_dict[target_mac][monitor_mac].add_packet(item)
                    
                    # plot_graph(monitor_mac, rssi)
                    # plot_graph(monitor_mac + "_filtered", monitor_dict[target_mac][monitor_mac].get_packet().rssi)
                    
                    print(monitor_dict)
                else:
                    print("No match")
            except Exception as e: 
                print(e)
                print("could not decode")

message_thread = threading.Thread(target=message_handler_func, daemon=True)
message_thread.start()


while True:    
    for target_mac in monitor_dict:
        if len(monitor_dict[target_mac].keys()) < 3:
            continue
        
        anchor_positions = [anchors[monitor_mac] for monitor_mac in monitor_dict[target_mac].keys()]
        rssis = [monitor_dict[target_mac][monitor_mac].get_packet().rssi for monitor_mac in monitor_dict[target_mac].keys()]
        distances = [inverse_path_loss_model(rssi) for rssi in rssis]
        
        # TODO: adjustable algorithm
        target_position_tri = trilaterate(anchor_positions, rssis)
        target_position_wcl = weighted_centroid_localization(anchor_positions, rssis)
        print(target_mac + ": " + str(target_position_tri))
        
        # plot_results(anchor_positions, distances, target_position, simulator.get_target_pos())
        plot_results(anchor_positions, distances, (target_position_tri, target_position_wcl), ("Tri", "WCL"))