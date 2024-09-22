import serial
import re
import threading
import time
import pandas as pd
from datetime import datetime

try:
    nodeSerial = serial.Serial('COM6', 115200, timeout=1)
except:
    print("Error opening serial port")

pattern = re.compile("^([0-9A-Fa-f]{12})_([0-9A-Fa-f]{12}):(-?[0-9]+\.?[0-9]*)$")

current_distance = None
    
timestamps = []
monitor_macs = []
distances = []
rssis = []

def message_handler_func():
    global current_distance, timestamps, monitor_macs, distances, rssis
    
    while True:
        #read data from serial port
        line = nodeSerial.readline()
        
        if current_distance is None:
            continue # ignore this line

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
                    
                    timestamps.append(timestamp)
                    monitor_macs.append(monitor_mac)
                    distances.append(current_distance)
                    rssis.append(rssi)
                else:
                    print("No match")
            except Exception as e: 
                print(e)
                print("could not decode")

message_thread = threading.Thread(target=message_handler_func, daemon=True)
message_thread.start()

try:
    while True:    
        current_distance = float(input("Current distance to monitor (in m): "))
        input("Input anything to stop")
        current_distance = None
except KeyboardInterrupt:
    print("Done!")
    print("Converting to Pandas Dataframe...")

df = pd.DataFrame({
    'timestamp': timestamps,
    'monitor_mac': monitor_macs,
    'distance': distances,
    'rssi': rssis,
})

filename = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
filepath = "./calibrations/" + filename

df.to_pickle(filepath + ".pkl")
df.to_csv(filepath + ".csv", index=False)