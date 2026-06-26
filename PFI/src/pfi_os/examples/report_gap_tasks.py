from __future__ import annotations

import argparse
from pathlib import Path

from pfi_os.config import PROJECT_ROOT, REPORT_ROOT_DIR
from pfi_os.research import append_report_gap_validation_tasks, build_report_gap_validation_tasks


def main() -> None:
    parser = argparse.ArgumentParser(description="Create validation-queue tasks from Report Decision Support evidence gaps.")
    parser.add_argument("--as-of", default=None, help="Audit date in YYYY-MM-DD format. Defaults to today.")
    parser.add_argument("--project-root", default=str(PROJECT_ROOT), help="PFI_OS / PFIOS project root.")
    parser.add_argument("--report-root", default=str(REPORT_ROOT_DIR), help="Formal report root.")
    parser.add_argument("--queue-path", default=None, help="ValidationTasks.json path. Defaults to data/validationQueue/ValidationTasks.json.")
    parser.add_argument("--output-dir", default=None, help="Optional output directory. Defaults to data/reportDecision when appending.")
    parser.add_argument("--max-records", type=int, default=500, help="Maximum report decision records to inspect.")
    parser.add_argument("--dry-run", action="store_true", help="Preview tasks and write optional outputs without appending to the queue.")
    parser.add_argument("--json-only", action="store_true", help="Build and print candidate task counts without queue append or file writes.")
    args = parser.parse_args()

    common = {
        "as_of": args.as_of,
        "project_root": Path(args.project_root),
        "report_root": Path(args.report_root),
        "max_records": args.max_records,
    }
    if args.json_only:
        payload = build_report_gap_validation_tasks(**common)
    else:
        payload = append_report_gap_validation_tasks(
            queue_path=Path(args.queue_path) if args.queue_path else None,
            output_dir=Path(args.output_dir) if args.output_dir else None,
            dry_run=args.dry_run,
            **common,
        )
    print(
        "REPORT_GAP_TASKS: "
        f"source_records={payload.get('source_record_count', 0)} "
        f"candidate={payload.get('task_count', 0)} "
        f"pending={payload.get('pending_task_count', payload.get('task_count', 0))} "
        f"appended={payload.get('appended_task_count', 0)} "
        f"skipped={payload.get('skipped_existing_count', 0)} "
        f"as_of={payload.get('as_of', '')}"
    )
    if payload.get("outputs"):
        print(f"REPORT_GAP_TASK_OUTPUTS: {payload['outputs']}")


if __name__ == "__main__":
    main()
