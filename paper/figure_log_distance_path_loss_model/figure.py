import matplotlib.pyplot as plt
import numpy as np

def log_path_loss_model(distance, L0, EXP):
    rssi = L0 - 10.0 * EXP * np.log10(distance)
    return rssi
    
fit_L0 = -50
fit_EXP = 2.35
    
X = np.linspace(0.1, 10, num = 1000)
Y = log_path_loss_model(X, fit_L0, fit_EXP)
plt.plot(X, Y)

plt.xlim([0, 10])

plt.ylabel("Signal Strength in dB")
plt.xlabel("Distance in m")

plt.grid()

plt.show()