import serial
import threading
import csv
import time

# Replace these with your actual serial ports and baud rates
ESP8266_PORT = 'COM7'  # Adjust as needed
ESP32_PORT = 'COM5'    # Adjust as needed
BAUD_RATE = 115200

# Global variables for data storage and control
esp8266_data = []
esp32_data = []
recording = False
start_time = None

def read_from_serial(ser, data_buffer, device_name):
    """Background thread function to read data from a serial port."""
    global recording, start_time
    while True:
        line = ser.readline().decode('utf-8').strip()
        
        if recording:
            try:
                # Assuming the data format is {timestamp}:{rssi}
                timestamp, rssi = line.split(':')
                rssi = int(rssi)  # Convert RSSI to integer
                data_buffer.append((timestamp, rssi))
            except ValueError:
                print(f"Invalid data format received on {device_name}: {line}")
        else:
            print(f"{device_name}: {line}")

def start_serial_reading():
    """Initialize serial connections and start background threads."""
    ser_esp8266 = serial.Serial(ESP8266_PORT, BAUD_RATE)
    ser_esp32 = serial.Serial(ESP32_PORT, BAUD_RATE)
    threading.Thread(target=read_from_serial, args=(ser_esp8266, esp8266_data, "ESP8266"), daemon=True).start()
    threading.Thread(target=read_from_serial, args=(ser_esp32, esp32_data, "ESP32"), daemon=True).start()

def write_to_csv(filename, data):
    """Write recorded data to a CSV file."""
    with open(filename, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(['Timestamp', 'RSSI'])
        csvwriter.writerows(data)

def main():
    global recording, start_time, esp8266_data, esp32_data

    print("Starting data reception...")
    start_serial_reading()

    print("Press Enter to start recording.")
    input()
    recording = True
    print("Recording started. Press Enter to stop.")

    input()
    recording = False
    print("Recording stopped.")

    # Write data to CSV files
    write_to_csv('esp8266_data.csv', esp8266_data)
    write_to_csv('esp32_data.csv', esp32_data)
    print("Data written to 'esp8266_data.csv' and 'esp32_data.csv'.")

if __name__ == '__main__':
    main()