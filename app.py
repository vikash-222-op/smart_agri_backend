from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# 🔗 MongoDB Atlas Connection
client = MongoClient("mongodb+srv://vikash:Vikash%40123@finalproject.x1lkbx3.mongodb.net/?appName=FinalProject")
db = client["smart_agri"]

# -------------------------------
# 📩 API 1: Receive ESP32 Data
# -------------------------------
@app.route('/api/data', methods=['POST'])
def receive_data():
    try:
        data = request.json

        print("📩 Received:", data)

        # Store in database
        db.sensor_data.insert_one({
            "soil": data['soil'],
            "temp": data['temp'],
            "humidity": data['humidity'],
            "rain": data['rain'],
            "motion": data['motion'],
            "timestamp": datetime.now()
        })

        # 🔧 Basic Decision Logic
        if data['rain'] < 2000:
            decision = "PUMP_OFF"
        elif data['soil'] > 2000 or data['temp'] > 30:
            decision = "PUMP_ON"
        else:
            decision = "PUMP_OFF"

        return decision

    except Exception as e:
        return str(e)


# -------------------------------
# 📊 API 2: Latest Data
# -------------------------------
@app.route('/api/latest', methods=['GET'])
def get_latest():
    data = db.sensor_data.find().sort("timestamp", -1).limit(1)
    return jsonify(list(data))


# -------------------------------
# 📈 API 3: Historical Data
# -------------------------------
@app.route('/api/history', methods=['GET'])
def get_history():
    data = db.sensor_data.find().sort("timestamp", -1).limit(50)
    return jsonify(list(data))


# -------------------------------
# 🧪 TEST API
# -------------------------------
@app.route('/')
def home():
    return "✅ Smart Agriculture Backend Running"


# -------------------------------
# ▶️ RUN SERVER
# -------------------------------
if __name__ == '__main__':
    import os

port = int(os.environ.get("PORT", 5000))
app.run(host='0.0.0.0', port=port)
