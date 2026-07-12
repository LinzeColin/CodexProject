#!/usr/bin/env python3
"""Validate KMFA v1.4 S02-P3 quality gate evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from KMFA.tools import check_report_grade_gate
from KMFA.tools.check_v014_s02_p2_immutability_policy import (
    validate_v014_s02_p2_immutability_policy,
)


MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V014_S02_P3_QUALITY_GATE/machine/"
    "s02_p3_quality_gate_manifest.json"
)
LOCK_PATH = Path("KMFA/metadata/protocol/quality_gate_lock_v1_4.json")
QUALITY_POLICY_PATH = Path("KMFA/metadata/quality/quality_grade_policy.yaml")
REPORT_POLICY_PATH = Path("KMFA/metadata/reports/report_grade_policy.yaml")
RELEASE_GATE_PATH = Path("KMFA/metadata/reports/report_release_gate.yaml")
DIRECTORY_MANIFEST_PATH = Path("KMFA/metadata/protocol/directory_manifest.json")
QUALITY_DOC_PATH = Path("KMFA/docs/governance/QUALITY_GATE_POLICY.md")
COMPLETION_RECORD_PATH = Path("KMFA/stage_artifacts/V014_S02_P3_QUALITY_GATE/human/s02_p3_completion_record.md")
TEST_RESULTS_PATH = Path("KMFA/stage_artifacts/V014_S02_P3_QUALITY_GATE/human/test_results.md")
RISK_REGISTER_PATH = Path("KMFA/stage_artifacts/V014_S02_P3_QUALITY_GATE/human/risk_register.md")
ROLLBACK_PATH = Path("KMFA/stage_artifacts/V014_S02_P3_QUALITY_GATE/human/rollback_plan.md")

QUALITY_ORDER = ["Q0", "Q1", "Q2", "Q3", "Q4", "Q5"]
REPORT_ORDER = ["A", "B", "C", "D"]
EXPECTED_QUALITY_MAPPING = {
    "Q0": ("D", "blocked"),
    "Q1": ("D", "blocked"),
    "Q2": ("D", "blocked"),
    "Q3": ("C", "preview_only"),
    "Q4": ("B", "internal_review_report"),
    "Q5": ("A", "formal_internal_report"),
}
EXPECTED_HARD_BLOCKS = [
    "unresolved_critical_difference",
    "zero_delta_failed",
    "missing_required_lineage",
    "missing_human_confirmation_for_A",
    "stale_or_expired_input",
    "raw_data_mutation_detected",
]
PHASE_SCOPE_FALSE_KEYS = (
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
    Path("KMFA/tools/check_v014_s02_p3_quality_gate.py"),
    Path("KMFA/tests/test_v014_s02_p3_quality_gate.py"),
    Path("KMFA/tools/check_report_grade_gate.py"),
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


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def run_legacy_report_grade_gate(errors: list[str]) -> None:
    try:
        check_report_grade_gate.check_required_files()
        check_report_grade_gate.check_quality_grades()
        check_report_grade_gate.check_report_grades()
        check_report_grade_gate.check_release_gate()
        check_report_grade_gate.check_metadata_headers()
        check_report_grade_gate.check_privacy_boundary()
    except SystemExit as exc:
        errors.append(f"check_report_grade_gate failed with exit={exc.code}")


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


def check_legacy_policy_files(errors: list[str]) -> None:
    quality_policy = read_json(QUALITY_POLICY_PATH)
    report_policy = read_json(REPORT_POLICY_PATH)
    release_gate = read_json(RELEASE_GATE_PATH)
    directory_manifest = read_json(DIRECTORY_MANIFEST_PATH)

    require(quality_policy.get("stage_phase") == "S02-P3", "quality policy stage phase mismatch", errors)
    require(report_policy.get("stage_phase") == "S02-P3", "report policy stage phase mismatch", errors)
    require(release_gate.get("stage_phase") == "S02-P3", "release gate stage phase mismatch", errors)
    require(quality_policy.get("append_only") is True, "quality policy must be append-only", errors)
    require(report_policy.get("append_only") is True, "report policy must be append-only", errors)
    require(release_gate.get("append_only") is True, "release gate must be append-only", errors)
    require(quality_policy.get("forbidden_plaintext") is True, "quality policy must forbid plaintext", errors)
    require(report_policy.get("forbidden_plaintext") is True, "report policy must forbid plaintext", errors)
    require(release_gate.get("forbidden_plaintext") is True, "release gate must forbid plaintext", errors)
    require("metadata/protocol/quality_gate_lock_v1_4.json" in directory_manifest.get("required_files", []), "directory manifest missing v1.4 quality gate lock", errors)

    quality_by_grade = {item.get("grade"): item for item in quality_policy.get("quality_grades", [])}
    require(list(quality_by_grade) == QUALITY_ORDER, "quality grades must be Q0-Q5 in order", errors)
    report_by_grade = {item.get("grade"): item for item in report_policy.get("report_grades", [])}
    require(list(report_by_grade) == REPORT_ORDER, "report grades must be A-D in order", errors)
    gate_by_quality = {item.get("quality_grade"): item for item in release_gate.get("quality_to_report_gate", [])}
    require(list(gate_by_quality) == QUALITY_ORDER, "release gate must cover Q0-Q5 in order", errors)
    for quality_grade, (report_grade, permission) in EXPECTED_QUALITY_MAPPING.items():
        gate = gate_by_quality.get(quality_grade, {})
        require(gate.get("maximum_report_grade") == report_grade, f"{quality_grade} report cap mismatch", errors)
        require(gate.get("release_permission") == permission, f"{quality_grade} release permission mismatch", errors)
    for block in EXPECTED_HARD_BLOCKS:
        require(block in release_gate.get("hard_blocks", []), f"release gate missing hard block {block}", errors)


def check_lock_and_manifest(lock: dict[str, Any], manifest: dict[str, Any], errors: list[str]) -> None:
    for item, label in ((lock, "lock"), (manifest, "manifest")):
        require(item.get("project_id") == "KMFA", f"{label} project_id mismatch", errors)
        require(item.get("version") == "0.1.4", f"{label} version mismatch", errors)
        require(item.get("stage_id") == "S02", f"{label} stage_id mismatch", errors)
        require(item.get("phase_id") == "S02-P3", f"{label} phase_id mismatch", errors)
        require(item.get("stage_phase") == "S02-P3", f"{label} stage_phase mismatch", errors)
        require(
            item.get("task_id") == "KMFA-V014-S02-P3-QUALITY-GATE-20260703",
            f"{label} task_id mismatch",
            errors,
        )
        require(item.get("acceptance_id") == "ACC-V014-S02-P3-QUALITY-GATE", f"{label} acceptance id mismatch", errors)
        require(item.get("status") == "completed_validated_local_only_no_go_upload_deferred", f"{label} status mismatch", errors)
        dependency = item.get("dependency", {})
        require(
            dependency.get("dependency_manifest")
            == "KMFA/stage_artifacts/V014_S02_P2_IMMUTABILITY_POLICY/machine/s02_p2_immutability_policy_manifest.json",
            f"{label} dependency manifest mismatch",
            errors,
        )
        phase_scope = item.get("phase_scope", {})
        require(phase_scope.get("current_phase_only") is True, f"{label} current phase flag missing", errors)
        require(phase_scope.get("quality_gate_policy_only") is True, f"{label} quality gate flag missing", errors)
        require(phase_scope.get("next_phase") == "S02-STAGE-REVIEW", f"{label} next phase must be S02-STAGE-REVIEW", errors)
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
        require(release.get("current_data_quality_grade") == "Q0", f"{label} data quality grade must be Q0", errors)
        require(release.get("current_report_grade") == "D", f"{label} report grade must be D", errors)
        require(release.get("release_permission") == "blocked", f"{label} release permission must be blocked", errors)

    require(lock.get("schema_version") == "kmfa.v014_s02_p3_quality_gate_lock.v1", "lock schema mismatch", errors)
    require(manifest.get("schema_version") == "kmfa.v014_s02_p3_quality_gate.v1", "manifest schema mismatch", errors)
    public_safety = lock.get("public_repo_safety", {})
    for key in PUBLIC_SAFETY_FALSE_KEYS:
        require(public_safety.get(key) is False, f"lock public_repo_safety.{key} must be false", errors)

    quality_contract = lock.get("quality_grade_contract", {})
    report_contract = lock.get("report_grade_contract", {})
    release_contract = lock.get("release_gate_contract", {})
    quality_gate = manifest.get("quality_gate", {})
    require(quality_contract.get("allowed_quality_grades") == QUALITY_ORDER, "lock quality grade order mismatch", errors)
    require(report_contract.get("allowed_report_grades") == REPORT_ORDER, "lock report grade order mismatch", errors)
    require(quality_contract.get("quality_grade_count") == 6, "lock quality grade count mismatch", errors)
    require(report_contract.get("report_grade_count") == 4, "lock report grade count mismatch", errors)
    require(release_contract.get("quality_to_report_gate_count") == 6, "lock release mapping count mismatch", errors)
    require(quality_gate.get("allowed_quality_grade_count") == 6, "manifest quality grade count mismatch", errors)
    require(quality_gate.get("allowed_report_grade_count") == 4, "manifest report grade count mismatch", errors)
    require(quality_gate.get("quality_to_report_gate_count") == 6, "manifest release mapping count mismatch", errors)
    require(report_contract.get("grade_a_minimum_quality_grade") == "Q5", "A report minimum quality mismatch", errors)
    require(report_contract.get("grade_a_zero_delta_required") is True, "A report zero-delta gate missing", errors)
    require(report_contract.get("grade_a_critical_differences_closed_required") is True, "A report critical difference gate missing", errors)
    require(report_contract.get("grade_a_human_confirmation_required") is True, "A report human confirmation gate missing", errors)
    require(release_contract.get("missing_gate_evidence_policy") == "block_release", "missing evidence policy mismatch", errors)
    require(release_contract.get("hard_blocks") == EXPECTED_HARD_BLOCKS, "hard block list mismatch", errors)
    require(quality_gate.get("runtime_quality_result_generated_by_this_phase") is False, "S02-P3 must not generate runtime quality result", errors)
    require(quality_gate.get("runtime_report_generated_by_this_phase") is False, "S02-P3 must not generate runtime report", errors)


def check_quality_doc(errors: list[str]) -> None:
    text = QUALITY_DOC_PATH.read_text(encoding="utf-8")
    required_fragments = [
        "0.1.4-s02p3-quality-gate",
        "S02-P3",
        "Q0",
        "Q5",
        "A",
        "D",
        "GitHub main upload",
        "Stage 1-18",
    ]
    for fragment in required_fragments:
        require(fragment in text, f"quality gate policy missing fragment {fragment!r}", errors)


def validate_v014_s02_p3_quality_gate(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []
    dependency = validate_v014_s02_p2_immutability_policy()
    run_legacy_report_grade_gate(errors)
    lock = read_json(LOCK_PATH)
    manifest = read_json(manifest_path)

    require(dependency.get("phase_id") == "S02-P2", "S02-P2 dependency did not validate", errors)
    check_legacy_policy_files(errors)
    check_lock_and_manifest(lock, manifest, errors)
    check_quality_doc(errors)

    for path in [
        COMPLETION_RECORD_PATH,
        TEST_RESULTS_PATH,
        RISK_REGISTER_PATH,
        ROLLBACK_PATH,
        LOCK_PATH,
        MANIFEST_PATH,
        QUALITY_DOC_PATH,
        QUALITY_POLICY_PATH,
        REPORT_POLICY_PATH,
        RELEASE_GATE_PATH,
        Path("KMFA/tools/check_report_grade_gate.py"),
        Path("KMFA/tools/check_v014_s02_p3_quality_gate.py"),
        Path("KMFA/tests/test_v014_s02_p3_quality_gate.py"),
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
        manifest = validate_v014_s02_p3_quality_gate(Path(args.manifest))
    except ValidationError as exc:
        print(f"FAIL: {exc}")
        return 1
    gate = manifest["quality_gate"]
    print(
        "PASS: KMFA v1.4 S02-P3 quality gate validated "
        f"(quality_grades={gate['allowed_quality_grade_count']}, "
        f"report_grades={gate['allowed_report_grade_count']}, "
        f"gate_mappings={gate['quality_to_report_gate_count']}, "
        "raw_read=false, github_upload=false, next=S02-STAGE-REVIEW, go_no_go=NO_GO)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
