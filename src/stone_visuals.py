import os
import random
from dataclasses import dataclass
from typing import List, Dict, Tuple
import matplotlib.pyplot as plt
import numpy as np


# DATA CLASSES (represent our fake objects)
@dataclass
class TestType:
    """
    Represents a verification test type with cost and duration.
    """
    name: str
    cost: float
    duration: float


@dataclass
class Environment:
    """
    Represents a testing environment with costs for setup, teardown, and operation.
    """
    name: str
    hourly_cost: float
    setup_cost: float
    teardown_cost: float


# FAKE DATA GENERATION FUNCTIONS
def generate_test_data(num_tests: int = 8) -> Dict[str, TestType]:
    """
    Creates fake test data to simulate verification activities.
    Each test has a random cost and duration.
    """
    rng = random.Random(42)  # consistent random seed for reproducibility
    test_data = {}

    for i in range(num_tests):
        name = f"Test_{i+1}"
        test_data[name] = TestType(
            name=name,
            cost=rng.randint(3000, 20000),   # test cost in dollars
            duration=rng.randint(2, 12)      # duration in hours
        )
    return test_data


def generate_environment_data(num_envs: int = 5) -> Dict[str, Environment]:
    """
    Creates fake environment data to represent different test setups.
    Each environment has setup, teardown, and hourly operational costs.
    """
    rng = random.Random(123)
    env_data = {}

    for i in range(num_envs):
        name = f"Env_{i+1}"
        env_data[name] = Environment(
            name=name,
            hourly_cost=rng.randint(400, 3000),
            setup_cost=rng.randint(1000, 8000),
            teardown_cost=rng.randint(1000, 8000)
        )
    return env_data


def generate_transition_matrix(envs: List[str]) -> np.ndarray:
    """
    Builds a matrix that represents the 'transition cost' from one environment to another.
    Used for heatmap visualization.
    """
    rng = np.random.default_rng(101)
    n = len(envs)
    matrix = rng.integers(100, 5000, size=(n, n)).astype(float)
    np.fill_diagonal(matrix, 0)  # zero out self-transitions
    return matrix


# VISUALIZATION FUNCTIONS
def plot_heatmap(matrix: np.ndarray, labels: List[str], out_path: str, show: bool = False):
    """
    Creates a heatmap that visualizes environment-to-environment transition costs.
    """
    plt.figure(figsize=(8, 6))
    plt.imshow(matrix, cmap='viridis')
    plt.colorbar(label="Changeover Cost ($)")
    plt.xticks(ticks=np.arange(len(labels)), labels=labels, rotation=45)
    plt.yticks(ticks=np.arange(len(labels)), labels=labels)
    plt.title("Environment Changeover Cost Heatmap")
    plt.tight_layout()
    plt.savefig(out_path)
    if not show:
        plt.close()


def plot_histograms(test_data: Dict[str, TestType], env_data: Dict[str, Environment], out_dir: str, show: bool = False):
    """
    Plots three histograms:
      - Test cost distribution
      - Test duration distribution
      - Environment cost breakdown (hourly, setup, teardown)
    """
    os.makedirs(out_dir, exist_ok=True)

    # 1) Test Cost Distribution
    plt.figure(figsize=(6, 4))
    plt.hist([t.cost for t in test_data.values()], bins=10, color='blue', alpha=0.7)
    plt.title("Test Cost Distribution")
    plt.xlabel("Cost ($)")
    plt.ylabel("Frequency")
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "test_cost_hist.png"))
    if not show:
        plt.close()

    # 2) Test Duration Distribution
    plt.figure(figsize=(6, 4))
    plt.hist([t.duration for t in test_data.values()], bins=8, color='orange', alpha=0.7)
    plt.title("Test Duration Distribution")
    plt.xlabel("Duration (hours)")
    plt.ylabel("Frequency")
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "test_duration_hist.png"))
    if not show:
        plt.close()

    # 3) Environment Cost Breakdown (Total and % by factor) — Pie
    hourly_sum = float(sum(e.hourly_cost for e in env_data.values()))
    setup_sum = float(sum(e.setup_cost for e in env_data.values()))
    teardown_sum = float(sum(e.teardown_cost for e in env_data.values()))
    total_env_cost = hourly_sum + setup_sum + teardown_sum

    labels = ["Hourly", "Setup", "Teardown"]
    values = [hourly_sum, setup_sum, teardown_sum]

    plt.figure(figsize=(6, 6))
    wedges, texts, autotexts = plt.pie(
        values,
        labels=labels,
        autopct=lambda p: f"{p:.1f}%",
        startangle=90,
        colors=["#4c78a8", "#f58518", "#54a24b"],
    )
    plt.title(f"Environment Cost Breakdown (Total ${total_env_cost:,.0f})")
    plt.tight_layout()
    # Renamed to better reflect the chart type/content
    plt.savefig(os.path.join(out_dir, "env_cost_breakdown_pie.png"))
    if not show:
        plt.close()


