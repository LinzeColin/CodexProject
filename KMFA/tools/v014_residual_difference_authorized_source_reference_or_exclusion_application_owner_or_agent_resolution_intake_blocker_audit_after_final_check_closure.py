#!/usr/bin/env python3
"""Audit owner/authorized-agent resolution-intake blockers after final-check closure."""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools import (  # noqa: E402
    v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_resolution_intake_after_final_check_closure
    as source_intake,
)
from KMFA.tools.v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_resolution_intake_after_final_check_closure import (  # noqa: E402
    _git_check_ignored,
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
    "RESOLUTION_INTAKE_BLOCKER_AUDIT_AFTER_FINAL_CHECK_CLOSURE"
)
TASK_ID = (
    "KMFA-V014-RESIDUAL-DIFFERENCE-AUTHORIZED-SOURCE-REFERENCE-OR-EXCLUSION-APPLICATION-OWNER-OR-"
    "AGENT-RESOLUTION-INTAKE-BLOCKER-AUDIT-AFTER-FINAL-CHECK-CLOSURE-20260708"
)
ACCEPTANCE_ID = (
    "ACC-V014-RESIDUAL-DIFFERENCE-AUTHORIZED-SOURCE-REFERENCE-OR-EXCLUSION-APPLICATION-OWNER-OR-"
    "AGENT-RESOLUTION-INTAKE-BLOCKER-AUDIT-AFTER-FINAL-CHECK-CLOSURE"
)
VERSION = (
    "0.1.4-residual-difference-authorized-source-reference-or-exclusion-application-owner-or-agent-"
    "resolution-intake-blocker-audit-after-final-check-closure"
)
STATUS = (
    "completed_validated_local_only_authorized_source_reference_or_exclusion_application_owner_or_agent_"
    "resolution_intake_blocker_audit_after_final_check_closure_no_go_blocked_first_observation"
)
DECISION = "NO_GO"
AUDIT_CONCLUSION = "blocked_first_resolution_intake_blocker_observation_no_owner_or_authorized_agent_resolution"
NEXT_REQUIRED_INPUT = source_intake.NEXT_REQUIRED_INPUT
NEXT_RECOMMENDED_PHASE = "owner_or_authorized_agent_resolution_intake_blocker_recheck_after_final_check_closure"

