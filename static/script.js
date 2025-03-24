let marker; // Store user marker
let userLat, userLng; // 🔹 Declare global variables

// Initialize the map (Malaysia center, zoom 6)
var map = L.map('map').setView([4.2105, 101.9758], 6);

// Load OpenStreetMap tiles
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 18,
  attribution: '© OpenStreetMap contributors'
}).addTo(map);

// ✅ Get User Location & Fetch Farms in Their State
if (navigator.geolocation) {
  navigator.geolocation.getCurrentPosition(
    (position) => {
      userLat = position.coords.latitude;
      userLng = position.coords.longitude;

      console.log("[DEBUG] User Location:", userLat, userLng);

      // Add a green pin for user location
      L.marker([userLat, userLng], {
        icon: L.icon({
          iconUrl: "https://maps.google.com/mapfiles/ms/icons/green-dot.png",
          iconSize: [32, 32],
          iconAnchor: [16, 32],
          popupAnchor: [0, -32]
        })
      }).bindPopup("📍 You are here").addTo(map);

      // ✅ Get the user's state and fetch farms there
      getUserState(userLat, userLng);
      fetchWeatherData(userLat, userLng);
      fetchWeatherStatistics(userLat, userLng);
    },
    (error) => {
      console.error("[ERROR] Geolocation failed:", error);
      alert("Failed to get your location.");
    }
  );
} else {
  console.warn("[WARNING] Geolocation not supported.");
  alert("Geolocation is not supported by your browser.");
}

