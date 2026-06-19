from __future__ import annotations

import argparse
import json
from pathlib import Path

from quantlab.config import PROJECT_ROOT, REPORT_ROOT_DIR
from quantlab.value import build_token_roi_ledger, write_token_roi_ledger


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the EVA_OS Token ROI Ledger from local research outputs.")
    parser.add_argument("--date", default=None, help="Ledger date in YYYY-MM-DD format. Defaults to today.")
    parser.add_argument("--project-root", default=str(PROJECT_ROOT), help="EVA_OS / QuantLab project root.")
    parser.add_argument("--report-root", default=str(REPORT_ROOT_DIR), help="Research report root.")
    parser.add_argument("--output-dir", default="", help="Optional output directory for JSON/CSV/Markdown/PDF artifacts.")
    parser.add_argument("--manual-entry-path", default=None, help="Optional reviewed/manual Token ROI entry JSON.")
    parser.add_argument("--artifact-limit", type=int, default=300, help="Maximum artifacts to include.")
    parser.add_argument("--json", action="store_true", help="Print the full JSON payload.")
    parser.add_argument("--summary-json", action="store_true", help="Print only EVATokenROIRuntimeSummaryV1 for low-token checks.")
    args = parser.parse_args()

    common = {
        "as_of": args.date,
        "project_root": Path(args.project_root).expanduser(),
        "report_root": Path(args.report_root).expanduser(),
        "manual_entry_path": Path(args.manual_entry_path).expanduser() if args.manual_entry_path else None,
        "artifact_limit": args.artifact_limit,
    }
    if args.output_dir:
        payload = write_token_roi_ledger(**common, output_dir=Path(args.output_dir).expanduser())
    else:
        payload = build_token_roi_ledger(**common)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
        return
    if args.summary_json:
        print(json.dumps(payload.get("runtime_summary", {}), ensure_ascii=False, indent=2, default=str))
        return
    summary = payload["summary"]
    runtime = payload.get("runtime_summary", {})
    totals = runtime.get("financial_totals", {})
    print(f"EVA_TOKEN_ROI_LEDGER: status={runtime.get('status', 'Unknown')} records={payload['record_count']} as_of={payload['as_of']}")
    print(f"quantified_records: {summary['quantified_records']}")
    print(f"unquantified_records: {summary['unquantified_records']}")
    print(f"benefit_total: {totals.get('benefit_total', 0.0)}")
    print(f"cost_total: {totals.get('cost_total', 0.0)}")
    print(f"aggregate_roi_score: {totals.get('aggregate_roi_score')}")
    print("financial_totals:", summary["financial_totals"])
    if args.output_dir and "outputs" in payload:
        print("")
        print(f"json: {payload['outputs']['json']}")
        print(f"csv: {payload['outputs']['csv']}")
        print(f"markdown: {payload['outputs']['markdown']}")
        print(f"pdf: {payload['outputs']['pdf']}")
        print(f"runtime_summary_json: {payload['outputs']['runtime_summary_json']}")


if __name__ == "__main__":
    main()
