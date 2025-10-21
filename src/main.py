from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import numpy as np
from TreeBuilder import Node, build_tree
from stone_visuals import plot_schedule_visuals
import sys
import argparse

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

def get_parents(visited: list[Node]) -> list[Node]:
    """Return parents whose children are all already in visited.

    Uses ids to avoid identity issues; skips None parents.
    """
    visited_ids = {n.id for n in visited}

    candidate_parents: list[Node] = []
    for n in visited:
        p = n.parent
        if p is None:
            continue
        if (p.id not in visited_ids) and (p not in candidate_parents):
            candidate_parents.append(p)

    return [p for p in candidate_parents if all(c.id in visited_ids for c in p.children)]


def get_first_insert(child_list: list[Node], parent_list: list[Node]):
    """Pick the parent with the smallest largest child index.

    Example: if a parent’s children occur in child_list at indices [2, 3, 1],
    that parent’s score is max([2,3,1]) == 3. Compute this score for every
    parent and return the parent with the minimal score. Parents with no
    children in child_list are ignored. Returns None if none qualify.
    """
    # Fast lookup of positions in the ordered child list
    position = {n.id: i for i, n in enumerate(child_list)}

    best_parent: Node | None = None
    best_max_idx: int | None = None

    for parent in parent_list:
        indices = [position[c.id] for c in parent.children if c.id in position]
        if not indices:
            continue
        latest = max(indices)
        if best_max_idx is None or latest < best_max_idx:
            best_max_idx = latest
            best_parent = parent

    return (best_parent, best_max_idx)


def print_tree(root: Node) -> None:
    """Pretty-print the node tree using Unicode when possible, ASCII otherwise.

    Each line shows: ID, environment, and test.
    """
    # Decide on symbol set based on console encoding capabilities
    try:
        enc = sys.stdout.encoding or "utf-8"
        "└".encode(enc)
        branch_sym = "├─ "
        last_sym = "└─ "
        vertical_sym = "│  "
        space_sym = "   "
    except Exception:
        branch_sym = "+- "
        last_sym = "`- "
        vertical_sym = "|  "
        space_sym = "   "

    def _visit(node: Node, prefix: str, is_last: bool) -> None:
        connector = last_sym if is_last else branch_sym
        label = f"ID:{node.id} env={node.enviroment.name} test={node.test.name}"
        if prefix:
            print(prefix + connector + label)
        else:
            print(label)
        new_prefix = prefix + (space_sym if is_last else vertical_sym)
        for i, child in enumerate(node.children):
            _visit(child, new_prefix, i == len(node.children) - 1)

    _visit(root, "", True)


def schedule_by_environment(ordered: list[Node]):
    """Compress schedule by environment while respecting child-before-parent.

    Returns (day_map, env_schedule):
      - day_map: node.id -> assigned integer day (0-based)
      - env_schedule: env.name -> list[(day, node)] sorted by day
    Assumptions:
      - Multiple environments can run in parallel on the same day.
      - Within a single environment, at most one node per day (we compact).
    """
    # Initial day assignment: current linear order
    day = {n.id: i for i, n in enumerate(ordered)}

    # Group nodes by environment
    env_to_nodes: dict[str, list[Node]] = {}
    for n in ordered:
        env_to_nodes.setdefault(n.enviroment.name, []).append(n)

    changed = True
    while changed:
        changed = False
        # Pass 1: per-environment packing by earliest feasible day (EFD)
        for env, nodes in env_to_nodes.items():
            items = []
            for n in nodes:
                efd = max((day[c.id] for c in n.children), default=-1) + 1
                latest = day[n.parent.id] - 1 if n.parent else float('inf')
                items.append((n, efd, latest))

            # Sort by earliest-feasible day, then current day as tie-breaker
            items.sort(key=lambda t: (t[1], day[t[0].id]))

            last_env_day = -1
            for n, efd, latest in items:
                # If infeasible window, skip for now (later passes may relax via parent push)
                if efd > latest:
                    last_env_day = max(last_env_day, day[n.id])
                    continue

                target = max(last_env_day + 1, efd)
                if target != day[n.id]:
                    day[n.id] = int(target)
                    changed = True
                last_env_day = max(last_env_day, day[n.id])

        # Pass 2: enforce precedence strictly (parent after children)
        for n in ordered:
            if n.parent is None:
                continue
            need = day[n.id] + 1
            if day[n.parent.id] < need:
                day[n.parent.id] = need
                changed = True

        # Pass 3: fix per-environment collisions by pushing later
        for env, nodes in env_to_nodes.items():
            nodes_sorted = sorted(nodes, key=lambda x: day[x.id])
            last = -1
            for n in nodes_sorted:
                if day[n.id] <= last:
                    day[n.id] = last + 1
                    changed = True
                last = day[n.id]

    env_schedule: dict[str, list[tuple[int, Node]]] = {}
    for env, nodes in env_to_nodes.items():
        env_schedule[env] = sorted(((day[n.id], n) for n in nodes), key=lambda t: t[0])

    return day, env_schedule


