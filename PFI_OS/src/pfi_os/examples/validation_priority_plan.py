from __future__ import annotations

import argparse
from pathlib import Path

from pfi_os.config import PROJECT_ROOT
from pfi_os.research import build_validation_priority_plan, write_validation_priority_plan


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a research-only priority plan for PFIOS validation tasks.")
    parser.add_argument("--as-of", default=None, help="Plan date in YYYY-MM-DD format. Defaults to today.")
    parser.add_argument("--project-root", default=str(PROJECT_ROOT), help="PFI_OS / PFIOS project root.")
    parser.add_argument("--queue-path", default=None, help="ValidationTasks.json path. Defaults to data/validationQueue/ValidationTasks.json.")
    parser.add_argument("--output-dir", default=None, help="Output directory. Defaults to data/validationQueue.")
    parser.add_argument("--max-tasks", type=int, default=120, help="Maximum prioritized tasks to write into the plan.")
    parser.add_argument("--include-completed", action="store_true", help="Include completed tasks in the planning payload.")
    parser.add_argument("--json-only", action="store_true", help="Build the plan and print counts without writing files.")
    args = parser.parse_args()

    common = {
        "as_of": args.as_of,
        "project_root": Path(args.project_root),
        "max_tasks": args.max_tasks,
        "include_completed": args.include_completed,
    }
    if args.queue_path:
        common["queue_path"] = Path(args.queue_path)
    if args.json_only:
        payload = build_validation_priority_plan(**common)
    else:
        payload = write_validation_priority_plan(
            output_dir=Path(args.output_dir) if args.output_dir else None,
            **common,
        )
    print(
        "VALIDATION_PRIORITY_PLAN: "
        f"queue_records={payload.get('queue_record_count', 0)} "
        f"candidate={payload.get('candidate_record_count', 0)} "
        f"prioritized={payload.get('prioritized_task_count', 0)} "
        f"as_of={payload.get('as_of', '')}"
    )
    bucket_counts = {row.get("action_bucket"): row.get("count") for row in payload.get("bucket_counts", [])}
    print(f"bucket_counts: {bucket_counts}")
    if payload.get("outputs"):
        print(f"VALIDATION_PRIORITY_OUTPUTS: {payload['outputs']}")


if __name__ == "__main__":
    main()
