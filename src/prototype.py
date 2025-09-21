import matplotlib.pyplot as plt
import numpy as np
from heapq import heappush, heappop

# --------------------------
# Graph Structures
# --------------------------

class Node:
    def __init__(self, node_id, name):
        self.id = node_id
        self.name = name
        self.edges = []

class Edge:
    def __init__(self, start, end, distance, elevation_gain, steps=10):
        self.start = start
        self.end = end
        self.distance = distance
        self.elevation_gain = elevation_gain

        # simple linear elevation profile for demo
        self.elevations = np.linspace(0, elevation_gain, steps).tolist()
        self.distances = np.linspace(0, distance, steps).tolist()

# --------------------------
# Cost Functions
# --------------------------

def cost_shortest(edge):
    return edge.distance

def cost_flattest(edge):
    return edge.elevation_gain

def cost_optimized(edge, alpha=0.5, beta=0.5):
    return alpha * edge.distance + beta * edge.elevation_gain

# --------------------------
# Dijkstra
# --------------------------

def dijkstra(start, end, cost_function):
    pq = []
    counter = 0
    heappush(pq, (0, counter, start, [], []))
    best_cost = {start.id: 0}
    
    while pq:
        cost, _, node, path_nodes, path_edges = heappop(pq)
        
        if node.id == end.id:
            return path_nodes + [node], path_edges
        
        for edge in node.edges:
            neighbor = edge.end
            new_cost = cost + cost_function(edge)
            
            if neighbor.id not in best_cost or new_cost < best_cost[neighbor.id]:
                best_cost[neighbor.id] = new_cost
                counter += 1
                heappush(pq, (new_cost, counter, neighbor,
                              path_nodes + [node], path_edges + [edge]))
    return None, None

# --------------------------
# Build Toy Graph
# --------------------------

A = Node(1, "A")
B = Node(2, "B")
C = Node(3, "C")
D = Node(4, "D")

edges = [
    Edge(A, B, 100, 20),   # steep uphill
    Edge(A, C, 150, 5),    # gentle incline
    Edge(B, D, 200, 0),    # flat
    Edge(C, D, 150, 15),   # moderate climb
    Edge(C, B, 100, 5)     # connector
]

for e in edges:
    e.start.edges.append(e)

# --------------------------
# Route Utilities
# --------------------------

def summarize(path_nodes, path_edges):
    if not path_nodes: return "No route"
    route_str = " → ".join([n.name for n in path_nodes])
    dist = sum(e.distance for e in path_edges)
    gain = sum(e.elevation_gain for e in path_edges)
    return f"{route_str} | Distance={dist}m | Elevation Gain={gain}m"

def build_elevation_profile(path_edges):
    dist_accum = 0
    dists = []
    elevs = []
    for e in path_edges:
        # offset each edge's distances by cumulative length
        dists.extend([d + dist_accum for d in e.distances])
        elevs.extend(np.cumsum(e.elevations) - e.elevations[0])  # ensure relative climb
        dist_accum += e.distance
    return dists, elevs

def plot_profile(path_nodes, path_edges, label):
    d, e = build_elevation_profile(path_edges)
    plt.plot(d, e, label=label)

# --------------------------
# Run & Plot
# --------------------------

routes = {}

# Shortest
nodes, edges_used = dijkstra(A, D, cost_shortest)
routes["Shortest"] = (nodes, edges_used)
print("Shortest Path:", summarize(nodes, edges_used))

# Flattest
nodes, edges_used = dijkstra(A, D, cost_flattest)
routes["Flattest"] = (nodes, edges_used)
print("Flattest Path:", summarize(nodes, edges_used))

# Optimized (α=0.5, β=0.5)
nodes, edges_used = dijkstra(A, D, lambda e: cost_optimized(e, 0.5, 0.5))
routes["Optimized"] = (nodes, edges_used)
print("Optimized Path:", summarize(nodes, edges_used))

# Plot
plt.figure(figsize=(8,5))
for label, (nodes, edges) in routes.items():
    plot_profile(nodes, edges, label)

plt.xlabel("Distance (m)")
plt.ylabel("Elevation (m)")
plt.title("Elevation Profiles of Routes")
plt.legend()
plt.grid(True)
plt.show()

# --------------------------
# Test different alpha/beta weights
# --------------------------

def test_weights(start, end, alphas, betas):
    for alpha in alphas:
        for beta in betas:
            nodes, edges_used = dijkstra(
                start,
                end,
                lambda e: cost_optimized(e, alpha, beta)
            )
            route = summarize(nodes, edges_used)
            print(f"α={alpha:.2f}, β={beta:.2f} → {route}")


# --------------------------
# Run Tests
# --------------------------

print("\n=== Optimized Path Experiments ===")
alphas = [0.2, 0.5, 0.8]   # distance importance
betas  = [0.2, 0.5, 0.8]   # elevation importance

test_weights(A, D, alphas, betas)

