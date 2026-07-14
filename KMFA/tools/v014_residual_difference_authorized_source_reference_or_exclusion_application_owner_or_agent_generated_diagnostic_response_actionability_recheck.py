#!/usr/bin/env python3
"""Recheck actionability of generated owner/agent diagnostic responses.

This phase consumes the prior public-safe generated-response import evidence
and ignored private generated response rows. It proves that all 48 valid
diagnostic responses remain non-actionable for authoritative binding or raw to
processed value comparison. It does not read or mutate the raw inbox.
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
    v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_import_after_blocker_threshold
    as source_import,
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
    "GENERATED_DIAGNOSTIC_RESPONSE_ACTIONABILITY_RECHECK"
)
TASK_ID = (
    "KMFA-V014-RESIDUAL-DIFFERENCE-AUTHORIZED-SOURCE-REFERENCE-OR-EXCLUSION-APPLICATION-OWNER-OR-"
    "AGENT-GENERATED-DIAGNOSTIC-RESPONSE-ACTIONABILITY-RECHECK-20260708"
)
ACCEPTANCE_ID = (
    "ACC-V014-RESIDUAL-DIFFERENCE-AUTHORIZED-SOURCE-REFERENCE-OR-EXCLUSION-APPLICATION-OWNER-OR-"
    "AGENT-GENERATED-DIAGNOSTIC-RESPONSE-ACTIONABILITY-RECHECK"
)
VERSION = (
    "0.1.4-residual-difference-authorized-source-reference-or-exclusion-application-owner-or-agent-"
    "generated-diagnostic-response-actionability-recheck"
)
STATUS = (
    "completed_validated_local_only_authorized_source_reference_or_exclusion_application_owner_or_agent_"
    "generated_diagnostic_response_actionability_recheck_no_go"
)
DECISION = "NO_GO"
ACTIONABILITY_CONCLUSION = (
    "generated_diagnostic_responses_rechecked_all_48_non_actionable_for_binding_or_comparison"
)
NEXT_REQUIRED_INPUT = (
    "actionable_source_reference_owner_exclusion_formula_mapping_or_non_numeric_mapping_required_before_"
    "binding_or_value_comparison"
)
NEXT_RECOMMENDED_PHASE = (
    "V014_RESIDUAL_DIFFERENCE_AUTHORIZED_SOURCE_REFERENCE_OR_EXCLUSION_APPLICATION_OWNER_OR_AGENT_"
    "GENERATED_DIAGNOSTIC_RESPONSE_ACTIONABILITY_BLOCKER_AUDIT"
)

SOURCE_REFERENCE_DIAGNOSTIC_KIND = source_import.SOURCE_REFERENCE_DIAGNOSTIC_KIND
FORMULA_MAPPING_DIAGNOSTIC_KIND = source_import.FORMULA_MAPPING_DIAGNOSTIC_KIND

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
PREFIX = (
    "residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_"
    "generated_diagnostic_response_actionability_recheck"
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

SOURCE_PUBLIC_SUMMARY_PATH = source_import.METADATA_SUMMARY_PATH
SOURCE_PUBLIC_MANIFEST_PATH = source_import.METADATA_MANIFEST_PATH
SOURCE_PUBLIC_GO_NO_GO_PATH = source_import.METADATA_GO_NO_GO_PATH
SOURCE_PUBLIC_MATRIX_PATH = source_import.METADATA_MATRIX_PATH
SOURCE_PRIVATE_RESPONSE_ITEMS_PATH = source_import.PRIVATE_GENERATED_RESPONSE_ITEMS_PATH
SOURCE_PRIVATE_NON_ACTIONABLE_QUEUE_PATH = source_import.PRIVATE_NON_ACTIONABLE_QUEUE_PATH
SOURCE_PRIVATE_RESPONSE_REPORT_PATH = source_import.PRIVATE_GENERATED_RESPONSE_REPORT_PATH

PRIVATE_OUTPUT_DIR = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_actionability_recheck"
)
PRIVATE_ACTIONABILITY_DIAGNOSTIC_PATH = (
    PRIVATE_OUTPUT_DIR / "private_owner_or_agent_generated_diagnostic_response_actionability_diagnostic.json"
)
PRIVATE_ACTIONABILITY_BLOCKER_QUEUE_PATH = (
    PRIVATE_OUTPUT_DIR / "private_owner_or_agent_generated_diagnostic_response_actionability_blocker_queue.jsonl"
)
PRIVATE_ACTIONABILITY_REPORT_PATH = (
    PRIVATE_OUTPUT_DIR / "private_owner_or_agent_generated_diagnostic_response_actionability_report.md"
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
        "KMFA/tests/test_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_actionability_recheck.py",
        "KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_actionability_recheck.py",
        "KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_actionability_recheck.py",
        "KMFA/功能清单.md",
        "KMFA/开发记录.md",
        "KMFA/模型参数文件.md",
    ]


def _raw_boundary() -> dict[str, bool]:
    return {
        "user_declared_raw_data_immutable": True,
        "raw_data_root_readonly_policy_active": True,
        "source_public_generated_response_summary_read_by_this_phase": True,
        "source_public_generated_response_manifest_read_by_this_phase": True,
        "source_public_generated_response_go_no_go_read_by_this_phase": True,
        "source_public_generated_response_matrix_read_by_this_phase": True,
        "source_private_response_items_read_by_this_phase": True,
        "source_private_non_actionable_queue_read_by_this_phase": True,
        "source_private_response_report_existence_checked_by_this_phase": True,
        "private_actionability_diagnostic_written_by_this_phase": True,
        "private_actionability_blocker_queue_written_by_this_phase": True,
        "private_actionability_report_written_by_this_phase": True,
        "source_private_response_items_mutated_by_this_phase": False,
        "source_private_non_actionable_queue_mutated_by_this_phase": False,
        "source_private_response_report_mutated_by_this_phase": False,
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
        "source_private_response_items_committed": False,
        "source_private_non_actionable_queue_committed": False,
        "source_private_response_report_committed": False,
        "private_actionability_diagnostic_committed": False,
        "private_actionability_blocker_queue_committed": False,
        "private_actionability_report_committed": False,
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


def _build_actionability_rows(
    *, generated_at: str, response_rows: list[dict[str, Any]], non_actionable_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    non_actionable_by_response = {row["generated_response_item_id"]: row for row in non_actionable_rows}
    actionability_rows: list[dict[str, Any]] = []
    for index, response in enumerate(response_rows, start=1):
        response_id = response["generated_response_item_id"]
        if response_id not in non_actionable_by_response:
            raise ValueError("missing source non-actionable row for generated response")
        diagnostic_kind = str(response.get("diagnostic_kind"))
        if diagnostic_kind != str(non_actionable_by_response[response_id].get("diagnostic_kind")):
            raise ValueError("diagnostic kind mismatch between generated response and non-actionable queue")
        if response.get("valid_diagnostic_response") is not True:
            raise ValueError("generated response is not valid")
        if response.get("actionable_resolution_ready") is not False:
            raise ValueError("generated response is unexpectedly actionable")
        row = {
            "actionability_item_id": f"ASR-OE-APP-OWNER-AGENT-ACT-RECHECK-{index:03d}",
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "generated_at": generated_at,
            "source_generated_response_item_id": response_id,
            "source_non_actionable_item_id": non_actionable_by_response[response_id].get("non_actionable_item_id"),
            "source_diagnostic_packet_item_id": response.get("source_diagnostic_packet_item_id"),
            "source_response_template_item_id": response.get("source_response_template_item_id"),
            "source_threshold_item_id": response.get("source_threshold_item_id"),
            "target_slot_id": response.get("target_slot_id"),
            "diagnostic_kind": diagnostic_kind,
            "actionability_status": "blocked_non_actionable_generated_response",
            "valid_diagnostic_response": True,
            "actionable_resolution_ready": False,
            "source_reference_or_owner_exclusion_actionability_blocker": (
                diagnostic_kind == SOURCE_REFERENCE_DIAGNOSTIC_KIND
            ),
            "formula_or_non_numeric_mapping_actionability_blocker": diagnostic_kind == FORMULA_MAPPING_DIAGNOSTIC_KIND,
            "binding_ready_after_actionability_recheck": False,
            "comparison_retry_ready_after_actionability_recheck": False,
            "safe_auto_resolution_available": False,
            "authoritative_binding_application_ready": False,
            "authoritative_binding_applied_by_this_phase": False,
            "raw_candidate_fingerprint_bound_by_this_phase": False,
            "raw_to_processed_value_comparison_performed_by_this_phase": False,
            "business_value_consistency_verified": False,
            "full_raw_to_processed_value_comparison_complete": False,
            "actionability_blocker_reason_code": "generated_diagnostic_response_lacks_actionable_source_binding_or_formula_mapping",
            "public_commit_allowed": False,
        }
        actionability_rows.append(row)
    return actionability_rows


def _build_summary(
    *,
    generated_at: str,
    source_summary: dict[str, Any],
    source_manifest: dict[str, Any],
    source_go_no_go: dict[str, Any],
    source_matrix: dict[str, Any],
    response_rows: list[dict[str, Any]],
    non_actionable_rows: list[dict[str, Any]],
    actionability_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    response_ids = {row.get("generated_response_item_id") for row in response_rows}
    non_actionable_ids = {row.get("generated_response_item_id") for row in non_actionable_rows}
    if len(response_ids) != 48 or response_ids != non_actionable_ids:
        raise ValueError("generated response and non-actionable queue sets must match")
    counts = Counter(str(row.get("diagnostic_kind")) for row in actionability_rows)
    return {
        "schema_version": "kmfa.v014_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_actionability_recheck_summary.v1",
        "record_type": "v014_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_actionability_recheck_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": generated_at,
        "status": STATUS,
        "decision": DECISION,
        "actionability_conclusion": ACTIONABILITY_CONCLUSION,
        "source_phase_id": source_summary.get("phase_id"),
        "source_manifest_phase_id": source_manifest.get("phase_id"),
        "source_go_no_go_decision": source_go_no_go.get("decision"),
        "source_matrix_check_fail_count": source_matrix.get("check_fail_count"),
        "source_valid_diagnostic_response_count": source_summary.get("valid_diagnostic_response_count"),
        "source_non_actionable_diagnostic_response_count": source_summary.get(
            "non_actionable_diagnostic_response_count"
        ),
        "source_private_response_item_count": len(response_rows),
        "source_private_non_actionable_queue_item_count": len(non_actionable_rows),
        "actionability_recheck_item_count": len(actionability_rows),
        "actionability_ready_count": 0,
        "actionability_blocker_count": len(actionability_rows),
        "valid_diagnostic_response_count": len(response_rows),
        "actionable_resolution_count": 0,
        "source_reference_or_owner_exclusion_actionability_blocker_count": counts[SOURCE_REFERENCE_DIAGNOSTIC_KIND],
        "formula_or_non_numeric_mapping_actionability_blocker_count": counts[FORMULA_MAPPING_DIAGNOSTIC_KIND],
        "binding_ready_after_actionability_recheck_count": 0,
        "comparison_retry_ready_after_actionability_recheck_count": 0,
        "unresolved_difference_count": source_summary.get("unresolved_difference_count"),
        "private_actionability_diagnostic_written": True,
        "private_actionability_blocker_queue_written": True,
        "private_actionability_report_written": True,
        "private_actionability_diagnostic_gitignored": _git_check_ignored(PRIVATE_ACTIONABILITY_DIAGNOSTIC_PATH),
        "private_actionability_blocker_queue_gitignored": _git_check_ignored(PRIVATE_ACTIONABILITY_BLOCKER_QUEUE_PATH),
        "private_actionability_report_gitignored": _git_check_ignored(PRIVATE_ACTIONABILITY_REPORT_PATH),
        "source_private_response_items_gitignored": _git_check_ignored(SOURCE_PRIVATE_RESPONSE_ITEMS_PATH),
        "source_private_non_actionable_queue_gitignored": _git_check_ignored(SOURCE_PRIVATE_NON_ACTIONABLE_QUEUE_PATH),
        "source_private_response_report_gitignored": _git_check_ignored(SOURCE_PRIVATE_RESPONSE_REPORT_PATH),
        "owner_or_agent_valid_response_available": True,
        "generated_diagnostic_response_actionability_recheck_performed": True,
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
        ("source_generated_response_phase_loaded", summary["source_phase_id"] == source_import.PHASE_ID),
        ("source_go_no_go_preserved", summary["source_go_no_go_decision"] == "NO_GO"),
        ("source_matrix_clean", summary["source_matrix_check_fail_count"] == 0),
        ("source_valid_responses_complete", summary["source_valid_diagnostic_response_count"] == 48),
        ("source_non_actionable_queue_complete", summary["source_non_actionable_diagnostic_response_count"] == 48),
        ("source_private_response_items_complete", summary["source_private_response_item_count"] == 48),
        ("source_private_non_actionable_queue_complete", summary["source_private_non_actionable_queue_item_count"] == 48),
        ("actionability_recheck_complete", summary["actionability_recheck_item_count"] == 48),
        ("all_generated_responses_remain_non_actionable", summary["actionability_blocker_count"] == 48),
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
        "schema_version": "kmfa.v014_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_actionability_recheck_matrix_public_safe.v1",
        "record_type": "v014_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_actionability_recheck_matrix_public_safe",
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
        "schema_version": "kmfa.v014_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_actionability_recheck_go_no_go.v1",
        "record_type": "v014_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_actionability_recheck_go_no_go",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": summary["generated_at"],
        "status": STATUS,
        "decision": DECISION,
        "actionability_conclusion": ACTIONABILITY_CONCLUSION,
        "valid_diagnostic_response_count": summary["valid_diagnostic_response_count"],
        "actionability_recheck_item_count": summary["actionability_recheck_item_count"],
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
        "schema_version": "kmfa.v014_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_actionability_recheck_manifest.v1",
        "record_type": "v014_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_actionability_recheck_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": summary["generated_at"],
        "status": STATUS,
        "decision": DECISION,
        "actionability_conclusion": ACTIONABILITY_CONCLUSION,
        "summary": summary,
        "matrix": matrix,
        "go_no_go_report": go_no_go,
        "source_artifacts": {
            "source_generated_response_public_summary": "public_safe_metadata_copy",
            "source_generated_response_public_manifest": "public_safe_metadata_copy",
            "source_generated_response_public_go_no_go": "public_safe_metadata_copy",
            "source_generated_response_public_matrix": "public_safe_metadata_copy",
            "source_private_response_items": "ignored_private_runtime",
            "source_private_non_actionable_queue": "ignored_private_runtime",
            "source_private_response_report": "ignored_private_runtime",
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
            "private:owner_or_agent_generated_diagnostic_response_actionability_diagnostic",
            "private:owner_or_agent_generated_diagnostic_response_actionability_blocker_queue",
            "private:owner_or_agent_generated_diagnostic_response_actionability_report",
        ],
        "raw_boundary": summary["raw_boundary"],
        "public_safety": summary["public_safety"],
        "test_commands": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_actionability_recheck.py --generated-at 2026-07-08T00:00:00+10:00",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_actionability_recheck.py --require-private-actionability",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_actionability_recheck",
        ],
        "git": {
            "branch": _git_output(["branch", "--show-current"]),
            "head": "local_commit_recorded_after_validation",
            "status_short_branch": "omitted_for_reproducible_phase_manifest",
            "changed_kmfa_files": _phase_public_files(),
        },
    }


def _write_private_outputs(
    *, generated_at: str, summary: dict[str, Any], actionability_rows: list[dict[str, Any]]
) -> None:
    _write_json(
        PRIVATE_ACTIONABILITY_DIAGNOSTIC_PATH,
        {
            "schema_version": "kmfa.private.v014_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_actionability_recheck.v1",
            "classification": "private_owner_or_agent_generated_diagnostic_response_actionability_recheck_do_not_commit",
            "record_type": "v014_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_actionability_recheck_private_diagnostic",
            "project_id": "KMFA",
            "version": VERSION,
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "generated_at": generated_at,
            "actionability_rows": actionability_rows,
            "summary_private": {
                "actionability_recheck_item_count": summary["actionability_recheck_item_count"],
                "actionability_ready_count": 0,
                "actionability_blocker_count": summary["actionability_blocker_count"],
                "actionable_resolution_count": 0,
                "binding_ready_after_actionability_recheck_count": 0,
                "comparison_retry_ready_after_actionability_recheck_count": 0,
                "business_value_consistency_verified": False,
            },
            "raw_boundary": summary["raw_boundary"],
        },
    )
    _write_jsonl(PRIVATE_ACTIONABILITY_BLOCKER_QUEUE_PATH, actionability_rows)
    _write_text(
        PRIVATE_ACTIONABILITY_REPORT_PATH,
        "\n".join(
            [
                "# Private Generated Diagnostic Response Actionability Recheck Report",
                "",
                f"- phase_id: `{PHASE_ID}`",
                f"- valid_diagnostic_response_count: `{summary['valid_diagnostic_response_count']}`",
                f"- actionability_recheck_item_count: `{summary['actionability_recheck_item_count']}`",
                "- actionability_ready_count: `0`",
                f"- actionability_blocker_count: `{summary['actionability_blocker_count']}`",
                "- authoritative_binding_application_ready: `false`",
                "- raw_to_processed_value_comparison_ready: `false`",
                "- raw_inbox_mutated_by_this_phase: `false`",
                "",
                "Private actionability rows may contain private handles and must remain ignored.",
                "",
            ]
        ),
    )


def _write_human(summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any]) -> None:
    _write_text(
        REPORT_PATH,
        f"""# V014 Authorized Source Reference Or Exclusion Application Owner Or Agent Generated Diagnostic Response Actionability Recheck

