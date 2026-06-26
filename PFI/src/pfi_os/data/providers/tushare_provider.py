from __future__ import annotations

import pandas as pd
import requests

from pfi_os.config import get_env_value
from pfi_os.data.cleaner import normalize_ohlcv
from pfi_os.data.models import BarDataRequest
from pfi_os.data.providers.base import DataProvider
from pfi_os.data.symbols import normalize_a_share_symbol


class TushareProvider(DataProvider):
    name = "tushare"
    base_url = "http://api.tushare.pro"

    def __init__(self, token: str | None = None):
        self.token = token or get_env_value("TUSHARE_TOKEN")
        if not self.token:
            raise ValueError("TUSHARE_TOKEN is required")

    def get_bars(self, request: BarDataRequest) -> pd.DataFrame:
        if request.interval != "1d":
            raise NotImplementedError("TushareProvider MVP currently supports daily bars only.")
        params = {
            "ts_code": normalize_a_share_symbol(request.symbol).tushare,
            "start_date": _compact_date(request.start),
            "end_date": _compact_date(request.end),
        }
        payload = {
            "api_name": "daily",
            "token": self.token,
            "params": {k: v for k, v in params.items() if v},
            "fields": "trade_date,ts_code,open,high,low,close,vol,amount",
        }
        response = requests.post(self.base_url, json=payload, timeout=30)
        response.raise_for_status()
        body = response.json()
        if body.get("code") != 0:
            raise RuntimeError(f"TuShare error: {body}")
        fields = body["data"]["fields"]
        rows = body["data"]["items"]
        raw = pd.DataFrame(rows, columns=fields)
        raw = raw.rename(columns={"trade_date": "datetime", "vol": "volume"})
        raw["datetime"] = pd.to_datetime(raw["datetime"], format="%Y%m%d")
        return normalize_ohlcv(raw, symbol=request.symbol, market=request.market)


def _compact_date(value) -> str | None:
    if value is None:
        return None
    return pd.Timestamp(value).strftime("%Y%m%d")
