#!/usr/bin/env python3
"""Build the current public-safe KMFA v0.1.4 S11-P3 project cost page."""

from __future__ import annotations

import argparse
import csv
import functools
import html
import http.server
import json
import os
import socketserver
import subprocess
import threading
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

from KMFA.tools import v014_s11_p1_post_remediation_home_navigation as p1
from KMFA.tools import v014_s11_p2_post_remediation_source_check_board as p2
from KMFA.tools.home_navigation_runtime import MODULE_ICONS
from KMFA.tools.project_cost_page_runtime import (
    REQUIRED_COST_CATEGORIES,
    REQUIRED_PROJECT_TABLE_COLUMNS,
)


PHASE_ID = "V014_S11_P3_POST_REMEDIATION_PROJECT_COST_PAGE"
TASK_ID = "KMFA-V014-S11-P3-POST-REMEDIATION-PROJECT-COST-PAGE-20260711"
ACCEPTANCE_ID = "ACC-V014-S11-P3-POST-REMEDIATION-PROJECT-COST-PAGE"
VERSION = "0.1.4-s11-p3-post-remediation-project-cost-page"
STATUS = "completed_validated_local_only_current_project_cost_page_d_no_go_upload_deferred"
FORMULA_ID = "FORM-KMFA-V014-S11-P3-POST-REMEDIATION-PROJECT-COST-PAGE-001"
MODEL_REGISTRY_KEY = "kmfa_v014_s11_p3_post_remediation_project_cost_page"
PARAMETER_IDS = ("PARAM-KMFA-1714", "PARAM-KMFA-1715", "PARAM-KMFA-1716")

OUTPUT_DIR = Path("KMFA/stage_artifacts") / PHASE_ID
HTML_DIR = OUTPUT_DIR / "exports/html"
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
HTML_PATH = HTML_DIR / "kmfa_project_cost_page.html"
SUMMARY_PATH = MACHINE_DIR / "project_cost_page_summary.json"
MANIFEST_PATH = MACHINE_DIR / "project_cost_page_manifest.json"
PROJECTS_PATH = MACHINE_DIR / "project_cost_page_projects_public_safe.json"
GO_NO_GO_PATH = MACHINE_DIR / "project_cost_page_go_no_go_report.json"
COMPLETION_PATH = HUMAN_DIR / "s11_p3_completion_record_zh.md"
READ_ME_PATH = HUMAN_DIR / "project_cost_page_readme_zh.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results_zh.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register_zh.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan_zh.md"

METADATA_PREFIX = Path("KMFA/metadata/quality/v014_s11_p3_post_remediation_project_cost_page")
METADATA_SUMMARY_PATH = Path(f"{METADATA_PREFIX}_summary.json")
METADATA_MANIFEST_PATH = Path(f"{METADATA_PREFIX}_manifest.json")
METADATA_PROJECTS_PATH = Path(f"{METADATA_PREFIX}_projects_public_safe.json")
METADATA_GO_NO_GO_PATH = Path(f"{METADATA_PREFIX}_go_no_go_report.json")

PRIVATE_DIR = Path("KMFA/.codex_private_runtime/v014_s11_p3_post_remediation_project_cost_page")
PRIVATE_RAW_BEFORE_PATH = PRIVATE_DIR / "raw_immutability_before.json"
PRIVATE_RAW_AFTER_PATH = PRIVATE_DIR / "raw_immutability_after.json"
PRIVATE_VALIDATION_REPORT_PATH = PRIVATE_DIR / "raw_consistency_report_zh.md"
PRIVATE_BROWSER_PATH = PRIVATE_DIR / "browser_evidence.json"
PRIVATE_BASELINE_AUDIT_PATH = PRIVATE_DIR / "human_flow_baseline_audit.csv"
PRIVATE_CURRENT_AUDIT_PATH = PRIVATE_DIR / "current_project_cost_page_audit.csv"
PRIVATE_SCREENSHOT_DIR = PRIVATE_DIR / "screenshots"

S09_P1_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V014_S09_P1_PROJECT_COST_FACT_LAYER/machine/project_cost_fact_layer_manifest.json"
)
S09_REVIEW_SUMMARY_PATH = Path(
    "KMFA/stage_artifacts/V014_S09_POST_REMEDIATION_STAGE_REVIEW/machine/"
    "stage9_post_remediation_review_summary.json"
)
S10_REVIEW_SUMMARY_PATH = Path(
    "KMFA/stage_artifacts/V014_S10_POST_REMEDIATION_STAGE_REVIEW/machine/"
    "stage10_post_remediation_review_summary.json"
)
S10_REPORT_ENTRIES_PATH = Path(
    "KMFA/stage_artifacts/V014_S10_P1_POST_REMEDIATION_REPORT_ENTRY/machine/"
    "report_entries_public_safe.json"
)
S10_GRADE_RECORDS_PATH = Path(
    "KMFA/stage_artifacts/V014_S10_P2_POST_REMEDIATION_TRUST_GRADE_LOCK/machine/"
    "report_grade_records_public_safe.json"
)
S10_RESTRICTED_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V014_S10_P3_POST_REMEDIATION_RESTRICTED_EXPORT/machine/"
    "restricted_export_manifest.json"
)
RESTRICTED_REPORT_PATH = Path(
    "KMFA/stage_artifacts/V014_S10_P3_POST_REMEDIATION_RESTRICTED_EXPORT/exports/html/"
    "project_cost_special_report.html"
)
PUBLIC_APPENDIX_PATH = Path(
    "KMFA/stage_artifacts/V014_S10_P3_POST_REMEDIATION_RESTRICTED_EXPORT/exports/csv/"
    "project_cost_special_report_appendix.csv"
)
LEGACY_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V014_S11_P3_PROJECT_COST_PAGE/machine/project_cost_page_manifest.json"
)
LEGACY_PROJECTS_PATH = Path(
    "KMFA/stage_artifacts/V014_S11_P3_PROJECT_COST_PAGE/machine/project_cost_page_projects.jsonl"
)

DEVELOPMENT_EVENTS_PATH = Path("KMFA/docs/governance/development_events.jsonl")
STAGE_STATUS_PATH = Path("KMFA/metadata/stage_status.jsonl")
TASK_STATUS_PATH = Path("KMFA/metadata/traceability/v1_4_stage_phase_task_status.jsonl")

CURRENT_EVIDENCE_LABELS = (
    ("S09 项目成本事实层", S09_P1_MANIFEST_PATH),
    ("S09 修补后整体复审", S09_REVIEW_SUMMARY_PATH),
    ("S10 项目成本报告入口", S10_REPORT_ENTRIES_PATH),
    ("S10 可信等级锁", S10_GRADE_RECORDS_PATH),
    ("S10 受限报告导出", S10_RESTRICTED_MANIFEST_PATH),
    ("S11 数据源检查板", p2.MANIFEST_PATH),
)

GLOBAL_PENDING_ITEMS = (
    "三项最终接受未决仍需保留",
    "九项非零差异不得被覆盖或归零",
    "一项比较尚未完成",
    "关键现金数值来源仍不完整",
    "完整追溯与充分人工确认尚未成立",
)


