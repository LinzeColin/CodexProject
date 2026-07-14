#!/usr/bin/env python3
"""Generate KMFA v0.1.3 S06-P2 difference queue replay evidence.

This phase replays the existing public-safe PDF/Excel cross-source difference
queue logic. It depends on the v0.1.3 S06-P1 zero-delta replay evidence and
does not read the raw data inbox, write metadata/quality runtime records, run
Stage 6 review, or upload to GitHub.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.check_v013_s06_p1_zero_delta_replay import validate_v013_s06_p1_zero_delta_replay
from KMFA.tools.cross_source_difference_queue import (
    build_queue_from_fixture,
    evaluate_report_grade_gate,
    validate_queue_item,
    write_queue_jsonl,
)
from KMFA.tools.v013_s05_p1_a0_file_registration import RAW_DIR


PUBLIC_OUTPUT_DIR = Path("KMFA/stage_artifacts/V013_S06_P2_DIFFERENCE_QUEUE_REPLAY")
MACHINE_DIR = PUBLIC_OUTPUT_DIR / "machine"
HUMAN_DIR = PUBLIC_OUTPUT_DIR / "human"
MANIFEST_PATH = MACHINE_DIR / "difference_queue_replay_manifest.json"
FIXTURE_PATH = MACHINE_DIR / "pdf_excel_conflict_fixture.json"
QUEUE_PATH = MACHINE_DIR / "source_difference_queue.jsonl"
GATE_PATH = MACHINE_DIR / "report_grade_gate.json"
REPORT_PATH = HUMAN_DIR / "difference_queue_replay_report.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
S06_P1_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V013_S06_P1_ZERO_DELTA_REPLAY/machine/zero_delta_replay_manifest.json"
)
TASK_ID = "KMFA-V013-S06-P2-DIFFERENCE-QUEUE-REPLAY-20260703"
SCHEMA_VERSION = "kmfa.v013_s06_p2_difference_queue_replay.v1"
PHASE_SCOPE = "v013_s06_p2_difference_queue_replay_only"
NEXT_REQUIRED_STEP = (
    "Proceed to v0.1.3 S06-P3 as a separate run. Do not run Stage 6 review or GitHub upload; "
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


def public_safe_conflict_fixture() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v013_s06_p2.pdf_excel_conflict_fixture.v1",
        "fixture_id": "KMFA-V013-S06P2-PDF-EXCEL-CONFLICT-PUBLIC-SAFE",
        "project_ref": "V013-SYN-PROJECT-S06P2-001",
        "field": "contract_amount_cents",
        "pdf_source_ref": {
            "source_id": "SRC-V013-S06P2-PDF-SYNTHETIC",
            "source_type": "pdf",
            "source_class": "raw_upload",
            "source_anchor_ref": "sha256:synthetic-v013-s06p2-pdf-anchor",
        },
        "excel_source_ref": {
            "source_id": "SRC-V013-S06P2-EXCEL-SYNTHETIC",
            "source_type": "excel",
            "source_class": "authorized_export",
            "source_anchor_ref": "sha256:synthetic-v013-s06p2-excel-anchor",
        },
        "pdf_value_cents": 10000,
        "excel_value_cents": 9999,
        "event_time": "2026-07-03T06:20:00+10:00",
        "evidence_ref": FIXTURE_PATH.as_posix(),
        "raw_business_data_used": False,
        "public_safe_fixture_only": True,
    }


def write_fixture_queue_and_gate() -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    fixture = public_safe_conflict_fixture()
    _json_dump(FIXTURE_PATH, fixture)
    queue_items = build_queue_from_fixture(FIXTURE_PATH)
    for item in queue_items:
        validate_queue_item(item)
    gate = evaluate_report_grade_gate(queue_items)
    write_queue_jsonl(queue_items, QUEUE_PATH)
    _json_dump(GATE_PATH, gate)
    return fixture, queue_items, gate


def build_manifest() -> dict[str, Any]:
    s06_p1 = validate_v013_s06_p1_zero_delta_replay()
    fixture, queue_items, gate = write_fixture_queue_and_gate()
    queue_item = queue_items[0]
    source_types = sorted(ref["source_type"] for ref in queue_item["source_refs"])

    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": "KMFA",
        "version": "0.1.3",
        "stage_id": "S06",
        "stage_name": "v0.1.3 zero-delta validation and difference handling",
        "phase_id": "S06-P2",
        "phase_name": "cross-source difference queue replay",
        "phase_scope": PHASE_SCOPE,
        "task_id": TASK_ID,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "reviewed_head": git_output(["rev-parse", "HEAD"]),
        "worktree": git_output(["rev-parse", "--show-toplevel"]),
        "branch": git_output(["branch", "--show-current"]),
        "remote": git_output(["remote", "get-url", "origin"]),
        "status": "completed_validated_local_only_upload_deferred_difference_queue_replay",
        "completed_task_ids": ["S6PBT01", "S6PBT02", "S6PBT03"],
        "acceptance_ids": ["ACC-V013-S06-P2-DIFFERENCE-QUEUE-REPLAY"],
        "s06_p1_dependency_validated": True,
        "s06_p1_manifest_ref": S06_P1_MANIFEST_PATH.as_posix(),
        "s06_p1_dependency_summary": {
            "phase_id": s06_p1["phase_id"],
            "pass_fixture_field_comparison_count": s06_p1["pass_fixture_field_comparison_count"],
            "one_cent_mismatch_detected": s06_p1["one_cent_mismatch_detected"],
            "minimum_fail_difference_cents": s06_p1["minimum_fail_difference_cents"],
            "metadata_quality_written": s06_p1["metadata_quality_written"],
            "difference_queue_created": s06_p1["difference_queue_created"],
            "github_upload_performed": s06_p1["github_upload_performed"],
        },
        "taskpack_zero_delta_plan_ref": "KMFA/taskpack/v1_2/08_KMFA_零差异验证与测试计划_v1_1.md",
        "taskpack_roadmap_ref": "KMFA/taskpack/v1_2/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_2.md",
        "source_queue_tool_ref": "KMFA/tools/cross_source_difference_queue.py",
        "legacy_queue_validator_ref": "KMFA/tools/check_s06_p2_difference_queue.py",
        "legacy_queue_unit_test_ref": "KMFA/tests/test_cross_source_difference_queue.py",
        "fixture_ref": FIXTURE_PATH.as_posix(),
        "queue_ref": QUEUE_PATH.as_posix(),
        "gate_ref": GATE_PATH.as_posix(),
        "queue_item_count": len(queue_items),
        "queue_ids": [item["queue_id"] for item in queue_items],
        "queue_statuses": [item["status"] for item in queue_items],
        "pdf_excel_conflict_detected": True,
        "conflict_scope": queue_item["conflict_scope"],
        "conflict_project_ref": queue_item["project_ref"],
        "conflict_field": queue_item["field"],
        "source_types": source_types,
        "pdf_value_cents": queue_item["pdf_value_cents"],
        "excel_value_cents": queue_item["excel_value_cents"],
        "difference_cents": queue_item["difference_cents"],
        "absolute_difference_cents": abs(queue_item["difference_cents"]),
        "minimum_queue_difference_cents": 1,
        "auto_correction_allowed": queue_item["auto_correction_allowed"],
        "averaging_allowed": queue_item["averaging_allowed"],
        "rounding_mask_allowed": queue_item["rounding_mask_allowed"],
        "auto_selection_allowed": queue_item["auto_selection_allowed"],
        "auto_selected_source_id": queue_item["auto_selected_source_id"],
        "resolved_value_cents": queue_item["resolved_value_cents"],
        "resolution_policy": queue_item["resolution_policy"],
        "report_grade_a_allowed": gate["report_grade_a_allowed"],
        "maximum_report_grade": gate["maximum_report_grade"],
        "hard_block_reason": gate["hard_block_reason"],
        "blocking_queue_ids": gate["blocking_queue_ids"],
        "queue_status_before_manual_review": "queued_for_manual_review",
        "manual_review_required": True,
        "difference_closed": False,
        "raw_business_data_used": False,
        "raw_dir_read_performed": False,
        "raw_dir_mutation_performed": False,
        "metadata_quality_written": False,
        "source_difference_queue_metadata_written": False,
        "stage6_review_performed": False,
        "s06_p3_performed": False,
        "github_upload_performed": False,
        "github_upload_deferred_until_stage10_batch": True,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "business_execution_allowed": False,
        "current_data_quality_grade": "Q2",
        "current_report_grade": "D",
        "release_permission": "blocked",
        "fixture_public_safe": fixture["public_safe_fixture_only"],
        "queue_public_safe": queue_item["public_safe_fixture_only"],
        "gate_public_safe": gate["public_safe_fixture_only"],
        "integer_cent_comparison_only": True,
        "float_money_allowed": False,
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
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v013_s06_p2_difference_queue_replay.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s06_p2_difference_queue_replay.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v013_s06_p2_difference_queue_replay -q",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s06_p1_zero_delta_replay.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s06_p2_difference_queue.py --queue-jsonl KMFA/stage_artifacts/V013_S06_P2_DIFFERENCE_QUEUE_REPLAY/machine/source_difference_queue.jsonl --gate-json KMFA/stage_artifacts/V013_S06_P2_DIFFERENCE_QUEUE_REPLAY/machine/report_grade_gate.json",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_cross_source_difference_queue -q",
        ],
        "evidence_refs": [
            MANIFEST_PATH.as_posix(),
            REPORT_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            FIXTURE_PATH.as_posix(),
            QUEUE_PATH.as_posix(),
            GATE_PATH.as_posix(),
            "KMFA/tools/v013_s06_p2_difference_queue_replay.py",
            "KMFA/tools/check_v013_s06_p2_difference_queue_replay.py",
            "KMFA/tests/test_v013_s06_p2_difference_queue_replay.py",
        ],
        "next_required_step": NEXT_REQUIRED_STEP,
    }


def write_report(manifest: dict[str, Any]) -> None:
    lines = [
        "# KMFA v0.1.3 S06-P2 Difference Queue Replay",
        "",
        f"- task_id: `{manifest['task_id']}`",
        f"- status: `{manifest['status']}`",
        "- scope: `S06-P2 only`",
        "- s06_p1_dependency_validated: `true`",
        f"- queue_item_count: `{manifest['queue_item_count']}`",
        f"- pdf_excel_conflict_detected: `{str(manifest['pdf_excel_conflict_detected']).lower()}`",
        f"- difference_cents: `{manifest['difference_cents']}`",
        f"- auto_correction_allowed: `{str(manifest['auto_correction_allowed']).lower()}`",
        f"- averaging_allowed: `{str(manifest['averaging_allowed']).lower()}`",
        f"- rounding_mask_allowed: `{str(manifest['rounding_mask_allowed']).lower()}`",
        f"- auto_selection_allowed: `{str(manifest['auto_selection_allowed']).lower()}`",
        f"- report_grade_a_allowed: `{str(manifest['report_grade_a_allowed']).lower()}`",
        f"- maximum_report_grade: `{manifest['maximum_report_grade']}`",
        f"- hard_block_reason: `{manifest['hard_block_reason']}`",
        "- raw_business_data_used: `false`",
        "- raw_dir_read_performed: `false`",
        "- raw_dir_mutation_performed: `false`",
        "- metadata_quality_written: `false`",
        "- stage6_review_performed: `false`",
        "- github_upload_performed: `false`",
        "- github_upload_deferred_until_stage10_batch: `true`",
        "- formal_report_allowed: `false`",
        "- business_execution_allowed: `false`",
        "",
        "## Task Mapping",
        "",
        "- `S6PBT01`: PDF and Excel same-project conflict enters the difference queue.",
        "- `S6PBT02`: no auto correction, averaging, rounding mask, or auto source selection is allowed.",
        "- `S6PBT03`: report grade A remains blocked until the difference is closed.",
        "",
        "## Evidence",
        "",
        f"- manifest: `{MANIFEST_PATH.as_posix()}`",
        f"- fixture: `{FIXTURE_PATH.as_posix()}`",
        f"- queue: `{QUEUE_PATH.as_posix()}`",
        f"- report grade gate: `{GATE_PATH.as_posix()}`",
        "",
        "## Boundary",
        "",
        "- This phase did not read, list, modify, delete, move, rename, overwrite, or write generated files inside the raw data inbox.",
        "- Public evidence uses a synthetic/public-safe PDF and Excel conflict fixture only.",
        "- This phase does not write runtime `metadata/quality` records; that belongs to S06-P3.",
        "- This phase does not resolve or close the difference.",
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
        "# KMFA v0.1.3 S06-P2 Difference Queue Replay Test Results",
        "",
        f"- task_id: `{manifest['task_id']}`",
        "- status: `generated_pending_final_validation_capture`",
        "- github_upload_performed: `false`",
        "- raw_dir_read_performed: `false`",
        "- raw_dir_mutation_performed: `false`",
        "- metadata_quality_written: `false`",
        "- stage6_review_performed: `false`",
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
        "PASS: KMFA v0.1.3 S06-P2 difference queue replay evidence generated "
        f"(queue_items={manifest['queue_item_count']}, "
        f"difference_cents={manifest['difference_cents']}, "
        f"report_grade_a_allowed={str(manifest['report_grade_a_allowed']).lower()}, "
        f"github_upload={str(manifest['github_upload_performed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
