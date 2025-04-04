from flask import Flask, render_template, request, jsonify
import requests
import google.generativeai as genai
import datetime

app = Flask(__name__)
app.secret_key = "your_secret_key"

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

# ----------------- Dashboard Code (Appended) -----------------
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

@app.route('/get_weather_data')
def get_weather_data():
    latitude = request.args.get("lat", 3.1390, type=float)
    longitude = request.args.get("lng", 101.6869, type=float)

    print(f"[DEBUG] Fetching weather data for lat={latitude}, lng={longitude}") 
    weather_data = fetch_weather(latitude, longitude)
    
    return jsonify(weather_data)

@app.route('/get_farm_locations')
def get_farm_locations():
    state = request.args.get("state") 
    if not state:
        return jsonify({"error": "State name is required"}), 400

    osm_url = "http://overpass-api.de/api/interpreter"

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

    print(f"[DEBUG] Farms found in {state}:", farms) 

    if not farms:
        return jsonify({"error": f"No farms found in {state}"}), 404

    return jsonify(farms)

@app.route('/get_farms')
def get_farms():
    state = request.args.get("state")
    if not state:
        return jsonify({"error": "State name is required"}), 400

    return get_farm_locations()

# ----------------- Chatbot Code (Appended) -----------------

GEMINI_API_KEY = "AIzaSyCCMqub_m4O8umGE_Rw_iuGIDkxPBl7QKE"
genai.configure(api_key=GEMINI_API_KEY)

MODEL_NAME = "gemini-1.5-flash-latest"

def get_agriculture_response(user_input):
    try:
        model = genai.GenerativeModel(MODEL_NAME)  
        response = model.generate_content(user_input)  
        return response.text  
    except Exception as e:
        print("[ERROR] Gemini API Request Failed:", str(e))
        return f"Error: {str(e)}"

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message")
    response = get_agriculture_response(user_message)
    return jsonify({"reply": response})

# ----------------- Irrigation Code (Appended) -----------------

@app.route("/get_irrigation")
def get_irrigation():
    location = request.args.get("location")
    crop = request.args.get("crop")
    soil = request.args.get("soil")

    if not location:
        return jsonify({"error": "Location is required"}), 400

    lat, lng = map(float, location.split(","))  

    weather_data = fetch_weather(lat, lng)

    if 'daily' not in weather_data:
        return jsonify({"error": "Failed to fetch weather data"}), 500

    precipitation = weather_data['daily']['precipitation_sum'][0]
    water_amount = max(0, 20 - precipitation) 
    is_rain = precipitation > 1

    response = {
        "location": f"{lat}, {lng}",
        "crop": crop,
        "soil": soil,
        "water_amount": round(water_amount, 2),
        "rain": is_rain
    }
    return jsonify(response)

CROP_WATER_NEEDS = {
    "rice": 7,
    "corn": 5,
    "wheat": 4
}

SOIL_TYPE_FACTOR = {
    "sandy": 0.3,
    "loamy": 0.5,
    "clay": 0.7
}

def calculate_irrigation(weather_data, crop_type, soil_type):
    precipitation = weather_data['daily']['precipitation_sum'][0]
    temperature = weather_data['daily']['temperature_2m_mean'][0]
    humidity = weather_data['daily']['relative_humidity_2m_mean'][0]

    water_need = CROP_WATER_NEEDS.get(crop_type.lower(), 5)
    soil_factor = SOIL_TYPE_FACTOR.get(soil_type.lower(), 0.5)
    estimated_soil_moisture = (humidity / 100) * soil_factor * 10
    effective_rainfall = precipitation * 0.8
    water_to_apply = max(0, water_need - (effective_rainfall + estimated_soil_moisture))
    is_rain = precipitation > 1

    if precipitation >= water_need:
        recommendation = "No irrigation needed today due to sufficient rainfall."
    elif water_to_apply < 2:
        recommendation = "Minimal irrigation needed. Consider a light watering."
    else:
        recommendation = f"Apply approximately {round(water_to_apply, 2)} mm of water."

    explanation = (
        f"Precipitation recorded at {precipitation} mm, with an estimated effective rainfall "
        f"of {round(effective_rainfall, 2)} mm after considering surface runoff. "
        f"The soil type '{soil_type}' contributes a retention factor of {soil_factor}, "
        f"resulting in an estimated soil moisture of {round(estimated_soil_moisture, 2)} mm. "
        f"With a crop water need of {water_need} mm, the final water to apply is "
        f"{round(water_to_apply, 2)} mm. "
        f"Rain forecast: {'Yes' if is_rain else 'No'}."
    )

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
        "water_need": water_need,
        "recommendation": recommendation,
        "explanation": explanation
    }

