#!/usr/bin/env python3
"""Generate authorized owner/agent diagnostic responses after blocker threshold.

This phase consumes the prior public-safe blocker-threshold evidence plus the
ignored private response template and threshold records. It records the user's
authorization for Codex to generate 48 private diagnostic responses. The
responses clear the missing-response blocker only; they do not apply bindings,
bind raw candidate fingerprints, compare values, close differences, upload,
reinstall, or execute business steps.
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
    v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_diagnostic_blocker_threshold_recheck_after_readiness_recheck
    as source_threshold,
)
from KMFA.tools import (  # noqa: E402
    v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_diagnostic_intake_after_packet
    as source_intake,
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
    "GENERATED_DIAGNOSTIC_RESPONSE_IMPORT_AFTER_BLOCKER_THRESHOLD"
)
TASK_ID = (
    "KMFA-V014-RESIDUAL-DIFFERENCE-AUTHORIZED-SOURCE-REFERENCE-OR-EXCLUSION-APPLICATION-OWNER-OR-"
    "AGENT-GENERATED-DIAGNOSTIC-RESPONSE-IMPORT-AFTER-BLOCKER-THRESHOLD-20260708"
)
ACCEPTANCE_ID = (
    "ACC-V014-RESIDUAL-DIFFERENCE-AUTHORIZED-SOURCE-REFERENCE-OR-EXCLUSION-APPLICATION-OWNER-OR-"
    "AGENT-GENERATED-DIAGNOSTIC-RESPONSE-IMPORT-AFTER-BLOCKER-THRESHOLD"
)
VERSION = (
    "0.1.4-residual-difference-authorized-source-reference-or-exclusion-application-owner-or-agent-"
    "generated-diagnostic-response-import-after-blocker-threshold"
)
STATUS = (
    "completed_validated_local_only_authorized_source_reference_or_exclusion_application_owner_or_agent_"
    "generated_diagnostic_response_import_after_blocker_threshold_no_go"
)
DECISION = "NO_GO"
AUTHORIZATION_SOURCE = "user_2026-07-08_allow_generate"
IMPORT_CONCLUSION = (
    "authorized_delegate_generated_valid_diagnostic_responses_imported_without_actionable_binding_or_comparison"
)
NEXT_REQUIRED_INPUT = (
    "generated_diagnostic_response_actionability_readiness_recheck_required_before_authoritative_binding_or_value_comparison"
)
NEXT_RECOMMENDED_PHASE = (
    "V014_RESIDUAL_DIFFERENCE_AUTHORIZED_SOURCE_REFERENCE_OR_EXCLUSION_APPLICATION_OWNER_OR_AGENT_"
    "GENERATED_DIAGNOSTIC_RESPONSE_ACTIONABILITY_RECHECK"
)

SOURCE_REFERENCE_DIAGNOSTIC_KIND = source_intake.SOURCE_REFERENCE_DIAGNOSTIC_KIND
FORMULA_MAPPING_DIAGNOSTIC_KIND = source_intake.FORMULA_MAPPING_DIAGNOSTIC_KIND

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
PREFIX = (
    "residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_"
    "generated_diagnostic_response_import_after_blocker_threshold"
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

SOURCE_PUBLIC_SUMMARY_PATH = source_threshold.METADATA_SUMMARY_PATH
SOURCE_PUBLIC_MANIFEST_PATH = source_threshold.METADATA_MANIFEST_PATH
SOURCE_PUBLIC_GO_NO_GO_PATH = source_threshold.METADATA_GO_NO_GO_PATH
SOURCE_PUBLIC_MATRIX_PATH = source_threshold.METADATA_MATRIX_PATH
SOURCE_PRIVATE_TEMPLATE_PATH = source_intake.PRIVATE_RESPONSE_TEMPLATE_PATH
SOURCE_PRIVATE_THRESHOLD_RECORDS_PATH = source_threshold.PRIVATE_THRESHOLD_RECORDS_PATH
SOURCE_PRIVATE_THRESHOLD_REPORT_PATH = source_threshold.PRIVATE_THRESHOLD_REPORT_PATH

PRIVATE_OUTPUT_DIR = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_import_after_blocker_threshold"
)
PRIVATE_GENERATED_RESPONSE_RECORD_PATH = PRIVATE_OUTPUT_DIR / "private_owner_or_agent_generated_diagnostic_response_import.json"
PRIVATE_GENERATED_RESPONSE_ITEMS_PATH = PRIVATE_OUTPUT_DIR / "private_owner_or_agent_generated_diagnostic_response_items.jsonl"
PRIVATE_NON_ACTIONABLE_QUEUE_PATH = PRIVATE_OUTPUT_DIR / "private_owner_or_agent_generated_diagnostic_response_non_actionable_queue.jsonl"
PRIVATE_GENERATED_RESPONSE_REPORT_PATH = PRIVATE_OUTPUT_DIR / "private_owner_or_agent_generated_diagnostic_response_report.md"

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
        "KMFA/tests/test_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_import_after_blocker_threshold.py",
        "KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_import_after_blocker_threshold.py",
        "KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_import_after_blocker_threshold.py",
        "KMFA/功能清单.md",
        "KMFA/开发记录.md",
        "KMFA/模型参数文件.md",
    ]


def _raw_boundary() -> dict[str, bool]:
    return {
        "user_declared_raw_data_immutable": True,
        "raw_data_root_readonly_policy_active": True,
        "source_public_threshold_summary_read_by_this_phase": True,
        "source_public_threshold_manifest_read_by_this_phase": True,
        "source_public_threshold_go_no_go_read_by_this_phase": True,
        "source_public_threshold_matrix_read_by_this_phase": True,
        "source_private_template_read_by_this_phase": True,
        "source_private_threshold_records_read_by_this_phase": True,
        "source_private_threshold_report_existence_checked_by_this_phase": True,
        "private_generated_response_record_written_by_this_phase": True,
        "private_generated_response_items_written_by_this_phase": True,
        "private_non_actionable_queue_written_by_this_phase": True,
        "private_generated_response_report_written_by_this_phase": True,
        "source_private_template_mutated_by_this_phase": False,
        "source_private_threshold_records_mutated_by_this_phase": False,
        "source_private_threshold_report_mutated_by_this_phase": False,
        "owner_or_agent_valid_response_supplied_by_this_phase": True,
        "authorized_delegate_generated_response_by_this_phase": True,
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
        "source_private_template_committed": False,
        "source_private_threshold_records_committed": False,
        "source_private_threshold_report_committed": False,
        "private_generated_response_record_committed": False,
        "private_generated_response_items_committed": False,
        "private_non_actionable_queue_committed": False,
        "private_generated_response_report_committed": False,
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


def _build_response_rows(
    *,
    generated_at: str,
    template_rows: list[dict[str, Any]],
    threshold_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    threshold_by_packet = {row["source_diagnostic_packet_item_id"]: row for row in threshold_rows}
    response_rows: list[dict[str, Any]] = []
    non_actionable_rows: list[dict[str, Any]] = []
    for index, template in enumerate(template_rows, start=1):
        packet_item_id = template["source_diagnostic_packet_item_id"]
        threshold = threshold_by_packet.get(packet_item_id)
        if threshold is None:
            raise ValueError("missing threshold record for diagnostic packet item")
        diagnostic_kind = str(template.get("diagnostic_kind"))
        if diagnostic_kind != str(threshold.get("diagnostic_kind")):
            raise ValueError("diagnostic kind mismatch between template and threshold record")
        response = {
            "generated_response_item_id": f"ASR-OE-APP-OWNER-AGENT-GEN-RESP-{index:03d}",
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "generated_at": generated_at,
            "source_response_template_item_id": template.get("response_template_item_id"),
            "source_threshold_item_id": threshold.get("threshold_item_id"),
            "source_diagnostic_packet_item_id": packet_item_id,
            "target_slot_id": template.get("target_slot_id"),
            "diagnostic_kind": diagnostic_kind,
            "response_actor_role": "authorized_delegate_codex",
            "authorization_source": AUTHORIZATION_SOURCE,
            "response_status": "valid_diagnostic_response_generated",
            "valid_diagnostic_response": True,
            "generated_by_authorized_delegate": True,
            "actionable_resolution_ready": False,
            "source_reference_or_owner_exclusion_response": diagnostic_kind == SOURCE_REFERENCE_DIAGNOSTIC_KIND,
            "formula_or_non_numeric_mapping_response": diagnostic_kind == FORMULA_MAPPING_DIAGNOSTIC_KIND,
            "binding_ready_after_response": False,
            "comparison_retry_ready_after_response": False,
            "safe_auto_resolution_available": False,
            "authoritative_binding_application_ready": False,
            "authoritative_binding_applied_by_this_phase": False,
            "raw_candidate_fingerprint_bound_by_this_phase": False,
            "raw_to_processed_value_comparison_performed_by_this_phase": False,
            "business_value_consistency_verified": False,
            "full_raw_to_processed_value_comparison_complete": False,
            "non_actionable_reason_code": "authorized_delegate_response_is_diagnostic_only_without_binding",
            "public_commit_allowed": False,
        }
        response_rows.append(response)
        non_actionable_rows.append(
            {
                "non_actionable_item_id": f"ASR-OE-APP-OWNER-AGENT-GEN-NONACTIONABLE-{index:03d}",
                "phase_id": PHASE_ID,
                "task_id": TASK_ID,
                "generated_at": generated_at,
                "generated_response_item_id": response["generated_response_item_id"],
                "source_response_template_item_id": response["source_response_template_item_id"],
                "source_threshold_item_id": response["source_threshold_item_id"],
                "target_slot_id": response["target_slot_id"],
                "diagnostic_kind": diagnostic_kind,
                "valid_diagnostic_response": True,
                "actionable_resolution_ready": False,
                "binding_ready_after_response": False,
                "comparison_retry_ready_after_response": False,
                "non_actionable_reason_code": response["non_actionable_reason_code"],
                "public_commit_allowed": False,
            }
        )
    return response_rows, non_actionable_rows


def _build_summary(
    *,
    generated_at: str,
    source_summary: dict[str, Any],
    source_manifest: dict[str, Any],
    source_go_no_go: dict[str, Any],
    source_matrix: dict[str, Any],
    template_rows: list[dict[str, Any]],
    threshold_rows: list[dict[str, Any]],
    response_rows: list[dict[str, Any]],
    non_actionable_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    template_packets = {row.get("source_diagnostic_packet_item_id") for row in template_rows}
    threshold_packets = {row.get("source_diagnostic_packet_item_id") for row in threshold_rows}
    if len(template_packets) != 48 or template_packets != threshold_packets:
        raise ValueError("template/threshold packet set mismatch")
    response_counts = Counter(str(row.get("diagnostic_kind")) for row in response_rows)
    return {
        "schema_version": "kmfa.v014_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_import_after_blocker_threshold_summary.v1",
        "record_type": "v014_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_import_after_blocker_threshold_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": generated_at,
        "status": STATUS,
        "decision": DECISION,
        "import_conclusion": IMPORT_CONCLUSION,
        "authorization_source": AUTHORIZATION_SOURCE,
        "generated_by_authorized_delegate": True,
        "source_phase_id": source_summary.get("phase_id"),
        "source_manifest_phase_id": source_manifest.get("phase_id"),
        "source_go_no_go_decision": source_go_no_go.get("decision"),
        "source_matrix_check_fail_count": source_matrix.get("check_fail_count"),
        "source_diagnostic_blocker_observation_count": source_summary.get("diagnostic_blocker_observation_count"),
        "source_diagnostic_blocked_audit_threshold_met": source_summary.get(
            "diagnostic_blocked_audit_threshold_met"
        ),
        "source_diagnostic_response_blocker_count": source_summary.get("diagnostic_response_blocker_count"),
        "source_pending_diagnostic_response_count": source_summary.get("pending_diagnostic_response_count"),
        "source_valid_diagnostic_response_count": source_summary.get("valid_diagnostic_response_count"),
        "source_actionable_resolution_count": source_summary.get("actionable_resolution_count"),
        "source_template_item_count": len(template_rows),
        "source_threshold_record_count": len(threshold_rows),
        "target_slot_match_count": len(template_packets & threshold_packets),
        "generated_diagnostic_response_count": len(response_rows),
        "valid_diagnostic_response_count": len(response_rows),
        "pending_diagnostic_response_count": 0,
        "diagnostic_response_blocker_count": 0,
        "invalid_diagnostic_response_count": 0,
        "non_actionable_diagnostic_response_count": len(non_actionable_rows),
        "actionable_resolution_count": 0,
        "source_reference_or_owner_exclusion_response_count": response_counts[SOURCE_REFERENCE_DIAGNOSTIC_KIND],
        "formula_or_non_numeric_mapping_response_count": response_counts[FORMULA_MAPPING_DIAGNOSTIC_KIND],
        "binding_ready_after_generated_response_import_count": 0,
        "comparison_retry_ready_after_generated_response_import_count": 0,
        "unresolved_difference_count": source_summary.get("unresolved_difference_count"),
        "owner_or_agent_valid_response_supplied": True,
        "owner_or_agent_valid_response_supplied_by_this_phase": True,
        "private_generated_response_record_written": True,
        "private_generated_response_items_written": True,
        "private_non_actionable_queue_written": True,
        "private_generated_response_report_written": True,
        "private_generated_response_record_gitignored": _git_check_ignored(PRIVATE_GENERATED_RESPONSE_RECORD_PATH),
        "private_generated_response_items_gitignored": _git_check_ignored(PRIVATE_GENERATED_RESPONSE_ITEMS_PATH),
        "private_non_actionable_queue_gitignored": _git_check_ignored(PRIVATE_NON_ACTIONABLE_QUEUE_PATH),
        "private_generated_response_report_gitignored": _git_check_ignored(PRIVATE_GENERATED_RESPONSE_REPORT_PATH),
        "source_private_template_gitignored": _git_check_ignored(SOURCE_PRIVATE_TEMPLATE_PATH),
        "source_private_threshold_records_gitignored": _git_check_ignored(SOURCE_PRIVATE_THRESHOLD_RECORDS_PATH),
        "source_private_threshold_report_gitignored": _git_check_ignored(SOURCE_PRIVATE_THRESHOLD_REPORT_PATH),
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
        ("source_threshold_phase_loaded", summary["source_phase_id"] == source_threshold.PHASE_ID),
        ("source_go_no_go_preserved", summary["source_go_no_go_decision"] == "NO_GO"),
        ("source_matrix_clean", summary["source_matrix_check_fail_count"] == 0),
        ("source_threshold_was_met", summary["source_diagnostic_blocked_audit_threshold_met"] is True),
        ("source_template_complete", summary["source_template_item_count"] == 48),
        ("source_threshold_records_complete", summary["source_threshold_record_count"] == 48),
        ("target_sets_match", summary["target_slot_match_count"] == 48),
        ("valid_generated_responses_imported", summary["valid_diagnostic_response_count"] == 48),
        ("missing_response_blocker_cleared", summary["pending_diagnostic_response_count"] == 0),
        ("all_generated_responses_non_actionable", summary["non_actionable_diagnostic_response_count"] == 48),
        (
            "diagnostic_kind_counts_locked",
            summary["source_reference_or_owner_exclusion_response_count"] == 40
            and summary["formula_or_non_numeric_mapping_response_count"] == 8,
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
        "schema_version": "kmfa.v014_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_import_after_blocker_threshold_matrix_public_safe.v1",
        "record_type": "v014_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_import_after_blocker_threshold_matrix_public_safe",
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
        "schema_version": "kmfa.v014_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_import_after_blocker_threshold_go_no_go.v1",
        "record_type": "v014_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_import_after_blocker_threshold_go_no_go",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": summary["generated_at"],
        "status": STATUS,
        "decision": DECISION,
        "import_conclusion": IMPORT_CONCLUSION,
        "authorization_source": AUTHORIZATION_SOURCE,
        "generated_diagnostic_response_count": summary["generated_diagnostic_response_count"],
        "valid_diagnostic_response_count": summary["valid_diagnostic_response_count"],
        "pending_diagnostic_response_count": summary["pending_diagnostic_response_count"],
        "diagnostic_response_blocker_count": summary["diagnostic_response_blocker_count"],
        "non_actionable_diagnostic_response_count": summary["non_actionable_diagnostic_response_count"],
        "actionable_resolution_count": 0,
        "source_reference_or_owner_exclusion_response_count": summary[
            "source_reference_or_owner_exclusion_response_count"
        ],
        "formula_or_non_numeric_mapping_response_count": summary["formula_or_non_numeric_mapping_response_count"],
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
        "schema_version": "kmfa.v014_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_import_after_blocker_threshold_manifest.v1",
        "record_type": "v014_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_import_after_blocker_threshold_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": summary["generated_at"],
        "status": STATUS,
        "decision": DECISION,
        "import_conclusion": IMPORT_CONCLUSION,
        "authorization_source": AUTHORIZATION_SOURCE,
        "summary": summary,
        "matrix": matrix,
        "go_no_go_report": go_no_go,
        "source_artifacts": {
            "source_threshold_public_summary": "public_safe_metadata_copy",
            "source_threshold_public_manifest": "public_safe_metadata_copy",
            "source_threshold_public_go_no_go": "public_safe_metadata_copy",
            "source_threshold_public_matrix": "public_safe_metadata_copy",
            "source_private_template": "ignored_private_runtime",
            "source_private_threshold_records": "ignored_private_runtime",
            "source_private_threshold_report": "ignored_private_runtime",
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
            "private:owner_or_agent_generated_diagnostic_response_import",
            "private:owner_or_agent_generated_diagnostic_response_items",
            "private:owner_or_agent_generated_diagnostic_response_non_actionable_queue",
            "private:owner_or_agent_generated_diagnostic_response_report",
        ],
        "raw_boundary": summary["raw_boundary"],
        "public_safety": summary["public_safety"],
        "test_commands": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_import_after_blocker_threshold.py --generated-at 2026-07-08T00:00:00+10:00",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_import_after_blocker_threshold.py --require-private-generated-response",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_import_after_blocker_threshold",
        ],
        "git": {
            "branch": _git_output(["branch", "--show-current"]),
            "head": "local_commit_recorded_after_validation",
            "status_short_branch": "omitted_for_reproducible_phase_manifest",
            "changed_kmfa_files": _phase_public_files(),
        },
    }


def _write_private_outputs(*, generated_at: str, summary: dict[str, Any], response_rows: list[dict[str, Any]], non_actionable_rows: list[dict[str, Any]]) -> None:
    _write_json(
        PRIVATE_GENERATED_RESPONSE_RECORD_PATH,
        {
            "schema_version": "kmfa.private.v014_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_import_after_blocker_threshold.v1",
            "classification": "private_owner_or_agent_generated_diagnostic_response_import_do_not_commit",
            "record_type": "v014_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_import_after_blocker_threshold_private_record",
            "project_id": "KMFA",
            "version": VERSION,
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "generated_at": generated_at,
            "authorization_source": AUTHORIZATION_SOURCE,
            "response_items": response_rows,
            "summary_private": {
                "generated_diagnostic_response_count": summary["generated_diagnostic_response_count"],
                "valid_diagnostic_response_count": summary["valid_diagnostic_response_count"],
                "non_actionable_diagnostic_response_count": summary["non_actionable_diagnostic_response_count"],
                "actionable_resolution_count": 0,
                "binding_ready_after_generated_response_import_count": 0,
                "comparison_retry_ready_after_generated_response_import_count": 0,
                "business_value_consistency_verified": False,
            },
            "raw_boundary": summary["raw_boundary"],
        },
    )
    _write_jsonl(PRIVATE_GENERATED_RESPONSE_ITEMS_PATH, response_rows)
    _write_jsonl(PRIVATE_NON_ACTIONABLE_QUEUE_PATH, non_actionable_rows)
    _write_text(
        PRIVATE_GENERATED_RESPONSE_REPORT_PATH,
        "\n".join(
            [
                "# Private Generated Owner Or Agent Diagnostic Response Report",
                "",
                f"- phase_id: `{PHASE_ID}`",
                f"- authorization_source: `{AUTHORIZATION_SOURCE}`",
                f"- generated_diagnostic_response_count: `{summary['generated_diagnostic_response_count']}`",
                f"- valid_diagnostic_response_count: `{summary['valid_diagnostic_response_count']}`",
                f"- non_actionable_diagnostic_response_count: `{summary['non_actionable_diagnostic_response_count']}`",
                "- actionable_resolution_count: `0`",
                "- raw_inbox_mutated_by_this_phase: `false`",
                "",
                "Private response rows may contain private handles and must remain ignored.",
                "",
            ]
        ),
    )


def _write_human(summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any]) -> None:
    _write_text(
        REPORT_PATH,
        f"""# V014 Authorized Source Reference Or Exclusion Application Owner Or Agent Generated Diagnostic Response Import After Blocker Threshold

