import logging
import json
import os
import numpy as np
import scipy.stats
from numpy.fft import fft
import pyodbc
import requests  
import azure.functions as func
from datetime import datetime, timezone

app = func.FunctionApp()


SQL_CONNECTION_STRING = os.environ.get('SqlConnectionString')
AML_ENDPOINT_URL = os.environ.get('AML_ENDPOINT_URL')
AML_PRIMARY_KEY = os.environ.get('AML_PRIMARY_KEY')

@app.event_hub_message_trigger(
    arg_name="event",  
    event_hub_name="IotEventHubName", 
    connection="IotHubTriggerConnection" 
)
def main(event: func.EventHubEvent):
    logging.info('Python EventHub trigger processed an event.')
    
    body = event.get_body().decode('utf-8')
    logging.info(f'Function triggered by a new batch.')

    try:
        #Feature Generation
        payload = json.loads(body)
        readings = payload['readings']
        device_id = payload.get('deviceId', 'unknown_device')

        if not readings:
            logging.info("Received an empty batch. Exiting.")
            return

        x_axis_data = np.array([r['x'] for r in readings])
        y_axis_data = np.array([r['y'] for r in readings])
        z_axis_data = np.array([r['z'] for r in readings])
        current_time = readings[0]['time']
        current_time = datetime.fromtimestamp(current_time/1000, tz=timezone.utc)

        features_dict = {}
        for axis_name, axis_data in [('x', x_axis_data), ('y', y_axis_data), ('z', z_axis_data)]:
            features_dict[f'{axis_name}_mean'] = np.mean(axis_data)
            features_dict[f'{axis_name}_variance'] = np.var(axis_data)
            features_dict[f'{axis_name}_median'] = np.median(axis_data)
            features_dict[f'{axis_name}_min'] = np.min(axis_data)
            features_dict[f'{axis_name}_max'] = np.max(axis_data)
            features_dict[f'{axis_name}_rms'] = np.sqrt(np.mean(np.square(axis_data)))
            features_dict[f'{axis_name}_skew'] = scipy.stats.skew(axis_data)
            features_dict[f'{axis_name}_Kurtiosis'] = scipy.stats.kurtosis(axis_data)
            
            fft_result = fft(axis_data)
            fft_magnitudes = np.abs(fft_result)
            features_dict[f'{axis_name}_FFT_variance'] = np.var(fft_magnitudes)

        logging.info(f"Successfully created {len(features_dict)} features for device {device_id}")

        #Run inference
        prediction_result = "Error: Model not called" 
        if not AML_ENDPOINT_URL or not AML_PRIMARY_KEY:
            logging.error("Azure ML endpoint URL or Key is not set in application settings.")
        else:
            print(features_dict)
            feature_list_for_model = [float(x) for x in features_dict.values()]
            
            inference_payload = {
                "input_data": {
                    "columns": list(features_dict.keys()),  
                    "index": [0],  
                    "data": [feature_list_for_model] 
                }
            }
            headers = {'Content-Type':'application/json', 'Authorization': f'Bearer {AML_PRIMARY_KEY}'}

            response = requests.post(AML_ENDPOINT_URL, json=inference_payload, headers=headers)
            response.raise_for_status() 

            result = response.json()
           

        #Connect and upload to AZURE SQL
        with pyodbc.connect(SQL_CONNECTION_STRING) as cnxn:
            cursor = cnxn.cursor()
            
            sql_insert_query = """
                INSERT INTO dbo.SoberFeatures (
                    DeviceID, 
                    X_Mean, X_Variance, X_Median, X_Min, X_Max, X_RMS, X_Skew, X_Kurtosis, X_FFT_Variance,
                    Y_Mean, Y_Variance, Y_Median, Y_Min, Y_Max, Y_RMS, Y_Skew, Y_Kurtosis, Y_FFT_Variance,
                    Z_Mean, Z_Variance, Z_Median, Z_Min, Z_Max, Z_RMS, Z_Skew, Z_Kurtosis, Z_FFT_Variance, DataTime, prediction
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?);
            """

            values = (
            device_id,
            features_dict['x_mean'], features_dict['x_variance'], features_dict['x_median'], features_dict['x_min'], features_dict['x_max'], features_dict['x_rms'], features_dict['x_skew'], features_dict['x_Kurtiosis'], features_dict['x_FFT_variance'],
            features_dict['y_mean'], features_dict['y_variance'], features_dict['y_median'], features_dict['y_min'], features_dict['y_max'], features_dict['y_rms'], features_dict['y_skew'], features_dict['y_Kurtiosis'], features_dict['y_FFT_variance'],
            features_dict['z_mean'], features_dict['z_variance'], features_dict['z_median'], features_dict['z_min'], features_dict['z_max'], features_dict['z_rms'], features_dict['z_skew'], features_dict['z_Kurtiosis'], features_dict['z_FFT_variance'], current_time,result[0]
        )

            cursor.execute(sql_insert_query, values)
            cnxn.commit()
            logging.info("Successfully saved all 27 features to the SQL database.")
       
    except Exception as e:
        logging.error(f"An error occurred: {e}", exc_info=True)