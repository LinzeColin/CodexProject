from __future__ import annotations

import argparse
from pathlib import Path

from pfi_os.config import PROJECT_ROOT
from pfi_os.data.replay import build_event_replay, write_event_replay


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a deterministic PFI_OS event replay batch.")
    parser.add_argument("--as-of", default=None, help="Snapshot date in YYYY-MM-DD format. Defaults to today.")
    parser.add_argument("--project-root", default=str(PROJECT_ROOT), help="PFI_OS / PFIOS project root.")
    parser.add_argument("--manifest", default=None, help="Optional DataLakeManifest JSON path.")
    parser.add_argument("--cursors", default=None, help="Optional replay cursor JSON path.")
    parser.add_argument("--output-dir", default=None, help="Optional output directory. Defaults to data/replay.")
    parser.add_argument("--cursor-id", default=None, help="Replay cursor id to select.")
    parser.add_argument("--dataset", default=None, help="Cursor dataset filter, for example market_events.")
    parser.add_argument("--market", default=None, help="Cursor market filter, for example US.")
    parser.add_argument("--symbol", default=None, help="Cursor symbol filter, for example SPY.")
    parser.add_argument("--interval", default=None, help="Cursor interval filter, for example 1d.")
    parser.add_argument("--source", default=None, help="Cursor source filter, for example sample.")
    parser.add_argument("--start-after", default=None, help="Replay events strictly after this event_time.")
    parser.add_argument("--end-at", default=None, help="Replay events at or before this event_time.")
    parser.add_argument("--limit", type=int, default=None, help="Maximum emitted events.")
    parser.add_argument("--json-only", action="store_true", help="Build and print status without writing files.")
    args = parser.parse_args()

    common = {
        "project_root": Path(args.project_root),
        "manifest_path": Path(args.manifest) if args.manifest else None,
        "cursors_path": Path(args.cursors) if args.cursors else None,
        "cursor_id": args.cursor_id,
        "dataset": args.dataset,
        "market": args.market,
        "symbol": args.symbol,
        "interval": args.interval,
        "source": args.source,
        "start_after": args.start_after,
        "end_at": args.end_at,
        "limit": args.limit,
        "as_of": args.as_of,
    }
    if args.json_only:
        payload = build_event_replay(**common)
    else:
        payload = write_event_replay(output_dir=Path(args.output_dir) if args.output_dir else None, **common)
    print(
        "PFI_OS_EVENT_REPLAY: "
        f"status={payload['replay_status']} "
        f"events={payload['event_count']} "
        f"cursors={payload['cursor_count']} "
        f"assets={payload['asset_count']} "
        f"next_after={payload['next_after']} "
        f"as_of={payload['as_of']}"
    )
    if payload.get("outputs"):
        print(f"PFI_OS_EVENT_REPLAY_OUTPUTS: {payload['outputs']}")


if __name__ == "__main__":
    main()
