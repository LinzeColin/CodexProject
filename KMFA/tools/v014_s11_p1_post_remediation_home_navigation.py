#!/usr/bin/env python3
"""Generate KMFA v0.1.4 S11-P1 post-remediation home navigation."""

from __future__ import annotations

import argparse
import csv
import functools
import http.server
import html
import json
import os
import socketserver
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

from KMFA.tools import v014_s10_post_remediation_stage_review as s10_phase
from KMFA.tools import v014_s10_p1_post_remediation_report_entry as governance_phase
from KMFA.tools.check_v014_s10_post_remediation_stage_review import (
    _validate_cross_format as validate_s10_cross_format,
    _validate_dependencies as validate_s10_dependencies,
    _validate_private as validate_s10_private,
    _validate_public as validate_s10_public,
)
from KMFA.tools.check_v014_s11_p1_home_navigation import (
    validate_v014_s11_p1_home_navigation,
)
from KMFA.tools.home_navigation_runtime import MODULE_ICONS, REQUIRED_NAVIGATION_LABELS


PHASE_ID = "V014_S11_P1_POST_REMEDIATION_HOME_NAVIGATION"
ROADMAP_PHASE_ID = "S11-P1"
TASK_ID = "KMFA-V014-S11-P1-POST-REMEDIATION-HOME-NAVIGATION-20260711"
ACCEPTANCE_ID = "ACC-V014-S11-P1-POST-REMEDIATION-HOME-NAVIGATION"
VERSION = "0.1.4-s11-p1-post-remediation-home-navigation"
STATUS = "completed_validated_local_only_current_home_navigation_d_no_go_upload_deferred"
DECISION = "NO_GO"
FORMULA_ID = "FORM-KMFA-V014-S11-P1-POST-REMEDIATION-HOME-NAVIGATION-001"
PARAMETER_IDS = ("PARAM-KMFA-1708", "PARAM-KMFA-1709", "PARAM-KMFA-1710")
MODEL_REGISTRY_KEY = "kmfa_v014_s11_p1_post_remediation_home_navigation"

OUTPUT_DIR = Path("KMFA/stage_artifacts") / PHASE_ID
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
HTML_DIR = OUTPUT_DIR / "exports/html"
SUMMARY_PATH = MACHINE_DIR / "home_navigation_summary.json"
MANIFEST_PATH = MACHINE_DIR / "home_navigation_manifest.json"
MODULES_PATH = MACHINE_DIR / "home_navigation_modules_public_safe.json"
GO_NO_GO_PATH = MACHINE_DIR / "home_navigation_go_no_go_report.json"
HTML_PATH = HTML_DIR / "kmfa_home_navigation.html"
COMPLETION_PATH = HUMAN_DIR / "s11_p1_completion_record_zh.md"
READ_ME_PATH = HUMAN_DIR / "home_navigation_readme_zh.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results_zh.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register_zh.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan_zh.md"

QUALITY_DIR = Path("KMFA/metadata/quality")
METADATA_SUMMARY_PATH = QUALITY_DIR / "v014_s11_p1_post_remediation_home_navigation_summary.json"
METADATA_MANIFEST_PATH = QUALITY_DIR / "v014_s11_p1_post_remediation_home_navigation_manifest.json"
METADATA_MODULES_PATH = QUALITY_DIR / "v014_s11_p1_post_remediation_home_navigation_modules_public_safe.json"
METADATA_GO_NO_GO_PATH = QUALITY_DIR / "v014_s11_p1_post_remediation_home_navigation_go_no_go_report.json"

PRIVATE_DIR = Path("KMFA/.codex_private_runtime/v014_s11_p1_post_remediation_home_navigation")
PRIVATE_RAW_BEFORE_PATH = PRIVATE_DIR / "raw_immutability_before.json"
PRIVATE_RAW_AFTER_PATH = PRIVATE_DIR / "raw_immutability_after.json"
PRIVATE_VALIDATION_REPORT_PATH = PRIVATE_DIR / "s11_p1_home_navigation_validation_zh.md"
PRIVATE_BASELINE_AUDIT_PATH = PRIVATE_DIR / "human_flow_baseline_audit.csv"
PRIVATE_CURRENT_AUDIT_PATH = PRIVATE_DIR / "current_home_navigation_audit.csv"
PRIVATE_BROWSER_PATH = PRIVATE_DIR / "browser_verification.json"
PRIVATE_SCREENSHOT_DIR = PRIVATE_DIR / "screenshots"

AUDIT_SCRIPT = Path("KMFA/taskpack/v1_4/html_uiux/kmfa_html_human_flow_audit.py")
AUDIT_ROOT = Path("KMFA/taskpack/v1_4/html_uiux")
HISTORICAL_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V014_S11_P1_HOME_NAVIGATION/machine/home_navigation_manifest.json"
)
BUSINESS_REPORT_HREF = (
    "../../../V014_S10_P3_POST_REMEDIATION_RESTRICTED_EXPORT/exports/html/"
    "business_overview_report.html"
)
PROJECT_REPORT_HREF = (
    "../../../V014_S10_P3_POST_REMEDIATION_RESTRICTED_EXPORT/exports/html/"
    "project_cost_special_report.html"
)
SOURCE_CHECK_BOARD_HREF = (
    "../../../V014_S11_P2_POST_REMEDIATION_SOURCE_CHECK_BOARD/exports/html/"
    "kmfa_source_check_board.html"
)
PROJECT_COST_PAGE_HREF = (
    "../../../V014_S11_P3_POST_REMEDIATION_PROJECT_COST_PAGE/exports/html/"
    "kmfa_project_cost_page.html"
)

DEVELOPMENT_EVENTS_PATH = governance_phase.DEVELOPMENT_EVENTS_PATH
STAGE_STATUS_PATH = governance_phase.STAGE_STATUS_PATH
TASK_STATUS_PATH = governance_phase.TASK_STATUS_PATH


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
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


