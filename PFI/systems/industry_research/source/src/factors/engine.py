from __future__ import annotations

from collections import defaultdict
from statistics import mean, pstdev


def compute_price_factors(price_rows: list[dict[str, str]], as_of: str) -> list[dict[str, object]]:
    by_symbol: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in price_rows:
        if row["date"] <= as_of:
            by_symbol[row["symbol"]].append(row)

    factors: list[dict[str, object]] = []
    for symbol, rows in by_symbol.items():
        rows = sorted(rows, key=lambda item: item["date"])
        if len(rows) < 2:
            continue
        closes = [float(row["close"]) for row in rows]
        volumes = [float(row["volume"]) for row in rows]
        returns = [(closes[i] / closes[i - 1]) - 1 for i in range(1, len(closes))]
        lookback = min(5, len(closes) - 1)
        momentum = closes[-1] / closes[-1 - lookback] - 1
        volatility = pstdev(returns[-lookback:]) if len(returns[-lookback:]) > 1 else 0.0
        volume_ratio = volumes[-1] / mean(volumes[-1 - lookback : -1])
        latest = rows[-1]
        factors.append(
            {
                "symbol": symbol,
                "name": latest["name"],
                "industry": latest["industry"],
                "date": latest["date"],
                "close": round(closes[-1], 4),
                "momentum_5d": round(momentum, 6),
                "volatility_5d": round(volatility, 6),
                "volume_ratio_5d": round(volume_ratio, 6),
                "expected_direction": "positive" if momentum > 0 else "negative",
                "factor_definition": "5日价格动量、5日波动率、成交量相对过去5日均值",
                "data_source": "market_prices.csv",
                "update_frequency": "daily",
                "validation_result": "sample_only",
            }
        )
    return factors


def merge_fundamental_factors(
    price_factors: list[dict[str, object]], fundamentals: list[dict[str, str]], as_of: str
) -> list[dict[str, object]]:
    fundamental_by_symbol = {
        row["symbol"]: row for row in fundamentals if row["date"] <= as_of
    }
    merged: list[dict[str, object]] = []
    for factor in price_factors:
        item = dict(factor)
        row = fundamental_by_symbol.get(str(factor["symbol"]), {})
        for key in ["revenue_growth", "net_profit_growth", "roe", "pe", "pb", "ev_ebitda", "debt_to_asset"]:
            if key in row:
                item[key] = float(row[key])
        if row:
            item["fundamental_source_name"] = row["source_name"]
            item["fundamental_source_url"] = row["source_url"]
        merged.append(item)
    return merged
