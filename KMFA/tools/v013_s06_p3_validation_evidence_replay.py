#!/usr/bin/env python3
"""Generate KMFA v0.1.3 S06-P3 validation evidence replay outputs.

This phase consumes only the v0.1.3 S06-P1/S06-P2 public-safe synthetic
evidence and writes sanitized validation evidence to stage artifacts plus
metadata/quality. It does not read the raw data inbox, close differences, run
Stage 6 review, or upload to GitHub.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.check_v013_s06_p1_zero_delta_replay import validate_v013_s06_p1_zero_delta_replay
from KMFA.tools.check_v013_s06_p2_difference_queue_replay import validate_v013_s06_p2_difference_queue_replay
from KMFA.tools.v013_s05_p1_a0_file_registration import RAW_DIR
from KMFA.tools.validation_evidence_output import build_from_paths, write_validation_evidence_outputs


PUBLIC_OUTPUT_DIR = Path("KMFA/stage_artifacts/V013_S06_P3_VALIDATION_EVIDENCE_REPLAY")
MACHINE_DIR = PUBLIC_OUTPUT_DIR / "machine"
HUMAN_DIR = PUBLIC_OUTPUT_DIR / "human"
METADATA_QUALITY_DIR = Path("KMFA/metadata/quality")

MANIFEST_PATH = MACHINE_DIR / "validation_evidence_replay_manifest.json"
ZERO_DELTA_OUTPUT_PATH = MACHINE_DIR / "zero_delta_result.json"
MISMATCH_OUTPUT_PATH = MACHINE_DIR / "mismatch_report.csv"
PROJECT_STATUS_OUTPUT_PATH = MACHINE_DIR / "project_validation_status.jsonl"
REPORT_PATH = HUMAN_DIR / "validation_evidence_replay_report.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"

S06_P1_RESULT_PATH = Path(
    "KMFA/stage_artifacts/V013_S06_P1_ZERO_DELTA_REPLAY/machine/zero_delta_mismatch_result.json"
)
S06_P1_MISMATCH_REPORT_PATH = Path(
    "KMFA/stage_artifacts/V013_S06_P1_ZERO_DELTA_REPLAY/machine/zero_delta_mismatch_report.csv"
)
S06_P2_QUEUE_PATH = Path(
    "KMFA/stage_artifacts/V013_S06_P2_DIFFERENCE_QUEUE_REPLAY/machine/source_difference_queue.jsonl"
)
S06_P2_GATE_PATH = Path(
    "KMFA/stage_artifacts/V013_S06_P2_DIFFERENCE_QUEUE_REPLAY/machine/report_grade_gate.json"
)

TASK_ID = "KMFA-V013-S06-P3-VALIDATION-EVIDENCE-REPLAY-20260703"
SCHEMA_VERSION = "kmfa.v013_s06_p3_validation_evidence_replay.v1"
PHASE_SCOPE = "v013_s06_p3_validation_evidence_replay_only"
EVIDENCE_TIME = "2026-07-03T07:20:00+10:00"
NEXT_REQUIRED_STEP = (
    "Proceed to v0.1.3 Stage 6 whole review as a separate run only after this phase is committed. "
    "Do not run GitHub upload; GitHub main upload remains deferred until v0.1.3 Stages 1-10 are "
    "complete, the whole Stage 1-10 review passes, and findings are fixed."
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


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _patch_metadata_refs(evidence: dict[str, Any]) -> None:
    for record in evidence["metadata_zero_delta_records"]:
        record["result_ref"] = ZERO_DELTA_OUTPUT_PATH.as_posix()
        record["mismatch_report_ref"] = MISMATCH_OUTPUT_PATH.as_posix()


def build_and_write_evidence() -> dict[str, Any]:
    validate_v013_s06_p1_zero_delta_replay()
    validate_v013_s06_p2_difference_queue_replay()
    evidence = build_from_paths(
        zero_delta_result_path=S06_P1_RESULT_PATH,
        source_mismatch_report_path=S06_P1_MISMATCH_REPORT_PATH,
        difference_queue_path=S06_P2_QUEUE_PATH,
        report_gate_path=S06_P2_GATE_PATH,
        evidence_time=EVIDENCE_TIME,
    )
    _patch_metadata_refs(evidence)
    write_validation_evidence_outputs(
        evidence,
        output_dir=MACHINE_DIR,
        metadata_quality_dir=METADATA_QUALITY_DIR,
    )
    return evidence


def build_manifest(evidence: dict[str, Any]) -> dict[str, Any]:
    zero_delta_result = evidence["zero_delta_result"]
    project_statuses = evidence["project_validation_statuses"]
    metadata_zero_delta_records = evidence["metadata_zero_delta_records"]
    metadata_data_quality_records = evidence["metadata_data_quality_records"]
    metadata_source_difference_records = evidence["metadata_source_difference_records"]
    mismatch_rows = evidence["mismatch_rows"]
    blocked_statuses = [status for status in project_statuses if status["validation_status"] == "blocked"]

    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": "KMFA",
        "version": "0.1.3",
        "stage_id": "S06",
        "stage_name": "v0.1.3 zero-delta validation and difference handling",
        "phase_id": "S06-P3",
        "phase_name": "metadata/quality validation evidence output replay",
        "phase_scope": PHASE_SCOPE,
        "task_id": TASK_ID,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "evidence_time": EVIDENCE_TIME,
        "reviewed_head": git_output(["rev-parse", "HEAD"]),
        "worktree": git_output(["rev-parse", "--show-toplevel"]),
        "branch": git_output(["branch", "--show-current"]),
        "remote": git_output(["remote", "get-url", "origin"]),
        "status": "completed_validated_local_only_upload_deferred_validation_evidence_replay",
        "completed_task_ids": ["S6PCT01", "S6PCT02", "S6PCT03"],
        "acceptance_ids": ["ACC-V013-S06-P3-VALIDATION-EVIDENCE-REPLAY"],
        "s06_p1_dependency_validated": True,
        "s06_p2_dependency_validated": True,
        "s06_p1_result_ref": S06_P1_RESULT_PATH.as_posix(),
        "s06_p1_mismatch_report_ref": S06_P1_MISMATCH_REPORT_PATH.as_posix(),
        "s06_p2_queue_ref": S06_P2_QUEUE_PATH.as_posix(),
        "s06_p2_gate_ref": S06_P2_GATE_PATH.as_posix(),
        "taskpack_roadmap_ref": "KMFA/taskpack/v1_2/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_2.md",
        "taskpack_zero_delta_plan_ref": "KMFA/taskpack/v1_2/08_KMFA_零差异验证与测试计划_v1_1.md",
        "source_evidence_builder_ref": "KMFA/tools/validation_evidence_output.py",
        "legacy_validator_ref": "KMFA/tools/check_s06_p3_validation_evidence.py",
        "zero_delta_result_output_ref": ZERO_DELTA_OUTPUT_PATH.as_posix(),
        "mismatch_report_output_ref": MISMATCH_OUTPUT_PATH.as_posix(),
        "project_validation_status_output_ref": PROJECT_STATUS_OUTPUT_PATH.as_posix(),
        "metadata_zero_delta_results_ref": "KMFA/metadata/quality/zero_delta_results.jsonl",
        "metadata_data_quality_results_ref": "KMFA/metadata/quality/data_quality_results.jsonl",
        "metadata_source_difference_queue_ref": "KMFA/metadata/quality/source_difference_queue.jsonl",
        "metadata_mismatch_report_ref": "KMFA/metadata/quality/mismatch_report.csv",
        "zero_delta_result_id": zero_delta_result["result_id"],
        "zero_delta_passed": zero_delta_result["zero_delta_passed"],
        "mismatch_count": zero_delta_result["mismatch_count"],
        "project_status_count": len(project_statuses),
        "blocked_project_status_count": len(blocked_statuses),
        "metadata_zero_delta_records_written": len(metadata_zero_delta_records),
        "metadata_data_quality_records_written": len(metadata_data_quality_records),
        "metadata_source_difference_records_written": len(metadata_source_difference_records),
        "metadata_mismatch_rows_written": len(mismatch_rows),
        "metadata_quality_written": True,
        "zero_delta_result_output_written": True,
        "mismatch_report_output_written": True,
        "project_validation_status_output_written": True,
        "q5_allowed_count": sum(1 for status in project_statuses if status["q5_allowed"]),
        "report_grade_a_allowed_count": sum(1 for status in project_statuses if status["report_grade_a_allowed"]),
        "hard_blocks": sorted({block for status in project_statuses for block in status["hard_blocks"]}),
        "metadata_quality_target": "KMFA/metadata/quality",
        "sanitized_mismatch_columns": [
            "mismatch_id",
            "source_id",
            "file_hash",
            "field_path",
            "mapping_version",
            "formula_version",
            "status",
            "evidence_ref",
        ],
        "field_plaintext_committed": False,
        "raw_business_values_committed": False,
        "source_amount_literals_committed": False,
        "raw_business_data_used": False,
        "raw_dir_read_performed": False,
        "raw_dir_mutation_performed": False,
        "raw_value_matching_performed": False,
        "difference_closed": False,
        "auto_correction_allowed": False,
        "averaging_allowed": False,
        "rounding_mask_allowed": False,
        "auto_selection_allowed": False,
        "stage6_review_performed": False,
        "github_upload_performed": False,
        "github_upload_deferred_until_stage10_batch": True,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "business_execution_allowed": False,
        "current_data_quality_grade": "Q4",
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
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v013_s06_p3_validation_evidence_replay.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s06_p3_validation_evidence_replay.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v013_s06_p3_validation_evidence_replay -q",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s06_p1_zero_delta_replay.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s06_p2_difference_queue_replay.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s06_p3_validation_evidence.py",
        ],
        "evidence_refs": [
            MANIFEST_PATH.as_posix(),
            REPORT_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            ZERO_DELTA_OUTPUT_PATH.as_posix(),
            MISMATCH_OUTPUT_PATH.as_posix(),
            PROJECT_STATUS_OUTPUT_PATH.as_posix(),
            "KMFA/metadata/quality/zero_delta_results.jsonl",
            "KMFA/metadata/quality/data_quality_results.jsonl",
            "KMFA/metadata/quality/source_difference_queue.jsonl",
            "KMFA/metadata/quality/mismatch_report.csv",
            "KMFA/tools/v013_s06_p3_validation_evidence_replay.py",
            "KMFA/tools/check_v013_s06_p3_validation_evidence_replay.py",
            "KMFA/tests/test_v013_s06_p3_validation_evidence_replay.py",
        ],
        "next_required_step": NEXT_REQUIRED_STEP,
    }


def write_report(manifest: dict[str, Any]) -> None:
    lines = [
        "# KMFA v0.1.3 S06-P3 Validation Evidence Replay",
        "",
        f"- task_id: `{TASK_ID}`",
        "- status: `completed_validated_local_only_upload_deferred_validation_evidence_replay`",
        "- scope: `S06-P3 only`",
        f"- s06_p1_dependency_validated: `{str(manifest['s06_p1_dependency_validated']).lower()}`",
        f"- s06_p2_dependency_validated: `{str(manifest['s06_p2_dependency_validated']).lower()}`",
        f"- metadata_quality_written: `{str(manifest['metadata_quality_written']).lower()}`",
        f"- zero_delta_result_output_written: `{str(manifest['zero_delta_result_output_written']).lower()}`",
        f"- mismatch_report_output_written: `{str(manifest['mismatch_report_output_written']).lower()}`",
        f"- project_validation_status_output_written: `{str(manifest['project_validation_status_output_written']).lower()}`",
        f"- project_status_count: `{manifest['project_status_count']}`",
        f"- blocked_project_status_count: `{manifest['blocked_project_status_count']}`",
        f"- metadata_zero_delta_records_written: `{manifest['metadata_zero_delta_records_written']}`",
        f"- metadata_data_quality_records_written: `{manifest['metadata_data_quality_records_written']}`",
        f"- metadata_source_difference_records_written: `{manifest['metadata_source_difference_records_written']}`",
        f"- metadata_mismatch_rows_written: `{manifest['metadata_mismatch_rows_written']}`",
        f"- q5_allowed_count: `{manifest['q5_allowed_count']}`",
        f"- report_grade_a_allowed_count: `{manifest['report_grade_a_allowed_count']}`",
        f"- hard_blocks: `{', '.join(manifest['hard_blocks'])}`",
        f"- raw_business_data_used: `{str(manifest['raw_business_data_used']).lower()}`",
        f"- raw_dir_read_performed: `{str(manifest['raw_dir_read_performed']).lower()}`",
        f"- raw_dir_mutation_performed: `{str(manifest['raw_dir_mutation_performed']).lower()}`",
        f"- stage6_review_performed: `{str(manifest['stage6_review_performed']).lower()}`",
        f"- github_upload_performed: `{str(manifest['github_upload_performed']).lower()}`",
        "",
        "## Task Mapping",
        "",
        "- `S6PCT01`: output sanitized `zero_delta_result.json` and `mismatch_report.csv`.",
        "- `S6PCT02`: output project validation statuses for the zero-delta mismatch project and unresolved difference project.",
        "- `S6PCT03`: append public-safe zero-delta, data-quality, difference-queue, and mismatch-index records to `metadata/quality`.",
        "",
        "## Boundary",
        "",
        "- This phase did not read, list, modify, delete, move, rename, overwrite, or write generated files inside the raw data inbox.",
        "- S06-P3 evidence consumes only v0.1.3 S06-P1/S06-P2 public-safe synthetic evidence.",
        "- Metadata/quality writes are limited to hash/ref/status/evidence and gate states.",
        "- Field plaintext, raw business values, PDF/Excel source values, raw filenames, sheet names, ZIP member names, and raw hashes are not published.",
        "- This phase does not close differences, run Stage 6 review, upload to GitHub, release a formal report, or allow business execution.",
        "",
        "## Next",
        "",
        NEXT_REQUIRED_STEP,
        "",
    ]
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_test_results_placeholder() -> None:
    TEST_RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    TEST_RESULTS_PATH.write_text(
        "\n".join(
            [
                "# KMFA v0.1.3 S06-P3 Validation Evidence Replay Test Results",
                "",
                f"- task_id: `{TASK_ID}`",
                "- status: `generated_pending_final_validation_capture`",
                "- github_upload_performed: `false`",
                "- raw_dir_read_performed: `false`",
                "- raw_dir_mutation_performed: `false`",
                "- stage6_review_performed: `false`",
                "",
                "Final command results are captured after the validator and governance checks complete in this run.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> int:
    evidence = build_and_write_evidence()
    manifest = build_manifest(evidence)
    _json_dump(MANIFEST_PATH, manifest)
    write_report(manifest)
    write_test_results_placeholder()
    print(
        "PASS: KMFA v0.1.3 S06-P3 validation evidence replay generated "
        f"(metadata_quality_written={str(manifest['metadata_quality_written']).lower()}, "
        f"project_statuses={manifest['project_status_count']}, "
        f"metadata_records={manifest['metadata_zero_delta_records_written'] + manifest['metadata_data_quality_records_written'] + manifest['metadata_source_difference_records_written']}, "
        f"github_upload={str(manifest['github_upload_performed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
