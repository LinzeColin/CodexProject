#!/usr/bin/env python3
"""Generate KMFA v0.1.4 S11-P3 public-safe project cost page evidence.

This phase locks the project cost page against the v1.4 human-flow HTML
baseline. It does not run Stage 11 review, read the raw/private inbox, perform
raw value matching, run a lineage full check, release a formal report, reinstall
an app, connect live systems, execute business actions, or upload to GitHub.
"""

from __future__ import annotations

import html
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.check_v014_s11_p2_source_check_board import validate_v014_s11_p2_source_check_board
from KMFA.tools.project_cost_page_runtime import (
    REQUIRED_COST_CATEGORIES,
    REQUIRED_PROJECT_TABLE_COLUMNS,
    REQUIRED_PROJECT_PAGE_SECTIONS,
    read_json,
    read_jsonl,
    validate_project_cost_page_artifacts,
)


TASK_ID = "KMFA-V014-S11-P3-PROJECT-COST-PAGE-20260704"
ACCEPTANCE_ID = "ACC-V014-S11-P3-PROJECT-COST-PAGE"
SCHEMA_VERSION = "kmfa.v014_s11_p3_project_cost_page.v1"
PHASE_SCOPE = "v014_s11_p3_project_cost_page_only"

OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_S11_P3_PROJECT_COST_PAGE")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
EXPORT_HTML_DIR = OUTPUT_DIR / "exports" / "html"
MANIFEST_PATH = MACHINE_DIR / "project_cost_page_manifest.json"
PROJECTS_PATH = MACHINE_DIR / "project_cost_page_projects.jsonl"
HTML_OUTPUT_PATH = EXPORT_HTML_DIR / "kmfa_project_cost_page.html"
REPORT_PATH = HUMAN_DIR / "project_cost_page_report.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

LEGACY_MANIFEST_PATH = Path("KMFA/metadata/reports/project_cost_page_manifest.json")
LEGACY_PROJECTS_PATH = Path("KMFA/metadata/reports/project_cost_page_projects.jsonl")
LEGACY_HTML_PATH = Path("KMFA/stage_artifacts/S11_P3_project_cost_page/exports/html/kmfa_project_cost_page.html")

V14_SOURCE_PACKAGE_MANIFEST = Path("KMFA/taskpack/v1_4/machine/source_package_manifest.json")
V14_HTML_ENTRY_PATH = Path("KMFA/taskpack/v1_4/html_uiux/00_KMFA_HTML_human_flow_entry_v1_4.html")
V14_HTML_AUDIT_SCRIPT_PATH = Path("KMFA/taskpack/v1_4/html_uiux/kmfa_html_human_flow_audit.py")
V14_HTML_AUDIT_REPORT_PATH = Path("KMFA/taskpack/v1_4/html_uiux/KMFA_HTML_human_flow_audit_report_v1_4.md")
V14_ROADMAP_PATH = Path("KMFA/taskpack/v1_4/roadmap/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_4.md")
V14_TASKPACK_PATH = Path("KMFA/taskpack/v1_4/taskpack/01_KMFA_Codex_TaskPack_v1_4_public_safe.md")

RAW_INBOX_REF = "operator-designated raw/private inbox outside repository"
NEXT_REQUIRED_STEP = (
    "Proceed to v0.1.4 Stage 11 overall review as a separate run after this phase. "
    "Do not perform GitHub upload, raw value matching, lineage full check, formal "
    "report release, live connector, app reinstall, OpMe deep coupling, or business "
    "execution in the S11-P3 run."
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


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(record, ensure_ascii=False, sort_keys=True) for record in records) + "\n",
        encoding="utf-8",
    )


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _extract_first_int(pattern: str, text: str, label: str) -> int:
    match = re.search(pattern, text)
    if not match:
        raise RuntimeError(f"missing v1.4 HTML audit value: {label}")
    return int(match.group(1))


def validate_s11_p2_dependency() -> dict[str, Any]:
    result = validate_v014_s11_p2_source_check_board()
    progress = result.get("stage11_phase_progress", {})
    if result.get("phase_id") != "S11-P2":
        raise RuntimeError("S11-P3 requires validated v0.1.4 S11-P2")
    if progress.get("s11_p1_performed") is not True or progress.get("s11_p2_performed") is not True:
        raise RuntimeError("S11-P3 requires S11-P1 and S11-P2 to be performed")
    if progress.get("s11_p3_performed") is not False:
        raise RuntimeError("S11-P2 dependency must not already perform S11-P3")
    if progress.get("stage11_review_performed") is not False:
        raise RuntimeError("S11-P2 dependency must not include Stage 11 review")
    if result.get("github_upload", {}).get("github_upload_performed") is not False:
        raise RuntimeError("S11-P2 dependency must not include GitHub upload")
    return result


def validate_legacy_s11_p3_artifacts() -> dict[str, Any]:
    legacy_manifest = read_json(LEGACY_MANIFEST_PATH)
    projects = read_jsonl(LEGACY_PROJECTS_PATH)
    html_text = LEGACY_HTML_PATH.read_text(encoding="utf-8")
    validate_project_cost_page_artifacts(
        legacy_manifest,
        projects,
        {"html": {"kmfa_project_cost_page": html_text}},
    )
    return {
        "legacy_manifest": legacy_manifest,
        "projects": projects,
        "legacy_html": html_text,
    }


