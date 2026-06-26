from __future__ import annotations

from datetime import date


def build_watchlist_factors(
    watchlist_rows: list[dict[str, str]],
    snapshot_rows: list[dict[str, str]],
    as_of: str,
) -> list[dict[str, object]]:
    watchlist_by_symbol = {row["symbol"]: row for row in watchlist_rows}
    snapshot_by_symbol = _latest_snapshot_by_symbol(snapshot_rows, as_of)
    factors: list[dict[str, object]] = []
    for symbol, row in snapshot_by_symbol.items():
        meta = watchlist_by_symbol.get(symbol, {})
        daily_change = _to_float(row.get("daily_change_pct"))
        has_price = row.get("close") not in {"", None}
        asset_class = row.get("asset_class") or meta.get("asset_class", "")
        research_group = row.get("research_group") or meta.get("research_group", "")
        factors.append(
            {
                "symbol": symbol,
                "name": row.get("name") or meta.get("name", symbol),
                "industry": research_group,
                "research_group": research_group,
                "exchange": row.get("exchange") or meta.get("exchange", ""),
                "asset_class": asset_class,
                "date": row["date"],
                "close": _to_float(row.get("close")) if has_price else "",
                "open": _to_float(row.get("open")) if row.get("open") not in {"", None} else "",
                "high": _to_float(row.get("high")) if row.get("high") not in {"", None} else "",
                "low": _to_float(row.get("low")) if row.get("low") not in {"", None} else "",
                "momentum_5d": daily_change if daily_change is not None else 0.0,
                "daily_change_pct": daily_change if daily_change is not None else "",
                "volume": _to_float(row.get("volume")) if row.get("volume") not in {"", None} else "",
                "turnover": _to_float(row.get("turnover")) if row.get("turnover") not in {"", None} else "",
                "volatility_5d": 0.0,
                "volume_ratio_5d": 1.10 if daily_change is not None and daily_change > 0.02 else 1.0,
                "expected_direction": _direction(daily_change),
                "factor_definition": "基于 moomoo 自选页可见行情快照构建的日报线索；缺行情标的仅观察。",
                "data_source": "watchlist_snapshot.csv",
                "update_frequency": "daily",
                "validation_result": "desktop_snapshot",
                "snapshot_note": row.get("snapshot_note", ""),
                "source_name": row.get("source_name", "Moomoo Watchlist"),
                "source_url": row.get("source_url", "local://moomoo-watchlist"),
            }
        )
    return factors


def _latest_snapshot_by_symbol(snapshot_rows: list[dict[str, str]], as_of: str) -> dict[str, dict[str, str]]:
    cutoff = _parse_date(as_of)
    latest: dict[str, dict[str, str]] = {}
    for row in snapshot_rows:
        row_date = _parse_date(row.get("date", ""))
        if row_date > cutoff:
            continue
        symbol = row.get("symbol", "")
        if not symbol:
            continue
        current = latest.get(symbol)
        if current is None or row_date > _parse_date(current.get("date", "")):
            latest[symbol] = row
    return latest


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"Invalid snapshot date {value!r}; expected YYYY-MM-DD.") from exc


def _to_float(value: str | None) -> float | None:
    if value in {None, ""}:
        return None
    return float(value)


def _direction(value: float | None) -> str:
    if value is None:
        return "unknown"
    if value > 0:
        return "positive"
    if value < 0:
        return "negative"
    return "neutral"
