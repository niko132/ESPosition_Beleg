import pandas as pd

def analyze_csv(file_path):
    # Read the CSV file
    df = pd.read_csv(file_path)

    # Extract unique target positions and their counts
    unique_positions = df.groupby(['target_position_x', 'target_position_y']).size()

    # Print unique positions and counts
    print("Unique (target_position_x, target_position_y) and their counts:")
    for position, count in unique_positions.items():
        print(f"Position: {position}, Count: {count}")

# Specify the path to your CSV file
csv_file_path = "2024_12_11_14_11_25.csv"

# Call the function to analyze the CSV
analyze_csv(csv_file_path)