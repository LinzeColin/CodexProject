#!/usr/bin/env python3
"""Build KMFA S11-P1 public-safe home navigation artifacts."""

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

DEFAULT_OUTPUT_MANIFEST = ROOT / "metadata" / "reports" / "home_navigation_manifest.json"
DEFAULT_OUTPUT_RECORDS = ROOT / "metadata" / "reports" / "home_navigation_modules.jsonl"
DEFAULT_OUTPUT_STAGE_MANIFEST = (
    ROOT / "stage_artifacts" / "S11_P1_home_navigation" / "machine" / "s11_p1_manifest.json"
)
DEFAULT_HTML_OUTPUT = ROOT / "stage_artifacts" / "S11_P1_home_navigation" / "exports" / "html" / "kmfa_home_navigation.html"

REQUIRED_NAVIGATION_LABELS = (
    "经营总览",
    "项目成本",
    "回款应收",
    "财务资金",
    "开票纳税",
    "数据源检查",
    "待处理事项",
    "报告中心",
)

HOME_NAVIGATION_VERSION = "UI-KMFA-S11P1-HOME-NAVIGATION-001"
STYLE_VERSION = "STYLE-KMFA-S11P1-BLUE-BUSINESS-001"
BRAND_MARK_VERSION = "BRAND-KMFA-KM-001"
PUBLIC_SAFETY_VERSION = "SAFE-KMFA-S11P1-PUBLIC-001"

MODULE_ICONS = {
    "business_overview": '<path d="M4 19h16"/><path d="M7 16V9"/><path d="M12 16V5"/><path d="M17 16v-6"/>',
    "project_cost": '<path d="M4 7h16v10H4z"/><path d="M8 11h8"/><path d="M8 14h5"/>',
    "receivable_collection": '<path d="M5 8h14"/><path d="M5 12h14"/><path d="M5 16h10"/><path d="M17 14l2 2 3-4"/>',
    "financial_cash": '<path d="M4 7h16v10H4z"/><path d="M8 12h.01"/><path d="M12 12h.01"/><path d="M16 12h.01"/>',
    "invoice_tax": '<path d="M7 3h10v18l-2-1-2 1-2-1-2 1-2-1z"/><path d="M9 8h6"/><path d="M9 12h6"/><path d="M9 16h3"/>',
    "source_check": '<path d="M5 7c0-2 14-2 14 0s-14 2-14 0z"/><path d="M5 7v5c0 2 14 2 14 0V7"/><path d="M5 12v5c0 2 14 2 14 0v-5"/>',
    "pending_actions": '<path d="M5 4h14v16H5z"/><path d="M8 9l2 2 4-4"/><path d="M8 15h7"/>',
    "report_center": '<path d="M7 3h7l3 3v15H7z"/><path d="M14 3v4h4"/><path d="M9 12h6"/><path d="M9 16h6"/>',
}

