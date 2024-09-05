import serial
import time
import re
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
from config import *

# GET ANCHOR POSITIONS

anchor_macs = ["24a1602ccfab", "d8bfc0117c7d", "a4cf12fdaea9"]

fig, ax = plt.subplots()
background = get_env_background_image()
ax.imshow(background)

anchor_positions_in_px = []
current_anchor_idx = 0

def print_prompt():
    global current_anchor_idx
    print("Click at position of anchor " + anchor_macs[current_anchor_idx])

print_prompt()

def onclick(event):
    global anchor_positions_in_px, current_anchor_idx
    x, y = event.xdata, event.ydata
    print (f'x = {x}, y = {y}')
    anchor_positions_in_px.append((x, y))
    current_anchor_idx = current_anchor_idx + 1
    if current_anchor_idx >= len(anchor_macs):
        plt.close(event.canvas.figure)
        return
    print_prompt()

cid = fig.canvas.mpl_connect('button_press_event', onclick)
plt.show()


anchor_positions_in_m = {mac: (env_to_m(x), env_to_m(y)) for (mac, (x, y)) in zip(anchor_macs, anchor_positions_in_px)}
print(anchor_positions_in_px)
print(anchor_positions_in_m)


# RECORD

try:
    nodeSerial = serial.Serial('COM5', 115200, timeout=1)
except:
    print("Error opening serial port")

pattern = re.compile("^([0-9A-Fa-f]{12})_([0-9A-Fa-f]{12}):(-?[0-9]+\.?[0-9]*)$")

timestamps = []
monitor_macs = []
target_macs = []
rssis = []
anchor_positions_x = []
anchor_positions_y = []

try:
    while True:
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
                    anchor_position_x, anchor_position_y = anchor_positions_in_m[monitor_mac]
                    print("Received: " + str(monitor_mac) + " "  + str(target_mac) + " "  + str(rssi))
                    
                    timestamps.append(timestamp)
                    monitor_macs.append(monitor_mac)
                    target_macs.append(target_mac)
                    rssis.append(rssi)
                    anchor_positions_x.append(anchor_position_x)
                    anchor_positions_y.append(anchor_position_y)
                else:
                    print("No match")
            except Exception as e: 
                print(e)
                print("could not decode")
except KeyboardInterrupt:
    print("Done!")
    print("Converting to Pandas Dataframe...")

df = pd.DataFrame({
    'timestamp': timestamps,
    'monitor_mac': monitor_macs,
    'target_mac': target_macs,
    'rssi': rssis,
    'anchor_position_x': anchor_positions_x,
    'anchor_position_y': anchor_positions_y,
})

filename = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
filepath = "./recordings/" + filename

df.to_pickle(filepath + ".pkl")
df.to_csv(filepath + ".csv", index=False)