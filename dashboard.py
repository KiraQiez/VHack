from flask import Flask, render_template, request, jsonify
import requests

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
    latitude = request.args.get("lat", type=float)
    longitude = request.args.get("lng", type=float)

    if latitude is None or longitude is None:
        return jsonify({"error": "Latitude and Longitude are required"}), 400

    osm_url = "http://overpass-api.de/api/interpreter"
    
    # Overpass query to find farmland within a 10km radius
    query = f"""
    [out:json];
    (
      node["landuse"="farmland"](around:10000, {latitude}, {longitude});
      way["landuse"="farmland"](around:10000, {latitude}, {longitude});
      relation["landuse"="farmland"](around:10000, {latitude}, {longitude});
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

    return jsonify(farms)

if __name__ == "__main__":
    app.run(debug=True)
    