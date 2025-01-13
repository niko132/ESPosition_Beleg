from abc import ABC, abstractmethod
import numpy as np
import pandas as pd
from scipy.interpolate import Rbf
import os
import re


target_macs = [ 
    "20f094118214", # Pixel
    "342eb61ec446", # P20
    "d81c79de34e1" # iPhone
]

device_names = {
    "20f094118214": "Google Pixel 9 Pro XL",
    "342eb61ec446": "Huawei P20 Pro",
    "d81c79de34e1": "Apple iPhone XR"
}

monitor_macs_esp8266 = [
    "483fda467e7a",
    "d8bfc0117c7d",
    "24a1602ccfab",
    "a4cf12fdaea9",
]

monitor_macs_esp32 = [
    "a0a3b3ff35c0",
    "f8b3b734347c",
    "a0a3b3ff66b4",
    "08a6f7a1e5c8",
    "f8b3b732fb6c",
    "f8b3b73303e8",
]

monitor_macs_esp32_extra = [
    "f8b3b734347c",
    "08a6f7a1e5c8"
]

monitor_macs_all = monitor_macs_esp8266 + monitor_macs_esp32

def filter_esp8266(df):
    return df[df["monitor_mac"].isin(monitor_macs_esp8266)]

def filter_esp32(df):
    return df[df["monitor_mac"].isin(monitor_macs_esp32)]

def filter_common_monitors(df):
    return df[~df["monitor_mac"].isin(monitor_macs_esp32_extra)]


def path_loss_model(distance, rssi_0, n):
    rssi = rssi_0 - 10.0 * n * np.log10(distance)
    return rssi

def inverse_path_loss_model(rssi, rssi_0, n):
    distance = pow(10, ((rssi_0 - rssi) / (10.0 * n)))
    return distance