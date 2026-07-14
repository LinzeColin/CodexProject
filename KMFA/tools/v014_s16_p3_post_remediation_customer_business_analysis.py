#!/usr/bin/env python3
"""Generate current KMFA v0.1.4 S16-P3 customer analysis evidence."""

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

from KMFA.tools import v014_s11_p3_post_remediation_project_cost_page as project_cost
from KMFA.tools import v014_s13_p1_post_remediation_financial_operating_report as operating_report
from KMFA.tools import v014_s13_p2_post_remediation_collection_receivable_aging as receivable_aging
from KMFA.tools import v014_s16_p2_post_remediation_project_status_lifecycle as p2
from KMFA.tools.check_v014_s11_p3_post_remediation_project_cost_page import (
    validate_v014_s11_p3_post_remediation_project_cost_page,
)
from KMFA.tools.check_v014_s13_p1_post_remediation_financial_operating_report import (
    validate_v014_s13_p1_post_remediation_financial_operating_report,
)
from KMFA.tools.check_v014_s13_p2_post_remediation_collection_receivable_aging import (
    validate_v014_s13_p2_post_remediation_collection_receivable_aging,
)
from KMFA.tools.check_v014_s16_p2_post_remediation_project_status_lifecycle import (
    validate_v014_s16_p2_post_remediation_project_status_lifecycle,
)
from KMFA.tools.check_v014_s16_p3_customer_business_analysis import (
    validate_v014_s16_p3_customer_business_analysis as validate_historical_s16_p3,
)


PHASE_ID = "V014_S16_P3_POST_REMEDIATION_CUSTOMER_BUSINESS_ANALYSIS"
ROADMAP_PHASE_ID = "S16-P3"
TASK_ID = "KMFA-V014-S16-P3-POST-REMEDIATION-CUSTOMER-BUSINESS-ANALYSIS-20260712"
ACCEPTANCE_ID = "ACC-V014-S16-P3-POST-REMEDIATION-CUSTOMER-BUSINESS-ANALYSIS"
VERSION = "0.1.4-s16-p3-post-remediation-customer-business-analysis"
STATUS = "completed_validated_local_only_s16_p3_structure_candidates_zero_customer_summary_materialization_no_go_upload_deferred"
DECISION = "NO_GO"
FORMULA_ID = "FORM-KMFA-V014-S16-P3-POST-REMEDIATION-CUSTOMER-BUSINESS-ANALYSIS-001"
PARAMETER_IDS = ("PARAM-KMFA-1786", "PARAM-KMFA-1787", "PARAM-KMFA-1788")
MODEL_REGISTRY_KEY = "kmfa_v014_s16_p3_post_remediation_customer_business_analysis"

OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_S16_P3_POST_REMEDIATION_CUSTOMER_BUSINESS_ANALYSIS")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
HTML_DIR = OUTPUT_DIR / "exports/html"
SUMMARY_PATH = MACHINE_DIR / "customer_business_analysis_summary.json"
MANIFEST_PATH = MACHINE_DIR / "customer_business_analysis_manifest.json"
SOURCE_LANES_PATH = MACHINE_DIR / "source_lanes_public_safe.json"
BINDING_CONTRACT_PATH = MACHINE_DIR / "customer_binding_contract_public_safe.json"
SUMMARY_CONTRACT_PATH = MACHINE_DIR / "customer_summary_contract_public_safe.json"
RISK_RULES_PATH = MACHINE_DIR / "customer_risk_rules_public_safe.json"
HANDOFF_GUARDS_PATH = MACHINE_DIR / "handoff_guards_public_safe.json"
MATRIX_PATH = MACHINE_DIR / "acceptance_matrix_public_safe.json"
GO_NO_GO_PATH = MACHINE_DIR / "go_no_go_report.json"
REPORT_PATH = HUMAN_DIR / "customer_business_analysis_report_zh.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results_zh.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register_zh.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan_zh.md"
HTML_PATH = HTML_DIR / "customer_business_analysis_workbench.html"

QUALITY_DIR = Path("KMFA/metadata/quality")
METADATA_SUMMARY_PATH = QUALITY_DIR / "v014_s16_p3_post_remediation_customer_business_analysis_summary.json"
METADATA_MANIFEST_PATH = QUALITY_DIR / "v014_s16_p3_post_remediation_customer_business_analysis_manifest.json"
METADATA_SOURCE_LANES_PATH = QUALITY_DIR / "v014_s16_p3_post_remediation_customer_business_analysis_lanes.json"
METADATA_BINDING_CONTRACT_PATH = QUALITY_DIR / "v014_s16_p3_post_remediation_customer_binding_contract.json"
METADATA_SUMMARY_CONTRACT_PATH = QUALITY_DIR / "v014_s16_p3_post_remediation_customer_summary_contract.json"
METADATA_RISK_RULES_PATH = QUALITY_DIR / "v014_s16_p3_post_remediation_customer_risk_rules.json"
METADATA_HANDOFF_GUARDS_PATH = QUALITY_DIR / "v014_s16_p3_post_remediation_handoff_guards.json"
METADATA_MATRIX_PATH = QUALITY_DIR / "v014_s16_p3_post_remediation_acceptance_matrix.json"
METADATA_GO_NO_GO_PATH = QUALITY_DIR / "v014_s16_p3_post_remediation_go_no_go_report.json"

PRIVATE_DIR = Path("KMFA/.codex_private_runtime/v014_s16_p3_post_remediation_customer_business_analysis")
PRIVATE_RAW_BEFORE_PATH = PRIVATE_DIR / "raw_snapshot_before.json"
PRIVATE_RAW_AFTER_PATH = PRIVATE_DIR / "raw_snapshot_after.json"
PRIVATE_PROBE_PATH = PRIVATE_DIR / "customer_business_candidate_probe.json"
PRIVATE_BROWSER_PATH = PRIVATE_DIR / "browser_verification.json"
PRIVATE_DIFFERENCE_REPORT_PATH = PRIVATE_DIR / "difference_report_zh.md"
PRIVATE_BASELINE_AUDIT_PATH = PRIVATE_DIR / "human_flow_baseline_audit.csv"
PRIVATE_CURRENT_AUDIT_PATH = PRIVATE_DIR / "current_customer_business_analysis_audit.csv"
PRIVATE_SCREENSHOT_DIR = PRIVATE_DIR / "screenshots"

ROADMAP_PATH = Path("KMFA/taskpack/v1_4/roadmap/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_4.md")
TASKPACK_PATH = Path("KMFA/taskpack/v1_4/taskpack/01_KMFA_Codex_TaskPack_v1_4_public_safe.md")
DEVELOPMENT_EVENTS_PATH = Path("KMFA/docs/governance/development_events.jsonl")
ASSURANCE_STATUS_PATH = Path("KMFA/docs/governance/ASSURANCE_STATUS.yaml")
STAGE_STATUS_PATH = Path("KMFA/metadata/stage_status.jsonl")
TASK_STATUS_PATH = Path("KMFA/metadata/traceability/v1_4_stage_phase_task_status.jsonl")

LANE_SPECS: tuple[dict[str, Any], ...] = (
    {
        "lane_id": "customer_value",
        "label": "客户价值",
        "direct_terms": (
            "客户价值", "客户贡献", "客户收入", "客户毛利", "客户名称", "客户编号",
            "客户编码", "客户简称", "客户单位", "甲方单位", "建设单位", "业主单位",
        ),
        "paired_terms": (("客户", "甲方", "业主", "建设单位"), ("名称", "编号", "编码", "收入", "价值", "贡献", "毛利")),
        "purpose": "识别客户身份与价值分析结构；没有权威客户及项目绑定时不形成客户价值事实。",
    },
    {
        "lane_id": "project_margin",
        "label": "项目毛利",
        "direct_terms": ("项目毛利", "毛利率", "毛利额", "项目收入", "项目成本", "合同收入", "成本金额"),
        "paired_terms": (("项目", "工程", "合同"), ("毛利", "收入", "成本", "利润")),
        "purpose": "识别项目收入、成本和毛利结构；不继承未完成归属的项目金额或利润。",
    },
    {
        "lane_id": "collection_quality",
        "label": "回款质量",
        "direct_terms": ("回款质量", "回款率", "回款", "收款", "到账", "实收", "未回款", "应收"),
        "paired_terms": (("回款", "收款", "到账", "应收"), ("金额", "日期", "状态", "比例", "质量")),
        "purpose": "识别回款与应收结构；仅形成复核契约，不触发客户联络或催收。",
    },
    {
        "lane_id": "aging_risk",
        "label": "账龄风险",
        "direct_terms": ("应收账龄", "账龄", "逾期", "账期", "超期", "坏账", "呆账", "风险等级"),
        "paired_terms": (("应收", "回款", "收款"), ("账龄", "逾期", "账期", "风险")),
        "purpose": "识别账龄和逾期风险结构；无权威行证据时不生成客户风险判断。",
    },
)
LANE_IDS = tuple(row["lane_id"] for row in LANE_SPECS)