def print_schedule_grid(env_schedule: dict[str, list[tuple[int, Node]]]):
    """Print a padded grid: columns=environments, rows=days (fixed-width)."""
    envs = sorted(env_schedule.keys())
    if not envs:
        print("(no environments)")
        return

    # Build lookup and track max day
    lookup: dict[tuple[str, int], Node] = {}
    max_day = 0
    for env in envs:
        for d, n in env_schedule[env]:
            lookup[(env, d)] = n
            if d > max_day:
                max_day = d

    # Compute column widths
    day_width = max(3, len(str(max_day)))
    col_widths: dict[str, int] = {}
    for env in envs:
        cell_max = len(env)
        for d in range(0, max_day + 1):
            n = lookup.get((env, d))
            cell_str = f"ID:{n.id}" if n else "-"
            if len(cell_str) > cell_max:
                cell_max = len(cell_str)
        col_widths[env] = cell_max

    # Header
    header = ["Day".rjust(day_width)] + [env.ljust(col_widths[env]) for env in envs]
    print(" ".join(header))

    # Rows
    for d in range(0, max_day + 1):
        cells = [str(d).rjust(day_width)]
        for env in envs:
            n = lookup.get((env, d))
            cell = f"ID:{n.id}" if n else "-"
            cells.append(cell.ljust(col_widths[env]))
        print(" ".join(cells))


def validate_schedule(visited: list[Node], initial_nodes: list[Node], day_map: dict[int, int] | None = None) -> bool:
    """Validate that all leaves remain present and children precede parents.

    Checks:
      - Every node from initial_nodes exists in visited.
      - In linear order (visited), each child appears before its parent.
      - If day_map is provided, each child day < parent day.

    Prints a concise report and returns True if all checks pass.
    """
    ok = True
    errors: list[str] = []

    # Presence of initial leaves
    pos = {n.id: i for i, n in enumerate(visited)}
    missing = [n.id for n in initial_nodes if n.id not in pos]
    if missing:
        ok = False
        errors.append(f"Missing initial node ids in visited: {sorted(missing)}")

    # Child-before-parent in order
    for n in visited:
        p_idx = pos[n.id]
        for c in n.children:
            c_idx = pos.get(c.id)
            if c_idx is None:
                ok = False
                errors.append(f"Child {c.id} of parent {n.id} not present in visited")
            elif c_idx >= p_idx:
                ok = False
                errors.append(f"Order violation: child {c.id} (idx {c_idx}) after parent {n.id} (idx {p_idx})")

    # Day schedule constraint
    if day_map is not None:
        for n in visited:
            p_day = day_map[n.id]
            for c in n.children:
                c_day = day_map[c.id]
                if c_day >= p_day:
                    ok = False
                    errors.append(f"Day violation: child {c.id} (day {c_day}) not before parent {n.id} (day {p_day})")

    if ok:
        print("Validation passed: leaves present and precedence holds" + (" (by day)" if day_map is not None else ""))
    else:
        print("VALIDATION FAILURES:")
        for e in errors:
            print(" - " + e)
        raise Exception
    return ok

if __name__ == '__main__':
    # Parse optional CLI arguments to flexibly control tree shape
    parser = argparse.ArgumentParser(description='Build tree and schedule tests.')
    parser.add_argument('--depth', type=int, default=5, help='Tree depth (levels of children)')
    parser.add_argument('--min-child', type=int, default=1, help='Minimum children per node')
    parser.add_argument('--max-child', type=int, default=3, help='Maximum children per node')
    parser.add_argument('--show-plots', action='store_true', help='Display Matplotlib figures in addition to saving files')
    args = parser.parse_args()

    # Build a tree and collect leaves to sort
    tree, node_list = build_tree(args.depth, args.min_child, args.max_child)

    # Print the tree structure (IDs with env and test) for inspection
    #print("Tree structure (child hierarchy):")
    #print_tree(tree)
    #print()



    initial_nodes = [n for n in node_list if len(n.children) == 0]

<<<<<<< HEAD
    # Build the distance matrix and solve open path without fixed start
    distance_matrix = np.array(generate_distance_matrix(initial_nodes))
    route_indices = solve_open_path(distance_matrix)
    order = [initial_nodes[idx] for idx in route_indices] if route_indices else list(initial_nodes)

    visited = list(order)
    to_visit = get_parents(visited)

    while True:
        if len(to_visit) == 0:
            break

        insert_node, insert_pos = get_first_insert(visited, to_visit)
        if insert_node is None or insert_pos is None:
            # No valid insert candidate; prevent infinite loop
            break

        # Stable insertion: place parent immediately after its latest child
        visited.insert(insert_pos + 1, insert_node)

        # Update candidates and continue upward
        to_visit = get_parents(visited)

    # Build compressed per-environment schedule
    day_map, env_schedule = schedule_by_environment(visited)

    # Validate constraints
    validate_schedule(visited, initial_nodes, day_map)

    # Show schedule
    print_schedule_grid(env_schedule)

    # Generate visualizations from the computed schedule
    plot_schedule_visuals(visited, day_map, out_dir="./out_viz", show=args.show_plots)
=======
    # Build the distance matrix and solve 
    distance_matrix = np.array(generate_distance_matrix(to_sort))
    print(distance_matrix)

    route_indices = solve_open_path(distance_matrix)
    order = [to_sort[idx] for idx in route_indices]
    print(order)
>>>>>>> 89dbec04ff3940ce47a1cda3996cd0184159755b
