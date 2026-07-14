#!/usr/bin/env python3
"""Validate KMFA v0.1.3 S05-P1 A0 file registration replay evidence."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from KMFA.tools.a0_file_register import (
    DEFAULT_OUTPUT_CANDIDATES,
    DEFAULT_OUTPUT_MANIFEST,
    validate_a0_registration,
)
from KMFA.tools.check_v013_s04_stage_review import validate_v013_s04_stage_review
from KMFA.tools.v013_s05_p1_a0_file_registration import (
    MANIFEST_PATH,
    PRIVATE_DIAGNOSTIC_PATH,
    REPORT_PATH,
    SCHEMA_VERSION,
    TASK_ID,
    TEST_RESULTS_PATH,
)


BOOLEAN_FALSE_KEYS = (
    "raw_dir_mutation_performed",
    "raw_file_bytes_committed",
    "raw_filename_publication_allowed",
    "raw_file_hash_publication_allowed",
    "field_plaintext_publication_allowed",
    "sheet_name_publication_allowed",
    "zip_member_name_publication_allowed",
    "row_value_publication_allowed",
    "business_value_publication_allowed",
    "business_field_parsing_performed",
    "raw_value_matching_performed",
    "s05_p2_performed",
    "stage5_review_performed",
    "github_upload_performed",
    "delivery_allowed",
    "formal_report_allowed",
    "business_decision_basis_allowed",
    "business_execution_allowed",
)
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
    "sheet_names_committed",
    "zip_member_names_committed",
    "raw_business_values_committed",
)
FORBIDDEN_PUBLIC_KEYS = {
    "actual_package_sha256",
    "actual_package_size_bytes",
    "package_name",
    "member_sha256",
    "member_name",
    "member_path",
    "sheet_name",
    "raw_value",
    "normalized_value",
    "source_header_text",
}
FORBIDDEN_PUBLIC_TEXT = (
    "actual_package_sha256",
    "member_sha256:",
    "raw_value:",
    "normalized_value:",
    "source_header_text:",
    "-----" "BEGIN",
    "sk-",
)
FORBIDDEN_TRACKED_SUFFIXES = (".zip", ".xlsx", ".xls", ".xlsm", ".pdf", ".sqlite", ".db")


class ValidationError(Exception):
    pass


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ValidationError(f"missing JSON file: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValidationError(f"{path} must contain a JSON object")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise ValidationError(f"missing JSONL file: {path}")
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValidationError(f"{path} contains non-object JSONL row")
            records.append(value)
    return records


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


def walk_public(value: Any, errors: list[str], path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_PUBLIC_KEYS:
                errors.append(f"forbidden public key {key!r} at {path}")
            walk_public(child, errors, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            walk_public(child, errors, f"{path}[{index}]")


def validate_v013_s05_p1_a0_file_registration(
    manifest_path: Path = MANIFEST_PATH,
    *,
    require_private_diagnostic: bool = False,
) -> dict[str, Any]:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    manifest = read_json(manifest_path)
    walk_public(manifest, errors)
    stage4 = validate_v013_s04_stage_review()
    a0_manifest = read_json(DEFAULT_OUTPUT_MANIFEST)
    candidates = read_jsonl(DEFAULT_OUTPUT_CANDIDATES)
    validate_a0_registration(a0_manifest, candidates)

    require(manifest.get("schema_version") == SCHEMA_VERSION, "schema_version mismatch")
    require(manifest.get("project_id") == "KMFA", "project_id mismatch")
    require(manifest.get("version") == "0.1.3", "version mismatch")
    require(manifest.get("stage_id") == "S05", "stage_id must be S05")
    require(manifest.get("phase_id") == "S05-P1", "phase_id must be S05-P1")
    require(
        manifest.get("phase_scope") == "v013_s05_p1_a0_file_registration_replay_only",
        "phase scope mismatch",
    )
    require(manifest.get("task_id") == TASK_ID, "task_id mismatch")
    require(
        manifest.get("status") == "completed_validated_local_only_no_go_upload_deferred_private_source_mismatch",
        "status mismatch",
    )
    require(manifest.get("completed_task_ids") == ["S5PAT01", "S5PAT02", "S5PAT03"], "task ids mismatch")
    require(stage4.get("stage_review_performed") is True, "Stage 4 review dependency not passed")
    require(stage4.get("github_upload_deferred_until_stage10_batch") is True, "Stage 4 upload deferral mismatch")
    require(manifest.get("stage4_review_dependency_validated") is True, "stage4 dependency flag must be true")
    require(manifest.get("legacy_s05_p1_dependency_validated") is True, "legacy S05-P1 dependency must be true")

    summary = manifest.get("a0_file_summary", {})
    require(summary.get("total_files") == 9, "A0 total file count must be 9")
    require(summary.get("pdf_files") == 8, "A0 PDF file count must be 8")
    require(summary.get("excel_files") == 1, "A0 Excel file count must be 1")
    require(summary.get("legacy_fingerprint_recorded_count") == 9, "legacy fingerprint count must be 9")
    require(summary.get("member_sha256_recorded_count") == 0, "public member SHA256 backfill must remain 0")
    require(summary.get("member_sha256_pending_count") == 9, "member SHA256 pending count must remain 9")

    candidate_summary = manifest.get("a0_candidate_summary", {})
    require(candidate_summary.get("candidate_count") == 9, "candidate count must be 9")
    require(candidate_summary.get("q3_machine_candidate_count") == 9, "Q3 candidate count must be 9")
    require(candidate_summary.get("q4_human_locked_count") == 0, "Q4 human locked count must be 0")
    require(candidate_summary.get("q5_formal_report_allowed_count") == 0, "Q5 formal report count must be 0")

    raw_alignment = manifest.get("raw_alignment", {})
    require(raw_alignment.get("raw_data_inbox_read_required") is True, "raw read required flag must be true")
    require(raw_alignment.get("raw_data_inbox_read_performed") is True, "raw read performed flag must be true")
    require(raw_alignment.get("raw_data_inbox_mutation_performed") is False, "raw mutation flag must be false")
    require(raw_alignment.get("local_raw_zip_present") is True, "local raw zip must be present for this local replay")
    require(raw_alignment.get("local_raw_zip_openable") is True, "local raw zip must be openable")
    require(
        raw_alignment.get("local_raw_package_hash_matches_registered") is False,
        "local raw package hash is expected to remain mismatched in this replay",
    )
    require(
        raw_alignment.get("local_raw_package_size_matches_registered") is False,
        "local raw package size is expected to remain mismatched in this replay",
    )
    require(raw_alignment.get("local_raw_business_member_count") == 9, "business member count must be 9")
    require(raw_alignment.get("local_raw_pdf_member_count") == 8, "PDF member count must be 8")
    require(raw_alignment.get("local_raw_excel_member_count") == 1, "Excel member count must be 1")
    require(raw_alignment.get("member_sha256_public_backfill_performed") is False, "public backfill must be false")
    require(
        raw_alignment.get("member_sha256_public_backfill_blocked_reason")
        == "local_raw_package_hash_or_size_mismatch",
        "public backfill blocked reason mismatch",
    )
    require(
        raw_alignment.get("private_raw_zip_selector") == "public_shape_or_env_private_path",
        "private raw zip selector mismatch",
    )
    require(
        raw_alignment.get("private_raw_zip_selector_status") in {"public_shape_unique_match", "env_path_missing"},
        "private raw zip selector status mismatch",
    )
    require(raw_alignment.get("public_actual_raw_package_hash_committed") is False, "actual raw package hash committed")
    require(raw_alignment.get("public_actual_raw_member_hashes_committed") is False, "actual member hashes committed")
    require(raw_alignment.get("public_raw_member_names_committed") is False, "raw member names committed")

    registered_source_package = manifest.get("registered_source_package", {})
    require(registered_source_package.get("package_name_committed") is False, "raw package name must not be committed")
    require(
        registered_source_package.get("package_ref") == "registered_a0_source_package_private_name_redacted",
        "raw package public ref mismatch",
    )

    raw_boundary = manifest.get("raw_data_boundary", {})
    require(raw_boundary.get("codex_read_required_by_this_phase") is True, "raw read required boundary mismatch")
    require(raw_boundary.get("codex_read_performed_by_this_phase") is True, "raw read performed boundary mismatch")
    require(raw_boundary.get("codex_modify_allowed") is False, "raw modify must be false")
    require(raw_boundary.get("codex_delete_allowed") is False, "raw delete must be false")
    require(raw_boundary.get("codex_move_allowed") is False, "raw move must be false")
    require(raw_boundary.get("codex_rename_allowed") is False, "raw rename must be false")
    require(raw_boundary.get("codex_overwrite_allowed") is False, "raw overwrite must be false")
    require(raw_boundary.get("codex_generate_inside_allowed") is False, "raw generate-inside must be false")
    require(raw_boundary.get("codex_create_extra_files_inside_allowed") is False, "raw extra-file write must be false")
    require(raw_boundary.get("github_commit_allowed") is False, "raw GitHub commit must be false")
    require(
        raw_boundary.get("private_runtime_output_dir") == "KMFA/.codex_private_runtime/",
        "private runtime output dir mismatch",
    )

    for key in BOOLEAN_FALSE_KEYS:
        require(manifest.get(key) is False, f"{key} must be false")
    require(manifest.get("github_upload_deferred_until_stage10_batch") is True, "upload deferral flag must be true")
    safety = manifest.get("public_repo_safety", {})
    for key in PUBLIC_SAFETY_FALSE_KEYS:
        require(safety.get(key) is False, f"public_repo_safety.{key} must be false")

    require(manifest.get("current_data_quality_grade") == "Q2", "quality grade mismatch")
    require(manifest.get("current_report_grade") == "D", "report grade mismatch")
    require(manifest.get("release_permission") == "blocked", "release permission mismatch")
    require("S05-P2" in manifest.get("next_required_step", ""), "next step must point to S05-P2")
    require("separate run" in manifest.get("next_required_step", ""), "next step must preserve one-run boundary")
    require("Stage 1-10" in manifest.get("next_required_step", ""), "next step must preserve batch upload boundary")

    for ref in manifest.get("legacy_s05_p1_refs", []):
        require(Path(ref).exists(), f"missing legacy S05-P1 ref: {ref}")
    for ref in manifest.get("evidence_refs", []):
        require(Path(ref).exists(), f"missing evidence ref: {ref}")
    for evidence in (REPORT_PATH, TEST_RESULTS_PATH):
        require(evidence.exists(), f"missing human evidence: {evidence}")
        if evidence.exists():
            text = evidence.read_text(encoding="utf-8")
            for forbidden in FORBIDDEN_PUBLIC_TEXT:
                require(forbidden not in text, f"forbidden public text {forbidden!r} in {evidence}")

    tracked_files = git_output(["ls-files", "KMFA"]).splitlines()
    forbidden_tracked = [
        path
        for path in tracked_files
        if path.lower().endswith(FORBIDDEN_TRACKED_SUFFIXES) or ".codex_private_runtime/" in path
    ]
    require(not forbidden_tracked, f"forbidden tracked raw/private artifacts: {forbidden_tracked}")

    if require_private_diagnostic:
        require(PRIVATE_DIAGNOSTIC_PATH.exists(), "private diagnostic must exist for local acceptance")
        if PRIVATE_DIAGNOSTIC_PATH.exists():
            private_diag = read_json(PRIVATE_DIAGNOSTIC_PATH)
            require(
                private_diag.get("classification") == "private_raw_diagnostic_do_not_commit",
                "private diagnostic classification mismatch",
            )
            require("actual_package_sha256" in private_diag, "private diagnostic missing actual package hash")
            require("member_records" in private_diag, "private diagnostic missing member records")
        tracked_private = git_output(["ls-files", str(PRIVATE_DIAGNOSTIC_PATH)]).strip()
        require(not tracked_private, "private diagnostic must not be tracked")

    if errors:
        raise ValidationError("\n".join(f"- {error}" for error in errors))
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.3 S05-P1 replay evidence.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--require-private-diagnostic", action="store_true")
    args = parser.parse_args(argv)

    manifest = validate_v013_s05_p1_a0_file_registration(
        args.manifest,
        require_private_diagnostic=args.require_private_diagnostic,
    )
    raw_alignment = manifest["raw_alignment"]
    print(
        "PASS: KMFA v0.1.3 S05-P1 A0 file registration replay validated "
        f"(files={manifest['a0_file_summary']['total_files']}, "
        f"candidates={manifest['a0_candidate_summary']['candidate_count']}, "
        f"raw_zip_openable={str(raw_alignment['local_raw_zip_openable']).lower()}, "
        f"package_hash_match={str(raw_alignment['local_raw_package_hash_matches_registered']).lower()}, "
        f"public_backfill=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
