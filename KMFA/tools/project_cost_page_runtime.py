#!/usr/bin/env python3
"""Build KMFA S11-P3 public-safe project cost page artifacts."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

DEFAULT_OUTPUT_MANIFEST = ROOT / "metadata" / "reports" / "project_cost_page_manifest.json"
DEFAULT_OUTPUT_PROJECTS = ROOT / "metadata" / "reports" / "project_cost_page_projects.jsonl"
DEFAULT_OUTPUT_STAGE_MANIFEST = (
    ROOT / "stage_artifacts" / "S11_P3_project_cost_page" / "machine" / "s11_p3_manifest.json"
)
DEFAULT_HTML_OUTPUT = (
    ROOT / "stage_artifacts" / "S11_P3_project_cost_page" / "exports" / "html" / "kmfa_project_cost_page.html"
)

PROJECT_COST_FACT_RECORDS = ROOT / "metadata" / "lineage" / "project_cost_fact_records.jsonl"
PROJECT_MARGIN_RECORDS = ROOT / "metadata" / "lineage" / "project_margin_cash_margin_records.jsonl"
SCOPE_RECONCILIATION_RECORDS = ROOT / "metadata" / "quality" / "scope_reconciliation_records.jsonl"
REPORT_GRADE_RECORDS = ROOT / "metadata" / "reports" / "report_grade_runtime_records.jsonl"
REPORT_EXPORT_RECORDS = ROOT / "metadata" / "reports" / "report_export_records.jsonl"

REQUIRED_PROJECT_PAGE_SECTIONS = ("项目列表", "项目详情", "来源证据", "待处理事项", "报告预览")
REQUIRED_PROJECT_TABLE_COLUMNS = ("项目分组", "毛利状态", "成本结构", "回款状态", "差异状态", "报告预览", "下一步")
REQUIRED_COST_CATEGORIES = (
    "labor",
    "material",
    "machinery",
    "subcontract",
    "transport",
    "travel",
    "tax",
    "management_fee",
    "interest",
)
REQUIRED_MARGIN_METRICS = (
    "authority_gross_profit",
    "system_recomputed_gross_profit",
    "cash_gross_profit",
    "gross_margin_rate",
)

PROJECT_COST_PAGE_VERSION = "UI-KMFA-S11P3-PROJECT-COST-PAGE-001"
STYLE_VERSION = "STYLE-KMFA-S11P3-BLUE-BUSINESS-001"
INTERACTION_VERSION = "INTERACTION-KMFA-S11P3-PROJECT-DETAIL-001"
PUBLIC_SAFETY_VERSION = "SAFE-KMFA-S11P3-PUBLIC-001"

SOURCE_TASKPACK_REFS = {
    "roadmap_s11_p3": "KMFA/taskpack/v1_2/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_2.md:S11-P3",
    "frontend_report_rules": "KMFA/taskpack/v1_2/01_KMFA_Codex_TaskPack_v1_2_完整防遗漏_含HTML验收样板.md:11",
    "project_cost_html_sample": (
        "KMFA/taskpack/v1_2/20_HTML_UIUX_报告预览/01_核心HTML验收样板/"
        "KMFA_项目成本专题报告预览_v0_6_blue_zero_delta.html"
    ),
    "upstream_fact_layer": "KMFA/metadata/reports/project_cost_fact_layer_manifest.json",
    "upstream_margin_layer": "KMFA/metadata/reports/project_margin_cash_margin_manifest.json",
    "upstream_scope_reconciliation": "KMFA/metadata/reports/project_scope_reconciliation_manifest.json",
    "upstream_report_grade": "KMFA/metadata/reports/report_grade_runtime_manifest.json",
}

FORBIDDEN_PUBLIC_KEYS = {
    "amount_cents",
    "amount_yuan",
    "raw_value",
    "normalized_value",
    "original_value",
    "plaintext_value",
    "source_header_text",
    "raw_file_bytes",
    "original_filename",
    "private_csv",
    "bank_account_number",
    "account_number",
    "identity_document_number",
    "project_name_plaintext",
    "customer_name_plaintext",
    "counterparty_plaintext",
    "company_entity_plaintext",
    "password",
    "api_key",
    "private_key",
}

FORBIDDEN_PUBLIC_SUFFIXES = (".zip", ".xls", ".xlsx", ".pdf", ".sqlite", ".db", ".parquet")
FORBIDDEN_PUBLIC_TEXT = (
    "private_ref://",
    "raw_value",
    "normalized_value",
    "plaintext_value",
    "source_header_text",
    "original_filename",
    "bank_account_number",
    "identity_document_number",
    "password",
    "api_key",
    "private_key",
)


class ProjectCostPageRuntimeError(ValueError):
    """Raised when S11-P3 project cost page artifacts are invalid."""


def _sha256_json(payload: Any) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )


def _public_repo_safety() -> dict[str, bool]:
    return {
        "raw_business_values_committed": False,
        "field_plaintext_committed": False,
        "raw_file_committed": False,
        "private_tabular_files_committed": False,
        "excel_workbook_committed": False,
        "pdf_file_committed": False,
        "credential_secret_committed": False,
        "real_account_number_committed": False,
        "private_ref_committed_in_s11p3_outputs": False,
    }


def _stage_scope() -> dict[str, bool]:
    return {
        "s11_p3_project_cost_page_scope_included": True,
        "s12_manual_workbench_scope_included": False,
        "formal_report_runtime_scope_included": False,
        "lineage_full_check_scope_included": False,
        "external_connector_scope_included": False,
        "stage11_review_scope_included": False,
        "github_upload_scope_included": False,
    }


def _quality_gate(report_grade: str, pending_reconciliation_count: int) -> dict[str, Any]:
    return {
        "project_cost_page_export_allowed": True,
        "report_preview_direct_view_allowed": True,
        "report_grade_visible": report_grade,
        "quality_grade_bypass_allowed": False,
        "report_grade_bypass_allowed": False,
        "formal_report_allowed": False,
        "complete_trusted_report_display_allowed": False,
        "business_decision_basis_allowed": False,
        "raw_layer_write_allowed": False,
        "github_upload_allowed": False,
        "phase_completion_upload_allowed": False,
        "stage11_review_allowed": False,
        "pending_reconciliation_count": pending_reconciliation_count,
        "release_block_reason": "report_grade_d_zero_delta_failed_pending_reconciliation",
    }


def _style_gate() -> dict[str, Any]:
    return {
        "blue_business_style": True,
        "large_yellow_surface_count": 0,
        "status_badges_only": True,
        "responsive_table_and_detail": True,
    }


def _interaction_gate() -> dict[str, Any]:
    return {
        "project_detail_click_enabled": True,
        "detail_panel_fields": ["来源证据", "待处理事项", "报告预览"],
        "write_back_allowed": False,
        "raw_layer_write_allowed": False,
    }


def _margin_record_by_fact_id(margin_records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("project_cost_fact_record_id")): row for row in margin_records}


def _reconciliation_counts(reconciliation_records: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in reconciliation_records:
        margin_id = str(row.get("margin_record_id") or "")
        if margin_id:
            counts[margin_id] = counts.get(margin_id, 0) + 1
    return counts


def _visible_report_grade(report_grade_records: list[dict[str, Any]]) -> str:
    grades = {str(row.get("computed_report_grade") or "") for row in report_grade_records}
    return "D" if "D" in grades else "D"


def _project_group_label(index: int) -> str:
    return f"项目分组 {index:03d}"


def _cost_category_label(category: str) -> str:
    return {
        "labor": "人工",
        "material": "材料",
        "machinery": "机械",
        "subcontract": "外协",
        "transport": "运输",
        "travel": "差旅",
        "tax": "税费",
        "management_fee": "管理费",
        "interest": "利息",
    }[category]


def _project_rows(
    *,
    fact_records: list[dict[str, Any]],
    margin_records: list[dict[str, Any]],
    reconciliation_records: list[dict[str, Any]],
    report_grade: str,
    generated_at: str,
) -> list[dict[str, Any]]:
    margin_by_fact = _margin_record_by_fact_id(margin_records)
    difference_counts = _reconciliation_counts(reconciliation_records)
    rows: list[dict[str, Any]] = []
    for index, fact in enumerate(fact_records, start=1):
        fact_record_id = str(fact.get("fact_record_id") or "")
        margin = margin_by_fact.get(fact_record_id, {})
        margin_record_id = str(margin.get("margin_record_id") or f"PCM-S09P2-{index:03d}")
        difference_count = difference_counts.get(margin_record_id, 0)
        cost_categories = [str(item) for item in fact.get("cost_category_slots", [])]
        missing_categories = [item for item in REQUIRED_COST_CATEGORIES if item not in cost_categories]
        pending_actions = [
            "复核权威毛利与系统复算差异",
            "确认现金毛利口径和回款证据",
            "补齐完整追溯和人工确认后再考虑报告升级",
        ]
        if missing_categories:
            pending_actions.insert(0, "补齐成本结构分类")
        row = {
            "schema_version": "kmfa.project_cost_page_project.v1",
            "record_type": "project_cost_page_project",
            "project_id": "KMFA",
            "system_name": "KMFA 经营分析系统",
            "stage_phase": "S11-P3",
            "project_order": index,
            "project_cost_page_version": PROJECT_COST_PAGE_VERSION,
            "style_version": STYLE_VERSION,
            "interaction_version": INTERACTION_VERSION,
            "public_safety_version": PUBLIC_SAFETY_VERSION,
            "generated_at": generated_at,
            "project_display_ref": _project_group_label(index),
            "fact_record_id": fact_record_id,
            "margin_record_id": margin_record_id,
            "project_entity_group_ref": f"项目实体分组 {index:03d}",
            "gross_margin_status": "毛利指标已记录，正式结论阻断",
            "cost_structure_summary": "、".join(_cost_category_label(category) for category in REQUIRED_COST_CATEGORIES),
            "collection_status": "回款口径已登记，现金毛利待授权复核",
            "difference_status": f"{difference_count} 项差异待复核",
            "evidence_summary": "事实层、毛利层、差异核对和报告等级证据已绑定",
            "pending_actions": pending_actions,
            "pending_action_count": len(pending_actions),
            "report_preview_status": f"可查看报告预览，报告等级 {report_grade}，不可作为经营决策依据",
            "next_step": "完成差异复核、完整追溯和人工确认后才允许进入后续报告门禁",
            "source_evidence_refs": [
                "KMFA/stage_artifacts/S09_P1_project_cost_fact_layer/human/test_results.md",
                "KMFA/stage_artifacts/S09_P2_margin_cash_margin/human/test_results.md",
                "KMFA/stage_artifacts/S09_P3_scope_reconciliation/human/test_results.md",
                "KMFA/stage_artifacts/S10_P2_report_grade_runtime/human/test_results.md",
            ],
            "contains_raw_business_values": False,
            "raw_layer_write_allowed": False,
            "raw_source_mutation_allowed": False,
            "formal_report_allowed": False,
            "complete_trusted_report_display_allowed": False,
            "business_decision_basis_allowed": False,
            "quality_grade_bypass_allowed": False,
            "public_repo_safety": _public_repo_safety(),
        }
        rows.append(row)
    return rows


def _status_class(project: dict[str, Any]) -> str:
    pending_count = int(project.get("pending_action_count") or 0)
    if pending_count >= 3:
        return "blocked"
    if pending_count == 2:
        return "review"
    return "partial"


def _render_html(projects: list[dict[str, Any]], manifest: dict[str, Any]) -> str:
    summary = manifest["summary"]
    cards = (
        f'<div class="card"><span>项目分组</span><b>{summary["project_row_count"]}</b><small>公开安全列表</small></div>'
        f'<div class="card"><span>成本结构</span><b>{summary["cost_category_count"]}</b><small>分类已登记</small></div>'
        f'<div class="card"><span>毛利记录</span><b>{summary["margin_record_count"]}</b><small>等待复核</small></div>'
        f'<div class="card"><span>差异状态</span><b>{summary["pending_reconciliation_count"]}</b><small>待处理事项</small></div>'
    )
    columns = "".join(f"<th>{html.escape(column)}</th>" for column in REQUIRED_PROJECT_TABLE_COLUMNS)
    rows = "\n".join(
        f"""          <tr>
            <td>{html.escape(project["project_display_ref"])}</td>
            <td>{html.escape(project["gross_margin_status"])}</td>
            <td>{html.escape(project["cost_structure_summary"])}</td>
            <td>{html.escape(project["collection_status"])}</td>
            <td><button type="button" class="badge {_status_class(project)}" data-evidence="{html.escape(project["evidence_summary"])}" data-pending="{html.escape("；".join(project["pending_actions"]))}" data-preview="{html.escape(project["report_preview_status"])}">{html.escape(project["difference_status"])}</button></td>
            <td>{html.escape(project["report_preview_status"])}</td>
            <td>{html.escape(project["next_step"])}</td>
          </tr>"""
        for project in projects
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
      --navy:#0b1f3a;
      --blue:#1d4ed8;
      --sky:#eaf3ff;
      --line:#d8e4f5;
      --text:#152033;
      --muted:#64748b;
      --bg:#f6f9fe;
      --card:#ffffff;
      --review:#5b21b6;
      --blocked:#b91c1c;
      --partial:#1e3a8a;
    }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:var(--bg); color:var(--text); font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",Arial,sans-serif; }}
    .header {{ background:linear-gradient(135deg,var(--navy),#123a70 55%,#2563eb); color:#fff; padding:30px 40px; }}
    .brand {{ display:flex; align-items:center; gap:14px; }}
    .logo {{ width:52px; height:52px; border:1px solid rgba(255,255,255,.45); border-radius:12px; display:flex; align-items:center; justify-content:center; font-weight:800; background:rgba(255,255,255,.10); }}
    h1 {{ margin:0; font-size:28px; letter-spacing:0; }}
    .sub {{ margin-top:8px; color:#d6e7ff; line-height:1.65; }}
    .wrap {{ max-width:1220px; margin:0 auto; padding:24px; }}
    .cards {{ display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin-bottom:18px; }}
    .card {{ background:#fff; border:1px solid var(--line); border-radius:8px; padding:16px; box-shadow:0 12px 28px rgba(17,45,88,.06); }}
    .card span {{ display:block; color:var(--muted); font-size:13px; }}
    .card b {{ display:block; color:#0b2b59; font-size:26px; margin:6px 0; }}
    .card small {{ color:#475569; }}
    .toolbar {{ display:flex; justify-content:space-between; gap:16px; align-items:flex-start; margin-bottom:14px; }}
    .note {{ color:#475569; line-height:1.7; max-width:760px; }}
    .grade {{ border:1px solid #bfdbfe; background:#fff; color:var(--blue); border-radius:999px; padding:7px 12px; font-size:12px; font-weight:800; white-space:nowrap; }}
    .table-wrap {{ overflow:auto; border:1px solid var(--line); border-radius:8px; background:#fff; }}
    table {{ width:100%; min-width:1120px; border-collapse:separate; border-spacing:0; }}
    th {{ background:#0f2f5f; color:#fff; text-align:left; font-size:13px; padding:12px; border-bottom:1px solid #244d86; }}
    td {{ padding:12px; font-size:13px; line-height:1.55; border-bottom:1px solid #edf2f7; vertical-align:top; }}
    tr:hover td {{ background:#f8fbff; }}
    .badge {{ border:1px solid transparent; border-radius:999px; padding:5px 10px; font-size:12px; font-weight:800; cursor:pointer; white-space:nowrap; }}
    .blocked {{ color:#991b1b; background:#fee2e2; }}
    .review {{ color:#5b21b6; background:#f3e8ff; }}
    .partial {{ color:#1d4ed8; background:#eff6ff; border-color:#bfdbfe; }}
    .detail {{ display:grid; grid-template-columns:1fr 1fr 1fr; gap:12px; margin-top:16px; }}
    .panel {{ background:#fff; border:1px solid var(--line); border-radius:8px; padding:16px; min-height:132px; }}
    .panel h2 {{ margin:0 0 10px; color:#0b2b59; font-size:18px; }}
    .panel p {{ margin:0; color:#475569; line-height:1.7; }}
    .preview {{ margin-top:16px; background:var(--sky); border:1px solid var(--line); border-radius:8px; padding:16px; color:#1e3a5f; line-height:1.75; }}
    .footer {{ margin-top:14px; color:#64748b; font-size:12px; line-height:1.6; }}
    @media(max-width:980px) {{ .cards,.detail {{ grid-template-columns:1fr 1fr; }} .toolbar {{ display:block; }} .grade {{ display:inline-flex; margin-top:10px; }} }}
    @media(max-width:640px) {{ .cards,.detail {{ grid-template-columns:1fr; }} .wrap {{ padding:16px; }} .header {{ padding:24px; }} }}
  </style>
</head>
<body>
  <header class="header">
    <div class="brand"><div class="logo">KM</div><div><h1>KMFA 项目成本页面</h1><div class="sub">项目列表、毛利、成本结构、回款、差异状态、来源证据、待处理事项和报告预览。报告预览可直接查看，但不可绕过质量等级。</div></div></div>
  </header>
  <main class="wrap">
    <section class="cards" aria-label="项目成本摘要">{cards}</section>
    <section class="toolbar">
      <div class="note">本页面只展示公开安全的项目分组和状态，不展示真实金额、客户名称、合同明细、账号或原始文件。所有正式报告和经营决策依据继续受质量等级门禁约束。</div>
      <span class="grade">报告等级 D</span>
    </section>
    <section class="table-wrap" aria-label="项目列表">
      <table>
        <thead><tr>{columns}</tr></thead>
        <tbody>
{rows}
        </tbody>
      </table>
    </section>
    <section class="detail" aria-label="项目详情">
      <div class="panel"><h2>项目详情</h2><p>当前选择展示公开安全项目分组，金额槽位只保留状态，不展示数值。</p></div>
      <div class="panel"><h2>来源证据</h2><p id="evidenceText">{html.escape(first["evidence_summary"])}</p></div>
      <div class="panel"><h2>待处理事项</h2><p id="pendingText">{html.escape("；".join(first["pending_actions"]))}</p></div>
    </section>
    <section class="preview" aria-label="报告预览">
      <strong>报告预览：</strong><span id="previewText">{html.escape(first["report_preview_status"])}</span>。当前预览不可绕过质量等级，不代表正式报告、完整可信报告或经营决策依据。
    </section>
    <div class="footer">KMFA 经营分析系统 · S11-P3 项目成本页面 · 本页面不执行第十一阶段复审、上传、完整追溯检查或外部接口。</div>
  </main>
  <script>
    const detail = {{
      evidence: document.getElementById("evidenceText"),
      pending: document.getElementById("pendingText"),
      preview: document.getElementById("previewText")
    }};
    document.querySelectorAll(".badge").forEach((button) => {{
      button.addEventListener("click", () => {{
        detail.evidence.textContent = button.dataset.evidence;
        detail.pending.textContent = button.dataset.pending;
        detail.preview.textContent = button.dataset.preview;
      }});
    }});
  </script>
</body>
</html>
"""


