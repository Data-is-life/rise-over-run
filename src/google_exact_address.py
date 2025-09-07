import googlemaps
from datetime import datetime
import matplotlib.pyplot as plt
from itertools import combinations
import os
import config

# Set up your Google Maps API key
gmaps = googlemaps.Client(key=config.api_key)

# Base addresses
start_address = "301 Pike St, Seattle, WA 98101"
end_address = "423 Terry Ave, Seattle, WA 98104"

# Define some potential waypoint candidates near the straight line between start and end
waypoint_candidates = [
    "Pine St & 7th Ave, Seattle, WA",
    "Olive Way & 8th Ave, Seattle, WA",
    "Stewart St & 9th Ave, Seattle, WA",
    "Union St & Terry Ave, Seattle, WA"
]

# Build all combinations of 1-2 waypoints
waypoint_combos = []
for r in [1, 2]:
    waypoint_combos.extend(combinations(waypoint_candidates, r))

# Include the no-waypoint direct route as well
waypoint_combos = [()] + waypoint_combos

routes = []

# Helper to calculate elevation gain/loss
def compute_elevation_stats(elevations):
    gain, loss = 0, 0
    for i in range(1, len(elevations)):
        diff = elevations[i] - elevations[i - 1]
        if diff > 0:
            gain += diff
        else:
            loss -= diff
    return gain, loss

# Query each route variation
for waypoints in waypoint_combos:
    try:
        directions_result = gmaps.directions(
            origin=start_address,
            destination=end_address,
            mode="walking",
            waypoints=waypoints,
            departure_time=datetime.now()
        )

        if not directions_result:
            continue

        # Decode the polyline for the first route
        steps = directions_result[0]["legs"][0]["steps"]
        path = []
        for step in steps:
            start_loc = step["start_location"]
            path.append((start_loc["lat"], start_loc["lng"]))
        end_loc = steps[-1]["end_location"]
        path.append((end_loc["lat"], end_loc["lng"]))

        # Get elevation data from Google Elevation API
        elevation_data = gmaps.elevation_along_path(path, samples=100)
        elevations = [point["elevation"] for point in elevation_data]

        gain, loss = compute_elevation_stats(elevations)
        distance = directions_result[0]["legs"][0]["distance"]["value"]  # in meters

        routes.append({
            "waypoints": waypoints,
            "elevations": elevations,
            "gain": gain,
            "loss": loss,
            "distance": distance,
        })

    except Exception as e:
        print(f"Failed for waypoints {waypoints}: {e}")

# Rank by elevation gain (least gain preferred)
routes_sorted = sorted(routes, key=lambda r: (r["gain"], r["distance"]))

# Plot elevation profiles for top 3 routes
plt.figure(figsize=(10, 6))
for i, route in enumerate(routes_sorted[:3]):
    plt.plot(route["elevations"], label=f"Route {i+1}: gain={round(route['gain'],1)}m, loss={round(route['loss'],1)}m, dist={round(route['distance']/1000,2)}km")
plt.title("Top 3 Routes by Elevation Gain")
plt.xlabel("Sample Points")
plt.ylabel("Elevation (m)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()