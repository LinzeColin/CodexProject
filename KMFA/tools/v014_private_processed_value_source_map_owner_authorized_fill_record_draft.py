#!/usr/bin/env python3
"""Prepare a private owner-authorized fill record draft for KMFA v0.1.4.

This phase does not create an active owner authorization record. It prepares a
git-ignored draft from the existing owner fill intake request so an owner or
authorized delegate can review and explicitly activate it later.
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


SCHEMA_VERSION = "kmfa.v014_private_processed_value_source_map_owner_authorized_fill_record_draft.v1"
GO_NO_GO_SCHEMA_VERSION = "kmfa.v014_private_processed_value_source_map_owner_authorized_fill_record_draft_go_no_go.v1"
SUMMARY_SCHEMA_VERSION = "kmfa.v014_private_processed_value_source_map_owner_authorized_fill_record_draft_summary.v1"
PREVIEW_SCHEMA_VERSION = "kmfa.v014_private_processed_value_source_map_owner_authorized_fill_record_draft_preview.v1"
PRIVATE_SCHEMA_VERSION = "kmfa.private.v014_private_processed_value_source_map_owner_authorized_fill_record_draft.v1"

PROJECT_ID = "KMFA"
VERSION = "0.1.4"
PRODUCT_VERSION = "0.1.4-private-processed-value-source-map-owner-authorized-fill-record-draft"
PHASE_ID = "V014_PRIVATE_PROCESSED_VALUE_SOURCE_MAP_OWNER_AUTHORIZED_FILL_RECORD_DRAFT"
TASK_ID = "KMFA-V014-PRIVATE-PROCESSED-VALUE-SOURCE-MAP-OWNER-AUTHORIZED-FILL-RECORD-DRAFT-20260705"
ACCEPTANCE_ID = "ACC-V014-PRIVATE-PROCESSED-VALUE-SOURCE-MAP-OWNER-AUTHORIZED-FILL-RECORD-DRAFT"
STATUS = "draft_prepared_local_only_no_go_pending_owner_authorization"
CURRENT_GATE = "KMFA-V014-PRIVATE-PROCESSED-VALUE-SOURCE-MAP-OWNER-AUTHORIZED-FILL-RECORD-DRAFT-GATE"
NEXT_REQUIRED_INPUT = "owner_or_authorized_delegate_activation_of_draft_fill_record"
NEXT_RECOMMENDED_PHASE = "V014_PRIVATE_PROCESSED_VALUE_SOURCE_MAP_OWNER_AUTHORIZED_FILL_APPLICATION"

OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_PRIVATE_PROCESSED_VALUE_SOURCE_MAP_OWNER_AUTHORIZED_FILL_RECORD_DRAFT")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
MANIFEST_PATH = MACHINE_DIR / "private_processed_value_source_map_owner_authorized_fill_record_draft_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "private_processed_value_source_map_owner_authorized_fill_record_draft_go_no_go_report.json"
SUMMARY_PATH = MACHINE_DIR / "private_processed_value_source_map_owner_authorized_fill_record_draft_summary.json"
PREVIEW_PATH = MACHINE_DIR / "private_processed_value_source_map_owner_authorized_fill_record_draft_preview.json"
REPORT_PATH = HUMAN_DIR / "private_processed_value_source_map_owner_authorized_fill_record_draft_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_MANIFEST_PATH = Path(
    "KMFA/metadata/quality/v014_private_processed_value_source_map_owner_authorized_fill_record_draft_manifest.json"
)
METADATA_GO_NO_GO_PATH = Path(
    "KMFA/metadata/quality/v014_private_processed_value_source_map_owner_authorized_fill_record_draft_go_no_go_report.json"
)
METADATA_SUMMARY_PATH = Path(
    "KMFA/metadata/quality/v014_private_processed_value_source_map_owner_authorized_fill_record_draft_summary.json"
)
METADATA_PREVIEW_PATH = Path(
    "KMFA/metadata/approvals/v014_private_processed_value_source_map_owner_authorized_fill_record_draft_preview.json"
)

INTAKE_CONTRACT_PATH = Path(
    "KMFA/stage_artifacts/V014_PRIVATE_PROCESSED_VALUE_SOURCE_MAP_OWNER_AUTHORIZED_FILL_INTAKE/machine/private_processed_value_source_map_owner_authorized_fill_intake_contract.json"
)
INTAKE_PACKET_PATH = Path(
    "KMFA/stage_artifacts/V014_PRIVATE_PROCESSED_VALUE_SOURCE_MAP_OWNER_AUTHORIZED_FILL_INTAKE/machine/private_processed_value_source_map_owner_authorized_fill_packet.json"
)
PRIVATE_INTAKE_REQUEST_PATH = Path(
    "KMFA/.codex_private_runtime/v014_private_processed_value_source_map_owner_authorized_fill_intake/private_owner_authorized_fill_intake_request.json"
)

PRIVATE_OUTPUT_DIR = Path("KMFA/.codex_private_runtime/v014_private_processed_value_source_map_owner_authorized_fill_record_draft")
PRIVATE_DRAFT_PATH = PRIVATE_OUTPUT_DIR / "draft_owner_authorized_fill_record.json"
ACTIVE_FILL_RECORD_CANDIDATE_PATHS = [
    Path("KMFA/.codex_private_runtime/v014_private_processed_value_source_map_owner_authorized_fill_application/active_owner_authorized_fill_record.json"),
    Path("KMFA/.codex_private_runtime/v014_private_processed_value_source_map_owner_authorized_fill_intake/active_owner_authorized_fill_record.json"),
]


def _now(generated_at: str | None = None) -> str:
    return generated_at or datetime.now().astimezone().isoformat(timespec="seconds")


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
        "private_draft_committed": False,
        "credential_or_secret_committed": False,
    }


def _build_draft_fill_items(private_request: dict[str, Any]) -> list[dict[str, str]]:
    request_items = private_request.get("intake_request_items", [])
    if not isinstance(request_items, list):
        raise ValueError("private intake request items must be a list")
    fill_items: list[dict[str, str]] = []
    for item in request_items:
        if not isinstance(item, dict):
            raise ValueError("each private intake request item must be an object")
        target_slot_id = item.get("target_slot_id")
        allowed = item.get("allowed_intake_action_codes", [])
        if not isinstance(target_slot_id, str) or not target_slot_id:
            raise ValueError("private intake request item missing target_slot_id")
        if "keep_pending" not in allowed:
            raise ValueError(f"keep_pending is not allowed for {target_slot_id}")
        fill_items.append(
            {
                "target_slot_id": target_slot_id,
                "action_code": "keep_pending",
                "basis_note": "draft default keeps this slot pending until owner or authorized delegate supplies an authorized value source",
                "reason_pending": "owner_or_authorized_delegate_value_source_confirmation_required",
                "next_review_trigger": "owner_or_authorized_delegate_activates_fill_record",
            }
        )
    return fill_items


def _active_record_status() -> dict[str, Any]:
    existing = [path for path in ACTIVE_FILL_RECORD_CANDIDATE_PATHS if path.exists()]
    return {
        "candidate_active_fill_record_path_count": len(ACTIVE_FILL_RECORD_CANDIDATE_PATHS),
        "existing_active_fill_record_path_count": len(existing),
        "active_authorized_fill_record_found": bool(existing),
    }


def _build_summary(
    *,
    contract: dict[str, Any],
    packet: dict[str, Any],
    private_request: dict[str, Any],
    draft_fill_items: list[dict[str, str]],
) -> dict[str, Any]:
    request_summary = private_request.get("intake_request_summary", {})
    if not isinstance(request_summary, dict):
        request_summary = {}
    active_status = _active_record_status()
    target_slot_ids = [item["target_slot_id"] for item in draft_fill_items]
    return {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "record_type": "v014_private_processed_value_source_map_owner_authorized_fill_record_draft_summary",
        "project_id": PROJECT_ID,
        "version": VERSION,
        "product_version": PRODUCT_VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "source_phase_id": contract.get("phase_id"),
        "source_packet_status": packet.get("packet_status"),
        "private_intake_request_item_count": int(request_summary.get("intake_request_item_count", 0)),
        "source_unresolved_gap_item_count": int(request_summary.get("source_unresolved_gap_item_count", 0)),
        "source_unresolved_unique_private_ref_count": int(request_summary.get("source_unresolved_unique_private_ref_count", 0)),
        "draft_fill_item_count": len(draft_fill_items),
        "draft_unique_target_slot_count": len(set(target_slot_ids)),
        "draft_keep_pending_item_count": sum(1 for item in draft_fill_items if item["action_code"] == "keep_pending"),
        "draft_supply_authorized_fingerprint_item_count": 0,
        "draft_map_existing_metadata_hash_sibling_item_count": 0,
        "draft_status": "draft_prepared_pending_owner_or_authorized_delegate_activation",
        "draft_private_runtime_written": True,
        "draft_is_active_record": False,
        "owner_authorized_fill_record_supplied": False,
        "active_authorized_fill_record_created": False,
        "fill_application_performed": False,
        "source_map_records_applied_count": 0,
        "new_authorized_fingerprint_count": 0,
        "source_map_gap_resolution_complete": False,
        "processed_value_materialization_replay_ready": False,
        "raw_to_processed_value_comparison_ready": False,
        "business_value_consistency_verified": False,
        "lineage_full_check_complete": False,
        "formal_report_allowed": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "business_execution_allowed": False,
        "next_required_input": NEXT_REQUIRED_INPUT,
        **active_status,
    }


def _build_private_draft(
    *,
    generated_at: str,
    contract: dict[str, Any],
    packet: dict[str, Any],
    summary: dict[str, Any],
    draft_fill_items: list[dict[str, str]],
) -> dict[str, Any]:
    return {
        "schema_version": PRIVATE_SCHEMA_VERSION,
        "classification": "private_owner_authorized_fill_record_draft_do_not_commit",
        "record_type": "v014_private_processed_value_source_map_owner_authorized_fill_record_draft",
        "project_id": PROJECT_ID,
        "version": VERSION,
        "product_version": PRODUCT_VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "draft_status": summary["draft_status"],
        "draft_is_active_record": False,
        "activation_required": True,
        "activation_policy": {
            "owner_or_authorized_delegate_must_confirm": True,
            "do_not_treat_this_file_as_active_record": True,
            "active_record_candidate_count": summary["candidate_active_fill_record_path_count"],
            "next_phase_after_activation": NEXT_RECOMMENDED_PHASE,
        },
        "source_contract_ref": str(INTAKE_CONTRACT_PATH),
        "source_packet_status": packet.get("packet_status"),
        "proposed_active_record_template": {
            "record_type": contract.get("accepted_record_type"),
            "actor_role": "PENDING_OWNER_OR_AUTHORIZED_DELEGATE_CONFIRMATION",
            "actor_ref": "PENDING_OWNER_OR_AUTHORIZED_DELEGATE_CONFIRMATION",
            "decision_time": "PENDING_OWNER_OR_AUTHORIZED_DELEGATE_CONFIRMATION",
            "fill_record_scope": "all_current_pending_items_default_keep_pending",
            "basis_refs": list(contract.get("basis_refs", [])),
            "fill_items": draft_fill_items,
            "draft_only_not_active": True,
        },
        "draft_summary": summary,
        "raw_readonly_boundary": _raw_readonly_boundary(),
    }


def _build_go_no_go(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": GO_NO_GO_SCHEMA_VERSION,
        "record_type": "v014_private_processed_value_source_map_owner_authorized_fill_record_draft_go_no_go_report",
        "project_id": PROJECT_ID,
        "version": VERSION,
        "product_version": PRODUCT_VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "decision": "NO_GO",
        "decision_reason": "A private draft was prepared, but no owner or authorized delegate activated an active fill record.",
        "draft_prepared": True,
        "draft_is_active_record": False,
        "owner_authorized_fill_record_supplied": False,
        "active_authorized_fill_record_created": False,
        "fill_application_performed": False,
        "source_map_records_applied_count": 0,
        "new_authorized_fingerprint_count": 0,
        "source_map_gap_resolution_complete": False,
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
            "OWNER_AUTHORIZED_FILL_RECORD_DRAFT_PREPARED",
            "PRIVATE_DRAFT_WRITTEN_TO_GIT_IGNORED_RUNTIME",
            "RAW_INBOX_NOT_ACCESSED_BY_THIS_PHASE",
        ],
        "blocker_ids": [
            "OWNER_OR_AUTHORIZED_DELEGATE_ACTIVATION_REQUIRED",
            "ACTIVE_OWNER_AUTHORIZED_FILL_RECORD_NOT_FOUND",
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


def _build_preview(generated_at: str, summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": PREVIEW_SCHEMA_VERSION,
        "record_type": "v014_private_processed_value_source_map_owner_authorized_fill_record_draft_preview",
        "project_id": PROJECT_ID,
        "version": VERSION,
        "product_version": PRODUCT_VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "current_gate": CURRENT_GATE,
        "generated_at": generated_at,
        "draft_status": summary["draft_status"],
        "draft_fill_item_count": summary["draft_fill_item_count"],
        "draft_keep_pending_item_count": summary["draft_keep_pending_item_count"],
        "draft_supply_authorized_fingerprint_item_count": 0,
        "draft_map_existing_metadata_hash_sibling_item_count": 0,
        "draft_is_active_record": False,
        "owner_authorized_fill_record_supplied": False,
        "active_authorized_fill_record_created": False,
        "fill_application_performed": False,
        "source_map_gap_resolution_complete": False,
        "processed_value_materialization_replay_allowed": False,
        "raw_to_processed_value_comparison_allowed": False,
        "business_value_consistency_verified": False,
        "lineage_full_check_complete": False,
        "formal_report_allowed": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "business_execution_allowed": False,
        "next_required_input": NEXT_REQUIRED_INPUT,
    }


def _write_human_files(summary: dict[str, Any], go_no_go: dict[str, Any]) -> None:
    _write_text(
        REPORT_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 Owner Authorized Fill Record Draft",
                "",
                f"- phase_id: `{PHASE_ID}`",
                f"- task_id: `{TASK_ID}`",
                f"- status: `{STATUS}`",
                f"- draft_fill_item_count: `{summary['draft_fill_item_count']}`",
                f"- draft_keep_pending_item_count: `{summary['draft_keep_pending_item_count']}`",
                f"- active_authorized_fill_record_created: `{str(summary['active_authorized_fill_record_created']).lower()}`",
                f"- fill_application_performed: `{str(summary['fill_application_performed']).lower()}`",
                f"- source_map_records_applied_count: `{summary['source_map_records_applied_count']}`",
                f"- go_no_go: `{go_no_go['decision']}`",
                f"- next_required_input: `{NEXT_REQUIRED_INPUT}`",
                "",
                "## Boundary",
                "",
                "- This phase prepares a private draft only; it is not an active owner-authorized fill record.",
                "- This phase did not read, list, stat, hash, write, delete, move, rename, overwrite, normalize or copy the raw inbox.",
                "- This phase did not run processed value materialization, raw-to-processed comparison, lineage full check, formal report, GitHub upload, app reinstall or business execution.",
                "- Public evidence is aggregate/status/ref only and does not contain raw values, field headers, row values, private refs or business values.",
                "",
            ]
        ),
    )
    _write_text(
        GO_NO_GO_RECORD_PATH,
        "\n".join(
            [
                "# Go/No-Go",
                "",
                f"- decision: `{go_no_go['decision']}`",
                f"- decision_reason: `{go_no_go['decision_reason']}`",
                "- delivery_allowed: `false`",
                "- formal_report_allowed: `false`",
                "- github_upload_allowed: `false`",
                "- app_reinstall_allowed: `false`",
                "- business_execution_allowed: `false`",
                "",
            ]
        ),
    )
    _write_text(
        TEST_RESULTS_PATH,
        "\n".join(
            [
                "# Test Results",
                "",
                "- py_compile: `PENDING_FINAL_VALIDATION`",
                "- focused_unit_test: `PENDING_FINAL_VALIDATION`",
                "- owner_fill_record_draft_validator: `PENDING_FINAL_VALIDATION`",
                "- governance_validators: `PENDING_FINAL_VALIDATION`",
                "- raw_private_suffix_scan: `PENDING_FINAL_VALIDATION`",
                "- secret_scan: `PENDING_FINAL_VALIDATION`",
                "",
            ]
        ),
    )
    _write_text(
        RISK_REGISTER_PATH,
        "\n".join(
            [
                "# Risk Register",
                "",
                "- risk: Draft evidence could be mistaken for active owner authorization.",
                "  mitigation: Public Go/No-Go and validator require `draft_is_active_record=false`, `active_authorized_fill_record_created=false` and downstream gates blocked.",
                "- risk: Downstream phases could be run before owner activation.",
                "  mitigation: Next required input remains owner or authorized delegate activation of the draft fill record.",
                "",
            ]
        ),
    )
    _write_text(
        ROLLBACK_PATH,
        "\n".join(
            [
                "# Rollback Plan",
                "",
                "- Remove draft phase public artifacts, metadata copies, validator, focused test and governance entries.",
                "- Remove the git-ignored private draft file if the owner rejects the draft.",
                "- Do not modify raw inbox contents.",
                "",
            ]
        ),
    )


def generate(generated_at: str | None = None) -> dict[str, Any]:
    timestamp = _now(generated_at)
    contract = _read_json(INTAKE_CONTRACT_PATH)
    packet = _read_json(INTAKE_PACKET_PATH)
    private_request = _read_json(PRIVATE_INTAKE_REQUEST_PATH)
    draft_fill_items = _build_draft_fill_items(private_request)
    summary = _build_summary(contract=contract, packet=packet, private_request=private_request, draft_fill_items=draft_fill_items)
    private_draft = _build_private_draft(
        generated_at=timestamp,
        contract=contract,
        packet=packet,
        summary=summary,
        draft_fill_items=draft_fill_items,
    )
    go_no_go = _build_go_no_go(summary)
    preview = _build_preview(timestamp, summary)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "v014_private_processed_value_source_map_owner_authorized_fill_record_draft_manifest",
        "project_id": PROJECT_ID,
        "version": VERSION,
        "product_version": PRODUCT_VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_ids": [ACCEPTANCE_ID],
        "status": STATUS,
        "generated_at": timestamp,
        "branch": _git_output(["branch", "--show-current"]),
        "source_commit": _git_output(["rev-parse", "HEAD"]),
        "current_gate": CURRENT_GATE,
        "dependencies": {
            "intake_contract": str(INTAKE_CONTRACT_PATH),
            "intake_packet": str(INTAKE_PACKET_PATH),
            "private_intake_request": "git_ignored_private_runtime",
        },
        "owner_authorized_fill_record_draft_summary": summary,
        "go_no_go": go_no_go,
        "public_safety": _public_safety(),
        "raw_readonly_boundary": _raw_readonly_boundary(),
        "evidence_refs": [
            str(REPORT_PATH),
            str(GO_NO_GO_RECORD_PATH),
            str(TEST_RESULTS_PATH),
            str(RISK_REGISTER_PATH),
            str(ROLLBACK_PATH),
            str(MANIFEST_PATH),
            str(GO_NO_GO_PATH),
            str(SUMMARY_PATH),
            str(PREVIEW_PATH),
            str(METADATA_MANIFEST_PATH),
            str(METADATA_GO_NO_GO_PATH),
            str(METADATA_SUMMARY_PATH),
            str(METADATA_PREVIEW_PATH),
        ],
        "validation_commands": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m py_compile KMFA/tools/v014_private_processed_value_source_map_owner_authorized_fill_record_draft.py KMFA/tools/check_v014_private_processed_value_source_map_owner_authorized_fill_record_draft.py KMFA/tests/test_v014_private_processed_value_source_map_owner_authorized_fill_record_draft.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_private_processed_value_source_map_owner_authorized_fill_record_draft.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_private_processed_value_source_map_owner_authorized_fill_record_draft.py --require-private-draft",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_private_processed_value_source_map_owner_authorized_fill_record_draft -q",
            "governance validators, raw/private suffix scan, secret scan and diff check",
        ],
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "formal_report_performed": False,
        "business_execution_performed": False,
    }
    _write_json(PRIVATE_DRAFT_PATH, private_draft)
    _write_json(MANIFEST_PATH, manifest)
    _write_json(GO_NO_GO_PATH, go_no_go)
    _write_json(SUMMARY_PATH, summary)
    _write_json(PREVIEW_PATH, preview)
    _write_json(METADATA_MANIFEST_PATH, manifest)
    _write_json(METADATA_GO_NO_GO_PATH, go_no_go)
    _write_json(METADATA_SUMMARY_PATH, summary)
    _write_json(METADATA_PREVIEW_PATH, preview)
    _write_human_files(summary, go_no_go)
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated-at")
    args = parser.parse_args(argv)
    manifest = generate(generated_at=args.generated_at)
    print(json.dumps({"ok": True, "phase_id": PHASE_ID, "status": manifest["status"]}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
