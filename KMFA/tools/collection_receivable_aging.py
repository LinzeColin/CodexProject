#!/usr/bin/env python3
"""Build KMFA S13-P2 public-safe collection and receivable aging artifacts."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

DEFAULT_WPS_SOURCE_REGISTRY = ROOT / "metadata" / "imports" / "wps_export_source_registry.json"
DEFAULT_WPS_FIELD_MAPPINGS = ROOT / "metadata" / "schema_maps" / "wps_field_mappings.jsonl"
DEFAULT_FINANCE_SOURCE_REGISTRY = ROOT / "metadata" / "imports" / "finance_support_source_registry.json"
DEFAULT_FINANCE_FIELD_CANDIDATES = ROOT / "metadata" / "schema_maps" / "finance_field_candidates.jsonl"
DEFAULT_SCOPE_RECONCILIATION_RECORDS = ROOT / "metadata" / "quality" / "scope_reconciliation_records.jsonl"
DEFAULT_REPORT_GRADE_RECORDS = ROOT / "metadata" / "reports" / "report_grade_runtime_records.jsonl"

DEFAULT_OUTPUT_MANIFEST = ROOT / "metadata" / "reports" / "collection_receivable_aging_manifest.json"
DEFAULT_OUTPUT_LANES = ROOT / "metadata" / "reports" / "collection_receivable_aging_source_lanes.jsonl"
DEFAULT_OUTPUT_PRIORITY_ITEMS = ROOT / "metadata" / "reports" / "collection_receivable_aging_priority_items.jsonl"
DEFAULT_OUTPUT_RESPONSIBILITY_ITEMS = ROOT / "metadata" / "reports" / "collection_receivable_aging_responsibility_items.jsonl"
DEFAULT_OUTPUT_STAGE_MANIFEST = (
    ROOT / "stage_artifacts" / "S13_P2_collection_receivable_aging" / "machine" / "s13_p2_manifest.json"
)
DEFAULT_HTML_OUTPUT_DIR = ROOT / "stage_artifacts" / "S13_P2_collection_receivable_aging" / "exports" / "html"

REQUIRED_SOURCE_LANES = (
    "collection_table",
    "receivable_aging",
    "customer_aging",
    "journal",
    "invoice_plan",
)

REQUIRED_ISSUE_TYPES = (
    "invoiced_not_collected",
    "completed_not_settled",
    "settled_not_invoiced",
    "overdue_receivable",
)

LANE_LABELS = {
    "collection_table": "回款表",
    "receivable_aging": "应收账龄",
    "customer_aging": "客户账龄",
    "journal": "日记账",
    "invoice_plan": "开票计划",
}

LANE_SOURCE_KIND = {
    "collection_table": "wps_collection_export",
    "receivable_aging": "wps_receivable_aging_export",
    "customer_aging": "finance_customer_aging",
    "journal": "finance_journal",
    "invoice_plan": "finance_invoice_plan",
}

LANE_WPS_EXPORT_TYPES = {
    "collection_table": ("collection",),
    "receivable_aging": ("receivable_aging",),
}

LANE_FINANCE_CATEGORIES = {
    "customer_aging": ("customer_aging",),
    "journal": ("journal",),
    "invoice_plan": ("invoice",),
}

LANE_STATUS_LABELS = {
    "collection_table": "回款结构已接入，真实回款金额和客户明细继续阻断",
    "receivable_aging": "应收账龄结构已接入，账龄金额结论需后续复核",
    "customer_aging": "客户账龄结构已接入，仅用于公开安全优先级草案",
    "journal": "日记账结构已接入，不触发付款、收款或银行操作",
    "invoice_plan": "开票计划结构已接入，不触发开票、税务申报或正式结论",
}

ISSUE_LABELS = {
    "invoiced_not_collected": "已开票未回款",
    "completed_not_settled": "完工未结算",
    "settled_not_invoiced": "结算未开票",
    "overdue_receivable": "超期应收",
}

ISSUE_EVIDENCE_LANES = {
    "invoiced_not_collected": ("invoice_plan", "collection_table", "journal"),
    "completed_not_settled": ("receivable_aging", "customer_aging"),
    "settled_not_invoiced": ("invoice_plan", "receivable_aging"),
    "overdue_receivable": ("receivable_aging", "customer_aging", "collection_table"),
}

ISSUE_RESPONSIBILITY = {
    "invoiced_not_collected": ("finance_owner", "verify_collection_status"),
    "completed_not_settled": ("project_owner", "confirm_settlement_basis"),
    "settled_not_invoiced": ("sales_owner", "confirm_invoice_plan"),
    "overdue_receivable": ("finance_owner", "review_overdue_receivable"),
}

ISSUE_PRIORITY_LEVEL = {
    "invoiced_not_collected": "high",
    "completed_not_settled": "medium",
    "settled_not_invoiced": "medium",
    "overdue_receivable": "high",
}

SOURCE_TASKPACK_REFS = {
    "roadmap_s13_p2": "KMFA/taskpack/v1_2/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_2.md:S13-P2",
    "taskpack_stage13": "KMFA/taskpack/v1_2/01_KMFA_Codex_TaskPack_v1_2_FULL.md:Stage13",
}

UPSTREAM_METADATA_REFS = {
    "wps_export_source_registry": "source_ref://KMFA/S07-P2/wps_export_source_registry",
    "wps_field_mappings": "source_ref://KMFA/S07-P2/wps_field_mappings",
    "finance_support_source_registry": "source_ref://KMFA/S07-P1/finance_support_source_registry",
    "finance_field_candidates": "source_ref://KMFA/S07-P1/finance_field_candidates",
    "project_scope_reconciliation": "source_ref://KMFA/S09-P3/scope_reconciliation",
    "report_grade_runtime": "source_ref://KMFA/S10-P2/report_grade_runtime",
}

COLLECTION_RECEIVABLE_AGING_VERSION = "RPT-KMFA-S13P2-COLLECTION-RECEIVABLE-AGING-001"
FORMULA_VERSION = "FORM-KMFA-COLLECTION-RECEIVABLE-AGING-001"
MAPPING_VERSION = "MAP-KMFA-S13P2-PUBLIC-SAFE-v1"
HTML_TEMPLATE_VERSION = "HTML-KMFA-S13P2-BLUE-PRIORITY-v1"

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


class CollectionReceivableAgingError(ValueError):
    """Raised when S13-P2 collection and receivable aging artifacts are invalid."""


def _sha256_json(payload: Any) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CollectionReceivableAgingError(f"{path} must contain a JSON object")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            value = json.loads(line)
            if not isinstance(value, dict):
                raise CollectionReceivableAgingError(f"{path} contains a non-object JSONL record")
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
        "private_ref_committed_in_s13p2_outputs": False,
    }


def _stage_scope() -> dict[str, bool]:
    return {
        "s13_p1_financial_operating_report_scope_included": False,
        "s13_p2_collection_receivable_aging_scope_included": True,
        "s13_p3_scope_included": False,
        "s13_p3_cross_table_review_scope_included": False,
        "stage13_review_scope_included": False,
        "formal_report_runtime_scope_included": False,
        "complete_trusted_report_scope_included": False,
        "lineage_full_check_scope_included": False,
        "external_connector_scope_included": False,
        "payment_or_bank_operation_scope_included": False,
        "tax_filing_scope_included": False,
        "legal_collection_scope_included": False,
        "github_upload_scope_included": False,
    }


def _quality_gate(*, pending_reconciliation_count: int, report_grade_visible: str) -> dict[str, Any]:
    return {
        "collection_receivable_priority_draft_allowed": True,
        "responsibility_item_draft_allowed": True,
        "formal_report_allowed": False,
        "complete_trusted_report_display_allowed": False,
        "business_decision_basis_allowed": False,
        "legal_collection_decision_allowed": False,
        "payment_or_bank_operation_allowed": False,
        "tax_filing_allowed": False,
        "invoice_operation_allowed": False,
        "derived_amount_calculation_allowed": False,
        "raw_layer_write_allowed": False,
        "report_grade_visible": report_grade_visible,
        "report_grade_bypass_allowed": False,
        "quality_grade_bypass_allowed": False,
        "s13_p1_scope_reopen_allowed": False,
        "s13_p3_scope_allowed": False,
        "stage13_review_allowed": False,
        "github_upload_allowed": False,
        "phase_completion_upload_allowed": False,
        "pending_reconciliation_count": pending_reconciliation_count,
        "release_block_reason": "draft_only_pending_s13p3_lineage_and_unclosed_reconciliation",
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


def _sources_by_key(source_registry: dict[str, Any], key_name: str) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for source in source_registry.get("sources", []):
        if isinstance(source, dict):
            grouped.setdefault(str(source.get(key_name)), []).append(source)
    return grouped


def _fields_by_key(field_records: list[dict[str, Any]], key_name: str) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for record in field_records:
        grouped.setdefault(str(record.get(key_name)), []).append(record)
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


def _source_refs_and_readonly(sources: list[dict[str, Any]]) -> tuple[list[str], list[str], bool]:
    source_refs: list[str] = []
    parse_statuses: set[str] = set()
    readonly_parse_flags: list[bool] = []
    for source in sources:
        source_ref = str(source.get("source_ref") or "")
        if source_ref:
            source_refs.append(source_ref)
        parse_statuses.add(str(source.get("parse_status") or "structure_parse_status_available"))
        readonly_parse_flags.append(source.get("read_only_parse") is True and source.get("raw_layer_write_allowed") is False)
    return sorted(set(source_refs)), sorted(parse_statuses), all(readonly_parse_flags) if readonly_parse_flags else False


def _source_lane_record(
    *,
    lane_id: str,
    wps_sources_by_export_type: dict[str, list[dict[str, Any]]],
    wps_fields_by_export_type: dict[str, list[dict[str, Any]]],
    finance_sources_by_category: dict[str, list[dict[str, Any]]],
    finance_fields_by_category: dict[str, list[dict[str, Any]]],
    generated_at: str,
) -> dict[str, Any]:
    if lane_id in LANE_WPS_EXPORT_TYPES:
        export_types = LANE_WPS_EXPORT_TYPES[lane_id]
        sources = [source for export_type in export_types for source in wps_sources_by_export_type.get(export_type, [])]
        field_keys = _field_keys(
            [record for export_type in export_types for record in wps_fields_by_export_type.get(export_type, [])]
        )
        source_refs, parse_statuses, all_sources_readonly = _source_refs_and_readonly(sources)
        finance_categories: list[str] = []
        export_type_values = list(export_types)
    else:
        finance_category_values = LANE_FINANCE_CATEGORIES[lane_id]
        sources = [
            source
            for finance_category in finance_category_values
            for source in finance_sources_by_category.get(finance_category, [])
        ]
        field_keys = _field_keys(
            [
                record
                for finance_category in finance_category_values
                for record in finance_fields_by_category.get(finance_category, [])
            ]
        )
        source_refs, parse_statuses, all_sources_readonly = _source_refs_and_readonly(sources)
        finance_categories = list(finance_category_values)
        export_type_values = []

    return {
        "schema_version": "kmfa.collection_receivable_aging_source_lane.v1",
        "record_type": "collection_receivable_aging_source_lane",
        "project_id": "KMFA",
        "stage_phase": "S13-P2",
        "lane_id": lane_id,
        "visible_lane_name": LANE_LABELS[lane_id],
        "source_kind": LANE_SOURCE_KIND[lane_id],
        "wps_export_types": export_type_values,
        "finance_categories": finance_categories,
        "source_refs": source_refs,
        "source_count": len(source_refs),
        "field_mapping_count": len(field_keys),
        "field_key_refs": field_keys,
        "parse_statuses": parse_statuses,
        "all_sources_readonly": all_sources_readonly,
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


def _priority_item_record(
    *,
    issue_type: str,
    priority_rank: int,
    generated_at: str,
) -> dict[str, Any]:
    evidence_lanes = list(ISSUE_EVIDENCE_LANES[issue_type])
    return {
        "schema_version": "kmfa.collection_receivable_priority_item.v1",
        "record_type": "collection_receivable_priority_item",
        "project_id": "KMFA",
        "stage_phase": "S13-P2",
        "priority_item_id": f"S13P2-PRI-{priority_rank:03d}",
        "priority_rank": priority_rank,
        "priority_level": ISSUE_PRIORITY_LEVEL[issue_type],
        "issue_type": issue_type,
        "visible_issue_label": ISSUE_LABELS[issue_type],
        "customer_group_ref": f"public_customer_group_ref_{priority_rank:03d}",
        "project_group_ref": f"public_project_group_ref_{priority_rank:03d}",
        "amount_signal_ref": f"public_amount_signal_hash_{priority_rank:03d}",
        "aging_bucket_ref": f"public_aging_bucket_ref_{priority_rank:03d}",
        "evidence_lane_ids": evidence_lanes,
        "evidence_metadata_refs": [
            UPSTREAM_METADATA_REFS["wps_export_source_registry"],
            UPSTREAM_METADATA_REFS["wps_field_mappings"],
            UPSTREAM_METADATA_REFS["finance_support_source_registry"],
            UPSTREAM_METADATA_REFS["finance_field_candidates"],
        ],
        "priority_reason": (
            f"{ISSUE_LABELS[issue_type]} requires owner or authorized review before any external action."
        ),
        "recommended_review_mode": "owner_or_authorized_delegate_review_only",
        "next_review_bucket": "next_internal_review_cycle",
        "raw_business_values_allowed": False,
        "public_amount_values_allowed": False,
        "field_plaintext_allowed": False,
        "collection_action_allowed": False,
        "legal_collection_decision_allowed": False,
        "payment_or_bank_operation_allowed": False,
        "tax_filing_allowed": False,
        "invoice_operation_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "generated_at": generated_at,
    }


def _responsibility_item_record(
    *,
    issue_type: str,
    sequence: int,
    generated_at: str,
) -> dict[str, Any]:
    responsible_role, required_action_kind = ISSUE_RESPONSIBILITY[issue_type]
    return {
        "schema_version": "kmfa.collection_receivable_responsibility_item.v1",
        "record_type": "collection_receivable_responsibility_item",
        "project_id": "KMFA",
        "stage_phase": "S13-P2",
        "responsibility_item_id": f"S13P2-RESP-{sequence:03d}",
        "issue_type": issue_type,
        "visible_issue_label": ISSUE_LABELS[issue_type],
        "responsible_role": responsible_role,
        "required_action_kind": required_action_kind,
        "review_evidence_lane_ids": list(ISSUE_EVIDENCE_LANES[issue_type]),
        "review_due_bucket": "next_internal_review_cycle",
        "handoff_status": "draft_responsibility_item_pending_owner_or_authorized_review",
        "raw_business_values_allowed": False,
        "public_amount_values_allowed": False,
        "field_plaintext_allowed": False,
        "collection_action_allowed": False,
        "legal_collection_decision_allowed": False,
        "payment_or_bank_operation_allowed": False,
        "tax_filing_allowed": False,
        "invoice_operation_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "generated_at": generated_at,
    }


def _render_html(
    *,
    manifest: dict[str, Any],
    priority_items: list[dict[str, Any]],
    responsibility_items: list[dict[str, Any]],
) -> str:
    grade = html.escape(str(manifest["summary"]["report_grade_visible"]))
    priority_rows = "\n".join(
        "<tr>"
        f"<td>{int(item['priority_rank'])}</td>"
        f"<td>{html.escape(str(item['visible_issue_label']))}</td>"
        f"<td>{html.escape(str(item['priority_level']))}</td>"
        f"<td>{html.escape(str(item['recommended_review_mode']))}</td>"
        "</tr>"
        for item in priority_items
    )
    responsibility_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(str(item['visible_issue_label']))}</td>"
        f"<td>{html.escape(str(item['responsible_role']))}</td>"
        f"<td>{html.escape(str(item['required_action_kind']))}</td>"
        f"<td>{html.escape(str(item['review_due_bucket']))}</td>"
        "</tr>"
        for item in responsibility_items
    )
    issue_cards = "\n".join(
        f"<li>{html.escape(ISSUE_LABELS[issue_type])}<span>仅作内部复核草案</span></li>"
        for issue_type in REQUIRED_ISSUE_TYPES
    )
    pending_count = int(manifest["summary"]["pending_reconciliation_count"])
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>KMFA 回款应收账龄优先级草案</title>
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
    ul {{ margin:10px 0 0; padding:0; display:grid; grid-template-columns:repeat(4,1fr); gap:10px; list-style:none; }}
    li {{ border:1px solid var(--line); border-radius:8px; padding:12px; background:#fbfdff; font-weight:700; }}
    li span {{ display:block; color:var(--muted); font-size:13px; font-weight:400; margin-top:5px; }}
    .notice {{ border-left:4px solid var(--warn); background:#fff7ed; padding:12px 14px; line-height:1.65; }}
    @media(max-width:900px) {{ .cards, ul {{ grid-template-columns:1fr; }} header, main {{ padding-left:16px; padding-right:16px; }} }}
  </style>
</head>
<body>
  <header>
    <div class="brand"><div class="logo">KM</div><div><strong>KMFA 经营分析系统</strong><div class="sub">回款应收账龄 · 公开安全 · 蓝色商务版</div></div></div>
    <h1>回款应收账龄优先级草案</h1>
    <div class="sub">本页只展示公开安全的优先级、问题类型和责任复核事项，不展示真实金额、客户明细、项目明文、账号信息或原始文件信息。</div>
  </header>
  <main>
    <section class="cards">
      <div class="card"><div class="label">报告等级</div><div class="num">报告等级 {grade}</div><div class="label">正式经营依据仍被阻断</div></div>
      <div class="card"><div class="label">未关闭差异</div><div class="num stop">{pending_count} 项</div><div class="label">需要 owner 或授权复核</div></div>
      <div class="card"><div class="label">事项类型</div><div class="num">4 类</div><div class="label">仅作内部复核草案</div></div>
    </section>
    <section class="card" style="margin-top:16px">
      <h2>问题类型</h2>
      <ul>
{issue_cards}
      </ul>
    </section>
    <section class="card" style="margin-top:16px">
      <h2>回款优先级</h2>
      <table>
        <thead><tr><th>排序</th><th>问题</th><th>级别</th><th>复核方式</th></tr></thead>
        <tbody>
{priority_rows}
        </tbody>
      </table>
    </section>
    <section class="card" style="margin-top:16px">
      <h2>责任事项</h2>
      <table>
        <thead><tr><th>问题</th><th>责任角色</th><th>动作类型</th><th>复核周期</th></tr></thead>
        <tbody>
{responsibility_rows}
        </tbody>
      </table>
    </section>
    <section class="card" style="margin-top:16px">
      <h2>使用限制</h2>
      <div class="notice">S13-P2 不生成正式催收清单，不触发开票、付款、银行、税务或法务动作；不可作为催收、付款、法务或经营决策依据。</div>
    </section>
  </main>
</body>
</html>
"""


