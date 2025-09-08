import googlemaps
import polyline
import time
import matplotlib.pyplot as plt
import numpy as np
import config


# Initialize with your Google Maps API key
gmaps = googlemaps.Client(key=config.api_key)


start_address = "301 Pike St, Seattle, WA 98101"
end_address = "423 Terry Ave, Seattle, WA 98104"


# Step 1: Get exact coordinates of start and end
start_location = gmaps.geocode(start_address)[0]["geometry"]["location"]
end_location = gmaps.geocode(end_address)[0]["geometry"]["location"]


# Step 2: Get the main route
directions = gmaps.directions(
    origin=start_location,
    destination=end_location,
    mode="walking",
    alternatives=False
)


route = directions[0]
points = polyline.decode(route["overview_polyline"]["points"])


# Step 3: Get elevation data in chunks (Google Elevation API limit = 512 samples)
# path = "|".join(f"{lat},{lng}" for lat, lng in points)
# Ensure points are lat/lon and >= 2
path = [(pt["lat"], pt["lng"]) for pt in points]

if len(path) < 2:
    raise ValueError("Need at least 2 points for elevation data.")

samples = min(512, len(path))

elevation_data = gmaps.elevation_along_path(path=path, samples=samples)


# elevation_data = gmaps.elevation_along_path(path=path, samples=min(512, len(points)))


elevations = [pt["elevation"] for pt in elevation_data]
latlngs = [(pt["location"]["lat"], pt["location"]["lng"]) for pt in elevation_data]


# Step 4: Compute slope between intersections and identify high-slope segments
def compute_slope(elevation_profile):
    slopes = []
    for i in range(1, len(elevation_profile)):
        delta_elev = elevation_profile[i] - elevation_profile[i - 1]
        horizontal_dist = 1 # unit-less, since we don't have actual distance
        slopes.append(delta_elev / horizontal_dist)
    return slopes


slopes = compute_slope(elevations)

# Step 5: Detect steep segments and intersections
def detect_intersections(slopes, threshold=0.05):
    intersection_indices = []
    for i, slope in enumerate(slopes):
        if abs(slope) > threshold:
            intersection_indices.append(i)
    return intersection_indices


intersections = detect_intersections(slopes)


# Step 6: Plot elevation and highlight steep slopes
plt.figure(figsize=(12, 5))
plt.plot(elevations, label="Elevation")
plt.scatter(intersections, [elevations[i] for i in intersections], color='red', label="Steep Slopes")
plt.title("Elevation Profile with Intersections")
plt.xlabel("Point Index")
plt.ylabel("Elevation (m)")
plt.legend()
plt.tight_layout()
plt.show()