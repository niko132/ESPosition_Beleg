import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import numpy as np
from PIL import Image

def log_path_loss_model(distance, L0, EXP):
    rssi = L0 - 10.0 * EXP * np.log10(distance)
    return rssi

CONFIG = {
    "2024_09_22_00_07_58_distance_6m_more_detailed.csv": (
        "flat.png",
        lambda background, w, h: background.crop((200, 50, w - 200, h - 180)).transpose(Image.Transpose.ROTATE_90)
    ),
    "2024_09_22_13_52_00_distance_8m_corridor_bedroom.csv": (
        "flat.png",
        lambda background, w, h: background.crop((15, 300, w - 15, h - 200)).transpose(Image.Transpose.ROTATE_180)
    )
}

current_file = "2024_09_22_13_52_00_distance_8m_corridor_bedroom.csv"

filepath = "./calibrations/" + current_file

use_background = current_file in CONFIG
if use_background:
    background_filepath = "./" + CONFIG[current_file][0]
    background_lambda = CONFIG[current_file][1]

    background = Image.open(background_filepath)
    w, h = background.size
    background = background_lambda(background, w, h)


df = pd.read_csv(filepath, index_col=False)
df_mean = df.groupby(['monitor_mac', 'distance'], as_index=False).agg({'rssi':['mean','std']})
df_mean.columns = ['monitor_mac', 'distance', 'rssi_mean', 'rssi_std']
print(df_mean)

df_mean_pivot = df_mean.pivot(index='distance', columns='monitor_mac', values='rssi_mean')
print(df_mean_pivot)

ax = df_mean_pivot.plot.line()

if use_background:
    x0,x1 = ax.get_xlim()
    y0,y1 = ax.get_ylim()
    ax.imshow(background, extent=[x0, x1, y0, y1], aspect='auto')

for idx, monitor_mac in enumerate(df_mean['monitor_mac'].unique()):
    df_monitor_mean = df_mean[df_mean['monitor_mac'] == monitor_mac]
    ax = df_monitor_mean.plot.line(x='distance', y='rssi_mean', yerr='rssi_std', label=monitor_mac, color='C' + str(idx))
    
    distances = df_monitor_mean['distance']
    rssis = df_monitor_mean['rssi_mean']
    
    parameters, covariance = curve_fit(log_path_loss_model, distances, rssis)
    fit_L0 = parameters[0]
    fit_EXP = parameters[1]
    print('Regression params for ' + monitor_mac + ': L0: ' + str(fit_L0) + ' EXP: ' + str(fit_EXP))
    
    X = np.linspace(distances.min(), distances.max(), num = 50)
    Y = log_path_loss_model(X, fit_L0, fit_EXP)
    ax.plot(X, Y, label='regression', color='red')
    ax.legend(loc="upper right")
    
    if use_background:
        x0,x1 = ax.get_xlim()
        y0,y1 = ax.get_ylim()
        ax.imshow(background, extent=[x0, x1, y0, y1], aspect='auto')

plt.show()