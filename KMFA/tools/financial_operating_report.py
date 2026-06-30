#!/usr/bin/env python3
"""Build KMFA S13-P1 public-safe financial operating report drafts."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

DEFAULT_FINANCE_SOURCE_REGISTRY = ROOT / "metadata" / "imports" / "finance_support_source_registry.json"
DEFAULT_FINANCE_FIELD_CANDIDATES = ROOT / "metadata" / "schema_maps" / "finance_field_candidates.jsonl"
DEFAULT_SCOPE_RECONCILIATION_RECORDS = ROOT / "metadata" / "quality" / "scope_reconciliation_records.jsonl"
DEFAULT_REPORT_GRADE_RECORDS = ROOT / "metadata" / "reports" / "report_grade_runtime_records.jsonl"
DEFAULT_OUTPUT_MANIFEST = ROOT / "metadata" / "reports" / "financial_operating_report_manifest.json"
DEFAULT_OUTPUT_LANES = ROOT / "metadata" / "reports" / "financial_operating_report_source_lanes.jsonl"
DEFAULT_OUTPUT_DRAFTS = ROOT / "metadata" / "reports" / "financial_operating_report_drafts.jsonl"
DEFAULT_OUTPUT_STAGE_MANIFEST = (
    ROOT / "stage_artifacts" / "S13_P1_financial_operating_report" / "machine" / "s13_p1_manifest.json"
)
DEFAULT_HTML_OUTPUT_DIR = ROOT / "stage_artifacts" / "S13_P1_financial_operating_report" / "exports" / "html"

REQUIRED_SOURCE_LANES = (
    "operating_situation",
    "expense_tax_asset",
    "cash_situation",
    "loan_detail",
)

LANE_LABELS = {
    "operating_situation": "经营情况",
    "expense_tax_asset": "费用税金资产",
    "cash_situation": "现金情况",
    "loan_detail": "贷款明细",
}

LANE_SOURCE_CATEGORIES = {
    "operating_situation": ("operating_analysis",),
    "expense_tax_asset": ("journal", "tax", "account", "r_and_d_expense"),
    "cash_situation": ("cash", "account"),
    "loan_detail": ("loan",),
}

LANE_STATUS_LABELS = {
    "operating_situation": "结构已接入，正式经营结论受 D 级报告门禁限制",
    "expense_tax_asset": "费用、税金、资产结构已接入，金额结论仍需后续复核",
    "cash_situation": "现金结构已接入，现金安全结论需银行日余额与差异关闭支持",
    "loan_detail": "贷款明细结构已接入，不触发贷款管理或付款动作",
}

REQUIRED_DRAFT_IDS = (
    "financial_operating_weekly_draft",
    "financial_operating_monthly_draft",
)

REPORT_SECTION_TITLES = (
    "经营摘要",
    "经营情况",
    "费用税金资产",
    "现金情况",
    "贷款明细",
    "数据状态与限制",
    "下一步复核事项",
)

SOURCE_TASKPACK_REFS = {
    "roadmap_s13_p1": "KMFA/taskpack/v1_2/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_2.md:S13-P1",
    "human_readable_report_spec": "KMFA/taskpack/v1_2/09_KMFA_前端交互与人类可读报告规范_v1_1.md",
    "business_overview_html_sample": (
        "KMFA/taskpack/v1_2/20_HTML_UIUX_报告预览/01_核心HTML验收样板/"
        "KMFA_经营分析报告预览_v3_blue.html"
    ),
}

UPSTREAM_METADATA_REFS = {
    "finance_support_source_registry": "source_ref://KMFA/S07-P1/finance_support_source_registry",
    "finance_field_candidates": "source_ref://KMFA/S07-P1/finance_field_candidates",
    "project_cost_fact_layer": "source_ref://KMFA/S09-P1/project_cost_fact_layer",
    "project_margin_cash_margin": "source_ref://KMFA/S09-P2/project_margin_cash_margin",
    "scope_reconciliation": "source_ref://KMFA/S09-P3/scope_reconciliation",
    "report_grade_runtime": "source_ref://KMFA/S10-P2/report_grade_runtime",
    "report_export_runtime": "source_ref://KMFA/S10-P3/report_export_runtime",
}

FINANCIAL_OPERATING_REPORT_VERSION = "RPT-KMFA-S13P1-FINANCIAL-OPERATING-DRAFT-001"
FORMULA_VERSION = "FORM-KMFA-S13P1-DRAFT-STATUS-001"
MAPPING_VERSION = "MAP-KMFA-S13P1-PUBLIC-SAFE-v1"
HTML_TEMPLATE_VERSION = "HTML-KMFA-S13P1-BLUE-DRAFT-v1"

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
    "token",
    "api_key",
    "private_key",
}

FORBIDDEN_PUBLIC_SUFFIXES = (".zip", ".xls", ".xlsx", ".pdf", ".sqlite", ".db", ".parquet")
FORBIDDEN_PUBLIC_TEXT = (
    "private://",
    "private_ref://",
    "raw_value",
    "normalized_value",
    "plaintext_value",
    "source_header_text",
    "original_filename",
    "bank_account_number",
    "identity_document_number",
    "password",
    "token",
    "api_key",
    "private_key",
)


class FinancialOperatingReportError(ValueError):
    """Raised when S13-P1 financial operating report artifacts are invalid."""


def _sha256_json(payload: Any) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise FinancialOperatingReportError(f"{path} must contain a JSON object")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            value = json.loads(line)
            if not isinstance(value, dict):
                raise FinancialOperatingReportError(f"{path} contains a non-object JSONL record")
            rows.append(value)
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
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
        "normalized_business_values_committed": False,
        "field_plaintext_committed": False,
        "raw_file_committed": False,
        "private_tabular_files_committed": False,
        "excel_workbook_committed": False,
        "pdf_file_committed": False,
        "credential_secret_committed": False,
        "real_account_number_committed": False,
        "private_ref_committed_in_s13p1_outputs": False,
    }


def _stage_scope() -> dict[str, bool]:
    return {
        "s13_p1_financial_operating_report_scope_included": True,
        "s13_p2_collection_receivable_aging_scope_included": False,
        "s13_p3_cross_table_review_scope_included": False,
        "formal_report_runtime_scope_included": False,
        "complete_trusted_report_scope_included": False,
        "lineage_full_check_scope_included": False,
        "external_connector_scope_included": False,
        "payment_or_bank_operation_scope_included": False,
        "tax_filing_scope_included": False,
        "stage13_review_scope_included": False,
        "github_upload_scope_included": False,
    }


def _quality_gate(*, pending_reconciliation_count: int, report_grade_visible: str) -> dict[str, Any]:
    return {
        "draft_report_allowed": True,
        "weekly_draft_allowed": True,
        "monthly_draft_allowed": True,
        "formal_report_allowed": False,
        "complete_trusted_report_display_allowed": False,
        "business_decision_basis_allowed": False,
        "report_grade_visible": report_grade_visible,
        "report_grade_bypass_allowed": False,
        "quality_grade_bypass_allowed": False,
        "raw_layer_write_allowed": False,
        "derived_amount_calculation_allowed": False,
        "cash_forecast_decision_allowed": False,
        "loan_management_action_allowed": False,
        "payment_or_bank_operation_allowed": False,
        "s13_p2_allowed": False,
        "s13_p3_allowed": False,
        "stage13_review_allowed": False,
        "github_upload_allowed": False,
        "phase_completion_upload_allowed": False,
        "pending_reconciliation_count": pending_reconciliation_count,
        "release_block_reason": "draft_only_pending_s13p2_s13p3_lineage_and_unclosed_reconciliation",
    }


def _report_grade_visible(report_grade_records: list[dict[str, Any]]) -> str:
    grades = {str(row.get("computed_report_grade") or "") for row in report_grade_records}
    if "D" in grades:
        return "D"
    return "D"


def _pending_reconciliation_count(scope_reconciliation_records: list[dict[str, Any]]) -> int:
    return sum(
        1
        for row in scope_reconciliation_records
        if str(row.get("resolution_status") or row.get("status")) == "pending_owner_or_authorized_review"
    )


def _source_registry_by_category(source_registry: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for source in source_registry.get("sources", []):
        if isinstance(source, dict):
            grouped.setdefault(str(source.get("finance_category")), []).append(source)
    return grouped


def _field_candidates_by_category(field_candidates: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for record in field_candidates:
        grouped.setdefault(str(record.get("finance_category")), []).append(record)
    return grouped


def _field_keys(records: list[dict[str, Any]]) -> list[str]:
    keys: list[str] = []
    for record in records:
        canonical_field = record.get("canonical_field", {})
        if isinstance(canonical_field, dict):
            field_key = str(canonical_field.get("field_key") or "")
            if field_key:
                keys.append(field_key)
    return keys


def _source_lane_record(
    *,
    lane_id: str,
    source_registry_by_category: dict[str, list[dict[str, Any]]],
    field_candidates_by_category: dict[str, list[dict[str, Any]]],
    generated_at: str,
) -> dict[str, Any]:
    categories = LANE_SOURCE_CATEGORIES[lane_id]
    source_refs: list[str] = []
    parse_statuses: set[str] = set()
    readonly_parse_flags: list[bool] = []
    field_keys: list[str] = []
    for category in categories:
        for source in source_registry_by_category.get(category, []):
            source_ref = str(source.get("source_ref") or "")
            if source_ref:
                source_refs.append(source_ref)
            parse_statuses.add(str(source.get("parse_status") or "unknown"))
            readonly_parse_flags.append(source.get("read_only_parse") is True)
        field_keys.extend(_field_keys(field_candidates_by_category.get(category, [])))
    field_keys = sorted(set(field_keys))
    source_refs = sorted(set(source_refs))
    return {
        "schema_version": "kmfa.financial_operating_source_lane.v1",
        "record_type": "financial_operating_source_lane",
        "project_id": "KMFA",
        "stage_phase": "S13-P1",
        "lane_id": lane_id,
        "visible_lane_name": LANE_LABELS[lane_id],
        "finance_categories": list(categories),
        "source_refs": source_refs,
        "source_count": len(source_refs),
        "field_mapping_count": len(field_keys),
        "field_key_refs": field_keys,
        "parse_statuses": sorted(parse_statuses),
        "all_sources_readonly": all(readonly_parse_flags) if readonly_parse_flags else False,
        "data_status": "structure_available_values_blocked",
        "status_label": LANE_STATUS_LABELS[lane_id],
        "source_metadata_refs": list(UPSTREAM_METADATA_REFS.values()),
        "raw_business_values_allowed": False,
        "public_amount_values_allowed": False,
        "field_plaintext_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "raw_layer_write_allowed": False,
        "generated_at": generated_at,
    }


def _draft_record(
    *,
    draft_id: str,
    source_lanes: list[dict[str, Any]],
    pending_reconciliation_count: int,
    report_grade_visible: str,
    generated_at: str,
) -> dict[str, Any]:
    period_label = "经营周报初稿" if draft_id.endswith("weekly_draft") else "经营月报初稿"
    html_ref = (
        "KMFA/stage_artifacts/S13_P1_financial_operating_report/exports/html/"
        f"{draft_id}.html"
    )
    data_status_cards = [
        {
            "visible_lane_name": lane["visible_lane_name"],
            "data_status": lane["data_status"],
            "status_label": lane["status_label"],
            "source_count": lane["source_count"],
            "field_mapping_count": lane["field_mapping_count"],
        }
        for lane in source_lanes
    ]
    return {
        "schema_version": "kmfa.financial_operating_report_draft.v1",
        "record_type": "financial_operating_report_draft",
        "project_id": "KMFA",
        "stage_phase": "S13-P1",
        "draft_id": draft_id,
        "draft_version": FINANCIAL_OPERATING_REPORT_VERSION,
        "visible_report_name": period_label,
        "visible_section_titles": list(REPORT_SECTION_TITLES),
        "data_status_cards": data_status_cards,
        "html_draft_ref": html_ref,
        "html_template_version": HTML_TEMPLATE_VERSION,
        "source_taskpack_refs": SOURCE_TASKPACK_REFS,
        "source_metadata_refs": list(UPSTREAM_METADATA_REFS.values()),
        "report_grade_visible": report_grade_visible,
        "pending_reconciliation_count": pending_reconciliation_count,
        "draft_report_allowed": True,
        "formal_report_allowed": False,
        "complete_trusted_report_display_allowed": False,
        "business_decision_basis_allowed": False,
        "lineage_full_check_included": False,
        "s13_p2_scope_included": False,
        "s13_p3_scope_included": False,
        "external_connector_included": False,
        "payment_or_bank_operation_allowed": False,
        "tax_filing_allowed": False,
        "contains_raw_business_values": False,
        "contains_field_plaintext": False,
        "generated_at": generated_at,
        "limitations": [
            "本记录是经营周报/月报初稿，不是正式可信经营报告。",
            "存在未关闭 reconciliation 和缺失 lineage full check 时，不得作为经营决策依据。",
            "S13-P1 不接入回款应收账龄明细、不执行跨表复核、不触发付款、税务申报或贷款管理动作。",
        ],
    }


def _render_html(draft: dict[str, Any]) -> str:
    report_name = html.escape(str(draft["visible_report_name"]))
    report_grade = html.escape(str(draft["report_grade_visible"]))
    rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(str(card['visible_lane_name']))}</td>"
        f"<td>{html.escape(str(card['status_label']))}</td>"
        f"<td>{int(card['source_count'])}</td>"
        f"<td>{int(card['field_mapping_count'])}</td>"
        "</tr>"
        for card in draft["data_status_cards"]
    )
    section_rows = "\n".join(
        f"<li>{html.escape(title)}<span>公开安全摘要和限制说明</span></li>"
        for title in draft["visible_section_titles"]
    )
    pending_count = int(draft["pending_reconciliation_count"])
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>KMFA {report_name}</title>
  <style>
    :root {{ --navy:#10233f; --blue:#2367d1; --cyan:#dff4ff; --line:#d7e3f2; --ink:#172033; --muted:#66758a; --card:#ffffff; --warn:#a16207; --stop:#b91c1c; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:#f5f8fc; color:var(--ink); font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",Arial,sans-serif; }}
    header {{ background:linear-gradient(135deg,var(--navy),#17477d); color:#fff; padding:28px 34px; }}
    .brand {{ display:flex; align-items:center; gap:12px; margin-bottom:18px; }}
    .logo {{ width:48px; height:48px; border-radius:8px; background:#1d4ed8; display:flex; align-items:center; justify-content:center; font-weight:800; }}
    h1 {{ margin:0 0 8px; font-size:28px; letter-spacing:0; }}
    .sub {{ color:#dbeafe; line-height:1.65; max-width:980px; }}
    main {{ max-width:1120px; margin:0 auto; padding:22px; }}
    .cards {{ display:grid; grid-template-columns:repeat(3,1fr); gap:14px; margin-top:-34px; }}
    .card {{ background:var(--card); border:1px solid var(--line); border-radius:8px; padding:18px; box-shadow:0 12px 26px rgba(15,23,42,.07); }}
    .label {{ color:var(--muted); font-size:13px; }}
    .num {{ font-size:24px; font-weight:800; color:var(--blue); margin-top:6px; }}
    .stop {{ color:var(--stop); }}
    table {{ width:100%; border-collapse:collapse; margin-top:12px; background:white; border:1px solid var(--line); }}
    th,td {{ text-align:left; border-bottom:1px solid var(--line); padding:11px 12px; line-height:1.55; }}
    th {{ background:var(--cyan); color:#153e75; }}
    ul {{ margin:10px 0 0; padding:0; display:grid; grid-template-columns:repeat(2,1fr); gap:10px; list-style:none; }}
    li {{ border:1px solid var(--line); border-radius:8px; padding:12px; background:#fbfdff; font-weight:700; }}
    li span {{ display:block; color:var(--muted); font-size:13px; font-weight:400; margin-top:5px; }}
    .notice {{ border-left:4px solid var(--warn); background:#fff7ed; padding:12px 14px; line-height:1.65; }}
    @media(max-width:820px) {{ .cards, ul {{ grid-template-columns:1fr; }} header, main {{ padding-left:16px; padding-right:16px; }} }}
  </style>
</head>
<body>
  <header>
    <div class="brand"><div class="logo">KM</div><div><strong>KMFA 经营分析系统</strong><div class="sub">财务经营报表初稿 · 公开安全 · 蓝色商务版</div></div></div>
    <h1>{report_name}</h1>
    <div class="sub">本初稿只展示经营情况、费用税金资产、现金情况和贷款明细的数据状态与限制，不展示真实金额、客户明细、项目明文或账号信息。</div>
  </header>
  <main>
    <section class="cards">
      <div class="card"><div class="label">报告等级</div><div class="num">报告等级 {report_grade}</div><div class="label">正式经营报告仍被阻断</div></div>
      <div class="card"><div class="label">未关闭差异</div><div class="num stop">{pending_count} 项</div><div class="label">需要 owner 或授权复核</div></div>
      <div class="card"><div class="label">报告权限</div><div class="num stop">初稿</div><div class="label">不可作为正式经营决策依据</div></div>
    </section>
    <section class="card" style="margin-top:16px">
      <h2>数据状态</h2>
      <table>
        <thead><tr><th>模块</th><th>状态与限制</th><th>来源数</th><th>字段映射数</th></tr></thead>
        <tbody>
{rows}
        </tbody>
      </table>
    </section>
    <section class="card" style="margin-top:16px">
      <h2>报告章节</h2>
      <ul>
{section_rows}
      </ul>
    </section>
    <section class="card" style="margin-top:16px">
      <h2>使用限制</h2>
      <div class="notice">S13-P1 仅生成周报/月报初稿。回款应收账龄、跨表复核、完整 lineage、正式报告、外部接口、付款、贷款管理和税务申报均不在本 phase 范围内。</div>
    </section>
  </main>
</body>
</html>
"""


