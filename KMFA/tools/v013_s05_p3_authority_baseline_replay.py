#!/usr/bin/env python3
"""Generate KMFA v0.1.3 S05-P3 authority baseline replay evidence.

This phase replays the existing public-safe S05-P3 A0 authority baseline lock.
It validates the v0.1.3 S05-P2 dependency and the legacy authority baseline
artifacts, then emits a public-safe aggregate evidence package. It does not
read the local raw data inbox and does not publish raw values, normalized
values, raw filenames, sheet names, ZIP member names, row values, business
values, or field/header plaintext.
"""

from __future__ import annotations

import json
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.a0_authority_baseline_lock import (
    DEFAULT_OUTPUT_MANIFEST as LEGACY_AUTHORITY_MANIFEST,
    DEFAULT_OUTPUT_RECORDS as LEGACY_AUTHORITY_RECORDS,
    validate_authority_baseline_lock,
)
from KMFA.tools.check_v013_s05_p2_field_candidate_replay import validate_v013_s05_p2_field_candidate_replay
from KMFA.tools.v013_s05_p1_a0_file_registration import RAW_DIR
from KMFA.tools.v013_s05_p2_field_candidate_replay import MANIFEST_PATH as S05_P2_MANIFEST_PATH


PUBLIC_OUTPUT_DIR = Path("KMFA/stage_artifacts/V013_S05_P3_AUTHORITY_BASELINE_REPLAY")
MANIFEST_PATH = PUBLIC_OUTPUT_DIR / "machine/authority_baseline_replay_manifest.json"
REPORT_PATH = PUBLIC_OUTPUT_DIR / "human/authority_baseline_replay_report.md"
TEST_RESULTS_PATH = PUBLIC_OUTPUT_DIR / "human/test_results.md"
TASK_ID = "KMFA-V013-S05-P3-AUTHORITY-BASELINE-REPLAY-20260702"
SCHEMA_VERSION = "kmfa.v013_s05_p3_authority_baseline_replay.v1"
EXPECTED_BASELINE_VERSION = "KMFA-A0-Q5-20260630-S05P3-PUBLIC-SAFE-HASH-LOCK"
EXPECTED_BASELINE_CONTENT_HASH = "sha256:dbb55ffb4e3608e49dbcf91e97fc0f19395a8269ff7c8f4d5c3f8ca398c03670"


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


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path} contains non-object JSONL row")
        records.append(value)
    return records


def validate_legacy_s05_p3() -> dict[str, Any]:
    manifest = read_json(LEGACY_AUTHORITY_MANIFEST)
    records = read_jsonl(LEGACY_AUTHORITY_RECORDS)
    validate_authority_baseline_lock(manifest, records)

    summary = manifest["lock_summary"]
    status_counts = Counter(str(record.get("lock_status")) for record in records)
    locked_records = [record for record in records if record.get("lock_status") == "q5_locked_public_safe_hash_baseline"]
    source_format_counts = Counter(
        str((record.get("source_lock") or {}).get("source_file_format", "not_applicable"))
        for record in locked_records
    )
    public_safety = manifest.get("public_repo_safety") or {}

    return {
        "baseline_version": manifest["baseline_version"],
        "baseline_content_hash": manifest["baseline_content_hash"],
        "locked_at": manifest["locked_at"],
        "locked_by_role": manifest["locked_by_role"],
        "locked_by_ref": manifest["locked_by_ref"],
        "authority_records": summary["authority_records"],
        "total_fixture_fields": summary["total_fixture_fields"],
        "q5_locked_field_count": summary["q5_locked_field_count"],
        "excluded_field_count": summary["excluded_field_count"],
        "q4_human_confirmed_count": summary["q4_human_confirmed_count"],
        "q5_calculation_baseline_allowed_count": summary["q5_calculation_baseline_allowed_count"],
        "formal_report_allowed": summary["formal_report_allowed"],
        "stage5_review_completed": summary["stage5_review_completed"],
        "github_upload_allowed": summary["github_upload_allowed"],
        "lock_status_counts": dict(sorted(status_counts.items())),
        "locked_source_format_counts": dict(sorted(source_format_counts.items())),
        "raw_business_values_committed": public_safety.get("raw_business_values_committed"),
        "normalized_business_values_committed": public_safety.get("normalized_business_values_committed"),
        "raw_file_bytes_committed": public_safety.get("raw_file_bytes_committed"),
        "private_csv_committed": public_safety.get("private_csv_committed"),
    }


