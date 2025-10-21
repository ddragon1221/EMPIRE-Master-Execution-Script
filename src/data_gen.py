from __future__ import annotations
from typing import Dict, Tuple, Optional
from pathlib import Path
import time, os, random
import numpy as np
import pandas as pd
from .config_loader import Config

def _make_rng(seed: Optional[int]) -> np.random.Generator:
    if seed is None:
        seed = int(time.time_ns() % (2**32 - 1))
        random.seed(seed)
        np.random.seed(seed)
    else:
        seed = int(seed) % (2**32 - 1)
        random.seed(seed)
        np.random.seed(seed)
    return np.random.default_rng(seed)

def generate_fake_dataset(cfg: Config) -> pd.DataFrame:
    """
    Returns a DataFrame with columns:
      test_id, test_type, environment, base_cost, setup_cost, teardown_cost,
      num_instruments, instruments, personnel_mix, total_cost
    """
    rng = _make_rng(cfg.random_seed)

    test_types = list(cfg.test_types.keys())
    envs      = list(cfg.environments.keys())
    instrs    = list(cfg.instruments.keys())
    people    = list(cfg.personnel.keys())

    rows = []
    last_env = None

    for i in range(cfg.num_tests):
        test_type = rng.choice(test_types)

        # environment selection with a bias to stay in same environment
        if last_env and rng.random() < cfg.same_env_bias:
            environment = last_env
        else:
            environment = rng.choice(envs)
        last_env = environment

        # base test cost sampled from configured range
        lo, hi   = cfg.test_types[test_type]
        base_cost = float(rng.integers(int(lo), int(hi + 1)))

        # setup/teardown
        setup_cost    = float(cfg.environments[environment]["setup"])
        teardown_cost = float(cfg.environments[environment]["teardown"])

        # instruments (1–3 randomly)
        k = int(rng.integers(1, min(4, len(instrs) + 1)))
        chosen_instr = rng.choice(instrs, size=k, replace=False).tolist()
        instr_hourly = sum(cfg.instruments[name] for name in chosen_instr)
        # assume 1.5 hours avg per test for instrument time
        instrument_cost = 1.5 * instr_hourly

        # personnel mix (1–2 people)
        p = int(rng.integers(1, min(3, len(people) + 1)))
        chosen_people = rng.choice(people, size=p, replace=False).tolist()
        people_hourly = sum(cfg.personnel[name] for name in chosen_people)
        # assume 2.0 hours avg per test for personnel
        personnel_cost = 2.0 * people_hourly

        total_cost = base_cost + setup_cost + teardown_cost + instrument_cost + personnel_cost

        rows.append({
            "test_id":          f"T{i:03d}",
            "test_type":        test_type,
            "environment":      environment,
            "base_cost":        base_cost,
            "setup_cost":       setup_cost,
            "teardown_cost":    teardown_cost,
            "num_instruments":  k,
            "instruments":      ", ".join(chosen_instr),
            "personnel_mix":    ", ".join(chosen_people),
            "total_cost":       round(total_cost, 2)
        })

    df = pd.DataFrame(rows)
    return df

def ensure_output_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p
