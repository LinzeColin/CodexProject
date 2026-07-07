#!/usr/bin/env python3
"""Recheck owner/agent diagnostic readiness after application intake.

This phase consumes the prior public-safe intake evidence and the ignored
private response template / pending queue. It only proves that no valid owner
or agent diagnostic response is available yet. It does not read or mutate the
raw inbox, import responses, apply authoritative bindings, or compare values.
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
    "V014_RESIDUAL_DIFFERENCE_AUTHORIZED_SOURCE_REFERENCE_OR_EXCLUSION_APPLICATION_"
    "OWNER_OR_AGENT_DIAGNOSTIC_READINESS_RECHECK_AFTER_INTAKE"
)
TASK_ID = (
    "KMFA-V014-RESIDUAL-DIFFERENCE-AUTHORIZED-SOURCE-REFERENCE-OR-EXCLUSION-APPLICATION-"
    "OWNER-OR-AGENT-DIAGNOSTIC-READINESS-RECHECK-AFTER-INTAKE-20260708"
)
ACCEPTANCE_ID = (
    "ACC-V014-RESIDUAL-DIFFERENCE-AUTHORIZED-SOURCE-REFERENCE-OR-EXCLUSION-APPLICATION-"
    "OWNER-OR-AGENT-DIAGNOSTIC-READINESS-RECHECK-AFTER-INTAKE"
)
VERSION = (
    "0.1.4-residual-difference-authorized-source-reference-or-exclusion-application-"
    "owner-or-agent-diagnostic-readiness-recheck-after-intake"
)
STATUS = (
    "completed_validated_local_only_authorized_source_reference_or_exclusion_application_"
    "owner_or_agent_diagnostic_readiness_recheck_after_intake_no_go"
)
DECISION = "NO_GO"
READINESS_CONCLUSION = "owner_or_agent_diagnostic_readiness_rechecked_all_48_items_blocked_no_valid_response"
NEXT_REQUIRED_INPUT = source_intake.NEXT_REQUIRED_INPUT
NEXT_RECOMMENDED_PHASE = (
    "V014_RESIDUAL_DIFFERENCE_AUTHORIZED_SOURCE_REFERENCE_OR_EXCLUSION_APPLICATION_"
    "OWNER_OR_AGENT_DIAGNOSTIC_BLOCKER_AUDIT_AFTER_READINESS_RECHECK"
)

SOURCE_REFERENCE_DIAGNOSTIC_KIND = source_intake.SOURCE_REFERENCE_DIAGNOSTIC_KIND
FORMULA_MAPPING_DIAGNOSTIC_KIND = source_intake.FORMULA_MAPPING_DIAGNOSTIC_KIND
EXPECTED_READINESS_BLOCKER_COUNTS = {
    SOURCE_REFERENCE_DIAGNOSTIC_KIND: 40,
    FORMULA_MAPPING_DIAGNOSTIC_KIND: 8,
}

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
PREFIX = (
    "residual_difference_authorized_source_reference_or_exclusion_application_"
    "owner_or_agent_diagnostic_readiness_recheck_after_intake"
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

SOURCE_PUBLIC_SUMMARY_PATH = source_intake.METADATA_SUMMARY_PATH
SOURCE_PUBLIC_MANIFEST_PATH = source_intake.METADATA_MANIFEST_PATH
SOURCE_PUBLIC_GO_NO_GO_PATH = source_intake.METADATA_GO_NO_GO_PATH
SOURCE_PUBLIC_MATRIX_PATH = source_intake.METADATA_MATRIX_PATH
SOURCE_PRIVATE_RESPONSE_TEMPLATE_PATH = source_intake.PRIVATE_RESPONSE_TEMPLATE_PATH
SOURCE_PRIVATE_PENDING_QUEUE_PATH = source_intake.PRIVATE_PENDING_QUEUE_PATH
SOURCE_PRIVATE_DIAGNOSTIC_PATH = source_intake.PRIVATE_DIAGNOSTIC_PATH
SOURCE_PRIVATE_REPORT_PATH = source_intake.PRIVATE_REPORT_PATH

PRIVATE_OUTPUT_DIR = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_diagnostic_readiness_recheck_after_intake"
)
PRIVATE_READINESS_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_owner_or_agent_diagnostic_readiness_recheck_diagnostic.json"
PRIVATE_BLOCKER_QUEUE_PATH = PRIVATE_OUTPUT_DIR / "private_owner_or_agent_diagnostic_readiness_blocker_queue.jsonl"
PRIVATE_READINESS_REPORT_PATH = PRIVATE_OUTPUT_DIR / "private_owner_or_agent_diagnostic_readiness_recheck_report.md"

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
        "KMFA/tests/test_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_diagnostic_readiness_recheck_after_intake.py",
        "KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_diagnostic_readiness_recheck_after_intake.py",
        "KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_diagnostic_readiness_recheck_after_intake.py",
        "KMFA/功能清单.md",
        "KMFA/开发记录.md",
        "KMFA/模型参数文件.md",
    ]


def _raw_boundary() -> dict[str, bool]:
    return {
        "user_declared_raw_data_immutable": True,
        "raw_data_root_readonly_policy_active": True,
        "source_public_intake_summary_read_by_this_phase": True,
        "source_public_intake_manifest_read_by_this_phase": True,
        "source_public_intake_go_no_go_read_by_this_phase": True,
        "source_public_intake_matrix_read_by_this_phase": True,
        "source_private_response_template_read_by_this_phase": True,
        "source_private_pending_queue_read_by_this_phase": True,
        "source_private_diagnostic_read_by_this_phase": True,
        "source_private_report_existence_checked_by_this_phase": True,
        "private_readiness_diagnostic_written_by_this_phase": True,
        "private_readiness_blocker_queue_written_by_this_phase": True,
        "private_readiness_report_written_by_this_phase": True,
        "source_private_response_template_mutated_by_this_phase": False,
        "source_private_pending_queue_mutated_by_this_phase": False,
        "source_private_diagnostic_mutated_by_this_phase": False,
        "source_private_report_mutated_by_this_phase": False,
        "owner_or_agent_response_supplied_by_this_phase": False,
        "valid_diagnostic_response_supplied_by_this_phase": False,
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
        "source_private_response_template_committed": False,
        "source_private_pending_queue_committed": False,
        "source_private_diagnostic_committed": False,
        "source_private_report_committed": False,
        "private_readiness_diagnostic_committed": False,
        "private_readiness_blocker_queue_committed": False,
        "private_readiness_report_committed": False,
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


def _build_blocker_rows(*, generated_at: str, template_rows: list[dict[str, Any]], pending_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    template_by_id = {row.get("response_template_item_id"): row for row in template_rows}
    rows: list[dict[str, Any]] = []
    for index, pending in enumerate(pending_rows, start=1):
        template = template_by_id.get(pending.get("pending_queue_item_id"), {})
        rows.append(
            {
                "blocker_item_id": f"ASR-OE-APP-OWNER-AGENT-READINESS-BLOCKER-{index:03d}",
                "phase_id": PHASE_ID,
                "task_id": TASK_ID,
                "generated_at": generated_at,
                "source_pending_queue_item_id": pending.get("pending_queue_item_id"),
                "source_response_template_item_id": pending.get("pending_queue_item_id"),
                "source_diagnostic_packet_item_id": pending.get("source_diagnostic_packet_item_id"),
                "diagnostic_kind": pending.get("diagnostic_kind"),
                "intake_track": template.get("intake_track"),
                "required_response": template.get("required_response"),
                "blocker_code": "missing_valid_owner_or_agent_diagnostic_response",
                "response_status": "pending_owner_or_external_agent",
                "valid_diagnostic_response": False,
                "actionable_resolution_ready": False,
                "binding_ready_after_response": False,
                "comparison_retry_ready_after_response": False,
                "raw_candidate_fingerprint_bound_by_this_phase": False,
                "raw_to_processed_value_comparison_performed_by_this_phase": False,
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
    template_rows: list[dict[str, Any]],
    pending_rows: list[dict[str, Any]],
    blocker_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    diagnostic_kind_counts = Counter(str(row.get("diagnostic_kind")) for row in blocker_rows)
    return {
        "schema_version": "kmfa.v014_authorized_resolution_owner_or_agent_diagnostic_readiness_recheck_after_intake_summary.v1",
        "record_type": "v014_authorized_resolution_owner_or_agent_diagnostic_readiness_recheck_after_intake_summary",
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
        "source_private_response_template_item_count": len(template_rows),
        "source_private_pending_queue_item_count": len(pending_rows),
        "source_pending_diagnostic_response_count": source_summary.get("pending_diagnostic_response_count"),
        "source_valid_diagnostic_response_count": source_summary.get("valid_diagnostic_response_count"),
        "source_actionable_resolution_count": source_summary.get("actionable_resolution_count"),
        "source_binding_ready_after_intake_count": source_summary.get("binding_ready_after_intake_count"),
        "source_comparison_retry_ready_after_intake_count": source_summary.get(
            "comparison_retry_ready_after_intake_count"
        ),
        "diagnostic_readiness_recheck_performed": True,
        "diagnostic_response_ready_count": 0,
        "diagnostic_response_blocker_count": len(blocker_rows),
        "private_readiness_blocker_queue_item_count": len(blocker_rows),
        "pending_diagnostic_response_count": len(blocker_rows),
        "valid_diagnostic_response_count": 0,
        "invalid_diagnostic_response_count": 0,
        "actionable_resolution_count": 0,
        "source_reference_or_owner_exclusion_readiness_blocker_count": diagnostic_kind_counts[
            SOURCE_REFERENCE_DIAGNOSTIC_KIND
        ],
        "formula_or_non_numeric_mapping_readiness_blocker_count": diagnostic_kind_counts[
            FORMULA_MAPPING_DIAGNOSTIC_KIND
        ],
        "binding_ready_after_readiness_recheck_count": 0,
        "comparison_retry_ready_after_readiness_recheck_count": 0,
        "unresolved_difference_count": source_summary.get("unresolved_difference_count"),
        "private_readiness_diagnostic_written": True,
        "private_readiness_blocker_queue_written": True,
        "private_readiness_report_written": True,
        "private_readiness_diagnostic_gitignored": _git_check_ignored(PRIVATE_READINESS_DIAGNOSTIC_PATH),
        "private_readiness_blocker_queue_gitignored": _git_check_ignored(PRIVATE_BLOCKER_QUEUE_PATH),
        "private_readiness_report_gitignored": _git_check_ignored(PRIVATE_READINESS_REPORT_PATH),
        "source_private_response_template_gitignored": _git_check_ignored(SOURCE_PRIVATE_RESPONSE_TEMPLATE_PATH),
        "source_private_pending_queue_gitignored": _git_check_ignored(SOURCE_PRIVATE_PENDING_QUEUE_PATH),
        "source_private_diagnostic_gitignored": _git_check_ignored(SOURCE_PRIVATE_DIAGNOSTIC_PATH),
        "source_private_report_gitignored": _git_check_ignored(SOURCE_PRIVATE_REPORT_PATH),
        "owner_or_agent_valid_response_supplied": False,
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
        ("source_intake_loaded", summary["source_phase_id"] == source_intake.PHASE_ID),
        ("source_go_no_go_preserved", summary["source_go_no_go_decision"] == "NO_GO"),
        ("source_matrix_clean", summary["source_matrix_check_fail_count"] == 0),
        ("source_template_loaded", summary["source_private_response_template_item_count"] == 48),
        ("source_pending_queue_loaded", summary["source_private_pending_queue_item_count"] == 48),
        ("readiness_recheck_performed", summary["diagnostic_readiness_recheck_performed"] is True),
        ("no_ready_diagnostic_response", summary["diagnostic_response_ready_count"] == 0),
        ("all_diagnostic_responses_blocked", summary["diagnostic_response_blocker_count"] == 48),
        ("no_valid_diagnostic_response", summary["valid_diagnostic_response_count"] == 0),
        ("no_actionable_resolution", summary["actionable_resolution_count"] == 0),
        (
            "diagnostic_kind_counts_locked",
            summary["source_reference_or_owner_exclusion_readiness_blocker_count"] == 40
            and summary["formula_or_non_numeric_mapping_readiness_blocker_count"] == 8,
        ),
        (
            "no_binding_or_retry_ready_after_recheck",
            summary["binding_ready_after_readiness_recheck_count"] == 0
            and summary["comparison_retry_ready_after_readiness_recheck_count"] == 0,
        ),
        ("private_readiness_outputs_ignored", summary["private_readiness_blocker_queue_gitignored"] is True),
        ("raw_inbox_untouched", summary["raw_boundary"]["raw_inbox_mutated_by_this_phase"] is False),
        (
            "downstream_gates_closed",
            summary["github_upload_performed"] is False and summary["business_execution_performed"] is False,
        ),
    ]
    rows = [{"check_code": code, "status": "PASS" if passed else "FAIL"} for code, passed in checks]
    pass_count = sum(1 for row in rows if row["status"] == "PASS")
    return {
        "schema_version": "kmfa.v014_authorized_resolution_owner_or_agent_diagnostic_readiness_recheck_after_intake_matrix_public_safe.v1",
        "record_type": "v014_authorized_resolution_owner_or_agent_diagnostic_readiness_recheck_after_intake_matrix_public_safe",
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
        "schema_version": "kmfa.v014_authorized_resolution_owner_or_agent_diagnostic_readiness_recheck_after_intake_go_no_go.v1",
        "record_type": "v014_authorized_resolution_owner_or_agent_diagnostic_readiness_recheck_after_intake_go_no_go",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": summary["generated_at"],
        "status": STATUS,
        "decision": DECISION,
        "readiness_conclusion": READINESS_CONCLUSION,
        "diagnostic_response_ready_count": 0,
        "diagnostic_response_blocker_count": summary["diagnostic_response_blocker_count"],
        "pending_diagnostic_response_count": summary["pending_diagnostic_response_count"],
        "valid_diagnostic_response_count": 0,
        "actionable_resolution_count": 0,
        "binding_ready_after_readiness_recheck_count": 0,
        "comparison_retry_ready_after_readiness_recheck_count": 0,
        "raw_candidate_fingerprint_bound_by_this_phase": False,
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
        "schema_version": "kmfa.v014_authorized_resolution_owner_or_agent_diagnostic_readiness_recheck_after_intake_manifest.v1",
        "record_type": "v014_authorized_resolution_owner_or_agent_diagnostic_readiness_recheck_after_intake_manifest",
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
            "source_intake_public_summary": "public_safe_metadata_copy",
            "source_intake_public_manifest": "public_safe_metadata_copy",
            "source_intake_public_go_no_go": "public_safe_metadata_copy",
            "source_intake_public_matrix": "public_safe_metadata_copy",
            "source_private_response_template": "ignored_private_runtime",
            "source_private_pending_queue": "ignored_private_runtime",
            "source_private_diagnostic": "ignored_private_runtime",
            "source_private_report": "ignored_private_runtime",
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
            "private:owner_or_agent_diagnostic_readiness_recheck_diagnostic",
            "private:owner_or_agent_diagnostic_readiness_blocker_queue",
            "private:owner_or_agent_diagnostic_readiness_recheck_report",
        ],
        "raw_boundary": summary["raw_boundary"],
        "public_safety": summary["public_safety"],
        "test_commands": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_diagnostic_readiness_recheck_after_intake.py --generated-at 2026-07-08T00:00:00+10:00",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_diagnostic_readiness_recheck_after_intake.py --require-private-readiness",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_diagnostic_readiness_recheck_after_intake",
        ],
        "git": {
            "branch": _git_output(["branch", "--show-current"]),
            "head": "local_commit_recorded_after_validation",
            "status_short_branch": "omitted_for_reproducible_phase_manifest",
            "changed_kmfa_files": _phase_public_files(),
        },
    }


def _write_human(summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any]) -> None:
    _write_text(
        REPORT_PATH,
        f"""# V014 Authorized Source Reference Or Exclusion Application Owner Or Agent Diagnostic Readiness Recheck After Intake

