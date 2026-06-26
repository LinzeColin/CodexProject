from __future__ import annotations

import pandas as pd

from pfi_os.strategies.base import Strategy, StrategyResult, finalize_signal_frame


class BollingerReversionStrategy(Strategy):
    strategy_id = "bollinger_reversion"
    description = "Long when close falls below the lower Bollinger Band; exit near the middle band."

    def __init__(self, window: int = 20, num_std: float = 2.0, exit_z: float = 0.0):
        super().__init__(window=window, num_std=num_std, exit_z=exit_z)
        self.window = window
        self.num_std = num_std
        self.exit_z = exit_z

    def generate_signals(self, data: pd.DataFrame) -> StrategyResult:
        close = pd.to_numeric(data["close"], errors="coerce")
        middle = close.rolling(self.window, min_periods=self.window).mean()
        std = close.rolling(self.window, min_periods=self.window).std(ddof=0)
        z_score = (close - middle) / std.replace(0, pd.NA)
        lower = middle - self.num_std * std
        upper = middle + self.num_std * std
        invested = False
        values = []
        for value in z_score:
            if pd.notna(value) and value <= -self.num_std:
                invested = True
            elif pd.notna(value) and value >= self.exit_z:
                invested = False
            values.append(1.0 if invested else 0.0)
        target = pd.Series(values, index=data.index)
        signals = finalize_signal_frame(data, target)
        signals["middle_band"] = middle
        signals["lower_band"] = lower
        signals["upper_band"] = upper
        signals["z_score"] = z_score
        return StrategyResult(signals=signals, metadata=self.metadata())
