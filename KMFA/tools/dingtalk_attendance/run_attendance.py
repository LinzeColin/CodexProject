#!/usr/bin/env python3
"""Run KMFA S19 DingTalk attendance collection and reporting."""

from __future__ import annotations

import argparse
import gzip
import json
import os
import sys
from collections.abc import Callable, Mapping
from datetime import datetime, timedelta
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
from KMFA.tools.dingtalk_attendance.dws_auth_guard import DWS_COMMAND_ALLOW_ENV, dws_command_safety_status
from KMFA.tools.dingtalk_attendance.dws_attendance import DwsAttendanceError, collect_org_attendance, write_private_outputs
from KMFA.tools.dingtalk_attendance.healthcheck import build_config_status
from KMFA.tools.dingtalk_attendance.notifier_dingtalk import send_group_robot_markdown
from KMFA.tools.dingtalk_attendance.notification_targets import dispatch_reports_to_targets
from KMFA.tools.dingtalk_attendance.notification_template import (
    REST_REQUIRED_EXCLUDED_NAMES,
    REST_REQUIRED_THRESHOLD_DAYS,
    build_notification_message,
    build_personal_notification_message,
    coerce_message_lines,
    notification_context_from_output_status,
    work_date_from_run_id,
)
from KMFA.tools.dingtalk_attendance.onedrive_archive import archive_paths_for_run
from KMFA.tools.dingtalk_attendance.secrets_loader import merged_runtime_env


RUN_TYPES = ("morning", "evening")
SCHEDULE = {"morning": "10:35", "evening": "20:05"}


