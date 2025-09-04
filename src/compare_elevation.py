import openrouteservice
import polyline
import matplotlib.pyplot as plt
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6ImExOWI5M2FjZTYwNjRjYzI4MTgwZmNmNmFjOWVkZWJlIiwiaCI6Im11cm11cjY0In0="
client = openrouteservice.Client(key=ORS_API_KEY)
geolocator = Nominatim(user_agent="rise-over-run")

# Geocode locations
start_address = "111 S Jackson St, Seattle, WA 98104"
end_address = "423 Terry Ave, Seattle, WA 98104"

start_location = geolocator.geocode(start_address)
end_location = geolocator.geocode(end_address)

# Use [lat, lon] format
coords = [
    [start_location.latitude, start_location.longitude],
    [end_location.latitude, end_location.longitude]
]

# Get directions to extract geometry
route = client.directions(coords, format='geojson')
route_coords = route['features'][0]['geometry']['coordinates']
# Convert to [lat, lon]
latlon_coords = [[coord[1], coord[0]] for coord in route_coords]
encoded_polyline = polyline.encode(latlon_coords)

# Get elevation
elevation = client.elevation_line(
    format_in='encodedpolyline',
    format_out='geojson',
    geometry=encoded_polyline
)

# Extract elevation points
elevation_points = elevation['geometry']['coordinates']
distances = [0]
elevations = [elevation_points[0][2]]

# Compute cumulative distance
for i in range(1, len(elevation_points)):
    prev = (elevation_points[i-1][1], elevation_points[i-1][0])  # (lat, lon)
    curr = (elevation_points[i][1], elevation_points[i][0])
    distances.append(distances[-1] + geodesic(prev, curr).meters)
    elevations.append(elevation_points[i][2])

# Plot elevation profile
plt.figure(figsize=(10, 4))
plt.plot(distances, elevations, marker='o')
plt.title('Elevation Profile')
plt.xlabel('Distance (meters)')
plt.ylabel('Elevation (m)')
plt.grid(True)
plt.tight_layout()
plt.show()