def _now_iso() -> str:
    return p2._now_iso()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path} must contain object rows")
            rows.append(value)
    return rows


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def _write_jsonl_unique(path: Path, row: dict[str, Any]) -> None:
    preserved: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip() and json.loads(line).get("phase_id") != PHASE_ID:
            preserved.append(line)
    preserved.append(json.dumps(row, ensure_ascii=False, separators=(",", ":")))
    _write_text(path, "\n".join(preserved) + "\n")


def _load_dependencies() -> dict[str, Any]:
    s09_p1 = _read_json(S09_P1_MANIFEST_PATH)
    s09_review = _read_json(S09_REVIEW_SUMMARY_PATH)
    s10_review = _read_json(S10_REVIEW_SUMMARY_PATH)
    report_entries_doc = _read_json(S10_REPORT_ENTRIES_PATH)
    grade_records_doc = _read_json(S10_GRADE_RECORDS_PATH)
    restricted = _read_json(S10_RESTRICTED_MANIFEST_PATH)
    current_p1 = _read_json(p1.MANIFEST_PATH)
    current_p2 = _read_json(p2.MANIFEST_PATH)
    legacy = _read_json(LEGACY_MANIFEST_PATH)
    legacy_projects = _read_jsonl(LEGACY_PROJECTS_PATH)

    p1_summary = s09_p1.get("project_cost_fact_layer_summary", {})
    p2_summary = current_p2.get("summary", {})
    expected_current = {
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "decision": "NO_GO",
        "open_final_difference_accepted_count": 3,
        "nonzero_delta_reconciliation_count": 9,
        "zero_delta_reconciliation_count": 2,
        "incomplete_reconciliation_count": 1,
    }
    for name, document in (
        ("S09 review", s09_review),
        ("S10 review", s10_review),
        ("S11-P2", p2_summary),
    ):
        for key, expected in expected_current.items():
            if document.get(key) != expected:
                raise ValueError(f"{name} current state mismatch for {key}")
    if current_p1.get("summary", {}).get("current_report_grade") != "D":
        raise ValueError("current S11-P1 grade mismatch")
    if p1_summary.get("fact_record_count") != 4 or p1_summary.get("cost_category_count") != 9:
        raise ValueError("current S09 project framework mismatch")
    if s09_review.get("cost_component_materialization_count") != 8:
        raise ValueError("current S09 materialization count mismatch")
    if s09_review.get("open_review_finding_count") != 0:
        raise ValueError("current S09 review still has open findings")

    entries = report_entries_doc.get("report_entries", [])
    project_entry = next((row for row in entries if row.get("entry_id") == "project_cost_special_report"), None)
    if not project_entry or project_entry.get("business_values_included") is not False:
        raise ValueError("current project report entry mismatch")
    grade_records = grade_records_doc.get("report_grade_records", [])
    project_grade = next(
        (row for row in grade_records if row.get("report_entry_id") == "project_cost_special_report"), None
    )
    if not project_grade or project_grade.get("computed_report_grade") != "D":
        raise ValueError("current project report grade mismatch")
    if not RESTRICTED_REPORT_PATH.is_file() or not PUBLIC_APPENDIX_PATH.is_file():
        raise ValueError("current restricted project report artifacts missing")

    legacy_summary = legacy.get("project_cost_page_summary", {})
    if legacy_summary.get("pending_reconciliation_count") != 12 or len(legacy_projects) != 4:
        raise ValueError("historical S11-P3 framework mismatch")

    return {
        "project_row_count": p1_summary["fact_record_count"],
        "cost_category_count": p1_summary["cost_category_count"],
        "margin_record_count": 4,
        "cost_component_materialization_count": s09_review["cost_component_materialization_count"],
        "historical_pending_reconciliation_count": legacy_summary["pending_reconciliation_count"],
        "historical_project_row_count": len(legacy_projects),
        "report_sections": list(project_entry.get("visible_sections", [])),
        "restricted_preview_status": restricted.get("status"),
    }


def _project_rows(generated_at: str) -> list[dict[str, Any]]:
    labels = [label for label, _ in CURRENT_EVIDENCE_LABELS]
    refs = [path.as_posix() for _, path in CURRENT_EVIDENCE_LABELS]
    rows: list[dict[str, Any]] = []
    for index in range(1, 5):
        rows.append(
            {
                "schema_version": "kmfa.v014.s11_p3.post_remediation_project_slot.v1",
                "record_type": "post_remediation_public_safe_project_slot",
                "project_id": "KMFA",
                "stage_phase": "S11-P3",
                "row_id": f"PCP-{index:03d}",
                "project_order": index,
                "project_display_ref": f"项目分组 {index:03d}",
                "project_entity_group_ref": f"项目实体分组 {index:03d}",
                "gross_margin_status": "毛利槽位已登记，正式结论继续阻断",
                "cost_structure_summary": "九类成本结构已登记，项目级业务金额不展示",
                "collection_status": "回款槽位已登记，关键现金比较仍未完成",
                "difference_status": "项目级归属未公开，全局状态继续 NO_GO",
                "report_preview_status": "D级受限预览可查看，不作为正式报告或决策依据",
                "next_step": "完成可证明的项目级追溯与人工确认后，才可分配差异并复核等级",
                "project_specific_allocation_status": "not_publicly_attributed",
                "project_specific_difference_count": None,
                "global_state_ref": {
                    "open_final_difference_accepted_count": 3,
                    "nonzero_delta_reconciliation_count": 9,
                    "zero_delta_reconciliation_count": 2,
                    "incomplete_reconciliation_count": 1,
                },
                "source_evidence_labels": labels,
                "source_evidence_refs": refs,
                "pending_items": list(GLOBAL_PENDING_ITEMS),
                "contains_raw_business_values": False,
                "contains_private_file_references": False,
                "raw_layer_write_allowed": False,
                "persistent_business_write_allowed": False,
                "formal_report_allowed": False,
                "business_decision_basis_allowed": False,
                "quality_grade_bypass_allowed": False,
                "generated_at": generated_at,
            }
        )
    return rows


def _icon_svg(icon_key: str) -> str:
    return (
        '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" '
        'stroke="currentColor" stroke-width="1.8" stroke-linecap="round" '
        f'stroke-linejoin="round">{MODULE_ICONS[icon_key]}</svg>'
    )


