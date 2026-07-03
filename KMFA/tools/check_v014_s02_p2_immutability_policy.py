#!/usr/bin/env python3
"""Validate KMFA v1.4 S02-P2 immutability policy evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from KMFA.tools import immutability_policy_check
from KMFA.tools.check_v014_s02_p1_metadata_protocol import validate_v014_s02_p1_metadata_protocol


MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V014_S02_P2_IMMUTABILITY_POLICY/machine/"
    "s02_p2_immutability_policy_manifest.json"
)
LOCK_PATH = Path("KMFA/metadata/protocol/immutability_policy_lock_v1_4.json")
RAW_ROOTS_POLICY_PATH = Path("KMFA/metadata/protocol/raw_data_roots_v1_4.json")
RAW_MANIFEST_SCHEMA_PATH = Path("KMFA/metadata/imports/raw_manifest_schema.json")
RAW_MANIFEST_POLICY_PATH = Path("KMFA/metadata/imports/raw_manifest_policy.yaml")
RAW_FILE_MANIFEST_PATH = Path("KMFA/metadata/imports/raw_file_manifest.jsonl")
DERIVED_POLICY_PATH = Path("KMFA/metadata/lineage/derived_data_policy.yaml")
DERIVED_VERSIONS_PATH = Path("KMFA/metadata/lineage/derived_data_versions.jsonl")
CONTROL_POLICY_PATH = Path("KMFA/metadata/approvals/control_event_policy.yaml")
CONTROL_EVENTS_PATH = Path("KMFA/metadata/approvals/control_events.jsonl")
IMMUTABILITY_DOC_PATH = Path("KMFA/docs/governance/IMMUTABILITY_POLICY.md")
COMPLETION_RECORD_PATH = Path("KMFA/stage_artifacts/V014_S02_P2_IMMUTABILITY_POLICY/human/s02_p2_completion_record.md")
TEST_RESULTS_PATH = Path("KMFA/stage_artifacts/V014_S02_P2_IMMUTABILITY_POLICY/human/test_results.md")
RISK_REGISTER_PATH = Path("KMFA/stage_artifacts/V014_S02_P2_IMMUTABILITY_POLICY/human/risk_register.md")
ROLLBACK_PATH = Path("KMFA/stage_artifacts/V014_S02_P2_IMMUTABILITY_POLICY/human/rollback_plan.md")
EXPECTED_IMMUTABLE_FIELDS = [
    "import_run_id",
    "source_id",
    "file_hash",
    "storage_ref",
    "original_filename_hash",
]
EXPECTED_DERIVED_ACTIONS = [
    "create_version",
    "invalidate_version",
    "rerun_version",
    "compare_versions",
]
EXPECTED_CONTROL_EVENT_TYPES = [
    "mapping_rule",
    "resolution_event",
    "approval_event",
    "comment",
    "rerun_request",
    "invalidation_request",
]
EXPECTED_FORBIDDEN_TARGET_LAYERS = [
    "raw",
    "raw_file_manifest_immutable_fields",
    "original_extracted_values",
]
PHASE_SCOPE_FALSE_KEYS = (
    "s02_p3_started",
    "stage2_review_performed",
    "github_upload_performed",
    "raw_inventory_performed",
    "raw_value_matching_performed",
    "lineage_full_check_performed",
    "formal_report_performed",
    "live_connector_called",
    "opme_deep_coupling_performed",
    "business_execution_performed",
    "next_phase_started",
)
RAW_BOUNDARY_FALSE_KEYS = (
    "raw_inbox_read_by_this_phase",
    "raw_inbox_listed_by_this_phase",
    "raw_inbox_inventory_by_this_phase",
    "raw_inbox_modified_by_this_phase",
    "raw_inbox_deleted_by_this_phase",
    "raw_inbox_moved_by_this_phase",
    "raw_inbox_renamed_by_this_phase",
    "raw_inbox_overwritten_by_this_phase",
    "raw_inbox_written_by_this_phase",
    "raw_filenames_committed",
    "raw_hashes_committed",
    "field_or_header_plaintext_committed",
    "row_or_cell_values_committed",
    "business_values_committed",
)
PUBLIC_SAFETY_FALSE_KEYS = (
    "raw_business_data_committed",
    "zip_committed",
    "excel_workbook_committed",
    "pdf_committed",
    "private_csv_committed",
    "sqlite_or_db_committed",
    "credentials_committed",
    "raw_filenames_committed",
    "raw_hashes_committed",
    "field_plaintext_committed",
    "normalized_business_values_committed",
)
RELEASE_FALSE_KEYS = (
    "delivery_allowed",
    "formal_report_allowed",
    "business_decision_basis_allowed",
    "business_execution_allowed",
    "github_main_upload_allowed",
)
FORBIDDEN_EXTENSIONS = {".zip", ".xlsx", ".xls", ".xlsm", ".pdf", ".sqlite", ".sqlite3", ".db"}
FORBIDDEN_EVIDENCE_TEXT = (
    "original_filename:",
    "member_path:",
    "member_name:",
    "sheet_name:",
    "cell_value:",
    "row_value:",
    "bank_statement:",
    "contract_full_text:",
    "salary_detail:",
    "tax_filing:",
    "connector_token:",
    "connector_password:",
    "api_key:",
    "private_key:",
    "-----" "BEGIN",
    "s" "k-",
)
CODE_OR_TEST_EVIDENCE = {
    Path("KMFA/tools/check_v014_s02_p2_immutability_policy.py"),
    Path("KMFA/tests/test_v014_s02_p2_immutability_policy.py"),
    Path("KMFA/tools/immutability_policy_check.py"),
}


class ValidationError(Exception):
    pass


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ValidationError(f"missing JSON file: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValidationError(f"{path} must contain a JSON object")
    return value


def iter_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise ValidationError(f"missing JSONL file: {path}")
    records: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValidationError(f"{path}:{line_no} must contain a JSON object")
        records.append(value)
    if not records:
        raise ValidationError(f"{path} must contain a protocol header")
    return records


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def run_legacy_immutability_check(errors: list[str]) -> None:
    try:
        immutability_policy_check.check_required_files()
        immutability_policy_check.check_raw_manifest_policy()
        immutability_policy_check.check_derived_policy()
        immutability_policy_check.check_control_event_policy()
        immutability_policy_check.check_privacy_boundary()
    except SystemExit as exc:
        errors.append(f"immutability_policy_check failed with exit={exc.code}")


def check_public_safe_file(path: Path, errors: list[str]) -> None:
    require(path.exists(), f"missing evidence file: {path}", errors)
    if not path.exists():
        return
    require(path.suffix.lower() not in FORBIDDEN_EXTENSIONS, f"forbidden evidence extension: {path}", errors)
    if path in CODE_OR_TEST_EVIDENCE:
        return
    if path.suffix.lower() in {".md", ".json", ".jsonl", ".csv", ".yaml", ".yml"}:
        text = path.read_text(encoding="utf-8").lower()
        for forbidden in FORBIDDEN_EVIDENCE_TEXT:
            require(forbidden.lower() not in text, f"forbidden evidence text {forbidden!r} in {path}", errors)


def check_raw_roots_policy(errors: list[str]) -> None:
    raw_roots = read_json(RAW_ROOTS_POLICY_PATH)
    require(raw_roots.get("schema_version") == "kmfa.raw_data_roots.v1_4", "raw roots schema mismatch", errors)
    roots = raw_roots.get("raw_roots")
    require(isinstance(roots, list) and len(roots) == 1, "raw roots policy must contain one root", errors)
    if isinstance(roots, list) and roots:
        root = roots[0]
        require(root.get("path") == "/Users/linzezhang/Downloads/KMFA_MetaData", "raw root path mismatch", errors)
        require(root.get("access_policy") == "read_only_when_phase_authorized", "raw root access policy mismatch", errors)
        for key in (
            "current_phase_read_performed",
            "current_phase_list_performed",
            "current_phase_mutation_performed",
            "current_phase_inventory_performed",
        ):
            require(root.get(key) is False, f"raw roots {key} must be false", errors)
    runtime = raw_roots.get("private_runtime_policy", {})
    require(runtime.get("preferred_project_runtime") == "KMFA/.codex_private_runtime/", "private runtime mismatch", errors)
    require(runtime.get("public_repo_private_runtime_commit_allowed") is False, "private runtime commit must be false", errors)


def check_raw_manifest_contract(lock: dict[str, Any], errors: list[str]) -> None:
    contract = lock.get("raw_manifest_contract", {})
    schema = read_json(RAW_MANIFEST_SCHEMA_PATH)
    policy = read_json(RAW_MANIFEST_POLICY_PATH)
    header = iter_jsonl(RAW_FILE_MANIFEST_PATH)[0]
    for source, label in ((contract, "lock"), (schema, "schema"), (policy, "policy")):
        immutable = source.get("immutable_fields") or []
        require(immutable == EXPECTED_IMMUTABLE_FIELDS, f"raw manifest immutable fields mismatch in {label}", errors)
    require(contract.get("append_only") is True, "raw manifest lock must be append-only", errors)
    require(policy.get("append_only") is True, "raw manifest policy must be append-only", errors)
    require(policy.get("mutates_original_file") is False, "raw manifest must not mutate original file", errors)
    require(policy.get("mutates_original_extracted_value") is False, "raw manifest must not mutate original extracted value", errors)
    require(schema.get("raw_file_bytes_public_repo_allowed") is False, "raw bytes must be forbidden", errors)
    require(schema.get("raw_extracted_values_public_repo_allowed") is False, "raw extracted values must be forbidden", errors)
    require(header.get("raw_file_bytes_public_repo_allowed") is False, "raw file manifest header must forbid bytes", errors)
    require("file_hash" in (header.get("required_identifiers") or []), "raw file manifest header must require file_hash", errors)
    require(contract.get("raw_manifest_write_service_implemented") is False, "S02-P2 must not implement raw manifest write service", errors)


def check_derived_contract(lock: dict[str, Any], errors: list[str]) -> None:
    contract = lock.get("derived_version_contract", {})
    policy = read_json(DERIVED_POLICY_PATH)
    header = iter_jsonl(DERIVED_VERSIONS_PATH)[0]
    require(contract.get("append_only") is True, "derived lock must be append-only", errors)
    require(policy.get("append_only") is True, "derived policy must be append-only", errors)
    require(header.get("append_only") is True, "derived versions header must be append-only", errors)
    require(contract.get("overwrite_old_version_allowed") is False, "derived lock must forbid overwrite", errors)
    require(policy.get("overwrite_old_version_allowed") is False, "derived policy must forbid overwrite", errors)
    require(header.get("overwrite_old_version_allowed") is False, "derived versions header must forbid overwrite", errors)
    for action in EXPECTED_DERIVED_ACTIONS:
        require(action in (contract.get("allowed_actions") or []), f"derived lock missing action {action}", errors)
        require(action in (policy.get("allowed_actions") or []), f"derived policy missing action {action}", errors)
    require(contract.get("raw_layer_write_allowed") is False, "derived lock must forbid raw writes", errors)
    require(policy.get("raw_layer_write_allowed") is False, "derived policy must forbid raw writes", errors)
    require(
        contract.get("derived_calculation_implemented_by_this_phase") is False,
        "S02-P2 must not implement derived calculation",
        errors,
    )


def check_control_event_contract(lock: dict[str, Any], errors: list[str]) -> None:
    contract = lock.get("control_event_contract", {})
    policy = read_json(CONTROL_POLICY_PATH)
    records = iter_jsonl(CONTROL_EVENTS_PATH)
    header = records[0]
    require(contract.get("append_only") is True, "control event lock must be append-only", errors)
    require(policy.get("append_only") is True, "control event policy must be append-only", errors)
    require(header.get("append_only") is True, "control events header must be append-only", errors)
    require(contract.get("raw_layer_write_allowed") is False, "control event lock must forbid raw writes", errors)
    require(policy.get("raw_layer_write_allowed") is False, "control event policy must forbid raw writes", errors)
    require(header.get("raw_layer_write_allowed") is False, "control events header must forbid raw writes", errors)
    for event_type in EXPECTED_CONTROL_EVENT_TYPES:
        require(event_type in (contract.get("allowed_event_types") or []), f"control lock missing event type {event_type}", errors)
        require(event_type in (policy.get("allowed_event_types") or []), f"control policy missing event type {event_type}", errors)
        require(event_type in (header.get("allowed_event_types") or []), f"control header missing event type {event_type}", errors)
    for layer in EXPECTED_FORBIDDEN_TARGET_LAYERS:
        require(layer in (contract.get("forbidden_target_layers") or []), f"control lock missing forbidden layer {layer}", errors)
        require(layer in (policy.get("forbidden_target_layers") or []), f"control policy missing forbidden layer {layer}", errors)
    require(
        contract.get("frontend_or_workbench_raw_write_allowed") is False,
        "frontend/workbench raw write must be forbidden",
        errors,
    )
    for record in records[1:]:
        if "raw_layer_write_allowed" in record:
            require(record.get("raw_layer_write_allowed") is False, "control event record permits raw write", errors)


def check_lock_and_manifest(lock: dict[str, Any], manifest: dict[str, Any], errors: list[str]) -> None:
    for item, label in ((lock, "lock"), (manifest, "manifest")):
        require(item.get("project_id") == "KMFA", f"{label} project_id mismatch", errors)
        require(item.get("version") == "0.1.4", f"{label} version mismatch", errors)
        require(item.get("stage_id") == "S02", f"{label} stage_id mismatch", errors)
        require(item.get("phase_id") == "S02-P2", f"{label} phase_id mismatch", errors)
        require(item.get("stage_phase") == "S02-P2", f"{label} stage_phase mismatch", errors)
        require(
            item.get("task_id") == "KMFA-V014-S02-P2-IMMUTABILITY-POLICY-20260703",
            f"{label} task_id mismatch",
            errors,
        )
        require(
            item.get("acceptance_id") == "ACC-V014-S02-P2-IMMUTABILITY-POLICY",
            f"{label} acceptance_id mismatch",
            errors,
        )
        require(item.get("status") == "completed_validated_local_only_no_go_upload_deferred", f"{label} status mismatch", errors)
        dependency = item.get("dependency", {})
        require(
            dependency.get("dependency_manifest")
            == "KMFA/stage_artifacts/V014_S02_P1_METADATA_PROTOCOL/machine/s02_p1_metadata_protocol_manifest.json",
            f"{label} dependency manifest mismatch",
            errors,
        )
        phase_scope = item.get("phase_scope", {})
        require(phase_scope.get("current_phase_only") is True, f"{label} current phase flag missing", errors)
        require(phase_scope.get("immutability_policy_only") is True, f"{label} immutability policy flag missing", errors)
        require(phase_scope.get("next_phase") == "S02-P3", f"{label} next phase must be S02-P3", errors)
        for key in PHASE_SCOPE_FALSE_KEYS:
            require(phase_scope.get(key) is False, f"{label} phase_scope.{key} must be false", errors)
        raw_boundary = item.get("raw_data_boundary", {})
        require(raw_boundary.get("raw_inbox_path") == "/Users/linzezhang/Downloads/KMFA_MetaData", f"{label} raw inbox mismatch", errors)
        for key in RAW_BOUNDARY_FALSE_KEYS:
            require(raw_boundary.get(key) is False, f"{label} raw_data_boundary.{key} must be false", errors)
        release = item.get("release_state", {})
        for key in RELEASE_FALSE_KEYS:
            require(release.get(key) is False, f"{label} release_state.{key} must be false", errors)
        require(release.get("current_go_no_go") == "NO_GO", f"{label} current_go_no_go must be NO_GO", errors)
        require(release.get("current_report_grade") == "D", f"{label} report grade must be D", errors)
    require(lock.get("schema_version") == "kmfa.v014_s02_p2_immutability_policy_lock.v1", "lock schema mismatch", errors)
    require(manifest.get("schema_version") == "kmfa.v014_s02_p2_immutability_policy.v1", "manifest schema mismatch", errors)
    public_safety = lock.get("public_repo_safety", {})
    for key in PUBLIC_SAFETY_FALSE_KEYS:
        require(public_safety.get(key) is False, f"lock public_repo_safety.{key} must be false", errors)
    immutability = manifest.get("immutability_policy", {})
    require(immutability.get("raw_manifest_append_only") is True, "manifest raw append-only missing", errors)
    require(immutability.get("raw_manifest_immutable_field_count") == 5, "manifest immutable field count mismatch", errors)
    require(immutability.get("derived_versions_append_only") is True, "manifest derived append-only missing", errors)
    require(immutability.get("derived_allowed_action_count") == 4, "manifest derived action count mismatch", errors)
    require(immutability.get("control_events_append_only") is True, "manifest control append-only missing", errors)
    require(immutability.get("control_events_allowed_event_type_count") == 6, "manifest control event type count mismatch", errors)
    require(immutability.get("control_events_raw_layer_write_allowed") is False, "manifest raw write flag must be false", errors)


def validate_v014_s02_p2_immutability_policy(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []
    dependency = validate_v014_s02_p1_metadata_protocol()
    run_legacy_immutability_check(errors)
    lock = read_json(LOCK_PATH)
    manifest = read_json(manifest_path)

    require(dependency.get("phase_id") == "S02-P1", "S02-P1 dependency did not validate", errors)
    check_raw_roots_policy(errors)
    check_lock_and_manifest(lock, manifest, errors)
    check_raw_manifest_contract(lock, errors)
    check_derived_contract(lock, errors)
    check_control_event_contract(lock, errors)

    for path in [
        COMPLETION_RECORD_PATH,
        TEST_RESULTS_PATH,
        RISK_REGISTER_PATH,
        ROLLBACK_PATH,
        LOCK_PATH,
        MANIFEST_PATH,
        IMMUTABILITY_DOC_PATH,
        Path("KMFA/tools/immutability_policy_check.py"),
        Path("KMFA/tools/check_v014_s02_p2_immutability_policy.py"),
        Path("KMFA/tests/test_v014_s02_p2_immutability_policy.py"),
    ]:
        check_public_safe_file(path, errors)

    if errors:
        raise ValidationError("\n".join(errors))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default=str(MANIFEST_PATH))
    args = parser.parse_args()
    try:
        manifest = validate_v014_s02_p2_immutability_policy(Path(args.manifest))
    except ValidationError as exc:
        print(f"FAIL: {exc}")
        return 1
    policy = manifest["immutability_policy"]
    print(
        "PASS: KMFA v1.4 S02-P2 immutability policy validated "
        f"(immutable_fields={policy['raw_manifest_immutable_field_count']}, "
        f"derived_actions={policy['derived_allowed_action_count']}, "
        f"control_event_types={policy['control_events_allowed_event_type_count']}, "
        "raw_read=false, github_upload=false, next=S02-P3, go_no_go=NO_GO)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
