#!/usr/bin/env python3
"""Generate KMFA v0.1.4 S06-P2 cross-source difference queue evidence.

This phase locks the public-safe PDF/Excel difference queue contract only. It
depends on v0.1.4 S06-P1 and does not read the raw inbox, write S06-P3
metadata/quality outputs, close differences, run Stage 6 review, upload to
GitHub, generate formal reports, or execute business actions.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.check_v014_s06_p1_zero_delta_validator import validate_v014_s06_p1_zero_delta_validator
from KMFA.tools.cross_source_difference_queue import (
    build_queue_from_fixture,
    evaluate_report_grade_gate,
    validate_queue_item,
    write_queue_jsonl,
)


TASK_ID = "KMFA-V014-S06-P2-DIFFERENCE-QUEUE-20260704"
ACCEPTANCE_ID = "ACC-V014-S06-P2-DIFFERENCE-QUEUE"
SCHEMA_VERSION = "kmfa.v014_s06_p2_difference_queue.v1"
PHASE_SCOPE = "v014_s06_p2_difference_queue_only"
OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_S06_P2_DIFFERENCE_QUEUE")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
MANIFEST_PATH = MACHINE_DIR / "difference_queue_manifest.json"
FIXTURE_PATH = MACHINE_DIR / "pdf_excel_conflict_fixture.json"
QUEUE_PATH = MACHINE_DIR / "source_difference_queue.jsonl"
GATE_PATH = MACHINE_DIR / "report_grade_gate.json"
REPORT_PATH = HUMAN_DIR / "difference_queue_report.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"
S06_P1_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V014_S06_P1_ZERO_DELTA_VALIDATOR/machine/zero_delta_validator_manifest.json"
)
NEXT_PHASE = "S06-P3"
NEXT_INSTRUCTION = (
    "Run S06-P3 validation evidence output as a separate run only after S06-P2 is committed. "
    "Do not run Stage 6 review or GitHub upload in S06-P2. GitHub main upload remains deferred "
    "until v1.4 Stage 1-18 are complete, overall review has passed, and findings are fixed."
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


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def public_safe_conflict_fixture() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v014_s06_p2.pdf_excel_conflict_fixture.v1",
        "fixture_id": "KMFA-V014-S06P2-PDF-EXCEL-CONFLICT-PUBLIC-SAFE",
        "project_ref": "V014-SYN-PROJECT-S06P2-001",
        "field": "contract_amount_cents",
        "pdf_source_ref": {
            "source_id": "SRC-V014-S06P2-PDF-SYNTHETIC",
            "source_type": "pdf",
            "source_class": "raw_upload",
            "source_anchor_ref": "sha256:synthetic-v014-s06p2-pdf-anchor",
        },
        "excel_source_ref": {
            "source_id": "SRC-V014-S06P2-EXCEL-SYNTHETIC",
            "source_type": "excel",
            "source_class": "authorized_export",
            "source_anchor_ref": "sha256:synthetic-v014-s06p2-excel-anchor",
        },
        "pdf_value_cents": 10000,
        "excel_value_cents": 9999,
        "event_time": "2026-07-04T11:40:00+10:00",
        "evidence_ref": FIXTURE_PATH.as_posix(),
        "raw_business_data_used": False,
        "public_safe_fixture_only": True,
    }


def write_fixture_queue_and_gate() -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    fixture = public_safe_conflict_fixture()
    write_json(FIXTURE_PATH, fixture)
    queue_items = build_queue_from_fixture(FIXTURE_PATH)
    for item in queue_items:
        validate_queue_item(item)
    gate = evaluate_report_grade_gate(queue_items)
    write_queue_jsonl(queue_items, QUEUE_PATH)
    write_json(GATE_PATH, gate)
    return fixture, queue_items, gate


def build_manifest() -> dict[str, Any]:
    s06_p1 = validate_v014_s06_p1_zero_delta_validator()
    fixture, queue_items, gate = write_fixture_queue_and_gate()
    queue_item = queue_items[0]
    source_types = sorted(ref["source_type"] for ref in queue_item["source_refs"])

    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": "KMFA",
        "version": "0.1.4",
        "stage_id": "S06",
        "stage_name": "zero-delta validation and difference handling",
        "phase_id": "S06-P2",
        "phase_name": "cross-source difference queue",
        "phase_scope": PHASE_SCOPE,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "reviewed_head": git_output(["rev-parse", "HEAD"]),
        "worktree": git_output(["rev-parse", "--show-toplevel"]),
        "branch": git_output(["branch", "--show-current"]),
        "remote": git_output(["remote", "get-url", "origin"]),
        "status": "completed_validated_local_only_no_go_upload_deferred_difference_queue",
        "completed_task_ids": ["S06P2T01", "S06P2T02", "S06P2T03"],
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
            "next_recommended_phase": s06_p1["next_recommended_phase"],
        },
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
        "integer_cent_comparison_only": True,
        "float_money_allowed": False,
        "raw_business_data_used": False,
        "actual_business_difference_validated": False,
        "metadata_quality_written": False,
        "source_difference_queue_metadata_written": False,
        "s06_p3_started": False,
        "stage6_review_performed": False,
        "github_upload_performed": False,
        "github_upload_status": "not_uploaded_deferred_until_v014_stage1_18_complete",
        "raw_value_matching_performed": False,
        "lineage_full_check_performed": False,
        "formal_report_performed": False,
        "live_connector_called": False,
        "opme_deep_coupling_performed": False,
        "business_execution_performed": False,
        "release_state": {
            "current_data_quality_grade": "Q4",
            "current_report_grade": "D",
            "current_go_no_go": "NO_GO",
            "release_permission": "blocked",
            "delivery_allowed": False,
            "formal_report_allowed": False,
            "business_decision_basis_allowed": False,
            "business_execution_allowed": False,
            "github_main_upload_allowed": False,
            "blocking_reason": "s06_p3_quality_output_lineage_and_formal_report_not_completed_unresolved_difference_blocks_a_grade",
        },
        "raw_data_boundary": {
            "raw_inbox_ref": RAW_INBOX_REF,
            "raw_inbox_read_required_by_this_phase": False,
            "raw_inbox_read_by_this_phase": False,
            "raw_inbox_listed_by_this_phase": False,
            "raw_inbox_stat_by_this_phase": False,
            "raw_inbox_hashed_by_this_phase": False,
            "raw_inbox_modified_by_this_phase": False,
            "raw_inbox_deleted_by_this_phase": False,
            "raw_inbox_moved_by_this_phase": False,
            "raw_inbox_renamed_by_this_phase": False,
            "raw_inbox_overwritten_by_this_phase": False,
            "raw_inbox_written_by_this_phase": False,
            "raw_inbox_mutated_by_this_phase": False,
            "private_runtime_written_by_this_phase": False,
            "github_commit_allowed_for_raw": False,
        },
        "public_repo_safety": {
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
            "source_header_plaintext_committed": False,
            "row_or_cell_values_committed": False,
            "source_or_normalized_values_committed": False,
            "business_values_committed": False,
        },
        "validation_summary": {
            "py_compile": "PENDING_FINAL_VALIDATION",
            "generator": "PASS",
            "s06_p1_dependency": "PASS",
            "s06_p2_validator": "PENDING_FINAL_VALIDATION",
            "focused_unit_test": "PENDING_FINAL_VALIDATION",
            "legacy_difference_queue_validator": "PENDING_FINAL_VALIDATION",
            "legacy_difference_queue_unit": "PENDING_FINAL_VALIDATION",
            "no_omission_check": "PENDING_FINAL_VALIDATION",
            "no_float_money_check": "PENDING_FINAL_VALIDATION",
            "governance_validator": "PENDING_FINAL_VALIDATION",
            "lean_governance_validator": "PENDING_FINAL_VALIDATION",
            "governance_sync_validator": "PENDING_FINAL_VALIDATION",
            "raw_private_scan": "PENDING_FINAL_VALIDATION",
            "secret_scan": "PENDING_FINAL_VALIDATION",
            "public_s06_evidence_semantic_scan": "PENDING_FINAL_VALIDATION",
            "diff_check": "PENDING_FINAL_VALIDATION",
        },
        "evidence_refs": [
            REPORT_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            RISK_REGISTER_PATH.as_posix(),
            ROLLBACK_PATH.as_posix(),
            MANIFEST_PATH.as_posix(),
            FIXTURE_PATH.as_posix(),
            QUEUE_PATH.as_posix(),
            GATE_PATH.as_posix(),
        ],
        "fixture_public_safe": fixture["public_safe_fixture_only"],
        "queue_public_safe": queue_item["public_safe_fixture_only"],
        "gate_public_safe": gate["public_safe_fixture_only"],
        "next_recommended_phase": NEXT_PHASE,
        "next_phase_instruction": NEXT_INSTRUCTION,
    }


def write_human_evidence(manifest: dict[str, Any]) -> None:
    HUMAN_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        "\n".join(
            [
                "# KMFA v0.1.4 S06-P2 Cross-Source Difference Queue",
                "",
                f"- task_id: `{TASK_ID}`",
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
                "",
                "## Task Mapping",
                "",
                "- `S06P2T01`: PDF and Excel same-project conflict enters a manual difference queue.",
                "- `S06P2T02`: auto correction, averaging, rounding masks and source auto-selection remain forbidden.",
                "- `S06P2T03`: unresolved differences block report grade A.",
                "",
                "## Boundaries",
                "",
                "- Public-safe synthetic fixture only; no raw business data was used.",
                "- Raw inbox read/list/stat/hash/mutation/write flags remain false for this phase.",
                "- Runtime `metadata/quality` output belongs to S06-P3 and was not written here.",
                "- Difference closure, Stage 6 review, GitHub upload, formal report, live connector and business execution were not performed.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    TEST_RESULTS_PATH.write_text(
        "\n".join(
            [
                "# Test Results",
                "",
                "- Generator: PASS",
                "- S06-P1 dependency: PASS",
                "- S06-P2 validator: pending final validation",
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
                "| Synthetic queue passes but actual business source conflict is unresolved | Manifest marks actual business difference validation false and keeps D/NO_GO | controlled |",
                "| S06-P3 metadata quality is accidentally written early | Generator writes only stage evidence and flags metadata_quality_written false | controlled |",
                "| Unclosed difference is treated as A-grade-ready | Report grade gate blocks A until manual closure | controlled |",
                "| Raw data exposure | Evidence contains synthetic public-safe refs only and no raw inbox access | controlled |",
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
                "- Revert the S06-P2 commit.",
                "- Remove `KMFA/stage_artifacts/V014_S06_P2_DIFFERENCE_QUEUE/` if the phase is abandoned before commit.",
                "- Keep the operator-designated local raw/private inbox untouched.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> int:
    manifest = build_manifest()
    write_human_evidence(manifest)
    write_json(MANIFEST_PATH, manifest)
    print(
        "PASS: KMFA v0.1.4 S06-P2 difference queue evidence generated "
        f"(queue_items={manifest['queue_item_count']}, "
        f"difference_cents={manifest['difference_cents']}, "
        f"report_grade_a_allowed={str(manifest['report_grade_a_allowed']).lower()}, "
        f"github_upload={str(manifest['github_upload_performed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
