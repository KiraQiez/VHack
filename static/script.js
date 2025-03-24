let map; // Declare map globally

document.addEventListener("DOMContentLoaded", function () {
  if ("geolocation" in navigator) {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const userLat = position.coords.latitude;
        const userLng = position.coords.longitude;

        console.log("[DEBUG] User Location:", userLat, userLng);

        initializeMap(userLat, userLng);  // ✅ Initialize map first
        fetchWeatherData(userLat, userLng);

        // ✅ Ensure farms are fetched after the map is ready
        setTimeout(() => {
          fetchFarmLocations(userLat, userLng);
        }, 500);
      },
      (error) => {
        console.error("[ERROR] Failed to get user location:", error.message);
        alert("Unable to fetch location. Using default (Kuala Lumpur).");

        initializeMap(3.1390, 101.6869);
        fetchWeatherData(3.1390, 101.6869);

        setTimeout(() => {
          fetchFarmLocations(3.1390, 101.6869);
        }, 500);
      }
    );
  } else {
    console.error("[ERROR] Geolocation not supported.");
  }
});

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
    map = L.map("map").setView([lat, lng], 10);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);
    console.log("[DEBUG] Map initialized.");
  }
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

      // Destroy chart if it exists
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

// ✅ Function to fetch farm locations
function fetchFarmLocations(lat, lng) {
  console.log("[DEBUG] Fetching farm locations for lat:", lat, "lng:", lng);

  fetch(`/get_farm_locations?lat=${lat}&lng=${lng}`)
    .then(response => response.json())
    .then(data => {
      console.log("[DEBUG] Farm Locations:", data);
      if (data.error) {
        console.error("[ERROR] Fetching farm locations:", data.error);
      } else {
        displayFarmsOnMap(data);
      }
    })
    .catch(error => console.error("[ERROR] Fetching farm locations:", error));
}

// ✅ Function to display farms on the map
function displayFarmsOnMap(farms) {
  if (!map) {
    console.error("[ERROR] Map not initialized yet.");
    return;
  }

  if (farms.length === 0) {
    console.warn("[WARNING] No farms found.");
    return;
  }

  farms.forEach((farm) => {
    L.marker([farm.lat, farm.lng])
      .bindPopup(`<b>${farm.name}</b><br>Lat: ${farm.lat}, Lng: ${farm.lng}`)
      .addTo(map);
  });

  console.log("[DEBUG] Farms displayed on map.");
}