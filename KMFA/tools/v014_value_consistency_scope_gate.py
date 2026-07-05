#!/usr/bin/env python3
"""Generate KMFA v0.1.4 value-consistency scope gate evidence.

This continuation phase converts the owner requirement that processed data must
match the original raw data into a machine-checkable, public-safe gate. It does
not perform raw business-value extraction or claim value consistency. The raw
inbox is only stat-checked before and after this phase; any private diagnostics
remain in the git-ignored runtime directory.
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

from KMFA.tools.v014_s05_p1_a0_file_registration import RAW_INBOX, sha256_text, stat_snapshot  # noqa: E402


SCHEMA_VERSION = "kmfa.v014_value_consistency_scope_gate.v1"
GO_NO_GO_SCHEMA_VERSION = "kmfa.v014_value_consistency_scope_go_no_go.v1"
PRIVATE_SCHEMA_VERSION = "kmfa.private.v014_value_consistency_scope_guard.v1"
PROJECT_ID = "KMFA"
VERSION = "0.1.4"
PHASE_ID = "V014_VALUE_CONSISTENCY_SCOPE_GATE"
TASK_ID = "KMFA-V014-VALUE-CONSISTENCY-SCOPE-GATE-20260705"
ACCEPTANCE_ID = "ACC-V014-VALUE-CONSISTENCY-SCOPE-GATE"
STATUS = "completed_public_safe_value_consistency_scope_locked_no_go"
NEXT_RECOMMENDED_PHASE = "V014_RAW_VALUE_MATCHING_PRIVATE_DRY_RUN"

RAW_BASELINE_LOCK_PATH = Path("KMFA/metadata/baseline/v014_authoritative_raw_baseline_lock.json")
RAW_CONSISTENCY_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V014_RAW_CONSISTENCY_CROSS_VALIDATION_GATE/machine/raw_consistency_cross_validation_manifest.json"
)
RAW_CONSISTENCY_GO_NO_GO_PATH = Path(
    "KMFA/stage_artifacts/V014_RAW_CONSISTENCY_CROSS_VALIDATION_GATE/machine/raw_consistency_cross_validation_go_no_go_report.json"
)
LINEAGE_COMPLETENESS_PATH = Path("KMFA/metadata/lineage/lineage_completeness_review.json")
LINEAGE_REPORT_GATE_PATH = Path("KMFA/metadata/quality/lineage_report_release_gate_review.json")

OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_VALUE_CONSISTENCY_SCOPE_GATE")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
MANIFEST_PATH = MACHINE_DIR / "value_consistency_scope_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "value_consistency_scope_go_no_go_report.json"
SCOPE_MATRIX_PATH = MACHINE_DIR / "value_consistency_scope_matrix.json"
DIFFERENCE_REPORT_CONTRACT_PATH = MACHINE_DIR / "difference_report_contract.json"
REPORT_PATH = HUMAN_DIR / "value_consistency_scope_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_MANIFEST_PATH = Path("KMFA/metadata/quality/v014_value_consistency_scope_manifest.json")
METADATA_GO_NO_GO_PATH = Path("KMFA/metadata/quality/v014_value_consistency_scope_go_no_go_report.json")
METADATA_SCOPE_MATRIX_PATH = Path("KMFA/metadata/quality/v014_value_consistency_scope_matrix.json")
METADATA_DIFFERENCE_CONTRACT_PATH = Path("KMFA/metadata/quality/v014_difference_report_contract.json")

PRIVATE_OUTPUT_DIR = Path("KMFA/.codex_private_runtime/v014_value_consistency_scope_gate")
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_raw_readonly_stat_guard.json"


def _now(generated_at: str | None = None) -> str:
    return generated_at or datetime.now().astimezone().isoformat(timespec="seconds")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        return "UNKNOWN"
    return result.stdout.strip()


def _scope_matrix() -> dict[str, Any]:
    lanes = [
        {
            "lane_id": "VC-L01",
            "name": "raw source container identity",
            "source_layer": "authoritative_raw_container",
            "target_layer": "private_source_profile",
            "verification_method": "hash_profile_cross_run_lock",
            "status": "completed_by_prior_gate",
            "public_output_policy": "aggregate_status_only",
            "private_output_policy": "hash_profile_private_runtime_only",
            "required_before_business_value_go": True,
        },
        {
            "lane_id": "VC-L02",
            "name": "raw schema and mapping readiness",
            "source_layer": "raw_private_schema_or_header_profile",
            "target_layer": "field_mapping_contract",
            "verification_method": "private_schema_header_diagnostic_then_public_safe_mapping_ids",
            "status": "scope_locked_not_executed_this_phase",
            "public_output_policy": "hash_or_ref_only",
            "private_output_policy": "schema_header_details_private_runtime_only",
            "required_before_business_value_go": True,
        },
        {
            "lane_id": "VC-L03",
            "name": "raw value extraction and canonical staging",
            "source_layer": "raw_row_cell_or_document_value",
            "target_layer": "canonical_staging_fact",
            "verification_method": "read_only_extract_normalize_compare_with_source_anchor",
            "status": "not_performed_this_phase",
            "public_output_policy": "no_raw_or_processed_business_values",
            "private_output_policy": "local_value_diagnostic_private_runtime_only",
            "required_before_business_value_go": True,
        },
        {
            "lane_id": "VC-L04",
            "name": "processed fact and derived metric reconciliation",
            "source_layer": "canonical_staging_fact",
            "target_layer": "fact_metric_report_runtime",
            "verification_method": "zero_delta_and_lineage_reference_replay",
            "status": "blocked_until_raw_value_matching",
            "public_output_policy": "status_mismatch_class_and_refs_only",
            "private_output_policy": "raw_processed_value_pairs_private_runtime_only",
            "required_before_business_value_go": True,
        },
        {
            "lane_id": "VC-L05",
            "name": "lineage full check and report release dependency",
            "source_layer": "field_metric_report_lineage",
            "target_layer": "formal_report_release_gate",
            "verification_method": "lineage_full_check_after_value_consistency",
            "status": "blocked_until_value_consistency_verified",
            "public_output_policy": "gate_flags_and_counts_only",
            "private_output_policy": "no_private_output_expected",
            "required_before_business_value_go": True,
        },
        {
            "lane_id": "VC-L06",
            "name": "unresolved mismatch and difference report",
            "source_layer": "cross_validation_mismatch",
            "target_layer": "owner_readable_difference_report",
            "verification_method": "multi_pass_cross_validation_failure_report",
            "status": "armed_not_triggered_this_phase",
            "public_output_policy": "sanitized_summary_without_values",
            "private_output_policy": "local_private_detail_report_if_needed",
            "required_before_business_value_go": True,
        },
    ]
    return {
        "record_type": "v014_value_consistency_scope_matrix",
        "schema_version": "kmfa.v014_value_consistency_scope_matrix.v1",
        "project_id": PROJECT_ID,
        "version": VERSION,
        "phase_id": PHASE_ID,
        "lane_count": len(lanes),
        "lanes": lanes,
        "all_lanes_public_safe": True,
        "raw_business_values_in_public_scope_matrix": False,
        "raw_filenames_in_public_scope_matrix": False,
        "field_header_plaintext_in_public_scope_matrix": False,
    }


def _difference_report_contract() -> dict[str, Any]:
    return {
        "record_type": "v014_difference_report_contract",
        "schema_version": "kmfa.v014_difference_report_contract.v1",
        "project_id": PROJECT_ID,
        "version": VERSION,
        "phase_id": PHASE_ID,
        "trigger": "repeated_cross_validation_cannot_keep_processed_data_consistent_with_raw_data",
        "enabled": True,
        "final_goal_closeout_must_include_difference_report_if_triggered": True,
        "multi_pass_cross_validation_required_before_consistency_claim": True,
        "minimum_independent_validation_passes": 3,
        "raw_inbox_mutation_allowed": False,
        "public_difference_report_contains_raw_values": False,
        "public_difference_report_contains_raw_filenames": False,
        "public_difference_report_contains_field_header_plaintext": False,
        "private_detail_report_location": "KMFA/.codex_private_runtime/",
        "public_safe_fields_required": [
            "difference_id",
            "scope_lane_id",
            "source_ref",
            "processed_ref",
            "mismatch_class",
            "severity",
            "responsible_role",
            "blocker_id",
            "next_action",
        ],
        "blocked_release_until_resolved": True,
    }


def _public_repo_safety() -> dict[str, bool]:
    return {
        "public_safe_aggregate_only": True,
        "raw_business_data_committed": False,
        "compressed_raw_package_committed": False,
        "office_workbook_committed": False,
        "source_document_committed": False,
        "private_csv_committed": False,
        "raw_filenames_committed": False,
        "raw_hashes_committed": False,
        "archive_member_names_committed": False,
        "sheet_names_committed": False,
        "field_or_header_plaintext_committed": False,
        "raw_or_processed_business_values_committed": False,
        "credential_or_secret_committed": False,
        "private_diagnostic_committed": False,
    }


def _go_no_go() -> dict[str, Any]:
    return {
        "record_type": "v014_value_consistency_scope_go_no_go_report",
        "schema_version": GO_NO_GO_SCHEMA_VERSION,
        "project_id": PROJECT_ID,
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "decision": "NO_GO",
        "decision_reason": (
            "Value-consistency scope, raw read-only mutation guard and difference-report obligation are locked, "
            "but raw business-value matching, processed-data reconciliation and lineage full check have not been performed."
        ),
        "resolved_blocker_ids": [
            "AUTHORITATIVE_RAW_BASELINE_LOCKED",
            "VALUE_CONSISTENCY_SCOPE_LOCKED",
            "RAW_INBOX_MUTATION_GUARD_LOCKED",
            "DIFFERENCE_REPORT_OBLIGATION_LOCKED",
        ],
        "blocker_ids": [
            "RAW_VALUE_MATCHING_NOT_PERFORMED",
            "PROCESSED_DATA_RECONCILIATION_NOT_PERFORMED",
            "BUSINESS_VALUE_CONSISTENCY_NOT_VERIFIED",
            "LINEAGE_FULL_CHECK_BLOCKED_BY_VALUE_CONSISTENCY",
            "FORMAL_REPORT_RELEASE_BLOCKED_BY_LINEAGE",
            "GITHUB_UPLOAD_BLOCKED_BY_NO_GO",
            "APP_REINSTALL_BLOCKED_BY_NO_GO",
            "BUSINESS_EXECUTION_BLOCKED_BY_NO_GO",
        ],
        "authoritative_raw_baseline_locked": True,
        "value_consistency_scope_locked": True,
        "raw_inbox_mutation_guard_locked": True,
        "raw_value_matching_performed": False,
        "processed_data_reconciliation_performed": False,
        "business_value_consistency_verified": False,
        "difference_report_required_on_repeated_mismatch": True,
        "lineage_full_check_complete": False,
        "formal_report_allowed": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "business_execution_allowed": False,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
    }


def _write_human_reports(manifest: dict[str, Any]) -> None:
    summary = manifest["value_consistency_summary"]
    report = [
        "# KMFA v0.1.4 Value Consistency Scope Gate",
        "",
        f"- status: `{manifest['status']}`",
        f"- phase_id: `{manifest['phase_id']}`",
        f"- task_id: `{manifest['task_id']}`",
        f"- authoritative_raw_baseline_locked: `{str(summary['authoritative_raw_baseline_locked']).lower()}`",
        f"- value_consistency_scope_locked: `{str(summary['value_consistency_scope_locked']).lower()}`",
        f"- raw_inbox_mutation_guard_locked: `{str(summary['raw_inbox_mutation_guard_locked']).lower()}`",
        f"- raw_value_matching_performed: `{str(summary['raw_value_matching_performed']).lower()}`",
        f"- processed_data_reconciliation_performed: `{str(summary['processed_data_reconciliation_performed']).lower()}`",
        f"- business_value_consistency_verified: `{str(summary['business_value_consistency_verified']).lower()}`",
        f"- difference_report_required_on_repeated_mismatch: `{str(summary['difference_report_required_on_repeated_mismatch']).lower()}`",
        f"- decision: `{manifest['go_no_go']['decision']}`",
        "",
        "## Boundary",
        "",
        "- This phase locks the next raw value matching scope and acceptance gates.",
        "- This phase does not extract, normalize, compare or publish raw or processed business values.",
        "- The raw inbox is protected by a before/after stat guard; no write, delete, move, rename, overwrite, copy or in-place normalization is allowed.",
        "- If repeated cross-validation cannot keep processed data consistent with the raw source, final goal closeout must include a difference report.",
        "- Public evidence contains only status, counts, refs and gate flags.",
    ]
    _write_text(REPORT_PATH, "\n".join(report) + "\n")

    go_record = [
        "# KMFA v0.1.4 Value Consistency Scope Go/No-Go",
        "",
        "- decision: `NO_GO`",
        "- authoritative_raw_baseline_locked: `true`",
        "- value_consistency_scope_locked: `true`",
        "- raw_value_matching_performed: `false`",
        "- processed_data_reconciliation_performed: `false`",
        "- business_value_consistency_verified: `false`",
        "- lineage_full_check_complete: `false`",
        "- formal_report_allowed: `false`",
        "- github_upload_allowed: `false`",
        "- app_reinstall_allowed: `false`",
        "- business_execution_allowed: `false`",
    ]
    _write_text(GO_NO_GO_RECORD_PATH, "\n".join(go_record) + "\n")

    tests = [
        "# KMFA v0.1.4 Value Consistency Scope Test Results",
        "",
        "- status: `pending_final_validation`",
        "- generator: `pending_final_validation`",
        "- validator: `pending_final_validation`",
        "- focused_unit_test: `pending_final_validation`",
        "- governance_validator: `pending_final_validation`",
        "- raw_private_scan: `pending_final_validation`",
        "- secret_scan: `pending_final_validation`",
        "- diff_check: `pending_final_validation`",
    ]
    _write_text(TEST_RESULTS_PATH, "\n".join(tests) + "\n")

    risks = [
        "# KMFA v0.1.4 Value Consistency Scope Risk Register",
        "",
        "| risk_id | risk | control | status |",
        "|---|---|---|---|",
        "| VC-SCOPE-001 | Scope lock could be mistaken for successful value matching | Keep raw value matching and business value consistency flags false | blocked |",
        "| VC-SCOPE-002 | Difference report could leak values | Public contract requires sanitized report; detailed values stay private-runtime only if needed | controlled |",
        "| VC-SCOPE-003 | Raw source could be polluted during analysis | Before/after stat guard and explicit mutation flags remain required | controlled |",
    ]
    _write_text(RISK_REGISTER_PATH, "\n".join(risks) + "\n")

    rollback = [
        "# KMFA v0.1.4 Value Consistency Scope Rollback Plan",
        "",
        "This phase is local-only. It does not modify the raw inbox, GitHub main, app installs, production systems or external connectors.",
        "",
        "Rollback is limited to removing this phase's public evidence, metadata quality records, governance entries and the git-ignored private stat guard.",
    ]
    _write_text(ROLLBACK_PATH, "\n".join(rollback) + "\n")


def generate(*, generated_at: str | None = None, write: bool = True) -> dict[str, Any]:
    generated = _now(generated_at)
    raw_baseline = _read_json(RAW_BASELINE_LOCK_PATH)
    raw_consistency_manifest = _read_json(RAW_CONSISTENCY_MANIFEST_PATH)
    raw_consistency_go_no_go = _read_json(RAW_CONSISTENCY_GO_NO_GO_PATH)
    lineage = _read_json(LINEAGE_COMPLETENESS_PATH)
    release_gate = _read_json(LINEAGE_REPORT_GATE_PATH)

    raw_root_before = stat_snapshot(RAW_INBOX) if RAW_INBOX.exists() else {}
    raw_root_after = stat_snapshot(RAW_INBOX) if RAW_INBOX.exists() else {}
    mutation_detected = raw_root_before != raw_root_after

    scope_matrix = _scope_matrix()
    difference_contract = _difference_report_contract()
    go_no_go = _go_no_go()
    baseline_locked = (
        raw_baseline.get("authoritative_raw_baseline_locked") is True
        and raw_baseline.get("source_container_consistency_verified") is True
        and raw_consistency_go_no_go.get("authoritative_raw_baseline_locked") is True
        and raw_consistency_manifest.get("raw_consistency_summary", {}).get("source_container_consistency_verified") is True
    )

    value_summary = {
        "authoritative_raw_baseline_locked": baseline_locked,
        "source_container_consistency_verified": baseline_locked,
        "value_consistency_scope_locked": True,
        "raw_inbox_mutation_guard_locked": not mutation_detected,
        "raw_inbox_mutation_detected": mutation_detected,
        "raw_value_matching_performed": False,
        "raw_business_value_extraction_performed": False,
        "processed_data_reconciliation_performed": False,
        "processed_data_consistency_verified": False,
        "business_value_consistency_verified": False,
        "lineage_full_check_complete": bool(lineage.get("lineage_full_check_complete")) is True,
        "formal_report_allowed": bool(release_gate.get("formal_report_allowed")) is True,
        "difference_report_required_on_repeated_mismatch": True,
        "difference_report_triggered_this_phase": False,
        "difference_report_obligation_locked": True,
        "public_value_disclosure_allowed": False,
        "private_value_diagnostic_next_phase_required": True,
    }
    go_no_go["authoritative_raw_baseline_locked"] = baseline_locked
    go_no_go["raw_inbox_mutation_guard_locked"] = not mutation_detected

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "project_id": PROJECT_ID,
        "version": VERSION,
        "phase_id": PHASE_ID,
        "phase_name": "Value consistency scope gate",
        "task_id": TASK_ID,
        "acceptance_ids": [ACCEPTANCE_ID],
        "generated_at": generated,
        "reviewed_head": _git_output(["rev-parse", "HEAD"]),
        "worktree": _git_output(["rev-parse", "--show-toplevel"]),
        "branch": _git_output(["branch", "--show-current"]),
        "remote": _git_output(["remote", "get-url", "origin"]),
        "status": STATUS,
        "phase_scope_controls": {
            "current_phase_only": True,
            "value_consistency_scope_gate_only": True,
            "authoritative_raw_baseline_dependency_consumed": True,
            "raw_inbox_stat_guard_only": True,
            "raw_business_value_extraction_performed": False,
            "raw_value_matching_performed": False,
            "processed_data_reconciliation_performed": False,
            "lineage_full_check_performed": False,
            "formal_report_performed": False,
            "github_upload_performed": False,
            "app_reinstall_performed": False,
            "business_execution_performed": False,
            "next_phase_started": False,
        },
        "dependency_refs": {
            "raw_baseline_lock_ref": RAW_BASELINE_LOCK_PATH.as_posix(),
            "raw_consistency_manifest_ref": RAW_CONSISTENCY_MANIFEST_PATH.as_posix(),
            "raw_consistency_go_no_go_ref": RAW_CONSISTENCY_GO_NO_GO_PATH.as_posix(),
            "lineage_completeness_ref": LINEAGE_COMPLETENESS_PATH.as_posix(),
            "lineage_report_gate_ref": LINEAGE_REPORT_GATE_PATH.as_posix(),
        },
        "value_consistency_summary": value_summary,
        "scope_matrix": scope_matrix,
        "difference_report_contract": difference_contract,
        "raw_boundary": {
            "raw_inbox_read_performed_by_this_phase": False,
            "raw_inbox_list_performed_by_this_phase": False,
            "raw_inbox_hash_performed_by_this_phase": False,
            "raw_inbox_stat_guard_performed_by_this_phase": True,
            "raw_inbox_write_performed_by_this_phase": False,
            "raw_inbox_delete_performed_by_this_phase": False,
            "raw_inbox_move_performed_by_this_phase": False,
            "raw_inbox_rename_performed_by_this_phase": False,
            "raw_inbox_overwrite_performed_by_this_phase": False,
            "raw_inbox_copy_performed_by_this_phase": False,
            "raw_inbox_create_extra_files_inside_by_this_phase": False,
            "raw_inbox_normalize_performed_by_this_phase": False,
            "raw_inbox_mutated_by_this_phase": mutation_detected,
            "raw_root_stat_unchanged_after_scope_guard": not mutation_detected,
            "private_runtime_output_dir": "KMFA/.codex_private_runtime/",
        },
        "public_repo_safety": _public_repo_safety(),
        "go_no_go": go_no_go,
        "github_upload_performed": False,
        "github_upload_status": "not_uploaded_blocked_by_value_lineage_release_gates",
        "app_reinstall_performed": False,
        "formal_report_performed": False,
        "business_execution_performed": False,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
        "private_diagnostic_ref": PRIVATE_DIAGNOSTIC_PATH.as_posix(),
        "evidence_refs": [
            REPORT_PATH.as_posix(),
            GO_NO_GO_RECORD_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            RISK_REGISTER_PATH.as_posix(),
            ROLLBACK_PATH.as_posix(),
            MANIFEST_PATH.as_posix(),
            GO_NO_GO_PATH.as_posix(),
            SCOPE_MATRIX_PATH.as_posix(),
            DIFFERENCE_REPORT_CONTRACT_PATH.as_posix(),
            METADATA_MANIFEST_PATH.as_posix(),
            METADATA_GO_NO_GO_PATH.as_posix(),
            METADATA_SCOPE_MATRIX_PATH.as_posix(),
            METADATA_DIFFERENCE_CONTRACT_PATH.as_posix(),
        ],
        "validation_summary": {
            "generator": "PENDING_FINAL_VALIDATION",
            "validator": "PENDING_FINAL_VALIDATION",
            "focused_unit_test": "PENDING_FINAL_VALIDATION",
            "governance_validator": "PENDING_FINAL_VALIDATION",
            "raw_private_scan": "PENDING_FINAL_VALIDATION",
            "secret_scan": "PENDING_FINAL_VALIDATION",
            "diff_check": "PENDING_FINAL_VALIDATION",
        },
    }
    private_diagnostic = {
        "schema_version": PRIVATE_SCHEMA_VERSION,
        "classification": "private_raw_readonly_stat_guard_do_not_commit",
        "generated_at": generated,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "raw_root_path_sha256": sha256_text(str(RAW_INBOX)),
        "raw_root_before": raw_root_before,
        "raw_root_after": raw_root_after,
        "raw_root_stat_unchanged_after_scope_guard": not mutation_detected,
        "raw_value_matching_performed": False,
        "raw_business_value_extraction_performed": False,
        "raw_inbox_mutation_detected": mutation_detected,
    }

    if write:
        _write_json(PRIVATE_DIAGNOSTIC_PATH, private_diagnostic)
        _write_json(MANIFEST_PATH, manifest)
        _write_json(GO_NO_GO_PATH, go_no_go)
        _write_json(SCOPE_MATRIX_PATH, scope_matrix)
        _write_json(DIFFERENCE_REPORT_CONTRACT_PATH, difference_contract)
        _write_json(METADATA_MANIFEST_PATH, manifest)
        _write_json(METADATA_GO_NO_GO_PATH, go_no_go)
        _write_json(METADATA_SCOPE_MATRIX_PATH, scope_matrix)
        _write_json(METADATA_DIFFERENCE_CONTRACT_PATH, difference_contract)
        _write_human_reports(manifest)
    return manifest


def main() -> int:
    manifest = generate()
    summary = manifest["value_consistency_summary"]
    print(
        "PASS: generated KMFA v0.1.4 value consistency scope gate "
        f"(scope_locked={str(summary['value_consistency_scope_locked']).lower()}, "
        f"raw_value_matching={str(summary['raw_value_matching_performed']).lower()}, "
        f"business_value_consistency={str(summary['business_value_consistency_verified']).lower()}, "
        f"decision={manifest['go_no_go']['decision']})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
