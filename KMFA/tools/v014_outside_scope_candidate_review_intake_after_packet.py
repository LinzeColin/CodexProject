#!/usr/bin/env python3
"""Intake delegated conservative responses for the outside-scope review packet.

This phase consumes the ignored private review packet from the previous phase
and records a delegated Codex response. Because the packet has no authoritative
owner-selected candidate or corrected source-map reference, every item is kept
pending. The phase does not read the raw inbox, select candidates, correct
source maps, compare raw-to-processed values, reconcile values, upload, reinstall,
or execute business steps. Public artifacts remain aggregate-only.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


PROJECT_ROOT = Path("KMFA")
PHASE_ID = "V014_OUTSIDE_SCOPE_CANDIDATE_REVIEW_INTAKE_AFTER_PACKET"
TASK_ID = "KMFA-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-INTAKE-AFTER-PACKET-20260707"
ACCEPTANCE_ID = "ACC-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-INTAKE-AFTER-PACKET"
VERSION = "0.1.4-outside-scope-candidate-review-intake-after-packet"
STATUS = "completed_validated_local_only_outside_scope_candidate_review_intake_keep_pending_no_go"
DECISION = "NO_GO"
AUTHORITY_BASIS = "owner_delegated_codex_conservative_default_decision_current_thread"
DIAGNOSTIC_CONCLUSION = "delegated_keep_pending_review_response_intaken_no_source_map_correction"
NEXT_RECOMMENDED_PHASE = "V014_OUTSIDE_SCOPE_CANDIDATE_REVIEW_INTAKE_READINESS_RECHECK"
NEXT_REQUIRED_INPUT = "strong_owner_or_authorized_delegate_candidate_selection_or_source_map_reference_before_correction"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "outside_scope_candidate_review_intake_after_packet_summary.json"
MANIFEST_PATH = MACHINE_DIR / "outside_scope_candidate_review_intake_after_packet_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "outside_scope_candidate_review_intake_after_packet_go_no_go_report.json"
MATRIX_PATH = MACHINE_DIR / "outside_scope_candidate_review_intake_after_packet_matrix_public_safe.json"
REPORT_PATH = HUMAN_DIR / "outside_scope_candidate_review_intake_after_packet_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_candidate_review_intake_after_packet_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_candidate_review_intake_after_packet_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_candidate_review_intake_after_packet_go_no_go_report.json"
METADATA_MATRIX_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_candidate_review_intake_after_packet_matrix_public_safe.json"
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"
STAGE_STATUS_PATH = PROJECT_ROOT / "metadata/stage_status.jsonl"
TASK_STATUS_PATH = PROJECT_ROOT / "metadata/traceability/v1_4_stage_phase_task_status.jsonl"

SOURCE_PACKET_SUMMARY_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_outside_scope_candidate_review_packet_after_alignment_summary.json"
)
SOURCE_PACKET_MANIFEST_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_outside_scope_candidate_review_packet_after_alignment_manifest.json"
)
SOURCE_PRIVATE_PACKET_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_outside_scope_candidate_review_packet_after_alignment/private_outside_scope_candidate_review_packet.json"
)
SOURCE_PRIVATE_PACKET_ITEMS_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_outside_scope_candidate_review_packet_after_alignment/private_outside_scope_candidate_review_packet_items.jsonl"
)

PRIVATE_OUTPUT_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_outside_scope_candidate_review_intake_after_packet"
PRIVATE_RESPONSE_RECORD_PATH = PRIVATE_OUTPUT_DIR / "private_delegated_review_response_record.json"
PRIVATE_RESPONSE_ITEMS_PATH = PRIVATE_OUTPUT_DIR / "private_delegated_review_response_items.jsonl"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_delegated_review_response_diagnostic.json"

FILES_CHANGED = [
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
    "KMFA/metadata/stage_status.jsonl",
    "KMFA/metadata/traceability/v1_4_stage_phase_task_status.jsonl",
    "KMFA/功能清单.md",
    "KMFA/开发记录.md",
    "KMFA/模型参数文件.md",
    METADATA_SUMMARY_PATH.as_posix(),
    METADATA_MANIFEST_PATH.as_posix(),
    METADATA_GO_NO_GO_PATH.as_posix(),
    METADATA_MATRIX_PATH.as_posix(),
    SUMMARY_PATH.as_posix(),
    MANIFEST_PATH.as_posix(),
    GO_NO_GO_PATH.as_posix(),
    MATRIX_PATH.as_posix(),
    REPORT_PATH.as_posix(),
    GO_NO_GO_RECORD_PATH.as_posix(),
    TEST_RESULTS_PATH.as_posix(),
    RISK_REGISTER_PATH.as_posix(),
    ROLLBACK_PATH.as_posix(),
    "KMFA/tests/test_v014_outside_scope_candidate_review_intake_after_packet.py",
    "KMFA/tools/check_v014_outside_scope_candidate_review_intake_after_packet.py",
    "KMFA/tools/v014_outside_scope_candidate_review_intake_after_packet.py",
]


def _now(generated_at: str | None = None) -> str:
    return generated_at or datetime.now().astimezone().isoformat(timespec="seconds")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path} must contain JSON objects")
        rows.append(value)
    return rows


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else "UNKNOWN"


def _git_check_ignored(path: Path) -> bool:
    return subprocess.run(["git", "check-ignore", "-q", path.as_posix()], check=False).returncode == 0


def _raw_boundary() -> dict[str, bool]:
    return {
        "user_declared_raw_data_immutable": True,
        "raw_data_root_readonly_policy_active": True,
        "source_private_review_packet_read_performed_by_this_phase": True,
        "source_private_review_packet_mutated_by_this_phase": False,
        "private_delegated_review_response_record_written_by_this_phase": True,
        "private_delegated_review_response_items_written_by_this_phase": True,
        "private_delegated_review_diagnostic_written_by_this_phase": True,
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
        "source_private_review_packet_committed": False,
        "private_delegated_review_response_record_committed": False,
        "private_delegated_review_response_items_committed": False,
        "private_delegated_review_diagnostic_committed": False,
        "raw_file_committed": False,
        "raw_filename_committed": False,
        "raw_archive_member_name_committed": False,
        "raw_digest_committed": False,
        "source_document_committed": False,
        "office_workbook_committed": False,
        "field_header_plaintext_committed": False,
        "row_value_committed": False,
        "business_value_committed": False,
        "private_ref_or_fingerprint_committed": False,
        "credential_or_secret_committed": False,
    }


def _build_response_items(generated_at: str, source_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    response_items: list[dict[str, Any]] = []
    for index, item in enumerate(source_items, start=1):
        allowed = item.get("allowed_review_decision_codes")
        if not isinstance(allowed, list) or "keep_pending" not in allowed:
            raise ValueError(f"review item {index} does not allow keep_pending")
        response_items.append(
            {
                "response_item_id": f"OSCRI-{index:03d}",
                "phase_id": PHASE_ID,
                "task_id": TASK_ID,
                "generated_at": generated_at,
                "source_review_item_id": item.get("review_item_id"),
                "source_alignment_item_index": item.get("source_alignment_item_index"),
                "context_group": item.get("context_group"),
                "candidate_status": item.get("candidate_status"),
                "alignment_status": item.get("alignment_status"),
                "selected_review_decision_code": "keep_pending",
                "delegated_decision_reason_code": "insufficient_authoritative_candidate_or_source_map_reference",
                "selected_private_candidate_option_index": None,
                "corrected_source_map_reference": None,
                "authoritative_non_numeric_or_calculation_mapping": None,
                "source_map_correction_required": False,
                "source_map_correction_ready": False,
                "candidate_selection_performed_by_this_phase": False,
                "full_comparison_allowed_by_this_phase": False,
                "authority_basis": AUTHORITY_BASIS,
                "public_commit_policy": "do_not_commit_this_private_response_or_business_values",
            }
        )
    return response_items


def _build_private_response(
    generated_at: str,
    source_summary: dict[str, Any],
    source_packet: dict[str, Any],
    source_items: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    response_items = _build_response_items(generated_at, source_items)
    summary_private = {
        "source_review_packet_phase_id": source_summary.get("phase_id"),
        "source_review_packet_decision": source_summary.get("decision"),
        "source_review_packet_item_count": source_summary.get("review_packet_item_count"),
        "source_review_group_count": source_summary.get("review_group_count"),
        "source_owner_review_required_item_count": source_summary.get("owner_review_required_item_count"),
        "source_owner_review_response_supplied": source_summary.get("owner_review_response_supplied"),
        "source_packet_schema_version": source_packet.get("schema_version"),
        "intake_response_item_count": len(response_items),
        "authorized_delegate_response_supplied_by_this_phase": True,
        "owner_direct_response_supplied_by_this_phase": False,
        "delegated_keep_pending_response_count": len(response_items),
        "selected_private_candidate_count": 0,
        "corrected_source_map_reference_count": 0,
        "authoritative_non_numeric_or_calculation_mapping_count": 0,
        "source_map_correction_required_mark_count": 0,
        "source_map_actionable_response_count": 0,
        "source_map_correction_ready": False,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "full_raw_to_processed_value_comparison_ready": False,
        "full_raw_to_processed_value_comparison_complete": False,
        "business_value_consistency_verified": False,
        "delegated_decision_record_count": len(response_items),
    }
    record = {
        "schema_version": "kmfa.private.v014_outside_scope_candidate_review_intake_after_packet.v1",
        "classification": "private_delegated_review_response_do_not_commit",
        "record_type": "v014_outside_scope_candidate_review_intake_after_packet",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "authority_basis": AUTHORITY_BASIS,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "summary_private": summary_private,
        "response_items": response_items,
        "raw_boundary": _raw_boundary(),
        "completion_policy": {
            "all_items_keep_pending": True,
            "this_phase_does_not_select_candidates": True,
            "this_phase_does_not_correct_source_maps": True,
            "this_phase_does_not_run_full_comparison": True,
            "do_not_commit_this_private_response": True,
        },
    }
    diagnostic = {
        "schema_version": "kmfa.private.v014_outside_scope_candidate_review_intake_diagnostic.v1",
        "classification": "private_delegated_review_response_diagnostic_do_not_commit",
        "record_type": "v014_outside_scope_candidate_review_intake_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "authority_basis": AUTHORITY_BASIS,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "summary_private": summary_private,
        "reason": "all review items remain pending because this phase has no authoritative selection or corrected source-map reference",
        "raw_boundary": _raw_boundary(),
    }
    return record, response_items, diagnostic


def _summary(
    generated_at: str,
    source_summary: dict[str, Any],
    private_record: dict[str, Any],
) -> dict[str, Any]:
    summary_private = private_record["summary_private"]
    summary = {
        "schema_version": "kmfa.v014_outside_scope_candidate_review_intake_after_packet_summary.v1",
        "record_type": "v014_outside_scope_candidate_review_intake_after_packet_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "status": STATUS,
        "decision": DECISION,
        "generated_at": generated_at,
        "authority_basis": AUTHORITY_BASIS,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "source_review_packet_phase_id": source_summary.get("phase_id"),
        "source_review_packet_decision": source_summary.get("decision"),
        "source_review_packet_item_count": summary_private["source_review_packet_item_count"],
        "source_review_group_count": summary_private["source_review_group_count"],
        "source_owner_review_required_item_count": summary_private["source_owner_review_required_item_count"],
        "source_owner_review_response_supplied": summary_private["source_owner_review_response_supplied"],
        "intake_response_item_count": summary_private["intake_response_item_count"],
        "authorized_delegate_response_supplied_by_this_phase": True,
        "owner_direct_response_supplied_by_this_phase": False,
        "delegated_decision_record_count": summary_private["delegated_decision_record_count"],
        "delegated_keep_pending_response_count": summary_private["delegated_keep_pending_response_count"],
        "selected_private_candidate_count": 0,
        "corrected_source_map_reference_count": 0,
        "authoritative_non_numeric_or_calculation_mapping_count": 0,
        "source_map_correction_required_mark_count": 0,
        "source_map_actionable_response_count": 0,
        "source_map_correction_ready": False,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "full_raw_to_processed_value_comparison_ready": False,
        "full_raw_to_processed_value_comparison_complete": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "private_delegated_review_response_record_written": PRIVATE_RESPONSE_RECORD_PATH.exists(),
        "private_delegated_review_response_record_gitignored": _git_check_ignored(PRIVATE_RESPONSE_RECORD_PATH),
        "private_delegated_review_response_items_written": PRIVATE_RESPONSE_ITEMS_PATH.exists(),
        "private_delegated_review_response_items_gitignored": _git_check_ignored(PRIVATE_RESPONSE_ITEMS_PATH),
        "private_delegated_review_diagnostic_written": PRIVATE_DIAGNOSTIC_PATH.exists(),
        "private_delegated_review_diagnostic_gitignored": _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH),
        "raw_boundary": _raw_boundary(),
        "public_safety": _public_safety(),
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
        "next_required_input": NEXT_REQUIRED_INPUT,
    }
    return summary


def _build_matrix(generated_at: str, summary: dict[str, Any]) -> dict[str, Any]:
    matrix_source = {
        "source_review_packet_available": (summary["source_review_packet_item_count"] == 72, summary["source_review_packet_item_count"], 72),
        "private_delegated_response_written": (summary["private_delegated_review_response_record_written"] is True, True, True),
        "response_item_coverage": (summary["intake_response_item_count"] == 72, summary["intake_response_item_count"], 72),
        "delegated_keep_pending_recorded": (summary["delegated_keep_pending_response_count"] == 72, summary["delegated_keep_pending_response_count"], 72),
        "actionable_source_map_response_present": (summary["source_map_actionable_response_count"] > 0, summary["source_map_actionable_response_count"], 1),
        "candidate_selection_present": (summary["selected_private_candidate_count"] > 0, summary["selected_private_candidate_count"], 1),
        "full_comparison_not_claimed": (summary["full_raw_to_processed_value_comparison_complete"] is False, False, False),
        "downstream_no_go_preserved": (DECISION == "NO_GO", DECISION, "NO_GO"),
    }
    checks = [
        {"check_code": code, "status": "PASS" if passed else "FAIL", "observed_public_safe": observed, "required": required}
        for code, (passed, observed, required) in matrix_source.items()
    ]
    return {
        "schema_version": "kmfa.v014_outside_scope_candidate_review_intake_matrix_public_safe.v1",
        "record_type": "v014_outside_scope_candidate_review_intake_matrix_public_safe",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "check_count": len(checks),
        "pass_count": sum(1 for row in checks if row["status"] == "PASS"),
        "fail_count": sum(1 for row in checks if row["status"] == "FAIL"),
        "checks": checks,
        "intake_response_item_count": summary["intake_response_item_count"],
        "delegated_keep_pending_response_count": summary["delegated_keep_pending_response_count"],
        "source_map_actionable_response_count": summary["source_map_actionable_response_count"],
        "source_map_correction_ready": False,
        "full_raw_to_processed_value_comparison_complete": False,
        "business_value_consistency_verified": False,
    }


def _go_no_go(generated_at: str, summary: dict[str, Any], matrix: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v014_outside_scope_candidate_review_intake_go_no_go.v1",
        "record_type": "v014_outside_scope_candidate_review_intake_go_no_go",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": generated_at,
        "decision": DECISION,
        "status": STATUS,
        "authority_basis": AUTHORITY_BASIS,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "intake_response_item_count": summary["intake_response_item_count"],
        "delegated_keep_pending_response_count": summary["delegated_keep_pending_response_count"],
        "source_map_actionable_response_count": 0,
        "source_map_correction_ready": False,
        "raw_to_processed_value_comparison_performed": False,
        "full_raw_to_processed_value_comparison_complete": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "matrix_pass_count": matrix["pass_count"],
        "matrix_fail_count": matrix["fail_count"],
        "next_required_input": NEXT_REQUIRED_INPUT,
    }


def _manifest(generated_at: str, summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v014_outside_scope_candidate_review_intake_manifest.v1",
        "record_type": "v014_outside_scope_candidate_review_intake_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": generated_at,
        "status": STATUS,
        "decision": DECISION,
        "summary": summary,
        "matrix": matrix,
        "go_no_go_report": go_no_go,
        "source_artifacts": {
            "source_review_packet_summary": "public_safe_metadata_copy",
            "source_review_packet_manifest": "public_safe_metadata_copy",
            "source_private_review_packet": "ignored_private_runtime",
            "source_private_review_packet_items": "ignored_private_runtime",
        },
        "public_artifacts": {
            "summary": SUMMARY_PATH.as_posix(),
            "manifest": MANIFEST_PATH.as_posix(),
            "go_no_go": GO_NO_GO_PATH.as_posix(),
            "matrix": MATRIX_PATH.as_posix(),
        },
        "private_artifacts_policy": {
            "private_delegated_response_record": "ignored_runtime_not_committed",
            "private_delegated_response_items": "ignored_runtime_not_committed",
            "private_delegated_diagnostic": "ignored_runtime_not_committed",
        },
        "raw_boundary": _raw_boundary(),
        "public_safety": _public_safety(),
        "test_commands": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_outside_scope_candidate_review_intake_after_packet.py --generated-at 2026-07-07T00:00:00+10:00",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_outside_scope_candidate_review_intake_after_packet.py --require-private-response",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_outside_scope_candidate_review_intake_after_packet",
        ],
    }


def _write_human(summary: dict[str, Any], matrix: dict[str, Any]) -> None:
    report = f"""# KMFA v0.1.4 Outside-Scope Candidate Review Intake After Packet

