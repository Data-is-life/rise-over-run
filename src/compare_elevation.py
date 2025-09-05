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

# Geocode addresses
start_address = "111 S Jackson St, Seattle, WA 98104"
end_address = "423 Terry Ave, Seattle, WA 98104"

start_location = geocode_with_retry(start_address)
end_location = geocode_with_retry(end_address)

if not start_location or not end_location:
    print("❌ Failed to geocode one or both addresses.")
    exit()

# Use [lat, lon] format for ORS
start_coords = [start_location.latitude, start_location.longitude]
end_coords = [end_location.latitude, end_location.longitude]

# Get route
try:
    route = client.directions(
        coordinates=[start_coords, end_coords],
        profile='foot-walking',
        format='geojson'
    )
except Exception as e:
    print(f"❌ Routing failed: {e}")
    exit()

# Extract coordinates from route
line_coords = route['features'][0]['geometry']['coordinates']
# Reformat to [lat, lon] for polyline encoding
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
    exit()

# Plot elevation
elevation_coords = elevation['geometry']['coordinates']
distances = list(range(len(elevation_coords)))
elevations = [pt[2] for pt in elevation_coords]

plt.figure(figsize=(10, 4))
plt.plot(distances, elevations, label="Elevation (m)")
plt.xlabel("Point Index")
plt.ylabel("Elevation (m)")
plt.title("Elevation Profile")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()