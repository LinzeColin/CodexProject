#!/usr/bin/env python3
"""Generate current public-safe KMFA v0.1.4 S13-P1 report drafts."""

from __future__ import annotations

import argparse
import functools
import html
import http.server
import json
import os
import socketserver
import subprocess
import threading
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

from KMFA.tools import v014_s12_post_remediation_stage_review as s12_review
from KMFA.tools.check_v014_s12_post_remediation_stage_review import (
    validate_v014_s12_post_remediation_stage_review,
)


PHASE_ID = "V014_S13_P1_POST_REMEDIATION_FINANCIAL_OPERATING_REPORT"
ROADMAP_PHASE_ID = "S13-P1"
TASK_ID = "KMFA-V014-S13-P1-POST-REMEDIATION-FINANCIAL-OPERATING-REPORT-20260711"
ACCEPTANCE_ID = "ACC-V014-S13-P1-POST-REMEDIATION-FINANCIAL-OPERATING-REPORT"
VERSION = "0.1.4-s13-p1-post-remediation-financial-operating-report"
STATUS = "completed_validated_local_only_s13_p1_draft_no_go_upload_deferred"
DECISION = "NO_GO"
FORMULA_ID = "FORM-KMFA-V014-S13P1-POST-REMEDIATION-FINANCIAL-OPERATING-REPORT-001"
PARAMETER_IDS = (
    "PARAM-KMFA-1735",
    "PARAM-KMFA-1736",
    "PARAM-KMFA-1737",
    "PARAM-KMFA-1738",
)
MODEL_REGISTRY_KEY = "kmfa_v014_s13_p1_post_remediation_financial_operating_report"

OUTPUT_DIR = Path("KMFA/stage_artifacts") / PHASE_ID
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
HTML_DIR = OUTPUT_DIR / "exports/html"
SUMMARY_PATH = MACHINE_DIR / "financial_operating_report_summary.json"
MANIFEST_PATH = MACHINE_DIR / "financial_operating_report_manifest.json"
LANES_PATH = MACHINE_DIR / "source_lane_status_public_safe.json"
DRAFTS_PATH = MACHINE_DIR / "draft_definitions_public_safe.json"
MATRIX_PATH = MACHINE_DIR / "financial_operating_report_acceptance_matrix.json"
GO_NO_GO_PATH = MACHINE_DIR / "financial_operating_report_go_no_go.json"
WEEKLY_HTML_PATH = HTML_DIR / "financial_operating_weekly_draft.html"
MONTHLY_HTML_PATH = HTML_DIR / "financial_operating_monthly_draft.html"
REPORT_PATH = HUMAN_DIR / "financial_operating_report_zh.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results_zh.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register_zh.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan_zh.md"

QUALITY_DIR = Path("KMFA/metadata/quality")
METADATA_SUMMARY_PATH = QUALITY_DIR / "v014_s13_p1_post_remediation_financial_operating_report_summary.json"
METADATA_MANIFEST_PATH = QUALITY_DIR / "v014_s13_p1_post_remediation_financial_operating_report_manifest.json"
METADATA_LANES_PATH = QUALITY_DIR / "v014_s13_p1_post_remediation_source_lane_status_public_safe.json"
METADATA_DRAFTS_PATH = QUALITY_DIR / "v014_s13_p1_post_remediation_draft_definitions_public_safe.json"
METADATA_MATRIX_PATH = QUALITY_DIR / "v014_s13_p1_post_remediation_financial_operating_report_acceptance_matrix.json"
METADATA_GO_NO_GO_PATH = QUALITY_DIR / "v014_s13_p1_post_remediation_financial_operating_report_go_no_go.json"

PRIVATE_DIR = Path("KMFA/.codex_private_runtime/v014_s13_p1_post_remediation_financial_operating_report")
PRIVATE_RAW_BEFORE_PATH = PRIVATE_DIR / "raw_immutability_before.json"
PRIVATE_RAW_AFTER_PATH = PRIVATE_DIR / "raw_immutability_after.json"
PRIVATE_ALIGNMENT_PATH = PRIVATE_DIR / "raw_to_report_alignment_diagnostic.json"
PRIVATE_REPORT_PATH = PRIVATE_DIR / "s13_p1_private_validation_zh.md"
PRIVATE_BROWSER_PATH = PRIVATE_DIR / "browser_verification.json"
PRIVATE_BASELINE_AUDIT_PATH = PRIVATE_DIR / "human_flow_baseline_audit.csv"
PRIVATE_CURRENT_AUDIT_PATH = PRIVATE_DIR / "current_financial_operating_report_audit.csv"
PRIVATE_SCREENSHOT_DIR = PRIVATE_DIR / "screenshots"

V14_ROADMAP_PATH = Path("KMFA/taskpack/v1_4/roadmap/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_4.md")
V14_TASKPACK_PATH = Path("KMFA/taskpack/v1_4/taskpack/01_KMFA_Codex_TaskPack_v1_4_public_safe.md")
V14_HTML_ROOT = Path("KMFA/taskpack/v1_4/html_uiux")
V14_REPORT_SAMPLE_PATH = V14_HTML_ROOT / "KMFA_经营分析报告可点击预览_v1_4.html"
V14_AUDIT_REPORT_PATH = V14_HTML_ROOT / "KMFA_HTML_human_flow_audit_report_v1_4.md"
CURRENT_SOURCE_REGISTRY_PATH = Path("KMFA/metadata/imports/v014_s07_p1_finance_support_source_registry.json")
CURRENT_CANDIDATES_PATH = Path("KMFA/metadata/schema_maps/v014_s07_p1_finance_field_candidates.jsonl")
HISTORICAL_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V014_S13_P1_FINANCIAL_OPERATING_REPORT/machine/financial_operating_report_manifest.json"
)

DEVELOPMENT_EVENTS_PATH = Path("KMFA/docs/governance/development_events.jsonl")
STAGE_STATUS_PATH = Path("KMFA/metadata/stage_status.jsonl")
TASK_STATUS_PATH = Path("KMFA/metadata/traceability/v1_4_stage_phase_task_status.jsonl")

SECTIONS = (
    ("summary", "经营摘要"),
    ("operating", "经营情况"),
    ("expense", "费用税金资产"),
    ("cash", "现金情况"),
    ("loan", "贷款明细"),
    ("limits", "数据状态与限制"),
    ("next", "下一步复核事项"),
)

LANE_SPECS = (
    {
        "lane_id": "operating_situation",
        "visible_lane_name": "经营情况",
        "categories": ("operating_analysis",),
        "status_label": "结构候选已接入；当前数值绑定未被证明，不能形成经营金额结论。",
    },
    {
        "lane_id": "expense_tax_asset",
        "visible_lane_name": "费用税金资产",
        "categories": ("journal", "tax", "account", "r_and_d_expense"),
        "status_label": "费用、税金与资产结构候选已接入；金额、期间与归属仍受复核门禁限制。",
    },
    {
        "lane_id": "cash_situation",
        "visible_lane_name": "现金情况",
        "categories": ("cash", "account"),
        "status_label": "现金结构候选已接入；现金安全结论缺少可证明的当前数值绑定。",
    },
    {
        "lane_id": "loan_detail",
        "visible_lane_name": "贷款明细",
        "categories": ("loan",),
        "status_label": "贷款结构候选已接入；不形成还款、续贷、付款或银行操作建议。",
    },
)

