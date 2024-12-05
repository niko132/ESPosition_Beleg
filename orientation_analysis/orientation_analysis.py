import matplotlib.pyplot as plt
import pandas as pd
import glob
import re
import numpy as np
from math import pi

def read_and_normalize_csv(file_path):
    """Read CSV file, normalize timestamps to start at 0, and return time and RSSI data."""
    data = pd.read_csv(file_path, delimiter=",")
    data.columns = ["Timestamp", "RSSI"]
    data["Timestamp"] = data["Timestamp"] / 1000000.0   # Convert to seconds
    data["Timestamp"] -= data["Timestamp"].min()  # Normalize timestamp to start at 0
    return data["Timestamp"], data["RSSI"]

def extract_direction_angle(file_name):
    """Extract direction and angle from the file name using regex."""
    match = re.search(r'(\w+?)([0-9]+)_(esp32|esp8266)\.csv', file_name)
    if match:
        direction, angle, microcontroller = match.groups()
        return direction, int(angle), microcontroller
    return "Unknown", 0, "Unknown"

def calculate_rssi_stats(csv_files):
    """Calculate median RSSI for each combination of microcontroller, direction, and angle and store in a DataFrame."""
    rssi_data = []

    for file_path in csv_files:
        direction, angle, microcontroller = extract_direction_angle(file_path.split("/")[-1])
        _, rssi = read_and_normalize_csv(file_path)
        median = np.median(rssi)
        
        rssi_data.append({
            "Microcontroller": microcontroller,
            "Direction": direction,
            "Angle": angle,
            "Median RSSI": median
        })
    
    # Convert to DataFrame
    rssi_df = pd.DataFrame(rssi_data)
    
    # Sort by Microcontroller, Direction, and Angle
    rssi_df = rssi_df.sort_values(by=["Microcontroller", "Direction", "Angle"])
    
    # Print the median RSSI values, now sorted
    print(f"\n{'Microcontroller':<10} {'Direction':<10} {'Angle':<5} {'Median RSSI':<10}")
    print("-" * 40)
    print(rssi_df.to_string(index=False))
    
    return rssi_df

def calculate_std_devs(rssi_df):
    """Calculate the standard deviation of the medians for each microcontroller and direction."""
    # Calculate standard deviation by grouping by microcontroller and direction
    grouped = rssi_df.groupby(['Microcontroller', 'Direction'])['Median RSSI']
    stats_df = grouped.agg(
        mean='mean',
        std=lambda x: x.std(ddof=0)  # Ensure ddof=0 for population std
    ).reset_index()
    
    # Rename columns for clarity
    stats_df.rename(columns={'mean': 'Mean of Median RSSI', 'std': 'Std Dev of Median RSSI'}, inplace=True)
    
    # Print mean and standard deviation values
    print(f"\n{'Microcontroller':<15} {'Direction':<15} {'Mean of Median RSSI':<20} {'Std Dev of Median RSSI':<20}")
    print("-" * 70)
    print(stats_df.to_string(index=False))

def plot_radar_chart(rssi_df):
    """Plot a combined radar chart for both microcontrollers using the median RSSI values."""
    # Prepare data for radar chart
    directions_list = sorted(rssi_df['Direction'].unique())  # Get unique directions
    angles_list = sorted(rssi_df['Angle'].unique())  # Get unique angles
    
    categories = [f"{direction} - {angle}°" for direction in directions_list for angle in angles_list]
    esp32_values = [abs(rssi_df[(rssi_df['Microcontroller'] == 'esp32') & (rssi_df['Direction'] == direction) & (rssi_df['Angle'] == angle)]['Median RSSI'].values[0]) for direction in directions_list for angle in angles_list]
    esp8266_values = [abs(rssi_df[(rssi_df['Microcontroller'] == 'esp8266') & (rssi_df['Direction'] == direction) & (rssi_df['Angle'] == angle)]['Median RSSI'].values[0]) for direction in directions_list for angle in angles_list]
    
    # Number of variables (directions and angles)
    num_vars = len(categories)
    
    # Set up the radar chart
    angles = [n / float(num_vars) * 2 * pi for n in range(num_vars)]
    esp32_values += esp32_values[:1]  # Close the circle for esp32
    esp8266_values += esp8266_values[:1]  # Close the circle for esp8266
    angles += angles[:1]  # Close the circle

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    ax.set_theta_offset(pi / 2)
    ax.set_theta_direction(-1)
    
    # Plot both microcontrollers
    ax.plot(angles, esp32_values, linewidth=2, linestyle='solid', label="ESP32")
    ax.fill(angles, esp32_values, alpha=0.4)
    
    ax.plot(angles, esp8266_values, linewidth=2, linestyle='solid', label="ESP8266", color='orange')
    ax.fill(angles, esp8266_values, alpha=0.4, color='orange')

    # Labels for each axis
    ax.set_yticklabels([])  # Remove radial ticks
    ax.set_xticks(angles[:-1])  # Remove the last duplicate angle
    ax.set_xticklabels(categories, fontsize=10, rotation=45, ha="center")
    ax.xaxis.set_tick_params(pad=20)

    ax.set_title("Median RSSI (Absolute) for ESP32 and ESP8266 - Radar Chart", size=16, y=1.1)

    ax.legend(loc='upper right', bbox_to_anchor=(1.1, 1.0), fontsize=12)

    # Show the chart
    plt.tight_layout()

