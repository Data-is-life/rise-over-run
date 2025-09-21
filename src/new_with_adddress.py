import requests, polyline, numpy as np, matplotlib.pyplot as plt
from heapq import heappush, heappop
import rasterio
from pyproj import Geod

# --------------------------
# Elevation Sampler
# --------------------------

class ElevationSampler:
    def __init__(self, hgt_files):
        self.datasets = [rasterio.open(f) for f in hgt_files]

    def get_elevation(self, lat, lon):
        for ds in self.datasets:
            if (ds.bounds.left <= lon <= ds.bounds.right and
                ds.bounds.bottom <= lat <= ds.bounds.top):
                height, width = ds.shape
                row, col = ds.index(lon, lat)
                row = min(max(row, 0), height-1)  # clamp
                col = min(max(col, 0), width-1)
                value = ds.read(1)[row, col]
                if value == -32768:  # voids
                    return None
                return int(value)
        return None

# --------------------------
# Graph Structures
# --------------------------

class Node:
    def __init__(self, node_id, lat, lon):
        self.id = node_id
        self.lat = lat
        self.lon = lon
        self.edges = []

class Edge:
    def __init__(self, start, end, shape_points, elevation_sampler, step=5):
        self.start = start
        self.end = end
        self.shape = shape_points
        self.distance, self.elevations, self.slopes = self._sample_profile(elevation_sampler, step)
        self.elevation_gain = sum(max(0, self.elevations[i+1] - self.elevations[i]) for i in range(len(self.elevations)-1))
        self.max_slope = max(self.slopes) if self.slopes else 0
        self.avg_slope = np.mean(self.slopes) if self.slopes else 0

    def _sample_profile(self, sampler, step):
        geod = Geod(ellps="WGS84")
        elevs, dists, slopes = [], [], []
        total_dist = 0

        for i in range(len(self.shape)-1):
            lat1, lon1 = self.shape[i]
            lat2, lon2 = self.shape[i+1]

            # skip identical points
            if lat1 == lat2 and lon1 == lon2:
                continue

            seg_len = geod.line_length([lon1, lon2], [lat1, lat2])

            # skip NaN or nonsense values
            if np.isnan(seg_len) or seg_len <= 0:
                continue

            steps = max(1, int(seg_len // step))
            lats = np.linspace(lat1, lat2, steps+1)
            lons = np.linspace(lon1, lon2, steps+1)

            for j in range(len(lats)):
                e = sampler.get_elevation(lats[j], lons[j])
                if e is not None:
                    elevs.append(e)
                    dists.append(total_dist + (j/steps)*seg_len)

            total_dist += seg_len

        # slopes
        for i in range(len(elevs)-1):
            run = dists[i+1] - dists[i]
            rise = elevs[i+1] - elevs[i]
            slopes.append((rise/run)*100 if run > 0 else 0)

        return total_dist, elevs, slopes


# --------------------------
# Cost Functions
# --------------------------

def cost_shortest(edge): return edge.distance
def cost_flattest(edge): return edge.elevation_gain
def cost_optimized(edge, alpha=0.5, beta=0.5):
    return alpha*edge.distance + beta*edge.elevation_gain

# --------------------------
# Dijkstra
# --------------------------

def dijkstra(start, end, cost_function):
    pq, counter = [], 0
    heappush(pq,(0,counter,start,[],[]))
    best_cost = {start.id:0}
    while pq:
        cost,_,node,path_nodes,path_edges = heappop(pq)
        if node.id == end.id:
            return path_nodes+[node], path_edges
        for edge in node.edges:
            neighbor=edge.end
            new_cost=cost+cost_function(edge)
            if neighbor.id not in best_cost or new_cost<best_cost[neighbor.id]:
                best_cost[neighbor.id]=new_cost
                counter+=1
                heappush(pq,(new_cost,counter,neighbor,path_nodes+[node],path_edges+[edge]))
    return None,None

# --------------------------
# Helpers
# --------------------------

def summarize(path_nodes,path_edges):
    if not path_nodes: return "No route"
    dist=sum(e.distance for e in path_edges)
    gain=sum(e.elevation_gain for e in path_edges)
    return f"Distance={dist:.1f}m | Elev Gain={gain:.1f}m"

def build_profile(path_edges):
    d,e=[],[]
    offset=0
    for edge in path_edges:
        d.extend([x+offset for x in range(len(edge.elevations))])
        e.extend(edge.elevations)
        offset+=edge.distance
    return d,e

def plot_profiles(routes):
    plt.figure(figsize=(9,6))
    for label,(nodes,edges) in routes.items():
        if nodes:
            d,e=build_profile(edges)
            plt.plot(d,e,label=f"{label} ({summarize(nodes,edges)})")
    plt.xlabel("Distance (m)")
    plt.ylabel("Elevation (m)")
    plt.title("Seattle Routes: Elevation Profiles")
    plt.legend()
    plt.grid(True)
    plt.show()

# --------------------------
# Main
# --------------------------

if __name__ == "__main__":
    # addresses → coords
    start = [-122.3365,47.6095]
    end = [-122.3235,47.6057]

    # query Valhalla
    payload = {"locations":[{"lon":start[0],"lat":start[1]},{"lon":end[0],"lat":end[1]}],
             "costing":"pedestrian","alternates":0}
    r = requests.post("http://localhost:8002/route",json=payload)
    data = r.json()
    shape = polyline.decode(data["trip"]["legs"][0]["shape"], precision=6) # (lat,lon)
    print("First 5 polyline points:", shape[:5])

    if "alternates" in data["trip"]:
        for alt in data["trip"]["alternates"]:
            alt_shape = polyline.decode(alt["legs"][0]["shape"])

    # build simple graph (just start→end edge for now)
    sampler = ElevationSampler(["N47W122.hgt","N47W123.hgt"])
    start_node = Node(1,start[1],start[0])
    end_node = Node(2,end[1],end[0])
    edge = Edge(start_node,end_node,shape,sampler,step=5)
    start_node.edges.append(edge)

    # run routing modes
    routes={}
    routes["Shortest"]=dijkstra(start_node,end_node,cost_shortest)
    routes["Flattest"]=dijkstra(start_node,end_node,cost_flattest)
    routes["Optimized"]=dijkstra(start_node,end_node,lambda e: cost_optimized(e,0.8,0.2))

    for label,(nodes,edges) in routes.items():
        print(label,":",summarize(nodes,edges))

    # plot
    plot_profiles(routes)