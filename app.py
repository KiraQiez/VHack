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


# Crop Water Needs (mm/day)
CROP_WATER_NEEDS = {
    "rice": 7,    # High water requirement
    "corn": 5,    # Moderate water requirement
    "wheat": 4    # Lower water requirement
}

# Soil Water Retention Factor (0-1)
SOIL_TYPE_FACTOR = {
    "sandy": 0.3,   # Low retention
    "loamy": 0.5,   # Medium retention
    "clay": 0.7     # High retention
}

# Function to calculate irrigation needs
def calculate_irrigation(weather_data, crop_type, soil_type):
    # Extract weather details
    precipitation = weather_data['daily']['precipitation_sum'][0]  # mm
    temperature = weather_data['daily']['temperature_2m_mean'][0]  # °C
    humidity = weather_data['daily']['relative_humidity_2m_mean'][0]  # %

    # Base water need from crop type
    water_need = CROP_WATER_NEEDS.get(crop_type.lower(), 5)
    
    # Soil moisture estimation (humidity & soil type)
    soil_factor = SOIL_TYPE_FACTOR.get(soil_type.lower(), 0.5)
    estimated_soil_moisture = (humidity / 100) * soil_factor * 10  # 0-10 mm

    # Effective Rainfall (assuming 80% effective)
    effective_rainfall = precipitation * 0.8
    
    # Water to apply = Crop water need - (Effective Rain + Soil Moisture)
    water_to_apply = max(0, water_need - (effective_rainfall + estimated_soil_moisture))

    # Rain forecast logic
    is_rain = precipitation > 1

    # Recommendation
    if precipitation >= water_need:
        recommendation = "No irrigation needed today due to sufficient rainfall."
    elif water_to_apply < 2:
        recommendation = "Minimal irrigation needed. Consider a light watering."
    else:
        recommendation = f"Apply approximately {round(water_to_apply, 2)} mm of water."

    # Construct explanation
    explanation = (
        f"Precipitation recorded at {precipitation} mm, with an estimated effective rainfall "
        f"of {round(effective_rainfall, 2)} mm after considering surface runoff. "
        f"The soil type '{soil_type}' contributes a retention factor of {soil_factor}, "
        f"resulting in an estimated soil moisture of {round(estimated_soil_moisture, 2)} mm. "
        f"With a crop water need of {water_need} mm, the final water to apply is "
        f"{round(water_to_apply, 2)} mm. "
        f"Rain forecast: {'Yes' if is_rain else 'No'}."
    )

    # ✅ **Add Debugging Logs (Print Statements)**
    print(f"[DEBUG] Precipitation: {precipitation} mm")
    print(f"[DEBUG] Temperature: {temperature} °C")
    print(f"[DEBUG] Humidity: {humidity} %")
    print(f"[DEBUG] Water Need (Crop): {water_need} mm")
    print(f"[DEBUG] Soil Factor: {soil_factor}")
    print(f"[DEBUG] Estimated Soil Moisture: {round(estimated_soil_moisture, 2)} mm")
    print(f"[DEBUG] Effective Rainfall: {round(effective_rainfall, 2)} mm")
    print(f"[DEBUG] Final Water to Apply: {round(water_to_apply, 2)} mm")
    print(f"[DEBUG] Rain Forecast: {'Yes' if is_rain else 'No'}")

    return {
        "temperature": temperature,
        "humidity": humidity,
        "precipitation": precipitation,
        "soil_moisture": round(estimated_soil_moisture, 2),
        "effective_rainfall": round(effective_rainfall, 2),
        "water_to_apply": round(water_to_apply, 2),
        "water_need": water_need,  # Add this line
        "recommendation": recommendation,
        "explanation": explanation
    }


# Advanced Route with Weather Data (Add This)
@app.route('/get_irrigation_advice', methods=["GET"])
def get_irrigation_advice():
    latitude = request.args.get("lat", 3.1390, type=float)
    longitude = request.args.get("lng", 101.6869, type=float)
    crop_type = request.args.get("crop", "rice")
    soil_type = request.args.get("soil", "loamy")

    # Fetch weather data
    weather_data = fetch_weather(latitude, longitude)
    if 'daily' not in weather_data:
        return jsonify({"error": "Failed to fetch weather data"}), 500

    # Calculate irrigation
    advice = calculate_irrigation(weather_data, crop_type, soil_type)
    
    # Include rain forecast logic in response
    rain_forecast = advice['effective_rainfall'] >= (0.5 * advice['water_need'])
    advice.update({"rain_forecast": rain_forecast})
    
    return jsonify(advice)


# ----------------- End of Appended Code -----------------

if __name__ == "__main__":
    app.run(debug=True)
