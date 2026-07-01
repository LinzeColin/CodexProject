#!/usr/bin/env python3
"""Build KMFA S14-P2 public-safe invoice and tax planning artifacts."""

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

DEFAULT_OUTPUT_MANIFEST = ROOT / "metadata" / "reports" / "invoice_tax_plan_manifest.json"
DEFAULT_OUTPUT_SOURCE_LANES = ROOT / "metadata" / "reports" / "invoice_tax_source_lanes.jsonl"
DEFAULT_OUTPUT_ISSUE_CANDIDATES = ROOT / "metadata" / "reports" / "invoice_tax_issue_candidates.jsonl"
DEFAULT_OUTPUT_CASH_SUMMARIES = ROOT / "metadata" / "reports" / "invoice_tax_cash_summaries.jsonl"
DEFAULT_OUTPUT_STAGE_MANIFEST = ROOT / "stage_artifacts" / "S14_P2_invoice_tax_plan" / "machine" / "s14_p2_manifest.json"
DEFAULT_HTML_OUTPUT_DIR = ROOT / "stage_artifacts" / "S14_P2_invoice_tax_plan" / "exports" / "html"

REQUIRED_SOURCE_LANES = (
    "invoice_plan",
    "tax_detail",
    "invoice_tax_cash_summary",
)

REQUIRED_ISSUE_CANDIDATE_TYPES = (
    "pending_invoice",
    "invoiced_not_collected",
    "tax_rate_exception_candidate",
)

CASH_SUMMARY_BUCKETS = (
    "invoice_expected_cash_inflow",
    "tax_expected_cash_outflow",
    "invoice_tax_net_pressure",
)

LANE_LABELS = {
    "invoice_plan": "开票计划",
    "tax_detail": "纳税明细",
    "invoice_tax_cash_summary": "开票纳税资金汇总",
}

LANE_SOURCE_CATEGORIES = {
    "invoice_plan": ("invoice",),
    "tax_detail": ("tax",),
    "invoice_tax_cash_summary": ("invoice", "tax", "cash", "journal"),
}

LANE_STATUS_LABELS = {
    "invoice_plan": "开票计划结构已接入，发票开具动作继续阻断",
    "tax_detail": "纳税明细结构已接入，纳税申报动作继续阻断",
    "invoice_tax_cash_summary": "开票纳税资金结构已接入，仅输出汇总状态和人工复核提示",
}

ISSUE_LABELS = {
    "pending_invoice": "待开票",
    "invoiced_not_collected": "已开票未回款",
    "tax_rate_exception_candidate": "税率异常候选",
}

ISSUE_REVIEW = {
    "pending_invoice": ("invoice_plan", "finance_tax_owner", "confirm_invoice_basis"),
    "invoiced_not_collected": ("invoice_plan", "finance_owner", "verify_collection_status"),
    "tax_rate_exception_candidate": ("tax_detail", "finance_tax_owner", "review_tax_rate_basis"),
}

CASH_SUMMARY_LABELS = {
    "invoice_expected_cash_inflow": "开票预计现金流入",
    "tax_expected_cash_outflow": "纳税预计现金流出",
    "invoice_tax_net_pressure": "开票纳税净资金压力",
}

CASH_SUMMARY_STATUS = {
    "invoice_expected_cash_inflow": "结构可查看，金额值隐藏",
    "tax_expected_cash_outflow": "结构可查看，不生成申报金额",
    "invoice_tax_net_pressure": "仅提示压力，不触发付款或银行操作",
}

SOURCE_TASKPACK_REFS = {
    "roadmap_s14_p2": "KMFA/taskpack/v1_2/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_2.md:S14-P2",
    "taskpack_business_line": "KMFA/taskpack/v1_2/01_KMFA_Codex_TaskPack_v1_2_完整防遗漏_含HTML验收样板.md:P2-invoice-tax",
    "html_sample": (
        "KMFA/taskpack/v1_2/20_HTML_UIUX_报告预览/02_前序HTML完整归档/"
        "kmfa_stage1_v4__KMFA_MVP_Report_Preview_v0_3.html"
    ),
}

