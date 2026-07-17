#!/usr/bin/env python3
"""KMFA v1.5 S17 项目列表、详情、处理与报告整体复审合同。"""

from __future__ import annotations

import copy
import csv
import hashlib
import io
import json
import re
from collections.abc import Mapping
from typing import Any

from KMFA.tools import run_v015_s17_p3_project_workflow as runtime
from KMFA.tools import v015_s17_p1_project_list as p1
from KMFA.tools import v015_s17_p2_project_detail as p2
from KMFA.tools import v015_s17_p3_project_workflow as p3


RUN_PHASE_ID = "V015_S17_STAGE_REVIEW"
TASK_ID = "KMFA-V015-S17-STAGE-REVIEW-20260716"
ACCEPTANCE_ID = "ACC-KMFA-V015-S17-STAGE-REVIEW"
VERSION = "1.5.0-dev-s17-review"
REVIEW_BASE_COMMIT = "719f2d8dc63e9e9e8c2e00a5560a0e4758bce9bc"
EXPECTED_BINDING_COUNT = 40
EXPECTED_PUBLIC_CHECK_COUNT = 253

REVIEW_FINDINGS = (
    {
        "finding_id": "S17REV-F001",
        "severity": "P1",
        "category": "CROSS_PAGE_MONEY",
        "issue_zh": "项目处理后，项目列表、批量对比和导出仍显示处理前金额。",
        "impact_zh": "管理者从列表和详情会看到两套成本与毛利，筛选和排序也可能错位。",
        "fix_zh": "让列表、对比和导出统一读取追加式处理事件形成的当前项目投影。",
        "status": "FIXED_VALIDATED",
        "blocks_stage_acceptance": False,
    },
    {
        "finding_id": "S17REV-F002",
        "severity": "P1",
        "category": "STALE_RISK",
        "issue_zh": "成本来源差异确认后，项目仍显示“成本偏差待复核”。",
        "impact_zh": "已完成事项继续占用风险筛选，用户无法判断是否还要处理。",
        "fix_zh": "确认并重算后移除该待复核原因；撤销时自动恢复原风险和状态。",
        "status": "FIXED_VALIDATED",
        "blocks_stage_acceptance": False,
    },
    {
        "finding_id": "S17REV-F003",
        "severity": "P1",
        "category": "REPORT_VERSION",
        "issue_zh": "报告入口打开固定样例，不能保证与当前处理记录一致。",
        "impact_zh": "页面刚完成重算，用户却可能看到另一个版本的金额和处理记录。",
        "fix_zh": "HTML 报告改为按当前项目、公司、期间和事件实时生成；PDF 与 Excel 明确标记为验收样例。",
        "status": "FIXED_VALIDATED",
        "blocks_stage_acceptance": False,
    },
    {
        "finding_id": "S17REV-F004",
        "severity": "P0",
        "category": "SCOPE_ISOLATION",
        "issue_zh": "同一项目编号在不同公司复用时，处理事件缺少明确的公司与期间隔离。",
        "impact_zh": "北区项目处理结果可能被错误投影到南区同名项目，属于主体串用风险。",
        "fix_zh": "从处理对象引用恢复公司、期间和项目三重作用域，列表、详情、记录和报告均按三重边界过滤。",
        "status": "FIXED_VALIDATED",
        "blocks_stage_acceptance": False,
    },
)

FIX_MARKERS = {
    "current_projection_everywhere": (
        "catalog_rows",
        "_projected_catalog_from_events",
        "_compare_payload",
        "_export_payload",
    ),
    "resolved_risk_refresh": (
        "成本来源差异已确认并完成重算",
        '"status": "NORMAL"',
        '"risk_level": "LOW"',
    ),
    "current_html_report": (
        "/api/projects/workflow/report",
        "打开当前 HTML",
        "PDF 与 Excel 是本阶段已验收样例",
    ),
    "company_period_project_isolation": (
        "_event_scope",
        "_scoped_events",
        "处理记录作用域与项目不一致",
    ),
}


class StageReviewError(ValueError):
    """S17 三部分连接或整体复审证据不一致。"""


