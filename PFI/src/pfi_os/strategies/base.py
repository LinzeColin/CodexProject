from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class StrategyResult:
    signals: pd.DataFrame
    metadata: dict[str, Any] = field(default_factory=dict)


class Strategy(ABC):
    strategy_id = "base"
    version = "0.1.0"
    description = ""

    def __init__(self, **params: Any):
        self.params = params

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> StrategyResult:
        """Return a DataFrame with datetime and target_weight columns."""
        raise NotImplementedError

    @property
    def name(self) -> str:
        return self.strategy_id

    def metadata(self) -> dict[str, Any]:
        return {
            "strategy_id": self.strategy_id,
            "version": self.version,
            "description": self.description,
            "params": self.params,
        }


def finalize_signal_frame(data: pd.DataFrame, target_weight: pd.Series) -> pd.DataFrame:
    out = data[["datetime", "symbol", "market", "close"]].copy()
    out["target_weight"] = target_weight.fillna(0.0).clip(-1.0, 1.0)
    out["signal"] = out["target_weight"].diff().fillna(out["target_weight"])
    return out