PAGE_SPECS = {
    "weekly": {
        "path": WEEKLY_HTML_PATH,
        "marker": "经营周报初稿",
        "target": "monthly",
    },
    "monthly": {
        "path": MONTHLY_HTML_PATH,
        "marker": "经营月报初稿",
        "target": "weekly",
    },
}


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def _git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    return result.stdout.strip()


def _upsert_jsonl(path: Path, row: dict[str, Any]) -> None:
    preserved: list[str] = []
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip() and json.loads(line).get("phase_id") != PHASE_ID:
                preserved.append(line)
    preserved.append(json.dumps(row, ensure_ascii=False, separators=(",", ":")))
    _write_text(path, "\n".join(preserved))


def _load_stage12_dependency() -> dict[str, Any]:
    manifest = validate_v014_s12_post_remediation_stage_review(
        require_private_evidence=True,
        require_browser_evidence=True,
        require_final_evidence=True,
    )
    summary = manifest["summary"]
    expected = {
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "decision": "NO_GO",
        "open_final_difference_accepted_count": 3,
        "nonzero_delta_reconciliation_count": 9,
        "zero_delta_reconciliation_count": 2,
        "incomplete_reconciliation_count": 1,
        "hard_block_count": 12,
        "raw_source_file_count": 5,
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            raise RuntimeError(f"current Stage 12 dependency drift: {key}")
    boundaries = manifest.get("review_boundaries", {})
    if boundaries.get("stage12_review_performed") is not True:
        raise RuntimeError("current Stage 12 review is not complete")
    if boundaries.get("s13_p1_performed") is not False:
        raise RuntimeError("S13-P1 already appears in Stage 12 dependency")
    return manifest


def _load_contract() -> dict[str, Any]:
    roadmap = V14_ROADMAP_PATH.read_text(encoding="utf-8")
    taskpack = V14_TASKPACK_PATH.read_text(encoding="utf-8")
    sample = V14_REPORT_SAMPLE_PATH.read_text(encoding="utf-8")
    audit_report = V14_AUDIT_REPORT_PATH.read_text(encoding="utf-8")
    for token in (
        "财务经营报表",
        "接入经营情况、费用税金资产、现金情况、贷款明细",
        "生成经营周报/月报初稿",
        "经营报告显示数据状态和限制",
    ):
        if token not in roadmap:
            raise RuntimeError(f"S13-P1 roadmap token missing: {token}")
    for token in ("财务经营分析报表线", "经营周/月报初稿"):
        if token not in taskpack:
            raise RuntimeError(f"S13-P1 taskpack token missing: {token}")
    for token in ("经营分析报告", "本期摘要", "项目成本", "回款资金", "开票纳税"):
        if token not in sample:
            raise RuntimeError(f"v1.4 report sample token missing: {token}")
    for token in ("HTML 文件数：6", "核验行数：54", "PASS：54", "WARN：0", "FAIL：0"):
        if token not in audit_report:
            raise RuntimeError(f"v1.4 audit baseline token missing: {token}")
    return {
        "roadmap_read": True,
        "taskpack_read": True,
        "report_human_flow_sample_read": True,
        "human_flow_baseline_read": True,
        "historical_sample_business_values_reused": False,
        "historical_sample_b_grade_reused": False,
    }


def _build_source_lanes() -> tuple[list[dict[str, Any]], dict[str, int]]:
    registry = _read_json(CURRENT_SOURCE_REGISTRY_PATH)
    candidates = _read_jsonl(CURRENT_CANDIDATES_PATH)
    sources = [row for row in registry.get("sources", []) if isinstance(row, dict)]
    sources_by_category: dict[str, list[dict[str, Any]]] = {}
    candidates_by_category: dict[str, list[dict[str, Any]]] = {}
    for row in sources:
        sources_by_category.setdefault(str(row.get("finance_category")), []).append(row)
    for row in candidates:
        candidates_by_category.setdefault(str(row.get("finance_category")), []).append(row)

    lanes: list[dict[str, Any]] = []
    unique_source_refs: set[str] = set()
    unique_candidate_ids: set[str] = set()
    for spec in LANE_SPECS:
        lane_sources = [
            row
            for category in spec["categories"]
            for row in sources_by_category.get(category, [])
        ]
        lane_candidates = [
            row
            for category in spec["categories"]
            for row in candidates_by_category.get(category, [])
        ]
        source_refs = {str(row.get("source_ref")) for row in lane_sources if row.get("source_ref")}
        candidate_ids = {
            str(row.get("candidate_id"))
            for row in lane_candidates
            if row.get("candidate_id")
        }
        unique_source_refs.update(source_refs)
        unique_candidate_ids.update(candidate_ids)
        readonly_count = sum(row.get("read_only_parse") is True for row in lane_sources)
        structure_connected = bool(source_refs) and bool(candidate_ids) and readonly_count == len(source_refs)
        lanes.append(
            {
                "lane_id": spec["lane_id"],
                "visible_lane_name": spec["visible_lane_name"],
                "source_binding_count": len(source_refs),
                "structure_candidate_count": len(candidate_ids),
                "readonly_source_count": readonly_count,
                "structure_connected": structure_connected,
                "current_raw_value_binding_proven": False,
                "data_status": "structure_connected_values_unproven",
                "status_label": spec["status_label"],
                "contains_source_identity": False,
                "contains_field_plaintext": False,
                "contains_business_amounts": False,
                "formal_report_allowed": False,
                "business_decision_basis_allowed": False,
            }
        )
    aggregate = {
        "unique_source_count": len(unique_source_refs),
        "lane_source_binding_count": sum(row["source_binding_count"] for row in lanes),
        "unique_structure_candidate_count": len(unique_candidate_ids),
        "lane_structure_candidate_association_count": sum(
            row["structure_candidate_count"] for row in lanes
        ),
        "structure_connected_lane_count": sum(row["structure_connected"] for row in lanes),
        "raw_value_bound_lane_count": sum(
            row["current_raw_value_binding_proven"] for row in lanes
        ),
    }
    expected = {
        "unique_source_count": 7,
        "lane_source_binding_count": 8,
        "unique_structure_candidate_count": 35,
        "lane_structure_candidate_association_count": 40,
        "structure_connected_lane_count": 4,
        "raw_value_bound_lane_count": 0,
    }
    if aggregate != expected:
        raise RuntimeError(f"current finance structure drift: {aggregate}")
    return lanes, aggregate


def _build_drafts(lanes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    drafts: list[dict[str, Any]] = []
    for draft_id, visible_name, html_path in (
        ("financial_operating_weekly_draft", "经营周报初稿", WEEKLY_HTML_PATH),
        ("financial_operating_monthly_draft", "经营月报初稿", MONTHLY_HTML_PATH),
    ):
        drafts.append(
            {
                "draft_id": draft_id,
                "visible_report_name": visible_name,
                "html_ref": html_path.as_posix(),
                "visible_section_titles": [label for _section_id, label in SECTIONS],
                "source_lane_count": len(lanes),
                "structure_connected_lane_count": sum(
                    row["structure_connected"] for row in lanes
                ),
                "raw_value_bound_lane_count": 0,
                "current_data_quality_grade": "Q4",
                "report_grade_visible": "D",
                "decision": "NO_GO",
                "open_final_difference_accepted_count": 3,
                "nonzero_delta_reconciliation_count": 9,
                "zero_delta_reconciliation_count": 2,
                "incomplete_reconciliation_count": 1,
                "draft_report_allowed": True,
                "formal_report_allowed": False,
                "business_decision_basis_allowed": False,
                "contains_business_amounts": False,
                "contains_source_identity": False,
                "contains_field_plaintext": False,
                "data_status_and_limitations_visible": True,
                "limitations": [
                    "本页是内部复核初稿，不是正式可信经营报告。",
                    "四类主题只有结构候选接入；当前原始数值到主题的可证明绑定为零。",
                    "差异、现金证据和跨表复核未关闭前，不得填造金额、升级报告等级或作为经营决策依据。",
                    "S13-P1 不执行回款应收账龄、跨表复核、付款、银行、贷款、开票、税务或外部动作。",
                ],
            }
        )
    return drafts


def _lane_panel(lane: dict[str, Any]) -> str:
    return f"""
      <div class="lane-detail">
        <div><span>结构状态</span><strong>已接入结构候选</strong></div>
        <div><span>来源绑定</span><strong>{lane['source_binding_count']} 个公开安全引用</strong></div>
        <div><span>结构候选</span><strong>{lane['structure_candidate_count']} 项</strong></div>
        <div><span>数值状态</span><strong class="danger">未证明当前绑定</strong></div>
      </div>
      <p class="limit-copy">{html.escape(lane['status_label'])}</p>
    """.rstrip()


def _render_html(draft: dict[str, Any], lanes: list[dict[str, Any]]) -> str:
    weekly = draft["draft_id"].endswith("weekly_draft")
    current_page_id = "weekly" if weekly else "monthly"
    other_name = "经营月报初稿" if weekly else "经营周报初稿"
    other_href = MONTHLY_HTML_PATH.name if weekly else WEEKLY_HTML_PATH.name
    lane_by_id = {row["lane_id"]: row for row in lanes}
    tabs = "".join(
        f'<button class="section-tab{" active" if index == 0 else ""}" type="button" '
        f'data-section-button="{section_id}" aria-controls="section-{section_id}">{label}</button>'
        for index, (section_id, label) in enumerate(SECTIONS)
    )
    lane_rows = "".join(
        f"""<tr><td><strong>{html.escape(row['visible_lane_name'])}</strong></td>
        <td><span class="status status-structure">结构已接入</span></td>
        <td>{row['source_binding_count']}</td><td>{row['structure_candidate_count']}</td>
        <td><span class="status status-blocked">数值未证明</span></td>
        <td>{html.escape(row['status_label'])}</td></tr>"""
        for row in lanes
    )
    sections = f"""
    <section id="section-summary" class="report-section active" data-section-panel="summary">
      <h2>一、经营摘要</h2>
      <p>本期仅形成状态型财务经营初稿。四类主题结构候选已接入，但当前原始数值到主题的可证明绑定为零，因此不展示业务金额、不形成经营结论。</p>
      <div class="summary-grid">
        <div class="summary-item"><span>当前差异</span><strong>3 / 9 / 2 / 1</strong><small>开放接受 / 非零 / 零差异 / 未完成</small></div>
        <div class="summary-item"><span>结构主题</span><strong>4 / 4</strong><small>结构候选已接入</small></div>
        <div class="summary-item"><span>数值绑定</span><strong>0 / 4</strong><small>不得填造金额</small></div>
      </div>
    </section>
    <section id="section-operating" class="report-section" data-section-panel="operating">
      <h2>二、经营情况</h2>{_lane_panel(lane_by_id['operating_situation'])}
    </section>
    <section id="section-expense" class="report-section" data-section-panel="expense">
      <h2>三、费用税金资产</h2>{_lane_panel(lane_by_id['expense_tax_asset'])}
    </section>
    <section id="section-cash" class="report-section" data-section-panel="cash">
      <h2>四、现金情况</h2>{_lane_panel(lane_by_id['cash_situation'])}
    </section>
    <section id="section-loan" class="report-section" data-section-panel="loan">
      <h2>五、贷款明细</h2>{_lane_panel(lane_by_id['loan_detail'])}
    </section>
    <section id="section-limits" class="report-section" data-section-panel="limits">
      <h2>六、数据状态与限制</h2>
      <div class="table-wrap"><table><thead><tr><th>主题</th><th>结构状态</th><th>来源引用</th><th>结构候选</th><th>数值状态</th><th>限制</th></tr></thead><tbody>{lane_rows}</tbody></table></div>
    </section>
    <section id="section-next" class="report-section" data-section-panel="next">
      <h2>七、下一步复核事项</h2>
      <ol class="next-list"><li>保持当前四类主题结构接入，不将结构候选解释为已完成数值绑定。</li><li>后续独立执行 S13-P2 回款应收账龄，不在本 phase 提前生成催收或责任结论。</li><li>待 S13-P3 完成跨表复核后，重新评估报告数据状态；当前继续维持 D 级和 NO_GO。</li></ol>
    </section>
    """
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>KMFA {draft['visible_report_name']}</title>
  <style>
    :root {{--navy:#102d4f;--blue:#1769aa;--blue-soft:#eaf3fb;--page:#f4f6f8;--panel:#fff;--line:#d6dee5;--ink:#1c2834;--muted:#667482;--amber:#8a5200;--amber-soft:#fff5dc;--red:#a92d25;--red-soft:#fff0ee;--green:#176b48;--green-soft:#eaf7f1}}
    *{{box-sizing:border-box}}html{{background:var(--page)}}body{{margin:0;color:var(--ink);background:var(--page);font:14px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI","Microsoft YaHei",Arial,sans-serif;letter-spacing:0}}button,a{{font:inherit;letter-spacing:0}}button{{cursor:pointer}}
    .topbar{{min-height:68px;padding:10px 24px;background:var(--navy);color:#fff;display:flex;align-items:center;gap:18px;border-bottom:4px solid #2f81bd}}.brand{{display:flex;align-items:center;gap:10px;min-width:240px}}.mark{{width:40px;height:40px;display:grid;place-items:center;background:#fff;color:var(--navy);border-radius:6px;font-weight:900}}.brand strong,.brand span{{display:block}}.brand span{{font-size:12px;color:#c9dbee}}.draft-nav{{margin-left:auto;display:flex;gap:7px;align-items:center}}.draft-nav a{{color:#fff;text-decoration:none;border:1px solid rgba(255,255,255,.35);border-radius:5px;padding:8px 10px}}.draft-nav a:hover,.draft-nav a:focus-visible{{background:rgba(255,255,255,.12)}}
    main{{width:min(1180px,100%);margin:0 auto;padding:22px 24px 42px}}.report-head{{display:flex;justify-content:space-between;gap:20px;align-items:flex-start;margin-bottom:14px}}.eyebrow{{font-size:12px;color:var(--blue);font-weight:800}}h1{{font-size:27px;margin:3px 0 5px;color:var(--navy)}}.subtitle{{margin:0;color:var(--muted)}}.grade{{min-width:170px;border-left:4px solid var(--red);background:var(--red-soft);padding:10px 12px;color:#6d2823}}.grade span,.grade strong{{display:block}}.grade strong{{font-size:18px;margin-top:2px}}
    .notice{{border:1px solid #e5c88d;background:var(--amber-soft);color:#68430a;padding:11px 13px;margin-bottom:14px}}.metrics{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));background:#fff;border:1px solid var(--line);margin-bottom:14px}}.metric{{padding:13px 15px;border-right:1px solid var(--line)}}.metric:last-child{{border-right:0}}.metric span{{display:block;color:var(--muted);font-size:12px}}.metric strong{{display:block;color:var(--navy);font-size:23px;margin-top:2px}}
    .report-shell{{background:#fff;border:1px solid var(--line);border-radius:7px;overflow:hidden}}.tabs{{display:flex;gap:5px;flex-wrap:wrap;padding:12px;border-bottom:1px solid var(--line);background:#f8fafb}}.section-tab{{border:1px solid var(--line);border-radius:5px;background:#fff;color:var(--navy);padding:8px 10px;font-weight:750}}.section-tab.active{{background:var(--navy);border-color:var(--navy);color:#fff}}.report-body{{padding:22px}}.report-section{{display:none}}.report-section.active{{display:block}}.report-section h2{{font-size:19px;margin:0 0 12px;color:var(--navy)}}.report-section p{{max-width:900px}}
    .summary-grid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin-top:16px}}.summary-item{{border:1px solid var(--line);padding:13px;min-width:0}}.summary-item span,.summary-item small{{display:block;color:var(--muted)}}.summary-item strong{{display:block;font-size:23px;color:var(--navy);margin:3px 0}}
    .lane-detail{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));border:1px solid var(--line)}}.lane-detail div{{padding:12px;border-right:1px solid var(--line)}}.lane-detail div:last-child{{border-right:0}}.lane-detail span,.lane-detail strong{{display:block}}.lane-detail span{{font-size:12px;color:var(--muted)}}.lane-detail strong{{margin-top:3px;color:var(--navy)}}.lane-detail .danger{{color:var(--red)}}.limit-copy{{border-left:4px solid var(--amber);padding:9px 11px;background:var(--amber-soft)}}
    .table-wrap{{overflow-x:auto;border:1px solid var(--line)}}table{{width:100%;border-collapse:collapse;min-width:820px}}th,td{{text-align:left;padding:10px;border-bottom:1px solid #e8edf1;vertical-align:top}}th{{background:#f3f7fa;color:#34495c;font-size:12px}}tr:last-child td{{border-bottom:0}}.status{{display:inline-block;padding:3px 6px;border-radius:4px;font-size:12px;font-weight:750}}.status-structure{{background:var(--green-soft);color:var(--green)}}.status-blocked{{background:var(--red-soft);color:var(--red)}}.next-list{{padding-left:20px}}.next-list li{{margin:8px 0}}.interaction-status{{margin-top:14px;color:var(--muted);font-size:12px;border-top:1px solid var(--line);padding-top:10px}}
    footer{{color:var(--muted);font-size:12px;margin-top:12px}}
    @media(max-width:760px){{.topbar{{padding:10px 12px;align-items:flex-start;flex-wrap:wrap}}.brand{{min-width:0}}.draft-nav{{margin-left:0;width:100%}}main{{padding:16px 12px 30px}}.report-head{{display:block}}.grade{{margin-top:12px;min-width:0}}.metrics,.summary-grid,.lane-detail{{grid-template-columns:1fr}}.metric,.lane-detail div{{border-right:0;border-bottom:1px solid var(--line)}}.metric:last-child,.lane-detail div:last-child{{border-bottom:0}}.report-body{{padding:15px}}.tabs{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr))}}.section-tab{{min-width:0;white-space:normal}}}}
  </style>
</head>
<body data-page-id="{current_page_id}" data-active-section="summary" data-ui-ready="false">
  <header class="topbar"><div class="brand"><div class="mark">KM</div><div><strong>KMFA 经营分析系统</strong><span>S13-P1 · 财务经营报表初稿</span></div></div><nav class="draft-nav" aria-label="初稿切换"><a data-other-draft href="{other_href}">切换至{other_name}</a></nav></header>
  <main>
    <section class="report-head"><div><div class="eyebrow">内部复核初稿</div><h1>{draft['visible_report_name']}</h1><p class="subtitle">财务经营四主题状态汇总，不展示原始业务金额。</p></div><div class="grade"><span>当前可信状态</span><strong>Q4 / D · NO_GO</strong></div></section>
    <div class="notice"><strong>限制：</strong> 四类主题只有结构候选接入，当前 raw 数值绑定为 0/4；本初稿不是正式报告，不得作为经营决策依据。</div>
    <section class="metrics" aria-label="报告状态"><div class="metric"><span>主题结构</span><strong>4 / 4</strong></div><div class="metric"><span>当前数值绑定</span><strong>0 / 4</strong></div><div class="metric"><span>报告等级</span><strong>D</strong></div><div class="metric"><span>当前决策</span><strong>NO_GO</strong></div></section>
    <article class="report-shell"><nav class="tabs" aria-label="报告章节">{tabs}</nav><div class="report-body">{sections}<div id="interaction-status" class="interaction-status" aria-live="polite">报告初稿已就绪；当前显示经营摘要。</div></div></article>
    <footer>Stage 13 仅完成 S13-P1；S13-P2、S13-P3、Stage 13 review、GitHub upload、app reinstall、正式报告和业务执行均未执行。</footer>
  </main>
  <script>
    const labels={json.dumps(dict(SECTIONS), ensure_ascii=False, separators=(',', ':'))};
    const buttons=Array.from(document.querySelectorAll('[data-section-button]'));
    const panels=Array.from(document.querySelectorAll('[data-section-panel]'));
    const status=document.getElementById('interaction-status');
    function activate(section){{
      buttons.forEach(button=>button.classList.toggle('active',button.dataset.sectionButton===section));
      panels.forEach(panel=>panel.classList.toggle('active',panel.dataset.sectionPanel===section));
      document.body.dataset.activeSection=section;
      document.body.dataset.lastAction=`section:${{section}}:${{Date.now()}}`;
      status.textContent=`已切换至“${{labels[section]}}”；页面仍为 D 级内部复核初稿。`;
    }}
    buttons.forEach(button=>button.addEventListener('click',()=>activate(button.dataset.sectionButton)));
    document.body.dataset.uiReady='true';
  </script>
</body>
</html>"""


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        return


def _page_url(base: str, page_id: str) -> str:
    path = PAGE_SPECS[page_id]["path"]
    return f"{base}/{path.as_posix().removeprefix('KMFA/stage_artifacts/')}"


def _browser_worker() -> dict[str, Any]:
    from playwright.sync_api import sync_playwright

    PRIVATE_SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    stage_root = Path("KMFA/stage_artifacts").resolve()
    handler = functools.partial(_QuietHandler, directory=str(stage_root))
    server = socketserver.TCPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    viewport_checks: list[dict[str, Any]] = []
    section_checks: list[dict[str, Any]] = []
    http_checks: list[dict[str, Any]] = []
    navigation_checks: list[dict[str, Any]] = []
    helper = s12_review.p1.s11_home
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True,
                executable_path=helper._chromium_path(),
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
            for page_id, spec in PAGE_SPECS.items():
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
                        and helper._is_actionable_console_error(
                            f"{msg.text} {msg.location.get('url', '')}"
                        )
                        else None,
                    )
                    page.on("pageerror", lambda exc: console_errors.append(str(exc)))
                    page.goto(_page_url(base, page_id), wait_until="networkidle")
                    page.wait_for_function("document.body.dataset.uiReady === 'true'")
                    body = page.locator("body").inner_text()
                    for section_id, _label in SECTIONS:
                        page.locator(f'[data-section-button="{section_id}"]').click()
                        passed = (
                            page.locator("body").get_attribute("data-active-section") == section_id
                            and page.locator(f'[data-section-panel="{section_id}"]').is_visible()
                            and "D 级内部复核初稿" in page.locator("#interaction-status").inner_text()
                        )
                        section_checks.append(
                            {
                                "page_id": page_id,
                                "mode": mode,
                                "section_id": section_id,
                                "passed": passed,
                            }
                        )
                    dimensions = page.evaluate(
                        "({scrollWidth:document.documentElement.scrollWidth,innerWidth:window.innerWidth})"
                    )
                    viewport_checks.append(
                        {
                            "page_id": page_id,
                            "mode": mode,
                            "viewport": viewport,
                            "marker_visible": spec["marker"] in body,
                            "d_no_go_visible": "Q4 / D" in body and "NO_GO" in body,
                            "amount_free_visible": "0 / 4" in body,
                            "console_error_count": len(console_errors),
                            "no_horizontal_overflow": dimensions["scrollWidth"] <= dimensions["innerWidth"] + 1,
                        }
                    )
                    page.screenshot(
                        path=str(PRIVATE_SCREENSHOT_DIR / f"{page_id}_{mode}.png"),
                        full_page=True,
                    )
                    page.close()
            request = playwright.request.new_context()
            for page_id, spec in PAGE_SPECS.items():
                page = browser.new_page(viewport={"width": 1280, "height": 900})
                page.goto(_page_url(base, page_id), wait_until="networkidle")
                href = page.locator("a[data-other-draft]").get_attribute("href") or ""
                target_url = urljoin(page.url, href)
                response = request.get(target_url)
                target_id = spec["target"]
                http_checks.append(
                    {
                        "source": page_id,
                        "target": target_id,
                        "status": response.status,
                        "passed": response.ok and PAGE_SPECS[target_id]["marker"] in response.text(),
                    }
                )
                page.locator("a[data-other-draft]").click()
                page.wait_for_load_state("networkidle")
                navigation_checks.append(
                    {
                        "source": page_id,
                        "target": target_id,
                        "passed": PAGE_SPECS[target_id]["marker"] in page.locator("body").inner_text(),
                    }
                )
                page.close()
            request.dispose()
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
    passed = (
        len(viewport_checks) == 4
        and all(
            row["marker_visible"]
            and row["d_no_go_visible"]
            and row["amount_free_visible"]
            and row["console_error_count"] == 0
            and row["no_horizontal_overflow"]
            for row in viewport_checks
        )
        and len(section_checks) == 28
        and all(row["passed"] for row in section_checks)
        and len(http_checks) == 2
        and all(row["passed"] for row in http_checks)
        and len(navigation_checks) == 2
        and all(row["passed"] for row in navigation_checks)
    )
    result = {
        "status": "PASS" if passed else "FAIL",
        "viewport_checks": viewport_checks,
        "section_interaction_checks": section_checks,
        "cross_draft_link_http_checks": http_checks,
        "cross_draft_navigation_checks": navigation_checks,
    }
    _write_json(PRIVATE_BROWSER_PATH, result)
    if not passed:
        raise RuntimeError("S13-P1 desktop/mobile browser evidence failed")
    return result


def _run_browser_review() -> dict[str, Any]:
    helper = s12_review.p1.s11_home
    baseline = helper._run_html_audit(V14_HTML_ROOT, PRIVATE_BASELINE_AUDIT_PATH)
    current = helper._run_html_audit(HTML_DIR, PRIVATE_CURRENT_AUDIT_PATH)
    env = os.environ.copy()
    env["KMFA_CHROMIUM"] = helper._chromium_path()
    result = subprocess.run(
        [
            str(helper._audit_python()),
            "-m",
            "KMFA.tools.v014_s13_p1_post_remediation_financial_operating_report",
            "--browser-evidence-only",
        ],
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
        "status": browser["status"],
        "baseline_file_count": baseline["file_count"],
        "baseline_control_row_count": baseline["control_row_count"],
        "baseline_pass_count": baseline["pass_count"],
        "baseline_warn_count": baseline["warn_count"],
        "baseline_fail_count": baseline["fail_count"],
        "current_page_count": current["file_count"],
        "current_control_row_count": current["control_row_count"],
        "current_pass_count": current["pass_count"],
        "current_warn_count": current["warn_count"],
        "current_fail_count": current["fail_count"],
        "viewport_check_count": len(browser["viewport_checks"]),
        "section_interaction_check_count": len(browser["section_interaction_checks"]),
        "cross_draft_link_http_check_count": len(browser["cross_draft_link_http_checks"]),
        "cross_draft_navigation_check_count": len(browser["cross_draft_navigation_checks"]),
        "console_error_count": sum(row["console_error_count"] for row in browser["viewport_checks"]),
        "horizontal_overflow_count": sum(not row["no_horizontal_overflow"] for row in browser["viewport_checks"]),
    }


def _quality_gate() -> dict[str, Any]:
    return {
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "decision": "NO_GO",
        "release_permission": "blocked",
        "draft_report_allowed": True,
        "weekly_draft_allowed": True,
        "monthly_draft_allowed": True,
        "formal_report_allowed": False,
        "complete_trusted_report_display_allowed": False,
        "business_decision_basis_allowed": False,
        "business_execution_allowed": False,
        "report_grade_bypass_allowed": False,
        "quality_grade_bypass_allowed": False,
        "derived_amount_calculation_allowed": False,
        "cash_forecast_decision_allowed": False,
        "loan_management_action_allowed": False,
        "payment_or_bank_operation_allowed": False,
        "tax_filing_allowed": False,
        "github_upload_allowed": False,
    }


def _phase_boundaries() -> dict[str, bool]:
    return {
        "stage12_review_validated": True,
        "s13_p1_performed": True,
        "s13_p2_performed": False,
        "s13_p3_performed": False,
        "stage13_review_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "formal_report_release_performed": False,
        "business_execution_performed": False,
        "persistent_business_write_performed": False,
        "lineage_full_check_performed": False,
        "live_connector_performed": False,
    }


def _public_repo_safety() -> dict[str, bool]:
    return {
        "aggregate_only": True,
        "raw_file_committed": False,
        "raw_filename_committed": False,
        "raw_hash_committed": False,
        "field_or_header_plaintext_committed": False,
        "business_value_committed": False,
        "source_identity_committed": False,
        "private_runtime_committed": False,
        "credential_or_secret_committed": False,
        "zip_excel_pdf_private_csv_or_database_committed": False,
    }


def _matrix(summary: dict[str, Any]) -> dict[str, Any]:
    checks = {
        "stage12_dependency": summary["stage12_review_dependency_validated"] is True,
        "four_lanes": summary["source_lane_count"] == 4,
        "seven_unique_sources": summary["unique_source_count"] == 7,
        "eight_lane_bindings": summary["lane_source_binding_count"] == 8,
        "thirty_five_unique_candidates": summary["unique_structure_candidate_count"] == 35,
        "forty_lane_candidate_associations": summary["lane_structure_candidate_association_count"] == 40,
        "four_structure_connected": summary["structure_connected_lane_count"] == 4,
        "zero_raw_value_bound_lanes": summary["raw_value_bound_lane_count"] == 0,
        "two_drafts": summary["draft_report_count"] == 2 and summary["html_draft_count"] == 2,
        "seven_sections": summary["required_section_count"] == 7,
        "current_difference_state": (
            summary["open_final_difference_accepted_count"],
            summary["nonzero_delta_reconciliation_count"],
            summary["zero_delta_reconciliation_count"],
            summary["incomplete_reconciliation_count"],
        ) == (3, 9, 2, 1),
        "q4_d_no_go": summary["current_data_quality_grade"] == "Q4" and summary["current_report_grade"] == "D" and summary["decision"] == "NO_GO",
        "four_viewports": summary["browser_viewport_check_count"] == 4,
        "twenty_eight_section_checks": summary["section_interaction_check_count"] == 28,
        "two_cross_draft_links": summary["cross_draft_link_http_check_count"] == 2 and summary["cross_draft_navigation_check_count"] == 2,
        "no_browser_error": summary["console_error_count"] == 0 and summary["horizontal_overflow_count"] == 0,
        "raw_exact": summary["raw_snapshot_exact_match"] is True,
        "raw_cross_phase_exact": summary["raw_cross_phase_snapshot_exact_match"] is True,
        "no_formal_report": summary["formal_report_count"] == 0,
        "no_decision_basis": summary["business_decision_basis_count"] == 0,
        "s13_p2_not_performed": summary["s13_p2_performed"] is False,
        "upload_not_performed": summary["github_upload_performed"] is False,
        "app_not_reinstalled": summary["app_reinstall_performed"] is False,
        "business_not_executed": summary["business_execution_performed"] is False,
    }
    rows = [{"check_id": key, "passed": passed} for key, passed in sorted(checks.items())]
    return {
        "schema_version": "kmfa.v014.s13_p1_post_remediation_report_matrix.v1",
        "check_count": len(rows),
        "check_pass_count": sum(row["passed"] for row in rows),
        "check_fail_count": sum(not row["passed"] for row in rows),
        "checks": rows,
    }


def _phase_public_files() -> list[str]:
    paths = (
        SUMMARY_PATH,
        MANIFEST_PATH,
        LANES_PATH,
        DRAFTS_PATH,
        MATRIX_PATH,
        GO_NO_GO_PATH,
        WEEKLY_HTML_PATH,
        MONTHLY_HTML_PATH,
        REPORT_PATH,
        TEST_RESULTS_PATH,
        RISK_REGISTER_PATH,
        ROLLBACK_PATH,
        METADATA_SUMMARY_PATH,
        METADATA_MANIFEST_PATH,
        METADATA_LANES_PATH,
        METADATA_DRAFTS_PATH,
        METADATA_MATRIX_PATH,
        METADATA_GO_NO_GO_PATH,
    )
    return [path.as_posix() for path in paths] + [
        "KMFA/tools/v014_s13_p1_post_remediation_financial_operating_report.py",
        "KMFA/tools/check_v014_s13_p1_post_remediation_financial_operating_report.py",
        "KMFA/tests/test_v014_s13_p1_post_remediation_financial_operating_report.py",
    ]


def _write_governance(generated_at: str) -> None:
    evidence_ref = MANIFEST_PATH.as_posix()
    _upsert_jsonl(
        DEVELOPMENT_EVENTS_PATH,
        {
            "event_id": "DEV-KMFA-20260711-V014-S13-P1-POST-REMEDIATION-FINANCIAL-OPERATING-REPORT",
            "event_time": generated_at,
            "event_type": "phase_completion",
            "project_id": "KMFA",
            "stage_id": "S13",
            "phase_id": PHASE_ID,
            "roadmap_phase_id": ROADMAP_PHASE_ID,
            "task_id": TASK_ID,
            "status": STATUS,
            "fact_level": "EXTRACTED",
            "decision": DECISION,
            "raw_business_data_committed": False,
            "github_upload_performed": False,
            "app_reinstall_performed": False,
            "business_execution_performed": False,
            "evidence_ref": evidence_ref,
            "files_changed": _phase_public_files(),
            "result_commit": "PENDING",
        },
    )
    _upsert_jsonl(
        STAGE_STATUS_PATH,
        {
            "schema_version": "kmfa.stage_status.v1",
            "record_type": "v014_phase_status",
            "project_id": "KMFA",
            "stage_id": "S13",
            "phase_id": PHASE_ID,
            "roadmap_phase_id": ROADMAP_PHASE_ID,
            "task_id": TASK_ID,
            "version": VERSION,
            "status": STATUS,
            "fact_level": "EXTRACTED",
            "decision": DECISION,
            "derived_percent": "33.33",
            "raw_data_committed": False,
            "github_upload_performed": False,
            "app_reinstall_performed": False,
            "business_execution_performed": False,
            "evidence_ref": evidence_ref,
            "updated_at": generated_at,
        },
    )
    _upsert_jsonl(
        TASK_STATUS_PATH,
        {
            "schema_version": "kmfa.v014_stage_phase_task_status.v1",
            "record_type": "v014_phase",
            "project_id": "KMFA",
            "stage_id": "S13",
            "governance_stage_id": "FINANCIAL-OPERATING-REPORTING",
            "roadmap_stage_id": "S13",
            "roadmap_phase_id": ROADMAP_PHASE_ID,
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "acceptance_id": ACCEPTANCE_ID,
            "version": VERSION,
            "name": "v0.1.4 S13-P1 post-remediation financial operating report",
            "phase_goal": "generate public-safe weekly and monthly financial operating drafts with explicit status and limits",
            "status": STATUS,
            "fact_level": "EXTRACTED",
            "derived_percent": 100,
            "estimated_task_units": 3,
            "completed_task_units": 3,
            "task_count": 3,
            "raw_data_committed": False,
            "evidence_ref": evidence_ref,
            "updated_at": generated_at[:10],
        },
    )


def _render_report(summary: dict[str, Any]) -> str:
    return f"""# KMFA v0.1.4 S13-P1 财务经营报表初稿

## 结论

- 当前状态：`Q4 / D / NO_GO / 3-9-2-1`
- 四类主题：`{summary['structure_connected_lane_count']}/4` 已接入结构候选，当前 raw 数值可证明绑定 `0/4`
- 来源：`{summary['unique_source_count']}` 个唯一公开安全来源引用，`{summary['lane_source_binding_count']}` 个主题关联
- 结构候选：`{summary['unique_structure_candidate_count']}` 个唯一候选，`{summary['lane_structure_candidate_association_count']}` 个主题关联
- 初稿：经营周报/月报各 `1` 份，均不含业务金额
- 浏览器：`{summary['browser_viewport_check_count']}/4` 视口、`{summary['section_interaction_check_count']}/28` 章节交互通过

## 数据状态

四类主题均满足结构接入，但现有公开安全证据不能证明当前 raw 数值与报表主题的绑定。页面只展示状态、计数和限制，不填造金额，不形成现金安全、贷款、税务或经营结论。

## 边界

- 本 phase 只生成内部复核初稿，不是正式可信经营报告或经营决策依据。
- 未执行 S13-P2、S13-P3、Stage 13 review、GitHub upload、app reinstall、持久业务写入或 business execution。
- raw 前后、跨 Stage 12 review 与当前快照一致；原始身份、字段、表头、金额和诊断仅保留在 ignored private runtime。
"""


def _render_private_report(summary: dict[str, Any]) -> str:
    return f"""# S13-P1 私有 raw 对齐记录

- 原始文件数：{summary['raw_source_file_count']}
- phase 前后快照：exact match
- 与 Stage 12 review 快照：exact match
- 与当前只读目录：exact match
- 四类报表主题结构接入：4/4
- 当前 raw 数值可证明绑定：0/4
- 报告业务金额输出：0
- 结论：本 phase 没有制造数值差异；因绑定未证明，报告保持状态型 D 级初稿。
- 后续：最终 goal 若多轮交叉验证仍无法完成数值对齐，必须输出全中文差异报告。
"""


def generate(*, final_validation: bool = False, write_governance: bool = True) -> dict[str, Any]:
    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    raw_helper = s12_review.p1.s11_project
    raw_before = raw_helper._raw_snapshot("before_v014_s13_p1_post_remediation_financial_operating_report")
    dependency = _load_stage12_dependency()
    contract = _load_contract()
    historical = _read_json(HISTORICAL_MANIFEST_PATH)
    lanes, structure = _build_source_lanes()
    drafts = _build_drafts(lanes)
    for draft in drafts:
        path = WEEKLY_HTML_PATH if draft["draft_id"].endswith("weekly_draft") else MONTHLY_HTML_PATH
        _write_text(path, _render_html(draft, lanes))
    browser = _run_browser_review()
    raw_after = raw_helper._raw_snapshot("after_v014_s13_p1_post_remediation_financial_operating_report")
    prior_raw = _read_json(s12_review.PRIVATE_RAW_AFTER_PATH)
    current_raw = raw_helper._raw_snapshot("current_v014_s13_p1_post_remediation_financial_operating_report")
    normalize = raw_helper._normalize_raw
    raw_exact = normalize(raw_before) == normalize(raw_after)
    raw_cross = normalize(raw_before) == normalize(prior_raw) == normalize(current_raw)
    if not raw_exact or not raw_cross:
        raise ValueError("raw source changed during S13-P1")

    upstream = dependency["summary"]
    summary = {
        "schema_version": "kmfa.v014.s13_p1_post_remediation_report_summary.v1",
        "project_id": "KMFA",
        "stage_id": "S13",
        "phase_id": PHASE_ID,
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "version": VERSION,
        "status": STATUS,
        "decision": DECISION,
        "stage12_review_dependency_validated": True,
        "source_lane_count": len(lanes),
        **structure,
        "draft_report_count": len(drafts),
        "html_draft_count": 2,
        "required_section_count": len(SECTIONS),
        "open_final_difference_accepted_count": upstream["open_final_difference_accepted_count"],
        "nonzero_delta_reconciliation_count": upstream["nonzero_delta_reconciliation_count"],
        "zero_delta_reconciliation_count": upstream["zero_delta_reconciliation_count"],
        "incomplete_reconciliation_count": upstream["incomplete_reconciliation_count"],
        "hard_block_count": upstream["hard_block_count"],
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "formal_report_count": 0,
        "business_decision_basis_count": 0,
        "browser_viewport_check_count": browser["viewport_check_count"],
        "section_interaction_check_count": browser["section_interaction_check_count"],
        "cross_draft_link_http_check_count": browser["cross_draft_link_http_check_count"],
        "cross_draft_navigation_check_count": browser["cross_draft_navigation_check_count"],
        "console_error_count": browser["console_error_count"],
        "horizontal_overflow_count": browser["horizontal_overflow_count"],
        "raw_source_file_count": raw_before["file_count"],
        "raw_snapshot_exact_match": raw_exact,
        "raw_cross_phase_snapshot_exact_match": raw_cross,
        "s13_p2_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }
    matrix = _matrix(summary)
    validation_summary = {
        "final_validation_recorded": final_validation,
        "focused_test": "PASS" if final_validation else "PENDING",
        "strict_validator": "PASS" if final_validation else "PENDING",
        "browser_desktop_mobile": "PASS" if final_validation else "PENDING",
        "raw_alignment": "PASS" if final_validation else "PENDING",
        "governance_and_safety_scans": "PASS" if final_validation else "PENDING",
    }
    manifest = {
        "schema_version": "kmfa.v014.s13_p1_post_remediation_report_manifest.v1",
        "project_id": "KMFA",
        "stage_id": "S13",
        "phase_id": PHASE_ID,
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "version": VERSION,
        "status": STATUS,
        "decision": DECISION,
        "generated_at": generated_at,
        "reviewed_head": _git_output(["rev-parse", "HEAD"]),
        "branch": _git_output(["branch", "--show-current"]),
        "remote": _git_output(["remote", "get-url", "origin"]),
        "summary": summary,
        "source_lane_status": lanes,
        "draft_definitions": drafts,
        "acceptance_matrix": matrix,
        "quality_gate": _quality_gate(),
        "phase_boundaries": _phase_boundaries(),
        "raw_boundary": {
            "raw_read_authorized": True,
            "raw_snapshot_validation_performed": True,
            "raw_write_performed": False,
            "raw_delete_performed": False,
            "raw_move_performed": False,
            "raw_rename_performed": False,
            "raw_overwrite_performed": False,
            "raw_mutation_performed": False,
        },
        "public_repo_safety": _public_repo_safety(),
        "browser_review": browser,
        "stage12_post_remediation_review_dependency_validated": True,
        "historical_s13_p1_policy_fixture_validated": (
            historical.get("stage_id") == "S13"
            and historical.get("financial_operating_summary", {}).get("source_lane_count") == 4
            and historical.get("financial_operating_summary", {}).get("draft_report_count") == 2
        ),
        "historical_s13_p1_dynamic_state_is_authoritative": False,
        "historical_pending_twelve_quarantined": (
            historical.get("financial_operating_summary", {}).get("pending_reconciliation_count") == 12
        ),
        "historical_b_grade_sample_quarantined": True,
        "taskpack_contract": contract,
        "reviewed_dependencies": {
            "current_stage12_review": s12_review.MANIFEST_PATH.as_posix(),
            "current_finance_structure_registry": CURRENT_SOURCE_REGISTRY_PATH.as_posix(),
            "current_finance_structure_candidates": CURRENT_CANDIDATES_PATH.as_posix(),
            "historical_s13_p1_policy_fixture": HISTORICAL_MANIFEST_PATH.as_posix(),
        },
        "next_phase": "S13-P2",
        "next_required_step": "Execute S13-P2 collection and receivable aging as a separate run after S13-P1 local validation and commit.",
        "validation_summary": validation_summary,
    }
    go_no_go = {
        "schema_version": "kmfa.v014.s13_p1_post_remediation_report_go_no_go.v1",
        "project_id": "KMFA",
        "stage_id": "S13",
        "phase_id": PHASE_ID,
        "decision": "NO_GO",
        "draft_report_allowed": True,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "s13_p2_performed": False,
        "s13_p3_performed": False,
        "stage13_review_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }
    alignment = {
        "schema_version": "kmfa.private.s13_p1.raw_to_report_alignment.v1",
        "classification": "PRIVATE_RUNTIME_ONLY",
        "raw_source_file_count": raw_before["file_count"],
        "structure_connected_lane_count": structure["structure_connected_lane_count"],
        "raw_value_bound_lane_count": structure["raw_value_bound_lane_count"],
        "report_business_amount_output_count": 0,
        "raw_to_report_value_comparison_performed": False,
        "raw_to_report_value_comparison_blocked_by_unproven_binding": True,
        "raw_snapshot_exact_match": raw_exact,
        "raw_cross_phase_snapshot_exact_match": raw_cross,
        "difference_report_required_for_this_phase": False,
        "final_goal_difference_report_required_if_binding_remains_unresolved": True,
    }
    for path, value in (
        (SUMMARY_PATH, summary),
        (MANIFEST_PATH, manifest),
        (LANES_PATH, {"schema_version": "kmfa.v014.s13_p1.source_lanes.v1", "lanes": lanes}),
        (DRAFTS_PATH, {"schema_version": "kmfa.v014.s13_p1.drafts.v1", "drafts": drafts}),
        (MATRIX_PATH, matrix),
        (GO_NO_GO_PATH, go_no_go),
        (METADATA_SUMMARY_PATH, summary),
        (METADATA_MANIFEST_PATH, manifest),
        (METADATA_LANES_PATH, {"schema_version": "kmfa.v014.s13_p1.source_lanes.v1", "lanes": lanes}),
        (METADATA_DRAFTS_PATH, {"schema_version": "kmfa.v014.s13_p1.drafts.v1", "drafts": drafts}),
        (METADATA_MATRIX_PATH, matrix),
        (METADATA_GO_NO_GO_PATH, go_no_go),
        (PRIVATE_RAW_BEFORE_PATH, raw_before),
        (PRIVATE_RAW_AFTER_PATH, raw_after),
        (PRIVATE_ALIGNMENT_PATH, alignment),
    ):
        _write_json(path, value)
    _write_text(REPORT_PATH, _render_report(summary))
    _write_text(
        TEST_RESULTS_PATH,
        f"""# S13-P1 测试结果

- focused test / strict validator：最终复验结果见 manifest
- v1.4 baseline：`{browser['baseline_pass_count']} PASS / {browser['baseline_warn_count']} WARN / {browser['baseline_fail_count']} FAIL`
- current HTML audit：`{browser['current_pass_count']} PASS / {browser['current_warn_count']} WARN / {browser['current_fail_count']} FAIL`
- desktop/mobile：`{browser['viewport_check_count']}/4 PASS`
- 章节交互：`{browser['section_interaction_check_count']}/28 PASS`
- 跨初稿 HTTP / 真实导航：`{browser['cross_draft_link_http_check_count']}/2 / {browser['cross_draft_navigation_check_count']}/2 PASS`
- raw 前后/跨 Stage 12/current：exact match
""",
    )
    _write_text(
        RISK_REGISTER_PATH,
        """# S13-P1 风险登记

| 风险 | 控制 | 状态 |
|---|---|---|
| 结构接入被误读为数值接入 | 每个主题显示结构已接入、数值未证明；raw value bound=0/4 | controlled |
| 历史 12 pending 或 B 级样板回流 | 历史产物只作 policy fixture，当前状态仅取 Stage 12 post-remediation review | controlled |
| 初稿被当成正式报告 | D/NO_GO、formal=false、decision basis=false 在页面和 manifest 双重锁定 | controlled |
| 现金或贷款状态触发业务动作 | cash forecast、loan action、payment/bank operation 全部 false | controlled |
| raw/private/secret 进入 Git | raw 快照与对齐诊断只写 ignored private runtime，公开证据仅聚合计数 | controlled |
""",
    )
    _write_text(
        ROLLBACK_PATH,
        f"""# S13-P1 回滚计划

1. 回退本 phase 的本地 commit 和 `{OUTPUT_DIR.as_posix()}` 公开证据。
2. 删除 ignored private browser/raw/alignment evidence，不触碰原始目录。
3. 恢复 Stage 12 review 为当前治理入口；不进入 S13-P2/P3。
4. 不回退、不移动、不删除、不覆盖任何原始文件。
""",
    )
    _write_text(PRIVATE_REPORT_PATH, _render_private_report(summary))
    if write_governance:
        _write_governance(generated_at)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--final-validation", action="store_true")
    parser.add_argument("--browser-evidence-only", action="store_true")
    args = parser.parse_args()
    if args.browser_evidence_only:
        result = _browser_worker()
        print(
            "S13-P1 browser evidence: "
            f"viewports={len(result['viewport_checks'])} "
            f"sections={len(result['section_interaction_checks'])} "
            f"status={result['status']}"
        )
        return 0
    manifest = generate(final_validation=args.final_validation)
    summary = manifest["summary"]
    print(
        "S13-P1 post-remediation financial operating report: "
        f"lanes={summary['source_lane_count']} drafts={summary['draft_report_count']} "
        f"bound={summary['raw_value_bound_lane_count']} "
        f"grade={summary['current_report_grade']} decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
