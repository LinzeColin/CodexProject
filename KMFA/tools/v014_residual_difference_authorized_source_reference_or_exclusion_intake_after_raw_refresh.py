#!/usr/bin/env python3
"""Create authorized source-reference / exclusion intake after raw refresh.

This phase converts the 48 still-blocked raw-candidate fingerprint refresh
items into an ignored private intake queue for owner-authorized source
reference, owner exclusion, formula mapping, or non-numeric mapping. It does
not read raw inbox files, bind raw candidates, run raw-to-processed comparison,
close discrepancies, upload GitHub, reinstall the app, or execute business
steps. Public artifacts remain aggregate-only.
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
    v014_residual_difference_raw_candidate_fingerprint_evidence_refresh_after_final_threshold
    as source_refresh,
)


PROJECT_ROOT = Path("KMFA")
PHASE_ID = "V014_RESIDUAL_DIFFERENCE_AUTHORIZED_SOURCE_REFERENCE_OR_EXCLUSION_INTAKE_AFTER_RAW_REFRESH"
TASK_ID = "KMFA-V014-RESIDUAL-DIFFERENCE-AUTHORIZED-SOURCE-REFERENCE-OR-EXCLUSION-INTAKE-AFTER-RAW-REFRESH-20260708"
ACCEPTANCE_ID = "ACC-V014-RESIDUAL-DIFFERENCE-AUTHORIZED-SOURCE-REFERENCE-OR-EXCLUSION-INTAKE-AFTER-RAW-REFRESH"
VERSION = "0.1.4-residual-difference-authorized-source-reference-or-exclusion-intake-after-raw-refresh"
STATUS = "completed_validated_local_only_authorized_source_reference_or_exclusion_intake_after_raw_refresh_no_go"
DECISION = "NO_GO"
INTAKE_CONCLUSION = "private_resolution_intake_queue_prepared_but_no_authoritative_binding_applied"
NEXT_REQUIRED_INPUT = "apply_owner_authorized_source_reference_exclusion_or_formula_mapping_before_comparison_retry"
NEXT_RECOMMENDED_PHASE = (
    "V014_RESIDUAL_DIFFERENCE_AUTHORIZED_SOURCE_REFERENCE_OR_EXCLUSION_APPLICATION_READINESS_AFTER_RAW_REFRESH"
)

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = (
    MACHINE_DIR / "residual_difference_authorized_source_reference_or_exclusion_intake_after_raw_refresh_summary.json"
)
MANIFEST_PATH = (
    MACHINE_DIR / "residual_difference_authorized_source_reference_or_exclusion_intake_after_raw_refresh_manifest.json"
)
GO_NO_GO_PATH = (
    MACHINE_DIR
    / "residual_difference_authorized_source_reference_or_exclusion_intake_after_raw_refresh_go_no_go_report.json"
)
MATRIX_PATH = (
    MACHINE_DIR
    / "residual_difference_authorized_source_reference_or_exclusion_intake_after_raw_refresh_matrix_public_safe.json"
)
REPORT_PATH = HUMAN_DIR / "residual_difference_authorized_source_reference_or_exclusion_intake_after_raw_refresh.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_authorized_source_reference_or_exclusion_intake_after_raw_refresh_summary.json"
)
METADATA_MANIFEST_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_authorized_source_reference_or_exclusion_intake_after_raw_refresh_manifest.json"
)
METADATA_GO_NO_GO_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_authorized_source_reference_or_exclusion_intake_after_raw_refresh_go_no_go_report.json"
)
METADATA_MATRIX_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_authorized_source_reference_or_exclusion_intake_after_raw_refresh_matrix_public_safe.json"
)

SOURCE_REFRESH_SUMMARY_PATH = source_refresh.METADATA_SUMMARY_PATH
SOURCE_REFRESH_MANIFEST_PATH = source_refresh.METADATA_MANIFEST_PATH
SOURCE_REFRESH_GO_NO_GO_PATH = source_refresh.METADATA_GO_NO_GO_PATH
SOURCE_REFRESH_MATRIX_PATH = source_refresh.METADATA_MATRIX_PATH
SOURCE_PRIVATE_REFRESH_RECORDS_PATH = source_refresh.PRIVATE_REFRESH_RECORDS_PATH
SOURCE_PRIVATE_REFRESH_DIAGNOSTIC_PATH = source_refresh.PRIVATE_REFRESH_DIAGNOSTIC_PATH

PRIVATE_OUTPUT_DIR = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_residual_difference_authorized_source_reference_or_exclusion_intake_after_raw_refresh"
)
PRIVATE_ACTIVE_RECORD_PATH = PRIVATE_OUTPUT_DIR / "private_authorized_source_reference_or_exclusion_intake_active_record.json"
PRIVATE_INTAKE_QUEUE_PATH = PRIVATE_OUTPUT_DIR / "private_authorized_source_reference_or_exclusion_intake_queue.jsonl"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_authorized_source_reference_or_exclusion_intake_diagnostic.json"
PRIVATE_REPORT_PATH = PRIVATE_OUTPUT_DIR / "private_authorized_source_reference_or_exclusion_intake.md"

DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"
STAGE_STATUS_PATH = PROJECT_ROOT / "metadata/stage_status.jsonl"
TASK_STATUS_PATH = PROJECT_ROOT / "metadata/traceability/v1_4_stage_phase_task_status.jsonl"

SOURCE_REFERENCE_TRACK = "provide_authoritative_source_reference_or_owner_exclusion"
FORMULA_MAPPING_TRACK = "provide_formula_or_non_numeric_mapping"


def _raw_boundary() -> dict[str, bool]:
    return {
        "user_declared_raw_data_immutable": True,
        "raw_data_root_readonly_policy_active": True,
        "source_refresh_public_artifacts_read_by_this_phase": True,
        "source_private_refresh_records_read_by_this_phase": True,
        "private_active_record_written_by_this_phase": True,
        "private_intake_queue_written_by_this_phase": True,
        "private_diagnostic_written_by_this_phase": True,
        "source_private_refresh_records_mutated_by_this_phase": False,
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
        "private_source_refresh_records_committed": False,
        "private_active_record_committed": False,
        "private_intake_queue_committed": False,
        "private_diagnostic_committed": False,
        "private_report_committed": False,
        "private_slot_detail_committed": False,
        "source_reference_detail_committed": False,
        "owner_exclusion_detail_committed": False,
        "formula_mapping_detail_committed": False,
        "raw_file_committed": False,
        "raw_filename_committed": False,
        "raw_archive_member_name_committed": False,
        "raw_digest_committed": False,
        "field_header_plaintext_committed": False,
        "row_value_committed": False,
        "business_value_committed": False,
        "private_ref_or_fingerprint_committed": False,
        "credential_or_secret_committed": False,
    }


def _resolution_options(track: str | None) -> list[str]:
    if track == FORMULA_MAPPING_TRACK:
        return ["provide_formula_mapping", "owner_authorized_non_numeric_mapping"]
    return ["provide_authoritative_source_reference", "owner_authorized_exclusion"]


def _intake_track(track: str | None) -> str:
    if track == FORMULA_MAPPING_TRACK:
        return "formula_or_non_numeric_mapping"
    return "source_reference_or_owner_exclusion"


def _build_intake_queue(*, generated_at: str, source_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(source_rows, start=1):
        track = row.get("diagnostic_track")
        rows.append(
            {
                "intake_item_id": f"ASR-OE-RAW-REFRESH-{index:03d}",
                "phase_id": PHASE_ID,
                "task_id": TASK_ID,
                "generated_at": generated_at,
                "source_refresh_item_id": row.get("refresh_item_id"),
                PRIVATE_SLOT_KEY: row.get(PRIVATE_SLOT_KEY),
                "source_diagnostic_track": track,
                "source_raw_refresh_status": row.get("raw_refresh_status"),
                "intake_track": _intake_track(track if isinstance(track, str) else None),
                "allowed_private_resolution_codes": _resolution_options(track if isinstance(track, str) else None),
                "owner_authorization_recorded_for_private_intake": True,
                "authoritative_source_reference_applied_by_this_phase": False,
                "owner_exclusion_applied_by_this_phase": False,
                "formula_mapping_applied_by_this_phase": False,
                "authoritative_binding_applied_by_this_phase": False,
                "binding_ready_after_intake": False,
                "comparison_retry_ready_after_intake": False,
                "raw_to_processed_value_comparison_performed_by_this_phase": False,
                "public_commit_allowed": False,
            }
        )
    return rows


def _build_active_record(*, generated_at: str, source_summary: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(row["intake_track"] for row in rows)
    return {
        "schema_version": "kmfa.private.v014_authorized_source_reference_or_exclusion_intake_after_raw_refresh.v1",
        "classification": "private_authorized_source_reference_or_exclusion_intake_do_not_commit",
        "record_type": "v014_authorized_source_reference_or_exclusion_intake_active_record",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "source_phase_id": source_summary.get("phase_id"),
        "intake_item_count": len(rows),
        "track_counts": dict(counts),
        "owner_authorization_recorded_for_private_intake": True,
        "authoritative_binding_applied_by_this_phase": False,
        "comparison_retry_ready_after_intake": False,
    }


def _build_summary(
    *,
    generated_at: str,
    source_summary: dict[str, Any],
    source_manifest: dict[str, Any],
    source_go_no_go: dict[str, Any],
    source_matrix: dict[str, Any],
    source_records: list[dict[str, Any]],
    active_record: dict[str, Any],
    intake_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    intake_counts = Counter(row["intake_track"] for row in intake_rows)
    source_track_counts = Counter(row.get("diagnostic_track") for row in source_records)
    return {
        "schema_version": "kmfa.v014_authorized_source_reference_or_exclusion_intake_after_raw_refresh_summary.v1",
        "record_type": "v014_authorized_source_reference_or_exclusion_intake_after_raw_refresh_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": generated_at,
        "status": STATUS,
        "decision": DECISION,
        "intake_conclusion": INTAKE_CONCLUSION,
        "source_phase_id": source_summary.get("phase_id"),
        "source_manifest_phase_id": source_manifest.get("phase_id"),
        "source_go_no_go_decision": source_go_no_go.get("decision"),
        "source_matrix_check_fail_count": source_matrix.get("check_fail_count"),
        "source_refresh_item_count": source_summary.get("refresh_item_count"),
        "source_still_blocked_after_raw_refresh_count": source_summary.get("still_blocked_after_raw_refresh_count"),
        "source_deterministic_match_count": source_summary.get("deterministic_raw_candidate_fingerprint_match_count"),
        "source_comparison_retry_ready_count": source_summary.get("comparison_retry_ready_after_raw_refresh_count"),
        "source_private_refresh_record_count": len(source_records),
        "intake_item_count": len(intake_rows),
        "private_active_record_item_count": active_record.get("intake_item_count"),
        "source_reference_or_owner_exclusion_intake_count": intake_counts["source_reference_or_owner_exclusion"],
        "formula_or_non_numeric_mapping_intake_count": intake_counts["formula_or_non_numeric_mapping"],
        "source_reference_or_owner_exclusion_source_track_count": source_track_counts[SOURCE_REFERENCE_TRACK],
        "formula_or_non_numeric_mapping_source_track_count": source_track_counts[FORMULA_MAPPING_TRACK],
        "active_authoritative_decision_count": 0,
        "active_authoritative_source_reference_count": 0,
        "active_owner_exclusion_count": 0,
        "active_formula_mapping_count": 0,
        "binding_ready_after_intake_count": 0,
        "comparison_retry_ready_after_intake_count": 0,
        "unresolved_difference_count": source_summary.get("unresolved_difference_count"),
        "private_active_record_written": True,
        "private_intake_queue_written": True,
        "private_diagnostic_written": True,
        "private_report_written": True,
        "private_active_record_gitignored": _git_check_ignored(PRIVATE_ACTIVE_RECORD_PATH),
        "private_intake_queue_gitignored": _git_check_ignored(PRIVATE_INTAKE_QUEUE_PATH),
        "private_diagnostic_gitignored": _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH),
        "private_report_gitignored": _git_check_ignored(PRIVATE_REPORT_PATH),
        "source_private_refresh_records_gitignored": _git_check_ignored(SOURCE_PRIVATE_REFRESH_RECORDS_PATH),
        "authoritative_source_reference_applied_by_this_phase": False,
        "owner_exclusion_applied_by_this_phase": False,
        "formula_mapping_applied_by_this_phase": False,
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
        "raw_boundary": _raw_boundary(),
        "public_safety": _public_safety(),
    }


def _build_matrix(summary: dict[str, Any]) -> dict[str, Any]:
    checks = [
        ("source_refresh_phase_loaded", str(summary["source_phase_id"]).endswith("EVIDENCE_REFRESH_AFTER_FINAL_THRESHOLD")),
        ("source_go_no_go_locked", summary["source_go_no_go_decision"] == "NO_GO"),
        ("source_matrix_clean", summary["source_matrix_check_fail_count"] == 0),
        ("source_refresh_items_locked", summary["source_refresh_item_count"] == 48),
        ("source_still_blocked_locked", summary["source_still_blocked_after_raw_refresh_count"] == 48),
        ("intake_queue_complete", summary["intake_item_count"] == 48),
        ("source_reference_or_exclusion_count_locked", summary["source_reference_or_owner_exclusion_intake_count"] == 40),
        ("formula_mapping_count_locked", summary["formula_or_non_numeric_mapping_intake_count"] == 8),
        ("no_authoritative_decisions_applied", summary["active_authoritative_decision_count"] == 0),
        ("no_binding_ready_claimed", summary["binding_ready_after_intake_count"] == 0),
        ("private_intake_queue_ignored", summary["private_intake_queue_gitignored"] is True),
        ("source_private_records_ignored", summary["source_private_refresh_records_gitignored"] is True),
        ("raw_inbox_untouched", summary["raw_boundary"]["raw_inbox_mutated_by_this_phase"] is False),
        ("no_value_comparison_claimed", summary["raw_to_processed_value_comparison_performed_by_this_phase"] is False),
        ("downstream_gates_closed", summary["github_upload_performed"] is False and summary["business_execution_performed"] is False),
    ]
    rows = [{"check_code": code, "status": "PASS" if passed else "FAIL"} for code, passed in checks]
    pass_count = sum(1 for row in rows if row["status"] == "PASS")
    return {
        "schema_version": "kmfa.v014_authorized_source_reference_or_exclusion_intake_after_raw_refresh_matrix_public_safe.v1",
        "record_type": "v014_authorized_source_reference_or_exclusion_intake_after_raw_refresh_matrix_public_safe",
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
        "schema_version": "kmfa.v014_authorized_source_reference_or_exclusion_intake_after_raw_refresh_go_no_go.v1",
        "record_type": "v014_authorized_source_reference_or_exclusion_intake_after_raw_refresh_go_no_go",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": summary["generated_at"],
        "status": STATUS,
        "decision": DECISION,
        "intake_conclusion": INTAKE_CONCLUSION,
        "intake_item_count": summary["intake_item_count"],
        "source_reference_or_owner_exclusion_intake_count": summary["source_reference_or_owner_exclusion_intake_count"],
        "formula_or_non_numeric_mapping_intake_count": summary["formula_or_non_numeric_mapping_intake_count"],
        "active_authoritative_decision_count": 0,
        "binding_ready_after_intake_count": 0,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "full_raw_to_processed_value_comparison_complete": False,
        "business_value_consistency_verified": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "business_execution_allowed": False,
        "next_required_input": NEXT_REQUIRED_INPUT,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
    }


def _write_private_outputs(
    *,
    generated_at: str,
    source_summary: dict[str, Any],
    active_record: dict[str, Any],
    intake_rows: list[dict[str, Any]],
    summary: dict[str, Any],
) -> dict[str, Any]:
    diagnostic = {
        "schema_version": "kmfa.private.v014_authorized_source_reference_or_exclusion_intake_after_raw_refresh.v1",
        "classification": "private_authorized_source_reference_or_exclusion_intake_do_not_commit",
        "record_type": "v014_authorized_source_reference_or_exclusion_intake_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "source_phase_id": source_summary.get("phase_id"),
        "intake_conclusion": INTAKE_CONCLUSION,
        "intake_item_count": len(intake_rows),
        "counts": {
            "source_reference_or_owner_exclusion_intake_count": summary[
                "source_reference_or_owner_exclusion_intake_count"
            ],
            "formula_or_non_numeric_mapping_intake_count": summary["formula_or_non_numeric_mapping_intake_count"],
            "binding_ready_after_intake_count": summary["binding_ready_after_intake_count"],
            "comparison_retry_ready_after_intake_count": summary["comparison_retry_ready_after_intake_count"],
        },
        "raw_boundary": summary["raw_boundary"],
    }
    _write_json(PRIVATE_ACTIVE_RECORD_PATH, active_record)
    _write_jsonl(PRIVATE_INTAKE_QUEUE_PATH, intake_rows)
    _write_json(PRIVATE_DIAGNOSTIC_PATH, diagnostic)
    _write_text(
        PRIVATE_REPORT_PATH,
        "\n".join(
            [
                "# Private Authorized Source Reference Or Exclusion Intake After Raw Refresh",
                "",
                f"- phase_id: `{PHASE_ID}`",
                f"- intake_item_count: `{len(intake_rows)}`",
                "- authoritative_binding_applied_by_this_phase: `false`",
                "- raw_to_processed_value_comparison_performed_by_this_phase: `false`",
                "",
            ]
        ),
    )
    return diagnostic


def _write_human(summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any]) -> None:
    report = f"""# V014 Authorized Source Reference Or Exclusion Intake After Raw Refresh

