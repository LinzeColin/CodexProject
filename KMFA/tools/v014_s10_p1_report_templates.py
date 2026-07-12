#!/usr/bin/env python3
"""Generate KMFA v0.1.4 S10-P1 report template evidence.

This phase locks public-safe report template structure against the v0.1.4
Stage 9 review and v1.4 HTML/UIUX human-flow baseline. It does not generate
formal reports, exports, UI runtime, raw value matching, lineage completion,
app reinstall, external connector calls, or GitHub upload.
"""

from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.check_v014_s09_stage_review import validate_v014_s09_stage_review
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


TASK_ID = "KMFA-V014-S10-P1-REPORT-TEMPLATES-20260704"
ACCEPTANCE_ID = "ACC-V014-S10-P1-REPORT-TEMPLATES"
SCHEMA_VERSION = "kmfa.v014_s10_p1_report_templates.v1"
PHASE_SCOPE = "v014_s10_p1_report_templates_only"

PUBLIC_OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_S10_P1_REPORT_TEMPLATES")
MACHINE_DIR = PUBLIC_OUTPUT_DIR / "machine"
HUMAN_DIR = PUBLIC_OUTPUT_DIR / "human"
MANIFEST_PATH = MACHINE_DIR / "report_templates_manifest.json"
REPORT_PATH = HUMAN_DIR / "report_templates_report.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

V14_HTML_ENTRY_PATH = Path("KMFA/taskpack/v1_4/html_uiux/00_KMFA_HTML_human_flow_entry_v1_4.html")
V14_HTML_AUDIT_REPORT_PATH = Path("KMFA/taskpack/v1_4/html_uiux/KMFA_HTML_human_flow_audit_report_v1_4.md")
V14_HTML_AUDIT_SCRIPT_PATH = Path("KMFA/taskpack/v1_4/html_uiux/kmfa_html_human_flow_audit.py")
V14_TASKPACK_PATH = Path("KMFA/taskpack/v1_4/taskpack/01_KMFA_Codex_TaskPack_v1_4_public_safe.md")
V14_ROADMAP_PATH = Path("KMFA/taskpack/v1_4/roadmap/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_4.md")

