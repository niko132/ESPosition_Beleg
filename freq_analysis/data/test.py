import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import glob

# Group files based on condition
conditions = ['high', 'medium', 'standby']
files_by_condition = {cond: sorted(glob.glob(f'home_{cond}_60s_2.csv')) for cond in conditions}

# Prepare data for histograms
timing_data = {}

for condition, files in files_by_condition.items():
    all_time_diffs = []
    
    for file in files:
        df = pd.read_csv(file, header=3, encoding_errors='ignore')
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        df['time_diff'] = df['Timestamp'].diff().dt.total_seconds()  # Calculate time differences
        all_time_diffs.extend(df['time_diff'].dropna().values)  # Collect all time differences, dropping NaNs
    
    # Store the time differences for each condition
    timing_data[condition] = all_time_diffs

# Plotting combined histograms
plt.figure(figsize=(10, 6))
#bins = 30  # Number of bins for the histograms
bins = np.arange(0, 20, 0.5) / 2000000.0
print(bins)

for condition, time_diffs in timing_data.items():
    plt.hist(time_diffs, bins=bins, alpha=0.5, label=condition, density=True)  # density=True to normalize

plt.xlabel('Time Difference Between Samples (s)')
plt.ylabel('Density')
plt.title('Histogram of Time Differences for Different Conditions')
plt.legend()
plt.show()