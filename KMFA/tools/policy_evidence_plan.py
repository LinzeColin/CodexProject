#!/usr/bin/env python3
"""Build KMFA S14-P3 public-safe policy evidence gap artifacts."""

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

DEFAULT_OUTPUT_MANIFEST = ROOT / "metadata" / "reports" / "policy_evidence_plan_manifest.json"
DEFAULT_OUTPUT_DIRECTORIES = ROOT / "metadata" / "reports" / "policy_evidence_directories.jsonl"
DEFAULT_OUTPUT_GAPS = ROOT / "metadata" / "reports" / "policy_evidence_gaps.jsonl"
DEFAULT_OUTPUT_RISK_TIPS = ROOT / "metadata" / "reports" / "policy_risk_tips.jsonl"
DEFAULT_OUTPUT_STAGE_MANIFEST = ROOT / "stage_artifacts" / "S14_P3_policy_evidence_plan" / "machine" / "s14_p3_manifest.json"
DEFAULT_HTML_OUTPUT_DIR = ROOT / "stage_artifacts" / "S14_P3_policy_evidence_plan" / "exports" / "html"

REQUIRED_POLICY_PROGRAMS = (
    "small_tech_company",
    "high_tech_enterprise",
    "specialized_refined_innovative",
    "little_giant",
    "r_and_d_expense",
)

REQUIRED_EVIDENCE_DIRECTORIES = (
    "evidence_dir_small_tech_company",
    "evidence_dir_high_tech_enterprise",
    "evidence_dir_specialized_refined_innovative",
    "evidence_dir_little_giant",
    "evidence_dir_r_and_d_expense",
)

PROGRAM_LABELS = {
    "small_tech_company": "科小",
    "high_tech_enterprise": "高新",
    "specialized_refined_innovative": "专精特新",
    "little_giant": "小巨人",
    "r_and_d_expense": "研发费用",
}

DIRECTORY_IDS = dict(zip(REQUIRED_POLICY_PROGRAMS, REQUIRED_EVIDENCE_DIRECTORIES))

PROGRAM_EVIDENCE_CATEGORIES = {
    "small_tech_company": (
        "enterprise_basic_qualification",
        "technical_activity_evidence",
        "r_and_d_project_record",
        "personnel_or_team_evidence",
    ),
    "high_tech_enterprise": (
        "intellectual_property_evidence",
        "r_and_d_expense_collection",
        "technology_field_mapping",
        "science_technology_personnel_evidence",
        "high_tech_revenue_evidence",
    ),
    "specialized_refined_innovative": (
        "specialization_evidence",
        "refinement_management_evidence",
        "innovation_output_evidence",
        "industry_chain_position_evidence",
    ),
    "little_giant": (
        "specialized_refined_innovative_basis",
        "market_segment_evidence",
        "innovation_capability_evidence",
        "quality_efficiency_evidence",
        "compliance_and_growth_evidence",
    ),
    "r_and_d_expense": (
        "r_and_d_project_ledger",
        "r_and_d_expense_detail",
        "personnel_time_evidence",
        "invoice_tax_support_evidence",
        "project_outcome_evidence",
    ),
}

PROGRAM_PRIMARY_CATEGORIES = {
    "small_tech_company": ("r_and_d_expense", "tax"),
    "high_tech_enterprise": ("r_and_d_expense", "tax", "invoice"),
    "specialized_refined_innovative": ("operating_analysis", "r_and_d_expense"),
    "little_giant": ("operating_analysis", "r_and_d_expense"),
    "r_and_d_expense": ("r_and_d_expense", "tax", "invoice"),
}

GAP_STATUS = {
    "small_tech_company": "partial_manual_review_required",
    "high_tech_enterprise": "missing_or_unverified",
    "specialized_refined_innovative": "partial_manual_review_required",
    "little_giant": "missing_or_unverified",
    "r_and_d_expense": "partial_manual_review_required",
}

RISK_LEVEL = {
    "small_tech_company": "medium",
    "high_tech_enterprise": "high",
    "specialized_refined_innovative": "medium",
    "little_giant": "high",
    "r_and_d_expense": "high",
}

