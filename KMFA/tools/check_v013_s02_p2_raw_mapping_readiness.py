#!/usr/bin/env python3
"""Validate KMFA v0.1.3 S02-P2 raw mapping readiness evidence."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from KMFA.tools.check_v013_s02_p1_raw_readiness import validate_v013_s02_p1_raw_readiness


RAW_DIR = Path("/Users/linzezhang/Downloads/KMFA_MetaData")
MANIFEST_PATH = Path("KMFA/stage_artifacts/V013_S02_P2_RAW_MAPPING_READINESS/machine/raw_mapping_readiness_manifest.json")
PUBLIC_REPORT_PATH = Path("KMFA/stage_artifacts/V013_S02_P2_RAW_MAPPING_READINESS/human/raw_mapping_readiness_report.md")
PRIVATE_SCHEMA_PATH = Path("KMFA/.codex_private_runtime/v013_s02_p2_raw_mapping_readiness/private_schema_inventory.json")
PRIVATE_REPORT_PATH = Path("KMFA/.codex_private_runtime/v013_s02_p2_raw_mapping_readiness/local_mapping_diagnostic_report.md")
TASK_ID = "KMFA-V013-S02-P2-RAW-MAPPING-READINESS-20260702"
SCHEMA_VERSION = "kmfa.v013_s02_p2_raw_mapping_readiness.v1"
FORBIDDEN_PUBLIC_SUFFIXES = (".zip", ".xlsx", ".xls", ".pdf", ".sqlite", ".db")
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


def git_check_ignored(path: Path) -> bool:
    result = subprocess.run(
        ["git", "check-ignore", "-q", str(path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return result.returncode == 0


def iter_private_leak_candidates(private_inventory: dict[str, Any]) -> list[str]:
    candidates: list[str] = []
    for record in private_inventory.get("xlsx_records", []):
        label = record.get("workbook_label")
        if isinstance(label, str):
            candidates.extend([label, Path(label).name])
        for sheet in record.get("sheets", []):
            sheet_name = sheet.get("sheet_name")
            if isinstance(sheet_name, str):
                candidates.append(sheet_name)
            candidates.extend(value for value in sheet.get("first_non_empty_row_values", []) if isinstance(value, str))
    for zip_record in private_inventory.get("zip_records", []):
        relative_path = zip_record.get("relative_path")
        if isinstance(relative_path, str):
            candidates.extend([relative_path, Path(relative_path).name])
        for nested in zip_record.get("nested_workbooks", []):
            label = nested.get("workbook_label")
            if isinstance(label, str):
                candidates.extend([label, Path(label).name])
            for sheet in nested.get("sheets", []):
                sheet_name = sheet.get("sheet_name")
                if isinstance(sheet_name, str):
                    candidates.append(sheet_name)
                candidates.extend(value for value in sheet.get("first_non_empty_row_values", []) if isinstance(value, str))
    return sorted({value.strip() for value in candidates if isinstance(value, str) and len(value.strip()) >= 4})


def validate_v013_s02_p2_raw_mapping_readiness(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    manifest = read_json(manifest_path)
    private_inventory = read_json(PRIVATE_SCHEMA_PATH)
    s02_p1 = validate_v013_s02_p1_raw_readiness()

    require(manifest.get("schema_version") == SCHEMA_VERSION, "manifest schema mismatch")
    require(manifest.get("project_id") == "KMFA", "project_id mismatch")
    require(manifest.get("version") == "0.1.3", "version mismatch")
    require(manifest.get("stage_id") == "S02", "stage_id must be S02")
    require(manifest.get("phase_id") == "S02-P2", "phase_id must be S02-P2")
    require(manifest.get("task_id") == TASK_ID, "task_id mismatch")
    require(manifest.get("phase_scope") == "raw_mapping_readiness_private_schema_inventory", "phase scope mismatch")
    require(s02_p1.get("phase_id") == "S02-P1", "S02-P1 dependency validator mismatch")
    require(manifest.get("s02_p1_dependency_validated") is True, "S02-P1 dependency must be validated")
    require(manifest.get("raw_dir") == str(RAW_DIR), "raw_dir mismatch")
    require(manifest.get("raw_dir_exists") is True, "raw_dir must exist")
    require(manifest.get("raw_dir_readable") is True, "raw_dir must be readable")
    require(manifest.get("raw_dir_mutation_allowed") is False, "raw mutation must be disallowed")
    require(manifest.get("raw_dir_mutation_performed") is False, "raw mutation must not be performed")
    require(manifest.get("raw_file_count") == s02_p1.get("file_count"), "raw file count must match S02-P1")
    require(manifest.get("raw_file_count", 0) > 0, "raw file count must be positive")
    require(manifest.get("xlsx_files_seen", 0) >= 1, "at least one xlsx file must be seen")
    require(manifest.get("zip_files_seen", 0) >= 1, "at least one zip file must be seen")
    require(manifest.get("zip_files_openable", 0) >= 1, "at least one zip file must be openable")
    require(manifest.get("workbooks_parseable", 0) >= 1, "at least one workbook must be parseable")
    require(manifest.get("sheets_seen", 0) >= 1, "at least one sheet must be seen")
    require(manifest.get("private_header_profile_count", 0) >= 1, "private header profiles must be recorded")
    require(manifest.get("private_mapping_candidate_count", 0) >= 1, "private mapping candidates must be recorded")
    require(manifest.get("private_schema_inventory_ref") == str(PRIVATE_SCHEMA_PATH), "private schema ref mismatch")
    require(manifest.get("private_mapping_diagnostic_ref") == str(PRIVATE_REPORT_PATH), "private report ref mismatch")
    require(PRIVATE_SCHEMA_PATH.exists(), "private schema inventory missing")
    require(PRIVATE_REPORT_PATH.exists(), "private mapping diagnostic missing")
    require(manifest.get("private_schema_inventory_written") is True, "private schema inventory must be written")
    require(manifest.get("private_mapping_diagnostic_written") is True, "private mapping diagnostic must be written")
    require(git_check_ignored(PRIVATE_SCHEMA_PATH), "private schema inventory must be git ignored")
    require(git_check_ignored(PRIVATE_REPORT_PATH), "private mapping diagnostic must be git ignored")
    require(manifest.get("private_outputs_git_ignored") is True, "private_outputs_git_ignored must be true")
    require(manifest.get("public_manifest_contains_raw_filenames") is False, "public raw filenames must be omitted")
    require(manifest.get("public_manifest_contains_field_plaintext") is False, "public field plaintext must be omitted")
    require(manifest.get("public_manifest_contains_raw_values") is False, "public raw values must be omitted")
    require(manifest.get("raw_field_plaintext_private_only") is True, "field plaintext must be private only")
    require(manifest.get("raw_business_value_extraction_performed") is False, "business value extraction must not run")
    require(
        manifest.get("raw_value_matching_readiness_status") == "blocked_authorized_mapping_required",
        "raw value matching readiness status mismatch",
    )
    require(manifest.get("raw_value_matching_performed") is False, "raw value matching must not run")
    require(manifest.get("github_upload_performed") is False, "GitHub upload must not be performed")
    require(manifest.get("delivery_allowed") is False, "delivery_allowed must remain false")
    require(manifest.get("formal_report_allowed") is False, "formal report must remain false")
    require(manifest.get("business_execution_allowed") is False, "business execution must remain false")
    require("S02-P3" in manifest.get("next_required_step", ""), "next step must point to S02-P3")

    require(private_inventory.get("raw_file_count") == manifest.get("raw_file_count"), "private raw file count mismatch")
    require(private_inventory.get("workbooks_parseable") == manifest.get("workbooks_parseable"), "private parseable count mismatch")
    require(
        private_inventory.get("private_mapping_candidate_count") == manifest.get("private_mapping_candidate_count"),
        "private mapping candidate count mismatch",
    )

    public_text = ""
    if PUBLIC_REPORT_PATH.exists():
        public_text += PUBLIC_REPORT_PATH.read_text(encoding="utf-8")
    public_text += json.dumps(manifest, ensure_ascii=False, sort_keys=True)
    leaked = [candidate for candidate in iter_private_leak_candidates(private_inventory) if candidate in public_text]
    require(not leaked, f"private raw/schema strings leaked to public evidence: {leaked[:10]}")

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

    status = git_output(["status", "--short", "--branch"])
    require("codex/kmfa" in status, "git status must be on codex/kmfa")

    if errors:
        raise ValidationError("\n".join(errors))

    return {
        "task_id": manifest["task_id"],
        "stage_id": manifest["stage_id"],
        "phase_id": manifest["phase_id"],
        "s02_p1_dependency_validated": manifest["s02_p1_dependency_validated"],
        "raw_dir": manifest["raw_dir"],
        "raw_dir_exists": manifest["raw_dir_exists"],
        "raw_dir_readable": manifest["raw_dir_readable"],
        "raw_file_count": manifest["raw_file_count"],
        "xlsx_files_seen": manifest["xlsx_files_seen"],
        "zip_files_seen": manifest["zip_files_seen"],
        "zip_files_openable": manifest["zip_files_openable"],
        "workbooks_parseable": manifest["workbooks_parseable"],
        "private_schema_inventory_written": manifest["private_schema_inventory_written"],
        "private_mapping_diagnostic_written": manifest["private_mapping_diagnostic_written"],
        "private_outputs_git_ignored": manifest["private_outputs_git_ignored"],
        "raw_dir_mutation_performed": manifest["raw_dir_mutation_performed"],
        "public_manifest_contains_raw_filenames": manifest["public_manifest_contains_raw_filenames"],
        "public_manifest_contains_field_plaintext": manifest["public_manifest_contains_field_plaintext"],
        "public_manifest_contains_raw_values": manifest["public_manifest_contains_raw_values"],
        "raw_value_matching_readiness_status": manifest["raw_value_matching_readiness_status"],
        "raw_value_matching_performed": manifest["raw_value_matching_performed"],
        "github_upload_performed": manifest["github_upload_performed"],
        "delivery_allowed": manifest["delivery_allowed"],
        "next_required_step": manifest["next_required_step"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.3 S02-P2 raw mapping readiness evidence.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args()
    try:
        result = validate_v013_s02_p2_raw_mapping_readiness(args.manifest)
    except ValidationError as exc:
        print("FAIL: KMFA v0.1.3 S02-P2 raw mapping readiness validation failed")
        print(exc)
        return 1
    print(
        "PASS: KMFA v0.1.3 S02-P2 raw mapping readiness validated "
        f"(raw_files={result['raw_file_count']}, zip_openable={result['zip_files_openable']}, "
        f"workbooks_parseable={result['workbooks_parseable']}, "
        f"matching={result['raw_value_matching_readiness_status']}, "
        f"github_upload={str(result['github_upload_performed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
