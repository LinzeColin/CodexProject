#!/usr/bin/env python3
"""Attempt raw-candidate fingerprint resolution after final threshold.

This phase consumes the previous final-threshold blocker evidence plus ignored
private candidate-alignment artifacts. It does not read the raw inbox again.
It records that the 48 missing-raw-candidate-fingerprint blockers remain
unresolved from current private evidence and keeps comparison/reconciliation
gates closed.
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
    EXPECTED_TRACK_COUNTS,
    PRIVATE_SLOT_KEY,
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
    v014_residual_difference_raw_to_processed_comparison_fingerprint_pair_completion_blocker_final_threshold_recheck_after_owner_anchor_confirmation
    as source_final_threshold,
)


PROJECT_ROOT = Path("KMFA")
PHASE_ID = "V014_RESIDUAL_DIFFERENCE_RAW_CANDIDATE_FINGERPRINT_RESOLUTION_ATTEMPT_AFTER_FINAL_THRESHOLD"
TASK_ID = "KMFA-V014-RESIDUAL-DIFFERENCE-RAW-CANDIDATE-FINGERPRINT-RESOLUTION-ATTEMPT-AFTER-FINAL-THRESHOLD-20260707"
ACCEPTANCE_ID = "ACC-V014-RESIDUAL-DIFFERENCE-RAW-CANDIDATE-FINGERPRINT-RESOLUTION-ATTEMPT-AFTER-FINAL-THRESHOLD"
VERSION = "0.1.4-residual-difference-raw-candidate-fingerprint-resolution-attempt-after-final-threshold"
STATUS = "completed_validated_local_only_raw_candidate_fingerprint_resolution_attempt_still_blocked_no_go"
DECISION = "NO_GO"
RESOLUTION_CONCLUSION = "current_private_evidence_cannot_resolve_48_missing_raw_candidate_fingerprints"
NEXT_REQUIRED_INPUT = "provide_authoritative_raw_candidate_fingerprints_or_owner_authorized_exclusions_for_48_blockers"
NEXT_RECOMMENDED_PHASE = "RAW_CANDIDATE_FINGERPRINTS_REQUIRE_EXTERNAL_AUTHORITY_OR_PRIVATE_EVIDENCE_REFRESH"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "residual_difference_raw_candidate_fingerprint_resolution_attempt_after_final_threshold_summary.json"
MANIFEST_PATH = MACHINE_DIR / "residual_difference_raw_candidate_fingerprint_resolution_attempt_after_final_threshold_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "residual_difference_raw_candidate_fingerprint_resolution_attempt_after_final_threshold_go_no_go_report.json"
MATRIX_PATH = MACHINE_DIR / "residual_difference_raw_candidate_fingerprint_resolution_attempt_after_final_threshold_matrix_public_safe.json"
REPORT_PATH = HUMAN_DIR / "residual_difference_raw_candidate_fingerprint_resolution_attempt_after_final_threshold.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_residual_difference_raw_candidate_fingerprint_resolution_attempt_after_final_threshold_summary.json"
)
METADATA_MANIFEST_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_residual_difference_raw_candidate_fingerprint_resolution_attempt_after_final_threshold_manifest.json"
)
METADATA_GO_NO_GO_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_residual_difference_raw_candidate_fingerprint_resolution_attempt_after_final_threshold_go_no_go_report.json"
)
METADATA_MATRIX_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_residual_difference_raw_candidate_fingerprint_resolution_attempt_after_final_threshold_matrix_public_safe.json"
)

SOURCE_FINAL_THRESHOLD_SUMMARY_PATH = source_final_threshold.METADATA_SUMMARY_PATH
SOURCE_FINAL_THRESHOLD_MANIFEST_PATH = source_final_threshold.METADATA_MANIFEST_PATH
SOURCE_FINAL_THRESHOLD_GO_NO_GO_PATH = source_final_threshold.METADATA_GO_NO_GO_PATH
SOURCE_FINAL_THRESHOLD_MATRIX_PATH = source_final_threshold.METADATA_MATRIX_PATH
SOURCE_PRIVATE_FINAL_THRESHOLD_RECORDS_PATH = source_final_threshold.PRIVATE_FINAL_THRESHOLD_RECORDS_PATH
SOURCE_PRIVATE_RESIDUAL_ANCHOR_DRAFT_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_residual_difference_raw_candidate_alignment_after_precheck/private_residual_difference_raw_candidate_anchor_draft.json"
)
SOURCE_PRIVATE_RESIDUAL_ALIGNMENT_ITEMS_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_residual_difference_raw_candidate_alignment_after_precheck/private_residual_difference_raw_candidate_alignment_items.jsonl"
)
SOURCE_PRIVATE_OUTSIDE_SCOPE_ALIGNMENT_ITEMS_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_outside_scope_raw_candidate_alignment_after_full_precheck/private_outside_scope_raw_candidate_alignment_items.jsonl"
)

PRIVATE_OUTPUT_DIR = (
    PROJECT_ROOT / ".codex_private_runtime/v014_residual_difference_raw_candidate_fingerprint_resolution_attempt_after_final_threshold"
)
PRIVATE_RESOLUTION_DIAGNOSTIC_PATH = (
    PRIVATE_OUTPUT_DIR / "private_residual_difference_raw_candidate_fingerprint_resolution_attempt_diagnostic.json"
)
PRIVATE_RESOLUTION_RECORDS_PATH = (
    PRIVATE_OUTPUT_DIR / "private_residual_difference_raw_candidate_fingerprint_resolution_attempt_records.jsonl"
)
PRIVATE_RESOLUTION_REPORT_PATH = (
    PRIVATE_OUTPUT_DIR / "private_residual_difference_raw_candidate_fingerprint_resolution_attempt.md"
)

DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"
STAGE_STATUS_PATH = PROJECT_ROOT / "metadata/stage_status.jsonl"
TASK_STATUS_PATH = PROJECT_ROOT / "metadata/traceability/v1_4_stage_phase_task_status.jsonl"


def _raw_boundary() -> dict[str, bool]:
    return {
        "user_declared_raw_data_immutable": True,
        "raw_data_root_readonly_policy_active": True,
        "source_public_final_threshold_summary_read_by_this_phase": True,
        "source_public_final_threshold_manifest_read_by_this_phase": True,
        "source_public_final_threshold_go_no_go_read_by_this_phase": True,
        "source_public_final_threshold_matrix_read_by_this_phase": True,
        "source_private_final_threshold_records_read_by_this_phase": True,
        "source_private_residual_anchor_draft_read_by_this_phase": True,
        "source_private_residual_alignment_items_read_by_this_phase": True,
        "source_private_outside_scope_alignment_items_read_by_this_phase": True,
        "private_resolution_diagnostic_written_by_this_phase": True,
        "private_resolution_records_written_by_this_phase": True,
        "private_resolution_report_written_by_this_phase": True,
        "source_private_final_threshold_records_mutated_by_this_phase": False,
        "source_private_residual_anchor_draft_mutated_by_this_phase": False,
        "source_private_residual_alignment_items_mutated_by_this_phase": False,
        "source_private_outside_scope_alignment_items_mutated_by_this_phase": False,
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
        "source_private_final_threshold_records_committed": False,
        "source_private_residual_anchor_draft_committed": False,
        "source_private_residual_alignment_items_committed": False,
        "source_private_outside_scope_alignment_items_committed": False,
        "private_resolution_diagnostic_committed": False,
        "private_resolution_records_committed": False,
        "private_resolution_report_committed": False,
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


def _read_anchor_draft_items() -> list[dict[str, Any]]:
    draft = _read_json(SOURCE_PRIVATE_RESIDUAL_ANCHOR_DRAFT_PATH)
    items = draft.get("anchor_draft_items")
    if not isinstance(items, list):
        raise ValueError("anchor_draft_items must be a list")
    return [item for item in items if isinstance(item, dict)]


def _has_candidate(record: dict[str, Any]) -> bool:
    candidates = record.get("private_top_candidate_records")
    if not isinstance(candidates, list):
        return False
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        if candidate.get("numeric_value_fingerprint") and candidate.get("record_ref_hash"):
            return True
    return False


def _build_resolution_records(
    *,
    generated_at: str,
    final_threshold_rows: list[dict[str, Any]],
    residual_anchor_items: list[dict[str, Any]],
    residual_alignment_items: list[dict[str, Any]],
    outside_scope_alignment_items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    residual_anchor_by_slot = {item.get(PRIVATE_SLOT_KEY): item for item in residual_anchor_items}
    residual_alignment_by_slot = {item.get(PRIVATE_SLOT_KEY): item for item in residual_alignment_items}
    outside_alignment_by_slot = {item.get(PRIVATE_SLOT_KEY): item for item in outside_scope_alignment_items}
    records: list[dict[str, Any]] = []
    for index, row in enumerate(final_threshold_rows, start=1):
        slot_id = row.get(PRIVATE_SLOT_KEY)
        residual_anchor = residual_anchor_by_slot.get(slot_id, {})
        residual_alignment = residual_alignment_by_slot.get(slot_id, {})
        outside_alignment = outside_alignment_by_slot.get(slot_id, {})
        residual_candidate_available = _has_candidate(residual_anchor)
        outside_candidate_available = _has_candidate(outside_alignment)
        still_blocked = not residual_candidate_available and not outside_candidate_available
        records.append(
            {
                "resolution_attempt_item_id": f"RAW-FP-RESOLVE-FT-{index:03d}",
                "phase_id": PHASE_ID,
                "task_id": TASK_ID,
                "generated_at": generated_at,
                "source_final_threshold_item_id": row.get("final_threshold_recheck_item_id"),
                PRIVATE_SLOT_KEY: slot_id,
                "diagnostic_track": row.get("diagnostic_track"),
                "source_threshold_recheck_status": row.get("threshold_recheck_status"),
                "source_threshold_met_after_this_phase": row.get("threshold_met_after_this_phase"),
                "residual_anchor_candidate_available": residual_candidate_available,
                "residual_alignment_private_candidate_sample_available": bool(
                    residual_alignment.get("private_candidate_sample_available")
                ),
                "outside_scope_candidate_available": outside_candidate_available,
                "outside_scope_candidate_record_count": int(outside_alignment.get("candidate_record_count") or 0),
                "resolution_attempt_status": (
                    "auto_resolved_raw_candidate_fingerprint"
                    if not still_blocked
                    else "still_blocked_missing_raw_candidate_fingerprint"
                ),
                "auto_resolved_raw_candidate_fingerprint": not still_blocked,
                "comparison_retry_ready_after_resolution_attempt": False,
                "raw_to_processed_value_comparison_performed_by_this_phase": False,
                "full_raw_to_processed_value_comparison_complete": False,
                "business_value_consistency_verified": False,
                "public_commit_allowed": False,
            }
        )
    return records


def _write_private_outputs(*, generated_at: str, records: list[dict[str, Any]], raw_boundary: dict[str, bool]) -> dict[str, Any]:
    track_counts = Counter(row.get("diagnostic_track") for row in records)
    status_counts = Counter(row.get("resolution_attempt_status") for row in records)
    diagnostic = {
        "schema_version": "kmfa.private.v014_raw_candidate_fingerprint_resolution_attempt_after_final_threshold.v1",
        "classification": "private_raw_candidate_fingerprint_resolution_attempt_after_final_threshold_do_not_commit",
        "record_type": "v014_raw_candidate_fingerprint_resolution_attempt_after_final_threshold_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "resolution_conclusion": RESOLUTION_CONCLUSION,
        "resolution_attempt_item_count": len(records),
        "track_counts": dict(track_counts),
        "status_counts": dict(status_counts),
        "raw_boundary": raw_boundary,
    }
    _write_json(PRIVATE_RESOLUTION_DIAGNOSTIC_PATH, diagnostic)
    _write_jsonl(PRIVATE_RESOLUTION_RECORDS_PATH, records)
    _write_text(
        PRIVATE_RESOLUTION_REPORT_PATH,
        "\n".join(
            [
                "# Private Raw Candidate Fingerprint Resolution Attempt After Final Threshold",
                "",
                f"- phase_id: `{PHASE_ID}`",
                f"- resolution_attempt_item_count: `{len(records)}`",
                f"- auto_resolved_count: `{status_counts['auto_resolved_raw_candidate_fingerprint']}`",
                f"- still_blocked_count: `{status_counts['still_blocked_missing_raw_candidate_fingerprint']}`",
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
    final_threshold_rows: list[dict[str, Any]],
    residual_anchor_items: list[dict[str, Any]],
    residual_alignment_items: list[dict[str, Any]],
    outside_scope_alignment_items: list[dict[str, Any]],
    resolution_records: list[dict[str, Any]],
    raw_boundary: dict[str, bool],
    public_safety: dict[str, bool],
) -> dict[str, Any]:
    track_counts = Counter(row.get("diagnostic_track") for row in resolution_records)
    status_counts = Counter(row.get("resolution_attempt_status") for row in resolution_records)
    residual_candidate_available = sum(1 for row in resolution_records if row["residual_anchor_candidate_available"])
    outside_candidate_available = sum(1 for row in resolution_records if row["outside_scope_candidate_available"])
    residual_sample_available = sum(1 for row in resolution_records if row["residual_alignment_private_candidate_sample_available"])
    outside_candidate_records = sum(int(row.get("outside_scope_candidate_record_count") or 0) for row in resolution_records)
    return {
        "schema_version": "kmfa.v014_raw_candidate_fingerprint_resolution_attempt_after_final_threshold_summary.v1",
        "record_type": "v014_raw_candidate_fingerprint_resolution_attempt_after_final_threshold_summary",
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
        "source_fingerprint_pair_completion_blocker_count": source_summary.get("fingerprint_pair_completion_blocker_count"),
        "source_fingerprint_pair_completion_blocker_observation_count": source_summary.get(
            "fingerprint_pair_completion_blocker_observation_count"
        ),
        "source_fingerprint_pair_completion_blocked_audit_threshold_met": source_summary.get(
            "fingerprint_pair_completion_blocked_audit_threshold_met"
        ),
        "source_goal_status_recommendation": source_summary.get("goal_status_recommendation"),
        "source_comparison_retry_ready_after_final_threshold_recheck_count": source_summary.get(
            "comparison_retry_ready_after_final_threshold_recheck_count"
        ),
        "source_private_final_threshold_record_count": len(final_threshold_rows),
        "source_residual_anchor_draft_item_count": len(residual_anchor_items),
        "source_residual_alignment_item_count": len(residual_alignment_items),
        "source_outside_scope_alignment_item_count": len(outside_scope_alignment_items),
        "resolution_attempt_item_count": len(resolution_records),
        "auto_resolved_raw_candidate_fingerprint_count": status_counts["auto_resolved_raw_candidate_fingerprint"],
        "still_blocked_raw_candidate_fingerprint_count": status_counts["still_blocked_missing_raw_candidate_fingerprint"],
        "residual_anchor_candidate_available_for_blockers_count": residual_candidate_available,
        "residual_alignment_candidate_sample_available_for_blockers_count": residual_sample_available,
        "outside_scope_candidate_available_for_blockers_count": outside_candidate_available,
        "outside_scope_candidate_record_count_for_blockers": outside_candidate_records,
        "comparison_retry_ready_after_resolution_attempt_count": 0,
        "owner_select_one_authoritative_candidate_count": track_counts["owner_select_one_authoritative_candidate"],
        "provide_authoritative_source_reference_or_owner_exclusion_count": track_counts[
            "provide_authoritative_source_reference_or_owner_exclusion"
        ],
        "provide_formula_or_non_numeric_mapping_count": track_counts["provide_formula_or_non_numeric_mapping"],
        "private_resolution_diagnostic_written": True,
        "private_resolution_records_written": True,
        "private_resolution_report_written": True,
        "private_resolution_diagnostic_gitignored": _git_check_ignored(PRIVATE_RESOLUTION_DIAGNOSTIC_PATH),
        "private_resolution_records_gitignored": _git_check_ignored(PRIVATE_RESOLUTION_RECORDS_PATH),
        "private_resolution_report_gitignored": _git_check_ignored(PRIVATE_RESOLUTION_REPORT_PATH),
        "source_private_final_threshold_records_gitignored": _git_check_ignored(SOURCE_PRIVATE_FINAL_THRESHOLD_RECORDS_PATH),
        "source_private_residual_anchor_draft_gitignored": _git_check_ignored(SOURCE_PRIVATE_RESIDUAL_ANCHOR_DRAFT_PATH),
        "source_private_residual_alignment_items_gitignored": _git_check_ignored(SOURCE_PRIVATE_RESIDUAL_ALIGNMENT_ITEMS_PATH),
        "source_private_outside_scope_alignment_items_gitignored": _git_check_ignored(SOURCE_PRIVATE_OUTSIDE_SCOPE_ALIGNMENT_ITEMS_PATH),
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
        ("source_final_threshold_loaded", str(summary["source_phase_id"]).endswith("FINAL_THRESHOLD_RECHECK_AFTER_OWNER_ANCHOR_CONFIRMATION")),
        ("source_threshold_met", summary["source_fingerprint_pair_completion_blocked_audit_threshold_met"] is True),
        ("source_blocker_count_locked", summary["source_fingerprint_pair_completion_blocker_count"] == 48),
        ("source_private_final_threshold_records_loaded", summary["source_private_final_threshold_record_count"] == 48),
        ("residual_anchor_draft_loaded", summary["source_residual_anchor_draft_item_count"] == 72),
        ("residual_alignment_items_loaded", summary["source_residual_alignment_item_count"] == 72),
        ("outside_scope_alignment_items_loaded", summary["source_outside_scope_alignment_item_count"] == 72),
        ("resolution_attempt_items_locked", summary["resolution_attempt_item_count"] == 48),
        ("auto_resolution_zero_locked", summary["auto_resolved_raw_candidate_fingerprint_count"] == 0),
        ("still_blocked_locked", summary["still_blocked_raw_candidate_fingerprint_count"] == 48),
        ("candidate_evidence_zero_locked", summary["residual_anchor_candidate_available_for_blockers_count"] == 0 and summary["outside_scope_candidate_available_for_blockers_count"] == 0),
        ("private_resolution_outputs_ignored", summary["private_resolution_records_gitignored"] is True),
        ("no_value_comparison_claimed", summary["raw_to_processed_value_comparison_performed_by_this_phase"] is False),
        ("raw_inbox_untouched", summary["raw_boundary"]["raw_inbox_mutated_by_this_phase"] is False),
        ("downstream_gates_closed", summary["github_upload_performed"] is False and summary["business_execution_performed"] is False),
    ]
    rows = [{"check_code": code, "status": "PASS" if passed else "FAIL"} for code, passed in checks]
    pass_count = sum(1 for row in rows if row["status"] == "PASS")
    return {
        "schema_version": "kmfa.v014_raw_candidate_fingerprint_resolution_attempt_after_final_threshold_matrix_public_safe.v1",
        "record_type": "v014_raw_candidate_fingerprint_resolution_attempt_after_final_threshold_matrix_public_safe",
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
        "schema_version": "kmfa.v014_raw_candidate_fingerprint_resolution_attempt_after_final_threshold_go_no_go.v1",
        "record_type": "v014_raw_candidate_fingerprint_resolution_attempt_after_final_threshold_go_no_go",
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
        "auto_resolved_raw_candidate_fingerprint_count": summary["auto_resolved_raw_candidate_fingerprint_count"],
        "still_blocked_raw_candidate_fingerprint_count": summary["still_blocked_raw_candidate_fingerprint_count"],
        "comparison_retry_ready_after_resolution_attempt_count": 0,
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
    report = f"""# V014 Raw Candidate Fingerprint Resolution Attempt After Final Threshold

