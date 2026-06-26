from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable

import pandas as pd

from qbvs.backtest import normalize_ohlcv
from qbvs.data import fetch_yahoo_universe, load_csv, load_universe
from qbvs.quality import assess_ohlcv_quality, infer_asset_class, infer_tradability


def cache_csv_ohlcv(
    csv_path: Path | str,
    cache_dir: Path | str,
    symbol: str,
    market: str,
    source: str = "csv",
    asset_class: str = "",
    tradability: str = "",
    currency: str = "",
    timezone: str = "",
) -> dict[str, object]:
    frame = load_csv(csv_path, symbol=symbol, market=market)
    return write_ohlcv_cache(
        frame,
        cache_dir,
        symbol=symbol,
        market=market,
        source=source,
        source_path=str(Path(csv_path).resolve()),
        asset_class=asset_class,
        tradability=tradability,
        currency=currency,
        timezone=timezone,
    )


def cache_yahoo_ohlcv(
    universe_path: Path | str,
    cache_dir: Path | str,
    limit: int | None = None,
    allow_insecure_ssl: bool = False,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    universe = load_universe(universe_path)
    errors: list[dict[str, str]] = []
    data = fetch_yahoo_universe(universe, limit=limit, allow_insecure_ssl=allow_insecure_ssl, errors=errors)
    rows = []
    by_symbol = {row["symbol"]: row for row in universe}
    for symbol, frame in data.items():
        row = by_symbol.get(symbol, {})
        market = row.get("market", "YAHOO")
        rows.append(
            write_ohlcv_cache(
                frame,
                cache_dir,
                symbol=symbol,
                market=market,
                source="yahoo",
                source_path=str(universe_path),
                asset_class=row.get("asset_class", ""),
                tradability=row.get("tradability", ""),
                currency=row.get("currency", ""),
                timezone=row.get("timezone", ""),
            )
        )
    return pd.DataFrame(rows), pd.DataFrame(errors)


def write_ohlcv_cache(
    frame: pd.DataFrame,
    cache_dir: Path | str,
    symbol: str,
    market: str,
    source: str,
    source_path: str = "",
    asset_class: str = "",
    tradability: str = "",
    currency: str = "",
    timezone: str = "",
) -> dict[str, object]:
    normalized = normalize_ohlcv(frame, symbol=symbol, market=market)
    quality = assess_ohlcv_quality(normalized, symbol=symbol, market=market)
    root = Path(cache_dir)
    asset_dir = root / safe_name(market)
    asset_dir.mkdir(parents=True, exist_ok=True)
    stem = safe_name(symbol)
    csv_path = asset_dir / f"{stem}.csv"
    meta_path = asset_dir / f"{stem}.metadata.json"
    normalized.to_csv(csv_path, index=False)
    metadata = {
        "symbol": symbol,
        "market": market,
        "source": source,
        "source_path": source_path,
        "cache_path": str(csv_path),
        "metadata_path": str(meta_path),
        "asset_class": asset_class or infer_asset_class(symbol, market),
        "tradability": tradability or infer_tradability(symbol, market, source),
        "currency": currency,
        "timezone": timezone,
        "quality_score": quality.quality_score,
        "quality_grade": quality.quality_grade,
        "quality_warnings": "|".join(quality.warnings),
        "gap_ratio": quality.gap_ratio,
        "max_abs_daily_return": quality.max_abs_daily_return,
        "bars": int(len(normalized)),
        "start": str(pd.Timestamp(normalized["datetime"].iloc[0]).date()),
        "end": str(pd.Timestamp(normalized["datetime"].iloc[-1]).date()),
    }
    meta_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    refresh_cache_index(root)
    return metadata


def refresh_cache_index(cache_dir: Path | str) -> pd.DataFrame:
    root = Path(cache_dir)
    rows = []
    for path in sorted(root.glob("*/*.metadata.json")):
        try:
            rows.append(json.loads(path.read_text(encoding="utf-8")))
        except Exception as exc:
            rows.append({"metadata_path": str(path), "error": str(exc)})
    index = pd.DataFrame(rows)
    if not index.empty:
        index.to_csv(root / "cache_index.csv", index=False)
    return index


def load_cache_index(path: Path | str) -> pd.DataFrame:
    index = pd.read_csv(path)
    required = {"symbol", "market", "cache_path"}
    missing = required - set(index.columns)
    if missing:
        raise ValueError(f"cache index missing fields: {sorted(missing)}")
    return index


def safe_name(value: object) -> str:
    text = str(value).strip()
    text = re.sub(r"[^A-Za-z0-9_.-]+", "_", text)
    return text.strip("_") or "UNKNOWN"
