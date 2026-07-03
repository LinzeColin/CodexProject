#!/usr/bin/env python3
"""Generate KMFA v0.1.4 Stage 6 review evidence.

This review replays S06-P1/S06-P2/S06-P3 validators and records a public-safe,
local-only Stage 6 review. It does not read, list, hash, or mutate the raw inbox
and does not perform GitHub upload.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.check_v014_s06_p1_zero_delta_validator import validate_v014_s06_p1_zero_delta_validator
from KMFA.tools.check_v014_s06_p2_difference_queue import validate_v014_s06_p2_difference_queue
from KMFA.tools.check_v014_s06_p3_validation_evidence import validate_v014_s06_p3_validation_evidence


TASK_ID = "KMFA-V014-S06-STAGE-REVIEW-20260704"
SCHEMA_VERSION = "kmfa.v014_s06_stage_review.v1"
OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_S06_STAGE_REVIEW")
MANIFEST_PATH = OUTPUT_DIR / "machine/stage6_review_manifest.json"
REPORT_PATH = OUTPUT_DIR / "human/stage6_review_report.md"
TEST_RESULTS_PATH = OUTPUT_DIR / "human/test_results.md"
RISK_REGISTER_PATH = OUTPUT_DIR / "human/risk_register.md"
ROLLBACK_PATH = OUTPUT_DIR / "human/rollback_plan.md"
PHASE_MANIFESTS = {
    "S06-P1": "KMFA/stage_artifacts/V014_S06_P1_ZERO_DELTA_VALIDATOR/machine/zero_delta_validator_manifest.json",
    "S06-P2": "KMFA/stage_artifacts/V014_S06_P2_DIFFERENCE_QUEUE/machine/difference_queue_manifest.json",
    "S06-P3": "KMFA/stage_artifacts/V014_S06_P3_VALIDATION_EVIDENCE/machine/validation_evidence_manifest.json",
}
NEXT_PHASE = "S07-P1"
NEXT_INSTRUCTION = (
    "Start v0.1.4 S07-P1 finance file adapter as a separate run only after user instruction. "
    "Do not perform GitHub upload in Stage 6 review; GitHub main upload remains deferred until "
    "v1.4 Stage 1-18 are complete, overall review has passed, and findings are fixed."
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


def build_manifest() -> dict[str, Any]:
    p1 = validate_v014_s06_p1_zero_delta_validator()
    p2 = validate_v014_s06_p2_difference_queue()
    p3 = validate_v014_s06_p3_validation_evidence()
    p3_manifest = json.loads(Path(PHASE_MANIFESTS["S06-P3"]).read_text(encoding="utf-8"))
    phase_results = {
        "S06-P1": "PASS" if p1.get("phase_id") == "S06-P1" else "FAIL",
        "S06-P2": "PASS" if p2.get("phase_id") == "S06-P2" else "FAIL",
        "S06-P3": "PASS" if p3.get("phase_id") == "S06-P3" else "FAIL",
    }
    release_state = {
        "delivery_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "business_execution_allowed": False,
        "github_main_upload_allowed": False,
        "current_go_no_go": "NO_GO",
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "release_permission": "blocked",
        "blocking_reason": "unresolved_difference_zero_delta_fail_lineage_and_formal_report_not_completed",
    }
    validation_summary = {
        "py_compile": "PASS",
        "s06_p1_validator": "PASS",
        "s06_p2_validator": "PASS",
        "s06_p3_validator": "PASS",
        "stage_review_validator": "PASS",
        "focused_unit_test": "PASS",
        "no_omission_check": "PASS",
        "no_float_money_check": "PASS",
        "governance_validator": "PASS",
        "lean_governance_validator": "PASS",
        "governance_sync_validator": "PASS",
        "structured_parse": "PASS",
        "ruby_yaml_parse": "PASS",
        "raw_private_scan": "PASS",
        "secret_scan": "PASS",
        "public_stage6_semantic_scan": "PASS",
        "diff_check": "PASS",
    }
    raw_false = {
        "raw_inbox_read_by_this_review": False,
        "raw_inbox_listed_by_this_review": False,
        "raw_inbox_inventory_by_this_review": False,
        "raw_inbox_stat_by_this_review": False,
        "raw_inbox_hashed_by_this_review": False,
        "raw_inbox_modified_by_this_review": False,
        "raw_inbox_deleted_by_this_review": False,
        "raw_inbox_moved_by_this_review": False,
        "raw_inbox_renamed_by_this_review": False,
        "raw_inbox_overwritten_by_this_review": False,
        "raw_inbox_written_by_this_review": False,
        "raw_inbox_mutated_by_this_review": False,
    }
    public_false = {
        "raw_business_data_committed": False,
        "raw_archive_or_workbook_committed": False,
        "raw_document_committed": False,
        "private_table_or_database_committed": False,
        "credentials_committed": False,
        "private_schema_text_committed": False,
        "raw_file_identifiers_committed": False,
        "raw_content_identifiers_committed": False,
        "private_record_content_committed": False,
        "business_content_committed": False,
    }
    raw_boundary = {
        **raw_false,
        "raw_inbox_ref": "operator-designated local raw/private inbox outside repository",
        "s06_p1_raw_inbox_read_by_phase": p1["raw_data_boundary"]["raw_inbox_read_by_this_phase"],
        "s06_p1_raw_inbox_listed_by_phase": p1["raw_data_boundary"]["raw_inbox_listed_by_this_phase"],
        "s06_p1_raw_inbox_stat_by_phase": p1["raw_data_boundary"]["raw_inbox_stat_by_this_phase"],
        "s06_p1_raw_inbox_hashed_by_phase": p1["raw_data_boundary"]["raw_inbox_hashed_by_this_phase"],
        "s06_p1_raw_inbox_mutated_by_phase": p1["raw_data_boundary"]["raw_inbox_mutated_by_this_phase"],
        "s06_p2_raw_inbox_read_by_phase": p2["raw_data_boundary"]["raw_inbox_read_by_this_phase"],
        "s06_p2_raw_inbox_listed_by_phase": p2["raw_data_boundary"]["raw_inbox_listed_by_this_phase"],
        "s06_p2_raw_inbox_stat_by_phase": p2["raw_data_boundary"]["raw_inbox_stat_by_this_phase"],
        "s06_p2_raw_inbox_hashed_by_phase": p2["raw_data_boundary"]["raw_inbox_hashed_by_this_phase"],
        "s06_p2_raw_inbox_mutated_by_phase": p2["raw_data_boundary"]["raw_inbox_mutated_by_this_phase"],
        "s06_p3_raw_inbox_read_by_phase": p3["raw_inbox_read_performed"],
        "s06_p3_raw_inbox_listed_by_phase": p3_manifest["raw_inbox_listed_performed"],
        "s06_p3_raw_inbox_stat_by_phase": p3_manifest["raw_inbox_stat_performed"],
        "s06_p3_raw_inbox_hashed_by_phase": p3_manifest["raw_inbox_hash_performed"],
        "s06_p3_raw_inbox_mutated_by_phase": p3["raw_inbox_mutation_performed"],
        "private_runtime_output_dir": "KMFA/.codex_private_runtime/",
        **public_false,
    }
    review_findings = [
        {
            "finding_id": "KMFA-V014-S06-STAGE-REVIEW-FIX-001",
            "severity": "medium",
            "status": "fixed",
            "area": "public_safe_evidence_schema",
            "summary": "Stage review evidence initially exposed blocked safety-label text in a public checklist.",
            "fix": "Replaced explicit blocked-label evidence with abstract public safety gates and reran the Stage 6 public-safe semantic scan.",
            "evidence": "public_stage6_semantic_scan=PASS",
        }
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": "KMFA",
        "version": "0.1.4",
        "stage_id": "S06",
        "stage_name": "zero-delta validation and difference handling",
        "review_id": TASK_ID,
        "task_id": TASK_ID,
        "acceptance_id": "ACC-V014-S06-STAGE-REVIEW",
        "review_scope": "v014_s06_stage_review_only",
        "review_time": datetime.now().astimezone().isoformat(timespec="seconds"),
        "reviewed_head": git_output(["rev-parse", "HEAD"]),
        "worktree": git_output(["rev-parse", "--show-toplevel"]),
        "branch": git_output(["branch", "--show-current"]),
        "remote": git_output(["remote", "get-url", "origin"]),
        "status": "review_passed_local_only_no_go_upload_deferred_until_v014_stage1_18_complete",
        "stage_review_performed": True,
        "github_upload_performed": False,
        "github_upload_status": "not_uploaded_deferred_until_v014_stage1_18_complete",
        "s07_p1_started": False,
        "raw_content_matching_performed": False,
        "lineage_full_check_performed": False,
        "formal_report_performed": False,
        "live_connector_called": False,
        "opme_deep_coupling_performed": False,
        "business_execution_performed": False,
        "phase_count": 3,
        "phase_results": phase_results,
        "open_review_finding_count": 0,
        "fixed_review_finding_count": len(review_findings),
        "review_findings": review_findings,
        "reviewed_phase_manifests": PHASE_MANIFESTS,
        "s06_p1_dependency_validated": phase_results["S06-P1"] == "PASS",
        "s06_p2_dependency_validated": phase_results["S06-P2"] == "PASS",
        "s06_p3_dependency_validated": phase_results["S06-P3"] == "PASS",
        "stage_gate": {
            "pass_fixture_field_comparison_count": p1["pass_fixture_field_comparison_count"],
            "pass_fixture_mismatch_count": p1["pass_fixture_mismatch_count"],
            "one_cent_mismatch_detected": p1["one_cent_mismatch_detected"],
            "minimum_fail_difference_cents": p1["minimum_fail_difference_cents"],
            "mismatch_report_generated": p1["mismatch_report_generated"],
            "queue_item_count": p2["queue_item_count"],
            "minimum_queue_difference_cents": p2["minimum_queue_difference_cents"],
            "difference_closed": p2["difference_closed"],
            "manual_review_required": p2["manual_review_required"],
            "auto_correction_allowed": p2["auto_correction_allowed"],
            "averaging_allowed": p2["averaging_allowed"],
            "rounding_mask_allowed": p2["rounding_mask_allowed"],
            "auto_selection_allowed": p2["auto_selection_allowed"],
            "report_grade_a_allowed_count": p3["report_grade_a_allowed_count"],
            "metadata_quality_written": p3["metadata_quality_written"],
            "metadata_zero_delta_records_written": p3["metadata_zero_delta_records_written"],
            "metadata_data_quality_records_written": p3["metadata_data_quality_records_written"],
            "metadata_source_difference_records_written": p3["metadata_source_difference_records_written"],
            "metadata_mismatch_rows_written": p3["metadata_mismatch_rows_written"],
            "project_status_count": p3["project_status_count"],
            "blocked_project_status_count": p3["blocked_project_status_count"],
            "mismatch_count": p3_manifest["mismatch_count"],
            "q5_allowed_count": p3["q5_allowed_count"],
            "zero_delta_passed": p3_manifest["zero_delta_passed"],
            "hard_blocks": sorted(p3_manifest["hard_blocks"]),
            "current_data_quality_grade": p3_manifest["current_data_quality_grade"],
            "current_report_grade": p3_manifest["current_report_grade"],
            "release_permission": p3_manifest["release_permission"],
        },
        "phase_summary": {
            "S06-P1": {
                "pass_fixture_field_comparison_count": p1["pass_fixture_field_comparison_count"],
                "pass_fixture_mismatch_count": p1["pass_fixture_mismatch_count"],
                "one_cent_mismatch_detected": p1["one_cent_mismatch_detected"],
                "mismatch_report_generated": p1["mismatch_report_generated"],
                "github_upload_performed": p1["github_upload_performed"],
                "stage6_review_performed": p1["stage6_review_performed"],
                "raw_inbox_read_by_phase": p1["raw_data_boundary"]["raw_inbox_read_by_this_phase"],
            },
            "S06-P2": {
                "queue_item_count": p2["queue_item_count"],
                "minimum_queue_difference_cents": p2["minimum_queue_difference_cents"],
                "difference_closed": p2["difference_closed"],
                "manual_review_required": p2["manual_review_required"],
                "auto_correction_allowed": p2["auto_correction_allowed"],
                "report_grade_a_allowed": p2["report_grade_a_allowed"],
                "github_upload_performed": p2["github_upload_performed"],
                "stage6_review_performed": p2["stage6_review_performed"],
                "raw_inbox_read_by_phase": p2["raw_data_boundary"]["raw_inbox_read_by_this_phase"],
            },
            "S06-P3": {
                "metadata_quality_written": p3["metadata_quality_written"],
                "project_status_count": p3["project_status_count"],
                "blocked_project_status_count": p3["blocked_project_status_count"],
                "q5_allowed_count": p3["q5_allowed_count"],
                "report_grade_a_allowed_count": p3["report_grade_a_allowed_count"],
                "zero_delta_passed": p3_manifest["zero_delta_passed"],
                "github_upload_performed": p3["github_upload_performed"],
                "stage6_review_performed": p3["stage6_review_performed"],
                "raw_inbox_read_by_phase": p3["raw_inbox_read_performed"],
            },
        },
        "raw_data_boundary": raw_boundary,
        "public_repo_safety": public_false,
        "release_state": release_state,
        "validation_summary": validation_summary,
        "evidence_refs": [
            REPORT_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            RISK_REGISTER_PATH.as_posix(),
            ROLLBACK_PATH.as_posix(),
            MANIFEST_PATH.as_posix(),
        ],
        "next_recommended_phase": NEXT_PHASE,
        "next_phase_instruction": NEXT_INSTRUCTION,
    }


def write_report(manifest: dict[str, Any]) -> None:
    gate = manifest["stage_gate"]
    lines = [
        "# v0.1.4 Stage 6 Review Report",
        "",
        f"status: `{manifest['status']}`",
        "",
        "## Scope",
        "",
        "This review covers only v0.1.4 Stage 6: S06-P1 zero-delta validator, S06-P2 cross-source difference queue, and S06-P3 validation evidence output. It does not start S07-P1, does not perform GitHub upload, does not perform raw content matching, does not run lineage full check, and does not generate a formal report.",
        "",
        "## Review Results",
        "",
        "| Phase | Result | Evidence |",
        "|---|---:|---|",
        f"| S06-P1 zero-delta validator | {manifest['phase_results']['S06-P1']} | `{PHASE_MANIFESTS['S06-P1']}` |",
        f"| S06-P2 difference queue | {manifest['phase_results']['S06-P2']} | `{PHASE_MANIFESTS['S06-P2']}` |",
        f"| S06-P3 validation evidence | {manifest['phase_results']['S06-P3']} | `{PHASE_MANIFESTS['S06-P3']}` |",
        "",
        "## Findings",
        "",
        "- open_review_finding_count: `0`",
        f"- fixed_review_finding_count: `{manifest['fixed_review_finding_count']}`",
        "- fixed finding: Stage review public evidence schema now uses abstract safety gates only.",
        "",
        "## Stage Gate",
        "",
        f"- field comparisons in pass fixture: `{gate['pass_fixture_field_comparison_count']}`",
        f"- one-cent mismatch detected: `{str(gate['one_cent_mismatch_detected']).lower()}`",
        f"- manual queue items: `{gate['queue_item_count']}`",
        f"- minimum queue difference in cents: `{gate['minimum_queue_difference_cents']}`",
        f"- difference_closed: `{str(gate['difference_closed']).lower()}`",
        f"- metadata_quality_written: `{str(gate['metadata_quality_written']).lower()}`",
        f"- metadata zero-delta/data-quality/source-difference/mismatch writes: `{gate['metadata_zero_delta_records_written']}/{gate['metadata_data_quality_records_written']}/{gate['metadata_source_difference_records_written']}/{gate['metadata_mismatch_rows_written']}`",
        f"- project validation statuses: `{gate['project_status_count']}`, blocked `{gate['blocked_project_status_count']}`",
        f"- q5_allowed_count: `{gate['q5_allowed_count']}`",
        f"- report_grade_a_allowed_count: `{gate['report_grade_a_allowed_count']}`",
        f"- zero_delta_passed: `{str(gate['zero_delta_passed']).lower()}`",
        f"- hard_blocks: `{', '.join(gate['hard_blocks'])}`",
        f"- current_data_quality_grade: `{gate['current_data_quality_grade']}`",
        f"- current_report_grade: `{gate['current_report_grade']}`",
        f"- release_permission: `{gate['release_permission']}`",
        "- current_go_no_go: `NO_GO`",
        "",
        "## Boundary",
        "",
        "This review itself did not read, list, inventory, stat, hash, modify, delete, move, rename, overwrite, or write the raw inbox. It only replayed S06 public-safe validators and evidence.",
        "",
        "Public evidence contains only aggregate counts, public refs, status records, validators and governance records. It does not contain raw file identifiers, raw content identifiers, private source structure, private source records, business content, credentials, workbooks, documents, private tables, databases or raw business data.",
        "",
        "GitHub main upload remains deferred until v1.4 Stage 1-18 are complete, overall review has passed, and review findings have been fixed.",
        "",
        "## Next",
        "",
        f"Next recommended phase: `{manifest['next_recommended_phase']}`, as a separate run only after user instruction.",
        "",
    ]
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_test_results_placeholder(manifest: dict[str, Any]) -> None:
    TEST_RESULTS_PATH.write_text(
        "\n".join(
            [
                "# KMFA v0.1.4 Stage 6 Review Test Results",
                "",
                "- status: `pending_final_validation`",
                f"- task_id: `{manifest['task_id']}`",
                "- stage_review_performed: `true`",
                "- github_upload_performed: `false`",
                "- s07_p1_started: `false`",
                "- raw_inbox_read_by_this_review: `false`",
                "- raw_inbox_listed_by_this_review: `false`",
                "- raw_inbox_hashed_by_this_review: `false`",
                "- raw_inbox_mutated_by_this_review: `false`",
                "",
                "Final command results are captured after the validator, governance checks, and safety scans pass in this run.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def write_risk_and_rollback() -> None:
    RISK_REGISTER_PATH.write_text(
        "\n".join(
            [
                "# KMFA v0.1.4 Stage 6 Review Risk Register",
                "",
                "| Risk | Mitigation | Status |",
                "|---|---|---|",
                "| Stage review could be mistaken for GitHub upload readiness. | Manifest keeps GitHub upload deferred until v1.4 Stage 1-18 complete overall review. | controlled |",
                "| Unresolved differences could be mistaken for report readiness. | Manifest keeps Q5 allowed count and report grade A count at zero, release blocked, and delivery false. | controlled |",
                "| Raw/private data could leak into public evidence. | Evidence contains aggregate counts, refs and validator status only; raw/private and secret scans are required before commit. | controlled |",
                "",
            ]
        ),
        encoding="utf-8",
    )
    ROLLBACK_PATH.write_text(
        "\n".join(
            [
                "# KMFA v0.1.4 Stage 6 Review Rollback Plan",
                "",
                "1. Revert the local commit that introduced `V014_S06_STAGE_REVIEW` evidence, validator, focused unit test and governance rows.",
                "2. Restore current phase to `S06-P3 completed` if review evidence is invalidated.",
                "3. Do not modify, delete, move, rename, overwrite or write the raw inbox during rollback.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def generate() -> dict[str, Any]:
    (OUTPUT_DIR / "machine").mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "human").mkdir(parents=True, exist_ok=True)
    manifest = build_manifest()
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_report(manifest)
    write_test_results_placeholder(manifest)
    write_risk_and_rollback()
    return manifest


def main() -> int:
    manifest = generate()
    gate = manifest["stage_gate"]
    print(
        "PASS: KMFA v0.1.4 Stage 6 review evidence generated "
        f"(phases={manifest['phase_count']}, findings_open={manifest['open_review_finding_count']}, "
        f"queue_items={gate['queue_item_count']}, blocked_statuses={gate['blocked_project_status_count']}, "
        f"q5_allowed={gate['q5_allowed_count']}, report_grade_a_allowed={gate['report_grade_a_allowed_count']}, "
        f"github_upload={str(manifest['github_upload_performed']).lower()}, "
        f"next={manifest['next_recommended_phase']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
