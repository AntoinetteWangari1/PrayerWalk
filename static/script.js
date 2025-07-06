let map = L.map('map').setView([0, 0], 16);
let polyline = L.polyline([], { color: 'blue' }).addTo(map);
let marker = null;
let route = [];
let watchId = null;

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

document.getElementById('startBtn').onclick = () => {
  route = [];
  polyline.setLatLngs([]);
  watchId = navigator.geolocation.watchPosition(pos => {
    const latlng = [pos.coords.latitude, pos.coords.longitude];
    map.setView(latlng, 18);
    if (!marker) marker = L.marker(latlng).addTo(map);
    else marker.setLatLng(latlng);
    route.push(latlng);
    polyline.setLatLngs(route);
  }, console.error, { enableHighAccuracy: true });

  document.getElementById('startBtn').disabled = true;
  document.getElementById('stopBtn').disabled = false;
};

document.getElementById('stopBtn').onclick = () => {
  navigator.geolocation.clearWatch(watchId);
  const geojson = {
    type: "Feature",
    geometry: {
      type: "LineString",
      coordinates: route.map(pt => [pt[1], pt[0]])
    },
    properties: {
      timestamp: new Date().toISOString()
    }
  };

  fetch('/save_geojson', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(geojson)
  })
    .then(res => res.json())
    .then(data => alert(data.message));

  document.getElementById('startBtn').disabled = false;
  document.getElementById('stopBtn').disabled = true;
};
