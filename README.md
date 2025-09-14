# Rise Over Run

Rise Over Run is a walking route optimization project designed to help pedestrians find routes that minimize steep climbs in hilly cities like San Francisco and Seattle. Instead of only showing the shortest or fastest path, Rise Over Run surfaces alternatives such as the flattest route or the best compromise between distance and slope.

---
### 🚀 Features (Work So Far)
1. Routing Engine (Valhalla)
   * Self-hosted Valhalla instance running with OSM extracts.
   * Configured with custom JSON settings to allow multiple alternate routes.
2. Elevation Integration
   * Local SRTM/HGT data loaded to provide elevation profiles.
   * Python scripts to fetch and compare elevation gain/loss along routes.
   * Verified elevation sampling at ~5–15 ft resolution.
3. Prototype Analysis
   * Compare multiple walking routes between start and end points.
   * Plot elevation profiles using Matplotlib.
   * Identify steep sections and calculate total elevation gain.
---
🏗️ Final Project Vision
1. Route Types
   * Shortest Route (baseline).
   * Flattest Route (least elevation gain).
   * Optimized Route (balance between slope and distance).
2. Slope-Aware Intersections
   * Calculate slope at each street intersection.
   * Use this information to re-evaluate possible turns dynamically.
3. Local, Self-Sufficient System
   * Fully offline routing and elevation service (Valhalla + DEM data).
   * No dependency on Google Maps or commercial APIs.
4. Algorithmic Approach
   * Start with Dijkstra/A* on Valhalla’s graph.
   * Overlay elevation gain per 5m segment.
   * Compute multi-objective optimization (distance vs. slope).
---
### ⚙️ Setup & Installation

1. Clone this repo:
```
git clone https://github.com/yourusername/rise-over-run.git
cd rise-over-run
```
2. Build and run Valhalla with OSM + elevation data:
```
mkdir -p data/osm
wget https://download.geofabrik.de/north-america/us/washington-latest.osm.pbf -O data/osm/washington.osm.pbf

# Build Valhalla Docker image
git submodule update --init --recursive
docker build -t valhalla -f docker/Dockerfile .
docker run -it -p 8002:8002 valhalla
```
3. Run the Python prototype:
```
pip install -r requirements.txt
python prototype.py
```
---
### Example Output
1. Multiple alternate walking routes.
2. Elevation profile charts.
3. Comparison of distance vs. elevation gain.
---
### 🔮 Roadmap
- [ ] Implement slope-aware intersection analysis.
- [ ] Add “optimized route” mode (distance + slope).
- [ ] Build minimal Flask/FastAPI service for route requests.
- [ ] Deploy demo web app with interactive map.
- [ ] Expand to additional cities.
- [ ] Mobile app integration (iOS).
---
### 🤝 Contributing

Contributions welcome! Please open issues and PRs for feature ideas, bug reports, or new datasets.

---
### 📜 License

This repository (prototype code, research scripts, and supporting materials) is released under the MIT License – free to use, modify, and distribute.
The production app (mobile and web) will remain proprietary and closed-source to protect commercial use and long-term sustainability of the project.
