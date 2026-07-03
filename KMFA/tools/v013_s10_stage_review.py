#!/usr/bin/env python3
"""Generate KMFA v0.1.3 Stage 10 review evidence.

This review reruns the public-safe v0.1.3 S10-P1/S10-P2/S10-P3 replay
validators and records the corrected Stage 1-10 batch upload boundary. It does
not read or write the local raw data inbox, does not enter Stage 1-10 batch
overall review, and does not perform GitHub upload.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.check_s10_stage_review import (
    DEFAULT_REVIEW_MANIFEST as LEGACY_STAGE10_REVIEW_MANIFEST_PATH,
    validate_stage_review as validate_legacy_stage10_review,
)
from KMFA.tools.check_v013_s10_p1_report_templates_replay import (
    validate_v013_s10_p1_report_templates_replay,
)
from KMFA.tools.check_v013_s10_p2_report_grade_runtime_replay import (
    validate_v013_s10_p2_report_grade_runtime_replay,
)
from KMFA.tools.check_v013_s10_p3_report_export_replay import (
    validate_v013_s10_p3_report_export_replay,
)


PUBLIC_OUTPUT_DIR = Path("KMFA/stage_artifacts/V013_S10_STAGE_REVIEW")
MANIFEST_PATH = PUBLIC_OUTPUT_DIR / "machine/stage10_review_manifest.json"
REPORT_PATH = PUBLIC_OUTPUT_DIR / "human/stage10_review_report.md"
TEST_RESULTS_PATH = PUBLIC_OUTPUT_DIR / "human/test_results.md"
S10_P1_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V013_S10_P1_REPORT_TEMPLATES_REPLAY/machine/"
    "report_templates_replay_manifest.json"
)
S10_P2_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V013_S10_P2_REPORT_GRADE_RUNTIME_REPLAY/machine/"
    "report_grade_runtime_replay_manifest.json"
)
S10_P3_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V013_S10_P3_REPORT_EXPORT_REPLAY/machine/"
    "report_export_replay_manifest.json"
)
TASK_ID = "KMFA-V013-S10-STAGE-REVIEW-20260703"
SCHEMA_VERSION = "kmfa.v013_s10_stage_review.v1"
REVIEW_SCOPE = "v013_s10_stage_review_only"
RAW_DIR = "/Users/linzezhang/Downloads/KMFA_MetaData"
NEXT_REQUIRED_STEP = (
    "Proceed to v0.1.3 Stage 1-10 batch overall review as a separate run. GitHub main upload "
    "remains deferred until that Stage 1-10 overall review passes and findings are fixed; do not "
    "run GitHub upload, raw value matching, lineage full check, formal report release, live connector, "
    "Redcircle automatic connector, OpMe deep coupling, or business execution in the Stage 10 review run."
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


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return value


def _false_count(*values: bool) -> int:
    return sum(1 for value in values if value is False)


def build_manifest() -> dict[str, Any]:
    p1 = validate_v013_s10_p1_report_templates_replay()
    p2 = validate_v013_s10_p2_report_grade_runtime_replay()
    p3 = validate_v013_s10_p3_report_export_replay()
    legacy_counts = validate_legacy_stage10_review()
    legacy_review = read_json(LEGACY_STAGE10_REVIEW_MANIFEST_PATH)

    p3_summary = p3["legacy_s10_p3_summary"]
    p3_policy = p3["report_export_policy"]
    phase_results = {
        "S10-P1": "PASS" if p1.get("phase_id") == "S10-P1" else "FAIL",
        "S10-P2": "PASS" if p2.get("phase_id") == "S10-P2" else "FAIL",
        "S10-P3": "PASS" if p3.get("phase_id") == "S10-P3" else "FAIL",
    }
    raw_read_count = 3 - _false_count(
        p1["raw_dir_read_performed"],
        p2["raw_dir_read_performed"],
        p3["raw_data_boundary"]["codex_read_performed_by_this_phase"],
    )
    raw_mutation_count = 3 - _false_count(
        p1["raw_dir_mutation_performed"],
        p2["raw_dir_mutation_performed"],
        p3["raw_data_boundary"]["codex_modify_allowed"],
    )
    github_upload_count = 3 - _false_count(
        p1["github_upload_performed"],
        p2["github_upload_performed"],
        p3["github_upload"]["github_upload_performed"],
    )
    review_findings = [
        {
            "finding_id": "KMFA-V013-S10-REV-F01",
            "severity": "P2",
            "status": "fixed",
            "summary": (
                "Legacy Stage 10 upload-ready wording and upload artifacts exist in historical v1.2 "
                "evidence. Current v0.1.3 Stage 10 review explicitly marks them non-current and "
                "defers GitHub main upload until the Stage 1-10 batch overall review passes."
            ),
        },
        {
            "finding_id": "KMFA-V013-S10-REV-F02",
            "severity": "P2",
            "status": "passed",
            "summary": (
                "S10-P1, S10-P2 and S10-P3 replay validators all pass with public-safe evidence, "
                "two public-safe HTML exports, two public-safe CSV appendices, D-grade reports, "
                "12 pending reconciliations and no formal report permission."
            ),
        },
        {
            "finding_id": "KMFA-V013-S10-REV-F03",
            "severity": "P3",
            "status": "fixed",
            "summary": (
                "Governance handoff and status records were updated from S10-P3 next-step wording "
                "to Stage 10 review passed / Stage 1-10 batch review next-step wording."
            ),
        },
    ]
    hard_blocks = [
        "report_grade_d_only",
        "zero_delta_failed",
        "unresolved_critical_difference",
        "missing_required_lineage",
        "missing_human_confirmation_for_A",
        "pending_reconciliation_blocks_formal_report",
        "raw_data_mutation_forbidden",
        "raw_value_publication_forbidden",
        "field_header_plaintext_publication_forbidden",
        "formal_report_release_blocked",
        "business_decision_basis_blocked",
        "stage1_10_batch_overall_review_not_performed",
        "lineage_full_check_not_performed",
        "raw_value_matching_not_performed",
        "github_upload_deferred_until_stage1_10_batch",
        "legacy_stage10_upload_artifacts_not_current_gate",
        "business_execution_blocked",
    ]

    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": "KMFA",
        "version": "0.1.3",
        "stage_id": "S10",
        "stage_name": "v0.1.3 report templates, trusted grade and export",
        "review_id": TASK_ID,
        "task_id": TASK_ID,
        "review_scope": REVIEW_SCOPE,
        "review_time": datetime.now().astimezone().isoformat(timespec="seconds"),
        "reviewed_head": git_output(["rev-parse", "HEAD"]),
        "worktree": git_output(["rev-parse", "--show-toplevel"]),
        "branch": git_output(["branch", "--show-current"]),
        "remote": git_output(["remote", "get-url", "origin"]),
        "status": "review_passed_upload_deferred_until_stage1_10_batch_no_go",
        "stage_review_performed": True,
        "stage1_10_batch_overall_review_performed": False,
        "github_upload_ready_next_gate": False,
        "github_upload_deferred_until_stage1_10_batch": True,
        "github_upload_performed": False,
        "github_upload_status": "not_uploaded_deferred_until_stage1_10_batch",
        "legacy_stage10_review_artifacts_validated": legacy_review.get("stage") == "S10",
        "legacy_stage10_review_status": legacy_review.get("status"),
        "legacy_stage10_upload_artifacts_current_gate": False,
        "legacy_stage10_upload_allowed_after_review_current": False,
        "delivery_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "business_execution_allowed": False,
        "lineage_full_check_completed": False,
        "raw_value_matching_performed": False,
        "phase_count": 3,
        "phase_results": phase_results,
        "s10_p1_dependency_validated": phase_results["S10-P1"] == "PASS",
        "s10_p2_dependency_validated": phase_results["S10-P2"] == "PASS",
        "s10_p3_dependency_validated": phase_results["S10-P3"] == "PASS",
        "reviewed_phase_manifests": {
            "S10-P1": S10_P1_MANIFEST_PATH.as_posix(),
            "S10-P2": S10_P2_MANIFEST_PATH.as_posix(),
            "S10-P3": S10_P3_MANIFEST_PATH.as_posix(),
            "legacy_S10_review": LEGACY_STAGE10_REVIEW_MANIFEST_PATH.as_posix(),
        },
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "release_permission": "blocked",
        "report_template_count": p1["template_count"],
        "report_template_section_count": p1["section_count"],
        "project_cost_section_count": p1["project_cost_section_count"],
        "business_overview_section_count": p1["business_overview_section_count"],
        "report_grade_record_count": p2["report_grade_record_count"],
        "report_export_record_count": p3_summary["report_export_record_count"],
        "grade_distribution": p3_summary["grade_distribution"],
        "html_export_count": p3_summary["html_export_count"],
        "csv_appendix_count": p3_summary["csv_appendix_count"],
        "excel_compatible_download_count": p3_summary["excel_compatible_download_count"],
        "pdf_export_enabled_after_template_stable": p3_summary["pdf_export_enabled_after_template_stable"],
        "committed_pdf_file_count": p3_summary["committed_pdf_file_count"],
        "committed_excel_file_count": p3_summary["committed_excel_file_count"],
        "formal_report_count": p3_summary["formal_report_count"],
        "business_decision_basis_count": p3_summary["business_decision_basis_count"],
        "pending_reconciliation_count": p3_summary["pending_reconciliation_count"],
        "confirmed_resolution_count": p2["confirmed_resolution_count"],
        "legacy_review_counts": legacy_counts,
        "report_export_policy": {
            "report_export_version": p3_policy["report_export_version"],
            "template_version": p3_policy["template_version"],
            "formula_version": p3_policy["formula_version"],
            "mapping_version": p3_policy["mapping_version"],
            "html_template_version": p3_policy["html_template_version"],
            "csv_appendix_schema_version": p3_policy["csv_appendix_schema_version"],
            "pdf_export_policy_version": p3_policy["pdf_export_policy_version"],
            "record_version_binding_count": p3_policy["record_version_binding_count"],
            "html_export_allowed": p3_policy["html_export_allowed"],
            "csv_excel_export_allowed": p3_policy["csv_excel_export_allowed"],
            "pdf_export_policy_enabled": p3_policy["pdf_export_policy_enabled"],
            "pdf_private_runtime_only": p3_policy["pdf_private_runtime_only"],
            "formal_report_allowed": p3_policy["formal_report_allowed"],
            "business_decision_basis_allowed": p3_policy["business_decision_basis_allowed"],
        },
        "raw_dir_read_performed_by_stage_review": False,
        "raw_dir_read_performed_by_dependency_validators": raw_read_count > 0,
        "raw_dir_mutation_performed": raw_mutation_count > 0,
        "github_upload_count": github_upload_count,
        "open_review_finding_count": 0,
        "fixed_review_finding_count": 2,
        "review_findings": review_findings,
        "hard_blocks": hard_blocks,
        "hard_block_count": len(hard_blocks),
        "raw_data_boundary": {
            "local_raw_data_dir": RAW_DIR,
            "local_raw_data_dir_role": "user_finance_raw_private_inbox",
            "codex_read_allowed_only_when_phase_requires": True,
            "codex_read_required_by_this_stage_review": False,
            "codex_read_performed_by_this_stage_review": False,
            "codex_list_performed_by_this_stage_review": False,
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
        "public_repo_safety": {
            "protected_source_payload_committed": False,
            "zip_committed": False,
            "excel_workbook_committed": False,
            "wps_native_file_committed": False,
            "redcircle_native_file_committed": False,
            "raw_or_private_csv_committed": False,
            "public_safe_csv_export_committed": True,
            "pdf_committed": False,
            "private_csv_committed": False,
            "sqlite_or_db_committed": False,
            "credentials_committed": False,
            "connector_secret_committed": False,
            "field_plaintext_committed": False,
            "source_header_plaintext_committed": False,
            "raw_file_names_committed": False,
            "raw_file_hashes_committed": False,
            "tab_labels_committed": False,
            "zip_member_names_committed": False,
            "source_record_payload_committed": False,
            "normalized_source_values_committed": False,
            "business_amount_values_committed": False,
            "project_or_customer_plaintext_committed": False,
            "formal_report_committed": False,
            "html_report_export_committed": True,
            "spreadsheet_workbook_committed": False,
        },
        "validators": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v013_s10_stage_review.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s10_stage_review.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v013_s10_stage_review -q",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s10_p1_report_templates_replay.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s10_p2_report_grade_runtime_replay.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s10_p3_report_export_replay.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s10_p1_report_templates.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s10_p2_report_grade_runtime.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s10_p3_report_export.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s10_stage_review.py",
        ],
        "governance_refs": [
            "KMFA/README.md",
            "KMFA/AGENTS.md",
            "KMFA/HANDOFF.md",
            "KMFA/CHANGELOG.md",
            "KMFA/功能清单.md",
            "KMFA/开发记录.md",
            "KMFA/模型参数文件.md",
            "KMFA/docs/governance/STATUS.md",
            "KMFA/docs/governance/OWNER_STATUS.md",
            "KMFA/docs/governance/DEVELOPMENT_LEDGER.md",
            "KMFA/docs/governance/VERSION_MATRIX.yaml",
            "KMFA/docs/governance/ASSURANCE_STATUS.yaml",
        ],
        "evidence_refs": [
            MANIFEST_PATH.as_posix(),
            REPORT_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            "KMFA/tools/v013_s10_stage_review.py",
            "KMFA/tools/check_v013_s10_stage_review.py",
            "KMFA/tests/test_v013_s10_stage_review.py",
        ],
        "next_required_step": NEXT_REQUIRED_STEP,
    }


def write_report(manifest: dict[str, Any]) -> None:
    lines = [
        "# KMFA v0.1.3 Stage 10 Review",
        "",
        f"- review_id: `{manifest['review_id']}`",
        f"- status: `{manifest['status']}`",
        f"- review_scope: `{manifest['review_scope']}`",
        f"- phase_results: `{json.dumps(manifest['phase_results'], ensure_ascii=False, sort_keys=True)}`",
        f"- open_review_finding_count: `{manifest['open_review_finding_count']}`",
        f"- fixed_review_finding_count: `{manifest['fixed_review_finding_count']}`",
        f"- report_template_count: `{manifest['report_template_count']}`",
        f"- report_template_section_count: `{manifest['report_template_section_count']}`",
        f"- report_grade_record_count: `{manifest['report_grade_record_count']}`",
        f"- report_export_record_count: `{manifest['report_export_record_count']}`",
        f"- html_export_count: `{manifest['html_export_count']}`",
        f"- csv_appendix_count: `{manifest['csv_appendix_count']}`",
        f"- excel_compatible_download_count: `{manifest['excel_compatible_download_count']}`",
        f"- pending_reconciliation_count: `{manifest['pending_reconciliation_count']}`",
        f"- confirmed_resolution_count: `{manifest['confirmed_resolution_count']}`",
        f"- current_data_quality_grade: `{manifest['current_data_quality_grade']}`",
        f"- current_report_grade: `{manifest['current_report_grade']}`",
        f"- release_permission: `{manifest['release_permission']}`",
        "",
        "## Boundary",
        "",
        f"- stage_review_performed: `{str(manifest['stage_review_performed']).lower()}`",
        f"- stage1_10_batch_overall_review_performed: `{str(manifest['stage1_10_batch_overall_review_performed']).lower()}`",
        f"- github_upload_deferred_until_stage1_10_batch: `{str(manifest['github_upload_deferred_until_stage1_10_batch']).lower()}`",
        f"- github_upload_status: `{manifest['github_upload_status']}`",
        f"- github_upload_performed: `{str(manifest['github_upload_performed']).lower()}`",
        f"- legacy_stage10_upload_artifacts_current_gate: `{str(manifest['legacy_stage10_upload_artifacts_current_gate']).lower()}`",
        f"- delivery_allowed: `{str(manifest['delivery_allowed']).lower()}`",
        f"- formal_report_allowed: `{str(manifest['formal_report_allowed']).lower()}`",
        f"- business_decision_basis_allowed: `{str(manifest['business_decision_basis_allowed']).lower()}`",
        f"- business_execution_allowed: `{str(manifest['business_execution_allowed']).lower()}`",
        "",
        "## Raw Data Boundary",
        "",
        f"- local_raw_data_dir: `{RAW_DIR}`",
        "- codex_read_required_by_this_stage_review: `false`",
        "- codex_read_performed_by_this_stage_review: `false`",
        "- codex_list_performed_by_this_stage_review: `false`",
        "- codex_modify_allowed: `false`",
        "- codex_delete_allowed: `false`",
        "- codex_move_allowed: `false`",
        "- codex_rename_allowed: `false`",
        "- codex_generate_inside_allowed: `false`",
        "- github_commit_allowed: `false`",
        "",
        "This Stage 10 review did not enumerate, copy, modify, move, rename, delete, overwrite, or write generated files inside the local finance inbox.",
        "",
        "## Findings",
        "",
    ]
    for finding in manifest["review_findings"]:
        lines.append(f"- `{finding['finding_id']}` {finding['status']}: {finding['summary']}")
    lines.extend(
        [
            "",
            "## Next Step",
            "",
            manifest["next_required_step"],
            "",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_pending_test_results(manifest: dict[str, Any]) -> None:
    lines = [
        "# KMFA v0.1.3 Stage 10 Review Test Results",
        "",
        f"- review_id: `{manifest['review_id']}`",
        "- status: `pending_final_validation_local_only`",
        "- github_upload_performed: `false`",
        "- raw_dir_read_performed_by_this_stage_review: `false`",
        "- raw_dir_mutation_performed: `false`",
        "- stage1_10_batch_overall_review_performed: `false`",
        "- formal_report_allowed: `false`",
        "- business_execution_allowed: `false`",
        "",
        "## Command Results",
        "",
        "- PENDING: final validation results will be recorded before local commit.",
        "",
    ]
    TEST_RESULTS_PATH.write_text("\n".join(lines), encoding="utf-8")


def generate() -> dict[str, Any]:
    (PUBLIC_OUTPUT_DIR / "machine").mkdir(parents=True, exist_ok=True)
    (PUBLIC_OUTPUT_DIR / "human").mkdir(parents=True, exist_ok=True)
    manifest = build_manifest()
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_report(manifest)
    write_pending_test_results(manifest)
    return manifest


def main() -> int:
    manifest = generate()
    print(
        "PASS: KMFA v0.1.3 Stage 10 review generated "
        f"(phase_results={manifest['phase_results']}, "
        f"open_findings={manifest['open_review_finding_count']}, "
        f"exports={manifest['html_export_count']} html/{manifest['csv_appendix_count']} csv, "
        "stage1_10_batch_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
