from __future__ import annotations

import csv
import json
import ssl
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Iterable

import pandas as pd

from qbvs.backtest import normalize_ohlcv


def load_csv(path: Path | str, symbol: str = "CSV", market: str = "CSV") -> pd.DataFrame:
    return normalize_ohlcv(pd.read_csv(path), symbol=symbol, market=market)


def load_universe(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    required = {"symbol", "market"}
    for row in rows:
        missing = required - set(row)
        if missing:
            raise ValueError(f"universe row missing fields: {missing}")
    return rows


def fetch_yahoo_chart(
    symbol: str,
    period1: str = "1970-01-01",
    period2: str | None = None,
    allow_insecure_ssl: bool = False,
) -> pd.DataFrame:
    start = int(pd.Timestamp(period1, tz="UTC").timestamp())
    end_ts = pd.Timestamp.utcnow() if period2 is None else pd.Timestamp(period2, tz="UTC")
    end = int(end_ts.timestamp())
    encoded = urllib.parse.quote(symbol, safe="")
    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/{encoded}"
        f"?period1={start}&period2={end}&interval=1d&events=history&includeAdjustedClose=true"
    )
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    context = ssl._create_unverified_context() if allow_insecure_ssl else None
    with urllib.request.urlopen(request, timeout=20, context=context) as response:
        payload = json.loads(response.read().decode("utf-8"))
    result = payload.get("chart", {}).get("result") or []
    if not result:
        error = payload.get("chart", {}).get("error")
        raise ValueError(f"Yahoo returned no chart data for {symbol}: {error}")
    item = result[0]
    timestamps = item.get("timestamp") or []
    quote = (item.get("indicators", {}).get("quote") or [{}])[0]
    adjclose = (item.get("indicators", {}).get("adjclose") or [{}])[0].get("adjclose")
    close = adjclose or quote.get("close")
    frame = pd.DataFrame(
        {
            "datetime": pd.to_datetime(timestamps, unit="s", utc=True).tz_convert(None),
            "open": quote.get("open"),
            "high": quote.get("high"),
            "low": quote.get("low"),
            "close": close,
            "volume": quote.get("volume"),
            "symbol": symbol,
            "market": "YAHOO",
        }
    )
    return normalize_ohlcv(frame, symbol=symbol, market="YAHOO")


def fetch_yahoo_universe(
    rows: Iterable[dict[str, str]],
    limit: int | None = None,
    sleep_seconds: float = 0.25,
    allow_insecure_ssl: bool = False,
    errors: list[dict[str, str]] | None = None,
) -> dict[str, pd.DataFrame]:
    output: dict[str, pd.DataFrame] = {}
    selected = list(rows)[:limit] if limit else list(rows)
    for row in selected:
        symbol = row["symbol"]
        try:
            frame = fetch_yahoo_chart(symbol, allow_insecure_ssl=allow_insecure_ssl)
            frame["market"] = row.get("market", "YAHOO")
            output[symbol] = frame
        except Exception as exc:
            if errors is not None:
                errors.append({"symbol": symbol, "market": row.get("market", ""), "error": str(exc)})
        finally:
            if sleep_seconds:
                time.sleep(sleep_seconds)
    return output