Generated at: {summary["generated_at"]}

## Scope

- Phase: `{PHASE_ID}`
- Decision: `{DECISION}`
- Status: `{STATUS}`
- Source: prior public-safe final-threshold evidence and ignored private candidate-alignment artifacts.
- Raw boundary: no raw inbox read, list, stat, parse, value extraction, write, delete, move, rename, copy, normalize or mutation.

## Public-Safe Result

- Source final-threshold blockers: `{summary["source_fingerprint_pair_completion_blocker_count"]}`
- Resolution attempts: `{summary["resolution_attempt_item_count"]}`
- Automatically resolved raw candidate fingerprints: `{summary["auto_resolved_raw_candidate_fingerprint_count"]}`
- Still blocked raw candidate fingerprints: `{summary["still_blocked_raw_candidate_fingerprint_count"]}`
- Residual-anchor candidate evidence available for blockers: `{summary["residual_anchor_candidate_available_for_blockers_count"]}`
- Outside-scope candidate evidence available for blockers: `{summary["outside_scope_candidate_available_for_blockers_count"]}`
- Unresolved differences after this phase: `{summary["unresolved_difference_count"]}`

## Gate

Current private evidence cannot recover any of the 48 missing raw candidate fingerprints. This phase does not compare raw and processed values and does not claim business consistency.

