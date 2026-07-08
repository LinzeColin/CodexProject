#!/usr/bin/env python3
"""Prepare blocked handoff after external owner/agent action readiness.

This phase consumes the previous public-safe external-action-readiness evidence
and ignored private blocker records. It prepares a private blocked handoff and
owner-action reminder queue while keeping public artifacts aggregate-only. It
does not read the raw inbox, bind authoritative fingerprints, compare values,
upload, reinstall, or execute business use.
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
    v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_action_intake_blocker_blocked_handoff_external_action_readiness_after_final_threshold
    as source_readiness,
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
    "EXTERNAL_ACTION_BLOCKED_HANDOFF_AFTER_EXTERNAL_ACTION_READINESS"
)
TASK_ID = (
    "KMFA-V014-RESIDUAL-DIFFERENCE-AUTHORIZED-SOURCE-REFERENCE-OR-EXCLUSION-APPLICATION-OWNER-OR-"
    "AGENT-EXTERNAL-ACTION-BLOCKED-HANDOFF-AFTER-EXTERNAL-ACTION-READINESS-20260708"
)
ACCEPTANCE_ID = (
    "ACC-V014-RESIDUAL-DIFFERENCE-AUTHORIZED-SOURCE-REFERENCE-OR-EXCLUSION-APPLICATION-OWNER-OR-"
    "AGENT-EXTERNAL-ACTION-BLOCKED-HANDOFF-AFTER-EXTERNAL-ACTION-READINESS"
)
VERSION = (
    "0.1.4-residual-difference-authorized-source-reference-or-exclusion-application-owner-or-agent-"
    "external-action-blocked-handoff-after-external-action-readiness"
)
STATUS = (
    "completed_validated_local_only_authorized_source_reference_or_exclusion_application_owner_or_agent_"
    "external_action_blocked_handoff_after_external_action_readiness_no_go_blocked"
)
DECISION = "NO_GO"
HANDOFF_CONCLUSION = "blocked_after_external_action_readiness_requires_owner_or_authorized_agent_action"
NEXT_REQUIRED_INPUT = source_readiness.NEXT_REQUIRED_INPUT
NEXT_RECOMMENDED_PHASE = "owner_or_authorized_agent_external_action_required_before_authoritative_binding"

SOURCE_REFERENCE_DIAGNOSTIC_KIND = source_readiness.SOURCE_REFERENCE_DIAGNOSTIC_KIND
FORMULA_MAPPING_DIAGNOSTIC_KIND = source_readiness.FORMULA_MAPPING_DIAGNOSTIC_KIND

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
PREFIX = (
    "residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_"
    "external_action_blocked_handoff_after_external_action_readiness"
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

SOURCE_EXTERNAL_ACTION_READINESS_SUMMARY_PATH = source_readiness.METADATA_SUMMARY_PATH
SOURCE_EXTERNAL_ACTION_READINESS_MANIFEST_PATH = source_readiness.METADATA_MANIFEST_PATH
SOURCE_EXTERNAL_ACTION_READINESS_GO_NO_GO_PATH = source_readiness.METADATA_GO_NO_GO_PATH
SOURCE_EXTERNAL_ACTION_READINESS_MATRIX_PATH = source_readiness.METADATA_MATRIX_PATH
SOURCE_PRIVATE_EXTERNAL_ACTION_READINESS_DIAGNOSTIC_PATH = (
    source_readiness.PRIVATE_EXTERNAL_ACTION_READINESS_DIAGNOSTIC_PATH
)
SOURCE_PRIVATE_EXTERNAL_ACTION_READINESS_BLOCKER_RECORDS_PATH = (
    source_readiness.PRIVATE_EXTERNAL_ACTION_READINESS_BLOCKER_RECORDS_PATH
)
SOURCE_PRIVATE_EXTERNAL_ACTION_READINESS_QUESTION_LIST_PATH = (
    source_readiness.PRIVATE_EXTERNAL_ACTION_READINESS_QUESTION_LIST_PATH
)

PRIVATE_OUTPUT_DIR = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_external_action_blocked_handoff_after_external_action_readiness"
)
PRIVATE_EXTERNAL_ACTION_BLOCKED_HANDOFF_DIAGNOSTIC_PATH = (
    PRIVATE_OUTPUT_DIR / "private_owner_or_agent_external_action_blocked_handoff_diagnostic.json"
)
PRIVATE_EXTERNAL_ACTION_BLOCKED_HANDOFF_RECORDS_PATH = (
    PRIVATE_OUTPUT_DIR / "private_owner_or_agent_external_action_blocked_handoff_records.jsonl"
)
PRIVATE_OWNER_ACTION_REMINDER_QUEUE_PATH = (
    PRIVATE_OUTPUT_DIR / "private_owner_or_agent_external_action_owner_action_reminder_queue.jsonl"
)
PRIVATE_OWNER_ACTION_REMINDER_REPORT_PATH = (
    PRIVATE_OUTPUT_DIR / "private_owner_or_agent_external_action_owner_action_reminder_report.md"
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
            "owner_or_agent_external_action_blocked_handoff_after_external_action_readiness.py"
        ),
        (
            "KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_"
            "owner_or_agent_external_action_blocked_handoff_after_external_action_readiness.py"
        ),
        (
            "KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_"
            "owner_or_agent_external_action_blocked_handoff_after_external_action_readiness.py"
        ),
        "KMFA/功能清单.md",
        "KMFA/开发记录.md",
        "KMFA/模型参数文件.md",
    ]


def _raw_boundary() -> dict[str, bool]:
    return {
        "user_declared_raw_data_immutable": True,
        "raw_data_root_readonly_policy_active": True,
        "source_external_action_readiness_public_artifacts_read_by_this_phase": True,
        "source_external_action_readiness_manifest_read_by_this_phase": True,
        "source_external_action_readiness_go_no_go_read_by_this_phase": True,
        "source_external_action_readiness_matrix_read_by_this_phase": True,
        "source_private_external_action_readiness_diagnostic_read_by_this_phase": True,
        "source_private_external_action_readiness_blocker_records_read_by_this_phase": True,
        "source_private_external_action_readiness_question_list_existence_checked_by_this_phase": True,
        "private_external_action_blocked_handoff_diagnostic_written_by_this_phase": True,
        "private_external_action_blocked_handoff_records_written_by_this_phase": True,
        "private_owner_action_reminder_queue_written_by_this_phase": True,
        "private_owner_action_reminder_report_written_by_this_phase": True,
        "source_private_external_action_readiness_diagnostic_mutated_by_this_phase": False,
        "source_private_external_action_readiness_blocker_records_mutated_by_this_phase": False,
        "source_private_external_action_readiness_question_list_mutated_by_this_phase": False,
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
        "source_private_external_action_readiness_diagnostic_committed": False,
        "source_private_external_action_readiness_blocker_records_committed": False,
        "source_private_external_action_readiness_question_list_committed": False,
        "private_external_action_blocked_handoff_diagnostic_committed": False,
        "private_external_action_blocked_handoff_records_committed": False,
        "private_owner_action_reminder_queue_committed": False,
        "private_owner_action_reminder_report_committed": False,
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


def _owner_action_reminder_type(diagnostic_kind: str) -> str:
    if diagnostic_kind == SOURCE_REFERENCE_DIAGNOSTIC_KIND:
        return "remind_owner_to_provide_actionable_source_reference_or_owner_exclusion"
    if diagnostic_kind == FORMULA_MAPPING_DIAGNOSTIC_KIND:
        return "remind_owner_to_provide_formula_or_non_numeric_mapping"
    return "remind_owner_to_provide_actionable_external_resolution"


def _validate_sources(
    *,
    source_summary: dict[str, Any],
    source_manifest: dict[str, Any],
    source_go_no_go: dict[str, Any],
    source_matrix: dict[str, Any],
    readiness_rows: list[dict[str, Any]],
) -> None:
    if source_summary.get("phase_id") != source_readiness.PHASE_ID:
        raise ValueError("source external-action-readiness phase mismatch")
    if source_manifest.get("phase_id") != source_readiness.PHASE_ID:
        raise ValueError("source external-action-readiness manifest phase mismatch")
    if source_go_no_go.get("decision") != "NO_GO":
        raise ValueError("source external-action-readiness decision must be NO_GO")
    if source_matrix.get("check_fail_count") != 0:
        raise ValueError("source external-action-readiness matrix must be clean")
    if source_summary.get("external_owner_action_blocker_count") != 48:
        raise ValueError("source external-action blocker count must be 48")
    if source_summary.get("external_owner_action_ready_count") != 0:
        raise ValueError("source external-action ready count must be 0")
    if source_summary.get("goal_status_recommendation") != "blocked":
        raise ValueError("source goal status must be blocked")
    if len(readiness_rows) != 48:
        raise ValueError("source private external-action readiness blocker records must contain 48 rows")
    for row in readiness_rows:
        if row.get("external_action_readiness_status") != source_readiness.READINESS_CONCLUSION:
            raise ValueError("source external-action readiness row is not blocked")
        if row.get("external_owner_action_ready") is not False:
            raise ValueError("source external-action row cannot be ready")
        if row.get("external_owner_action_blocker") is not True:
            raise ValueError("source external-action row must be blocked")
        if row.get("actionable_owner_resolution_ready") is not False:
            raise ValueError("source external-action row cannot be actionable")


def _build_private_records(
    *, generated_at: str, readiness_rows: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    handoff_rows: list[dict[str, Any]] = []
    reminder_rows: list[dict[str, Any]] = []
    for index, row in enumerate(readiness_rows, start=1):
        diagnostic_kind = str(row.get("diagnostic_kind"))
        reminder_item_id = f"ASR-OE-APP-OWNER-AGENT-EXTERNAL-ACTION-REMINDER-{index:03d}"
        handoff_item_id = f"ASR-OE-APP-OWNER-AGENT-EXTERNAL-ACTION-BLOCKED-HANDOFF-{index:03d}"
        handoff = {
            "external_action_blocked_handoff_item_id": handoff_item_id,
            "owner_action_reminder_item_id": reminder_item_id,
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "generated_at": generated_at,
            "source_action_readiness_item_id": row.get("action_readiness_item_id"),
            "source_owner_action_item_id": row.get("source_owner_action_item_id"),
            "source_blocked_handoff_item_id": row.get("source_blocked_handoff_item_id"),
            "target_slot_id": row.get("target_slot_id"),
            "diagnostic_kind": diagnostic_kind,
            "external_action_blocked_handoff_status": HANDOFF_CONCLUSION,
            "owner_action_reminder_required": True,
            "owner_or_authorized_agent_required": True,
            "owner_action_reminder_type": _owner_action_reminder_type(diagnostic_kind),
            "goal_status_recommendation": "blocked",
            "external_owner_action_ready": False,
            "external_owner_action_blocker": True,
            "actionable_owner_resolution_ready": False,
            "source_reference_or_owner_exclusion_reminder_required": (
                diagnostic_kind == SOURCE_REFERENCE_DIAGNOSTIC_KIND
            ),
            "formula_or_non_numeric_mapping_reminder_required": (
                diagnostic_kind == FORMULA_MAPPING_DIAGNOSTIC_KIND
            ),
            "binding_ready_after_external_action_blocked_handoff": False,
            "comparison_retry_ready_after_external_action_blocked_handoff": False,
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
        reminder = {
            "owner_action_reminder_item_id": reminder_item_id,
            "external_action_blocked_handoff_item_id": handoff_item_id,
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "generated_at": generated_at,
            "target_slot_id": row.get("target_slot_id"),
            "diagnostic_kind": diagnostic_kind,
            "owner_action_reminder_required": True,
            "owner_action_reminder_status": "required_before_binding_or_value_comparison",
            "owner_action_reminder_type": handoff["owner_action_reminder_type"],
            "actionable_owner_resolution_required": True,
            "authoritative_binding_application_ready": False,
            "raw_to_processed_value_comparison_ready": False,
            "public_commit_allowed": False,
        }
        handoff_rows.append(handoff)
        reminder_rows.append(reminder)
    return handoff_rows, reminder_rows


def _build_summary(
    *,
    generated_at: str,
    source_summary: dict[str, Any],
    source_manifest: dict[str, Any],
    source_go_no_go: dict[str, Any],
    source_matrix: dict[str, Any],
    readiness_rows: list[dict[str, Any]],
    handoff_rows: list[dict[str, Any]],
    reminder_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    counts = Counter(str(row.get("diagnostic_kind")) for row in handoff_rows)
    return {
        "schema_version": "kmfa.v014_owner_agent_external_action_blocked_handoff_after_readiness_summary.v1",
        "record_type": "v014_owner_agent_external_action_blocked_handoff_after_readiness_summary",
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
        "source_external_action_readiness_blocker_count": source_summary.get(
            "external_owner_action_blocker_count"
        ),
        "source_external_owner_action_ready_count": source_summary.get("external_owner_action_ready_count"),
        "source_private_external_action_readiness_blocker_records_item_count": len(readiness_rows),
        "external_action_blocked_handoff_item_count": len(handoff_rows),
        "owner_action_reminder_item_count": len(reminder_rows),
        "goal_status_recommendation": "blocked",
        "actionable_owner_resolution_count": 0,
        "source_reference_or_owner_exclusion_reminder_count": counts[SOURCE_REFERENCE_DIAGNOSTIC_KIND],
        "formula_or_non_numeric_mapping_reminder_count": counts[FORMULA_MAPPING_DIAGNOSTIC_KIND],
        "binding_ready_after_external_action_blocked_handoff_count": 0,
        "comparison_retry_ready_after_external_action_blocked_handoff_count": 0,
        "unresolved_difference_count": source_summary.get("unresolved_difference_count"),
        "private_external_action_blocked_handoff_diagnostic_written": True,
        "private_external_action_blocked_handoff_records_written": True,
        "private_owner_action_reminder_queue_written": True,
        "private_owner_action_reminder_report_written": True,
        "private_external_action_blocked_handoff_diagnostic_gitignored": _git_check_ignored(
            PRIVATE_EXTERNAL_ACTION_BLOCKED_HANDOFF_DIAGNOSTIC_PATH
        ),
        "private_external_action_blocked_handoff_records_gitignored": _git_check_ignored(
            PRIVATE_EXTERNAL_ACTION_BLOCKED_HANDOFF_RECORDS_PATH
        ),
        "private_owner_action_reminder_queue_gitignored": _git_check_ignored(
            PRIVATE_OWNER_ACTION_REMINDER_QUEUE_PATH
        ),
        "private_owner_action_reminder_report_gitignored": _git_check_ignored(
            PRIVATE_OWNER_ACTION_REMINDER_REPORT_PATH
        ),
        "source_private_external_action_readiness_diagnostic_gitignored": _git_check_ignored(
            SOURCE_PRIVATE_EXTERNAL_ACTION_READINESS_DIAGNOSTIC_PATH
        ),
        "source_private_external_action_readiness_blocker_records_gitignored": _git_check_ignored(
            SOURCE_PRIVATE_EXTERNAL_ACTION_READINESS_BLOCKER_RECORDS_PATH
        ),
        "source_private_external_action_readiness_question_list_gitignored": _git_check_ignored(
            SOURCE_PRIVATE_EXTERNAL_ACTION_READINESS_QUESTION_LIST_PATH
        ),
        "external_action_blocked_handoff_prepared_by_this_phase": True,
        "owner_action_reminder_queue_prepared_by_this_phase": True,
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
        ("source_external_action_readiness_phase_loaded", summary["source_phase_id"] == source_readiness.PHASE_ID),
        ("source_go_no_go_preserved", summary["source_go_no_go_decision"] == "NO_GO"),
        ("source_matrix_clean", summary["source_matrix_check_fail_count"] == 0),
        ("source_external_action_readiness_blockers_complete", summary["source_external_action_readiness_blocker_count"] == 48),
        ("source_external_action_ready_none", summary["source_external_owner_action_ready_count"] == 0),
        (
            "source_private_external_action_readiness_records_complete",
            summary["source_private_external_action_readiness_blocker_records_item_count"] == 48,
        ),
        ("blocked_handoff_complete", summary["external_action_blocked_handoff_item_count"] == 48),
        ("owner_action_reminder_queue_complete", summary["owner_action_reminder_item_count"] == 48),
        (
            "diagnostic_kind_reminder_counts_locked",
            summary["source_reference_or_owner_exclusion_reminder_count"] == 40
            and summary["formula_or_non_numeric_mapping_reminder_count"] == 8,
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
        "schema_version": "kmfa.v014_owner_agent_external_action_blocked_handoff_after_readiness_matrix.v1",
        "record_type": "v014_owner_agent_external_action_blocked_handoff_after_readiness_matrix_public_safe",
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
        "schema_version": "kmfa.v014_owner_agent_external_action_blocked_handoff_after_readiness_go_no_go.v1",
        "record_type": "v014_owner_agent_external_action_blocked_handoff_after_readiness_go_no_go",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": summary["generated_at"],
        "status": STATUS,
        "decision": DECISION,
        "handoff_conclusion": HANDOFF_CONCLUSION,
        "external_action_blocked_handoff_item_count": summary["external_action_blocked_handoff_item_count"],
        "owner_action_reminder_item_count": summary["owner_action_reminder_item_count"],
        "goal_status_recommendation": "blocked",
        "external_owner_action_ready_count": 0,
        "external_owner_action_blocker_count": summary["external_action_blocked_handoff_item_count"],
        "actionable_owner_resolution_count": 0,
        "source_reference_or_owner_exclusion_reminder_count": summary[
            "source_reference_or_owner_exclusion_reminder_count"
        ],
        "formula_or_non_numeric_mapping_reminder_count": summary["formula_or_non_numeric_mapping_reminder_count"],
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
        "schema_version": "kmfa.v014_owner_agent_external_action_blocked_handoff_after_readiness_manifest.v1",
        "record_type": "v014_owner_agent_external_action_blocked_handoff_after_readiness_manifest",
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
            "source_external_action_readiness_public_summary": "public_safe_metadata_copy",
            "source_external_action_readiness_public_manifest": "public_safe_metadata_copy",
            "source_external_action_readiness_public_go_no_go": "public_safe_metadata_copy",
            "source_external_action_readiness_public_matrix": "public_safe_metadata_copy",
            "source_private_external_action_readiness_diagnostic": "ignored_private_runtime",
            "source_private_external_action_readiness_blocker_records": "ignored_private_runtime",
            "source_private_external_action_readiness_question_list": "ignored_private_runtime",
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
            "private:owner_or_agent_external_action_blocked_handoff_diagnostic",
            "private:owner_or_agent_external_action_blocked_handoff_records",
            "private:owner_or_agent_external_action_owner_action_reminder_queue",
            "private:owner_or_agent_external_action_owner_action_reminder_report",
        ],
        "raw_boundary": summary["raw_boundary"],
        "public_safety": summary["public_safety"],
        "test_commands": [
            (
                "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 "
                "KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_"
                "owner_or_agent_external_action_blocked_handoff_after_external_action_readiness.py --generated-at "
                "2026-07-08T00:00:00+10:00"
            ),
            (
                "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 "
                "KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_"
                "owner_or_agent_external_action_blocked_handoff_after_external_action_readiness.py "
                "--require-private-external-action-blocked-handoff"
            ),
            (
                "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest "
                "KMFA.tests.test_v014_residual_difference_authorized_source_reference_or_exclusion_application_"
                "owner_or_agent_external_action_blocked_handoff_after_external_action_readiness"
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
    *,
    generated_at: str,
    summary: dict[str, Any],
    handoff_rows: list[dict[str, Any]],
    reminder_rows: list[dict[str, Any]],
) -> None:
    counts = Counter(str(row.get("diagnostic_kind")) for row in handoff_rows)
    _write_json(
        PRIVATE_EXTERNAL_ACTION_BLOCKED_HANDOFF_DIAGNOSTIC_PATH,
        {
            "schema_version": "kmfa.private.v014_owner_agent_external_action_blocked_handoff_after_readiness.v1",
            "classification": "private_owner_or_agent_external_action_blocked_handoff_do_not_commit",
            "record_type": "v014_owner_agent_external_action_blocked_handoff_after_readiness_private_diagnostic",
            "project_id": "KMFA",
            "version": VERSION,
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "generated_at": generated_at,
            "blocked_handoff_rows": handoff_rows,
            "owner_action_reminder_rows": reminder_rows,
            "summary_private": {
                "external_action_blocked_handoff_item_count": len(handoff_rows),
                "owner_action_reminder_item_count": len(reminder_rows),
                "goal_status_recommendation": "blocked",
                "source_reference_or_owner_exclusion_reminder_count": counts[SOURCE_REFERENCE_DIAGNOSTIC_KIND],
                "formula_or_non_numeric_mapping_reminder_count": counts[FORMULA_MAPPING_DIAGNOSTIC_KIND],
                "binding_ready_after_external_action_blocked_handoff_count": 0,
                "comparison_retry_ready_after_external_action_blocked_handoff_count": 0,
                "business_value_consistency_verified": False,
            },
            "raw_boundary": summary["raw_boundary"],
        },
    )
    _write_jsonl(PRIVATE_EXTERNAL_ACTION_BLOCKED_HANDOFF_RECORDS_PATH, handoff_rows)
    _write_jsonl(PRIVATE_OWNER_ACTION_REMINDER_QUEUE_PATH, reminder_rows)
    _write_text(
        PRIVATE_OWNER_ACTION_REMINDER_REPORT_PATH,
        "\n".join(
            [
                "# Private External Action Blocked Handoff Reminder Report",
                "",
                f"- phase_id: `{PHASE_ID}`",
                f"- external_action_blocked_handoff_item_count: `{len(handoff_rows)}`",
                f"- owner_action_reminder_item_count: `{len(reminder_rows)}`",
                "- goal_status_recommendation: `blocked`",
                f"- source reference / owner exclusion reminders: `{counts[SOURCE_REFERENCE_DIAGNOSTIC_KIND]}`",
                f"- formula / non-numeric mapping reminders: `{counts[FORMULA_MAPPING_DIAGNOSTIC_KIND]}`",
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
        f"""# V014 External Action Blocked Handoff After External Action Readiness

