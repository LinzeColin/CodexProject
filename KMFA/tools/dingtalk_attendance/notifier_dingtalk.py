#!/usr/bin/env python3
"""DingTalk robot notification boundary for KMFA S19."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def robot_notification_status(env: Mapping[str, str]) -> dict[str, Any]:
    configured = bool(env.get("DINGTALK_ROBOT_URL") and env.get("DINGTALK_ROBOT_SIGNING_KEY"))
    return {
        "channel": "dingtalk_robot",
        "configured": configured,
        "status": "READY" if configured else "NOTIFIER_CONFIG_MISSING",
    }
