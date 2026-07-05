#!/usr/bin/env python3
"""Validate KMFA v0.1.4 Stage 17 review evidence."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.check_v014_s17_p1_access_security import validate_v014_s17_p1_access_security  # noqa: E402
from KMFA.tools.check_v014_s17_p2_notification_policy import validate_v014_s17_p2_notification_policy  # noqa: E402
from KMFA.tools.check_v014_s17_p3_operations_sop import validate_v014_s17_p3_operations_sop  # noqa: E402
from KMFA.tools.v014_s17_stage_review import (  # noqa: E402
    ACCEPTANCE_ID,
    MANIFEST_PATH,
    NEXT_PHASE,
    NEXT_REQUIRED_STEP,
    REPORT_PATH,
    REVIEW_SCOPE,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
    SCHEMA_VERSION,
    TASK_ID,
    TEST_RESULTS_PATH,
    _public_repo_safety,
    _release_state,
    load_v14_taskpack_baseline,
)


PUBLIC_SAFETY_FALSE_KEYS = tuple(key for key, value in _public_repo_safety().items() if value is False)
RELEASE_FALSE_KEYS = tuple(
    key
    for key, value in _release_state().items()
    if isinstance(value, bool) and value is False
)
REQUIRED_HARD_BLOCKS = (
    "stage17_review_public_safe_only",
    "report_grade_d_only",
    "raw_data_mutation_forbidden",
    "raw_publication_forbidden",
    "field_header_plaintext_publication_forbidden",
    "formal_report_release_blocked",
    "business_decision_basis_blocked",
    "real_notification_delivery_blocked",
    "full_report_email_blocked",
    "report_attachment_blocked",
    "recipient_address_plaintext_blocked",
    "production_restore_blocked",
    "external_service_call_blocked",
    "live_connector_blocked",
    "app_reinstall_blocked",
    "s18_p1_not_performed",
    "lineage_full_check_not_performed",
    "protected_source_matching_not_performed",
    "github_upload_deferred_until_v014_stage1_18_complete",
    "business_execution_blocked",
)
FORBIDDEN_PUBLIC_TEXT = (
    "raw_value:",
    "normalized_value:",
    "source_header_text:",
    "original_filename",
    "member_sha256:",
    "actual_package_sha256",
    "authoritative_value_cents",
    "system_value_cents",
    "amount_cents:",
    "amount_yuan:",
    "sheet_name:",
    "row_value:",
    "cell_value:",
    "business_data:",
    "bank_statement_payload",
    "contract_full_text",
    "salary_detail",
    "tax_filing_material",
    "connector_" + "token:",
    "connector_" + "pass" + "word:",
    "api" + "_key:",
    "private" + "_key:",
    "credential_payload",
    "report_attachment_path",
    "production_restore_payload",
    "external_service_payload",
    "live_connector_payload",
    "app_reinstall_payload",
    "-----" "BEGIN",
    "s" "k-",
    "project_name_plaintext",
    "customer_name_plaintext",
    "counterparty_plaintext",
    "company_entity_plaintext",
    "supplier_name_plaintext",
    "payment_account",
    "account_number:",
    "invoice_number:",
    "tax_identifier:",
    "private_ref://",
    "recipient_" + "email",
    "smtp",
    "KMFA" "_MetaData",
    "/Users/linzezhang/Downloads",
    ".xlsx",
    ".xls",
    ".zip",
    ".pdf",
    ".sqlite",
    ".db",
)
STRICT_SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)(password|passwd|secret|api" + r"_key|token)\s*=\s*[^\s,;]{8,}"),
)


class ValidationError(Exception):
    pass


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ValidationError(f"missing JSON file: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValidationError(f"{path} must contain a JSON object")
    return value


def git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise ValidationError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def check_public_evidence_text(path: Path, errors: list[str]) -> None:
    require(path.exists(), f"missing public evidence: {path}", errors)
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8", errors="ignore")
    lower = text.lower()
    for forbidden in FORBIDDEN_PUBLIC_TEXT:
        require(forbidden.lower() not in lower, f"forbidden public evidence text {forbidden!r} in {path}", errors)
    for pattern in STRICT_SECRET_PATTERNS:
        require(pattern.search(text) is None, f"secret-like token found in {path}: {pattern.pattern}", errors)


def _expected_gate(p1: dict[str, Any], p2: dict[str, Any], p3: dict[str, Any]) -> dict[str, Any]:
    p1s = p1["access_security_summary"]
    p2s = p2["notification_policy_summary"]
    p3s = p3["operations_sop_summary"]
    return {
        "role_count": p1s["role_count"],
        "required_role_count": p1s["required_role_count"],
        "sensitive_policy_category_count": p1s["sensitive_policy_category_count"],
        "required_sensitive_category_count": p1s["required_sensitive_category_count"],
        "audit_action_type_count": p1s["audit_action_type_count"],
        "required_audit_action_type_count": p1s["required_audit_action_type_count"],
        "notification_rule_count": p2s["notification_rule_count"],
        "notification_event_count": p2s["notification_event_count"],
        "notification_dispatch_log_count": p2s["notification_dispatch_log_count"],
        "metadata_outbox_log_count": p2s["metadata_outbox_log_count"],
        "trigger_type_count": p2s["trigger_type_count"],
        "required_trigger_count": p2s["required_trigger_count"],
        "operation_runbook_count": p3s["operation_runbook_count"],
        "knowledge_item_count": p3s["knowledge_item_count"],
        "drill_log_count": p3s["drill_log_count"],
        "runbook_type_count": p3s["runbook_type_count"],
        "knowledge_item_type_count": p3s["knowledge_item_type_count"],
        "drill_type_count": p3s["drill_type_count"],
        "production_restore_count": p3s["production_restore_count"],
        "external_service_call_count": p3s["external_service_call_count"],
        "live_connector_call_count": p3s["live_connector_call_count"],
        "app_reinstall_count": p3s["app_reinstall_count"],
        "real_notification_delivery_count": p2s["real_notification_delivery_count"],
        "notification_delivery_count": p1s["notification_delivery_count"],
        "full_report_email_body_count": max(
            p1s["full_report_email_body_count"],
            p2s["full_report_email_body_count"],
        ),
        "report_attachment_count": p2s["report_attachment_count"],
        "recipient_address_plaintext_count": p2s["recipient_address_plaintext_count"],
        "formal_report_count": max(
            p1s["formal_report_count"],
            p2s["formal_report_count"],
            p3s["formal_report_count"],
        ),
        "business_decision_basis_count": max(
            p1s["business_decision_basis_count"],
            p2s["business_decision_basis_count"],
        ),
        "business_execution_count": max(
            p1s["business_execution_count"],
            p2s["business_execution_count"],
            p3s["business_execution_count"],
        ),
        "external_connector_count": max(
            p1s["external_connector_count"],
            p2s["external_connector_count"],
        ),
        "raw_inbox_access_count": max(
            p1s["raw_inbox_access_count"],
            p2s["raw_inbox_access_count"],
            p3s["raw_inbox_access_count"],
        ),
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "release_permission": "blocked",
    }


def validate_v014_s17_stage_review(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []
    manifest = read_json(manifest_path)
    p1 = validate_v014_s17_p1_access_security()
    p2 = validate_v014_s17_p2_notification_policy()
    p3 = validate_v014_s17_p3_operations_sop()
    baseline = load_v14_taskpack_baseline()

    require(manifest.get("schema_version") == SCHEMA_VERSION, "manifest schema mismatch", errors)
    require(manifest.get("project_id") == "KMFA", "project_id mismatch", errors)
    require(manifest.get("version") == "0.1.4", "version mismatch", errors)
    require(manifest.get("stage_id") == "S17", "stage_id must be S17", errors)
    require(manifest.get("phase_id") == "S17_STAGE_REVIEW", "phase_id mismatch", errors)
    require(manifest.get("review_scope") == REVIEW_SCOPE, "review_scope mismatch", errors)
    require(manifest.get("task_id") == TASK_ID, "task_id mismatch", errors)
    require(manifest.get("acceptance_ids") == [ACCEPTANCE_ID], "acceptance id mismatch", errors)
    require(
        manifest.get("completed_task_ids") == ["S17REVT01", "S17REVT02", "S17REVT03"],
        "completed task ids mismatch",
        errors,
    )
    require(
        manifest.get("status") == "review_passed_local_only_no_go_upload_deferred_until_v014_stage1_18_complete",
        "status mismatch",
        errors,
    )
    require(manifest.get("stage_review_performed") is True, "stage review flag must be true", errors)
    require(manifest.get("phase_results") == {"S17-P1": "PASS", "S17-P2": "PASS", "S17-P3": "PASS"}, "phase results mismatch", errors)

    progress = manifest.get("stage17_phase_progress", {})
    require(progress.get("completed_phase_count") == 3, "completed phase count mismatch", errors)
    require(progress.get("total_phase_count") == 3, "total phase count mismatch", errors)
    require(progress.get("derived_percent_bps") == 10000, "derived percent bps mismatch", errors)
    require(progress.get("derived_percent_label") == "100.00%", "derived percent label mismatch", errors)
    for key in ("s17_p1_performed", "s17_p2_performed", "s17_p3_performed", "stage17_review_performed"):
        require(progress.get(key) is True, f"{key} must be true", errors)

    expected_gate = _expected_gate(p1, p2, p3)
    gate = manifest.get("stage_gate", {})
    for key, expected in expected_gate.items():
        require(gate.get(key) == expected, f"stage_gate {key} must be {expected!r}", errors)

    findings = manifest.get("review_findings_summary", {})
    require(findings.get("open_finding_count") == 0, "open finding count must be zero", errors)
    require(findings.get("fixed_finding_count", 0) >= 1, "fixed finding count must be at least one", errors)

    release = manifest.get("release_state", {})
    for key in RELEASE_FALSE_KEYS:
        require(release.get(key) is False, f"release_state {key} must be false", errors)
    require(release.get("current_go_no_go") == "NO_GO", "go/no-go mismatch", errors)
    require(release.get("current_report_grade") == "D", "release report grade mismatch", errors)
    require(release.get("release_permission") == "blocked", "release permission mismatch", errors)

    raw = manifest.get("raw_data_boundary", {})
    for key in (
        "raw_inbox_read_by_this_review",
        "raw_inbox_listed_by_this_review",
        "raw_inbox_inventory_by_this_review",
        "raw_inbox_stat_by_this_review",
        "raw_inbox_hashed_by_this_review",
        "raw_inbox_modified_by_this_review",
        "raw_inbox_deleted_by_this_review",
        "raw_inbox_moved_by_this_review",
        "raw_inbox_renamed_by_this_review",
        "raw_inbox_overwritten_by_this_review",
        "raw_inbox_written_by_this_review",
        "raw_inbox_mutated_by_this_review",
        "raw_inbox_read_required_by_this_review",
    ):
        require(raw.get(key) is False, f"raw boundary {key} must be false", errors)
    require(raw.get("s17_p1_raw_inbox_all_false") is True, "S17-P1 raw boundary must be all false", errors)
    require(raw.get("s17_p2_raw_inbox_all_false") is True, "S17-P2 raw boundary must be all false", errors)
    require(raw.get("s17_p3_raw_inbox_all_false") is True, "S17-P3 raw boundary must be all false", errors)

    safety = manifest.get("public_repo_safety", {})
    for key in PUBLIC_SAFETY_FALSE_KEYS:
        require(safety.get(key) is False, f"public safety {key} must be false", errors)

    require(baseline.get("roadmap_includes_stage17_requirements") is True, "v1.4 roadmap baseline mismatch", errors)
    require(
        baseline.get("taskpack_includes_stage17_public_safe_safety_boundary") is True,
        "v1.4 taskpack baseline mismatch",
        errors,
    )
    for key in REQUIRED_HARD_BLOCKS:
        require(key in manifest.get("hard_blocks", []), f"missing hard block {key}", errors)
    require(manifest.get("s18_p1_performed") is False, "S18-P1 must not be performed", errors)
    require(manifest.get("github_upload_performed") is False, "GitHub upload must not be performed", errors)
    require(manifest.get("github_upload_ready_next_gate") is False, "GitHub upload ready gate must be false", errors)
    require(
        manifest.get("github_upload_deferred_until_v014_stage1_18_complete") is True,
        "GitHub upload deferred flag must be true",
        errors,
    )
    require(manifest.get("github_upload_status") == "not_uploaded_deferred_until_v014_stage1_18_complete", "upload status mismatch", errors)
    require(manifest.get("next_phase") == NEXT_PHASE, "next phase mismatch", errors)
    require(manifest.get("next_required_step") == NEXT_REQUIRED_STEP, "next required step mismatch", errors)

    require(re.match(r"^[0-9a-f]{40}$", str(manifest.get("git_head"))), "git head must be a full SHA", errors)
    require(manifest.get("branch") == git_output(["branch", "--show-current"]), "branch mismatch", errors)

    for path in (MANIFEST_PATH, REPORT_PATH, TEST_RESULTS_PATH, RISK_REGISTER_PATH, ROLLBACK_PATH):
        check_public_evidence_text(path, errors)

    if errors:
        raise ValidationError("; ".join(errors))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args()
    manifest = validate_v014_s17_stage_review(args.manifest)
    gate = manifest["stage_gate"]
    print(
        "PASS: KMFA v0.1.4 Stage 17 review validated "
        f"(phase_results={manifest['phase_results']}, open_findings={manifest['review_findings_summary']['open_finding_count']}, "
        f"roles={gate['role_count']}, notifications={gate['notification_rule_count']}, "
        f"runbooks={gate['operation_runbook_count']}, drills={gate['drill_log_count']}, "
        f"delivery={gate['real_notification_delivery_count']}, restore={gate['production_restore_count']}, "
        f"external={gate['external_service_call_count']}, app_reinstall={gate['app_reinstall_count']}, "
        f"s18={manifest['s18_p1_performed']}, github_upload={manifest['github_upload_performed']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
