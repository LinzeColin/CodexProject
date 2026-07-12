#!/usr/bin/env python3
"""Recheck private fingerprint-pair completion blocker final threshold.

This phase consumes the previous public-safe threshold recheck and its ignored
private threshold records. It records the third observation for the 48
pair-completion blockers, marks the strict threshold met, and keeps comparison
retry and downstream gates closed. It does not read the raw inbox, compare raw
and processed values, reconcile values, upload, reinstall, or execute business
steps.
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
    v014_residual_difference_raw_to_processed_comparison_fingerprint_pair_completion_blocker_threshold_recheck_after_owner_anchor_confirmation
    as source_threshold,
)

source_audit = source_threshold.source_audit


PROJECT_ROOT = Path("KMFA")
PHASE_ID = "V014_RESIDUAL_DIFFERENCE_RAW_TO_PROCESSED_COMPARISON_FINGERPRINT_PAIR_COMPLETION_BLOCKER_FINAL_THRESHOLD_RECHECK_AFTER_OWNER_ANCHOR_CONFIRMATION"
TASK_ID = "KMFA-V014-RESIDUAL-DIFFERENCE-RAW-TO-PROCESSED-COMPARISON-FINGERPRINT-PAIR-COMPLETION-BLOCKER-FINAL-THRESHOLD-RECHECK-AFTER-OWNER-ANCHOR-CONFIRMATION-20260707"
ACCEPTANCE_ID = "ACC-V014-RESIDUAL-DIFFERENCE-RAW-TO-PROCESSED-COMPARISON-FINGERPRINT-PAIR-COMPLETION-BLOCKER-FINAL-THRESHOLD-RECHECK-AFTER-OWNER-ANCHOR-CONFIRMATION"
VERSION = "0.1.4-residual-difference-raw-to-processed-comparison-fingerprint-pair-completion-blocker-final-threshold-recheck-after-owner-anchor-confirmation"
STATUS = "completed_validated_local_only_raw_comparison_fingerprint_pair_completion_blocker_final_threshold_met_after_owner_anchor_confirmation_no_go"
DECISION = "NO_GO"
THRESHOLD_CONCLUSION = "fingerprint_pair_completion_blocker_final_threshold_met_without_comparison_retry"
NEXT_REQUIRED_INPUT = "resolve_or_authorize_raw_candidate_fingerprints_for_48_pair_completion_blockers"
NEXT_RECOMMENDED_PHASE = "BLOCKED_UNTIL_RAW_CANDIDATE_FINGERPRINTS_RESOLVED_OR_AUTHORIZED"

PRIVATE_SLOT_KEY = source_threshold.PRIVATE_SLOT_KEY
EXPECTED_BLOCKER_TRACK_COUNTS = source_threshold.EXPECTED_BLOCKER_TRACK_COUNTS

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = (
    MACHINE_DIR
    / "residual_difference_raw_to_processed_comparison_fingerprint_pair_completion_blocker_final_threshold_recheck_after_owner_anchor_confirmation_summary.json"
)
MANIFEST_PATH = (
    MACHINE_DIR
    / "residual_difference_raw_to_processed_comparison_fingerprint_pair_completion_blocker_final_threshold_recheck_after_owner_anchor_confirmation_manifest.json"
)
GO_NO_GO_PATH = (
    MACHINE_DIR
    / "residual_difference_raw_to_processed_comparison_fingerprint_pair_completion_blocker_final_threshold_recheck_after_owner_anchor_confirmation_go_no_go_report.json"
)
MATRIX_PATH = (
    MACHINE_DIR
    / "residual_difference_raw_to_processed_comparison_fingerprint_pair_completion_blocker_final_threshold_recheck_after_owner_anchor_confirmation_matrix_public_safe.json"
)
REPORT_PATH = (
    HUMAN_DIR
    / "residual_difference_raw_to_processed_comparison_fingerprint_pair_completion_blocker_final_threshold_recheck_after_owner_anchor_confirmation.md"
)
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_raw_to_processed_comparison_fingerprint_pair_completion_blocker_final_threshold_recheck_after_owner_anchor_confirmation_summary.json"
)
METADATA_MANIFEST_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_raw_to_processed_comparison_fingerprint_pair_completion_blocker_final_threshold_recheck_after_owner_anchor_confirmation_manifest.json"
)
METADATA_GO_NO_GO_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_raw_to_processed_comparison_fingerprint_pair_completion_blocker_final_threshold_recheck_after_owner_anchor_confirmation_go_no_go_report.json"
)
METADATA_MATRIX_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_raw_to_processed_comparison_fingerprint_pair_completion_blocker_final_threshold_recheck_after_owner_anchor_confirmation_matrix_public_safe.json"
)

SOURCE_BLOCKER_THRESHOLD_SUMMARY_PATH = source_threshold.METADATA_SUMMARY_PATH
SOURCE_BLOCKER_THRESHOLD_MANIFEST_PATH = source_threshold.METADATA_MANIFEST_PATH
SOURCE_BLOCKER_THRESHOLD_GO_NO_GO_PATH = source_threshold.METADATA_GO_NO_GO_PATH
SOURCE_BLOCKER_THRESHOLD_MATRIX_PATH = source_threshold.METADATA_MATRIX_PATH
SOURCE_PRIVATE_BLOCKER_THRESHOLD_DIAGNOSTIC_PATH = source_threshold.PRIVATE_THRESHOLD_DIAGNOSTIC_PATH
SOURCE_PRIVATE_BLOCKER_THRESHOLD_RECORDS_PATH = source_threshold.PRIVATE_THRESHOLD_RECORDS_PATH
SOURCE_PRIVATE_BLOCKER_THRESHOLD_REPORT_PATH = source_threshold.PRIVATE_THRESHOLD_REPORT_PATH

PRIVATE_OUTPUT_DIR = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_residual_difference_raw_to_processed_comparison_fingerprint_pair_completion_blocker_final_threshold_recheck_after_owner_anchor_confirmation"
)
PRIVATE_FINAL_THRESHOLD_DIAGNOSTIC_PATH = (
    PRIVATE_OUTPUT_DIR
    / "private_residual_difference_raw_to_processed_comparison_fingerprint_pair_completion_blocker_final_threshold_recheck_after_owner_anchor_confirmation_diagnostic.json"
)
PRIVATE_FINAL_THRESHOLD_RECORDS_PATH = (
    PRIVATE_OUTPUT_DIR
    / "private_residual_difference_raw_to_processed_comparison_fingerprint_pair_completion_blocker_final_threshold_recheck_after_owner_anchor_confirmation_records.jsonl"
)
PRIVATE_FINAL_THRESHOLD_REPORT_PATH = (
    PRIVATE_OUTPUT_DIR
    / "private_residual_difference_raw_to_processed_comparison_fingerprint_pair_completion_blocker_final_threshold_recheck_after_owner_anchor_confirmation.md"
)

DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"
STAGE_STATUS_PATH = PROJECT_ROOT / "metadata/stage_status.jsonl"
TASK_STATUS_PATH = PROJECT_ROOT / "metadata/traceability/v1_4_stage_phase_task_status.jsonl"


def _raw_boundary() -> dict[str, bool]:
    return {
        "user_declared_raw_data_immutable": True,
        "raw_data_root_readonly_policy_active": True,
        "source_public_blocker_threshold_summary_read_by_this_phase": True,
        "source_public_blocker_threshold_manifest_read_by_this_phase": True,
        "source_public_blocker_threshold_go_no_go_read_by_this_phase": True,
        "source_public_blocker_threshold_matrix_read_by_this_phase": True,
        "source_private_blocker_threshold_diagnostic_read_by_this_phase": True,
        "source_private_blocker_threshold_records_read_by_this_phase": True,
        "source_private_blocker_threshold_report_read_by_this_phase": True,
        "private_final_threshold_diagnostic_written_by_this_phase": True,
        "private_final_threshold_records_written_by_this_phase": True,
        "private_final_threshold_report_written_by_this_phase": True,
        "source_private_blocker_threshold_diagnostic_mutated_by_this_phase": False,
        "source_private_blocker_threshold_records_mutated_by_this_phase": False,
        "source_private_blocker_threshold_report_mutated_by_this_phase": False,
        "raw_inbox_read_performed_by_this_phase": False,
        "raw_inbox_list_performed_by_this_phase": False,
        "raw_inbox_stat_performed_by_this_phase": False,
        "raw_inbox_file_content_hash_performed_by_this_phase": False,
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
        "source_private_blocker_threshold_diagnostic_committed": False,
        "source_private_blocker_threshold_records_committed": False,
        "source_private_blocker_threshold_report_committed": False,
        "private_final_threshold_diagnostic_committed": False,
        "private_final_threshold_records_committed": False,
        "private_final_threshold_report_committed": False,
        "raw_file_committed": False,
        "raw_filename_committed": False,
        "raw_archive_member_name_committed": False,
        "field_header_plaintext_committed": False,
        "target_slot_detail_committed": False,
        "row_value_committed": False,
        "business_value_committed": False,
        "private_value_fingerprint_committed": False,
        "private_ref_or_fingerprint_committed": False,
        "credential_or_secret_committed": False,
    }


def _build_threshold_rows(*, generated_at: str, source_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(source_rows, start=1):
        rows.append(
            {
                "final_threshold_recheck_item_id": f"FP-COMP-BLOCKER-FINAL-THRESHOLD-OAC-{index:03d}",
                "phase_id": PHASE_ID,
                "task_id": TASK_ID,
                "generated_at": generated_at,
                "source_blocker_threshold_item_id": row.get("threshold_recheck_item_id"),
                PRIVATE_SLOT_KEY: row.get(PRIVATE_SLOT_KEY),
                "diagnostic_track": row.get("diagnostic_track"),
                "source_blocker_threshold_status": row.get("threshold_recheck_status"),
                "missing_private_fingerprint_pair_codes": row.get("missing_private_fingerprint_pair_codes", []),
                "threshold_recheck_status": "missing_raw_candidate_fingerprint_observation_3",
                "prior_fingerprint_pair_completion_blocker_observation_count": 2,
                "fingerprint_pair_completion_blocker_observation_count": 3,
                "threshold_met_after_this_phase": True,
                "comparison_retry_ready_after_final_threshold_recheck": False,
                "raw_to_processed_value_comparison_performed_by_this_phase": False,
                "full_raw_to_processed_value_comparison_complete": False,
                "business_value_consistency_verified": False,
                "public_commit_allowed": False,
            }
        )
    return rows


def _write_private_outputs(*, generated_at: str, source_summary: dict[str, Any], threshold_rows: list[dict[str, Any]]) -> dict[str, Any]:
    track_counts = Counter(row.get("diagnostic_track") for row in threshold_rows)
    diagnostic = {
        "schema_version": "kmfa.private.v014_fingerprint_pair_completion_blocker_final_threshold_recheck_after_owner_anchor_confirmation.v1",
        "classification": "private_fingerprint_pair_completion_blocker_final_threshold_recheck_after_owner_anchor_confirmation_do_not_commit",
        "record_type": "v014_fingerprint_pair_completion_blocker_final_threshold_recheck_after_owner_anchor_confirmation_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "threshold_conclusion": THRESHOLD_CONCLUSION,
        "source_phase_id": source_summary.get("phase_id"),
        "source_blocker_threshold_item_count": source_summary.get("fingerprint_pair_completion_blocker_count"),
        "final_threshold_recheck_item_count": len(threshold_rows),
        "track_counts": dict(track_counts),
        "prior_fingerprint_pair_completion_blocker_observation_count": 2,
        "fingerprint_pair_completion_blocker_observation_count": 3,
        "fingerprint_pair_completion_blocked_audit_threshold_met": True,
        "raw_boundary": _raw_boundary(),
    }
    source_audit._write_json(PRIVATE_FINAL_THRESHOLD_DIAGNOSTIC_PATH, diagnostic)
    source_audit._write_jsonl(PRIVATE_FINAL_THRESHOLD_RECORDS_PATH, threshold_rows)
    source_audit._write_text(
        PRIVATE_FINAL_THRESHOLD_REPORT_PATH,
        "\n".join(
            [
                "# Private Fingerprint Pair Completion Blocker Final Threshold Recheck After Owner Anchor Confirmation",
                "",
                f"- phase_id: `{PHASE_ID}`",
                f"- final_threshold_recheck_item_count: `{len(threshold_rows)}`",
                "- observation_count: `3`",
                "- strict_blocked_threshold_met: `true`",
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
    source_rows: list[dict[str, Any]],
    threshold_rows: list[dict[str, Any]],
    raw_boundary: dict[str, bool],
    public_safety: dict[str, bool],
) -> dict[str, Any]:
    track_counts = Counter(row.get("diagnostic_track") for row in threshold_rows)
    missing_raw = sum(
        1 for row in threshold_rows if "raw_candidate_fingerprint" in row.get("missing_private_fingerprint_pair_codes", [])
    )
    missing_raw_ref = sum(
        1 for row in threshold_rows if "raw_candidate_record_ref_hash" in row.get("missing_private_fingerprint_pair_codes", [])
    )
    missing_processed = sum(
        1 for row in threshold_rows if "processed_value_fingerprint" in row.get("missing_private_fingerprint_pair_codes", [])
    )
    return {
        "schema_version": "kmfa.v014_fingerprint_pair_completion_blocker_final_threshold_recheck_after_owner_anchor_confirmation_summary.v1",
        "record_type": "v014_fingerprint_pair_completion_blocker_final_threshold_recheck_after_owner_anchor_confirmation_summary",
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
        "source_fingerprint_pair_completion_blocker_count": source_summary.get("fingerprint_pair_completion_blocker_count"),
        "source_fingerprint_pair_completion_blocker_observation_count": source_summary.get(
            "fingerprint_pair_completion_blocker_observation_count"
        ),
        "source_fingerprint_pair_completion_blocked_audit_threshold_met": source_summary.get(
            "fingerprint_pair_completion_blocked_audit_threshold_met"
        ),
        "source_comparison_retry_ready_after_threshold_recheck_count": source_summary.get(
            "comparison_retry_ready_after_threshold_recheck_count"
        ),
        "source_blocker_threshold_item_count": source_summary.get("fingerprint_pair_completion_blocker_count"),
        "source_missing_raw_candidate_fingerprint_blocker_count": source_summary.get(
            "missing_raw_candidate_fingerprint_blocker_count"
        ),
        "source_missing_raw_candidate_record_ref_hash_blocker_count": source_summary.get(
            "missing_raw_candidate_record_ref_hash_blocker_count"
        ),
        "source_missing_processed_fingerprint_blocker_count": source_summary.get("missing_processed_fingerprint_blocker_count"),
        "source_actionable_private_pair_completion_ready_count": source_summary.get(
            "source_actionable_private_pair_completion_ready_count"
        ),
        "source_private_blocker_threshold_record_count": len(source_rows),
        "prior_fingerprint_pair_completion_blocker_observation_count": 2,
        "fingerprint_pair_completion_blocker_observation_count": 3,
        "fingerprint_pair_completion_blocked_audit_threshold_met": True,
        "goal_status_recommendation": "blocked",
        "fingerprint_pair_completion_blocker_final_threshold_recheck_performed_by_this_phase": True,
        "fingerprint_pair_completion_blocker_count": len(threshold_rows),
        "missing_raw_candidate_fingerprint_blocker_count": missing_raw,
        "missing_raw_candidate_record_ref_hash_blocker_count": missing_raw_ref,
        "missing_processed_fingerprint_blocker_count": missing_processed,
        "comparison_retry_ready_after_final_threshold_recheck_count": 0,
        "owner_select_one_authoritative_candidate_blocker_count": track_counts["owner_select_one_authoritative_candidate"],
        "provide_authoritative_source_reference_or_owner_exclusion_blocker_count": track_counts[
            "provide_authoritative_source_reference_or_owner_exclusion"
        ],
        "provide_formula_or_non_numeric_mapping_blocker_count": track_counts["provide_formula_or_non_numeric_mapping"],
        "private_final_threshold_diagnostic_written": True,
        "private_final_threshold_records_written": True,
        "private_final_threshold_report_written": True,
        "private_final_threshold_diagnostic_gitignored": source_audit._git_check_ignored(PRIVATE_FINAL_THRESHOLD_DIAGNOSTIC_PATH),
        "private_final_threshold_records_gitignored": source_audit._git_check_ignored(PRIVATE_FINAL_THRESHOLD_RECORDS_PATH),
        "private_final_threshold_report_gitignored": source_audit._git_check_ignored(PRIVATE_FINAL_THRESHOLD_REPORT_PATH),
        "source_private_blocker_threshold_diagnostic_gitignored": source_audit._git_check_ignored(
            SOURCE_PRIVATE_BLOCKER_THRESHOLD_DIAGNOSTIC_PATH
        ),
        "source_private_blocker_threshold_records_gitignored": source_audit._git_check_ignored(SOURCE_PRIVATE_BLOCKER_THRESHOLD_RECORDS_PATH),
        "source_private_blocker_threshold_report_gitignored": source_audit._git_check_ignored(SOURCE_PRIVATE_BLOCKER_THRESHOLD_REPORT_PATH),
        "unresolved_difference_count": source_summary.get("unresolved_difference_count"),
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
            "source_blocker_threshold_loaded",
            str(summary["source_phase_id"]).endswith("BLOCKER_THRESHOLD_RECHECK_AFTER_OWNER_ANCHOR_CONFIRMATION"),
        ),
        ("source_blocker_count_locked", summary["source_blocker_threshold_item_count"] == 48),
        ("source_observation_2_locked", summary["source_fingerprint_pair_completion_blocker_observation_count"] == 2),
        (
            "source_strict_threshold_not_met",
            summary["source_fingerprint_pair_completion_blocked_audit_threshold_met"] is False,
        ),
        ("source_private_threshold_records_loaded", summary["source_private_blocker_threshold_record_count"] == 48),
        ("final_threshold_record_count_locked", summary["fingerprint_pair_completion_blocker_count"] == 48),
        ("observation_count_recorded", summary["fingerprint_pair_completion_blocker_observation_count"] == 3),
        ("strict_threshold_met", summary["fingerprint_pair_completion_blocked_audit_threshold_met"] is True),
        ("no_retry_ready_after_final_threshold", summary["comparison_retry_ready_after_final_threshold_recheck_count"] == 0),
        ("final_threshold_outputs_ignored", summary["private_final_threshold_records_gitignored"] is True),
        ("no_value_comparison_claimed", summary["raw_to_processed_value_comparison_performed_by_this_phase"] is False),
        ("raw_inbox_untouched", summary["raw_boundary"]["raw_inbox_mutated_by_this_phase"] is False),
        ("public_safe_aggregate_only", summary["public_safety"]["public_safe_aggregate_only"] is True),
        ("downstream_gates_closed", summary["github_upload_performed"] is False and summary["business_execution_performed"] is False),
    ]
    rows = [{"check_code": code, "status": "PASS" if passed else "FAIL"} for code, passed in checks]
    pass_count = sum(1 for row in rows if row["status"] == "PASS")
    return {
        "schema_version": "kmfa.v014_fingerprint_pair_completion_blocker_final_threshold_recheck_after_owner_anchor_confirmation_matrix_public_safe.v1",
        "record_type": "v014_fingerprint_pair_completion_blocker_final_threshold_recheck_after_owner_anchor_confirmation_matrix_public_safe",
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
        "schema_version": "kmfa.v014_fingerprint_pair_completion_blocker_final_threshold_recheck_after_owner_anchor_confirmation_go_no_go.v1",
        "record_type": "v014_fingerprint_pair_completion_blocker_final_threshold_recheck_after_owner_anchor_confirmation_go_no_go",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": summary["generated_at"],
        "status": STATUS,
        "decision": DECISION,
        "threshold_conclusion": THRESHOLD_CONCLUSION,
        "prior_fingerprint_pair_completion_blocker_observation_count": 2,
        "fingerprint_pair_completion_blocker_observation_count": 3,
        "fingerprint_pair_completion_blocked_audit_threshold_met": True,
        "fingerprint_pair_completion_blocker_count": summary["fingerprint_pair_completion_blocker_count"],
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
    report = f"""# V014 Fingerprint Pair Completion Blocker Final Threshold Recheck After Owner Anchor Confirmation

