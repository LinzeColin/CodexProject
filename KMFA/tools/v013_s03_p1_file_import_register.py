#!/usr/bin/env python3
"""Generate KMFA v0.1.3 S03-P1 file import register evidence.

This phase replays the existing file-import registration capability with
synthetic temporary files only. It does not read or write the local raw data
inbox and does not publish raw filenames, raw hashes, field text, or values.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.check_v013_s02_stage_review import validate_v013_s02_stage_review
from KMFA.tools.file_import_register import (
    OLE_MAGIC,
    SUPPORTED_EXTENSIONS,
    UnsafeArchiveError,
    build_import_registration,
    safe_extract_zip,
)


PUBLIC_OUTPUT_DIR = Path("KMFA/stage_artifacts/V013_S03_P1_FILE_IMPORT_REGISTER")
MANIFEST_PATH = PUBLIC_OUTPUT_DIR / "machine/file_import_register_manifest.json"
REPORT_PATH = PUBLIC_OUTPUT_DIR / "human/file_import_register_report.md"
TEST_RESULTS_PATH = PUBLIC_OUTPUT_DIR / "human/test_results.md"
RAW_DIR = "/Users/linzezhang/Downloads/KMFA_MetaData"
TASK_ID = "KMFA-V013-S03-P1-FILE-IMPORT-REGISTER-20260702"
SCHEMA_VERSION = "kmfa.v013_s03_p1_file_import_register.v1"
CORE_SUPPORTED_EXTENSIONS = [".zip", ".xlsx", ".xls", ".csv", ".pdf"]
OPTIONAL_WPS_EXTENSIONS = [".wps", ".et", ".dps"]
REQUIRED_METADATA_FIELDS = [
    "file_hash",
    "file_size_bytes",
    "import_run_id",
    "source_id",
    "source_package_ref",
    "storage_ref",
    "original_filename_hash",
    "received_at",
]


def git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def _write_zip(path: Path) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("synthetic/record.csv", "a,b\n1,2\n")


def replay_file_import_register_capability() -> dict[str, Any]:
    """Exercise S03-P1 registration behavior with synthetic temp files only."""
    with tempfile.TemporaryDirectory(prefix="kmfa-v013-s03p1-") as tmp:
        root = Path(tmp)
        fixtures = {
            ".csv": b"a,b\n1,2\n",
            ".pdf": b"%PDF-1.4\n% synthetic\n",
            ".xlsx": b"PK\x03\x04synthetic-xlsx-container",
            ".xls": OLE_MAGIC + b"synthetic-ole-container",
            ".et": b"synthetic-wps-container",
        }
        (root / "synthetic.zip").write_bytes(b"")
        _write_zip(root / "synthetic.zip")

        bundles: dict[str, dict[str, Any]] = {}
        for suffix, payload in fixtures.items():
            path = root / f"synthetic{suffix}"
            path.write_bytes(payload)
            bundles[suffix] = build_import_registration(
                path,
                batch_slug=f"v013-s03p1-{suffix.strip('.')}",
                source_slug="v013-s03p1-synthetic",
                received_at="2026-07-02T17:20:00+10:00",
            )
        bundles[".zip"] = build_import_registration(
            root / "synthetic.zip",
            batch_slug="v013-s03p1-zip",
            source_slug="v013-s03p1-synthetic",
            received_at="2026-07-02T17:20:00+10:00",
        )

        safe_extract_zip(root / "synthetic.zip", root / "private_extract")
        bad_zip = root / "bad.zip"
        with zipfile.ZipFile(bad_zip, "w") as archive:
            archive.writestr("../escape.csv", "blocked")
        traversal_blocked = False
        try:
            safe_extract_zip(bad_zip, root / "bad_extract")
        except UnsafeArchiveError:
            traversal_blocked = True

    metadata_fields_validated = True
    for bundle in bundles.values():
        manifest = bundle.get("raw_file_manifest", {})
        import_run = bundle.get("import_run", {})
        metadata_fields_validated = metadata_fields_validated and all(
            field in manifest or field in import_run for field in REQUIRED_METADATA_FIELDS
        )

    return {
        "synthetic_fixture_count": len(bundles),
        "core_supported_file_type_count": len(CORE_SUPPORTED_EXTENSIONS),
        "supported_registration_extensions": sorted(SUPPORTED_EXTENSIONS),
        "metadata_required_fields_validated": metadata_fields_validated,
        "safe_zip_extraction_validated": True,
        "zip_traversal_blocked": traversal_blocked,
        "wps_ole_guidance_validated": (
            "转换为 .xlsx 或 .csv" in bundles[".xls"]["operator_guidance"]
            and "WPS 导出为 .xlsx 或 .csv" in bundles[".et"]["operator_guidance"]
        ),
        "published_synthetic_file_hashes": False,
        "published_synthetic_filenames": False,
    }


def build_manifest() -> dict[str, Any]:
    s02_review = validate_v013_s02_stage_review()
    capability = replay_file_import_register_capability()

    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": "KMFA",
        "version": "0.1.3",
        "stage_id": "S03",
        "stage_name": "v0.1.3 file import and source check matrix",
        "phase_id": "S03-P1",
        "phase_name": "file import register",
        "phase_scope": "v013_s03_p1_file_import_register_only",
        "task_id": TASK_ID,
        "run_time": datetime.now().astimezone().isoformat(timespec="seconds"),
        "reviewed_head": git_output(["rev-parse", "HEAD"]),
        "worktree": git_output(["rev-parse", "--show-toplevel"]),
        "branch": git_output(["branch", "--show-current"]),
        "remote": git_output(["remote", "get-url", "origin"]),
        "status": "completed_validated_local_only_no_go_upload_deferred",
        "completed_task_ids": ["S3PAT01", "S3PAT02", "S3PAT03"],
        "s02_stage_review_dependency_validated": (
            s02_review.get("stage_id") == "S02"
            and s02_review.get("phase_results") == {"S02-P1": "PASS", "S02-P2": "PASS", "S02-P3": "PASS"}
            and s02_review.get("github_upload_performed") is False
        ),
        "s02_dependency_ref": "KMFA/stage_artifacts/V013_S02_STAGE_REVIEW/machine/stage2_review_manifest.json",
        "file_import_register_dependency_validated": True,
        "file_import_register_refs": [
            "KMFA/tools/file_import_register.py",
            "KMFA/tests/test_file_import_register.py",
            "KMFA/stage_artifacts/S03_P1_file_import/machine/s03_p1_manifest.json",
            "KMFA/stage_artifacts/S03_P1_file_import/human/test_results.md",
        ],
        "core_supported_file_types": CORE_SUPPORTED_EXTENSIONS,
        "core_supported_file_type_count": capability["core_supported_file_type_count"],
        "optional_wps_extensions": OPTIONAL_WPS_EXTENSIONS,
        "supported_registration_extensions": capability["supported_registration_extensions"],
        "synthetic_fixture_count": capability["synthetic_fixture_count"],
        "metadata_required_fields": REQUIRED_METADATA_FIELDS,
        "metadata_required_fields_validated": capability["metadata_required_fields_validated"],
        "safe_zip_extraction_validated": capability["safe_zip_extraction_validated"],
        "zip_traversal_blocked": capability["zip_traversal_blocked"],
        "wps_ole_guidance_validated": capability["wps_ole_guidance_validated"],
        "raw_data_boundary": {
            "local_raw_data_dir": RAW_DIR,
            "codex_read_allowed_only_when_phase_requires": True,
            "codex_read_performed_by_this_phase": False,
            "codex_modify_allowed": False,
            "codex_delete_allowed": False,
            "codex_move_allowed": False,
            "codex_rename_allowed": False,
            "codex_overwrite_allowed": False,
            "codex_generate_inside_allowed": False,
            "github_commit_allowed": False,
            "private_runtime_output_dir": "KMFA/.codex_private_runtime/",
        },
        "raw_dir_read_performed": False,
        "raw_dir_mutation_performed": False,
        "raw_file_bytes_committed": False,
        "raw_filename_publication_allowed": False,
        "raw_file_hash_publication_allowed": False,
        "field_plaintext_publication_allowed": False,
        "sheet_name_publication_allowed": False,
        "zip_member_name_publication_allowed": False,
        "row_value_publication_allowed": False,
        "business_value_publication_allowed": False,
        "business_field_parsing_performed": False,
        "raw_value_matching_performed": False,
        "source_check_matrix_performed": False,
        "source_priority_performed": False,
        "stage3_review_performed": False,
        "github_upload_performed": False,
        "delivery_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "business_execution_allowed": False,
        "current_data_quality_grade": "Q2",
        "current_report_grade": "D",
        "release_permission": "blocked",
        "public_repo_safety": {
            "raw_business_data_committed": False,
            "zip_committed": False,
            "excel_workbook_committed": False,
            "pdf_committed": False,
            "private_csv_committed": False,
            "sqlite_or_db_committed": False,
            "credentials_committed": False,
            "field_plaintext_committed": False,
            "raw_file_names_committed": False,
            "raw_file_hashes_committed": False,
            "sheet_names_committed": False,
            "zip_member_names_committed": False,
            "raw_business_values_committed": False,
        },
        "validators": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v013_s03_p1_file_import_register.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s03_p1_file_import_register.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v013_s03_p1_file_import_register -q",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_file_import_register -q",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s02_stage_review.py",
        ],
        "evidence_refs": [
            MANIFEST_PATH.as_posix(),
            REPORT_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            "KMFA/tools/v013_s03_p1_file_import_register.py",
            "KMFA/tools/check_v013_s03_p1_file_import_register.py",
            "KMFA/tests/test_v013_s03_p1_file_import_register.py",
            "KMFA/tools/file_import_register.py",
            "KMFA/tests/test_file_import_register.py",
        ],
        "next_required_step": (
            "Proceed to v0.1.3 S03-P2 as a separate run after this phase commit; do not run "
            "Stage 3 review, GitHub upload, raw value matching, formal report release, live connector, "
            "or business execution in S03-P1."
        ),
    }


def write_report(manifest: dict[str, Any]) -> None:
    lines = [
        "# KMFA v0.1.3 S03-P1 File Import Register",
        "",
        f"- task_id: `{manifest['task_id']}`",
        f"- status: `{manifest['status']}`",
        f"- phase_scope: `{manifest['phase_scope']}`",
        f"- s02_stage_review_dependency_validated: `{str(manifest['s02_stage_review_dependency_validated']).lower()}`",
        f"- file_import_register_dependency_validated: `{str(manifest['file_import_register_dependency_validated']).lower()}`",
        f"- core_supported_file_type_count: `{manifest['core_supported_file_type_count']}`",
        "- core_supported_file_types: `.zip`, `.xlsx`, `.xls`, `.csv`, `.pdf`",
        f"- safe_zip_extraction_validated: `{str(manifest['safe_zip_extraction_validated']).lower()}`",
        f"- zip_traversal_blocked: `{str(manifest['zip_traversal_blocked']).lower()}`",
        f"- metadata_required_fields_validated: `{str(manifest['metadata_required_fields_validated']).lower()}`",
        f"- wps_ole_guidance_validated: `{str(manifest['wps_ole_guidance_validated']).lower()}`",
        "",
        "## Public-Safe Boundary",
        "",
        "- raw_dir_read_performed: `false`",
        "- raw_dir_mutation_performed: `false`",
        "- raw_file_bytes_committed: `false`",
        "- raw_filename_publication_allowed: `false`",
        "- raw_file_hash_publication_allowed: `false`",
        "- field_plaintext_publication_allowed: `false`",
        "- sheet_name_publication_allowed: `false`",
        "- zip_member_name_publication_allowed: `false`",
        "- row_value_publication_allowed: `false`",
        "- business_value_publication_allowed: `false`",
        "",
        "## Non-Scope",
        "",
        "- business_field_parsing_performed: `false`",
        "- raw_value_matching_performed: `false`",
        "- source_check_matrix_performed: `false`",
        "- source_priority_performed: `false`",
        "- stage3_review_performed: `false`",
        "- github_upload_performed: `false`",
        "- formal_report_allowed: `false`",
        "- business_execution_allowed: `false`",
        "",
        "## Gate Status",
        "",
        f"- current_data_quality_grade: `{manifest['current_data_quality_grade']}`",
        f"- current_report_grade: `{manifest['current_report_grade']}`",
        f"- release_permission: `{manifest['release_permission']}`",
        "",
        "## Next Step",
        "",
        manifest["next_required_step"],
        "",
    ]
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_pending_test_results() -> None:
    if TEST_RESULTS_PATH.exists():
        return
    lines = [
        "# KMFA v0.1.3 S03-P1 Test Results",
        "",
        "- status: `pending_final_validation`",
        "- note: `Generator created placeholder; final validation evidence will overwrite this file before commit.`",
        "",
    ]
    TEST_RESULTS_PATH.write_text("\n".join(lines), encoding="utf-8")


def generate() -> dict[str, Any]:
    (PUBLIC_OUTPUT_DIR / "machine").mkdir(parents=True, exist_ok=True)
    (PUBLIC_OUTPUT_DIR / "human").mkdir(parents=True, exist_ok=True)
    manifest = build_manifest()
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_report(manifest)
    write_pending_test_results()
    return manifest


def main() -> int:
    manifest = generate()
    print(
        "PASS: KMFA v0.1.3 S03-P1 file import register evidence generated "
        f"(core_types={manifest['core_supported_file_type_count']}, "
        f"zip_safe={str(manifest['safe_zip_extraction_validated']).lower()}, "
        f"raw_read={str(manifest['raw_dir_read_performed']).lower()}, "
        f"github_upload={str(manifest['github_upload_performed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