def plot_orientation_experiment(csv_files):
    """Plot a grid of subplots showing RSSI values over time for different orientations and microcontrollers."""
    # Group files by direction and angle
    file_groups = {}
    for file_path in csv_files:
        direction, angle, microcontroller = extract_direction_angle(file_path.split("/")[-1])
        key = (direction, angle)
        if key not in file_groups:
            file_groups[key] = {}
        file_groups[key][microcontroller] = file_path

    fig, axes = plt.subplots(3, 4, figsize=(18, 10), sharey=True)
    fig.suptitle('RSSI over Time for Different Directions and Angles', fontsize=16)
    axes = axes.flatten()

    for idx, ((direction, angle), mc_files) in enumerate(sorted(file_groups.items())):
        ax = axes[idx]
        for microcontroller, file_path in mc_files.items():
            timestamp, rssi = read_and_normalize_csv(file_path)
            file_label = f"{microcontroller.upper()}"
            ax.plot(timestamp, rssi, label=file_label, lw=1.5, alpha=0.8)

        ax.set_title(f"{direction} - {angle}°", fontsize=12)
        ax.set_xlabel('Time (s)', fontsize=10)
        ax.set_ylabel('RSSI (dBm)', fontsize=10)
        ax.grid(True)
        ax.legend(loc='lower right', fontsize=8)

    # Hide any unused subplots
    for i in range(len(file_groups), len(axes)):
        fig.delaxes(axes[i])

    plt.tight_layout(rect=[0, 0, 1, 0.95])  # Adjust layout to fit title

def plot_median_rssi_separate_bar_charts(rssi_df):
    """Plot separate bar charts for the ESP8266 and ESP32 showing median RSSI grouped by direction and angle."""
    # Prepare data for the bar charts
    directions = sorted(rssi_df['Direction'].unique())  # Unique directions
    angles = sorted(rssi_df['Angle'].unique())  # Unique angles
    microcontrollers = ['esp32', 'esp8266']  # Microcontrollers

    # Set up plots
    fig, axes = plt.subplots(1, 2, figsize=(14, 6), sharey=True)
    colors = plt.cm.tab10(np.linspace(0, 1, len(angles)))  # Generate distinct colors for angles

    for ax, mc in zip(axes, microcontrollers):
        # Filter data for the current microcontroller
        mc_data = rssi_df[rssi_df['Microcontroller'] == mc]
        
        # Grouped positions for bars
        x_indices = np.arange(len(directions))  # X-axis positions for the first group
        bar_width = 0.2
        
        # Plot bars for each angle
        for i, angle in enumerate(angles):
            values = [
                mc_data[(mc_data['Direction'] == direction) & 
                        (mc_data['Angle'] == angle)]['Median RSSI'].mean()
                for direction in directions
            ]
            
            # Offset bars by angle index
            ax.bar(x_indices + i * bar_width, values, bar_width, label=f"{angle}°", color=colors[i])
        
        # Configure the plot
        ax.set_title(f"Median RSSI for {mc.upper()}", fontsize=14)
        ax.set_xticks(x_indices + (len(angles) - 1) * bar_width / 2)
        ax.set_xticklabels(directions, fontsize=10)
        ax.set_xlabel("Direction", fontsize=12)
        ax.grid(axis='y', linestyle='--', alpha=0.7)
        ax.legend(title="Angle", fontsize=10, loc="upper left", bbox_to_anchor=(1.02, 1))
        if mc == 'esp8266':
            ax.set_ylabel("Median RSSI", fontsize=12)

    # Adjust layout
    plt.tight_layout()

if __name__ == "__main__":
    # Assuming all files match the pattern 'direction_angle_esp32.csv' or 'direction_angle_esp8266.csv'
    csv_files = sorted(glob.glob("*_esp32.csv") + glob.glob("*_esp8266.csv"))
    
    # Calculate and store RSSI stats in a DataFrame
    rssi_df = calculate_rssi_stats(csv_files)
    
    # Calculate and print the standard deviation of the medians
    calculate_std_devs(rssi_df)
    
    # Plot the radar chart for both microcontrollers combined
    plot_radar_chart(rssi_df)
    
    plot_median_rssi_separate_bar_charts(rssi_df)
    
    # Plot the orientation experiment with line graphs
    plot_orientation_experiment(csv_files)
    
    plt.show()
