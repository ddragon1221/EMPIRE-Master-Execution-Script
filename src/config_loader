from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Tuple, Optional
import yaml
from pathlib import Path

@dataclass
class Config:
    random_seed: Optional[int]
    num_tests: int
    test_types: Dict[str, Tuple[float, float]]
    environments: Dict[str, Dict[str, float]]
    instruments: Dict[str, float]
    personnel: Dict[str, float]
    same_env_bias: float
    output_dir: str
    write_csv: bool
    charts: Dict[str, bool]

def load_config(path: str | Path = "config.yaml") -> Config:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    return Config(
        random_seed      = raw.get("random_seed"),
        num_tests        = int(raw["num_tests"]),
        test_types       = {k: tuple(v) for k, v in raw["test_types"].items()},
        environments     = raw["environments"],
        instruments      = raw["instruments"],
        personnel        = raw["personnel"],
        same_env_bias    = float(raw["same_env_bias"]),
        output_dir       = raw["output_dir"],
        write_csv        = bool(raw["write_csv"]),
        charts           = raw["charts"],
    )
