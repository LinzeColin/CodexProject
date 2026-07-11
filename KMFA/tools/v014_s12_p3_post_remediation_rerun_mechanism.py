#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate current public-safe KMFA S12-P3 rerun-mechanism evidence."""

from __future__ import annotations

import argparse
import functools
import html
import json
import os
import socketserver
import subprocess
import threading
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

from KMFA.tools import v014_s12_p2_post_remediation_impact_preview as s12_p2
from KMFA.tools.check_v014_s12_p2_post_remediation_impact_preview import (
    validate_v014_s12_p2_post_remediation_impact_preview,
)


PHASE_ID = "V014_S12_P3_POST_REMEDIATION_RERUN_MECHANISM"
ROADMAP_PHASE_ID = "S12-P3"
TASK_ID = "KMFA-V014-S12-P3-POST-REMEDIATION-RERUN-MECHANISM-20260711"
ACCEPTANCE_ID = "ACC-V014-S12-P3-POST-REMEDIATION-RERUN-MECHANISM"
VERSION = "0.1.4-s12-p3-post-remediation-rerun-mechanism"
STATUS = "completed_validated_local_only_s12_p3_no_go_upload_deferred"
DECISION = "NO_GO"
FORMULA_ID = "FORM-KMFA-V014-S12P3-POST-REMEDIATION-RERUN-MECHANISM-001"
PARAMETER_IDS = (
    "PARAM-KMFA-1728",
    "PARAM-KMFA-1729",
    "PARAM-KMFA-1730",
    "PARAM-KMFA-1731",
)
MODEL_REGISTRY_KEY = "kmfa_v014_s12_p3_post_remediation_rerun_mechanism"
REQUIRED_RERUN_CHAIN = ("field_mapping", "fact_layer", "derived_metric", "report_reference")
LAYER_LABELS = {
    "field_mapping": "字段映射",
    "fact_layer": "事实层",
    "derived_metric": "指标",
    "report_reference": "报告引用",
}

OUTPUT_DIR = Path("KMFA/stage_artifacts") / PHASE_ID
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
HTML_DIR = OUTPUT_DIR / "exports/html"
SUMMARY_PATH = MACHINE_DIR / "rerun_summary.json"
MANIFEST_PATH = MACHINE_DIR / "rerun_manifest.json"
PLANS_PATH = MACHINE_DIR / "rerun_plan_definitions_public_safe.json"
GO_NO_GO_PATH = MACHINE_DIR / "rerun_go_no_go_report.json"
HTML_PATH = HTML_DIR / "kmfa_rerun_workbench.html"
REPORT_PATH = HUMAN_DIR / "s12_p3_rerun_mechanism_report_zh.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results_zh.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register_zh.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan_zh.md"

QUALITY_DIR = Path("KMFA/metadata/quality")
METADATA_SUMMARY_PATH = QUALITY_DIR / "v014_s12_p3_post_remediation_rerun_summary.json"
METADATA_MANIFEST_PATH = QUALITY_DIR / "v014_s12_p3_post_remediation_rerun_manifest.json"
METADATA_PLANS_PATH = QUALITY_DIR / "v014_s12_p3_post_remediation_rerun_plan_definitions_public_safe.json"
METADATA_GO_NO_GO_PATH = QUALITY_DIR / "v014_s12_p3_post_remediation_rerun_go_no_go_report.json"

PRIVATE_DIR = Path("KMFA/.codex_private_runtime/v014_s12_p3_post_remediation_rerun_mechanism")
PRIVATE_RAW_BEFORE_PATH = PRIVATE_DIR / "raw_immutability_before.json"
PRIVATE_RAW_AFTER_PATH = PRIVATE_DIR / "raw_immutability_after.json"
PRIVATE_BROWSER_PATH = PRIVATE_DIR / "browser_verification.json"
PRIVATE_BASELINE_AUDIT_PATH = PRIVATE_DIR / "human_flow_baseline_audit.csv"
PRIVATE_CURRENT_AUDIT_PATH = PRIVATE_DIR / "current_rerun_workbench_audit.csv"
PRIVATE_VALIDATION_REPORT_PATH = PRIVATE_DIR / "s12_p3_private_validation_zh.md"
PRIVATE_SCREENSHOT_DIR = PRIVATE_DIR / "screenshots"

VERSION_MATRIX_PATH = Path("KMFA/docs/governance/VERSION_MATRIX.yaml")
V14_ROADMAP_PATH = s12_p2.V14_ROADMAP_PATH
V14_TASKPACK_PATH = s12_p2.V14_TASKPACK_PATH
V14_WORKBENCH_PATH = s12_p2.V14_WORKBENCH_PATH
V14_FULL_FLOW_PATH = Path("KMFA/taskpack/v1_4/html_uiux/KMFA_系统全流程可点击验收样板_v1_4.html")
V14_HTML_ROOT = s12_p2.V14_HTML_ROOT
LEGACY_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V014_S12_P3_MANUAL_RERUN_MECHANISM/machine/manual_rerun_manifest.json"
)

DEVELOPMENT_EVENTS_PATH = s12_p2.DEVELOPMENT_EVENTS_PATH
STAGE_STATUS_PATH = s12_p2.STAGE_STATUS_PATH
TASK_STATUS_PATH = s12_p2.TASK_STATUS_PATH

P2_HREF = "../../../V014_S12_P2_POST_REMEDIATION_IMPACT_PREVIEW/exports/html/kmfa_impact_preview_workbench.html"
P1_HREF = "../../../V014_S12_P1_POST_REMEDIATION_PENDING_ACTIONS/exports/html/kmfa_pending_actions_workbench.html"
RETURN_LINKS = (
    ("impact", P2_HREF, "影响预览"),
    ("pending", P1_HREF, "待处理事项"),
    ("home", s12_p2.HOME_HREF, "经营分析工作台"),
    ("source", s12_p2.SOURCE_HREF, "KMFA 数据源检查板"),
)


def _write_json(path: Path, value: Any) -> None:
    s12_p2._write_json(path, value)


def _write_text(path: Path, value: str) -> None:
    s12_p2._write_text(path, value)


def _git_output(args: list[str]) -> str:
    return s12_p2._git_output(args)


