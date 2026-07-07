#!/usr/bin/env python3
"""Prepare a public-safe diagnostic packet after blocked handoff.

This phase packages the prior blocked handoff into a diagnostic packet for owner
or authorized external-agent review. It does not read the raw inbox, does not
apply any resolution, and does not claim business-value consistency.
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
    v014_residual_difference_authorized_source_reference_or_exclusion_application_blocked_handoff_after_resolution_attempt
    as source_handoff,
)


PROJECT_ROOT = Path("KMFA")
PHASE_ID = (
    "V014_RESIDUAL_DIFFERENCE_AUTHORIZED_SOURCE_REFERENCE_OR_EXCLUSION_"
    "APPLICATION_DIAGNOSTIC_PACKET_AFTER_BLOCKED_HANDOFF"
)
TASK_ID = (
    "KMFA-V014-RESIDUAL-DIFFERENCE-AUTHORIZED-SOURCE-REFERENCE-OR-EXCLUSION-"
    "APPLICATION-DIAGNOSTIC-PACKET-AFTER-BLOCKED-HANDOFF-20260708"
)
ACCEPTANCE_ID = (
    "ACC-V014-RESIDUAL-DIFFERENCE-AUTHORIZED-SOURCE-REFERENCE-OR-EXCLUSION-"
    "APPLICATION-DIAGNOSTIC-PACKET-AFTER-BLOCKED-HANDOFF"
)
VERSION = (
    "0.1.4-residual-difference-authorized-source-reference-or-exclusion-"
    "application-diagnostic-packet-after-blocked-handoff"
)
STATUS = (
    "completed_validated_local_only_authorized_source_reference_or_exclusion_"
    "application_diagnostic_packet_after_blocked_handoff_no_go"
)
DECISION = "NO_GO"
DIAGNOSTIC_CONCLUSION = "diagnostic_packet_ready_waiting_for_authorized_resolution_input"
NEXT_REQUIRED_INPUT = source_handoff.NEXT_REQUIRED_INPUT
NEXT_RECOMMENDED_PHASE = source_handoff.NEXT_RECOMMENDED_PHASE

PRIVATE_SLOT_KEY = source_handoff.PRIVATE_SLOT_KEY
SOURCE_REFERENCE_INTAKE_TRACK = source_handoff.SOURCE_REFERENCE_INTAKE_TRACK
FORMULA_MAPPING_INTAKE_TRACK = source_handoff.FORMULA_MAPPING_INTAKE_TRACK
EXPECTED_DIAGNOSTIC_TRACK_COUNTS = source_handoff.EXPECTED_HANDOFF_TRACK_COUNTS

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = (
    MACHINE_DIR
    / "residual_difference_authorized_source_reference_or_exclusion_application_diagnostic_packet_after_blocked_handoff_summary.json"
)
MANIFEST_PATH = (
    MACHINE_DIR
    / "residual_difference_authorized_source_reference_or_exclusion_application_diagnostic_packet_after_blocked_handoff_manifest.json"
)
GO_NO_GO_PATH = (
    MACHINE_DIR
    / "residual_difference_authorized_source_reference_or_exclusion_application_diagnostic_packet_after_blocked_handoff_go_no_go_report.json"
)
MATRIX_PATH = (
    MACHINE_DIR
    / "residual_difference_authorized_source_reference_or_exclusion_application_diagnostic_packet_after_blocked_handoff_matrix_public_safe.json"
)
REPORT_PATH = (
    HUMAN_DIR
    / "residual_difference_authorized_source_reference_or_exclusion_application_diagnostic_packet_after_blocked_handoff.md"
)
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_authorized_source_reference_or_exclusion_application_diagnostic_packet_after_blocked_handoff_summary.json"
)
METADATA_MANIFEST_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_authorized_source_reference_or_exclusion_application_diagnostic_packet_after_blocked_handoff_manifest.json"
)
METADATA_GO_NO_GO_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_authorized_source_reference_or_exclusion_application_diagnostic_packet_after_blocked_handoff_go_no_go_report.json"
)
METADATA_MATRIX_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_authorized_source_reference_or_exclusion_application_diagnostic_packet_after_blocked_handoff_matrix_public_safe.json"
)

SOURCE_BLOCKED_HANDOFF_SUMMARY_PATH = source_handoff.METADATA_SUMMARY_PATH
SOURCE_BLOCKED_HANDOFF_MANIFEST_PATH = source_handoff.METADATA_MANIFEST_PATH
SOURCE_BLOCKED_HANDOFF_GO_NO_GO_PATH = source_handoff.METADATA_GO_NO_GO_PATH
SOURCE_BLOCKED_HANDOFF_MATRIX_PATH = source_handoff.METADATA_MATRIX_PATH
SOURCE_PRIVATE_BLOCKED_HANDOFF_DIAGNOSTIC_PATH = source_handoff.PRIVATE_BLOCKED_HANDOFF_DIAGNOSTIC_PATH
SOURCE_PRIVATE_BLOCKED_HANDOFF_RECORDS_PATH = source_handoff.PRIVATE_BLOCKED_HANDOFF_RECORDS_PATH
SOURCE_PRIVATE_BLOCKED_HANDOFF_PACKET_PATH = source_handoff.PRIVATE_BLOCKED_HANDOFF_PACKET_PATH

PRIVATE_OUTPUT_DIR = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_residual_difference_authorized_source_reference_or_exclusion_application_diagnostic_packet_after_blocked_handoff"
)
PRIVATE_DIAGNOSTIC_PACKET_PATH = PRIVATE_OUTPUT_DIR / "private_diagnostic_packet.json"
PRIVATE_DIAGNOSTIC_QUEUE_PATH = PRIVATE_OUTPUT_DIR / "private_diagnostic_queue.jsonl"
PRIVATE_DIAGNOSTIC_REPORT_PATH = PRIVATE_OUTPUT_DIR / "private_diagnostic_report.md"

DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"
STAGE_STATUS_PATH = PROJECT_ROOT / "metadata/stage_status.jsonl"
TASK_STATUS_PATH = PROJECT_ROOT / "metadata/traceability/v1_4_stage_phase_task_status.jsonl"


def _raw_boundary() -> dict[str, bool]:
    return {
        "user_declared_raw_data_immutable": True,
        "raw_data_root_readonly_policy_active": True,
        "source_blocked_handoff_public_artifacts_read_by_this_phase": True,
        "source_blocked_handoff_manifest_read_by_this_phase": True,
        "source_blocked_handoff_go_no_go_read_by_this_phase": True,
        "source_blocked_handoff_matrix_read_by_this_phase": True,
        "source_private_blocked_handoff_diagnostic_read_by_this_phase": True,
        "source_private_blocked_handoff_records_read_by_this_phase": True,
        "source_private_blocked_handoff_packet_read_by_this_phase": True,
        "private_diagnostic_packet_written_by_this_phase": True,
        "private_diagnostic_queue_written_by_this_phase": True,
        "private_diagnostic_report_written_by_this_phase": True,
        "source_private_blocked_handoff_diagnostic_mutated_by_this_phase": False,
        "source_private_blocked_handoff_records_mutated_by_this_phase": False,
        "source_private_blocked_handoff_packet_mutated_by_this_phase": False,
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
        "source_private_blocked_handoff_diagnostic_committed": False,
        "source_private_blocked_handoff_records_committed": False,
        "source_private_blocked_handoff_packet_committed": False,
        "private_diagnostic_packet_committed": False,
        "private_diagnostic_queue_committed": False,
        "private_diagnostic_report_committed": False,
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


def _diagnostic_kind(track: str | None) -> str:
    if track == SOURCE_REFERENCE_INTAKE_TRACK:
        return "provide_authoritative_source_reference_or_owner_exclusion"
    if track == FORMULA_MAPPING_INTAKE_TRACK:
        return "provide_formula_or_non_numeric_mapping"
    return "provide_authorized_resolution_application"


def _build_diagnostic_records(*, generated_at: str, source_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, row in enumerate(source_rows, start=1):
        records.append(
            {
                "diagnostic_packet_item_id": f"ASR-OE-APP-DIAG-PACKET-BH-{index:03d}",
                "phase_id": PHASE_ID,
                "task_id": TASK_ID,
                "generated_at": generated_at,
                "source_blocked_handoff_item_id": row.get("blocked_handoff_item_id"),
                PRIVATE_SLOT_KEY: row.get(PRIVATE_SLOT_KEY),
                "intake_track": row.get("intake_track"),
                "source_required_authorized_input_type": row.get("required_authorized_input_type"),
                "diagnostic_kind": _diagnostic_kind(row.get("intake_track")),
                "diagnostic_packet_status": "waiting_for_authorized_resolution_input",
                "owner_or_external_agent_action_required": True,
                "external_agent_private_packet_item": True,
                "safe_auto_resolution_available": False,
                "binding_ready_after_diagnostic_packet": False,
                "comparison_retry_ready_after_diagnostic_packet": False,
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
    status_counts = Counter(row.get("diagnostic_packet_status") for row in records)
    diagnostic = {
        "schema_version": "kmfa.private.v014_authorized_resolution_diagnostic_packet_after_blocked_handoff.v1",
        "classification": "private_authorized_resolution_diagnostic_packet_after_blocked_handoff_do_not_commit",
        "record_type": "v014_authorized_resolution_diagnostic_packet_after_blocked_handoff_private_packet",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "source_phase_id": source_summary.get("phase_id"),
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "diagnostic_packet_item_count": len(records),
        "external_agent_private_packet_item_count": len(records),
        "track_counts": dict(track_counts),
        "status_counts": dict(status_counts),
        "binding_ready_after_diagnostic_packet_count": 0,
        "comparison_retry_ready_after_diagnostic_packet_count": 0,
        "raw_boundary": raw_boundary,
    }
    _write_json(PRIVATE_DIAGNOSTIC_PACKET_PATH, diagnostic)
    _write_jsonl(PRIVATE_DIAGNOSTIC_QUEUE_PATH, records)
    _write_text(
        PRIVATE_DIAGNOSTIC_REPORT_PATH,
        "\n".join(
            [
                "# Private Authorized Resolution Diagnostic Packet After Blocked Handoff",
                "",
                f"- phase_id: `{PHASE_ID}`",
                f"- diagnostic_packet_item_count: `{len(records)}`",
                f"- external_agent_private_packet_item_count: `{len(records)}`",
                "- binding_ready_after_diagnostic_packet_count: `0`",
                "- comparison_retry_ready_after_diagnostic_packet_count: `0`",
                "- raw_to_processed_value_comparison_performed_by_this_phase: `false`",
                "",
                "This private packet may contain private handles and must remain ignored.",
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
    diagnostic_records: list[dict[str, Any]],
    raw_boundary: dict[str, bool],
    public_safety: dict[str, bool],
) -> dict[str, Any]:
    track_counts = Counter(row.get("intake_track") for row in diagnostic_records)
    return {
        "schema_version": "kmfa.v014_authorized_resolution_diagnostic_packet_after_blocked_handoff_summary.v1",
        "record_type": "v014_authorized_resolution_diagnostic_packet_after_blocked_handoff_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": generated_at,
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "source_phase_id": source_summary.get("phase_id"),
        "source_manifest_phase_id": source_manifest.get("phase_id"),
        "source_go_no_go_decision": source_go_no_go.get("decision"),
        "source_matrix_check_fail_count": source_matrix.get("check_fail_count"),
        "source_private_diagnostic_phase_id": source_diagnostic.get("phase_id"),
        "source_private_blocked_handoff_record_count": len(source_rows),
        "source_blocked_handoff_item_count": source_summary.get("blocked_handoff_item_count"),
        "source_owner_action_item_count": source_summary.get("owner_action_item_count"),
        "source_authorized_resolution_blockers_remain": source_summary.get(
            "authorized_resolution_blockers_remain"
        ),
        "diagnostic_packet_prepared_by_this_phase": True,
        "external_agent_private_packet_ready": True,
        "diagnostic_packet_item_count": len(diagnostic_records),
        "external_agent_private_packet_item_count": len(diagnostic_records),
        "source_reference_or_owner_exclusion_diagnostic_item_count": track_counts[
            SOURCE_REFERENCE_INTAKE_TRACK
        ],
        "formula_or_non_numeric_mapping_diagnostic_item_count": track_counts[
            FORMULA_MAPPING_INTAKE_TRACK
        ],
        "safe_auto_resolution_available_count": 0,
        "binding_ready_after_diagnostic_packet_count": 0,
        "comparison_retry_ready_after_diagnostic_packet_count": 0,
        "unresolved_difference_count": source_summary.get("unresolved_difference_count"),
        "private_diagnostic_packet_written": True,
        "private_diagnostic_queue_written": True,
        "private_diagnostic_report_written": True,
        "private_diagnostic_packet_gitignored": _git_check_ignored(PRIVATE_DIAGNOSTIC_PACKET_PATH),
        "private_diagnostic_queue_gitignored": _git_check_ignored(PRIVATE_DIAGNOSTIC_QUEUE_PATH),
        "private_diagnostic_report_gitignored": _git_check_ignored(PRIVATE_DIAGNOSTIC_REPORT_PATH),
        "source_private_blocked_handoff_diagnostic_gitignored": _git_check_ignored(
            SOURCE_PRIVATE_BLOCKED_HANDOFF_DIAGNOSTIC_PATH
        ),
        "source_private_blocked_handoff_records_gitignored": _git_check_ignored(
            SOURCE_PRIVATE_BLOCKED_HANDOFF_RECORDS_PATH
        ),
        "source_private_blocked_handoff_packet_gitignored": _git_check_ignored(
            SOURCE_PRIVATE_BLOCKED_HANDOFF_PACKET_PATH
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
        ("source_blocked_handoff_loaded", str(summary["source_phase_id"]).endswith("APPLICATION_BLOCKED_HANDOFF_AFTER_RESOLUTION_ATTEMPT")),
        ("source_go_no_go_preserved", summary["source_go_no_go_decision"] == "NO_GO"),
        ("source_matrix_clean", summary["source_matrix_check_fail_count"] == 0),
        ("source_private_records_locked", summary["source_private_blocked_handoff_record_count"] == 48),
        ("source_blocked_handoff_items_locked", summary["source_blocked_handoff_item_count"] == 48),
        ("source_owner_actions_locked", summary["source_owner_action_item_count"] == 48),
        ("source_blockers_remain", summary["source_authorized_resolution_blockers_remain"] is True),
        ("diagnostic_packet_items_locked", summary["diagnostic_packet_item_count"] == 48),
        ("external_agent_packet_ready", summary["external_agent_private_packet_ready"] is True),
        (
            "diagnostic_track_counts_locked",
            summary["source_reference_or_owner_exclusion_diagnostic_item_count"] == 40
            and summary["formula_or_non_numeric_mapping_diagnostic_item_count"] == 8,
        ),
        (
            "no_binding_or_retry_ready_after_packet",
            summary["binding_ready_after_diagnostic_packet_count"] == 0
            and summary["comparison_retry_ready_after_diagnostic_packet_count"] == 0,
        ),
        ("private_diagnostic_outputs_ignored", summary["private_diagnostic_queue_gitignored"] is True),
        ("raw_inbox_untouched", summary["raw_boundary"]["raw_inbox_mutated_by_this_phase"] is False),
        ("public_safe_aggregate_only", summary["public_safety"]["public_safe_aggregate_only"] is True),
        ("downstream_gates_closed", summary["github_upload_performed"] is False and summary["business_execution_performed"] is False),
    ]
    rows = [{"check_code": code, "status": "PASS" if passed else "FAIL"} for code, passed in checks]
    pass_count = sum(1 for row in rows if row["status"] == "PASS")
    return {
        "schema_version": "kmfa.v014_authorized_resolution_diagnostic_packet_after_blocked_handoff_matrix_public_safe.v1",
        "record_type": "v014_authorized_resolution_diagnostic_packet_after_blocked_handoff_matrix_public_safe",
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
        "schema_version": "kmfa.v014_authorized_resolution_diagnostic_packet_after_blocked_handoff_go_no_go.v1",
        "record_type": "v014_authorized_resolution_diagnostic_packet_after_blocked_handoff_go_no_go",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": summary["generated_at"],
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "diagnostic_packet_item_count": summary["diagnostic_packet_item_count"],
        "external_agent_private_packet_ready": True,
        "binding_ready_after_diagnostic_packet_count": 0,
        "comparison_retry_ready_after_diagnostic_packet_count": 0,
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
    report = f"""# V014 Authorized Source Reference Or Exclusion Application Diagnostic Packet After Blocked Handoff

