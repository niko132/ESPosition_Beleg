import csv
import matplotlib.pyplot as plt
import numpy as np

def load_rssi_data(filename):
    """Load RSSI data from a CSV file and normalize timestamps."""
    timestamps = []
    rssi_values = []
    with open(filename, 'r') as csvfile:
        csvreader = csv.reader(csvfile)
        next(csvreader)  # Skip the header row
        for row in csvreader:
            timestamps.append(float(row[0]) / 1000000.0)  # Load timestamp
            rssi_values.append(float(row[1]))  # Load RSSI value
    
    # Normalize timestamps to start at 0
    start_time = timestamps[0]
    normalized_timestamps = [t - start_time for t in timestamps]
    return normalized_timestamps, rssi_values

def plot_combined_graph(fig, ax1, ax2, timestamps1, rssi_values1, timestamps2, rssi_values2, label1, label2):
    """Plot a combined line graph of RSSI values over time."""
    ax1.plot(timestamps1, rssi_values1, marker='o', linestyle='-', markersize=2, alpha=0.7, label=label1)
    ax1.plot(timestamps2, rssi_values2, marker='o', linestyle='-', markersize=2, alpha=0.7, label=label2)
    ax1.set_title('RSSI over Time', fontsize=14)
    ax1.set_xlabel('Time (s)', fontsize=14)
    ax1.set_ylabel('RSSI (dBm)', fontsize=14)
    ax1.legend()
    ax1.grid(True)

def plot_combined_boxplot(fig, ax2, rssi_values1, rssi_values2, label1, label2):
    """Plot a combined box plot comparing RSSI variability with default colors and a distinct median line color."""
    # Create the box plot
    box = ax2.boxplot(
        [rssi_values1, rssi_values2],
        tick_labels=[label1, label2],
        patch_artist=True,
        vert=True
    )
    
    # Get colors from the default Matplotlib color cycle
    color_cycle = plt.rcParams['axes.prop_cycle'].by_key()['color']
    colors = [color_cycle[0], color_cycle[1]]  # Use first two colors from the default cycle

    # Apply colors to each box with distinct edge and fill properties
    for patch, color in zip(box['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_edgecolor('black')  # Ensure the edges are visible
        patch.set_alpha(0.7)         # Slight transparency for clarity

    # Set median line properties to make it pop (e.g., red color)
    for median in box['medians']:
        median.set_color('red')
        median.set_linewidth(2)

    # Ensure whiskers and caps are visible
    for whisker in box['whiskers']:
        whisker.set_color('black')
        whisker.set_linewidth(1.2)
    for cap in box['caps']:
        cap.set_color('black')
        cap.set_linewidth(1.2)

    ax2.set_title('RSSI Variability', fontsize=14)
    ax2.set_ylabel('RSSI (dBm)', fontsize=14)
    ax2.grid(True)

def print_statistics(rssi_values, label):
    """Print statistical information about the RSSI values, including relevant percentiles."""
    rssi_values = np.array(rssi_values)
    mean_rssi = np.mean(rssi_values)
    std_rssi = np.std(rssi_values)
    min_rssi = np.min(rssi_values)
    max_rssi = np.max(rssi_values)
    median_rssi = np.percentile(rssi_values, 50)  # 50th percentile (median)
    lower_quartile = np.percentile(rssi_values, 25)  # 25th percentile
    upper_quartile = np.percentile(rssi_values, 75)  # 75th percentile
    median_percentage = (np.sum(rssi_values == median_rssi) / rssi_values.size) * 100
    
    print(f"Statistics for {label}:")
    print(f"  Mean RSSI: {mean_rssi:.2f} dBm")
    print(f"  Standard Deviation of RSSI: {std_rssi:.2f} dBm")
    print(f"  Min RSSI: {min_rssi:.2f} dBm")
    print(f"  Max RSSI: {max_rssi:.2f} dBm")
    print(f"  Median (50th Percentile): {median_rssi:.2f} dBm")
    print(f"  25th Percentile (Lower Quartile): {lower_quartile:.2f} dBm")
    print(f"  75th Percentile (Upper Quartile): {upper_quartile:.2f} dBm")
    print(f"  Percentage of Median values: {median_percentage:.2f} %")
    print(f"  Number of Packets: {len(rssi_values)}")    
    print()

def main():
    # Replace with your actual CSV filenames
    filename1 = 'esp32_data.csv'
    filename2 = 'esp8266_data.csv'

    # Load data for both scenarios
    timestamps1, rssi_values1 = load_rssi_data(filename1)
    timestamps2, rssi_values2 = load_rssi_data(filename2)

    # Print statistics for both scenarios
    print_statistics(rssi_values1, 'ESP32')
    print_statistics(rssi_values2, 'ESP8266')

    # Create a figure with specific size
    fig = plt.figure(figsize=(12, 6))

    # Define the gridspec layout for 2/3 for line plot and 1/3 for box plot
    gs = fig.add_gridspec(1, 3, width_ratios=[2, 1, 0])  # 2 parts for the line plot, 1 part for the box plot

    # Create axes for the line plot
    ax1 = fig.add_subplot(gs[0])

    # Create axes for the box plot
    ax2 = fig.add_subplot(gs[1])

    # Plot line graph
    plot_combined_graph(fig, ax1, ax2, timestamps1, rssi_values1, timestamps2, rssi_values2, 'ESP32', 'ESP8266')

    # Plot box plot
    plot_combined_boxplot(fig, ax2, rssi_values1, rssi_values2, 'ESP32', 'ESP8266')

    # Show the combined figure
    plt.tight_layout()
    plt.show()

if __name__ == '__main__':
    main()
