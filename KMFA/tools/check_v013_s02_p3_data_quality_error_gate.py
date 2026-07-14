#!/usr/bin/env python3
"""Validate KMFA v0.1.3 S02-P3 data quality and error gate evidence."""

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


MANIFEST_PATH = Path("KMFA/stage_artifacts/V013_S02_P3_DATA_QUALITY_ERROR_GATE/machine/data_quality_error_gate_manifest.json")
REPORT_PATH = Path("KMFA/stage_artifacts/V013_S02_P3_DATA_QUALITY_ERROR_GATE/human/data_quality_error_gate_report.md")
TASK_ID = "KMFA-V013-S02-P3-DATA-QUALITY-ERROR-GATE-20260702"
SCHEMA_VERSION = "kmfa.v013_s02_p3_data_quality_error_gate.v1"
QUALITY_GRADES = ["Q0", "Q1", "Q2", "Q3", "Q4", "Q5"]
REPORT_GRADES = ["A", "B", "C", "D"]
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
)
REQUIRED_HARD_BLOCKS = (
    "raw_value_matching_blocked_authorized_mapping_required",
    "owner_authorized_semantic_mapping_missing",
    "raw_row_value_extraction_not_performed",
    "zero_delta_not_performed",
    "lineage_full_check_not_performed",
    "formal_report_release_blocked",
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


def validate_policy_protocol() -> None:
    result = subprocess.run(
        [sys.executable, "KMFA/tools/check_report_grade_gate.py"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise ValidationError("S02-P3 policy protocol validator failed: " + result.stdout + result.stderr)


def validate_v013_s02_p3_data_quality_error_gate(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    validate_policy_protocol()
    s02_p1 = validate_v013_s02_p1_raw_readiness()
    s02_p2 = validate_v013_s02_p2_raw_mapping_readiness()
    manifest = read_json(manifest_path)

    require(manifest.get("schema_version") == SCHEMA_VERSION, "manifest schema mismatch")
    require(manifest.get("project_id") == "KMFA", "project_id mismatch")
    require(manifest.get("version") == "0.1.3", "version mismatch")
    require(manifest.get("stage_id") == "S02", "stage_id must be S02")
    require(manifest.get("phase_id") == "S02-P3", "phase_id must be S02-P3")
    require(manifest.get("task_id") == TASK_ID, "task_id mismatch")
    require(manifest.get("phase_scope") == "data_quality_error_gate_public_safe_lock", "phase scope mismatch")
    require(manifest.get("s02_p1_dependency_validated") is True, "S02-P1 dependency must be validated")
    require(manifest.get("s02_p2_dependency_validated") is True, "S02-P2 dependency must be validated")
    require(s02_p1.get("phase_id") == "S02-P1", "S02-P1 validator dependency mismatch")
    require(s02_p2.get("phase_id") == "S02-P2", "S02-P2 validator dependency mismatch")
    require(manifest.get("quality_grade_policy_validated") is True, "quality policy must be validated")
    require(manifest.get("report_grade_policy_validated") is True, "report policy must be validated")
    require(manifest.get("release_gate_policy_validated") is True, "release gate policy must be validated")
    require(manifest.get("quality_grades") == QUALITY_GRADES, "quality grades must be Q0-Q5")
    require(manifest.get("report_grades") == REPORT_GRADES, "report grades must be A-D")
    gate = manifest.get("quality_to_report_gate", {})
    require(isinstance(gate, dict), "quality_to_report_gate must be a dict")
    for grade in ["Q0", "Q1", "Q2"]:
        require(gate.get(grade, {}).get("maximum_report_grade") == "D", f"{grade} must cap at D")
        require(gate.get(grade, {}).get("release_permission") == "blocked", f"{grade} must block release")
    require(gate.get("Q3", {}).get("maximum_report_grade") == "C", "Q3 must cap at C")
    require(gate.get("Q4", {}).get("maximum_report_grade") == "B", "Q4 must cap at B")
    require(gate.get("Q5", {}).get("maximum_report_grade") == "A", "Q5 must cap at A")
    require(manifest.get("current_data_quality_grade") == "Q2", "current quality grade must be Q2")
    require(manifest.get("current_report_grade") == "D", "current report grade must be D")
    require(manifest.get("release_permission") == "blocked", "release must be blocked")
    require(manifest.get("raw_value_matching_readiness_status") == "blocked_authorized_mapping_required", "matching status mismatch")
    for key in [
        "formal_report_allowed",
        "internal_review_report_allowed",
        "preview_allowed",
        "business_decision_basis_allowed",
        "data_matches_raw_claim_allowed",
        "complete_trusted_report_display_allowed",
        "raw_value_matching_performed",
        "raw_business_value_extraction_performed",
        "raw_row_value_extraction_performed",
        "raw_dir_read_performed_by_s02_p3",
        "raw_dir_mutation_allowed",
        "raw_dir_mutation_performed",
        "stage_review_performed",
        "github_upload_performed",
        "delivery_allowed",
        "business_execution_allowed",
        "public_manifest_contains_raw_filenames",
        "public_manifest_contains_field_plaintext",
        "public_manifest_contains_sheet_names",
        "public_manifest_contains_zip_member_names",
        "public_manifest_contains_raw_values",
    ]:
        require(manifest.get(key) is False, f"{key} must be false")
    hard_blocks = manifest.get("hard_blocks", [])
    require(isinstance(hard_blocks, list), "hard_blocks must be a list")
    for block in REQUIRED_HARD_BLOCKS:
        require(block in hard_blocks, f"missing hard block: {block}")
    require(manifest.get("hard_block_count") == len(REQUIRED_HARD_BLOCKS), "hard block count mismatch")
    require("Stage 2 review" in manifest.get("next_required_step", ""), "next step must mention Stage 2 review")
    require("GitHub main upload remains deferred" in manifest.get("next_required_step", ""), "next step must defer GitHub main upload")
    require(REPORT_PATH.exists(), "human report missing")

    report_text = REPORT_PATH.read_text(encoding="utf-8")
    require("current_data_quality_grade: `Q2`" in report_text, "human report must show Q2")
    require("current_report_grade: `D`" in report_text, "human report must show D")
    require("release_permission: `blocked`" in report_text, "human report must show blocked release")
    require("raw_dir_read_performed_by_s02_p3: `false`" in report_text, "human report must show no raw read in S02-P3")

    safety = manifest.get("public_repo_safety", {})
    for key in PUBLIC_SAFETY_FALSE_KEYS:
        require(safety.get(key) is False, f"public_repo_safety.{key} must be false")

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
        "phase_id": manifest["phase_id"],
        "s02_p1_dependency_validated": manifest["s02_p1_dependency_validated"],
        "s02_p2_dependency_validated": manifest["s02_p2_dependency_validated"],
        "quality_grades": manifest["quality_grades"],
        "report_grades": manifest["report_grades"],
        "quality_to_report_gate": manifest["quality_to_report_gate"],
        "current_data_quality_grade": manifest["current_data_quality_grade"],
        "current_report_grade": manifest["current_report_grade"],
        "release_permission": manifest["release_permission"],
        "formal_report_allowed": manifest["formal_report_allowed"],
        "business_decision_basis_allowed": manifest["business_decision_basis_allowed"],
        "data_matches_raw_claim_allowed": manifest["data_matches_raw_claim_allowed"],
        "raw_value_matching_performed": manifest["raw_value_matching_performed"],
        "raw_business_value_extraction_performed": manifest["raw_business_value_extraction_performed"],
        "raw_dir_mutation_performed": manifest["raw_dir_mutation_performed"],
        "hard_blocks": manifest["hard_blocks"],
        "stage_review_performed": manifest["stage_review_performed"],
        "github_upload_performed": manifest["github_upload_performed"],
        "delivery_allowed": manifest["delivery_allowed"],
        "next_required_step": manifest["next_required_step"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.3 S02-P3 data quality/error gate evidence.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args()
    try:
        result = validate_v013_s02_p3_data_quality_error_gate(args.manifest)
    except ValidationError as exc:
        print("FAIL: KMFA v0.1.3 S02-P3 data quality/error gate validation failed")
        print(exc)
        return 1
    print(
        "PASS: KMFA v0.1.3 S02-P3 data quality/error gate validated "
        f"(quality={result['current_data_quality_grade']}, report={result['current_report_grade']}, "
        f"release={result['release_permission']}, github_upload={str(result['github_upload_performed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
