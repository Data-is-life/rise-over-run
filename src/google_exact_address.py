import googlemaps
import random
import time
import matplotlib.pyplot as plt
import config

# Initialize Google Maps client (replace with your API key)
API_KEY = config.api_key
gmaps = googlemaps.Client(key=API_KEY)

# Addresses
start_address = "301 Pike St, Seattle, WA 98101"
end_address = "423 Terry Ave, Seattle, WA 98104"

# Geocode addresses to get lat/lng
start_location = gmaps.geocode(start_address)[0]["geometry"]["location"]
end_location = gmaps.geocode(end_address)[0]["geometry"]["location"]

# Generate jittered waypoints around midpoint
mid_lat = (start_location["lat"] + end_location["lat"]) / 2
mid_lng = (start_location["lng"] + end_location["lng"]) / 2
waypoints = [
    {"lat": mid_lat + random.uniform(-0.001, 0.001), "lng": mid_lng + random.uniform(-0.001, 0.001)}
    for _ in range(3)
]

routes_info = []

for idx, wp in enumerate(waypoints):
    waypoint_str = f"{wp['lat']},{wp['lng']}"
    directions_result = gmaps.directions(
        origin=start_address,
        destination=end_address,
        waypoints=[waypoint_str],
        mode="walking"
    )
    
    if not directions_result:
        continue

    # Extract path (list of lat/lng tuples)
    steps = directions_result[0]["legs"][0]["steps"]
    points = [(step["end_location"]["lat"], step["end_location"]["lng"]) for step in steps]
    
    # Fetch elevation data
    elevations = gmaps.elevation_along_path(path=points, samples=min(512, len(points)))
    print(elevations[0]['elevation'] - elevations[-1]['elevation'])
    # Compute elevation gain/loss
    gain = 0
    loss = 0
    for i in range(1, len(elevations)):
        delta = elevations[i]["elevation"] - elevations[i-1]["elevation"]
        if delta > 0:
            gain += delta
        else:
            loss -= delta
    
    # Save route info
    routes_info.append({
        "waypoint": waypoint_str,
        "gain": gain,
        "loss": loss,
        "elevations": elevations
    })

# Plot elevation profiles
for i, route in enumerate(routes_info):
    elevs = [pt["elevation"] for pt in route["elevations"]]
    plt.plot(elevs, label=f"Route {i+1} (Gain: {route['gain']:.1f}m, Loss: {route['loss']:.1f}m)")


plt.title("Elevation Profiles of Routes with Jittered Waypoints")
plt.xlabel("Sample Points")
plt.ylabel("Elevation (m)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()
