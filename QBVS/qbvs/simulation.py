from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class RandomPathConfig:
    paths: int = 10_000
    days: int = 252
    seed: int = 42
    start_price: float = 100.0


REGIMES: dict[str, dict[str, float]] = {
    "bull": {"mu": 0.00075, "sigma": 0.012, "jump_p": 0.002, "jump_mu": -0.02, "jump_sigma": 0.025},
    "bear": {"mu": -0.00035, "sigma": 0.016, "jump_p": 0.004, "jump_mu": -0.03, "jump_sigma": 0.035},
    "sideways": {"mu": 0.00005, "sigma": 0.010, "jump_p": 0.002, "jump_mu": 0.0, "jump_sigma": 0.02},
    "crash": {"mu": -0.0012, "sigma": 0.024, "jump_p": 0.015, "jump_mu": -0.055, "jump_sigma": 0.045},
    "highvol": {"mu": 0.00015, "sigma": 0.026, "jump_p": 0.008, "jump_mu": -0.015, "jump_sigma": 0.055},
    "rotation": {"mu": 0.00025, "sigma": 0.018, "jump_p": 0.004, "jump_mu": 0.0, "jump_sigma": 0.04},
}


def generate_random_paths(config: RandomPathConfig) -> list[tuple[str, pd.DataFrame]]:
    rng = np.random.default_rng(config.seed)
    regime_names = list(REGIMES)
    chosen = rng.choice(regime_names, size=config.paths, replace=True)
    paths: list[tuple[str, pd.DataFrame]] = []
    dates = pd.bdate_range("2000-01-03", periods=config.days)
    for i, regime in enumerate(chosen):
        p = REGIMES[str(regime)]
        base = rng.normal(p["mu"], p["sigma"], size=config.days)
        jump_mask = rng.random(config.days) < p["jump_p"]
        jumps = rng.normal(p["jump_mu"], p["jump_sigma"], size=config.days)
        returns = np.clip(base + jump_mask * jumps, -0.35, 0.35)
        close = config.start_price * np.exp(np.cumsum(returns))
        open_ = np.concatenate([[config.start_price], close[:-1]]) * (1 + rng.normal(0, 0.001, size=config.days))
        high = np.maximum(open_, close) * (1 + rng.random(config.days) * 0.01)
        low = np.minimum(open_, close) * (1 - rng.random(config.days) * 0.01)
        frame = pd.DataFrame(
            {
                "datetime": dates,
                "symbol": f"SIM{i:06d}",
                "market": regime,
                "open": open_,
                "high": high,
                "low": low,
                "close": close,
                "volume": 0.0,
            }
        )
        paths.append((str(regime), frame))
    return paths
