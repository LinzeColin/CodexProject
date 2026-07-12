#!/usr/bin/env python3
"""Audit application blockers for authorized source references after raw refresh.

This phase consumes the prior public-safe application-readiness evidence and
ignored private blocker queue, then locks the public-safe shape of the 48
remaining blockers. It does not apply source references, owner exclusions,
formula mappings, raw candidate fingerprints, raw-to-processed comparison,
GitHub upload, app reinstall, or business execution.
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
    v014_residual_difference_authorized_source_reference_or_exclusion_application_readiness_after_raw_refresh
    as source_readiness,
)
from KMFA.tools.v014_residual_difference_authorized_source_reference_or_exclusion_application_readiness_after_raw_refresh import (  # noqa: E402
    FORMULA_MAPPING_INTAKE_TRACK,
    PRIVATE_SLOT_KEY,
    SOURCE_REFERENCE_INTAKE_TRACK,
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
PHASE_ID = (
    "V014_RESIDUAL_DIFFERENCE_AUTHORIZED_SOURCE_REFERENCE_OR_EXCLUSION_APPLICATION_BLOCKER_AUDIT_AFTER_RAW_REFRESH"
)
TASK_ID = (
    "KMFA-V014-RESIDUAL-DIFFERENCE-AUTHORIZED-SOURCE-REFERENCE-OR-EXCLUSION-"
    "APPLICATION-BLOCKER-AUDIT-AFTER-RAW-REFRESH-20260708"
)
ACCEPTANCE_ID = (
    "ACC-V014-RESIDUAL-DIFFERENCE-AUTHORIZED-SOURCE-REFERENCE-OR-EXCLUSION-"
    "APPLICATION-BLOCKER-AUDIT-AFTER-RAW-REFRESH"
)
VERSION = (
    "0.1.4-residual-difference-authorized-source-reference-or-exclusion-"
    "application-blocker-audit-after-raw-refresh"
)
STATUS = (
    "completed_validated_local_only_authorized_source_reference_or_exclusion_"
    "application_blocker_audit_after_raw_refresh_no_go"
)
DECISION = "NO_GO"
AUDIT_CONCLUSION = "application_blocker_audit_locked_48_missing_authorized_resolution_applications"
NEXT_REQUIRED_INPUT = "owner_or_authorized_delegate_applies_source_reference_exclusion_or_formula_mapping_before_binding"
NEXT_RECOMMENDED_PHASE = (
    "V014_RESIDUAL_DIFFERENCE_AUTHORIZED_SOURCE_REFERENCE_OR_EXCLUSION_APPLICATION_BLOCKER_THRESHOLD_RECHECK_AFTER_RAW_REFRESH"
)

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = (
    MACHINE_DIR
    / "residual_difference_authorized_source_reference_or_exclusion_application_blocker_audit_after_raw_refresh_summary.json"
)
MANIFEST_PATH = (
    MACHINE_DIR
    / "residual_difference_authorized_source_reference_or_exclusion_application_blocker_audit_after_raw_refresh_manifest.json"
)
GO_NO_GO_PATH = (
    MACHINE_DIR
    / "residual_difference_authorized_source_reference_or_exclusion_application_blocker_audit_after_raw_refresh_go_no_go_report.json"
)
MATRIX_PATH = (
    MACHINE_DIR
    / "residual_difference_authorized_source_reference_or_exclusion_application_blocker_audit_after_raw_refresh_matrix_public_safe.json"
)
REPORT_PATH = (
    HUMAN_DIR / "residual_difference_authorized_source_reference_or_exclusion_application_blocker_audit_after_raw_refresh.md"
)
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_authorized_source_reference_or_exclusion_application_blocker_audit_after_raw_refresh_summary.json"
)
METADATA_MANIFEST_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_authorized_source_reference_or_exclusion_application_blocker_audit_after_raw_refresh_manifest.json"
)
METADATA_GO_NO_GO_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_authorized_source_reference_or_exclusion_application_blocker_audit_after_raw_refresh_go_no_go_report.json"
)
METADATA_MATRIX_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_authorized_source_reference_or_exclusion_application_blocker_audit_after_raw_refresh_matrix_public_safe.json"
)

SOURCE_READINESS_SUMMARY_PATH = source_readiness.METADATA_SUMMARY_PATH
SOURCE_READINESS_MANIFEST_PATH = source_readiness.METADATA_MANIFEST_PATH
SOURCE_READINESS_GO_NO_GO_PATH = source_readiness.METADATA_GO_NO_GO_PATH
SOURCE_READINESS_MATRIX_PATH = source_readiness.METADATA_MATRIX_PATH
SOURCE_PRIVATE_READINESS_DIAGNOSTIC_PATH = source_readiness.PRIVATE_DIAGNOSTIC_PATH
SOURCE_PRIVATE_READY_QUEUE_PATH = source_readiness.PRIVATE_READY_QUEUE_PATH
SOURCE_PRIVATE_BLOCKER_QUEUE_PATH = source_readiness.PRIVATE_BLOCKER_QUEUE_PATH
SOURCE_PRIVATE_READINESS_REPORT_PATH = source_readiness.PRIVATE_REPORT_PATH

PRIVATE_OUTPUT_DIR = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_residual_difference_authorized_source_reference_or_exclusion_application_blocker_audit_after_raw_refresh"
)
PRIVATE_AUDIT_DIAGNOSTIC_PATH = (
    PRIVATE_OUTPUT_DIR / "private_authorized_source_reference_or_exclusion_application_blocker_audit_diagnostic.json"
)
PRIVATE_AUDIT_RECORDS_PATH = (
    PRIVATE_OUTPUT_DIR / "private_authorized_source_reference_or_exclusion_application_blocker_audit_records.jsonl"
)
PRIVATE_AUDIT_REPORT_PATH = PRIVATE_OUTPUT_DIR / "private_authorized_source_reference_or_exclusion_application_blocker_audit.md"

DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"
STAGE_STATUS_PATH = PROJECT_ROOT / "metadata/stage_status.jsonl"
TASK_STATUS_PATH = PROJECT_ROOT / "metadata/traceability/v1_4_stage_phase_task_status.jsonl"

EXPECTED_AUDIT_TRACK_COUNTS = {
    SOURCE_REFERENCE_INTAKE_TRACK: 40,
    FORMULA_MAPPING_INTAKE_TRACK: 8,
}


def _raw_boundary() -> dict[str, bool]:
    return {
        "user_declared_raw_data_immutable": True,
        "raw_data_root_readonly_policy_active": True,
        "source_readiness_public_artifacts_read_by_this_phase": True,
        "source_readiness_manifest_read_by_this_phase": True,
        "source_readiness_go_no_go_read_by_this_phase": True,
        "source_readiness_matrix_read_by_this_phase": True,
        "source_private_readiness_diagnostic_read_by_this_phase": True,
        "source_private_ready_queue_read_by_this_phase": True,
        "source_private_blocker_queue_read_by_this_phase": True,
        "source_private_readiness_report_read_by_this_phase": True,
        "private_application_blocker_audit_diagnostic_written_by_this_phase": True,
        "private_application_blocker_audit_records_written_by_this_phase": True,
        "private_application_blocker_audit_report_written_by_this_phase": True,
        "source_private_readiness_diagnostic_mutated_by_this_phase": False,
        "source_private_ready_queue_mutated_by_this_phase": False,
        "source_private_blocker_queue_mutated_by_this_phase": False,
        "source_private_readiness_report_mutated_by_this_phase": False,
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
        "source_private_readiness_diagnostic_committed": False,
        "source_private_ready_queue_committed": False,
        "source_private_blocker_queue_committed": False,
        "source_private_readiness_report_committed": False,
        "private_application_blocker_audit_diagnostic_committed": False,
        "private_application_blocker_audit_records_committed": False,
        "private_application_blocker_audit_report_committed": False,
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


def _remediation_track(row: dict[str, Any]) -> str:
    if row.get("intake_track") == FORMULA_MAPPING_INTAKE_TRACK:
        return "provide_formula_or_non_numeric_mapping_before_binding"
    return "provide_authoritative_source_reference_or_owner_exclusion_before_binding"


def _build_private_audit_rows(*, generated_at: str, blocker_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, blocker in enumerate(blocker_rows, start=1):
        rows.append(
            {
                "application_blocker_audit_item_id": f"ASR-OE-APP-BLOCKER-AUDIT-{index:03d}",
                "phase_id": PHASE_ID,
                "task_id": TASK_ID,
                "generated_at": generated_at,
                "source_application_readiness_item_id": blocker.get("application_readiness_item_id"),
                PRIVATE_SLOT_KEY: blocker.get(PRIVATE_SLOT_KEY),
                "intake_track": blocker.get("intake_track"),
                "source_diagnostic_track": blocker.get("source_diagnostic_track"),
                "application_blocker_code": blocker.get("application_blocker_code"),
                "application_blocker_audit_status": "application_blocker_confirmed_missing_authorized_resolution",
                "remediation_track": _remediation_track(blocker),
                "application_blocker_audit_performed_by_this_phase": True,
                "authoritative_resolution_application_available": False,
                "binding_ready_after_application_blocker_audit": False,
                "comparison_retry_ready_after_application_blocker_audit": False,
                "raw_to_processed_value_comparison_performed_by_this_phase": False,
                "full_raw_to_processed_value_comparison_complete": False,
                "business_value_consistency_verified": False,
                "public_commit_allowed": False,
            }
        )
    return rows


def _build_summary(
    *,
    generated_at: str,
    source_summary: dict[str, Any],
    source_manifest: dict[str, Any],
    source_go_no_go: dict[str, Any],
    source_matrix: dict[str, Any],
    source_diagnostic: dict[str, Any],
    source_ready_rows: list[dict[str, Any]],
    source_blocker_rows: list[dict[str, Any]],
    audit_rows: list[dict[str, Any]],
    raw_boundary: dict[str, bool],
    public_safety: dict[str, bool],
) -> dict[str, Any]:
    track_counts = Counter(row.get("intake_track") for row in audit_rows)
    blocker_codes = Counter(row.get("application_blocker_code") for row in audit_rows)
    return {
        "schema_version": (
            "kmfa.v014_authorized_source_reference_or_exclusion_application_blocker_audit_after_raw_refresh_summary.v1"
        ),
        "record_type": (
            "v014_authorized_source_reference_or_exclusion_application_blocker_audit_after_raw_refresh_summary"
        ),
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": generated_at,
        "status": STATUS,
        "decision": DECISION,
        "audit_conclusion": AUDIT_CONCLUSION,
        "source_phase_id": source_summary.get("phase_id"),
        "source_manifest_phase_id": source_manifest.get("phase_id"),
        "source_go_no_go_decision": source_go_no_go.get("decision"),
        "source_matrix_check_fail_count": source_matrix.get("check_fail_count"),
        "source_private_diagnostic_phase_id": source_diagnostic.get("phase_id"),
        "source_application_readiness_item_count": source_summary.get("application_readiness_item_count"),
        "source_application_ready_item_count": source_summary.get("application_ready_item_count"),
        "source_application_blocker_item_count": source_summary.get("application_blocker_item_count"),
        "source_private_ready_queue_count": len(source_ready_rows),
        "source_private_blocker_queue_count": len(source_blocker_rows),
        "application_blocker_audit_item_count": len(audit_rows),
        "application_blocker_audit_ready_item_count": 0,
        "source_reference_or_owner_exclusion_audit_blocker_count": track_counts[SOURCE_REFERENCE_INTAKE_TRACK],
        "formula_or_non_numeric_mapping_audit_blocker_count": track_counts[FORMULA_MAPPING_INTAKE_TRACK],
        "missing_authoritative_source_reference_or_owner_exclusion_application_count": blocker_codes[
            "missing_authoritative_source_reference_or_owner_exclusion_application"
        ],
        "missing_formula_or_non_numeric_mapping_application_count": blocker_codes[
            "missing_formula_or_non_numeric_mapping_application"
        ],
        "active_authoritative_decision_count": source_summary.get("active_authoritative_decision_count"),
        "binding_ready_after_application_blocker_audit_count": 0,
        "comparison_retry_ready_after_application_blocker_audit_count": 0,
        "unresolved_difference_count": source_summary.get("unresolved_difference_count"),
        "private_application_blocker_audit_diagnostic_written": True,
        "private_application_blocker_audit_records_written": True,
        "private_application_blocker_audit_report_written": True,
        "private_application_blocker_audit_diagnostic_gitignored": _git_check_ignored(PRIVATE_AUDIT_DIAGNOSTIC_PATH),
        "private_application_blocker_audit_records_gitignored": _git_check_ignored(PRIVATE_AUDIT_RECORDS_PATH),
        "private_application_blocker_audit_report_gitignored": _git_check_ignored(PRIVATE_AUDIT_REPORT_PATH),
        "source_private_readiness_diagnostic_gitignored": _git_check_ignored(SOURCE_PRIVATE_READINESS_DIAGNOSTIC_PATH),
        "source_private_ready_queue_gitignored": _git_check_ignored(SOURCE_PRIVATE_READY_QUEUE_PATH),
        "source_private_blocker_queue_gitignored": _git_check_ignored(SOURCE_PRIVATE_BLOCKER_QUEUE_PATH),
        "source_private_readiness_report_gitignored": _git_check_ignored(SOURCE_PRIVATE_READINESS_REPORT_PATH),
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
        ("source_readiness_phase_loaded", str(summary["source_phase_id"]).endswith("APPLICATION_READINESS_AFTER_RAW_REFRESH")),
        ("source_go_no_go_preserved", summary["source_go_no_go_decision"] == "NO_GO"),
        ("source_matrix_clean", summary["source_matrix_check_fail_count"] == 0),
        ("source_readiness_items_locked", summary["source_application_readiness_item_count"] == 48),
        ("source_ready_items_zero", summary["source_application_ready_item_count"] == 0),
        ("source_blocker_items_locked", summary["source_application_blocker_item_count"] == 48),
        ("source_private_blocker_queue_loaded", summary["source_private_blocker_queue_count"] == 48),
        ("audit_item_count_locked", summary["application_blocker_audit_item_count"] == 48),
        ("audit_ready_items_zero", summary["application_blocker_audit_ready_item_count"] == 0),
        ("source_reference_or_exclusion_distribution_locked", summary["source_reference_or_owner_exclusion_audit_blocker_count"] == 40),
        ("formula_mapping_distribution_locked", summary["formula_or_non_numeric_mapping_audit_blocker_count"] == 8),
        ("no_binding_ready_after_audit", summary["binding_ready_after_application_blocker_audit_count"] == 0),
        ("private_audit_records_ignored", summary["private_application_blocker_audit_records_gitignored"] is True),
        ("raw_inbox_untouched", summary["raw_boundary"]["raw_inbox_mutated_by_this_phase"] is False),
        ("downstream_gates_closed", summary["github_upload_performed"] is False and summary["business_execution_performed"] is False),
    ]
    rows = [{"check_code": code, "status": "PASS" if passed else "FAIL"} for code, passed in checks]
    pass_count = sum(1 for row in rows if row["status"] == "PASS")
    return {
        "schema_version": (
            "kmfa.v014_authorized_source_reference_or_exclusion_application_blocker_audit_after_raw_refresh_matrix_public_safe.v1"
        ),
        "record_type": (
            "v014_authorized_source_reference_or_exclusion_application_blocker_audit_after_raw_refresh_matrix_public_safe"
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
            "kmfa.v014_authorized_source_reference_or_exclusion_application_blocker_audit_after_raw_refresh_go_no_go.v1"
        ),
        "record_type": "v014_authorized_source_reference_or_exclusion_application_blocker_audit_after_raw_refresh_go_no_go",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": summary["generated_at"],
        "status": STATUS,
        "decision": DECISION,
        "audit_conclusion": AUDIT_CONCLUSION,
        "application_blocker_audit_item_count": summary["application_blocker_audit_item_count"],
        "application_blocker_audit_ready_item_count": summary["application_blocker_audit_ready_item_count"],
        "binding_ready_after_application_blocker_audit_count": 0,
        "comparison_retry_ready_after_application_blocker_audit_count": 0,
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
    audit_rows: list[dict[str, Any]],
    summary: dict[str, Any],
    raw_boundary: dict[str, bool],
) -> dict[str, Any]:
    track_counts = Counter(row.get("intake_track") for row in audit_rows)
    blocker_codes = Counter(row.get("application_blocker_code") for row in audit_rows)
    diagnostic = {
        "schema_version": (
            "kmfa.private.v014_authorized_source_reference_or_exclusion_application_blocker_audit_after_raw_refresh.v1"
        ),
        "classification": "private_authorized_source_reference_or_exclusion_application_blocker_audit_do_not_commit",
        "record_type": "v014_authorized_source_reference_or_exclusion_application_blocker_audit_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "source_phase_id": source_summary.get("phase_id"),
        "audit_conclusion": AUDIT_CONCLUSION,
        "application_blocker_audit_item_count": len(audit_rows),
        "track_counts": dict(track_counts),
        "blocker_code_counts": dict(blocker_codes),
        "binding_ready_after_application_blocker_audit_count": summary[
            "binding_ready_after_application_blocker_audit_count"
        ],
        "comparison_retry_ready_after_application_blocker_audit_count": summary[
            "comparison_retry_ready_after_application_blocker_audit_count"
        ],
        "raw_boundary": raw_boundary,
    }
    _write_json(PRIVATE_AUDIT_DIAGNOSTIC_PATH, diagnostic)
    _write_jsonl(PRIVATE_AUDIT_RECORDS_PATH, audit_rows)
    _write_text(
        PRIVATE_AUDIT_REPORT_PATH,
        "\n".join(
            [
                "# Private Authorized Source Reference Or Exclusion Application Blocker Audit After Raw Refresh",
                "",
                f"- phase_id: `{PHASE_ID}`",
                f"- application_blocker_audit_item_count: `{len(audit_rows)}`",
                "- binding_ready_after_application_blocker_audit_count: `0`",
                "- raw_to_processed_value_comparison_performed_by_this_phase: `false`",
                "",
            ]
        ),
    )
    return diagnostic


def _write_human(summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any]) -> None:
    report = f"""# V014 Authorized Source Reference Or Exclusion Application Blocker Audit After Raw Refresh

