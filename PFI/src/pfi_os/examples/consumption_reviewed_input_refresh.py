from __future__ import annotations

import argparse
import json
from pathlib import Path

from pfi_os.config import PROJECT_ROOT
from pfi_os.consumption import refresh_consumption_from_reviewed_input


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh Consumption Guard outputs from a local reviewed input file.")
    parser.add_argument("--as-of", default=None, help="Snapshot date in YYYY-MM-DD format. Defaults to today.")
    parser.add_argument("--project-root", default=str(PROJECT_ROOT), help="PFI_OS / PFIOS project root.")
    parser.add_argument("--event-path", default=None, help="Reviewed consumption input JSON. Defaults to data/private/consumption/ConsumptionGuardReviewedInput.json.")
    parser.add_argument("--output-dir", default=None, help="Output directory. Defaults to data/consumption.")
    parser.add_argument("--lookback-days", type=int, default=30, help="Lookback window for spending summaries.")
    parser.add_argument("--monthly-investable-budget", type=float, default=0.0, help="Optional monthly investable cashflow budget.")
    parser.add_argument("--json", action="store_true", help="Print PFIOSConsumptionGuardReviewedInputRefreshV1 as JSON.")
    args = parser.parse_args()

    payload = refresh_consumption_from_reviewed_input(
        as_of=args.as_of,
        project_root=Path(args.project_root),
        event_path=Path(args.event_path).expanduser() if args.event_path else None,
        output_dir=Path(args.output_dir).expanduser() if args.output_dir else None,
        lookback_days=args.lookback_days,
        monthly_investable_budget=args.monthly_investable_budget,
    )
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
        return
    summary = payload.get("summary", {}) if isinstance(payload.get("summary"), dict) else {}
    print(
        "PFI_OS_CONSUMPTION_REVIEWED_INPUT_REFRESH: "
        f"status={payload['status']} "
        f"guard_status={payload['guard_status']} "
        f"input_status={payload['input_status']} "
        f"spend={summary.get('counted_spend')} "
        f"impulse={summary.get('impulse_spend')} "
        f"pressure={summary.get('investable_cashflow_pressure')} "
        f"as_of={payload['as_of']}"
    )
    if payload.get("next_action"):
        print(f"PFI_OS_CONSUMPTION_NEXT_ACTION: {payload['next_action']}")
    if payload.get("outputs"):
        print(f"PFI_OS_CONSUMPTION_REVIEWED_INPUT_OUTPUTS: {payload['outputs']}")


if __name__ == "__main__":
    main()