def plot_env_cost_histograms(env_data: Dict[str, Environment], out_dir: str, show: bool = False):
    """Plot histograms for environment cost components (hourly/setup/teardown)."""
    os.makedirs(out_dir, exist_ok=True)

    plt.figure(figsize=(6, 4))
    plt.hist([e.hourly_cost for e in env_data.values()], bins=8, alpha=0.6, label="Hourly")
    plt.hist([e.setup_cost for e in env_data.values()], bins=8, alpha=0.6, label="Setup")
    plt.hist([e.teardown_cost for e in env_data.values()], bins=8, alpha=0.6, label="Teardown")
    plt.title("Environment Cost Components — Histograms")
    plt.xlabel("Cost ($)")
    plt.ylabel("Frequency")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "env_cost_hist.png"))
    if not show:
        plt.close()


def plot_gantt(schedule: List[Dict], out_path: str, show: bool = False, x_label: str = "Time (hours)"):
    """
    Creates a Gantt chart that shows when each test occurs in a given environment.
    The schedule input is a list of dictionaries with:
      { "test": str, "env": str, "start": float, "duration": float }
    """
    plt.figure(figsize=(10, 6))
    for idx, task in enumerate(schedule):
        plt.barh(task["env"], task["duration"], left=task["start"], label=task["test"])
    plt.xlabel(x_label)
    plt.ylabel("Environment")
    plt.title("Verification Test Schedule (Gantt Chart)")
    plt.tight_layout()
    plt.savefig(out_path)
    if show:
        try:
            plt.show(block=False)
        except Exception:
            pass
    else:
        plt.close()


# SCHEDULE-DRIVEN VISUALS
def _collect_from_nodes(nodes: List, key_fn):
    items: Dict[str, any] = {}
    for n in nodes:
        k = key_fn(n)
        if k not in items:
            items[k] = k
    return items


def build_env_transition_cost_matrix_from_schedule(nodes_in_day_order: List) -> Tuple[List[str], np.ndarray]:
    """Build an environment changeover cost matrix from a linearized schedule.

    For each consecutive pair (prev -> curr) with different environments,
    accumulates prev.env.teardown_cost + curr.env.setup_cost into M[prev_env, curr_env].
    Returns (env_labels, matrix).
    """
    env_labels = sorted({n.enviroment.name for n in nodes_in_day_order})
    idx = {e: i for i, e in enumerate(env_labels)}
    m = np.zeros((len(env_labels), len(env_labels)), dtype=float)
    for a, b in zip(nodes_in_day_order, nodes_in_day_order[1:]):
        ea, eb = a.enviroment.name, b.enviroment.name
        if ea == eb:
            continue
        m[idx[ea], idx[eb]] += (a.enviroment.teardown_cost + b.enviroment.setup_cost)
    return env_labels, m


