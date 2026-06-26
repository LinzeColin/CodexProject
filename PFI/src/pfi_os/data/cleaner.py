from __future__ import annotations

import pandas as pd

from pfi_os.data.models import REQUIRED_BAR_COLUMNS


def normalize_ohlcv(df: pd.DataFrame, symbol: str | None = None, market: str | None = None) -> pd.DataFrame:
    """Normalize raw OHLCV data into PFIOS's canonical bar format."""
    if df.empty:
        return pd.DataFrame(columns=REQUIRED_BAR_COLUMNS + ["symbol", "market"])

    normalized = df.copy()
    normalized.columns = [str(c).strip().lower() for c in normalized.columns]
    if "date" in normalized.columns and "datetime" not in normalized.columns:
        normalized = normalized.rename(columns={"date": "datetime"})

    missing = [col for col in REQUIRED_BAR_COLUMNS if col not in normalized.columns]
    if missing:
        raise ValueError(f"OHLCV data missing required columns: {missing}")

    normalized["datetime"] = pd.to_datetime(normalized["datetime"], errors="coerce")
    normalized = normalized.dropna(subset=["datetime"])
    for col in ["open", "high", "low", "close", "volume"]:
        normalized[col] = pd.to_numeric(normalized[col], errors="coerce")
    normalized = normalized.dropna(subset=["open", "high", "low", "close"])
    normalized["volume"] = normalized["volume"].fillna(0.0)

    if symbol is not None:
        normalized["symbol"] = symbol
    elif "symbol" not in normalized.columns:
        normalized["symbol"] = "UNKNOWN"

    if market is not None:
        normalized["market"] = market
    elif "market" not in normalized.columns:
        normalized["market"] = "UNKNOWN"

    normalized = normalized.sort_values("datetime").drop_duplicates(subset=["datetime", "symbol"], keep="last")
    columns = ["datetime", "symbol", "market", "open", "high", "low", "close", "volume"]
    optional = [c for c in ["amount", "adjustment"] if c in normalized.columns]
    return normalized[columns + optional].reset_index(drop=True)


def resample_bars(df: pd.DataFrame, interval: str) -> pd.DataFrame:
    """Resample canonical bars to a larger interval."""
    if df.empty:
        return df.copy()
    data = df.copy()
    data["datetime"] = pd.to_datetime(data["datetime"])
    data = data.set_index("datetime").sort_index()
    symbol = data["symbol"].iloc[0] if "symbol" in data else "UNKNOWN"
    market = data["market"].iloc[0] if "market" in data else "UNKNOWN"
    agg = {
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum",
    }
    out = data.resample(interval).agg(agg).dropna(subset=["open", "high", "low", "close"])
    out["symbol"] = symbol
    out["market"] = market
    return out.reset_index()[["datetime", "symbol", "market", "open", "high", "low", "close", "volume"]]
