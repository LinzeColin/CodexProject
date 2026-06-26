from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from pfi_os.config import PROJECT_ROOT
from pfi_os.data.market_events import build_market_event_log, write_market_event_log
from pfi_os.data.models import BarDataRequest
from pfi_os.data.providers.sample_provider import SampleDataProvider


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a local PFI_OS market event log from sample bars or a CSV file.")
    parser.add_argument("--as-of", default=None, help="Snapshot date in YYYY-MM-DD format. Defaults to today.")
    parser.add_argument("--project-root", default=str(PROJECT_ROOT), help="PFI_OS / PFIOS project root.")
    parser.add_argument("--output-dir", default=None, help="Optional output directory. Defaults to data/marketEvents.")
    parser.add_argument("--symbol", default="SPY", help="Market symbol.")
    parser.add_argument("--market", default="US", help="Market code.")
    parser.add_argument("--interval", default="1d", help="Bar interval.")
    parser.add_argument("--start", default="2026-01-01", help="Start date for sample data.")
    parser.add_argument("--end", default="2026-01-10", help="End date for sample data.")
    parser.add_argument("--source", default="sample", help="Source label recorded on each event.")
    parser.add_argument("--input-csv", default=None, help="Optional CSV with datetime, open, high, low, close, volume columns.")
    parser.add_argument("--json-only", action="store_true", help="Build and print status without writing files.")
    args = parser.parse_args()

    bars = _load_bars(args)
    common = {
        "symbol": args.symbol,
        "market": args.market,
        "interval": args.interval,
        "source": args.source,
        "as_of": args.as_of,
        "evidence_layer": "OBSERVATION",
    }
    if args.json_only:
        payload = build_market_event_log(bars, **common)
    else:
        payload = write_market_event_log(
            bars,
            output_dir=Path(args.output_dir) if args.output_dir else None,
            project_root=Path(args.project_root),
            **common,
        )
    print(
        "PFI_OS_MARKET_EVENT_LAYER: "
        f"status={payload['event_log_status']} "
        f"events={payload['event_count']} "
        f"symbol={args.market.upper()}:{args.symbol} "
        f"interval={args.interval} "
        f"as_of={payload['as_of']}"
    )
    if payload.get("outputs"):
        print(f"PFI_OS_MARKET_EVENT_LAYER_OUTPUTS: {payload['outputs']}")


def _load_bars(args: argparse.Namespace) -> pd.DataFrame:
    if args.input_csv:
        return pd.read_csv(Path(args.input_csv).expanduser())
    provider = SampleDataProvider(seed=42)
    return provider.get_bars(
        BarDataRequest(
            symbol=args.symbol,
            market=args.market,
            interval=args.interval,
            start=args.start,
            end=args.end,
        )
    )


if __name__ == "__main__":
    main()