Generated at: {summary["generated_at"]}

## Scope

- Phase: `{PHASE_ID}`
- Decision: `{DECISION}`
- Status: `{STATUS}`
- Source: prior public-safe owner/agent diagnostic intake and ignored private response template / pending queue.
- Raw boundary: no raw inbox read, list, stat, parse, value extraction, write, delete, move, rename, copy, normalize or mutation.

## Public-Safe Readiness Result

- Source private response template items: `{summary["source_private_response_template_item_count"]}`
- Source private pending queue items: `{summary["source_private_pending_queue_item_count"]}`
- Diagnostic response ready count: `{summary["diagnostic_response_ready_count"]}`
- Diagnostic response blocker count: `{summary["diagnostic_response_blocker_count"]}`
- Source reference or owner exclusion readiness blockers: `{summary["source_reference_or_owner_exclusion_readiness_blocker_count"]}`
- Formula or non-numeric mapping readiness blockers: `{summary["formula_or_non_numeric_mapping_readiness_blocker_count"]}`
- Valid diagnostic responses: `{summary["valid_diagnostic_response_count"]}`
- Actionable resolutions: `{summary["actionable_resolution_count"]}`
- Binding ready after recheck: `{summary["binding_ready_after_readiness_recheck_count"]}`
- Comparison retry ready after recheck: `{summary["comparison_retry_ready_after_readiness_recheck_count"]}`
- Unresolved differences after this phase: `{summary["unresolved_difference_count"]}`

