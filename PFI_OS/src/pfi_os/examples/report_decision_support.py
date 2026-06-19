from __future__ import annotations

import argparse
from pathlib import Path

from pfi_os.config import PROJECT_ROOT, REPORT_ROOT_DIR
from pfi_os.reports import build_report_decision_support_index, write_report_decision_support_index


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the PFIOS report decision support index.")
    parser.add_argument("--as-of", default=None, help="Audit date in YYYY-MM-DD format. Defaults to today.")
    parser.add_argument("--project-root", default=str(PROJECT_ROOT), help="PFI_OS / PFIOS project root.")
    parser.add_argument("--report-root", default=str(REPORT_ROOT_DIR), help="Formal report root.")
    parser.add_argument("--output-dir", default=None, help="Optional output directory. Defaults to data/reportDecision.")
    parser.add_argument("--max-records", type=int, default=500, help="Maximum RunMetadata records to index.")
    parser.add_argument("--json-only", action="store_true", help="Build and print status without writing files.")
    args = parser.parse_args()

    common = {
        "as_of": args.as_of,
        "project_root": Path(args.project_root),
        "report_root": Path(args.report_root),
        "max_records": args.max_records,
    }
    if args.json_only:
        payload = build_report_decision_support_index(**common)
    else:
        payload = write_report_decision_support_index(output_dir=Path(args.output_dir) if args.output_dir else None, **common)
    summary = payload.get("summary", {})
    print(
        "REPORT_DECISION_SUPPORT_INDEX: "
        f"records={payload['record_count']} "
        f"continue={summary.get('continue_research_count', 0)} "
        f"needs_more={summary.get('needs_more_evidence_count', 0)} "
        f"watch={summary.get('watch_only_count', 0)} "
        f"do_not_use={summary.get('do_not_use_count', 0)} "
        f"as_of={payload['as_of']}"
    )
    if payload.get("outputs"):
        print(f"REPORT_DECISION_SUPPORT_OUTPUTS: {payload['outputs']}")


if __name__ == "__main__":
    main()
