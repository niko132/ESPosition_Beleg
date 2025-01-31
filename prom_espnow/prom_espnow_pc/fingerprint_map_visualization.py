import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import numpy as np
from PIL import Image
from config import *
from matplotlib.ticker import MultipleLocator
import matplotlib.pyplot as pp
from scipy.interpolate import Rbf
import matplotlib.cm as cm
import matplotlib

current_file = "2024_12_12_10_17_51_iPhone_3_filtered.csv"
filepath = "./fingerprint_maps/12_12_24/" + current_file

df = pd.read_csv(filepath, index_col=False)
df_mean = df.groupby(['monitor_mac', 'target_position_x', 'target_position_y', 'anchor_position_x', 'anchor_position_y'], as_index=False).agg({'rssi':['median']})

print(df_mean)


df_mean.columns = ['monitor_mac', 'target_position_x', 'target_position_y', 'anchor_position_x', 'anchor_position_y', 'rssi_median']
print(df_mean)


background = get_env_background_image()
# scale so that 1px = 1cm
new_size = (int(background.size[0] * env_to_m(100)), int(background.size[1] * env_to_m(100)))
background = background.resize(new_size, Image.LANCZOS)

monitor_macs = df_mean['monitor_mac'].unique()
for monitor_mac in monitor_macs:
    monitor_rows = df_mean[df_mean['monitor_mac'] == monitor_mac]

    fig, ax = plt.subplots()
    ax.title.set_text(monitor_mac)
    ax.imshow(background)
        
    anchor_position = (monitor_rows['anchor_position_x'].unique()[0], monitor_rows['anchor_position_y'].unique()[0])
    ax.add_patch(plt.Circle(anchor_position, 10, color='r'))
    
    #for _, monitor_row in monitor_rows.iterrows():
    #    target_position = (monitor_row['target_position_x'], monitor_row['target_position_y'])
    #    ax.add_patch(plt.Circle(target_position, 5, color='g'))
    
    target_positions_x = monitor_rows['target_position_x'].to_list()
    target_positions_y = monitor_rows['target_position_y'].to_list()
    rssi_medians = monitor_rows['rssi_median'].to_list()
    
    
    
    # from https://github.com/jantman/python-wifi-survey-heatmap/blob/master/wifi_survey_heatmap/heatmap.py
    vmin = min(rssi_medians)
    vmax = max(rssi_medians)
    
    num_x = int(background.size[0] / 4)
    num_y = int(background.size[1] / 4)
    x = np.linspace(0, background.size[0], num_x)
    y = np.linspace(0, background.size[1], num_y)
    gx, gy = np.meshgrid(x, y)
    gx, gy = gx.flatten(), gy.flatten()
    
    rbf = Rbf(target_positions_x, target_positions_y, rssi_medians, function='linear')
    z = rbf(gx, gy)
    z = z.reshape((num_y, num_x))
    
    cmap = pp.get_cmap('RdYlBu_r')
    
    # begin color mapping
    norm = matplotlib.colors.Normalize(vmin=vmin, vmax=vmax, clip=True)
    mapper = cm.ScalarMappable(norm=norm, cmap=cmap)
    # end color mapping
    image = ax.imshow(
        z,
        extent=(0, background.size[0], background.size[1], 0),
        alpha=0.5, zorder=100,
        cmap=cmap, vmin=vmin, vmax=vmax
    )
    
    CS = ax.contour(z, colors='k', linewidths=1,
                    extent=(0, background.size[0], background.size[1], 0),
                    alpha=0.3, zorder=150, origin='upper')
    ax.clabel(CS, inline=1, fontsize=6)
    cbar = fig.colorbar(image)
    
    for _, monitor_row in monitor_rows.iterrows():
        target_position = (monitor_row['target_position_x'], monitor_row['target_position_y'])
        rssi_median = monitor_row['rssi_median']
        ax.plot(
            target_position[0], target_position[1], zorder=200,
            marker='o', markeredgecolor='black', markeredgewidth=1,
            markerfacecolor=mapper.to_rgba(rssi_median), markersize=6
        )
    
    
    
        
    ax.grid(which='major', linewidth=1.1)
    ax.grid(which='minor', linestyle=':', linewidth=0.7)
    ax.minorticks_on()
    ax.xaxis.set_major_locator(MultipleLocator(base=100))
    ax.yaxis.set_major_locator(MultipleLocator(base=100))
    ax.xaxis.set_minor_locator(MultipleLocator(base=50))
    ax.yaxis.set_minor_locator(MultipleLocator(base=50))
        
    # manager = plt.get_current_fig_manager()
    # manager.full_screen_toggle()
      
plt.show()