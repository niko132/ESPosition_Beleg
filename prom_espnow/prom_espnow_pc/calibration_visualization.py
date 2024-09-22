import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import numpy as np

filepath = "./calibrations/2024_09_22_02_07_16.csv"

df = pd.read_csv(filepath, index_col=False)

monitor_macs = list(df['monitor_mac'].unique())

df_mean = df.groupby(['monitor_mac', 'distance'], as_index=False).agg({'rssi':['mean','std']})
df_mean.columns = ['monitor_mac', 'distance', 'rssi_mean', 'rssi_std']
print(df_mean)

df_mean_pivot = df_mean.pivot(index='distance', columns='monitor_mac', values='rssi_mean')
print(df_mean_pivot)

df_mean_pivot.plot.line()

def log_path_loss_model(distance, L0, EXP):
    rssi = L0 - 10.0 * EXP * np.log10(distance)
    return rssi

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

plt.show()