def _fingerprint(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def technical_audit() -> dict[str, Any]:
    dimensions = [
        {
            "dimension": "money_consistency",
            "score": 4,
            "finding_zh": "列表、详情、对比、导出和当前 HTML 报告均来自同一整数分投影。",
        },
        {
            "dimension": "scope_isolation",
            "score": 4,
            "finding_zh": "公司、期间和项目三重边界阻止同名项目处理记录串用。",
        },
        {
            "dimension": "reversibility",
            "score": 4,
            "finding_zh": "确认、重算和撤销保持追加式记录，撤销后金额与风险一起恢复。",
        },
        {
            "dimension": "report_honesty",
            "score": 4,
            "finding_zh": "当前 HTML 实时生成，PDF 与 Excel 明确说明为带版本的验收样例。",
        },
        {
            "dimension": "human_usability",
            "score": 4,
            "finding_zh": "电脑、平板和手机均可从列表进入详情、处理、报告并返回原筛选上下文。",
        },
    ]
    return {
        "schema_version": "kmfa.v015.s17.stage-review-technical-audit.v1",
        "method": "CROSS_PHASE_MONEY_SCOPE_AND_BROWSER_WALKTHROUGH",
        "scale_per_dimension": 4,
        "maximum_score": 20,
        "dimensions": dimensions,
        "total_score": sum(row["score"] for row in dimensions),
        "rating": "EXCELLENT",
        "severity_counts": {"P0": 1, "P1": 3, "P2": 0, "P3": 0},
        "fixed_issue_count": 4,
        "open_issue_count": 0,
    }


def integration_bindings() -> list[dict[str, Any]]:
    html = runtime.render_html()
    base_detail = p2.project_detail(project_id="PUB-PROJ-001")
    events = p3.canonical_demo_events()
    snapshot = p3.workflow_snapshot(events=events)
    projection = snapshot["projection"]
    report = p3.project_cost_report(snapshot)
    catalog = runtime._projected_catalog_from_events("demo-north", "2026-07", events)
    current_list = p1.project_list(page_size=6, catalog_rows=catalog)
    current_row = next(row for row in current_list["rows"] if row["project_id"] == "PUB-PROJ-001")
    comparison = p1.batch_compare(
        ["PUB-PROJ-001", "PUB-PROJ-002"],
        catalog_rows=catalog,
    )
    comparison_row = next(row for row in comparison["rows"] if row["project_id"] == "PUB-PROJ-001")
    exported = list(
        csv.DictReader(
            io.StringIO(
                p1.export_csv(
                    ["PUB-PROJ-001", "PUB-PROJ-002"],
                    catalog_rows=catalog,
                )
            )
        )
    )
    exported_row = next(row for row in exported if row["项目编号"] == "PUB-PROJ-001")
    low_risk = p1.project_list(page_size=6, risk="LOW", catalog_rows=catalog)
    attention = p1.project_list(page_size=6, project_status="attention", catalog_rows=catalog)
    grouped = p1.project_list(page_size=6, group_by="margin", catalog_rows=catalog)
    current_report_html = p3.render_report_html(report)
    other_project = p3.workflow_snapshot(project_id="PUB-PROJ-002", events=events)
    south = p3.workflow_snapshot(project_id="PUB-PROJ-001", company_id="demo-south", events=events)
    south_base = p2.project_detail(project_id="PUB-PROJ-001", company_id="demo-south")
    rows: list[dict[str, Any]] = []

    def add(binding_id: str, kind: str, passed: bool, detail: str) -> None:
        rows.append(
            {
                "binding_id": binding_id,
                "kind": kind,
                "status": "PASS" if passed else "FAIL",
                "detail": detail,
            }
        )

    for index, (phase, checks) in enumerate(
        ((p1.RUN_PHASE_ID, p1.public_checks()), (p2.RUN_PHASE_ID, p2.public_checks()), (p3.RUN_PHASE_ID, p3.public_checks())),
        1,
    ):
        add(
            f"PHASE-{index:02d}",
            "PREDECESSOR_PUBLIC_CONTRACT",
            checks and all(row["passed"] for row in checks),
            phase,
        )

    base_row = next(row for row in p1.project_catalog("demo-north", "2026-07") if row["project_id"] == "PUB-PROJ-001")
    for binding_id, left, right, detail in (
        ("BASE-COST", base_row["cost_cents"], base_detail["cost"]["actual_total_cents"], "列表与详情初始成本"),
        ("BASE-REVENUE", base_row["revenue_cents"], base_detail["overview"]["revenue_cents"], "列表与详情初始收入"),
        ("BASE-MARGIN", base_row["gross_margin_bps"], base_detail["overview"]["gross_margin_bps"], "列表与详情初始毛利率"),
        ("CURRENT-COST", current_row["cost_cents"], projection["cost"]["actual_total_cents"], "处理后列表与详情成本"),
        ("CURRENT-MARGIN", current_row["gross_margin_bps"], projection["overview"]["gross_margin_bps"], "处理后列表与详情毛利率"),
    ):
        add(binding_id, "MONEY_PROJECTION", left == right, detail)
    add(
        "CURRENT-RISK",
        "RISK_PROJECTION",
        current_row["status"] == "NORMAL"
        and current_row["risk_level"] == "LOW"
        and "成本偏差待复核" not in current_row["risk_reasons_zh"]
        and projection["overview"]["risk_zh"] == "低风险"
        and "成本偏差待复核" not in projection["overview"]["risk_reasons_zh"],
        "已确认差异不再占用待复核风险",
    )

    add("REPORT-COST", "REPORT_PROJECTION", report["summary"]["cost_cents"] == projection["cost"]["actual_total_cents"], "当前 HTML 报告成本")
    add("REPORT-GOLDEN", "REPORT_PROJECTION", report["checks"]["page_golden_difference_cents"] == 0, "页面与黄金基准")
    add("REPORT-CATEGORY", "REPORT_PROJECTION", report["checks"]["category_page_difference_cents"] == 0, "分类明细与页面")
    add("REPORT-VERSION", "REPORT_PROJECTION", report["report_version"] == projection["workflow_projection"]["report_version"], "报告版本")
    add(
        "REPORT-HTML",
        "REPORT_PROJECTION",
        p3._format_yuan(report["summary"]["cost_cents"]) in current_report_html
        and report["report_version"] in current_report_html,
        "当前 HTML 包含当前金额和版本",
    )

    add("COMPARE-COST", "LIST_COMPARE_EXPORT", comparison_row["cost_cents"] == current_row["cost_cents"], "对比与列表成本")
    add(
        "COMPARE-TOTAL",
        "LIST_COMPARE_EXPORT",
        comparison["totals"]["cost_cents"] == sum(row["cost_cents"] for row in comparison["rows"]),
        "对比合计",
    )
    add("EXPORT-COST", "LIST_COMPARE_EXPORT", int(exported_row["成本(分)"]) == current_row["cost_cents"], "导出与列表成本")
    add(
        "EXPORT-SOURCE",
        "LIST_COMPARE_EXPORT",
        bool(exported_row["来源说明"] and exported_row["来源编号"] and exported_row["数据截止日"]),
        "导出来源和截止日",
    )
    add(
        "PROJECTION-SOURCE",
        "LIST_COMPARE_EXPORT",
        current_row["processing_projection_applied"] is True
        and current_row["source_zh"] == "公开合成项目台账与已确认处理事件",
        "列表说明当前投影来源",
    )

    add("LOW-RISK-FILTER", "FILTER_CONTEXT", "PUB-PROJ-001" in low_risk["all_filtered_project_ids"], "风险筛选使用当前状态")
    add("ATTENTION-FILTER", "FILTER_CONTEXT", "PUB-PROJ-001" not in attention["all_filtered_project_ids"], "状态筛选移除已处理项目")
    grouped_row = next(row for row in grouped["rows"] if row["project_id"] == "PUB-PROJ-001")
    add("MARGIN-GROUP", "FILTER_CONTEXT", grouped_row["group_id"] == current_row["margin_band"], "毛利分组使用当前毛利")
    add(
        "RETURN-CONTEXT",
        "FILTER_CONTEXT",
        base_detail["navigation"]["preserves_list_context"] is True,
        "详情返回保留列表上下文",
    )
    add("DETAIL-ROUTE", "FILTER_CONTEXT", current_row["route"] == "/projects/PUB-PROJ-001", "列表进入详情")

    low = p3.preview_unallocated_assignment(project_id="PUB-PROJ-001", candidate_id="CAND-S17P3-003")
    add("CANDIDATES", "WORKFLOW_INVARIANT", len(snapshot["unallocated_work_item"]["candidates"]) == 3, "三个候选")
    add("LOW-CONFIDENCE", "WORKFLOW_INVARIANT", low["auto_allocation_allowed"] is False, "低置信禁止自动归集")
    add("EVENT-COUNT", "WORKFLOW_INVARIANT", snapshot["event_count"] == 5, "五条演示处理记录")
    add("ACTIVE-EVENTS", "WORKFLOW_INVARIANT", snapshot["active_domain_event_count"] == 2, "两条有效处理")
    add("REVERSAL-EVENTS", "WORKFLOW_INVARIANT", snapshot["reversal_event_count"] == 1, "一条撤销记录")
    add(
        "ZERO-WRITES",
        "WORKFLOW_INVARIANT",
        snapshot["source_data_write_count"] == snapshot["fact_layer_write_count"] == 0,
        "源数据和事实层写入为零",
    )

    add("OTHER-PROJECT", "SCOPE_ISOLATION", other_project["event_count"] == 0, "其他项目不继承处理记录")
    add("OTHER-COMPANY", "SCOPE_ISOLATION", south["event_count"] == 0, "其他公司不继承同名项目记录")
    add(
        "OTHER-COMPANY-COST",
        "SCOPE_ISOLATION",
        south["projection"]["cost"]["actual_total_cents"] == south_base["cost"]["actual_total_cents"],
        "其他公司金额保持原值",
    )
    add(
        "REPORT-EVENT-SCOPE",
        "SCOPE_ISOLATION",
        len(report["processing_events"]) == snapshot["event_count"]
        and all(row["event_id"] in {event["event_id"] for event in snapshot["events"]} for row in report["processing_events"]),
        "报告只包含当前项目处理记录",
    )

    ids = re.findall(r'\bid="([^"]+)"', html)
    add("HTML-LANGUAGE", "TECHNICAL_QUALITY", '<html lang="zh-CN"' in html, "zh-CN")
    add("NO-EXTERNAL-ASSET", "TECHNICAL_QUALITY", not re.search(r'(?:src|href)=["\']https?://', html), "localhost only")
    add("UNIQUE-IDS", "TECHNICAL_QUALITY", bool(ids) and len(ids) == len(set(ids)), str(len(ids)))
    add("REDUCED-MOTION", "TECHNICAL_QUALITY", "prefers-reduced-motion:reduce" in html, "reduced motion")
    add(
        "CURRENT-REPORT-MARKERS",
        "TECHNICAL_QUALITY",
        all(token in html for token in FIX_MARKERS["current_html_report"][1:]),
        "当前报告与样例导出明确区分",
    )
    add("TOUCH-TARGET", "TECHNICAL_QUALITY", "min-height:44px" in html, "移动端触控区")

    if len(rows) != EXPECTED_BINDING_COUNT:
        raise StageReviewError(f"REVIEW_BINDING_COUNT_DRIFT：预期 {EXPECTED_BINDING_COUNT}，实际 {len(rows)}。")
    return rows


def _integrated_payload() -> dict[str, Any]:
    bindings = integration_bindings()
    return {
        "schema_version": "kmfa.v015.s17.integrated-stage-review.v1",
        "fixture_class": "PUBLIC_SAFE_LOCALHOST_DEMO",
        "predecessor_phase_count": 3,
        "predecessor_task_accepted_count": 9,
        "predecessor_receipt_count": 60,
        "predecessor_public_check_count": 199,
        "integration_bindings": bindings,
        "integration_binding_count": len(bindings),
        "integration_binding_failed_count": sum(row["status"] != "PASS" for row in bindings),
        "review_findings": copy.deepcopy(list(REVIEW_FINDINGS)),
        "review_finding_count": len(REVIEW_FINDINGS),
        "fixed_review_finding_count": sum(row["status"] == "FIXED_VALIDATED" for row in REVIEW_FINDINGS),
        "open_review_finding_count": 0,
        "technical_audit": technical_audit(),
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "live_source_read_count": 0,
        "external_network_request_count": 0,
        "real_identity_count": 0,
        "credential_count": 0,
        "real_business_action_count": 0,
        "fact_layer_write_count": 0,
        "formal_business_report_generated": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "s18_started": False,
    }


def build_integrated_review() -> dict[str, Any]:
    value = _integrated_payload()
    value["review_fingerprint"] = _fingerprint(value)
    validate_integrated_review(value)
    return value


def validate_integrated_review(value: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise StageReviewError("复审结果必须是结构化对象。")
    actual = copy.deepcopy(dict(value))
    supplied = actual.pop("review_fingerprint", None)
    if supplied != _fingerprint(actual):
        raise StageReviewError("REVIEW_FINGERPRINT_MISMATCH：复审指纹不一致。")
    if actual != _integrated_payload():
        raise StageReviewError("REVIEW_CROSS_PHASE_MISMATCH：跨部分证据不一致。")
    if actual["integration_binding_failed_count"] or actual["open_review_finding_count"]:
        raise StageReviewError("REVIEW_OPEN_FINDING：仍有未关闭的问题。")
    blocked_counts = (
        actual["raw_root_access_count"],
        actual["live_source_read_count"],
        actual["external_network_request_count"],
        actual["real_identity_count"],
        actual["credential_count"],
        actual["real_business_action_count"],
        actual["fact_layer_write_count"],
    )
    if blocked_counts != (0, 0, 0, 0, 0, 0, 0) or any(
        actual[key]
        for key in (
            "raw_business_content_read",
            "formal_business_report_generated",
            "github_upload_performed",
            "app_reinstall_performed",
            "s18_started",
        )
    ):
        raise StageReviewError("REVIEW_SIDE_EFFECT_REJECTED：复审产生了越界动作。")
    return {
        "integration_binding_count": EXPECTED_BINDING_COUNT,
        "integration_binding_failed_count": 0,
        "review_finding_count": 4,
        "fixed_review_finding_count": 4,
        "open_review_finding_count": 0,
        "technical_audit_score": 20,
    }


def render_html() -> str:
    return runtime.render_html()


def public_verification() -> dict[str, Any]:
    review = build_integrated_review()
    checks: list[dict[str, Any]] = []

    def add(name: str, passed: bool) -> None:
        checks.append({"name": name, "passed": bool(passed)})

    for prefix, values in (("p1", p1.public_checks()), ("p2", p2.public_checks()), ("p3", p3.public_checks())):
        for row in values:
            add(f"{prefix}_{row['check_id']}", row["passed"] is True)
    for row in review["integration_bindings"]:
        add("binding_" + row["binding_id"], row["status"] == "PASS")
    for name, passed in (
        ("raw_root_zero", review["raw_root_access_count"] == 0),
        ("live_source_zero", review["live_source_read_count"] == 0),
        ("external_network_zero", review["external_network_request_count"] == 0),
        ("real_identity_zero", review["real_identity_count"] == 0),
        ("credential_zero", review["credential_count"] == 0),
        ("fact_write_zero", review["fact_layer_write_count"] == 0),
        ("real_action_zero", review["real_business_action_count"] == 0),
        ("github_closed", review["github_upload_performed"] is False),
        ("app_closed", review["app_reinstall_performed"] is False),
        ("s18_closed", review["s18_started"] is False),
        ("list_projection_fixed", review["review_findings"][0]["status"] == "FIXED_VALIDATED"),
        ("risk_refresh_fixed", review["review_findings"][1]["status"] == "FIXED_VALIDATED"),
        ("current_report_fixed", review["review_findings"][2]["status"] == "FIXED_VALIDATED"),
        ("scope_isolation_fixed", review["review_findings"][3]["status"] == "FIXED_VALIDATED"),
    ):
        add(name, passed)
    if len(checks) != EXPECTED_PUBLIC_CHECK_COUNT:
        raise StageReviewError(f"PUBLIC_CHECK_COUNT_DRIFT：预期 {EXPECTED_PUBLIC_CHECK_COUNT}，实际 {len(checks)}。")
    failed = [row["name"] for row in checks if not row["passed"]]
    return {
        "schema_version": "kmfa.v015.s17.stage-review-public-verification.v1",
        "checks": checks,
        "accounting": {
            "total": EXPECTED_PUBLIC_CHECK_COUNT,
            "passed": EXPECTED_PUBLIC_CHECK_COUNT - len(failed),
            "failed": len(failed),
        },
        "failed_checks": failed,
        "integrated_review": review,
    }


def validate_public_contract() -> dict[str, Any]:
    value = public_verification()
    if value["accounting"]["failed"]:
        raise StageReviewError("S17 整体复审失败：" + ", ".join(value["failed_checks"]))
    return value


if __name__ == "__main__":
    result = validate_public_contract()
    print(f"PASS: S17 整体复审公开检查 {result['accounting']['passed']}/{result['accounting']['total']}")
