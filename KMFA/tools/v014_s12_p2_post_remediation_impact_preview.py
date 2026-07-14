#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate current public-safe KMFA S12-P2 impact-preview evidence."""

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

from KMFA.tools import v014_s12_p1_post_remediation_pending_actions as s12_p1
from KMFA.tools import v014_s12_p2_manual_impact_preview as legacy_s12_p2
from KMFA.tools.check_v014_s12_p1_post_remediation_pending_actions import (
    validate_v014_s12_p1_post_remediation_pending_actions,
)


PHASE_ID = "V014_S12_P2_POST_REMEDIATION_IMPACT_PREVIEW"
ROADMAP_PHASE_ID = "S12-P2"
TASK_ID = "KMFA-V014-S12-P2-POST-REMEDIATION-IMPACT-PREVIEW-20260711"
ACCEPTANCE_ID = "ACC-V014-S12-P2-POST-REMEDIATION-IMPACT-PREVIEW"
VERSION = "0.1.4-s12-p2-post-remediation-impact-preview"
STATUS = "completed_validated_local_only_s12_p2_no_go_upload_deferred"
DECISION = "NO_GO"
FORMULA_ID = "FORM-KMFA-V014-S12P2-POST-REMEDIATION-IMPACT-PREVIEW-001"
PARAMETER_IDS = (
    "PARAM-KMFA-1724",
    "PARAM-KMFA-1725",
    "PARAM-KMFA-1726",
    "PARAM-KMFA-1727",
)
MODEL_REGISTRY_KEY = "kmfa_v014_s12_p2_post_remediation_impact_preview"

OUTPUT_DIR = Path("KMFA/stage_artifacts") / PHASE_ID
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
HTML_DIR = OUTPUT_DIR / "exports/html"
SUMMARY_PATH = MACHINE_DIR / "impact_preview_summary.json"
MANIFEST_PATH = MACHINE_DIR / "impact_preview_manifest.json"
PREVIEWS_PATH = MACHINE_DIR / "impact_preview_definitions_public_safe.json"
GO_NO_GO_PATH = MACHINE_DIR / "impact_preview_go_no_go_report.json"
HTML_PATH = HTML_DIR / "kmfa_impact_preview_workbench.html"
REPORT_PATH = HUMAN_DIR / "s12_p2_impact_preview_report_zh.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results_zh.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register_zh.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan_zh.md"

QUALITY_DIR = Path("KMFA/metadata/quality")
METADATA_SUMMARY_PATH = QUALITY_DIR / "v014_s12_p2_post_remediation_impact_preview_summary.json"
METADATA_MANIFEST_PATH = QUALITY_DIR / "v014_s12_p2_post_remediation_impact_preview_manifest.json"
METADATA_PREVIEWS_PATH = QUALITY_DIR / "v014_s12_p2_post_remediation_impact_preview_definitions_public_safe.json"
METADATA_GO_NO_GO_PATH = QUALITY_DIR / "v014_s12_p2_post_remediation_impact_preview_go_no_go_report.json"

PRIVATE_DIR = Path("KMFA/.codex_private_runtime/v014_s12_p2_post_remediation_impact_preview")
PRIVATE_RAW_BEFORE_PATH = PRIVATE_DIR / "raw_immutability_before.json"
PRIVATE_RAW_AFTER_PATH = PRIVATE_DIR / "raw_immutability_after.json"
PRIVATE_BROWSER_PATH = PRIVATE_DIR / "browser_verification.json"
PRIVATE_BASELINE_AUDIT_PATH = PRIVATE_DIR / "human_flow_baseline_audit.csv"
PRIVATE_CURRENT_AUDIT_PATH = PRIVATE_DIR / "current_impact_preview_audit.csv"
PRIVATE_VALIDATION_REPORT_PATH = PRIVATE_DIR / "s12_p2_private_validation_zh.md"
PRIVATE_SCREENSHOT_DIR = PRIVATE_DIR / "screenshots"

VERSION_MATRIX_PATH = Path("KMFA/docs/governance/VERSION_MATRIX.yaml")
V14_ROADMAP_PATH = s12_p1.V14_ROADMAP_PATH
V14_TASKPACK_PATH = s12_p1.V14_TASKPACK_PATH
V14_WORKBENCH_PATH = s12_p1.V14_WORKBENCH_PATH
V14_HTML_ROOT = s12_p1.V14_HTML_ROOT

DEVELOPMENT_EVENTS_PATH = s12_p1.DEVELOPMENT_EVENTS_PATH
STAGE_STATUS_PATH = s12_p1.STAGE_STATUS_PATH
TASK_STATUS_PATH = s12_p1.TASK_STATUS_PATH

P1_HREF = "../../../V014_S12_P1_POST_REMEDIATION_PENDING_ACTIONS/exports/html/kmfa_pending_actions_workbench.html"
P3_HREF = "../../../V014_S12_P3_POST_REMEDIATION_RERUN_MECHANISM/exports/html/kmfa_rerun_workbench.html"
HOME_HREF = s12_p1.HOME_HREF
SOURCE_HREF = s12_p1.SOURCE_HREF
PROJECT_HREF = s12_p1.PROJECT_HREF
RETURN_LINKS = (
    ("pending", P1_HREF, "待处理事项"),
    ("rerun", P3_HREF, "KMFA 重跑机制"),
    ("home", HOME_HREF, "经营分析工作台"),
    ("source", SOURCE_HREF, "KMFA 数据源检查板"),
    ("project", PROJECT_HREF, "KMFA 项目成本页面"),
)

RISK_LABELS = {"medium": "中风险", "high": "高风险"}
KIND_LABELS = s12_p1.ACTION_LABELS


def _write_json(path: Path, value: Any) -> None:
    s12_p1._write_json(path, value)


def _write_text(path: Path, value: str) -> None:
    s12_p1._write_text(path, value)


def _git_output(args: list[str]) -> str:
    return s12_p1._git_output(args)


