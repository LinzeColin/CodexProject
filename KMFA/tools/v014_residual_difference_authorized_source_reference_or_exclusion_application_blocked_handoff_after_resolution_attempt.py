#!/usr/bin/env python3
"""Prepare a safe blocked handoff after authorized-resolution attempt.

This phase converts the previous NO_GO resolution-attempt evidence into a
public-safe owner-action handoff. It does not read the raw inbox and does not
claim binding, raw-to-processed comparison, reconciliation, upload, reinstall or
business execution readiness.
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
    v014_residual_difference_authorized_source_reference_or_exclusion_application_resolution_attempt_after_final_threshold
    as source_resolution,
)


PROJECT_ROOT = Path("KMFA")
PHASE_ID = (
    "V014_RESIDUAL_DIFFERENCE_AUTHORIZED_SOURCE_REFERENCE_OR_EXCLUSION_"
    "APPLICATION_BLOCKED_HANDOFF_AFTER_RESOLUTION_ATTEMPT"
)
TASK_ID = (
    "KMFA-V014-RESIDUAL-DIFFERENCE-AUTHORIZED-SOURCE-REFERENCE-OR-EXCLUSION-"
    "APPLICATION-BLOCKED-HANDOFF-AFTER-RESOLUTION-ATTEMPT-20260708"
)
ACCEPTANCE_ID = (
    "ACC-V014-RESIDUAL-DIFFERENCE-AUTHORIZED-SOURCE-REFERENCE-OR-EXCLUSION-"
    "APPLICATION-BLOCKED-HANDOFF-AFTER-RESOLUTION-ATTEMPT"
)
VERSION = (
    "0.1.4-residual-difference-authorized-source-reference-or-exclusion-"
    "application-blocked-handoff-after-resolution-attempt"
)
STATUS = (
    "completed_validated_local_only_authorized_source_reference_or_exclusion_"
    "application_blocked_handoff_after_resolution_attempt_no_go"
)
DECISION = "NO_GO"
HANDOFF_CONCLUSION = "blocked_until_authorized_resolution_application_available"
NEXT_REQUIRED_INPUT = source_resolution.NEXT_REQUIRED_INPUT
NEXT_RECOMMENDED_PHASE = source_resolution.NEXT_RECOMMENDED_PHASE

PRIVATE_SLOT_KEY = source_resolution.PRIVATE_SLOT_KEY
SOURCE_REFERENCE_INTAKE_TRACK = source_resolution.SOURCE_REFERENCE_INTAKE_TRACK
FORMULA_MAPPING_INTAKE_TRACK = source_resolution.FORMULA_MAPPING_INTAKE_TRACK
EXPECTED_HANDOFF_TRACK_COUNTS = source_resolution.EXPECTED_RESOLUTION_TRACK_COUNTS

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = (
    MACHINE_DIR
    / "residual_difference_authorized_source_reference_or_exclusion_application_blocked_handoff_after_resolution_attempt_summary.json"
)
MANIFEST_PATH = (
    MACHINE_DIR
    / "residual_difference_authorized_source_reference_or_exclusion_application_blocked_handoff_after_resolution_attempt_manifest.json"
)
GO_NO_GO_PATH = (
    MACHINE_DIR
    / "residual_difference_authorized_source_reference_or_exclusion_application_blocked_handoff_after_resolution_attempt_go_no_go_report.json"
)
MATRIX_PATH = (
    MACHINE_DIR
    / "residual_difference_authorized_source_reference_or_exclusion_application_blocked_handoff_after_resolution_attempt_matrix_public_safe.json"
)
REPORT_PATH = (
    HUMAN_DIR
    / "residual_difference_authorized_source_reference_or_exclusion_application_blocked_handoff_after_resolution_attempt.md"
)
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_authorized_source_reference_or_exclusion_application_blocked_handoff_after_resolution_attempt_summary.json"
)
METADATA_MANIFEST_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_authorized_source_reference_or_exclusion_application_blocked_handoff_after_resolution_attempt_manifest.json"
)
METADATA_GO_NO_GO_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_authorized_source_reference_or_exclusion_application_blocked_handoff_after_resolution_attempt_go_no_go_report.json"
)
METADATA_MATRIX_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_authorized_source_reference_or_exclusion_application_blocked_handoff_after_resolution_attempt_matrix_public_safe.json"
)

SOURCE_RESOLUTION_ATTEMPT_SUMMARY_PATH = source_resolution.METADATA_SUMMARY_PATH
SOURCE_RESOLUTION_ATTEMPT_MANIFEST_PATH = source_resolution.METADATA_MANIFEST_PATH
SOURCE_RESOLUTION_ATTEMPT_GO_NO_GO_PATH = source_resolution.METADATA_GO_NO_GO_PATH
SOURCE_RESOLUTION_ATTEMPT_MATRIX_PATH = source_resolution.METADATA_MATRIX_PATH
SOURCE_PRIVATE_RESOLUTION_DIAGNOSTIC_PATH = source_resolution.PRIVATE_RESOLUTION_DIAGNOSTIC_PATH
SOURCE_PRIVATE_RESOLUTION_RECORDS_PATH = source_resolution.PRIVATE_RESOLUTION_RECORDS_PATH
SOURCE_PRIVATE_RESOLUTION_REPORT_PATH = source_resolution.PRIVATE_RESOLUTION_REPORT_PATH

PRIVATE_OUTPUT_DIR = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_residual_difference_authorized_source_reference_or_exclusion_application_blocked_handoff_after_resolution_attempt"
)
PRIVATE_BLOCKED_HANDOFF_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_blocked_handoff_diagnostic.json"
PRIVATE_BLOCKED_HANDOFF_RECORDS_PATH = PRIVATE_OUTPUT_DIR / "private_blocked_handoff_records.jsonl"
PRIVATE_BLOCKED_HANDOFF_PACKET_PATH = PRIVATE_OUTPUT_DIR / "private_blocked_handoff_packet.md"

DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"
STAGE_STATUS_PATH = PROJECT_ROOT / "metadata/stage_status.jsonl"
TASK_STATUS_PATH = PROJECT_ROOT / "metadata/traceability/v1_4_stage_phase_task_status.jsonl"


def _raw_boundary() -> dict[str, bool]:
    return {
        "user_declared_raw_data_immutable": True,
        "raw_data_root_readonly_policy_active": True,
        "source_resolution_attempt_public_artifacts_read_by_this_phase": True,
        "source_resolution_attempt_manifest_read_by_this_phase": True,
        "source_resolution_attempt_go_no_go_read_by_this_phase": True,
        "source_resolution_attempt_matrix_read_by_this_phase": True,
        "source_private_resolution_diagnostic_read_by_this_phase": True,
        "source_private_resolution_records_read_by_this_phase": True,
        "source_private_resolution_report_read_by_this_phase": True,
        "private_blocked_handoff_diagnostic_written_by_this_phase": True,
        "private_blocked_handoff_records_written_by_this_phase": True,
        "private_blocked_handoff_packet_written_by_this_phase": True,
        "source_private_resolution_diagnostic_mutated_by_this_phase": False,
        "source_private_resolution_records_mutated_by_this_phase": False,
        "source_private_resolution_report_mutated_by_this_phase": False,
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
        "source_private_resolution_diagnostic_committed": False,
        "source_private_resolution_records_committed": False,
        "source_private_resolution_report_committed": False,
        "private_blocked_handoff_diagnostic_committed": False,
        "private_blocked_handoff_records_committed": False,
        "private_blocked_handoff_packet_committed": False,
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


def _required_input_type(track: str | None) -> str:
    if track == SOURCE_REFERENCE_INTAKE_TRACK:
        return "source_reference_or_owner_exclusion"
    if track == FORMULA_MAPPING_INTAKE_TRACK:
        return "formula_or_non_numeric_mapping"
    return "authorized_resolution_application"


def _build_handoff_records(*, generated_at: str, source_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, row in enumerate(source_rows, start=1):
        records.append(
            {
                "blocked_handoff_item_id": f"ASR-OE-APP-BLOCKED-HANDOFF-RA-{index:03d}",
                "phase_id": PHASE_ID,
                "task_id": TASK_ID,
                "generated_at": generated_at,
                "source_resolution_attempt_item_id": row.get("resolution_attempt_item_id"),
                PRIVATE_SLOT_KEY: row.get(PRIVATE_SLOT_KEY),
                "intake_track": row.get("intake_track"),
                "source_resolution_attempt_status": row.get("resolution_attempt_status"),
                "source_application_blocker_code": row.get("application_blocker_code"),
                "required_authorized_input_type": _required_input_type(row.get("intake_track")),
                "handoff_action_status": "blocked_waiting_for_authorized_resolution_application",
                "owner_action_required": True,
                "owner_or_authorized_delegate_required": True,
                "auto_resolution_allowed": False,
                "binding_ready_after_blocked_handoff": False,
                "comparison_retry_ready_after_blocked_handoff": False,
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
    status_counts = Counter(row.get("handoff_action_status") for row in records)
    diagnostic = {
        "schema_version": "kmfa.private.v014_authorized_resolution_blocked_handoff_after_resolution_attempt.v1",
        "classification": "private_authorized_resolution_blocked_handoff_after_resolution_attempt_do_not_commit",
        "record_type": "v014_authorized_resolution_blocked_handoff_after_resolution_attempt_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "source_phase_id": source_summary.get("phase_id"),
        "handoff_conclusion": HANDOFF_CONCLUSION,
        "blocked_handoff_item_count": len(records),
        "owner_action_item_count": len(records),
        "track_counts": dict(track_counts),
        "status_counts": dict(status_counts),
        "binding_ready_after_blocked_handoff_count": 0,
        "comparison_retry_ready_after_blocked_handoff_count": 0,
        "raw_boundary": raw_boundary,
    }
    _write_json(PRIVATE_BLOCKED_HANDOFF_DIAGNOSTIC_PATH, diagnostic)
    _write_jsonl(PRIVATE_BLOCKED_HANDOFF_RECORDS_PATH, records)
    _write_text(
        PRIVATE_BLOCKED_HANDOFF_PACKET_PATH,
        "\n".join(
            [
                "# Private Authorized Resolution Blocked Handoff Packet",
                "",
                f"- phase_id: `{PHASE_ID}`",
                f"- blocked_handoff_item_count: `{len(records)}`",
                f"- owner_action_item_count: `{len(records)}`",
                "- binding_ready_after_blocked_handoff_count: `0`",
                "- comparison_retry_ready_after_blocked_handoff_count: `0`",
                "- raw_to_processed_value_comparison_performed_by_this_phase: `false`",
                "",
                "This packet may contain private handles and must remain ignored.",
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
    handoff_records: list[dict[str, Any]],
    raw_boundary: dict[str, bool],
    public_safety: dict[str, bool],
) -> dict[str, Any]:
    track_counts = Counter(row.get("intake_track") for row in handoff_records)
    return {
        "schema_version": "kmfa.v014_authorized_resolution_blocked_handoff_after_resolution_attempt_summary.v1",
        "record_type": "v014_authorized_resolution_blocked_handoff_after_resolution_attempt_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": generated_at,
        "status": STATUS,
        "decision": DECISION,
        "handoff_conclusion": HANDOFF_CONCLUSION,
        "source_phase_id": source_summary.get("phase_id"),
        "source_manifest_phase_id": source_manifest.get("phase_id"),
        "source_go_no_go_decision": source_go_no_go.get("decision"),
        "source_matrix_check_fail_count": source_matrix.get("check_fail_count"),
        "source_private_diagnostic_phase_id": source_diagnostic.get("phase_id"),
        "source_private_resolution_record_count": len(source_rows),
        "source_resolution_attempt_item_count": source_summary.get("resolution_attempt_item_count"),
        "source_active_authoritative_resolution_application_count": source_summary.get(
            "active_authoritative_resolution_application_count"
        ),
        "source_auto_applied_authorized_resolution_count": source_summary.get(
            "auto_applied_authorized_resolution_count"
        ),
        "source_still_blocked_authorized_resolution_application_count": source_summary.get(
            "still_blocked_authorized_resolution_application_count"
        ),
        "blocked_handoff_prepared_by_this_phase": True,
        "blocked_handoff_item_count": len(handoff_records),
        "owner_action_item_count": len(handoff_records),
        "authorized_resolution_blockers_remain": True,
        "source_reference_or_owner_exclusion_handoff_item_count": track_counts[SOURCE_REFERENCE_INTAKE_TRACK],
        "formula_or_non_numeric_mapping_handoff_item_count": track_counts[FORMULA_MAPPING_INTAKE_TRACK],
        "binding_ready_after_blocked_handoff_count": 0,
        "comparison_retry_ready_after_blocked_handoff_count": 0,
        "unresolved_difference_count": source_summary.get("unresolved_difference_count"),
        "private_blocked_handoff_diagnostic_written": True,
        "private_blocked_handoff_records_written": True,
        "private_blocked_handoff_packet_written": True,
        "private_blocked_handoff_diagnostic_gitignored": _git_check_ignored(
            PRIVATE_BLOCKED_HANDOFF_DIAGNOSTIC_PATH
        ),
        "private_blocked_handoff_records_gitignored": _git_check_ignored(PRIVATE_BLOCKED_HANDOFF_RECORDS_PATH),
        "private_blocked_handoff_packet_gitignored": _git_check_ignored(PRIVATE_BLOCKED_HANDOFF_PACKET_PATH),
        "source_private_resolution_diagnostic_gitignored": _git_check_ignored(
            SOURCE_PRIVATE_RESOLUTION_DIAGNOSTIC_PATH
        ),
        "source_private_resolution_records_gitignored": _git_check_ignored(SOURCE_PRIVATE_RESOLUTION_RECORDS_PATH),
        "source_private_resolution_report_gitignored": _git_check_ignored(SOURCE_PRIVATE_RESOLUTION_REPORT_PATH),
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
            "source_resolution_attempt_loaded",
            str(summary["source_phase_id"]).endswith("APPLICATION_RESOLUTION_ATTEMPT_AFTER_FINAL_THRESHOLD"),
        ),
        ("source_go_no_go_preserved", summary["source_go_no_go_decision"] == "NO_GO"),
        ("source_matrix_clean", summary["source_matrix_check_fail_count"] == 0),
        ("source_resolution_attempt_items_locked", summary["source_resolution_attempt_item_count"] == 48),
        ("source_active_authoritative_resolution_zero_locked", summary["source_active_authoritative_resolution_application_count"] == 0),
        ("source_auto_application_zero_locked", summary["source_auto_applied_authorized_resolution_count"] == 0),
        ("source_still_blocked_locked", summary["source_still_blocked_authorized_resolution_application_count"] == 48),
        ("blocked_handoff_items_locked", summary["blocked_handoff_item_count"] == 48),
        ("owner_action_items_locked", summary["owner_action_item_count"] == 48),
        (
            "handoff_track_counts_locked",
            summary["source_reference_or_owner_exclusion_handoff_item_count"] == 40
            and summary["formula_or_non_numeric_mapping_handoff_item_count"] == 8,
        ),
        (
            "no_binding_or_retry_ready_after_handoff",
            summary["binding_ready_after_blocked_handoff_count"] == 0
            and summary["comparison_retry_ready_after_blocked_handoff_count"] == 0,
        ),
        ("private_blocked_handoff_outputs_ignored", summary["private_blocked_handoff_records_gitignored"] is True),
        ("raw_inbox_untouched", summary["raw_boundary"]["raw_inbox_mutated_by_this_phase"] is False),
        ("public_safe_aggregate_only", summary["public_safety"]["public_safe_aggregate_only"] is True),
        (
            "downstream_gates_closed",
            summary["github_upload_performed"] is False and summary["business_execution_performed"] is False,
        ),
    ]
    rows = [{"check_code": code, "status": "PASS" if passed else "FAIL"} for code, passed in checks]
    pass_count = sum(1 for row in rows if row["status"] == "PASS")
    return {
        "schema_version": "kmfa.v014_authorized_resolution_blocked_handoff_after_resolution_attempt_matrix_public_safe.v1",
        "record_type": "v014_authorized_resolution_blocked_handoff_after_resolution_attempt_matrix_public_safe",
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
        "schema_version": "kmfa.v014_authorized_resolution_blocked_handoff_after_resolution_attempt_go_no_go.v1",
        "record_type": "v014_authorized_resolution_blocked_handoff_after_resolution_attempt_go_no_go",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": summary["generated_at"],
        "status": STATUS,
        "decision": DECISION,
        "handoff_conclusion": HANDOFF_CONCLUSION,
        "blocked_handoff_item_count": summary["blocked_handoff_item_count"],
        "owner_action_item_count": summary["owner_action_item_count"],
        "authorized_resolution_blockers_remain": True,
        "binding_ready_after_blocked_handoff_count": 0,
        "comparison_retry_ready_after_blocked_handoff_count": 0,
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
    report = f"""# V014 Authorized Source Reference Or Exclusion Application Blocked Handoff After Resolution Attempt