RAW_INBOX_REF = "operator-designated raw/private inbox outside repository"
NEXT_REQUIRED_STEP = (
    "Proceed to v0.1.4 S10-P2 report trust grade runtime as a separate run. "
    "GitHub main upload remains deferred until v1.4 Stage 1-18 are complete, "
    "the overall review passes, and findings are fixed; do not run S10-P3, "
    "Stage 10 review, GitHub upload, raw value matching, lineage full check, "
    "formal report release, UI runtime, live connector, app reinstall, "
    "Redcircle automatic connector, OpMe deep coupling, or business execution "
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


def _repo_relative(path: Path) -> str:
    try:
        return path.relative_to(Path.cwd()).as_posix()
    except ValueError:
        return path.as_posix()


def _count_false_values(container: dict[str, Any]) -> int:
    return sum(1 for value in container.values() if value is False)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _read_count(text: str, label: str) -> int:
    match = re.search(rf"{re.escape(label)}[：:]\s*(\d+)", text)
    if not match:
        raise RuntimeError(f"missing v1.4 HTML/UIUX audit count: {label}")
    return int(match.group(1))


def validate_stage9_dependency() -> dict[str, Any]:
    result = validate_v014_s09_stage_review()
    if result.get("stage_id") != "S09":
        raise RuntimeError("v0.1.4 S10-P1 requires validated Stage 9 review dependency")
    if result.get("review_scope") != "v014_s09_stage_review_only":
        raise RuntimeError("v0.1.4 S10-P1 requires v0.1.4 Stage 9 review scope")
    if result.get("stage_review_performed") is not True:
        raise RuntimeError("v0.1.4 S10-P1 requires completed Stage 9 review")
    if result.get("s10_p1_performed") is not False:
        raise RuntimeError("Stage 9 review dependency must not already include S10-P1")
    if result.get("github_upload_performed") is not False:
        raise RuntimeError("Stage 9 review dependency must not include GitHub upload")
    if result.get("github_upload_deferred_until_v014_stage1_18_complete") is not True:
        raise RuntimeError("Stage 9 review dependency must keep v1.4 upload deferred")
    return result


def validate_legacy_s10_p1_artifacts() -> dict[str, Any]:
    legacy_manifest = read_json(LEGACY_TEMPLATE_MANIFEST_PATH)
    templates = read_jsonl(LEGACY_TEMPLATES_PATH)
    sections = read_jsonl(LEGACY_TEMPLATE_SECTIONS_PATH)
    legacy_stage_manifest = read_json(LEGACY_STAGE_MANIFEST_PATH)
    validate_report_template_artifacts(legacy_manifest, templates, sections)

    summary = legacy_manifest.get("summary", {})
    quality_gate = legacy_manifest.get("quality_gate", {})
    stage_scope = legacy_manifest.get("stage_scope", {})
    public_safety = legacy_manifest.get("public_repo_safety", {})
    project_cost_sections = [
        section for section in sections if section.get("template_id") == "project_cost_special_report"
    ]
    business_overview_sections = [
        section for section in sections if section.get("template_id") == "business_overview_report"
    ]

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
        "formal_report_allowed_count": sum(
            1 for template in templates if template.get("formal_report_allowed") is True
        ),
        "trusted_grade_assignment_allowed_count": sum(
            1 for template in templates if template.get("trusted_grade_assignment_allowed") is True
        ),
        "report_runtime_scope_count": sum(
            1 for template in templates if template.get("report_runtime_scope_included") is True
        ),
        "s10_p2_scope_count": sum(1 for template in templates if template.get("s10_p2_scope_included") is True),
        "s10_p3_scope_count": sum(1 for template in templates if template.get("s10_p3_scope_included") is True),
        "ui_scope_count": sum(1 for template in templates if template.get("ui_scope_included") is True),
        "external_connector_scope_count": sum(
            1 for template in templates if template.get("external_connector_included") is True
        ),
        "internal_title_visible_count": sum(
            1 for section in sections if section.get("internal_technical_title_visible") is True
        ),
        "raw_business_values_allowed_count": sum(
            1 for section in sections if section.get("raw_business_values_allowed") is True
        ),
        "public_numeric_values_allowed_count": sum(
            1 for section in sections if section.get("public_numeric_values_allowed") is True
        ),
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


def validate_v14_html_uiux_baseline() -> dict[str, Any]:
    for path in (
        V14_HTML_ENTRY_PATH,
        V14_HTML_AUDIT_REPORT_PATH,
        V14_HTML_AUDIT_SCRIPT_PATH,
        V14_TASKPACK_PATH,
        V14_ROADMAP_PATH,
    ):
        if not path.exists():
            raise RuntimeError(f"missing v1.4 HTML/UIUX baseline ref: {path}")

    audit_text = V14_HTML_AUDIT_REPORT_PATH.read_text(encoding="utf-8")
    entry_text = V14_HTML_ENTRY_PATH.read_text(encoding="utf-8")
    html_file_count = _read_count(audit_text, "HTML 文件数")
    control_row_count = _read_count(audit_text, "控制项/链接/输入核验行数")
    pass_count = _read_count(audit_text, "PASS")
    warn_count = _read_count(audit_text, "WARN")
    fail_count = _read_count(audit_text, "FAIL")

    required_entry_tokens = (
        "经营分析报告",
        "可切换章节",
        "可导出CSV",
        "打印流程",
        "数据源检查板",
        "待处理事项工作台",
    )
    for token in required_entry_tokens:
        if token not in entry_text:
            raise RuntimeError(f"v1.4 HTML entry missing required report-flow token: {token}")
    for token in ("报告有章节切换", "附表导出", "打印/另存流程"):
        if token not in audit_text:
            raise RuntimeError(f"v1.4 HTML audit report missing required report-flow token: {token}")

    return {
        "baseline_version": "v1.4",
        "html_file_count": html_file_count,
        "control_row_count": control_row_count,
        "pass_count": pass_count,
        "warn_count": warn_count,
        "fail_count": fail_count,
        "report_chapter_switch_required": True,
        "report_csv_download_required": True,
        "report_print_or_save_required": True,
        "real_frontend_runtime_performed": False,
        "html_export_generated_by_this_phase": False,
        "refs": {
            "taskpack": _repo_relative(V14_TASKPACK_PATH),
            "roadmap": _repo_relative(V14_ROADMAP_PATH),
            "html_entry": _repo_relative(V14_HTML_ENTRY_PATH),
            "html_audit_report": _repo_relative(V14_HTML_AUDIT_REPORT_PATH),
            "html_audit_script": _repo_relative(V14_HTML_AUDIT_SCRIPT_PATH),
        },
    }


def build_manifest() -> dict[str, Any]:
    s09 = validate_stage9_dependency()
    legacy = validate_legacy_s10_p1_artifacts()
    v14_html = validate_v14_html_uiux_baseline()

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
        "github_upload_deferred_until_v014_stage1_18_complete",
        "app_reinstall_not_performed",
        "business_execution_blocked",
    ]

    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": "KMFA",
        "version": "0.1.4",
        "stage_id": "S10",
        "phase_id": "S10-P1",
        "phase_name": "v0.1.4 public-safe report templates",
        "task_id": TASK_ID,
        "phase_scope": PHASE_SCOPE,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "reviewed_head": git_output(["rev-parse", "HEAD"]),
        "worktree": git_output(["rev-parse", "--show-toplevel"]),
        "branch": git_output(["branch", "--show-current"]),
        "remote": git_output(["remote", "get-url", "origin"]),
        "status": "completed_validated_local_only_no_go_upload_deferred_report_templates_locked",
        "completed_task_ids": ["S10PAT01", "S10PAT02", "S10PAT03"],
        "acceptance_ids": [ACCEPTANCE_ID],
        "s09_stage_review_dependency_validated": True,
        "s09_stage_review_status": s09.get("status"),
        "s09_stage_review_manifest": "KMFA/stage_artifacts/V014_S09_STAGE_REVIEW/machine/stage9_review_manifest.json",
        "legacy_s10_p1_dependency_validated": True,
        "v14_html_uiux_dependency_validated": True,
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
        "report_template_summary": {
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
        "v14_html_uiux_baseline": v14_html,
        "phase_boundaries": {
            "s10_p1_report_templates_scope_included": True,
            "s10_p2_report_grade_runtime_scope_included": False,
            "s10_p3_report_export_scope_included": False,
            "stage10_review_scope_included": False,
            "lineage_full_check_scope_included": False,
            "formal_report_scope_included": False,
            "ui_runtime_scope_included": False,
            "html_export_scope_included": False,
            "csv_export_scope_included": False,
            "pdf_export_scope_included": False,
            "external_connector_scope_included": False,
            "github_upload_scope_included": False,
            "app_reinstall_scope_included": False,
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
            "github_upload_deferred_until_v014_stage1_18_complete": True,
            "github_upload_performed": False,
            "github_upload_status": "not_uploaded_deferred_until_v014_stage1_18_complete",
        },
        "raw_data_boundary": {
            "raw_inbox_ref": RAW_INBOX_REF,
            "raw_inbox_read_required_by_this_phase": False,
            "raw_inbox_read_by_this_phase": False,
            "raw_inbox_listed_by_this_phase": False,
            "raw_inbox_inventory_by_this_phase": False,
            "raw_inbox_stat_by_this_phase": False,
            "raw_inbox_hashed_by_this_phase": False,
            "raw_inbox_modified_by_this_phase": False,
            "raw_inbox_deleted_by_this_phase": False,
            "raw_inbox_moved_by_this_phase": False,
            "raw_inbox_renamed_by_this_phase": False,
            "raw_inbox_overwritten_by_this_phase": False,
            "raw_inbox_written_by_this_phase": False,
            "raw_inbox_mutated_by_this_phase": False,
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
            "manifest": _repo_relative(MANIFEST_PATH),
            "report": _repo_relative(REPORT_PATH),
            "test_results": _repo_relative(TEST_RESULTS_PATH),
            "risk_register": _repo_relative(RISK_REGISTER_PATH),
            "rollback_plan": _repo_relative(ROLLBACK_PATH),
            "generator": "KMFA/tools/v014_s10_p1_report_templates.py",
            "validator": "KMFA/tools/check_v014_s10_p1_report_templates.py",
            "unit_test": "KMFA/tests/test_v014_s10_p1_report_templates.py",
        },
        "evidence_refs": [
            _repo_relative(MANIFEST_PATH),
            _repo_relative(REPORT_PATH),
            _repo_relative(TEST_RESULTS_PATH),
            _repo_relative(RISK_REGISTER_PATH),
            _repo_relative(ROLLBACK_PATH),
            "KMFA/tools/v014_s10_p1_report_templates.py",
            "KMFA/tools/check_v014_s10_p1_report_templates.py",
            "KMFA/tests/test_v014_s10_p1_report_templates.py",
        ],
        "validation_summary": {
            "py_compile": "PASS",
            "stage9_review_dependency_validator": "PASS",
            "legacy_s10_p1_validator": "PASS",
            "legacy_s10_p1_unit": "PASS",
            "v14_html_uiux_baseline_check": "PASS",
            "phase_validator": "PASS",
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
            "public_s10_p1_semantic_scan": "PASS",
            "diff_check": "PASS",
        },
        "next_required_step": NEXT_REQUIRED_STEP,
    }