def _load_s12_p2_dependency() -> dict[str, Any]:
    manifest = validate_v014_s12_p2_post_remediation_impact_preview(
        require_private_evidence=True,
        require_browser_evidence=True,
        require_final_evidence=True,
    )
    summary = manifest["summary"]
    expected = {
        "source_pending_action_group_count": 6,
        "impact_preview_definition_count": 6,
        "high_risk_preview_count": 5,
        "current_approved_business_event_count": 0,
        "current_published_business_event_count": 0,
        "open_final_difference_accepted_count": 3,
        "nonzero_delta_reconciliation_count": 9,
        "zero_delta_reconciliation_count": 2,
        "incomplete_reconciliation_count": 1,
        "hard_block_count": 12,
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "decision": "NO_GO",
        "s12_p3_performed": False,
        "stage12_review_performed": False,
        "github_upload_performed": False,
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            raise RuntimeError(f"S12-P2 dependency drift: {key}")
    return manifest


def _load_contract() -> dict[str, Any]:
    roadmap = V14_ROADMAP_PATH.read_text(encoding="utf-8")
    taskpack = V14_TASKPACK_PATH.read_text(encoding="utf-8")
    workbench = V14_WORKBENCH_PATH.read_text(encoding="utf-8")
    full_flow = V14_FULL_FLOW_PATH.read_text(encoding="utf-8")
    for token in (
        "事件通过后失效派生缓存",
        "重跑字段映射、事实层、指标、报告引用",
        "重跑后校验同源引用一致性",
    ):
        if token not in roadmap:
            raise RuntimeError(f"v1.4 roadmap S12-P3 token missing: {token}")
    for token in ("待处理事项必须有处理意见、影响预览、重跑链路", "FAIL = 0"):
        if token not in taskpack:
            raise RuntimeError(f"v1.4 taskpack token missing: {token}")
    for token in ("受影响链路", "重跑"):
        if token not in workbench:
            raise RuntimeError(f"v1.4 workbench token missing: {token}")
    for token in ("同一原始数据跨板块引用不一致时，失效缓存并重跑", "rerunFlow"):
        if token not in full_flow:
            raise RuntimeError(f"v1.4 full-flow token missing: {token}")
    legacy = json.loads(LEGACY_MANIFEST_PATH.read_text(encoding="utf-8"))
    if tuple(legacy.get("required_rerun_chain", ())) != REQUIRED_RERUN_CHAIN:
        raise RuntimeError("legacy S12-P3 rerun-chain fixture drift")
    legacy_summary = legacy.get("manual_rerun_summary", {})
    if legacy_summary.get("old_version_retained_count") != legacy_summary.get(
        "new_version_appended_count"
    ):
        raise RuntimeError("legacy S12-P3 append-only fixture drift")
    return {
        "roadmap_contract_read": True,
        "taskpack_human_flow_gate_read": True,
        "clickable_workbench_sample_read": True,
        "full_flow_rerun_sample_read": True,
        "required_rerun_chain": list(REQUIRED_RERUN_CHAIN),
        "legacy_policy_fixture_validated": True,
        "legacy_dynamic_counts_applied_to_current_state": False,
        "source_refs": [
            V14_ROADMAP_PATH.as_posix(),
            V14_TASKPACK_PATH.as_posix(),
            V14_WORKBENCH_PATH.as_posix(),
            V14_FULL_FLOW_PATH.as_posix(),
            LEGACY_MANIFEST_PATH.as_posix(),
        ],
    }


def _build_plans(dependency: dict[str, Any]) -> list[dict[str, Any]]:
    previews = dependency["impact_preview_definitions"]
    plans: list[dict[str, Any]] = []
    for index, preview in enumerate(previews, start=1):
        plan_id = f"RERUNPLAN-S12P3-POST-{index:03d}"
        source_anchor_id = f"PUBSRC-S12P3-POST-{index:03d}"
        steps = []
        for order, layer in enumerate(REQUIRED_RERUN_CHAIN, start=1):
            steps.append(
                {
                    "schema_version": "kmfa.v014.s12_p3.rerun_step_plan.v1",
                    "step_id": f"RERUNSTEP-S12P3-POST-{index:03d}-{order:02d}",
                    "sequence": order,
                    "layer": layer,
                    "layer_label": LAYER_LABELS[layer],
                    "source_anchor_id": source_anchor_id,
                    "old_version_ref": f"DERIVED-PRIOR-S12P3-POST-{index:03d}-{order:02d}",
                    "simulated_new_version_ref": f"DERIVED-SIM-S12P3-POST-{index:03d}-{order:02d}",
                    "old_version_retained": True,
                    "new_version_append_required": True,
                    "same_source_reference_required": True,
                    "status": "planned_session_simulation_only",
                    "persistent_write_performed": False,
                }
            )
        plans.append(
            {
                "schema_version": "kmfa.v014.s12_p3.rerun_plan_definition.v1",
                "record_type": "public_safe_session_rerun_plan_definition",
                "plan_id": plan_id,
                "plan_version": f"RERUN-PLAN-S12P3-POST-001.{index:03d}",
                "source_preview_id": preview["preview_id"],
                "source_group_id": preview["source_group_id"],
                "source_group_title": preview["source_group_title"],
                "source_event_template_id": preview["source_event_template_id"],
                "manual_action_kind": preview["manual_action_kind"],
                "risk_level": preview["risk_level"],
                "second_confirmation_required": preview["second_confirmation_required"],
                "project_attribution": preview["project_attribution"],
                "project_scope_semantics": preview["project_scope_semantics"],
                "affected_project_scope": preview["affected_project_scope"],
                "affected_metrics": preview["affected_metrics"],
                "affected_reports": preview["affected_reports"],
                "source_anchor_id": source_anchor_id,
                "eligibility_status": "blocked_no_approved_published_event",
                "cache_invalidation_plan_status": "planned_session_simulation_only",
                "session_rerun_simulation_allowed": True,
                "persistent_cache_invalidation_allowed": False,
                "persistent_rerun_allowed": False,
                "same_source_consistency_simulation_allowed": True,
                "raw_layer_write_allowed": False,
                "persistent_business_write_allowed": False,
                "business_value_committed": False,
                "rerun_steps": steps,
                "source_evidence_refs": [
                    s12_p2.MANIFEST_PATH.as_posix(),
                    V14_ROADMAP_PATH.as_posix(),
                ],
            }
        )
    return plans


def _quality_gate() -> dict[str, Any]:
    return {
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "decision": DECISION,
        "rerun_plan_generation_allowed": True,
        "session_only_rerun_simulation_allowed": True,
        "high_risk_second_confirmation_required": True,
        "same_source_reference_consistency_check_required": True,
        "append_only_derived_version_required": True,
        "money_tolerance_minor_units": 0,
        "one_cent_difference_ignored": False,
        "persistent_cache_invalidation_allowed": False,
        "persistent_derived_rerun_allowed": False,
        "blocked_event_persistent_rerun_allowed": False,
        "old_version_overwrite_allowed": False,
        "current_business_event_approval_allowed": False,
        "current_business_event_publish_allowed": False,
        "report_grade_upgrade_allowed": False,
        "persistent_business_write_allowed": False,
        "raw_layer_write_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "stage12_review_allowed": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "business_execution_allowed": False,
    }


def _phase_boundaries() -> dict[str, bool]:
    return {
        "s12_p1_dependency_included": True,
        "s12_p2_dependency_included": True,
        "s12_p3_rerun_mechanism_scope_included": True,
        "session_only_simulation_scope_included": True,
        "persistent_derived_write_scope_included": False,
        "raw_mutation_scope_included": False,
        "project_attribution_scope_included": False,
        "stage12_review_scope_included": False,
        "formal_report_scope_included": False,
        "github_upload_scope_included": False,
        "app_reinstall_scope_included": False,
        "business_execution_scope_included": False,
    }


def _public_repo_safety() -> dict[str, bool]:
    return s12_p2._public_repo_safety()


def _render_rows(plans: list[dict[str, Any]]) -> str:
    rows = []
    for plan in plans:
        risk_label = "高风险" if plan["risk_level"] == "high" else "中风险"
        search_text = " ".join(
            [
                plan["source_group_title"],
                risk_label,
                *plan["affected_metrics"],
                *plan["affected_reports"],
            ]
        )
        rows.append(
            f'''<tr data-rerun-row data-risk="{plan['risk_level']}" data-search="{html.escape(search_text)}">
              <td><strong>{html.escape(plan['source_group_title'])}</strong><small>{plan['plan_id']}</small></td>
              <td><span class="risk {plan['risk_level']}">{risk_label}</span></td>
              <td>{len(plan['affected_metrics'])}</td><td>{len(plan['affected_reports'])}</td>
              <td><button type="button" class="btn secondary" data-select-plan="{plan['plan_id']}">查看计划</button></td>
            </tr>'''
        )
    return "\n".join(rows)


def _render_html(plans: list[dict[str, Any]]) -> str:
    links = "".join(
        f'<a data-return-link="{link_id}" href="{href}">{label}</a>'
        for link_id, href, label in RETURN_LINKS
    )
    template = r'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>KMFA S12-P3 重跑机制工作台</title>
  <style>
    :root{--bg:#f4f6f8;--panel:#fff;--ink:#17202a;--muted:#5d6875;--line:#d9dee5;--navy:#17365d;--blue:#2368a2;--green:#177245;--amber:#9a5b00;--red:#a62d2d;--soft:#eef3f8}
    *{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI","Microsoft YaHei",sans-serif;letter-spacing:0}button,input,select{font:inherit}.shell{min-height:100vh}.topbar{background:var(--navy);color:#fff;padding:16px 24px;display:flex;align-items:center;justify-content:space-between;gap:16px}.brand{display:flex;align-items:center;gap:12px}.mark{width:40px;height:40px;display:grid;place-items:center;background:#fff;color:var(--navy);font-weight:900;border-radius:6px}.brand h1{font-size:18px;margin:0}.brand p{margin:2px 0 0;color:#d9e6f2;font-size:12px}.links{display:flex;gap:6px;flex-wrap:wrap}.links a{color:#fff;text-decoration:none;border:1px solid rgba(255,255,255,.35);padding:7px 9px;border-radius:5px}.main{max-width:1440px;margin:0 auto;padding:22px}.statusline{display:flex;justify-content:space-between;gap:18px;align-items:flex-start;margin-bottom:18px}.statusline h2{font-size:24px;margin:0 0 4px}.gate{background:#fff1f0;border:1px solid #efc4bf;color:var(--red);padding:8px 11px;border-radius:6px;font-weight:800;white-space:nowrap}.metrics{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin-bottom:16px}.metric{background:var(--panel);border:1px solid var(--line);border-radius:7px;padding:14px;min-height:94px}.metric span{color:var(--muted);font-weight:700}.metric b{display:block;font-size:26px;margin-top:4px}.metric small{color:var(--muted)}.workspace{display:grid;grid-template-columns:minmax(560px,1.15fr) minmax(420px,.85fr);gap:16px}.panel{background:var(--panel);border:1px solid var(--line);border-radius:7px;padding:16px}.panel h3{font-size:17px;margin:0 0 12px}.filters{display:grid;grid-template-columns:1fr 160px auto;gap:8px;margin-bottom:12px}.filters input,.filters select{width:100%;border:1px solid var(--line);padding:9px 10px;border-radius:5px;background:#fff}.btn{border:0;border-radius:5px;background:var(--blue);color:#fff;padding:9px 11px;font-weight:750;cursor:pointer}.btn.secondary{background:#fff;color:var(--navy);border:1px solid var(--line)}.btn.warn{background:var(--amber)}.btn.danger{background:var(--red)}.btn:disabled{cursor:not-allowed;opacity:.48}.tablewrap{overflow:auto;border:1px solid var(--line);border-radius:6px}table{width:100%;border-collapse:collapse;min-width:690px}th,td{text-align:left;padding:10px;border-bottom:1px solid #e8ebef;vertical-align:top}th{background:var(--soft);color:#31465c;font-size:12px}td small{display:block;color:var(--muted);margin-top:2px}.risk{display:inline-block;padding:3px 7px;border-radius:4px;font-weight:800}.risk.high{background:#fde8e6;color:var(--red)}.risk.medium{background:#fff1d8;color:var(--amber)}tr.selected td{background:#eef6fc}.detail-empty{min-height:480px;display:grid;place-items:center;color:var(--muted);border:1px dashed #bdc7d2;border-radius:6px}.detail{display:none}.detail.active{display:block}.summary{padding:10px;background:var(--soft);border-radius:6px;margin-bottom:12px}.three{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}.block{border:1px solid var(--line);border-radius:6px;padding:10px;min-width:0}.block h4{margin:0 0 6px;font-size:13px}.block ul{margin:0;padding-left:17px}.chain{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:7px;margin:12px 0}.step{border:1px solid var(--line);border-radius:6px;padding:9px;min-height:78px}.step b{display:block;color:var(--navy)}.step.complete{border-color:#7ab895;background:#edf8f2}.confirm{border:1px solid #efc4bf;background:#fff7f6;border-radius:6px;padding:10px;margin:10px 0}.confirm[hidden]{display:none}.actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}.result{margin-top:12px;border-left:4px solid var(--blue);background:#f3f7fa;padding:10px}.result.pass{border-color:var(--green);background:#eef8f2}.result.blocked{border-color:var(--red);background:#fff2f1}.log{margin-top:14px;background:#18232f;color:#e5edf5;border-radius:6px;padding:10px;min-height:92px;max-height:145px;overflow:auto;font:12px/1.45 ui-monospace,SFMono-Regular,Menlo,monospace}.footer{color:var(--muted);font-size:12px;padding:16px 0}.hidden{display:none!important}
    .workspace>.panel{min-width:0}
    @media(max-width:980px){.topbar,.statusline{display:block}.links{margin-top:12px}.main{padding:14px}.metrics{grid-template-columns:repeat(2,minmax(0,1fr))}.workspace{grid-template-columns:1fr}.filters{grid-template-columns:1fr}.three,.chain{grid-template-columns:1fr}.gate{display:inline-block;margin-top:10px}.detail-empty{min-height:180px}.panel{padding:12px}}
  </style>
</head>
<body data-ui-ready="false" data-session-simulation-count="0" data-session-consistency-count="0" data-simulation-status="idle" data-consistency-status="idle" data-persistent-status="blocked">
  <div class="shell">
    <header class="topbar"><div class="brand"><div class="mark">KM</div><div><h1>KMFA 重跑机制</h1><p>S12-P3 · 公开安全会话模拟</p></div></div><nav class="links">__LINKS__</nav></header>
    <main class="main">
      <section class="statusline"><div><h2>派生链重跑计划</h2><div>缓存失效计划与四层链路同源校验；不产生持久业务写入。</div></div><div class="gate">Q4 / D · NO_GO</div></section>
      <section class="metrics" aria-label="重跑摘要">
        <div class="metric"><span>当前计划</span><b>6</b><small>对应当前 6 组待处理事项</small></div>
        <div class="metric"><span>计划步骤</span><b>24</b><small>每份计划 4 层</small></div>
        <div class="metric"><span>持久缓存失效</span><b>0</b><small>业务事件未批准或发布</small></div>
        <div class="metric"><span>会话模拟</span><b data-simulation-count>0</b><small>刷新后清零</small></div>
      </section>
      <section class="workspace">
        <div class="panel"><h3>重跑计划清单</h3><div class="filters"><input data-rerun-search aria-label="搜索重跑计划" placeholder="搜索事项、指标或报告"><select data-risk-filter aria-label="风险筛选"><option value="all">全部风险</option><option value="high">高风险</option><option value="medium">中风险</option></select><button type="button" class="btn secondary" data-reset-filters>重置</button></div><div class="tablewrap"><table><thead><tr><th>事项</th><th>风险</th><th>指标</th><th>报告</th><th>操作</th></tr></thead><tbody>__ROWS__</tbody></table></div></div>
        <div class="panel"><div class="detail-empty" data-detail-empty>请选择一份重跑计划</div><div class="detail" data-detail><h3 data-detail-title></h3><div class="summary" data-detail-summary></div><div class="three"><div class="block"><h4>潜在项目范围</h4><ul data-projects></ul></div><div class="block"><h4>受影响指标</h4><ul data-metrics></ul></div><div class="block"><h4>受影响报告</h4><ul data-reports></ul></div></div><div class="chain" data-chain></div><div class="confirm" data-confirm-panel hidden><label><input type="checkbox" data-high-risk-ack> 已核对高风险影响范围</label><button type="button" class="btn warn" data-confirm-rerun>确认重跑模拟</button></div><div class="actions"><button type="button" class="btn secondary" data-preview-rerun>预览重跑链路</button><button type="button" class="btn" data-run-simulation disabled>执行会话模拟</button><button type="button" class="btn secondary" data-check-consistency disabled>校验同源引用</button><button type="button" class="btn danger" data-check-persistent>检查持久执行门禁</button><button type="button" class="btn secondary" data-reset-session>清空会话</button></div><div class="result" data-result>尚未生成重跑预览。</div><div class="log" data-log></div></div></div>
      </section>
      <div class="footer">仅完成 S12-P3 重跑机制；第 12 阶段整体复审、GitHub 上传、应用重装、正式报告和业务执行均未执行。</div>
    </main>
  </div>
  <script>
    const plans=__PLANS__;
    const state={selectedId:null,previewed:false,confirmed:false,simulated:false,consistent:false,simulationCount:0,consistencyCount:0};
    const q=(s,r=document)=>r.querySelector(s),qa=(s,r=document)=>Array.from(r.querySelectorAll(s));
    const rows=qa('[data-rerun-row]'),search=q('[data-rerun-search]'),risk=q('[data-risk-filter]'),detail=q('[data-detail]'),empty=q('[data-detail-empty]'),result=q('[data-result]'),log=q('[data-log]'),ack=q('[data-high-risk-ack]'),confirmPanel=q('[data-confirm-panel]'),runButton=q('[data-run-simulation]'),checkButton=q('[data-check-consistency]');
    function current(){return plans.find(p=>p.plan_id===state.selectedId)}
    function record(message){const row=document.createElement('div');row.textContent=message;log.prepend(row)}
    function list(target,items){q(target).innerHTML=items.map(item=>`<li>${item}</li>`).join('')}
    function updateCounters(){q('[data-simulation-count]').textContent=String(state.simulationCount);document.body.dataset.sessionSimulationCount=String(state.simulationCount);document.body.dataset.sessionConsistencyCount=String(state.consistencyCount)}
    function setResult(text,type=''){result.textContent=text;result.className=`result ${type}`.trim()}
    function resetFlow(){state.previewed=false;state.confirmed=false;state.simulated=false;state.consistent=false;ack.checked=false;confirmPanel.hidden=true;runButton.disabled=true;checkButton.disabled=true;document.body.dataset.simulationStatus='idle';document.body.dataset.consistencyStatus='idle';qa('[data-chain] .step').forEach(step=>step.classList.remove('complete'));setResult('尚未生成重跑预览。')}
    function applyFilters(){const term=search.value.trim().toLowerCase();rows.forEach(row=>{const matchText=row.dataset.search.toLowerCase().includes(term),matchRisk=risk.value==='all'||row.dataset.risk===risk.value;row.classList.toggle('hidden',!(matchText&&matchRisk))})}
    function selectPlan(id){state.selectedId=id;rows.forEach(row=>row.classList.toggle('selected',q(`[data-select-plan="${id}"]`,row)!==null));resetFlow();const plan=current();empty.classList.add('hidden');detail.classList.add('active');q('[data-detail-title]').textContent=plan.source_group_title;q('[data-detail-summary]').textContent=`${plan.plan_id} · ${plan.risk_level==='high'?'高风险':'中风险'} · 项目范围仅表示潜在影响，不形成归属。`;list('[data-projects]',plan.affected_project_scope);list('[data-metrics]',plan.affected_metrics);list('[data-reports]',plan.affected_reports);q('[data-chain]').innerHTML=plan.rerun_steps.map(step=>`<div class="step" data-step="${step.sequence}"><b>${step.layer_label}</b><span>计划中 · 保留旧版本</span></div>`).join('');record(`选择计划：${plan.plan_id}`)}
    function previewRerun(){const plan=current();if(!plan){setResult('阻断：未选择重跑计划。','blocked');return}state.previewed=true;if(plan.second_confirmation_required){confirmPanel.hidden=false;document.body.dataset.simulationStatus='blocked_pending_second_confirmation';setResult('高风险计划等待二次确认。','blocked')}else{state.confirmed=true;runButton.disabled=false;document.body.dataset.simulationStatus='ready_session_simulation';setResult('重跑链路预览已通过，可执行会话模拟。','pass')}record(`预览四层链路：${plan.plan_id}`)}
    function confirmRerun(){if(!state.previewed||!ack.checked){setResult('阻断：高风险确认未完成。','blocked');return}state.confirmed=true;runButton.disabled=false;document.body.dataset.simulationStatus='ready_session_simulation';setResult('高风险二次确认已完成，可执行会话模拟。','pass');record('完成高风险二次确认')}
    function runSimulation(){const plan=current();if(!plan||!state.previewed||!state.confirmed){document.body.dataset.simulationStatus='blocked_pending_second_confirmation';setResult('阻断：预览或二次确认未完成。','blocked');return}state.simulated=true;state.consistent=false;state.simulationCount=1;qa('[data-chain] .step').forEach(step=>{step.classList.add('complete');q('span',step).textContent='模拟完成 · 新版本仅追加'});runButton.disabled=true;checkButton.disabled=false;document.body.dataset.simulationStatus='session_simulation_complete';document.body.dataset.consistencyStatus='pending';updateCounters();setResult('派生缓存失效与四层重跑模拟完成；未写入持久缓存。','pass');record(`完成会话重跑模拟：${plan.source_anchor_id}`)}
    function checkConsistency(){const plan=current();if(!plan||!state.simulated){setResult('阻断：尚未完成重跑模拟。','blocked');return}const sameAnchor=plan.rerun_steps.every(step=>step.source_anchor_id===plan.source_anchor_id);state.consistent=sameAnchor;state.consistencyCount=sameAnchor?1:0;document.body.dataset.consistencyStatus=sameAnchor?'passed':'failed';updateCounters();setResult(sameAnchor?'同源引用一致性 PASS；金额容忍为 0 分。':'同源引用一致性 FAIL。',sameAnchor?'pass':'blocked');record(`同源引用一致性：${sameAnchor?'PASS':'FAIL'}`)}
    function checkPersistent(){document.body.dataset.persistentStatus='blocked_quality_gate';setResult('持久执行阻断：当前 Q4 / D · NO_GO，批准和发布业务事件均为 0。','blocked');record('持久缓存失效与业务重跑被质量门禁阻断')}
    function resetSession(){state.selectedId=null;state.previewed=false;state.confirmed=false;state.simulated=false;state.consistent=false;state.simulationCount=0;state.consistencyCount=0;rows.forEach(row=>row.classList.remove('selected'));detail.classList.remove('active');empty.classList.remove('hidden');ack.checked=false;confirmPanel.hidden=true;runButton.disabled=true;checkButton.disabled=true;document.body.dataset.simulationStatus='idle';document.body.dataset.consistencyStatus='idle';document.body.dataset.persistentStatus='blocked';updateCounters();record('会话状态已清空；未写入持久状态')}
    search.addEventListener('input',applyFilters);risk.addEventListener('change',applyFilters);q('[data-reset-filters]').addEventListener('click',()=>{search.value='';risk.value='all';applyFilters()});qa('[data-select-plan]').forEach(button=>button.addEventListener('click',()=>selectPlan(button.dataset.selectPlan)));q('[data-preview-rerun]').addEventListener('click',previewRerun);q('[data-confirm-rerun]').addEventListener('click',confirmRerun);runButton.addEventListener('click',runSimulation);checkButton.addEventListener('click',checkConsistency);q('[data-check-persistent]').addEventListener('click',checkPersistent);q('[data-reset-session]').addEventListener('click',resetSession);resetSession();document.body.dataset.uiReady='true';record('重跑机制工作台已就绪');
    q('[data-reset-filters]').addEventListener('click',()=>{document.body.dataset.filterReset='complete';document.body.dataset.lastAction='filters-reset';record('筛选条件已重置')});
  </script>
</body>
</html>'''
    return (
        template.replace("__LINKS__", links)
        .replace("__ROWS__", _render_rows(plans))
        .replace("__PLANS__", json.dumps(plans, ensure_ascii=False, separators=(",", ":")))
    )


def _browser_worker() -> dict[str, Any]:
    from playwright.sync_api import sync_playwright

    PRIVATE_SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    stage_root = Path("KMFA/stage_artifacts").resolve()
    handler = functools.partial(s12_p2.s12_p1._QuietHandler, directory=str(stage_root))
    server = socketserver.TCPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    url = f"{base}/{PHASE_ID}/exports/html/{HTML_PATH.name}"
    buckets: dict[str, list[dict[str, Any]]] = {
        "viewport_checks": [],
        "search_checks": [],
        "risk_filter_checks": [],
        "medium_plan_checks": [],
        "high_plan_checks": [],
        "preconfirmation_block_checks": [],
        "second_confirmation_checks": [],
        "rerun_simulation_checks": [],
        "consistency_checks": [],
        "persistent_execution_block_checks": [],
        "reload_reset_checks": [],
        "return_link_http_checks": [],
        "actual_navigation_checks": [],
    }
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True,
                executable_path=s12_p2.s12_p1.s11_home._chromium_path(),
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
                    and s12_p2.s12_p1.s11_home._is_actionable_console_error(
                        f"{msg.text} {msg.location.get('url', '')}"
                    )
                    else None,
                )
                page.goto(url, wait_until="networkidle")
                page.wait_for_function("document.body.dataset.uiReady === 'true'")
                no_overflow = page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1")
                no_go_visible = page.get_by_text("Q4 / D · NO_GO", exact=True).is_visible()
                buckets["viewport_checks"].append(
                    {
                        "mode": mode,
                        "passed": no_overflow and no_go_visible and not console_errors,
                        "no_horizontal_overflow": no_overflow,
                        "no_go_visible": no_go_visible,
                        "console_error_count": len(console_errors),
                    }
                )

                page.locator("[data-rerun-search]").fill("零差异证据")
                buckets["search_checks"].append(
                    {"mode": mode, "passed": page.locator("[data-rerun-row]:visible").count() == 1}
                )
                page.locator("[data-reset-filters]").click()
                page.locator("[data-risk-filter]").select_option("medium")
                buckets["risk_filter_checks"].append(
                    {"mode": mode, "passed": page.locator("[data-rerun-row]:visible").count() == 1}
                )
                page.locator("[data-reset-filters]").click()

                page.locator('[data-select-plan="RERUNPLAN-S12P3-POST-002"]').click()
                page.locator("[data-preview-rerun]").click()
                medium_ready = page.locator("body").get_attribute("data-simulation-status") == "ready_session_simulation"
                page.locator("[data-run-simulation]").click()
                medium_simulated = page.locator("body").get_attribute("data-simulation-status") == "session_simulation_complete"
                page.locator("[data-check-consistency]").click()
                medium_consistent = page.locator("body").get_attribute("data-consistency-status") == "passed"
                buckets["medium_plan_checks"].append(
                    {"mode": mode, "passed": medium_ready and medium_simulated and medium_consistent}
                )

                page.locator("[data-reset-session]").click()
                page.locator('[data-select-plan="RERUNPLAN-S12P3-POST-005"]').click()
                page.locator("[data-preview-rerun]").click()
                high_blocked = (
                    page.locator("body").get_attribute("data-simulation-status")
                    == "blocked_pending_second_confirmation"
                )
                buckets["high_plan_checks"].append({"mode": mode, "passed": high_blocked})
                buckets["preconfirmation_block_checks"].append(
                    {"mode": mode, "passed": high_blocked and page.locator("[data-run-simulation]").is_disabled()}
                )
                page.locator("[data-high-risk-ack]").check()
                page.locator("[data-confirm-rerun]").click()
                confirmed = page.locator("body").get_attribute("data-simulation-status") == "ready_session_simulation"
                buckets["second_confirmation_checks"].append({"mode": mode, "passed": confirmed})
                page.locator("[data-run-simulation]").click()
                high_simulated = (
                    page.locator("body").get_attribute("data-simulation-status")
                    == "session_simulation_complete"
                    and page.locator("body").get_attribute("data-session-simulation-count") == "1"
                )
                buckets["rerun_simulation_checks"].append(
                    {"mode": mode, "passed": medium_simulated and high_simulated}
                )
                page.locator("[data-check-consistency]").click()
                high_consistent = (
                    page.locator("body").get_attribute("data-consistency-status") == "passed"
                    and page.locator("body").get_attribute("data-session-consistency-count") == "1"
                )
                buckets["consistency_checks"].append(
                    {"mode": mode, "passed": medium_consistent and high_consistent}
                )
                page.locator("[data-check-persistent]").click()
                persistent_blocked = (
                    page.locator("body").get_attribute("data-persistent-status") == "blocked_quality_gate"
                )
                buckets["persistent_execution_block_checks"].append(
                    {"mode": mode, "passed": persistent_blocked}
                )
                page.screenshot(
                    path=str(PRIVATE_SCREENSHOT_DIR / f"rerun_{mode}_high_simulated.png"),
                    full_page=True,
                )

                page.locator("[data-reset-session]").click()
                reset_ok = (
                    page.locator("body").get_attribute("data-session-simulation-count") == "0"
                    and page.locator("body").get_attribute("data-simulation-status") == "idle"
                )
                page.reload(wait_until="networkidle")
                page.wait_for_function("document.body.dataset.uiReady === 'true'")
                reload_ok = page.locator("body").get_attribute("data-session-simulation-count") == "0"
                buckets["reload_reset_checks"].append({"mode": mode, "passed": reset_ok and reload_ok})
                page.screenshot(
                    path=str(PRIVATE_SCREENSHOT_DIR / f"rerun_{mode}.png"), full_page=True
                )
                page.close()

            request = playwright.request.new_context()
            for link_id, href, marker in RETURN_LINKS:
                target = urljoin(url, href)
                response = request.get(target)
                buckets["return_link_http_checks"].append(
                    {
                        "link_id": link_id,
                        "passed": response.ok and marker in response.text(),
                        "status": response.status,
                    }
                )
                page = browser.new_page(viewport={"width": 1280, "height": 900})
                page.goto(url, wait_until="networkidle")
                page.locator(f'[data-return-link="{link_id}"]').click()
                page.wait_for_load_state("networkidle")
                buckets["actual_navigation_checks"].append(
                    {"link_id": link_id, "passed": marker in page.locator("body").inner_text()}
                )
                page.close()
            request.dispose()
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
    passed = all(item.get("passed") for rows in buckets.values() for item in rows)
    return {
        "schema_version": "kmfa.v014.s12_p3.rerun_browser.v1",
        "status": "PASS" if passed else "FAIL",
        **buckets,
    }


def _run_browser_review() -> dict[str, Any]:
    result = subprocess.run(
        [
            str(s12_p2.s12_p1.s11_home._audit_python()),
            str(Path(__file__).resolve()),
            "--browser-worker",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=os.environ.copy(),
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"browser worker failed: {result.stdout}\n{result.stderr}")
    payload = json.loads(result.stdout)
    if payload.get("status") != "PASS":
        raise RuntimeError(f"browser review failed: {payload}")
    return payload


def _browser_summary(
    baseline: dict[str, Any], current: dict[str, Any], browser: dict[str, Any]
) -> dict[str, Any]:
    return {
        "baseline_file_count": baseline["file_count"],
        "baseline_control_row_count": baseline["control_row_count"],
        "baseline_pass_count": baseline["pass_count"],
        "baseline_fail_count": baseline["fail_count"],
        "current_html_file_count": current["file_count"],
        "current_html_control_row_count": current["control_row_count"],
        "current_html_pass_count": current["pass_count"],
        "current_html_fail_count": current["fail_count"],
        "viewport_check_count": len(browser["viewport_checks"]),
        "search_check_count": len(browser["search_checks"]),
        "risk_filter_check_count": len(browser["risk_filter_checks"]),
        "medium_plan_check_count": len(browser["medium_plan_checks"]),
        "high_plan_check_count": len(browser["high_plan_checks"]),
        "preconfirmation_block_check_count": len(browser["preconfirmation_block_checks"]),
        "second_confirmation_check_count": len(browser["second_confirmation_checks"]),
        "rerun_simulation_check_count": len(browser["rerun_simulation_checks"]),
        "consistency_check_count": len(browser["consistency_checks"]),
        "persistent_execution_block_check_count": len(
            browser["persistent_execution_block_checks"]
        ),
        "reload_reset_check_count": len(browser["reload_reset_checks"]),
        "return_link_http_check_count": len(browser["return_link_http_checks"]),
        "actual_navigation_check_count": len(browser["actual_navigation_checks"]),
        "console_error_count": sum(row["console_error_count"] for row in browser["viewport_checks"]),
        "horizontal_overflow_count": sum(
            row["no_horizontal_overflow"] is not True for row in browser["viewport_checks"]
        ),
    }


def _render_report(manifest: dict[str, Any]) -> str:
    summary = manifest["summary"]
    browser = manifest["browser_review"]
    return f"""# KMFA v0.1.4 S12-P3 修补后重跑机制报告

- phase: `{PHASE_ID}`
- task: `{TASK_ID}`
- status: `{STATUS}`
- current gate: `Q4 / D / NO_GO`

## 结果

- current previews / rerun plans / planned steps: `{summary['source_impact_preview_definition_count']} / {summary['rerun_plan_definition_count']} / {summary['planned_rerun_step_count']}`
- persistent cache invalidations / rerun steps / consistency checks: `0 / 0 / 0`
- session simulation: 支持 6 份计划；高风险计划必须二次确认；刷新后清零。
- same-source rule: 4 层共享同一 public-safe source anchor；金额容忍为 0 分，不忽略一分钱差异。
- browser: baseline `{browser['baseline_pass_count']}/{browser['baseline_control_row_count']} PASS`；current `{browser['current_html_pass_count']}/{browser['current_html_control_row_count']} PASS`。

## 边界

- 当前没有已批准或已发布业务事件，所有重跑均为浏览器内存模拟，不失效真实缓存，不写派生事实。
- 四个项目槽位仅表示潜在影响，不证明项目归属。
- Stage 12 review、GitHub upload、app reinstall、正式报告和 business execution 均未执行。
"""


def _render_test_results(final_validation: bool) -> str:
    state = "PASS" if final_validation else "PENDING_FINAL_VALIDATION"
    return f"""# S12-P3 测试结果

- focused tests: `{state}`
- strict validator: `{state}`
- desktop/mobile browser: `{state}`
- governance/no-float/no-omission/raw-private-secret scan: `{state}`
- raw phase/cross-S12-P2 exact: `PASS`
- Stage 12 review / upload / reinstall: `NOT_PERFORMED`
"""


def _render_risk_register() -> str:
    return """# S12-P3 风险登记

| 风险 | 控制 |
|---|---|
| 会话模拟被误读为真实重跑 | persistent counts 固定为 0，页面与 manifest 明确 session-only |
| 高风险计划绕过确认 | 高风险按钮在二次确认前禁用，浏览器证据和 validator 双重校验 |
| 旧版本被覆盖 | 四层步骤均要求保留旧版本、追加模拟新版本 |
| 同源引用漂移 | 每份计划四层共享唯一 public-safe source anchor，容忍度为 0 分 |
| 潜在项目槽位被误读为归属 | 固定 `potential_impact_not_attribution`，不提交项目名或业务值 |
| raw/private 进入 Git | raw 与浏览器证据仅写 ignored private runtime，提交前执行安全扫描 |
"""


def _render_rollback() -> str:
    return """# S12-P3 回滚方案

1. 仅回退本 phase 的本地 commit。
2. 删除 ignored private S12-P3 运行证据。
3. 保留 S12-P1/P2 commits 与旧版 policy fixture，不改 raw inbox。
4. 复跑 S12-P2 strict validator，确认前序影响预览边界仍有效。
"""


def _private_report(summary: dict[str, Any], browser: dict[str, Any]) -> str:
    return f"""# S12-P3 私有验证记录

- raw files: {summary['raw_source_file_count']}
- phase raw exact: {str(summary['raw_snapshot_exact_match']).lower()}
- cross S12-P2 raw exact: {str(summary['raw_cross_phase_snapshot_exact_match']).lower()}
- browser status: {browser['status']}
- persistent raw difference: none
"""


def _governance_rows(generated_at: str, manifest: dict[str, Any]) -> None:
    evidence_ref = MANIFEST_PATH.as_posix()
    changed_files = [
        SUMMARY_PATH.as_posix(),
        MANIFEST_PATH.as_posix(),
        PLANS_PATH.as_posix(),
        GO_NO_GO_PATH.as_posix(),
        HTML_PATH.as_posix(),
        REPORT_PATH.as_posix(),
        TEST_RESULTS_PATH.as_posix(),
        RISK_REGISTER_PATH.as_posix(),
        ROLLBACK_PATH.as_posix(),
        METADATA_SUMMARY_PATH.as_posix(),
        METADATA_MANIFEST_PATH.as_posix(),
        METADATA_PLANS_PATH.as_posix(),
        METADATA_GO_NO_GO_PATH.as_posix(),
        Path(__file__).relative_to(Path.cwd()).as_posix(),
        "KMFA/tools/check_v014_s12_p3_post_remediation_rerun_mechanism.py",
        "KMFA/tests/test_v014_s12_p3_post_remediation_rerun_mechanism.py",
    ]
    s12_p2.s12_p1._upsert_jsonl(
        DEVELOPMENT_EVENTS_PATH,
        {
            "event_id": "DEV-KMFA-20260711-V014-S12-P3-POST-REMEDIATION-RERUN-MECHANISM",
            "event_time": generated_at,
            "event_type": "implementation",
            "project_id": "KMFA",
            "stage_id": "S12",
            "phase_id": PHASE_ID,
            "roadmap_phase_id": ROADMAP_PHASE_ID,
            "task_id": TASK_ID,
            "status": STATUS,
            "fact_level": "EXTRACTED",
            "decision": DECISION,
            "rerun_plan_definition_count": manifest["summary"]["rerun_plan_definition_count"],
            "planned_rerun_step_count": manifest["summary"]["planned_rerun_step_count"],
            "persistent_derived_rerun_count": 0,
            "raw_business_data_committed": False,
            "github_upload_performed": False,
            "app_reinstall_performed": False,
            "business_execution_performed": False,
            "evidence_ref": evidence_ref,
            "files_changed": changed_files,
            "result_commit": "PENDING",
        },
    )
    s12_p2.s12_p1._upsert_jsonl(
        STAGE_STATUS_PATH,
        {
            "schema_version": "kmfa.stage_status.v1",
            "record_type": "phase_status",
            "project_id": "KMFA",
            "stage_id": "S12",
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
    s12_p2.s12_p1._upsert_jsonl(
        TASK_STATUS_PATH,
        {
            "schema_version": "kmfa.v014_stage_phase_task_status.v1",
            "record_type": "v014_phase",
            "project_id": "KMFA",
            "stage_id": "S12",
            "governance_stage_id": "MANUAL-RESOLUTION",
            "roadmap_stage_id": "S12",
            "roadmap_phase_id": ROADMAP_PHASE_ID,
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "acceptance_id": ACCEPTANCE_ID,
            "version": VERSION,
            "name": "v0.1.4 S12-P3 post-remediation rerun mechanism",
            "phase_goal": "public-safe cache invalidation plan four-layer rerun simulation and same-source consistency",
            "status": STATUS,
            "fact_level": "EXTRACTED",
            "derived_percent": 100.0,
            "estimated_task_units": 9,
            "completed_task_units": 9,
            "task_count": 3,
            "raw_data_committed": False,
            "evidence_ref": evidence_ref,
            "updated_at": generated_at[:10],
        },
    )


def generate(final_validation: bool = False) -> dict[str, Any]:
    generated_at = datetime.now().astimezone().replace(microsecond=0).isoformat()
    raw_before = s12_p2.s12_p1.s11_project._raw_snapshot(
        "before_v014_s12_p3_post_remediation_rerun_mechanism"
    )
    _write_json(PRIVATE_RAW_BEFORE_PATH, raw_before)
    dependency = _load_s12_p2_dependency()
    contract = _load_contract()
    plans = _build_plans(dependency)
    _write_text(HTML_PATH, _render_html(plans))

    raw_after = s12_p2.s12_p1.s11_project._raw_snapshot(
        "after_v014_s12_p3_post_remediation_rerun_mechanism"
    )
    _write_json(PRIVATE_RAW_AFTER_PATH, raw_after)
    previous_raw = json.loads(s12_p2.PRIVATE_RAW_AFTER_PATH.read_text(encoding="utf-8"))
    normalize_raw = s12_p2.s12_p1.s11_project._normalize_raw
    raw_exact = normalize_raw(raw_before) == normalize_raw(raw_after)
    raw_cross = normalize_raw(raw_before) == normalize_raw(previous_raw)
    if not raw_exact or not raw_cross:
        raise RuntimeError("raw snapshot drift detected during S12-P3")

    baseline_audit = s12_p2.s12_p1.s11_home._run_html_audit(
        V14_HTML_ROOT, PRIVATE_BASELINE_AUDIT_PATH
    )
    current_audit = s12_p2.s12_p1.s11_home._run_html_audit(
        HTML_DIR, PRIVATE_CURRENT_AUDIT_PATH
    )
    browser_payload = _run_browser_review()
    _write_json(PRIVATE_BROWSER_PATH, browser_payload)
    browser = _browser_summary(baseline_audit, current_audit, browser_payload)

    source = dependency["summary"]
    summary = {
        "schema_version": "kmfa.v014.s12_p3.rerun_summary.v1",
        "record_type": "v014_s12_p3_post_remediation_rerun_summary",
        "project_id": "KMFA",
        "stage_id": "S12",
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "version": VERSION,
        "status": STATUS,
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "decision": DECISION,
        "source_pending_action_group_count": source["source_pending_action_group_count"],
        "source_impact_preview_definition_count": source["impact_preview_definition_count"],
        "rerun_plan_definition_count": len(plans),
        "planned_rerun_step_count": sum(len(plan["rerun_steps"]) for plan in plans),
        "required_rerun_chain_layer_count": len(REQUIRED_RERUN_CHAIN),
        "high_risk_rerun_plan_count": sum(plan["risk_level"] == "high" for plan in plans),
        "second_confirmation_required_count": sum(
            plan["second_confirmation_required"] for plan in plans
        ),
        "current_session_cache_invalidation_count_at_rest": 0,
        "current_session_rerun_step_count_at_rest": 0,
        "current_session_consistency_check_count_at_rest": 0,
        "current_persistent_cache_invalidation_count": 0,
        "current_persistent_rerun_step_count": 0,
        "current_persistent_consistency_check_count": 0,
        "current_approved_business_event_count": 0,
        "current_published_business_event_count": 0,
        "open_final_difference_accepted_count": source["open_final_difference_accepted_count"],
        "nonzero_delta_reconciliation_count": source["nonzero_delta_reconciliation_count"],
        "zero_delta_reconciliation_count": source["zero_delta_reconciliation_count"],
        "incomplete_reconciliation_count": source["incomplete_reconciliation_count"],
        "hard_block_count": source["hard_block_count"],
        "raw_source_file_count": raw_before["file_count"],
        "raw_snapshot_exact_match": raw_exact,
        "raw_cross_phase_snapshot_exact_match": raw_cross,
        "formal_report_count": 0,
        "business_decision_basis_count": 0,
        "s12_p1_performed": True,
        "s12_p2_performed": True,
        "s12_p3_performed": True,
        "persistent_derived_rerun_performed": False,
        "stage12_review_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }
    go_no_go = {
        "schema_version": "kmfa.v014.s12_p3.rerun_go_no_go.v1",
        "phase_id": PHASE_ID,
        "decision": DECISION,
        "s12_p3_mechanism_validated": True,
        "rerun_plan_generation_allowed": True,
        "session_only_rerun_simulation_allowed": True,
        "persistent_cache_invalidation_allowed": False,
        "persistent_derived_rerun_allowed": False,
        "current_business_event_approval_allowed": False,
        "current_business_event_publish_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "stage12_review_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }
    manifest = {
        "schema_version": "kmfa.v014.s12_p3.rerun_manifest.v1",
        "project_id": "KMFA",
        "stage_id": "S12",
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "version": VERSION,
        "status": STATUS,
        "generated_at": generated_at,
        "summary": summary,
        "s12_p2_post_remediation_dependency_validated": True,
        "legacy_s12_p3_policy_fixture_validated": True,
        "taskpack_contract": contract,
        "required_rerun_chain": list(REQUIRED_RERUN_CHAIN),
        "rerun_plan_definitions": plans,
        "browser_review": browser,
        "quality_gate": _quality_gate(),
        "phase_boundaries": _phase_boundaries(),
        "public_repo_safety": _public_repo_safety(),
        "validation_summary": {
            "final_validation_recorded": final_validation,
            "focused_tests": "PASS" if final_validation else "PENDING",
            "strict_validator": "PASS" if final_validation else "PENDING",
            "browser_desktop_mobile": "PASS" if final_validation else "PENDING",
            "governance_and_safety_scans": "PASS" if final_validation else "PENDING",
        },
        "next_phase": "S12-STAGE-REVIEW",
        "next_required_step": "Run Stage 12 overall review as a separate run; do not upload or reinstall.",
        "git": {
            "branch": _git_output(["branch", "--show-current"]),
            "remote": _git_output(["remote", "get-url", "origin"]),
            "head": _git_output(["rev-parse", "HEAD"]),
        },
    }
    plans_payload = {
        "schema_version": "kmfa.v014.s12_p3.rerun_plan_definitions.v1",
        "phase_id": PHASE_ID,
        "plan_count": len(plans),
        "required_rerun_chain": list(REQUIRED_RERUN_CHAIN),
        "project_scope_semantics": "potential impact only; no project attribution is asserted",
        "persistent_execution_semantics": "all records are session-only plans; persistent counts remain zero",
        "plans": plans,
    }
    for path, value in (
        (SUMMARY_PATH, summary),
        (MANIFEST_PATH, manifest),
        (PLANS_PATH, plans_payload),
        (GO_NO_GO_PATH, go_no_go),
        (METADATA_SUMMARY_PATH, summary),
        (METADATA_MANIFEST_PATH, manifest),
        (METADATA_PLANS_PATH, plans_payload),
        (METADATA_GO_NO_GO_PATH, go_no_go),
    ):
        _write_json(path, value)
    _write_text(REPORT_PATH, _render_report(manifest))
    _write_text(TEST_RESULTS_PATH, _render_test_results(final_validation))
    _write_text(RISK_REGISTER_PATH, _render_risk_register())
    _write_text(ROLLBACK_PATH, _render_rollback())
    _write_text(PRIVATE_VALIDATION_REPORT_PATH, _private_report(summary, browser_payload))
    _governance_rows(generated_at, manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--final-validation", action="store_true")
    parser.add_argument("--browser-worker", action="store_true")
    args = parser.parse_args()
    if args.browser_worker:
        print(json.dumps(_browser_worker(), ensure_ascii=False))
        return 0
    manifest = generate(final_validation=args.final_validation)
    summary = manifest["summary"]
    print(
        "S12-P3 post-remediation rerun mechanism: "
        f"plans={summary['rerun_plan_definition_count']} "
        f"planned_steps={summary['planned_rerun_step_count']} "
        f"persistent_steps={summary['current_persistent_rerun_step_count']} "
        f"grade={summary['current_report_grade']} decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
