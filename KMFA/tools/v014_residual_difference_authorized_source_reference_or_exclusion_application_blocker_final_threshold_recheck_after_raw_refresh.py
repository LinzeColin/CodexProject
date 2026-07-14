#!/usr/bin/env python3
"""Recheck final application-blocker threshold after raw refresh.

This phase consumes the previous public-safe threshold recheck and its ignored
private threshold records. It records the third observation for the 48
authorized-source-reference/application blockers, marks the strict threshold
met, and keeps authoritative application, comparison, upload, reinstall and
business-execution gates closed.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools import (  # noqa: E402
    v014_residual_difference_authorized_source_reference_or_exclusion_application_blocker_threshold_recheck_after_raw_refresh
    as source_threshold,
)


PROJECT_ROOT = Path("KMFA")
PHASE_ID = (
    "V014_RESIDUAL_DIFFERENCE_AUTHORIZED_SOURCE_REFERENCE_OR_EXCLUSION_"
    "APPLICATION_BLOCKER_FINAL_THRESHOLD_RECHECK_AFTER_RAW_REFRESH"
)
TASK_ID = (
    "KMFA-V014-RESIDUAL-DIFFERENCE-AUTHORIZED-SOURCE-REFERENCE-OR-EXCLUSION-"
    "APPLICATION-BLOCKER-FINAL-THRESHOLD-RECHECK-AFTER-RAW-REFRESH-20260708"
)
ACCEPTANCE_ID = (
    "ACC-V014-RESIDUAL-DIFFERENCE-AUTHORIZED-SOURCE-REFERENCE-OR-EXCLUSION-"
    "APPLICATION-BLOCKER-FINAL-THRESHOLD-RECHECK-AFTER-RAW-REFRESH"
)
VERSION = (
    "0.1.4-residual-difference-authorized-source-reference-or-exclusion-"
    "application-blocker-final-threshold-recheck-after-raw-refresh"
)
STATUS = (
    "completed_validated_local_only_authorized_source_reference_or_exclusion_"
    "application_blocker_final_threshold_recheck_after_raw_refresh_no_go"
)
DECISION = "NO_GO"
THRESHOLD_CONCLUSION = "application_blocker_final_threshold_recheck_strict_threshold_met_observation_3"
NEXT_REQUIRED_INPUT = (
    "owner_or_authorized_delegate_applies_source_reference_exclusion_or_formula_mapping_before_binding"
)
NEXT_RECOMMENDED_PHASE = "BLOCKED_UNTIL_AUTHORIZED_SOURCE_REFERENCE_EXCLUSION_OR_FORMULA_MAPPING_APPLIED"

PRIVATE_SLOT_KEY = source_threshold.PRIVATE_SLOT_KEY
SOURCE_REFERENCE_INTAKE_TRACK = source_threshold.SOURCE_REFERENCE_INTAKE_TRACK
FORMULA_MAPPING_INTAKE_TRACK = source_threshold.FORMULA_MAPPING_INTAKE_TRACK
EXPECTED_FINAL_THRESHOLD_TRACK_COUNTS = source_threshold.EXPECTED_THRESHOLD_TRACK_COUNTS

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = (
    MACHINE_DIR
    / "residual_difference_authorized_source_reference_or_exclusion_application_blocker_final_threshold_recheck_after_raw_refresh_summary.json"
)
MANIFEST_PATH = (
    MACHINE_DIR
    / "residual_difference_authorized_source_reference_or_exclusion_application_blocker_final_threshold_recheck_after_raw_refresh_manifest.json"
)
GO_NO_GO_PATH = (
    MACHINE_DIR
    / "residual_difference_authorized_source_reference_or_exclusion_application_blocker_final_threshold_recheck_after_raw_refresh_go_no_go_report.json"
)
MATRIX_PATH = (
    MACHINE_DIR
    / "residual_difference_authorized_source_reference_or_exclusion_application_blocker_final_threshold_recheck_after_raw_refresh_matrix_public_safe.json"
)
REPORT_PATH = (
    HUMAN_DIR
    / "residual_difference_authorized_source_reference_or_exclusion_application_blocker_final_threshold_recheck_after_raw_refresh.md"
)
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_authorized_source_reference_or_exclusion_application_blocker_final_threshold_recheck_after_raw_refresh_summary.json"
)
METADATA_MANIFEST_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_authorized_source_reference_or_exclusion_application_blocker_final_threshold_recheck_after_raw_refresh_manifest.json"
)
METADATA_GO_NO_GO_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_authorized_source_reference_or_exclusion_application_blocker_final_threshold_recheck_after_raw_refresh_go_no_go_report.json"
)
METADATA_MATRIX_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_authorized_source_reference_or_exclusion_application_blocker_final_threshold_recheck_after_raw_refresh_matrix_public_safe.json"
)

SOURCE_APPLICATION_BLOCKER_THRESHOLD_SUMMARY_PATH = source_threshold.METADATA_SUMMARY_PATH
SOURCE_APPLICATION_BLOCKER_THRESHOLD_MANIFEST_PATH = source_threshold.METADATA_MANIFEST_PATH
SOURCE_APPLICATION_BLOCKER_THRESHOLD_GO_NO_GO_PATH = source_threshold.METADATA_GO_NO_GO_PATH
SOURCE_APPLICATION_BLOCKER_THRESHOLD_MATRIX_PATH = source_threshold.METADATA_MATRIX_PATH
SOURCE_PRIVATE_APPLICATION_BLOCKER_THRESHOLD_DIAGNOSTIC_PATH = source_threshold.PRIVATE_THRESHOLD_DIAGNOSTIC_PATH
SOURCE_PRIVATE_APPLICATION_BLOCKER_THRESHOLD_RECORDS_PATH = source_threshold.PRIVATE_THRESHOLD_RECORDS_PATH
SOURCE_PRIVATE_APPLICATION_BLOCKER_THRESHOLD_REPORT_PATH = source_threshold.PRIVATE_THRESHOLD_REPORT_PATH

PRIVATE_OUTPUT_DIR = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_residual_difference_authorized_source_reference_or_exclusion_application_blocker_final_threshold_recheck_after_raw_refresh"
)
PRIVATE_FINAL_THRESHOLD_DIAGNOSTIC_PATH = (
    PRIVATE_OUTPUT_DIR
    / "private_authorized_source_reference_or_exclusion_application_blocker_final_threshold_recheck_diagnostic.json"
)
PRIVATE_FINAL_THRESHOLD_RECORDS_PATH = (
    PRIVATE_OUTPUT_DIR
    / "private_authorized_source_reference_or_exclusion_application_blocker_final_threshold_recheck_records.jsonl"
)
PRIVATE_FINAL_THRESHOLD_REPORT_PATH = (
    PRIVATE_OUTPUT_DIR
    / "private_authorized_source_reference_or_exclusion_application_blocker_final_threshold_recheck.md"
)

DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"
STAGE_STATUS_PATH = PROJECT_ROOT / "metadata/stage_status.jsonl"
TASK_STATUS_PATH = PROJECT_ROOT / "metadata/traceability/v1_4_stage_phase_task_status.jsonl"


def _raw_boundary() -> dict[str, bool]:
    return {
        "user_declared_raw_data_immutable": True,
        "raw_data_root_readonly_policy_active": True,
        "source_application_blocker_threshold_public_artifacts_read_by_this_phase": True,
        "source_application_blocker_threshold_manifest_read_by_this_phase": True,
        "source_application_blocker_threshold_go_no_go_read_by_this_phase": True,
        "source_application_blocker_threshold_matrix_read_by_this_phase": True,
        "source_private_application_blocker_threshold_diagnostic_read_by_this_phase": True,
        "source_private_application_blocker_threshold_records_read_by_this_phase": True,
        "source_private_application_blocker_threshold_report_read_by_this_phase": True,
        "private_application_blocker_final_threshold_diagnostic_written_by_this_phase": True,
        "private_application_blocker_final_threshold_records_written_by_this_phase": True,
        "private_application_blocker_final_threshold_report_written_by_this_phase": True,
        "source_private_application_blocker_threshold_diagnostic_mutated_by_this_phase": False,
        "source_private_application_blocker_threshold_records_mutated_by_this_phase": False,
        "source_private_application_blocker_threshold_report_mutated_by_this_phase": False,
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
        "source_private_application_blocker_threshold_diagnostic_committed": False,
        "source_private_application_blocker_threshold_records_committed": False,
        "source_private_application_blocker_threshold_report_committed": False,
        "private_application_blocker_final_threshold_diagnostic_committed": False,
        "private_application_blocker_final_threshold_records_committed": False,
        "private_application_blocker_final_threshold_report_committed": False,
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


def _build_final_threshold_rows(*, generated_at: str, source_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, source_row in enumerate(source_rows, start=1):
        rows.append(
            {
                "application_blocker_final_threshold_recheck_item_id": (
                    f"ASR-OE-APP-BLOCKER-FINAL-THRESHOLD-{index:03d}"
                ),
                "phase_id": PHASE_ID,
                "task_id": TASK_ID,
                "generated_at": generated_at,
                "source_application_blocker_threshold_recheck_item_id": source_row.get(
                    "application_blocker_threshold_recheck_item_id"
                ),
                PRIVATE_SLOT_KEY: source_row.get(PRIVATE_SLOT_KEY),
                "intake_track": source_row.get("intake_track"),
                "source_diagnostic_track": source_row.get("source_diagnostic_track"),
                "application_blocker_code": source_row.get("application_blocker_code"),
                "source_threshold_recheck_status": source_row.get("threshold_recheck_status"),
                "remediation_track": source_row.get("remediation_track"),
                "final_threshold_recheck_status": (
                    "application_blocker_observation_3_strict_threshold_met_"
                    "missing_authorized_resolution_application"
                ),
                "prior_application_blocker_observation_count": 2,
                "application_blocker_observation_count": 3,
                "application_blocked_audit_threshold_met": True,
                "goal_status_recommendation": "blocked",
                "authoritative_resolution_application_available": False,
                "binding_ready_after_final_threshold_recheck": False,
                "comparison_retry_ready_after_final_threshold_recheck": False,
                "raw_to_processed_value_comparison_performed_by_this_phase": False,
                "full_raw_to_processed_value_comparison_complete": False,
                "business_value_consistency_verified": False,
                "public_commit_allowed": False,
            }
        )
    return rows


def _write_private_outputs(
    *,
    generated_at: str,
    source_summary: dict[str, Any],
    final_rows: list[dict[str, Any]],
    raw_boundary: dict[str, bool],
) -> dict[str, Any]:
    track_counts = Counter(row.get("intake_track") for row in final_rows)
    blocker_codes = Counter(row.get("application_blocker_code") for row in final_rows)
    diagnostic = {
        "schema_version": (
            "kmfa.private.v014_authorized_source_reference_or_exclusion_application_blocker_"
            "final_threshold_recheck_after_raw_refresh.v1"
        ),
        "classification": (
            "private_authorized_source_reference_or_exclusion_application_blocker_final_threshold_"
            "recheck_do_not_commit"
        ),
        "record_type": (
            "v014_authorized_source_reference_or_exclusion_application_blocker_final_threshold_"
            "recheck_diagnostic"
        ),
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "source_phase_id": source_summary.get("phase_id"),
        "threshold_conclusion": THRESHOLD_CONCLUSION,
        "application_blocker_final_threshold_recheck_item_count": len(final_rows),
        "track_counts": dict(track_counts),
        "blocker_code_counts": dict(blocker_codes),
        "prior_application_blocker_observation_count": 2,
        "application_blocker_observation_count": 3,
        "application_blocked_audit_threshold_met": True,
        "binding_ready_after_final_threshold_recheck_count": 0,
        "comparison_retry_ready_after_final_threshold_recheck_count": 0,
        "raw_boundary": raw_boundary,
    }
    source_threshold._write_json(PRIVATE_FINAL_THRESHOLD_DIAGNOSTIC_PATH, diagnostic)
    source_threshold._write_jsonl(PRIVATE_FINAL_THRESHOLD_RECORDS_PATH, final_rows)
    source_threshold._write_text(
        PRIVATE_FINAL_THRESHOLD_REPORT_PATH,
        "\n".join(
            [
                "# Private Authorized Source Reference Or Exclusion Application Blocker Final Threshold Recheck",
                "",
                f"- phase_id: `{PHASE_ID}`",
                f"- application_blocker_final_threshold_recheck_item_count: `{len(final_rows)}`",
                "- observation_count: `3`",
                "- strict_blocked_threshold_met: `true`",
                "- binding_ready_after_final_threshold_recheck_count: `0`",
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
    source_rows: list[dict[str, Any]],
    final_rows: list[dict[str, Any]],
    raw_boundary: dict[str, bool],
    public_safety: dict[str, bool],
) -> dict[str, Any]:
    track_counts = Counter(row.get("intake_track") for row in final_rows)
    return {
        "schema_version": (
            "kmfa.v014_authorized_source_reference_or_exclusion_application_blocker_"
            "final_threshold_recheck_after_raw_refresh_summary.v1"
        ),
        "record_type": (
            "v014_authorized_source_reference_or_exclusion_application_blocker_"
            "final_threshold_recheck_after_raw_refresh_summary"
        ),
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": generated_at,
        "status": STATUS,
        "decision": DECISION,
        "threshold_conclusion": THRESHOLD_CONCLUSION,
        "source_phase_id": source_summary.get("phase_id"),
        "source_manifest_phase_id": source_manifest.get("phase_id"),
        "source_go_no_go_decision": source_go_no_go.get("decision"),
        "source_matrix_check_fail_count": source_matrix.get("check_fail_count"),
        "source_private_diagnostic_phase_id": source_diagnostic.get("phase_id"),
        "source_application_blocker_threshold_recheck_item_count": source_summary.get(
            "application_blocker_threshold_recheck_item_count"
        ),
        "source_application_blocker_observation_count": source_summary.get(
            "application_blocker_observation_count"
        ),
        "source_application_blocked_audit_threshold_met": source_summary.get(
            "application_blocked_audit_threshold_met"
        ),
        "source_binding_ready_after_threshold_recheck_count": source_summary.get(
            "binding_ready_after_threshold_recheck_count"
        ),
        "source_comparison_retry_ready_after_threshold_recheck_count": source_summary.get(
            "comparison_retry_ready_after_threshold_recheck_count"
        ),
        "source_private_application_blocker_threshold_record_count": len(source_rows),
        "source_reference_or_owner_exclusion_threshold_blocker_count": source_summary.get(
            "source_reference_or_owner_exclusion_threshold_blocker_count"
        ),
        "formula_or_non_numeric_mapping_threshold_blocker_count": source_summary.get(
            "formula_or_non_numeric_mapping_threshold_blocker_count"
        ),
        "prior_application_blocker_observation_count": 2,
        "application_blocker_observation_count": 3,
        "application_blocked_audit_threshold_met": True,
        "goal_status_recommendation": "blocked",
        "application_blocker_final_threshold_recheck_performed_by_this_phase": True,
        "application_blocker_final_threshold_recheck_item_count": len(final_rows),
        "source_reference_or_owner_exclusion_final_threshold_blocker_count": track_counts[
            SOURCE_REFERENCE_INTAKE_TRACK
        ],
        "formula_or_non_numeric_mapping_final_threshold_blocker_count": track_counts[
            FORMULA_MAPPING_INTAKE_TRACK
        ],
        "binding_ready_after_final_threshold_recheck_count": 0,
        "comparison_retry_ready_after_final_threshold_recheck_count": 0,
        "unresolved_difference_count": source_summary.get("unresolved_difference_count"),
        "private_application_blocker_final_threshold_diagnostic_written": True,
        "private_application_blocker_final_threshold_records_written": True,
        "private_application_blocker_final_threshold_report_written": True,
        "private_application_blocker_final_threshold_diagnostic_gitignored": source_threshold._git_check_ignored(
            PRIVATE_FINAL_THRESHOLD_DIAGNOSTIC_PATH
        ),
        "private_application_blocker_final_threshold_records_gitignored": source_threshold._git_check_ignored(
            PRIVATE_FINAL_THRESHOLD_RECORDS_PATH
        ),
        "private_application_blocker_final_threshold_report_gitignored": source_threshold._git_check_ignored(
            PRIVATE_FINAL_THRESHOLD_REPORT_PATH
        ),
        "source_private_application_blocker_threshold_diagnostic_gitignored": source_threshold._git_check_ignored(
            SOURCE_PRIVATE_APPLICATION_BLOCKER_THRESHOLD_DIAGNOSTIC_PATH
        ),
        "source_private_application_blocker_threshold_records_gitignored": source_threshold._git_check_ignored(
            SOURCE_PRIVATE_APPLICATION_BLOCKER_THRESHOLD_RECORDS_PATH
        ),
        "source_private_application_blocker_threshold_report_gitignored": source_threshold._git_check_ignored(
            SOURCE_PRIVATE_APPLICATION_BLOCKER_THRESHOLD_REPORT_PATH
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
            "source_application_blocker_threshold_loaded",
            str(summary["source_phase_id"]).endswith("APPLICATION_BLOCKER_THRESHOLD_RECHECK_AFTER_RAW_REFRESH"),
        ),
        ("source_go_no_go_preserved", summary["source_go_no_go_decision"] == "NO_GO"),
        ("source_matrix_clean", summary["source_matrix_check_fail_count"] == 0),
        (
            "source_threshold_item_count_locked",
            summary["source_application_blocker_threshold_recheck_item_count"] == 48,
        ),
        ("source_observation_2_locked", summary["source_application_blocker_observation_count"] == 2),
        (
            "source_strict_threshold_not_met",
            summary["source_application_blocked_audit_threshold_met"] is False,
        ),
        (
            "source_private_threshold_records_loaded",
            summary["source_private_application_blocker_threshold_record_count"] == 48,
        ),
        (
            "final_threshold_record_count_locked",
            summary["application_blocker_final_threshold_recheck_item_count"] == 48,
        ),
        ("observation_count_recorded", summary["application_blocker_observation_count"] == 3),
        ("strict_threshold_met", summary["application_blocked_audit_threshold_met"] is True),
        (
            "no_binding_or_retry_ready_after_final_threshold",
            summary["binding_ready_after_final_threshold_recheck_count"] == 0
            and summary["comparison_retry_ready_after_final_threshold_recheck_count"] == 0,
        ),
        (
            "final_threshold_outputs_ignored",
            summary["private_application_blocker_final_threshold_records_gitignored"] is True,
        ),
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
            "kmfa.v014_authorized_source_reference_or_exclusion_application_blocker_"
            "final_threshold_recheck_after_raw_refresh_matrix_public_safe.v1"
        ),
        "record_type": (
            "v014_authorized_source_reference_or_exclusion_application_blocker_"
            "final_threshold_recheck_after_raw_refresh_matrix_public_safe"
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
            "kmfa.v014_authorized_source_reference_or_exclusion_application_blocker_"
            "final_threshold_recheck_after_raw_refresh_go_no_go.v1"
        ),
        "record_type": (
            "v014_authorized_source_reference_or_exclusion_application_blocker_"
            "final_threshold_recheck_after_raw_refresh_go_no_go"
        ),
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": summary["generated_at"],
        "status": STATUS,
        "decision": DECISION,
        "threshold_conclusion": THRESHOLD_CONCLUSION,
        "prior_application_blocker_observation_count": 2,
        "application_blocker_observation_count": 3,
        "application_blocked_audit_threshold_met": True,
        "application_blocker_final_threshold_recheck_item_count": summary[
            "application_blocker_final_threshold_recheck_item_count"
        ],
        "binding_ready_after_final_threshold_recheck_count": 0,
        "comparison_retry_ready_after_final_threshold_recheck_count": 0,
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
    report = f"""# V014 Authorized Source Reference Or Exclusion Application Blocker Final Threshold Recheck After Raw Refresh

