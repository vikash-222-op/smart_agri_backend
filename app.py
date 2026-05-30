
from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime
from flask_cors import CORS
import os
import requests

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
    "buzzer": "ON",
    "auto_mode": True
})

BOT_TOKEN = "8737343680:AAGxRyrvaKo2Wx9emSz76k0UZjjKFK1r1G0"
CHAT_ID = "899994439"




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

            "pump_status":
            data.get(
                "pump_status",
                "OFF"
            ),

            "day_mode":
            data.get(
                "day_mode",
                "DAY"
            ),

            "timestamp":
            datetime.now()

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

# =====================
# WEATHER API
# =====================

@app.route('/api/weather', methods=['GET'])
def weather():

    latitude = "25.5941"
    longitude = "85.1376"

    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={latitude}"
        f"&longitude={longitude}"
        "&current="
        "temperature_2m,"
        "relative_humidity_2m,"
        "weather_code,"
        "wind_speed_10m"

        "&hourly="
        "temperature_2m,"
        "precipitation_probability,"
        "weather_code"

        "&daily="
        "weather_code,"
        "temperature_2m_max,"
        "temperature_2m_min,"
        "sunrise,"
        "sunset"

        "&forecast_days=10"
    )

    response = requests.get(url)

    data = response.json()

    return jsonify(data)


# Telegram
def send_telegram(message):

    try:

        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

        payload = {
            "chat_id": CHAT_ID,
            "text": message
        }

        requests.post(url, json=payload)

    except Exception as e:

        print("Telegram Error:", e)

# -------------------------------
# 🎮 API 4: Update Controls
# -------------------------------

@app.route('/api/control', methods=['POST'])
def update_control():

    data = request.json
    update_fields = {}

    if data.get("pump") is not None:
        update_fields["pump"] = data["pump"]

    if data.get("buzzer") is not None:
        update_fields["buzzer"] = data["buzzer"]

    if data.get("auto_mode") is not None:
        update_fields["auto_mode"] = data["auto_mode"]

    control_collection.update_one(
        {},
        {
            "$set": update_fields
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

@app.route('/api/test-telegram')
def test_telegram():

    send_telegram(
        "✅ Telegram Notification System Working"
    )

    return "Telegram Message Sent"

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
