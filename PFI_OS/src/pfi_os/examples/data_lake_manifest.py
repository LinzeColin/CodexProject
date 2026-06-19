from __future__ import annotations

import argparse
from pathlib import Path

from pfi_os.config import PROJECT_ROOT
from pfi_os.data.lake import build_data_lake_manifest, write_data_lake_manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the PFI_OS reproducible data lake manifest.")
    parser.add_argument("--as-of", default=None, help="Snapshot date in YYYY-MM-DD format. Defaults to today.")
    parser.add_argument("--project-root", default=str(PROJECT_ROOT), help="PFI_OS / PFIOS project root.")
    parser.add_argument("--output-dir", default=None, help="Optional output directory. Defaults to data/dataLake.")
    parser.add_argument("--no-cache", action="store_true", help="Skip structured bar cache discovery.")
    parser.add_argument("--no-market-events", action="store_true", help="Skip MarketEventLog JSONL discovery.")
    parser.add_argument("--json-only", action="store_true", help="Build and print status without writing files.")
    args = parser.parse_args()

    common = {
        "project_root": Path(args.project_root),
        "as_of": args.as_of,
        "include_cache": not args.no_cache,
        "include_market_events": not args.no_market_events,
    }
    if args.json_only:
        payload = build_data_lake_manifest(**common)
    else:
        payload = write_data_lake_manifest(output_dir=Path(args.output_dir) if args.output_dir else None, **common)
    print(
        "PFI_OS_DATA_LAKE_MANIFEST: "
        f"status={payload['lake_status']} "
        f"assets={payload['asset_count']} "
        f"partitions={payload['partition_count']} "
        f"cursors={payload['replay_cursor_count']} "
        f"as_of={payload['as_of']}"
    )
    if payload.get("outputs"):
        print(f"PFI_OS_DATA_LAKE_MANIFEST_OUTPUTS: {payload['outputs']}")


if __name__ == "__main__":
    main()
