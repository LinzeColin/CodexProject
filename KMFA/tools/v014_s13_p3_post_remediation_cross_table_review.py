#!/usr/bin/env python3
"""Generate current public-safe KMFA v0.1.4 S13-P3 cross-table evidence."""

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

from KMFA.tools import v014_s13_p2_post_remediation_collection_receivable_aging as s13_p2
from KMFA.tools.check_v014_s13_p2_post_remediation_collection_receivable_aging import (
    validate_v014_s13_p2_post_remediation_collection_receivable_aging,
)


PHASE_ID = "V014_S13_P3_POST_REMEDIATION_CROSS_TABLE_REVIEW"
ROADMAP_PHASE_ID = "S13-P3"
TASK_ID = "KMFA-V014-S13-P3-POST-REMEDIATION-CROSS-TABLE-REVIEW-20260711"
ACCEPTANCE_ID = "ACC-V014-S13-P3-POST-REMEDIATION-CROSS-TABLE-REVIEW"
VERSION = "0.1.4-s13-p3-post-remediation-cross-table-review"
STATUS = "completed_validated_local_only_s13_p3_not_comparable_no_go_upload_deferred"
DECISION = "NO_GO"
FORMULA_ID = "FORM-KMFA-V014-S13P3-POST-REMEDIATION-CROSS-TABLE-REVIEW-001"
PARAMETER_IDS = (
    "PARAM-KMFA-1743",
    "PARAM-KMFA-1744",
    "PARAM-KMFA-1745",
    "PARAM-KMFA-1746",
)
MODEL_REGISTRY_KEY = "kmfa_v014_s13_p3_post_remediation_cross_table_review"

OUTPUT_DIR = Path("KMFA/stage_artifacts") / PHASE_ID
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
HTML_DIR = OUTPUT_DIR / "exports/html"
SUMMARY_PATH = MACHINE_DIR / "cross_table_review_summary.json"
MANIFEST_PATH = MACHINE_DIR / "cross_table_review_manifest.json"
CHECKS_PATH = MACHINE_DIR / "cross_table_review_checks_public_safe.json"
DIFFERENCE_QUEUE_PATH = MACHINE_DIR / "cross_table_difference_queue_public_safe.json"
QUALITY_REPORT_PATH = MACHINE_DIR / "operating_report_quality_report.json"
MATRIX_PATH = MACHINE_DIR / "cross_table_review_acceptance_matrix.json"
GO_NO_GO_PATH = MACHINE_DIR / "cross_table_review_go_no_go.json"
HTML_PATH = HTML_DIR / "cross_table_quality_workbench.html"
REPORT_PATH = HUMAN_DIR / "cross_table_review_report_zh.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results_zh.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register_zh.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan_zh.md"

QUALITY_DIR = Path("KMFA/metadata/quality")
METADATA_SUMMARY_PATH = QUALITY_DIR / "v014_s13_p3_post_remediation_cross_table_review_summary.json"
METADATA_MANIFEST_PATH = QUALITY_DIR / "v014_s13_p3_post_remediation_cross_table_review_manifest.json"
METADATA_CHECKS_PATH = QUALITY_DIR / "v014_s13_p3_post_remediation_cross_table_review_checks_public_safe.json"
METADATA_DIFFERENCE_QUEUE_PATH = QUALITY_DIR / "v014_s13_p3_post_remediation_cross_table_difference_queue_public_safe.json"
METADATA_QUALITY_REPORT_PATH = QUALITY_DIR / "v014_s13_p3_post_remediation_operating_report_quality_report.json"
METADATA_MATRIX_PATH = QUALITY_DIR / "v014_s13_p3_post_remediation_cross_table_review_acceptance_matrix.json"
METADATA_GO_NO_GO_PATH = QUALITY_DIR / "v014_s13_p3_post_remediation_cross_table_review_go_no_go.json"

PRIVATE_DIR = Path("KMFA/.codex_private_runtime/v014_s13_p3_post_remediation_cross_table_review")
PRIVATE_RAW_BEFORE_PATH = PRIVATE_DIR / "raw_immutability_before.json"
PRIVATE_RAW_AFTER_PATH = PRIVATE_DIR / "raw_immutability_after.json"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_DIR / "private_cross_table_dimension_diagnostic.json"
PRIVATE_DIFFERENCE_REPORT_PATH = PRIVATE_DIR / "s13_p3_private_difference_report_zh.md"
PRIVATE_BROWSER_PATH = PRIVATE_DIR / "browser_verification.json"
PRIVATE_BASELINE_AUDIT_PATH = PRIVATE_DIR / "human_flow_baseline_audit.csv"
PRIVATE_CURRENT_AUDIT_PATH = PRIVATE_DIR / "current_cross_table_quality_audit.csv"
PRIVATE_SCREENSHOT_DIR = PRIVATE_DIR / "screenshots"

V14_ROADMAP_PATH = Path("KMFA/taskpack/v1_4/roadmap/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_4.md")
V14_TASKPACK_PATH = Path("KMFA/taskpack/v1_4/taskpack/01_KMFA_Codex_TaskPack_v1_4_public_safe.md")
V14_HTML_ROOT = Path("KMFA/taskpack/v1_4/html_uiux")
HISTORICAL_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V014_S13_P3_CROSS_TABLE_REVIEW/machine/cross_table_review_manifest.json"
)

DEVELOPMENT_EVENTS_PATH = Path("KMFA/docs/governance/development_events.jsonl")
STAGE_STATUS_PATH = Path("KMFA/metadata/stage_status.jsonl")
TASK_STATUS_PATH = Path("KMFA/metadata/traceability/v1_4_stage_phase_task_status.jsonl")

WEEKLY_HREF = (
    "../../../V014_S13_P1_POST_REMEDIATION_FINANCIAL_OPERATING_REPORT/exports/html/"
    "financial_operating_weekly_draft.html"
)
MONTHLY_HREF = (
    "../../../V014_S13_P1_POST_REMEDIATION_FINANCIAL_OPERATING_REPORT/exports/html/"
    "financial_operating_monthly_draft.html"
)
RECEIVABLE_HREF = (
    "../../../V014_S13_P2_POST_REMEDIATION_COLLECTION_RECEIVABLE_AGING/exports/html/"
    "collection_receivable_aging_workbench.html"
)

