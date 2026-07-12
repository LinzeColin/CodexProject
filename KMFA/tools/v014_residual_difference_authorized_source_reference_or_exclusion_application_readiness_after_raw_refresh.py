#!/usr/bin/env python3
"""Create application-readiness evidence for authorized source references after raw refresh.

This phase consumes the prior public-safe intake evidence and ignored private
intake queue, then determines whether any item is ready for private
application. It does not apply source references, owner exclusions, formula
mappings, raw candidate fingerprints, raw-to-processed comparison, GitHub
upload, app reinstall, or business execution. Public artifacts remain
aggregate-only.
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
    v014_residual_difference_authorized_source_reference_or_exclusion_intake_after_raw_refresh
    as source_intake,
)


PROJECT_ROOT = Path("KMFA")
PHASE_ID = (
    "V014_RESIDUAL_DIFFERENCE_AUTHORIZED_SOURCE_REFERENCE_OR_EXCLUSION_APPLICATION_READINESS_AFTER_RAW_REFRESH"
)
TASK_ID = (
    "KMFA-V014-RESIDUAL-DIFFERENCE-AUTHORIZED-SOURCE-REFERENCE-OR-EXCLUSION-"
    "APPLICATION-READINESS-AFTER-RAW-REFRESH-20260708"
)
ACCEPTANCE_ID = (
    "ACC-V014-RESIDUAL-DIFFERENCE-AUTHORIZED-SOURCE-REFERENCE-OR-EXCLUSION-"
    "APPLICATION-READINESS-AFTER-RAW-REFRESH"
)
VERSION = (
    "0.1.4-residual-difference-authorized-source-reference-or-exclusion-"
    "application-readiness-after-raw-refresh"
)
STATUS = (
    "completed_validated_local_only_authorized_source_reference_or_exclusion_"
    "application_readiness_after_raw_refresh_no_go"
)
DECISION = "NO_GO"
DIAGNOSTIC_CONCLUSION = "private_resolution_application_readiness_blocked_no_authoritative_binding_records"
NEXT_REQUIRED_INPUT = "owner_or_authorized_delegate_applies_source_reference_exclusion_or_formula_mapping_before_binding"
NEXT_RECOMMENDED_PHASE = (
    "V014_RESIDUAL_DIFFERENCE_AUTHORIZED_SOURCE_REFERENCE_OR_EXCLUSION_APPLICATION_BLOCKER_AUDIT_AFTER_RAW_REFRESH"
)

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = (
    MACHINE_DIR
    / "residual_difference_authorized_source_reference_or_exclusion_application_readiness_after_raw_refresh_summary.json"
)
MANIFEST_PATH = (
    MACHINE_DIR
    / "residual_difference_authorized_source_reference_or_exclusion_application_readiness_after_raw_refresh_manifest.json"
)
GO_NO_GO_PATH = (
    MACHINE_DIR
    / "residual_difference_authorized_source_reference_or_exclusion_application_readiness_after_raw_refresh_go_no_go_report.json"
)
MATRIX_PATH = (
    MACHINE_DIR
    / "residual_difference_authorized_source_reference_or_exclusion_application_readiness_after_raw_refresh_matrix_public_safe.json"
)
REPORT_PATH = (
    HUMAN_DIR / "residual_difference_authorized_source_reference_or_exclusion_application_readiness_after_raw_refresh.md"
)
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_authorized_source_reference_or_exclusion_application_readiness_after_raw_refresh_summary.json"
)
METADATA_MANIFEST_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_authorized_source_reference_or_exclusion_application_readiness_after_raw_refresh_manifest.json"
)
METADATA_GO_NO_GO_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_authorized_source_reference_or_exclusion_application_readiness_after_raw_refresh_go_no_go_report.json"
)
METADATA_MATRIX_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_authorized_source_reference_or_exclusion_application_readiness_after_raw_refresh_matrix_public_safe.json"
)

SOURCE_INTAKE_SUMMARY_PATH = source_intake.METADATA_SUMMARY_PATH
SOURCE_INTAKE_MANIFEST_PATH = source_intake.METADATA_MANIFEST_PATH
SOURCE_INTAKE_GO_NO_GO_PATH = source_intake.METADATA_GO_NO_GO_PATH
SOURCE_INTAKE_MATRIX_PATH = source_intake.METADATA_MATRIX_PATH
SOURCE_PRIVATE_ACTIVE_RECORD_PATH = source_intake.PRIVATE_ACTIVE_RECORD_PATH
SOURCE_PRIVATE_INTAKE_QUEUE_PATH = source_intake.PRIVATE_INTAKE_QUEUE_PATH
SOURCE_PRIVATE_DIAGNOSTIC_PATH = source_intake.PRIVATE_DIAGNOSTIC_PATH
SOURCE_PRIVATE_REPORT_PATH = source_intake.PRIVATE_REPORT_PATH

PRIVATE_OUTPUT_DIR = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_residual_difference_authorized_source_reference_or_exclusion_application_readiness_after_raw_refresh"
)
PRIVATE_DIAGNOSTIC_PATH = (
    PRIVATE_OUTPUT_DIR / "private_authorized_source_reference_or_exclusion_application_readiness_diagnostic.json"
)
PRIVATE_READY_QUEUE_PATH = (
    PRIVATE_OUTPUT_DIR / "private_authorized_source_reference_or_exclusion_application_ready_queue.jsonl"
)
PRIVATE_BLOCKER_QUEUE_PATH = (
    PRIVATE_OUTPUT_DIR / "private_authorized_source_reference_or_exclusion_application_blocker_queue.jsonl"
)
PRIVATE_REPORT_PATH = PRIVATE_OUTPUT_DIR / "private_authorized_source_reference_or_exclusion_application_readiness.md"

DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"
STAGE_STATUS_PATH = PROJECT_ROOT / "metadata/stage_status.jsonl"
TASK_STATUS_PATH = PROJECT_ROOT / "metadata/traceability/v1_4_stage_phase_task_status.jsonl"

SOURCE_REFERENCE_INTAKE_TRACK = "source_reference_or_owner_exclusion"
FORMULA_MAPPING_INTAKE_TRACK = "formula_or_non_numeric_mapping"
EXPECTED_INTAKE_TRACK_COUNTS = {
    SOURCE_REFERENCE_INTAKE_TRACK: 40,
    FORMULA_MAPPING_INTAKE_TRACK: 8,
}


def _raw_boundary() -> dict[str, bool]:
    return {
        "user_declared_raw_data_immutable": True,
        "raw_data_root_readonly_policy_active": True,
        "source_intake_public_artifacts_read_by_this_phase": True,
        "source_intake_manifest_read_by_this_phase": True,
        "source_intake_go_no_go_read_by_this_phase": True,
        "source_intake_matrix_read_by_this_phase": True,
        "source_private_active_record_read_by_this_phase": True,
        "source_private_intake_queue_read_by_this_phase": True,
        "source_private_intake_diagnostic_read_by_this_phase": True,
        "source_private_intake_report_read_by_this_phase": True,
        "private_application_readiness_diagnostic_written_by_this_phase": True,
        "private_application_ready_queue_written_by_this_phase": True,
        "private_application_blocker_queue_written_by_this_phase": True,
        "source_private_active_record_mutated_by_this_phase": False,
        "source_private_intake_queue_mutated_by_this_phase": False,
        "source_private_intake_diagnostic_mutated_by_this_phase": False,
        "source_private_intake_report_mutated_by_this_phase": False,
        "authoritative_source_reference_applied_by_this_phase": False,
        "owner_exclusion_applied_by_this_phase": False,
        "formula_mapping_applied_by_this_phase": False,
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
        "source_private_active_record_committed": False,
        "source_private_intake_queue_committed": False,
        "source_private_intake_diagnostic_committed": False,
        "source_private_intake_report_committed": False,
        "private_application_readiness_diagnostic_committed": False,
        "private_application_ready_queue_committed": False,
        "private_application_blocker_queue_committed": False,
        "private_application_report_committed": False,
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


def _active_decision_present(row: dict[str, Any]) -> bool:
    return any(
        row.get(key) is True
        for key in (
            "authoritative_source_reference_applied_by_this_phase",
            "owner_exclusion_applied_by_this_phase",
            "formula_mapping_applied_by_this_phase",
            "authoritative_binding_applied_by_this_phase",
            "binding_ready_after_intake",
            "comparison_retry_ready_after_intake",
        )
    )


def _blocker_code(row: dict[str, Any]) -> str:
    if row.get("intake_track") == FORMULA_MAPPING_INTAKE_TRACK:
        return "missing_formula_or_non_numeric_mapping_application"
    return "missing_authoritative_source_reference_or_owner_exclusion_application"


def _build_private_readiness_queues(
    *, generated_at: str, intake_rows: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    ready_rows: list[dict[str, Any]] = []
    blocker_rows: list[dict[str, Any]] = []
    for index, row in enumerate(intake_rows, start=1):
        application_ready = _active_decision_present(row)
        readiness_row = {
            "application_readiness_item_id": f"ASR-OE-APP-READY-{index:03d}",
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "generated_at": generated_at,
            "source_intake_item_id": row.get("intake_item_id"),
            PRIVATE_SLOT_KEY: row.get(PRIVATE_SLOT_KEY),
            "intake_track": row.get("intake_track"),
            "source_diagnostic_track": row.get("source_diagnostic_track"),
            "allowed_private_resolution_codes": row.get("allowed_private_resolution_codes"),
            "authoritative_decision_present": application_ready,
            "application_ready": application_ready,
            "application_blocker_code": None if application_ready else _blocker_code(row),
            "authoritative_source_reference_application_ready": False,
            "owner_exclusion_application_ready": False,
            "formula_mapping_application_ready": False,
            "non_numeric_mapping_application_ready": False,
            "authoritative_binding_application_ready": False,
            "binding_ready_after_application_readiness": False,
            "raw_candidate_fingerprint_bound_by_this_phase": False,
            "comparison_retry_ready_after_application_readiness": False,
            "raw_to_processed_value_comparison_ready": False,
            "raw_to_processed_value_comparison_performed_by_this_phase": False,
            "full_reconciliation_allowed_by_this_phase": False,
            "public_commit_allowed": False,
        }
        if application_ready:
            ready_rows.append(readiness_row)
        else:
            blocker_rows.append(readiness_row)
    return ready_rows, blocker_rows


def _build_summary(
    *,
    generated_at: str,
    source_summary: dict[str, Any],
    source_manifest: dict[str, Any],
    source_go_no_go: dict[str, Any],
    source_matrix: dict[str, Any],
    source_active_record: dict[str, Any],
    source_intake_rows: list[dict[str, Any]],
    source_private_diagnostic: dict[str, Any],
    source_private_report: str,
    ready_rows: list[dict[str, Any]],
    blocker_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    del source_private_report
    intake_counts = Counter(row.get("intake_track") for row in source_intake_rows)
    blocker_counts = Counter(row.get("intake_track") for row in blocker_rows)
    ready_counts = Counter(row.get("intake_track") for row in ready_rows)
    return {
        "schema_version": (
            "kmfa.v014_authorized_source_reference_or_exclusion_application_readiness_after_raw_refresh_summary.v1"
        ),
        "record_type": (
            "v014_authorized_source_reference_or_exclusion_application_readiness_after_raw_refresh_summary"
        ),
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
        "source_private_active_record_phase_id": source_active_record.get("phase_id"),
        "source_private_diagnostic_phase_id": source_private_diagnostic.get("phase_id"),
        "source_intake_item_count": source_summary.get("intake_item_count"),
        "source_private_active_record_item_count": source_active_record.get("intake_item_count"),
        "source_private_intake_queue_count": len(source_intake_rows),
        "source_reference_or_owner_exclusion_intake_count": intake_counts[SOURCE_REFERENCE_INTAKE_TRACK],
        "formula_or_non_numeric_mapping_intake_count": intake_counts[FORMULA_MAPPING_INTAKE_TRACK],
        "application_readiness_item_count": len(source_intake_rows),
        "application_ready_item_count": len(ready_rows),
        "application_blocker_item_count": len(blocker_rows),
        "source_reference_or_owner_exclusion_application_ready_count": ready_counts[
            SOURCE_REFERENCE_INTAKE_TRACK
        ],
        "formula_or_non_numeric_mapping_application_ready_count": ready_counts[FORMULA_MAPPING_INTAKE_TRACK],
        "source_reference_or_owner_exclusion_application_blocker_count": blocker_counts[
            SOURCE_REFERENCE_INTAKE_TRACK
        ],
        "formula_or_non_numeric_mapping_application_blocker_count": blocker_counts[FORMULA_MAPPING_INTAKE_TRACK],
        "active_authoritative_decision_count": source_summary.get("active_authoritative_decision_count"),
        "authoritative_source_reference_application_ready_count": 0,
        "owner_exclusion_application_ready_count": 0,
        "formula_mapping_application_ready_count": 0,
        "non_numeric_mapping_application_ready_count": 0,
        "binding_ready_after_application_readiness_count": 0,
        "comparison_retry_ready_after_application_readiness_count": 0,
        "unresolved_difference_count": source_summary.get("unresolved_difference_count"),
        "private_application_readiness_diagnostic_written": True,
        "private_application_ready_queue_written": True,
        "private_application_blocker_queue_written": True,
        "private_application_report_written": True,
        "private_application_readiness_diagnostic_gitignored": _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH),
        "private_application_ready_queue_gitignored": _git_check_ignored(PRIVATE_READY_QUEUE_PATH),
        "private_application_blocker_queue_gitignored": _git_check_ignored(PRIVATE_BLOCKER_QUEUE_PATH),
        "private_application_report_gitignored": _git_check_ignored(PRIVATE_REPORT_PATH),
        "source_private_active_record_gitignored": _git_check_ignored(SOURCE_PRIVATE_ACTIVE_RECORD_PATH),
        "source_private_intake_queue_gitignored": _git_check_ignored(SOURCE_PRIVATE_INTAKE_QUEUE_PATH),
        "source_private_diagnostic_gitignored": _git_check_ignored(SOURCE_PRIVATE_DIAGNOSTIC_PATH),
        "authoritative_binding_application_ready": False,
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
        ("source_intake_phase_loaded", str(summary["source_phase_id"]).endswith("INTAKE_AFTER_RAW_REFRESH")),
        ("source_go_no_go_preserved", summary["source_go_no_go_decision"] == "NO_GO"),
        ("source_matrix_clean", summary["source_matrix_check_fail_count"] == 0),
        ("source_intake_count_locked", summary["source_intake_item_count"] == 48),
        ("source_private_queue_count_locked", summary["source_private_intake_queue_count"] == 48),
        ("source_intake_track_counts_locked", summary["source_reference_or_owner_exclusion_intake_count"] == 40),
        ("formula_mapping_intake_count_locked", summary["formula_or_non_numeric_mapping_intake_count"] == 8),
        ("no_active_authoritative_decisions", summary["active_authoritative_decision_count"] == 0),
        ("readiness_items_complete", summary["application_readiness_item_count"] == 48),
        ("no_application_ready_items", summary["application_ready_item_count"] == 0),
        ("all_application_items_blocked", summary["application_blocker_item_count"] == 48),
        ("private_readiness_outputs_ignored", summary["private_application_blocker_queue_gitignored"] is True),
        ("raw_inbox_untouched", summary["raw_boundary"]["raw_inbox_mutated_by_this_phase"] is False),
        ("no_value_comparison_claimed", summary["raw_to_processed_value_comparison_performed_by_this_phase"] is False),
        ("downstream_gates_closed", summary["github_upload_performed"] is False and summary["business_execution_performed"] is False),
    ]
    rows = [{"check_code": code, "status": "PASS" if passed else "FAIL"} for code, passed in checks]
    pass_count = sum(1 for row in rows if row["status"] == "PASS")
    return {
        "schema_version": (
            "kmfa.v014_authorized_source_reference_or_exclusion_application_readiness_after_raw_refresh_matrix_public_safe.v1"
        ),
        "record_type": (
            "v014_authorized_source_reference_or_exclusion_application_readiness_after_raw_refresh_matrix_public_safe"
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
            "kmfa.v014_authorized_source_reference_or_exclusion_application_readiness_after_raw_refresh_go_no_go.v1"
        ),
        "record_type": "v014_authorized_source_reference_or_exclusion_application_readiness_after_raw_refresh_go_no_go",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": summary["generated_at"],
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "application_readiness_item_count": summary["application_readiness_item_count"],
        "application_ready_item_count": summary["application_ready_item_count"],
        "application_blocker_item_count": summary["application_blocker_item_count"],
        "active_authoritative_decision_count": summary["active_authoritative_decision_count"],
        "authoritative_binding_application_ready": False,
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
    ready_rows: list[dict[str, Any]],
    blocker_rows: list[dict[str, Any]],
    summary: dict[str, Any],
) -> dict[str, Any]:
    diagnostic = {
        "schema_version": (
            "kmfa.private.v014_authorized_source_reference_or_exclusion_application_readiness_after_raw_refresh.v1"
        ),
        "classification": "private_authorized_source_reference_or_exclusion_application_readiness_do_not_commit",
        "record_type": "v014_authorized_source_reference_or_exclusion_application_readiness_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "source_phase_id": source_summary.get("phase_id"),
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "application_readiness_item_count": summary["application_readiness_item_count"],
        "application_ready_item_count": len(ready_rows),
        "application_blocker_item_count": len(blocker_rows),
        "counts": {
            "source_reference_or_owner_exclusion_application_blocker_count": summary[
                "source_reference_or_owner_exclusion_application_blocker_count"
            ],
            "formula_or_non_numeric_mapping_application_blocker_count": summary[
                "formula_or_non_numeric_mapping_application_blocker_count"
            ],
            "binding_ready_after_application_readiness_count": summary[
                "binding_ready_after_application_readiness_count"
            ],
            "comparison_retry_ready_after_application_readiness_count": summary[
                "comparison_retry_ready_after_application_readiness_count"
            ],
        },
        "raw_boundary": summary["raw_boundary"],
    }
    _write_json(PRIVATE_DIAGNOSTIC_PATH, diagnostic)
    _write_jsonl(PRIVATE_READY_QUEUE_PATH, ready_rows)
    _write_jsonl(PRIVATE_BLOCKER_QUEUE_PATH, blocker_rows)
    _write_text(
        PRIVATE_REPORT_PATH,
        "\n".join(
            [
                "# Private Authorized Source Reference Or Exclusion Application Readiness After Raw Refresh",
                "",
                f"- phase_id: `{PHASE_ID}`",
                f"- application_readiness_item_count: `{summary['application_readiness_item_count']}`",
                f"- application_ready_item_count: `{len(ready_rows)}`",
                f"- application_blocker_item_count: `{len(blocker_rows)}`",
                "- authoritative_binding_application_ready: `false`",
                "- raw_to_processed_value_comparison_performed_by_this_phase: `false`",
                "",
            ]
        ),
    )
    return diagnostic


def _write_human(summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any]) -> None:
    report = f"""# V014 Authorized Source Reference Or Exclusion Application Readiness After Raw Refresh

