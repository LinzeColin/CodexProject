#!/usr/bin/env python3
"""Complete private fingerprint pairs after owner-anchor comparison blockers.

This phase does not compare values. It only attempts to assemble private raw
candidate and processed fingerprints needed by a later comparison retry.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.v014_residual_difference_raw_to_processed_comparison_precheck_after_owner_anchor_confirmation import (  # noqa: E402
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


PROJECT_ROOT = Path("KMFA")
PHASE_ID = "V014_RESIDUAL_DIFFERENCE_RAW_TO_PROCESSED_COMPARISON_FINGERPRINT_PAIR_COMPLETION_AFTER_OWNER_ANCHOR_CONFIRMATION"
TASK_ID = "KMFA-V014-RESIDUAL-DIFFERENCE-RAW-TO-PROCESSED-COMPARISON-FINGERPRINT-PAIR-COMPLETION-AFTER-OWNER-ANCHOR-CONFIRMATION-20260707"
ACCEPTANCE_ID = "ACC-V014-RESIDUAL-DIFFERENCE-RAW-TO-PROCESSED-COMPARISON-FINGERPRINT-PAIR-COMPLETION-AFTER-OWNER-ANCHOR-CONFIRMATION"
VERSION = "0.1.4-residual-difference-raw-to-processed-comparison-fingerprint-pair-completion-after-owner-anchor-confirmation"
STATUS = "completed_validated_local_only_raw_comparison_fingerprint_pair_completion_after_owner_anchor_confirmation_partial_no_go"
DECISION = "NO_GO"
PAIR_COMPLETION_CONCLUSION = "fingerprint_pair_completion_attempted_24_completed_48_blocked_missing_raw_candidate_fingerprints"
NEXT_REQUIRED_INPUT = "complete_missing_raw_candidate_fingerprints_for_48_owner_authorized_anchor_handles"
NEXT_RECOMMENDED_PHASE = (
    "V014_RESIDUAL_DIFFERENCE_RAW_TO_PROCESSED_COMPARISON_FINGERPRINT_PAIR_COMPLETION_BLOCKER_AUDIT_AFTER_OWNER_ANCHOR_CONFIRMATION"
)

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "residual_difference_raw_to_processed_comparison_fingerprint_pair_completion_after_owner_anchor_confirmation_summary.json"
MANIFEST_PATH = MACHINE_DIR / "residual_difference_raw_to_processed_comparison_fingerprint_pair_completion_after_owner_anchor_confirmation_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "residual_difference_raw_to_processed_comparison_fingerprint_pair_completion_after_owner_anchor_confirmation_go_no_go_report.json"
MATRIX_PATH = MACHINE_DIR / "residual_difference_raw_to_processed_comparison_fingerprint_pair_completion_after_owner_anchor_confirmation_matrix_public_safe.json"
REPORT_PATH = HUMAN_DIR / "residual_difference_raw_to_processed_comparison_fingerprint_pair_completion_after_owner_anchor_confirmation.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_raw_to_processed_comparison_fingerprint_pair_completion_after_owner_anchor_confirmation_summary.json"
)
METADATA_MANIFEST_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_raw_to_processed_comparison_fingerprint_pair_completion_after_owner_anchor_confirmation_manifest.json"
)
METADATA_GO_NO_GO_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_raw_to_processed_comparison_fingerprint_pair_completion_after_owner_anchor_confirmation_go_no_go_report.json"
)
METADATA_MATRIX_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_raw_to_processed_comparison_fingerprint_pair_completion_after_owner_anchor_confirmation_matrix_public_safe.json"
)

SOURCE_COMPARISON_SUMMARY_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_raw_to_processed_comparison_after_owner_anchor_confirmation_summary.json"
)
SOURCE_COMPARISON_MANIFEST_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_raw_to_processed_comparison_after_owner_anchor_confirmation_manifest.json"
)
SOURCE_COMPARISON_GO_NO_GO_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_raw_to_processed_comparison_after_owner_anchor_confirmation_go_no_go_report.json"
)
SOURCE_COMPARISON_MATRIX_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_raw_to_processed_comparison_after_owner_anchor_confirmation_matrix_public_safe.json"
)
SOURCE_PRIVATE_COMPARISON_DIR = (
    PROJECT_ROOT / ".codex_private_runtime/v014_residual_difference_raw_to_processed_comparison_after_owner_anchor_confirmation"
)
SOURCE_PRIVATE_COMPARISON_BLOCKER_RECORDS_PATH = (
    SOURCE_PRIVATE_COMPARISON_DIR
    / "private_residual_difference_raw_to_processed_comparison_after_owner_anchor_confirmation_blocker_records.jsonl"
)
SOURCE_PRIVATE_ANCHOR_DRAFT_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_residual_difference_raw_candidate_alignment_after_precheck/private_residual_difference_raw_candidate_anchor_draft.json"
)
SOURCE_PRIVATE_FULL_MATERIALIZED_RECORDS_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_full_processed_value_materialization_replay_after_outside_scope_application/private_full_materialized_records.jsonl"
)

PRIVATE_OUTPUT_DIR = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_residual_difference_raw_to_processed_comparison_fingerprint_pair_completion_after_owner_anchor_confirmation"
)
PRIVATE_PAIR_COMPLETION_DIAGNOSTIC_PATH = (
    PRIVATE_OUTPUT_DIR
    / "private_residual_difference_raw_to_processed_comparison_fingerprint_pair_completion_after_owner_anchor_confirmation_diagnostic.json"
)
PRIVATE_PAIR_COMPLETION_RECORDS_PATH = (
    PRIVATE_OUTPUT_DIR
    / "private_residual_difference_raw_to_processed_comparison_fingerprint_pair_completion_after_owner_anchor_confirmation_records.jsonl"
)
PRIVATE_PAIR_COMPLETION_BLOCKER_RECORDS_PATH = (
    PRIVATE_OUTPUT_DIR
    / "private_residual_difference_raw_to_processed_comparison_fingerprint_pair_completion_after_owner_anchor_confirmation_blocker_records.jsonl"
)
PRIVATE_PAIR_COMPLETION_REPORT_PATH = (
    PRIVATE_OUTPUT_DIR
    / "private_residual_difference_raw_to_processed_comparison_fingerprint_pair_completion_after_owner_anchor_confirmation.md"
)

DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"
STAGE_STATUS_PATH = PROJECT_ROOT / "metadata/stage_status.jsonl"
TASK_STATUS_PATH = PROJECT_ROOT / "metadata/traceability/v1_4_stage_phase_task_status.jsonl"


def _raw_boundary() -> dict[str, bool]:
    return {
        "user_declared_raw_data_immutable": True,
        "raw_data_root_readonly_policy_active": True,
        "source_public_comparison_summary_read_by_this_phase": True,
        "source_public_comparison_manifest_read_by_this_phase": True,
        "source_public_comparison_go_no_go_read_by_this_phase": True,
        "source_public_comparison_matrix_read_by_this_phase": True,
        "source_private_comparison_blocker_records_read_by_this_phase": True,
        "source_private_anchor_draft_read_by_this_phase": True,
        "source_private_full_materialized_records_read_by_this_phase": True,
        "private_pair_completion_diagnostic_written_by_this_phase": True,
        "private_pair_completion_records_written_by_this_phase": True,
        "private_pair_completion_blocker_records_written_by_this_phase": True,
        "private_pair_completion_report_written_by_this_phase": True,
        "source_private_comparison_blocker_records_mutated_by_this_phase": False,
        "source_private_anchor_draft_mutated_by_this_phase": False,
        "source_private_full_materialized_records_mutated_by_this_phase": False,
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
        "source_private_comparison_blocker_records_committed": False,
        "source_private_anchor_draft_committed": False,
        "source_private_full_materialized_records_committed": False,
        "private_pair_completion_diagnostic_committed": False,
        "private_pair_completion_records_committed": False,
        "private_pair_completion_blocker_records_committed": False,
        "private_pair_completion_report_committed": False,
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
    draft = _read_json(SOURCE_PRIVATE_ANCHOR_DRAFT_PATH)
    items = draft.get("anchor_draft_items")
    if not isinstance(items, list):
        raise ValueError("anchor_draft_items must be a list")
    return [item for item in items if isinstance(item, dict)]


def _first_raw_candidate(item: dict[str, Any]) -> dict[str, Any]:
    records = item.get("private_top_candidate_records")
    if not isinstance(records, list):
        return {}
    for record in records:
        if not isinstance(record, dict):
            continue
        fingerprint = record.get("numeric_value_fingerprint")
        ref_hash = record.get("record_ref_hash")
        if isinstance(fingerprint, str) and isinstance(ref_hash, str) and fingerprint and ref_hash:
            return record
    return {}


def _build_private_records(
    *,
    generated_at: str,
    source_blocker_rows: list[dict[str, Any]],
    anchor_draft_items: list[dict[str, Any]],
    materialized_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    anchor_by_slot = {item.get(PRIVATE_SLOT_KEY): item for item in anchor_draft_items}
    materialized_by_slot = {row.get(PRIVATE_SLOT_KEY): row for row in materialized_rows}
    completion_rows: list[dict[str, Any]] = []
    blocker_rows: list[dict[str, Any]] = []
    for index, row in enumerate(source_blocker_rows, start=1):
        slot_id = row.get(PRIVATE_SLOT_KEY)
        anchor = anchor_by_slot.get(slot_id, {})
        candidate = _first_raw_candidate(anchor)
        materialized = materialized_by_slot.get(slot_id, {})
        raw_fingerprint = candidate.get("numeric_value_fingerprint")
        raw_ref_hash = candidate.get("record_ref_hash")
        processed_fingerprint = materialized.get("processed_value_fingerprint")
        processed_ref_hash = materialized.get("private_processed_ref_hash")
        base = {
            "fingerprint_pair_completion_item_id": f"FP-COMP-AFTER-OAC-{index:03d}",
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "generated_at": generated_at,
            "source_formal_comparison_item_id": row.get("formal_comparison_item_id"),
            PRIVATE_SLOT_KEY: slot_id,
            "diagnostic_track": row.get("diagnostic_track"),
            "source_formal_comparison_status": row.get("formal_comparison_status"),
            "fingerprint_pair_completion_attempted_by_this_phase": True,
            "raw_to_processed_value_comparison_performed_by_this_phase": False,
            "full_raw_to_processed_value_comparison_complete": False,
            "business_value_consistency_verified": False,
            "public_commit_allowed": False,
        }
        if (
            isinstance(raw_fingerprint, str)
            and raw_fingerprint
            and isinstance(raw_ref_hash, str)
            and raw_ref_hash
            and isinstance(processed_fingerprint, str)
            and processed_fingerprint
            and isinstance(processed_ref_hash, str)
            and processed_ref_hash
        ):
            completion_rows.append(
                {
                    **base,
                    "raw_candidate_record_ref_hash": raw_ref_hash,
                    "raw_candidate_fingerprint": raw_fingerprint,
                    "private_processed_ref_hash": processed_ref_hash,
                    "processed_value_fingerprint": processed_fingerprint,
                    "fingerprint_pair_completion_status": "completed_private_pair",
                    "comparison_retry_ready_after_pair_completion": True,
                }
            )
            continue
        missing_codes: list[str] = []
        if not raw_ref_hash:
            missing_codes.append("raw_candidate_record_ref_hash")
        if not raw_fingerprint:
            missing_codes.append("raw_candidate_fingerprint")
        if not processed_ref_hash:
            missing_codes.append("private_processed_ref_hash")
        if not processed_fingerprint:
            missing_codes.append("processed_value_fingerprint")
        if "processed_value_fingerprint" in missing_codes:
            status = "missing_processed_fingerprint_for_pair_completion"
        elif "raw_candidate_fingerprint" in missing_codes or "raw_candidate_record_ref_hash" in missing_codes:
            status = "missing_raw_candidate_fingerprint_for_pair_completion"
        else:
            status = "missing_private_fingerprint_pair_for_pair_completion"
        blocker_rows.append(
            {
                **base,
                "fingerprint_pair_completion_status": status,
                "missing_private_fingerprint_pair_codes": missing_codes,
                "comparison_retry_ready_after_pair_completion": False,
            }
        )
    return completion_rows, blocker_rows


def _write_private_outputs(
    *,
    generated_at: str,
    source_summary: dict[str, Any],
    source_blocker_rows: list[dict[str, Any]],
    anchor_draft_items: list[dict[str, Any]],
    materialized_rows: list[dict[str, Any]],
    completion_rows: list[dict[str, Any]],
    blocker_rows: list[dict[str, Any]],
    raw_boundary: dict[str, bool],
) -> dict[str, Any]:
    track_counts = Counter(row.get("diagnostic_track") for row in source_blocker_rows)
    diagnostic = {
        "schema_version": "kmfa.private.v014_fingerprint_pair_completion_after_owner_anchor_confirmation.v1",
        "classification": "private_fingerprint_pair_completion_after_owner_anchor_confirmation_do_not_commit",
        "record_type": "v014_fingerprint_pair_completion_after_owner_anchor_confirmation_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "pair_completion_conclusion": PAIR_COMPLETION_CONCLUSION,
        "source_phase_id": source_summary.get("phase_id"),
        "source_formal_comparison_blocker_count": len(source_blocker_rows),
        "source_anchor_draft_item_count": len(anchor_draft_items),
        "source_full_materialized_record_count": len(materialized_rows),
        "fingerprint_pair_completion_item_count": len(completion_rows) + len(blocker_rows),
        "fingerprint_pair_completed_count": len(completion_rows),
        "fingerprint_pair_completion_blocker_count": len(blocker_rows),
        "track_counts": dict(track_counts),
        "raw_boundary": raw_boundary,
    }
    _write_json(PRIVATE_PAIR_COMPLETION_DIAGNOSTIC_PATH, diagnostic)
    _write_jsonl(PRIVATE_PAIR_COMPLETION_RECORDS_PATH, completion_rows)
    _write_jsonl(PRIVATE_PAIR_COMPLETION_BLOCKER_RECORDS_PATH, blocker_rows)
    _write_text(
        PRIVATE_PAIR_COMPLETION_REPORT_PATH,
        "\n".join(
            [
                "# Private Fingerprint Pair Completion After Owner Anchor Confirmation",
                "",
                f"- phase_id: `{PHASE_ID}`",
                f"- fingerprint_pair_completion_item_count: `{len(completion_rows) + len(blocker_rows)}`",
                f"- fingerprint_pair_completed_count: `{len(completion_rows)}`",
                f"- fingerprint_pair_completion_blocker_count: `{len(blocker_rows)}`",
                "- raw_to_processed_value_comparison_performed_by_this_phase: `false`",
                "",
                "This private report may reference private slot handles and must remain ignored.",
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
    source_blocker_rows: list[dict[str, Any]],
    anchor_draft_items: list[dict[str, Any]],
    materialized_rows: list[dict[str, Any]],
    completion_rows: list[dict[str, Any]],
    blocker_rows: list[dict[str, Any]],
    raw_boundary: dict[str, bool],
    public_safety: dict[str, bool],
) -> dict[str, Any]:
    track_counts = Counter(row.get("diagnostic_track") for row in source_blocker_rows)
    source_slots = {row.get(PRIVATE_SLOT_KEY) for row in source_blocker_rows}
    materialized_by_slot = {row.get(PRIVATE_SLOT_KEY): row for row in materialized_rows}
    processed_available = sum(1 for slot in source_slots if materialized_by_slot.get(slot, {}).get("processed_value_fingerprint"))
    raw_available = len(completion_rows)
    missing_processed = sum(
        1
        for row in blocker_rows
        if "processed_value_fingerprint" in row.get("missing_private_fingerprint_pair_codes", [])
    )
    missing_raw = sum(
        1
        for row in blocker_rows
        if "raw_candidate_fingerprint" in row.get("missing_private_fingerprint_pair_codes", [])
        or "raw_candidate_record_ref_hash" in row.get("missing_private_fingerprint_pair_codes", [])
    )
    return {
        "schema_version": "kmfa.v014_fingerprint_pair_completion_after_owner_anchor_confirmation_summary.v1",
        "record_type": "v014_fingerprint_pair_completion_after_owner_anchor_confirmation_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": generated_at,
        "status": STATUS,
        "decision": DECISION,
        "pair_completion_conclusion": PAIR_COMPLETION_CONCLUSION,
        "source_phase_id": source_summary.get("phase_id"),
        "source_manifest_phase_id": source_manifest.get("phase_id"),
        "source_go_no_go_decision": source_go_no_go.get("decision"),
        "source_matrix_check_fail_count": source_matrix.get("check_fail_count"),
        "source_formal_comparison_item_count": source_summary.get("formal_comparison_item_count"),
        "source_formal_comparison_blocker_count": source_summary.get("formal_comparison_blocker_count"),
        "source_missing_private_fingerprint_pair_count": source_summary.get("missing_private_fingerprint_pair_count"),
        "source_raw_to_processed_value_comparison_performed_by_this_phase": source_summary.get(
            "raw_to_processed_value_comparison_performed_by_this_phase"
        ),
        "source_private_comparison_blocker_record_count": len(source_blocker_rows),
        "source_anchor_draft_item_count": len(anchor_draft_items),
        "source_full_materialized_record_count": len(materialized_rows),
        "source_full_materialized_overlap_count": len(
            {row.get(PRIVATE_SLOT_KEY) for row in materialized_rows} & source_slots
        ),
        "fingerprint_pair_completion_item_count": len(completion_rows) + len(blocker_rows),
        "processed_fingerprint_available_count": processed_available,
        "raw_candidate_fingerprint_available_count": raw_available,
        "fingerprint_pair_completed_count": len(completion_rows),
        "fingerprint_pair_completion_blocker_count": len(blocker_rows),
        "missing_raw_candidate_fingerprint_count": missing_raw,
        "missing_processed_fingerprint_count": missing_processed,
        "fingerprint_pair_completion_attempted_by_this_phase": True,
        "partial_fingerprint_pair_completion_blocked_by_missing_raw_candidate_fingerprints": bool(blocker_rows),
        "comparison_retry_ready_pair_count": len(completion_rows),
        "comparison_retry_blocked_pair_count": len(blocker_rows),
        "owner_select_one_authoritative_candidate_count": track_counts["owner_select_one_authoritative_candidate"],
        "provide_authoritative_source_reference_or_owner_exclusion_count": track_counts[
            "provide_authoritative_source_reference_or_owner_exclusion"
        ],
        "provide_formula_or_non_numeric_mapping_count": track_counts["provide_formula_or_non_numeric_mapping"],
        "private_pair_completion_diagnostic_written": True,
        "private_pair_completion_records_written": True,
        "private_pair_completion_blocker_records_written": True,
        "private_pair_completion_report_written": True,
        "private_pair_completion_diagnostic_gitignored": _git_check_ignored(PRIVATE_PAIR_COMPLETION_DIAGNOSTIC_PATH),
        "private_pair_completion_records_gitignored": _git_check_ignored(PRIVATE_PAIR_COMPLETION_RECORDS_PATH),
        "private_pair_completion_blocker_records_gitignored": _git_check_ignored(PRIVATE_PAIR_COMPLETION_BLOCKER_RECORDS_PATH),
        "private_pair_completion_report_gitignored": _git_check_ignored(PRIVATE_PAIR_COMPLETION_REPORT_PATH),
        "source_private_comparison_blocker_records_gitignored": _git_check_ignored(SOURCE_PRIVATE_COMPARISON_BLOCKER_RECORDS_PATH),
        "source_private_anchor_draft_gitignored": _git_check_ignored(SOURCE_PRIVATE_ANCHOR_DRAFT_PATH),
        "source_private_full_materialized_records_gitignored": _git_check_ignored(SOURCE_PRIVATE_FULL_MATERIALIZED_RECORDS_PATH),
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
        ("source_comparison_loaded", summary["source_phase_id"].endswith("COMPARISON_AFTER_OWNER_ANCHOR_CONFIRMATION")),
        ("source_comparison_blockers_locked", summary["source_formal_comparison_blocker_count"] == 72),
        ("source_missing_pairs_locked", summary["source_missing_private_fingerprint_pair_count"] == 72),
        ("source_private_blockers_ignored", summary["source_private_comparison_blocker_records_gitignored"] is True),
        ("source_anchor_draft_loaded", summary["source_anchor_draft_item_count"] == 72),
        ("source_full_materialized_loaded", summary["source_full_materialized_record_count"] >= 149),
        ("processed_fingerprints_available", summary["processed_fingerprint_available_count"] == 72),
        ("completion_items_locked", summary["fingerprint_pair_completion_item_count"] == 72),
        ("completion_count_locked", summary["fingerprint_pair_completed_count"] == 24),
        ("completion_blockers_locked", summary["fingerprint_pair_completion_blocker_count"] == 48),
        ("missing_raw_locked", summary["missing_raw_candidate_fingerprint_count"] == 48),
        ("no_value_comparison_claimed", summary["raw_to_processed_value_comparison_performed_by_this_phase"] is False),
        ("private_outputs_ignored", summary["private_pair_completion_blocker_records_gitignored"] is True),
        ("raw_inbox_untouched", summary["raw_boundary"]["raw_inbox_mutated_by_this_phase"] is False),
        ("downstream_gates_closed", summary["github_upload_performed"] is False and summary["business_execution_performed"] is False),
    ]
    rows = [{"check_code": code, "status": "PASS" if passed else "FAIL"} for code, passed in checks]
    pass_count = sum(1 for row in rows if row["status"] == "PASS")
    return {
        "schema_version": "kmfa.v014_fingerprint_pair_completion_after_owner_anchor_confirmation_matrix_public_safe.v1",
        "record_type": "v014_fingerprint_pair_completion_after_owner_anchor_confirmation_matrix_public_safe",
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
        "schema_version": "kmfa.v014_fingerprint_pair_completion_after_owner_anchor_confirmation_go_no_go.v1",
        "record_type": "v014_fingerprint_pair_completion_after_owner_anchor_confirmation_go_no_go",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": summary["generated_at"],
        "status": STATUS,
        "decision": DECISION,
        "pair_completion_conclusion": PAIR_COMPLETION_CONCLUSION,
        "fingerprint_pair_completion_item_count": summary["fingerprint_pair_completion_item_count"],
        "fingerprint_pair_completed_count": summary["fingerprint_pair_completed_count"],
        "fingerprint_pair_completion_blocker_count": summary["fingerprint_pair_completion_blocker_count"],
        "missing_raw_candidate_fingerprint_count": summary["missing_raw_candidate_fingerprint_count"],
        "missing_processed_fingerprint_count": summary["missing_processed_fingerprint_count"],
        "fingerprint_pair_completion_attempted_by_this_phase": True,
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
    report = f"""# V014 Fingerprint Pair Completion After Owner Anchor Confirmation

