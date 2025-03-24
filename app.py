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

@app.route("/insights")
def insights():
    return render_template("insights.html")

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

if __name__ == "__main__":
    app.run(debug=True)