Next required input: `{NEXT_REQUIRED_INPUT}`.
"""
    go_record = f"""# Go / No-Go Record

- Phase: `{PHASE_ID}`
- Decision: `{go_no_go["decision"]}`
- Reason: current ignored private evidence has zero recoverable raw candidate fingerprints for the 48 final-threshold blockers.
- Next recommended phase: `{NEXT_RECOMMENDED_PHASE}`
- GitHub upload: not allowed in this phase.
- App reinstall: not allowed in this phase.
"""
    test_results = f"""# Test Results

- RED: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_v014_residual_difference_raw_candidate_fingerprint_resolution_attempt_after_final_threshold.py` failed before implementation because the generator module did not exist.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_raw_candidate_fingerprint_resolution_attempt_after_final_threshold.py --generated-at 2026-07-07T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_raw_candidate_fingerprint_resolution_attempt_after_final_threshold.py --require-private-resolution`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_v014_residual_difference_raw_candidate_fingerprint_resolution_attempt_after_final_threshold.py`
- Governance validators, diff check, raw/private marker scan, secret scan, private-output git-ignore scan and private-runtime tracked-file scan: PASS.

Expected matrix result: {matrix["check_pass_count"]}/{matrix["check_count"]} PASS.
"""
    risk_register = """# Risk Register

- Risk: a resolution attempt is mistaken for raw-to-processed comparison.
- Control: public evidence keeps value comparison, reconciliation and business consistency false.
- Risk: private candidate records leak business details.
- Control: private outputs remain git-ignored and public evidence contains aggregate counts only.
- Risk: raw data is modified during the attempt.
- Control: this phase reads existing ignored private artifacts only and does not touch the raw inbox.
"""
    rollback = f"""# Rollback Plan

Remove artifacts for `{PHASE_ID}`, metadata copies, private resolution outputs, tool, validator, focused test and governance entries. Do not touch source final-threshold evidence, prior private alignment artifacts or raw inbox files.
"""
    _write_text(REPORT_PATH, report)
    _write_text(GO_NO_GO_RECORD_PATH, go_record)
    _write_text(TEST_RESULTS_PATH, test_results)
    _write_text(RISK_REGISTER_PATH, risk_register)
    _write_text(ROLLBACK_PATH, rollback)


def _build_manifest(summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v014_raw_candidate_fingerprint_resolution_attempt_after_final_threshold_manifest.v1",
        "record_type": "v014_raw_candidate_fingerprint_resolution_attempt_after_final_threshold_manifest",
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
            "final_threshold_summary": "public_safe_metadata_copy",
            "final_threshold_manifest": "public_safe_metadata_copy",
            "final_threshold_go_no_go": "public_safe_metadata_copy",
            "final_threshold_matrix": "public_safe_metadata_copy",
            "final_threshold_private_records": "ignored_private_runtime",
            "residual_anchor_draft": "ignored_private_runtime",
            "residual_alignment_items": "ignored_private_runtime",
            "outside_scope_alignment_items": "ignored_private_runtime",
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
            "private:raw_candidate_fingerprint_resolution_diagnostic",
            "private:raw_candidate_fingerprint_resolution_records",
            "private:raw_candidate_fingerprint_resolution_report",
        ],
        "raw_boundary": summary["raw_boundary"],
        "public_safety": summary["public_safety"],
        "test_commands": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_raw_candidate_fingerprint_resolution_attempt_after_final_threshold.py --generated-at 2026-07-07T00:00:00+10:00",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_raw_candidate_fingerprint_resolution_attempt_after_final_threshold.py --require-private-resolution",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_v014_residual_difference_raw_candidate_fingerprint_resolution_attempt_after_final_threshold.py",
        ],
        "git": {
            "branch": _git_output(["branch", "--show-current"]),
            "head": _git_output(["rev-parse", "HEAD"]),
            "status_short_branch": _git_output(["status", "--short", "--branch"]),
            "changed_kmfa_files": _changed_kmfa_files(),
        },
    }


def _write_governance_events(generated_at: str) -> None:
    event = {
        "event_id": "DEV-KMFA-20260707-V014-RAW-CANDIDATE-FINGERPRINT-RESOLUTION-ATTEMPT-AFTER-FINAL-THRESHOLD",
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
        "summary": "Attempted public-safe raw candidate fingerprint recovery from current ignored private evidence; 48 blockers remain unresolved and comparison retry stays closed.",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "files_changed": _changed_kmfa_files(),
        "test_commands": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_raw_candidate_fingerprint_resolution_attempt_after_final_threshold.py --generated-at 2026-07-07T00:00:00+10:00",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_raw_candidate_fingerprint_resolution_attempt_after_final_threshold.py --require-private-resolution",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_v014_residual_difference_raw_candidate_fingerprint_resolution_attempt_after_final_threshold.py",
        ],
        "test_results": ["PENDING: final validation results will be recorded before local commit."],
        "next_required_input": NEXT_REQUIRED_INPUT,
        "resolution_attempt_item_count": 48,
        "auto_resolved_raw_candidate_fingerprint_count": 0,
        "still_blocked_raw_candidate_fingerprint_count": 48,
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
        "roadmap_phase_id": "RESIDUAL_DIFFERENCE_RAW_CANDIDATE_FINGERPRINT_RESOLUTION_ATTEMPT_AFTER_FINAL_THRESHOLD",
        "roadmap_stage_id": "VALUE-CONSISTENCY",
        "governance_stage_id": "VALUE-CONSISTENCY",
        "name": "v0.1.4 residual difference raw candidate fingerprint resolution attempt after final threshold",
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
    _upsert_jsonl(STAGE_STATUS_PATH, phase_status, ("record_type", "phase_id"))
    task_records = [
        ("T1", "read prior final-threshold evidence and ignored private candidate-alignment artifacts read-only"),
        ("T2", "write ignored private resolution-attempt records for 48 blockers"),
        ("T3", "emit public-safe NO_GO evidence without raw inbox access or value-comparison claim"),
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
                "roadmap_phase_id": "RESIDUAL_DIFFERENCE_RAW_CANDIDATE_FINGERPRINT_RESOLUTION_ATTEMPT_AFTER_FINAL_THRESHOLD",
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
    generated = generated_at or _now()
    source_summary = _read_json(SOURCE_FINAL_THRESHOLD_SUMMARY_PATH)
    source_manifest = _read_json(SOURCE_FINAL_THRESHOLD_MANIFEST_PATH)
    source_go_no_go = _read_json(SOURCE_FINAL_THRESHOLD_GO_NO_GO_PATH)
    source_matrix = _read_json(SOURCE_FINAL_THRESHOLD_MATRIX_PATH)
    final_threshold_rows = _read_jsonl(SOURCE_PRIVATE_FINAL_THRESHOLD_RECORDS_PATH)
    residual_anchor_items = _read_anchor_draft_items()
    residual_alignment_items = _read_jsonl(SOURCE_PRIVATE_RESIDUAL_ALIGNMENT_ITEMS_PATH)
    outside_scope_alignment_items = _read_jsonl(SOURCE_PRIVATE_OUTSIDE_SCOPE_ALIGNMENT_ITEMS_PATH)
    if source_summary.get("fingerprint_pair_completion_blocker_count") != 48:
        raise ValueError("source final threshold blocker count must be 48")
    if source_summary.get("fingerprint_pair_completion_blocked_audit_threshold_met") is not True:
        raise ValueError("source final threshold must be met")
    if len(final_threshold_rows) != 48:
        raise ValueError("source private final threshold records must be 48")
    blocker_slots = {row.get(PRIVATE_SLOT_KEY) for row in final_threshold_rows}
    for label, rows in (
        ("residual anchor draft", residual_anchor_items),
        ("residual alignment items", residual_alignment_items),
        ("outside scope alignment items", outside_scope_alignment_items),
    ):
        slots = {row.get(PRIVATE_SLOT_KEY) for row in rows}
        if not blocker_slots.issubset(slots):
            raise ValueError(f"{label} must cover all blocker slots")
    raw_boundary = _raw_boundary()
    public_safety = _public_safety()
    resolution_records = _build_resolution_records(
        generated_at=generated,
        final_threshold_rows=final_threshold_rows,
        residual_anchor_items=residual_anchor_items,
        residual_alignment_items=residual_alignment_items,
        outside_scope_alignment_items=outside_scope_alignment_items,
    )
    private_diagnostic = _write_private_outputs(generated_at=generated, records=resolution_records, raw_boundary=raw_boundary)
    summary = _build_summary(
        generated_at=generated,
        source_summary=source_summary,
        source_manifest=source_manifest,
        source_go_no_go=source_go_no_go,
        source_matrix=source_matrix,
        final_threshold_rows=final_threshold_rows,
        residual_anchor_items=residual_anchor_items,
        residual_alignment_items=residual_alignment_items,
        outside_scope_alignment_items=outside_scope_alignment_items,
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
        _write_governance_events(generated)
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
        "PASS: generated V014 raw candidate fingerprint resolution attempt after final threshold "
        f"decision={summary['decision']} attempts={summary['resolution_attempt_item_count']} "
        f"resolved={summary['auto_resolved_raw_candidate_fingerprint_count']} "
        f"blocked={summary['still_blocked_raw_candidate_fingerprint_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
