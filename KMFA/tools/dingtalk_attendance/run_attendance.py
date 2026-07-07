#!/usr/bin/env python3
"""Run KMFA S19 DingTalk attendance collection and reporting."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable, Mapping
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

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
from KMFA.tools.dingtalk_attendance.notifier_dingtalk import send_group_robot_markdown
from KMFA.tools.dingtalk_attendance.onedrive_archive import archive_paths_for_run
from KMFA.tools.dingtalk_attendance.secrets_loader import merged_runtime_env


RUN_TYPES = ("morning", "evening")
SCHEDULE = {"morning": "08:35", "evening": "18:15"}
REPORT_MESSAGES = (
    ("management_report", "开明考勤管理报告"),
    ("hr_report", "开明考勤 HR 报告"),
)


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


def dispatch_reports_to_robot(
    *,
    output_status: Mapping[str, Any],
    env: Mapping[str, str] | None = None,
    sender: Callable[..., dict[str, Any]] = send_group_robot_markdown,
) -> dict[str, Any]:
    values = dict(env) if env is not None else merged_runtime_env()
    receipt_path = Path(str(output_status["dispatch_receipt"]))
    messages: list[dict[str, Any]] = []

    if not values.get("DINGTALK_ROBOT_URL") or not values.get("DINGTALK_ROBOT_SIGNING_KEY"):
        receipt = {
            "notification_status": "NOTIFIER_CONFIG_MISSING",
            "channel": "dingtalk_group_robot",
            "messages": messages,
            "management_report": str(output_status.get("management_report", "")),
            "hr_report": str(output_status.get("hr_report", "")),
        }
        receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
        return receipt

    for report_key, title in REPORT_MESSAGES:
        report_path = Path(str(output_status[report_key]))
        try:
            markdown_text = report_path.read_text(encoding="utf-8")
            send_result = sender(title=title, markdown_text=markdown_text, env=values)
        except OSError as exc:
            send_result = {
                "status": "FAILED",
                "channel": "dingtalk_group_robot",
                "error_type": exc.__class__.__name__,
            }
        messages.append(
            {
                "report": report_key,
                "report_path": str(report_path),
                "status": send_result.get("status", "FAILED"),
                "channel": send_result.get("channel", "dingtalk_group_robot"),
                "http_status": send_result.get("http_status"),
                "errcode": send_result.get("errcode"),
                "error_type": send_result.get("error_type"),
            }
        )

    notification_status = _summarize_notification_status([str(message["status"]) for message in messages])
    receipt = {
        "notification_status": notification_status,
        "channel": "dingtalk_group_robot",
        "messages": messages,
        "management_report": str(output_status.get("management_report", "")),
        "hr_report": str(output_status.get("hr_report", "")),
    }
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    return receipt


def _work_date_from_run_id(run_id: str) -> str | None:
    parts = run_id.split("_")
    if len(parts) >= 3 and len(parts[2]) == 8 and parts[2].isdigit():
        return f"{parts[2][:4]}-{parts[2][4:6]}-{parts[2][6:8]}"
    return None


def _summarize_notification_status(statuses: list[str]) -> str:
    if statuses and all(status == "SENT" for status in statuses):
        return "SENT"
    if statuses and any(status == "DINGTALK_ROBOT_ERROR" for status in statuses):
        return "DINGTALK_ROBOT_ERROR"
    if statuses and all(status == "NOTIFIER_CONFIG_MISSING" for status in statuses):
        return "NOTIFIER_CONFIG_MISSING"
    return "FAILED"


def _write_cleanup_audit(output_status: Mapping[str, Any], cleanup_status: Mapping[str, Any]) -> None:
    cleanup_path = output_status.get("cleanup_audit")
    if cleanup_path:
        Path(str(cleanup_path)).write_text(json.dumps(cleanup_status, ensure_ascii=False, indent=2), encoding="utf-8")


def run_attendance(run_type: str, timezone: str) -> dict[str, Any]:
    plan = build_run_plan(run_type=run_type, timezone=timezone)
    notification_config_status = build_config_status()
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
                "notification_config_status": notification_config_status,
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

    output_status: dict[str, Any] = {}
    dispatch_receipt: dict[str, Any] = {"notification_status": "FAILED"}
    output_status = write_private_outputs(
        plan=plan,
        collection=collection,
        cleanup_status={"status": "PENDING_AFTER_NOTIFICATION"},
    )
    output_status.update(
        {
            "run_id": plan["run_id"],
            "run_type": run_type,
            "work_date": work_date,
            "current_time": datetime.now(ZoneInfo(timezone)).strftime("%H:%M"),
            "stats": collection["stats"],
        }
    )
    try:
        dispatch_receipt = dispatch_reports_to_robot(output_status=output_status)
    finally:
        cleanup_status.update(cleanup_runtime())
        _write_cleanup_audit(output_status, cleanup_status)

    run_status = "COMPLETED" if collection["stats"]["command_failure_count"] == 0 else "PARTIAL"
    return {
        "status": run_status,
        "run_plan": plan,
        "config_status": {
            "status": "OK",
            "backend": "dws",
            "uses_sample_data": False,
            "notification_config_status": notification_config_status["status"],
            "notifier_configured": notification_config_status["notifier_configured"],
            "notification_missing": notification_config_status["notification_missing"],
            "notification_ready_channels": notification_config_status["notification_ready_channels"],
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
        "notification_status": dispatch_receipt["notification_status"],
        "dispatch_receipt": dispatch_receipt,
        "onedrive_archive_status": output_status,
        "cleanup_status": cleanup_status,
    }


def find_latest_report_manifest(*, run_type: str, onedrive_root: str = ONEDRIVE_ROOT) -> Path | None:
    root = Path(onedrive_root)
    pattern = f"20[0-9][0-9][0-9][0-9]/s19_{run_type}_*.manifest.json"
    candidates = [path for path in root.glob(pattern) if path.is_file()]
    if not candidates:
        return None
    return sorted(candidates, key=lambda path: path.name, reverse=True)[0]


def send_latest_report_only(run_type: str, timezone: str) -> dict[str, Any]:
    manifest_path = find_latest_report_manifest(run_type=run_type)
    cleanup_status: dict[str, Any] = {"status": "NOT_RUN"}
    if manifest_path is None:
        cleanup_status.update(cleanup_runtime())
        return {
            "status": "NO_LATEST_REPORT",
            "mode": "send_latest_report_only",
            "run_type": run_type,
            "timezone": timezone,
            "notification_status": "FAILED",
            "cleanup_status": cleanup_status,
        }

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    output_status = {
        "run_id": manifest["run_id"],
        "run_type": run_type,
        "work_date": _work_date_from_run_id(str(manifest["run_id"])),
        "current_time": datetime.now(ZoneInfo(timezone)).strftime("%H:%M"),
        "stats": manifest.get("stats", {}),
        "management_report": manifest["management_report"],
        "hr_report": manifest["hr_report"],
        "dispatch_receipt": manifest["dispatch_receipt"],
        "cleanup_audit": manifest["cleanup_audit"],
    }
    dispatch_receipt: dict[str, Any] = {"notification_status": "FAILED"}
    try:
        dispatch_receipt = dispatch_reports_to_robot(output_status=output_status)
    finally:
        cleanup_status.update(cleanup_runtime())
        _write_cleanup_audit(output_status, cleanup_status)

    return {
        "status": dispatch_receipt["notification_status"],
        "mode": "send_latest_report_only",
        "run_type": run_type,
        "timezone": timezone,
        "manifest": str(manifest_path),
        "notification_status": dispatch_receipt["notification_status"],
        "dispatch_receipt": dispatch_receipt,
        "cleanup_status": cleanup_status,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run KMFA S19 DingTalk attendance automation.")
    parser.add_argument("--run-type", required=True, choices=RUN_TYPES)
    parser.add_argument("--timezone", default=TIMEZONE)
    parser.add_argument("--send-latest-report-only", action="store_true", help="Send the latest private reports without DWS collection.")
    args = parser.parse_args(argv)

    if args.send_latest_report_only:
        result = send_latest_report_only(run_type=args.run_type, timezone=args.timezone)
    else:
        result = run_attendance(run_type=args.run_type, timezone=args.timezone)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
