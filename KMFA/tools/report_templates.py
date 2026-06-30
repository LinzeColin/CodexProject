#!/usr/bin/env python3
"""Build KMFA S10-P1 public-safe report template metadata."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

DEFAULT_OUTPUT_MANIFEST = ROOT / "metadata" / "reports" / "report_template_manifest.json"
DEFAULT_OUTPUT_TEMPLATES = ROOT / "metadata" / "reports" / "report_templates.jsonl"
DEFAULT_OUTPUT_SECTIONS = ROOT / "metadata" / "reports" / "report_template_sections.jsonl"
DEFAULT_OUTPUT_STAGE_MANIFEST = (
    ROOT / "stage_artifacts" / "S10_P1_report_templates" / "machine" / "s10_p1_manifest.json"
)

REQUIRED_TEMPLATE_IDS = (
    "project_cost_special_report",
    "business_overview_report",
)

REQUIRED_PROJECT_COST_SECTION_TITLES = (
    "经营摘要",
    "项目毛利",
    "成本结构",
    "风险事项",
)

REQUIRED_BUSINESS_OVERVIEW_SECTION_TITLES = (
    "经营总览",
    "收入",
    "开票",
    "回款",
    "现金",
    "项目",
    "税务",
)

HTML_ACCEPTANCE_SAMPLE_REFS = {
    "project_cost_special_report": (
        "KMFA/taskpack/v1_2/20_HTML_UIUX_报告预览/01_核心HTML验收样板/"
        "KMFA_项目成本专题报告预览_v0_6_blue_zero_delta.html"
    ),
    "business_overview_report": (
        "KMFA/taskpack/v1_2/20_HTML_UIUX_报告预览/01_核心HTML验收样板/"
        "KMFA_经营分析报告预览_v3_blue.html"
    ),
}

SOURCE_TASKPACK_REFS = {
    "roadmap_s10_p1": "KMFA/taskpack/v1_2/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_2.md:S10-P1",
    "human_readable_report_spec": "KMFA/taskpack/v1_2/09_KMFA_前端交互与人类可读报告规范_v1_1.md:4",
    "html_acceptance_samples": "KMFA/taskpack/v1_2/20_HTML_UIUX_报告预览/HTML文件索引_v1_2.csv",
}

UPSTREAM_METADATA_REFS = {
    "project_cost_fact_layer": "source_ref://KMFA/S09-P1/project_cost_fact_layer_manifest",
    "margin_cash_margin_layer": "source_ref://KMFA/S09-P2/project_margin_cash_margin_manifest",
    "scope_reconciliation_layer": "source_ref://KMFA/S09-P3/project_scope_reconciliation_manifest",
    "report_release_gate": "source_ref://KMFA/S02-P3/report_release_gate_policy",
    "report_grade_policy": "source_ref://KMFA/S02-P3/report_grade_policy",
}

SECTION_SOURCE_REFS = {
    "经营摘要": (
        "source_ref://KMFA/S09-P3/scope_reconciliation_summary",
        "source_ref://KMFA/S02-P3/report_release_gate_policy",
    ),
    "项目毛利": (
        "source_ref://KMFA/S09-P2/margin_cash_margin_records",
        "source_ref://KMFA/S05-P3/authority_baseline_summary",
    ),
    "成本结构": (
        "source_ref://KMFA/S09-P1/project_cost_fact_records",
        "source_ref://KMFA/S07-P1/finance_support_registry",
    ),
    "风险事项": (
        "source_ref://KMFA/S09-P3/scope_reconciliation_records",
        "source_ref://KMFA/S06-P2/source_difference_queue",
    ),
    "经营总览": (
        "source_ref://KMFA/S09-P1/project_cost_fact_layer_manifest",
        "source_ref://KMFA/S09-P3/scope_reconciliation_summary",
    ),
    "收入": (
        "source_ref://KMFA/S09-P1/revenue_fact_slot",
        "source_ref://KMFA/S05-P3/authority_contract_amount",
    ),
    "开票": (
        "source_ref://KMFA/S09-P1/invoice_fact_slot",
        "source_ref://KMFA/S07-P1/tax_invoice_support",
    ),
    "回款": (
        "source_ref://KMFA/S09-P1/collection_fact_slot",
        "source_ref://KMFA/S07-P2/receivable_aging_support",
    ),
    "现金": (
        "source_ref://KMFA/S09-P2/cash_margin_records",
        "source_ref://KMFA/S07-P1/cash_support_registry",
    ),
    "项目": (
        "source_ref://KMFA/S08-P2/project_entity_model",
        "source_ref://KMFA/S08-P3/entity_matching_quality",
    ),
    "税务": (
        "source_ref://KMFA/S07-P1/tax_support_registry",
        "source_ref://KMFA/S09-P3/invoice_tax_reconciliation_domain",
    ),
}

SECTION_PROMPTS = {
    "经营摘要": "概括本期项目成本表现、已确认依据和仍需管理层关注的限制。",
    "项目毛利": "展示权威口径、系统复算口径和现金口径的管理摘要，并保留差异说明位置。",
    "成本结构": "按人工、材料、机械、分包、运输、差旅、税费、管理费和利息概括成本构成。",
    "风险事项": "列示未关闭差异、待授权确认、数据时效和发布限制。",
    "经营总览": "汇总收入、开票、回款、现金、项目和税务的本期经营态势。",
    "收入": "展示收入确认范围、合同支撑和未满足正式发布条件的限制。",
    "开票": "概括开票进度、开票依据和税务证据的可读状态。",
    "回款": "概括回款进度、应收账龄支撑和时间差异提示。",
    "现金": "概括现金流入、现金毛利和现金口径限制。",
    "项目": "概括项目数量、匹配质量、生命周期状态和人工复核风险。",
    "税务": "概括纳税、发票和政策证据的支持状态。",
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
    "token",
    "api_key",
    "private_key",
}

FORBIDDEN_PUBLIC_SUFFIXES = (".zip", ".xls", ".xlsx", ".pdf", ".sqlite", ".db")
FORBIDDEN_VISIBLE_TEXT_RE = re.compile(
    r"(S\d{2}|S\d+P|validator|manifest|jsonl?|metadata|hash|source_ref|private_ref|schema|"
    r"internal|technical|stage|phase)",
    re.IGNORECASE,
)


class ReportTemplateError(ValueError):
    """Raised when S10-P1 report template artifacts are invalid."""


def _sha256_json(payload: Any) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _public_repo_safety() -> dict[str, bool]:
    return {
        "raw_business_values_committed": False,
        "normalized_business_values_committed": False,
        "field_plaintext_committed": False,
        "raw_file_committed": False,
        "private_tabular_files_committed": False,
    }


def _quality_gate(*, pending_reconciliation_count: int) -> dict[str, Any]:
    return {
        "raw_layer_write_allowed": False,
        "formal_report_allowed": False,
        "report_runtime_scope_included": False,
        "trusted_grade_assignment_allowed": False,
        "s10_p2_report_grade_runtime_allowed": False,
        "s10_p3_export_allowed": False,
        "html_export_allowed": False,
        "csv_excel_export_allowed": False,
        "pdf_export_allowed": False,
        "github_upload_allowed": False,
        "phase_completion_upload_allowed": False,
        "stage10_review_allowed": False,
        "pending_reconciliation_count": pending_reconciliation_count,
        "release_block_reason": "pending_report_grade_runtime_and_unclosed_scope_reconciliations",
    }


def _stage_scope() -> dict[str, bool]:
    return {
        "s10_p1_report_template_scope_included": True,
        "s10_p2_report_grade_scope_included": False,
        "s10_p3_export_scope_included": False,
        "formal_report_runtime_scope_included": False,
        "trusted_report_grade_scope_included": False,
        "lineage_full_check_scope_included": False,
        "ui_scope_included": False,
        "external_connector_scope_included": False,
        "stage10_review_scope_included": False,
    }


def _template_record(
    *,
    template_id: str,
    visible_report_name: str,
    section_titles: tuple[str, ...],
    management_use: str,
    pending_reconciliation_count: int,
    generated_at: str,
) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.report_template.v1",
        "record_type": "report_template",
        "project_id": "KMFA",
        "stage_phase": "S10-P1",
        "template_id": template_id,
        "template_version": "TPL-KMFA-S10P1-REPORT-TEMPLATES-001",
        "generated_at": generated_at,
        "visible_report_name": visible_report_name,
        "management_use": management_use,
        "visible_section_titles": list(section_titles),
        "html_acceptance_sample_ref": HTML_ACCEPTANCE_SAMPLE_REFS[template_id],
        "source_taskpack_refs": SOURCE_TASKPACK_REFS,
        "source_metadata_refs": list(UPSTREAM_METADATA_REFS.values()),
        "quality_gate": _quality_gate(pending_reconciliation_count=pending_reconciliation_count),
        "public_repo_safety": _public_repo_safety(),
        "formal_report_allowed": False,
        "trusted_grade_assignment_allowed": False,
        "report_runtime_scope_included": False,
        "s10_p2_scope_included": False,
        "s10_p3_scope_included": False,
        "ui_scope_included": False,
        "lineage_full_check_included": False,
        "external_connector_included": False,
        "limitations": [
            "本阶段只定义报告模板结构，不判定 A/B/C/D 可信等级。",
            "未关闭差异和缺失运行时等级证据时不得作为正式经营报告发布。",
            "本阶段不生成 HTML、CSV、Excel 或 PDF 导出文件。",
        ],
    }


def _section_record(
    *,
    template_id: str,
    visible_order: int,
    visible_title: str,
    generated_at: str,
) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.report_template_section.v1",
        "record_type": "report_template_section",
        "project_id": "KMFA",
        "stage_phase": "S10-P1",
        "section_id": f"S10P1-{template_id.upper().replace('_', '-')}-{visible_order:02d}",
        "template_id": template_id,
        "visible_order": visible_order,
        "visible_title": visible_title,
        "management_summary_prompt": SECTION_PROMPTS[visible_title],
        "source_metadata_refs": list(SECTION_SOURCE_REFS[visible_title]),
        "raw_business_values_allowed": False,
        "public_numeric_values_allowed": False,
        "internal_technical_title_visible": False,
        "generated_at": generated_at,
    }


def build_default_report_template_artifacts(
    *,
    generated_at: str = "2026-06-30T23:59:45+10:00",
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    pending_reconciliation_count = 12
    templates = [
        _template_record(
            template_id="project_cost_special_report",
            visible_report_name="项目成本专题报告",
            section_titles=REQUIRED_PROJECT_COST_SECTION_TITLES,
            management_use="用于管理层查看项目成本、毛利、成本结构和风险事项的摘要模板。",
            pending_reconciliation_count=pending_reconciliation_count,
            generated_at=generated_at,
        ),
        _template_record(
            template_id="business_overview_report",
            visible_report_name="经营总览报告",
            section_titles=REQUIRED_BUSINESS_OVERVIEW_SECTION_TITLES,
            management_use="用于管理层查看收入、开票、回款、现金、项目和税务的总览模板。",
            pending_reconciliation_count=pending_reconciliation_count,
            generated_at=generated_at,
        ),
    ]

    sections: list[dict[str, Any]] = []
    for template_id, section_titles in (
        ("project_cost_special_report", REQUIRED_PROJECT_COST_SECTION_TITLES),
        ("business_overview_report", REQUIRED_BUSINESS_OVERVIEW_SECTION_TITLES),
    ):
        for visible_order, visible_title in enumerate(section_titles, start=1):
            sections.append(
                _section_record(
                    template_id=template_id,
                    visible_order=visible_order,
                    visible_title=visible_title,
                    generated_at=generated_at,
                )
            )

    manifest = {
        "schema_version": "kmfa.report_template_manifest.v1",
        "record_type": "report_template_manifest",
        "project_id": "KMFA",
        "stage_phase": "S10-P1",
        "template_version": "TPL-KMFA-S10P1-REPORT-TEMPLATES-001",
        "mapping_version": "MAP-KMFA-S10P1-PUBLIC-SAFE-v1",
        "formula_version": "FORM-KMFA-S10P1-REPORT-TEMPLATES-001",
        "generated_at": generated_at,
        "template_status": "public_safe_templates_created_no_formal_report",
        "required_template_ids": list(REQUIRED_TEMPLATE_IDS),
        "required_project_cost_section_titles": list(REQUIRED_PROJECT_COST_SECTION_TITLES),
        "required_business_overview_section_titles": list(REQUIRED_BUSINESS_OVERVIEW_SECTION_TITLES),
        "source_taskpack_refs": SOURCE_TASKPACK_REFS,
        "html_acceptance_sample_refs": HTML_ACCEPTANCE_SAMPLE_REFS,
        "upstream_metadata_refs": UPSTREAM_METADATA_REFS,
        "quality_gate": _quality_gate(pending_reconciliation_count=pending_reconciliation_count),
        "stage_scope": _stage_scope(),
        "public_repo_safety": _public_repo_safety(),
        "artifact_refs": {
            "report_template_manifest": "KMFA/metadata/reports/report_template_manifest.json",
            "report_templates": "KMFA/metadata/reports/report_templates.jsonl",
            "report_template_sections": "KMFA/metadata/reports/report_template_sections.jsonl",
            "validator": "KMFA/tools/check_s10_p1_report_templates.py",
            "completion_record": "KMFA/stage_artifacts/S10_P1_report_templates/human/s10_p1_completion_record.md",
            "test_results": "KMFA/stage_artifacts/S10_P1_report_templates/human/test_results.md",
            "stage_manifest": "KMFA/stage_artifacts/S10_P1_report_templates/machine/s10_p1_manifest.json",
        },
        "summary": {
            "template_count": len(templates),
            "section_count": len(sections),
            "project_cost_section_count": len(REQUIRED_PROJECT_COST_SECTION_TITLES),
            "business_overview_section_count": len(REQUIRED_BUSINESS_OVERVIEW_SECTION_TITLES),
            "pending_reconciliation_count": pending_reconciliation_count,
            "formal_report_count": 0,
            "export_artifact_count": 0,
        },
        "limitations": [
            "S10-P1 只建立模板，不执行 S10-P2 可信等级运行时判定。",
            "S10-P1 不执行 S10-P3 导出，不生成 HTML、CSV、Excel 或 PDF 报告文件。",
            "S09-P3 仍有 12 条待 owner 或授权复核记录，正式报告继续阻断。",
        ],
    }
    manifest["content_hash"] = _sha256_json({"manifest": manifest, "templates": templates, "sections": sections})
    return manifest, templates, sections


def _ensure_no_forbidden_public_payload(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in FORBIDDEN_PUBLIC_KEYS:
                raise ReportTemplateError(f"forbidden public key found: {key}")
            _ensure_no_forbidden_public_payload(item)
    elif isinstance(value, list):
        for item in value:
            _ensure_no_forbidden_public_payload(item)
    elif isinstance(value, str):
        lowered = value.lower()
        if any(lowered.endswith(suffix) or suffix in lowered for suffix in FORBIDDEN_PUBLIC_SUFFIXES):
            raise ReportTemplateError(f"forbidden private business file reference found: {value}")


def _ensure_management_readable_text(label: str, text: str) -> None:
    if not text.strip():
        raise ReportTemplateError(f"{label} is required")
    if FORBIDDEN_VISIBLE_TEXT_RE.search(text):
        raise ReportTemplateError(f"{label} contains an internal technical marker: {text}")


def _validate_template_record(template: dict[str, Any]) -> None:
    template_id = str(template.get("template_id", ""))
    if template_id not in REQUIRED_TEMPLATE_IDS:
        raise ReportTemplateError(f"unexpected template_id: {template_id}")
    _ensure_management_readable_text("visible_report_name", str(template.get("visible_report_name", "")))
    for field_name in (
        "formal_report_allowed",
        "trusted_grade_assignment_allowed",
        "report_runtime_scope_included",
        "s10_p2_scope_included",
        "s10_p3_scope_included",
        "ui_scope_included",
        "lineage_full_check_included",
        "external_connector_included",
    ):
        if template.get(field_name) is not False:
            raise ReportTemplateError(f"{template_id}.{field_name} must be false")

    html_ref = str(template.get("html_acceptance_sample_ref", ""))
    expected_html_ref = HTML_ACCEPTANCE_SAMPLE_REFS[template_id]
    if html_ref != expected_html_ref:
        raise ReportTemplateError(f"{template_id}.html_acceptance_sample_ref mismatch")
    if not (ROOT.parent / html_ref).is_file():
        raise ReportTemplateError(f"missing HTML acceptance sample: {html_ref}")


def _validate_section_records(sections: list[dict[str, Any]]) -> None:
    titles_by_template: dict[str, list[str]] = {template_id: [] for template_id in REQUIRED_TEMPLATE_IDS}
    seen_ids: set[str] = set()
    for section in sections:
        if section.get("record_type") != "report_template_section":
            raise ReportTemplateError("section record_type must be report_template_section")
        section_id = str(section.get("section_id", ""))
        if not section_id or section_id in seen_ids:
            raise ReportTemplateError(f"duplicate or empty section_id: {section_id}")
        seen_ids.add(section_id)
        template_id = str(section.get("template_id", ""))
        if template_id not in titles_by_template:
            raise ReportTemplateError(f"section has unexpected template_id: {template_id}")
        visible_title = str(section.get("visible_title", ""))
        _ensure_management_readable_text("visible_title", visible_title)
        _ensure_management_readable_text(
            "management_summary_prompt",
            str(section.get("management_summary_prompt", "")),
        )
        if section.get("raw_business_values_allowed") is not False:
            raise ReportTemplateError(f"{section_id}.raw_business_values_allowed must be false")
        if section.get("public_numeric_values_allowed") is not False:
            raise ReportTemplateError(f"{section_id}.public_numeric_values_allowed must be false")
        if section.get("internal_technical_title_visible") is not False:
            raise ReportTemplateError(f"{section_id}.internal_technical_title_visible must be false")
        if not section.get("source_metadata_refs"):
            raise ReportTemplateError(f"{section_id}.source_metadata_refs is required")
        titles_by_template[template_id].append(visible_title)

    if tuple(titles_by_template["project_cost_special_report"]) != REQUIRED_PROJECT_COST_SECTION_TITLES:
        raise ReportTemplateError("project cost section titles do not match S10-P1 requirement")
    if tuple(titles_by_template["business_overview_report"]) != REQUIRED_BUSINESS_OVERVIEW_SECTION_TITLES:
        raise ReportTemplateError("business overview section titles do not match S10-P1 requirement")


def validate_report_template_artifacts(
    manifest: dict[str, Any],
    templates: list[dict[str, Any]],
    sections: list[dict[str, Any]],
) -> None:
    if manifest.get("schema_version") != "kmfa.report_template_manifest.v1":
        raise ReportTemplateError("manifest schema_version mismatch")
    if manifest.get("stage_phase") != "S10-P1":
        raise ReportTemplateError("manifest stage_phase must be S10-P1")
    if tuple(manifest.get("required_template_ids", [])) != REQUIRED_TEMPLATE_IDS:
        raise ReportTemplateError("manifest required_template_ids mismatch")
    if len(templates) != len(REQUIRED_TEMPLATE_IDS):
        raise ReportTemplateError("template count mismatch")
    if len(sections) != len(REQUIRED_PROJECT_COST_SECTION_TITLES) + len(REQUIRED_BUSINESS_OVERVIEW_SECTION_TITLES):
        raise ReportTemplateError("section count mismatch")

    summary = manifest.get("summary", {})
    expected_summary = {
        "template_count": 2,
        "section_count": 11,
        "project_cost_section_count": 4,
        "business_overview_section_count": 7,
        "pending_reconciliation_count": 12,
        "formal_report_count": 0,
        "export_artifact_count": 0,
    }
    for key, expected in expected_summary.items():
        if summary.get(key) != expected:
            raise ReportTemplateError(f"manifest summary {key} must be {expected}")

    for scope_key, expected in _stage_scope().items():
        if manifest.get("stage_scope", {}).get(scope_key) is not expected:
            raise ReportTemplateError(f"manifest stage_scope {scope_key} must be {expected}")
    for gate_key, expected in _quality_gate(pending_reconciliation_count=12).items():
        if manifest.get("quality_gate", {}).get(gate_key) != expected:
            raise ReportTemplateError(f"manifest quality_gate {gate_key} must be {expected}")
    for safety_key, expected in _public_repo_safety().items():
        if manifest.get("public_repo_safety", {}).get(safety_key) is not expected:
            raise ReportTemplateError(f"manifest public_repo_safety {safety_key} must be {expected}")

    for template in templates:
        _validate_template_record(template)
    _validate_section_records(sections)
    _ensure_no_forbidden_public_payload({"manifest": manifest, "templates": templates, "sections": sections})


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        value = json.load(f)
    if not isinstance(value, dict):
        raise ReportTemplateError(f"{path} must contain a JSON object")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ReportTemplateError(f"{path} contains a non-object JSONL record")
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


def write_default_report_template_artifacts(
    *,
    output_manifest: Path = DEFAULT_OUTPUT_MANIFEST,
    output_templates: Path = DEFAULT_OUTPUT_TEMPLATES,
    output_sections: Path = DEFAULT_OUTPUT_SECTIONS,
    output_stage_manifest: Path = DEFAULT_OUTPUT_STAGE_MANIFEST,
    generated_at: str = "2026-06-30T23:59:45+10:00",
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    manifest, templates, sections = build_default_report_template_artifacts(generated_at=generated_at)
    validate_report_template_artifacts(manifest, templates, sections)
    _write_json(output_manifest, manifest)
    _write_jsonl(output_templates, templates)
    _write_jsonl(output_sections, sections)
    stage_manifest = {
        "schema_version": "kmfa.s10_p1_stage_manifest.v1",
        "record_type": "s10_p1_report_templates_stage_manifest",
        "project_id": "KMFA",
        "stage_phase": "S10-P1",
        "generated_at": generated_at,
        "status": "completed_validated_local_only",
        "content_hash": manifest["content_hash"],
        "artifact_refs": manifest["artifact_refs"],
        "summary": manifest["summary"],
        "quality_gate": manifest["quality_gate"],
        "stage_scope": manifest["stage_scope"],
        "public_repo_safety": manifest["public_repo_safety"],
    }
    _write_json(output_stage_manifest, stage_manifest)
    return manifest, templates, sections


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build KMFA S10-P1 public-safe report template artifacts.")
    parser.add_argument("--output-manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--output-templates", type=Path, default=DEFAULT_OUTPUT_TEMPLATES)
    parser.add_argument("--output-sections", type=Path, default=DEFAULT_OUTPUT_SECTIONS)
    parser.add_argument("--output-stage-manifest", type=Path, default=DEFAULT_OUTPUT_STAGE_MANIFEST)
    parser.add_argument("--generated-at", default="2026-06-30T23:59:45+10:00")
    args = parser.parse_args(argv)

    manifest, templates, sections = write_default_report_template_artifacts(
        output_manifest=args.output_manifest,
        output_templates=args.output_templates,
        output_sections=args.output_sections,
        output_stage_manifest=args.output_stage_manifest,
        generated_at=args.generated_at,
    )
    summary = manifest["summary"]
    print(
        "PASS: KMFA S10-P1 report template artifacts generated "
        f"(templates={len(templates)}, sections={len(sections)}, "
        f"project_cost_sections={summary['project_cost_section_count']}, "
        f"business_overview_sections={summary['business_overview_section_count']}, "
        "formal_report_allowed=false, s10_p2_scope=false, s10_p3_scope=false, ui_scope=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
