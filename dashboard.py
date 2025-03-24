from flask import Flask, render_template, session, redirect, url_for, jsonify
import requests
import random

app = Flask(__name__)
app.secret_key = "your_secret_key"

# OpenWeatherMap API Key
WEATHER_API_KEY = "6dc82925be8c87db12b22ab278fc1e93"

# Fetch Weather Data
def fetch_weather(city):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
    response = requests.get(url)
    data = response.json()
    if data.get("main"):
        return {
            "city": city,
            "temperature": data["main"]["temp"],
            "description": data["weather"][0]["description"],
            "icon": data["weather"][0]["icon"]
        }
    return None

@app.route("/")
def index():

    city = "Kuala Lumpur"
    weather_data = fetch_weather(city)
    return render_template("index.html", weather=weather_data)

# API: Weekly Weather Data for Charts
@app.route('/get_weather_data')
def get_weather_data():
    data = {
        "temperature": [random.randint(20, 40) for _ in range(7)],
        "humidity": [random.randint(50, 90) for _ in range(7)],
        "days": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    }
    return jsonify(data)

# API: Farm Locations for Map
@app.route('/get_farm_locations')
def get_farm_locations():
    farms = [
        {"name": "Farm A", "lat": 3.1390, "lng": 101.6869},
        {"name": "Farm B", "lat": 2.7456, "lng": 101.7072},
        {"name": "Farm C", "lat": 1.4927, "lng": 103.7414}
    ]
    return jsonify(farms)

if __name__ == "__main__":
    app.run(debug=True)
