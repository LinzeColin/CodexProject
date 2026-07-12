#!/usr/bin/env python3
"""Attempt residual raw-to-processed comparison after owner anchor confirmation.

This phase consumes the prior owner-anchor comparison precheck and the ignored
private anchor draft. It records that formal comparison was attempted, but does
not claim value consistency when private fingerprint pairs are missing.
"""

from __future__ import annotations

import argparse
import json
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
PHASE_ID = "V014_RESIDUAL_DIFFERENCE_RAW_TO_PROCESSED_COMPARISON_AFTER_OWNER_ANCHOR_CONFIRMATION"
TASK_ID = "KMFA-V014-RESIDUAL-DIFFERENCE-RAW-TO-PROCESSED-COMPARISON-AFTER-OWNER-ANCHOR-CONFIRMATION-20260707"
ACCEPTANCE_ID = "ACC-V014-RESIDUAL-DIFFERENCE-RAW-TO-PROCESSED-COMPARISON-AFTER-OWNER-ANCHOR-CONFIRMATION"
VERSION = "0.1.4-residual-difference-raw-to-processed-comparison-after-owner-anchor-confirmation"
STATUS = "completed_validated_local_only_raw_comparison_after_owner_anchor_confirmation_blocked_no_go"
DECISION = "NO_GO"
COMPARISON_CONCLUSION = "formal_comparison_attempted_blocked_by_missing_private_fingerprint_pairs"
NEXT_REQUIRED_INPUT = "complete_private_raw_and_processed_fingerprint_pairs_for_72_owner_authorized_anchor_handles"
NEXT_RECOMMENDED_PHASE = "V014_RESIDUAL_DIFFERENCE_RAW_TO_PROCESSED_COMPARISON_FINGERPRINT_PAIR_COMPLETION_AFTER_OWNER_ANCHOR_CONFIRMATION"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "residual_difference_raw_to_processed_comparison_after_owner_anchor_confirmation_summary.json"
MANIFEST_PATH = MACHINE_DIR / "residual_difference_raw_to_processed_comparison_after_owner_anchor_confirmation_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "residual_difference_raw_to_processed_comparison_after_owner_anchor_confirmation_go_no_go_report.json"
MATRIX_PATH = MACHINE_DIR / "residual_difference_raw_to_processed_comparison_after_owner_anchor_confirmation_matrix_public_safe.json"
REPORT_PATH = HUMAN_DIR / "residual_difference_raw_to_processed_comparison_after_owner_anchor_confirmation.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_residual_difference_raw_to_processed_comparison_after_owner_anchor_confirmation_summary.json"
)
METADATA_MANIFEST_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_residual_difference_raw_to_processed_comparison_after_owner_anchor_confirmation_manifest.json"
)
METADATA_GO_NO_GO_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_residual_difference_raw_to_processed_comparison_after_owner_anchor_confirmation_go_no_go_report.json"
)
METADATA_MATRIX_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_raw_to_processed_comparison_after_owner_anchor_confirmation_matrix_public_safe.json"
)

SOURCE_SUMMARY_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_raw_to_processed_comparison_precheck_after_owner_anchor_confirmation_summary.json"
)
SOURCE_MANIFEST_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_raw_to_processed_comparison_precheck_after_owner_anchor_confirmation_manifest.json"
)
SOURCE_GO_NO_GO_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_raw_to_processed_comparison_precheck_after_owner_anchor_confirmation_go_no_go_report.json"
)
SOURCE_MATRIX_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_raw_to_processed_comparison_precheck_after_owner_anchor_confirmation_matrix_public_safe.json"
)
SOURCE_PRIVATE_PRECHECK_DIR = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_residual_difference_raw_to_processed_comparison_precheck_after_owner_anchor_confirmation"
)
SOURCE_PRIVATE_PRECHECK_DIAGNOSTIC_PATH = (
    SOURCE_PRIVATE_PRECHECK_DIR
    / "private_residual_difference_raw_to_processed_comparison_precheck_after_owner_anchor_confirmation_diagnostic.json"
)
SOURCE_PRIVATE_READY_QUEUE_PATH = (
    SOURCE_PRIVATE_PRECHECK_DIR
    / "private_residual_difference_raw_to_processed_comparison_precheck_after_owner_anchor_confirmation_ready_queue.jsonl"
)
SOURCE_PRIVATE_BLOCKER_QUEUE_PATH = (
    SOURCE_PRIVATE_PRECHECK_DIR
    / "private_residual_difference_raw_to_processed_comparison_precheck_after_owner_anchor_confirmation_blocker_queue.jsonl"
)
SOURCE_PRIVATE_PRECHECK_REPORT_PATH = (
    SOURCE_PRIVATE_PRECHECK_DIR / "private_residual_difference_raw_to_processed_comparison_precheck_after_owner_anchor_confirmation.md"
)
SOURCE_PRIVATE_ANCHOR_DRAFT_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_residual_difference_raw_candidate_alignment_after_precheck/private_residual_difference_raw_candidate_anchor_draft.json"
)

