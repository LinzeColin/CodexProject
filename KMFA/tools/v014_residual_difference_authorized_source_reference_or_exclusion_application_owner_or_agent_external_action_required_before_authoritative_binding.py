#!/usr/bin/env python3
"""Generate the external-action requirement gate before authoritative binding.

This phase consumes the previous public-safe external-action follow-up evidence
and the ignored private follow-up queue. It does not read the raw inbox and it
does not bind fingerprints, compare values, upload, reinstall, or execute
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
    v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_external_action_readiness_final_blocked_handoff_follow_up_after_final_threshold_handoff
    as source_follow_up,
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
    "EXTERNAL_ACTION_REQUIRED_BEFORE_AUTHORITATIVE_BINDING"
)
TASK_ID = (
    "KMFA-V014-RESIDUAL-DIFFERENCE-AUTHORIZED-SOURCE-REFERENCE-OR-EXCLUSION-APPLICATION-OWNER-OR-"
    "AGENT-EXTERNAL-ACTION-REQUIRED-BEFORE-AUTHORITATIVE-BINDING-20260708"
)
ACCEPTANCE_ID = (
    "ACC-V014-RESIDUAL-DIFFERENCE-AUTHORIZED-SOURCE-REFERENCE-OR-EXCLUSION-APPLICATION-OWNER-OR-"
    "AGENT-EXTERNAL-ACTION-REQUIRED-BEFORE-AUTHORITATIVE-BINDING"
)
VERSION = (
    "0.1.4-residual-difference-authorized-source-reference-or-exclusion-application-owner-or-agent-"
    "external-action-required-before-authoritative-binding"
)
STATUS = (
    "completed_validated_local_only_authorized_source_reference_or_exclusion_application_owner_or_agent_"
    "external_action_required_before_authoritative_binding_no_go_blocked"
)
DECISION = "NO_GO"
REQUIREMENT_CONCLUSION = (
    "blocked_owner_or_authorized_agent_external_action_required_before_authoritative_binding"
)
NEXT_REQUIRED_INPUT = source_follow_up.NEXT_REQUIRED_INPUT
NEXT_RECOMMENDED_PHASE = "owner_or_authorized_agent_external_action_required_before_raw_to_processed_value_comparison"

SOURCE_REFERENCE_DIAGNOSTIC_KIND = source_follow_up.SOURCE_REFERENCE_DIAGNOSTIC_KIND
FORMULA_MAPPING_DIAGNOSTIC_KIND = source_follow_up.FORMULA_MAPPING_DIAGNOSTIC_KIND

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
PREFIX = (
    "residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_"
    "external_action_required_before_authoritative_binding"
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

SOURCE_FOLLOW_UP_SUMMARY_PATH = source_follow_up.METADATA_SUMMARY_PATH
SOURCE_FOLLOW_UP_MANIFEST_PATH = source_follow_up.METADATA_MANIFEST_PATH
SOURCE_FOLLOW_UP_GO_NO_GO_PATH = source_follow_up.METADATA_GO_NO_GO_PATH
SOURCE_FOLLOW_UP_MATRIX_PATH = source_follow_up.METADATA_MATRIX_PATH
SOURCE_PRIVATE_EXTERNAL_ACTION_FOLLOW_UP_DIAGNOSTIC_PATH = (
    source_follow_up.PRIVATE_EXTERNAL_ACTION_FOLLOW_UP_DIAGNOSTIC_PATH
)
SOURCE_PRIVATE_EXTERNAL_ACTION_FOLLOW_UP_QUEUE_PATH = (
    source_follow_up.PRIVATE_EXTERNAL_ACTION_FOLLOW_UP_QUEUE_PATH
)
SOURCE_PRIVATE_EXTERNAL_ACTION_FOLLOW_UP_REPORT_PATH = (
    source_follow_up.PRIVATE_EXTERNAL_ACTION_FOLLOW_UP_REPORT_PATH
)

PRIVATE_OUTPUT_DIR = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_external_action_required_before_authoritative_binding"
)
PRIVATE_AUTHORITATIVE_BINDING_REQUIREMENT_DIAGNOSTIC_PATH = (
    PRIVATE_OUTPUT_DIR / "private_owner_or_agent_external_action_required_before_authoritative_binding_diagnostic.json"
)
PRIVATE_AUTHORITATIVE_BINDING_REQUIREMENT_QUEUE_PATH = (
    PRIVATE_OUTPUT_DIR / "private_owner_or_agent_external_action_required_before_authoritative_binding_queue.jsonl"
)
PRIVATE_AUTHORITATIVE_BINDING_REQUIREMENT_REPORT_PATH = (
    PRIVATE_OUTPUT_DIR / "private_owner_or_agent_external_action_required_before_authoritative_binding_report.md"
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
        "KMFA/metadata/quality/v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_external_action_required_before_authoritative_binding_summary.json",
        "KMFA/metadata/quality/v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_external_action_required_before_authoritative_binding_manifest.json",
        "KMFA/metadata/quality/v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_external_action_required_before_authoritative_binding_go_no_go_report.json",
        "KMFA/metadata/quality/v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_external_action_required_before_authoritative_binding_matrix_public_safe.json",
        "KMFA/metadata/stage_status.jsonl",
        "KMFA/metadata/traceability/v1_4_stage_phase_task_status.jsonl",
        "KMFA/stage_artifacts/V014_RESIDUAL_DIFFERENCE_AUTHORIZED_SOURCE_REFERENCE_OR_EXCLUSION_APPLICATION_OWNER_OR_AGENT_EXTERNAL_ACTION_REQUIRED_BEFORE_AUTHORITATIVE_BINDING/human/go_no_go_record.md",
        "KMFA/stage_artifacts/V014_RESIDUAL_DIFFERENCE_AUTHORIZED_SOURCE_REFERENCE_OR_EXCLUSION_APPLICATION_OWNER_OR_AGENT_EXTERNAL_ACTION_REQUIRED_BEFORE_AUTHORITATIVE_BINDING/human/residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_external_action_required_before_authoritative_binding.md",
        "KMFA/stage_artifacts/V014_RESIDUAL_DIFFERENCE_AUTHORIZED_SOURCE_REFERENCE_OR_EXCLUSION_APPLICATION_OWNER_OR_AGENT_EXTERNAL_ACTION_REQUIRED_BEFORE_AUTHORITATIVE_BINDING/human/risk_register.md",
        "KMFA/stage_artifacts/V014_RESIDUAL_DIFFERENCE_AUTHORIZED_SOURCE_REFERENCE_OR_EXCLUSION_APPLICATION_OWNER_OR_AGENT_EXTERNAL_ACTION_REQUIRED_BEFORE_AUTHORITATIVE_BINDING/human/rollback_plan.md",
        "KMFA/stage_artifacts/V014_RESIDUAL_DIFFERENCE_AUTHORIZED_SOURCE_REFERENCE_OR_EXCLUSION_APPLICATION_OWNER_OR_AGENT_EXTERNAL_ACTION_REQUIRED_BEFORE_AUTHORITATIVE_BINDING/human/test_results.md",
        "KMFA/stage_artifacts/V014_RESIDUAL_DIFFERENCE_AUTHORIZED_SOURCE_REFERENCE_OR_EXCLUSION_APPLICATION_OWNER_OR_AGENT_EXTERNAL_ACTION_REQUIRED_BEFORE_AUTHORITATIVE_BINDING/machine/residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_external_action_required_before_authoritative_binding_go_no_go_report.json",
        "KMFA/stage_artifacts/V014_RESIDUAL_DIFFERENCE_AUTHORIZED_SOURCE_REFERENCE_OR_EXCLUSION_APPLICATION_OWNER_OR_AGENT_EXTERNAL_ACTION_REQUIRED_BEFORE_AUTHORITATIVE_BINDING/machine/residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_external_action_required_before_authoritative_binding_manifest.json",
        "KMFA/stage_artifacts/V014_RESIDUAL_DIFFERENCE_AUTHORIZED_SOURCE_REFERENCE_OR_EXCLUSION_APPLICATION_OWNER_OR_AGENT_EXTERNAL_ACTION_REQUIRED_BEFORE_AUTHORITATIVE_BINDING/machine/residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_external_action_required_before_authoritative_binding_matrix_public_safe.json",
        "KMFA/stage_artifacts/V014_RESIDUAL_DIFFERENCE_AUTHORIZED_SOURCE_REFERENCE_OR_EXCLUSION_APPLICATION_OWNER_OR_AGENT_EXTERNAL_ACTION_REQUIRED_BEFORE_AUTHORITATIVE_BINDING/machine/residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_external_action_required_before_authoritative_binding_summary.json",
        "KMFA/tests/test_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_external_action_required_before_authoritative_binding.py",
        "KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_external_action_required_before_authoritative_binding.py",
        "KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_external_action_required_before_authoritative_binding.py",
    ]


def _raw_boundary() -> dict[str, bool]:
    return {
        "user_declared_raw_data_immutable": True,
        "raw_data_root_readonly_policy_active": True,
        "source_follow_up_public_artifacts_read_by_this_phase": True,
        "source_follow_up_manifest_read_by_this_phase": True,
        "source_follow_up_go_no_go_read_by_this_phase": True,
        "source_follow_up_matrix_read_by_this_phase": True,
        "source_private_follow_up_diagnostic_read_by_this_phase": True,
        "source_private_follow_up_queue_read_by_this_phase": True,
        "source_private_follow_up_report_existence_checked_by_this_phase": True,
        "private_authoritative_binding_requirement_diagnostic_written_by_this_phase": True,
        "private_authoritative_binding_requirement_queue_written_by_this_phase": True,
        "private_authoritative_binding_requirement_report_written_by_this_phase": True,
        "source_private_follow_up_diagnostic_mutated_by_this_phase": False,
        "source_private_follow_up_queue_mutated_by_this_phase": False,
        "source_private_follow_up_report_mutated_by_this_phase": False,
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
        "source_private_follow_up_diagnostic_committed": False,
        "source_private_follow_up_queue_committed": False,
        "source_private_follow_up_report_committed": False,
        "private_authoritative_binding_requirement_diagnostic_committed": False,
        "private_authoritative_binding_requirement_queue_committed": False,
        "private_authoritative_binding_requirement_report_committed": False,
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
        return "owner_authorized_source_reference_or_owner_exclusion_required_before_authoritative_binding"
    if diagnostic_kind == FORMULA_MAPPING_DIAGNOSTIC_KIND:
        return "owner_authorized_formula_or_non_numeric_mapping_required_before_authoritative_binding"
    return "owner_authorized_actionable_resolution_required_before_authoritative_binding"


def _validate_sources(
    *,
    source_summary: dict[str, Any],
    source_manifest: dict[str, Any],
    source_go_no_go: dict[str, Any],
    source_matrix: dict[str, Any],
    source_follow_up_rows: list[dict[str, Any]],
) -> None:
    if source_summary.get("phase_id") != source_follow_up.PHASE_ID:
        raise ValueError("source follow-up phase mismatch")
    if source_manifest.get("phase_id") != source_follow_up.PHASE_ID:
        raise ValueError("source follow-up manifest phase mismatch")
    if source_go_no_go.get("decision") != "NO_GO":
        raise ValueError("source follow-up decision must be NO_GO")
    if source_matrix.get("check_fail_count") != 0:
        raise ValueError("source follow-up matrix must be clean")
    if source_summary.get("external_action_follow_up_ready_count") != 0:
        raise ValueError("source follow-up ready count must be 0")
    if source_summary.get("external_action_follow_up_blocker_count") != 48:
        raise ValueError("source follow-up blocker count must be 48")
    if source_summary.get("external_action_follow_up_required_count") != 48:
        raise ValueError("source follow-up required count must be 48")
    if source_summary.get("goal_status_recommendation") != "blocked":
        raise ValueError("source goal status must be blocked")
    if len(source_follow_up_rows) != 48:
        raise ValueError("source private follow-up queue must contain 48 rows")
    for row in source_follow_up_rows:
        if row.get("external_action_follow_up_status") != source_follow_up.FOLLOW_UP_CONCLUSION:
            raise ValueError("source follow-up row has unexpected status")
        if row.get("external_action_follow_up_ready") is not False:
            raise ValueError("source follow-up row cannot be ready")
        if row.get("external_action_follow_up_blocker") is not True:
            raise ValueError("source follow-up row must remain blocker")
        if row.get("authoritative_binding_application_ready") is not False:
            raise ValueError("source follow-up row cannot be binding-ready")
        if row.get("raw_to_processed_value_comparison_ready") is not False:
            raise ValueError("source follow-up row cannot be comparison-ready")
        if row.get("public_commit_allowed") is not False:
            raise ValueError("source follow-up row cannot be public-committable")


def _build_requirement_records(
    *, generated_at: str, source_follow_up_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, row in enumerate(source_follow_up_rows, start=1):
        diagnostic_kind = str(row.get("diagnostic_kind"))
        records.append(
            {
                "authoritative_binding_requirement_item_id": f"ASR-OE-APP-OWNER-AGENT-BINDING-REQ-{index:03d}",
                "source_external_action_follow_up_item_id": row.get("external_action_follow_up_item_id"),
                "source_action_readiness_item_id": row.get("source_action_readiness_item_id"),
                "source_owner_action_item_id": row.get("source_owner_action_item_id"),
                "source_blocked_handoff_item_id": row.get("source_blocked_handoff_item_id"),
                "phase_id": PHASE_ID,
                "task_id": TASK_ID,
                "generated_at": generated_at,
                "target_slot_id": row.get("target_slot_id"),
                "diagnostic_kind": diagnostic_kind,
                "authoritative_binding_requirement_status": REQUIREMENT_CONCLUSION,
                "authoritative_binding_requirement_required": True,
                "authoritative_binding_requirement_ready": False,
                "authoritative_binding_requirement_blocker": True,
                "authoritative_binding_requirement_reason": _blocker_reason(diagnostic_kind),
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
    source_follow_up_rows: list[dict[str, Any]],
    requirement_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    counts = Counter(str(row.get("diagnostic_kind")) for row in requirement_rows)
    return {
        "schema_version": "kmfa.v014_owner_agent_external_action_required_before_authoritative_binding_summary.v1",
        "record_type": "v014_owner_agent_external_action_required_before_authoritative_binding_summary",
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
        "source_external_action_follow_up_ready_count": source_summary.get("external_action_follow_up_ready_count"),
        "source_external_action_follow_up_blocker_count": source_summary.get(
            "external_action_follow_up_blocker_count"
        ),
        "source_external_action_follow_up_required_count": source_summary.get(
            "external_action_follow_up_required_count"
        ),
        "source_private_external_action_follow_up_queue_item_count": len(source_follow_up_rows),
        "source_goal_status_recommendation": source_summary.get("goal_status_recommendation"),
        "goal_status_recommendation": "blocked",
        "authoritative_binding_requirement_ready_count": 0,
        "authoritative_binding_requirement_blocker_count": len(requirement_rows),
        "authoritative_binding_requirement_required_count": len(requirement_rows),
        "actionable_owner_resolution_count": 0,
        "source_reference_or_owner_exclusion_binding_requirement_count": counts[SOURCE_REFERENCE_DIAGNOSTIC_KIND],
        "formula_or_non_numeric_mapping_binding_requirement_count": counts[FORMULA_MAPPING_DIAGNOSTIC_KIND],
        "authoritative_binding_application_ready_count": 0,
        "unresolved_difference_count": source_summary.get("unresolved_difference_count"),
        "private_authoritative_binding_requirement_diagnostic_written": True,
        "private_authoritative_binding_requirement_queue_written": True,
        "private_authoritative_binding_requirement_report_written": True,
        "private_authoritative_binding_requirement_diagnostic_gitignored": _git_check_ignored(
            PRIVATE_AUTHORITATIVE_BINDING_REQUIREMENT_DIAGNOSTIC_PATH
        ),
        "private_authoritative_binding_requirement_queue_gitignored": _git_check_ignored(
            PRIVATE_AUTHORITATIVE_BINDING_REQUIREMENT_QUEUE_PATH
        ),
        "private_authoritative_binding_requirement_report_gitignored": _git_check_ignored(
            PRIVATE_AUTHORITATIVE_BINDING_REQUIREMENT_REPORT_PATH
        ),
        "source_private_external_action_follow_up_diagnostic_gitignored": _git_check_ignored(
            SOURCE_PRIVATE_EXTERNAL_ACTION_FOLLOW_UP_DIAGNOSTIC_PATH
        ),
        "source_private_external_action_follow_up_queue_gitignored": _git_check_ignored(
            SOURCE_PRIVATE_EXTERNAL_ACTION_FOLLOW_UP_QUEUE_PATH
        ),
        "source_private_external_action_follow_up_report_gitignored": _git_check_ignored(
            SOURCE_PRIVATE_EXTERNAL_ACTION_FOLLOW_UP_REPORT_PATH
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
        ("source_follow_up_phase_loaded", summary["source_phase_id"] == source_follow_up.PHASE_ID),
        ("source_go_no_go_preserved", summary["source_go_no_go_decision"] == "NO_GO"),
        ("source_matrix_clean", summary["source_matrix_check_fail_count"] == 0),
        ("source_follow_up_blockers_complete", summary["source_external_action_follow_up_blocker_count"] == 48),
        ("source_private_follow_up_queue_read", summary["source_private_external_action_follow_up_queue_item_count"] == 48),
        ("binding_requirement_queue_complete", summary["authoritative_binding_requirement_required_count"] == 48),
        ("binding_requirement_blockers_locked", summary["authoritative_binding_requirement_blocker_count"] == 48),
        (
            "diagnostic_kind_binding_requirement_counts_locked",
            summary["source_reference_or_owner_exclusion_binding_requirement_count"] == 40
            and summary["formula_or_non_numeric_mapping_binding_requirement_count"] == 8,
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
        "schema_version": "kmfa.v014_owner_agent_external_action_required_before_authoritative_binding_matrix.v1",
        "record_type": "v014_owner_agent_external_action_required_before_authoritative_binding_matrix_public_safe",
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
        "schema_version": "kmfa.v014_owner_agent_external_action_required_before_authoritative_binding_go_no_go.v1",
        "record_type": "v014_owner_agent_external_action_required_before_authoritative_binding_go_no_go",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": summary["generated_at"],
        "status": STATUS,
        "decision": DECISION,
        "requirement_conclusion": REQUIREMENT_CONCLUSION,
        "source_external_action_follow_up_ready_count": summary["source_external_action_follow_up_ready_count"],
        "source_external_action_follow_up_blocker_count": summary["source_external_action_follow_up_blocker_count"],
        "source_external_action_follow_up_required_count": summary["source_external_action_follow_up_required_count"],
        "authoritative_binding_requirement_ready_count": 0,
        "authoritative_binding_requirement_blocker_count": summary[
            "authoritative_binding_requirement_blocker_count"
        ],
        "authoritative_binding_requirement_required_count": summary[
            "authoritative_binding_requirement_required_count"
        ],
        "actionable_owner_resolution_count": 0,
        "source_reference_or_owner_exclusion_binding_requirement_count": summary[
            "source_reference_or_owner_exclusion_binding_requirement_count"
        ],
        "formula_or_non_numeric_mapping_binding_requirement_count": summary[
            "formula_or_non_numeric_mapping_binding_requirement_count"
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
            "owner_or_agent_external_action_required_before_authoritative_binding.py --generated-at "
            "2026-07-08T00:00:00+10:00"
        ),
        (
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 "
            "KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_"
            "owner_or_agent_external_action_required_before_authoritative_binding.py "
            "--require-private-authoritative-binding-requirement"
        ),
        (
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest "
            "KMFA.tests.test_v014_residual_difference_authorized_source_reference_or_exclusion_application_"
            "owner_or_agent_external_action_required_before_authoritative_binding"
        ),
    ]


def _build_manifest(summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v014_owner_agent_external_action_required_before_authoritative_binding_manifest.v1",
        "record_type": "v014_owner_agent_external_action_required_before_authoritative_binding_manifest",
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
            "source_follow_up_public_summary": "public_safe_metadata_copy",
            "source_follow_up_public_manifest": "public_safe_metadata_copy",
            "source_follow_up_public_go_no_go": "public_safe_metadata_copy",
            "source_follow_up_public_matrix": "public_safe_metadata_copy",
            "source_private_follow_up_diagnostic": "ignored_private_runtime",
            "source_private_follow_up_queue": "ignored_private_runtime",
            "source_private_follow_up_report": "ignored_private_runtime",
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
            "private:owner_or_agent_external_action_required_before_authoritative_binding_diagnostic",
            "private:owner_or_agent_external_action_required_before_authoritative_binding_queue",
            "private:owner_or_agent_external_action_required_before_authoritative_binding_report",
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
        PRIVATE_AUTHORITATIVE_BINDING_REQUIREMENT_DIAGNOSTIC_PATH,
        {
            "schema_version": "kmfa.private.v014_owner_agent_external_action_required_before_authoritative_binding.v1",
            "classification": "private_owner_or_agent_authoritative_binding_requirement_do_not_commit",
            "record_type": "v014_owner_agent_authoritative_binding_requirement_private_diagnostic",
            "project_id": "KMFA",
            "version": VERSION,
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "generated_at": generated_at,
            "authoritative_binding_requirement_rows": requirement_rows,
            "summary_private": {
                "authoritative_binding_requirement_blocker_count": len(requirement_rows),
                "authoritative_binding_requirement_ready_count": 0,
                "authoritative_binding_requirement_required_count": len(requirement_rows),
                "goal_status_recommendation": "blocked",
                "source_reference_or_owner_exclusion_binding_requirement_count": counts[
                    SOURCE_REFERENCE_DIAGNOSTIC_KIND
                ],
                "formula_or_non_numeric_mapping_binding_requirement_count": counts[FORMULA_MAPPING_DIAGNOSTIC_KIND],
                "authoritative_binding_application_ready_count": 0,
            },
            "raw_boundary": summary["raw_boundary"],
        },
    )
    _write_jsonl(PRIVATE_AUTHORITATIVE_BINDING_REQUIREMENT_QUEUE_PATH, requirement_rows)
    report_lines = [
        "# owner/授权代理 external action required before authoritative binding 队列",
        "",
        f"- phase_id: `{PHASE_ID}`",
        f"- authoritative_binding_requirement_blocker_count: `{len(requirement_rows)}`",
        f"- source reference / owner exclusion requirement: `{counts[SOURCE_REFERENCE_DIAGNOSTIC_KIND]}`",
        f"- formula / non-numeric mapping requirement: `{counts[FORMULA_MAPPING_DIAGNOSTIC_KIND]}`",
        "- raw inbox touched: `false`",
        "",
        "## authoritative binding 前置要求",
        "",
        "1. source reference / owner exclusion 类 blocker 必须由 owner 或授权代理提供可执行依据或明确排除。",
        "2. formula / non-numeric mapping 类 blocker 必须由 owner 或授权代理提供可执行公式映射或非数值映射依据。",
        "3. 在上述动作完成前，不允许绑定 raw candidate fingerprint、执行 raw-to-processed value comparison 或业务执行。",
        "",
        "当前未检测到可执行 owner/授权代理外部动作，因此 authoritative binding 继续关闭。",
        "",
    ]
    _write_text(PRIVATE_AUTHORITATIVE_BINDING_REQUIREMENT_REPORT_PATH, "\n".join(report_lines))


def _write_human(summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any]) -> None:
    _write_text(
        REPORT_PATH,
        f"""# V014 Owner / Authorized Agent External Action Required Before Authoritative Binding

