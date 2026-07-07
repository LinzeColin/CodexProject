#!/usr/bin/env python3
"""DingTalk work-notification boundary for KMFA S19."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from KMFA.tools.dingtalk_attendance import ZHANG_LINZE_USER_ID


def work_notification_status(env: Mapping[str, str]) -> dict[str, Any]:
    boss_user_id = env.get("DINGTALK_BOSS_USER_ID")
    configured = bool(boss_user_id)
    return {
        "channel": "dingtalk_work_notification",
        "configured": configured,
        "status": "READY" if configured else "NOTIFIER_CONFIG_MISSING",
        "recipients": {
            "zhang_linze": ZHANG_LINZE_USER_ID,
            "boss": boss_user_id or "CONFIG_REQUIRED",
        },
    }