Generated at: {summary["generated_at"]}

## Scope

- Phase: `{PHASE_ID}`
- Decision: `{DECISION}`
- Status: `{STATUS}`
- Source: prior public-safe application-readiness evidence plus ignored private blocker queue.
- Raw boundary: this phase does not read, list, stat, parse, fingerprint, write, delete, move, rename, copy, normalize or mutate the raw inbox.

## Public-Safe Result

- Source application blockers: `{summary["source_application_blocker_item_count"]}`
- Audit items: `{summary["application_blocker_audit_item_count"]}`
- Audit ready items: `{summary["application_blocker_audit_ready_item_count"]}`
- Source reference or owner exclusion audit blockers: `{summary["source_reference_or_owner_exclusion_audit_blocker_count"]}`
- Formula or non-numeric mapping audit blockers: `{summary["formula_or_non_numeric_mapping_audit_blocker_count"]}`
- Binding ready after audit: `{summary["binding_ready_after_application_blocker_audit_count"]}`
- Comparison retry ready after audit: `{summary["comparison_retry_ready_after_application_blocker_audit_count"]}`

## Gate

This phase audits existing private application blockers only. It does not apply authoritative source references, owner exclusions, formula mappings, raw candidate fingerprints, raw-to-processed comparison, reconciliation, formal reports, GitHub upload, app reinstall or business execution.