SOURCE_TASKPACK_REFS = {
    "roadmap_s11_p1": "KMFA/taskpack/v1_2/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_2.md:S11-P1",
    "frontend_report_rules": "KMFA/taskpack/v1_2/01_KMFA_Codex_TaskPack_v1_2_完整防遗漏_含HTML验收样板.md:11",
    "home_html_sample": (
        "KMFA/taskpack/v1_2/20_HTML_UIUX_报告预览/01_核心HTML验收样板/"
        "KMFA_系统首页预览_v4_blue.html"
    ),
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

FORBIDDEN_PUBLIC_SUFFIXES = (".zip", ".xls", ".xlsx", ".pdf", ".sqlite", ".db")
ALLOWED_VISIBLE_LATIN = ("KMFA", "KM", "S11-P1", "D", "Q0-Q5")


class HomeNavigationRuntimeError(ValueError):
    """Raised when S11-P1 home navigation artifacts are invalid."""


def _sha256_json(payload: Any) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _public_repo_safety() -> dict[str, bool]:
    return {
        "raw_business_values_committed": False,
        "field_plaintext_committed": False,
        "raw_file_committed": False,
        "private_tabular_files_committed": False,
        "excel_workbook_committed": False,
        "pdf_file_committed": False,
        "credential_secret_committed": False,
    }


def _stage_scope() -> dict[str, bool]:
    return {
        "s11_p1_home_navigation_scope_included": True,
        "s11_p2_source_matrix_scope_included": False,
        "s11_p3_project_cost_detail_scope_included": False,
        "formal_report_runtime_scope_included": False,
        "lineage_full_check_scope_included": False,
        "external_connector_scope_included": False,
        "stage11_review_scope_included": False,
        "github_upload_scope_included": False,
    }


def _quality_gate() -> dict[str, Any]:
    return {
        "home_navigation_export_allowed": True,
        "raw_layer_write_allowed": False,
        "formal_report_allowed": False,
        "complete_trusted_report_display_allowed": False,
        "business_decision_basis_allowed": False,
        "github_upload_allowed": False,
        "phase_completion_upload_allowed": False,
        "stage11_review_allowed": False,
        "report_grade_visible": "D",
        "release_block_reason": "s11_p1_navigation_only_reports_remain_blocked",
    }


def _module_records(generated_at: str) -> list[dict[str, Any]]:
    module_specs = [
        {
            "module_id": "business_overview",
            "visible_label": "经营总览",
            "visible_summary": "集中查看经营健康、回款压力、成本风险和本期重点事项。",
            "primary_action": "查看经营概览",
            "target_href": "../../../S10_P3_report_export/exports/html/business_overview_report.html",
            "status_label": "可预览",
            "badge_style": "blue",
            "warning_badge_count": 0,
        },
        {
            "module_id": "project_cost",
            "visible_label": "项目成本",
            "visible_summary": "进入项目成本专题入口，保留质量等级和差异阻断提示。",
            "primary_action": "查看成本入口",
            "target_href": "../../../S11_P3_project_cost_page/exports/html/kmfa_project_cost_page.html",
            "status_label": "受控预览",
            "badge_style": "blue",
            "warning_badge_count": 1,
        },
        {
            "module_id": "receivable_collection",
            "visible_label": "回款应收",
            "visible_summary": "展示回款、应收和逾期压力的公开安全摘要入口。",
            "primary_action": "查看回款入口",
            "target_href": "../../../S13_P2_collection_receivable_aging/exports/html/collection_receivable_aging_priority.html",
            "status_label": "待复核",
            "badge_style": "blue",
            "warning_badge_count": 1,
        },
        {
            "module_id": "financial_cash",
            "visible_label": "财务资金",
            "visible_summary": "查看现金、资金计划和财务口径说明的入口。",
            "primary_action": "查看资金入口",
            "target_href": "../../../S14_P1_fund_cash_loan_plan/exports/html/fund_cash_loan_plan_overview.html",
            "status_label": "可预览",
            "badge_style": "blue",
            "warning_badge_count": 0,
        },
        {
            "module_id": "invoice_tax",
            "visible_label": "开票纳税",
            "visible_summary": "查看开票、税务和合规提醒入口，不执行开票或报税。",
            "primary_action": "查看税务入口",
            "target_href": "../../../S14_P2_invoice_tax_plan/exports/html/invoice_tax_plan_overview.html",
            "status_label": "提示",
            "badge_style": "warning_tag",
            "warning_badge_count": 1,
        },
        {
            "module_id": "source_check",
            "visible_label": "数据源检查",
            "visible_summary": "进入数据源检查板入口；矩阵明细留到 S11-P2。",
            "primary_action": "查看检查入口",
            "target_href": "../../../S11_P2_source_check_board/exports/html/kmfa_source_check_board.html",
            "status_label": "下一阶段展开",
            "badge_style": "blue",
            "warning_badge_count": 0,
        },
        {
            "module_id": "pending_actions",
            "visible_label": "待处理事项",
            "visible_summary": "汇总差异处理、人工确认和报告发布前的待办入口。",
            "primary_action": "查看待办入口",
            "target_href": "../../../S12_P1_manual_resolution_events/exports/html/kmfa_manual_resolution_workbench.html",
            "status_label": "受控",
            "badge_style": "blue",
            "warning_badge_count": 0,
        },
        {
            "module_id": "report_center",
            "visible_label": "报告中心",
            "visible_summary": "查看报告样张和发布限制，正式报告继续受质量等级阻断。",
            "primary_action": "查看报告入口",
            "target_href": "../../../S13_P1_financial_operating_report/exports/html/financial_operating_monthly_draft.html",
            "status_label": "报告等级 D",
            "badge_style": "blue",
            "warning_badge_count": 1,
        },
    ]
    records: list[dict[str, Any]] = []
    for index, spec in enumerate(module_specs, start=1):
        records.append(
            {
                "schema_version": "kmfa.home_navigation_module.v1",
                "record_type": "home_navigation_module",
                "project_id": "KMFA",
                "system_name": "KMFA 经营分析系统",
                "stage_phase": "S11-P1",
                "module_order": index,
                "home_navigation_version": HOME_NAVIGATION_VERSION,
                "style_version": STYLE_VERSION,
                "brand_mark_version": BRAND_MARK_VERSION,
                "public_safety_version": PUBLIC_SAFETY_VERSION,
                "generated_at": generated_at,
                "brand_mark": "KM",
                "brand_mark_is_single_k": False,
                "blue_business_style": True,
                "all_chinese_visible_copy": True,
                "contains_raw_business_values": False,
                "allows_raw_layer_write": False,
                "formal_report_allowed": False,
                "complete_trusted_report_display_allowed": False,
                "business_decision_basis_allowed": False,
                **spec,
            }
        )
    return records


def _render_html(records: list[dict[str, Any]], manifest: dict[str, Any]) -> str:
    def render_icon(module_id: str) -> str:
        paths = MODULE_ICONS[module_id]
        return (
            '<svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true" '
            'focusable="false" fill="none" stroke="currentColor" stroke-width="2" '
            f'stroke-linecap="round" stroke-linejoin="round">{paths}</svg>'
        )

    nav_items = "\n".join(
        (
            f'        <button type="button" data-target="{html.escape(record["module_id"])}"'
            f'{" class=" + chr(34) + "active" + chr(34) + " aria-current=" + chr(34) + "page" + chr(34) if index == 0 else " aria-current=" + chr(34) + "false" + chr(34)}>'
            f'<span class="nav-button-content">{render_icon(record["module_id"])}'
            f'<span>{html.escape(record["visible_label"])}</span></span></button>'
        )
        for index, record in enumerate(records)
    )
    module_cards = "\n".join(
        f"""        <article class="module-card" id="{html.escape(record["module_id"])}">
          <div class="module-top">
            <h2>{html.escape(record["visible_label"])}</h2>
            <span class="tag {html.escape(record["badge_style"])}">{html.escape(record["status_label"])}</span>
          </div>
          <p>{html.escape(record["visible_summary"])}</p>
          <button type="button" class="module-action" data-target="{html.escape(record["module_id"])}" data-href="{html.escape(record["target_href"])}">{render_icon(record["module_id"])}<span>{html.escape(record["primary_action"])}</span></button>
        </article>"""
        for record in records
    )
    module_state_json = json.dumps(
        {
            record["module_id"]: {
                "title": f"{record['visible_label']}入口已选中",
                "body": (
                    f"当前打开的是{record['visible_label']}的公开安全入口预览。"
                    f"{record['primary_action']}会打开对应本地页面，不读取或写入原始数据。"
                ),
                "href": record["target_href"],
            }
            for record in records
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    required_labels = "、".join(html.escape(label) for label in REQUIRED_NAVIGATION_LABELS)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>KMFA 经营分析系统 首页导航</title>
  <style>
    :root {{
      --navy:#082143;
      --navy-2:#103a72;
      --blue:#1d4ed8;
      --blue-soft:#eaf3ff;
      --line:#d8e4f5;
      --text:#142033;
      --muted:#63718a;
      --card:#ffffff;
      --warning:#b45309;
      --warning-bg:#fff7ed;
    }}
    * {{ box-sizing:border-box; }}
    body {{
      margin:0;
      background:#f5f8fc;
      color:var(--text);
      font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",Arial,sans-serif;
    }}
    .app {{ display:grid; grid-template-columns:264px 1fr; min-height:100vh; }}
    aside {{ background:#082143; color:#fff; padding:24px 20px; }}
    .brand {{ display:flex; align-items:center; gap:12px; margin-bottom:24px; }}
    .logo {{
      width:48px; height:48px; border-radius:8px; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:1px;
      background:#1d4ed8; border:1px solid rgba(255,255,255,.32); font-weight:800; font-size:18px;
    }}
    .logo .ui-icon {{ width:20px; height:20px; }}
    .logo-text {{ font-size:12px; line-height:1; letter-spacing:0; }}
    .brand strong {{ display:block; font-size:18px; }}
    .brand span {{ display:block; color:#c7dcff; font-size:13px; margin-top:3px; }}
    nav {{ display:grid; gap:6px; }}
    nav button {{
      width:100%; border:0; border-radius:8px; padding:11px 12px; color:#dbeafe; background:transparent;
      text-align:left; font-size:15px; cursor:pointer; transition:background .16s ease,color .16s ease,transform .16s ease;
    }}
    nav button.active, nav button:hover {{ background:rgba(255,255,255,.12); color:#fff; }}
    nav button:active {{ transform:translateY(1px); }}
    nav button:focus-visible, .module-action:focus-visible {{ outline:3px solid rgba(29,78,216,.35); outline-offset:2px; }}
    .nav-button-content {{ display:flex; align-items:center; gap:10px; }}
    .ui-icon {{ width:18px; height:18px; flex:0 0 18px; }}
    main {{ padding:28px 34px 34px; }}
    .topbar {{ display:flex; justify-content:space-between; gap:16px; align-items:flex-start; margin-bottom:18px; }}
    h1 {{ margin:0 0 8px; font-size:28px; color:#0b2b59; letter-spacing:0; }}
    .subline {{ margin:0; color:var(--muted); line-height:1.6; }}
    .status-strip {{ display:flex; gap:8px; flex-wrap:wrap; justify-content:flex-end; }}
    .pill {{
      border:1px solid #bfdbfe; background:var(--blue-soft); color:#1d4ed8;
      border-radius:999px; padding:6px 10px; font-size:12px; font-weight:700; white-space:nowrap;
    }}
    .overview {{ display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin:18px 0; }}
    .metric {{ background:#fff; border:1px solid var(--line); border-radius:8px; padding:16px; }}
    .metric b {{ display:block; color:#0f2f5f; font-size:22px; margin-bottom:4px; }}
    .metric span {{ color:var(--muted); font-size:13px; }}
    .module-grid {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; }}
    .module-card {{ background:var(--card); border:1px solid var(--line); border-radius:8px; padding:16px; min-height:184px; transition:border-color .16s ease,box-shadow .16s ease; }}
    .module-card.active {{ border-color:#93c5fd; box-shadow:0 0 0 3px rgba(29,78,216,.10); }}
    .module-top {{ display:flex; gap:8px; justify-content:space-between; align-items:flex-start; margin-bottom:12px; }}
    h2 {{ margin:0; color:#0b2b59; font-size:18px; letter-spacing:0; }}
    .module-card p {{ margin:0 0 16px; color:#475569; line-height:1.65; min-height:78px; }}
    .tag {{ display:inline-flex; align-items:center; border-radius:999px; padding:4px 8px; font-size:12px; font-weight:700; white-space:nowrap; }}
    .tag.blue {{ color:#1d4ed8; background:#eff6ff; border:1px solid #bfdbfe; }}
    .tag.warning_tag {{ color:var(--warning); background:var(--warning-bg); border:1px solid #fed7aa; }}
    .module-action {{
      display:inline-flex; align-items:center; gap:8px; border:1px solid #bfdbfe; background:#fff; color:#1d4ed8;
      border-radius:8px; padding:9px 11px; font-weight:700; cursor:pointer; transition:background .16s ease,border-color .16s ease,transform .16s ease;
    }}
    .module-action:hover {{ background:#eff6ff; border-color:#93c5fd; }}
    .module-action:active {{ transform:translateY(1px); }}
    .action-panel {{
      display:flex; justify-content:space-between; gap:18px; align-items:flex-start; margin-top:16px; background:#fff;
      border:1px solid var(--line); border-radius:8px; padding:16px; line-height:1.7;
    }}
    .action-panel h2 {{ margin:0 0 4px; }}
    .action-panel p {{ margin:0; color:#475569; }}
    .notice {{ margin-top:16px; background:#fff; border:1px solid var(--line); border-radius:8px; padding:16px; line-height:1.7; }}
    .notice b {{ color:#0b2b59; }}
    footer {{ color:var(--muted); font-size:12px; padding:16px 0 0; }}
    @media(max-width:1100px) {{ .module-grid,.overview {{ grid-template-columns:repeat(2,minmax(0,1fr)); }} }}
    @media(max-width:820px) {{
      .app {{ grid-template-columns:1fr; }}
      main {{ padding:22px; }}
      .topbar {{ display:block; }}
      .status-strip {{ justify-content:flex-start; margin-top:12px; }}
      .module-grid,.overview {{ grid-template-columns:1fr; }}
      .action-panel {{ display:block; }}
    }}
    @media(prefers-reduced-motion:reduce) {{
      nav button, .module-card, .module-action {{ transition:none; }}
    }}
  </style>
</head>
<body>
  <div class="app">
    <aside>
      <div class="brand"><div class="logo" aria-hidden="true">{render_icon("business_overview")}<span class="logo-text">KM</span></div><div><strong>KMFA</strong><span>经营分析系统</span></div></div>
      <nav aria-label="首页导航">
{nav_items}
      </nav>
    </aside>
    <main>
      <header class="topbar">
        <div>
          <h1>KMFA 经营分析系统</h1>
          <p class="subline">首页与导航 · 蓝色商务版 · 全中文业务入口 · 不展示真实经营明细</p>
        </div>
        <div class="status-strip">
          <span class="pill">报告等级 D</span>
          <span class="pill">不可作为正式经营报告</span>
          <span class="pill">公开安全样张</span>
        </div>
      </header>
      <section class="overview" aria-label="首页状态">
        <div class="metric"><b>{manifest["summary"]["navigation_module_count"]}</b><span>首页模块</span></div>
        <div class="metric"><b>KM</b><span>品牌标识</span></div>
        <div class="metric"><b>蓝色</b><span>商务视觉基调</span></div>
        <div class="metric"><b>受控</b><span>报告发布状态</span></div>
      </section>
      <section class="module-grid" aria-label="业务模块">
{module_cards}
      </section>
      <section class="action-panel" id="module_action_panel" aria-live="polite" data-module="business_overview">
        <div>
          <h2 id="module_action_title">经营总览入口已选中</h2>
          <p id="module_action_body">当前打开的是经营总览的公开安全入口预览。查看经营概览会打开对应本地页面，不读取或写入原始数据。</p>
        </div>
        <span class="pill">受控入口</span>
      </section>
      <section class="notice">
        <b>范围说明：</b>S11-P1 只锁定首页与导航，覆盖 {required_labels}。数据源检查矩阵留到 S11-P2，项目成本详情留到 S11-P3；当前页面不提交原始业务数据，不执行外部接口，不绕过质量等级。
      </section>
      <footer>KMFA 经营分析系统 · S11-P1 首页与导航 · 样张不包含真实经营数据</footer>
    </main>
  </div>
  <script>
    const moduleState = {module_state_json};
    const panel = document.getElementById("module_action_panel");
    const panelTitle = document.getElementById("module_action_title");
    const panelBody = document.getElementById("module_action_body");

    function selectModule(moduleId, options = {{ scrollTarget:false, scrollPanel:false }}) {{
      const target = document.getElementById(moduleId);
      const state = moduleState[moduleId];
      if (!target || !state) return;
      document.querySelectorAll("nav button").forEach((item) => {{
        const isActive = item.dataset.target === moduleId;
        item.classList.toggle("active", isActive);
        item.setAttribute("aria-current", isActive ? "page" : "false");
      }});
      document.querySelectorAll(".module-card").forEach((card) => card.classList.toggle("active", card.id === moduleId));
      panel.dataset.module = moduleId;
      panelTitle.textContent = state.title;
      panelBody.textContent = state.body;
      if (options.scrollTarget) target.scrollIntoView({{ behavior:"smooth", block:"center" }});
      if (options.scrollPanel) panel.scrollIntoView({{ behavior:"smooth", block:"nearest" }});
    }}

    function openModulePage(moduleId, href) {{
      selectModule(moduleId, {{ scrollTarget:false, scrollPanel:false }});
      if (!href) return;
      window.location.href = href;
    }}

    document.querySelectorAll("nav button").forEach((button) => {{
      button.addEventListener("click", () => selectModule(button.dataset.target, {{ scrollTarget:true, scrollPanel:false }}));
    }});
    document.querySelectorAll(".module-action").forEach((button) => {{
      button.addEventListener("click", () => openModulePage(button.dataset.target, button.dataset.href));
    }});
    selectModule("business_overview");
  </script>
</body>
</html>
"""


def build_default_home_navigation_artifacts(
    *,
    generated_at: str = "2026-07-01T09:00:00+10:00",
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, dict[str, str]]]:
    records = _module_records(generated_at)
    label_set = {record["visible_label"] for record in records}
    warning_badge_count = sum(int(record["warning_badge_count"]) for record in records)
    manifest = {
        "schema_version": "kmfa.home_navigation_manifest.v1",
        "record_type": "home_navigation_manifest",
        "project_id": "KMFA",
        "system_name": "KMFA 经营分析系统",
        "stage_phase": "S11-P1",
        "runtime_status": "public_safe_home_navigation_generated_local_only",
        "home_navigation_version": HOME_NAVIGATION_VERSION,
        "style_version": STYLE_VERSION,
        "brand_mark_version": BRAND_MARK_VERSION,
        "public_safety_version": PUBLIC_SAFETY_VERSION,
        "generated_at": generated_at,
        "brand_mark": "KM",
        "brand_mark_is_single_k": False,
        "required_navigation_labels": list(REQUIRED_NAVIGATION_LABELS),
        "source_taskpack_refs": SOURCE_TASKPACK_REFS,
        "quality_gate": _quality_gate(),
        "stage_scope": _stage_scope(),
        "public_repo_safety": _public_repo_safety(),
        "artifact_refs": {
            "home_navigation_manifest": "KMFA/metadata/reports/home_navigation_manifest.json",
            "home_navigation_records": "KMFA/metadata/reports/home_navigation_modules.jsonl",
            "html_export": "KMFA/stage_artifacts/S11_P1_home_navigation/exports/html/kmfa_home_navigation.html",
            "validator": "KMFA/tools/check_s11_p1_home_navigation.py",
            "completion_record": "KMFA/stage_artifacts/S11_P1_home_navigation/human/s11_p1_completion_record.md",
            "test_results": "KMFA/stage_artifacts/S11_P1_home_navigation/human/test_results.md",
            "stage_manifest": "KMFA/stage_artifacts/S11_P1_home_navigation/machine/s11_p1_manifest.json",
        },
        "summary": {
            "navigation_module_count": len(records),
            "required_label_count": len(REQUIRED_NAVIGATION_LABELS),
            "required_labels_covered": label_set == set(REQUIRED_NAVIGATION_LABELS),
            "html_export_count": 1,
            "km_brand_mark_count": 1,
            "single_k_brand_mark_count": 0,
            "blue_business_style": True,
            "all_chinese_visible_copy": True,
            "warning_badge_count": warning_badge_count,
            "large_yellow_surface_count": 0,
            "formal_report_count": 0,
            "business_decision_basis_count": 0,
            "raw_business_value_count": 0,
            "private_file_reference_count": 0,
        },
        "limitations": [
            "S11-P1 只生成首页与导航，不生成数据源检查矩阵或项目成本详情。",
            "首页只展示公开安全摘要和入口，不展示真实经营明细或字段明文。",
            "正式报告、完整可信报告和经营决策依据继续受报告等级阻断。",
            "本 phase 不执行 Stage 11 整体复审或 GitHub upload。",
        ],
    }
    render_outputs = {"html": {"kmfa_home_navigation": _render_html(records, manifest)}}
    manifest["content_hash"] = _sha256_json(
        {"manifest": manifest, "records": records, "render_outputs": render_outputs}
    )
    return manifest, records, render_outputs


def _looks_like_file_reference(value: str) -> bool:
    lowered = value.lower()
    path_markers = ("/", "\\", "kmfa/", "source_ref://", "file://")
    return any(marker in lowered for marker in path_markers) or any(
        lowered.endswith(suffix) for suffix in FORBIDDEN_PUBLIC_SUFFIXES
    )


def _ensure_no_forbidden_public_payload(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in FORBIDDEN_PUBLIC_KEYS:
                raise HomeNavigationRuntimeError(f"forbidden public key found: {key}")
            _ensure_no_forbidden_public_payload(item)
    elif isinstance(value, list):
        for item in value:
            _ensure_no_forbidden_public_payload(item)
    elif isinstance(value, str):
        lowered = value.lower()
        if _looks_like_file_reference(value) and any(suffix in lowered for suffix in FORBIDDEN_PUBLIC_SUFFIXES):
            raise HomeNavigationRuntimeError(f"forbidden private business file reference found: {value}")


def _visible_copy_has_no_internal_english(value: str) -> bool:
    clean = value
    for allowed in ALLOWED_VISIBLE_LATIN:
        clean = clean.replace(allowed, "")
    return not re.search(r"[A-Za-z]{2,}", clean)


def _validate_record(record: dict[str, Any]) -> None:
    label = str(record.get("visible_label", ""))
    if record.get("record_type") != "home_navigation_module":
        raise HomeNavigationRuntimeError(f"{label}.record_type mismatch")
    if record.get("stage_phase") != "S11-P1":
        raise HomeNavigationRuntimeError(f"{label}.stage_phase must be S11-P1")
    if record.get("system_name") != "KMFA 经营分析系统":
        raise HomeNavigationRuntimeError(f"{label}.system_name mismatch")
    if record.get("brand_mark") != "KM" or record.get("brand_mark_is_single_k") is not False:
        raise HomeNavigationRuntimeError(f"{label}.brand_mark must be KM and not single K")
    for field_name in ("home_navigation_version", "style_version", "brand_mark_version", "public_safety_version"):
        if not record.get(field_name):
            raise HomeNavigationRuntimeError(f"{label}.{field_name} is required")
    if record.get("blue_business_style") is not True:
        raise HomeNavigationRuntimeError(f"{label}.blue_business_style must be true")
    if record.get("all_chinese_visible_copy") is not True:
        raise HomeNavigationRuntimeError(f"{label}.all_chinese_visible_copy must be true")
    for copy_field in ("visible_label", "visible_summary", "primary_action", "status_label"):
        if not _visible_copy_has_no_internal_english(str(record.get(copy_field, ""))):
            raise HomeNavigationRuntimeError(f"{label}.{copy_field} exposes internal English")
    if int(record.get("warning_badge_count", 0)) > 1:
        raise HomeNavigationRuntimeError(f"{label}.warning_badge_count must stay small")
    for blocked_field in (
        "contains_raw_business_values",
        "allows_raw_layer_write",
        "formal_report_allowed",
        "complete_trusted_report_display_allowed",
        "business_decision_basis_allowed",
    ):
        if record.get(blocked_field) is not False:
            raise HomeNavigationRuntimeError(f"{label}.{blocked_field} must be false")


def _validate_html(records: list[dict[str, Any]], html_text: str) -> None:
    if not html_text.startswith("<!doctype html>"):
        raise HomeNavigationRuntimeError("HTML must start with doctype")
    for required_text in (
        'lang="zh-CN"',
        "KMFA 经营分析系统",
        ">KM<",
        "蓝色商务版",
        "不可作为正式经营报告",
        "报告等级 D",
    ):
        if required_text not in html_text:
            raise HomeNavigationRuntimeError(f"HTML missing required text: {required_text}")
    if ">K<" in html_text:
        raise HomeNavigationRuntimeError("HTML must not use single K brand mark")
    for record in records:
        for copy_field in ("visible_label", "visible_summary", "primary_action", "status_label"):
            if str(record[copy_field]) not in html_text:
                raise HomeNavigationRuntimeError(f"HTML missing {record['visible_label']}.{copy_field}")
    for forbidden_visible in ("source_ref://", "validator", "manifest", "metadata"):
        if forbidden_visible in html_text.lower():
            raise HomeNavigationRuntimeError(f"HTML exposes internal marker: {forbidden_visible}")
    if "#facc15" in html_text.lower() or "yellow" in html_text.lower():
        raise HomeNavigationRuntimeError("HTML must not use large yellow surfaces")


def validate_home_navigation_artifacts(
    manifest: dict[str, Any],
    records: list[dict[str, Any]],
    render_outputs: dict[str, dict[str, str]],
) -> None:
    if manifest.get("schema_version") != "kmfa.home_navigation_manifest.v1":
        raise HomeNavigationRuntimeError("manifest schema_version mismatch")
    if manifest.get("stage_phase") != "S11-P1":
        raise HomeNavigationRuntimeError("manifest stage_phase must be S11-P1")
    if tuple(manifest.get("required_navigation_labels", [])) != REQUIRED_NAVIGATION_LABELS:
        raise HomeNavigationRuntimeError("manifest required_navigation_labels mismatch")
    if len(records) != len(REQUIRED_NAVIGATION_LABELS):
        raise HomeNavigationRuntimeError("home navigation record count mismatch")

    summary = manifest.get("summary", {})
    expected_summary = {
        "navigation_module_count": 8,
        "required_label_count": 8,
        "required_labels_covered": True,
        "html_export_count": 1,
        "km_brand_mark_count": 1,
        "single_k_brand_mark_count": 0,
        "blue_business_style": True,
        "all_chinese_visible_copy": True,
        "large_yellow_surface_count": 0,
        "formal_report_count": 0,
        "business_decision_basis_count": 0,
        "raw_business_value_count": 0,
        "private_file_reference_count": 0,
    }
    for key, expected in expected_summary.items():
        if summary.get(key) != expected:
            raise HomeNavigationRuntimeError(f"manifest summary {key} must be {expected}")
    if int(summary.get("warning_badge_count", 0)) > 4:
        raise HomeNavigationRuntimeError("warning badges must remain small")
    for scope_key, expected in _stage_scope().items():
        if manifest.get("stage_scope", {}).get(scope_key) is not expected:
            raise HomeNavigationRuntimeError(f"manifest stage_scope {scope_key} must be {expected}")
    for gate_key, expected in _quality_gate().items():
        if manifest.get("quality_gate", {}).get(gate_key) != expected:
            raise HomeNavigationRuntimeError(f"manifest quality_gate {gate_key} must be {expected}")
    for safety_key, expected in _public_repo_safety().items():
        if manifest.get("public_repo_safety", {}).get(safety_key) is not expected:
            raise HomeNavigationRuntimeError(f"manifest public_repo_safety {safety_key} must be {expected}")

    seen_labels: list[str] = []
    seen_orders: list[int] = []
    for record in records:
        _validate_record(record)
        seen_labels.append(str(record.get("visible_label")))
        seen_orders.append(int(record.get("module_order", 0)))
        for field_name in ("home_navigation_version", "style_version", "brand_mark_version", "public_safety_version"):
            if record.get(field_name) != manifest.get(field_name):
                raise HomeNavigationRuntimeError(f"{record['visible_label']}.{field_name} must match manifest")
    if tuple(seen_labels) != REQUIRED_NAVIGATION_LABELS:
        raise HomeNavigationRuntimeError("records must preserve required navigation label order")
    if seen_orders != list(range(1, len(REQUIRED_NAVIGATION_LABELS) + 1)):
        raise HomeNavigationRuntimeError("records module_order mismatch")

    html_text = render_outputs.get("html", {}).get("kmfa_home_navigation")
    if not isinstance(html_text, str):
        raise HomeNavigationRuntimeError("render_outputs.html.kmfa_home_navigation is required")
    _validate_html(records, html_text)
    _ensure_no_forbidden_public_payload(
        {"manifest": manifest, "records": records, "render_outputs": render_outputs}
    )


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        value = json.load(f)
    if not isinstance(value, dict):
        raise HomeNavigationRuntimeError(f"{path} must contain a JSON object")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise HomeNavigationRuntimeError(f"{path} contains a non-object JSONL record")
            records.append(value)
    return records


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
            f.write("\n")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_default_home_navigation_artifacts(
    *,
    output_manifest: Path = DEFAULT_OUTPUT_MANIFEST,
    output_records: Path = DEFAULT_OUTPUT_RECORDS,
    output_stage_manifest: Path = DEFAULT_OUTPUT_STAGE_MANIFEST,
    html_output: Path = DEFAULT_HTML_OUTPUT,
    generated_at: str = "2026-07-01T09:00:00+10:00",
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, dict[str, str]]]:
    manifest, records, render_outputs = build_default_home_navigation_artifacts(generated_at=generated_at)
    validate_home_navigation_artifacts(manifest, records, render_outputs)
    _write_json(output_manifest, manifest)
    _write_jsonl(output_records, records)
    _write_text(html_output, render_outputs["html"]["kmfa_home_navigation"])
    stage_manifest = {
        "schema_version": "kmfa.s11_p1_stage_manifest.v1",
        "record_type": "s11_p1_home_navigation_stage_manifest",
        "project_id": "KMFA",
        "stage_phase": "S11-P1",
        "generated_at": generated_at,
        "status": "completed_validated_local_only_stage_review_pending",
        "content_hash": manifest["content_hash"],
        "artifact_refs": manifest["artifact_refs"],
        "summary": manifest["summary"],
        "quality_gate": manifest["quality_gate"],
        "stage_scope": manifest["stage_scope"],
        "public_repo_safety": manifest["public_repo_safety"],
        "next_gate": "S11_P2_REQUIRED_OR_STAGE11_REVIEW_AFTER_ALL_PHASES",
    }
    _write_json(output_stage_manifest, stage_manifest)
    return manifest, records, render_outputs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build KMFA S11-P1 public-safe home navigation artifacts.")
    parser.add_argument("--output-manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--output-records", type=Path, default=DEFAULT_OUTPUT_RECORDS)
    parser.add_argument("--output-stage-manifest", type=Path, default=DEFAULT_OUTPUT_STAGE_MANIFEST)
    parser.add_argument("--html-output", type=Path, default=DEFAULT_HTML_OUTPUT)
    parser.add_argument("--generated-at", default="2026-07-01T09:00:00+10:00")
    args = parser.parse_args(argv)

    manifest, records, _render_outputs = write_default_home_navigation_artifacts(
        output_manifest=args.output_manifest,
        output_records=args.output_records,
        output_stage_manifest=args.output_stage_manifest,
        html_output=args.html_output,
        generated_at=args.generated_at,
    )
    summary = manifest["summary"]
    print(
        "PASS: KMFA S11-P1 home navigation artifacts generated "
        f"(navigation_modules={len(records)}, html_exports={summary['html_export_count']}, "
        "km_brand=true, blue_business_style=true, all_chinese=true, "
        "formal_report_allowed=false, business_decision_basis_allowed=false, "
        "s11_p2_scope=false, s11_p3_scope=false, stage11_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
