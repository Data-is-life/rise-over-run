"""
Rise Over Run — Valhalla routing core (v1)

What this does
--------------
1) Calls a local Valhalla /route service (walking) and asks for alternates.
2) For each returned route polyline, resamples it at 10 ft spacing and samples elevation.
3) Computes:
   - total_distance_m
   - total_abs_gain_m (absolute gain, up + down counted positive)
   - per_step_gain_m (series over 10 ft steps)
   - grade_smoothness (std dev of gain per 10 ft, lower is smoother)
   - gain_per_10ft_m
4) Picks three options:
   - Shortest
   - Flattest (min abs gain) subject to distance <= (1+tau) * shortest_distance
   - Compromise (weighted distance + gain + smoothness)

Assumptions
-----------
- You have Valhalla running locally at http://localhost:8002.
- You have SRTM/DEM rasters (e.g., .hgt or GeoTIFF) covering your area; we sample with rasterio.
- Coordinates are in [lon, lat] (Valhalla style); we reproject for metric resampling.

Notes
-----
- If you prefer Valhalla's built-in elevation tiles, swap `sample_elevation_raster` with a Valhalla /height (if enabled) call.
- All constants are easy to tune at the bottom.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple, Dict, Any, Optional
import math
import json
import requests
import numpy as np
from shapely.geometry import LineString, Point
from shapely.ops import transform
import pyproj
import rasterio


# -----------------------------
# Data structures
# -----------------------------
@dataclass
class RouteMetrics:
    name: str
    distance_m: float
    abs_gain_m: float
    grade_smoothness: float  # std dev of per-step gain (m per 10 ft)
    gain_per_10ft_m: float   # mean absolute gain per 10 ft step
    steps: int

    def as_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "distance_m": round(self.distance_m, 2),
            "abs_gain_m": round(self.abs_gain_m, 2),
            "grade_smoothness": round(self.grade_smoothness, 4),
            "gain_per_10ft_m": round(self.gain_per_10ft_m, 4),
            "steps": int(self.steps),
        }


# -----------------------------
# Geometry helpers
# -----------------------------
WGS84 = pyproj.CRS.from_epsg(4326)
# Use a local UTM auto projection so distances are in meters
AUTO_PROJ = pyproj.CRS.from_user_input("+proj=utm +zone=10 +datum=WGS84 +units=m +no_defs")  # Seattle example; swap per city
PROJECT_TO_M = pyproj.Transformer.from_crs(WGS84, AUTO_PROJ, always_xy=True).transform
PROJECT_TO_LL = pyproj.Transformer.from_crs(AUTO_PROJ, WGS84, always_xy=True).transform


def to_linestring(coords_lonlat: List[Tuple[float, float]]) -> LineString:
    return LineString(coords_lonlat)


def resample_linestring_metric(ls: LineString, step_m: float) -> LineString:
    if ls.length == 0:
        return ls
    target = [ls.interpolate(d) for d in np.arange(0, ls.length, step_m)]
    # Ensure last point included
    if target[-1].distance(ls.boundary.geoms[-1]) > 1e-6:
        target.append(ls.boundary.geoms[-1])
    return LineString(target)


# -----------------------------
# Elevation sampling
# -----------------------------
class ElevationSampler:
    """Sample elevation from a list of raster files that cover the area.
    Rasters must be in a projected or geographic CRS with a transform.
    """
    def __init__(self, raster_paths: List[str]):
        self.datasets = [rasterio.open(p) for p in raster_paths]

    def _sample_one(self, lon: float, lat: float) -> Optional[float]:
        for ds in self.datasets:
            try:
                row, col = ds.index(lon, lat)
                val = ds.read(1)[row, col]
                if ds.nodata is not None and val == ds.nodata:
                    continue
                # Some DEMs store in centimeters or with scale; assume meters
                return float(val)
            except Exception:
                continue
        return None

    def sample_profile(self, coords_lonlat: List[Tuple[float, float]]) -> List[Optional[float]]:
        return [self._sample_one(lon, lat) for lon, lat in coords_lonlat]


# -----------------------------
# Metric computation
# -----------------------------
TEN_FT_IN_M = 3.048


def compute_metrics_for_coords(coords_lonlat: List[Tuple[float, float]], elevs_m: List[Optional[float]], name: str) -> RouteMetrics:
    """Compute distance, absolute gain, smoothness, etc., at 10 ft cadence."""
    # Project to meters for distance & resampling
    ls_ll = LineString(coords_lonlat)
    ls_m = transform(PROJECT_TO_M, ls_ll)

    # Resample to 10 ft spacing in meters
    rs_m = resample_linestring_metric(ls_m, TEN_FT_IN_M)
    rs_ll = transform(PROJECT_TO_LL, rs_m)
    rs_coords = list(rs_ll.coords)

    # If input elevations are for original coords, resample elevations along rs_coords
    # For simplicity: re-sample elevations directly for rs_coords
    # Caller can pass an ElevationSampler.sample_profile(rs_coords)
    distance_m = rs_m.length

    # Compute per-step absolute elevation deltas
    # Elevations may contain None; forward-fill simple
    def ffill(vals: List[Optional[float]]) -> List[Optional[float]]:
        last = None
        out = []
        for v in vals:
            if v is None and last is not None:
                out.append(last)
            else:
                out.append(v)
                last = v if v is not None else last
        return out

    elevs_rs = ffill(elevs_m)
    # If still None at the beginning, backfill with first non-None
    first_valid = next((v for v in elevs_rs if v is not None), None)
    elevs_rs = [first_valid if v is None else v for v in elevs_rs]

    per_step_gain = []
    abs_gain_sum = 0.0
    for i in range(1, len(elevs_rs)):
        dz = float(elevs_rs[i] - elevs_rs[i-1]) if elevs_rs[i] is not None and elevs_rs[i-1] is not None else 0.0
        per_step_gain.append(abs(dz))  # absolute gain rule
        abs_gain_sum += abs(dz)

    steps = max(0, len(per_step_gain))
    gain_per_10ft = (abs_gain_sum / steps) if steps else 0.0
    grade_smoothness = float(np.std(per_step_gain)) if steps else 0.0

    return RouteMetrics(
        name=name,
        distance_m=float(distance_m),
        abs_gain_m=float(abs_gain_sum),
        grade_smoothness=grade_smoothness,
        gain_per_10ft_m=gain_per_10ft,
        steps=steps,
    )


# -----------------------------
# Scoring / selection
# -----------------------------
@dataclass
class SelectionParams:
    distance_threshold_tau: float = 0.15  # flattest must be within +15% of shortest distance
    w_distance: float = 0.4
    w_abs_gain: float = 0.4
    w_smooth: float = 0.2


def pick_routes(metric_list: List[RouteMetrics], params: SelectionParams) -> Dict[str, RouteMetrics]:
    if not metric_list:
        raise ValueError("No routes to pick from")

    # Shortest
    shortest = min(metric_list, key=lambda m: m.distance_m)

    # Flattest subject to distance constraint
    max_dist = (1.0 + params.distance_threshold_tau) * shortest.distance_m
    feas = [m for m in metric_list if m.distance_m <= max_dist]
    flattest = min(feas or metric_list, key=lambda m: m.abs_gain_m)

    # Compromise: normalize and weighted sum
    dists = np.array([m.distance_m for m in metric_list], dtype=float)
    gains = np.array([m.abs_gain_m for m in metric_list], dtype=float)
    smooth = np.array([m.grade_smoothness for m in metric_list], dtype=float)

    def norm(x):
        rng = x.max() - x.min()
        return (x - x.min()) / rng if rng > 0 else np.zeros_like(x)

    D, G, S = norm(dists), norm(gains), norm(smooth)
    score = params.w_distance * D + params.w_abs_gain * G + params.w_smooth * S
    compromise = metric_list[int(np.argmin(score))]

    return {"shortest": shortest, "flattest": flattest, "compromise": compromise}


# -----------------------------
# Valhalla route fetch
# -----------------------------
VALHALLA_URL = "http://localhost:8002/route"


def valhalla_route_with_alternates(origin_lonlat: Tuple[float, float], dest_lonlat: Tuple[float, float], max_alternates: int = 4) -> Dict[str, Any]:
    payload = {
        "locations": [
            {"lon": origin_lonlat[0], "lat": origin_lonlat[1]},
            {"lon": dest_lonlat[0], "lat": dest_lonlat[1]},
        ],
        "costing": "pedestrian",
        "alternates": max_alternates,
        "language": "en-US",
        "units": "kilometers",
        "directions_options": {"units": "kilometers"},
    }
    r = requests.post(VALHALLA_URL, json=payload, timeout=60)
    r.raise_for_status()
    return r.json()


# -----------------------------
# Polyline extraction and end-to-end scoring
# -----------------------------

def decode_polyline(poly: Dict[str, Any]) -> List[Tuple[float, float]]:
    # Valhalla encodes shapes as string; but JSON results usually include decoded shape in each leg's shape as polyline5
    # To keep things generic, we expect a list of [lon, lat] pairs already; adjust if you need to decode
    return poly  # placeholder if already decoded


def extract_route_coords(route_json: Dict[str, Any]) -> List[List[Tuple[float, float]]]:
    routes = []
    for i, rt in enumerate(route_json.get("routes", [])):
        coords: List[Tuple[float, float]] = []
        for leg in rt.get("legs", []):
            # Prefer decoded shape if available; otherwise decode polyline5
            if "shape" in leg and isinstance(leg["shape"], list):
                coords.extend([(pt[0], pt[1]) for pt in leg["shape"]])
            elif "shape" in leg and isinstance(leg["shape"], str):
                # Polyline5 decode (lon,lat). Implement quick decoder
                coords.extend(polyline5_decode(leg["shape"]))
        if coords:
            routes.append(coords)
    return routes


# Polyline5 decoder (lon, lat) for Valhalla
# Adapted minimal implementation

def polyline5_decode(encoded: str) -> List[Tuple[float, float]]:
    coords = []
    index = 0
    lat = 0
    lon = 0
    while index < len(encoded):
        result = 1
        shift = 0
        b = 0
        while True:
            b = ord(encoded[index]) - 63 - 1
            index += 1
            result += b << shift
            shift += 5
            if b < 0x1f:
                break
        dlat = ~(result >> 1) if (result & 1) else (result >> 1)
        lat += dlat
        result = 1
        shift = 0
        while True:
            b = ord(encoded[index]) - 63 - 1
            index += 1
            result += b << shift
            shift += 5
            if b < 0x1f:
                break
        dlng = ~(result >> 1) if (result & 1) else (result >> 1)
        lon += dlng
        coords.append((lon * 1e-5, lat * 1e-5))
    return coords


# -----------------------------
# Public API
# -----------------------------

def score_routes(
    origin_lonlat: Tuple[float, float],
    dest_lonlat: Tuple[float, float],
    raster_paths: List[str],
    tau_distance_threshold: float = 0.15,
    weights: Tuple[float, float, float] = (0.4, 0.4, 0.2),
    max_alternates: int = 4,
) -> Dict[str, Any]:
    """Fetch routes from Valhalla, compute metrics, and pick 3 options."""
    resp = valhalla_route_with_alternates(origin_lonlat, dest_lonlat, max_alternates=max_alternates)
    route_coords_list = extract_route_coords(resp)

    sampler = ElevationSampler(raster_paths)

    metrics: List[RouteMetrics] = []
    for i, coords in enumerate(route_coords_list):
        # Resample profile directly on 10 ft-resampled coords inside compute_metrics
        # So sample elevations on those resampled coords
        # First create a quick metrics pass to get resampled coords
        ls_ll = LineString(coords)
        ls_m = transform(PROJECT_TO_M, ls_ll)
        rs_m = resample_linestring_metric(ls_m, TEN_FT_IN_M)
        rs_ll = transform(PROJECT_TO_LL, rs_m)
        rs_coords = list(rs_ll.coords)
        elevs = sampler.sample_profile(rs_coords)
        m = compute_metrics_for_coords(rs_coords, elevs, name=f"route_{i+1}")
        metrics.append(m)

    params = SelectionParams(distance_threshold_tau=tau_distance_threshold,
                             w_distance=weights[0], w_abs_gain=weights[1], w_smooth=weights[2])
    picks = pick_routes(metrics, params)

    return {
        "params": {
            "tau": tau_distance_threshold,
            "weights": {"distance": weights[0], "abs_gain": weights[1], "smooth": weights[2]},
            "max_alternates": max_alternates,
        },
        "all_routes": [m.as_dict() for m in metrics],
        "choices": {k: v.as_dict() for k, v in picks.items()},
    }


if __name__ == "__main__":
    # Example usage (Seattle City Hall to UW): lon, lat
    origin = (-122.3316, 47.6062)
    dest = (-122.3035, 47.6553)
    rasters = [
        # Put your local DEMs here; examples:
        # "data/dem/N47_W122.hgt",
        # "data/dem/N47_W123.hgt",
    ]
    result = score_routes(origin, dest, rasters, tau_distance_threshold=0.15, weights=(0.45, 0.4, 0.15), max_alternates=4)
    print(json.dumps(result, indent=2))