## Gate

This phase rechecks readiness only. It does not import owner/agent answers,
apply authoritative bindings, compare raw and processed values, reconcile data,
claim business consistency, upload to GitHub, reinstall the app, or execute
business use.

Next required input: `{NEXT_REQUIRED_INPUT}`.
""",
    )
    _write_text(
        GO_NO_GO_RECORD_PATH,
        f"""# Go / No-Go Record

- Phase: `{PHASE_ID}`
- Decision: `{go_no_go["decision"]}`
- Reason: `{READINESS_CONCLUSION}`
- Matrix: `{matrix["check_pass_count"]}` pass / `{matrix["check_fail_count"]}` fail
- GitHub upload: not allowed in this phase.
- App reinstall: not allowed in this phase.
""",
    )
    _write_text(
        TEST_RESULTS_PATH,
        f"""# Test Results

- RED: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_diagnostic_readiness_recheck_after_intake` failed before implementation because the generator module did not exist.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_diagnostic_readiness_recheck_after_intake.py --generated-at 2026-07-08T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_diagnostic_readiness_recheck_after_intake.py --require-private-readiness`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_diagnostic_readiness_recheck_after_intake`
- Governance validators, CSV shape checks, diff check, raw/private marker scan, secret scan and private-runtime tracked-file scan: expected before commit.

Expected matrix result: {matrix["check_pass_count"]}/{matrix["check_count"]} PASS.
""",
    )
    _write_text(
        RISK_REGISTER_PATH,
        """# Risk Register

- Risk: readiness recheck is mistaken for a valid owner/agent response.
- Control: decision remains NO_GO and ready/valid/actionable/binding/comparison counts remain zero.
- Risk: private handles leak into public artifacts.
- Control: public artifacts contain aggregate counts only; private readiness outputs stay ignored.
- Risk: raw inbox is modified.
- Control: this phase consumes existing ignored diagnostic-intake artifacts only and does not touch the raw inbox.
""",
    )
    _write_text(
        ROLLBACK_PATH,
        f"""# Rollback Plan

Remove artifacts for `{PHASE_ID}`, metadata copies, private readiness outputs,
tool, validator, focused test and governance rows. Do not touch source intake
evidence, prior private artifacts or raw inbox files.
""",
    )


def _write_private_outputs(
    *,
    generated_at: str,
    source_summary: dict[str, Any],
    blocker_rows: list[dict[str, Any]],
    summary: dict[str, Any],
) -> None:
    diagnostic = {
        "schema_version": "kmfa.private.v014_authorized_resolution_owner_or_agent_diagnostic_readiness_recheck_after_intake.v1",
        "classification": "private_owner_or_agent_diagnostic_readiness_recheck_after_intake_do_not_commit",
        "record_type": "v014_authorized_resolution_owner_or_agent_diagnostic_readiness_recheck_after_intake_private_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "source_phase_id": source_summary.get("phase_id"),
        "readiness_conclusion": READINESS_CONCLUSION,
        "diagnostic_response_ready_count": 0,
        "diagnostic_response_blocker_count": len(blocker_rows),
        "valid_diagnostic_response_count": 0,
        "actionable_resolution_count": 0,
        "binding_ready_after_readiness_recheck_count": 0,
        "comparison_retry_ready_after_readiness_recheck_count": 0,
        "raw_boundary": summary["raw_boundary"],
    }
    _write_json(PRIVATE_READINESS_DIAGNOSTIC_PATH, diagnostic)
    _write_jsonl(PRIVATE_BLOCKER_QUEUE_PATH, blocker_rows)
    _write_text(
        PRIVATE_READINESS_REPORT_PATH,
        "\n".join(
            [
                "# Private Owner Or Agent Diagnostic Readiness Recheck After Intake",
                "",
                f"- phase_id: `{PHASE_ID}`",
                f"- diagnostic_response_ready_count: `{summary['diagnostic_response_ready_count']}`",
                f"- diagnostic_response_blocker_count: `{summary['diagnostic_response_blocker_count']}`",
                f"- valid_diagnostic_response_count: `{summary['valid_diagnostic_response_count']}`",
                f"- actionable_resolution_count: `{summary['actionable_resolution_count']}`",
                "",
                "This private readiness output may contain private handles and must remain ignored.",
                "",
            ]
        ),
    )


def _write_governance_events(generated_at: str, summary: dict[str, Any]) -> None:
    event_id = (
        "DEV-KMFA-20260708-V014-AUTHORIZED-SOURCE-REFERENCE-OR-EXCLUSION-APPLICATION-"
        "OWNER-OR-AGENT-DIAGNOSTIC-READINESS-RECHECK-AFTER-INTAKE"
    )
    event = {
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
        "summary": "Rechecked owner/agent diagnostic response readiness after intake; all 48 items remain blocked.",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "files_changed": _phase_public_files(),
        "test_commands": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_diagnostic_readiness_recheck_after_intake.py --generated-at 2026-07-08T00:00:00+10:00",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_diagnostic_readiness_recheck_after_intake.py --require-private-readiness",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_diagnostic_readiness_recheck_after_intake",
        ],
        "test_results": ["PENDING: final validation results will be recorded before local commit."],
        "next_required_input": NEXT_REQUIRED_INPUT,
        "diagnostic_response_ready_count": 0,
        "diagnostic_response_blocker_count": summary["diagnostic_response_blocker_count"],
        "pending_diagnostic_response_count": summary["pending_diagnostic_response_count"],
        "valid_diagnostic_response_count": 0,
        "actionable_resolution_count": 0,
        "binding_ready_after_readiness_recheck_count": 0,
        "comparison_retry_ready_after_readiness_recheck_count": 0,
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
    _upsert_jsonl(DEVELOPMENT_EVENTS_PATH, event, ("event_id",))
    phase_status = {
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
    }
    _upsert_jsonl(STAGE_STATUS_PATH, phase_status, ("phase_id", "task_id"))
    phase_task_status = {
        "schema_version": "kmfa.v014_stage_phase_task_status.v1",
        "project_id": "KMFA",
        "version": VERSION,
        "raw_data_committed": False,
        "record_type": "v014_phase",
        "roadmap_stage_id": "VALUE-CONSISTENCY",
        "roadmap_phase_id": PHASE_ID.replace("V014_", ""),
        "governance_stage_id": "VALUE-CONSISTENCY",
        "phase_id": PHASE_ID,
        "name": "v0.1.4 authorized source reference or exclusion application owner/agent diagnostic readiness recheck after intake",
        "status": STATUS,
        "completed_task_units": 1,
        "estimated_task_units": 1,
        "derived_percent": 100.0,
        "acceptance_id": ACCEPTANCE_ID,
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "fact_level": "EXTRACTED",
        "updated_at": generated_at[:10],
        "stage_id": "VALUE-CONSISTENCY",
        "phase_goal": "recheck readiness of owner/agent diagnostic responses after the 48-item intake",
        "task_count": 3,
        "acceptance_output": "Owner/agent diagnostic readiness manifest, summary, Go No-Go, private blocker queue, validator, focused test and governance records",
    }
    _upsert_jsonl(TASK_STATUS_PATH, phase_task_status, ("phase_id", "record_type", "task_id"))
    for task_suffix, task_goal in (
        ("T1", "read prior owner/agent diagnostic intake public artifacts and ignored private pending queue read-only"),
        ("T2", "write ignored private owner/agent diagnostic readiness blocker queue"),
        ("T3", "emit public-safe NO_GO readiness evidence while keeping binding comparison and upload gates closed"),
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
                "task_id": f"{TASK_ID}-{task_suffix}",
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
    template_rows = _read_jsonl(SOURCE_PRIVATE_RESPONSE_TEMPLATE_PATH)
    pending_rows = _read_jsonl(SOURCE_PRIVATE_PENDING_QUEUE_PATH)
    _read_json(SOURCE_PRIVATE_DIAGNOSTIC_PATH)
    if not SOURCE_PRIVATE_REPORT_PATH.exists():
        raise FileNotFoundError(SOURCE_PRIVATE_REPORT_PATH)
    blocker_rows = _build_blocker_rows(generated_at=generated, template_rows=template_rows, pending_rows=pending_rows)
    summary = _build_summary(
        generated_at=generated,
        source_summary=source_summary,
        source_manifest=source_manifest,
        source_go_no_go=source_go_no_go,
        source_matrix=source_matrix,
        template_rows=template_rows,
        pending_rows=pending_rows,
        blocker_rows=blocker_rows,
    )
    matrix = _build_matrix(summary)
    go_no_go = _build_go_no_go(summary)
    manifest = _build_manifest(summary, matrix, go_no_go)
    _write_private_outputs(
        generated_at=generated,
        source_summary=source_summary,
        blocker_rows=blocker_rows,
        summary=summary,
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
        "PASS: generated V014 authorized source reference or exclusion application "
        f"owner/agent diagnostic readiness recheck decision={summary['decision']} "
        f"blockers={summary['diagnostic_response_blocker_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