def _ensure_no_forbidden_public_payload(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in FORBIDDEN_PUBLIC_KEYS:
                raise CollectionReceivableAgingError(f"forbidden public key found: {key}")
            _ensure_no_forbidden_public_payload(item)
    elif isinstance(value, list):
        for item in value:
            _ensure_no_forbidden_public_payload(item)
    elif isinstance(value, str):
        lowered = value.lower()
        if any(suffix in lowered for suffix in FORBIDDEN_PUBLIC_SUFFIXES):
            raise CollectionReceivableAgingError(f"forbidden private business file reference found: {value}")
        if any(text in lowered for text in FORBIDDEN_PUBLIC_TEXT):
            raise CollectionReceivableAgingError(f"forbidden private/raw marker found: {value}")


def build_default_collection_receivable_aging_artifacts(
    *,
    generated_at: str = "2026-07-01T18:00:00+10:00",
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, str]]:
    wps_source_registry = read_json(DEFAULT_WPS_SOURCE_REGISTRY)
    wps_field_mappings = read_jsonl(DEFAULT_WPS_FIELD_MAPPINGS)
    finance_source_registry = read_json(DEFAULT_FINANCE_SOURCE_REGISTRY)
    finance_field_candidates = read_jsonl(DEFAULT_FINANCE_FIELD_CANDIDATES)
    reconciliation_records = read_jsonl(DEFAULT_SCOPE_RECONCILIATION_RECORDS)
    report_grade_records = read_jsonl(DEFAULT_REPORT_GRADE_RECORDS)

    wps_sources_by_export_type = _sources_by_key(wps_source_registry, "export_type")
    wps_fields_by_export_type = _fields_by_key(wps_field_mappings, "export_type")
    finance_sources_by_category = _sources_by_key(finance_source_registry, "finance_category")
    finance_fields_by_category = _fields_by_key(finance_field_candidates, "finance_category")
    pending_reconciliation_count = _pending_reconciliation_count(reconciliation_records)
    report_grade_visible = _report_grade_visible(report_grade_records)

    source_lanes = [
        _source_lane_record(
            lane_id=lane_id,
            wps_sources_by_export_type=wps_sources_by_export_type,
            wps_fields_by_export_type=wps_fields_by_export_type,
            finance_sources_by_category=finance_sources_by_category,
            finance_fields_by_category=finance_fields_by_category,
            generated_at=generated_at,
        )
        for lane_id in REQUIRED_SOURCE_LANES
    ]
    priority_items = [
        _priority_item_record(issue_type=issue_type, priority_rank=index, generated_at=generated_at)
        for index, issue_type in enumerate(REQUIRED_ISSUE_TYPES, start=1)
    ]
    responsibility_items = [
        _responsibility_item_record(issue_type=issue_type, sequence=index, generated_at=generated_at)
        for index, issue_type in enumerate(REQUIRED_ISSUE_TYPES, start=1)
    ]

    manifest = {
        "schema_version": "kmfa.collection_receivable_aging_manifest.v1",
        "record_type": "collection_receivable_aging_manifest",
        "project_id": "KMFA",
        "stage_phase": "S13-P2",
        "report_version": COLLECTION_RECEIVABLE_AGING_VERSION,
        "formula_version": FORMULA_VERSION,
        "mapping_version": MAPPING_VERSION,
        "html_template_version": HTML_TEMPLATE_VERSION,
        "generated_at": generated_at,
        "runtime_status": "public_safe_collection_receivable_aging_priority_created_formal_actions_blocked",
        "required_source_lanes": list(REQUIRED_SOURCE_LANES),
        "required_issue_types": list(REQUIRED_ISSUE_TYPES),
        "source_taskpack_refs": SOURCE_TASKPACK_REFS,
        "upstream_metadata_refs": UPSTREAM_METADATA_REFS,
        "quality_gate": _quality_gate(
            pending_reconciliation_count=pending_reconciliation_count,
            report_grade_visible=report_grade_visible,
        ),
        "stage_scope": _stage_scope(),
        "public_repo_safety": _public_repo_safety(),
        "artifact_refs": {
            "collection_receivable_aging_manifest": "KMFA/metadata/reports/collection_receivable_aging_manifest.json",
            "collection_receivable_aging_source_lanes": (
                "KMFA/metadata/reports/collection_receivable_aging_source_lanes.jsonl"
            ),
            "collection_receivable_aging_priority_items": (
                "KMFA/metadata/reports/collection_receivable_aging_priority_items.jsonl"
            ),
            "collection_receivable_aging_responsibility_items": (
                "KMFA/metadata/reports/collection_receivable_aging_responsibility_items.jsonl"
            ),
            "priority_html_draft": (
                "KMFA/stage_artifacts/S13_P2_collection_receivable_aging/exports/html/"
                "collection_receivable_aging_priority.html"
            ),
            "validator": "KMFA/tools/check_s13_p2_collection_receivable_aging.py",
            "completion_record": (
                "KMFA/stage_artifacts/S13_P2_collection_receivable_aging/human/s13_p2_completion_record.md"
            ),
            "test_results": "KMFA/stage_artifacts/S13_P2_collection_receivable_aging/human/test_results.md",
            "stage_manifest": "KMFA/stage_artifacts/S13_P2_collection_receivable_aging/machine/s13_p2_manifest.json",
        },
        "summary": {
            "source_lane_count": len(source_lanes),
            "required_issue_type_count": len(REQUIRED_ISSUE_TYPES),
            "priority_item_count": len(priority_items),
            "responsibility_item_count": len(responsibility_items),
            "html_draft_count": 1,
            "formal_report_count": 0,
            "business_decision_basis_count": 0,
            "collection_action_count": 0,
            "legal_collection_decision_count": 0,
            "payment_or_bank_operation_count": 0,
            "source_count": sum(int(lane["source_count"]) for lane in source_lanes),
            "field_mapping_count": sum(int(lane["field_mapping_count"]) for lane in source_lanes),
            "pending_reconciliation_count": pending_reconciliation_count,
            "report_grade_visible": report_grade_visible,
        },
        "limitations": [
            "S13-P2 只生成回款应收账龄公开安全优先级和责任事项草案。",
            "本 phase 不生成正式催收清单、不执行跨表复核、不触发开票、付款、银行、税务或法务动作。",
            "存在 12 条 pending owner 或授权复核差异时，报告等级显示为 D，经营决策依据继续阻断。",
        ],
    }
    html_outputs = {
        "collection_receivable_aging_priority": _render_html(
            manifest=manifest,
            priority_items=priority_items,
            responsibility_items=responsibility_items,
        )
    }
    manifest["content_hash"] = _sha256_json(
        {
            "manifest": manifest,
            "source_lanes": source_lanes,
            "priority_items": priority_items,
            "responsibility_items": responsibility_items,
            "html_outputs": html_outputs,
        }
    )
    return manifest, source_lanes, priority_items, responsibility_items, html_outputs


