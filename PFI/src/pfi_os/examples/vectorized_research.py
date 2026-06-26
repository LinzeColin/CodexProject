from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from pfi_os.config import PROJECT_ROOT
from pfi_os.research.vectorized import build_vectorized_research, write_vectorized_research


def main() -> None:
    parser = argparse.ArgumentParser(description="Run PFI_OS Vectorized Research Mode from EventReplay_latest.json.")
    parser.add_argument("--project-root", default=str(PROJECT_ROOT), help="PFI_OS / PFIOS project root.")
    parser.add_argument("--replay", default=None, help="Optional EventReplay JSON path. Defaults to data/replay/EventReplay_latest.json.")
    parser.add_argument("--output-dir", default=None, help="Optional output directory. Defaults to data/vectorized.")
    parser.add_argument("--symbol", default=None, help="Optional symbol filter, for example SPY.")
    parser.add_argument("--market", default=None, help="Optional market filter, for example US.")
    parser.add_argument("--interval", default=None, help="Optional interval filter, for example 1d.")
    parser.add_argument("--strategy", default="ma_crossover", help="Strategy id. MVP supports ma_crossover.")
    parser.add_argument("--param", action="append", default=[], help="Grid item such as short_window=2,3. Repeat for multiple parameters.")
    parser.add_argument("--initial-cash", type=float, default=100_000.0)
    parser.add_argument("--as-of", default=None, help="Snapshot date in YYYY-MM-DD format. Defaults to today.")
    parser.add_argument("--json-only", action="store_true", help="Build and print status without writing files.")
    args = parser.parse_args()

    common = {
        "project_root": Path(args.project_root),
        "replay_path": Path(args.replay) if args.replay else None,
        "symbol": args.symbol,
        "market": args.market,
        "interval": args.interval,
        "strategy_id": args.strategy,
        "param_grid": _parse_param_grid(args.param) or None,
        "initial_cash": args.initial_cash,
        "as_of": args.as_of,
    }
    if args.json_only:
        payload = build_vectorized_research(**common)
    else:
        payload = write_vectorized_research(output_dir=Path(args.output_dir) if args.output_dir else None, **common)
    print(
        "PFI_OS_VECTORIZED_RESEARCH: "
        f"status={payload['status']} "
        f"symbol={payload['selected_symbol']} "
        f"rows={payload['row_count']} "
        f"runs={payload['scan_run_count']}/{payload['parameter_run_count']} "
        f"strategy={payload['strategy_id']} "
        f"as_of={payload['as_of']}"
    )
    if payload.get("outputs"):
        print(f"PFI_OS_VECTORIZED_RESEARCH_OUTPUTS: {payload['outputs']}")


def _parse_param_grid(values: list[str]) -> dict[str, list[Any]]:
    grid: dict[str, list[Any]] = {}
    for value in values:
        key, sep, raw = value.partition("=")
        if not sep:
            raise SystemExit(f"Invalid --param value, expected key=v1,v2: {value}")
        key = key.strip()
        if not key:
            raise SystemExit(f"Invalid --param key: {value}")
        parsed = [_parse_scalar(item.strip()) for item in raw.split(",") if item.strip()]
        if not parsed:
            raise SystemExit(f"Invalid --param values: {value}")
        grid[key] = parsed
    return grid


def _parse_scalar(value: str) -> Any:
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    try:
        number = float(value)
    except ValueError:
        return value
    return int(number) if number.is_integer() else number


if __name__ == "__main__":
    main()