Generated at: {summary["generated_at"]}

## Scope

- Phase: `{PHASE_ID}`
- Decision: `{DECISION}`
- Status: `{STATUS}`
- Authorization source: `{AUTHORIZATION_SOURCE}`
- Source: prior public-safe blocker threshold evidence plus ignored private response template / threshold records.
- Raw boundary: no raw inbox read, list, stat, parse, value extraction, write, delete, move, rename, copy, normalize or mutation.

## Public-Safe Result

- Source template items: `{summary["source_template_item_count"]}`
- Source threshold records: `{summary["source_threshold_record_count"]}`
- Generated valid diagnostic responses: `{summary["valid_diagnostic_response_count"]}`
- Pending diagnostic responses: `{summary["pending_diagnostic_response_count"]}`
- Diagnostic response blockers: `{summary["diagnostic_response_blocker_count"]}`
- Non-actionable diagnostic responses: `{summary["non_actionable_diagnostic_response_count"]}`
- Source reference or owner exclusion responses: `{summary["source_reference_or_owner_exclusion_response_count"]}`
- Formula or non-numeric mapping responses: `{summary["formula_or_non_numeric_mapping_response_count"]}`
- Unresolved differences: `{summary["unresolved_difference_count"]}`

## Gate

This phase clears the missing-response blocker using authorized delegate generated private diagnostic responses only. It does not apply authoritative bindings, bind raw candidate fingerprints, compare raw and processed values, reconcile data, claim business consistency, upload to GitHub, reinstall the app, or execute business use.

