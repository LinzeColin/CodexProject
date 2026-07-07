#!/usr/bin/env python3
"""Validate KMFA S19 DingTalk attendance public-safe file contract."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from KMFA.tools.dingtalk_attendance import AUTOMATION_NAME, ONEDRIVE_ROOT
from KMFA.tools.dingtalk_attendance.notification_template import (
    build_notification_message,
    notification_context_from_output_status,
)


REQUIRED_METADATA_FILES = (
    "README.md",
    "attendance_database_manifest.json",
    "retention_policy.yaml",
    "report_policy.yaml",
    "notification_policy.yaml",
    "notification_channel_manifest.json",
    "notification_targets_manifest.json",
    "onedrive_storage_manifest.yaml",
    "secrets_policy.md",
    "codex_automation/morning_0835.prompt.md",
    "codex_automation/evening_1815.prompt.md",
    "codex_automation/manual_rerun.prompt.md",
    "private_runtime/README.md",
    "private_runtime/.gitkeep",
)

REQUIRED_TOOL_FILES = (
    "__init__.py",
    "run_attendance.py",
    "dws_auth_guard.py",
    "dws_attendance.py",
    "dingtalk_client.py",
    "roster_sync.py",
    "attendance_collect.py",
    "anomaly_rules.py",
    "report_renderer.py",
    "notifier_dingtalk.py",
    "notifier_dws_personal_chat.py",
    "notifier_dingtalk_work_notification.py",
    "notifier_wecom_optional.py",
    "notification_template.py",
    "notification_targets.py",
    "onedrive_archive.py",
    "cleanup_runtime.py",
    "healthcheck.py",
    "notification_probe.py",
    "manage_notification_targets.py",
    "send_latest_report.py",
    "sync_attendance_ledger.py",
    "query_attendance_ledger.py",
    "secrets_loader.py",
    "validate_no_sensitive_git.py",
    "check_s19_dingtalk_attendance.py",
)
ALLOWED_PRIVATE_RUNTIME_FILES = {
    ".gitkeep",
    "README.md",
    ".env.local",
    "notification_channel_resolved.json",
    "notification_probe_diagnostic.json",
    "notification_targets.local.json",
    "notification_targets_resolved.json",
    "attendance_ledger.sqlite",
}
TRACKED_PRIVATE_RUNTIME_FILES = [".gitkeep", "README.md"]


def validate_s19_files(root: Path) -> dict[str, Any]:
    metadata_root = root / "metadata" / "dingtalk_attendance"
    tool_root = root / "tools" / "dingtalk_attendance"
    missing = [
        f"metadata/dingtalk_attendance/{rel}"
        for rel in REQUIRED_METADATA_FILES
        if not (metadata_root / rel).exists()
    ]
    missing.extend(
        f"tools/dingtalk_attendance/{rel}"
        for rel in REQUIRED_TOOL_FILES
        if not (tool_root / rel).exists()
    )
    if missing:
        return {"status": "FAIL", "missing": missing}

    manifest = json.loads((metadata_root / "attendance_database_manifest.json").read_text(encoding="utf-8"))
    private_runtime_files = sorted(path.name for path in (metadata_root / "private_runtime").iterdir() if path.is_file())
    unexpected_private_runtime_files = [
        name for name in private_runtime_files if name not in ALLOWED_PRIVATE_RUNTIME_FILES
    ]
    prompt_files = sorted((metadata_root / "codex_automation").glob("*.prompt.md"))

    errors: list[str] = []
    if manifest.get("automation_name") != AUTOMATION_NAME:
        errors.append("automation name drift")
    if manifest.get("onedrive_root") != ONEDRIVE_ROOT:
        errors.append("onedrive root drift")
    if manifest.get("onedrive_month_folder_pattern") != "YYYYMM":
        errors.append("onedrive month folder pattern drift")
    if unexpected_private_runtime_files:
        errors.append("private runtime contains unexpected local files")
    if len(prompt_files) != 3:
        errors.append("prompt count drift")
    exemption_probe_context = notification_context_from_output_status(
        {
            "run_id": "s19_morning_20260707_083500",
            "run_type": "morning",
            "work_date": "2026-07-07",
            "current_time": "08:35",
            "stats": {
                "attendance_anomaly_names": ["张三", "李四"],
                "known_no_record_names": ["张霖泽", "林全意"],
            },
        }
    )
    exemption_probe = build_notification_message(**exemption_probe_context, markdown=False)
    if "今日异常 / 无考勤\n张三（本月累计1次）\n李四（本月累计1次）" not in exemption_probe:
        errors.append("real anomaly names not rendered in user-visible notification template")
    if "张霖泽" in exemption_probe or "林全意" in exemption_probe:
        errors.append("exempt no-attendance names rendered as user-visible anomalies")
    if "morning" in exemption_probe or "evening" in exemption_probe:
        errors.append("English run type rendered in user-visible notification template")

    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "automation_name": manifest.get("automation_name"),
        "onedrive_root": manifest.get("onedrive_root"),
        "prompt_count": len(prompt_files),
        "private_runtime_tracked_files": TRACKED_PRIVATE_RUNTIME_FILES,
        "private_runtime_local_files_allowed": sorted(
            name for name in private_runtime_files if name in ALLOWED_PRIVATE_RUNTIME_FILES
        ),
        "private_runtime_unexpected_files": unexpected_private_runtime_files,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA S19 DingTalk attendance file contract.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args(argv)

    result = validate_s19_files(args.root)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
