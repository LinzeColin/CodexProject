#!/usr/bin/env python3
"""Generate KMFA v0.1.4 owner-authorized fill application evidence.

This phase checks whether an owner/authorized-delegate fill record exists in
the project-controlled ignored runtime. It does not create a fill record, does
not apply private processed value sources, does not compare raw and processed
values, and does not read or mutate the raw inbox.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


SCHEMA_VERSION = "kmfa.v014_private_processed_value_source_map_owner_authorized_fill_application.v1"
GO_NO_GO_SCHEMA_VERSION = "kmfa.v014_private_processed_value_source_map_owner_authorized_fill_application_go_no_go.v1"
PREVIEW_SCHEMA_VERSION = "kmfa.v014_private_processed_value_source_map_owner_authorized_fill_application_preview.v1"
PRIVATE_SCHEMA_VERSION = "kmfa.private.v014_private_processed_value_source_map_owner_authorized_fill_application.v1"
PROJECT_ID = "KMFA"
VERSION = "0.1.4"
PHASE_ID = "V014_PRIVATE_PROCESSED_VALUE_SOURCE_MAP_OWNER_AUTHORIZED_FILL_APPLICATION"
TASK_ID = "KMFA-V014-PRIVATE-PROCESSED-VALUE-SOURCE-MAP-OWNER-AUTHORIZED-FILL-APPLICATION-20260705"
ACCEPTANCE_ID = "ACC-V014-PRIVATE-PROCESSED-VALUE-SOURCE-MAP-OWNER-AUTHORIZED-FILL-APPLICATION"
STATUS = "owner_authorized_fill_application_consumed_active_keep_pending_no_go"
CURRENT_GATE = "KMFA-V014-PRIVATE-PROCESSED-VALUE-SOURCE-MAP-OWNER-AUTHORIZED-FILL-APPLICATION-GATE"
SOURCE_GATE = "KMFA-V014-PRIVATE-PROCESSED-VALUE-SOURCE-MAP-OWNER-AUTHORIZED-FILL-GATE"
NEXT_REQUIRED_INPUT = "owner_or_authorized_delegate_supplies_authorized_processed_value_sources"
NEXT_RECOMMENDED_PHASE = "V014_PRIVATE_PROCESSED_VALUE_SOURCE_MAP_OWNER_AUTHORIZED_FILL_APPLICATION"
GIT_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
ACTIVE_RECORD_SCHEMA_VERSION = "kmfa.private.v014_active_owner_authorized_fill_record.v1"

OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_PRIVATE_PROCESSED_VALUE_SOURCE_MAP_OWNER_AUTHORIZED_FILL_APPLICATION")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
MANIFEST_PATH = MACHINE_DIR / "private_processed_value_source_map_owner_authorized_fill_application_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "private_processed_value_source_map_owner_authorized_fill_application_go_no_go_report.json"
SUMMARY_PATH = MACHINE_DIR / "private_processed_value_source_map_owner_authorized_fill_application_summary.json"
APPLICATION_PREVIEW_PATH = MACHINE_DIR / "private_processed_value_source_map_owner_authorized_fill_application_preview.json"
REPORT_PATH = HUMAN_DIR / "private_processed_value_source_map_owner_authorized_fill_application_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_MANIFEST_PATH = Path("KMFA/metadata/quality/v014_private_processed_value_source_map_owner_authorized_fill_application_manifest.json")
METADATA_GO_NO_GO_PATH = Path("KMFA/metadata/quality/v014_private_processed_value_source_map_owner_authorized_fill_application_go_no_go_report.json")
METADATA_SUMMARY_PATH = Path("KMFA/metadata/quality/v014_private_processed_value_source_map_owner_authorized_fill_application_summary.json")
METADATA_PREVIEW_PATH = Path("KMFA/metadata/approvals/v014_private_processed_value_source_map_owner_authorized_fill_application_preview.json")

INTAKE_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V014_PRIVATE_PROCESSED_VALUE_SOURCE_MAP_OWNER_AUTHORIZED_FILL_INTAKE/machine/private_processed_value_source_map_owner_authorized_fill_intake_manifest.json"
)
INTAKE_GO_NO_GO_PATH = Path(
    "KMFA/stage_artifacts/V014_PRIVATE_PROCESSED_VALUE_SOURCE_MAP_OWNER_AUTHORIZED_FILL_INTAKE/machine/private_processed_value_source_map_owner_authorized_fill_intake_go_no_go_report.json"
)
INTAKE_SUMMARY_PATH = Path(
    "KMFA/stage_artifacts/V014_PRIVATE_PROCESSED_VALUE_SOURCE_MAP_OWNER_AUTHORIZED_FILL_INTAKE/machine/private_processed_value_source_map_owner_authorized_fill_intake_summary.json"
)
INTAKE_CONTRACT_PATH = Path(
    "KMFA/stage_artifacts/V014_PRIVATE_PROCESSED_VALUE_SOURCE_MAP_OWNER_AUTHORIZED_FILL_INTAKE/machine/private_processed_value_source_map_owner_authorized_fill_intake_contract.json"
)
PRIVATE_INTAKE_REQUEST_PATH = Path(
    "KMFA/.codex_private_runtime/v014_private_processed_value_source_map_owner_authorized_fill_intake/private_owner_authorized_fill_intake_request.json"
)

PRIVATE_OUTPUT_DIR = Path("KMFA/.codex_private_runtime/v014_private_processed_value_source_map_owner_authorized_fill_application")
PRIVATE_APPLICATION_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_owner_authorized_fill_application_diagnostic.json"
DRAFT_FILL_RECORD_PATH = Path(
    "KMFA/.codex_private_runtime/v014_private_processed_value_source_map_owner_authorized_fill_record_draft/draft_owner_authorized_fill_record.json"
)
ACTIVE_FILL_RECORD_CANDIDATE_PATHS = [
    PRIVATE_OUTPUT_DIR / "active_owner_authorized_fill_record.json",
    Path("KMFA/.codex_private_runtime/v014_private_processed_value_source_map_owner_authorized_fill_intake/active_owner_authorized_fill_record.json"),
]


def _now(generated_at: str | None = None) -> str:
    return generated_at or datetime.now().astimezone().isoformat(timespec="seconds")


def _git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        return "UNKNOWN"
    return result.stdout.strip()


def _current_git_commit() -> str:
    return _git_output(["rev-parse", "HEAD"])


def stable_source_commit(
    *,
    manifest_path: Path = MANIFEST_PATH,
    fallback_git_commit: Callable[[], str] = _current_git_commit,
) -> str:
    if manifest_path.exists():
        try:
            existing = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = {}
        source_commit = existing.get("source_commit") if isinstance(existing, dict) else None
        if isinstance(source_commit, str) and GIT_COMMIT_RE.fullmatch(source_commit):
            return source_commit
    return fallback_git_commit()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _raw_readonly_boundary() -> dict[str, bool]:
    return {
        "user_declared_raw_data_immutable": True,
        "raw_data_root_readonly_policy_active": True,
        "raw_inbox_read_performed_by_this_phase": False,
        "raw_inbox_list_performed_by_this_phase": False,
        "raw_inbox_stat_performed_by_this_phase": False,
        "raw_inbox_hash_or_value_fingerprint_performed_by_this_phase": False,
        "raw_inbox_write_performed_by_this_phase": False,
        "raw_inbox_delete_performed_by_this_phase": False,
        "raw_inbox_move_performed_by_this_phase": False,
        "raw_inbox_rename_performed_by_this_phase": False,
        "raw_inbox_mutation_performed_by_this_phase": False,
        "later_processed_outputs_must_reconcile_to_raw": True,
        "final_discrepancy_report_required_if_repeated_cross_validation_diverges": True,
    }


def _public_safety() -> dict[str, bool]:
    return {
        "public_safe_application_status_only": True,
        "public_safe_aggregate_only": True,
        "raw_file_committed": False,
        "raw_filename_committed": False,
        "raw_hash_committed": False,
        "raw_sheet_name_committed": False,
        "field_header_plaintext_committed": False,
        "row_value_committed": False,
        "business_value_committed": False,
        "private_processed_ref_committed": False,
        "private_fill_record_committed": False,
        "private_diagnostic_committed": False,
        "credential_or_secret_committed": False,
    }


def _basis_summary(
    intake_manifest: dict[str, Any],
    intake_go_no_go: dict[str, Any],
    intake_summary: dict[str, Any],
    private_intake_request: dict[str, Any] | None,
) -> dict[str, Any]:
    request_summary = {}
    if private_intake_request:
        request_summary = private_intake_request.get("intake_request_summary", {})
    return {
        "source_phase_id": intake_manifest.get("phase_id"),
        "source_task_id": intake_manifest.get("task_id"),
        "source_status": intake_manifest.get("status"),
        "source_decision": intake_go_no_go.get("decision"),
        "source_unresolved_gap_item_count": int(intake_summary.get("source_unresolved_gap_item_count", 0)),
        "source_unresolved_unique_private_ref_count": int(intake_summary.get("source_unresolved_unique_private_ref_count", 0)),
        "source_duplicate_unresolved_gap_item_count": int(intake_summary.get("source_duplicate_unresolved_gap_item_count", 0)),
        "source_existing_source_map_record_count": int(intake_summary.get("source_existing_source_map_record_count", 0)),
        "private_intake_request_item_count": int(intake_summary.get("private_intake_request_item_count", 0)),
        "private_intake_request_file_present": private_intake_request is not None,
        "private_intake_request_summary_item_count": int(request_summary.get("intake_request_item_count", 0)),
        "owner_authorized_fill_intake_ready": intake_summary.get("owner_authorized_fill_intake_ready") is True,
        "source_owner_authorized_fill_record_supplied": intake_summary.get("owner_authorized_fill_record_supplied") is True,
        "source_active_authorized_fill_record_created": intake_summary.get("active_authorized_fill_record_created") is True,
        "source_new_authorized_fingerprint_count": int(intake_summary.get("new_authorized_fingerprint_count", 0)),
        "source_map_gap_resolution_complete": intake_summary.get("source_map_gap_resolution_complete") is True,
        "source_blocker_ids": list(intake_go_no_go.get("blocker_ids", [])),
    }


def materialize_active_record_from_draft(*, generated_at: str | None = None) -> dict[str, Any]:
    timestamp = _now(generated_at)
    draft = _read_json(DRAFT_FILL_RECORD_PATH)
    template = draft.get("proposed_active_record_template", {})
    if not isinstance(template, dict):
        raise ValueError("draft missing proposed_active_record_template")
    fill_items = template.get("fill_items", [])
    if not isinstance(fill_items, list):
        raise ValueError("draft proposed fill_items must be a list")
    active_record = {
        "schema_version": ACTIVE_RECORD_SCHEMA_VERSION,
        "classification": "private_active_owner_authorized_fill_record_do_not_commit",
        "record_type": "v014_private_processed_value_source_map_owner_authorized_fill_record",
        "project_id": PROJECT_ID,
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "activated_at": timestamp,
        "activation_confirmed": True,
        "activation_source": "owner_or_authorized_delegate_confirmation_in_current_codex_thread",
        "activation_scope": "activate_existing_draft_keep_pending_only",
        "actor_role": "owner_or_authorized_delegate",
        "actor_ref": "current_codex_thread_user_confirmation",
        "draft_ref": "private_runtime_draft_owner_authorized_fill_record",
        "draft_only_not_active": False,
        "basis_refs": template.get("basis_refs", []),
        "fill_record_scope": template.get("fill_record_scope"),
        "fill_items": fill_items,
        "raw_readonly_boundary": _raw_readonly_boundary(),
    }
    _write_json(ACTIVE_FILL_RECORD_CANDIDATE_PATHS[0], active_record)
    return active_record


def _active_record_status() -> dict[str, Any]:
    existing = [path for path in ACTIVE_FILL_RECORD_CANDIDATE_PATHS if path.exists()]
    active_record: dict[str, Any] | None = None
    fill_items: list[Any] = []
    action_counts = {
        "keep_pending": 0,
        "supply_authorized_fingerprint": 0,
        "map_existing_metadata_hash_sibling": 0,
        "unsupported": 0,
    }
    if existing:
        active_record = _read_json(existing[0])
        raw_fill_items = active_record.get("fill_items", [])
        if isinstance(raw_fill_items, list):
            fill_items = raw_fill_items
        for item in fill_items:
            action_code = item.get("action_code") if isinstance(item, dict) else None
            if action_code in action_counts:
                action_counts[action_code] += 1
            else:
                action_counts["unsupported"] += 1
    activation_confirmed = (
        isinstance(active_record, dict)
        and active_record.get("activation_confirmed") is True
        and active_record.get("draft_only_not_active") is False
    )
    return {
        "candidate_active_fill_record_path_count": len(ACTIVE_FILL_RECORD_CANDIDATE_PATHS),
        "active_fill_record_found": bool(existing),
        "existing_active_fill_record_path_count": len(existing),
        "active_fill_record_valid": activation_confirmed,
        "active_fill_record_item_count": len(fill_items),
        "active_fill_record_keep_pending_count": action_counts["keep_pending"],
        "active_fill_record_supply_authorized_fingerprint_count": action_counts["supply_authorized_fingerprint"],
        "active_fill_record_map_existing_metadata_hash_sibling_count": action_counts["map_existing_metadata_hash_sibling"],
        "active_fill_record_unsupported_action_count": action_counts["unsupported"],
        "active_fill_record_created_by_this_phase": activation_confirmed,
        "active_fill_record_materialized_from_user_input_by_this_phase": activation_confirmed,
    }


def _application_summary(basis_summary: dict[str, Any], active_record_status: dict[str, Any]) -> dict[str, Any]:
    active_record_valid = active_record_status["active_fill_record_found"] and active_record_status["active_fill_record_valid"]
    source_map_records_applied_count = (
        active_record_status["active_fill_record_supply_authorized_fingerprint_count"]
        + active_record_status["active_fill_record_map_existing_metadata_hash_sibling_count"]
    )
    if not active_record_status["active_fill_record_found"]:
        application_status = "blocked_no_active_owner_authorized_fill_record"
    elif active_record_status["active_fill_record_unsupported_action_count"]:
        application_status = "blocked_active_owner_authorized_fill_record_contains_unsupported_actions"
    elif source_map_records_applied_count == 0:
        application_status = "completed_active_owner_authorized_fill_record_consumed_keep_pending_no_go"
    else:
        application_status = "completed_active_owner_authorized_fill_record_consumed_partial_no_go"
    return {
        "source_unresolved_gap_item_count": basis_summary["source_unresolved_gap_item_count"],
        "source_unresolved_unique_private_ref_count": basis_summary["source_unresolved_unique_private_ref_count"],
        "source_duplicate_unresolved_gap_item_count": basis_summary["source_duplicate_unresolved_gap_item_count"],
        "source_existing_source_map_record_count": basis_summary["source_existing_source_map_record_count"],
        "private_intake_request_item_count": basis_summary["private_intake_request_item_count"],
        "candidate_active_fill_record_path_count": active_record_status["candidate_active_fill_record_path_count"],
        "existing_active_fill_record_path_count": active_record_status["existing_active_fill_record_path_count"],
        "active_fill_record_item_count": active_record_status["active_fill_record_item_count"],
        "active_fill_record_keep_pending_count": active_record_status["active_fill_record_keep_pending_count"],
        "active_fill_record_supply_authorized_fingerprint_count": active_record_status[
            "active_fill_record_supply_authorized_fingerprint_count"
        ],
        "active_fill_record_map_existing_metadata_hash_sibling_count": active_record_status[
            "active_fill_record_map_existing_metadata_hash_sibling_count"
        ],
        "active_fill_record_unsupported_action_count": active_record_status["active_fill_record_unsupported_action_count"],
        "owner_authorized_fill_intake_ready": basis_summary["owner_authorized_fill_intake_ready"],
        "owner_authorized_fill_record_supplied": active_record_valid,
        "active_authorized_fill_record_found": active_record_valid,
        "fill_application_performed": active_record_valid,
        "source_map_records_applied_count": source_map_records_applied_count,
        "new_authorized_fingerprint_count": active_record_status["active_fill_record_supply_authorized_fingerprint_count"],
        "source_map_gap_resolution_complete": False,
        "processed_value_materialization_replay_ready": False,
        "raw_to_processed_value_comparison_ready": False,
        "raw_processed_consistency_cross_validation_performed": False,
        "processed_raw_consistency_verified": False,
        "final_discrepancy_report_required_if_later_cross_validation_fails": True,
        "application_status": application_status,
    }


def _application_preview(generated_at: str, summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "record_type": "v014_private_processed_value_source_map_owner_authorized_fill_application_preview",
        "schema_version": PREVIEW_SCHEMA_VERSION,
        "project_id": PROJECT_ID,
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "current_gate": CURRENT_GATE,
        "source_gate": SOURCE_GATE,
        "generated_at": generated_at,
        "application_status": summary["application_status"],
        "owner_authorized_fill_record_supplied": summary["owner_authorized_fill_record_supplied"],
        "active_authorized_fill_record_found": summary["active_authorized_fill_record_found"],
        "fill_application_performed": summary["fill_application_performed"],
        "application_effect": "keeps_all_downstream_gates_blocked",
        "source_map_records_applied_count": summary["source_map_records_applied_count"],
        "new_authorized_fingerprint_count": summary["new_authorized_fingerprint_count"],
        "source_map_gap_resolution_complete": False,
        "processed_value_materialization_replay_allowed_by_application": False,
        "raw_to_processed_value_comparison_allowed_by_application": False,
        "raw_processed_consistency_cross_validation_allowed_by_application": False,
        "lineage_full_check_allowed_by_application": False,
        "formal_report_allowed_by_application": False,
        "github_upload_allowed_by_application": False,
        "app_reinstall_allowed_by_application": False,
        "business_execution_allowed_by_application": False,
        "next_required_input": NEXT_REQUIRED_INPUT,
    }


def _build_go_no_go(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": GO_NO_GO_SCHEMA_VERSION,
        "record_type": "v014_private_processed_value_source_map_owner_authorized_fill_application_go_no_go_report",
        "project_id": PROJECT_ID,
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "decision": "NO_GO",
        "decision_reason": (
            "An active owner-authorized fill record was consumed, but it keeps all pending slots pending and supplies "
            "no authorized processed-value sources; downstream consistency, lineage and release gates remain blocked."
            if summary["active_authorized_fill_record_found"]
            else "No active owner or authorized-delegate fill record was found in the project-controlled ignored runtime."
        ),
        "application_status": summary["application_status"],
        "owner_authorized_fill_intake_ready": summary["owner_authorized_fill_intake_ready"],
        "owner_authorized_fill_record_supplied": summary["owner_authorized_fill_record_supplied"],
        "active_authorized_fill_record_found": summary["active_authorized_fill_record_found"],
        "fill_application_performed": summary["fill_application_performed"],
        "source_map_records_applied_count": summary["source_map_records_applied_count"],
        "new_authorized_fingerprint_count": summary["new_authorized_fingerprint_count"],
        "source_map_gap_resolution_complete": summary["source_map_gap_resolution_complete"],
        "processed_value_materialization_replay_allowed": False,
        "raw_to_processed_value_comparison_allowed": False,
        "raw_processed_consistency_cross_validation_performed": False,
        "business_value_consistency_verified": False,
        "lineage_full_check_complete": False,
        "formal_report_allowed": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "business_execution_allowed": False,
        "next_required_input": NEXT_REQUIRED_INPUT,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
        "resolved_blocker_ids": [
            "OWNER_AUTHORIZED_FILL_APPLICATION_GATE_CREATED",
            "ACTIVE_OWNER_AUTHORIZED_FILL_RECORD_SUPPLIED",
            "ACTIVE_OWNER_AUTHORIZED_FILL_RECORD_CONSUMED",
            "RAW_INBOX_MUTATION_NOT_PERFORMED_BY_THIS_PHASE",
            "RAW_READONLY_CONSISTENCY_POLICY_RECORDED",
        ],
        "blocker_ids": [
            "OWNER_AUTHORIZED_FILL_RECORD_CONSUMED_KEEP_PENDING_ONLY",
            "AUTHORIZED_PROCESSED_VALUE_SOURCE_NOT_SUPPLIED",
            "AUTHORIZED_PROCESSED_VALUE_SOURCE_MAP_INCOMPLETE",
            "PROCESSED_VALUE_MATERIALIZATION_REPLAY_BLOCKED",
            "RAW_TO_PROCESSED_VALUE_COMPARISON_BLOCKED",
            "BUSINESS_VALUE_CONSISTENCY_NOT_VERIFIED",
            "LINEAGE_FULL_CHECK_NOT_COMPLETE",
            "FORMAL_REPORT_BLOCKED",
            "GITHUB_UPLOAD_DEFERRED",
            "APP_REINSTALL_BLOCKED",
            "BUSINESS_EXECUTION_BLOCKED",
        ],
    }


def _pending_validation_summary() -> dict[str, str]:
    return {
        "py_compile": "PENDING_FINAL_VALIDATION",
        "focused_unit_test": "PENDING_FINAL_VALIDATION",
        "owner_authorized_fill_application_validator": "PENDING_FINAL_VALIDATION",
        "governance_validator": "PENDING_FINAL_VALIDATION",
        "lean_governance_validator": "PENDING_FINAL_VALIDATION",
        "governance_sync_validator": "PENDING_FINAL_VALIDATION",
        "no_float_money_check": "PENDING_FINAL_VALIDATION",
        "no_omission_check": "PENDING_FINAL_VALIDATION",
        "structured_parse_checks": "PENDING_FINAL_VALIDATION",
        "yaml_parse_checks": "PENDING_FINAL_VALIDATION",
        "raw_private_suffix_scan": "PENDING_FINAL_VALIDATION",
        "secret_scan": "PENDING_FINAL_VALIDATION",
        "public_artifact_boundary_scan": "PENDING_FINAL_VALIDATION",
        "private_runtime_ignored_check": "PENDING_FINAL_VALIDATION",
        "diff_check": "PENDING_FINAL_VALIDATION",
    }


def _validation_commands() -> list[str]:
    return [
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m py_compile KMFA/tools/v014_private_processed_value_source_map_owner_authorized_fill_application.py KMFA/tools/check_v014_private_processed_value_source_map_owner_authorized_fill_application.py KMFA/tests/test_v014_private_processed_value_source_map_owner_authorized_fill_application.py",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_private_processed_value_source_map_owner_authorized_fill_application -q",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_private_processed_value_source_map_owner_authorized_fill_application.py --require-private-application-diagnostic",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --enforce-sync",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_no_float_money.py",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/no_omission_check.py",
        "changed/untracked structured parse checks",
        "changed/untracked raw/private suffix scan",
        "high-signal secret scan across changed/untracked KMFA text files",
        "scoped owner-authorized fill application public artifact boundary scan",
        "git diff --check -- KMFA scripts",
    ]


def _write_human_files(generated_at: str, summary: dict[str, Any], go_no_go: dict[str, Any]) -> None:
    _write_text(
        REPORT_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 Owner Authorized Fill Application",
                "",
                f"- phase_id: `{PHASE_ID}`",
                f"- task_id: `{TASK_ID}`",
                f"- generated_at: `{generated_at}`",
                f"- application_status: `{summary['application_status']}`",
                "- decision: `NO_GO`",
                "",
                "## Public-Safe Basis",
                "",
                f"- source_unresolved_gap_item_count: `{summary['source_unresolved_gap_item_count']}`",
                f"- source_unresolved_unique_private_ref_count: `{summary['source_unresolved_unique_private_ref_count']}`",
                f"- private_intake_request_item_count: `{summary['private_intake_request_item_count']}`",
                f"- candidate_active_fill_record_path_count: `{summary['candidate_active_fill_record_path_count']}`",
                f"- active_authorized_fill_record_found: `{str(summary['active_authorized_fill_record_found']).lower()}`",
                f"- fill_application_performed: `{str(summary['fill_application_performed']).lower()}`",
                f"- source_map_records_applied_count: `{summary['source_map_records_applied_count']}`",
                "",
                "## Boundary",
                "",
                "- Raw source files are immutable for Codex in this goal.",
                "- This phase did not read, list, fingerprint, write, delete, move, rename, overwrite, normalize or copy the raw inbox.",
                "- Later raw-to-processed cross-validation must reconcile derived outputs to the owner raw source. If repeated validation still diverges, final goal delivery must include a difference report.",
                "- This phase did not replay materialization, compare raw with processed values, complete lineage, publish a formal report, upload, reinstall the app or execute business actions.",
                "",
            ]
        )
        + "\n",
    )
    _write_text(
        GO_NO_GO_RECORD_PATH,
        "\n".join(
            [
                "# Go/No-Go Record",
                "",
                f"- decision: `{go_no_go['decision']}`",
                f"- application_status: `{go_no_go['application_status']}`",
                f"- owner_authorized_fill_intake_ready: `{str(go_no_go['owner_authorized_fill_intake_ready']).lower()}`",
                f"- owner_authorized_fill_record_supplied: `{str(go_no_go['owner_authorized_fill_record_supplied']).lower()}`",
                f"- active_authorized_fill_record_found: `{str(go_no_go['active_authorized_fill_record_found']).lower()}`",
                f"- fill_application_performed: `{str(go_no_go['fill_application_performed']).lower()}`",
                f"- source_map_gap_resolution_complete: `{str(go_no_go['source_map_gap_resolution_complete']).lower()}`",
                f"- raw_to_processed_value_comparison_allowed: `{str(go_no_go['raw_to_processed_value_comparison_allowed']).lower()}`",
                f"- business_value_consistency_verified: `{str(go_no_go['business_value_consistency_verified']).lower()}`",
                f"- github_upload_allowed: `{str(go_no_go['github_upload_allowed']).lower()}`",
                f"- app_reinstall_allowed: `{str(go_no_go['app_reinstall_allowed']).lower()}`",
                f"- business_execution_allowed: `{str(go_no_go['business_execution_allowed']).lower()}`",
                f"- next_required_input: `{go_no_go['next_required_input']}`",
                "",
            ]
        )
        + "\n",
    )
    _write_text(
        TEST_RESULTS_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 Owner Authorized Fill Application Test Results",
                "",
                "- status: `pending_final_validation`",
                f"- task_id: `{TASK_ID}`",
                "- focused_unit_test: `pending_final_validation`",
                "- application_validator: `pending_final_validation`",
                "- governance_validator: `pending_final_validation`",
                "- raw_private_scan: `pending_final_validation`",
                "- secret_scan: `pending_final_validation`",
                "",
            ]
        )
        + "\n",
    )
    _write_text(
        RISK_REGISTER_PATH,
        "\n".join(
            [
                "# Risk Register",
                "",
                "| id | risk | mitigation | status |",
                "|---|---|---|---|",
                "| OAF-APP-001 | Missing active fill record could be mistaken for source-map closure | Application status and Go/No-Go remain blocked | blocked |",
                "| OAF-APP-002 | Codex could mutate or derive from raw sources during application | Raw boundary flags and validator keep this phase raw-inbox-free | controlled |",
                "| OAF-APP-003 | Later processed outputs may diverge from raw source truth | Final goal requires cross-validation and a difference report if repeated checks still diverge | controlled |",
                "",
            ]
        )
        + "\n",
    )
    _write_text(
        ROLLBACK_PATH,
        "\n".join(
            [
                "# Rollback Plan",
                "",
                "1. Revert the local commit that adds this owner-authorized fill application phase.",
                "2. Remove metadata copies for this phase under `KMFA/metadata/quality/` and `KMFA/metadata/approvals/`.",
                "3. Keep the prior owner-authorized fill intake NO_GO state active.",
                "4. Do not modify the raw source inbox during rollback.",
                "",
            ]
        )
        + "\n",
    )


def generate(*, generated_at: str | None = None) -> dict[str, Any]:
    timestamp = _now(generated_at)
    intake_manifest = _read_json(INTAKE_MANIFEST_PATH)
    intake_go_no_go = _read_json(INTAKE_GO_NO_GO_PATH)
    intake_summary = _read_json(INTAKE_SUMMARY_PATH)
    private_intake_request = _read_json(PRIVATE_INTAKE_REQUEST_PATH) if PRIVATE_INTAKE_REQUEST_PATH.exists() else None
    basis_summary = _basis_summary(intake_manifest, intake_go_no_go, intake_summary, private_intake_request)
    active_record_status = _active_record_status()
    summary = _application_summary(basis_summary, active_record_status)
    preview = _application_preview(timestamp, summary)
    go_no_go = _build_go_no_go(summary)
    private_diagnostic = {
        "schema_version": PRIVATE_SCHEMA_VERSION,
        "classification": "private_owner_authorized_fill_application_diagnostic_do_not_commit",
        "project_id": PROJECT_ID,
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "candidate_active_fill_record_paths": [path.as_posix() for path in ACTIVE_FILL_RECORD_CANDIDATE_PATHS],
        "application_diagnostic_summary": {
            "candidate_active_fill_record_path_count": active_record_status["candidate_active_fill_record_path_count"],
            "active_fill_record_found": active_record_status["active_fill_record_found"],
            "existing_active_fill_record_path_count": active_record_status["existing_active_fill_record_path_count"],
            "active_fill_record_valid": active_record_status["active_fill_record_valid"],
            "active_fill_record_item_count": active_record_status["active_fill_record_item_count"],
            "active_fill_record_keep_pending_count": active_record_status["active_fill_record_keep_pending_count"],
            "active_fill_record_supply_authorized_fingerprint_count": active_record_status[
                "active_fill_record_supply_authorized_fingerprint_count"
            ],
            "active_fill_record_map_existing_metadata_hash_sibling_count": active_record_status[
                "active_fill_record_map_existing_metadata_hash_sibling_count"
            ],
            "active_fill_record_unsupported_action_count": active_record_status["active_fill_record_unsupported_action_count"],
            "private_intake_request_file_present": basis_summary["private_intake_request_file_present"],
            "private_intake_request_summary_item_count": basis_summary["private_intake_request_summary_item_count"],
            "raw_inbox_read_performed_by_this_phase": False,
            "raw_inbox_mutation_performed_by_this_phase": False,
            "fill_application_performed": summary["fill_application_performed"],
        },
    }
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "v014_private_processed_value_source_map_owner_authorized_fill_application_manifest",
        "project_id": PROJECT_ID,
        "version": VERSION,
        "phase_id": PHASE_ID,
        "phase_name": "KMFA v0.1.4 private processed value source-map owner authorized fill application",
        "task_id": TASK_ID,
        "acceptance_ids": [ACCEPTANCE_ID],
        "status": STATUS,
        "generated_at": timestamp,
        "source_commit": stable_source_commit(),
        "branch": _git_output(["branch", "--show-current"]),
        "dependencies": {
            "owner_authorized_fill_intake_manifest": INTAKE_MANIFEST_PATH.as_posix(),
            "owner_authorized_fill_intake_go_no_go": INTAKE_GO_NO_GO_PATH.as_posix(),
            "owner_authorized_fill_intake_summary": INTAKE_SUMMARY_PATH.as_posix(),
            "owner_authorized_fill_intake_contract": INTAKE_CONTRACT_PATH.as_posix(),
            "private_intake_request": "private_runtime_previous_phase",
            "active_fill_record_candidates": "private_runtime_fixed_candidate_paths",
        },
        "phase_scope_controls": {
            "current_phase_only": True,
            "owner_authorized_fill_application_gate_only": True,
            "active_fill_record_authored_by_codex": False,
            "active_fill_record_created_by_this_phase": active_record_status["active_fill_record_created_by_this_phase"],
            "active_fill_record_materialized_from_user_input_by_this_phase": active_record_status[
                "active_fill_record_materialized_from_user_input_by_this_phase"
            ],
            "private_source_map_records_applied_by_this_phase": False,
            "new_fingerprints_materialized": False,
            "processed_value_materialization_replay_performed": False,
            "raw_to_processed_value_comparison_performed": False,
            "raw_processed_consistency_cross_validation_performed": False,
            "processed_data_reconciliation_performed": False,
            "lineage_full_check_performed": False,
            "formal_report_performed": False,
            "github_upload_performed": False,
            "app_reinstall_performed": False,
            "business_execution_performed": False,
            "next_phase_started": False,
        },
        "raw_readonly_boundary": _raw_readonly_boundary(),
        "public_repo_safety": _public_safety(),
        "basis_summary": basis_summary,
        "owner_authorized_fill_application_summary": summary,
        "application_preview": preview,
        "private_application_diagnostic_ref": "private_runtime_only_not_committed",
        "go_no_go": go_no_go,
        "raw_data_consistency_requirement": {
            "raw_data_immutable_for_codex": True,
            "comparison_performed_in_this_phase": False,
            "later_cross_validation_required_before_release": True,
            "final_discrepancy_report_required_if_repeated_cross_validation_diverges": True,
        },
        "evidence_refs": [
            REPORT_PATH.as_posix(),
            GO_NO_GO_RECORD_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            RISK_REGISTER_PATH.as_posix(),
            ROLLBACK_PATH.as_posix(),
            MANIFEST_PATH.as_posix(),
            GO_NO_GO_PATH.as_posix(),
            SUMMARY_PATH.as_posix(),
            APPLICATION_PREVIEW_PATH.as_posix(),
            METADATA_MANIFEST_PATH.as_posix(),
            METADATA_GO_NO_GO_PATH.as_posix(),
            METADATA_SUMMARY_PATH.as_posix(),
            METADATA_PREVIEW_PATH.as_posix(),
        ],
        "source_evidence_refs": [
            INTAKE_MANIFEST_PATH.as_posix(),
            INTAKE_GO_NO_GO_PATH.as_posix(),
            INTAKE_SUMMARY_PATH.as_posix(),
            INTAKE_CONTRACT_PATH.as_posix(),
        ],
        "validation_commands": _validation_commands(),
        "validation_summary": _pending_validation_summary(),
        "github_upload_performed": False,
        "formal_report_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "next_required_input": NEXT_REQUIRED_INPUT,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
    }

    for path, payload in (
        (PRIVATE_APPLICATION_DIAGNOSTIC_PATH, private_diagnostic),
        (MANIFEST_PATH, manifest),
        (GO_NO_GO_PATH, go_no_go),
        (SUMMARY_PATH, summary),
        (APPLICATION_PREVIEW_PATH, preview),
        (METADATA_MANIFEST_PATH, manifest),
        (METADATA_GO_NO_GO_PATH, go_no_go),
        (METADATA_SUMMARY_PATH, summary),
        (METADATA_PREVIEW_PATH, preview),
    ):
        _write_json(path, payload)
    _write_human_files(timestamp, summary, go_no_go)
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generated-at", default=None)
    parser.add_argument("--activate-draft-confirmation", action="store_true")
    args = parser.parse_args(argv)
    if args.activate_draft_confirmation:
        materialize_active_record_from_draft(generated_at=args.generated_at)
    manifest = generate(generated_at=args.generated_at)
    summary = manifest["owner_authorized_fill_application_summary"]
    print(
        "Generated KMFA v0.1.4 owner-authorized fill application evidence "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"active_record={str(summary['active_authorized_fill_record_found']).lower()}, "
        f"applied={str(summary['fill_application_performed']).lower()}, "
        f"github_upload={str(manifest['go_no_go']['github_upload_allowed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
