import pandas as pd
import matplotlib.pyplot as plt

seconds = 60

data = pd.read_csv('./home_standby_60s_3.csv', header=3, encoding_errors='ignore')

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

data.boxplot(column=['time_diff'])
plt.show()