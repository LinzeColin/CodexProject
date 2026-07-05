#!/usr/bin/env python3
"""Validate KMFA v0.1.4 owner-authorized fill intake evidence."""

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

from KMFA.tools.v014_private_processed_value_source_map_owner_authorized_fill_intake import (  # noqa: E402
    ACCEPTANCE_ID,
    ALLOWED_ACTOR_ROLES,
    ALLOWED_INTAKE_ACTION_CODES,
    CONTRACT_SCHEMA_VERSION,
    CURRENT_GATE,
    DECISION_REQUEST_PATH,
    GO_NO_GO_PATH,
    GO_NO_GO_RECORD_PATH,
    GO_NO_GO_SCHEMA_VERSION,
    INTAKE_CONTRACT_PATH,
    INTAKE_PACKET_PATH,
    MANIFEST_PATH,
    METADATA_CONTRACT_PATH,
    METADATA_GO_NO_GO_PATH,
    METADATA_MANIFEST_PATH,
    METADATA_PACKET_PATH,
    METADATA_SUMMARY_PATH,
    NEXT_RECOMMENDED_PHASE,
    PACKET_SCHEMA_VERSION,
    PHASE_ID,
    PRIVATE_INTAKE_DIAGNOSTIC_PATH,
    PRIVATE_INTAKE_REQUEST_PATH,
    PRIVATE_SCHEMA_VERSION,
    REPORT_PATH,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
    SCHEMA_VERSION,
    STATUS,
    SUMMARY_PATH,
    TASK_ID,
    TEMPLATE_SCHEMA_VERSION,
    TEMPLATES_DIR,
    TEST_RESULTS_PATH,
)


FORBIDDEN_PUBLIC_KEYS = {
    "private_processed_ref",
    "raw_value",
    "normalized_value",
    "processed_value",
    "business_value",
    "source_header_text",
    "cell_value",
    "row_value",
    "plaintext_content",
    "raw_file_bytes",
    "raw_filename",
    "zip_member_name",
    "sheet_name",
    "bank_account_number",
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
    "private://",
    "private_ref://",
    "raw path",
    "raw filename",
    "sheet name",
    "cell value",
)
SECRET_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)\b(password|passwd|secret|api" + r"_key|token)\s*=\s*[^\s,;]{8,}"),
)
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


