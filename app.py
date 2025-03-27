# ----------------- Your Original app.py Code -----------------
from flask import Flask, render_template, request, jsonify
import requests
import google.generativeai as genai

app = Flask(__name__)
app.secret_key = "your_secret_key"

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

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/analytics")
def analytics():
    return render_template("analytics.html")

@app.route("/weather")
def weather():
    return render_template("weather.html")

@app.route("/chatbot")
def chatbot():
    return render_template("chatbot.html")

@app.route("/crop")
def crop():
    return render_template("crop.html")

@app.route("/irrigation")
def irrigation():
    return render_template("irrigation.html")


# API: Weekly Weather Data for Charts
@app.route('/get_weather_data')
def get_weather_data():
    latitude = request.args.get("lat", 3.1390, type=float)
    longitude = request.args.get("lng", 101.6869, type=float)

    print(f"[DEBUG] Fetching weather data for lat={latitude}, lng={longitude}")  # Debugging
    weather_data = fetch_weather(latitude, longitude)
    
    return jsonify(weather_data)

@app.route('/get_farm_locations')
def get_farm_locations():
    state = request.args.get("state")  # Get state name from frontend
    if not state:
        return jsonify({"error": "State name is required"}), 400

    osm_url = "http://overpass-api.de/api/interpreter"

    # **Query to get all farmland in the specified state**
    query = f"""
    [out:json][timeout:50];
    area["name"="{state}"]->.state;
    (
      node["landuse"="farmland"](area.state);
      way["landuse"="farmland"](area.state);
      relation["landuse"="farmland"](area.state);
      
      node["farmer"="yes"](area.state);
      way["farmer"="yes"](area.state);
      
      node["agriculture"="yes"](area.state);
      way["agriculture"="yes"](area.state);
    );
    out center;
    """

    response = requests.get(osm_url, params={"data": query})

    try:
        data = response.json()
    except requests.exceptions.JSONDecodeError:
        return jsonify({"error": "Invalid JSON response from OSM"}), 500

    farms = []
    for element in data.get("elements", []):
        if "lat" in element and "lon" in element:
            farms.append({
                "name": element.get("tags", {}).get("name", "Unnamed Farm"),
                "lat": element["lat"],
                "lng": element["lon"]
            })
        elif "center" in element:
            farms.append({
                "name": element.get("tags", {}).get("name", "Unnamed Farm"),
                "lat": element["center"]["lat"],
                "lng": element["center"]["lon"]
            })

    print(f"[DEBUG] Farms found in {state}:", farms)  # Debugging Output

    if not farms:
        return jsonify({"error": f"No farms found in {state}"}), 404

    return jsonify(farms)

# Set up Google Gemini API Key
GEMINI_API_KEY = "AIzaSyCCMqub_m4O8umGE_Rw_iuGIDkxPBl7QKE"
genai.configure(api_key=GEMINI_API_KEY)

# Correct model name (Check from list_models output)
MODEL_NAME = "gemini-1.5-flash-latest"  # Change based on available models

# Function to interact with Gemini AI
def get_agriculture_response(user_input):
    try:
        model = genai.GenerativeModel(MODEL_NAME)  # Use correct model
        response = model.generate_content(user_input)  # Generate response
        return response.text  # Extract text response
    except Exception as e:
        print("[ERROR] Gemini API Request Failed:", str(e))
        return f"Error: {str(e)}"

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message")
    response = get_agriculture_response(user_message)
    return jsonify({"reply": response})

# ----------------- Irrigation Guidance Code (Appended) -----------------

@app.route("/get_irrigation")
def get_irrigation():
    location = request.args.get("location")
    crop = request.args.get("crop")
    soil = request.args.get("soil")

    if not location:
        return jsonify({"error": "Location is required"}), 400

    lat, lng = map(float, location.split(","))  # Get coordinates

    # Fetch real weather data
    weather_data = fetch_weather(lat, lng)

    if 'daily' not in weather_data:
        return jsonify({"error": "Failed to fetch weather data"}), 500

    precipitation = weather_data['daily']['precipitation_sum'][0]
    water_amount = max(0, 20 - precipitation)  # 20 mm base water need
    is_rain = precipitation > 1

    response = {
        "location": f"{lat}, {lng}",
        "crop": crop,
        "soil": soil,
        "water_amount": round(water_amount, 2),
        "rain": is_rain
    }
    return jsonify(response)

# Function to calculate irrigation needs
def calculate_irrigation(weather_data, crop_type):
    crop_water_needs = {
        "Rice": 7,
        "Corn": 5,
        "Wheat": 4
    }
    water_need = crop_water_needs.get(crop_type, 5)

    # Extract weather details
    precipitation = weather_data['daily']['precipitation_sum'][0]
    temperature = weather_data['daily']['temperature_2m_mean'][0]
    humidity = weather_data['daily']['relative_humidity_2m_mean'][0]

    # Soil moisture estimation (simplified)
    estimated_soil_moisture = max(0, (humidity / 100) * (100 - temperature))  

    # Water to apply = water need - (rainfall + soil moisture contribution)
    water_to_apply = max(0, water_need - (precipitation + (estimated_soil_moisture / 10)))

    if precipitation > 5:
        recommendation = "No irrigation needed. Rain is sufficient."
    elif water_to_apply < 2:
        recommendation = "Minimal irrigation needed. Consider skipping today."
    else:
        recommendation = f"Apply {round(water_to_apply, 2)} mm of water."

    return {
        "temperature": temperature,
        "humidity": humidity,
        "precipitation": precipitation,
        "soil_moisture": round(estimated_soil_moisture, 2),
        "water_to_apply": round(water_to_apply, 2),
        "recommendation": recommendation
    }

# Advanced Route with Weather Data (Add This)
@app.route('/get_irrigation_advice', methods=["GET"])
def get_irrigation_advice():
    latitude = request.args.get("lat", 3.1390, type=float)
    longitude = request.args.get("lng", 101.6869, type=float)
    crop_type = request.args.get("crop", "Rice")

    # Fetch weather data
    weather_data = fetch_weather(latitude, longitude)
    if 'daily' not in weather_data:
        return jsonify({"error": "Failed to fetch weather data"}), 500

    # Calculate irrigation
    irrigation_advice = calculate_irrigation(weather_data, crop_type)
    return jsonify(irrigation_advice)

# ----------------- End of Appended Code -----------------

if __name__ == "__main__":
    app.run(debug=True)
