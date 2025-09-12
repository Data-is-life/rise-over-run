import openrouteservice
from openrouteservice import convert
from geopy.geocoders import Nominatim
import polyline
import matplotlib.pyplot as plt
import numpy as np
import time
import config

# Initialize clients
ORS_API_KEY = config.ors_api
geolocator = Nominatim(user_agent="rise-over-run", timeout=10)
client = openrouteservice.Client(key=ORS_API_KEY)


def geocode(address):
    location = geolocator.geocode(address, timeout=10)
    if location:
        return [location.longitude, location.latitude]
    else:
        raise ValueError(f"Could not geocode: {address}")


def get_route(start, end):
    for _ in range(3):
        try:
            route = client.directions(
                coordinates=[start, end],
                profile='foot-walking',
                format='geojson'
                )
            return route
        except Exception as e:
            print("Retrying route fetch due to:", e)
            time.sleep(1)
            raise RuntimeError("Failed to fetch route")


def get_elevation_along_route(route):
    coords = [list(reversed(coord)) for coord in route['features'][0]['geometry']['coordinates']]
    encoded_poly = polyline.encode(coords)
    print("Encoded polyline:", encoded_poly)


    elevation = client.elevation_line(
        format_out="geojson",
        geometry=encoded_poly,
        format_in="encodedpolyline"
    )


    print("Elevation response full:", elevation)
    return elevation['geometry']['coordinates']


def plot_elevation(elevation_coords):
    if elevation_coords:
        elevations = [pt[2] for pt in elevation_coords if len(pt) == 3]

        if elevations:
            plt.figure(figsize=(10, 5))
            plt.plot(range(len(elevations)), elevations, label="Route Elevation")
            plt.title("Elevation Profile")
            plt.xlabel("Point Index")
            plt.ylabel("Elevation (m)")
            plt.grid(True)
            plt.legend()
            plt.tight_layout()
            plt.show()
        else:
            print("⚠️ No elevation values found in coordinates.")
    else:
        print("⚠️ Elevation coordinates list is empty.")


if __name__ == "__main__":
    start_address = "301 Pike St, Seattle, WA 98101"
    end_address = "423 Terry Ave, Seattle, WA 98104"


    start_coords = geocode(start_address)
    end_coords = geocode(end_address)


    route = get_route(start_coords, end_coords)
    elevation_coords = get_elevation_along_route(route)
    plot_elevation(elevation_coords)