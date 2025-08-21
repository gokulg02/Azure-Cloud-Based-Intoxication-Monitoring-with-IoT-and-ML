# Azure Cloud-Native Platform for ML based Intoxication Detection and Monitoring
This project is a scalable end-to-end machine learning system designed to predict user intoxication levels in real-time using accelerometer data from a smartphone. The entire pipeline is built and deployed on the Azure cloud platform, from data ingestion, model training and model inference to a live monitoring dashboard


## Features
- **ETL Pipeline**: Extracts time-series lag features from IoT device accelerometer data and processes streaming data in Azure.  
- **Machine Learning**: Trained a Random Forest Classifier with 83% accuracy on historical sensor data to predict intoxication using Azure ML studio.  
- **Azure IoT Hub**: Ingests live accelerometer data securely from multiple connected IoT devices.  
- **Azure Functions**: Transforms input data, applies ML model, makes predictions ans stores it on SQL server in real time.  
- **Azure SQL Database**: Stores prediction results for each device.  
- **Web Dashboard**: Interactive UI to monitor intoxication / sobriety status of users in real time.  

## Project Highlights
- End-to-end **Azure Cloud-native** System.
- Fully **serverless and scalable** cloud architecture.  
- **Real-time monitoring** of intoxication levels.  

 ## Demo
 ![demo](sober-demo.gif)
 
## Setup

1.  Pipeline for ETL, feature engineering, and model training data preparation

    -   First, set up Azure Blob Storage to hold the raw and processed data for the training pipeline.
        -   Create an Azure Storage Account in the Azure portal.
        -   Create two Blob Containers: `raw-data` for inputs and `processed-data` for the output.
        -   Upload the training data into the `raw-data` container:
            -   `/raw-data/all_accelerometer_data_pids_13.csv`: The main CSV file with all participant data.
            -   `/raw-data/clean_tac/`: A folder containing the ground truth TAC reading files for each participant.
    -   Next, create the Azure Function project on your local machine using VS Code.
        -   Ensure you have the [Azure Functions](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-azurefunctions) VS Code extension installed.
        -   Use the VS Code Command Palette (`Ctrl+Shift+P`) to run `Azure Functions: Create New Project...` and follow the prompts:

            ```
            Select a folder for your project.
            Select a language: Choose Python.
            Select a Python interpreter to create a virtual environment.
            Select a template: Choose HTTP trigger.
            Provide a function name: e.g., train_model.
            Authorization level: Choose Anonymous.
            ```
        -   Replace the contents of the generated `function_app.py` and `requirements.txt` with the files from the `Training/` directory.
        -   Add your Azure Storage connection string to the `local.settings.json` file:

            ```json
            {
              "IsEncrypted": false,
              "Values": {
                "AzureWebJobsStorage": "Your_connection_string",
                "FUNCTIONS_WORKER_RUNTIME": "python"
              }
            }
            ```
    -   Then, create the Function App resource in Azure which will host the code.
        -   Run `Azure Functions: Create Function App in Azure...` from the Command Palette and follow the prompts:
            ```
            Enter a globally unique name for your Function App.
            Select a runtime stack: Choose the same Python version you used locally.
            Select a region for your resources (e.g., East US).
            ```
    -   Finally, deploy your local function code to the newly created Azure resource.
        -   Run `Azure Functions: Deploy to Function App...` from the Command Palette.
        -   Select the Function App you just created from the list to begin the deployment.


2. Pipeline for capturing live data streaming from IoT device, running ML model to make predictions and storing results in SQL server

    - First, set up Azure IoT Hub to that listens for data from IoT devices.
        - Create an Azure IoT Hub instance in your Azure portal.
        -  Register a new IoT device within your IoT Hub to obtain the connection string.
    - To simulate a real-world IoT device streaming accelerometer data, use a python script.
        -   The `Inference/IoTSimulator/IOT.py` script reads from the training dataset and sends it to your IoT Hub in real-time.
        -   Before running the script, set the `IoTHubConnectionString` environment variable with the connection string for the device you registered in the previous step.
        -   Execute the script on local macine to begin streaming data:

            ```bash
            python Inference/IoTSimulator/IOT.py
            ```
        - Multiple instances of this script can be executed simultaneously to mock multiple IoT devices streaming data.  
    - Next, create an **Azure SQL Server** instance to store the prediction results generated by the pipeline.

        -   After creating the server, connect to it and execute the following SQL query to create the `SoberFeatures` table to store data:

            ```sql
            CREATE TABLE dbo.SoberFeatures (
                ID INT PRIMARY KEY IDENTITY(1,1),
                DeviceID NVARCHAR(50),
                WindowEndTime DATETIME2 DEFAULT GETUTCDATE(),
                X_Mean FLOAT, X_Variance FLOAT, X_Median FLOAT, X_Min FLOAT, X_Max FLOAT, X_RMS FLOAT, X_Skew FLOAT, X_Kurtosis FLOAT, X_FFT_Variance FLOAT,
                Y_Mean FLOAT, Y_Variance FLOAT, Y_Median FLOAT, Y_Min FLOAT, Y_Max FLOAT, Y_RMS FLOAT, Y_Skew FLOAT, Y_Kurtosis FLOAT, Y_FFT_Variance FLOAT,
                Z_Mean FLOAT, Z_Variance FLOAT, Z_Median FLOAT, Z_Min FLOAT, Z_Max FLOAT, Z_RMS FLOAT, Z_Skew FLOAT, Z_Kurtosis FLOAT, Z_FFT_Variance FLOAT,
                DataTime DATETIME2,
                prediction INT
            );
            ```
    - Finally, we create a Azure Function triggered by IoT hub to process the incoming data, run predictions, and store the results.
        -   The code for this function is located in the `Inference/PredictionETLFunctionApp` directory.
        -   This serverless function is triggered by new messages ingested into the IoT Hub. It performs the following actions:
            1. Extracts time-series lag features from the raw accelerometer data.
            2. Calls the ML model endpoint to get an intoxication prediction.
            3. Stores the features and prediction in the Azure SQL database.
        -   After deploying the function app to Azure, you must configure the following environment variables in the function's application settings:
            -   `SqlConnectionString`: The connection string for your Azure SQL database.
            -   `AML_ENDPOINT_URL`: The URL for your deployed machine learning model endpoint.
            -   `AML_PRIMARY_KEY`: The primary key for authenticating with the model endpoint.


3. Deploying the web dashboard:

    - Create a Ubuntu 22.04 VM on Azure cloud with the SSH, HTTP and HTTPS ports exposed.
    - SSH into the VM using `ssh azureuser@<your_vm_public_ip>`
    - Download the deployment script using:
        `curl -o deploy.sh https://raw.githubusercontent.com/gokulg02/Azure-Cloud-Based-Intoxication-Monitoring-with-IoT-and-ML/main/web_dashboard/deploy.sh`
    - Replace the `SQL_CONN_STR` in `deploy.sh` using `nano deploy.sh`.
    - Run the script using:
        ```sh
        chmod +x deploy.sh
        sudo ./deploy.sh
        ```
    - The React front-end will be accesible at `http://<your_azure_vm_ip>`.


 ## Dataset

 - Bar Crawl: Detecting Heavy Drinking. (2020). UCI Machine Learning Repository. https://doi.org/10.24432/C5TK6G.
