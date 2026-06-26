from __future__ import annotations

import pandas as pd

from pfi_os.strategies.base import Strategy, StrategyResult


class MomentumRotationStrategy(Strategy):
    strategy_id = "momentum_rotation"
    description = "Select top symbols by trailing return. Intended for multi-symbol research."

    def __init__(self, lookback: int = 126, top_n: int = 3):
        super().__init__(lookback=lookback, top_n=top_n)
        self.lookback = lookback
        self.top_n = top_n

    def generate_signals(self, data: pd.DataFrame) -> StrategyResult:
        if "symbol" not in data.columns:
            raise ValueError("MomentumRotationStrategy requires a symbol column")
        frame = data.copy().sort_values(["datetime", "symbol"])
        wide = frame.pivot(index="datetime", columns="symbol", values="close")
        momentum = wide.pct_change(self.lookback)
        weights = momentum.rank(axis=1, ascending=False) <= self.top_n
        weights = weights.div(weights.sum(axis=1), axis=0).fillna(0.0)
        signals = weights.stack().rename("target_weight").reset_index()
        signals = signals.merge(frame[["datetime", "symbol", "market", "close"]], on=["datetime", "symbol"], how="left")
        signals["signal"] = signals.groupby("symbol")["target_weight"].diff().fillna(signals["target_weight"])
        return StrategyResult(signals=signals, metadata=self.metadata())
