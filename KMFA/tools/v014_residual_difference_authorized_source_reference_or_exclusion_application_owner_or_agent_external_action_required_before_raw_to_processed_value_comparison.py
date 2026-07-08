#!/usr/bin/env python3
"""Generate the external-action requirement gate before raw-to-processed comparison.

This phase consumes the previous public-safe authoritative-binding requirement
evidence and the ignored private requirement queue. It does not read the raw
inbox, bind fingerprints, compare values, upload, reinstall, or execute
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
    v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_external_action_required_before_authoritative_binding
    as source_binding,
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
    "EXTERNAL_ACTION_REQUIRED_BEFORE_RAW_TO_PROCESSED_VALUE_COMPARISON"
)
TASK_ID = (
    "KMFA-V014-RESIDUAL-DIFFERENCE-AUTHORIZED-SOURCE-REFERENCE-OR-EXCLUSION-APPLICATION-OWNER-OR-"
    "AGENT-EXTERNAL-ACTION-REQUIRED-BEFORE-RAW-TO-PROCESSED-VALUE-COMPARISON-20260708"
)
ACCEPTANCE_ID = (
    "ACC-V014-RESIDUAL-DIFFERENCE-AUTHORIZED-SOURCE-REFERENCE-OR-EXCLUSION-APPLICATION-OWNER-OR-"
    "AGENT-EXTERNAL-ACTION-REQUIRED-BEFORE-RAW-TO-PROCESSED-VALUE-COMPARISON"
)
VERSION = (
    "0.1.4-residual-difference-authorized-source-reference-or-exclusion-application-owner-or-agent-"
    "external-action-required-before-raw-to-processed-value-comparison"
)
STATUS = (
    "completed_validated_local_only_authorized_source_reference_or_exclusion_application_owner_or_agent_"
    "external_action_required_before_raw_to_processed_value_comparison_no_go_blocked"
)
DECISION = "NO_GO"
REQUIREMENT_CONCLUSION = (
    "blocked_owner_or_authorized_agent_external_action_required_before_raw_to_processed_value_comparison"
)
NEXT_REQUIRED_INPUT = source_binding.NEXT_REQUIRED_INPUT
NEXT_RECOMMENDED_PHASE = "owner_or_authorized_agent_external_action_required_before_processed_data_reconciliation"

SOURCE_REFERENCE_DIAGNOSTIC_KIND = source_binding.SOURCE_REFERENCE_DIAGNOSTIC_KIND
FORMULA_MAPPING_DIAGNOSTIC_KIND = source_binding.FORMULA_MAPPING_DIAGNOSTIC_KIND

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
PREFIX = (
    "residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_"
    "external_action_required_before_raw_to_processed_value_comparison"
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

SOURCE_BINDING_SUMMARY_PATH = source_binding.METADATA_SUMMARY_PATH
SOURCE_BINDING_MANIFEST_PATH = source_binding.METADATA_MANIFEST_PATH
SOURCE_BINDING_GO_NO_GO_PATH = source_binding.METADATA_GO_NO_GO_PATH
SOURCE_BINDING_MATRIX_PATH = source_binding.METADATA_MATRIX_PATH
SOURCE_PRIVATE_AUTHORITATIVE_BINDING_REQUIREMENT_DIAGNOSTIC_PATH = (
    source_binding.PRIVATE_AUTHORITATIVE_BINDING_REQUIREMENT_DIAGNOSTIC_PATH
)
SOURCE_PRIVATE_AUTHORITATIVE_BINDING_REQUIREMENT_QUEUE_PATH = (
    source_binding.PRIVATE_AUTHORITATIVE_BINDING_REQUIREMENT_QUEUE_PATH
)
SOURCE_PRIVATE_AUTHORITATIVE_BINDING_REQUIREMENT_REPORT_PATH = (
    source_binding.PRIVATE_AUTHORITATIVE_BINDING_REQUIREMENT_REPORT_PATH
)

PRIVATE_OUTPUT_DIR = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_external_action_required_before_raw_to_processed_value_comparison"
)
PRIVATE_RAW_TO_PROCESSED_VALUE_COMPARISON_REQUIREMENT_DIAGNOSTIC_PATH = (
    PRIVATE_OUTPUT_DIR
    / "private_owner_or_agent_external_action_required_before_raw_to_processed_value_comparison_diagnostic.json"
)
PRIVATE_RAW_TO_PROCESSED_VALUE_COMPARISON_REQUIREMENT_QUEUE_PATH = (
    PRIVATE_OUTPUT_DIR
    / "private_owner_or_agent_external_action_required_before_raw_to_processed_value_comparison_queue.jsonl"
)
PRIVATE_RAW_TO_PROCESSED_VALUE_COMPARISON_REQUIREMENT_REPORT_PATH = (
    PRIVATE_OUTPUT_DIR
    / "private_owner_or_agent_external_action_required_before_raw_to_processed_value_comparison_report.md"
)

DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"
STAGE_STATUS_PATH = PROJECT_ROOT / "metadata/stage_status.jsonl"
TASK_STATUS_PATH = PROJECT_ROOT / "metadata/traceability/v1_4_stage_phase_task_status.jsonl"


def _phase_public_files() -> list[str]:
    static = [
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
        "KMFA/metadata/stage_status.jsonl",
        "KMFA/metadata/traceability/v1_4_stage_phase_task_status.jsonl",
        "KMFA/功能清单.md",
        "KMFA/开发记录.md",
        "KMFA/模型参数文件.md",
        "KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_external_action_required_before_raw_to_processed_value_comparison.py",
        "KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_external_action_required_before_raw_to_processed_value_comparison.py",
        "KMFA/tests/test_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_external_action_required_before_raw_to_processed_value_comparison.py",
    ]
    artifacts = [
        SUMMARY_PATH,
        MANIFEST_PATH,
        GO_NO_GO_PATH,
        MATRIX_PATH,
        REPORT_PATH,
        GO_NO_GO_RECORD_PATH,
        TEST_RESULTS_PATH,
        RISK_REGISTER_PATH,
        ROLLBACK_PATH,
        METADATA_SUMMARY_PATH,
        METADATA_MANIFEST_PATH,
        METADATA_GO_NO_GO_PATH,
        METADATA_MATRIX_PATH,
    ]
    return [Path(item).as_posix() for item in static] + [path.as_posix() for path in artifacts]


def _raw_boundary() -> dict[str, bool]:
    return {
        "user_declared_raw_data_immutable": True,
        "raw_data_root_readonly_policy_active": True,
        "source_binding_public_artifacts_read_by_this_phase": True,
        "source_binding_manifest_read_by_this_phase": True,
        "source_binding_go_no_go_read_by_this_phase": True,
        "source_binding_matrix_read_by_this_phase": True,
        "source_private_binding_requirement_diagnostic_read_by_this_phase": True,
        "source_private_binding_requirement_queue_read_by_this_phase": True,
        "source_private_binding_requirement_report_existence_checked_by_this_phase": True,
        "private_raw_to_processed_value_comparison_requirement_diagnostic_written_by_this_phase": True,
        "private_raw_to_processed_value_comparison_requirement_queue_written_by_this_phase": True,
        "private_raw_to_processed_value_comparison_requirement_report_written_by_this_phase": True,
        "source_private_binding_requirement_diagnostic_mutated_by_this_phase": False,
        "source_private_binding_requirement_queue_mutated_by_this_phase": False,
        "source_private_binding_requirement_report_mutated_by_this_phase": False,
        "owner_or_agent_external_action_completed_by_this_phase": False,
        "authoritative_binding_applied_by_this_phase": False,
        "raw_candidate_fingerprint_bound_by_this_phase": False,
        "raw_to_processed_value_comparison_ready_by_this_phase": False,
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
        "source_private_binding_requirement_diagnostic_committed": False,
        "source_private_binding_requirement_queue_committed": False,
        "source_private_binding_requirement_report_committed": False,
        "private_raw_to_processed_value_comparison_requirement_diagnostic_committed": False,
        "private_raw_to_processed_value_comparison_requirement_queue_committed": False,
        "private_raw_to_processed_value_comparison_requirement_report_committed": False,
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
        return "owner_authorized_source_reference_or_owner_exclusion_required_before_raw_to_processed_value_comparison"
    if diagnostic_kind == FORMULA_MAPPING_DIAGNOSTIC_KIND:
        return "owner_authorized_formula_or_non_numeric_mapping_required_before_raw_to_processed_value_comparison"
    return "owner_authorized_actionable_resolution_required_before_raw_to_processed_value_comparison"


def _validate_sources(
    *,
    source_summary: dict[str, Any],
    source_manifest: dict[str, Any],
    source_go_no_go: dict[str, Any],
    source_matrix: dict[str, Any],
    source_binding_rows: list[dict[str, Any]],
) -> None:
    if source_summary.get("phase_id") != source_binding.PHASE_ID:
        raise ValueError("source binding phase mismatch")
    if source_manifest.get("phase_id") != source_binding.PHASE_ID:
        raise ValueError("source binding manifest phase mismatch")
    if source_go_no_go.get("decision") != "NO_GO":
        raise ValueError("source binding decision must be NO_GO")
    if source_matrix.get("check_fail_count") != 0:
        raise ValueError("source binding matrix must be clean")
    expected_counts = {
        "authoritative_binding_requirement_ready_count": 0,
        "authoritative_binding_requirement_blocker_count": 48,
        "authoritative_binding_requirement_required_count": 48,
        "authoritative_binding_application_ready_count": 0,
    }
    for key, expected in expected_counts.items():
        if source_summary.get(key) != expected:
            raise ValueError(f"source binding {key} must be {expected}")
    if source_summary.get("goal_status_recommendation") != "blocked":
        raise ValueError("source goal status must be blocked")
    if len(source_binding_rows) != 48:
        raise ValueError("source private binding requirement queue must contain 48 rows")
    for row in source_binding_rows:
        if row.get("authoritative_binding_requirement_status") != source_binding.REQUIREMENT_CONCLUSION:
            raise ValueError("source binding row has unexpected requirement status")
        if row.get("authoritative_binding_requirement_ready") is not False:
            raise ValueError("source binding row cannot be ready")
        if row.get("authoritative_binding_requirement_blocker") is not True:
            raise ValueError("source binding row must remain blocker")
        if row.get("authoritative_binding_application_ready") is not False:
            raise ValueError("source binding row cannot be binding-ready")
        if row.get("raw_to_processed_value_comparison_ready") is not False:
            raise ValueError("source binding row cannot be comparison-ready")
        if row.get("public_commit_allowed") is not False:
            raise ValueError("source binding row cannot be public-committable")


def _build_requirement_records(
    *, generated_at: str, source_binding_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, row in enumerate(source_binding_rows, start=1):
        diagnostic_kind = str(row.get("diagnostic_kind"))
        records.append(
            {
                "raw_to_processed_value_comparison_requirement_item_id": (
                    f"ASR-OE-APP-OWNER-AGENT-COMPARISON-REQ-{index:03d}"
                ),
                "source_authoritative_binding_requirement_item_id": row.get(
                    "authoritative_binding_requirement_item_id"
                ),
                "source_external_action_follow_up_item_id": row.get("source_external_action_follow_up_item_id"),
                "source_action_readiness_item_id": row.get("source_action_readiness_item_id"),
                "source_owner_action_item_id": row.get("source_owner_action_item_id"),
                "source_blocked_handoff_item_id": row.get("source_blocked_handoff_item_id"),
                "phase_id": PHASE_ID,
                "task_id": TASK_ID,
                "generated_at": generated_at,
                "target_slot_id": row.get("target_slot_id"),
                "diagnostic_kind": diagnostic_kind,
                "raw_to_processed_value_comparison_requirement_status": REQUIREMENT_CONCLUSION,
                "raw_to_processed_value_comparison_requirement_required": True,
                "raw_to_processed_value_comparison_requirement_ready": False,
                "raw_to_processed_value_comparison_requirement_blocker": True,
                "raw_to_processed_value_comparison_requirement_reason": _blocker_reason(diagnostic_kind),
                "owner_action_status": row.get("owner_action_status"),
                "owner_action_type": row.get("owner_action_type"),
                "owner_or_agent_external_action_completed": False,
                "actionable_owner_resolution_ready": False,
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
    source_binding_rows: list[dict[str, Any]],
    requirement_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    counts = Counter(str(row.get("diagnostic_kind")) for row in requirement_rows)
    return {
        "schema_version": "kmfa.v014_owner_agent_external_action_required_before_raw_comparison_summary.v1",
        "record_type": "v014_owner_agent_external_action_required_before_raw_comparison_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": generated_at,
        "status": STATUS,
        "decision": DECISION,
        "requirement_conclusion": REQUIREMENT_CONCLUSION,
        "source_phase_id": source_summary.get("phase_id"),
        "source_manifest_phase_id": source_manifest.get("phase_id"),
        "source_go_no_go_decision": source_go_no_go.get("decision"),
        "source_matrix_check_fail_count": source_matrix.get("check_fail_count"),
        "source_authoritative_binding_requirement_ready_count": source_summary.get(
            "authoritative_binding_requirement_ready_count"
        ),
        "source_authoritative_binding_requirement_blocker_count": source_summary.get(
            "authoritative_binding_requirement_blocker_count"
        ),
        "source_authoritative_binding_requirement_required_count": source_summary.get(
            "authoritative_binding_requirement_required_count"
        ),
        "source_private_authoritative_binding_requirement_queue_item_count": len(source_binding_rows),
        "source_goal_status_recommendation": source_summary.get("goal_status_recommendation"),
        "goal_status_recommendation": "blocked",
        "raw_to_processed_value_comparison_requirement_ready_count": 0,
        "raw_to_processed_value_comparison_requirement_blocker_count": len(requirement_rows),
        "raw_to_processed_value_comparison_requirement_required_count": len(requirement_rows),
        "actionable_owner_resolution_count": 0,
        "source_reference_or_owner_exclusion_comparison_requirement_count": counts[
            SOURCE_REFERENCE_DIAGNOSTIC_KIND
        ],
        "formula_or_non_numeric_mapping_comparison_requirement_count": counts[FORMULA_MAPPING_DIAGNOSTIC_KIND],
        "authoritative_binding_application_ready_count": 0,
        "raw_to_processed_value_comparison_ready_count": 0,
        "unresolved_difference_count": source_summary.get("unresolved_difference_count"),
        "private_raw_to_processed_value_comparison_requirement_diagnostic_written": True,
        "private_raw_to_processed_value_comparison_requirement_queue_written": True,
        "private_raw_to_processed_value_comparison_requirement_report_written": True,
        "private_raw_to_processed_value_comparison_requirement_diagnostic_gitignored": _git_check_ignored(
            PRIVATE_RAW_TO_PROCESSED_VALUE_COMPARISON_REQUIREMENT_DIAGNOSTIC_PATH
        ),
        "private_raw_to_processed_value_comparison_requirement_queue_gitignored": _git_check_ignored(
            PRIVATE_RAW_TO_PROCESSED_VALUE_COMPARISON_REQUIREMENT_QUEUE_PATH
        ),
        "private_raw_to_processed_value_comparison_requirement_report_gitignored": _git_check_ignored(
            PRIVATE_RAW_TO_PROCESSED_VALUE_COMPARISON_REQUIREMENT_REPORT_PATH
        ),
        "source_private_authoritative_binding_requirement_diagnostic_gitignored": _git_check_ignored(
            SOURCE_PRIVATE_AUTHORITATIVE_BINDING_REQUIREMENT_DIAGNOSTIC_PATH
        ),
        "source_private_authoritative_binding_requirement_queue_gitignored": _git_check_ignored(
            SOURCE_PRIVATE_AUTHORITATIVE_BINDING_REQUIREMENT_QUEUE_PATH
        ),
        "source_private_authoritative_binding_requirement_report_gitignored": _git_check_ignored(
            SOURCE_PRIVATE_AUTHORITATIVE_BINDING_REQUIREMENT_REPORT_PATH
        ),
        "external_action_requirement_checked_by_this_phase": True,
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
        ("source_binding_phase_loaded", summary["source_phase_id"] == source_binding.PHASE_ID),
        ("source_go_no_go_preserved", summary["source_go_no_go_decision"] == "NO_GO"),
        ("source_matrix_clean", summary["source_matrix_check_fail_count"] == 0),
        ("source_binding_blockers_complete", summary["source_authoritative_binding_requirement_blocker_count"] == 48),
        (
            "source_private_binding_requirement_queue_read",
            summary["source_private_authoritative_binding_requirement_queue_item_count"] == 48,
        ),
        (
            "comparison_requirement_queue_complete",
            summary["raw_to_processed_value_comparison_requirement_required_count"] == 48,
        ),
        (
            "comparison_requirement_blockers_locked",
            summary["raw_to_processed_value_comparison_requirement_blocker_count"] == 48,
        ),
        (
            "diagnostic_kind_comparison_requirement_counts_locked",
            summary["source_reference_or_owner_exclusion_comparison_requirement_count"] == 40
            and summary["formula_or_non_numeric_mapping_comparison_requirement_count"] == 8,
        ),
        ("blocked_goal_preserved", summary["goal_status_recommendation"] == "blocked"),
        ("raw_inbox_untouched", summary["raw_boundary"]["raw_inbox_mutated_by_this_phase"] is False),
        (
            "downstream_gates_closed",
            summary["github_upload_performed"] is False and summary["business_execution_performed"] is False,
        ),
        ("public_safety_locked", summary["public_safety"]["public_safe_aggregate_only"] is True),
    ]
    rows = [{"check_code": code, "status": "PASS" if passed else "FAIL"} for code, passed in checks]
    pass_count = sum(1 for row in rows if row["status"] == "PASS")
    return {
        "schema_version": "kmfa.v014_owner_agent_external_action_required_before_raw_comparison_matrix.v1",
        "record_type": "v014_owner_agent_external_action_required_before_raw_comparison_matrix_public_safe",
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
        "schema_version": "kmfa.v014_owner_agent_external_action_required_before_raw_comparison_go_no_go.v1",
        "record_type": "v014_owner_agent_external_action_required_before_raw_comparison_go_no_go",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": summary["generated_at"],
        "status": STATUS,
        "decision": DECISION,
        "requirement_conclusion": REQUIREMENT_CONCLUSION,
        "source_authoritative_binding_requirement_ready_count": summary[
            "source_authoritative_binding_requirement_ready_count"
        ],
        "source_authoritative_binding_requirement_blocker_count": summary[
            "source_authoritative_binding_requirement_blocker_count"
        ],
        "source_authoritative_binding_requirement_required_count": summary[
            "source_authoritative_binding_requirement_required_count"
        ],
        "raw_to_processed_value_comparison_requirement_ready_count": 0,
        "raw_to_processed_value_comparison_requirement_blocker_count": summary[
            "raw_to_processed_value_comparison_requirement_blocker_count"
        ],
        "raw_to_processed_value_comparison_requirement_required_count": summary[
            "raw_to_processed_value_comparison_requirement_required_count"
        ],
        "actionable_owner_resolution_count": 0,
        "source_reference_or_owner_exclusion_comparison_requirement_count": summary[
            "source_reference_or_owner_exclusion_comparison_requirement_count"
        ],
        "formula_or_non_numeric_mapping_comparison_requirement_count": summary[
            "formula_or_non_numeric_mapping_comparison_requirement_count"
        ],
        "unresolved_difference_count": summary["unresolved_difference_count"],
        "goal_status_recommendation": "blocked",
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


def _test_commands() -> list[str]:
    return [
        (
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 "
            "KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_"
            "owner_or_agent_external_action_required_before_raw_to_processed_value_comparison.py --generated-at "
            "2026-07-08T00:00:00+10:00"
        ),
        (
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 "
            "KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_"
            "owner_or_agent_external_action_required_before_raw_to_processed_value_comparison.py "
            "--require-private-raw-to-processed-value-comparison-requirement"
        ),
        (
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest "
            "KMFA.tests.test_v014_residual_difference_authorized_source_reference_or_exclusion_application_"
            "owner_or_agent_external_action_required_before_raw_to_processed_value_comparison"
        ),
    ]


def _build_manifest(summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v014_owner_agent_external_action_required_before_raw_comparison_manifest.v1",
        "record_type": "v014_owner_agent_external_action_required_before_raw_comparison_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": summary["generated_at"],
        "status": STATUS,
        "decision": DECISION,
        "requirement_conclusion": REQUIREMENT_CONCLUSION,
        "summary": summary,
        "matrix": matrix,
        "go_no_go_report": go_no_go,
        "source_artifacts": {
            "source_binding_public_summary": "public_safe_metadata_copy",
            "source_binding_public_manifest": "public_safe_metadata_copy",
            "source_binding_public_go_no_go": "public_safe_metadata_copy",
            "source_binding_public_matrix": "public_safe_metadata_copy",
            "source_private_binding_requirement_diagnostic": "ignored_private_runtime",
            "source_private_binding_requirement_queue": "ignored_private_runtime",
            "source_private_binding_requirement_report": "ignored_private_runtime",
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
            "private:owner_or_agent_external_action_required_before_raw_to_processed_value_comparison_diagnostic",
            "private:owner_or_agent_external_action_required_before_raw_to_processed_value_comparison_queue",
            "private:owner_or_agent_external_action_required_before_raw_to_processed_value_comparison_report",
        ],
        "raw_boundary": summary["raw_boundary"],
        "public_safety": summary["public_safety"],
        "test_commands": _test_commands(),
        "git": {
            "branch": _git_output(["branch", "--show-current"]),
            "head": "local_commit_recorded_after_validation",
            "status_short_branch": "omitted_for_reproducible_phase_manifest",
            "changed_kmfa_files": _phase_public_files(),
        },
    }


def _write_private_outputs(
    *, generated_at: str, summary: dict[str, Any], requirement_rows: list[dict[str, Any]]
) -> None:
    counts = Counter(str(row.get("diagnostic_kind")) for row in requirement_rows)
    _write_json(
        PRIVATE_RAW_TO_PROCESSED_VALUE_COMPARISON_REQUIREMENT_DIAGNOSTIC_PATH,
        {
            "schema_version": "kmfa.private.v014_owner_agent_external_action_required_before_raw_comparison.v1",
            "classification": "private_owner_or_agent_raw_to_processed_value_comparison_requirement_do_not_commit",
            "record_type": "v014_owner_agent_raw_to_processed_value_comparison_requirement_private_diagnostic",
            "project_id": "KMFA",
            "version": VERSION,
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "generated_at": generated_at,
            "raw_to_processed_value_comparison_requirement_rows": requirement_rows,
            "summary_private": {
                "raw_to_processed_value_comparison_requirement_blocker_count": len(requirement_rows),
                "raw_to_processed_value_comparison_requirement_ready_count": 0,
                "raw_to_processed_value_comparison_requirement_required_count": len(requirement_rows),
                "goal_status_recommendation": "blocked",
                "source_reference_or_owner_exclusion_comparison_requirement_count": counts[
                    SOURCE_REFERENCE_DIAGNOSTIC_KIND
                ],
                "formula_or_non_numeric_mapping_comparison_requirement_count": counts[FORMULA_MAPPING_DIAGNOSTIC_KIND],
                "raw_to_processed_value_comparison_ready_count": 0,
            },
            "raw_boundary": summary["raw_boundary"],
        },
    )
    _write_jsonl(PRIVATE_RAW_TO_PROCESSED_VALUE_COMPARISON_REQUIREMENT_QUEUE_PATH, requirement_rows)
    report_lines = [
        "# owner/授权代理 external action required before raw-to-processed value comparison 队列",
        "",
        f"- phase_id: `{PHASE_ID}`",
        f"- raw_to_processed_value_comparison_requirement_blocker_count: `{len(requirement_rows)}`",
        f"- source reference / owner exclusion requirement: `{counts[SOURCE_REFERENCE_DIAGNOSTIC_KIND]}`",
        f"- formula / non-numeric mapping requirement: `{counts[FORMULA_MAPPING_DIAGNOSTIC_KIND]}`",
        "- raw inbox touched: `false`",
        "",
        "## raw-to-processed value comparison 前置要求",
        "",
        "1. source reference / owner exclusion 类 blocker 必须由 owner 或授权代理提供可执行依据或明确排除。",
        "2. formula / non-numeric mapping 类 blocker 必须由 owner 或授权代理提供可执行公式映射或非数值映射依据。",
        "3. 在上述动作完成前，不允许执行 raw-to-processed value comparison 或业务执行。",
        "",
        "当前未检测到可执行 owner/授权代理外部动作，因此 raw-to-processed value comparison 继续关闭。",
        "",
    ]
    _write_text(PRIVATE_RAW_TO_PROCESSED_VALUE_COMPARISON_REQUIREMENT_REPORT_PATH, "\n".join(report_lines))


def _write_human(summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any]) -> None:
    _write_text(
        REPORT_PATH,
        f"""# V014 Owner / Authorized Agent External Action Required Before Raw-To-Processed Value Comparison

