#!/usr/bin/env python3
"""Unified KMFA S19 attendance notification template."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from KMFA.tools.dingtalk_attendance import TIMEZONE


REST_REQUIRED_THRESHOLD_DAYS = 23
REST_REQUIRED_EXCLUDED_NAMES = frozenset({"丁春法", "李永占"})
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
    monthly_attendance_anomalies: list[dict[str, Any]] | None = None,
    monthly_consecutive_anomalies: list[dict[str, Any]] | None = None,
    monthly_pending_actions: list[dict[str, Any]] | None = None,
    run_id: str | None = None,
    beijing_time: str | None = None,
    report_paths: Mapping[str, Any] | None = None,
    markdown: bool = True,
    member_count: int | None = None,
    collection_complete: bool = True,
) -> str:
    title = f"开明考勤提醒｜{work_date}｜{display_run_type(run_type)}"
    lines = [f"# {title}" if markdown else title, "", f"截止 {current_time}", ""]
    abnormal_names = _filter_hidden_names(_dedupe_nonempty([*unexpected_empty_record_names, *known_no_record_names]))
    consecutive_lines = _filter_hidden_lines(coerce_message_lines(consecutive_anomaly_summary))
    abnormal_items = coerce_current_monthly_status_people(monthly_attendance_anomalies, current_names=abnormal_names)
    consecutive_items = _filter_status_people_by_work_date(
        coerce_monthly_status_people(monthly_consecutive_anomalies),
        work_date=work_date,
    )
    rest_items = coerce_rest_required_people(rest_required_people)
    if not abnormal_items and not consecutive_items and not consecutive_lines and not rest_items:
        if collection_complete:
            lines.extend([f"本次{_coerce_nonnegative_int(member_count)}人全部考勤正常", ""])
        else:
            lines.extend(["本次暂无需要处理的考勤事项", ""])
    else:
        _extend_section(
            lines,
            title="今日异常 / 无考勤",
            body_lines=_format_count_people(
                abnormal_items,
                over_limit_header="共 {total} 人，本月累计 Top10:",
                formatter=lambda item: f"{item['name']}（本月累计{item['monthly_count']}次）",
            ),
            markdown=markdown,
        )
        _extend_section(
            lines,
            title="连续异常",
            body_lines=[
                *_format_count_people(
                    consecutive_items,
                    over_limit_header="共 {total} 人，本月累计 Top10:",
                    formatter=lambda item: (
                        f"{item['name']}（连续{item.get('consecutive_days', 0)}天，"
                        f"本月累计{item['monthly_count']}次）"
                    ),
                ),
                *consecutive_lines,
            ],
            markdown=markdown,
        )
        _extend_section(
            lines,
            title="需要休息",
            body_lines=_format_rest_required_people(rest_items),
            markdown=markdown,
        )

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
    run_type = str(output_status.get("run_type") or run_type_from_run_id(run_id) or "unknown")
    anomaly_names = current_notification_anomaly_names(stats, run_type=run_type)
    monthly_consecutive_anomalies = _filter_monthly_people_by_names(
        coerce_monthly_status_people(stats.get("monthly_consecutive_anomalies")),
        anomaly_names,
    )
    return {
        "work_date": str(output_status.get("work_date") or work_date_from_run_id(run_id) or "UNKNOWN_DATE"),
        "run_type": run_type,
        "current_time": current_time,
        "unexpected_empty_record_names": _filter_hidden_names(_dedupe_nonempty(anomaly_names)),
        "known_no_record_names": [],
        "consecutive_anomaly_summary": coerce_message_lines(output_status.get("consecutive_anomaly_summary")),
        "pending_hr_actions": [],
        "rest_required_people": coerce_rest_required_people(stats.get("rest_required_people")),
        "monthly_attendance_anomalies": coerce_monthly_status_people(
            stats.get("monthly_attendance_anomalies"),
            fallback_names=anomaly_names,
        ),
        "monthly_consecutive_anomalies": monthly_consecutive_anomalies,
        "monthly_pending_actions": [],
        "member_count": _coerce_nonnegative_int(stats.get("member_count")),
        "collection_complete": collection_is_complete(stats),
        "run_id": run_id or None,
        "beijing_time": str(output_status.get("beijing_time") or current_time),
        "report_paths": {
            key: str(output_status.get(key) or "")
            for key in ("management_report", "hr_report")
            if output_status.get(key)
        },
    }


def collection_is_complete(stats: Mapping[str, Any]) -> bool:
    member_count = _coerce_nonnegative_int(stats.get("member_count"))
    if _coerce_nonnegative_int(stats.get("record_failure_count")):
        return False
    if _coerce_nonnegative_int(stats.get("summary_failure_count")):
        return False
    if _coerce_nonnegative_int(stats.get("command_failure_count")):
        return False
    if member_count and "record_success_count" in stats and _coerce_nonnegative_int(stats.get("record_success_count")) != member_count:
        return False
    if member_count and "summary_success_count" in stats and _coerce_nonnegative_int(stats.get("summary_success_count")) != member_count:
        return False
    return True


def current_notification_anomaly_names(stats: Mapping[str, Any], *, run_type: str) -> list[str]:
    detail_keys = {"unexpected_empty_record_names", "summary_today_anomaly_names", "incomplete_record_names"}
    known_no_record_names = set(coerce_message_lines(stats.get("known_no_record_names")))
    if any(key in stats for key in detail_keys):
        names = [
            *coerce_message_lines(stats.get("unexpected_empty_record_names")),
            *coerce_message_lines(stats.get("summary_today_anomaly_names")),
        ]
        if str(run_type) != "morning":
            names.extend(coerce_message_lines(stats.get("incomplete_record_names")))
    else:
        names = coerce_message_lines(stats.get("attendance_anomaly_names"))
    return _filter_hidden_names(_dedupe_nonempty(name for name in names if name not in known_no_record_names))


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
        if name and name not in REST_REQUIRED_EXCLUDED_NAMES and days >= REST_REQUIRED_THRESHOLD_DAYS:
            person = {"name": name, "effective_attendance_days": days}
            latest_date = str(item.get("latest_date") or item.get("last_date") or "").strip()
            if latest_date:
                person["latest_date"] = latest_date
            people.append(person)
    return _sort_people(people, metric_key="effective_attendance_days")


def coerce_monthly_status_people(value: Any, *, fallback_names: list[str] | None = None) -> list[dict[str, Any]]:
    people: list[dict[str, Any]] = []
    if isinstance(value, list):
        for item in value:
            if not isinstance(item, Mapping):
                continue
            name = str(item.get("name") or "").strip()
            if not name:
                continue
            count = _coerce_nonnegative_int(item.get("monthly_count", item.get("count")))
            if count <= 0:
                count = 1
            person: dict[str, Any] = {
                "name": name,
                "monthly_count": count,
                "latest_date": str(item.get("latest_date") or item.get("last_date") or "").strip(),
            }
            consecutive_days = _coerce_nonnegative_int(item.get("consecutive_days"))
            if consecutive_days:
                person["consecutive_days"] = consecutive_days
            people.append(person)
    if not people and fallback_names:
        people = [{"name": name, "monthly_count": 1, "latest_date": ""} for name in _filter_hidden_names(_dedupe_nonempty(fallback_names))]
    return _sort_people(_filter_hidden_people(people), metric_key="monthly_count")


def coerce_current_monthly_status_people(value: Any, *, current_names: list[str]) -> list[dict[str, Any]]:
    names = _filter_hidden_names(_dedupe_nonempty(current_names))
    if not names:
        return []
    monthly_by_name = {str(item.get("name") or ""): item for item in coerce_monthly_status_people(value)}
    people: list[dict[str, Any]] = []
    for name in names:
        monthly_item = monthly_by_name.get(name)
        if monthly_item:
            people.append(monthly_item)
        else:
            people.append({"name": name, "monthly_count": 1, "latest_date": ""})
    return _sort_people(_filter_hidden_people(people), metric_key="monthly_count")


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


def _extend_section(lines: list[str], *, title: str, body_lines: list[str], markdown: bool) -> None:
    if not body_lines:
        return
    lines.append(f"## {title}" if markdown else title)
    lines.extend(body_lines)
    lines.append("")


def _format_count_people(
    people: list[dict[str, Any]],
    *,
    over_limit_header: str,
    formatter: Any,
) -> list[str]:
    if not people:
        return []
    if len(people) <= 10:
        return [formatter(item) for item in people]
    top10 = people[:10]
    return [
        over_limit_header.format(total=len(people)),
        *[f"{index}. {formatter(item)}" for index, item in enumerate(top10, start=1)],
    ]


def _format_rest_required_people(people: list[dict[str, Any]] | None) -> list[str]:
    rest_people = coerce_rest_required_people(people)
    if not rest_people:
        return []
    formatter = lambda item: f"{item['name']}（本月有效考勤{item['effective_attendance_days']}天）"
    if len(rest_people) <= 10:
        return [formatter(item) for item in rest_people]
    return [
        f"共 {len(rest_people)} 人需要安排休息，展示 Top10:",
        *[f"{index}. {formatter(item)}" for index, item in enumerate(rest_people[:10], start=1)],
    ]


def _filter_hidden_people(people: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [person for person in people if str(person.get("name") or "") not in NOTIFICATION_HIDDEN_NAMES]


def _sort_people(people: list[dict[str, Any]], *, metric_key: str) -> list[dict[str, Any]]:
    return sorted(
        people,
        key=lambda item: (
            -_coerce_nonnegative_int(item.get(metric_key)),
            -_date_ordinal(str(item.get("latest_date") or "")),
            str(item.get("name") or ""),
        ),
    )


def _date_ordinal(value: str) -> int:
    try:
        return datetime.fromisoformat(value[:10]).date().toordinal()
    except ValueError:
        return 0


def _filter_hidden_names(names: list[str]) -> list[str]:
    return [name for name in names if name not in NOTIFICATION_HIDDEN_NAMES]


def _filter_hidden_lines(lines: list[str]) -> list[str]:
    return [line for line in lines if not any(name in line for name in NOTIFICATION_HIDDEN_NAMES)]


def _filter_status_people_by_work_date(people: list[dict[str, Any]], *, work_date: str) -> list[dict[str, Any]]:
    return [
        person
        for person in people
        if not str(person.get("latest_date") or "").strip() or str(person.get("latest_date") or "").strip()[:10] == work_date
    ]


def _filter_monthly_people_by_names(people: list[dict[str, Any]], names: list[str]) -> list[dict[str, Any]]:
    allowed = set(names)
    if not allowed:
        return []
    return [person for person in people if str(person.get("name") or "") in allowed]


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
