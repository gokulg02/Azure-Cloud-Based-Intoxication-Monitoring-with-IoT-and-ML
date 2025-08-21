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
 
