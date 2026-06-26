from __future__ import annotations

from dataclasses import replace

import pandas as pd

from pfi_os.config import SUPPORTED_INTERVALS
from pfi_os.data.cleaner import resample_bars
from pfi_os.data.models import BarDataRequest
from pfi_os.data.providers.base import DataProvider


INTERVAL_OPTIONS = tuple(SUPPORTED_INTERVALS.keys())


def pandas_interval_rule(interval: str) -> str:
    if interval not in SUPPORTED_INTERVALS:
        raise ValueError(f"Unsupported interval: {interval}")
    return SUPPORTED_INTERVALS[interval]


def fallback_base_intervals(interval: str) -> tuple[str, ...]:
    if interval in {"1q", "1y"}:
        return ("1m", "1d")
    if interval in {"1w", "1m"}:
        return ("1d",)
    return ()


def get_bars_with_interval_fallback(provider: DataProvider, request: BarDataRequest) -> tuple[pd.DataFrame, str | None]:
    try:
        return provider.get_bars(request), None
    except NotImplementedError as original_exc:
        last_exc: Exception = original_exc
        for base_interval in fallback_base_intervals(request.interval):
            try:
                base_request = replace(request, interval=base_interval)
                base_data = provider.get_bars(base_request)
            except NotImplementedError as fallback_exc:
                last_exc = fallback_exc
                continue
            resampled = resample_bars(base_data, pandas_interval_rule(request.interval))
            return resampled, base_interval
        raise last_exc
