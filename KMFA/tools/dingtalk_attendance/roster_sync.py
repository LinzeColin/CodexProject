#!/usr/bin/env python3
"""Roster sync boundary for KMFA S19 live-only attendance."""

from __future__ import annotations

from typing import Any

from KMFA.tools.dingtalk_attendance.dingtalk_client import DingTalkClient


def sync_roster(client: DingTalkClient) -> dict[str, Any]:
    client.ensure_ready()
    return {
        "status": "READY_FOR_LIVE_ROSTER_SYNC",
        "uses_sample_data": False,
        "employee_count": None,
    }
