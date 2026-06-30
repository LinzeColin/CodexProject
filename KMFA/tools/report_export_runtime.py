#!/usr/bin/env python3
"""Build KMFA S10-P3 public-safe report export artifacts."""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import sys
from io import StringIO
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

DEFAULT_TEMPLATE_MANIFEST = ROOT / "metadata" / "reports" / "report_template_manifest.json"
DEFAULT_TEMPLATE_RECORDS = ROOT / "metadata" / "reports" / "report_templates.jsonl"
DEFAULT_GRADE_MANIFEST = ROOT / "metadata" / "reports" / "report_grade_runtime_manifest.json"
DEFAULT_GRADE_RECORDS = ROOT / "metadata" / "reports" / "report_grade_runtime_records.jsonl"
DEFAULT_OUTPUT_MANIFEST = ROOT / "metadata" / "reports" / "report_export_manifest.json"
DEFAULT_OUTPUT_RECORDS = ROOT / "metadata" / "reports" / "report_export_records.jsonl"
DEFAULT_OUTPUT_STAGE_MANIFEST = (
    ROOT / "stage_artifacts" / "S10_P3_report_export" / "machine" / "s10_p3_manifest.json"
)
DEFAULT_HTML_OUTPUT_DIR = ROOT / "stage_artifacts" / "S10_P3_report_export" / "exports" / "html"
DEFAULT_CSV_OUTPUT_DIR = ROOT / "stage_artifacts" / "S10_P3_report_export" / "exports" / "csv"

REQUIRED_TEMPLATE_IDS = (
    "project_cost_special_report",
    "business_overview_report",
)

EXPORT_RECORD_VERSION = "RPTEXP-KMFA-S10P3-REPORT-EXPORT-001"
FORMULA_VERSION = "FORM-KMFA-S10P3-REPORT-EXPORT-001"
MAPPING_VERSION = "MAP-KMFA-S10P3-PUBLIC-SAFE-v1"
HTML_TEMPLATE_VERSION = "HTML-KMFA-S10P3-BLUE-v1"
CSV_APPENDIX_SCHEMA_VERSION = "CSV-KMFA-S10P3-APPENDIX-v1"
PDF_EXPORT_POLICY_VERSION = "PDF-KMFA-S10P3-PRIVATE-RUNTIME-v1"

EXPORT_FILE_REFS = {
    "project_cost_special_report": {
        "html": "KMFA/stage_artifacts/S10_P3_report_export/exports/html/project_cost_special_report.html",
        "csv": "KMFA/stage_artifacts/S10_P3_report_export/exports/csv/project_cost_special_report_appendix.csv",
    },
    "business_overview_report": {
        "html": "KMFA/stage_artifacts/S10_P3_report_export/exports/html/business_overview_report.html",
        "csv": "KMFA/stage_artifacts/S10_P3_report_export/exports/csv/business_overview_report_appendix.csv",
    },
}

SOURCE_TASKPACK_REFS = {
    "roadmap_s10_p3": "KMFA/taskpack/v1_2/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_2.md:S10-P3",
    "html_acceptance_inheritance": (
        "KMFA/taskpack/v1_2/00_总索引与补漏复核/"
        "KMFA_HTML_UIUX_报告样板强制继承规范_v1_2.md"
    ),
    "html_acceptance_index": "KMFA/taskpack/v1_2/20_HTML_UIUX_报告预览/HTML文件索引_v1_2.csv",
}

UPSTREAM_METADATA_REFS = {
    "report_template_manifest": "source_ref://KMFA/S10-P1/report_template_manifest",
    "report_grade_runtime_manifest": "source_ref://KMFA/S10-P2/report_grade_runtime_manifest",
    "report_grade_runtime_records": "source_ref://KMFA/S10-P2/report_grade_runtime_records",
    "scope_reconciliation_manifest": "source_ref://KMFA/S09-P3/project_scope_reconciliation_manifest",
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


class ReportExportRuntimeError(ValueError):
    """Raised when S10-P3 report export artifacts are invalid."""


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
        "excel_workbook_committed": False,
        "pdf_file_committed": False,
    }


def _stage_scope() -> dict[str, bool]:
    return {
        "s10_p1_report_template_scope_included": False,
        "s10_p2_report_grade_scope_included": False,
        "s10_p3_export_scope_included": True,
        "report_export_runtime_scope_included": True,
        "formal_report_runtime_scope_included": False,
        "full_trusted_report_scope_included": False,
        "lineage_full_check_scope_included": False,
        "ui_scope_included": False,
        "external_connector_scope_included": False,
        "stage10_review_scope_included": False,
    }


