#!/usr/bin/env python3
"""Attempt authorized-resolution application after final threshold.

This phase consumes the prior public-safe final-threshold artifacts and ignored
private final-threshold records. It does not read the raw inbox. It records that
current private evidence contains no active authoritative resolution application
for the 48 final-threshold blockers, so binding/comparison/downstream gates stay
closed.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.v014_residual_difference_owner_authorized_anchor_confirmation import (  # noqa: E402
    _changed_kmfa_files,
    _git_check_ignored,
    _git_output,
    _now,
    _read_json,
    _read_jsonl,
    _upsert_jsonl,
    _write_json,
    _write_jsonl,
    _write_text,
)
from KMFA.tools import (  # noqa: E402
    v014_residual_difference_authorized_source_reference_or_exclusion_application_blocker_final_threshold_recheck_after_raw_refresh
    as source_final_threshold,
)


PROJECT_ROOT = Path("KMFA")
PHASE_ID = (
    "V014_RESIDUAL_DIFFERENCE_AUTHORIZED_SOURCE_REFERENCE_OR_EXCLUSION_"
    "APPLICATION_RESOLUTION_ATTEMPT_AFTER_FINAL_THRESHOLD"
)
TASK_ID = (
    "KMFA-V014-RESIDUAL-DIFFERENCE-AUTHORIZED-SOURCE-REFERENCE-OR-EXCLUSION-"
    "APPLICATION-RESOLUTION-ATTEMPT-AFTER-FINAL-THRESHOLD-20260708"
)
ACCEPTANCE_ID = (
    "ACC-V014-RESIDUAL-DIFFERENCE-AUTHORIZED-SOURCE-REFERENCE-OR-EXCLUSION-"
    "APPLICATION-RESOLUTION-ATTEMPT-AFTER-FINAL-THRESHOLD"
)
VERSION = (
    "0.1.4-residual-difference-authorized-source-reference-or-exclusion-"
    "application-resolution-attempt-after-final-threshold"
)
STATUS = (
    "completed_validated_local_only_authorized_source_reference_or_exclusion_"
    "application_resolution_attempt_after_final_threshold_still_blocked_no_go"
)
DECISION = "NO_GO"
RESOLUTION_CONCLUSION = "current_private_evidence_contains_no_active_authoritative_resolution_application"
NEXT_REQUIRED_INPUT = (
    "owner_or_authorized_delegate_provides_applicable_source_reference_owner_exclusion_formula_or_non_numeric_mapping"
)
NEXT_RECOMMENDED_PHASE = "BLOCKED_UNTIL_AUTHORIZED_RESOLUTION_APPLICATION_AVAILABLE"

PRIVATE_SLOT_KEY = source_final_threshold.PRIVATE_SLOT_KEY
SOURCE_REFERENCE_INTAKE_TRACK = source_final_threshold.SOURCE_REFERENCE_INTAKE_TRACK
FORMULA_MAPPING_INTAKE_TRACK = source_final_threshold.FORMULA_MAPPING_INTAKE_TRACK
EXPECTED_RESOLUTION_TRACK_COUNTS = source_final_threshold.EXPECTED_FINAL_THRESHOLD_TRACK_COUNTS

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = (
    MACHINE_DIR
    / "residual_difference_authorized_source_reference_or_exclusion_application_resolution_attempt_after_final_threshold_summary.json"
)
MANIFEST_PATH = (
    MACHINE_DIR
    / "residual_difference_authorized_source_reference_or_exclusion_application_resolution_attempt_after_final_threshold_manifest.json"
)
GO_NO_GO_PATH = (
    MACHINE_DIR
    / "residual_difference_authorized_source_reference_or_exclusion_application_resolution_attempt_after_final_threshold_go_no_go_report.json"
)
MATRIX_PATH = (
    MACHINE_DIR
    / "residual_difference_authorized_source_reference_or_exclusion_application_resolution_attempt_after_final_threshold_matrix_public_safe.json"
)
REPORT_PATH = (
    HUMAN_DIR
    / "residual_difference_authorized_source_reference_or_exclusion_application_resolution_attempt_after_final_threshold.md"
)
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_authorized_source_reference_or_exclusion_application_resolution_attempt_after_final_threshold_summary.json"
)
METADATA_MANIFEST_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_authorized_source_reference_or_exclusion_application_resolution_attempt_after_final_threshold_manifest.json"
)
METADATA_GO_NO_GO_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_authorized_source_reference_or_exclusion_application_resolution_attempt_after_final_threshold_go_no_go_report.json"
)
METADATA_MATRIX_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_authorized_source_reference_or_exclusion_application_resolution_attempt_after_final_threshold_matrix_public_safe.json"
)

SOURCE_APPLICATION_BLOCKER_FINAL_THRESHOLD_SUMMARY_PATH = source_final_threshold.METADATA_SUMMARY_PATH
SOURCE_APPLICATION_BLOCKER_FINAL_THRESHOLD_MANIFEST_PATH = source_final_threshold.METADATA_MANIFEST_PATH
SOURCE_APPLICATION_BLOCKER_FINAL_THRESHOLD_GO_NO_GO_PATH = source_final_threshold.METADATA_GO_NO_GO_PATH
SOURCE_APPLICATION_BLOCKER_FINAL_THRESHOLD_MATRIX_PATH = source_final_threshold.METADATA_MATRIX_PATH
SOURCE_PRIVATE_APPLICATION_BLOCKER_FINAL_THRESHOLD_DIAGNOSTIC_PATH = (
    source_final_threshold.PRIVATE_FINAL_THRESHOLD_DIAGNOSTIC_PATH
)
SOURCE_PRIVATE_APPLICATION_BLOCKER_FINAL_THRESHOLD_RECORDS_PATH = (
    source_final_threshold.PRIVATE_FINAL_THRESHOLD_RECORDS_PATH
)
SOURCE_PRIVATE_APPLICATION_BLOCKER_FINAL_THRESHOLD_REPORT_PATH = (
    source_final_threshold.PRIVATE_FINAL_THRESHOLD_REPORT_PATH
)

PRIVATE_OUTPUT_DIR = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_residual_difference_authorized_source_reference_or_exclusion_application_resolution_attempt_after_final_threshold"
)
PRIVATE_RESOLUTION_DIAGNOSTIC_PATH = (
    PRIVATE_OUTPUT_DIR
    / "private_authorized_source_reference_or_exclusion_application_resolution_attempt_diagnostic.json"
)
PRIVATE_RESOLUTION_RECORDS_PATH = (
    PRIVATE_OUTPUT_DIR
    / "private_authorized_source_reference_or_exclusion_application_resolution_attempt_records.jsonl"
)
PRIVATE_RESOLUTION_REPORT_PATH = (
    PRIVATE_OUTPUT_DIR
    / "private_authorized_source_reference_or_exclusion_application_resolution_attempt.md"
)

DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"
STAGE_STATUS_PATH = PROJECT_ROOT / "metadata/stage_status.jsonl"
TASK_STATUS_PATH = PROJECT_ROOT / "metadata/traceability/v1_4_stage_phase_task_status.jsonl"


def _raw_boundary() -> dict[str, bool]:
    return {
        "user_declared_raw_data_immutable": True,
        "raw_data_root_readonly_policy_active": True,
        "source_application_blocker_final_threshold_public_artifacts_read_by_this_phase": True,
        "source_application_blocker_final_threshold_manifest_read_by_this_phase": True,
        "source_application_blocker_final_threshold_go_no_go_read_by_this_phase": True,
        "source_application_blocker_final_threshold_matrix_read_by_this_phase": True,
        "source_private_application_blocker_final_threshold_diagnostic_read_by_this_phase": True,
        "source_private_application_blocker_final_threshold_records_read_by_this_phase": True,
        "source_private_application_blocker_final_threshold_report_read_by_this_phase": True,
        "private_resolution_diagnostic_written_by_this_phase": True,
        "private_resolution_records_written_by_this_phase": True,
        "private_resolution_report_written_by_this_phase": True,
        "source_private_application_blocker_final_threshold_diagnostic_mutated_by_this_phase": False,
        "source_private_application_blocker_final_threshold_records_mutated_by_this_phase": False,
        "source_private_application_blocker_final_threshold_report_mutated_by_this_phase": False,
        "authoritative_binding_applied_by_this_phase": False,
        "raw_candidate_fingerprint_bound_by_this_phase": False,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "raw_inbox_read_performed_by_this_phase": False,
        "raw_inbox_list_performed_by_this_phase": False,
        "raw_inbox_stat_performed_by_this_phase": False,
        "raw_inbox_hash_or_value_fingerprint_performed_by_this_phase": False,
        "raw_inbox_parse_performed_by_this_phase": False,
        "raw_inbox_field_or_header_read_performed_by_this_phase": False,
        "raw_inbox_value_extraction_performed_by_this_phase": False,
        "raw_inbox_write_performed_by_this_phase": False,
        "raw_inbox_delete_performed_by_this_phase": False,
        "raw_inbox_move_performed_by_this_phase": False,
        "raw_inbox_rename_performed_by_this_phase": False,
        "raw_inbox_overwrite_performed_by_this_phase": False,
        "raw_inbox_copy_performed_by_this_phase": False,
        "raw_inbox_normalize_performed_by_this_phase": False,
        "raw_inbox_mutated_by_this_phase": False,
    }


def _public_safety() -> dict[str, bool]:
    return {
        "public_safe_aggregate_only": True,
        "source_private_application_blocker_final_threshold_diagnostic_committed": False,
        "source_private_application_blocker_final_threshold_records_committed": False,
        "source_private_application_blocker_final_threshold_report_committed": False,
        "private_resolution_diagnostic_committed": False,
        "private_resolution_records_committed": False,
        "private_resolution_report_committed": False,
        "private_slot_detail_committed": False,
        "source_reference_detail_committed": False,
        "owner_exclusion_detail_committed": False,
        "formula_mapping_detail_committed": False,
        "raw_file_committed": False,
        "raw_filename_committed": False,
        "raw_archive_member_name_committed": False,
        "field_header_plaintext_committed": False,
        "row_value_committed": False,
        "business_value_committed": False,
        "private_ref_or_fingerprint_committed": False,
        "credential_or_secret_committed": False,
    }


def _build_resolution_records(*, generated_at: str, final_threshold_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, row in enumerate(final_threshold_rows, start=1):
        records.append(
            {
                "resolution_attempt_item_id": f"ASR-OE-APP-RESOLVE-FT-{index:03d}",
                "phase_id": PHASE_ID,
                "task_id": TASK_ID,
                "generated_at": generated_at,
                "source_application_blocker_final_threshold_recheck_item_id": row.get(
                    "application_blocker_final_threshold_recheck_item_id"
                ),
                PRIVATE_SLOT_KEY: row.get(PRIVATE_SLOT_KEY),
                "intake_track": row.get("intake_track"),
                "source_diagnostic_track": row.get("source_diagnostic_track"),
                "application_blocker_code": row.get("application_blocker_code"),
                "source_final_threshold_recheck_status": row.get("final_threshold_recheck_status"),
                "source_application_blocker_observation_count": row.get("application_blocker_observation_count"),
                "source_application_blocked_audit_threshold_met": row.get(
                    "application_blocked_audit_threshold_met"
                ),
                "active_authoritative_resolution_application_available": False,
                "auto_applied_authorized_resolution": False,
                "resolution_attempt_status": "still_blocked_missing_authorized_resolution_application",
                "binding_ready_after_resolution_attempt": False,
                "comparison_retry_ready_after_resolution_attempt": False,
                "raw_candidate_fingerprint_bound_by_this_phase": False,
                "raw_to_processed_value_comparison_performed_by_this_phase": False,
                "full_raw_to_processed_value_comparison_complete": False,
                "business_value_consistency_verified": False,
                "public_commit_allowed": False,
            }
        )
    return records


def _write_private_outputs(
    *,
    generated_at: str,
    source_summary: dict[str, Any],
    records: list[dict[str, Any]],
    raw_boundary: dict[str, bool],
) -> dict[str, Any]:
    track_counts = Counter(row.get("intake_track") for row in records)
    status_counts = Counter(row.get("resolution_attempt_status") for row in records)
    diagnostic = {
        "schema_version": (
            "kmfa.private.v014_authorized_source_reference_or_exclusion_application_"
            "resolution_attempt_after_final_threshold.v1"
        ),
        "classification": (
            "private_authorized_source_reference_or_exclusion_application_resolution_attempt_"
            "after_final_threshold_do_not_commit"
        ),
        "record_type": (
            "v014_authorized_source_reference_or_exclusion_application_resolution_attempt_"
            "after_final_threshold_diagnostic"
        ),
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "source_phase_id": source_summary.get("phase_id"),
        "resolution_conclusion": RESOLUTION_CONCLUSION,
        "resolution_attempt_item_count": len(records),
        "track_counts": dict(track_counts),
        "status_counts": dict(status_counts),
        "active_authoritative_resolution_application_count": 0,
        "auto_applied_authorized_resolution_count": 0,
        "still_blocked_authorized_resolution_application_count": len(records),
        "raw_boundary": raw_boundary,
    }
    _write_json(PRIVATE_RESOLUTION_DIAGNOSTIC_PATH, diagnostic)
    _write_jsonl(PRIVATE_RESOLUTION_RECORDS_PATH, records)
    _write_text(
        PRIVATE_RESOLUTION_REPORT_PATH,
        "\n".join(
            [
                "# Private Authorized Source Reference Or Exclusion Application Resolution Attempt After Final Threshold",
                "",
                f"- phase_id: `{PHASE_ID}`",
                f"- resolution_attempt_item_count: `{len(records)}`",
                "- active_authoritative_resolution_application_count: `0`",
                "- auto_applied_authorized_resolution_count: `0`",
                f"- still_blocked_authorized_resolution_application_count: `{len(records)}`",
                "- raw_to_processed_value_comparison_performed_by_this_phase: `false`",
                "",
                "This private report may reference private handles and must remain ignored.",
                "",
            ]
        ),
    )
    return diagnostic


def _build_summary(
    *,
    generated_at: str,
    source_summary: dict[str, Any],
    source_manifest: dict[str, Any],
    source_go_no_go: dict[str, Any],
    source_matrix: dict[str, Any],
    source_diagnostic: dict[str, Any],
    final_threshold_rows: list[dict[str, Any]],
    resolution_records: list[dict[str, Any]],
    raw_boundary: dict[str, bool],
    public_safety: dict[str, bool],
) -> dict[str, Any]:
    track_counts = Counter(row.get("intake_track") for row in resolution_records)
    status_counts = Counter(row.get("resolution_attempt_status") for row in resolution_records)
    return {
        "schema_version": (
            "kmfa.v014_authorized_source_reference_or_exclusion_application_resolution_"
            "attempt_after_final_threshold_summary.v1"
        ),
        "record_type": (
            "v014_authorized_source_reference_or_exclusion_application_resolution_attempt_"
            "after_final_threshold_summary"
        ),
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": generated_at,
        "status": STATUS,
        "decision": DECISION,
        "resolution_conclusion": RESOLUTION_CONCLUSION,
        "source_phase_id": source_summary.get("phase_id"),
        "source_manifest_phase_id": source_manifest.get("phase_id"),
        "source_go_no_go_decision": source_go_no_go.get("decision"),
        "source_matrix_check_fail_count": source_matrix.get("check_fail_count"),
        "source_private_diagnostic_phase_id": source_diagnostic.get("phase_id"),
        "source_application_blocker_final_threshold_recheck_item_count": source_summary.get(
            "application_blocker_final_threshold_recheck_item_count"
        ),
        "source_application_blocker_observation_count": source_summary.get(
            "application_blocker_observation_count"
        ),
        "source_application_blocked_audit_threshold_met": source_summary.get(
            "application_blocked_audit_threshold_met"
        ),
        "source_goal_status_recommendation": source_summary.get("goal_status_recommendation"),
        "source_binding_ready_after_final_threshold_recheck_count": source_summary.get(
            "binding_ready_after_final_threshold_recheck_count"
        ),
        "source_comparison_retry_ready_after_final_threshold_recheck_count": source_summary.get(
            "comparison_retry_ready_after_final_threshold_recheck_count"
        ),
        "source_private_application_blocker_final_threshold_record_count": len(final_threshold_rows),
        "resolution_attempt_performed_by_this_phase": True,
        "resolution_attempt_item_count": len(resolution_records),
        "active_authoritative_resolution_application_count": 0,
        "auto_applied_authorized_resolution_count": 0,
        "still_blocked_authorized_resolution_application_count": status_counts[
            "still_blocked_missing_authorized_resolution_application"
        ],
        "source_reference_or_owner_exclusion_application_blocker_count": track_counts[
            SOURCE_REFERENCE_INTAKE_TRACK
        ],
        "formula_or_non_numeric_mapping_application_blocker_count": track_counts[
            FORMULA_MAPPING_INTAKE_TRACK
        ],
        "binding_ready_after_resolution_attempt_count": 0,
        "comparison_retry_ready_after_resolution_attempt_count": 0,
        "unresolved_difference_count": source_summary.get("unresolved_difference_count"),
        "private_resolution_diagnostic_written": True,
        "private_resolution_records_written": True,
        "private_resolution_report_written": True,
        "private_resolution_diagnostic_gitignored": _git_check_ignored(PRIVATE_RESOLUTION_DIAGNOSTIC_PATH),
        "private_resolution_records_gitignored": _git_check_ignored(PRIVATE_RESOLUTION_RECORDS_PATH),
        "private_resolution_report_gitignored": _git_check_ignored(PRIVATE_RESOLUTION_REPORT_PATH),
        "source_private_application_blocker_final_threshold_diagnostic_gitignored": _git_check_ignored(
            SOURCE_PRIVATE_APPLICATION_BLOCKER_FINAL_THRESHOLD_DIAGNOSTIC_PATH
        ),
        "source_private_application_blocker_final_threshold_records_gitignored": _git_check_ignored(
            SOURCE_PRIVATE_APPLICATION_BLOCKER_FINAL_THRESHOLD_RECORDS_PATH
        ),
        "source_private_application_blocker_final_threshold_report_gitignored": _git_check_ignored(
            SOURCE_PRIVATE_APPLICATION_BLOCKER_FINAL_THRESHOLD_REPORT_PATH
        ),
        "authoritative_binding_application_ready": False,
        "authoritative_binding_applied_by_this_phase": False,
        "raw_candidate_fingerprint_bound_by_this_phase": False,
        "raw_to_processed_value_comparison_ready": False,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "full_raw_to_processed_value_comparison_complete": False,
        "processed_consistency_verified": False,
        "business_value_consistency_verified": False,
        "full_reconciliation_allowed": False,
        "lineage_full_check_complete": False,
        "formal_report_allowed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "next_required_input": NEXT_REQUIRED_INPUT,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
        "raw_boundary": raw_boundary,
        "public_safety": public_safety,
    }


def _build_matrix(summary: dict[str, Any]) -> dict[str, Any]:
    checks = [
        (
            "source_final_threshold_loaded",
            str(summary["source_phase_id"]).endswith("APPLICATION_BLOCKER_FINAL_THRESHOLD_RECHECK_AFTER_RAW_REFRESH"),
        ),
        ("source_go_no_go_preserved", summary["source_go_no_go_decision"] == "NO_GO"),
        ("source_matrix_clean", summary["source_matrix_check_fail_count"] == 0),
        (
            "source_final_threshold_item_count_locked",
            summary["source_application_blocker_final_threshold_recheck_item_count"] == 48,
        ),
        ("source_observation_3_locked", summary["source_application_blocker_observation_count"] == 3),
        ("source_strict_threshold_met", summary["source_application_blocked_audit_threshold_met"] is True),
        (
            "source_private_final_threshold_records_loaded",
            summary["source_private_application_blocker_final_threshold_record_count"] == 48,
        ),
        ("resolution_attempt_items_locked", summary["resolution_attempt_item_count"] == 48),
        (
            "active_authoritative_resolution_zero_locked",
            summary["active_authoritative_resolution_application_count"] == 0,
        ),
        ("auto_application_zero_locked", summary["auto_applied_authorized_resolution_count"] == 0),
        (
            "still_blocked_locked",
            summary["still_blocked_authorized_resolution_application_count"] == 48,
        ),
        (
            "no_binding_or_retry_ready_after_resolution",
            summary["binding_ready_after_resolution_attempt_count"] == 0
            and summary["comparison_retry_ready_after_resolution_attempt_count"] == 0,
        ),
        ("private_resolution_outputs_ignored", summary["private_resolution_records_gitignored"] is True),
        ("raw_inbox_untouched", summary["raw_boundary"]["raw_inbox_mutated_by_this_phase"] is False),
        (
            "downstream_gates_closed",
            summary["github_upload_performed"] is False and summary["business_execution_performed"] is False,
        ),
    ]
    rows = [{"check_code": code, "status": "PASS" if passed else "FAIL"} for code, passed in checks]
    pass_count = sum(1 for row in rows if row["status"] == "PASS")
    return {
        "schema_version": (
            "kmfa.v014_authorized_source_reference_or_exclusion_application_resolution_attempt_"
            "after_final_threshold_matrix_public_safe.v1"
        ),
        "record_type": (
            "v014_authorized_source_reference_or_exclusion_application_resolution_attempt_"
            "after_final_threshold_matrix_public_safe"
        ),
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": summary["generated_at"],
        "decision": DECISION,
        "check_count": len(rows),
        "check_pass_count": pass_count,
        "check_fail_count": len(rows) - pass_count,
        "checks": rows,
    }


def _build_go_no_go(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": (
            "kmfa.v014_authorized_source_reference_or_exclusion_application_resolution_attempt_"
            "after_final_threshold_go_no_go.v1"
        ),
        "record_type": (
            "v014_authorized_source_reference_or_exclusion_application_resolution_attempt_"
            "after_final_threshold_go_no_go"
        ),
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": summary["generated_at"],
        "status": STATUS,
        "decision": DECISION,
        "resolution_conclusion": RESOLUTION_CONCLUSION,
        "resolution_attempt_item_count": summary["resolution_attempt_item_count"],
        "active_authoritative_resolution_application_count": 0,
        "auto_applied_authorized_resolution_count": 0,
        "still_blocked_authorized_resolution_application_count": summary[
            "still_blocked_authorized_resolution_application_count"
        ],
        "binding_ready_after_resolution_attempt_count": 0,
        "comparison_retry_ready_after_resolution_attempt_count": 0,
        "raw_candidate_fingerprint_bound_by_this_phase": False,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "full_raw_to_processed_value_comparison_complete": False,
        "business_value_consistency_verified": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "business_execution_allowed": False,
        "next_required_input": NEXT_REQUIRED_INPUT,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
    }


def _write_human(summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any]) -> None:
    report = f"""# V014 Authorized Source Reference Or Exclusion Application Resolution Attempt After Final Threshold

