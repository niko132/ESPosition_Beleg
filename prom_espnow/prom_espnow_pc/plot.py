import matplotlib.pyplot as plt
import matplotlib.patches as patches
from config import *

fig = None
ax = None

def plot_init():
    global fig, ax
    
    plt.ion()

    # Create figure and axes
    fig, ax = plt.subplots()

def plot_monitors(positions):
    background = get_env_background_image()

    # Create figure and axes
    fig, ax = plt.subplots()

    # Display the image
    ax.imshow(background)

    for position in positions:
        # Create a Circle patch
        circle = patches.Circle(position, 10, linewidth=1, edgecolor='r', facecolor='r')

        # Add the patch to the Axes
        ax.add_patch(circle)

    plt.show()
    
def plot_results(anchor_positions_in_m, distances_in_m, target_position_in_m, gt_position_in_m = None):
    global fig, ax
    
    ax.clear()
    
    background = get_env_background_image()

    # Display the image
    ax.imshow(background)

    if anchor_positions_in_m is not None:
        anchor_positions_in_px = [(env_to_px(x), env_to_px(y)) for (x, y) in anchor_positions_in_m]
        for anchor_position in anchor_positions_in_px:
            # Create a Circle patch
            circle = patches.Circle(anchor_position, 10, linewidth=1, edgecolor='r', facecolor='r')

            # Add the patch to the Axes
            ax.add_patch(circle)
    
    if anchor_positions_in_m is not None and distances_in_m is not None:
        anchor_positions_in_px = [(env_to_px(x), env_to_px(y)) for (x, y) in anchor_positions_in_m]
        distances_in_px = [env_to_px(dist) for dist in distances_in_m]
        for (anchor_position, distances) in zip(anchor_positions_in_px, distances_in_px):
            # Create a Circle patch
            circle = patches.Circle(anchor_position, distances, linewidth=2, edgecolor='g', fill=False)

            # Add the patch to the Axes
            ax.add_patch(circle)

    if target_position_in_m is not None:
        target_position_in_px = (env_to_px(target_position_in_m[0]), env_to_px(target_position_in_m[1]))
        
        # Create a Circle patch
        circle = patches.Circle(target_position_in_px, 10, linewidth=1, edgecolor='b', facecolor='b')

        # Add the patch to the Axes
        ax.add_patch(circle)

    if gt_position_in_m is not None:
        gt_position_in_px = (env_to_px(gt_position_in_m[0]), env_to_px(gt_position_in_m[1]))
        
        # Create a Circle patch
        circle = patches.Circle(gt_position_in_px, 10, linewidth=1, edgecolor='y', facecolor='y')

        # Add the patch to the Axes
        ax.add_patch(circle)

    fig.canvas.draw()
    fig.canvas.flush_events()