Generated at: {summary["generated_at"]}

## Scope

- Phase: `{PHASE_ID}`
- Decision: `{DECISION}`
- Status: `{STATUS}`
- Source: prior public-safe authoritative-binding requirement evidence plus ignored private requirement queue.
- Raw boundary: no raw inbox read, list, stat, parse, value extraction, write, delete, move, rename, copy, normalize or mutation.

## Public-Safe Raw Comparison Requirement Result

- Source binding requirement ready count: `{summary["source_authoritative_binding_requirement_ready_count"]}`
- Source binding requirement blocker count: `{summary["source_authoritative_binding_requirement_blocker_count"]}`
- Source binding requirement required count: `{summary["source_authoritative_binding_requirement_required_count"]}`
- Raw comparison requirement ready count: `{summary["raw_to_processed_value_comparison_requirement_ready_count"]}`
- Raw comparison requirement required count: `{summary["raw_to_processed_value_comparison_requirement_required_count"]}`
- Raw comparison requirement blocker count: `{summary["raw_to_processed_value_comparison_requirement_blocker_count"]}`
- Actionable owner resolution count: `{summary["actionable_owner_resolution_count"]}`
- Source reference or owner exclusion comparison requirement: `{summary["source_reference_or_owner_exclusion_comparison_requirement_count"]}`
- Formula or non-numeric mapping comparison requirement: `{summary["formula_or_non_numeric_mapping_comparison_requirement_count"]}`
- Raw-to-processed value comparison ready count: `{summary["raw_to_processed_value_comparison_ready_count"]}`
- Unresolved differences: `{summary["unresolved_difference_count"]}`