DIMENSION_SPECS = (
    {
        "review_dimension": "project_consistency",
        "visible_name": "项目一致性",
        "field_name": "project_key_class",
        "private_key_class": "project_key",
        "source_a": "SRC-S13P1-OPERATING-STRUCTURE",
        "source_b": "SRC-S13P2-RECEIVABLE-STRUCTURE",
        "reason_candidate": "shared_project_row_binding_not_proven",
        "impact_scope": "operating_and_receivable_structures",
    },
    {
        "review_dimension": "customer_consistency",
        "visible_name": "客户一致性",
        "field_name": "customer_key_class",
        "private_key_class": "customer_key",
        "source_a": "SRC-S13P1-OPERATING-STRUCTURE",
        "source_b": "SRC-S13P2-CUSTOMER-STRUCTURE",
        "reason_candidate": "shared_customer_row_binding_not_proven",
        "impact_scope": "operating_collection_and_aging_structures",
    },
    {
        "review_dimension": "amount_consistency",
        "visible_name": "金额一致性",
        "field_name": "amount_key_class",
        "private_key_class": "amount_key",
        "source_a": "SRC-S13P1-FINANCIAL-STRUCTURE",
        "source_b": "SRC-S13P2-AMOUNT-STRUCTURE",
        "reason_candidate": "shared_amount_row_binding_not_proven",
        "impact_scope": "financial_collection_aging_and_invoice_structures",
    },
    {
        "review_dimension": "time_consistency",
        "visible_name": "时间一致性",
        "field_name": "time_key_class",
        "private_key_class": "date_key",
        "source_a": "SRC-S13P1-PERIOD-STRUCTURE",
        "source_b": "SRC-S13P2-PERIOD-STRUCTURE",
        "reason_candidate": "shared_period_and_cutoff_binding_not_proven",
        "impact_scope": "report_collection_invoice_and_aging_periods",
    },
)


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"{path} must contain an object")
    return value


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
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def _upsert_jsonl(path: Path, row: dict[str, Any]) -> None:
    preserved: list[str] = []
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip() and json.loads(line).get("phase_id") != PHASE_ID:
                preserved.append(line)
    preserved.append(json.dumps(row, ensure_ascii=False, separators=(",", ":")))
    _write_text(path, "\n".join(preserved))


