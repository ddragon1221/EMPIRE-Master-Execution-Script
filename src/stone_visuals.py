import os
import random
from dataclasses import dataclass
from typing import List, Dict
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
def plot_heatmap(matrix: np.ndarray, labels: List[str], out_path: str):
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
    plt.close()


def plot_histograms(test_data: Dict[str, TestType], env_data: Dict[str, Environment], out_dir: str):
    """
    Plots three histograms:
      - Test cost distribution
      - Test duration distribution
      - Environment cost breakdown (hourly, setup, teardown)
    """
    os.makedirs(out_dir, exist_ok=True)

    # 1) Test Cost Distribution
    plt.hist([t.cost for t in test_data.values()], bins=10, color='blue', alpha=0.7)
    plt.title("Test Cost Distribution")
    plt.xlabel("Cost ($)")
    plt.ylabel("Frequency")
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "test_cost_hist.png"))
    plt.close()

    # 2) Test Duration Distribution
    plt.hist([t.duration for t in test_data.values()], bins=8, color='orange', alpha=0.7)
    plt.title("Test Duration Distribution")
    plt.xlabel("Duration (hours)")
    plt.ylabel("Frequency")
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "test_duration_hist.png"))
    plt.close()

    # 3) Environment Cost Breakdown
    plt.hist([e.hourly_cost for e in env_data.values()], bins=8, alpha=0.5, label="Hourly")
    plt.hist([e.setup_cost for e in env_data.values()], bins=8, alpha=0.5, label="Setup")
    plt.hist([e.teardown_cost for e in env_data.values()], bins=8, alpha=0.5, label="Teardown")
    plt.title("Environment Cost Distribution")
    plt.xlabel("Cost ($)")
    plt.ylabel("Frequency")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "env_cost_hist.png"))
    plt.close()


def plot_gantt(schedule: List[Dict], out_path: str):
    """
    Creates a Gantt chart that shows when each test occurs in a given environment.
    The schedule input is a list of dictionaries with:
      { "test": str, "env": str, "start": float, "duration": float }
    """
    plt.figure(figsize=(10, 6))
    for idx, task in enumerate(schedule):
        plt.barh(task["env"], task["duration"], left=task["start"], label=task["test"])
    plt.xlabel("Time (hours)")
    plt.ylabel("Environment")
    plt.title("Verification Test Schedule (Gantt Chart)")
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()


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
