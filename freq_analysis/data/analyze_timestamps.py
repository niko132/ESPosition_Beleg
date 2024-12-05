import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

seconds = 60

for i in range(1, 4):
    data = pd.read_csv('./home_standby_60s_' + str(i) + '.csv', header=3, encoding_errors='ignore')

    number_of_packets = data.shape[0]
    packets_per_second = number_of_packets / seconds

    print("Freq: %.2f P/s" % packets_per_second)

    data['time_diff'] = data.diff()['Timestamp']
    min_time_diff = data['time_diff'].min()
    max_time_diff = data['time_diff'].max()
    mean_time_diff = data['time_diff'].mean()
    median_time_diff = data['time_diff'].median()

    print("Min: %.2f ms" % min_time_diff)
    print("Max: %.2f ms" % max_time_diff)
    print("Mean: %.2f ms" % mean_time_diff)
    print("Median: %.2f ms" % median_time_diff)

    fig, ax = plt.subplots()
    # data.boxplot(column=['time_diff'], ax=ax)
    
    bins = np.arange(0, 20, 0.5)
    
    plt.hist(data['time_diff'].dropna() / 1000.0, bins=bins)  # Adjust bins as needed
    plt.xlabel('Time Difference Between Packets (s)')
    plt.ylabel('Frequency')
    plt.title('Packet Frequency Distribution')
    
    '''
    plt.plot(data.index, data['time_diff'] / 1000.0, label='Inter-Packet Delay')
    plt.xlabel('Packet Index')
    plt.ylabel('Delay (s)')
    plt.title('Inter-Packet Delay Over Time')
    plt.legend()
    '''
    
    '''
    plt.boxplot(data['time_diff'].dropna())
    plt.ylabel('Delay (s)')
    plt.title('Distribution of Packet Delays')
    '''
    
    '''
    plt.scatter(data['Timestamp'].iloc[1:], data['time_diff'].iloc[1:], alpha=0.6)
    plt.xlabel('Timestamp')
    plt.ylabel('Inter-Packet Delay (s)')
    plt.title('Packet Timing Analysis')
    '''
    
plt.show()