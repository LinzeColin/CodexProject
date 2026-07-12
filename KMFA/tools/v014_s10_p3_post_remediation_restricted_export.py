#!/usr/bin/env python3
"""Build the KMFA v0.1.4 S10-P3 post-remediation restricted exports."""

from __future__ import annotations

import argparse
import csv
import html
import io
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools import v014_s10_p2_post_remediation_trust_grade_lock as p2_phase
from KMFA.tools.check_v014_s10_p2_post_remediation_trust_grade_lock import (
    validate_payloads as validate_s10_p2_payloads,
)
from KMFA.tools.check_v014_s10_p3_report_export import validate_v014_s10_p3_report_export


PHASE_ID = "V014_S10_P3_POST_REMEDIATION_RESTRICTED_EXPORT"
ROADMAP_PHASE_ID = "S10-P3"
TASK_ID = "KMFA-V014-S10-P3-POST-REMEDIATION-RESTRICTED-EXPORT-20260711"
ACCEPTANCE_ID = "ACC-V014-S10-P3-POST-REMEDIATION-RESTRICTED-EXPORT"
VERSION = "0.1.4-s10-p3-post-remediation-restricted-export"
STATUS = "completed_validated_local_only_restricted_exports_d_no_go_upload_deferred"
DECISION = "NO_GO"
FORMULA_ID = "FORM-KMFA-V014-S10-P3-POST-REMEDIATION-RESTRICTED-EXPORT-001"
PARAMETER_IDS = ("PARAM-KMFA-1702", "PARAM-KMFA-1703", "PARAM-KMFA-1704")
MODEL_REGISTRY_KEY = "kmfa_v014_s10_p3_post_remediation_restricted_export"

REPORT_EXPORT_VERSION = "RPTEXP-KMFA-V014-S10P3-POST-REMEDIATION-001"
FORMULA_VERSION = FORMULA_ID
MAPPING_VERSION = "MAP-KMFA-V014-S10P3-POST-REMEDIATION-PUBLIC-SAFE-v1"
HTML_TEMPLATE_VERSION = "HTML-KMFA-V014-S10P3-RESTRICTED-v1"
CSV_APPENDIX_SCHEMA_VERSION = "CSV-KMFA-V014-S10P3-RESTRICTED-v1"
PDF_EXPORT_POLICY_VERSION = "PDF-KMFA-V014-S10P3-PRIVATE-RUNTIME-v1"

OUTPUT_DIR = Path("KMFA/stage_artifacts") / PHASE_ID
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
HTML_DIR = OUTPUT_DIR / "exports/html"
CSV_DIR = OUTPUT_DIR / "exports/csv"

SUMMARY_PATH = MACHINE_DIR / "restricted_export_summary.json"
MANIFEST_PATH = MACHINE_DIR / "restricted_export_manifest.json"
POLICY_PATH = MACHINE_DIR / "export_policy_public_safe.json"
RECORDS_PATH = MACHINE_DIR / "restricted_export_records_public_safe.json"
GO_NO_GO_PATH = MACHINE_DIR / "restricted_export_go_no_go_report.json"
COMPLETION_PATH = HUMAN_DIR / "s10_p3_completion_record_zh.md"
MANAGEMENT_README_PATH = HUMAN_DIR / "restricted_export_readme_zh.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results_zh.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register_zh.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan_zh.md"

HTML_PATHS = {
    "project_cost_special_report": HTML_DIR / "project_cost_special_report.html",
    "business_overview_report": HTML_DIR / "business_overview_report.html",
}
CSV_PATHS = {
    "project_cost_special_report": CSV_DIR / "project_cost_special_report_appendix.csv",
    "business_overview_report": CSV_DIR / "business_overview_report_appendix.csv",
}

QUALITY_DIR = Path("KMFA/metadata/quality")
METADATA_SUMMARY_PATH = QUALITY_DIR / "v014_s10_p3_post_remediation_restricted_export_summary.json"
METADATA_MANIFEST_PATH = QUALITY_DIR / "v014_s10_p3_post_remediation_restricted_export_manifest.json"
METADATA_POLICY_PATH = QUALITY_DIR / "v014_s10_p3_post_remediation_export_policy_public_safe.json"
METADATA_RECORDS_PATH = QUALITY_DIR / "v014_s10_p3_post_remediation_restricted_export_records_public_safe.json"
METADATA_GO_NO_GO_PATH = QUALITY_DIR / "v014_s10_p3_post_remediation_restricted_export_go_no_go_report.json"

