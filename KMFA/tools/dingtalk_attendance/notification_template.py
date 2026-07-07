#!/usr/bin/env python3
"""Unified KMFA S19 attendance notification template."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from KMFA.tools.dingtalk_attendance import TIMEZONE


REST_REQUIRED_THRESHOLD_DAYS = 27
NOTIFICATION_HIDDEN_NAMES = frozenset()
RUN_TYPE_DISPLAY_LABELS = {
    "morning": "晨报",
    "evening": "晚报",
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
    run_id: str | None = None,
    beijing_time: str | None = None,
    report_paths: Mapping[str, Any] | None = None,
    markdown: bool = True,
    member_count: int | None = None,
) -> str:
    title = f"开明考勤提醒｜{work_date}｜{display_run_type(run_type)}"
    lines = [f"# {title}" if markdown else title, "", f"截止 {current_time}", ""]
    abnormal_names = _filter_hidden_names(_dedupe_nonempty([*unexpected_empty_record_names, *known_no_record_names]))
    consecutive_lines = _filter_hidden_lines(coerce_message_lines(consecutive_anomaly_summary))
    pending_lines = _filter_hidden_lines(coerce_message_lines(pending_hr_actions))
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
        lines.extend([f"本次{_coerce_nonnegative_int(member_count)}人全部考勤正常，今天一切良好", ""])

    return "\n".join(lines).rstrip() + "\n"


def build_personal_notification_message(**kwargs: Any) -> str:
    kwargs.pop("markdown", None)
    return build_notification_message(**kwargs, markdown=False)


def notification_context_from_output_status(output_status: Mapping[str, Any]) -> dict[str, Any]:
    stats = output_status.get("stats", {})
    if not isinstance(stats, Mapping):
        stats = {}
    current_time = str(output_status.get("current_time") or datetime.now(ZoneInfo(TIMEZONE)).strftime("%H:%M"))
    run_id = str(output_status.get("run_id") or "")
    pending_actions = coerce_message_lines(output_status.get("pending_hr_actions"))
    pending_actions.extend(system_issue_lines_from_stats(stats))
    anomaly_names = coerce_message_lines(stats.get("attendance_anomaly_names"))
    if not anomaly_names:
        anomaly_names = [
            *coerce_message_lines(stats.get("unexpected_empty_record_names")),
            *coerce_message_lines(stats.get("incomplete_record_names")),
        ]
    return {
        "work_date": str(output_status.get("work_date") or work_date_from_run_id(run_id) or "UNKNOWN_DATE"),
        "run_type": str(output_status.get("run_type") or run_type_from_run_id(run_id) or "unknown"),
        "current_time": current_time,
        "unexpected_empty_record_names": _filter_hidden_names(_dedupe_nonempty(anomaly_names)),
        "known_no_record_names": [],
        "consecutive_anomaly_summary": coerce_message_lines(output_status.get("consecutive_anomaly_summary")),
        "pending_hr_actions": pending_actions,
        "rest_required_people": coerce_rest_required_people(stats.get("rest_required_people")),
        "member_count": _coerce_nonnegative_int(stats.get("member_count")),
        "run_id": run_id or None,
        "beijing_time": str(output_status.get("beijing_time") or current_time),
        "report_paths": {
            key: str(output_status.get(key) or "")
            for key in ("management_report", "hr_report")
            if output_status.get(key)
        },
    }


def system_issue_lines_from_stats(stats: Mapping[str, Any]) -> list[str]:
    lines: list[str] = []
    member_count = _coerce_nonnegative_int(stats.get("member_count"))
    record_successes = _coerce_nonnegative_int(stats.get("record_success_count"))
    summary_successes = _coerce_nonnegative_int(stats.get("summary_success_count"))
    record_failures = _coerce_nonnegative_int(stats.get("record_failure_count"))
    summary_failures = _coerce_nonnegative_int(stats.get("summary_failure_count"))
    command_failures = _coerce_nonnegative_int(stats.get("command_failure_count"))
    if record_failures:
        lines.append(f"DWS record 取数失败 {record_failures} 人，需核查 attendance.record:get 权限。")
    elif member_count and record_successes != member_count:
        lines.append(f"DWS record 取数未覆盖全部人员：成功 {record_successes}/{member_count}，不得判定为正常。")
    if summary_failures:
        lines.append(f"DWS summary 取数失败 {summary_failures} 人，需核查 attendance:summary 权限。")
    elif member_count and summary_successes != member_count:
        lines.append(f"DWS summary 取数未覆盖全部人员：成功 {summary_successes}/{member_count}，不得判定为正常。")
    if command_failures and not record_failures and not summary_failures:
        lines.append(f"DWS 取数命令失败 {command_failures} 次，需核查权限或接口状态。")
    return lines


def coerce_message_lines(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        stripped = value.strip()
        return [stripped] if stripped and stripped != "无" else []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip() and str(item).strip() != "无"]
    return []


def coerce_rest_required_people(value: Any) -> list[dict[str, Any]]:
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


def _coerce_nonnegative_int(value: Any) -> int:
    try:
        result = int(value)
    except (TypeError, ValueError):
        return 0
    return max(result, 0)


def work_date_from_run_id(run_id: str) -> str | None:
    parts = run_id.split("_")
    if len(parts) >= 3 and len(parts[2]) == 8 and parts[2].isdigit():
        return f"{parts[2][:4]}-{parts[2][4:6]}-{parts[2][6:8]}"
    return None


def run_type_from_run_id(run_id: str) -> str | None:
    parts = run_id.split("_")
    if len(parts) >= 2 and parts[1] in {"morning", "evening"}:
        return parts[1]
    return None


def display_run_type(run_type: str) -> str:
    return RUN_TYPE_DISPLAY_LABELS.get(str(run_type), "未知报次")


def _format_rest_required_people(people: list[dict[str, Any]] | None) -> list[str]:
    lines: list[str] = []
    for person in coerce_rest_required_people(people):
        name = person["name"]
        days = person["effective_attendance_days"]
        if days >= REST_REQUIRED_THRESHOLD_DAYS and name not in NOTIFICATION_HIDDEN_NAMES:
            lines.append(f"{name}（已考勤{days}天）")
    return lines


def _filter_hidden_names(names: list[str]) -> list[str]:
    return [name for name in names if name not in NOTIFICATION_HIDDEN_NAMES]


def _filter_hidden_lines(lines: list[str]) -> list[str]:
    return [line for line in lines if not any(name in line for name in NOTIFICATION_HIDDEN_NAMES)]


def _dedupe_nonempty(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _join_names(names: list[str]) -> str:
    return "、".join(names)