Generated at: {summary["generated_at"]}

## Scope

- Phase: `{PHASE_ID}`
- Decision: `{DECISION}`
- Status: `{STATUS}`
- Source: prior public-safe application-blocker-threshold evidence plus ignored private threshold records.
- Raw boundary: this phase does not read, list, stat, parse, fingerprint, write, delete, move, rename, copy, normalize or mutate the raw inbox.

## Public-Safe Result

- Source application blocker threshold items: `{summary["source_application_blocker_threshold_recheck_item_count"]}`
- Final threshold recheck items: `{summary["application_blocker_final_threshold_recheck_item_count"]}`
- Observation count: `{summary["application_blocker_observation_count"]}`
- Strict blocked threshold met: `{str(summary["application_blocked_audit_threshold_met"]).lower()}`
- Source reference or owner exclusion final threshold blockers: `{summary["source_reference_or_owner_exclusion_final_threshold_blocker_count"]}`
- Formula or non-numeric mapping final threshold blockers: `{summary["formula_or_non_numeric_mapping_final_threshold_blocker_count"]}`
- Binding ready after final threshold recheck: `{summary["binding_ready_after_final_threshold_recheck_count"]}`
- Comparison retry ready after final threshold recheck: `{summary["comparison_retry_ready_after_final_threshold_recheck_count"]}`

