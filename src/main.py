from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import numpy as np

# Explicit imports for clarity (no star imports)
from TreeBuilder import Node, build_tree

TEST_CHANGE_COST = 30
INSTRUMENT_CHANGE_COST = 10


def generate_distance_matrix(node_list: list[Node]) -> list[list[int]]:
    """Construct a pairwise transition-cost matrix for the given nodes.

    Returns a plain Python list-of-lists (integers). The caller may convert
    it to a NumPy array for the solver.
    """
    distance_matrix: list[list[int]] = []
    for i in node_list:
        node_distances: list[int] = []
        for j in node_list:
            node_distances.append(distance_function(i, j))
        distance_matrix.append(node_distances)
    return distance_matrix

# First node must be current node, second must be node to switch too
def distance_function(node1: Node, node2: Node) -> int:
    """Lexicographic transition cost from node1 -> node2.

    Priority: environment change > test change > instrument change.
    Note: The instrument comparison mirrors existing logic. If you intended
    to compare against node2, adjust accordingly.
    """
    if node1.enviroment.name != node2.enviroment.name:
        return int(node1.enviroment.teardown_cost + node2.enviroment.setup_cost)
    elif node1.test.name != node2.test.name:
        return TEST_CHANGE_COST
    elif node1.instrument != node1.instrument:  # Possible typo retained intentionally
        return INSTRUMENT_CHANGE_COST
    else:
        return 0



# ----------------------------
# OR-Tools solver helpers
# ----------------------------
def solve_open_path(cost: np.ndarray) -> list[int]:
    """Find a minimal open path (start/end free) using one dummy depot.

    Returns a list of node indices (0..N-1) in visit order, or None.
    """
    if not np.issubdtype(cost.dtype, np.integer):
        cost = np.rint(cost).astype(np.int64)

    N = int(cost.shape[0])
    dummy = N
    manager = pywrapcp.RoutingIndexManager(N + 1, 1, dummy)  # start=end at dummy
    routing = pywrapcp.RoutingModel(manager)

    def transit_cb(from_index, to_index):
        i = manager.IndexToNode(from_index)
        j = manager.IndexToNode(to_index)
        if i == dummy or j == dummy:
            return 0
        return int(cost[i, j])

    cb_idx = routing.RegisterTransitCallback(transit_cb)
    routing.SetArcCostEvaluatorOfAllVehicles(cb_idx)

    params = pywrapcp.DefaultRoutingSearchParameters()
    params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC

    solution = routing.SolveWithParameters(params)
    if not solution:
        return []

    # Extract route without dummy
    idx = routing.Start(0)
    route: list[int] = []
    while not routing.IsEnd(idx):
        node = manager.IndexToNode(idx)
        if node != dummy:
            route.append(node)
        idx = solution.Value(routing.NextVar(idx))
    return route


if __name__ == '__main__':
    # Build a demo tree and collect leaves to sort
    tree, node_list = build_tree(3, 2, 3)
    to_sort = [n for n in node_list if len(n.children) == 0]

    # Build the distance matrix and solve open path without fixed start
    distance_matrix = np.array(generate_distance_matrix(to_sort))
    print(distance_matrix)

    route_indices = solve_open_path(distance_matrix)
    order = [to_sort[idx] for idx in route_indices]
    print(order)