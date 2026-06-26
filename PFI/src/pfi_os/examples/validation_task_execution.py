from __future__ import annotations

import argparse
from pathlib import Path

from pfi_os.config import PROJECT_ROOT
from pfi_os.research import write_validation_task_execution


def main() -> None:
    parser = argparse.ArgumentParser(description="Execute one research-only validation task and write a traceable execution record.")
    parser.add_argument("--as-of", default=None, help="Execution date in YYYY-MM-DD format. Defaults to today.")
    parser.add_argument("--project-root", default=str(PROJECT_ROOT), help="PFI_OS / PFIOS project root.")
    parser.add_argument("--queue-path", default=None, help="ValidationTasks.json path. Defaults to data/validationQueue/ValidationTasks.json.")
    parser.add_argument("--output-dir", default=None, help="Output directory. Defaults to data/validationQueue.")
    parser.add_argument("--task-id", default=None, help="Specific validation task id. Defaults to the top runnable CrossSourceValidation task.")
    parser.add_argument("--symbol", default=None, help="Override symbol.")
    parser.add_argument("--market", default=None, help="Override market.")
    parser.add_argument("--provider", action="append", default=None, help="Provider name. Repeat to force provider list.")
    parser.add_argument("--start", default="2024-01-01", help="Validation start date.")
    parser.add_argument("--end", default="2024-01-31", help="Validation end date.")
    parser.add_argument("--interval", default="1d", help="Bar interval.")
    parser.add_argument("--tolerance", type=float, default=0.01, help="Maximum close-price difference tolerance.")
    args = parser.parse_args()

    common = {
        "as_of": args.as_of,
        "project_root": Path(args.project_root),
        "task_id": args.task_id,
        "symbol": args.symbol,
        "market": args.market,
        "providers": args.provider,
        "start": args.start,
        "end": args.end,
        "interval": args.interval,
        "tolerance_pct": args.tolerance,
    }
    if args.queue_path:
        common["queue_path"] = Path(args.queue_path)
    payload = write_validation_task_execution(
        output_dir=Path(args.output_dir) if args.output_dir else None,
        **common,
    )
    print(
        "VALIDATION_TASK_EXECUTION: "
        f"status={payload.get('execution_status', '')} "
        f"evidence={payload.get('evidence_status', '')} "
        f"task_id={payload.get('task_id', '')} "
        f"symbol={payload.get('symbol', '')} "
        f"market={payload.get('market', '')}"
    )
    print(f"providers_requested: {payload.get('providers_requested', [])}")
    print(f"providers_used: {payload.get('providers_used', [])}")
    print(f"blockers: {payload.get('blockers', [])}")
    if payload.get("error"):
        print(f"error: {payload['error']}")
    if payload.get("outputs"):
        print(f"VALIDATION_TASK_EXECUTION_OUTPUTS: {payload['outputs']}")


if __name__ == "__main__":
    main()