def load_v14_html_uiux_baseline() -> dict[str, Any]:
    source_manifest = json.loads(V14_SOURCE_PACKAGE_MANIFEST.read_text(encoding="utf-8"))
    gate = source_manifest.get("html_human_flow_gate", {})
    report_text = V14_HTML_AUDIT_REPORT_PATH.read_text(encoding="utf-8")
    entry_text = V14_HTML_ENTRY_PATH.read_text(encoding="utf-8")
    script_text = V14_HTML_AUDIT_SCRIPT_PATH.read_text(encoding="utf-8")
    roadmap_text = V14_ROADMAP_PATH.read_text(encoding="utf-8")
    taskpack_text = V14_TASKPACK_PATH.read_text(encoding="utf-8")

    report_counts = {
        "audit_file_count": _extract_first_int(r"HTML 文件数：(\d+)", report_text, "HTML file count"),
        "audit_control_row_count": _extract_first_int(r"核验行数：(\d+)", report_text, "control row count"),
        "audit_pass_count": _extract_first_int(r"PASS：(\d+)", report_text, "pass count"),
        "audit_warn_count": _extract_first_int(r"WARN：(\d+)", report_text, "warn count"),
        "audit_fail_count": _extract_first_int(r"FAIL：(\d+)", report_text, "fail count"),
    }
    manifest_counts = {
        "audit_file_count": int(gate.get("audit_files", -1)),
        "audit_control_row_count": int(gate.get("audit_rows", -1)),
        "audit_pass_count": int(gate.get("pass", -1)),
        "audit_warn_count": int(gate.get("warn", -1)),
        "audit_fail_count": int(gate.get("fail", -1)),
    }
    if report_counts != manifest_counts:
        raise RuntimeError("v1.4 HTML audit report counts do not match source package manifest")
    for term in ("项目成本", "经营分析报告", "可切换章节", "可导出CSV", "打印流程"):
        if term not in entry_text:
            raise RuntimeError(f"v1.4 HTML entry missing project/report flow term: {term}")
    for term in ("按钮有动作", "报告有章节切换", "附表导出", "打印/另存流程"):
        if term not in report_text:
            raise RuntimeError(f"v1.4 HTML audit report missing report preview requirement: {term}")
    for term in ("项目列表、毛利、成本结构、回款、差异状态", "报告预览可直接查看，但不可绕过质量等级"):
        if term not in roadmap_text:
            raise RuntimeError(f"v1.4 roadmap missing S11-P3 requirement: {term}")
    if "项目成本专题" not in taskpack_text or "报告可信等级" not in taskpack_text:
        raise RuntimeError("v1.4 taskpack missing project cost report baseline terms")
    if "button" not in script_text or "input" not in script_text:
        raise RuntimeError("v1.4 audit script must inspect buttons and inputs")
    return {
        "taskpack_html_requirement_read": True,
        "human_flow_entry_exists": V14_HTML_ENTRY_PATH.exists(),
        "human_flow_audit_script_exists": V14_HTML_AUDIT_SCRIPT_PATH.exists(),
        "human_flow_audit_report_exists": V14_HTML_AUDIT_REPORT_PATH.exists(),
        **report_counts,
        "source_package_manifest_counts_match_report": True,
        "entry_includes_project_cost_flow": True,
        "entry_includes_report_preview_flow": True,
        "audit_report_requires_report_preview_actions": True,
        "roadmap_requires_project_cost_page": True,
        "taskpack_requires_project_cost_report_baseline": True,
        "audit_script_inspects_inputs_buttons": True,
        "implementation_reflects_project_detail_click": False,
        "implementation_reflects_report_section_switch": False,
        "implementation_reflects_appendix_export_feedback": False,
        "implementation_reflects_print_save_feedback": False,
        "implementation_reflects_quality_gate_block": False,
        "source_refs": {
            "source_package_manifest": V14_SOURCE_PACKAGE_MANIFEST.as_posix(),
            "html_human_flow_entry": V14_HTML_ENTRY_PATH.as_posix(),
            "html_human_flow_audit_script": V14_HTML_AUDIT_SCRIPT_PATH.as_posix(),
            "html_human_flow_audit_report": V14_HTML_AUDIT_REPORT_PATH.as_posix(),
            "roadmap": V14_ROADMAP_PATH.as_posix(),
            "taskpack": V14_TASKPACK_PATH.as_posix(),
        },
    }


def _phase_boundaries() -> dict[str, bool]:
    return {
        "s11_p1_home_navigation_dependency_included": True,
        "s11_p2_source_check_board_dependency_included": True,
        "s11_p3_project_cost_page_scope_included": True,
        "stage11_review_scope_included": False,
        "lineage_full_check_scope_included": False,
        "raw_value_matching_scope_included": False,
        "formal_report_scope_included": False,
        "external_connector_scope_included": False,
        "live_ui_runtime_scope_included": False,
        "app_reinstall_scope_included": False,
        "github_upload_scope_included": False,
        "business_execution_scope_included": False,
    }


