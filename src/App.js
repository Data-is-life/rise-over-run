import React, { useState } from "react";
import {
    MapContainer,
    TileLayer,
    Polyline
} from "react-leaflet";
import "leaflet/dist/leaflet.css";
import polyline from "@mapbox/polyline";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

const API_KEY = process.env.REACT_APP_ORS_API_KEY;

const App = () => {
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [routeCoords, setRouteCoords] = useState([]);
  const [elevationGain, setElevationGain] = useState(null);
  const [elevationData, setElevationData] = useState([]);
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
    
    // console.log("Encoded polyline:", encoded); // ADD THIS LINE
    // console.log("Sending elevation polyline:", encoded);
    
    const elevRes = await fetch("https://api.openrouteservice.org/elevation/line", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        format_in: "encodedpolyline",
        format_out: "geojson",
        geometry: encoded,
      }),
    });
    
    const elevData = await elevRes.json();

    setElevationData(elevationChart);

    if (
      elevData &&
      elevData.geometry &&
      Array.isArray(elevData.geometry.coordinates) &&
      elevData.geometry.coordinates.length > 0
    ) {
      const elevations = elevData.geometry.coordinates.map((point) => point[2]);
      const elevationChart = elevData.geometry.coordinates.map((coord, i) => ({
          distance: i * 10, // ~10m increments
          elevation: coord[2],
      }));
      setElevationData(elevationChart);

      const gain = calculateElevationGain(elevations);
      setElevationGain(gain);
      // Optional: comment out or keep the log below if you want to verify elevation data
      // console.log("Elevation gain calculated:", gain);
    } else {
      console.error("❌ Elevation data missing or invalid:", elevData);
      alert("Couldn't get elevation data.");
    }
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
      {elevationGain && elevationData.length > 0 && (
          <Card className="shadow-md">
            <CardContent className="p-4">
              <h2 className="text-lg font-semibold mb-2 text-center text-gray-800 dark:text-white">
                Elevation Profile
              </h2>
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={elevationData}>
                  <XAxis dataKey="distance" unit="m" />
                  <YAxis dataKey="elevation" unit="m" />
                  <Tooltip />
                  <Line type="monotone" dataKey="elevation" stroke="#8884d8" dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        )}
    </div>
  );
};

export default App;
