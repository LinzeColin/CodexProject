#!/usr/bin/env python3
"""Generate KMFA v0.1.3 S10-P3 report export replay evidence.

This replay validates the v0.1.3 S10-P2 dependency, reuses the existing
public-safe S10-P3 report export artifacts, and records the phase-level
no-go / upload-deferred boundary for the v0.1.3 Stage 1-10 run. It does not
run Stage 10 review, publish formal reports, or upload to GitHub.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.check_v013_s10_p2_report_grade_runtime_replay import (
    validate_v013_s10_p2_report_grade_runtime_replay,
)
from KMFA.tools.report_export_runtime import (
    CSV_APPENDIX_SCHEMA_VERSION,
    DEFAULT_CSV_OUTPUT_DIR as LEGACY_CSV_OUTPUT_DIR,
    DEFAULT_HTML_OUTPUT_DIR as LEGACY_HTML_OUTPUT_DIR,
    DEFAULT_OUTPUT_MANIFEST as LEGACY_EXPORT_MANIFEST_PATH,
    DEFAULT_OUTPUT_RECORDS as LEGACY_EXPORT_RECORDS_PATH,
    DEFAULT_OUTPUT_STAGE_MANIFEST as LEGACY_STAGE_MANIFEST_PATH,
    EXPORT_RECORD_VERSION,
    FORMULA_VERSION,
    HTML_TEMPLATE_VERSION,
    MAPPING_VERSION,
    PDF_EXPORT_POLICY_VERSION,
    REQUIRED_TEMPLATE_IDS,
    read_json,
    read_jsonl,
    validate_report_export_artifacts,
)


PUBLIC_OUTPUT_DIR = Path("KMFA/stage_artifacts/V013_S10_P3_REPORT_EXPORT_REPLAY")
MANIFEST_PATH = PUBLIC_OUTPUT_DIR / "machine/report_export_replay_manifest.json"
REPORT_PATH = PUBLIC_OUTPUT_DIR / "human/report_export_replay_report.md"
TEST_RESULTS_PATH = PUBLIC_OUTPUT_DIR / "human/test_results.md"
TASK_ID = "KMFA-V013-S10-P3-REPORT-EXPORT-REPLAY-20260703"
SCHEMA_VERSION = "kmfa.v013_s10_p3_report_export_replay.v1"
PHASE_SCOPE = "v013_s10_p3_report_export_replay_only"
RAW_DIR = "/Users/linzezhang/Downloads/KMFA_MetaData"
NEXT_REQUIRED_STEP = (
    "Proceed to v0.1.3 Stage 10 review as a separate run. GitHub main upload remains deferred "
    "until v0.1.3 Stages 1-10 are complete, the whole Stage 1-10 review passes, and findings are "
    "fixed; do not run GitHub upload, raw value matching, lineage full check, formal report release, "
    "live connector, Redcircle automatic connector, OpMe deep coupling, or business execution in the "
    "S10-P3 run."
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


def _repo_relative(path: Path) -> str:
    try:
        return path.relative_to(Path.cwd()).as_posix()
    except ValueError:
        return path.as_posix()


def _count_false_values(container: dict[str, Any]) -> int:
    return sum(1 for value in container.values() if value is False)


def _record_version_binding_count(records: list[dict[str, Any]], legacy_manifest: dict[str, Any]) -> int:
    version_fields = (
        "report_export_version",
        "formula_version",
        "mapping_version",
        "html_template_version",
        "csv_appendix_schema_version",
        "pdf_export_policy_version",
    )
    return sum(
        1
        for record in records
        if all(record.get(field) == legacy_manifest.get(field) for field in version_fields)
        and record.get("template_content_hash") == legacy_manifest.get("upstream_template_content_hash")
        and record.get("grade_runtime_content_hash") == legacy_manifest.get("grade_runtime_content_hash")
    )


def _read_render_outputs() -> dict[str, dict[str, str]]:
    return {
        "html": {
            template_id: (LEGACY_HTML_OUTPUT_DIR / f"{template_id}.html").read_text(encoding="utf-8")
            for template_id in REQUIRED_TEMPLATE_IDS
        },
        "csv": {
            template_id: (LEGACY_CSV_OUTPUT_DIR / f"{template_id}_appendix.csv").read_text(encoding="utf-8")
            for template_id in REQUIRED_TEMPLATE_IDS
        },
    }


def validate_s10_p2_dependency() -> dict[str, Any]:
    result = validate_v013_s10_p2_report_grade_runtime_replay()
    if result.get("stage_id") != "S10" or result.get("phase_id") != "S10-P2":
        raise RuntimeError("v0.1.3 S10-P3 requires validated S10-P2 dependency")
    if result.get("phase_scope") != "v013_s10_p2_report_grade_runtime_replay_only":
        raise RuntimeError("v0.1.3 S10-P3 requires v0.1.3 S10-P2 replay scope")
    if result.get("s10_p3_performed") is not False:
        raise RuntimeError("S10-P2 dependency must not already include S10-P3")
    if result.get("stage10_review_performed") is not False:
        raise RuntimeError("S10-P2 dependency must not include Stage 10 review")
    if result.get("github_upload_performed") is not False:
        raise RuntimeError("S10-P2 dependency must not include GitHub upload")
    if result.get("github_upload_deferred_until_stage10_batch") is not True:
        raise RuntimeError("S10-P2 dependency must keep upload deferred")
    return result


def validate_legacy_s10_p3_artifacts() -> dict[str, Any]:
    legacy_manifest = read_json(LEGACY_EXPORT_MANIFEST_PATH)
    records = read_jsonl(LEGACY_EXPORT_RECORDS_PATH)
    render_outputs = _read_render_outputs()
    legacy_stage_manifest = read_json(LEGACY_STAGE_MANIFEST_PATH)
    validate_report_export_artifacts(legacy_manifest, records, render_outputs)

    summary = legacy_manifest.get("summary", {})
    quality_gate = legacy_manifest.get("quality_gate", {})
    stage_scope = legacy_manifest.get("stage_scope", {})
    public_safety = legacy_manifest.get("public_repo_safety", {})
    html_output_paths = [
        LEGACY_HTML_OUTPUT_DIR / f"{template_id}.html"
        for template_id in REQUIRED_TEMPLATE_IDS
    ]
    csv_output_paths = [
        LEGACY_CSV_OUTPUT_DIR / f"{template_id}_appendix.csv"
        for template_id in REQUIRED_TEMPLATE_IDS
    ]
    inherits_blue_business_sample_count = sum(
        1
        for record in records
        if record.get("export_formats", {}).get("html_report", {}).get("inherits_blue_business_sample") is True
    )
    pdf_private_runtime_only_count = sum(
        1
        for record in records
        if record.get("export_formats", {}).get("pdf_report", {}).get("private_runtime_only") is True
    )
    excel_compatible_csv_count = sum(
        1
        for record in records
        if record.get("export_formats", {}).get("excel_appendix", {}).get("download_mode")
        == "excel_compatible_csv"
    )
    committed_excel_workbook_count = sum(
        1
        for record in records
        if record.get("export_formats", {}).get("excel_appendix", {}).get("committed_artifact_path")
    )
    committed_pdf_file_count = sum(
        1
        for record in records
        if record.get("export_formats", {}).get("pdf_report", {}).get("committed_artifact_path")
    )

    return {
        "legacy_manifest": legacy_manifest,
        "legacy_stage_manifest": legacy_stage_manifest,
        "records": records,
        "render_outputs": render_outputs,
        "template_count": summary.get("template_count"),
        "report_export_record_count": summary.get("report_export_record_count"),
        "grade_distribution": summary.get("grade_distribution"),
        "html_export_count": summary.get("html_export_count"),
        "csv_appendix_count": summary.get("csv_appendix_count"),
        "excel_compatible_download_count": summary.get("excel_compatible_download_count"),
        "pdf_export_enabled_after_template_stable": summary.get("pdf_export_enabled_after_template_stable"),
        "committed_pdf_file_count": summary.get("committed_pdf_file_count"),
        "committed_excel_file_count": summary.get("committed_excel_file_count"),
        "formal_report_count": summary.get("formal_report_count"),
        "business_decision_basis_count": summary.get("business_decision_basis_count"),
        "pending_reconciliation_count": summary.get("pending_reconciliation_count"),
        "required_template_ids": legacy_manifest.get("required_template_ids", []),
        "report_export_version": legacy_manifest.get("report_export_version"),
        "template_version": legacy_manifest.get("template_version"),
        "formula_version": legacy_manifest.get("formula_version"),
        "mapping_version": legacy_manifest.get("mapping_version"),
        "html_template_version": legacy_manifest.get("html_template_version"),
        "csv_appendix_schema_version": legacy_manifest.get("csv_appendix_schema_version"),
        "pdf_export_policy_version": legacy_manifest.get("pdf_export_policy_version"),
        "content_hash": legacy_manifest.get("content_hash"),
        "upstream_template_content_hash": legacy_manifest.get("upstream_template_content_hash"),
        "grade_runtime_content_hash": legacy_manifest.get("grade_runtime_content_hash"),
        "quality_gate": quality_gate,
        "stage_scope": stage_scope,
        "public_repo_safety": public_safety,
        "quality_gate_false_count": _count_false_values(quality_gate),
        "stage_scope_false_count": _count_false_values(stage_scope),
        "public_safety_false_count": _count_false_values(public_safety),
        "record_version_binding_count": _record_version_binding_count(records, legacy_manifest),
        "inherits_blue_business_sample_count": inherits_blue_business_sample_count,
        "pdf_private_runtime_only_count": pdf_private_runtime_only_count,
        "excel_compatible_csv_count": excel_compatible_csv_count,
        "committed_excel_workbook_count": committed_excel_workbook_count,
        "committed_pdf_file_count_recomputed": committed_pdf_file_count,
        "html_output_paths": [_repo_relative(path) for path in html_output_paths],
        "csv_output_paths": [_repo_relative(path) for path in csv_output_paths],
        "source_taskpack_refs": legacy_manifest.get("source_taskpack_refs", {}),
        "artifact_refs": {
            "legacy_manifest": _repo_relative(LEGACY_EXPORT_MANIFEST_PATH),
            "legacy_records": _repo_relative(LEGACY_EXPORT_RECORDS_PATH),
            "legacy_stage_manifest": _repo_relative(LEGACY_STAGE_MANIFEST_PATH),
            "legacy_completion_record": "KMFA/stage_artifacts/S10_P3_report_export/human/s10_p3_completion_record.md",
            "legacy_test_results": "KMFA/stage_artifacts/S10_P3_report_export/human/test_results.md",
            "legacy_html_project_cost": _repo_relative(
                LEGACY_HTML_OUTPUT_DIR / "project_cost_special_report.html"
            ),
            "legacy_html_business_overview": _repo_relative(
                LEGACY_HTML_OUTPUT_DIR / "business_overview_report.html"
            ),
            "legacy_csv_project_cost": _repo_relative(
                LEGACY_CSV_OUTPUT_DIR / "project_cost_special_report_appendix.csv"
            ),
            "legacy_csv_business_overview": _repo_relative(
                LEGACY_CSV_OUTPUT_DIR / "business_overview_report_appendix.csv"
            ),
        },
    }


def build_manifest() -> dict[str, Any]:
    s10_p2 = validate_s10_p2_dependency()
    legacy = validate_legacy_s10_p3_artifacts()
    hard_blocks = [
        "report_grade_d_only",
        "zero_delta_failed",
        "unresolved_critical_difference",
        "missing_required_lineage",
        "missing_human_confirmation_for_A",
        "raw_data_mutation_forbidden",
        "raw_value_publication_forbidden",
        "field_header_plaintext_publication_forbidden",
        "formal_report_release_blocked",
        "business_decision_basis_blocked",
        "stage10_review_not_performed",
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
        "phase_id": "S10-P3",
        "phase_name": "v0.1.3 public-safe report export replay",
        "task_id": TASK_ID,
        "phase_scope": PHASE_SCOPE,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "reviewed_head": git_output(["rev-parse", "HEAD"]),
        "worktree": git_output(["rev-parse", "--show-toplevel"]),
        "branch": git_output(["branch", "--show-current"]),
        "remote": git_output(["remote", "get-url", "origin"]),
        "status": "completed_validated_local_only_no_go_upload_deferred_report_export_replayed",
        "completed_task_ids": ["S10PCT01", "S10PCT02", "S10PCT03"],
        "acceptance_ids": ["ACC-V013-S10-P3-REPORT-EXPORT-REPLAY"],
        "s10_p2_dependency_validated": True,
        "s10_p2_dependency_status": s10_p2.get("status"),
        "legacy_s10_p3_dependency_validated": True,
        "stage10_phase_progress": {
            "completed_phase_count": 3,
            "total_phase_count": 3,
            "derived_percent_bps": 10000,
            "derived_percent_label": "100.00%",
            "s10_p1_performed": True,
            "s10_p2_performed": True,
            "s10_p3_performed": True,
            "stage10_review_performed": False,
        },
        "legacy_s10_p3_summary": {
            "template_count": legacy["template_count"],
            "report_export_record_count": legacy["report_export_record_count"],
            "grade_distribution": legacy["grade_distribution"],
            "html_export_count": legacy["html_export_count"],
            "csv_appendix_count": legacy["csv_appendix_count"],
            "excel_compatible_download_count": legacy["excel_compatible_download_count"],
            "pdf_export_enabled_after_template_stable": legacy["pdf_export_enabled_after_template_stable"],
            "committed_pdf_file_count": legacy["committed_pdf_file_count"],
            "committed_excel_file_count": legacy["committed_excel_file_count"],
            "formal_report_count": legacy["formal_report_count"],
            "business_decision_basis_count": legacy["business_decision_basis_count"],
            "pending_reconciliation_count": legacy["pending_reconciliation_count"],
            "required_template_ids": legacy["required_template_ids"],
        },
        "report_export_policy": {
            "report_export_version": legacy["report_export_version"],
            "expected_report_export_version": EXPORT_RECORD_VERSION,
            "template_version": legacy["template_version"],
            "formula_version": legacy["formula_version"],
            "expected_formula_version": FORMULA_VERSION,
            "mapping_version": legacy["mapping_version"],
            "expected_mapping_version": MAPPING_VERSION,
            "html_template_version": legacy["html_template_version"],
            "expected_html_template_version": HTML_TEMPLATE_VERSION,
            "csv_appendix_schema_version": legacy["csv_appendix_schema_version"],
            "expected_csv_appendix_schema_version": CSV_APPENDIX_SCHEMA_VERSION,
            "pdf_export_policy_version": legacy["pdf_export_policy_version"],
            "expected_pdf_export_policy_version": PDF_EXPORT_POLICY_VERSION,
            "content_hash": legacy["content_hash"],
            "upstream_template_content_hash": legacy["upstream_template_content_hash"],
            "grade_runtime_content_hash": legacy["grade_runtime_content_hash"],
            "record_version_binding_required": True,
            "record_version_binding_count": legacy["record_version_binding_count"],
            "html_export_allowed": True,
            "html_export_count": legacy["html_export_count"],
            "inherits_blue_business_sample_count": legacy["inherits_blue_business_sample_count"],
            "csv_excel_export_allowed": True,
            "csv_appendix_count": legacy["csv_appendix_count"],
            "excel_download_mode": "excel_compatible_csv_no_workbook_committed",
            "excel_compatible_csv_count": legacy["excel_compatible_csv_count"],
            "excel_workbook_committed": False,
            "committed_excel_workbook_count": legacy["committed_excel_workbook_count"],
            "pdf_export_policy_enabled": True,
            "pdf_private_runtime_only": True,
            "pdf_private_runtime_only_count": legacy["pdf_private_runtime_only_count"],
            "pdf_file_committed": False,
            "committed_pdf_file_count": legacy["committed_pdf_file_count"],
            "formal_report_allowed": False,
            "business_decision_basis_allowed": False,
            "quality_gate_false_count": legacy["quality_gate_false_count"],
            "stage_scope_false_count": legacy["stage_scope_false_count"],
            "public_safety_false_count": legacy["public_safety_false_count"],
        },
        "html_sample_inheritance": {
            "taskpack_html_requirement_read": True,
            "source_taskpack_refs": legacy["source_taskpack_refs"],
            "html_output_count": legacy["html_export_count"],
            "inherits_blue_business_sample_count": legacy["inherits_blue_business_sample_count"],
            "implementation_difference": (
                "v0.1.3 replay reuses legacy public-safe HTML/CSV exports and records aggregate "
                "evidence only; no new report design, screenshots, or formal report release are performed."
            ),
        },
        "phase_boundaries": {
            "s10_p1_report_templates_dependency_included": True,
            "s10_p2_report_grade_runtime_dependency_included": True,
            "s10_p3_report_export_scope_included": True,
            "stage10_review_scope_included": False,
            "lineage_full_check_scope_included": False,
            "raw_value_matching_scope_included": False,
            "formal_report_scope_included": False,
            "ui_scope_included": False,
            "external_connector_scope_included": False,
            "github_upload_scope_included": False,
        },
        "quality_gate": {
            "current_data_quality_grade": "Q4",
            "current_report_grade": "D",
            "release_permission": "blocked",
            "pending_reconciliation_count": legacy["pending_reconciliation_count"],
            "confirmed_resolution_count": 0,
            "zero_delta_passed": False,
            "html_export_allowed": True,
            "csv_excel_export_allowed": True,
            "pdf_export_policy_enabled": True,
            "complete_trusted_report_display_allowed": False,
            "full_trusted_report_allowed": False,
            "formal_report_allowed": False,
            "business_decision_basis_allowed": False,
            "business_execution_allowed": False,
            "delivery_allowed": False,
            "raw_layer_write_allowed": False,
            "automatic_external_action_allowed": False,
            "stage10_review_allowed": False,
            "github_upload_allowed": False,
        },
        "github_upload": {
            "github_upload_ready_next_gate": False,
            "github_upload_deferred_until_stage10_batch": True,
            "github_upload_performed": False,
            "github_upload_status": "not_uploaded_deferred_until_stage10_review_and_stage1_10_batch",
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
        "hard_blocks": hard_blocks,
        "hard_block_count": len(hard_blocks),
        "artifact_refs": {
            **legacy["artifact_refs"],
            "manifest": MANIFEST_PATH.as_posix(),
            "report": REPORT_PATH.as_posix(),
            "test_results": TEST_RESULTS_PATH.as_posix(),
            "generator": "KMFA/tools/v013_s10_p3_report_export_replay.py",
            "validator": "KMFA/tools/check_v013_s10_p3_report_export_replay.py",
            "unit_test": "KMFA/tests/test_v013_s10_p3_report_export_replay.py",
        },
        "validators": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v013_s10_p3_report_export_replay.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s10_p3_report_export_replay.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v013_s10_p3_report_export_replay -q",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s10_p3_report_export.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_report_export_runtime -q",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s10_p2_report_grade_runtime_replay.py",
        ],
        "evidence_refs": [
            MANIFEST_PATH.as_posix(),
            REPORT_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            "KMFA/tools/v013_s10_p3_report_export_replay.py",
            "KMFA/tools/check_v013_s10_p3_report_export_replay.py",
            "KMFA/tests/test_v013_s10_p3_report_export_replay.py",
        ],
        "next_required_step": NEXT_REQUIRED_STEP,
    }


def write_report(manifest: dict[str, Any]) -> None:
    summary = manifest["legacy_s10_p3_summary"]
    policy = manifest["report_export_policy"]
    quality = manifest["quality_gate"]
    lines = [
        "# KMFA v0.1.3 S10-P3 Report Export Replay",
        "",
        f"- task_id: `{manifest['task_id']}`",
        f"- status: `{manifest['status']}`",
        f"- phase_scope: `{manifest['phase_scope']}`",
        "- dependency: `v0.1.3 S10-P2 report grade runtime replay PASS`",
        "- legacy_s10_p3_dependency_validated: `true`",
        f"- template_count: `{summary['template_count']}`",
        f"- report_export_record_count: `{summary['report_export_record_count']}`",
        f"- grade_distribution: `{summary['grade_distribution']}`",
        f"- html_export_count: `{summary['html_export_count']}`",
        f"- csv_appendix_count: `{summary['csv_appendix_count']}`",
        f"- excel_compatible_download_count: `{summary['excel_compatible_download_count']}`",
        f"- committed_excel_file_count: `{summary['committed_excel_file_count']}`",
        f"- pdf_export_enabled_after_template_stable: `{str(summary['pdf_export_enabled_after_template_stable']).lower()}`",
        f"- committed_pdf_file_count: `{summary['committed_pdf_file_count']}`",
        f"- formal_report_count: `{summary['formal_report_count']}`",
        f"- business_decision_basis_count: `{summary['business_decision_basis_count']}`",
        f"- pending_reconciliation_count: `{summary['pending_reconciliation_count']}`",
        f"- report_export_version: `{policy['report_export_version']}`",
        f"- formula_version: `{policy['formula_version']}`",
        f"- mapping_version: `{policy['mapping_version']}`",
        f"- html_template_version: `{policy['html_template_version']}`",
        f"- csv_appendix_schema_version: `{policy['csv_appendix_schema_version']}`",
        f"- record_version_binding_count: `{policy['record_version_binding_count']}`",
        "",
        "## Boundary",
        "",
        "- s10_p3_report_export_scope_included: `true`",
        "- stage10_review_scope_included: `false`",
        "- github_upload_deferred_until_stage10_batch: `true`",
        "- github_upload_performed: `false`",
        "- complete_trusted_report_display_allowed: `false`",
        "- formal_report_allowed: `false`",
        "- business_decision_basis_allowed: `false`",
        "- business_execution_allowed: `false`",
        f"- current_report_grade: `{quality['current_report_grade']}`",
        f"- release_permission: `{quality['release_permission']}`",
        "",
        "## HTML/UIUX Inheritance",
        "",
        "- taskpack_html_requirement_read: `true`",
        "- html_output_count: `2`",
        f"- inherits_blue_business_sample_count: `{policy['inherits_blue_business_sample_count']}`",
        "- implementation_difference: `replay only; no new report design or formal release`",
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
            "public-safe report export metadata and existing public-safe HTML/CSV artifacts."
        ),
        "",
        "## Public Safety",
        "",
        (
            "Evidence contains only export counts, D-grade blockers, version bindings, "
            "public-safe artifact references, validator references, and governance paths."
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
        "# KMFA v0.1.3 S10-P3 Report Export Replay Test Results",
        "",
        f"- task_id: `{TASK_ID}`",
        "- status: `pending_final_validation_local_only`",
        "- github_upload_performed: `false`",
        "- raw_dir_read_performed_by_this_phase: `false`",
        "- raw_dir_mutation_performed: `false`",
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
    summary = manifest["legacy_s10_p3_summary"]
    print(
        "PASS: KMFA v0.1.3 S10-P3 report export replay generated "
        f"(export_records={summary['report_export_record_count']}, "
        f"html_exports={summary['html_export_count']}, "
        f"csv_appendices={summary['csv_appendix_count']}, "
        f"excel_compatible_downloads={summary['excel_compatible_download_count']}, "
        f"committed_pdf_files={summary['committed_pdf_file_count']}, "
        f"committed_excel_files={summary['committed_excel_file_count']}, "
        "stage10_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
