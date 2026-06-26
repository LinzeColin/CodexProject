from __future__ import annotations

import pandas as pd

from pfi_os.strategies.base import Strategy, StrategyResult, finalize_signal_frame


class BreakoutStrategy(Strategy):
    strategy_id = "breakout"
    description = "Long when close breaks above the previous rolling high; exit below rolling low."

    def __init__(self, lookback: int = 55, exit_lookback: int = 20):
        super().__init__(lookback=lookback, exit_lookback=exit_lookback)
        self.lookback = lookback
        self.exit_lookback = exit_lookback

    def generate_signals(self, data: pd.DataFrame) -> StrategyResult:
        close = data["close"]
        rolling_high = data["high"].rolling(self.lookback, min_periods=self.lookback).max().shift(1)
        rolling_low = data["low"].rolling(self.exit_lookback, min_periods=self.exit_lookback).min().shift(1)
        target = pd.Series(0.0, index=data.index)
        invested = False
        values = []
        for i in range(len(data)):
            if close.iloc[i] > rolling_high.iloc[i]:
                invested = True
            elif close.iloc[i] < rolling_low.iloc[i]:
                invested = False
            values.append(1.0 if invested else 0.0)
        target[:] = values
        signals = finalize_signal_frame(data, target)
        signals["rolling_high"] = rolling_high
        signals["rolling_low"] = rolling_low
        return StrategyResult(signals=signals, metadata=self.metadata())