GAP_LABELS = {
    "small_tech_company": "企业基础、研发活动和人员证据需人工复核",
    "high_tech_enterprise": "知识产权、研发费用、科技人员和高新收入证据链未闭合",
    "specialized_refined_innovative": "专业化、精细化、创新输出和产业链位置材料需补齐",
    "little_giant": "细分市场、创新能力、质量效益和成长合规材料缺口较大",
    "r_and_d_expense": "研发项目台账、费用明细、人员工时和成果证据需要闭环",
}

RISK_TIP_LABELS = {
    "small_tech_company": "避免把结构性证据目录解读为科小资格判断",
    "high_tech_enterprise": "高新准备度不得在证据链未闭合时输出肯定结论",
    "specialized_refined_innovative": "专精特新风险提示只能指向材料缺口和复核动作",
    "little_giant": "小巨人材料要求更高，当前只能提示准备风险",
    "r_and_d_expense": "研发费用证据缺口不得替代税务申报或加计扣除结论",
}

SOURCE_TASKPACK_REFS = {
    "roadmap_s14_p3": "KMFA/taskpack/v1_2/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_2.md:S14-P3",
    "taskpack_business_line": "KMFA/taskpack/v1_2/01_KMFA_Codex_TaskPack_v1_2_完整防遗漏_含HTML验收样板.md:P1-tax-policy",
    "requirement_trace": "KMFA/taskpack/v1_2/04_KMFA_需求追溯矩阵_v1_1.csv:REQ-P1-013",
}

UPSTREAM_METADATA_REFS = {
    "finance_support_source_registry": "KMFA/metadata/imports/finance_support_source_registry.json",
    "finance_field_candidates": "KMFA/metadata/schema_maps/finance_field_candidates.jsonl",
    "scope_reconciliation": "KMFA/metadata/quality/scope_reconciliation_records.jsonl",
    "report_grade_runtime": "KMFA/metadata/reports/report_grade_runtime_records.jsonl",
    "invoice_tax_plan": "KMFA/metadata/reports/invoice_tax_plan_manifest.json",
    "fund_cash_loan_plan": "KMFA/metadata/reports/fund_cash_loan_plan_manifest.json",
}

POLICY_EVIDENCE_PLAN_VERSION = "PLAN-KMFA-S14P3-POLICY-EVIDENCE-PUBLIC-SAFE-001"
FORMULA_VERSION = "FORM-KMFA-S14P3-POLICY-EVIDENCE-GAP-001"
MAPPING_VERSION = "MAP-KMFA-S14P3-PUBLIC-SAFE-v1"
HTML_TEMPLATE_VERSION = "HTML-KMFA-S14P3-BLUE-v1"

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
    "policy_score",
    "eligibility_result",
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


class PolicyEvidencePlanError(ValueError):
    """Raised when S14-P3 policy evidence artifacts are invalid."""


def _sha256_json(payload: Any) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise PolicyEvidencePlanError(f"{path} must contain a JSON object")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            value = json.loads(line)
            if not isinstance(value, dict):
                raise PolicyEvidencePlanError(f"{path} contains a non-object JSONL record")
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
        "policy_application_file_committed": False,
        "tax_filing_file_committed": False,
        "formal_policy_conclusion_committed": False,
        "policy_score_committed": False,
    }


def _stage_scope() -> dict[str, bool]:
    return {
        "s14_p1_scope_reopened": False,
        "s14_p2_scope_reopened": False,
        "s14_p3_policy_evidence_scope_included": True,
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
        "policy_application_submission_scope_included": False,
        "formal_policy_qualification_scope_included": False,
    }


