#!/usr/bin/env python3
"""Validate KMFA v0.1.3 Stage 2 review evidence."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from KMFA.tools.check_v013_s02_p1_raw_readiness import validate_v013_s02_p1_raw_readiness
from KMFA.tools.check_v013_s02_p2_raw_mapping_readiness import (
    validate_v013_s02_p2_raw_mapping_readiness,
)
from KMFA.tools.check_v013_s02_p3_data_quality_error_gate import (
    validate_v013_s02_p3_data_quality_error_gate,
)


MANIFEST_PATH = Path("KMFA/stage_artifacts/V013_S02_STAGE_REVIEW/machine/stage2_review_manifest.json")
REPORT_PATH = Path("KMFA/stage_artifacts/V013_S02_STAGE_REVIEW/human/stage2_review_report.md")
TEST_RESULTS_PATH = Path("KMFA/stage_artifacts/V013_S02_STAGE_REVIEW/human/test_results.md")
PHASE_MANIFESTS = {
    "S02-P1": Path("KMFA/stage_artifacts/V013_S02_P1_RAW_READINESS/machine/raw_readiness_manifest.json"),
    "S02-P2": Path("KMFA/stage_artifacts/V013_S02_P2_RAW_MAPPING_READINESS/machine/raw_mapping_readiness_manifest.json"),
    "S02-P3": Path("KMFA/stage_artifacts/V013_S02_P3_DATA_QUALITY_ERROR_GATE/machine/data_quality_error_gate_manifest.json"),
}
TASK_ID = "KMFA-V013-S02-STAGE-REVIEW-20260702"
SCHEMA_VERSION = "kmfa.v013_s02_stage_review.v1"
RAW_DIR = "/Users/linzezhang/Downloads/KMFA_MetaData"
PUBLIC_SAFETY_FALSE_KEYS = (
    "raw_business_data_committed",
    "zip_committed",
    "excel_workbook_committed",
    "pdf_committed",
    "private_csv_committed",
    "sqlite_or_db_committed",
    "credentials_committed",
    "field_plaintext_committed",
    "raw_file_names_committed",
    "raw_file_hashes_committed",
    "raw_business_values_committed",
    "sheet_names_committed",
    "zip_member_names_committed",
    "normalized_business_values_committed",
)
REQUIRED_HARD_BLOCKS = (
    "raw_value_matching_blocked_authorized_mapping_required",
    "owner_authorized_semantic_mapping_missing",
    "raw_row_value_extraction_not_performed",
    "zero_delta_not_performed",
    "lineage_full_check_not_performed",
    "formal_report_release_blocked",
)
FORBIDDEN_EVIDENCE_TEXT = (
    "raw_value:",
    "normalized_value:",
    "source_header_text:",
    "bank_statement",
    "contract_full_text",
    "salary_detail",
    "tax_filing",
    "-----" "BEGIN",
    "sk-",
)
FORBIDDEN_PUBLIC_SUFFIXES = (".zip", ".xlsx", ".xls", ".pdf", ".sqlite", ".db")


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


def validate_v013_s02_stage_review(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    manifest = read_json(manifest_path)
    p1_result = validate_v013_s02_p1_raw_readiness()
    p2_result = validate_v013_s02_p2_raw_mapping_readiness()
    p3_result = validate_v013_s02_p3_data_quality_error_gate()

    require(manifest.get("schema_version") == SCHEMA_VERSION, "manifest schema mismatch")
    require(manifest.get("project_id") == "KMFA", "project_id mismatch")
    require(manifest.get("version") == "0.1.3", "version mismatch")
    require(manifest.get("stage_id") == "S02", "stage_id must be S02")
    require(manifest.get("review_id") == TASK_ID, "review_id mismatch")
    require(manifest.get("task_id") == TASK_ID, "task_id mismatch")
    require(manifest.get("review_scope") == "v013_s02_stage_review_only", "review scope mismatch")
    require(manifest.get("status") == "pass_local_only_no_go_upload_deferred", "status mismatch")
    require(manifest.get("stage_review_performed") is True, "stage review must be performed")
    require(manifest.get("github_upload_performed") is False, "GitHub upload must not be performed")
    require(manifest.get("delivery_allowed") is False, "delivery_allowed must remain false")
    require(manifest.get("formal_report_allowed") is False, "formal_report_allowed must remain false")
    require(manifest.get("business_decision_basis_allowed") is False, "business decision basis must remain false")
    require(manifest.get("business_execution_allowed") is False, "business execution must remain false")
    require(manifest.get("lineage_full_check_completed") is False, "lineage full check must not be completed")
    require(manifest.get("raw_value_matching_performed") is False, "raw value matching must not be performed")
    require(manifest.get("raw_dir_read_performed_by_stage_review") is False, "direct stage review raw read must be false")
    require(manifest.get("raw_dir_read_performed_by_dependency_validators") is True, "dependency validator raw read flag mismatch")
    require(manifest.get("raw_dir_mutation_performed") is False, "raw directory mutation must not be performed")
    require(manifest.get("phase_count") == 3, "phase_count must be 3")
    require(manifest.get("open_review_finding_count") == 0, "open review findings must be 0")
    require(manifest.get("fixed_review_finding_count") == 0, "fixed review findings must be 0")
    require(manifest.get("review_findings") == [], "review findings must be empty")
    require(
        manifest.get("next_required_step")
        == "Proceed to v0.1.3 S03-P1 as a separate run; GitHub main upload remains deferred until the overall completion upload gate.",
        "next_required_step mismatch",
    )

    phase_results = manifest.get("phase_results", {})
    require(phase_results == {"S02-P1": "PASS", "S02-P2": "PASS", "S02-P3": "PASS"}, "phase_results mismatch")
    require(p1_result.get("phase_id") == "S02-P1", "S02-P1 validator did not return S02-P1")
    require(p2_result.get("phase_id") == "S02-P2", "S02-P2 validator did not return S02-P2")
    require(p3_result.get("phase_id") == "S02-P3", "S02-P3 validator did not return S02-P3")
    require(p1_result.get("delivery_allowed") is False, "S02-P1 delivery gate mismatch")
    require(p2_result.get("delivery_allowed") is False, "S02-P2 delivery gate mismatch")
    require(p3_result.get("delivery_allowed") is False, "S02-P3 delivery gate mismatch")

    gate = manifest.get("stage_gate", {})
    require(gate.get("current_data_quality_grade") == "Q2", "stage gate quality mismatch")
    require(gate.get("current_report_grade") == "D", "stage gate report grade mismatch")
    require(gate.get("release_permission") == "blocked", "stage gate release permission mismatch")
    require(manifest.get("current_data_quality_grade") == p3_result.get("current_data_quality_grade") == "Q2", "quality grade mismatch")
    require(manifest.get("current_report_grade") == p3_result.get("current_report_grade") == "D", "report grade mismatch")
    require(manifest.get("release_permission") == p3_result.get("release_permission") == "blocked", "release permission mismatch")

    hard_blocks = manifest.get("hard_blocks", [])
    require(isinstance(hard_blocks, list), "hard_blocks must be a list")
    for block in REQUIRED_HARD_BLOCKS:
        require(block in hard_blocks, f"missing hard block: {block}")
    require(manifest.get("hard_block_count") == len(REQUIRED_HARD_BLOCKS), "hard block count mismatch")

    raw_boundary = manifest.get("raw_data_boundary", {})
    require(raw_boundary.get("local_raw_data_dir") == RAW_DIR, "raw directory mismatch")
    require(raw_boundary.get("codex_read_allowed_only_when_phase_requires") is True, "raw read policy mismatch")
    require(raw_boundary.get("codex_modify_allowed") is False, "raw directory modify must be false")
    require(raw_boundary.get("codex_delete_allowed") is False, "raw directory delete must be false")
    require(raw_boundary.get("codex_move_allowed") is False, "raw directory move must be false")
    require(raw_boundary.get("codex_rename_allowed") is False, "raw directory rename must be false")
    require(raw_boundary.get("codex_overwrite_allowed") is False, "raw directory overwrite must be false")
    require(raw_boundary.get("codex_generate_inside_allowed") is False, "raw directory generate-inside must be false")
    require(raw_boundary.get("github_commit_allowed") is False, "raw directory commit must be false")

    safety = manifest.get("public_repo_safety", {})
    for key in PUBLIC_SAFETY_FALSE_KEYS:
        require(safety.get(key) is False, f"public_repo_safety.{key} must be false")

    reviewed_phase_manifests = manifest.get("reviewed_phase_manifests", {})
    for phase, path in PHASE_MANIFESTS.items():
        require(reviewed_phase_manifests.get(phase) == str(path), f"{phase} manifest ref mismatch")
        require(path.exists(), f"missing phase manifest: {path}")
    for ref in manifest.get("evidence_refs", []):
        ref_path = Path(ref)
        require(ref_path.exists(), f"missing evidence ref: {ref}")
    for evidence in (REPORT_PATH, TEST_RESULTS_PATH):
        require(evidence.exists(), f"missing human evidence: {evidence}")
        if evidence.exists():
            text = evidence.read_text(encoding="utf-8")
            for forbidden in FORBIDDEN_EVIDENCE_TEXT:
                require(forbidden not in text, f"forbidden evidence text {forbidden!r} in {evidence}")

    tracked_files = git_output(["ls-files", "KMFA"]).splitlines()
    forbidden_tracked = [
        path
        for path in tracked_files
        if path.lower().endswith(FORBIDDEN_PUBLIC_SUFFIXES) or ".codex_private_runtime/" in path
    ]
    require(not forbidden_tracked, f"forbidden public/private tracked files: {forbidden_tracked}")
    require("codex/kmfa" in git_output(["status", "--short", "--branch"]), "git status must be on codex/kmfa")

    if errors:
        raise ValidationError("\n".join(errors))

    return {
        "task_id": manifest["task_id"],
        "stage_id": manifest["stage_id"],
        "review_scope": manifest["review_scope"],
        "phase_count": manifest["phase_count"],
        "phase_results": phase_results,
        "stage_review_performed": manifest["stage_review_performed"],
        "github_upload_performed": manifest["github_upload_performed"],
        "delivery_allowed": manifest["delivery_allowed"],
        "formal_report_allowed": manifest["formal_report_allowed"],
        "business_decision_basis_allowed": manifest["business_decision_basis_allowed"],
        "business_execution_allowed": manifest["business_execution_allowed"],
        "raw_value_matching_performed": manifest["raw_value_matching_performed"],
        "raw_dir_read_performed_by_stage_review": manifest["raw_dir_read_performed_by_stage_review"],
        "raw_dir_mutation_performed": manifest["raw_dir_mutation_performed"],
        "current_data_quality_grade": manifest["current_data_quality_grade"],
        "current_report_grade": manifest["current_report_grade"],
        "release_permission": manifest["release_permission"],
        "open_review_finding_count": manifest["open_review_finding_count"],
        "fixed_review_finding_count": manifest["fixed_review_finding_count"],
        "hard_blocks": hard_blocks,
        "next_required_step": manifest["next_required_step"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.3 Stage 2 review evidence.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args()
    try:
        result = validate_v013_s02_stage_review(args.manifest)
    except ValidationError as exc:
        print("FAIL: KMFA v0.1.3 Stage 2 review validation failed")
        print(exc)
        return 1
    print(
        "PASS: KMFA v0.1.3 Stage 2 review validated "
        f"(phases={result['phase_count']}, findings_open={result['open_review_finding_count']}, "
        f"quality={result['current_data_quality_grade']}, report={result['current_report_grade']}, "
        f"release={result['release_permission']}, github_upload={str(result['github_upload_performed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