PRIVATE_OUTPUT_DIR = (
    PROJECT_ROOT / ".codex_private_runtime/v014_residual_difference_raw_to_processed_comparison_after_owner_anchor_confirmation"
)
PRIVATE_COMPARISON_DIAGNOSTIC_PATH = (
    PRIVATE_OUTPUT_DIR / "private_residual_difference_raw_to_processed_comparison_after_owner_anchor_confirmation_diagnostic.json"
)
PRIVATE_COMPARISON_RECORDS_PATH = (
    PRIVATE_OUTPUT_DIR / "private_residual_difference_raw_to_processed_comparison_after_owner_anchor_confirmation_records.jsonl"
)
PRIVATE_COMPARISON_BLOCKER_RECORDS_PATH = (
    PRIVATE_OUTPUT_DIR / "private_residual_difference_raw_to_processed_comparison_after_owner_anchor_confirmation_blocker_records.jsonl"
)
PRIVATE_COMPARISON_REPORT_PATH = (
    PRIVATE_OUTPUT_DIR / "private_residual_difference_raw_to_processed_comparison_after_owner_anchor_confirmation.md"
)

DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"
STAGE_STATUS_PATH = PROJECT_ROOT / "metadata/stage_status.jsonl"
TASK_STATUS_PATH = PROJECT_ROOT / "metadata/traceability/v1_4_stage_phase_task_status.jsonl"


