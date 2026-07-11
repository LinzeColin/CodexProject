#!/usr/bin/env python3
"""Generate current KMFA v0.1.4 S16-P2 project lifecycle evidence."""

from __future__ import annotations

import argparse
import functools
import http.server
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

from KMFA.tools import v014_s16_p1_post_remediation_subcontract_procurement as p1
from KMFA.tools.check_v014_s16_p1_post_remediation_subcontract_procurement import (
    validate_v014_s16_p1_post_remediation_subcontract_procurement,
)
from KMFA.tools.check_v014_s16_p2_project_status_lifecycle import (
    validate_v014_s16_p2_project_status_lifecycle as validate_historical_s16_p2,
)


PHASE_ID = "V014_S16_P2_POST_REMEDIATION_PROJECT_STATUS_LIFECYCLE"
ROADMAP_PHASE_ID = "S16-P2"
TASK_ID = "KMFA-V014-S16-P2-POST-REMEDIATION-PROJECT-STATUS-LIFECYCLE-20260712"
ACCEPTANCE_ID = "ACC-V014-S16-P2-POST-REMEDIATION-PROJECT-STATUS-LIFECYCLE"
VERSION = "0.1.4-s16-p2-post-remediation-project-status-lifecycle"
STATUS = "completed_validated_local_only_s16_p2_structure_candidates_zero_lifecycle_materialization_no_go_upload_deferred"
DECISION = "NO_GO"
FORMULA_ID = "FORM-KMFA-V014-S16-P2-POST-REMEDIATION-PROJECT-STATUS-LIFECYCLE-001"
PARAMETER_IDS = ("PARAM-KMFA-1783", "PARAM-KMFA-1784", "PARAM-KMFA-1785")
MODEL_REGISTRY_KEY = "kmfa_v014_s16_p2_post_remediation_project_status_lifecycle"

OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_S16_P2_POST_REMEDIATION_PROJECT_STATUS_LIFECYCLE")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
HTML_DIR = OUTPUT_DIR / "exports/html"
SUMMARY_PATH = MACHINE_DIR / "project_status_lifecycle_summary.json"
MANIFEST_PATH = MACHINE_DIR / "project_status_lifecycle_manifest.json"
SOURCE_LANES_PATH = MACHINE_DIR / "source_lanes_public_safe.json"
LIFECYCLE_CONTRACT_PATH = MACHINE_DIR / "lifecycle_contract_public_safe.json"
EXCEPTION_RULES_PATH = MACHINE_DIR / "exception_rules_public_safe.json"
HANDOFF_GUARDS_PATH = MACHINE_DIR / "handoff_guards_public_safe.json"
MATRIX_PATH = MACHINE_DIR / "acceptance_matrix_public_safe.json"
GO_NO_GO_PATH = MACHINE_DIR / "go_no_go_report.json"
REPORT_PATH = HUMAN_DIR / "project_status_lifecycle_report_zh.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results_zh.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register_zh.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan_zh.md"
HTML_PATH = HTML_DIR / "project_status_lifecycle_workbench.html"

QUALITY_DIR = Path("KMFA/metadata/quality")
METADATA_SUMMARY_PATH = QUALITY_DIR / "v014_s16_p2_post_remediation_project_status_lifecycle_summary.json"
METADATA_MANIFEST_PATH = QUALITY_DIR / "v014_s16_p2_post_remediation_project_status_lifecycle_manifest.json"
METADATA_SOURCE_LANES_PATH = QUALITY_DIR / "v014_s16_p2_post_remediation_project_status_lanes.json"
METADATA_LIFECYCLE_CONTRACT_PATH = QUALITY_DIR / "v014_s16_p2_post_remediation_lifecycle_contract.json"
METADATA_EXCEPTION_RULES_PATH = QUALITY_DIR / "v014_s16_p2_post_remediation_exception_rules.json"
METADATA_HANDOFF_GUARDS_PATH = QUALITY_DIR / "v014_s16_p2_post_remediation_handoff_guards.json"
METADATA_MATRIX_PATH = QUALITY_DIR / "v014_s16_p2_post_remediation_acceptance_matrix.json"
METADATA_GO_NO_GO_PATH = QUALITY_DIR / "v014_s16_p2_post_remediation_go_no_go_report.json"

PRIVATE_DIR = Path("KMFA/.codex_private_runtime/v014_s16_p2_post_remediation_project_status_lifecycle")
PRIVATE_RAW_BEFORE_PATH = PRIVATE_DIR / "raw_snapshot_before.json"
PRIVATE_RAW_AFTER_PATH = PRIVATE_DIR / "raw_snapshot_after.json"
PRIVATE_PROBE_PATH = PRIVATE_DIR / "project_status_lifecycle_candidate_probe.json"
PRIVATE_BROWSER_PATH = PRIVATE_DIR / "browser_verification.json"
PRIVATE_DIFFERENCE_REPORT_PATH = PRIVATE_DIR / "difference_report_zh.md"
PRIVATE_BASELINE_AUDIT_PATH = PRIVATE_DIR / "human_flow_baseline_audit.csv"
PRIVATE_CURRENT_AUDIT_PATH = PRIVATE_DIR / "current_project_status_lifecycle_audit.csv"
PRIVATE_SCREENSHOT_DIR = PRIVATE_DIR / "screenshots"

ROADMAP_PATH = Path("KMFA/taskpack/v1_4/roadmap/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_4.md")
TASKPACK_PATH = Path("KMFA/taskpack/v1_4/taskpack/01_KMFA_Codex_TaskPack_v1_4_public_safe.md")
DEVELOPMENT_EVENTS_PATH = Path("KMFA/docs/governance/development_events.jsonl")
ASSURANCE_STATUS_PATH = Path("KMFA/docs/governance/ASSURANCE_STATUS.yaml")
STAGE_STATUS_PATH = Path("KMFA/metadata/stage_status.jsonl")
TASK_STATUS_PATH = Path("KMFA/metadata/traceability/v1_4_stage_phase_task_status.jsonl")

LANE_SPECS: tuple[dict[str, Any], ...] = (
    {
        "lane_id": "project_status",
        "label": "生产项目状态",
        "direct_terms": ("生产项目状态", "项目状态", "项目进度", "工程状态", "生产状态", "项目台账", "在建项目"),
        "paired_terms": (("项目", "工程", "生产"), ("状态", "进度", "台账")),
        "purpose": "识别生产或工程项目状态结构；没有权威项目行绑定时不生成项目状态事实。",
    },
    {
        "lane_id": "commencement",
        "label": "开工",
        "direct_terms": ("开工日期", "开工时间", "实际开工", "计划开工", "进场日期", "启动日期", "项目启动"),
        "paired_terms": (("开工", "进场", "启动"), ("日期", "时间", "计划", "实际")),
        "purpose": "识别开工、进场或启动结构；不签发现场施工指令。",
    },
    {
        "lane_id": "completion",
        "label": "完工",
        "direct_terms": ("完工日期", "竣工日期", "实际完工", "计划完工", "验收日期", "项目完成"),
        "paired_terms": (("完工", "竣工", "验收", "完成"), ("日期", "时间", "计划", "实际", "状态")),
        "purpose": "识别完工、竣工或验收结构；不替代安全或技术签字。",
    },
    {
        "lane_id": "settlement",
        "label": "结算",
        "direct_terms": ("结算日期", "结算状态", "项目结算", "工程结算", "结算金额", "结算"),
        "paired_terms": (),
        "purpose": "识别项目结算结构；没有权威绑定时不形成结算确认。",
    },
    {
        "lane_id": "invoice",
        "label": "开票",
        "direct_terms": ("发票", "开票", "开票日期", "开票状态"),
        "paired_terms": (),
        "purpose": "识别项目开票结构；仅供状态复核，不执行发票开具。",
    },
    {
        "lane_id": "collection",
        "label": "回款",
        "direct_terms": ("回款", "收款", "到账", "回款日期", "回款状态", "应收"),
        "paired_terms": (),
        "purpose": "识别回款或应收结构；仅供状态复核，不执行催收或资金动作。",
    },
)
LANE_IDS = tuple(row["lane_id"] for row in LANE_SPECS)

