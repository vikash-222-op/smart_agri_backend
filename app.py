from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# 🔗 MongoDB Atlas Connection (ENV BASED)
mongo_uri = os.environ.get("MONGO_URI")

if not mongo_uri:
    raise Exception("❌ MONGO_URI not set")

client = MongoClient(mongo_uri)
db = client["smart_agri"]
control_collection = db["control"]

if control_collection.count_documents({}) == 0:

    control_collection.insert_one({
        "pump": "OFF",
        "buzzer": "OFF",
        "auto_mode": True
    })

# -------------------------------
# 📩 API 1: Receive ESP32 Data
# -------------------------------
@app.route('/api/data', methods=['POST'])
def receive_data():
    try:
        data = request.json

        print("📩 Received:", data)

        db.sensor_data.insert_one({
            "soil": data['soil'],
            "temp": data['temp'],
            "humidity": data['humidity'],
            "rain": data['rain'],
            "motion": data['motion'],
            "timestamp": datetime.now()
        })

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

    latest = db.sensor_data.find_one(
        sort=[("timestamp", -1)]
    )

    if latest:

        latest["_id"] = str(latest["_id"])

        return jsonify(latest)

    return jsonify({
        "message": "No data found"
    })


# -------------------------------
# 📈 API 3: Historical Data
# -------------------------------
@app.route('/api/history', methods=['GET'])
def get_history():

    data = list(
        db.sensor_data.find()
        .sort("timestamp", -1)
        .limit(50)
    )

    for item in data:
        item["_id"] = str(item["_id"])

    return jsonify(data)

# -------------------------------
# 🎮 API 4: Update Controls
# -------------------------------
@app.route('/api/control', methods=['POST'])
def update_control():

    data = request.json

    control_collection.update_one(
        {},
        {
            "$set": {
                "pump": data.get("pump", "OFF"),
                "buzzer": data.get("buzzer", "OFF"),
                "auto_mode": data.get("auto_mode", True)
            }
        }
    )

    return jsonify({
        "message": "Control updated"
    })


# -------------------------------
# 📡 API 5: Get Controls
# -------------------------------
@app.route('/api/control', methods=['GET'])
def get_control():

    control = control_collection.find_one()

    control["_id"] = str(control["_id"])

    return jsonify(control)

# -------------------------------
# 🧪 TEST API
# -------------------------------
@app.route('/')
def home():
    return "✅ Smart Agriculture Backend Running"


# -------------------------------
# ▶️ RUN SERVER (FIXED)
# -------------------------------
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