def build_run_plan(
    run_type: str,
    timezone: str = TIMEZONE,
    run_id: str | None = None,
    run_datetime: datetime | None = None,
) -> dict[str, Any]:
    if run_type not in RUN_TYPES:
        raise ValueError(f"run_type must be one of {RUN_TYPES}")
    now = run_datetime or datetime.now(ZoneInfo(timezone))
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
            "notification_template_text": "",
            "notification_delivery_table": "| 发送对象 | 是否成功 |\n|---|---|\n| 钉钉群机器人 | 否 |",
        }
        receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
        return receipt

    notification_context = notification_context_from_output_status(output_status)
    markdown_text = build_notification_message(**notification_context, markdown=True)
    send_result = sender(title="开明考勤提醒", markdown_text=markdown_text, env=values)
    messages.append(
        {
            "report": "combined_attendance_notification",
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
        "notification_template_text": markdown_text,
        "notification_delivery_table": (
            "| 发送对象 | 是否成功 |\n|---|---|\n"
            f"| 钉钉群机器人 | {'是' if notification_status == 'SENT' else '否'} |"
        ),
    }
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    return receipt


def build_stats_with_rest_required_people(
    stats: Mapping[str, Any],
    *,
    month_dir: Path,
    threshold_days: int = REST_REQUIRED_THRESHOLD_DAYS,
    work_date: str | None = None,
) -> dict[str, Any]:
    enriched = dict(stats)
    enriched.update(
        build_monthly_notification_rollups(
            _monthly_attendance_records(month_dir),
            current_stats=stats,
            work_date=work_date,
            threshold_days=threshold_days,
        )
    )
    return enriched


def build_monthly_notification_rollups(
    records: list[Mapping[str, Any]],
    *,
    current_stats: Mapping[str, Any],
    work_date: str | None,
    threshold_days: int = REST_REQUIRED_THRESHOLD_DAYS,
) -> dict[str, Any]:
    current_work_date = work_date or _max_work_date(records)
    current_month = current_work_date[:7] if current_work_date else ""
    names_by_user: dict[str, str] = {}
    users_by_name: dict[str, str] = {}
    effective_dates_by_user: dict[str, set[str]] = {}
    anomaly_dates_by_user: dict[str, set[str]] = {}
    pending_counts_by_user: dict[str, int] = {}
    pending_latest_by_user: dict[str, str] = {}
    current_pending_users: set[str] = set()

    for record in records:
        member = record.get("member", {})
        if not isinstance(member, Mapping):
            continue
        name = str(member.get("name") or "").strip()
        user_id = str(member.get("userId") or name).strip()
        record_work_date = str(record.get("work_date") or "").strip()
        if not name or not user_id or not _date_in_current_month(record_work_date, current_month):
            continue
        if current_work_date and record_work_date > current_work_date:
            continue
        names_by_user[user_id] = name
        users_by_name[name] = user_id
        if _attendance_record_success(record) and _record_list_has_morning_and_evening(_record_list_from_attendance_record(record)):
            effective_dates_by_user.setdefault(user_id, set()).add(record_work_date)
        summary_issues = _summary_today_issues_from_attendance_record(record)
        if _attendance_record_has_anomaly(record) or summary_issues:
            anomaly_dates_by_user.setdefault(user_id, set()).add(record_work_date)
        if summary_issues:
            pending_counts_by_user[user_id] = pending_counts_by_user.get(user_id, 0) + len(summary_issues)
            pending_latest_by_user[user_id] = max(pending_latest_by_user.get(user_id, ""), record_work_date)
            if record_work_date == current_work_date:
                current_pending_users.add(user_id)

    current_anomaly_names = _coerce_name_list(
        current_stats.get("attendance_anomaly_names")
        or [
            *coerce_message_lines(current_stats.get("unexpected_empty_record_names")),
            *coerce_message_lines(current_stats.get("incomplete_record_names")),
        ]
    )
    monthly_attendance_anomalies: list[dict[str, Any]] = []
    for name in current_anomaly_names:
        user_id = users_by_name.get(name, name)
        dates = anomaly_dates_by_user.get(user_id, set())
        monthly_attendance_anomalies.append(
            {
                "name": name,
                "monthly_count": max(len(dates), 1),
                "latest_date": max(dates) if dates else (current_work_date or ""),
            }
        )

    monthly_consecutive_anomalies: list[dict[str, Any]] = []
    for user_id, dates in anomaly_dates_by_user.items():
        if not current_work_date or current_work_date not in dates:
            continue
        streak = _current_consecutive_day_count(dates, current_work_date)
        if streak >= 2:
            monthly_consecutive_anomalies.append(
                {
                    "name": names_by_user[user_id],
                    "monthly_count": len(dates),
                    "consecutive_days": streak,
                    "latest_date": current_work_date,
                }
            )

    monthly_pending_actions = [
        {
            "name": names_by_user[user_id],
            "monthly_count": pending_counts_by_user[user_id],
            "latest_date": pending_latest_by_user.get(user_id, ""),
        }
        for user_id in current_pending_users
        if user_id in names_by_user
    ]
    rest_required_people = [
        {
            "name": names_by_user[user_id],
            "effective_attendance_days": len(work_dates),
            "latest_date": max(work_dates),
        }
        for user_id, work_dates in effective_dates_by_user.items()
        if names_by_user[user_id] not in REST_REQUIRED_EXCLUDED_NAMES and len(work_dates) >= threshold_days
    ]
    return {
        "monthly_attendance_anomalies": _sort_monthly_people(monthly_attendance_anomalies, metric_key="monthly_count"),
        "monthly_consecutive_anomalies": _sort_monthly_people(monthly_consecutive_anomalies, metric_key="monthly_count"),
        "monthly_pending_actions": _sort_monthly_people(monthly_pending_actions, metric_key="monthly_count"),
        "rest_required_people": _sort_monthly_people(
            rest_required_people,
            metric_key="effective_attendance_days",
        ),
    }


def build_monthly_rest_required_people(
    records: list[Mapping[str, Any]],
    *,
    threshold_days: int = REST_REQUIRED_THRESHOLD_DAYS,
) -> list[dict[str, Any]]:
    return build_monthly_notification_rollups(
        records,
        current_stats={},
        work_date=_max_work_date(records),
        threshold_days=threshold_days,
    )["rest_required_people"]


def _coerce_name_list(value: Any) -> list[str]:
    return coerce_message_lines(value)


def _date_in_current_month(work_date: str, current_month: str) -> bool:
    return bool(work_date) and (not current_month or work_date.startswith(current_month))


def _max_work_date(records: list[Mapping[str, Any]]) -> str | None:
    dates = sorted(str(record.get("work_date") or "") for record in records if str(record.get("work_date") or ""))
    return dates[-1] if dates else None


def _attendance_record_success(record: Mapping[str, Any]) -> bool:
    derived = record.get("derived", {})
    if isinstance(derived, Mapping) and "record_success" in derived:
        return bool(derived["record_success"])
    record_payload = record.get("record", {})
    if not isinstance(record_payload, Mapping):
        return True
    final = record_payload.get("final", record_payload)
    if not isinstance(final, Mapping):
        return True
    payload = final.get("payload", {})
    return int(final.get("returncode", 0)) == 0 and (not isinstance(payload, Mapping) or payload.get("success", True) is not False)


def _attendance_record_has_anomaly(record: Mapping[str, Any]) -> bool:
    derived = record.get("derived", {})
    if not isinstance(derived, Mapping):
        return False
    return bool(derived.get("record_anomaly") or derived.get("summary_today_anomaly"))


def _summary_today_issues_from_attendance_record(record: Mapping[str, Any]) -> list[str]:
    derived = record.get("derived", {})
    if isinstance(derived, Mapping):
        issues = coerce_message_lines(derived.get("summary_today_issues"))
        if issues:
            return issues
        if derived.get("summary_today_anomaly"):
            return ["summary_today_anomaly"]
    return []


def _current_consecutive_day_count(dates: set[str], current_work_date: str) -> int:
    try:
        cursor = datetime.fromisoformat(current_work_date).date()
    except ValueError:
        return 0
    count = 0
    while cursor.isoformat() in dates:
        count += 1
        cursor -= timedelta(days=1)
    return count


def _sort_monthly_people(people: list[dict[str, Any]], *, metric_key: str) -> list[dict[str, Any]]:
    return sorted(
        people,
        key=lambda item: (
            -_coerce_nonnegative_int(item.get(metric_key)),
            -_date_ordinal(str(item.get("latest_date") or "")),
            str(item.get("name") or ""),
        ),
    )


def _coerce_nonnegative_int(value: Any) -> int:
    try:
        result = int(value)
    except (TypeError, ValueError):
        return 0
    return max(result, 0)


def _date_ordinal(value: str) -> int:
    try:
        return datetime.fromisoformat(value[:10]).date().toordinal()
    except ValueError:
        return 0


def _monthly_attendance_records(month_dir: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for raw_path in sorted(month_dir.glob("s19_*.raw.jsonl.gz")):
        work_date = work_date_from_run_id(raw_path.name)
        try:
            with gzip.open(raw_path, "rt", encoding="utf-8") as handle:
                for line in handle:
                    if not line.strip():
                        continue
                    payload = json.loads(line)
                    if not isinstance(payload, dict):
                        continue
                    if payload.get("type") == "metadata":
                        run_plan = payload.get("run_plan", {})
                        if isinstance(run_plan, Mapping):
                            work_date = work_date_from_run_id(str(run_plan.get("run_id") or raw_path.name))
                        continue
                    if payload.get("type") != "employee_attendance":
                        continue
                    row = dict(payload)
                    row["work_date"] = str(row.get("work_date") or work_date or "")
                    records.append(row)
        except (OSError, EOFError, json.JSONDecodeError):
            continue
    return records


def _record_list_from_attendance_record(record: Mapping[str, Any]) -> list[Any]:
    direct_record_list = record.get("record_list")
    if isinstance(direct_record_list, list):
        return direct_record_list
    record_payload = record.get("record", {})
    if not isinstance(record_payload, Mapping):
        return []
    final = record_payload.get("final", {})
    if not isinstance(final, Mapping):
        return []
    payload = final.get("payload", {})
    if not isinstance(payload, Mapping):
        return []
    result = payload.get("result", {})
    if not isinstance(result, Mapping):
        return []
    record_list = result.get("recordList", [])
    return record_list if isinstance(record_list, list) else []


def _record_list_has_morning_and_evening(record_list: list[Any]) -> bool:
    has_morning = False
    has_evening = False
    for item in record_list:
        if not isinstance(item, Mapping):
            continue
        values = " ".join(
            str(item.get(key) or "")
            for key in ("checkTypeDesc", "checkType", "timeResult", "sourceType")
        )
        has_morning = has_morning or "上班" in values or "OnDuty" in values
        has_evening = has_evening or "下班" in values or "OffDuty" in values
    return has_morning and has_evening


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


def run_attendance(
    run_type: str,
    timezone: str,
    *,
    allow_dws_commands: bool = False,
    work_date: str | None = None,
    notification_target_filter: str = "all",
    env: Mapping[str, str] | None = None,
    collector: Callable[..., dict[str, Any]] = collect_org_attendance,
    cleanup: Callable[[], dict[str, Any]] = cleanup_runtime,
) -> dict[str, Any]:
    effective_work_date = work_date or os.environ.get("KMFA_WORK_DATE_OVERRIDE") or os.environ.get("KMFA_TODAY_OVERRIDE")
    run_datetime = _scheduled_run_datetime(run_type=run_type, timezone=timezone, work_date=effective_work_date)
    effective_work_date = run_datetime.strftime("%Y-%m-%d")
    plan = build_run_plan(run_type=run_type, timezone=timezone, run_datetime=run_datetime)
    notification_config_status = build_config_status()
    cleanup_status: dict[str, Any] = {"status": "NOT_RUN"}
    summary_datetime = f"{effective_work_date} {SCHEDULE[run_type]}:00"
    dws_safety = dws_command_safety_status(env=env, allow_override=allow_dws_commands)
    if dws_safety["status"] != "READY":
        cleanup_status.update(cleanup())
        return {
            "status": "DWS_AUTH_REQUIRED",
            "run_plan": plan,
            "config_status": {
                "status": "DWS_AUTH_REQUIRED",
                "backend": "dws",
                "notification_config_status": notification_config_status,
            },
            "dws_command_safety": dws_safety,
            "collection_status": "SKIPPED_DWS_AUTH_REQUIRED",
            "anomaly_count": None,
            "management_report_status": "NOT_GENERATED",
            "hr_report_status": "NOT_GENERATED",
            "notification_status": "NOT_SENT_DWS_AUTH_REQUIRED",
            "onedrive_archive_status": "NOT_WRITTEN_DWS_AUTH_REQUIRED",
            "cleanup_status": cleanup_status,
        }
    os.environ[DWS_COMMAND_ALLOW_ENV] = "1"
    try:
        collection = collector(
            work_date=effective_work_date,
            summary_datetime=summary_datetime,
        )
    except (DwsAttendanceError, FileNotFoundError, TimeoutError) as exc:
        cleanup_status.update(cleanup())
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
    notification_stats = build_stats_with_rest_required_people(
        collection["stats"],
        month_dir=Path(str(output_status["month_dir"])),
        work_date=effective_work_date,
    )
    output_status.update(
        {
            "run_id": plan["run_id"],
            "run_type": run_type,
            "work_date": effective_work_date,
            "current_time": run_datetime.strftime("%H:%M"),
            "stats": notification_stats,
        }
    )
    try:
        dispatch_receipt = dispatch_reports_to_targets(output_status=output_status, target_filter=notification_target_filter)
    finally:
        cleanup_status.update(cleanup())
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
        "work_date": effective_work_date,
        "summary_datetime": summary_datetime,
        "collection_status": "DWS_LIVE_COLLECTION_WRITTEN",
        "collection_stats": collection["stats"],
        "anomaly_count": collection["stats"].get("attendance_anomaly_count", collection["stats"]["unexpected_empty_record_count"]),
        "management_report_status": "GENERATED",
        "hr_report_status": "GENERATED",
        "notification_status": dispatch_receipt["notification_status"],
        "notification_template_text": dispatch_receipt.get("notification_template_text", ""),
        "notification_delivery_table": dispatch_receipt.get("notification_delivery_table", ""),
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
        "work_date": work_date_from_run_id(str(manifest["run_id"])),
        "current_time": datetime.now(ZoneInfo(timezone)).strftime("%H:%M"),
        "stats": build_stats_with_rest_required_people(
            manifest.get("stats", {}),
            month_dir=manifest_path.parent,
            work_date=work_date_from_run_id(str(manifest["run_id"])),
        ),
        "management_report": manifest["management_report"],
        "hr_report": manifest["hr_report"],
        "dispatch_receipt": manifest["dispatch_receipt"],
        "cleanup_audit": manifest["cleanup_audit"],
    }
    dispatch_receipt: dict[str, Any] = {"notification_status": "FAILED"}
    try:
        dispatch_receipt = dispatch_reports_to_targets(output_status=output_status)
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
        "notification_template_text": dispatch_receipt.get("notification_template_text", ""),
        "notification_delivery_table": dispatch_receipt.get("notification_delivery_table", ""),
        "dispatch_receipt": dispatch_receipt,
        "cleanup_status": cleanup_status,
    }


