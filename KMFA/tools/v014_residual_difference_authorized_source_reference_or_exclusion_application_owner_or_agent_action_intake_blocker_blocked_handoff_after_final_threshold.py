#!/usr/bin/env python3
"""Prepare blocked handoff after action-intake blocker final threshold.

This phase consumes the previous public-safe final-threshold recheck evidence
and ignored private final-threshold records. It prepares a private blocked
handoff and owner-action queue while keeping public artifacts aggregate-only.
It does not read the raw inbox, bind authoritative fingerprints, compare raw
and processed values, upload, reinstall, or execute business use.
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
    v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_action_intake_blocker_final_threshold_recheck_after_blocked_handoff
    as source_final_threshold,
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
    "ACTION_INTAKE_BLOCKER_BLOCKED_HANDOFF_AFTER_FINAL_THRESHOLD"
)
TASK_ID = (
    "KMFA-V014-RESIDUAL-DIFFERENCE-AUTHORIZED-SOURCE-REFERENCE-OR-EXCLUSION-APPLICATION-OWNER-OR-"
    "AGENT-ACTION-INTAKE-BLOCKER-BLOCKED-HANDOFF-AFTER-FINAL-THRESHOLD-20260708"
)
ACCEPTANCE_ID = (
    "ACC-V014-RESIDUAL-DIFFERENCE-AUTHORIZED-SOURCE-REFERENCE-OR-EXCLUSION-APPLICATION-OWNER-OR-"
    "AGENT-ACTION-INTAKE-BLOCKER-BLOCKED-HANDOFF-AFTER-FINAL-THRESHOLD"
)
VERSION = (
    "0.1.4-residual-difference-authorized-source-reference-or-exclusion-application-owner-or-agent-"
    "action-intake-blocker-blocked-handoff-after-final-threshold"
)
STATUS = (
    "completed_validated_local_only_authorized_source_reference_or_exclusion_application_owner_or_agent_"
    "action_intake_blocker_blocked_handoff_after_final_threshold_no_go_blocked"
)
DECISION = "NO_GO"
HANDOFF_CONCLUSION = "blocked_after_action_intake_final_threshold_requires_owner_or_authorized_agent_action"
NEXT_REQUIRED_INPUT = source_final_threshold.NEXT_REQUIRED_INPUT
NEXT_RECOMMENDED_PHASE = "owner_or_authorized_agent_action_required_before_authoritative_binding"

SOURCE_REFERENCE_DIAGNOSTIC_KIND = source_final_threshold.SOURCE_REFERENCE_DIAGNOSTIC_KIND
FORMULA_MAPPING_DIAGNOSTIC_KIND = source_final_threshold.FORMULA_MAPPING_DIAGNOSTIC_KIND

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
PREFIX = (
    "residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_"
    "action_intake_blocker_blocked_handoff_after_final_threshold"
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

SOURCE_FINAL_THRESHOLD_SUMMARY_PATH = source_final_threshold.METADATA_SUMMARY_PATH
SOURCE_FINAL_THRESHOLD_MANIFEST_PATH = source_final_threshold.METADATA_MANIFEST_PATH
SOURCE_FINAL_THRESHOLD_GO_NO_GO_PATH = source_final_threshold.METADATA_GO_NO_GO_PATH
SOURCE_FINAL_THRESHOLD_MATRIX_PATH = source_final_threshold.METADATA_MATRIX_PATH
SOURCE_ACTION_INTAKE_BLOCKER_FINAL_THRESHOLD_SUMMARY_PATH = SOURCE_FINAL_THRESHOLD_SUMMARY_PATH
SOURCE_ACTION_INTAKE_BLOCKER_FINAL_THRESHOLD_MANIFEST_PATH = SOURCE_FINAL_THRESHOLD_MANIFEST_PATH
SOURCE_ACTION_INTAKE_BLOCKER_FINAL_THRESHOLD_GO_NO_GO_PATH = SOURCE_FINAL_THRESHOLD_GO_NO_GO_PATH
SOURCE_ACTION_INTAKE_BLOCKER_FINAL_THRESHOLD_MATRIX_PATH = SOURCE_FINAL_THRESHOLD_MATRIX_PATH
SOURCE_PRIVATE_ACTION_INTAKE_BLOCKER_FINAL_THRESHOLD_DIAGNOSTIC_PATH = (
    source_final_threshold.PRIVATE_ACTION_INTAKE_BLOCKER_FINAL_THRESHOLD_DIAGNOSTIC_PATH
)
SOURCE_PRIVATE_ACTION_INTAKE_BLOCKER_FINAL_THRESHOLD_RECORDS_PATH = (
    source_final_threshold.PRIVATE_ACTION_INTAKE_BLOCKER_FINAL_THRESHOLD_RECORDS_PATH
)
SOURCE_PRIVATE_ACTION_INTAKE_BLOCKER_FINAL_THRESHOLD_REPORT_PATH = (
    source_final_threshold.PRIVATE_ACTION_INTAKE_BLOCKER_FINAL_THRESHOLD_REPORT_PATH
)

PRIVATE_OUTPUT_DIR = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_action_intake_blocker_blocked_handoff_after_final_threshold"
)
PRIVATE_ACTION_INTAKE_BLOCKER_BLOCKED_HANDOFF_DIAGNOSTIC_PATH = (
    PRIVATE_OUTPUT_DIR / "private_owner_or_agent_action_intake_blocker_blocked_handoff_diagnostic.json"
)
PRIVATE_ACTION_INTAKE_BLOCKER_BLOCKED_HANDOFF_RECORDS_PATH = (
    PRIVATE_OUTPUT_DIR / "private_owner_or_agent_action_intake_blocker_blocked_handoff_records.jsonl"
)
PRIVATE_ACTION_INTAKE_BLOCKER_OWNER_ACTION_QUEUE_PATH = (
    PRIVATE_OUTPUT_DIR / "private_owner_or_agent_action_intake_blocker_blocked_handoff_owner_action_queue.jsonl"
)
PRIVATE_ACTION_INTAKE_BLOCKER_BLOCKED_HANDOFF_REPORT_PATH = (
    PRIVATE_OUTPUT_DIR / "private_owner_or_agent_action_intake_blocker_blocked_handoff_report.md"
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
        "KMFA/tests/test_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_action_intake_blocker_blocked_handoff_after_final_threshold.py",
        "KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_action_intake_blocker_blocked_handoff_after_final_threshold.py",
        "KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_action_intake_blocker_blocked_handoff_after_final_threshold.py",
        "KMFA/功能清单.md",
        "KMFA/开发记录.md",
        "KMFA/模型参数文件.md",
    ]


def _raw_boundary() -> dict[str, bool]:
    return {
        "user_declared_raw_data_immutable": True,
        "raw_data_root_readonly_policy_active": True,
        "source_final_threshold_public_artifacts_read_by_this_phase": True,
        "source_final_threshold_manifest_read_by_this_phase": True,
        "source_final_threshold_go_no_go_read_by_this_phase": True,
        "source_final_threshold_matrix_read_by_this_phase": True,
        "source_private_action_intake_blocker_final_threshold_diagnostic_read_by_this_phase": True,
        "source_private_action_intake_blocker_final_threshold_records_read_by_this_phase": True,
        "source_private_action_intake_blocker_final_threshold_report_existence_checked_by_this_phase": True,
        "private_action_intake_blocker_blocked_handoff_diagnostic_written_by_this_phase": True,
        "private_action_intake_blocker_blocked_handoff_records_written_by_this_phase": True,
        "private_action_intake_blocker_owner_action_queue_written_by_this_phase": True,
        "private_action_intake_blocker_blocked_handoff_report_written_by_this_phase": True,
        "source_private_action_intake_blocker_final_threshold_diagnostic_mutated_by_this_phase": False,
        "source_private_action_intake_blocker_final_threshold_records_mutated_by_this_phase": False,
        "source_private_action_intake_blocker_final_threshold_report_mutated_by_this_phase": False,
        "owner_or_agent_action_completed_by_this_phase": False,
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
        "source_private_action_intake_blocker_final_threshold_diagnostic_committed": False,
        "source_private_action_intake_blocker_final_threshold_records_committed": False,
        "source_private_action_intake_blocker_final_threshold_report_committed": False,
        "private_action_intake_blocker_blocked_handoff_diagnostic_committed": False,
        "private_action_intake_blocker_blocked_handoff_records_committed": False,
        "private_action_intake_blocker_owner_action_queue_committed": False,
        "private_action_intake_blocker_blocked_handoff_report_committed": False,
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


def _owner_action_type(diagnostic_kind: str) -> str:
    if diagnostic_kind == SOURCE_REFERENCE_DIAGNOSTIC_KIND:
        return "provide_actionable_source_reference_or_owner_exclusion"
    if diagnostic_kind == FORMULA_MAPPING_DIAGNOSTIC_KIND:
        return "provide_formula_or_non_numeric_mapping"
    return "provide_owner_authorized_actionable_diagnostic_response"


def _build_private_records(
    *, generated_at: str, final_rows: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    handoff_rows: list[dict[str, Any]] = []
    owner_action_rows: list[dict[str, Any]] = []
    for index, row in enumerate(final_rows, start=1):
        diagnostic_kind = str(row.get("diagnostic_kind"))
        if row.get("action_intake_blocker_final_threshold_status") != source_final_threshold.FINAL_THRESHOLD_CONCLUSION:
            raise ValueError("source final-threshold row is not blocked")
        if row.get("action_intake_blocker_observation_count") != 3:
            raise ValueError("source final-threshold row must be third observation")
        if row.get("action_intake_blocked_audit_threshold_met") is not True:
            raise ValueError("source final-threshold row must be threshold-met")
        if row.get("goal_status_recommendation") != "blocked":
            raise ValueError("source final-threshold row must recommend blocked goal")
        if row.get("actionable_owner_resolution_ready") is not False:
            raise ValueError("source final-threshold row cannot be actionable")

        owner_action_item_id = f"ASR-OE-APP-OWNER-AGENT-ACTION-INTAKE-BLOCKER-OWNER-ACTION-{index:03d}"
        handoff = {
            "blocked_handoff_item_id": f"ASR-OE-APP-OWNER-AGENT-ACTION-INTAKE-BLOCKER-BLOCKED-HANDOFF-{index:03d}",
            "owner_action_item_id": owner_action_item_id,
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "generated_at": generated_at,
            "source_action_intake_blocker_final_threshold_item_id": row.get(
                "action_intake_blocker_final_threshold_item_id"
            ),
            "source_action_intake_blocker_threshold_item_id": row.get(
                "source_action_intake_blocker_threshold_item_id"
            ),
            "source_action_intake_item_id": row.get("source_action_intake_item_id"),
            "source_action_readiness_item_id": row.get("source_action_readiness_item_id"),
            "source_owner_action_item_id": row.get("source_owner_action_item_id"),
            "source_blocked_handoff_item_id": row.get("source_blocked_handoff_item_id"),
            "target_slot_id": row.get("target_slot_id"),
            "diagnostic_kind": diagnostic_kind,
            "blocked_handoff_status": HANDOFF_CONCLUSION,
            "owner_action_required": True,
            "owner_or_authorized_agent_required": True,
            "owner_action_status": "required_before_binding_or_value_comparison",
            "owner_action_type": _owner_action_type(diagnostic_kind),
            "prior_action_intake_blocker_observation_count": 2,
            "action_intake_blocker_observation_count": 3,
            "action_intake_blocked_audit_threshold_met": True,
            "goal_status_recommendation": "blocked",
            "actionable_owner_resolution_ready": False,
            "source_reference_or_owner_exclusion_owner_action_required": (
                diagnostic_kind == SOURCE_REFERENCE_DIAGNOSTIC_KIND
            ),
            "formula_or_non_numeric_mapping_owner_action_required": (
                diagnostic_kind == FORMULA_MAPPING_DIAGNOSTIC_KIND
            ),
            "binding_ready_after_blocked_handoff": False,
            "comparison_retry_ready_after_blocked_handoff": False,
            "safe_auto_resolution_available": False,
            "authoritative_binding_application_ready": False,
            "authoritative_binding_applied_by_this_phase": False,
            "raw_candidate_fingerprint_bound_by_this_phase": False,
            "raw_to_processed_value_comparison_performed_by_this_phase": False,
            "business_value_consistency_verified": False,
            "full_raw_to_processed_value_comparison_complete": False,
            "public_commit_allowed": False,
        }
        owner_action = {
            "owner_action_item_id": owner_action_item_id,
            "blocked_handoff_item_id": handoff["blocked_handoff_item_id"],
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "generated_at": generated_at,
            "target_slot_id": row.get("target_slot_id"),
            "diagnostic_kind": diagnostic_kind,
            "owner_action_status": "required_before_binding_or_value_comparison",
            "owner_action_type": handoff["owner_action_type"],
            "owner_or_authorized_agent_required": True,
            "actionable_owner_resolution_required": True,
            "action_intake_blocked_audit_threshold_met": True,
            "goal_status_recommendation": "blocked",
            "authoritative_binding_application_ready": False,
            "raw_to_processed_value_comparison_ready": False,
            "public_commit_allowed": False,
        }
        handoff_rows.append(handoff)
        owner_action_rows.append(owner_action)
    return handoff_rows, owner_action_rows


def _validate_sources(
    *,
    source_summary: dict[str, Any],
    source_manifest: dict[str, Any],
    source_go_no_go: dict[str, Any],
    source_matrix: dict[str, Any],
    final_rows: list[dict[str, Any]],
) -> None:
    if source_summary.get("phase_id") != source_final_threshold.PHASE_ID:
        raise ValueError("source final-threshold phase mismatch")
    if source_manifest.get("phase_id") != source_final_threshold.PHASE_ID:
        raise ValueError("source final-threshold manifest phase mismatch")
    if source_go_no_go.get("decision") != "NO_GO":
        raise ValueError("source final-threshold decision must be NO_GO")
    if source_matrix.get("check_fail_count") != 0:
        raise ValueError("source final-threshold matrix must be clean")
    if source_summary.get("private_final_threshold_records_item_count") != 48:
        raise ValueError("source final-threshold item count must be 48")
    if source_summary.get("owner_action_intake_blocker_count") != 48:
        raise ValueError("source action-intake blocker count must be 48")
    if source_summary.get("owner_action_intake_ready_count") != 0:
        raise ValueError("source action-intake ready count must be 0")
    if source_summary.get("action_intake_blocked_audit_threshold_met") is not True:
        raise ValueError("source final-threshold audit threshold must be met")
    if source_summary.get("goal_status_recommendation") != "blocked":
        raise ValueError("source final-threshold goal status must be blocked")
    if len(final_rows) != 48:
        raise ValueError("source private final-threshold records must contain 48 rows")


def _build_summary(
    *,
    generated_at: str,
    source_summary: dict[str, Any],
    source_manifest: dict[str, Any],
    source_go_no_go: dict[str, Any],
    source_matrix: dict[str, Any],
    final_rows: list[dict[str, Any]],
    handoff_rows: list[dict[str, Any]],
    owner_action_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    counts = Counter(str(row.get("diagnostic_kind")) for row in handoff_rows)
    return {
        "schema_version": (
            "kmfa.v014_authorized_source_reference_or_exclusion_application_owner_or_agent_action_intake_"
            "blocker_blocked_handoff_after_final_threshold_summary.v1"
        ),
        "record_type": (
            "v014_authorized_source_reference_or_exclusion_application_owner_or_agent_action_intake_"
            "blocker_blocked_handoff_after_final_threshold_summary"
        ),
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
        "source_action_intake_blocker_final_threshold_recheck_item_count": source_summary.get(
            "private_final_threshold_records_item_count"
        ),
        "source_owner_action_intake_blocker_count": source_summary.get("owner_action_intake_blocker_count"),
        "source_owner_action_intake_ready_count": source_summary.get("owner_action_intake_ready_count"),
        "source_private_action_intake_blocker_final_threshold_records_item_count": len(final_rows),
        "blocked_handoff_item_count": len(handoff_rows),
        "owner_action_item_count": len(owner_action_rows),
        "goal_status_recommendation": "blocked",
        "action_intake_blocked_audit_threshold_met": True,
        "owner_action_intake_ready_count": 0,
        "owner_action_intake_blocker_count": len(handoff_rows),
        "valid_owner_action_intake_blocker_count": len(handoff_rows),
        "actionable_owner_resolution_count": 0,
        "source_reference_or_owner_exclusion_owner_action_count": counts[SOURCE_REFERENCE_DIAGNOSTIC_KIND],
        "formula_or_non_numeric_mapping_owner_action_count": counts[FORMULA_MAPPING_DIAGNOSTIC_KIND],
        "binding_ready_after_blocked_handoff_count": 0,
        "comparison_retry_ready_after_blocked_handoff_count": 0,
        "unresolved_difference_count": source_summary.get("unresolved_difference_count"),
        "private_action_intake_blocker_blocked_handoff_diagnostic_written": True,
        "private_action_intake_blocker_blocked_handoff_records_written": True,
        "private_action_intake_blocker_owner_action_queue_written": True,
        "private_action_intake_blocker_blocked_handoff_report_written": True,
        "private_action_intake_blocker_blocked_handoff_diagnostic_gitignored": _git_check_ignored(
            PRIVATE_ACTION_INTAKE_BLOCKER_BLOCKED_HANDOFF_DIAGNOSTIC_PATH
        ),
        "private_action_intake_blocker_blocked_handoff_records_gitignored": _git_check_ignored(PRIVATE_ACTION_INTAKE_BLOCKER_BLOCKED_HANDOFF_RECORDS_PATH),
        "private_action_intake_blocker_owner_action_queue_gitignored": _git_check_ignored(PRIVATE_ACTION_INTAKE_BLOCKER_OWNER_ACTION_QUEUE_PATH),
        "private_action_intake_blocker_blocked_handoff_report_gitignored": _git_check_ignored(PRIVATE_ACTION_INTAKE_BLOCKER_BLOCKED_HANDOFF_REPORT_PATH),
        "source_private_action_intake_blocker_final_threshold_diagnostic_gitignored": _git_check_ignored(
            SOURCE_PRIVATE_ACTION_INTAKE_BLOCKER_FINAL_THRESHOLD_DIAGNOSTIC_PATH
        ),
        "source_private_action_intake_blocker_final_threshold_records_gitignored": _git_check_ignored(
            SOURCE_PRIVATE_ACTION_INTAKE_BLOCKER_FINAL_THRESHOLD_RECORDS_PATH
        ),
        "source_private_action_intake_blocker_final_threshold_report_gitignored": _git_check_ignored(
            SOURCE_PRIVATE_ACTION_INTAKE_BLOCKER_FINAL_THRESHOLD_REPORT_PATH
        ),
        "blocked_handoff_prepared_by_this_phase": True,
        "owner_action_queue_prepared_by_this_phase": True,
        "owner_or_agent_action_completed_by_this_phase": False,
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
        ("source_final_threshold_phase_loaded", summary["source_phase_id"] == source_final_threshold.PHASE_ID),
        ("source_go_no_go_preserved", summary["source_go_no_go_decision"] == "NO_GO"),
        ("source_matrix_clean", summary["source_matrix_check_fail_count"] == 0),
        (
            "source_final_threshold_complete",
            summary["source_action_intake_blocker_final_threshold_recheck_item_count"] == 48,
        ),
        ("source_blockers_complete", summary["source_owner_action_intake_blocker_count"] == 48),
        (
            "source_private_final_threshold_records_complete",
            summary["source_private_action_intake_blocker_final_threshold_records_item_count"] == 48,
        ),
        ("blocked_handoff_complete", summary["blocked_handoff_item_count"] == 48),
        ("owner_action_queue_complete", summary["owner_action_item_count"] == 48),
        (
            "blocked_goal_preserved",
            summary["goal_status_recommendation"] == "blocked"
            and summary["action_intake_blocked_audit_threshold_met"] is True,
        ),
        (
            "diagnostic_kind_owner_action_counts_locked",
            summary["source_reference_or_owner_exclusion_owner_action_count"] == 40
            and summary["formula_or_non_numeric_mapping_owner_action_count"] == 8,
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
            "kmfa.v014_authorized_source_reference_or_exclusion_application_owner_or_agent_action_intake_"
            "blocker_blocked_handoff_after_final_threshold_matrix_public_safe.v1"
        ),
        "record_type": (
            "v014_authorized_source_reference_or_exclusion_application_owner_or_agent_action_intake_"
            "blocker_blocked_handoff_after_final_threshold_matrix_public_safe"
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
            "kmfa.v014_authorized_source_reference_or_exclusion_application_owner_or_agent_action_intake_"
            "blocker_blocked_handoff_after_final_threshold_go_no_go.v1"
        ),
        "record_type": (
            "v014_authorized_source_reference_or_exclusion_application_owner_or_agent_action_intake_"
            "blocker_blocked_handoff_after_final_threshold_go_no_go"
        ),
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
        "goal_status_recommendation": "blocked",
        "action_intake_blocked_audit_threshold_met": True,
        "owner_action_intake_ready_count": 0,
        "owner_action_intake_blocker_count": summary["owner_action_intake_blocker_count"],
        "actionable_owner_resolution_count": 0,
        "source_reference_or_owner_exclusion_owner_action_count": summary[
            "source_reference_or_owner_exclusion_owner_action_count"
        ],
        "formula_or_non_numeric_mapping_owner_action_count": summary[
            "formula_or_non_numeric_mapping_owner_action_count"
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
            "kmfa.v014_authorized_source_reference_or_exclusion_application_owner_or_agent_action_intake_"
            "blocker_blocked_handoff_after_final_threshold_manifest.v1"
        ),
        "record_type": (
            "v014_authorized_source_reference_or_exclusion_application_owner_or_agent_action_intake_"
            "blocker_blocked_handoff_after_final_threshold_manifest"
        ),
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
            "source_final_threshold_public_summary": "public_safe_metadata_copy",
            "source_final_threshold_public_manifest": "public_safe_metadata_copy",
            "source_final_threshold_public_go_no_go": "public_safe_metadata_copy",
            "source_final_threshold_public_matrix": "public_safe_metadata_copy",
            "source_private_action_intake_blocker_final_threshold_diagnostic": "ignored_private_runtime",
            "source_private_action_intake_blocker_final_threshold_records": "ignored_private_runtime",
            "source_private_action_intake_blocker_final_threshold_report": "ignored_private_runtime",
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
            "private:owner_or_agent_action_intake_blocker_blocked_handoff_diagnostic",
            "private:owner_or_agent_action_intake_blocker_blocked_handoff_records",
            "private:owner_or_agent_action_intake_blocker_blocked_handoff_owner_action_queue",
            "private:owner_or_agent_action_intake_blocker_blocked_handoff_report",
        ],
        "raw_boundary": summary["raw_boundary"],
        "public_safety": summary["public_safety"],
        "test_commands": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_action_intake_blocker_blocked_handoff_after_final_threshold.py --generated-at 2026-07-08T00:00:00+10:00",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_action_intake_blocker_blocked_handoff_after_final_threshold.py --require-private-blocked-handoff",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_action_intake_blocker_blocked_handoff_after_final_threshold",
        ],
        "git": {
            "branch": _git_output(["branch", "--show-current"]),
            "head": "local_commit_recorded_after_validation",
            "status_short_branch": "omitted_for_reproducible_phase_manifest",
            "changed_kmfa_files": _phase_public_files(),
        },
    }


def _write_private_outputs(
    *,
    generated_at: str,
    summary: dict[str, Any],
    handoff_rows: list[dict[str, Any]],
    owner_action_rows: list[dict[str, Any]],
) -> None:
    counts = Counter(str(row.get("diagnostic_kind")) for row in handoff_rows)
    _write_json(
        PRIVATE_ACTION_INTAKE_BLOCKER_BLOCKED_HANDOFF_DIAGNOSTIC_PATH,
        {
            "schema_version": (
                "kmfa.private.v014_authorized_source_reference_or_exclusion_application_owner_or_agent_action_intake_"
                "blocker_blocked_handoff_after_final_threshold.v1"
            ),
            "classification": "private_owner_or_agent_action_intake_blocker_blocked_handoff_do_not_commit",
            "record_type": (
                "v014_authorized_source_reference_or_exclusion_application_owner_or_agent_action_intake_"
                "blocker_blocked_handoff_after_final_threshold_private_diagnostic"
            ),
            "project_id": "KMFA",
            "version": VERSION,
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "generated_at": generated_at,
            "blocked_handoff_rows": handoff_rows,
            "owner_action_queue_rows": owner_action_rows,
            "summary_private": {
                "blocked_handoff_item_count": len(handoff_rows),
                "owner_action_item_count": len(owner_action_rows),
                "goal_status_recommendation": "blocked",
                "action_intake_blocked_audit_threshold_met": True,
                "source_reference_or_owner_exclusion_owner_action_count": counts[SOURCE_REFERENCE_DIAGNOSTIC_KIND],
                "formula_or_non_numeric_mapping_owner_action_count": counts[FORMULA_MAPPING_DIAGNOSTIC_KIND],
                "binding_ready_after_blocked_handoff_count": 0,
                "comparison_retry_ready_after_blocked_handoff_count": 0,
                "business_value_consistency_verified": False,
            },
            "raw_boundary": summary["raw_boundary"],
        },
    )
    _write_jsonl(PRIVATE_ACTION_INTAKE_BLOCKER_BLOCKED_HANDOFF_RECORDS_PATH, handoff_rows)
    _write_jsonl(PRIVATE_ACTION_INTAKE_BLOCKER_OWNER_ACTION_QUEUE_PATH, owner_action_rows)
    _write_text(
        PRIVATE_ACTION_INTAKE_BLOCKER_BLOCKED_HANDOFF_REPORT_PATH,
        "\n".join(
            [
                "# Private Action Intake Blocker Blocked Handoff After Final Threshold Report",
                "",
                f"- phase_id: `{PHASE_ID}`",
                f"- blocked_handoff_item_count: `{len(handoff_rows)}`",
                f"- owner_action_item_count: `{len(owner_action_rows)}`",
                "- goal_status_recommendation: `blocked`",
                "- action_intake_blocked_audit_threshold_met: `true`",
                "- authoritative_binding_application_ready: `false`",
                "- raw_to_processed_value_comparison_ready: `false`",
                "- raw_inbox_mutated_by_this_phase: `false`",
                "",
                "Private handoff rows may contain private handles and must remain ignored.",
                "",
            ]
        ),
    )


def _write_human(summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any]) -> None:
    _write_text(
        REPORT_PATH,
        f"""# V014 Action Intake Blocker Blocked Handoff After Final Threshold