## Gate

No executable owner/authorized-agent source reference, owner exclusion, formula mapping or non-numeric mapping has been provided after the authoritative-binding requirement gate. This phase records the private raw-to-processed value comparison requirement queue only and does not authorize binding, raw-to-processed value comparison, reconciliation, business consistency, GitHub upload, app reinstall or business execution.

Next required input: `{NEXT_REQUIRED_INPUT}`.
""",
    )
    _write_text(
        GO_NO_GO_RECORD_PATH,
        f"""# Go / No-Go Record

- Phase: `{PHASE_ID}`
- Decision: `{go_no_go["decision"]}`
- Reason: `{REQUIREMENT_CONCLUSION}`
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

- RED: focused unittest failed before implementation because the raw-to-processed value comparison requirement generator was missing.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_external_action_required_before_raw_to_processed_value_comparison.py --generated-at 2026-07-08T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_external_action_required_before_raw_to_processed_value_comparison.py --require-private-raw-to-processed-value-comparison-requirement`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_external_action_required_before_raw_to_processed_value_comparison`
- Governance validators, CSV shape checks, diff check, raw/private marker scan, secret scan and private-runtime tracked-file scan: expected before commit.

Expected matrix result: {matrix["check_pass_count"]}/{matrix["check_count"]} PASS.
""",
    )
    _write_text(
        RISK_REGISTER_PATH,
        """# Risk Register

