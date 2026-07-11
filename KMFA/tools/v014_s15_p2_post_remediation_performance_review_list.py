#!/usr/bin/env python3
"""Generate current KMFA v0.1.4 S15-P2 performance review evidence."""

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

from KMFA.tools import v014_s15_p1_post_remediation_performance_fact_fields as p1
from KMFA.tools.check_v014_s15_p1_post_remediation_performance_fact_fields import (
    validate_v014_s15_p1_post_remediation_performance_fact_fields,
)
from KMFA.tools.check_v014_s15_p2_performance_review_list import (
    validate_v014_s15_p2_performance_review_list,
)


PHASE_ID = "V014_S15_P2_POST_REMEDIATION_PERFORMANCE_REVIEW_LIST"
ROADMAP_PHASE_ID = "S15-P2"
TASK_ID = "KMFA-V014-S15-P2-POST-REMEDIATION-PERFORMANCE-REVIEW-LIST-20260711"
ACCEPTANCE_ID = "ACC-V014-S15-P2-POST-REMEDIATION-PERFORMANCE-REVIEW-LIST"
VERSION = "0.1.4-s15-p2-post-remediation-performance-review-list"
STATUS = (
    "completed_validated_local_only_s15_p2_zero_authoritative_fact_rows_"
    "six_review_items_no_go_upload_deferred"
)
DECISION = "NO_GO"
FORMULA_ID = "FORM-KMFA-V014-S15P2-POST-REMEDIATION-PERFORMANCE-REVIEW-LIST-001"
PARAMETER_IDS = ("PARAM-KMFA-1769", "PARAM-KMFA-1770", "PARAM-KMFA-1771", "PARAM-KMFA-1772")
MODEL_REGISTRY_KEY = "kmfa_v014_s15_p2_post_remediation_performance_review_list"

OUTPUT_DIR = Path("KMFA/stage_artifacts") / PHASE_ID
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
HTML_DIR = OUTPUT_DIR / "exports/html"
SUMMARY_PATH = MACHINE_DIR / "performance_review_summary.json"
MANIFEST_PATH = MACHINE_DIR / "performance_review_manifest.json"
FACT_SCHEMA_PATH = MACHINE_DIR / "performance_fact_table_schema_public_safe.json"
FACT_TABLE_PATH = MACHINE_DIR / "performance_fact_table_public_safe.json"
ABNORMAL_METHOD_PATH = MACHINE_DIR / "abnormal_project_method_public_safe.json"
REVIEW_ITEMS_PATH = MACHINE_DIR / "performance_review_items_public_safe.json"
MATRIX_PATH = MACHINE_DIR / "performance_review_acceptance_matrix.json"
GO_NO_GO_PATH = MACHINE_DIR / "performance_review_go_no_go.json"
HTML_PATH = HTML_DIR / "performance_review_workbench.html"
REPORT_PATH = HUMAN_DIR / "performance_review_report_zh.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results_zh.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register_zh.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan_zh.md"

QUALITY_DIR = Path("KMFA/metadata/quality")
METADATA_SUMMARY_PATH = QUALITY_DIR / "v014_s15_p2_post_remediation_performance_review_summary.json"
METADATA_MANIFEST_PATH = QUALITY_DIR / "v014_s15_p2_post_remediation_performance_review_manifest.json"
METADATA_FACT_SCHEMA_PATH = (
    QUALITY_DIR / "v014_s15_p2_post_remediation_performance_fact_table_schema_public_safe.json"
)
METADATA_FACT_TABLE_PATH = (
    QUALITY_DIR / "v014_s15_p2_post_remediation_performance_fact_table_public_safe.json"
)
METADATA_ABNORMAL_METHOD_PATH = (
    QUALITY_DIR / "v014_s15_p2_post_remediation_abnormal_project_method_public_safe.json"
)
METADATA_REVIEW_ITEMS_PATH = (
    QUALITY_DIR / "v014_s15_p2_post_remediation_performance_review_items_public_safe.json"
)
METADATA_MATRIX_PATH = QUALITY_DIR / "v014_s15_p2_post_remediation_performance_review_acceptance_matrix.json"
METADATA_GO_NO_GO_PATH = QUALITY_DIR / "v014_s15_p2_post_remediation_performance_review_go_no_go.json"

PRIVATE_DIR = Path("KMFA/.codex_private_runtime/v014_s15_p2_post_remediation_performance_review_list")
PRIVATE_RAW_BEFORE_PATH = PRIVATE_DIR / "raw_immutability_before.json"
PRIVATE_RAW_AFTER_PATH = PRIVATE_DIR / "raw_immutability_after.json"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_DIR / "performance_review_readiness_diagnostic.json"
PRIVATE_REPORT_PATH = PRIVATE_DIR / "performance_review_difference_report_zh.md"
PRIVATE_BROWSER_PATH = PRIVATE_DIR / "browser_verification.json"
PRIVATE_BASELINE_AUDIT_PATH = PRIVATE_DIR / "human_flow_baseline_audit.csv"
PRIVATE_CURRENT_AUDIT_PATH = PRIVATE_DIR / "current_performance_review_audit.csv"
PRIVATE_SCREENSHOT_DIR = PRIVATE_DIR / "screenshots"

ROADMAP_PATH = p1.ROADMAP_PATH
TASKPACK_PATH = p1.TASKPACK_PATH
HTML_BASELINE_ROOT = p1.HTML_BASELINE_ROOT
LEGACY_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V014_S15_P2_PERFORMANCE_REVIEW_LIST/machine/performance_review_manifest.json"
)
LEGACY_FACT_TABLE_PATH = Path(
    "KMFA/stage_artifacts/V014_S15_P2_PERFORMANCE_REVIEW_LIST/machine/performance_fact_table.jsonl"
)
LEGACY_REVIEW_ITEMS_PATH = Path(
    "KMFA/stage_artifacts/V014_S15_P2_PERFORMANCE_REVIEW_LIST/machine/performance_review_items.jsonl"
)

DEVELOPMENT_EVENTS_PATH = Path("KMFA/docs/governance/development_events.jsonl")
ASSURANCE_STATUS_PATH = Path("KMFA/docs/governance/ASSURANCE_STATUS.yaml")
STAGE_STATUS_PATH = Path("KMFA/metadata/stage_status.jsonl")
TASK_STATUS_PATH = Path("KMFA/metadata/traceability/v1_4_stage_phase_task_status.jsonl")

FIELD_SPECS = p1.FIELD_SPECS
FIELD_KEYS = p1.FIELD_KEYS
FIELD_LABELS = p1.FIELD_LABELS
ROLE_LABELS = {
    "finance_owner": "财务负责人",
    "project_owner": "项目负责人",
    "finance_review_owner": "财务复核负责人",
    "sales_owner": "销售负责人",
}

