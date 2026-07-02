#!/usr/bin/env python3
"""Generate KMFA v0.1.3 S06-P1 zero-delta replay evidence.

This phase replays the existing integer-cent zero-delta validator against
public-safe synthetic fixtures and records the v0.1.3 gate. It does not read
or write the local raw data inbox and does not perform S06-P2, Stage 6 review,
or GitHub upload.
"""

from __future__ import annotations

import csv
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.check_v013_s05_stage_review import validate_v013_s05_stage_review
from KMFA.tools.v013_s05_p1_a0_file_registration import RAW_DIR
from KMFA.tools.zero_delta_validator import validate_fixture_file, write_mismatch_report


PUBLIC_OUTPUT_DIR = Path("KMFA/stage_artifacts/V013_S06_P1_ZERO_DELTA_REPLAY")
MACHINE_DIR = PUBLIC_OUTPUT_DIR / "machine"
HUMAN_DIR = PUBLIC_OUTPUT_DIR / "human"
MANIFEST_PATH = MACHINE_DIR / "zero_delta_replay_manifest.json"
PASS_FIXTURE_PATH = MACHINE_DIR / "zero_delta_pass_fixture.json"
PASS_RESULT_PATH = MACHINE_DIR / "zero_delta_pass_result.json"
MISMATCH_FIXTURE_PATH = MACHINE_DIR / "zero_delta_mismatch_fixture.json"
MISMATCH_RESULT_PATH = MACHINE_DIR / "zero_delta_mismatch_result.json"
MISMATCH_REPORT_PATH = MACHINE_DIR / "zero_delta_mismatch_report.csv"
REPORT_PATH = HUMAN_DIR / "zero_delta_replay_report.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
TASKPACK_FIXTURE_PATH = Path("KMFA/metadata/fixtures/a0_project_cost_fixture.json")
S05_STAGE_REVIEW_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V013_S05_STAGE_REVIEW/machine/stage5_review_manifest.json"
)
TASK_ID = "KMFA-V013-S06-P1-ZERO-DELTA-REPLAY-20260703"
SCHEMA_VERSION = "kmfa.v013_s06_p1_zero_delta_replay.v1"
PHASE_SCOPE = "v013_s06_p1_zero_delta_replay_only"
NEXT_REQUIRED_STEP = (
    "Proceed to v0.1.3 S06-P2 as a separate run. Do not run Stage 6 review or GitHub upload; "
    "GitHub main upload remains deferred until v0.1.3 Stages 1-10 are complete, the whole "
    "Stage 1-10 review passes, and findings are fixed."
)


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


def _json_dump(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _taskpack_pass_fixture() -> dict[str, Any]:
    fixture = _read_json(TASKPACK_FIXTURE_PATH)
    return {
        "schema_version": "kmfa.v013_s06_p1.zero_delta_fixture.v1",
        "fixture_id": "KMFA-V013-S06P1-PUBLIC-SAFE-PASS-FIXTURE",
        "source_fixture_ref": TASKPACK_FIXTURE_PATH.as_posix(),
        "public_safe_fixture_only": True,
        "raw_business_data_used": False,
        "key_fields": fixture["key_fields"],
        "amount_fields": fixture["amount_fields"],
        "authoritative_records": fixture["authoritative_records"],
        "system_records": fixture["system_records"],
    }


def _mismatch_fixture() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v013_s06_p1.zero_delta_fixture.v1",
        "fixture_id": "KMFA-V013-S06P1-ONE-CENT-MISMATCH-FIXTURE",
        "public_safe_fixture_only": True,
        "raw_business_data_used": False,
        "key_fields": ["record_id"],
        "amount_fields": ["contract_amount_cents"],
        "authoritative_records": [
            {
                "record_id": "V013-SYN-ZERO-DELTA-001",
                "source": "A0_Q5_PUBLIC_SAFE_AUTHORITY_BASELINE_SYNTHETIC",
                "contract_amount_cents": 10000,
            }
        ],
        "system_records": [
            {
                "record_id": "V013-SYN-ZERO-DELTA-001",
                "source": "SYSTEM_RECOMPUTE_PUBLIC_SAFE_SYNTHETIC",
                "contract_amount_cents": 9999,
            }
        ],
    }


def _write_result_and_report() -> tuple[dict[str, Any], dict[str, Any]]:
    _json_dump(PASS_FIXTURE_PATH, _taskpack_pass_fixture())
    _json_dump(MISMATCH_FIXTURE_PATH, _mismatch_fixture())

    pass_result = validate_fixture_file(PASS_FIXTURE_PATH)
    mismatch_result = validate_fixture_file(MISMATCH_FIXTURE_PATH)
    _json_dump(PASS_RESULT_PATH, pass_result)
    _json_dump(MISMATCH_RESULT_PATH, mismatch_result)
    write_mismatch_report(mismatch_result["mismatches"], MISMATCH_REPORT_PATH)
    return pass_result, mismatch_result


def _mismatch_report_columns() -> list[str]:
    with MISMATCH_REPORT_PATH.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or [])


