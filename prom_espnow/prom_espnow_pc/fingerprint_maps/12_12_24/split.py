import pandas as pd
import sys

mac_esp8266 = {
    "483fda467e7a",
    "d8bfc0117c7d",
    "24a1602ccfab",
    "a4cf12fdaea9"
}

mac_esp32 = {
    "a0a3b3ff35c0",
    "f8b3b734347c",
    "a0a3b3ff66b4",
    "08a6f7a1e5c8",
    "f8b3b732fb6c",
    "f8b3b73303e8"
}

def split_csv(filename):
    try:
        # Read the CSV file into a DataFrame
        df = pd.read_csv(filename)

        # Validate required column exists
        if 'monitor_mac' not in df.columns:
            raise KeyError("monitor_mac column is missing in the input file.")

        # Split the DataFrame based on the monitor_mac column
        df_esp8266 = df[df['monitor_mac'].isin(mac_esp8266)]
        df_esp32 = df[df['monitor_mac'].isin(mac_esp32)]
        
        # Remove .csv from the original filename for new file names
        base_name = filename.rsplit('.csv', 1)[0]

        # Create output file names
        file_esp8266 = f"{base_name}_esp8266.csv"
        file_esp32 = f"{base_name}_esp32.csv"

        # Save the resulting DataFrames to new CSV files
        df_esp8266.to_csv(file_esp8266, index=False)
        df_esp32.to_csv(file_esp32, index=False)

        print(f"File successfully split into '{file_esp8266}' and '{file_esp32}'")
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
    except KeyError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python split_csv.py <filename>")
        sys.exit(1)

    input_filename = sys.argv[1]
    split_csv(input_filename)
