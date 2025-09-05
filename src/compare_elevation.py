import openrouteservice
from geopy.geocoders import Nominatim
import polyline
import time
import matplotlib.pyplot as plt
import argparse
import sys

# Set up CLI arguments
parser = argparse.ArgumentParser(description='Plot elevation gain/loss between two locations.')
parser.add_argument('--start', required=True, help='Starting address (in quotes)')
parser.add_argument('--end', required=True, help='Ending address (in quotes)')
args = parser.parse_args()


# Initialize clients
ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6ImExOWI5M2FjZTYwNjRjYzI4MTgwZmNmNmFjOWVkZWJlIiwiaCI6Im11cm11cjY0In0="
geolocator = Nominatim(user_agent="rise-over-run", timeout=10)
client = openrouteservice.Client(key=ORS_API_KEY)

# Geocode with retry
def geocode_with_retry(address, retries=3, delay=2):
    for _ in range(retries):
        try:
            location = geolocator.geocode(address, timeout=10)
            if location:
                return location
        except Exception:
            time.sleep(delay)
    return None

# Fallback route function with coordinate jittering
def try_route_with_fallback(start, end, profile='foot-walking'):
    jitter_values = [0, 0.0001, -0.0001, 0.0002, -0.0002]
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
                    continue
                else:
                    raise e
    raise Exception("❌ Failed to find routable point near the starting location.")

# Main logic
start_location = geocode_with_retry(args.start)
end_location = geocode_with_retry(args.end)

if not start_location or not end_location:
    print("❌ Failed to geocode one or both addresses.")
    sys.exit(1)

start_coords = [start_location.longitude, start_location.latitude]
end_coords = [end_location.longitude, end_location.latitude]

# Get route
try:
    route = try_route_with_fallback(start_coords, end_coords)
except Exception as e:
    print(e)
    sys.exit(1)

# Decode geometry
line_coords = route['features'][0]['geometry']['coordinates']
latlon_coords = [[c[1], c[0]] for c in line_coords]
encoded = polyline.encode(latlon_coords)

# Get elevation
try:
    elevation = client.elevation_line(
        format_in='encodedpolyline',
        format_out='geojson',
        geometry=encoded
    )
except Exception as e:
    print(f"❌ Elevation API error: {e}")
    sys.exit(1)

# Analyze elevation
elevation_coords = elevation['geometry']['coordinates']
elevations = [pt[2] for pt in elevation_coords]
gain = sum(max(e2 - e1, 0) for e1, e2 in zip(elevations, elevations[1:]))
loss = sum(max(e1 - e2, 0) for e1, e2 in zip(elevations, elevations[1:]))

# Plot
plt.figure(figsize=(10, 4))
plt.plot(range(len(elevations)), elevations, label="Elevation (m)", color="green")
plt.xlabel("Point Index")
plt.ylabel("Elevation (m)")
plt.title(f"Elevation Profile\nGain: {gain:.1f} m, Loss: {loss:.1f} m")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()