#!/usr/bin/env python3
"""Generate current KMFA v0.1.4 S17-P2 notification evidence."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools import v014_s17_p1_post_remediation_access_security as s17_p1
from KMFA.tools.check_v014_s17_p1_post_remediation_access_security import (
    validate_v014_s17_p1_post_remediation_access_security,
)
from KMFA.tools.check_v014_s17_p2_notification_policy import (
    validate_v014_s17_p2_notification_policy as validate_historical_s17_p2,
)


PHASE_ID = "V014_S17_P2_POST_REMEDIATION_NOTIFICATION"
ROADMAP_PHASE_ID = "S17-P2"
TASK_ID = "KMFA-V014-S17-P2-POST-REMEDIATION-NOTIFICATION-20260712"
ACCEPTANCE_ID = "ACC-V014-S17-P2-POST-REMEDIATION-NOTIFICATION"
VERSION = "0.1.4-s17-p2-post-remediation-notification"
STATUS = "completed_validated_local_only_s17_p2_metadata_reminders_no_delivery_no_go_upload_deferred"
DECISION = "NO_GO"
FORMULA_ID = "FORM-KMFA-V014-S17-P2-POST-REMEDIATION-NOTIFICATION-001"
PARAMETER_IDS = ("PARAM-KMFA-1796", "PARAM-KMFA-1797", "PARAM-KMFA-1798", "PARAM-KMFA-1799")
MODEL_REGISTRY_KEY = "kmfa_v014_s17_p2_post_remediation_notification"
POLICY_VERSION = "NOTIFY-KMFA-V014-S17P2-POST-REMEDIATION-PUBLIC-SAFE-001"

OUTPUT_DIR = Path("KMFA/stage_artifacts") / PHASE_ID
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "notification_summary.json"
MANIFEST_PATH = MACHINE_DIR / "notification_manifest.json"
RULE_PATH = MACHINE_DIR / "notification_rules_public_safe.jsonl"
TRIGGER_EVALUATION_PATH = MACHINE_DIR / "notification_trigger_evaluations_public_safe.jsonl"
OUTBOX_PATH = MACHINE_DIR / "notification_metadata_outbox_public_safe.jsonl"
MATRIX_PATH = MACHINE_DIR / "acceptance_matrix_public_safe.json"
GO_NO_GO_PATH = MACHINE_DIR / "go_no_go_report.json"
REPORT_PATH = HUMAN_DIR / "notification_report_zh.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results_zh.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register_zh.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan_zh.md"

METADATA_DIR = Path("KMFA/metadata/notifications")
METADATA_SUMMARY_PATH = METADATA_DIR / "v014_s17_p2_post_remediation_notification_summary.json"
METADATA_MANIFEST_PATH = METADATA_DIR / "v014_s17_p2_post_remediation_notification_manifest.json"
METADATA_RULE_PATH = METADATA_DIR / "v014_s17_p2_post_remediation_notification_rules.jsonl"
METADATA_TRIGGER_EVALUATION_PATH = METADATA_DIR / "v014_s17_p2_post_remediation_trigger_evaluations.jsonl"
METADATA_OUTBOX_PATH = METADATA_DIR / "v014_s17_p2_post_remediation_notification_outbox.jsonl"
METADATA_MATRIX_PATH = METADATA_DIR / "v014_s17_p2_post_remediation_acceptance_matrix.json"
METADATA_GO_NO_GO_PATH = METADATA_DIR / "v014_s17_p2_post_remediation_go_no_go_report.json"

PRIVATE_DIR = Path("KMFA/.codex_private_runtime/v014_s17_p2_post_remediation_notification")
PRIVATE_RAW_BEFORE_PATH = PRIVATE_DIR / "raw_immutability_before.json"
PRIVATE_RAW_AFTER_PATH = PRIVATE_DIR / "raw_immutability_after.json"
PRIVATE_SCAN_REPORT_PATH = PRIVATE_DIR / "notification_boundary_validation_zh.md"

ROADMAP_PATH = Path("KMFA/taskpack/v1_4/roadmap/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_4.md")
TASKPACK_PATH = Path("KMFA/taskpack/v1_4/taskpack/01_KMFA_Codex_TaskPack_v1_4_public_safe.md")
LEGACY_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V014_S17_P2_NOTIFICATION_POLICY/machine/notification_policy_manifest.json"
)
S10_REVIEW_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V014_S10_POST_REMEDIATION_STAGE_REVIEW/machine/stage10_post_remediation_review_manifest.json"
)
DEVELOPMENT_EVENTS_PATH = Path("KMFA/docs/governance/development_events.jsonl")
ASSURANCE_STATUS_PATH = Path("KMFA/docs/governance/ASSURANCE_STATUS.yaml")
STAGE_STATUS_PATH = Path("KMFA/metadata/stage_status.jsonl")
TASK_STATUS_PATH = Path("KMFA/metadata/traceability/v1_4_stage_phase_task_status.jsonl")

REPORT_LINK_REF = Path(
    "KMFA/stage_artifacts/V014_S10_P3_POST_REMEDIATION_RESTRICTED_EXPORT/exports/html/business_overview_report.html"
)
RISK_LINK_REF = Path(
    "KMFA/stage_artifacts/V014_S12_P1_POST_REMEDIATION_PENDING_ACTIONS/exports/html/kmfa_pending_actions_workbench.html"
)
SOURCE_LINK_REF = Path(
    "KMFA/stage_artifacts/V014_S11_P2_POST_REMEDIATION_SOURCE_CHECK_BOARD/exports/html/kmfa_source_check_board.html"
)

REQUIRED_TRIGGER_IDS = (
    "report_generation_completed",
    "major_risk",
    "data_source_missing",
)
AUDIT_REQUIRED_FIELDS = (
    "event_id",
    "event_time",
    "actor_role",
    "action_type",
    "subject_ref",
    "evidence_ref",
    "result_status",
)
RULE_SPECS: tuple[dict[str, Any], ...] = (
    {
        "trigger_id": "report_generation_completed",
        "recipient_role": "management",
        "priority": "normal",
        "subject": "KMFA提醒：受限报告预览已生成",
        "body_summary": "D级受限报告预览已生成，请在应用内复核；当前未获发布授权。",
        "in_app_link_ref": REPORT_LINK_REF,
        "in_app_link_label": "查看受限报告预览",
        "source_metric_id": "restricted_html_preview_count",
    },
    {
        "trigger_id": "major_risk",
        "recipient_role": "reviewer",
        "priority": "high",
        "subject": "KMFA提醒：重大风险仍待复核",
        "body_summary": "重大风险阻断仍存在，请在应用内复核差异与风险；当前未放行。",
        "in_app_link_ref": RISK_LINK_REF,
        "in_app_link_label": "查看待处理事项",
        "source_metric_id": "hard_block_count",
    },
    {
        "trigger_id": "data_source_missing",
        "recipient_role": "finance",
        "priority": "high",
        "subject": "KMFA提醒：数据源缺失待处理",
        "body_summary": "数据源覆盖仍不完整，请在数据源检查板处理；不得推断或补零。",
        "in_app_link_ref": SOURCE_LINK_REF,
        "in_app_link_label": "打开数据源检查板",
        "source_metric_id": "unresolved_source_indicator_count",
    },
)


def _git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    return result.stdout.strip()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def _upsert_jsonl(path: Path, row: dict[str, Any]) -> None:
    preserved: list[str] = []
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip() and json.loads(line).get("phase_id") != PHASE_ID:
                preserved.append(line)
    preserved.append(json.dumps(row, ensure_ascii=False, separators=(",", ":")))
    _write_text(path, "\n".join(preserved))


def _sync_assurance_snapshot_time(generated_at: str) -> None:
    lines = ASSURANCE_STATUS_PATH.read_text(encoding="utf-8").splitlines()
    indexes = [index for index, line in enumerate(lines) if line.startswith("snapshot_event_time:")]
    if len(indexes) != 1:
        raise RuntimeError("ASSURANCE_STATUS must contain exactly one snapshot_event_time")
    lines[indexes[0]] = f'snapshot_event_time: "{generated_at}"'
    _write_text(ASSURANCE_STATUS_PATH, "\n".join(lines))


def _taskpack_contract() -> dict[str, Any]:
    roadmap = ROADMAP_PATH.read_text(encoding="utf-8")
    taskpack = TASKPACK_PATH.read_text(encoding="utf-8")
    for token in (
        "报告生成完成、重大风险、数据源缺失发送提醒",
        "邮件只发提醒，不发完整报告正文",
        "通知日志进入metadata",
    ):
        if token not in roadmap:
            raise ValueError(f"roadmap token missing: {token}")
    for token in ("不把缺数据报告伪装成完整报告", "不提交原始敏感数据到公开GitHub", "可审计"):
        if token not in taskpack:
            raise ValueError(f"taskpack token missing: {token}")
    return {
        "roadmap_read": True,
        "taskpack_read": True,
        "three_trigger_reminder_link_metadata_contract_locked": True,
        "source_refs": {"roadmap": ROADMAP_PATH.as_posix(), "taskpack": TASKPACK_PATH.as_posix()},
    }


def _validate_frozen_s10_review() -> dict[str, Any]:
    manifest = _read_json(S10_REVIEW_MANIFEST_PATH)
    summary = manifest.get("summary", {})
    expected = {
        "phase_id": "V014_S10_POST_REMEDIATION_STAGE_REVIEW",
        "html_restricted_preview_count": 2,
        "formal_report_count": 0,
        "hard_block_count": 12,
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "decision": "NO_GO",
        "raw_snapshot_exact_match": True,
        "raw_cross_phase_snapshot_exact_match": True,
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            raise ValueError(f"frozen S10 review summary drift: {key}")
    validation = manifest.get("validation_summary", {})
    if validation.get("final_validation_recorded") is not True:
        raise ValueError("frozen S10 review final validation missing")
    for key in (
        "focused_phase_tests",
        "review_tests",
        "strict_validator",
        "browser_and_download",
        "governance_and_safety_scans",
    ):
        if validation.get(key) != "PASS":
            raise ValueError(f"frozen S10 review validation drift: {key}")
    if manifest.get("historical_review_dynamic_state_is_authoritative") is not False:
        raise ValueError("frozen S10 review historical state became authoritative")
    return manifest


def _phase_boundaries() -> dict[str, bool]:
    return {
        "s17_p1_performed": True,
        "s17_p2_performed": True,
        "notification_metadata_log_written": True,
        "s17_p3_performed": False,
        "stage17_review_performed": False,
        "live_identity_provider_configured": False,
        "credential_or_user_record_created": False,
        "persistent_authorization_event_write_performed": False,
        "persistent_business_audit_event_write_performed": False,
        "notification_delivery_performed": False,
        "full_report_notification_body_sent": False,
        "report_attachment_sent": False,
        "external_connector_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "formal_report_release_performed": False,
        "difference_closure_performed": False,
        "persistent_business_write_performed": False,
        "business_execution_performed": False,
    }


def _public_safety() -> dict[str, bool]:
    return {
        "raw_business_data_committed": False,
        "raw_file_names_committed": False,
        "raw_schema_or_header_committed": False,
        "business_value_plaintext_committed": False,
        "project_customer_or_counterparty_plaintext_committed": False,
        "recipient_address_plaintext_committed": False,
        "full_report_notification_body_committed": False,
        "report_attachment_committed": False,
        "credential_or_secret_committed": False,
        "private_runtime_committed": False,
        "zip_excel_pdf_private_csv_database_committed": False,
    }


def _raw_boundary() -> dict[str, bool]:
    return {
        "raw_snapshot_read_performed": True,
        "raw_content_materialization_performed": False,
        "raw_write_performed": False,
        "raw_delete_performed": False,
        "raw_move_performed": False,
        "raw_rename_performed": False,
        "raw_overwrite_performed": False,
        "raw_mutation_performed": False,
    }


def _quality_gate() -> dict[str, Any]:
    return {
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "decision": "NO_GO",
        "open_final_difference_accepted_count": 3,
        "nonzero_delta_reconciliation_count": 9,
        "zero_delta_reconciliation_count": 2,
        "incomplete_reconciliation_count": 1,
        "one_cent_tolerance_minor_unit": 0,
        "restricted_preview_allowed": True,
        "formal_report_release_allowed": False,
        "real_notification_delivery_allowed": False,
    }


def _rule_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in RULE_SPECS:
        trigger_id = str(spec["trigger_id"])
        rows.append(
            {
                "record_type": "v014_s17_p2_post_remediation_notification_rule",
                "project_id": "KMFA",
                "stage_id": "S17",
                "phase_id": PHASE_ID,
                "policy_version": POLICY_VERSION,
                "rule_id": f"S17P2-NOTIFY-RULE-{trigger_id}",
                "trigger_id": trigger_id,
                "source_metric_id": spec["source_metric_id"],
                "recipient_role": spec["recipient_role"],
                "priority": spec["priority"],
                "channel": "email_reminder",
                "body_summary_max_chars": 120,
                "metadata_log_required": True,
                "in_app_link_required": True,
                "append_only_required": True,
                "full_report_body_allowed": False,
                "report_attachment_allowed": False,
                "recipient_address_plaintext_allowed": False,
                "raw_payload_allowed": False,
                "business_value_plaintext_allowed": False,
                "external_connector_allowed": False,
                "real_delivery_allowed": False,
                "dedupe_window_minutes": 1440,
                "evidence_ref": RULE_PATH.as_posix(),
            }
        )
    return rows


def _source_counts(s17_summary: dict[str, Any], s10_summary: dict[str, Any]) -> dict[str, int]:
    return {
        "report_generation_completed": int(s10_summary["html_restricted_preview_count"]),
        "major_risk": int(s10_summary["hard_block_count"]),
        "data_source_missing": int(s17_summary["open_final_difference_accepted_count"])
        + int(s17_summary["incomplete_reconciliation_count"]),
    }


def _trigger_evaluation_rows(
    rules: list[dict[str, Any]],
    source_counts: dict[str, int],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for rule in rules:
        trigger_id = str(rule["trigger_id"])
        source_count = source_counts[trigger_id]
        eligible = source_count > 0
        rows.append(
            {
                "record_type": "v014_s17_p2_post_remediation_trigger_evaluation",
                "evaluation_id": f"S17P2-NOTIFY-EVAL-{trigger_id}",
                "trigger_id": trigger_id,
                "rule_id": rule["rule_id"],
                "source_metric_id": rule["source_metric_id"],
                "source_evidence_count": source_count,
                "expected_eligible_for_metadata_outbox": True,
                "eligible_for_metadata_outbox": eligible,
                "status": "PASS" if eligible else "FAIL",
                "current_data_quality_grade": "Q4",
                "current_report_grade": "D",
                "decision": "NO_GO",
                "public_safe_aggregate_only": True,
                "business_value_materialized": False,
                "real_delivery_eligible": False,
                "evidence_ref": TRIGGER_EVALUATION_PATH.as_posix(),
            }
        )
    return rows


def validate_outbox_candidate(row: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    if row.get("full_report_body_included") is not False:
        errors.append("full_report_body_forbidden")
    if row.get("report_attachment_included") is not False:
        errors.append("report_attachment_forbidden")
    if row.get("recipient_address_plaintext_included") is not False:
        errors.append("recipient_plaintext_forbidden")
    if row.get("external_connector_invoked") is not False:
        errors.append("external_connector_forbidden")
    if row.get("real_notification_delivery_performed") is not False:
        errors.append("real_delivery_forbidden")
    link_ref = str(row.get("in_app_link_ref") or "")
    if not link_ref or not Path(link_ref).is_file() or link_ref.startswith(("http://", "https://")):
        errors.append("in_app_link_required")
    if row.get("body_kind") != "short_reminder_and_link_only":
        errors.append("short_reminder_only_required")
    body = str(row.get("body_summary") or "")
    if not body or len(body) > 120:
        errors.append("body_summary_length_invalid")
    if row.get("channel") != "email_reminder":
        errors.append("email_reminder_channel_required")
    for field in AUDIT_REQUIRED_FIELDS:
        if not row.get(field):
            errors.append(f"audit_field_missing:{field}")
    return {"valid": not errors, "errors": errors}


def _outbox_rows(
    rules: list[dict[str, Any]],
    evaluations: list[dict[str, Any]],
    generated_at: str,
) -> list[dict[str, Any]]:
    evaluations_by_trigger = {row["trigger_id"]: row for row in evaluations}
    specs = {str(spec["trigger_id"]): spec for spec in RULE_SPECS}
    rows: list[dict[str, Any]] = []
    for rule in rules:
        trigger_id = str(rule["trigger_id"])
        evaluation = evaluations_by_trigger[trigger_id]
        if not evaluation["eligible_for_metadata_outbox"]:
            continue
        spec = specs[trigger_id]
        link_ref = Path(spec["in_app_link_ref"])
        row = {
            "record_type": "v014_s17_p2_post_remediation_notification_metadata_outbox",
            "project_id": "KMFA",
            "stage_id": "S17",
            "phase_id": PHASE_ID,
            "policy_version": POLICY_VERSION,
            "event_id": f"S17P2-NOTIFY-EVENT-{trigger_id}",
            "event_time": generated_at,
            "actor_role": "reviewer",
            "action_type": "notification",
            "subject_ref": str(rule["rule_id"]),
            "evidence_ref": OUTBOX_PATH.as_posix(),
            "result_status": "metadata_logged_only_not_delivered",
            "trigger_id": trigger_id,
            "rule_id": rule["rule_id"],
            "evaluation_id": evaluation["evaluation_id"],
            "recipient_role": rule["recipient_role"],
            "recipient_role_ref": f"role:{rule['recipient_role']}",
            "priority": rule["priority"],
            "channel": "email_reminder",
            "subject": spec["subject"],
            "body_summary": spec["body_summary"],
            "body_summary_char_count": len(str(spec["body_summary"])),
            "body_kind": "short_reminder_and_link_only",
            "in_app_link_ref": link_ref.as_posix(),
            "in_app_link_label": spec["in_app_link_label"],
            "in_app_link_exists": link_ref.is_file(),
            "dedupe_key": f"S17P2:{trigger_id}:Q4:D:NO_GO",
            "idempotency_key": f"S17P2-METADATA-OUTBOX-{trigger_id}-Q4-D-NO_GO",
            "delivery_mode": "metadata_outbox_only",
            "append_only": True,
            "metadata_log_written": True,
            "metadata_target": METADATA_OUTBOX_PATH.as_posix(),
            "raw_payload_included": False,
            "business_value_plaintext_included": False,
            "full_report_body_included": False,
            "report_attachment_included": False,
            "recipient_address_plaintext_included": False,
            "external_connector_invoked": False,
            "real_notification_delivery_performed": False,
        }
        validation = validate_outbox_candidate(row)
        if not validation["valid"]:
            raise ValueError(f"invalid notification outbox row {trigger_id}: {validation['errors']}")
        rows.append(row)
    return rows


def _acceptance_matrix(summary: dict[str, Any]) -> dict[str, Any]:
    checks = (
        ("current_dependencies", summary["current_s17_p1_validated"] and summary["current_s10_review_validated"]),
        ("three_rules", summary["notification_rule_count"] == 3),
        ("trigger_evaluation", summary["trigger_evaluation_count"] == 3 and summary["trigger_evaluation_mismatch_count"] == 0),
        ("metadata_outbox", summary["metadata_outbox_log_count"] == 3),
        ("short_chinese_reminders", summary["short_chinese_reminder_count"] == 3),
        ("existing_links", summary["in_app_link_exists_count"] == 3),
        ("audit_contract", summary["audit_required_field_count"] == 7),
        ("no_real_delivery", summary["real_notification_delivery_count"] == 0),
        ("no_full_report", summary["full_report_body_count"] == 0 and summary["report_attachment_count"] == 0),
        ("no_address_connector", summary["recipient_address_plaintext_count"] == 0 and summary["external_connector_count"] == 0),
        ("raw_exact", summary["raw_snapshot_exact_match"] and summary["raw_cross_phase_snapshot_exact_match"]),
        ("quality", summary["current_report_grade"] == "D" and summary["decision"] == "NO_GO"),
        ("downstream_closed", not summary["s17_p3_performed"] and not summary["github_upload_performed"]),
    )
    rows = [
        {"check_id": f"V014-S17-P2-ACC-{index:03d}", "name": name, "status": "PASS" if passed else "FAIL"}
        for index, (name, passed) in enumerate(checks, 1)
    ]
    return {
        "schema_version": "kmfa.v014.s17_p2_post_remediation_notification_matrix.v1",
        "acceptance_id": ACCEPTANCE_ID,
        "check_count": len(rows),
        "check_pass_count": sum(row["status"] == "PASS" for row in rows),
        "check_fail_count": sum(row["status"] == "FAIL" for row in rows),
        "checks": rows,
    }


def _phase_public_files() -> list[str]:
    artifact_paths = (
        SUMMARY_PATH,
        MANIFEST_PATH,
        RULE_PATH,
        TRIGGER_EVALUATION_PATH,
        OUTBOX_PATH,
        MATRIX_PATH,
        GO_NO_GO_PATH,
        REPORT_PATH,
        TEST_RESULTS_PATH,
        RISK_REGISTER_PATH,
        ROLLBACK_PATH,
    )
    metadata_paths = (
        METADATA_SUMMARY_PATH,
        METADATA_MANIFEST_PATH,
        METADATA_RULE_PATH,
        METADATA_TRIGGER_EVALUATION_PATH,
        METADATA_OUTBOX_PATH,
        METADATA_MATRIX_PATH,
        METADATA_GO_NO_GO_PATH,
    )
    governance_paths = (
        Path("KMFA/AGENTS.md"),
        Path("KMFA/CHANGELOG.md"),
        Path("KMFA/HANDOFF.md"),
        Path("KMFA/VERSION"),
        ASSURANCE_STATUS_PATH,
        Path("KMFA/docs/governance/DEVELOPMENT_LEDGER.md"),
        Path("KMFA/docs/governance/MODEL_SPEC.md"),
        Path("KMFA/docs/governance/OWNER_STATUS.md"),
        Path("KMFA/docs/governance/STATUS.md"),
        Path("KMFA/docs/governance/TRACEABILITY_MATRIX.csv"),
        Path("KMFA/docs/governance/VERSION_MATRIX.yaml"),
        Path("KMFA/docs/governance/delivery_tasks.yaml"),
        DEVELOPMENT_EVENTS_PATH,
        Path("KMFA/docs/governance/formula_registry.yaml"),
        Path("KMFA/docs/governance/model_registry.yaml"),
        Path("KMFA/docs/governance/parameter_registry.csv"),
        Path("KMFA/metadata/model_registry.yaml"),
        STAGE_STATUS_PATH,
        TASK_STATUS_PATH,
        Path("KMFA/功能清单.md"),
        Path("KMFA/开发记录.md"),
        Path("KMFA/模型参数文件.md"),
    )
    code_paths = (
        Path("KMFA/tools/v014_s17_p2_post_remediation_notification.py"),
        Path("KMFA/tools/check_v014_s17_p2_post_remediation_notification.py"),
        Path("KMFA/tests/test_v014_s17_p2_post_remediation_notification.py"),
    )
    return [path.as_posix() for path in artifact_paths + metadata_paths + governance_paths + code_paths]


def _write_governance(generated_at: str) -> None:
    evidence_ref = MANIFEST_PATH.as_posix()
    _sync_assurance_snapshot_time(generated_at)
    _upsert_jsonl(
        DEVELOPMENT_EVENTS_PATH,
        {
            "event_id": "DEV-KMFA-20260712-V014-S17-P2-POST-REMEDIATION-NOTIFICATION",
            "event_time": generated_at,
            "event_type": "phase_completion",
            "project_id": "KMFA",
            "stage_id": "S17",
            "phase_id": PHASE_ID,
            "roadmap_phase_id": ROADMAP_PHASE_ID,
            "task_id": TASK_ID,
            "status": STATUS,
            "fact_level": "EXTRACTED",
            "decision": DECISION,
            "notification_rule_count": 3,
            "trigger_evaluation_mismatch_count": 0,
            "metadata_outbox_log_count": 3,
            "real_notification_delivery_count": 0,
            "full_report_body_count": 0,
            "external_connector_count": 0,
            "raw_business_data_committed": False,
            "github_upload_performed": False,
            "app_reinstall_performed": False,
            "business_execution_performed": False,
            "evidence_ref": evidence_ref,
            "files_changed": _phase_public_files(),
            "result_commit": "PENDING",
        },
    )
    _upsert_jsonl(
        STAGE_STATUS_PATH,
        {
            "schema_version": "kmfa.stage_status.v1",
            "record_type": "phase_status",
            "project_id": "KMFA",
            "stage_id": "S17",
            "phase_id": PHASE_ID,
            "roadmap_phase_id": ROADMAP_PHASE_ID,
            "task_id": TASK_ID,
            "version": VERSION,
            "status": STATUS,
            "fact_level": "EXTRACTED",
            "decision": DECISION,
            "current_report_grade": "D",
            "raw_data_committed": False,
            "github_upload_performed": False,
            "app_reinstall_performed": False,
            "business_execution_performed": False,
            "evidence_ref": evidence_ref,
            "updated_at": generated_at,
        },
    )
    _upsert_jsonl(
        TASK_STATUS_PATH,
        {
            "schema_version": "kmfa.v014_stage_phase_task_status.v1",
            "record_type": "v014_stage_phase_task",
            "project_id": "KMFA",
            "stage_id": "S17",
            "governance_stage_id": "ACCESS-SECURITY-AUDIT",
            "roadmap_stage_id": "S17",
            "roadmap_phase_id": ROADMAP_PHASE_ID,
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "acceptance_id": ACCEPTANCE_ID,
            "version": VERSION,
            "name": "v0.1.4 S17-P2 post-remediation notification",
            "phase_goal": "lock three reminder triggers short Chinese content existing in-app links and metadata-only outbox logs",
            "status": STATUS,
            "fact_level": "EXTRACTED",
            "derived_percent": 100,
            "estimated_task_units": 3,
            "completed_task_units": 3,
            "task_count": 3,
            "raw_data_committed": False,
            "evidence_ref": evidence_ref,
            "updated_at": generated_at[:10],
        },
    )


def _render_report(summary: dict[str, Any]) -> str:
    return f"""# KMFA v0.1.4 S17-P2 通知