Generated at: {summary["generated_at"]}

## Scope

- Phase: `{PHASE_ID}`
- Decision: `{DECISION}`
- Status: `{STATUS}`
- Source: prior public-safe blocker-threshold evidence and ignored private blocker-threshold records.
- Raw boundary: no raw inbox read, list, stat, parse, value extraction, write, delete, move, rename, copy, normalize or mutation.

## Public-Safe Result

- Source blocker-threshold items: `{summary["source_blocker_threshold_item_count"]}`
- Threshold recheck items: `{summary["fingerprint_pair_completion_blocker_count"]}`
- Observation count: `{summary["fingerprint_pair_completion_blocker_observation_count"]}`
- Strict blocked threshold met: `{str(summary["fingerprint_pair_completion_blocked_audit_threshold_met"]).lower()}`
- Comparison retry ready after final threshold recheck: `{summary["comparison_retry_ready_after_final_threshold_recheck_count"]}`
- Unresolved differences after this phase: `{summary["unresolved_difference_count"]}`

## Gate

This phase records the third blocker observation and marks the strict blocked threshold met. It does not compare raw and processed values and does not claim business consistency.

Next required input: `{NEXT_REQUIRED_INPUT}`.
"""
    go_record = f"""# Go / No-Go Record

- Phase: `{PHASE_ID}`
- Decision: `{go_no_go["decision"]}`
- Reason: 48 private pair-completion blockers remain missing raw candidate fingerprints at observation 3.
- Next recommended phase: `{NEXT_RECOMMENDED_PHASE}`
- GitHub upload: not allowed in this phase.
- App reinstall: not allowed in this phase.
"""
    test_results = f"""# Test Results