Generated at: {summary["generated_at"]}

## Scope

- Phase: `{PHASE_ID}`
- Decision: `{DECISION}`
- Status: `{STATUS}`
- Source: prior public-safe blocked-handoff evidence and ignored private blocked-handoff records.
- Raw boundary: no raw inbox read, list, stat, parse, value extraction, write, delete, move, rename, copy, normalize or mutation.

## Public-Safe Diagnostic Result

- Source blocked handoff items: `{summary["source_blocked_handoff_item_count"]}`
- Source owner action items: `{summary["source_owner_action_item_count"]}`
- Diagnostic packet items: `{summary["diagnostic_packet_item_count"]}`
- External agent private packet items: `{summary["external_agent_private_packet_item_count"]}`
- Source reference or owner exclusion diagnostic items: `{summary["source_reference_or_owner_exclusion_diagnostic_item_count"]}`
- Formula or non-numeric mapping diagnostic items: `{summary["formula_or_non_numeric_mapping_diagnostic_item_count"]}`
- Binding ready after diagnostic packet: `{summary["binding_ready_after_diagnostic_packet_count"]}`
- Comparison retry ready after diagnostic packet: `{summary["comparison_retry_ready_after_diagnostic_packet_count"]}`
- Unresolved differences after this phase: `{summary["unresolved_difference_count"]}`