Generated at: {summary["generated_at"]}

## Scope

- Phase: `{PHASE_ID}`
- Decision: `{DECISION}`
- Status: `{STATUS}`
- Source: prior public-safe external-action-readiness evidence plus ignored private readiness blocker records.
- Raw boundary: no raw inbox read, list, stat, parse, value extraction, write, delete, move, rename, copy, normalize or mutation.

## Public-Safe Handoff Result

- Source readiness blockers: `{summary["source_external_action_readiness_blocker_count"]}`
- Source ready count: `{summary["source_external_owner_action_ready_count"]}`
- Source private readiness blocker records: `{summary["source_private_external_action_readiness_blocker_records_item_count"]}`
- External action blocked handoff items: `{summary["external_action_blocked_handoff_item_count"]}`
- Owner action reminder items: `{summary["owner_action_reminder_item_count"]}`
- Goal status recommendation: `{summary["goal_status_recommendation"]}`
- Source reference or owner exclusion reminders: `{summary["source_reference_or_owner_exclusion_reminder_count"]}`
- Formula or non-numeric mapping reminders: `{summary["formula_or_non_numeric_mapping_reminder_count"]}`
- Binding ready after blocked handoff: `{summary["binding_ready_after_external_action_blocked_handoff_count"]}`
- Comparison retry ready after blocked handoff: `{summary["comparison_retry_ready_after_external_action_blocked_handoff_count"]}`
- Unresolved differences: `{summary["unresolved_difference_count"]}`

