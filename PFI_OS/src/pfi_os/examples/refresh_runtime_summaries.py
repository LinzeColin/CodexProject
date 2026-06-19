from __future__ import annotations

import argparse
import json
from pathlib import Path

from pfi_os.config import PROJECT_ROOT, REPORT_ROOT_DIR
from pfi_os.executive import refresh_runtime_summary_latest


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh compact PFI_OS runtime summary latest artifacts.")
    parser.add_argument("--as-of", default=None, help="Snapshot date in YYYY-MM-DD format. Defaults to today.")
    parser.add_argument("--project-root", default=str(PROJECT_ROOT), help="PFI_OS / PFIOS project root.")
    parser.add_argument("--report-root", default=str(REPORT_ROOT_DIR), help="Report artifact root kept for command compatibility.")
    parser.add_argument("--artifact-limit", type=int, default=300, help="Reserved compatibility limit; not used by retired value-layer refresh.")
    parser.add_argument("--lookback-days", type=int, default=30, help="Cashflow and consumption lookback window.")
    parser.add_argument("--monthly-investable-budget", type=float, default=0.0, help="Consumption Guard planning budget.")
    parser.add_argument("--cashflow-entry-path", default=None, help="Optional reviewed Company CashFlow input JSON.")
    parser.add_argument("--policy-entry-path", default=None, help="Optional reviewed Policy Intelligence input JSON.")
    parser.add_argument("--consumption-event-path", default=None, help="Optional reviewed Consumption Guard event JSON.")
    parser.add_argument("--json", action="store_true", help="Print PFIOSRuntimeSummaryRefreshV1 as JSON.")
    args = parser.parse_args()

    payload = refresh_runtime_summary_latest(
        as_of=args.as_of,
        project_root=Path(args.project_root),
        report_root=Path(args.report_root),
        artifact_limit=args.artifact_limit,
        lookback_days=args.lookback_days,
        monthly_investable_budget=args.monthly_investable_budget,
        cashflow_entry_path=Path(args.cashflow_entry_path).expanduser() if args.cashflow_entry_path else None,
        policy_entry_path=Path(args.policy_entry_path).expanduser() if args.policy_entry_path else None,
        consumption_event_path=Path(args.consumption_event_path).expanduser() if args.consumption_event_path else None,
    )
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
        return
    print(
        "PFI_OS_RUNTIME_SUMMARIES: "
        f"status={payload['status']} summaries={payload['summary_count']} as_of={payload['as_of']}"
    )
    for row in payload["outputs"]:
        print(
            "PFI_OS_RUNTIME_SUMMARY: "
            f"subsystem={row['subsystem']} "
            f"schema={row['schema']} "
            f"runtime_status={row['runtime_status']} "
            f"latest={row['latest_runtime_summary_json']}"
        )


if __name__ == "__main__":
    main()