def _ensure_no_forbidden_public_payload(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in FORBIDDEN_PUBLIC_KEYS:
                raise FinancialOperatingReportError(f"forbidden public key found: {key}")
            _ensure_no_forbidden_public_payload(item)
    elif isinstance(value, list):
        for item in value:
            _ensure_no_forbidden_public_payload(item)
    elif isinstance(value, str):
        lowered = value.lower()
        if any(suffix in lowered for suffix in FORBIDDEN_PUBLIC_SUFFIXES):
            raise FinancialOperatingReportError(f"forbidden private business file reference found: {value}")
        if any(text in lowered for text in FORBIDDEN_PUBLIC_TEXT):
            raise FinancialOperatingReportError(f"forbidden private/raw marker found: {value}")


def build_default_financial_operating_report_artifacts(
    *,
    generated_at: str = "2026-07-01T17:00:00+10:00",
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], dict[str, str]]:
    source_registry = read_json(DEFAULT_FINANCE_SOURCE_REGISTRY)
    field_candidates = read_jsonl(DEFAULT_FINANCE_FIELD_CANDIDATES)
    reconciliation_records = read_jsonl(DEFAULT_SCOPE_RECONCILIATION_RECORDS)
    report_grade_records = read_jsonl(DEFAULT_REPORT_GRADE_RECORDS)

    registry_by_category = _source_registry_by_category(source_registry)
    fields_by_category = _field_candidates_by_category(field_candidates)
    pending_reconciliation_count = _pending_reconciliation_count(reconciliation_records)
    report_grade_visible = _report_grade_visible(report_grade_records)

    source_lanes = [
        _source_lane_record(
            lane_id=lane_id,
            source_registry_by_category=registry_by_category,
            field_candidates_by_category=fields_by_category,
            generated_at=generated_at,
        )
        for lane_id in REQUIRED_SOURCE_LANES
    ]
    drafts = [
        _draft_record(
            draft_id=draft_id,
            source_lanes=source_lanes,
            pending_reconciliation_count=pending_reconciliation_count,
            report_grade_visible=report_grade_visible,
            generated_at=generated_at,
        )
        for draft_id in REQUIRED_DRAFT_IDS
    ]
    html_outputs = {draft["draft_id"]: _render_html(draft) for draft in drafts}

    manifest = {
        "schema_version": "kmfa.financial_operating_report_manifest.v1",
        "record_type": "financial_operating_report_manifest",
        "project_id": "KMFA",
        "stage_phase": "S13-P1",
        "report_version": FINANCIAL_OPERATING_REPORT_VERSION,
        "formula_version": FORMULA_VERSION,
        "mapping_version": MAPPING_VERSION,
        "html_template_version": HTML_TEMPLATE_VERSION,
        "generated_at": generated_at,
        "runtime_status": "public_safe_financial_operating_drafts_created_formal_report_blocked",
        "required_source_lanes": list(REQUIRED_SOURCE_LANES),
        "required_draft_ids": list(REQUIRED_DRAFT_IDS),
        "required_section_titles": list(REPORT_SECTION_TITLES),
        "source_taskpack_refs": SOURCE_TASKPACK_REFS,
        "upstream_metadata_refs": UPSTREAM_METADATA_REFS,
        "quality_gate": _quality_gate(
            pending_reconciliation_count=pending_reconciliation_count,
            report_grade_visible=report_grade_visible,
        ),
        "stage_scope": _stage_scope(),
        "public_repo_safety": _public_repo_safety(),
        "artifact_refs": {
            "financial_operating_report_manifest": "KMFA/metadata/reports/financial_operating_report_manifest.json",
            "financial_operating_report_source_lanes": "KMFA/metadata/reports/financial_operating_report_source_lanes.jsonl",
            "financial_operating_report_drafts": "KMFA/metadata/reports/financial_operating_report_drafts.jsonl",
            "weekly_html_draft": "KMFA/stage_artifacts/S13_P1_financial_operating_report/exports/html/financial_operating_weekly_draft.html",
            "monthly_html_draft": "KMFA/stage_artifacts/S13_P1_financial_operating_report/exports/html/financial_operating_monthly_draft.html",
            "validator": "KMFA/tools/check_s13_p1_financial_operating_report.py",
            "completion_record": "KMFA/stage_artifacts/S13_P1_financial_operating_report/human/s13_p1_completion_record.md",
            "test_results": "KMFA/stage_artifacts/S13_P1_financial_operating_report/human/test_results.md",
            "stage_manifest": "KMFA/stage_artifacts/S13_P1_financial_operating_report/machine/s13_p1_manifest.json",
        },
        "summary": {
            "source_lane_count": len(source_lanes),
            "draft_report_count": len(drafts),
            "html_draft_count": len(html_outputs),
            "formal_report_count": 0,
            "business_decision_basis_count": 0,
            "source_count": sum(int(lane["source_count"]) for lane in source_lanes),
            "field_mapping_count": sum(int(lane["field_mapping_count"]) for lane in source_lanes),
            "pending_reconciliation_count": pending_reconciliation_count,
            "report_grade_visible": report_grade_visible,
        },
        "limitations": [
            "S13-P1 只生成财务经营周报/月报初稿，不生成正式可信经营报告。",
            "S13-P2 回款应收账龄、S13-P3 跨表复核、lineage full check 和外部接口均未执行。",
            "存在 12 条 pending owner 或授权复核差异时，报告等级显示为 D，经营决策依据继续阻断。",
        ],
    }
    manifest["content_hash"] = _sha256_json(
        {"manifest": manifest, "source_lanes": source_lanes, "drafts": drafts, "html_outputs": html_outputs}
    )
    return manifest, source_lanes, drafts, html_outputs