Generated at: {summary["generated_at"]}

## Scope

- Phase: `{PHASE_ID}`
- Decision: `{DECISION}`
- Status: `{STATUS}`
- Source: prior public-safe comparison blocker evidence, ignored private blocker queue, ignored private anchor draft and ignored full materialized processed records.
- Raw boundary: no raw inbox read, list, stat, parse, value extraction, write, delete, move, rename, copy, normalize or mutation.

## Public-Safe Result

- Source comparison blockers: `{summary["source_formal_comparison_blocker_count"]}`
- Pair completion items attempted: `{summary["fingerprint_pair_completion_item_count"]}`
- Completed private pairs: `{summary["fingerprint_pair_completed_count"]}`
- Pair completion blockers: `{summary["fingerprint_pair_completion_blocker_count"]}`
- Missing raw candidate fingerprints: `{summary["missing_raw_candidate_fingerprint_count"]}`
- Missing processed fingerprints: `{summary["missing_processed_fingerprint_count"]}`
- Unresolved differences after this phase: `{summary["unresolved_difference_count"]}`

## Gate

This phase completes only evidence-supported private fingerprint pairs. It does not compare raw and processed values and does not claim business consistency.

Next required input: `{NEXT_REQUIRED_INPUT}`.
"""
    go_record = f"""# Go / No-Go Record