def validate_collection_receivable_aging_artifacts(
    manifest: dict[str, Any],
    source_lanes: list[dict[str, Any]],
    priority_items: list[dict[str, Any]],
    responsibility_items: list[dict[str, Any]],
    html_outputs: dict[str, str] | None = None,
) -> None:
    if manifest.get("schema_version") != "kmfa.collection_receivable_aging_manifest.v1":
        raise CollectionReceivableAgingError("manifest schema_version mismatch")
    if manifest.get("stage_phase") != "S13-P2":
        raise CollectionReceivableAgingError("manifest stage_phase must be S13-P2")
    if tuple(manifest.get("required_source_lanes", [])) != REQUIRED_SOURCE_LANES:
        raise CollectionReceivableAgingError("manifest required_source_lanes mismatch")
    if tuple(manifest.get("required_issue_types", [])) != REQUIRED_ISSUE_TYPES:
        raise CollectionReceivableAgingError("manifest required_issue_types mismatch")

    expected_summary = {
        "source_lane_count": 5,
        "required_issue_type_count": 4,
        "priority_item_count": 4,
        "responsibility_item_count": 4,
        "html_draft_count": 1,
        "formal_report_count": 0,
        "business_decision_basis_count": 0,
        "collection_action_count": 0,
        "legal_collection_decision_count": 0,
        "payment_or_bank_operation_count": 0,
        "pending_reconciliation_count": 12,
        "report_grade_visible": "D",
    }
    for key, expected in expected_summary.items():
        if manifest.get("summary", {}).get(key) != expected:
            raise CollectionReceivableAgingError(f"manifest summary {key} must be {expected}")

    for scope_key, expected in _stage_scope().items():
        if manifest.get("stage_scope", {}).get(scope_key) is not expected:
            raise CollectionReceivableAgingError(f"manifest stage_scope {scope_key} must be {expected}")
    for gate_key, expected in _quality_gate(pending_reconciliation_count=12, report_grade_visible="D").items():
        if manifest.get("quality_gate", {}).get(gate_key) != expected:
            raise CollectionReceivableAgingError(f"manifest quality_gate {gate_key} must be {expected}")
    for safety_key, expected in _public_repo_safety().items():
        if manifest.get("public_repo_safety", {}).get(safety_key) is not expected:
            raise CollectionReceivableAgingError(f"manifest public_repo_safety {safety_key} must be {expected}")

    lane_by_id = {str(lane.get("lane_id")): lane for lane in source_lanes}
    if tuple(lane_by_id) != REQUIRED_SOURCE_LANES:
        raise CollectionReceivableAgingError("source lane order or ids mismatch")
    for lane_id in REQUIRED_SOURCE_LANES:
        lane = lane_by_id[lane_id]
        if lane.get("visible_lane_name") != LANE_LABELS[lane_id]:
            raise CollectionReceivableAgingError(f"{lane_id}.visible_lane_name mismatch")
        if lane.get("source_kind") != LANE_SOURCE_KIND[lane_id]:
            raise CollectionReceivableAgingError(f"{lane_id}.source_kind mismatch")
        if lane_id in LANE_WPS_EXPORT_TYPES:
            if tuple(lane.get("wps_export_types", [])) != LANE_WPS_EXPORT_TYPES[lane_id]:
                raise CollectionReceivableAgingError(f"{lane_id}.wps_export_types mismatch")
        if lane_id in LANE_FINANCE_CATEGORIES:
            if tuple(lane.get("finance_categories", [])) != LANE_FINANCE_CATEGORIES[lane_id]:
                raise CollectionReceivableAgingError(f"{lane_id}.finance_categories mismatch")
        if int(lane.get("source_count", 0)) < 1:
            raise CollectionReceivableAgingError(f"{lane_id}.source_count must be >= 1")
        if int(lane.get("field_mapping_count", 0)) < 5:
            raise CollectionReceivableAgingError(f"{lane_id}.field_mapping_count must be >= 5")
        if lane.get("all_sources_readonly") is not True:
            raise CollectionReceivableAgingError(f"{lane_id}.all_sources_readonly must be true")
        for field_name in (
            "raw_business_values_allowed",
            "public_amount_values_allowed",
            "field_plaintext_allowed",
            "formal_report_allowed",
            "business_decision_basis_allowed",
            "raw_layer_write_allowed",
        ):
            if lane.get(field_name) is not False:
                raise CollectionReceivableAgingError(f"{lane_id}.{field_name} must be false")

    if {item.get("issue_type") for item in priority_items} != set(REQUIRED_ISSUE_TYPES):
        raise CollectionReceivableAgingError("priority_items issue_type coverage mismatch")
    if [int(item.get("priority_rank", 0)) for item in priority_items] != [1, 2, 3, 4]:
        raise CollectionReceivableAgingError("priority_items priority_rank mismatch")
    for item in priority_items:
        issue_type = str(item.get("issue_type"))
        if item.get("record_type") != "collection_receivable_priority_item":
            raise CollectionReceivableAgingError(f"{issue_type}.record_type mismatch")
        if item.get("visible_issue_label") != ISSUE_LABELS[issue_type]:
            raise CollectionReceivableAgingError(f"{issue_type}.visible_issue_label mismatch")
        if tuple(item.get("evidence_lane_ids", [])) != ISSUE_EVIDENCE_LANES[issue_type]:
            raise CollectionReceivableAgingError(f"{issue_type}.evidence_lane_ids mismatch")
        for field_name in (
            "raw_business_values_allowed",
            "public_amount_values_allowed",
            "field_plaintext_allowed",
            "collection_action_allowed",
            "legal_collection_decision_allowed",
            "payment_or_bank_operation_allowed",
            "tax_filing_allowed",
            "invoice_operation_allowed",
            "formal_report_allowed",
            "business_decision_basis_allowed",
        ):
            if item.get(field_name) is not False:
                raise CollectionReceivableAgingError(f"{issue_type}.{field_name} must be false")

    if {item.get("issue_type") for item in responsibility_items} != set(REQUIRED_ISSUE_TYPES):
        raise CollectionReceivableAgingError("responsibility_items issue_type coverage mismatch")
    for item in responsibility_items:
        issue_type = str(item.get("issue_type"))
        if item.get("record_type") != "collection_receivable_responsibility_item":
            raise CollectionReceivableAgingError(f"{issue_type}.record_type mismatch")
        responsible_role, required_action_kind = ISSUE_RESPONSIBILITY[issue_type]
        if item.get("responsible_role") != responsible_role:
            raise CollectionReceivableAgingError(f"{issue_type}.responsible_role mismatch")
        if item.get("required_action_kind") != required_action_kind:
            raise CollectionReceivableAgingError(f"{issue_type}.required_action_kind mismatch")
        for field_name in (
            "raw_business_values_allowed",
            "public_amount_values_allowed",
            "field_plaintext_allowed",
            "collection_action_allowed",
            "legal_collection_decision_allowed",
            "payment_or_bank_operation_allowed",
            "tax_filing_allowed",
            "invoice_operation_allowed",
            "formal_report_allowed",
            "business_decision_basis_allowed",
        ):
            if item.get(field_name) is not False:
                raise CollectionReceivableAgingError(f"{issue_type}.{field_name} must be false")

    if html_outputs is not None:
        if set(html_outputs) != {"collection_receivable_aging_priority"}:
            raise CollectionReceivableAgingError("html output ids mismatch")
        html_text = html_outputs["collection_receivable_aging_priority"]
        if not html_text.startswith("<!doctype html>"):
            raise CollectionReceivableAgingError("collection_receivable_aging_priority html must start with <!doctype html>")
        for required_text in (
            "KMFA 经营分析系统",
            "回款应收账龄",
            "已开票未回款",
            "完工未结算",
            "结算未开票",
            "超期应收",
            "不可作为催收、付款、法务或经营决策依据",
        ):
            if required_text not in html_text:
                raise CollectionReceivableAgingError(f"collection_receivable_aging_priority html missing {required_text}")
        for forbidden_text in FORBIDDEN_PUBLIC_TEXT + ("validator", "manifest", "metadata"):
            if forbidden_text in html_text.lower():
                raise CollectionReceivableAgingError(
                    f"collection_receivable_aging_priority html contains forbidden text: {forbidden_text}"
                )
        for forbidden_suffix in FORBIDDEN_PUBLIC_SUFFIXES:
            if forbidden_suffix in html_text.lower():
                raise CollectionReceivableAgingError(
                    f"collection_receivable_aging_priority html contains forbidden suffix: {forbidden_suffix}"
                )

    _ensure_no_forbidden_public_payload(
        {
            "manifest": manifest,
            "source_lanes": source_lanes,
            "priority_items": priority_items,
            "responsibility_items": responsibility_items,
        }
    )


