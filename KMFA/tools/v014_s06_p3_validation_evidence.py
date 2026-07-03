#!/usr/bin/env python3
"""Generate KMFA v0.1.4 S06-P3 public-safe validation evidence outputs."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.check_v014_s06_p1_zero_delta_validator import validate_v014_s06_p1_zero_delta_validator
from KMFA.tools.check_v014_s06_p2_difference_queue import validate_v014_s06_p2_difference_queue
from KMFA.tools.validation_evidence_output import build_from_paths, write_validation_evidence_outputs


TASK_ID = "KMFA-V014-S06-P3-VALIDATION-EVIDENCE-20260704"
ACCEPTANCE_ID = "ACC-V014-S06-P3-VALIDATION-EVIDENCE"
SCHEMA_VERSION = "kmfa.v014_s06_p3_validation_evidence.v1"
PHASE_SCOPE = "v014_s06_p3_validation_evidence_only"
EVIDENCE_TIME = "2026-07-04T12:20:00+10:00"

OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_S06_P3_VALIDATION_EVIDENCE")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
METADATA_QUALITY_DIR = Path("KMFA/metadata/quality")

MANIFEST_PATH = MACHINE_DIR / "validation_evidence_manifest.json"
ZERO_DELTA_OUTPUT_PATH = MACHINE_DIR / "zero_delta_result.json"
MISMATCH_OUTPUT_PATH = MACHINE_DIR / "mismatch_report.csv"
PROJECT_STATUS_OUTPUT_PATH = MACHINE_DIR / "project_validation_status.jsonl"
REPORT_PATH = HUMAN_DIR / "validation_evidence_report.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

S06_P1_RESULT_PATH = Path(
    "KMFA/stage_artifacts/V014_S06_P1_ZERO_DELTA_VALIDATOR/machine/zero_delta_one_cent_mismatch_result.json"
)
S06_P1_MISMATCH_REPORT_PATH = Path(
    "KMFA/stage_artifacts/V014_S06_P1_ZERO_DELTA_VALIDATOR/machine/mismatch_report.csv"
)
S06_P2_QUEUE_PATH = Path(
    "KMFA/stage_artifacts/V014_S06_P2_DIFFERENCE_QUEUE/machine/source_difference_queue.jsonl"
)
S06_P2_GATE_PATH = Path(
    "KMFA/stage_artifacts/V014_S06_P2_DIFFERENCE_QUEUE/machine/report_grade_gate.json"
)

NEXT_PHASE = "Stage 6 review"
NEXT_INSTRUCTION = (
    "Run v0.1.4 Stage 6 overall review as a separate run after S06-P3 is committed. "
    "Do not perform GitHub upload. GitHub main upload remains deferred until v1.4 Stage 1-18 "
    "are complete, overall review has passed, and findings are fixed."
)
RAW_INBOX_REF = "operator-designated local raw/private inbox outside repository"


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


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def patch_metadata_refs(evidence: dict[str, Any]) -> None:
    for record in evidence["metadata_zero_delta_records"]:
        record["result_ref"] = ZERO_DELTA_OUTPUT_PATH.as_posix()
        record["mismatch_report_ref"] = MISMATCH_OUTPUT_PATH.as_posix()


def build_and_write_evidence() -> dict[str, Any]:
    validate_v014_s06_p1_zero_delta_validator()
    validate_v014_s06_p2_difference_queue()
    evidence = build_from_paths(
        zero_delta_result_path=S06_P1_RESULT_PATH,
        source_mismatch_report_path=S06_P1_MISMATCH_REPORT_PATH,
        difference_queue_path=S06_P2_QUEUE_PATH,
        report_gate_path=S06_P2_GATE_PATH,
        evidence_time=EVIDENCE_TIME,
    )
    patch_metadata_refs(evidence)
    write_validation_evidence_outputs(
        evidence,
        output_dir=MACHINE_DIR,
        metadata_quality_dir=METADATA_QUALITY_DIR,
    )
    return evidence


def build_manifest(evidence: dict[str, Any]) -> dict[str, Any]:
    zero_delta_result = evidence["zero_delta_result"]
    project_statuses = evidence["project_validation_statuses"]
    mismatch_rows = evidence["mismatch_rows"]
    metadata_zero_delta_records = evidence["metadata_zero_delta_records"]
    metadata_data_quality_records = evidence["metadata_data_quality_records"]
    metadata_source_difference_records = evidence["metadata_source_difference_records"]
    blocked_statuses = [status for status in project_statuses if status["validation_status"] == "blocked"]

    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": "KMFA",
        "version": "0.1.4",
        "stage_id": "S06",
        "stage_name": "zero-delta validation and difference handling",
        "phase_id": "S06-P3",
        "phase_name": "validation evidence output",
        "phase_scope": PHASE_SCOPE,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "evidence_time": EVIDENCE_TIME,
        "reviewed_head": git_output(["rev-parse", "HEAD"]),
        "worktree": git_output(["rev-parse", "--show-toplevel"]),
        "branch": git_output(["branch", "--show-current"]),
        "remote": git_output(["remote", "get-url", "origin"]),
        "status": "completed_validated_local_only_no_go_upload_deferred_validation_evidence",
        "completed_task_ids": ["S06P3T01", "S06P3T02", "S06P3T03"],
        "s06_p1_dependency_validated": True,
        "s06_p2_dependency_validated": True,
        "s06_p1_result_ref": S06_P1_RESULT_PATH.as_posix(),
        "s06_p1_mismatch_report_ref": S06_P1_MISMATCH_REPORT_PATH.as_posix(),
        "s06_p2_queue_ref": S06_P2_QUEUE_PATH.as_posix(),
        "s06_p2_gate_ref": S06_P2_GATE_PATH.as_posix(),
        "source_evidence_builder_ref": "KMFA/tools/validation_evidence_output.py",
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
        "raw_inbox_read_performed": False,
        "raw_inbox_listed_performed": False,
        "raw_inbox_stat_performed": False,
        "raw_inbox_hash_performed": False,
        "raw_inbox_mutation_performed": False,
        "raw_value_matching_performed": False,
        "difference_closed": False,
        "auto_correction_allowed": False,
        "averaging_allowed": False,
        "rounding_mask_allowed": False,
        "auto_selection_allowed": False,
        "stage6_review_performed": False,
        "github_upload_performed": False,
        "github_upload_status": "not_uploaded_deferred_until_v014_stage1_18_complete",
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "business_execution_allowed": False,
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "release_permission": "blocked",
        "raw_data_boundary": {
            "raw_inbox_ref": RAW_INBOX_REF,
            "codex_read_required_by_this_phase": False,
            "codex_read_performed_by_this_phase": False,
            "codex_list_performed_by_this_phase": False,
            "codex_stat_performed_by_this_phase": False,
            "codex_hash_performed_by_this_phase": False,
            "codex_modify_allowed": False,
            "codex_delete_allowed": False,
            "codex_move_allowed": False,
            "codex_rename_allowed": False,
            "codex_overwrite_allowed": False,
            "codex_generate_inside_allowed": False,
            "github_commit_allowed": False,
        },
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
        "validation_summary": {
            "generator": "PASS",
            "s06_p1_dependency": "PASS",
            "s06_p2_dependency": "PASS",
            "s06_p3_validator": "PENDING_FINAL_VALIDATION",
            "focused_unit_test": "PENDING_FINAL_VALIDATION",
            "governance_validator": "PENDING_FINAL_VALIDATION",
            "lean_governance_validator": "PENDING_FINAL_VALIDATION",
            "governance_sync_validator": "PENDING_FINAL_VALIDATION",
            "raw_private_scan": "PENDING_FINAL_VALIDATION",
            "secret_scan": "PENDING_FINAL_VALIDATION",
            "diff_check": "PENDING_FINAL_VALIDATION",
        },
        "evidence_refs": [
            REPORT_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            RISK_REGISTER_PATH.as_posix(),
            ROLLBACK_PATH.as_posix(),
            MANIFEST_PATH.as_posix(),
            ZERO_DELTA_OUTPUT_PATH.as_posix(),
            MISMATCH_OUTPUT_PATH.as_posix(),
            PROJECT_STATUS_OUTPUT_PATH.as_posix(),
            "KMFA/metadata/quality/zero_delta_results.jsonl",
            "KMFA/metadata/quality/data_quality_results.jsonl",
            "KMFA/metadata/quality/source_difference_queue.jsonl",
            "KMFA/metadata/quality/mismatch_report.csv",
            "KMFA/tools/v014_s06_p3_validation_evidence.py",
            "KMFA/tools/check_v014_s06_p3_validation_evidence.py",
            "KMFA/tests/test_v014_s06_p3_validation_evidence.py",
        ],
        "next_recommended_phase": NEXT_PHASE,
        "next_phase_instruction": NEXT_INSTRUCTION,
    }


def write_human_evidence(manifest: dict[str, Any]) -> None:
    HUMAN_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        "\n".join(
            [
                "# KMFA v0.1.4 S06-P3 Validation Evidence",
                "",
                f"- task_id: `{TASK_ID}`",
                "- status: `completed_validated_local_only_no_go_upload_deferred_validation_evidence`",
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
                f"- raw_inbox_read_performed: `{str(manifest['raw_inbox_read_performed']).lower()}`",
                f"- raw_inbox_mutation_performed: `{str(manifest['raw_inbox_mutation_performed']).lower()}`",
                f"- stage6_review_performed: `{str(manifest['stage6_review_performed']).lower()}`",
                f"- github_upload_performed: `{str(manifest['github_upload_performed']).lower()}`",
                "",
                "## Task Mapping",
                "",
                "- `S06P3T01`: output sanitized `zero_delta_result.json` and `mismatch_report.csv`.",
                "- `S06P3T02`: output project validation statuses for the zero-delta mismatch and unresolved difference projects.",
                "- `S06P3T03`: append public-safe validation records to `metadata/quality`.",
                "",
                "## Boundary",
                "",
                "- This phase consumes only v0.1.4 S06-P1/S06-P2 public-safe evidence.",
                "- Metadata/quality writes are limited to hash/ref/status/evidence and gate states.",
                "- Field plaintext, raw business values, PDF/Excel source values, raw filenames, sheet names, ZIP member names, and raw hashes are not published.",
                "- This phase does not read or mutate the operator-designated local raw/private inbox.",
                "- This phase does not close differences, run Stage 6 review, upload to GitHub, release a formal report, or allow business execution.",
                "",
                "## Next",
                "",
                NEXT_INSTRUCTION,
                "",
            ]
        ),
        encoding="utf-8",
    )
    TEST_RESULTS_PATH.write_text(
        "\n".join(
            [
                "# Test Results",
                "",
                "- Generator: PASS",
                "- S06-P1 dependency: PASS",
                "- S06-P2 dependency: PASS",
                "- S06-P3 validator: pending final validation",
                "- Focused unit test: pending final validation",
                "- Governance and safety scans: pending final validation",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    RISK_REGISTER_PATH.write_text(
        "\n".join(
            [
                "# Risk Register",
                "",
                "| Risk | Control | Status |",
                "|---|---|---|",
                "| Metadata/quality output is mistaken for actual business zero-delta | Manifest keeps actual raw value matching false and Go/No-Go blocked | controlled |",
                "| Sanitized report leaks source field/value plaintext | Validator blocks forbidden public output keys and source amount literals | controlled |",
                "| S06-P3 is used to close unresolved difference | Manifest keeps difference_closed false and report grade A count zero | controlled |",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    ROLLBACK_PATH.write_text(
        "\n".join(
            [
                "# Rollback Plan",
                "",
                "- Revert the S06-P3 commit.",
                "- Remove `KMFA/stage_artifacts/V014_S06_P3_VALIDATION_EVIDENCE/` if the phase is abandoned before commit.",
                "- Remove the S06-P3 records appended to `KMFA/metadata/quality` only by reverting the same commit.",
                "- Keep the operator-designated local raw/private inbox untouched.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> int:
    evidence = build_and_write_evidence()
    manifest = build_manifest(evidence)
    write_human_evidence(manifest)
    write_json(MANIFEST_PATH, manifest)
    print(
        "PASS: KMFA v0.1.4 S06-P3 validation evidence generated "
        f"(metadata_quality_written={str(manifest['metadata_quality_written']).lower()}, "
        f"project_statuses={manifest['project_status_count']}, "
        f"blocked={manifest['blocked_project_status_count']}, "
        f"q5_allowed={manifest['q5_allowed_count']}, "
        f"github_upload={str(manifest['github_upload_performed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
