#!/usr/bin/env python3
"""Generate current KMFA v0.1.4 S15-P3 salary-boundary evidence."""

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

from KMFA.tools import v014_s15_p2_post_remediation_performance_review_list as p2
from KMFA.tools.check_v014_s15_p2_post_remediation_performance_review_list import (
    validate_v014_s15_p2_post_remediation_performance_review_list,
)
from KMFA.tools.check_v014_s15_p3_salary_boundary import validate_v014_s15_p3_salary_boundary


PHASE_ID = "V014_S15_P3_POST_REMEDIATION_SALARY_BOUNDARY"
ROADMAP_PHASE_ID = "S15-P3"
TASK_ID = "KMFA-V014-S15-P3-POST-REMEDIATION-SALARY-BOUNDARY-20260711"
ACCEPTANCE_ID = "ACC-V014-S15-P3-POST-REMEDIATION-SALARY-BOUNDARY"
VERSION = "0.1.4-s15-p3-post-remediation-salary-boundary"
STATUS = "completed_validated_local_only_s15_p3_schema_only_zero_salary_records_no_go_upload_deferred"
DECISION = "NO_GO"
BOUNDARY_VERSION = "BOUNDARY-KMFA-V014-S15P3-POST-REMEDIATION-SALARY-FACT-INTERFACE-001"
FORMULA_ID = "FORM-KMFA-V014-S15P3-POST-REMEDIATION-SALARY-BOUNDARY-001"
PARAMETER_IDS = ("PARAM-KMFA-1773", "PARAM-KMFA-1774", "PARAM-KMFA-1775", "PARAM-KMFA-1776")
MODEL_REGISTRY_KEY = "kmfa_v014_s15_p3_post_remediation_salary_boundary"

OUTPUT_DIR = Path("KMFA/stage_artifacts") / PHASE_ID
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
HTML_DIR = OUTPUT_DIR / "exports/html"
SUMMARY_PATH = MACHINE_DIR / "salary_boundary_summary.json"
MANIFEST_PATH = MACHINE_DIR / "salary_boundary_manifest.json"
INTERFACE_PATH = MACHINE_DIR / "fact_output_interface_contract_public_safe.json"
READ_DRAFT_PATH = MACHINE_DIR / "future_salary_system_read_draft_public_safe.json"
HUMAN_BOUNDARY_PATH = MACHINE_DIR / "human_approval_boundary_public_safe.json"
MATRIX_PATH = MACHINE_DIR / "salary_boundary_acceptance_matrix.json"
GO_NO_GO_PATH = MACHINE_DIR / "salary_boundary_go_no_go.json"
HTML_PATH = HTML_DIR / "salary_boundary_workbench.html"
REPORT_PATH = HUMAN_DIR / "salary_boundary_report_zh.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results_zh.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register_zh.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan_zh.md"

QUALITY_DIR = Path("KMFA/metadata/quality")
METADATA_SUMMARY_PATH = QUALITY_DIR / "v014_s15_p3_post_remediation_salary_boundary_summary.json"
METADATA_MANIFEST_PATH = QUALITY_DIR / "v014_s15_p3_post_remediation_salary_boundary_manifest.json"
METADATA_INTERFACE_PATH = (
    QUALITY_DIR / "v014_s15_p3_post_remediation_fact_output_interface_contract_public_safe.json"
)
METADATA_READ_DRAFT_PATH = (
    QUALITY_DIR / "v014_s15_p3_post_remediation_future_salary_system_read_draft_public_safe.json"
)
METADATA_HUMAN_BOUNDARY_PATH = (
    QUALITY_DIR / "v014_s15_p3_post_remediation_human_approval_boundary_public_safe.json"
)
METADATA_MATRIX_PATH = QUALITY_DIR / "v014_s15_p3_post_remediation_salary_boundary_acceptance_matrix.json"
METADATA_GO_NO_GO_PATH = QUALITY_DIR / "v014_s15_p3_post_remediation_salary_boundary_go_no_go.json"

PRIVATE_DIR = Path("KMFA/.codex_private_runtime/v014_s15_p3_post_remediation_salary_boundary")
PRIVATE_RAW_BEFORE_PATH = PRIVATE_DIR / "raw_immutability_before.json"
PRIVATE_RAW_AFTER_PATH = PRIVATE_DIR / "raw_immutability_after.json"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_DIR / "salary_boundary_readiness_diagnostic.json"
PRIVATE_REPORT_PATH = PRIVATE_DIR / "salary_boundary_difference_report_zh.md"
PRIVATE_BROWSER_PATH = PRIVATE_DIR / "browser_verification.json"
PRIVATE_BASELINE_AUDIT_PATH = PRIVATE_DIR / "human_flow_baseline_audit.csv"
PRIVATE_CURRENT_AUDIT_PATH = PRIVATE_DIR / "current_salary_boundary_audit.csv"
PRIVATE_SCREENSHOT_DIR = PRIVATE_DIR / "screenshots"

