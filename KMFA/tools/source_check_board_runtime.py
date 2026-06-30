#!/usr/bin/env python3
"""Build KMFA S11-P2 public-safe source check board artifacts."""

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

DEFAULT_OUTPUT_MANIFEST = ROOT / "metadata" / "reports" / "source_check_board_manifest.json"
DEFAULT_OUTPUT_ROWS = ROOT / "metadata" / "reports" / "source_check_board_rows.jsonl"
DEFAULT_OUTPUT_STAGE_MANIFEST = (
    ROOT / "stage_artifacts" / "S11_P2_source_check_board" / "machine" / "s11_p2_manifest.json"
)
DEFAULT_HTML_OUTPUT = (
    ROOT / "stage_artifacts" / "S11_P2_source_check_board" / "exports" / "html" / "kmfa_source_check_board.html"
)

REQUIRED_BOARD_COLUMNS = (
    "来源系统",
    "业务板块",
    "文件包",
    "公司主体",
    "银行或系统账户",
    "账户或报表",
    "频率",
    "状态",
    "影响报告",
    "处理规则",
    "下一步",
)

ALLOWED_BOARD_STATUSES = ("已就绪", "部分/阻塞", "失败/不适用", "已过期", "人工复核")

SOURCE_CHECK_BOARD_VERSION = "UI-KMFA-S11P2-SOURCE-CHECK-BOARD-001"
STYLE_VERSION = "STYLE-KMFA-S11P2-BLUE-GRAY-001"
INTERACTION_VERSION = "INTERACTION-KMFA-S11P2-STATUS-DETAIL-001"
PUBLIC_SAFETY_VERSION = "SAFE-KMFA-S11P2-PUBLIC-001"

SOURCE_TASKPACK_REFS = {
    "roadmap_s11_p2": "KMFA/taskpack/v1_2/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_2.md:S11-P2",
    "frontend_report_rules": "KMFA/taskpack/v1_2/01_KMFA_Codex_TaskPack_v1_2_完整防遗漏_含HTML验收样板.md:11",
    "source_check_html_sample": (
        "KMFA/taskpack/v1_2/20_HTML_UIUX_报告预览/01_核心HTML验收样板/"
        "KMFA_数据源检查板_v0_5_blue.html"
    ),
    "s03_metadata_protocol": "KMFA/metadata/sources/source_check_matrix_policy.yaml",
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
ALLOWED_VISIBLE_LATIN = ("KMFA", "KM", "S11-P2", "D", "Q0-Q5")


class SourceCheckBoardRuntimeError(ValueError):
    """Raised when S11-P2 source check board artifacts are invalid."""


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
        "real_account_number_committed": False,
    }


def _stage_scope() -> dict[str, bool]:
    return {
        "s11_p1_home_navigation_scope_included": False,
        "s11_p2_source_check_board_scope_included": True,
        "s11_p3_project_cost_detail_scope_included": False,
        "formal_report_runtime_scope_included": False,
        "lineage_full_check_scope_included": False,
        "external_connector_scope_included": False,
        "stage11_review_scope_included": False,
        "github_upload_scope_included": False,
    }


def _quality_gate() -> dict[str, Any]:
    return {
        "source_check_board_export_allowed": True,
        "raw_layer_write_allowed": False,
        "raw_source_mutation_allowed": False,
        "formal_report_allowed": False,
        "complete_trusted_report_display_allowed": False,
        "business_decision_basis_allowed": False,
        "github_upload_allowed": False,
        "phase_completion_upload_allowed": False,
        "stage11_review_allowed": False,
        "report_grade_visible": "D",
        "release_block_reason": "s11_p2_source_check_board_only_reports_remain_blocked",
    }


def _style_gate() -> dict[str, Any]:
    return {
        "blue_gray_surface_dominant": True,
        "status_badges_only": True,
        "large_yellow_surface_count": 0,
        "yellow_surface_allowed": False,
        "status_color_accessibility_note": "异常只用小徽标提示，大面积区域保持蓝灰和白色。",
    }


def _interaction_gate() -> dict[str, Any]:
    return {
        "status_click_detail_enabled": True,
        "detail_panel_fields": ["影响报告", "处理规则", "下一步"],
        "write_back_allowed": False,
        "raw_layer_write_allowed": False,
    }


