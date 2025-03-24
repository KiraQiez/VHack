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

// Load Weather Data into Chart.js
fetch('/get_weather_data')
  .then(response => response.json())
  .then(data => {
    const ctx = document.getElementById('weatherChart').getContext('2d');
    new Chart(ctx, {
      type: 'line',
      data: {
        labels: data.days,
        datasets: [
          {
            label: 'Temperature (°C)',
            data: data.temperature,
            borderColor: 'red',
            backgroundColor: 'rgba(255, 0, 0, 0.2)',
            fill: true
          },
          {
            label: 'Humidity (%)',
            data: data.humidity,
            borderColor: 'blue',
            backgroundColor: 'rgba(0, 0, 255, 0.2)',
            fill: true
          }
        ]
      }
    });
  });

// Load Farm Locations into Leaflet Map
var map = L.map('map').setView([3.1390, 101.6869], 6);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
fetch('/get_farm_locations')
  .then(response => response.json())
  .then(farms => {
    farms.forEach(farm => {
      L.marker([farm.lat, farm.lng]).addTo(map).bindPopup(`<b>${farm.name}</b>`);
    });
  });