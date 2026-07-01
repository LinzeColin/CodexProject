#!/usr/bin/env python3
"""Validate KMFA Stage 17 review evidence and gates."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


DEFAULT_REVIEW_MANIFEST = Path("KMFA/stage_artifacts/S17_STAGE_REVIEW/machine/stage17_review_manifest.json")
DEFAULT_P1_MANIFEST = Path("KMFA/stage_artifacts/S17_P1_access_security/machine/s17_p1_manifest.json")
DEFAULT_P2_MANIFEST = Path("KMFA/stage_artifacts/S17_P2_notification/machine/s17_p2_manifest.json")
DEFAULT_P3_MANIFEST = Path("KMFA/stage_artifacts/S17_P3_operations_sop/machine/s17_p3_manifest.json")

DEFAULT_ROLE_MATRIX = Path("KMFA/metadata/security/role_permission_matrix.jsonl")
DEFAULT_SENSITIVE_POLICY = Path("KMFA/metadata/security/public_repo_sensitive_data_policy.jsonl")
DEFAULT_AUDIT_POLICY = Path("KMFA/metadata/security/audit_log_policy.jsonl")
DEFAULT_NOTIFICATION_RULES = Path("KMFA/metadata/notifications/notification_rules.jsonl")
DEFAULT_NOTIFICATION_EVENTS = Path("KMFA/metadata/notifications/notification_events.jsonl")
DEFAULT_NOTIFICATION_DISPATCH_LOG = Path("KMFA/metadata/notifications/notification_dispatch_log.jsonl")
DEFAULT_OPERATION_RUNBOOKS = Path("KMFA/metadata/operations/operations_runbooks.jsonl")
DEFAULT_KNOWLEDGE_INDEX = Path("KMFA/metadata/operations/finance_sop_knowledge_index.jsonl")
DEFAULT_DRILL_LOG = Path("KMFA/metadata/operations/error_backup_drill_log.jsonl")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def fail(message: str) -> None:
    raise ValueError(message)


def require_equal(label: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        fail(f"{label}: expected {expected!r}, got {actual!r}")


def require_true(label: str, actual: Any) -> None:
    if actual is not True:
        fail(f"{label}: expected true, got {actual!r}")


def require_false(label: str, actual: Any) -> None:
    if actual is not False:
        fail(f"{label}: expected false, got {actual!r}")


def require_false_flags(label: str, payload: dict[str, Any], keys: tuple[str, ...]) -> None:
    for key in keys:
        require_false(f"{label}.{key}", payload.get(key))


def require_public_safety(label: str, payload: dict[str, Any]) -> None:
    public_safety = payload.get("public_repo_safety")
    if not isinstance(public_safety, dict):
        fail(f"{label}.public_repo_safety: expected object")
    for key, value in public_safety.items():
        require_false(f"{label}.public_repo_safety.{key}", value)


def require_phase_status(stage_phase_status: Any, phase: str) -> None:
    if not isinstance(stage_phase_status, dict):
        fail("stage_phase_status: expected object")
    status = stage_phase_status.get(phase)
    if not isinstance(status, str) or not status.startswith("completed_validated_local_only"):
        fail(f"stage_phase_status.{phase}: expected completed_validated_local_only*, got {status!r}")


def require_existing_refs(refs: Any) -> None:
    if not isinstance(refs, list) or not refs:
        fail("evidence_refs: expected non-empty list")
    for ref in refs:
        if not isinstance(ref, str):
            fail(f"evidence_refs: expected string ref, got {ref!r}")
        if not Path(ref).exists():
            fail(f"missing evidence ref: {ref}")


def validate_stage_review(
    review_manifest_path: Path = DEFAULT_REVIEW_MANIFEST,
    p1_manifest_path: Path = DEFAULT_P1_MANIFEST,
    p2_manifest_path: Path = DEFAULT_P2_MANIFEST,
    p3_manifest_path: Path = DEFAULT_P3_MANIFEST,
) -> dict[str, int]:
    required_paths = [
        review_manifest_path,
        p1_manifest_path,
        p2_manifest_path,
        p3_manifest_path,
        DEFAULT_ROLE_MATRIX,
        DEFAULT_SENSITIVE_POLICY,
        DEFAULT_AUDIT_POLICY,
        DEFAULT_NOTIFICATION_RULES,
        DEFAULT_NOTIFICATION_EVENTS,
        DEFAULT_NOTIFICATION_DISPATCH_LOG,
        DEFAULT_OPERATION_RUNBOOKS,
        DEFAULT_KNOWLEDGE_INDEX,
        DEFAULT_DRILL_LOG,
        Path("KMFA/stage_artifacts/S17_STAGE_REVIEW/human/stage17_review_report.md"),
        Path("KMFA/stage_artifacts/S17_STAGE_REVIEW/human/test_results.md"),
    ]
    missing = [str(path) for path in required_paths if not path.exists()]
    if missing:
        fail("missing required evidence paths: " + ", ".join(missing))

    forbidden_upload_paths = [
        Path("KMFA/stage_artifacts/S17_STAGE_REVIEW/human/github_upload_record.md"),
        Path("KMFA/stage_artifacts/S17_STAGE_REVIEW/machine/stage17_upload_manifest.json"),
    ]
    unexpected = [str(path) for path in forbidden_upload_paths if path.exists()]
    if unexpected:
        fail("Stage 17 review must not contain upload evidence: " + ", ".join(unexpected))

    review_manifest = read_json(review_manifest_path)
    p1_manifest = read_json(p1_manifest_path)
    p2_manifest = read_json(p2_manifest_path)
    p3_manifest = read_json(p3_manifest_path)

    role_matrix = read_jsonl(DEFAULT_ROLE_MATRIX)
    sensitive_policy = read_jsonl(DEFAULT_SENSITIVE_POLICY)
    audit_policy = read_jsonl(DEFAULT_AUDIT_POLICY)
    notification_rules = read_jsonl(DEFAULT_NOTIFICATION_RULES)
    notification_events = read_jsonl(DEFAULT_NOTIFICATION_EVENTS)
    notification_dispatch_log = read_jsonl(DEFAULT_NOTIFICATION_DISPATCH_LOG)
    operation_runbooks = read_jsonl(DEFAULT_OPERATION_RUNBOOKS)
    knowledge_index = read_jsonl(DEFAULT_KNOWLEDGE_INDEX)
    drill_log = read_jsonl(DEFAULT_DRILL_LOG)

    require_equal("stage", review_manifest.get("stage"), "S17")
    require_equal("status", review_manifest.get("status"), "review_passed_upload_ready_local_only")
    require_equal("github_upload_status", review_manifest.get("github_upload_status"), "not_pushed")
    require_true("upload_allowed_after_review", review_manifest.get("upload_allowed_after_review"))
    require_false("github_upload_performed", review_manifest.get("github_upload_performed"))
    require_false("s18_allowed", review_manifest.get("s18_allowed"))
    require_false("lineage_full_check_performed", review_manifest.get("lineage_full_check_performed"))
    require_false("formal_report_generated", review_manifest.get("formal_report_generated"))
    require_false("external_connector_included", review_manifest.get("external_connector_included"))
    require_false("full_report_email_allowed", review_manifest.get("full_report_email_allowed"))
    require_false("report_attachment_allowed", review_manifest.get("report_attachment_allowed"))
    require_false("recipient_plaintext_allowed", review_manifest.get("recipient_plaintext_allowed"))
    require_false("live_connector_allowed", review_manifest.get("live_connector_allowed"))
    require_false("production_restore_allowed", review_manifest.get("production_restore_allowed"))
    require_false("business_decision_basis_allowed", review_manifest.get("business_decision_basis_allowed"))
    require_false("business_execution_allowed", review_manifest.get("business_execution_allowed"))
    require_false("payment_execution_allowed", review_manifest.get("payment_execution_allowed"))
    require_false("bank_operation_allowed", review_manifest.get("bank_operation_allowed"))
    require_false("invoice_issuance_allowed", review_manifest.get("invoice_issuance_allowed"))
    require_false("legal_collection_decision_allowed", review_manifest.get("legal_collection_decision_allowed"))
    require_false("salary_action_allowed", review_manifest.get("salary_action_allowed"))
    require_false("tax_formal_action_allowed", review_manifest.get("tax_formal_action_allowed"))
    require_equal("report_grade_visible", review_manifest.get("report_grade_visible"), "D")
    require_equal("pending_reconciliation_count", review_manifest.get("pending_reconciliation_count"), 12)
    require_equal("next_gate_id", review_manifest.get("next_gate_id"), "KMFA-S17-GITHUB-UPLOAD-GATE")
    require_equal("open_review_finding_count", review_manifest.get("open_review_finding_count"), 0)
    require_public_safety("review", review_manifest)

    for phase in ("S17-P1", "S17-P2", "S17-P3"):
        require_phase_status(review_manifest.get("stage_phase_status"), phase)
    require_existing_refs(review_manifest.get("evidence_refs"))

    require_equal("p1.stage_phase", p1_manifest.get("stage_phase"), "S17-P1")
    require_equal("p1.summary.role_count", p1_manifest.get("summary", {}).get("role_count"), 4)
    require_equal("p1.summary.sensitive_policy_category_count", p1_manifest.get("summary", {}).get("sensitive_policy_category_count"), 15)
    require_equal("p1.summary.audit_action_type_count", p1_manifest.get("summary", {}).get("audit_action_type_count"), 5)
    require_true("p1.quality_gate.role_permission_matrix_complete", p1_manifest.get("quality_gate", {}).get("role_permission_matrix_complete"))
    require_true("p1.quality_gate.sensitive_public_repo_policy_enforced", p1_manifest.get("quality_gate", {}).get("sensitive_public_repo_policy_enforced"))
    require_true("p1.quality_gate.audit_log_policy_complete", p1_manifest.get("quality_gate", {}).get("audit_log_policy_complete"))
    require_false_flags(
        "p1.quality_gate",
        p1_manifest.get("quality_gate", {}),
        (
            "notification_delivery_allowed",
            "notification_full_report_body_allowed",
            "raw_sensitive_public_repo_allowed",
            "business_execution_allowed",
            "external_connector_allowed",
            "formal_report_allowed",
            "lineage_full_check_allowed",
            "stage17_review_allowed",
            "github_upload_allowed",
        ),
    )
    require_public_safety("p1", p1_manifest)

    require_equal("p2.stage_phase", p2_manifest.get("stage_phase"), "S17-P2")
    require_equal("p2.summary.notification_rule_count", p2_manifest.get("summary", {}).get("notification_rule_count"), 3)
    require_equal("p2.summary.notification_event_count", p2_manifest.get("summary", {}).get("notification_event_count"), 3)
    require_equal(
        "p2.summary.notification_dispatch_log_count",
        p2_manifest.get("summary", {}).get("notification_dispatch_log_count"),
        3,
    )
    require_true("p2.quality_gate.email_reminder_only", p2_manifest.get("quality_gate", {}).get("email_reminder_only"))
    require_true(
        "p2.quality_gate.notification_logs_written_to_metadata",
        p2_manifest.get("quality_gate", {}).get("notification_logs_written_to_metadata"),
    )
    require_false_flags(
        "p2.quality_gate",
        p2_manifest.get("quality_gate", {}),
        (
            "email_full_report_body_allowed",
            "email_attachment_allowed",
            "recipient_address_plaintext_allowed",
            "external_email_connector_allowed",
            "raw_payload_allowed",
            "business_execution_allowed",
            "formal_report_allowed",
            "lineage_full_check_allowed",
            "stage17_review_allowed",
            "github_upload_allowed",
        ),
    )
    require_public_safety("p2", p2_manifest)

    require_equal("p3.stage_phase", p3_manifest.get("stage_phase"), "S17-P3")
    require_equal("p3.summary.operation_runbook_count", p3_manifest.get("summary", {}).get("operation_runbook_count"), 4)
    require_equal("p3.summary.knowledge_item_count", p3_manifest.get("summary", {}).get("knowledge_item_count"), 2)
    require_equal("p3.summary.drill_log_count", p3_manifest.get("summary", {}).get("drill_log_count"), 2)
    require_true("p3.quality_gate.metadata_only", p3_manifest.get("quality_gate", {}).get("metadata_only"))
    require_true("p3.quality_gate.manual_execution_only", p3_manifest.get("quality_gate", {}).get("manual_execution_only"))
    require_true("p3.quality_gate.operation_runbooks_complete", p3_manifest.get("quality_gate", {}).get("operation_runbooks_complete"))
    require_true("p3.quality_gate.finance_sop_indexed", p3_manifest.get("quality_gate", {}).get("finance_sop_indexed"))
    require_true("p3.quality_gate.handoff_materials_indexed", p3_manifest.get("quality_gate", {}).get("handoff_materials_indexed"))
    require_true("p3.quality_gate.error_handling_drill_recorded", p3_manifest.get("quality_gate", {}).get("error_handling_drill_recorded"))
    require_true("p3.quality_gate.backup_recovery_drill_recorded", p3_manifest.get("quality_gate", {}).get("backup_recovery_drill_recorded"))
    require_false_flags(
        "p3.quality_gate",
        p3_manifest.get("quality_gate", {}),
        (
            "live_connector_allowed",
            "external_service_call_allowed",
            "production_restore_allowed",
            "full_report_email_allowed",
            "automatic_payment_allowed",
            "bank_operation_allowed",
            "invoice_issue_allowed",
            "legal_collection_allowed",
            "salary_action_allowed",
            "tax_formal_action_allowed",
            "business_execution_allowed",
            "formal_report_allowed",
            "lineage_full_check_allowed",
            "stage17_review_allowed",
            "github_upload_allowed",
        ),
    )
    require_public_safety("p3", p3_manifest)

    counts = review_manifest.get("review_counts", {})
    expected_counts = {
        "role_count": len(role_matrix),
        "sensitive_policy_category_count": len(sensitive_policy),
        "audit_action_type_count": len(audit_policy),
        "notification_rule_count": len(notification_rules),
        "notification_event_count": len(notification_events),
        "notification_dispatch_log_count": len(notification_dispatch_log),
        "operation_runbook_count": len(operation_runbooks),
        "knowledge_item_count": len(knowledge_index),
        "drill_log_count": len(drill_log),
        "pending_reconciliation_count": 12,
        "full_report_email_count": 0,
        "report_attachment_count": 0,
        "recipient_plaintext_count": 0,
        "live_connector_count": 0,
        "production_restore_count": 0,
        "business_execution_count": 0,
        "formal_report_count": 0,
        "lineage_full_check_count": 0,
        "github_upload_count": 0,
        "s18_scope_count": 0,
        "full_kmfa_unit_tests": 246,
    }
    for key, expected in expected_counts.items():
        require_equal(f"review_counts.{key}", counts.get(key), expected)

    return {key: int(value) for key, value in expected_counts.items()}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA Stage 17 review evidence.")
    parser.add_argument("--review-manifest", type=Path, default=DEFAULT_REVIEW_MANIFEST)
    args = parser.parse_args(argv)
    try:
        counts = validate_stage_review(args.review_manifest)
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(
        "PASS: KMFA Stage 17 review check passed "
        f"(roles={counts['role_count']}, notification_rules={counts['notification_rule_count']}, "
        f"runbooks={counts['operation_runbook_count']}, knowledge_items={counts['knowledge_item_count']}, "
        f"drill_logs={counts['drill_log_count']}, github_upload={counts['github_upload_count']}, "
        f"full_tests={counts['full_kmfa_unit_tests']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
