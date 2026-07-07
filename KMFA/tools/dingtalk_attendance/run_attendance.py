#!/usr/bin/env python3
"""Run KMFA S19 DingTalk attendance collection and reporting."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.dingtalk_attendance import (
    AUTOMATION_NAME,
    ONEDRIVE_ROOT,
    STAGE_ID,
    TIMEZONE,
    ZHANG_LINZE_USER_ID,
)
from KMFA.tools.dingtalk_attendance.cleanup_runtime import cleanup_runtime
from KMFA.tools.dingtalk_attendance.dws_attendance import DwsAttendanceError, collect_org_attendance, write_private_outputs
from KMFA.tools.dingtalk_attendance.healthcheck import build_config_status
from KMFA.tools.dingtalk_attendance.onedrive_archive import archive_paths_for_run


RUN_TYPES = ("morning", "evening")
SCHEDULE = {"morning": "08:35", "evening": "18:15"}


def build_run_plan(run_type: str, timezone: str = TIMEZONE, run_id: str | None = None) -> dict[str, Any]:
    if run_type not in RUN_TYPES:
        raise ValueError(f"run_type must be one of {RUN_TYPES}")
    now = datetime.now(ZoneInfo(timezone))
    effective_run_id = run_id or f"s19_{run_type}_{now.strftime('%Y%m%d_%H%M%S')}"
    return {
        "project_id": "KMFA",
        "stage_id": STAGE_ID,
        "automation_name": AUTOMATION_NAME,
        "run_id": effective_run_id,
        "run_type": run_type,
        "timezone": timezone,
        "schedule": dict(SCHEDULE),
        "live_only": True,
        "uses_sample_data": False,
        "onedrive_root": ONEDRIVE_ROOT,
        "onedrive_month_folder_pattern": "YYYYMM",
        "archive_paths": archive_paths_for_run(effective_run_id, now),
        "known_recipients": {
            "zhang_linze": {
                "name": "张霖泽",
                "dingtalk_user_id": ZHANG_LINZE_USER_ID,
            },
            "boss": {
                "name": "老板",
                "dingtalk_user_id": "CONFIG_REQUIRED",
            },
        },
        "public_repo_safety": {
            "employee_plaintext_committed": False,
            "sqlite_committed": False,
            "credential_committed": False,
            "raw_api_response_committed": False,
            "report_body_committed": False,
        },
    }


def run_attendance(run_type: str, timezone: str) -> dict[str, Any]:
    plan = build_run_plan(run_type=run_type, timezone=timezone)
    openapi_config_status = build_config_status()
    cleanup_status: dict[str, Any] = {"status": "NOT_RUN"}
    work_date = datetime.now(ZoneInfo(timezone)).strftime("%Y-%m-%d")
    summary_datetime = f"{work_date} {SCHEDULE[run_type]}:00"
    try:
        collection = collect_org_attendance(
            work_date=work_date,
            summary_datetime=summary_datetime,
        )
    except (DwsAttendanceError, FileNotFoundError, TimeoutError) as exc:
        cleanup_status.update(cleanup_runtime())
        return {
            "status": "DWS_UNAVAILABLE",
            "run_plan": plan,
            "config_status": {
                "status": "DWS_UNAVAILABLE",
                "backend": "dws",
                "openapi_env_status": openapi_config_status,
            },
            "dws_error": str(exc),
            "collection_status": "SKIPPED_DWS_UNAVAILABLE",
            "anomaly_count": None,
            "management_report_status": "NOT_GENERATED",
            "hr_report_status": "NOT_GENERATED",
            "notification_status": "NOT_SENT_DWS_UNAVAILABLE",
            "onedrive_archive_status": "NOT_WRITTEN_DWS_UNAVAILABLE",
            "cleanup_status": cleanup_status,
        }

    cleanup_status.update(cleanup_runtime())
    output_status = write_private_outputs(
        plan=plan,
        collection=collection,
        cleanup_status=cleanup_status,
    )
    run_status = "COMPLETED" if collection["stats"]["command_failure_count"] == 0 else "PARTIAL"
    return {
        "status": run_status,
        "run_plan": plan,
        "config_status": {
            "status": "OK",
            "backend": "dws",
            "uses_sample_data": False,
            "openapi_env_status": openapi_config_status["status"],
            "openapi_missing": openapi_config_status["missing"],
            "notifier_configured": openapi_config_status["notifier_configured"],
            "notification_missing": openapi_config_status["notification_missing"],
        },
        "backend": "dws",
        "dws_live": True,
        "uses_mock_data": False,
        "work_date": work_date,
        "summary_datetime": summary_datetime,
        "collection_status": "DWS_LIVE_COLLECTION_WRITTEN",
        "collection_stats": collection["stats"],
        "anomaly_count": collection["stats"]["unexpected_empty_record_count"],
        "management_report_status": "GENERATED",
        "hr_report_status": "GENERATED",
        "notification_status": "NOT_SENT_DWS_VALIDATION_MODE",
        "onedrive_archive_status": output_status,
        "cleanup_status": cleanup_status,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run KMFA S19 DingTalk attendance automation.")
    parser.add_argument("--run-type", required=True, choices=RUN_TYPES)
    parser.add_argument("--timezone", default=TIMEZONE)
    args = parser.parse_args(argv)

    result = run_attendance(run_type=args.run_type, timezone=args.timezone)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