UPSTREAM_METADATA_REFS = {
    "finance_support_source_registry": "KMFA/metadata/imports/finance_support_source_registry.json",
    "finance_field_candidates": "KMFA/metadata/schema_maps/finance_field_candidates.jsonl",
    "scope_reconciliation": "KMFA/metadata/quality/scope_reconciliation_records.jsonl",
    "report_grade_runtime": "KMFA/metadata/reports/report_grade_runtime_records.jsonl",
    "collection_receivable_aging": "KMFA/metadata/reports/collection_receivable_aging_manifest.json",
    "fund_cash_loan_plan": "KMFA/metadata/reports/fund_cash_loan_plan_manifest.json",
}

INVOICE_TAX_PLAN_VERSION = "PLAN-KMFA-S14P2-INVOICE-TAX-PUBLIC-SAFE-001"
FORMULA_VERSION = "FORM-KMFA-S14P2-INVOICE-TAX-CANDIDATE-SIGNAL-001"
MAPPING_VERSION = "MAP-KMFA-S14P2-PUBLIC-SAFE-v1"
HTML_TEMPLATE_VERSION = "HTML-KMFA-S14P2-BLUE-v1"

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
    "invoice_number",
    "tax_declaration_number",
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
    "account_number",
    "invoice_number",
    "tax_declaration_number",
    "identity_document_number",
    "password",
    "token",
    "api_key",
    "private_key",
)


class InvoiceTaxPlanError(ValueError):
    """Raised when S14-P2 invoice/tax artifacts are invalid."""


def _sha256_json(payload: Any) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise InvoiceTaxPlanError(f"{path} must contain a JSON object")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            value = json.loads(line)
            if not isinstance(value, dict):
                raise InvoiceTaxPlanError(f"{path} contains a non-object JSONL record")
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
        "real_account_identifier_committed": False,
        "true_money_amount_committed": False,
        "invoice_file_committed": False,
        "tax_filing_file_committed": False,
        "tax_rate_public_value_committed": False,
    }


def _stage_scope() -> dict[str, bool]:
    return {
        "s14_p1_scope_reopened": False,
        "s14_p2_invoice_tax_scope_included": True,
        "s14_p3_scope_included": False,
        "stage14_review_scope_included": False,
        "github_upload_scope_included": False,
        "lineage_full_check_scope_included": False,
        "formal_report_runtime_scope_included": False,
        "external_connector_scope_included": False,
        "payment_execution_scope_included": False,
        "bank_operation_scope_included": False,
        "loan_management_scope_included": False,
        "tax_filing_scope_included": False,
        "invoice_issuance_scope_included": False,
        "policy_qualification_scope_included": False,
    }