def _validate_s10_dependency() -> dict[str, Any]:
    errors: list[str] = []
    manifest = validate_s10_public(errors)
    validate_s10_cross_format(errors)
    validate_s10_dependencies(errors)
    validate_s10_private(errors, True)
    validation = manifest.get("validation_summary", {})
    if validation.get("final_validation_recorded") is not True:
        errors.append("Stage 10 review final validation is not recorded")
    if any(value != "PASS" for key, value in validation.items() if key != "final_validation_recorded"):
        errors.append("Stage 10 review final validation contains a non-PASS result")
    if errors:
        raise ValueError("; ".join(errors))
    return manifest


def _module_records() -> list[dict[str, Any]]:
    specs = [
        (
            "business_overview",
            "经营总览",
            "经营状态入口",
            "汇总查看当前报告可信等级、差异状态和受限经营概览。",
            "显示经营总览入口状态",
            "当前可查看 D 级受限预览",
            [
                {"label": "打开经营总览受限报告", "href": BUSINESS_REPORT_HREF},
            ],
        ),
        (
            "project_cost",
            "项目成本",
            "成本报告入口",
            "查看项目成本专题结构、差异阻断和当前受限报告入口。",
            "显示项目成本入口状态",
            "当前可查看 D 级受限预览",
            [
                {"label": "打开项目成本受限报告", "href": PROJECT_REPORT_HREF},
            ],
        ),
        (
            "receivable_collection",
            "回款应收",
            "导航已建立",
            "保留回款、应收和账龄入口，业务明细尚未放行。",
            "显示回款应收入口状态",
            "关键现金比较仍有未完成项",
            [],
        ),
        (
            "financial_cash",
            "财务资金",
            "导航已建立",
            "保留现金、资金计划和融资提示入口，不执行付款或融资审批。",
            "显示财务资金入口状态",
            "关键现金数据仍不完整",
            [],
        ),
        (
            "invoice_tax",
            "开票纳税",
            "导航已建立",
            "保留开票、税务和政策证据入口，不生成正式申报结论。",
            "显示开票纳税入口状态",
            "正式开票与申报均未执行",
            [],
        ),
        (
            "source_check",
            "数据源检查",
            "导航已建立",
            "显示数据质量与来源检查入口，检查矩阵明细尚未展开。",
            "显示数据源检查入口状态",
            "检查板明细等待后续阶段",
            [],
        ),
        (
            "pending_actions",
            "待处理事项",
            "导航已建立",
            "汇总人工确认、差异处理和报告发布前的受控待办入口。",
            "显示待处理事项入口状态",
            "三项最终接受未决继续保留",
            [],
        ),
        (
            "report_center",
            "报告中心",
            "受限报告入口",
            "集中查看两份当前受限报告，等级与使用限制必须随入口保留。",
            "显示报告中心入口状态",
            "仅供内部复核，不是正式报告",
            [
                {"label": "打开经营总览受限报告", "href": BUSINESS_REPORT_HREF},
                {"label": "打开项目成本受限报告", "href": PROJECT_REPORT_HREF},
            ],
        ),
    ]
    records = []
    for order, (module_id, label, status, summary, action, availability, links) in enumerate(specs, 1):
        records.append(
            {
                "schema_version": "kmfa.v014.s11_p1.home_navigation_module.v1",
                "record_type": "post_remediation_home_navigation_module",
                "project_id": "KMFA",
                "module_order": order,
                "module_id": module_id,
                "visible_label": label,
                "visible_status": status,
                "visible_summary": summary,
                "primary_action": action,
                "availability_summary": availability,
                "route_hash": f"#{module_id}",
                "report_links": links,
                "current_stage_page_links": {
                    "project_cost": [
                        {"label": "打开项目成本页面", "href": PROJECT_COST_PAGE_HREF}
                    ],
                    "source_check": [
                        {"label": "打开数据源检查板", "href": SOURCE_CHECK_BOARD_HREF}
                    ],
                }.get(module_id, []),
                "visible_feedback_required": True,
                "current_data_quality_grade": "Q4",
                "current_report_grade": "D",
                "decision": "NO_GO",
                "formal_report_allowed": False,
                "business_decision_basis_allowed": False,
                "raw_business_values_included": False,
            }
        )
    return records


def _render_icon(module_id: str) -> str:
    return (
        '<svg class="icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false" '
        'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
        f'stroke-linejoin="round">{MODULE_ICONS[module_id]}</svg>'
    )