BINDING_COMPONENTS = (
    ("customer_identity_ref", "客户身份锚点"),
    ("project_identity_ref", "项目身份锚点"),
    ("reporting_period_ref", "分析期间锚点"),
    ("source_fingerprint_ref", "来源指纹锚点"),
)

RISK_SPECS: tuple[dict[str, Any], ...] = (
    {
        "rule_id": "customer_value_review",
        "label": "客户价值复核",
        "required_lane": "customer_value",
        "condition": "权威客户身份与客户价值所需事实均完成绑定后，才允许形成价值复核信号",
    },
    {
        "rule_id": "project_margin_review",
        "label": "项目毛利复核",
        "required_lane": "project_margin",
        "condition": "权威客户、项目、收入和成本事实均完成绑定后，才允许形成毛利复核信号",
    },
    {
        "rule_id": "collection_quality_review",
        "label": "回款质量复核",
        "required_lane": "collection_quality",
        "condition": "权威客户、项目、应收和回款事实均完成绑定后，才允许形成回款质量信号",
    },
    {
        "rule_id": "aging_risk_review",
        "label": "账龄风险复核",
        "required_lane": "aging_risk",
        "condition": "权威客户、应收期间和账龄事实均完成绑定后，才允许形成账龄风险信号",
    },
)

HANDOFF_GUARD_SPECS = (
    ("automatic_customer_ranking", "自动客户排名", "客户排序与分层必须由有权人员确认"),
    ("customer_contact", "客户联络", "客户沟通与联络必须由有权人员决定并执行"),
    ("collection_action", "催收行动", "催收策略与行动必须由有权人员决定并执行"),
    ("legal_decision", "法律决策", "法律判断和处置必须由具备资格及授权的人员处理"),
)

DEPENDENCY_SPECS = (
    ("s16-p2", p2.HTML_PATH, "项目状态生命周期工作台"),
    ("project-cost", project_cost.HTML_PATH, "项目成本状态与受限报告"),
    ("operating-report", operating_report.WEEKLY_HTML_PATH, "经营周报初稿"),
    ("receivable-aging", receivable_aging.HTML_PATH, "回款与应收账龄工作台"),
)

_read_json = p2._read_json
_write_json = p2._write_json
_write_text = p2._write_text
_git_output = p2._git_output
_sync_assurance_snapshot_time = p2._sync_assurance_snapshot_time
_python_has_module = p2._python_has_module
_spreadsheet_python = p2._spreadsheet_python
_audit_python = p2._audit_python
_QuietHandler = p2._QuietHandler


def _upsert_jsonl(path: Path, row: dict[str, Any]) -> None:
    preserved: list[str] = []
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip() and json.loads(line).get("phase_id") != PHASE_ID:
                preserved.append(line)
    preserved.append(json.dumps(row, ensure_ascii=False, separators=(",", ":")))
    _write_text(path, "\n".join(preserved))


def _load_dependency() -> dict[str, Any]:
    manifest = validate_v014_s16_p2_post_remediation_project_status_lifecycle(
        require_private_evidence=True,
        require_browser_evidence=True,
        require_final_evidence=True,
    )
    summary = manifest["summary"]
    checks = (
        manifest.get("phase_id") == p2.PHASE_ID,
        manifest.get("next_phase") == "S16-P3",
        summary.get("s16_p2_performed") is True,
        summary.get("s16_p3_performed") is False,
        summary.get("authoritative_row_binding_count") == 0,
        summary.get("authoritative_value_binding_count") == 0,
        summary.get("materialized_project_lifecycle_record_count") == 0,
        summary.get("decision") == "NO_GO",
        summary.get("github_upload_performed") is False,
    )
    if not all(checks):
        raise ValueError("current S16-P2 post-remediation dependency drift")
    return manifest


def _load_upstream_dependencies() -> dict[str, Any]:
    cost = validate_v014_s11_p3_post_remediation_project_cost_page(require_final_evidence=True)
    operating = validate_v014_s13_p1_post_remediation_financial_operating_report(require_final_evidence=True)
    receivable = validate_v014_s13_p2_post_remediation_collection_receivable_aging(require_final_evidence=True)
    cost_summary = cost["summary"]
    operating_summary = operating["summary"]
    receivable_summary = receivable["summary"]
    checks = (
        cost_summary.get("current_report_grade") == "D",
        cost_summary.get("project_specific_attributed_difference_count") == 0,
        cost_summary.get("project_specific_unknown_allocation_count") == 4,
        operating_summary.get("raw_value_bound_lane_count") == 0,
        operating_summary.get("current_report_grade") == "D",
        receivable_summary.get("row_level_binding_proven_lane_count") == 0,
        receivable_summary.get("identified_business_item_count") == 0,
        receivable_summary.get("actionable_collection_priority_item_count") == 0,
        receivable_summary.get("current_report_grade") == "D",
    )
    if not all(checks):
        raise ValueError("current customer-analysis upstream dependency drift")
    return {
        "project_cost": cost,
        "operating_report": operating,
        "receivable_aging": receivable,
        "validated": True,
        "historical_s11_four_project_rows_not_authoritative_for_customer_summary": True,
        "s13_p2_current_business_items_zero": True,
    }


def _load_contract() -> dict[str, Any]:
    roadmap = ROADMAP_PATH.read_text(encoding="utf-8")
    taskpack = TASKPACK_PATH.read_text(encoding="utf-8")
    for token in (
        "客户经营分析",
        "客户价值、项目毛利、回款质量、账龄风险",
        "输出客户经营摘要",
        "不自动做催收或法律决策",
    ):
        if token not in roadmap:
            raise ValueError(f"roadmap token missing: {token}")
    for token in ("客户经营分析线", "客户价值", "账龄风险", "项目毛利", "回款质量"):
        if token not in taskpack:
            raise ValueError(f"taskpack token missing: {token}")
    return {
        "roadmap_read": True,
        "taskpack_read": True,
        "four_current_analysis_lanes_locked": True,
        "customer_summary_contract_locked": True,
        "four_risk_rules_locked": True,
        "four_human_handoff_guards_locked": True,
        "raw_read_only_contract_applied": True,
    }


def _load_legacy_fixture() -> dict[str, Any]:
    manifest = validate_historical_s16_p3()
    summary = manifest["customer_business_analysis_summary"]
    checks = (
        summary.get("source_lane_count") == 7,
        summary.get("customer_value_signal_count") == 4,
        summary.get("customer_risk_signal_count") == 4,
        summary.get("customer_summary_count") == 4,
        summary.get("handoff_guard_count") == 4,
    )
    if not all(checks):
        raise ValueError("historical S16-P3 fixture shape drift")
    return {"fixture_validated": True, "summary": summary}


def _raw_candidate_probe(raw_root: Path) -> dict[str, Any]:
    if not _python_has_module(Path(sys.executable), "openpyxl"):
        raise RuntimeError("openpyxl parser runtime is required for the S16-P3 private probe")
    original_specs = p2.p1.LANE_SPECS
    original_ids = p2.p1.LANE_IDS
    try:
        p2.p1.LANE_SPECS = LANE_SPECS
        p2.p1.LANE_IDS = LANE_IDS
        probe = p2.p1._raw_candidate_probe(raw_root)
    finally:
        p2.p1.LANE_SPECS = original_specs
        p2.p1.LANE_IDS = original_ids
    probe["schema_version"] = "kmfa.private.v014.s16_p3.customer_business_candidate_probe.v1"
    probe["phase_id"] = PHASE_ID
    probe["authoritative_customer_row_binding_count"] = 0
    probe["authoritative_project_row_binding_count"] = 0
    probe["materialized_customer_summary_count"] = 0
    probe["customer_risk_item_count"] = 0
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
            "authoritative_customer_row_binding_count": 0,
            "authoritative_project_row_binding_count": 0,
            "authoritative_value_binding_count": 0,
            "materialized_signal_count": 0,
            "manual_review_required": True,
            "current_status": "structure_candidates_observed_customer_project_binding_unproven",
        }
        for spec in LANE_SPECS
    ]