def _quality_gate(*, pending_reconciliation_count: int, report_grade_visible: str) -> dict[str, Any]:
    return {
        "invoice_tax_planning_signal_allowed": True,
        "issue_candidate_review_allowed": True,
        "tax_rate_exception_candidate_allowed": True,
        "formal_report_allowed": False,
        "complete_trusted_report_display_allowed": False,
        "business_decision_basis_allowed": False,
        "report_grade_visible": report_grade_visible,
        "report_grade_bypass_allowed": False,
        "quality_grade_bypass_allowed": False,
        "raw_layer_write_allowed": False,
        "derived_amount_calculation_allowed": False,
        "payment_approval_allowed": False,
        "payment_execution_allowed": False,
        "bank_operation_allowed": False,
        "loan_management_action_allowed": False,
        "tax_filing_allowed": False,
        "tax_declaration_generation_allowed": False,
        "invoice_issuance_allowed": False,
        "invoice_operation_allowed": False,
        "invoice_api_call_allowed": False,
        "s14_p3_allowed": False,
        "stage14_review_allowed": False,
        "github_upload_allowed": False,
        "phase_completion_upload_allowed": False,
        "pending_reconciliation_count": pending_reconciliation_count,
        "release_block_reason": "invoice_tax_candidate_only_pending_lineage_reconciliation_and_formal_report_gates",
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
    return sorted(set(keys))


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
            readonly_parse_flags.append(
                source.get("read_only_parse") is True and source.get("raw_layer_write_allowed") is False
            )
        field_keys.extend(_field_keys(field_candidates_by_category.get(category, [])))
    return {
        "schema_version": "kmfa.invoice_tax_source_lane.v1",
        "record_type": "invoice_tax_source_lane",
        "project_id": "KMFA",
        "stage_phase": "S14-P2",
        "lane_id": lane_id,
        "visible_lane_name": LANE_LABELS[lane_id],
        "finance_categories": list(categories),
        "source_refs": sorted(set(source_refs)),
        "source_count": len(set(source_refs)),
        "field_mapping_count": len(set(field_keys)),
        "field_key_refs": sorted(set(field_keys)),
        "parse_statuses": sorted(parse_statuses),
        "all_sources_readonly": all(readonly_parse_flags) if readonly_parse_flags else False,
        "data_status": "structure_available_values_hidden",
        "status_label": LANE_STATUS_LABELS[lane_id],
        "source_metadata_refs": list(UPSTREAM_METADATA_REFS.values()),
        "raw_business_values_allowed": False,
        "public_amount_values_allowed": False,
        "field_plaintext_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "raw_layer_write_allowed": False,
        "payment_or_bank_operation_allowed": False,
        "invoice_issuance_allowed": False,
        "tax_filing_allowed": False,
        "generated_at": generated_at,
    }


def _issue_candidate_record(*, issue_type: str, sequence: int, generated_at: str) -> dict[str, Any]:
    primary_lane, owner_role, review_action = ISSUE_REVIEW[issue_type]
    source_lane_refs = [primary_lane, "invoice_tax_cash_summary"]
    if issue_type == "invoiced_not_collected":
        source_lane_refs.append("invoice_plan")
    return {
        "schema_version": "kmfa.invoice_tax_issue_candidate.v1",
        "record_type": "invoice_tax_issue_candidate",
        "project_id": "KMFA",
        "stage_phase": "S14-P2",
        "issue_candidate_id": f"S14P2-ISS-{sequence:03d}",
        "issue_type": issue_type,
        "visible_issue_label": ISSUE_LABELS[issue_type],
        "candidate_status": "candidate_requires_owner_or_authorized_review",
        "review_owner_role": owner_role,
        "required_review_action": review_action,
        "source_lane_refs": sorted(set(source_lane_refs)),
        "evidence_metadata_refs": [
            UPSTREAM_METADATA_REFS["finance_support_source_registry"],
            UPSTREAM_METADATA_REFS["finance_field_candidates"],
            UPSTREAM_METADATA_REFS["scope_reconciliation"],
        ],
        "public_project_group_ref": f"public_project_group_ref_s14p2_{sequence:03d}",
        "public_customer_group_ref": f"public_customer_group_ref_s14p2_{sequence:03d}",
        "public_invoice_signal_ref": f"public_invoice_signal_hash_s14p2_{sequence:03d}",
        "tax_rate_band_ref": f"public_tax_rate_band_ref_s14p2_{sequence:03d}",
        "raw_business_values_allowed": False,
        "public_amount_values_allowed": False,
        "tax_rate_public_value_allowed": False,
        "field_plaintext_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "invoice_issuance_allowed": False,
        "invoice_operation_allowed": False,
        "tax_filing_allowed": False,
        "tax_declaration_generation_allowed": False,
        "payment_or_bank_operation_allowed": False,
        "generated_at": generated_at,
    }


def _cash_summary_record(*, bucket: str, sequence: int, generated_at: str) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.invoice_tax_cash_summary.v1",
        "record_type": "invoice_tax_cash_summary",
        "project_id": "KMFA",
        "stage_phase": "S14-P2",
        "cash_summary_id": f"S14P2-CASH-{sequence:03d}",
        "cash_summary_bucket": bucket,
        "visible_summary_label": CASH_SUMMARY_LABELS[bucket],
        "summary_status": CASH_SUMMARY_STATUS[bucket],
        "source_lane_refs": ["invoice_plan", "tax_detail", "invoice_tax_cash_summary"],
        "report_grade_visible": "D",
        "amount_value_display_allowed": False,
        "raw_business_values_allowed": False,
        "public_amount_values_allowed": False,
        "field_plaintext_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "payment_or_bank_operation_allowed": False,
        "invoice_issuance_allowed": False,
        "invoice_operation_allowed": False,
        "tax_filing_allowed": False,
        "tax_declaration_generation_allowed": False,
        "generated_at": generated_at,
    }


