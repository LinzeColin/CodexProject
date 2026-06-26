from __future__ import annotations

import pandas as pd

from pfi_os.data.cleaner import normalize_ohlcv
from pfi_os.data.models import BarDataRequest
from pfi_os.data.providers.base import DataProvider


class YahooFinanceProvider(DataProvider):
    name = "yahoo_finance"

    def get_bars(self, request: BarDataRequest) -> pd.DataFrame:
        try:
            import yfinance as yf
        except ModuleNotFoundError as exc:
            raise RuntimeError("yfinance is not installed. Run: .venv/bin/pip install -e \".[data]\"") from exc

        interval = _yahoo_interval(request.interval)
        raw = yf.download(
            tickers=request.symbol,
            start=str(pd.Timestamp(request.start).date()) if request.start is not None else None,
            end=str(pd.Timestamp(request.end).date()) if request.end is not None else None,
            interval=interval,
            auto_adjust=request.adjustment.lower() in {"adjusted", "auto", "qfq", "forward"},
            progress=False,
            threads=False,
        )
        if raw.empty:
            return normalize_ohlcv(pd.DataFrame(), symbol=request.symbol, market=request.market)
        if isinstance(raw.columns, pd.MultiIndex):
            raw.columns = raw.columns.get_level_values(0)
        mapped = raw.reset_index().rename(
            columns={
                "Date": "datetime",
                "Datetime": "datetime",
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Adj Close": "adjusted_close",
                "Volume": "volume",
            }
        )
        return normalize_ohlcv(mapped, symbol=request.symbol, market=request.market)


def _yahoo_interval(interval: str) -> str:
    mapping = {
        "1min": "1m",
        "5min": "5m",
        "15min": "15m",
        "30min": "30m",
        "60min": "60m",
        "1d": "1d",
        "1w": "1wk",
        "1m": "1mo",
    }
    if interval not in mapping:
        raise NotImplementedError(f"Yahoo Finance interval not supported: {interval}")
    return mapping[interval]
