#!/usr/bin/env python3
"""Prepare owner/agent diagnostic intake after the authorized-resolution packet.

This phase creates a private response template and pending queue from the prior
diagnostic packet. It does not read or mutate the raw inbox, does not accept a
valid response, and does not apply any binding or value comparison.
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
    v014_residual_difference_authorized_source_reference_or_exclusion_application_diagnostic_packet_after_blocked_handoff
    as source_packet,
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
    "OWNER_OR_AGENT_DIAGNOSTIC_INTAKE_AFTER_PACKET"
)
TASK_ID = (
    "KMFA-V014-RESIDUAL-DIFFERENCE-AUTHORIZED-SOURCE-REFERENCE-OR-EXCLUSION-APPLICATION-"
    "OWNER-OR-AGENT-DIAGNOSTIC-INTAKE-AFTER-PACKET-20260708"
)
ACCEPTANCE_ID = (
    "ACC-V014-RESIDUAL-DIFFERENCE-AUTHORIZED-SOURCE-REFERENCE-OR-EXCLUSION-APPLICATION-"
    "OWNER-OR-AGENT-DIAGNOSTIC-INTAKE-AFTER-PACKET"
)
VERSION = (
    "0.1.4-residual-difference-authorized-source-reference-or-exclusion-application-"
    "owner-or-agent-diagnostic-intake-after-packet"
)
STATUS = (
    "completed_validated_local_only_authorized_source_reference_or_exclusion_application_"
    "owner_or_agent_diagnostic_intake_after_packet_no_go"
)
DECISION = "NO_GO"
INTAKE_CONCLUSION = "private_owner_or_agent_diagnostic_response_template_written_all_48_items_pending"
NEXT_REQUIRED_INPUT = source_packet.NEXT_REQUIRED_INPUT
NEXT_RECOMMENDED_PHASE = (
    "V014_RESIDUAL_DIFFERENCE_AUTHORIZED_SOURCE_REFERENCE_OR_EXCLUSION_APPLICATION_"
    "OWNER_OR_AGENT_DIAGNOSTIC_READINESS_RECHECK_AFTER_INTAKE"
)

SOURCE_REFERENCE_DIAGNOSTIC_KIND = "provide_authoritative_source_reference_or_owner_exclusion"
FORMULA_MAPPING_DIAGNOSTIC_KIND = "provide_formula_or_non_numeric_mapping"
EXPECTED_RESPONSE_TEMPLATE_COUNTS = {
    SOURCE_REFERENCE_DIAGNOSTIC_KIND: 40,
    FORMULA_MAPPING_DIAGNOSTIC_KIND: 8,
}

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
PREFIX = (
    "residual_difference_authorized_source_reference_or_exclusion_application_"
    "owner_or_agent_diagnostic_intake_after_packet"
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

SOURCE_DIAGNOSTIC_PACKET_SUMMARY_PATH = source_packet.METADATA_SUMMARY_PATH
SOURCE_DIAGNOSTIC_PACKET_MANIFEST_PATH = source_packet.METADATA_MANIFEST_PATH
SOURCE_DIAGNOSTIC_PACKET_GO_NO_GO_PATH = source_packet.METADATA_GO_NO_GO_PATH
SOURCE_DIAGNOSTIC_PACKET_MATRIX_PATH = source_packet.METADATA_MATRIX_PATH
SOURCE_PRIVATE_DIAGNOSTIC_PACKET_PATH = source_packet.PRIVATE_DIAGNOSTIC_PACKET_PATH
SOURCE_PRIVATE_DIAGNOSTIC_QUEUE_PATH = source_packet.PRIVATE_DIAGNOSTIC_QUEUE_PATH
SOURCE_PRIVATE_DIAGNOSTIC_REPORT_PATH = source_packet.PRIVATE_DIAGNOSTIC_REPORT_PATH

PRIVATE_OUTPUT_DIR = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_diagnostic_intake_after_packet"
)
PRIVATE_RESPONSE_TEMPLATE_PATH = PRIVATE_OUTPUT_DIR / "private_owner_or_agent_diagnostic_response_template.jsonl"
PRIVATE_PENDING_QUEUE_PATH = PRIVATE_OUTPUT_DIR / "private_owner_or_agent_diagnostic_pending_queue.jsonl"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_owner_or_agent_diagnostic_intake_diagnostic.json"
PRIVATE_REPORT_PATH = PRIVATE_OUTPUT_DIR / "private_owner_or_agent_diagnostic_intake_report.md"

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
        "KMFA/tests/test_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_diagnostic_intake_after_packet.py",
        "KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_diagnostic_intake_after_packet.py",
        "KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_diagnostic_intake_after_packet.py",
        "KMFA/功能清单.md",
        "KMFA/开发记录.md",
        "KMFA/模型参数文件.md",
    ]


def _raw_boundary() -> dict[str, bool]:
    return {
        "user_declared_raw_data_immutable": True,
        "raw_data_root_readonly_policy_active": True,
        "source_diagnostic_packet_public_artifacts_read_by_this_phase": True,
        "source_diagnostic_packet_manifest_read_by_this_phase": True,
        "source_diagnostic_packet_go_no_go_read_by_this_phase": True,
        "source_diagnostic_packet_matrix_read_by_this_phase": True,
        "source_private_diagnostic_packet_read_by_this_phase": True,
        "source_private_diagnostic_queue_read_by_this_phase": True,
        "source_private_diagnostic_report_existence_checked_by_this_phase": True,
        "private_response_template_written_by_this_phase": True,
        "private_pending_queue_written_by_this_phase": True,
        "private_diagnostic_written_by_this_phase": True,
        "private_report_written_by_this_phase": True,
        "source_private_diagnostic_packet_mutated_by_this_phase": False,
        "source_private_diagnostic_queue_mutated_by_this_phase": False,
        "source_private_diagnostic_report_mutated_by_this_phase": False,
        "owner_or_agent_valid_response_supplied_by_this_phase": False,
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
        "source_private_diagnostic_packet_committed": False,
        "source_private_diagnostic_queue_committed": False,
        "source_private_diagnostic_report_committed": False,
        "private_response_template_committed": False,
        "private_pending_queue_committed": False,
        "private_diagnostic_committed": False,
        "private_report_committed": False,
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


def _build_template_rows(*, generated_at: str, source_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(source_rows, start=1):
        rows.append(
            {
                "response_template_item_id": f"ASR-OE-APP-OWNER-AGENT-INTAKE-{index:03d}",
                "phase_id": PHASE_ID,
                "task_id": TASK_ID,
                "generated_at": generated_at,
                "source_diagnostic_packet_item_id": row.get("diagnostic_packet_item_id"),
                source_packet.PRIVATE_SLOT_KEY: row.get(source_packet.PRIVATE_SLOT_KEY),
                "intake_track": row.get("intake_track"),
                "diagnostic_kind": row.get("diagnostic_kind"),
                "response_status": "pending_owner_or_external_agent",
                "required_response": row.get("source_required_authorized_input_type"),
                "valid_diagnostic_response": False,
                "actionable_resolution_ready": False,
                "binding_ready_after_response": False,
                "comparison_retry_ready_after_response": False,
                "raw_candidate_fingerprint_bound_by_this_phase": False,
                "raw_to_processed_value_comparison_performed_by_this_phase": False,
                "full_raw_to_processed_value_comparison_complete": False,
                "business_value_consistency_verified": False,
                "public_commit_allowed": False,
            }
        )
    return rows


def _build_pending_rows(template_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "pending_queue_item_id": row["response_template_item_id"],
            "phase_id": PHASE_ID,
            "source_diagnostic_packet_item_id": row.get("source_diagnostic_packet_item_id"),
            "diagnostic_kind": row.get("diagnostic_kind"),
            "pending_reason": "missing_valid_owner_or_agent_diagnostic_response",
            "owner_or_external_agent_action_required": True,
            "valid_diagnostic_response": False,
            "actionable_resolution_ready": False,
            "public_commit_allowed": False,
        }
        for row in template_rows
    ]


def _write_private_outputs(
    *,
    generated_at: str,
    source_summary: dict[str, Any],
    template_rows: list[dict[str, Any]],
    pending_rows: list[dict[str, Any]],
    raw_boundary: dict[str, bool],
) -> dict[str, Any]:
    diagnostic_kind_counts = Counter(row.get("diagnostic_kind") for row in template_rows)
    diagnostic = {
        "schema_version": "kmfa.private.v014_authorized_resolution_owner_or_agent_diagnostic_intake_after_packet.v1",
        "classification": "private_owner_or_agent_diagnostic_intake_after_packet_do_not_commit",
        "record_type": "v014_authorized_resolution_owner_or_agent_diagnostic_intake_after_packet_private_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "source_phase_id": source_summary.get("phase_id"),
        "intake_conclusion": INTAKE_CONCLUSION,
        "private_response_template_item_count": len(template_rows),
        "private_pending_queue_item_count": len(pending_rows),
        "diagnostic_kind_counts": dict(diagnostic_kind_counts),
        "valid_diagnostic_response_count": 0,
        "actionable_resolution_count": 0,
        "binding_ready_after_intake_count": 0,
        "comparison_retry_ready_after_intake_count": 0,
        "raw_boundary": raw_boundary,
    }
    _write_jsonl(PRIVATE_RESPONSE_TEMPLATE_PATH, template_rows)
    _write_jsonl(PRIVATE_PENDING_QUEUE_PATH, pending_rows)
    _write_json(PRIVATE_DIAGNOSTIC_PATH, diagnostic)
    _write_text(
        PRIVATE_REPORT_PATH,
        "\n".join(
            [
                "# Private Owner Or Agent Diagnostic Intake After Packet",
                "",
                f"- phase_id: `{PHASE_ID}`",
                f"- private_response_template_item_count: `{len(template_rows)}`",
                f"- private_pending_queue_item_count: `{len(pending_rows)}`",
                "- valid_diagnostic_response_count: `0`",
                "- actionable_resolution_count: `0`",
                "- binding_ready_after_intake_count: `0`",
                "- comparison_retry_ready_after_intake_count: `0`",
                "",
                "This private intake may contain private handles and must remain ignored.",
                "",
            ]
        ),
    )
    return diagnostic


def _build_summary(
    *,
    generated_at: str,
    source_summary: dict[str, Any],
    source_manifest: dict[str, Any],
    source_go_no_go: dict[str, Any],
    source_matrix: dict[str, Any],
    source_private_packet: dict[str, Any],
    source_rows: list[dict[str, Any]],
    template_rows: list[dict[str, Any]],
    pending_rows: list[dict[str, Any]],
    raw_boundary: dict[str, bool],
    public_safety: dict[str, bool],
) -> dict[str, Any]:
    diagnostic_kind_counts = Counter(row.get("diagnostic_kind") for row in template_rows)
    return {
        "schema_version": "kmfa.v014_authorized_resolution_owner_or_agent_diagnostic_intake_after_packet_summary.v1",
        "record_type": "v014_authorized_resolution_owner_or_agent_diagnostic_intake_after_packet_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": generated_at,
        "status": STATUS,
        "decision": DECISION,
        "intake_conclusion": INTAKE_CONCLUSION,
        "source_phase_id": source_summary.get("phase_id"),
        "source_manifest_phase_id": source_manifest.get("phase_id"),
        "source_go_no_go_decision": source_go_no_go.get("decision"),
        "source_matrix_check_fail_count": source_matrix.get("check_fail_count"),
        "source_private_packet_phase_id": source_private_packet.get("phase_id"),
        "source_private_diagnostic_queue_item_count": len(source_rows),
        "source_diagnostic_packet_item_count": source_summary.get("diagnostic_packet_item_count"),
        "source_external_agent_private_packet_item_count": source_summary.get(
            "external_agent_private_packet_item_count"
        ),
        "source_reference_or_owner_exclusion_diagnostic_item_count": source_summary.get(
            "source_reference_or_owner_exclusion_diagnostic_item_count"
        ),
        "formula_or_non_numeric_mapping_diagnostic_item_count": source_summary.get(
            "formula_or_non_numeric_mapping_diagnostic_item_count"
        ),
        "source_binding_ready_after_diagnostic_packet_count": source_summary.get(
            "binding_ready_after_diagnostic_packet_count"
        ),
        "source_comparison_retry_ready_after_diagnostic_packet_count": source_summary.get(
            "comparison_retry_ready_after_diagnostic_packet_count"
        ),
        "owner_or_agent_diagnostic_intake_performed_by_this_phase": True,
        "private_response_template_item_count": len(template_rows),
        "private_pending_queue_item_count": len(pending_rows),
        "pending_diagnostic_response_count": len(pending_rows),
        "valid_diagnostic_response_count": 0,
        "invalid_diagnostic_response_count": 0,
        "actionable_resolution_count": 0,
        "source_reference_or_owner_exclusion_response_template_count": diagnostic_kind_counts[
            SOURCE_REFERENCE_DIAGNOSTIC_KIND
        ],
        "formula_or_non_numeric_mapping_response_template_count": diagnostic_kind_counts[
            FORMULA_MAPPING_DIAGNOSTIC_KIND
        ],
        "safe_auto_resolution_available_count": 0,
        "binding_ready_after_intake_count": 0,
        "comparison_retry_ready_after_intake_count": 0,
        "unresolved_difference_count": source_summary.get("unresolved_difference_count"),
        "private_response_template_gitignored": _git_check_ignored(PRIVATE_RESPONSE_TEMPLATE_PATH),
        "private_pending_queue_gitignored": _git_check_ignored(PRIVATE_PENDING_QUEUE_PATH),
        "private_diagnostic_gitignored": _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH),
        "private_report_gitignored": _git_check_ignored(PRIVATE_REPORT_PATH),
        "source_private_diagnostic_packet_gitignored": _git_check_ignored(SOURCE_PRIVATE_DIAGNOSTIC_PACKET_PATH),
        "source_private_diagnostic_queue_gitignored": _git_check_ignored(SOURCE_PRIVATE_DIAGNOSTIC_QUEUE_PATH),
        "source_private_diagnostic_report_gitignored": _git_check_ignored(SOURCE_PRIVATE_DIAGNOSTIC_REPORT_PATH),
        "owner_or_agent_valid_response_supplied_by_this_phase": False,
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
        "raw_boundary": raw_boundary,
        "public_safety": public_safety,
    }


def _build_matrix(summary: dict[str, Any]) -> dict[str, Any]:
    checks = [
        ("source_packet_loaded", summary["source_phase_id"] == source_packet.PHASE_ID),
        ("source_go_no_go_preserved", summary["source_go_no_go_decision"] == "NO_GO"),
        ("source_matrix_clean", summary["source_matrix_check_fail_count"] == 0),
        ("source_private_queue_locked", summary["source_private_diagnostic_queue_item_count"] == 48),
        ("source_packet_items_locked", summary["source_diagnostic_packet_item_count"] == 48),
        ("source_external_packet_items_locked", summary["source_external_agent_private_packet_item_count"] == 48),
        (
            "source_diagnostic_kinds_locked",
            summary["source_reference_or_owner_exclusion_diagnostic_item_count"] == 40
            and summary["formula_or_non_numeric_mapping_diagnostic_item_count"] == 8,
        ),
        ("private_template_items_locked", summary["private_response_template_item_count"] == 48),
        ("private_pending_items_locked", summary["private_pending_queue_item_count"] == 48),
        (
            "template_kind_counts_locked",
            summary["source_reference_or_owner_exclusion_response_template_count"] == 40
            and summary["formula_or_non_numeric_mapping_response_template_count"] == 8,
        ),
        ("no_valid_response_yet", summary["valid_diagnostic_response_count"] == 0),
        ("no_actionable_resolution_yet", summary["actionable_resolution_count"] == 0),
        (
            "no_binding_or_retry_ready_after_intake",
            summary["binding_ready_after_intake_count"] == 0
            and summary["comparison_retry_ready_after_intake_count"] == 0,
        ),
        ("private_intake_outputs_ignored", summary["private_pending_queue_gitignored"] is True),
        ("raw_inbox_untouched", summary["raw_boundary"]["raw_inbox_mutated_by_this_phase"] is False),
        ("downstream_gates_closed", summary["github_upload_performed"] is False and summary["business_execution_performed"] is False),
    ]
    rows = [{"check_code": code, "status": "PASS" if passed else "FAIL"} for code, passed in checks]
    pass_count = sum(1 for row in rows if row["status"] == "PASS")
    return {
        "schema_version": "kmfa.v014_authorized_resolution_owner_or_agent_diagnostic_intake_after_packet_matrix_public_safe.v1",
        "record_type": "v014_authorized_resolution_owner_or_agent_diagnostic_intake_after_packet_matrix_public_safe",
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
        "schema_version": "kmfa.v014_authorized_resolution_owner_or_agent_diagnostic_intake_after_packet_go_no_go.v1",
        "record_type": "v014_authorized_resolution_owner_or_agent_diagnostic_intake_after_packet_go_no_go",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": summary["generated_at"],
        "status": STATUS,
        "decision": DECISION,
        "intake_conclusion": INTAKE_CONCLUSION,
        "private_response_template_item_count": summary["private_response_template_item_count"],
        "pending_diagnostic_response_count": summary["pending_diagnostic_response_count"],
        "valid_diagnostic_response_count": 0,
        "actionable_resolution_count": 0,
        "binding_ready_after_intake_count": 0,
        "comparison_retry_ready_after_intake_count": 0,
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


def _write_human(summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any]) -> None:
    _write_text(
        REPORT_PATH,
        f"""# V014 Authorized Source Reference Or Exclusion Application Owner Or Agent Diagnostic Intake After Packet

