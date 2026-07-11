#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate current public-safe KMFA S12-P1 pending-action evidence."""

from __future__ import annotations

import argparse
import functools
import html
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

from KMFA.tools import v014_s11_p1_post_remediation_home_navigation as s11_home
from KMFA.tools import v014_s11_p3_post_remediation_project_cost_page as s11_project
from KMFA.tools import v014_s11_post_remediation_stage_review as s11_review
from KMFA.tools import v014_s12_p1_manual_resolution_events as legacy_s12
from KMFA.tools.check_v014_s11_post_remediation_stage_review import (
    validate_v014_s11_post_remediation_stage_review,
)


PHASE_ID = "V014_S12_P1_POST_REMEDIATION_PENDING_ACTIONS"
ROADMAP_PHASE_ID = "S12-P1"
TASK_ID = "KMFA-V014-S12-P1-POST-REMEDIATION-PENDING-ACTIONS-20260711"
ACCEPTANCE_ID = "ACC-V014-S12-P1-POST-REMEDIATION-PENDING-ACTIONS"
VERSION = "0.1.4-s12-p1-post-remediation-pending-actions"
STATUS = "completed_validated_local_only_s12_p1_no_go_upload_deferred"
DECISION = "NO_GO"
FORMULA_ID = "FORM-KMFA-V014-S12P1-POST-REMEDIATION-PENDING-ACTIONS-001"
PARAMETER_IDS = (
    "PARAM-KMFA-1720",
    "PARAM-KMFA-1721",
    "PARAM-KMFA-1722",
    "PARAM-KMFA-1723",
)
MODEL_REGISTRY_KEY = "kmfa_v014_s12_p1_post_remediation_pending_actions"

OUTPUT_DIR = Path("KMFA/stage_artifacts") / PHASE_ID
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
HTML_DIR = OUTPUT_DIR / "exports" / "html"
SUMMARY_PATH = MACHINE_DIR / "pending_actions_summary.json"
MANIFEST_PATH = MACHINE_DIR / "pending_actions_manifest.json"
GROUPS_PATH = MACHINE_DIR / "pending_action_groups_public_safe.json"
EVENT_TEMPLATES_PATH = MACHINE_DIR / "manual_event_templates_public_safe.json"
GO_NO_GO_PATH = MACHINE_DIR / "pending_actions_go_no_go_report.json"
HTML_PATH = HTML_DIR / "kmfa_pending_actions_workbench.html"
REPORT_PATH = HUMAN_DIR / "s12_p1_pending_actions_report_zh.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results_zh.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register_zh.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan_zh.md"

QUALITY_DIR = Path("KMFA/metadata/quality")
METADATA_SUMMARY_PATH = QUALITY_DIR / "v014_s12_p1_post_remediation_pending_actions_summary.json"
METADATA_MANIFEST_PATH = QUALITY_DIR / "v014_s12_p1_post_remediation_pending_actions_manifest.json"
METADATA_GROUPS_PATH = QUALITY_DIR / "v014_s12_p1_post_remediation_pending_action_groups_public_safe.json"
METADATA_EVENT_TEMPLATES_PATH = (
    QUALITY_DIR / "v014_s12_p1_post_remediation_manual_event_templates_public_safe.json"
)
METADATA_GO_NO_GO_PATH = QUALITY_DIR / "v014_s12_p1_post_remediation_pending_actions_go_no_go_report.json"

PRIVATE_DIR = Path("KMFA/.codex_private_runtime/v014_s12_p1_post_remediation_pending_actions")
PRIVATE_RAW_BEFORE_PATH = PRIVATE_DIR / "raw_immutability_before.json"
PRIVATE_RAW_AFTER_PATH = PRIVATE_DIR / "raw_immutability_after.json"
PRIVATE_VALIDATION_REPORT_PATH = PRIVATE_DIR / "s12_p1_private_validation_zh.md"
PRIVATE_BROWSER_PATH = PRIVATE_DIR / "browser_verification.json"
PRIVATE_BASELINE_AUDIT_PATH = PRIVATE_DIR / "human_flow_baseline_audit.csv"
PRIVATE_CURRENT_AUDIT_PATH = PRIVATE_DIR / "current_pending_actions_audit.csv"
PRIVATE_SCREENSHOT_DIR = PRIVATE_DIR / "screenshots"

V14_ROADMAP_PATH = Path("KMFA/taskpack/v1_4/roadmap/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_4.md")
V14_TASKPACK_PATH = Path("KMFA/taskpack/v1_4/taskpack/01_KMFA_Codex_TaskPack_v1_4_public_safe.md")
V14_WORKBENCH_PATH = Path("KMFA/taskpack/v1_4/html_uiux/KMFA_待处理事项工作台可点击预览_v1_4.html")
V14_HTML_ROOT = Path("KMFA/taskpack/v1_4/html_uiux")

DEVELOPMENT_EVENTS_PATH = Path("KMFA/docs/governance/development_events.jsonl")
STAGE_STATUS_PATH = Path("KMFA/metadata/stage_status.jsonl")
TASK_STATUS_PATH = Path("KMFA/metadata/traceability/v1_4_stage_phase_task_status.jsonl")

HOME_HREF = "../../../V014_S11_P1_POST_REMEDIATION_HOME_NAVIGATION/exports/html/kmfa_home_navigation.html#pending_actions"
SOURCE_HREF = "../../../V014_S11_P2_POST_REMEDIATION_SOURCE_CHECK_BOARD/exports/html/kmfa_source_check_board.html"
PROJECT_HREF = "../../../V014_S11_P3_POST_REMEDIATION_PROJECT_COST_PAGE/exports/html/kmfa_project_cost_page.html"
RETURN_LINKS = (
    ("home", HOME_HREF, "经营分析工作台"),
    ("source", SOURCE_HREF, "KMFA 数据源检查板"),
    ("project", PROJECT_HREF, "KMFA 项目成本页面"),
)

ACTION_LABELS = {
    "field_mapping": "字段映射",
    "project_matching": "项目匹配",
    "difference_handling": "差异处理",
    "note": "备注",
}
STATUS_LABELS = {
    "pending_review": "待复核",
    "evidence_ready": "证据待确认",
    "comparison_incomplete": "比较未完成",
    "accepted_global_only": "仅全局接受",
    "unknown_attribution": "归属未知",
    "source_not_ready": "来源未就绪",
}


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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
    lines: list[str] = []
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip() and json.loads(line).get("phase_id") != row.get("phase_id"):
                lines.append(line)
    lines.append(json.dumps(row, ensure_ascii=False, separators=(",", ":")))
    _write_text(path, "\n".join(lines))