def build_manifest() -> dict[str, Any]:
    s05_p2 = validate_v013_s05_p2_field_candidate_replay()
    legacy = validate_legacy_s05_p3()
    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": "KMFA",
        "version": "0.1.3",
        "stage_id": "S05",
        "stage_name": "v0.1.3 A0 authority project cost golden baseline",
        "phase_id": "S05-P3",
        "phase_name": "authority baseline lock replay",
        "phase_scope": "v013_s05_p3_authority_baseline_replay_only",
        "task_id": TASK_ID,
        "run_time": datetime.now().astimezone().isoformat(timespec="seconds"),
        "reviewed_head": git_output(["rev-parse", "HEAD"]),
        "worktree": git_output(["rev-parse", "--show-toplevel"]),
        "branch": git_output(["branch", "--show-current"]),
        "remote": git_output(["remote", "get-url", "origin"]),
        "status": "completed_validated_local_only_no_go_upload_deferred_authority_baseline_replayed",
        "completed_task_ids": ["S5PCT01", "S5PCT02", "S5PCT03"],
        "s05_p2_dependency_validated": (
            s05_p2.get("phase_id") == "S05-P2"
            and s05_p2.get("github_upload_performed") is False
            and s05_p2.get("github_upload_deferred_until_stage10_batch") is True
        ),
        "s05_p2_dependency_ref": str(S05_P2_MANIFEST_PATH),
        "legacy_s05_p3_dependency_validated": True,
        "authority_baseline_summary": {
            "baseline_version": legacy["baseline_version"],
            "baseline_content_hash": legacy["baseline_content_hash"],
            "locked_at": legacy["locked_at"],
            "locked_by_role": legacy["locked_by_role"],
            "locked_by_ref": legacy["locked_by_ref"],
            "authority_records": legacy["authority_records"],
            "total_fixture_fields": legacy["total_fixture_fields"],
            "q5_locked_field_count": legacy["q5_locked_field_count"],
            "excluded_field_count": legacy["excluded_field_count"],
            "q4_human_confirmed_count": legacy["q4_human_confirmed_count"],
            "q5_calculation_baseline_allowed_count": legacy["q5_calculation_baseline_allowed_count"],
            "formal_report_allowed": legacy["formal_report_allowed"],
            "stage5_review_completed": legacy["stage5_review_completed"],
            "github_upload_allowed": legacy["github_upload_allowed"],
            "lock_status_counts": legacy["lock_status_counts"],
            "locked_source_format_counts": legacy["locked_source_format_counts"],
            "raw_business_values_committed": legacy["raw_business_values_committed"],
            "normalized_business_values_committed": legacy["normalized_business_values_committed"],
            "raw_file_bytes_committed": legacy["raw_file_bytes_committed"],
            "private_csv_committed": legacy["private_csv_committed"],
        },
        "baseline_lock": {
            "authority_baseline_lock_performed": True,
            "public_safe_hash_lock_only": True,
            "raw_or_normalized_value_publication_performed": False,
            "raw_file_or_business_document_publication_performed": False,
            "field_or_header_plaintext_publication_performed": False,
            "formal_report_release_performed": False,
        },
        "raw_data_boundary": {
            "local_raw_data_dir": str(RAW_DIR),
            "local_raw_data_dir_role": "user_finance_raw_business_data_inbox",
            "codex_read_allowed_only_when_phase_requires": True,
            "codex_read_required_by_this_phase": False,
            "codex_read_performed_by_this_phase": False,
            "codex_modify_allowed": False,
            "codex_delete_allowed": False,
            "codex_move_allowed": False,
            "codex_rename_allowed": False,
            "codex_overwrite_allowed": False,
            "codex_generate_inside_allowed": False,
            "codex_create_extra_files_inside_allowed": False,
            "github_commit_allowed": False,
            "private_runtime_output_dir": "KMFA/.codex_private_runtime/",
            "extra_work_dir_requirement": "must_be_project_controlled_and_gitignored",
        },
        "raw_dir_read_required": False,
        "raw_dir_read_performed": False,
        "raw_dir_mutation_performed": False,
        "raw_layer_write_allowed": False,
        "raw_source_mutation_allowed": False,
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
        "s05_p3_performed": True,
        "stage5_review_performed": False,
        "github_upload_performed": False,
        "github_upload_deferred_until_stage10_batch": True,
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
            "normalized_business_values_committed": False,
        },
        "validators": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v013_s05_p3_authority_baseline_replay.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s05_p3_authority_baseline_replay.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v013_s05_p3_authority_baseline_replay -q",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s05_p2_field_candidate_replay.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_a0_authority_baseline_lock.py",
        ],
        "evidence_refs": [
            "KMFA/stage_artifacts/V013_S05_P3_AUTHORITY_BASELINE_REPLAY/human/authority_baseline_replay_report.md",
            "KMFA/stage_artifacts/V013_S05_P3_AUTHORITY_BASELINE_REPLAY/human/test_results.md",
            "KMFA/stage_artifacts/V013_S05_P3_AUTHORITY_BASELINE_REPLAY/machine/authority_baseline_replay_manifest.json",
        ],
        "legacy_s05_p3_refs": [
            "KMFA/tools/a0_authority_baseline_lock.py",
            "KMFA/tools/check_a0_authority_baseline_lock.py",
            "KMFA/metadata/baseline/a0_authority_baseline_manifest.json",
            "KMFA/metadata/baseline/a0_authority_baseline_records.jsonl",
            "KMFA/stage_artifacts/S05_P3_authority_baseline_lock/human/test_results.md",
            "KMFA/stage_artifacts/S05_P3_authority_baseline_lock/machine/s05_p3_manifest.json",
        ],
        "non_scope": [
            "Stage 5 review",
            "GitHub upload",
            "raw data inspection",
            "raw directory mutation",
            "raw filename or raw hash publication",
            "field/header plaintext from raw sources",
            "sheet or ZIP member name publication",
            "row value publication",
            "business value publication",
            "raw value matching",
            "lineage full check completion",
            "formal report release",
            "live connector",
            "business execution",
        ],
        "next_required_step": "Stage 5 whole review in a separate run. Do not perform GitHub upload in S05-P3; GitHub main upload remains deferred until Stage 1-10 are complete, whole review passes, and findings are fixed.",
    }