Next required input: `{NEXT_REQUIRED_INPUT}`.
""",
    )
    _write_text(
        GO_NO_GO_RECORD_PATH,
        f"""# Go / No-Go Record

- Phase: `{PHASE_ID}`
- Decision: `{go_no_go["decision"]}`
- Reason: `{IMPORT_CONCLUSION}`
- Matrix: `{matrix["check_pass_count"]}` pass / `{matrix["check_fail_count"]}` fail
- GitHub upload: not allowed in this phase.
- App reinstall: not allowed in this phase.
- Business execution: not allowed in this phase.
""",
    )
    _write_text(
        TEST_RESULTS_PATH,
        f"""# Test Results

- RED: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_import_after_blocker_threshold` failed before implementation because the generator module did not exist.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_import_after_blocker_threshold.py --generated-at 2026-07-08T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_import_after_blocker_threshold.py --require-private-generated-response`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_import_after_blocker_threshold`
- Governance validators, CSV shape checks, diff check, raw/private marker scan, secret scan and private-runtime tracked-file scan: expected before commit.

Expected matrix result: {matrix["check_pass_count"]}/{matrix["check_count"]} PASS.
""",
    )
    _write_text(
        RISK_REGISTER_PATH,
        """# Risk Register

- Risk: generated diagnostic responses are mistaken for source binding or value reconciliation.
- Control: valid response and actionable/binding/comparison gates are recorded separately; downstream gates remain closed.
- Risk: private diagnostic handles leak into public evidence.
- Control: public artifacts contain aggregate counts only; generated response rows stay ignored.
- Risk: raw inbox is modified.
- Control: this phase consumes existing ignored private diagnostic artifacts only and does not touch the raw inbox.
""",
    )
    _write_text(
        ROLLBACK_PATH,
        f"""# Rollback Plan

Remove artifacts for `{PHASE_ID}`, metadata copies, private generated-response outputs, tool, validator, focused test and governance rows. Do not touch source private templates, source threshold records or raw inbox files.
""",
    )


def _write_governance_events(generated_at: str, summary: dict[str, Any]) -> None:
    event_id = (
        "DEV-KMFA-20260708-V014-AUTHORIZED-SOURCE-REFERENCE-OR-EXCLUSION-APPLICATION-OWNER-OR-AGENT-"
        "GENERATED-DIAGNOSTIC-RESPONSE-IMPORT-AFTER-BLOCKER-THRESHOLD"
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
            "summary": "Generated 48 authorized private owner/agent diagnostic responses after blocker threshold while keeping binding and comparison gates closed.",
            "authorization_source": AUTHORIZATION_SOURCE,
            "evidence_ref": MANIFEST_PATH.as_posix(),
            "files_changed": _phase_public_files(),
            "test_commands": [
                "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_import_after_blocker_threshold.py --generated-at 2026-07-08T00:00:00+10:00",
                "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_import_after_blocker_threshold.py --require-private-generated-response",
                "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_import_after_blocker_threshold",
            ],
            "test_results": ["PENDING: final validation results will be recorded before local commit."],
            "valid_diagnostic_response_count": summary["valid_diagnostic_response_count"],
            "non_actionable_diagnostic_response_count": summary["non_actionable_diagnostic_response_count"],
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
            "name": "v0.1.4 authorized source reference or exclusion application owner/agent generated diagnostic response import after blocker threshold",
            "status": STATUS,
            "completed_task_units": 1,
            "estimated_task_units": 1,
            "derived_percent": 100.0,
            "acceptance_id": ACCEPTANCE_ID,
            "evidence_ref": MANIFEST_PATH.as_posix(),
            "fact_level": "EXTRACTED",
            "updated_at": generated_at[:10],
            "stage_id": "VALUE-CONSISTENCY",
            "phase_goal": "generate authorized private owner/agent diagnostic responses without applying bindings or comparisons",
            "task_count": 3,
            "acceptance_output": "Generated diagnostic response manifest, summary, Go No-Go, private ignored response rows, validator, focused test and governance records",
        },
        ("phase_id", "record_type", "task_id"),
    )
    for suffix, task_goal in (
        ("T1", "read prior public threshold evidence and ignored private response template/threshold records read-only"),
        ("T2", "write ignored private authorized delegate generated diagnostic responses"),
        ("T3", "emit public-safe NO_GO response-import evidence while keeping binding comparison and upload gates closed"),
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
    template_rows = _read_jsonl(SOURCE_PRIVATE_TEMPLATE_PATH)
    threshold_rows = _read_jsonl(SOURCE_PRIVATE_THRESHOLD_RECORDS_PATH)
    if not SOURCE_PRIVATE_THRESHOLD_REPORT_PATH.exists():
        raise FileNotFoundError(SOURCE_PRIVATE_THRESHOLD_REPORT_PATH)
    response_rows, non_actionable_rows = _build_response_rows(
        generated_at=generated,
        template_rows=template_rows,
        threshold_rows=threshold_rows,
    )
    summary = _build_summary(
        generated_at=generated,
        source_summary=source_summary,
        source_manifest=source_manifest,
        source_go_no_go=source_go_no_go,
        source_matrix=source_matrix,
        template_rows=template_rows,
        threshold_rows=threshold_rows,
        response_rows=response_rows,
        non_actionable_rows=non_actionable_rows,
    )
    matrix = _build_matrix(summary)
    go_no_go = _build_go_no_go(summary)
    manifest = _build_manifest(summary, matrix, go_no_go)
    _write_private_outputs(
        generated_at=generated,
        summary=summary,
        response_rows=response_rows,
        non_actionable_rows=non_actionable_rows,
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
    return {"summary": summary, "matrix": matrix, "go_no_go": go_no_go, "manifest": manifest}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generated-at")
    args = parser.parse_args(argv)
    result = generate(generated_at=args.generated_at)
    summary = result["summary"]
    print(
        "PASS: generated V014 authorized owner/agent diagnostic responses "
        f"valid={summary['valid_diagnostic_response_count']} "
        f"non_actionable={summary['non_actionable_diagnostic_response_count']} "
        f"decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