Generated at: {summary["generated_at"]}

## Scope

- Phase: `{PHASE_ID}`
- Decision: `{DECISION}`
- Status: `{STATUS}`
- Source: prior public-safe external-action follow-up evidence plus ignored private follow-up queue.
- Raw boundary: no raw inbox read, list, stat, parse, value extraction, write, delete, move, rename, copy, normalize or mutation.

## Public-Safe Binding Requirement Result

- Source follow-up ready count: `{summary["source_external_action_follow_up_ready_count"]}`
- Source follow-up blocker count: `{summary["source_external_action_follow_up_blocker_count"]}`
- Source follow-up required count: `{summary["source_external_action_follow_up_required_count"]}`
- Binding requirement ready count: `{summary["authoritative_binding_requirement_ready_count"]}`
- Binding requirement required count: `{summary["authoritative_binding_requirement_required_count"]}`
- Binding requirement blocker count: `{summary["authoritative_binding_requirement_blocker_count"]}`
- Actionable owner resolution count: `{summary["actionable_owner_resolution_count"]}`
- Source reference or owner exclusion binding requirement: `{summary["source_reference_or_owner_exclusion_binding_requirement_count"]}`
- Formula or non-numeric mapping binding requirement: `{summary["formula_or_non_numeric_mapping_binding_requirement_count"]}`
- Authoritative binding application ready count: `{summary["authoritative_binding_application_ready_count"]}`
- Unresolved differences: `{summary["unresolved_difference_count"]}`