def write_report(manifest: dict[str, Any]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    summary = manifest["authority_baseline_summary"]
    lines = [
        "# KMFA v0.1.3 S05-P3 Authority Baseline Replay",
        "",
        "- status: `completed_validated_local_only_no_go_upload_deferred_authority_baseline_replayed`",
        "- phase_scope: `v013_s05_p3_authority_baseline_replay_only`",
        f"- baseline_version: `{summary['baseline_version']}`",
        f"- baseline_content_hash: `{summary['baseline_content_hash']}`",
        f"- authority_records: `{summary['authority_records']}`",
        f"- total_fixture_fields: `{summary['total_fixture_fields']}`",
        f"- q5_locked_field_count: `{summary['q5_locked_field_count']}`",
        f"- excluded_field_count: `{summary['excluded_field_count']}`",
        f"- q4_human_confirmed_count: `{summary['q4_human_confirmed_count']}`",
        f"- q5_calculation_baseline_allowed_count: `{summary['q5_calculation_baseline_allowed_count']}`",
        f"- formal_report_allowed: `{str(summary['formal_report_allowed']).lower()}`",
        f"- stage5_review_completed: `{str(summary['stage5_review_completed']).lower()}`",
        f"- github_upload_allowed: `{str(summary['github_upload_allowed']).lower()}`",
        "- s05_p2_dependency_validated: `true`",
        "- legacy_s05_p3_dependency_validated: `true`",
        "- raw_dir_read_required: `false`",
        "- raw_dir_read_performed: `false`",
        "- raw_dir_mutation_performed: `false`",
        f"- local_raw_data_dir: `{manifest['raw_data_boundary']['local_raw_data_dir']}`",
        "- raw_filename_publication_allowed: `false`",
        "- field_plaintext_publication_allowed: `false`",
        "- sheet_name_publication_allowed: `false`",
        "- zip_member_name_publication_allowed: `false`",
        "- row_value_publication_allowed: `false`",
        "- business_value_publication_allowed: `false`",
        "- s05_p3_performed: `true`",
        "- stage5_review_performed: `false`",
        "- github_upload_performed: `false`",
        "- github_upload_deferred_until_stage10_batch: `true`",
        "- current_data_quality_grade: `Q2`",
        "- current_report_grade: `D`",
        "- release_permission: `blocked`",
        "",
        "## Boundary Note",
        "",
        "This replay uses only existing public-safe S05-P3 aggregate authority baseline metadata and validator results. It does not read the local raw inbox and does not publish raw values, normalized values, source filenames, sheet names, ZIP member names, row values, business values, or field/header plaintext.",
        "",
        "`/Users/linzezhang/Downloads/KMFA_MetaData` is the user finance raw business data inbox. Codex must not modify, delete, move, rename, overwrite, or write generated/extra files inside that directory. Private diagnostics or scratch outputs must use `KMFA/.codex_private_runtime/` or another project-controlled gitignored work directory.",
        "",
        "## Next",
        "",
        manifest["next_required_step"],
        "",
    ]
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_test_results_if_missing() -> None:
    TEST_RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    if TEST_RESULTS_PATH.exists():
        return
    TEST_RESULTS_PATH.write_text(
        "\n".join(
            [
                "# KMFA v0.1.3 S05-P3 Test Results",
                "",
                "- status: `pending_final_validation`",
                "",
                "Final validation results will be recorded before local commit.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def generate() -> dict[str, Any]:
    PUBLIC_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    manifest = build_manifest()
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_report(manifest)
    write_test_results_if_missing()
    return manifest


def main() -> int:
    manifest = generate()
    summary = manifest["authority_baseline_summary"]
    print(
        "PASS: KMFA v0.1.3 S05-P3 authority baseline replay evidence generated "
        f"(authority_records={summary['authority_records']}, "
        f"q5_locked={summary['q5_locked_field_count']}, "
        f"excluded={summary['excluded_field_count']}, "
        f"formal_report_allowed={str(summary['formal_report_allowed']).lower()}, "
        f"github_upload={str(manifest['github_upload_performed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
