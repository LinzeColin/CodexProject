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
            "status_label": "可预览",
            "badge_style": "blue",
            "warning_badge_count": 0,
        },
        {
            "module_id": "project_cost",
            "visible_label": "项目成本",
            "visible_summary": "进入项目成本专题入口，保留质量等级和差异阻断提示。",
            "primary_action": "查看成本入口",
            "status_label": "受控预览",
            "badge_style": "blue",
            "warning_badge_count": 1,
        },
        {
            "module_id": "receivable_collection",
            "visible_label": "回款应收",
            "visible_summary": "展示回款、应收和逾期压力的公开安全摘要入口。",
            "primary_action": "查看回款入口",
            "status_label": "待复核",
            "badge_style": "blue",
            "warning_badge_count": 1,
        },
        {
            "module_id": "financial_cash",
            "visible_label": "财务资金",
            "visible_summary": "查看现金、资金计划和财务口径说明的入口。",
            "primary_action": "查看资金入口",
            "status_label": "可预览",
            "badge_style": "blue",
            "warning_badge_count": 0,
        },
        {
            "module_id": "invoice_tax",
            "visible_label": "开票纳税",
            "visible_summary": "查看开票、税务和合规提醒入口，不执行开票或报税。",
            "primary_action": "查看税务入口",
            "status_label": "提示",
            "badge_style": "warning_tag",
            "warning_badge_count": 1,
        },
        {
            "module_id": "source_check",
            "visible_label": "数据源检查",
            "visible_summary": "进入数据源检查板入口；矩阵明细留到 S11-P2。",
            "primary_action": "查看检查入口",
            "status_label": "下一阶段展开",
            "badge_style": "blue",
            "warning_badge_count": 0,
        },
        {
            "module_id": "pending_actions",
            "visible_label": "待处理事项",
            "visible_summary": "汇总差异处理、人工确认和报告发布前的待办入口。",
            "primary_action": "查看待办入口",
            "status_label": "受控",
            "badge_style": "blue",
            "warning_badge_count": 0,
        },
        {
            "module_id": "report_center",
            "visible_label": "报告中心",
            "visible_summary": "查看报告样张和发布限制，正式报告继续受质量等级阻断。",
            "primary_action": "查看报告入口",
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
    nav_items = "\n".join(
        (
            f'        <button type="button" data-target="{html.escape(record["module_id"])}"'
            f'{" class=" + chr(34) + "active" + chr(34) if index == 0 else ""}>'
            f'{html.escape(record["visible_label"])}</button>'
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
          <button type="button" class="module-action">{html.escape(record["primary_action"])}</button>
        </article>"""
        for record in records
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
      width:48px; height:48px; border-radius:8px; display:flex; align-items:center; justify-content:center;
      background:#1d4ed8; border:1px solid rgba(255,255,255,.32); font-weight:800; font-size:18px;
    }}
    .brand strong {{ display:block; font-size:18px; }}
    .brand span {{ display:block; color:#c7dcff; font-size:13px; margin-top:3px; }}
    nav {{ display:grid; gap:6px; }}
    nav button {{
      width:100%; border:0; border-radius:8px; padding:12px 12px; color:#dbeafe; background:transparent;
      text-align:left; font-size:15px; cursor:pointer;
    }}
    nav button.active, nav button:hover {{ background:rgba(255,255,255,.12); color:#fff; }}
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
    .module-card {{ background:var(--card); border:1px solid var(--line); border-radius:8px; padding:16px; min-height:184px; }}
    .module-top {{ display:flex; gap:8px; justify-content:space-between; align-items:flex-start; margin-bottom:12px; }}
    h2 {{ margin:0; color:#0b2b59; font-size:18px; letter-spacing:0; }}
    .module-card p {{ margin:0 0 16px; color:#475569; line-height:1.65; min-height:78px; }}
    .tag {{ display:inline-flex; align-items:center; border-radius:999px; padding:4px 8px; font-size:12px; font-weight:700; white-space:nowrap; }}
    .tag.blue {{ color:#1d4ed8; background:#eff6ff; border:1px solid #bfdbfe; }}
    .tag.warning_tag {{ color:var(--warning); background:var(--warning-bg); border:1px solid #fed7aa; }}
    .module-action {{ border:1px solid #bfdbfe; background:#fff; color:#1d4ed8; border-radius:8px; padding:9px 11px; font-weight:700; cursor:pointer; }}
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
    }}
  </style>
</head>
<body>
  <div class="app">
    <aside>
      <div class="brand"><div class="logo">KM</div><div><strong>KMFA</strong><span>经营分析系统</span></div></div>
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
      <section class="notice">
        <b>范围说明：</b>S11-P1 只锁定首页与导航，覆盖 {required_labels}。数据源检查矩阵留到 S11-P2，项目成本详情留到 S11-P3；当前页面不提交原始业务数据，不执行外部接口，不绕过质量等级。
      </section>
      <footer>KMFA 经营分析系统 · S11-P1 首页与导航 · 样张不包含真实经营数据</footer>
    </main>
  </div>
  <script>
    document.querySelectorAll("nav button").forEach((button) => {{
      button.addEventListener("click", () => {{
        document.querySelectorAll("nav button").forEach((item) => item.classList.remove("active"));
        button.classList.add("active");
        const target = document.getElementById(button.dataset.target);
        if (target) target.scrollIntoView({{ behavior:"smooth", block:"nearest" }});
      }});
    }});
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
