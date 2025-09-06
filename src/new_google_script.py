import googlemaps
import requests
import polyline
import matplotlib.pyplot as plt
import config

# Initialize Google Maps client
API_KEY = config.api_key
gmaps = googlemaps.Client(key=API_KEY)

# Define start and end addresses
start_address = "301 Pike St, Seattle, WA 98101"
end_address = "423 Terry Ave, Seattle, WA 98104"

# Get directions
directions = gmaps.directions(
    start_address,
    end_address,
    mode="walking",
    alternatives=False
)

# Extract encoded polyline
polyline_points = directions[0]['overview_polyline']['points']
coords = polyline.decode(polyline_points)  # Returns (lat, lon)

# Prepare elevation API call (max 512 locations per request)
locations_param = "|".join([f"{lat},{lon}" for lat, lon in coords])

elevation_url = (
    f"https://maps.googleapis.com/maps/api/elevation/json"
    f"?locations={locations_param}"
    f"&key={API_KEY}"
)
elevation_response = requests.get(elevation_url).json()

# Parse elevation data
elevations = [result['elevation'] for result in elevation_response['results']]
distances = [i for i in range(len(elevations))]

# Compute gain and loss
gain = sum(
    max(elevations[i+1] - elevations[i], 0) for i in range(len(elevations)-1)
)
loss = sum(
    max(elevations[i] - elevations[i+1], 0) for i in range(len(elevations)-1)
)

# Plot
plt.figure(figsize=(10, 4))
plt.plot(distances, elevations, color='green')
plt.title(f"Elevation Profile\nTotal Gain: {gain:.2f} m | Total Loss: {loss:.2f} m")
plt.xlabel("Path Point Index")
plt.ylabel("Elevation (m)")
plt.grid(True)
plt.tight_layout()
plt.show()