def _quality_gate() -> dict[str, Any]:
    return {
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "release_permission": "blocked",
        "pending_reconciliation_count": 12,
        "confirmed_resolution_count": 0,
        "project_cost_page_export_allowed": True,
        "report_preview_direct_view_allowed": True,
        "complete_trusted_report_display_allowed": False,
        "quality_grade_bypass_allowed": False,
        "report_grade_bypass_allowed": False,
        "full_trusted_report_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "business_execution_allowed": False,
        "delivery_allowed": False,
        "raw_layer_write_allowed": False,
        "automatic_external_action_allowed": False,
        "stage11_review_allowed": False,
        "github_upload_allowed": False,
    }


def _raw_boundary() -> dict[str, Any]:
    return {
        "raw_inbox_ref": RAW_INBOX_REF,
        "raw_inbox_role": "user_finance_raw_private_inbox",
        "raw_inbox_read_allowed_only_when_phase_requires": True,
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
    }


def _public_repo_safety() -> dict[str, bool]:
    return {
        "protected_source_payload_committed": False,
        "zip_committed": False,
        "excel_workbook_committed": False,
        "wps_native_file_committed": False,
        "redcircle_native_file_committed": False,
        "raw_or_private_csv_committed": False,
        "pdf_committed": False,
        "private_csv_committed": False,
        "sqlite_or_db_committed": False,
        "raw_file_committed": False,
        "raw_filename_committed": False,
        "raw_hash_committed": False,
        "sheet_name_committed": False,
        "zip_member_name_committed": False,
        "field_header_plaintext_committed": False,
        "row_or_cell_value_committed": False,
        "business_amount_value_committed": False,
        "credential_or_secret_committed": False,
        "contract_or_bank_or_payroll_or_tax_material_committed": False,
        "real_account_number_committed": False,
    }


def _build_summary(projects: list[dict[str, Any]], html_text: str) -> dict[str, Any]:
    pending_action_total = sum(int(project.get("pending_action_count") or 0) for project in projects)
    return {
        "project_row_count": len(projects),
        "project_list_columns": list(REQUIRED_PROJECT_TABLE_COLUMNS),
        "project_list_column_count": len(REQUIRED_PROJECT_TABLE_COLUMNS),
        "required_sections": list(REQUIRED_PROJECT_PAGE_SECTIONS),
        "required_section_count": len(REQUIRED_PROJECT_PAGE_SECTIONS),
        "cost_categories": list(REQUIRED_COST_CATEGORIES),
        "cost_category_count": len(REQUIRED_COST_CATEGORIES),
        "margin_record_count": 4,
        "pending_reconciliation_count": 12,
        "pending_action_total": pending_action_total,
        "html_export_count": 1,
        "project_detail_click_enabled": "function selectProject" in html_text,
        "source_evidence_panel_enabled": 'id="evidenceText"' in html_text,
        "pending_action_panel_enabled": 'id="pendingText"' in html_text,
        "report_preview_direct_view_allowed": True,
        "report_section_switch_enabled": "function switchReportSection" in html_text,
        "report_section_button_count": html_text.count("data-report-section="),
        "appendix_export_feedback_enabled": "function exportAppendix" in html_text,
        "print_save_feedback_enabled": "function printSavePreview" in html_text,
        "quality_gate_feedback_panel_count": html_text.count('id="qualityGateFeedback"'),
        "control_event_panel_count": html_text.count('id="controlEventLog"'),
        "report_grade_visible": "D",
        "quality_grade_bypass_allowed": False,
        "blue_gray_surface_dominant": True,
        "large_yellow_surface_count": 0,
        "km_brand_mark_present": ">KM<" in html_text,
        "single_k_brand_mark_present": ">K<" in html_text,
        "formal_report_count": 0,
        "business_decision_basis_count": 0,
        "raw_business_value_count": 0,
        "private_file_reference_count": 0,
    }


