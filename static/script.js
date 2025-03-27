let marker;
let userLat, userLng;

// ----------------- Map Code (Appended) -----------------
var map = L.map('map').setView([4.2105, 101.9758], 6);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 18,
  attribution: '© OpenStreetMap contributors'
}).addTo(map);

if (navigator.geolocation) {
  navigator.geolocation.getCurrentPosition(
    (position) => {
      userLat = position.coords.latitude;
      userLng = position.coords.longitude;

      console.log("[DEBUG] User Location:", userLat, userLng);

      L.marker([userLat, userLng], {
        icon: L.icon({
          iconUrl: "https://maps.google.com/mapfiles/ms/icons/green-dot.png",
          iconSize: [32, 32],
          iconAnchor: [16, 32],
          popupAnchor: [0, -32]
        })
      }).bindPopup("📍 You are here").addTo(map);

      getUserState(userLat, userLng);
      fetchWeatherData(userLat, userLng);
      fetchWeatherStatistics(userLat, userLng);
      getFarmSize(userLat, userLng);
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

// ----------------- Weather Code (Appended) -----------------
function fetchWeatherStatistics(lat, lng) {
  console.log("[DEBUG] Fetching weather stats for:", lat, lng);

  const weatherAPI = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lng}&daily=temperature_2m_mean,relative_humidity_2m_mean,precipitation_sum&timezone=Asia/Kuala_Lumpur`;

  fetch(weatherAPI)
    .then(response => response.json())
    .then(data => {
      console.log("[DEBUG] Weather Data:", data);

      const avgTemp = data.daily.temperature_2m_mean[0];
      const avgHumidity = data.daily.relative_humidity_2m_mean[0];
      const rainfall = data.daily.precipitation_sum[0];

      document.getElementById("avgTemp").textContent = `${avgTemp.toFixed(1)}°C`;
      document.getElementById("avgHumidity").textContent = `${avgHumidity.toFixed(1)}%`;
      document.getElementById("rainfall").textContent = `${rainfall.toFixed(1)} mm`;

      console.log("[DEBUG] Weather stats updated!");
    })
    .catch(error => console.error("[ERROR] Fetching weather statistics:", error));
}

// ----------------- Navbar Code (Appended) -----------------
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

// ----------------- Map Code (Appended) -----------------
function initializeMap(lat, lng) {
  if (!map) {
    map = L.map("map").setView([lat, lng], 10);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);
    console.log("[DEBUG] Map initialized.");
  }
}

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

// ----------------- Weather Code (Appended) -----------------
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

// ----------------- Map Code (Appended) -----------------
function getUserState(lat, lng) {
  console.log("[DEBUG] Getting user state...");

  const reverseGeocodeURL = `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&zoom=5&addressdetails=1`;

  fetch(reverseGeocodeURL)
    .then(response => response.json())
    .then(data => {
      if (data && data.address && data.address.state) {
        let userState = data.address.state;
        console.log("[DEBUG] User State:", userState);
        document.getElementById("userState").innerHTML = userState;
        fetchFarmLocations(userState);
      } else {
        console.warn("[WARNING] Could not determine user state.");
        document.getElementById("userState").textContent = "Unknown State";
      }
    })
    .catch(error => {
      console.error("[ERROR] Reverse geocoding failed:", error);
      document.getElementById("userState").textContent = "Error retrieving state";
    });
}

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
        if (typeof userLat === "undefined" || typeof userLng === "undefined") {
          console.error("[ERROR] User location (userLat, userLng) is undefined. Cannot display farms.");
        } else {
          displayFarmsOnMap(data);
          fetchFarmSizes(data);
        }
      }
    })
    .catch(error => console.error("[ERROR] Fetching farm locations:", error));
}

function updateFarmStatistics(farms) {
  let totalFarms = farms.length;

  document.getElementById("totalFarms").textContent = totalFarms;

  console.log(`[DEBUG] Total Farms Displayed: ${totalFarms}`);
}

function displayFarmsOnMap(farms) {
  if (!map) {
    console.error("[ERROR] Map not initialized yet.");
    return;
  }

  map.eachLayer(layer => {
    if (layer instanceof L.Marker && layer !== marker) {
      map.removeLayer(layer);
    }
  });

  if (!marker) {
    console.warn("[WARNING] User marker missing. Re-adding...");
    addUserMarker(userLat, userLng);
  }

  let validFarms = farms.filter(farm => farm.lat !== undefined && farm.lng !== undefined);
  let invalidFarms = farms.filter(farm => farm.lat === undefined || farm.lng === undefined);

  if (invalidFarms.length > 0) {
    console.warn("[WARNING] Skipping invalid farm locations:", invalidFarms);
  }

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

function updateFarmSize(size) {
  let farmSizeElement = document.getElementById("avgFarmSize");

  farmSizeElement.classList.remove("loading");

  farmSizeElement.textContent = size + " m²";
}

document.getElementById("avgFarmSize").classList.add("loading");

async function fetchFarmSizes(farms) {
  let totalSize = 0;
  let farmCount = farms.length;

  for (let farm of farms) {
    let farmSize = await getFarmSize(farm.lat, farm.lng);
    if (farmSize > 0) {
      totalSize += farmSize;
    }
  }

  let avgSize = farmCount > 0 ? (totalSize / farmCount).toFixed(2) : "N/A";
  document.getElementById("avgFarmSize").textContent = avgSize;
  setTimeout(() => {
    updateFarmSize(avgSize);
  }, 3000);
}

async function getFarmSize(lat, lng) {
  let overpassURL = `https://overpass-api.de/api/interpreter?data=[out:json];(way["landuse"="farmland"](around:1000,${lat},${lng}););out geom;`;

  try {
    let response = await fetch(overpassURL);
    let data = await response.json();

    let totalArea = 0;
    if (data.elements) {
      for (let element of data.elements) {
        if (element.geometry) {
          totalArea += calculatePolygonArea(element.geometry);
        }
      }
    }

    console.log(`[DEBUG] Farm at (${lat}, ${lng}) - Size: ${totalArea} m²`);
    return totalArea;
  } catch (error) {
    console.error("[ERROR] Failed to fetch farm size:", error);
    return 0;
  }
}

function calculatePolygonArea(points) {
  let area = 0;
  let j = points.length - 1;

  for (let i = 0; i < points.length; i++) {
    area += (points[j].lon + points[i].lon) * (points[j].lat - points[i].lat);
    j = i;
  }

  return Math.abs(area / 2.0) * 111139 * 111139;
}
