from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Iterable

from pfi_os.analysis import (
    HOTSPOT_REFRESH_TTL_SECONDS,
    SentimentInstrument,
    build_hotspot_history,
    default_hotspot_universe,
    hotspot_cache_directory_summary,
    hotspot_persisted_cache_status,
    hotspot_runtime_cache_key,
    hotspot_runtime_summary,
    invalidate_hotspot_persisted_cache,
    load_hotspot_persisted_cache,
    write_hotspot_persisted_cache,
)
from pfi_os.config import PROJECT_ROOT
from pfi_os.data.models import BarDataRequest
from pfi_os.data.providers.sample_provider import SampleDataProvider


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a compact PFI_OS hotspot runtime summary from deterministic Sample data.")
    parser.add_argument("--market", default="US", choices=["US", "CN", "HK"], help="Market universe.")
    parser.add_argument("--interval", default="60min", choices=["60min", "1d"], help="Hotspot interval.")
    parser.add_argument("--start", default="2026-05-01", help="Display start date.")
    parser.add_argument("--end", default="2026-06-15", help="Display end date.")
    parser.add_argument("--max-snapshots", type=int, default=96, help="Maximum display snapshots.")
    parser.add_argument("--limit", type=int, default=8, help="Maximum instruments from the default universe.")
    parser.add_argument("--symbol", action="append", default=[], help="Optional symbol override. Repeat for multiple symbols.")
    parser.add_argument("--use-persisted-cache", action="store_true", help="Read/write local data/cache/hotspots derived cache.")
    parser.add_argument("--cache-root", default=str(PROJECT_ROOT / "data" / "cache" / "hotspots"), help="Persisted hotspot cache root.")
    parser.add_argument("--cache-status", action="store_true", help="Print current request cache status without loading market bars.")
    parser.add_argument("--invalidate-cache", action="store_true", help="Delete the current request persisted hotspot cache and exit.")
    parser.add_argument("--json-only", action="store_true", help="Print the compact JSON summary only.")
    args = parser.parse_args()

    instruments = _select_instruments(args.market, args.symbol, args.limit)
    request_key = hotspot_runtime_cache_key(
        data_source="Sample",
        market=args.market,
        interval=args.interval,
        instruments=instruments,
        display_start=args.start,
        display_end=args.end,
        max_snapshots=args.max_snapshots,
    )
    cache_source = "computed"
    cache_age_seconds = None
    cache_root = Path(args.cache_root)
    if args.cache_status:
        payload = {
            "request": hotspot_persisted_cache_status(cache_root, request_key=request_key),
            "directory": hotspot_cache_directory_summary(cache_root),
        }
        _print_payload(payload, args.json_only)
        return
    if args.invalidate_cache:
        payload = {
            "invalidate": invalidate_hotspot_persisted_cache(cache_root, request_key=request_key),
            "directory": hotspot_cache_directory_summary(cache_root),
        }
        _print_payload(payload, args.json_only)
        return
    if args.use_persisted_cache:
        persisted = load_hotspot_persisted_cache(cache_root, request_key=request_key)
        if persisted:
            history = persisted["history"]
            errors = persisted["errors"]
            cache_source = "persisted"
            cache_age_seconds = persisted.get("age_seconds")
            summary = hotspot_runtime_summary(
                history,
                errors,
                data_source="Sample",
                market=args.market,
                interval=args.interval,
                requested_count=len(instruments),
                max_snapshots=args.max_snapshots,
                ttl_seconds=HOTSPOT_REFRESH_TTL_SECONDS,
                request_key=request_key,
                cache_source=cache_source,
                persisted_cache_age_seconds=cache_age_seconds,
                request_trace=persisted.get("request_trace", []),
            )
            _print_summary(summary, args.json_only)
            return
    provider = SampleDataProvider(seed=42)
    frames = {}
    errors: list[dict[str, str]] = []
    request_trace: list[dict[str, object]] = []
    for instrument in instruments:
        request = BarDataRequest(
            symbol=instrument.symbol,
            market=instrument.market or args.market,
            interval=args.interval,
            start=args.start,
            end=args.end,
            adjustment="auto",
        )
        started_at = time.perf_counter()
        try:
            bars = provider.get_bars(request)
            frames[instrument.symbol] = bars
            request_trace.append(
                _trace_row(
                    instrument,
                    provider_symbol=instrument.symbol,
                    status="Pass",
                    elapsed_ms=(time.perf_counter() - started_at) * 1000,
                    row_count=len(bars),
                )
            )
        except Exception as exc:
            errors.append({"代码": instrument.symbol, "名称": instrument.name, "错误": str(exc)})
            request_trace.append(
                _trace_row(
                    instrument,
                    provider_symbol=instrument.symbol,
                    status="Fail",
                    elapsed_ms=(time.perf_counter() - started_at) * 1000,
                    row_count=0,
                    error=str(exc),
                )
            )
    history = build_hotspot_history(
        frames,
        instruments,
        data_source="Sample",
        max_snapshots=args.max_snapshots,
        display_start=args.start,
        display_end=args.end,
    )
    summary = hotspot_runtime_summary(
        history,
        errors,
        data_source="Sample",
        market=args.market,
        interval=args.interval,
        requested_count=len(instruments),
        max_snapshots=args.max_snapshots,
        ttl_seconds=HOTSPOT_REFRESH_TTL_SECONDS,
        request_key=request_key,
        cache_source=cache_source,
        persisted_cache_age_seconds=cache_age_seconds,
        request_trace=request_trace,
    )
    if args.use_persisted_cache and not history.empty:
        write_hotspot_persisted_cache(
            cache_root,
            request_key=request_key,
            history=history,
            errors=errors,
            summary=summary,
            request_trace=request_trace,
            ttl_seconds=HOTSPOT_REFRESH_TTL_SECONDS,
        )
    _print_summary(summary, args.json_only)


def _print_summary(summary: dict[str, object], json_only: bool) -> None:
    if json_only:
        print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
        return
    print(
        "PFI_OS_HOTSPOT_RUNTIME: "
        f"status={summary['status']} "
        f"market={summary['market']} "
        f"objects={summary['success_count']}/{summary['requested_count']} "
        f"slices={summary['slice_count']} "
        f"rows={summary['row_count']} "
        f"ttl={summary['ttl_seconds']} "
        f"cache={summary['cache_source']} "
        f"key={summary['request_key']} "
        f"elapsed_ms={summary.get('request_trace', {}).get('total_elapsed_ms', 0)}"
    )


def _print_payload(payload: dict[str, object], json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def _select_instruments(market: str, symbols: Iterable[str], limit: int) -> list[SentimentInstrument]:
    universe = default_hotspot_universe(market)
    symbol_values = [symbol.strip() for symbol in symbols if symbol.strip()]
    if not symbol_values:
        return universe[: max(1, int(limit))]
    lookup = {item.symbol.upper(): item for item in universe}
    selected: list[SentimentInstrument] = []
    for symbol in symbol_values:
        selected.append(lookup.get(symbol.upper(), SentimentInstrument(symbol, symbol, market, "自选观察")))
    return selected[: max(1, int(limit))]


def _trace_row(
    instrument: SentimentInstrument,
    *,
    provider_symbol: str,
    status: str,
    elapsed_ms: float,
    row_count: int,
    error: str = "",
) -> dict[str, object]:
    return {
        "symbol": instrument.symbol,
        "name": instrument.name,
        "market": instrument.market,
        "provider_symbol": provider_symbol,
        "status": status,
        "elapsed_ms": round(float(elapsed_ms), 2),
        "row_count": int(row_count),
        "error": error,
    }


if __name__ == "__main__":
    main()