Generated at: {summary["generated_at"]}

## Scope

- Phase: `{PHASE_ID}`
- Decision: `{DECISION}`
- Status: `{STATUS}`
- Source: prior public-safe action-intake blocker final-threshold evidence plus ignored private final-threshold records.
- Raw boundary: no raw inbox read, list, stat, parse, value extraction, write, delete, move, rename, copy, normalize or mutation.

## Public-Safe Handoff Result

- Source final-threshold items: `{summary["source_action_intake_blocker_final_threshold_recheck_item_count"]}`
- Source action-intake blockers: `{summary["source_owner_action_intake_blocker_count"]}`
- Source private final-threshold records: `{summary["source_private_action_intake_blocker_final_threshold_records_item_count"]}`
- Blocked handoff items: `{summary["blocked_handoff_item_count"]}`
- Owner action items: `{summary["owner_action_item_count"]}`
- Goal status recommendation: `{summary["goal_status_recommendation"]}`
- Action-intake blocked audit threshold met: `{str(summary["action_intake_blocked_audit_threshold_met"]).lower()}`
- Source reference or owner exclusion owner actions: `{summary["source_reference_or_owner_exclusion_owner_action_count"]}`
- Formula or non-numeric mapping owner actions: `{summary["formula_or_non_numeric_mapping_owner_action_count"]}`
- Binding ready after blocked handoff: `{summary["binding_ready_after_blocked_handoff_count"]}`
- Comparison retry ready after blocked handoff: `{summary["comparison_retry_ready_after_blocked_handoff_count"]}`
- Unresolved differences: `{summary["unresolved_difference_count"]}`