ROADMAP_PATH = p2.ROADMAP_PATH
TASKPACK_PATH = p2.TASKPACK_PATH
HTML_BASELINE_ROOT = p2.HTML_BASELINE_ROOT
LEGACY_MANIFEST_PATH = Path("KMFA/stage_artifacts/V014_S15_P3_SALARY_BOUNDARY/machine/salary_boundary_manifest.json")
LEGACY_INTERFACE_PATH = Path(
    "KMFA/stage_artifacts/V014_S15_P3_SALARY_BOUNDARY/machine/fact_output_interface_contract.json"
)
LEGACY_READINESS_PATH = Path(
    "KMFA/stage_artifacts/V014_S15_P3_SALARY_BOUNDARY/machine/future_salary_system_readiness_draft.jsonl"
)

DEVELOPMENT_EVENTS_PATH = Path("KMFA/docs/governance/development_events.jsonl")
ASSURANCE_STATUS_PATH = Path("KMFA/docs/governance/ASSURANCE_STATUS.yaml")
STAGE_STATUS_PATH = Path("KMFA/metadata/stage_status.jsonl")
TASK_STATUS_PATH = Path("KMFA/metadata/traceability/v1_4_stage_phase_task_status.jsonl")

FIELD_SPECS = p2.FIELD_SPECS
FIELD_KEYS = p2.FIELD_KEYS
FIELD_LABELS = p2.FIELD_LABELS
FACT_KIND_LABELS = {
    "money_minor_unit": "金额（整数分）",
    "ratio_basis_points": "比率（基点）",
    "duration_days": "时长（天）",
    "money_minor_unit_or_ratio_basis_points": "金额（整数分）或比率（基点）",
}
HUMAN_CHECKPOINT_KEYS = (
    "fact_quality_acceptance",
    "compensation_policy_mapping_approval",
    "final_compensation_approval",
    "payment_release_approval",
)
HUMAN_CHECKPOINT_LABELS = {
    "fact_quality_acceptance": "绩效事实质量确认",
    "compensation_policy_mapping_approval": "薪酬政策映射审批",
    "final_compensation_approval": "最终薪酬审批",
    "payment_release_approval": "发放放行审批",
}

