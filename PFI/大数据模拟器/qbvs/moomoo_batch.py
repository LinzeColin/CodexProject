from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Any

import pandas as pd

from qbvs.cache import refresh_cache_index
from qbvs.datasources import cache_moomoo_history
from qbvs.symbol_aliases import normalize_moomoo_source_symbol


@dataclass(frozen=True)
class MoomooBatchConfig:
    universe: Path | str
    cache_dir: Path | str
    attempts_output: Path | str
    summary_output: Path | str
    start: str
    end: str
    offset: int = 0
    limit: int | None = None
    host: str = "127.0.0.1"
    port: int = 11111
    ktype: str = "K_DAY"
    autype: str = "QFQ"


def cache_moomoo_batch(
    config: MoomooBatchConfig,
    cache_func: Callable[..., dict[str, object]] = cache_moomoo_history,
) -> dict[str, Path]:
    universe = pd.read_csv(config.universe)
    _validate_universe_columns(universe)
    selected = universe.iloc[config.offset :]
    if config.limit is not None:
        selected = selected.head(config.limit)
    attempts_path = Path(config.attempts_output)
    summary_path = Path(config.summary_output)
    attempts_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    for batch_index, (_, row) in enumerate(selected.iterrows(), start=1):
        market = str(row["market"])
        alias = normalize_moomoo_source_symbol(
            symbol=str(row["symbol"]),
            market=market,
            source_symbol=str(row.get("source_symbol") or row["symbol"]),
        )
        source_symbol = alias.normalized_source_symbol
        attempt = {
            "batch_index": batch_index,
            "universe_index": int(row.name),
            "symbol": str(row["symbol"]),
            "source_symbol": source_symbol,
            "original_source_symbol": alias.original_source_symbol,
            "source_symbol_rule": alias.rule_id,
            "source_symbol_requires_probe": alias.requires_single_symbol_probe,
            "market": market,
            "asset_class": str(row.get("asset_class", "")),
            "tradability": str(row.get("tradability", "")),
            "returncode": 0,
            "cache_path": "",
            "metadata_path": "",
            "error": "",
        }
        try:
            cached = cache_func(
                symbol=source_symbol,
                market=market,
                cache_dir=config.cache_dir,
                start=config.start,
                end=config.end,
                host=config.host,
                port=config.port,
                ktype=config.ktype,
                autype=config.autype,
                asset_class=str(row.get("asset_class", "")),
                tradability=str(row.get("tradability", "")),
                currency=str(row.get("currency", "")),
                timezone=str(row.get("timezone", "")),
            )
            attempt["cache_path"] = str(cached.get("cache_path", ""))
            attempt["metadata_path"] = str(cached.get("metadata_path", ""))
        except Exception as exc:
            attempt["returncode"] = 1
            attempt["error"] = str(exc)
        rows.append(attempt)
        pd.DataFrame(rows).to_csv(attempts_path, index=False)

    cache_index = refresh_cache_index(config.cache_dir)
    attempts = pd.DataFrame(rows)
    summary = {
        "universe": str(config.universe),
        "cache_dir": str(config.cache_dir),
        "attempts_output": str(attempts_path),
        "cache_index": str(Path(config.cache_dir) / "cache_index.csv"),
        "offset": config.offset,
        "limit": config.limit,
        "requested_rows": int(len(selected)),
        "success": int((attempts["returncode"] == 0).sum()) if not attempts.empty else 0,
        "failed": int((attempts["returncode"] != 0).sum()) if not attempts.empty else 0,
        "cached_rows": int(len(cache_index)),
        "starts_background_processes": False,
        "writes_quantlab_database": False,
        "writes_quantlab_source": False,
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"attempts": attempts_path, "summary": summary_path, "cache_index": Path(config.cache_dir) / "cache_index.csv"}


def _validate_universe_columns(frame: pd.DataFrame) -> None:
    required = {"symbol", "market"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"Moomoo batch universe missing columns: {missing}")
