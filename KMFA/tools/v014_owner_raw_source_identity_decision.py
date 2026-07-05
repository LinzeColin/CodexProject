#!/usr/bin/env python3
"""Generate KMFA v0.1.4 raw source identity owner-decision intake evidence.

This phase prepares a public-safe owner decision gate. It does not decide which
raw source is authoritative, does not read the raw inbox, and does not unlock
lineage, report release, GitHub upload, app reinstall, or business execution.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "kmfa.v014_owner_raw_source_identity_decision.v1"
CONTRACT_SCHEMA_VERSION = "kmfa.v014_raw_source_identity_owner_decision_intake_contract.v1"
PACKET_SCHEMA_VERSION = "kmfa.v014_raw_source_identity_owner_decision_packet.v1"
TEMPLATE_SCHEMA_VERSION = "kmfa.v014_raw_source_identity_owner_decision_template.v1"
DECISION_SCHEMA_VERSION = "kmfa.v014_raw_source_identity_owner_decision.v1"
PROJECT_ID = "KMFA"
VERSION = "0.1.4"
PHASE_ID = "V014_OWNER_RAW_SOURCE_IDENTITY_DECISION"
TASK_ID = "KMFA-V014-OWNER-RAW-SOURCE-IDENTITY-DECISION-20260705"
ACCEPTANCE_ID = "ACC-V014-OWNER-RAW-SOURCE-IDENTITY-DECISION"
STATUS = "owner_raw_source_identity_decision_intake_ready_no_active_decision_no_go"
CURRENT_GATE = "KMFA-V014-RAW-SOURCE-IDENTITY-OWNER-GATE"
NEXT_REQUIRED_INPUT = "owner_decision_code_or_corrected_registered_source_package"
NEXT_RECOMMENDED_PHASE = "V014_RAW_SOURCE_IDENTITY_DECISION_APPLICATION"

ALLOWED_DECISION_CODES = [
    "confirm_current_container_as_authoritative",
    "register_corrected_source_package",
    "keep_pending",
]
ALLOWED_ACTOR_ROLES = ["owner", "authorized_delegate"]
RAW_ALIGNMENT_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V014_RAW_ALIGNMENT_REMEDIATION/machine/raw_alignment_remediation_manifest.json"
)
RAW_ALIGNMENT_GO_NO_GO_PATH = Path(
    "KMFA/stage_artifacts/V014_RAW_ALIGNMENT_REMEDIATION/machine/raw_alignment_go_no_go_report.json"
)

OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_OWNER_RAW_SOURCE_IDENTITY_DECISION")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
TEMPLATES_DIR = MACHINE_DIR / "owner_decision_templates"
MANIFEST_PATH = MACHINE_DIR / "owner_raw_source_identity_decision_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "owner_raw_source_identity_go_no_go_report.json"
DECISION_PACKET_PATH = MACHINE_DIR / "owner_raw_source_identity_decision_packet.json"
INTAKE_CONTRACT_PATH = MACHINE_DIR / "owner_raw_source_identity_decision_intake_contract.json"
REPORT_PATH = HUMAN_DIR / "owner_raw_source_identity_decision_report.md"
DECISION_REQUEST_PATH = HUMAN_DIR / "owner_decision_request.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_MANIFEST_PATH = Path("KMFA/metadata/quality/v014_owner_raw_source_identity_decision_manifest.json")
METADATA_GO_NO_GO_PATH = Path("KMFA/metadata/quality/v014_owner_raw_source_identity_go_no_go_report.json")
METADATA_PACKET_PATH = Path("KMFA/metadata/approvals/v014_raw_source_identity_decision_packet.json")
METADATA_CONTRACT_PATH = Path("KMFA/metadata/approvals/v014_raw_source_identity_decision_intake_contract.json")


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


def _basis_summary(raw_manifest: dict[str, Any], raw_go_no_go: dict[str, Any]) -> dict[str, Any]:
    raw = raw_manifest.get("raw_source_identity_summary", {})
    return {
        "source_phase_id": raw_manifest.get("phase_id"),
        "source_task_id": raw_manifest.get("task_id"),
        "source_status": raw_manifest.get("status"),
        "source_decision": raw_go_no_go.get("decision"),
        "business_shape_matches_expected_a0": raw.get("business_shape_matches_expected_a0") is True,
        "package_hash_matches_registered": raw.get("package_hash_matches_registered") is True,
        "package_size_matches_registered": raw.get("package_size_matches_registered") is True,
        "raw_alignment_complete": raw.get("raw_alignment_complete") is True,
        "public_member_hash_backfill_allowed": raw.get("public_member_hash_backfill_allowed") is True,
        "private_member_hashes_recorded": raw.get("private_member_hashes_recorded") is True,
        "raw_root_file_count": int(raw.get("raw_root_file_count", 0)),
        "raw_root_archive_count": int(raw.get("raw_root_archive_count", 0)),
        "raw_root_spreadsheet_count": int(raw.get("raw_root_spreadsheet_count", 0)),
        "selected_candidate_count": int(raw.get("selected_candidate_count", 0)),
        "business_member_count": int(raw.get("business_member_count", 0)),
        "blocker_ids_inherited": list(raw_go_no_go.get("blocker_ids", [])),
    }


def _public_safety() -> dict[str, bool]:
    return {
        "public_safe_decision_codes_only": True,
        "raw_business_data_committed": False,
        "compressed_raw_package_committed": False,
        "office_workbook_committed": False,
        "source_document_committed": False,
        "raw_or_private_table_committed": False,
        "local_database_committed": False,
        "credential_or_secret_committed": False,
        "raw_filenames_committed": False,
        "raw_hashes_committed": False,
        "private_diagnostic_committed": False,
        "directory_tree_plaintext_committed": False,
        "zip_member_names_committed": False,
        "sheet_names_committed": False,
        "field_or_header_plaintext_committed": False,
        "row_or_cell_values_committed": False,
        "business_values_committed": False,
    }


def _intake_contract(generated_at: str) -> dict[str, Any]:
    return {
        "record_type": "v014_raw_source_identity_owner_decision_intake_contract",
        "schema_version": CONTRACT_SCHEMA_VERSION,
        "project_id": PROJECT_ID,
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "current_gate": CURRENT_GATE,
        "generated_at": generated_at,
        "readiness_status": "ready_for_owner_decision_record",
        "decision_record_status": "no_owner_decision_recorded",
        "accepted_record_type": "v014_raw_source_identity_owner_decision",
        "allowed_decision_codes": ALLOWED_DECISION_CODES,
        "allowed_actor_roles": ALLOWED_ACTOR_ROLES,
        "basis_refs": [
            RAW_ALIGNMENT_MANIFEST_PATH.as_posix(),
            RAW_ALIGNMENT_GO_NO_GO_PATH.as_posix(),
        ],
        "required_common_fields": [
            "actor_role",
            "actor_ref",
            "decision_time",
            "decision_code",
            "basis_refs",
            "source_identity_scope",
        ],
        "source_identity_scope": "raw_container_identity_only",
        "post_intake_rules": {
            "confirm_current_container_as_authoritative": [
                "raw_container_authoritative_confirmed must be true",
                "confirmation_scope is required",
                "no raw hash or filename may be committed",
                "public member hash backfill remains a later separate phase",
            ],
            "register_corrected_source_package": [
                "corrected_package_private_ref is required",
                "current_container_superseded must be true",
                "the corrected source must remain private until a public-safe registry gate",
            ],
            "keep_pending": [
                "reason_pending is required",
                "next_review_trigger is required",
                "all upload, app, lineage, formal report and business gates remain blocked",
            ],
        },
        "raw_or_plaintext_allowed": False,
        "raw_hash_allowed": False,
        "private_diagnostic_allowed_in_public_repo": False,
        "public_hash_backfill_allowed_by_intake": False,
        "raw_alignment_complete_allowed_by_intake": False,
        "lineage_full_check_allowed_by_intake": False,
        "formal_report_allowed_by_intake": False,
        "github_upload_allowed_by_intake": False,
        "app_reinstall_allowed_by_intake": False,
        "business_execution_allowed_by_intake": False,
        "forbidden_public_metadata_categories": [
            "raw container digest fields",
            "archive member digest fields",
            "raw or normalized business values",
            "plaintext source extracts",
            "local source identifiers",
            "archive member labels",
            "worksheet labels",
            "credentials and private keys",
        ],
    }


def _decision_packet(generated_at: str, basis_summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "record_type": "v014_raw_source_identity_owner_decision_packet",
        "schema_version": PACKET_SCHEMA_VERSION,
        "project_id": PROJECT_ID,
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "current_gate": CURRENT_GATE,
        "generated_at": generated_at,
        "packet_status": "ready_for_owner_or_authorized_decision",
        "decision_record_status": "no_owner_decision_recorded",
        "allowed_decision_codes": ALLOWED_DECISION_CODES,
        "basis_summary": basis_summary,
        "decision_options": [
            {
                "decision_code": "confirm_current_container_as_authoritative",
                "meaning": "Owner confirms the current private raw container is the authoritative source despite registered container mismatch.",
                "effect": "Allows a later separate public-safe application phase to consider hash backfill and lineage checks.",
                "this_phase_unlocks_anything": False,
            },
            {
                "decision_code": "register_corrected_source_package",
                "meaning": "Owner supplies or identifies a corrected private source package to replace the mismatched registered source identity.",
                "effect": "Keeps current NO_GO until corrected package registry and validation are run.",
                "this_phase_unlocks_anything": False,
            },
            {
                "decision_code": "keep_pending",
                "meaning": "Owner keeps raw source identity unresolved.",
                "effect": "Keeps public hash backfill, lineage, report, upload and app gates blocked.",
                "this_phase_unlocks_anything": False,
            },
        ],
        "owner_action_required": True,
        "safe_response_fields": [
            "decision_code",
            "actor_role",
            "actor_ref",
            "decision_time",
            "reason_or_confirmation_scope",
        ],
        "raw_boundary": {
            "raw_inbox_read_by_this_phase": False,
            "raw_inbox_list_by_this_phase": False,
            "raw_inbox_stat_by_this_phase": False,
            "raw_inbox_hash_by_this_phase": False,
            "raw_inbox_mutated_by_this_phase": False,
        },
        "public_repo_safety": _public_safety(),
    }


def _template(decision_code: str) -> dict[str, Any]:
    base: dict[str, Any] = {
        "record_type": "v014_raw_source_identity_owner_decision_template",
        "schema_version": TEMPLATE_SCHEMA_VERSION,
        "project_id": PROJECT_ID,
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "current_gate": CURRENT_GATE,
        "template_id": f"TPL-KMFA-V014-RAW-SOURCE-IDENTITY-{decision_code.upper().replace('_', '-')}",
        "decision_code": decision_code,
        "not_decision_record": True,
        "output_record_type_after_activation": "v014_raw_source_identity_owner_decision",
        "activation_requires": [
            "owner_or_authorized_actor",
            "decision_time",
            "remove_template_marker",
            "change_record_type_to_v014_raw_source_identity_owner_decision",
        ],
        "basis_refs": [
            RAW_ALIGNMENT_MANIFEST_PATH.as_posix(),
            RAW_ALIGNMENT_GO_NO_GO_PATH.as_posix(),
        ],
        "source_identity_scope": "raw_container_identity_only",
        "raw_business_data_committed": False,
        "raw_filename_committed": False,
        "raw_hash_committed": False,
        "private_diagnostic_committed": False,
        "public_hash_backfill_performed": False,
        "raw_alignment_complete_claimed_by_intake": False,
        "lineage_full_check_performed": False,
        "formal_report_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }
    if decision_code == "confirm_current_container_as_authoritative":
        base.update(
            {
                "required_fill_fields": [
                    "actor_role",
                    "actor_ref",
                    "decision_time",
                    "confirmation_scope",
                    "raw_container_authoritative_confirmed",
                ],
                "required_raw_container_authoritative_confirmed": True,
            }
        )
    elif decision_code == "register_corrected_source_package":
        base.update(
            {
                "required_fill_fields": [
                    "actor_role",
                    "actor_ref",
                    "decision_time",
                    "corrected_package_private_ref",
                    "current_container_superseded",
                ],
                "required_current_container_superseded": True,
            }
        )
    else:
        base.update(
            {
                "required_fill_fields": [
                    "actor_role",
                    "actor_ref",
                    "decision_time",
                    "reason_pending",
                    "next_review_trigger",
                ]
            }
        )
    return base


def _go_no_go() -> dict[str, Any]:
    return {
        "record_type": "v014_owner_raw_source_identity_go_no_go_report",
        "project_id": PROJECT_ID,
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "decision": "NO_GO",
        "decision_reason": (
            "Owner raw source identity intake is ready, but no active owner or authorized decision record has been "
            "supplied. Raw alignment, public hash backfill, lineage closure, report release, GitHub upload, app "
            "reinstall and business execution remain blocked."
        ),
        "blocker_ids": [
            "RAW_SOURCE_IDENTITY_OWNER_DECISION_NOT_SUPPLIED",
            "PUBLIC_MEMBER_HASH_BACKFILL_STILL_BLOCKED",
            "LINEAGE_FULL_CHECK_BLOCKED_BY_OWNER_DECISION",
            "FORMAL_REPORT_BLOCKED_BY_OWNER_DECISION",
            "GITHUB_UPLOAD_BLOCKED_BY_OWNER_DECISION",
            "APP_REINSTALL_BLOCKED_BY_OWNER_DECISION",
        ],
        "resolved_blocker_ids": ["OWNER_DECISION_INTAKE_READY"],
        "owner_decision_intake_ready": True,
        "owner_decision_supplied": False,
        "raw_alignment_complete": False,
        "public_member_hash_backfill_allowed": False,
        "lineage_full_check_complete": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "formal_report_allowed": False,
        "business_execution_allowed": False,
        "next_required_input": NEXT_REQUIRED_INPUT,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
    }


def _manifest(
    *,
    generated_at: str,
    basis_summary: dict[str, Any],
    contract: dict[str, Any],
    packet: dict[str, Any],
    go_no_go: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": PROJECT_ID,
        "version": VERSION,
        "phase_id": PHASE_ID,
        "phase_name": "Owner raw source identity decision intake",
        "task_id": TASK_ID,
        "acceptance_ids": [ACCEPTANCE_ID],
        "status": STATUS,
        "generated_at": generated_at,
        "worktree": Path.cwd().as_posix(),
        "branch": _git_output(["branch", "--show-current"]),
        "remote": _git_output(["remote", "get-url", "origin"]),
        "reviewed_head": _git_output(["rev-parse", "HEAD"]),
        "basis_summary": basis_summary,
        "owner_decision_intake": {
            "readiness_status": contract["readiness_status"],
            "decision_record_status": contract["decision_record_status"],
            "accepted_record_type": contract["accepted_record_type"],
            "allowed_decision_codes": ALLOWED_DECISION_CODES,
            "allowed_actor_roles": ALLOWED_ACTOR_ROLES,
            "owner_decision_supplied_by_this_phase": False,
            "raw_alignment_complete_claimed_by_this_phase": False,
            "public_hash_backfill_allowed_by_this_phase": False,
            "intake_contract_ref": INTAKE_CONTRACT_PATH.as_posix(),
            "decision_packet_ref": DECISION_PACKET_PATH.as_posix(),
            "template_dir_ref": TEMPLATES_DIR.as_posix(),
        },
        "phase_scope_controls": {
            "current_phase_only": True,
            "owner_decision_intake_only": True,
            "active_owner_decision_record_created": False,
            "raw_inbox_read_performed_by_this_phase": False,
            "raw_inbox_list_performed_by_this_phase": False,
            "raw_inbox_stat_performed_by_this_phase": False,
            "raw_inbox_hash_performed_by_this_phase": False,
            "raw_inbox_mutated_by_this_phase": False,
            "public_hash_backfill_performed": False,
            "lineage_full_check_performed": False,
            "formal_report_performed": False,
            "github_upload_performed": False,
            "app_reinstall_performed": False,
            "business_execution_performed": False,
            "next_phase_started": False,
        },
        "public_repo_safety": _public_safety(),
        "go_no_go": go_no_go,
        "github_upload_performed": False,
        "github_upload_status": "not_uploaded_blocked_by_missing_owner_raw_source_identity_decision",
        "next_required_input": NEXT_REQUIRED_INPUT,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
        "evidence_refs": [
            REPORT_PATH.as_posix(),
            DECISION_REQUEST_PATH.as_posix(),
            GO_NO_GO_RECORD_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            RISK_REGISTER_PATH.as_posix(),
            ROLLBACK_PATH.as_posix(),
            MANIFEST_PATH.as_posix(),
            GO_NO_GO_PATH.as_posix(),
            DECISION_PACKET_PATH.as_posix(),
            INTAKE_CONTRACT_PATH.as_posix(),
            METADATA_MANIFEST_PATH.as_posix(),
            METADATA_GO_NO_GO_PATH.as_posix(),
            METADATA_PACKET_PATH.as_posix(),
            METADATA_CONTRACT_PATH.as_posix(),
        ],
        "validation_summary": {
            "py_compile": "PENDING_FINAL_VALIDATION",
            "focused_unit_test": "PENDING_FINAL_VALIDATION",
            "owner_raw_source_identity_decision_validator": "PENDING_FINAL_VALIDATION",
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
            "diff_check": "PENDING_FINAL_VALIDATION",
        },
    }


def _write_human_files(generated_at: str, basis_summary: dict[str, Any], go_no_go: dict[str, Any]) -> None:
    _write_text(
        REPORT_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 Owner Raw Source Identity Decision Intake",
                "",
                f"- phase_id: `{PHASE_ID}`",
                f"- task_id: `{TASK_ID}`",
                f"- generated_at: `{generated_at}`",
                "- status: `owner decision intake ready; no active decision supplied`",
                "- decision: `NO_GO`",
                "",
                "## Public-Safe Basis",
                "",
                f"- source_phase_id: `{basis_summary['source_phase_id']}`",
                f"- source_decision: `{basis_summary['source_decision']}`",
                f"- business_shape_matches_expected_a0: `{str(basis_summary['business_shape_matches_expected_a0']).lower()}`",
                f"- registered_container_hash_match: `{str(basis_summary['package_hash_matches_registered']).lower()}`",
                f"- registered_container_size_match: `{str(basis_summary['package_size_matches_registered']).lower()}`",
                f"- raw_alignment_complete: `{str(basis_summary['raw_alignment_complete']).lower()}`",
                f"- aggregate_counts: files=`{basis_summary['raw_root_file_count']}`, archives=`{basis_summary['raw_root_archive_count']}`, spreadsheets=`{basis_summary['raw_root_spreadsheet_count']}`, selected_candidate=`{basis_summary['selected_candidate_count']}`, business_members=`{basis_summary['business_member_count']}`",
                "",
                "## Decision Boundary",
                "",
                "- This phase prepares the owner or authorized-delegate decision gate only.",
                "- No active owner decision is recorded by this phase.",
                "- Public member hash backfill, lineage full check, official report release, GitHub upload, app reinstall and business execution remain blocked.",
                "- The public repository does not include raw file names, raw hashes, member names, sheet names, field/header plaintext, row values, business values, private diagnostics, source documents, office workbooks or credentials.",
                "",
            ]
        ),
    )
    _write_text(
        DECISION_REQUEST_PATH,
        "\n".join(
            [
                "# Owner Decision Request",
                "",
                "Choose exactly one public-safe decision code when ready:",
                "",
                "1. `confirm_current_container_as_authoritative`",
                "2. `register_corrected_source_package`",
                "3. `keep_pending`",
                "",
                "Required safe reply fields: `decision_code`, `actor_role`, `actor_ref`, `decision_time`, and a short reason or confirmation scope.",
                "",
                "Do not paste raw file names, raw hashes, workbook contents, PDF text, sheet names, field/header plaintext, row/cell values, bank details, contract contents, payroll/tax data or credentials into the public repository.",
                "",
            ]
        ),
    )
    _write_text(
        GO_NO_GO_RECORD_PATH,
        "\n".join(
            [
                "# Go/No-Go Record",
                "",
                f"- decision: `{go_no_go['decision']}`",
                f"- owner_decision_intake_ready: `{str(go_no_go['owner_decision_intake_ready']).lower()}`",
                f"- owner_decision_supplied: `{str(go_no_go['owner_decision_supplied']).lower()}`",
                f"- raw_alignment_complete: `{str(go_no_go['raw_alignment_complete']).lower()}`",
                f"- public_member_hash_backfill_allowed: `{str(go_no_go['public_member_hash_backfill_allowed']).lower()}`",
                f"- lineage_full_check_complete: `{str(go_no_go['lineage_full_check_complete']).lower()}`",
                f"- github_upload_allowed: `{str(go_no_go['github_upload_allowed']).lower()}`",
                f"- app_reinstall_allowed: `{str(go_no_go['app_reinstall_allowed']).lower()}`",
                f"- formal_report_allowed: `{str(go_no_go['formal_report_allowed']).lower()}`",
                f"- business_execution_allowed: `{str(go_no_go['business_execution_allowed']).lower()}`",
                f"- next_required_input: `{go_no_go['next_required_input']}`",
                "",
            ]
        ),
    )
    _write_text(
        TEST_RESULTS_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 Owner Raw Source Identity Decision Test Results",
                "",
                "- status: `pending_final_validation`",
                f"- task_id: `{TASK_ID}`",
                "- focused_unit_test: `pending_final_validation`",
                "- owner_decision_validator: `pending_final_validation`",
                "- governance_validator: `pending_final_validation`",
                "- raw_private_scan: `pending_final_validation`",
                "- secret_scan: `pending_final_validation`",
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
                "| id | risk | mitigation | status |",
                "|---|---|---|---|",
                "| RAW-OWNER-001 | Owner decision could be confused with raw alignment completion | Keep NO_GO until a later application phase validates an active public-safe decision | open |",
                "| RAW-OWNER-002 | Raw names or hashes could be pasted into public decision records | Validator rejects forbidden keys, local source tokens and hash-like values | controlled |",
                "| RAW-OWNER-003 | GitHub upload or app reinstall could proceed before source identity is resolved | Go/No-Go blocks upload and app reinstall | blocked |",
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
                "1. Revert the local commit that adds `V014_OWNER_RAW_SOURCE_IDENTITY_DECISION` evidence.",
                "2. Remove metadata copies under `KMFA/metadata/quality/` and `KMFA/metadata/approvals/` for this phase.",
                "3. Keep the prior `V014_RAW_ALIGNMENT_REMEDIATION` NO_GO state active.",
                "4. Do not modify the raw inbox during rollback.",
                "",
            ]
        ),
    )


def generate(*, generated_at: str | None = None) -> dict[str, Any]:
    timestamp = _now(generated_at)
    raw_manifest = _read_json(RAW_ALIGNMENT_MANIFEST_PATH)
    raw_go_no_go = _read_json(RAW_ALIGNMENT_GO_NO_GO_PATH)
    basis_summary = _basis_summary(raw_manifest, raw_go_no_go)
    contract = _intake_contract(timestamp)
    packet = _decision_packet(timestamp, basis_summary)
    go_no_go = _go_no_go()
    manifest = _manifest(
        generated_at=timestamp,
        basis_summary=basis_summary,
        contract=contract,
        packet=packet,
        go_no_go=go_no_go,
    )

    _write_json(INTAKE_CONTRACT_PATH, contract)
    _write_json(METADATA_CONTRACT_PATH, contract)
    _write_json(DECISION_PACKET_PATH, packet)
    _write_json(METADATA_PACKET_PATH, packet)
    for decision_code in ALLOWED_DECISION_CODES:
        _write_json(TEMPLATES_DIR / f"{decision_code}_template.json", _template(decision_code))
    _write_json(GO_NO_GO_PATH, go_no_go)
    _write_json(METADATA_GO_NO_GO_PATH, go_no_go)
    _write_json(MANIFEST_PATH, manifest)
    _write_json(METADATA_MANIFEST_PATH, manifest)
    _write_human_files(timestamp, basis_summary, go_no_go)
    return manifest


def main() -> int:
    manifest = generate()
    print(
        "Generated KMFA v0.1.4 owner raw source identity decision intake "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"owner_decision_supplied={str(manifest['go_no_go']['owner_decision_supplied']).lower()})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
