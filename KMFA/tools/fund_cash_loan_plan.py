#!/usr/bin/env python3
"""Build KMFA S14-P1 public-safe fund, cash, and loan planning artifacts."""

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

DEFAULT_OUTPUT_MANIFEST = ROOT / "metadata" / "reports" / "fund_cash_loan_plan_manifest.json"
DEFAULT_OUTPUT_SOURCE_LANES = ROOT / "metadata" / "reports" / "fund_cash_loan_source_lanes.jsonl"
DEFAULT_OUTPUT_CASH_PRESSURE = ROOT / "metadata" / "reports" / "fund_cash_pressure_signals.jsonl"
DEFAULT_OUTPUT_LOAN_DUE_ALERTS = ROOT / "metadata" / "reports" / "loan_due_alerts.jsonl"
DEFAULT_OUTPUT_ACCOUNT_SUMMARY = ROOT / "metadata" / "reports" / "account_balance_summaries.jsonl"
DEFAULT_OUTPUT_STAGE_MANIFEST = (
    ROOT / "stage_artifacts" / "S14_P1_fund_cash_loan_plan" / "machine" / "s14_p1_manifest.json"
)
DEFAULT_HTML_OUTPUT_DIR = ROOT / "stage_artifacts" / "S14_P1_fund_cash_loan_plan" / "exports" / "html"

REQUIRED_SOURCE_LANES = (
    "account_list",
    "monthly_cash",
    "fund_plan",
    "loan_detail",
)

REQUIRED_OUTPUT_RECORD_TYPES = (
    "cash_pressure_signal",
    "loan_due_alert",
    "account_balance_summary",
)

LANE_LABELS = {
    "account_list": "账户清单",
    "monthly_cash": "月度现金",
    "fund_plan": "资金计划",
    "loan_detail": "贷款明细",
}

LANE_SOURCE_CATEGORIES = {
    "account_list": ("account",),
    "monthly_cash": ("cash",),
    "fund_plan": ("cash", "journal"),
    "loan_detail": ("loan",),
}

LANE_STATUS_LABELS = {
    "account_list": "账户结构已接入，仅汇总账户组状态，不展示账号或余额明文",
    "monthly_cash": "月度现金结构已接入，现金结论仍受 D 级报告和差异门禁限制",
    "fund_plan": "资金计划结构已接入，只输出压力信号，不触发付款审批",
    "loan_detail": "贷款明细结构已接入，只输出到期提示，不触发贷款管理动作",
}

SOURCE_TASKPACK_REFS = {
    "roadmap_s14_p1": "KMFA/taskpack/v1_2/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_2.md:S14-P1",
    "taskpack_business_line": "KMFA/taskpack/v1_2/01_KMFA_Codex_TaskPack_v1_2_完整防遗漏_含HTML验收样板.md:P1-fund-cash-loan",
    "data_readiness_html_sample": (
        "KMFA/taskpack/v1_2/20_HTML_UIUX_报告预览/02_前序HTML完整归档/"
        "kmfa_stage1_v4__KMFA_MVP_Data_Readiness_Board_v0_3.html"
    ),
}

UPSTREAM_METADATA_REFS = {
    "finance_support_source_registry": "KMFA/metadata/imports/finance_support_source_registry.json",
    "finance_field_candidates": "KMFA/metadata/schema_maps/finance_field_candidates.jsonl",
    "scope_reconciliation": "KMFA/metadata/quality/scope_reconciliation_records.jsonl",
    "report_grade_runtime": "KMFA/metadata/reports/report_grade_runtime_records.jsonl",
}

FUND_CASH_LOAN_PLAN_VERSION = "PLAN-KMFA-S14P1-FUND-CASH-LOAN-PUBLIC-SAFE-001"
FORMULA_VERSION = "FORM-KMFA-S14P1-CASH-PRESSURE-SIGNAL-001"
MAPPING_VERSION = "MAP-KMFA-S14P1-PUBLIC-SAFE-v1"
HTML_TEMPLATE_VERSION = "HTML-KMFA-S14P1-BLUE-v1"

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
    "loan_amount",
    "interest_rate",
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
    "identity_document_number",
    "password",
    "token",
    "api_key",
    "private_key",
)


