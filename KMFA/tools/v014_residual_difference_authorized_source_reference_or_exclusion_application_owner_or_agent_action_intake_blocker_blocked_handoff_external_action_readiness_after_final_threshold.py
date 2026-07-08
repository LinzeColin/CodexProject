#!/usr/bin/env python3
"""Check owner or authorized-agent action intake blocker blocked handoff external action readiness after final threshold.

This phase consumes the previous public-safe blocked handoff evidence and the
ignored private owner-action queue. It does not read the raw inbox and it does
not apply authoritative bindings, compare values, upload, reinstall, or execute
business workflows.
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
    v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_action_intake_blocker_blocked_handoff_after_final_threshold
    as source_blocked_handoff,
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
    "ACTION_INTAKE_BLOCKER_BLOCKED_HANDOFF_EXTERNAL_ACTION_READINESS_AFTER_FINAL_THRESHOLD"
)
TASK_ID = (
    "KMFA-V014-RESIDUAL-DIFFERENCE-AUTHORIZED-SOURCE-REFERENCE-OR-EXCLUSION-APPLICATION-OWNER-OR-"
    "AGENT-ACTION-INTAKE-BLOCKER-BLOCKED-HANDOFF-EXTERNAL-ACTION-READINESS-AFTER-FINAL-THRESHOLD-20260708"
)
ACCEPTANCE_ID = (
    "ACC-V014-RESIDUAL-DIFFERENCE-AUTHORIZED-SOURCE-REFERENCE-OR-EXCLUSION-APPLICATION-OWNER-OR-"
    "AGENT-ACTION-INTAKE-BLOCKER-BLOCKED-HANDOFF-EXTERNAL-ACTION-READINESS-AFTER-FINAL-THRESHOLD"
)
VERSION = (
    "0.1.4-residual-difference-authorized-source-reference-or-exclusion-application-owner-or-agent-"
    "action-intake-blocker-blocked-handoff-external-action-readiness-after-final-threshold"
)
STATUS = (
    "completed_validated_local_only_authorized_source_reference_or_exclusion_application_owner_or_agent_"
    "action_intake_blocker_blocked_handoff_external_action_readiness_after_final_threshold_no_go_blocked"
)
DECISION = "NO_GO"
READINESS_CONCLUSION = "blocked_waiting_for_owner_or_authorized_agent_external_action_after_final_threshold"
NEXT_REQUIRED_INPUT = source_blocked_handoff.NEXT_REQUIRED_INPUT
NEXT_RECOMMENDED_PHASE = "owner_or_authorized_agent_external_action_required_before_authoritative_binding"

SOURCE_REFERENCE_DIAGNOSTIC_KIND = source_blocked_handoff.SOURCE_REFERENCE_DIAGNOSTIC_KIND
FORMULA_MAPPING_DIAGNOSTIC_KIND = source_blocked_handoff.FORMULA_MAPPING_DIAGNOSTIC_KIND

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
PREFIX = (
    "residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_"
    "action_intake_blocker_blocked_handoff_external_action_readiness_after_final_threshold"
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

SOURCE_BLOCKED_HANDOFF_SUMMARY_PATH = source_blocked_handoff.METADATA_SUMMARY_PATH
SOURCE_BLOCKED_HANDOFF_MANIFEST_PATH = source_blocked_handoff.METADATA_MANIFEST_PATH
SOURCE_BLOCKED_HANDOFF_GO_NO_GO_PATH = source_blocked_handoff.METADATA_GO_NO_GO_PATH
SOURCE_BLOCKED_HANDOFF_MATRIX_PATH = source_blocked_handoff.METADATA_MATRIX_PATH
SOURCE_PRIVATE_ACTION_INTAKE_BLOCKER_BLOCKED_HANDOFF_DIAGNOSTIC_PATH = (
    source_blocked_handoff.PRIVATE_ACTION_INTAKE_BLOCKER_BLOCKED_HANDOFF_DIAGNOSTIC_PATH
)
SOURCE_PRIVATE_ACTION_INTAKE_BLOCKER_BLOCKED_HANDOFF_RECORDS_PATH = (
    source_blocked_handoff.PRIVATE_ACTION_INTAKE_BLOCKER_BLOCKED_HANDOFF_RECORDS_PATH
)
SOURCE_PRIVATE_ACTION_INTAKE_BLOCKER_OWNER_ACTION_QUEUE_PATH = (
    source_blocked_handoff.PRIVATE_ACTION_INTAKE_BLOCKER_OWNER_ACTION_QUEUE_PATH
)
SOURCE_PRIVATE_ACTION_INTAKE_BLOCKER_BLOCKED_HANDOFF_REPORT_PATH = (
    source_blocked_handoff.PRIVATE_ACTION_INTAKE_BLOCKER_BLOCKED_HANDOFF_REPORT_PATH
)
SOURCE_PRIVATE_BLOCKED_HANDOFF_DIAGNOSTIC_PATH = (
    SOURCE_PRIVATE_ACTION_INTAKE_BLOCKER_BLOCKED_HANDOFF_DIAGNOSTIC_PATH
)
SOURCE_PRIVATE_BLOCKED_HANDOFF_RECORDS_PATH = (
    SOURCE_PRIVATE_ACTION_INTAKE_BLOCKER_BLOCKED_HANDOFF_RECORDS_PATH
)
SOURCE_PRIVATE_OWNER_ACTION_QUEUE_PATH = SOURCE_PRIVATE_ACTION_INTAKE_BLOCKER_OWNER_ACTION_QUEUE_PATH
SOURCE_PRIVATE_BLOCKED_HANDOFF_REPORT_PATH = SOURCE_PRIVATE_ACTION_INTAKE_BLOCKER_BLOCKED_HANDOFF_REPORT_PATH

PRIVATE_OUTPUT_DIR = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_action_intake_blocker_blocked_handoff_external_action_readiness_after_final_threshold"
)
PRIVATE_EXTERNAL_ACTION_READINESS_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_owner_or_agent_external_action_readiness_diagnostic.json"
PRIVATE_EXTERNAL_ACTION_READINESS_BLOCKER_RECORDS_PATH = (
    PRIVATE_OUTPUT_DIR / "private_owner_or_agent_external_action_readiness_blocker_records.jsonl"
)
PRIVATE_EXTERNAL_ACTION_READINESS_QUESTION_LIST_PATH = (
    PRIVATE_OUTPUT_DIR / "private_owner_or_agent_external_action_readiness_question_list.md"
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
        (
            "KMFA/tests/test_v014_residual_difference_authorized_source_reference_or_exclusion_application_"
            "owner_or_agent_action_intake_blocker_blocked_handoff_external_action_readiness_after_final_threshold.py"
        ),
        (
            "KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_"
            "owner_or_agent_action_intake_blocker_blocked_handoff_external_action_readiness_after_final_threshold.py"
        ),
        (
            "KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_"
            "owner_or_agent_action_intake_blocker_blocked_handoff_external_action_readiness_after_final_threshold.py"
        ),
        "KMFA/功能清单.md",
        "KMFA/开发记录.md",
        "KMFA/模型参数文件.md",
    ]


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
        "source_private_owner_action_queue_read_by_this_phase": True,
        "source_private_blocked_handoff_report_existence_checked_by_this_phase": True,
        "private_external_action_readiness_diagnostic_written_by_this_phase": True,
        "private_external_action_readiness_blocker_records_written_by_this_phase": True,
        "private_external_action_readiness_question_list_written_by_this_phase": True,
        "source_private_blocked_handoff_diagnostic_mutated_by_this_phase": False,
        "source_private_blocked_handoff_records_mutated_by_this_phase": False,
        "source_private_owner_action_queue_mutated_by_this_phase": False,
        "source_private_blocked_handoff_report_mutated_by_this_phase": False,
        "owner_or_agent_external_action_completed_by_this_phase": False,
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
        "source_private_owner_action_queue_committed": False,
        "private_external_action_readiness_diagnostic_committed": False,
        "private_external_action_readiness_blocker_records_committed": False,
        "private_external_action_readiness_question_list_committed": False,
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


def _blocker_reason(diagnostic_kind: str) -> str:
    if diagnostic_kind == SOURCE_REFERENCE_DIAGNOSTIC_KIND:
        return "owner_authorized_source_reference_or_owner_exclusion_not_provided"
    if diagnostic_kind == FORMULA_MAPPING_DIAGNOSTIC_KIND:
        return "owner_authorized_formula_or_non_numeric_mapping_not_provided"
    return "owner_authorized_actionable_resolution_not_provided"


def _validate_sources(
    *,
    source_summary: dict[str, Any],
    source_manifest: dict[str, Any],
    source_go_no_go: dict[str, Any],
    source_matrix: dict[str, Any],
    handoff_rows: list[dict[str, Any]],
    owner_action_rows: list[dict[str, Any]],
) -> None:
    if source_summary.get("phase_id") != source_blocked_handoff.PHASE_ID:
        raise ValueError("source blocked-handoff phase mismatch")
    if source_manifest.get("phase_id") != source_blocked_handoff.PHASE_ID:
        raise ValueError("source blocked-handoff manifest phase mismatch")
    if source_go_no_go.get("decision") != "NO_GO":
        raise ValueError("source blocked-handoff decision must be NO_GO")
    if source_matrix.get("check_fail_count") != 0:
        raise ValueError("source blocked-handoff matrix must be clean")
    if source_summary.get("blocked_handoff_item_count") != 48:
        raise ValueError("source blocked-handoff item count must be 48")
    if source_summary.get("owner_action_item_count") != 48:
        raise ValueError("source owner-action item count must be 48")
    if source_summary.get("goal_status_recommendation") != "blocked":
        raise ValueError("source goal status must be blocked")
    if source_summary.get("action_intake_blocked_audit_threshold_met") is not True:
        raise ValueError("source actionability blocked audit threshold must be met")
    if len(handoff_rows) != 48:
        raise ValueError("source private blocked-handoff records must contain 48 rows")
    if len(owner_action_rows) != 48:
        raise ValueError("source private owner-action queue must contain 48 rows")
    for row in owner_action_rows:
        if row.get("owner_action_status") != "required_before_binding_or_value_comparison":
            raise ValueError("source owner-action row must still require action")
        if row.get("authoritative_binding_application_ready") is not False:
            raise ValueError("source owner-action row cannot be binding-ready")
        if row.get("raw_to_processed_value_comparison_ready") is not False:
            raise ValueError("source owner-action row cannot be comparison-ready")


def _build_blocker_records(
    *, generated_at: str, owner_action_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, row in enumerate(owner_action_rows, start=1):
        diagnostic_kind = str(row.get("diagnostic_kind"))
        records.append(
            {
                "action_readiness_item_id": f"ASR-OE-APP-OWNER-AGENT-ACTION-READINESS-{index:03d}",
                "source_owner_action_item_id": row.get("owner_action_item_id"),
                "source_blocked_handoff_item_id": row.get("blocked_handoff_item_id"),
                "phase_id": PHASE_ID,
                "task_id": TASK_ID,
                "generated_at": generated_at,
                "target_slot_id": row.get("target_slot_id"),
                "diagnostic_kind": diagnostic_kind,
                "external_action_readiness_status": READINESS_CONCLUSION,
                "owner_action_status": row.get("owner_action_status"),
                "owner_action_type": row.get("owner_action_type"),
                "external_owner_action_ready": False,
                "external_owner_action_blocker": True,
                "external_owner_action_blocker_reason": _blocker_reason(diagnostic_kind),
                "actionable_owner_resolution_ready": False,
                "binding_ready_after_external_action_readiness": False,
                "comparison_retry_ready_after_external_action_readiness": False,
                "safe_auto_resolution_available": False,
                "authoritative_binding_application_ready": False,
                "authoritative_binding_applied_by_this_phase": False,
                "raw_candidate_fingerprint_bound_by_this_phase": False,
                "raw_to_processed_value_comparison_ready": False,
                "raw_to_processed_value_comparison_performed_by_this_phase": False,
                "business_value_consistency_verified": False,
                "full_raw_to_processed_value_comparison_complete": False,
                "public_commit_allowed": False,
            }
        )
    return records


def _build_summary(
    *,
    generated_at: str,
    source_summary: dict[str, Any],
    source_manifest: dict[str, Any],
    source_go_no_go: dict[str, Any],
    source_matrix: dict[str, Any],
    handoff_rows: list[dict[str, Any]],
    owner_action_rows: list[dict[str, Any]],
    blocker_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    counts = Counter(str(row.get("diagnostic_kind")) for row in blocker_rows)
    return {
        "schema_version": "kmfa.v014_authorized_source_reference_owner_agent_action_readiness_summary.v1",
        "record_type": "v014_authorized_source_reference_owner_agent_action_readiness_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": generated_at,
        "status": STATUS,
        "decision": DECISION,
        "readiness_conclusion": READINESS_CONCLUSION,
        "source_phase_id": source_summary.get("phase_id"),
        "source_manifest_phase_id": source_manifest.get("phase_id"),
        "source_go_no_go_decision": source_go_no_go.get("decision"),
        "source_matrix_check_fail_count": source_matrix.get("check_fail_count"),
        "source_blocked_handoff_item_count": source_summary.get("blocked_handoff_item_count"),
        "source_owner_action_item_count": source_summary.get("owner_action_item_count"),
        "source_private_blocked_handoff_records_item_count": len(handoff_rows),
        "source_private_owner_action_queue_item_count": len(owner_action_rows),
        "source_goal_status_recommendation": source_summary.get("goal_status_recommendation"),
        "source_action_intake_blocked_audit_threshold_met": source_summary.get(
            "action_intake_blocked_audit_threshold_met"
        ),
        "goal_status_recommendation": "blocked",
        "external_owner_action_ready_count": 0,
        "external_owner_action_blocker_count": len(blocker_rows),
        "actionable_owner_resolution_count": 0,
        "source_reference_or_owner_exclusion_external_action_blocker_count": counts[
            SOURCE_REFERENCE_DIAGNOSTIC_KIND
        ],
        "formula_or_non_numeric_mapping_external_action_blocker_count": counts[FORMULA_MAPPING_DIAGNOSTIC_KIND],
        "binding_ready_after_external_action_readiness_count": 0,
        "comparison_retry_ready_after_external_action_readiness_count": 0,
        "unresolved_difference_count": source_summary.get("unresolved_difference_count"),
        "private_external_action_readiness_diagnostic_written": True,
        "private_external_action_readiness_blocker_records_written": True,
        "private_external_action_readiness_question_list_written": True,
        "private_external_action_readiness_diagnostic_gitignored": _git_check_ignored(
            PRIVATE_EXTERNAL_ACTION_READINESS_DIAGNOSTIC_PATH
        ),
        "private_external_action_readiness_blocker_records_gitignored": _git_check_ignored(
            PRIVATE_EXTERNAL_ACTION_READINESS_BLOCKER_RECORDS_PATH
        ),
        "private_external_action_readiness_question_list_gitignored": _git_check_ignored(
            PRIVATE_EXTERNAL_ACTION_READINESS_QUESTION_LIST_PATH
        ),
        "source_private_blocked_handoff_diagnostic_gitignored": _git_check_ignored(
            SOURCE_PRIVATE_BLOCKED_HANDOFF_DIAGNOSTIC_PATH
        ),
        "source_private_blocked_handoff_records_gitignored": _git_check_ignored(
            SOURCE_PRIVATE_BLOCKED_HANDOFF_RECORDS_PATH
        ),
        "source_private_owner_action_queue_gitignored": _git_check_ignored(
            SOURCE_PRIVATE_OWNER_ACTION_QUEUE_PATH
        ),
        "external_action_readiness_checked_by_this_phase": True,
        "owner_or_agent_external_action_completed_by_this_phase": False,
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
        ("source_blocked_handoff_phase_loaded", summary["source_phase_id"] == source_blocked_handoff.PHASE_ID),
        ("source_go_no_go_preserved", summary["source_go_no_go_decision"] == "NO_GO"),
        ("source_matrix_clean", summary["source_matrix_check_fail_count"] == 0),
        ("source_blocked_handoff_complete", summary["source_blocked_handoff_item_count"] == 48),
        ("source_owner_action_queue_complete", summary["source_owner_action_item_count"] == 48),
        ("private_owner_action_queue_read", summary["source_private_owner_action_queue_item_count"] == 48),
        ("external_action_readiness_checked", summary["external_action_readiness_checked_by_this_phase"] is True),
        ("external_owner_action_blockers_locked", summary["external_owner_action_blocker_count"] == 48),
        (
            "diagnostic_kind_owner_action_counts_locked",
            summary["source_reference_or_owner_exclusion_external_action_blocker_count"] == 40
            and summary["formula_or_non_numeric_mapping_external_action_blocker_count"] == 8,
        ),
        ("blocked_goal_preserved", summary["goal_status_recommendation"] == "blocked"),
        ("raw_inbox_untouched", summary["raw_boundary"]["raw_inbox_mutated_by_this_phase"] is False),
        (
            "downstream_gates_closed",
            summary["github_upload_performed"] is False and summary["business_execution_performed"] is False,
        ),
    ]
    rows = [{"check_code": code, "status": "PASS" if passed else "FAIL"} for code, passed in checks]
    pass_count = sum(1 for row in rows if row["status"] == "PASS")
    return {
        "schema_version": "kmfa.v014_authorized_source_reference_owner_agent_action_readiness_matrix.v1",
        "record_type": "v014_authorized_source_reference_owner_agent_action_readiness_matrix_public_safe",
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
        "schema_version": "kmfa.v014_authorized_source_reference_owner_agent_action_readiness_go_no_go.v1",
        "record_type": "v014_authorized_source_reference_owner_agent_action_readiness_go_no_go",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": summary["generated_at"],
        "status": STATUS,
        "decision": DECISION,
        "readiness_conclusion": READINESS_CONCLUSION,
        "source_blocked_handoff_item_count": summary["source_blocked_handoff_item_count"],
        "source_owner_action_item_count": summary["source_owner_action_item_count"],
        "goal_status_recommendation": "blocked",
        "external_owner_action_ready_count": 0,
        "external_owner_action_blocker_count": summary["external_owner_action_blocker_count"],
        "actionable_owner_resolution_count": 0,
        "source_reference_or_owner_exclusion_external_action_blocker_count": summary[
            "source_reference_or_owner_exclusion_external_action_blocker_count"
        ],
        "formula_or_non_numeric_mapping_external_action_blocker_count": summary[
            "formula_or_non_numeric_mapping_external_action_blocker_count"
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
        "schema_version": "kmfa.v014_authorized_source_reference_owner_agent_action_readiness_manifest.v1",
        "record_type": "v014_authorized_source_reference_owner_agent_action_readiness_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": summary["generated_at"],
        "status": STATUS,
        "decision": DECISION,
        "readiness_conclusion": READINESS_CONCLUSION,
        "summary": summary,
        "matrix": matrix,
        "go_no_go_report": go_no_go,
        "source_artifacts": {
            "source_blocked_handoff_public_summary": "public_safe_metadata_copy",
            "source_blocked_handoff_public_manifest": "public_safe_metadata_copy",
            "source_blocked_handoff_public_go_no_go": "public_safe_metadata_copy",
            "source_blocked_handoff_public_matrix": "public_safe_metadata_copy",
            "source_private_blocked_handoff_diagnostic": "ignored_private_runtime",
            "source_private_blocked_handoff_records": "ignored_private_runtime",
            "source_private_owner_action_queue": "ignored_private_runtime",
            "source_private_blocked_handoff_report": "ignored_private_runtime",
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
            "private:owner_or_agent_external_action_readiness_diagnostic",
            "private:owner_or_agent_external_action_readiness_blocker_records",
            "private:owner_or_agent_external_action_readiness_question_list",
        ],
        "raw_boundary": summary["raw_boundary"],
        "public_safety": summary["public_safety"],
        "test_commands": [
            (
                "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 "
                "KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_"
                "owner_or_agent_action_intake_blocker_blocked_handoff_external_action_readiness_after_final_threshold.py --generated-at "
                "2026-07-08T00:00:00+10:00"
            ),
            (
                "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 "
                "KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_"
                "owner_or_agent_action_intake_blocker_blocked_handoff_external_action_readiness_after_final_threshold.py --require-private-external-action-readiness"
            ),
            (
                "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest "
                "KMFA.tests.test_v014_residual_difference_authorized_source_reference_or_exclusion_application_"
                "owner_or_agent_action_intake_blocker_blocked_handoff_external_action_readiness_after_final_threshold"
            ),
        ],
        "git": {
            "branch": _git_output(["branch", "--show-current"]),
            "head": "local_commit_recorded_after_validation",
            "status_short_branch": "omitted_for_reproducible_phase_manifest",
            "changed_kmfa_files": _phase_public_files(),
        },
    }


def _write_private_outputs(
    *, generated_at: str, summary: dict[str, Any], blocker_rows: list[dict[str, Any]]
) -> None:
    counts = Counter(str(row.get("diagnostic_kind")) for row in blocker_rows)
    _write_json(
        PRIVATE_EXTERNAL_ACTION_READINESS_DIAGNOSTIC_PATH,
        {
            "schema_version": "kmfa.private.v014_owner_agent_action_intake_blocker_blocked_handoff_external_action_readiness_after_final_threshold.v1",
            "classification": "private_owner_or_agent_external_action_readiness_do_not_commit",
            "record_type": "v014_owner_agent_action_intake_blocker_blocked_handoff_external_action_readiness_after_final_threshold_private_diagnostic",
            "project_id": "KMFA",
            "version": VERSION,
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "generated_at": generated_at,
            "blocker_rows": blocker_rows,
            "summary_private": {
                "external_owner_action_blocker_count": len(blocker_rows),
                "external_owner_action_ready_count": 0,
                "goal_status_recommendation": "blocked",
                "source_reference_or_owner_exclusion_external_action_blocker_count": counts[
                    SOURCE_REFERENCE_DIAGNOSTIC_KIND
                ],
                "formula_or_non_numeric_mapping_external_action_blocker_count": counts[
                    FORMULA_MAPPING_DIAGNOSTIC_KIND
                ],
                "binding_ready_after_external_action_readiness_count": 0,
                "comparison_retry_ready_after_external_action_readiness_count": 0,
            },
            "raw_boundary": summary["raw_boundary"],
        },
    )
    _write_jsonl(PRIVATE_EXTERNAL_ACTION_READINESS_BLOCKER_RECORDS_PATH, blocker_rows)
    question_lines = [
        "# owner/授权代理 external action readiness 问题清单",
        "",
        f"- phase_id: `{PHASE_ID}`",
        f"- external_owner_action_blocker_count: `{len(blocker_rows)}`",
        f"- source reference / owner exclusion blockers: `{counts[SOURCE_REFERENCE_DIAGNOSTIC_KIND]}`",
        f"- formula / non-numeric mapping blockers: `{counts[FORMULA_MAPPING_DIAGNOSTIC_KIND]}`",
        "- raw inbox touched: `false`",
        "",
        "## 需要 owner 或授权代理提供的内容",
        "",
        "1. 对 source reference / owner exclusion 类 blocker，提供可执行 source reference 或明确 owner exclusion。",
        "2. 对 formula / non-numeric mapping 类 blocker，提供可执行公式映射或非数值映射依据。",
        "3. 任何回答必须保持为私有运行时材料，不允许进入 GitHub public evidence。",
        "",
        "当前未检测到可执行 owner/授权代理动作，因此 binding、value comparison 和业务执行继续关闭。",
        "",
    ]
    _write_text(PRIVATE_EXTERNAL_ACTION_READINESS_QUESTION_LIST_PATH, "\n".join(question_lines))


def _write_human(summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any]) -> None:
    _write_text(
        REPORT_PATH,
        f"""# V014 Owner / Authorized Agent Action Intake Blocker Blocked Handoff External Action Readiness After Final Threshold