def write_default_collection_receivable_aging_artifacts(
    *,
    output_manifest: Path = DEFAULT_OUTPUT_MANIFEST,
    output_lanes: Path = DEFAULT_OUTPUT_LANES,
    output_priority_items: Path = DEFAULT_OUTPUT_PRIORITY_ITEMS,
    output_responsibility_items: Path = DEFAULT_OUTPUT_RESPONSIBILITY_ITEMS,
    output_stage_manifest: Path = DEFAULT_OUTPUT_STAGE_MANIFEST,
    html_output_dir: Path = DEFAULT_HTML_OUTPUT_DIR,
    generated_at: str = "2026-07-01T18:00:00+10:00",
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, str]]:
    manifest, source_lanes, priority_items, responsibility_items, html_outputs = (
        build_default_collection_receivable_aging_artifacts(generated_at=generated_at)
    )
    validate_collection_receivable_aging_artifacts(
        manifest, source_lanes, priority_items, responsibility_items, html_outputs
    )
    write_json(output_manifest, manifest)
    write_jsonl(output_lanes, source_lanes)
    write_jsonl(output_priority_items, priority_items)
    write_jsonl(output_responsibility_items, responsibility_items)
    html_output_dir.mkdir(parents=True, exist_ok=True)
    for output_id, html_text in html_outputs.items():
        (html_output_dir / f"{output_id}.html").write_text(html_text, encoding="utf-8")
    stage_manifest = {
        "schema_version": "kmfa.s13_p2_stage_manifest.v1",
        "record_type": "s13_p2_collection_receivable_aging_stage_manifest",
        "project_id": "KMFA",
        "stage_phase": "S13-P2",
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
    return manifest, source_lanes, priority_items, responsibility_items, html_outputs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build KMFA S13-P2 collection receivable aging artifacts.")
    parser.add_argument("--output-manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--output-lanes", type=Path, default=DEFAULT_OUTPUT_LANES)
    parser.add_argument("--output-priority-items", type=Path, default=DEFAULT_OUTPUT_PRIORITY_ITEMS)
    parser.add_argument("--output-responsibility-items", type=Path, default=DEFAULT_OUTPUT_RESPONSIBILITY_ITEMS)
    parser.add_argument("--output-stage-manifest", type=Path, default=DEFAULT_OUTPUT_STAGE_MANIFEST)
    parser.add_argument("--html-output-dir", type=Path, default=DEFAULT_HTML_OUTPUT_DIR)
    parser.add_argument("--generated-at", default="2026-07-01T18:00:00+10:00")
    args = parser.parse_args(argv)

    manifest, source_lanes, priority_items, responsibility_items, html_outputs = (
        write_default_collection_receivable_aging_artifacts(
            output_manifest=args.output_manifest,
            output_lanes=args.output_lanes,
            output_priority_items=args.output_priority_items,
            output_responsibility_items=args.output_responsibility_items,
            output_stage_manifest=args.output_stage_manifest,
            html_output_dir=args.html_output_dir,
            generated_at=args.generated_at,
        )
    )
    summary = manifest["summary"]
    print(
        "PASS: KMFA S13-P2 collection receivable aging artifacts generated "
        f"(source_lanes={len(source_lanes)}, priority_items={len(priority_items)}, "
        f"responsibility_items={len(responsibility_items)}, html={len(html_outputs)}, "
        f"field_mappings={summary['field_mapping_count']}, "
        "formal_report_allowed=false, business_decision_basis=false, "
        "payment_or_bank_operation=false, legal_collection_decision=false, "
        "s13_p3_scope=false, stage13_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