def compute_hour_schedule(visited_nodes: List, day_map: Dict[int, int]) -> Dict[int, float]:
    """Compute hour-based start times from discrete day slots and durations.

    For each node n, start_hour[n] = max(
      day_map[n]*24,
      max(child_start + child_duration for child in n.children),
      env_available[n.env]
    )
    where env_available tracks the end time of the last task scheduled in that environment.
    Assumes visited_nodes is ordered child-before-parent.
    Returns a mapping node.id -> start_hour (float).
    """
    start_hour: Dict[int, float] = {}
    env_available: Dict[str, float] = {}

    for n in visited_nodes:
        base = float(day_map[n.id] * 24.0)
        children_end = 0.0
        if getattr(n, "children", None):
            for c in n.children:
                c_start = start_hour.get(c.id, 0.0)
                c_end = c_start + float(getattr(c.test, "duration", 0.0))
                if c_end > children_end:
                    children_end = c_end
        env_key = n.enviroment.name
        env_ready = env_available.get(env_key, 0.0)
        s = max(base, children_end, env_ready)
        start_hour[n.id] = s
        env_available[env_key] = s + float(getattr(n.test, "duration", 0.0))

    return start_hour


def plot_schedule_visuals(visited_nodes: List, day_map: Dict[int, int], out_dir: str = "./out_viz", show: bool = False):
    """Generate heatmap, histograms, and a Gantt chart from the computed schedule.

    - Heatmap: environment changeover accumulated cost along chronological order.
    - Histograms: distributions of test durations and environment costs for used items.
    - Gantt: per-environment bars at day-based starts; duration uses test.duration (hours).
    """
    os.makedirs(out_dir, exist_ok=True)

    # Day-based sequence: reflect the schedule planned in discrete days
    nodes_time = sorted(visited_nodes, key=lambda n: (day_map[n.id], n.enviroment.name, n.id))
    env_labels, changeover = build_env_transition_cost_matrix_from_schedule(nodes_time)
    plot_heatmap(changeover, env_labels, os.path.join(out_dir, "schedule_changeover_heatmap.png"), show=show)

    # Histograms from actual used tests/envs
    tests: Dict[str, TestType] = {}
    envs: Dict[str, Environment] = {}
    for n in visited_nodes:
        tests[n.test.name] = n.test
        envs[n.enviroment.name] = n.enviroment
    plot_histograms(tests, envs, out_dir, show=show)
    # Additional environment cost histograms
    plot_env_cost_histograms(envs, out_dir, show=show)

    # Gantt by day; one unit per task to reflect day slots
    schedule: List[Dict] = []
    for n in nodes_time:
        schedule.append({
            "test": f"ID:{n.id}-{n.test.name}",
            "env": n.enviroment.name,
            "start": float(day_map[n.id]),
            "duration": 1.0,
        })
    plot_gantt(schedule, os.path.join(out_dir, "schedule_gantt.png"), show=show, x_label="Day")

    # Keep figures open when requested (block until user closes)
    if show:
        try:
            plt.show()
        except Exception:
            pass

# MAIN EXECUTION FUNCTION
def generate_visuals(output_dir: str = "./out_viz"):
    """
    Generates fake data, constructs visualizations, and saves them as image files.
    This function can be called independently or from a master script.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Step 1: Generate fake data for tests and environments
    tests = generate_test_data()
    envs = generate_environment_data()

    # Step 2: Create a fake environment changeover matrix
    matrix = generate_transition_matrix(list(envs.keys()))

    # Step 3: Build a simple sequential test schedule for Gantt chart
    schedule = []
    start_time = 0
    for test, env in zip(tests.values(), envs.values()):
        schedule.append({
            "test": test.name,
            "env": env.name,
            "start": start_time,
            "duration": test.duration
        })
        start_time += test.duration + 1  # adds a one-hour gap between tests

    # Step 4: Create and export all visualizations
    plot_heatmap(matrix, list(envs.keys()), os.path.join(output_dir, "heatmap.png"))
    plot_histograms(tests, envs, output_dir)
    plot_gantt(schedule, os.path.join(output_dir, "gantt.png"))

    print(f"Visualizations saved to {os.path.abspath(output_dir)}")


# SCRIPT ENTRY POINT
if __name__ == "__main__":
    generate_visuals()
