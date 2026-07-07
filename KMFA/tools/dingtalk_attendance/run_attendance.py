#!/usr/bin/env python3
"""Run KMFA S19 DingTalk attendance collection and reporting."""

from __future__ import annotations

import argparse
import gzip
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
from KMFA.tools.dingtalk_attendance.notifier_dws_personal_chat import dispatch_reports_with_resolved_channel
from KMFA.tools.dingtalk_attendance.onedrive_archive import archive_paths_for_run
from KMFA.tools.dingtalk_attendance.secrets_loader import merged_runtime_env


RUN_TYPES = ("morning", "evening")
SCHEDULE = {"morning": "08:35", "evening": "18:15"}
REST_REQUIRED_THRESHOLD_DAYS = 27


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


def build_notification_message(
    *,
    work_date: str,
    run_type: str,
    current_time: str,
    unexpected_empty_record_names: list[str],
    known_no_record_names: list[str],
    consecutive_anomaly_summary: list[str] | str | None = None,
    pending_hr_actions: list[str] | str | None = None,
    rest_required_people: list[dict[str, Any]] | None = None,
    markdown: bool = True,
) -> str:
    title = f"开明考勤提醒｜{work_date}｜{run_type}"
    lines = [f"# {title}" if markdown else title, "", f"截止 {current_time}", ""]
    abnormal_names = _dedupe_nonempty([*unexpected_empty_record_names, *known_no_record_names])
    consecutive_lines = _coerce_message_lines(consecutive_anomaly_summary)
    pending_lines = _coerce_message_lines(pending_hr_actions)
    rest_required_lines = _format_rest_required_people(rest_required_people)

    if abnormal_names:
        lines.extend([f"今日异常人员 / 无考勤人员：{_join_names(abnormal_names)}。", ""])
    if consecutive_lines:
        lines.extend(["连续异常人员：", *consecutive_lines, ""])
    if pending_lines:
        lines.extend(["待审批/待补卡/待核查：", *pending_lines, ""])
    if rest_required_lines:
        lines.extend(["需要休息的人员：", *rest_required_lines, ""])
    if not abnormal_names and not consecutive_lines and not pending_lines and not rest_required_lines:
        lines.append("今天一切良好")

    return "\n".join(lines).rstrip() + "\n"


def build_personal_notification_message(**kwargs: Any) -> str:
    kwargs.pop("markdown", None)
    return build_notification_message(**kwargs, markdown=False)


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

    notification_context = _notification_context_from_output_status(output_status)
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
    }
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    return receipt


def _notification_context_from_output_status(output_status: Mapping[str, Any]) -> dict[str, Any]:
    stats = output_status.get("stats", {})
    if not isinstance(stats, Mapping):
        stats = {}
    return {
        "work_date": str(
            output_status.get("work_date") or _work_date_from_run_id(str(output_status.get("run_id", ""))) or "UNKNOWN_DATE"
        ),
        "run_type": str(output_status.get("run_type") or _run_type_from_run_id(str(output_status.get("run_id", ""))) or "unknown"),
        "current_time": str(output_status.get("current_time") or datetime.now(ZoneInfo(TIMEZONE)).strftime("%H:%M")),
        "unexpected_empty_record_names": _coerce_message_lines(stats.get("unexpected_empty_record_names")),
        "known_no_record_names": _coerce_message_lines(stats.get("known_no_record_names")),
        "consecutive_anomaly_summary": _coerce_message_lines(output_status.get("consecutive_anomaly_summary")),
        "pending_hr_actions": _coerce_message_lines(output_status.get("pending_hr_actions")),
        "rest_required_people": _coerce_rest_required_people(stats.get("rest_required_people")),
    }


def _coerce_message_lines(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        stripped = value.strip()
        return [stripped] if stripped and stripped != "无" else []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip() and str(item).strip() != "无"]
    return []