## Gate

This phase prepares a diagnostic packet only. It does not apply owner/agent answers, bind fingerprints, compare raw and processed values, reconcile processed data, claim business consistency, upload to GitHub, reinstall the app, or execute business use.

Next required input: `{NEXT_REQUIRED_INPUT}`.
"""
    go_record = f"""# Go / No-Go Record

- Phase: `{PHASE_ID}`
- Decision: `{go_no_go["decision"]}`
- Reason: `{DIAGNOSTIC_CONCLUSION}`
- Matrix: `{matrix["check_pass_count"]}` pass / `{matrix["check_fail_count"]}` fail
- GitHub upload: not allowed in this phase.
- App reinstall: not allowed in this phase.
"""
    test_results = f"""# Test Results

- RED: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_authorized_source_reference_or_exclusion_application_diagnostic_packet_after_blocked_handoff` failed before implementation because the generator module did not exist.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_diagnostic_packet_after_blocked_handoff.py --generated-at 2026-07-08T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_diagnostic_packet_after_blocked_handoff.py --require-private-packet`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_authorized_source_reference_or_exclusion_application_diagnostic_packet_after_blocked_handoff`
- Governance validators, CSV shape checks, diff check, raw/private marker scan, secret scan and private-runtime tracked-file scan: expected before commit.

Expected matrix result: {matrix["check_pass_count"]}/{matrix["check_count"]} PASS.
"""
    risk_register = """# Risk Register

- Risk: diagnostic packet is mistaken for discrepancy closure.
- Control: decision remains NO_GO and binding, comparison, reconciliation and business consistency flags remain false.
- Risk: private slot or owner-action details leak into public artifacts.
- Control: public artifacts contain aggregate counts only; private diagnostic outputs stay ignored.
- Risk: raw inbox is modified.
- Control: this phase consumes existing ignored blocked-handoff artifacts only and does not touch the raw inbox.
"""
    rollback = f"""# Rollback Plan

Remove artifacts for `{PHASE_ID}`, metadata copies, private diagnostic outputs, tool, validator, focused test and governance rows. Do not touch source blocked-handoff evidence, prior private artifacts or raw inbox files.
"""
    _write_text(REPORT_PATH, report)
    _write_text(GO_NO_GO_RECORD_PATH, go_record)
    _write_text(TEST_RESULTS_PATH, test_results)
    _write_text(RISK_REGISTER_PATH, risk_register)
    _write_text(ROLLBACK_PATH, rollback)


def _build_manifest(summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v014_authorized_resolution_diagnostic_packet_after_blocked_handoff_manifest.v1",
        "record_type": "v014_authorized_resolution_diagnostic_packet_after_blocked_handoff_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": summary["generated_at"],
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "summary": summary,
        "matrix": matrix,
        "go_no_go_report": go_no_go,
        "source_artifacts": {
            "blocked_handoff_summary": "public_safe_metadata_copy",
            "blocked_handoff_manifest": "public_safe_metadata_copy",
            "blocked_handoff_go_no_go": "public_safe_metadata_copy",
            "blocked_handoff_matrix": "public_safe_metadata_copy",
            "blocked_handoff_private_diagnostic": "ignored_private_runtime",
            "blocked_handoff_private_records": "ignored_private_runtime",
            "blocked_handoff_private_packet": "ignored_private_runtime",
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
            "private:authorized_resolution_diagnostic_packet",
            "private:authorized_resolution_diagnostic_queue",
            "private:authorized_resolution_diagnostic_report",
        ],
        "raw_boundary": summary["raw_boundary"],
        "public_safety": summary["public_safety"],
        "test_commands": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_diagnostic_packet_after_blocked_handoff.py --generated-at 2026-07-08T00:00:00+10:00",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_diagnostic_packet_after_blocked_handoff.py --require-private-packet",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_authorized_source_reference_or_exclusion_application_diagnostic_packet_after_blocked_handoff",
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
            "APPLICATION-DIAGNOSTIC-PACKET-AFTER-BLOCKED-HANDOFF"
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
        "summary": "Prepared a public-safe diagnostic packet for the 48 blocked handoff items; downstream gates remain closed.",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "files_changed": _changed_kmfa_files(),
        "test_commands": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_diagnostic_packet_after_blocked_handoff.py --generated-at 2026-07-08T00:00:00+10:00",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_diagnostic_packet_after_blocked_handoff.py --require-private-packet",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_authorized_source_reference_or_exclusion_application_diagnostic_packet_after_blocked_handoff",
        ],
        "test_results": ["PENDING: final validation results will be recorded before local commit."],
        "next_required_input": NEXT_REQUIRED_INPUT,
        "diagnostic_packet_item_count": summary["diagnostic_packet_item_count"],
        "external_agent_private_packet_ready": True,
        "binding_ready_after_diagnostic_packet_count": 0,
        "comparison_retry_ready_after_diagnostic_packet_count": 0,
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
            "APPLICATION_DIAGNOSTIC_PACKET_AFTER_BLOCKED_HANDOFF"
        ),
        "roadmap_stage_id": "VALUE-CONSISTENCY",
        "governance_stage_id": "VALUE-CONSISTENCY",
        "name": (
            "v0.1.4 residual difference authorized source reference or exclusion "
            "application diagnostic packet after blocked handoff"
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
        ("T1", "read prior blocked-handoff evidence and ignored private handoff records read-only"),
        ("T2", "write ignored private diagnostic packet and diagnostic queue"),
        ("T3", "emit public-safe NO_GO diagnostic evidence while keeping binding comparison and upload gates closed"),
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
                    "APPLICATION_DIAGNOSTIC_PACKET_AFTER_BLOCKED_HANDOFF"
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
    if source_summary.get("phase_id") != source_handoff.PHASE_ID:
        raise ValueError("source blocked-handoff phase mismatch")
    if source_go_no_go.get("decision") != "NO_GO":
        raise ValueError("source blocked-handoff decision must be NO_GO")
    if source_matrix.get("check_fail_count") != 0:
        raise ValueError("source blocked-handoff matrix must be clean")
    if source_summary.get("blocked_handoff_item_count") != 48:
        raise ValueError("source blocked handoff item count must be 48")
    if source_summary.get("owner_action_item_count") != 48:
        raise ValueError("source owner action item count must be 48")
    if source_summary.get("authorized_resolution_blockers_remain") is not True:
        raise ValueError("source authorized resolution blockers must remain")
    if source_diagnostic.get("blocked_handoff_item_count") != 48:
        raise ValueError("source private blocked-handoff diagnostic item count must be 48")
    if len(source_rows) != 48:
        raise ValueError("source private blocked-handoff records must contain 48 rows")
    counts = Counter(row.get("intake_track") for row in source_rows)
    if dict(counts) != EXPECTED_DIAGNOSTIC_TRACK_COUNTS:
        raise ValueError(f"source blocked-handoff track counts must be {EXPECTED_DIAGNOSTIC_TRACK_COUNTS!r}")


def generate(*, generated_at: str | None = None, write_governance_event: bool = True) -> dict[str, Any]:
    generated = generated_at or _now()
    source_summary = _read_json(SOURCE_BLOCKED_HANDOFF_SUMMARY_PATH)
    source_manifest = _read_json(SOURCE_BLOCKED_HANDOFF_MANIFEST_PATH)
    source_go_no_go = _read_json(SOURCE_BLOCKED_HANDOFF_GO_NO_GO_PATH)
    source_matrix = _read_json(SOURCE_BLOCKED_HANDOFF_MATRIX_PATH)
    source_diagnostic = _read_json(SOURCE_PRIVATE_BLOCKED_HANDOFF_DIAGNOSTIC_PATH)
    source_rows = _read_jsonl(SOURCE_PRIVATE_BLOCKED_HANDOFF_RECORDS_PATH)
    SOURCE_PRIVATE_BLOCKED_HANDOFF_PACKET_PATH.read_text(encoding="utf-8")
    _validate_sources(
        source_summary=source_summary,
        source_go_no_go=source_go_no_go,
        source_matrix=source_matrix,
        source_diagnostic=source_diagnostic,
        source_rows=source_rows,
    )
    raw_boundary = _raw_boundary()
    public_safety = _public_safety()
    diagnostic_records = _build_diagnostic_records(generated_at=generated, source_rows=source_rows)
    private_diagnostic = _write_private_outputs(
        generated_at=generated,
        source_summary=source_summary,
        records=diagnostic_records,
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
        diagnostic_records=diagnostic_records,
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
        "private_diagnostic_records": diagnostic_records,
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
        "diagnostic packet after blocked handoff "
        f"decision={summary['decision']} packet={summary['diagnostic_packet_item_count']} "
        f"external_ready={summary['external_agent_private_packet_ready']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
