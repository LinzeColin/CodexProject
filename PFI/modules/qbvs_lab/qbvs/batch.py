from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from typing import Iterable

import pandas as pd

from qbvs.simulation import RandomPathConfig, generate_random_paths
from qbvs.strategies import BehaviorStrategySpec
from qbvs.validation import ValidationConfig, validate_one


def stress_random_parallel(
    specs: Iterable[BehaviorStrategySpec],
    random_config: RandomPathConfig,
    config: ValidationConfig | None = None,
    workers: int = 2,
    chunk_size: int = 20,
) -> pd.DataFrame:
    config = config or ValidationConfig()
    paths = generate_random_paths(random_config)
    jobs = [(spec, regime, frame, config) for spec in specs for regime, frame in paths]
    if workers <= 1:
        return pd.DataFrame([_random_job(job) for job in jobs])
    with ProcessPoolExecutor(max_workers=workers) as executor:
        rows = list(executor.map(_random_job, jobs, chunksize=max(1, chunk_size)))
    return pd.DataFrame(rows)


def _random_job(job: tuple[BehaviorStrategySpec, str, pd.DataFrame, ValidationConfig]) -> dict[str, object]:
    spec, regime, frame, config = job
    try:
        result = validate_one(frame, spec, config)
        result["regime"] = regime
        return result
    except Exception as exc:
        return {"strategy_id": spec.strategy_id, "symbol": str(frame["symbol"].iloc[0]), "regime": regime, "error": str(exc)}