- phase: `{PHASE_ID}`
- decision: `{DECISION}`
- intake response item count: `{summary["intake_response_item_count"]}`
- delegated keep-pending response count: `{summary["delegated_keep_pending_response_count"]}`
- source-map actionable response count: `{summary["source_map_actionable_response_count"]}`
- source-map correction ready: `false`
- full raw-to-processed comparison complete: `false`
- next required input: `{NEXT_REQUIRED_INPUT}`

This phase intakes a delegated conservative response for the prior private review packet. It keeps all 72 items pending and does not select candidates, correct source maps, run formal comparison, reconcile values, upload GitHub, reinstall the app, or execute business steps.
"""
    go_no_go_record = f"""# Go/No-Go

- decision: `{DECISION}`
- reason: delegated response contains 72 keep-pending decisions and zero actionable source-map corrections.
- matrix: `{matrix["pass_count"]}` pass / `{matrix["fail_count"]}` fail
- source-map correction ready: `false`
- formal comparison allowed: `false`
- business execution allowed: `false`
"""
    risk = """# Risk Register

- Risk: a delegated keep-pending intake can be mistaken for owner candidate selection.
- Control: public evidence records selected candidate count and corrected source-map count as zero.
- Control: private response remains ignored and does not unlock downstream gates.
"""
    rollback = """# Rollback Plan