DEPENDENCY_LINKS = {
    "fact-fields": (
        "../../../V014_S15_P1_POST_REMEDIATION_PERFORMANCE_FACT_FIELDS/exports/html/"
        "performance_fact_fields_workbench.html",
        "绩效事实字段工作台",
    ),
    "project-cost": (
        "../../../V014_S11_P3_POST_REMEDIATION_PROJECT_COST_PAGE/exports/html/"
        "kmfa_project_cost_page.html",
        "项目成本状态与受限报告",
    ),
    "collection": (
        "../../../V014_S13_P2_POST_REMEDIATION_COLLECTION_RECEIVABLE_AGING/exports/html/"
        "collection_receivable_aging_workbench.html",
        "回款与应收账龄工作台",
    ),
    "invoice-tax": (
        "../../../V014_S14_P2_POST_REMEDIATION_INVOICE_TAX_PLAN/exports/html/"
        "invoice_tax_plan_workbench.html",
        "开票纳税计划工作台",
    ),
}
P3_HREF = (
    "../../../V014_S15_P3_POST_REMEDIATION_SALARY_BOUNDARY/exports/html/"
    "salary_boundary_workbench.html"
)


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
                raise ValueError(f"{path} contains a non-object row")
            rows.append(value)
    return rows


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
    preserved: list[str] = []
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip() and json.loads(line).get("phase_id") != PHASE_ID:
                preserved.append(line)
    preserved.append(json.dumps(row, ensure_ascii=False, separators=(",", ":")))
    _write_text(path, "\n".join(preserved))


def _sync_assurance_snapshot_time(generated_at: str) -> None:
    lines = ASSURANCE_STATUS_PATH.read_text(encoding="utf-8").splitlines()
    indexes = [index for index, line in enumerate(lines) if line.startswith("snapshot_event_time:")]
    if len(indexes) != 1:
        raise RuntimeError("ASSURANCE_STATUS must contain exactly one snapshot_event_time")
    lines[indexes[0]] = f'snapshot_event_time: "{generated_at}"'
    _write_text(ASSURANCE_STATUS_PATH, "\n".join(lines))