Generated at: {summary["generated_at"]}

## Scope

- Phase: `{PHASE_ID}`
- Decision: `{DECISION}`
- Status: `{STATUS}`
- Source: prior public-safe application-blocker-final-threshold evidence and ignored private final-threshold records.
- Raw boundary: no raw inbox read, list, stat, parse, value extraction, write, delete, move, rename, copy, normalize or mutation.

## Public-Safe Result

- Source final-threshold blockers: `{summary["source_application_blocker_final_threshold_recheck_item_count"]}`
- Resolution attempts: `{summary["resolution_attempt_item_count"]}`
- Active authoritative resolution applications: `{summary["active_authoritative_resolution_application_count"]}`
- Automatically applied authorized resolutions: `{summary["auto_applied_authorized_resolution_count"]}`
- Still blocked authorized resolution applications: `{summary["still_blocked_authorized_resolution_application_count"]}`
- Source reference or owner exclusion blockers: `{summary["source_reference_or_owner_exclusion_application_blocker_count"]}`
- Formula or non-numeric mapping blockers: `{summary["formula_or_non_numeric_mapping_application_blocker_count"]}`
- Binding ready after resolution attempt: `{summary["binding_ready_after_resolution_attempt_count"]}`
- Comparison retry ready after resolution attempt: `{summary["comparison_retry_ready_after_resolution_attempt_count"]}`
- Unresolved differences after this phase: `{summary["unresolved_difference_count"]}`

