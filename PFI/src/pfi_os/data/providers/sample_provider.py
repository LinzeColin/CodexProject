from __future__ import annotations

import hashlib
import numpy as np
import pandas as pd

from pfi_os.config import SUPPORTED_INTERVALS
from pfi_os.data.cleaner import normalize_ohlcv
from pfi_os.data.models import BarDataRequest
from pfi_os.data.providers.base import DataProvider


SAMPLE_ANCHOR = pd.Timestamp("2000-01-03")


class SampleDataProvider(DataProvider):
    """Deterministic synthetic OHLCV data for demos and tests."""

    name = "sample"

    def __init__(self, seed: int = 42):
        self.seed = seed

    def get_bars(self, request: BarDataRequest) -> pd.DataFrame:
        start = pd.Timestamp(request.start or "2020-01-01")
        end = pd.Timestamp(request.end or "2024-12-31")
        freq = "B" if request.interval == "1d" else SUPPORTED_INTERVALS.get(request.interval, request.interval)
        index = pd.date_range(start=start, end=end, freq=freq)
        stable_key = f"{request.symbol}|{request.market}|{request.interval}|{self.seed}".encode("utf-8")
        stable_seed = int.from_bytes(hashlib.sha256(stable_key).digest()[:4], "little")
        phase = (stable_seed % 10000) / 10000.0 * 2.0 * np.pi
        elapsed_days = _elapsed_days(index)
        trend = 0.00032 * elapsed_days
        medium_cycle = 0.12 * np.sin(elapsed_days / 37.0 + phase)
        long_cycle = 0.08 * np.cos(elapsed_days / 181.0 + phase / 2.0)
        micro_cycle = 0.012 * np.sin(elapsed_days * 6.7 + phase * 1.7)
        level_offset = 1.0 + ((stable_seed % 2000) - 1000) / 10000.0
        close = 100.0 * level_offset * np.exp(trend + medium_cycle + long_cycle + micro_cycle)
        open_shift = 0.0025 * np.sin(elapsed_days * 9.1 + phase)
        open_ = close * (1 + open_shift)
        spread = 0.004 + 0.003 * np.abs(np.sin(elapsed_days * 4.3 + phase / 3.0))
        high = np.maximum(open_, close) * (1 + spread)
        low = np.minimum(open_, close) * (1 - spread)
        volume_wave = 0.55 + 0.45 * np.abs(np.sin(elapsed_days * 1.9 + phase))
        volume = np.maximum(1, (250_000 + 1_750_000 * volume_wave).round()).astype(int)
        data = pd.DataFrame(
            {
                "datetime": index,
                "open": open_,
                "high": high,
                "low": low,
                "close": close,
                "volume": volume,
            }
        )
        return normalize_ohlcv(data, symbol=request.symbol, market=request.market)


def _elapsed_days(index: pd.DatetimeIndex) -> np.ndarray:
    if index.empty:
        return np.array([], dtype=float)
    return ((index - SAMPLE_ANCHOR) / pd.Timedelta(days=1)).astype(float).to_numpy()
