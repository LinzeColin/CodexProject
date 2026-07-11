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
    "codex_automation/morning_1035.prompt.md",
    "codex_automation/evening_2000.prompt.md",
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
    "offline_validate_manifest.json",
    "runtime_capability_manifest.json",
}
TRACKED_PRIVATE_RUNTIME_FILES = [".gitkeep", "README.md"]

PROMPT_CONTRACT_NEEDLES = {
    "calls_skill": ("$kmfa-dingtalk-attendance-skill",),
    "uses_beijing_time": ("Asia/Shanghai",),
    "preserves_github_sync": ("HEAD == origin/main", "GitHub `main`"),
    "fails_closed_for_dws": ("DWS_AUTH_REQUIRED", "Do not fabricate data"),
    "uses_official_report_parity": (
        "attendance report columns/query-data",
        "official_report_parity_status=PASS",
        "OFFICIAL_ATTENDANCE_PARITY_FAILED",
    ),
    "protects_private_runtime": (".env.local", "SQLite", "raw JSON", "report bodies"),
}


def validate_prompt_contracts(prompt_files: list[Path]) -> tuple[dict[str, Any], list[str]]:
    by_file: dict[str, dict[str, bool]] = {}
    aggregate = {
        "all_prompts_call_skill": True,
        "all_prompts_use_beijing_time": True,
        "all_prompts_preserve_github_sync": True,
        "all_prompts_fail_closed_for_dws": True,
        "all_prompts_use_official_report_parity": True,
        "all_prompts_protect_private_runtime": True,
    }
    errors: list[str] = []
    aggregate_key_by_contract = {
        "calls_skill": "all_prompts_call_skill",
        "uses_beijing_time": "all_prompts_use_beijing_time",
        "preserves_github_sync": "all_prompts_preserve_github_sync",
        "fails_closed_for_dws": "all_prompts_fail_closed_for_dws",
        "uses_official_report_parity": "all_prompts_use_official_report_parity",
        "protects_private_runtime": "all_prompts_protect_private_runtime",
    }
    for path in prompt_files:
        text = path.read_text(encoding="utf-8")
        rel = path.name
        checks: dict[str, bool] = {}
        for contract_key, needles in PROMPT_CONTRACT_NEEDLES.items():
            passed = all(needle in text for needle in needles)
            checks[contract_key] = passed
            aggregate[aggregate_key_by_contract[contract_key]] = (
                aggregate[aggregate_key_by_contract[contract_key]] and passed
            )
            if not passed:
                errors.append(f"automation prompt contract drift:{rel}:{contract_key}")
        by_file[rel] = checks
    return {**aggregate, "by_file": by_file}, errors


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
    schedule = manifest.get("schedule", {})
    if (
        not isinstance(schedule, dict)
        or schedule.get("morning") != "10:35"
        or schedule.get("evening") != "20:00"
        or schedule.get("evening_clock") != "local_wall_clock"
        or schedule.get("business_date_timezone") != "Asia/Shanghai"
        or schedule.get("scheduler_timezone_configured") is not False
        or schedule.get("summary_datetime_source") != "actual_run_datetime_in_business_date_timezone"
    ):
        errors.append("automation schedule drift")
    if (metadata_root / "codex_automation" / "morning_1035.prompt.md").read_text(encoding="utf-8").find("10:35") < 0:
        errors.append("morning prompt schedule drift")
    if (metadata_root / "codex_automation" / "evening_2000.prompt.md").read_text(encoding="utf-8").find("20:00") < 0:
        errors.append("evening prompt schedule drift")
    if manifest.get("onedrive_root") != ONEDRIVE_ROOT:
        errors.append("onedrive root drift")
    if manifest.get("onedrive_month_folder_pattern") != "YYYYMM":
        errors.append("onedrive month folder pattern drift")
    official_source = manifest.get("official_statistics_source", {})
    if (
        not isinstance(official_source, dict)
        or official_source.get("membership_scope") != "current_attendance_groups"
        or official_source.get("anomaly_source") != "attendance_report_exact_columns"
        or official_source.get("batch_size") != 5
        or official_source.get("business_date_timezone") != "Asia/Shanghai"
        or official_source.get("failure_status") != "OFFICIAL_ATTENDANCE_PARITY_FAILED"
        or official_source.get("legacy_record_and_summary_role") != "diagnostic_only"
    ):
        errors.append("official attendance statistics source drift")
    if unexpected_private_runtime_files:
        errors.append("private runtime contains unexpected local files")
    if len(prompt_files) != 3:
        errors.append("prompt count drift")
    prompt_contracts, prompt_errors = validate_prompt_contracts(prompt_files)
    errors.extend(prompt_errors)
    exemption_probe_context = notification_context_from_output_status(
        {
            "run_id": "s19_morning_20260707_103500",
            "run_type": "morning",
            "work_date": "2026-07-07",
            "current_time": "10:35",
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
    pending_probe = build_notification_message(
        work_date="2026-07-07",
        run_type="morning",
        current_time="10:35",
        unexpected_empty_record_names=[],
        known_no_record_names=[],
        pending_hr_actions=["王五待补卡"],
        monthly_pending_actions=[{"name": "王五", "monthly_count": 3, "latest_date": "2026-07-07"}],
        member_count=44,
        markdown=False,
    )
    if "待审批" in pending_probe or "待补卡" in pending_probe or "待核查" in pending_probe or "王五" in pending_probe:
        errors.append("pending action section rendered in user-visible notification template")
    historical_probe = build_notification_message(
        work_date="2026-07-08",
        run_type="morning",
        current_time="10:35",
        unexpected_empty_record_names=[],
        known_no_record_names=[],
        monthly_attendance_anomalies=[{"name": "历史累计甲", "monthly_count": 3, "latest_date": "2026-07-03"}],
        member_count=44,
        markdown=False,
    )
    if "历史累计甲" in historical_probe or "今日异常 / 无考勤" in historical_probe:
        errors.append("historical monthly anomaly rendered as today anomaly")
    backend_probe_context = notification_context_from_output_status(
        {
            "run_id": "s19_morning_20260707_103500",
            "run_type": "morning",
            "work_date": "2026-07-07",
            "current_time": "10:35",
            "stats": {
                "member_count": 44,
                "record_success_count": 43,
                "summary_success_count": 44,
                "record_failure_count": 1,
                "summary_failure_count": 0,
                "command_failure_count": 1,
                "unexpected_empty_record_names": [],
                "summary_today_anomaly_names": [],
                "incomplete_record_names": [],
                "attendance_anomaly_names": [],
            },
        }
    )
    backend_probe = build_notification_message(**backend_probe_context, markdown=False)
    backend_terms = ("DWS", "record", "summary", "attendance.record:get", "权限", "取数失败", "未覆盖")
    if any(term in backend_probe for term in backend_terms):
        errors.append("backend diagnostics rendered in user-visible notification template")

    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "automation_name": manifest.get("automation_name"),
        "onedrive_root": manifest.get("onedrive_root"),
        "prompt_count": len(prompt_files),
        "automation_prompt_contracts": prompt_contracts,
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
