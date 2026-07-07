#!/usr/bin/env python3
"""DingTalk work-notification boundary for KMFA S19."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from KMFA.tools.dingtalk_attendance import ZHANG_LINZE_USER_ID


WORK_NOTIFICATION_REQUIRED_ENV = (
    "DINGTALK_BOSS_USER_ID",
    "DINGTALK_APP_KEY",
    "DINGTALK_APP_CREDENTIAL",
    "DINGTALK_CORP_ID",
    "DINGTALK_AGENT_ID",
)


def work_notification_status(env: Mapping[str, str]) -> dict[str, Any]:
    boss_user_id = env.get("DINGTALK_BOSS_USER_ID")
    missing = [name for name in WORK_NOTIFICATION_REQUIRED_ENV if not env.get(name)]
    configured = not missing
    return {
        "channel": "dingtalk_work_notification",
        "configured": configured,
        "status": "READY" if configured else "NOTIFIER_CONFIG_MISSING",
        "missing": missing,
        "recipients": {
            "zhang_linze": ZHANG_LINZE_USER_ID,
            "boss": boss_user_id or "CONFIG_REQUIRED",
        },
    }
