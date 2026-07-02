#!/usr/bin/env python3
"""Validate KMFA v0.1.3 S02-P1 raw readiness evidence."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any


RAW_DIR = Path("/Users/linzezhang/Downloads/KMFA_MetaData")
MANIFEST_PATH = Path("KMFA/stage_artifacts/V013_S02_P1_RAW_READINESS/machine/raw_readiness_manifest.json")
PUBLIC_REPORT_PATH = Path("KMFA/stage_artifacts/V013_S02_P1_RAW_READINESS/human/raw_readiness_report.md")
PRIVATE_INVENTORY_PATH = Path("KMFA/.codex_private_runtime/v013_s02_p1_raw_inventory/private_inventory.json")
PRIVATE_REPORT_PATH = Path("KMFA/.codex_private_runtime/v013_s02_p1_raw_inventory/local_diagnostic_report.md")
TASK_ID = "KMFA-V013-S02-P1-RAW-READINESS-20260702"
SCHEMA_VERSION = "kmfa.v013_s02_p1_raw_readiness.v1"
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


def iter_raw_files(raw_dir: Path) -> list[Path]:
    if not raw_dir.exists() or not raw_dir.is_dir():
        return []
    return sorted(path for path in raw_dir.rglob("*") if path.is_file())


def actual_raw_summary(raw_dir: Path) -> dict[str, Any]:
    files = iter_raw_files(raw_dir)
    suffixes = Counter(path.suffix.lower() or "<none>" for path in files)
    return {
        "file_count": len(files),
        "total_bytes": sum(path.stat().st_size for path in files),
        "extension_counts": dict(sorted(suffixes.items())),
    }


def validate_v013_s02_p1_raw_readiness(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    manifest = read_json(manifest_path)
    private_inventory = read_json(PRIVATE_INVENTORY_PATH)
    public_text = ""
    if PUBLIC_REPORT_PATH.exists():
        public_text += PUBLIC_REPORT_PATH.read_text(encoding="utf-8")
    public_text += json.dumps(manifest, ensure_ascii=False, sort_keys=True)

    require(manifest.get("schema_version") == SCHEMA_VERSION, "manifest schema mismatch")
    require(manifest.get("project_id") == "KMFA", "project_id mismatch")
    require(manifest.get("version") == "0.1.3", "version mismatch")
    require(manifest.get("stage_id") == "S02", "stage_id must be S02")
    require(manifest.get("phase_id") == "S02-P1", "phase_id must be S02-P1")
    require(manifest.get("task_id") == TASK_ID, "task_id mismatch")
    require(manifest.get("phase_scope") == "raw_data_read_only_inventory_readiness", "phase scope mismatch")
    require(manifest.get("raw_dir") == str(RAW_DIR), "raw_dir mismatch")
    require(manifest.get("raw_dir_exists") is True, "raw_dir must exist")
    require(manifest.get("raw_dir_readable") is True, "raw_dir must be readable")
    require(manifest.get("raw_dir_mutation_allowed") is False, "raw mutation must be disallowed")
    require(manifest.get("raw_dir_mutation_performed") is False, "raw mutation must not be performed")
    require(manifest.get("raw_dir_delete_allowed") is False, "raw delete must be disallowed")
    require(manifest.get("raw_dir_move_allowed") is False, "raw move must be disallowed")
    require(manifest.get("raw_dir_github_commit_allowed") is False, "raw commit must be disallowed")
    require(manifest.get("private_inventory_ref") == str(PRIVATE_INVENTORY_PATH), "private inventory ref mismatch")
    require(manifest.get("private_diagnostic_report_ref") == str(PRIVATE_REPORT_PATH), "private report ref mismatch")
    require(manifest.get("private_inventory_written") is True, "private inventory must be written")
    require(manifest.get("private_diagnostic_report_written") is True, "private report must be written")
    require(PRIVATE_INVENTORY_PATH.exists(), "private inventory file missing")
    require(PRIVATE_REPORT_PATH.exists(), "private report file missing")
    require(git_check_ignored(PRIVATE_INVENTORY_PATH), "private inventory must be git-ignored")
    require(git_check_ignored(PRIVATE_REPORT_PATH), "private report must be git-ignored")
    require(manifest.get("private_outputs_git_ignored") is True, "manifest private_outputs_git_ignored must be true")
    require(manifest.get("raw_value_matching_performed") is False, "raw value matching must be deferred")
    require(manifest.get("github_upload_performed") is False, "GitHub upload must not be performed")
    require(manifest.get("delivery_allowed") is False, "delivery_allowed must remain false")
    require(manifest.get("formal_report_allowed") is False, "formal_report_allowed must remain false")
    require(manifest.get("business_execution_allowed") is False, "business execution must remain false")
    require(manifest.get("public_manifest_contains_raw_file_records") is False, "public file records must be omitted")
    require(manifest.get("public_manifest_contains_raw_filenames") is False, "public filenames must be omitted")
    require(manifest.get("public_manifest_contains_raw_values") is False, "public raw values must be omitted")
    require("overall completion" in manifest.get("next_required_step", ""), "overall upload deferral missing")

    actual = actual_raw_summary(RAW_DIR)
    require(actual["file_count"] > 0, "raw file count must be positive")
    require(manifest.get("file_count") == actual["file_count"], "manifest file_count does not match raw dir")
    require(manifest.get("total_bytes") == actual["total_bytes"], "manifest total_bytes does not match raw dir")
    require(
        manifest.get("extension_counts") == actual["extension_counts"],
        "manifest extension_counts does not match raw dir",
    )
    require(private_inventory.get("file_count") == actual["file_count"], "private file_count mismatch")
    require(private_inventory.get("total_bytes") == actual["total_bytes"], "private total_bytes mismatch")
    require(private_inventory.get("extension_counts") == actual["extension_counts"], "private extension_counts mismatch")
    records = private_inventory.get("records", [])
    require(isinstance(records, list), "private records must be a list")
    require(len(records) == actual["file_count"], "private record count mismatch")

    for record in records:
        if not isinstance(record, dict):
            errors.append("private inventory record must be object")
            continue
        relative_path = record.get("relative_path")
        if isinstance(relative_path, str):
            basename = Path(relative_path).name
            require(relative_path not in public_text, f"raw relative path leaked to public evidence: {relative_path}")
            require(basename not in public_text, f"raw basename leaked to public evidence: {basename}")
        require("sha256" in record, "private inventory records must include sha256")

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
        "raw_dir": manifest["raw_dir"],
        "raw_dir_exists": manifest["raw_dir_exists"],
        "raw_dir_readable": manifest["raw_dir_readable"],
        "file_count": manifest["file_count"],
        "total_bytes": manifest["total_bytes"],
        "extension_counts": manifest["extension_counts"],
        "private_inventory_written": manifest["private_inventory_written"],
        "private_outputs_git_ignored": manifest["private_outputs_git_ignored"],
        "raw_dir_mutation_performed": manifest["raw_dir_mutation_performed"],
        "raw_value_matching_performed": manifest["raw_value_matching_performed"],
        "github_upload_performed": manifest["github_upload_performed"],
        "delivery_allowed": manifest["delivery_allowed"],
        "public_manifest_contains_raw_filenames": manifest["public_manifest_contains_raw_filenames"],
        "public_manifest_contains_raw_values": manifest["public_manifest_contains_raw_values"],
        "next_required_step": manifest["next_required_step"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.3 S02-P1 raw readiness evidence.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args()
    try:
        result = validate_v013_s02_p1_raw_readiness(args.manifest)
    except ValidationError as exc:
        print("FAIL: KMFA v0.1.3 S02-P1 raw readiness validation failed")
        print(exc)
        return 1
    print(
        "PASS: KMFA v0.1.3 S02-P1 raw readiness validated "
        f"(files={result['file_count']}, raw_dir_readable={str(result['raw_dir_readable']).lower()}, "
        f"private_ignored={str(result['private_outputs_git_ignored']).lower()}, "
        f"raw_value_matching={str(result['raw_value_matching_performed']).lower()}, "
        f"github_upload={str(result['github_upload_performed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