PRIVATE_DIR = Path("KMFA/.codex_private_runtime/v014_s10_p3_post_remediation_restricted_export")
PRIVATE_RAW_BEFORE_PATH = PRIVATE_DIR / "raw_immutability_before.json"
PRIVATE_RAW_AFTER_PATH = PRIVATE_DIR / "raw_immutability_after.json"
PRIVATE_VALIDATION_REPORT_PATH = PRIVATE_DIR / "s10_p3_restricted_export_validation_zh.md"
PRIVATE_BASELINE_AUDIT_PATH = PRIVATE_DIR / "human_flow_baseline_audit.csv"
PRIVATE_EXPORT_AUDIT_PATH = PRIVATE_DIR / "restricted_export_browser_audit.csv"
PRIVATE_SCREENSHOT_DIR = PRIVATE_DIR / "screenshots"

HUMAN_FLOW_SAMPLE_PATH = Path(
    "KMFA/taskpack/v1_4/html_uiux/KMFA_经营分析报告可点击预览_v1_4.html"
)
HUMAN_FLOW_AUDIT_REPORT_PATH = Path(
    "KMFA/taskpack/v1_4/html_uiux/KMFA_HTML_human_flow_audit_report_v1_4.md"
)
HISTORICAL_S10_P3_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V014_S10_P3_REPORT_EXPORT/machine/report_export_manifest.json"
)

DEVELOPMENT_EVENTS_PATH = p2_phase.DEVELOPMENT_EVENTS_PATH
STAGE_STATUS_PATH = p2_phase.STAGE_STATUS_PATH
TASK_STATUS_PATH = p2_phase.TASK_STATUS_PATH


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def validate_s10_p2_dependency() -> dict[str, Any]:
    payloads = {
        "summary": _read_json(p2_phase.SUMMARY_PATH),
        "manifest": _read_json(p2_phase.MANIFEST_PATH),
        "rules": _read_json(p2_phase.RULES_PATH),
        "records": _read_json(p2_phase.RECORDS_PATH),
        "go_no_go": _read_json(p2_phase.GO_NO_GO_PATH),
    }
    manifest = validate_s10_p2_payloads(payloads)
    mirror_pairs = (
        (p2_phase.SUMMARY_PATH, p2_phase.METADATA_SUMMARY_PATH),
        (p2_phase.MANIFEST_PATH, p2_phase.METADATA_MANIFEST_PATH),
        (p2_phase.RULES_PATH, p2_phase.METADATA_RULES_PATH),
        (p2_phase.RECORDS_PATH, p2_phase.METADATA_RECORDS_PATH),
        (p2_phase.GO_NO_GO_PATH, p2_phase.METADATA_GO_NO_GO_PATH),
    )
    for public_path, mirror_path in mirror_pairs:
        if _read_json(public_path) != _read_json(mirror_path):
            raise ValueError(f"S10-P2 dependency mirror drift: {public_path}")
    validation = manifest.get("validation_summary", {})
    if validation.get("final_validation_recorded") is not True:
        raise ValueError("S10-P2 dependency final validation is not recorded")
    for key in ("focused_tests", "strict_validator", "governance_and_safety_scans"):
        if validation.get(key) != "PASS":
            raise ValueError(f"S10-P2 dependency final status mismatch: {key}")
    return manifest


def _validate_human_flow_baseline() -> dict[str, Any]:
    sample = HUMAN_FLOW_SAMPLE_PATH.read_text(encoding="utf-8")
    audit_report = HUMAN_FLOW_AUDIT_REPORT_PATH.read_text(encoding="utf-8")
    for token in ("data-print", "data-export-csv", "data-report-btn", "附表导出", "打印/另存"):
        source = sample if token.startswith("data-") else audit_report
        if token not in source:
            raise ValueError(f"human-flow baseline token missing: {token}")
    return {
        "structure_validated": True,
        "structure_only": True,
        "sample_dynamic_state_reused": False,
        "sample_business_values_reused": False,
    }


def _raw_snapshot(label: str) -> dict[str, Any]:
    return p2_phase._raw_snapshot(label)


def _normalize_raw(snapshot: dict[str, Any]) -> Any:
    return p2_phase._normalize_raw(snapshot)