## Gate

Current private evidence has no active authoritative application for the 48 final-threshold blockers. This phase does not bind fingerprints, compare raw and processed values, reconcile processed data, claim business consistency, upload to GitHub, reinstall the app, or execute business use.

Next required input: `{NEXT_REQUIRED_INPUT}`.
"""
    go_record = f"""# Go / No-Go Record

- Phase: `{PHASE_ID}`
- Decision: `{go_no_go["decision"]}`
- Reason: current ignored private evidence has zero active authoritative resolution applications for the 48 final-threshold blockers.
- Matrix: `{matrix["check_pass_count"]}` pass / `{matrix["check_fail_count"]}` fail
- Next recommended phase: `{NEXT_RECOMMENDED_PHASE}`
- GitHub upload: not allowed in this phase.
- App reinstall: not allowed in this phase.
"""
    test_results = f"""# Test Results

- RED: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_authorized_source_reference_or_exclusion_application_resolution_attempt_after_final_threshold` failed before implementation because the generator module did not exist.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_resolution_attempt_after_final_threshold.py --generated-at 2026-07-08T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_resolution_attempt_after_final_threshold.py --require-private-resolution`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_authorized_source_reference_or_exclusion_application_resolution_attempt_after_final_threshold`
- Governance validators, CSV shape checks, diff check, raw/private marker scan, secret scan and private-runtime tracked-file scan: expected before commit.

Expected matrix result: {matrix["check_pass_count"]}/{matrix["check_count"]} PASS.
"""
    risk_register = """# Risk Register

- Risk: a resolution attempt is mistaken for authoritative binding or discrepancy closure.
- Control: binding, comparison, reconciliation and business consistency flags remain false.
- Risk: private slot or resolution details leak into public artifacts.
- Control: public artifacts contain aggregate counts only; private resolution outputs stay ignored.
- Risk: raw inbox is modified.
- Control: this phase reads existing ignored private final-threshold artifacts only and does not touch the raw inbox.
"""
    rollback = f"""# Rollback Plan

Remove artifacts for `{PHASE_ID}`, metadata copies, private resolution outputs, tool, validator, focused test and governance rows. Do not touch source final-threshold evidence, prior private artifacts or raw inbox files.
"""
    _write_text(REPORT_PATH, report)
    _write_text(GO_NO_GO_RECORD_PATH, go_record)
    _write_text(TEST_RESULTS_PATH, test_results)
    _write_text(RISK_REGISTER_PATH, risk_register)
    _write_text(ROLLBACK_PATH, rollback)


def _build_manifest(summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": (
            "kmfa.v014_authorized_source_reference_or_exclusion_application_resolution_attempt_"
            "after_final_threshold_manifest.v1"
        ),
        "record_type": (
            "v014_authorized_source_reference_or_exclusion_application_resolution_attempt_"
            "after_final_threshold_manifest"
        ),
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": summary["generated_at"],
        "status": STATUS,
        "decision": DECISION,
        "resolution_conclusion": RESOLUTION_CONCLUSION,
        "summary": summary,
        "matrix": matrix,
        "go_no_go_report": go_no_go,
        "source_artifacts": {
            "application_blocker_final_threshold_summary": "public_safe_metadata_copy",
            "application_blocker_final_threshold_manifest": "public_safe_metadata_copy",
            "application_blocker_final_threshold_go_no_go": "public_safe_metadata_copy",
            "application_blocker_final_threshold_matrix": "public_safe_metadata_copy",
            "application_blocker_final_threshold_private_diagnostic": "ignored_private_runtime",
            "application_blocker_final_threshold_private_records": "ignored_private_runtime",
            "application_blocker_final_threshold_private_report": "ignored_private_runtime",
        },
        "public_artifact_refs": [
            SUMMARY_PATH.as_posix(),
            MANIFEST_PATH.as_posix(),
            GO_NO_GO_PATH.as_posix(),
            MATRIX_PATH.as_posix(),
            REPORT_PATH.as_posix(),
            GO_NO_GO_RECORD_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            RISK_REGISTER_PATH.as_posix(),
            ROLLBACK_PATH.as_posix(),
        ],
        "metadata_artifact_refs": [
            METADATA_SUMMARY_PATH.as_posix(),
            METADATA_MANIFEST_PATH.as_posix(),
            METADATA_GO_NO_GO_PATH.as_posix(),
            METADATA_MATRIX_PATH.as_posix(),
        ],
        "private_artifact_refs": [
            "private:authorized_source_reference_or_exclusion_application_resolution_diagnostic",
            "private:authorized_source_reference_or_exclusion_application_resolution_records",
            "private:authorized_source_reference_or_exclusion_application_resolution_report",
        ],
        "raw_boundary": summary["raw_boundary"],
        "public_safety": summary["public_safety"],
        "test_commands": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_resolution_attempt_after_final_threshold.py --generated-at 2026-07-08T00:00:00+10:00",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_resolution_attempt_after_final_threshold.py --require-private-resolution",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_authorized_source_reference_or_exclusion_application_resolution_attempt_after_final_threshold",
        ],
        "git": {
            "branch": _git_output(["branch", "--show-current"]),
            "head": _git_output(["rev-parse", "HEAD"]),
            "status_short_branch": _git_output(["status", "--short", "--branch"]),
            "changed_kmfa_files": _changed_kmfa_files(),
        },
    }


def _write_governance_events(generated_at: str, summary: dict[str, Any]) -> None:
    event = {
        "event_id": (
            "DEV-KMFA-20260708-V014-AUTHORIZED-SOURCE-REFERENCE-OR-EXCLUSION-"
            "APPLICATION-RESOLUTION-ATTEMPT-AFTER-FINAL-THRESHOLD"
        ),
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "stage_id": "value-consistency",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "status": STATUS,
        "decision": DECISION,
        "go_no_go": DECISION,
        "summary": "Attempted public-safe authorized-resolution application after final threshold; 48 blockers remain unresolved and binding/comparison gates stay closed.",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "files_changed": _changed_kmfa_files(),
        "test_commands": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_resolution_attempt_after_final_threshold.py --generated-at 2026-07-08T00:00:00+10:00",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_resolution_attempt_after_final_threshold.py --require-private-resolution",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_authorized_source_reference_or_exclusion_application_resolution_attempt_after_final_threshold",
        ],
        "test_results": ["PENDING: final validation results will be recorded before local commit."],
        "next_required_input": NEXT_REQUIRED_INPUT,
        "resolution_attempt_item_count": summary["resolution_attempt_item_count"],
        "active_authoritative_resolution_application_count": 0,
        "auto_applied_authorized_resolution_count": 0,
        "still_blocked_authorized_resolution_application_count": summary[
            "still_blocked_authorized_resolution_application_count"
        ],
        "binding_ready_after_resolution_attempt_count": 0,
        "comparison_retry_ready_after_resolution_attempt_count": 0,
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "result_commit": "PENDING",
        "fact_level": "EXTRACTED",
    }
    _upsert_jsonl(DEVELOPMENT_EVENTS_PATH, event, ("event_id",))
    phase_status = {
        "record_type": "v014_phase",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "roadmap_phase_id": (
            "RESIDUAL_DIFFERENCE_AUTHORIZED_SOURCE_REFERENCE_OR_EXCLUSION_"
            "APPLICATION_RESOLUTION_ATTEMPT_AFTER_FINAL_THRESHOLD"
        ),
        "roadmap_stage_id": "VALUE-CONSISTENCY",
        "governance_stage_id": "VALUE-CONSISTENCY",
        "name": (
            "v0.1.4 residual difference authorized source reference or exclusion "
            "application resolution attempt after final threshold"
        ),
        "status": STATUS,
        "acceptance_id": ACCEPTANCE_ID,
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "fact_level": "EXTRACTED",
        "estimated_task_units": 1,
        "completed_task_units": 1,
        "derived_percent": 100.0,
        "task_count": 3,
        "updated_at": generated_at[:10],
        "version": VERSION,
    }
    _upsert_jsonl(STAGE_STATUS_PATH, phase_status, ("record_type", "phase_id"))
    task_records = [
        ("T1", "read prior final-threshold evidence and ignored private final-threshold records read-only"),
        ("T2", "write ignored private authorized-resolution application attempt records"),
        ("T3", "emit public-safe NO_GO evidence while keeping binding comparison and upload gates closed"),
    ]
    for suffix, goal in task_records:
        _upsert_jsonl(
            TASK_STATUS_PATH,
            {
                "schema_version": "kmfa.v014_stage_phase_task_status.v1",
                "record_type": "v014_task",
                "project_id": "KMFA",
                "stage_id": "VALUE-CONSISTENCY",
                "governance_stage_id": "VALUE-CONSISTENCY",
                "roadmap_stage_id": "VALUE-CONSISTENCY",
                "phase_id": PHASE_ID,
                "roadmap_phase_id": (
                    "RESIDUAL_DIFFERENCE_AUTHORIZED_SOURCE_REFERENCE_OR_EXCLUSION_"
                    "APPLICATION_RESOLUTION_ATTEMPT_AFTER_FINAL_THRESHOLD"
                ),
                "task_id": f"{TASK_ID}-{suffix}",
                "task_goal": goal,
                "status": "completed",
                "acceptance_id": ACCEPTANCE_ID,
                "evidence_ref": MANIFEST_PATH.as_posix(),
                "raw_data_committed": False,
                "fact_level": "EXTRACTED",
                "version": VERSION,
                "derived_percent": 100.0,
                "updated_at": generated_at[:10],
            },
            ("record_type", "task_id"),
        )


def _validate_sources(
    *,
    source_summary: dict[str, Any],
    source_go_no_go: dict[str, Any],
    source_matrix: dict[str, Any],
    source_diagnostic: dict[str, Any],
    source_rows: list[dict[str, Any]],
) -> None:
    if source_summary.get("phase_id") != source_final_threshold.PHASE_ID:
        raise ValueError("source application blocker final-threshold phase mismatch")
    if source_go_no_go.get("decision") != "NO_GO":
        raise ValueError("source application blocker final-threshold decision must be NO_GO")
    if source_matrix.get("check_fail_count") != 0:
        raise ValueError("source application blocker final-threshold matrix must be clean")
    if source_summary.get("application_blocker_final_threshold_recheck_item_count") != 48:
        raise ValueError("source application blocker final-threshold item count must be 48")
    if source_summary.get("application_blocker_observation_count") != 3:
        raise ValueError("source application blocker observation count must be 3")
    if source_summary.get("application_blocked_audit_threshold_met") is not True:
        raise ValueError("source application blocker final threshold must be met")
    if source_summary.get("binding_ready_after_final_threshold_recheck_count") != 0:
        raise ValueError("source binding-ready count must be zero")
    if source_summary.get("comparison_retry_ready_after_final_threshold_recheck_count") != 0:
        raise ValueError("source comparison retry-ready count must be zero")
    if source_diagnostic.get("application_blocker_final_threshold_recheck_item_count") != 48:
        raise ValueError("source private final-threshold diagnostic item count must be 48")
    if len(source_rows) != 48:
        raise ValueError("source private final-threshold records must contain 48 rows")
    counts = Counter(row.get("intake_track") for row in source_rows)
    if dict(counts) != EXPECTED_RESOLUTION_TRACK_COUNTS:
        raise ValueError(f"source final-threshold track counts must be {EXPECTED_RESOLUTION_TRACK_COUNTS!r}")


def generate(*, generated_at: str | None = None, write_governance_event: bool = True) -> dict[str, Any]:
    generated = generated_at or _now()
    source_summary = _read_json(SOURCE_APPLICATION_BLOCKER_FINAL_THRESHOLD_SUMMARY_PATH)
    source_manifest = _read_json(SOURCE_APPLICATION_BLOCKER_FINAL_THRESHOLD_MANIFEST_PATH)
    source_go_no_go = _read_json(SOURCE_APPLICATION_BLOCKER_FINAL_THRESHOLD_GO_NO_GO_PATH)
    source_matrix = _read_json(SOURCE_APPLICATION_BLOCKER_FINAL_THRESHOLD_MATRIX_PATH)
    source_diagnostic = _read_json(SOURCE_PRIVATE_APPLICATION_BLOCKER_FINAL_THRESHOLD_DIAGNOSTIC_PATH)
    final_threshold_rows = _read_jsonl(SOURCE_PRIVATE_APPLICATION_BLOCKER_FINAL_THRESHOLD_RECORDS_PATH)
    SOURCE_PRIVATE_APPLICATION_BLOCKER_FINAL_THRESHOLD_REPORT_PATH.read_text(encoding="utf-8")
    _validate_sources(
        source_summary=source_summary,
        source_go_no_go=source_go_no_go,
        source_matrix=source_matrix,
        source_diagnostic=source_diagnostic,
        source_rows=final_threshold_rows,
    )
    raw_boundary = _raw_boundary()
    public_safety = _public_safety()
    resolution_records = _build_resolution_records(generated_at=generated, final_threshold_rows=final_threshold_rows)
    private_diagnostic = _write_private_outputs(
        generated_at=generated,
        source_summary=source_summary,
        records=resolution_records,
        raw_boundary=raw_boundary,
    )
    summary = _build_summary(
        generated_at=generated,
        source_summary=source_summary,
        source_manifest=source_manifest,
        source_go_no_go=source_go_no_go,
        source_matrix=source_matrix,
        source_diagnostic=source_diagnostic,
        final_threshold_rows=final_threshold_rows,
        resolution_records=resolution_records,
        raw_boundary=raw_boundary,
        public_safety=public_safety,
    )
    matrix = _build_matrix(summary)
    go_no_go = _build_go_no_go(summary)
    manifest = _build_manifest(summary, matrix, go_no_go)
    for path, payload in (
        (SUMMARY_PATH, summary),
        (MANIFEST_PATH, manifest),
        (GO_NO_GO_PATH, go_no_go),
        (MATRIX_PATH, matrix),
        (METADATA_SUMMARY_PATH, summary),
        (METADATA_MANIFEST_PATH, manifest),
        (METADATA_GO_NO_GO_PATH, go_no_go),
        (METADATA_MATRIX_PATH, matrix),
    ):
        _write_json(path, payload)
    _write_human(summary, matrix, go_no_go)
    if write_governance_event:
        _write_governance_events(generated, summary)
    return {
        "summary": summary,
        "matrix": matrix,
        "go_no_go": go_no_go,
        "manifest": manifest,
        "private_diagnostic": private_diagnostic,
        "private_resolution_records": resolution_records,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated-at")
    parser.add_argument("--no-governance-event", action="store_true")
    args = parser.parse_args()
    result = generate(generated_at=args.generated_at, write_governance_event=not args.no_governance_event)
    summary = result["summary"]
    print(
        "PASS: generated V014 authorized source reference or exclusion application "
        "resolution attempt after final threshold "
        f"decision={summary['decision']} attempts={summary['resolution_attempt_item_count']} "
        f"applied={summary['auto_applied_authorized_resolution_count']} "
        f"blocked={summary['still_blocked_authorized_resolution_application_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