SOURCE_REFERENCE_DIAGNOSTIC_KIND = source_intake.SOURCE_REFERENCE_DIAGNOSTIC_KIND
FORMULA_MAPPING_DIAGNOSTIC_KIND = source_intake.FORMULA_MAPPING_DIAGNOSTIC_KIND

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
PREFIX = (
    "residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_"
    "resolution_intake_blocker_audit_after_final_check_closure"
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

SOURCE_RESOLUTION_INTAKE_SUMMARY_PATH = source_intake.METADATA_SUMMARY_PATH
SOURCE_RESOLUTION_INTAKE_MANIFEST_PATH = source_intake.METADATA_MANIFEST_PATH
SOURCE_RESOLUTION_INTAKE_GO_NO_GO_PATH = source_intake.METADATA_GO_NO_GO_PATH
SOURCE_RESOLUTION_INTAKE_MATRIX_PATH = source_intake.METADATA_MATRIX_PATH
SOURCE_PRIVATE_RESOLUTION_INTAKE_DIAGNOSTIC_PATH = (
    source_intake.PRIVATE_OWNER_OR_AUTHORIZED_AGENT_RESOLUTION_INTAKE_DIAGNOSTIC_PATH
)
SOURCE_PRIVATE_RESOLUTION_INTAKE_QUEUE_PATH = source_intake.PRIVATE_OWNER_OR_AUTHORIZED_AGENT_RESOLUTION_INTAKE_QUEUE_PATH
SOURCE_PRIVATE_RESOLUTION_INTAKE_REPORT_PATH = source_intake.PRIVATE_OWNER_OR_AUTHORIZED_AGENT_RESOLUTION_INTAKE_REPORT_PATH

PRIVATE_OUTPUT_DIR = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_resolution_intake_blocker_audit_after_final_check_closure"
)
PRIVATE_RESOLUTION_INTAKE_BLOCKER_AUDIT_DIAGNOSTIC_PATH = (
    PRIVATE_OUTPUT_DIR / "private_owner_or_authorized_agent_resolution_intake_blocker_audit_diagnostic.json"
)
PRIVATE_RESOLUTION_INTAKE_BLOCKER_AUDIT_QUEUE_PATH = (
    PRIVATE_OUTPUT_DIR / "private_owner_or_authorized_agent_resolution_intake_blocker_audit_queue.jsonl"
)
PRIVATE_RESOLUTION_INTAKE_BLOCKER_AUDIT_REPORT_PATH = (
    PRIVATE_OUTPUT_DIR / "private_owner_or_authorized_agent_resolution_intake_blocker_audit_report.md"
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
        (
            "KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_"
            "owner_or_agent_resolution_intake_blocker_audit_after_final_check_closure.py"
        ),
        (
            "KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_"
            "owner_or_agent_resolution_intake_blocker_audit_after_final_check_closure.py"
        ),
        (
            "KMFA/tests/test_v014_residual_difference_authorized_source_reference_or_exclusion_application_"
            "owner_or_agent_resolution_intake_blocker_audit_after_final_check_closure.py"
        ),
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
    return static + [path.as_posix() for path in artifacts]


def _raw_boundary() -> dict[str, bool]:
    return {
        "user_declared_raw_data_immutable": True,
        "raw_data_root_readonly_policy_active": True,
        "source_resolution_intake_public_artifacts_read_by_this_phase": True,
        "source_resolution_intake_manifest_read_by_this_phase": True,
        "source_resolution_intake_go_no_go_read_by_this_phase": True,
        "source_resolution_intake_matrix_read_by_this_phase": True,
        "source_private_resolution_intake_diagnostic_read_by_this_phase": True,
        "source_private_resolution_intake_queue_read_by_this_phase": True,
        "source_private_resolution_intake_report_existence_checked_by_this_phase": True,
        "private_resolution_intake_blocker_audit_diagnostic_written_by_this_phase": True,
        "private_resolution_intake_blocker_audit_queue_written_by_this_phase": True,
        "private_resolution_intake_blocker_audit_report_written_by_this_phase": True,
        "source_private_resolution_intake_diagnostic_mutated_by_this_phase": False,
        "source_private_resolution_intake_queue_mutated_by_this_phase": False,
        "source_private_resolution_intake_report_mutated_by_this_phase": False,
        "owner_or_authorized_agent_resolution_completed_by_this_phase": False,
        "authoritative_binding_applied_by_this_phase": False,
        "raw_candidate_fingerprint_bound_by_this_phase": False,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "processed_data_reconciliation_performed_by_this_phase": False,
        "business_value_consistency_verified_by_this_phase": False,
        "lineage_full_check_performed_by_this_phase": False,
        "github_upload_performed_by_this_phase": False,
        "app_reinstall_performed_by_this_phase": False,
        "business_execution_performed_by_this_phase": False,
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
        "source_private_resolution_intake_diagnostic_committed": False,
        "source_private_resolution_intake_queue_committed": False,
        "source_private_resolution_intake_report_committed": False,
        "private_resolution_intake_blocker_audit_diagnostic_committed": False,
        "private_resolution_intake_blocker_audit_queue_committed": False,
        "private_resolution_intake_blocker_audit_report_committed": False,
        "target_slot_detail_committed": False,
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


def _validate_sources(
    *,
    source_summary: dict[str, Any],
    source_manifest: dict[str, Any],
    source_go_no_go: dict[str, Any],
    source_matrix: dict[str, Any],
    intake_rows: list[dict[str, Any]],
) -> None:
    if source_summary.get("phase_id") != source_intake.PHASE_ID:
        raise ValueError("source resolution-intake phase mismatch")
    if source_manifest.get("phase_id") != source_intake.PHASE_ID:
        raise ValueError("source resolution-intake manifest phase mismatch")
    if source_go_no_go.get("decision") != "NO_GO":
        raise ValueError("source resolution-intake decision must be NO_GO")
    if source_matrix.get("check_fail_count") != 0:
        raise ValueError("source resolution-intake matrix must be clean")
    expected_counts = {
        "owner_or_authorized_agent_resolution_intake_ready_count": 0,
        "owner_or_authorized_agent_resolution_intake_blocker_count": 48,
        "owner_or_authorized_agent_resolution_intake_required_count": 48,
        "owner_or_authorized_agent_resolution_count": 0,
        "business_execution_ready_count": 0,
        "unresolved_difference_count": 72,
    }
    for key, expected in expected_counts.items():
        if source_summary.get(key) != expected:
            raise ValueError(f"source resolution-intake {key} must be {expected}")
    if source_summary.get("goal_status_recommendation") != "blocked":
        raise ValueError("source resolution-intake goal status must be blocked")
    if len(intake_rows) != 48:
        raise ValueError("source private resolution-intake queue must contain 48 rows")
    for row in intake_rows:
        if row.get("owner_or_authorized_agent_resolution_intake_status") != source_intake.REQUIREMENT_CONCLUSION:
            raise ValueError("source resolution-intake row status mismatch")
        if row.get("owner_or_authorized_agent_resolution_intake_ready") is not False:
            raise ValueError("source resolution-intake row cannot be ready")
        if row.get("owner_or_authorized_agent_resolution_intake_blocker") is not True:
            raise ValueError("source resolution-intake row must be blocked")
        if row.get("public_commit_allowed") is not False:
            raise ValueError("source resolution-intake row cannot be public-committable")


def _build_audit_queue(*, generated_at: str, intake_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    queue: list[dict[str, Any]] = []
    for index, row in enumerate(intake_rows, start=1):
        queue.append(
            {
                "resolution_intake_blocker_audit_item_id": (
                    f"ASR-OE-APP-OWNER-AGENT-RESOLUTION-INTAKE-BLOCKER-AUDIT-{index:03d}"
                ),
                "source_owner_or_authorized_agent_resolution_intake_item_id": row.get(
                    "owner_or_authorized_agent_resolution_intake_item_id"
                ),
                "source_final_check_closure_item_id": row.get("source_final_check_closure_item_id"),
                "source_business_execution_blocked_follow_up_continuation_recheck_follow_up_final_check_item_id": row.get(
                    "source_business_execution_blocked_follow_up_continuation_recheck_follow_up_final_check_item_id"
                ),
                "source_external_action_follow_up_item_id": row.get("source_external_action_follow_up_item_id"),
                "source_action_readiness_item_id": row.get("source_action_readiness_item_id"),
                "source_owner_action_item_id": row.get("source_owner_action_item_id"),
                "phase_id": PHASE_ID,
                "task_id": TASK_ID,
                "generated_at": generated_at,
                "target_slot_id": row.get("target_slot_id"),
                "diagnostic_kind": row.get("diagnostic_kind"),
                "source_resolution_intake_status": row.get("owner_or_authorized_agent_resolution_intake_status"),
                "resolution_intake_blocker_audit_status": AUDIT_CONCLUSION,
                "resolution_intake_blocker_audit_ready": False,
                "resolution_intake_blocker_audit_blocker": True,
                "resolution_intake_blocker_observation_count": 1,
                "resolution_intake_blocker_audit_threshold_met": False,
                "owner_or_authorized_agent_resolution_intake_ready": False,
                "owner_or_authorized_agent_resolution_intake_blocker": True,
                "owner_or_authorized_agent_resolution_completed_by_this_phase": False,
                "owner_or_authorized_agent_resolution_count": 0,
                "actionable_owner_resolution_ready": False,
                "authoritative_binding_application_ready": False,
                "authoritative_binding_applied_by_this_phase": False,
                "raw_candidate_fingerprint_bound_by_this_phase": False,
                "raw_to_processed_value_comparison_ready": False,
                "raw_to_processed_value_comparison_performed_by_this_phase": False,
                "processed_data_reconciliation_ready": False,
                "processed_data_reconciliation_performed_by_this_phase": False,
                "business_value_consistency_ready": False,
                "business_value_consistency_verified": False,
                "business_value_consistency_verified_by_this_phase": False,
                "lineage_full_check_ready": False,
                "lineage_full_check_performed_by_this_phase": False,
                "lineage_full_check_complete": False,
                "github_upload_ready": False,
                "github_upload_allowed": False,
                "github_upload_performed_by_this_phase": False,
                "app_reinstall_ready": False,
                "app_reinstall_allowed": False,
                "app_reinstall_performed_by_this_phase": False,
                "business_execution_ready": False,
                "business_execution_allowed": False,
                "business_execution_performed_by_this_phase": False,
                "public_commit_allowed": False,
            }
        )
    return queue


def _build_summary(
    *,
    generated_at: str,
    source_summary: dict[str, Any],
    source_manifest: dict[str, Any],
    source_go_no_go: dict[str, Any],
    source_matrix: dict[str, Any],
    intake_rows: list[dict[str, Any]],
    audit_queue: list[dict[str, Any]],
) -> dict[str, Any]:
    counts = Counter(str(row.get("diagnostic_kind")) for row in audit_queue)
    return {
        "schema_version": "kmfa.v014_owner_authorized_agent_resolution_intake_blocker_audit_after_final_check_closure_summary.v1",
        "record_type": "v014_owner_authorized_agent_resolution_intake_blocker_audit_after_final_check_closure_summary",
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
        "source_matrix_check_count": source_matrix.get("check_count"),
        "source_resolution_intake_ready_count": source_summary.get("owner_or_authorized_agent_resolution_intake_ready_count"),
        "source_resolution_intake_blocker_count": source_summary.get(
            "owner_or_authorized_agent_resolution_intake_blocker_count"
        ),
        "source_resolution_intake_item_count": source_summary.get("owner_or_authorized_agent_resolution_intake_item_count"),
        "source_resolution_intake_required_count": source_summary.get(
            "owner_or_authorized_agent_resolution_intake_required_count"
        ),
        "source_private_resolution_intake_queue_item_count": len(intake_rows),
        "source_goal_status_recommendation": source_summary.get("goal_status_recommendation"),
        "goal_status_recommendation": "blocked",
        "prior_resolution_intake_blocker_observation_count": 0,
        "resolution_intake_blocker_observation_count": 1,
        "resolution_intake_blocker_audit_threshold_met": False,
        "resolution_intake_blocker_audit_ready_count": 0,
        "resolution_intake_blocker_audit_blocker_count": len(audit_queue),
        "resolution_intake_blocker_audit_item_count": len(audit_queue),
        "private_audit_queue_item_count": len(audit_queue),
        "actionable_owner_resolution_count": 0,
        "owner_or_authorized_agent_resolution_count": 0,
        "source_reference_or_owner_exclusion_audit_blocker_count": counts[SOURCE_REFERENCE_DIAGNOSTIC_KIND],
        "formula_or_non_numeric_mapping_audit_blocker_count": counts[FORMULA_MAPPING_DIAGNOSTIC_KIND],
        "authoritative_binding_application_ready_count": 0,
        "raw_to_processed_value_comparison_ready_count": 0,
        "processed_data_reconciliation_ready_count": 0,
        "business_value_consistency_ready_count": 0,
        "lineage_full_check_ready_count": 0,
        "business_execution_ready_count": 0,
        "unresolved_difference_count": source_summary.get("unresolved_difference_count"),
        "private_resolution_intake_blocker_audit_diagnostic_written": True,
        "private_resolution_intake_blocker_audit_queue_written": True,
        "private_resolution_intake_blocker_audit_report_written": True,
        "private_resolution_intake_blocker_audit_diagnostic_gitignored": _git_check_ignored(
            PRIVATE_RESOLUTION_INTAKE_BLOCKER_AUDIT_DIAGNOSTIC_PATH
        ),
        "private_resolution_intake_blocker_audit_queue_gitignored": _git_check_ignored(
            PRIVATE_RESOLUTION_INTAKE_BLOCKER_AUDIT_QUEUE_PATH
        ),
        "private_resolution_intake_blocker_audit_report_gitignored": _git_check_ignored(
            PRIVATE_RESOLUTION_INTAKE_BLOCKER_AUDIT_REPORT_PATH
        ),
        "source_private_resolution_intake_diagnostic_gitignored": _git_check_ignored(
            SOURCE_PRIVATE_RESOLUTION_INTAKE_DIAGNOSTIC_PATH
        ),
        "source_private_resolution_intake_queue_gitignored": _git_check_ignored(SOURCE_PRIVATE_RESOLUTION_INTAKE_QUEUE_PATH),
        "source_private_resolution_intake_report_gitignored": _git_check_ignored(SOURCE_PRIVATE_RESOLUTION_INTAKE_REPORT_PATH),
        "resolution_intake_blocker_audit_checked_by_this_phase": True,
        "owner_or_authorized_agent_resolution_completed_by_this_phase": False,
        "authoritative_binding_application_ready": False,
        "authoritative_binding_applied_by_this_phase": False,
        "raw_candidate_fingerprint_bound_by_this_phase": False,
        "raw_to_processed_value_comparison_ready": False,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "full_raw_to_processed_value_comparison_complete": False,
        "processed_data_reconciliation_ready": False,
        "processed_data_reconciliation_performed_by_this_phase": False,
        "business_value_consistency_ready": False,
        "business_value_consistency_verified": False,
        "business_value_consistency_verified_by_this_phase": False,
        "lineage_full_check_ready": False,
        "lineage_full_check_performed_by_this_phase": False,
        "lineage_full_check_complete": False,
        "formal_report_allowed": False,
        "github_upload_ready": False,
        "github_upload_allowed": False,
        "github_upload_performed_by_this_phase": False,
        "github_upload_performed": False,
        "app_reinstall_ready": False,
        "app_reinstall_allowed": False,
        "app_reinstall_performed_by_this_phase": False,
        "app_reinstall_performed": False,
        "business_execution_ready": False,
        "business_execution_allowed": False,
        "business_execution_performed_by_this_phase": False,
        "business_execution_performed": False,
        "next_required_input": NEXT_REQUIRED_INPUT,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
        "raw_boundary": _raw_boundary(),
        "public_safety": _public_safety(),
    }


def _build_matrix(summary: dict[str, Any]) -> dict[str, Any]:
    checks = [
        ("source_resolution_intake_phase_loaded", summary["source_phase_id"] == source_intake.PHASE_ID),
        ("source_go_no_go_preserved", summary["source_go_no_go_decision"] == "NO_GO"),
        ("source_matrix_clean", summary["source_matrix_check_fail_count"] == 0),
        ("source_resolution_intake_blockers_complete", summary["source_resolution_intake_blocker_count"] == 48),
        ("source_resolution_intake_ready_absent", summary["source_resolution_intake_ready_count"] == 0),
        ("source_private_resolution_intake_queue_read", summary["source_private_resolution_intake_queue_item_count"] == 48),
        ("first_resolution_intake_blocker_observation_recorded", summary["resolution_intake_blocker_observation_count"] == 1),
        ("resolution_intake_blocker_threshold_not_met", summary["resolution_intake_blocker_audit_threshold_met"] is False),
        ("private_audit_queue_locked", summary["private_audit_queue_item_count"] == 48),
        (
            "diagnostic_kind_audit_counts_locked",
            summary["source_reference_or_owner_exclusion_audit_blocker_count"] == 40
            and summary["formula_or_non_numeric_mapping_audit_blocker_count"] == 8,
        ),
        ("raw_inbox_untouched", summary["raw_boundary"]["raw_inbox_mutated_by_this_phase"] is False),
        (
            "downstream_gates_closed",
            summary["github_upload_performed"] is False
            and summary["app_reinstall_performed"] is False
            and summary["business_execution_performed"] is False,
        ),
    ]
    rows = [{"check_code": code, "status": "PASS" if passed else "FAIL"} for code, passed in checks]
    pass_count = sum(1 for row in rows if row["status"] == "PASS")
    return {
        "schema_version": "kmfa.v014_owner_authorized_agent_resolution_intake_blocker_audit_after_final_check_closure_matrix.v1",
        "record_type": "v014_owner_authorized_agent_resolution_intake_blocker_audit_after_final_check_closure_matrix_public_safe",
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
        "schema_version": "kmfa.v014_owner_authorized_agent_resolution_intake_blocker_audit_after_final_check_closure_go_no_go.v1",
        "record_type": "v014_owner_authorized_agent_resolution_intake_blocker_audit_after_final_check_closure_go_no_go",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": summary["generated_at"],
        "status": STATUS,
        "decision": DECISION,
        "audit_conclusion": AUDIT_CONCLUSION,
        "source_resolution_intake_blocker_count": summary["source_resolution_intake_blocker_count"],
        "source_resolution_intake_ready_count": summary["source_resolution_intake_ready_count"],
        "goal_status_recommendation": "blocked",
        "prior_resolution_intake_blocker_observation_count": 0,
        "resolution_intake_blocker_observation_count": 1,
        "resolution_intake_blocker_audit_threshold_met": False,
        "resolution_intake_blocker_audit_ready_count": 0,
        "resolution_intake_blocker_audit_blocker_count": summary["resolution_intake_blocker_audit_blocker_count"],
        "actionable_owner_resolution_count": 0,
        "owner_or_authorized_agent_resolution_count": 0,
        "source_reference_or_owner_exclusion_audit_blocker_count": summary[
            "source_reference_or_owner_exclusion_audit_blocker_count"
        ],
        "formula_or_non_numeric_mapping_audit_blocker_count": summary[
            "formula_or_non_numeric_mapping_audit_blocker_count"
        ],
        "unresolved_difference_count": summary["unresolved_difference_count"],
        "authoritative_binding_application_ready": False,
        "raw_to_processed_value_comparison_allowed": False,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "processed_data_reconciliation_allowed": False,
        "business_value_consistency_allowed": False,
        "business_value_consistency_verified": False,
        "lineage_full_check_allowed": False,
        "github_upload_allowed": False,
        "github_upload_performed": False,
        "app_reinstall_allowed": False,
        "app_reinstall_performed": False,
        "business_execution_allowed": False,
        "business_execution_performed": False,
        "next_required_input": NEXT_REQUIRED_INPUT,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
    }


def _test_commands() -> list[str]:
    return [
        (
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 "
            "KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_"
            "owner_or_agent_resolution_intake_blocker_audit_after_final_check_closure.py "
            "--generated-at 2026-07-08T00:00:00+10:00"
        ),
        (
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 "
            "KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_"
            "owner_or_agent_resolution_intake_blocker_audit_after_final_check_closure.py --require-private-audit"
        ),
        (
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest "
            "KMFA.tests.test_v014_residual_difference_authorized_source_reference_or_exclusion_application_"
            "owner_or_agent_resolution_intake_blocker_audit_after_final_check_closure"
        ),
    ]


def _build_manifest(summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v014_owner_authorized_agent_resolution_intake_blocker_audit_after_final_check_closure_manifest.v1",
        "record_type": "v014_owner_authorized_agent_resolution_intake_blocker_audit_after_final_check_closure_manifest",
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
            "source_resolution_intake_public_summary": "public_safe_metadata_copy",
            "source_resolution_intake_public_manifest": "public_safe_metadata_copy",
            "source_resolution_intake_public_go_no_go": "public_safe_metadata_copy",
            "source_resolution_intake_public_matrix": "public_safe_metadata_copy",
            "source_private_resolution_intake_diagnostic": "ignored_private_runtime",
            "source_private_resolution_intake_queue": "ignored_private_runtime",
            "source_private_resolution_intake_report": "ignored_private_runtime",
        },
        "public_files": _phase_public_files(),
        "private_runtime_files": [
            "private:owner_or_authorized_agent_resolution_intake_blocker_audit_diagnostic",
            "private:owner_or_authorized_agent_resolution_intake_blocker_audit_queue",
            "private:owner_or_authorized_agent_resolution_intake_blocker_audit_report",
        ],
        "test_commands": _test_commands(),
        "raw_boundary": summary["raw_boundary"],
        "public_safety": summary["public_safety"],
    }


def _write_private_outputs(
    *, generated_at: str, summary: dict[str, Any], audit_queue: list[dict[str, Any]]
) -> None:
    counts = Counter(str(row.get("diagnostic_kind")) for row in audit_queue)
    _write_json(
        PRIVATE_RESOLUTION_INTAKE_BLOCKER_AUDIT_DIAGNOSTIC_PATH,
        {
            "schema_version": "kmfa.private.v014_owner_authorized_agent_resolution_intake_blocker_audit_after_final_check_closure.v1",
            "classification": "private_owner_authorized_agent_resolution_intake_blocker_audit_do_not_commit",
            "record_type": "v014_owner_authorized_agent_resolution_intake_blocker_audit_after_final_check_closure_private_diagnostic",
            "project_id": "KMFA",
            "version": VERSION,
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "generated_at": generated_at,
            "audit_queue": audit_queue,
            "summary_private": {
                "prior_resolution_intake_blocker_observation_count": 0,
                "resolution_intake_blocker_observation_count": 1,
                "resolution_intake_blocker_audit_threshold_met": False,
                "resolution_intake_blocker_audit_blocker_count": len(audit_queue),
                "resolution_intake_blocker_audit_ready_count": 0,
                "goal_status_recommendation": "blocked",
                "source_reference_or_owner_exclusion_audit_blocker_count": counts[
                    SOURCE_REFERENCE_DIAGNOSTIC_KIND
                ],
                "formula_or_non_numeric_mapping_audit_blocker_count": counts[FORMULA_MAPPING_DIAGNOSTIC_KIND],
                "authoritative_binding_application_ready_count": 0,
                "raw_to_processed_value_comparison_ready_count": 0,
            },
            "raw_boundary": summary["raw_boundary"],
        },
    )
    _write_jsonl(PRIVATE_RESOLUTION_INTAKE_BLOCKER_AUDIT_QUEUE_PATH, audit_queue)
    report_lines = [
        "# owner/授权代理 resolution intake blocker audit 私有报告",
        "",
        f"- phase_id: `{PHASE_ID}`",
        f"- resolution_intake_blocker_audit_blocker_count: `{len(audit_queue)}`",
        "- resolution_intake_blocker_observation_count: `1`",
        "- resolution_intake_blocker_audit_threshold_met: `false`",
        f"- source reference / owner exclusion audit blockers: `{counts[SOURCE_REFERENCE_DIAGNOSTIC_KIND]}`",
        f"- formula / non-numeric mapping audit blockers: `{counts[FORMULA_MAPPING_DIAGNOSTIC_KIND]}`",
        "- raw inbox touched: `false`",
        "",
        "Resolution intake blocker observation 1 recorded.",
        "",
        "No executable owner or authorized-agent resolution was detected.",
        "",
        "当前没有可执行 source reference、owner exclusion、formula mapping 或 non-numeric mapping；binding、value comparison 和业务执行继续关闭。",
        "",
    ]
    _write_text(PRIVATE_RESOLUTION_INTAKE_BLOCKER_AUDIT_REPORT_PATH, "\n".join(report_lines))


def _write_human(summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any]) -> None:
    _write_text(
        REPORT_PATH,
        f"""# V014 Owner / Authorized Agent Resolution Intake Blocker Audit After Final Check Closure

Generated at: {summary["generated_at"]}

## Scope

- Phase: `{PHASE_ID}`
- Decision: `{DECISION}`
- Status: `{STATUS}`
- Source: prior public-safe resolution-intake evidence plus ignored private resolution-intake queue.
- Raw boundary: no raw inbox read, list, stat, parse, value extraction, write, delete, move, rename, copy, normalize or mutation.

## Public-Safe Audit Result

- Source resolution-intake blocker count: `{summary["source_resolution_intake_blocker_count"]}`
- Source resolution-intake ready count: `{summary["source_resolution_intake_ready_count"]}`
- Prior blocker observation count: `{summary["prior_resolution_intake_blocker_observation_count"]}`
- Current blocker observation count: `{summary["resolution_intake_blocker_observation_count"]}`
- Blocker audit threshold met: `{summary["resolution_intake_blocker_audit_threshold_met"]}`
- Resolution-intake audit ready count: `{summary["resolution_intake_blocker_audit_ready_count"]}`
- Resolution-intake audit blocker count: `{summary["resolution_intake_blocker_audit_blocker_count"]}`
- Source reference or owner exclusion audit blockers: `{summary["source_reference_or_owner_exclusion_audit_blocker_count"]}`
- Formula or non-numeric mapping audit blockers: `{summary["formula_or_non_numeric_mapping_audit_blocker_count"]}`
- Authoritative binding ready count: `{summary["authoritative_binding_application_ready_count"]}`
- Raw-to-processed comparison ready count: `{summary["raw_to_processed_value_comparison_ready_count"]}`
- Unresolved differences: `{summary["unresolved_difference_count"]}`

## Gate

The first resolution-intake blocker observation is recorded. No executable owner/authorized-agent
resolution is available from the current intake queue, so this phase keeps authoritative binding,
raw-to-processed value comparison, reconciliation, business consistency, GitHub upload, app reinstall
and business execution closed.

Next required input: `{NEXT_REQUIRED_INPUT}`.
""",
    )
    _write_text(
        GO_NO_GO_RECORD_PATH,
        f"""# Go / No-Go Record

- Phase: `{PHASE_ID}`
- Decision: `{go_no_go["decision"]}`
- Reason: `{AUDIT_CONCLUSION}`
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

- RED: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_resolution_intake_blocker_audit_after_final_check_closure` failed before implementation because the generator module did not exist.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_resolution_intake_blocker_audit_after_final_check_closure.py --generated-at 2026-07-08T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_resolution_intake_blocker_audit_after_final_check_closure.py --require-private-audit`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_resolution_intake_blocker_audit_after_final_check_closure`
- Governance validators, CSV shape checks, diff check, raw/private marker scan, secret scan and private-runtime tracked-file scan: expected before commit.

Expected matrix result: {matrix["check_pass_count"]}/{matrix["check_count"]} PASS.
""",
    )
    _write_text(
        RISK_REGISTER_PATH,
        """# Risk Register

- Risk: first blocker observation is mistaken for authorization to bind fields or compare values.
- Control: decision remains NO_GO and all downstream gates remain false.
- Risk: private resolution-intake details leak into public evidence.
- Control: public artifacts contain aggregate counts only; detailed audit queue stays ignored.
- Risk: raw inbox is modified.
- Control: this phase consumes existing resolution-intake artifacts only and does not touch the raw inbox.
""",
    )
    _write_text(
        ROLLBACK_PATH,
        f"""# Rollback Plan

Remove artifacts for `{PHASE_ID}`, metadata copies, private audit outputs, tool, validator, focused test and governance rows. Do not touch source resolution-intake evidence or raw inbox files.
""",
    )


def _write_governance_events(generated_at: str, summary: dict[str, Any]) -> None:
    event = {
        "event_id": (
            "DEV-KMFA-20260708-V014-AUTHORIZED-SOURCE-REFERENCE-OR-EXCLUSION-APPLICATION-OWNER-OR-"
            "AGENT-RESOLUTION-INTAKE-BLOCKER-AUDIT-AFTER-FINAL-CHECK-CLOSURE"
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
        "summary": (
            "Audited first resolution-intake blocker observation after final-check closure; no executable owner or "
            "authorized-agent resolution is available, so 48 blockers remain and downstream gates stay closed."
        ),
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "files_changed": _phase_public_files(),
        "test_commands": _test_commands(),
        "test_results": ["PENDING: final validation results will be recorded before local commit."],
        "prior_resolution_intake_blocker_observation_count": 0,
        "resolution_intake_blocker_observation_count": 1,
        "resolution_intake_blocker_audit_threshold_met": False,
        "resolution_intake_blocker_audit_ready_count": summary["resolution_intake_blocker_audit_ready_count"],
        "resolution_intake_blocker_audit_blocker_count": summary["resolution_intake_blocker_audit_blocker_count"],
        "goal_status_recommendation": "blocked",
        "actionable_owner_resolution_count": 0,
        "owner_or_authorized_agent_resolution_count": 0,
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
    }
    stage_status = {
        "schema_version": "kmfa.stage_status.v1",
        "record_type": "stage_phase_status",
        "project_id": "KMFA",
        "stage_id": "VALUE-CONSISTENCY",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "status": STATUS,
        "decision": DECISION,
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "raw_data_committed": False,
        "updated_at": generated_at,
    }
    task_status = {
        "schema_version": "kmfa.v1_4_stage_phase_task_status.v1",
        "record_type": "stage_phase_task_status",
        "project_id": "KMFA",
        "stage_id": "value-consistency",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "status": STATUS,
        "decision": DECISION,
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "completed_at": generated_at,
        "acceptance_id": ACCEPTANCE_ID,
    }
    _upsert_jsonl(DEVELOPMENT_EVENTS_PATH, event, ("event_id",))
    _upsert_jsonl(STAGE_STATUS_PATH, stage_status, ("phase_id", "task_id"))
    _upsert_jsonl(TASK_STATUS_PATH, task_status, ("phase_id", "task_id"))


def generate(*, generated_at: str | None = None, write_governance_event: bool = True) -> dict[str, Any]:
    generated = _now(generated_at)
    source_summary = _read_json(SOURCE_RESOLUTION_INTAKE_SUMMARY_PATH)
    source_manifest = _read_json(SOURCE_RESOLUTION_INTAKE_MANIFEST_PATH)
    source_go_no_go = _read_json(SOURCE_RESOLUTION_INTAKE_GO_NO_GO_PATH)
    source_matrix = _read_json(SOURCE_RESOLUTION_INTAKE_MATRIX_PATH)
    intake_rows = _read_jsonl(SOURCE_PRIVATE_RESOLUTION_INTAKE_QUEUE_PATH)
    if not SOURCE_PRIVATE_RESOLUTION_INTAKE_DIAGNOSTIC_PATH.exists():
        raise FileNotFoundError(SOURCE_PRIVATE_RESOLUTION_INTAKE_DIAGNOSTIC_PATH)
    if not SOURCE_PRIVATE_RESOLUTION_INTAKE_REPORT_PATH.exists():
        raise FileNotFoundError(SOURCE_PRIVATE_RESOLUTION_INTAKE_REPORT_PATH)
    _validate_sources(
        source_summary=source_summary,
        source_manifest=source_manifest,
        source_go_no_go=source_go_no_go,
        source_matrix=source_matrix,
        intake_rows=intake_rows,
    )
    audit_queue = _build_audit_queue(generated_at=generated, intake_rows=intake_rows)
    summary = _build_summary(
        generated_at=generated,
        source_summary=source_summary,
        source_manifest=source_manifest,
        source_go_no_go=source_go_no_go,
        source_matrix=source_matrix,
        intake_rows=intake_rows,
        audit_queue=audit_queue,
    )
    matrix = _build_matrix(summary)
    go_no_go = _build_go_no_go(summary)
    manifest = _build_manifest(summary, matrix, go_no_go)
    _write_private_outputs(generated_at=generated, summary=summary, audit_queue=audit_queue)
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
        "private_resolution_intake_blocker_audit_queue": audit_queue,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generated-at")
    args = parser.parse_args(argv)
    result = generate(generated_at=args.generated_at)
    summary = result["summary"]
    print(
        "PASS: generated V014 owner/authorized-agent resolution-intake blocker audit after final-check closure "
        f"observations={summary['resolution_intake_blocker_observation_count']} "
        f"threshold={summary['resolution_intake_blocker_audit_threshold_met']} "
        f"blockers={summary['resolution_intake_blocker_audit_blocker_count']} "
        f"goal={summary['goal_status_recommendation']} "
        f"decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
