import os
import sys
import time
import json
import pandas as pd 
from azure.iot.device import IoTHubDeviceClient, Message

CONNECTION_STRING = os.environ.get('IoTHubConnectionString')
WINDOW_SIZE_MS = 10000 

def create_client():
    """Create and connect the IoT Hub client."""
    client = IoTHubDeviceClient.create_from_connection_string(CONNECTION_STRING)
    client.connect()
    print('Connected to client')
    return client

def load_and_filter_data(file_path, target_device_id):
    """
    Loads the dataset directly using Pandas, which handles CSVs and headers perfectly,
    and then filters it for a single device ID.
    """
    print(f"Loading data from CSV file: {file_path}...")
    try:
        
        df = pd.read_csv(file_path)
        print(f"Loaded {len(df)} total records.")
        print(f"Filtering for pid: '{target_device_id}'...")
        device_df = df[df['pid'] == target_device_id].copy()

        if device_df.empty:
            print(f"Error: No data found for pid '{target_device_id}'. Please check the ID and the file.")
            sys.exit(1)

        device_df.sort_values(by='time', inplace=True)
        print(f"Found {len(device_df)} records for this device. Starting simulation.")
        return device_df

    except FileNotFoundError:
        print(f"Error: Data file not found at '{file_path}'")
        sys.exit(1)


def run_simulation_from_dataframe(client, dataframe):
    """
    Runs the simulation using a pre-loaded and filtered Pandas DataFrame.
    (This function does not need any changes)
    """
    last_data_timestamp = None
    window_start_timestamp = None
    data_points_batch = []
    count = 0

    for index, row in dataframe.iterrows():
        count += 1
       
        current_timestamp = row['time'] 

        if last_data_timestamp is None:
            last_data_timestamp = current_timestamp
            window_start_timestamp = current_timestamp

        # Simulate time delay
        time_delta_ms = current_timestamp - last_data_timestamp
        if time_delta_ms > 0:
            time.sleep(time_delta_ms/4000.0)

        if current_timestamp - window_start_timestamp >= WINDOW_SIZE_MS:
            if data_points_batch:
                batch_payload = {"deviceId": row['pid'], "readings": data_points_batch} 
                msg_string = json.dumps(batch_payload)
                client.send_message(Message(msg_string))
                print(f"--> Sent batch with {len(data_points_batch)} readings.")
            data_points_batch = []
            window_start_timestamp = current_timestamp

        # Add current reading to the batch
        data_points_batch.append({"x": row['x'], "y": row['y'], "z": row['z'], "time":row['time']})
        last_data_timestamp = current_timestamp
        

    # Send the final batch
    if data_points_batch:
        batch_payload = {"deviceId": dataframe.iloc[-1]['pid'], "readings": data_points_batch} 
        msg_string = json.dumps(batch_payload)
        client.send_message(Message(msg_string))
        print(f"--> Sent final batch with {len(data_points_batch)} readings.")

    print("Finished processing data file.")


if __name__ == '__main__':
    
    data_file = 'all_accelerometer_data_pids_13.csv' #File
    target_id = 'DK3500' #Chosen target

    filtered_df = load_and_filter_data(data_file, target_id)
    
    device_client = create_client()
    try:
        run_simulation_from_dataframe(device_client, filtered_df)
    finally:
        print("Shutting down the client.")
        device_client.shutdown()