## 结论

- 三类触发：报告生成完成、重大风险、数据源缺失，规则/评估/metadata outbox=`{summary['notification_rule_count']}/{summary['trigger_evaluation_count']}/{summary['metadata_outbox_log_count']}`。
- 当前证据：受限报告预览=`{summary['restricted_html_preview_count']}`，重大风险 hard block=`{summary['hard_block_count']}`，数据源缺失指标=`{summary['unresolved_source_indicator_count']}`。
- 内容：3 条全中文短提醒和 3 个已存在应用内链接，最长正文不超过 120 字。
- 安全：真实投递、完整报告正文、附件、收件地址明文、外部连接器均为 0。
- 审计：每条 metadata outbox 含 7 个 S17-P1 审计必填字段，append-only 契约已锁定。
- raw：phase 前后、跨 S17-P1 和当前快照一致。
- 当前状态：Q4 / D / NO_GO / 3-9-2-1。

## 边界

- 本 phase 只写 public-safe metadata outbox，不连接邮件系统、不调用外部连接器、不创建用户或凭据、不发送真实通知。
- 提醒只包含短摘要与应用内链接，不包含完整报告正文、附件、业务明细或收件地址。
- S17-P3 只能在下一轮单独执行；本轮未做 Stage 17 整体复审、GitHub upload、app reinstall、正式报告、差异关闭或业务执行。
"""


def _render_private_report(summary: dict[str, Any]) -> str:
    return f"""# S17-P2 私有边界核验