def _scheduled_run_datetime(*, run_type: str, timezone: str, work_date: str | None) -> datetime:
    if work_date:
        try:
            return datetime.fromisoformat(f"{work_date[:10]}T{SCHEDULE[run_type]}:00").replace(tzinfo=ZoneInfo(timezone))
        except ValueError as exc:
            raise ValueError("work_date must be YYYY-MM-DD") from exc
    return datetime.now(ZoneInfo(timezone))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run KMFA S19 DingTalk attendance automation.")
    parser.add_argument("--run-type", required=True, choices=RUN_TYPES)
    parser.add_argument("--timezone", default=TIMEZONE)
    parser.add_argument("--work-date", help="YYYY-MM-DD business date override for controlled reruns/tests.")
    parser.add_argument("--notification-targets", default="all", choices=("all", "personal", "group"))
    parser.add_argument("--send-latest-report-only", action="store_true", help="Send the latest private reports without DWS collection.")
    parser.add_argument(
        "--allow-dws-commands",
        action="store_true",
        help=f"Explicitly allow DWS subprocess calls for this run. Without this or {DWS_COMMAND_ALLOW_ENV}=1, live collection fails closed.",
    )
    args = parser.parse_args(argv)
    if args.allow_dws_commands:
        os.environ[DWS_COMMAND_ALLOW_ENV] = "1"

    if args.send_latest_report_only:
        result = send_latest_report_only(run_type=args.run_type, timezone=args.timezone)
    else:
        result = run_attendance(
            run_type=args.run_type,
            timezone=args.timezone,
            allow_dws_commands=args.allow_dws_commands,
            work_date=args.work_date,
            notification_target_filter=args.notification_targets,
        )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