def _quality_gate(*, pending_reconciliation_count: int) -> dict[str, Any]:
    return {
        "raw_layer_write_allowed": False,
        "html_export_allowed": True,
        "csv_excel_export_allowed": True,
        "excel_download_mode": "excel_compatible_csv_no_workbook_committed",
        "pdf_export_allowed": True,
        "pdf_export_mode": "enabled_private_runtime_only_no_public_file_committed",
        "formal_report_allowed": False,
        "complete_trusted_report_display_allowed": False,
        "business_decision_basis_allowed": False,
        "s10_p3_export_allowed": True,
        "github_upload_allowed": False,
        "phase_completion_upload_allowed": False,
        "stage10_review_allowed": False,
        "pending_reconciliation_count": pending_reconciliation_count,
        "release_block_reason": "exports_available_as_public_safe_draft_only_report_grade_d",
    }


def _visible_report_names(template_records: list[dict[str, Any]]) -> dict[str, str]:
    names: dict[str, str] = {}
    for record in template_records:
        template_id = str(record.get("template_id", ""))
        if template_id in REQUIRED_TEMPLATE_IDS:
            names[template_id] = str(record.get("visible_report_name", ""))
    return {
        "project_cost_special_report": names.get("project_cost_special_report") or "项目成本专题报告",
        "business_overview_report": names.get("business_overview_report") or "经营总览报告",
    }


def _grade_records_by_template(grade_records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(record.get("template_id")): record for record in grade_records if record.get("template_id")}