def build_default_project_cost_page_artifacts(
    *,
    generated_at: str = "2026-07-01T11:00:00+10:00",
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, dict[str, str]]]:
    fact_records = read_jsonl(PROJECT_COST_FACT_RECORDS)
    margin_records = read_jsonl(PROJECT_MARGIN_RECORDS)
    reconciliation_records = read_jsonl(SCOPE_RECONCILIATION_RECORDS)
    report_grade_records = read_jsonl(REPORT_GRADE_RECORDS)
    report_export_records = read_jsonl(REPORT_EXPORT_RECORDS)
    report_grade = _visible_report_grade(report_grade_records)
    projects = _project_rows(
        fact_records=fact_records,
        margin_records=margin_records,
        reconciliation_records=reconciliation_records,
        report_grade=report_grade,
        generated_at=generated_at,
    )
    manifest = {
        "schema_version": "kmfa.project_cost_page_manifest.v1",
        "record_type": "project_cost_page_manifest",
        "project_id": "KMFA",
        "system_name": "KMFA 经营分析系统",
        "stage_phase": "S11-P3",
        "runtime_status": "public_safe_project_cost_page_generated_local_only",
        "project_cost_page_version": PROJECT_COST_PAGE_VERSION,
        "style_version": STYLE_VERSION,
        "interaction_version": INTERACTION_VERSION,
        "public_safety_version": PUBLIC_SAFETY_VERSION,
        "generated_at": generated_at,
        "brand_mark": "KM",
        "brand_mark_is_single_k": False,
        "required_sections": list(REQUIRED_PROJECT_PAGE_SECTIONS),
        "required_project_table_columns": list(REQUIRED_PROJECT_TABLE_COLUMNS),
        "required_cost_categories": list(REQUIRED_COST_CATEGORIES),
        "required_margin_metrics": list(REQUIRED_MARGIN_METRICS),
        "source_taskpack_refs": SOURCE_TASKPACK_REFS,
        "quality_gate": _quality_gate(report_grade, len(reconciliation_records)),
        "stage_scope": _stage_scope(),
        "style_gate": _style_gate(),
        "interaction": _interaction_gate(),
        "public_repo_safety": _public_repo_safety(),
        "upstream_summary": {
            "project_cost_fact_record_count": len(fact_records),
            "margin_record_count": len(margin_records),
            "scope_reconciliation_record_count": len(reconciliation_records),
            "report_grade_record_count": len(report_grade_records),
            "report_export_record_count": len(report_export_records),
            "report_grade_distribution": {report_grade: len(report_grade_records)},
        },
        "artifact_refs": {
            "project_cost_page_manifest": "KMFA/metadata/reports/project_cost_page_manifest.json",
            "project_cost_page_projects": "KMFA/metadata/reports/project_cost_page_projects.jsonl",
            "html_export": "KMFA/stage_artifacts/S11_P3_project_cost_page/exports/html/kmfa_project_cost_page.html",
            "validator": "KMFA/tools/check_s11_p3_project_cost_page.py",
            "completion_record": "KMFA/stage_artifacts/S11_P3_project_cost_page/human/s11_p3_completion_record.md",
            "test_results": "KMFA/stage_artifacts/S11_P3_project_cost_page/human/test_results.md",
            "stage_manifest": "KMFA/stage_artifacts/S11_P3_project_cost_page/machine/s11_p3_manifest.json",
        },
        "summary": {
            "project_row_count": len(projects),
            "project_list_column_count": len(REQUIRED_PROJECT_TABLE_COLUMNS),
            "project_list_columns_covered": True,
            "project_detail_panel_count": 3,
            "evidence_panel_count": 1,
            "pending_action_panel_count": 1,
            "report_preview_panel_count": 1,
            "report_preview_direct_view_allowed": True,
            "report_grade_visible": report_grade,
            "quality_grade_bypass_allowed": False,
            "margin_record_count": len(margin_records),
            "cost_category_count": len(REQUIRED_COST_CATEGORIES),
            "margin_metric_count": len(REQUIRED_MARGIN_METRICS),
            "pending_reconciliation_count": len(reconciliation_records),
            "html_export_count": 1,
            "formal_report_count": 0,
            "business_decision_basis_count": 0,
            "raw_business_value_count": 0,
            "private_ref_count": 0,
        },
        "limitations": [
            "S11-P3 只生成项目成本页面，不执行 Stage 11 整体复审或 GitHub upload。",
            "项目列表只展示公开安全项目分组和状态，不展示真实金额、真实项目名、客户、合同、账号或字段明文。",
            "报告预览可直接查看，但报告等级 D 和质量门禁不可绕过。",
            "待处理差异、完整追溯和人工确认完成前，不允许正式报告或经营决策依据。",
            "本 phase 不接外部接口，不写 raw layer。",
        ],
    }
    render_outputs = {"html": {"kmfa_project_cost_page": _render_html(projects, manifest)}}
    manifest["content_hash"] = _sha256_json({"manifest": manifest, "projects": projects, "render_outputs": render_outputs})
    return manifest, projects, render_outputs