- Risk: raw comparison requirement queue is mistaken for permission to compare values.
- Control: decision remains NO_GO and all downstream gates remain false.
- Risk: private source handles leak into public evidence.
- Control: public artifacts contain aggregate counts only; detailed requirement rows stay ignored.
- Risk: raw inbox is modified.
- Control: this phase consumes existing requirement artifacts only and does not touch the raw inbox.
""",
    )
    _write_text(
        ROLLBACK_PATH,
        f"""# Rollback Plan

Remove artifacts for `{PHASE_ID}`, metadata copies, private raw comparison requirement outputs, tool, validator, focused test and governance rows. Do not touch source binding evidence or raw inbox files.
""",
    )


def _write_governance_events(generated_at: str, summary: dict[str, Any]) -> None:
    event_id = (
        "DEV-KMFA-20260708-V014-AUTHORIZED-SOURCE-REFERENCE-OR-EXCLUSION-APPLICATION-OWNER-OR-AGENT-"
        "EXTERNAL-ACTION-REQUIRED-BEFORE-RAW-TO-PROCESSED-VALUE-COMPARISON"
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
                "Generated a private owner/authorized-agent raw-to-processed value comparison requirement queue; "
                "48 blockers remain and comparison, upload and execution stay closed."
            ),
            "evidence_ref": MANIFEST_PATH.as_posix(),
            "files_changed": _phase_public_files(),
            "test_commands": _test_commands(),
            "test_results": ["PENDING: final validation results will be recorded before local commit."],
            "raw_to_processed_value_comparison_requirement_ready_count": summary[
                "raw_to_processed_value_comparison_requirement_ready_count"
            ],
            "raw_to_processed_value_comparison_requirement_blocker_count": summary[
                "raw_to_processed_value_comparison_requirement_blocker_count"
            ],
            "raw_to_processed_value_comparison_requirement_required_count": summary[
                "raw_to_processed_value_comparison_requirement_required_count"
            ],
            "goal_status_recommendation": "blocked",
            "actionable_owner_resolution_count": 0,
            "unresolved_difference_count": summary["unresolved_difference_count"],
            "raw_inbox_read_performed": False,
            "raw_inbox_mutation_performed": False,
            "authoritative_binding_applied_by_this_phase": False,
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
            "name": "v0.1.4 owner or authorized agent external action required before raw comparison",
            "status": STATUS,
            "completed_task_units": 1,
            "estimated_task_units": 1,
            "derived_percent": 100.0,
            "acceptance_id": ACCEPTANCE_ID,
            "evidence_ref": MANIFEST_PATH.as_posix(),
            "fact_level": "EXTRACTED",
            "updated_at": generated_at[:10],
            "stage_id": "VALUE-CONSISTENCY",
            "phase_goal": (
                "lock owner or authorized-agent external action as a required precondition before raw-to-processed comparison"
            ),
            "task_count": 3,
            "acceptance_output": (
                "Raw comparison requirement manifest, summary, Go No-Go, private ignored requirement queue/report, "
                "validator, focused test and governance records"
            ),
        },
        ("phase_id", "record_type", "task_id"),
    )
    for suffix, task_goal in (
        ("T1", "read prior public binding requirement evidence and ignored private requirement queue read-only"),
        ("T2", "write ignored private raw comparison requirement queue and Chinese requirement report"),
        ("T3", "emit public-safe NO_GO requirement evidence while keeping comparison and upload closed"),
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
    source_summary = _read_json(SOURCE_BINDING_SUMMARY_PATH)
    source_manifest = _read_json(SOURCE_BINDING_MANIFEST_PATH)
    source_go_no_go = _read_json(SOURCE_BINDING_GO_NO_GO_PATH)
    source_matrix = _read_json(SOURCE_BINDING_MATRIX_PATH)
    source_binding_rows = _read_jsonl(SOURCE_PRIVATE_AUTHORITATIVE_BINDING_REQUIREMENT_QUEUE_PATH)
    if not SOURCE_PRIVATE_AUTHORITATIVE_BINDING_REQUIREMENT_DIAGNOSTIC_PATH.exists():
        raise FileNotFoundError(SOURCE_PRIVATE_AUTHORITATIVE_BINDING_REQUIREMENT_DIAGNOSTIC_PATH)
    if not SOURCE_PRIVATE_AUTHORITATIVE_BINDING_REQUIREMENT_REPORT_PATH.exists():
        raise FileNotFoundError(SOURCE_PRIVATE_AUTHORITATIVE_BINDING_REQUIREMENT_REPORT_PATH)
    _validate_sources(
        source_summary=source_summary,
        source_manifest=source_manifest,
        source_go_no_go=source_go_no_go,
        source_matrix=source_matrix,
        source_binding_rows=source_binding_rows,
    )
    requirement_rows = _build_requirement_records(generated_at=generated, source_binding_rows=source_binding_rows)
    summary = _build_summary(
        generated_at=generated,
        source_summary=source_summary,
        source_manifest=source_manifest,
        source_go_no_go=source_go_no_go,
        source_matrix=source_matrix,
        source_binding_rows=source_binding_rows,
        requirement_rows=requirement_rows,
    )
    matrix = _build_matrix(summary)
    go_no_go = _build_go_no_go(summary)
    manifest = _build_manifest(summary, matrix, go_no_go)
    _write_private_outputs(generated_at=generated, summary=summary, requirement_rows=requirement_rows)
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
        "private_raw_to_processed_value_comparison_requirement_queue": requirement_rows,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generated-at")
    args = parser.parse_args(argv)
    result = generate(generated_at=args.generated_at)
    summary = result["summary"]
    print(
        "PASS: generated V014 owner/authorized-agent external action required before raw comparison "
        f"ready={summary['raw_to_processed_value_comparison_requirement_ready_count']} "
        f"blockers={summary['raw_to_processed_value_comparison_requirement_blocker_count']} "
        f"goal={summary['goal_status_recommendation']} "
        f"decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