def build_manifest() -> dict[str, Any]:
    s05 = validate_v013_s05_stage_review()
    pass_result, mismatch_result = _write_result_and_report()
    pass_fixture = _read_json(PASS_FIXTURE_PATH)
    mismatch_fixture = _read_json(MISMATCH_FIXTURE_PATH)
    comparison_count = len(pass_fixture["authoritative_records"]) * len(pass_fixture["amount_fields"])
    mismatch = mismatch_result["mismatches"][0]
    required_columns = [
        "record_id",
        "source",
        "field",
        "authoritative_value_cents",
        "system_value_cents",
        "difference_cents",
    ]

    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": "KMFA",
        "version": "0.1.3",
        "stage_id": "S06",
        "stage_name": "v0.1.3 zero-delta validation and difference handling",
        "phase_id": "S06-P1",
        "phase_name": "zero-delta validator replay",
        "phase_scope": PHASE_SCOPE,
        "task_id": TASK_ID,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "reviewed_head": git_output(["rev-parse", "HEAD"]),
        "worktree": git_output(["rev-parse", "--show-toplevel"]),
        "branch": git_output(["branch", "--show-current"]),
        "remote": git_output(["remote", "get-url", "origin"]),
        "status": "completed_validated_local_only_upload_deferred_zero_delta_replay",
        "completed_task_ids": ["S6PAT01", "S6PAT02", "S6PAT03"],
        "acceptance_ids": ["ACC-V013-S06-P1-ZERO-DELTA-REPLAY"],
        "s05_stage_review_dependency_validated": True,
        "s05_stage_review_manifest_ref": S05_STAGE_REVIEW_MANIFEST_PATH.as_posix(),
        "s05_dependency_summary": {
            "stage_id": s05["stage_id"],
            "phase_count": s05["phase_count"],
            "open_review_finding_count": s05["open_review_finding_count"],
            "q5_locked_field_count": s05["q5_locked_field_count"],
            "excluded_field_count": s05["excluded_field_count"],
            "github_upload_deferred_until_stage10_batch": s05[
                "github_upload_deferred_until_stage10_batch"
            ],
            "github_upload_performed": s05["github_upload_performed"],
        },
        "taskpack_zero_delta_plan_ref": "KMFA/taskpack/v1_2/08_KMFA_零差异验证与测试计划_v1_1.md",
        "taskpack_roadmap_ref": "KMFA/taskpack/v1_2/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_2.md",
        "source_validator_ref": "KMFA/tools/zero_delta_validator.py",
        "source_unit_test_ref": "KMFA/tests/test_zero_delta_validator.py",
        "pass_fixture_ref": PASS_FIXTURE_PATH.as_posix(),
        "pass_result_ref": PASS_RESULT_PATH.as_posix(),
        "mismatch_fixture_ref": MISMATCH_FIXTURE_PATH.as_posix(),
        "mismatch_result_ref": MISMATCH_RESULT_PATH.as_posix(),
        "mismatch_report_ref": MISMATCH_REPORT_PATH.as_posix(),
        "taskpack_fixture_ref": TASKPACK_FIXTURE_PATH.as_posix(),
        "pass_fixture_record_count": len(pass_fixture["authoritative_records"]),
        "pass_fixture_amount_field_count": len(pass_fixture["amount_fields"]),
        "pass_fixture_field_comparison_count": comparison_count,
        "zero_delta_passed_for_public_safe_fixture": pass_result["zero_delta_passed"],
        "pass_fixture_mismatch_count": pass_result["mismatch_count"],
        "one_cent_mismatch_detected": mismatch_result["zero_delta_passed"] is False
        and mismatch_result["mismatch_count"] == 1
        and mismatch["difference_cents"] == 1,
        "minimum_fail_difference_cents": mismatch_result["minimum_fail_difference_cents"],
        "mismatch_fixture_mismatch_count": mismatch_result["mismatch_count"],
        "mismatch_report_generated": MISMATCH_REPORT_PATH.exists(),
        "mismatch_report_required_columns": required_columns,
        "mismatch_report_columns": _mismatch_report_columns(),
        "mismatch_report_contains_required_columns": all(column in _mismatch_report_columns() for column in required_columns),
        "mismatch_report_public_safe": True,
        "integer_cent_comparison_only": True,
        "float_money_allowed": False,
        "raw_business_data_used": False,
        "raw_dir_read_performed": False,
        "raw_dir_mutation_performed": False,
        "metadata_quality_written": False,
        "difference_queue_created": False,
        "stage6_review_performed": False,
        "github_upload_performed": False,
        "github_upload_deferred_until_stage10_batch": True,
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
            "raw_business_values_committed": False,
            "sheet_names_committed": False,
            "zip_member_names_committed": False,
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
            "github_commit_allowed": False,
            "private_runtime_output_dir": "KMFA/.codex_private_runtime/",
        },
        "validators": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v013_s06_p1_zero_delta_replay.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s06_p1_zero_delta_replay.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v013_s06_p1_zero_delta_replay -q",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s05_stage_review.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_zero_delta_validator -q",
        ],
        "evidence_refs": [
            MANIFEST_PATH.as_posix(),
            REPORT_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            PASS_FIXTURE_PATH.as_posix(),
            PASS_RESULT_PATH.as_posix(),
            MISMATCH_FIXTURE_PATH.as_posix(),
            MISMATCH_RESULT_PATH.as_posix(),
            MISMATCH_REPORT_PATH.as_posix(),
            "KMFA/tools/v013_s06_p1_zero_delta_replay.py",
            "KMFA/tools/check_v013_s06_p1_zero_delta_replay.py",
            "KMFA/tests/test_v013_s06_p1_zero_delta_replay.py",
        ],
        "next_required_step": NEXT_REQUIRED_STEP,
    }