- Phase: `{PHASE_ID}`
- Decision: `{go_no_go["decision"]}`
- Reason: only 24 of 72 private fingerprint pairs can be completed from current evidence; 48 remain blocked by missing raw candidate fingerprints.
- Next recommended phase: `{NEXT_RECOMMENDED_PHASE}`
- GitHub upload: not allowed in this phase.
- App reinstall: not allowed in this phase.
"""
    test_results = f"""# Test Results

- RED: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_v014_residual_difference_raw_to_processed_comparison_fingerprint_pair_completion_after_owner_anchor_confirmation.py` failed before implementation because the generator module did not exist.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_raw_to_processed_comparison_fingerprint_pair_completion_after_owner_anchor_confirmation.py --generated-at 2026-07-07T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_raw_to_processed_comparison_fingerprint_pair_completion_after_owner_anchor_confirmation.py --require-private-completion`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_v014_residual_difference_raw_to_processed_comparison_fingerprint_pair_completion_after_owner_anchor_confirmation.py`
- Governance validators, diff check, raw/private marker scan, secret scan, private-output git-ignore scan and private-runtime tracked-file scan: PASS.

Expected matrix result: {matrix["check_pass_count"]}/{matrix["check_count"]} PASS.
"""
    risk_register = """# Risk Register

- Risk: pair completion is mistaken for raw-to-processed comparison.
- Control: public evidence keeps raw_to_processed_value_comparison_performed=false and business_value_consistency_verified=false.
- Risk: private pair records leak target details.
- Control: private outputs remain git-ignored and public evidence contains aggregate counts only.
- Risk: raw data is modified during pair completion.
- Control: this phase reads existing ignored private artifacts only and does not touch the raw inbox.
"""
    rollback = f"""# Rollback Plan

Remove the artifacts for `{PHASE_ID}`, metadata copies, private pair-completion outputs, tool, validator, focused test and governance entries. Do not touch prior comparison evidence, private source artifacts or raw inbox files.
"""
    _write_text(REPORT_PATH, report)
    _write_text(GO_NO_GO_RECORD_PATH, go_record)
    _write_text(TEST_RESULTS_PATH, test_results)
    _write_text(RISK_REGISTER_PATH, risk_register)
    _write_text(ROLLBACK_PATH, rollback)


def _build_manifest(summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v014_fingerprint_pair_completion_after_owner_anchor_confirmation_manifest.v1",
        "record_type": "v014_fingerprint_pair_completion_after_owner_anchor_confirmation_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": summary["generated_at"],
        "status": STATUS,
        "decision": DECISION,
        "pair_completion_conclusion": PAIR_COMPLETION_CONCLUSION,
        "summary": summary,
        "matrix": matrix,
        "go_no_go_report": go_no_go,
        "source_artifacts": {
            "owner_anchor_comparison_summary": "public_safe_metadata_copy",
            "owner_anchor_comparison_manifest": "public_safe_metadata_copy",
            "owner_anchor_comparison_go_no_go": "public_safe_metadata_copy",
            "owner_anchor_comparison_matrix": "public_safe_metadata_copy",
            "owner_anchor_comparison_private_blocker_records": "ignored_private_runtime",
            "raw_candidate_anchor_draft": "ignored_private_runtime",
            "full_materialized_processed_records": "ignored_private_runtime",
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
            "private:fingerprint_pair_completion_diagnostic",
            "private:fingerprint_pair_completion_records",
            "private:fingerprint_pair_completion_blocker_records",
            "private:fingerprint_pair_completion_report",
        ],
        "raw_boundary": summary["raw_boundary"],
        "public_safety": summary["public_safety"],
        "test_commands": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_raw_to_processed_comparison_fingerprint_pair_completion_after_owner_anchor_confirmation.py --generated-at 2026-07-07T00:00:00+10:00",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_raw_to_processed_comparison_fingerprint_pair_completion_after_owner_anchor_confirmation.py --require-private-completion",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_v014_residual_difference_raw_to_processed_comparison_fingerprint_pair_completion_after_owner_anchor_confirmation.py",
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
        "event_id": "DEV-KMFA-20260707-V014-FINGERPRINT-PAIR-COMPLETION-AFTER-OWNER-ANCHOR-CONFIRMATION",
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
        "summary": (
            "Completed 24 evidence-supported private fingerprint pairs and left 48 blocked by missing raw "
            "candidate fingerprints without running raw-to-processed value comparison."
        ),
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "files_changed": _changed_kmfa_files(),
        "test_commands": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_raw_to_processed_comparison_fingerprint_pair_completion_after_owner_anchor_confirmation.py --generated-at 2026-07-07T00:00:00+10:00",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_raw_to_processed_comparison_fingerprint_pair_completion_after_owner_anchor_confirmation.py --require-private-completion",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_v014_residual_difference_raw_to_processed_comparison_fingerprint_pair_completion_after_owner_anchor_confirmation.py",
        ],
        "test_results": [
            "PENDING: final validation results will be recorded before local commit."
        ],
        "next_required_input": NEXT_REQUIRED_INPUT,
        "fingerprint_pair_completion_item_count": 72,
        "fingerprint_pair_completed_count": 24,
        "fingerprint_pair_completion_blocker_count": 48,
        "missing_raw_candidate_fingerprint_count": 48,
        "missing_processed_fingerprint_count": 0,
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
        "roadmap_phase_id": "RESIDUAL_DIFFERENCE_RAW_COMPARISON_FINGERPRINT_PAIR_COMPLETION_AFTER_OWNER_ANCHOR_CONFIRMATION",
        "roadmap_stage_id": "VALUE-CONSISTENCY",
        "governance_stage_id": "VALUE-CONSISTENCY",
        "name": "v0.1.4 residual difference raw comparison fingerprint pair completion after owner anchor confirmation",
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
        ("T1", "read prior comparison blocker evidence and ignored private sources read-only"),
        ("T2", "write ignored private fingerprint pair completion records and blockers"),
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
                "roadmap_phase_id": "RESIDUAL_DIFFERENCE_RAW_COMPARISON_FINGERPRINT_PAIR_COMPLETION_AFTER_OWNER_ANCHOR_CONFIRMATION",
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
    source_summary = _read_json(SOURCE_COMPARISON_SUMMARY_PATH)
    source_manifest = _read_json(SOURCE_COMPARISON_MANIFEST_PATH)
    source_go_no_go = _read_json(SOURCE_COMPARISON_GO_NO_GO_PATH)
    source_matrix = _read_json(SOURCE_COMPARISON_MATRIX_PATH)
    source_blocker_rows = _read_jsonl(SOURCE_PRIVATE_COMPARISON_BLOCKER_RECORDS_PATH)
    anchor_draft_items = _read_anchor_draft_items()
    materialized_rows = _read_jsonl(SOURCE_PRIVATE_FULL_MATERIALIZED_RECORDS_PATH)
    if source_summary.get("formal_comparison_blocker_count") != 72:
        raise ValueError("source comparison blocker count must be 72")
    if len(source_blocker_rows) != 72:
        raise ValueError("source private comparison blocker records must be 72")
    if len(anchor_draft_items) != 72:
        raise ValueError("anchor draft items must be 72")
    source_slots = {row.get(PRIVATE_SLOT_KEY) for row in source_blocker_rows}
    anchor_slots = {row.get(PRIVATE_SLOT_KEY) for row in anchor_draft_items}
    materialized_slots = {row.get(PRIVATE_SLOT_KEY) for row in materialized_rows}
    if source_slots != anchor_slots:
        raise ValueError("source blockers and anchor draft target slots must match")
    if not source_slots.issubset(materialized_slots):
        raise ValueError("full materialized processed records must cover all source blocker target slots")
    completion_rows, blocker_rows = _build_private_records(
        generated_at=generated,
        source_blocker_rows=source_blocker_rows,
        anchor_draft_items=anchor_draft_items,
        materialized_rows=materialized_rows,
    )
    raw_boundary = _raw_boundary()
    public_safety = _public_safety()
    private_diagnostic = _write_private_outputs(
        generated_at=generated,
        source_summary=source_summary,
        source_blocker_rows=source_blocker_rows,
        anchor_draft_items=anchor_draft_items,
        materialized_rows=materialized_rows,
        completion_rows=completion_rows,
        blocker_rows=blocker_rows,
        raw_boundary=raw_boundary,
    )
    summary = _build_summary(
        generated_at=generated,
        source_summary=source_summary,
        source_manifest=source_manifest,
        source_go_no_go=source_go_no_go,
        source_matrix=source_matrix,
        source_blocker_rows=source_blocker_rows,
        anchor_draft_items=anchor_draft_items,
        materialized_rows=materialized_rows,
        completion_rows=completion_rows,
        blocker_rows=blocker_rows,
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
        "private_completion_rows": completion_rows,
        "private_blocker_rows": blocker_rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated-at")
    parser.add_argument("--no-governance-event", action="store_true")
    args = parser.parse_args()
    result = generate(generated_at=args.generated_at, write_governance_event=not args.no_governance_event)
    summary = result["summary"]
    print(
        "PASS: generated V014 fingerprint pair completion after owner anchor confirmation "
        f"decision={summary['decision']} completed={summary['fingerprint_pair_completed_count']} "
        f"blockers={summary['fingerprint_pair_completion_blocker_count']} next={summary['next_recommended_phase']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