def _board_rows(generated_at: str) -> list[dict[str, Any]]:
    row_specs = [
        {
            "row_id": "SCB-001",
            "source_system": "财务支撑源",
            "business_segment": "经营总览",
            "source_package_ref": "财务经营摘要包",
            "entity_ref": "主体分组：全部",
            "bank_or_system_account": "系统报表组",
            "account_or_report_ref": "经营指标组",
            "frequency": "每月",
            "status": "已就绪",
            "report_impact": "经营总览可预览，但仍受报告等级约束。",
            "handling_rule": "只展示汇总状态，不展示原始明细。",
            "next_step": "继续保留来源指纹和字段合同复核。",
        },
        {
            "row_id": "SCB-002",
            "source_system": "财务支撑源",
            "business_segment": "项目成本",
            "source_package_ref": "成本汇总支撑包",
            "entity_ref": "主体分组：多主体",
            "bank_or_system_account": "系统报表组",
            "account_or_report_ref": "成本结构组",
            "frequency": "每月",
            "status": "已就绪",
            "report_impact": "项目成本报告只能以 D 级预览进入报告中心。",
            "handling_rule": "不得绕过待复核差异和追溯完整性阻断。",
            "next_step": "等待下一阶段项目成本页面展示详情入口。",
        },
        {
            "row_id": "SCB-003",
            "source_system": "财务支撑源",
            "business_segment": "现金资金",
            "source_package_ref": "现金流支撑包",
            "entity_ref": "主体分组：全部",
            "bank_or_system_account": "账户分组",
            "account_or_report_ref": "现金摘要组",
            "frequency": "每周或每月",
            "status": "已就绪",
            "report_impact": "现金安全摘要可预览，账户明细不公开展示。",
            "handling_rule": "账户只能使用分组引用，不能展示真实账号。",
            "next_step": "保持账户脱敏和公开仓库禁止提交规则。",
        },
        {
            "row_id": "SCB-004",
            "source_system": "表格文档支撑源",
            "business_segment": "回款应收",
            "source_package_ref": "回款与应收支撑包",
            "entity_ref": "主体分组：全部",
            "bank_or_system_account": "工作表分组",
            "account_or_report_ref": "回款应收组",
            "frequency": "每周或每月",
            "status": "已就绪",
            "report_impact": "回款应收摘要可预览，催收结论需人工复核。",
            "handling_rule": "不得输出客户明细、合同明细或真实金额。",
            "next_step": "继续使用指纹、引用和状态证据绑定。",
        },
        {
            "row_id": "SCB-005",
            "source_system": "表格文档支撑源",
            "business_segment": "项目状态",
            "source_package_ref": "项目状态支撑包",
            "entity_ref": "主体分组：全部",
            "bank_or_system_account": "工作表分组",
            "account_or_report_ref": "项目状态组",
            "frequency": "每周",
            "status": "部分/阻塞",
            "report_impact": "项目状态只能提示，不得形成完整履约结论。",
            "handling_rule": "结构不完整时进入人工复核，不参与自动报告解锁。",
            "next_step": "补齐标准导出或确认字段映射规则。",
        },
        {
            "row_id": "SCB-006",
            "source_system": "红圈预留源",
            "business_segment": "经营数据",
            "source_package_ref": "经营导出预留包",
            "entity_ref": "主体分组：全部",
            "bank_or_system_account": "系统账户组",
            "account_or_report_ref": "经营对象组",
            "frequency": "每周",
            "status": "部分/阻塞",
            "report_impact": "缺少只读导出时经营结论保持降级。",
            "handling_rule": "本阶段不接自动接口，只保留后置策略。",
            "next_step": "后续需负责人授权只读导出模板。",
        },
        {
            "row_id": "SCB-007",
            "source_system": "红圈预留源",
            "business_segment": "合同数据",
            "source_package_ref": "合同导出预留包",
            "entity_ref": "主体分组：全部",
            "bank_or_system_account": "系统账户组",
            "account_or_report_ref": "合同对象组",
            "frequency": "每周",
            "status": "部分/阻塞",
            "report_impact": "合同口径完整性不能作为正式结论。",
            "handling_rule": "缺失时必须标注替代来源和质量等级。",
            "next_step": "后续确认只读导出模板与回滚计划。",
        },
        {
            "row_id": "SCB-008",
            "source_system": "金蝶预留源",
            "business_segment": "总账凭证",
            "source_package_ref": "账务核验预留包",
            "entity_ref": "账套分组：多主体",
            "bank_or_system_account": "账套分组",
            "account_or_report_ref": "科目与凭证组",
            "frequency": "每月",
            "status": "部分/阻塞",
            "report_impact": "账务核验缺失时成本与费用结论继续降级。",
            "handling_rule": "未提供标准只读导出前不得标记为已核验。",
            "next_step": "确认版本、模板和只读导出边界。",
        },
        {
            "row_id": "SCB-009",
            "source_system": "银行支撑源",
            "business_segment": "银行流水",
            "source_package_ref": "账户流水支撑包",
            "entity_ref": "主体分组：多主体",
            "bank_or_system_account": "账户分组",
            "account_or_report_ref": "流水摘要组",
            "frequency": "每日或每周",
            "status": "人工复核",
            "report_impact": "现金与付款核销只能提示风险，不能解锁正式报告。",
            "handling_rule": "真实账号、对手方和流水明细不得进入公开仓库。",
            "next_step": "人工确认脱敏账户映射和只读抽取边界。",
        },
        {
            "row_id": "SCB-010",
            "source_system": "税务支撑源",
            "business_segment": "开票纳税",
            "source_package_ref": "税务票据支撑包",
            "entity_ref": "主体分组：多主体",
            "bank_or_system_account": "系统报表组",
            "account_or_report_ref": "票据摘要组",
            "frequency": "每月",
            "status": "人工复核",
            "report_impact": "税务风险只能提示，不能形成税务申报结论。",
            "handling_rule": "税务申报和开票执行不在 KMFA 自动范围内。",
            "next_step": "人工确认政策证据和发票摘要映射。",
        },
        {
            "row_id": "SCB-011",
            "source_system": "政策证据源",
            "business_segment": "研发费用",
            "source_package_ref": "政策证据支撑包",
            "entity_ref": "主体分组：相关主体",
            "bank_or_system_account": "证据分组",
            "account_or_report_ref": "政策证据组",
            "frequency": "每月或季度",
            "status": "已过期",
            "report_impact": "政策准备度只能显示过期提示。",
            "handling_rule": "过期证据不能参与正式报告或税务判断。",
            "next_step": "补充最新证据并重新锁定来源状态。",
        },
        {
            "row_id": "SCB-012",
            "source_system": "外部接口源",
            "business_segment": "自动接口",
            "source_package_ref": "接口接入预留包",
            "entity_ref": "主体分组：不适用",
            "bank_or_system_account": "系统账户组",
            "account_or_report_ref": "接口预留组",
            "frequency": "不适用",
            "status": "失败/不适用",
            "report_impact": "本阶段不因接口缺失阻断公开安全页面，但正式报告仍阻断。",
            "handling_rule": "S11-P2 不接自动接口，不保存凭证。",
            "next_step": "保持文件型最小版本和后续授权接入边界。",
        },
        {
            "row_id": "SCB-013",
            "source_system": "合同证据源",
            "business_segment": "验收结算",
            "source_package_ref": "项目证据支撑包",
            "entity_ref": "项目分组：证据项",
            "bank_or_system_account": "证据分组",
            "account_or_report_ref": "验收结算组",
            "frequency": "按项目",
            "status": "已过期",
            "report_impact": "验收结算证据过期时项目状态保持提示。",
            "handling_rule": "证据附件只登记指纹和引用，不做全文公开展示。",
            "next_step": "补充有效证据并进入人工确认。",
        },
    ]
    rows: list[dict[str, Any]] = []
    for index, spec in enumerate(row_specs, start=1):
        rows.append(
            {
                "schema_version": "kmfa.source_check_board_row.v1",
                "record_type": "source_check_board_row",
                "project_id": "KMFA",
                "system_name": "KMFA 经营分析系统",
                "stage_phase": "S11-P2",
                "row_order": index,
                "source_check_board_version": SOURCE_CHECK_BOARD_VERSION,
                "style_version": STYLE_VERSION,
                "interaction_version": INTERACTION_VERSION,
                "public_safety_version": PUBLIC_SAFETY_VERSION,
                "generated_at": generated_at,
                "status_allowed_values": list(ALLOWED_BOARD_STATUSES),
                "contains_raw_business_values": False,
                "raw_layer_write_allowed": False,
                "raw_source_mutation_allowed": False,
                "formal_report_allowed": False,
                "complete_trusted_report_display_allowed": False,
                "business_decision_basis_allowed": False,
                **spec,
            }
        )
    return rows


