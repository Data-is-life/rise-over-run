import openrouteservice
import polyline
import matplotlib.pyplot as plt
from geopy.geocoders import Nominatim
import time


# Initialize clients
ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6ImExOWI5M2FjZTYwNjRjYzI4MTgwZmNmNmFjOWVkZWJlIiwiaCI6Im11cm11cjY0In0="
geolocator = Nominatim(user_agent="rise-over-run", timeout=10)
client = openrouteservice.Client(key=ORS_API_KEY)

# Get base coordinates
start_address = "111 S Jackson St, Seattle, WA 98104"
end_address = "423 Terry Ave, Seattle, WA 98104"
start = geolocator.geocode(start_address)
end = geolocator.geocode(end_address)
time.sleep(1)

base_start = [start.longitude, start.latitude]
end_coords = [end.longitude, end.latitude]

# Create small variations in start coords
offsets = [0, 0.0003, -0.0003]
routes = []

for dx in offsets:
    start_coords = [base_start[0] + dx, base_start[1]]
    try:
        route = client.directions([start_coords, end_coords], profile='foot-walking', format='geojson')
        coords = route['features'][0]['geometry']['coordinates']
        latlon = [[c[1], c[0]] for c in coords]
        encoded = polyline.encode(latlon)

        elev = client.elevation_line(format_in='encodedpolyline', geometry=encoded)
        elevation = [pt[2] for pt in elev['geometry']['coordinates']]
        gain = max(elevation) - min(elevation)
        routes.append((elevation, gain))
    except Exception as e:
        print("Route failed:", e)

# Plotting
plt.figure(figsize=(12, 6))
for i, (elevation, gain) in enumerate(routes):
    plt.plot(elevation, label=f"Route {i+1} (Gain: {gain:.1f} m)")

plt.title("Elevation Profiles of Nearby Routes")
plt.xlabel("Point Index")
plt.ylabel("Elevation (m)")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()