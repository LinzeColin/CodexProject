#!/usr/bin/env python3
"""Generate KMFA v0.1.3 S10-P1 report templates replay evidence.

This replay validates the v0.1.3 Stage 9 review dependency, reuses the
public-safe legacy S10-P1 report template artifacts, and records the
phase-level no-go / upload-deferred boundary for the v0.1.3 Stage 1-10 run.
It does not generate report exports or formal reports.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.check_v013_s09_stage_review import validate_v013_s09_stage_review
from KMFA.tools.report_templates import (
    DEFAULT_OUTPUT_MANIFEST as LEGACY_TEMPLATE_MANIFEST_PATH,
    DEFAULT_OUTPUT_SECTIONS as LEGACY_TEMPLATE_SECTIONS_PATH,
    DEFAULT_OUTPUT_STAGE_MANIFEST as LEGACY_STAGE_MANIFEST_PATH,
    DEFAULT_OUTPUT_TEMPLATES as LEGACY_TEMPLATES_PATH,
    REQUIRED_BUSINESS_OVERVIEW_SECTION_TITLES,
    REQUIRED_PROJECT_COST_SECTION_TITLES,
    REQUIRED_TEMPLATE_IDS,
    read_json,
    read_jsonl,
    validate_report_template_artifacts,
)


PUBLIC_OUTPUT_DIR = Path("KMFA/stage_artifacts/V013_S10_P1_REPORT_TEMPLATES_REPLAY")
MANIFEST_PATH = PUBLIC_OUTPUT_DIR / "machine/report_templates_replay_manifest.json"
REPORT_PATH = PUBLIC_OUTPUT_DIR / "human/report_templates_replay_report.md"
TEST_RESULTS_PATH = PUBLIC_OUTPUT_DIR / "human/test_results.md"
TASK_ID = "KMFA-V013-S10-P1-REPORT-TEMPLATES-REPLAY-20260703"
SCHEMA_VERSION = "kmfa.v013_s10_p1_report_templates_replay.v1"
PHASE_SCOPE = "v013_s10_p1_report_templates_replay_only"
RAW_DIR = "/Users/linzezhang/Downloads/KMFA_MetaData"
NEXT_REQUIRED_STEP = (
    "Proceed to v0.1.3 S10-P2 as a separate run. GitHub main upload remains deferred until "
    "v0.1.3 Stages 1-10 are complete, the whole Stage 1-10 review passes, and findings are fixed; "
    "do not run S10-P3, Stage 10 review, GitHub upload, raw value matching, lineage full check, "
    "formal report release, live connector, Redcircle automatic connector, or business execution "
    "in the S10-P1 run."
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


def validate_stage9_dependency() -> dict[str, Any]:
    result = validate_v013_s09_stage_review()
    if result.get("stage_id") != "S09":
        raise RuntimeError("v0.1.3 S10-P1 requires validated Stage 9 review dependency")
    if result.get("review_scope") != "v013_s09_stage_review_only":
        raise RuntimeError("v0.1.3 S10-P1 requires v0.1.3 Stage 9 review scope")
    if result.get("s10_p1_performed") is not False:
        raise RuntimeError("Stage 9 review dependency must not already include S10-P1")
    if result.get("github_upload_performed") is not False:
        raise RuntimeError("Stage 9 review dependency must not include GitHub upload")
    if result.get("github_upload_deferred_until_stage10_batch") is not True:
        raise RuntimeError("Stage 9 review dependency must keep upload deferred")
    return result


def _count_false_values(container: dict[str, Any]) -> int:
    return sum(1 for value in container.values() if value is False)


def _repo_relative(path: Path) -> str:
    try:
        return path.relative_to(Path.cwd()).as_posix()
    except ValueError:
        return path.as_posix()


def validate_legacy_s10_p1_artifacts() -> dict[str, Any]:
    legacy_manifest = read_json(LEGACY_TEMPLATE_MANIFEST_PATH)
    templates = read_jsonl(LEGACY_TEMPLATES_PATH)
    sections = read_jsonl(LEGACY_TEMPLATE_SECTIONS_PATH)
    legacy_stage_manifest = read_json(LEGACY_STAGE_MANIFEST_PATH)
    validate_report_template_artifacts(legacy_manifest, templates, sections)

    quality_gate = legacy_manifest.get("quality_gate", {})
    stage_scope = legacy_manifest.get("stage_scope", {})
    public_safety = legacy_manifest.get("public_repo_safety", {})
    summary = legacy_manifest.get("summary", {})
    project_cost_sections = [
        section
        for section in sections
        if section.get("template_id") == "project_cost_special_report"
    ]
    business_overview_sections = [
        section
        for section in sections
        if section.get("template_id") == "business_overview_report"
    ]
    internal_title_visible_count = sum(
        1 for section in sections if section.get("internal_technical_title_visible") is True
    )
    raw_business_values_allowed_count = sum(
        1 for section in sections if section.get("raw_business_values_allowed") is True
    )
    public_numeric_values_allowed_count = sum(
        1 for section in sections if section.get("public_numeric_values_allowed") is True
    )
    formal_report_allowed_count = sum(
        1 for template in templates if template.get("formal_report_allowed") is True
    )
    trusted_grade_assignment_allowed_count = sum(
        1 for template in templates if template.get("trusted_grade_assignment_allowed") is True
    )
    report_runtime_scope_count = sum(
        1 for template in templates if template.get("report_runtime_scope_included") is True
    )
    s10_p2_scope_count = sum(1 for template in templates if template.get("s10_p2_scope_included") is True)
    s10_p3_scope_count = sum(1 for template in templates if template.get("s10_p3_scope_included") is True)
    ui_scope_count = sum(1 for template in templates if template.get("ui_scope_included") is True)
    external_connector_scope_count = sum(
        1 for template in templates if template.get("external_connector_included") is True
    )

    return {
        "legacy_manifest": legacy_manifest,
        "legacy_stage_manifest": legacy_stage_manifest,
        "template_count": len(templates),
        "section_count": len(sections),
        "project_cost_section_count": len(project_cost_sections),
        "business_overview_section_count": len(business_overview_sections),
        "required_template_ids": list(REQUIRED_TEMPLATE_IDS),
        "required_project_cost_section_titles": list(REQUIRED_PROJECT_COST_SECTION_TITLES),
        "required_business_overview_section_titles": list(REQUIRED_BUSINESS_OVERVIEW_SECTION_TITLES),
        "pending_reconciliation_count": summary.get("pending_reconciliation_count"),
        "formal_report_count": summary.get("formal_report_count"),
        "export_artifact_count": summary.get("export_artifact_count"),
        "template_status": legacy_manifest.get("template_status"),
        "template_version": legacy_manifest.get("template_version"),
        "mapping_version": legacy_manifest.get("mapping_version"),
        "formula_version": legacy_manifest.get("formula_version"),
        "content_hash": legacy_manifest.get("content_hash"),
        "formal_report_allowed_count": formal_report_allowed_count,
        "trusted_grade_assignment_allowed_count": trusted_grade_assignment_allowed_count,
        "report_runtime_scope_count": report_runtime_scope_count,
        "s10_p2_scope_count": s10_p2_scope_count,
        "s10_p3_scope_count": s10_p3_scope_count,
        "ui_scope_count": ui_scope_count,
        "external_connector_scope_count": external_connector_scope_count,
        "internal_title_visible_count": internal_title_visible_count,
        "raw_business_values_allowed_count": raw_business_values_allowed_count,
        "public_numeric_values_allowed_count": public_numeric_values_allowed_count,
        "quality_gate": quality_gate,
        "stage_scope": stage_scope,
        "public_repo_safety": public_safety,
        "quality_gate_false_count": _count_false_values(quality_gate),
        "stage_scope_false_count": _count_false_values(stage_scope),
        "public_safety_false_count": _count_false_values(public_safety),
        "artifact_refs": {
            "legacy_manifest": _repo_relative(LEGACY_TEMPLATE_MANIFEST_PATH),
            "legacy_templates": _repo_relative(LEGACY_TEMPLATES_PATH),
            "legacy_sections": _repo_relative(LEGACY_TEMPLATE_SECTIONS_PATH),
            "legacy_stage_manifest": _repo_relative(LEGACY_STAGE_MANIFEST_PATH),
        },
    }


def build_manifest() -> dict[str, Any]:
    s09 = validate_stage9_dependency()
    legacy = validate_legacy_s10_p1_artifacts()
    hard_blocks = [
        "raw_data_mutation_forbidden",
        "raw_value_publication_forbidden",
        "field_header_plaintext_publication_forbidden",
        "report_templates_structural_only",
        "report_runtime_not_performed",
        "trusted_grade_assignment_blocked",
        "s10_p2_report_grade_runtime_not_performed",
        "s10_p3_report_export_not_performed",
        "stage10_review_not_performed",
        "formal_report_release_blocked",
        "lineage_full_check_not_performed",
        "raw_value_matching_not_performed",
        "github_upload_deferred_until_stage10_batch",
        "business_execution_blocked",
    ]

    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": "KMFA",
        "version": "0.1.3",
        "stage_id": "S10",
        "phase_id": "S10-P1",
        "phase_name": "v0.1.3 public-safe report templates replay",
        "task_id": TASK_ID,
        "phase_scope": PHASE_SCOPE,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "reviewed_head": git_output(["rev-parse", "HEAD"]),
        "worktree": git_output(["rev-parse", "--show-toplevel"]),
        "branch": git_output(["branch", "--show-current"]),
        "remote": git_output(["remote", "get-url", "origin"]),
        "status": "completed_validated_local_only_no_go_upload_deferred_report_templates_replayed",
        "completed_task_ids": ["S10PAT01", "S10PAT02", "S10PAT03"],
        "acceptance_ids": ["ACC-V013-S10-P1-REPORT-TEMPLATES-REPLAY"],
        "s09_stage_review_dependency_validated": True,
        "s09_stage_review_status": s09.get("status", "review_passed_upload_deferred_until_stage10_batch_no_go"),
        "legacy_s10_p1_dependency_validated": True,
        "stage10_phase_progress": {
            "completed_phase_count": 1,
            "total_phase_count": 3,
            "derived_percent_bps": 3333,
            "derived_percent_label": "33.33%",
            "s10_p1_performed": True,
            "s10_p2_performed": False,
            "s10_p3_performed": False,
            "stage10_review_performed": False,
        },
        "legacy_s10_p1_summary": {
            "template_count": legacy["template_count"],
            "section_count": legacy["section_count"],
            "project_cost_section_count": legacy["project_cost_section_count"],
            "business_overview_section_count": legacy["business_overview_section_count"],
            "required_template_ids": legacy["required_template_ids"],
            "required_project_cost_section_titles": legacy["required_project_cost_section_titles"],
            "required_business_overview_section_titles": legacy["required_business_overview_section_titles"],
            "pending_reconciliation_count": legacy["pending_reconciliation_count"],
            "formal_report_count": legacy["formal_report_count"],
            "export_artifact_count": legacy["export_artifact_count"],
            "template_status": legacy["template_status"],
        },
        "report_template_policy": {
            "template_version": legacy["template_version"],
            "mapping_version": legacy["mapping_version"],
            "formula_version": legacy["formula_version"],
            "content_hash": legacy["content_hash"],
            "formal_report_allowed": False,
            "formal_report_allowed_count": legacy["formal_report_allowed_count"],
            "trusted_grade_assignment_allowed": False,
            "trusted_grade_assignment_allowed_count": legacy["trusted_grade_assignment_allowed_count"],
            "report_runtime_scope_count": legacy["report_runtime_scope_count"],
            "s10_p2_scope_count": legacy["s10_p2_scope_count"],
            "s10_p3_scope_count": legacy["s10_p3_scope_count"],
            "ui_scope_count": legacy["ui_scope_count"],
            "external_connector_scope_count": legacy["external_connector_scope_count"],
            "internal_title_visible_count": legacy["internal_title_visible_count"],
            "raw_business_values_allowed_count": legacy["raw_business_values_allowed_count"],
            "public_numeric_values_allowed_count": legacy["public_numeric_values_allowed_count"],
            "quality_gate_false_count": legacy["quality_gate_false_count"],
            "stage_scope_false_count": legacy["stage_scope_false_count"],
            "public_safety_false_count": legacy["public_safety_false_count"],
        },
        "phase_boundaries": {
            "s10_p1_report_templates_scope_included": True,
            "s10_p2_report_grade_runtime_scope_included": False,
            "s10_p3_report_export_scope_included": False,
            "stage10_review_scope_included": False,
            "lineage_full_check_scope_included": False,
            "formal_report_scope_included": False,
            "ui_scope_included": False,
            "external_connector_scope_included": False,
            "github_upload_scope_included": False,
        },
        "quality_gate": {
            "current_data_quality_grade": "Q4",
            "current_report_grade": "D",
            "release_permission": "blocked",
            "formal_report_allowed": False,
            "formal_report_allowed_count": 0,
            "trusted_grade_assignment_allowed": False,
            "business_decision_basis_allowed": False,
            "business_execution_allowed": False,
            "delivery_allowed": False,
            "raw_layer_write_allowed": False,
            "automatic_external_action_allowed": False,
            "pending_reconciliation_count": legacy["pending_reconciliation_count"],
        },
        "github_upload": {
            "github_upload_ready_next_gate": False,
            "github_upload_deferred_until_stage10_batch": True,
            "github_upload_performed": False,
            "github_upload_status": "not_uploaded_deferred_until_stage10_batch",
        },
        "raw_data_boundary": {
            "local_raw_data_dir": RAW_DIR,
            "local_raw_data_dir_role": "user_finance_raw_private_inbox",
            "codex_read_allowed_only_when_phase_requires": True,
            "codex_read_required_by_this_phase": False,
            "codex_read_performed_by_this_phase": False,
            "codex_list_performed_by_this_phase": False,
            "codex_modify_allowed": False,
            "codex_delete_allowed": False,
            "codex_move_allowed": False,
            "codex_rename_allowed": False,
            "codex_overwrite_allowed": False,
            "codex_generate_inside_allowed": False,
            "codex_create_extra_files_inside_allowed": False,
            "github_commit_allowed": False,
            "private_runtime_output_dir": "KMFA/.codex_private_runtime/",
        },
        "public_repo_safety": {
            "protected_source_payload_committed": False,
            "zip_committed": False,
            "excel_workbook_committed": False,
            "wps_native_file_committed": False,
            "redcircle_native_file_committed": False,
            "csv_committed": False,
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
            "report_export_committed": False,
            "html_report_export_committed": False,
            "spreadsheet_report_export_committed": False,
        },
        "hard_blocks": hard_blocks,
        "hard_block_count": len(hard_blocks),
        "artifact_refs": {
            **legacy["artifact_refs"],
            "manifest": MANIFEST_PATH.as_posix(),
            "report": REPORT_PATH.as_posix(),
            "test_results": TEST_RESULTS_PATH.as_posix(),
            "generator": "KMFA/tools/v013_s10_p1_report_templates_replay.py",
            "validator": "KMFA/tools/check_v013_s10_p1_report_templates_replay.py",
            "unit_test": "KMFA/tests/test_v013_s10_p1_report_templates_replay.py",
        },
        "validators": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v013_s10_p1_report_templates_replay.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s10_p1_report_templates_replay.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v013_s10_p1_report_templates_replay -q",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s10_p1_report_templates.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_report_templates -q",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s09_stage_review.py",
        ],
        "evidence_refs": [
            MANIFEST_PATH.as_posix(),
            REPORT_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            "KMFA/tools/v013_s10_p1_report_templates_replay.py",
            "KMFA/tools/check_v013_s10_p1_report_templates_replay.py",
            "KMFA/tests/test_v013_s10_p1_report_templates_replay.py",
        ],
        "next_required_step": NEXT_REQUIRED_STEP,
    }


def write_report(manifest: dict[str, Any]) -> None:
    summary = manifest["legacy_s10_p1_summary"]
    policy = manifest["report_template_policy"]
    lines = [
        "# KMFA v0.1.3 S10-P1 Report Templates Replay",
        "",
        f"- task_id: `{manifest['task_id']}`",
        f"- status: `{manifest['status']}`",
        f"- phase_scope: `{manifest['phase_scope']}`",
        "- dependency: `v0.1.3 Stage 9 review PASS`",
        "- legacy_s10_p1_dependency_validated: `true`",
        f"- template_count: `{summary['template_count']}`",
        f"- section_count: `{summary['section_count']}`",
        f"- project_cost_section_count: `{summary['project_cost_section_count']}`",
        f"- business_overview_section_count: `{summary['business_overview_section_count']}`",
        f"- pending_reconciliation_count: `{summary['pending_reconciliation_count']}`",
        f"- formal_report_count: `{summary['formal_report_count']}`",
        f"- export_artifact_count: `{summary['export_artifact_count']}`",
        f"- template_status: `{summary['template_status']}`",
        f"- formal_report_allowed_count: `{policy['formal_report_allowed_count']}`",
        f"- trusted_grade_assignment_allowed_count: `{policy['trusted_grade_assignment_allowed_count']}`",
        f"- report_runtime_scope_count: `{policy['report_runtime_scope_count']}`",
        f"- s10_p2_scope_count: `{policy['s10_p2_scope_count']}`",
        f"- s10_p3_scope_count: `{policy['s10_p3_scope_count']}`",
        f"- internal_title_visible_count: `{policy['internal_title_visible_count']}`",
        f"- raw_business_values_allowed_count: `{policy['raw_business_values_allowed_count']}`",
        f"- public_numeric_values_allowed_count: `{policy['public_numeric_values_allowed_count']}`",
        "",
        "## Boundary",
        "",
        "- s10_p1_report_templates_scope_included: `true`",
        "- s10_p2_report_grade_runtime_scope_included: `false`",
        "- s10_p3_report_export_scope_included: `false`",
        "- stage10_review_scope_included: `false`",
        "- github_upload_deferred_until_stage10_batch: `true`",
        "- github_upload_performed: `false`",
        "- formal_report_allowed: `false`",
        "- trusted_grade_assignment_allowed: `false`",
        "- business_decision_basis_allowed: `false`",
        "- business_execution_allowed: `false`",
        "",
        "## Raw Data Boundary",
        "",
        f"- local_raw_data_dir: `{RAW_DIR}`",
        "- local_raw_data_dir_role: `user_finance_raw_private_inbox`",
        "- codex_read_required_by_this_phase: `false`",
        "- codex_read_performed_by_this_phase: `false`",
        "- codex_list_performed_by_this_phase: `false`",
        "- codex_modify_allowed: `false`",
        "- codex_delete_allowed: `false`",
        "- codex_move_allowed: `false`",
        "- codex_rename_allowed: `false`",
        "- codex_generate_inside_allowed: `false`",
        "- codex_create_extra_files_inside_allowed: `false`",
        "- github_commit_allowed: `false`",
        "",
        (
            "This phase did not enumerate, copy, modify, move, rename, delete, overwrite, "
            "or write generated files inside the local finance inbox. It only replayed "
            "public-safe report template structure already present in the repository."
        ),
        "",
        "## Public Safety",
        "",
        (
            "Evidence contains only template identifiers, management-readable section titles, "
            "aggregate counts, validator references, quality blockers, and governance paths."
        ),
        (
            "It does not contain source filenames, source hashes from the private inbox, tab labels, "
            "ZIP member names, field/header plaintext, row values, business amount values, credentials, "
            "contracts, payroll, tax filings, or bank statements."
        ),
        "",
        "## Next Step",
        "",
        manifest["next_required_step"],
        "",
    ]
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_test_results() -> None:
    lines = [
        "# KMFA v0.1.3 S10-P1 Report Templates Replay Test Results",
        "",
        f"- task_id: `{TASK_ID}`",
        "- status: `pending_final_validation_local_only`",
        "- github_upload_performed: `false`",
        "- raw_dir_read_performed_by_this_phase: `false`",
        "- raw_dir_mutation_performed: `false`",
        "- s10_p2_performed: `false`",
        "- s10_p3_performed: `false`",
        "- stage10_review_performed: `false`",
        "- raw_value_matching_performed: `false`",
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
    write_test_results()
    return manifest


def main() -> int:
    manifest = generate()
    summary = manifest["legacy_s10_p1_summary"]
    print(
        "PASS: KMFA v0.1.3 S10-P1 report templates replay generated "
        f"(templates={summary['template_count']}, sections={summary['section_count']}, "
        f"project_cost_sections={summary['project_cost_section_count']}, "
        f"business_overview_sections={summary['business_overview_section_count']}, "
        "s10p2=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
