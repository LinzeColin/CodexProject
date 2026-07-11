#!/usr/bin/env python3
"""Optional WeCom fallback boundary for the KMFA DingTalk attendance skill."""

from __future__ import annotations

from typing import Any


def optional_wecom_status() -> dict[str, Any]:
    return {
        "channel": "wecom_optional",
        "enabled": False,
        "status": "NOT_CONFIGURED_OPTIONAL_FALLBACK",
    }