Generated at: {summary["generated_at"]}

## Scope

- Phase: `{PHASE_ID}`
- Decision: `{DECISION}`
- Status: `{STATUS}`
- Source: prior public-safe intake evidence plus ignored private intake queue.
- Raw boundary: this phase does not read, list, stat, parse, fingerprint, write, delete, move, rename, copy, normalize or mutate the raw inbox.

## Public-Safe Result

- Source intake items: `{summary["source_intake_item_count"]}`
- Application readiness items: `{summary["application_readiness_item_count"]}`
- Application ready items: `{summary["application_ready_item_count"]}`
- Application blocker items: `{summary["application_blocker_item_count"]}`
- Source reference or owner exclusion blockers: `{summary["source_reference_or_owner_exclusion_application_blocker_count"]}`
- Formula or non-numeric mapping blockers: `{summary["formula_or_non_numeric_mapping_application_blocker_count"]}`
- Active authoritative decisions: `{summary["active_authoritative_decision_count"]}`

## Gate

This phase only checks whether private intake can be applied. No authoritative binding exists, so all 48 readiness items remain blocked. It does not apply source references, owner exclusions, formula mappings, raw candidate fingerprints, raw-to-processed comparison, reconciliation, formal reports, GitHub upload, app reinstall or business execution.

Next required input: `{NEXT_REQUIRED_INPUT}`.
"""
    go_record = f"""# Go / No-Go Record

