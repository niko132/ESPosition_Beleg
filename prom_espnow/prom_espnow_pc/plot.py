import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.pyplot as pp
import matplotlib.animation as animation
import numpy as np
from config import *

vis_fig = None
vis_ax = None

graph_fig = None
graph_ax = None
graph_data = {}


def plot_init():
    global vis_fig, vis_ax, graph_fig, graph_ax
    
    # plt.ion()

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
    
def plot_results(anchor_positions_in_m_dict, distances_in_m_dict, target_positions_in_m, labels, gt_position_in_m = None):
    global vis_fig, vis_ax
    
    anchor_positions_in_m = []
    distances_in_m = []
    
    # TODO: better take the intersection set of rssis mac & anchor_positions mac
    for monitor_mac in anchor_positions_in_m_dict:
        anchor_positions_in_m.append(anchor_positions_in_m_dict[monitor_mac])
        distances_in_m.append(distances_in_m_dict[monitor_mac])
    
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





class RealtimePlotter:
    def __init__(self):
        self.background = get_scaled_env_background_image()
        self.background_width = self.background.size[0]
        self.background_height = self.background.size[1]
        
        self.heatmap_width = int(self.background.size[0] / 4)
        self.heatmap_height = int(self.background.size[1] / 4)
    
        self.cmap = pp.get_cmap('RdYlBu_r')
        
        self.heatmap = np.zeros((self.heatmap_height, self.heatmap_width))
        self.anchor_positions = []
        self.anchor_distances = []
        self.target_estimation = {}
        self.new_data_available = False
    
    def helper_unpack_coordinates(self, coordinate_list):
        if coordinate_list:
            x_coords, y_coords = zip(*coordinate_list)
            return x_coords, y_coords
        else:
            return [], []
    
    def start_plotting(self):
        self.fig, self.ax = plt.subplots()
        
        self.plt_bg = self.ax.imshow(self.background)
        
        def init():
            self.plt_heatmap = self.ax.imshow(self.heatmap,
                alpha=0.3, zorder=100,
                cmap=self.cmap, extent=(0, self.background_width, self.background_height, 0)
            )
            self.plt_anchor_pos, = self.ax.plot([], [], 'bo', markersize=8, zorder=101)
            self.plt_target_pos, = self.ax.plot([], [], 'ro', markersize=8, zorder=102)
            
            self.plt_anchor_dists = [patches.Circle((0.0, 0.0), radius=0.1, fill=False) for _ in range(4)]
            for circle in self.plt_anchor_dists:
                self.ax.add_patch(circle)
            
            self.annotations = [self.ax.annotate('annotation', xy=(0,0), xytext=(0,0), ha='center') for _ in range(3)]
            
            return self.plt_heatmap, self.plt_anchor_pos, self.plt_target_pos, *self.plt_anchor_dists, *self.annotations
        
        def update(frame):
            if self.new_data_available:
                # Update the heatmap and marker with new data
                self.plt_heatmap.set_data(self.heatmap)
                
                anchor_positions_x, anchor_positions_y = self.helper_unpack_coordinates(self.anchor_positions)
                self.plt_anchor_pos.set_data(list(anchor_positions_x), list(anchor_positions_y))
                
                target_estimation_x, target_estimation_y = self.helper_unpack_coordinates(self.target_estimation.values())
                self.plt_target_pos.set_data(list(target_estimation_x), list(target_estimation_y))
                
                for i in range(len(self.anchor_distances)):
                    self.plt_anchor_dists[i].set_center(self.anchor_positions[i])
                    self.plt_anchor_dists[i].set_radius(self.anchor_distances[i])
                
                for i, key in enumerate(self.target_estimation.keys()):
                    self.annotations[i].set_position((self.target_estimation[key][0], self.target_estimation[key][1] - 20))
                    self.annotations[i].set_text(key)
                
                self.new_data_available = False  # Reset the flag

            return self.plt_heatmap, self.plt_anchor_pos, self.plt_target_pos, *self.plt_anchor_dists, *self.annotations
        
        # Use the FuncAnimation with blitting for speedup
        ani = animation.FuncAnimation(self.fig, update, init_func=init, blit=True, interval=20)
        
        plt.show()