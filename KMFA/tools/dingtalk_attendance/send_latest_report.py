#!/usr/bin/env python3
"""Send the latest KMFA S19 private reports without collecting attendance again."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable, Mapping
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from KMFA.tools.dingtalk_attendance import ONEDRIVE_ROOT, TIMEZONE, ZHANG_LINZE_USER_ID
from KMFA.tools.dingtalk_attendance.cleanup_runtime import cleanup_runtime
from KMFA.tools.dingtalk_attendance.notification_probe import probe_notification_channels
from KMFA.tools.dingtalk_attendance.notifier_dws_personal_chat import (
    RESOLVED_CHANNEL_PATH,
    dispatch_reports_with_resolved_channel,
    send_text_with_resolved_channel,
)
from KMFA.tools.dingtalk_attendance.secrets_loader import merged_runtime_env


def find_latest_manifest(onedrive_root: Path = Path(ONEDRIVE_ROOT)) -> Path | None:
    candidates = [path for path in onedrive_root.glob("20[0-9][0-9][0-9][0-9]/s19_*_*.manifest.json") if path.is_file()]
    if not candidates:
        return None
    return sorted(candidates, key=lambda path: (path.parent.name, path.name), reverse=True)[0]


def send_latest_report(
    *,
    channel: str = "auto",
    onedrive_root: Path = Path(ONEDRIVE_ROOT),
    resolved_path: Path = RESOLVED_CHANNEL_PATH,
    env: Mapping[str, str] | None = None,
    sender: Callable[..., dict[str, Any]] = send_text_with_resolved_channel,
) -> dict[str, Any]:
    values = merged_runtime_env() if env is None else dict(env)
    cleanup_status: dict[str, Any] = {"status": "NOT_RUN"}
    if channel != "auto":
        return {"status": "FAILED", "failure_reason": f"unsupported channel selector: {channel}"}
    if not resolved_path.exists():
        probe_result = probe_notification_channels(recipient=ZHANG_LINZE_USER_ID, env=values)
        if probe_result.get("status") != "SENT":
            cleanup_status.update(cleanup_runtime())
            return {
                "status": "FAILED",
                "failure_reason": "notification probe failed before latest report send",
                "probe_result": probe_result,
                "cleanup_status": cleanup_status,
            }

    manifest_path = find_latest_manifest(onedrive_root)
    if manifest_path is None:
        cleanup_status.update(cleanup_runtime())
        return {
            "status": "NO_LATEST_REPORT",
            "mode": "send_latest_report",
            "notification_status": "FAILED",
            "cleanup_status": cleanup_status,
        }

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    output_status = {
        "run_id": manifest["run_id"],
        "current_time": datetime.now(ZoneInfo(TIMEZONE)).strftime("%Y-%m-%d %H:%M:%S"),
        "management_report": manifest["management_report"],
        "hr_report": manifest["hr_report"],
        "dispatch_receipt": manifest["dispatch_receipt"],
    }
    try:
        dispatch_receipt = dispatch_reports_with_resolved_channel(
            output_status=output_status,
            resolved_path=resolved_path,
            env=values,
            sender=sender,
        )
    finally:
        cleanup_status.update(cleanup_runtime())

    return {
        "status": dispatch_receipt["notification_status"],
        "mode": "send_latest_report",
        "manifest": str(manifest_path),
        "notification_status": dispatch_receipt["notification_status"],
        "dispatch_receipt": dispatch_receipt,
        "cleanup_status": cleanup_status,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Send latest KMFA S19 private reports.")
    parser.add_argument("--channel", default="auto", choices=("auto",))
    args = parser.parse_args(argv)

    result = send_latest_report(channel=args.channel)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "SENT" else 2


if __name__ == "__main__":
    sys.exit(main())