def _quality_gate(*, pending_reconciliation_count: int, report_grade_visible: str) -> dict[str, Any]:
    return {
        "policy_evidence_directory_registration_allowed": True,
        "evidence_gap_signal_allowed": True,
        "risk_tip_allowed": True,
        "formal_report_allowed": False,
        "complete_trusted_report_display_allowed": False,
        "business_decision_basis_allowed": False,
        "policy_qualification_conclusion_allowed": False,
        "policy_application_submission_allowed": False,
        "subsidy_application_allowed": False,
        "tax_filing_allowed": False,
        "tax_declaration_generation_allowed": False,
        "invoice_issuance_allowed": False,
        "invoice_operation_allowed": False,
        "payment_approval_allowed": False,
        "payment_execution_allowed": False,
        "bank_operation_allowed": False,
        "loan_management_action_allowed": False,
        "external_connector_action_allowed": False,
        "report_grade_visible": report_grade_visible,
        "report_grade_bypass_allowed": False,
        "quality_grade_bypass_allowed": False,
        "raw_layer_write_allowed": False,
        "derived_amount_calculation_allowed": False,
        "stage14_review_allowed": False,
        "github_upload_allowed": False,
        "phase_completion_upload_allowed": False,
        "pending_reconciliation_count": pending_reconciliation_count,
        "release_block_reason": "policy_evidence_gap_only_pending_lineage_reconciliation_and_formal_report_gates",
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


def _source_refs_for_program(
    *,
    policy_program: str,
    source_registry_by_category: dict[str, list[dict[str, Any]]],
    field_candidates_by_category: dict[str, list[dict[str, Any]]],
) -> tuple[list[str], list[str], int]:
    source_refs: list[str] = []
    field_keys: list[str] = []
    read_only_flags: list[bool] = []
    for category in PROGRAM_PRIMARY_CATEGORIES[policy_program]:
        for source in source_registry_by_category.get(category, []):
            source_ref = str(source.get("source_ref") or "")
            if source_ref:
                source_refs.append(source_ref)
            read_only_flags.append(source.get("read_only_parse") is True and source.get("raw_layer_write_allowed") is False)
        field_keys.extend(_field_keys(field_candidates_by_category.get(category, [])))
    read_only_count = sum(1 for item in read_only_flags if item)
    return sorted(set(source_refs)), sorted(set(field_keys)), read_only_count


def _directory_record(
    *,
    policy_program: str,
    sequence: int,
    source_registry_by_category: dict[str, list[dict[str, Any]]],
    field_candidates_by_category: dict[str, list[dict[str, Any]]],
    generated_at: str,
) -> dict[str, Any]:
    source_refs, field_keys, read_only_count = _source_refs_for_program(
        policy_program=policy_program,
        source_registry_by_category=source_registry_by_category,
        field_candidates_by_category=field_candidates_by_category,
    )
    return {
        "schema_version": "kmfa.policy_evidence_directory.v1",
        "record_type": "policy_evidence_directory",
        "project_id": "KMFA",
        "stage_phase": "S14-P3",
        "directory_id": DIRECTORY_IDS[policy_program],
        "directory_sequence": sequence,
        "policy_program": policy_program,
        "visible_program_name": PROGRAM_LABELS[policy_program],
        "directory_registered": True,
        "required_evidence_categories": list(PROGRAM_EVIDENCE_CATEGORIES[policy_program]),
        "required_evidence_category_count": len(PROGRAM_EVIDENCE_CATEGORIES[policy_program]),
        "finance_categories": list(PROGRAM_PRIMARY_CATEGORIES[policy_program]),
        "public_source_refs": source_refs,
        "public_field_key_refs": field_keys,
        "readonly_source_count": read_only_count,
        "directory_status": "registered_public_safe_evidence_index_only",
        "evidence_material_storage": "private_authorized_runtime_only_not_committed",
        "evidence_material_values_committed": False,
        "raw_business_values_allowed": False,
        "public_amount_values_allowed": False,
        "field_plaintext_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "formal_policy_conclusion_allowed": False,
        "policy_application_submission_allowed": False,
        "generated_at": generated_at,
    }


def _gap_record(*, policy_program: str, sequence: int, generated_at: str) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.policy_evidence_gap.v1",
        "record_type": "policy_evidence_gap",
        "project_id": "KMFA",
        "stage_phase": "S14-P3",
        "gap_id": f"S14P3-GAP-{sequence:03d}",
        "policy_program": policy_program,
        "visible_program_name": PROGRAM_LABELS[policy_program],
        "gap_status": GAP_STATUS[policy_program],
        "visible_gap_summary": GAP_LABELS[policy_program],
        "required_owner_role": "finance_tax_policy_owner",
        "required_review_action": "provide_or_verify_public_safe_evidence_index",
        "directory_ref": DIRECTORY_IDS[policy_program],
        "evidence_gap_only": True,
        "risk_tip_only": False,
        "eligibility_conclusion_allowed": False,
        "formal_policy_conclusion_allowed": False,
        "policy_score_allowed": False,
        "policy_application_submission_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "raw_business_values_allowed": False,
        "public_amount_values_allowed": False,
        "field_plaintext_allowed": False,
        "generated_at": generated_at,
    }