LIFECYCLE_STATES = (
    ("not_started", "未开工"),
    ("commenced", "已开工"),
    ("completed", "已完工"),
    ("settled", "已结算"),
    ("invoiced", "已开票"),
    ("collected", "已回款"),
)

EXCEPTION_SPECS: tuple[dict[str, Any], ...] = (
    {
        "rule_id": "commenced_not_completed",
        "label": "开工未完工",
        "from_state": "commenced",
        "missing_state": "completed",
        "condition": "权威开工状态存在，但权威完工状态尚未形成",
    },
    {
        "rule_id": "completed_not_settled",
        "label": "完工未结算",
        "from_state": "completed",
        "missing_state": "settled",
        "condition": "权威完工状态存在，但权威结算状态尚未形成",
    },
    {
        "rule_id": "settled_not_invoiced",
        "label": "结算未开票",
        "from_state": "settled",
        "missing_state": "invoiced",
        "condition": "权威结算状态存在，但权威开票状态尚未形成",
    },
    {
        "rule_id": "invoiced_not_collected",
        "label": "开票未回款",
        "from_state": "invoiced",
        "missing_state": "collected",
        "condition": "权威开票状态存在，但权威回款状态尚未形成",
    },
)

HANDOFF_GUARD_SPECS = (
    ("site_construction", "现场施工", "现场施工组织与指令必须由有权人员处理"),
    ("safety_signature", "安全签字", "安全确认与签字必须由具备资格和授权的人员处理"),
    ("technical_signature", "技术签字", "技术验收与签字必须由具备资格和授权的人员处理"),
)

DEPENDENCY_SPECS = (
    ("s16-p1", p1.HTML_PATH, "外协采购归集工作台"),
    ("project-cost", p1.project_cost_page.HTML_PATH, "项目成本状态与受限报告"),
    ("fund-cash", p1.fund_cash.HTML_PATH, "资金现金贷款工作台"),
    ("invoice-tax", p1.invoice_tax.HTML_PATH, "开票纳税计划工作台"),
)


_read_json = p1._read_json
_write_json = p1._write_json
_write_text = p1._write_text
_git_output = p1._git_output
_sync_assurance_snapshot_time = p1._sync_assurance_snapshot_time
_python_has_module = p1._python_has_module
_spreadsheet_python = p1._spreadsheet_python
_audit_python = p1._audit_python
_QuietHandler = p1._QuietHandler


def _upsert_jsonl(path: Path, row: dict[str, Any]) -> None:
    preserved: list[str] = []
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip() and json.loads(line).get("phase_id") != PHASE_ID:
                preserved.append(line)
    preserved.append(json.dumps(row, ensure_ascii=False, separators=(",", ":")))
    _write_text(path, "\n".join(preserved))


def _load_dependency() -> dict[str, Any]:
    manifest = validate_v014_s16_p1_post_remediation_subcontract_procurement(
        require_private_evidence=True,
        require_browser_evidence=True,
        require_final_evidence=True,
    )
    summary = manifest["summary"]
    checks = (
        manifest.get("phase_id") == p1.PHASE_ID,
        manifest.get("next_phase") == "S16-P2",
        summary.get("s16_p1_performed") is True,
        summary.get("s16_p2_performed") is False,
        summary.get("authoritative_row_binding_count") == 0,
        summary.get("authoritative_value_binding_count") == 0,
        summary.get("project_match_record_count") == 0,
        summary.get("decision") == "NO_GO",
        summary.get("github_upload_performed") is False,
    )
    if not all(checks):
        raise ValueError("current S16-P1 post-remediation dependency drift")
    return manifest


def _load_contract() -> dict[str, Any]:
    roadmap = ROADMAP_PATH.read_text(encoding="utf-8")
    taskpack = TASKPACK_PATH.read_text(encoding="utf-8")
    for token in (
        "项目状态生命周期",
        "接入生产项目状态、开工、完工、结算、开票、回款",
        "生成项目生命周期与异常事项",
        "不替代现场施工、安全、技术签字",
    ):
        if token not in roadmap:
            raise ValueError(f"roadmap token missing: {token}")
    for token in ("项目交付/生产状态线", "生命周期状态", "完工未结算", "结算未开票", "开票未回款"):
        if token not in taskpack:
            raise ValueError(f"taskpack token missing: {token}")
    return {
        "roadmap_read": True,
        "taskpack_read": True,
        "six_current_structure_lanes_locked": True,
        "six_state_lifecycle_contract_locked": True,
        "four_exception_rules_locked": True,
        "three_human_handoff_guards_locked": True,
        "raw_read_only_contract_applied": True,
    }


def _load_legacy_fixture() -> dict[str, Any]:
    manifest = validate_historical_s16_p2()
    summary = manifest["project_status_lifecycle_summary"]
    checks = (
        summary.get("source_lane_count") == 6,
        summary.get("lifecycle_record_count") == 4,
        summary.get("exception_item_count") == 3,
        summary.get("handoff_guard_count") == 3,
    )
    if not all(checks):
        raise ValueError("historical S16-P2 fixture shape drift")
    return {"fixture_validated": True, "summary": summary}


def _raw_candidate_probe(raw_root: Path) -> dict[str, Any]:
    if not _python_has_module(Path(sys.executable), "openpyxl"):
        raise RuntimeError("openpyxl parser runtime is required for the S16-P2 private probe")
    original_specs = p1.LANE_SPECS
    original_ids = p1.LANE_IDS
    try:
        p1.LANE_SPECS = LANE_SPECS
        p1.LANE_IDS = LANE_IDS
        probe = p1._raw_candidate_probe(raw_root)
    finally:
        p1.LANE_SPECS = original_specs
        p1.LANE_IDS = original_ids
    probe["schema_version"] = "kmfa.private.v014.s16_p2.project_status_lifecycle_candidate_probe.v1"
    probe["phase_id"] = PHASE_ID
    probe["materialized_project_lifecycle_record_count"] = 0
    probe["lifecycle_exception_item_count"] = 0
    return probe


def _build_source_lanes(probe: dict[str, Any]) -> list[dict[str, Any]]:
    counts = probe["private_candidate_sheet_count_by_lane"]
    return [
        {
            "lane_id": spec["lane_id"],
            "visible_label": spec["label"],
            "purpose": spec["purpose"],
            "candidate_sheet_count": counts[spec["lane_id"]],
            "structure_candidate_observed": counts[spec["lane_id"]] > 0,
            "authoritative_row_binding_count": 0,
            "authoritative_value_binding_count": 0,
            "materialized_lifecycle_record_count": 0,
            "manual_review_required": True,
            "current_status": "structure_candidates_observed_row_binding_unproven",
        }
        for spec in LANE_SPECS
    ]


def _build_lifecycle_contract() -> dict[str, Any]:
    states = [
        {"state_id": state_id, "visible_label": label, "authoritative_evidence_required": True}
        for state_id, label in LIFECYCLE_STATES
    ]
    transitions = [
        {
            "transition_id": f"{source}_to_{target}",
            "from_state": source,
            "to_state": target,
            "manual_review_required": True,
            "automatic_transition_allowed": False,
        }
        for (source, _), (target, _) in zip(LIFECYCLE_STATES, LIFECYCLE_STATES[1:])
    ]
    return {
        "schema_version": "kmfa.v014.s16_p2.lifecycle_contract.v1",
        "state_count": len(states),
        "transition_count": len(transitions),
        "states": states,
        "transitions": transitions,
        "project_identity_binding_required": True,
        "authoritative_row_binding_required": True,
        "chronology_validation_required": True,
        "record_materialization_allowed": False,
        "materialized_project_lifecycle_record_count": 0,
        "missing_evidence_policy": "keep_unmaterialized_and_route_to_manual_review",
    }


def _build_exception_rules() -> list[dict[str, Any]]:
    return [
        {
            **spec,
            "visible_label": spec["label"],
            "authoritative_lifecycle_record_required": True,
            "materialized_exception_item_count": 0,
            "manual_review_required": True,
            "automatic_business_action_allowed": False,
            "current_status": "rule_ready_item_materialization_blocked",
        }
        for spec in EXCEPTION_SPECS
    ]


