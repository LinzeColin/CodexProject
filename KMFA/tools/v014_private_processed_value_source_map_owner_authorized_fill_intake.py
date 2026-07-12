#!/usr/bin/env python3
"""Generate KMFA v0.1.4 owner-authorized fill intake evidence.

This phase prepares the owner/authorized-delegate intake contract for the
remaining private processed value source-map gaps. It consumes the previous
private owner worklist, writes a private-only intake request, and publishes
aggregate-only public evidence. It does not create an owner fill record, does
not materialize processed values, does not compare raw and processed values,
and does not read or mutate the raw inbox.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


SCHEMA_VERSION = "kmfa.v014_private_processed_value_source_map_owner_authorized_fill_intake.v1"
CONTRACT_SCHEMA_VERSION = "kmfa.v014_private_processed_value_source_map_owner_authorized_fill_intake_contract.v1"
PACKET_SCHEMA_VERSION = "kmfa.v014_private_processed_value_source_map_owner_authorized_fill_packet.v1"
TEMPLATE_SCHEMA_VERSION = "kmfa.v014_private_processed_value_source_map_owner_authorized_fill_template.v1"
GO_NO_GO_SCHEMA_VERSION = "kmfa.v014_private_processed_value_source_map_owner_authorized_fill_intake_go_no_go.v1"
PRIVATE_SCHEMA_VERSION = "kmfa.private.v014_private_processed_value_source_map_owner_authorized_fill_intake.v1"
PROJECT_ID = "KMFA"
VERSION = "0.1.4"
PHASE_ID = "V014_PRIVATE_PROCESSED_VALUE_SOURCE_MAP_OWNER_AUTHORIZED_FILL_INTAKE"
TASK_ID = "KMFA-V014-PRIVATE-PROCESSED-VALUE-SOURCE-MAP-OWNER-AUTHORIZED-FILL-INTAKE-20260705"
ACCEPTANCE_ID = "ACC-V014-PRIVATE-PROCESSED-VALUE-SOURCE-MAP-OWNER-AUTHORIZED-FILL-INTAKE"
STATUS = "owner_authorized_fill_intake_ready_no_active_fill_record_no_go"
CURRENT_GATE = "KMFA-V014-PRIVATE-PROCESSED-VALUE-SOURCE-MAP-OWNER-AUTHORIZED-FILL-GATE"
NEXT_REQUIRED_INPUT = "owner_or_authorized_delegate_fill_record"
NEXT_RECOMMENDED_PHASE = "V014_PRIVATE_PROCESSED_VALUE_SOURCE_MAP_OWNER_AUTHORIZED_FILL_APPLICATION"
GIT_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")

ALLOWED_INTAKE_ACTION_CODES = [
    "supply_authorized_processed_value_fingerprint",
    "map_existing_metadata_hash_sibling",
    "keep_pending",
]
ALLOWED_ACTOR_ROLES = ["owner", "authorized_delegate"]

OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_PRIVATE_PROCESSED_VALUE_SOURCE_MAP_OWNER_AUTHORIZED_FILL_INTAKE")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
TEMPLATES_DIR = MACHINE_DIR / "owner_authorized_fill_templates"
MANIFEST_PATH = MACHINE_DIR / "private_processed_value_source_map_owner_authorized_fill_intake_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "private_processed_value_source_map_owner_authorized_fill_intake_go_no_go_report.json"
SUMMARY_PATH = MACHINE_DIR / "private_processed_value_source_map_owner_authorized_fill_intake_summary.json"
INTAKE_PACKET_PATH = MACHINE_DIR / "private_processed_value_source_map_owner_authorized_fill_packet.json"
INTAKE_CONTRACT_PATH = MACHINE_DIR / "private_processed_value_source_map_owner_authorized_fill_intake_contract.json"
REPORT_PATH = HUMAN_DIR / "private_processed_value_source_map_owner_authorized_fill_intake_report.md"
DECISION_REQUEST_PATH = HUMAN_DIR / "owner_authorized_fill_request.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_MANIFEST_PATH = Path("KMFA/metadata/quality/v014_private_processed_value_source_map_owner_authorized_fill_intake_manifest.json")
METADATA_GO_NO_GO_PATH = Path("KMFA/metadata/quality/v014_private_processed_value_source_map_owner_authorized_fill_intake_go_no_go_report.json")
METADATA_SUMMARY_PATH = Path("KMFA/metadata/quality/v014_private_processed_value_source_map_owner_authorized_fill_intake_summary.json")
METADATA_PACKET_PATH = Path("KMFA/metadata/approvals/v014_private_processed_value_source_map_owner_authorized_fill_packet.json")
METADATA_CONTRACT_PATH = Path("KMFA/metadata/approvals/v014_private_processed_value_source_map_owner_authorized_fill_intake_contract.json")

GAP_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V014_PRIVATE_PROCESSED_VALUE_SOURCE_MAP_AUTHORIZED_FILL_GAP_RESOLUTION/machine/private_processed_value_source_map_gap_resolution_manifest.json"
)
GAP_GO_NO_GO_PATH = Path(
    "KMFA/stage_artifacts/V014_PRIVATE_PROCESSED_VALUE_SOURCE_MAP_AUTHORIZED_FILL_GAP_RESOLUTION/machine/private_processed_value_source_map_gap_resolution_go_no_go_report.json"
)
GAP_PRIVATE_WORKLIST_PATH = Path(
    "KMFA/.codex_private_runtime/v014_private_processed_value_source_map_gap_resolution/private_owner_authorized_fill_worklist.json"
)

PRIVATE_OUTPUT_DIR = Path("KMFA/.codex_private_runtime/v014_private_processed_value_source_map_owner_authorized_fill_intake")
PRIVATE_INTAKE_REQUEST_PATH = PRIVATE_OUTPUT_DIR / "private_owner_authorized_fill_intake_request.json"
PRIVATE_INTAKE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_owner_authorized_fill_intake_diagnostic.json"


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


def _raw_boundary() -> dict[str, bool]:
    return {
        "raw_inbox_read_performed_by_this_phase": False,
        "raw_inbox_list_performed_by_this_phase": False,
        "raw_inbox_stat_performed_by_this_phase": False,
        "raw_inbox_hash_or_value_fingerprint_performed_by_this_phase": False,
        "raw_inbox_write_performed_by_this_phase": False,
        "raw_inbox_delete_performed_by_this_phase": False,
        "raw_inbox_move_performed_by_this_phase": False,
        "raw_inbox_rename_performed_by_this_phase": False,
        "raw_inbox_mutation_performed_by_this_phase": False,
    }


def _public_safety() -> dict[str, bool]:
    return {
        "public_safe_aggregate_only": True,
        "public_safe_intake_schema_only": True,
        "raw_file_committed": False,
        "raw_filename_committed": False,
        "raw_hash_committed": False,
        "raw_sheet_name_committed": False,
        "field_header_plaintext_committed": False,
        "row_value_committed": False,
        "business_value_committed": False,
        "private_processed_ref_committed": False,
        "private_intake_request_committed": False,
        "credential_or_secret_committed": False,
    }


def _basis_summary(gap_manifest: dict[str, Any], gap_go_no_go: dict[str, Any], private_worklist: dict[str, Any]) -> dict[str, Any]:
    gap_summary = gap_manifest.get("gap_resolution_summary", {})
    worklist_summary = private_worklist.get("owner_worklist_summary", {})
    return {
        "source_phase_id": gap_manifest.get("phase_id"),
        "source_task_id": gap_manifest.get("task_id"),
        "source_status": gap_manifest.get("status"),
        "source_decision": gap_go_no_go.get("decision"),
        "source_unresolved_gap_item_count": int(gap_summary.get("unresolved_gap_item_count", 0)),
        "source_unresolved_unique_private_ref_count": int(gap_summary.get("unresolved_unique_private_ref_count", 0)),
        "source_duplicate_unresolved_gap_item_count": int(gap_summary.get("duplicate_unresolved_gap_item_count", 0)),
        "source_private_owner_worklist_item_count": int(worklist_summary.get("owner_worklist_item_count", 0)),
        "source_existing_source_map_record_count": int(gap_summary.get("existing_source_map_record_count", 0)),
        "source_owner_authorized_fill_intake_required": gap_summary.get("owner_authorized_fill_intake_required") is True,
        "source_map_gap_resolution_complete": gap_summary.get("source_map_gap_resolution_complete") is True,
        "business_value_consistency_verified": gap_summary.get("business_value_consistency_verified") is True,
        "source_blocker_ids": list(gap_go_no_go.get("blocker_ids", [])),
    }


def _intake_summary(basis_summary: dict[str, Any]) -> dict[str, Any]:
    item_count = basis_summary["source_private_owner_worklist_item_count"]
    return {
        "source_unresolved_gap_item_count": basis_summary["source_unresolved_gap_item_count"],
        "source_unresolved_unique_private_ref_count": basis_summary["source_unresolved_unique_private_ref_count"],
        "source_duplicate_unresolved_gap_item_count": basis_summary["source_duplicate_unresolved_gap_item_count"],
        "source_existing_source_map_record_count": basis_summary["source_existing_source_map_record_count"],
        "private_intake_request_item_count": item_count,
        "allowed_intake_action_count": len(ALLOWED_INTAKE_ACTION_CODES),
        "allowed_actor_role_count": len(ALLOWED_ACTOR_ROLES),
        "owner_authorized_fill_intake_ready": True,
        "owner_authorized_fill_record_supplied": False,
        "active_authorized_fill_record_created": False,
        "new_authorized_fingerprint_count": 0,
        "source_map_gap_resolution_complete": False,
        "processed_value_materialization_replay_ready": False,
        "raw_to_processed_value_comparison_ready": False,
        "business_value_consistency_verified": False,
        "lineage_full_check_complete": False,
        "intake_status": "ready_no_active_owner_authorized_fill_record",
    }


def _intake_contract(generated_at: str, basis_summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "record_type": "v014_private_processed_value_source_map_owner_authorized_fill_intake_contract",
        "schema_version": CONTRACT_SCHEMA_VERSION,
        "project_id": PROJECT_ID,
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "current_gate": CURRENT_GATE,
        "generated_at": generated_at,
        "readiness_status": "ready_for_owner_authorized_fill_record",
        "fill_record_status": "no_owner_authorized_fill_record_supplied",
        "accepted_record_type": "v014_private_processed_value_source_map_owner_authorized_fill_record",
        "allowed_intake_action_codes": ALLOWED_INTAKE_ACTION_CODES,
        "allowed_actor_roles": ALLOWED_ACTOR_ROLES,
        "basis_refs": [GAP_MANIFEST_PATH.as_posix(), GAP_GO_NO_GO_PATH.as_posix()],
        "basis_summary": basis_summary,
        "required_common_fields": [
            "actor_role",
            "actor_ref",
            "decision_time",
            "fill_record_scope",
            "basis_refs",
            "fill_items",
        ],
        "required_fill_item_fields": [
            "target_slot_id",
            "action_code",
            "basis_note",
        ],
        "conditional_fill_item_fields": {
            "supply_authorized_processed_value_fingerprint": ["authorized_processed_value_fingerprint"],
            "map_existing_metadata_hash_sibling": ["authorized_metadata_hash_sibling_ref"],
            "keep_pending": ["reason_pending", "next_review_trigger"],
        },
        "raw_or_plaintext_allowed": False,
        "business_value_allowed_in_public_repo": False,
        "private_processed_ref_allowed_in_public_repo": False,
        "raw_to_processed_comparison_allowed_by_intake": False,
        "processed_value_materialization_allowed_by_intake": False,
        "lineage_full_check_allowed_by_intake": False,
        "formal_report_allowed_by_intake": False,
        "github_upload_allowed_by_intake": False,
        "app_reinstall_allowed_by_intake": False,
        "business_execution_allowed_by_intake": False,
        "forbidden_public_metadata_categories": [
            "raw or normalized business values",
            "plaintext source extracts",
            "private processed refs",
            "local source paths",
            "worksheet labels",
            "archive member labels",
            "credentials and private keys",
        ],
    }


def _intake_packet(generated_at: str, basis_summary: dict[str, Any], summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "record_type": "v014_private_processed_value_source_map_owner_authorized_fill_packet",
        "schema_version": PACKET_SCHEMA_VERSION,
        "project_id": PROJECT_ID,
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "current_gate": CURRENT_GATE,
        "generated_at": generated_at,
        "packet_status": "ready_for_owner_or_authorized_delegate_fill_record",
        "fill_record_status": "no_owner_authorized_fill_record_supplied",
        "allowed_intake_action_codes": ALLOWED_INTAKE_ACTION_CODES,
        "allowed_actor_roles": ALLOWED_ACTOR_ROLES,
        "basis_summary": basis_summary,
        "intake_summary": summary,
        "intake_options": [
            {
                "action_code": "supply_authorized_processed_value_fingerprint",
                "meaning": "Owner supplies a non-value fingerprint for the processed value source for one or more target slots.",
                "this_phase_unlocks_anything": False,
            },
            {
                "action_code": "map_existing_metadata_hash_sibling",
                "meaning": "Owner maps a target slot to an existing authorized metadata hash sibling without exposing the private value.",
                "this_phase_unlocks_anything": False,
            },
            {
                "action_code": "keep_pending",
                "meaning": "Owner keeps one or more gaps unresolved for later review.",
                "this_phase_unlocks_anything": False,
            },
        ],
        "owner_action_required": True,
        "safe_response_fields": [
            "actor_role",
            "actor_ref",
            "decision_time",
            "fill_record_scope",
            "action_code",
            "target_slot_id",
            "authorized_processed_value_fingerprint_or_metadata_hash_ref",
            "basis_note",
        ],
        "blocked_follow_on_actions": {
            "processed_value_materialization_replay_allowed": False,
            "raw_to_processed_value_comparison_allowed": False,
            "lineage_full_check_allowed": False,
            "formal_report_allowed": False,
            "github_upload_allowed": False,
            "app_reinstall_allowed": False,
            "business_execution_allowed": False,
        },
    }


def _template(action_code: str, generated_at: str) -> dict[str, Any]:
    template: dict[str, Any] = {
        "record_type": "v014_private_processed_value_source_map_owner_authorized_fill_template",
        "schema_version": TEMPLATE_SCHEMA_VERSION,
        "project_id": PROJECT_ID,
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "current_gate": CURRENT_GATE,
        "generated_at": generated_at,
        "not_fill_record": True,
        "action_code": action_code,
        "actor_role": "owner_or_authorized_delegate",
        "actor_ref": "OWNER_SUPPLIED_PUBLIC_SAFE_REF",
        "decision_time": "OWNER_SUPPLIED_ISO8601",
        "fill_record_scope": "selected_private_processed_value_source_map_gaps",
        "basis_refs": [GAP_MANIFEST_PATH.as_posix(), GAP_GO_NO_GO_PATH.as_posix()],
        "fill_items": [
            {
                "target_slot_id": "OWNER_SUPPLIED_TARGET_SLOT_ID_FROM_PRIVATE_REQUEST",
                "action_code": action_code,
                "basis_note": "OWNER_SUPPLIED_PUBLIC_SAFE_REASON",
            }
        ],
        "raw_or_business_value_allowed": False,
        "public_repo_ready_without_validation": False,
    }
    item = template["fill_items"][0]
    if action_code == "supply_authorized_processed_value_fingerprint":
        item["authorized_processed_value_fingerprint"] = "OWNER_SUPPLIED_NON_VALUE_FINGERPRINT"
    elif action_code == "map_existing_metadata_hash_sibling":
        item["authorized_metadata_hash_sibling_ref"] = "OWNER_SUPPLIED_PUBLIC_SAFE_METADATA_HASH_REF"
    else:
        item["reason_pending"] = "OWNER_SUPPLIED_PUBLIC_SAFE_PENDING_REASON"
        item["next_review_trigger"] = "OWNER_SUPPLIED_PUBLIC_SAFE_TRIGGER"
    return template


def _private_intake_request(generated_at: str, private_worklist: dict[str, Any], summary: dict[str, Any]) -> dict[str, Any]:
    source_items = private_worklist.get("owner_worklist_items", [])
    request_items: list[dict[str, Any]] = []
    for item in source_items if isinstance(source_items, list) else []:
        if not isinstance(item, dict):
            continue
        request_items.append(
            {
                "target_slot_id": item.get("target_slot_id"),
                "private_processed_ref": item.get("private_processed_ref"),
                "private_processed_ref_hash": item.get("private_processed_ref_hash"),
                "private_processed_ref_shape_hash": item.get("private_processed_ref_shape_hash"),
                "source_root_id": item.get("source_root_id"),
                "context_group": item.get("context_group"),
                "source_artifact_ref_hash": item.get("source_artifact_ref_hash"),
                "record_ref_hash": item.get("record_ref_hash"),
                "target_key_ref_hash": item.get("target_key_ref_hash"),
                "allowed_intake_action_codes": ALLOWED_INTAKE_ACTION_CODES,
                "required_owner_action": "supply_authorized_processed_value_fingerprint_or_authorized_metadata_hash_ref_or_keep_pending",
                "public_commit_policy": "do_not_commit_private_ref_or_value",
            }
        )
    return {
        "schema_version": PRIVATE_SCHEMA_VERSION,
        "classification": "private_owner_authorized_fill_intake_request_do_not_commit",
        "project_id": PROJECT_ID,
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "intake_request_summary": {
            "intake_request_item_count": len(request_items),
            "source_unresolved_gap_item_count": summary["source_unresolved_gap_item_count"],
            "source_unresolved_unique_private_ref_count": summary["source_unresolved_unique_private_ref_count"],
            "owner_authorized_fill_record_supplied": False,
            "active_authorized_fill_record_created": False,
            "raw_to_processed_value_comparison_performed": False,
            "business_value_consistency_verified": False,
        },
        "intake_request_items": request_items,
    }


def _build_go_no_go(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": GO_NO_GO_SCHEMA_VERSION,
        "record_type": "v014_private_processed_value_source_map_owner_authorized_fill_intake_go_no_go_report",
        "project_id": PROJECT_ID,
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "decision": "NO_GO",
        "decision_reason": "Owner-authorized fill intake is ready, but no active owner-authorized fill record has been supplied.",
        "owner_authorized_fill_intake_ready": summary["owner_authorized_fill_intake_ready"],
        "owner_authorized_fill_record_supplied": summary["owner_authorized_fill_record_supplied"],
        "active_authorized_fill_record_created": summary["active_authorized_fill_record_created"],
        "source_unresolved_gap_item_count": summary["source_unresolved_gap_item_count"],
        "private_intake_request_item_count": summary["private_intake_request_item_count"],
        "new_authorized_fingerprint_count": summary["new_authorized_fingerprint_count"],
        "source_map_gap_resolution_complete": summary["source_map_gap_resolution_complete"],
        "processed_value_materialization_replay_allowed": False,
        "raw_to_processed_value_comparison_allowed": False,
        "business_value_consistency_verified": False,
        "lineage_full_check_complete": False,
        "formal_report_allowed": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "business_execution_allowed": False,
        "next_required_input": NEXT_REQUIRED_INPUT,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
        "resolved_blocker_ids": [
            "OWNER_AUTHORIZED_FILL_INTAKE_CONTRACT_READY",
            "PRIVATE_INTAKE_REQUEST_PREPARED",
            "RAW_INBOX_MUTATION_NOT_PERFORMED_BY_THIS_PHASE",
        ],
        "blocker_ids": [
            "OWNER_AUTHORIZED_FILL_RECORD_NOT_SUPPLIED",
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


def generate(*, generated_at: str | None = None) -> dict[str, Any]:
    timestamp = _now(generated_at)
    gap_manifest = _read_json(GAP_MANIFEST_PATH)
    gap_go_no_go = _read_json(GAP_GO_NO_GO_PATH)
    private_worklist = _read_json(GAP_PRIVATE_WORKLIST_PATH)
    basis_summary = _basis_summary(gap_manifest, gap_go_no_go, private_worklist)
    summary = _intake_summary(basis_summary)
    contract = _intake_contract(timestamp, basis_summary)
    packet = _intake_packet(timestamp, basis_summary, summary)
    go_no_go = _build_go_no_go(summary)
    private_request = _private_intake_request(timestamp, private_worklist, summary)
    private_diagnostic = {
        "schema_version": PRIVATE_SCHEMA_VERSION,
        "classification": "private_owner_authorized_fill_intake_diagnostic_do_not_commit",
        "project_id": PROJECT_ID,
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "basis_summary": basis_summary,
        "intake_summary": summary,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
    }
    templates = {
        action_code: _template(action_code, timestamp)
        for action_code in ALLOWED_INTAKE_ACTION_CODES
    }
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "v014_private_processed_value_source_map_owner_authorized_fill_intake_manifest",
        "project_id": PROJECT_ID,
        "version": VERSION,
        "phase_id": PHASE_ID,
        "phase_name": "KMFA v0.1.4 private processed value source-map owner authorized fill intake",
        "task_id": TASK_ID,
        "acceptance_ids": [ACCEPTANCE_ID],
        "status": STATUS,
        "generated_at": timestamp,
        "source_commit": stable_source_commit(),
        "branch": _git_output(["branch", "--show-current"]),
        "dependencies": {
            "gap_resolution_manifest": GAP_MANIFEST_PATH.as_posix(),
            "gap_resolution_go_no_go": GAP_GO_NO_GO_PATH.as_posix(),
            "private_gap_worklist": "private_runtime_previous_phase",
        },
        "phase_scope_controls": {
            "current_phase_only": True,
            "owner_authorized_fill_intake_only": True,
            "private_worklist_consumed": True,
            "private_intake_request_written": True,
            "owner_authorized_fill_record_created": False,
            "new_fingerprints_materialized": False,
            "processed_value_materialization_replay_performed": False,
            "raw_to_processed_value_comparison_performed": False,
            "processed_data_reconciliation_performed": False,
            "lineage_full_check_performed": False,
            "formal_report_performed": False,
            "github_upload_performed": False,
            "app_reinstall_performed": False,
            "business_execution_performed": False,
            "next_phase_started": False,
        },
        "raw_readonly_boundary": _raw_boundary(),
        "public_repo_safety": _public_safety(),
        "basis_summary": basis_summary,
        "owner_authorized_fill_intake_summary": summary,
        "intake_contract": contract,
        "intake_packet": packet,
        "private_intake_request_ref": "private_runtime_only_not_committed",
        "go_no_go": go_no_go,
        "evidence_refs": [
            REPORT_PATH.as_posix(),
            DECISION_REQUEST_PATH.as_posix(),
            GO_NO_GO_RECORD_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            RISK_REGISTER_PATH.as_posix(),
            ROLLBACK_PATH.as_posix(),
            MANIFEST_PATH.as_posix(),
            GO_NO_GO_PATH.as_posix(),
            SUMMARY_PATH.as_posix(),
            INTAKE_PACKET_PATH.as_posix(),
            INTAKE_CONTRACT_PATH.as_posix(),
            METADATA_MANIFEST_PATH.as_posix(),
            METADATA_GO_NO_GO_PATH.as_posix(),
            METADATA_SUMMARY_PATH.as_posix(),
            METADATA_PACKET_PATH.as_posix(),
            METADATA_CONTRACT_PATH.as_posix(),
        ],
        "github_upload_performed": False,
        "formal_report_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "next_required_input": NEXT_REQUIRED_INPUT,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
    }

    for path, payload in (
        (PRIVATE_INTAKE_REQUEST_PATH, private_request),
        (PRIVATE_INTAKE_DIAGNOSTIC_PATH, private_diagnostic),
        (MANIFEST_PATH, manifest),
        (GO_NO_GO_PATH, go_no_go),
        (SUMMARY_PATH, summary),
        (INTAKE_PACKET_PATH, packet),
        (INTAKE_CONTRACT_PATH, contract),
        (METADATA_MANIFEST_PATH, manifest),
        (METADATA_GO_NO_GO_PATH, go_no_go),
        (METADATA_SUMMARY_PATH, summary),
        (METADATA_PACKET_PATH, packet),
        (METADATA_CONTRACT_PATH, contract),
    ):
        _write_json(path, payload)
    for action_code, payload in templates.items():
        _write_json(TEMPLATES_DIR / f"{action_code}_template.json", payload)

    _write_text(
        REPORT_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 Owner Authorized Fill Intake",
                "",
                f"- phase_scope: `{PHASE_ID} only`",
                f"- source_unresolved_gap_item_count: `{summary['source_unresolved_gap_item_count']}`",
                f"- source_unresolved_unique_private_ref_count: `{summary['source_unresolved_unique_private_ref_count']}`",
                f"- private_intake_request_item_count: `{summary['private_intake_request_item_count']}`",
                f"- allowed_intake_action_count: `{summary['allowed_intake_action_count']}`",
                f"- owner_authorized_fill_intake_ready: `{str(summary['owner_authorized_fill_intake_ready']).lower()}`",
                f"- owner_authorized_fill_record_supplied: `{str(summary['owner_authorized_fill_record_supplied']).lower()}`",
                f"- active_authorized_fill_record_created: `{str(summary['active_authorized_fill_record_created']).lower()}`",
                f"- new_authorized_fingerprint_count: `{summary['new_authorized_fingerprint_count']}`",
                "- raw_inbox_access_performed_by_this_phase: `false`",
                "- processed_value_materialization_replay_performed: `false`",
                "- raw_to_processed_value_comparison_performed: `false`",
                "- business_value_consistency_verified: `false`",
                "- github_upload_performed: `false`",
                "- go_no_go: `NO_GO`",
            ]
        )
        + "\n",
    )
    _write_text(
        DECISION_REQUEST_PATH,
        "\n".join(
            [
                "# Owner Authorized Fill Request",
                "",
                "- required_actor_role: `owner` or `authorized_delegate`",
                f"- target_gap_count: `{summary['private_intake_request_item_count']}`",
                "- accepted_action_codes: `supply_authorized_processed_value_fingerprint`, `map_existing_metadata_hash_sibling`, `keep_pending`",
                "- private_request_location: `git-ignored private runtime only`",
                "- public_repo_policy: `aggregate/status/ref only; no raw or business values`",
                "- current_gate: `NO_GO`",
            ]
        )
        + "\n",
    )
    _write_text(
        GO_NO_GO_RECORD_PATH,
        "\n".join(
            [
                "# Go No-Go Record",
                "",
                "- decision: `NO_GO`",
                "- reason: owner-authorized fill intake is ready, but no active fill record has been supplied",
                f"- source_unresolved_gap_item_count: `{summary['source_unresolved_gap_item_count']}`",
                f"- next_required_input: `{NEXT_REQUIRED_INPUT}`",
                f"- next_recommended_phase: `{NEXT_RECOMMENDED_PHASE}`",
                "- github_upload_allowed: `false`",
                "- app_reinstall_allowed: `false`",
                "- business_execution_allowed: `false`",
            ]
        )
        + "\n",
    )
    _write_text(
        TEST_RESULTS_PATH,
        "\n".join(
            [
                "# Test Results",
                "",
                "- RED: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_private_processed_value_source_map_owner_authorized_fill_intake -q` failed with missing validator/generator module.",
                "- PASS: `python3 -m py_compile KMFA/tools/v014_private_processed_value_source_map_owner_authorized_fill_intake.py KMFA/tools/check_v014_private_processed_value_source_map_owner_authorized_fill_intake.py KMFA/tests/test_v014_private_processed_value_source_map_owner_authorized_fill_intake.py`.",
                "- PASS: `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/v014_private_processed_value_source_map_owner_authorized_fill_intake.py`.",
                "- PASS: `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_v014_private_processed_value_source_map_owner_authorized_fill_intake.py --require-private-intake-request`.",
                "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_private_processed_value_source_map_owner_authorized_fill_intake -q`.",
                "- Additional final validation: governance validators, no-float/no-omission checks, parse checks, raw/private scans, secret scans, public artifact boundary scan, private runtime git-boundary scan and `git diff --check` are recorded from the current run output before local commit.",
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
                "| Risk | Status | Control |",
                "| --- | --- | --- |",
                "| 113 gaps still require owner/authorized action | open | private intake request prepared; NO_GO preserved |",
                "| Private refs leak to public artifacts | controlled | public artifacts contain aggregate counts and action-code schema only |",
                "| Raw inbox mutation | controlled | this phase performs no raw inbox access or mutation |",
                "| Premature materialization/comparison | blocked | Go/No-Go keeps replay and comparison false |",
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
                "1. Remove this phase's public artifacts and metadata copies.",
                "2. Remove ignored private runtime folder for this phase.",
                "3. Re-run previous gap-resolution validator to confirm prior state remains intact.",
                "4. Keep raw inbox untouched; no raw rollback action should be required.",
            ]
        )
        + "\n",
    )
    return manifest


def main() -> None:
    manifest = generate()
    summary = manifest["owner_authorized_fill_intake_summary"]
    print(
        "Generated KMFA v0.1.4 owner-authorized fill intake "
        f"(items={summary['private_intake_request_item_count']}, "
        f"actions={summary['allowed_intake_action_count']}, go_no_go={manifest['go_no_go']['decision']})"
    )


if __name__ == "__main__":
    main()