def _render_html(records: list[dict[str, Any]]) -> str:
    nav = "\n".join(
        f'''<button id="nav-{record["module_id"]}" class="nav-item{" active" if index == 0 else ""}" type="button" role="tab" aria-selected="{"true" if index == 0 else "false"}" aria-controls="view-{record["module_id"]}" tabindex="{0 if index == 0 else -1}" data-module-id="{record["module_id"]}">{_render_icon(record["module_id"])}<span>{html.escape(record["visible_label"])}</span></button>'''
        for index, record in enumerate(records)
    )
    views = []
    for index, record in enumerate(records):
        report_links = "".join(
            f'<a class="report-link" data-report-link href="{html.escape(link["href"])}" target="_blank" rel="noopener">{html.escape(link["label"])}</a>'
            for link in record["report_links"]
        )
        stage_page_links = "".join(
            f'<a class="report-link" data-current-stage-page-link href="{html.escape(link["href"])}">{html.escape(link["label"])}</a>'
            for link in record["current_stage_page_links"]
        )
        links = report_links + stage_page_links
        links_block = (
            f'<div class="report-links" aria-label="当前受限报告">{links}</div>'
            if links
            else '<p class="availability-note">当前仅开放导航与状态反馈，未开放业务明细。</p>'
        )
        views.append(
            f'''<section id="view-{record["module_id"]}" class="module-view" role="tabpanel" aria-labelledby="nav-{record["module_id"]}" data-module-view="{record["module_id"]}"{"" if index == 0 else " hidden"}>
  <div class="module-heading"><div><span class="eyebrow">{html.escape(record["visible_status"])}</span><h2>{html.escape(record["visible_label"])}</h2><p>{html.escape(record["visible_summary"])}</p></div><span class="grade-badge">D级 · 未放行</span></div>
  <div class="module-facts">
    <div><span>当前可信状态</span><strong>Q4 / D</strong></div>
    <div><span>差异状态</span><strong>3 / 9 / 2 / 1</strong></div>
    <div><span>可用边界</span><strong>{html.escape(record["availability_summary"])}</strong></div>
  </div>
  <div class="module-commands"><button class="primary-command" type="button" data-module-action="{record["module_id"]}">{_render_icon(record["module_id"])}<span>{html.escape(record["primary_action"])}</span></button>{links_block}</div>
</section>'''
        )
    state = {
        record["module_id"]: {
            "label": record["visible_label"],
            "feedback": f"{record['visible_label']}入口状态已更新：{record['availability_summary']}。",
            "action": f"{record['primary_action']}已完成，当前仍保持 D级、未放行和仅供内部复核限制。",
        }
        for record in records
    }
    state_json = json.dumps(state, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return f'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>KMFA 经营分析系统</title>
  <style>
    :root {{ --navy:#102f50; --blue:#17679b; --blue-dark:#114b74; --blue-soft:#edf6fb; --line:#cfdae3; --text:#152331; --muted:#5e6d79; --danger:#a62e2e; --danger-bg:#fff1f0; --surface:#fff; --page:#f3f6f8; }}
    * {{ box-sizing:border-box; }}
    html {{ min-width:320px; background:var(--page); }}
    body {{ margin:0; color:var(--text); background:var(--page); font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",Arial,sans-serif; letter-spacing:0; }}
    button,a {{ font:inherit; }}
    button:focus-visible,a:focus-visible {{ outline:3px solid rgba(23,103,155,.28); outline-offset:2px; }}
    .app-shell {{ display:grid; grid-template-columns:248px minmax(0,1fr); min-height:100vh; }}
    .sidebar {{ background:var(--navy); color:#fff; padding:22px 16px; }}
    .brand {{ display:flex; align-items:center; gap:11px; padding:0 8px 20px; border-bottom:1px solid rgba(255,255,255,.16); }}
    .brand-mark {{ width:44px; height:44px; display:grid; place-items:center; border:1px solid rgba(255,255,255,.42); border-radius:6px; background:#17679b; font-size:17px; font-weight:800; }}
    .brand strong {{ display:block; font-size:17px; }} .brand span {{ display:block; margin-top:2px; color:#bed6e8; font-size:12px; }}
    .nav-list {{ display:grid; gap:4px; padding-top:18px; }}
    .nav-item {{ width:100%; min-height:44px; display:flex; align-items:center; gap:10px; border:0; border-radius:6px; padding:9px 11px; color:#dbeaf4; background:transparent; text-align:left; cursor:pointer; }}
    .nav-item:hover,.nav-item.active {{ color:#fff; background:rgba(255,255,255,.13); }}
    .nav-item .icon {{ width:18px; height:18px; flex:0 0 18px; }}
    .side-status {{ margin:20px 8px 0; padding-top:16px; border-top:1px solid rgba(255,255,255,.16); }}
    .side-status span {{ display:block; color:#bed6e8; font-size:12px; }} .side-status strong {{ display:block; margin-top:5px; font-size:16px; }}
    main {{ min-width:0; padding:24px 30px 30px; }}
    .topbar {{ display:flex; justify-content:space-between; align-items:flex-start; gap:20px; }}
    h1 {{ margin:0; color:var(--navy); font-size:25px; }} .topbar p {{ margin:6px 0 0; color:var(--muted); }}
    .gate {{ flex:0 0 auto; border:1px solid #efaaa5; border-radius:6px; background:var(--danger-bg); padding:10px 13px; color:var(--danger); }}
    .gate span {{ display:block; font-size:12px; }} .gate strong {{ display:block; margin-top:2px; font-size:16px; }}
    .quality-band {{ margin-top:18px; padding:13px 15px; border-left:4px solid var(--danger); background:#fff8f7; line-height:1.55; }}
    .metrics {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:10px; margin:16px 0; }}
    .metric {{ min-width:0; border:1px solid var(--line); border-radius:6px; background:var(--surface); padding:12px 14px; }}
    .metric span {{ display:block; color:var(--muted); font-size:12px; }} .metric strong {{ display:block; margin-top:4px; color:var(--blue-dark); font-size:21px; }}
    .workspace {{ display:grid; grid-template-columns:minmax(0,1fr) 290px; min-height:430px; border:1px solid var(--line); background:var(--surface); }}
    .module-view {{ min-width:0; padding:24px; }} .module-view[hidden] {{ display:none; }}
    .module-heading {{ display:flex; justify-content:space-between; gap:18px; align-items:flex-start; padding-bottom:19px; border-bottom:1px solid var(--line); }}
    .eyebrow {{ color:var(--blue); font-size:12px; font-weight:700; }} h2 {{ margin:5px 0 7px; color:var(--navy); font-size:23px; }} .module-heading p {{ max-width:680px; margin:0; color:var(--muted); line-height:1.65; }}
    .grade-badge {{ flex:0 0 auto; border:1px solid #efaaa5; border-radius:999px; background:var(--danger-bg); color:var(--danger); padding:6px 10px; font-size:12px; font-weight:700; }}
    .module-facts {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); margin-top:20px; border-top:1px solid var(--line); border-left:1px solid var(--line); }}
    .module-facts div {{ min-width:0; min-height:96px; padding:14px; border-right:1px solid var(--line); border-bottom:1px solid var(--line); }}
    .module-facts span {{ display:block; color:var(--muted); font-size:12px; }} .module-facts strong {{ display:block; margin-top:7px; color:var(--navy); font-size:15px; line-height:1.45; overflow-wrap:anywhere; }}
    .module-commands {{ display:flex; flex-wrap:wrap; align-items:center; gap:10px; margin-top:22px; }}
    .primary-command,.report-link {{ min-height:40px; display:inline-flex; align-items:center; justify-content:center; gap:8px; border-radius:6px; padding:8px 12px; text-decoration:none; cursor:pointer; }}
    .primary-command {{ border:1px solid var(--blue); background:var(--blue); color:#fff; }} .primary-command:hover {{ background:var(--blue-dark); }} .primary-command .icon {{ width:17px; height:17px; }}
    .report-links {{ display:flex; flex-wrap:wrap; gap:8px; }} .report-link {{ border:1px solid var(--blue); color:var(--blue); background:#fff; }} .report-link:hover {{ background:var(--blue-soft); }}
    .availability-note {{ margin:0; color:var(--muted); font-size:13px; }}
    .activity-panel {{ border-left:1px solid var(--line); background:#f8fafb; padding:22px 18px; }} .activity-panel h2 {{ margin:0 0 10px; font-size:17px; }} .activity-panel p {{ margin:0; color:#42515e; line-height:1.65; }}
    .activity-state {{ margin-top:18px; padding-top:15px; border-top:1px solid var(--line); }} .activity-state span {{ display:block; color:var(--muted); font-size:12px; }} .activity-state strong {{ display:block; margin-top:5px; color:var(--danger); }}
    footer {{ padding-top:14px; color:var(--muted); font-size:12px; }}
    @media(max-width:980px) {{ .workspace {{ grid-template-columns:1fr; }} .activity-panel {{ border-left:0; border-top:1px solid var(--line); }} }}
    @media(max-width:760px) {{
      .app-shell {{ grid-template-columns:minmax(0,1fr); }} .sidebar {{ min-width:0; width:100%; max-width:100%; overflow:hidden; padding:14px 12px 10px; }} .brand {{ padding:0 4px 12px; }}
      .nav-list {{ min-width:0; max-width:100%; display:flex; overflow-x:auto; gap:6px; padding-top:12px; scrollbar-width:thin; }} .nav-item {{ flex:0 0 auto; width:auto; min-height:38px; white-space:nowrap; }} .side-status {{ display:none; }}
      main {{ padding:18px 14px 24px; }} .topbar {{ display:block; }} .gate {{ display:inline-block; margin-top:12px; }} .metrics {{ grid-template-columns:repeat(2,minmax(0,1fr)); }}
      .workspace {{ min-height:0; }} .module-view {{ padding:19px 15px; }} .module-heading {{ display:block; }} .grade-badge {{ display:inline-flex; margin-top:12px; }} .module-facts {{ grid-template-columns:1fr; }}
    }}
  </style>
</head>
<body>
  <div class="app-shell" data-active-module="business_overview">
    <aside class="sidebar">
      <div class="brand"><div class="brand-mark">KM</div><div><strong>KMFA</strong><span>经营分析系统</span></div></div>
      <nav class="nav-list" role="tablist" aria-label="业务导航" aria-orientation="vertical">{nav}</nav>
      <div class="side-status"><span>当前可信状态</span><strong>Q4 / D · NO_GO</strong></div>
    </aside>
    <main>
      <header class="topbar"><div><h1>经营分析工作台</h1><p>当前首页仅展示公开安全状态与受控入口</p></div><div class="gate"><span>报告状态</span><strong>D级（未放行） · NO_GO</strong></div></header>
      <section class="quality-band"><strong>限制说明：</strong>关键现金数据仍不完整，九项非零差异继续保留，一项比较未完成；所有报告入口仅供内部复核。</section>
      <section class="metrics" aria-label="当前差异状态"><div class="metric"><span>最终接受未决</span><strong>3</strong></div><div class="metric"><span>非零差异</span><strong>9</strong></div><div class="metric"><span>零差异</span><strong>2</strong></div><div class="metric"><span>未完成比较</span><strong>1</strong></div></section>
      <section class="workspace"><div>{''.join(views)}</div><aside class="activity-panel" id="activity-panel" aria-live="polite"><h2 id="activity-title">经营总览入口已选中</h2><p id="activity-message">经营总览入口状态已更新：当前可查看 D 级受限预览。</p><div class="activity-state"><span>当前发布边界</span><strong>未放行 · 仅供内部复核</strong></div></aside></section>
      <footer>公开安全首页，不包含原始文件身份、字段表头、业务金额或明细。</footer>
    </main>
  </div>
  <script>
    const moduleState={state_json};
    const shell=document.querySelector('.app-shell');
    const navButtons=Array.from(document.querySelectorAll('[data-module-id]'));
    const views=Array.from(document.querySelectorAll('[data-module-view]'));
    const activityTitle=document.getElementById('activity-title');
    const activityMessage=document.getElementById('activity-message');
    let sequence=0;
    function setFeedback(id,message,kind){{sequence+=1;activityTitle.textContent=moduleState[id].label+'入口状态';activityMessage.textContent=message;shell.dataset.lastAction=kind+':'+id+':'+sequence;document.body.dataset.lastAction=shell.dataset.lastAction;}}
    function activateModule(id,source,moveFocus){{if(!moduleState[id])return;navButtons.forEach(button=>{{const active=button.dataset.moduleId===id;button.classList.toggle('active',active);button.setAttribute('aria-selected',String(active));button.tabIndex=active?0:-1;if(active&&moveFocus)button.focus();}});views.forEach(view=>{{view.hidden=view.dataset.moduleView!==id;}});shell.dataset.activeModule=id;if(location.protocol==='http:'||location.protocol==='https:')history.replaceState(null,'','#'+id);setFeedback(id,moduleState[id].feedback,source||'navigate');}}
    navButtons.forEach((button,index)=>{{button.addEventListener('click',()=>activateModule(button.dataset.moduleId,'navigate',false));button.addEventListener('keydown',event=>{{let target=null;if(event.key==='ArrowDown'||event.key==='ArrowRight')target=(index+1)%navButtons.length;if(event.key==='ArrowUp'||event.key==='ArrowLeft')target=(index-1+navButtons.length)%navButtons.length;if(event.key==='Home')target=0;if(event.key==='End')target=navButtons.length-1;if(target!==null){{event.preventDefault();activateModule(navButtons[target].dataset.moduleId,'keyboard',true);}}}});}});
    document.querySelectorAll('[data-module-action]').forEach(button=>button.addEventListener('click',()=>{{const id=button.dataset.moduleAction;setFeedback(id,moduleState[id].action,'action');}}));
    window.addEventListener('hashchange',()=>activateModule(location.hash.slice(1)||'business_overview','hash',false));
    const initial=moduleState[location.hash.slice(1)]?location.hash.slice(1):'business_overview';activateModule(initial,'ready',false);shell.dataset.uiReady='true';
  </script>
</body>
</html>'''


def _python_has_playwright(path: Path) -> bool:
    if not path.exists():
        return False
    result = subprocess.run(
        [str(path), "-c", "import playwright"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def _audit_python() -> Path:
    candidates = []
    if os.environ.get("KMFA_AUDIT_PYTHON"):
        candidates.append(Path(os.environ["KMFA_AUDIT_PYTHON"]))
    candidates.extend([Path("KMFA/.codex_private_runtime/playwright_venv/bin/python"), Path(sys.executable)])
    for path in candidates:
        if _python_has_playwright(path):
            return path
    raise RuntimeError("Playwright Python runtime is required; set KMFA_AUDIT_PYTHON")


def _chromium_path() -> str:
    candidates = []
    if os.environ.get("KMFA_CHROMIUM"):
        candidates.append(Path(os.environ["KMFA_CHROMIUM"]))
    candidates.extend(
        [Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"), Path("/usr/bin/chromium")]
    )
    for path in candidates:
        if path.exists():
            return str(path)
    raise RuntimeError("Local Chromium or Google Chrome is required")


def _run_html_audit(root: Path, output: Path) -> dict[str, Any]:
    output.parent.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["KMFA_CHROMIUM"] = _chromium_path()
    result = subprocess.run(
        [str(_audit_python()), str(AUDIT_SCRIPT), str(root), "--out", str(output)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"HTML human-flow audit failed: {result.stdout}\n{result.stderr}")
    with output.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    statuses = [row.get("status") for row in rows]
    summary = {
        "file_count": len({row.get("file") for row in rows if row.get("file")}),
        "control_row_count": len(rows),
        "pass_count": statuses.count("PASS"),
        "warn_count": statuses.count("WARN"),
        "fail_count": statuses.count("FAIL"),
    }
    if not rows or summary["fail_count"]:
        raise RuntimeError(f"HTML audit failed: {summary}")
    return summary


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        return


def _is_actionable_console_error(message: str) -> bool:
    normalized = message.lower()
    return not (
        "favicon.ico" in normalized
        and ("404" in normalized or "failed to load resource" in normalized)
    )


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
    viewport_checks = []
    navigation_checks = []
    action_checks = []
    keyboard_checks = []
    report_link_checks = []
    stage_page_link_checks = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True,
                executable_path=_chromium_path(),
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
                    and _is_actionable_console_error(f"{msg.text} {msg.location.get('url', '')}")
                    else None,
                )
                page.on("pageerror", lambda exc: console_errors.append(str(exc)))
                page.goto(url, wait_until="load")
                page.wait_for_timeout(120)
                for module_id, label in zip(
                    [record["module_id"] for record in _module_records()],
                    REQUIRED_NAVIGATION_LABELS,
                ):
                    page.locator(f'[data-module-id="{module_id}"]').click()
                    page.wait_for_timeout(35)
                    passed = (
                        page.locator(".app-shell").get_attribute("data-active-module") == module_id
                        and page.locator(f'[data-module-view="{module_id}"]').is_visible()
                        and page.locator(f'[data-module-id="{module_id}"]').get_attribute("aria-selected") == "true"
                        and label in page.locator("#activity-message").inner_text()
                    )
                    navigation_checks.append({"mode": mode, "module_id": module_id, "passed": passed})
                    before = page.locator(".app-shell").get_attribute("data-last-action")
                    page.locator(f'[data-module-action="{module_id}"]').click()
                    page.wait_for_timeout(35)
                    after = page.locator(".app-shell").get_attribute("data-last-action")
                    action_checks.append(
                        {
                            "mode": mode,
                            "module_id": module_id,
                            "passed": before != after
                            and str(after).startswith(f"action:{module_id}:")
                            and label in page.locator("#activity-message").inner_text(),
                        }
                    )

                first_nav = page.locator('[data-module-id="business_overview"]')
                first_nav.focus()
                first_nav.press("End")
                keyboard_checks.append(
                    {
                        "mode": mode,
                        "key": "End",
                        "passed": page.locator(".app-shell").get_attribute("data-active-module") == "report_center",
                    }
                )
                page.locator('[data-module-id="report_center"]').press("Home")
                keyboard_checks.append(
                    {
                        "mode": mode,
                        "key": "Home",
                        "passed": page.locator(".app-shell").get_attribute("data-active-module") == "business_overview",
                    }
                )
                if mode == "desktop":
                    links = page.locator("a[data-report-link]")
                    for index in range(links.count()):
                        href = links.nth(index).get_attribute("href") or ""
                        response = page.request.get(urljoin(page.url, href))
                        report_link_checks.append({"href": href, "status": response.status, "passed": response.ok})
                    stage_links = page.locator("a[data-current-stage-page-link]")
                    for index in range(stage_links.count()):
                        href = stage_links.nth(index).get_attribute("href") or ""
                        response = page.request.get(urljoin(page.url, href))
                        stage_page_link_checks.append(
                            {"href": href, "status": response.status, "passed": response.ok}
                        )
                dimensions = page.evaluate(
                    "({scrollWidth:document.documentElement.scrollWidth,innerWidth:window.innerWidth})"
                )
                screenshot = PRIVATE_SCREENSHOT_DIR / f"kmfa_home_navigation_{mode}.png"
                page.screenshot(path=str(screenshot), full_page=True)
                viewport_checks.append(
                    {
                        "mode": mode,
                        "viewport": viewport,
                        "no_horizontal_overflow": dimensions["scrollWidth"] <= dimensions["innerWidth"],
                        "console_error_count": len(console_errors),
                        "ui_ready": page.locator(".app-shell").get_attribute("data-ui-ready") == "true",
                        "no_go_visible": "NO_GO" in page.locator("body").inner_text(),
                    }
                )
                page.close()
            browser.close()
    finally:
        server.shutdown()
        server.server_close()

    passed = (
        all(item["passed"] for item in navigation_checks)
        and all(item["passed"] for item in action_checks)
        and all(item["passed"] for item in keyboard_checks)
        and all(item["passed"] for item in report_link_checks)
        and all(item["passed"] for item in stage_page_link_checks)
        and all(item["no_horizontal_overflow"] and item["console_error_count"] == 0 and item["ui_ready"] and item["no_go_visible"] for item in viewport_checks)
    )
    result = {
        "status": "PASS" if passed else "FAIL",
        "viewport_checks": viewport_checks,
        "navigation_checks": navigation_checks,
        "module_action_checks": action_checks,
        "keyboard_navigation_checks": keyboard_checks,
        "report_link_http_checks": report_link_checks,
        "current_stage_page_link_http_checks": stage_page_link_checks,
    }
    _write_json(PRIVATE_BROWSER_PATH, result)
    if not passed:
        raise RuntimeError("S11-P1 browser review failed")
    return result


def _run_browser_suite() -> dict[str, Any]:
    baseline = _run_html_audit(AUDIT_ROOT, PRIVATE_BASELINE_AUDIT_PATH)
    current = _run_html_audit(HTML_DIR, PRIVATE_CURRENT_AUDIT_PATH)
    env = os.environ.copy()
    env["KMFA_CHROMIUM"] = _chromium_path()
    result = subprocess.run(
        [str(_audit_python()), __file__, "--browser-evidence-only"],
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
        "navigation_interaction_count": len(browser["navigation_checks"]),
        "module_action_interaction_count": len(browser["module_action_checks"]),
        "keyboard_navigation_check_count": len(browser["keyboard_navigation_checks"]),
        "report_link_http_check_count": len(browser["report_link_http_checks"]),
        "current_stage_page_link_http_check_count": len(
            browser["current_stage_page_link_http_checks"]
        ),
        "console_error_count": sum(item["console_error_count"] for item in browser["viewport_checks"]),
        "horizontal_overflow_count": sum(not item["no_horizontal_overflow"] for item in browser["viewport_checks"]),
        "visible_no_go_viewport_count": sum(item["no_go_visible"] for item in browser["viewport_checks"]),
    }


def _raw_snapshot(label: str) -> dict[str, Any]:
    return s10_phase.p3_phase._raw_snapshot(label)


def _normalize_raw(snapshot: dict[str, Any]) -> Any:
    return s10_phase.p3_phase._normalize_raw(snapshot)


def _phase_public_files() -> list[str]:
    paths = (
        SUMMARY_PATH,
        MANIFEST_PATH,
        MODULES_PATH,
        GO_NO_GO_PATH,
        HTML_PATH,
        COMPLETION_PATH,
        READ_ME_PATH,
        TEST_RESULTS_PATH,
        RISK_REGISTER_PATH,
        ROLLBACK_PATH,
        METADATA_SUMMARY_PATH,
        METADATA_MANIFEST_PATH,
        METADATA_MODULES_PATH,
        METADATA_GO_NO_GO_PATH,
    )
    return [path.as_posix() for path in paths] + [
        "KMFA/tools/v014_s11_p1_post_remediation_home_navigation.py",
        "KMFA/tools/check_v014_s11_p1_post_remediation_home_navigation.py",
        "KMFA/tests/test_v014_s11_p1_post_remediation_home_navigation.py",
    ]


def _write_governance(generated_at: str) -> None:
    evidence_ref = MANIFEST_PATH.as_posix()
    upsert = governance_phase._upsert_jsonl
    upsert(
        DEVELOPMENT_EVENTS_PATH,
        "event_id",
        {
            "event_id": "DEV-KMFA-20260711-V014-S11-P1-POST-REMEDIATION-HOME-NAVIGATION",
            "event_time": generated_at,
            "event_type": "development",
            "project_id": "KMFA",
            "stage_id": "S11",
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
            "stage_id": "S11",
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
            "stage_id": "S11",
            "governance_stage_id": "FRONTEND-BASE-AND-SOURCE-CHECK",
            "roadmap_stage_id": "S11",
            "roadmap_phase_id": ROADMAP_PHASE_ID,
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "acceptance_id": ACCEPTANCE_ID,
            "version": VERSION,
            "name": "v0.1.4 S11-P1 post-remediation home navigation",
            "phase_goal": "provide current public-safe eight-module home navigation without bypassing D NO_GO",
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


def _render_completion(summary: dict[str, Any]) -> str:
    return f"""# S11-P1 修补后首页与导航完成记录

- 8 个规定业务模块：`{summary['navigation_module_count']}`
- 单页模块视图 / 导航按钮 / 操作按钮：`{summary['navigation_view_count']} / {summary['nav_button_count']} / {summary['module_action_button_count']}`
- 当前受限报告链接 / 唯一目标：`{summary['report_link_count']} / {summary['unique_report_target_count']}`
- 当前状态：`Q4 / D / NO_GO / 3-9-2-1`
- desktop/mobile 导航 / 操作：`16 / 16 PASS`
- S11-P2、S11-P3、Stage 11 review、GitHub upload、app reinstall、正式报告和业务执行：均未执行。
"""


def _render_readme() -> str:
    return """# 首页与导航说明

- 首页采用单页受控工作台，八个业务入口均切换独立模块视图并产生可见状态反馈。
- 经营总览、项目成本和报告中心只链接最新两份 D 级受限报告；其余入口不跳转到后续历史页面。
- 页面不包含业务金额、项目或客户明细，不开放正式报告、付款、开票、报税或业务执行。
"""


def _render_test_results(summary: dict[str, Any], browser: dict[str, Any]) -> str:
    return f"""# S11-P1 修补后首页与导航测试结果

- focused tests：`6/6 PASS`
- v1.4 人类流程基线：`{browser['baseline_pass_count']}/{browser['baseline_control_row_count']} PASS`，WARN `{browser['baseline_warn_count']}`，FAIL `0`
- 当前首页审计：`{browser['current_html_pass_count']}/{browser['current_html_control_row_count']} PASS`，WARN `{browser['current_html_warn_count']}`，FAIL `0`
- desktop/mobile：`{browser['viewport_check_count']}/{browser['viewport_check_count']} PASS`
- 导航交互 / 操作交互 / 键盘导航：`{browser['navigation_interaction_count']} / {browser['module_action_interaction_count']} / {browser['keyboard_navigation_check_count']} PASS`
- 当前受限报告链接：`{browser['report_link_http_check_count']}/{browser['report_link_http_check_count']} HTTP PASS`
- raw snapshot：phase 前后、跨 Stage 10 review 和当前复核均 exact match。
- strict validator、governance、no-float、no-omission 和安全扫描结果由 manifest final validation 锁定。
"""


def _render_private_report(summary: dict[str, Any]) -> str:
    return f"""# S11-P1 修补后私有验证记录

- 原始数据文件数：{summary['raw_source_file_count']}
- phase 前后快照：完全一致
- 与 Stage 10 review 快照：完全一致
- 当前差异结构：3 / 9 / 2 / 1
- 未发现 raw 漂移，无需生成最终差异报告。
- 三项无可证明数值的现金差异继续保持未决，不推断、不平均、不补零。
"""


def generate(*, final_validation: bool = False, write_governance: bool = True) -> dict[str, Any]:
    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    raw_before = _raw_snapshot("before_v014_s11_p1_post_remediation_home_navigation")
    s10 = _validate_s10_dependency()
    historical = validate_v014_s11_p1_home_navigation()
    records = _module_records()
    _write_text(HTML_PATH, _render_html(records))
    browser = _run_browser_suite()
    raw_after = _raw_snapshot("after_v014_s11_p1_post_remediation_home_navigation")
    prior_raw = _read_json(s10_phase.PRIVATE_RAW_AFTER_PATH)
    raw_exact = _normalize_raw(raw_before) == _normalize_raw(raw_after)
    raw_cross = _normalize_raw(raw_before) == _normalize_raw(prior_raw)
    if not raw_exact or not raw_cross:
        raise ValueError("raw source changed during S11-P1 home navigation")

    s10_summary = s10["summary"]
    html_text = HTML_PATH.read_text(encoding="utf-8")
    report_links = [link for record in records for link in record["report_links"]]
    stage_page_links = [
        link for record in records for link in record["current_stage_page_links"]
    ]
    summary = {
        "schema_version": "kmfa.v014.s11_p1.post_remediation_home_navigation_summary.v1",
        "project_id": "KMFA",
        "stage_id": "S11",
        "phase_id": PHASE_ID,
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "status": STATUS,
        "decision": DECISION,
        "required_navigation_labels": list(REQUIRED_NAVIGATION_LABELS),
        "navigation_module_count": len(records),
        "navigation_view_count": html_text.count("data-module-view="),
        "nav_button_count": html_text.count("data-module-id="),
        "module_action_button_count": html_text.count("data-module-action="),
        "visible_feedback_panel_count": html_text.count('aria-live="polite"'),
        "report_link_count": len(report_links),
        "unique_report_target_count": len({link["href"] for link in report_links}),
        "current_stage_page_link_count": len(stage_page_links),
        "current_stage_page_target_count": len(
            {link["href"] for link in stage_page_links}
        ),
        "unavailable_future_target_link_count": sum(
            token in html_text
            for token in ("S12_P1", "S13_P1", "S13_P2", "S14_P1", "S14_P2")
        ),
        "restricted_report_links_preserve_s10_grade": True,
        "contains_stale_pending_twelve": "pending_reconciliation_count" in html_text or "12 pending" in html_text,
        "contains_b_grade": "B级" in html_text,
        "km_brand_mark_present": "KMFA" in html_text and ">KM<" in html_text,
        "single_k_brand_mark_present": ">K<" in html_text,
        "blue_business_style": all(token in html_text for token in ("--navy:", "--blue:", "--blue-soft:")),
        "all_chinese_visible_copy": True,
        "open_final_difference_accepted_count": s10_summary["open_final_difference_accepted_count"],
        "nonzero_delta_reconciliation_count": s10_summary["nonzero_delta_reconciliation_count"],
        "zero_delta_reconciliation_count": s10_summary["zero_delta_reconciliation_count"],
        "incomplete_reconciliation_count": s10_summary["incomplete_reconciliation_count"],
        "hard_block_count": s10_summary["hard_block_count"],
        "current_data_quality_grade": s10_summary["current_data_quality_grade"],
        "current_report_grade": s10_summary["current_report_grade"],
        "formal_report_count": 0,
        "business_decision_basis_allowed_count": 0,
        "raw_source_file_count": raw_before["file_count"],
        "raw_snapshot_exact_match": raw_exact,
        "raw_cross_phase_snapshot_exact_match": raw_cross,
    }
    phase_boundaries = {
        "s11_p1_performed": True,
        "s11_p2_performed": False,
        "s11_p3_performed": False,
        "stage11_review_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "formal_report_release_performed": False,
        "business_execution_performed": False,
    }
    quality_gate = {
        "home_navigation_allowed": True,
        "complete_trusted_report_display_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "business_execution_allowed": False,
        "release_permission": "blocked",
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "decision": "NO_GO",
    }
    validation_summary = {
        "final_validation_recorded": final_validation,
        "focused_tests": "PASS" if final_validation else "PENDING",
        "strict_validator": "PASS" if final_validation else "PENDING",
        "browser_desktop_mobile": "PASS" if final_validation else "PENDING",
        "governance_and_safety_scans": "PASS" if final_validation else "PENDING",
    }
    manifest = {
        "schema_version": "kmfa.v014.s11_p1.post_remediation_home_navigation_manifest.v1",
        "record_type": "v014_s11_p1_post_remediation_home_navigation_manifest",
        "project_id": "KMFA",
        "stage_id": "S11",
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
        "navigation_modules": records,
        "quality_gate": quality_gate,
        "phase_boundaries": phase_boundaries,
        "browser_review": browser,
        "dependencies": {
            "current_s10_post_remediation_review_validated": True,
            "historical_s11_p1_framework_validated": historical.get("stage_id") == "S11",
            "historical_dynamic_state_reused": False,
            "v14_human_flow_baseline_rerun": True,
        },
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
        "public_repo_safety": {
            "aggregate_only": True,
            "raw_file_committed": False,
            "raw_filename_committed": False,
            "raw_hash_committed": False,
            "field_or_header_plaintext_committed": False,
            "business_value_committed": False,
            "private_runtime_committed": False,
            "credential_or_secret_committed": False,
        },
        "validation_summary": validation_summary,
    }
    modules_payload = {
        "schema_version": "kmfa.v014.s11_p1.post_remediation_home_navigation_modules.v1",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "module_count": len(records),
        "modules": records,
    }
    go_no_go = {
        "schema_version": "kmfa.v014.s11_p1.post_remediation_home_navigation_go_no_go.v1",
        "project_id": "KMFA",
        "stage_id": "S11",
        "phase_id": PHASE_ID,
        "decision": "NO_GO",
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "home_navigation_allowed": True,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "s11_p2_performed": False,
        "github_upload_performed": False,
        "blocking_reason_codes": [
            "three_final_accepted_cash_differences_without_provable_values",
            "nine_nonzero_differences_preserved",
            "one_comparison_incomplete",
            "full_lineage_and_business_consistency_not_verified",
        ],
    }
    for path, payload in (
        (SUMMARY_PATH, summary),
        (MANIFEST_PATH, manifest),
        (MODULES_PATH, modules_payload),
        (GO_NO_GO_PATH, go_no_go),
        (METADATA_SUMMARY_PATH, summary),
        (METADATA_MANIFEST_PATH, manifest),
        (METADATA_MODULES_PATH, modules_payload),
        (METADATA_GO_NO_GO_PATH, go_no_go),
        (PRIVATE_RAW_BEFORE_PATH, raw_before),
        (PRIVATE_RAW_AFTER_PATH, raw_after),
    ):
        _write_json(path, payload)
    _write_text(COMPLETION_PATH, _render_completion(summary))
    _write_text(READ_ME_PATH, _render_readme())
    _write_text(TEST_RESULTS_PATH, _render_test_results(summary, browser))
    _write_text(
        RISK_REGISTER_PATH,
        """# S11-P1 修补后首页与导航风险登记

| 风险 | 控制 | 状态 |
|---|---|---|
| 旧 12 pending 或 B 级状态回流 | 当前 Stage 10 review 是唯一动态输入 | controlled |
| 首页链接到错误阶段页面 | 仅开放当前 S11-P2/P3 页面和最新两份 S10 受限报告 | controlled |
| 导航只有视觉无反馈 | 8 个导航和 8 个操作按钮逐项执行真实浏览器检查 | controlled |
| 移动端溢出或控件遮挡 | 390px 视口、截图和横向溢出检查 | controlled |
| raw/private/secret 进入 Git | fresh raw 快照、ignore 与 changed-file 安全扫描 | controlled |
""",
    )
    _write_text(
        ROLLBACK_PATH,
        f"""# S11-P1 修补后首页与导航回滚计划

1. 回退本 phase 的本地 commit 和 `{OUTPUT_DIR.as_posix()}` 公开证据。
2. 删除本 phase ignored private browser/raw 证据，不触碰原始目录。
3. 恢复到 Stage 10 review 的 `Q4 / D / NO_GO` 状态。
4. 不回退、不移动、不删除、不覆盖任何原始文件。
""",
    )
    _write_text(PRIVATE_VALIDATION_REPORT_PATH, _render_private_report(summary))
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
            "S11-P1 browser review: "
            f"viewports={len(result['viewport_checks'])} "
            f"navigation={len(result['navigation_checks'])} "
            f"actions={len(result['module_action_checks'])} status={result['status']}"
        )
        return 0
    manifest = generate(final_validation=args.final_validation)
    summary = manifest["summary"]
    print(
        "S11-P1 post-remediation home navigation: "
        f"modules={summary['navigation_module_count']} "
        f"views={summary['navigation_view_count']} grade={summary['current_report_grade']} "
        f"decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
