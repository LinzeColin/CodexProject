from __future__ import annotations

import pandas as pd
import requests

from pfi_os.config import get_env_value
from pfi_os.data.cleaner import normalize_ohlcv
from pfi_os.data.models import BarDataRequest
from pfi_os.data.providers.base import DataProvider


class AlphaVantageProvider(DataProvider):
    name = "alpha_vantage"
    base_url = "https://www.alphavantage.co/query"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or get_env_value("ALPHA_VANTAGE_API_KEY")
        if not self.api_key:
            raise ValueError("ALPHA_VANTAGE_API_KEY is required")

    def get_bars(self, request: BarDataRequest) -> pd.DataFrame:
        params = self._params(request)
        response = requests.get(self.base_url, params=params, timeout=30)
        response.raise_for_status()
        payload = response.json()
        key = next((k for k in payload if "Time Series" in k), None)
        if key is None:
            raise RuntimeError(f"Alpha Vantage response did not include time series data: {payload}")
        rows = []
        for dt, values in payload[key].items():
            rows.append(
                {
                    "datetime": dt,
                    "open": values.get("1. open"),
                    "high": values.get("2. high"),
                    "low": values.get("3. low"),
                    "close": values.get("4. close"),
                    "volume": values.get("6. volume", values.get("5. volume", 0)),
                }
            )
        data = normalize_ohlcv(pd.DataFrame(rows), symbol=request.symbol, market=request.market)
        if request.start is not None:
            data = data[data["datetime"] >= pd.Timestamp(request.start)]
        if request.end is not None:
            data = data[data["datetime"] <= pd.Timestamp(request.end)]
        return data.reset_index(drop=True)

    def _params(self, request: BarDataRequest) -> dict[str, str]:
        if request.interval == "1d":
            return {
                "function": "TIME_SERIES_DAILY_ADJUSTED",
                "symbol": request.symbol,
                "outputsize": "full",
                "apikey": self.api_key,
            }
        interval = request.interval.replace("min", "min")
        return {
            "function": "TIME_SERIES_INTRADAY",
            "symbol": request.symbol,
            "interval": interval,
            "outputsize": "full",
            "apikey": self.api_key,
        }
