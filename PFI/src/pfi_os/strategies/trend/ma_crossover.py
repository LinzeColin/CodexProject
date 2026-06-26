from __future__ import annotations

import pandas as pd

from pfi_os.indicators import sma
from pfi_os.strategies.base import Strategy, StrategyResult, finalize_signal_frame


class MovingAverageCrossoverStrategy(Strategy):
    strategy_id = "ma_crossover"
    description = "Long when short moving average is above long moving average."

    def __init__(self, short_window: int = 20, long_window: int = 60, long_only: bool = True):
        if short_window >= long_window:
            raise ValueError("short_window must be smaller than long_window")
        super().__init__(short_window=short_window, long_window=long_window, long_only=long_only)
        self.short_window = short_window
        self.long_window = long_window
        self.long_only = long_only

    def generate_signals(self, data: pd.DataFrame) -> StrategyResult:
        close = data["close"]
        short_ma = sma(close, self.short_window)
        long_ma = sma(close, self.long_window)
        target = pd.Series(0.0, index=data.index)
        target[short_ma > long_ma] = 1.0
        if not self.long_only:
            target[short_ma < long_ma] = -1.0
        signals = finalize_signal_frame(data, target)
        signals["short_ma"] = short_ma
        signals["long_ma"] = long_ma
        return StrategyResult(signals=signals, metadata=self.metadata())