def _render_html(record: dict[str, Any]) -> str:
    report_name = html.escape(str(record["visible_report_name"]))
    report_grade = html.escape(str(record["report_grade"]))
    release_label = "不可作为正式经营决策依据"
    section_labels = record["visible_sections"]
    sections = "\n".join(
        f"<tr><td>{idx}</td><td>{html.escape(title)}</td><td>仅展示公开安全摘要和限制说明</td></tr>"
        for idx, title in enumerate(section_labels, start=1)
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>KMFA {report_name} S10-P3</title>
  <style>
    :root {{ --navy:#0b1f3a; --blue:#1d4ed8; --sky:#eaf3ff; --line:#d8e4f5; --text:#152033; --muted:#64748b; --card:#ffffff; --bad:#b91c1c; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:#f6f9fe; color:var(--text); font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",Arial,sans-serif; }}
    header {{ background:linear-gradient(135deg,var(--navy),#103a72); color:white; padding:28px 34px; }}
    .brand {{ display:flex; gap:14px; align-items:center; margin-bottom:18px; }}
    .logo {{ width:46px; height:46px; border-radius:12px; display:flex; align-items:center; justify-content:center; background:#1d4ed8; font-weight:800; }}
    h1 {{ margin:0 0 8px; font-size:28px; }}
    .sub {{ color:#dbeafe; line-height:1.65; }}
    .wrap {{ max-width:1120px; margin:0 auto; padding:22px; }}
    .grid {{ display:grid; grid-template-columns:repeat(3,1fr); gap:14px; margin-top:-34px; }}
    .card {{ background:var(--card); border:1px solid var(--line); border-radius:8px; padding:18px; box-shadow:0 12px 28px rgba(15,23,42,.08); }}
    .label {{ color:var(--muted); font-size:13px; }}
    .num {{ color:var(--blue); font-size:26px; font-weight:800; margin:6px 0; }}
    .bad {{ color:var(--bad); font-weight:700; }}
    table {{ width:100%; border-collapse:collapse; margin-top:12px; background:white; border:1px solid var(--line); }}
    th,td {{ text-align:left; border-bottom:1px solid var(--line); padding:11px 12px; line-height:1.55; }}
    th {{ background:var(--sky); color:#1e3a8a; }}
    footer {{ color:var(--muted); font-size:12px; padding:18px 22px 28px; }}
  </style>
</head>
<body>
  <header>
    <div class="brand"><div class="logo">KM</div><div><strong>KMFA 经营分析系统</strong><div class="sub">报告导出 · 蓝色商务版 · 公开安全摘要</div></div></div>
    <h1>{report_name}</h1>
    <div class="sub">本导出用于内部复核预览。存在未关闭差异或缺少完整证据时，报告自动降级并保留限制说明。</div>
  </header>
  <main class="wrap">
    <section class="grid">
      <div class="card"><div class="label">报告等级</div><div class="num">报告等级 {report_grade}</div><div class="label">由质量、差异、人工确认和时效门禁决定</div></div>
      <div class="card"><div class="label">发布权限</div><div class="num bad">受限</div><div class="label">{release_label}</div></div>
      <div class="card"><div class="label">导出状态</div><div class="num">HTML / CSV</div><div class="label">Excel 采用兼容 CSV；PDF 仅私有运行时启用</div></div>
    </section>
    <section class="card" style="margin-top:16px">
      <h2>报告内容</h2>
      <table>
        <thead><tr><th>序号</th><th>章节</th><th>导出说明</th></tr></thead>
        <tbody>
{sections}
        </tbody>
      </table>
    </section>
    <section class="card" style="margin-top:16px">
      <h2>限制说明</h2>
      <p>当前导出不包含原始业务明细、字段明文、账号凭证或私有文件。等级为 D 时，完整可信报告、正式报告和经营决策依据均保持阻断。</p>
    </section>
  </main>
  <footer>KMFA 经营分析系统 · S10-P3 导出 · 样张不包含真实经营数据</footer>
</body>
</html>
"""


def _render_csv(record: dict[str, Any]) -> str:
    output = StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "report_id",
            "template_id",
            "visible_report_name",
            "report_grade",
            "release_permission",
            "export_notice",
        ],
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerow(
        {
            "report_id": record["report_export_id"],
            "template_id": record["template_id"],
            "visible_report_name": record["visible_report_name"],
            "report_grade": record["report_grade"],
            "release_permission": record["release_permission"],
            "export_notice": "public-safe draft only; not decision basis",
        }
    )
    return output.getvalue()


def _export_record(
    *,
    template_id: str,
    visible_report_name: str,
    visible_sections: list[str],
    grade_record: dict[str, Any],
    template_manifest: dict[str, Any],
    grade_manifest: dict[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    export_refs = EXPORT_FILE_REFS[template_id]
    return {
        "schema_version": "kmfa.report_export_record.v1",
        "record_type": "report_export_record",
        "project_id": "KMFA",
        "stage_phase": "S10-P3",
        "report_export_id": f"S10P3-EXPORT-{template_id.upper().replace('_', '-')}",
        "report_export_version": EXPORT_RECORD_VERSION,
        "template_id": template_id,
        "visible_report_name": visible_report_name,
        "visible_sections": visible_sections,
        "template_version": str(template_manifest.get("template_version")),
        "template_content_hash": str(template_manifest.get("content_hash")),
        "grade_runtime_content_hash": str(grade_manifest.get("content_hash")),
        "formula_version": FORMULA_VERSION,
        "mapping_version": MAPPING_VERSION,
        "html_template_version": HTML_TEMPLATE_VERSION,
        "csv_appendix_schema_version": CSV_APPENDIX_SCHEMA_VERSION,
        "pdf_export_policy_version": PDF_EXPORT_POLICY_VERSION,
        "generated_at": generated_at,
        "report_grade": str(grade_record.get("computed_report_grade")),
        "release_permission": str(grade_record.get("release_permission")),
        "hard_blocks": list(grade_record.get("hard_blocks", [])),
        "complete_trusted_report_display_allowed": bool(
            grade_record.get("complete_trusted_report_display_allowed")
        ),
        "formal_report_allowed": bool(grade_record.get("formal_report_allowed")),
        "business_decision_basis_allowed": bool(grade_record.get("business_decision_basis_allowed")),
        "export_formats": {
            "html_report": {
                "status": "stable_public_safe",
                "committed_artifact_path": export_refs["html"],
                "inherits_blue_business_sample": True,
            },
            "csv_appendix": {
                "status": "downloadable_public_safe",
                "committed_artifact_path": export_refs["csv"],
            },
            "excel_appendix": {
                "status": "downloadable_public_safe",
                "download_mode": "excel_compatible_csv",
                "download_ref": export_refs["csv"],
                "committed_artifact_path": None,
            },
            "pdf_report": {
                "status": "enabled_private_runtime_only",
                "enabled_after_template_stable": True,
                "private_runtime_only": True,
                "committed_artifact_path": None,
            },
        },
        "source_metadata_refs": list(UPSTREAM_METADATA_REFS.values()),
        "public_repo_safety": _public_repo_safety(),
        "limitations": [
            "HTML 与 CSV 导出只承载公开安全摘要和限制说明。",
            "Excel 下载通过兼容 CSV 实现，公开仓库不提交工作簿文件。",
            "PDF 导出只作为模板稳定后的私有运行时能力，公开仓库不提交 PDF 文件。",
            "报告等级为 D 时，不得作为正式经营报告或经营决策依据。",
        ],
    }


def _load_default_inputs() -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    return (
        read_json(DEFAULT_TEMPLATE_MANIFEST),
        read_jsonl(DEFAULT_TEMPLATE_RECORDS),
        read_json(DEFAULT_GRADE_MANIFEST),
        read_jsonl(DEFAULT_GRADE_RECORDS),
    )


def build_default_report_export_artifacts(
    *,
    generated_at: str = "2026-06-30T23:59:55+10:00",
    template_manifest: dict[str, Any] | None = None,
    template_records: list[dict[str, Any]] | None = None,
    grade_manifest: dict[str, Any] | None = None,
    grade_records: list[dict[str, Any]] | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, dict[str, str]]]:
    if template_manifest is None or template_records is None or grade_manifest is None or grade_records is None:
        loaded_template_manifest, loaded_template_records, loaded_grade_manifest, loaded_grade_records = (
            _load_default_inputs()
        )
        template_manifest = template_manifest or loaded_template_manifest
        template_records = template_records or loaded_template_records
        grade_manifest = grade_manifest or loaded_grade_manifest
        grade_records = grade_records or loaded_grade_records

    visible_names = _visible_report_names(template_records)
    grade_by_template = _grade_records_by_template(grade_records)
    template_sections = {
        "project_cost_special_report": list(template_manifest.get("required_project_cost_section_titles", [])),
        "business_overview_report": list(template_manifest.get("required_business_overview_section_titles", [])),
    }
    pending_reconciliation_count = int(grade_manifest.get("summary", {}).get("pending_reconciliation_count", 0))
    records = [
        _export_record(
            template_id=template_id,
            visible_report_name=visible_names[template_id],
            visible_sections=template_sections[template_id],
            grade_record=grade_by_template[template_id],
            template_manifest=template_manifest,
            grade_manifest=grade_manifest,
            generated_at=generated_at,
        )
        for template_id in REQUIRED_TEMPLATE_IDS
    ]
    render_outputs = {
        "html": {record["template_id"]: _render_html(record) for record in records},
        "csv": {record["template_id"]: _render_csv(record) for record in records},
    }
    grade_distribution: dict[str, int] = {}
    for record in records:
        grade = str(record["report_grade"])
        grade_distribution[grade] = grade_distribution.get(grade, 0) + 1

    manifest = {
        "schema_version": "kmfa.report_export_manifest.v1",
        "record_type": "report_export_manifest",
        "project_id": "KMFA",
        "stage_phase": "S10-P3",
        "runtime_status": "public_safe_exports_generated_formal_report_blocked",
        "report_export_version": EXPORT_RECORD_VERSION,
        "template_version": str(template_manifest.get("template_version")),
        "upstream_template_content_hash": str(template_manifest.get("content_hash")),
        "grade_runtime_content_hash": str(grade_manifest.get("content_hash")),
        "formula_version": FORMULA_VERSION,
        "mapping_version": MAPPING_VERSION,
        "html_template_version": HTML_TEMPLATE_VERSION,
        "csv_appendix_schema_version": CSV_APPENDIX_SCHEMA_VERSION,
        "pdf_export_policy_version": PDF_EXPORT_POLICY_VERSION,
        "generated_at": generated_at,
        "required_template_ids": list(REQUIRED_TEMPLATE_IDS),
        "source_taskpack_refs": SOURCE_TASKPACK_REFS,
        "upstream_metadata_refs": UPSTREAM_METADATA_REFS,
        "quality_gate": _quality_gate(pending_reconciliation_count=pending_reconciliation_count),
        "stage_scope": _stage_scope(),
        "public_repo_safety": _public_repo_safety(),
        "artifact_refs": {
            "report_export_manifest": "KMFA/metadata/reports/report_export_manifest.json",
            "report_export_records": "KMFA/metadata/reports/report_export_records.jsonl",
            "html_exports_dir": "KMFA/stage_artifacts/S10_P3_report_export/exports/html",
            "csv_exports_dir": "KMFA/stage_artifacts/S10_P3_report_export/exports/csv",
            "validator": "KMFA/tools/check_s10_p3_report_export.py",
            "completion_record": "KMFA/stage_artifacts/S10_P3_report_export/human/s10_p3_completion_record.md",
            "test_results": "KMFA/stage_artifacts/S10_P3_report_export/human/test_results.md",
            "stage_manifest": "KMFA/stage_artifacts/S10_P3_report_export/machine/s10_p3_manifest.json",
        },
        "summary": {
            "template_count": len(REQUIRED_TEMPLATE_IDS),
            "report_export_record_count": len(records),
            "grade_distribution": grade_distribution,
            "html_export_count": len(render_outputs["html"]),
            "csv_appendix_count": len(render_outputs["csv"]),
            "excel_compatible_download_count": len(records),
            "pdf_export_enabled_after_template_stable": True,
            "committed_pdf_file_count": 0,
            "committed_excel_file_count": 0,
            "formal_report_count": 0,
            "business_decision_basis_count": 0,
            "pending_reconciliation_count": pending_reconciliation_count,
        },
        "limitations": [
            "S10-P3 只生成 public-safe HTML 和 CSV 附表导出，不关闭报告等级阻断。",
            "Excel 附表下载以兼容 CSV 实现，公开仓库不提交工作簿文件。",
            "PDF 导出在模板稳定后启用为私有运行时策略，公开仓库不提交 PDF 文件。",
            "本阶段不执行 Stage 10 整体复审、UI、lineage full check、外部接口或 GitHub upload。",
        ],
    }
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
                raise ReportExportRuntimeError(f"forbidden public key found: {key}")
            _ensure_no_forbidden_public_payload(item)
    elif isinstance(value, list):
        for item in value:
            _ensure_no_forbidden_public_payload(item)
    elif isinstance(value, str):
        lowered = value.lower()
        if _looks_like_file_reference(value) and any(suffix in lowered for suffix in FORBIDDEN_PUBLIC_SUFFIXES):
            raise ReportExportRuntimeError(f"forbidden private business file reference found: {value}")


def _validate_record(record: dict[str, Any], manifest: dict[str, Any]) -> None:
    template_id = str(record.get("template_id", ""))
    if template_id not in REQUIRED_TEMPLATE_IDS:
        raise ReportExportRuntimeError(f"unexpected template_id: {template_id}")
    if record.get("record_type") != "report_export_record":
        raise ReportExportRuntimeError(f"{template_id}.record_type mismatch")
    for field_name in (
        "report_export_version",
        "template_version",
        "template_content_hash",
        "grade_runtime_content_hash",
        "formula_version",
        "mapping_version",
        "html_template_version",
        "csv_appendix_schema_version",
        "pdf_export_policy_version",
    ):
        if not record.get(field_name):
            raise ReportExportRuntimeError(f"{template_id}.{field_name} is required")
        expected = {
            "template_content_hash": "upstream_template_content_hash",
        }.get(field_name, field_name)
        if record.get(field_name) != manifest.get(expected):
            raise ReportExportRuntimeError(f"{template_id}.{field_name} must match manifest")
    if record.get("report_export_version") != EXPORT_RECORD_VERSION:
        raise ReportExportRuntimeError(f"{template_id}.report_export_version mismatch")
    if record.get("report_grade") != "D":
        raise ReportExportRuntimeError(f"{template_id}.report_grade must remain D")
    if record.get("release_permission") != "blocked_decision_use":
        raise ReportExportRuntimeError(f"{template_id}.release_permission must remain blocked")
    for field_name in (
        "complete_trusted_report_display_allowed",
        "formal_report_allowed",
        "business_decision_basis_allowed",
    ):
        if record.get(field_name) is not False:
            raise ReportExportRuntimeError(f"{template_id}.{field_name} must be false")

    formats = record.get("export_formats", {})
    if formats.get("html_report", {}).get("status") != "stable_public_safe":
        raise ReportExportRuntimeError(f"{template_id}.html_report must be stable_public_safe")
    if formats.get("csv_appendix", {}).get("status") != "downloadable_public_safe":
        raise ReportExportRuntimeError(f"{template_id}.csv_appendix must be downloadable_public_safe")
    if formats.get("excel_appendix", {}).get("download_mode") != "excel_compatible_csv":
        raise ReportExportRuntimeError(f"{template_id}.excel_appendix must use excel_compatible_csv")
    if formats.get("excel_appendix", {}).get("committed_artifact_path") is not None:
        raise ReportExportRuntimeError(f"{template_id}.excel_appendix must not commit workbook artifacts")
    pdf = formats.get("pdf_report", {})
    if pdf.get("enabled_after_template_stable") is not True:
        raise ReportExportRuntimeError(f"{template_id}.pdf_report must be enabled after template stable")
    if pdf.get("private_runtime_only") is not True:
        raise ReportExportRuntimeError(f"{template_id}.pdf_report must be private runtime only")
    if pdf.get("committed_artifact_path") is not None:
        raise ReportExportRuntimeError(f"{template_id}.pdf_report must not commit files")
    for safety_key, expected in _public_repo_safety().items():
        if record.get("public_repo_safety", {}).get(safety_key) is not expected:
            raise ReportExportRuntimeError(f"{template_id}.public_repo_safety {safety_key} must be {expected}")


def _validate_render_outputs(records: list[dict[str, Any]], render_outputs: dict[str, dict[str, str]]) -> None:
    for output_type in ("html", "csv"):
        if set(render_outputs.get(output_type, {})) != set(REQUIRED_TEMPLATE_IDS):
            raise ReportExportRuntimeError(f"render_outputs.{output_type} must cover required templates")
    for record in records:
        template_id = str(record["template_id"])
        html_text = render_outputs["html"][template_id]
        csv_text = render_outputs["csv"][template_id]
        if not html_text.startswith("<!doctype html>"):
            raise ReportExportRuntimeError(f"{template_id} HTML must start with doctype")
        for forbidden_visible in ("source_ref://", "validator", "manifest"):
            if forbidden_visible in html_text.lower():
                raise ReportExportRuntimeError(f"{template_id} HTML exposes internal marker: {forbidden_visible}")
        reader = csv.DictReader(StringIO(csv_text))
        if reader.fieldnames != [
            "report_id",
            "template_id",
            "visible_report_name",
            "report_grade",
            "release_permission",
            "export_notice",
        ]:
            raise ReportExportRuntimeError(f"{template_id} CSV header mismatch")
        rows = list(reader)
        if len(rows) != 1:
            raise ReportExportRuntimeError(f"{template_id} CSV must contain one public-safe summary row")
        if rows[0].get("report_grade") != "D":
            raise ReportExportRuntimeError(f"{template_id} CSV must keep report grade D")


def validate_report_export_artifacts(
    manifest: dict[str, Any],
    records: list[dict[str, Any]],
    render_outputs: dict[str, dict[str, str]],
) -> None:
    if manifest.get("schema_version") != "kmfa.report_export_manifest.v1":
        raise ReportExportRuntimeError("manifest schema_version mismatch")
    if manifest.get("stage_phase") != "S10-P3":
        raise ReportExportRuntimeError("manifest stage_phase must be S10-P3")
    if tuple(manifest.get("required_template_ids", [])) != REQUIRED_TEMPLATE_IDS:
        raise ReportExportRuntimeError("manifest required_template_ids mismatch")
    if len(records) != len(REQUIRED_TEMPLATE_IDS):
        raise ReportExportRuntimeError("report export record count mismatch")

    expected_summary = {
        "template_count": 2,
        "report_export_record_count": 2,
        "grade_distribution": {"D": 2},
        "html_export_count": 2,
        "csv_appendix_count": 2,
        "excel_compatible_download_count": 2,
        "pdf_export_enabled_after_template_stable": True,
        "committed_pdf_file_count": 0,
        "committed_excel_file_count": 0,
        "formal_report_count": 0,
        "business_decision_basis_count": 0,
        "pending_reconciliation_count": 12,
    }
    summary = manifest.get("summary", {})
    for key, expected in expected_summary.items():
        if summary.get(key) != expected:
            raise ReportExportRuntimeError(f"manifest summary {key} must be {expected}")
    for scope_key, expected in _stage_scope().items():
        if manifest.get("stage_scope", {}).get(scope_key) is not expected:
            raise ReportExportRuntimeError(f"manifest stage_scope {scope_key} must be {expected}")
    for gate_key, expected in _quality_gate(pending_reconciliation_count=12).items():
        if manifest.get("quality_gate", {}).get(gate_key) != expected:
            raise ReportExportRuntimeError(f"manifest quality_gate {gate_key} must be {expected}")
    for safety_key, expected in _public_repo_safety().items():
        if manifest.get("public_repo_safety", {}).get(safety_key) is not expected:
            raise ReportExportRuntimeError(f"manifest public_repo_safety {safety_key} must be {expected}")

    seen_template_ids: set[str] = set()
    for record in records:
        template_id = str(record.get("template_id", ""))
        if template_id in seen_template_ids:
            raise ReportExportRuntimeError(f"duplicate template_id: {template_id}")
        seen_template_ids.add(template_id)
        _validate_record(record, manifest)
    if seen_template_ids != set(REQUIRED_TEMPLATE_IDS):
        raise ReportExportRuntimeError("records do not cover all required templates")
    _validate_render_outputs(records, render_outputs)
    _ensure_no_forbidden_public_payload(
        {"manifest": manifest, "records": records, "render_outputs": render_outputs}
    )


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        value = json.load(f)
    if not isinstance(value, dict):
        raise ReportExportRuntimeError(f"{path} must contain a JSON object")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ReportExportRuntimeError(f"{path} contains a non-object JSONL record")
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


def write_default_report_export_artifacts(
    *,
    output_manifest: Path = DEFAULT_OUTPUT_MANIFEST,
    output_records: Path = DEFAULT_OUTPUT_RECORDS,
    output_stage_manifest: Path = DEFAULT_OUTPUT_STAGE_MANIFEST,
    html_output_dir: Path = DEFAULT_HTML_OUTPUT_DIR,
    csv_output_dir: Path = DEFAULT_CSV_OUTPUT_DIR,
    generated_at: str = "2026-06-30T23:59:55+10:00",
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, dict[str, str]]]:
    manifest, records, render_outputs = build_default_report_export_artifacts(generated_at=generated_at)
    validate_report_export_artifacts(manifest, records, render_outputs)
    _write_json(output_manifest, manifest)
    _write_jsonl(output_records, records)
    for template_id, html_text in render_outputs["html"].items():
        _write_text(html_output_dir / f"{template_id}.html", html_text)
    for template_id, csv_text in render_outputs["csv"].items():
        _write_text(csv_output_dir / f"{template_id}_appendix.csv", csv_text)
    stage_manifest = {
        "schema_version": "kmfa.s10_p3_stage_manifest.v1",
        "record_type": "s10_p3_report_export_stage_manifest",
        "project_id": "KMFA",
        "stage_phase": "S10-P3",
        "generated_at": generated_at,
        "status": "completed_validated_local_only_review_pending",
        "content_hash": manifest["content_hash"],
        "artifact_refs": manifest["artifact_refs"],
        "summary": manifest["summary"],
        "quality_gate": manifest["quality_gate"],
        "stage_scope": manifest["stage_scope"],
        "public_repo_safety": manifest["public_repo_safety"],
        "next_gate": "S10_STAGE_REVIEW_REQUIRED_BEFORE_GITHUB_UPLOAD",
    }
    _write_json(output_stage_manifest, stage_manifest)
    return manifest, records, render_outputs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build KMFA S10-P3 public-safe report export artifacts.")
    parser.add_argument("--output-manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--output-records", type=Path, default=DEFAULT_OUTPUT_RECORDS)
    parser.add_argument("--output-stage-manifest", type=Path, default=DEFAULT_OUTPUT_STAGE_MANIFEST)
    parser.add_argument("--html-output-dir", type=Path, default=DEFAULT_HTML_OUTPUT_DIR)
    parser.add_argument("--csv-output-dir", type=Path, default=DEFAULT_CSV_OUTPUT_DIR)
    parser.add_argument("--generated-at", default="2026-06-30T23:59:55+10:00")
    args = parser.parse_args(argv)

    manifest, records, _render_outputs = write_default_report_export_artifacts(
        output_manifest=args.output_manifest,
        output_records=args.output_records,
        output_stage_manifest=args.output_stage_manifest,
        html_output_dir=args.html_output_dir,
        csv_output_dir=args.csv_output_dir,
        generated_at=args.generated_at,
    )
    summary = manifest["summary"]
    print(
        "PASS: KMFA S10-P3 report export artifacts generated "
        f"(export_records={len(records)}, html_exports={summary['html_export_count']}, "
        f"csv_appendices={summary['csv_appendix_count']}, "
        f"excel_compatible_downloads={summary['excel_compatible_download_count']}, "
        "pdf_private_runtime_enabled=true, committed_pdf_files=0, committed_excel_files=0, "
        "stage10_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