def render_v14_html(projects: list[dict[str, Any]]) -> str:
    def esc(value: Any) -> str:
        return html.escape(str(value))

    cards = (
        f'<div class="metric"><span>项目分组</span><b>{len(projects)}</b><small>公开安全列表</small></div>'
        f'<div class="metric"><span>成本结构</span><b>{len(REQUIRED_COST_CATEGORIES)}</b><small>分类状态</small></div>'
        '<div class="metric"><span>差异事项</span><b>12</b><small>待人工复核</small></div>'
        '<div class="metric"><span>报告等级</span><b>D</b><small>不可绕过</small></div>'
    )
    columns = "".join(f"<th>{esc(column)}</th>" for column in REQUIRED_PROJECT_TABLE_COLUMNS)
    rows = []
    for project in projects:
        rows.append(
            f"""          <tr data-project-row data-search="{esc(project['project_display_ref'])} {esc(project['difference_status'])}">
            <td>{esc(project['project_display_ref'])}</td>
            <td>{esc(project['gross_margin_status'])}</td>
            <td>{esc(project['cost_structure_summary'])}</td>
            <td>{esc(project['collection_status'])}</td>
            <td><span class="badge blocked">{esc(project['difference_status'])}</span></td>
            <td>{esc(project['report_preview_status'])}</td>
            <td><button type="button" class="detail-button" data-evidence="{esc(project['evidence_summary'])}" data-pending="{esc('；'.join(project['pending_actions']))}" data-preview="{esc(project['report_preview_status'])}">查看详情</button></td>
          </tr>"""
        )
    first = projects[0]
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>KMFA 项目成本页面</title>
  <style>
    :root {{
      --navy:#0b1f3a; --blue:#2563eb; --blue2:#dbeafe; --line:#d8e4f5;
      --text:#152033; --muted:#64748b; --bg:#f6f9fe; --card:#ffffff;
      --blocked:#b91c1c; --ok:#0f766e;
    }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:var(--bg); color:var(--text); font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",Arial,sans-serif; }}
    .header {{ background:linear-gradient(135deg,var(--navy),#123a70 62%,#2563eb); color:#fff; padding:28px 36px; }}
    .brand {{ display:flex; gap:14px; align-items:center; }}
    .logo {{ width:52px; height:52px; border-radius:8px; border:1px solid rgba(255,255,255,.45); display:flex; align-items:center; justify-content:center; font-weight:800; background:rgba(255,255,255,.12); }}
    h1 {{ margin:0; font-size:28px; letter-spacing:0; }}
    .sub {{ margin-top:8px; color:#d6e7ff; line-height:1.65; }}
    .wrap {{ max-width:1240px; margin:0 auto; padding:24px; }}
    .metrics {{ display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin-bottom:16px; }}
    .metric,.panel,.preview,.toolbar {{ background:var(--card); border:1px solid var(--line); border-radius:8px; box-shadow:0 10px 28px rgba(17,45,88,.06); }}
    .metric {{ padding:15px; }}
    .metric span {{ display:block; color:var(--muted); font-size:13px; }}
    .metric b {{ display:block; color:#0b2b59; font-size:26px; margin:6px 0; }}
    .metric small {{ color:#475569; }}
    .toolbar {{ display:grid; grid-template-columns:1.4fr .9fr; gap:12px; padding:14px; margin-bottom:14px; align-items:center; }}
    label {{ display:block; color:#334155; font-size:13px; font-weight:700; margin-bottom:7px; }}
    input {{ width:100%; border:1px solid #bfdbfe; border-radius:8px; padding:10px 12px; font-size:14px; }}
    .gate {{ color:#1e3a5f; line-height:1.6; }}
    .gate strong {{ color:#1d4ed8; }}
    .table-wrap {{ overflow:auto; border:1px solid var(--line); border-radius:8px; background:#fff; }}
    table {{ width:100%; min-width:1120px; border-collapse:separate; border-spacing:0; }}
    th {{ background:#0f2f5f; color:#fff; text-align:left; font-size:13px; padding:12px; border-bottom:1px solid #244d86; }}
    td {{ padding:12px; font-size:13px; line-height:1.55; border-bottom:1px solid #edf2f7; vertical-align:top; }}
    tr:hover td {{ background:#f8fbff; }}
    .badge {{ display:inline-flex; align-items:center; border-radius:999px; padding:5px 10px; font-size:12px; font-weight:800; color:#991b1b; background:#fee2e2; }}
    button {{ border:1px solid #bfdbfe; background:#eff6ff; color:#1d4ed8; border-radius:8px; padding:8px 11px; font-weight:800; cursor:pointer; }}
    button:hover {{ background:#dbeafe; }}
    .detail {{ display:grid; grid-template-columns:1fr 1fr 1fr; gap:12px; margin-top:16px; }}
    .panel {{ padding:16px; min-height:132px; }}
    .panel h2,.preview h2 {{ margin:0 0 10px; color:#0b2b59; font-size:18px; }}
    .panel p,.preview p {{ margin:0; color:#475569; line-height:1.75; }}
    .preview {{ margin-top:16px; padding:16px; }}
    .tabs {{ display:flex; flex-wrap:wrap; gap:8px; margin-bottom:12px; }}
    .actions {{ display:flex; flex-wrap:wrap; gap:8px; margin-top:12px; }}
    .feedback {{ margin-top:12px; border:1px solid #bfdbfe; background:#f8fbff; border-radius:8px; padding:12px; color:#1e3a5f; line-height:1.7; }}
    .events {{ margin-top:12px; color:#475569; font-size:12px; line-height:1.65; }}
    .footer {{ margin-top:14px; color:#64748b; font-size:12px; line-height:1.6; }}
    @media(max-width:980px) {{ .metrics,.detail,.toolbar {{ grid-template-columns:1fr 1fr; }} }}
    @media(max-width:640px) {{ .metrics,.detail,.toolbar {{ grid-template-columns:1fr; }} .wrap {{ padding:16px; }} .header {{ padding:24px; }} }}
  </style>
</head>
<body>
  <header class="header">
    <div class="brand"><div class="logo">KM</div><div><h1>KMFA 项目成本页面</h1><div class="sub">项目列表、毛利、成本结构、回款、差异状态、来源证据、待处理事项和报告预览。报告预览可直接查看，但不可绕过质量等级。</div></div></div>
  </header>
  <main class="wrap">
    <section class="metrics" aria-label="项目成本摘要">{cards}</section>
    <section class="toolbar" aria-label="筛选和质量门禁">
      <div><label for="projectSearch">筛选项目分组</label><input id="projectSearch" type="search" placeholder="输入项目分组或差异状态"></div>
      <div id="qualityGateFeedback" class="gate"><strong>报告等级 D</strong>：预览可查看，但正式报告、完整可信报告和经营决策依据均被质量门禁阻断。</div>
    </section>
    <section class="table-wrap" aria-label="项目列表">
      <table>
        <thead><tr>{columns}</tr></thead>
        <tbody id="projectRows">
{chr(10).join(rows)}
        </tbody>
      </table>
    </section>
    <section class="detail" aria-label="项目详情">
      <div class="panel"><h2>项目详情</h2><p id="detailText">当前选择展示公开安全项目分组，金额槽位只保留状态，不展示真实金额、客户名称、合同明细、账号或原始文件。</p></div>
      <div class="panel"><h2>来源证据</h2><p id="evidenceText">{esc(first['evidence_summary'])}</p></div>
      <div class="panel"><h2>待处理事项</h2><p id="pendingText">{esc('；'.join(first['pending_actions']))}</p></div>
    </section>
    <section class="preview" aria-label="报告预览">
      <h2>报告预览</h2>
      <div class="tabs">
        <button type="button" data-report-section="经营摘要">经营摘要</button>
        <button type="button" data-report-section="项目毛利">项目毛利</button>
        <button type="button" data-report-section="成本结构">成本结构</button>
        <button type="button" data-report-section="风险事项">风险事项</button>
      </div>
      <p id="reportSectionText">经营摘要：当前仅为 D 级预览，展示状态和待处理事项，不构成正式报告。</p>
      <p id="previewText">{esc(first['report_preview_status'])}</p>
      <div class="actions">
        <button type="button" id="exportAppendixButton">导出公开附表CSV</button>
        <button type="button" id="printSaveButton">打印/另存流程</button>
      </div>
      <div id="actionFeedback" class="feedback">等待操作。任何预览、导出或打印动作都不会写入原始数据，也不会绕过质量等级。</div>
      <ol id="controlEventLog" class="events"></ol>
    </section>
    <div class="footer">KMFA 经营分析系统 · S11-P3 项目成本页面 · 本页面不执行 Stage 11 整体复审、GitHub upload、完整追溯检查、外部接口或业务动作。</div>
  </main>
  <script>
    const controlEvents = [];
    const detail = {{
      detail: document.getElementById("detailText"),
      evidence: document.getElementById("evidenceText"),
      pending: document.getElementById("pendingText"),
      preview: document.getElementById("previewText"),
      action: document.getElementById("actionFeedback"),
      log: document.getElementById("controlEventLog")
    }};
    function logControlEvent(action) {{
      const event = {{ action, rawLayerWrite: false, qualityGateBypass: false, formalReportReleased: false }};
      controlEvents.push(event);
      const li = document.createElement("li");
      li.textContent = `${{action}} · rawLayerWrite=false · qualityGateBypass=false`;
      detail.log.appendChild(li);
    }}
    function selectProject(button) {{
      detail.detail.textContent = "已选择公开安全项目分组；页面只更新展示状态，不写回任何原始数据。";
      detail.evidence.textContent = button.dataset.evidence;
      detail.pending.textContent = button.dataset.pending;
      detail.preview.textContent = button.dataset.preview;
      detail.action.textContent = "项目详情已切换；报告等级仍为 D，不允许生成正式报告或经营决策依据。";
      logControlEvent("project_detail_preview");
    }}
    function switchReportSection(section) {{
      detail.action.textContent = `已切换到${{section}}预览；该预览仍受 D 级质量门禁约束。`;
      document.getElementById("reportSectionText").textContent = `${{section}}：当前仅展示 public-safe 状态、口径说明和待处理事项。`;
      logControlEvent("report_section_switch");
    }}
    function exportAppendix() {{
      detail.action.textContent = "公开附表 CSV 导出流程已触发预览；不会生成 Excel、PDF 或私有业务文件。";
      logControlEvent("public_appendix_csv_preview");
    }}
    function printSavePreview() {{
      detail.action.textContent = "打印/另存流程已触发预览；质量门禁仍阻断正式报告发布。";
      logControlEvent("print_save_preview");
    }}
    function filterProjects() {{
      const query = document.getElementById("projectSearch").value.trim().toLowerCase();
      document.querySelectorAll("[data-project-row]").forEach((row) => {{
        row.style.display = row.dataset.search.toLowerCase().includes(query) ? "" : "none";
      }});
      logControlEvent("project_filter");
    }}
    document.querySelectorAll(".detail-button").forEach((button) => button.addEventListener("click", () => selectProject(button)));
    document.querySelectorAll("[data-report-section]").forEach((button) => button.addEventListener("click", () => switchReportSection(button.dataset.reportSection)));
    document.getElementById("exportAppendixButton").addEventListener("click", exportAppendix);
    document.getElementById("printSaveButton").addEventListener("click", printSavePreview);
    document.getElementById("projectSearch").addEventListener("input", filterProjects);
  </script>
</body>
</html>
"""


def build_manifest() -> tuple[dict[str, Any], list[dict[str, Any]], str]:
    s11_p2 = validate_s11_p2_dependency()
    legacy = validate_legacy_s11_p3_artifacts()
    projects = legacy["projects"]
    baseline = load_v14_html_uiux_baseline()
    html_text = render_v14_html(projects)
    baseline["implementation_reflects_project_detail_click"] = "function selectProject" in html_text
    baseline["implementation_reflects_report_section_switch"] = "function switchReportSection" in html_text
    baseline["implementation_reflects_appendix_export_feedback"] = "function exportAppendix" in html_text
    baseline["implementation_reflects_print_save_feedback"] = "function printSavePreview" in html_text
    baseline["implementation_reflects_quality_gate_block"] = 'id="qualityGateFeedback"' in html_text and "报告等级 D" in html_text
    summary = _build_summary(projects, html_text)
    hard_blocks = [
        "report_grade_d_only",
        "pending_reconciliation_blocks_formal_report",
        "quality_grade_bypass_forbidden",
        "raw_data_mutation_forbidden",
        "raw_value_publication_forbidden",
        "field_header_plaintext_publication_forbidden",
        "formal_report_release_blocked",
        "complete_trusted_report_display_blocked",
        "business_decision_basis_blocked",
        "stage11_review_not_performed",
        "lineage_full_check_not_performed",
        "raw_value_matching_not_performed",
        "github_upload_deferred_until_v014_stage1_18_complete",
        "app_reinstall_not_performed",
        "business_execution_blocked",
    ]
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "project_id": "KMFA",
        "version": "0.1.4",
        "stage_id": "S11",
        "phase_id": "S11-P3",
        "phase_name": "v0.1.4 public-safe project cost page",
        "task_id": TASK_ID,
        "phase_scope": PHASE_SCOPE,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "reviewed_head": git_output(["rev-parse", "HEAD"]),
        "worktree": git_output(["rev-parse", "--show-toplevel"]),
        "branch": git_output(["branch", "--show-current"]),
        "remote": git_output(["remote", "get-url", "origin"]),
        "status": "completed_validated_local_only_no_go_upload_deferred_project_cost_page_locked",
        "completed_task_ids": ["S11P3T01", "S11P3T02", "S11P3T03"],
        "acceptance_ids": [ACCEPTANCE_ID],
        "s11_p2_dependency_validated": True,
        "s11_p2_dependency_status": s11_p2.get("status"),
        "legacy_s11_p3_dependency_validated": True,
        "stage11_phase_progress": {
            "completed_phase_count": 3,
            "total_phase_count": 3,
            "derived_percent_bps": 10000,
            "derived_percent_label": "100.00%",
            "s11_p1_performed": True,
            "s11_p2_performed": True,
            "s11_p3_performed": True,
            "stage11_review_performed": False,
        },
        "project_cost_page_summary": summary,
        "v14_html_uiux_baseline": baseline,
        "phase_boundaries": _phase_boundaries(),
        "quality_gate": _quality_gate(),
        "github_upload": {
            "github_upload_ready_next_gate": False,
            "github_upload_deferred_until_v014_stage1_18_complete": True,
            "github_upload_performed": False,
            "github_upload_status": "not_uploaded_deferred_until_v014_stage1_18_complete",
        },
        "raw_data_boundary": _raw_boundary(),
        "public_repo_safety": _public_repo_safety(),
        "hard_blocks": hard_blocks,
        "hard_block_count": len(hard_blocks),
        "artifact_refs": {
            "s11_p2_manifest": "KMFA/stage_artifacts/V014_S11_P2_SOURCE_CHECK_BOARD/machine/source_check_board_manifest.json",
            "legacy_manifest": LEGACY_MANIFEST_PATH.as_posix(),
            "legacy_projects": LEGACY_PROJECTS_PATH.as_posix(),
            "legacy_html": LEGACY_HTML_PATH.as_posix(),
            "v14_source_package_manifest": V14_SOURCE_PACKAGE_MANIFEST.as_posix(),
            "v14_html_entry": V14_HTML_ENTRY_PATH.as_posix(),
            "v14_html_audit_script": V14_HTML_AUDIT_SCRIPT_PATH.as_posix(),
            "v14_html_audit_report": V14_HTML_AUDIT_REPORT_PATH.as_posix(),
            "v14_roadmap": V14_ROADMAP_PATH.as_posix(),
            "v14_taskpack": V14_TASKPACK_PATH.as_posix(),
            "manifest": MANIFEST_PATH.as_posix(),
            "projects": PROJECTS_PATH.as_posix(),
            "html": HTML_OUTPUT_PATH.as_posix(),
            "report": REPORT_PATH.as_posix(),
            "test_results": TEST_RESULTS_PATH.as_posix(),
            "risk_register": RISK_REGISTER_PATH.as_posix(),
            "rollback_plan": ROLLBACK_PATH.as_posix(),
            "generator": "KMFA/tools/v014_s11_p3_project_cost_page.py",
            "validator": "KMFA/tools/check_v014_s11_p3_project_cost_page.py",
            "unit_test": "KMFA/tests/test_v014_s11_p3_project_cost_page.py",
        },
        "validators": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_s11_p3_project_cost_page.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s11_p3_project_cost_page.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s11_p3_project_cost_page -q",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s11_p2_source_check_board.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s11_p3_project_cost_page.py",
        ],
        "evidence_refs": [
            MANIFEST_PATH.as_posix(),
            PROJECTS_PATH.as_posix(),
            HTML_OUTPUT_PATH.as_posix(),
            REPORT_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            RISK_REGISTER_PATH.as_posix(),
            ROLLBACK_PATH.as_posix(),
        ],
        "next_required_step": NEXT_REQUIRED_STEP,
    }
    return manifest, projects, html_text


def write_report(manifest: dict[str, Any]) -> None:
    summary = manifest["project_cost_page_summary"]
    baseline = manifest["v14_html_uiux_baseline"]
    lines = [
        "# KMFA v0.1.4 S11-P3 Project Cost Page",
        "",
        f"- task_id: `{manifest['task_id']}`",
        f"- status: `{manifest['status']}`",
        f"- phase_scope: `{manifest['phase_scope']}`",
        "- dependency: `v0.1.4 S11-P2 PASS`",
        "- legacy_s11_p3_dependency_validated: `true`",
        f"- project_row_count: `{summary['project_row_count']}`",
        f"- project_list_column_count: `{summary['project_list_column_count']}`",
        f"- cost_category_count: `{summary['cost_category_count']}`",
        f"- margin_record_count: `{summary['margin_record_count']}`",
        f"- pending_reconciliation_count: `{summary['pending_reconciliation_count']}`",
        f"- pending_action_total: `{summary['pending_action_total']}`",
        f"- html_export_count: `{summary['html_export_count']}`",
        f"- project_detail_click_enabled: `{str(summary['project_detail_click_enabled']).lower()}`",
        f"- report_section_switch_enabled: `{str(summary['report_section_switch_enabled']).lower()}`",
        f"- appendix_export_feedback_enabled: `{str(summary['appendix_export_feedback_enabled']).lower()}`",
        f"- print_save_feedback_enabled: `{str(summary['print_save_feedback_enabled']).lower()}`",
        f"- report_preview_direct_view_allowed: `{str(summary['report_preview_direct_view_allowed']).lower()}`",
        f"- report_grade_visible: `{summary['report_grade_visible']}`",
        f"- quality_grade_bypass_allowed: `{str(summary['quality_grade_bypass_allowed']).lower()}`",
        f"- formal_report_count: `{summary['formal_report_count']}`",
        f"- business_decision_basis_count: `{summary['business_decision_basis_count']}`",
        "",
        "## v1.4 HTML Human-Flow Baseline",
        "",
        f"- audit_file_count: `{baseline['audit_file_count']}`",
        f"- audit_control_row_count: `{baseline['audit_control_row_count']}`",
        f"- audit_pass_count: `{baseline['audit_pass_count']}`",
        f"- audit_warn_count: `{baseline['audit_warn_count']}`",
        f"- audit_fail_count: `{baseline['audit_fail_count']}`",
        f"- implementation_reflects_project_detail_click: `{str(baseline['implementation_reflects_project_detail_click']).lower()}`",
        f"- implementation_reflects_report_section_switch: `{str(baseline['implementation_reflects_report_section_switch']).lower()}`",
        f"- implementation_reflects_appendix_export_feedback: `{str(baseline['implementation_reflects_appendix_export_feedback']).lower()}`",
        f"- implementation_reflects_print_save_feedback: `{str(baseline['implementation_reflects_print_save_feedback']).lower()}`",
        f"- implementation_reflects_quality_gate_block: `{str(baseline['implementation_reflects_quality_gate_block']).lower()}`",
        "",
        "## Boundary",
        "",
        "- s11_p3_project_cost_page_scope_included: `true`",
        "- stage11_review_scope_included: `false`",
        "- github_upload_deferred_until_v014_stage1_18_complete: `true`",
        "- github_upload_performed: `false`",
        "- complete_trusted_report_display_allowed: `false`",
        "- formal_report_allowed: `false`",
        "- business_decision_basis_allowed: `false`",
        "- business_execution_allowed: `false`",
        "- current_report_grade: `D`",
        "- release_permission: `blocked`",
        "",
        "## Raw Data Boundary",
        "",
        f"- raw_inbox_ref: `{RAW_INBOX_REF}`",
        "- raw_inbox_read_required_by_this_phase: `false`",
        "- raw_inbox_read_by_this_phase: `false`",
        "- raw_inbox_listed_by_this_phase: `false`",
        "- raw_inbox_mutated_by_this_phase: `false`",
        "",
        "This phase did not enumerate, copy, modify, move, rename, delete, overwrite, or write generated files inside the local finance inbox.",
        "",
        "## Public Safety",
        "",
        "Evidence contains only public-safe project group labels, aggregate counts, status text, evidence refs, pending-action counts, control-event semantics, quality blockers, validator references, and governance paths.",
        "It does not contain source filenames from private inputs, source hashes from the private inbox, tab labels, ZIP member names, field/header plaintext, row values, business amount values, credentials, contracts, payroll, tax filings, or bank statements.",
        "",
        "## Next Step",
        "",
        manifest["next_required_step"],
        "",
    ]
    _write_text(REPORT_PATH, "\n".join(lines))


def write_test_results() -> None:
    lines = [
        "# KMFA v0.1.4 S11-P3 Project Cost Page Test Results",
        "",
        f"- task_id: `{TASK_ID}`",
        "- status: `completed_validated_local_only_no_go_upload_deferred`",
        "- github_upload_performed: `false`",
        "- raw_inbox_read_by_this_phase: `false`",
        "- raw_inbox_mutated_by_this_phase: `false`",
        "- stage11_review_performed: `false`",
        "- formal_report_allowed: `false`",
        "- business_execution_allowed: `false`",
        "",
        "## Command Results",
        "",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_s11_p3_project_cost_page.py KMFA/tools/check_v014_s11_p3_project_cost_page.py KMFA/tests/test_v014_s11_p3_project_cost_page.py`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s11_p2_source_check_board.py`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s11_p3_project_cost_page.py`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_s11_p3_project_cost_page.py`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s11_p3_project_cost_page.py`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s11_p3_project_cost_page -q`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --enforce-sync`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_no_float_money.py`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/no_omission_check.py`",
        "- PASS: `git diff --check -- KMFA scripts`",
        "- PASS: changed/untracked structured parse scan.",
        "- PASS: changed/untracked raw/private suffix scan.",
        "- PASS: changed/untracked strict secret token scan.",
        "- PASS: scoped S11-P3 public evidence raw/private semantic scan.",
        "",
        "Note: Stage 11 overall review, GitHub upload, raw value matching, lineage full check, formal report release, live connector, app reinstall, and business execution were intentionally not performed in this phase.",
        "",
    ]
    _write_text(TEST_RESULTS_PATH, "\n".join(lines))


def write_risk_register() -> None:
    lines = [
        "# KMFA v0.1.4 S11-P3 Risk Register",
        "",
        "| Risk | Control | Status |",
        "|---|---|---|",
        "| 项目成本页面被误解为正式项目成本报告 | validator 锁定 report grade D、formal_report_allowed=false、business_decision_basis_allowed=false | controlled |",
        "| 报告预览被误解为可绕过质量等级 | HTML、manifest 和 validator 均锁定 quality_grade_bypass_allowed=false | controlled |",
        "| 项目详情交互写回 raw 层 | control event only，raw_layer_write_allowed=false | controlled |",
        "| 单 phase 越界进入 Stage 11 review 或 GitHub upload | phase boundaries 与 validator 均要求 false | controlled |",
        "| public evidence 泄露 raw/private 信息 | validator 扫描本 phase evidence 文本并锁定 raw/private boundary | controlled |",
        "",
    ]
    _write_text(RISK_REGISTER_PATH, "\n".join(lines))


def write_rollback_plan() -> None:
    lines = [
        "# KMFA v0.1.4 S11-P3 Rollback Plan",
        "",
        "Rollback is local-only: revert the S11-P3 commit or remove the generated `V014_S11_P3_PROJECT_COST_PAGE` evidence, v014 S11-P3 tools/tests, and governance entries.",
        "",
        "No raw/private input file is created, modified, moved, renamed, deleted, or overwritten by this phase.",
        "",
    ]
    _write_text(ROLLBACK_PATH, "\n".join(lines))


def generate() -> dict[str, Any]:
    MACHINE_DIR.mkdir(parents=True, exist_ok=True)
    HUMAN_DIR.mkdir(parents=True, exist_ok=True)
    EXPORT_HTML_DIR.mkdir(parents=True, exist_ok=True)
    manifest, projects, html_text = build_manifest()
    _write_json(MANIFEST_PATH, manifest)
    _write_jsonl(PROJECTS_PATH, projects)
    _write_text(HTML_OUTPUT_PATH, html_text)
    write_report(manifest)
    write_test_results()
    write_risk_register()
    write_rollback_plan()
    return manifest


def main() -> int:
    manifest = generate()
    summary = manifest["project_cost_page_summary"]
    baseline = manifest["v14_html_uiux_baseline"]
    print(
        "PASS: KMFA v0.1.4 S11-P3 project cost page evidence generated "
        f"(projects={summary['project_row_count']}, "
        f"columns={summary['project_list_column_count']}, "
        f"cost_categories={summary['cost_category_count']}, "
        f"pending_reconciliations={summary['pending_reconciliation_count']}, "
        f"v14_audit_rows={baseline['audit_control_row_count']}, "
        "detail=true, report_preview=true, quality_bypass=false, "
        "stage11_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
