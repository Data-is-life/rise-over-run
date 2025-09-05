import openrouteservice
from geopy.geocoders import Nominatim
import polyline
import time
import matplotlib.pyplot as plt


# Initialize clients
ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6ImExOWI5M2FjZTYwNjRjYzI4MTgwZmNmNmFjOWVkZWJlIiwiaCI6Im11cm11cjY0In0="
geolocator = Nominatim(user_agent="rise-over-run", timeout=10)
client = openrouteservice.Client(key=ORS_API_KEY)

def geocode_with_retry(address, retries=3, delay=2):
    for _ in range(retries):
        try:
            location = geolocator.geocode(address, timeout=10)
            if location:
                return location
        except Exception as e:
            print(f"Geocoding error: {e}, retrying...")
            time.sleep(delay)
    return None

def try_route_with_fallback(start, end, profile='foot-walking', max_tries=9):
    jitter_values = [0, 0.0001, -0.0001, 0.0002, -0.0002, 0.0003, -0.0003, 0.0004, -0.0004]
    for lat_jitter in jitter_values:
        for lon_jitter in jitter_values:
            try_start = [start[0] + lon_jitter, start[1] + lat_jitter]
            try:
                route = client.directions(
                    coordinates=[try_start, end],
                    profile=profile,
                    format='geojson'
                )
                print(f"✅ Routing succeeded after jitter: {try_start}")
                return route
            except openrouteservice.exceptions.ApiError as e:
                if e.status_code == 404 and "routable point" in str(e):
                    continue  # try next jitter
                else:
                    raise e
    raise Exception("❌ Failed to find routable point near the starting location.")

# Addresses
start_address = "111 S Jackson St, Seattle, WA 98104"
end_address = "423 Terry Ave, Seattle, WA 98104"

start_location = geocode_with_retry(start_address)
end_location = geocode_with_retry(end_address)

if not start_location or not end_location:
    print("❌ Failed to geocode one or both addresses.")
    exit()

# Format: [longitude, latitude]
start_coords = [start_location.longitude, start_location.latitude]
end_coords = [end_location.longitude, end_location.latitude]

# Get route (with jitter fallback)
try:
    route = try_route_with_fallback(start_coords, end_coords)
except Exception as e:
    print(e)
    exit()

# Extract geometry
line_coords = route['features'][0]['geometry']['coordinates']
latlon_coords = [[c[1], c[0]] for c in line_coords]
encoded = polyline.encode(latlon_coords)

# Elevation
try:
    elevation = client.elevation_line(
        format_in='encodedpolyline',
        format_out='geojson',
        geometry=encoded
    )
except Exception as e:
    print(f"❌ Elevation API error: {e}")
    exit()

# Plot
elevation_coords = elevation['geometry']['coordinates']
distances = list(range(len(elevation_coords)))
elevations = [pt[2] for pt in elevation_coords]

plt.figure(figsize=(10, 4))
plt.plot(distances, elevations, label="Elevation (m)", color="green")
plt.xlabel("Point Index")
plt.ylabel("Elevation (m)")
plt.title("Elevation Profile")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()