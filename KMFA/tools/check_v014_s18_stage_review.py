#!/usr/bin/env python3
"""Validate KMFA v0.1.4 Stage 18 review evidence."""

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

from KMFA.tools.check_v014_s18_p1_precision_stress import validate_v014_s18_p1_precision_stress  # noqa: E402
from KMFA.tools.check_v014_s18_p2_full_regression_acceptance import validate_v014_s18_p2_full_regression_acceptance  # noqa: E402
from KMFA.tools.check_v014_s18_p3_integration_preparation import validate_v014_s18_p3_integration_preparation  # noqa: E402
from KMFA.tools.v014_s18_stage_review import (  # noqa: E402
    ACCEPTANCE_ID,
    GO_NO_GO_PATH,
    GO_NO_GO_RECORD_PATH,
    MANIFEST_PATH,
    METADATA_GO_NO_GO_PATH,
    METADATA_MANIFEST_PATH,
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
    key for key, value in _release_state().items() if isinstance(value, bool) and value is False
)
REQUIRED_HARD_BLOCKS = (
    "stage18_review_public_safe_only",
    "report_grade_d_only",
    "data_quality_q4_only",
    "raw_data_mutation_forbidden",
    "raw_publication_forbidden",
    "field_header_plaintext_publication_forbidden",
    "formal_report_release_blocked",
    "business_decision_basis_blocked",
    "production_restore_blocked",
    "external_service_call_blocked",
    "live_connector_blocked",
    "app_reinstall_blocked",
    "lineage_full_check_not_complete",
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
    "credential_material",
    "report_attachment_path",
    "production_restore_material",
    "external_service_material",
    "live_connector_material",
    "app_reinstall_material",
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


def _expected_stage_gate(p1: dict[str, Any], p2: dict[str, Any], p3: dict[str, Any]) -> dict[str, Any]:
    p1s = p1["precision_stress_summary"]
    p2s = p2["full_regression_summary"]
    p3s = p3["integration_preparation_summary"]
    return {
        "precision_scenario_count": p1s["scenario_count"],
        "precision_scenario_type_count": p1s["scenario_type_count"],
        "consecutive_import_run_count": p1s["consecutive_import_run_count"],
        "unique_import_result_hash_count": p1s["unique_import_result_hash_count"],
        "large_batch_file_count": p1s["large_batch_file_count"],
        "error_report_count": p1s["error_report_count"],
        "full_regression_check_category_count": p2s["check_category_count"],
        "stage_evidence_count": p2s["stage_evidence_count"],
        "html_audit_file_count": p2s["html_audit_file_count"],
        "html_audit_row_count": p2s["html_audit_row_count"],
        "html_audit_pass_count": p2s["html_audit_pass_count"],
        "html_audit_warn_count": p2s["html_audit_warn_count"],
        "html_audit_fail_count": p2s["html_audit_fail_count"],
        "connector_plan_count": p3s["connector_plan_count"],
        "read_only_connector_count": p3s["read_only_connector_count"],
        "opme_entry_surface_count": p3s["opme_entry_surface_count"],
        "next_stage_backlog_item_count": p3s["backlog_item_count"],
        "live_connector_call_count": p3s["live_connector_call_count"],
        "external_service_call_count": p3s["external_service_call_count"],
        "source_mutation_allowed_count": p3s["source_mutation_allowed_count"],
        "lineage_full_check_complete": False,
        "official_report_release_allowed": False,
        "pending_reconciliation_count": p2["quality_gate"]["s09_pending_reconciliation_count"],
        "current_go_no_go": "NO_GO",
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "release_permission": "blocked",
    }


def validate_v014_s18_stage_review(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []
    manifest = read_json(manifest_path)
    metadata_manifest = read_json(METADATA_MANIFEST_PATH)
    go_no_go = read_json(GO_NO_GO_PATH)
    metadata_go_no_go = read_json(METADATA_GO_NO_GO_PATH)
    p1 = validate_v014_s18_p1_precision_stress()
    p2 = validate_v014_s18_p2_full_regression_acceptance()
    p3 = validate_v014_s18_p3_integration_preparation()
    baseline = load_v14_taskpack_baseline()

    require(metadata_manifest == manifest, "metadata manifest copy must match machine manifest", errors)
    require(metadata_go_no_go == go_no_go, "metadata Go/No-Go copy must match machine Go/No-Go", errors)
    require(manifest.get("schema_version") == SCHEMA_VERSION, "manifest schema mismatch", errors)
    require(manifest.get("project_id") == "KMFA", "project_id mismatch", errors)
    require(manifest.get("version") == "0.1.4", "version mismatch", errors)
    require(manifest.get("stage_id") == "S18", "stage_id must be S18", errors)
    require(manifest.get("phase_id") == "S18_STAGE_REVIEW", "phase_id mismatch", errors)
    require(manifest.get("review_scope") == REVIEW_SCOPE, "review_scope mismatch", errors)
    require(manifest.get("task_id") == TASK_ID, "task_id mismatch", errors)
    require(manifest.get("acceptance_ids") == [ACCEPTANCE_ID], "acceptance id mismatch", errors)
    require(manifest.get("completed_task_ids") == ["S18REVT01", "S18REVT02", "S18REVT03"], "completed task ids mismatch", errors)
    require(
        manifest.get("status") == "review_passed_local_only_no_go_upload_deferred_until_v014_stage1_18_complete",
        "status mismatch",
        errors,
    )
    require(manifest.get("stage_review_performed") is True, "stage review flag must be true", errors)
    require(manifest.get("phase_results") == {"S18-P1": "PASS", "S18-P2": "PASS", "S18-P3": "PASS"}, "phase results mismatch", errors)
    require(p1.get("next_phase") == "S18-P2", "S18-P1 next phase mismatch", errors)
    require(p2.get("next_phase") == "S18-P3", "S18-P2 next phase mismatch", errors)
    require(p3.get("next_phase") == "S18_STAGE_REVIEW", "S18-P3 next phase mismatch", errors)

    progress = manifest.get("stage18_phase_progress", {})
    require(progress.get("completed_phase_count") == 3, "completed phase count mismatch", errors)
    require(progress.get("total_phase_count") == 3, "total phase count mismatch", errors)
    require(progress.get("derived_percent_bps") == 10000, "derived percent bps mismatch", errors)
    require(progress.get("derived_percent_label") == "100.00%", "derived percent label mismatch", errors)
    for key in ("s18_p1_performed", "s18_p2_performed", "s18_p3_performed", "stage18_review_performed"):
        require(progress.get(key) is True, f"{key} must be true", errors)

    expected_gate = _expected_stage_gate(p1, p2, p3)
    gate = manifest.get("stage_gate", {})
    for key, expected in expected_gate.items():
        require(gate.get(key) == expected, f"stage_gate {key} must be {expected!r}", errors)

    review_go_no_go = manifest.get("stage_review_go_no_go", {})
    require(review_go_no_go == go_no_go, "manifest Go/No-Go must match file", errors)
    require(go_no_go.get("decision") == "NO_GO", "Go/No-Go decision mismatch", errors)
    require(go_no_go.get("stage18_review_performed") is True, "stage review performed must be true", errors)
    require(go_no_go.get("lineage_full_check_complete") is False, "lineage full check must be false", errors)
    require(go_no_go.get("official_report_release_allowed") is False, "official report release must be false", errors)
    require(go_no_go.get("delivery_allowed") is False, "delivery must be false", errors)
    require(go_no_go.get("github_upload_allowed") is False, "GitHub upload allowed must be false", errors)
    require(go_no_go.get("github_upload_performed") is False, "GitHub upload performed must be false", errors)
    for blocker in (
        "LINEAGE_FULL_CHECK_NOT_COMPLETE",
        "OFFICIAL_REPORT_RELEASE_NOT_ALLOWED",
        "S09_PENDING_RECONCILIATION_12",
        "GITHUB_UPLOAD_DEFERRED_UNTIL_V014_STAGE1_18_COMPLETE",
    ):
        require(blocker in go_no_go.get("blocker_ids", []), f"missing blocker {blocker}", errors)
    for resolved in ("S18_P3_PENDING", "STAGE18_REVIEW_PENDING"):
        require(resolved in go_no_go.get("resolved_blocker_ids", []), f"missing resolved blocker {resolved}", errors)
        require(resolved not in go_no_go.get("blocker_ids", []), f"resolved blocker still active {resolved}", errors)
    require(go_no_go.get("next_required_phase") == NEXT_PHASE, "next required phase mismatch", errors)

    findings = manifest.get("review_findings_summary", {})
    require(findings.get("open_finding_count") == 0, "open finding count must be zero", errors)
    require(findings.get("fixed_finding_count", 0) >= 1, "fixed finding count must be at least one", errors)

    release = manifest.get("release_state", {})
    for key in RELEASE_FALSE_KEYS:
        require(release.get(key) is False, f"release_state {key} must be false", errors)
    require(release.get("current_go_no_go") == "NO_GO", "release Go/No-Go mismatch", errors)
    require(release.get("current_report_grade") == "D", "release report grade mismatch", errors)
    require(release.get("release_permission") == "blocked", "release permission mismatch", errors)

    raw = manifest.get("raw_data_boundary", {})
    for key in (
        "raw_inbox_read_required_by_this_review",
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
    ):
        require(raw.get(key) is False, f"raw boundary {key} must be false", errors)
    for key in ("s18_p1_raw_inbox_all_false", "s18_p2_raw_inbox_all_false", "s18_p3_raw_inbox_all_false"):
        require(raw.get(key) is True, f"raw boundary {key} must be true", errors)

    safety = manifest.get("public_repo_safety", {})
    for key in PUBLIC_SAFETY_FALSE_KEYS:
        require(safety.get(key) is False, f"public safety {key} must be false", errors)
    require(baseline == manifest.get("v14_taskpack_baseline"), "v1.4 taskpack baseline mismatch", errors)
    for key in REQUIRED_HARD_BLOCKS:
        require(key in manifest.get("hard_blocks", []), f"missing hard block {key}", errors)

    require(manifest.get("legacy_stage18_upload_artifacts_current_gate") is False, "legacy upload artifacts must not be current gate", errors)
    require(manifest.get("github_upload_performed") is False, "GitHub upload must be false", errors)
    require(manifest.get("github_upload_ready_next_gate") is False, "GitHub upload ready must be false", errors)
    require(
        manifest.get("github_upload_deferred_until_v014_stage1_18_complete") is True,
        "GitHub upload deferred flag must be true",
        errors,
    )
    require(manifest.get("github_upload_status") == "not_uploaded_deferred_until_v014_stage1_18_complete", "upload status mismatch", errors)
    require(manifest.get("next_phase") == NEXT_PHASE, "next phase mismatch", errors)
    require(manifest.get("next_required_step") == NEXT_REQUIRED_STEP, "next required step mismatch", errors)
    require(not Path("KMFA/stage_artifacts/V014_S18_GITHUB_UPLOAD").exists(), "v0.1.4 Stage 18 upload evidence must not exist", errors)
    require(re.match(r"^[0-9a-f]{40}$", str(manifest.get("git_head"))), "git head must be a full SHA", errors)
    require(manifest.get("branch") == git_output(["branch", "--show-current"]), "branch mismatch", errors)

    for path in (
        MANIFEST_PATH,
        GO_NO_GO_PATH,
        REPORT_PATH,
        GO_NO_GO_RECORD_PATH,
        TEST_RESULTS_PATH,
        RISK_REGISTER_PATH,
        ROLLBACK_PATH,
    ):
        check_public_evidence_text(path, errors)

    if errors:
        raise ValidationError("; ".join(errors))
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args(argv)
    manifest = validate_v014_s18_stage_review(args.manifest)
    gate = manifest["stage_gate"]
    print(
        "PASS: KMFA v0.1.4 Stage 18 review validated "
        f"(phase_results={manifest['phase_results']}, open_findings={manifest['review_findings_summary']['open_finding_count']}, "
        f"checks={gate['full_regression_check_category_count']}, stages={gate['stage_evidence_count']}, "
        f"connectors={gate['connector_plan_count']}, opme_surfaces={gate['opme_entry_surface_count']}, "
        f"backlog={gate['next_stage_backlog_item_count']}, go_no_go={gate['current_go_no_go']}, "
        f"github_upload={manifest['github_upload_performed']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