def _load_s12_p1_dependency() -> dict[str, Any]:
    manifest = validate_v014_s12_p1_post_remediation_pending_actions(
        require_private_evidence=True,
        require_browser_evidence=True,
        require_final_evidence=True,
    )
    summary = manifest["summary"]
    expected = {
        "pending_action_group_count": 6,
        "manual_event_template_count": 4,
        "current_approved_business_event_count": 0,
        "open_final_difference_accepted_count": 3,
        "nonzero_delta_reconciliation_count": 9,
        "zero_delta_reconciliation_count": 2,
        "incomplete_reconciliation_count": 1,
        "project_specific_unknown_allocation_count": 4,
        "source_check_matrix_row_count": 13,
        "hard_block_count": 12,
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "decision": "NO_GO",
        "s12_p2_performed": False,
        "s12_p3_performed": False,
        "stage12_review_performed": False,
        "github_upload_performed": False,
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            raise RuntimeError(f"S12-P1 dependency drift: {key}")
    return manifest


def _load_contract() -> dict[str, Any]:
    roadmap = V14_ROADMAP_PATH.read_text(encoding="utf-8")
    taskpack = V14_TASKPACK_PATH.read_text(encoding="utf-8")
    sample = V14_WORKBENCH_PATH.read_text(encoding="utf-8")
    for token in (
        "处理事件提交前展示影响哪些项目、指标、报告",
        "高风险处理需要二次确认",
        "未通过影响预览不得发布",
    ):
        if token not in roadmap:
            raise RuntimeError(f"v1.4 roadmap S12-P2 token missing: {token}")
    for token in ("待处理事项必须有处理意见、影响预览、重跑链路", "FAIL = 0"):
        if token not in taskpack:
            raise RuntimeError(f"v1.4 taskpack token missing: {token}")
    for token in ("生成影响预览", "受影响链路", "影响预览"):
        if token not in sample:
            raise RuntimeError(f"v1.4 workbench token missing: {token}")
    legacy = legacy_s12_p2.validate_legacy_s12_p2_artifacts()
    if legacy["impact_preview_count"] != 5 or legacy["high_risk_count"] != 3:
        raise RuntimeError("legacy S12-P2 policy fixture drift")
    if legacy["second_confirmation_required_count"] != legacy["high_risk_count"]:
        raise RuntimeError("legacy high-risk confirmation policy invalid")
    return {
        "roadmap_contract_read": True,
        "taskpack_human_flow_gate_read": True,
        "clickable_workbench_sample_read": True,
        "required_impact_domains": ["affected_projects", "affected_metrics", "affected_reports"],
        "legacy_policy_fixture_preview_count": legacy["impact_preview_count"],
        "legacy_policy_fixture_high_risk_count": legacy["high_risk_count"],
        "legacy_policy_fixture_confirmation_rule_validated": True,
        "legacy_dynamic_counts_applied_to_current_state": False,
        "source_refs": [
            V14_ROADMAP_PATH.as_posix(),
            V14_TASKPACK_PATH.as_posix(),
            V14_WORKBENCH_PATH.as_posix(),
            legacy_s12_p2.MANIFEST_PATH.as_posix(),
        ],
    }


def _preview_specs() -> dict[str, dict[str, Any]]:
    return {
        "PEND-S12P1-001": {
            "risk_level": "high",
            "affected_project_slot_count": 4,
            "affected_project_scope": ["四个未证明归属的潜在项目槽位"],
            "affected_metrics": ["差异状态", "报告可信等级", "待处理状态"],
            "affected_reports": ["项目成本受限预览", "经营总览受限预览"],
            "impact_reason": "非零差异处理可能改变差异状态和报告可信等级，必须二次确认。",
        },
        "PEND-S12P1-002": {
            "risk_level": "medium",
            "affected_project_slot_count": 0,
            "affected_project_scope": ["不形成项目级归属；仅影响全局证据范围"],
            "affected_metrics": ["零差异证据状态", "复核说明完整性"],
            "affected_reports": ["待处理事项工作台", "数据质量证据摘要"],
            "impact_reason": "公开安全复核备注只影响证据说明，不改变业务值或项目归属。",
        },
        "PEND-S12P1-003": {
            "risk_level": "high",
            "affected_project_slot_count": 4,
            "affected_project_scope": ["四个未证明归属的潜在项目槽位"],
            "affected_metrics": ["未完成比较状态", "现金链路完整性", "报告可信等级"],
            "affected_reports": ["项目成本受限预览", "经营总览受限预览"],
            "impact_reason": "补全未完成比较可能影响现金链路和报告等级，必须二次确认。",
        },
        "PEND-S12P1-004": {
            "risk_level": "high",
            "affected_project_slot_count": 4,
            "affected_project_scope": ["四个未证明归属的潜在项目槽位"],
            "affected_metrics": ["最终接受状态", "差异说明完整性", "报告限制状态"],
            "affected_reports": ["项目成本受限预览", "经营总览受限预览", "待处理事项工作台"],
            "impact_reason": "最终差异接受说明可能被误读为项目归属或放行结论，必须二次确认。",
        },
        "PEND-S12P1-005": {
            "risk_level": "high",
            "affected_project_slot_count": 4,
            "affected_project_scope": ["四个未证明归属的潜在项目槽位"],
            "affected_metrics": ["项目匹配状态", "项目毛利槽位绑定", "回款槽位绑定"],
            "affected_reports": ["项目成本页面", "经营总览受限预览", "待处理事项工作台"],
            "impact_reason": "项目匹配可能改变分组和报告汇总口径，必须二次确认且不得自动归属。",
        },
        "PEND-S12P1-006": {
            "risk_level": "high",
            "affected_project_slot_count": 4,
            "affected_project_scope": ["四个未证明归属的潜在项目槽位"],
            "affected_metrics": ["来源就绪状态", "字段映射状态", "报告可用性"],
            "affected_reports": ["数据源检查板", "项目成本受限预览", "经营总览受限预览"],
            "impact_reason": "字段映射可能影响来源状态和报告可用性，必须二次确认。",
        },
    }


def _build_previews(dependency: dict[str, Any]) -> list[dict[str, Any]]:
    templates = {
        row["manual_action_kind"]: row for row in dependency["manual_event_templates"]
    }
    specs = _preview_specs()
    previews: list[dict[str, Any]] = []
    for index, group in enumerate(dependency["pending_action_groups"], start=1):
        spec = specs[group["group_id"]]
        template = templates[group["manual_action_kind"]]
        high_risk = spec["risk_level"] == "high"
        previews.append(
            {
                "schema_version": "kmfa.v014.s12_p2.impact_preview_definition.v1",
                "record_type": "public_safe_session_impact_preview_definition",
                "preview_id": f"IMPREV-S12P2-POST-{index:03d}",
                "source_group_id": group["group_id"],
                "source_group_title": group["visible_title"],
                "source_group_item_count": group["item_count"],
                "source_event_template_id": template["event_id"],
                "manual_action_kind": group["manual_action_kind"],
                "risk_level": spec["risk_level"],
                "second_confirmation_required": high_risk,
                "second_confirmation_status": "required_in_session" if high_risk else "not_required",
                "project_attribution": "unproven_or_not_applicable",
                "project_scope_semantics": "potential_impact_not_attribution",
                "affected_project_slot_count": spec["affected_project_slot_count"],
                "affected_project_scope": spec["affected_project_scope"],
                "affected_metrics": spec["affected_metrics"],
                "affected_reports": spec["affected_reports"],
                "impact_reason": spec["impact_reason"],
                "preview_status": "definition_ready_session_preview_required",
                "preview_passed_persistently": False,
                "session_preview_allowed": True,
                "publish_allowed": False,
                "business_event_approval_allowed": False,
                "derived_rerun_allowed": False,
                "persistent_business_write_allowed": False,
                "raw_layer_write_allowed": False,
                "business_value_committed": False,
                "preview_version": f"IMPACT-PREVIEW-S12P2-POST-001.{index:03d}",
                "source_evidence_refs": [
                    s12_p1.MANIFEST_PATH.as_posix(),
                    V14_ROADMAP_PATH.as_posix(),
                ],
            }
        )
    return previews


def _quality_gate() -> dict[str, Any]:
    return {
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "decision": DECISION,
        "release_permission": "blocked",
        "impact_preview_generation_allowed": True,
        "impact_preview_required_before_publish": True,
        "high_risk_second_confirmation_required": True,
        "unpassed_preview_publish_allowed": False,
        "current_business_event_approval_allowed": False,
        "current_business_event_publish_allowed": False,
        "derived_rerun_allowed": False,
        "persistent_business_write_allowed": False,
        "raw_layer_write_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "business_execution_allowed": False,
        "github_upload_allowed": False,
    }


def _phase_boundaries() -> dict[str, bool]:
    return {
        "s12_p1_dependency_validated": True,
        "s12_p2_performed": True,
        "s12_p3_performed": False,
        "stage12_review_performed": False,
        "derived_cache_invalidated": False,
        "derived_rerun_performed": False,
        "persistent_business_write_performed": False,
        "raw_write_performed": False,
        "raw_delete_performed": False,
        "raw_move_performed": False,
        "raw_rename_performed": False,
        "raw_overwrite_performed": False,
        "formal_report_release_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }


def _public_repo_safety() -> dict[str, bool]:
    return {
        "aggregate_only": True,
        "raw_file_committed": False,
        "raw_filename_committed": False,
        "raw_hash_committed": False,
        "field_or_header_plaintext_committed": False,
        "project_or_customer_plaintext_committed": False,
        "business_value_committed": False,
        "persistent_business_event_committed": False,
        "credential_or_secret_committed": False,
        "private_runtime_committed": False,
        "zip_excel_pdf_private_csv_or_database_committed": False,
    }


def _render_rows(previews: list[dict[str, Any]]) -> str:
    rows = []
    for preview in previews:
        search = " ".join(
            [
                preview["source_group_title"],
                KIND_LABELS[preview["manual_action_kind"]],
                RISK_LABELS[preview["risk_level"]],
                *preview["affected_metrics"],
                *preview["affected_reports"],
            ]
        )
        rows.append(
            f'''<article class="preview-card" data-preview-row data-preview-id="{html.escape(preview["preview_id"])}" data-risk="{html.escape(preview["risk_level"])}" data-search-text="{html.escape(search)}">
              <div><span class="eyebrow">{html.escape(preview["source_group_id"])}</span><h3>{html.escape(preview["source_group_title"])}</h3><p>{html.escape(preview["impact_reason"])}</p></div>
              <div class="preview-meta"><span class="risk risk-{html.escape(preview["risk_level"])}">{html.escape(RISK_LABELS[preview["risk_level"]])}</span><span>{html.escape(KIND_LABELS[preview["manual_action_kind"]])}</span><span>潜在项目槽位 {preview["affected_project_slot_count"]}</span></div>
              <button class="button button-secondary" type="button" data-generate-preview="{html.escape(preview["preview_id"])}">生成预览</button>
            </article>'''
        )
    return "\n".join(rows)


def _render_html(previews: list[dict[str, Any]]) -> str:
    links = "".join(
        f'<a data-return-link="{link_id}" href="{html.escape(href)}">{html.escape(marker)}</a>'
        for link_id, href, marker in RETURN_LINKS
    )
    template = '''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>KMFA 影响预览工作台</title>
  <style>
    :root { --navy:#102d4f; --blue:#1769aa; --blue-soft:#eaf3fb; --surface:#fff; --page:#f4f7f9; --line:#d7e0e7; --ink:#182634; --muted:#637282; --danger:#a92d25; --danger-soft:#fff0ee; --green:#16754b; --green-soft:#eaf7f1; --amber:#8a5200; --amber-soft:#fff5dc; }
    * { box-sizing:border-box; }
    body { margin:0; background:var(--page); color:var(--ink); font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Microsoft YaHei",Arial,sans-serif; font-size:14px; line-height:1.55; }
    button,input,select { font:inherit; letter-spacing:0; }
    button,a { -webkit-tap-highlight-color:transparent; }
    .topbar { display:flex; align-items:center; gap:18px; min-height:68px; padding:10px 24px; background:var(--navy); color:#fff; border-bottom:4px solid #2f81bd; }
    .brand { display:flex; align-items:center; gap:10px; min-width:205px; }.brand-mark { width:40px; height:40px; display:grid; place-items:center; border-radius:6px; background:#fff; color:var(--navy); font-weight:900; }.brand strong,.brand span { display:block; }.brand span { color:#c9dbee; font-size:12px; }
    .top-links { display:flex; flex-wrap:wrap; gap:6px; }.top-links a { color:#e5f0fa; text-decoration:none; border:1px solid rgba(255,255,255,.24); border-radius:6px; padding:7px 10px; }.top-links a:hover,.top-links a:focus-visible { background:rgba(255,255,255,.12); }
    .gate { margin-left:auto; text-align:right; }.gate span { display:block; color:#c9dbee; font-size:12px; }.gate strong { color:#fff; }
    main { width:min(1440px,100%); margin:0 auto; padding:22px 24px 40px; }
    .page-head { display:flex; justify-content:space-between; align-items:flex-start; gap:20px; margin-bottom:16px; }.page-head h1 { margin:0; color:var(--navy); font-size:27px; }.page-head p { margin:6px 0 0; color:var(--muted); }.boundary { max-width:460px; border-left:4px solid var(--danger); background:var(--danger-soft); color:#6b2a25; padding:10px 12px; }
    .metrics { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); border:1px solid var(--line); background:#fff; margin-bottom:16px; }.metric { min-width:0; padding:13px 15px; border-right:1px solid var(--line); }.metric:last-child { border-right:0; }.metric span { display:block; color:var(--muted); font-size:12px; }.metric strong { display:block; color:var(--navy); font-size:22px; margin-top:3px; }
    .layout { display:grid; grid-template-columns:minmax(360px,.82fr) minmax(0,1.18fr); gap:16px; align-items:start; }.panel { min-width:0; border:1px solid var(--line); border-radius:7px; background:#fff; }.panel-head { display:flex; justify-content:space-between; align-items:center; gap:12px; padding:14px 16px; border-bottom:1px solid var(--line); }.panel-head h2 { margin:0; color:var(--navy); font-size:18px; }
    .filters { display:grid; grid-template-columns:1fr 150px auto; gap:8px; padding:12px; background:#f8fafb; border-bottom:1px solid var(--line); }.control { width:100%; min-height:40px; border:1px solid #bfcbd5; border-radius:6px; background:#fff; color:var(--ink); padding:8px 10px; }.button { min-height:40px; border:1px solid var(--blue); border-radius:6px; padding:8px 12px; background:var(--blue); color:#fff; cursor:pointer; font-weight:700; }.button:hover,.button:focus-visible { background:#12568c; }.button-secondary { background:#fff; color:var(--blue); }.button-secondary:hover,.button-secondary:focus-visible { background:var(--blue-soft); }.button-muted { border-color:#aab7c2; background:#fff; color:#3e4e5b; }
    .preview-list { display:grid; gap:8px; padding:12px; max-height:720px; overflow:auto; }.preview-card { display:grid; grid-template-columns:minmax(0,1fr) auto; gap:8px 12px; border:1px solid var(--line); border-radius:6px; padding:12px; }.preview-card[hidden] { display:none; }.preview-card.selected { border-color:var(--blue); background:#f4f9fd; }.preview-card h3 { margin:2px 0 3px; color:var(--navy); font-size:15px; }.preview-card p { margin:0; color:var(--muted); font-size:12px; }.preview-card .button { grid-column:2; grid-row:1 / 3; align-self:center; }.eyebrow { color:var(--muted); font-size:11px; }.preview-meta { display:flex; flex-wrap:wrap; gap:6px; }.preview-meta span { border-radius:999px; padding:3px 7px; background:#eef3f6; color:#4e6172; font-size:11px; }.preview-meta .risk-high { background:var(--danger-soft); color:var(--danger); }.preview-meta .risk-medium { background:var(--amber-soft); color:var(--amber); }
    .workbench { padding:16px; }.selected-summary { min-height:72px; border-left:3px solid var(--blue); background:var(--blue-soft); color:#28455f; padding:10px 12px; }.impact-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px; margin-top:12px; }.impact-box { min-width:0; border:1px solid var(--line); border-radius:6px; padding:11px; }.impact-box h3 { margin:0 0 7px; color:var(--navy); font-size:13px; }.impact-box ul { margin:0; padding-left:18px; }.impact-box li { overflow-wrap:anywhere; }
    .confirm { margin-top:12px; border:1px solid #e8c9c5; background:#fff8f7; padding:12px; }.confirm[hidden] { display:none; }.confirm label { display:flex; align-items:flex-start; gap:8px; }.confirm input { margin-top:4px; }.actions { display:flex; flex-wrap:wrap; gap:8px; margin-top:12px; }.feedback { min-height:48px; margin-top:12px; border:1px solid var(--line); background:#fff; padding:10px 12px; color:#31465a; }.status-line { display:flex; justify-content:space-between; gap:12px; padding:11px 0; border-bottom:1px solid var(--line); }.status-line strong { color:var(--navy); }
    .flow { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); margin-top:16px; border:1px solid var(--line); background:#fff; }.flow div { padding:12px 14px; border-right:1px solid var(--line); }.flow div:last-child { border-right:0; }.flow span { display:block; color:var(--muted); font-size:12px; }.flow strong { color:var(--navy); } footer { margin-top:14px; color:var(--muted); font-size:12px; }
    @media(max-width:980px) { .layout { grid-template-columns:1fr; }.preview-list { max-height:none; }.impact-grid { grid-template-columns:1fr; }.metrics { grid-template-columns:repeat(2,minmax(0,1fr)); }.metric:nth-child(2) { border-right:0; }.metric:nth-child(-n+2) { border-bottom:1px solid var(--line); } }
    @media(max-width:640px) { .topbar { align-items:flex-start; flex-wrap:wrap; padding:10px 12px; }.brand { min-width:0; }.gate { margin-left:0; width:100%; text-align:left; } main { padding:16px 12px 30px; }.page-head { display:block; }.boundary { max-width:none; margin-top:12px; }.metrics,.filters,.flow { grid-template-columns:1fr; }.metric { border-right:0; border-bottom:1px solid var(--line); }.metric:last-child { border-bottom:0; }.preview-card { grid-template-columns:minmax(0,1fr) 76px; }.preview-card .button { padding:7px; }.workbench { padding:13px; } }
  </style>
</head>
<body>
  <header class="topbar"><div class="brand"><div class="brand-mark">KM</div><div><strong>KMFA</strong><span>经营分析系统</span></div></div><nav class="top-links" aria-label="返回当前页面">__LINKS__</nav><div class="gate"><span>当前可信状态</span><strong>Q4 / D · NO_GO</strong></div></header>
  <main>
    <section class="page-head"><div><h1>影响预览</h1><p>事件提交前展示潜在项目槽位、指标和报告影响。</p></div><div class="boundary"><strong>未通过影响预览不得发布。</strong> 高风险必须二次确认；即使预览通过，当前 D 级门禁仍阻止批准和发布。</div></section>
    <section class="metrics" aria-label="影响预览概况"><div class="metric"><span>预览定义</span><strong>6</strong></div><div class="metric"><span>高风险</span><strong>5</strong></div><div class="metric"><span>潜在项目槽位</span><strong>4</strong></div><div class="metric"><span>当前会话预览</span><strong id="session-preview-count">0</strong></div></section>
    <section class="layout">
      <div class="panel"><div class="panel-head"><h2>待预览事项</h2><span id="visible-count">6 项</span></div><div class="filters"><input class="control" type="search" data-preview-search aria-label="搜索影响预览" placeholder="搜索事项、指标或报告"><select class="control" data-risk-filter aria-label="按风险筛选"><option value="">全部风险</option><option value="high">高风险</option><option value="medium">中风险</option></select><button class="button button-muted" type="button" data-reset-filters>重置</button></div><div class="preview-list">__ROWS__</div></div>
      <div class="panel workbench"><div class="panel-head" style="padding:0 0 12px"><h2>会话影响预览</h2><span>不写业务状态</span></div><div class="selected-summary" id="selected-summary">请选择一个事项并生成影响预览。</div><div class="impact-grid"><section class="impact-box"><h3>受影响项目</h3><ul id="affected-projects"><li>待生成预览</li></ul></section><section class="impact-box"><h3>受影响指标</h3><ul id="affected-metrics"><li>待生成预览</li></ul></section><section class="impact-box"><h3>受影响报告</h3><ul id="affected-reports"><li>待生成预览</li></ul></section></div><section class="confirm" id="high-risk-confirm" hidden><h3 style="margin:0 0 8px">高风险二次确认</h3><label><input type="checkbox" data-high-risk-ack>我已阅读潜在项目、指标和报告影响；此确认只作用于当前会话。</label><button class="button" type="button" data-confirm-preview style="margin-top:10px">完成二次确认</button></section><div class="status-line"><span>预览状态</span><strong id="preview-status">尚未生成</strong></div><div class="status-line"><span>发布状态</span><strong id="publish-status">阻断</strong></div><div class="actions"><button class="button" type="button" data-check-publish>检查发布门禁</button><button class="button button-secondary" type="button" data-reset-session>清空会话预览</button></div><div class="feedback" id="impact-feedback" aria-live="polite">工作台已就绪；所有预览和确认仅保留在当前页面内存。</div></div>
    </section>
    <section class="flow" aria-label="阶段边界"><div><span>已完成</span><strong>S12-P1 · 候选事件</strong></div><div><span>已完成</span><strong>S12-P2 · 影响预览</strong></div><div><span>已完成</span><strong>S12-P3 · 派生重跑</strong></div></section>
    <footer>公开页面只含聚合计数和影响范围标签，不含原始文件身份、字段表头、业务金额、项目或客户明文。Stage 12 三个 phase 均已完成，当前仍为 Q4 / D · NO_GO。</footer>
  </main>
  <script>
    const previews=__PREVIEWS__;
    const state={selectedId:null,previewGenerated:false,confirmed:false,previewCount:0,confirmationCount:0};
    const rows=Array.from(document.querySelectorAll('[data-preview-row]'));
    const search=document.querySelector('[data-preview-search]');
    const riskFilter=document.querySelector('[data-risk-filter]');
    const selectedSummary=document.getElementById('selected-summary');
    const previewStatus=document.getElementById('preview-status');
    const publishStatus=document.getElementById('publish-status');
    const confirmPanel=document.getElementById('high-risk-confirm');
    const acknowledgement=document.querySelector('[data-high-risk-ack]');
    const feedback=document.getElementById('impact-feedback');
    function current(){return previews.find(item=>item.preview_id===state.selectedId)||null;}
    function record(action,message){document.body.dataset.lastAction=action;feedback.textContent=message;}
    function renderList(id,items){const list=document.getElementById(id);list.replaceChildren();items.forEach(item=>{const li=document.createElement('li');li.textContent=item;list.appendChild(li);});}
    function updateCounters(){document.getElementById('session-preview-count').textContent=String(state.previewCount);document.body.dataset.sessionPreviewCount=String(state.previewCount);document.body.dataset.secondConfirmationCount=String(state.confirmationCount);}
    function applyFilters(){const term=search.value.trim().toLowerCase();let visible=0;rows.forEach(row=>{const show=(!term||row.dataset.searchText.toLowerCase().includes(term))&&(!riskFilter.value||row.dataset.risk===riskFilter.value);row.hidden=!show;if(show)visible+=1;});document.getElementById('visible-count').textContent=`${visible} 项`;document.body.dataset.visibleRows=String(visible);record('filter',`筛选完成，当前显示 ${visible} 项。`);}
    function resetFilters(){search.value='';riskFilter.value='';applyFilters();record('reset-filters','筛选条件已重置。');}
    function generatePreview(id){const preview=previews.find(item=>item.preview_id===id);if(!preview)return;state.selectedId=id;state.previewGenerated=true;state.confirmed=preview.second_confirmation_required?false:true;state.previewCount+=1;rows.forEach(row=>row.classList.toggle('selected',row.dataset.previewId===id));selectedSummary.textContent=`${preview.source_group_title}｜${preview.impact_reason}`;renderList('affected-projects',preview.affected_project_scope);renderList('affected-metrics',preview.affected_metrics);renderList('affected-reports',preview.affected_reports);acknowledgement.checked=false;confirmPanel.hidden=!preview.second_confirmation_required;if(preview.second_confirmation_required){previewStatus.textContent='等待高风险二次确认';document.body.dataset.previewStatus='blocked_pending_second_confirmation';record('generate-high-preview','已生成高风险影响预览；二次确认前不得发布。');}else{previewStatus.textContent='会话预览通过';document.body.dataset.previewStatus='passed_session_preview';record('generate-medium-preview','影响预览已在当前会话通过；业务发布仍受 D 级门禁阻断。');}publishStatus.textContent='阻断';document.body.dataset.publishStatus='blocked';document.body.dataset.selectedPreview=id;updateCounters();}
    function confirmPreview(){const preview=current();if(!preview||!preview.second_confirmation_required){record('confirm-blocked','当前预览不需要高风险二次确认。');return;}if(!acknowledgement.checked){record('confirm-blocked','请先勾选已阅读影响范围。');return;}state.confirmed=true;state.confirmationCount+=1;previewStatus.textContent='高风险会话预览通过';document.body.dataset.previewStatus='passed_session_preview';updateCounters();record('second-confirmation','高风险影响范围已完成当前会话二次确认；未批准业务事件。');}
    function checkPublish(){const preview=current();if(!preview||!state.previewGenerated){publishStatus.textContent='阻断：缺少影响预览';document.body.dataset.publishStatus='blocked_missing_preview';record('publish-blocked','未通过影响预览不得发布。');return;}if(preview.second_confirmation_required&&!state.confirmed){publishStatus.textContent='阻断：等待二次确认';document.body.dataset.publishStatus='blocked_pending_second_confirmation';record('publish-blocked','高风险二次确认未完成，不得发布。');return;}publishStatus.textContent='阻断：Q4 / D · NO_GO';document.body.dataset.publishStatus='blocked_quality_gate';record('publish-blocked','预览已通过，但当前 Q4 / D · NO_GO 禁止批准和发布。');}
    function resetSession(){state.selectedId=null;state.previewGenerated=false;state.confirmed=false;state.previewCount=0;state.confirmationCount=0;rows.forEach(row=>row.classList.remove('selected'));selectedSummary.textContent='请选择一个事项并生成影响预览。';renderList('affected-projects',['待生成预览']);renderList('affected-metrics',['待生成预览']);renderList('affected-reports',['待生成预览']);confirmPanel.hidden=true;acknowledgement.checked=false;previewStatus.textContent='尚未生成';publishStatus.textContent='阻断';document.body.dataset.previewStatus='idle';document.body.dataset.publishStatus='blocked';document.body.dataset.selectedPreview='';updateCounters();record('reset-session','会话预览和二次确认已清空；未写入持久业务状态。');}
    search.addEventListener('input',applyFilters);riskFilter.addEventListener('change',applyFilters);document.querySelector('[data-reset-filters]').addEventListener('click',resetFilters);document.querySelectorAll('[data-generate-preview]').forEach(button=>button.addEventListener('click',()=>generatePreview(button.dataset.generatePreview)));document.querySelector('[data-confirm-preview]').addEventListener('click',confirmPreview);document.querySelector('[data-check-publish]').addEventListener('click',checkPublish);document.querySelector('[data-reset-session]').addEventListener('click',resetSession);resetSession();document.body.dataset.uiReady='true';record('ready','工作台已就绪；所有预览和确认仅保留在当前页面内存。');
  </script>
</body>
</html>'''
    return (
        template.replace("__LINKS__", links)
        .replace("__ROWS__", _render_rows(previews))
        .replace("__PREVIEWS__", json.dumps(previews, ensure_ascii=False, separators=(",", ":")))
    )


def _browser_worker() -> dict[str, Any]:
    from playwright.sync_api import sync_playwright

    PRIVATE_SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    stage_root = Path("KMFA/stage_artifacts").resolve()
    handler = functools.partial(s12_p1._QuietHandler, directory=str(stage_root))
    server = socketserver.TCPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    url = f"{base}/{PHASE_ID}/exports/html/{HTML_PATH.name}"
    buckets: dict[str, list[dict[str, Any]]] = {
        "viewport_checks": [],
        "search_checks": [],
        "risk_filter_checks": [],
        "medium_preview_checks": [],
        "high_preview_checks": [],
        "preconfirmation_block_checks": [],
        "second_confirmation_checks": [],
        "publish_block_checks": [],
        "reload_reset_checks": [],
        "return_link_http_checks": [],
        "actual_navigation_checks": [],
    }
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True,
                executable_path=s12_p1.s11_home._chromium_path(),
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
                    and s12_p1.s11_home._is_actionable_console_error(
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

                page.locator("[data-preview-search]").fill("零差异证据")
                buckets["search_checks"].append(
                    {"mode": mode, "passed": page.locator("[data-preview-row]:visible").count() == 1}
                )
                page.locator("[data-reset-filters]").click()
                page.locator("[data-risk-filter]").select_option("medium")
                buckets["risk_filter_checks"].append(
                    {"mode": mode, "passed": page.locator("[data-preview-row]:visible").count() == 1}
                )
                page.locator("[data-reset-filters]").click()

                page.locator('[data-generate-preview="IMPREV-S12P2-POST-002"]').click()
                medium_ok = page.locator("body").get_attribute("data-preview-status") == "passed_session_preview"
                buckets["medium_preview_checks"].append({"mode": mode, "passed": medium_ok})
                page.locator("[data-check-publish]").click()
                medium_publish_blocked = page.locator("body").get_attribute("data-publish-status") == "blocked_quality_gate"
                buckets["publish_block_checks"].append(
                    {"mode": mode, "flow": "medium", "passed": medium_publish_blocked}
                )

                page.locator('[data-generate-preview="IMPREV-S12P2-POST-005"]').click()
                high_ok = page.locator("body").get_attribute("data-preview-status") == "blocked_pending_second_confirmation"
                buckets["high_preview_checks"].append({"mode": mode, "passed": high_ok})
                page.locator("[data-check-publish]").click()
                preconfirm_blocked = page.locator("body").get_attribute("data-publish-status") == "blocked_pending_second_confirmation"
                buckets["preconfirmation_block_checks"].append({"mode": mode, "passed": preconfirm_blocked})
                page.locator("[data-high-risk-ack]").check()
                page.locator("[data-confirm-preview]").click()
                confirmed = (
                    page.locator("body").get_attribute("data-preview-status") == "passed_session_preview"
                    and page.locator("body").get_attribute("data-second-confirmation-count") == "1"
                )
                buckets["second_confirmation_checks"].append({"mode": mode, "passed": confirmed})
                page.locator("[data-check-publish]").click()
                high_publish_blocked = page.locator("body").get_attribute("data-publish-status") == "blocked_quality_gate"
                buckets["publish_block_checks"].append(
                    {"mode": mode, "flow": "high-confirmed", "passed": high_publish_blocked}
                )
                page.screenshot(
                    path=str(PRIVATE_SCREENSHOT_DIR / f"impact_preview_{mode}_high_confirmed.png"),
                    full_page=True,
                )

                page.locator("[data-reset-session]").click()
                reset_ok = (
                    page.locator("body").get_attribute("data-session-preview-count") == "0"
                    and page.locator("body").get_attribute("data-preview-status") == "idle"
                )
                page.reload(wait_until="networkidle")
                page.wait_for_function("document.body.dataset.uiReady === 'true'")
                reload_ok = page.locator("body").get_attribute("data-session-preview-count") == "0"
                buckets["reload_reset_checks"].append(
                    {"mode": mode, "passed": reset_ok and reload_ok}
                )
                page.screenshot(
                    path=str(PRIVATE_SCREENSHOT_DIR / f"impact_preview_{mode}.png"),
                    full_page=True,
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
        "schema_version": "kmfa.v014.s12_p2.impact_preview_browser.v1",
        "status": "PASS" if passed else "FAIL",
        **buckets,
    }


def _run_browser_review() -> dict[str, Any]:
    result = subprocess.run(
        [str(s12_p1.s11_home._audit_python()), str(Path(__file__).resolve()), "--browser-worker"],
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
        "medium_preview_check_count": len(browser["medium_preview_checks"]),
        "high_preview_check_count": len(browser["high_preview_checks"]),
        "preconfirmation_block_check_count": len(browser["preconfirmation_block_checks"]),
        "second_confirmation_check_count": len(browser["second_confirmation_checks"]),
        "publish_block_check_count": len(browser["publish_block_checks"]),
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
    return f"""# KMFA v0.1.4 S12-P2 修补后影响预览报告

- phase: `{PHASE_ID}`
- task: `{TASK_ID}`
- status: `{STATUS}`
- current gate: `Q4 / D / NO_GO`

## 结果

- current pending groups / templates / preview definitions: `{summary['source_pending_action_group_count']} / {summary['source_event_template_count']} / {summary['impact_preview_definition_count']}`
- high risk / second confirmation required: `{summary['high_risk_preview_count']} / {summary['second_confirmation_required_count']}`
- potential project slots: `{summary['potential_affected_project_slot_count']}`；仅表示潜在影响，不证明归属。
- current approved / published business events: `0 / 0`
- browser: baseline `{browser['baseline_pass_count']}/{browser['baseline_control_row_count']} PASS`；current `{browser['current_html_pass_count']}/{browser['current_html_control_row_count']} PASS`；desktop/mobile、二次确认和发布阻断均通过。

## 边界

- 影响预览和二次确认只存在浏览器会话，不写 raw、localStorage、数据库或持久业务状态。
- 预览通过不等于事件批准；当前 `Q4 / D / NO_GO` 始终阻止发布。
- S12-P3 重跑、Stage 12 review、GitHub upload、app reinstall、正式报告和 business execution 均未执行。
"""


def _render_test_results(final_validation: bool) -> str:
    state = "PASS" if final_validation else "PENDING_FINAL_VALIDATION"
    return f"""# S12-P2 测试结果

- focused tests: `{state}`
- strict validator: `{state}`
- desktop/mobile browser: `{state}`
- governance/no-float/no-omission/raw-private-secret scan: `{state}`
- raw phase/cross-phase exact: `PASS`
- S12-P3 / Stage 12 review / upload / reinstall: `NOT_PERFORMED`
"""


def _render_risk_register() -> str:
    return """# S12-P2 风险登记

| 风险 | 控制 |
|---|---|
| 潜在项目槽位被误读为已归属项目 | 所有预览固定 `potential_impact_not_attribution`，不公开项目名或金额 |
| 高风险预览绕过二次确认 | 浏览器状态机与 validator 同时阻断 |
| 预览通过被误读为业务批准 | 当前批准/发布始终为 0，Q4/D/NO_GO 继续阻断 |
| S12-P2 误执行重跑 | 页面无 rerun 控件，manifest 保持 S12-P3=false |
| raw/private 进入 Git | raw/browser 证据仅写 ignored private runtime，提交前执行安全扫描 |
"""


def _render_rollback() -> str:
    return """# S12-P2 回滚方案

1. 仅回退本 phase 的本地 commit。
2. 删除 ignored private S12-P2 运行证据。
3. 保留 S12-P1 commit 与历史 S12-P2 fixture，不改 raw inbox。
4. 复跑 S12-P1 strict validator，确认前序边界仍有效。
"""


def _private_report(summary: dict[str, Any], browser: dict[str, Any]) -> str:
    return f"""# S12-P2 私有验证记录

- raw files: {summary['raw_source_file_count']}
- phase raw exact: {str(summary['raw_snapshot_exact_match']).lower()}
- cross S12-P1 raw exact: {str(summary['raw_cross_phase_snapshot_exact_match']).lower()}
- browser status: {browser['status']}
- screenshots: desktop/mobile private ignored
- persistent raw difference: none
"""


def _governance_rows(generated_at: str, manifest: dict[str, Any]) -> None:
    evidence_ref = MANIFEST_PATH.as_posix()
    changed_files = [
        SUMMARY_PATH.as_posix(),
        MANIFEST_PATH.as_posix(),
        PREVIEWS_PATH.as_posix(),
        GO_NO_GO_PATH.as_posix(),
        HTML_PATH.as_posix(),
        REPORT_PATH.as_posix(),
        TEST_RESULTS_PATH.as_posix(),
        RISK_REGISTER_PATH.as_posix(),
        ROLLBACK_PATH.as_posix(),
        METADATA_SUMMARY_PATH.as_posix(),
        METADATA_MANIFEST_PATH.as_posix(),
        METADATA_PREVIEWS_PATH.as_posix(),
        METADATA_GO_NO_GO_PATH.as_posix(),
        Path(__file__).relative_to(Path.cwd()).as_posix(),
        "KMFA/tools/check_v014_s12_p2_post_remediation_impact_preview.py",
        "KMFA/tests/test_v014_s12_p2_post_remediation_impact_preview.py",
    ]
    s12_p1._upsert_jsonl(
        DEVELOPMENT_EVENTS_PATH,
        {
            "event_id": "DEV-KMFA-20260711-V014-S12-P2-POST-REMEDIATION-IMPACT-PREVIEW",
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
            "impact_preview_definition_count": manifest["summary"]["impact_preview_definition_count"],
            "current_business_event_publish_count": 0,
            "raw_business_data_committed": False,
            "github_upload_performed": False,
            "app_reinstall_performed": False,
            "business_execution_performed": False,
            "evidence_ref": evidence_ref,
            "files_changed": changed_files,
            "result_commit": "PENDING",
        },
    )
    s12_p1._upsert_jsonl(
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
    s12_p1._upsert_jsonl(
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
            "name": "v0.1.4 S12-P2 post-remediation impact preview",
            "phase_goal": "public-safe project metric report impact preview with high-risk second confirmation",
            "status": STATUS,
            "fact_level": "EXTRACTED",
            "derived_percent": 66.67,
            "estimated_task_units": 9,
            "completed_task_units": 6,
            "task_count": 3,
            "raw_data_committed": False,
            "evidence_ref": evidence_ref,
            "updated_at": generated_at[:10],
        },
    )


def generate(final_validation: bool = False) -> dict[str, Any]:
    generated_at = datetime.now().astimezone().replace(microsecond=0).isoformat()
    raw_before = s12_p1.s11_project._raw_snapshot("before_v014_s12_p2_post_remediation_impact_preview")
    _write_json(PRIVATE_RAW_BEFORE_PATH, raw_before)
    dependency = _load_s12_p1_dependency()
    contract = _load_contract()
    previews = _build_previews(dependency)
    _write_text(HTML_PATH, _render_html(previews))

    raw_after = s12_p1.s11_project._raw_snapshot("after_v014_s12_p2_post_remediation_impact_preview")
    _write_json(PRIVATE_RAW_AFTER_PATH, raw_after)
    previous_raw = json.loads(s12_p1.PRIVATE_RAW_AFTER_PATH.read_text(encoding="utf-8"))
    normalize_raw = s12_p1.s11_project._normalize_raw
    raw_exact = normalize_raw(raw_before) == normalize_raw(raw_after)
    raw_cross = normalize_raw(raw_before) == normalize_raw(previous_raw)
    if not raw_exact or not raw_cross:
        raise RuntimeError("raw snapshot drift detected during S12-P2")

    baseline_audit = s12_p1.s11_home._run_html_audit(V14_HTML_ROOT, PRIVATE_BASELINE_AUDIT_PATH)
    current_audit = s12_p1.s11_home._run_html_audit(HTML_DIR, PRIVATE_CURRENT_AUDIT_PATH)
    browser_payload = _run_browser_review()
    _write_json(PRIVATE_BROWSER_PATH, browser_payload)
    browser = _browser_summary(baseline_audit, current_audit, browser_payload)

    dependency_summary = dependency["summary"]
    unique_metrics = sorted({item for row in previews for item in row["affected_metrics"]})
    unique_reports = sorted({item for row in previews for item in row["affected_reports"]})
    summary = {
        "schema_version": "kmfa.v014.s12_p2.impact_preview_summary.v1",
        "record_type": "v014_s12_p2_post_remediation_impact_preview_summary",
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
        "source_pending_action_group_count": dependency_summary["pending_action_group_count"],
        "source_event_template_count": dependency_summary["manual_event_template_count"],
        "impact_preview_definition_count": len(previews),
        "high_risk_preview_count": sum(row["risk_level"] == "high" for row in previews),
        "medium_risk_preview_count": sum(row["risk_level"] == "medium" for row in previews),
        "second_confirmation_required_count": sum(row["second_confirmation_required"] for row in previews),
        "potential_affected_project_slot_count": dependency_summary["project_specific_unknown_allocation_count"],
        "unique_affected_metric_count": len(unique_metrics),
        "unique_affected_report_count": len(unique_reports),
        "current_session_preview_count_at_rest": 0,
        "current_session_second_confirmation_count_at_rest": 0,
        "current_approved_business_event_count": 0,
        "current_published_business_event_count": 0,
        "open_final_difference_accepted_count": dependency_summary["open_final_difference_accepted_count"],
        "nonzero_delta_reconciliation_count": dependency_summary["nonzero_delta_reconciliation_count"],
        "zero_delta_reconciliation_count": dependency_summary["zero_delta_reconciliation_count"],
        "incomplete_reconciliation_count": dependency_summary["incomplete_reconciliation_count"],
        "hard_block_count": dependency_summary["hard_block_count"],
        "raw_source_file_count": raw_before["file_count"],
        "raw_snapshot_exact_match": raw_exact,
        "raw_cross_phase_snapshot_exact_match": raw_cross,
        "formal_report_count": 0,
        "business_decision_basis_count": 0,
        "s12_p1_performed": True,
        "s12_p2_performed": True,
        "s12_p3_performed": False,
        "stage12_review_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }
    go_no_go = {
        "schema_version": "kmfa.v014.s12_p2.impact_preview_go_no_go.v1",
        "phase_id": PHASE_ID,
        "decision": DECISION,
        "s12_p2_validated": True,
        "impact_preview_generation_allowed": True,
        "high_risk_second_confirmation_required": True,
        "current_business_event_approval_allowed": False,
        "current_business_event_publish_allowed": False,
        "derived_rerun_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "s12_p3_performed": False,
        "stage12_review_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }
    manifest = {
        "schema_version": "kmfa.v014.s12_p2.impact_preview_manifest.v1",
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
        "s12_p1_post_remediation_dependency_validated": True,
        "legacy_s12_p2_policy_fixture_validated": True,
        "taskpack_contract": contract,
        "impact_preview_definitions": previews,
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
        "next_phase": "S12-P3",
        "next_required_step": "Execute S12-P3 derived rerun as a separate run after S12-P2 local validation and commit.",
        "git": {
            "branch": _git_output(["branch", "--show-current"]),
            "remote": _git_output(["remote", "get-url", "origin"]),
            "head": _git_output(["rev-parse", "HEAD"]),
        },
    }
    previews_payload = {
        "schema_version": "kmfa.v014.s12_p2.impact_preview_definitions.v1",
        "phase_id": PHASE_ID,
        "preview_count": len(previews),
        "project_scope_semantics": "potential impact only; no project attribution is asserted",
        "previews": previews,
    }
    for path, value in (
        (SUMMARY_PATH, summary),
        (MANIFEST_PATH, manifest),
        (PREVIEWS_PATH, previews_payload),
        (GO_NO_GO_PATH, go_no_go),
        (METADATA_SUMMARY_PATH, summary),
        (METADATA_MANIFEST_PATH, manifest),
        (METADATA_PREVIEWS_PATH, previews_payload),
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
        "S12-P2 post-remediation impact preview: "
        f"definitions={summary['impact_preview_definition_count']} "
        f"high_risk={summary['high_risk_preview_count']} "
        f"published={summary['current_published_business_event_count']} "
        f"grade={summary['current_report_grade']} decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
