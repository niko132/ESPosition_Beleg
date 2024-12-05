import csv
import matplotlib.pyplot as plt
import numpy as np

def load_data(filename):
    """Load timestamp data from CSV file."""
    timestamps = []
    with open(filename, 'r') as csvfile:
        csvreader = csv.reader(csvfile)
        next(csvreader)  # Skip the header row
        for row in csvreader:
            timestamps.append(float(row[0]))  # Only take the timestamp
    return np.array(timestamps) / 1000000.0

def calculate_inter_packet_times(timestamps):
    """Calculate the inter-packet times (time between consecutive packets)."""
    inter_packet_times = np.diff(timestamps)  # Compute difference between consecutive timestamps
    return inter_packet_times

def plot_histogram(data, label, ax, color):
    """Plot histogram for the inter-packet times on the provided axes (subplot)."""
    min_time = np.min(data)
    max_time = np.max(data)
    
    # Create bin edges with a constant width of 1 second
    # bin_edges = np.arange(min_time, max_time + 1, 1)  # Create bins from min to max time with a width of 1 second
    bin_edges = 30
    
    ax.hist(data, bins=bin_edges, edgecolor='black', alpha=0.7, label=label, color=color)
    ax.set_xlabel('Inter-packet Time (s)', fontsize=14)
    ax.set_ylabel('Number of Packets', fontsize=14)
    # ax.set_title(f'Histogram of Inter-packet Time - {label}')
    # ax.set_xlim([0, 30])  # Set the x-axis range from 0 to 30 seconds
    ax.legend(fontsize=14)

def plot_comparison_histograms(filenames, labels):
    """Load data from multiple files, calculate inter-packet times, and plot histograms in subplots."""
    # Set up subplots
    num_scenarios = len(filenames)
    fig, axes = plt.subplots(1, num_scenarios, figsize=(4 * num_scenarios, 5))
    # fig, axes = plt.subplots(2, 2, figsize=(6, 5))  # 2 rows and 2 columns grid
    # axes = axes.ravel()  # Flatten the axes array for easier indexing
    
    # If there's only one subplot, `axes` is a single axis, not an array, so we make it an array for consistency
    if num_scenarios == 1:
        axes = [axes]
    
    # Set the color cycle across all subplots
    color_cycle = plt.cm.tab10.colors  # You can choose another color map here
    plt.set_cmap('tab10')  # Set the color map for the histograms
    
    # Load data and plot histograms for each scenario
    for i, (filename, label) in enumerate(zip(filenames, labels)):
        timestamps = load_data(filename)
        inter_packet_times = calculate_inter_packet_times(timestamps)
        color = color_cycle[i % len(color_cycle)]  # Cycle through colors
        plot_histogram(inter_packet_times, label, axes[i], color)

    # Adjust layout to prevent overlapping labels
    plt.tight_layout()

def plot_cdf(data, label, ax):
    """Plot the CDF for the inter-packet times on the provided axes."""
    # Sort the data
    sorted_data = np.sort(data)
    
    # Calculate CDF: cumulative count divided by total number of samples
    cdf = np.arange(1, len(sorted_data) + 1) / len(sorted_data)
    
    # Plot the CDF
    ax.plot(sorted_data, cdf, label=label, linewidth=2)
    
    ax.set_xlabel('Inter-packet Time (s)')
    ax.set_ylabel('Cumulative Probability')
    ax.legend()

def plot_comparison_cdfs(filenames, labels):
    """Load data from multiple files, calculate inter-packet times, and plot CDFs."""
    fig, ax = plt.subplots(figsize=(10, 6))

    # Load data and plot CDFs for each scenario
    for filename, label in zip(filenames, labels):
        timestamps = load_data(filename)
        inter_packet_times = calculate_inter_packet_times(timestamps)
        plot_cdf(inter_packet_times, label, ax)

    ax.set_xlim(0, 5)  # Adjust these limits based on your data's range
    ax.set_ylim(0.8, 1)  # The CDF should always be between 0.8 and 1

    plt.title('CDF of Inter-packet Time Comparison')
    plt.tight_layout()

def plot_boxplot(data, label, ax):
    """Plot vertical boxplot for the inter-packet times on the provided axes (subplot)."""
    ax.boxplot(data, vert=True)  # Vertical boxplot
    ax.set_xlabel('Inter-packet Time (s)')
    ax.set_title(f'Boxplot of Inter-packet Time - {label}')
    ax.set_xlim([0, 30])  # Set the x-axis range from 0 to 30 seconds
    ax.grid(True)  # Add a grid to help visualize the boxplots better

def plot_box_plots(filenames, labels):
    """Load data from multiple files, calculate inter-packet times, and plot box plots."""
    num_scenarios = len(filenames)
    fig, axes = plt.subplots(1, num_scenarios, figsize=(6 * num_scenarios, 6))
    
    # If there's only one subplot, `axes` is a single axis, not an array, so we make it an array for consistency
    if num_scenarios == 1:
        axes = [axes]
    
    # Load data and plot boxplots for each scenario
    for i, (filename, label) in enumerate(zip(filenames, labels)):
        timestamps = load_data(filename)
        inter_packet_times = calculate_inter_packet_times(timestamps)
        plot_boxplot(inter_packet_times, label, axes[i])

    # Adjust layout to prevent overlapping labels
    plt.tight_layout()

def print_statistics(inter_packet_times, label):
    """Print important statistics for each scenario."""
    min_time = np.min(inter_packet_times)
    max_time = np.max(inter_packet_times)
    mean_time = np.mean(inter_packet_times)
    median_time = np.median(inter_packet_times)
    total_packets = len(inter_packet_times) + 1  # Total number of packets (including the first one)
    packets_per_second = total_packets / 60  # Total number of packets divided by 60s of recording time
    
    print(f"Statistics for {label}:")
    print(f"  Minimum inter-packet time: {min_time:.4f} seconds")
    print(f"  Maximum inter-packet time: {max_time:.4f} seconds")
    print(f"  Mean inter-packet time: {mean_time:.4f} seconds")
    print(f"  Median inter-packet time: {median_time:.4f} seconds")
    print(f"  Total number of packets: {total_packets}")
    print(f"  Packets per second: {packets_per_second:.4f}\n")

def main():
    # Filenames and labels for different scenarios
    filenames = ['60s_standby_esp32_2.csv', '60s_spotify_esp32_2.csv', '60s_youtube_esp32_2.csv', '60s_ping_esp32_2.csv']  # Replace with your actual filenames
    labels = ['Standby', 'Spotify', 'YouTube', 'Ping']

    # Plot histograms for comparison
    plot_comparison_histograms(filenames, labels)
    
    # Plot CDFs for comparison
    plot_comparison_cdfs(filenames, labels)
    
    # Plot box plots for comparison
    plot_box_plots(filenames, labels)
    
    # Call functions to print statistics
    for filename, label in zip(filenames, labels):
        timestamps = load_data(filename)
        inter_packet_times = calculate_inter_packet_times(timestamps)
        print_statistics(inter_packet_times, label)
    
    plt.show()

if __name__ == '__main__':
    main()