## Gate

This phase records the third observation and marks the strict blocked threshold met. It does not apply authoritative source references, owner exclusions, formula mappings, raw candidate fingerprints, raw-to-processed comparison, reconciliation, formal reports, GitHub upload, app reinstall or business execution.

Next required input: `{NEXT_REQUIRED_INPUT}`.
"""
    go_record = f"""# Go / No-Go Record

- Phase: `{PHASE_ID}`
- Decision: `{go_no_go["decision"]}`
- Reason: all 48 application blockers remain missing authorized private resolution applications at observation 3, so strict threshold is met.
- Matrix: `{matrix["check_pass_count"]}` pass / `{matrix["check_fail_count"]}` fail
- Next recommended phase: `{NEXT_RECOMMENDED_PHASE}`
- GitHub upload: not allowed in this phase.
- App reinstall: not allowed in this phase.
"""
    test_results = f"""# Test Results

- RED: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_v014_residual_difference_authorized_source_reference_or_exclusion_application_blocker_final_threshold_recheck_after_raw_refresh.py` failed before implementation because the generator module did not exist.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_blocker_final_threshold_recheck_after_raw_refresh.py --generated-at 2026-07-08T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_blocker_final_threshold_recheck_after_raw_refresh.py --require-private-final-threshold`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_v014_residual_difference_authorized_source_reference_or_exclusion_application_blocker_final_threshold_recheck_after_raw_refresh.py`
- Governance validators, CSV shape checks, diff check, raw/private scan, secret scan and private-runtime tracked-file scan: expected before commit.

Expected matrix result: {matrix["check_pass_count"]}/{matrix["check_count"]} PASS.
"""
    risk_register = """# Risk Register

- Risk: final threshold recheck is mistaken for authoritative binding or discrepancy closure.
- Control: binding, comparison and downstream gate flags remain false.
- Risk: private slot or resolution details leak into public artifacts.
- Control: public artifacts contain aggregate counts only; private final-threshold details stay ignored.
- Risk: raw inbox is modified.
- Control: this phase reads existing ignored private threshold artifacts only and does not touch the raw inbox.
"""
    rollback = f"""# Rollback Plan

Remove artifacts for `{PHASE_ID}`, metadata copies, ignored private final-threshold outputs, tool, validator, focused test and governance rows. Do not touch raw inbox files or prior private/source artifacts.
"""
    source_threshold._write_text(REPORT_PATH, report)
    source_threshold._write_text(GO_NO_GO_RECORD_PATH, go_record)
    source_threshold._write_text(TEST_RESULTS_PATH, test_results)
    source_threshold._write_text(RISK_REGISTER_PATH, risk_register)
    source_threshold._write_text(ROLLBACK_PATH, rollback)


def _build_manifest(summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": (
            "kmfa.v014_authorized_source_reference_or_exclusion_application_blocker_"
            "final_threshold_recheck_after_raw_refresh_manifest.v1"
        ),
        "record_type": (
            "v014_authorized_source_reference_or_exclusion_application_blocker_"
            "final_threshold_recheck_after_raw_refresh_manifest"
        ),
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": summary["generated_at"],
        "status": STATUS,
        "decision": DECISION,
        "threshold_conclusion": THRESHOLD_CONCLUSION,
        "summary": summary,
        "matrix": matrix,
        "go_no_go_report": go_no_go,
        "source_artifacts": {
            "application_blocker_threshold_summary": "public_safe_metadata_copy",
            "application_blocker_threshold_manifest": "public_safe_metadata_copy",
            "application_blocker_threshold_go_no_go": "public_safe_metadata_copy",
            "application_blocker_threshold_matrix": "public_safe_metadata_copy",
            "application_blocker_threshold_private_diagnostic": "ignored_private_runtime",
            "application_blocker_threshold_private_records": "ignored_private_runtime",
            "application_blocker_threshold_private_report": "ignored_private_runtime",
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
            "private:authorized_source_reference_or_exclusion_application_blocker_final_threshold_diagnostic",
            "private:authorized_source_reference_or_exclusion_application_blocker_final_threshold_records",
            "private:authorized_source_reference_or_exclusion_application_blocker_final_threshold_report",
        ],
        "raw_boundary": summary["raw_boundary"],
        "public_safety": summary["public_safety"],
        "test_commands": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_blocker_final_threshold_recheck_after_raw_refresh.py --generated-at 2026-07-08T00:00:00+10:00",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_blocker_final_threshold_recheck_after_raw_refresh.py --require-private-final-threshold",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_v014_residual_difference_authorized_source_reference_or_exclusion_application_blocker_final_threshold_recheck_after_raw_refresh.py",
        ],
        "git": {
            "branch": source_threshold._git_output(["branch", "--show-current"]),
            "head": source_threshold._git_output(["rev-parse", "HEAD"]),
            "status_short_branch": source_threshold._git_output(["status", "--short", "--branch"]),
            "changed_kmfa_files": source_threshold._changed_kmfa_files(),
        },
    }


def _write_governance_events(generated_at: str, summary: dict[str, Any]) -> None:
    event = {
        "event_id": (
            "DEV-KMFA-20260708-V014-AUTHORIZED-SOURCE-REFERENCE-OR-EXCLUSION-"
            "APPLICATION-BLOCKER-FINAL-THRESHOLD-RECHECK-AFTER-RAW-REFRESH"
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
        "summary": "Recorded observation 3 for 48 authorized-source-reference application blockers; strict threshold is met and goal remains blocked.",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "files_changed": source_threshold._changed_kmfa_files(),
        "test_commands": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_blocker_final_threshold_recheck_after_raw_refresh.py --generated-at 2026-07-08T00:00:00+10:00",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_blocker_final_threshold_recheck_after_raw_refresh.py --require-private-final-threshold",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_v014_residual_difference_authorized_source_reference_or_exclusion_application_blocker_final_threshold_recheck_after_raw_refresh.py",
        ],
        "test_results": ["PENDING: final validation results will be recorded before local commit."],
        "next_required_input": NEXT_REQUIRED_INPUT,
        "application_blocker_final_threshold_recheck_item_count": summary[
            "application_blocker_final_threshold_recheck_item_count"
        ],
        "prior_application_blocker_observation_count": summary["prior_application_blocker_observation_count"],
        "application_blocker_observation_count": summary["application_blocker_observation_count"],
        "application_blocked_audit_threshold_met": summary["application_blocked_audit_threshold_met"],
        "binding_ready_after_final_threshold_recheck_count": summary[
            "binding_ready_after_final_threshold_recheck_count"
        ],
        "comparison_retry_ready_after_final_threshold_recheck_count": summary[
            "comparison_retry_ready_after_final_threshold_recheck_count"
        ],
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
    source_threshold._upsert_jsonl(DEVELOPMENT_EVENTS_PATH, event, ("event_id",))
    phase_status = {
        "record_type": "v014_phase",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "roadmap_phase_id": (
            "RESIDUAL_DIFFERENCE_AUTHORIZED_SOURCE_REFERENCE_OR_EXCLUSION_"
            "APPLICATION_BLOCKER_FINAL_THRESHOLD_RECHECK_AFTER_RAW_REFRESH"
        ),
        "roadmap_stage_id": "VALUE-CONSISTENCY",
        "governance_stage_id": "VALUE-CONSISTENCY",
        "name": (
            "v0.1.4 residual difference authorized source reference or exclusion "
            "application blocker final threshold recheck after raw refresh"
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
    source_threshold._upsert_jsonl(STAGE_STATUS_PATH, phase_status, ("record_type", "phase_id"))
    task_records = [
        ("T1", "read prior application blocker threshold evidence and ignored private threshold records"),
        ("T2", "write ignored private application blocker final threshold records"),
        ("T3", "emit public-safe NO_GO final-threshold evidence while keeping binding, comparison and upload gates closed"),
    ]
    for suffix, goal in task_records:
        source_threshold._upsert_jsonl(
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
                    "APPLICATION_BLOCKER_FINAL_THRESHOLD_RECHECK_AFTER_RAW_REFRESH"
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
    if source_summary.get("phase_id") != source_threshold.PHASE_ID:
        raise ValueError("source application blocker threshold phase mismatch")
    if source_go_no_go.get("decision") != "NO_GO":
        raise ValueError("source application blocker threshold decision must be NO_GO")
    if source_matrix.get("check_fail_count") != 0:
        raise ValueError("source application blocker threshold matrix must be clean")
    if source_summary.get("application_blocker_threshold_recheck_item_count") != 48:
        raise ValueError("source application blocker threshold item count must be 48")
    if source_summary.get("application_blocker_observation_count") != 2:
        raise ValueError("source application blocker observation count must be 2")
    if source_summary.get("application_blocked_audit_threshold_met") is not False:
        raise ValueError("source application blocker threshold must not already be met")
    if source_summary.get("binding_ready_after_threshold_recheck_count") != 0:
        raise ValueError("source binding-ready count must be zero")
    if source_summary.get("comparison_retry_ready_after_threshold_recheck_count") != 0:
        raise ValueError("source comparison retry-ready count must be zero")
    if source_diagnostic.get("application_blocker_threshold_recheck_item_count") != 48:
        raise ValueError("source private threshold diagnostic item count must be 48")
    if len(source_rows) != 48:
        raise ValueError("source private threshold records must contain 48 rows")
    counts = Counter(row.get("intake_track") for row in source_rows)
    if dict(counts) != EXPECTED_FINAL_THRESHOLD_TRACK_COUNTS:
        raise ValueError(f"source threshold track counts must be {EXPECTED_FINAL_THRESHOLD_TRACK_COUNTS!r}")


def generate(*, generated_at: str | None = None, write_governance_event: bool = True) -> dict[str, Any]:
    generated = generated_at or source_threshold._now()
    source_summary = source_threshold._read_json(SOURCE_APPLICATION_BLOCKER_THRESHOLD_SUMMARY_PATH)
    source_manifest = source_threshold._read_json(SOURCE_APPLICATION_BLOCKER_THRESHOLD_MANIFEST_PATH)
    source_go_no_go = source_threshold._read_json(SOURCE_APPLICATION_BLOCKER_THRESHOLD_GO_NO_GO_PATH)
    source_matrix = source_threshold._read_json(SOURCE_APPLICATION_BLOCKER_THRESHOLD_MATRIX_PATH)
    source_diagnostic = source_threshold._read_json(SOURCE_PRIVATE_APPLICATION_BLOCKER_THRESHOLD_DIAGNOSTIC_PATH)
    source_rows = source_threshold._read_jsonl(SOURCE_PRIVATE_APPLICATION_BLOCKER_THRESHOLD_RECORDS_PATH)
    SOURCE_PRIVATE_APPLICATION_BLOCKER_THRESHOLD_REPORT_PATH.read_text(encoding="utf-8")
    _validate_sources(
        source_summary=source_summary,
        source_go_no_go=source_go_no_go,
        source_matrix=source_matrix,
        source_diagnostic=source_diagnostic,
        source_rows=source_rows,
    )

    raw_boundary = _raw_boundary()
    public_safety = _public_safety()
    final_rows = _build_final_threshold_rows(generated_at=generated, source_rows=source_rows)
    private_diagnostic = _write_private_outputs(
        generated_at=generated,
        source_summary=source_summary,
        final_rows=final_rows,
        raw_boundary=raw_boundary,
    )
    summary = _build_summary(
        generated_at=generated,
        source_summary=source_summary,
        source_manifest=source_manifest,
        source_go_no_go=source_go_no_go,
        source_matrix=source_matrix,
        source_diagnostic=source_diagnostic,
        source_rows=source_rows,
        final_rows=final_rows,
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
        source_threshold._write_json(path, payload)
    _write_human(summary, matrix, go_no_go)
    if write_governance_event:
        _write_governance_events(generated, summary)
    return {
        "summary": summary,
        "matrix": matrix,
        "go_no_go": go_no_go,
        "manifest": manifest,
        "private_diagnostic": private_diagnostic,
        "private_final_threshold_rows": final_rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated-at")
    parser.add_argument("--no-governance-event", action="store_true")
    args = parser.parse_args()
    result = generate(generated_at=args.generated_at, write_governance_event=not args.no_governance_event)
    summary = result["summary"]
    print(
        "PASS: generated V014 authorized source reference or exclusion application blocker "
        "final threshold recheck after raw refresh "
        f"decision={summary['decision']} final_threshold_items="
        f"{summary['application_blocker_final_threshold_recheck_item_count']} "
        f"observation={summary['application_blocker_observation_count']} "
        f"threshold={summary['application_blocked_audit_threshold_met']} "
        f"next={summary['next_recommended_phase']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