function fetchWeatherStatistics(lat, lng) {
  console.log("[DEBUG] Fetching weather stats for:", lat, lng);

  const weatherAPI = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lng}&daily=temperature_2m_mean,relative_humidity_2m_mean,precipitation_sum&timezone=Asia/Kuala_Lumpur`;

  fetch(weatherAPI)
    .then(response => response.json())
    .then(data => {
      console.log("[DEBUG] Weather Data:", data);

      // Extract today's weather data
      const avgTemp = data.daily.temperature_2m_mean[0]; // First day's temp
      const avgHumidity = data.daily.relative_humidity_2m_mean[0]; // First day's humidity
      const rainfall = data.daily.precipitation_sum[0]; // First day's rainfall

      // Update HTML
      document.getElementById("avgTemp").textContent = `${avgTemp.toFixed(1)}°C`;
      document.getElementById("avgHumidity").textContent = `${avgHumidity.toFixed(1)}%`;
      document.getElementById("rainfall").textContent = `${rainfall.toFixed(1)} mm`;

      console.log("[DEBUG] Weather stats updated!");
    })
    .catch(error => console.error("[ERROR] Fetching weather statistics:", error));
}

const navBar = document.querySelector("nav"),
  menuBtns = document.querySelectorAll(".menu-icon"),
  overlay = document.querySelector(".overlay");

menuBtns.forEach((menuBtn) => {
  menuBtn.addEventListener("click", () => {
    navBar.classList.toggle("open");
  });
});
overlay.addEventListener("click", () => {
  navBar.classList.remove("open");
});

// ✅ Function to initialize the map
function initializeMap(lat, lng) {
  if (!map) {
    map = L.map("map").setView([lat, lng], 10); // ✅ No automatic zooming
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);
    console.log("[DEBUG] Map initialized.");
  }
}

// ✅ Add user location marker (Green Pin)
function addUserMarker(lat, lng) {
  if (marker) {
    map.removeLayer(marker);
  }
  marker = L.marker([lat, lng], {
    icon: L.icon({
      iconUrl: "https://maps.google.com/mapfiles/ms/icons/green-dot.png",
      iconSize: [32, 32],
      iconAnchor: [16, 32],
      popupAnchor: [0, -32]
    })
  }).addTo(map).bindPopup("<b>You are here</b>").openPopup();

  console.log("[DEBUG] User location marked.");
}

// Fetch and update weather chart
function fetchWeatherData(lat, lng) {
  console.log("[DEBUG] Fetching weather data for:", lat, lng);

  fetch(`/get_weather_data?lat=${lat}&lng=${lng}`)
    .then(response => response.json())
    .then(data => {
      console.log("[DEBUG] Weather API Response:", data);

      const labels = data.daily.time.map(date =>
        new Date(date).toLocaleDateString("en-GB", { weekday: "short" })
      );
      const temperatures = data.daily.temperature_2m_mean;
      const humidity = data.daily.relative_humidity_2m_mean;
      const rainfall = data.daily.precipitation_sum;

      const ctx = document.getElementById("weatherChart").getContext("2d");

      if (window.weatherChart instanceof Chart) {
        window.weatherChart.destroy();
      }

      window.weatherChart = new Chart(ctx, {
        type: "line",
        data: {
          labels: labels,
          datasets: [
            {
              label: "Temperature (°C)",
              data: temperatures,
              borderColor: "red",
              backgroundColor: "rgba(255, 0, 0, 0.2)",
              fill: true,
            },
            {
              label: "Humidity (%)",
              data: humidity,
              borderColor: "blue",
              backgroundColor: "rgba(0, 0, 255, 0.2)",
              fill: true,
            },
            {
              label: "Rainfall (mm)",
              data: rainfall,
              borderColor: "green",
              backgroundColor: "rgba(0, 255, 0, 0.2)",
              fill: true,
            }
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            y: {
              beginAtZero: true
            }
          }
        }
      });
    })
    .catch(error => console.error("[ERROR] Fetching weather data:", error));
}

// ✅ Fetch the user's state using reverse geocoding
function getUserState(lat, lng) {
  console.log("[DEBUG] Getting user state...");

  const reverseGeocodeURL = `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&zoom=5&addressdetails=1`;

  fetch(reverseGeocodeURL)
    .then(response => response.json())
    .then(data => {
      if (data && data.address && data.address.state) {
        let userState = data.address.state;
        console.log("[DEBUG] User State:", userState);
        fetchFarmLocations(userState); // Fetch farms in the user's state
      } else {
        console.warn("[WARNING] Could not determine user state.");
      }
    })
    .catch(error => console.error("[ERROR] Reverse geocoding failed:", error));
}


// ✅ Fetch farms in the user's state
function fetchFarmLocations(state) {
  console.log(`[DEBUG] Fetching farms in state: ${state}`);

  fetch(`/get_farm_locations?state=${encodeURIComponent(state)}`)
    .then(response => response.json())
    .then(data => {
      console.log("[DEBUG] Farm Locations:", data);
      if (data.error) {
        console.warn(`[WARNING] No farms found in ${state}.`);
        alert(`No farms found in ${state}.`);
      } else {
        if (typeof userLat === "undefined" || typeof userLng === "undefined") {  // 🔹 Use global variables
          console.error("[ERROR] User location (userLat, userLng) is undefined. Cannot display farms.");
        } else {
          displayFarmsOnMap(data); // ✅ Fix: Pass the actual `data` (farms list)
        }
      }
    })
    .catch(error => console.error("[ERROR] Fetching farm locations:", error));
}

// ✅ Function to update farm statistics
function updateFarmStatistics(farms) {
  let totalFarms = farms.length;

  // Update total farms count
  document.getElementById("totalFarms").textContent = totalFarms;

  console.log(`[DEBUG] Total Farms Displayed: ${totalFarms}`);
}

// ✅ Display farms on the map with red pins
function displayFarmsOnMap(farms) {
  if (!map) {
    console.error("[ERROR] Map not initialized yet.");
    return;
  }

  // ✅ Remove only farm markers, NOT the user marker
  map.eachLayer(layer => {
    if (layer instanceof L.Marker && layer !== marker) {
      map.removeLayer(layer);
    }
  });

  // ✅ Re-add user marker if missing
  if (!marker) {
    console.warn("[WARNING] User marker missing. Re-adding...");
    addUserMarker(userLat, userLng);
  }

  // ✅ Validate farm data before adding markers
  let validFarms = farms.filter(farm => farm.lat !== undefined && farm.lng !== undefined);
  let invalidFarms = farms.filter(farm => farm.lat === undefined || farm.lng === undefined);

  if (invalidFarms.length > 0) {
    console.warn("[WARNING] Skipping invalid farm locations:", invalidFarms);
  }

  // ✅ Add farm markers
  validFarms.forEach((farm) => {
    L.marker([farm.lat, farm.lng], {
      icon: L.icon({
        iconUrl: "https://maps.google.com/mapfiles/ms/icons/red-dot.png",
        iconSize: [32, 32],
        iconAnchor: [16, 32],
        popupAnchor: [0, -32]
      })
    }).bindPopup(`<b>${farm.name}</b><br>Lat: ${farm.lat}, Lng: ${farm.lng}`).addTo(map);
  });

  console.log("[DEBUG] Farms displayed on map.");
  updateFarmStatistics(validFarms);
}