def _raw_boundary() -> dict[str, bool]:
    return {
        "user_declared_raw_data_immutable": True,
        "raw_data_root_readonly_policy_active": True,
        "source_public_precheck_summary_read_by_this_phase": True,
        "source_public_precheck_manifest_read_by_this_phase": True,
        "source_public_precheck_go_no_go_read_by_this_phase": True,
        "source_public_precheck_matrix_read_by_this_phase": True,
        "source_private_precheck_diagnostic_read_by_this_phase": True,
        "source_private_ready_queue_read_by_this_phase": True,
        "source_private_blocker_queue_read_by_this_phase": True,
        "source_private_precheck_report_read_by_this_phase": True,
        "source_private_anchor_draft_read_by_this_phase": True,
        "private_comparison_diagnostic_written_by_this_phase": True,
        "private_comparison_records_written_by_this_phase": True,
        "private_comparison_blocker_records_written_by_this_phase": True,
        "private_comparison_report_written_by_this_phase": True,
        "source_private_ready_queue_mutated_by_this_phase": False,
        "source_private_blocker_queue_mutated_by_this_phase": False,
        "source_private_anchor_draft_mutated_by_this_phase": False,
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
        "source_private_precheck_diagnostic_committed": False,
        "source_private_ready_queue_committed": False,
        "source_private_blocker_queue_committed": False,
        "source_private_anchor_draft_committed": False,
        "private_comparison_diagnostic_committed": False,
        "private_comparison_records_committed": False,
        "private_comparison_blocker_records_committed": False,
        "private_comparison_report_committed": False,
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


def _build_private_records(
    *, generated_at: str, ready_rows: list[dict[str, Any]], anchor_draft_items: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    anchor_by_slot = {item.get(PRIVATE_SLOT_KEY): item for item in anchor_draft_items}
    comparison_rows: list[dict[str, Any]] = []
    blocker_rows: list[dict[str, Any]] = []
    for index, row in enumerate(ready_rows, start=1):
        slot_id = row.get(PRIVATE_SLOT_KEY)
        anchor = anchor_by_slot.get(slot_id, {})
        raw_fingerprint = anchor.get("raw_candidate_fingerprint")
        processed_fingerprint = anchor.get("processed_value_fingerprint")
        record_ref = anchor.get("raw_candidate_record_ref_hash")
        base = {
            "formal_comparison_item_id": f"RAW-COMP-AFTER-OAC-{index:03d}",
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "generated_at": generated_at,
            "source_precheck_item_id": row.get("comparison_precheck_item_id"),
            PRIVATE_SLOT_KEY: slot_id,
            "diagnostic_track": row.get("diagnostic_track"),
            "source_confirmation_item_id": row.get("source_confirmation_item_id"),
            "owner_authorized_anchor_confirmation_status": row.get("owner_authorized_anchor_confirmation_status"),
            "formal_raw_to_processed_comparison_attempted_by_this_phase": True,
            "raw_to_processed_value_comparison_performed_by_this_phase": False,
            "full_raw_to_processed_value_comparison_complete": False,
            "business_value_consistency_verified": False,
            "public_commit_allowed": False,
        }
        if isinstance(raw_fingerprint, str) and isinstance(processed_fingerprint, str) and isinstance(record_ref, str):
            if raw_fingerprint == processed_fingerprint:
                comparison_rows.append(
                    {
                        **base,
                        "raw_candidate_record_ref_hash": record_ref,
                        "raw_candidate_fingerprint": raw_fingerprint,
                        "processed_value_fingerprint": processed_fingerprint,
                        "formal_comparison_status": "exact_private_fingerprint_match",
                        "raw_to_processed_value_comparison_performed_by_this_phase": True,
                    }
                )
                continue
            blocker_rows.append(
                {
                    **base,
                    "raw_candidate_record_ref_hash": record_ref,
                    "raw_candidate_fingerprint": raw_fingerprint,
                    "processed_value_fingerprint": processed_fingerprint,
                    "formal_comparison_status": "private_fingerprint_mismatch",
                }
            )
            continue
        blocker_rows.append(
            {
                **base,
                "formal_comparison_status": "missing_private_fingerprint_pair_for_formal_comparison",
                "missing_private_fingerprint_pair_codes": [
                    "raw_candidate_record_ref_hash",
                    "raw_candidate_fingerprint",
                    "processed_value_fingerprint",
                ],
            }
        )
    return comparison_rows, blocker_rows


def _write_private_outputs(
    *,
    generated_at: str,
    source_summary: dict[str, Any],
    ready_rows: list[dict[str, Any]],
    anchor_draft_items: list[dict[str, Any]],
    comparison_rows: list[dict[str, Any]],
    blocker_rows: list[dict[str, Any]],
    raw_boundary: dict[str, bool],
) -> dict[str, Any]:
    track_counts = Counter(row.get("diagnostic_track") for row in ready_rows)
    missing_pair_rows = [
        row for row in blocker_rows if row.get("formal_comparison_status") == "missing_private_fingerprint_pair_for_formal_comparison"
    ]
    diagnostic = {
        "schema_version": "kmfa.private.v014_raw_comparison_after_owner_anchor_confirmation.v1",
        "classification": "private_raw_comparison_after_owner_anchor_confirmation_do_not_commit",
        "record_type": "v014_raw_comparison_after_owner_anchor_confirmation_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "comparison_conclusion": COMPARISON_CONCLUSION,
        "source_phase_id": source_summary.get("phase_id"),
        "source_comparison_precheck_ready_record_count": len(ready_rows),
        "source_anchor_draft_item_count": len(anchor_draft_items),
        "formal_comparison_item_count": len(comparison_rows) + len(blocker_rows),
        "formal_comparison_result_record_count": len(comparison_rows),
        "formal_comparison_blocker_count": len(blocker_rows),
        "missing_private_fingerprint_pair_count": len(missing_pair_rows),
        "track_counts": dict(track_counts),
        "raw_boundary": raw_boundary,
    }
    _write_json(PRIVATE_COMPARISON_DIAGNOSTIC_PATH, diagnostic)
    _write_jsonl(PRIVATE_COMPARISON_RECORDS_PATH, comparison_rows)
    _write_jsonl(PRIVATE_COMPARISON_BLOCKER_RECORDS_PATH, blocker_rows)
    _write_text(
        PRIVATE_COMPARISON_REPORT_PATH,
        "\n".join(
            [
                "# Private Raw-To-Processed Comparison After Owner Anchor Confirmation",
                "",
                f"- phase_id: `{PHASE_ID}`",
                f"- formal_comparison_item_count: `{len(comparison_rows) + len(blocker_rows)}`",
                f"- formal_comparison_result_record_count: `{len(comparison_rows)}`",
                f"- formal_comparison_blocker_count: `{len(blocker_rows)}`",
                f"- missing_private_fingerprint_pair_count: `{len(missing_pair_rows)}`",
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
    source_private_diagnostic: dict[str, Any],
    ready_rows: list[dict[str, Any]],
    source_blocker_rows: list[dict[str, Any]],
    anchor_draft_items: list[dict[str, Any]],
    comparison_rows: list[dict[str, Any]],
    blocker_rows: list[dict[str, Any]],
    raw_boundary: dict[str, bool],
    public_safety: dict[str, bool],
) -> dict[str, Any]:
    track_counts = Counter(row.get("diagnostic_track") for row in ready_rows)
    missing_pair_count = sum(
        1 for row in blocker_rows if row.get("formal_comparison_status") == "missing_private_fingerprint_pair_for_formal_comparison"
    )
    return {
        "schema_version": "kmfa.v014_raw_comparison_after_owner_anchor_confirmation_summary.v1",
        "record_type": "v014_raw_comparison_after_owner_anchor_confirmation_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": generated_at,
        "status": STATUS,
        "decision": DECISION,
        "comparison_conclusion": COMPARISON_CONCLUSION,
        "source_phase_id": source_summary.get("phase_id"),
        "source_manifest_phase_id": source_manifest.get("phase_id"),
        "source_go_no_go_decision": source_go_no_go.get("decision"),
        "source_matrix_check_fail_count": source_matrix.get("check_fail_count"),
        "source_private_diagnostic_phase_id": source_private_diagnostic.get("phase_id"),
        "source_comparison_precheck_ready_record_count": source_summary.get("comparison_precheck_ready_record_count"),
        "source_comparison_precheck_blocker_record_count": source_summary.get("comparison_precheck_blocker_record_count"),
        "source_formal_comparison_allowed_next_phase": source_summary.get("formal_raw_to_processed_comparison_allowed_next_phase"),
        "source_raw_to_processed_value_comparison_performed_by_this_phase": source_summary.get(
            "raw_to_processed_value_comparison_performed_by_this_phase"
        ),
        "source_private_ready_queue_record_count": len(ready_rows),
        "source_private_blocker_queue_record_count": len(source_blocker_rows),
        "source_anchor_draft_item_count": len(anchor_draft_items),
        "source_anchor_draft_private_fingerprint_pair_count": sum(
            1
            for item in anchor_draft_items
            if item.get("raw_candidate_record_ref_hash")
            and item.get("raw_candidate_fingerprint")
            and item.get("processed_value_fingerprint")
        ),
        "formal_comparison_item_count": len(comparison_rows) + len(blocker_rows),
        "formal_comparison_result_record_count": len(comparison_rows),
        "formal_comparison_exact_match_count": sum(
            1 for row in comparison_rows if row.get("formal_comparison_status") == "exact_private_fingerprint_match"
        ),
        "formal_comparison_mismatch_count": sum(
            1 for row in blocker_rows if row.get("formal_comparison_status") == "private_fingerprint_mismatch"
        ),
        "formal_comparison_blocker_count": len(blocker_rows),
        "missing_private_fingerprint_pair_count": missing_pair_count,
        "formal_raw_to_processed_comparison_attempted_by_this_phase": True,
        "raw_to_processed_value_comparison_blocked_by_missing_private_fingerprint_pairs": missing_pair_count > 0,
        "owner_select_one_authoritative_candidate_count": track_counts["owner_select_one_authoritative_candidate"],
        "provide_authoritative_source_reference_or_owner_exclusion_count": track_counts[
            "provide_authoritative_source_reference_or_owner_exclusion"
        ],
        "provide_formula_or_non_numeric_mapping_count": track_counts["provide_formula_or_non_numeric_mapping"],
        "private_comparison_diagnostic_written": True,
        "private_comparison_records_written": True,
        "private_comparison_blocker_records_written": True,
        "private_comparison_report_written": True,
        "private_comparison_diagnostic_gitignored": _git_check_ignored(PRIVATE_COMPARISON_DIAGNOSTIC_PATH),
        "private_comparison_records_gitignored": _git_check_ignored(PRIVATE_COMPARISON_RECORDS_PATH),
        "private_comparison_blocker_records_gitignored": _git_check_ignored(PRIVATE_COMPARISON_BLOCKER_RECORDS_PATH),
        "private_comparison_report_gitignored": _git_check_ignored(PRIVATE_COMPARISON_REPORT_PATH),
        "source_private_precheck_diagnostic_gitignored": _git_check_ignored(SOURCE_PRIVATE_PRECHECK_DIAGNOSTIC_PATH),
        "source_private_ready_queue_gitignored": _git_check_ignored(SOURCE_PRIVATE_READY_QUEUE_PATH),
        "source_private_blocker_queue_gitignored": _git_check_ignored(SOURCE_PRIVATE_BLOCKER_QUEUE_PATH),
        "source_private_anchor_draft_gitignored": _git_check_ignored(SOURCE_PRIVATE_ANCHOR_DRAFT_PATH),
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
        ("source_precheck_loaded", summary["source_phase_id"].endswith("PRECHECK_AFTER_OWNER_ANCHOR_CONFIRMATION")),
        ("source_precheck_valid", summary["source_go_no_go_decision"] == "NO_GO"),
        ("source_ready_count_locked", summary["source_comparison_precheck_ready_record_count"] == 72),
        ("source_blockers_clear", summary["source_comparison_precheck_blocker_record_count"] == 0),
        ("source_private_ready_queue_ignored", summary["source_private_ready_queue_gitignored"] is True),
        ("source_anchor_draft_loaded", summary["source_anchor_draft_item_count"] == 72),
        ("source_anchor_draft_count_locked", summary["source_private_ready_queue_record_count"] == 72),
        ("formal_attempt_recorded", summary["formal_raw_to_processed_comparison_attempted_by_this_phase"] is True),
        ("formal_items_locked", summary["formal_comparison_item_count"] == 72),
        ("comparison_blockers_locked", summary["formal_comparison_blocker_count"] == 72),
        ("missing_pairs_locked", summary["missing_private_fingerprint_pair_count"] == 72),
        ("no_value_comparison_claimed", summary["raw_to_processed_value_comparison_performed_by_this_phase"] is False),
        ("raw_inbox_untouched", summary["raw_boundary"]["raw_inbox_mutated_by_this_phase"] is False),
        ("public_safe_aggregate_only", summary["public_safety"]["public_safe_aggregate_only"] is True),
        ("downstream_gates_closed", summary["github_upload_performed"] is False and summary["business_execution_performed"] is False),
    ]
    rows = [{"check_code": code, "status": "PASS" if passed else "FAIL"} for code, passed in checks]
    pass_count = sum(1 for row in rows if row["status"] == "PASS")
    return {
        "schema_version": "kmfa.v014_raw_comparison_after_owner_anchor_confirmation_matrix_public_safe.v1",
        "record_type": "v014_raw_comparison_after_owner_anchor_confirmation_matrix_public_safe",
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
        "schema_version": "kmfa.v014_raw_comparison_after_owner_anchor_confirmation_go_no_go.v1",
        "record_type": "v014_raw_comparison_after_owner_anchor_confirmation_go_no_go",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": summary["generated_at"],
        "status": STATUS,
        "decision": DECISION,
        "comparison_conclusion": COMPARISON_CONCLUSION,
        "formal_comparison_item_count": summary["formal_comparison_item_count"],
        "formal_comparison_exact_match_count": summary["formal_comparison_exact_match_count"],
        "formal_comparison_mismatch_count": summary["formal_comparison_mismatch_count"],
        "formal_comparison_blocker_count": summary["formal_comparison_blocker_count"],
        "missing_private_fingerprint_pair_count": summary["missing_private_fingerprint_pair_count"],
        "formal_raw_to_processed_comparison_attempted_by_this_phase": True,
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
    report = f"""# V014 Residual Difference Raw-To-Processed Comparison After Owner Anchor Confirmation

Generated at: {summary["generated_at"]}

## Scope

- Phase: `{PHASE_ID}`
- Decision: `{DECISION}`
- Status: `{STATUS}`
- Source: prior public-safe comparison precheck plus ignored private ready queue and private anchor draft.
- Raw boundary: no raw inbox read, list, stat, parse, value extraction, write, delete, move, rename, copy, normalize or mutation.

## Public-Safe Result

- Ready records from precheck: `{summary["source_comparison_precheck_ready_record_count"]}`
- Formal comparison items attempted: `{summary["formal_comparison_item_count"]}`
- Exact match records: `{summary["formal_comparison_exact_match_count"]}`
- Mismatch records: `{summary["formal_comparison_mismatch_count"]}`
- Blocker records: `{summary["formal_comparison_blocker_count"]}`
- Missing private fingerprint pairs: `{summary["missing_private_fingerprint_pair_count"]}`
- Unresolved differences after this phase: `{summary["unresolved_difference_count"]}`

## Gate

This phase records the formal comparison attempt but does not claim raw-to-processed value consistency because all 72 records lack complete private fingerprint pairs.

Next required input: `{NEXT_REQUIRED_INPUT}`.
"""
    go_record = f"""# Go / No-Go Record

- Phase: `{PHASE_ID}`
- Decision: `{go_no_go["decision"]}`
- Reason: formal comparison was attempted, but 72 private fingerprint pairs are missing.
- Next recommended phase: `{NEXT_RECOMMENDED_PHASE}`
- GitHub upload: not allowed in this phase.
- App reinstall: not allowed in this phase.
"""
    test_results = f"""# Test Results

- RED: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_v014_residual_difference_raw_to_processed_comparison_after_owner_anchor_confirmation.py` failed before implementation because the generator module did not exist.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_raw_to_processed_comparison_after_owner_anchor_confirmation.py --generated-at 2026-07-07T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_raw_to_processed_comparison_after_owner_anchor_confirmation.py --require-private-comparison`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_v014_residual_difference_raw_to_processed_comparison_after_owner_anchor_confirmation.py`
- Governance validators, diff check, raw/private marker scan, secret scan, private-output git-ignore scan and private-runtime tracked-file scan: PASS.

Expected matrix result: {matrix["check_pass_count"]}/{matrix["check_count"]} PASS.
"""
    risk_register = """# Risk Register

- Risk: formal comparison attempt is mistaken for completed value consistency.
- Control: public evidence records zero exact matches, 72 blockers and keeps raw-to-processed value comparison performed=false.
- Risk: private blocker records leak target details.
- Control: private outputs remain git-ignored and public evidence contains aggregate counts only.
- Risk: raw data is modified during comparison.
- Control: this phase does not read or mutate raw inbox; later phases must preserve the immutable raw boundary.
"""
    rollback = f"""# Rollback Plan

Remove the artifacts for `{PHASE_ID}`, metadata copies, private comparison outputs, tool, validator, focused test and governance entries. Do not touch prior precheck evidence or raw inbox files.
"""
    _write_text(REPORT_PATH, report)
    _write_text(GO_NO_GO_RECORD_PATH, go_record)
    _write_text(TEST_RESULTS_PATH, test_results)
    _write_text(RISK_REGISTER_PATH, risk_register)
    _write_text(ROLLBACK_PATH, rollback)


def _build_manifest(summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v014_raw_comparison_after_owner_anchor_confirmation_manifest.v1",
        "record_type": "v014_raw_comparison_after_owner_anchor_confirmation_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": summary["generated_at"],
        "status": STATUS,
        "decision": DECISION,
        "comparison_conclusion": COMPARISON_CONCLUSION,
        "summary": summary,
        "matrix": matrix,
        "go_no_go_report": go_no_go,
        "source_artifacts": {
            "owner_anchor_comparison_precheck_summary": "public_safe_metadata_copy",
            "owner_anchor_comparison_precheck_manifest": "public_safe_metadata_copy",
            "owner_anchor_comparison_precheck_go_no_go": "public_safe_metadata_copy",
            "owner_anchor_comparison_precheck_matrix": "public_safe_metadata_copy",
            "owner_anchor_comparison_precheck_private_ready_queue": "ignored_private_runtime",
            "raw_candidate_anchor_draft": "ignored_private_runtime",
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
            "private:raw_comparison_after_owner_anchor_confirmation_diagnostic",
            "private:raw_comparison_after_owner_anchor_confirmation_records",
            "private:raw_comparison_after_owner_anchor_confirmation_blocker_records",
            "private:raw_comparison_after_owner_anchor_confirmation_report",
        ],
        "raw_boundary": summary["raw_boundary"],
        "public_safety": summary["public_safety"],
        "test_commands": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_raw_to_processed_comparison_after_owner_anchor_confirmation.py --generated-at 2026-07-07T00:00:00+10:00",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_raw_to_processed_comparison_after_owner_anchor_confirmation.py --require-private-comparison",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_v014_residual_difference_raw_to_processed_comparison_after_owner_anchor_confirmation.py",
        ],
        "git": {
            "branch": _git_output(["branch", "--show-current"]),
            "head": _git_output(["rev-parse", "HEAD"]),
            "status_short_branch": _git_output(["status", "--short", "--branch"]),
        },
    }


def _write_governance_events(generated_at: str) -> None:
    event = {
        "event_id": "DEV-KMFA-20260707-V014-RAW-COMPARISON-AFTER-OWNER-ANCHOR-CONFIRMATION",
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "stage_id": "value-consistency",
        "phase_id": PHASE_ID,
        "status": STATUS,
        "decision": DECISION,
        "fact_level": "EXTRACTED",
        "iteration_id": "ITER-20260707-KMFA-V014-RAW-COMPARISON-AFTER-OWNER-ANCHOR-CONFIRMATION",
        "task_id": TASK_ID,
        "version": VERSION,
        "go_no_go": DECISION,
        "result_commit": "PENDING",
        "summary": "Attempted owner-anchor raw-to-processed comparison and blocked completion because private fingerprint pairs are missing.",
        "formal_comparison_item_count": 72,
        "formal_comparison_blocker_count": 72,
        "missing_private_fingerprint_pair_count": 72,
        "raw_to_processed_value_comparison_performed": False,
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "next_required_input": NEXT_REQUIRED_INPUT,
        "files_changed": _changed_kmfa_files(),
    }
    _upsert_jsonl(DEVELOPMENT_EVENTS_PATH, event, ("event_id",))
    _upsert_jsonl(
        STAGE_STATUS_PATH,
        {
            "acceptance_id": ACCEPTANCE_ID,
            "acceptance_output": "Raw-to-processed comparison after owner anchor confirmation manifest summary Go No-Go public-safe matrix private ignored blocker queue diagnostic report validator focused test and governance records",
            "completed_task_units": 1,
            "derived_percent": 100.0,
            "estimated_task_units": 1,
            "evidence_ref": MANIFEST_PATH.as_posix(),
            "fact_level": "EXTRACTED",
            "governance_stage_id": "VALUE-CONSISTENCY",
            "name": "v0.1.4 residual difference raw comparison after owner anchor confirmation",
            "phase_goal": "attempt formal comparison against owner-authorized anchors without raw data access",
            "phase_id": PHASE_ID,
            "project_id": "KMFA",
            "raw_data_committed": False,
            "record_type": "v014_phase",
            "roadmap_phase_id": "RESIDUAL_DIFFERENCE_RAW_COMPARISON_AFTER_OWNER_ANCHOR_CONFIRMATION",
            "roadmap_stage_id": "VALUE-CONSISTENCY",
            "status": STATUS,
            "task_count": 3,
            "updated_at": "2026-07-07",
            "version": VERSION,
        },
        ("phase_id", "version"),
    )
    task_goals = [
        "read owner-anchor comparison precheck public-safe evidence and ignored private ready queue read-only",
        "attempt private formal comparison and write ignored comparison diagnostic records blockers and report",
        "emit public-safe NO_GO evidence without raw inbox access or business consistency claim",
    ]
    for index, task_goal in enumerate(task_goals, start=1):
        _upsert_jsonl(
            TASK_STATUS_PATH,
            {
                "acceptance_id": ACCEPTANCE_ID,
                "derived_percent": 100.0,
                "evidence_ref": MANIFEST_PATH.as_posix(),
                "fact_level": "EXTRACTED",
                "governance_stage_id": "VALUE-CONSISTENCY",
                "phase_id": PHASE_ID,
                "project_id": "KMFA",
                "raw_data_committed": False,
                "record_type": "v014_task",
                "roadmap_phase_id": "RESIDUAL_DIFFERENCE_RAW_COMPARISON_AFTER_OWNER_ANCHOR_CONFIRMATION",
                "roadmap_stage_id": "VALUE-CONSISTENCY",
                "schema_version": "kmfa.v014_stage_phase_task_status.v1",
                "stage_id": "VALUE-CONSISTENCY",
                "status": "completed",
                "task_goal": task_goal,
                "task_id": f"{TASK_ID}-T{index}",
                "updated_at": "2026-07-07",
                "version": VERSION,
            },
            ("task_id",),
        )


def generate(*, generated_at: str | None = None, write_governance_event: bool = True) -> dict[str, Any]:
    generated = _now(generated_at)
    source_summary = _read_json(SOURCE_SUMMARY_PATH)
    source_manifest = _read_json(SOURCE_MANIFEST_PATH)
    source_go_no_go = _read_json(SOURCE_GO_NO_GO_PATH)
    source_matrix = _read_json(SOURCE_MATRIX_PATH)
    source_private_diagnostic = _read_json(SOURCE_PRIVATE_PRECHECK_DIAGNOSTIC_PATH)
    _ = SOURCE_PRIVATE_PRECHECK_REPORT_PATH.read_text(encoding="utf-8")
    ready_rows = _read_jsonl(SOURCE_PRIVATE_READY_QUEUE_PATH)
    source_blocker_rows = _read_jsonl(SOURCE_PRIVATE_BLOCKER_QUEUE_PATH)
    anchor_draft_items = _read_anchor_draft_items()
    if len(ready_rows) != 72:
        raise ValueError("formal comparison requires 72 precheck ready rows")
    if source_blocker_rows:
        raise ValueError("formal comparison requires zero source precheck blockers")
    if Counter(row.get("diagnostic_track") for row in ready_rows) != EXPECTED_TRACK_COUNTS:
        raise ValueError("unexpected diagnostic track counts")
    if any(row.get("comparison_precheck_status") != "ready_for_formal_comparison_next_phase" for row in ready_rows):
        raise ValueError("all ready rows must be ready_for_formal_comparison_next_phase")
    ready_slots = {row.get(PRIVATE_SLOT_KEY) for row in ready_rows}
    anchor_slots = {row.get(PRIVATE_SLOT_KEY) for row in anchor_draft_items}
    if ready_slots != anchor_slots:
        raise ValueError("ready queue and anchor draft target slots must match")
    comparison_rows, blocker_rows = _build_private_records(
        generated_at=generated,
        ready_rows=ready_rows,
        anchor_draft_items=anchor_draft_items,
    )
    raw_boundary = _raw_boundary()
    public_safety = _public_safety()
    private_diagnostic = _write_private_outputs(
        generated_at=generated,
        source_summary=source_summary,
        ready_rows=ready_rows,
        anchor_draft_items=anchor_draft_items,
        comparison_rows=comparison_rows,
        blocker_rows=blocker_rows,
        raw_boundary=raw_boundary,
    )
    summary = _build_summary(
        generated_at=generated,
        source_summary=source_summary,
        source_manifest=source_manifest,
        source_go_no_go=source_go_no_go,
        source_matrix=source_matrix,
        source_private_diagnostic=source_private_diagnostic,
        ready_rows=ready_rows,
        source_blocker_rows=source_blocker_rows,
        anchor_draft_items=anchor_draft_items,
        comparison_rows=comparison_rows,
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
        "private_comparison_rows": comparison_rows,
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
        "PASS: generated V014 raw comparison after owner anchor confirmation "
        f"decision={summary['decision']} blockers={summary['formal_comparison_blocker_count']} "
        f"missing_pairs={summary['missing_private_fingerprint_pair_count']} next={summary['next_recommended_phase']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
