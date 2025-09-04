import openrouteservice
from openrouteservice import convert
import matplotlib.pyplot as plt


# ORS API Key
ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6ImExOWI5M2FjZTYwNjRjYzI4MTgwZmNmNmFjOWVkZWJlIiwiaCI6Im11cm11cjY0In0="

# Create client
client = openrouteservice.Client(key=ORS_API_KEY)

# Define coordinates
start_coords = (-122.333592, 47.598941)  # 111 S Jackson St
end_coords = (-122.327005, 47.605090)    # 423 Terry Ave

# Get route
route = client.directions(
    coordinates=[start_coords, end_coords],
    profile='foot-walking',
    format='geojson'
)

# Get encoded polyline
geometry = route['features'][0]['geometry']
encoded_polyline = convert.encode_polyline(geometry)

# Get elevation data
elevation_response = client.elevation_line(
    format_out='geojson',
    geometry=encoded_polyline,
    format_in='encodedpolyline'
)

# Extract and plot
elevations = [coord[2] for coord in elevation_response['geometry']['coordinates']]
distances = list(range(len(elevations)))

plt.figure(figsize=(10, 4))
plt.plot(distances, elevations, label="Elevation (m)", color="green")
plt.xlabel("Point Index")
plt.ylabel("Elevation (m)")
plt.title("Elevation Profile from Start to End")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()