def _load_stage11_dependency() -> dict[str, Any]:
    manifest = validate_v014_s11_post_remediation_stage_review(require_final_evidence=True)
    summary = manifest["summary"]
    expected = {
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "decision": "NO_GO",
        "open_final_difference_accepted_count": 3,
        "nonzero_delta_reconciliation_count": 9,
        "zero_delta_reconciliation_count": 2,
        "incomplete_reconciliation_count": 1,
        "project_specific_unknown_allocation_count": 4,
        "source_check_matrix_row_count": 13,
        "hard_block_count": 12,
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            raise RuntimeError(f"Stage 11 dependency drift: {key}")
    if summary.get("s12_p1_performed") is not False:
        raise RuntimeError("Stage 11 dependency already claims S12-P1")
    if summary.get("github_upload_performed") is not False:
        raise RuntimeError("Stage 11 dependency must not include GitHub upload")
    return manifest


def _load_contract() -> dict[str, Any]:
    roadmap = V14_ROADMAP_PATH.read_text(encoding="utf-8")
    taskpack = V14_TASKPACK_PATH.read_text(encoding="utf-8")
    workbench = V14_WORKBENCH_PATH.read_text(encoding="utf-8")
    for token in (
        "前端处理只写事件：字段映射、项目匹配、差异处理、备注",
        "每个事件有处理人、时间、原因、影响范围、版本",
        "已批准事件不可静默改写，只能追加反向事件",
    ):
        if token not in roadmap:
            raise RuntimeError(f"v1.4 roadmap S12-P1 token missing: {token}")
    for token in ("待处理事项必须有处理意见、影响预览、重跑链路", "FAIL = 0"):
        if token not in taskpack:
            raise RuntimeError(f"v1.4 taskpack token missing: {token}")
    for token in ("待处理事项", "处理面板", "处理意见", "生成影响预览", "复跑受影响链路"):
        if token not in workbench:
            raise RuntimeError(f"v1.4 workbench token missing: {token}")
    legacy = legacy_s12.validate_legacy_s12_p1_artifacts()
    if not legacy["approved_event_reversal_chain_present"]:
        raise RuntimeError("legacy approved/reverse policy fixture invalid")
    return {
        "roadmap_contract_read": True,
        "taskpack_human_flow_gate_read": True,
        "clickable_workbench_sample_read": True,
        "required_manual_action_kinds": list(ACTION_LABELS),
        "impact_preview_required_in_s12_p2": True,
        "derived_rerun_required_in_s12_p3": True,
        "legacy_approved_event_count": legacy["approved_event_count"],
        "legacy_reverse_event_count": legacy["reverse_event_count"],
        "legacy_reverse_chain_validated": True,
        "source_refs": [
            V14_ROADMAP_PATH.as_posix(),
            V14_TASKPACK_PATH.as_posix(),
            V14_WORKBENCH_PATH.as_posix(),
            legacy_s12.MANIFEST_PATH.as_posix(),
        ],
    }


def _pending_action_groups(summary: dict[str, Any]) -> list[dict[str, Any]]:
    specs = (
        (
            "PEND-S12P1-001",
            "非零差异复核",
            "difference_handling",
            summary["nonzero_delta_reconciliation_count"],
            "pending_review",
            "D级报告与经营结论继续阻断",
            "选择差异处理意见并生成仅当前会话候选事件",
        ),
        (
            "PEND-S12P1-002",
            "零差异证据复核",
            "note",
            summary["zero_delta_reconciliation_count"],
            "evidence_ready",
            "零差异结果仍需保留来源证据与复核说明",
            "追加公开安全复核备注候选",
        ),
        (
            "PEND-S12P1-003",
            "未完成比较补全",
            "difference_handling",
            summary["incomplete_reconciliation_count"],
            "comparison_incomplete",
            "现金与项目成本链路仍有未完成比较",
            "记录待补证原因，不执行影响预览或重跑",
        ),
        (
            "PEND-S12P1-004",
            "最终差异接受说明",
            "note",
            summary["open_final_difference_accepted_count"],
            "accepted_global_only",
            "仅保留全局接受状态，不证明项目级归属",
            "追加限制说明，禁止改写为项目归属结论",
        ),
        (
            "PEND-S12P1-005",
            "项目归属复核",
            "project_matching",
            summary["project_specific_unknown_allocation_count"],
            "unknown_attribution",
            "项目成本页面继续显示未知归属",
            "生成项目匹配候选事件，不自动合并或归属",
        ),
        (
            "PEND-S12P1-006",
            "数据源映射与状态复核",
            "field_mapping",
            summary["source_check_matrix_row_count"],
            "source_not_ready",
            "数据源检查板状态继续影响报告可用性",
            "生成字段映射候选事件，不改原始字段或表头",
        ),
    )
    groups = []
    for group_id, title, kind, count, status, impact, next_step in specs:
        groups.append(
            {
                "schema_version": "kmfa.v014.s12_p1.pending_action_group.v1",
                "record_type": "public_safe_pending_action_group",
                "group_id": group_id,
                "visible_title": title,
                "manual_action_kind": kind,
                "item_count": count,
                "count_semantics": "aggregate_non_additive",
                "responsible_role": "owner_or_authorized_delegate",
                "status": status,
                "impact_summary": impact,
                "next_step": next_step,
                "project_attribution": "unknown_or_not_applicable",
                "session_candidate_only": True,
                "persistent_business_write_allowed": False,
                "raw_layer_write_allowed": False,
                "public_amount_values_committed": False,
                "source_evidence_refs": [s11_review.MANIFEST_PATH.as_posix()],
            }
        )
    return groups


def _manual_event_templates() -> list[dict[str, Any]]:
    specs = (
        (
            "CAND-EVT-S12P1-001",
            "mapping_rule",
            "field_mapping",
            "propose_field_mapping_rule",
            "FIELD_MAPPING_REVIEW_REQUIRED",
            ["source_check_matrix", "field_mapping_catalog"],
        ),
        (
            "CAND-EVT-S12P1-002",
            "approval_event",
            "project_matching",
            "propose_project_match_review",
            "PROJECT_MATCH_REVIEW_REQUIRED",
            ["project_identity_review_queue", "project_cost_pending_actions"],
        ),
        (
            "CAND-EVT-S12P1-003",
            "resolution_event",
            "difference_handling",
            "propose_difference_handling",
            "DIFFERENCE_HANDLING_REVIEW_REQUIRED",
            ["scope_reconciliation_queue", "restricted_report_grade"],
        ),
        (
            "CAND-EVT-S12P1-004",
            "comment",
            "note",
            "add_review_note_candidate",
            "OWNER_NOTE_DRAFTED",
            ["manual_resolution_workbench", "review_note_log"],
        ),
    )
    rows = []
    for index, (event_id, event_type, kind, action, reason, impact_scope) in enumerate(specs, 1):
        rows.append(
            {
                "schema_version": "kmfa.v014.s12_p1.manual_event_template.v1",
                "record_type": "public_safe_session_event_template",
                "event_id": event_id,
                "event_type": event_type,
                "manual_action_kind": kind,
                "event_action": action,
                "actor_ref": "actor_ref://owner_or_authorized_delegate/session-only",
                "event_time_policy": "browser_session_clock_at_creation",
                "reason_code": reason,
                "impact_scope": impact_scope,
                "event_version": f"SESSION-CANDIDATE-S12P1-001.{index:03d}",
                "approval_state": "draft",
                "append_only": True,
                "session_candidate_only": True,
                "silent_update_allowed": False,
                "persistent_business_write_allowed": False,
                "raw_layer_write_allowed": False,
                "public_amount_values_committed": False,
            }
        )
    return rows


def _phase_boundaries() -> dict[str, bool]:
    return {
        "stage11_post_remediation_review_dependency_validated": True,
        "s12_p1_performed": True,
        "s12_p2_performed": False,
        "s12_p3_performed": False,
        "stage12_review_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "formal_report_release_performed": False,
        "persistent_business_write_performed": False,
        "business_execution_performed": False,
        "raw_write_performed": False,
        "raw_delete_performed": False,
        "raw_move_performed": False,
        "raw_rename_performed": False,
        "raw_overwrite_performed": False,
    }


def _quality_gate() -> dict[str, Any]:
    return {
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "decision": DECISION,
        "release_permission": "blocked",
        "candidate_event_creation_allowed": True,
        "control_event_append_only": True,
        "approved_event_silent_update_allowed": False,
        "approved_event_reversal_required_for_change": True,
        "current_business_event_approval_allowed": False,
        "impact_preview_publish_allowed": False,
        "derived_rerun_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "business_execution_allowed": False,
        "raw_layer_write_allowed": False,
        "github_upload_allowed": False,
    }


def _public_repo_safety() -> dict[str, bool]:
    return {
        "aggregate_only": True,
        "raw_file_committed": False,
        "raw_filename_committed": False,
        "raw_hash_committed": False,
        "business_value_committed": False,
        "field_or_header_plaintext_committed": False,
        "project_or_customer_plaintext_committed": False,
        "private_runtime_committed": False,
        "credential_or_secret_committed": False,
        "zip_excel_pdf_private_csv_or_database_committed": False,
        "persistent_business_event_committed": False,
    }


def _render_html(groups: list[dict[str, Any]], templates: list[dict[str, Any]]) -> str:
    rows = []
    for group in groups:
        kind = group["manual_action_kind"]
        status = group["status"]
        search_text = " ".join(
            (
                group["visible_title"],
                ACTION_LABELS[kind],
                STATUS_LABELS[status],
                group["impact_summary"],
                group["next_step"],
            )
        )
        rows.append(
            """<tr data-pending-row data-group-id="{group_id}" data-kind="{kind}" data-status="{status}" data-search-text="{search}">
              <td><strong>{title}</strong><span class="subline">{group_id}</span></td>
              <td>{count}</td><td>{kind_label}</td><td>所有者或授权代理</td>
              <td><span class="status status-{status}">{status_label}</span></td>
              <td>{impact}</td><td>{next_step}</td>
              <td><button class="button button-secondary" type="button" data-select-group="{group_id}">选择</button></td>
            </tr>""".format(
                group_id=html.escape(group["group_id"]),
                kind=html.escape(kind),
                status=html.escape(status),
                search=html.escape(search_text),
                title=html.escape(group["visible_title"]),
                count=group["item_count"],
                kind_label=html.escape(ACTION_LABELS[kind]),
                status_label=html.escape(STATUS_LABELS[status]),
                impact=html.escape(group["impact_summary"]),
                next_step=html.escape(group["next_step"]),
            )
        )
    status_options = "".join(
        f'<option value="{html.escape(key)}">{html.escape(value)}</option>'
        for key, value in STATUS_LABELS.items()
    )
    kind_options = "".join(
        f'<option value="{html.escape(key)}">{html.escape(value)}</option>'
        for key, value in ACTION_LABELS.items()
    )
    return (
        """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>KMFA 待处理事项工作台</title>
  <style>
    :root { --navy:#102d4f; --blue:#1769aa; --blue-soft:#eaf3fb; --surface:#fff; --page:#f4f7f9; --line:#d7e0e7; --ink:#182634; --muted:#637282; --danger:#a92d25; --danger-soft:#fff0ee; --green:#16754b; --green-soft:#eaf7f1; --purple:#6b4ca1; --purple-soft:#f2edfa; }
    * { box-sizing:border-box; }
    body { margin:0; background:var(--page); color:var(--ink); font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Microsoft YaHei",Arial,sans-serif; font-size:14px; line-height:1.55; }
    button,input,select,textarea { font:inherit; letter-spacing:0; }
    button,a { -webkit-tap-highlight-color:transparent; }
    .app { min-height:100vh; display:grid; grid-template-rows:auto 1fr; }
    .topbar { display:flex; align-items:center; gap:18px; min-height:68px; padding:10px 24px; background:var(--navy); color:#fff; border-bottom:4px solid #2f81bd; }
    .brand { display:flex; align-items:center; gap:10px; min-width:210px; }
    .brand-mark { width:40px; height:40px; display:grid; place-items:center; border-radius:6px; background:#fff; color:var(--navy); font-weight:900; }
    .brand strong,.brand span { display:block; } .brand span { color:#c9dbee; font-size:12px; }
    .top-links { display:flex; gap:6px; flex-wrap:wrap; }
    .top-links a { color:#e5f0fa; text-decoration:none; border:1px solid rgba(255,255,255,.24); border-radius:6px; padding:7px 10px; }
    .top-links a:hover,.top-links a:focus-visible { background:rgba(255,255,255,.12); }
    .gate { margin-left:auto; text-align:right; } .gate span { display:block; color:#c9dbee; font-size:12px; } .gate strong { color:#fff; }
    main { min-width:0; width:min(1500px,100%); margin:0 auto; padding:22px 24px 40px; }
    .page-head { display:flex; align-items:flex-start; justify-content:space-between; gap:20px; margin-bottom:16px; }
    .page-head h1 { margin:0; color:var(--navy); font-size:27px; } .page-head p { margin:6px 0 0; color:var(--muted); }
    .boundary { max-width:430px; border-left:4px solid var(--danger); background:var(--danger-soft); padding:10px 12px; color:#6b2a25; }
    .metrics { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); border:1px solid var(--line); background:var(--surface); margin-bottom:16px; }
    .metric { min-width:0; padding:13px 15px; border-right:1px solid var(--line); } .metric:last-child { border-right:0; }
    .metric span { display:block; color:var(--muted); font-size:12px; } .metric strong { display:block; color:var(--navy); font-size:22px; margin-top:3px; }
    .panel { min-width:0; border:1px solid var(--line); border-radius:7px; background:var(--surface); }
    .panel-head { display:flex; align-items:center; justify-content:space-between; gap:14px; padding:14px 16px; border-bottom:1px solid var(--line); }
    .panel-head h2 { margin:0; color:var(--navy); font-size:18px; }
    .filters { display:grid; grid-template-columns:minmax(220px,1fr) 180px 180px auto; gap:8px; padding:12px 16px; border-bottom:1px solid var(--line); background:#f8fafb; }
    .control { display:block; width:100%; min-height:40px; border:1px solid #bfcbd5; border-radius:6px; background:#fff; color:var(--ink); padding:8px 10px; }
    .button { min-height:40px; border:1px solid var(--blue); border-radius:6px; padding:8px 12px; background:var(--blue); color:#fff; cursor:pointer; font-weight:700; }
    .button:hover,.button:focus-visible { background:#12568c; }
    .button-secondary { background:#fff; color:var(--blue); } .button-secondary:hover,.button-secondary:focus-visible { background:var(--blue-soft); }
    .button-muted { border-color:#aab7c2; background:#fff; color:#3e4e5b; }
    .table-wrap { max-width:100%; overflow:auto; }
    table { width:100%; min-width:1120px; border-collapse:collapse; }
    th,td { padding:11px 12px; border-bottom:1px solid #e8edf1; text-align:left; vertical-align:top; }
    th { position:sticky; top:0; background:#eef4f8; color:#36516a; font-size:12px; white-space:nowrap; }
    td strong { color:var(--navy); } .subline { display:block; margin-top:2px; color:var(--muted); font-size:11px; }
    tr[hidden] { display:none; }
    tr.selected td { background:#f1f7fc; }
    .status { display:inline-flex; border-radius:999px; padding:3px 8px; font-size:12px; font-weight:700; white-space:nowrap; }
    .status-pending_review,.status-comparison_incomplete,.status-source_not_ready { color:var(--danger); background:var(--danger-soft); }
    .status-evidence_ready { color:var(--green); background:var(--green-soft); }
    .status-accepted_global_only,.status-unknown_attribution { color:var(--purple); background:var(--purple-soft); }
    .workbench { display:grid; grid-template-columns:minmax(0,1.05fr) minmax(340px,.95fr); margin-top:16px; }
    .editor,.ledger { padding:17px; } .ledger { border-left:1px solid var(--line); background:#fbfcfd; }
    .editor h2,.ledger h2 { margin:0 0 12px; color:var(--navy); font-size:18px; }
    .field-grid { display:grid; grid-template-columns:1fr 1fr; gap:10px; }
    label { display:block; color:#3d5265; font-size:12px; font-weight:700; } label .control { margin-top:4px; font-size:14px; font-weight:400; }
    textarea.control { min-height:86px; resize:vertical; }
    .selected-summary { min-height:76px; margin:12px 0; padding:10px 12px; border-left:3px solid var(--blue); background:var(--blue-soft); color:#28455f; }
    .actions { display:flex; flex-wrap:wrap; gap:8px; }
    .feedback { min-height:44px; margin-top:12px; padding:10px 12px; border:1px solid var(--line); background:#fff; color:#31465a; }
    .event-count { display:flex; align-items:center; justify-content:space-between; border-bottom:1px solid var(--line); padding-bottom:10px; margin-bottom:10px; }
    .event-count strong { font-size:22px; color:var(--navy); }
    .event-log { display:grid; gap:8px; min-height:190px; max-height:330px; overflow:auto; }
    .event-row { border:1px solid var(--line); border-radius:6px; background:#fff; padding:10px; }
    .event-row strong,.event-row span { display:block; } .event-row span { margin-top:3px; color:var(--muted); font-size:12px; overflow-wrap:anywhere; }
    .empty { color:var(--muted); padding:28px 10px; text-align:center; border:1px dashed #c7d3dc; border-radius:6px; }
    .flow { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); margin-top:16px; border:1px solid var(--line); background:#fff; }
    .flow div { padding:12px 14px; border-right:1px solid var(--line); } .flow div:last-child { border-right:0; }
    .flow span { display:block; color:var(--muted); font-size:12px; } .flow strong { color:var(--navy); }
    footer { margin-top:14px; color:var(--muted); font-size:12px; }
    @media(max-width:980px) { .metrics { grid-template-columns:repeat(2,minmax(0,1fr)); } .metric:nth-child(2) { border-right:0; } .metric:nth-child(-n+2) { border-bottom:1px solid var(--line); } .filters { grid-template-columns:1fr 1fr; } .workbench { grid-template-columns:1fr; } .ledger { border-left:0; border-top:1px solid var(--line); } }
    @media(max-width:640px) { .topbar { align-items:flex-start; padding:10px 12px; flex-wrap:wrap; } .brand { min-width:0; } .gate { margin-left:0; text-align:left; width:100%; } main { padding:16px 12px 30px; } .page-head { display:block; } .boundary { margin-top:12px; max-width:none; } .metrics,.filters,.field-grid,.flow { grid-template-columns:1fr; } .metric { border-right:0; border-bottom:1px solid var(--line); } .metric:last-child { border-bottom:0; } .filters { padding:10px; } .panel-head { padding:12px; } .editor,.ledger { padding:13px; } .table-wrap { overflow:visible; padding:10px; } table,tbody { display:block; width:100%; min-width:0; } thead { position:absolute; width:1px; height:1px; padding:0; margin:-1px; overflow:hidden; clip:rect(0,0,0,0); white-space:nowrap; border:0; } tbody { display:grid; gap:8px; } tr[data-pending-row] { display:grid; grid-template-columns:minmax(0,1fr) auto 70px; gap:6px 10px; align-items:center; padding:10px; border:1px solid var(--line); border-radius:6px; background:#fff; } tr[data-pending-row][hidden] { display:none; } tr[data-pending-row].selected { background:#f1f7fc; } tr[data-pending-row] td { min-width:0; padding:0; border:0; background:transparent; } tr[data-pending-row] td:first-child { grid-column:1; grid-row:1 / 3; } tr[data-pending-row] td:nth-child(2) { grid-column:2; grid-row:1; white-space:nowrap; } tr[data-pending-row] td:nth-child(2)::before { content:"数量 "; color:var(--muted); font-size:11px; } tr[data-pending-row] td:nth-child(3) { grid-column:2; grid-row:2; } tr[data-pending-row] td:nth-child(4),tr[data-pending-row] td:nth-child(6),tr[data-pending-row] td:nth-child(7) { display:none; } tr[data-pending-row] td:nth-child(5) { grid-column:1 / 3; grid-row:3; } tr[data-pending-row] td:last-child { grid-column:3; grid-row:1 / 4; } }
  </style>
</head>
<body>
  <div class="app">
    <header class="topbar">
      <div class="brand"><div class="brand-mark">KM</div><div><strong>KMFA</strong><span>经营分析系统</span></div></div>
      <nav class="top-links" aria-label="返回当前页面"><a data-return-link="home" href="__HOME_HREF__">经营首页</a><a data-return-link="source" href="__SOURCE_HREF__">数据源检查</a><a data-return-link="project" href="__PROJECT_HREF__">项目成本</a></nav>
      <div class="gate"><span>当前可信状态</span><strong>Q4 / D · NO_GO</strong></div>
    </header>
    <main>
      <section class="page-head"><div><h1>待处理事项</h1><p>按责任、状态、影响和下一步形成公开安全复核入口。</p></div><div class="boundary"><strong>当前仅生成候选事件。</strong> 不写原始数据，不批准业务结论，不执行影响预览或重跑。</div></section>
      <section class="metrics" aria-label="当前待处理概况"><div class="metric"><span>待处理分组</span><strong>6</strong></div><div class="metric"><span>非零差异</span><strong>9</strong></div><div class="metric"><span>未知项目归属</span><strong>4</strong></div><div class="metric"><span>当前会话候选</span><strong id="session-event-count">0</strong></div></section>
      <section class="panel">
        <div class="panel-head"><h2>待处理事项列表</h2><span id="visible-count">6 项</span></div>
        <div class="filters"><input class="control" type="search" data-pending-search aria-label="搜索待处理事项" placeholder="搜索事项、影响或下一步"><select class="control" data-kind-filter aria-label="按处理类型筛选"><option value="">全部处理类型</option>__KIND_OPTIONS__</select><select class="control" data-status-filter aria-label="按状态筛选"><option value="">全部状态</option>__STATUS_OPTIONS__</select><button class="button button-muted" type="button" data-reset-filters>重置</button></div>
        <div class="table-wrap"><table><thead><tr><th>事项</th><th>数量</th><th>处理类型</th><th>处理人</th><th>状态</th><th>影响</th><th>下一步</th><th>操作</th></tr></thead><tbody>__ROWS__</tbody></table></div>
      </section>
      <section class="panel workbench">
        <div class="editor"><h2>候选事件</h2><div class="selected-summary" id="selected-summary">请选择一个待处理分组。</div><div class="field-grid"><label>处理类型<select class="control" id="event-kind">__KIND_OPTIONS__</select></label><label>处理人<span class="control" id="event-actor" role="status">所有者或授权代理</span></label></div><label style="margin-top:10px">原因与备注<textarea class="control" id="event-reason" placeholder="填写公开安全原因，不输入业务金额、原始字段或明细"></textarea></label><label style="margin-top:10px">影响范围<span class="control" id="event-impact" role="status">待选择事项</span></label><div class="actions" style="margin-top:12px"><button class="button" type="button" data-create-event>生成候选事件</button><button class="button button-secondary" type="button" data-reverse-approved>追加反向事件候选</button></div><div class="feedback" id="event-feedback" aria-live="polite">候选事件只存在于当前页面内存，刷新页面后清空。</div></div>
        <div class="ledger"><h2>当前会话事件</h2><div class="event-count"><span>append-only 草案</span><strong id="ledger-count">0</strong></div><div class="event-log" id="event-log"><div class="empty">尚未生成候选事件</div></div></div>
      </section>
      <section class="flow" aria-label="阶段边界"><div><span>当前 phase</span><strong>S12-P1 · 候选事件</strong></div><div><span>后续独立 phase</span><strong>S12-P2 · 影响预览</strong></div><div><span>后续独立 phase</span><strong>S12-P3 · 派生重跑</strong></div></section>
      <footer>公开页面只含聚合计数、状态与候选事件模板，不含原始文件身份、表头、业务金额、项目或客户明文。</footer>
    </main>
  </div>
  <script>
    const groups=__GROUP_JSON__;
    const templates=__TEMPLATE_JSON__;
    const kindLabels=__KIND_LABELS__;
    const state={selectedGroupId:null,events:[],sequence:0};
    const rows=Array.from(document.querySelectorAll('[data-pending-row]'));
    const search=document.querySelector('[data-pending-search]');
    const kindFilter=document.querySelector('[data-kind-filter]');
    const statusFilter=document.querySelector('[data-status-filter]');
    const selectedSummary=document.getElementById('selected-summary');
    const eventKind=document.getElementById('event-kind');
    const eventReason=document.getElementById('event-reason');
    const eventImpact=document.getElementById('event-impact');
    const feedback=document.getElementById('event-feedback');
    const eventLog=document.getElementById('event-log');
    function record(action,message){state.sequence+=1;document.body.dataset.lastAction=`${action}:${state.sequence}`;feedback.textContent=message;}
    function applyFilters(){const term=search.value.trim().toLowerCase();let visible=0;rows.forEach(row=>{const show=(!term||row.dataset.searchText.toLowerCase().includes(term))&&(!kindFilter.value||row.dataset.kind===kindFilter.value)&&(!statusFilter.value||row.dataset.status===statusFilter.value);row.hidden=!show;if(show)visible+=1;});document.getElementById('visible-count').textContent=`${visible} 项`;document.body.dataset.visibleRows=String(visible);record('filter',`筛选完成，当前显示 ${visible} 项。`);}
    function resetFilters(){search.value='';kindFilter.value='';statusFilter.value='';applyFilters();record('reset','筛选条件已重置。');}
    function selectGroup(groupId){const group=groups.find(item=>item.group_id===groupId);if(!group)return;state.selectedGroupId=groupId;rows.forEach(row=>row.classList.toggle('selected',row.dataset.groupId===groupId));eventKind.value=group.manual_action_kind;eventImpact.textContent=group.impact_summary;selectedSummary.textContent=`${group.visible_title}｜${group.item_count} 项｜${group.next_step}`;document.body.dataset.selectedGroup=groupId;record('select',`已选择 ${group.visible_title}。`);}
    function renderEvents(){document.getElementById('session-event-count').textContent=String(state.events.length);document.getElementById('ledger-count').textContent=String(state.events.length);document.body.dataset.sessionEventCount=String(state.events.length);eventLog.replaceChildren();if(!state.events.length){const empty=document.createElement('div');empty.className='empty';empty.textContent='尚未生成候选事件';eventLog.appendChild(empty);return;}state.events.slice().reverse().forEach(event=>{const row=document.createElement('div');row.className='event-row';const title=document.createElement('strong');title.textContent=`${event.event_id}｜${kindLabels[event.manual_action_kind]||'反向事件'}`;const detail=document.createElement('span');detail.textContent=`${event.event_time}｜${event.event_version}｜${event.reason}`;row.append(title,detail);eventLog.appendChild(row);});}
    function createCandidate(){if(!state.selectedGroupId){record('blocked','请先选择待处理事项。');return;}const reason=eventReason.value.trim();if(!reason){record('blocked','请填写公开安全原因。');return;}const template=templates.find(item=>item.manual_action_kind===eventKind.value);const group=groups.find(item=>item.group_id===state.selectedGroupId);const next=state.events.length+1;state.events.push({event_id:`SESSION-EVT-${String(next).padStart(3,'0')}`,manual_action_kind:template.manual_action_kind,actor_ref:template.actor_ref,event_time:new Date().toISOString(),reason,impact_scope:group.impact_summary,event_version:`${template.event_version}-S${next}`,approval_state:'draft',append_only:true,session_candidate_only:true,silent_update_allowed:false});renderEvents();record('candidate',`已生成 ${kindLabels[template.manual_action_kind]}候选事件，仅当前会话可见。`);}
    function createReverseCandidate(){const next=state.events.length+1;state.events.push({event_id:`SESSION-EVT-${String(next).padStart(3,'0')}`,manual_action_kind:'reverse_event',actor_ref:'actor_ref://owner_or_authorized_delegate/session-only',event_time:new Date().toISOString(),reason:'已批准事件变更只能追加反向事件候选',impact_scope:'historical_approved_event_policy_fixture',event_version:`SESSION-REVERSAL-S12P1-001.${String(next).padStart(3,'0')}`,approval_state:'draft',append_only:true,session_candidate_only:true,silent_update_allowed:false,reverses_event_id:'HISTORICAL-APPROVED-FIXTURE'});renderEvents();record('reverse','已追加反向事件候选；原已批准记录未被改写。');}
    search.addEventListener('input',applyFilters);kindFilter.addEventListener('change',applyFilters);statusFilter.addEventListener('change',applyFilters);document.querySelector('[data-reset-filters]').addEventListener('click',resetFilters);document.querySelectorAll('[data-select-group]').forEach(button=>button.addEventListener('click',()=>selectGroup(button.dataset.selectGroup)));document.querySelector('[data-create-event]').addEventListener('click',createCandidate);document.querySelector('[data-reverse-approved]').addEventListener('click',createReverseCandidate);eventKind.addEventListener('change',()=>record('kind',`处理类型已切换为 ${kindLabels[eventKind.value]}。`));renderEvents();document.body.dataset.uiReady='true';record('ready','工作台已就绪；所有候选事件仅保留在当前会话。');
  </script>
</body>
</html>"""
        .replace("__HOME_HREF__", html.escape(HOME_HREF))
        .replace("__SOURCE_HREF__", html.escape(SOURCE_HREF))
        .replace("__PROJECT_HREF__", html.escape(PROJECT_HREF))
        .replace("__ROWS__", "".join(rows))
        .replace("__KIND_OPTIONS__", kind_options)
        .replace("__STATUS_OPTIONS__", status_options)
        .replace("__GROUP_JSON__", json.dumps(groups, ensure_ascii=False, separators=(",", ":")))
        .replace("__TEMPLATE_JSON__", json.dumps(templates, ensure_ascii=False, separators=(",", ":")))
        .replace("__KIND_LABELS__", json.dumps(ACTION_LABELS, ensure_ascii=False, separators=(",", ":")))
    )


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
    kind_filter_checks: list[dict[str, Any]] = []
    status_filter_checks: list[dict[str, Any]] = []
    row_selection_checks: list[dict[str, Any]] = []
    candidate_event_checks: list[dict[str, Any]] = []
    reverse_event_checks: list[dict[str, Any]] = []
    reload_reset_checks: list[dict[str, Any]] = []
    http_checks: list[dict[str, Any]] = []
    navigation_checks: list[dict[str, Any]] = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True,
                executable_path=s11_home._chromium_path(),
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
                    and s11_home._is_actionable_console_error(
                        f"{msg.text} {msg.location.get('url', '')}"
                    )
                    else None,
                )
                page.goto(url, wait_until="networkidle")
                page.wait_for_function("document.body.dataset.uiReady === 'true'")
                no_overflow = page.evaluate(
                    "document.documentElement.scrollWidth <= window.innerWidth + 1"
                )
                no_go_visible = page.get_by_text("Q4 / D · NO_GO", exact=True).is_visible()
                viewport_checks.append(
                    {
                        "mode": mode,
                        "passed": no_overflow and no_go_visible and not console_errors,
                        "no_horizontal_overflow": no_overflow,
                        "no_go_visible": no_go_visible,
                        "console_error_count": len(console_errors),
                    }
                )

                page.locator("[data-pending-search]").fill("归属未知")
                search_ok = page.locator("tbody tr[data-pending-row]:visible").count() == 1
                search_checks.append({"mode": mode, "passed": search_ok})
                page.locator("[data-reset-filters]").click()

                page.locator("[data-kind-filter]").select_option("project_matching")
                kind_ok = page.locator("tbody tr[data-pending-row]:visible").count() == 1
                kind_filter_checks.append({"mode": mode, "passed": kind_ok})
                page.locator("[data-reset-filters]").click()

                page.locator("[data-status-filter]").select_option("unknown_attribution")
                status_ok = page.locator("tbody tr[data-pending-row]:visible").count() == 1
                status_filter_checks.append({"mode": mode, "passed": status_ok})
                page.locator("[data-reset-filters]").click()

                page.locator('[data-select-group="PEND-S12P1-005"]').click()
                selected_ok = page.locator("body").get_attribute("data-selected-group") == "PEND-S12P1-005"
                row_selection_checks.append({"mode": mode, "passed": selected_ok})
                page.locator("#event-reason").fill("公开安全项目匹配复核候选")
                page.locator("[data-create-event]").click()
                candidate_ok = page.locator("body").get_attribute("data-session-event-count") == "1"
                candidate_event_checks.append({"mode": mode, "passed": candidate_ok})
                page.locator("[data-reverse-approved]").click()
                reverse_ok = page.locator("body").get_attribute("data-session-event-count") == "2"
                reverse_event_checks.append({"mode": mode, "passed": reverse_ok})

                page.reload(wait_until="networkidle")
                page.wait_for_function("document.body.dataset.uiReady === 'true'")
                reset_ok = page.locator("body").get_attribute("data-session-event-count") == "0"
                reload_reset_checks.append({"mode": mode, "passed": reset_ok})
                page.screenshot(
                    path=str(PRIVATE_SCREENSHOT_DIR / f"pending_actions_{mode}.png"),
                    full_page=True,
                )
                page.close()

            request = playwright.request.new_context()
            for link_id, href, marker in RETURN_LINKS:
                target = urljoin(url, href)
                response = request.get(target)
                http_checks.append(
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
                navigation_checks.append(
                    {
                        "link_id": link_id,
                        "passed": marker in page.locator("body").inner_text(),
                    }
                )
                page.close()
            request.dispose()
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
    collections = (
        viewport_checks,
        search_checks,
        kind_filter_checks,
        status_filter_checks,
        row_selection_checks,
        candidate_event_checks,
        reverse_event_checks,
        reload_reset_checks,
        http_checks,
        navigation_checks,
    )
    return {
        "schema_version": "kmfa.v014.s12_p1.pending_actions_browser.v1",
        "status": "PASS" if all(item.get("passed") for rows in collections for item in rows) else "FAIL",
        "viewport_checks": viewport_checks,
        "search_checks": search_checks,
        "kind_filter_checks": kind_filter_checks,
        "status_filter_checks": status_filter_checks,
        "row_selection_checks": row_selection_checks,
        "candidate_event_checks": candidate_event_checks,
        "reverse_event_checks": reverse_event_checks,
        "reload_reset_checks": reload_reset_checks,
        "return_link_http_checks": http_checks,
        "actual_navigation_checks": navigation_checks,
    }


def _run_browser_review() -> dict[str, Any]:
    result = subprocess.run(
        [str(s11_home._audit_python()), str(Path(__file__).resolve()), "--browser-worker"],
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
        "kind_filter_check_count": len(browser["kind_filter_checks"]),
        "status_filter_check_count": len(browser["status_filter_checks"]),
        "row_selection_check_count": len(browser["row_selection_checks"]),
        "candidate_event_check_count": len(browser["candidate_event_checks"]),
        "reverse_event_check_count": len(browser["reverse_event_checks"]),
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
    return f"""# v0.1.4 S12-P1 待处理事项与人工事件

## 结论

- 当前状态：`Q4 / D / NO_GO`。
- 待处理分组：`{summary['pending_action_group_count']}`；事件模板：`{summary['manual_event_template_count']}`。
- 当前已批准业务事件：`0`；页面只生成 session-only 候选草案。
- 旧批准/反向事件链仅作为不变式 fixture，未应用当前业务变更。

## 当前状态

- 最终差异接受 / 非零 / 零差异 / 未完成：`3 / 9 / 2 / 1`。
- 项目归属 unknown / 数据源检查行：`4 / 13`。
- 浏览器 viewports / 搜索 / 类型筛选 / 状态筛选：`{browser['viewport_check_count']} / {browser['search_check_count']} / {browser['kind_filter_check_count']} / {browser['status_filter_check_count']}`。
- session 候选 / 反向候选 / 刷新清空：`{browser['candidate_event_check_count']} / {browser['reverse_event_check_count']} / {browser['reload_reset_check_count']}`。

## 边界

- S12-P2 影响预览、S12-P3 重跑、Stage 12 review、GitHub upload、app reinstall、正式报告和业务执行均未执行。
- 原始数据前后及跨 Stage 11 快照一致，无持久 raw 差异；本 phase 不触发差异报告。
"""


def _render_test_results(final_validation: bool) -> str:
    status = "PASS" if final_validation else "PENDING"
    return f"""# v0.1.4 S12-P1 测试结果

- focused tests：`{status}`
- strict validator：`{status}`
- desktop/mobile browser：`{status}`
- governance/no-float/no-omission/safety scan：`{status}`
- raw before/after/cross-phase：`PASS`

最终命令：

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest -v KMFA.tests.test_v014_s12_p1_post_remediation_pending_actions`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s12_p1_post_remediation_pending_actions.py --require-private-evidence --require-browser-evidence --require-final-evidence`
"""


def _render_risk_register() -> str:
    return """# v0.1.4 S12-P1 风险登记

| 风险 | 控制 | 状态 |
|---|---|---|
| 将旧 pending=12 当成当前状态 | 只引用 current Stage 11 `3/9/2/1` | controlled |
| 虚构项目归属 | 4 个项目槽位保持 unknown/null | controlled |
| 候选事件被误解为已批准 | session-only、刷新清空、approved count=0 | controlled |
| 静默改写已批准事件 | 仅允许追加反向候选，legacy chain 只作 fixture | controlled |
| 提前执行影响预览或重跑 | 页面与 manifest 均无 P2/P3 控件或执行 | controlled |
| raw/private 泄漏 | raw 四向快照、ignored private evidence、提交前安全扫描 | controlled |
"""


def _render_rollback() -> str:
    return """# v0.1.4 S12-P1 回滚方案

1. 回退本 phase 本地 commit。
2. 删除本 phase public-safe 派生产物并重新生成。
3. 删除 ignored private browser/raw 证据。
4. 不修改旧 S12-P1/P2/P3 历史证据，不触碰原始数据目录。
"""


def _private_report(summary: dict[str, Any], browser: dict[str, Any]) -> str:
    return f"""# S12-P1 私有验证

- raw files: {summary['raw_source_file_count']}
- before = after = Stage 11 prior = current: true
- browser status: PASS
- viewports: {browser['viewport_check_count']}
- console errors: {browser['console_error_count']}
- horizontal overflow: {browser['horizontal_overflow_count']}
- 结论：原始数据未变化，无需生成本 phase 差异报告。
"""


def _governance_rows(generated_at: str, manifest: dict[str, Any]) -> None:
    evidence_ref = MANIFEST_PATH.as_posix()
    changed_files = [
        SUMMARY_PATH.as_posix(),
        MANIFEST_PATH.as_posix(),
        GROUPS_PATH.as_posix(),
        EVENT_TEMPLATES_PATH.as_posix(),
        GO_NO_GO_PATH.as_posix(),
        HTML_PATH.as_posix(),
        REPORT_PATH.as_posix(),
        TEST_RESULTS_PATH.as_posix(),
        RISK_REGISTER_PATH.as_posix(),
        ROLLBACK_PATH.as_posix(),
        METADATA_SUMMARY_PATH.as_posix(),
        METADATA_MANIFEST_PATH.as_posix(),
        METADATA_GROUPS_PATH.as_posix(),
        METADATA_EVENT_TEMPLATES_PATH.as_posix(),
        METADATA_GO_NO_GO_PATH.as_posix(),
        Path(__file__).relative_to(Path.cwd()).as_posix(),
        "KMFA/tools/check_v014_s12_p1_post_remediation_pending_actions.py",
        "KMFA/tests/test_v014_s12_p1_post_remediation_pending_actions.py",
    ]
    _upsert_jsonl(
        DEVELOPMENT_EVENTS_PATH,
        {
            "event_id": "DEV-KMFA-20260711-V014-S12-P1-POST-REMEDIATION-PENDING-ACTIONS",
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
            "pending_action_group_count": manifest["summary"]["pending_action_group_count"],
            "current_approved_business_event_count": 0,
            "raw_business_data_committed": False,
            "github_upload_performed": False,
            "app_reinstall_performed": False,
            "business_execution_performed": False,
            "evidence_ref": evidence_ref,
            "files_changed": changed_files,
            "result_commit": "PENDING",
        },
    )
    _upsert_jsonl(
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
    _upsert_jsonl(
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
            "name": "v0.1.4 S12-P1 post-remediation pending actions",
            "phase_goal": "public-safe pending actions and append-only session event candidates",
            "status": STATUS,
            "fact_level": "EXTRACTED",
            "derived_percent": 33.33,
            "estimated_task_units": 9,
            "completed_task_units": 3,
            "task_count": 3,
            "raw_data_committed": False,
            "evidence_ref": evidence_ref,
            "updated_at": generated_at[:10],
        },
    )


def generate(final_validation: bool = False) -> dict[str, Any]:
    generated_at = datetime.now().astimezone().replace(microsecond=0).isoformat()
    raw_before = s11_project._raw_snapshot("before_v014_s12_p1_post_remediation_pending_actions")
    _write_json(PRIVATE_RAW_BEFORE_PATH, raw_before)
    dependency = _load_stage11_dependency()
    contract = _load_contract()
    dependency_summary = dependency["summary"]
    groups = _pending_action_groups(dependency_summary)
    templates = _manual_event_templates()
    _write_text(HTML_PATH, _render_html(groups, templates))

    baseline_audit = s11_home._run_html_audit(V14_HTML_ROOT, PRIVATE_BASELINE_AUDIT_PATH)
    current_audit = s11_home._run_html_audit(HTML_DIR, PRIVATE_CURRENT_AUDIT_PATH)
    browser_payload = _run_browser_review()
    _write_json(PRIVATE_BROWSER_PATH, browser_payload)
    browser = _browser_summary(baseline_audit, current_audit, browser_payload)

    raw_after = s11_project._raw_snapshot("after_v014_s12_p1_post_remediation_pending_actions")
    prior_raw = json.loads(s11_review.PRIVATE_RAW_AFTER_PATH.read_text(encoding="utf-8"))
    current_raw = s11_project._raw_snapshot("current_v014_s12_p1_post_remediation_pending_actions")
    normalize = s11_project._normalize_raw
    raw_exact = normalize(raw_before) == normalize(raw_after)
    raw_cross = normalize(raw_before) == normalize(prior_raw) == normalize(current_raw)
    if not raw_exact or not raw_cross:
        raise RuntimeError("raw source changed during S12-P1 generation")
    _write_json(PRIVATE_RAW_AFTER_PATH, raw_after)

    summary = {
        "schema_version": "kmfa.v014.s12_p1.pending_actions_summary.v1",
        "record_type": "v014_s12_p1_post_remediation_pending_actions_summary",
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
        "open_final_difference_accepted_count": dependency_summary["open_final_difference_accepted_count"],
        "nonzero_delta_reconciliation_count": dependency_summary["nonzero_delta_reconciliation_count"],
        "zero_delta_reconciliation_count": dependency_summary["zero_delta_reconciliation_count"],
        "incomplete_reconciliation_count": dependency_summary["incomplete_reconciliation_count"],
        "project_specific_unknown_allocation_count": dependency_summary["project_specific_unknown_allocation_count"],
        "source_check_matrix_row_count": dependency_summary["source_check_matrix_row_count"],
        "hard_block_count": dependency_summary["hard_block_count"],
        "pending_action_group_count": len(groups),
        "manual_event_template_count": len(templates),
        "manual_action_kind_count": len({row["manual_action_kind"] for row in templates}),
        "current_approved_business_event_count": 0,
        "current_persistent_business_event_count": 0,
        "historical_approved_policy_fixture_count": contract["legacy_approved_event_count"],
        "historical_reverse_policy_fixture_count": contract["legacy_reverse_event_count"],
        "raw_source_file_count": raw_before["file_count"],
        "raw_snapshot_exact_match": raw_exact,
        "raw_cross_phase_snapshot_exact_match": raw_cross,
        "formal_report_count": 0,
        "business_decision_basis_count": 0,
        "s12_p2_performed": False,
        "s12_p3_performed": False,
        "stage12_review_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }
    fixture = {
        "schema_version": "kmfa.v014.s12_p1.approved_event_reversal_policy_fixture.v1",
        "historical_approved_event_count": contract["legacy_approved_event_count"],
        "historical_reverse_event_count": contract["legacy_reverse_event_count"],
        "reverse_chain_validated": contract["legacy_reverse_chain_validated"],
        "current_business_resolution_applied": False,
        "approved_event_silent_update_allowed": False,
        "approved_event_reversal_required_for_change": True,
        "fixture_only": True,
        "source_ref": legacy_s12.MANIFEST_PATH.as_posix(),
    }
    go_no_go = {
        "schema_version": "kmfa.v014.s12_p1.pending_actions_go_no_go.v1",
        "phase_id": PHASE_ID,
        "decision": DECISION,
        "s12_p1_validated": True,
        "candidate_event_creation_allowed": True,
        "current_business_event_approval_allowed": False,
        "impact_preview_publish_allowed": False,
        "derived_rerun_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "s12_p2_performed": False,
        "s12_p3_performed": False,
        "stage12_review_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }
    manifest = {
        "schema_version": "kmfa.v014.s12_p1.pending_actions_manifest.v1",
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
        "stage11_post_remediation_review_dependency_validated": True,
        "taskpack_contract": contract,
        "pending_action_groups": groups,
        "manual_event_templates": templates,
        "approved_event_reversal_policy_fixture": fixture,
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
        "next_phase": "S12-P2",
        "next_required_step": "Execute S12-P2 impact preview as a separate run after S12-P1 local validation and commit.",
        "git": {
            "branch": _git_output(["branch", "--show-current"]),
            "remote": _git_output(["remote", "get-url", "origin"]),
            "head": _git_output(["rev-parse", "HEAD"]),
        },
    }
    groups_payload = {
        "schema_version": "kmfa.v014.s12_p1.pending_action_groups.v1",
        "phase_id": PHASE_ID,
        "group_count": len(groups),
        "count_semantics": "groups overlap and must not be added into a business total",
        "groups": groups,
    }
    templates_payload = {
        "schema_version": "kmfa.v014.s12_p1.manual_event_templates.v1",
        "phase_id": PHASE_ID,
        "template_count": len(templates),
        "templates": templates,
        "approved_event_reversal_policy_fixture": fixture,
    }
    for path, value in (
        (SUMMARY_PATH, summary),
        (MANIFEST_PATH, manifest),
        (GROUPS_PATH, groups_payload),
        (EVENT_TEMPLATES_PATH, templates_payload),
        (GO_NO_GO_PATH, go_no_go),
        (METADATA_SUMMARY_PATH, summary),
        (METADATA_MANIFEST_PATH, manifest),
        (METADATA_GROUPS_PATH, groups_payload),
        (METADATA_EVENT_TEMPLATES_PATH, templates_payload),
        (METADATA_GO_NO_GO_PATH, go_no_go),
    ):
        _write_json(path, value)
    _write_text(REPORT_PATH, _render_report(manifest))
    _write_text(TEST_RESULTS_PATH, _render_test_results(final_validation))
    _write_text(RISK_REGISTER_PATH, _render_risk_register())
    _write_text(ROLLBACK_PATH, _render_rollback())
    _write_text(PRIVATE_VALIDATION_REPORT_PATH, _private_report(summary, browser))
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
        "S12-P1 post-remediation pending actions: "
        f"groups={summary['pending_action_group_count']} templates={summary['manual_event_template_count']} "
        f"approved={summary['current_approved_business_event_count']} grade={summary['current_report_grade']} "
        f"decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
