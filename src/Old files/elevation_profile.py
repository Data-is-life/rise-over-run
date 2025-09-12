import openrouteservice
import matplotlib.pyplot as plt
from geopy.distance import geodesic
import numpy as np
import config


# ORS API Key
ORS_API_KEY = cofig.ors_api

# Create client
client = openrouteservice.Client(key=ORS_API_KEY)

# Define coordinates (lng, lat)
start_coords = (-122.333592, 47.598941)  # 111 S Jackson St
end_coords = (-122.327005, 47.605090)    # 423 Terry Ave

# Get route
route = client.directions(
    coordinates=[start_coords, end_coords],
    profile='foot-walking',
    format='geojson'
)

# Get geometry
geometry = route['features'][0]['geometry']

# Elevation request using geojson format directly
elevation_response = client.elevation_line(
    geometry=geometry,
    format_in='geojson',
    format_out='geojson'
)

# Extract and plot elevation data
coords = elevation_response['geometry']['coordinates']
elevations = [coord[2] for coord in coords]

# Compute distances and slopes
distances = [0.0]
slopes = []

for i in range(1, len(coords)):
    prev = coords[i-1]
    curr = coords[i]

    # Compute distance in meters between two points
    dist = geodesic((prev[1], prev[0]), (curr[1], curr[0])).meters
    distances.append(distances[-1] + dist)

    # Slope: rise/run as a percentage
    rise = curr[2] - prev[2]
    slope_percent = (rise / dist) * 100 if dist != 0 else 0
    slopes.append(slope_percent)

# Pad slope list to match elevation points
slopes = [slopes[0]] + slopes

# Print slope stats
max_slope = max(slopes)
min_slope = min(slopes)
avg_slope = sum(slopes) / len(slopes)
uphill_pct = sum(1 for s in slopes if s > 1) / len(slopes) * 100
downhill_pct = sum(1 for s in slopes if s < -1) / len(slopes) * 100
flat_pct = 100 - uphill_pct - downhill_pct

print(f"Max slope: {max_slope:.2f}%")
print(f"Min slope: {min_slope:.2f}%")
print(f"Average slope: {avg_slope:.2f}%")
print(f"Uphill: {uphill_pct:.1f}%, Downhill: {downhill_pct:.1f}%, Flat: {flat_pct:.1f}%")


# Plot elevation and slope
fig, ax1 = plt.subplots(figsize=(12, 5))

# Elevation
ax1.set_xlabel("Distance (m)")
ax1.set_ylabel("Elevation (m)", color='green')
ax1.plot(distances, elevations, color='green', label='Elevation')
ax1.tick_params(axis='y', labelcolor='green')

# Slope
ax2 = ax1.twinx()
ax2.set_ylabel("Slope (%)", color='blue')
ax2.plot(distances, slopes, color='blue', linestyle='dashed', label='Slope')
ax2.tick_params(axis='y', labelcolor='blue')

plt.title("Elevation and Slope Profile")
fig.tight_layout()
plt.grid(True)
plt.show()