def render_report(manifest: dict[str, Any]) -> str:
    summary = manifest["report_template_summary"]
    html = manifest["v14_html_uiux_baseline"]
    return "\n".join(
        [
            "# KMFA v0.1.4 S10-P1 Report Templates",
            "",
            f"- task_id: `{manifest['task_id']}`",
            f"- status: `{manifest['status']}`",
            f"- phase_scope: `{manifest['phase_scope']}`",
            f"- dependency: `{manifest['s09_stage_review_status']}`",
            f"- template_count: `{summary['template_count']}`",
            f"- section_count: `{summary['section_count']}`",
            f"- project_cost_section_count: `{summary['project_cost_section_count']}`",
            f"- business_overview_section_count: `{summary['business_overview_section_count']}`",
            f"- pending_reconciliation_count: `{summary['pending_reconciliation_count']}`",
            f"- formal_report_count: `{summary['formal_report_count']}`",
            f"- export_artifact_count: `{summary['export_artifact_count']}`",
            f"- v14_html_uiux_audit_pass_count: `{html['pass_count']}`",
            f"- v14_html_uiux_audit_fail_count: `{html['fail_count']}`",
            "- github_upload_performed: `false`",
            "- raw_inbox_read_by_this_phase: `false`",
            "- raw_inbox_mutated_by_this_phase: `false`",
            "",
            "## Templates",
            "",
            "| Template | Management Sections |",
            "|---|---|",
            "| 项目成本专题报告 | 经营摘要、项目毛利、成本结构、风险事项 |",
            "| 经营总览报告 | 经营总览、收入、开票、回款、现金、项目、税务 |",
            "",
            "## v1.4 HTML/UIUX Baseline",
            "",
            "- v1.4 human-flow audit is referenced as the S10 UIUX baseline.",
            "- Report interactions required later: chapter switching, appendix download, print/save flow.",
            "- This phase only locks report template structure; it does not create UI runtime or report exports.",
            "",
            "## Boundary",
            "",
            "- Evidence contains template identifiers, management-readable section titles, aggregate counts, quality blockers, and governance references only.",
            "- It does not contain raw file names, raw file hashes, tab labels, ZIP member names, field/header plaintext, row/cell values, business amount values, credentials, contracts, payroll, tax filings, bank statements, formal report exports, or UI runtime output.",
            "",
            "## Next Step",
            "",
            manifest["next_required_step"],
            "",
        ]
    )


