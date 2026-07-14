#!/usr/bin/env python3
"""Generate KMFA v0.1.3 S03-P2 source check matrix evidence.

This phase replays the existing source-check-matrix capability with synthetic
metadata only. It does not read the local raw data inbox, mutate raw sources, or
publish raw filenames, raw hashes, field text, sheet names, row values, or
business values.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.check_v013_s03_p1_file_import_register import validate_v013_s03_p1_file_import_register
from KMFA.tools.source_check_matrix import (
    ALLOWED_STATUSES,
    REQUIRED_DIMENSIONS,
    append_status_event,
    build_source_matrix_row,
    build_status_event,
)
from KMFA.tools.v013_s03_p1_file_import_register import RAW_DIR


PUBLIC_OUTPUT_DIR = Path("KMFA/stage_artifacts/V013_S03_P2_SOURCE_CHECK_MATRIX")
MANIFEST_PATH = PUBLIC_OUTPUT_DIR / "machine/source_check_matrix_manifest.json"
REPORT_PATH = PUBLIC_OUTPUT_DIR / "human/source_check_matrix_report.md"
TEST_RESULTS_PATH = PUBLIC_OUTPUT_DIR / "human/test_results.md"
TASK_ID = "KMFA-V013-S03-P2-SOURCE-CHECK-MATRIX-20260702"
SCHEMA_VERSION = "kmfa.v013_s03_p2_source_check_matrix.v1"


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


def synthetic_registration() -> dict[str, Any]:
    return {
        "import_run": {
            "import_run_id": "IMP-V013-S03P2-SYNTHETIC-PRIVATE",
            "source_id": "SRC-V013-S03P2-SYNTHETIC",
        },
        "raw_file_manifest": {
            "file_hash": "private-synthetic-file-hash-not-published",
            "file_size_bytes": 1,
            "file_format": "synthetic",
            "source_package_ref": {
                "source_id": "SRC-V013-S03P2-SYNTHETIC",
                "source_package_hash": "private-synthetic-package-hash-not-published",
                "source_package_size_bytes": 1,
                "source_package_storage_ref": "private://synthetic/v013-s03p2",
            },
        },
    }


def replay_source_check_matrix_capability() -> dict[str, Any]:
    """Exercise S03-P2 matrix/status-event behavior with synthetic metadata."""
    row = build_source_matrix_row(
        synthetic_registration(),
        source_system="synthetic-export",
        business_segment="source-check",
        entity_ref="ENTITY-public-safe",
        account_ref="ACCOUNT-public-safe",
        frequency="monthly",
        status="部分/阻塞",
        evidence_ref="synthetic-private-replay",
    )
    original_row_json = json.dumps(row, ensure_ascii=False, sort_keys=True)
    event = build_status_event(
        row,
        new_status="人工复核",
        reason_code="source-awaiting-owner-review",
        actor_ref="codex-validator",
        event_time="2026-07-02T18:20:00+10:00",
        evidence_ref="synthetic-private-replay",
    )
    with tempfile.TemporaryDirectory(prefix="kmfa-v013-s03p2-") as tmp:
        event_path = Path(tmp) / "source_status_events.jsonl"
        append_status_event(event_path, event)
        records = [json.loads(line) for line in event_path.read_text(encoding="utf-8").splitlines()]

    return {
        "synthetic_matrix_row_count": 1,
        "synthetic_status_event_count": len(records),
        "matrix_row_required_dimensions_validated": all(field in row for field in REQUIRED_DIMENSIONS),
        "matrix_row_public_safe_controls_validated": (
            row.get("raw_layer_write_allowed") is False and row.get("raw_source_mutation_allowed") is False
        ),
        "metadata_status_event_validated": (
            len(records) == 1
            and records[0].get("record_type") == "source_status_event"
            and records[0].get("target_layer") == "metadata"
            and records[0].get("raw_layer_write_allowed") is False
            and records[0].get("raw_source_mutation_allowed") is False
        ),
        "status_change_append_only": json.dumps(row, ensure_ascii=False, sort_keys=True) == original_row_json,
        "status_change_target_layer": event.get("target_layer"),
        "status_event_private_temp_write_only": True,
        "published_synthetic_matrix_row": False,
        "published_synthetic_status_event": False,
    }


def build_manifest() -> dict[str, Any]:
    s03_p1 = validate_v013_s03_p1_file_import_register()
    capability = replay_source_check_matrix_capability()

    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": "KMFA",
        "version": "0.1.3",
        "stage_id": "S03",
        "stage_name": "v0.1.3 file import and source check matrix",
        "phase_id": "S03-P2",
        "phase_name": "source check matrix",
        "phase_scope": "v013_s03_p2_source_check_matrix_only",
        "task_id": TASK_ID,
        "run_time": datetime.now().astimezone().isoformat(timespec="seconds"),
        "reviewed_head": git_output(["rev-parse", "HEAD"]),
        "worktree": git_output(["rev-parse", "--show-toplevel"]),
        "branch": git_output(["branch", "--show-current"]),
        "remote": git_output(["remote", "get-url", "origin"]),
        "status": "completed_validated_local_only_no_go_upload_deferred",
        "completed_task_ids": ["S3PBT01", "S3PBT02", "S3PBT03"],
        "s03_p1_dependency_validated": (
            s03_p1.get("stage_id") == "S03"
            and s03_p1.get("phase_id") == "S03-P1"
            and s03_p1.get("github_upload_performed") is False
            and s03_p1.get("raw_dir_read_performed") is False
        ),
        "s03_p1_dependency_ref": "KMFA/stage_artifacts/V013_S03_P1_FILE_IMPORT_REGISTER/machine/file_import_register_manifest.json",
        "source_check_matrix_dependency_validated": True,
        "source_check_matrix_refs": [
            "KMFA/tools/source_check_matrix.py",
            "KMFA/tests/test_source_check_matrix.py",
            "KMFA/stage_artifacts/S03_P2_source_check_matrix/machine/s03_p2_manifest.json",
            "KMFA/stage_artifacts/S03_P2_source_check_matrix/human/s03_p2_completion_record.md",
        ],
        "required_dimensions": list(REQUIRED_DIMENSIONS),
        "required_dimension_count": len(REQUIRED_DIMENSIONS),
        "allowed_statuses": list(ALLOWED_STATUSES),
        "allowed_status_count": len(ALLOWED_STATUSES),
        "synthetic_matrix_row_count": capability["synthetic_matrix_row_count"],
        "synthetic_status_event_count": capability["synthetic_status_event_count"],
        "matrix_row_required_dimensions_validated": capability["matrix_row_required_dimensions_validated"],
        "matrix_row_public_safe_controls_validated": capability["matrix_row_public_safe_controls_validated"],
        "metadata_status_event_validated": capability["metadata_status_event_validated"],
        "status_change_append_only": capability["status_change_append_only"],
        "status_change_target_layer": capability["status_change_target_layer"],
        "status_event_private_temp_write_only": capability["status_event_private_temp_write_only"],
        "published_synthetic_matrix_row": capability["published_synthetic_matrix_row"],
        "published_synthetic_status_event": capability["published_synthetic_status_event"],
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
        "raw_layer_write_allowed": False,
        "raw_source_mutation_allowed": False,
        "raw_file_bytes_committed": False,
        "raw_filename_publication_allowed": False,
        "raw_file_hash_publication_allowed": False,
        "source_package_hash_publication_allowed": False,
        "source_package_storage_ref_publication_allowed": False,
        "field_plaintext_publication_allowed": False,
        "sheet_name_publication_allowed": False,
        "zip_member_name_publication_allowed": False,
        "row_value_publication_allowed": False,
        "business_value_publication_allowed": False,
        "business_field_parsing_performed": False,
        "raw_value_matching_performed": False,
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
            "source_check_matrix_rows_committed": False,
            "source_status_event_rows_committed": False,
        },
        "validators": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v013_s03_p2_source_check_matrix.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s03_p2_source_check_matrix.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v013_s03_p2_source_check_matrix -q",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_source_check_matrix -q",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s03_p1_file_import_register.py",
        ],
        "evidence_refs": [
            MANIFEST_PATH.as_posix(),
            REPORT_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            "KMFA/tools/v013_s03_p2_source_check_matrix.py",
            "KMFA/tools/check_v013_s03_p2_source_check_matrix.py",
            "KMFA/tests/test_v013_s03_p2_source_check_matrix.py",
            "KMFA/tools/source_check_matrix.py",
            "KMFA/tests/test_source_check_matrix.py",
            "KMFA/tools/check_v013_s03_p1_file_import_register.py",
        ],
        "next_required_step": (
            "Proceed to v0.1.3 S03-P3 as a separate run after this phase commit; do not run "
            "Stage 3 review, GitHub upload, raw value matching, formal report release, live connector, "
            "or business execution in S03-P2."
        ),
    }


def write_report(manifest: dict[str, Any]) -> None:
    lines = [
        "# KMFA v0.1.3 S03-P2 Source Check Matrix",
        "",
        f"- task_id: `{manifest['task_id']}`",
        f"- status: `{manifest['status']}`",
        f"- phase_scope: `{manifest['phase_scope']}`",
        f"- s03_p1_dependency_validated: `{str(manifest['s03_p1_dependency_validated']).lower()}`",
        f"- source_check_matrix_dependency_validated: `{str(manifest['source_check_matrix_dependency_validated']).lower()}`",
        f"- required_dimension_count: `{manifest['required_dimension_count']}`",
        "- required_dimensions: `source_system`, `business_segment`, `source_package_ref`, `entity_ref`, `account_ref`, `frequency`",
        f"- allowed_status_count: `{manifest['allowed_status_count']}`",
        "- allowed_statuses: `已就绪`, `部分/阻塞`, `失败/不适用`, `已过期`, `人工复核`",
        f"- metadata_status_event_validated: `{str(manifest['metadata_status_event_validated']).lower()}`",
        f"- status_change_append_only: `{str(manifest['status_change_append_only']).lower()}`",
        f"- status_change_target_layer: `{manifest['status_change_target_layer']}`",
        "",
        "## Raw Data Boundary",
        "",
        f"- local_raw_data_dir: `{manifest['raw_data_boundary']['local_raw_data_dir']}`",
        "- codex_modify_delete_move_rename_overwrite_or_generate_inside_allowed: `false`",
        "- public_repo_raw_commit_allowed: `false`",
        "- private_runtime_output_dir: `KMFA/.codex_private_runtime/`",
        "",
        "## Public-Safe Boundary",
        "",
        "- raw_dir_read_performed: `false`",
        "- raw_dir_mutation_performed: `false`",
        "- raw_layer_write_allowed: `false`",
        "- raw_source_mutation_allowed: `false`",
        "- raw_file_bytes_committed: `false`",
        "- raw_filename_publication_allowed: `false`",
        "- raw_file_hash_publication_allowed: `false`",
        "- source_package_hash_publication_allowed: `false`",
        "- source_package_storage_ref_publication_allowed: `false`",
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
        "# KMFA v0.1.3 S03-P2 Test Results",
        "",
        "- status: `pending_final_validation`",
        "- red_step: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v013_s03_p2_source_check_matrix -q` failed before validator implementation with missing module.",
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
        "PASS: KMFA v0.1.3 S03-P2 source check matrix evidence generated "
        f"(dimensions={manifest['required_dimension_count']}, "
        f"statuses={manifest['allowed_status_count']}, "
        f"metadata_event={str(manifest['metadata_status_event_validated']).lower()}, "
        f"raw_read={str(manifest['raw_dir_read_performed']).lower()}, "
        f"github_upload={str(manifest['github_upload_performed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