Generated at: {summary["generated_at"]}

## Scope

- Phase: `{PHASE_ID}`
- Decision: `{DECISION}`
- Status: `{STATUS}`
- Source: prior public-safe raw refresh evidence plus ignored private refresh records.
- Raw boundary: this phase does not read, list, stat, parse, fingerprint, write, delete, move, rename, copy, normalize or mutate the raw inbox.

## Public-Safe Result

- Source refresh items: `{summary["source_refresh_item_count"]}`
- Still blocked after raw refresh: `{summary["source_still_blocked_after_raw_refresh_count"]}`
- Intake items: `{summary["intake_item_count"]}`
- Source reference or owner exclusion intake items: `{summary["source_reference_or_owner_exclusion_intake_count"]}`
- Formula or non-numeric mapping intake items: `{summary["formula_or_non_numeric_mapping_intake_count"]}`
- Active authoritative decisions applied: `{summary["active_authoritative_decision_count"]}`
- Binding ready after intake: `{summary["binding_ready_after_intake_count"]}`

## Gate

This phase prepares a private intake queue only. It does not apply authoritative source references, owner exclusions, formula mappings, raw candidate fingerprints, raw-to-processed comparison, reconciliation, formal reports, GitHub upload, app reinstall or business execution.

Next required input: `{NEXT_REQUIRED_INPUT}`.
"""
    go_record = f"""# Go / No-Go Record

