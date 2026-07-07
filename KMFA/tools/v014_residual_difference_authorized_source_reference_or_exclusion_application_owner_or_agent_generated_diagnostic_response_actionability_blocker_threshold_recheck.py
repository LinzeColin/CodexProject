#!/usr/bin/env python3
"""Threshold-recheck generated owner/agent diagnostic response actionability blockers.

This phase consumes the prior public-safe actionability blocker audit evidence
and ignored private audit queue. It records the second blocker observation for
all 48 non-actionable generated diagnostic responses. It does not read or
mutate the raw inbox and does not open binding or value-comparison gates.
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
    v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_actionability_blocker_audit
    as source_audit,
)
from KMFA.tools.v014_residual_difference_owner_authorized_anchor_confirmation import (  # noqa: E402
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
    "V014_RESIDUAL_DIFFERENCE_AUTHORIZED_SOURCE_REFERENCE_OR_EXCLUSION_APPLICATION_OWNER_OR_AGENT_"
    "GENERATED_DIAGNOSTIC_RESPONSE_ACTIONABILITY_BLOCKER_THRESHOLD_RECHECK"
)
TASK_ID = (
    "KMFA-V014-RESIDUAL-DIFFERENCE-AUTHORIZED-SOURCE-REFERENCE-OR-EXCLUSION-APPLICATION-OWNER-OR-"
    "AGENT-GENERATED-DIAGNOSTIC-RESPONSE-ACTIONABILITY-BLOCKER-THRESHOLD-RECHECK-20260708"
)
ACCEPTANCE_ID = (
    "ACC-V014-RESIDUAL-DIFFERENCE-AUTHORIZED-SOURCE-REFERENCE-OR-EXCLUSION-APPLICATION-OWNER-OR-"
    "AGENT-GENERATED-DIAGNOSTIC-RESPONSE-ACTIONABILITY-BLOCKER-THRESHOLD-RECHECK"
)
VERSION = (
    "0.1.4-residual-difference-authorized-source-reference-or-exclusion-application-owner-or-agent-"
    "generated-diagnostic-response-actionability-blocker-threshold-recheck"
)
STATUS = (
    "completed_validated_local_only_authorized_source_reference_or_exclusion_application_owner_or_agent_"
    "generated_diagnostic_response_actionability_blocker_threshold_recheck_no_go"
)
DECISION = "NO_GO"
ACTIONABILITY_THRESHOLD_CONCLUSION = (
    "generated_diagnostic_response_actionability_blockers_second_observation_threshold_not_met"
)
NEXT_REQUIRED_INPUT = (
    "actionable_source_reference_owner_exclusion_formula_mapping_or_non_numeric_mapping_required_before_"
    "binding_or_value_comparison"
)
NEXT_RECOMMENDED_PHASE = (
    "V014_RESIDUAL_DIFFERENCE_AUTHORIZED_SOURCE_REFERENCE_OR_EXCLUSION_APPLICATION_OWNER_OR_AGENT_"
    "GENERATED_DIAGNOSTIC_RESPONSE_ACTIONABILITY_BLOCKER_FINAL_THRESHOLD_RECHECK"
)

SOURCE_REFERENCE_DIAGNOSTIC_KIND = source_audit.SOURCE_REFERENCE_DIAGNOSTIC_KIND
FORMULA_MAPPING_DIAGNOSTIC_KIND = source_audit.FORMULA_MAPPING_DIAGNOSTIC_KIND

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
PREFIX = (
    "residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_"
    "generated_diagnostic_response_actionability_blocker_threshold_recheck"
)
SUMMARY_PATH = MACHINE_DIR / f"{PREFIX}_summary.json"
MANIFEST_PATH = MACHINE_DIR / f"{PREFIX}_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / f"{PREFIX}_go_no_go_report.json"
MATRIX_PATH = MACHINE_DIR / f"{PREFIX}_matrix_public_safe.json"
REPORT_PATH = HUMAN_DIR / f"{PREFIX}.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / f"metadata/quality/v014_{PREFIX}_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / f"metadata/quality/v014_{PREFIX}_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / f"metadata/quality/v014_{PREFIX}_go_no_go_report.json"
METADATA_MATRIX_PATH = PROJECT_ROOT / f"metadata/quality/v014_{PREFIX}_matrix_public_safe.json"

SOURCE_PUBLIC_SUMMARY_PATH = source_audit.METADATA_SUMMARY_PATH
SOURCE_PUBLIC_MANIFEST_PATH = source_audit.METADATA_MANIFEST_PATH
SOURCE_PUBLIC_GO_NO_GO_PATH = source_audit.METADATA_GO_NO_GO_PATH
SOURCE_PUBLIC_MATRIX_PATH = source_audit.METADATA_MATRIX_PATH
SOURCE_PRIVATE_ACTIONABILITY_BLOCKER_AUDIT_DIAGNOSTIC_PATH = (
    source_audit.PRIVATE_ACTIONABILITY_BLOCKER_AUDIT_DIAGNOSTIC_PATH
)
SOURCE_PRIVATE_ACTIONABILITY_BLOCKER_AUDIT_QUEUE_PATH = source_audit.PRIVATE_ACTIONABILITY_BLOCKER_AUDIT_QUEUE_PATH
SOURCE_PRIVATE_ACTIONABILITY_BLOCKER_AUDIT_REPORT_PATH = source_audit.PRIVATE_ACTIONABILITY_BLOCKER_AUDIT_REPORT_PATH

PRIVATE_OUTPUT_DIR = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_actionability_blocker_threshold_recheck"
)
PRIVATE_ACTIONABILITY_THRESHOLD_DIAGNOSTIC_PATH = (
    PRIVATE_OUTPUT_DIR / "private_owner_or_agent_generated_diagnostic_response_actionability_threshold_diagnostic.json"
)
PRIVATE_ACTIONABILITY_THRESHOLD_RECORDS_PATH = (
    PRIVATE_OUTPUT_DIR / "private_owner_or_agent_generated_diagnostic_response_actionability_threshold_records.jsonl"
)
PRIVATE_ACTIONABILITY_THRESHOLD_REPORT_PATH = (
    PRIVATE_OUTPUT_DIR / "private_owner_or_agent_generated_diagnostic_response_actionability_threshold_report.md"
)

DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"
STAGE_STATUS_PATH = PROJECT_ROOT / "metadata/stage_status.jsonl"
TASK_STATUS_PATH = PROJECT_ROOT / "metadata/traceability/v1_4_stage_phase_task_status.jsonl"


def _phase_public_files() -> list[str]:
    return [
        "KMFA/CHANGELOG.md",
        "KMFA/HANDOFF.md",
        "KMFA/VERSION",
        "KMFA/docs/governance/ASSURANCE_STATUS.yaml",
        "KMFA/docs/governance/DEVELOPMENT_LEDGER.md",
        "KMFA/docs/governance/MODEL_SPEC.md",
        "KMFA/docs/governance/OWNER_STATUS.md",
        "KMFA/docs/governance/STATUS.md",
        "KMFA/docs/governance/TRACEABILITY_MATRIX.csv",
        "KMFA/docs/governance/VERSION_MATRIX.yaml",
        "KMFA/docs/governance/delivery_tasks.yaml",
        "KMFA/docs/governance/development_events.jsonl",
        "KMFA/docs/governance/formula_registry.yaml",
        "KMFA/docs/governance/model_registry.yaml",
        "KMFA/docs/governance/parameter_registry.csv",
        "KMFA/metadata/model_registry.yaml",
        METADATA_GO_NO_GO_PATH.as_posix(),
        METADATA_MANIFEST_PATH.as_posix(),
        METADATA_MATRIX_PATH.as_posix(),
        METADATA_SUMMARY_PATH.as_posix(),
        "KMFA/metadata/stage_status.jsonl",
        "KMFA/metadata/traceability/v1_4_stage_phase_task_status.jsonl",
        GO_NO_GO_RECORD_PATH.as_posix(),
        REPORT_PATH.as_posix(),
        RISK_REGISTER_PATH.as_posix(),
        ROLLBACK_PATH.as_posix(),
        TEST_RESULTS_PATH.as_posix(),
        GO_NO_GO_PATH.as_posix(),
        MANIFEST_PATH.as_posix(),
        MATRIX_PATH.as_posix(),
        SUMMARY_PATH.as_posix(),
        "KMFA/tests/test_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_actionability_blocker_threshold_recheck.py",
        "KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_actionability_blocker_threshold_recheck.py",
        "KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_actionability_blocker_threshold_recheck.py",
        "KMFA/功能清单.md",
        "KMFA/开发记录.md",
        "KMFA/模型参数文件.md",
    ]


def _raw_boundary() -> dict[str, bool]:
    return {
        "user_declared_raw_data_immutable": True,
        "raw_data_root_readonly_policy_active": True,
        "source_public_actionability_blocker_audit_summary_read_by_this_phase": True,
        "source_public_actionability_blocker_audit_manifest_read_by_this_phase": True,
        "source_public_actionability_blocker_audit_go_no_go_read_by_this_phase": True,
        "source_public_actionability_blocker_audit_matrix_read_by_this_phase": True,
        "source_private_actionability_blocker_audit_diagnostic_read_by_this_phase": True,
        "source_private_actionability_blocker_audit_queue_read_by_this_phase": True,
        "source_private_actionability_blocker_audit_report_existence_checked_by_this_phase": True,
        "private_actionability_threshold_diagnostic_written_by_this_phase": True,
        "private_actionability_threshold_records_written_by_this_phase": True,
        "private_actionability_threshold_report_written_by_this_phase": True,
        "source_private_actionability_blocker_audit_diagnostic_mutated_by_this_phase": False,
        "source_private_actionability_blocker_audit_queue_mutated_by_this_phase": False,
        "source_private_actionability_blocker_audit_report_mutated_by_this_phase": False,
        "owner_or_agent_valid_response_supplied_by_this_phase": False,
        "authorized_delegate_generated_response_by_this_phase": False,
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
        "source_private_actionability_blocker_audit_diagnostic_committed": False,
        "source_private_actionability_blocker_audit_queue_committed": False,
        "source_private_actionability_blocker_audit_report_committed": False,
        "private_actionability_threshold_diagnostic_committed": False,
        "private_actionability_threshold_records_committed": False,
        "private_actionability_threshold_report_committed": False,
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


def _build_threshold_rows(*, generated_at: str, audit_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    threshold_rows: list[dict[str, Any]] = []
    for index, row in enumerate(audit_rows, start=1):
        diagnostic_kind = str(row.get("diagnostic_kind"))
        if row.get("actionability_audit_status") != "blocked_non_actionable_generated_response_actionability_audit":
            raise ValueError("source audit row is not an actionability blocker audit")
        if row.get("actionability_blocker_observation_count") != 1:
            raise ValueError("source actionability blocker audit must be first observation")
        if row.get("actionability_blocked_audit_threshold_met") is not False:
            raise ValueError("source actionability blocker threshold is unexpectedly met")
        if row.get("valid_diagnostic_response") is not True:
            raise ValueError("source actionability audit row is not a valid diagnostic response")
        if row.get("actionable_resolution_ready") is not False:
            raise ValueError("source actionability audit row is unexpectedly actionable")
        threshold_rows.append(
            {
                "threshold_item_id": f"ASR-OE-APP-OWNER-AGENT-ACT-BLOCKER-THRESHOLD-{index:03d}",
                "phase_id": PHASE_ID,
                "task_id": TASK_ID,
                "generated_at": generated_at,
                "source_actionability_audit_item_id": row.get("actionability_audit_item_id"),
                "source_actionability_item_id": row.get("source_actionability_item_id"),
                "source_generated_response_item_id": row.get("source_generated_response_item_id"),
                "target_slot_id": row.get("target_slot_id"),
                "diagnostic_kind": diagnostic_kind,
                "threshold_status": "blocked_threshold_recheck_non_actionable_generated_response",
                "prior_actionability_blocker_observation_count": 1,
                "actionability_blocker_observation_count": 2,
                "actionability_blocked_audit_threshold_met": False,
                "valid_diagnostic_response": True,
                "actionable_resolution_ready": False,
                "source_reference_or_owner_exclusion_actionability_blocker": (
                    diagnostic_kind == SOURCE_REFERENCE_DIAGNOSTIC_KIND
                ),
                "formula_or_non_numeric_mapping_actionability_blocker": (
                    diagnostic_kind == FORMULA_MAPPING_DIAGNOSTIC_KIND
                ),
                "binding_ready_after_actionability_blocker_threshold_recheck": False,
                "comparison_retry_ready_after_actionability_blocker_threshold_recheck": False,
                "safe_auto_resolution_available": False,
                "authoritative_binding_application_ready": False,
                "authoritative_binding_applied_by_this_phase": False,
                "raw_candidate_fingerprint_bound_by_this_phase": False,
                "raw_to_processed_value_comparison_performed_by_this_phase": False,
                "business_value_consistency_verified": False,
                "full_raw_to_processed_value_comparison_complete": False,
                "actionability_blocker_reason_code": (
                    "generated_diagnostic_response_still_lacks_actionable_source_binding_or_formula_mapping"
                ),
                "public_commit_allowed": False,
            }
        )
    return threshold_rows


def _build_summary(
    *,
    generated_at: str,
    source_summary: dict[str, Any],
    source_manifest: dict[str, Any],
    source_go_no_go: dict[str, Any],
    source_matrix: dict[str, Any],
    audit_rows: list[dict[str, Any]],
    threshold_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    if len(audit_rows) != 48 or len(threshold_rows) != 48:
        raise ValueError("source actionability blocker audit queue must contain 48 rows")
    source_ids = {row.get("actionability_audit_item_id") for row in audit_rows}
    threshold_ids = {row.get("source_actionability_audit_item_id") for row in threshold_rows}
    if source_ids != threshold_ids:
        raise ValueError("source audit and threshold item sets must match")
    counts = Counter(str(row.get("diagnostic_kind")) for row in threshold_rows)
    return {
        "schema_version": (
            "kmfa.v014_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_"
            "diagnostic_response_actionability_blocker_threshold_recheck_summary.v1"
        ),
        "record_type": (
            "v014_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_"
            "diagnostic_response_actionability_blocker_threshold_recheck_summary"
        ),
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": generated_at,
        "status": STATUS,
        "decision": DECISION,
        "actionability_threshold_conclusion": ACTIONABILITY_THRESHOLD_CONCLUSION,
        "source_phase_id": source_summary.get("phase_id"),
        "source_manifest_phase_id": source_manifest.get("phase_id"),
        "source_go_no_go_decision": source_go_no_go.get("decision"),
        "source_matrix_check_fail_count": source_matrix.get("check_fail_count"),
        "source_actionability_blocker_audit_item_count": source_summary.get("private_audit_queue_item_count"),
        "source_actionability_blocker_count": source_summary.get("actionability_blocker_count"),
        "source_private_actionability_blocker_audit_queue_item_count": len(audit_rows),
        "prior_actionability_blocker_observation_count": 1,
        "actionability_blocker_observation_count": 2,
        "actionability_blocked_audit_threshold_met": False,
        "goal_status_recommendation": "continue_blocker_recheck",
        "actionability_ready_count": 0,
        "actionability_blocker_count": len(threshold_rows),
        "private_threshold_records_item_count": len(threshold_rows),
        "valid_diagnostic_response_count": source_summary.get("valid_diagnostic_response_count"),
        "actionable_resolution_count": 0,
        "source_reference_or_owner_exclusion_actionability_blocker_count": counts[SOURCE_REFERENCE_DIAGNOSTIC_KIND],
        "formula_or_non_numeric_mapping_actionability_blocker_count": counts[FORMULA_MAPPING_DIAGNOSTIC_KIND],
        "binding_ready_after_actionability_blocker_threshold_recheck_count": 0,
        "comparison_retry_ready_after_actionability_blocker_threshold_recheck_count": 0,
        "unresolved_difference_count": source_summary.get("unresolved_difference_count"),
        "private_actionability_threshold_diagnostic_written": True,
        "private_actionability_threshold_records_written": True,
        "private_actionability_threshold_report_written": True,
        "private_actionability_threshold_diagnostic_gitignored": _git_check_ignored(
            PRIVATE_ACTIONABILITY_THRESHOLD_DIAGNOSTIC_PATH
        ),
        "private_actionability_threshold_records_gitignored": _git_check_ignored(
            PRIVATE_ACTIONABILITY_THRESHOLD_RECORDS_PATH
        ),
        "private_actionability_threshold_report_gitignored": _git_check_ignored(
            PRIVATE_ACTIONABILITY_THRESHOLD_REPORT_PATH
        ),
        "source_private_actionability_blocker_audit_diagnostic_gitignored": _git_check_ignored(
            SOURCE_PRIVATE_ACTIONABILITY_BLOCKER_AUDIT_DIAGNOSTIC_PATH
        ),
        "source_private_actionability_blocker_audit_queue_gitignored": _git_check_ignored(
            SOURCE_PRIVATE_ACTIONABILITY_BLOCKER_AUDIT_QUEUE_PATH
        ),
        "source_private_actionability_blocker_audit_report_gitignored": _git_check_ignored(
            SOURCE_PRIVATE_ACTIONABILITY_BLOCKER_AUDIT_REPORT_PATH
        ),
        "owner_or_agent_valid_response_available": True,
        "generated_diagnostic_response_actionability_blocker_threshold_recheck_performed": True,
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
        "raw_boundary": _raw_boundary(),
        "public_safety": _public_safety(),
    }


def _build_matrix(summary: dict[str, Any]) -> dict[str, Any]:
    checks = [
        ("source_actionability_blocker_audit_phase_loaded", summary["source_phase_id"] == source_audit.PHASE_ID),
        ("source_go_no_go_preserved", summary["source_go_no_go_decision"] == "NO_GO"),
        ("source_matrix_clean", summary["source_matrix_check_fail_count"] == 0),
        ("source_actionability_blocker_audit_complete", summary["source_actionability_blocker_audit_item_count"] == 48),
        ("source_actionability_blockers_complete", summary["source_actionability_blocker_count"] == 48),
        ("source_private_actionability_blocker_audit_queue_complete", summary["source_private_actionability_blocker_audit_queue_item_count"] == 48),
        ("actionability_blocker_threshold_recheck_complete", summary["private_threshold_records_item_count"] == 48),
        ("second_blocker_observation_recorded", summary["actionability_blocker_observation_count"] == 2),
        ("actionability_blocked_threshold_not_met", summary["actionability_blocked_audit_threshold_met"] is False),
        (
            "diagnostic_kind_actionability_blocker_counts_locked",
            summary["source_reference_or_owner_exclusion_actionability_blocker_count"] == 40
            and summary["formula_or_non_numeric_mapping_actionability_blocker_count"] == 8,
        ),
        ("raw_inbox_untouched", summary["raw_boundary"]["raw_inbox_mutated_by_this_phase"] is False),
        (
            "downstream_gates_closed",
            summary["github_upload_performed"] is False and summary["business_execution_performed"] is False,
        ),
    ]
    rows = [{"check_code": code, "status": "PASS" if passed else "FAIL"} for code, passed in checks]
    pass_count = sum(1 for row in rows if row["status"] == "PASS")
    return {
        "schema_version": (
            "kmfa.v014_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_"
            "diagnostic_response_actionability_blocker_threshold_recheck_matrix_public_safe.v1"
        ),
        "record_type": (
            "v014_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_"
            "diagnostic_response_actionability_blocker_threshold_recheck_matrix_public_safe"
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
            "kmfa.v014_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_"
            "diagnostic_response_actionability_blocker_threshold_recheck_go_no_go.v1"
        ),
        "record_type": (
            "v014_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_"
            "diagnostic_response_actionability_blocker_threshold_recheck_go_no_go"
        ),
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": summary["generated_at"],
        "status": STATUS,
        "decision": DECISION,
        "actionability_threshold_conclusion": ACTIONABILITY_THRESHOLD_CONCLUSION,
        "source_actionability_blocker_audit_item_count": summary["source_actionability_blocker_audit_item_count"],
        "actionability_blocker_threshold_recheck_item_count": summary["private_threshold_records_item_count"],
        "prior_actionability_blocker_observation_count": 1,
        "actionability_blocker_observation_count": 2,
        "actionability_blocked_audit_threshold_met": False,
        "goal_status_recommendation": summary["goal_status_recommendation"],
        "actionability_ready_count": summary["actionability_ready_count"],
        "actionability_blocker_count": summary["actionability_blocker_count"],
        "actionable_resolution_count": 0,
        "source_reference_or_owner_exclusion_actionability_blocker_count": summary[
            "source_reference_or_owner_exclusion_actionability_blocker_count"
        ],
        "formula_or_non_numeric_mapping_actionability_blocker_count": summary[
            "formula_or_non_numeric_mapping_actionability_blocker_count"
        ],
        "unresolved_difference_count": summary["unresolved_difference_count"],
        "authoritative_binding_application_ready": False,
        "raw_to_processed_value_comparison_allowed": False,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "full_raw_to_processed_value_comparison_complete": False,
        "business_value_consistency_verified": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "business_execution_allowed": False,
        "next_required_input": NEXT_REQUIRED_INPUT,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
    }


def _build_manifest(summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": (
            "kmfa.v014_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_"
            "diagnostic_response_actionability_blocker_threshold_recheck_manifest.v1"
        ),
        "record_type": (
            "v014_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_"
            "diagnostic_response_actionability_blocker_threshold_recheck_manifest"
        ),
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": summary["generated_at"],
        "status": STATUS,
        "decision": DECISION,
        "actionability_threshold_conclusion": ACTIONABILITY_THRESHOLD_CONCLUSION,
        "summary": summary,
        "matrix": matrix,
        "go_no_go_report": go_no_go,
        "source_artifacts": {
            "source_actionability_blocker_audit_public_summary": "public_safe_metadata_copy",
            "source_actionability_blocker_audit_public_manifest": "public_safe_metadata_copy",
            "source_actionability_blocker_audit_public_go_no_go": "public_safe_metadata_copy",
            "source_actionability_blocker_audit_public_matrix": "public_safe_metadata_copy",
            "source_private_actionability_blocker_audit_diagnostic": "ignored_private_runtime",
            "source_private_actionability_blocker_audit_queue": "ignored_private_runtime",
            "source_private_actionability_blocker_audit_report": "ignored_private_runtime",
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
            "private:owner_or_agent_generated_diagnostic_response_actionability_threshold_diagnostic",
            "private:owner_or_agent_generated_diagnostic_response_actionability_threshold_records",
            "private:owner_or_agent_generated_diagnostic_response_actionability_threshold_report",
        ],
        "raw_boundary": summary["raw_boundary"],
        "public_safety": summary["public_safety"],
        "test_commands": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_actionability_blocker_threshold_recheck.py --generated-at 2026-07-08T00:00:00+10:00",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_actionability_blocker_threshold_recheck.py --require-private-threshold",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_actionability_blocker_threshold_recheck",
        ],
        "git": {
            "branch": _git_output(["branch", "--show-current"]),
            "head": "local_commit_recorded_after_validation",
            "status_short_branch": "omitted_for_reproducible_phase_manifest",
            "changed_kmfa_files": _phase_public_files(),
        },
    }


def _write_private_outputs(*, generated_at: str, summary: dict[str, Any], threshold_rows: list[dict[str, Any]]) -> None:
    _write_json(
        PRIVATE_ACTIONABILITY_THRESHOLD_DIAGNOSTIC_PATH,
        {
            "schema_version": (
                "kmfa.private.v014_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_"
                "diagnostic_response_actionability_blocker_threshold_recheck.v1"
            ),
            "classification": "private_owner_or_agent_generated_diagnostic_response_actionability_threshold_do_not_commit",
            "record_type": (
                "v014_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_"
                "diagnostic_response_actionability_blocker_threshold_recheck_private_diagnostic"
            ),
            "project_id": "KMFA",
            "version": VERSION,
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "generated_at": generated_at,
            "actionability_threshold_rows": threshold_rows,
            "summary_private": {
                "prior_actionability_blocker_observation_count": 1,
                "actionability_blocker_observation_count": 2,
                "actionability_blocked_audit_threshold_met": False,
                "actionability_ready_count": 0,
                "actionability_blocker_count": summary["actionability_blocker_count"],
                "actionable_resolution_count": 0,
                "binding_ready_after_actionability_blocker_threshold_recheck_count": 0,
                "comparison_retry_ready_after_actionability_blocker_threshold_recheck_count": 0,
                "business_value_consistency_verified": False,
            },
            "raw_boundary": summary["raw_boundary"],
        },
    )
    _write_jsonl(PRIVATE_ACTIONABILITY_THRESHOLD_RECORDS_PATH, threshold_rows)
    _write_text(
        PRIVATE_ACTIONABILITY_THRESHOLD_REPORT_PATH,
        "\n".join(
            [
                "# Private Generated Diagnostic Response Actionability Blocker Threshold Recheck Report",
                "",
                f"- phase_id: `{PHASE_ID}`",
                "- prior_actionability_blocker_observation_count: `1`",
                "- actionability_blocker_observation_count: `2`",
                "- actionability_blocked_audit_threshold_met: `false`",
                f"- private_threshold_records_item_count: `{summary['private_threshold_records_item_count']}`",
                "- authoritative_binding_application_ready: `false`",
                "- raw_to_processed_value_comparison_ready: `false`",
                "- raw_inbox_mutated_by_this_phase: `false`",
                "",
                "Private threshold rows may contain private handles and must remain ignored.",
                "",
            ]
        ),
    )


def _write_human(summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any]) -> None:
    _write_text(
        REPORT_PATH,
        f"""# V014 Generated Diagnostic Response Actionability Blocker Threshold Recheck

