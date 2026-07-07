#!/usr/bin/env python3
"""Health checks for KMFA S19 DingTalk attendance automation."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.dingtalk_attendance import AUTOMATION_NAME, ONEDRIVE_ROOT, STAGE_ID, TIMEZONE


REQUIRED_LIVE_ENV = (
    "DINGTALK_APP_KEY",
    "DINGTALK_APP_CREDENTIAL",
    "DINGTALK_CORP_ID",
    "DINGTALK_AGENT_ID",
)

OPTIONAL_NOTIFY_ENV = (
    "DINGTALK_ROBOT_URL",
    "DINGTALK_ROBOT_SIGNING_KEY",
    "DINGTALK_BOSS_USER_ID",
    "DINGTALK_CONVERSATION_ID",
)


def build_config_status(env: Mapping[str, str] | None = None) -> dict[str, Any]:
    values = dict(os.environ if env is None else env)
    missing = [name for name in REQUIRED_LIVE_ENV if not values.get(name)]
    missing_notify = [name for name in OPTIONAL_NOTIFY_ENV if not values.get(name)]
    status = "OK" if not missing else "CONFIG_MISSING"
    return {
        "project_id": "KMFA",
        "stage_id": STAGE_ID,
        "automation_name": AUTOMATION_NAME,
        "status": status,
        "timezone": TIMEZONE,
        "onedrive_root": ONEDRIVE_ROOT,
        "live_collection_allowed": status == "OK",
        "uses_sample_data": False,
        "missing": missing,
        "notification_missing": missing_notify,
        "notifier_configured": not missing_notify,
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
