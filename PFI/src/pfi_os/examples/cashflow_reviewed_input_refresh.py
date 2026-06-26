from __future__ import annotations

import argparse
import json
from pathlib import Path

from pfi_os.business import refresh_cashflow_from_reviewed_input
from pfi_os.config import PROJECT_ROOT


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh Company CashFlow outputs from a local reviewed input file.")
    parser.add_argument("--as-of", default=None, help="Snapshot date in YYYY-MM-DD format. Defaults to today.")
    parser.add_argument("--project-root", default=str(PROJECT_ROOT), help="PFI_OS / PFIOS project root.")
    parser.add_argument("--entry-path", default=None, help="Reviewed cashflow input JSON. Defaults to data/private/cashflow/CompanyCashFlowReviewedInput.json.")
    parser.add_argument("--output-dir", default=None, help="Output directory. Defaults to data/cashflow.")
    parser.add_argument("--lookback-days", type=int, default=30, help="Lookback window for inflow/outflow summaries.")
    parser.add_argument("--json", action="store_true", help="Print PFIOSCompanyCashFlowReviewedInputRefreshV1 as JSON.")
    args = parser.parse_args()

    payload = refresh_cashflow_from_reviewed_input(
        as_of=args.as_of,
        project_root=Path(args.project_root),
        entry_path=Path(args.entry_path).expanduser() if args.entry_path else None,
        output_dir=Path(args.output_dir).expanduser() if args.output_dir else None,
        lookback_days=args.lookback_days,
    )
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
        return
    summary = payload.get("summary", {}) if isinstance(payload.get("summary"), dict) else {}
    print(
        "PFI_OS_CASHFLOW_REVIEWED_INPUT_REFRESH: "
        f"status={payload['status']} "
        f"cashflow_status={payload['cashflow_status']} "
        f"input_status={payload['input_status']} "
        f"balance={summary.get('latest_balance')} "
        f"net={summary.get('net_cashflow')} "
        f"runway_days={summary.get('runway_days')} "
        f"as_of={payload['as_of']}"
    )
    if payload.get("next_action"):
        print(f"PFI_OS_CASHFLOW_NEXT_ACTION: {payload['next_action']}")
    if payload.get("outputs"):
        print(f"PFI_OS_CASHFLOW_REVIEWED_INPUT_OUTPUTS: {payload['outputs']}")


if __name__ == "__main__":
    main()