Generated at: {summary["generated_at"]}

## Scope

- Phase: `{PHASE_ID}`
- Decision: `{DECISION}`
- Status: `{STATUS}`
- Source: prior public-safe resolution-attempt evidence and ignored private resolution records.
- Raw boundary: no raw inbox read, list, stat, parse, value extraction, write, delete, move, rename, copy, normalize or mutation.

## Public-Safe Handoff Result

- Source resolution attempts: `{summary["source_resolution_attempt_item_count"]}`
- Source active authoritative resolution applications: `{summary["source_active_authoritative_resolution_application_count"]}`
- Source automatically applied authorized resolutions: `{summary["source_auto_applied_authorized_resolution_count"]}`
- Source still blocked authorized resolution applications: `{summary["source_still_blocked_authorized_resolution_application_count"]}`
- Blocked handoff items: `{summary["blocked_handoff_item_count"]}`
- Owner action items: `{summary["owner_action_item_count"]}`
- Source reference or owner exclusion handoff items: `{summary["source_reference_or_owner_exclusion_handoff_item_count"]}`
- Formula or non-numeric mapping handoff items: `{summary["formula_or_non_numeric_mapping_handoff_item_count"]}`
- Binding ready after blocked handoff: `{summary["binding_ready_after_blocked_handoff_count"]}`
- Comparison retry ready after blocked handoff: `{summary["comparison_retry_ready_after_blocked_handoff_count"]}`
- Unresolved differences after this phase: `{summary["unresolved_difference_count"]}`