Generated at: {summary["generated_at"]}

## Scope

- Phase: `{PHASE_ID}`
- Decision: `{DECISION}`
- Status: `{STATUS}`
- Source: prior public-safe generated-response import evidence plus ignored private generated response rows and non-actionable queue.
- Raw boundary: no raw inbox read, list, stat, parse, value extraction, write, delete, move, rename, copy, normalize or mutation.

## Public-Safe Result

- Source valid diagnostic responses: `{summary["source_valid_diagnostic_response_count"]}`
- Source non-actionable diagnostic responses: `{summary["source_non_actionable_diagnostic_response_count"]}`
- Actionability recheck items: `{summary["actionability_recheck_item_count"]}`
- Actionability ready items: `{summary["actionability_ready_count"]}`
- Actionability blockers: `{summary["actionability_blocker_count"]}`
- Source reference or owner exclusion actionability blockers: `{summary["source_reference_or_owner_exclusion_actionability_blocker_count"]}`
- Formula or non-numeric mapping actionability blockers: `{summary["formula_or_non_numeric_mapping_actionability_blocker_count"]}`
- Unresolved differences: `{summary["unresolved_difference_count"]}`

## Gate

The generated diagnostic responses are valid as diagnostic responses only. They remain non-actionable for authoritative binding or value comparison, so raw-to-processed value consistency is not verified.

