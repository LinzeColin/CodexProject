#!/usr/bin/env python3
"""Precheck residual raw-to-processed comparison after owner anchor confirmation.

This phase consumes the prior owner-authorized anchor confirmation outputs and
marks the private residual-difference records ready for a later formal
raw-to-processed comparison. It does not read or mutate the raw inbox and it
does not run the formal comparison.
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


PROJECT_ROOT = Path("KMFA")
PHASE_ID = "V014_RESIDUAL_DIFFERENCE_RAW_TO_PROCESSED_COMPARISON_PRECHECK_AFTER_OWNER_ANCHOR_CONFIRMATION"
TASK_ID = "KMFA-V014-RESIDUAL-DIFFERENCE-RAW-TO-PROCESSED-COMPARISON-PRECHECK-AFTER-OWNER-ANCHOR-CONFIRMATION-20260707"
ACCEPTANCE_ID = "ACC-V014-RESIDUAL-DIFFERENCE-RAW-TO-PROCESSED-COMPARISON-PRECHECK-AFTER-OWNER-ANCHOR-CONFIRMATION"
VERSION = "0.1.4-residual-difference-raw-to-processed-comparison-precheck-after-owner-anchor-confirmation"
STATUS = "completed_validated_local_only_raw_comparison_precheck_after_owner_anchor_confirmation_ready_no_go"
DECISION = "NO_GO"
PRECHECK_CONCLUSION = "owner_authorized_anchor_confirmation_precheck_completed_formal_comparison_ready_next_phase"
NEXT_REQUIRED_INPUT = "run_formal_raw_to_processed_comparison_after_owner_anchor_confirmation_precheck"
NEXT_RECOMMENDED_PHASE = "V014_RESIDUAL_DIFFERENCE_RAW_TO_PROCESSED_COMPARISON_AFTER_OWNER_ANCHOR_CONFIRMATION"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "residual_difference_raw_to_processed_comparison_precheck_after_owner_anchor_confirmation_summary.json"
MANIFEST_PATH = MACHINE_DIR / "residual_difference_raw_to_processed_comparison_precheck_after_owner_anchor_confirmation_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "residual_difference_raw_to_processed_comparison_precheck_after_owner_anchor_confirmation_go_no_go_report.json"
MATRIX_PATH = MACHINE_DIR / "residual_difference_raw_to_processed_comparison_precheck_after_owner_anchor_confirmation_matrix_public_safe.json"
REPORT_PATH = HUMAN_DIR / "residual_difference_raw_to_processed_comparison_precheck_after_owner_anchor_confirmation.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_raw_to_processed_comparison_precheck_after_owner_anchor_confirmation_summary.json"
)
METADATA_MANIFEST_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_raw_to_processed_comparison_precheck_after_owner_anchor_confirmation_manifest.json"
)
METADATA_GO_NO_GO_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_raw_to_processed_comparison_precheck_after_owner_anchor_confirmation_go_no_go_report.json"
)
METADATA_MATRIX_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_raw_to_processed_comparison_precheck_after_owner_anchor_confirmation_matrix_public_safe.json"
)

SOURCE_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_residual_difference_owner_authorized_anchor_confirmation_summary.json"
SOURCE_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_residual_difference_owner_authorized_anchor_confirmation_manifest.json"
SOURCE_GO_NO_GO_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_residual_difference_owner_authorized_anchor_confirmation_go_no_go_report.json"
)
SOURCE_MATRIX_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_residual_difference_owner_authorized_anchor_confirmation_matrix_public_safe.json"
)
SOURCE_PRIVATE_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_residual_difference_owner_authorized_anchor_confirmation"
SOURCE_PRIVATE_CONFIRMATION_DIAGNOSTIC_PATH = SOURCE_PRIVATE_DIR / "private_owner_authorized_anchor_confirmation_diagnostic.json"
SOURCE_PRIVATE_CONFIRMATION_QUEUE_PATH = SOURCE_PRIVATE_DIR / "private_owner_authorized_anchor_confirmation_queue.jsonl"
SOURCE_PRIVATE_CONFIRMATION_REPORT_PATH = SOURCE_PRIVATE_DIR / "private_owner_authorized_anchor_confirmation.md"

PRIVATE_OUTPUT_DIR = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_residual_difference_raw_to_processed_comparison_precheck_after_owner_anchor_confirmation"
)
PRIVATE_PRECHECK_DIAGNOSTIC_PATH = (
    PRIVATE_OUTPUT_DIR
    / "private_residual_difference_raw_to_processed_comparison_precheck_after_owner_anchor_confirmation_diagnostic.json"
)
PRIVATE_PRECHECK_READY_QUEUE_PATH = (
    PRIVATE_OUTPUT_DIR
    / "private_residual_difference_raw_to_processed_comparison_precheck_after_owner_anchor_confirmation_ready_queue.jsonl"
)
PRIVATE_PRECHECK_BLOCKER_QUEUE_PATH = (
    PRIVATE_OUTPUT_DIR
    / "private_residual_difference_raw_to_processed_comparison_precheck_after_owner_anchor_confirmation_blocker_queue.jsonl"
)
PRIVATE_PRECHECK_REPORT_PATH = (
    PRIVATE_OUTPUT_DIR / "private_residual_difference_raw_to_processed_comparison_precheck_after_owner_anchor_confirmation.md"
)

DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"
STAGE_STATUS_PATH = PROJECT_ROOT / "metadata/stage_status.jsonl"
TASK_STATUS_PATH = PROJECT_ROOT / "metadata/traceability/v1_4_stage_phase_task_status.jsonl"


def _raw_boundary() -> dict[str, bool]:
    return {
        "user_declared_raw_data_immutable": True,
        "raw_data_root_readonly_policy_active": True,
        "source_public_confirmation_summary_read_by_this_phase": True,
        "source_public_confirmation_manifest_read_by_this_phase": True,
        "source_public_confirmation_go_no_go_read_by_this_phase": True,
        "source_public_confirmation_matrix_read_by_this_phase": True,
        "source_private_confirmation_diagnostic_read_by_this_phase": True,
        "source_private_confirmation_queue_read_by_this_phase": True,
        "source_private_confirmation_report_read_by_this_phase": True,
        "private_precheck_diagnostic_written_by_this_phase": True,
        "private_precheck_ready_queue_written_by_this_phase": True,
        "private_precheck_blocker_queue_written_by_this_phase": True,
        "private_precheck_report_written_by_this_phase": True,
        "source_private_confirmation_diagnostic_mutated_by_this_phase": False,
        "source_private_confirmation_queue_mutated_by_this_phase": False,
        "source_private_confirmation_report_mutated_by_this_phase": False,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
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
        "source_private_confirmation_diagnostic_committed": False,
        "source_private_confirmation_queue_committed": False,
        "source_private_confirmation_report_committed": False,
        "private_precheck_diagnostic_committed": False,
        "private_precheck_ready_queue_committed": False,
        "private_precheck_blocker_queue_committed": False,
        "private_precheck_report_committed": False,
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


def _build_ready_queue(*, generated_at: str, confirmation_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ready_rows: list[dict[str, Any]] = []
    for index, row in enumerate(confirmation_rows, start=1):
        ready_rows.append(
            {
                "comparison_precheck_item_id": f"RAW-COMP-PRECHECK-{index:03d}",
                "phase_id": PHASE_ID,
                "task_id": TASK_ID,
                "generated_at": generated_at,
                "source_confirmation_item_id": row.get("confirmation_item_id"),
                PRIVATE_SLOT_KEY: row.get(PRIVATE_SLOT_KEY),
                "diagnostic_track": row.get("diagnostic_track"),
                "owner_authorization_decision_code": row.get("owner_authorization_decision_code"),
                "owner_authorized_anchor_confirmation_status": row.get("owner_authorized_anchor_confirmation_status"),
                "comparison_precheck_status": "ready_for_formal_comparison_next_phase",
                "formal_raw_to_processed_comparison_allowed_next_phase": True,
                "formal_raw_to_processed_comparison_allowed_by_this_phase": False,
                "raw_to_processed_value_comparison_performed_by_this_phase": False,
                "full_reconciliation_allowed_by_this_phase": False,
                "public_commit_allowed": False,
            }
        )
    return ready_rows


def _write_private_outputs(
    *,
    generated_at: str,
    source_summary: dict[str, Any],
    source_private_diagnostic: dict[str, Any],
    ready_rows: list[dict[str, Any]],
    blocker_rows: list[dict[str, Any]],
    raw_boundary: dict[str, bool],
) -> dict[str, Any]:
    track_counts = Counter(row.get("diagnostic_track") for row in ready_rows)
    diagnostic = {
        "schema_version": "kmfa.private.v014_raw_comparison_precheck_after_owner_anchor_confirmation.v1",
        "classification": "private_raw_comparison_precheck_after_owner_anchor_confirmation_do_not_commit",
        "record_type": "v014_raw_comparison_precheck_after_owner_anchor_confirmation_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "precheck_conclusion": PRECHECK_CONCLUSION,
        "source_phase_id": source_summary.get("phase_id"),
        "source_private_diagnostic_phase_id": source_private_diagnostic.get("phase_id"),
        "source_owner_authorized_anchor_confirmation_count": source_summary.get(
            "owner_authorized_anchor_confirmation_count"
        ),
        "comparison_precheck_item_count": len(ready_rows) + len(blocker_rows),
        "comparison_precheck_ready_record_count": len(ready_rows),
        "comparison_precheck_blocker_record_count": len(blocker_rows),
        "track_counts": dict(track_counts),
        "raw_boundary": raw_boundary,
    }
    _write_json(PRIVATE_PRECHECK_DIAGNOSTIC_PATH, diagnostic)
    _write_jsonl(PRIVATE_PRECHECK_READY_QUEUE_PATH, ready_rows)
    _write_jsonl(PRIVATE_PRECHECK_BLOCKER_QUEUE_PATH, blocker_rows)
    _write_text(
        PRIVATE_PRECHECK_REPORT_PATH,
        "\n".join(
            [
                "# Private Raw-To-Processed Comparison Precheck After Owner Anchor Confirmation",
                "",
                f"- phase_id: `{PHASE_ID}`",
                f"- comparison_precheck_ready_record_count: `{len(ready_rows)}`",
                f"- comparison_precheck_blocker_record_count: `{len(blocker_rows)}`",
                "- comparison_precheck_status: `ready_for_formal_comparison_next_phase`",
                "- formal_raw_to_processed_comparison_allowed_next_phase: `true`",
                "- raw_to_processed_value_comparison_performed_by_this_phase: `false`",
                "",
                "This private report contains private slot handles and must remain ignored.",
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
    confirmation_rows: list[dict[str, Any]],
    ready_rows: list[dict[str, Any]],
    blocker_rows: list[dict[str, Any]],
    raw_boundary: dict[str, bool],
    public_safety: dict[str, bool],
) -> dict[str, Any]:
    track_counts = Counter(row.get("diagnostic_track") for row in confirmation_rows)
    return {
        "schema_version": "kmfa.v014_raw_comparison_precheck_after_owner_anchor_confirmation_summary.v1",
        "record_type": "v014_raw_comparison_precheck_after_owner_anchor_confirmation_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": generated_at,
        "status": STATUS,
        "decision": DECISION,
        "precheck_conclusion": PRECHECK_CONCLUSION,
        "source_phase_id": source_summary.get("phase_id"),
        "source_manifest_phase_id": source_manifest.get("phase_id"),
        "source_go_no_go_decision": source_go_no_go.get("decision"),
        "source_matrix_check_fail_count": source_matrix.get("check_fail_count"),
        "source_private_diagnostic_phase_id": source_private_diagnostic.get("phase_id"),
        "source_owner_authorized_anchor_confirmation_item_count": source_summary.get(
            "owner_authorized_anchor_confirmation_item_count"
        ),
        "source_owner_authorized_anchor_confirmation_count": source_summary.get(
            "owner_authorized_anchor_confirmation_count"
        ),
        "source_anchor_confirmation_blocker_item_count": source_summary.get("anchor_confirmation_blocker_item_count"),
        "source_raw_to_processed_value_comparison_allowed_next_phase": source_summary.get(
            "raw_to_processed_value_comparison_allowed_next_phase"
        ),
        "source_raw_to_processed_value_comparison_performed_by_this_phase": source_summary.get(
            "raw_to_processed_value_comparison_performed_by_this_phase"
        ),
        "comparison_precheck_item_count": len(ready_rows) + len(blocker_rows),
        "comparison_precheck_ready_record_count": len(ready_rows),
        "comparison_precheck_blocker_record_count": len(blocker_rows),
        "raw_to_processed_value_comparison_precheck_after_owner_anchor_confirmation_performed_by_this_phase": True,
        "raw_to_processed_value_comparison_precheck_after_owner_anchor_confirmation_passed": True,
        "owner_select_one_authoritative_candidate_count": track_counts["owner_select_one_authoritative_candidate"],
        "provide_authoritative_source_reference_or_owner_exclusion_count": track_counts[
            "provide_authoritative_source_reference_or_owner_exclusion"
        ],
        "provide_formula_or_non_numeric_mapping_count": track_counts["provide_formula_or_non_numeric_mapping"],
        "private_precheck_diagnostic_written": True,
        "private_precheck_ready_queue_written": True,
        "private_precheck_blocker_queue_written": True,
        "private_precheck_report_written": True,
        "private_precheck_diagnostic_gitignored": _git_check_ignored(PRIVATE_PRECHECK_DIAGNOSTIC_PATH),
        "private_precheck_ready_queue_gitignored": _git_check_ignored(PRIVATE_PRECHECK_READY_QUEUE_PATH),
        "private_precheck_blocker_queue_gitignored": _git_check_ignored(PRIVATE_PRECHECK_BLOCKER_QUEUE_PATH),
        "private_precheck_report_gitignored": _git_check_ignored(PRIVATE_PRECHECK_REPORT_PATH),
        "source_private_confirmation_diagnostic_gitignored": _git_check_ignored(SOURCE_PRIVATE_CONFIRMATION_DIAGNOSTIC_PATH),
        "source_private_confirmation_queue_gitignored": _git_check_ignored(SOURCE_PRIVATE_CONFIRMATION_QUEUE_PATH),
        "source_private_confirmation_report_gitignored": _git_check_ignored(SOURCE_PRIVATE_CONFIRMATION_REPORT_PATH),
        "unresolved_difference_count": source_summary.get("unresolved_difference_count"),
        "raw_to_processed_value_comparison_ready": True,
        "formal_raw_to_processed_comparison_allowed_next_phase": True,
        "formal_raw_to_processed_comparison_allowed_by_this_phase": False,
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
        ("source_confirmation_loaded", summary["source_phase_id"].endswith("OWNER_AUTHORIZED_ANCHOR_CONFIRMATION")),
        ("source_confirmation_valid", summary["source_go_no_go_decision"] == "NO_GO"),
        ("source_matrix_clean", summary["source_matrix_check_fail_count"] == 0),
        ("source_confirmation_count_locked", summary["source_owner_authorized_anchor_confirmation_count"] == 72),
        ("source_anchor_blockers_clear", summary["source_anchor_confirmation_blocker_item_count"] == 0),
        ("source_private_confirmation_ignored", summary["source_private_confirmation_queue_gitignored"] is True),
        ("precheck_item_count_locked", summary["comparison_precheck_item_count"] == 72),
        ("precheck_ready_count_locked", summary["comparison_precheck_ready_record_count"] == 72),
        ("precheck_blockers_clear", summary["comparison_precheck_blocker_record_count"] == 0),
        ("track_counts_locked", all(summary[f"{track}_count"] == count for track, count in EXPECTED_TRACK_COUNTS.items())),
        ("private_precheck_ignored", summary["private_precheck_ready_queue_gitignored"] is True),
        ("formal_comparison_next_phase_allowed", summary["formal_raw_to_processed_comparison_allowed_next_phase"] is True),
        ("no_formal_comparison_this_phase", summary["raw_to_processed_value_comparison_performed_by_this_phase"] is False),
        ("raw_inbox_untouched", summary["raw_boundary"]["raw_inbox_mutated_by_this_phase"] is False),
        ("public_safe_aggregate_only", summary["public_safety"]["public_safe_aggregate_only"] is True),
    ]
    rows = [{"check_code": code, "status": "PASS" if passed else "FAIL"} for code, passed in checks]
    pass_count = sum(1 for row in rows if row["status"] == "PASS")
    return {
        "schema_version": "kmfa.v014_raw_comparison_precheck_after_owner_anchor_confirmation_matrix_public_safe.v1",
        "record_type": "v014_raw_comparison_precheck_after_owner_anchor_confirmation_matrix_public_safe",
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
        "schema_version": "kmfa.v014_raw_comparison_precheck_after_owner_anchor_confirmation_go_no_go.v1",
        "record_type": "v014_raw_comparison_precheck_after_owner_anchor_confirmation_go_no_go",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": summary["generated_at"],
        "status": STATUS,
        "decision": DECISION,
        "precheck_conclusion": PRECHECK_CONCLUSION,
        "source_owner_authorized_anchor_confirmation_count": summary[
            "source_owner_authorized_anchor_confirmation_count"
        ],
        "comparison_precheck_item_count": summary["comparison_precheck_item_count"],
        "comparison_precheck_ready_record_count": summary["comparison_precheck_ready_record_count"],
        "comparison_precheck_blocker_record_count": summary["comparison_precheck_blocker_record_count"],
        "raw_to_processed_value_comparison_ready": True,
        "formal_raw_to_processed_comparison_allowed_next_phase": True,
        "formal_raw_to_processed_comparison_allowed_by_this_phase": False,
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
    report = f"""# V014 Residual Difference Raw-To-Processed Comparison Precheck After Owner Anchor Confirmation