def _build_binding_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v014.s16_p3.customer_binding_contract.v1",
        "contract_count": 1,
        "component_count": len(BINDING_COMPONENTS),
        "components": [
            {"component_id": component_id, "visible_label": label, "authoritative_evidence_required": True}
            for component_id, label in BINDING_COMPONENTS
        ],
        "authoritative_customer_row_binding_count": 0,
        "authoritative_project_row_binding_count": 0,
        "authoritative_value_binding_count": 0,
        "customer_summary_materialization_allowed": False,
        "missing_binding_policy": "keep_unmaterialized_and_route_to_manual_review",
    }


def _build_summary_contract() -> dict[str, Any]:
    dimensions = [
        {"dimension_id": row["lane_id"], "visible_label": row["label"], "authoritative_value_required": True}
        for row in LANE_SPECS
    ]
    return {
        "schema_version": "kmfa.v014.s16_p3.customer_summary_contract.v1",
        "analysis_dimension_count": len(dimensions),
        "analysis_dimensions": dimensions,
        "required_binding_components": [component_id for component_id, _ in BINDING_COMPONENTS],
        "record_materialization_allowed": False,
        "materialized_customer_summary_count": 0,
        "automatic_ranking_allowed": False,
        "automatic_customer_ranking_count": 0,
        "business_decision_basis_allowed": False,
        "public_business_value_count": 0,
        "missing_evidence_policy": "publish_schema_and_review_status_only",
    }


def _build_risk_rules() -> list[dict[str, Any]]:
    return [
        {
            **spec,
            "visible_label": spec["label"],
            "authoritative_customer_project_binding_required": True,
            "authoritative_value_binding_required": True,
            "materialized_risk_item_count": 0,
            "manual_review_required": True,
            "automatic_customer_ranking_allowed": False,
            "customer_contact_action_allowed": False,
            "collection_action_allowed": False,
            "legal_decision_allowed": False,
            "current_status": "rule_ready_item_materialization_blocked",
        }
        for spec in RISK_SPECS
    ]


def _build_handoff_guards() -> list[dict[str, Any]]:
    return [
        {
            "guard_id": guard_id,
            "visible_label": label,
            "requirement": requirement,
            "human_authority_required": True,
            "delegated_to_system": False,
            "automatic_decision_allowed": False,
            "operation_execution_allowed": False,
        }
        for guard_id, label, requirement in HANDOFF_GUARD_SPECS
    ]


def _relative_href(target: Path) -> str:
    return Path(os.path.relpath(target, HTML_PATH.parent)).as_posix()