def git_check_ignore(path: Path) -> bool:
    result = subprocess.run(
        ["git", "check-ignore", "-q", str(path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return result.returncode == 0


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def walk_forbidden_public_keys(value: Any, errors: list[str], path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_PUBLIC_KEYS:
                errors.append(f"forbidden public metadata key {key!r} at {path}")
            walk_forbidden_public_keys(child, errors, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            walk_forbidden_public_keys(child, errors, f"{path}[{index}]")


def check_public_text(path: Path, errors: list[str]) -> None:
    require(path.exists(), f"missing public evidence: {path}", errors)
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8", errors="ignore")
    lower = text.lower()
    for forbidden in FORBIDDEN_PUBLIC_TEXT:
        require(forbidden.lower() not in lower, f"forbidden public text {forbidden!r} in {path}", errors)
    for pattern in SECRET_PATTERNS:
        require(pattern.search(text) is None, f"secret-like token found in {path}: {pattern.pattern}", errors)


def _validate_contract(contract: dict[str, Any], packet: dict[str, Any], errors: list[str]) -> None:
    walk_forbidden_public_keys(contract, errors)
    require(
        contract.get("record_type") == "v014_private_processed_value_source_map_owner_authorized_fill_intake_contract",
        "contract record_type mismatch",
        errors,
    )
    require(contract.get("schema_version") == CONTRACT_SCHEMA_VERSION, "contract schema mismatch", errors)
    require(contract.get("project_id") == "KMFA", "contract project mismatch", errors)
    require(contract.get("phase_id") == PHASE_ID, "contract phase mismatch", errors)
    require(contract.get("current_gate") == CURRENT_GATE, "contract gate mismatch", errors)
    require(contract.get("readiness_status") == "ready_for_owner_authorized_fill_record", "contract readiness mismatch", errors)
    require(contract.get("fill_record_status") == "no_owner_authorized_fill_record_supplied", "contract fill status mismatch", errors)
    require(
        set(contract.get("allowed_intake_action_codes") or []) == set(ALLOWED_INTAKE_ACTION_CODES),
        "contract allowed action mismatch",
        errors,
    )
    require(set(contract.get("allowed_actor_roles") or []) == set(ALLOWED_ACTOR_ROLES), "contract actor roles mismatch", errors)
    for key in (
        "raw_or_plaintext_allowed",
        "business_value_allowed_in_public_repo",
        "private_processed_ref_allowed_in_public_repo",
        "raw_to_processed_comparison_allowed_by_intake",
        "processed_value_materialization_allowed_by_intake",
        "lineage_full_check_allowed_by_intake",
        "formal_report_allowed_by_intake",
        "github_upload_allowed_by_intake",
        "app_reinstall_allowed_by_intake",
        "business_execution_allowed_by_intake",
    ):
        require(contract.get(key) is False, f"contract.{key} must be false", errors)
    require(packet.get("current_gate") == contract.get("current_gate"), "packet/contract gate mismatch", errors)
    require(
        set(packet.get("allowed_intake_action_codes") or []) == set(contract.get("allowed_intake_action_codes") or []),
        "packet/contract actions mismatch",
        errors,
    )


def _validate_packet(packet: dict[str, Any], summary: dict[str, Any], errors: list[str]) -> None:
    walk_forbidden_public_keys(packet, errors)
    require(
        packet.get("record_type") == "v014_private_processed_value_source_map_owner_authorized_fill_packet",
        "packet record_type mismatch",
        errors,
    )
    require(packet.get("schema_version") == PACKET_SCHEMA_VERSION, "packet schema mismatch", errors)
    require(packet.get("project_id") == "KMFA", "packet project mismatch", errors)
    require(packet.get("phase_id") == PHASE_ID, "packet phase mismatch", errors)
    require(packet.get("packet_status") == "ready_for_owner_or_authorized_delegate_fill_record", "packet status mismatch", errors)
    require(packet.get("fill_record_status") == "no_owner_authorized_fill_record_supplied", "packet fill status mismatch", errors)
    require(packet.get("intake_summary") == summary, "packet summary mismatch", errors)
    require(packet.get("owner_action_required") is True, "packet owner action flag mismatch", errors)
    blocked = packet.get("blocked_follow_on_actions", {})
    for key in (
        "processed_value_materialization_replay_allowed",
        "raw_to_processed_value_comparison_allowed",
        "lineage_full_check_allowed",
        "formal_report_allowed",
        "github_upload_allowed",
        "app_reinstall_allowed",
        "business_execution_allowed",
    ):
        require(blocked.get(key) is False, f"packet blocked action {key} must be false", errors)


def _validate_templates(errors: list[str]) -> None:
    for action_code in ALLOWED_INTAKE_ACTION_CODES:
        path = TEMPLATES_DIR / f"{action_code}_template.json"
        template = read_json(path)
        walk_forbidden_public_keys(template, errors)
        require(
            template.get("record_type") == "v014_private_processed_value_source_map_owner_authorized_fill_template",
            f"{path} record_type mismatch",
            errors,
        )
        require(template.get("schema_version") == TEMPLATE_SCHEMA_VERSION, f"{path} schema mismatch", errors)
        require(template.get("action_code") == action_code, f"{path} action code mismatch", errors)
        require(template.get("not_fill_record") is True, f"{path} must be marked not_fill_record", errors)
        require(template.get("raw_or_business_value_allowed") is False, f"{path} raw/value flag must be false", errors)
        items = template.get("fill_items", [])
        require(isinstance(items, list) and len(items) == 1, f"{path} fill_items must contain one template item", errors)
        if items and isinstance(items[0], dict):
            require(items[0].get("action_code") == action_code, f"{path} item action mismatch", errors)


def check_private_intake_request(*, require_private_intake_request: bool, expected_count: int, errors: list[str]) -> None:
    for path in (PRIVATE_INTAKE_REQUEST_PATH, PRIVATE_INTAKE_DIAGNOSTIC_PATH):
        require(".codex_private_runtime/" in path.as_posix(), f"private path mismatch: {path}", errors)
        require(not git_output(["ls-files", str(path)]), f"private artifact must not be tracked: {path}", errors)
        require(git_check_ignore(path), f"private artifact must be git-ignored: {path}", errors)
    if not require_private_intake_request:
        return
    for path in (PRIVATE_INTAKE_REQUEST_PATH, PRIVATE_INTAKE_DIAGNOSTIC_PATH):
        require(path.exists(), f"private intake artifact must exist: {path}", errors)
    if not PRIVATE_INTAKE_REQUEST_PATH.exists():
        return
    private_request = read_json(PRIVATE_INTAKE_REQUEST_PATH)
    require(private_request.get("schema_version") == PRIVATE_SCHEMA_VERSION, "private request schema mismatch", errors)
    require(
        private_request.get("classification") == "private_owner_authorized_fill_intake_request_do_not_commit",
        "private request classification mismatch",
        errors,
    )
    summary = private_request.get("intake_request_summary", {})
    require(summary.get("intake_request_item_count") == expected_count, "private request item count mismatch", errors)
    require(summary.get("owner_authorized_fill_record_supplied") is False, "private request fill supplied flag must be false", errors)
    require(summary.get("active_authorized_fill_record_created") is False, "private request active record flag must be false", errors)
    require(summary.get("raw_to_processed_value_comparison_performed") is False, "private request comparison flag must be false", errors)
    require(summary.get("business_value_consistency_verified") is False, "private request business consistency flag must be false", errors)
    items = private_request.get("intake_request_items", [])
    require(isinstance(items, list), "private request items must be list", errors)
    require(len(items) == expected_count, "private request item list length mismatch", errors)
    for item in items if isinstance(items, list) else []:
        if not isinstance(item, dict):
            continue
        require(
            item.get("allowed_intake_action_codes") == ALLOWED_INTAKE_ACTION_CODES,
            "private request allowed action list mismatch",
            errors,
        )
        for forbidden_key in ("raw_value", "normalized_value", "processed_value", "business_value", "value"):
            require(forbidden_key not in item, f"value-bearing key must not be in private request: {forbidden_key}", errors)


def check_tracked_sensitive_suffixes(errors: list[str]) -> None:
    tracked = git_output(["ls-files", "KMFA"])
    for filename in tracked.splitlines():
        lower = filename.lower()
        if any(lower.endswith(suffix) for suffix in FORBIDDEN_TRACKED_SUFFIXES):
            errors.append(f"forbidden raw/private suffix tracked: {filename}")


def validate_v014_private_processed_value_source_map_owner_authorized_fill_intake(
    manifest_path: Path = MANIFEST_PATH,
    *,
    require_private_intake_request: bool = False,
) -> dict[str, Any]:
    errors: list[str] = []
    manifest = read_json(manifest_path)
    go_no_go = read_json(GO_NO_GO_PATH)
    summary = read_json(SUMMARY_PATH)
    packet = read_json(INTAKE_PACKET_PATH)
    contract = read_json(INTAKE_CONTRACT_PATH)
    metadata_manifest = read_json(METADATA_MANIFEST_PATH)
    metadata_go_no_go = read_json(METADATA_GO_NO_GO_PATH)
    metadata_summary = read_json(METADATA_SUMMARY_PATH)
    metadata_packet = read_json(METADATA_PACKET_PATH)
    metadata_contract = read_json(METADATA_CONTRACT_PATH)

    require(metadata_manifest == manifest, "metadata manifest copy mismatch", errors)
    require(metadata_go_no_go == go_no_go, "metadata go/no-go copy mismatch", errors)
    require(metadata_summary == summary, "metadata summary copy mismatch", errors)
    require(metadata_packet == packet, "metadata packet copy mismatch", errors)
    require(metadata_contract == contract, "metadata contract copy mismatch", errors)

    walk_forbidden_public_keys(manifest, errors)
    walk_forbidden_public_keys(go_no_go, errors)
    walk_forbidden_public_keys(summary, errors)

    require(manifest.get("schema_version") == SCHEMA_VERSION, "manifest schema mismatch", errors)
    require(manifest.get("project_id") == "KMFA", "manifest project mismatch", errors)
    require(manifest.get("version") == "0.1.4", "manifest version mismatch", errors)
    require(manifest.get("phase_id") == PHASE_ID, "manifest phase mismatch", errors)
    require(manifest.get("task_id") == TASK_ID, "manifest task mismatch", errors)
    require(manifest.get("acceptance_ids") == [ACCEPTANCE_ID], "manifest acceptance mismatch", errors)
    require(manifest.get("status") == STATUS, "manifest status mismatch", errors)
    require(manifest.get("owner_authorized_fill_intake_summary") == summary, "manifest summary mismatch", errors)
    require(manifest.get("go_no_go") == go_no_go, "manifest go/no-go mismatch", errors)
    require(manifest.get("intake_packet") == packet, "manifest packet mismatch", errors)
    require(manifest.get("intake_contract") == contract, "manifest contract mismatch", errors)
    require(manifest.get("next_recommended_phase") == NEXT_RECOMMENDED_PHASE, "manifest next phase mismatch", errors)

    expected_summary = {
        "source_unresolved_gap_item_count": 113,
        "source_unresolved_unique_private_ref_count": 101,
        "source_duplicate_unresolved_gap_item_count": 12,
        "source_existing_source_map_record_count": 36,
        "private_intake_request_item_count": 113,
        "allowed_intake_action_count": 3,
        "allowed_actor_role_count": 2,
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
    for key, expected in expected_summary.items():
        require(summary.get(key) == expected, f"summary {key} mismatch: {summary.get(key)!r} != {expected!r}", errors)

    require(go_no_go.get("schema_version") == GO_NO_GO_SCHEMA_VERSION, "go/no-go schema mismatch", errors)
    require(go_no_go.get("decision") == "NO_GO", "go/no-go decision mismatch", errors)
    require(go_no_go.get("owner_authorized_fill_intake_ready") is True, "go/no-go intake readiness mismatch", errors)
    require(go_no_go.get("owner_authorized_fill_record_supplied") is False, "go/no-go fill supplied flag mismatch", errors)
    require(go_no_go.get("active_authorized_fill_record_created") is False, "go/no-go active record flag mismatch", errors)
    require(go_no_go.get("next_recommended_phase") == NEXT_RECOMMENDED_PHASE, "go/no-go next phase mismatch", errors)
    for key in (
        "processed_value_materialization_replay_allowed",
        "raw_to_processed_value_comparison_allowed",
        "business_value_consistency_verified",
        "lineage_full_check_complete",
        "formal_report_allowed",
        "github_upload_allowed",
        "app_reinstall_allowed",
        "business_execution_allowed",
    ):
        require(go_no_go.get(key) is False, f"go/no-go {key} must be false", errors)

    _validate_packet(packet, summary, errors)
    _validate_contract(contract, packet, errors)
    _validate_templates(errors)

    controls = manifest.get("phase_scope_controls", {})
    for key in (
        "owner_authorized_fill_record_created",
        "new_fingerprints_materialized",
        "processed_value_materialization_replay_performed",
        "raw_to_processed_value_comparison_performed",
        "processed_data_reconciliation_performed",
        "lineage_full_check_performed",
        "formal_report_performed",
        "github_upload_performed",
        "app_reinstall_performed",
        "business_execution_performed",
        "next_phase_started",
    ):
        require(controls.get(key) is False, f"phase_scope_controls.{key} must be false", errors)
    for key, value in (manifest.get("raw_readonly_boundary") or {}).items():
        require(value is False, f"raw_readonly_boundary.{key} must be false", errors)
    public_safety = manifest.get("public_repo_safety", {})
    require(public_safety.get("public_safe_aggregate_only") is True, "public safety aggregate flag mismatch", errors)
    for key, value in public_safety.items():
        if key.startswith("public_safe_"):
            continue
        require(value is False, f"public_repo_safety.{key} must be false", errors)

    for path in (
        REPORT_PATH,
        DECISION_REQUEST_PATH,
        GO_NO_GO_RECORD_PATH,
        TEST_RESULTS_PATH,
        RISK_REGISTER_PATH,
        ROLLBACK_PATH,
        MANIFEST_PATH,
        GO_NO_GO_PATH,
        SUMMARY_PATH,
        INTAKE_PACKET_PATH,
        INTAKE_CONTRACT_PATH,
        METADATA_MANIFEST_PATH,
        METADATA_GO_NO_GO_PATH,
        METADATA_SUMMARY_PATH,
        METADATA_PACKET_PATH,
        METADATA_CONTRACT_PATH,
        *(TEMPLATES_DIR / f"{action_code}_template.json" for action_code in ALLOWED_INTAKE_ACTION_CODES),
    ):
        check_public_text(path, errors)

    check_private_intake_request(
        require_private_intake_request=require_private_intake_request,
        expected_count=113,
        errors=errors,
    )
    check_tracked_sensitive_suffixes(errors)
    if errors:
        raise ValidationError("\n".join(f"- {error}" for error in errors))
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--require-private-intake-request", action="store_true")
    args = parser.parse_args(argv)
    try:
        manifest = validate_v014_private_processed_value_source_map_owner_authorized_fill_intake(
            args.manifest,
            require_private_intake_request=args.require_private_intake_request,
        )
    except ValidationError as exc:
        print("FAIL: KMFA v0.1.4 owner-authorized fill intake validation failed")
        print(exc)
        return 1
    summary = manifest["owner_authorized_fill_intake_summary"]
    print(
        "PASS: KMFA v0.1.4 owner-authorized fill intake validated "
        f"(items={summary['private_intake_request_item_count']}, "
        f"actions={summary['allowed_intake_action_count']}, "
        f"github_upload={str(manifest['go_no_go']['github_upload_allowed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
