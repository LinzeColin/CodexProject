#!/usr/bin/env python3
"""Validate KMFA v0.1.4 owner raw source identity decision intake evidence."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.v014_owner_raw_source_identity_decision import (  # noqa: E402
    ACCEPTANCE_ID,
    ALLOWED_ACTOR_ROLES,
    ALLOWED_DECISION_CODES,
    CONTRACT_SCHEMA_VERSION,
    CURRENT_GATE,
    DECISION_PACKET_PATH,
    DECISION_REQUEST_PATH,
    DECISION_SCHEMA_VERSION,
    GO_NO_GO_PATH,
    GO_NO_GO_RECORD_PATH,
    INTAKE_CONTRACT_PATH,
    MANIFEST_PATH,
    METADATA_CONTRACT_PATH,
    METADATA_GO_NO_GO_PATH,
    METADATA_MANIFEST_PATH,
    METADATA_PACKET_PATH,
    NEXT_RECOMMENDED_PHASE,
    PACKET_SCHEMA_VERSION,
    PHASE_ID,
    REPORT_PATH,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
    SCHEMA_VERSION,
    STATUS,
    TASK_ID,
    TEMPLATE_SCHEMA_VERSION,
    TEMPLATES_DIR,
    TEST_RESULTS_PATH,
)


FALSE_REQUIRED_DECISION_FLAGS = (
    "raw_business_data_committed",
    "raw_filename_committed",
    "raw_hash_committed",
    "private_diagnostic_committed",
    "public_hash_backfill_performed",
    "raw_alignment_complete_claimed_by_intake",
    "lineage_full_check_performed",
    "formal_report_performed",
    "github_upload_performed",
    "app_reinstall_performed",
    "business_execution_performed",
)
FORBIDDEN_PUBLIC_KEYS = {
    "actual_package_sha256",
    "expected_package_sha256",
    "member_sha256",
    "member_name_sha256",
    "raw_value",
    "normalized_value",
    "plaintext_content",
    "full_file_text",
    "raw_file_bytes",
    "raw_filename",
    "zip_member_name",
    "sheet_name",
    "bank_account_number",
    "identity_document_number",
    "password",
    "token",
    "api_key",
    "private_key",
}
FORBIDDEN_PUBLIC_TEXT = (
    "KMFA_MetaData",
    "/Users/linzezhang/Downloads",
    ".xlsx",
    ".xls",
    ".zip",
    ".pdf",
    ".sqlite",
    ".db",
    "actual_package_sha256",
    "expected_package_sha256",
    "member_sha256",
    "member_name_sha256",
    "private_ref://",
    "raw path",
    "raw filename",
)
SECRET_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)\b(password|passwd|secret|api" + r"_key|token)\s*=\s*[^\s,;]{8,}"),
)
SHA256_VALUE = re.compile(r"\b[a-f0-9]{64}\b")
FORBIDDEN_TRACKED_SUFFIXES = (
    ".zip",
    ".xlsx",
    ".xls",
    ".xlsm",
    ".pdf",
    ".sqlite",
    ".sqlite3",
    ".sqlite-shm",
    ".sqlite-wal",
    ".db",
)


class ValidationError(Exception):
    pass


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ValidationError(f"missing JSON file: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValidationError(f"{path} must contain a JSON object")
    return value


def git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise ValidationError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def walk_forbidden_keys(value: Any, errors: list[str], path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_PUBLIC_KEYS:
                errors.append(f"forbidden public metadata key {key!r} at {path}")
            walk_forbidden_keys(child, errors, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            walk_forbidden_keys(child, errors, f"{path}[{index}]")


def check_public_text(path: Path, errors: list[str]) -> None:
    require(path.exists(), f"missing public evidence: {path}", errors)
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8", errors="ignore")
    lower = text.lower()
    for forbidden in FORBIDDEN_PUBLIC_TEXT:
        require(forbidden.lower() not in lower, f"forbidden public text {forbidden!r} in {path}", errors)
    require(SHA256_VALUE.search(text) is None, f"raw/hash-like 64 hex value found in {path}", errors)
    for pattern in SECRET_PATTERNS:
        require(pattern.search(text) is None, f"secret-like token found in {path}: {pattern.pattern}", errors)


def _require_non_empty_string(payload: dict[str, Any], key: str, errors: list[str], label: str) -> None:
    require(isinstance(payload.get(key), str) and bool(str(payload[key]).strip()), f"{label}.{key} must be non-empty", errors)


def validate_owner_decision_payload(decision: dict[str, Any]) -> str:
    errors: list[str] = []
    walk_forbidden_keys(decision, errors)
    require(decision.get("record_type") == "v014_raw_source_identity_owner_decision", "decision record_type mismatch", errors)
    require(decision.get("schema_version") == DECISION_SCHEMA_VERSION, "decision schema mismatch", errors)
    require(decision.get("project_id") == "KMFA", "decision project_id mismatch", errors)
    require(decision.get("phase_id") == PHASE_ID, "decision phase_id mismatch", errors)
    require(decision.get("current_gate") == CURRENT_GATE, "decision current_gate mismatch", errors)
    decision_code = decision.get("decision_code")
    require(decision_code in ALLOWED_DECISION_CODES, "decision_code is not allowed", errors)
    require(decision.get("actor_role") in ALLOWED_ACTOR_ROLES, "actor_role must be owner or authorized_delegate", errors)
    for key in ("actor_ref", "decision_time", "source_identity_scope"):
        _require_non_empty_string(decision, key, errors, "decision")
    require(decision.get("source_identity_scope") == "raw_container_identity_only", "decision source_identity_scope mismatch", errors)
    basis_refs = decision.get("basis_refs")
    require(isinstance(basis_refs, list) and bool(basis_refs), "decision.basis_refs must be a non-empty list", errors)
    for key in FALSE_REQUIRED_DECISION_FLAGS:
        require(decision.get(key) is False, f"decision.{key} must be false", errors)

    if decision_code == "confirm_current_container_as_authoritative":
        require(decision.get("raw_container_authoritative_confirmed") is True, "confirm decision must confirm current container", errors)
        _require_non_empty_string(decision, "confirmation_scope", errors, "decision")
    elif decision_code == "register_corrected_source_package":
        _require_non_empty_string(decision, "corrected_package_private_ref", errors, "decision")
        require(decision.get("current_container_superseded") is True, "corrected package decision must supersede current container", errors)
    elif decision_code == "keep_pending":
        _require_non_empty_string(decision, "reason_pending", errors, "decision")
        _require_non_empty_string(decision, "next_review_trigger", errors, "decision")

    encoded = json.dumps(decision, ensure_ascii=False)
    require(SHA256_VALUE.search(encoded) is None, "decision must not contain raw/hash-like 64 hex values", errors)
    for forbidden in FORBIDDEN_PUBLIC_TEXT:
        require(forbidden.lower() not in encoded.lower(), f"decision contains forbidden text {forbidden!r}", errors)
    if errors:
        print("FAIL: KMFA v0.1.4 owner raw source identity decision record validation failed")
        print("\n".join(f"- {error}" for error in errors))
        raise SystemExit(1)
    return str(decision_code)


def validate_owner_decision_record(path: Path) -> str:
    return validate_owner_decision_payload(read_json(path))


def _validate_contract(contract: dict[str, Any], packet: dict[str, Any], errors: list[str]) -> None:
    walk_forbidden_keys(contract, errors)
    require(contract.get("record_type") == "v014_raw_source_identity_owner_decision_intake_contract", "contract record_type mismatch", errors)
    require(contract.get("schema_version") == CONTRACT_SCHEMA_VERSION, "contract schema mismatch", errors)
    require(contract.get("project_id") == "KMFA", "contract project_id mismatch", errors)
    require(contract.get("phase_id") == PHASE_ID, "contract phase_id mismatch", errors)
    require(contract.get("current_gate") == CURRENT_GATE, "contract gate mismatch", errors)
    require(contract.get("readiness_status") == "ready_for_owner_decision_record", "contract readiness mismatch", errors)
    require(contract.get("decision_record_status") == "no_owner_decision_recorded", "contract decision status mismatch", errors)
    require(contract.get("accepted_record_type") == "v014_raw_source_identity_owner_decision", "contract accepted record mismatch", errors)
    require(set(contract.get("allowed_decision_codes") or []) == set(ALLOWED_DECISION_CODES), "contract allowed decisions mismatch", errors)
    require(set(contract.get("allowed_actor_roles") or []) == set(ALLOWED_ACTOR_ROLES), "contract actor roles mismatch", errors)
    for key in (
        "raw_or_plaintext_allowed",
        "raw_hash_allowed",
        "private_diagnostic_allowed_in_public_repo",
        "public_hash_backfill_allowed_by_intake",
        "raw_alignment_complete_allowed_by_intake",
        "lineage_full_check_allowed_by_intake",
        "formal_report_allowed_by_intake",
        "github_upload_allowed_by_intake",
        "app_reinstall_allowed_by_intake",
        "business_execution_allowed_by_intake",
    ):
        require(contract.get(key) is False, f"contract.{key} must be false", errors)
    require(packet.get("current_gate") == contract.get("current_gate"), "packet/contract gate mismatch", errors)
    require(set(packet.get("allowed_decision_codes") or []) == set(contract.get("allowed_decision_codes") or []), "packet/contract allowed decisions mismatch", errors)


def _validate_templates(errors: list[str]) -> None:
    for decision_code in ALLOWED_DECISION_CODES:
        path = TEMPLATES_DIR / f"{decision_code}_template.json"
        template = read_json(path)
        walk_forbidden_keys(template, errors)
        require(template.get("record_type") == "v014_raw_source_identity_owner_decision_template", f"{path} record_type mismatch", errors)
        require(template.get("schema_version") == TEMPLATE_SCHEMA_VERSION, f"{path} schema mismatch", errors)
        require(template.get("decision_code") == decision_code, f"{path} decision code mismatch", errors)
        require(template.get("not_decision_record") is True, f"{path} must be marked not_decision_record", errors)
        require(template.get("current_gate") == CURRENT_GATE, f"{path} gate mismatch", errors)
        require(template.get("output_record_type_after_activation") == "v014_raw_source_identity_owner_decision", f"{path} output record mismatch", errors)
        for key in FALSE_REQUIRED_DECISION_FLAGS:
            require(template.get(key) is False, f"{path}.{key} must be false", errors)
        required = set(template.get("required_fill_fields") or [])
        require({"actor_role", "actor_ref", "decision_time"}.issubset(required), f"{path} required fields incomplete", errors)


def validate_v014_owner_raw_source_identity_decision(
    manifest_path: Path = MANIFEST_PATH,
    *,
    decision_path: Path | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    manifest = read_json(manifest_path)
    metadata_manifest = read_json(METADATA_MANIFEST_PATH)
    go_no_go = read_json(GO_NO_GO_PATH)
    metadata_go_no_go = read_json(METADATA_GO_NO_GO_PATH)
    packet = read_json(DECISION_PACKET_PATH)
    metadata_packet = read_json(METADATA_PACKET_PATH)
    contract = read_json(INTAKE_CONTRACT_PATH)
    metadata_contract = read_json(METADATA_CONTRACT_PATH)

    require(metadata_manifest == manifest, "metadata manifest copy mismatch", errors)
    require(metadata_go_no_go == go_no_go, "metadata go/no-go copy mismatch", errors)
    require(metadata_packet == packet, "metadata packet copy mismatch", errors)
    require(metadata_contract == contract, "metadata contract copy mismatch", errors)
    require(manifest.get("schema_version") == SCHEMA_VERSION, "manifest schema mismatch", errors)
    require(manifest.get("project_id") == "KMFA", "manifest project_id mismatch", errors)
    require(manifest.get("version") == "0.1.4", "manifest version mismatch", errors)
    require(manifest.get("phase_id") == PHASE_ID, "manifest phase_id mismatch", errors)
    require(manifest.get("task_id") == TASK_ID, "manifest task_id mismatch", errors)
    require(manifest.get("acceptance_ids") == [ACCEPTANCE_ID], "acceptance ids mismatch", errors)
    require(manifest.get("status") == STATUS, "manifest status mismatch", errors)
    require(manifest.get("go_no_go") == go_no_go, "embedded go/no-go mismatch", errors)
    require(packet.get("schema_version") == PACKET_SCHEMA_VERSION, "packet schema mismatch", errors)
    require(packet.get("packet_status") == "ready_for_owner_or_authorized_decision", "packet status mismatch", errors)

    basis = manifest.get("basis_summary", {})
    require(basis.get("source_phase_id") == "V014_RAW_ALIGNMENT_REMEDIATION", "basis source phase mismatch", errors)
    require(basis.get("source_decision") == "NO_GO", "basis source decision mismatch", errors)
    require(basis.get("business_shape_matches_expected_a0") is True, "basis business shape mismatch", errors)
    require(basis.get("package_hash_matches_registered") is False, "basis package hash match must be false", errors)
    require(basis.get("package_size_matches_registered") is False, "basis package size match must be false", errors)
    require(basis.get("raw_alignment_complete") is False, "basis raw alignment complete must be false", errors)
    require(basis.get("public_member_hash_backfill_allowed") is False, "basis hash backfill must be false", errors)
    require(basis.get("business_member_count") == 9, "basis business member count mismatch", errors)

    _validate_contract(contract, packet, errors)
    _validate_templates(errors)

    intake = manifest.get("owner_decision_intake", {})
    require(intake.get("readiness_status") == "ready_for_owner_decision_record", "intake readiness mismatch", errors)
    require(intake.get("decision_record_status") == "no_owner_decision_recorded", "intake decision status mismatch", errors)
    require(set(intake.get("allowed_decision_codes") or []) == set(ALLOWED_DECISION_CODES), "intake allowed decisions mismatch", errors)
    require(intake.get("owner_decision_supplied_by_this_phase") is False, "owner decision supplied flag must be false", errors)
    require(intake.get("raw_alignment_complete_claimed_by_this_phase") is False, "raw alignment claim must be false", errors)
    require(intake.get("public_hash_backfill_allowed_by_this_phase") is False, "hash backfill allowed flag must be false", errors)

    scope = manifest.get("phase_scope_controls", {})
    require(scope.get("current_phase_only") is True, "scope current_phase_only must be true", errors)
    require(scope.get("owner_decision_intake_only") is True, "scope owner_decision_intake_only must be true", errors)
    for key in (
        "active_owner_decision_record_created",
        "raw_inbox_read_performed_by_this_phase",
        "raw_inbox_list_performed_by_this_phase",
        "raw_inbox_stat_performed_by_this_phase",
        "raw_inbox_hash_performed_by_this_phase",
        "raw_inbox_mutated_by_this_phase",
        "public_hash_backfill_performed",
        "lineage_full_check_performed",
        "formal_report_performed",
        "github_upload_performed",
        "app_reinstall_performed",
        "business_execution_performed",
        "next_phase_started",
    ):
        require(scope.get(key) is False, f"scope.{key} must be false", errors)

    public_safety = manifest.get("public_repo_safety", {})
    require(public_safety.get("public_safe_decision_codes_only") is True, "public safety decision-code flag mismatch", errors)
    for key, value in public_safety.items():
        if key == "public_safe_decision_codes_only":
            continue
        require(value is False, f"public_repo_safety.{key} must be false", errors)

    require(go_no_go.get("decision") == "NO_GO", "go/no-go decision mismatch", errors)
    require(go_no_go.get("owner_decision_intake_ready") is True, "go/no-go intake flag mismatch", errors)
    require(go_no_go.get("owner_decision_supplied") is False, "go/no-go supplied flag must be false", errors)
    require("RAW_SOURCE_IDENTITY_OWNER_DECISION_NOT_SUPPLIED" in go_no_go.get("blocker_ids", []), "missing owner decision blocker", errors)
    require("OWNER_DECISION_INTAKE_READY" in go_no_go.get("resolved_blocker_ids", []), "missing intake-ready resolved marker", errors)
    require(go_no_go.get("next_recommended_phase") == NEXT_RECOMMENDED_PHASE, "go/no-go next phase mismatch", errors)
    for key in (
        "raw_alignment_complete",
        "public_member_hash_backfill_allowed",
        "lineage_full_check_complete",
        "github_upload_allowed",
        "app_reinstall_allowed",
        "formal_report_allowed",
        "business_execution_allowed",
    ):
        require(go_no_go.get(key) is False, f"go_no_go.{key} must be false", errors)
    require(manifest.get("github_upload_performed") is False, "manifest github upload must be false", errors)

    for ref in manifest.get("evidence_refs", []):
        check_public_text(Path(ref), errors)
    for path in (
        MANIFEST_PATH,
        GO_NO_GO_PATH,
        DECISION_PACKET_PATH,
        INTAKE_CONTRACT_PATH,
        METADATA_MANIFEST_PATH,
        METADATA_GO_NO_GO_PATH,
        METADATA_PACKET_PATH,
        METADATA_CONTRACT_PATH,
        REPORT_PATH,
        DECISION_REQUEST_PATH,
        GO_NO_GO_RECORD_PATH,
        TEST_RESULTS_PATH,
        RISK_REGISTER_PATH,
        ROLLBACK_PATH,
        *[TEMPLATES_DIR / f"{decision_code}_template.json" for decision_code in ALLOWED_DECISION_CODES],
    ):
        check_public_text(path, errors)

    tracked_files = git_output(["ls-files", "KMFA"]).splitlines()
    forbidden = [
        path for path in tracked_files if path.lower().endswith(FORBIDDEN_TRACKED_SUFFIXES) or ".codex_private_runtime/" in path
    ]
    require(not forbidden, "forbidden raw/private tracked artifacts: " + ", ".join(forbidden[:20]), errors)
    require("codex/kmfa" in git_output(["status", "--short", "--branch"]), "git status must be on codex/kmfa", errors)

    if decision_path is not None:
        validate_owner_decision_record(decision_path)

    if errors:
        raise ValidationError("\n".join(f"- {error}" for error in errors))
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.4 owner raw source identity decision intake.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--decision", type=Path)
    args = parser.parse_args(argv)
    try:
        manifest = validate_v014_owner_raw_source_identity_decision(args.manifest, decision_path=args.decision)
    except ValidationError as exc:
        print("FAIL: KMFA v0.1.4 owner raw source identity decision validation failed")
        print(exc)
        return 1
    print(
        "PASS: KMFA v0.1.4 owner raw source identity decision intake validated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"intake_ready={str(manifest['go_no_go']['owner_decision_intake_ready']).lower()}, "
        f"owner_decision_supplied={str(manifest['go_no_go']['owner_decision_supplied']).lower()}, "
        f"github_upload={str(manifest['go_no_go']['github_upload_allowed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
