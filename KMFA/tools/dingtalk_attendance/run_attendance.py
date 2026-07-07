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
    config_status = build_config_status()
    cleanup_status: dict[str, Any] = {"status": "NOT_RUN"}
    try:
        if config_status["status"] != "OK":
            return {
                "status": "CONFIG_MISSING",
                "run_plan": plan,
                "config_status": config_status,
                "collection_status": "SKIPPED_CONFIG_MISSING",
                "anomaly_count": None,
                "management_report_status": "NOT_GENERATED",
                "hr_report_status": "NOT_GENERATED",
                "notification_status": "NOT_SENT_CONFIG_MISSING",
                "onedrive_archive_status": "NOT_WRITTEN_CONFIG_MISSING",
                "cleanup_status": cleanup_status,
            }
        return {
            "status": "READY_FOR_LIVE_RUN",
            "run_plan": plan,
            "config_status": config_status,
            "collection_status": "LIVE_CONNECTOR_READY",
            "anomaly_count": None,
            "management_report_status": "PENDING_LIVE_DATA",
            "hr_report_status": "PENDING_LIVE_DATA",
            "notification_status": "PENDING_LIVE_DATA",
            "onedrive_archive_status": "PENDING_LIVE_DATA",
            "cleanup_status": cleanup_status,
        }
    finally:
        cleanup_status.update(cleanup_runtime())


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