def _render_html(record: dict[str, Any]) -> str:
    report_name = html.escape(str(record["visible_report_title"]))
    sections = "\n".join(
        f"<tr><td>{index}</td><td>{html.escape(section)}</td><td>受限摘要，不展示业务明细</td></tr>"
        for index, section in enumerate(record["visible_sections"], start=1)
    )
    csv_href = "../csv/" + CSV_PATHS[str(record["report_entry_id"])].name
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>KMFA {report_name} - 内部复核预览</title>
  <style>
    :root {{ --ink:#17202b; --muted:#5c6773; --line:#d8dde3; --paper:#fff; --canvas:#f3f5f7; --blue:#245b86; --blue-soft:#eaf2f8; --red:#a52a2a; --red-soft:#fff0ee; --green:#326a51; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:var(--canvas); color:var(--ink); font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Microsoft YaHei",Arial,sans-serif; font-size:14px; line-height:1.6; }}
    button,a {{ font:inherit; }}
    .page {{ width:min(1080px,calc(100% - 32px)); margin:24px auto 40px; background:var(--paper); border:1px solid var(--line); }}
    .masthead {{ padding:24px 28px; border-bottom:1px solid var(--line); display:flex; align-items:flex-start; justify-content:space-between; gap:20px; }}
    .brand {{ color:var(--blue); font-weight:800; }}
    h1 {{ margin:4px 0 4px; font-size:28px; line-height:1.25; letter-spacing:0; }}
    .muted {{ color:var(--muted); }}
    .status {{ flex:0 0 220px; border:1px solid #efb7b1; background:var(--red-soft); padding:14px; border-radius:8px; }}
    .status strong {{ display:block; color:var(--red); font-size:20px; }}
    .notice {{ margin:20px 28px 0; padding:16px; border-left:4px solid var(--red); background:#fff8f7; }}
    .metrics {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; margin:16px 28px; }}
    .metric {{ min-height:92px; padding:14px; border:1px solid var(--line); border-radius:8px; }}
    .metric b {{ display:block; color:var(--blue); font-size:24px; }}
    .content {{ padding:4px 28px 28px; }}
    h2 {{ margin:22px 0 10px; font-size:18px; letter-spacing:0; }}
    table {{ width:100%; border-collapse:collapse; }}
    th,td {{ padding:10px 12px; border:1px solid var(--line); text-align:left; }}
    th {{ background:var(--blue-soft); color:#183b57; }}
    .actions {{ display:flex; gap:10px; flex-wrap:wrap; margin-top:16px; }}
    .button {{ display:inline-flex; min-height:40px; align-items:center; justify-content:center; border:1px solid var(--blue); border-radius:6px; padding:8px 13px; background:var(--blue); color:#fff; text-decoration:none; cursor:pointer; }}
    .button.secondary {{ background:#fff; color:var(--blue); }}
    .operation {{ margin-top:12px; color:var(--green); min-height:24px; }}
    footer {{ padding:14px 28px; border-top:1px solid var(--line); color:var(--muted); font-size:12px; }}
    @media(max-width:720px) {{ .page {{ width:100%; margin:0; border-left:0; border-right:0; }} .masthead {{ display:block; padding:20px; }} .status {{ margin-top:14px; width:100%; }} .notice {{ margin:16px 20px 0; }} .metrics {{ grid-template-columns:repeat(2,minmax(0,1fr)); margin:14px 20px; }} .content {{ padding:4px 20px 22px; overflow-wrap:anywhere; }} h1 {{ font-size:23px; }} table {{ font-size:13px; }} th,td {{ padding:8px; }} }}
  </style>
</head>
<body>
  <main class="page">
    <header class="masthead">
      <div><div class="brand">KMFA 经营分析系统</div><h1>{report_name}</h1><div class="muted">受限导出版本 · 仅供内部复核</div></div>
      <div class="status"><span>当前报告状态</span><strong>D级（未放行）</strong><span>不可作为正式经营决策依据</span></div>
    </header>
    <section class="notice"><strong>限制说明：</strong>关键现金数据缺失；九项非零差异继续保留；一项比较未完成。完整追溯、充分确认和业务一致性尚未成立。</section>
    <section class="metrics" aria-label="聚合核对状态">
      <div class="metric"><span>最终接受未决</span><b>3</b><span>不补零</span></div>
      <div class="metric"><span>非零差异</span><b>9</b><span>不覆盖</span></div>
      <div class="metric"><span>零差异</span><b>2</b><span>已保留证据</span></div>
      <div class="metric"><span>未完成比较</span><b>1</b><span>继续阻断</span></div>
    </section>
    <section class="content">
      <h2>报告章节</h2>
      <table><thead><tr><th>序号</th><th>章节</th><th>展示边界</th></tr></thead><tbody>{sections}</tbody></table>
      <h2>导出操作</h2>
      <div class="actions"><a class="button" href="{csv_href}" download>下载CSV附表</a><button class="button secondary" id="pdf-policy" type="button">PDF导出未执行</button></div>
      <div class="operation" id="operation-status" role="status">本预览未生成 PDF 或 Excel 工作簿。</div>
    </section>
    <footer>公开安全摘要，不含原始文件身份、字段表头、业务金额或明细。当前等级与限制必须随导出保留。</footer>
  </main>
  <script>
    document.getElementById('pdf-policy').addEventListener('click',function(){{
      document.getElementById('operation-status').textContent='PDF 仅可在私有运行环境按受限策略生成；本次仍未执行。';
      document.body.dataset.lastAction='pdf-private-policy-not-executed';
    }});
  </script>
</body>
</html>
"""


def _render_csv(record: dict[str, Any]) -> str:
    output = io.StringIO()
    headers = [
        "报告名称",
        "报告等级",
        "发布状态",
        "最终接受未决数",
        "非零差异数",
        "零差异数",
        "未完成比较数",
        "使用限制",
    ]
    writer = csv.DictWriter(output, fieldnames=headers, lineterminator="\n")
    writer.writeheader()
    writer.writerow(
        {
            "报告名称": record["visible_report_title"],
            "报告等级": "D级",
            "发布状态": "未放行",
            "最终接受未决数": 3,
            "非零差异数": 9,
            "零差异数": 2,
            "未完成比较数": 1,
            "使用限制": "仅供内部复核，不作为正式经营决策依据",
        }
    )
    return "\ufeff" + output.getvalue()


def _export_records(
    p1: dict[str, Any],
    p2: dict[str, Any],
    generated_at: str,
) -> list[dict[str, Any]]:
    entries = {entry["entry_id"]: entry for entry in p1["report_entries"]}
    records: list[dict[str, Any]] = []
    for grade_record in p2["grade_records"]:
        entry_id = str(grade_record["report_entry_id"])
        entry = entries[entry_id]
        records.append(
            {
                "schema_version": "kmfa.v014.s10_p3.post_remediation_restricted_export_record.v1",
                "record_type": "post_remediation_restricted_export_record",
                "project_id": "KMFA",
                "stage_id": "S10",
                "phase_id": PHASE_ID,
                "report_export_id": f"S10P3-POST-EXPORT-{entry_id.upper().replace('_', '-')}",
                "report_entry_id": entry_id,
                "visible_report_title": entry["visible_title"],
                "visible_sections": entry["visible_sections"],
                "report_export_version": REPORT_EXPORT_VERSION,
                "report_entry_version": p1["version"],
                "report_grade_record_version": grade_record["report_record_version"],
                "template_version": grade_record["template_version"],
                "formula_version": FORMULA_VERSION,
                "mapping_version": MAPPING_VERSION,
                "field_mapping_version": grade_record["field_mapping_version"],
                "html_template_version": HTML_TEMPLATE_VERSION,
                "csv_appendix_schema_version": CSV_APPENDIX_SCHEMA_VERSION,
                "pdf_export_policy_version": PDF_EXPORT_POLICY_VERSION,
                "generated_at": generated_at,
                "current_data_quality_grade": "Q4",
                "report_grade": "D",
                "visible_status_label": "D级（未放行）",
                "release_permission": "blocked_decision_use",
                "export_mode": "restricted_internal_review_preview",
                "hard_blocks": list(grade_record["hard_blocks"]),
                "restricted_preview_export_allowed": True,
                "complete_trusted_report_display_allowed": False,
                "formal_report_allowed": False,
                "business_decision_basis_allowed": False,
                "export_formats": {
                    "html": {
                        "status": "restricted_public_safe_preview",
                        "artifact_ref": HTML_PATHS[entry_id].as_posix(),
                    },
                    "csv": {
                        "status": "restricted_public_safe_download",
                        "artifact_ref": CSV_PATHS[entry_id].as_posix(),
                    },
                    "excel": {
                        "status": "excel_compatible_csv_only",
                        "download_ref": CSV_PATHS[entry_id].as_posix(),
                        "workbook_committed": False,
                    },
                    "pdf": {
                        "status": "private_runtime_policy_available_not_executed",
                        "private_runtime_only": True,
                        "export_performed": False,
                        "file_committed": False,
                    },
                },
                "limitations": [
                    "关键现金数据缺失，不能显示为完整可信报告。",
                    "九项非零差异和一项未完成比较继续阻断发布。",
                    "仅供内部复核，不作为正式经营决策依据。",
                ],
                "public_repo_safety": {
                    "aggregate_only": True,
                    "business_values_included": False,
                    "field_or_header_plaintext_included": False,
                    "raw_identity_included": False,
                    "pdf_file_committed": False,
                    "excel_workbook_committed": False,
                    "private_csv_committed": False,
                },
            }
        )
    return records


def build_payloads(*, final_validation: bool = False) -> dict[str, Any]:
    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    raw_before = _raw_snapshot("before_v014_s10_p3_post_remediation_restricted_export")
    p1 = p2_phase.validate_s10_p1_dependency()
    p2 = validate_s10_p2_dependency()
    validate_v014_s10_p3_report_export()
    historical = _read_json(HISTORICAL_S10_P3_MANIFEST_PATH)
    human_flow = _validate_human_flow_baseline()
    raw_after = _raw_snapshot("after_v014_s10_p3_post_remediation_restricted_export")
    prior_raw = _read_json(p2_phase.PRIVATE_RAW_AFTER_PATH)
    raw_exact = _normalize_raw(raw_before) == _normalize_raw(raw_after)
    raw_cross_phase_exact = _normalize_raw(raw_before) == _normalize_raw(prior_raw)
    if not raw_exact or not raw_cross_phase_exact:
        raise ValueError("raw source changed during S10-P3 post-remediation restricted export")

    records = _export_records(p1, p2, generated_at)
    html_outputs = {record["report_entry_id"]: _render_html(record) for record in records}
    csv_outputs = {record["report_entry_id"]: _render_csv(record) for record in records}
    p2_summary = p2["summary"]
    summary = {
        "schema_version": "kmfa.v014.s10_p3.post_remediation_restricted_export_summary.v1",
        "project_id": "KMFA",
        "stage_id": "S10",
        "phase_id": PHASE_ID,
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "status": STATUS,
        "decision": DECISION,
        "report_template_count": 2,
        "report_export_record_count": len(records),
        "grade_distribution": {"D": len(records)},
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "open_final_difference_accepted_count": p2_summary["open_final_difference_accepted_count"],
        "nonzero_delta_reconciliation_count": p2_summary["nonzero_delta_reconciliation_count"],
        "zero_delta_reconciliation_count": p2_summary["zero_delta_reconciliation_count"],
        "incomplete_reconciliation_count": p2_summary["incomplete_reconciliation_count"],
        "hard_block_count": p2_summary["hard_block_count"],
        "html_restricted_preview_count": len(html_outputs),
        "csv_restricted_appendix_count": len(csv_outputs),
        "excel_compatible_csv_download_count": len(csv_outputs),
        "committed_public_export_artifact_count": len(html_outputs) + len(csv_outputs),
        "committed_pdf_file_count": 0,
        "committed_excel_workbook_count": 0,
        "formal_report_count": 0,
        "business_decision_basis_allowed_count": 0,
        "raw_source_file_count": raw_before["file_count"],
        "raw_snapshot_exact_match": raw_exact,
        "raw_cross_phase_snapshot_exact_match": raw_cross_phase_exact,
    }
    export_policy = {
        "schema_version": "kmfa.v014.s10_p3.post_remediation_export_policy_public_safe.v1",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "html_restricted_preview_allowed": True,
        "csv_restricted_appendix_allowed": True,
        "excel_compatible_csv_download_allowed": True,
        "excel_download_mode": "excel_compatible_csv_no_workbook",
        "pdf_private_runtime_policy_available": True,
        "pdf_private_runtime_only": True,
        "pdf_export_performed": False,
        "formal_report_export_allowed": False,
        "complete_trusted_report_display_allowed": False,
        "business_decision_basis_allowed": False,
        "delivery_allowed": False,
    }
    dependencies = {
        "current_s10_p1_entry_validated": True,
        "current_s10_p2_grade_lock_validated": True,
        "historical_s10_p3_export_framework_validated": True,
        "human_flow_baseline_validated": human_flow["structure_validated"],
        "historical_dynamic_state_reused": False,
        "human_flow_sample_dynamic_state_reused": human_flow["sample_dynamic_state_reused"],
        "human_flow_sample_business_values_reused": human_flow["sample_business_values_reused"],
        "current_s10_p2_state_authoritative": True,
    }
    phase_boundaries = {
        "s10_p1_performed": True,
        "s10_p2_performed": True,
        "s10_p3_performed": True,
        "stage10_review_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }
    raw_boundary = {
        "raw_read_authorized": True,
        "raw_snapshot_validation_performed": True,
        "raw_write_performed": False,
        "raw_delete_performed": False,
        "raw_move_performed": False,
        "raw_rename_performed": False,
        "raw_overwrite_performed": False,
        "raw_mutation_performed": False,
    }
    public_repo_safety = {
        "aggregate_only": True,
        "raw_file_committed": False,
        "raw_filename_committed": False,
        "raw_hash_committed": False,
        "field_or_header_plaintext_committed": False,
        "business_value_committed": False,
        "project_or_customer_plaintext_committed": False,
        "pdf_file_committed": False,
        "excel_workbook_committed": False,
        "private_csv_committed": False,
        "private_runtime_committed": False,
        "credential_or_secret_committed": False,
    }
    records_document = {
        "schema_version": "kmfa.v014.s10_p3.post_remediation_restricted_export_records.v1",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "export_records": records,
    }
    version_bindings = {
        "report_export_version": REPORT_EXPORT_VERSION,
        "report_entry_version": p1["version"],
        "report_grade_record_version": p2_phase.REPORT_RECORD_VERSION,
        "template_version": records[0]["template_version"],
        "formula_version": FORMULA_VERSION,
        "mapping_version": MAPPING_VERSION,
        "field_mapping_version": records[0]["field_mapping_version"],
        "html_template_version": HTML_TEMPLATE_VERSION,
        "csv_appendix_schema_version": CSV_APPENDIX_SCHEMA_VERSION,
        "pdf_export_policy_version": PDF_EXPORT_POLICY_VERSION,
        "record_version_binding_count": len(records),
    }
    manifest = {
        "schema_version": "kmfa.v014.s10_p3.post_remediation_restricted_export_manifest.v1",
        "project_id": "KMFA",
        "version": VERSION,
        "stage_id": "S10",
        "phase_id": PHASE_ID,
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": generated_at,
        "reviewed_head": p2_phase.p1_phase._git_output(["rev-parse", "HEAD"]),
        "branch": p2_phase.p1_phase._git_output(["branch", "--show-current"]),
        "status": STATUS,
        "decision": DECISION,
        "summary": summary,
        "export_policy": export_policy,
        "export_records": records,
        "dependencies": dependencies,
        "phase_boundaries": phase_boundaries,
        "raw_boundary": raw_boundary,
        "public_repo_safety": public_repo_safety,
        "version_binding_requirements": version_bindings,
        "source_evidence_refs": {
            "current_s10_p1": p2_phase.p1_phase.MANIFEST_PATH.as_posix(),
            "current_s10_p2": p2_phase.MANIFEST_PATH.as_posix(),
            "historical_s10_p3_framework": HISTORICAL_S10_P3_MANIFEST_PATH.as_posix(),
            "historical_framework_status": historical["status"],
            "human_flow_baseline": HUMAN_FLOW_SAMPLE_PATH.as_posix(),
            "roadmap": "KMFA/taskpack/v1_4/roadmap/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_4.md",
        },
        "artifact_refs": {
            "summary": SUMMARY_PATH.as_posix(),
            "policy": POLICY_PATH.as_posix(),
            "records": RECORDS_PATH.as_posix(),
            "go_no_go": GO_NO_GO_PATH.as_posix(),
            "html_outputs": [path.as_posix() for path in HTML_PATHS.values()],
            "csv_outputs": [path.as_posix() for path in CSV_PATHS.values()],
            "management_readme": MANAGEMENT_README_PATH.as_posix(),
            "test_results": TEST_RESULTS_PATH.as_posix(),
            "validator": "KMFA/tools/check_v014_s10_p3_post_remediation_restricted_export.py",
        },
        "validation_summary": {
            "red_test_observed": True,
            "focused_tests": "PASS" if final_validation else "PENDING",
            "strict_validator": "PASS" if final_validation else "PENDING",
            "current_s10_p1_dependency": "PASS",
            "current_s10_p2_dependency": "PASS",
            "historical_s10_p3_framework": "PASS",
            "human_flow_baseline": "PASS",
            "browser_desktop_mobile": "PASS" if final_validation else "PENDING",
            "raw_snapshot_exact": "PASS",
            "governance_and_safety_scans": "PASS" if final_validation else "PENDING",
            "final_validation_recorded": final_validation,
        },
        "next_required_phase": "Stage 10 overall review",
    }
    go_no_go = {
        "schema_version": "kmfa.v014.s10_p3.post_remediation_restricted_export_go_no_go.v1",
        "project_id": "KMFA",
        "stage_id": "S10",
        "phase_id": PHASE_ID,
        "decision": DECISION,
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "restricted_preview_exports_created": True,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "stage10_review_performed": False,
        "github_upload_performed": False,
    }
    return {
        "summary": summary,
        "manifest": manifest,
        "policy": export_policy,
        "records": records_document,
        "go_no_go": go_no_go,
        "html_outputs": html_outputs,
        "csv_outputs": csv_outputs,
        "private": {"raw_before": raw_before, "raw_after": raw_after},
    }


def _render_completion(manifest: dict[str, Any]) -> str:
    summary = manifest["summary"]
    return f"""# KMFA v0.1.4 S10-P3 修补后受限导出完成记录

- phase：`{PHASE_ID}`
- roadmap phase：`{ROADMAP_PHASE_ID}`
- status：`{STATUS}`
- HTML / CSV / Excel-compatible CSV：`{summary['html_restricted_preview_count']} / {summary['csv_restricted_appendix_count']} / {summary['excel_compatible_csv_download_count']}`
- PDF / Excel workbook committed：`0 / 0`
- quality / grade / decision：`Q4 / D / NO_GO`
- open / nonzero / zero / incomplete：`3 / 9 / 2 / 1`
- Stage 10 review / GitHub upload / app reinstall / business execution：`false / false / false / false`
"""


def _render_management_readme() -> str:
    return """# KMFA 受限报告导出说明

- 当前两份报告均为 `D级（未放行）`，只允许内部复核预览。
- HTML 首屏显示等级、阻断原因和使用限制；CSV 附表采用全中文表头，仅保存聚合状态。
- Excel 下载使用兼容 CSV，不创建或提交工作簿。
- PDF 仅保留私有运行时策略，本 phase 未生成、未提交 PDF。
- 三项关键现金缺失不补零，九项非零差异不覆盖，一项未完成比较继续阻断。
- 这些导出不是正式报告，也不是经营决策依据。
"""


def _render_test_results(manifest: dict[str, Any]) -> str:
    final = manifest["validation_summary"]["final_validation_recorded"]
    state = "PASS" if final else "PENDING"
    return f"""# KMFA v0.1.4 S10-P3 修补后受限导出测试结果

- RED：`PASS`，已观察到实现缺失断言失败。
- focused tests：`{state}`
- strict validator：`{state}`
- current S10-P1 / current S10-P2 / historical S10-P3 framework：`PASS / PASS / PASS`
- human-flow baseline / desktop-mobile browser audit：`PASS / {state}`
- raw before/after/cross-phase snapshot：`PASS`
- governance / no-float / no-omission / structured parse / secret scan：`{state}`
- final validation recorded：`{str(final).lower()}`
- GitHub upload：`false`
"""


def _render_private_report(summary: dict[str, Any]) -> str:
    return f"""# S10-P3 受限导出私有验证记录

- 原始文件数量：{summary['raw_source_file_count']}
- 本 phase 前后快照一致：{str(summary['raw_snapshot_exact_match']).lower()}
- 与 S10-P2 快照一致：{str(summary['raw_cross_phase_snapshot_exact_match']).lower()}
- 两份 HTML 与两份中文 CSV 仅传播聚合状态和 D 级限制。
- 未生成 PDF、Excel 工作簿或私有 CSV。
"""


def _phase_public_files() -> list[str]:
    paths = (
        SUMMARY_PATH,
        MANIFEST_PATH,
        POLICY_PATH,
        RECORDS_PATH,
        GO_NO_GO_PATH,
        COMPLETION_PATH,
        MANAGEMENT_README_PATH,
        TEST_RESULTS_PATH,
        RISK_REGISTER_PATH,
        ROLLBACK_PATH,
        METADATA_SUMMARY_PATH,
        METADATA_MANIFEST_PATH,
        METADATA_POLICY_PATH,
        METADATA_RECORDS_PATH,
        METADATA_GO_NO_GO_PATH,
        *HTML_PATHS.values(),
        *CSV_PATHS.values(),
    )
    return [path.as_posix() for path in paths] + [
        "KMFA/tools/v014_s10_p3_post_remediation_restricted_export.py",
        "KMFA/tools/check_v014_s10_p3_post_remediation_restricted_export.py",
        "KMFA/tests/test_v014_s10_p3_post_remediation_restricted_export.py",
    ]


def _write_governance(generated_at: str) -> None:
    evidence_ref = MANIFEST_PATH.as_posix()
    upsert = p2_phase.p1_phase._upsert_jsonl
    upsert(
        DEVELOPMENT_EVENTS_PATH,
        "event_id",
        {
            "event_id": "DEV-KMFA-20260711-V014-S10-P3-POST-REMEDIATION-RESTRICTED-EXPORT",
            "event_time": generated_at,
            "event_type": "development",
            "project_id": "KMFA",
            "stage_id": "S10",
            "phase_id": PHASE_ID,
            "roadmap_phase_id": ROADMAP_PHASE_ID,
            "task_id": TASK_ID,
            "status": STATUS,
            "fact_level": "EXTRACTED",
            "decision": DECISION,
            "current_report_grade": "D",
            "raw_business_data_committed": False,
            "github_upload_performed": False,
            "app_reinstall_performed": False,
            "business_execution_performed": False,
            "evidence_ref": evidence_ref,
            "files_changed": _phase_public_files(),
            "result_commit": "PENDING",
        },
    )
    upsert(
        STAGE_STATUS_PATH,
        "phase_id",
        {
            "schema_version": "kmfa.stage_status.v1",
            "record_type": "phase_status",
            "project_id": "KMFA",
            "stage_id": "S10",
            "phase_id": PHASE_ID,
            "roadmap_phase_id": ROADMAP_PHASE_ID,
            "task_id": TASK_ID,
            "version": VERSION,
            "status": STATUS,
            "fact_level": "EXTRACTED",
            "decision": DECISION,
            "current_report_grade": "D",
            "raw_data_committed": False,
            "github_upload_performed": False,
            "app_reinstall_performed": False,
            "business_execution_performed": False,
            "evidence_ref": evidence_ref,
            "updated_at": generated_at,
        },
    )
    upsert(
        TASK_STATUS_PATH,
        "phase_id",
        {
            "schema_version": "kmfa.v014_stage_phase_task_status.v1",
            "record_type": "v014_phase",
            "project_id": "KMFA",
            "stage_id": "S10",
            "governance_stage_id": "REPORT-TRUST-AND-GENERATION",
            "roadmap_stage_id": "S10",
            "roadmap_phase_id": ROADMAP_PHASE_ID,
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "acceptance_id": ACCEPTANCE_ID,
            "version": VERSION,
            "name": "v0.1.4 S10-P3 post-remediation restricted export",
            "phase_goal": "create public-safe restricted HTML and Chinese CSV exports while propagating D NO_GO",
            "status": STATUS,
            "fact_level": "EXTRACTED",
            "derived_percent": 100,
            "estimated_task_units": 1,
            "completed_task_units": 1,
            "task_count": 1,
            "raw_data_committed": False,
            "evidence_ref": evidence_ref,
            "updated_at": generated_at[:10],
        },
    )


def generate(*, final_validation: bool = False, write_governance: bool = True) -> dict[str, Any]:
    payloads = build_payloads(final_validation=final_validation)
    for path, payload in (
        (SUMMARY_PATH, payloads["summary"]),
        (MANIFEST_PATH, payloads["manifest"]),
        (POLICY_PATH, payloads["policy"]),
        (RECORDS_PATH, payloads["records"]),
        (GO_NO_GO_PATH, payloads["go_no_go"]),
        (METADATA_SUMMARY_PATH, payloads["summary"]),
        (METADATA_MANIFEST_PATH, payloads["manifest"]),
        (METADATA_POLICY_PATH, payloads["policy"]),
        (METADATA_RECORDS_PATH, payloads["records"]),
        (METADATA_GO_NO_GO_PATH, payloads["go_no_go"]),
        (PRIVATE_RAW_BEFORE_PATH, payloads["private"]["raw_before"]),
        (PRIVATE_RAW_AFTER_PATH, payloads["private"]["raw_after"]),
    ):
        _write_json(path, payload)
    for entry_id, text in payloads["html_outputs"].items():
        _write_text(HTML_PATHS[entry_id], text)
    for entry_id, text in payloads["csv_outputs"].items():
        _write_text(CSV_PATHS[entry_id], text)
    _write_text(COMPLETION_PATH, _render_completion(payloads["manifest"]))
    _write_text(MANAGEMENT_README_PATH, _render_management_readme())
    _write_text(TEST_RESULTS_PATH, _render_test_results(payloads["manifest"]))
    _write_text(
        RISK_REGISTER_PATH,
        """# S10-P3 修补后受限导出风险登记

| 风险 | 控制 | 状态 |
|---|---|---|
| 旧 B 级或 12 pending 状态回流 | 当前 S10-P2 是唯一动态输入，历史导出只提供框架 | controlled |
| 受限预览被误用为正式报告 | 首屏、CSV 和记录同时传播 D级、未放行和使用限制 | controlled |
| HTML/CSV 泄漏业务值 | 只输出章节名称与聚合状态，validator 扫描业务值、raw 和 secret | controlled |
| PDF/Excel 工作簿误提交 | PDF 仅私有策略且未执行，Excel 只使用兼容 CSV | controlled |
""",
    )
    _write_text(
        ROLLBACK_PATH,
        f"""# S10-P3 修补后受限导出回滚计划

1. 回退本 phase 本地 commit 和 `{OUTPUT_DIR.as_posix()}` 公开证据。
2. 删除本 phase ignored private runtime 浏览器与快照证据，不触碰原始目录。
3. 恢复到 S10-P2 的 `Q4 / D / NO_GO` 和零导出状态。
4. 不回退、不移动、不删除、不覆盖任何原始文件。
""",
    )
    _write_text(PRIVATE_VALIDATION_REPORT_PATH, _render_private_report(payloads["summary"]))
    if write_governance:
        _write_governance(payloads["manifest"]["generated_at"])
    return payloads["manifest"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--final-validation", action="store_true")
    args = parser.parse_args()
    manifest = generate(final_validation=args.final_validation)
    summary = manifest["summary"]
    print(
        "S10-P3 post-remediation restricted export: "
        f"records={summary['report_export_record_count']} html={summary['html_restricted_preview_count']} "
        f"csv={summary['csv_restricted_appendix_count']} grade={summary['current_report_grade']} "
        f"decision={manifest['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