def validate_financial_operating_report_artifacts(
    manifest: dict[str, Any],
    source_lanes: list[dict[str, Any]],
    drafts: list[dict[str, Any]],
    html_outputs: dict[str, str] | None = None,
) -> None:
    if manifest.get("schema_version") != "kmfa.financial_operating_report_manifest.v1":
        raise FinancialOperatingReportError("manifest schema_version mismatch")
    if manifest.get("stage_phase") != "S13-P1":
        raise FinancialOperatingReportError("manifest stage_phase must be S13-P1")
    if tuple(manifest.get("required_source_lanes", [])) != REQUIRED_SOURCE_LANES:
        raise FinancialOperatingReportError("manifest required_source_lanes mismatch")
    if tuple(manifest.get("required_draft_ids", [])) != REQUIRED_DRAFT_IDS:
        raise FinancialOperatingReportError("manifest required_draft_ids mismatch")
    if tuple(manifest.get("required_section_titles", [])) != REPORT_SECTION_TITLES:
        raise FinancialOperatingReportError("manifest required_section_titles mismatch")

    expected_summary = {
        "source_lane_count": 4,
        "draft_report_count": 2,
        "html_draft_count": 2,
        "formal_report_count": 0,
        "business_decision_basis_count": 0,
        "pending_reconciliation_count": 12,
        "report_grade_visible": "D",
    }
    for key, expected in expected_summary.items():
        if manifest.get("summary", {}).get(key) != expected:
            raise FinancialOperatingReportError(f"manifest summary {key} must be {expected}")

    for scope_key, expected in _stage_scope().items():
        if manifest.get("stage_scope", {}).get(scope_key) is not expected:
            raise FinancialOperatingReportError(f"manifest stage_scope {scope_key} must be {expected}")
    for gate_key, expected in _quality_gate(pending_reconciliation_count=12, report_grade_visible="D").items():
        if manifest.get("quality_gate", {}).get(gate_key) != expected:
            raise FinancialOperatingReportError(f"manifest quality_gate {gate_key} must be {expected}")
    for safety_key, expected in _public_repo_safety().items():
        if manifest.get("public_repo_safety", {}).get(safety_key) is not expected:
            raise FinancialOperatingReportError(f"manifest public_repo_safety {safety_key} must be {expected}")

    lane_by_id = {str(lane.get("lane_id")): lane for lane in source_lanes}
    if tuple(lane_by_id) != REQUIRED_SOURCE_LANES:
        raise FinancialOperatingReportError("source lane order or ids mismatch")
    for lane_id in REQUIRED_SOURCE_LANES:
        lane = lane_by_id[lane_id]
        if lane.get("visible_lane_name") != LANE_LABELS[lane_id]:
            raise FinancialOperatingReportError(f"{lane_id}.visible_lane_name mismatch")
        if tuple(lane.get("finance_categories", [])) != LANE_SOURCE_CATEGORIES[lane_id]:
            raise FinancialOperatingReportError(f"{lane_id}.finance_categories mismatch")
        if int(lane.get("source_count", 0)) < 1:
            raise FinancialOperatingReportError(f"{lane_id}.source_count must be >= 1")
        if int(lane.get("field_mapping_count", 0)) < 5:
            raise FinancialOperatingReportError(f"{lane_id}.field_mapping_count must be >= 5")
        for field_name in (
            "raw_business_values_allowed",
            "public_amount_values_allowed",
            "field_plaintext_allowed",
            "formal_report_allowed",
            "business_decision_basis_allowed",
            "raw_layer_write_allowed",
        ):
            if lane.get(field_name) is not False:
                raise FinancialOperatingReportError(f"{lane_id}.{field_name} must be false")
        if lane.get("all_sources_readonly") is not True:
            raise FinancialOperatingReportError(f"{lane_id}.all_sources_readonly must be true")

    draft_by_id = {str(draft.get("draft_id")): draft for draft in drafts}
    if tuple(draft_by_id) != REQUIRED_DRAFT_IDS:
        raise FinancialOperatingReportError("draft order or ids mismatch")
    for draft_id, draft in draft_by_id.items():
        if tuple(draft.get("visible_section_titles", [])) != REPORT_SECTION_TITLES:
            raise FinancialOperatingReportError(f"{draft_id}.visible_section_titles mismatch")
        if len(draft.get("data_status_cards", [])) != len(REQUIRED_SOURCE_LANES):
            raise FinancialOperatingReportError(f"{draft_id}.data_status_cards count mismatch")
        for field_name in (
            "formal_report_allowed",
            "complete_trusted_report_display_allowed",
            "business_decision_basis_allowed",
            "lineage_full_check_included",
            "s13_p2_scope_included",
            "s13_p3_scope_included",
            "external_connector_included",
            "payment_or_bank_operation_allowed",
            "tax_filing_allowed",
            "contains_raw_business_values",
            "contains_field_plaintext",
        ):
            if draft.get(field_name) is not False:
                raise FinancialOperatingReportError(f"{draft_id}.{field_name} must be false")
        if draft.get("draft_report_allowed") is not True:
            raise FinancialOperatingReportError(f"{draft_id}.draft_report_allowed must be true")
        if draft.get("report_grade_visible") != "D":
            raise FinancialOperatingReportError(f"{draft_id}.report_grade_visible must be D")

    if html_outputs is not None:
        if set(html_outputs) != set(REQUIRED_DRAFT_IDS):
            raise FinancialOperatingReportError("html output ids mismatch")
        for draft_id, html_text in html_outputs.items():
            if not html_text.startswith("<!doctype html>"):
                raise FinancialOperatingReportError(f"{draft_id} html must start with <!doctype html>")
            for required_text in ("KMFA 经营分析系统", "报告等级 D", "不可作为正式经营决策依据", "数据状态"):
                if required_text not in html_text:
                    raise FinancialOperatingReportError(f"{draft_id} html missing required text: {required_text}")
            for forbidden_text in FORBIDDEN_PUBLIC_TEXT:
                if forbidden_text in html_text.lower():
                    raise FinancialOperatingReportError(f"{draft_id} html contains forbidden text: {forbidden_text}")
            for forbidden_suffix in FORBIDDEN_PUBLIC_SUFFIXES:
                if forbidden_suffix in html_text.lower():
                    raise FinancialOperatingReportError(f"{draft_id} html contains forbidden suffix: {forbidden_suffix}")

    _ensure_no_forbidden_public_payload({"manifest": manifest, "source_lanes": source_lanes, "drafts": drafts})


