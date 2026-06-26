from __future__ import annotations

import argparse
import json
from pathlib import Path

from pfi_os.business import build_cashflow_command, write_cashflow_command
from pfi_os.config import PROJECT_ROOT


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the PFI_OS Company CashFlow Command snapshot.")
    parser.add_argument("--as-of", default=None, help="Snapshot date in YYYY-MM-DD format. Defaults to today.")
    parser.add_argument("--project-root", default=str(PROJECT_ROOT), help="PFI_OS / PFIOS project root.")
    parser.add_argument("--entry-path", default=None, help="Optional cashflow entry JSON path.")
    parser.add_argument("--output-dir", default=None, help="Optional output directory. Defaults to data/cashflow.")
    parser.add_argument("--lookback-days", type=int, default=30, help="Lookback window for inflow/outflow summaries.")
    parser.add_argument("--json-only", action="store_true", help="Build and print JSON without writing files.")
    parser.add_argument("--summary-json", action="store_true", help="Print only PFIOSCompanyCashFlowRuntimeSummaryV1 for low-token checks.")
    args = parser.parse_args()

    common = {
        "as_of": args.as_of,
        "project_root": Path(args.project_root),
        "entry_path": Path(args.entry_path).expanduser() if args.entry_path else None,
        "lookback_days": args.lookback_days,
    }
    if args.json_only or args.summary_json:
        payload = build_cashflow_command(**common)
        if args.summary_json:
            print(json.dumps(payload.get("runtime_summary", {}), ensure_ascii=False, indent=2, default=str))
            return
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
        return
    payload = write_cashflow_command(output_dir=Path(args.output_dir).expanduser() if args.output_dir else None, **common)
    summary = payload["summary"]
    print(
        "PFI_OS_CASHFLOW_COMMAND: "
        f"status={payload['cashflow_status']} "
        f"balance={summary.get('latest_balance')} "
        f"net={summary.get('net_cashflow')} "
        f"runway_days={summary.get('runway_days')} "
        f"as_of={payload['as_of']}"
    )
    print(f"PFI_OS_CASHFLOW_RUNTIME_STATUS: {payload.get('runtime_summary', {}).get('status')}")
    print(f"PFI_OS_CASHFLOW_OUTPUTS: {payload.get('outputs', {})}")


if __name__ == "__main__":
    main()