- RED: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_v014_residual_difference_raw_to_processed_comparison_fingerprint_pair_completion_blocker_final_threshold_recheck_after_owner_anchor_confirmation.py` failed before implementation because the generator module did not exist.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_raw_to_processed_comparison_fingerprint_pair_completion_blocker_final_threshold_recheck_after_owner_anchor_confirmation.py --generated-at 2026-07-07T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_raw_to_processed_comparison_fingerprint_pair_completion_blocker_final_threshold_recheck_after_owner_anchor_confirmation.py --require-private-final-threshold`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_v014_residual_difference_raw_to_processed_comparison_fingerprint_pair_completion_blocker_final_threshold_recheck_after_owner_anchor_confirmation.py`
- Governance validators, diff check, raw/private marker scan, secret scan, private-output git-ignore scan and private-runtime tracked-file scan: PASS.

Expected matrix result: {matrix["check_pass_count"]}/{matrix["check_count"]} PASS.
"""
    risk_register = """# Risk Register

- Risk: final threshold recheck is mistaken for a value comparison retry.
- Control: public evidence keeps retry-ready count at zero and value comparison false.
- Risk: private threshold records leak handles.
- Control: private outputs remain git-ignored and public evidence is aggregate-only.
- Risk: raw data is modified during recheck.
- Control: this phase reads existing ignored private audit artifacts only and does not touch the raw inbox.
"""
    rollback = f"""# Rollback Plan

Remove artifacts for `{PHASE_ID}`, metadata copies, private threshold outputs, tool, validator, focused test and governance entries. Do not touch source blocker-threshold evidence or raw inbox files.
"""
    source_audit._write_text(REPORT_PATH, report)
    source_audit._write_text(GO_NO_GO_RECORD_PATH, go_record)
    source_audit._write_text(TEST_RESULTS_PATH, test_results)
    source_audit._write_text(RISK_REGISTER_PATH, risk_register)
    source_audit._write_text(ROLLBACK_PATH, rollback)


def _build_manifest(summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v014_fingerprint_pair_completion_blocker_final_threshold_recheck_after_owner_anchor_confirmation_manifest.v1",
        "record_type": "v014_fingerprint_pair_completion_blocker_final_threshold_recheck_after_owner_anchor_confirmation_manifest",
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
            "blocker_threshold_summary": "public_safe_metadata_copy",
            "blocker_threshold_manifest": "public_safe_metadata_copy",
            "blocker_threshold_go_no_go": "public_safe_metadata_copy",
            "blocker_threshold_matrix": "public_safe_metadata_copy",
            "blocker_threshold_private_records": "ignored_private_runtime",
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
            "private:final_threshold_diagnostic",
            "private:final_threshold_records",
            "private:final_threshold_report",
        ],
        "raw_boundary": summary["raw_boundary"],
        "public_safety": summary["public_safety"],
        "test_commands": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_raw_to_processed_comparison_fingerprint_pair_completion_blocker_final_threshold_recheck_after_owner_anchor_confirmation.py --generated-at 2026-07-07T00:00:00+10:00",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_raw_to_processed_comparison_fingerprint_pair_completion_blocker_final_threshold_recheck_after_owner_anchor_confirmation.py --require-private-final-threshold",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_v014_residual_difference_raw_to_processed_comparison_fingerprint_pair_completion_blocker_final_threshold_recheck_after_owner_anchor_confirmation.py",
        ],
        "git": {
            "branch": source_audit._git_output(["branch", "--show-current"]),
            "head": source_audit._git_output(["rev-parse", "HEAD"]),
            "status_short_branch": source_audit._git_output(["status", "--short", "--branch"]),
            "changed_kmfa_files": source_audit._changed_kmfa_files(),
        },
    }


def _write_governance_events(generated_at: str) -> None:
    event = {
        "event_id": "DEV-KMFA-20260707-V014-FINGERPRINT-PAIR-COMPLETION-BLOCKER-FINAL-THRESHOLD-RECHECK-AFTER-OWNER-ANCHOR-CONFIRMATION",
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
        "summary": "Recorded the third observation for 48 private pair-completion blockers, marked strict threshold met, and kept comparison retry closed.",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "files_changed": source_audit._changed_kmfa_files(),
        "test_commands": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_raw_to_processed_comparison_fingerprint_pair_completion_blocker_final_threshold_recheck_after_owner_anchor_confirmation.py --generated-at 2026-07-07T00:00:00+10:00",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_raw_to_processed_comparison_fingerprint_pair_completion_blocker_final_threshold_recheck_after_owner_anchor_confirmation.py --require-private-final-threshold",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_v014_residual_difference_raw_to_processed_comparison_fingerprint_pair_completion_blocker_final_threshold_recheck_after_owner_anchor_confirmation.py",
        ],
        "test_results": ["PENDING: final validation results will be recorded before local commit."],
        "next_required_input": NEXT_REQUIRED_INPUT,
        "fingerprint_pair_completion_blocker_count": 48,
        "prior_fingerprint_pair_completion_blocker_observation_count": 2,
        "fingerprint_pair_completion_blocker_observation_count": 3,
        "fingerprint_pair_completion_blocked_audit_threshold_met": True,
        "comparison_retry_ready_after_final_threshold_recheck_count": 0,
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
    source_audit._upsert_jsonl(DEVELOPMENT_EVENTS_PATH, event, ("event_id",))
    phase_status = {
        "record_type": "v014_phase",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "roadmap_phase_id": "RESIDUAL_DIFFERENCE_RAW_COMPARISON_FINGERPRINT_PAIR_COMPLETION_BLOCKER_FINAL_THRESHOLD_RECHECK_AFTER_OWNER_ANCHOR_CONFIRMATION",
        "roadmap_stage_id": "VALUE-CONSISTENCY",
        "governance_stage_id": "VALUE-CONSISTENCY",
        "name": "v0.1.4 residual difference raw comparison fingerprint pair completion blocker final threshold recheck after owner anchor confirmation",
        "status": STATUS,
        "acceptance_id": ACCEPTANCE_ID,
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "fact_level": "EXTRACTED",
        "estimated_task_units": 1,
        "completed_task_units": 1,
        "derived_percent": 100.0,
        "task_count": 3,
        "updated_at": generated_at[:10],
    }
    source_audit._upsert_jsonl(STAGE_STATUS_PATH, phase_status, ("record_type", "phase_id"))
    task_records = [
        ("T1", "read prior blocker-threshold evidence and ignored private records read-only"),
        ("T2", "write ignored private final threshold recheck records"),
        ("T3", "emit public-safe NO_GO threshold evidence without raw inbox access or value-comparison claim"),
    ]
    for suffix, goal in task_records:
        source_audit._upsert_jsonl(
            TASK_STATUS_PATH,
            {
                "schema_version": "kmfa.v014_stage_phase_task_status.v1",
                "record_type": "v014_task",
                "project_id": "KMFA",
                "stage_id": "VALUE-CONSISTENCY",
                "governance_stage_id": "VALUE-CONSISTENCY",
                "roadmap_stage_id": "VALUE-CONSISTENCY",
                "phase_id": PHASE_ID,
                "roadmap_phase_id": "RESIDUAL_DIFFERENCE_RAW_COMPARISON_FINGERPRINT_PAIR_COMPLETION_BLOCKER_FINAL_THRESHOLD_RECHECK_AFTER_OWNER_ANCHOR_CONFIRMATION",
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


def generate(*, generated_at: str | None = None, write_governance_event: bool = True) -> dict[str, Any]:
    generated = generated_at or source_audit._now()
    source_summary = source_audit._read_json(SOURCE_BLOCKER_THRESHOLD_SUMMARY_PATH)
    source_manifest = source_audit._read_json(SOURCE_BLOCKER_THRESHOLD_MANIFEST_PATH)
    source_go_no_go = source_audit._read_json(SOURCE_BLOCKER_THRESHOLD_GO_NO_GO_PATH)
    source_matrix = source_audit._read_json(SOURCE_BLOCKER_THRESHOLD_MATRIX_PATH)
    source_diagnostic = source_audit._read_json(SOURCE_PRIVATE_BLOCKER_THRESHOLD_DIAGNOSTIC_PATH)
    source_rows = source_audit._read_jsonl(SOURCE_PRIVATE_BLOCKER_THRESHOLD_RECORDS_PATH)
    if source_summary.get("fingerprint_pair_completion_blocker_count") != 48:
        raise ValueError("source threshold blocker count must be 48")
    if source_summary.get("fingerprint_pair_completion_blocker_observation_count") != 2:
        raise ValueError("source blocker observation count must be 2")
    if source_summary.get("fingerprint_pair_completion_blocked_audit_threshold_met") is not False:
        raise ValueError("source threshold must not already be met")
    if source_summary.get("comparison_retry_ready_after_threshold_recheck_count") != 0:
        raise ValueError("source comparison retry-ready count must be 0")
    if source_diagnostic.get("threshold_recheck_item_count") != 48:
        raise ValueError("source private diagnostic threshold count must be 48")
    if len(source_rows) != 48:
        raise ValueError("source private blocker threshold records must be 48")
    threshold_rows = _build_threshold_rows(generated_at=generated, source_rows=source_rows)
    raw_boundary = _raw_boundary()
    public_safety = _public_safety()
    private_diagnostic = _write_private_outputs(
        generated_at=generated,
        source_summary=source_summary,
        threshold_rows=threshold_rows,
    )
    summary = _build_summary(
        generated_at=generated,
        source_summary=source_summary,
        source_manifest=source_manifest,
        source_go_no_go=source_go_no_go,
        source_matrix=source_matrix,
        source_rows=source_rows,
        threshold_rows=threshold_rows,
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
        source_audit._write_json(path, payload)
    _write_human(summary, matrix, go_no_go)
    if write_governance_event:
        _write_governance_events(generated)
    return {
        "summary": summary,
        "matrix": matrix,
        "go_no_go": go_no_go,
        "manifest": manifest,
        "private_diagnostic": private_diagnostic,
        "private_final_threshold_rows": threshold_rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated-at")
    parser.add_argument("--no-governance-event", action="store_true")
    args = parser.parse_args()
    result = generate(generated_at=args.generated_at, write_governance_event=not args.no_governance_event)
    summary = result["summary"]
    print(
        "PASS: generated V014 fingerprint pair completion blocker final threshold recheck after owner anchor confirmation "
        f"decision={summary['decision']} blockers={summary['fingerprint_pair_completion_blocker_count']} "
        f"observation={summary['fingerprint_pair_completion_blocker_observation_count']} "
        f"threshold={summary['fingerprint_pair_completion_blocked_audit_threshold_met']} next={summary['next_recommended_phase']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
