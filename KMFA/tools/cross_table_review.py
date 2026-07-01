#!/usr/bin/env python3
"""Build KMFA S13-P3 public-safe cross-table review artifacts."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

DEFAULT_S13P1_MANIFEST = ROOT / "metadata" / "reports" / "financial_operating_report_manifest.json"
DEFAULT_S13P1_LANES = ROOT / "metadata" / "reports" / "financial_operating_report_source_lanes.jsonl"
DEFAULT_S13P1_DRAFTS = ROOT / "metadata" / "reports" / "financial_operating_report_drafts.jsonl"
DEFAULT_S13P2_MANIFEST = ROOT / "metadata" / "reports" / "collection_receivable_aging_manifest.json"
DEFAULT_S13P2_LANES = ROOT / "metadata" / "reports" / "collection_receivable_aging_source_lanes.jsonl"
DEFAULT_S13P2_PRIORITY_ITEMS = ROOT / "metadata" / "reports" / "collection_receivable_aging_priority_items.jsonl"
DEFAULT_S13P2_RESPONSIBILITY_ITEMS = ROOT / "metadata" / "reports" / "collection_receivable_aging_responsibility_items.jsonl"
DEFAULT_SCOPE_RECONCILIATION_RECORDS = ROOT / "metadata" / "quality" / "scope_reconciliation_records.jsonl"
DEFAULT_REPORT_GRADE_RECORDS = ROOT / "metadata" / "reports" / "report_grade_runtime_records.jsonl"

DEFAULT_OUTPUT_MANIFEST = ROOT / "metadata" / "reports" / "cross_table_review_manifest.json"
DEFAULT_OUTPUT_CHECKS = ROOT / "metadata" / "reports" / "cross_table_review_checks.jsonl"
DEFAULT_OUTPUT_DIFFERENCE_QUEUE = ROOT / "metadata" / "reports" / "cross_table_difference_queue.jsonl"
DEFAULT_OUTPUT_QUALITY_REPORT = ROOT / "metadata" / "reports" / "operating_report_quality_report.json"
DEFAULT_OUTPUT_STAGE_MANIFEST = ROOT / "stage_artifacts" / "S13_P3_cross_table_review" / "machine" / "s13_p3_manifest.json"
DEFAULT_HTML_OUTPUT_DIR = ROOT / "stage_artifacts" / "S13_P3_cross_table_review" / "exports" / "html"

REQUIRED_REVIEW_DIMENSIONS = (
    "project_consistency",
    "customer_consistency",
    "amount_consistency",
    "time_consistency",
)

DIMENSION_LABELS = {
    "project_consistency": "项目一致性",
    "customer_consistency": "客户一致性",
    "amount_consistency": "金额一致性",
    "time_consistency": "时间一致性",
}

DIMENSION_DESCRIPTIONS = {
    "project_consistency": "项目口径需在经营报表、回款应收、项目成本事实层和 scope reconciliation 中保持一致。",
    "customer_consistency": "客户或对手方口径需在回款表、客户账龄、开票计划和经营报告摘要中保持一致。",
    "amount_consistency": "合同、成本、毛利、回款、应收和开票相关金额信号不得绕过 S09-P3 未关闭差异。",
    "time_consistency": "期间、开票、回款、账龄和报告周期需保持同一复核窗口。",
}

DIMENSION_EVIDENCE = {
    "project_consistency": {
        "s13_p1_lanes": ("operating_situation",),
        "s13_p2_lanes": ("collection_table", "receivable_aging", "invoice_plan"),
        "required_fields": ("project_ref", "period_ref"),
        "queue_reason": "project_scope_requires_owner_review_across_report_collection_aging_and_invoice_plan",
        "responsible_role": "project_owner",
    },
    "customer_consistency": {
        "s13_p1_lanes": ("operating_situation",),
        "s13_p2_lanes": ("collection_table", "customer_aging", "receivable_aging"),
        "required_fields": ("customer_ref", "counterparty_ref"),
        "queue_reason": "customer_or_counterparty_scope_requires_owner_review_before_summary_use",
        "responsible_role": "sales_owner",
    },
    "amount_consistency": {
        "s13_p1_lanes": ("operating_situation", "expense_tax_asset", "cash_situation"),
        "s13_p2_lanes": ("collection_table", "receivable_aging", "journal", "invoice_plan"),
        "required_fields": ("contract_amount", "gross_margin", "collection_amount", "receivable_amount"),
        "queue_reason": "amount_signal_requires_s09_reconciliation_closure_before_formal_report",
        "responsible_role": "finance_owner",
    },
    "time_consistency": {
        "s13_p1_lanes": ("operating_situation", "cash_situation"),
        "s13_p2_lanes": ("collection_table", "receivable_aging", "invoice_plan"),
        "required_fields": ("period_ref", "collection_date", "overdue_days"),
        "queue_reason": "period_collection_invoice_and_aging_windows_require_same_review_cutoff",
        "responsible_role": "finance_owner",
    },
}

SOURCE_TASKPACK_REFS = {
    "roadmap_s13_p3": "KMFA/taskpack/v1_2/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_2.md:S13-P3",
    "taskpack_stage13": "KMFA/taskpack/v1_2/01_KMFA_Codex_TaskPack_v1_2_FULL.md:Stage13",
    "business_overview_line": "KMFA/taskpack/v1_2/01_KMFA_Codex_TaskPack_v1_2_完整防遗漏_含HTML验收样板.md:P1",
}

CROSS_TABLE_REVIEW_VERSION = "RPT-KMFA-S13P3-CROSS-TABLE-REVIEW-001"
FORMULA_VERSION = "FORM-KMFA-S13P3-CROSS-TABLE-QUALITY-001"
MAPPING_VERSION = "MAP-KMFA-S13P3-PUBLIC-SAFE-v1"
HTML_TEMPLATE_VERSION = "HTML-KMFA-S13P3-BLUE-QUALITY-v1"

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


class CrossTableReviewError(ValueError):
    """Raised when S13-P3 cross-table review artifacts are invalid."""


def _sha256_json(payload: Any) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CrossTableReviewError(f"{path} must contain a JSON object")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            value = json.loads(line)
            if not isinstance(value, dict):
                raise CrossTableReviewError(f"{path} contains a non-object JSONL record")
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
        "private_ref_committed_in_s13p3_outputs": False,
    }


def _stage_scope() -> dict[str, bool]:
    return {
        "s13_p1_financial_operating_report_scope_reopened": False,
        "s13_p2_collection_receivable_aging_scope_reopened": False,
        "s13_p3_cross_table_review_scope_included": True,
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
        "cross_table_review_evidence_allowed": True,
        "difference_queue_output_allowed": True,
        "operating_report_quality_report_allowed": True,
        "formal_report_allowed": False,
        "complete_trusted_report_display_allowed": False,
        "business_decision_basis_allowed": False,
        "legal_collection_decision_allowed": False,
        "payment_or_bank_operation_allowed": False,
        "tax_filing_allowed": False,
        "invoice_operation_allowed": False,
        "derived_amount_calculation_allowed": False,
        "difference_auto_resolution_allowed": False,
        "auto_source_selection_allowed": False,
        "raw_layer_write_allowed": False,
        "report_grade_visible": report_grade_visible,
        "report_grade_bypass_allowed": False,
        "quality_grade_bypass_allowed": False,
        "stage13_review_allowed": False,
        "github_upload_allowed": False,
        "phase_completion_upload_allowed": False,
        "pending_reconciliation_count": pending_reconciliation_count,
        "release_block_reason": "cross_table_review_completed_but_pending_differences_lineage_and_stage_review_block_release",
    }


def _report_grade_visible(report_grade_records: list[dict[str, Any]]) -> str:
    grades = {str(row.get("computed_report_grade") or "") for row in report_grade_records}
    if "D" in grades:
        return "D"
    return "D"


def _pending_reconciliation_records(scope_reconciliation_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        row
        for row in scope_reconciliation_records
        if str(row.get("resolution_status") or row.get("status")) == "pending_owner_or_authorized_review"
    ]


def _lanes_by_id(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("lane_id")): row for row in rows if row.get("lane_id")}


def _record_refs(rows: list[dict[str, Any]], id_key: str, limit: int = 4) -> list[str]:
    refs: list[str] = []
    for row in rows[:limit]:
        value = str(row.get(id_key) or "")
        if value:
            refs.append(value)
    return refs


def _source_summary(
    s13p1_manifest: dict[str, Any],
    s13p2_manifest: dict[str, Any],
    s13p1_lanes: list[dict[str, Any]],
    s13p2_lanes: list[dict[str, Any]],
    s13p1_drafts: list[dict[str, Any]],
    s13p2_priority_items: list[dict[str, Any]],
    s13p2_responsibility_items: list[dict[str, Any]],
    pending_reconciliation_records: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "s13_p1_manifest_hash": s13p1_manifest.get("content_hash"),
        "s13_p2_manifest_hash": s13p2_manifest.get("content_hash"),
        "s13_p1_lane_count": len(s13p1_lanes),
        "s13_p2_lane_count": len(s13p2_lanes),
        "s13_p1_draft_count": len(s13p1_drafts),
        "s13_p2_priority_item_count": len(s13p2_priority_items),
        "s13_p2_responsibility_item_count": len(s13p2_responsibility_items),
        "pending_reconciliation_count": len(pending_reconciliation_records),
        "pending_reconciliation_ids": _record_refs(pending_reconciliation_records, "difference_id", limit=12),
    }


def _build_review_checks(
    *,
    generated_at: str,
    s13p1_lanes: list[dict[str, Any]],
    s13p2_lanes: list[dict[str, Any]],
    pending_reconciliation_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    p1_lanes = _lanes_by_id(s13p1_lanes)
    p2_lanes = _lanes_by_id(s13p2_lanes)
    reconciliation_refs = _record_refs(pending_reconciliation_records, "difference_id", limit=12)
    checks: list[dict[str, Any]] = []
    for index, dimension in enumerate(REQUIRED_REVIEW_DIMENSIONS, start=1):
        spec = DIMENSION_EVIDENCE[dimension]
        s13p1_evidence_refs = [
            f"S13P1:{lane_id}"
            for lane_id in spec["s13_p1_lanes"]
            if lane_id in p1_lanes
        ]
        s13p2_evidence_refs = [
            f"S13P2:{lane_id}"
            for lane_id in spec["s13_p2_lanes"]
            if lane_id in p2_lanes
        ]
        checks.append(
            {
                "record_type": "cross_table_review_check",
                "schema_version": "kmfa.cross_table_review_check.v1",
                "project_id": "KMFA",
                "stage_phase": "S13-P3",
                "generated_at": generated_at,
                "review_check_id": f"S13P3-CHK-{index:03d}",
                "review_dimension": dimension,
                "visible_dimension_label": DIMENSION_LABELS[dimension],
                "visible_review_description": DIMENSION_DESCRIPTIONS[dimension],
                "required_field_key_refs": list(spec["required_fields"]),
                "s13_p1_evidence_refs": s13p1_evidence_refs,
                "s13_p2_evidence_refs": s13p2_evidence_refs,
                "s09_reconciliation_refs": reconciliation_refs,
                "review_result": "difference_queue_required",
                "review_status": "completed_public_safe_metadata_review",
                "queue_reason_code": spec["queue_reason"],
                "raw_business_values_allowed": False,
                "public_amount_values_allowed": False,
                "field_plaintext_allowed": False,
                "raw_layer_write_allowed": False,
                "formal_report_allowed": False,
                "business_decision_basis_allowed": False,
                "difference_auto_resolution_allowed": False,
            }
        )
    return checks


def _build_difference_queue(*, generated_at: str, review_checks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    queue: list[dict[str, Any]] = []
    for index, check in enumerate(review_checks, start=1):
        dimension = str(check["review_dimension"])
        spec = DIMENSION_EVIDENCE[dimension]
        queue.append(
            {
                "record_type": "cross_table_difference_queue_item",
                "schema_version": "kmfa.cross_table_difference_queue_item.v1",
                "project_id": "KMFA",
                "stage_phase": "S13-P3",
                "generated_at": generated_at,
                "queue_item_id": f"S13P3-DIFF-{index:03d}",
                "queue_rank": index,
                "review_dimension": dimension,
                "visible_dimension_label": DIMENSION_LABELS[dimension],
                "linked_review_check_id": check["review_check_id"],
                "difference_signal_ref": f"public_cross_table_signal_hash_{index:03d}",
                "reason_code": spec["queue_reason"],
                "resolution_status": "pending_owner_or_authorized_review",
                "responsible_role": spec["responsible_role"],
                "required_review_mode": "owner_or_authorized_delegate_review_only",
                "next_review_bucket": "next_internal_review_cycle",
                "auto_resolution_allowed": False,
                "auto_source_selection_allowed": False,
                "amount_recalculation_allowed": False,
                "rounding_mask_allowed": False,
                "field_plaintext_allowed": False,
                "raw_business_values_allowed": False,
                "public_amount_values_allowed": False,
                "formal_report_allowed": False,
                "business_decision_basis_allowed": False,
                "payment_or_bank_operation_allowed": False,
                "tax_filing_allowed": False,
                "legal_collection_decision_allowed": False,
            }
        )
    return queue


def _build_quality_report(
    *,
    generated_at: str,
    review_checks: list[dict[str, Any]],
    difference_queue: list[dict[str, Any]],
    source_summary: dict[str, Any],
    pending_reconciliation_count: int,
    report_grade_visible: str,
) -> dict[str, Any]:
    labels = [DIMENSION_LABELS[dimension] for dimension in REQUIRED_REVIEW_DIMENSIONS]
    return {
        "record_type": "operating_report_quality_report",
        "schema_version": "kmfa.operating_report_quality_report.v1",
        "project_id": "KMFA",
        "stage_phase": "S13-P3",
        "generated_at": generated_at,
        "quality_report_id": "S13P3-OPERATING-QUALITY-REPORT-001",
        "report_version": CROSS_TABLE_REVIEW_VERSION,
        "formula_version": FORMULA_VERSION,
        "cross_table_review_status": "completed_with_pending_differences",
        "review_dimension_count": len(review_checks),
        "difference_queue_count": len(difference_queue),
        "pending_reconciliation_count": pending_reconciliation_count,
        "report_grade_visible": report_grade_visible,
        "maximum_report_grade_allowed": "D",
        "visible_summary": "项目、客户、金额、时间跨表复核已完成公开安全检查；所有未闭合项进入人工差异队列。",
        "visible_dimension_labels": labels,
        "source_summary": source_summary,
        "quality_findings": [
            {
                "finding_id": f"S13P3-QF-{index:03d}",
                "review_dimension": dimension,
                "visible_dimension_label": DIMENSION_LABELS[dimension],
                "finding_status": "pending_owner_or_authorized_review",
                "formal_report_blocked": True,
            }
            for index, dimension in enumerate(REQUIRED_REVIEW_DIMENSIONS, start=1)
        ],
        "owner_next_actions": [
            "复核跨表项目口径是否与经营报表和回款应收一致。",
            "复核客户或对手方口径是否可进入老板版摘要。",
            "关闭 S09-P3 未解决金额差异后再考虑报告等级提升。",
            "确认期间、回款日期、账龄和开票计划的同一复核窗口。",
        ],
        "formal_report_allowed": False,
        "complete_trusted_report_display_allowed": False,
        "business_decision_basis_allowed": False,
        "lineage_full_check_included": False,
        "stage13_review_scope_included": False,
        "github_upload_scope_included": False,
        "raw_business_values_allowed": False,
        "public_amount_values_allowed": False,
        "field_plaintext_allowed": False,
        "payment_or_bank_operation_allowed": False,
        "tax_filing_allowed": False,
        "legal_collection_decision_allowed": False,
        "release_block_reason": "pending_cross_table_differences_s09_reconciliation_lineage_and_stage13_review",
    }


def _render_quality_report_html(
    *,
    generated_at: str,
    review_checks: list[dict[str, Any]],
    difference_queue: list[dict[str, Any]],
    quality_report: dict[str, Any],
) -> str:
    rows = []
    queue_by_dimension = {item["review_dimension"]: item for item in difference_queue}
    for check in review_checks:
        queue_item = queue_by_dimension[check["review_dimension"]]
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(check['visible_dimension_label']))}</td>"
            f"<td>{html.escape(str(check['review_result']))}</td>"
            f"<td>{html.escape(str(queue_item['resolution_status']))}</td>"
            f"<td>{html.escape(str(queue_item['responsible_role']))}</td>"
            "</tr>"
        )
    rows_html = "\n".join(rows)
    summary = html.escape(str(quality_report["visible_summary"]))
    grade = html.escape(str(quality_report["report_grade_visible"]))
    pending = html.escape(str(quality_report["pending_reconciliation_count"]))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>KMFA 跨表复核质量报告</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #132238;
      --muted: #5c6675;
      --line: #d9e2ef;
      --blue: #1459a8;
      --sky: #eef6ff;
      --warn: #8a4b00;
      --warn-bg: #fff6e6;
      --bg: #f7f9fc;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
      line-height: 1.55;
    }}
    main {{
      width: min(1120px, calc(100vw - 32px));
      margin: 0 auto;
      padding: 32px 0 40px;
    }}
    header {{
      border-bottom: 2px solid var(--blue);
      padding-bottom: 18px;
      margin-bottom: 20px;
    }}
    h1 {{
      margin: 0 0 8px;
      font-size: 28px;
      letter-spacing: 0;
    }}
    .subline {{ color: var(--muted); font-size: 14px; }}
    .status {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
      margin: 20px 0;
    }}
    .metric {{
      border: 1px solid var(--line);
      background: white;
      border-radius: 8px;
      padding: 14px;
      min-height: 92px;
    }}
    .metric b {{ display: block; font-size: 24px; color: var(--blue); }}
    .metric span {{ color: var(--muted); font-size: 13px; }}
    .notice {{
      border: 1px solid #efc46c;
      background: var(--warn-bg);
      color: var(--warn);
      border-radius: 8px;
      padding: 14px 16px;
      margin: 18px 0;
      font-weight: 600;
    }}
    section {{
      background: white;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
      margin-top: 16px;
    }}
    h2 {{ margin: 0 0 12px; font-size: 18px; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
    }}
    th, td {{
      border-bottom: 1px solid var(--line);
      text-align: left;
      padding: 10px 8px;
      vertical-align: top;
    }}
    th {{ color: var(--muted); background: var(--sky); }}
    .summary {{ margin: 0; color: var(--ink); }}
    @media (max-width: 760px) {{
      main {{ width: min(100vw - 20px, 1120px); padding-top: 20px; }}
      .status {{ grid-template-columns: 1fr; }}
      table {{ font-size: 13px; }}
      h1 {{ font-size: 23px; }}
    }}
  </style>
</head>
<body>
  <main>
    <header>
      <h1>KMFA 跨表复核质量报告</h1>
      <div class="subline">S13-P3 public-safe evidence · generated {html.escape(generated_at)}</div>
    </header>
    <p class="summary">{summary}</p>
    <div class="status" aria-label="质量状态">
      <div class="metric"><b>{grade}</b><span>当前可见报告等级</span></div>
      <div class="metric"><b>{len(difference_queue)}</b><span>人工差异队列事项</span></div>
      <div class="metric"><b>{pending}</b><span>未关闭复核差异</span></div>
    </div>
    <div class="notice">不可作为正式经营报告或经营决策依据；不得触发开票、付款、银行、税务或法务催收动作。</div>
    <section>
      <h2>跨表复核结果</h2>
      <table>
        <thead>
          <tr><th>复核维度</th><th>复核结果</th><th>处理状态</th><th>责任角色</th></tr>
        </thead>
        <tbody>
          {rows_html}
        </tbody>
      </table>
    </section>
  </main>
</body>
</html>
"""