def _risk_tip_record(*, policy_program: str, sequence: int, generated_at: str) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.policy_risk_tip.v1",
        "record_type": "policy_risk_tip",
        "project_id": "KMFA",
        "stage_phase": "S14-P3",
        "risk_tip_id": f"S14P3-RISK-{sequence:03d}",
        "policy_program": policy_program,
        "visible_program_name": PROGRAM_LABELS[policy_program],
        "risk_level": RISK_LEVEL[policy_program],
        "visible_risk_tip": RISK_TIP_LABELS[policy_program],
        "required_control": "manual_policy_evidence_review_before_any_conclusion",
        "evidence_gap_only": False,
        "risk_tip_only": True,
        "formal_policy_conclusion_allowed": False,
        "policy_qualification_conclusion_allowed": False,
        "policy_application_submission_allowed": False,
        "external_connector_action_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "tax_filing_allowed": False,
        "invoice_issuance_allowed": False,
        "generated_at": generated_at,
    }


def _render_html(
    *,
    manifest: dict[str, Any],
    directories: list[dict[str, Any]],
    gaps: list[dict[str, Any]],
    risk_tips: list[dict[str, Any]],
) -> str:
    grade = html.escape(str(manifest["summary"]["report_grade_visible"]))
    pending_count = int(manifest["summary"]["pending_reconciliation_count"])
    directory_cards = "\n".join(
        f"<li>{html.escape(str(item['visible_program_name']))}<span>{item['required_evidence_category_count']} 类证据目录已登记</span></li>"
        for item in directories
    )
    gap_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(str(item['visible_program_name']))}</td>"
        f"<td>{html.escape(str(item['visible_gap_summary']))}</td>"
        f"<td>{html.escape(str(item['required_review_action']))}</td>"
        "<td>只输出证据缺口和风险提示</td>"
        "</tr>"
        for item in gaps
    )
    risk_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(str(item['visible_program_name']))}</td>"
        f"<td>{html.escape(str(item['risk_level']))}</td>"
        f"<td>{html.escape(str(item['visible_risk_tip']))}</td>"
        "</tr>"
        for item in risk_tips
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>KMFA 政策证据</title>
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
    ul {{ margin:10px 0 0; padding:0; display:grid; grid-template-columns:repeat(5,1fr); gap:10px; list-style:none; }}
    li {{ border:1px solid var(--line); border-radius:8px; padding:12px; background:#fbfdff; font-weight:700; min-height:78px; }}
    li span {{ display:block; color:var(--muted); font-size:13px; font-weight:400; margin-top:5px; }}
    .notice {{ border-left:4px solid var(--warn); background:#fff7ed; padding:12px 14px; line-height:1.65; }}
    @media(max-width:1000px) {{ .cards, ul {{ grid-template-columns:1fr; }} header, main {{ padding-left:16px; padding-right:16px; }} }}
  </style>
</head>
<body>
  <header>
    <div class="brand"><div class="logo">KM</div><div><strong>KMFA 经营分析系统</strong><div class="sub">S14-P3 · 公开安全 · 政策证据</div></div></div>
    <h1>KMFA 政策证据</h1>
    <div class="sub">登记科小、高新、专精特新、小巨人、研发费用五类政策证据目录，只输出证据缺口和风险提示。页面不展示真实材料、金额、税号、人员明细、项目明文或任何申报文件。</div>
  </header>
  <main>
    <section class="cards">
      <div class="card"><div class="label">报告等级</div><div class="num">报告等级 {grade}</div><div class="label">正式政策结论仍被阻断</div></div>
      <div class="card"><div class="label">未关闭差异</div><div class="num stop">{pending_count} 项</div><div class="label">需要 owner 或授权复核</div></div>
      <div class="card"><div class="label">操作边界</div><div class="num stop">只读</div><div class="label">不输出正式政策资格结论</div></div>
    </section>
    <section class="card" style="margin-top:16px">
      <h2>证据目录</h2>
      <ul>
{directory_cards}
      </ul>
    </section>
    <section class="card" style="margin-top:16px">
      <h2>证据缺口</h2>
      <table>
        <thead><tr><th>政策方向</th><th>缺口提示</th><th>复核动作</th><th>边界</th></tr></thead>
        <tbody>
{gap_rows}
        </tbody>
      </table>
    </section>
    <section class="card" style="margin-top:16px">
      <h2>风险提示</h2>
      <table>
        <thead><tr><th>政策方向</th><th>风险等级</th><th>提示</th></tr></thead>
        <tbody>
{risk_rows}
        </tbody>
      </table>
    </section>
    <section class="card" style="margin-top:16px">
      <h2>使用限制</h2>
      <div class="notice">S14-P3 只输出证据缺口和风险提示，不输出正式政策资格结论，不生成申报材料，不调用外部接口，不作为经营决策或税务申报依据。</div>
    </section>
  </main>
</body>
</html>
"""


def _ensure_no_forbidden_public_payload(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in FORBIDDEN_PUBLIC_KEYS:
                raise PolicyEvidencePlanError(f"forbidden public key found: {key}")
            _ensure_no_forbidden_public_payload(item)
    elif isinstance(value, list):
        for item in value:
            _ensure_no_forbidden_public_payload(item)
    elif isinstance(value, str):
        lowered = value.lower()
        if any(suffix in lowered for suffix in FORBIDDEN_PUBLIC_SUFFIXES):
            raise PolicyEvidencePlanError(f"forbidden private business file reference found: {value}")
        if any(text in lowered for text in FORBIDDEN_PUBLIC_TEXT):
            raise PolicyEvidencePlanError(f"forbidden private/raw marker found: {value}")


def build_default_policy_evidence_artifacts(
    *,
    generated_at: str = "2026-07-01T23:30:00+10:00",
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, str]]:
    source_registry = read_json(DEFAULT_FINANCE_SOURCE_REGISTRY)
    field_candidates = read_jsonl(DEFAULT_FINANCE_FIELD_CANDIDATES)
    reconciliation_records = read_jsonl(DEFAULT_SCOPE_RECONCILIATION_RECORDS)
    report_grade_records = read_jsonl(DEFAULT_REPORT_GRADE_RECORDS)

    registry_by_category = _source_registry_by_category(source_registry)
    fields_by_category = _field_candidates_by_category(field_candidates)
    pending_reconciliation_count = _pending_reconciliation_count(reconciliation_records)
    report_grade_visible = _report_grade_visible(report_grade_records)

    directories = [
        _directory_record(
            policy_program=program,
            sequence=index,
            source_registry_by_category=registry_by_category,
            field_candidates_by_category=fields_by_category,
            generated_at=generated_at,
        )
        for index, program in enumerate(REQUIRED_POLICY_PROGRAMS, start=1)
    ]
    gaps = [
        _gap_record(policy_program=program, sequence=index, generated_at=generated_at)
        for index, program in enumerate(REQUIRED_POLICY_PROGRAMS, start=1)
    ]
    risk_tips = [
        _risk_tip_record(policy_program=program, sequence=index, generated_at=generated_at)
        for index, program in enumerate(REQUIRED_POLICY_PROGRAMS, start=1)
    ]

    manifest = {
        "schema_version": "kmfa.policy_evidence_plan_manifest.v1",
        "record_type": "policy_evidence_plan_manifest",
        "project_id": "KMFA",
        "stage_phase": "S14-P3",
        "plan_version": POLICY_EVIDENCE_PLAN_VERSION,
        "formula_version": FORMULA_VERSION,
        "mapping_version": MAPPING_VERSION,
        "html_template_version": HTML_TEMPLATE_VERSION,
        "generated_at": generated_at,
        "runtime_status": "public_safe_policy_evidence_gaps_created_formal_policy_conclusions_blocked",
        "required_policy_programs": list(REQUIRED_POLICY_PROGRAMS),
        "required_evidence_directories": list(REQUIRED_EVIDENCE_DIRECTORIES),
        "source_taskpack_refs": SOURCE_TASKPACK_REFS,
        "upstream_metadata_refs": UPSTREAM_METADATA_REFS,
        "quality_gate": _quality_gate(
            pending_reconciliation_count=pending_reconciliation_count,
            report_grade_visible=report_grade_visible,
        ),
        "stage_scope": _stage_scope(),
        "public_repo_safety": _public_repo_safety(),
        "artifact_refs": {
            "policy_evidence_plan_manifest": "KMFA/metadata/reports/policy_evidence_plan_manifest.json",
            "policy_evidence_directories": "KMFA/metadata/reports/policy_evidence_directories.jsonl",
            "policy_evidence_gaps": "KMFA/metadata/reports/policy_evidence_gaps.jsonl",
            "policy_risk_tips": "KMFA/metadata/reports/policy_risk_tips.jsonl",
            "html_overview": "KMFA/stage_artifacts/S14_P3_policy_evidence_plan/exports/html/policy_evidence_overview.html",
            "validator": "KMFA/tools/check_s14_p3_policy_evidence_plan.py",
            "completion_record": "KMFA/stage_artifacts/S14_P3_policy_evidence_plan/human/s14_p3_completion_record.md",
            "test_results": "KMFA/stage_artifacts/S14_P3_policy_evidence_plan/human/test_results.md",
            "stage_manifest": "KMFA/stage_artifacts/S14_P3_policy_evidence_plan/machine/s14_p3_manifest.json",
        },
        "summary": {
            "policy_program_count": len(REQUIRED_POLICY_PROGRAMS),
            "evidence_directory_count": len(directories),
            "evidence_gap_count": len(gaps),
            "risk_tip_count": len(risk_tips),
            "html_output_count": 1,
            "source_count": len({ref for item in directories for ref in item["public_source_refs"]}),
            "field_mapping_count": len({ref for item in directories for ref in item["public_field_key_refs"]}),
            "pending_reconciliation_count": pending_reconciliation_count,
            "report_grade_visible": report_grade_visible,
            "formal_report_count": 0,
            "formal_policy_conclusion_count": 0,
            "policy_application_submission_count": 0,
            "business_decision_basis_count": 0,
            "external_connector_action_count": 0,
            "tax_filing_count": 0,
            "invoice_issuance_count": 0,
            "payment_or_bank_operation_count": 0,
        },
    }
    manifest["content_hash"] = _sha256_json(
        {
            "directories": directories,
            "gaps": gaps,
            "risk_tips": risk_tips,
            "summary": manifest["summary"],
            "quality_gate": manifest["quality_gate"],
            "stage_scope": manifest["stage_scope"],
        }
    )
    html_outputs = {
        "policy_evidence_overview": _render_html(
            manifest=manifest,
            directories=directories,
            gaps=gaps,
            risk_tips=risk_tips,
        )
    }
    validate_policy_evidence_artifacts(manifest, directories, gaps, risk_tips, html_outputs)
    return manifest, directories, gaps, risk_tips, html_outputs


def validate_policy_evidence_artifacts(
    manifest: dict[str, Any],
    directories: list[dict[str, Any]],
    gaps: list[dict[str, Any]],
    risk_tips: list[dict[str, Any]],
    html_outputs: dict[str, str],
) -> None:
    if manifest.get("stage_phase") != "S14-P3":
        raise PolicyEvidencePlanError("manifest must be scoped to S14-P3")
    if tuple(manifest.get("required_policy_programs", [])) != REQUIRED_POLICY_PROGRAMS:
        raise PolicyEvidencePlanError("manifest must include all required policy programs")
    if tuple(manifest.get("required_evidence_directories", [])) != REQUIRED_EVIDENCE_DIRECTORIES:
        raise PolicyEvidencePlanError("manifest must include all required evidence directories")

    summary = manifest.get("summary", {})
    expected_summary = {
        "policy_program_count": 5,
        "evidence_directory_count": 5,
        "evidence_gap_count": 5,
        "risk_tip_count": 5,
        "html_output_count": 1,
        "pending_reconciliation_count": 12,
        "report_grade_visible": "D",
        "formal_report_count": 0,
        "formal_policy_conclusion_count": 0,
        "policy_application_submission_count": 0,
        "business_decision_basis_count": 0,
        "external_connector_action_count": 0,
        "tax_filing_count": 0,
        "invoice_issuance_count": 0,
        "payment_or_bank_operation_count": 0,
    }
    for key, expected in expected_summary.items():
        if summary.get(key) != expected:
            raise PolicyEvidencePlanError(f"summary {key} must be {expected!r}")

    quality_gate = manifest.get("quality_gate", {})
    required_false_gate = (
        "formal_report_allowed",
        "complete_trusted_report_display_allowed",
        "business_decision_basis_allowed",
        "policy_qualification_conclusion_allowed",
        "policy_application_submission_allowed",
        "subsidy_application_allowed",
        "tax_filing_allowed",
        "tax_declaration_generation_allowed",
        "invoice_issuance_allowed",
        "invoice_operation_allowed",
        "payment_approval_allowed",
        "payment_execution_allowed",
        "bank_operation_allowed",
        "loan_management_action_allowed",
        "external_connector_action_allowed",
        "report_grade_bypass_allowed",
        "quality_grade_bypass_allowed",
        "raw_layer_write_allowed",
        "derived_amount_calculation_allowed",
        "stage14_review_allowed",
        "github_upload_allowed",
        "phase_completion_upload_allowed",
    )
    for key in required_false_gate:
        if quality_gate.get(key) is not False:
            raise PolicyEvidencePlanError(f"quality gate {key} must be false")
    if quality_gate.get("report_grade_visible") != "D":
        raise PolicyEvidencePlanError("quality gate must display report grade D")
    if quality_gate.get("pending_reconciliation_count") != 12:
        raise PolicyEvidencePlanError("quality gate must carry 12 pending reconciliation records")

    stage_scope = manifest.get("stage_scope", {})
    if stage_scope.get("s14_p3_policy_evidence_scope_included") is not True:
        raise PolicyEvidencePlanError("stage scope must include only S14-P3 policy evidence")
    for key, value in stage_scope.items():
        if key != "s14_p3_policy_evidence_scope_included" and value is not False:
            raise PolicyEvidencePlanError(f"stage scope {key} must be false")

    public_safety = manifest.get("public_repo_safety", {})
    for key, value in public_safety.items():
        if value is not False:
            raise PolicyEvidencePlanError(f"public safety {key} must be false")

    if {item.get("policy_program") for item in directories} != set(REQUIRED_POLICY_PROGRAMS):
        raise PolicyEvidencePlanError("directories must cover all policy programs")
    if {item.get("directory_id") for item in directories} != set(REQUIRED_EVIDENCE_DIRECTORIES):
        raise PolicyEvidencePlanError("directories must cover all required directory ids")
    for item in directories:
        if item.get("record_type") != "policy_evidence_directory":
            raise PolicyEvidencePlanError("directory record type mismatch")
        if item.get("stage_phase") != "S14-P3":
            raise PolicyEvidencePlanError("directory must be scoped to S14-P3")
        if item.get("directory_registered") is not True:
            raise PolicyEvidencePlanError("directory must be registered")
        if len(item.get("required_evidence_categories", [])) < 3:
            raise PolicyEvidencePlanError("directory must include evidence categories")
        for key in (
            "raw_business_values_allowed",
            "public_amount_values_allowed",
            "field_plaintext_allowed",
            "formal_report_allowed",
            "business_decision_basis_allowed",
            "formal_policy_conclusion_allowed",
            "policy_application_submission_allowed",
        ):
            if item.get(key) is not False:
                raise PolicyEvidencePlanError(f"directory {item.get('directory_id')} {key} must be false")

    if {item.get("policy_program") for item in gaps} != set(REQUIRED_POLICY_PROGRAMS):
        raise PolicyEvidencePlanError("gaps must cover all policy programs")
    for item in gaps:
        if item.get("record_type") != "policy_evidence_gap":
            raise PolicyEvidencePlanError("gap record type mismatch")
        if item.get("gap_status") not in {"missing_or_unverified", "partial_manual_review_required"}:
            raise PolicyEvidencePlanError("gap status must be a controlled value")
        for key in (
            "eligibility_conclusion_allowed",
            "formal_policy_conclusion_allowed",
            "policy_score_allowed",
            "policy_application_submission_allowed",
            "formal_report_allowed",
            "business_decision_basis_allowed",
            "raw_business_values_allowed",
            "public_amount_values_allowed",
            "field_plaintext_allowed",
        ):
            if item.get(key) is not False:
                raise PolicyEvidencePlanError(f"gap {item.get('gap_id')} {key} must be false")

    if {item.get("policy_program") for item in risk_tips} != set(REQUIRED_POLICY_PROGRAMS):
        raise PolicyEvidencePlanError("risk tips must cover all policy programs")
    for item in risk_tips:
        if item.get("record_type") != "policy_risk_tip":
            raise PolicyEvidencePlanError("risk tip record type mismatch")
        if item.get("risk_level") not in {"medium", "high"}:
            raise PolicyEvidencePlanError("risk level must be controlled")
        for key in (
            "formal_policy_conclusion_allowed",
            "policy_qualification_conclusion_allowed",
            "policy_application_submission_allowed",
            "external_connector_action_allowed",
            "formal_report_allowed",
            "business_decision_basis_allowed",
            "tax_filing_allowed",
            "invoice_issuance_allowed",
        ):
            if item.get(key) is not False:
                raise PolicyEvidencePlanError(f"risk tip {item.get('risk_tip_id')} {key} must be false")

    html_text = html_outputs.get("policy_evidence_overview")
    if not html_text or not html_text.startswith("<!doctype html>"):
        raise PolicyEvidencePlanError("policy evidence HTML overview is missing")
    for required_text in (
        'lang="zh-CN"',
        "KMFA 政策证据",
        "科小",
        "高新",
        "专精特新",
        "小巨人",
        "研发费用",
        "只输出证据缺口和风险提示",
        "不输出正式政策资格结论",
        "报告等级 D",
    ):
        if required_text not in html_text:
            raise PolicyEvidencePlanError(f"HTML overview missing {required_text}")
    lowered_html = html_text.lower()
    for forbidden in ("source_ref://", "private://", "private_ref://", "validator", "manifest", "metadata"):
        if forbidden in lowered_html:
            raise PolicyEvidencePlanError(f"HTML overview contains forbidden technical/private text: {forbidden}")
    for forbidden_suffix in FORBIDDEN_PUBLIC_SUFFIXES:
        if forbidden_suffix in lowered_html:
            raise PolicyEvidencePlanError(f"HTML overview contains forbidden file suffix: {forbidden_suffix}")

    _ensure_no_forbidden_public_payload([manifest, directories, gaps, risk_tips, html_outputs])


def write_policy_evidence_artifacts(
    *,
    manifest_path: Path = DEFAULT_OUTPUT_MANIFEST,
    directories_path: Path = DEFAULT_OUTPUT_DIRECTORIES,
    gaps_path: Path = DEFAULT_OUTPUT_GAPS,
    risk_tips_path: Path = DEFAULT_OUTPUT_RISK_TIPS,
    stage_manifest_path: Path = DEFAULT_OUTPUT_STAGE_MANIFEST,
    html_output_dir: Path = DEFAULT_HTML_OUTPUT_DIR,
    generated_at: str = "2026-07-01T23:30:00+10:00",
) -> dict[str, Any]:
    manifest, directories, gaps, risk_tips, html_outputs = build_default_policy_evidence_artifacts(
        generated_at=generated_at
    )
    write_json(manifest_path, manifest)
    write_jsonl(directories_path, directories)
    write_jsonl(gaps_path, gaps)
    write_jsonl(risk_tips_path, risk_tips)
    html_output_dir.mkdir(parents=True, exist_ok=True)
    (html_output_dir / "policy_evidence_overview.html").write_text(
        html_outputs["policy_evidence_overview"], encoding="utf-8"
    )
    write_json(stage_manifest_path, manifest)
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate KMFA S14-P3 public-safe policy evidence artifacts.")
    parser.add_argument("--generated-at", default="2026-07-01T23:30:00+10:00")
    args = parser.parse_args(argv)
    manifest = write_policy_evidence_artifacts(generated_at=args.generated_at)
    summary = manifest["summary"]
    print(
        "PASS: KMFA S14-P3 policy evidence artifacts generated "
        f"(policy_programs={summary['policy_program_count']}, "
        f"directories={summary['evidence_directory_count']}, "
        f"gaps={summary['evidence_gap_count']}, "
        f"risk_tips={summary['risk_tip_count']}, "
        "report_grade_visible=D, formal_report_allowed=false, "
        "policy_conclusion=false, policy_submission=false, "
        "stage14_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