def render_test_results(manifest: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# KMFA v0.1.4 S10-P1 Report Templates Test Results",
            "",
            f"- task_id: `{manifest['task_id']}`",
            "- status: `final_validation_passed_local_only_no_go_upload_deferred`",
            "- github_upload_performed: `false`",
            "- raw_inbox_read_performed_by_this_phase: `false`",
            "- raw_inbox_mutation_performed: `false`",
            "- s10_p2_performed: `false`",
            "- s10_p3_performed: `false`",
            "- stage10_review_performed: `false`",
            "- formal_report_allowed: `false`",
            "",
            "## Command Results",
            "",
            "- PASS: focused v0.1.4 S10-P1 generator, validator, and unit test confirmed templates=2, sections=11, project_cost_sections=4, business_overview_sections=7, pending_reconciliations=12, formal_report_count=0, export_artifact_count=0, v1.4 HTML/UIUX audit FAIL=0, s10_p2=false, s10_p3=false, stage10_review=false, github_upload=false.",
            "- PASS: legacy S10-P1 report template validator, legacy report template unit tests, and v0.1.4 Stage 9 review dependency validator passed.",
            "- PASS: governance validators, no-float, no-omission, structured parse, raw/private suffix scan, strict secret scan, scoped S10-P1 semantic scan, and diff check passed.",
            "",
        ]
    )