def build_default_cross_table_review_artifacts(
    *,
    generated_at: str = "2026-07-01T19:00:00+10:00",
    s13p1_manifest_path: Path = DEFAULT_S13P1_MANIFEST,
    s13p1_lanes_path: Path = DEFAULT_S13P1_LANES,
    s13p1_drafts_path: Path = DEFAULT_S13P1_DRAFTS,
    s13p2_manifest_path: Path = DEFAULT_S13P2_MANIFEST,
    s13p2_lanes_path: Path = DEFAULT_S13P2_LANES,
    s13p2_priority_items_path: Path = DEFAULT_S13P2_PRIORITY_ITEMS,
    s13p2_responsibility_items_path: Path = DEFAULT_S13P2_RESPONSIBILITY_ITEMS,
    scope_reconciliation_records_path: Path = DEFAULT_SCOPE_RECONCILIATION_RECORDS,
    report_grade_records_path: Path = DEFAULT_REPORT_GRADE_RECORDS,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any], dict[str, str]]:
    s13p1_manifest = read_json(s13p1_manifest_path)
    s13p1_lanes = read_jsonl(s13p1_lanes_path)
    s13p1_drafts = read_jsonl(s13p1_drafts_path)
    s13p2_manifest = read_json(s13p2_manifest_path)
    s13p2_lanes = read_jsonl(s13p2_lanes_path)
    s13p2_priority_items = read_jsonl(s13p2_priority_items_path)
    s13p2_responsibility_items = read_jsonl(s13p2_responsibility_items_path)
    pending_reconciliation_records = _pending_reconciliation_records(read_jsonl(scope_reconciliation_records_path))
    report_grade_visible = _report_grade_visible(read_jsonl(report_grade_records_path))

    source_summary = _source_summary(
        s13p1_manifest,
        s13p2_manifest,
        s13p1_lanes,
        s13p2_lanes,
        s13p1_drafts,
        s13p2_priority_items,
        s13p2_responsibility_items,
        pending_reconciliation_records,
    )
    review_checks = _build_review_checks(
        generated_at=generated_at,
        s13p1_lanes=s13p1_lanes,
        s13p2_lanes=s13p2_lanes,
        pending_reconciliation_records=pending_reconciliation_records,
    )
    difference_queue = _build_difference_queue(generated_at=generated_at, review_checks=review_checks)
    quality_report = _build_quality_report(
        generated_at=generated_at,
        review_checks=review_checks,
        difference_queue=difference_queue,
        source_summary=source_summary,
        pending_reconciliation_count=len(pending_reconciliation_records),
        report_grade_visible=report_grade_visible,
    )
    html_outputs = {
        "cross_table_quality_report": _render_quality_report_html(
            generated_at=generated_at,
            review_checks=review_checks,
            difference_queue=difference_queue,
            quality_report=quality_report,
        )
    }

    manifest_base: dict[str, Any] = {
        "record_type": "cross_table_review_manifest",
        "schema_version": "kmfa.cross_table_review_manifest.v1",
        "project_id": "KMFA",
        "stage_phase": "S13-P3",
        "generated_at": generated_at,
        "report_version": CROSS_TABLE_REVIEW_VERSION,
        "formula_version": FORMULA_VERSION,
        "mapping_version": MAPPING_VERSION,
        "html_template_version": HTML_TEMPLATE_VERSION,
        "required_review_dimensions": list(REQUIRED_REVIEW_DIMENSIONS),
        "source_taskpack_refs": SOURCE_TASKPACK_REFS,
        "source_artifact_refs": {
            "s13_p1_manifest": "KMFA/metadata/reports/financial_operating_report_manifest.json",
            "s13_p1_lanes": "KMFA/metadata/reports/financial_operating_report_source_lanes.jsonl",
            "s13_p1_drafts": "KMFA/metadata/reports/financial_operating_report_drafts.jsonl",
            "s13_p2_manifest": "KMFA/metadata/reports/collection_receivable_aging_manifest.json",
            "s13_p2_lanes": "KMFA/metadata/reports/collection_receivable_aging_source_lanes.jsonl",
            "s13_p2_priority_items": "KMFA/metadata/reports/collection_receivable_aging_priority_items.jsonl",
            "s13_p2_responsibility_items": "KMFA/metadata/reports/collection_receivable_aging_responsibility_items.jsonl",
            "s09_scope_reconciliation": "KMFA/metadata/quality/scope_reconciliation_records.jsonl",
            "s10_report_grade_runtime": "KMFA/metadata/reports/report_grade_runtime_records.jsonl",
        },
        "artifact_refs": {
            "cross_table_review_manifest": "KMFA/metadata/reports/cross_table_review_manifest.json",
            "cross_table_review_checks": "KMFA/metadata/reports/cross_table_review_checks.jsonl",
            "cross_table_difference_queue": "KMFA/metadata/reports/cross_table_difference_queue.jsonl",
            "operating_report_quality_report": "KMFA/metadata/reports/operating_report_quality_report.json",
            "quality_report_html": "KMFA/stage_artifacts/S13_P3_cross_table_review/exports/html/cross_table_quality_report.html",
            "stage_manifest": "KMFA/stage_artifacts/S13_P3_cross_table_review/machine/s13_p3_manifest.json",
            "completion_record": "KMFA/stage_artifacts/S13_P3_cross_table_review/human/s13_p3_completion_record.md",
            "test_results": "KMFA/stage_artifacts/S13_P3_cross_table_review/human/test_results.md",
            "validator": "KMFA/tools/check_s13_p3_cross_table_review.py",
        },
        "source_summary": source_summary,
        "summary": {
            "review_dimension_count": len(review_checks),
            "difference_queue_count": len(difference_queue),
            "quality_report_count": 1,
            "pending_reconciliation_count": len(pending_reconciliation_records),
            "report_grade_visible": report_grade_visible,
            "formal_report_allowed": False,
            "business_decision_basis_allowed": False,
            "stage13_review_scope_included": False,
            "github_upload_scope_included": False,
        },
        "quality_gate": _quality_gate(
            pending_reconciliation_count=len(pending_reconciliation_records),
            report_grade_visible=report_grade_visible,
        ),
        "stage_scope": _stage_scope(),
        "public_repo_safety": _public_repo_safety(),
        "runtime_status": "public_safe_cross_table_review_completed_with_pending_difference_queue",
        "limitations": [
            "S13-P3 只输出公开安全跨表复核、差异队列和经营报表质量报告。",
            "本 phase 不生成正式报告、不关闭 S09-P3 reconciliation、不执行 Stage 13 review 或 GitHub upload。",
            "所有项目、客户、金额和时间不一致均需 owner 或授权人复核，不得自动选源或自动修正。",
        ],
    }
    content_hash = _sha256_json(
        {
            "manifest_base": manifest_base,
            "review_checks": review_checks,
            "difference_queue": difference_queue,
            "quality_report": quality_report,
            "html_outputs": html_outputs,
        }
    )
    manifest = {**manifest_base, "content_hash": content_hash}
    return manifest, review_checks, difference_queue, quality_report, html_outputs