def _dedupe_nonempty(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def build_monthly_rest_required_people(
    records: list[Mapping[str, Any]],
    *,
    threshold_days: int = REST_REQUIRED_THRESHOLD_DAYS,
) -> list[dict[str, Any]]:
    effective_dates_by_user: dict[str, set[str]] = {}
    names_by_user: dict[str, str] = {}
    for record in records:
        member = record.get("member", {})
        if not isinstance(member, Mapping):
            continue
        name = str(member.get("name") or "").strip()
        user_id = str(member.get("userId") or name).strip()
        work_date = str(record.get("work_date") or "").strip()
        if not name or not user_id or not work_date:
            continue
        if not _record_list_has_morning_and_evening(_record_list_from_attendance_record(record)):
            continue
        names_by_user[user_id] = name
        effective_dates_by_user.setdefault(user_id, set()).add(work_date)

    people = [
        {"name": names_by_user[user_id], "effective_attendance_days": len(work_dates)}
        for user_id, work_dates in effective_dates_by_user.items()
        if len(work_dates) >= threshold_days
    ]
    return sorted(people, key=lambda item: (-int(item["effective_attendance_days"]), str(item["name"])))


def build_stats_with_rest_required_people(
    stats: Mapping[str, Any],
    *,
    month_dir: Path,
    threshold_days: int = REST_REQUIRED_THRESHOLD_DAYS,
) -> dict[str, Any]:
    enriched = dict(stats)
    enriched["rest_required_people"] = build_monthly_rest_required_people(
        _monthly_attendance_records(month_dir),
        threshold_days=threshold_days,
    )
    return enriched


def _monthly_attendance_records(month_dir: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for raw_path in sorted(month_dir.glob("s19_*.raw.jsonl.gz")):
        work_date = _work_date_from_run_id(raw_path.name)
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
                            work_date = _work_date_from_run_id(str(run_plan.get("run_id") or raw_path.name))
                        continue
                    if payload.get("type") != "employee_attendance":
                        continue
                    row = dict(payload)
                    row["work_date"] = str(row.get("work_date") or work_date or "")
                    records.append(row)
        except (OSError, EOFError, json.JSONDecodeError):
            continue
    return records


def _format_rest_required_people(people: list[dict[str, Any]] | None) -> list[str]:
    lines: list[str] = []
    for person in _coerce_rest_required_people(people):
        name = person["name"]
        days = person["effective_attendance_days"]
        if days >= REST_REQUIRED_THRESHOLD_DAYS:
            lines.append(f"{name}（已考勤{days}天）")
    return lines


def _coerce_rest_required_people(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    people: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, Mapping):
            continue
        name = str(item.get("name") or "").strip()
        try:
            days = int(item.get("effective_attendance_days"))
        except (TypeError, ValueError):
            continue
        if name:
            people.append({"name": name, "effective_attendance_days": days})
    return people


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


def _join_names(names: list[str]) -> str:
    return "、".join(names)


def _work_date_from_run_id(run_id: str) -> str | None:
    parts = run_id.split("_")
    if len(parts) >= 3 and len(parts[2]) == 8 and parts[2].isdigit():
        return f"{parts[2][:4]}-{parts[2][4:6]}-{parts[2][6:8]}"
    return None


def _run_type_from_run_id(run_id: str) -> str | None:
    parts = run_id.split("_")
    if len(parts) >= 2 and parts[1] in RUN_TYPES:
        return parts[1]
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
    notification_stats = build_stats_with_rest_required_people(
        collection["stats"],
        month_dir=Path(str(output_status["month_dir"])),
    )
    output_status.update(
        {
            "run_id": plan["run_id"],
            "run_type": run_type,
            "work_date": work_date,
            "current_time": datetime.now(ZoneInfo(timezone)).strftime("%H:%M"),
            "stats": notification_stats,
        }
    )
    try:
        dispatch_receipt = dispatch_reports_with_resolved_channel(output_status=output_status)
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
        "stats": build_stats_with_rest_required_people(
            manifest.get("stats", {}),
            month_dir=manifest_path.parent,
        ),
        "management_report": manifest["management_report"],
        "hr_report": manifest["hr_report"],
        "dispatch_receipt": manifest["dispatch_receipt"],
        "cleanup_audit": manifest["cleanup_audit"],
    }
    dispatch_receipt: dict[str, Any] = {"notification_status": "FAILED"}
    try:
        dispatch_receipt = dispatch_reports_with_resolved_channel(output_status=output_status)
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
