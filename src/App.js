import React, { useState } from "react";
import { MapContainer, TileLayer, Polyline } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import polyline from "@mapbox/polyline";

const API_KEY = process.env.REACT_APP_ORS_API_KEY;

const App = () => {
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [routeCoords, setRouteCoords] = useState([]);
  const [elevationGain, setElevationGain] = useState(null);
  const [center, setCenter] = useState([37.7749, -122.4194]);
  const [routeType, setRouteType] = useState("flat");

  const geocode = async (place) => {
    const res = await fetch(`https://api.openrouteservice.org/geocode/search?api_key=${API_KEY}&text=${encodeURIComponent(place)}`);
    const data = await res.json();
    const coords = data.features[0]?.geometry.coordinates;
    return coords ? [coords[1], coords[0]] : null;
  };

  const calculateElevationGain = (elevations) => {
    let gain = 0;
    for (let i = 1; i < elevations.length; i++) {
      const diff = elevations[i] - elevations[i - 1];
      if (diff > 0) gain += diff;
    }
    return gain.toFixed(1) + " m";
  };

  const handleRouteRequest = async () => {
    const startCoords = await geocode(start);
    const endCoords = await geocode(end);
    if (!startCoords || !endCoords) {
      alert("Unable to geocode one or both addresses.");
      return;
    }

    const preference = routeType === "fast" ? "fastest" : "recommended";
    const routeRes = await fetch(`https://api.openrouteservice.org/v2/directions/foot-walking/geojson`, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        preference,
        coordinates: [
          [startCoords[1], startCoords[0]],
          [endCoords[1], endCoords[0]],
        ],
      }),
    });

    const routeData = await routeRes.json();

    // Convert coordinates back to [lng, lat] for polyline encoding
    const originalCoords = routeData.features[0].geometry.coordinates;
    const coords = originalCoords.map(([lng, lat]) => [lat, lng]);
    setRouteCoords(coords);
    setCenter(coords[0]);
  
    const encoded = polyline.encode(originalCoords.map(([lng, lat]) => [lat, lng]));
    
    console.log("Encoded polyline:", encoded); // ADD THIS LINE
    
    const elevRes = await fetch("https://api.openrouteservice.org/elevation/line", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        format_in: "encodedpolyline",
        format_out: "json",
        geometry: encoded,
      }),
    });
    
    const elevData = await elevRes.json();
    console.log("Elevation API response:", elevData);

    if (!elevData.geometry) {
      console.error("Elevation response invalid:", elevData);
      alert("Couldn't get elevation data.");
      return;
    }

    const elevations = elevData.geometry.map((point) => point[2]);
    const gain = calculateElevationGain(elevations);
    setElevationGain(gain);
  };

  return (
    <div style={{ maxWidth: 600, margin: 'auto', padding: 20 }}>
      <h1>Rise Over Run</h1>
      <input placeholder="Start location" value={start} onChange={(e) => setStart(e.target.value)} />
      <input placeholder="End location" value={end} onChange={(e) => setEnd(e.target.value)} />
      <select value={routeType} onChange={(e) => setRouteType(e.target.value)}>
        <option value="flat">Flattest</option>
        <option value="fast">Fastest</option>
      </select>
      <button onClick={handleRouteRequest}>Find Route</button>
      <div style={{ height: 400, marginTop: 20 }}>
        <MapContainer center={center} zoom={14} style={{ height: "100%" }}>
          <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
          {routeCoords.length > 0 && <Polyline positions={routeCoords} color="blue" />}
        </MapContainer>
      </div>
      {elevationGain && <p>Estimated Elevation Gain: {elevationGain}</p>}
    </div>
  );
};

export default App;