## Gate

No executable owner/authorized-agent external action exists in the readiness blocker records. This phase only prepares a blocked handoff/reminder queue and does not authorize binding, raw-to-processed value comparison, reconciliation, business consistency, GitHub upload, app reinstall or business execution.

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

- RED: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_external_action_blocked_handoff_after_external_action_readiness` failed before implementation because the generator module did not exist.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_external_action_blocked_handoff_after_external_action_readiness.py --generated-at 2026-07-08T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_external_action_blocked_handoff_after_external_action_readiness.py --require-private-external-action-blocked-handoff`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_external_action_blocked_handoff_after_external_action_readiness`
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
- Control: public artifacts contain aggregate counts only; detailed handoff/reminder rows stay ignored.
- Risk: raw inbox is modified.
- Control: this phase consumes existing external-action-readiness artifacts only and does not touch the raw inbox.
""",
    )
    _write_text(
        ROLLBACK_PATH,
        f"""# Rollback Plan

Remove artifacts for `{PHASE_ID}`, metadata copies, private blocked-handoff outputs, tool, validator, focused test and governance rows. Do not touch source external-action-readiness evidence or raw inbox files.
""",
    )


def _write_governance_events(generated_at: str, summary: dict[str, Any]) -> None:
    event_id = (
        "DEV-KMFA-20260708-V014-AUTHORIZED-SOURCE-REFERENCE-OR-EXCLUSION-APPLICATION-OWNER-OR-AGENT-"
        "EXTERNAL-ACTION-BLOCKED-HANDOFF-AFTER-EXTERNAL-ACTION-READINESS"
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
                "Converted 48 external-action readiness blockers into a blocked handoff and owner-action "
                "reminder queue; no owner/authorized-agent executable action is present."
            ),
            "evidence_ref": MANIFEST_PATH.as_posix(),
            "files_changed": _phase_public_files(),
            "test_commands": _build_manifest(
                {"generated_at": generated_at, "raw_boundary": {}, "public_safety": {}},
                {"checks": [], "check_count": 0},
                {},
            )["test_commands"],
            "test_results": ["PENDING: final validation results will be recorded before local commit."],
            "external_action_blocked_handoff_item_count": summary["external_action_blocked_handoff_item_count"],
            "owner_action_reminder_item_count": summary["owner_action_reminder_item_count"],
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
            "name": "v0.1.4 owner or authorized agent external action blocked handoff after external action readiness",
            "status": STATUS,
            "completed_task_units": 1,
            "estimated_task_units": 1,
            "derived_percent": 100.0,
            "acceptance_id": ACCEPTANCE_ID,
            "evidence_ref": MANIFEST_PATH.as_posix(),
            "fact_level": "EXTRACTED",
            "updated_at": generated_at[:10],
            "stage_id": "VALUE-CONSISTENCY",
            "phase_goal": "prepare blocked handoff and owner-action reminders after external action readiness",
            "task_count": 3,
            "acceptance_output": (
                "External-action blocked handoff manifest, summary, Go No-Go, private ignored handoff/reminder "
                "records, validator, focused test and governance records"
            ),
        },
        ("phase_id", "record_type", "task_id"),
    )
    for suffix, task_goal in (
        ("T1", "read prior public external-action-readiness evidence and ignored private blocker records read-only"),
        ("T2", "write ignored private external-action blocked-handoff records and owner-action reminders"),
        ("T3", "emit public-safe NO_GO handoff evidence while keeping binding comparison and upload closed"),
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
    source_summary = _read_json(SOURCE_EXTERNAL_ACTION_READINESS_SUMMARY_PATH)
    source_manifest = _read_json(SOURCE_EXTERNAL_ACTION_READINESS_MANIFEST_PATH)
    source_go_no_go = _read_json(SOURCE_EXTERNAL_ACTION_READINESS_GO_NO_GO_PATH)
    source_matrix = _read_json(SOURCE_EXTERNAL_ACTION_READINESS_MATRIX_PATH)
    readiness_rows = _read_jsonl(SOURCE_PRIVATE_EXTERNAL_ACTION_READINESS_BLOCKER_RECORDS_PATH)
    if not SOURCE_PRIVATE_EXTERNAL_ACTION_READINESS_DIAGNOSTIC_PATH.exists():
        raise FileNotFoundError(SOURCE_PRIVATE_EXTERNAL_ACTION_READINESS_DIAGNOSTIC_PATH)
    if not SOURCE_PRIVATE_EXTERNAL_ACTION_READINESS_QUESTION_LIST_PATH.exists():
        raise FileNotFoundError(SOURCE_PRIVATE_EXTERNAL_ACTION_READINESS_QUESTION_LIST_PATH)
    _validate_sources(
        source_summary=source_summary,
        source_manifest=source_manifest,
        source_go_no_go=source_go_no_go,
        source_matrix=source_matrix,
        readiness_rows=readiness_rows,
    )
    handoff_rows, reminder_rows = _build_private_records(generated_at=generated, readiness_rows=readiness_rows)
    summary = _build_summary(
        generated_at=generated,
        source_summary=source_summary,
        source_manifest=source_manifest,
        source_go_no_go=source_go_no_go,
        source_matrix=source_matrix,
        readiness_rows=readiness_rows,
        handoff_rows=handoff_rows,
        reminder_rows=reminder_rows,
    )
    matrix = _build_matrix(summary)
    go_no_go = _build_go_no_go(summary)
    manifest = _build_manifest(summary, matrix, go_no_go)
    _write_private_outputs(
        generated_at=generated,
        summary=summary,
        handoff_rows=handoff_rows,
        reminder_rows=reminder_rows,
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
        "private_external_action_blocked_handoff_records": handoff_rows,
        "private_owner_action_reminder_queue": reminder_rows,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generated-at")
    args = parser.parse_args(argv)
    result = generate(generated_at=args.generated_at)
    summary = result["summary"]
    print(
        "PASS: generated V014 owner/authorized-agent external action blocked handoff after external action readiness "
        f"handoff={summary['external_action_blocked_handoff_item_count']} "
        f"reminders={summary['owner_action_reminder_item_count']} "
        f"goal={summary['goal_status_recommendation']} "
        f"decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
