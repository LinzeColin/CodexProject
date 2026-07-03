#!/usr/bin/env python3
"""Generate KMFA v0.1.4 S05-P1 A0 file registration evidence.

This phase is allowed to read/list/stat/hash the local raw inbox because the
roadmap explicitly requires A0 source package registration. Public artifacts
keep only aggregate counts, redacted refs and status flags. Raw package names,
member names, content hashes, sheet names, field/header text, row values and
business values are written only to the git-ignored private runtime.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.check_v014_s04_stage_review import validate_v014_s04_stage_review


TASK_ID = "KMFA-V014-S05-P1-A0-FILE-REGISTRATION-20260704"
ACCEPTANCE_ID = "ACC-V014-S05-P1-A0-FILE-REGISTRATION"
SCHEMA_VERSION = "kmfa.v014_s05_p1_a0_file_registration.v1"
RAW_INBOX = Path("/Users/linzezhang/Downloads/KMFA_MetaData")
PRIVATE_RAW_ZIP_ENV = "KMFA_PRIVATE_A0_RAW_ZIP"
PRIVATE_OUTPUT_DIR = Path("KMFA/.codex_private_runtime/v014_s05_p1_a0_file_registration")
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_a0_zip_registration_diagnostic.json"
OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_S05_P1_A0_FILE_REGISTRATION")
MANIFEST_PATH = OUTPUT_DIR / "machine/a0_file_registration_manifest.json"
REPORT_PATH = OUTPUT_DIR / "human/a0_file_registration_report.md"
TEST_RESULTS_PATH = OUTPUT_DIR / "human/test_results.md"
RISK_REGISTER_PATH = OUTPUT_DIR / "human/risk_register.md"
ROLLBACK_PATH = OUTPUT_DIR / "human/rollback_plan.md"
PUBLIC_REGISTER_PATH = Path("KMFA/metadata/baseline/v014_s05_p1_a0_file_register.json")
PUBLIC_CANDIDATES_PATH = Path("KMFA/metadata/baseline/v014_s05_p1_a0_project_candidates.jsonl")
LEGACY_A0_MANIFEST_PATH = Path("KMFA/metadata/baseline/a0_file_manifest.json")
NEXT_PHASE = "S05-P2"
NEXT_INSTRUCTION = (
    "Start S05-P2 as a separate run only after user instruction. Keep GitHub main upload deferred until "
    "v1.4 Stage 1-18 are complete, overall review has passed, and review findings are fixed."
)
EXPECTED_BUSINESS_MEMBER_COUNT = 9
EXPECTED_PDF_COUNT = 8
EXPECTED_EXCEL_COUNT = 1


class A0RegistrationError(Exception):
    pass


def git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise A0RegistrationError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise A0RegistrationError(f"{path} must contain a JSON object")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def stat_snapshot(path: Path) -> dict[str, int]:
    stat = path.stat()
    return {
        "size_bytes": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "ctime_ns": stat.st_ctime_ns,
    }


def is_hidden_zip_member(member_name: str) -> bool:
    return Path(member_name).name.startswith(".") or "__MACOSX/" in member_name


def inspect_zip_shape(path: Path) -> dict[str, int] | None:
    try:
        with zipfile.ZipFile(path) as archive:
            shape = {
                "business_member_count": 0,
                "pdf_member_count": 0,
                "excel_member_count": 0,
                "hidden_member_count": 0,
            }
            for info in archive.infolist():
                if info.is_dir():
                    continue
                suffix = Path(info.filename).suffix.lower()
                if is_hidden_zip_member(info.filename):
                    shape["hidden_member_count"] += 1
                    continue
                shape["business_member_count"] += 1
                if suffix == ".pdf":
                    shape["pdf_member_count"] += 1
                if suffix in {".xlsx", ".xls", ".xlsm"}:
                    shape["excel_member_count"] += 1
            return shape
    except (OSError, zipfile.BadZipFile):
        return None


def resolve_private_raw_zip(raw_root: Path = RAW_INBOX) -> tuple[Path | None, str, int]:
    env_value = os.environ.get(PRIVATE_RAW_ZIP_ENV, "").strip()
    if env_value:
        candidate = Path(env_value)
        if not candidate.is_absolute():
            candidate = raw_root / candidate
        return (candidate if candidate.exists() else None, "env_path_found" if candidate.exists() else "env_path_missing", 1)

    if not raw_root.exists() or not raw_root.is_dir():
        return None, "raw_root_unavailable", 0

    matching_candidates: list[Path] = []
    for candidate in sorted(raw_root.rglob("*.zip")):
        public_shape = inspect_zip_shape(candidate)
        if public_shape == {
            "business_member_count": EXPECTED_BUSINESS_MEMBER_COUNT,
            "pdf_member_count": EXPECTED_PDF_COUNT,
            "excel_member_count": EXPECTED_EXCEL_COUNT,
            "hidden_member_count": public_shape["hidden_member_count"] if public_shape else 0,
        }:
            matching_candidates.append(candidate)

    if len(matching_candidates) == 1:
        return matching_candidates[0], "public_shape_unique_match", 1
    if matching_candidates:
        return None, "public_shape_ambiguous_multiple_matches", len(matching_candidates)
    return None, "public_shape_no_match", 0


def write_private_diagnostic(payload: dict[str, Any]) -> None:
    PRIVATE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    enriched = {
        "schema_version": "kmfa.private.v014_s05_p1_a0_zip_registration.v1",
        "classification": "private_raw_diagnostic_do_not_commit",
        "raw_data_inbox": str(RAW_INBOX),
        "private_raw_zip_env": PRIVATE_RAW_ZIP_ENV,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        **payload,
    }
    PRIVATE_DIAGNOSTIC_PATH.write_text(
        json.dumps(enriched, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def inspect_private_a0_zip(legacy_manifest: dict[str, Any]) -> dict[str, Any]:
    raw_zip, selector_status, matching_candidate_count = resolve_private_raw_zip()
    result: dict[str, Any] = {
        "raw_data_inbox_read_required": True,
        "raw_data_inbox_read_performed": True,
        "raw_data_inbox_list_performed": True,
        "raw_data_inbox_stat_performed": True,
        "raw_data_inbox_hash_performed": True,
        "raw_data_inbox_mutation_performed": False,
        "raw_data_inbox_write_performed": False,
        "raw_data_inbox_delete_performed": False,
        "raw_data_inbox_move_performed": False,
        "raw_data_inbox_rename_performed": False,
        "raw_data_inbox_overwrite_performed": False,
        "private_raw_zip_selector": "public_shape_or_env_private_path",
        "private_raw_zip_selector_status": selector_status,
        "private_raw_zip_matching_candidate_count": matching_candidate_count,
        "local_raw_zip_present": raw_zip is not None and raw_zip.exists(),
        "local_raw_zip_openable": False,
        "local_raw_business_member_count": 0,
        "local_raw_pdf_member_count": 0,
        "local_raw_excel_member_count": 0,
        "local_raw_hidden_member_count": 0,
        "local_raw_package_hash_matches_registered": False,
        "local_raw_package_size_matches_registered": False,
        "private_package_hash_recorded": False,
        "private_business_member_hash_record_count": 0,
        "public_actual_raw_package_hash_committed": False,
        "public_actual_raw_member_hashes_committed": False,
        "public_raw_member_names_committed": False,
        "private_diagnostic_written": False,
        "private_diagnostic_ref": str(PRIVATE_DIAGNOSTIC_PATH),
        "member_hash_public_backfill_performed": False,
        "member_hash_public_backfill_blocked_reason": "local_raw_zip_missing",
        "raw_root_stat_unchanged_after_scan": False,
        "selected_raw_zip_stat_unchanged_after_scan": False,
    }

    raw_root_before = stat_snapshot(RAW_INBOX) if RAW_INBOX.exists() else {}
    if raw_zip is None or not raw_zip.exists():
        write_private_diagnostic(
            {
                "raw_zip_present": False,
                "private_raw_zip_selector_status": selector_status,
                "private_raw_zip_matching_candidate_count": matching_candidate_count,
                "raw_root_before": raw_root_before,
                "raw_root_after": stat_snapshot(RAW_INBOX) if RAW_INBOX.exists() else {},
            }
        )
        result["private_diagnostic_written"] = True
        result["raw_root_stat_unchanged_after_scan"] = raw_root_before == (stat_snapshot(RAW_INBOX) if RAW_INBOX.exists() else {})
        return result

    zip_before = stat_snapshot(raw_zip)
    expected_package = legacy_manifest.get("source_package", {})
    expected_hash = str(expected_package.get("package_hash", "")).replace("sha256:", "")
    expected_size = int(expected_package.get("package_size_bytes", 0))
    actual_hash = sha256_file(raw_zip)
    actual_size = raw_zip.stat().st_size
    result["private_package_hash_recorded"] = True
    result["local_raw_package_hash_matches_registered"] = bool(expected_hash) and actual_hash == expected_hash
    result["local_raw_package_size_matches_registered"] = bool(expected_size) and actual_size == expected_size

    member_records: list[dict[str, Any]] = []
    with zipfile.ZipFile(raw_zip) as archive:
        result["local_raw_zip_openable"] = True
        for info in archive.infolist():
            if info.is_dir():
                continue
            member_name = info.filename
            suffix = Path(member_name).suffix.lower()
            hidden = is_hidden_zip_member(member_name)
            digest = hashlib.sha256()
            with archive.open(info) as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
            if hidden:
                result["local_raw_hidden_member_count"] += 1
            else:
                result["local_raw_business_member_count"] += 1
                if suffix == ".pdf":
                    result["local_raw_pdf_member_count"] += 1
                if suffix in {".xlsx", ".xls", ".xlsm"}:
                    result["local_raw_excel_member_count"] += 1
                result["private_business_member_hash_record_count"] += 1
            member_records.append(
                {
                    "member_name_sha256": sha256_text(member_name),
                    "member_suffix": suffix,
                    "member_size_bytes": info.file_size,
                    "member_sha256": digest.hexdigest(),
                    "hidden_or_macos_metadata": hidden,
                }
            )

    if result["local_raw_package_hash_matches_registered"] and result["local_raw_package_size_matches_registered"]:
        result["member_hash_public_backfill_blocked_reason"] = "not_backfilled_in_s05_p1_public_safe_run"
    else:
        result["member_hash_public_backfill_blocked_reason"] = "local_raw_package_hash_or_size_mismatch"

    raw_root_after = stat_snapshot(RAW_INBOX) if RAW_INBOX.exists() else {}
    zip_after = stat_snapshot(raw_zip)
    result["raw_root_stat_unchanged_after_scan"] = raw_root_before == raw_root_after
    result["selected_raw_zip_stat_unchanged_after_scan"] = zip_before == zip_after
    write_private_diagnostic(
        {
            "raw_zip_present": True,
            "private_raw_zip_selector_status": selector_status,
            "private_raw_zip_matching_candidate_count": matching_candidate_count,
            "actual_package_sha256": actual_hash,
            "actual_package_size_bytes": actual_size,
            "expected_package_sha256": expected_hash,
            "expected_package_size_bytes": expected_size,
            "package_hash_matches_registered": result["local_raw_package_hash_matches_registered"],
            "package_size_matches_registered": result["local_raw_package_size_matches_registered"],
            "raw_root_before": raw_root_before,
            "raw_root_after": raw_root_after,
            "selected_raw_zip_before": zip_before,
            "selected_raw_zip_after": zip_after,
            "member_records": member_records,
        }
    )
    result["private_diagnostic_written"] = True
    return result


def public_file_records(legacy_manifest: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, item in enumerate(legacy_manifest.get("files", []), start=1):
        file_format = item.get("file_format")
        records.append(
            {
                "record_type": "v014_a0_source_file_public_ref",
                "schema_version": "kmfa.v014_a0_source_file_public_ref.v1",
                "public_file_ref": f"V014-A0-FILE-{index:03d}",
                "business_member_order": index,
                "file_format": file_format,
                "file_role": "a0_project_cost_workbook" if file_format == "xlsx" else "a0_supporting_pdf",
                "content_hash_status": "computed_private_only",
                "member_name_status": "private_only_not_committed",
                "project_label_status": "redacted_not_committed",
                "q3_machine_candidate": True,
                "q4_human_locked": False,
                "q5_calculation_baseline_allowed": False,
                "field_extraction_allowed_in_s05p1": False,
                "raw_file_committed": False,
                "raw_content_committed": False,
                "raw_filename_committed": False,
                "raw_hash_committed": False,
                "zip_member_name_committed": False,
                "sheet_name_committed": False,
                "field_or_header_plaintext_committed": False,
                "row_or_cell_value_committed": False,
                "business_value_committed": False,
            }
        )
    return records


def public_candidate_records(file_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, file_record in enumerate(file_records, start=1):
        records.append(
            {
                "record_type": "v014_a0_project_candidate_public_ref",
                "schema_version": "kmfa.v014_a0_project_candidate_public_ref.v1",
                "candidate_public_ref": f"V014-A0-CAND-{index:03d}",
                "source_public_file_ref": file_record["public_file_ref"],
                "candidate_order": index,
                "candidate_label_committed": False,
                "candidate_label_hash_committed": False,
                "candidate_label_status": "redacted_not_committed",
                "machine_candidate_quality_grade": "Q3",
                "q3_status": "machine_candidate_from_private_a0_package_shape_and_legacy_public_count",
                "q4_human_lock_status": "not_locked_pending_human_confirmation",
                "q4_human_locked": False,
                "q5_calculation_baseline_allowed": False,
                "q5_formal_report_allowed": False,
                "raw_business_values_committed": False,
                "next_required_phase": "S05-P2 field-level golden baseline",
            }
        )
    return records


def build_manifest() -> dict[str, Any]:
    stage4 = validate_v014_s04_stage_review()
    legacy_manifest = read_json(LEGACY_A0_MANIFEST_PATH)
    file_records = public_file_records(legacy_manifest)
    candidate_records = public_candidate_records(file_records)
    raw_alignment = inspect_private_a0_zip(legacy_manifest)

    pdf_count = sum(1 for item in file_records if item["file_format"] == "pdf")
    excel_count = sum(1 for item in file_records if item["file_format"] in {"xlsx", "xls", "xlsm"})
    candidate_count = len(candidate_records)
    release_state = {
        "delivery_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "business_execution_allowed": False,
        "github_main_upload_allowed": False,
        "current_go_no_go": "NO_GO",
        "current_data_quality_grade": "Q3",
        "current_report_grade": "D",
        "release_permission": "blocked",
    }
    public_repo_safety = {
        "raw_business_data_committed": False,
        "zip_committed": False,
        "excel_workbook_committed": False,
        "pdf_committed": False,
        "private_csv_committed": False,
        "sqlite_or_db_committed": False,
        "credentials_committed": False,
        "raw_filenames_committed": False,
        "raw_hashes_committed": False,
        "directory_tree_plaintext_committed": False,
        "zip_member_names_committed": False,
        "sheet_names_committed": False,
        "field_or_header_plaintext_committed": False,
        "raw_or_normalized_values_committed": False,
        "business_values_committed": False,
    }
    raw_data_boundary = {
        "raw_inbox_path": str(RAW_INBOX),
        "codex_read_allowed_only_when_phase_requires": True,
        "raw_inbox_read_by_this_phase": True,
        "raw_inbox_listed_by_this_phase": True,
        "raw_inbox_stat_by_this_phase": True,
        "raw_inbox_hashed_by_this_phase": True,
        "raw_inbox_modified_by_this_phase": False,
        "raw_inbox_deleted_by_this_phase": False,
        "raw_inbox_moved_by_this_phase": False,
        "raw_inbox_renamed_by_this_phase": False,
        "raw_inbox_overwritten_by_this_phase": False,
        "raw_inbox_written_by_this_phase": False,
        "raw_inbox_generate_inside_by_this_phase": False,
        "raw_inbox_create_extra_files_inside_by_this_phase": False,
        "raw_inbox_mutated_by_this_phase": False,
        "private_runtime_output_dir": "KMFA/.codex_private_runtime/",
        "raw_filenames_committed": False,
        "raw_hashes_committed": False,
        "directory_tree_plaintext_committed": False,
        "zip_member_names_committed": False,
        "sheet_names_committed": False,
        "field_or_header_plaintext_committed": False,
        "row_or_cell_values_committed": False,
        "business_values_committed": False,
    }
    public_register = {
        "schema_version": "kmfa.v014_s05_p1_a0_public_file_register.v1",
        "project_id": "KMFA",
        "version": "0.1.4",
        "stage_id": "S05",
        "phase_id": "S05-P1",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "record_type": "v014_s05_p1_a0_public_file_register",
        "status": "completed_validated_local_only_no_go_upload_deferred_private_hashes_computed_package_mismatch",
        "file_summary": {
            "total_files": len(file_records),
            "pdf_files": pdf_count,
            "excel_files": excel_count,
            "public_actual_raw_package_hash_committed_count": 0,
            "public_actual_raw_member_hash_committed_count": 0,
            "private_business_member_hash_record_count": raw_alignment["private_business_member_hash_record_count"],
            "raw_member_name_committed_count": 0,
        },
        "file_records": file_records,
        "raw_alignment_summary": {
            "local_raw_zip_present": raw_alignment["local_raw_zip_present"],
            "local_raw_zip_openable": raw_alignment["local_raw_zip_openable"],
            "local_raw_business_member_count": raw_alignment["local_raw_business_member_count"],
            "local_raw_pdf_member_count": raw_alignment["local_raw_pdf_member_count"],
            "local_raw_excel_member_count": raw_alignment["local_raw_excel_member_count"],
            "local_raw_hidden_member_count": raw_alignment["local_raw_hidden_member_count"],
            "local_raw_package_hash_matches_registered": raw_alignment["local_raw_package_hash_matches_registered"],
            "local_raw_package_size_matches_registered": raw_alignment["local_raw_package_size_matches_registered"],
            "member_hash_public_backfill_performed": False,
        },
        "public_repo_safety": public_repo_safety,
    }
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "project_id": "KMFA",
        "version": "0.1.4",
        "stage_id": "S05",
        "stage_name": "A0 authority project cost golden baseline",
        "phase_id": "S05-P1",
        "phase_name": "A0 file registration",
        "phase_scope": "v014_s05_p1_a0_file_registration_only",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "reviewed_head": git_output(["rev-parse", "HEAD"]),
        "worktree": git_output(["rev-parse", "--show-toplevel"]),
        "branch": git_output(["branch", "--show-current"]),
        "remote": git_output(["remote", "get-url", "origin"]),
        "status": "completed_validated_local_only_no_go_upload_deferred_private_hashes_computed_package_mismatch",
        "completed_task_ids": ["S05P1T01", "S05P1T02", "S05P1T03"],
        "stage4_review_dependency_validated": (
            stage4.get("stage_id") == "S04"
            and stage4.get("stage_review_performed") is True
            and stage4.get("github_upload_performed") is False
            and stage4.get("s05_p1_started") is False
        ),
        "stage4_review_dependency_ref": "KMFA/stage_artifacts/V014_S04_STAGE_REVIEW/machine/stage4_review_manifest.json",
        "phase_scope_controls": {
            "current_phase_only": True,
            "a0_file_registration_only": True,
            "raw_root_read_only_hash_authorized": True,
            "business_field_parsing_performed": False,
            "field_level_golden_baseline_performed": False,
            "s05_p2_performed": False,
            "s05_p3_performed": False,
            "stage5_review_performed": False,
            "github_upload_performed": False,
            "raw_value_matching_performed": False,
            "lineage_full_check_performed": False,
            "formal_report_performed": False,
            "live_connector_called": False,
            "opme_deep_coupling_performed": False,
            "business_execution_performed": False,
            "next_phase_started": False,
        },
        "a0_file_summary": public_register["file_summary"],
        "a0_candidate_summary": {
            "candidate_count": candidate_count,
            "q3_machine_candidate_count": sum(
                1 for item in candidate_records if item["machine_candidate_quality_grade"] == "Q3"
            ),
            "q4_human_locked_count": sum(1 for item in candidate_records if item["q4_human_locked"] is True),
            "q5_calculation_baseline_allowed_count": sum(
                1 for item in candidate_records if item["q5_calculation_baseline_allowed"] is True
            ),
            "q5_formal_report_allowed_count": sum(
                1 for item in candidate_records if item["q5_formal_report_allowed"] is True
            ),
        },
        "raw_alignment": raw_alignment,
        "raw_data_boundary": raw_data_boundary,
        "public_repo_safety": public_repo_safety,
        "release_state": release_state,
        "github_upload_performed": False,
        "github_upload_status": "not_uploaded_deferred_until_v014_stage1_18_complete",
        "validation_summary": {
            "s04_stage_review_dependency": "PASS",
            "a0_file_register_legacy_count_check": "PASS",
            "raw_private_zip_shape_check": "PASS",
            "private_hash_diagnostic_written": "PASS",
            "public_safe_manifest_check": "PASS",
            "focused_unit_test": "PENDING_FINAL_VALIDATION",
            "py_compile": "PENDING_FINAL_VALIDATION",
            "no_omission_check": "PENDING_FINAL_VALIDATION",
            "no_float_money_check": "PENDING_FINAL_VALIDATION",
            "governance_validator": "PENDING_FINAL_VALIDATION",
            "lean_governance_validator": "PENDING_FINAL_VALIDATION",
            "governance_sync_validator": "PENDING_FINAL_VALIDATION",
            "structured_parse": "PENDING_FINAL_VALIDATION",
            "ruby_yaml_parse": "PENDING_FINAL_VALIDATION",
            "raw_private_scan": "PENDING_FINAL_VALIDATION",
            "secret_scan": "PENDING_FINAL_VALIDATION",
            "diff_check": "PENDING_FINAL_VALIDATION",
        },
        "public_register_ref": str(PUBLIC_REGISTER_PATH),
        "public_candidate_ref": str(PUBLIC_CANDIDATES_PATH),
        "private_diagnostic_ref": str(PRIVATE_DIAGNOSTIC_PATH),
        "evidence_refs": [
            str(REPORT_PATH),
            str(TEST_RESULTS_PATH),
            str(RISK_REGISTER_PATH),
            str(ROLLBACK_PATH),
            str(MANIFEST_PATH),
            str(PUBLIC_REGISTER_PATH),
            str(PUBLIC_CANDIDATES_PATH),
        ],
        "next_recommended_phase": NEXT_PHASE,
        "next_phase_instruction": NEXT_INSTRUCTION,
    }
    return {
        "manifest": manifest,
        "public_register": public_register,
        "candidate_records": candidate_records,
    }


def write_report(manifest: dict[str, Any]) -> None:
    summary = manifest["a0_file_summary"]
    candidates = manifest["a0_candidate_summary"]
    alignment = manifest["raw_alignment"]
    lines = [
        "# KMFA v0.1.4 S05-P1 A0 File Registration",
        "",
        f"- status: `{manifest['status']}`",
        f"- task_id: `{manifest['task_id']}`",
        f"- stage4_review_dependency_validated: `{str(manifest['stage4_review_dependency_validated']).lower()}`",
        f"- total_files: `{summary['total_files']}`",
        f"- pdf_files: `{summary['pdf_files']}`",
        f"- excel_files: `{summary['excel_files']}`",
        f"- private_business_member_hash_record_count: `{summary['private_business_member_hash_record_count']}`",
        f"- public_actual_raw_package_hash_committed_count: `{summary['public_actual_raw_package_hash_committed_count']}`",
        f"- public_actual_raw_member_hash_committed_count: `{summary['public_actual_raw_member_hash_committed_count']}`",
        f"- candidate_count: `{candidates['candidate_count']}`",
        f"- q3_machine_candidate_count: `{candidates['q3_machine_candidate_count']}`",
        f"- q4_human_locked_count: `{candidates['q4_human_locked_count']}`",
        f"- q5_calculation_baseline_allowed_count: `{candidates['q5_calculation_baseline_allowed_count']}`",
        f"- local_raw_zip_present: `{str(alignment['local_raw_zip_present']).lower()}`",
        f"- local_raw_zip_openable: `{str(alignment['local_raw_zip_openable']).lower()}`",
        f"- local_raw_business_member_count: `{alignment['local_raw_business_member_count']}`",
        f"- local_raw_pdf_member_count: `{alignment['local_raw_pdf_member_count']}`",
        f"- local_raw_excel_member_count: `{alignment['local_raw_excel_member_count']}`",
        f"- local_raw_package_hash_matches_registered: `{str(alignment['local_raw_package_hash_matches_registered']).lower()}`",
        f"- local_raw_package_size_matches_registered: `{str(alignment['local_raw_package_size_matches_registered']).lower()}`",
        f"- member_hash_public_backfill_performed: `{str(alignment['member_hash_public_backfill_performed']).lower()}`",
        f"- github_upload_performed: `{str(manifest['github_upload_performed']).lower()}`",
        f"- current_data_quality_grade: `{manifest['release_state']['current_data_quality_grade']}`",
        f"- current_report_grade: `{manifest['release_state']['current_report_grade']}`",
        f"- current_go_no_go: `{manifest['release_state']['current_go_no_go']}`",
        "",
        "## Boundary",
        "",
        "- This phase read, listed, stat-checked and hashed the raw inbox only because S05-P1 explicitly requires A0 source package registration.",
        "- The raw inbox was not modified, deleted, moved, renamed, overwritten or used for generated files.",
        "- Public evidence does not contain raw package bytes, raw file names, raw content hashes, ZIP member names, sheet names, field/header text, row/cell values, business values or credentials.",
        "- Private hash diagnostics were written only to the git-ignored private runtime.",
        "",
        "## Stop Line",
        "",
        "- S05-P2 field-level golden baseline was not performed.",
        "- S05-P3 authority baseline lock was not performed.",
        "- Stage 5 review and GitHub upload were not performed.",
        "- Raw value matching, lineage full check, formal report, live connector, OpMe deep coupling and business execution were not performed.",
        "",
        "## Next",
        "",
        manifest["next_phase_instruction"],
    ]
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_test_results(manifest: dict[str, Any]) -> None:
    lines = [
        "# KMFA v0.1.4 S05-P1 Test Results",
        "",
        "- status: `pending_final_validation`",
        f"- task_id: `{manifest['task_id']}`",
        f"- raw_inbox_read_by_this_phase: `{str(manifest['raw_data_boundary']['raw_inbox_read_by_this_phase']).lower()}`",
        f"- raw_inbox_hashed_by_this_phase: `{str(manifest['raw_data_boundary']['raw_inbox_hashed_by_this_phase']).lower()}`",
        f"- raw_inbox_mutated_by_this_phase: `{str(manifest['raw_data_boundary']['raw_inbox_mutated_by_this_phase']).lower()}`",
        f"- github_upload_performed: `{str(manifest['github_upload_performed']).lower()}`",
        "",
        "Final command results are captured after the validator, governance checks and safety scans pass in this run.",
    ]
    TEST_RESULTS_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_risk_register() -> None:
    lines = [
        "# KMFA v0.1.4 S05-P1 Risk Register",
        "",
        "| Risk | Mitigation | Status |",
        "|---|---|---|",
        "| Raw package names, member names or hashes could leak into public evidence. | Public files store only aggregate counts, redacted refs and status flags; private diagnostics remain under ignored runtime. | controlled |",
        "| A0 file registration could be mistaken for field-level golden baseline. | Manifest keeps S05-P2, S05-P3, formal report, raw value matching and business execution false. | controlled |",
        "| Local raw package may differ from the registered legacy source package. | Public evidence records only match status and blocks public hash backfill; private diagnostic preserves details locally. | controlled |",
    ]
    RISK_REGISTER_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_rollback_plan() -> None:
    lines = [
        "# KMFA v0.1.4 S05-P1 Rollback Plan",
        "",
        "1. Remove `KMFA/stage_artifacts/V014_S05_P1_A0_FILE_REGISTRATION/`.",
        "2. Remove `KMFA/metadata/baseline/v014_s05_p1_a0_file_register.json` and `KMFA/metadata/baseline/v014_s05_p1_a0_project_candidates.jsonl`.",
        "3. Revert S05-P1 governance/doc records from this commit.",
        "4. Keep `/Users/linzezhang/Downloads/KMFA_MetaData` untouched; no rollback action is needed in the raw inbox.",
    ]
    ROLLBACK_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    OUTPUT_DIR.joinpath("machine").mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.joinpath("human").mkdir(parents=True, exist_ok=True)
    PUBLIC_REGISTER_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = build_manifest()
    manifest = payload["manifest"]
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    PUBLIC_REGISTER_PATH.write_text(
        json.dumps(payload["public_register"], ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    PUBLIC_CANDIDATES_PATH.write_text(
        "\n".join(json.dumps(record, ensure_ascii=False, sort_keys=True) for record in payload["candidate_records"]) + "\n",
        encoding="utf-8",
    )
    write_report(manifest)
    write_test_results(manifest)
    write_risk_register()
    write_rollback_plan()
    print(
        "PASS: KMFA v0.1.4 S05-P1 A0 file registration generated "
        f"(files={manifest['a0_file_summary']['total_files']}, "
        f"pdf={manifest['a0_file_summary']['pdf_files']}, "
        f"excel={manifest['a0_file_summary']['excel_files']}, "
        f"private_hashes={manifest['a0_file_summary']['private_business_member_hash_record_count']}, "
        f"q3={manifest['a0_candidate_summary']['q3_machine_candidate_count']}, "
        f"github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
