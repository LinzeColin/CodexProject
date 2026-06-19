from __future__ import annotations

import argparse
import json
from pathlib import Path

from pfi_os.integrations.research_bus import (
    bus_pfi_os_results_frame,
    bus_validation_task_frame,
    export_research_bus_snapshot,
    research_bus_status_frame,
    sync_all_research_bus,
    sync_holdings_to_bus,
    sync_industry_reports_to_bus,
    sync_pfi_os_results_to_bus,
)
from pfi_os.integrations.consumer_behavior import consumer_behavior_state_frame, sync_consumer_behavior_state
from pfi_os.integrations.research_bus_audit import AUDIT_OUTPUT_PATH, run_research_bus_interop_audit


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync PFIOS, AI-Research-System, and holdings into the unified research data bus.")
    parser.add_argument("--db", default="", help="Optional ResearchBus SQLite path.")
    parser.add_argument("--industry-report-root", default="", help="Optional industry report directory.")
    parser.add_argument("--report-root", default="", help="Optional PFIOS report directory.")
    parser.add_argument("--ai-research-root", default="", help="Optional AI-Research-System root for PFIOS result outbox.")
    parser.add_argument(
        "--mode",
        choices=["all", "industry", "pfi_os-results", "holdings", "consumer", "status", "snapshot", "audit"],
        default="all",
    )
    parser.add_argument("--no-push-validation-queue", action="store_true", help="Do not push generated validation tasks into PFIOS JSON queue.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args()

    db_path = Path(args.db).expanduser() if args.db else None
    industry_root = Path(args.industry_report_root).expanduser() if args.industry_report_root else None
    report_root = Path(args.report_root).expanduser() if args.report_root else None
    ai_root = Path(args.ai_research_root).expanduser() if args.ai_research_root else None

    if args.mode == "all":
        result = sync_all_research_bus(
            report_root=report_root,
            industry_report_root=industry_root,
            db_path=db_path,
            push_validation_queue=not args.no_push_validation_queue,
            ai_research_root=ai_root,
        ).to_dict()
    elif args.mode == "industry":
        result = sync_industry_reports_to_bus(
            industry_root,
            db_path,
            push_validation_queue=not args.no_push_validation_queue,
        ).to_dict()
    elif args.mode == "pfi_os-results":
        result = sync_pfi_os_results_to_bus(report_root, db_path, ai_research_root=ai_root).to_dict()
    elif args.mode == "holdings":
        result = sync_holdings_to_bus(db_path=db_path).to_dict()
    elif args.mode == "consumer":
        result = sync_consumer_behavior_state(bus_db_path=db_path).to_dict()
    elif args.mode == "snapshot":
        result = {"snapshot_path": str(export_research_bus_snapshot(db_path))}
    elif args.mode == "audit":
        result = run_research_bus_interop_audit(db_path=db_path, ai_research_root=ai_root, output_path=AUDIT_OUTPUT_PATH)
    else:
        status = research_bus_status_frame(db_path)
        tasks = bus_validation_task_frame(db_path)
        results = bus_pfi_os_results_frame(db_path)
        consumer = consumer_behavior_state_frame(db_path)
        result = {
            "systems": status.to_dict("records"),
            "validation_task_count": int(len(tasks)),
            "pfi_os_result_count": int(len(results)),
            "consumer_behavior_state_count": int(len(consumer)),
        }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    for key, value in result.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