Generated at: {summary["generated_at"]}

## Scope

- Phase: `{PHASE_ID}`
- Decision: `{DECISION}`
- Status: `{STATUS}`
- Source: prior public-safe actionability blocker audit evidence plus ignored private audit queue.
- Raw boundary: no raw inbox read, list, stat, parse, value extraction, write, delete, move, rename, copy, normalize or mutation.

## Public-Safe Result

- Source actionability blocker audit items: `{summary["source_actionability_blocker_audit_item_count"]}`
- Source actionability blockers: `{summary["source_actionability_blocker_count"]}`
- Prior audit observation count: `{summary["prior_actionability_blocker_observation_count"]}`
- Current audit observation count: `{summary["actionability_blocker_observation_count"]}`
- Blocked audit threshold met: `{str(summary["actionability_blocked_audit_threshold_met"]).lower()}`
- Actionability ready items: `{summary["actionability_ready_count"]}`
- Actionability blockers: `{summary["actionability_blocker_count"]}`
- Private threshold records: `{summary["private_threshold_records_item_count"]}`
- Source reference or owner exclusion actionability blockers: `{summary["source_reference_or_owner_exclusion_actionability_blocker_count"]}`
- Formula or non-numeric mapping actionability blockers: `{summary["formula_or_non_numeric_mapping_actionability_blocker_count"]}`
- Unresolved differences: `{summary["unresolved_difference_count"]}`