## Gate

No executable owner/authorized-agent source reference, owner exclusion, formula mapping or non-numeric mapping has been provided after the external-action follow-up. This phase records the private authoritative-binding requirement queue only and does not authorize binding, raw-to-processed value comparison, reconciliation, business consistency, GitHub upload, app reinstall or business execution.

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

- RED: focused unittest failed before implementation because the authoritative-binding requirement generator was missing.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_external_action_required_before_authoritative_binding.py --generated-at 2026-07-08T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_external_action_required_before_authoritative_binding.py --require-private-authoritative-binding-requirement`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_external_action_required_before_authoritative_binding`
- Governance validators, CSV shape checks, diff check, raw/private marker scan, secret scan and private-runtime tracked-file scan: expected before commit.

Expected matrix result: {matrix["check_pass_count"]}/{matrix["check_count"]} PASS.
""",
    )
    _write_text(
        RISK_REGISTER_PATH,
        """# Risk Register

- Risk: binding requirement queue is mistaken for permission to bind fields or compare values.
- Control: decision remains NO_GO and all downstream gates remain false.
- Risk: private source handles leak into public evidence.
- Control: public artifacts contain aggregate counts only; detailed requirement rows stay ignored.
- Risk: raw inbox is modified.
- Control: this phase consumes existing follow-up artifacts only and does not touch the raw inbox.
""",
    )
    _write_text(
        ROLLBACK_PATH,
        f"""# Rollback Plan

