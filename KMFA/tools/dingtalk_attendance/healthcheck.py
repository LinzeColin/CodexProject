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
from KMFA.tools.dingtalk_attendance.notifier_dingtalk_work_notification import work_notification_status
from KMFA.tools.dingtalk_attendance.secrets_loader import DEFAULT_RUNTIME_ENV_PATH, merged_runtime_env


def build_config_status(env: Mapping[str, str] | None = None) -> dict[str, Any]:
    values = merged_runtime_env() if env is None else dict(env)
    group_robot = robot_notification_status(values)
    work_notification = work_notification_status(values)
    ready_channels = [
        channel["channel"]
        for channel in (group_robot, work_notification)
        if channel["status"] == "READY"
    ]
    channel_aliases = {
        "dingtalk_robot": "dingtalk_group_robot",
        "dingtalk_work_notification": "dingtalk_work_notification",
    }
    ready_aliases = [channel_aliases.get(channel, channel) for channel in ready_channels]
    active_notify_mode = values.get("DINGTALK_NOTIFY_MODE") or (ready_aliases[0] if ready_aliases else "CONFIG_REQUIRED")
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
