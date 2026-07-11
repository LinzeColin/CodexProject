#!/usr/bin/env python3
"""Minimal live-only DingTalk client boundary for KMFA DingTalk attendance."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from KMFA.tools.dingtalk_attendance.healthcheck import build_config_status


class DingTalkConfigError(RuntimeError):
    """Raised when live DingTalk configuration is missing."""


@dataclass(frozen=True)
class DingTalkClient:
    env: dict[str, str]

    def ensure_ready(self) -> None:
        status = build_config_status(self.env)
        if status["status"] != "OK":
            raise DingTalkConfigError("CONFIG_MISSING")

    def list_attendance_results(self, *, user_ids: list[str], work_date_from: str, work_date_to: str) -> dict[str, Any]:
        self.ensure_ready()
        return {
            "status": "LIVE_CALL_NOT_EXECUTED_IN_CONFIG_ONLY_MODE",
            "user_id_count": len(user_ids),
            "work_date_from": work_date_from,
            "work_date_to": work_date_to,
        }

    def list_attendance_records(self, *, user_id: str, check_date_from: str, check_date_to: str) -> dict[str, Any]:
        self.ensure_ready()
        return {
            "status": "LIVE_CALL_NOT_EXECUTED_IN_CONFIG_ONLY_MODE",
            "user_id": user_id,
            "check_date_from": check_date_from,
            "check_date_to": check_date_to,
        }
