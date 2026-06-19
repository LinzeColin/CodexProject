from __future__ import annotations

import argparse
import json
from pathlib import Path

from pfi_os.config import PROJECT_ROOT, REPORT_ROOT_DIR
from pfi_os.system.report_validation_hub import (
    build_report_validation_hub,
    build_report_validation_mode_guide,
    report_validation_hub_summary,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the user-friendly PFI_OS report validation hub.")
    parser.add_argument("--as-of", default=None, help="Audit date in YYYY-MM-DD format. Defaults to today.")
    parser.add_argument("--project-root", default=str(PROJECT_ROOT), help="PFI_OS / PFIOS project root.")
    parser.add_argument("--report-root", default=str(REPORT_ROOT_DIR), help="Formal report root.")
    parser.add_argument("--queue-path", default=None, help="ValidationTasks.json path. Defaults to data/validationQueue/ValidationTasks.json.")
    parser.add_argument("--max-records", type=int, default=500, help="Maximum report records to inspect.")
    parser.add_argument("--max-tasks", type=int, default=120, help="Maximum validation tasks to inspect.")
    parser.add_argument("--include-completed", action="store_true", help="Include completed validation tasks in priority counts.")
    parser.add_argument(
        "--mode",
        default="daily",
        choices=["daily", "decision", "gaps", "priority"],
        help="Read-only hub mode. daily is the safe default.",
    )
    parser.add_argument("--list-modes", action="store_true", help="Print available modes and advanced commands.")
    parser.add_argument("--json", action="store_true", help="Print PFIOSReportValidationHubV1 as JSON.")
    parser.add_argument("--summary-json", action="store_true", help="Print compact summary JSON.")
    args = parser.parse_args()

    if args.list_modes:
        print(json.dumps(build_report_validation_mode_guide(), ensure_ascii=False, indent=2, default=str))
        return

    payload = build_report_validation_hub(
        mode=args.mode,
        as_of=args.as_of,
        project_root=Path(args.project_root),
        report_root=Path(args.report_root),
        queue_path=Path(args.queue_path) if args.queue_path else None,
        max_records=args.max_records,
        max_tasks=args.max_tasks,
        include_completed=args.include_completed,
    )
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
        return
    if args.summary_json:
        print(json.dumps(report_validation_hub_summary(payload), ensure_ascii=False, indent=2, default=str))
        return

    summary = payload["summary"]
    print(
        "PFI_OS_REPORT_VALIDATION: "
        f"mode={payload['mode']} "
        f"status={payload['status']} "
        f"records={summary.get('report_record_count', 0)} "
        f"needs_more={summary.get('needs_more_evidence_count', 0)} "
        f"gap_tasks={summary.get('gap_candidate_task_count', 0)} "
        f"prioritized={summary.get('prioritized_task_count', 0)}"
    )
    print(f"PFI_OS_REPORT_VALIDATION_NEXT_ACTION: {payload['next_action']}")


if __name__ == "__main__":
    main()