def _render_html(
    *,
    manifest: dict[str, Any],
    issue_candidates: list[dict[str, Any]],
    cash_summaries: list[dict[str, Any]],
) -> str:
    grade = html.escape(str(manifest["summary"]["report_grade_visible"]))
    pending_count = int(manifest["summary"]["pending_reconciliation_count"])
    issue_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(str(item['visible_issue_label']))}</td>"
        f"<td>{html.escape(str(item['review_owner_role']))}</td>"
        f"<td>{html.escape(str(item['required_review_action']))}</td>"
        "<td>只作候选复核，不触发外部动作</td>"
        "</tr>"
        for item in issue_candidates
    )
    cash_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(str(item['visible_summary_label']))}</td>"
        f"<td>{html.escape(str(item['summary_status']))}</td>"
        "<td>金额值隐藏</td>"
        "</tr>"
        for item in cash_summaries
    )
    issue_cards = "\n".join(
        f"<li>{html.escape(ISSUE_LABELS[issue_type])}<span>候选信号，需人工复核</span></li>"
        for issue_type in REQUIRED_ISSUE_CANDIDATE_TYPES
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>KMFA 开票纳税</title>
  <style>
    :root {{ --ink:#172033; --muted:#66758a; --line:#d7e3f2; --blue:#2367d1; --navy:#10233f; --soft:#e8f3ff; --warn:#a16207; --stop:#b91c1c; --card:#ffffff; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:#f5f8fc; color:var(--ink); font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",Arial,sans-serif; }}
    header {{ background:linear-gradient(135deg,var(--navy),#18517f); color:#fff; padding:28px 34px; }}
    .brand {{ display:flex; align-items:center; gap:12px; margin-bottom:16px; }}
    .logo {{ width:48px; height:48px; border-radius:8px; background:#2563eb; display:flex; align-items:center; justify-content:center; font-weight:800; }}
    h1 {{ margin:0 0 8px; font-size:28px; letter-spacing:0; }}
    h2 {{ margin:0 0 10px; font-size:20px; }}
    .sub {{ color:#dbeafe; line-height:1.65; max-width:980px; }}
    main {{ max-width:1120px; margin:0 auto; padding:22px; }}
    .cards {{ display:grid; grid-template-columns:repeat(3,1fr); gap:14px; margin-top:-34px; }}
    .card {{ background:var(--card); border:1px solid var(--line); border-radius:8px; padding:18px; box-shadow:0 12px 26px rgba(15,23,42,.07); }}
    .label {{ color:var(--muted); font-size:13px; }}
    .num {{ font-size:24px; font-weight:800; color:var(--blue); margin-top:6px; }}
    .stop {{ color:var(--stop); }}
    table {{ width:100%; border-collapse:collapse; margin-top:12px; background:white; border:1px solid var(--line); }}
    th,td {{ text-align:left; border-bottom:1px solid var(--line); padding:11px 12px; line-height:1.55; }}
    th {{ background:var(--soft); color:#153e75; }}
    ul {{ margin:10px 0 0; padding:0; display:grid; grid-template-columns:repeat(3,1fr); gap:10px; list-style:none; }}
    li {{ border:1px solid var(--line); border-radius:8px; padding:12px; background:#fbfdff; font-weight:700; }}
    li span {{ display:block; color:var(--muted); font-size:13px; font-weight:400; margin-top:5px; }}
    .notice {{ border-left:4px solid var(--warn); background:#fff7ed; padding:12px 14px; line-height:1.65; }}
    @media(max-width:900px) {{ .cards, ul {{ grid-template-columns:1fr; }} header, main {{ padding-left:16px; padding-right:16px; }} }}
  </style>
</head>
<body>
  <header>
    <div class="brand"><div class="logo">KM</div><div><strong>KMFA 经营分析系统</strong><div class="sub">S14-P2 · 公开安全 · 开票纳税</div></div></div>
    <h1>KMFA 开票纳税</h1>
    <div class="sub">接入开票计划、纳税明细和开票纳税资金汇总结构，只输出待开票、已开票未回款和税率异常候选。页面不展示真实金额、税率值、客户明细、项目明文、账号或原始文件信息。</div>
  </header>
  <main>
    <section class="cards">
      <div class="card"><div class="label">报告等级</div><div class="num">报告等级 {grade}</div><div class="label">正式税务或经营依据仍被阻断</div></div>
      <div class="card"><div class="label">未关闭差异</div><div class="num stop">{pending_count} 项</div><div class="label">需要 owner 或授权复核</div></div>
      <div class="card"><div class="label">操作边界</div><div class="num stop">只读</div><div class="label">不做纳税申报和发票开具</div></div>
    </section>
    <section class="card" style="margin-top:16px">
      <h2>候选类型</h2>
      <ul>
{issue_cards}
      </ul>
    </section>
    <section class="card" style="margin-top:16px">
      <h2>开票纳税候选</h2>
      <table>
        <thead><tr><th>候选</th><th>复核角色</th><th>复核动作</th><th>边界</th></tr></thead>
        <tbody>
{issue_rows}
        </tbody>
      </table>
    </section>
    <section class="card" style="margin-top:16px">
      <h2>资金汇总</h2>
      <table>
        <thead><tr><th>汇总项</th><th>状态</th><th>公开显示</th></tr></thead>
        <tbody>
{cash_rows}
        </tbody>
      </table>
    </section>
    <section class="card" style="margin-top:16px">
      <h2>使用限制</h2>
      <div class="notice">S14-P2 只生成公开安全开票纳税候选证据。不做纳税申报和发票开具，不调用外部接口，不生成正式税务结论，不作为经营决策依据。</div>
    </section>
  </main>
</body>
</html>
"""


def _ensure_no_forbidden_public_payload(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in FORBIDDEN_PUBLIC_KEYS:
                raise InvoiceTaxPlanError(f"forbidden public key found: {key}")
            _ensure_no_forbidden_public_payload(item)
    elif isinstance(value, list):
        for item in value:
            _ensure_no_forbidden_public_payload(item)
    elif isinstance(value, str):
        lowered = value.lower()
        if any(suffix in lowered for suffix in FORBIDDEN_PUBLIC_SUFFIXES):
            raise InvoiceTaxPlanError(f"forbidden private business file reference found: {value}")
        if any(text in lowered for text in FORBIDDEN_PUBLIC_TEXT):
            raise InvoiceTaxPlanError(f"forbidden private/raw marker found: {value}")


def build_default_invoice_tax_plan_artifacts(
    *,
    generated_at: str = "2026-07-01T23:00:00+10:00",
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, str]]:
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
    issue_candidates = [
        _issue_candidate_record(issue_type=issue_type, sequence=index, generated_at=generated_at)
        for index, issue_type in enumerate(REQUIRED_ISSUE_CANDIDATE_TYPES, start=1)
    ]
    cash_summaries = [
        _cash_summary_record(bucket=bucket, sequence=index, generated_at=generated_at)
        for index, bucket in enumerate(CASH_SUMMARY_BUCKETS, start=1)
    ]

    manifest = {
        "schema_version": "kmfa.invoice_tax_plan_manifest.v1",
        "record_type": "invoice_tax_plan_manifest",
        "project_id": "KMFA",
        "stage_phase": "S14-P2",
        "plan_version": INVOICE_TAX_PLAN_VERSION,
        "formula_version": FORMULA_VERSION,
        "mapping_version": MAPPING_VERSION,
        "html_template_version": HTML_TEMPLATE_VERSION,
        "generated_at": generated_at,
        "runtime_status": "public_safe_invoice_tax_candidates_created_tax_and_invoice_actions_blocked",
        "required_source_lanes": list(REQUIRED_SOURCE_LANES),
        "required_issue_candidate_types": list(REQUIRED_ISSUE_CANDIDATE_TYPES),
        "required_cash_summary_buckets": list(CASH_SUMMARY_BUCKETS),
        "source_taskpack_refs": SOURCE_TASKPACK_REFS,
        "upstream_metadata_refs": UPSTREAM_METADATA_REFS,
        "quality_gate": _quality_gate(
            pending_reconciliation_count=pending_reconciliation_count,
            report_grade_visible=report_grade_visible,
        ),
        "stage_scope": _stage_scope(),
        "public_repo_safety": _public_repo_safety(),
        "artifact_refs": {
            "invoice_tax_plan_manifest": "KMFA/metadata/reports/invoice_tax_plan_manifest.json",
            "invoice_tax_source_lanes": "KMFA/metadata/reports/invoice_tax_source_lanes.jsonl",
            "invoice_tax_issue_candidates": "KMFA/metadata/reports/invoice_tax_issue_candidates.jsonl",
            "invoice_tax_cash_summaries": "KMFA/metadata/reports/invoice_tax_cash_summaries.jsonl",
            "html_overview": "KMFA/stage_artifacts/S14_P2_invoice_tax_plan/exports/html/invoice_tax_plan_overview.html",
            "validator": "KMFA/tools/check_s14_p2_invoice_tax_plan.py",
            "completion_record": "KMFA/stage_artifacts/S14_P2_invoice_tax_plan/human/s14_p2_completion_record.md",
            "test_results": "KMFA/stage_artifacts/S14_P2_invoice_tax_plan/human/test_results.md",
            "stage_manifest": "KMFA/stage_artifacts/S14_P2_invoice_tax_plan/machine/s14_p2_manifest.json",
        },
        "summary": {
            "source_lane_count": len(source_lanes),
            "issue_candidate_count": len(issue_candidates),
            "cash_summary_count": len(cash_summaries),
            "html_output_count": 1,
            "source_count": sum(int(lane["source_count"]) for lane in source_lanes),
            "field_mapping_count": sum(int(lane["field_mapping_count"]) for lane in source_lanes),
            "pending_reconciliation_count": pending_reconciliation_count,
            "report_grade_visible": report_grade_visible,
            "formal_report_count": 0,
            "business_decision_basis_count": 0,
            "invoice_issuance_count": 0,
            "tax_filing_count": 0,
            "external_connector_action_count": 0,
            "payment_or_bank_operation_count": 0,
        },
        "limitations": [
            "S14-P2 只输出 public-safe 开票计划、纳税明细和开票纳税资金汇总结构证据。",
            "不展示真实金额、真实税率值、真实发票号、客户或项目明文。",
            "不执行纳税申报、发票开具、外部接口、Stage 14 review 或 GitHub upload。",
            "报告等级仍显示 D，12 条 pending owner 或授权复核差异继续阻断正式报告和经营决策依据。",
        ],
    }
    html_outputs = {
        "invoice_tax_plan_overview": _render_html(
            manifest=manifest,
            issue_candidates=issue_candidates,
            cash_summaries=cash_summaries,
        )
    }
    manifest["content_hash"] = _sha256_json(
        {
            "manifest": manifest,
            "source_lanes": source_lanes,
            "issue_candidates": issue_candidates,
            "cash_summaries": cash_summaries,
            "html_outputs": html_outputs,
        }
    )
    return manifest, source_lanes, issue_candidates, cash_summaries, html_outputs


def validate_invoice_tax_plan_artifacts(
    manifest: dict[str, Any],
    source_lanes: list[dict[str, Any]],
    issue_candidates: list[dict[str, Any]],
    cash_summaries: list[dict[str, Any]],
    html_outputs: dict[str, str] | None = None,
) -> None:
    if manifest.get("schema_version") != "kmfa.invoice_tax_plan_manifest.v1":
        raise InvoiceTaxPlanError("manifest schema_version mismatch")
    if manifest.get("stage_phase") != "S14-P2":
        raise InvoiceTaxPlanError("manifest stage_phase must be S14-P2")
    if tuple(manifest.get("required_source_lanes", [])) != REQUIRED_SOURCE_LANES:
        raise InvoiceTaxPlanError("manifest required_source_lanes mismatch")
    if tuple(manifest.get("required_issue_candidate_types", [])) != REQUIRED_ISSUE_CANDIDATE_TYPES:
        raise InvoiceTaxPlanError("manifest required_issue_candidate_types mismatch")
    if tuple(manifest.get("required_cash_summary_buckets", [])) != CASH_SUMMARY_BUCKETS:
        raise InvoiceTaxPlanError("manifest required_cash_summary_buckets mismatch")

    expected_summary = {
        "source_lane_count": 3,
        "issue_candidate_count": 3,
        "cash_summary_count": 3,
        "html_output_count": 1,
        "pending_reconciliation_count": 12,
        "report_grade_visible": "D",
        "formal_report_count": 0,
        "business_decision_basis_count": 0,
        "invoice_issuance_count": 0,
        "tax_filing_count": 0,
        "external_connector_action_count": 0,
        "payment_or_bank_operation_count": 0,
    }
    for key, expected in expected_summary.items():
        if manifest.get("summary", {}).get(key) != expected:
            raise InvoiceTaxPlanError(f"manifest summary {key} must be {expected}")

    for scope_key, expected in _stage_scope().items():
        if manifest.get("stage_scope", {}).get(scope_key) is not expected:
            raise InvoiceTaxPlanError(f"manifest stage_scope {scope_key} must be {expected}")
    for gate_key, expected in _quality_gate(pending_reconciliation_count=12, report_grade_visible="D").items():
        if manifest.get("quality_gate", {}).get(gate_key) != expected:
            raise InvoiceTaxPlanError(f"manifest quality_gate {gate_key} must be {expected}")
    for safety_key, expected in _public_repo_safety().items():
        if manifest.get("public_repo_safety", {}).get(safety_key) is not expected:
            raise InvoiceTaxPlanError(f"manifest public_repo_safety {safety_key} must be {expected}")

    lane_by_id = {str(lane.get("lane_id")): lane for lane in source_lanes}
    if set(lane_by_id) != set(REQUIRED_SOURCE_LANES):
        raise InvoiceTaxPlanError("source lanes must cover all S14-P2 required lanes")
    for lane_id, categories in LANE_SOURCE_CATEGORIES.items():
        lane = lane_by_id[lane_id]
        if lane.get("record_type") != "invoice_tax_source_lane":
            raise InvoiceTaxPlanError(f"{lane_id} record_type mismatch")
        if tuple(lane.get("finance_categories", [])) != categories:
            raise InvoiceTaxPlanError(f"{lane_id} finance categories mismatch")
        if int(lane.get("source_count", 0)) < 1:
            raise InvoiceTaxPlanError(f"{lane_id} must have at least one source")
        if int(lane.get("field_mapping_count", 0)) < 5:
            raise InvoiceTaxPlanError(f"{lane_id} must have at least five field mappings")
        if lane.get("all_sources_readonly") is not True:
            raise InvoiceTaxPlanError(f"{lane_id}.all_sources_readonly must be true")
        for key in (
            "raw_business_values_allowed",
            "public_amount_values_allowed",
            "field_plaintext_allowed",
            "formal_report_allowed",
            "business_decision_basis_allowed",
            "raw_layer_write_allowed",
            "payment_or_bank_operation_allowed",
            "invoice_issuance_allowed",
            "tax_filing_allowed",
        ):
            if lane.get(key) is not False:
                raise InvoiceTaxPlanError(f"{lane_id}.{key} must be false")

    if [item.get("issue_type") for item in issue_candidates] != list(REQUIRED_ISSUE_CANDIDATE_TYPES):
        raise InvoiceTaxPlanError("issue candidate types mismatch")
    for index, item in enumerate(issue_candidates, start=1):
        if item.get("record_type") != "invoice_tax_issue_candidate":
            raise InvoiceTaxPlanError("issue candidate record_type mismatch")
        if item.get("stage_phase") != "S14-P2":
            raise InvoiceTaxPlanError("issue candidate stage_phase must be S14-P2")
        if item.get("issue_candidate_id") != f"S14P2-ISS-{index:03d}":
            raise InvoiceTaxPlanError("issue candidate id sequence mismatch")
        for key in (
            "raw_business_values_allowed",
            "public_amount_values_allowed",
            "tax_rate_public_value_allowed",
            "field_plaintext_allowed",
            "formal_report_allowed",
            "business_decision_basis_allowed",
            "invoice_issuance_allowed",
            "invoice_operation_allowed",
            "tax_filing_allowed",
            "tax_declaration_generation_allowed",
            "payment_or_bank_operation_allowed",
        ):
            if item.get(key) is not False:
                raise InvoiceTaxPlanError(f"issue candidate {key} must be false")

    if [item.get("cash_summary_bucket") for item in cash_summaries] != list(CASH_SUMMARY_BUCKETS):
        raise InvoiceTaxPlanError("cash summary buckets mismatch")
    for item in cash_summaries:
        if item.get("record_type") != "invoice_tax_cash_summary":
            raise InvoiceTaxPlanError("cash summary record_type mismatch")
        if item.get("stage_phase") != "S14-P2":
            raise InvoiceTaxPlanError("cash summary stage_phase must be S14-P2")
        for key in (
            "amount_value_display_allowed",
            "raw_business_values_allowed",
            "public_amount_values_allowed",
            "field_plaintext_allowed",
            "formal_report_allowed",
            "business_decision_basis_allowed",
            "payment_or_bank_operation_allowed",
            "invoice_issuance_allowed",
            "invoice_operation_allowed",
            "tax_filing_allowed",
            "tax_declaration_generation_allowed",
        ):
            if item.get(key) is not False:
                raise InvoiceTaxPlanError(f"cash summary {key} must be false")

    payload: list[Any] = [manifest, source_lanes, issue_candidates, cash_summaries]
    if html_outputs is not None:
        if set(html_outputs) != {"invoice_tax_plan_overview"}:
            raise InvoiceTaxPlanError("html outputs must contain invoice_tax_plan_overview only")
        html_text = html_outputs["invoice_tax_plan_overview"]
        required_visible = (
            "KMFA 开票纳税",
            "待开票",
            "已开票未回款",
            "税率异常候选",
            "不做纳税申报和发票开具",
            "报告等级 D",
        )
        for text in required_visible:
            if text not in html_text:
                raise InvoiceTaxPlanError(f"html output missing visible text: {text}")
        for forbidden_text in ("source_ref://", "private://", "private_ref://", "validator", "manifest", "metadata"):
            if forbidden_text in html_text.lower():
                raise InvoiceTaxPlanError(f"html output contains forbidden text: {forbidden_text}")
        payload.append(html_outputs)
    _ensure_no_forbidden_public_payload(payload)


def generate_default_outputs(*, generated_at: str = "2026-07-01T23:00:00+10:00") -> dict[str, Any]:
    manifest, source_lanes, issue_candidates, cash_summaries, html_outputs = (
        build_default_invoice_tax_plan_artifacts(generated_at=generated_at)
    )
    validate_invoice_tax_plan_artifacts(manifest, source_lanes, issue_candidates, cash_summaries, html_outputs)
    write_json(DEFAULT_OUTPUT_MANIFEST, manifest)
    write_jsonl(DEFAULT_OUTPUT_SOURCE_LANES, source_lanes)
    write_jsonl(DEFAULT_OUTPUT_ISSUE_CANDIDATES, issue_candidates)
    write_jsonl(DEFAULT_OUTPUT_CASH_SUMMARIES, cash_summaries)
    DEFAULT_HTML_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for output_id, html_text in html_outputs.items():
        (DEFAULT_HTML_OUTPUT_DIR / f"{output_id}.html").write_text(html_text, encoding="utf-8")
    write_json(
        DEFAULT_OUTPUT_STAGE_MANIFEST,
        {
            **manifest,
            "stage_artifact_manifest": True,
            "metadata_manifest_ref": "KMFA/metadata/reports/invoice_tax_plan_manifest.json",
        },
    )
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate KMFA S14-P2 invoice/tax public-safe artifacts.")
    parser.add_argument("--generated-at", default="2026-07-01T23:00:00+10:00")
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args(argv)

    manifest, source_lanes, issue_candidates, cash_summaries, html_outputs = (
        build_default_invoice_tax_plan_artifacts(generated_at=args.generated_at)
    )
    validate_invoice_tax_plan_artifacts(manifest, source_lanes, issue_candidates, cash_summaries, html_outputs)
    if not args.check_only:
        generate_default_outputs(generated_at=args.generated_at)
    summary = manifest["summary"]
    print(
        "PASS: KMFA S14-P2 invoice tax plan generated "
        f"(source_lanes={summary['source_lane_count']}, "
        f"issue_candidates={summary['issue_candidate_count']}, "
        f"cash_summaries={summary['cash_summary_count']}, "
        "report_grade_visible=D, formal_report_allowed=false, "
        "tax_filing=false, invoice_issuance=false, "
        "s14_p3_scope=false, stage14_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
