from __future__ import annotations

import pandas as pd

from pfi_os.indicators import rsi
from pfi_os.strategies.base import Strategy, StrategyResult, finalize_signal_frame


class RSIReversionStrategy(Strategy):
    strategy_id = "rsi_reversion"
    description = "Long after RSI oversold; exit after RSI recovers."

    def __init__(self, window: int = 14, entry: float = 30.0, exit: float = 55.0):
        super().__init__(window=window, entry=entry, exit=exit)
        self.window = window
        self.entry = entry
        self.exit = exit

    def generate_signals(self, data: pd.DataFrame) -> StrategyResult:
        rsi_value = rsi(data["close"], self.window)
        invested = False
        values = []
        for value in rsi_value:
            if pd.notna(value) and value < self.entry:
                invested = True
            elif pd.notna(value) and value > self.exit:
                invested = False
            values.append(1.0 if invested else 0.0)
        target = pd.Series(values, index=data.index)
        signals = finalize_signal_frame(data, target)
        signals["rsi"] = rsi_value
        return StrategyResult(signals=signals, metadata=self.metadata())