def _status_class(status: str) -> str:
    return {
        "已就绪": "ready",
        "部分/阻塞": "partial",
        "失败/不适用": "failed",
        "已过期": "outdated",
        "人工复核": "review",
    }[status]


def _render_html(rows: list[dict[str, Any]], manifest: dict[str, Any]) -> str:
    status_counts = manifest["summary"]["status_counts"]
    summary_cards = "\n".join(
        f'        <div class="summary-card"><b>{html.escape(str(status_counts[status]))}</b><span>{html.escape(status)}</span></div>'
        for status in ALLOWED_BOARD_STATUSES
    )
    table_rows = "\n".join(
        f"""          <tr>
            <td>{html.escape(row["source_system"])}</td>
            <td>{html.escape(row["business_segment"])}</td>
            <td>{html.escape(row["source_package_ref"])}</td>
            <td>{html.escape(row["entity_ref"])}</td>
            <td>{html.escape(row["bank_or_system_account"])}</td>
            <td>{html.escape(row["account_or_report_ref"])}</td>
            <td>{html.escape(row["frequency"])}</td>
            <td><button type="button" class="status-badge {_status_class(row["status"])}" data-impact="{html.escape(row["report_impact"])}" data-rule="{html.escape(row["handling_rule"])}" data-next="{html.escape(row["next_step"])}">{html.escape(row["status"])}</button></td>
            <td>{html.escape(row["report_impact"])}</td>
            <td>{html.escape(row["handling_rule"])}</td>
            <td>{html.escape(row["next_step"])}</td>
          </tr>"""
        for row in rows
    )
    columns = "".join(f"<th>{html.escape(column)}</th>" for column in REQUIRED_BOARD_COLUMNS)
    first_row = rows[0]
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>KMFA 数据源检查板</title>
  <style>
    :root {{
      --navy:#0b1f3a;
      --blue:#1d4ed8;
      --blue-soft:#eff6ff;
      --bg:#f7faff;
      --card:#ffffff;
      --line:#d8e7ff;
      --text:#172033;
      --muted:#64748b;
      --ready:#0f766e;
      --partial:#1d4ed8;
      --failed:#b91c1c;
      --review:#6d28d9;
      --outdated:#111827;
    }}
    * {{ box-sizing:border-box; }}
    body {{
      margin:0;
      background:linear-gradient(180deg,#f8fbff 0%,#eef5ff 100%);
      color:var(--text);
      font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",Arial,sans-serif;
    }}
    .header {{ background:linear-gradient(135deg,#071a33,#0f3b74); color:#fff; padding:28px 36px; }}
    .brand {{ display:flex; align-items:center; gap:14px; }}
    .logo {{
      width:54px; height:54px; border:1px solid rgba(255,255,255,.35); border-radius:12px;
      display:flex; align-items:center; justify-content:center; font-weight:800; background:rgba(255,255,255,.08);
    }}
    h1 {{ margin:0; font-size:26px; letter-spacing:0; }}
    .header p {{ margin:8px 0 0; color:#c7ddff; line-height:1.6; }}
    .wrap {{ padding:24px 36px 38px; }}
    .summary {{ display:grid; grid-template-columns:repeat(5,1fr); gap:12px; margin-bottom:18px; }}
    .summary-card {{ background:rgba(255,255,255,.92); border:1px solid var(--line); border-radius:8px; padding:16px; }}
    .summary-card b {{ display:block; font-size:25px; color:#0b376d; }}
    .summary-card span {{ color:var(--muted); font-size:13px; }}
    .toolbar {{ display:flex; justify-content:space-between; gap:16px; align-items:flex-start; margin-bottom:14px; }}
    .note {{ color:#475569; line-height:1.7; max-width:720px; }}
    .grade {{ border:1px solid #bfdbfe; background:#fff; color:var(--blue); border-radius:999px; padding:7px 11px; font-size:12px; font-weight:800; white-space:nowrap; }}
    .matrix-wrap {{ overflow:auto; border:1px solid var(--line); border-radius:8px; background:#fff; box-shadow:0 14px 38px rgba(15,54,113,.08); }}
    table {{ width:100%; min-width:1280px; border-collapse:separate; border-spacing:0; }}
    th {{ position:sticky; top:0; background:#0f2f5f; color:#fff; font-size:13px; text-align:left; padding:12px; border-bottom:1px solid #244d86; }}
    td {{ font-size:13px; padding:11px 12px; border-bottom:1px solid #e7f0ff; vertical-align:top; line-height:1.55; }}
    tr:hover td {{ background:#f8fbff; }}
    .status-badge {{ border:1px solid transparent; border-radius:999px; padding:4px 10px; font-size:12px; font-weight:800; white-space:nowrap; cursor:pointer; }}
    .ready {{ color:#065f46; background:#dcfce7; }}
    .partial {{ color:#1d4ed8; background:#eff6ff; border-color:#bfdbfe; }}
    .failed {{ color:#991b1b; background:#fee2e2; }}
    .review {{ color:#5b21b6; background:#f3e8ff; }}
    .outdated {{ color:#111827; background:#e5e7eb; }}
    .detail {{ margin-top:16px; background:#fff; border:1px solid var(--line); border-radius:8px; padding:16px; display:grid; gap:10px; }}
    .detail h2 {{ margin:0; color:#0b2b59; font-size:18px; letter-spacing:0; }}
    .detail p {{ margin:0; color:#475569; line-height:1.7; }}
    .detail strong {{ color:#0b2b59; }}
    .footer {{ margin-top:16px; color:#64748b; font-size:12px; line-height:1.6; }}
    @media(max-width:1000px) {{
      .wrap {{ padding:18px; }}
      .summary {{ grid-template-columns:repeat(2,1fr); }}
      .toolbar {{ display:block; }}
      .grade {{ display:inline-flex; margin-top:10px; }}
    }}
    @media(max-width:560px) {{ .summary {{ grid-template-columns:1fr; }} }}
  </style>
</head>
<body>
  <header class="header">
    <div class="brand"><div class="logo">KM</div><div><h1>KMFA 数据源检查板</h1><p>来源系统、业务板块、文件包、公司主体、账户分组和状态矩阵。点击状态查看影响报告和下一步处理。</p></div></div>
  </header>
  <main class="wrap">
    <section class="summary" aria-label="状态汇总">
{summary_cards}
    </section>
    <section class="toolbar">
      <div class="note">状态色采用低干扰方案，大面积区域保持蓝灰和白色；异常只用小型徽标提示。当前页面只展示公开安全状态，不展示原始金额、客户明细、字段明文或账号凭证。</div>
      <span class="grade">报告等级 D</span>
    </section>
    <section class="matrix-wrap" aria-label="数据源检查矩阵">
      <table>
        <thead><tr>{columns}</tr></thead>
        <tbody>
{table_rows}
        </tbody>
      </table>
    </section>
    <section class="detail" aria-live="polite">
      <h2>状态详情</h2>
      <p><strong>影响报告：</strong><span id="impactText">{html.escape(first_row["report_impact"])}</span></p>
      <p><strong>处理规则：</strong><span id="ruleText">{html.escape(first_row["handling_rule"])}</span></p>
      <p><strong>下一步：</strong><span id="nextText">{html.escape(first_row["next_step"])}</span></p>
    </section>
    <div class="footer">KMFA 经营分析系统 · S11-P2 数据源检查板 · 本页面不解锁正式报告、项目成本详情、第十一阶段复审或上传。</div>
  </main>
  <script>
    const detail = {{
      impact: document.getElementById("impactText"),
      rule: document.getElementById("ruleText"),
      next: document.getElementById("nextText")
    }};
    document.querySelectorAll(".status-badge").forEach((button) => {{
      button.addEventListener("click", () => {{
        detail.impact.textContent = button.dataset.impact;
        detail.rule.textContent = button.dataset.rule;
        detail.next.textContent = button.dataset.next;
      }});
    }});
  </script>
</body>
</html>
"""


def build_default_source_check_board_artifacts(
    *,
    generated_at: str = "2026-07-01T10:00:00+10:00",
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, dict[str, str]]]:
    rows = _board_rows(generated_at)
    status_counts = {status: 0 for status in ALLOWED_BOARD_STATUSES}
    for row in rows:
        status_counts[str(row["status"])] += 1
    manifest = {
        "schema_version": "kmfa.source_check_board_manifest.v1",
        "record_type": "source_check_board_manifest",
        "project_id": "KMFA",
        "system_name": "KMFA 经营分析系统",
        "stage_phase": "S11-P2",
        "runtime_status": "public_safe_source_check_board_generated_local_only",
        "source_check_board_version": SOURCE_CHECK_BOARD_VERSION,
        "style_version": STYLE_VERSION,
        "interaction_version": INTERACTION_VERSION,
        "public_safety_version": PUBLIC_SAFETY_VERSION,
        "generated_at": generated_at,
        "brand_mark": "KM",
        "brand_mark_is_single_k": False,
        "required_columns": list(REQUIRED_BOARD_COLUMNS),
        "allowed_statuses": list(ALLOWED_BOARD_STATUSES),
        "source_taskpack_refs": SOURCE_TASKPACK_REFS,
        "quality_gate": _quality_gate(),
        "stage_scope": _stage_scope(),
        "style_gate": _style_gate(),
        "interaction": _interaction_gate(),
        "public_repo_safety": _public_repo_safety(),
        "artifact_refs": {
            "source_check_board_manifest": "KMFA/metadata/reports/source_check_board_manifest.json",
            "source_check_board_rows": "KMFA/metadata/reports/source_check_board_rows.jsonl",
            "html_export": "KMFA/stage_artifacts/S11_P2_source_check_board/exports/html/kmfa_source_check_board.html",
            "validator": "KMFA/tools/check_s11_p2_source_check_board.py",
            "completion_record": "KMFA/stage_artifacts/S11_P2_source_check_board/human/s11_p2_completion_record.md",
            "test_results": "KMFA/stage_artifacts/S11_P2_source_check_board/human/test_results.md",
            "stage_manifest": "KMFA/stage_artifacts/S11_P2_source_check_board/machine/s11_p2_manifest.json",
        },
        "summary": {
            "matrix_row_count": len(rows),
            "required_column_count": len(REQUIRED_BOARD_COLUMNS),
            "required_columns_covered": True,
            "allowed_status_count": len(ALLOWED_BOARD_STATUSES),
            "status_counts": status_counts,
            "html_export_count": 1,
            "km_brand_mark_count": 1,
            "single_k_brand_mark_count": 0,
            "blue_gray_surface_dominant": True,
            "large_yellow_surface_count": 0,
            "status_click_detail_enabled": True,
            "formal_report_count": 0,
            "business_decision_basis_count": 0,
            "raw_business_value_count": 0,
            "private_file_reference_count": 0,
        },
        "limitations": [
            "S11-P2 只生成数据源检查板，不生成 S11-P3 项目成本页面。",
            "检查板只展示公开安全来源状态和处理提示，不展示真实文件名、账号、字段明文或业务值。",
            "状态点击只切换页面详情，不写 raw layer，不执行外部接口。",
            "正式报告、完整可信报告和经营决策依据继续受报告等级阻断。",
            "本 phase 不执行 Stage 11 整体复审或 GitHub upload。",
        ],
    }
    render_outputs = {"html": {"kmfa_source_check_board": _render_html(rows, manifest)}}
    manifest["content_hash"] = _sha256_json({"manifest": manifest, "rows": rows, "render_outputs": render_outputs})
    return manifest, rows, render_outputs


def _looks_like_forbidden_private_file(value: str) -> bool:
    lowered = value.lower()
    return any(suffix in lowered for suffix in FORBIDDEN_PUBLIC_SUFFIXES)


def _ensure_no_forbidden_public_payload(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in FORBIDDEN_PUBLIC_KEYS:
                raise SourceCheckBoardRuntimeError(f"forbidden public key found: {key}")
            _ensure_no_forbidden_public_payload(item)
    elif isinstance(value, list):
        for item in value:
            _ensure_no_forbidden_public_payload(item)
    elif isinstance(value, str):
        if _looks_like_forbidden_private_file(value):
            raise SourceCheckBoardRuntimeError(f"forbidden private business file reference found: {value}")


def _visible_copy_has_no_internal_english(value: str) -> bool:
    clean = value
    for allowed in ALLOWED_VISIBLE_LATIN:
        clean = clean.replace(allowed, "")
    return not re.search(r"[A-Za-z]{2,}", clean)


def _validate_row(row: dict[str, Any]) -> None:
    label = str(row.get("row_id", ""))
    if row.get("record_type") != "source_check_board_row":
        raise SourceCheckBoardRuntimeError(f"{label}.record_type mismatch")
    if row.get("stage_phase") != "S11-P2":
        raise SourceCheckBoardRuntimeError(f"{label}.stage_phase must be S11-P2")
    if row.get("system_name") != "KMFA 经营分析系统":
        raise SourceCheckBoardRuntimeError(f"{label}.system_name mismatch")
    for field_name in (
        "source_check_board_version",
        "style_version",
        "interaction_version",
        "public_safety_version",
    ):
        if not row.get(field_name):
            raise SourceCheckBoardRuntimeError(f"{label}.{field_name} is required")
    if row.get("status") not in ALLOWED_BOARD_STATUSES:
        raise SourceCheckBoardRuntimeError(f"{label}.status invalid")
    if tuple(row.get("status_allowed_values", [])) != ALLOWED_BOARD_STATUSES:
        raise SourceCheckBoardRuntimeError(f"{label}.status_allowed_values mismatch")
    for copy_field in (
        "source_system",
        "business_segment",
        "source_package_ref",
        "entity_ref",
        "bank_or_system_account",
        "account_or_report_ref",
        "frequency",
        "status",
        "report_impact",
        "handling_rule",
        "next_step",
    ):
        value = str(row.get(copy_field, ""))
        if not value:
            raise SourceCheckBoardRuntimeError(f"{label}.{copy_field} is required")
        if not _visible_copy_has_no_internal_english(value):
            raise SourceCheckBoardRuntimeError(f"{label}.{copy_field} exposes internal English")
        if _looks_like_forbidden_private_file(value):
            raise SourceCheckBoardRuntimeError(f"{label}.{copy_field} exposes private file reference")
    for blocked_field in (
        "contains_raw_business_values",
        "raw_layer_write_allowed",
        "raw_source_mutation_allowed",
        "formal_report_allowed",
        "complete_trusted_report_display_allowed",
        "business_decision_basis_allowed",
    ):
        if row.get(blocked_field) is not False:
            raise SourceCheckBoardRuntimeError(f"{label}.{blocked_field} must be false")


def _validate_html(rows: list[dict[str, Any]], html_text: str) -> None:
    if not html_text.startswith("<!doctype html>"):
        raise SourceCheckBoardRuntimeError("HTML must start with doctype")
    for required_text in (
        'lang="zh-CN"',
        "KMFA 数据源检查板",
        ">KM<",
        "点击状态查看影响报告和下一步处理",
        "状态详情",
        "报告等级 D",
    ):
        if required_text not in html_text:
            raise SourceCheckBoardRuntimeError(f"HTML missing required text: {required_text}")
    if ">K<" in html_text:
        raise SourceCheckBoardRuntimeError("HTML must not use single K brand mark")
    for column in REQUIRED_BOARD_COLUMNS:
        if column not in html_text:
            raise SourceCheckBoardRuntimeError(f"HTML missing column: {column}")
    for status in ALLOWED_BOARD_STATUSES:
        if status not in html_text:
            raise SourceCheckBoardRuntimeError(f"HTML missing status: {status}")
    for row in rows:
        for copy_field in (
            "source_system",
            "business_segment",
            "source_package_ref",
            "entity_ref",
            "bank_or_system_account",
            "account_or_report_ref",
            "frequency",
            "status",
            "report_impact",
            "handling_rule",
            "next_step",
        ):
            if str(row[copy_field]) not in html_text:
                raise SourceCheckBoardRuntimeError(f"HTML missing {row['row_id']}.{copy_field}")
    for forbidden_visible in ("source_ref://", "validator", "manifest", "metadata"):
        if forbidden_visible in html_text.lower():
            raise SourceCheckBoardRuntimeError(f"HTML exposes internal marker: {forbidden_visible}")
    if "yellow" in html_text.lower() or "#facc15" in html_text.lower() or "#eab308" in html_text.lower():
        raise SourceCheckBoardRuntimeError("HTML must not use large yellow surfaces")
    if not all(snippet in html_text for snippet in ("addEventListener(\"click\"", "dataset.impact", "dataset.next")):
        raise SourceCheckBoardRuntimeError("HTML must support status click detail interaction")
    if _looks_like_forbidden_private_file(html_text):
        raise SourceCheckBoardRuntimeError("HTML exposes forbidden private file suffix")


def validate_source_check_board_artifacts(
    manifest: dict[str, Any],
    rows: list[dict[str, Any]],
    render_outputs: dict[str, dict[str, str]],
) -> None:
    if manifest.get("schema_version") != "kmfa.source_check_board_manifest.v1":
        raise SourceCheckBoardRuntimeError("manifest schema_version mismatch")
    if manifest.get("stage_phase") != "S11-P2":
        raise SourceCheckBoardRuntimeError("manifest stage_phase must be S11-P2")
    if tuple(manifest.get("required_columns", [])) != REQUIRED_BOARD_COLUMNS:
        raise SourceCheckBoardRuntimeError("manifest required_columns mismatch")
    if tuple(manifest.get("allowed_statuses", [])) != ALLOWED_BOARD_STATUSES:
        raise SourceCheckBoardRuntimeError("manifest allowed_statuses mismatch")
    if len(rows) < 10:
        raise SourceCheckBoardRuntimeError("source check board must include enough matrix rows")

    status_counts = {status: 0 for status in ALLOWED_BOARD_STATUSES}
    seen_orders: list[int] = []
    for row in rows:
        _validate_row(row)
        status_counts[str(row["status"])] += 1
        seen_orders.append(int(row.get("row_order", 0)))
        for field_name in (
            "source_check_board_version",
            "style_version",
            "interaction_version",
            "public_safety_version",
        ):
            if row.get(field_name) != manifest.get(field_name):
                raise SourceCheckBoardRuntimeError(f"{row['row_id']}.{field_name} must match manifest")
    if seen_orders != list(range(1, len(rows) + 1)):
        raise SourceCheckBoardRuntimeError("rows row_order mismatch")
    if not all(count > 0 for count in status_counts.values()):
        raise SourceCheckBoardRuntimeError("all allowed statuses must be represented")

    summary = manifest.get("summary", {})
    expected_summary = {
        "matrix_row_count": len(rows),
        "required_column_count": len(REQUIRED_BOARD_COLUMNS),
        "required_columns_covered": True,
        "allowed_status_count": len(ALLOWED_BOARD_STATUSES),
        "status_counts": status_counts,
        "html_export_count": 1,
        "km_brand_mark_count": 1,
        "single_k_brand_mark_count": 0,
        "blue_gray_surface_dominant": True,
        "large_yellow_surface_count": 0,
        "status_click_detail_enabled": True,
        "formal_report_count": 0,
        "business_decision_basis_count": 0,
        "raw_business_value_count": 0,
        "private_file_reference_count": 0,
    }
    for key, expected in expected_summary.items():
        if summary.get(key) != expected:
            raise SourceCheckBoardRuntimeError(f"manifest summary {key} must be {expected}")
    for scope_key, expected in _stage_scope().items():
        if manifest.get("stage_scope", {}).get(scope_key) is not expected:
            raise SourceCheckBoardRuntimeError(f"manifest stage_scope {scope_key} must be {expected}")
    for gate_key, expected in _quality_gate().items():
        if manifest.get("quality_gate", {}).get(gate_key) != expected:
            raise SourceCheckBoardRuntimeError(f"manifest quality_gate {gate_key} must be {expected}")
    for style_key, expected in _style_gate().items():
        if manifest.get("style_gate", {}).get(style_key) != expected:
            raise SourceCheckBoardRuntimeError(f"manifest style_gate {style_key} must be {expected}")
    for interaction_key, expected in _interaction_gate().items():
        if manifest.get("interaction", {}).get(interaction_key) != expected:
            raise SourceCheckBoardRuntimeError(f"manifest interaction {interaction_key} must be {expected}")
    for safety_key, expected in _public_repo_safety().items():
        if manifest.get("public_repo_safety", {}).get(safety_key) is not expected:
            raise SourceCheckBoardRuntimeError(f"manifest public_repo_safety {safety_key} must be {expected}")

    html_text = render_outputs.get("html", {}).get("kmfa_source_check_board")
    if not isinstance(html_text, str):
        raise SourceCheckBoardRuntimeError("render_outputs.html.kmfa_source_check_board is required")
    _validate_html(rows, html_text)
    _ensure_no_forbidden_public_payload({"manifest": manifest, "rows": rows, "render_outputs": render_outputs})


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        value = json.load(f)
    if not isinstance(value, dict):
        raise SourceCheckBoardRuntimeError(f"{path} must contain a JSON object")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise SourceCheckBoardRuntimeError(f"{path} contains a non-object JSONL record")
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


def write_default_source_check_board_artifacts(
    *,
    output_manifest: Path = DEFAULT_OUTPUT_MANIFEST,
    output_rows: Path = DEFAULT_OUTPUT_ROWS,
    output_stage_manifest: Path = DEFAULT_OUTPUT_STAGE_MANIFEST,
    html_output: Path = DEFAULT_HTML_OUTPUT,
    generated_at: str = "2026-07-01T10:00:00+10:00",
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, dict[str, str]]]:
    manifest, rows, render_outputs = build_default_source_check_board_artifacts(generated_at=generated_at)
    validate_source_check_board_artifacts(manifest, rows, render_outputs)
    _write_json(output_manifest, manifest)
    _write_jsonl(output_rows, rows)
    _write_text(html_output, render_outputs["html"]["kmfa_source_check_board"])
    stage_manifest = {
        "schema_version": "kmfa.s11_p2_stage_manifest.v1",
        "record_type": "s11_p2_source_check_board_stage_manifest",
        "project_id": "KMFA",
        "stage_phase": "S11-P2",
        "generated_at": generated_at,
        "status": "completed_validated_local_only_stage_review_pending",
        "content_hash": manifest["content_hash"],
        "artifact_refs": manifest["artifact_refs"],
        "summary": manifest["summary"],
        "quality_gate": manifest["quality_gate"],
        "stage_scope": manifest["stage_scope"],
        "style_gate": manifest["style_gate"],
        "interaction": manifest["interaction"],
        "public_repo_safety": manifest["public_repo_safety"],
        "next_gate": "S11_P3_REQUIRED_OR_STAGE11_REVIEW_AFTER_ALL_PHASES",
    }
    _write_json(output_stage_manifest, stage_manifest)
    return manifest, rows, render_outputs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build KMFA S11-P2 public-safe source check board artifacts.")
    parser.add_argument("--output-manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--output-rows", type=Path, default=DEFAULT_OUTPUT_ROWS)
    parser.add_argument("--output-stage-manifest", type=Path, default=DEFAULT_OUTPUT_STAGE_MANIFEST)
    parser.add_argument("--html-output", type=Path, default=DEFAULT_HTML_OUTPUT)
    parser.add_argument("--generated-at", default="2026-07-01T10:00:00+10:00")
    args = parser.parse_args(argv)

    manifest, rows, _render_outputs = write_default_source_check_board_artifacts(
        output_manifest=args.output_manifest,
        output_rows=args.output_rows,
        output_stage_manifest=args.output_stage_manifest,
        html_output=args.html_output,
        generated_at=args.generated_at,
    )
    summary = manifest["summary"]
    print(
        "PASS: KMFA S11-P2 source check board artifacts generated "
        f"(matrix_rows={len(rows)}, html_exports={summary['html_export_count']}, "
        "columns=11, statuses=5, status_click_detail=true, "
        "blue_gray_surface=true, large_yellow_surface_count=0, "
        "formal_report_allowed=false, s11_p3_scope=false, stage11_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