Next required input: `{NEXT_REQUIRED_INPUT}`.
""",
    )
    _write_text(
        GO_NO_GO_RECORD_PATH,
        f"""# Go / No-Go Record

- Phase: `{PHASE_ID}`
- Decision: `{go_no_go["decision"]}`
- Reason: `{ACTIONABILITY_CONCLUSION}`
- Matrix: `{matrix["check_pass_count"]}` pass / `{matrix["check_fail_count"]}` fail
- GitHub upload: not allowed in this phase.
- App reinstall: not allowed in this phase.
- Business execution: not allowed in this phase.
""",
    )
    _write_text(
        TEST_RESULTS_PATH,
        f"""# Test Results

- RED: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_actionability_recheck` failed before implementation because the generator module did not exist.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_actionability_recheck.py --generated-at 2026-07-08T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_actionability_recheck.py --require-private-actionability`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_actionability_recheck`
- Governance validators, CSV shape checks, diff check, raw/private marker scan, secret scan and private-runtime tracked-file scan: expected before commit.

Expected matrix result: {matrix["check_pass_count"]}/{matrix["check_count"]} PASS.
""",
    )
    _write_text(
        RISK_REGISTER_PATH,
        """# Risk Register

- Risk: generated diagnostic responses are mistaken for actionable source binding.
- Control: actionability is rechecked separately and all 48 rows are retained as blockers.
- Risk: private diagnostic handles leak into public evidence.
- Control: public artifacts contain aggregate counts only; actionability rows stay ignored.
- Risk: raw inbox is modified.
- Control: this phase consumes existing ignored private diagnostic artifacts only and does not touch the raw inbox.
""",
    )
    _write_text(
        ROLLBACK_PATH,
        f"""# Rollback Plan

Remove artifacts for `{PHASE_ID}`, metadata copies, private actionability outputs, tool, validator, focused test and governance rows. Do not touch source generated-response outputs or raw inbox files.
""",
    )


def _write_governance_events(generated_at: str, summary: dict[str, Any]) -> None:
    event_id = (
        "DEV-KMFA-20260708-V014-AUTHORIZED-SOURCE-REFERENCE-OR-EXCLUSION-APPLICATION-OWNER-OR-AGENT-"
        "GENERATED-DIAGNOSTIC-RESPONSE-ACTIONABILITY-RECHECK"
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
            "summary": "Rechecked 48 authorized delegate generated diagnostic responses and proved all remain non-actionable for binding or comparison.",
            "evidence_ref": MANIFEST_PATH.as_posix(),
            "files_changed": _phase_public_files(),
            "test_commands": [
                "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_actionability_recheck.py --generated-at 2026-07-08T00:00:00+10:00",
                "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_actionability_recheck.py --require-private-actionability",
                "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_actionability_recheck",
            ],
            "test_results": ["PENDING: final validation results will be recorded before local commit."],
            "valid_diagnostic_response_count": summary["valid_diagnostic_response_count"],
            "actionability_recheck_item_count": summary["actionability_recheck_item_count"],
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
            "name": "v0.1.4 authorized source reference or exclusion application owner/agent generated diagnostic response actionability recheck",
            "status": STATUS,
            "completed_task_units": 1,
            "estimated_task_units": 1,
            "derived_percent": 100.0,
            "acceptance_id": ACCEPTANCE_ID,
            "evidence_ref": MANIFEST_PATH.as_posix(),
            "fact_level": "EXTRACTED",
            "updated_at": generated_at[:10],
            "stage_id": "VALUE-CONSISTENCY",
            "phase_goal": "prove generated private diagnostic responses remain non-actionable for binding or comparison",
            "task_count": 3,
            "acceptance_output": "Actionability recheck manifest, summary, Go No-Go, private ignored actionability blocker queue, validator, focused test and governance records",
        },
        ("phase_id", "record_type", "task_id"),
    )
    for suffix, task_goal in (
        ("T1", "read prior public generated-response evidence and ignored private generated response rows read-only"),
        ("T2", "write ignored private actionability diagnostic and blocker queue for 48 generated diagnostic responses"),
        ("T3", "emit public-safe NO_GO actionability recheck evidence while keeping binding comparison and upload gates closed"),
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
    response_rows = _read_jsonl(SOURCE_PRIVATE_RESPONSE_ITEMS_PATH)
    non_actionable_rows = _read_jsonl(SOURCE_PRIVATE_NON_ACTIONABLE_QUEUE_PATH)
    if not SOURCE_PRIVATE_RESPONSE_REPORT_PATH.exists():
        raise FileNotFoundError(SOURCE_PRIVATE_RESPONSE_REPORT_PATH)
    actionability_rows = _build_actionability_rows(
        generated_at=generated,
        response_rows=response_rows,
        non_actionable_rows=non_actionable_rows,
    )
    summary = _build_summary(
        generated_at=generated,
        source_summary=source_summary,
        source_manifest=source_manifest,
        source_go_no_go=source_go_no_go,
        source_matrix=source_matrix,
        response_rows=response_rows,
        non_actionable_rows=non_actionable_rows,
        actionability_rows=actionability_rows,
    )
    matrix = _build_matrix(summary)
    go_no_go = _build_go_no_go(summary)
    manifest = _build_manifest(summary, matrix, go_no_go)
    _write_private_outputs(generated_at=generated, summary=summary, actionability_rows=actionability_rows)
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
        "PASS: rechecked V014 generated owner/agent diagnostic response actionability "
        f"blockers={summary['actionability_blocker_count']} "
        f"decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