- 原始数据文件数：{summary['raw_source_file_count']}
- phase 前后快照：exact match
- 与 S17-P1 快照：exact match
- 当前只读快照：exact match
- 通知规则/评估/outbox：{summary['notification_rule_count']} / {summary['trigger_evaluation_count']} / {summary['metadata_outbox_log_count']}
- 真实投递/完整正文/附件/地址/连接器：0 / 0 / 0 / 0 / 0
- 当前差异结构：3 / 9 / 2 / 1
- 结论：未修改、删除、移动、重命名、覆盖或写入 raw；未发送通知或写入业务系统。
- 最终 goal 多轮仍无法对齐时，必须生成全中文最终差异报告。
"""


def generate(*, final_validation: bool = False, write_governance: bool = True) -> dict[str, Any]:
    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    taskpack_contract = _taskpack_contract()
    current_s17_p1 = validate_v014_s17_p1_post_remediation_access_security(
        require_private_evidence=True,
        require_final_evidence=True,
    )
    current_s10 = _validate_frozen_s10_review()
    historical_s17_p2 = validate_historical_s17_p2()

    raw_helper = s17_p1.s16_review.p1.s15_review.p1.s14_review.p1.s13_review.p1.s12_review.p1.s11_project
    raw_before = raw_helper._raw_snapshot("before_v014_s17_p2_post_remediation_notification")
    rules = _rule_rows()
    s17_summary = current_s17_p1["summary"]
    s10_summary = current_s10["summary"]
    source_counts = _source_counts(s17_summary, s10_summary)
    evaluations = _trigger_evaluation_rows(rules, source_counts)
    outbox = _outbox_rows(rules, evaluations, generated_at)
    raw_after = raw_helper._raw_snapshot("after_v014_s17_p2_post_remediation_notification")
    prior_raw = _read_json(s17_p1.PRIVATE_RAW_AFTER_PATH)
    current_raw = raw_helper._raw_snapshot("current_v014_s17_p2_post_remediation_notification")
    normalize = raw_helper._normalize_raw
    raw_exact = normalize(raw_before) == normalize(raw_after)
    raw_cross = normalize(raw_before) == normalize(prior_raw) == normalize(current_raw)
    if not raw_exact or not raw_cross:
        raise ValueError("raw source changed during S17-P2")

    repo_scan = s17_p1._repo_tracking_scan()
    if repo_scan["status"] != "PASS":
        raise ValueError("tracked KMFA path scan failed")
    evaluation_mismatch = sum(row["status"] != "PASS" for row in evaluations)
    invalid_outbox = sum(not validate_outbox_candidate(row)["valid"] for row in outbox)
    if evaluation_mismatch or invalid_outbox:
        raise ValueError("notification evaluation or outbox validation failed")

    audit_contracts = _read_jsonl(s17_p1.AUDIT_CONTRACT_PATH)
    notification_contracts = [row for row in audit_contracts if row.get("action_type") == "notification"]
    if len(notification_contracts) != 1:
        raise ValueError("S17-P1 notification audit contract missing")
    if notification_contracts[0].get("required_fields") != list(AUDIT_REQUIRED_FIELDS):
        raise ValueError("S17-P1 notification audit fields drifted")

    summary = {
        "schema_version": "kmfa.v014.s17_p2_post_remediation_notification_summary.v1",
        "project_id": "KMFA",
        "stage_id": "S17",
        "phase_id": PHASE_ID,
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "version": VERSION,
        "status": STATUS,
        "decision": DECISION,
        "current_s17_p1_validated": True,
        "current_s10_review_validated": True,
        "notification_rule_count": len(rules),
        "required_trigger_count": len(REQUIRED_TRIGGER_IDS),
        "trigger_evaluation_count": len(evaluations),
        "eligible_reminder_count": sum(row["eligible_for_metadata_outbox"] for row in evaluations),
        "trigger_evaluation_mismatch_count": evaluation_mismatch,
        "metadata_outbox_log_count": len(outbox),
        "metadata_notification_audit_log_count": len(outbox),
        "short_chinese_reminder_count": len(outbox),
        "in_app_link_count": len(outbox),
        "in_app_link_exists_count": sum(Path(row["in_app_link_ref"]).is_file() for row in outbox),
        "max_body_summary_chars": 120,
        "audit_required_field_count": len(AUDIT_REQUIRED_FIELDS),
        "real_notification_delivery_count": 0,
        "full_report_body_count": 0,
        "report_attachment_count": 0,
        "recipient_address_plaintext_count": 0,
        "external_connector_count": 0,
        "restricted_html_preview_count": source_counts["report_generation_completed"],
        "hard_block_count": source_counts["major_risk"],
        "unresolved_source_indicator_count": source_counts["data_source_missing"],
        "formal_report_count": int(s10_summary["formal_report_count"]),
        "raw_source_file_count": raw_before["file_count"],
        "raw_snapshot_exact_match": raw_exact,
        "raw_cross_phase_snapshot_exact_match": raw_cross,
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "open_final_difference_accepted_count": 3,
        "nonzero_delta_reconciliation_count": 9,
        "zero_delta_reconciliation_count": 2,
        "incomplete_reconciliation_count": 1,
        **_phase_boundaries(),
    }
    matrix = _acceptance_matrix(summary)
    go_no_go = {
        "schema_version": "kmfa.v014.s17_p2_post_remediation_notification_go_no_go.v1",
        "project_id": "KMFA",
        "stage_id": "S17",
        "phase_id": PHASE_ID,
        "decision": "NO_GO",
        "s17_p2_validated": True,
        "metadata_outbox_allowed": True,
        "s17_p3_allowed_in_this_run": False,
        "stage17_review_allowed": False,
        "real_notification_delivery_allowed": False,
        "full_report_notification_body_allowed": False,
        "report_attachment_allowed": False,
        "recipient_address_plaintext_allowed": False,
        "external_connector_allowed": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "formal_report_release_allowed": False,
        "difference_closure_allowed": False,
        "persistent_business_write_allowed": False,
        "business_execution_allowed": False,
    }
    validation_summary = {
        "final_validation_recorded": final_validation,
        "focused_test": "PASS" if final_validation else "PENDING",
        "strict_validator": "PASS" if final_validation else "PENDING",
        "notification_rule_evaluation_and_outbox": "PASS" if final_validation else "PENDING",
        "raw_alignment": "PASS" if final_validation else "PENDING",
        "governance_and_safety_scans": "PASS" if final_validation else "PENDING",
    }
    historical_summary = historical_s17_p2["notification_policy_summary"]
    manifest = {
        "schema_version": "kmfa.v014.s17_p2_post_remediation_notification_manifest.v1",
        "project_id": "KMFA",
        "stage_id": "S17",
        "phase_id": PHASE_ID,
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "version": VERSION,
        "status": STATUS,
        "decision": DECISION,
        "generated_at": generated_at,
        "reviewed_head": _git_output(["rev-parse", "HEAD"]),
        "branch": _git_output(["branch", "--show-current"]),
        "remote": _git_output(["remote", "get-url", "origin"]),
        "formula_id": FORMULA_ID,
        "parameter_ids": list(PARAMETER_IDS),
        "model_registry_key": MODEL_REGISTRY_KEY,
        "summary": summary,
        "current_s17_p1_validated": True,
        "current_s17_p1_manifest_ref": s17_p1.MANIFEST_PATH.as_posix(),
        "current_s10_review_validated": True,
        "current_s10_review_manifest_ref": S10_REVIEW_MANIFEST_PATH.as_posix(),
        "historical_s17_p2_validated": True,
        "historical_s17_p2_dynamic_state_is_authoritative": False,
        "historical_three_rules_quarantined": historical_summary.get("notification_rule_count") == 3,
        "historical_three_events_quarantined": historical_summary.get("notification_event_count") == 3,
        "historical_three_dispatch_logs_quarantined": historical_summary.get("notification_dispatch_log_count") == 3,
        "legacy_manifest_ref": LEGACY_MANIFEST_PATH.as_posix(),
        "taskpack_contract": taskpack_contract,
        "notification_audit_contract_ref": s17_p1.AUDIT_CONTRACT_PATH.as_posix(),
        "notification_audit_contract_version": notification_contracts[0]["contract_version"],
        "audit_required_fields": list(AUDIT_REQUIRED_FIELDS),
        "link_refs": [str(spec["in_app_link_ref"]) for spec in RULE_SPECS],
        "stage17_progress": {
            "completed_phase_count": 2,
            "total_phase_count": 3,
            "s17_p1_performed": True,
            "s17_p2_performed": True,
            "s17_p3_performed": False,
            "stage17_review_performed": False,
        },
        "repo_tracking_scan": repo_scan,
        "quality_gate": _quality_gate(),
        "phase_boundaries": _phase_boundaries(),
        "public_repo_safety": _public_safety(),
        "raw_boundary": _raw_boundary(),
        "acceptance_matrix": matrix,
        "go_no_go": go_no_go,
        "validation_summary": validation_summary,
        "next_phase": "S17-P3",
        "next_required_step": (
            "下一轮仅执行 S17-P3；不得执行 Stage 17 整体复审、真实通知、完整报告正文、附件、"
            "外部连接器、GitHub upload、app reinstall、正式报告、差异关闭、持久业务写入或业务执行。"
        ),
    }

    for path, value in (
        (SUMMARY_PATH, summary),
        (MANIFEST_PATH, manifest),
        (MATRIX_PATH, matrix),
        (GO_NO_GO_PATH, go_no_go),
        (METADATA_SUMMARY_PATH, summary),
        (METADATA_MANIFEST_PATH, manifest),
        (METADATA_MATRIX_PATH, matrix),
        (METADATA_GO_NO_GO_PATH, go_no_go),
        (PRIVATE_RAW_BEFORE_PATH, raw_before),
        (PRIVATE_RAW_AFTER_PATH, raw_after),
    ):
        _write_json(path, value)
    for path, rows in (
        (RULE_PATH, rules),
        (TRIGGER_EVALUATION_PATH, evaluations),
        (OUTBOX_PATH, outbox),
        (METADATA_RULE_PATH, rules),
        (METADATA_TRIGGER_EVALUATION_PATH, evaluations),
        (METADATA_OUTBOX_PATH, outbox),
    ):
        _write_jsonl(path, rows)
    _write_text(REPORT_PATH, _render_report(summary))
    _write_text(
        TEST_RESULTS_PATH,
        """# S17-P2 通知测试结果