Remove artifacts for `{PHASE_ID}`, metadata copies, private authoritative-binding requirement outputs, tool, validator, focused test and governance rows. Do not touch source follow-up evidence or raw inbox files.
""",
    )


def _write_governance_events(generated_at: str, summary: dict[str, Any]) -> None:
    event_id = (
        "DEV-KMFA-20260708-V014-AUTHORIZED-SOURCE-REFERENCE-OR-EXCLUSION-APPLICATION-OWNER-OR-AGENT-"
        "EXTERNAL-ACTION-REQUIRED-BEFORE-AUTHORITATIVE-BINDING"
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
                "Generated a private owner/authorized-agent authoritative-binding requirement queue; "
                "48 blockers remain and binding, value comparison, upload and execution stay closed."
            ),
            "evidence_ref": MANIFEST_PATH.as_posix(),
            "files_changed": _phase_public_files(),
            "test_commands": _test_commands(),
            "test_results": ["PENDING: final validation results will be recorded before local commit."],
            "authoritative_binding_requirement_ready_count": summary[
                "authoritative_binding_requirement_ready_count"
            ],
            "authoritative_binding_requirement_blocker_count": summary[
                "authoritative_binding_requirement_blocker_count"
            ],
            "authoritative_binding_requirement_required_count": summary[
                "authoritative_binding_requirement_required_count"
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
            "name": "v0.1.4 owner or authorized agent external action required before authoritative binding",
            "status": STATUS,
            "completed_task_units": 1,
            "estimated_task_units": 1,
            "derived_percent": 100.0,
            "acceptance_id": ACCEPTANCE_ID,
            "evidence_ref": MANIFEST_PATH.as_posix(),
            "fact_level": "EXTRACTED",
            "updated_at": generated_at[:10],
            "stage_id": "VALUE-CONSISTENCY",
            "phase_goal": "lock owner or authorized-agent external action as a required precondition before authoritative binding",
            "task_count": 3,
            "acceptance_output": (
                "Binding requirement manifest, summary, Go No-Go, private ignored requirement queue/report, "
                "validator, focused test and governance records"
            ),
        },
        ("phase_id", "record_type", "task_id"),
    )
    for suffix, task_goal in (
        ("T1", "read prior public follow-up evidence and ignored private follow-up queue read-only"),
        ("T2", "write ignored private authoritative-binding requirement queue and Chinese requirement report"),
        ("T3", "emit public-safe NO_GO requirement evidence while keeping binding comparison and upload closed"),
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
    source_summary = _read_json(SOURCE_FOLLOW_UP_SUMMARY_PATH)
    source_manifest = _read_json(SOURCE_FOLLOW_UP_MANIFEST_PATH)
    source_go_no_go = _read_json(SOURCE_FOLLOW_UP_GO_NO_GO_PATH)
    source_matrix = _read_json(SOURCE_FOLLOW_UP_MATRIX_PATH)
    source_follow_up_rows = _read_jsonl(SOURCE_PRIVATE_EXTERNAL_ACTION_FOLLOW_UP_QUEUE_PATH)
    if not SOURCE_PRIVATE_EXTERNAL_ACTION_FOLLOW_UP_DIAGNOSTIC_PATH.exists():
        raise FileNotFoundError(SOURCE_PRIVATE_EXTERNAL_ACTION_FOLLOW_UP_DIAGNOSTIC_PATH)
    if not SOURCE_PRIVATE_EXTERNAL_ACTION_FOLLOW_UP_REPORT_PATH.exists():
        raise FileNotFoundError(SOURCE_PRIVATE_EXTERNAL_ACTION_FOLLOW_UP_REPORT_PATH)
    _validate_sources(
        source_summary=source_summary,
        source_manifest=source_manifest,
        source_go_no_go=source_go_no_go,
        source_matrix=source_matrix,
        source_follow_up_rows=source_follow_up_rows,
    )
    requirement_rows = _build_requirement_records(generated_at=generated, source_follow_up_rows=source_follow_up_rows)
    summary = _build_summary(
        generated_at=generated,
        source_summary=source_summary,
        source_manifest=source_manifest,
        source_go_no_go=source_go_no_go,
        source_matrix=source_matrix,
        source_follow_up_rows=source_follow_up_rows,
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
        "private_authoritative_binding_requirement_queue": requirement_rows,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generated-at")
    args = parser.parse_args(argv)
    result = generate(generated_at=args.generated_at)
    summary = result["summary"]
    print(
        "PASS: generated V014 owner/authorized-agent external action required before authoritative binding "
        f"ready={summary['authoritative_binding_requirement_ready_count']} "
        f"blockers={summary['authoritative_binding_requirement_blocker_count']} "
        f"goal={summary['goal_status_recommendation']} "
        f"decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