- Phase: `{PHASE_ID}`
- Decision: `{go_no_go["decision"]}`
- Reason: private intake queue was prepared but no authoritative binding was applied.
- Matrix: `{matrix["check_pass_count"]}` pass / `{matrix["check_fail_count"]}` fail
- GitHub upload: not allowed in this phase.
- App reinstall: not allowed in this phase.
"""
    test_results = f"""# Test Results

- RED: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_v014_residual_difference_authorized_source_reference_or_exclusion_intake_after_raw_refresh.py` failed before implementation because the generator module did not exist.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_intake_after_raw_refresh.py --generated-at 2026-07-08T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_intake_after_raw_refresh.py --require-private-intake`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_v014_residual_difference_authorized_source_reference_or_exclusion_intake_after_raw_refresh.py`
- Governance validators, CSV shape checks, diff check, raw/private scan, secret scan and private-runtime tracked-file scan: expected before commit.

Expected matrix result: {matrix["check_pass_count"]}/{matrix["check_count"]} PASS.
"""
    risk_register = """# Risk Register

- Risk: intake queue is mistaken for authoritative source binding.
- Control: all binding, comparison and downstream gate flags remain false.
- Risk: private slot or resolution details leak into public artifacts.
- Control: public artifacts contain aggregate counts only; private details stay ignored.
- Risk: raw inbox is modified.
- Control: this phase does not access raw inbox and preserves raw immutability.
"""
    rollback = f"""# Rollback Plan

Remove artifacts for `{PHASE_ID}`, metadata copies, ignored private intake outputs, tool, validator, focused test and governance rows. Do not touch raw inbox files or prior private/source artifacts.
"""
    _write_text(REPORT_PATH, report)
    _write_text(GO_NO_GO_RECORD_PATH, go_record)
    _write_text(TEST_RESULTS_PATH, test_results)
    _write_text(RISK_REGISTER_PATH, risk_register)
    _write_text(ROLLBACK_PATH, rollback)


def _build_manifest(summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v014_authorized_source_reference_or_exclusion_intake_after_raw_refresh_manifest.v1",
        "record_type": "v014_authorized_source_reference_or_exclusion_intake_after_raw_refresh_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": summary["generated_at"],
        "status": STATUS,
        "decision": DECISION,
        "intake_conclusion": INTAKE_CONCLUSION,
        "summary": summary,
        "matrix": matrix,
        "go_no_go_report": go_no_go,
        "source_artifacts": {
            "raw_refresh_summary": "public_safe_metadata_copy",
            "raw_refresh_manifest": "public_safe_metadata_copy",
            "raw_refresh_go_no_go": "public_safe_metadata_copy",
            "raw_refresh_matrix": "public_safe_metadata_copy",
            "raw_refresh_private_records": "ignored_private_runtime",
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
            "private:authorized_source_reference_or_exclusion_intake_active_record",
            "private:authorized_source_reference_or_exclusion_intake_queue",
            "private:authorized_source_reference_or_exclusion_intake_diagnostic",
            "private:authorized_source_reference_or_exclusion_intake_report",
        ],
        "raw_boundary": summary["raw_boundary"],
        "public_safety": summary["public_safety"],
        "test_commands": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_intake_after_raw_refresh.py --generated-at 2026-07-08T00:00:00+10:00",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_intake_after_raw_refresh.py --require-private-intake",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_v014_residual_difference_authorized_source_reference_or_exclusion_intake_after_raw_refresh.py",
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
        "event_id": "DEV-KMFA-20260708-V014-AUTHORIZED-SOURCE-REFERENCE-OR-EXCLUSION-INTAKE-AFTER-RAW-REFRESH",
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
        "summary": "Prepared ignored private intake queue for 48 raw-refresh blockers without applying authoritative binding.",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "files_changed": _changed_kmfa_files(),
        "test_commands": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_intake_after_raw_refresh.py --generated-at 2026-07-08T00:00:00+10:00",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_intake_after_raw_refresh.py --require-private-intake",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_v014_residual_difference_authorized_source_reference_or_exclusion_intake_after_raw_refresh.py",
        ],
        "test_results": ["PENDING: final validation results will be recorded before local commit."],
        "next_required_input": NEXT_REQUIRED_INPUT,
        "intake_item_count": summary["intake_item_count"],
        "source_reference_or_owner_exclusion_intake_count": summary[
            "source_reference_or_owner_exclusion_intake_count"
        ],
        "formula_or_non_numeric_mapping_intake_count": summary["formula_or_non_numeric_mapping_intake_count"],
        "binding_ready_after_intake_count": summary["binding_ready_after_intake_count"],
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
        "roadmap_phase_id": "RESIDUAL_DIFFERENCE_AUTHORIZED_SOURCE_REFERENCE_OR_EXCLUSION_INTAKE_AFTER_RAW_REFRESH",
        "roadmap_stage_id": "VALUE-CONSISTENCY",
        "governance_stage_id": "VALUE-CONSISTENCY",
        "name": "v0.1.4 residual difference authorized source reference or exclusion intake after raw refresh",
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
        ("T1", "read raw-refresh public evidence and ignored private refresh records"),
        ("T2", "write ignored private intake queue for 48 remaining blockers"),
        ("T3", "emit public-safe NO_GO evidence while keeping comparison and upload gates closed"),
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
                "roadmap_phase_id": "RESIDUAL_DIFFERENCE_AUTHORIZED_SOURCE_REFERENCE_OR_EXCLUSION_INTAKE_AFTER_RAW_REFRESH",
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
    source_summary = _read_json(SOURCE_REFRESH_SUMMARY_PATH)
    source_manifest = _read_json(SOURCE_REFRESH_MANIFEST_PATH)
    source_go_no_go = _read_json(SOURCE_REFRESH_GO_NO_GO_PATH)
    source_matrix = _read_json(SOURCE_REFRESH_MATRIX_PATH)
    source_records = _read_jsonl(SOURCE_PRIVATE_REFRESH_RECORDS_PATH)
    if source_summary.get("still_blocked_after_raw_refresh_count") != 48:
        raise ValueError("source still-blocked-after-raw-refresh count must be 48")
    if source_summary.get("deterministic_raw_candidate_fingerprint_match_count") != 0:
        raise ValueError("source deterministic match count must be 0")
    if len(source_records) != 48:
        raise ValueError("source private refresh records must be 48")

    intake_rows = _build_intake_queue(generated_at=generated, source_rows=source_records)
    active_record = _build_active_record(generated_at=generated, source_summary=source_summary, rows=intake_rows)
    summary = _build_summary(
        generated_at=generated,
        source_summary=source_summary,
        source_manifest=source_manifest,
        source_go_no_go=source_go_no_go,
        source_matrix=source_matrix,
        source_records=source_records,
        active_record=active_record,
        intake_rows=intake_rows,
    )
    private_diagnostic = _write_private_outputs(
        generated_at=generated,
        source_summary=source_summary,
        active_record=active_record,
        intake_rows=intake_rows,
        summary=summary,
    )
    summary["private_active_record_gitignored"] = _git_check_ignored(PRIVATE_ACTIVE_RECORD_PATH)
    summary["private_intake_queue_gitignored"] = _git_check_ignored(PRIVATE_INTAKE_QUEUE_PATH)
    summary["private_diagnostic_gitignored"] = _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH)
    summary["private_report_gitignored"] = _git_check_ignored(PRIVATE_REPORT_PATH)
    summary["source_private_refresh_records_gitignored"] = _git_check_ignored(SOURCE_PRIVATE_REFRESH_RECORDS_PATH)
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
        "private_active_record": active_record,
        "private_intake_rows": intake_rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated-at")
    parser.add_argument("--no-governance-event", action="store_true")
    args = parser.parse_args()
    result = generate(generated_at=args.generated_at, write_governance_event=not args.no_governance_event)
    summary = result["summary"]
    print(
        "PASS: generated V014 authorized source reference or exclusion intake after raw refresh "
        f"decision={summary['decision']} intake_items={summary['intake_item_count']} "
        f"source_reference_or_exclusion={summary['source_reference_or_owner_exclusion_intake_count']} "
        f"formula_or_mapping={summary['formula_or_non_numeric_mapping_intake_count']} "
        f"binding_ready={summary['binding_ready_after_intake_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