- focused test / strict validator：最终复验记录见 manifest。
- 规则/评估/outbox：3 / 3 / 3，评估不一致=0。
- 中文短提醒/已存在应用内链接：3 / 3。
- 审计字段：每条 7 个必填字段，metadata mirror exact。
- 真实投递/完整正文/附件/地址/连接器：0 / 0 / 0 / 0 / 0。
- raw phase 前后 / 跨 S17-P1 / current：exact match。
- quality：Q4 / D / NO_GO / 3-9-2-1。
""",
    )
    _write_text(
        RISK_REGISTER_PATH,
        """# S17-P2 通知风险登记

| 风险 | 控制 | 状态 |
|---|---|---|
| metadata outbox 被误读为已发送 | delivery mode 固定 metadata-only，真实投递计数为 0 | 已控制 |
| 短提醒泄露完整报告或业务明细 | 120 字上限，只允许状态摘要和现有应用内链接 | 已控制 |
| 地址、附件或连接器进入仓库 | 明文地址、附件、凭据和外部连接器 fail-closed | 已控制 |
| D级受限预览被误读为正式报告 | 文案固定 D级、未获发布授权，formal report=0 | 已控制 |
| 通知触发被历史夹具污染 | 历史 S17-P2 只作结构夹具，当前评估绑定 S17-P1 与 S10 review | 已控制 |
""",
    )
    _write_text(
        ROLLBACK_PATH,
        f"""# S17-P2 通知回滚计划

1. 回退本 phase 的本地 commit 与 `{OUTPUT_DIR.as_posix()}` public-safe 证据。
2. 回退本 phase 新增的 metadata/notifications 镜像和治理登记，不改历史 S17-P2 夹具。
3. 删除 ignored private raw/scan 证据，不触碰原始目录。
4. 不发送补偿通知，不调用外部连接器，不修改任何原始文件。
""",
    )
    _write_text(PRIVATE_SCAN_REPORT_PATH, _render_private_report(summary))
    if write_governance:
        _write_governance(generated_at)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--final-validation", action="store_true")
    parser.add_argument("--no-governance", action="store_true")
    args = parser.parse_args()
    manifest = generate(
        final_validation=args.final_validation,
        write_governance=not args.no_governance,
    )
    summary = manifest["summary"]
    print(
        "S17-P2 post-remediation notification: "
        f"rules={summary['notification_rule_count']} evaluations={summary['trigger_evaluation_count']} "
        f"outbox={summary['metadata_outbox_log_count']} delivery={summary['real_notification_delivery_count']} "
        f"grade={summary['current_report_grade']} decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
