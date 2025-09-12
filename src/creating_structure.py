# Represents an intersection (or endpoint of a street segment).
class Node:
    def __init__(self, node_id, lat, lon, elevation=None):
        self.id = node_id
        self.lat = lat
        self.lon = lon
        self.elevation = elevation  # sampled directly at the node
        self.edges = []  # list of connected Edge objects

# Represents a street segment between two intersections.
class Edge:
    def __init__(self, start_node, end_node, shape_points):
        self.start = start_node      # Node object
        self.end = end_node          # Node object
        self.shape = shape_points    # list of (lat, lon) along the street
        self.distance = None         # meters (computed from shape)
        
        # Elevation profile (sampled every ~5m)
        self.elevations = []         # list of elevation values
        self.slopes = []             # slope % between consecutive samples
        
        # Derived metrics
        self.elevation_gain = 0      # sum of uphill rises only
        self.max_slope = 0           # steepest slope %
        self.avg_slope = 0           # mean slope %
    
    def compute_metrics(self, elevation_sampler, step=5):
        """
        - Resample shape points at 'step' meter intervals
        - Use elevation_sampler(lat, lon) to fill self.elevations
        - Compute slopes, elevation gain, max slope, avg slope
        """
        pass


# Holds all nodes and edges, and lets us run Dijkstra/A* with different cost functions.
class Graph:
    def __init__(self):
        self.nodes = {}  # node_id → Node
        self.edges = []  # list of Edge objects
    
    def add_node(self, node_id, lat, lon):
        if node_id not in self.nodes:
            self.nodes[node_id] = Node(node_id, lat, lon)
        return self.nodes[node_id]
    
    def add_edge(self, start_node, end_node, shape_points):
        edge = Edge(start_node, end_node, shape_points)
        self.edges.append(edge)
        start_node.edges.append(edge)
        return edge

# Each edge gets a cost depending on the chosen mode:
def cost_shortest(edge):
    return edge.distance

def cost_flattest(edge):
    return edge.elevation_gain

def cost_optimized(edge, alpha=0.5, beta=0.5):
    return alpha * edge.distance + beta * edge.elevation_gain

# To hold final path results:
class Route:
    def __init__(self, nodes, edges):
        self.nodes = nodes
        self.edges = edges
        self.distance = sum(e.distance for e in edges)
        self.elevation_gain = sum(e.elevation_gain for e in edges)
        self.max_slope = max(e.max_slope for e in edges)
        self.avg_slope = (self.elevation_gain / self.distance) * 100 if self.distance > 0 else 0
        self.polyline = [ (n.lat, n.lon) for n in nodes ]