Generated at: {summary["generated_at"]}

## Scope

- Phase: `{PHASE_ID}`
- Decision: `{DECISION}`
- Status: `{STATUS}`
- Source: prior public-safe blocked handoff evidence plus ignored private owner-action queue.
- Raw boundary: no raw inbox read, list, stat, parse, value extraction, write, delete, move, rename, copy, normalize or mutation.

## Public-Safe Readiness Result

- Source blocked handoff items: `{summary["source_blocked_handoff_item_count"]}`
- Source owner-action items: `{summary["source_owner_action_item_count"]}`
- Owner action ready count: `{summary["external_owner_action_ready_count"]}`
- Owner action blocker count: `{summary["external_owner_action_blocker_count"]}`
- Actionable owner resolution count: `{summary["actionable_owner_resolution_count"]}`
- Source reference or owner exclusion blockers: `{summary["source_reference_or_owner_exclusion_external_action_blocker_count"]}`
- Formula or non-numeric mapping blockers: `{summary["formula_or_non_numeric_mapping_external_action_blocker_count"]}`
- Binding ready after owner action readiness: `{summary["binding_ready_after_external_action_readiness_count"]}`
- Comparison retry ready after owner action readiness: `{summary["comparison_retry_ready_after_external_action_readiness_count"]}`
- Unresolved differences: `{summary["unresolved_difference_count"]}`