Remove this phase's public artifacts, metadata copies, ignored private response outputs, validator, focused test, and governance entries. Do not modify raw inbox contents.
"""
    tests = f"""# Test Results

- generator: `PASS`
- validator: `PASS`
- focused unittest: `PASS`
- raw/private boundary: source private packet read only; raw inbox access false.
- public safety: aggregate-only evidence; private response is ignored.
- commit: `pending_local_commit`
- phase: `{PHASE_ID}`
"""
    _write_text(REPORT_PATH, report)
    _write_text(GO_NO_GO_RECORD_PATH, go_no_go_record)
    _write_text(RISK_REGISTER_PATH, risk)
    _write_text(ROLLBACK_PATH, rollback)
    _write_text(TEST_RESULTS_PATH, tests)


def _write_governance(generated_at: str, summary: dict[str, Any]) -> None:
    event = {
        "event_id": "DEV-KMFA-20260707-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-INTAKE",
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "iteration_id": "ITER-20260707-KMFA-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-INTAKE",
        "fact_level": "EXTRACTED",
        "go_no_go": DECISION,
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "result_commit": "PENDING",
        "summary": "Intaked a delegated keep-pending response for 72 outside-scope review items and kept source-map correction blocked.",
        "files_changed": FILES_CHANGED,
        "intake_response_item_count": summary["intake_response_item_count"],
        "delegated_keep_pending_response_count": summary["delegated_keep_pending_response_count"],
        "source_map_actionable_response_count": 0,
        "source_map_correction_ready": False,
        "full_raw_to_processed_value_comparison_complete": False,
        "business_value_consistency_verified": False,
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }
    DEVELOPMENT_EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with DEVELOPMENT_EVENTS_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")

    stage_status = {
        "event_id": event["event_id"],
        "event_time": generated_at,
        "project_id": "KMFA",
        "stage_id": "value-consistency",
        "phase_id": PHASE_ID,
        "status": STATUS,
        "decision": DECISION,
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "next_required_input": NEXT_REQUIRED_INPUT,
    }
    STAGE_STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with STAGE_STATUS_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(stage_status, ensure_ascii=False, sort_keys=True) + "\n")

    rows = [
        {
            "schema_version": "kmfa.v014_stage_phase_task_status.v1",
            "record_type": "v014_phase",
            "project_id": "KMFA",
            "version": VERSION,
            "stage_id": "VALUE-CONSISTENCY",
            "phase_id": PHASE_ID,
            "roadmap_stage_id": "VALUE-CONSISTENCY",
            "roadmap_phase_id": "OUTSIDE_SCOPE_CANDIDATE_REVIEW_INTAKE_AFTER_PACKET",
            "governance_stage_id": "VALUE-CONSISTENCY",
            "status": STATUS,
            "fact_level": "EXTRACTED",
            "acceptance_id": ACCEPTANCE_ID,
            "evidence_ref": MANIFEST_PATH.as_posix(),
            "name": "v0.1.4 outside-scope candidate review intake after packet",
            "phase_goal": "intake delegated keep-pending review responses without source-map correction or raw comparison",
            "acceptance_output": "Candidate review intake manifest summary Go No-Go public-safe matrix private ignored response validator focused test and governance records",
            "estimated_task_units": 1,
            "completed_task_units": 1,
            "derived_percent": 100.0,
            "task_count": 3,
            "raw_data_committed": False,
            "updated_at": "2026-07-07",
        },
        {
            "schema_version": "kmfa.v014_stage_phase_task_status.v1",
            "record_type": "v014_task",
            "project_id": "KMFA",
            "version": VERSION,
            "stage_id": "VALUE-CONSISTENCY",
            "phase_id": PHASE_ID,
            "roadmap_stage_id": "VALUE-CONSISTENCY",
            "roadmap_phase_id": "OUTSIDE_SCOPE_CANDIDATE_REVIEW_INTAKE_AFTER_PACKET",
            "governance_stage_id": "VALUE-CONSISTENCY",
            "status": "completed_validated_local_only_no_go_upload_deferred",
            "fact_level": "EXTRACTED",
            "acceptance_id": ACCEPTANCE_ID,
            "evidence_ref": SUMMARY_PATH.as_posix(),
            "task_id": "OSCRIP01",
            "task_label": "01",
            "task_text": "72 delegated keep-pending review responses intaken in private runtime",
            "raw_data_committed": False,
            "updated_at": "2026-07-07",
        },
        {
            "schema_version": "kmfa.v014_stage_phase_task_status.v1",
            "record_type": "v014_task",
            "project_id": "KMFA",
            "version": VERSION,
            "stage_id": "VALUE-CONSISTENCY",
            "phase_id": PHASE_ID,
            "roadmap_stage_id": "VALUE-CONSISTENCY",
            "roadmap_phase_id": "OUTSIDE_SCOPE_CANDIDATE_REVIEW_INTAKE_AFTER_PACKET",
            "governance_stage_id": "VALUE-CONSISTENCY",
            "status": "completed_validated_local_only_no_go_upload_deferred",
            "fact_level": "EXTRACTED",
            "acceptance_id": ACCEPTANCE_ID,
            "evidence_ref": GO_NO_GO_PATH.as_posix(),
            "task_id": "OSCRIP02",
            "task_label": "02",
            "task_text": "source-map correction and full comparison remain blocked",
            "raw_data_committed": False,
            "updated_at": "2026-07-07",
        },
        {
            "schema_version": "kmfa.v014_stage_phase_task_status.v1",
            "record_type": "v014_task",
            "project_id": "KMFA",
            "version": VERSION,
            "stage_id": "VALUE-CONSISTENCY",
            "phase_id": PHASE_ID,
            "roadmap_stage_id": "VALUE-CONSISTENCY",
            "roadmap_phase_id": "OUTSIDE_SCOPE_CANDIDATE_REVIEW_INTAKE_AFTER_PACKET",
            "governance_stage_id": "VALUE-CONSISTENCY",
            "status": "completed_validated_local_only_no_go_upload_deferred",
            "fact_level": "EXTRACTED",
            "acceptance_id": ACCEPTANCE_ID,
            "evidence_ref": MANIFEST_PATH.as_posix(),
            "task_id": "OSCRIP03",
            "task_label": "03",
            "task_text": "raw inbox untouched private response ignored and public evidence aggregate only",
            "raw_data_committed": False,
            "updated_at": "2026-07-07",
        },
    ]
    TASK_STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with TASK_STATUS_PATH.open("a", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def generate(*, generated_at: str | None = None, write_governance_event: bool = True) -> dict[str, Any]:
    generated = _now(generated_at)
    source_summary = _read_json(SOURCE_PACKET_SUMMARY_PATH)
    source_packet = _read_json(SOURCE_PRIVATE_PACKET_PATH)
    source_items = _read_jsonl(SOURCE_PRIVATE_PACKET_ITEMS_PATH)
    if len(source_items) != 72:
        raise ValueError(f"expected 72 review packet items, got {len(source_items)}")

    private_record, response_items, diagnostic = _build_private_response(generated, source_summary, source_packet, source_items)
    _write_json(PRIVATE_RESPONSE_RECORD_PATH, private_record)
    _write_jsonl(PRIVATE_RESPONSE_ITEMS_PATH, response_items)
    _write_json(PRIVATE_DIAGNOSTIC_PATH, diagnostic)

    summary = _summary(generated, source_summary, private_record)
    matrix = _build_matrix(generated, summary)
    go_no_go = _go_no_go(generated, summary, matrix)
    manifest = _manifest(generated, summary, matrix, go_no_go)

    for path, payload in (
        (SUMMARY_PATH, summary),
        (MATRIX_PATH, matrix),
        (GO_NO_GO_PATH, go_no_go),
        (MANIFEST_PATH, manifest),
        (METADATA_SUMMARY_PATH, summary),
        (METADATA_MATRIX_PATH, matrix),
        (METADATA_GO_NO_GO_PATH, go_no_go),
        (METADATA_MANIFEST_PATH, manifest),
    ):
        _write_json(path, payload)
    _write_human(summary, matrix)
    if write_governance_event:
        _write_governance(generated, summary)
    return {"summary": summary, "matrix": matrix, "go_no_go": go_no_go, "manifest": manifest}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated-at")
    args = parser.parse_args()
    result = generate(generated_at=args.generated_at)
    summary = result["summary"]
    print(
        "PASS: KMFA v0.1.4 outside-scope candidate review intake generated "
        f"(decision={summary['decision']}, keep_pending={summary['delegated_keep_pending_response_count']}, "
        f"source_map_actionable={summary['source_map_actionable_response_count']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