Generated at: {summary["generated_at"]}

## Scope

- Phase: `{PHASE_ID}`
- Decision: `{DECISION}`
- Status: `{STATUS}`
- Source: prior public-safe diagnostic packet and ignored private diagnostic queue.
- Raw boundary: no raw inbox read, list, stat, parse, value extraction, write, delete, move, rename, copy, normalize or mutation.

## Public-Safe Intake Result

- Source diagnostic packet items: `{summary["source_diagnostic_packet_item_count"]}`
- Private response template items: `{summary["private_response_template_item_count"]}`
- Private pending queue items: `{summary["private_pending_queue_item_count"]}`
- Source reference or owner exclusion response-template items: `{summary["source_reference_or_owner_exclusion_response_template_count"]}`
- Formula or non-numeric mapping response-template items: `{summary["formula_or_non_numeric_mapping_response_template_count"]}`
- Valid diagnostic responses: `{summary["valid_diagnostic_response_count"]}`
- Actionable resolutions: `{summary["actionable_resolution_count"]}`
- Binding ready after intake: `{summary["binding_ready_after_intake_count"]}`
- Comparison retry ready after intake: `{summary["comparison_retry_ready_after_intake_count"]}`
- Unresolved differences after this phase: `{summary["unresolved_difference_count"]}`