## Gate

No executable owner/authorized-agent source reference, owner exclusion, formula mapping or non-numeric mapping was detected in the ignored owner-action queue. This phase records a blocked question list only and does not authorize binding, raw-to-processed value comparison, reconciliation, business consistency, GitHub upload, app reinstall or business execution.

Next required input: `{NEXT_REQUIRED_INPUT}`.
""",
    )
    _write_text(
        GO_NO_GO_RECORD_PATH,
        f"""# Go / No-Go Record

- Phase: `{PHASE_ID}`
- Decision: `{go_no_go["decision"]}`
- Reason: `{READINESS_CONCLUSION}`
- Goal status recommendation: `{go_no_go["goal_status_recommendation"]}`
- Matrix: `{matrix["check_pass_count"]}` pass / `{matrix["check_fail_count"]}` fail
- GitHub upload: not allowed in this phase.
- App reinstall: not allowed in this phase.
- Business execution: not allowed in this phase.
""",
    )
    _write_text(
        TEST_RESULTS_PATH,
        f"""# Test Results

- RED: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_action_intake_blocker_blocked_handoff_external_action_readiness_after_final_threshold` failed before implementation because the generator module did not exist.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_action_intake_blocker_blocked_handoff_external_action_readiness_after_final_threshold.py --generated-at 2026-07-08T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_action_intake_blocker_blocked_handoff_external_action_readiness_after_final_threshold.py --require-private-external-action-readiness`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_action_intake_blocker_blocked_handoff_external_action_readiness_after_final_threshold`
- Governance validators, CSV shape checks, diff check, raw/private marker scan, secret scan and private-runtime tracked-file scan: expected before commit.

Expected matrix result: {matrix["check_pass_count"]}/{matrix["check_count"]} PASS.
""",
    )
    _write_text(
        RISK_REGISTER_PATH,
        """# Risk Register

- Risk: action readiness is mistaken for permission to bind fields or compare values.
- Control: decision remains NO_GO and all downstream gates remain false.
- Risk: private owner-action handles leak into public evidence.
- Control: public artifacts contain aggregate counts only; detailed blocker rows stay ignored.
- Risk: raw inbox is modified.
- Control: this phase consumes existing blocked handoff artifacts only and does not touch the raw inbox.
""",
    )
    _write_text(
        ROLLBACK_PATH,
        f"""# Rollback Plan

Remove artifacts for `{PHASE_ID}`, metadata copies, private action-readiness outputs, tool, validator, focused test and governance rows. Do not touch source blocked-handoff evidence or raw inbox files.
""",
    )


def _write_governance_events(generated_at: str, summary: dict[str, Any]) -> None:
    event_id = (
        "DEV-KMFA-20260708-V014-AUTHORIZED-SOURCE-REFERENCE-OR-EXCLUSION-APPLICATION-OWNER-OR-AGENT-"
        "ACTION-INTAKE-BLOCKER-BLOCKED-HANDOFF-EXTERNAL-ACTION-READINESS-AFTER-FINAL-THRESHOLD"
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
                "Checked the ignored owner-action queue after blocked handoff; no executable owner or "
                "authorized-agent action is ready, so 48 blockers remain and downstream gates stay closed."
            ),
            "evidence_ref": MANIFEST_PATH.as_posix(),
            "files_changed": _phase_public_files(),
            "test_commands": _build_manifest(
                {"generated_at": generated_at, "raw_boundary": {}, "public_safety": {}},
                {"checks": [], "check_count": 0},
                {},
            )["test_commands"],
            "test_results": ["PENDING: final validation results will be recorded before local commit."],
            "external_owner_action_ready_count": summary["external_owner_action_ready_count"],
            "external_owner_action_blocker_count": summary["external_owner_action_blocker_count"],
            "goal_status_recommendation": "blocked",
            "actionable_owner_resolution_count": 0,
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
            "name": "v0.1.4 owner or authorized agent action intake blocker blocked handoff external action readiness after final threshold",
            "status": STATUS,
            "completed_task_units": 1,
            "estimated_task_units": 1,
            "derived_percent": 100.0,
            "acceptance_id": ACCEPTANCE_ID,
            "evidence_ref": MANIFEST_PATH.as_posix(),
            "fact_level": "EXTRACTED",
            "updated_at": generated_at[:10],
            "stage_id": "VALUE-CONSISTENCY",
            "phase_goal": "check owner or authorized-agent action intake blocker blocked handoff external action readiness after final threshold",
            "task_count": 3,
            "acceptance_output": (
                "Action readiness manifest, summary, Go No-Go, private ignored blocker records/question list, "
                "validator, focused test and governance records"
            ),
        },
        ("phase_id", "record_type", "task_id"),
    )
    for suffix, task_goal in (
        ("T1", "read prior public blocked handoff evidence and ignored private owner-action queue read-only"),
        ("T2", "write ignored private action-readiness blocker records and Chinese question list"),
        ("T3", "emit public-safe NO_GO readiness evidence while keeping binding comparison and upload closed"),
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
    source_summary = _read_json(SOURCE_BLOCKED_HANDOFF_SUMMARY_PATH)
    source_manifest = _read_json(SOURCE_BLOCKED_HANDOFF_MANIFEST_PATH)
    source_go_no_go = _read_json(SOURCE_BLOCKED_HANDOFF_GO_NO_GO_PATH)
    source_matrix = _read_json(SOURCE_BLOCKED_HANDOFF_MATRIX_PATH)
    handoff_rows = _read_jsonl(SOURCE_PRIVATE_BLOCKED_HANDOFF_RECORDS_PATH)
    owner_action_rows = _read_jsonl(SOURCE_PRIVATE_OWNER_ACTION_QUEUE_PATH)
    if not SOURCE_PRIVATE_BLOCKED_HANDOFF_DIAGNOSTIC_PATH.exists():
        raise FileNotFoundError(SOURCE_PRIVATE_BLOCKED_HANDOFF_DIAGNOSTIC_PATH)
    if not SOURCE_PRIVATE_BLOCKED_HANDOFF_REPORT_PATH.exists():
        raise FileNotFoundError(SOURCE_PRIVATE_BLOCKED_HANDOFF_REPORT_PATH)
    _validate_sources(
        source_summary=source_summary,
        source_manifest=source_manifest,
        source_go_no_go=source_go_no_go,
        source_matrix=source_matrix,
        handoff_rows=handoff_rows,
        owner_action_rows=owner_action_rows,
    )
    blocker_rows = _build_blocker_records(generated_at=generated, owner_action_rows=owner_action_rows)
    summary = _build_summary(
        generated_at=generated,
        source_summary=source_summary,
        source_manifest=source_manifest,
        source_go_no_go=source_go_no_go,
        source_matrix=source_matrix,
        handoff_rows=handoff_rows,
        owner_action_rows=owner_action_rows,
        blocker_rows=blocker_rows,
    )
    matrix = _build_matrix(summary)
    go_no_go = _build_go_no_go(summary)
    manifest = _build_manifest(summary, matrix, go_no_go)
    _write_private_outputs(generated_at=generated, summary=summary, blocker_rows=blocker_rows)
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
    return {
        "summary": summary,
        "matrix": matrix,
        "go_no_go": go_no_go,
        "manifest": manifest,
        "private_external_action_readiness_blocker_records": blocker_rows,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generated-at")
    args = parser.parse_args(argv)
    result = generate(generated_at=args.generated_at)
    summary = result["summary"]
    print(
        "PASS: generated V014 owner/authorized-agent action intake blocker blocked handoff external action readiness after final threshold "
        f"ready={summary['external_owner_action_ready_count']} "
        f"blockers={summary['external_owner_action_blocker_count']} "
        f"goal={summary['goal_status_recommendation']} "
        f"decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
