#!/usr/bin/env python3
"""Health checks for KMFA S19 DingTalk attendance automation."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from KMFA.tools.dingtalk_attendance import AUTOMATION_NAME, ONEDRIVE_ROOT, STAGE_ID, TIMEZONE
from KMFA.tools.dingtalk_attendance.notifier_dingtalk import robot_notification_status
from KMFA.tools.dingtalk_attendance.notifier_dws_personal_chat import RESOLVED_CHANNEL_PATH
from KMFA.tools.dingtalk_attendance.notifier_dingtalk_work_notification import work_notification_status
from KMFA.tools.dingtalk_attendance.notification_targets import TARGETS_RESOLVED_PATH
from KMFA.tools.dingtalk_attendance.secrets_loader import DEFAULT_RUNTIME_ENV_PATH, merged_runtime_env


def build_config_status(env: Mapping[str, str] | None = None) -> dict[str, Any]:
    values = merged_runtime_env() if env is None else dict(env)
    group_robot = robot_notification_status(values)
    work_notification = work_notification_status(values)
    multi_target = _notification_targets_status() if env is None else _missing_notification_targets_status()
    resolved_personal = _resolved_personal_status() if env is None else _missing_resolved_personal_status()
    ready_channels = [
        channel["channel"]
        for channel in (multi_target, resolved_personal, group_robot, work_notification)
        if channel["status"] == "READY"
    ]
    channel_aliases = {
        "dingtalk_robot": "dingtalk_group_robot",
        "dingtalk_work_notification": "dingtalk_work_notification",
    }
    ready_aliases = [channel_aliases.get(channel, channel) for channel in ready_channels]
    active_notify_mode = ready_aliases[0] if ready_aliases else values.get("DINGTALK_NOTIFY_MODE", "CONFIG_REQUIRED")
    notification_ready = bool(ready_aliases)
    status = "READY" if notification_ready else "NOTIFIER_CONFIG_MISSING"
    return {
        "project_id": "KMFA",
        "stage_id": STAGE_ID,
        "automation_name": AUTOMATION_NAME,
        "status": status,
        "timezone": TIMEZONE,
        "onedrive_root": ONEDRIVE_ROOT,
        "backend": "dws",
        "live_collection_allowed": True,
        "uses_sample_data": False,
        "missing": [] if notification_ready else sorted(set(group_robot["missing"] + work_notification["missing"])),
        "notification_ready": notification_ready,
        "notification_ready_channels": ready_aliases,
        "active_notify_mode": active_notify_mode,
        "notification_missing": [] if notification_ready else sorted(set(group_robot["missing"] + work_notification["missing"])),
        "group_robot_missing": group_robot["missing"],
        "work_notification_missing": work_notification["missing"],
        "notifier_configured": notification_ready,
        "notification_channels": {
            "multi_target": multi_target,
            "resolved_personal": resolved_personal,
            "dingtalk_group_robot": group_robot,
            "dingtalk_work_notification": work_notification,
        },
        "runtime_env_path": str(DEFAULT_RUNTIME_ENV_PATH),
        "private_runtime_expected": "KMFA/metadata/dingtalk_attendance/private_runtime",
        "public_repo_safety": {
            "employee_plaintext_committed": False,
            "sqlite_committed": False,
            "credential_committed": False,
            "raw_api_response_committed": False,
            "report_body_committed": False,
        },
    }


def _resolved_personal_status() -> dict[str, Any]:
    if not RESOLVED_CHANNEL_PATH.exists():
        return _missing_resolved_personal_status()
    try:
        payload = json.loads(RESOLVED_CHANNEL_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {
            "channel": "resolved_personal",
            "configured": False,
            "status": "NOTIFIER_CONFIG_MISSING",
            "missing": ["notification_channel_resolved.json"],
        }
    channel = str(payload.get("channel") or "")
    ready = payload.get("status") == "SENT" and bool(channel)
    return {
        "channel": channel or "resolved_personal",
        "configured": ready,
        "status": "READY" if ready else "NOTIFIER_CONFIG_MISSING",
        "missing": [] if ready else ["notification_channel_resolved.json"],
        "channel_type": payload.get("channel_type"),
    }


def _notification_targets_status() -> dict[str, Any]:
    if not TARGETS_RESOLVED_PATH.exists():
        return _missing_notification_targets_status()
    try:
        payload = json.loads(TARGETS_RESOLVED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _missing_notification_targets_status()
    targets = [target for target in payload.get("targets", []) if isinstance(target, Mapping) and target.get("enabled", True)]
    ready_targets = [target for target in targets if target.get("last_probe_status") == "SENT" and target.get("resolved_channel")]
    ready = bool(ready_targets)
    return {
        "channel": "multi_target",
        "configured": ready,
        "status": "READY" if ready else "NOTIFIER_CONFIG_MISSING",
        "missing": [] if ready else ["notification_targets_resolved.json"],
        "target_count": len(targets),
        "ready_target_count": len(ready_targets),
        "ready_channels": sorted({str(target.get("resolved_channel")) for target in ready_targets}),
    }


def _missing_notification_targets_status() -> dict[str, Any]:
    return {
        "channel": "multi_target",
        "configured": False,
        "status": "NOTIFIER_CONFIG_MISSING",
        "missing": ["notification_targets_resolved.json"],
        "target_count": 0,
        "ready_target_count": 0,
        "ready_channels": [],
    }


def _missing_resolved_personal_status() -> dict[str, Any]:
    return {
        "channel": "resolved_personal",
        "configured": False,
        "status": "NOTIFIER_CONFIG_MISSING",
        "missing": ["notification_channel_resolved.json"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check KMFA S19 DingTalk attendance configuration.")
    parser.add_argument("--config-only", action="store_true", help="Only inspect local configuration readiness.")
    args = parser.parse_args(argv)

    status = build_config_status()
    print(json.dumps(status, ensure_ascii=False, indent=2, sort_keys=True))
    if args.config_only:
        return 0
    return 0 if status["status"] == "OK" else 2


if __name__ == "__main__":
    sys.exit(main())
