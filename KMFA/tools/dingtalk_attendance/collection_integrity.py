#!/usr/bin/env python3
"""Run-type-specific completeness gates for attendance collection."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from KMFA.tools.dingtalk_attendance.notification_template import (
    official_report_parity_failure_reason,
)


REMINDER_RUN_TYPES = frozenset({"morning", "evening"})


def realtime_reminder_integrity_failure_reason(
    stats: Mapping[str, Any],
    *,
    run_type: str,
) -> str | None:
    """Return None only for an exact, successfully parsed live reminder scope."""

    if run_type not in REMINDER_RUN_TYPES:
        return f"unsupported realtime reminder run_type: {run_type}"
    if stats.get("realtime_reminder_run_type") != run_type:
        return "realtime reminder run_type does not match collection"
    if stats.get("realtime_reminder_integrity_status") != "PASS":
        return "realtime_reminder_integrity_status must be PASS"

    count_keys = (
        "attendance_group_member_count",
        "member_count",
        "realtime_reminder_expected_count",
        "realtime_reminder_coverage_count",
        "realtime_reminder_query_failure_count",
        "realtime_reminder_parse_failure_count",
        "realtime_reminder_anomaly_count",
    )
    counts: dict[str, int] = {}
    for key in count_keys:
        if key not in stats:
            return f"missing required realtime reminder field: {key}"
        value = stats.get(key)
        if isinstance(value, bool):
            return f"invalid realtime reminder count: {key}"
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return f"invalid realtime reminder count: {key}"
        if parsed < 0 or str(value).strip() not in {str(parsed), f"{parsed}.0"}:
            return f"invalid realtime reminder count: {key}"
        counts[key] = parsed

    member_count = counts["member_count"]
    if member_count <= 0:
        return "realtime reminder member_count must be positive"
    for key in (
        "attendance_group_member_count",
        "realtime_reminder_expected_count",
        "realtime_reminder_coverage_count",
    ):
        if counts[key] != member_count:
            return f"realtime reminder scope mismatch: {key}"
    if counts["realtime_reminder_query_failure_count"] != 0:
        return "realtime reminder query failure count must be zero"
    if counts["realtime_reminder_parse_failure_count"] != 0:
        return "realtime reminder parse failure count must be zero"
    if counts["realtime_reminder_anomaly_count"] > member_count:
        return "realtime reminder anomaly count exceeds member_count"

    names = stats.get("realtime_reminder_anomaly_names")
    if not isinstance(names, list):
        return "realtime_reminder_anomaly_names must be a list"
    normalized_names = [str(name).strip() for name in names if str(name).strip()]
    if len(normalized_names) != len(names):
        return "realtime_reminder_anomaly_names contains blank entries"
    if len(normalized_names) != counts["realtime_reminder_anomaly_count"]:
        return "realtime reminder anomaly names/count mismatch"
    return None


def collection_integrity_failure_reason(
    stats: Mapping[str, Any],
    *,
    run_type: str,
) -> str | None:
    """Route temporary reminders and final reconciliation to separate gates."""

    if run_type in REMINDER_RUN_TYPES:
        return realtime_reminder_integrity_failure_reason(stats, run_type=run_type)
    if run_type == "final":
        return official_report_parity_failure_reason(stats)
    return f"unsupported attendance run_type: {run_type}"