## Gate

This phase prepares response intake only. It does not import owner/agent answers,
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
- Reason: `{INTAKE_CONCLUSION}`
- Matrix: `{matrix["check_pass_count"]}` pass / `{matrix["check_fail_count"]}` fail
- GitHub upload: not allowed in this phase.
- App reinstall: not allowed in this phase.
""",
    )
    _write_text(
        TEST_RESULTS_PATH,
        f"""# Test Results

- RED: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_diagnostic_intake_after_packet` failed before implementation because the generator module did not exist.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_diagnostic_intake_after_packet.py --generated-at 2026-07-08T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_diagnostic_intake_after_packet.py --require-private-intake`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_diagnostic_intake_after_packet`
- Governance validators, CSV shape checks, diff check, raw/private marker scan, secret scan and private-runtime tracked-file scan: expected before commit.

Expected matrix result: {matrix["check_pass_count"]}/{matrix["check_count"]} PASS.
""",
    )
    _write_text(
        RISK_REGISTER_PATH,
        """# Risk Register

- Risk: response template is mistaken for a valid owner/agent response.
- Control: decision remains NO_GO and valid/actionable/binding/comparison counts remain zero.
- Risk: private handles leak into public artifacts.
- Control: public artifacts contain aggregate counts only; private intake outputs stay ignored.
- Risk: raw inbox is modified.
- Control: this phase consumes existing ignored diagnostic-packet artifacts only and does not touch the raw inbox.
""",
    )
    _write_text(
        ROLLBACK_PATH,
        f"""# Rollback Plan

Remove artifacts for `{PHASE_ID}`, metadata copies, private intake outputs, tool,
validator, focused test and governance rows. Do not touch source diagnostic
packet evidence, prior private artifacts or raw inbox files.
""",
    )


def _build_manifest(summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v014_authorized_resolution_owner_or_agent_diagnostic_intake_after_packet_manifest.v1",
        "record_type": "v014_authorized_resolution_owner_or_agent_diagnostic_intake_after_packet_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": summary["generated_at"],
        "status": STATUS,
        "decision": DECISION,
        "intake_conclusion": INTAKE_CONCLUSION,
        "summary": summary,
        "matrix": matrix,
        "go_no_go_report": go_no_go,
        "source_artifacts": {
            "diagnostic_packet_summary": "public_safe_metadata_copy",
            "diagnostic_packet_manifest": "public_safe_metadata_copy",
            "diagnostic_packet_go_no_go": "public_safe_metadata_copy",
            "diagnostic_packet_matrix": "public_safe_metadata_copy",
            "diagnostic_packet_private_packet": "ignored_private_runtime",
            "diagnostic_packet_private_queue": "ignored_private_runtime",
            "diagnostic_packet_private_report": "ignored_private_runtime",
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
            "private:owner_or_agent_diagnostic_response_template",
            "private:owner_or_agent_diagnostic_pending_queue",
            "private:owner_or_agent_diagnostic_intake_diagnostic",
            "private:owner_or_agent_diagnostic_intake_report",
        ],
        "raw_boundary": summary["raw_boundary"],
        "public_safety": summary["public_safety"],
        "test_commands": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_diagnostic_intake_after_packet.py --generated-at 2026-07-08T00:00:00+10:00",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_diagnostic_intake_after_packet.py --require-private-intake",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_diagnostic_intake_after_packet",
        ],
        "git": {
            "branch": _git_output(["branch", "--show-current"]),
            "head": "local_commit_recorded_after_validation",
            "status_short_branch": "omitted_for_reproducible_phase_manifest",
            "changed_kmfa_files": _phase_public_files(),
        },
    }


def _write_governance_events(generated_at: str, summary: dict[str, Any]) -> None:
    event_id = (
        "DEV-KMFA-20260708-V014-AUTHORIZED-SOURCE-REFERENCE-OR-EXCLUSION-APPLICATION-"
        "OWNER-OR-AGENT-DIAGNOSTIC-INTAKE-AFTER-PACKET"
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
        "summary": "Prepared private owner/agent response template and pending queue for 48 diagnostic-packet items.",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "files_changed": _phase_public_files(),
        "test_commands": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_diagnostic_intake_after_packet.py --generated-at 2026-07-08T00:00:00+10:00",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_diagnostic_intake_after_packet.py --require-private-intake",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_diagnostic_intake_after_packet",
        ],
        "test_results": ["PENDING: final validation results will be recorded before local commit."],
        "next_required_input": NEXT_REQUIRED_INPUT,
        "private_response_template_item_count": summary["private_response_template_item_count"],
        "pending_diagnostic_response_count": summary["pending_diagnostic_response_count"],
        "valid_diagnostic_response_count": 0,
        "actionable_resolution_count": 0,
        "binding_ready_after_intake_count": 0,
        "comparison_retry_ready_after_intake_count": 0,
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
        "name": "v0.1.4 authorized source reference or exclusion application owner/agent diagnostic intake after packet",
        "status": STATUS,
        "completed_task_units": 1,
        "estimated_task_units": 1,
        "derived_percent": 100.0,
        "acceptance_id": ACCEPTANCE_ID,
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "fact_level": "EXTRACTED",
        "updated_at": generated_at[:10],
        "stage_id": "VALUE-CONSISTENCY",
        "phase_goal": "prepare owner/agent diagnostic response template from the 48-item diagnostic packet",
        "task_count": 3,
        "acceptance_output": "Owner/agent diagnostic intake manifest, summary, Go No-Go, private response template, validator, focused test and governance records",
    }
    _upsert_jsonl(TASK_STATUS_PATH, phase_task_status, ("phase_id", "record_type", "task_id"))
    for task_suffix, task_goal in (
        ("T1", "read prior public-safe diagnostic packet and ignored private diagnostic queue read-only"),
        ("T2", "write ignored private owner/agent diagnostic response template and pending queue"),
        ("T3", "emit public-safe NO_GO intake evidence while keeping binding comparison and upload gates closed"),
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
    source_summary = _read_json(SOURCE_DIAGNOSTIC_PACKET_SUMMARY_PATH)
    source_manifest = _read_json(SOURCE_DIAGNOSTIC_PACKET_MANIFEST_PATH)
    source_go_no_go = _read_json(SOURCE_DIAGNOSTIC_PACKET_GO_NO_GO_PATH)
    source_matrix = _read_json(SOURCE_DIAGNOSTIC_PACKET_MATRIX_PATH)
    source_private_packet = _read_json(SOURCE_PRIVATE_DIAGNOSTIC_PACKET_PATH)
    source_rows = _read_jsonl(SOURCE_PRIVATE_DIAGNOSTIC_QUEUE_PATH)
    if not SOURCE_PRIVATE_DIAGNOSTIC_REPORT_PATH.exists():
        raise FileNotFoundError(SOURCE_PRIVATE_DIAGNOSTIC_REPORT_PATH)
    raw_boundary = _raw_boundary()
    public_safety = _public_safety()
    template_rows = _build_template_rows(generated_at=generated, source_rows=source_rows)
    pending_rows = _build_pending_rows(template_rows)
    _write_private_outputs(
        generated_at=generated,
        source_summary=source_summary,
        template_rows=template_rows,
        pending_rows=pending_rows,
        raw_boundary=raw_boundary,
    )
    summary = _build_summary(
        generated_at=generated,
        source_summary=source_summary,
        source_manifest=source_manifest,
        source_go_no_go=source_go_no_go,
        source_matrix=source_matrix,
        source_private_packet=source_private_packet,
        source_rows=source_rows,
        template_rows=template_rows,
        pending_rows=pending_rows,
        raw_boundary=raw_boundary,
        public_safety=public_safety,
    )
    matrix = _build_matrix(summary)
    go_no_go = _build_go_no_go(summary)
    _write_human(summary, matrix, go_no_go)
    manifest = _build_manifest(summary, matrix, go_no_go)
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
        f"owner/agent diagnostic intake decision={summary['decision']} "
        f"pending={summary['pending_diagnostic_response_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