DEPENDENCY_LINKS = {
    "review-list": (
        "../../../V014_S15_P2_POST_REMEDIATION_PERFORMANCE_REVIEW_LIST/exports/html/"
        "performance_review_workbench.html",
        "绩效复核清单工作台",
    ),
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
}


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
    manifest = validate_v014_s15_p2_post_remediation_performance_review_list(
        require_private_evidence=True,
        require_browser_evidence=True,
        require_final_evidence=True,
    )
    summary = manifest["summary"]
    expected = {
        "performance_fact_table_column_count": 6,
        "performance_fact_row_count": 0,
        "actual_abnormal_project_count": 0,
        "field_review_item_count": 6,
        "project_specific_review_item_count": 0,
        "public_business_value_count": 0,
        "s15_p1_performed": True,
        "s15_p2_performed": True,
        "s15_p3_performed": False,
        "stage15_review_performed": False,
        "decision": "NO_GO",
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            raise ValueError(f"S15-P2 dependency drift: {key}")
    if manifest.get("next_phase") != "S15-P3":
        raise ValueError("S15-P2 must route to S15-P3")
    return manifest


def _load_contract() -> dict[str, Any]:
    roadmap = ROADMAP_PATH.read_text(encoding="utf-8")
    taskpack = TASKPACK_PATH.read_text(encoding="utf-8")
    for token in (
        "S15｜销售绩效事实与复核清单",
        "P3 | 与工资项目边界",
        "仅预留事实输出接口",
        "未来可供工资系统读取草案",
        "最终审批和发放必须人工处理",
    ):
        if token not in roadmap:
            raise ValueError(f"roadmap token missing: {token}")
    for token in ("销售绩效/业务考核线", "不做工资最终审批", "不自动发工资或奖金"):
        if token not in taskpack:
            raise ValueError(f"taskpack token missing: {token}")
    return {
        "taskpack_read": True,
        "roadmap_read": True,
        "s15_p3_contract_validated": True,
        "fact_output_interface_only": True,
        "future_salary_read_draft_only": True,
        "final_approval_must_be_human": True,
        "payment_release_must_be_human": True,
    }


def _load_legacy_fixture() -> dict[str, Any]:
    manifest = validate_v014_s15_p3_salary_boundary()
    interface = _read_json(LEGACY_INTERFACE_PATH)
    readiness = _read_jsonl(LEGACY_READINESS_PATH)
    summary = manifest["salary_boundary_summary"]
    if len(readiness) != 4 or summary.get("pending_review_item_count") != 16:
        raise ValueError("historical S15-P3 fixture drift")
    return {
        "fixture_validated": True,
        "historical_interface_contract_count": 1 if interface else 0,
        "historical_readiness_row_count": len(readiness),
        "historical_review_ref_count": summary["pending_review_item_count"],
        "dynamic_rows_are_authoritative": False,
        "four_readiness_rows_quarantined": True,
        "sixteen_review_refs_quarantined": True,
    }


def _build_interface_fields() -> list[dict[str, Any]]:
    return [
        {
            "interface_field_id": f"V014-S15P3-POST-FIELD-{index:03d}",
            "field_key": spec["field_key"],
            "visible_field_label": spec["label"],
            "fact_kind": spec["fact_kind"],
            "fact_kind_zh": FACT_KIND_LABELS[spec["fact_kind"]],
            "source_column_ref": f"V014-S15P2-POST-COLUMN-{index:03d}",
            "current_source_status": "pending_authoritative_binding",
            "value_available": False,
            "readable_after_authoritative_binding": True,
            "salary_calculation_input_allowed": False,
            "bonus_approval_input_allowed": False,
            "payroll_export_input_allowed": False,
        }
        for index, spec in enumerate(FIELD_SPECS, 1)
    ]


def _build_interface(fields: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v014.s15_p3.post_remediation.fact_output_interface.v1",
        "record_type": "public_safe_salary_fact_interface_contract",
        "boundary_version": BOUNDARY_VERSION,
        "interface_mode": "schema_only_no_records",
        "field_count": len(fields),
        "fields": fields,
        "source_performance_fact_row_count": 0,
        "payload_record_count": 0,
        "payload_records": [],
        "project_reference_count": 0,
        "employee_reference_count": 0,
        "salary_numeric_value_count": 0,
        "live_read_enabled": False,
        "api_endpoint_created": False,
        "connector_enabled": False,
        "file_export_created": False,
        "scheduled_sync_enabled": False,
        "external_write_enabled": False,
        "raw_layer_write_allowed": False,
        "final_approval_must_be_human": True,
        "payment_release_must_be_human": True,
    }


def _build_read_draft(fields: list[dict[str, Any]]) -> dict[str, Any]:
    mappings = [
        {
            "mapping_id": f"V014-S15P3-POST-MAP-{index:03d}",
            "source_field_key": row["field_key"],
            "visible_field_label": row["visible_field_label"],
            "future_target_slot": f"performance_fact.{row['field_key']}",
            "current_mapping_status": "defined_but_value_unavailable",
            "automatic_compensation_use_allowed": False,
        }
        for index, row in enumerate(fields, 1)
    ]
    return {
        "schema_version": "kmfa.v014.s15_p3.post_remediation.future_salary_read_draft.v1",
        "record_type": "public_safe_future_salary_read_draft",
        "draft_count": 1,
        "field_mapping_count": len(mappings),
        "field_mappings": mappings,
        "current_status": "draft_blocked_no_authoritative_fact_rows",
        "readiness_record_count": 0,
        "readiness_records": [],
        "project_reference_count": 0,
        "employee_reference_count": 0,
        "salary_numeric_value_count": 0,
        "future_read_enabled": False,
        "salary_calculation_allowed": False,
        "bonus_approval_allowed": False,
        "payroll_export_allowed": False,
        "final_compensation_decision_allowed": False,
        "final_payment_allowed": False,
        "payment_execution_allowed": False,
    }


def _build_human_boundaries() -> list[dict[str, Any]]:
    return [
        {
            "checkpoint_id": f"V014-S15P3-POST-HUMAN-{index:03d}",
            "checkpoint_key": key,
            "visible_label": HUMAN_CHECKPOINT_LABELS[key],
            "sequence": index,
            "human_action_required": True,
            "current_status": "not_performed",
            "automatic_execution_allowed": False,
            "business_record_created": False,
            "approval_or_release_result_count": 0,
        }
        for index, key in enumerate(HUMAN_CHECKPOINT_KEYS, 1)
    ]


def _render_html(
    fields: list[dict[str, Any]],
    draft: dict[str, Any],
    boundaries: list[dict[str, Any]],
) -> str:
    field_rows = "".join(
        "<tr>"
        f"<td>{html.escape(row['visible_field_label'])}</td>"
        f"<td>{html.escape(row['fact_kind_zh'])}</td>"
        "<td>待权威绑定</td><td>不可用于薪资计算</td>"
        "</tr>"
        for row in fields
    )
    boundary_rows = "".join(
        "<tr>"
        f"<td>{row['sequence']}</td><td>{html.escape(row['visible_label'])}</td>"
        "<td>必须人工</td><td>未执行</td>"
        "</tr>"
        for row in boundaries
    )
    buttons = "".join(
        f'<button type="button" data-field-button="{row["field_key"]}">'
        f'{html.escape(row["visible_field_label"])}</button>'
        for row in fields
    )
    panels = "".join(
        f'<section data-field-panel="{row["field_key"]}" hidden>'
        f'<div class="panel-head"><div><span>接口字段 {index}/6</span>'
        f'<h3>{html.escape(row["visible_field_label"])}</h3></div>'
        '<span class="tag blocked">值不可用</span></div>'
        '<dl><div><dt>来源状态</dt><dd>待权威绑定</dd></div>'
        '<div><dt>未来可读</dt><dd>绑定后</dd></div>'
        '<div><dt>当前记录</dt><dd>0</dd></div></dl>'
        f'<div class="reason">字段类型：{html.escape(row["fact_kind_zh"])}；当前只登记结构，不包含业务值。</div>'
        '<div class="limit">不得用于工资计算、奖金审批、薪资导出或最终发放。</div>'
        '</section>'
        for index, row in enumerate(fields, 1)
    )
    links = "".join(
        f'<a data-dependency-link="{link_id}" href="{href}">{label}</a>'
        for link_id, (href, label) in DEPENDENCY_LINKS.items()
    )
    labels = json.dumps(FIELD_LABELS, ensure_ascii=False, sort_keys=True)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>KMFA 工资项目边界工作台</title>
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
    .draft{{padding:16px;display:grid;grid-template-columns:repeat(3,1fr);gap:12px}}.draft div{{border-left:3px solid #7fc5b2;padding-left:10px}}.draft span{{display:block;font-size:12px;color:#687b76}}.draft strong{{display:block;margin-top:2px}}
    .workspace{{display:grid;grid-template-columns:220px 1fr}}.field-buttons{{padding:14px;background:#f3f6f5;border-right:1px solid #cad6d3}}
    .field-buttons button{{width:100%;background:transparent;border:1px solid transparent;text-align:left;padding:9px;border-radius:4px;font:inherit}}
    .field-buttons button.active{{background:#fff;border-color:#60af9a;color:#087258;font-weight:700}}.panel{{padding:18px 20px}}
    .panel-head{{display:flex;justify-content:space-between;gap:20px;align-items:flex-start}}.panel-head span:first-child{{font-size:12px;color:#6b7d78}}
    dl{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}}dl div{{border-left:3px solid #7fc5b2;padding-left:10px}}dt{{font-size:12px;color:#6b7d78}}dd{{margin:2px 0 0;font-weight:700}}
    .reason{{background:#f5f8f7;border:1px solid #cad6d3;padding:12px;margin-top:12px;overflow-wrap:anywhere}}.limit{{background:#fff1ef;border:1px solid #efaaa5;color:#9b332d;padding:12px;margin-top:10px}}
    .status{{padding:12px 16px;background:#f5f8f7;border-top:1px solid #cad6d3;color:#5d716b}}.status-links{{display:flex;gap:12px;flex-wrap:wrap;margin-top:8px}}.status a{{color:#007696;text-decoration:none}}
    footer{{color:#5f736e;font-size:13px}}button:focus-visible,a:focus-visible{{outline:3px solid #f0ba4d;outline-offset:2px}}
    @media(max-width:680px){{.nav{{display:block}}nav{{justify-content:flex-start;margin-top:12px}}h1{{font-size:27px}}.stats{{grid-template-columns:repeat(2,1fr)}}.stat:nth-child(2){{border-right:0}}.stat:nth-child(-n+2){{border-bottom:1px solid #cad6d3}}
      .draft{{grid-template-columns:1fr}}.workspace{{display:block}}.field-buttons{{border-right:0;border-bottom:1px solid #cad6d3;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:6px}}.field-buttons button{{text-align:center}}
      .panel{{padding:16px}}dl{{grid-template-columns:1fr}}.panel-head{{align-items:center}}.section-head{{align-items:flex-start}}}}
  </style>
</head>
<body data-active-field="">
  <header><div class="nav"><div class="brand"><div class="logo">KM</div><div><strong>KMFA 经营分析系统</strong><small>S15-P3 · 工资项目边界</small></div></div><nav>{links}</nav></div></header>
  <main class="page">
    <h1>工资项目边界工作台</h1>
    <p class="intro">仅登记未来可读的绩效事实接口结构；不展示项目、员工、金额、比率、工资或奖金记录。</p>
    <div class="badges"><span class="badge ok">Q4 / D</span><span class="badge blocked">NO_GO</span><span class="badge">仅结构草案</span></div>
    <div class="gate"><strong>门禁：</strong>接口记录为 0，未来读取未启用；最终审批和发放必须由人工完成。</div>
    <section class="stats"><div class="stat"><strong>1</strong><span>事实接口契约</span></div><div class="stat"><strong>6</strong><span>字段映射</span></div><div class="stat"><strong>0</strong><span>读取记录</span></div><div class="stat"><strong>4</strong><span>人工检查点</span></div></section>
    <section class="section"><div class="section-head"><h2>事实输出接口结构</h2><span class="tag blocked">记录 0</span></div><div class="table-scroll"><table><thead><tr><th>字段</th><th>类型</th><th>来源状态</th><th>当前用途</th></tr></thead><tbody>{field_rows}</tbody></table></div></section>
    <section class="section"><div class="section-head"><h2>未来工资系统读取草案</h2><span class="tag blocked">未启用</span></div><div class="draft"><div><span>草案状态</span><strong>无权威事实行，保持阻断</strong></div><div><span>读取方式</span><strong>仅结构定义</strong></div><div><span>映射 / 记录</span><strong>{draft['field_mapping_count']} / 0</strong></div></div></section>
    <section class="section"><div class="section-head"><h2>人工审批与发放边界</h2><span class="tag blocked">4 项均未执行</span></div><div class="table-scroll"><table><thead><tr><th>顺序</th><th>检查点</th><th>责任方式</th><th>当前状态</th></tr></thead><tbody>{boundary_rows}</tbody></table></div></section>
    <section class="section"><div class="section-head"><h2>接口字段检查</h2><span class="tag blocked">6 项值不可用</span></div><div class="workspace"><div class="field-buttons">{buttons}</div><div class="panel">{panels}</div></div>
      <div class="status"><span id="interaction-status">接口字段结构已加载。</span><div class="status-links">{links}</div></div></section>
    <footer>Stage 15 当前完成 S15-P1/P2/P3；Stage 15 整体复审、工资计算、奖金审批、薪资导出、最终发放、GitHub 上传、应用重装、正式报告、差异关闭和业务执行均未执行。</footer>
  </main>
  <script>
    const labels={labels};let actionSequence=0;
    function activate(id){{document.body.dataset.activeField=id;document.body.dataset.lastAction='field:'+id+':'+(++actionSequence);document.querySelectorAll('[data-field-button]').forEach(b=>b.classList.toggle('active',b.dataset.fieldButton===id));document.querySelectorAll('[data-field-panel]').forEach(p=>p.hidden=p.dataset.fieldPanel!==id);document.getElementById('interaction-status').textContent='已显示“'+labels[id]+'”接口字段；当前只有结构且不含业务值。';}}
    document.querySelectorAll('[data-field-button]').forEach(button=>button.addEventListener('click',()=>activate(button.dataset.fieldButton)));
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
    field_checks: list[dict[str, Any]] = []
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
                        "marker_visible": page.get_by_role("heading", name="工资项目边界工作台").is_visible(),
                        "quality_visible": "Q4 / D" in body and "NO_GO" in body,
                        "zero_records_visible": "读取记录" in body and "记录 0" in body,
                        "four_human_visible": "4 项均未执行" in body,
                        "stage_boundary_visible": "Stage 15 整体复审" in body,
                        "console_error_count": len(errors),
                        "no_horizontal_overflow": page.evaluate(
                            "document.documentElement.scrollWidth <= document.documentElement.clientWidth"
                        ),
                    }
                )
                for row in fields_for_browser():
                    field_key = row["field_key"]
                    page.locator(f'[data-field-button="{field_key}"]').click()
                    field_checks.append(
                        {
                            "mode": mode,
                            "field_key": field_key,
                            "passed": page.locator(f'[data-field-panel="{field_key}"]').is_visible()
                            and page.locator("body").get_attribute("data-active-field") == field_key
                            and row["visible_field_label"] in page.locator("#interaction-status").inner_text(),
                        }
                    )
                page.screenshot(
                    path=str(PRIVATE_SCREENSHOT_DIR / f"salary_boundary_{mode}.png"),
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
        "interface_field_interaction_checks": field_checks,
        "dependency_link_http_checks": http_checks,
        "dependency_navigation_checks": navigation_checks,
    }
    if not (
        len(viewport_checks) == 2
        and all(
            row["marker_visible"]
            and row["quality_visible"]
            and row["zero_records_visible"]
            and row["four_human_visible"]
            and row["stage_boundary_visible"]
            and row["console_error_count"] == 0
            and row["no_horizontal_overflow"]
            for row in viewport_checks
        )
        and len(field_checks) == 12
        and all(row["passed"] for row in field_checks)
        and len(http_checks) == 4
        and all(row["passed"] for row in http_checks)
        and len(navigation_checks) == 4
        and all(row["passed"] for row in navigation_checks)
    ):
        result["status"] = "FAIL"
    _write_json(PRIVATE_BROWSER_PATH, result)
    return result


def fields_for_browser() -> list[dict[str, Any]]:
    return _build_interface_fields()


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
        raise RuntimeError("S15-P3 browser validation failed")
    helper = p2.p1.s14_review.p1.s13_review.p1.s12_review.p1.s11_home
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
        raise RuntimeError("S15-P3 HTML audit failed")
    if current["pass_count"] != current["control_row_count"]:
        raise RuntimeError("S15-P3 HTML audit incomplete")
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
        "interface_field_interaction_check_count": len(browser["interface_field_interaction_checks"]),
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
        "fact_output_interface_schema_allowed": True,
        "future_salary_read_draft_allowed": True,
        "human_boundary_registration_allowed": True,
        "live_salary_system_integration_allowed": False,
        "api_endpoint_allowed": False,
        "connector_allowed": False,
        "file_export_allowed": False,
        "scheduled_sync_allowed": False,
        "external_write_allowed": False,
        "salary_calculation_allowed": False,
        "bonus_approval_allowed": False,
        "payroll_export_allowed": False,
        "final_compensation_decision_allowed": False,
        "final_payment_allowed": False,
        "payment_execution_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
    }


def _phase_boundaries() -> dict[str, bool]:
    return {
        "s15_p2_dependency_included": True,
        "s15_p3_scope_included": True,
        "stage15_review_scope_included": False,
        "s16_scope_included": False,
        "github_upload_scope_included": False,
        "app_reinstall_scope_included": False,
        "formal_report_scope_included": False,
        "difference_closure_scope_included": False,
        "salary_calculation_scope_included": False,
        "bonus_approval_scope_included": False,
        "payroll_export_scope_included": False,
        "final_compensation_scope_included": False,
        "final_payment_scope_included": False,
        "payment_execution_scope_included": False,
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
        "employee_or_staff_plaintext_committed": False,
        "business_amount_committed": False,
        "salary_or_bonus_value_committed": False,
        "synthetic_project_reference_committed": False,
        "payroll_payload_committed": False,
        "credential_or_secret_committed": False,
        "private_runtime_committed": False,
    }


def _acceptance_matrix(summary: dict[str, Any]) -> dict[str, Any]:
    checks = [
        ("s15_p2_current_dependency", summary["s15_p2_post_remediation_dependency_validated"]),
        ("taskpack_contract", summary["taskpack_contract_validated"]),
        ("legacy_fixture", summary["historical_s15_p3_fixture_validated"]),
        ("legacy_rows_quarantined", summary["historical_four_readiness_rows_quarantined"]),
        ("interface_contract", summary["fact_output_interface_contract_count"] == 1),
        ("six_interface_fields", summary["fact_output_interface_field_count"] == 6),
        ("zero_source_rows", summary["source_performance_fact_row_count"] == 0),
        ("zero_payload_records", summary["interface_payload_record_count"] == 0),
        ("read_draft", summary["future_salary_read_draft_count"] == 1),
        ("six_mappings", summary["future_salary_field_mapping_count"] == 6),
        ("zero_readiness_records", summary["future_salary_readiness_record_count"] == 0),
        ("four_human_boundaries", summary["human_boundary_checkpoint_count"] == 4),
        ("zero_approvals", summary["human_approval_completed_count"] == 0),
        ("zero_salary_values", summary["salary_numeric_value_count"] == 0),
        ("raw_exact", summary["raw_snapshot_exact_match"]),
        ("raw_cross_phase", summary["raw_cross_phase_snapshot_exact_match"]),
        ("browser", summary["browser_status"] == "PASS"),
        ("quality_block", summary["decision"] == "NO_GO"),
        ("downstream_closed", not summary["stage15_review_performed"] and not summary["salary_calculation_performed"]),
        ("upload_deferred", not summary["github_upload_performed"]),
    ]
    rows = [
        {"check_id": f"V014-S15P3-POST-ACC-{index:03d}", "name": name, "status": "PASS" if passed else "FAIL"}
        for index, (name, passed) in enumerate(checks, 1)
    ]
    return {
        "schema_version": "kmfa.v014.s15_p3.post_remediation.acceptance_matrix.v1",
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
        INTERFACE_PATH,
        READ_DRAFT_PATH,
        HUMAN_BOUNDARY_PATH,
        MATRIX_PATH,
        GO_NO_GO_PATH,
        HTML_PATH,
        REPORT_PATH,
        TEST_RESULTS_PATH,
        RISK_REGISTER_PATH,
        ROLLBACK_PATH,
        METADATA_SUMMARY_PATH,
        METADATA_MANIFEST_PATH,
        METADATA_INTERFACE_PATH,
        METADATA_READ_DRAFT_PATH,
        METADATA_HUMAN_BOUNDARY_PATH,
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
        Path("KMFA/tools/check_v014_s15_p2_post_remediation_performance_review_list.py"),
        Path("KMFA/tools/v014_s15_p3_post_remediation_salary_boundary.py"),
        Path("KMFA/tools/check_v014_s15_p3_post_remediation_salary_boundary.py"),
        Path("KMFA/tests/test_v014_s15_p3_post_remediation_salary_boundary.py"),
    )
    return [path.as_posix() for path in artifact_paths + governance_paths + code_paths]


def _write_governance(generated_at: str) -> None:
    evidence_ref = MANIFEST_PATH.as_posix()
    _sync_assurance_snapshot_time(generated_at)
    _upsert_jsonl(
        DEVELOPMENT_EVENTS_PATH,
        {
            "event_id": "DEV-KMFA-20260711-V014-S15-P3-POST-REMEDIATION-SALARY-BOUNDARY",
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
            "interface_payload_record_count": 0,
            "future_salary_readiness_record_count": 0,
            "human_boundary_checkpoint_count": 4,
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
            "governance_stage_id": "SALES-PERFORMANCE-SALARY-BOUNDARY",
            "roadmap_stage_id": "S15",
            "roadmap_phase_id": ROADMAP_PHASE_ID,
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "acceptance_id": ACCEPTANCE_ID,
            "version": VERSION,
            "name": "v0.1.4 S15-P3 post-remediation salary boundary",
            "phase_goal": "reserve schema-only fact interface and human compensation boundary with zero records",
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
    return f"""# KMFA v0.1.4 S15-P3 修补后工资项目边界

## 结论

- 事实输出接口：{summary['fact_output_interface_contract_count']} 个，字段 {summary['fact_output_interface_field_count']} 个，记录 0。
- 未来工资系统读取草案：1 个，字段映射 6 个，读取记录 0。
- 人工检查点：4 项；已完成审批、发放放行和支付执行均为 0。
- live API、connector、文件导出、定时同步和外部写入：均未创建。
- 当前状态：Q4 / D / NO_GO / 3-9-2-1。

## 边界

1. 接口和读取草案只登记结构，不包含项目、员工、工资、奖金或支付记录。
2. S15-P2 当前事实行为 0，任何未来读取都保持禁用。
3. 事实质量、政策映射、最终薪酬和发放放行均必须人工处理。
4. 本 phase 不执行 Stage 15 整体复审、S16、上传、重装、正式报告或业务动作。
"""


def _render_test_results(summary: dict[str, Any]) -> str:
    return f"""# S15-P3 测试结果

- focused test / strict validator：最终复验结果见 manifest。
- v1.4 baseline：54/54 PASS。
- current HTML audit：{summary['current_html_pass_count']}/{summary['current_html_control_row_count']} PASS。
- desktop/mobile：2/2 PASS。
- 六字段交互：12/12 PASS。
- 依赖 HTTP / 真实导航：4/4 / 4/4 PASS。
- raw 前后/跨 S15-P2/current：exact match。
- 接口记录 / 未来读取记录 / 薪资数值：0 / 0 / 0。
"""


def _render_private_report(summary: dict[str, Any]) -> str:
    return f"""# S15-P3 私有差异记录

## 当前事实

- 原始文件：{summary['raw_source_file_count']}
- XLSX 容器：{summary['private_xlsx_container_count']}
- 可解析 / 不可解析：{summary['private_parseable_xlsx_count']} / {summary['private_unparseable_xlsx_count']}
- 可解析工作表：{summary['private_parseable_sheet_count']}
- 唯一候选：{summary['private_unique_candidate_sheet_count']}
- S15-P1 双次探针指纹不一致：{summary['private_probe_roundtrip_mismatch_count']}

## 当前差异

1. S15-P2 没有权威项目事实行或业务值，未来工资读取草案不能生成记录。
2. 接口只能登记六字段结构，不能关联项目或员工。
3. 四个人工检查点均未执行，不得形成工资、奖金或发放结论。

## 处理结论

- raw phase 前后、跨 S15-P2 和当前快照完全一致。
- 原始文件未修改、删除、移动、重命名、覆盖或写入。
- 最终 goal 多轮交叉验证仍无法对齐时，必须纳入全中文最终差异报告。
"""


def generate(*, final_validation: bool = False, write_governance: bool = True) -> dict[str, Any]:
    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    raw_helper = p2.p1.s14_review.p1.s13_review.p1.s12_review.p1.s11_project
    raw_before = raw_helper._raw_snapshot("before_v014_s15_p3_post_remediation_salary_boundary")
    dependency = _load_dependency()
    contract = _load_contract()
    legacy = _load_legacy_fixture()
    probe = _read_json(p2.p1.PRIVATE_PROBE_PATH)
    fields = _build_interface_fields()
    interface = _build_interface(fields)
    draft = _build_read_draft(fields)
    boundaries = _build_human_boundaries()
    _write_text(HTML_PATH, _render_html(fields, draft, boundaries))
    browser = _run_browser_review()
    raw_after = raw_helper._raw_snapshot("after_v014_s15_p3_post_remediation_salary_boundary")
    prior_raw = _read_json(p2.PRIVATE_RAW_AFTER_PATH)
    current_raw = raw_helper._raw_snapshot("current_v014_s15_p3_post_remediation_salary_boundary")
    normalize = raw_helper._normalize_raw
    raw_exact = normalize(raw_before) == normalize(raw_after)
    raw_cross = normalize(raw_before) == normalize(prior_raw) == normalize(current_raw)
    if not raw_exact or not raw_cross:
        raise RuntimeError("raw source changed during S15-P3")

    upstream = dependency["summary"]
    summary = {
        "schema_version": "kmfa.v014.s15_p3.post_remediation.summary.v1",
        "project_id": "KMFA",
        "stage_id": "S15",
        "phase_id": PHASE_ID,
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "version": VERSION,
        "status": STATUS,
        "decision": DECISION,
        "s15_p2_post_remediation_dependency_validated": True,
        "taskpack_contract_validated": True,
        "historical_s15_p3_fixture_validated": True,
        "historical_four_readiness_rows_quarantined": True,
        "historical_sixteen_review_refs_quarantined": True,
        "required_field_count": len(FIELD_KEYS),
        "s15_p2_field_review_item_count": upstream["field_review_item_count"],
        "s15_p2_performance_fact_row_count": upstream["performance_fact_row_count"],
        "fact_output_interface_contract_count": 1,
        "fact_output_interface_field_count": len(fields),
        "source_performance_fact_row_count": interface["source_performance_fact_row_count"],
        "interface_payload_record_count": interface["payload_record_count"],
        "project_reference_count": interface["project_reference_count"],
        "employee_reference_count": interface["employee_reference_count"],
        "future_salary_read_draft_count": draft["draft_count"],
        "future_salary_field_mapping_count": draft["field_mapping_count"],
        "future_salary_readiness_record_count": draft["readiness_record_count"],
        "salary_numeric_value_count": draft["salary_numeric_value_count"],
        "human_boundary_checkpoint_count": len(boundaries),
        "human_approval_completed_count": sum(row["current_status"] == "completed" for row in boundaries),
        "automatic_approval_count": 0,
        "payment_release_count": 0,
        "payment_execution_count": 0,
        "workbench_html_count": 1,
        "raw_source_file_count": probe["raw_source_file_count"],
        "private_xlsx_container_count": probe["private_xlsx_container_count"],
        "private_parseable_xlsx_count": probe["private_parseable_xlsx_count"],
        "private_unparseable_xlsx_count": probe["private_unparseable_xlsx_count"],
        "private_parseable_sheet_count": probe["private_parseable_sheet_count"],
        "private_unique_candidate_sheet_count": probe["private_unique_candidate_sheet_count"],
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
        "interface_field_interaction_check_count": browser["interface_field_interaction_check_count"],
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
        "s15_p3_performed": True,
        "stage15_review_performed": False,
        "salary_calculation_performed": False,
        "bonus_approval_performed": False,
        "payroll_export_performed": False,
        "final_compensation_decision_performed": False,
        "final_payment_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "formal_report_release_performed": False,
        "business_execution_performed": False,
    }
    matrix = _acceptance_matrix(summary)
    go_no_go = {
        "schema_version": "kmfa.v014.s15_p3.post_remediation.go_no_go.v1",
        "project_id": "KMFA",
        "stage_id": "S15",
        "phase_id": PHASE_ID,
        "decision": "NO_GO",
        "fact_output_interface_schema_allowed": True,
        "future_salary_read_draft_allowed": True,
        "human_boundary_registration_allowed": True,
        "live_salary_integration_allowed": False,
        "api_endpoint_allowed": False,
        "connector_allowed": False,
        "file_export_allowed": False,
        "salary_calculation_allowed": False,
        "bonus_approval_allowed": False,
        "payroll_export_allowed": False,
        "final_payment_allowed": False,
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
        "schema_version": "kmfa.v014.s15_p3.post_remediation.manifest.v1",
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
        "boundary_version": BOUNDARY_VERSION,
        "formula_id": FORMULA_ID,
        "parameter_ids": list(PARAMETER_IDS),
        "model_registry_key": MODEL_REGISTRY_KEY,
        "summary": summary,
        "fact_output_interface_contract": interface,
        "future_salary_read_draft": draft,
        "human_boundaries": boundaries,
        "acceptance_matrix": matrix,
        "go_no_go": go_no_go,
        "quality_gate": _quality_gate(),
        "phase_boundaries": _phase_boundaries(),
        "raw_boundary": _raw_boundary(),
        "public_repo_safety": _public_safety(),
        "browser_review": browser,
        "taskpack_contract": contract,
        "s15_p2_post_remediation_dependency_validated": True,
        "historical_s15_p3_fixture_validated": legacy["fixture_validated"],
        "historical_s15_p3_dynamic_rows_are_authoritative": False,
        "historical_four_readiness_rows_quarantined": legacy["four_readiness_rows_quarantined"],
        "historical_sixteen_review_refs_quarantined": legacy["sixteen_review_refs_quarantined"],
        "historical_fixture_counts": legacy,
        "validation_summary": validation_summary,
        "next_phase": "S15_STAGE_REVIEW",
        "next_required_step": (
            "下一轮仅执行 Stage 15 整体复审；不得执行 S16、工资奖金、GitHub upload、"
            "app reinstall、正式报告、差异关闭或业务执行。"
        ),
    }
    boundary_document = {
        "schema_version": "kmfa.v014.s15_p3.post_remediation.human_boundaries.v1",
        "checkpoint_count": len(boundaries),
        "checkpoints": boundaries,
    }
    diagnostic = {
        "schema_version": "kmfa.private.v014.s15_p3.salary_boundary_readiness.v1",
        "generated_at": generated_at,
        "raw_source_file_count": probe["raw_source_file_count"],
        "private_xlsx_container_count": probe["private_xlsx_container_count"],
        "private_parseable_sheet_count": probe["private_parseable_sheet_count"],
        "private_unique_candidate_sheet_count": probe["private_unique_candidate_sheet_count"],
        "private_probe_roundtrip_mismatch_count": probe["private_probe_roundtrip_mismatch_count"],
        "source_performance_fact_row_count": 0,
        "interface_payload_record_count": 0,
        "future_salary_readiness_record_count": 0,
        "project_reference_count": 0,
        "employee_reference_count": 0,
        "salary_numeric_value_count": 0,
        "human_boundary_checkpoint_count": 4,
        "legacy_readiness_rows_quarantined": 4,
        "legacy_review_refs_quarantined": 16,
        "raw_snapshot_exact_match": raw_exact,
        "raw_cross_phase_snapshot_exact_match": raw_cross,
    }
    for path, value in (
        (SUMMARY_PATH, summary),
        (MANIFEST_PATH, manifest),
        (INTERFACE_PATH, interface),
        (READ_DRAFT_PATH, draft),
        (HUMAN_BOUNDARY_PATH, boundary_document),
        (MATRIX_PATH, matrix),
        (GO_NO_GO_PATH, go_no_go),
        (METADATA_SUMMARY_PATH, summary),
        (METADATA_MANIFEST_PATH, manifest),
        (METADATA_INTERFACE_PATH, interface),
        (METADATA_READ_DRAFT_PATH, draft),
        (METADATA_HUMAN_BOUNDARY_PATH, boundary_document),
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
        """# S15-P3 风险登记

| 风险 | 控制 | 状态 |
|---|---|---|
| legacy 合成项目读取行回流 | 4 条读取行和 16 个复核引用只作历史夹具 | controlled |
| 接口契约被误读为 live 集成 | API、connector、导出、同步和外部写入全部为 false | controlled |
| 结构草案被用于工资奖金 | 事实行、读取记录和薪资数值均为 0 | controlled |
| 人工边界被自动化绕过 | 四个检查点均必须人工且未执行 | controlled |
| raw/private/secret 进入 Git | 快照、诊断与截图只写 ignored private runtime | controlled |
""",
    )
    _write_text(
        ROLLBACK_PATH,
        f"""# S15-P3 回滚计划

1. 回退本 phase 的本地 commit 和 {OUTPUT_DIR.as_posix()} 公开证据。
2. 删除 ignored private raw/diagnostic/browser evidence，不触碰原始目录。
3. 恢复 S15-P2 为当前治理入口；不执行 Stage 15 整体复审。
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
    manifest = generate(final_validation=args.final_validation, write_governance=not args.no_governance)
    summary = manifest["summary"]
    print(
        "S15-P3 post-remediation salary boundary: "
        f"fields={summary['fact_output_interface_field_count']} "
        f"interface_records={summary['interface_payload_record_count']} "
        f"readiness_records={summary['future_salary_readiness_record_count']} "
        f"human_checkpoints={summary['human_boundary_checkpoint_count']} "
        f"decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