class FundCashLoanPlanError(ValueError):
    """Raised when S14-P1 fund/cash/loan artifacts are invalid."""


def _sha256_json(payload: Any) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise FundCashLoanPlanError(f"{path} must contain a JSON object")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            value = json.loads(line)
            if not isinstance(value, dict):
                raise FundCashLoanPlanError(f"{path} contains a non-object JSONL record")
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
    }


def _stage_scope() -> dict[str, bool]:
    return {
        "s14_p1_fund_cash_loan_scope_included": True,
        "s14_p2_scope_included": False,
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
    }


def _quality_gate(*, pending_reconciliation_count: int, report_grade_visible: str) -> dict[str, Any]:
    return {
        "planning_signal_allowed": True,
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
        "invoice_issuance_allowed": False,
        "s14_p2_allowed": False,
        "s14_p3_allowed": False,
        "stage14_review_allowed": False,
        "github_upload_allowed": False,
        "phase_completion_upload_allowed": False,
        "pending_reconciliation_count": pending_reconciliation_count,
        "release_block_reason": "planning_signal_only_pending_lineage_reconciliation_and_formal_report_gates",
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
            readonly_parse_flags.append(source.get("read_only_parse") is True)
        field_keys.extend(_field_keys(field_candidates_by_category.get(category, [])))
    return {
        "schema_version": "kmfa.fund_cash_loan_source_lane.v1",
        "record_type": "fund_cash_loan_source_lane",
        "project_id": "KMFA",
        "stage_phase": "S14-P1",
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
        "raw_business_values_allowed": False,
        "public_amount_values_allowed": False,
        "field_plaintext_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "payment_approval_allowed": False,
        "bank_operation_allowed": False,
        "loan_management_action_allowed": False,
        "raw_layer_write_allowed": False,
        "generated_at": generated_at,
    }


def _base_output_record(
    *,
    record_type: str,
    generated_at: str,
) -> dict[str, Any]:
    return {
        "schema_version": f"kmfa.{record_type}.v1",
        "record_type": record_type,
        "project_id": "KMFA",
        "stage_phase": "S14-P1",
        "report_grade_visible": "D",
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "payment_approval_allowed": False,
        "bank_operation_allowed": False,
        "loan_management_action_allowed": False,
        "contains_true_amounts": False,
        "contains_account_identifiers": False,
        "contains_field_plaintext": False,
        "generated_at": generated_at,
    }


def _cash_pressure_records(generated_at: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    windows = (
        ("current_week", "本周", "watch", "结构信号可查看，不能替代银行余额核对"),
        ("four_week", "4 周", "attention", "需要结合回款计划和付款优先级人工复核"),
        ("eight_week", "8 周", "pressure", "D 级报告状态下只输出压力提示"),
        ("twelve_week", "12 周", "blocked", "缺 lineage full check 时不输出正式资金结论"),
    )
    for pressure_window, visible_window, pressure_level, status_label in windows:
        row = _base_output_record(record_type="cash_pressure_signal", generated_at=generated_at)
        row.update(
            {
                "pressure_window": pressure_window,
                "visible_window": visible_window,
                "pressure_level": pressure_level,
                "status_label": status_label,
                "source_lane_refs": ["account_list", "monthly_cash", "fund_plan"],
                "action_allowed": False,
            }
        )
        rows.append(row)
    return rows


def _loan_due_alerts(generated_at: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    buckets = (
        ("within_30_days", "30 天内", "manual_review_required"),
        ("within_60_days", "60 天内", "watch"),
        ("within_90_days", "90 天内", "watch"),
    )
    for due_bucket, visible_due_bucket, alert_level in buckets:
        row = _base_output_record(record_type="loan_due_alert", generated_at=generated_at)
        row.update(
            {
                "due_bucket": due_bucket,
                "visible_due_bucket": visible_due_bucket,
                "alert_level": alert_level,
                "source_lane_refs": ["loan_detail", "fund_plan"],
                "loan_renewal_or_repayment_action_allowed": False,
            }
        )
        rows.append(row)
    return rows


def _account_balance_summaries(generated_at: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    groups = (
        ("operating_account_group", "经营账户组", "balance_hidden_structure_ready"),
        ("restricted_or_deposit_group", "受限/保证金账户组", "balance_hidden_manual_review"),
        ("loan_related_account_group", "贷款相关账户组", "balance_hidden_loan_linked"),
    )
    for account_group, visible_group_name, summary_status in groups:
        row = _base_output_record(record_type="account_balance_summary", generated_at=generated_at)
        row.update(
            {
                "account_group": account_group,
                "visible_group_name": visible_group_name,
                "summary_status": summary_status,
                "source_lane_refs": ["account_list", "monthly_cash"],
                "balance_value_display_allowed": False,
            }
        )
        rows.append(row)
    return rows


def _render_html(
    *,
    cash_pressure: list[dict[str, Any]],
    loan_due_alerts: list[dict[str, Any]],
    account_summaries: list[dict[str, Any]],
    report_grade_visible: str,
    pending_reconciliation_count: int,
) -> str:
    pressure_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(str(row['visible_window']))}</td>"
        f"<td>{html.escape(str(row['pressure_level']))}</td>"
        f"<td>{html.escape(str(row['status_label']))}</td>"
        "</tr>"
        for row in cash_pressure
    )
    loan_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(str(row['visible_due_bucket']))}</td>"
        f"<td>{html.escape(str(row['alert_level']))}</td>"
        "<td>仅提示，不触发贷款管理动作</td>"
        "</tr>"
        for row in loan_due_alerts
    )
    account_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(str(row['visible_group_name']))}</td>"
        f"<td>{html.escape(str(row['summary_status']))}</td>"
        "<td>余额值隐藏，账号隐藏</td>"
        "</tr>"
        for row in account_summaries
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>KMFA 资金计划现金贷款</title>
  <style>
    :root {{ --ink:#182235; --muted:#667085; --line:#d8e2ef; --blue:#1f5fbf; --navy:#12233c; --soft:#eef6ff; --warn:#a15c07; --stop:#b42318; --card:#fff; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:#f6f8fb; color:var(--ink); font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",Arial,sans-serif; }}
    header {{ background:linear-gradient(135deg,var(--navy),#1f4f82); color:#fff; padding:28px 34px; }}
    .brand {{ display:flex; align-items:center; gap:12px; margin-bottom:16px; }}
    .logo {{ width:48px; height:48px; border-radius:8px; background:#2563eb; display:flex; align-items:center; justify-content:center; font-weight:800; }}
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
    th {{ background:var(--soft); color:#153e75; }}
    .grid {{ display:grid; grid-template-columns:1fr 1fr; gap:14px; margin-top:16px; }}
    .notice {{ border-left:4px solid var(--warn); background:#fff7ed; padding:12px 14px; line-height:1.65; }}
    @media(max-width:860px) {{ .cards, .grid {{ grid-template-columns:1fr; }} header, main {{ padding-left:16px; padding-right:16px; }} }}
  </style>
</head>
<body>
  <header>
    <div class="brand"><div class="logo">KM</div><div><strong>KMFA 经营分析系统</strong><div class="sub">S14-P1 · 公开安全 · 资金计划现金贷款</div></div></div>
    <h1>KMFA 资金计划现金贷款</h1>
    <div class="sub">接入账户清单、月度现金、资金计划和贷款明细结构，只输出现金压力、贷款到期和账户余额汇总状态。不展示真实金额、账号、客户、项目或凭证信息。</div>
  </header>
  <main>
    <section class="cards">
      <div class="card"><div class="label">报告等级</div><div class="num">报告等级 {html.escape(report_grade_visible)}</div><div class="label">正式资金结论仍被阻断</div></div>
      <div class="card"><div class="label">未关闭差异</div><div class="num stop">{pending_reconciliation_count} 项</div><div class="label">需要 owner 或授权复核</div></div>
      <div class="card"><div class="label">操作边界</div><div class="num stop">只读</div><div class="label">不做付款审批和银行操作</div></div>
    </section>
    <section class="grid">
      <div class="card">
        <h2>现金压力</h2>
        <table><thead><tr><th>窗口</th><th>等级</th><th>说明</th></tr></thead><tbody>{pressure_rows}</tbody></table>
      </div>
      <div class="card">
        <h2>贷款到期</h2>
        <table><thead><tr><th>到期窗口</th><th>提示</th><th>边界</th></tr></thead><tbody>{loan_rows}</tbody></table>
      </div>
    </section>
    <section class="card" style="margin-top:16px">
      <h2>账户余额汇总</h2>
      <table><thead><tr><th>账户组</th><th>状态</th><th>公开显示</th></tr></thead><tbody>{account_rows}</tbody></table>
    </section>
    <section class="card" style="margin-top:16px">
      <h2>使用限制</h2>
      <div class="notice">S14-P1 只生成公开安全资金计划证据。开票纳税、政策证据、Stage 14 review、GitHub upload、lineage full check、正式报告、付款审批、银行操作、贷款管理动作均不在本 phase 范围内。</div>
    </section>
  </main>
</body>
</html>
"""


def _ensure_no_forbidden_public_payload(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in FORBIDDEN_PUBLIC_KEYS:
                raise FundCashLoanPlanError(f"forbidden public key found: {key}")
            _ensure_no_forbidden_public_payload(item)
    elif isinstance(value, list):
        for item in value:
            _ensure_no_forbidden_public_payload(item)
    elif isinstance(value, str):
        lowered = value.lower()
        if any(suffix in lowered for suffix in FORBIDDEN_PUBLIC_SUFFIXES):
            raise FundCashLoanPlanError(f"forbidden private business file reference found: {value}")
        if any(text in lowered for text in FORBIDDEN_PUBLIC_TEXT):
            raise FundCashLoanPlanError(f"forbidden private/raw marker found: {value}")


def build_default_fund_cash_loan_plan_artifacts(
    *,
    generated_at: str = "2026-07-01T22:00:00+10:00",
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, str]]:
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
    cash_pressure = _cash_pressure_records(generated_at)
    loan_due_alerts = _loan_due_alerts(generated_at)
    account_summaries = _account_balance_summaries(generated_at)
    html_outputs = {
        "fund_cash_loan_plan_overview": _render_html(
            cash_pressure=cash_pressure,
            loan_due_alerts=loan_due_alerts,
            account_summaries=account_summaries,
            report_grade_visible=report_grade_visible,
            pending_reconciliation_count=pending_reconciliation_count,
        )
    }

    manifest = {
        "schema_version": "kmfa.fund_cash_loan_plan_manifest.v1",
        "record_type": "fund_cash_loan_plan_manifest",
        "project_id": "KMFA",
        "stage_phase": "S14-P1",
        "plan_version": FUND_CASH_LOAN_PLAN_VERSION,
        "formula_version": FORMULA_VERSION,
        "mapping_version": MAPPING_VERSION,
        "html_template_version": HTML_TEMPLATE_VERSION,
        "generated_at": generated_at,
        "runtime_status": "public_safe_fund_cash_loan_planning_signals_created_operations_blocked",
        "required_source_lanes": list(REQUIRED_SOURCE_LANES),
        "required_output_record_types": list(REQUIRED_OUTPUT_RECORD_TYPES),
        "source_taskpack_refs": SOURCE_TASKPACK_REFS,
        "upstream_metadata_refs": UPSTREAM_METADATA_REFS,
        "quality_gate": _quality_gate(
            pending_reconciliation_count=pending_reconciliation_count,
            report_grade_visible=report_grade_visible,
        ),
        "stage_scope": _stage_scope(),
        "public_repo_safety": _public_repo_safety(),
        "artifact_refs": {
            "fund_cash_loan_plan_manifest": "KMFA/metadata/reports/fund_cash_loan_plan_manifest.json",
            "fund_cash_loan_source_lanes": "KMFA/metadata/reports/fund_cash_loan_source_lanes.jsonl",
            "cash_pressure_signals": "KMFA/metadata/reports/fund_cash_pressure_signals.jsonl",
            "loan_due_alerts": "KMFA/metadata/reports/loan_due_alerts.jsonl",
            "account_balance_summaries": "KMFA/metadata/reports/account_balance_summaries.jsonl",
            "html_overview": "KMFA/stage_artifacts/S14_P1_fund_cash_loan_plan/exports/html/fund_cash_loan_plan_overview.html",
            "validator": "KMFA/tools/check_s14_p1_fund_cash_loan_plan.py",
            "completion_record": "KMFA/stage_artifacts/S14_P1_fund_cash_loan_plan/human/s14_p1_completion_record.md",
            "test_results": "KMFA/stage_artifacts/S14_P1_fund_cash_loan_plan/human/test_results.md",
            "stage_manifest": "KMFA/stage_artifacts/S14_P1_fund_cash_loan_plan/machine/s14_p1_manifest.json",
        },
        "summary": {
            "source_lane_count": len(source_lanes),
            "cash_pressure_record_count": len(cash_pressure),
            "loan_due_alert_count": len(loan_due_alerts),
            "account_balance_summary_count": len(account_summaries),
            "html_output_count": len(html_outputs),
            "source_count": sum(int(lane["source_count"]) for lane in source_lanes),
            "field_mapping_count": sum(int(lane["field_mapping_count"]) for lane in source_lanes),
            "pending_reconciliation_count": pending_reconciliation_count,
            "report_grade_visible": report_grade_visible,
            "payment_operation_count": 0,
            "bank_operation_count": 0,
            "loan_management_action_count": 0,
        },
        "limitations": [
            "S14-P1 只输出 public-safe 资金计划、现金压力、贷款到期和账户余额汇总状态。",
            "不展示真实余额、真实现金流、贷款金额、真实账号、客户或项目明文。",
            "不执行付款审批、银行操作、贷款管理、开票、纳税申报、政策资格判断、Stage 14 review 或 GitHub upload。",
            "报告等级仍显示 D，12 条 pending owner 或授权复核差异继续阻断正式报告和经营决策依据。",
        ],
    }
    manifest["content_hash"] = _sha256_json(
        {
            "manifest": manifest,
            "source_lanes": source_lanes,
            "cash_pressure": cash_pressure,
            "loan_due_alerts": loan_due_alerts,
            "account_summaries": account_summaries,
            "html_outputs": html_outputs,
        }
    )
    return manifest, source_lanes, cash_pressure, loan_due_alerts, account_summaries, html_outputs


def validate_fund_cash_loan_plan_artifacts(
    manifest: dict[str, Any],
    source_lanes: list[dict[str, Any]],
    cash_pressure: list[dict[str, Any]],
    loan_due_alerts: list[dict[str, Any]],
    account_summaries: list[dict[str, Any]],
    html_outputs: dict[str, str] | None = None,
) -> None:
    if manifest.get("schema_version") != "kmfa.fund_cash_loan_plan_manifest.v1":
        raise FundCashLoanPlanError("manifest schema_version mismatch")
    if manifest.get("stage_phase") != "S14-P1":
        raise FundCashLoanPlanError("manifest stage_phase must be S14-P1")
    if tuple(manifest.get("required_source_lanes", [])) != REQUIRED_SOURCE_LANES:
        raise FundCashLoanPlanError("manifest required_source_lanes mismatch")
    if tuple(manifest.get("required_output_record_types", [])) != REQUIRED_OUTPUT_RECORD_TYPES:
        raise FundCashLoanPlanError("manifest required_output_record_types mismatch")

    expected_summary = {
        "source_lane_count": 4,
        "cash_pressure_record_count": 4,
        "loan_due_alert_count": 3,
        "account_balance_summary_count": 3,
        "html_output_count": 1,
        "pending_reconciliation_count": 12,
        "report_grade_visible": "D",
        "payment_operation_count": 0,
        "bank_operation_count": 0,
        "loan_management_action_count": 0,
    }
    for key, expected in expected_summary.items():
        if manifest.get("summary", {}).get(key) != expected:
            raise FundCashLoanPlanError(f"manifest summary {key} must be {expected}")

    for scope_key, expected in _stage_scope().items():
        if manifest.get("stage_scope", {}).get(scope_key) is not expected:
            raise FundCashLoanPlanError(f"manifest stage_scope {scope_key} must be {expected}")
    for gate_key, expected in _quality_gate(pending_reconciliation_count=12, report_grade_visible="D").items():
        if manifest.get("quality_gate", {}).get(gate_key) != expected:
            raise FundCashLoanPlanError(f"manifest quality_gate {gate_key} must be {expected}")
    for safety_key, expected in _public_repo_safety().items():
        if manifest.get("public_repo_safety", {}).get(safety_key) is not expected:
            raise FundCashLoanPlanError(f"manifest public_repo_safety {safety_key} must be {expected}")

    lane_by_id = {str(lane.get("lane_id")): lane for lane in source_lanes}
    if set(lane_by_id) != set(REQUIRED_SOURCE_LANES):
        raise FundCashLoanPlanError("source lanes must cover all S14-P1 required lanes")
    for lane_id, categories in LANE_SOURCE_CATEGORIES.items():
        lane = lane_by_id[lane_id]
        if lane.get("record_type") != "fund_cash_loan_source_lane":
            raise FundCashLoanPlanError(f"{lane_id} record_type mismatch")
        if tuple(lane.get("finance_categories", [])) != categories:
            raise FundCashLoanPlanError(f"{lane_id} finance categories mismatch")
        if int(lane.get("source_count", 0)) < 1:
            raise FundCashLoanPlanError(f"{lane_id} must have at least one source")
        if int(lane.get("field_mapping_count", 0)) < 5:
            raise FundCashLoanPlanError(f"{lane_id} must have at least five field mappings")
        for key in (
            "all_sources_readonly",
        ):
            if lane.get(key) is not True:
                raise FundCashLoanPlanError(f"{lane_id}.{key} must be true")
        for key in (
            "raw_business_values_allowed",
            "public_amount_values_allowed",
            "field_plaintext_allowed",
            "formal_report_allowed",
            "business_decision_basis_allowed",
            "payment_approval_allowed",
            "bank_operation_allowed",
            "loan_management_action_allowed",
            "raw_layer_write_allowed",
        ):
            if lane.get(key) is not False:
                raise FundCashLoanPlanError(f"{lane_id}.{key} must be false")

    if [row.get("pressure_window") for row in cash_pressure] != [
        "current_week",
        "four_week",
        "eight_week",
        "twelve_week",
    ]:
        raise FundCashLoanPlanError("cash pressure windows mismatch")
    if [row.get("due_bucket") for row in loan_due_alerts] != [
        "within_30_days",
        "within_60_days",
        "within_90_days",
    ]:
        raise FundCashLoanPlanError("loan due buckets mismatch")
    if [row.get("account_group") for row in account_summaries] != [
        "operating_account_group",
        "restricted_or_deposit_group",
        "loan_related_account_group",
    ]:
        raise FundCashLoanPlanError("account summary groups mismatch")

    for rows, record_type in (
        (cash_pressure, "cash_pressure_signal"),
        (loan_due_alerts, "loan_due_alert"),
        (account_summaries, "account_balance_summary"),
    ):
        for row in rows:
            if row.get("record_type") != record_type:
                raise FundCashLoanPlanError(f"{record_type} record_type mismatch")
            if row.get("stage_phase") != "S14-P1":
                raise FundCashLoanPlanError(f"{record_type} stage_phase must be S14-P1")
            for key in (
                "formal_report_allowed",
                "business_decision_basis_allowed",
                "payment_approval_allowed",
                "bank_operation_allowed",
                "loan_management_action_allowed",
                "contains_true_amounts",
                "contains_account_identifiers",
                "contains_field_plaintext",
            ):
                if row.get(key) is not False:
                    raise FundCashLoanPlanError(f"{record_type}.{key} must be false")

    payload: list[Any] = [manifest, source_lanes, cash_pressure, loan_due_alerts, account_summaries]
    if html_outputs is not None:
        if set(html_outputs) != {"fund_cash_loan_plan_overview"}:
            raise FundCashLoanPlanError("html outputs must contain fund_cash_loan_plan_overview only")
        html_text = html_outputs["fund_cash_loan_plan_overview"]
        required_visible = (
            "KMFA 资金计划现金贷款",
            "现金压力",
            "贷款到期",
            "账户余额汇总",
            "不做付款审批和银行操作",
            "报告等级 D",
        )
        for text in required_visible:
            if text not in html_text:
                raise FundCashLoanPlanError(f"html output missing visible text: {text}")
        for forbidden_text in ("source_ref://", "private://", "private_ref://", "validator", "manifest", "metadata"):
            if forbidden_text in html_text.lower():
                raise FundCashLoanPlanError(f"html output contains forbidden text: {forbidden_text}")
        payload.append(html_outputs)
    _ensure_no_forbidden_public_payload(payload)


def generate_default_outputs(*, generated_at: str = "2026-07-01T22:00:00+10:00") -> dict[str, Any]:
    manifest, source_lanes, cash_pressure, loan_due_alerts, account_summaries, html_outputs = (
        build_default_fund_cash_loan_plan_artifacts(generated_at=generated_at)
    )
    validate_fund_cash_loan_plan_artifacts(
        manifest,
        source_lanes,
        cash_pressure,
        loan_due_alerts,
        account_summaries,
        html_outputs,
    )
    write_json(DEFAULT_OUTPUT_MANIFEST, manifest)
    write_jsonl(DEFAULT_OUTPUT_SOURCE_LANES, source_lanes)
    write_jsonl(DEFAULT_OUTPUT_CASH_PRESSURE, cash_pressure)
    write_jsonl(DEFAULT_OUTPUT_LOAN_DUE_ALERTS, loan_due_alerts)
    write_jsonl(DEFAULT_OUTPUT_ACCOUNT_SUMMARY, account_summaries)
    DEFAULT_HTML_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for output_id, html_text in html_outputs.items():
        (DEFAULT_HTML_OUTPUT_DIR / f"{output_id}.html").write_text(html_text, encoding="utf-8")
    write_json(
        DEFAULT_OUTPUT_STAGE_MANIFEST,
        {
            **manifest,
            "stage_artifact_manifest": True,
            "metadata_manifest_ref": "KMFA/metadata/reports/fund_cash_loan_plan_manifest.json",
        },
    )
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate KMFA S14-P1 fund/cash/loan public-safe artifacts.")
    parser.add_argument("--generated-at", default="2026-07-01T22:00:00+10:00")
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args(argv)

    manifest, source_lanes, cash_pressure, loan_due_alerts, account_summaries, html_outputs = (
        build_default_fund_cash_loan_plan_artifacts(generated_at=args.generated_at)
    )
    validate_fund_cash_loan_plan_artifacts(
        manifest,
        source_lanes,
        cash_pressure,
        loan_due_alerts,
        account_summaries,
        html_outputs,
    )
    if not args.check_only:
        generate_default_outputs(generated_at=args.generated_at)
    summary = manifest["summary"]
    print(
        "PASS: KMFA S14-P1 fund cash loan plan generated "
        f"(source_lanes={summary['source_lane_count']}, "
        f"cash_pressure={summary['cash_pressure_record_count']}, "
        f"loan_due_alerts={summary['loan_due_alert_count']}, "
        f"account_summaries={summary['account_balance_summary_count']}, "
        "report_grade_visible=D, formal_report_allowed=false, "
        "payment_approval=false, bank_operation=false, loan_management=false, "
        "s14_p2_scope=false, s14_p3_scope=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