## Gate

The authorized-resolution application blocker remains open. This phase only prepares a safe handoff and does not bind fingerprints, compare raw and processed values, reconcile processed data, claim business consistency, upload to GitHub, reinstall the app, or execute business use.

Next required input: `{NEXT_REQUIRED_INPUT}`.
"""
    go_record = f"""# Go / No-Go Record

- Phase: `{PHASE_ID}`
- Decision: `{go_no_go["decision"]}`
- Reason: `{HANDOFF_CONCLUSION}`
- Matrix: `{matrix["check_pass_count"]}` pass / `{matrix["check_fail_count"]}` fail
- Next recommended phase: `{NEXT_RECOMMENDED_PHASE}`
- GitHub upload: not allowed in this phase.
- App reinstall: not allowed in this phase.
"""
    test_results = f"""# Test Results

- RED: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_authorized_source_reference_or_exclusion_application_blocked_handoff_after_resolution_attempt` failed before implementation because the generator module did not exist.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_blocked_handoff_after_resolution_attempt.py --generated-at 2026-07-08T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_blocked_handoff_after_resolution_attempt.py --require-private-handoff`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_authorized_source_reference_or_exclusion_application_blocked_handoff_after_resolution_attempt`
- Governance validators, CSV shape checks, diff check, raw/private marker scan, secret scan and private-runtime tracked-file scan: expected before commit.

Expected matrix result: {matrix["check_pass_count"]}/{matrix["check_count"]} PASS.
"""
    risk_register = """# Risk Register

- Risk: a blocked handoff is mistaken for discrepancy closure.
- Control: decision remains NO_GO and binding, comparison, reconciliation and business consistency flags remain false.
- Risk: private slot or owner-action details leak into public artifacts.
- Control: public artifacts contain aggregate counts only; private blocked-handoff outputs stay ignored.
- Risk: raw inbox is modified.
- Control: this phase consumes existing ignored private resolution-attempt artifacts only and does not touch the raw inbox.
"""
    rollback = f"""# Rollback Plan

Remove artifacts for `{PHASE_ID}`, metadata copies, private blocked-handoff outputs, tool, validator, focused test and governance rows. Do not touch source resolution-attempt evidence, prior private artifacts or raw inbox files.
"""
    _write_text(REPORT_PATH, report)
    _write_text(GO_NO_GO_RECORD_PATH, go_record)
    _write_text(TEST_RESULTS_PATH, test_results)
    _write_text(RISK_REGISTER_PATH, risk_register)
    _write_text(ROLLBACK_PATH, rollback)


def _build_manifest(summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v014_authorized_resolution_blocked_handoff_after_resolution_attempt_manifest.v1",
        "record_type": "v014_authorized_resolution_blocked_handoff_after_resolution_attempt_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": summary["generated_at"],
        "status": STATUS,
        "decision": DECISION,
        "handoff_conclusion": HANDOFF_CONCLUSION,
        "summary": summary,
        "matrix": matrix,
        "go_no_go_report": go_no_go,
        "source_artifacts": {
            "resolution_attempt_summary": "public_safe_metadata_copy",
            "resolution_attempt_manifest": "public_safe_metadata_copy",
            "resolution_attempt_go_no_go": "public_safe_metadata_copy",
            "resolution_attempt_matrix": "public_safe_metadata_copy",
            "resolution_attempt_private_diagnostic": "ignored_private_runtime",
            "resolution_attempt_private_records": "ignored_private_runtime",
            "resolution_attempt_private_report": "ignored_private_runtime",
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
            "private:authorized_resolution_blocked_handoff_diagnostic",
            "private:authorized_resolution_blocked_handoff_records",
            "private:authorized_resolution_blocked_handoff_packet",
        ],
        "raw_boundary": summary["raw_boundary"],
        "public_safety": summary["public_safety"],
        "test_commands": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_blocked_handoff_after_resolution_attempt.py --generated-at 2026-07-08T00:00:00+10:00",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_blocked_handoff_after_resolution_attempt.py --require-private-handoff",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_authorized_source_reference_or_exclusion_application_blocked_handoff_after_resolution_attempt",
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
            "APPLICATION-BLOCKED-HANDOFF-AFTER-RESOLUTION-ATTEMPT"
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
        "summary": "Prepared a public-safe blocked handoff for the 48 unresolved authorized-resolution application blockers; downstream gates remain closed.",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "files_changed": _changed_kmfa_files(),
        "test_commands": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_blocked_handoff_after_resolution_attempt.py --generated-at 2026-07-08T00:00:00+10:00",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_blocked_handoff_after_resolution_attempt.py --require-private-handoff",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_authorized_source_reference_or_exclusion_application_blocked_handoff_after_resolution_attempt",
        ],
        "test_results": ["PENDING: final validation results will be recorded before local commit."],
        "next_required_input": NEXT_REQUIRED_INPUT,
        "blocked_handoff_item_count": summary["blocked_handoff_item_count"],
        "owner_action_item_count": summary["owner_action_item_count"],
        "binding_ready_after_blocked_handoff_count": 0,
        "comparison_retry_ready_after_blocked_handoff_count": 0,
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
            "APPLICATION_BLOCKED_HANDOFF_AFTER_RESOLUTION_ATTEMPT"
        ),
        "roadmap_stage_id": "VALUE-CONSISTENCY",
        "governance_stage_id": "VALUE-CONSISTENCY",
        "name": (
            "v0.1.4 residual difference authorized source reference or exclusion "
            "application blocked handoff after resolution attempt"
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
        ("T1", "read prior resolution-attempt evidence and ignored private resolution records read-only"),
        ("T2", "write ignored private blocked-handoff records and owner-action packet"),
        ("T3", "emit public-safe NO_GO handoff evidence while keeping binding comparison and upload gates closed"),
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
                    "APPLICATION_BLOCKED_HANDOFF_AFTER_RESOLUTION_ATTEMPT"
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
    if source_summary.get("phase_id") != source_resolution.PHASE_ID:
        raise ValueError("source resolution-attempt phase mismatch")
    if source_go_no_go.get("decision") != "NO_GO":
        raise ValueError("source resolution-attempt decision must be NO_GO")
    if source_matrix.get("check_fail_count") != 0:
        raise ValueError("source resolution-attempt matrix must be clean")
    if source_summary.get("resolution_attempt_item_count") != 48:
        raise ValueError("source resolution-attempt item count must be 48")
    if source_summary.get("active_authoritative_resolution_application_count") != 0:
        raise ValueError("source active authoritative resolution applications must be zero")
    if source_summary.get("auto_applied_authorized_resolution_count") != 0:
        raise ValueError("source auto-applied resolutions must be zero")
    if source_summary.get("still_blocked_authorized_resolution_application_count") != 48:
        raise ValueError("source still-blocked resolution applications must be 48")
    if source_diagnostic.get("resolution_attempt_item_count") != 48:
        raise ValueError("source private resolution diagnostic item count must be 48")
    if len(source_rows) != 48:
        raise ValueError("source private resolution records must contain 48 rows")
    counts = Counter(row.get("intake_track") for row in source_rows)
    if dict(counts) != EXPECTED_HANDOFF_TRACK_COUNTS:
        raise ValueError(f"source resolution track counts must be {EXPECTED_HANDOFF_TRACK_COUNTS!r}")


def generate(*, generated_at: str | None = None, write_governance_event: bool = True) -> dict[str, Any]:
    generated = generated_at or _now()
    source_summary = _read_json(SOURCE_RESOLUTION_ATTEMPT_SUMMARY_PATH)
    source_manifest = _read_json(SOURCE_RESOLUTION_ATTEMPT_MANIFEST_PATH)
    source_go_no_go = _read_json(SOURCE_RESOLUTION_ATTEMPT_GO_NO_GO_PATH)
    source_matrix = _read_json(SOURCE_RESOLUTION_ATTEMPT_MATRIX_PATH)
    source_diagnostic = _read_json(SOURCE_PRIVATE_RESOLUTION_DIAGNOSTIC_PATH)
    source_rows = _read_jsonl(SOURCE_PRIVATE_RESOLUTION_RECORDS_PATH)
    SOURCE_PRIVATE_RESOLUTION_REPORT_PATH.read_text(encoding="utf-8")
    _validate_sources(
        source_summary=source_summary,
        source_go_no_go=source_go_no_go,
        source_matrix=source_matrix,
        source_diagnostic=source_diagnostic,
        source_rows=source_rows,
    )
    raw_boundary = _raw_boundary()
    public_safety = _public_safety()
    handoff_records = _build_handoff_records(generated_at=generated, source_rows=source_rows)
    private_diagnostic = _write_private_outputs(
        generated_at=generated,
        source_summary=source_summary,
        records=handoff_records,
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
        handoff_records=handoff_records,
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
        "private_blocked_handoff_records": handoff_records,
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
        "blocked handoff after resolution attempt "
        f"decision={summary['decision']} handoff={summary['blocked_handoff_item_count']} "
        f"owner_actions={summary['owner_action_item_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