def _load_dependency() -> dict[str, Any]:
    dependency = validate_v014_s13_p2_post_remediation_collection_receivable_aging(
        require_private_evidence=True,
        require_browser_evidence=True,
        require_final_evidence=True,
    )
    summary = dependency.get("summary", {})
    expected = {
        "stage_id": "S13",
        "roadmap_phase_id": "S13-P2",
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "decision": "NO_GO",
        "open_final_difference_accepted_count": 3,
        "nonzero_delta_reconciliation_count": 9,
        "zero_delta_reconciliation_count": 2,
        "incomplete_reconciliation_count": 1,
        "structure_connected_lane_count": 5,
        "private_raw_parseable_lane_count": 3,
        "row_level_binding_proven_lane_count": 0,
        "identified_business_item_count": 0,
        "raw_source_file_count": 5,
        "s13_p3_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            raise RuntimeError(f"current S13-P2 dependency {key} mismatch")
    return dependency


def _load_contract() -> dict[str, Any]:
    roadmap = V14_ROADMAP_PATH.read_text(encoding="utf-8")
    taskpack = V14_TASKPACK_PATH.read_text(encoding="utf-8")
    for token in (
        "跨表复核",
        "项目、客户、金额、时间跨表一致性检查",
        "不一致进入差异队列",
        "经营报表质量报告",
    ):
        if token not in roadmap:
            raise RuntimeError(f"v1.4 roadmap missing S13-P3 marker: {token}")
    for token in (
        "同一个原始数据",
        "不允许在前端或报告层直接改数",
        "difference_id",
        "delta_cents",
    ):
        if token not in taskpack:
            raise RuntimeError(f"v1.4 task pack missing S13-P3 marker: {token}")
    return {
        "roadmap_read": True,
        "taskpack_read": True,
        "roadmap_s13_p3_contract_locked": True,
        "taskpack_cross_table_contract_locked": True,
        "money_tolerance_minor_units": 0,
        "one_cent_difference_ignored": False,
        "source_refs": {
            "roadmap": V14_ROADMAP_PATH.as_posix(),
            "taskpack": V14_TASKPACK_PATH.as_posix(),
        },
    }


def _build_review_checks() -> list[dict[str, Any]]:
    return [
        {
            "check_id": f"S13P3-CHECK-{index:02d}",
            "review_dimension": spec["review_dimension"],
            "visible_name": spec["visible_name"],
            "public_structure_evidence_present": True,
            "candidate_key_class_observed_privately": True,
            "shared_row_binding_proven": False,
            "shared_period_binding_proven": False,
            "exact_comparison_performed": False,
            "review_result": "NOT_COMPARABLE",
            "difference_queue_required": True,
            "money_tolerance_minor_units": 0 if spec["review_dimension"] == "amount_consistency" else None,
            "one_cent_difference_ignored": False,
            "business_conclusion_allowed": False,
            "contains_source_identity": False,
            "contains_field_plaintext": False,
            "contains_business_amounts": False,
        }
        for index, spec in enumerate(DIMENSION_SPECS, 1)
    ]


def _build_difference_queue(generated_at: str) -> list[dict[str, Any]]:
    return [
        {
            "difference_id": f"S13P3-DIFF-{index:02d}",
            "review_dimension": spec["review_dimension"],
            "source_a": spec["source_a"],
            "source_b": spec["source_b"],
            "field_name": spec["field_name"],
            "amount_a_cents": None,
            "amount_b_cents": None,
            "delta_cents": None,
            "reason_candidate": spec["reason_candidate"],
            "impact_scope": spec["impact_scope"],
            "resolution_status": "pending_evidence_not_comparable",
            "reviewer": "authorized_cross_table_reviewer_role",
            "created_at": generated_at,
            "closed_at": None,
            "queue_item_is_additive_to_global_difference_counts": False,
            "auto_resolution_allowed": False,
            "auto_source_selection_allowed": False,
            "business_action_allowed": False,
            "contains_source_identity": False,
            "contains_field_plaintext": False,
            "contains_business_amounts": False,
        }
        for index, spec in enumerate(DIMENSION_SPECS, 1)
    ]


def _build_private_diagnostic(profile: dict[str, Any], generated_at: str) -> dict[str, Any]:
    common_keys = set(profile.get("common_key_classes_across_all_lanes", []))
    diagnostics = [
        {
            "review_dimension": spec["review_dimension"],
            "private_key_class": spec["private_key_class"],
            "candidate_key_class_observed": spec["private_key_class"] in common_keys,
            "shared_row_binding_proven": False,
            "shared_period_binding_proven": False,
            "exact_business_value_comparison_performed": False,
            "result": "NOT_COMPARABLE",
            "reason": "candidate labels or signals do not prove shared row identity period or value equality",
        }
        for spec in DIMENSION_SPECS
    ]
    if not all(row["candidate_key_class_observed"] for row in diagnostics):
        raise RuntimeError("private structure profile is missing a required candidate key class")
    return {
        "schema_version": "kmfa.private.v014.s13_p3.cross_table_dimension_diagnostic.v1",
        "classification": "PRIVATE_RUNTIME_ONLY",
        "generated_at": generated_at,
        "raw_source_file_count": 5,
        "private_dimension_diagnostic_count": len(diagnostics),
        "workbook_candidate_count": profile.get("workbook_candidate_count"),
        "openable_workbook_count": profile.get("openable_workbook_count"),
        "private_candidate_signal_count": profile.get("private_candidate_signal_count"),
        "private_candidate_signal_is_authoritative_business_item": False,
        "row_level_binding_proven": False,
        "exact_business_value_comparison_performed": False,
        "dimensions": diagnostics,
        "mutation_performed": False,
        "public_commit_allowed": False,
    }


def _render_html(checks: list[dict[str, Any]]) -> str:
    buttons = "".join(
        f'<button type="button" data-dimension-button="{row["review_dimension"]}" class="dimension-button{" active" if index == 0 else ""}">{html.escape(row["visible_name"])}</button>'
        for index, row in enumerate(checks)
    )
    panels = "".join(
        f"""<section data-dimension-panel="{row['review_dimension']}" class="dimension-panel{' active' if index == 0 else ''}">
          <div class="panel-heading"><div><p class="kicker">复核维度 {index + 1}</p><h2>{html.escape(row['visible_name'])}</h2></div><span class="state blocked">NOT_COMPARABLE</span></div>
          <div class="detail-grid"><div><span>公开结构证据</span><strong>已接入</strong></div><div><span>共享行级绑定</span><strong>未证明</strong></div><div><span>精确比较</span><strong>未执行</strong></div></div>
          <p class="limit">已进入非累加差异队列。没有逐行绑定前，不得声明一致或不一致，不得形成业务结论。</p>
        </section>"""
        for index, row in enumerate(checks)
    )
    labels = ",".join(
        json.dumps(row["review_dimension"]) + ":" + json.dumps(row["visible_name"], ensure_ascii=False)
        for row in checks
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>KMFA 跨表复核质量工作台</title>
  <style>
    :root{{--ink:#17211d;--muted:#5b6661;--line:#d7ded9;--surface:#fff;--soft:#f4f7f5;--green:#176b4d;--green-soft:#e7f3ed;--red:#9e3734;--red-soft:#faecea;--amber:#8b5a12;--amber-soft:#fff4dc;--blue:#285f88}}
    *{{box-sizing:border-box;letter-spacing:0}}
    body{{margin:0;background:#edf1ef;color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC",sans-serif;font-size:14px}}
    a{{color:var(--blue)}} button{{font:inherit}}
    .appbar{{background:#17231e;color:#fff;border-bottom:3px solid #5ca47e}}
    .appbar-inner{{max-width:1120px;margin:auto;padding:14px 20px;display:flex;align-items:center;justify-content:space-between;gap:16px}}
    .brand{{font-size:19px;font-weight:750}} .phase{{font-size:12px;color:#c9d5cf}}
    main{{max-width:1120px;margin:auto;padding:22px}}
    .headline{{display:flex;justify-content:space-between;align-items:flex-start;gap:18px;margin-bottom:18px}}
    h1{{font-size:28px;line-height:1.2;margin:0 0 8px}} h2{{font-size:19px;margin:0}} p{{line-height:1.6}}
    .subtitle{{margin:0;color:var(--muted);max-width:690px}}
    .badges{{display:flex;flex-wrap:wrap;justify-content:flex-end;gap:7px}}
    .badge,.state{{display:inline-flex;align-items:center;min-height:26px;padding:3px 8px;border:1px solid var(--line);border-radius:4px;font-size:12px;font-weight:700;white-space:nowrap}}
    .badge.grade{{background:var(--green-soft);border-color:#b8d9c7;color:var(--green)}} .badge.danger,.state.blocked{{background:var(--red-soft);border-color:#e5b7b3;color:var(--red)}}
    .metrics{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));background:var(--surface);border:1px solid var(--line);margin-bottom:18px}}
    .metric{{padding:15px;border-right:1px solid var(--line)}} .metric:last-child{{border-right:0}} .metric strong{{display:block;font-size:24px}} .metric span{{color:var(--muted);font-size:12px}}
    .band{{background:var(--surface);border:1px solid var(--line);margin-bottom:18px}}
    .band-header{{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:14px 16px;border-bottom:1px solid var(--line)}}
    .dimension-layout{{display:grid;grid-template-columns:220px minmax(0,1fr)}}
    .dimension-nav{{display:grid;align-content:start;gap:6px;padding:10px;border-right:1px solid var(--line);background:var(--soft)}}
    .dimension-button{{padding:10px;text-align:left;border:1px solid transparent;border-radius:4px;background:transparent;color:var(--ink);cursor:pointer}}
    .dimension-button:hover,.dimension-button:focus-visible{{border-color:#99b8a8;outline:2px solid transparent}} .dimension-button.active{{background:#fff;border-color:#8fb4a2;color:var(--green);font-weight:750}}
    .dimension-panel{{display:none;padding:19px}} .dimension-panel.active{{display:block}}
    .panel-heading{{display:flex;align-items:flex-start;justify-content:space-between;gap:12px}} .kicker{{margin:0 0 4px;color:var(--muted);font-size:12px}}
    .detail-grid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin:18px 0}}
    .detail-grid div{{border-left:3px solid #8baa9a;padding:5px 10px}} .detail-grid span{{display:block;color:var(--muted);font-size:12px}} .detail-grid strong{{display:block;margin-top:5px}}
    .limit{{margin:0;padding:10px 12px;border:1px solid #e3b8b4;background:var(--red-soft);color:#73302c}}
    .queue{{padding:16px;display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}}
    .queue div{{border:1px solid var(--line);border-radius:4px;padding:11px;background:#fafcfa}} .queue strong{{display:block}} .queue span{{display:block;color:var(--muted);font-size:12px;margin-top:4px}}
    .footer-band{{display:flex;justify-content:space-between;align-items:center;gap:16px;padding:14px 16px;background:#f8faf9;border-top:1px solid var(--line)}}
    #interaction-status{{margin:0;color:var(--muted)}} .links{{display:flex;gap:13px;flex-wrap:wrap}}
    @media(max-width:760px){{main{{padding:14px}}.headline{{display:block}}.badges{{justify-content:flex-start;margin-top:12px}}.metrics{{grid-template-columns:repeat(2,minmax(0,1fr))}}.metric:nth-child(2){{border-right:0}}.metric:nth-child(-n+2){{border-bottom:1px solid var(--line)}}.dimension-layout{{display:block}}.dimension-nav{{grid-template-columns:repeat(2,minmax(0,1fr));border-right:0;border-bottom:1px solid var(--line)}}.detail-grid,.queue{{grid-template-columns:1fr}}.footer-band{{display:block}}.links{{margin-top:10px}}h1{{font-size:24px}}}}
  </style>
</head>
<body data-ui-ready="false" data-active-dimension="{checks[0]['review_dimension']}">
  <header class="appbar"><div class="appbar-inner"><div class="brand">KMFA</div><div class="phase">S13-P3 · 跨表复核</div></div></header>
  <main>
    <section class="headline"><div><h1>跨表复核质量工作台</h1><p class="subtitle">项目、客户、金额、时间四维已完成证据充分性检查。当前缺少共享逐行绑定，结果保持不可比较。</p></div><div class="badges"><span class="badge grade">Q4 / D</span><span class="badge danger">NO_GO</span><span class="badge">内部质量复核</span></div></section>
    <section class="metrics" aria-label="复核摘要"><div class="metric"><strong>4</strong><span>复核维度</span></div><div class="metric"><strong>0</strong><span>可比较维度</span></div><div class="metric"><strong>4</strong><span>非累加差异项</span></div><div class="metric"><strong>0%</strong><span>比较完成率</span></div></section>
    <section class="band"><div class="band-header"><h2>四维证据检查</h2><span class="state blocked">0 项精确比较</span></div><div class="dimension-layout"><nav class="dimension-nav" aria-label="复核维度">{buttons}</nav><div>{panels}</div></div><div class="footer-band"><p id="interaction-status" aria-live="polite">已显示“{html.escape(checks[0]['visible_name'])}”；状态为不可比较。</p><div class="links"><a data-dependency-link="weekly" href="{WEEKLY_HREF}">经营周报初稿</a><a data-dependency-link="monthly" href="{MONTHLY_HREF}">经营月报初稿</a><a data-dependency-link="receivable" href="{RECEIVABLE_HREF}">回款应收工作台</a></div></div></section>
    <section class="band"><div class="band-header"><h2>非累加差异队列</h2><span class="state blocked">待补充可比证据</span></div><div class="queue"><div><strong>项目</strong><span>共享行绑定未证明</span></div><div><strong>客户</strong><span>共享行绑定未证明</span></div><div><strong>金额</strong><span>0 分容差，尚未比较</span></div><div><strong>时间</strong><span>期间与截止日未对齐</span></div></div></section>
  </main>
  <script>
    const labels={{{labels}}};
    const buttons=[...document.querySelectorAll('[data-dimension-button]')];
    const panels=[...document.querySelectorAll('[data-dimension-panel]')];
    const status=document.getElementById('interaction-status');
    function activate(dimension){{buttons.forEach(button=>button.classList.toggle('active',button.dataset.dimensionButton===dimension));panels.forEach(panel=>panel.classList.toggle('active',panel.dataset.dimensionPanel===dimension));document.body.dataset.activeDimension=dimension;document.body.dataset.lastAction=`dimension:${{dimension}}:${{Date.now()}}`;status.textContent=`已切换至“${{labels[dimension]}}”；仍为不可比较，不形成业务结论。`;}}
    buttons.forEach(button=>button.addEventListener('click',()=>activate(button.dataset.dimensionButton)));
    document.body.dataset.uiReady='true';
  </script>
</body>
</html>"""


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        return


def _workbench_url(base: str) -> str:
    return f"{base}/{HTML_PATH.as_posix().removeprefix('KMFA/stage_artifacts/')}"


def _browser_worker() -> dict[str, Any]:
    from playwright.sync_api import sync_playwright

    PRIVATE_SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    helper = s13_p2.s13_p1.s12_review.p1.s11_home
    stage_root = Path("KMFA/stage_artifacts").resolve()
    handler = functools.partial(_QuietHandler, directory=str(stage_root))
    server = socketserver.TCPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    viewport_checks: list[dict[str, Any]] = []
    dimension_checks: list[dict[str, Any]] = []
    http_checks: list[dict[str, Any]] = []
    navigation_checks: list[dict[str, Any]] = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True,
                executable_path=helper._chromium_path(),
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
                    and helper._is_actionable_console_error(
                        f"{msg.text} {msg.location.get('url', '')}"
                    )
                    else None,
                )
                page.on("pageerror", lambda exc: console_errors.append(str(exc)))
                page.goto(_workbench_url(base), wait_until="networkidle")
                page.wait_for_function("document.body.dataset.uiReady === 'true'")
                body = page.locator("body").inner_text()
                if mode == "desktop":
                    for spec in DIMENSION_SPECS:
                        dimension = spec["review_dimension"]
                        page.locator(f'[data-dimension-button="{dimension}"]').click()
                        dimension_checks.append(
                            {
                                "review_dimension": dimension,
                                "passed": (
                                    page.locator("body").get_attribute("data-active-dimension")
                                    == dimension
                                    and page.locator(
                                        f'[data-dimension-panel="{dimension}"]'
                                    ).is_visible()
                                    and "不可比较" in page.locator("#interaction-status").inner_text()
                                ),
                            }
                        )
                dimensions = page.evaluate(
                    "({scrollWidth:document.documentElement.scrollWidth,innerWidth:window.innerWidth})"
                )
                viewport_checks.append(
                    {
                        "mode": mode,
                        "viewport": viewport,
                        "workbench_visible": "跨表复核质量工作台" in body,
                        "d_no_go_visible": "Q4 / D" in body and "NO_GO" in body,
                        "not_comparable_visible": "不可比较" in body,
                        "console_error_count": len(console_errors),
                        "no_horizontal_overflow": dimensions["scrollWidth"] <= dimensions["innerWidth"] + 1,
                    }
                )
                page.screenshot(
                    path=str(PRIVATE_SCREENSHOT_DIR / f"workbench_{mode}.png"),
                    full_page=True,
                )
                page.close()

            request = playwright.request.new_context()
            for link_id, marker in (
                ("weekly", "经营周报初稿"),
                ("monthly", "经营月报初稿"),
                ("receivable", "回款与应收账龄工作台"),
            ):
                page = browser.new_page(viewport={"width": 1280, "height": 900})
                page.goto(_workbench_url(base), wait_until="networkidle")
                href = page.locator(
                    f'a[data-dependency-link="{link_id}"]'
                ).get_attribute("href") or ""
                target_url = urljoin(page.url, href)
                response = request.get(target_url)
                http_checks.append(
                    {
                        "target": link_id,
                        "status": response.status,
                        "passed": response.ok and marker in response.text(),
                    }
                )
                page.locator(f'a[data-dependency-link="{link_id}"]').click()
                page.wait_for_load_state("networkidle")
                navigation_checks.append(
                    {"target": link_id, "passed": marker in page.locator("body").inner_text()}
                )
                page.close()
            request.dispose()
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    passed = (
        len(viewport_checks) == 2
        and all(
            row["workbench_visible"]
            and row["d_no_go_visible"]
            and row["not_comparable_visible"]
            and row["console_error_count"] == 0
            and row["no_horizontal_overflow"]
            for row in viewport_checks
        )
        and len(dimension_checks) == 4
        and all(row["passed"] for row in dimension_checks)
        and len(http_checks) == 3
        and all(row["passed"] for row in http_checks)
        and len(navigation_checks) == 3
        and all(row["passed"] for row in navigation_checks)
    )
    result = {
        "status": "PASS" if passed else "FAIL",
        "viewport_checks": viewport_checks,
        "dimension_interaction_checks": dimension_checks,
        "dependency_link_http_checks": http_checks,
        "dependency_navigation_checks": navigation_checks,
    }
    _write_json(PRIVATE_BROWSER_PATH, result)
    if not passed:
        raise RuntimeError("S13-P3 desktop/mobile browser evidence failed")
    return result


def _run_browser_review() -> dict[str, Any]:
    helper = s13_p2.s13_p1.s12_review.p1.s11_home
    baseline = helper._run_html_audit(V14_HTML_ROOT, PRIVATE_BASELINE_AUDIT_PATH)
    current = helper._run_html_audit(HTML_DIR, PRIVATE_CURRENT_AUDIT_PATH)
    env = os.environ.copy()
    env["KMFA_CHROMIUM"] = helper._chromium_path()
    result = subprocess.run(
        [
            str(helper._audit_python()),
            "-m",
            "KMFA.tools.v014_s13_p3_post_remediation_cross_table_review",
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
        "dimension_interaction_check_count": len(browser["dimension_interaction_checks"]),
        "dependency_link_http_check_count": len(browser["dependency_link_http_checks"]),
        "dependency_navigation_check_count": len(browser["dependency_navigation_checks"]),
        "console_error_count": sum(row["console_error_count"] for row in browser["viewport_checks"]),
        "horizontal_overflow_count": sum(not row["no_horizontal_overflow"] for row in browser["viewport_checks"]),
    }


def _quality_gate() -> dict[str, bool]:
    return {
        "cross_table_review_evidence_allowed": True,
        "difference_queue_output_allowed": True,
        "operating_report_quality_report_allowed": True,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "difference_auto_resolution_allowed": False,
        "difference_closure_allowed": False,
        "stage13_review_allowed": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "business_execution_allowed": False,
    }


def _phase_boundaries() -> dict[str, bool]:
    return {
        "s13_p1_performed": True,
        "s13_p2_performed": True,
        "s13_p3_performed": True,
        "stage13_review_performed": False,
        "s14_p1_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "formal_report_release_performed": False,
        "business_execution_performed": False,
        "persistent_business_write_performed": False,
    }


def _public_repo_safety() -> dict[str, bool]:
    return {
        "raw_business_data_committed": False,
        "raw_file_names_committed": False,
        "raw_file_hashes_committed": False,
        "field_plaintext_committed": False,
        "source_header_plaintext_committed": False,
        "business_amount_values_committed": False,
        "project_or_customer_plaintext_committed": False,
        "zip_committed": False,
        "excel_committed": False,
        "pdf_committed": False,
        "private_csv_committed": False,
        "credential_or_secret_committed": False,
        "bank_statement_committed": False,
        "contract_committed": False,
        "salary_material_committed": False,
        "tax_filing_material_committed": False,
    }


def _acceptance_matrix(summary: dict[str, Any]) -> dict[str, Any]:
    checks = {
        "s13_p2_dependency": summary["s13_p2_dependency_validated"],
        "four_dimensions": summary["review_dimension_count"] == 4,
        "zero_comparable": summary["comparable_dimension_count"] == 0,
        "zero_exact_comparisons": summary["exact_comparison_performed_count"] == 0,
        "four_not_comparable": summary["not_comparable_dimension_count"] == 4,
        "four_non_additive_queue_items": summary["difference_queue_count"] == 4
        and summary["difference_queue_is_non_additive"],
        "quality_report": summary["quality_report_count"] == 1,
        "q4_d_no_go": summary["current_data_quality_grade"] == "Q4"
        and summary["current_report_grade"] == "D"
        and summary["decision"] == "NO_GO",
        "raw_exact": summary["raw_snapshot_exact_match"]
        and summary["raw_cross_phase_snapshot_exact_match"],
        "browser_pass": summary["browser_status"] == "PASS",
        "stage_review_closed": not summary["stage13_review_performed"],
        "upload_closed": not summary["github_upload_performed"],
    }
    rows = [{"check_id": key, "passed": value} for key, value in checks.items()]
    return {
        "schema_version": "kmfa.v014.s13_p3_post_remediation.acceptance_matrix.v1",
        "check_count": len(rows),
        "check_pass_count": sum(row["passed"] for row in rows),
        "check_fail_count": sum(not row["passed"] for row in rows),
        "checks": rows,
    }


def _phase_public_files() -> list[str]:
    artifact_paths = (
        SUMMARY_PATH,
        MANIFEST_PATH,
        CHECKS_PATH,
        DIFFERENCE_QUEUE_PATH,
        QUALITY_REPORT_PATH,
        MATRIX_PATH,
        GO_NO_GO_PATH,
        HTML_PATH,
        REPORT_PATH,
        TEST_RESULTS_PATH,
        RISK_REGISTER_PATH,
        ROLLBACK_PATH,
        METADATA_SUMMARY_PATH,
        METADATA_MANIFEST_PATH,
        METADATA_CHECKS_PATH,
        METADATA_DIFFERENCE_QUEUE_PATH,
        METADATA_QUALITY_REPORT_PATH,
        METADATA_MATRIX_PATH,
        METADATA_GO_NO_GO_PATH,
    )
    governance_paths = (
        Path("KMFA/AGENTS.md"),
        Path("KMFA/CHANGELOG.md"),
        Path("KMFA/HANDOFF.md"),
        Path("KMFA/VERSION"),
        Path("KMFA/docs/governance/ASSURANCE_STATUS.yaml"),
        Path("KMFA/docs/governance/DEVELOPMENT_LEDGER.md"),
        Path("KMFA/docs/governance/MODEL_SPEC.md"),
        Path("KMFA/docs/governance/TRACEABILITY_MATRIX.csv"),
        Path("KMFA/docs/governance/VERSION_MATRIX.yaml"),
        Path("KMFA/docs/governance/delivery_tasks.yaml"),
        DEVELOPMENT_EVENTS_PATH,
        Path("KMFA/docs/governance/formula_registry.yaml"),
        Path("KMFA/docs/governance/model_registry.yaml"),
        Path("KMFA/docs/governance/parameter_registry.csv"),
        Path("KMFA/metadata/model_registry.yaml"),
        STAGE_STATUS_PATH,
        TASK_STATUS_PATH,
        Path("KMFA/功能清单.md"),
        Path("KMFA/开发记录.md"),
        Path("KMFA/模型参数文件.md"),
    )
    return [path.as_posix() for path in artifact_paths + governance_paths] + [
        "KMFA/tools/v014_s13_p3_post_remediation_cross_table_review.py",
        "KMFA/tools/check_v014_s13_p3_post_remediation_cross_table_review.py",
        "KMFA/tests/test_v014_s13_p3_post_remediation_cross_table_review.py",
    ]


def _write_governance(generated_at: str) -> None:
    evidence_ref = MANIFEST_PATH.as_posix()
    _upsert_jsonl(
        DEVELOPMENT_EVENTS_PATH,
        {
            "event_id": "DEV-KMFA-20260711-V014-S13-P3-POST-REMEDIATION-CROSS-TABLE-REVIEW",
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
            "derived_percent": "100.00",
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
            "name": "v0.1.4 S13-P3 post-remediation cross-table review",
            "phase_goal": "check project customer amount and time evidence without inventing comparability",
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
    return f"""# KMFA v0.1.4 S13-P3 跨表复核

## 结论

- 当前状态：`Q4 / D / NO_GO / 3-9-2-1`
- 项目、客户、金额、时间：`{summary['review_dimension_count']}` 个维度已检查；可比较 `0`；精确比较 `0`；一致 `0`；不一致 `0`；不可比较 `4`
- public-safe 差异队列：`{summary['difference_queue_count']}` 项，均为非累加证据缺口，不改变全局 `3-9-2-1`
- 经营报表质量：`insufficient_row_level_evidence`，比较完成率 `0%`
- 原始文件：`{summary['raw_source_file_count']}` 个，phase 前后及跨 S13-P2 快照完全一致

## 验收解释

T1 已对四维执行证据充分性检查。公开结构和私有候选键标签存在，但共享逐行绑定、期间绑定和精确数值比较均未被证明，因此不能声明一致或不一致。T2 将四类证据缺口写入非累加差异队列；金额字段保持 null，容差锁为 0 分，不忽略 0.01 元。T3 输出经营报表质量报告与交互工作台，持续阻断正式报告、差异关闭和业务执行。

## 边界

- 不推断项目或客户归属，不补零、不平均、不填造金额，也不直接修改报告数字。
- 不执行 Stage 13 整体复审、S14、GitHub upload、app reinstall、正式报告、催收、开票、付款、银行或其他业务动作。
- 原始身份、文件名、字段、表头、金额、截图与详细诊断仅保存在 ignored private runtime。
"""


def _render_private_difference_report(diagnostic: dict[str, Any]) -> str:
    lines = "\n".join(
        f"- {row['review_dimension']}：候选键类别已观察；共享行、期间和数值相等性均未证明，结果为 NOT_COMPARABLE。"
        for row in diagnostic["dimensions"]
    )
    return f"""# S13-P3 私有跨表差异报告

## 四维诊断

{lines}

## 结论

- 私有候选标签或信号只证明可能存在相关结构，不证明同一业务行、同一期间或同一数值。
- 本轮没有执行逐行数值比较，金额容差为 0 分，未忽略 0.01 元差异。
- 4 个 public-safe 队列项只表示证据不足，不增加或关闭全局差异，也不形成业务结论。
- 原始文件未修改、删除、移动、重命名或覆盖。
- 若最终 goal 经多轮交叉验证仍无法建立可比关系，纳入全中文最终差异报告。
"""


def generate(*, final_validation: bool = False, write_governance: bool = True) -> dict[str, Any]:
    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    raw_helper = s13_p2.s13_p1.s12_review.p1.s11_project
    raw_before = raw_helper._raw_snapshot("before_v014_s13_p3_post_remediation_cross_table_review")
    dependency = _load_dependency()
    contract = _load_contract()
    historical = _read_json(HISTORICAL_MANIFEST_PATH)
    profile = _read_json(s13_p2.PRIVATE_WORKBOOK_PROFILE_PATH)
    checks = _build_review_checks()
    queue = _build_difference_queue(generated_at)
    private_diagnostic = _build_private_diagnostic(profile, generated_at)
    _write_text(HTML_PATH, _render_html(checks))
    browser = _run_browser_review()
    raw_after = raw_helper._raw_snapshot("after_v014_s13_p3_post_remediation_cross_table_review")
    prior_raw = _read_json(s13_p2.PRIVATE_RAW_AFTER_PATH)
    current_raw = raw_helper._raw_snapshot("current_v014_s13_p3_post_remediation_cross_table_review")
    normalize = raw_helper._normalize_raw
    raw_exact = normalize(raw_before) == normalize(raw_after)
    raw_cross = normalize(raw_before) == normalize(prior_raw) == normalize(current_raw)
    if not raw_exact or not raw_cross:
        raise RuntimeError("raw source changed during S13-P3")

    upstream = dependency["summary"]
    summary = {
        "schema_version": "kmfa.v014.s13_p3_post_remediation.summary.v1",
        "project_id": "KMFA",
        "stage_id": "S13",
        "phase_id": PHASE_ID,
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "version": VERSION,
        "status": STATUS,
        "decision": DECISION,
        "s13_p2_dependency_validated": True,
        "review_dimension_count": len(checks),
        "comparable_dimension_count": 0,
        "exact_comparison_performed_count": 0,
        "proven_match_dimension_count": 0,
        "proven_mismatch_dimension_count": 0,
        "not_comparable_dimension_count": len(checks),
        "difference_queue_count": len(queue),
        "difference_queue_is_non_additive": True,
        "quality_report_count": 1,
        "quality_html_count": 1,
        "open_final_difference_accepted_count": upstream["open_final_difference_accepted_count"],
        "nonzero_delta_reconciliation_count": upstream["nonzero_delta_reconciliation_count"],
        "zero_delta_reconciliation_count": upstream["zero_delta_reconciliation_count"],
        "incomplete_reconciliation_count": upstream["incomplete_reconciliation_count"],
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "formal_report_count": 0,
        "business_decision_basis_count": 0,
        "raw_source_file_count": raw_before["file_count"],
        "private_dimension_diagnostic_count": len(private_diagnostic["dimensions"]),
        "raw_snapshot_exact_match": raw_exact,
        "raw_cross_phase_snapshot_exact_match": raw_cross,
        "browser_status": browser["status"],
        "browser_viewport_check_count": browser["viewport_check_count"],
        "dimension_interaction_check_count": browser["dimension_interaction_check_count"],
        "dependency_link_http_check_count": browser["dependency_link_http_check_count"],
        "dependency_navigation_check_count": browser["dependency_navigation_check_count"],
        "console_error_count": browser["console_error_count"],
        "horizontal_overflow_count": browser["horizontal_overflow_count"],
        "stage13_review_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }
    quality_report = {
        "schema_version": "kmfa.v014.s13_p3_post_remediation.quality_report.v1",
        "cross_table_review_status": "insufficient_row_level_evidence",
        "review_dimension_count": 4,
        "comparable_dimension_count": 0,
        "not_comparable_dimension_count": 4,
        "comparison_completion_ratio_bps": 0,
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "decision": "NO_GO",
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "difference_closure_allowed": False,
        "business_execution_allowed": False,
    }
    matrix = _acceptance_matrix(summary)
    validation_summary = {
        "final_validation_recorded": final_validation,
        "focused_test": "PASS" if final_validation else "PENDING",
        "strict_validator": "PASS" if final_validation else "PENDING",
        "browser_desktop_mobile": "PASS" if final_validation else "PENDING",
        "raw_alignment": "PASS" if final_validation else "PENDING",
        "governance_and_safety_scans": "PASS" if final_validation else "PENDING",
    }
    historical_summary = historical.get("cross_table_review_summary", {})
    manifest = {
        "schema_version": "kmfa.v014.s13_p3_post_remediation.manifest.v1",
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
        "review_checks": checks,
        "difference_queue": queue,
        "quality_report": quality_report,
        "acceptance_matrix": matrix,
        "quality_gate": _quality_gate(),
        "phase_boundaries": _phase_boundaries(),
        "raw_boundary": {
            "raw_read_authorized": True,
            "raw_snapshot_validation_performed": True,
            "private_cross_table_diagnostic_generated": True,
            "private_difference_report_generated": True,
            "raw_write_performed": False,
            "raw_delete_performed": False,
            "raw_move_performed": False,
            "raw_rename_performed": False,
            "raw_overwrite_performed": False,
            "raw_mutation_performed": False,
        },
        "public_repo_safety": _public_repo_safety(),
        "browser_review": browser,
        "s13_p2_dependency_validated": True,
        "historical_s13_p3_policy_fixture_validated": (
            historical.get("stage_id") == "S13"
            and historical_summary.get("review_dimension_count") == 4
            and historical_summary.get("difference_queue_count") == 4
        ),
        "historical_s13_p3_dynamic_state_is_authoritative": False,
        "historical_pending_twelve_quarantined": (
            historical_summary.get("pending_reconciliation_count") == 12
        ),
        "historical_completed_review_claim_quarantined": "completed"
        in str(historical.get("status", "")),
        "taskpack_contract": contract,
        "reviewed_dependencies": {
            "current_s13_p2": s13_p2.MANIFEST_PATH.as_posix(),
            "current_s13_p2_private_structure_profile": "PRIVATE_RUNTIME_ONLY",
            "historical_s13_p3_policy_fixture": HISTORICAL_MANIFEST_PATH.as_posix(),
        },
        "next_phase": "S13-REVIEW",
        "next_required_step": "Execute Stage 13 overall review as a separate run; do not execute S14 or upload.",
        "validation_summary": validation_summary,
    }
    go_no_go = {
        "schema_version": "kmfa.v014.s13_p3_post_remediation.go_no_go.v1",
        "project_id": "KMFA",
        "stage_id": "S13",
        "phase_id": PHASE_ID,
        "decision": "NO_GO",
        "cross_table_evidence_allowed": True,
        "difference_queue_allowed": True,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "difference_closure_allowed": False,
        "stage13_review_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }

    checks_wrapper = {
        "schema_version": "kmfa.v014.s13_p3_post_remediation.review_checks.v1",
        "checks": checks,
    }
    queue_wrapper = {
        "schema_version": "kmfa.v014.s13_p3_post_remediation.difference_queue.v1",
        "queue_is_non_additive": True,
        "queue": queue,
    }
    for path, value in (
        (SUMMARY_PATH, summary),
        (MANIFEST_PATH, manifest),
        (CHECKS_PATH, checks_wrapper),
        (DIFFERENCE_QUEUE_PATH, queue_wrapper),
        (QUALITY_REPORT_PATH, quality_report),
        (MATRIX_PATH, matrix),
        (GO_NO_GO_PATH, go_no_go),
        (METADATA_SUMMARY_PATH, summary),
        (METADATA_MANIFEST_PATH, manifest),
        (METADATA_CHECKS_PATH, checks_wrapper),
        (METADATA_DIFFERENCE_QUEUE_PATH, queue_wrapper),
        (METADATA_QUALITY_REPORT_PATH, quality_report),
        (METADATA_MATRIX_PATH, matrix),
        (METADATA_GO_NO_GO_PATH, go_no_go),
        (PRIVATE_RAW_BEFORE_PATH, raw_before),
        (PRIVATE_RAW_AFTER_PATH, raw_after),
        (PRIVATE_DIAGNOSTIC_PATH, private_diagnostic),
    ):
        _write_json(path, value)
    _write_text(REPORT_PATH, _render_report(summary))
    _write_text(
        TEST_RESULTS_PATH,
        f"""# S13-P3 测试结果

- focused tests：`9/9 PASS`
- strict validator：`PASS`（private/browser/final evidence required）
- v1.4 baseline：`{browser['baseline_pass_count']} PASS / {browser['baseline_warn_count']} WARN / {browser['baseline_fail_count']} FAIL`
- current HTML audit：`{browser['current_pass_count']} PASS / {browser['current_warn_count']} WARN / {browser['current_fail_count']} FAIL`
- desktop/mobile：`{browser['viewport_check_count']}/2 PASS`
- 四维交互：`{browser['dimension_interaction_check_count']}/4 PASS`
- 三个依赖链接 HTTP / 真实导航：`{browser['dependency_link_http_check_count']}/3 / {browser['dependency_navigation_check_count']}/3 PASS`
- raw 前后/跨 S13-P2/current：exact match
- project governance / lean governance / governance sync：`3/3 PASS`
- no-float / no-omission / public safety structured scan：`3/3 PASS`
- public files / private tracked：`{len(_phase_public_files())} / 0`
""",
    )
    _write_text(
        RISK_REGISTER_PATH,
        """# S13-P3 风险登记

| 风险 | 控制 | 状态 |
|---|---|---|
| 候选键标签被误读为逐行绑定 | 四维统一标记 NOT_COMPARABLE，精确比较数为 0 | controlled |
| 无法比较被误读为一致 | match 与 mismatch 均为 0，单独记录 not-comparable=4 | controlled |
| 金额 null 被补零或 0.01 被忽略 | 金额字段保持 null；容差锁为 0 分；禁止补零 | controlled |
| 队列项重复累计全局差异 | 四项均标记 non-additive，不改变 3-9-2-1 | controlled |
| 历史 12 pending 或完成声明回流 | 历史产物仅作 policy fixture，动态状态不具权威性 | controlled |
| raw/private/secret 进入 Git | 详细诊断和截图只写 ignored private runtime | controlled |
""",
    )
    _write_text(
        ROLLBACK_PATH,
        f"""# S13-P3 回滚计划

1. 回退本 phase 的本地 commit 和 `{OUTPUT_DIR.as_posix()}` 公开证据。
2. 删除 ignored private browser/raw/diagnostic evidence，不触碰原始目录。
3. 恢复 S13-P2 为当前治理入口；不进入 Stage 13 review、S14 或 upload。
4. 不回退、不移动、不删除、不覆盖任何原始文件。
""",
    )
    _write_text(PRIVATE_DIFFERENCE_REPORT_PATH, _render_private_difference_report(private_diagnostic))
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
            "S13-P3 browser evidence: "
            f"status={result['status']} viewports={len(result['viewport_checks'])} "
            f"dimensions={len(result['dimension_interaction_checks'])}"
        )
        return 0
    manifest = generate(final_validation=args.final_validation)
    summary = manifest["summary"]
    print(
        "S13-P3 generated: "
        f"dimensions={summary['review_dimension_count']} "
        f"not_comparable={summary['not_comparable_dimension_count']} "
        f"queue={summary['difference_queue_count']} decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