- Phase: `{PHASE_ID}`
- Decision: `{go_no_go["decision"]}`
- Reason: application readiness is blocked because no authoritative binding record is present.
- Matrix: `{matrix["check_pass_count"]}` pass / `{matrix["check_fail_count"]}` fail
- GitHub upload: not allowed in this phase.
- App reinstall: not allowed in this phase.
"""
    test_results = f"""# Test Results

- RED: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_v014_residual_difference_authorized_source_reference_or_exclusion_application_readiness_after_raw_refresh.py` failed before implementation because the generator module did not exist.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_readiness_after_raw_refresh.py --generated-at 2026-07-08T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_readiness_after_raw_refresh.py --require-private-readiness`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_v014_residual_difference_authorized_source_reference_or_exclusion_application_readiness_after_raw_refresh.py`
- Governance validators, CSV shape checks, diff check, raw/private scan, secret scan and private-runtime tracked-file scan: expected before commit.

Expected matrix result: {matrix["check_pass_count"]}/{matrix["check_count"]} PASS.
"""
    risk_register = """# Risk Register

- Risk: application readiness is mistaken for authoritative binding or discrepancy closure.
- Control: binding, comparison and downstream gate flags remain false.
- Risk: private slot or resolution details leak into public artifacts.
- Control: public artifacts contain aggregate counts only; private details stay ignored.
- Risk: raw inbox is modified.
- Control: this phase does not access raw inbox and preserves raw immutability.
"""
    rollback = f"""# Rollback Plan

Remove artifacts for `{PHASE_ID}`, metadata copies, ignored private readiness outputs, tool, validator, focused test and governance rows. Do not touch raw inbox files or prior private/source artifacts.
"""
    _write_text(REPORT_PATH, report)
    _write_text(GO_NO_GO_RECORD_PATH, go_record)
    _write_text(TEST_RESULTS_PATH, test_results)
    _write_text(RISK_REGISTER_PATH, risk_register)
    _write_text(ROLLBACK_PATH, rollback)


def _build_manifest(summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": (
            "kmfa.v014_authorized_source_reference_or_exclusion_application_readiness_after_raw_refresh_manifest.v1"
        ),
        "record_type": "v014_authorized_source_reference_or_exclusion_application_readiness_after_raw_refresh_manifest",
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
            "intake_summary": "public_safe_metadata_copy",
            "intake_manifest": "public_safe_metadata_copy",
            "intake_go_no_go": "public_safe_metadata_copy",
            "intake_matrix": "public_safe_metadata_copy",
            "intake_private_active_record": "ignored_private_runtime",
            "intake_private_queue": "ignored_private_runtime",
            "intake_private_diagnostic": "ignored_private_runtime",
            "intake_private_report": "ignored_private_runtime",
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
            "private:authorized_source_reference_or_exclusion_application_readiness_diagnostic",
            "private:authorized_source_reference_or_exclusion_application_ready_queue",
            "private:authorized_source_reference_or_exclusion_application_blocker_queue",
            "private:authorized_source_reference_or_exclusion_application_readiness_report",
        ],
        "raw_boundary": summary["raw_boundary"],
        "public_safety": summary["public_safety"],
        "test_commands": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_readiness_after_raw_refresh.py --generated-at 2026-07-08T00:00:00+10:00",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_readiness_after_raw_refresh.py --require-private-readiness",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_v014_residual_difference_authorized_source_reference_or_exclusion_application_readiness_after_raw_refresh.py",
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
            "APPLICATION-READINESS-AFTER-RAW-REFRESH"
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
        "summary": "Checked application readiness for 48 authorized-source-reference intake items; all remain blocked.",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "files_changed": _changed_kmfa_files(),
        "test_commands": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_readiness_after_raw_refresh.py --generated-at 2026-07-08T00:00:00+10:00",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_readiness_after_raw_refresh.py --require-private-readiness",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_v014_residual_difference_authorized_source_reference_or_exclusion_application_readiness_after_raw_refresh.py",
        ],
        "test_results": ["PENDING: final validation results will be recorded before local commit."],
        "next_required_input": NEXT_REQUIRED_INPUT,
        "application_readiness_item_count": summary["application_readiness_item_count"],
        "application_ready_item_count": summary["application_ready_item_count"],
        "application_blocker_item_count": summary["application_blocker_item_count"],
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
            "RESIDUAL_DIFFERENCE_AUTHORIZED_SOURCE_REFERENCE_OR_EXCLUSION_APPLICATION_READINESS_AFTER_RAW_REFRESH"
        ),
        "roadmap_stage_id": "VALUE-CONSISTENCY",
        "governance_stage_id": "VALUE-CONSISTENCY",
        "name": "v0.1.4 residual difference authorized source reference or exclusion application readiness after raw refresh",
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
        ("T1", "read prior intake public evidence and ignored private intake queue"),
        ("T2", "write ignored private application readiness ready and blocker queues"),
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
                "roadmap_phase_id": (
                    "RESIDUAL_DIFFERENCE_AUTHORIZED_SOURCE_REFERENCE_OR_EXCLUSION_"
                    "APPLICATION_READINESS_AFTER_RAW_REFRESH"
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
    source_active_record: dict[str, Any],
    source_intake_rows: list[dict[str, Any]],
) -> None:
    if source_summary.get("phase_id") != source_intake.PHASE_ID:
        raise ValueError("source intake phase mismatch")
    if source_go_no_go.get("decision") != "NO_GO":
        raise ValueError("source intake go/no-go decision must be NO_GO")
    if source_matrix.get("check_fail_count") != 0:
        raise ValueError("source intake matrix must be clean")
    if source_summary.get("intake_item_count") != 48:
        raise ValueError("source intake item count must be 48")
    if source_active_record.get("intake_item_count") != 48:
        raise ValueError("source private active record count must be 48")
    if len(source_intake_rows) != 48:
        raise ValueError("source private intake queue must contain 48 rows")
    counts = Counter(row.get("intake_track") for row in source_intake_rows)
    if dict(counts) != EXPECTED_INTAKE_TRACK_COUNTS:
        raise ValueError(f"source intake track counts must be {EXPECTED_INTAKE_TRACK_COUNTS!r}")
    if source_summary.get("active_authoritative_decision_count") != 0:
        raise ValueError("source active authoritative decision count must be zero")
    if source_summary.get("binding_ready_after_intake_count") != 0:
        raise ValueError("source binding-ready-after-intake count must be zero")
    if source_summary.get("comparison_retry_ready_after_intake_count") != 0:
        raise ValueError("source comparison-retry-ready-after-intake count must be zero")


def generate(*, generated_at: str | None = None, write_governance_event: bool = True) -> dict[str, Any]:
    generated = generated_at or _now()
    source_summary = _read_json(SOURCE_INTAKE_SUMMARY_PATH)
    source_manifest = _read_json(SOURCE_INTAKE_MANIFEST_PATH)
    source_go_no_go = _read_json(SOURCE_INTAKE_GO_NO_GO_PATH)
    source_matrix = _read_json(SOURCE_INTAKE_MATRIX_PATH)
    source_active_record = _read_json(SOURCE_PRIVATE_ACTIVE_RECORD_PATH)
    source_intake_rows = _read_jsonl(SOURCE_PRIVATE_INTAKE_QUEUE_PATH)
    source_private_diagnostic = _read_json(SOURCE_PRIVATE_DIAGNOSTIC_PATH)
    source_private_report = SOURCE_PRIVATE_REPORT_PATH.read_text(encoding="utf-8")
    _validate_sources(
        source_summary=source_summary,
        source_go_no_go=source_go_no_go,
        source_matrix=source_matrix,
        source_active_record=source_active_record,
        source_intake_rows=source_intake_rows,
    )

    ready_rows, blocker_rows = _build_private_readiness_queues(generated_at=generated, intake_rows=source_intake_rows)
    summary = _build_summary(
        generated_at=generated,
        source_summary=source_summary,
        source_manifest=source_manifest,
        source_go_no_go=source_go_no_go,
        source_matrix=source_matrix,
        source_active_record=source_active_record,
        source_intake_rows=source_intake_rows,
        source_private_diagnostic=source_private_diagnostic,
        source_private_report=source_private_report,
        ready_rows=ready_rows,
        blocker_rows=blocker_rows,
    )
    private_diagnostic = _write_private_outputs(
        generated_at=generated,
        source_summary=source_summary,
        ready_rows=ready_rows,
        blocker_rows=blocker_rows,
        summary=summary,
    )
    summary["private_application_readiness_diagnostic_gitignored"] = _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH)
    summary["private_application_ready_queue_gitignored"] = _git_check_ignored(PRIVATE_READY_QUEUE_PATH)
    summary["private_application_blocker_queue_gitignored"] = _git_check_ignored(PRIVATE_BLOCKER_QUEUE_PATH)
    summary["private_application_report_gitignored"] = _git_check_ignored(PRIVATE_REPORT_PATH)
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
        "PASS: generated V014 authorized source reference or exclusion application readiness after raw refresh "
        f"decision={summary['decision']} readiness_items={summary['application_readiness_item_count']} "
        f"ready={summary['application_ready_item_count']} blockers={summary['application_blocker_item_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
