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

from KMFA.tools.dingtalk_attendance import ONEDRIVE_ROOT, TIMEZONE
from KMFA.tools.dingtalk_attendance.cleanup_runtime import cleanup_runtime
from KMFA.tools.dingtalk_attendance.notifier_dws_personal_chat import (
    RESOLVED_CHANNEL_PATH,
    send_text_with_resolved_channel,
)
from KMFA.tools.dingtalk_attendance.notification_targets import (
    PUBLIC_TARGETS_MANIFEST_PATH,
    TARGETS_RESOLVED_PATH,
    dispatch_reports_to_targets,
    migrate_legacy_resolved_channel,
    probe_notification_targets,
)
from KMFA.tools.dingtalk_attendance.notification_template import run_type_from_run_id, work_date_from_run_id
from KMFA.tools.dingtalk_attendance.secrets_loader import merged_runtime_env


def find_latest_manifest(onedrive_root: Path = Path(ONEDRIVE_ROOT)) -> Path | None:
    candidates = [path for path in onedrive_root.glob("20[0-9][0-9][0-9][0-9]/s19_*_*.manifest.json") if path.is_file()]
    if not candidates:
        return None
    return sorted(candidates, key=lambda path: (path.parent.name, path.name), reverse=True)[0]


def send_latest_report(
    *,
    channel: str = "auto",
    targets: str = "all",
    onedrive_root: Path = Path(ONEDRIVE_ROOT),
    resolved_path: Path = RESOLVED_CHANNEL_PATH,
    targets_resolved_path: Path = TARGETS_RESOLVED_PATH,
    public_targets_manifest_path: Path = PUBLIC_TARGETS_MANIFEST_PATH,
    env: Mapping[str, str] | None = None,
    sender: Callable[..., dict[str, Any]] = send_text_with_resolved_channel,
) -> dict[str, Any]:
    values = merged_runtime_env() if env is None else dict(env)
    cleanup_status: dict[str, Any] = {"status": "NOT_RUN"}
    if channel != "auto":
        return {"status": "FAILED", "failure_reason": f"unsupported channel selector: {channel}"}
    if targets not in {"all", "personal", "group"}:
        return {"status": "FAILED", "failure_reason": f"unsupported targets selector: {targets}"}
    if not targets_resolved_path.exists():
        migrate_legacy_resolved_channel(
            legacy_path=resolved_path,
            targets_resolved_path=targets_resolved_path,
            public_manifest_path=public_targets_manifest_path,
        )
    if not targets_resolved_path.exists():
        probe_result = probe_notification_targets(
            targets_resolved_path=targets_resolved_path,
            public_manifest_path=public_targets_manifest_path,
            target_filter=targets,
            env=values,
        )
        if probe_result.get("status") not in {"SENT", "PARTIAL"}:
            cleanup_status.update(cleanup_runtime())
            return {
                "status": "FAILED",
                "failure_reason": "notification targets probe failed before latest report send",
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
        "run_type": manifest.get("run_type") or run_type_from_run_id(str(manifest["run_id"])),
        "work_date": manifest.get("work_date") or work_date_from_run_id(str(manifest["run_id"])),
        "current_time": datetime.now(ZoneInfo(TIMEZONE)).strftime("%Y-%m-%d %H:%M:%S"),
        "stats": manifest.get("stats", {}),
        "management_report": manifest["management_report"],
        "hr_report": manifest["hr_report"],
        "dispatch_receipt": manifest["dispatch_receipt"],
    }
    try:
        dispatch_receipt = dispatch_reports_to_targets(
            output_status=output_status,
            targets_resolved_path=targets_resolved_path,
            legacy_resolved_path=resolved_path,
            public_manifest_path=public_targets_manifest_path,
            target_filter=targets,
            env=values,
            sender=sender,
        )
    finally:
        cleanup_status.update(cleanup_runtime())

    return {
        "status": dispatch_receipt["notification_status"],
        "mode": "send_latest_report",
        "targets": targets,
        "manifest": str(manifest_path),
        "notification_status": dispatch_receipt["notification_status"],
        "dispatch_receipt": dispatch_receipt,
        "cleanup_status": cleanup_status,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Send latest KMFA S19 private reports.")
    parser.add_argument("--channel", default="auto", choices=("auto",))
    parser.add_argument("--targets", default="all", choices=("all", "personal", "group"))
    args = parser.parse_args(argv)

    result = send_latest_report(channel=args.channel, targets=args.targets)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "SENT" else 2


if __name__ == "__main__":
    sys.exit(main())