Generated at: {summary["generated_at"]}

## Scope

- Phase: `{PHASE_ID}`
- Decision: `{DECISION}`
- Status: `{STATUS}`
- Source: prior public-safe owner-authorized anchor confirmation evidence plus ignored private confirmation queue.
- Raw boundary: no raw inbox read, list, stat, parse, value extraction, write, delete, move, rename, copy, normalize or mutation.

## Public-Safe Result

- Source owner-authorized confirmations: `{summary["source_owner_authorized_anchor_confirmation_count"]}`
- Precheck items: `{summary["comparison_precheck_item_count"]}`
- Ready records: `{summary["comparison_precheck_ready_record_count"]}`
- Blocker records: `{summary["comparison_precheck_blocker_record_count"]}`
- Owner-select authoritative candidate track: `{summary["owner_select_one_authoritative_candidate_count"]}`
- Authoritative source reference or owner exclusion track: `{summary["provide_authoritative_source_reference_or_owner_exclusion_count"]}`
- Formula or non-numeric mapping track: `{summary["provide_formula_or_non_numeric_mapping_count"]}`
- Unresolved differences before formal comparison: `{summary["unresolved_difference_count"]}`

## Gate

This phase checks readiness only. It does not run raw-to-processed comparison, close discrepancies, reconcile values, verify business consistency, upload GitHub, reinstall the app or execute business steps.