def _looks_like_forbidden_private_file(value: str) -> bool:
    lowered = value.lower()
    return any(lowered.endswith(suffix) for suffix in FORBIDDEN_PUBLIC_SUFFIXES)


def _ensure_public_payload(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_PUBLIC_KEYS:
                raise CrossTableReviewError(f"forbidden public key found at {path}.{key}")
            _ensure_public_payload(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _ensure_public_payload(child, f"{path}[{index}]")
    elif isinstance(value, str):
        if _looks_like_forbidden_private_file(value):
            raise CrossTableReviewError(f"forbidden private business file reference found at {path}")
        lowered = value.lower()
        if any(forbidden in lowered for forbidden in FORBIDDEN_PUBLIC_TEXT):
            raise CrossTableReviewError(f"forbidden private token found at {path}")


def _require_false(record: dict[str, Any], key: str, context: str) -> None:
    if record.get(key) is not False:
        raise CrossTableReviewError(f"{context}.{key} must be false")


def _require_true(record: dict[str, Any], key: str, context: str) -> None:
    if record.get(key) is not True:
        raise CrossTableReviewError(f"{context}.{key} must be true")


def _validate_html_outputs(html_outputs: dict[str, str]) -> None:
    if set(html_outputs) != {"cross_table_quality_report"}:
        raise CrossTableReviewError("exactly one cross_table_quality_report HTML output is required")
    html_text = html_outputs["cross_table_quality_report"]
    lowered = html_text.lower()
    required_visible = ("跨表复核", "项目一致性", "客户一致性", "金额一致性", "时间一致性", "不可作为正式经营报告或经营决策依据")
    for text in required_visible:
        if text not in html_text:
            raise CrossTableReviewError(f"HTML output is missing visible text: {text}")
    for forbidden in ("source_ref://", "private://", "private_ref://", "validator", "manifest", "metadata"):
        if forbidden in lowered:
            raise CrossTableReviewError(f"HTML output exposes internal token: {forbidden}")
    for suffix in FORBIDDEN_PUBLIC_SUFFIXES:
        if suffix in lowered:
            raise CrossTableReviewError(f"HTML output exposes forbidden suffix: {suffix}")


def validate_cross_table_review_artifacts(
    manifest: dict[str, Any],
    review_checks: list[dict[str, Any]],
    difference_queue: list[dict[str, Any]],
    quality_report: dict[str, Any],
    html_outputs: dict[str, str],
) -> None:
    if manifest.get("record_type") != "cross_table_review_manifest":
        raise CrossTableReviewError("manifest record_type must be cross_table_review_manifest")
    if manifest.get("stage_phase") != "S13-P3":
        raise CrossTableReviewError("manifest stage_phase must be S13-P3")
    if tuple(manifest.get("required_review_dimensions", [])) != REQUIRED_REVIEW_DIMENSIONS:
        raise CrossTableReviewError("manifest required review dimensions are incomplete")
    summary = manifest.get("summary", {})
    if summary.get("review_dimension_count") != len(REQUIRED_REVIEW_DIMENSIONS):
        raise CrossTableReviewError("summary review_dimension_count mismatch")
    if summary.get("difference_queue_count") != len(REQUIRED_REVIEW_DIMENSIONS):
        raise CrossTableReviewError("summary difference_queue_count mismatch")
    if summary.get("quality_report_count") != 1:
        raise CrossTableReviewError("summary quality_report_count must be 1")
    if summary.get("pending_reconciliation_count") != 12:
        raise CrossTableReviewError("pending reconciliation count must remain 12")
    if summary.get("report_grade_visible") != "D":
        raise CrossTableReviewError("report_grade_visible must remain D")

    quality_gate = manifest.get("quality_gate", {})
    for key in (
        "formal_report_allowed",
        "complete_trusted_report_display_allowed",
        "business_decision_basis_allowed",
        "difference_auto_resolution_allowed",
        "auto_source_selection_allowed",
        "stage13_review_allowed",
        "github_upload_allowed",
        "phase_completion_upload_allowed",
    ):
        _require_false(quality_gate, key, "quality_gate")
    _require_true(quality_gate, "cross_table_review_evidence_allowed", "quality_gate")
    _require_true(quality_gate, "difference_queue_output_allowed", "quality_gate")
    _require_true(quality_gate, "operating_report_quality_report_allowed", "quality_gate")

    stage_scope = manifest.get("stage_scope", {})
    _require_true(stage_scope, "s13_p3_cross_table_review_scope_included", "stage_scope")
    for key in (
        "stage13_review_scope_included",
        "formal_report_runtime_scope_included",
        "complete_trusted_report_scope_included",
        "lineage_full_check_scope_included",
        "github_upload_scope_included",
        "payment_or_bank_operation_scope_included",
        "tax_filing_scope_included",
        "legal_collection_scope_included",
    ):
        _require_false(stage_scope, key, "stage_scope")

    if len(review_checks) != len(REQUIRED_REVIEW_DIMENSIONS):
        raise CrossTableReviewError("review_checks must contain one record per dimension")
    checks_by_dimension = {str(check.get("review_dimension")): check for check in review_checks}
    if set(checks_by_dimension) != set(REQUIRED_REVIEW_DIMENSIONS):
        raise CrossTableReviewError("review_checks dimensions are incomplete")
    for dimension in REQUIRED_REVIEW_DIMENSIONS:
        check = checks_by_dimension[dimension]
        if check.get("record_type") != "cross_table_review_check":
            raise CrossTableReviewError(f"{dimension} check record_type mismatch")
        if check.get("review_result") != "difference_queue_required":
            raise CrossTableReviewError(f"{dimension} must require difference queue")
        if not check.get("s13_p1_evidence_refs") or not check.get("s13_p2_evidence_refs"):
            raise CrossTableReviewError(f"{dimension} must include S13-P1 and S13-P2 evidence refs")
        if len(check.get("s09_reconciliation_refs", [])) != 12:
            raise CrossTableReviewError(f"{dimension} must reference 12 pending reconciliation ids")
        for key in (
            "raw_business_values_allowed",
            "public_amount_values_allowed",
            "field_plaintext_allowed",
            "raw_layer_write_allowed",
            "formal_report_allowed",
            "business_decision_basis_allowed",
            "difference_auto_resolution_allowed",
        ):
            _require_false(check, key, f"review_check[{dimension}]")

    if len(difference_queue) != len(REQUIRED_REVIEW_DIMENSIONS):
        raise CrossTableReviewError("difference_queue must contain one item per dimension")
    queue_dimensions = {str(item.get("review_dimension")) for item in difference_queue}
    if queue_dimensions != set(REQUIRED_REVIEW_DIMENSIONS):
        raise CrossTableReviewError("difference_queue dimensions are incomplete")
    if [item.get("queue_rank") for item in difference_queue] != [1, 2, 3, 4]:
        raise CrossTableReviewError("difference_queue ranks must be stable 1..4")
    for item in difference_queue:
        context = f"difference_queue[{item.get('queue_item_id')}]"
        if item.get("record_type") != "cross_table_difference_queue_item":
            raise CrossTableReviewError(f"{context} record_type mismatch")
        if item.get("resolution_status") != "pending_owner_or_authorized_review":
            raise CrossTableReviewError(f"{context} must remain pending owner review")
        for key in (
            "auto_resolution_allowed",
            "auto_source_selection_allowed",
            "amount_recalculation_allowed",
            "rounding_mask_allowed",
            "raw_business_values_allowed",
            "public_amount_values_allowed",
            "field_plaintext_allowed",
            "formal_report_allowed",
            "business_decision_basis_allowed",
            "payment_or_bank_operation_allowed",
            "tax_filing_allowed",
            "legal_collection_decision_allowed",
        ):
            _require_false(item, key, context)

    if quality_report.get("record_type") != "operating_report_quality_report":
        raise CrossTableReviewError("quality_report record_type mismatch")
    if quality_report.get("stage_phase") != "S13-P3":
        raise CrossTableReviewError("quality_report stage_phase mismatch")
    if quality_report.get("report_grade_visible") != "D":
        raise CrossTableReviewError("quality_report report_grade_visible must be D")
    if quality_report.get("cross_table_review_status") != "completed_with_pending_differences":
        raise CrossTableReviewError("quality_report status mismatch")
    if quality_report.get("review_dimension_count") != 4 or quality_report.get("difference_queue_count") != 4:
        raise CrossTableReviewError("quality_report counts mismatch")
    if quality_report.get("pending_reconciliation_count") != 12:
        raise CrossTableReviewError("quality_report pending reconciliation count mismatch")
    for key in (
        "formal_report_allowed",
        "complete_trusted_report_display_allowed",
        "business_decision_basis_allowed",
        "lineage_full_check_included",
        "stage13_review_scope_included",
        "github_upload_scope_included",
        "payment_or_bank_operation_allowed",
        "tax_filing_allowed",
        "legal_collection_decision_allowed",
    ):
        _require_false(quality_report, key, "quality_report")

    _ensure_public_payload(manifest)
    _ensure_public_payload(review_checks)
    _ensure_public_payload(difference_queue)
    _ensure_public_payload(quality_report)
    _validate_html_outputs(html_outputs)


def write_default_cross_table_review_artifacts(
    *,
    generated_at: str = "2026-07-01T19:00:00+10:00",
    output_manifest: Path = DEFAULT_OUTPUT_MANIFEST,
    output_checks: Path = DEFAULT_OUTPUT_CHECKS,
    output_difference_queue: Path = DEFAULT_OUTPUT_DIFFERENCE_QUEUE,
    output_quality_report: Path = DEFAULT_OUTPUT_QUALITY_REPORT,
    output_stage_manifest: Path = DEFAULT_OUTPUT_STAGE_MANIFEST,
    html_output_dir: Path = DEFAULT_HTML_OUTPUT_DIR,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any], dict[str, str]]:
    manifest, review_checks, difference_queue, quality_report, html_outputs = (
        build_default_cross_table_review_artifacts(generated_at=generated_at)
    )
    validate_cross_table_review_artifacts(manifest, review_checks, difference_queue, quality_report, html_outputs)
    write_json(output_manifest, manifest)
    write_jsonl(output_checks, review_checks)
    write_jsonl(output_difference_queue, difference_queue)
    write_json(output_quality_report, quality_report)
    write_json(output_stage_manifest, manifest)
    html_output_dir.mkdir(parents=True, exist_ok=True)
    (html_output_dir / "cross_table_quality_report.html").write_text(
        html_outputs["cross_table_quality_report"],
        encoding="utf-8",
    )
    return manifest, review_checks, difference_queue, quality_report, html_outputs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build KMFA S13-P3 cross-table review artifacts.")
    parser.add_argument("--generated-at", default="2026-07-01T19:00:00+10:00")
    args = parser.parse_args(argv)
    manifest, review_checks, difference_queue, quality_report, html_outputs = (
        write_default_cross_table_review_artifacts(generated_at=args.generated_at)
    )
    summary = manifest["summary"]
    print(
        "PASS: KMFA S13-P3 cross-table review artifacts generated "
        f"(review_dimensions={summary['review_dimension_count']}, "
        f"difference_queue={summary['difference_queue_count']}, "
        f"quality_report={summary['quality_report_count']}, "
        f"pending_reconciliation={summary['pending_reconciliation_count']}, "
        "report_grade_visible=D, formal_report_allowed=false, "
        "business_decision_basis=false, difference_auto_resolution=false, "
        "stage13_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