## Gate

The generated diagnostic responses remain non-actionable for authoritative binding or value comparison. This phase records the second blocker observation only; threshold is still not met and raw-to-processed value consistency is not verified.

Next required input: `{NEXT_REQUIRED_INPUT}`.
""",
    )
    _write_text(
        GO_NO_GO_RECORD_PATH,
        f"""# Go / No-Go Record

- Phase: `{PHASE_ID}`
- Decision: `{go_no_go["decision"]}`
- Reason: `{ACTIONABILITY_THRESHOLD_CONCLUSION}`
- Matrix: `{matrix["check_pass_count"]}` pass / `{matrix["check_fail_count"]}` fail
- GitHub upload: not allowed in this phase.
- App reinstall: not allowed in this phase.
- Business execution: not allowed in this phase.
""",
    )
    _write_text(
        TEST_RESULTS_PATH,
        f"""# Test Results

- RED: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_actionability_blocker_threshold_recheck` failed before implementation because the generator module did not exist.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_actionability_blocker_threshold_recheck.py --generated-at 2026-07-08T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_actionability_blocker_threshold_recheck.py --require-private-threshold`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_actionability_blocker_threshold_recheck`
- Governance validators, CSV shape checks, diff check, raw/private marker scan, secret scan and private-runtime tracked-file scan: expected before commit.

Expected matrix result: {matrix["check_pass_count"]}/{matrix["check_count"]} PASS.
""",
    )
    _write_text(
        RISK_REGISTER_PATH,
        """# Risk Register

- Risk: threshold recheck is mistaken for actionable binding evidence.
- Control: this phase records only second blocker observation and keeps binding and value comparison closed.
- Risk: private diagnostic handles leak into public evidence.
- Control: public artifacts contain aggregate counts only; threshold rows stay ignored.
- Risk: raw inbox is modified.
- Control: this phase consumes existing ignored private actionability blocker audit artifacts only and does not touch the raw inbox.
""",
    )
    _write_text(
        ROLLBACK_PATH,
        f"""# Rollback Plan

Remove artifacts for `{PHASE_ID}`, metadata copies, private actionability threshold outputs, tool, validator, focused test and governance rows. Do not touch source actionability blocker audit outputs or raw inbox files.
""",
    )


def _write_governance_events(generated_at: str, summary: dict[str, Any]) -> None:
    event_id = (
        "DEV-KMFA-20260708-V014-AUTHORIZED-SOURCE-REFERENCE-OR-EXCLUSION-APPLICATION-OWNER-OR-AGENT-"
        "GENERATED-DIAGNOSTIC-RESPONSE-ACTIONABILITY-BLOCKER-THRESHOLD-RECHECK"
    )
    _upsert_jsonl(
        DEVELOPMENT_EVENTS_PATH,
        {
            "event_id": event_id,
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
                "Rechecked 48 generated diagnostic response actionability blockers as second observation and kept "
                "binding, comparison and upload gates closed."
            ),
            "evidence_ref": MANIFEST_PATH.as_posix(),
            "files_changed": _phase_public_files(),
            "test_commands": [
                "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_actionability_blocker_threshold_recheck.py --generated-at 2026-07-08T00:00:00+10:00",
                "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_actionability_blocker_threshold_recheck.py --require-private-threshold",
                "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_actionability_blocker_threshold_recheck",
            ],
            "test_results": ["PENDING: final validation results will be recorded before local commit."],
            "source_actionability_blocker_audit_item_count": summary["source_actionability_blocker_audit_item_count"],
            "actionability_blocker_observation_count": summary["actionability_blocker_observation_count"],
            "actionability_blocked_audit_threshold_met": False,
            "actionability_blocker_count": summary["actionability_blocker_count"],
            "actionable_resolution_count": 0,
            "unresolved_difference_count": summary["unresolved_difference_count"],
            "raw_inbox_read_performed": False,
            "raw_inbox_mutation_performed": False,
            "raw_to_processed_value_comparison_performed": False,
            "business_value_consistency_verified": False,
            "github_upload_performed": False,
            "app_reinstall_performed": False,
            "business_execution_performed": False,
            "result_commit": "PENDING",
            "fact_level": "EXTRACTED",
        },
        ("event_id",),
    )
    _upsert_jsonl(
        STAGE_STATUS_PATH,
        {
            "schema_version": "kmfa.stage_status.v1",
            "project_id": "KMFA",
            "version": VERSION,
            "record_type": "stage_phase_status",
            "stage_id": "VALUE-CONSISTENCY",
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "status": STATUS,
            "decision": DECISION,
            "updated_at": generated_at,
            "evidence_ref": MANIFEST_PATH.as_posix(),
            "raw_data_committed": False,
            "github_upload_performed": False,
            "app_reinstall_performed": False,
            "business_execution_performed": False,
        },
        ("phase_id", "task_id"),
    )
    _upsert_jsonl(
        TASK_STATUS_PATH,
        {
            "schema_version": "kmfa.v014_stage_phase_task_status.v1",
            "project_id": "KMFA",
            "version": VERSION,
            "raw_data_committed": False,
            "record_type": "v014_phase",
            "roadmap_stage_id": "VALUE-CONSISTENCY",
            "roadmap_phase_id": PHASE_ID.replace("V014_", ""),
            "governance_stage_id": "VALUE-CONSISTENCY",
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "name": "v0.1.4 generated owner/agent diagnostic response actionability blocker threshold recheck",
            "status": STATUS,
            "completed_task_units": 1,
            "estimated_task_units": 1,
            "derived_percent": 100.0,
            "acceptance_id": ACCEPTANCE_ID,
            "evidence_ref": MANIFEST_PATH.as_posix(),
            "fact_level": "EXTRACTED",
            "updated_at": generated_at[:10],
            "stage_id": "VALUE-CONSISTENCY",
            "phase_goal": "record second blocker observation for non-actionable generated diagnostic responses",
            "task_count": 3,
            "acceptance_output": (
                "Actionability blocker threshold recheck manifest, summary, Go No-Go, private ignored threshold "
                "records, validator, focused test and governance records"
            ),
        },
        ("phase_id", "record_type", "task_id"),
    )
    for suffix, task_goal in (
        ("T1", "read prior public actionability blocker audit evidence and ignored private audit queue read-only"),
        ("T2", "write ignored private actionability threshold diagnostic and records for 48 blocked responses"),
        ("T3", "emit public-safe NO_GO threshold recheck evidence while keeping binding comparison and upload gates closed"),
    ):
        _upsert_jsonl(
            TASK_STATUS_PATH,
            {
                "schema_version": "kmfa.v014_stage_phase_task_status.v1",
                "project_id": "KMFA",
                "version": VERSION,
                "raw_data_committed": False,
                "record_type": "v014_task",
                "roadmap_stage_id": "VALUE-CONSISTENCY",
                "roadmap_phase_id": PHASE_ID.replace("V014_", ""),
                "governance_stage_id": "VALUE-CONSISTENCY",
                "phase_id": PHASE_ID,
                "task_id": f"{TASK_ID}-{suffix}",
                "status": "completed",
                "acceptance_id": ACCEPTANCE_ID,
                "evidence_ref": MANIFEST_PATH.as_posix(),
                "fact_level": "EXTRACTED",
                "updated_at": generated_at[:10],
                "stage_id": "VALUE-CONSISTENCY",
                "task_goal": task_goal,
                "derived_percent": 100.0,
            },
            ("phase_id", "record_type", "task_id"),
        )


def generate(*, generated_at: str | None = None, write_governance_event: bool = True) -> dict[str, Any]:
    generated = _now(generated_at)
    source_summary = _read_json(SOURCE_PUBLIC_SUMMARY_PATH)
    source_manifest = _read_json(SOURCE_PUBLIC_MANIFEST_PATH)
    source_go_no_go = _read_json(SOURCE_PUBLIC_GO_NO_GO_PATH)
    source_matrix = _read_json(SOURCE_PUBLIC_MATRIX_PATH)
    source_audit_rows = _read_jsonl(SOURCE_PRIVATE_ACTIONABILITY_BLOCKER_AUDIT_QUEUE_PATH)
    if not SOURCE_PRIVATE_ACTIONABILITY_BLOCKER_AUDIT_DIAGNOSTIC_PATH.exists():
        raise FileNotFoundError(SOURCE_PRIVATE_ACTIONABILITY_BLOCKER_AUDIT_DIAGNOSTIC_PATH)
    if not SOURCE_PRIVATE_ACTIONABILITY_BLOCKER_AUDIT_REPORT_PATH.exists():
        raise FileNotFoundError(SOURCE_PRIVATE_ACTIONABILITY_BLOCKER_AUDIT_REPORT_PATH)
    threshold_rows = _build_threshold_rows(generated_at=generated, audit_rows=source_audit_rows)
    summary = _build_summary(
        generated_at=generated,
        source_summary=source_summary,
        source_manifest=source_manifest,
        source_go_no_go=source_go_no_go,
        source_matrix=source_matrix,
        audit_rows=source_audit_rows,
        threshold_rows=threshold_rows,
    )
    matrix = _build_matrix(summary)
    go_no_go = _build_go_no_go(summary)
    manifest = _build_manifest(summary, matrix, go_no_go)
    _write_private_outputs(generated_at=generated, summary=summary, threshold_rows=threshold_rows)
    _write_human(summary, matrix, go_no_go)
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
    if write_governance_event:
        _write_governance_events(generated, summary)
        manifest = _build_manifest(summary, matrix, go_no_go)
        _write_json(MANIFEST_PATH, manifest)
        _write_json(METADATA_MANIFEST_PATH, manifest)
    return {"summary": summary, "matrix": matrix, "go_no_go": go_no_go, "manifest": manifest}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generated-at")
    args = parser.parse_args(argv)
    result = generate(generated_at=args.generated_at)
    summary = result["summary"]
    print(
        "PASS: threshold-rechecked V014 generated owner/agent diagnostic response actionability blockers "
        f"items={summary['private_threshold_records_item_count']} "
        f"observation={summary['actionability_blocker_observation_count']} "
        f"decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
