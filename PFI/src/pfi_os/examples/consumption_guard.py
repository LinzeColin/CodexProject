from __future__ import annotations

import argparse
import json
from pathlib import Path

from pfi_os.config import PROJECT_ROOT
from pfi_os.consumption import build_consumption_guard, write_consumption_guard


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the PFI_OS Consumption Guard snapshot.")
    parser.add_argument("--as-of", default=None, help="Snapshot date in YYYY-MM-DD format. Defaults to today.")
    parser.add_argument("--project-root", default=str(PROJECT_ROOT), help="PFI_OS / PFIOS project root.")
    parser.add_argument("--event-path", default=None, help="Optional consumption event JSON path.")
    parser.add_argument("--output-dir", default=None, help="Optional output directory. Defaults to data/consumption.")
    parser.add_argument("--lookback-days", type=int, default=30, help="Lookback window for spending summaries.")
    parser.add_argument("--monthly-investable-budget", type=float, default=0.0, help="Optional monthly investable cashflow budget.")
    parser.add_argument("--json-only", action="store_true", help="Build and print JSON without writing files.")
    parser.add_argument("--summary-json", action="store_true", help="Print only PFIOSConsumptionGuardRuntimeSummaryV1 for low-token checks.")
    args = parser.parse_args()

    common = {
        "as_of": args.as_of,
        "project_root": Path(args.project_root),
        "event_path": Path(args.event_path).expanduser() if args.event_path else None,
        "lookback_days": args.lookback_days,
        "monthly_investable_budget": args.monthly_investable_budget,
    }
    if args.json_only or args.summary_json:
        payload = build_consumption_guard(**common)
        if args.summary_json:
            print(json.dumps(payload.get("runtime_summary", {}), ensure_ascii=False, indent=2, default=str))
            return
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
        return
    payload = write_consumption_guard(output_dir=Path(args.output_dir).expanduser() if args.output_dir else None, **common)
    summary = payload["summary"]
    print(
        "PFI_OS_CONSUMPTION_GUARD: "
        f"status={payload['guard_status']} "
        f"spend={summary.get('counted_spend')} "
        f"impulse={summary.get('impulse_spend')} "
        f"pressure={summary.get('investable_cashflow_pressure')} "
        f"as_of={payload['as_of']}"
    )
    print(f"PFI_OS_CONSUMPTION_RUNTIME_STATUS: {payload.get('runtime_summary', {}).get('status')}")
    print(f"PFI_OS_CONSUMPTION_OUTPUTS: {payload.get('outputs', {})}")


if __name__ == "__main__":
    main()