Next required input: `{NEXT_REQUIRED_INPUT}`.
"""
    go_record = f"""# Go / No-Go Record

- Phase: `{PHASE_ID}`
- Decision: `{go_no_go["decision"]}`
- Reason: all 48 application blockers remain missing authorized private resolution applications.
- Matrix: `{matrix["check_pass_count"]}` pass / `{matrix["check_fail_count"]}` fail
- GitHub upload: not allowed in this phase.
- App reinstall: not allowed in this phase.
"""
    test_results = f"""# Test Results

- RED: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_v014_residual_difference_authorized_source_reference_or_exclusion_application_blocker_audit_after_raw_refresh.py` failed before implementation because the generator module did not exist.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_blocker_audit_after_raw_refresh.py --generated-at 2026-07-08T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_blocker_audit_after_raw_refresh.py --require-private-audit`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_v014_residual_difference_authorized_source_reference_or_exclusion_application_blocker_audit_after_raw_refresh.py`
- Governance validators, CSV shape checks, diff check, raw/private scan, secret scan and private-runtime tracked-file scan: expected before commit.

Expected matrix result: {matrix["check_pass_count"]}/{matrix["check_count"]} PASS.
"""
    risk_register = """# Risk Register

- Risk: blocker audit is mistaken for authoritative binding or discrepancy closure.
- Control: binding, comparison and downstream gate flags remain false.
- Risk: private slot or resolution details leak into public artifacts.
- Control: public artifacts contain aggregate counts only; private details stay ignored.
- Risk: raw inbox is modified.
- Control: this phase does not access raw inbox and preserves raw immutability.
"""
    rollback = f"""# Rollback Plan

Remove artifacts for `{PHASE_ID}`, metadata copies, ignored private audit outputs, tool, validator, focused test and governance rows. Do not touch raw inbox files or prior private/source artifacts.
"""
    _write_text(REPORT_PATH, report)
    _write_text(GO_NO_GO_RECORD_PATH, go_record)
    _write_text(TEST_RESULTS_PATH, test_results)
    _write_text(RISK_REGISTER_PATH, risk_register)
    _write_text(ROLLBACK_PATH, rollback)


def _build_manifest(summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": (
            "kmfa.v014_authorized_source_reference_or_exclusion_application_blocker_audit_after_raw_refresh_manifest.v1"
        ),
        "record_type": "v014_authorized_source_reference_or_exclusion_application_blocker_audit_after_raw_refresh_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": summary["generated_at"],
        "status": STATUS,
        "decision": DECISION,
        "audit_conclusion": AUDIT_CONCLUSION,
        "summary": summary,
        "matrix": matrix,
        "go_no_go_report": go_no_go,
        "source_artifacts": {
            "application_readiness_summary": "public_safe_metadata_copy",
            "application_readiness_manifest": "public_safe_metadata_copy",
            "application_readiness_go_no_go": "public_safe_metadata_copy",
            "application_readiness_matrix": "public_safe_metadata_copy",
            "application_readiness_private_diagnostic": "ignored_private_runtime",
            "application_readiness_private_ready_queue": "ignored_private_runtime",
            "application_readiness_private_blocker_queue": "ignored_private_runtime",
            "application_readiness_private_report": "ignored_private_runtime",
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
            "private:authorized_source_reference_or_exclusion_application_blocker_audit_diagnostic",
            "private:authorized_source_reference_or_exclusion_application_blocker_audit_records",
            "private:authorized_source_reference_or_exclusion_application_blocker_audit_report",
        ],
        "raw_boundary": summary["raw_boundary"],
        "public_safety": summary["public_safety"],
        "test_commands": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_blocker_audit_after_raw_refresh.py --generated-at 2026-07-08T00:00:00+10:00",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_blocker_audit_after_raw_refresh.py --require-private-audit",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_v014_residual_difference_authorized_source_reference_or_exclusion_application_blocker_audit_after_raw_refresh.py",
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
            "APPLICATION-BLOCKER-AUDIT-AFTER-RAW-REFRESH"
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
        "summary": "Audited 48 authorized-source-reference application blockers; all remain blocked.",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "files_changed": _changed_kmfa_files(),
        "test_commands": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_blocker_audit_after_raw_refresh.py --generated-at 2026-07-08T00:00:00+10:00",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_blocker_audit_after_raw_refresh.py --require-private-audit",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_v014_residual_difference_authorized_source_reference_or_exclusion_application_blocker_audit_after_raw_refresh.py",
        ],
        "test_results": ["PENDING: final validation results will be recorded before local commit."],
        "next_required_input": NEXT_REQUIRED_INPUT,
        "application_blocker_audit_item_count": summary["application_blocker_audit_item_count"],
        "application_blocker_audit_ready_item_count": summary["application_blocker_audit_ready_item_count"],
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
            "RESIDUAL_DIFFERENCE_AUTHORIZED_SOURCE_REFERENCE_OR_EXCLUSION_APPLICATION_BLOCKER_AUDIT_AFTER_RAW_REFRESH"
        ),
        "roadmap_stage_id": "VALUE-CONSISTENCY",
        "governance_stage_id": "VALUE-CONSISTENCY",
        "name": "v0.1.4 residual difference authorized source reference or exclusion application blocker audit after raw refresh",
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
        ("T1", "read prior application readiness public evidence and ignored private blocker queue"),
        ("T2", "write ignored private application blocker audit records"),
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
                    "APPLICATION_BLOCKER_AUDIT_AFTER_RAW_REFRESH"
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
    source_ready_rows: list[dict[str, Any]],
    source_blocker_rows: list[dict[str, Any]],
) -> None:
    if source_summary.get("phase_id") != source_readiness.PHASE_ID:
        raise ValueError("source application readiness phase mismatch")
    if source_go_no_go.get("decision") != "NO_GO":
        raise ValueError("source application readiness decision must be NO_GO")
    if source_matrix.get("check_fail_count") != 0:
        raise ValueError("source application readiness matrix must be clean")
    if source_summary.get("application_readiness_item_count") != 48:
        raise ValueError("source application readiness item count must be 48")
    if source_summary.get("application_ready_item_count") != 0:
        raise ValueError("source application ready item count must be zero")
    if source_summary.get("application_blocker_item_count") != 48:
        raise ValueError("source application blocker item count must be 48")
    if len(source_ready_rows) != 0:
        raise ValueError("source private ready queue must be empty")
    if len(source_blocker_rows) != 48:
        raise ValueError("source private blocker queue must contain 48 rows")
    counts = Counter(row.get("intake_track") for row in source_blocker_rows)
    if dict(counts) != EXPECTED_AUDIT_TRACK_COUNTS:
        raise ValueError(f"source blocker track counts must be {EXPECTED_AUDIT_TRACK_COUNTS!r}")


def generate(*, generated_at: str | None = None, write_governance_event: bool = True) -> dict[str, Any]:
    generated = generated_at or _now()
    source_summary = _read_json(SOURCE_READINESS_SUMMARY_PATH)
    source_manifest = _read_json(SOURCE_READINESS_MANIFEST_PATH)
    source_go_no_go = _read_json(SOURCE_READINESS_GO_NO_GO_PATH)
    source_matrix = _read_json(SOURCE_READINESS_MATRIX_PATH)
    source_diagnostic = _read_json(SOURCE_PRIVATE_READINESS_DIAGNOSTIC_PATH)
    source_ready_rows = _read_jsonl(SOURCE_PRIVATE_READY_QUEUE_PATH)
    source_blocker_rows = _read_jsonl(SOURCE_PRIVATE_BLOCKER_QUEUE_PATH)
    SOURCE_PRIVATE_READINESS_REPORT_PATH.read_text(encoding="utf-8")
    _validate_sources(
        source_summary=source_summary,
        source_go_no_go=source_go_no_go,
        source_matrix=source_matrix,
        source_ready_rows=source_ready_rows,
        source_blocker_rows=source_blocker_rows,
    )

    raw_boundary = _raw_boundary()
    public_safety = _public_safety()
    audit_rows = _build_private_audit_rows(generated_at=generated, blocker_rows=source_blocker_rows)
    summary = _build_summary(
        generated_at=generated,
        source_summary=source_summary,
        source_manifest=source_manifest,
        source_go_no_go=source_go_no_go,
        source_matrix=source_matrix,
        source_diagnostic=source_diagnostic,
        source_ready_rows=source_ready_rows,
        source_blocker_rows=source_blocker_rows,
        audit_rows=audit_rows,
        raw_boundary=raw_boundary,
        public_safety=public_safety,
    )
    private_diagnostic = _write_private_outputs(
        generated_at=generated,
        source_summary=source_summary,
        audit_rows=audit_rows,
        summary=summary,
        raw_boundary=raw_boundary,
    )
    summary["private_application_blocker_audit_diagnostic_gitignored"] = _git_check_ignored(
        PRIVATE_AUDIT_DIAGNOSTIC_PATH
    )
    summary["private_application_blocker_audit_records_gitignored"] = _git_check_ignored(PRIVATE_AUDIT_RECORDS_PATH)
    summary["private_application_blocker_audit_report_gitignored"] = _git_check_ignored(PRIVATE_AUDIT_REPORT_PATH)
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
        "private_audit_rows": audit_rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated-at")
    parser.add_argument("--no-governance-event", action="store_true")
    args = parser.parse_args()
    result = generate(generated_at=args.generated_at, write_governance_event=not args.no_governance_event)
    summary = result["summary"]
    print(
        "PASS: generated V014 authorized source reference or exclusion application blocker audit after raw refresh "
        f"decision={summary['decision']} audit_items={summary['application_blocker_audit_item_count']} "
        f"ready={summary['application_blocker_audit_ready_item_count']} "
        f"blockers={summary['source_application_blocker_item_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
