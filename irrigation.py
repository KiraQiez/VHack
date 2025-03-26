from flask import Flask, render_template, request, jsonify
import requests
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Initialize SQLite Database
def init_db():
    conn = sqlite3.connect('database.db')  # Changed from 'irrigation.db' to 'database.db'
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS irrigation
                 (id INTEGER PRIMARY KEY, date TEXT, water_amount REAL)''')
    conn.commit()
    conn.close()

# Fetch Weather Data from Open-Meteo
def fetch_weather(latitude, longitude):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": "temperature_2m_mean,precipitation_sum,relative_humidity_2m_mean",
        "timezone": "Asia/Kuala_Lumpur"
    }
    response = requests.get(url, params=params)
    data = response.json()
    return data

# Calculate Water Requirement (Simple ET Model)
def calculate_water_requirement(temp, humidity, rainfall, soil_moisture):
    base_water = 5  # Example base value
    temp_factor = temp / 30
    humidity_factor = (100 - humidity) / 100
    rainfall_factor = 1 if rainfall < 2 else 0.5

    water_needed = base_water * temp_factor * humidity_factor * rainfall_factor

    if soil_moisture > 60:
        water_needed *= 0.5
    elif soil_moisture < 30:
        water_needed *= 1.5

    return round(water_needed, 2)

@app.route('/', methods=['GET', 'POST'])
def irrigation():
    water_amount = None
    if request.method == 'POST':
        soil_moisture = float(request.form['soil_moisture'])
        latitude = float(request.form['latitude'])
        longitude = float(request.form['longitude'])

        weather = fetch_weather(latitude, longitude)  # Changed function call to 'fetch_weather'

        # Extract weather data
        temp = weather['daily']['temperature_2m_mean'][0]
        humidity = weather['daily']['relative_humidity_2m_mean'][0]
        rainfall = weather['daily']['precipitation_sum'][0]

        # Calculate water requirement
        water_amount = calculate_water_requirement(temp, humidity, rainfall, soil_moisture)

        # Save to database
        conn = sqlite3.connect('database.db')  # Changed from 'irrigation.db' to 'database.db'
        c = conn.cursor()
        c.execute('INSERT INTO irrigation (date, water_amount) VALUES (?, ?)',
                  (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), water_amount))
        conn.commit()
        conn.close()

    # Fetch recent records
    conn = sqlite3.connect('database.db')  # Changed from 'irrigation.db' to 'database.db'
    c = conn.cursor()
    c.execute('SELECT * FROM irrigation ORDER BY id DESC LIMIT 5')
    records = c.fetchall()
    conn.close()

    return render_template('irrigation.html', water_amount=water_amount, records=records)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
