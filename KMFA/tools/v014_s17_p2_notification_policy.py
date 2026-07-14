#!/usr/bin/env python3
"""Generate KMFA v0.1.4 S17-P2 notification policy evidence.

This phase locks public-safe notification reminder rules and metadata logs.
It does not deliver notifications, invoke external mail connectors, include
full report email body, attach reports, expose recipient addresses, read raw
private inbox content, enter S17-P3, perform Stage 17 review, or upload.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.check_v014_s17_p1_access_security import (  # noqa: E402
    validate_v014_s17_p1_access_security,
)
from KMFA.tools.notification_reminders import (  # noqa: E402
    POLICY_VERSION as LEGACY_S17_P2_POLICY_VERSION,
    REQUIRED_NOTIFICATION_TRIGGERS,
    build_default_notification_reminders,
    validate_notification_reminder_artifacts,
)


TASK_ID = "KMFA-V014-S17-P2-NOTIFICATION-POLICY-20260705"
ACCEPTANCE_ID = "ACC-V014-S17-P2-NOTIFICATION-POLICY"
SCHEMA_VERSION = "kmfa.v014_s17_p2_notification_policy.v1"
PHASE_SCOPE = "v014_s17_p2_notification_policy_only"
POLICY_LOCK_VERSION = "LOCK-KMFA-V014-S17P2-NOTIFICATION-POLICY-PUBLIC-SAFE-001"
FORMULA_ID = "FORM-KMFA-V014-S17P2-NOTIFICATION-POLICY-001"
MAPPING_VERSION = "MAP-KMFA-V014-S17P2-NOTIFICATION-POLICY-v1"

REQUIRED_V014_NOTIFICATION_TRIGGERS = REQUIRED_NOTIFICATION_TRIGGERS

OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_S17_P2_NOTIFICATION_POLICY")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
METADATA_DIR = Path("KMFA/metadata/notifications")

MANIFEST_PATH = MACHINE_DIR / "notification_policy_manifest.json"
RULE_LOCK_PATH = MACHINE_DIR / "notification_rule_lock.jsonl"
EVENT_LOG_PATH = MACHINE_DIR / "notification_event_log.jsonl"
DISPATCH_LOG_PATH = MACHINE_DIR / "notification_dispatch_log.jsonl"
METADATA_MANIFEST_PATH = METADATA_DIR / "v014_s17_p2_notification_manifest.json"
METADATA_RULES_PATH = METADATA_DIR / "v014_s17_p2_notification_rules.jsonl"
METADATA_EVENTS_PATH = METADATA_DIR / "v014_s17_p2_notification_events.jsonl"
METADATA_DISPATCH_LOG_PATH = METADATA_DIR / "v014_s17_p2_notification_dispatch_log.jsonl"

REPORT_PATH = HUMAN_DIR / "notification_policy_report.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

V14_TASKPACK_PATH = Path("KMFA/taskpack/v1_4/taskpack/01_KMFA_Codex_TaskPack_v1_4_public_safe.md")
V14_ROADMAP_PATH = Path("KMFA/taskpack/v1_4/roadmap/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_4.md")
RAW_INBOX_REF = "operator-designated raw/private inbox outside repository"
NEXT_PHASE = "S17-P3"
NEXT_REQUIRED_STEP = (
    "Proceed to v0.1.4 S17-P3 audit and operations as a separate run only after user instruction. "
    "Do not perform Stage 17 review, GitHub upload, real notification delivery, external connector use, "
    "full report email body, formal report release, app reinstall, raw inbox access, or business execution in S17-P2."
)
RAW_ACTION_KEYS = (
    "raw_inbox_read_by_this_phase",
    "raw_inbox_listed_by_this_phase",
    "raw_inbox_inventory_by_this_phase",
    "raw_inbox_stat_by_this_phase",
    "raw_inbox_hashed_by_this_phase",
    "raw_inbox_modified_by_this_phase",
    "raw_inbox_deleted_by_this_phase",
    "raw_inbox_moved_by_this_phase",
    "raw_inbox_renamed_by_this_phase",
    "raw_inbox_overwritten_by_this_phase",
    "raw_inbox_written_by_this_phase",
    "raw_inbox_mutated_by_this_phase",
)


def git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_test_results_placeholder() -> None:
    if TEST_RESULTS_PATH.exists():
        existing = TEST_RESULTS_PATH.read_text(encoding="utf-8")
        if (
            "focused v0.1.4 S17-P2 unit test: PASS" in existing
            and "scoped S17-P2 public artifact boundary scan: PASS" in existing
        ):
            return
    write_text(
        TEST_RESULTS_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 S17-P2 Notification Policy Test Results",
                "",
                "- generator: pending final validation replay",
                "- validator: pending final validation replay",
                "- focused_unittest: pending final validation replay",
                "- governance_validation: pending final validation replay",
                "- raw_secret_scan: pending final validation replay",
                "",
            ]
        ),
    )


def validate_s17_p1_dependency() -> dict[str, Any]:
    result = validate_v014_s17_p1_access_security()
    if result.get("stage_id") != "S17" or result.get("phase_id") != "S17-P1":
        raise RuntimeError("S17-P2 requires validated v0.1.4 S17-P1 evidence")
    if result.get("next_phase") != "S17-P2":
        raise RuntimeError("S17-P1 must route to S17-P2")
    progress = result.get("stage17_phase_progress", {})
    if progress.get("s17_p1_performed") is not True:
        raise RuntimeError("S17-P1 dependency must be completed")
    if progress.get("s17_p2_performed") is not False:
        raise RuntimeError("S17-P1 dependency must not already include S17-P2")
    if result.get("github_upload", {}).get("github_upload_performed") is not False:
        raise RuntimeError("v1.4 GitHub upload must remain deferred")
    if result.get("phase_boundaries", {}).get("notification_delivery_scope_included") is not False:
        raise RuntimeError("S17-P1 dependency must not include notification delivery")
    return result


def validate_legacy_s17_p2_artifacts() -> tuple[
    dict[str, Any],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    artifacts = build_default_notification_reminders(generated_at="2026-07-05T14:30:00+10:00")
    validate_notification_reminder_artifacts(*artifacts)
    return artifacts


def load_v14_taskpack_baseline() -> dict[str, Any]:
    taskpack_text = V14_TASKPACK_PATH.read_text(encoding="utf-8")
    roadmap_text = V14_ROADMAP_PATH.read_text(encoding="utf-8")
    for token in ("报告生成完成", "重大风险", "数据源缺失", "邮件只发提醒", "通知日志进入metadata"):
        if token not in roadmap_text:
            raise RuntimeError(f"v1.4 roadmap missing S17-P2 marker {token}")
    for token in ("不把缺数据报告伪装成完整报告", "不提交原始敏感数据到公开GitHub", "可审计"):
        if token not in taskpack_text:
            raise RuntimeError(f"v1.4 taskpack missing S17-P2 safety marker {token}")
    return {
        "taskpack_read": True,
        "roadmap_read": True,
        "roadmap_includes_s17_p2_requirements": True,
        "taskpack_includes_notification_safety_boundary": True,
        "source_refs": {
            "taskpack": V14_TASKPACK_PATH.as_posix(),
            "roadmap": V14_ROADMAP_PATH.as_posix(),
        },
    }


def _raw_boundary() -> dict[str, Any]:
    result: dict[str, Any] = {key: False for key in RAW_ACTION_KEYS}
    result.update(
        {
            "raw_inbox_read_required_by_this_phase": False,
            "raw_inbox_ref": RAW_INBOX_REF,
            "private_runtime_output_dir": "KMFA/.codex_private_runtime/",
        }
    )
    return result


def _public_repo_safety() -> dict[str, bool]:
    return {
        "protected_source_payload_committed": False,
        "compressed_raw_package_committed": False,
        "office_workbook_committed": False,
        "source_document_committed": False,
        "raw_or_private_table_committed": False,
        "local_database_committed": False,
        "auth_material_committed": False,
        "connector_auth_material_committed": False,
        "field_plaintext_committed": False,
        "source_header_plaintext_committed": False,
        "raw_file_names_committed": False,
        "raw_file_hashes_committed": False,
        "source_record_payload_committed": False,
        "normalized_source_values_committed": False,
        "business_numeric_payload_committed": False,
        "public_numeric_values_committed": False,
        "project_or_customer_plaintext_committed": False,
        "recipient_address_plaintext_committed": False,
        "bank_payload_committed": False,
        "contract_payroll_tax_material_committed": False,
        "full_report_notification_body_committed": False,
        "report_attachment_committed": False,
        "business_decision_basis_committed": False,
    }


def _quality_gate() -> dict[str, Any]:
    return {
        "notification_rules_complete": True,
        "notification_events_generated": True,
        "notification_logs_written_to_metadata": True,
        "email_reminder_only": True,
        "email_full_report_body_allowed": False,
        "email_attachment_allowed": False,
        "recipient_address_plaintext_allowed": False,
        "raw_payload_allowed": False,
        "external_email_connector_allowed": False,
        "real_notification_delivery_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "business_execution_allowed": False,
        "lineage_full_check_allowed": False,
        "s17_p3_scope_allowed": False,
        "stage17_review_allowed": False,
        "github_upload_allowed": False,
        "phase_completion_upload_allowed": False,
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "release_permission": "blocked",
        "release_block_reason": "s17_p2_is_local_metadata_notification_policy_only",
    }


def _phase_boundaries() -> dict[str, bool]:
    return {
        "s17_p1_dependency_reused": True,
        "legacy_s17_p2_public_safe_baseline_reused": True,
        "s17_p1_access_security_scope_included": False,
        "s17_p2_notification_scope_included": True,
        "s17_p3_scope_included": False,
        "stage17_review_scope_included": False,
        "github_upload_scope_included": False,
        "lineage_full_check_scope_included": False,
        "protected_source_matching_scope_included": False,
        "formal_report_runtime_scope_included": False,
        "live_ui_runtime_scope_included": False,
        "external_connector_scope_included": False,
        "app_reinstall_scope_included": False,
        "real_notification_delivery_scope_included": False,
        "full_report_email_body_scope_included": False,
        "notification_attachment_scope_included": False,
        "recipient_address_plaintext_scope_included": False,
        "business_execution_scope_included": False,
        "raw_inbox_access_scope_included": False,
    }


def _trigger_body_summary(trigger_type: str) -> str:
    summaries = {
        "report_generation_completed": "Public-safe reminder: report preview state is ready for in-app review.",
        "major_risk": "Public-safe reminder: high-risk blocker requires reviewer attention.",
        "data_source_missing": "Public-safe reminder: required source coverage needs operator follow-up.",
    }
    return summaries[trigger_type]


def _lock_notification_rules(legacy_rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in legacy_rules:
        trigger_type = str(row["trigger_type"])
        rows.append(
            {
                "record_type": "v014_s17_p2_notification_rule_lock",
                "project_id": "KMFA",
                "stage_id": "S17",
                "phase_id": "S17-P2",
                "policy_lock_version": POLICY_LOCK_VERSION,
                "rule_id": f"v014_s17p2_notification_rule_{trigger_type}",
                "trigger_type": trigger_type,
                "channel": "email_reminder",
                "recipient_role": row["recipient_role"],
                "priority": row["priority"],
                "subject_template_id": row["subject_template_id"],
                "body_template_id": row["body_template_id"],
                "body_summary_max_chars": row["body_summary_max_chars"],
                "metadata_log_required": True,
                "public_safe_template_only": True,
                "full_report_body_allowed": False,
                "report_attachment_allowed": False,
                "raw_payload_allowed": False,
                "recipient_address_plaintext_allowed": False,
                "external_connector_required": False,
                "real_delivery_allowed": False,
                "metadata_target": METADATA_RULES_PATH.as_posix(),
                "evidence_ref": RULE_LOCK_PATH.as_posix(),
            }
        )
    return rows


def _lock_notification_events(legacy_events: list[dict[str, Any]], generated_at: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in legacy_events:
        trigger_type = str(row["trigger_type"])
        rows.append(
            {
                "record_type": "v014_s17_p2_notification_event_log",
                "project_id": "KMFA",
                "stage_id": "S17",
                "phase_id": "S17-P2",
                "policy_lock_version": POLICY_LOCK_VERSION,
                "event_id": f"V014-S17P2-NOTIFICATION-EVENT-{trigger_type}",
                "event_time": generated_at,
                "trigger_type": trigger_type,
                "recipient_role": row["recipient_role"],
                "channel": "email_reminder",
                "append_only": True,
                "metadata_target": METADATA_EVENTS_PATH.as_posix(),
                "raw_business_data_included": False,
                "full_report_body_included": False,
                "report_attachment_included": False,
                "recipient_address_plaintext_included": False,
                "real_notification_delivery_performed": False,
                "external_connector_invoked": False,
                "evidence_ref": EVENT_LOG_PATH.as_posix(),
                "result_status": "metadata_event_logged_only",
            }
        )
    return rows


def _lock_dispatch_logs(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for event in events:
        trigger_type = str(event["trigger_type"])
        rows.append(
            {
                "record_type": "v014_s17_p2_notification_dispatch_log",
                "project_id": "KMFA",
                "stage_id": "S17",
                "phase_id": "S17-P2",
                "policy_lock_version": POLICY_LOCK_VERSION,
                "dispatch_log_id": f"V014-S17P2-NOTIFICATION-DISPATCH-{trigger_type}",
                "event_id": event["event_id"],
                "trigger_type": trigger_type,
                "recipient_role": event["recipient_role"],
                "recipient_address_ref": "role_ref_only",
                "channel": "email_reminder",
                "delivery_mode": "metadata_outbox_only",
                "delivery_status": "metadata_logged_only",
                "result_status": "metadata_logged_only",
                "body_summary": _trigger_body_summary(trigger_type),
                "full_report_body_included": False,
                "report_attachment_included": False,
                "raw_payload_included": False,
                "recipient_address_plaintext_included": False,
                "external_connector_invoked": False,
                "real_notification_delivery_performed": False,
                "append_only": True,
                "metadata_target": METADATA_DISPATCH_LOG_PATH.as_posix(),
                "evidence_ref": DISPATCH_LOG_PATH.as_posix(),
            }
        )
    return rows


def build_manifest(generated_at: str | None = None) -> tuple[
    dict[str, Any],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    generated_at = generated_at or datetime.now().isoformat(timespec="seconds")
    s17_p1 = validate_s17_p1_dependency()
    legacy_manifest, legacy_rules, legacy_events, legacy_logs = validate_legacy_s17_p2_artifacts()
    baseline = load_v14_taskpack_baseline()
    rule_locks = _lock_notification_rules(legacy_rules)
    event_logs = _lock_notification_events(legacy_events, generated_at)
    dispatch_logs = _lock_dispatch_logs(event_logs)

    trigger_types = {row["trigger_type"] for row in rule_locks}
    summary = {
        "notification_rule_count": len(rule_locks),
        "notification_event_count": len(event_logs),
        "notification_dispatch_log_count": len(dispatch_logs),
        "trigger_type_count": len(trigger_types),
        "required_trigger_count": len(REQUIRED_V014_NOTIFICATION_TRIGGERS),
        "metadata_outbox_log_count": len(dispatch_logs),
        "real_notification_delivery_count": 0,
        "full_report_email_body_count": 0,
        "report_attachment_count": 0,
        "recipient_address_plaintext_count": 0,
        "external_connector_count": 0,
        "formal_report_count": 0,
        "business_decision_basis_count": 0,
        "business_execution_count": 0,
        "raw_inbox_access_count": 0,
        "report_grade_visible": "D",
    }

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "v014_s17_p2_notification_policy_manifest",
        "project_id": "KMFA",
        "version": "0.1.4",
        "stage_id": "S17",
        "phase_id": "S17-P2",
        "phase_scope": PHASE_SCOPE,
        "task_id": TASK_ID,
        "acceptance_ids": [ACCEPTANCE_ID],
        "completed_task_ids": ["S17P2T01", "S17P2T02", "S17P2T03"],
        "status": "completed_validated_local_only_no_go_upload_deferred_notification_policy_locked",
        "generated_at": generated_at,
        "branch": git_output(["branch", "--show-current"]),
        "git_head": git_output(["rev-parse", "HEAD"]),
        "s17_p1_dependency_validated": True,
        "s17_p1_dependency_task_id": s17_p1["task_id"],
        "historical_s17_p2_public_safe_baseline_validated": True,
        "historical_s17_p2_policy_version": legacy_manifest["policy_version"],
        "v14_taskpack_baseline": baseline,
        "required_notification_triggers": list(REQUIRED_V014_NOTIFICATION_TRIGGERS),
        "stage17_phase_progress": {
            "completed_phase_count": 2,
            "total_phase_count": 3,
            "derived_percent_bps": 6667,
            "derived_percent_label": "66.67%",
            "s17_p1_performed": True,
            "s17_p2_performed": True,
            "s17_p3_performed": False,
            "stage17_review_performed": False,
        },
        "notification_policy_summary": summary,
        "quality_gate": _quality_gate(),
        "phase_boundaries": _phase_boundaries(),
        "raw_data_boundary": _raw_boundary(),
        "public_repo_safety": _public_repo_safety(),
        "github_upload": {
            "github_upload_performed": False,
            "github_upload_ready_next_gate": False,
            "github_upload_deferred_until_v014_stage1_18_complete": True,
            "github_upload_status": "not_uploaded_deferred_until_v014_stage1_18_complete",
        },
        "metadata_outputs": {
            "notification_manifest": METADATA_MANIFEST_PATH.as_posix(),
            "notification_rules": METADATA_RULES_PATH.as_posix(),
            "notification_events": METADATA_EVENTS_PATH.as_posix(),
            "notification_dispatch_log": METADATA_DISPATCH_LOG_PATH.as_posix(),
        },
        "artifact_refs": {
            "manifest": MANIFEST_PATH.as_posix(),
            "notification_rule_lock": RULE_LOCK_PATH.as_posix(),
            "notification_event_log": EVENT_LOG_PATH.as_posix(),
            "notification_dispatch_log": DISPATCH_LOG_PATH.as_posix(),
            "metadata_manifest": METADATA_MANIFEST_PATH.as_posix(),
            "metadata_rules": METADATA_RULES_PATH.as_posix(),
            "metadata_events": METADATA_EVENTS_PATH.as_posix(),
            "metadata_dispatch_log": METADATA_DISPATCH_LOG_PATH.as_posix(),
            "report": REPORT_PATH.as_posix(),
            "test_results": TEST_RESULTS_PATH.as_posix(),
            "risk_register": RISK_REGISTER_PATH.as_posix(),
            "rollback_plan": ROLLBACK_PATH.as_posix(),
        },
        "formula_id": FORMULA_ID,
        "mapping_version": MAPPING_VERSION,
        "next_phase": NEXT_PHASE,
        "next_required_step": NEXT_REQUIRED_STEP,
    }
    return manifest, rule_locks, event_logs, dispatch_logs


def write_artifacts(
    manifest: dict[str, Any],
    rule_locks: list[dict[str, Any]],
    event_logs: list[dict[str, Any]],
    dispatch_logs: list[dict[str, Any]],
) -> None:
    write_json(MANIFEST_PATH, manifest)
    write_jsonl(RULE_LOCK_PATH, rule_locks)
    write_jsonl(EVENT_LOG_PATH, event_logs)
    write_jsonl(DISPATCH_LOG_PATH, dispatch_logs)
    write_json(METADATA_MANIFEST_PATH, manifest)
    write_jsonl(METADATA_RULES_PATH, rule_locks)
    write_jsonl(METADATA_EVENTS_PATH, event_logs)
    write_jsonl(METADATA_DISPATCH_LOG_PATH, dispatch_logs)

    summary = manifest["notification_policy_summary"]
    write_text(
        REPORT_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 S17-P2 Notification Policy",
                "",
                f"- notification_rule_count: `{summary['notification_rule_count']}`",
                f"- notification_event_count: `{summary['notification_event_count']}`",
                f"- notification_dispatch_log_count: `{summary['notification_dispatch_log_count']}`",
                f"- metadata_outbox_log_count: `{summary['metadata_outbox_log_count']}`",
                f"- real_notification_delivery_count: `{summary['real_notification_delivery_count']}`",
                f"- full_report_email_body_count: `{summary['full_report_email_body_count']}`",
                f"- report_attachment_count: `{summary['report_attachment_count']}`",
                f"- recipient_address_plaintext_count: `{summary['recipient_address_plaintext_count']}`",
                f"- external_connector_count: `{summary['external_connector_count']}`",
                f"- raw_inbox_access_count: `{summary['raw_inbox_access_count']}`",
                f"- report_grade_visible: `{summary['report_grade_visible']}`",
                "- GitHub upload: `deferred_until_v014_stage1_18_complete`",
                "",
                "This phase is public-safe and local-only. It records reminder policy metadata for report-ready, risk, and missing-source triggers without delivery, connector use, address plaintext, attachments, raw inbox access, formal report release, or business execution.",
                "",
            ]
        ),
    )
    write_test_results_placeholder()
    write_text(
        RISK_REGISTER_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 S17-P2 Notification Policy Risk Register",
                "",
                "- risk: Reminder metadata could be mistaken for real message delivery.",
                "  mitigation: Delivery mode is metadata outbox only; delivery count stays zero.",
                "- risk: Reminder content could be mistaken for a formal report.",
                "  mitigation: The phase logs only short public-safe reminders and blocks report body, attachments, and decision basis.",
                "",
            ]
        ),
    )
    write_text(
        ROLLBACK_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 S17-P2 Notification Policy Rollback Plan",
                "",
                "- Remove only `KMFA/stage_artifacts/V014_S17_P2_NOTIFICATION_POLICY/` and `KMFA/metadata/notifications/v014_s17_p2_*` if rollback is required.",
                "- Remove paired v014 S17-P2 governance entries only after confirming no later phase depends on them.",
                "- Do not touch raw/private inbox contents.",
                "",
            ]
        ),
    )


def generate(generated_at: str | None = None) -> dict[str, Any]:
    manifest, rule_locks, event_logs, dispatch_logs = build_manifest(generated_at=generated_at)
    write_artifacts(manifest, rule_locks, event_logs, dispatch_logs)
    return manifest


def main() -> int:
    manifest = generate()
    summary = manifest["notification_policy_summary"]
    print(
        "PASS: KMFA v0.1.4 S17-P2 notification policy generated "
        f"(rules={summary['notification_rule_count']}, events={summary['notification_event_count']}, "
        f"dispatch_logs={summary['notification_dispatch_log_count']}, "
        f"delivery={summary['real_notification_delivery_count']}, "
        f"full_report_email_body={summary['full_report_email_body_count']}, "
        f"attachments={summary['report_attachment_count']}, "
        f"external_connector={summary['external_connector_count']}, "
        f"s17_p3={manifest['stage17_phase_progress']['s17_p3_performed']}, "
        f"github_upload={manifest['github_upload']['github_upload_performed']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