def write_report(manifest: dict[str, Any]) -> None:
    lines = [
        "# KMFA v0.1.3 S06-P1 Zero-Delta Replay",
        "",
        f"- task_id: `{manifest['task_id']}`",
        f"- status: `{manifest['status']}`",
        "- scope: `S06-P1 only`",
        "- s05_stage_review_dependency_validated: `true`",
        f"- pass_fixture_record_count: `{manifest['pass_fixture_record_count']}`",
        f"- pass_fixture_field_comparison_count: `{manifest['pass_fixture_field_comparison_count']}`",
        f"- zero_delta_passed_for_public_safe_fixture: `{str(manifest['zero_delta_passed_for_public_safe_fixture']).lower()}`",
        f"- pass_fixture_mismatch_count: `{manifest['pass_fixture_mismatch_count']}`",
        f"- minimum_fail_difference_cents: `{manifest['minimum_fail_difference_cents']}`",
        f"- one_cent_mismatch_detected: `{str(manifest['one_cent_mismatch_detected']).lower()}`",
        f"- mismatch_report_generated: `{str(manifest['mismatch_report_generated']).lower()}`",
        "- raw_business_data_used: `false`",
        "- raw_dir_read_performed: `false`",
        "- raw_dir_mutation_performed: `false`",
        "- metadata_quality_written: `false`",
        "- difference_queue_created: `false`",
        "- stage6_review_performed: `false`",
        "- github_upload_performed: `false`",
        "- github_upload_deferred_until_stage10_batch: `true`",
        "- formal_report_allowed: `false`",
        "- business_execution_allowed: `false`",
        "",
        "## Task Mapping",
        "",
        "- `S6PAT01`: existing `zero_delta_validator` replayed against a public-safe integer-cent fixture.",
        "- `S6PAT02`: one-cent mismatch fixture failed with `difference_cents=1`.",
        "- `S6PAT03`: mismatch report includes source, field, authoritative value, system value, and difference.",
        "",
        "## Evidence",
        "",
        f"- manifest: `{MANIFEST_PATH.as_posix()}`",
        f"- pass fixture: `{PASS_FIXTURE_PATH.as_posix()}`",
        f"- pass result: `{PASS_RESULT_PATH.as_posix()}`",
        f"- mismatch fixture: `{MISMATCH_FIXTURE_PATH.as_posix()}`",
        f"- mismatch result: `{MISMATCH_RESULT_PATH.as_posix()}`",
        f"- mismatch report: `{MISMATCH_REPORT_PATH.as_posix()}`",
        "",
        "## Boundary",
        "",
        "- This phase did not read, list, modify, delete, move, rename, overwrite, or write generated files inside the raw data inbox.",
        "- Public evidence uses synthetic/public-safe fixture records only.",
        "- This phase does not write runtime `metadata/quality` records; that belongs to S06-P3.",
        "- This phase does not create a cross-source difference queue; that belongs to S06-P2.",
        "- GitHub upload remains deferred until the Stage 1-10 batch gate.",
        "",
        "## Next",
        "",
        manifest["next_required_step"],
        "",
    ]
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_pending_test_results(manifest: dict[str, Any]) -> None:
    lines = [
        "# KMFA v0.1.3 S06-P1 Zero-Delta Replay Test Results",
        "",
        f"- task_id: `{manifest['task_id']}`",
        "- status: `generated_pending_final_validation_capture`",
        "- github_upload_performed: `false`",
        "- raw_dir_read_performed: `false`",
        "- raw_dir_mutation_performed: `false`",
        "",
        "Final command results are captured after the validator and governance checks complete in this run.",
        "",
    ]
    TEST_RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    TEST_RESULTS_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    manifest = build_manifest()
    _json_dump(MANIFEST_PATH, manifest)
    write_report(manifest)
    write_pending_test_results(manifest)
    print(
        "PASS: KMFA v0.1.3 S06-P1 zero-delta replay evidence generated "
        f"(comparisons={manifest['pass_fixture_field_comparison_count']}, "
        f"pass_mismatches={manifest['pass_fixture_mismatch_count']}, "
        f"one_cent_detected={str(manifest['one_cent_mismatch_detected']).lower()}, "
        f"github_upload={str(manifest['github_upload_performed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