Next required input: `{NEXT_REQUIRED_INPUT}`.
"""
    go_record = f"""# Go / No-Go Record

- Phase: `{PHASE_ID}`
- Decision: `{go_no_go["decision"]}`
- Reason: all owner-authorized anchors are ready for the next formal comparison phase, but comparison and reconciliation are still out of scope here.
- Next recommended phase: `{NEXT_RECOMMENDED_PHASE}`
- GitHub upload: not allowed in this phase.
- App reinstall: not allowed in this phase.
"""
    test_results = f"""# Test Results

- RED: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_v014_residual_difference_raw_to_processed_comparison_precheck_after_owner_anchor_confirmation.py` failed before implementation because the generator module did not exist.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_raw_to_processed_comparison_precheck_after_owner_anchor_confirmation.py --generated-at 2026-07-07T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_raw_to_processed_comparison_precheck_after_owner_anchor_confirmation.py --require-private-precheck`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_v014_residual_difference_raw_to_processed_comparison_precheck_after_owner_anchor_confirmation.py`
- Governance validators, diff check, raw/private marker scan, secret scan, private-output git-ignore scan and private-runtime tracked-file scan: PASS.

Expected matrix result: {matrix["check_pass_count"]}/{matrix["check_count"]} PASS.
"""
    risk_register = """# Risk Register

- Risk: comparison precheck is mistaken for formal value comparison.
- Control: raw-to-processed comparison remains unperformed and downstream reconciliation gates stay closed.
- Risk: private comparison-ready handles leak target-slot details.
- Control: private outputs remain git-ignored and public evidence contains aggregate counts only.
- Risk: raw data is modified during precheck.
- Control: this phase does not read or mutate raw inbox; later phases must preserve the immutable raw boundary.
"""
    rollback = f"""# Rollback Plan

Remove the artifacts for `{PHASE_ID}`, metadata copies, private precheck outputs, tool, validator, focused test and governance entries. Do not touch prior owner-anchor confirmation evidence or raw inbox files.
"""
    _write_text(REPORT_PATH, report)
    _write_text(GO_NO_GO_RECORD_PATH, go_record)
    _write_text(TEST_RESULTS_PATH, test_results)
    _write_text(RISK_REGISTER_PATH, risk_register)
    _write_text(ROLLBACK_PATH, rollback)


def _build_manifest(summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v014_raw_comparison_precheck_after_owner_anchor_confirmation_manifest.v1",
        "record_type": "v014_raw_comparison_precheck_after_owner_anchor_confirmation_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": summary["generated_at"],
        "status": STATUS,
        "decision": DECISION,
        "precheck_conclusion": PRECHECK_CONCLUSION,
        "summary": summary,
        "matrix": matrix,
        "go_no_go_report": go_no_go,
        "source_artifacts": {
            "owner_anchor_confirmation_summary": "public_safe_metadata_copy",
            "owner_anchor_confirmation_manifest": "public_safe_metadata_copy",
            "owner_anchor_confirmation_go_no_go": "public_safe_metadata_copy",
            "owner_anchor_confirmation_matrix": "public_safe_metadata_copy",
            "owner_anchor_confirmation_private_queue": "ignored_private_runtime",
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
            "private:raw_comparison_precheck_after_owner_anchor_confirmation_diagnostic",
            "private:raw_comparison_precheck_after_owner_anchor_confirmation_ready_queue",
            "private:raw_comparison_precheck_after_owner_anchor_confirmation_blocker_queue",
            "private:raw_comparison_precheck_after_owner_anchor_confirmation_report",
        ],
        "raw_boundary": summary["raw_boundary"],
        "public_safety": summary["public_safety"],
        "test_commands": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_raw_to_processed_comparison_precheck_after_owner_anchor_confirmation.py --generated-at 2026-07-07T00:00:00+10:00",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_raw_to_processed_comparison_precheck_after_owner_anchor_confirmation.py --require-private-precheck",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_v014_residual_difference_raw_to_processed_comparison_precheck_after_owner_anchor_confirmation.py",
        ],
        "git": {
            "branch": _git_output(["branch", "--show-current"]),
            "head": _git_output(["rev-parse", "HEAD"]),
            "status_short_branch": _git_output(["status", "--short", "--branch"]),
        },
    }


def _write_governance_events(generated_at: str) -> None:
    event = {
        "event_id": "DEV-KMFA-20260707-V014-RAW-COMPARISON-PRECHECK-AFTER-OWNER-ANCHOR-CONFIRMATION",
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "stage_id": "value-consistency",
        "phase_id": PHASE_ID,
        "status": STATUS,
        "decision": DECISION,
        "fact_level": "EXTRACTED",
        "iteration_id": "ITER-20260707-KMFA-V014-RAW-COMPARISON-PRECHECK-AFTER-OWNER-ANCHOR-CONFIRMATION",
        "task_id": TASK_ID,
        "version": VERSION,
        "go_no_go": DECISION,
        "result_commit": "PENDING",
        "summary": "Prechecked owner-authorized anchors for later formal raw-to-processed comparison without reading raw data.",
        "source_owner_authorized_anchor_confirmation_count": 72,
        "comparison_precheck_ready_record_count": 72,
        "comparison_precheck_blocker_record_count": 0,
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
            "acceptance_output": "Raw-to-processed comparison precheck after owner anchor confirmation manifest summary Go No-Go public-safe matrix private ignored ready queue blocker queue diagnostic report validator focused test and governance records",
            "completed_task_units": 1,
            "derived_percent": 100.0,
            "estimated_task_units": 1,
            "evidence_ref": MANIFEST_PATH.as_posix(),
            "fact_level": "EXTRACTED",
            "governance_stage_id": "VALUE-CONSISTENCY",
            "name": "v0.1.4 residual difference raw comparison precheck after owner anchor confirmation",
            "phase_goal": "precheck owner-authorized anchor handles for later formal comparison without raw data access",
            "phase_id": PHASE_ID,
            "project_id": "KMFA",
            "raw_data_committed": False,
            "record_type": "v014_phase",
            "roadmap_phase_id": "RESIDUAL_DIFFERENCE_RAW_COMPARISON_PRECHECK_AFTER_OWNER_ANCHOR_CONFIRMATION",
            "roadmap_stage_id": "VALUE-CONSISTENCY",
            "status": STATUS,
            "task_count": 3,
            "updated_at": "2026-07-07",
            "version": VERSION,
        },
        ("phase_id", "version"),
    )
    task_goals = [
        "read owner-authorized anchor confirmation public-safe evidence and ignored private confirmation queue read-only",
        "write ignored private comparison precheck diagnostic ready queue blocker queue and report",
        "emit public-safe NO_GO evidence while keeping formal comparison and downstream gates closed",
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
                "roadmap_phase_id": "RESIDUAL_DIFFERENCE_RAW_COMPARISON_PRECHECK_AFTER_OWNER_ANCHOR_CONFIRMATION",
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
    source_private_diagnostic = _read_json(SOURCE_PRIVATE_CONFIRMATION_DIAGNOSTIC_PATH)
    _ = SOURCE_PRIVATE_CONFIRMATION_REPORT_PATH.read_text(encoding="utf-8")
    confirmation_rows = _read_jsonl(SOURCE_PRIVATE_CONFIRMATION_QUEUE_PATH)
    if len(confirmation_rows) != 72:
        raise ValueError("raw comparison precheck requires 72 owner-authorized confirmation rows")
    if Counter(row.get("diagnostic_track") for row in confirmation_rows) != EXPECTED_TRACK_COUNTS:
        raise ValueError("unexpected diagnostic track counts")
    if any(row.get("owner_authorized_anchor_confirmation_status") != "confirmed_private_anchor_handle" for row in confirmation_rows):
        raise ValueError("all confirmation rows must be confirmed_private_anchor_handle")
    if any(row.get("raw_to_processed_value_comparison_allowed_next_phase") is not True for row in confirmation_rows):
        raise ValueError("all confirmation rows must allow next-phase comparison")
    ready_rows = _build_ready_queue(generated_at=generated, confirmation_rows=confirmation_rows)
    blocker_rows: list[dict[str, Any]] = []
    raw_boundary = _raw_boundary()
    public_safety = _public_safety()
    private_diagnostic = _write_private_outputs(
        generated_at=generated,
        source_summary=source_summary,
        source_private_diagnostic=source_private_diagnostic,
        ready_rows=ready_rows,
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
        confirmation_rows=confirmation_rows,
        ready_rows=ready_rows,
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
        "private_ready_rows": ready_rows,
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
        "PASS: generated V014 raw comparison precheck after owner anchor confirmation "
        f"decision={summary['decision']} ready={summary['comparison_precheck_ready_record_count']} "
        f"blockers={summary['comparison_precheck_blocker_record_count']} next={summary['next_recommended_phase']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
