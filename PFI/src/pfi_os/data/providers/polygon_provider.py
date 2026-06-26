from __future__ import annotations

import pandas as pd
import requests

from pfi_os.config import get_env_value
from pfi_os.data.cleaner import normalize_ohlcv
from pfi_os.data.models import BarDataRequest
from pfi_os.data.providers.base import DataProvider


class PolygonProvider(DataProvider):
    name = "polygon"
    base_url = "https://api.polygon.io"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or get_env_value("POLYGON_API_KEY")
        if not self.api_key:
            raise ValueError("POLYGON_API_KEY is required")

    def get_bars(self, request: BarDataRequest) -> pd.DataFrame:
        if request.market.upper() not in {"US", "HK"}:
            raise ValueError("PolygonProvider currently supports US and selected HK-compatible tickers only.")
        multiplier, timespan = _polygon_interval(request.interval)
        start = pd.Timestamp(request.start).strftime("%Y-%m-%d") if request.start is not None else "1970-01-01"
        end = pd.Timestamp(request.end).strftime("%Y-%m-%d") if request.end is not None else pd.Timestamp.utcnow().strftime("%Y-%m-%d")
        url = f"{self.base_url}/v2/aggs/ticker/{request.symbol}/range/{multiplier}/{timespan}/{start}/{end}"
        response = requests.get(
            url,
            params={"adjusted": _polygon_adjusted(request.adjustment), "sort": "asc", "limit": 50000, "apiKey": self.api_key},
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("status") not in {"OK", "DELAYED"}:
            raise RuntimeError(f"Polygon response status was not OK: {payload}")
        rows = [
            {
                "datetime": pd.to_datetime(item["t"], unit="ms", utc=True).tz_convert(None),
                "open": item.get("o"),
                "high": item.get("h"),
                "low": item.get("l"),
                "close": item.get("c"),
                "volume": item.get("v", 0),
            }
            for item in payload.get("results", [])
        ]
        return normalize_ohlcv(pd.DataFrame(rows), symbol=request.symbol, market=request.market)


def _polygon_interval(interval: str) -> tuple[int, str]:
    mapping = {
        "1min": (1, "minute"),
        "5min": (5, "minute"),
        "15min": (15, "minute"),
        "30min": (30, "minute"),
        "60min": (1, "hour"),
        "1d": (1, "day"),
        "1w": (1, "week"),
        "1m": (1, "month"),
    }
    if interval not in mapping:
        raise NotImplementedError(f"Polygon interval not supported: {interval}")
    return mapping[interval]


def _polygon_adjusted(adjustment: str) -> str:
    return "true" if adjustment.lower() in {"adjusted", "auto", "qfq", "forward"} else "false"