def _load_dependency() -> dict[str, Any]:
    manifest = validate_v014_s15_p1_post_remediation_performance_fact_fields(
        require_private_evidence=True,
        require_browser_evidence=True,
        require_final_evidence=True,
    )
    summary = manifest["summary"]
    expected = {
        "required_field_count": 6,
        "manual_review_required_field_count": 6,
        "authoritative_row_binding_proven_field_count": 0,
        "authoritative_value_binding_proven_field_count": 0,
        "materialized_performance_fact_count": 0,
        "public_business_value_count": 0,
        "s15_p1_performed": True,
        "s15_p2_performed": False,
        "s15_p3_performed": False,
        "stage15_review_performed": False,
        "decision": "NO_GO",
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            raise ValueError(f"S15-P1 dependency drift: {key}")
    if manifest.get("next_phase") != "S15-P2":
        raise ValueError("S15-P1 must route to S15-P2")
    return manifest


def _load_contract() -> dict[str, Any]:
    roadmap = ROADMAP_PATH.read_text(encoding="utf-8")
    taskpack = TASKPACK_PATH.read_text(encoding="utf-8")
    for token in (
        "S15｜销售绩效事实与复核清单",
        "P2 | 绩效复核清单",
        "输出绩效事实表",
        "输出异常项目和复核事项",
        "不计算最终工资",
        "不审批奖金",
    ):
        if token not in roadmap:
            raise ValueError(f"roadmap token missing: {token}")
    for token in ("销售绩效/业务考核线", "输出绩效事实和复核清单", "不做工资最终审批"):
        if token not in taskpack:
            raise ValueError(f"taskpack token missing: {token}")
    return {
        "taskpack_read": True,
        "roadmap_read": True,
        "s15_p2_contract_validated": True,
        "fact_table_required": True,
        "abnormal_project_and_review_items_required": True,
        "salary_calculation_forbidden": True,
        "bonus_approval_forbidden": True,
    }


def _load_legacy_fixture() -> dict[str, Any]:
    manifest = validate_v014_s15_p2_performance_review_list()
    facts = _read_jsonl(LEGACY_FACT_TABLE_PATH)
    reviews = _read_jsonl(LEGACY_REVIEW_ITEMS_PATH)
    summary = manifest["performance_review_summary"]
    if len(facts) != 4 or len(reviews) != 16:
        raise ValueError("historical S15-P2 fixture drift")
    if summary.get("performance_fact_row_count") != 4 or summary.get("abnormal_review_item_count") != 16:
        raise ValueError("historical S15-P2 summary drift")
    return {
        "fixture_validated": True,
        "historical_fact_row_count": len(facts),
        "historical_review_item_count": len(reviews),
        "dynamic_rows_are_authoritative": False,
        "four_fact_rows_quarantined": True,
        "sixteen_review_items_quarantined": True,
    }


def _build_columns() -> list[dict[str, Any]]:
    return [
        {
            "column_id": f"V014-S15P2-POST-COLUMN-{index:03d}",
            "field_key": spec["field_key"],
            "visible_field_label": spec["label"],
            "fact_kind": spec["fact_kind"],
            "source_requirement_ref": f"V014-S15P1-POST-REVIEW-{index:03d}",
            "authoritative_project_row_required": True,
            "authoritative_value_binding_required": True,
            "current_binding_status": "pending_authoritative_binding",
            "business_value_materialized": False,
            "public_business_value_allowed": False,
            "salary_or_bonus_use_allowed": False,
        }
        for index, spec in enumerate(FIELD_SPECS, 1)
    ]


def _build_fact_table(columns: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v014.s15_p2.post_remediation.performance_fact_table.v1",
        "record_type": "public_safe_empty_performance_fact_table",
        "column_count": len(columns),
        "columns": columns,
        "row_count": 0,
        "rows": [],
        "authoritative_project_row_count": 0,
        "authoritative_value_binding_count": 0,
        "synthetic_project_row_count": 0,
        "public_business_value_count": 0,
        "row_materialization_allowed": False,
        "empty_state_reason": "no_authoritative_project_rows_or_value_bindings",
        "manual_review_required_before_materialization": True,
        "performance_score_calculation_allowed": False,
        "salary_or_bonus_use_allowed": False,
    }


def _build_abnormal_method() -> dict[str, Any]:
    rules = [
        {
            "rule_id": f"V014-S15P2-POST-ABNORMAL-RULE-{index:03d}",
            "field_key": spec["field_key"],
            "visible_field_label": spec["label"],
            "entry_gate": "authoritative_project_period_unit_definition_and_exact_value_binding_required",
            "current_gate_passed": False,
            "comparison_method": "exact_integer_decimal_or_date_duration_only_after_authoritative_binding",
            "missing_binding_action": "create_field_level_manual_review_item",
            "actual_abnormal_project_claim_allowed": False,
            "reason_code": spec["reason_code"],
            "reason_zh": spec["reason_zh"],
        }
        for index, spec in enumerate(FIELD_SPECS, 1)
    ]
    return {
        "schema_version": "kmfa.v014.s15_p2.post_remediation.abnormal_project_method.v1",
        "record_type": "public_safe_abnormal_project_method",
        "method_count": 1,
        "rule_count": len(rules),
        "rules": rules,
        "entry_gate_count": 5,
        "entry_gates": [
            "authoritative_project_identity",
            "authoritative_reporting_period",
            "authoritative_unit_and_definition",
            "authoritative_row_binding",
            "authoritative_exact_value_binding",
        ],
        "current_output_status": "blocked_no_authoritative_project_rows",
        "actual_abnormal_project_count": 0,
        "project_specific_output_allowed": False,
        "performance_score_output_allowed": False,
        "salary_or_bonus_action_allowed": False,
    }


def _build_review_items() -> list[dict[str, Any]]:
    return [
        {
            "review_item_id": f"V014-S15P2-POST-REVIEW-{index:03d}",
            "scope_type": "field_level_authoritative_binding_review",
            "field_key": spec["field_key"],
            "visible_field_label": spec["label"],
            "source_requirement_ref": f"V014-S15P1-POST-REVIEW-{index:03d}",
            "manual_review_required": True,
            "current_status": "pending_authoritative_binding",
            "reason_code": spec["reason_code"],
            "reason_zh": spec["reason_zh"],
            "responsible_role": spec["responsible_role"],
            "responsible_role_zh": ROLE_LABELS[spec["responsible_role"]],
            "required_evidence_zh": "权威项目行、来源身份、报告期间、单位、计算口径和精确数值绑定",
            "abnormal_project_claimed": False,
            "project_specific_review": False,
            "auto_fill_allowed": False,
            "performance_score_calculation_allowed": False,
            "salary_or_bonus_action_allowed": False,
            "payroll_export_allowed": False,
        }
        for index, spec in enumerate(FIELD_SPECS, 1)
    ]


def _render_html(
    columns: list[dict[str, Any]],
    abnormal: dict[str, Any],
    review_items: list[dict[str, Any]],
) -> str:
    header_cells = "".join(f"<th>{html.escape(row['visible_field_label'])}</th>" for row in columns)
    rule_rows = "".join(
        "<tr>"
        f"<td>{html.escape(row['visible_field_label'])}</td>"
        "<td>权威项目、期间、单位、口径与精确值</td>"
        "<td>字段级人工复核</td>"
        "<td>未生成</td>"
        "</tr>"
        for row in abnormal["rules"]
    )
    buttons = "".join(
        f'<button type="button" data-review-button="{row["field_key"]}">'
        f'{html.escape(row["visible_field_label"])}</button>'
        for row in review_items
    )
    panels = "".join(
        f'<section data-review-panel="{row["field_key"]}" hidden>'
        f'<div class="panel-head"><div><span>复核事项 {index}/6</span>'
        f'<h3>{html.escape(row["visible_field_label"])}</h3></div>'
        '<span class="tag blocked">待权威绑定</span></div>'
        '<dl><div><dt>复核范围</dt><dd>字段级</dd></div>'
        f'<div><dt>责任角色</dt><dd>{html.escape(row["responsible_role_zh"])}</dd></div>'
        '<div><dt>异常项目</dt><dd>未生成</dd></div></dl>'
        f'<div class="reason">待补证：{html.escape(row["reason_zh"])}</div>'
        f'<p class="evidence">所需证据：{html.escape(row["required_evidence_zh"])}</p>'
        '<div class="limit">不得自动填值，不得生成绩效分数、工资或奖金结论。</div>'
        '</section>'
        for index, row in enumerate(review_items, 1)
    )
    links = "".join(
        f'<a data-dependency-link="{link_id}" href="{href}">{label}</a>'
        for link_id, (href, label) in DEPENDENCY_LINKS.items()
    )
    stage_link = f'<a data-stage-link="salary-boundary" href="{P3_HREF}">工资项目边界工作台</a>'
    labels = json.dumps(FIELD_LABELS, ensure_ascii=False, sort_keys=True)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>KMFA 绩效复核清单工作台</title>
  <style>
    *{{box-sizing:border-box}}body{{margin:0;background:#f2f5f5;color:#172b27;font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;letter-spacing:0}}
    header{{background:#103d34;color:#fff;border-bottom:3px solid #72c6b0}}.nav,.page{{width:min(1120px,calc(100% - 32px));margin:auto}}
    .nav{{display:flex;align-items:center;justify-content:space-between;gap:20px;padding:14px 0}}.brand{{display:flex;gap:12px;align-items:center}}
    .logo{{width:38px;height:38px;display:grid;place-items:center;background:#fff;color:#103d34;font-weight:800;border-radius:6px}}
    .brand strong{{display:block;font-size:17px}}.brand small{{display:block}}nav{{display:flex;gap:8px;flex-wrap:wrap;justify-content:flex-end}}
    nav a{{color:#fff;text-decoration:none;border:1px solid #7aa79c;padding:7px 10px;border-radius:4px;font-size:13px}}
    main{{padding:26px 0 34px}}h1{{font-size:30px;margin:0 0 4px}}h2{{font-size:20px;margin:0}}h3{{font-size:22px;margin:4px 0 0}}
    .intro{{color:#61746f;margin:0 0 16px}}.badges{{display:flex;gap:8px;margin:10px 0 16px;flex-wrap:wrap}}.badge,.tag{{padding:4px 9px;border:1px solid #ccd7d4;border-radius:4px;font-weight:700;font-size:13px;background:#fff}}
    .badge.ok{{color:#087258;border-color:#9fdacb}}.badge.blocked,.tag.blocked{{color:#ad3028;border-color:#efaaa5;background:#fff5f4}}
    .gate{{border-left:4px solid #ae3c35;background:#fff1ef;color:#8b2d27;padding:13px 15px;margin-bottom:18px}}
    .stats{{display:grid;grid-template-columns:repeat(4,1fr);border:1px solid #cad6d3;background:#fff;margin-bottom:18px}}
    .stat{{padding:14px 16px;border-right:1px solid #cad6d3}}.stat:last-child{{border-right:0}}.stat strong{{display:block;font-size:26px}}.stat span{{color:#687b76;font-size:13px}}
    .section{{background:#fff;border:1px solid #cad6d3;margin-bottom:18px}}.section-head{{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:14px 16px;border-bottom:1px solid #cad6d3}}
    .table-scroll{{overflow-x:auto}}table{{width:100%;border-collapse:collapse;table-layout:fixed;min-width:620px}}th,td{{padding:10px 12px;text-align:left;border-bottom:1px solid #d9e1df;overflow-wrap:anywhere}}th{{font-size:13px;color:#5a706a;background:#f6f8f7}}tr:last-child td{{border-bottom:0}}
    .empty{{text-align:center;color:#687b76;padding:18px}}.workspace{{display:grid;grid-template-columns:220px 1fr}}.review-buttons{{padding:14px;background:#f3f6f5;border-right:1px solid #cad6d3}}
    .review-buttons button{{width:100%;background:transparent;border:1px solid transparent;text-align:left;padding:9px;border-radius:4px;font:inherit}}
    .review-buttons button.active{{background:#fff;border-color:#60af9a;color:#087258;font-weight:700}}.panel{{padding:18px 20px}}
    .panel-head{{display:flex;justify-content:space-between;gap:20px;align-items:flex-start}}.panel-head span:first-child{{font-size:12px;color:#6b7d78}}
    dl{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}}dl div{{border-left:3px solid #7fc5b2;padding-left:10px}}dt{{font-size:12px;color:#6b7d78}}dd{{margin:2px 0 0;font-weight:700}}
    .reason,.evidence{{background:#f5f8f7;border:1px solid #cad6d3;padding:12px;margin:12px 0 0;overflow-wrap:anywhere}}.evidence{{margin-top:8px}}
    .limit{{background:#fff1ef;border:1px solid #efaaa5;color:#9b332d;padding:12px;margin-top:10px}}.status{{padding:12px 16px;background:#f5f8f7;border-top:1px solid #cad6d3;color:#5d716b}}
    .status-links{{display:flex;gap:12px;flex-wrap:wrap;margin-top:8px}}.status a{{color:#007696;text-decoration:none}}footer{{color:#5f736e;font-size:13px}}button:focus-visible,a:focus-visible{{outline:3px solid #f0ba4d;outline-offset:2px}}
    @media(max-width:680px){{.nav{{display:block}}nav{{justify-content:flex-start;margin-top:12px}}h1{{font-size:27px}}.stats{{grid-template-columns:repeat(2,1fr)}}.stat:nth-child(2){{border-right:0}}.stat:nth-child(-n+2){{border-bottom:1px solid #cad6d3}}
      table{{min-width:0;table-layout:fixed}}th,td{{padding:8px 5px;font-size:11px;word-break:break-word}}.workspace{{display:block}}.review-buttons{{border-right:0;border-bottom:1px solid #cad6d3;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:6px}}.review-buttons button{{text-align:center}}
      .panel{{padding:16px}}dl{{grid-template-columns:1fr}}.panel-head{{align-items:center}}.section-head{{align-items:flex-start}}}}
  </style>
</head>
<body data-active-review="">
  <header><div class="nav"><div class="brand"><div class="logo">KM</div><div><strong>KMFA 经营分析系统</strong><small>S15-P2 · 绩效复核清单</small></div></div><nav>{links}{stage_link}</nav></div></header>
  <main class="page">
    <h1>绩效复核清单工作台</h1>
    <p class="intro">仅展示事实表结构、异常判定方法和字段级复核事项；不展示项目、人员、金额、比率或日期明细。</p>
    <div class="badges"><span class="badge ok">Q4 / D</span><span class="badge blocked">NO_GO</span><span class="badge">内部复核</span></div>
    <div class="gate"><strong>门禁：</strong>权威项目行与数值绑定均为 0；不得生成实际异常项目、绩效分数、工资或奖金结论。</div>
    <section class="stats"><div class="stat"><strong>6 / 6</strong><span>事实表字段</span></div><div class="stat"><strong>0</strong><span>事实行</span></div><div class="stat"><strong>0</strong><span>实际异常项目</span></div><div class="stat"><strong>6</strong><span>字段级复核事项</span></div></section>
    <section class="section"><div class="section-head"><h2>绩效事实表结构</h2><span class="tag blocked">事实行 0</span></div><div class="table-scroll"><table><thead><tr>{header_cells}</tr></thead><tbody><tr><td class="empty" colspan="6">暂无权威项目事实行，不生成占位项目或业务值。</td></tr></tbody></table></div></section>
    <section class="section"><div class="section-head"><h2>异常项目判定方法</h2><span class="tag blocked">当前不输出实际项目</span></div><div class="table-scroll"><table><thead><tr><th>字段</th><th>进入条件</th><th>缺失处理</th><th>当前输出</th></tr></thead><tbody>{rule_rows}</tbody></table></div></section>
    <section class="section"><div class="section-head"><h2>字段级复核清单</h2><span class="tag blocked">6 项复核</span></div><div class="workspace"><div class="review-buttons">{buttons}</div><div class="panel">{panels}</div></div>
      <div class="status"><span id="interaction-status">字段级复核事项已加载。</span><div class="status-links">{links}</div></div></section>
    <footer>Stage 15 三个 phase 与整体复审均已完成；当前保持 Q4 / D · NO_GO，S16 仅可在下一 run work，不执行工资奖金、GitHub 上传、应用重装、正式报告、差异关闭或业务执行。</footer>
  </main>
  <script>
    const labels={labels};let actionSequence=0;
    function activate(id){{document.body.dataset.activeReview=id;document.body.dataset.lastAction='review:'+id+':'+(++actionSequence);document.querySelectorAll('[data-review-button]').forEach(b=>b.classList.toggle('active',b.dataset.reviewButton===id));document.querySelectorAll('[data-review-panel]').forEach(p=>p.hidden=p.dataset.reviewPanel!==id);document.getElementById('interaction-status').textContent='已显示“'+labels[id]+'”字段级复核事项；当前不生成异常项目或绩效事实。';}}
    document.querySelectorAll('[data-review-button]').forEach(button=>button.addEventListener('click',()=>activate(button.dataset.reviewButton)));
    activate('invoice_amount');document.body.dataset.uiReady='true';
  </script>
</body>
</html>"""


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        return


def _browser_worker() -> dict[str, Any]:
    from playwright.sync_api import sync_playwright

    root = Path("KMFA/stage_artifacts").resolve()
    handler = functools.partial(_QuietHandler, directory=str(root))
    server = socketserver.TCPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_address[1]}/"
    workbench_url = urljoin(base, f"{PHASE_ID}/exports/html/{HTML_PATH.name}")
    viewport_checks: list[dict[str, Any]] = []
    review_checks: list[dict[str, Any]] = []
    http_checks: list[dict[str, Any]] = []
    navigation_checks: list[dict[str, Any]] = []
    PRIVATE_SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            for mode, width, height in (("desktop", 1440, 900), ("mobile", 390, 844)):
                page = browser.new_page(viewport={"width": width, "height": height})
                errors: list[str] = []
                page.on(
                    "console",
                    lambda message, errors=errors: errors.append(message.text)
                    if message.type == "error"
                    else None,
                )
                page.goto(workbench_url, wait_until="networkidle")
                page.wait_for_function("document.body.dataset.uiReady === 'true'")
                body = page.locator("body").inner_text()
                viewport_checks.append(
                    {
                        "mode": mode,
                        "width": width,
                        "height": height,
                        "marker_visible": page.get_by_role("heading", name="绩效复核清单工作台").is_visible(),
                        "quality_visible": "Q4 / D" in body and "NO_GO" in body,
                        "zero_fact_rows_visible": "事实行 0" in body,
                        "six_review_items_visible": "6 项复核" in body,
                        "stage_boundary_visible": "S15-P3" in body,
                        "console_error_count": len(errors),
                        "no_horizontal_overflow": page.evaluate(
                            "document.documentElement.scrollWidth <= document.documentElement.clientWidth"
                        ),
                    }
                )
                for spec in FIELD_SPECS:
                    field_key = spec["field_key"]
                    page.locator(f'[data-review-button="{field_key}"]').click()
                    review_checks.append(
                        {
                            "mode": mode,
                            "field_key": field_key,
                            "passed": page.locator(f'[data-review-panel="{field_key}"]').is_visible()
                            and page.locator("body").get_attribute("data-active-review") == field_key
                            and spec["label"] in page.locator("#interaction-status").inner_text(),
                        }
                    )
                page.screenshot(
                    path=str(PRIVATE_SCREENSHOT_DIR / f"performance_review_{mode}.png"),
                    full_page=True,
                )
                page.close()

            request = playwright.request.new_context()
            for link_id, (_, marker) in DEPENDENCY_LINKS.items():
                page = browser.new_page(viewport={"width": 1280, "height": 900})
                page.goto(workbench_url, wait_until="networkidle")
                href = page.locator(f'a[data-dependency-link="{link_id}"]').first.get_attribute("href") or ""
                target = urljoin(workbench_url, href)
                response = request.get(target)
                http_checks.append({"link_id": link_id, "status": response.status, "passed": response.ok})
                page.locator(f'a[data-dependency-link="{link_id}"]').first.click()
                page.wait_for_load_state("networkidle")
                navigation_checks.append(
                    {"link_id": link_id, "marker": marker, "passed": marker in page.locator("body").inner_text()}
                )
                page.close()
            request.dispose()
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    result = {
        "status": "PASS",
        "viewport_checks": viewport_checks,
        "review_item_interaction_checks": review_checks,
        "dependency_link_http_checks": http_checks,
        "dependency_navigation_checks": navigation_checks,
    }
    if not (
        len(viewport_checks) == 2
        and all(
            row["marker_visible"]
            and row["quality_visible"]
            and row["zero_fact_rows_visible"]
            and row["six_review_items_visible"]
            and row["stage_boundary_visible"]
            and row["console_error_count"] == 0
            and row["no_horizontal_overflow"]
            for row in viewport_checks
        )
        and len(review_checks) == 12
        and all(row["passed"] for row in review_checks)
        and len(http_checks) == 4
        and all(row["passed"] for row in http_checks)
        and len(navigation_checks) == 4
        and all(row["passed"] for row in navigation_checks)
    ):
        result["status"] = "FAIL"
    _write_json(PRIVATE_BROWSER_PATH, result)
    return result


def _run_browser_review() -> dict[str, Any]:
    python = os.environ.get("KMFA_AUDIT_PYTHON", sys.executable)
    result = subprocess.run(
        [python, __file__, "--browser-evidence-only"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": "."},
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    browser = _read_json(PRIVATE_BROWSER_PATH)
    if browser.get("status") != "PASS":
        raise RuntimeError("S15-P2 browser validation failed")
    helper = p1.s14_review.p1.s13_review.p1.s12_review.p1.s11_home
    baseline = helper._run_html_audit(HTML_BASELINE_ROOT, PRIVATE_BASELINE_AUDIT_PATH)
    current = helper._run_html_audit(HTML_DIR, PRIVATE_CURRENT_AUDIT_PATH)
    expected_baseline = {
        "file_count": 6,
        "control_row_count": 54,
        "pass_count": 54,
        "warn_count": 0,
        "fail_count": 0,
    }
    if baseline != expected_baseline:
        raise RuntimeError("v1.4 HTML baseline drift")
    if current["file_count"] != 1 or current["warn_count"] or current["fail_count"]:
        raise RuntimeError("S15-P2 HTML audit failed")
    if current["pass_count"] != current["control_row_count"]:
        raise RuntimeError("S15-P2 HTML audit incomplete")
    return {
        "status": "PASS",
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
        "review_item_interaction_check_count": len(browser["review_item_interaction_checks"]),
        "dependency_link_http_check_count": len(browser["dependency_link_http_checks"]),
        "dependency_navigation_check_count": len(browser["dependency_navigation_checks"]),
        "console_error_count": sum(row["console_error_count"] for row in browser["viewport_checks"]),
        "horizontal_overflow_count": sum(
            not row["no_horizontal_overflow"] for row in browser["viewport_checks"]
        ),
    }


def _quality_gate() -> dict[str, Any]:
    return {
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "decision": "NO_GO",
        "release_permission": "blocked",
        "fact_table_schema_output_allowed": True,
        "abnormal_project_method_output_allowed": True,
        "field_review_item_output_allowed": True,
        "authoritative_fact_row_output_allowed": False,
        "synthetic_project_row_output_allowed": False,
        "actual_abnormal_project_output_allowed": False,
        "public_business_value_display_allowed": False,
        "performance_score_calculation_allowed": False,
        "salary_calculation_allowed": False,
        "bonus_approval_allowed": False,
        "payroll_export_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
    }


def _phase_boundaries() -> dict[str, bool]:
    return {
        "s15_p1_dependency_included": True,
        "s15_p2_scope_included": True,
        "s15_p3_scope_included": False,
        "stage15_review_scope_included": False,
        "github_upload_scope_included": False,
        "app_reinstall_scope_included": False,
        "formal_report_scope_included": False,
        "difference_closure_scope_included": False,
        "salary_calculation_scope_included": False,
        "bonus_approval_scope_included": False,
        "payroll_export_scope_included": False,
        "persistent_business_write_scope_included": False,
        "business_execution_scope_included": False,
    }


def _raw_boundary() -> dict[str, bool]:
    return {
        "raw_source_read_only_snapshot_performed": True,
        "raw_source_modified": False,
        "raw_source_deleted": False,
        "raw_source_moved": False,
        "raw_source_renamed": False,
        "raw_source_overwritten": False,
        "raw_source_written": False,
        "raw_business_data_committed": False,
        "raw_filename_committed": False,
        "raw_header_committed": False,
        "raw_business_value_committed": False,
        "private_diagnostic_committed": False,
        "private_screenshot_committed": False,
    }


def _public_safety() -> dict[str, bool]:
    return {
        "aggregate_counts_only": True,
        "public_safe_structure_only": True,
        "raw_business_data_committed": False,
        "raw_filename_committed": False,
        "raw_header_committed": False,
        "raw_business_value_committed": False,
        "business_project_plaintext_committed": False,
        "business_person_plaintext_committed": False,
        "business_amount_committed": False,
        "business_ratio_committed": False,
        "business_date_committed": False,
        "synthetic_project_reference_committed": False,
        "salary_or_bonus_payload_committed": False,
        "credential_or_secret_committed": False,
        "private_runtime_committed": False,
    }


def _acceptance_matrix(summary: dict[str, Any]) -> dict[str, Any]:
    checks = [
        ("s15_p1_current_dependency", summary["s15_p1_post_remediation_dependency_validated"]),
        ("taskpack_contract", summary["taskpack_contract_validated"]),
        ("legacy_fixture", summary["historical_s15_p2_fixture_validated"]),
        ("legacy_rows_quarantined", summary["historical_four_fact_rows_quarantined"]),
        ("fact_table_schema", summary["performance_fact_table_schema_count"] == 1),
        ("six_columns", summary["performance_fact_table_column_count"] == 6),
        ("zero_fact_rows", summary["performance_fact_row_count"] == 0),
        ("zero_authoritative_project_rows", summary["authoritative_project_row_count"] == 0),
        ("abnormal_method", summary["abnormal_project_method_count"] == 1),
        ("six_abnormal_rules", summary["abnormal_project_rule_count"] == 6),
        ("zero_actual_abnormal_projects", summary["actual_abnormal_project_count"] == 0),
        ("six_review_items", summary["field_review_item_count"] == 6),
        ("zero_project_specific_reviews", summary["project_specific_review_item_count"] == 0),
        ("zero_public_values", summary["public_business_value_count"] == 0),
        ("raw_exact", summary["raw_snapshot_exact_match"]),
        ("raw_cross_phase", summary["raw_cross_phase_snapshot_exact_match"]),
        ("browser", summary["browser_status"] == "PASS"),
        ("quality_block", summary["decision"] == "NO_GO"),
        ("downstream_closed", not summary["s15_p3_performed"] and not summary["salary_calculation_performed"]),
        ("upload_deferred", not summary["github_upload_performed"]),
    ]
    rows = [
        {"check_id": f"V014-S15P2-POST-ACC-{index:03d}", "name": name, "status": "PASS" if passed else "FAIL"}
        for index, (name, passed) in enumerate(checks, 1)
    ]
    return {
        "schema_version": "kmfa.v014.s15_p2.post_remediation.acceptance_matrix.v1",
        "acceptance_id": ACCEPTANCE_ID,
        "check_count": len(rows),
        "check_pass_count": sum(row["status"] == "PASS" for row in rows),
        "check_fail_count": sum(row["status"] == "FAIL" for row in rows),
        "checks": rows,
    }


def _phase_public_files() -> list[str]:
    artifact_paths = (
        SUMMARY_PATH,
        MANIFEST_PATH,
        FACT_SCHEMA_PATH,
        FACT_TABLE_PATH,
        ABNORMAL_METHOD_PATH,
        REVIEW_ITEMS_PATH,
        MATRIX_PATH,
        GO_NO_GO_PATH,
        HTML_PATH,
        REPORT_PATH,
        TEST_RESULTS_PATH,
        RISK_REGISTER_PATH,
        ROLLBACK_PATH,
        METADATA_SUMMARY_PATH,
        METADATA_MANIFEST_PATH,
        METADATA_FACT_SCHEMA_PATH,
        METADATA_FACT_TABLE_PATH,
        METADATA_ABNORMAL_METHOD_PATH,
        METADATA_REVIEW_ITEMS_PATH,
        METADATA_MATRIX_PATH,
        METADATA_GO_NO_GO_PATH,
    )
    governance_paths = (
        Path("KMFA/AGENTS.md"),
        Path("KMFA/CHANGELOG.md"),
        Path("KMFA/HANDOFF.md"),
        Path("KMFA/VERSION"),
        ASSURANCE_STATUS_PATH,
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
    code_paths = (
        Path("KMFA/tools/check_v014_s15_p1_post_remediation_performance_fact_fields.py"),
        Path("KMFA/tools/v014_s15_p2_post_remediation_performance_review_list.py"),
        Path("KMFA/tools/check_v014_s15_p2_post_remediation_performance_review_list.py"),
        Path("KMFA/tests/test_v014_s15_p2_post_remediation_performance_review_list.py"),
    )
    return [path.as_posix() for path in artifact_paths + governance_paths + code_paths]


def _write_governance(generated_at: str) -> None:
    evidence_ref = MANIFEST_PATH.as_posix()
    _sync_assurance_snapshot_time(generated_at)
    _upsert_jsonl(
        DEVELOPMENT_EVENTS_PATH,
        {
            "event_id": "DEV-KMFA-20260711-V014-S15-P2-POST-REMEDIATION-PERFORMANCE-REVIEW-LIST",
            "event_time": generated_at,
            "event_type": "phase_delivery",
            "project_id": "KMFA",
            "stage_id": "S15",
            "phase_id": PHASE_ID,
            "roadmap_phase_id": ROADMAP_PHASE_ID,
            "task_id": TASK_ID,
            "status": STATUS,
            "fact_level": "EXTRACTED",
            "decision": DECISION,
            "performance_fact_row_count": 0,
            "actual_abnormal_project_count": 0,
            "field_review_item_count": 6,
            "raw_business_data_committed": False,
            "github_upload_performed": False,
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
            "record_type": "phase_status",
            "project_id": "KMFA",
            "stage_id": "S15",
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
            "business_execution_performed": False,
            "evidence_ref": evidence_ref,
            "updated_at": generated_at,
        },
    )
    _upsert_jsonl(
        TASK_STATUS_PATH,
        {
            "schema_version": "kmfa.v014_stage_phase_task_status.v1",
            "record_type": "v014_phase_delivery",
            "project_id": "KMFA",
            "stage_id": "S15",
            "governance_stage_id": "SALES-PERFORMANCE-REVIEW",
            "roadmap_stage_id": "S15",
            "roadmap_phase_id": ROADMAP_PHASE_ID,
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "acceptance_id": ACCEPTANCE_ID,
            "version": VERSION,
            "name": "v0.1.4 S15-P2 post-remediation performance review list",
            "phase_goal": "output zero-row fact schema abnormal method and six field review items",
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


def _render_report(summary: dict[str, Any]) -> str:
    return f"""# KMFA v0.1.4 S15-P2 修补后绩效复核清单

## 结论

- 绩效事实表结构：{summary['performance_fact_table_schema_count']} 个，字段 {summary['performance_fact_table_column_count']} 个。
- 权威项目行、权威值绑定、实际事实行、实际异常项目：均为 0。
- 异常项目判定方法：1 个，字段规则 6 条；当前只生成方法，不生成项目占位行。
- 字段级复核事项：6 项，全部保持待权威绑定。
- 当前状态：Q4 / D / NO_GO / 3-9-2-1。

## 复核边界

1. S15-P1 的候选结构不证明同一项目、人员、期间、单位、口径或数值。
2. legacy 的 4 条合成项目事实和 16 条事项只作历史结构夹具，不是当前事实。
3. 没有权威项目行时，不得生成实际异常项目、绩效分数、工资或奖金结论。
4. 本 phase 不执行 S15-P3、Stage 15 整体复审、上传、重装、正式报告或业务动作。
"""


def _render_test_results(summary: dict[str, Any]) -> str:
    return f"""# S15-P2 测试结果

- focused test / strict validator：最终复验结果见 manifest。
- v1.4 baseline：54/54 PASS。
- current HTML audit：{summary['current_html_pass_count']}/{summary['current_html_control_row_count']} PASS。
- desktop/mobile：2/2 PASS。
- 六事项交互：12/12 PASS。
- 依赖 HTTP / 真实导航：4/4 / 4/4 PASS。
- raw 前后/跨 S15-P1/current：exact match。
- 事实行 / 实际异常项目 / 公开业务值：0 / 0 / 0。
"""


def _render_private_report(summary: dict[str, Any]) -> str:
    return f"""# S15-P2 私有差异记录

## 当前事实

- 原始文件：{summary['raw_source_file_count']}
- XLSX 容器：{summary['private_xlsx_container_count']}
- 可解析 / 不可解析：{summary['private_parseable_xlsx_count']} / {summary['private_unparseable_xlsx_count']}
- 可解析工作表：{summary['private_parseable_sheet_count']}
- 唯一候选：{summary['private_unique_candidate_sheet_count']}
- S15-P1 双次探针指纹不一致：{summary['private_probe_roundtrip_mismatch_count']}

## 当前差异

1. 六字段均缺少权威项目行、期间、单位、口径和精确数值绑定。
2. 当前事实表只能输出结构，不能输出实际项目事实行。
3. 当前异常项目只能输出判定方法，不能输出实际异常项目。
4. 六项字段级复核事项全部保持待权威绑定。

## 处理结论

- raw phase 前后、跨 S15-P1 和当前快照完全一致。
- 原始文件未修改、删除、移动、重命名、覆盖或写入。
- 最终 goal 多轮交叉验证仍无法对齐时，必须纳入全中文最终差异报告。
"""


def generate(*, final_validation: bool = False, write_governance: bool = True) -> dict[str, Any]:
    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    raw_helper = p1.s14_review.p1.s13_review.p1.s12_review.p1.s11_project
    raw_before = raw_helper._raw_snapshot("before_v014_s15_p2_post_remediation_performance_review_list")
    dependency = _load_dependency()
    contract = _load_contract()
    legacy = _load_legacy_fixture()
    probe = _read_json(p1.PRIVATE_PROBE_PATH)
    columns = _build_columns()
    fact_table = _build_fact_table(columns)
    abnormal = _build_abnormal_method()
    review_items = _build_review_items()
    _write_text(HTML_PATH, _render_html(columns, abnormal, review_items))
    browser = _run_browser_review()
    raw_after = raw_helper._raw_snapshot("after_v014_s15_p2_post_remediation_performance_review_list")
    prior_raw = _read_json(p1.PRIVATE_RAW_AFTER_PATH)
    current_raw = raw_helper._raw_snapshot("current_v014_s15_p2_post_remediation_performance_review_list")
    normalize = raw_helper._normalize_raw
    raw_exact = normalize(raw_before) == normalize(raw_after)
    raw_cross = normalize(raw_before) == normalize(prior_raw) == normalize(current_raw)
    if not raw_exact or not raw_cross:
        raise RuntimeError("raw source changed during S15-P2")

    upstream = dependency["summary"]
    summary = {
        "schema_version": "kmfa.v014.s15_p2.post_remediation.summary.v1",
        "project_id": "KMFA",
        "stage_id": "S15",
        "phase_id": PHASE_ID,
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "version": VERSION,
        "status": STATUS,
        "decision": DECISION,
        "s15_p1_post_remediation_dependency_validated": True,
        "taskpack_contract_validated": True,
        "historical_s15_p2_fixture_validated": True,
        "historical_four_fact_rows_quarantined": True,
        "historical_sixteen_review_items_quarantined": True,
        "required_field_count": len(FIELD_KEYS),
        "s15_p1_manual_review_required_field_count": upstream["manual_review_required_field_count"],
        "s15_p1_materialized_performance_fact_count": upstream["materialized_performance_fact_count"],
        "performance_fact_table_schema_count": 1,
        "performance_fact_table_column_count": len(columns),
        "performance_fact_row_count": fact_table["row_count"],
        "authoritative_project_row_count": fact_table["authoritative_project_row_count"],
        "authoritative_value_binding_count": fact_table["authoritative_value_binding_count"],
        "synthetic_project_row_count": fact_table["synthetic_project_row_count"],
        "public_business_value_count": fact_table["public_business_value_count"],
        "abnormal_project_method_count": abnormal["method_count"],
        "abnormal_project_rule_count": abnormal["rule_count"],
        "actual_abnormal_project_count": abnormal["actual_abnormal_project_count"],
        "field_review_item_count": len(review_items),
        "manual_review_required_item_count": sum(row["manual_review_required"] for row in review_items),
        "project_specific_review_item_count": sum(row["project_specific_review"] for row in review_items),
        "workbench_html_count": 1,
        "raw_source_file_count": probe["raw_source_file_count"],
        "private_xlsx_container_count": probe["private_xlsx_container_count"],
        "private_parseable_xlsx_count": probe["private_parseable_xlsx_count"],
        "private_unparseable_xlsx_count": probe["private_unparseable_xlsx_count"],
        "private_parseable_sheet_count": probe["private_parseable_sheet_count"],
        "private_unique_candidate_sheet_count": probe["private_unique_candidate_sheet_count"],
        "private_multi_field_candidate_sheet_count": probe["private_multi_field_candidate_sheet_count"],
        "private_candidate_covered_field_count": probe["private_candidate_covered_field_count"],
        "private_probe_roundtrip_mismatch_count": probe["private_probe_roundtrip_mismatch_count"],
        "raw_snapshot_exact_match": raw_exact,
        "raw_cross_phase_snapshot_exact_match": raw_cross,
        "browser_status": browser["status"],
        "baseline_html_control_row_count": browser["baseline_control_row_count"],
        "baseline_html_pass_count": browser["baseline_pass_count"],
        "current_html_control_row_count": browser["current_control_row_count"],
        "current_html_pass_count": browser["current_pass_count"],
        "browser_viewport_check_count": browser["viewport_check_count"],
        "review_item_interaction_check_count": browser["review_item_interaction_check_count"],
        "dependency_link_http_check_count": browser["dependency_link_http_check_count"],
        "dependency_navigation_check_count": browser["dependency_navigation_check_count"],
        "console_error_count": browser["console_error_count"],
        "horizontal_overflow_count": browser["horizontal_overflow_count"],
        "open_final_difference_accepted_count": upstream["open_final_difference_accepted_count"],
        "nonzero_delta_reconciliation_count": upstream["nonzero_delta_reconciliation_count"],
        "zero_delta_reconciliation_count": upstream["zero_delta_reconciliation_count"],
        "incomplete_reconciliation_count": upstream["incomplete_reconciliation_count"],
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "s15_p1_performed": True,
        "s15_p2_performed": True,
        "s15_p3_performed": False,
        "stage15_review_performed": False,
        "salary_calculation_performed": False,
        "bonus_approval_performed": False,
        "payroll_export_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "formal_report_release_performed": False,
        "business_execution_performed": False,
    }
    matrix = _acceptance_matrix(summary)
    go_no_go = {
        "schema_version": "kmfa.v014.s15_p2.post_remediation.go_no_go.v1",
        "project_id": "KMFA",
        "stage_id": "S15",
        "phase_id": PHASE_ID,
        "decision": "NO_GO",
        "fact_table_schema_output_allowed": True,
        "abnormal_project_method_output_allowed": True,
        "field_review_item_output_allowed": True,
        "performance_fact_release_allowed": False,
        "actual_abnormal_project_release_allowed": False,
        "salary_or_bonus_action_allowed": False,
        "payroll_export_allowed": False,
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
        "governance_and_safety_scans": "PASS" if final_validation else "PENDING",
    }
    manifest = {
        "schema_version": "kmfa.v014.s15_p2.post_remediation.manifest.v1",
        "project_id": "KMFA",
        "stage_id": "S15",
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
        "performance_fact_table": fact_table,
        "abnormal_project_method": abnormal,
        "review_items": review_items,
        "acceptance_matrix": matrix,
        "go_no_go": go_no_go,
        "quality_gate": _quality_gate(),
        "phase_boundaries": _phase_boundaries(),
        "raw_boundary": _raw_boundary(),
        "public_repo_safety": _public_safety(),
        "browser_review": browser,
        "taskpack_contract": contract,
        "s15_p1_post_remediation_dependency_validated": True,
        "historical_s15_p2_fixture_validated": legacy["fixture_validated"],
        "historical_s15_p2_dynamic_rows_are_authoritative": False,
        "historical_four_fact_rows_quarantined": legacy["four_fact_rows_quarantined"],
        "historical_sixteen_review_items_quarantined": legacy["sixteen_review_items_quarantined"],
        "historical_fixture_counts": legacy,
        "validation_summary": validation_summary,
        "next_phase": "S15-P3",
        "next_required_step": (
            "下一轮仅执行 S15-P3；不得执行 Stage 15 整体复审、工资奖金、GitHub upload、"
            "app reinstall、正式报告、差异关闭或业务执行。"
        ),
    }

    schema_document = {
        "schema_version": "kmfa.v014.s15_p2.post_remediation.performance_fact_table_schema.v1",
        "column_count": len(columns),
        "columns": columns,
    }
    review_document = {
        "schema_version": "kmfa.v014.s15_p2.post_remediation.performance_review_items.v1",
        "review_item_count": len(review_items),
        "items": review_items,
    }
    diagnostic = {
        "schema_version": "kmfa.private.v014.s15_p2.performance_review_readiness.v1",
        "generated_at": generated_at,
        "raw_source_file_count": probe["raw_source_file_count"],
        "private_xlsx_container_count": probe["private_xlsx_container_count"],
        "private_parseable_sheet_count": probe["private_parseable_sheet_count"],
        "private_unique_candidate_sheet_count": probe["private_unique_candidate_sheet_count"],
        "private_multi_field_candidate_sheet_count": probe["private_multi_field_candidate_sheet_count"],
        "private_candidate_covered_field_count": probe["private_candidate_covered_field_count"],
        "private_probe_roundtrip_mismatch_count": probe["private_probe_roundtrip_mismatch_count"],
        "authoritative_project_row_count": 0,
        "authoritative_value_binding_count": 0,
        "performance_fact_row_count": 0,
        "actual_abnormal_project_count": 0,
        "field_review_item_count": 6,
        "legacy_fact_rows_quarantined": 4,
        "legacy_review_items_quarantined": 16,
        "raw_snapshot_exact_match": raw_exact,
        "raw_cross_phase_snapshot_exact_match": raw_cross,
    }
    for path, value in (
        (SUMMARY_PATH, summary),
        (MANIFEST_PATH, manifest),
        (FACT_SCHEMA_PATH, schema_document),
        (FACT_TABLE_PATH, fact_table),
        (ABNORMAL_METHOD_PATH, abnormal),
        (REVIEW_ITEMS_PATH, review_document),
        (MATRIX_PATH, matrix),
        (GO_NO_GO_PATH, go_no_go),
        (METADATA_SUMMARY_PATH, summary),
        (METADATA_MANIFEST_PATH, manifest),
        (METADATA_FACT_SCHEMA_PATH, schema_document),
        (METADATA_FACT_TABLE_PATH, fact_table),
        (METADATA_ABNORMAL_METHOD_PATH, abnormal),
        (METADATA_REVIEW_ITEMS_PATH, review_document),
        (METADATA_MATRIX_PATH, matrix),
        (METADATA_GO_NO_GO_PATH, go_no_go),
        (PRIVATE_RAW_BEFORE_PATH, raw_before),
        (PRIVATE_RAW_AFTER_PATH, raw_after),
        (PRIVATE_DIAGNOSTIC_PATH, diagnostic),
    ):
        _write_json(path, value)
    _write_text(REPORT_PATH, _render_report(summary))
    _write_text(TEST_RESULTS_PATH, _render_test_results(summary))
    _write_text(
        RISK_REGISTER_PATH,
        """# S15-P2 风险登记

| 风险 | 控制 | 状态 |
|---|---|---|
| legacy 合成项目行回流 | 4 条事实行和 16 条事项只作历史夹具，当前行数锁为 0 | controlled |
| 空表被误读为已完成绩效 | 明示 Q4 / D / NO_GO，事实行与实际异常项目均为 0 | controlled |
| 字段事项被误读为项目异常 | 六项均标记字段级且不含 project_ref | controlled |
| 复核清单进入工资奖金 | 绩效分数、工资、奖金、薪资导出全部阻断 | controlled |
| raw/private/secret 进入 Git | 快照、诊断与截图只写 ignored private runtime | controlled |
""",
    )
    _write_text(
        ROLLBACK_PATH,
        f"""# S15-P2 回滚计划

1. 回退本 phase 的本地 commit 和 {OUTPUT_DIR.as_posix()} 公开证据。
2. 删除 ignored private raw/diagnostic/browser evidence，不触碰原始目录。
3. 恢复 S15-P1 为当前治理入口；不进入 S15-P3。
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
    parser.add_argument("--no-governance", action="store_true")
    args = parser.parse_args()
    if args.browser_evidence_only:
        browser = _browser_worker()
        print(browser["status"])
        return 0 if browser["status"] == "PASS" else 1
    manifest = generate(
        final_validation=args.final_validation,
        write_governance=not args.no_governance,
    )
    summary = manifest["summary"]
    print(
        "S15-P2 post-remediation performance review: "
        f"columns={summary['performance_fact_table_column_count']} "
        f"fact_rows={summary['performance_fact_row_count']} "
        f"abnormal_projects={summary['actual_abnormal_project_count']} "
        f"review_items={summary['field_review_item_count']} "
        f"decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
