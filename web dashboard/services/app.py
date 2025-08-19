from flask import Flask, request, jsonify
from flask_cors import CORS
import pyodbc
import os


app = Flask(__name__)

CORS(app, resources={r"/*": {"origins": "*"}}) 

# Connection string for SQL server
conn_str = os.getenv("SQL_CONN_STR")
print("Using connection string:", conn_str)

def get_connection():
    return pyodbc.connect(conn_str)


# ---------- API 1: Get all unique DeviceIDs ----------
@app.route('/devices', methods=['GET'])
def get_devices():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT DeviceID FROM [dbo].[SoberFeatures]")
    rows = cursor.fetchall()
    devices = [row[0] for row in rows]
    return jsonify({"devices": devices})


# ---------- API 2: Get predictions for a given DeviceID ----------
@app.route('/predictions', methods=['GET'])
def get_predictions():
    device_id = request.args.get('device_id')
    if not device_id:
        return jsonify({"error": "device_id is required"}), 400
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DataTime, prediction FROM [dbo].[SoberFeatures] WHERE DeviceID = ?", (device_id,))
        rows = cursor.fetchall()
        results = [{"DataTime": str(row[0]), "Prediction": row[1]} for row in rows]
        return jsonify({"device_id": device_id, "predictions": results})
    except Exception as e:
        return jsonify({"error": str(e)})
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    app.run()
