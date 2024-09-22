import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from config import *

vis_fig = None
vis_ax = None

graph_fig = None
graph_ax = None
graph_data = {}

def plot_init():
    global vis_fig, vis_ax, graph_fig, graph_ax
    
    plt.ion()

    # Create vis_figure and vis_axes
    vis_fig, vis_ax = plt.subplots()
    
    # Create graph_figure and graph_axes
    graph_fig, graph_ax = plt.subplots()

def plot_monitors(positions):
    background = get_env_background_image()

    # Create vis_figure and vis_axes
    vis_fig, vis_ax = plt.subplots()

    # Display the image
    vis_ax.imshow(background)

    for position in positions:
        # Create a Circle patch
        circle = patches.Circle(position, 10, linewidth=1, edgecolor='r', facecolor='r')

        # Add the patch to the vis_axes
        vis_ax.add_patch(circle)

    plt.show()
    
def plot_results(anchor_positions_in_m, distances_in_m, target_positions_in_m, labels, gt_position_in_m = None):
    global vis_fig, vis_ax
    
    vis_ax.clear()
    
    background = get_env_background_image()

    # Display the image
    vis_ax.imshow(background)

    if anchor_positions_in_m is not None:
        anchor_positions_in_px = [(env_to_px(x), env_to_px(y)) for (x, y) in anchor_positions_in_m]
        for anchor_position in anchor_positions_in_px:
            # Create a Circle patch
            circle = patches.Circle(anchor_position, 10, linewidth=1, edgecolor='r', facecolor='r')

            # Add the patch to the vis_axes
            vis_ax.add_patch(circle)
    
    if anchor_positions_in_m is not None and distances_in_m is not None:
        anchor_positions_in_px = [(env_to_px(x), env_to_px(y)) for (x, y) in anchor_positions_in_m]
        distances_in_px = [env_to_px(dist) for dist in distances_in_m]
        for (anchor_position, distances) in zip(anchor_positions_in_px, distances_in_px):
            # Create a Circle patch
            circle = patches.Circle(anchor_position, distances, linewidth=2, edgecolor='g', fill=False)

            # Add the patch to the vis_axes
            vis_ax.add_patch(circle)
    
    handles = [patches.Patch(facecolor='C' + str(idx), label=label) for idx, label in enumerate(labels)]
    vis_ax.legend(handles=handles)

    if target_positions_in_m is not None:
        for index, target_position_in_m in enumerate(target_positions_in_m):
            target_position_in_px = (env_to_px(target_position_in_m[0]), env_to_px(target_position_in_m[1]))
            
            # Create a Circle patch
            color = 'C' + str(index)
            circle = patches.Circle(target_position_in_px, 10, linewidth=1, edgecolor=color, facecolor=color)

            # Add the patch to the vis_axes
            vis_ax.add_patch(circle)

    if gt_position_in_m is not None:
        gt_position_in_px = (env_to_px(gt_position_in_m[0]), env_to_px(gt_position_in_m[1]))
        
        # Create a Circle patch
        circle = patches.Circle(gt_position_in_px, 10, linewidth=1, edgecolor='y', facecolor='y')

        # Add the patch to the vis_axes
        vis_ax.add_patch(circle)

    vis_fig.canvas.draw()
    vis_fig.canvas.flush_events()

def plot_graph(identifier, new_y):
    global graph_fig, graph_ax, graph_data
    
    if not identifier in graph_data:
        graph_data[identifier] = []
    
    graph_data[identifier].append(new_y)
    
    graph_ax.clear()
    
    x = np.arange(np.max([len(series) for series in graph_data.values()]))
    x = x[-100:]
    for idx, identifier in enumerate(graph_data.keys()):
        values = graph_data[identifier][-100:]
        padding_len = len(x) - len(values)
        if padding_len > 0:
            values = np.pad(values, (padding_len, 0), constant_values=None)
        graph_ax.plot(x, values, color='C'+str(idx))

    graph_fig.canvas.draw()
    graph_fig.canvas.flush_events()