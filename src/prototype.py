from heapq import heappush, heappop

# --------------------------
# Basic Graph Structures
# --------------------------

class Node:
    def __init__(self, node_id, name):
        self.id = node_id
        self.name = name
        self.edges = []

class Edge:
    def __init__(self, start, end, distance, elevation_gain):
        self.start = start
        self.end = end
        self.distance = distance
        self.elevation_gain = elevation_gain

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
# Dijkstra Implementation
# --------------------------

def dijkstra(start, end, cost_function):
    pq = []
    heappush(pq, (0, start, [], []))  # cost, node, path_nodes, path_edges
    best_cost = {start.id: 0}
    
    while pq:
        cost, node, path_nodes, path_edges = heappop(pq)
        
        if node.id == end.id:
            return path_nodes + [node], path_edges
        
        for edge in node.edges:
            neighbor = edge.end
            new_cost = cost + cost_function(edge)
            
            if neighbor.id not in best_cost or new_cost < best_cost[neighbor.id]:
                best_cost[neighbor.id] = new_cost
                heappush(pq, (new_cost, neighbor, path_nodes + [node], path_edges + [edge]))
    
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
    Edge(A, C, 150, 5),    # gentle
    Edge(B, D, 200, 0),    # flat
    Edge(C, D, 150, 15),   # moderate
    Edge(C, B, 100, 5)     # connector
]

# connect nodes
for e in edges:
    e.start.edges.append(e)

# --------------------------
# Run Routing Modes
# --------------------------

def summarize(path_nodes, path_edges):
    if not path_nodes: return "No route"
    route_str = " → ".join([n.name for n in path_nodes])
    dist = sum(e.distance for e in path_edges)
    gain = sum(e.elevation_gain for e in path_edges)
    return f"{route_str} | Distance={dist}m | Elevation Gain={gain}m"

# Shortest
nodes, edges_used = dijkstra(A, D, cost_shortest)
print("Shortest Path:", summarize(nodes, edges_used))

# Flattest
nodes, edges_used = dijkstra(A, D, cost_flattest)
print("Flattest Path:", summarize(nodes, edges_used))

# Optimized (50/50)
nodes, edges_used = dijkstra(A, D, lambda e: cost_optimized(e, 0.5, 0.5))
print("Optimized Path:", summarize(nodes, edges_used))