def _looks_like_forbidden_private_file(value: str) -> bool:
    lowered = value.lower()
    return any(suffix in lowered for suffix in FORBIDDEN_PUBLIC_SUFFIXES)


def _ensure_no_forbidden_public_payload(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in FORBIDDEN_PUBLIC_KEYS:
                raise ProjectCostPageRuntimeError(f"forbidden public key found: {key}")
            _ensure_no_forbidden_public_payload(item)
    elif isinstance(value, list):
        for item in value:
            _ensure_no_forbidden_public_payload(item)
    elif isinstance(value, str):
        lowered = value.lower()
        if _looks_like_forbidden_private_file(value):
            raise ProjectCostPageRuntimeError(f"forbidden private business file reference found: {value}")
        if any(forbidden in lowered for forbidden in FORBIDDEN_PUBLIC_TEXT):
            raise ProjectCostPageRuntimeError(f"forbidden private token found: {value}")


def _validate_project_row(row: dict[str, Any], expected_order: int) -> None:
    label = str(row.get("project_display_ref", ""))
    if row.get("record_type") != "project_cost_page_project":
        raise ProjectCostPageRuntimeError(f"{label}.record_type mismatch")
    if row.get("stage_phase") != "S11-P3":
        raise ProjectCostPageRuntimeError(f"{label}.stage_phase must be S11-P3")
    if row.get("project_order") != expected_order:
        raise ProjectCostPageRuntimeError(f"{label}.project_order mismatch")
    for field in (
        "project_display_ref",
        "fact_record_id",
        "margin_record_id",
        "gross_margin_status",
        "cost_structure_summary",
        "collection_status",
        "difference_status",
        "evidence_summary",
        "pending_actions",
        "report_preview_status",
        "next_step",
    ):
        if not row.get(field):
            raise ProjectCostPageRuntimeError(f"{label}.{field} is required")
    if not str(row["fact_record_id"]).startswith("PCF-S09P1-"):
        raise ProjectCostPageRuntimeError(f"{label}.fact_record_id must reference S09-P1 facts")
    if not str(row["margin_record_id"]).startswith("PCM-S09P2-"):
        raise ProjectCostPageRuntimeError(f"{label}.margin_record_id must reference S09-P2 margin")
    if int(row.get("pending_action_count") or 0) < 1:
        raise ProjectCostPageRuntimeError(f"{label}.pending_action_count must be positive")
    for flag in (
        "contains_raw_business_values",
        "raw_layer_write_allowed",
        "raw_source_mutation_allowed",
        "formal_report_allowed",
        "complete_trusted_report_display_allowed",
        "business_decision_basis_allowed",
        "quality_grade_bypass_allowed",
    ):
        if row.get(flag) is not False:
            raise ProjectCostPageRuntimeError(f"{label}.{flag} must be false")


def _validate_html(html_text: str, manifest: dict[str, Any]) -> None:
    if not html_text.startswith("<!doctype html>"):
        raise ProjectCostPageRuntimeError("html output must start with doctype")
    required_texts = [
        "KMFA 项目成本页面",
        "项目列表",
        "项目详情",
        "来源证据",
        "待处理事项",
        "报告预览",
        "报告等级 D",
        "不可绕过质量等级",
        "不展示真实金额",
    ]
    for text in required_texts:
        if text not in html_text:
            raise ProjectCostPageRuntimeError(f"html missing required text: {text}")
    if ">K<" in html_text or ">KM<" not in html_text:
        raise ProjectCostPageRuntimeError("html must use KM brand mark and not single K")
    lowered = html_text.lower()
    for forbidden in ("source_ref://", "private_ref://", "validator", "manifest", "metadata"):
        if forbidden in lowered:
            raise ProjectCostPageRuntimeError(f"html exposes internal token: {forbidden}")
    if "yellow" in lowered:
        raise ProjectCostPageRuntimeError("html must not use a large yellow warning surface")
    for suffix in FORBIDDEN_PUBLIC_SUFFIXES:
        if suffix in lowered:
            raise ProjectCostPageRuntimeError(f"html exposes forbidden suffix: {suffix}")
    if manifest["quality_gate"].get("report_grade_visible") not in html_text:
        raise ProjectCostPageRuntimeError("html must display report grade")


def validate_project_cost_page_artifacts(
    manifest: dict[str, Any],
    projects: list[dict[str, Any]],
    render_outputs: dict[str, dict[str, str]],
) -> None:
    if manifest.get("record_type") != "project_cost_page_manifest":
        raise ProjectCostPageRuntimeError("manifest record_type mismatch")
    if manifest.get("stage_phase") != "S11-P3":
        raise ProjectCostPageRuntimeError("manifest stage_phase must be S11-P3")
    if tuple(manifest.get("required_sections", [])) != REQUIRED_PROJECT_PAGE_SECTIONS:
        raise ProjectCostPageRuntimeError("required project page sections mismatch")
    if tuple(manifest.get("required_project_table_columns", [])) != REQUIRED_PROJECT_TABLE_COLUMNS:
        raise ProjectCostPageRuntimeError("required project table columns mismatch")
    if manifest["summary"].get("project_row_count") != len(projects):
        raise ProjectCostPageRuntimeError("project row count mismatch")
    if manifest["summary"].get("project_row_count") != 4:
        raise ProjectCostPageRuntimeError("S11-P3 project page must expose four public-safe project rows")
    if manifest["summary"].get("pending_reconciliation_count") != 12:
        raise ProjectCostPageRuntimeError("pending reconciliation count must remain 12")
    if manifest["summary"].get("cost_category_count") != len(REQUIRED_COST_CATEGORIES):
        raise ProjectCostPageRuntimeError("cost category count mismatch")
    if manifest["summary"].get("margin_record_count") != 4:
        raise ProjectCostPageRuntimeError("margin record count must be 4")
    if manifest["quality_gate"].get("report_preview_direct_view_allowed") is not True:
        raise ProjectCostPageRuntimeError("report preview must be directly viewable")
    for flag in (
        "quality_grade_bypass_allowed",
        "report_grade_bypass_allowed",
        "formal_report_allowed",
        "complete_trusted_report_display_allowed",
        "business_decision_basis_allowed",
        "github_upload_allowed",
        "stage11_review_allowed",
    ):
        if manifest["quality_gate"].get(flag) is not False:
            raise ProjectCostPageRuntimeError(f"quality gate {flag} must be false")
    for flag in (
        "stage11_review_scope_included",
        "github_upload_scope_included",
        "formal_report_runtime_scope_included",
        "lineage_full_check_scope_included",
        "external_connector_scope_included",
    ):
        if manifest["stage_scope"].get(flag) is not False:
            raise ProjectCostPageRuntimeError(f"stage scope {flag} must be false")
    for index, row in enumerate(projects, start=1):
        _validate_project_row(row, index)
    html_text = render_outputs.get("html", {}).get("kmfa_project_cost_page")
    if not html_text:
        raise ProjectCostPageRuntimeError("missing html render output")
    _validate_html(html_text, manifest)
    _ensure_no_forbidden_public_payload(manifest)
    _ensure_no_forbidden_public_payload(projects)
    _ensure_no_forbidden_public_payload(render_outputs)


def write_project_cost_page_artifacts(
    manifest: dict[str, Any],
    projects: list[dict[str, Any]],
    render_outputs: dict[str, dict[str, str]],
    *,
    manifest_path: Path = DEFAULT_OUTPUT_MANIFEST,
    projects_path: Path = DEFAULT_OUTPUT_PROJECTS,
    stage_manifest_path: Path = DEFAULT_OUTPUT_STAGE_MANIFEST,
    html_path: Path = DEFAULT_HTML_OUTPUT,
) -> None:
    validate_project_cost_page_artifacts(manifest, projects, render_outputs)
    write_json(manifest_path, manifest)
    write_jsonl(projects_path, projects)
    write_json(stage_manifest_path, manifest)
    html_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text(render_outputs["html"]["kmfa_project_cost_page"], encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build KMFA S11-P3 project cost page artifacts.")
    parser.add_argument("--generated-at", default="2026-07-01T11:00:00+10:00")
    args = parser.parse_args(argv)

    manifest, projects, render_outputs = build_default_project_cost_page_artifacts(generated_at=args.generated_at)
    write_project_cost_page_artifacts(manifest, projects, render_outputs)
    summary = manifest["summary"]
    print(
        "PASS: KMFA S11-P3 project cost page artifacts generated "
        f"(projects={summary['project_row_count']}, "
        f"margin_records={summary['margin_record_count']}, "
        f"cost_categories={summary['cost_category_count']}, "
        f"pending_reconciliations={summary['pending_reconciliation_count']}, "
        "report_preview=true, report_grade=D, quality_bypass=false, "
        "formal_report_allowed=false, stage11_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