def write_default_financial_operating_report_artifacts(
    *,
    output_manifest: Path = DEFAULT_OUTPUT_MANIFEST,
    output_lanes: Path = DEFAULT_OUTPUT_LANES,
    output_drafts: Path = DEFAULT_OUTPUT_DRAFTS,
    output_stage_manifest: Path = DEFAULT_OUTPUT_STAGE_MANIFEST,
    html_output_dir: Path = DEFAULT_HTML_OUTPUT_DIR,
    generated_at: str = "2026-07-01T17:00:00+10:00",
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], dict[str, str]]:
    manifest, source_lanes, drafts, html_outputs = build_default_financial_operating_report_artifacts(
        generated_at=generated_at
    )
    validate_financial_operating_report_artifacts(manifest, source_lanes, drafts, html_outputs)
    write_json(output_manifest, manifest)
    write_jsonl(output_lanes, source_lanes)
    write_jsonl(output_drafts, drafts)
    html_output_dir.mkdir(parents=True, exist_ok=True)
    for draft_id, html_text in html_outputs.items():
        (html_output_dir / f"{draft_id}.html").write_text(html_text, encoding="utf-8")
    stage_manifest = {
        "schema_version": "kmfa.s13_p1_stage_manifest.v1",
        "record_type": "s13_p1_financial_operating_report_stage_manifest",
        "project_id": "KMFA",
        "stage_phase": "S13-P1",
        "generated_at": generated_at,
        "status": "completed_validated_local_only",
        "content_hash": manifest["content_hash"],
        "artifact_refs": manifest["artifact_refs"],
        "summary": manifest["summary"],
        "quality_gate": manifest["quality_gate"],
        "stage_scope": manifest["stage_scope"],
        "public_repo_safety": manifest["public_repo_safety"],
    }
    write_json(output_stage_manifest, stage_manifest)
    return manifest, source_lanes, drafts, html_outputs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build KMFA S13-P1 financial operating report artifacts.")
    parser.add_argument("--output-manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--output-lanes", type=Path, default=DEFAULT_OUTPUT_LANES)
    parser.add_argument("--output-drafts", type=Path, default=DEFAULT_OUTPUT_DRAFTS)
    parser.add_argument("--output-stage-manifest", type=Path, default=DEFAULT_OUTPUT_STAGE_MANIFEST)
    parser.add_argument("--html-output-dir", type=Path, default=DEFAULT_HTML_OUTPUT_DIR)
    parser.add_argument("--generated-at", default="2026-07-01T17:00:00+10:00")
    args = parser.parse_args(argv)

    manifest, source_lanes, drafts, html_outputs = write_default_financial_operating_report_artifacts(
        output_manifest=args.output_manifest,
        output_lanes=args.output_lanes,
        output_drafts=args.output_drafts,
        output_stage_manifest=args.output_stage_manifest,
        html_output_dir=args.html_output_dir,
        generated_at=args.generated_at,
    )
    summary = manifest["summary"]
    print(
        "PASS: KMFA S13-P1 financial operating report artifacts generated "
        f"(source_lanes={len(source_lanes)}, drafts={len(drafts)}, html={len(html_outputs)}, "
        f"field_mappings={summary['field_mapping_count']}, "
        "formal_report_allowed=false, s13_p2_scope=false, s13_p3_scope=false, "
        "lineage_full_check_scope=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