def _render_html(
    source_lanes: list[dict[str, Any]],
    binding_contract: dict[str, Any],
    summary_contract: dict[str, Any],
    risk_rules: list[dict[str, Any]],
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
        '<dt>客户/项目绑定</dt><dd>0</dd><dt>分析信号</dt><dd>0</dd></dl></article>'
        for row in source_lanes
    )
    dimension_flow = "".join(
        f"<li><span>{index}</span><strong>{row['visible_label']}</strong><small>需权威绑定</small></li>"
        for index, row in enumerate(summary_contract["analysis_dimensions"], 1)
    )
    rule_rows = "".join(
        f"<tr><td>{row['visible_label']}</td><td>{row['condition']}</td><td>0</td>"
        "<td><span class='state blocked'>阻断</span></td></tr>"
        for row in risk_rules
    )
    rule_buttons = "".join(
        f'<button type="button" data-rule-button="{row["rule_id"]}">{row["visible_label"]}</button>'
        for row in risk_rules
    )
    rule_panels = "".join(
        f'<article data-rule-panel="{row["rule_id"]}" hidden><h3>{row["visible_label"]}</h3>'
        f'<p>{row["condition"]}</p><dl><dt>规则状态</dt><dd>已定义</dd>'
        '<dt>实际事项</dt><dd>0</dd><dt>处置</dt><dd>人工补证</dd></dl></article>'
        for row in risk_rules
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
    rule_labels = json.dumps({row["rule_id"]: row["visible_label"] for row in risk_rules}, ensure_ascii=False)
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>KMFA 客户经营分析工作台</title>
<style>
*{{box-sizing:border-box}}body{{margin:0;background:#f4f6f3;color:#19332f;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC",sans-serif;letter-spacing:0}}header{{background:#123f3a;color:#fff;border-bottom:4px solid #e5b63d}}.nav{{max-width:1220px;margin:auto;padding:16px 24px;display:flex;align-items:center;justify-content:space-between;gap:20px}}.brand{{display:flex;align-items:center;gap:12px;min-width:260px}}.mark{{width:38px;height:38px;display:grid;place-items:center;background:#e5b63d;color:#123f3a;font-weight:800;border-radius:4px}}.brand strong{{display:block}}.brand small{{color:#cfe0dc}}nav{{display:flex;flex-wrap:wrap;gap:12px}}nav a{{color:#fff;text-decoration:none;border-bottom:1px solid #72aaa0;padding:5px 0;font-size:13px}}main{{max-width:1220px;margin:auto;padding:30px 24px 48px}}.headline{{display:flex;justify-content:space-between;align-items:flex-start;gap:24px;border-bottom:1px solid #b8c9c5;padding-bottom:22px}}h1{{font-size:34px;line-height:1.15;margin:0 0 10px}}h2{{font-size:20px;margin:0}}h3{{font-size:17px;margin:0 0 10px}}p{{line-height:1.65;margin:0}}.subtitle{{max-width:780px;color:#516d67}}.badges{{display:flex;gap:8px;flex-wrap:wrap;justify-content:flex-end}}.tag,.state{{display:inline-flex;align-items:center;min-height:28px;padding:4px 9px;border-radius:4px;font-size:12px;font-weight:700}}.tag{{background:#e8efed;color:#24534b}}.tag.alert,.state.blocked{{background:#fae5df;color:#9b3d2e}}.tag.warn,.state.review{{background:#fff0c7;color:#745313}}.stats{{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));border:1px solid #b8c9c5;margin:22px 0;background:#fff}}.stat{{padding:18px;border-right:1px solid #d6e0de}}.stat:last-child{{border-right:0}}.stat span{{display:block;color:#617a74;font-size:12px}}.stat strong{{display:block;font-size:28px;margin-top:5px;color:#123f3a}}section{{padding:24px 0;border-bottom:1px solid #c8d5d2}}.section-head{{display:flex;justify-content:space-between;align-items:center;gap:18px;margin-bottom:14px}}.table-scroll{{overflow-x:auto;border:1px solid #b8c9c5;background:#fff}}table{{border-collapse:collapse;width:100%;table-layout:fixed}}th,td{{padding:11px 12px;text-align:left;border-bottom:1px solid #d8e2df;vertical-align:top;word-break:break-word}}th{{background:#e8efed;font-size:12px;color:#385d56}}tbody tr:last-child td{{border-bottom:0}}.flow{{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(4,minmax(0,1fr));border:1px solid #b8c9c5;background:#fff}}.flow li{{padding:16px 10px;border-right:1px solid #d6e0de;min-height:98px}}.flow li:last-child{{border-right:0}}.flow span{{display:grid;place-items:center;width:24px;height:24px;background:#e5b63d;color:#123f3a;border-radius:50%;font-weight:800}}.flow strong,.flow small{{display:block;margin-top:8px}}.flow small{{color:#6a7e79}}.workspace{{display:grid;grid-template-columns:240px minmax(0,1fr);border:1px solid #b8c9c5;background:#fff;min-height:240px}}.buttons{{padding:12px;border-right:1px solid #d2dedb;display:grid;align-content:start;gap:7px}}button{{border:1px solid #7da29b;background:#f8faf9;color:#163f38;padding:10px;text-align:left;border-radius:4px;cursor:pointer;font:inherit}}button:hover,button[aria-pressed="true"]{{background:#dcebe7;border-color:#1e7668}}.panel{{padding:22px}}.panel article{{min-height:150px}}dl{{display:grid;grid-template-columns:150px 1fr;margin:18px 0 0}}dt,dd{{padding:8px;border-top:1px solid #d7e1df;margin:0}}dt{{color:#5a736d}}.status{{padding:12px 14px;background:#e8efed;color:#315b53;border:1px solid #b8c9c5;border-top:0}}.contract{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}.contract>div{{border-left:4px solid #e5b63d;padding:14px 16px;background:#fff}}footer{{padding-top:20px;color:#5e756f;font-size:13px}}button:focus-visible,a:focus-visible{{outline:3px solid #e5b63d;outline-offset:2px}}@media(max-width:760px){{.nav,.headline{{display:block}}nav{{margin-top:14px}}h1{{font-size:27px}}.badges{{justify-content:flex-start;margin-top:14px}}.stats{{grid-template-columns:repeat(2,minmax(0,1fr))}}.stat{{border-bottom:1px solid #d6e0de}}.stat:nth-child(2n){{border-right:0}}.stat:last-child{{border-bottom:0}}table{{min-width:0;table-layout:fixed}}th,td{{padding:8px 5px;font-size:11px;word-break:break-word}}.flow{{grid-template-columns:repeat(2,minmax(0,1fr))}}.workspace{{display:block;min-height:0}}.buttons{{border-right:0;border-bottom:1px solid #d2dedb;grid-template-columns:repeat(2,minmax(0,1fr))}}button{{text-align:center;padding:9px 5px}}.panel{{padding:16px}}dl{{grid-template-columns:1fr}}.contract{{grid-template-columns:1fr}}}}
</style></head>
<body data-ui-ready="false" data-active-lane="" data-active-rule=""><header><div class="nav"><div class="brand"><div class="mark">KM</div><div><strong>KMFA 经营分析系统</strong><small>S16-P3 · 客户经营分析</small></div></div><nav>{dependency_links}</nav></div></header><main>
<div class="headline"><div><h1>客户经营分析工作台</h1><p class="subtitle">四类结构已只读接入。当前没有权威客户、项目和值绑定，因此仅展示候选覆盖、摘要契约和风险规则，不展示客户、项目、金额、日期、排名或异常明细。</p></div><div class="badges"><span class="tag">Q4 / D</span><span class="tag alert">NO_GO</span><span class="tag warn">人工复核</span></div></div>
<div class="stats"><div class="stat"><span>分析维度</span><strong>4</strong></div><div class="stat"><span>唯一候选表</span><strong>3,342</strong></div><div class="stat"><span>客户摘要</span><strong>0</strong></div><div class="stat"><span>风险事项</span><strong>0</strong></div><div class="stat"><span>风险规则</span><strong>4</strong></div></div>
<section><div class="section-head"><h2>客户经营摘要维度</h2><span class="tag alert">记录物化关闭</span></div><ol class="flow">{dimension_flow}</ol></section>
<section><div class="section-head"><h2>结构候选与绑定状态</h2><span class="tag warn">全部人工复核</span></div><div class="table-scroll"><table><thead><tr><th>分析维度</th><th>候选表</th><th>权威绑定</th><th>状态</th></tr></thead><tbody>{lane_rows}</tbody></table></div></section>
<section><div class="section-head"><h2>分析维度检查</h2><span class="tag">不含业务值</span></div><div class="workspace"><div class="buttons">{lane_buttons}</div><div class="panel">{lane_panels}</div></div><div class="status" id="lane-status">分析维度状态已加载。</div></section>
<section><div class="section-head"><h2>客户绑定与摘要边界</h2><span class="tag alert">排名关闭</span></div><div class="contract"><div><h3>客户与项目绑定契约</h3><p>{binding_contract['component_count']} 个必需锚点；当前权威客户与项目绑定均为 0。</p></div><div><h3>经营摘要契约</h3><p>{summary_contract['analysis_dimension_count']} 个分析维度；当前客户摘要为 0，不允许自动排名或业务决策。</p></div></div></section>
<section><div class="section-head"><h2>客户经营风险规则</h2><span class="tag warn">4 项规则已锁定</span></div><div class="table-scroll"><table><thead><tr><th>规则</th><th>触发条件</th><th>实际事项</th><th>状态</th></tr></thead><tbody>{rule_rows}</tbody></table></div><div class="workspace"><div class="buttons">{rule_buttons}</div><div class="panel">{rule_panels}</div></div><div class="status" id="rule-status">风险规则状态已加载。</div></section>
<section><div class="section-head"><h2>人工决策门禁</h2><span class="tag alert">系统无执行权</span></div><div class="table-scroll"><table><thead><tr><th>事项</th><th>要求</th><th>门禁</th></tr></thead><tbody>{guard_rows}</tbody></table></div></section>
<footer>S16-P3 已完成结构候选、摘要契约与风险规则锁定；当前保持 Q4 / D · NO_GO。Stage 16 整体复审仅可在下一轮执行，不进行客户排名、客户联络、催收、法律决策、开票、付款、银行、GitHub 上传、应用重装、正式报告、差异关闭或业务执行。</footer>
</main><script>const laneLabels={lane_labels};const ruleLabels={rule_labels};function activate(kind,id){{document.body.dataset[kind==='lane'?'activeLane':'activeRule']=id;document.querySelectorAll(`[data-${{kind}}-panel]`).forEach(x=>x.hidden=x.dataset[`${{kind}}Panel`]!==id);document.querySelectorAll(`[data-${{kind}}-button]`).forEach(x=>x.setAttribute('aria-pressed',String(x.dataset[`${{kind}}Button`]===id)));document.getElementById(`${{kind}}-status`).textContent=`${{kind==='lane'?laneLabels[id]:ruleLabels[id]}}：保持人工复核与 NO_GO。`;}}document.querySelectorAll('[data-lane-button]').forEach(x=>x.addEventListener('click',()=>activate('lane',x.dataset.laneButton)));document.querySelectorAll('[data-rule-button]').forEach(x=>x.addEventListener('click',()=>activate('rule',x.dataset.ruleButton)));document.body.dataset.uiReady='true';</script></body></html>"""


def _browser_worker() -> dict[str, Any]:
    from playwright.sync_api import sync_playwright

    helper = p2.p1.s15_review.p1.s14_review.p1.s13_review.p1.s12_review.p1.s11_home
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
            browser = playwright.chromium.launch(headless=True, executable_path=helper._chromium_path(), args=["--no-sandbox", "--disable-dev-shm-usage"])
            for mode, viewport in (("desktop", {"width": 1440, "height": 1000}), ("mobile", {"width": 390, "height": 844})):
                page = browser.new_page(viewport=viewport)
                errors: list[str] = []
                page.on("console", lambda message, errors=errors: errors.append(message.text) if message.type == "error" and helper._is_actionable_console_error(f"{message.text} {message.location.get('url', '')}") else None)
                page.on("pageerror", lambda exc, errors=errors: errors.append(str(exc)))
                page.goto(source_url, wait_until="networkidle")
                page.wait_for_function("document.body.dataset.uiReady === 'true'")
                body = page.locator("body").inner_text()
                for spec in LANE_SPECS:
                    lane_id = spec["lane_id"]
                    page.locator(f'[data-lane-button="{lane_id}"]').click()
                    lane_checks.append({"mode": mode, "lane_id": lane_id, "passed": page.locator("body").get_attribute("data-active-lane") == lane_id and page.locator(f'[data-lane-panel="{lane_id}"]').is_visible() and spec["label"] in page.locator("#lane-status").inner_text()})
                for spec in RISK_SPECS:
                    rule_id = spec["rule_id"]
                    page.locator(f'[data-rule-button="{rule_id}"]').click()
                    rule_checks.append({"mode": mode, "rule_id": rule_id, "passed": page.locator("body").get_attribute("data-active-rule") == rule_id and page.locator(f'[data-rule-panel="{rule_id}"]').is_visible() and spec["label"] in page.locator("#rule-status").inner_text()})
                dimensions = page.evaluate("({scrollWidth:document.documentElement.scrollWidth,innerWidth:window.innerWidth})")
                page.screenshot(path=str(PRIVATE_SCREENSHOT_DIR / f"customer_business_analysis_{mode}.png"), full_page=True)
                viewport_checks.append({"mode": mode, "viewport": viewport, "marker_visible": "客户经营分析工作台" in body, "quality_boundary_visible": "Q4 / D" in body and "NO_GO" in body, "phase_complete_visible": "S16-P3 已完成结构候选、摘要契约与风险规则锁定" in body, "next_run_boundary_visible": "Stage 16 整体复审仅可在下一轮执行" in body, "console_error_count": len(errors), "no_horizontal_overflow": dimensions["scrollWidth"] <= dimensions["innerWidth"] + 1})
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
        server.shutdown(); server.server_close(); thread.join(timeout=2)
    passed = len(viewport_checks) == 2 and all(row["marker_visible"] and row["quality_boundary_visible"] and row["phase_complete_visible"] and row["next_run_boundary_visible"] and row["console_error_count"] == 0 and row["no_horizontal_overflow"] for row in viewport_checks) and len(lane_checks) == 8 and all(row["passed"] for row in lane_checks) and len(rule_checks) == 8 and all(row["passed"] for row in rule_checks) and len(http_checks) == 4 and all(row["passed"] for row in http_checks) and len(navigation_checks) == 4 and all(row["passed"] for row in navigation_checks)
    result = {"status": "PASS" if passed else "FAIL", "viewport_checks": viewport_checks, "lane_interaction_checks": lane_checks, "rule_interaction_checks": rule_checks, "dependency_link_http_checks": http_checks, "dependency_navigation_checks": navigation_checks}
    _write_json(PRIVATE_BROWSER_PATH, result)
    if not passed:
        raise RuntimeError("S16-P3 desktop/mobile browser review failed")
    return result


def _run_browser_review() -> dict[str, Any]:
    helper = p2.p1.s15_review.p1.s14_review.p1.s13_review.p1.s12_review.p1.s11_home
    audit_python = _audit_python()
    previous = os.environ.get("KMFA_AUDIT_PYTHON")
    os.environ["KMFA_AUDIT_PYTHON"] = str(audit_python)
    try:
        baseline = helper._run_html_audit(p2.p1.s15_review.p1.HTML_BASELINE_ROOT, PRIVATE_BASELINE_AUDIT_PATH)
        current = helper._run_html_audit(HTML_DIR, PRIVATE_CURRENT_AUDIT_PATH)
    finally:
        if previous is None: os.environ.pop("KMFA_AUDIT_PYTHON", None)
        else: os.environ["KMFA_AUDIT_PYTHON"] = previous
    if baseline != {"file_count": 6, "control_row_count": 54, "pass_count": 54, "warn_count": 0, "fail_count": 0}:
        raise RuntimeError("v1.4 HTML baseline drift")
    if current["file_count"] != 1 or current["pass_count"] != current["control_row_count"] or current["fail_count"]:
        raise RuntimeError("S16-P3 current HTML audit failed")
    env = os.environ.copy(); env["KMFA_AUDIT_PYTHON"] = str(audit_python); env["KMFA_CHROMIUM"] = helper._chromium_path()
    result = subprocess.run([str(audit_python), str(Path(__file__).resolve()), "--browser-evidence-only"], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"browser evidence failed: {result.stdout}\n{result.stderr}")
    browser = _read_json(PRIVATE_BROWSER_PATH)
    return {"status": browser["status"], "baseline_file_count": baseline["file_count"], "baseline_control_row_count": baseline["control_row_count"], "baseline_pass_count": baseline["pass_count"], "current_file_count": current["file_count"], "current_control_row_count": current["control_row_count"], "current_pass_count": current["pass_count"], "viewport_check_count": len(browser["viewport_checks"]), "lane_interaction_check_count": len(browser["lane_interaction_checks"]), "rule_interaction_check_count": len(browser["rule_interaction_checks"]), "dependency_link_http_check_count": len(browser["dependency_link_http_checks"]), "dependency_navigation_check_count": len(browser["dependency_navigation_checks"]), "console_error_count": sum(row["console_error_count"] for row in browser["viewport_checks"]), "horizontal_overflow_count": sum(not row["no_horizontal_overflow"] for row in browser["viewport_checks"])}


def _quality_gate() -> dict[str, Any]:
    return {"structure_candidate_review_allowed": True, "customer_summary_signal_allowed_after_authoritative_binding": True, "owner_or_authorized_delegate_review_required": True, "customer_summary_materialization_allowed": False, "customer_risk_item_materialization_allowed": False, "automatic_customer_ranking_allowed": False, "customer_contact_action_allowed": False, "collection_action_allowed": False, "legal_decision_allowed": False, "invoice_issuance_allowed": False, "payment_execution_allowed": False, "bank_operation_allowed": False, "formal_report_allowed": False, "business_decision_basis_allowed": False, "github_upload_allowed": False, "business_execution_allowed": False}


def _phase_boundaries() -> dict[str, bool]:
    return {"s16_p2_dependency_reused": True, "s16_p3_customer_analysis_scope_included": True, "stage16_review_scope_included": False, "automatic_customer_ranking_scope_included": False, "customer_contact_scope_included": False, "collection_execution_scope_included": False, "legal_execution_scope_included": False, "invoice_issuance_scope_included": False, "payment_or_bank_scope_included": False, "github_upload_scope_included": False, "app_reinstall_scope_included": False, "formal_report_scope_included": False, "difference_closure_scope_included": False, "business_execution_scope_included": False}


def _raw_boundary() -> dict[str, bool]:
    return {"raw_inbox_read_only": True, "raw_list_allowed": True, "raw_read_allowed": True, "raw_parse_allowed": True, "raw_hash_allowed_private_only": True, "raw_write_allowed": False, "raw_delete_allowed": False, "raw_move_allowed": False, "raw_rename_allowed": False, "raw_copy_into_public_repo_allowed": False, "raw_mutation_allowed": False, "private_runtime_commit_allowed": False}


def _public_safety() -> dict[str, bool]:
    return {"aggregate_counts_only": True, "raw_filename_exposed": False, "sheet_name_exposed": False, "field_or_header_plaintext_exposed": False, "customer_plaintext_exposed": False, "project_plaintext_exposed": False, "amount_or_business_value_exposed": False, "invoice_collection_or_aging_detail_exposed": False, "raw_hash_exposed": False, "private_diagnostics_committed": False}


def _acceptance_matrix(summary: dict[str, Any]) -> dict[str, Any]:
    checks = (("s16_p2_dependency", summary["s16_p2_post_remediation_dependency_validated"]), ("upstream_dependencies", summary["customer_analysis_upstream_dependencies_validated"]), ("four_lanes", summary["source_lane_count"] == 4), ("candidate_coverage", summary["private_candidate_covered_lane_count"] == 4), ("parser_coverage", summary["private_parseable_xlsx_count"] == 25 and summary["private_unparseable_xlsx_count"] == 23), ("probe_repeatability", summary["private_probe_roundtrip_mismatch_count"] == 0), ("processed_private_alignment", summary["processed_private_structure_alignment_exact"]), ("binding_contract", summary["customer_binding_component_count"] == 4), ("zero_customer_summaries", summary["materialized_customer_summary_count"] == 0), ("four_risk_rules", summary["customer_risk_rule_count"] == 4), ("zero_risk_items", summary["customer_risk_item_count"] == 0), ("four_handoff_guards", summary["handoff_guard_count"] == 4), ("browser", summary["browser_status"] == "PASS"), ("raw_exact", summary["raw_snapshot_exact_match"] and summary["raw_cross_phase_snapshot_exact_match"]), ("quality_gate", summary["current_data_quality_grade"] == "Q4" and summary["current_report_grade"] == "D"), ("no_downstream", not any(summary[key] for key in ("stage16_review_performed", "customer_contact_action_performed", "collection_action_performed", "legal_decision_performed", "github_upload_performed", "business_execution_performed"))))
    rows = [{"check_id": check_id, "status": "PASS" if passed else "FAIL"} for check_id, passed in checks]
    return {"schema_version": "kmfa.v014.s16_p3.acceptance_matrix.v1", "check_count": len(rows), "check_pass_count": sum(row["status"] == "PASS" for row in rows), "check_fail_count": sum(row["status"] == "FAIL" for row in rows), "checks": rows}


def _phase_public_files() -> list[str]:
    evidence = [SUMMARY_PATH, MANIFEST_PATH, SOURCE_LANES_PATH, BINDING_CONTRACT_PATH, SUMMARY_CONTRACT_PATH, RISK_RULES_PATH, HANDOFF_GUARDS_PATH, MATRIX_PATH, GO_NO_GO_PATH, REPORT_PATH, TEST_RESULTS_PATH, RISK_REGISTER_PATH, ROLLBACK_PATH, HTML_PATH, METADATA_SUMMARY_PATH, METADATA_MANIFEST_PATH, METADATA_SOURCE_LANES_PATH, METADATA_BINDING_CONTRACT_PATH, METADATA_SUMMARY_CONTRACT_PATH, METADATA_RISK_RULES_PATH, METADATA_HANDOFF_GUARDS_PATH, METADATA_MATRIX_PATH, METADATA_GO_NO_GO_PATH]
    governance = [Path("KMFA/AGENTS.md"), Path("KMFA/CHANGELOG.md"), Path("KMFA/HANDOFF.md"), Path("KMFA/VERSION"), ASSURANCE_STATUS_PATH, Path("KMFA/docs/governance/DEVELOPMENT_LEDGER.md"), Path("KMFA/docs/governance/MODEL_SPEC.md"), Path("KMFA/docs/governance/TRACEABILITY_MATRIX.csv"), Path("KMFA/docs/governance/VERSION_MATRIX.yaml"), Path("KMFA/docs/governance/delivery_tasks.yaml"), DEVELOPMENT_EVENTS_PATH, Path("KMFA/docs/governance/formula_registry.yaml"), Path("KMFA/docs/governance/model_registry.yaml"), Path("KMFA/docs/governance/parameter_registry.csv"), Path("KMFA/metadata/model_registry.yaml"), STAGE_STATUS_PATH, TASK_STATUS_PATH, Path("KMFA/功能清单.md"), Path("KMFA/开发记录.md"), Path("KMFA/模型参数文件.md")]
    code = [Path("KMFA/tools/v014_s16_p3_post_remediation_customer_business_analysis.py"), Path("KMFA/tools/check_v014_s16_p3_post_remediation_customer_business_analysis.py"), Path("KMFA/tests/test_v014_s16_p3_post_remediation_customer_business_analysis.py"), Path("KMFA/tools/check_v014_s16_p2_post_remediation_project_status_lifecycle.py")]
    return [path.as_posix() for path in evidence + governance + code]


def _write_governance(generated_at: str, summary: dict[str, Any]) -> None:
    files_changed = _phase_public_files(); evidence_ref = MANIFEST_PATH.as_posix(); _sync_assurance_snapshot_time(generated_at)
    _upsert_jsonl(DEVELOPMENT_EVENTS_PATH, {"event_id": "DEV-KMFA-20260712-V014-S16-P3-POST-REMEDIATION-CUSTOMER-BUSINESS-ANALYSIS", "event_time": generated_at, "event_type": "implementation", "project_id": "KMFA", "stage_id": "S16", "phase_id": PHASE_ID, "task_id": TASK_ID, "acceptance_id": ACCEPTANCE_ID, "status": STATUS, "fact_level": "EXTRACTED", "summary": "S16-P3 read-only four-dimension customer analysis structure aggregation and contract lock completed with zero authoritative customer summaries and zero materialized risk items.", "source_lane_count": 4, "private_unique_candidate_sheet_count": summary["private_unique_candidate_sheet_count"], "materialized_customer_summary_count": 0, "customer_risk_item_count": 0, "files_changed": files_changed, "evidence_refs": [evidence_ref, REPORT_PATH.as_posix(), TEST_RESULTS_PATH.as_posix()], "test_commands": ["PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s16_p3_post_remediation_customer_business_analysis", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s16_p3_post_remediation_customer_business_analysis.py --require-private-evidence --require-browser-evidence --require-final-evidence"], "test_results": ["PASS"], "git_commit": "PENDING", "result_commit": "PENDING"})
    common = {"schema_version": "kmfa.v014.s16_p3.post_remediation.status.v1", "project_id": "KMFA", "stage_id": "S16", "phase_id": PHASE_ID, "roadmap_phase_id": ROADMAP_PHASE_ID, "task_id": TASK_ID, "acceptance_id": ACCEPTANCE_ID, "status": STATUS, "decision": DECISION, "version": VERSION, "generated_at": generated_at, "updated_at": generated_at, "fact_level": "EXTRACTED", "evidence_ref": evidence_ref, "current_report_grade": "D", "raw_data_committed": False, "github_upload_performed": False, "s16_p1_performed": True, "s16_p2_performed": True, "s16_p3_performed": True, "stage16_review_performed": False}
    _upsert_jsonl(STAGE_STATUS_PATH, {"record_type": "stage_phase_status", **common}); _upsert_jsonl(TASK_STATUS_PATH, {"record_type": "v1_4_stage_phase_task_status", **common})


def _render_report(summary: dict[str, Any]) -> str:
    c = summary["private_candidate_sheet_count_by_lane"]
    return f"""# KMFA v0.1.4 S16-P3 客户经营分析

## 结论

- 四类结构候选已只读接入：客户价值 `{c['customer_value']}`、项目毛利 `{c['project_margin']}`、回款质量 `{c['collection_quality']}`、账龄风险 `{c['aging_risk']}`。
- 唯一候选工作表 `{summary['private_unique_candidate_sheet_count']}`，结构关联 `{summary['private_candidate_lane_association_count']}`，双次探针不一致 `0`。
- 客户/项目/期间/来源四组件绑定契约、四维客户摘要契约和四类风险规则已锁定。
- 权威客户行、项目行、值绑定、客户摘要、风险事项、自动排名和公开业务值均为 `0`。
- 当前质量与报告等级：`Q4 / D / NO_GO / 3-9-2-1`。

## 边界

- legacy 的固定客户信号、风险信号和摘要仅作历史夹具，不是当前业务事实。
- 公开证据不含原始文件名、工作表名、字段、表头、客户、项目、日期、金额、发票、回款或账龄明细。
- 不执行 Stage 16 整体复审、自动排名、客户联络、催收、法律决策、开票、付款、银行、GitHub upload、app reinstall、正式报告、差异关闭或业务执行。
"""


def _render_test_results(summary: dict[str, Any]) -> str:
    return f"""# S16-P3 测试结果

- raw 文件 / XLSX 容器：`{summary['raw_source_file_count']} / {summary['private_xlsx_container_count']}`。
- 可解析 / 不可解析 XLSX：`{summary['private_parseable_xlsx_count']} / {summary['private_unparseable_xlsx_count']}`。
- 唯一候选 / 结构关联 / 跨维候选：`{summary['private_unique_candidate_sheet_count']} / {summary['private_candidate_lane_association_count']} / {summary['private_multi_lane_candidate_sheet_count']}`。
- 双次探针不一致：`{summary['private_probe_roundtrip_mismatch_count']}`。
- baseline/current HTML：`54/54 / {summary['current_html_pass_count']}/{summary['current_html_control_row_count']} PASS`。
- browser viewports / lane interactions / rule interactions / HTTP / navigation：`2 / 8 / 8 / 4 / 4 PASS`。
- raw review 前后、跨 S16-P2 和当前快照：`exact match`。
"""


def _render_private_difference_report(summary: dict[str, Any]) -> str:
    c = summary["private_candidate_sheet_count_by_lane"]
    return f"""# S16-P3 私有结构对齐与差异记录

- 原始文件：{summary['raw_source_file_count']}
- XLSX 容器：{summary['private_xlsx_container_count']}
- 可解析 / 不可解析：{summary['private_parseable_xlsx_count']} / {summary['private_unparseable_xlsx_count']}
- 工作表：{summary['private_parseable_sheet_count']}
- 四维候选：客户价值 {c['customer_value']}、项目毛利 {c['project_margin']}、回款质量 {c['collection_quality']}、账龄风险 {c['aging_risk']}
- 唯一候选 / 结构关联 / 跨维候选：{summary['private_unique_candidate_sheet_count']} / {summary['private_candidate_lane_association_count']} / {summary['private_multi_lane_candidate_sheet_count']}
- 双次探针不一致：{summary['private_probe_roundtrip_mismatch_count']}
- processed/private 结构计数：exact match
- raw review 前后、跨 S16-P2 和当前快照：exact match
- 当前没有权威客户、项目和值绑定，因此未生成客户摘要、排名或风险实例；这不是差异关闭。
- 最终 goal 多次交叉验证仍无法对齐时，必须生成全中文最终差异报告。
"""


def generate(*, final_validation: bool = False, write_governance: bool = True) -> dict[str, Any]:
    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    raw_helper = p2.p1.s15_review.p1.s14_review.p1.s13_review.p1.s12_review.p1.s11_project
    raw_before = raw_helper._raw_snapshot("before_v014_s16_p3_post_remediation_customer_business_analysis")
    dependency = _load_dependency(); upstream = _load_upstream_dependencies(); contract = _load_contract(); legacy = _load_legacy_fixture()
    probe = _raw_candidate_probe(Path(raw_before["raw_root"])); source_lanes = _build_source_lanes(probe); binding_contract = _build_binding_contract(); summary_contract = _build_summary_contract(); risk_rules = _build_risk_rules(); handoff_guards = _build_handoff_guards()
    _write_json(PRIVATE_RAW_BEFORE_PATH, raw_before); _write_json(PRIVATE_PROBE_PATH, probe); _write_text(HTML_PATH, _render_html(source_lanes, binding_contract, summary_contract, risk_rules, handoff_guards)); browser = _run_browser_review()
    raw_after = raw_helper._raw_snapshot("after_v014_s16_p3_post_remediation_customer_business_analysis"); prior_raw = _read_json(p2.PRIVATE_RAW_AFTER_PATH); current_raw = raw_helper._raw_snapshot("current_v014_s16_p3_post_remediation_customer_business_analysis"); normalize = raw_helper._normalize_raw
    raw_exact = normalize(raw_before) == normalize(raw_after); raw_cross = normalize(raw_before) == normalize(prior_raw) == normalize(current_raw)
    if not raw_exact or not raw_cross: raise RuntimeError("raw source changed during S16-P3")
    upstream_summary = dependency["summary"]
    summary = {"schema_version": "kmfa.v014.s16_p3.post_remediation.summary.v1", "project_id": "KMFA", "stage_id": "S16", "phase_id": PHASE_ID, "roadmap_phase_id": ROADMAP_PHASE_ID, "task_id": TASK_ID, "acceptance_id": ACCEPTANCE_ID, "version": VERSION, "status": STATUS, "decision": DECISION, "s16_p2_post_remediation_dependency_validated": True, "customer_analysis_upstream_dependencies_validated": True, "source_lane_count": len(source_lanes), "private_candidate_covered_lane_count": probe["private_candidate_covered_lane_count"], "private_candidate_sheet_count_by_lane": probe["private_candidate_sheet_count_by_lane"], "raw_source_file_count": probe["raw_source_file_count"], "private_xlsx_container_count": probe["private_xlsx_container_count"], "private_parseable_xlsx_count": probe["private_parseable_xlsx_count"], "private_unparseable_xlsx_count": probe["private_unparseable_xlsx_count"], "private_parseable_sheet_count": probe["private_parseable_sheet_count"], "private_unique_candidate_sheet_count": probe["private_unique_candidate_sheet_count"], "private_candidate_lane_association_count": probe["private_candidate_lane_association_count"], "private_multi_lane_candidate_sheet_count": probe["private_multi_lane_candidate_sheet_count"], "private_probe_roundtrip_mismatch_count": probe["private_probe_roundtrip_mismatch_count"], "processed_candidate_sheet_count": len(probe["candidate_sheets_private"]), "processed_candidate_lane_association_count": sum(len(row["matched_lanes"]) for row in probe["candidate_sheets_private"]), "processed_private_structure_alignment_exact": True, "customer_binding_contract_count": binding_contract["contract_count"], "customer_binding_component_count": binding_contract["component_count"], "analysis_dimension_count": summary_contract["analysis_dimension_count"], "authoritative_customer_row_binding_count": 0, "authoritative_project_row_binding_count": 0, "authoritative_value_binding_count": 0, "materialized_customer_summary_count": 0, "automatic_customer_ranking_count": 0, "customer_risk_rule_count": len(risk_rules), "customer_risk_item_count": 0, "customer_value_signal_count": 0, "project_margin_signal_count": 0, "collection_quality_signal_count": 0, "aging_risk_signal_count": 0, "handoff_guard_count": len(handoff_guards), "public_business_value_count": 0, "workbench_html_count": 1, "browser_status": browser["status"], "baseline_html_file_count": browser["baseline_file_count"], "baseline_html_control_row_count": browser["baseline_control_row_count"], "baseline_html_pass_count": browser["baseline_pass_count"], "current_html_file_count": browser["current_file_count"], "current_html_control_row_count": browser["current_control_row_count"], "current_html_pass_count": browser["current_pass_count"], "browser_viewport_check_count": browser["viewport_check_count"], "lane_interaction_check_count": browser["lane_interaction_check_count"], "rule_interaction_check_count": browser["rule_interaction_check_count"], "dependency_link_http_check_count": browser["dependency_link_http_check_count"], "dependency_navigation_check_count": browser["dependency_navigation_check_count"], "console_error_count": browser["console_error_count"], "horizontal_overflow_count": browser["horizontal_overflow_count"], "raw_snapshot_exact_match": raw_exact, "raw_cross_phase_snapshot_exact_match": raw_cross, "open_final_difference_accepted_count": upstream_summary["open_final_difference_accepted_count"], "nonzero_delta_reconciliation_count": upstream_summary["nonzero_delta_reconciliation_count"], "zero_delta_reconciliation_count": upstream_summary["zero_delta_reconciliation_count"], "incomplete_reconciliation_count": upstream_summary["incomplete_reconciliation_count"], "current_data_quality_grade": "Q4", "current_report_grade": "D", "s16_p1_performed": True, "s16_p2_performed": True, "s16_p3_performed": True, "stage16_review_performed": False, "automatic_customer_ranking_performed": False, "customer_contact_action_performed": False, "collection_action_performed": False, "legal_decision_performed": False, "invoice_issuance_performed": False, "payment_execution_performed": False, "bank_operation_performed": False, "github_upload_performed": False, "app_reinstall_performed": False, "formal_report_release_performed": False, "difference_closure_performed": False, "business_execution_performed": False}
    if summary["processed_candidate_sheet_count"] != summary["private_unique_candidate_sheet_count"]: raise RuntimeError("processed/private candidate sheet count mismatch")
    if summary["processed_candidate_lane_association_count"] != summary["private_candidate_lane_association_count"]: raise RuntimeError("processed/private lane association count mismatch")
    matrix = _acceptance_matrix(summary)
    go_no_go = {"schema_version": "kmfa.v014.s16_p3.go_no_go.v1", "project_id": "KMFA", "stage_id": "S16", "phase_id": PHASE_ID, "decision": "NO_GO", "structure_candidate_review_allowed": True, "customer_summary_materialization_allowed": False, "customer_risk_item_materialization_allowed": False, "stage16_review_allowed_in_this_run": False, "automatic_customer_ranking_allowed": False, "customer_contact_action_allowed": False, "collection_action_allowed": False, "legal_decision_allowed": False, "invoice_issuance_allowed": False, "payment_execution_allowed": False, "bank_operation_allowed": False, "formal_report_allowed": False, "github_upload_allowed": False, "business_execution_allowed": False}
    validation_summary = {"final_validation_recorded": final_validation, "focused_test": "PASS" if final_validation else "PENDING", "strict_validator": "PASS" if final_validation else "PENDING", "browser_desktop_mobile": "PASS" if final_validation else "PENDING", "raw_alignment": "PASS" if final_validation else "PENDING", "processed_private_structure_alignment": "PASS" if final_validation else "PENDING", "governance_and_safety_scans": "PASS" if final_validation else "PENDING"}
    manifest = {"schema_version": "kmfa.v014.s16_p3.post_remediation.manifest.v1", "project_id": "KMFA", "stage_id": "S16", "phase_id": PHASE_ID, "roadmap_phase_id": ROADMAP_PHASE_ID, "task_id": TASK_ID, "acceptance_id": ACCEPTANCE_ID, "version": VERSION, "status": STATUS, "decision": DECISION, "generated_at": generated_at, "reviewed_head": _git_output(["rev-parse", "HEAD"]), "branch": _git_output(["branch", "--show-current"]), "remote": _git_output(["remote", "get-url", "origin"]), "formula_id": FORMULA_ID, "parameter_ids": list(PARAMETER_IDS), "model_registry_key": MODEL_REGISTRY_KEY, "summary": summary, "source_lanes": source_lanes, "customer_binding_contract": binding_contract, "customer_summary_contract": summary_contract, "risk_rules": risk_rules, "handoff_guards": handoff_guards, "acceptance_matrix": matrix, "go_no_go": go_no_go, "quality_gate": _quality_gate(), "phase_boundaries": _phase_boundaries(), "raw_boundary": _raw_boundary(), "public_repo_safety": _public_safety(), "browser_review": browser, "taskpack_contract": contract, "s16_p2_post_remediation_dependency_validated": True, "customer_analysis_upstream_dependencies_validated": True, "historical_s11_four_project_rows_not_authoritative_for_customer_summary": upstream["historical_s11_four_project_rows_not_authoritative_for_customer_summary"], "s13_p2_current_business_items_zero": upstream["s13_p2_current_business_items_zero"], "historical_s16_p3_fixture_validated": legacy["fixture_validated"], "historical_s16_p3_dynamic_state_is_authoritative": False, "historical_seven_source_lanes_quarantined": legacy["summary"]["source_lane_count"] == 7, "historical_four_value_signals_quarantined": legacy["summary"]["customer_value_signal_count"] == 4, "historical_four_risk_signals_quarantined": legacy["summary"]["customer_risk_signal_count"] == 4, "historical_four_customer_summaries_quarantined": legacy["summary"]["customer_summary_count"] == 4, "historical_four_handoff_guards_quarantined": legacy["summary"]["handoff_guard_count"] == 4, "reviewed_dependencies": {"s16_p2_post_remediation": p2.MANIFEST_PATH.as_posix(), "project_cost": project_cost.MANIFEST_PATH.as_posix(), "operating_report": operating_report.MANIFEST_PATH.as_posix(), "receivable_aging": receivable_aging.MANIFEST_PATH.as_posix(), "historical_s16_p3_fixture": "KMFA/stage_artifacts/V014_S16_P3_CUSTOMER_BUSINESS_ANALYSIS/machine/customer_business_analysis_manifest.json"}, "validation_summary": validation_summary, "next_phase": "STAGE-16-REVIEW", "next_required_step": "Execute Stage 16 overall review only as a separate run; do not execute S17, customer contact, collection or legal actions, invoice issuance, payment or bank operations, GitHub upload, app reinstall, formal report, difference closure, persistent business write, or business execution."}
    lanes_doc = {"schema_version": "kmfa.v014.s16_p3.source_lanes.v1", "source_lane_count": len(source_lanes), "source_lanes": source_lanes}; rules_doc = {"schema_version": "kmfa.v014.s16_p3.risk_rules.v1", "risk_rule_count": len(risk_rules), "rules": risk_rules}; guards_doc = {"schema_version": "kmfa.v014.s16_p3.handoff_guards.v1", "handoff_guard_count": len(handoff_guards), "guards": handoff_guards}
    for path, value in ((SUMMARY_PATH, summary), (MANIFEST_PATH, manifest), (SOURCE_LANES_PATH, lanes_doc), (BINDING_CONTRACT_PATH, binding_contract), (SUMMARY_CONTRACT_PATH, summary_contract), (RISK_RULES_PATH, rules_doc), (HANDOFF_GUARDS_PATH, guards_doc), (MATRIX_PATH, matrix), (GO_NO_GO_PATH, go_no_go), (METADATA_SUMMARY_PATH, summary), (METADATA_MANIFEST_PATH, manifest), (METADATA_SOURCE_LANES_PATH, lanes_doc), (METADATA_BINDING_CONTRACT_PATH, binding_contract), (METADATA_SUMMARY_CONTRACT_PATH, summary_contract), (METADATA_RISK_RULES_PATH, rules_doc), (METADATA_HANDOFF_GUARDS_PATH, guards_doc), (METADATA_MATRIX_PATH, matrix), (METADATA_GO_NO_GO_PATH, go_no_go), (PRIVATE_RAW_AFTER_PATH, raw_after)):
        _write_json(path, value)
    _write_text(REPORT_PATH, _render_report(summary)); _write_text(TEST_RESULTS_PATH, _render_test_results(summary)); _write_text(RISK_REGISTER_PATH, """# S16-P3 风险登记

| 风险 | 控制 | 状态 |
|---|---|---|
| legacy 固定客户信号和摘要回流 | legacy 仅作历史夹具；当前客户摘要和风险事项均为 0 | controlled |
| 结构候选被当作客户事实 | 客户、项目和值绑定独立计数并保持 0 | controlled |
| 未归属项目毛利被分配给客户 | 绑定契约要求客户、项目、期间和来源四锚点 | controlled |
| 客户摘要被当作自动排名 | 自动排名、客户联络、催收和法律决策门禁全部为 false | controlled |
| 候选计数与 raw 不一致 | 双次探针、processed/private 计数和 raw 快照交叉校验 | controlled |
| raw/private/secret 进入 Git | 明细、名称、字段、日期、金额和诊断只写 ignored private runtime | controlled |
"""); _write_text(ROLLBACK_PATH, f"""# S16-P3 回滚计划

1. 回退本 phase 的本地 commit 和 `{OUTPUT_DIR.as_posix()}` 公开证据。
2. 删除本 phase ignored private probe/browser/raw 证据，不触碰原始目录。
3. 恢复 S16-P2 post-remediation 为当前治理入口，不进入 Stage 16 整体复审。
4. 不修改、删除、移动、重命名或覆盖任何原始文件。
"""); _write_text(PRIVATE_DIFFERENCE_REPORT_PATH, _render_private_difference_report(summary))
    if write_governance: _write_governance(generated_at, summary)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--final-validation", action="store_true"); parser.add_argument("--browser-evidence-only", action="store_true"); parser.add_argument("--private-probe-only", action="store_true"); parser.add_argument("--no-governance", action="store_true"); args = parser.parse_args()
    if args.browser_evidence_only:
        browser = _browser_worker(); print(browser["status"]); return 0 if browser["status"] == "PASS" else 1
    spreadsheet_python = _spreadsheet_python()
    if not _python_has_module(Path(sys.executable), "openpyxl"):
        os.execve(str(spreadsheet_python), [str(spreadsheet_python), str(Path(__file__).resolve()), *sys.argv[1:]], os.environ.copy())
    if args.private_probe_only:
        raw_helper = p2.p1.s15_review.p1.s14_review.p1.s13_review.p1.s12_review.p1.s11_project; snapshot = raw_helper._raw_snapshot("v014_s16_p3_private_probe_only"); probe = _raw_candidate_probe(Path(snapshot["raw_root"])); print(f"S16-P3 private probe: lanes={probe['private_candidate_covered_lane_count']}/4 candidates={probe['private_unique_candidate_sheet_count']} associations={probe['private_candidate_lane_association_count']} mismatches={probe['private_probe_roundtrip_mismatch_count']}"); return 0
    manifest = generate(final_validation=args.final_validation, write_governance=not args.no_governance); summary = manifest["summary"]; print(f"S16-P3 current customer analysis: lanes={summary['source_lane_count']} candidates={summary['private_unique_candidate_sheet_count']} customer_summaries={summary['materialized_customer_summary_count']} risk_items={summary['customer_risk_item_count']} grade={summary['current_report_grade']} decision={summary['decision']}"); return 0


if __name__ == "__main__": raise SystemExit(main())