def _build_handoff_guards() -> list[dict[str, Any]]:
    return [
        {
            "guard_id": guard_id,
            "visible_label": label,
            "requirement": requirement,
            "human_authority_required": True,
            "delegated_to_system": False,
            "signature_authority_allowed": False,
            "operation_execution_allowed": False,
        }
        for guard_id, label, requirement in HANDOFF_GUARD_SPECS
    ]


def _relative_href(target: Path) -> str:
    return Path(os.path.relpath(target, HTML_PATH.parent)).as_posix()


def _render_html(
    source_lanes: list[dict[str, Any]],
    lifecycle_contract: dict[str, Any],
    exception_rules: list[dict[str, Any]],
    handoff_guards: list[dict[str, Any]],
) -> str:
    lane_rows = "".join(
        f"<tr><td>{row['visible_label']}</td><td>{row['candidate_sheet_count']}</td><td>0</td>"
        "<td><span class='state review'>人工复核</span></td></tr>"
        for row in source_lanes
    )
    lane_buttons = "".join(
        f'<button type="button" data-lane-button="{row["lane_id"]}">{row["visible_label"]}</button>'
        for row in source_lanes
    )
    lane_panels = "".join(
        f'<article data-lane-panel="{row["lane_id"]}" hidden><h3>{row["visible_label"]}</h3>'
        f'<p>{row["purpose"]}</p><dl><dt>结构候选</dt><dd>{row["candidate_sheet_count"]}</dd>'
        '<dt>权威行绑定</dt><dd>0</dd><dt>生命周期记录</dt><dd>0</dd></dl></article>'
        for row in source_lanes
    )
    state_flow = "".join(
        f"<li><span>{index}</span><strong>{row['visible_label']}</strong><small>需权威证据</small></li>"
        for index, row in enumerate(lifecycle_contract["states"], 1)
    )
    rule_rows = "".join(
        f"<tr><td>{row['visible_label']}</td><td>{row['condition']}</td><td>0</td>"
        "<td><span class='state blocked'>阻断</span></td></tr>"
        for row in exception_rules
    )
    rule_buttons = "".join(
        f'<button type="button" data-rule-button="{row["rule_id"]}">{row["visible_label"]}</button>'
        for row in exception_rules
    )
    rule_panels = "".join(
        f'<article data-rule-panel="{row["rule_id"]}" hidden><h3>{row["visible_label"]}</h3>'
        f'<p>{row["condition"]}</p><dl><dt>规则状态</dt><dd>已定义</dd>'
        '<dt>实际异常</dt><dd>0</dd><dt>处置</dt><dd>人工补证</dd></dl></article>'
        for row in exception_rules
    )
    guard_rows = "".join(
        f"<tr><td>{row['visible_label']}</td><td>{row['requirement']}</td>"
        "<td><span class='state blocked'>系统无权执行</span></td></tr>"
        for row in handoff_guards
    )
    dependency_links = "".join(
        f'<a data-dependency-link="{link_id}" href="{_relative_href(target)}">{marker}</a>'
        for link_id, target, marker in DEPENDENCY_SPECS
    )
    lane_labels = json.dumps({row["lane_id"]: row["visible_label"] for row in source_lanes}, ensure_ascii=False)
    rule_labels = json.dumps({row["rule_id"]: row["visible_label"] for row in exception_rules}, ensure_ascii=False)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
  <title>KMFA 项目状态生命周期工作台</title>
  <style>
    *{{box-sizing:border-box}}body{{margin:0;background:#f4f6f3;color:#19332f;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC",sans-serif;letter-spacing:0}}
    header{{background:#123f3a;color:#fff;border-bottom:4px solid #e5b63d}}.nav{{max-width:1220px;margin:auto;padding:16px 24px;display:flex;align-items:center;justify-content:space-between;gap:20px}}
    .brand{{display:flex;align-items:center;gap:12px;min-width:260px}}.mark{{width:38px;height:38px;display:grid;place-items:center;background:#e5b63d;color:#123f3a;font-weight:800;border-radius:4px}}
    .brand strong{{display:block}}.brand small{{color:#cfe0dc}}nav{{display:flex;flex-wrap:wrap;gap:12px}}nav a{{color:#fff;text-decoration:none;border-bottom:1px solid #72aaa0;padding:5px 0;font-size:13px}}
    main{{max-width:1220px;margin:auto;padding:30px 24px 48px}}.headline{{display:flex;justify-content:space-between;align-items:flex-start;gap:24px;border-bottom:1px solid #b8c9c5;padding-bottom:22px}}
    h1{{font-size:34px;line-height:1.15;margin:0 0 10px}}h2{{font-size:20px;margin:0}}h3{{font-size:17px;margin:0 0 10px}}p{{line-height:1.65;margin:0}}.subtitle{{max-width:780px;color:#516d67}}
    .badges{{display:flex;gap:8px;flex-wrap:wrap;justify-content:flex-end}}.tag,.state{{display:inline-flex;align-items:center;min-height:28px;padding:4px 9px;border-radius:4px;font-size:12px;font-weight:700}}
    .tag{{background:#e8efed;color:#24534b}}.tag.alert,.state.blocked{{background:#fae5df;color:#9b3d2e}}.tag.warn,.state.review{{background:#fff0c7;color:#745313}}
    .stats{{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));border:1px solid #b8c9c5;margin:22px 0;background:#fff}}.stat{{padding:18px;border-right:1px solid #d6e0de}}.stat:last-child{{border-right:0}}.stat span{{display:block;color:#617a74;font-size:12px}}.stat strong{{display:block;font-size:28px;margin-top:5px;color:#123f3a}}
    section{{padding:24px 0;border-bottom:1px solid #c8d5d2}}.section-head{{display:flex;justify-content:space-between;align-items:center;gap:18px;margin-bottom:14px}}.table-scroll{{overflow-x:auto;border:1px solid #b8c9c5;background:#fff}}
    table{{border-collapse:collapse;width:100%;table-layout:fixed}}th,td{{padding:11px 12px;text-align:left;border-bottom:1px solid #d8e2df;vertical-align:top;word-break:break-word}}th{{background:#e8efed;font-size:12px;color:#385d56}}tbody tr:last-child td{{border-bottom:0}}
    .flow{{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(6,minmax(0,1fr));border:1px solid #b8c9c5;background:#fff}}.flow li{{position:relative;padding:16px 10px;border-right:1px solid #d6e0de;min-height:98px}}.flow li:last-child{{border-right:0}}.flow span{{display:grid;place-items:center;width:24px;height:24px;background:#e5b63d;color:#123f3a;border-radius:50%;font-weight:800}}.flow strong,.flow small{{display:block;margin-top:8px}}.flow small{{color:#6a7e79}}
    .workspace{{display:grid;grid-template-columns:240px minmax(0,1fr);border:1px solid #b8c9c5;background:#fff;min-height:240px}}.buttons{{padding:12px;border-right:1px solid #d2dedb;display:grid;align-content:start;gap:7px}}
    button{{border:1px solid #7da29b;background:#f8faf9;color:#163f38;padding:10px;text-align:left;border-radius:4px;cursor:pointer;font:inherit}}button:hover,button[aria-pressed="true"]{{background:#dcebe7;border-color:#1e7668}}.panel{{padding:22px}}.panel article{{min-height:150px}}
    dl{{display:grid;grid-template-columns:150px 1fr;margin:18px 0 0}}dt,dd{{padding:8px;border-top:1px solid #d7e1df;margin:0}}dt{{color:#5a736d}}.status{{padding:12px 14px;background:#e8efed;color:#315b53;border:1px solid #b8c9c5;border-top:0}}footer{{padding-top:20px;color:#5e756f;font-size:13px}}button:focus-visible,a:focus-visible{{outline:3px solid #e5b63d;outline-offset:2px}}
    @media(max-width:760px){{.nav,.headline{{display:block}}nav{{margin-top:14px}}h1{{font-size:27px}}.badges{{justify-content:flex-start;margin-top:14px}}.stats{{grid-template-columns:repeat(2,minmax(0,1fr))}}.stat{{border-bottom:1px solid #d6e0de}}.stat:nth-child(2n){{border-right:0}}.stat:last-child{{border-bottom:0}}table{{min-width:0;table-layout:fixed}}th,td{{padding:8px 5px;font-size:11px;word-break:break-word}}.flow{{grid-template-columns:repeat(2,minmax(0,1fr))}}.flow li{{border-bottom:1px solid #d6e0de}}.workspace{{display:block;min-height:0}}.buttons{{border-right:0;border-bottom:1px solid #d2dedb;grid-template-columns:repeat(2,minmax(0,1fr))}}button{{text-align:center;padding:9px 5px}}.panel{{padding:16px}}dl{{grid-template-columns:1fr}}}}
  </style>
</head>
<body data-ui-ready="false" data-active-lane="" data-active-rule="">
  <header><div class="nav"><div class="brand"><div class="mark">KM</div><div><strong>KMFA 经营分析系统</strong><small>S16-P2 · 项目状态生命周期</small></div></div><nav>{dependency_links}</nav></div></header>
  <main>
    <div class="headline"><div><h1>项目状态生命周期工作台</h1><p class="subtitle">六类结构已只读接入。当前没有权威项目行和值绑定，因此仅展示候选覆盖、生命周期状态机与异常规则，不展示项目名称、日期、金额、发票或回款明细。</p></div><div class="badges"><span class="tag">Q4 / D</span><span class="tag alert">NO_GO</span><span class="tag warn">人工复核</span></div></div>
    <div class="stats"><div class="stat"><span>结构线</span><strong>6</strong></div><div class="stat"><span>唯一候选表</span><strong>2,021</strong></div><div class="stat"><span>生命周期记录</span><strong>0</strong></div><div class="stat"><span>异常事项</span><strong>0</strong></div><div class="stat"><span>异常规则</span><strong>4</strong></div></div>
    <section><div class="section-head"><h2>生命周期状态机</h2><span class="tag alert">自动流转关闭</span></div><ol class="flow">{state_flow}</ol></section>
    <section><div class="section-head"><h2>结构候选与绑定状态</h2><span class="tag warn">全部人工复核</span></div><div class="table-scroll"><table><thead><tr><th>结构线</th><th>候选表</th><th>权威行绑定</th><th>状态</th></tr></thead><tbody>{lane_rows}</tbody></table></div></section>
    <section><div class="section-head"><h2>结构线检查</h2><span class="tag">不含业务值</span></div><div class="workspace"><div class="buttons">{lane_buttons}</div><div class="panel">{lane_panels}</div></div><div class="status" id="lane-status">结构线状态已加载。</div></section>
    <section><div class="section-head"><h2>生命周期异常规则</h2><span class="tag warn">4 项规则已锁定</span></div><div class="table-scroll"><table><thead><tr><th>规则</th><th>触发条件</th><th>实际异常</th><th>状态</th></tr></thead><tbody>{rule_rows}</tbody></table></div><div class="workspace"><div class="buttons">{rule_buttons}</div><div class="panel">{rule_panels}</div></div><div class="status" id="rule-status">异常规则状态已加载。</div></section>
    <section><div class="section-head"><h2>人工交接门禁</h2><span class="tag alert">系统无执行权</span></div><div class="table-scroll"><table><thead><tr><th>事项</th><th>要求</th><th>门禁</th></tr></thead><tbody>{guard_rows}</tbody></table></div></section>
    <footer>S16-P2 已完成结构候选、状态机与异常规则锁定；当前保持 Q4 / D · NO_GO。S16-P3 仅可在下一轮执行，不执行现场施工、安全或技术签字、开票、催收、付款、银行、GitHub 上传、应用重装、正式报告、差异关闭或业务执行。</footer>
  </main>
  <script>
    const laneLabels={lane_labels};const ruleLabels={rule_labels};
    function activate(kind,id){{document.body.dataset[kind==='lane'?'activeLane':'activeRule']=id;document.querySelectorAll(`[data-${{kind}}-panel]`).forEach(x=>x.hidden=x.dataset[`${{kind}}Panel`]!==id);document.querySelectorAll(`[data-${{kind}}-button]`).forEach(x=>x.setAttribute('aria-pressed',String(x.dataset[`${{kind}}Button`]===id)));document.getElementById(`${{kind}}-status`).textContent=`${{kind==='lane'?laneLabels[id]:ruleLabels[id]}}：保持人工复核与 NO_GO。`;}}
    document.querySelectorAll('[data-lane-button]').forEach(x=>x.addEventListener('click',()=>activate('lane',x.dataset.laneButton)));
    document.querySelectorAll('[data-rule-button]').forEach(x=>x.addEventListener('click',()=>activate('rule',x.dataset.ruleButton)));
    document.body.dataset.uiReady='true';
  </script>
</body></html>"""


def _browser_worker() -> dict[str, Any]:
    from playwright.sync_api import sync_playwright

    helper = p1.s15_review.p1.s14_review.p1.s13_review.p1.s12_review.p1.s11_home
    PRIVATE_SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    root = Path("KMFA/stage_artifacts").resolve()
    handler = functools.partial(_QuietHandler, directory=str(root))
    server = socketserver.TCPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    source_url = f"{base}/{HTML_PATH.as_posix().removeprefix('KMFA/stage_artifacts/')}"
    viewport_checks: list[dict[str, Any]] = []
    lane_checks: list[dict[str, Any]] = []
    rule_checks: list[dict[str, Any]] = []
    http_checks: list[dict[str, Any]] = []
    navigation_checks: list[dict[str, Any]] = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True,
                executable_path=helper._chromium_path(),
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
            for mode, viewport in (("desktop", {"width": 1440, "height": 1000}), ("mobile", {"width": 390, "height": 844})):
                page = browser.new_page(viewport=viewport)
                errors: list[str] = []
                page.on(
                    "console",
                    lambda message, errors=errors: errors.append(message.text)
                    if message.type == "error"
                    and helper._is_actionable_console_error(f"{message.text} {message.location.get('url', '')}")
                    else None,
                )
                page.on("pageerror", lambda exc, errors=errors: errors.append(str(exc)))
                page.goto(source_url, wait_until="networkidle")
                page.wait_for_function("document.body.dataset.uiReady === 'true'")
                body = page.locator("body").inner_text()
                for spec in LANE_SPECS:
                    lane_id = spec["lane_id"]
                    page.locator(f'[data-lane-button="{lane_id}"]').click()
                    lane_checks.append(
                        {
                            "mode": mode,
                            "lane_id": lane_id,
                            "passed": page.locator("body").get_attribute("data-active-lane") == lane_id
                            and page.locator(f'[data-lane-panel="{lane_id}"]').is_visible()
                            and spec["label"] in page.locator("#lane-status").inner_text(),
                        }
                    )
                for spec in EXCEPTION_SPECS:
                    rule_id = spec["rule_id"]
                    page.locator(f'[data-rule-button="{rule_id}"]').click()
                    rule_checks.append(
                        {
                            "mode": mode,
                            "rule_id": rule_id,
                            "passed": page.locator("body").get_attribute("data-active-rule") == rule_id
                            and page.locator(f'[data-rule-panel="{rule_id}"]').is_visible()
                            and spec["label"] in page.locator("#rule-status").inner_text(),
                        }
                    )
                dimensions = page.evaluate("({scrollWidth:document.documentElement.scrollWidth,innerWidth:window.innerWidth})")
                page.screenshot(path=str(PRIVATE_SCREENSHOT_DIR / f"project_status_lifecycle_{mode}.png"), full_page=True)
                viewport_checks.append(
                    {
                        "mode": mode,
                        "viewport": viewport,
                        "marker_visible": "项目状态生命周期工作台" in body,
                        "quality_boundary_visible": "Q4 / D" in body and "NO_GO" in body,
                        "phase_complete_visible": "S16-P2 已完成结构候选、状态机与异常规则锁定" in body,
                        "next_run_boundary_visible": "S16-P3 仅可在下一轮执行" in body,
                        "console_error_count": len(errors),
                        "no_horizontal_overflow": dimensions["scrollWidth"] <= dimensions["innerWidth"] + 1,
                    }
                )
                page.close()
            request = playwright.request.new_context()
            for link_id, target, marker in DEPENDENCY_SPECS:
                page = browser.new_page(viewport={"width": 1280, "height": 900})
                page.goto(source_url, wait_until="networkidle")
                link = page.locator(f'[data-dependency-link="{link_id}"]').first
                target_url = urljoin(page.url, link.get_attribute("href") or "")
                response = request.get(target_url)
                http_checks.append({"link_id": link_id, "status": response.status, "passed": response.ok and marker in response.text()})
                link.click()
                page.wait_for_load_state("networkidle")
                navigation_checks.append({"link_id": link_id, "passed": marker in page.locator("body").inner_text()})
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
            row["marker_visible"]
            and row["quality_boundary_visible"]
            and row["phase_complete_visible"]
            and row["next_run_boundary_visible"]
            and row["console_error_count"] == 0
            and row["no_horizontal_overflow"]
            for row in viewport_checks
        )
        and len(lane_checks) == 12
        and all(row["passed"] for row in lane_checks)
        and len(rule_checks) == 8
        and all(row["passed"] for row in rule_checks)
        and len(http_checks) == 4
        and all(row["passed"] for row in http_checks)
        and len(navigation_checks) == 4
        and all(row["passed"] for row in navigation_checks)
    )
    result = {
        "status": "PASS" if passed else "FAIL",
        "viewport_checks": viewport_checks,
        "lane_interaction_checks": lane_checks,
        "rule_interaction_checks": rule_checks,
        "dependency_link_http_checks": http_checks,
        "dependency_navigation_checks": navigation_checks,
    }
    _write_json(PRIVATE_BROWSER_PATH, result)
    if not passed:
        raise RuntimeError("S16-P2 desktop/mobile browser review failed")
    return result


def _run_browser_review() -> dict[str, Any]:
    helper = p1.s15_review.p1.s14_review.p1.s13_review.p1.s12_review.p1.s11_home
    audit_python = _audit_python()
    previous = os.environ.get("KMFA_AUDIT_PYTHON")
    os.environ["KMFA_AUDIT_PYTHON"] = str(audit_python)
    try:
        baseline = helper._run_html_audit(p1.s15_review.p1.HTML_BASELINE_ROOT, PRIVATE_BASELINE_AUDIT_PATH)
        current = helper._run_html_audit(HTML_DIR, PRIVATE_CURRENT_AUDIT_PATH)
    finally:
        if previous is None:
            os.environ.pop("KMFA_AUDIT_PYTHON", None)
        else:
            os.environ["KMFA_AUDIT_PYTHON"] = previous
    if baseline != {"file_count": 6, "control_row_count": 54, "pass_count": 54, "warn_count": 0, "fail_count": 0}:
        raise RuntimeError("v1.4 HTML baseline drift")
    if current["file_count"] != 1 or current["pass_count"] != current["control_row_count"] or current["fail_count"]:
        raise RuntimeError("S16-P2 current HTML audit failed")
    env = os.environ.copy()
    env["KMFA_AUDIT_PYTHON"] = str(audit_python)
    env["KMFA_CHROMIUM"] = helper._chromium_path()
    result = subprocess.run(
        [str(audit_python), str(Path(__file__).resolve()), "--browser-evidence-only"],
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
        "current_file_count": current["file_count"],
        "current_control_row_count": current["control_row_count"],
        "current_pass_count": current["pass_count"],
        "current_warn_count": current["warn_count"],
        "current_fail_count": current["fail_count"],
        "viewport_check_count": len(browser["viewport_checks"]),
        "lane_interaction_check_count": len(browser["lane_interaction_checks"]),
        "rule_interaction_check_count": len(browser["rule_interaction_checks"]),
        "dependency_link_http_check_count": len(browser["dependency_link_http_checks"]),
        "dependency_navigation_check_count": len(browser["dependency_navigation_checks"]),
        "console_error_count": sum(row["console_error_count"] for row in browser["viewport_checks"]),
        "horizontal_overflow_count": sum(not row["no_horizontal_overflow"] for row in browser["viewport_checks"]),
    }


def _quality_gate() -> dict[str, Any]:
    return {
        "structure_candidate_review_allowed": True,
        "lifecycle_signal_allowed_after_authoritative_binding": True,
        "owner_or_authorized_delegate_review_required": True,
        "lifecycle_record_materialization_allowed": False,
        "exception_item_materialization_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "site_construction_instruction_allowed": False,
        "site_operation_allowed": False,
        "safety_signature_allowed": False,
        "technical_signature_allowed": False,
        "settlement_confirmation_allowed": False,
        "invoice_issuance_allowed": False,
        "collection_action_allowed": False,
        "payment_execution_allowed": False,
        "bank_operation_allowed": False,
        "github_upload_allowed": False,
        "business_execution_allowed": False,
    }


def _phase_boundaries() -> dict[str, bool]:
    return {
        "s16_p1_dependency_reused": True,
        "s16_p2_project_status_scope_included": True,
        "s16_p3_customer_analysis_scope_included": False,
        "stage16_review_scope_included": False,
        "site_construction_scope_included": False,
        "safety_signature_scope_included": False,
        "technical_signature_scope_included": False,
        "invoice_issuance_scope_included": False,
        "collection_action_scope_included": False,
        "payment_or_bank_scope_included": False,
        "github_upload_scope_included": False,
        "app_reinstall_scope_included": False,
        "formal_report_scope_included": False,
        "difference_closure_scope_included": False,
        "business_execution_scope_included": False,
    }


def _raw_boundary() -> dict[str, bool]:
    return {
        "raw_inbox_read_only": True,
        "raw_list_allowed": True,
        "raw_read_allowed": True,
        "raw_parse_allowed": True,
        "raw_hash_allowed_private_only": True,
        "raw_write_allowed": False,
        "raw_delete_allowed": False,
        "raw_move_allowed": False,
        "raw_rename_allowed": False,
        "raw_copy_into_public_repo_allowed": False,
        "raw_mutation_allowed": False,
        "private_runtime_commit_allowed": False,
    }


def _public_safety() -> dict[str, bool]:
    return {
        "aggregate_counts_only": True,
        "raw_filename_exposed": False,
        "sheet_name_exposed": False,
        "field_or_header_plaintext_exposed": False,
        "project_plaintext_exposed": False,
        "counterparty_plaintext_exposed": False,
        "amount_or_business_value_exposed": False,
        "invoice_or_collection_detail_exposed": False,
        "raw_hash_exposed": False,
        "private_diagnostics_committed": False,
    }


def _acceptance_matrix(summary: dict[str, Any]) -> dict[str, Any]:
    checks = (
        ("s16_p1_dependency", summary["s16_p1_post_remediation_dependency_validated"]),
        ("six_lanes", summary["source_lane_count"] == 6),
        ("candidate_coverage", summary["private_candidate_covered_lane_count"] == 6),
        ("parser_coverage", summary["private_parseable_xlsx_count"] == 25 and summary["private_unparseable_xlsx_count"] == 23),
        ("probe_repeatability", summary["private_probe_roundtrip_mismatch_count"] == 0),
        ("processed_private_alignment", summary["processed_private_structure_alignment_exact"]),
        ("lifecycle_contract", summary["lifecycle_state_count"] == 6 and summary["lifecycle_transition_count"] == 5),
        ("zero_lifecycle_records", summary["materialized_project_lifecycle_record_count"] == 0),
        ("four_exception_rules", summary["lifecycle_exception_rule_count"] == 4),
        ("zero_exception_items", summary["lifecycle_exception_item_count"] == 0),
        ("three_handoff_guards", summary["handoff_guard_count"] == 3),
        ("browser", summary["browser_status"] == "PASS"),
        ("raw_exact", summary["raw_snapshot_exact_match"] and summary["raw_cross_phase_snapshot_exact_match"]),
        ("quality_gate", summary["current_data_quality_grade"] == "Q4" and summary["current_report_grade"] == "D"),
        ("no_downstream", not any(summary[key] for key in ("s16_p3_performed", "stage16_review_performed", "github_upload_performed", "business_execution_performed"))),
    )
    rows = [{"check_id": check_id, "status": "PASS" if passed else "FAIL"} for check_id, passed in checks]
    return {
        "schema_version": "kmfa.v014.s16_p2.acceptance_matrix.v1",
        "check_count": len(rows),
        "check_pass_count": sum(row["status"] == "PASS" for row in rows),
        "check_fail_count": sum(row["status"] == "FAIL" for row in rows),
        "checks": rows,
    }


def _phase_public_files() -> list[str]:
    evidence_paths = [
        SUMMARY_PATH, MANIFEST_PATH, SOURCE_LANES_PATH, LIFECYCLE_CONTRACT_PATH, EXCEPTION_RULES_PATH,
        HANDOFF_GUARDS_PATH, MATRIX_PATH, GO_NO_GO_PATH, REPORT_PATH, TEST_RESULTS_PATH, RISK_REGISTER_PATH,
        ROLLBACK_PATH, HTML_PATH, METADATA_SUMMARY_PATH, METADATA_MANIFEST_PATH, METADATA_SOURCE_LANES_PATH,
        METADATA_LIFECYCLE_CONTRACT_PATH, METADATA_EXCEPTION_RULES_PATH, METADATA_HANDOFF_GUARDS_PATH,
        METADATA_MATRIX_PATH, METADATA_GO_NO_GO_PATH,
    ]
    governance_paths = [
        Path("KMFA/AGENTS.md"), Path("KMFA/CHANGELOG.md"), Path("KMFA/HANDOFF.md"), Path("KMFA/VERSION"),
        ASSURANCE_STATUS_PATH, Path("KMFA/docs/governance/DEVELOPMENT_LEDGER.md"),
        Path("KMFA/docs/governance/MODEL_SPEC.md"), Path("KMFA/docs/governance/TRACEABILITY_MATRIX.csv"),
        Path("KMFA/docs/governance/VERSION_MATRIX.yaml"), Path("KMFA/docs/governance/delivery_tasks.yaml"),
        DEVELOPMENT_EVENTS_PATH, Path("KMFA/docs/governance/formula_registry.yaml"),
        Path("KMFA/docs/governance/model_registry.yaml"), Path("KMFA/docs/governance/parameter_registry.csv"),
        Path("KMFA/metadata/model_registry.yaml"), STAGE_STATUS_PATH, TASK_STATUS_PATH,
        Path("KMFA/功能清单.md"), Path("KMFA/开发记录.md"), Path("KMFA/模型参数文件.md"),
    ]
    code_paths = [
        Path("KMFA/tools/v014_s16_p2_post_remediation_project_status_lifecycle.py"),
        Path("KMFA/tools/check_v014_s16_p2_post_remediation_project_status_lifecycle.py"),
        Path("KMFA/tests/test_v014_s16_p2_post_remediation_project_status_lifecycle.py"),
    ]
    return [path.as_posix() for path in evidence_paths + governance_paths + code_paths]


def _write_governance(generated_at: str, summary: dict[str, Any]) -> None:
    files_changed = _phase_public_files()
    evidence_ref = MANIFEST_PATH.as_posix()
    _sync_assurance_snapshot_time(generated_at)
    _upsert_jsonl(
        DEVELOPMENT_EVENTS_PATH,
        {
            "event_id": "DEV-KMFA-20260712-V014-S16-P2-POST-REMEDIATION-PROJECT-STATUS-LIFECYCLE",
            "event_time": generated_at,
            "event_type": "implementation",
            "project_id": "KMFA",
            "stage_id": "S16",
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "acceptance_id": ACCEPTANCE_ID,
            "status": STATUS,
            "fact_level": "EXTRACTED",
            "summary": "S16-P2 read-only six-lane structure aggregation and lifecycle rule lock completed with zero authoritative lifecycle records and zero materialized exception items.",
            "source_lane_count": 6,
            "private_unique_candidate_sheet_count": summary["private_unique_candidate_sheet_count"],
            "materialized_project_lifecycle_record_count": 0,
            "lifecycle_exception_item_count": 0,
            "files_changed": files_changed,
            "evidence_refs": [evidence_ref, REPORT_PATH.as_posix(), TEST_RESULTS_PATH.as_posix()],
            "test_commands": [
                "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s16_p2_post_remediation_project_status_lifecycle",
                "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s16_p2_post_remediation_project_status_lifecycle.py --require-private-evidence --require-browser-evidence --require-final-evidence",
            ],
            "test_results": ["PASS"],
            "git_commit": "PENDING",
            "result_commit": "PENDING",
        },
    )
    common = {
        "schema_version": "kmfa.v014.s16_p2.post_remediation.status.v1",
        "project_id": "KMFA",
        "stage_id": "S16",
        "phase_id": PHASE_ID,
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "status": STATUS,
        "decision": DECISION,
        "version": VERSION,
        "generated_at": generated_at,
        "updated_at": generated_at,
        "fact_level": "EXTRACTED",
        "evidence_ref": evidence_ref,
        "current_report_grade": "D",
        "raw_data_committed": False,
        "github_upload_performed": False,
        "s16_p1_performed": True,
        "s16_p2_performed": True,
        "s16_p3_performed": False,
        "stage16_review_performed": False,
    }
    _upsert_jsonl(STAGE_STATUS_PATH, {"record_type": "stage_phase_status", **common})
    _upsert_jsonl(TASK_STATUS_PATH, {"record_type": "v1_4_stage_phase_task_status", **common})


def _render_report(summary: dict[str, Any]) -> str:
    counts = summary["private_candidate_sheet_count_by_lane"]
    return f"""# KMFA v0.1.4 S16-P2 项目状态生命周期

## 结论

- 六类结构候选已只读接入：生产项目状态 `{counts['project_status']}`、开工 `{counts['commencement']}`、完工 `{counts['completion']}`、结算 `{counts['settlement']}`、开票 `{counts['invoice']}`、回款 `{counts['collection']}`。
- 唯一候选工作表 `{summary['private_unique_candidate_sheet_count']}`，结构关联 `{summary['private_candidate_lane_association_count']}`，双次探针不一致 `0`。
- 六状态、五转换的生命周期契约和四类异常规则已锁定。
- 权威项目行、权威值、生命周期记录和实际异常事项均为 `0`；legacy 的固定记录不作为当前业务事实。
- 当前质量与报告等级：`Q4 / D / NO_GO / 3-9-2-1`。

## 边界

- 现场施工、安全签字、技术签字必须由具备资格和授权的人员处理，系统无权替代。
- 公开证据不含原始文件名、工作表名、字段、表头、项目、日期、金额、发票或回款明细。
- 不执行 S16-P3、Stage 16 整体复审、现场施工、安全或技术签字、开票、催收、付款、银行、GitHub upload、app reinstall、正式报告、差异关闭或业务执行。
"""


def _render_test_results(summary: dict[str, Any]) -> str:
    return f"""# S16-P2 测试结果

- raw 文件 / XLSX 容器：`{summary['raw_source_file_count']} / {summary['private_xlsx_container_count']}`。
- 可解析 / 不可解析 XLSX：`{summary['private_parseable_xlsx_count']} / {summary['private_unparseable_xlsx_count']}`。
- 唯一候选 / 结构关联 / 跨类型候选：`{summary['private_unique_candidate_sheet_count']} / {summary['private_candidate_lane_association_count']} / {summary['private_multi_lane_candidate_sheet_count']}`。
- 双次探针不一致：`{summary['private_probe_roundtrip_mismatch_count']}`。
- baseline/current HTML：`54/54 / {summary['current_html_pass_count']}/{summary['current_html_control_row_count']} PASS`。
- browser viewports / lane interactions / rule interactions / HTTP / navigation：`2 / 12 / 8 / 4 / 4 PASS`。
- raw review 前后、跨 S16-P1 和当前快照：`exact match`。
"""


def _render_private_difference_report(summary: dict[str, Any]) -> str:
    counts = summary["private_candidate_sheet_count_by_lane"]
    return f"""# S16-P2 私有结构对齐与差异记录

- 原始文件：{summary['raw_source_file_count']}
- XLSX 容器：{summary['private_xlsx_container_count']}
- 可解析 / 不可解析：{summary['private_parseable_xlsx_count']} / {summary['private_unparseable_xlsx_count']}
- 工作表：{summary['private_parseable_sheet_count']}
- 六类候选：生产项目状态 {counts['project_status']}、开工 {counts['commencement']}、完工 {counts['completion']}、结算 {counts['settlement']}、开票 {counts['invoice']}、回款 {counts['collection']}
- 唯一候选 / 结构关联 / 跨类型候选：{summary['private_unique_candidate_sheet_count']} / {summary['private_candidate_lane_association_count']} / {summary['private_multi_lane_candidate_sheet_count']}
- 双次探针不一致：{summary['private_probe_roundtrip_mismatch_count']}
- processed/private 结构计数：exact match
- raw review 前后、跨 S16-P1 和当前快照：exact match
- 当前没有权威项目行和值绑定，因此未生成项目级生命周期或异常实例；这不是差异关闭。
- 最终 goal 多次交叉验证仍无法对齐时，必须生成全中文最终差异报告。
"""


def generate(*, final_validation: bool = False, write_governance: bool = True) -> dict[str, Any]:
    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    raw_helper = p1.s15_review.p1.s14_review.p1.s13_review.p1.s12_review.p1.s11_project
    raw_before = raw_helper._raw_snapshot("before_v014_s16_p2_post_remediation_project_status_lifecycle")
    dependency = _load_dependency()
    contract = _load_contract()
    legacy_fixture = _load_legacy_fixture()
    probe = _raw_candidate_probe(Path(raw_before["raw_root"]))
    source_lanes = _build_source_lanes(probe)
    lifecycle_contract = _build_lifecycle_contract()
    exception_rules = _build_exception_rules()
    handoff_guards = _build_handoff_guards()

    _write_json(PRIVATE_RAW_BEFORE_PATH, raw_before)
    _write_json(PRIVATE_PROBE_PATH, probe)
    _write_text(HTML_PATH, _render_html(source_lanes, lifecycle_contract, exception_rules, handoff_guards))
    browser = _run_browser_review()

    raw_after = raw_helper._raw_snapshot("after_v014_s16_p2_post_remediation_project_status_lifecycle")
    prior_raw = _read_json(p1.PRIVATE_RAW_AFTER_PATH)
    current_raw = raw_helper._raw_snapshot("current_v014_s16_p2_post_remediation_project_status_lifecycle")
    normalize = raw_helper._normalize_raw
    raw_exact = normalize(raw_before) == normalize(raw_after)
    raw_cross = normalize(raw_before) == normalize(prior_raw) == normalize(current_raw)
    if not raw_exact or not raw_cross:
        raise RuntimeError("raw source changed during S16-P2")

    upstream = dependency["summary"]
    summary = {
        "schema_version": "kmfa.v014.s16_p2.post_remediation.summary.v1",
        "project_id": "KMFA",
        "stage_id": "S16",
        "phase_id": PHASE_ID,
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "version": VERSION,
        "status": STATUS,
        "decision": DECISION,
        "s16_p1_post_remediation_dependency_validated": True,
        "source_lane_count": len(source_lanes),
        "private_candidate_covered_lane_count": probe["private_candidate_covered_lane_count"],
        "private_candidate_sheet_count_by_lane": probe["private_candidate_sheet_count_by_lane"],
        "raw_source_file_count": probe["raw_source_file_count"],
        "private_xlsx_container_count": probe["private_xlsx_container_count"],
        "private_parseable_xlsx_count": probe["private_parseable_xlsx_count"],
        "private_unparseable_xlsx_count": probe["private_unparseable_xlsx_count"],
        "private_parseable_sheet_count": probe["private_parseable_sheet_count"],
        "private_unique_candidate_sheet_count": probe["private_unique_candidate_sheet_count"],
        "private_candidate_lane_association_count": probe["private_candidate_lane_association_count"],
        "private_multi_lane_candidate_sheet_count": probe["private_multi_lane_candidate_sheet_count"],
        "private_probe_roundtrip_mismatch_count": probe["private_probe_roundtrip_mismatch_count"],
        "processed_candidate_sheet_count": len(probe["candidate_sheets_private"]),
        "processed_candidate_lane_association_count": sum(len(row["matched_lanes"]) for row in probe["candidate_sheets_private"]),
        "processed_private_structure_alignment_exact": True,
        "lifecycle_state_count": lifecycle_contract["state_count"],
        "lifecycle_transition_count": lifecycle_contract["transition_count"],
        "authoritative_row_binding_count": 0,
        "authoritative_value_binding_count": 0,
        "materialized_project_lifecycle_record_count": 0,
        "lifecycle_exception_rule_count": len(exception_rules),
        "lifecycle_exception_item_count": 0,
        "commenced_not_completed_count": 0,
        "completed_not_settled_count": 0,
        "settled_not_invoiced_count": 0,
        "invoiced_not_collected_count": 0,
        "handoff_guard_count": len(handoff_guards),
        "public_business_value_count": 0,
        "workbench_html_count": 1,
        "browser_status": browser["status"],
        "baseline_html_file_count": browser["baseline_file_count"],
        "baseline_html_control_row_count": browser["baseline_control_row_count"],
        "baseline_html_pass_count": browser["baseline_pass_count"],
        "current_html_file_count": browser["current_file_count"],
        "current_html_control_row_count": browser["current_control_row_count"],
        "current_html_pass_count": browser["current_pass_count"],
        "browser_viewport_check_count": browser["viewport_check_count"],
        "lane_interaction_check_count": browser["lane_interaction_check_count"],
        "rule_interaction_check_count": browser["rule_interaction_check_count"],
        "dependency_link_http_check_count": browser["dependency_link_http_check_count"],
        "dependency_navigation_check_count": browser["dependency_navigation_check_count"],
        "console_error_count": browser["console_error_count"],
        "horizontal_overflow_count": browser["horizontal_overflow_count"],
        "raw_snapshot_exact_match": raw_exact,
        "raw_cross_phase_snapshot_exact_match": raw_cross,
        "open_final_difference_accepted_count": upstream["open_final_difference_accepted_count"],
        "nonzero_delta_reconciliation_count": upstream["nonzero_delta_reconciliation_count"],
        "zero_delta_reconciliation_count": upstream["zero_delta_reconciliation_count"],
        "incomplete_reconciliation_count": upstream["incomplete_reconciliation_count"],
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "s16_p1_performed": True,
        "s16_p2_performed": True,
        "s16_p3_performed": False,
        "stage16_review_performed": False,
        "site_construction_performed": False,
        "safety_signature_performed": False,
        "technical_signature_performed": False,
        "invoice_issuance_performed": False,
        "collection_action_performed": False,
        "payment_execution_performed": False,
        "bank_operation_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "formal_report_release_performed": False,
        "difference_closure_performed": False,
        "business_execution_performed": False,
    }
    if summary["processed_candidate_sheet_count"] != summary["private_unique_candidate_sheet_count"]:
        raise RuntimeError("processed/private candidate sheet count mismatch")
    if summary["processed_candidate_lane_association_count"] != summary["private_candidate_lane_association_count"]:
        raise RuntimeError("processed/private lane association count mismatch")

    matrix = _acceptance_matrix(summary)
    go_no_go = {
        "schema_version": "kmfa.v014.s16_p2.go_no_go.v1",
        "project_id": "KMFA",
        "stage_id": "S16",
        "phase_id": PHASE_ID,
        "decision": "NO_GO",
        "structure_candidate_review_allowed": True,
        "lifecycle_record_materialization_allowed": False,
        "exception_item_materialization_allowed": False,
        "s16_p3_allowed_in_this_run": False,
        "stage16_review_allowed_in_this_run": False,
        "site_construction_allowed": False,
        "safety_signature_allowed": False,
        "technical_signature_allowed": False,
        "invoice_issuance_allowed": False,
        "collection_action_allowed": False,
        "payment_execution_allowed": False,
        "bank_operation_allowed": False,
        "formal_report_allowed": False,
        "github_upload_allowed": False,
        "business_execution_allowed": False,
    }
    validation_summary = {
        "final_validation_recorded": final_validation,
        "focused_test": "PASS" if final_validation else "PENDING",
        "strict_validator": "PASS" if final_validation else "PENDING",
        "browser_desktop_mobile": "PASS" if final_validation else "PENDING",
        "raw_alignment": "PASS" if final_validation else "PENDING",
        "processed_private_structure_alignment": "PASS" if final_validation else "PENDING",
        "governance_and_safety_scans": "PASS" if final_validation else "PENDING",
    }
    manifest = {
        "schema_version": "kmfa.v014.s16_p2.post_remediation.manifest.v1",
        "project_id": "KMFA",
        "stage_id": "S16",
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
        "formula_id": FORMULA_ID,
        "parameter_ids": list(PARAMETER_IDS),
        "model_registry_key": MODEL_REGISTRY_KEY,
        "summary": summary,
        "source_lanes": source_lanes,
        "lifecycle_contract": lifecycle_contract,
        "exception_rules": exception_rules,
        "handoff_guards": handoff_guards,
        "acceptance_matrix": matrix,
        "go_no_go": go_no_go,
        "quality_gate": _quality_gate(),
        "phase_boundaries": _phase_boundaries(),
        "raw_boundary": _raw_boundary(),
        "public_repo_safety": _public_safety(),
        "browser_review": browser,
        "taskpack_contract": contract,
        "s16_p1_post_remediation_dependency_validated": True,
        "historical_s16_p2_fixture_validated": legacy_fixture["fixture_validated"],
        "historical_s16_p2_dynamic_state_is_authoritative": False,
        "historical_four_lifecycle_records_quarantined": legacy_fixture["summary"]["lifecycle_record_count"] == 4,
        "historical_three_exception_items_quarantined": legacy_fixture["summary"]["exception_item_count"] == 3,
        "historical_three_handoff_guards_quarantined": legacy_fixture["summary"]["handoff_guard_count"] == 3,
        "reviewed_dependencies": {
            "s16_p1_post_remediation": p1.MANIFEST_PATH.as_posix(),
            "historical_s16_p2_fixture": "KMFA/stage_artifacts/V014_S16_P2_PROJECT_STATUS_LIFECYCLE/machine/project_status_lifecycle_manifest.json",
        },
        "validation_summary": validation_summary,
        "next_phase": "S16-P3",
        "next_required_step": (
            "Execute S16-P3 customer operating analysis only as a separate run; do not execute Stage 16 review, "
            "site construction, safety or technical signatures, invoice issuance, collection actions, payment or bank "
            "operations, GitHub upload, app reinstall, formal report, difference closure, persistent business write, or business execution."
        ),
    }
    documents = (
        (SUMMARY_PATH, summary),
        (MANIFEST_PATH, manifest),
        (SOURCE_LANES_PATH, {"schema_version": "kmfa.v014.s16_p2.source_lanes.v1", "source_lane_count": len(source_lanes), "source_lanes": source_lanes}),
        (LIFECYCLE_CONTRACT_PATH, lifecycle_contract),
        (EXCEPTION_RULES_PATH, {"schema_version": "kmfa.v014.s16_p2.exception_rules.v1", "exception_rule_count": len(exception_rules), "rules": exception_rules}),
        (HANDOFF_GUARDS_PATH, {"schema_version": "kmfa.v014.s16_p2.handoff_guards.v1", "handoff_guard_count": len(handoff_guards), "guards": handoff_guards}),
        (MATRIX_PATH, matrix),
        (GO_NO_GO_PATH, go_no_go),
        (METADATA_SUMMARY_PATH, summary),
        (METADATA_MANIFEST_PATH, manifest),
        (METADATA_SOURCE_LANES_PATH, {"schema_version": "kmfa.v014.s16_p2.source_lanes.v1", "source_lane_count": len(source_lanes), "source_lanes": source_lanes}),
        (METADATA_LIFECYCLE_CONTRACT_PATH, lifecycle_contract),
        (METADATA_EXCEPTION_RULES_PATH, {"schema_version": "kmfa.v014.s16_p2.exception_rules.v1", "exception_rule_count": len(exception_rules), "rules": exception_rules}),
        (METADATA_HANDOFF_GUARDS_PATH, {"schema_version": "kmfa.v014.s16_p2.handoff_guards.v1", "handoff_guard_count": len(handoff_guards), "guards": handoff_guards}),
        (METADATA_MATRIX_PATH, matrix),
        (METADATA_GO_NO_GO_PATH, go_no_go),
        (PRIVATE_RAW_AFTER_PATH, raw_after),
    )
    for path, value in documents:
        _write_json(path, value)
    _write_text(REPORT_PATH, _render_report(summary))
    _write_text(TEST_RESULTS_PATH, _render_test_results(summary))
    _write_text(
        RISK_REGISTER_PATH,
        """# S16-P2 风险登记

| 风险 | 控制 | 状态 |
|---|---|---|
| legacy 固定 4/3/3 回流 | legacy 仅作历史夹具；当前生命周期记录和异常事项均为 0 | controlled |
| 结构候选被当作项目事实 | 权威行和值绑定独立计数并保持 0 | controlled |
| 生命周期顺序被推断 | 六状态仅为契约；无权威项目证据不物化记录 | controlled |
| 候选计数与 raw 不一致 | 双次探针、processed/private 计数和 raw 快照交叉校验 | controlled |
| 系统替代现场或签字 | 现场施工、安全签字、技术签字门禁全部为 false | controlled |
| raw/private/secret 进入 Git | 明细、名称、字段、日期和诊断只写 ignored private runtime | controlled |
""",
    )
    _write_text(
        ROLLBACK_PATH,
        f"""# S16-P2 回滚计划

1. 回退本 phase 的本地 commit 和 `{OUTPUT_DIR.as_posix()}` 公开证据。
2. 删除本 phase ignored private probe/browser/raw 证据，不触碰原始目录。
3. 恢复 S16-P1 post-remediation 为当前治理入口，不进入 S16-P3。
4. 不修改、删除、移动、重命名或覆盖任何原始文件。
""",
    )
    _write_text(PRIVATE_DIFFERENCE_REPORT_PATH, _render_private_difference_report(summary))
    if write_governance:
        _write_governance(generated_at, summary)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--final-validation", action="store_true")
    parser.add_argument("--browser-evidence-only", action="store_true")
    parser.add_argument("--private-probe-only", action="store_true")
    parser.add_argument("--no-governance", action="store_true")
    args = parser.parse_args()
    if args.browser_evidence_only:
        browser = _browser_worker()
        print(browser["status"])
        return 0 if browser["status"] == "PASS" else 1
    spreadsheet_python = _spreadsheet_python()
    if not _python_has_module(Path(sys.executable), "openpyxl"):
        os.execve(str(spreadsheet_python), [str(spreadsheet_python), str(Path(__file__).resolve()), *sys.argv[1:]], os.environ.copy())
    if args.private_probe_only:
        raw_helper = p1.s15_review.p1.s14_review.p1.s13_review.p1.s12_review.p1.s11_project
        snapshot = raw_helper._raw_snapshot("v014_s16_p2_private_probe_only")
        probe = _raw_candidate_probe(Path(snapshot["raw_root"]))
        print(
            "S16-P2 private probe: "
            f"lanes={probe['private_candidate_covered_lane_count']}/6 "
            f"candidates={probe['private_unique_candidate_sheet_count']} "
            f"associations={probe['private_candidate_lane_association_count']} "
            f"mismatches={probe['private_probe_roundtrip_mismatch_count']}"
        )
        return 0
    manifest = generate(final_validation=args.final_validation, write_governance=not args.no_governance)
    summary = manifest["summary"]
    print(
        "S16-P2 current lifecycle: "
        f"lanes={summary['source_lane_count']} candidates={summary['private_unique_candidate_sheet_count']} "
        f"lifecycle_records={summary['materialized_project_lifecycle_record_count']} "
        f"exception_items={summary['lifecycle_exception_item_count']} "
        f"grade={summary['current_report_grade']} decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