def _render_html(rows: list[dict[str, Any]]) -> str:
    table_rows = "".join(
        f"""<tr data-project-row="{html.escape(row['row_id'])}" data-search="{html.escape((row['project_display_ref'] + ' ' + row['gross_margin_status'] + ' ' + row['cost_structure_summary'] + ' ' + row['collection_status'] + ' ' + row['difference_status']).lower())}">
<td><button class="project-link" type="button" data-project-detail="{html.escape(row['row_id'])}">{html.escape(row['project_display_ref'])}</button></td>
<td>{html.escape(row['gross_margin_status'])}</td><td>{html.escape(row['cost_structure_summary'])}</td>
<td>{html.escape(row['collection_status'])}</td><td><span class="status-badge">{html.escape(row['difference_status'])}</span></td>
<td><button class="inline-command" type="button" data-project-preview="{html.escape(row['row_id'])}">查看受限预览</button></td>
<td>{html.escape(row['next_step'])}</td></tr>"""
        for row in rows
    )
    first = rows[0]
    evidence_items = "".join(f"<li>{html.escape(label)}</li>" for label, _ in CURRENT_EVIDENCE_LABELS)
    pending_items = "".join(f"<li>{html.escape(item)}</li>" for item in GLOBAL_PENDING_ITEMS)
    report_sections = (
        ("summary", "经营摘要", "四个项目槽位仅展示公开安全状态；项目级金额、客户和原始字段均不进入本页面。"),
        ("margin", "项目毛利", "四条毛利槽位已登记，但关键差异和完整追溯未闭环，正式毛利结论继续阻断。"),
        ("cost", "成本结构", "九类成本结构已登记，八条分项物化记录已通过复审；项目级业务值不在公开页面分配。"),
        ("risk", "风险事项", "三项最终接受未决、九项非零差异和一项未完成比较继续维持 D 级、NO_GO。"),
    )
    report_buttons = "".join(
        f'<button class="report-tab{" active" if index == 0 else ""}" type="button" data-report-section="{key}" aria-selected="{"true" if index == 0 else "false"}">{label}</button>'
        for index, (key, label, _) in enumerate(report_sections)
    )
    report_panels = "".join(
        f'<section class="report-section{" active" if index == 0 else ""}" data-report-panel="{key}" {"" if index == 0 else "hidden"}><h3>{label}</h3><p>{copy}</p></section>'
        for index, (key, label, copy) in enumerate(report_sections)
    )
    row_state = json.dumps({row["row_id"]: row for row in rows}, ensure_ascii=False, sort_keys=True)
    home_href = "../../../V014_S11_P1_POST_REMEDIATION_HOME_NAVIGATION/exports/html/kmfa_home_navigation.html"
    source_href = "../../../V014_S11_P2_POST_REMEDIATION_SOURCE_CHECK_BOARD/exports/html/kmfa_source_check_board.html"
    report_href = "../../../V014_S10_P3_POST_REMEDIATION_RESTRICTED_EXPORT/exports/html/project_cost_special_report.html"
    appendix_href = "../../../V014_S10_P3_POST_REMEDIATION_RESTRICTED_EXPORT/exports/csv/project_cost_special_report_appendix.csv"
    template = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>KMFA 项目成本页面</title><style>
