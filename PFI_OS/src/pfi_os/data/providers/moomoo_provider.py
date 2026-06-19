from __future__ import annotations

import os

import pandas as pd

from pfi_os.config import get_env_value
from pfi_os.data.cleaner import normalize_ohlcv
from pfi_os.data.models import BarDataRequest
from pfi_os.data.providers.base import DataProvider


class MoomooProvider(DataProvider):
    name = "moomoo"

    def __init__(self, host: str | None = None, port: int | None = None):
        try:
            import futu as ft
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("Moomoo requires the futu-api package and a running OpenD gateway.") from exc
        self.ft = ft
        self.host = host or get_env_value("MOOMOO_HOST", "127.0.0.1")
        self.port = int(port or get_env_value("MOOMOO_PORT", "11111"))

    def get_bars(self, request: BarDataRequest) -> pd.DataFrame:
        subtype = _moomoo_interval(request.interval, self.ft)
        symbol = _moomoo_symbol(request.symbol, request.market)
        quote_ctx = self.ft.OpenQuoteContext(host=self.host, port=self.port)
        try:
            ret, data, page_req_key = quote_ctx.request_history_kline(
                code=symbol,
                start=str(request.start) if request.start is not None else None,
                end=str(request.end) if request.end is not None else None,
                ktype=subtype,
                autype=self.ft.AuType.QFQ if request.adjustment.lower() in {"adjusted", "auto", "qfq", "forward"} else self.ft.AuType.NONE,
                max_count=1000,
            )
            frames = []
            if ret == self.ft.RET_OK:
                frames.append(data)
            else:
                raise RuntimeError(f"Moomoo error: {data}")
            while page_req_key is not None:
                ret, data, page_req_key = quote_ctx.request_history_kline(
                    code=symbol,
                    start=str(request.start) if request.start is not None else None,
                    end=str(request.end) if request.end is not None else None,
                    ktype=subtype,
                    autype=self.ft.AuType.QFQ if request.adjustment.lower() in {"adjusted", "auto", "qfq", "forward"} else self.ft.AuType.NONE,
                    max_count=1000,
                    page_req_key=page_req_key,
                )
                if ret != self.ft.RET_OK:
                    raise RuntimeError(f"Moomoo error: {data}")
                frames.append(data)
        finally:
            quote_ctx.close()
        raw = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
        if raw.empty:
            return normalize_ohlcv(pd.DataFrame(), symbol=request.symbol, market=request.market)
        out = raw.rename(
            columns={
                "time_key": "datetime",
                "open": "open",
                "high": "high",
                "low": "low",
                "close": "close",
                "volume": "volume",
            }
        )
        return normalize_ohlcv(out[["datetime", "open", "high", "low", "close", "volume"]], symbol=request.symbol, market=request.market)


def _moomoo_symbol(symbol: str, market: str) -> str:
    value = symbol.strip().upper()
    if "." in value and value.split(".", 1)[0] in {"US", "HK", "SH", "SZ"}:
        return value
    market = market.upper()
    if market == "US":
        return f"US.{value}"
    if market == "HK":
        return f"HK.{value.replace('.HK', '').zfill(5)}"
    if value.startswith("6"):
        return f"SH.{value.replace('.SH', '')}"
    return f"SZ.{value.replace('.SZ', '')}"


def _moomoo_interval(interval: str, ft):
    mapping = {
        "1min": ft.KLType.K_1M,
        "5min": ft.KLType.K_5M,
        "15min": ft.KLType.K_15M,
        "30min": ft.KLType.K_30M,
        "60min": ft.KLType.K_60M,
        "1d": ft.KLType.K_DAY,
        "1w": ft.KLType.K_WEEK,
        "1m": ft.KLType.K_MON,
    }
    if interval not in mapping:
        raise NotImplementedError(f"Moomoo interval not supported: {interval}")
    return mapping[interval]
