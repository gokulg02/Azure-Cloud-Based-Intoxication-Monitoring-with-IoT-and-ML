import azure.functions as func
import logging
import pandas as pd
import numpy as np
import scipy
import os
from azure.storage.blob import BlobServiceClient

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

BLOB_CONN_STR = os.environ["AzureWebJobsStorage"]
#Container names in Azure
INPUT_CONTAINER = "raw-data"
TAC_FOLDER = "clean_tac"
OUTPUT_CONTAINER = "processed-data"

@app.route(route="train_model")
def train_model(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Training pipeline triggered.")

    try:
        
        blob_service_client = BlobServiceClient.from_connection_string(BLOB_CONN_STR)
        logging.info("Conn. Success.")

        accel_blob = blob_service_client.get_blob_client(INPUT_CONTAINER, "all_accelerometer_data_pids_13.csv")
        accel_data = accel_blob.download_blob().readall()
        df = pd.read_csv(pd.io.common.BytesIO(accel_data))
        logging.info("Data Loaded")

        df = df.drop(df.index[df["time"] == 0])

        funcs = [
            ('mean', np.mean), ('variance', np.var), ('median', np.median),
            ('min', np.min), ('max', np.max),
            ('rms', lambda x: np.sqrt(np.mean(np.square(x)))),
            ('skew', scipy.stats.skew), ('Kurtiosis', scipy.stats.kurtosis)
        ]
        fft_funcs = [('variance', np.var)]
        cols = ['x', 'y', 'z']
        t = 10
        window_size_ms = t * 1000

        # Windowing
        df['t_win'] = ((df['time'] // window_size_ms) * window_size_ms) // 1000
        look_up_frames = {}
        logging.info("t_win calc.")

        for pid in df.pid.unique():
            rf = pd.DataFrame()
            grouped = df[df.pid == pid].groupby('t_win')
            for col in cols:
                col_array = grouped[col].apply(np.array)
                col_fft = col_array.apply(scipy.fft.fft)
                for key, func in funcs:
                    rf['_'.join([col, key])] = col_array.apply(func)
                for key, func in fft_funcs:
                    rf['_'.join([col, 'FFT', key])] = col_fft.apply(func)
            rf.pid = pid
            look_up_frames[pid] = rf
        logging.info("Feature Extraction")

        tac_dict = {}
        tac_container_client = blob_service_client.get_container_client(INPUT_CONTAINER)  # same container

        for blob in tac_container_client.list_blobs(name_starts_with=f"{TAC_FOLDER}/"):
            tac_blob = blob_service_client.get_blob_client(INPUT_CONTAINER, blob.name)
            tac_df = pd.read_csv(pd.io.common.BytesIO(tac_blob.download_blob().readall()))
            filename = blob.name.split('/')[-1]
            tac_dict[filename.split('_')[0]] = tac_df

        logging.info("TAC Data loaded")

        def get_y(pid, t):
            ind = np.argmax(tac_dict[pid]['timestamp'] > t)
            if ind != 0:
                ind -= 1
            tac = tac_dict[pid].iloc[[ind]]['TAC_Reading'].values[0]
            return 1 if tac > 0.08 else 0

        #Label windows
        for pid in df.pid.unique():
            look_up_frames[pid]['t'] = look_up_frames[pid].index.astype(int)
            look_up_frames[pid]['pid'] = pid
            look_up_frames[pid]['drunk'] = [
                get_y(pid, ts) for ts in look_up_frames[pid]['t']
            ]
        logging.info("Merge done")

        combined_df = pd.concat(look_up_frames.values(), ignore_index=True)
        output_blob = blob_service_client.get_blob_client(OUTPUT_CONTAINER, "clean_data_new.csv")
        output_blob.upload_blob(combined_df.to_csv(index=False), overwrite=True)

        logging.info("Training pipeline completed successfully.")
        return func.HttpResponse("Training completed and data saved.", status_code=200)

    except Exception as e:
        logging.error(f"Error during training: {str(e)}")
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)
