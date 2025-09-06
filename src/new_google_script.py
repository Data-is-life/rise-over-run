import googlemaps
import random
import time
from math import radians, cos, sin, asin, sqrt
import matplotlib.pyplot as plt
import config

# --- CONFIG ---
API_KEY = config.api_key
gmaps = googlemaps.Client(key=API_KEY)
start_address = "301 Pike St, Seattle, WA 98101"
end_address = "423 Terry Ave, Seattle, WA 98104"
JITTER_COUNT = 3  # Number of jittered variants

# --- HELPERS ---
def jitter_location(lat, lng, meters=50):
    # Roughly 1 deg latitude ~ 111km
    jitter_factor = meters / 111000
    dlat = random.uniform(-jitter_factor, jitter_factor)
    dlng = random.uniform(-jitter_factor, jitter_factor) / cos(radians(lat))
    return lat + dlat, lng + dlng

def haversine(lat1, lon1, lat2, lon2):
    # Returns distance in meters between two points
    R = 6371000  # Radius of Earth in meters
    dlat, dlon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    return 2 * R * asin(sqrt(a))

def get_route(start, end):
    return gmaps.directions(start, end, mode="walking")

def get_elevation(path):
    return gmaps.elevation_along_path(path, samples=100)

def summarize_elevation(elevations):
    gain = sum(max(elevations[i+1] - elevations[i], 0) for i in range(len(elevations)-1))
    loss = sum(max(elevations[i] - elevations[i+1], 0) for i in range(len(elevations)-1))
    return gain, loss

# --- MAIN LOGIC ---
start_location = gmaps.geocode(start_address)[0]["geometry"]["location"]
end_location = gmaps.geocode(end_address)[0]["geometry"]["location"]

routes_info = []
for i in range(JITTER_COUNT):
    jittered_start = jitter_location(start_location["lat"], start_location["lng"])
    jittered_end = jitter_location(end_location["lat"], end_location["lng"])
    
    try:
        route = get_route(jittered_start, jittered_end)
        if not route:
            continue
        path = [(step["start_location"]["lat"], step["start_location"]["lng"])
                for leg in route[0]["legs"]
                for step in leg["steps"]]
        elevation_data = get_elevation(path)
        elevations = [pt["elevation"] for pt in elevation_data]
        gain, loss = summarize_elevation(elevations)
        routes_info.append({
            "route_index": i,
            "gain": gain,
            "loss": loss,
            "distance": route[0]["legs"][0]["distance"]["value"],
            "duration": route[0]["legs"][0]["duration"]["value"],
            "path": path,
            "elevations": elevations
        })
        time.sleep(1)
    except Exception as e:
        print(f"Error in route {i}: {e}")

# --- PLOT ---
for route in routes_info:
    plt.plot(route["elevations"], label=f"Route {route['route_index']} - Gain {int(route['gain'])}m")

plt.title("Jittered Walking Routes - Elevation Profiles")
plt.xlabel("Sample Point")
plt.ylabel("Elevation (m)")
plt.legend()
plt.tight_layout()
plt.show()
