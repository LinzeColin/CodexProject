#!/usr/bin/env python3
"""Attendance collection boundary for KMFA S19."""

from __future__ import annotations

from typing import Any

from KMFA.tools.dingtalk_attendance.dingtalk_client import DingTalkClient


def collect_attendance(client: DingTalkClient, *, run_type: str) -> dict[str, Any]:
    client.ensure_ready()
    return {
        "status": "READY_FOR_LIVE_ATTENDANCE_COLLECTION",
        "run_type": run_type,
        "uses_sample_data": False,
        "attendance_result_count": None,
        "detail_record_count": None,
    }
