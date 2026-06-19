from __future__ import annotations

import argparse
import json
from pathlib import Path

from quantlab.config import PROJECT_ROOT, REPORT_ROOT_DIR
from quantlab.value import refresh_token_roi_from_reviewed_input


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh Token ROI outputs from a local reviewed value evidence file.")
    parser.add_argument("--as-of", default=None, help="Snapshot date in YYYY-MM-DD format. Defaults to today.")
    parser.add_argument("--project-root", default=str(PROJECT_ROOT), help="EVA_OS / QuantLab project root.")
    parser.add_argument("--report-root", default=str(REPORT_ROOT_DIR), help="Report artifact root used by Token ROI.")
    parser.add_argument("--entry-path", default=None, help="Reviewed value evidence JSON. Defaults to data/private/value/TokenROIReviewedValueEvidence.json.")
    parser.add_argument("--output-dir", default=None, help="Output directory. Defaults to data/value.")
    parser.add_argument("--artifact-limit", type=int, default=300, help="Maximum existing artifacts to include.")
    parser.add_argument("--json", action="store_true", help="Print EVATokenROIReviewedValueEvidenceRefreshV1 as JSON.")
    args = parser.parse_args()

    payload = refresh_token_roi_from_reviewed_input(
        as_of=args.as_of,
        project_root=Path(args.project_root),
        report_root=Path(args.report_root),
        entry_path=Path(args.entry_path).expanduser() if args.entry_path else None,
        output_dir=Path(args.output_dir).expanduser() if args.output_dir else None,
        artifact_limit=args.artifact_limit,
    )
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
        return
    summary = payload.get("summary", {}) if isinstance(payload.get("summary"), dict) else {}
    totals = summary.get("financial_totals", {}) if isinstance(summary.get("financial_totals"), dict) else {}
    print(
        "EVA_OS_TOKEN_ROI_REVIEWED_VALUE_REFRESH: "
        f"status={payload['status']} "
        f"roi_status={payload['roi_status']} "
        f"input_status={payload['input_status']} "
        f"records={summary.get('record_count')} "
        f"quantified={summary.get('quantified_records')} "
        f"benefit={totals.get('benefit_total')} "
        f"cost={totals.get('cost_total')} "
        f"as_of={payload['as_of']}"
    )
    if payload.get("next_action"):
        print(f"EVA_OS_TOKEN_ROI_NEXT_ACTION: {payload['next_action']}")
    if payload.get("outputs"):
        print(f"EVA_OS_TOKEN_ROI_REVIEWED_VALUE_OUTPUTS: {payload['outputs']}")


if __name__ == "__main__":
    main()
