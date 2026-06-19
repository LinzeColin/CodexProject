from __future__ import annotations

import pandas as pd

from pfi_os.data.cleaner import normalize_ohlcv
from pfi_os.data.models import BarDataRequest
from pfi_os.data.providers.base import DataProvider
from pfi_os.data.symbols import normalize_a_share_symbol


class AKShareProvider(DataProvider):
    name = "akshare"

    def get_bars(self, request: BarDataRequest) -> pd.DataFrame:
        try:
            import akshare as ak
        except ModuleNotFoundError as exc:
            raise RuntimeError("AKShare is not installed. Run: .venv/bin/pip install -e \".[data]\"") from exc

        if request.market.upper() != "CN":
            raise ValueError("AKShareProvider MVP is intended for A-share market CN.")
        if request.interval not in {"1d", "1w", "1m"}:
            raise NotImplementedError("AKShareProvider currently supports daily, weekly, and monthly A-share bars.")

        start_date = _compact_date(request.start)
        end_date = _compact_date(request.end)
        period = {"1d": "daily", "1w": "weekly", "1m": "monthly"}[request.interval]
        adjust = _akshare_adjustment(request.adjustment)
        raw = ak.stock_zh_a_hist(
            symbol=normalize_a_share_symbol(request.symbol).akshare,
            period=period,
            start_date=start_date,
            end_date=end_date,
            adjust=adjust,
        )
        mapped = raw.rename(
            columns={
                "日期": "datetime",
                "开盘": "open",
                "最高": "high",
                "最低": "low",
                "收盘": "close",
                "成交量": "volume",
                "成交额": "amount",
            }
        )
        return normalize_ohlcv(mapped, symbol=request.symbol, market=request.market)

def _compact_date(value) -> str:
    if value is None:
        return "19700101"
    return pd.Timestamp(value).strftime("%Y%m%d")


def _akshare_adjustment(adjustment: str) -> str:
    normalized = adjustment.lower()
    if normalized in {"qfq", "forward", "前复权"}:
        return "qfq"
    if normalized in {"hfq", "backward", "后复权"}:
        return "hfq"
    return ""
