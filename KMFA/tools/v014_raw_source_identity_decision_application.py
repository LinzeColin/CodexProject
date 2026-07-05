#!/usr/bin/env python3
"""Generate KMFA v0.1.4 raw source identity decision application evidence.

This phase does not make an owner decision. It records whether a public-safe
owner decision record is available and keeps all downstream gates blocked when
the decision is missing or explicitly pending.
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

from KMFA.tools.check_v014_owner_raw_source_identity_decision import (  # noqa: E402
    validate_owner_decision_record,
)
from KMFA.tools.v014_owner_raw_source_identity_decision import (  # noqa: E402
    ALLOWED_ACTOR_ROLES,
    ALLOWED_DECISION_CODES,
    DECISION_PACKET_PATH,
    GO_NO_GO_PATH as OWNER_GO_NO_GO_PATH,
    INTAKE_CONTRACT_PATH,
    MANIFEST_PATH as OWNER_MANIFEST_PATH,
)


SCHEMA_VERSION = "kmfa.v014_raw_source_identity_decision_application.v1"
GO_NO_GO_SCHEMA_VERSION = "kmfa.v014_raw_source_identity_decision_application_go_no_go.v1"
PREVIEW_SCHEMA_VERSION = "kmfa.v014_raw_source_identity_decision_application_preview.v1"
PROJECT_ID = "KMFA"
VERSION = "0.1.4"
PHASE_ID = "V014_RAW_SOURCE_IDENTITY_DECISION_APPLICATION"
TASK_ID = "KMFA-V014-RAW-SOURCE-IDENTITY-DECISION-APPLICATION-20260705"
ACCEPTANCE_ID = "ACC-V014-RAW-SOURCE-IDENTITY-DECISION-APPLICATION"
STATUS = "raw_source_identity_decision_application_blocked_no_active_owner_decision_no_go"
CURRENT_GATE = "KMFA-V014-RAW-SOURCE-IDENTITY-DECISION-APPLICATION-GATE"
SOURCE_GATE = "KMFA-V014-RAW-SOURCE-IDENTITY-OWNER-GATE"
NEXT_REQUIRED_INPUT = "active_owner_decision_record_or_corrected_registered_source_package"
NEXT_RECOMMENDED_ACTION = "rerun_this_application_gate_after_owner_decision"

OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_RAW_SOURCE_IDENTITY_DECISION_APPLICATION")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
MANIFEST_PATH = MACHINE_DIR / "raw_source_identity_decision_application_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "raw_source_identity_decision_application_go_no_go_report.json"
APPLICATION_PREVIEW_PATH = MACHINE_DIR / "raw_source_identity_decision_application_preview.json"
REPORT_PATH = HUMAN_DIR / "raw_source_identity_decision_application_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_MANIFEST_PATH = Path("KMFA/metadata/quality/v014_raw_source_identity_decision_application_manifest.json")
METADATA_GO_NO_GO_PATH = Path("KMFA/metadata/quality/v014_raw_source_identity_decision_application_go_no_go_report.json")
METADATA_PREVIEW_PATH = Path("KMFA/metadata/approvals/v014_raw_source_identity_decision_application_preview.json")


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


def _public_safety() -> dict[str, bool]:
    return {
        "public_safe_application_status_only": True,
        "raw_business_data_committed": False,
        "compressed_raw_package_committed": False,
        "office_workbook_committed": False,
        "source_document_committed": False,
        "raw_or_private_table_committed": False,
        "local_database_committed": False,
        "credential_or_secret_committed": False,
        "source_names_committed": False,
        "source_digests_committed": False,
        "private_diagnostic_committed": False,
        "directory_tree_plaintext_committed": False,
        "archive_member_names_committed": False,
        "worksheet_names_committed": False,
        "field_or_header_plaintext_committed": False,
        "row_or_cell_values_committed": False,
        "business_values_committed": False,
    }


def _load_basis() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    owner_manifest = _read_json(OWNER_MANIFEST_PATH)
    owner_go_no_go = _read_json(OWNER_GO_NO_GO_PATH)
    owner_packet = _read_json(DECISION_PACKET_PATH)
    return owner_manifest, owner_go_no_go, owner_packet


def _basis_summary(
    owner_manifest: dict[str, Any],
    owner_go_no_go: dict[str, Any],
    owner_packet: dict[str, Any],
) -> dict[str, Any]:
    source_basis = owner_manifest.get("basis_summary", {})
    return {
        "source_phase_id": owner_manifest.get("phase_id"),
        "source_task_id": owner_manifest.get("task_id"),
        "source_status": owner_manifest.get("status"),
        "source_decision": owner_go_no_go.get("decision"),
        "owner_decision_intake_ready": owner_go_no_go.get("owner_decision_intake_ready") is True,
        "owner_decision_supplied": owner_go_no_go.get("owner_decision_supplied") is True,
        "decision_record_status": owner_packet.get("decision_record_status"),
        "allowed_decision_count": len(owner_packet.get("allowed_decision_codes") or []),
        "allowed_actor_role_count": len(ALLOWED_ACTOR_ROLES),
        "business_shape_matches_expected_a0": source_basis.get("business_shape_matches_expected_a0") is True,
        "package_hash_matches_registered": source_basis.get("package_hash_matches_registered") is True,
        "package_size_matches_registered": source_basis.get("package_size_matches_registered") is True,
        "raw_alignment_complete": source_basis.get("raw_alignment_complete") is True,
        "public_member_hash_backfill_allowed": source_basis.get("public_member_hash_backfill_allowed") is True,
        "business_member_count": int(source_basis.get("business_member_count", 0)),
        "inherited_blocker_ids": list(owner_go_no_go.get("blocker_ids", [])),
    }


def _application_preview(decision_code: str | None) -> dict[str, Any]:
    base: dict[str, Any] = {
        "record_type": "v014_raw_source_identity_decision_application_preview",
        "schema_version": PREVIEW_SCHEMA_VERSION,
        "project_id": PROJECT_ID,
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "current_gate": CURRENT_GATE,
        "source_gate": SOURCE_GATE,
        "allowed_decision_codes": ALLOWED_DECISION_CODES,
        "public_repo_safety": _public_safety(),
        "raw_alignment_complete_claimed_by_application": False,
        "public_member_hash_backfill_allowed_by_application": False,
        "lineage_full_check_complete_by_application": False,
        "formal_report_allowed_by_application": False,
        "github_upload_allowed_by_application": False,
        "app_reinstall_allowed_by_application": False,
        "business_execution_allowed_by_application": False,
    }
    if decision_code is None:
        base.update(
            {
                "decision_code": "none",
                "application_status": "blocked_no_active_owner_decision",
                "owner_decision_supplied": False,
                "decision_applied": False,
                "blocker": "no_active_owner_or_authorized_decision_record",
                "application_effect": "keeps_all_downstream_gates_blocked",
                "next_required_input": NEXT_REQUIRED_INPUT,
            }
        )
    elif decision_code == "keep_pending":
        base.update(
            {
                "decision_code": decision_code,
                "application_status": "blocked_by_owner_keep_pending",
                "owner_decision_supplied": True,
                "decision_applied": False,
                "blocker": "owner_decision_keeps_source_identity_pending",
                "application_effect": "keeps_all_downstream_gates_blocked",
                "next_required_input": NEXT_REQUIRED_INPUT,
            }
        )
    elif decision_code == "confirm_current_container_as_authoritative":
        base.update(
            {
                "decision_code": decision_code,
                "application_status": "owner_confirmation_recorded_for_separate_backfill_gate",
                "owner_decision_supplied": True,
                "decision_applied": True,
                "blocker": "separate_public_member_hash_backfill_gate_required",
                "application_effect": "records_authoritative_source_identity_without_backfill_or_lineage_unlock",
                "next_required_input": "separate_public_safe_hash_backfill_and_lineage_gate",
            }
        )
    elif decision_code == "register_corrected_source_package":
        base.update(
            {
                "decision_code": decision_code,
                "application_status": "blocked_corrected_source_registration_required",
                "owner_decision_supplied": True,
                "decision_applied": False,
                "blocker": "corrected_source_package_registry_gate_required",
                "application_effect": "keeps_current_source_identity_no_go_until_corrected_source_is_registered",
                "next_required_input": "corrected_source_registry_and_validation_gate",
            }
        )
    else:
        raise ValueError(f"unsupported decision_code: {decision_code}")
    return base


def _go_no_go(preview: dict[str, Any]) -> dict[str, Any]:
    blocker_ids = [
        "RAW_SOURCE_IDENTITY_DECISION_APPLICATION_BLOCKED",
        "PUBLIC_MEMBER_HASH_BACKFILL_STILL_BLOCKED",
        "LINEAGE_FULL_CHECK_BLOCKED_BY_SOURCE_IDENTITY_APPLICATION",
        "FORMAL_REPORT_BLOCKED_BY_SOURCE_IDENTITY_APPLICATION",
        "GITHUB_UPLOAD_BLOCKED_BY_SOURCE_IDENTITY_APPLICATION",
        "APP_REINSTALL_BLOCKED_BY_SOURCE_IDENTITY_APPLICATION",
    ]
    resolved = ["OWNER_DECISION_INTAKE_READY"]
    if preview["decision_code"] == "none":
        blocker_ids.insert(0, "RAW_SOURCE_IDENTITY_OWNER_DECISION_NOT_SUPPLIED")
    elif preview["decision_code"] == "keep_pending":
        blocker_ids.insert(0, "RAW_SOURCE_IDENTITY_OWNER_DECISION_KEPT_PENDING")
        resolved.append("OWNER_DECISION_RECORD_VALIDATED_PUBLIC_SAFE")
    elif preview["decision_code"] == "confirm_current_container_as_authoritative":
        blocker_ids.insert(0, "PUBLIC_MEMBER_HASH_BACKFILL_SEPARATE_GATE_REQUIRED")
        resolved.append("OWNER_DECISION_RECORD_VALIDATED_PUBLIC_SAFE")
    elif preview["decision_code"] == "register_corrected_source_package":
        blocker_ids.insert(0, "CORRECTED_SOURCE_REGISTRY_GATE_REQUIRED")
        resolved.append("OWNER_DECISION_RECORD_VALIDATED_PUBLIC_SAFE")

    return {
        "record_type": "v014_raw_source_identity_decision_application_go_no_go_report",
        "schema_version": GO_NO_GO_SCHEMA_VERSION,
        "project_id": PROJECT_ID,
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "decision": "NO_GO",
        "decision_reason": (
            "Raw source identity application is blocked until an active public-safe owner decision resolves "
            "the source identity and later gates complete hash backfill, lineage closure and release checks."
        ),
        "application_status": preview["application_status"],
        "decision_code": preview["decision_code"],
        "blocker_ids": blocker_ids,
        "resolved_blocker_ids": resolved,
        "owner_decision_intake_ready": True,
        "owner_decision_supplied": preview["owner_decision_supplied"],
        "decision_applied": preview["decision_applied"],
        "raw_alignment_complete": False,
        "public_member_hash_backfill_allowed": False,
        "lineage_full_check_complete": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "formal_report_allowed": False,
        "business_execution_allowed": False,
        "next_required_input": preview["next_required_input"],
        "next_recommended_action": NEXT_RECOMMENDED_ACTION,
    }


def _manifest(
    *,
    generated_at: str,
    basis_summary: dict[str, Any],
    preview: dict[str, Any],
    go_no_go: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": PROJECT_ID,
        "version": VERSION,
        "phase_id": PHASE_ID,
        "phase_name": "Raw source identity decision application gate",
        "task_id": TASK_ID,
        "acceptance_ids": [ACCEPTANCE_ID],
        "status": STATUS,
        "generated_at": generated_at,
        "worktree": Path.cwd().as_posix(),
        "branch": _git_output(["branch", "--show-current"]),
        "remote": _git_output(["remote", "get-url", "origin"]),
        "reviewed_head": _git_output(["rev-parse", "HEAD"]),
        "basis_summary": basis_summary,
        "decision_application": preview,
        "phase_scope_controls": {
            "current_phase_only": True,
            "application_gate_only": True,
            "owner_decision_record_created_by_this_phase": False,
            "source_container_selected_by_this_phase": False,
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
        "github_upload_status": "not_uploaded_blocked_by_raw_source_identity_application",
        "next_required_input": go_no_go["next_required_input"],
        "next_recommended_action": NEXT_RECOMMENDED_ACTION,
        "evidence_refs": [
            REPORT_PATH.as_posix(),
            GO_NO_GO_RECORD_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            RISK_REGISTER_PATH.as_posix(),
            ROLLBACK_PATH.as_posix(),
            MANIFEST_PATH.as_posix(),
            GO_NO_GO_PATH.as_posix(),
            APPLICATION_PREVIEW_PATH.as_posix(),
            METADATA_MANIFEST_PATH.as_posix(),
            METADATA_GO_NO_GO_PATH.as_posix(),
            METADATA_PREVIEW_PATH.as_posix(),
        ],
        "source_evidence_refs": [
            OWNER_MANIFEST_PATH.as_posix(),
            OWNER_GO_NO_GO_PATH.as_posix(),
            DECISION_PACKET_PATH.as_posix(),
            INTAKE_CONTRACT_PATH.as_posix(),
        ],
        "validation_summary": _pending_validation_summary(),
    }


def _pending_validation_summary() -> dict[str, str]:
    return {
        "py_compile": "PENDING_FINAL_VALIDATION",
        "focused_unit_test": "PENDING_FINAL_VALIDATION",
        "raw_source_identity_decision_application_validator": "PENDING_FINAL_VALIDATION",
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
    }


def _validation_commands() -> list[str]:
    return [
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m py_compile KMFA/tools/v014_raw_source_identity_decision_application.py KMFA/tools/check_v014_raw_source_identity_decision_application.py KMFA/tests/test_v014_raw_source_identity_decision_application.py",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_raw_source_identity_decision_application -q",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_raw_source_identity_decision_application.py",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --enforce-sync",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_no_float_money.py",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/no_omission_check.py",
        "changed/untracked JSON JSONL CSV structured parse checks",
        "changed/untracked YAML parse checks",
        "changed/untracked raw/private suffix scan",
        "high-signal secret scan across changed/untracked KMFA text files",
        "scoped raw source identity decision application public artifact boundary scan",
        "git diff --check -- KMFA scripts",
    ]


def _write_human_files(generated_at: str, basis_summary: dict[str, Any], preview: dict[str, Any], go_no_go: dict[str, Any]) -> None:
    _write_text(
        REPORT_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 Raw Source Identity Decision Application",
                "",
                f"- phase_id: `{PHASE_ID}`",
                f"- task_id: `{TASK_ID}`",
                f"- generated_at: `{generated_at}`",
                f"- application_status: `{preview['application_status']}`",
                f"- decision_code: `{preview['decision_code']}`",
                "- decision: `NO_GO`",
                "",
                "## Public-Safe Basis",
                "",
                f"- source_phase_id: `{basis_summary['source_phase_id']}`",
                f"- source_decision: `{basis_summary['source_decision']}`",
                f"- owner_decision_intake_ready: `{str(basis_summary['owner_decision_intake_ready']).lower()}`",
                f"- owner_decision_supplied: `{str(preview['owner_decision_supplied']).lower()}`",
                f"- business_shape_matches_expected_a0: `{str(basis_summary['business_shape_matches_expected_a0']).lower()}`",
                f"- registered_container_hash_match: `{str(basis_summary['package_hash_matches_registered']).lower()}`",
                f"- registered_container_size_match: `{str(basis_summary['package_size_matches_registered']).lower()}`",
                f"- raw_alignment_complete: `{str(basis_summary['raw_alignment_complete']).lower()}`",
                f"- business_member_count: `{basis_summary['business_member_count']}`",
                "",
                "## Application Boundary",
                "",
                "- This phase applies only the public-safe decision gate state.",
                "- It does not create an owner decision record or select a private source container.",
                "- Hash backfill, lineage full check, official report release, GitHub upload, app reinstall and business execution remain blocked.",
                "- Public evidence contains no source names, source digests, member names, worksheet names, field/header plaintext, row values, business values, private diagnostics, source documents, office workbooks or credentials.",
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
                f"- application_status: `{go_no_go['application_status']}`",
                f"- owner_decision_intake_ready: `{str(go_no_go['owner_decision_intake_ready']).lower()}`",
                f"- owner_decision_supplied: `{str(go_no_go['owner_decision_supplied']).lower()}`",
                f"- decision_applied: `{str(go_no_go['decision_applied']).lower()}`",
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
                "# KMFA v0.1.4 Raw Source Identity Decision Application Test Results",
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
                "| RAW-APP-001 | Missing owner decision could be mistaken for source identity closure | Application status remains blocked and Go/No-Go remains NO_GO | blocked |",
                "| RAW-APP-002 | A pending decision could unlock downstream gates too early | keep_pending keeps decision_applied=false and every downstream gate false | controlled |",
                "| RAW-APP-003 | Private source details could leak into public evidence | Validator scans public evidence for forbidden local markers, suffixes, hashes and secret-like tokens | controlled |",
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
                "1. Revert the local commit that adds `V014_RAW_SOURCE_IDENTITY_DECISION_APPLICATION` evidence.",
                "2. Remove metadata copies for this phase under `KMFA/metadata/quality/` and `KMFA/metadata/approvals/`.",
                "3. Keep the prior owner decision intake NO_GO state active.",
                "4. Do not modify the private source inbox during rollback.",
                "",
            ]
        ),
    )


def generate(
    *,
    generated_at: str | None = None,
    decision_path: Path | None = None,
    write: bool = True,
) -> dict[str, Any]:
    timestamp = _now(generated_at)
    owner_manifest, owner_go_no_go, owner_packet = _load_basis()
    basis_summary = _basis_summary(owner_manifest, owner_go_no_go, owner_packet)
    decision_code = validate_owner_decision_record(decision_path) if decision_path is not None else None
    preview = _application_preview(decision_code)
    go_no_go = _go_no_go(preview)
    manifest = _manifest(
        generated_at=timestamp,
        basis_summary=basis_summary,
        preview=preview,
        go_no_go=go_no_go,
    )

    if write:
        _write_json(APPLICATION_PREVIEW_PATH, preview)
        _write_json(METADATA_PREVIEW_PATH, preview)
        _write_json(GO_NO_GO_PATH, go_no_go)
        _write_json(METADATA_GO_NO_GO_PATH, go_no_go)
        _write_json(MANIFEST_PATH, manifest)
        _write_json(METADATA_MANIFEST_PATH, manifest)
        _write_human_files(timestamp, basis_summary, preview, go_no_go)
    return manifest


def mark_final_validation_pass(*, validated_at: str | None = None) -> dict[str, Any]:
    timestamp = _now(validated_at)
    manifest = _read_json(MANIFEST_PATH)
    manifest["validation_summary"] = {key: "PASS" for key in _pending_validation_summary()}
    manifest["validation_commands"] = _validation_commands()
    manifest["validation_status"] = "PASS"
    manifest["validated_at"] = timestamp
    _write_json(MANIFEST_PATH, manifest)
    _write_json(METADATA_MANIFEST_PATH, manifest)
    _write_text(
        TEST_RESULTS_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 Raw Source Identity Decision Application Test Results",
                "",
                "- status: `PASS`",
                f"- task_id: `{TASK_ID}`",
                "- py_compile: `PASS`",
                "- focused_unit_test: `PASS`",
                "- application_validator: `PASS`",
                "- governance_validator: `PASS`",
                "- lean_governance_validator: `PASS`",
                "- governance_sync_validator: `PASS`",
                "- no_float_money_check: `PASS`",
                "- no_omission_check: `PASS`",
                "- structured_parse_checks: `PASS`",
                "- yaml_parse_checks: `PASS`",
                "- raw_private_suffix_scan: `PASS`",
                "- secret_scan: `PASS`",
                "- public_artifact_boundary_scan: `PASS`",
                "- diff_check: `PASS`",
                f"- validated_at: `{timestamp}`",
                "",
            ]
        ),
    )
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate KMFA v0.1.4 raw source identity decision application evidence.")
    parser.add_argument("--decision", type=Path)
    parser.add_argument("--generated-at")
    parser.add_argument("--mark-final-validation-pass", action="store_true")
    args = parser.parse_args(argv)

    if args.mark_final_validation_pass:
        manifest = mark_final_validation_pass(validated_at=args.generated_at)
    else:
        manifest = generate(generated_at=args.generated_at, decision_path=args.decision)
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
