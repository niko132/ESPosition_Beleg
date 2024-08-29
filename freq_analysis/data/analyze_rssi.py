import pandas as pd
import matplotlib.pyplot as plt

seconds = 60

data = pd.read_csv('./home_standby_60s_3.csv', header=3, encoding_errors='ignore')

min_time_diff = data['RSSI'].min()
max_time_diff = data['RSSI'].max()
mean_time_diff = data['RSSI'].mean()
median_time_diff = data['RSSI'].median()

print("Min: %.2f" % min_time_diff)
print("Max: %.2f" % max_time_diff)
print("Mean: %.2f" % mean_time_diff)
print("Median: %.2f" % median_time_diff)

data.boxplot(column=['RSSI'])
plt.show()