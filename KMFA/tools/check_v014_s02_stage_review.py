#!/usr/bin/env python3
"""Validate KMFA v1.4 Stage 2 overall review evidence."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from KMFA.tools.check_v014_s02_p1_metadata_protocol import validate_v014_s02_p1_metadata_protocol
from KMFA.tools.check_v014_s02_p2_immutability_policy import validate_v014_s02_p2_immutability_policy
from KMFA.tools.check_v014_s02_p3_quality_gate import validate_v014_s02_p3_quality_gate


TASK_ID = "KMFA-V014-S02-STAGE-REVIEW-20260703"
SCHEMA_VERSION = "kmfa.v014_s02_stage_review.v1"
RAW_INBOX = "/Users/linzezhang/Downloads/KMFA_MetaData"
MANIFEST_PATH = Path("KMFA/stage_artifacts/V014_S02_STAGE_REVIEW/machine/stage2_review_manifest.json")
REPORT_PATH = Path("KMFA/stage_artifacts/V014_S02_STAGE_REVIEW/human/stage2_review_report.md")
TEST_RESULTS_PATH = Path("KMFA/stage_artifacts/V014_S02_STAGE_REVIEW/human/test_results.md")
RISK_REGISTER_PATH = Path("KMFA/stage_artifacts/V014_S02_STAGE_REVIEW/human/risk_register.md")
ROLLBACK_PATH = Path("KMFA/stage_artifacts/V014_S02_STAGE_REVIEW/human/rollback_plan.md")
PHASE_MANIFESTS = {
    "S02-P1": Path(
        "KMFA/stage_artifacts/V014_S02_P1_METADATA_PROTOCOL/machine/"
        "s02_p1_metadata_protocol_manifest.json"
    ),
    "S02-P2": Path(
        "KMFA/stage_artifacts/V014_S02_P2_IMMUTABILITY_POLICY/machine/"
        "s02_p2_immutability_policy_manifest.json"
    ),
    "S02-P3": Path(
        "KMFA/stage_artifacts/V014_S02_P3_QUALITY_GATE/machine/"
        "s02_p3_quality_gate_manifest.json"
    ),
}
FORBIDDEN_EXTENSIONS = {".zip", ".xlsx", ".xls", ".xlsm", ".pdf", ".sqlite", ".sqlite3", ".db"}
FORBIDDEN_TEXT = (
    "raw_value:",
    "normalized_value:",
    "source_header_text:",
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
RAW_BOUNDARY_FALSE_KEYS = (
    "raw_inbox_read_by_this_review",
    "raw_inbox_listed_by_this_review",
    "raw_inbox_inventory_by_this_review",
    "raw_inbox_modified_by_this_review",
    "raw_inbox_deleted_by_this_review",
    "raw_inbox_moved_by_this_review",
    "raw_inbox_renamed_by_this_review",
    "raw_inbox_overwritten_by_this_review",
    "raw_inbox_written_by_this_review",
    "raw_filenames_committed",
    "raw_hashes_committed",
    "field_or_header_plaintext_committed",
    "row_or_cell_values_committed",
    "business_values_committed",
    "zip_committed",
    "excel_workbook_committed",
    "pdf_committed",
    "private_csv_committed",
    "sqlite_or_db_committed",
    "credentials_committed",
)
RELEASE_FALSE_KEYS = (
    "delivery_allowed",
    "formal_report_allowed",
    "business_decision_basis_allowed",
    "business_execution_allowed",
    "github_main_upload_allowed",
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


def check_public_safe_file(path: Path, errors: list[str]) -> None:
    require(path.exists(), f"missing evidence file: {path}", errors)
    if not path.exists():
        return
    require(path.suffix.lower() not in FORBIDDEN_EXTENSIONS, f"forbidden evidence extension: {path}", errors)
    if path.suffix.lower() in {".md", ".json", ".jsonl", ".csv", ".yaml", ".yml"}:
        text = path.read_text(encoding="utf-8").lower()
        for forbidden in FORBIDDEN_TEXT:
            require(forbidden.lower() not in text, f"forbidden evidence text {forbidden!r} in {path}", errors)


def validate_v014_s02_stage_review(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []
    manifest = read_json(manifest_path)
    p1_result = validate_v014_s02_p1_metadata_protocol()
    p2_result = validate_v014_s02_p2_immutability_policy()
    p3_result = validate_v014_s02_p3_quality_gate()

    require(manifest.get("schema_version") == SCHEMA_VERSION, "schema mismatch", errors)
    require(manifest.get("project_id") == "KMFA", "project_id mismatch", errors)
    require(manifest.get("version") == "0.1.4", "version mismatch", errors)
    require(manifest.get("stage_id") == "S02", "stage_id must be S02", errors)
    require(manifest.get("review_id") == TASK_ID, "review_id mismatch", errors)
    require(manifest.get("task_id") == TASK_ID, "task_id mismatch", errors)
    require(manifest.get("acceptance_id") == "ACC-V014-S02-STAGE-REVIEW", "acceptance id mismatch", errors)
    require(manifest.get("review_scope") == "v014_s02_stage_review_only", "review scope mismatch", errors)
    require(
        manifest.get("status") == "review_passed_local_only_no_go_upload_deferred_until_v014_stage1_18_complete",
        "status mismatch",
        errors,
    )
    require(manifest.get("stage_review_performed") is True, "stage_review_performed must be true", errors)
    require(manifest.get("github_upload_performed") is False, "GitHub upload must not be performed", errors)
    require(manifest.get("s03_p1_started") is False, "S03-P1 must not be started", errors)
    require(manifest.get("raw_inventory_performed") is False, "raw inventory must not be performed", errors)
    require(manifest.get("raw_value_matching_performed") is False, "raw value matching must not be performed", errors)
    require(manifest.get("lineage_full_check_performed") is False, "lineage full check must not be performed", errors)
    require(manifest.get("formal_report_performed") is False, "formal report must not be performed", errors)
    require(manifest.get("live_connector_called") is False, "live connector must not be called", errors)
    require(manifest.get("opme_deep_coupling_performed") is False, "OpMe deep coupling must not be performed", errors)
    require(manifest.get("business_execution_performed") is False, "business execution must not be performed", errors)
    require(manifest.get("phase_count") == 3, "phase_count must be 3", errors)
    require(
        manifest.get("phase_results") == {"S02-P1": "PASS", "S02-P2": "PASS", "S02-P3": "PASS"},
        "phase_results mismatch",
        errors,
    )
    require(p1_result.get("phase_id") == "S02-P1", "S02-P1 validator did not return S02-P1", errors)
    require(p2_result.get("phase_id") == "S02-P2", "S02-P2 validator did not return S02-P2", errors)
    require(p3_result.get("phase_id") == "S02-P3", "S02-P3 validator did not return S02-P3", errors)
    require(manifest.get("open_review_finding_count") == 0, "open findings must be 0", errors)
    require(manifest.get("fixed_review_finding_count") == 0, "fixed findings must be 0", errors)
    require(manifest.get("review_findings") == [], "review findings must be empty", errors)

    reviewed = manifest.get("reviewed_phase_manifests", {})
    for phase, path in PHASE_MANIFESTS.items():
        require(reviewed.get(phase) == str(path), f"{phase} manifest ref mismatch", errors)
        require(path.exists(), f"missing phase manifest: {path}", errors)

    release = manifest.get("release_state", {})
    for key in RELEASE_FALSE_KEYS:
        require(release.get(key) is False, f"release_state.{key} must be false", errors)
    require(release.get("current_go_no_go") == "NO_GO", "current Go/No-Go must be NO_GO", errors)
    require(release.get("current_data_quality_grade") == "Q0", "current data quality grade must be Q0", errors)
    require(release.get("current_report_grade") == "D", "current report grade must be D", errors)
    require(release.get("release_permission") == "blocked", "release permission must be blocked", errors)
    require(release == p3_result.get("release_state"), "release state must inherit S02-P3", errors)

    gate = manifest.get("stage_gate", {})
    require(gate.get("metadata_directory_count") == 7, "metadata directory count mismatch", errors)
    require(gate.get("metadata_identifier_count") == 5, "metadata identifier count mismatch", errors)
    require(gate.get("raw_manifest_immutable_field_count") == 5, "immutable field count mismatch", errors)
    require(gate.get("derived_allowed_action_count") == 4, "derived action count mismatch", errors)
    require(gate.get("control_event_type_count") == 6, "control event type count mismatch", errors)
    require(gate.get("quality_grade_count") == 6, "quality grade count mismatch", errors)
    require(gate.get("report_grade_count") == 4, "report grade count mismatch", errors)
    require(gate.get("quality_to_report_gate_count") == 6, "quality-to-report gate count mismatch", errors)
    require(gate.get("hard_block_count") == 6, "hard block count mismatch", errors)
    require(gate.get("current_data_quality_grade") == "Q0", "stage gate data quality mismatch", errors)
    require(gate.get("current_report_grade") == "D", "stage gate report grade mismatch", errors)
    require(gate.get("release_permission") == "blocked", "stage gate release permission mismatch", errors)

    raw_boundary = manifest.get("raw_data_boundary", {})
    require(raw_boundary.get("raw_inbox_path") == RAW_INBOX, "raw inbox path mismatch", errors)
    for key in RAW_BOUNDARY_FALSE_KEYS:
        require(raw_boundary.get(key) is False, f"raw_data_boundary.{key} must be false", errors)

    safety = manifest.get("public_repo_safety", {})
    for key in PUBLIC_SAFETY_FALSE_KEYS:
        require(safety.get(key) is False, f"public_repo_safety.{key} must be false", errors)

    validation = manifest.get("validation_summary", {})
    for key in (
        "s02_p1_validator",
        "s02_p2_validator",
        "s02_p3_validator",
        "stage_review_validator",
    ):
        require(validation.get(key) == "PASS", f"validation_summary.{key} must be PASS", errors)

    for ref in manifest.get("evidence_refs", []):
        check_public_safe_file(Path(ref), errors)
    for path in (REPORT_PATH, TEST_RESULTS_PATH, RISK_REGISTER_PATH, ROLLBACK_PATH, MANIFEST_PATH):
        check_public_safe_file(path, errors)

    tracked_files = git_output(["ls-files", "KMFA"]).splitlines()
    forbidden_tracked = [
        path for path in tracked_files if path.lower().endswith(tuple(FORBIDDEN_EXTENSIONS)) or ".codex_private_runtime/" in path
    ]
    require(not forbidden_tracked, f"forbidden public/private tracked files: {forbidden_tracked}", errors)
    require("codex/kmfa" in git_output(["status", "--short", "--branch"]), "git status must be on codex/kmfa", errors)

    if errors:
        raise ValidationError("\n".join(errors))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v1.4 Stage 2 overall review evidence.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args()
    try:
        manifest = validate_v014_s02_stage_review(args.manifest)
    except ValidationError as exc:
        print("FAIL: KMFA v1.4 Stage 2 review validation failed")
        print(exc)
        return 1
    gate = manifest["stage_gate"]
    print(
        "PASS: KMFA v1.4 Stage 2 review validated "
        f"(phases={manifest['phase_count']}, findings_open={manifest['open_review_finding_count']}, "
        f"metadata={gate['metadata_directory_count']}/{gate['metadata_identifier_count']}, "
        f"immutability={gate['raw_manifest_immutable_field_count']}/{gate['derived_allowed_action_count']}/"
        f"{gate['control_event_type_count']}, quality={gate['quality_grade_count']}, "
        f"report={gate['report_grade_count']}, gate_mappings={gate['quality_to_report_gate_count']}, "
        f"github_upload={str(manifest['github_upload_performed']).lower()}, "
        f"next={manifest['next_recommended_phase']}, go_no_go={manifest['release_state']['current_go_no_go']})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
