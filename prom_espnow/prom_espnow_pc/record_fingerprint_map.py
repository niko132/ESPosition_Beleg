import serial
import time
import re
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
from config import *

from matplotlib.ticker import MultipleLocator

# GET ANCHOR POSITIONS

anchor_macs = [
    # ESP8266
    "483fda467e7a", # 1461, 241
    "d8bfc0117c7d", # 107, 884
    "24a1602ccfab", # 2048, 884
    "a4cf12fdaea9", # 861, 580

    # ESP32
    "a0a3b3ff35c0", # 2048, 884
    "f8b3b734347c", # 1047, 884
    "a0a3b3ff66b4", # 107, 884
    "08a6f7a1e5c8", # 884, 45
    "f8b3b732fb6c", # 1461, 241
    "f8b3b73303e8", # 861, 580
]

background = get_env_background_image()
# scale so that 1px = 1cm
new_size = (int(background.size[0] * env_to_m(100)), int(background.size[1] * env_to_m(100)))
background = background.resize(new_size, Image.LANCZOS)

def get_anchor_positions():
    anchor_positions_in_cm = {}

    for anchor_mac in anchor_macs:
        print("Click at the position of anchor " + anchor_mac)
        
        fig, ax = plt.subplots()
        ax.imshow(background)
        
        for anchor_position in anchor_positions_in_cm.values():
            ax.add_patch(plt.Circle(anchor_position, 10, color='r'))
        
        ax.grid(which='major', linewidth=1.1)
        ax.grid(which='minor', linestyle=':', linewidth=0.7)
        ax.minorticks_on()
        ax.xaxis.set_major_locator(MultipleLocator(base=100))
        ax.yaxis.set_major_locator(MultipleLocator(base=100))
        ax.xaxis.set_minor_locator(MultipleLocator(base=50))
        ax.yaxis.set_minor_locator(MultipleLocator(base=50))
        
        def onclick(event):
            x, y = event.xdata, event.ydata
            print (f'x = {x}, y = {y}')
            anchor_positions_in_cm[anchor_mac] = (x, y)
            plt.close(event.canvas.figure)
        
        cid = fig.canvas.mpl_connect('button_press_event', onclick)
        
        # manager = plt.get_current_fig_manager()
        # manager.full_screen_toggle()
        
        plt.show()
    
    return anchor_positions_in_cm

# anchor_positions_in_cm = get_anchor_positions()
anchor_positions_in_cm = {
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
print(anchor_positions_in_cm)


# RECORD

try:
    nodeSerial = serial.Serial('COM5', 115200, timeout=1)
except:
    print("Error opening serial port")

pattern = re.compile("^([0-9A-Fa-f]{12})_([0-9A-Fa-f]{12}):(-?[0-9]+\.?[0-9]*)\s*$")

def save_csv(filepath, timestamps = [], monitor_macs = [], target_macs = [], rssis = [], anchor_positions_x = [], anchor_positions_y = [], target_positions_x = [], target_positions_y = [], header=False):
    df = pd.DataFrame({
        'timestamp': timestamps,
        'monitor_mac': monitor_macs,
        'target_mac': target_macs,
        'rssi': rssis,
        'anchor_position_x': anchor_positions_x,
        'anchor_position_y': anchor_positions_y,
        'target_position_x': target_positions_x,
        'target_position_y': target_positions_y,
    })

    if header:
        df.to_csv(filepath, mode='w', header=True, index=False)
    else:
        df.to_csv(filepath, mode='a', header=False, index=False)

filename = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
filepath = "./fingerprint_maps/" + filename + ".csv"
save_csv(filepath, header=True)

target_positions = []

try:
    while True:
        print("Click at the position of the target")
        
        fig, ax = plt.subplots()
        ax.imshow(background)
        
        for anchor_position in anchor_positions_in_cm.values():
            ax.add_patch(plt.Circle(anchor_position, 10, color='r'))
        
        for target_position in target_positions:
            ax.add_patch(plt.Circle(target_position, 5, color='g'))
        
        ax.grid(which='major', linewidth=1.1)
        ax.grid(which='minor', linestyle=':', linewidth=0.7)
        ax.minorticks_on()
        ax.xaxis.set_major_locator(MultipleLocator(base=100))
        ax.yaxis.set_major_locator(MultipleLocator(base=100))
        ax.xaxis.set_minor_locator(MultipleLocator(base=50))
        ax.yaxis.set_minor_locator(MultipleLocator(base=50))
        
        def onclick(event):
            x, y = event.xdata, event.ydata
            print (f'x = {x}, y = {y}')
            target_positions.append((x, y))
            print("Collecting samples...")
            
            timestamps = []
            monitor_macs = []
            target_macs = []
            rssis = []
            anchor_positions_x = []
            anchor_positions_y = []
            target_positions_x = []
            target_positions_y = []
            
            # drain the serial port
            nodeSerial.reset_input_buffer()
            
            start_time = time.time()
            timeout = 80 # 30s per measurement
            
            while True:
                if time.time() > start_time + timeout:
                    break
                
                #read data from serial port
                line = nodeSerial.readline()

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
                            anchor_position_x, anchor_position_y = anchor_positions_in_cm[monitor_mac]
                            print("Received: " + str(monitor_mac) + " "  + str(target_mac) + " "  + str(rssi))
                            
                            timestamps.append(timestamp)
                            monitor_macs.append(monitor_mac)
                            target_macs.append(target_mac)
                            rssis.append(rssi)
                            anchor_positions_x.append(anchor_position_x)
                            anchor_positions_y.append(anchor_position_y)
                            target_positions_x.append(x)
                            target_positions_y.append(y)
                        else:
                            print("No match")
                    except Exception as e: 
                        print(e)
                        print("could not decode")
            
            print("Done!")
            plt.close(event.canvas.figure)
            
            save_csv(filepath, timestamps, monitor_macs, target_macs, rssis, anchor_positions_x, anchor_positions_y, target_positions_x, target_positions_y)
        
        cid = fig.canvas.mpl_connect('button_press_event', onclick)
        
        # manager = plt.get_current_fig_manager()
        # manager.full_screen_toggle()
        
        plt.show()
except KeyboardInterrupt:
    print("Done!")
    print("Converting to Pandas Dataframe...")