@app.route('/get_irrigation_advice', methods=["GET"])
def get_irrigation_advice():
    latitude = request.args.get("lat", 3.1390, type=float)
    longitude = request.args.get("lng", 101.6869, type=float)
    crop_type = request.args.get("crop", "rice")
    soil_type = request.args.get("soil", "loamy")

    weather_data = fetch_weather(latitude, longitude)
    if 'daily' not in weather_data:
        return jsonify({"error": "Failed to fetch weather data"}), 500

    advice = calculate_irrigation(weather_data, crop_type, soil_type)
    
    rain_forecast = advice['effective_rainfall'] >= (0.5 * advice['water_need'])
    advice.update({"rain_forecast": rain_forecast})
    
    return jsonify(advice)

# ----------------- Weather Code (Appended) -----------------
MET_TOKEN = "31baf53255cd39bbe37efa2463824e9b60273431"
API_URL_FORECAST = "https://api.met.gov.my/v2.1/data"
API_URL_LOC = "https://api.met.gov.my/v2.1/locations?locationcategoryid=TOWN"

@app.route('/fetch_towns', methods=['GET'])
def fetch_towns():
    state_id = request.args.get("stateId")

    if not state_id:
        return jsonify({"error": "No state selected"}), 400

    headers = {"Authorization": f"METToken {MET_TOKEN}"}
    response = requests.get(API_URL_LOC, headers=headers)

    if response.status_code == 200:
        data = response.json()

        if "results" not in data or not data["results"]:
            return jsonify({"error": "No towns found"}), 404

        towns = [
            {"id": entry["id"], "name": entry["name"]}
            for entry in data["results"]
            if entry["locationrootid"] == state_id
        ]

        return jsonify(towns)

    return jsonify({"error": f"Failed to fetch towns (HTTP Code: {response.status_code})"}), response.status_code

@app.route('/fetch_forecast', methods=['GET'])
def fetch_forecast():
    location_id = request.args.get('locationId')
    if not location_id:
        return jsonify({"error": "No town selected"}), 400

    today_date = datetime.date.today().strftime("%Y-%m-%d")
    params = {
        "datasetid": "FORECAST",
        "datacategoryid": "GENERAL",
        "locationid": location_id,
        "start_date": today_date,
        "end_date": today_date
    }

    headers = {"Authorization": f"METToken {MET_TOKEN}"}

    response = requests.get(API_URL_FORECAST, headers=headers, params=params)
    
    if response.status_code != 200:
        return jsonify({"error": f"Failed to fetch forecast (HTTP Code: {response.status_code})"}), response.status_code
    
    data = response.json()
    
    if "results" not in data or not data["results"]:
        return jsonify({"error": "No forecast data found"})
    
    filtered_results = [entry for entry in data["results"] if entry.get("datatype") == "FSIGW"]
    
    if not filtered_results:
        return jsonify({"error": "No significant weather data (FSIGW) found"})
    
    forecast_data = [{
        "date": entry["date"],
        "weather": entry["value"]
    } for entry in filtered_results]
    
    return jsonify(forecast_data)

# ----------------- End of Appended Code -----------------

if __name__ == "__main__":
    app.run(debug=True)