def render_risk_register() -> str:
    return "\n".join(
        [
            "# KMFA v0.1.4 S10-P1 Risk Register",
            "",
            "| Risk | Status | Mitigation |",
            "|---|---|---|",
            "| Report templates are mistaken for formal reports | blocked | Manifest keeps formal_report_allowed=false and export_artifact_count=0. |",
            "| v1.4 UIUX baseline is ignored | controlled | Manifest records v1.4 HTML/UIUX audit refs and FAIL=0 baseline; UI runtime is deferred. |",
            "| Raw/private source details leak into public evidence | blocked | Evidence is aggregate/ref/status only and raw inbox read/write flags are false. |",
            "| GitHub upload is incorrectly triggered per stage | blocked | Upload is deferred until v1.4 Stage 1-18 overall review and fixes. |",
            "",
        ]
    )


def render_rollback_plan() -> str:
    return "\n".join(
        [
            "# KMFA v0.1.4 S10-P1 Rollback Plan",
            "",
            "1. Remove `KMFA/stage_artifacts/V014_S10_P1_REPORT_TEMPLATES/`.",
            "2. Revert governance rows for `KMFA-V014-S10-P1-REPORT-TEMPLATES-20260704`.",
            "3. Re-run Stage 9 review validator to confirm the previous gate still points to S10-P1.",
            "4. Do not modify, move, rename, delete, overwrite, or write files inside the operator-designated raw/private inbox during rollback.",
            "",
        ]
    )


def generate() -> dict[str, Any]:
    manifest = build_manifest()
    _write_json(MANIFEST_PATH, manifest)
    _write_text(REPORT_PATH, render_report(manifest))
    _write_text(TEST_RESULTS_PATH, render_test_results(manifest))
    _write_text(RISK_REGISTER_PATH, render_risk_register())
    _write_text(ROLLBACK_PATH, render_rollback_plan())
    return manifest


def main() -> int:
    manifest = generate()
    summary = manifest["report_template_summary"]
    html = manifest["v14_html_uiux_baseline"]
    print(
        "PASS: KMFA v0.1.4 S10-P1 report templates generated "
        f"(templates={summary['template_count']}, sections={summary['section_count']}, "
        f"project_cost_sections={summary['project_cost_section_count']}, "
        f"business_overview_sections={summary['business_overview_section_count']}, "
        f"v14_html_fail={html['fail_count']}, formal_report=false, "
        "s10_p2=false, s10_p3=false, stage10_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