## Gate

The final-threshold blocker has moved to a blocked handoff queue only. This phase does not authorize binding, raw-to-processed value comparison, reconciliation, business consistency, GitHub upload, app reinstall or business execution.

Next required input: `{NEXT_REQUIRED_INPUT}`.
""",
    )
    _write_text(
        GO_NO_GO_RECORD_PATH,
        f"""# Go / No-Go Record

- Phase: `{PHASE_ID}`
- Decision: `{go_no_go["decision"]}`
- Reason: `{HANDOFF_CONCLUSION}`
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

- RED: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_action_intake_blocker_blocked_handoff_after_final_threshold` failed before implementation because the generator module did not exist.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_action_intake_blocker_blocked_handoff_after_final_threshold.py --generated-at 2026-07-08T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_action_intake_blocker_blocked_handoff_after_final_threshold.py --require-private-blocked-handoff`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_action_intake_blocker_blocked_handoff_after_final_threshold`
- Governance validators, CSV shape checks, diff check, raw/private marker scan, secret scan and private-runtime tracked-file scan: expected before commit.

Expected matrix result: {matrix["check_pass_count"]}/{matrix["check_count"]} PASS.
""",
    )
    _write_text(
        RISK_REGISTER_PATH,
        """# Risk Register

- Risk: blocked handoff is mistaken for permission to bind fields or compare values.
- Control: decision remains NO_GO and all downstream gates remain false.
- Risk: private owner-action handles leak into public evidence.
- Control: public artifacts contain aggregate counts only; handoff and owner-action rows stay ignored.
- Risk: raw inbox is modified.
- Control: this phase consumes existing ignored private final-threshold artifacts only and does not touch the raw inbox.
""",
    )
    _write_text(
        ROLLBACK_PATH,
        f"""# Rollback Plan

Remove artifacts for `{PHASE_ID}`, metadata copies, private blocked-handoff outputs, tool, validator, focused test and governance rows. Do not touch source final-threshold evidence or raw inbox files.
""",
    )


def _write_governance_events(generated_at: str, summary: dict[str, Any]) -> None:
    event_id = (
        "DEV-KMFA-20260708-V014-AUTHORIZED-SOURCE-REFERENCE-OR-EXCLUSION-APPLICATION-OWNER-OR-AGENT-"
        "ACTION-INTAKE-BLOCKER-BLOCKED-HANDOFF-AFTER-FINAL-THRESHOLD"
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
                "Prepared public-safe blocked handoff and ignored private owner-action queue for 48 owner/authorized-agent "
                "action-intake final-threshold blockers; binding, comparison and upload gates remain closed."
            ),
            "evidence_ref": MANIFEST_PATH.as_posix(),
            "files_changed": _phase_public_files(),
            "test_commands": [
                "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_action_intake_blocker_blocked_handoff_after_final_threshold.py --generated-at 2026-07-08T00:00:00+10:00",
                "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_action_intake_blocker_blocked_handoff_after_final_threshold.py --require-private-blocked-handoff",
                "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_action_intake_blocker_blocked_handoff_after_final_threshold",
            ],
            "test_results": ["PENDING: final validation results will be recorded before local commit."],
            "blocked_handoff_item_count": summary["blocked_handoff_item_count"],
            "owner_action_item_count": summary["owner_action_item_count"],
            "goal_status_recommendation": "blocked",
            "action_intake_blocked_audit_threshold_met": True,
            "owner_action_intake_blocker_count": summary["owner_action_intake_blocker_count"],
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
            "name": "v0.1.4 owner/agent action-intake blocker blocked handoff after final threshold",
            "status": STATUS,
            "completed_task_units": 1,
            "estimated_task_units": 1,
            "derived_percent": 100.0,
            "acceptance_id": ACCEPTANCE_ID,
            "evidence_ref": MANIFEST_PATH.as_posix(),
            "fact_level": "EXTRACTED",
            "updated_at": generated_at[:10],
            "stage_id": "VALUE-CONSISTENCY",
            "phase_goal": "prepare blocked handoff and owner action queue after final action-intake blocker threshold",
            "task_count": 3,
            "acceptance_output": (
                "Blocked handoff manifest, summary, Go No-Go, private ignored owner-action queue, validator, "
                "focused test and governance records"
            ),
        },
        ("phase_id", "record_type", "task_id"),
    )
    for suffix, task_goal in (
        ("T1", "read prior public final-threshold evidence and ignored private final-threshold records read-only"),
        ("T2", "write ignored private blocked-handoff records and owner-action queue for 48 action-intake blockers"),
        ("T3", "emit public-safe NO_GO handoff evidence while keeping binding comparison and upload gates closed"),
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
    source_summary = _read_json(SOURCE_FINAL_THRESHOLD_SUMMARY_PATH)
    source_manifest = _read_json(SOURCE_FINAL_THRESHOLD_MANIFEST_PATH)
    source_go_no_go = _read_json(SOURCE_FINAL_THRESHOLD_GO_NO_GO_PATH)
    source_matrix = _read_json(SOURCE_FINAL_THRESHOLD_MATRIX_PATH)
    final_rows = _read_jsonl(SOURCE_PRIVATE_ACTION_INTAKE_BLOCKER_FINAL_THRESHOLD_RECORDS_PATH)
    if not SOURCE_PRIVATE_ACTION_INTAKE_BLOCKER_FINAL_THRESHOLD_DIAGNOSTIC_PATH.exists():
        raise FileNotFoundError(SOURCE_PRIVATE_ACTION_INTAKE_BLOCKER_FINAL_THRESHOLD_DIAGNOSTIC_PATH)
    if not SOURCE_PRIVATE_ACTION_INTAKE_BLOCKER_FINAL_THRESHOLD_REPORT_PATH.exists():
        raise FileNotFoundError(SOURCE_PRIVATE_ACTION_INTAKE_BLOCKER_FINAL_THRESHOLD_REPORT_PATH)
    _validate_sources(
        source_summary=source_summary,
        source_manifest=source_manifest,
        source_go_no_go=source_go_no_go,
        source_matrix=source_matrix,
        final_rows=final_rows,
    )
    handoff_rows, owner_action_rows = _build_private_records(generated_at=generated, final_rows=final_rows)
    summary = _build_summary(
        generated_at=generated,
        source_summary=source_summary,
        source_manifest=source_manifest,
        source_go_no_go=source_go_no_go,
        source_matrix=source_matrix,
        final_rows=final_rows,
        handoff_rows=handoff_rows,
        owner_action_rows=owner_action_rows,
    )
    matrix = _build_matrix(summary)
    go_no_go = _build_go_no_go(summary)
    manifest = _build_manifest(summary, matrix, go_no_go)
    _write_private_outputs(
        generated_at=generated,
        summary=summary,
        handoff_rows=handoff_rows,
        owner_action_rows=owner_action_rows,
    )
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
        "private_action_intake_blocker_blocked_handoff_records": handoff_rows,
        "private_action_intake_blocker_owner_action_queue": owner_action_rows,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generated-at")
    args = parser.parse_args(argv)
    result = generate(generated_at=args.generated_at)
    summary = result["summary"]
    print(
        "PASS: generated V014 owner/agent action-intake blocker blocked handoff after final threshold "
        f"handoff={summary['blocked_handoff_item_count']} "
        f"owner_actions={summary['owner_action_item_count']} "
        f"goal={summary['goal_status_recommendation']} "
        f"decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