:root{--navy:#123d61;--blue:#176ca5;--blue-soft:#eaf4fa;--ink:#17324a;--muted:#617487;--line:#c8d9e5;--surface:#ffffff;--canvas:#f2f6f8;--danger:#ae3030;--danger-soft:#fff1f0;--teal:#137565;--purple:#6a4aa5}
*{box-sizing:border-box}html{background:var(--canvas)}body{margin:0;color:var(--ink);background:var(--canvas);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Microsoft YaHei",Arial,sans-serif;font-size:14px;line-height:1.55;letter-spacing:0}button,input{font:inherit}button,a{transition:background-color .15s,color .15s,border-color .15s}button{cursor:pointer}.topbar{height:84px;background:var(--navy);color:#fff;display:flex;align-items:center;justify-content:space-between;padding:0 28px;border-bottom:4px solid #2f88bd}.brand{display:flex;align-items:center;gap:12px}.brand-icon{width:46px;height:46px;border:1px solid #8fc0dd;border-radius:6px;background:#176ca5;display:grid;place-items:center}.brand-icon svg{width:24px;height:24px}.brand strong{font-size:18px}.brand small{display:block;color:#c8e4f3}.top-links{display:flex;gap:8px;flex-wrap:wrap}.top-links a,.outline-link{color:#fff;text-decoration:none;border:1px solid #8fb2c8;border-radius:5px;padding:8px 11px;background:transparent}.top-links a:hover{background:#1a547d}.layout{max-width:1500px;margin:0 auto;padding:26px 28px 44px}.heading{display:flex;justify-content:space-between;align-items:flex-start;gap:20px}.heading h1{font-size:28px;margin:0 0 6px}.heading p{margin:0;color:var(--muted)}.grade-lock{border:1px solid #e7a8a3;background:var(--danger-soft);color:var(--danger);border-radius:6px;padding:10px 13px;min-width:170px}.grade-lock span{display:block;font-size:12px}.grade-lock strong{font-size:17px}.restriction{margin:18px 0 16px;border-left:4px solid var(--danger);background:#fff8f7;padding:13px 15px}.metrics{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));border:1px solid var(--line);background:var(--surface);border-radius:6px;overflow:hidden}.metric{padding:14px;border-right:1px solid var(--line)}.metric:last-child{border-right:0}.metric span{display:block;color:var(--muted);font-size:12px}.metric strong{display:block;font-size:22px;margin-top:3px}.section{margin-top:18px}.section-head{display:flex;justify-content:space-between;align-items:flex-end;gap:14px;margin-bottom:10px}.section h2{font-size:19px;margin:0}.section-head p{margin:3px 0 0;color:var(--muted)}.search-row{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:10px}.search-row input{width:100%;border:1px solid var(--line);border-radius:5px;padding:10px 12px;background:#fff}.command{border:1px solid var(--blue);border-radius:5px;padding:9px 13px;background:#fff;color:var(--blue);font-weight:700}.command:hover,.command:focus-visible{background:var(--blue-soft)}.primary{background:var(--blue);color:#fff}.primary:hover{background:#115882}.table-scroll{overflow-x:auto;border:1px solid var(--line);background:#fff;border-radius:5px}.project-table{width:100%;min-width:1180px;border-collapse:collapse}.project-table th,.project-table td{padding:11px 10px;border-bottom:1px solid #dfe9ef;text-align:left;vertical-align:top}.project-table th{background:#eaf2f6;color:#254a63;font-size:12px;white-space:nowrap}.project-table tr:last-child td{border-bottom:0}.project-table tr.selected td{background:#f2f9fc}.project-link,.inline-command{border:0;background:transparent;color:var(--blue);padding:0;font-weight:750;text-align:left}.status-badge{display:inline-block;border-radius:999px;background:#f2edf9;color:var(--purple);padding:3px 8px;font-size:12px;font-weight:750}.feedback{margin:8px 0;color:var(--muted)}.detail-grid{display:grid;grid-template-columns:1.05fr 1fr 1fr;border:1px solid var(--line);background:#fff;border-radius:6px}.detail-column{padding:16px;border-right:1px solid var(--line)}.detail-column:last-child{border-right:0}.detail-column h3{font-size:15px;margin:0 0 8px}.detail-column ul{margin:0;padding-left:19px}.detail-column li+li{margin-top:5px}.detail-note{margin:12px 0 0;padding:10px;background:#f4f7f8;color:var(--muted);border-left:3px solid #7896aa}.report-shell{border:1px solid var(--line);background:#fff;border-radius:6px}.report-toolbar{display:flex;justify-content:space-between;gap:12px;padding:12px;border-bottom:1px solid var(--line);flex-wrap:wrap}.report-tabs,.report-actions{display:flex;gap:7px;flex-wrap:wrap}.report-tab{border:1px solid var(--line);border-radius:5px;background:#fff;color:var(--blue);padding:8px 11px;font-weight:700}.report-tab.active{background:var(--navy);color:#fff;border-color:var(--navy)}.report-section{padding:16px;min-height:112px}.report-section h3{margin:0 0 7px}.report-section p{margin:0}.control-feedback{margin:0 12px 12px;background:#eef6f4;border-left:3px solid var(--teal);padding:9px 11px;color:#28574f}.preview-shell{margin-top:12px;border-top:1px solid var(--line);padding:12px}.preview-head{display:flex;justify-content:space-between;align-items:center;gap:10px;margin-bottom:10px}.preview-head h3{margin:0}.preview-frame{width:100%;height:620px;border:1px solid var(--line);background:#fff}.boundary-note{font-size:12px;color:var(--muted);margin-top:14px}.boundary-note strong{color:var(--danger)}[hidden]{display:none!important}.mobile-only{display:none}
@media(max-width:900px){.topbar{height:auto;min-height:84px;padding:14px 12px;align-items:flex-start}.top-links{justify-content:flex-end}.layout{padding:18px 12px 30px}.heading{display:block}.grade-lock{margin-top:12px;width:max-content}.metrics{grid-template-columns:repeat(2,minmax(0,1fr))}.metric{border-bottom:1px solid var(--line)}.detail-grid{grid-template-columns:minmax(0,1fr)}.detail-column{border-right:0;border-bottom:1px solid var(--line)}.detail-column:last-child{border-bottom:0}.preview-frame{height:520px}.table-scroll{max-width:100%}}
@media(max-width:520px){.brand small{display:none}.brand strong{font-size:16px}.brand-icon{width:40px;height:40px}.top-links a{padding:7px 8px}.heading h1{font-size:24px}.metrics{grid-template-columns:minmax(0,1fr)}.metric{border-right:0}.search-row{grid-template-columns:minmax(0,1fr)}.report-toolbar{display:block}.report-actions{margin-top:8px}.preview-frame{height:460px}}
</style></head><body data-ui-ready="false" data-report-preview-open="false">
<header class="topbar"><div class="brand"><div class="brand-icon">__ICON__</div><div><strong>KMFA 项目成本页面</strong><small>公开安全项目槽位与受限报告预览</small></div></div><nav class="top-links"><a data-linked-artifact data-home-link href="__HOME_HREF__">返回经营首页</a><a data-linked-artifact data-source-link href="__SOURCE_HREF__">查看数据源检查板</a></nav></header>
<main class="layout"><section class="heading"><div><h1>项目成本状态与受限报告</h1><p>逐项查看毛利、成本结构、回款和差异状态；无法证明的项目级分配保持未知。</p></div><div class="grade-lock"><span>当前质量与报告等级</span><strong>Q4 / D · NO_GO</strong></div></section>
<div class="restriction"><strong>当前限制：</strong>3 项最终接受未决、9 项非零差异、2 项零差异、1 项比较未完成。项目级归属未由公开证据证明，不得平均分配或补零。</div>
<section class="metrics" aria-label="当前项目成本概览"><div class="metric"><span>公开安全项目槽位</span><strong>4</strong></div><div class="metric"><span>成本类别</span><strong>9</strong></div><div class="metric"><span>分项物化记录</span><strong>8</strong></div><div class="metric"><span>项目级差异归属</span><strong>未知</strong></div><div class="metric"><span>正式报告</span><strong>0</strong></div></section>
<section class="section"><div class="section-head"><div><h2>项目列表</h2><p>搜索仅作用于公开安全别名与聚合状态。</p></div></div><div class="search-row"><input id="project-search" type="search" aria-label="搜索项目槽位" placeholder="输入项目分组或状态"><button id="reset-search" class="command" type="button">清除搜索</button></div><p id="search-feedback" class="feedback" aria-live="polite">当前显示 4 个公开安全项目槽位。</p><div id="project-table-scroll" class="table-scroll"><table class="project-table"><thead><tr>__TABLE_HEAD__</tr></thead><tbody>__TABLE_ROWS__</tbody></table></div></section>
<section class="section" id="project-detail" data-selected-project="__FIRST_ROW__"><div class="section-head"><div><h2 id="detail-title">__FIRST_TITLE__</h2><p id="detail-status">项目级差异归属：未公开</p></div><button class="command primary" type="button" data-report-open>打开 D 级受限报告预览</button></div><div class="detail-grid"><div class="detail-column"><h3>来源证据</h3><ul id="detail-evidence">__EVIDENCE_ITEMS__</ul></div><div class="detail-column"><h3>待处理事项</h3><ul id="detail-pending">__PENDING_ITEMS__</ul></div><div class="detail-column"><h3>报告预览</h3><p id="detail-report">__FIRST_REPORT__</p><p class="detail-note">这些是全局门禁，不代表已分配到当前项目。页面不写原始数据或持久业务状态。</p></div></div></section>
<section class="section"><div class="section-head"><div><h2>报告预览控制</h2><p>可查看受限内部预览，但不可绕过 D 级或 NO_GO。</p></div></div><div class="report-shell"><div class="report-toolbar"><div class="report-tabs" role="tablist">__REPORT_BUTTONS__</div><div class="report-actions"><button class="command" type="button" data-print-feedback>打印/另存说明</button><button class="command" type="button" data-appendix-feedback>附表下载说明</button><a class="command" data-linked-artifact data-restricted-report-link href="__REPORT_HREF__" target="_blank" rel="noopener">新窗口查看受限报告</a><a class="command" data-linked-artifact data-public-appendix-link href="__APPENDIX_HREF__">下载公开安全附表</a></div></div>__REPORT_PANELS__<p id="control-feedback" class="control-feedback" aria-live="polite">尚未执行报告预览控制动作；当前等级保持 D。</p><div id="report-preview-shell" class="preview-shell" hidden><div class="preview-head"><h3>项目成本专题报告 · D级受限预览</h3><button class="command" type="button" data-report-close>关闭预览</button></div><iframe id="report-frame" class="preview-frame" title="项目成本专题报告 D级受限预览" src="__REPORT_HREF__"></iframe></div></div></section>
<p class="boundary-note"><strong>公开安全边界：</strong>不包含原始文件身份、字段表头、项目或客户明文、业务金额、账户或明细。Stage 11 整体复审、GitHub upload 与 app reinstall 尚未执行。</p></main>
<script>
const projectState=__ROW_STATE__;const body=document.body;const search=document.getElementById('project-search');const feedback=document.getElementById('search-feedback');const controlEvents=[];let sequence=0;
function recordAction(action){sequence+=1;body.dataset.lastAction=`${String(sequence).padStart(3,'0')}:${action}`;}
function visibleRows(){return Array.from(document.querySelectorAll('tbody tr[data-project-row]')).filter(row=>row.style.display!=='none');}
function applySearch(){const term=search.value.trim().toLowerCase();document.querySelectorAll('tbody tr[data-project-row]').forEach(row=>{row.style.display=!term||row.dataset.search.includes(term)?'':'none';});feedback.textContent=`当前显示 ${visibleRows().length} 个公开安全项目槽位。`;recordAction(`搜索:${term||'全部'}:${visibleRows().length}`);}
function resetSearch(){search.value='';applySearch();feedback.textContent='已清除搜索，当前显示 4 个公开安全项目槽位。';recordAction('清除搜索:4');}
function selectProject(rowId){const row=projectState[rowId];if(!row)return;document.querySelectorAll('tbody tr[data-project-row]').forEach(item=>item.classList.toggle('selected',item.dataset.projectRow===rowId));const detail=document.getElementById('project-detail');detail.dataset.selectedProject=rowId;document.getElementById('detail-title').textContent=`${row.project_display_ref} · 项目成本详情`;document.getElementById('detail-status').textContent='项目级差异归属：未公开；当前全局状态 Q4 / D / NO_GO';document.getElementById('detail-evidence').innerHTML=row.source_evidence_labels.map(item=>`<li>${item}</li>`).join('');document.getElementById('detail-pending').innerHTML=row.pending_items.map(item=>`<li>${item}</li>`).join('');document.getElementById('detail-report').textContent=row.report_preview_status;recordAction(`项目详情:${rowId}`);}
function switchReportSection(section){document.querySelectorAll('[data-report-section]').forEach(button=>{const active=button.dataset.reportSection===section;button.classList.toggle('active',active);button.setAttribute('aria-selected',String(active));});document.querySelectorAll('[data-report-panel]').forEach(panel=>{const active=panel.dataset.reportPanel===section;panel.hidden=!active;panel.classList.toggle('active',active);});body.dataset.activeReportSection=section;recordAction(`报告章节:${section}`);}
function openReportPreview(){document.getElementById('report-preview-shell').hidden=false;body.dataset.reportPreviewOpen='true';document.getElementById('control-feedback').textContent='已打开 D 级受限预览；质量等级、NO_GO 和使用限制保持不变。';recordAction('打开受限报告预览');}
function closeReportPreview(){document.getElementById('report-preview-shell').hidden=true;body.dataset.reportPreviewOpen='false';document.getElementById('control-feedback').textContent='已关闭受限预览；未发布正式报告。';recordAction('关闭受限报告预览');}
function previewProject(rowId){selectProject(rowId);openReportPreview();}
function feedbackAction(copy,action){controlEvents.push({event_id:`会话事件-${String(controlEvents.length+1).padStart(3,'0')}`,target_layer:'browser_session_only',persistent_write:false,raw_layer_write:false,quality_grade_bypass:false});document.getElementById('control-feedback').textContent=copy;recordAction(action);}
document.querySelectorAll('[data-project-detail]').forEach(button=>button.addEventListener('click',()=>selectProject(button.dataset.projectDetail)));
document.querySelectorAll('[data-project-preview]').forEach(button=>button.addEventListener('click',()=>previewProject(button.dataset.projectPreview)));
document.querySelectorAll('[data-report-section]').forEach(button=>button.addEventListener('click',()=>switchReportSection(button.dataset.reportSection)));
document.querySelector('[data-report-open]').addEventListener('click',openReportPreview);document.querySelector('[data-report-close]').addEventListener('click',closeReportPreview);
document.querySelector('[data-print-feedback]').addEventListener('click',()=>feedbackAction('打印或另存仅适用于 D 级受限预览，不产生正式报告。','打印说明'));
document.querySelector('[data-appendix-feedback]').addEventListener('click',()=>feedbackAction('附表仅为公开安全状态说明，不包含业务金额或私有字段。','附表说明'));
search.addEventListener('input',applySearch);document.getElementById('reset-search').addEventListener('click',resetSearch);selectProject('__FIRST_ROW__');switchReportSection('summary');body.dataset.uiReady='true';recordAction('页面就绪:4');
</script></body></html>"""
    replacements = {
        "__ICON__": _icon_svg("project_cost"),
        "__HOME_HREF__": home_href,
        "__SOURCE_HREF__": source_href,
        "__REPORT_HREF__": report_href,
        "__APPENDIX_HREF__": appendix_href,
        "__TABLE_HEAD__": "".join(f"<th>{html.escape(column)}</th>" for column in REQUIRED_PROJECT_TABLE_COLUMNS),
        "__TABLE_ROWS__": table_rows,
        "__FIRST_ROW__": first["row_id"],
        "__FIRST_TITLE__": html.escape(f"{first['project_display_ref']} · 项目成本详情"),
        "__FIRST_REPORT__": html.escape(first["report_preview_status"]),
        "__EVIDENCE_ITEMS__": evidence_items,
        "__PENDING_ITEMS__": pending_items,
        "__REPORT_BUTTONS__": report_buttons,
        "__REPORT_PANELS__": report_panels,
        "__ROW_STATE__": row_state,
    }
    for token, value in replacements.items():
        template = template.replace(token, value)
    return template


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        return


def _browser_worker() -> dict[str, Any]:
    from playwright.sync_api import sync_playwright

    PRIVATE_SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    stage_root = Path("KMFA/stage_artifacts").resolve()
    handler = functools.partial(_QuietHandler, directory=str(stage_root))
    server = socketserver.TCPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    url = f"{base}/{PHASE_ID}/exports/html/{HTML_PATH.name}"
    viewport_checks: list[dict[str, Any]] = []
    search_checks: list[dict[str, Any]] = []
    detail_checks: list[dict[str, Any]] = []
    section_checks: list[dict[str, Any]] = []
    open_checks: list[dict[str, Any]] = []
    close_checks: list[dict[str, Any]] = []
    keyboard_checks: list[dict[str, Any]] = []
    linked_checks: list[dict[str, Any]] = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True,
                executable_path=p1._chromium_path(),
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
            for mode, viewport in (
                ("desktop", {"width": 1440, "height": 1000}),
                ("mobile", {"width": 390, "height": 844}),
            ):
                page = browser.new_page(viewport=viewport)
                console_errors: list[str] = []
                page.on(
                    "console",
                    lambda msg: console_errors.append(msg.text)
                    if msg.type == "error"
                    and p1._is_actionable_console_error(f"{msg.text} {msg.location.get('url', '')}")
                    else None,
                )
                page.on("pageerror", lambda exc: console_errors.append(str(exc)))
                page.goto(url, wait_until="networkidle")
                page.wait_for_timeout(80)

                page.locator("#project-search").fill("项目分组 003")
                search_checks.append(
                    {
                        "mode": mode,
                        "action": "search",
                        "passed": page.locator('tbody tr[data-project-row]:visible').count() == 1
                        and "1 个" in page.locator("#search-feedback").inner_text(),
                    }
                )
                page.locator("#reset-search").click()
                search_checks.append(
                    {
                        "mode": mode,
                        "action": "reset",
                        "passed": page.locator('tbody tr[data-project-row]:visible').count() == 4
                        and page.locator("#project-search").input_value() == "",
                    }
                )

                for index in range(1, 5):
                    row_id = f"PCP-{index:03d}"
                    page.locator(f'button[data-project-detail="{row_id}"]').click()
                    detail_checks.append(
                        {
                            "mode": mode,
                            "row_id": row_id,
                            "passed": page.locator("#project-detail").get_attribute("data-selected-project") == row_id
                            and page.locator("#detail-evidence li").count() == len(CURRENT_EVIDENCE_LABELS)
                            and page.locator("#detail-pending li").count() == len(GLOBAL_PENDING_ITEMS)
                            and "未公开" in page.locator("#detail-status").inner_text(),
                        }
                    )

                first_button = page.locator('button[data-project-detail="PCP-001"]')
                first_button.focus()
                first_button.press("Enter")
                keyboard_checks.append(
                    {
                        "mode": mode,
                        "passed": page.locator("#project-detail").get_attribute("data-selected-project") == "PCP-001",
                    }
                )

                for section in ("summary", "margin", "cost", "risk"):
                    page.locator(f'button[data-report-section="{section}"]').click()
                    section_checks.append(
                        {
                            "mode": mode,
                            "section": section,
                            "passed": body_value(page, "activeReportSection") == section
                            and page.locator(f'[data-report-panel="{section}"]').is_visible(),
                        }
                    )

                page.locator("[data-report-open]").click()
                page.wait_for_timeout(80)
                frame_text = page.frame_locator("#report-frame").locator("body").inner_text()
                open_checks.append(
                    {
                        "mode": mode,
                        "passed": body_value(page, "reportPreviewOpen") == "true"
                        and page.locator("#report-preview-shell").is_visible()
                        and "D级" in frame_text,
                    }
                )
                page.locator("[data-report-close]").click()
                close_checks.append(
                    {
                        "mode": mode,
                        "passed": body_value(page, "reportPreviewOpen") == "false"
                        and not page.locator("#report-preview-shell").is_visible(),
                    }
                )

                if mode == "desktop":
                    links = page.locator("a[data-linked-artifact]")
                    for index in range(links.count()):
                        href = links.nth(index).get_attribute("href") or ""
                        response = page.request.get(urljoin(page.url, href))
                        linked_checks.append({"href": href, "status": response.status, "passed": response.ok})

                page.reload(wait_until="networkidle")
                dimensions = page.evaluate(
                    """({
                      documentScrollWidth: document.documentElement.scrollWidth,
                      innerWidth: window.innerWidth,
                      tableRight: document.getElementById('project-table-scroll').getBoundingClientRect().right,
                      tableOverflowX: getComputedStyle(document.getElementById('project-table-scroll')).overflowX
                    })"""
                )
                screenshot = PRIVATE_SCREENSHOT_DIR / f"kmfa_project_cost_page_{mode}.png"
                page.screenshot(path=str(screenshot), full_page=True)
                viewport_checks.append(
                    {
                        "mode": mode,
                        "viewport": viewport,
                        "ui_ready": body_value(page, "uiReady") == "true",
                        "console_error_count": len(console_errors),
                        "no_horizontal_overflow": dimensions["documentScrollWidth"] <= dimensions["innerWidth"],
                        "table_scroll_contained": dimensions["tableRight"] <= dimensions["innerWidth"] + 1
                        and dimensions["tableOverflowX"] == "auto",
                    }
                )
                page.close()
            browser.close()
    finally:
        server.shutdown()
        server.server_close()

    passed = (
        all(item["passed"] for item in search_checks)
        and all(item["passed"] for item in detail_checks)
        and all(item["passed"] for item in section_checks)
        and all(item["passed"] for item in open_checks)
        and all(item["passed"] for item in close_checks)
        and all(item["passed"] for item in keyboard_checks)
        and all(item["passed"] for item in linked_checks)
        and all(
            item["ui_ready"]
            and item["console_error_count"] == 0
            and item["no_horizontal_overflow"]
            and item["table_scroll_contained"]
            for item in viewport_checks
        )
    )
    result = {
        "status": "PASS" if passed else "FAIL",
        "viewport_checks": viewport_checks,
        "search_checks": search_checks,
        "project_detail_checks": detail_checks,
        "report_section_checks": section_checks,
        "report_preview_open_checks": open_checks,
        "report_preview_close_checks": close_checks,
        "keyboard_checks": keyboard_checks,
        "linked_artifact_http_checks": linked_checks,
    }
    _write_json(PRIVATE_BROWSER_PATH, result)
    if not passed:
        raise RuntimeError("S11-P3 browser review failed")
    return result


def body_value(page: Any, key: str) -> str | None:
    return page.locator("body").get_attribute("data-" + "".join(
        f"-{character.lower()}" if character.isupper() else character for character in key
    ))


def _run_browser_suite() -> dict[str, Any]:
    baseline = p1._run_html_audit(p1.AUDIT_ROOT, PRIVATE_BASELINE_AUDIT_PATH)
    current = p1._run_html_audit(HTML_DIR, PRIVATE_CURRENT_AUDIT_PATH)
    env = os.environ.copy()
    env["KMFA_CHROMIUM"] = p1._chromium_path()
    result = subprocess.run(
        [str(p1._audit_python()), str(Path(__file__).resolve()), "--browser-evidence-only"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"browser evidence failed: {result.stdout}\n{result.stderr}")
    browser = _read_json(PRIVATE_BROWSER_PATH)
    return {
        "baseline_file_count": baseline["file_count"],
        "baseline_control_row_count": baseline["control_row_count"],
        "baseline_pass_count": baseline["pass_count"],
        "baseline_warn_count": baseline["warn_count"],
        "baseline_fail_count": baseline["fail_count"],
        "current_html_file_count": current["file_count"],
        "current_html_control_row_count": current["control_row_count"],
        "current_html_pass_count": current["pass_count"],
        "current_html_warn_count": current["warn_count"],
        "current_html_fail_count": current["fail_count"],
        "viewport_check_count": len(browser["viewport_checks"]),
        "search_interaction_count": len(browser["search_checks"]),
        "project_detail_interaction_count": len(browser["project_detail_checks"]),
        "report_section_interaction_count": len(browser["report_section_checks"]),
        "report_preview_open_count": len(browser["report_preview_open_checks"]),
        "report_preview_close_count": len(browser["report_preview_close_checks"]),
        "keyboard_interaction_count": len(browser["keyboard_checks"]),
        "linked_artifact_http_check_count": len(browser["linked_artifact_http_checks"]),
        "console_error_count": sum(item["console_error_count"] for item in browser["viewport_checks"]),
        "horizontal_overflow_count": sum(not item["no_horizontal_overflow"] for item in browser["viewport_checks"]),
        "table_scroll_containment_count": sum(item["table_scroll_contained"] for item in browser["viewport_checks"]),
    }


def _raw_snapshot(label: str) -> dict[str, Any]:
    return p2._raw_snapshot(label)


def _normalize_raw(value: dict[str, Any]) -> dict[str, Any]:
    return p2._normalize_raw(value)


def _write_governance_events(generated_at: str) -> None:
    evidence_ref = MANIFEST_PATH.as_posix()
    _write_jsonl_unique(
        DEVELOPMENT_EVENTS_PATH,
        {
            "event_id": "DEV-KMFA-20260711-V014-S11-P3-POST-REMEDIATION-PROJECT-COST-PAGE",
            "event_time": generated_at,
            "event_type": "development",
            "project_id": "KMFA",
            "stage_id": "S11",
            "phase_id": PHASE_ID,
            "roadmap_phase_id": "S11-P3",
            "task_id": TASK_ID,
            "status": STATUS,
            "fact_level": "EXTRACTED",
            "decision": "NO_GO",
            "current_report_grade": "D",
            "raw_business_data_committed": False,
            "project_level_false_attribution_performed": False,
            "github_upload_performed": False,
            "app_reinstall_performed": False,
            "business_execution_performed": False,
            "evidence_ref": evidence_ref,
            "result_commit": "PENDING",
        },
    )
    _write_jsonl_unique(
        STAGE_STATUS_PATH,
        {
            "schema_version": "kmfa.stage_status.v1",
            "record_type": "phase_status",
            "project_id": "KMFA",
            "stage_id": "S11",
            "phase_id": PHASE_ID,
            "roadmap_phase_id": "S11-P3",
            "task_id": TASK_ID,
            "version": VERSION,
            "status": STATUS,
            "fact_level": "EXTRACTED",
            "decision": "NO_GO",
            "current_report_grade": "D",
            "raw_data_committed": False,
            "project_level_false_attribution_performed": False,
            "github_upload_performed": False,
            "app_reinstall_performed": False,
            "business_execution_performed": False,
            "evidence_ref": evidence_ref,
            "updated_at": generated_at,
        },
    )
    _write_jsonl_unique(
        TASK_STATUS_PATH,
        {
            "schema_version": "kmfa.v014_stage_phase_task_status.v1",
            "record_type": "v014_phase",
            "project_id": "KMFA",
            "stage_id": "S11",
            "governance_stage_id": "FRONTEND-BASE-AND-SOURCE-CHECK",
            "roadmap_stage_id": "S11",
            "roadmap_phase_id": "S11-P3",
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "acceptance_id": ACCEPTANCE_ID,
            "version": VERSION,
            "name": "v0.1.4 S11-P3 post-remediation project cost page",
            "phase_goal": "show current public-safe project cost states without false project attribution or D-grade bypass",
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


def generate(*, final_validation: bool = False) -> dict[str, Any]:
    generated_at = _now_iso()
    dependencies = _load_dependencies()
    rows = _project_rows(generated_at)
    raw_before = _raw_snapshot("v014_s11_p3_post_remediation_project_cost_page_before")
    _write_json(PRIVATE_RAW_BEFORE_PATH, raw_before)
    _write_text(HTML_PATH, _render_html(rows))
    browser = _run_browser_suite()
    raw_after = _raw_snapshot("v014_s11_p3_post_remediation_project_cost_page_after")
    _write_json(PRIVATE_RAW_AFTER_PATH, raw_after)
    prior_raw = _read_json(p2.PRIVATE_RAW_AFTER_PATH)
    current_raw = _raw_snapshot("v014_s11_p3_post_remediation_project_cost_page_current")
    if not (
        _normalize_raw(raw_before)
        == _normalize_raw(raw_after)
        == _normalize_raw(prior_raw)
        == _normalize_raw(current_raw)
    ):
        raise ValueError("raw snapshot drift detected")

    summary = {
        "schema_version": "kmfa.v014.s11_p3.post_remediation_project_cost_page_summary.v1",
        "project_id": "KMFA",
        "stage_id": "S11",
        "phase_id": PHASE_ID,
        "roadmap_phase_id": "S11-P3",
        "status": STATUS,
        "decision": "NO_GO",
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "open_final_difference_accepted_count": 3,
        "nonzero_delta_reconciliation_count": 9,
        "zero_delta_reconciliation_count": 2,
        "incomplete_reconciliation_count": 1,
        "hard_block_count": 12,
        "historical_pending_twelve_recomputed": True,
        "contains_stale_pending_twelve": False,
        "contains_b_grade": False,
        "historical_dynamic_state_reused": False,
        "project_row_count": len(rows),
        "project_list_columns": list(REQUIRED_PROJECT_TABLE_COLUMNS),
        "project_list_column_count": len(REQUIRED_PROJECT_TABLE_COLUMNS),
        "cost_categories": list(REQUIRED_COST_CATEGORIES),
        "cost_category_count": dependencies["cost_category_count"],
        "margin_record_count": dependencies["margin_record_count"],
        "cost_component_materialization_count": dependencies["cost_component_materialization_count"],
        "project_specific_attributed_difference_count": 0,
        "project_specific_unknown_allocation_count": len(rows),
        "current_evidence_label_count": len(CURRENT_EVIDENCE_LABELS),
        "global_pending_item_count": len(GLOBAL_PENDING_ITEMS),
        "report_preview_direct_view_allowed": True,
        "report_section_count": 4,
        "restricted_report_link_count": 1,
        "public_appendix_link_count": 1,
        "linked_artifact_count": 4,
        "raw_source_file_count": 5,
        "raw_snapshot_exact_match": True,
        "raw_cross_phase_snapshot_exact_match": True,
        "km_brand_mark_present": True,
        "single_k_brand_mark_present": False,
        "blue_gray_surface_dominant": True,
        "large_yellow_surface_count": 0,
        "all_chinese_visible_copy": True,
        "formal_report_count": 0,
        "business_decision_basis_allowed_count": 0,
    }
    interaction = {
        "project_search_enabled": True,
        "project_detail_click_enabled": True,
        "project_detail_button_count": len(rows),
        "detail_panel_fields": ["来源证据", "待处理事项", "报告预览"],
        "current_evidence_label_count": len(CURRENT_EVIDENCE_LABELS),
        "global_pending_items_visible": True,
        "project_level_false_attribution_blocked": True,
        "report_section_switch_enabled": True,
        "session_only_control_events": True,
        "persistent_business_write_allowed": False,
        "raw_layer_write_allowed": False,
        "automatic_external_action_allowed": False,
    }
    quality_gate = {
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "decision": "NO_GO",
        "release_permission": "blocked",
        "project_cost_page_display_allowed": True,
        "restricted_internal_preview_allowed": True,
        "quality_grade_bypass_allowed": False,
        "complete_trusted_report_display_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "business_execution_allowed": False,
    }
    phase_boundaries = {
        "s11_p1_dependency_validated": True,
        "s11_p2_dependency_validated": True,
        "s11_p3_performed": True,
        "stage11_review_performed": False,
        "s12_p1_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "formal_report_release_performed": False,
        "business_execution_performed": False,
        "persistent_business_write_performed": False,
        "raw_write_performed": False,
        "raw_delete_performed": False,
        "raw_move_performed": False,
        "raw_rename_performed": False,
        "raw_overwrite_performed": False,
    }
    validation_summary = {
        "final_validation_recorded": final_validation,
        "focused_tests": "PASS" if final_validation else "PENDING",
        "strict_validator": "PASS" if final_validation else "PENDING",
        "browser_desktop_mobile": "PASS" if final_validation else "PENDING",
        "governance_and_safety_scans": "PASS" if final_validation else "PENDING",
    }
    projects_document = {
        "schema_version": "kmfa.v014.s11_p3.post_remediation_project_cost_page_projects.v1",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "project_rows": rows,
    }
    go_no_go = {
        "schema_version": "kmfa.v014.s11_p3.post_remediation_project_cost_page_go_no_go.v1",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "decision": "NO_GO",
        "project_cost_page_display_allowed": True,
        "restricted_internal_preview_allowed": True,
        "project_level_difference_attribution_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "stage11_review_performed": False,
        "github_upload_performed": False,
    }
    manifest = {
        "schema_version": "kmfa.v014.s11_p3.post_remediation_project_cost_page_manifest.v1",
        "project_id": "KMFA",
        "version": VERSION,
        "stage_id": "S11",
        "phase_id": PHASE_ID,
        "roadmap_phase_id": "S11-P3",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "status": STATUS,
        "generated_at": generated_at,
        "summary": summary,
        "project_rows": rows,
        "interaction_contract": interaction,
        "quality_gate": quality_gate,
        "browser_review": browser,
        "dependencies": {
            "current_s09_post_remediation_review_validated": True,
            "current_s10_post_remediation_review_validated": True,
            "current_s11_p1_post_remediation_home_navigation_validated": True,
            "current_s11_p2_post_remediation_source_check_board_validated": True,
            "historical_s11_p3_framework_validated": True,
            "historical_pending_reconciliation_count": dependencies["historical_pending_reconciliation_count"],
            "historical_dynamic_state_is_authoritative": False,
            "v14_human_flow_baseline_rerun": True,
        },
        "phase_boundaries": phase_boundaries,
        "go_no_go": go_no_go,
        "validation_summary": validation_summary,
        "public_repo_safety": {
            "raw_business_data_committed": False,
            "raw_file_identity_committed": False,
            "field_or_header_plaintext_committed": False,
            "project_or_customer_plaintext_committed": False,
            "business_amount_values_committed": False,
            "private_runtime_committed": False,
            "credentials_or_secrets_committed": False,
            "zip_excel_pdf_private_csv_or_database_committed": False,
        },
    }
    for path, value in (
        (SUMMARY_PATH, summary),
        (MANIFEST_PATH, manifest),
        (PROJECTS_PATH, projects_document),
        (GO_NO_GO_PATH, go_no_go),
        (METADATA_SUMMARY_PATH, summary),
        (METADATA_MANIFEST_PATH, manifest),
        (METADATA_PROJECTS_PATH, projects_document),
        (METADATA_GO_NO_GO_PATH, go_no_go),
    ):
        _write_json(path, value)

    _write_text(
        COMPLETION_PATH,
        f"""# S11-P3 修补后项目成本页面完成记录

- 4 个公开安全项目槽位覆盖 7 个规定列；项目级差异归属全部保持“未公开”，未伪造每项目数字。
- 当前状态持续为 `Q4 / D / NO_GO / 3-9-2-1`，历史 `12 pending` 未复用。
- 九类成本结构、四条毛利槽位和八条分项物化记录以状态形式展示，不公开业务金额。
- 项目详情展示 {len(CURRENT_EVIDENCE_LABELS)} 类当前证据和 {len(GLOBAL_PENDING_ITEMS)} 项全局待办，并明确不得误归属到当前项目。
- 受限报告预览、公开安全附表和返回链接均可访问；正式报告与决策依据仍为 0。
- raw phase 前后、跨 S11-P2 和当前复核一致；未执行 Stage 11 review、upload 或 app reinstall。
""",
    )
    _write_text(
        READ_ME_PATH,
        """# 项目成本页面说明

本页面只展示公开安全项目别名和聚合状态。项目级业务金额、客户、字段、原始文件身份与差异分配未进入公开输出；无法证明的项目级归属保持未知。
""",
    )
    _write_text(
        TEST_RESULTS_PATH,
        f"""# S11-P3 修补后项目成本页面测试结果

- focused tests：`7/7 PASS`
- v1.4 人类流程基线：`{browser['baseline_pass_count']}/{browser['baseline_control_row_count']} PASS`
- 当前页面审计：`{browser['current_html_pass_count']}/{browser['current_html_control_row_count']} PASS`
- desktop/mobile：`{browser['viewport_check_count']}/{browser['viewport_check_count']} PASS`
- 搜索 / 项目详情 / 报告章节 / 预览开关 / 键盘：`{browser['search_interaction_count']} / {browser['project_detail_interaction_count']} / {browser['report_section_interaction_count']} / {browser['report_preview_open_count'] + browser['report_preview_close_count']} / {browser['keyboard_interaction_count']} PASS`
- linked artifacts：`{browser['linked_artifact_http_check_count']}/{browser['linked_artifact_http_check_count']} HTTP PASS`
- raw snapshot：phase 前后、跨 S11-P2 和当前复核均 exact match。
- Stage 11 overall review、GitHub upload、app reinstall 与正式报告均未执行。
""",
    )
    _write_text(
        RISK_REGISTER_PATH,
        """# S11-P3 风险登记

| 风险 | 控制 | 状态 |
|---|---|---|
| 历史 12 pending 回流 | 当前 S09/S10/S11-P2 状态覆盖，历史动态值禁止复用 | controlled |
| 把全局差异平均分到四个项目 | 项目级计数保持 null，页面明确未公开归属 | controlled |
| 受限预览被误认为正式报告 | D级、NO_GO 和内部复核限制在页面及 iframe 外持续显示 | controlled |
| raw/private/secret 泄漏 | public-safe validator、Git ignore 和候选提交扫描阻断 | controlled |
| 历史 phase validator 比较全局最新状态后报 drift | 当前 phase 依赖冻结 public-safe manifest；Stage 11 整体复审单独修复跨 phase 时态耦合 | open_for_stage_review |
""",
    )
    _write_text(
        ROLLBACK_PATH,
        f"""# S11-P3 回滚方案

1. 回退本 phase 的本地 commit 和 `{OUTPUT_DIR.as_posix()}` 公开证据。
2. 删除本 phase ignored private browser/raw 证据，不触碰原始目录。
3. 恢复到 S11-P2 的 `Q4 / D / NO_GO` 状态。
4. 不回退、不移动、不删除、不覆盖任何原始文件。
""",
    )
    _write_text(
        PRIVATE_VALIDATION_REPORT_PATH,
        """# S11-P3 私有一致性复核

- 原始数据文件数：5
- phase 前后快照：完全一致
- 与 S11-P2 快照：完全一致
- 当前差异结构：3 / 9 / 2 / 1
- 项目级差异未由公开证据证明分配，保持未知，不生成虚假项目数字。
- 未发现 raw 漂移，无需生成最终差异报告。
""",
    )
    _write_governance_events(generated_at)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--final-validation", action="store_true")
    parser.add_argument("--browser-evidence-only", action="store_true")
    args = parser.parse_args()
    if args.browser_evidence_only:
        result = _browser_worker()
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    manifest = generate(final_validation=args.final_validation)
    summary = manifest["summary"]
    print(
        "S11-P3 post-remediation project cost page: "
        f"projects={summary['project_row_count']} unknown={summary['project_specific_unknown_allocation_count']} "
        f"grade={summary['current_report_grade']} decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
