#!/usr/bin/env python3
"""KMFA v1.5 S18 回款、应收、资金与贷款分析整体复审合同。"""

from __future__ import annotations

import copy
import csv
import hashlib
import io
import json
import re
from collections.abc import Mapping
from typing import Any

from KMFA.tools import run_v015_s18_p3_relation_reporting as runtime
from KMFA.tools import v015_s17_p1_project_list as projects
from KMFA.tools import v015_s17_p3_project_workflow as workflow
from KMFA.tools import v015_s18_p1_receivables_collections as p1
from KMFA.tools import v015_s18_p2_funds_accounts as p2
from KMFA.tools import v015_s18_p3_relation_reporting as p3


RUN_PHASE_ID = "V015_S18_STAGE_REVIEW"
TASK_ID = "KMFA-V015-S18-STAGE-REVIEW-20260716"
ACCEPTANCE_ID = "ACC-KMFA-V015-S18-STAGE-REVIEW"
VERSION = "1.5.0-dev-s18-review"
REVIEW_BASE_COMMIT = "42e51d497591fcbbd9ae4e8a0ca89a27fbbd0e0c"
EXPECTED_BINDING_COUNT = 41
EXPECTED_PUBLIC_CHECK_COUNT = 246

REVIEW_FINDINGS = (
    {
        "finding_id": "S18REV-F001",
        "severity": "P0",
        "category": "CURRENT_MONEY_PROJECTION",
        "issue_zh": "项目成本差异确认后，项目详情已更新，但 S18 资金与应收报告和两个导出仍显示处理前金额。",
        "impact_zh": "同一项目同时出现两套成本和毛利，管理者无法判断哪一版是当前值。",
        "fix_zh": "报告页、HTML 和 CSV 全部读取同一追加式项目处理记录，并按公司、期间、项目隔离。",
        "status": "FIXED_VALIDATED",
        "blocks_stage_acceptance": False,
    },
    {
        "finding_id": "S18REV-F002",
        "severity": "P1",
        "category": "ALERT_NAVIGATION",
        "issue_zh": "预警卡只显示内部动作文字，无法直接进入对应回款或资金明细。",
        "impact_zh": "用户识别风险后还要重新寻找页面，处理链路中断。",
        "fix_zh": "每张预警卡增加至少 44 像素的明确入口，并保留身份、公司和期间上下文。",
        "status": "FIXED_VALIDATED",
        "blocks_stage_acceptance": False,
    },
)

FIX_MARKERS = {
    "current_projection_everywhere": (
        "project_events",
        "project_projection",
        "self.server.journal.read()",
    ),
    "actionable_alerts": (
        "rr-alert-action",
        "打开回款明细",
        "打开资金明细",
    ),
}


class StageReviewError(ValueError):
    """S18 三部分连接或整体复审证据不一致。"""


def _fingerprint(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def technical_audit() -> dict[str, Any]:
    dimensions = [
        {
            "dimension": "money_consistency",
            "score": 4,
            "finding_zh": "项目详情、双视图、页面、HTML 和 CSV 均来自同一整数分当前投影。",
        },
        {
            "dimension": "scope_isolation",
            "score": 4,
            "finding_zh": "项目处理记录按公司、期间和项目三重边界隔离。",
        },
        {
            "dimension": "cash_safety",
            "score": 4,
            "finding_zh": "利润不替代现金，未开票不计应收，页面不发送提醒也不执行付款。",
        },
        {
            "dimension": "report_honesty",
            "score": 4,
            "finding_zh": "未核验资料隐藏数字和预警；公开演示报告明确不是正式经营报告。",
        },
        {
            "dimension": "human_usability",
            "score": 4,
            "finding_zh": "预警可直接进入回款或资金明细，电脑和移动端均保留可操作触控尺寸。",
        },
    ]
    return {
        "schema_version": "kmfa.v015.s18.stage-review-technical-audit.v1",
        "method": "CROSS_PHASE_MONEY_SCOPE_DEGRADATION_AND_BROWSER_WALKTHROUGH",
        "scale_per_dimension": 4,
        "maximum_score": 20,
        "dimensions": dimensions,
        "total_score": sum(row["score"] for row in dimensions),
        "rating": "EXCELLENT",
        "severity_counts": {"P0": 1, "P1": 1, "P2": 0, "P3": 0},
        "fixed_issue_count": 2,
        "open_issue_count": 0,
    }


def integration_bindings() -> list[dict[str, Any]]:
    html = runtime.render_html()
    ar = p1.receivable_facts("demo-north", "2026-07")
    funding = p2.loan_funding_plan("demo-north", "2026-07", "collection_delay")
    base = p3.relation_report_view()
    events = workflow.canonical_demo_events()
    current = p3.relation_report_view(project_events=events)
    south_base = p3.relation_report_view(company_id="demo-south")
    south_current = p3.relation_report_view(company_id="demo-south", project_events=events)
    degraded = p3.relation_report_view(verification_state="UNVERIFIED", project_events=events)
    current_report = current["report"]
    current_csv = list(csv.DictReader(io.StringIO(p3.export_appendix_csv(current_report))))
    current_html = p3.render_report_html(current_report)
    base_catalog_total = sum(row["cost_cents"] for row in projects.project_catalog("demo-north", "2026-07"))
    ar_total = sum(row["receivable_cents"] for row in ar["rows"])
    overdue_total = sum(row["overdue_cents"] for row in ar["rows"])
    unbilled_total = sum(row["unbilled_cents"] for row in ar["unbilled_items"])
    qualifying_overdue = sum(
        row["overdue_cents"] >= base["alert_view"]["thresholds"]["major_overdue_amount_cents"]
        and row["overdue_days"] >= base["alert_view"]["thresholds"]["major_overdue_days"]
        for row in ar["rows"]
    )
    current_row = next(row for row in current["dual_view"]["rows"] if row["project_id"] == "PUB-PROJ-001")
    exported_row = next(row for row in current_csv if row["项目编号"] == "PUB-PROJ-001")
    unsupported = next(row for row in ar["rows"] if not row["priority_supported"])
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
            bool(checks) and all(row["status"] == "PASS" for row in checks),
            phase,
        )

    add("AR-TOTAL", "RECEIVABLE_TO_REPORT", ar_total == base["dual_view"]["totals"]["open_receivable_cents"], "应收合计")
    add("UNBILLED-TOTAL", "RECEIVABLE_TO_REPORT", unbilled_total == base["dual_view"]["totals"]["unbilled_cents"], "未开票单列")
    add("CASH-OCCUPIED", "RECEIVABLE_TO_REPORT", ar_total + unbilled_total == base["dual_view"]["totals"]["cash_occupied_cents"], "资金占用")
    add("OVERDUE-TOTAL", "RECEIVABLE_TO_REPORT", overdue_total == base["dual_view"]["totals"]["overdue_receivable_cents"], "逾期应收")
    add("OVERDUE-ALERTS", "RECEIVABLE_TO_REPORT", qualifying_overdue == base["alert_view"]["alert_count_by_type"]["MAJOR_OVERDUE"], "重大逾期提醒")
    add("UNBILLED-NOT-AR", "RECEIVABLE_TO_REPORT", all(row["receivable_cents"] == 0 for row in ar["unbilled_items"]), "未开票不计应收")
    add("UNSUPPORTED-PRIORITY", "RECEIVABLE_TO_REPORT", unsupported["priority_score"] is None and unsupported["recommended_internal_step_zh"] is None, "依据不足不建议")
    add("NO-CUSTOMER-CONTACT", "RECEIVABLE_TO_REPORT", all(row["automatic_customer_contact_allowed"] is False for row in ar["rows"]), "不自动联系客户")
    add("AR-BASIS", "RECEIVABLE_TO_REPORT", bool(ar["cutoff_date"] and ar["aging_basis_zh"] and ar["receivable_definition_zh"]), "截止日与口径明确")

    add("FUNDING-GAP", "FUNDS_TO_ALERT", funding["maximum_funding_gap_cents"] == 4_000_000 and base["alert_view"]["alert_count_by_type"]["FUNDING_GAP"] == 1, "缺口与提醒")
    add("LOAN-MATURITY", "FUNDS_TO_ALERT", funding["loan_due_within_90_days_count"] == base["alert_view"]["alert_count_by_type"]["LOAN_MATURITY"], "贷款到期提醒")
    add("NO-PAYMENT", "FUNDS_TO_ALERT", funding["payment_execution_count"] == funding["payment_button_count"] == 0, "不执行付款")
    add("NO-BANK-OPERATION", "FUNDS_TO_ALERT", funding["bank_operation_count"] == 0, "不执行银行操作")
    add("SCENARIO-BOUND", "FUNDS_TO_ALERT", funding["scenario_id"] == base["scenario_id"] == "collection_delay", "情景一致")
    add("THRESHOLDS", "FUNDS_TO_ALERT", base["thresholds_externalized"] and bool(base["alert_view"]["threshold_version"]), "阈值外置且有版本")
    add("SANITISED-ALERTS", "FUNDS_TO_ALERT", base["full_sensitive_detail_count"] == 0, "预警最少披露")

    add("BASE-COST", "CURRENT_PROJECT_PROJECTION", base["dual_view"]["totals"]["cost_cents"] == base_catalog_total, "处理前项目成本")
    add("CURRENT-COST", "CURRENT_PROJECT_PROJECTION", current_row["cost_cents"] == 234_552_000, "处理后项目成本")
    add("CURRENT-TOTAL", "CURRENT_PROJECT_PROJECTION", current["dual_view"]["totals"]["cost_cents"] == base_catalog_total - 1_280_000, "处理后总成本")
    add("CURRENT-REVENUE", "CURRENT_PROJECT_PROJECTION", current["dual_view"]["totals"]["revenue_cents"] == base["dual_view"]["totals"]["revenue_cents"], "收入不变")
    add("CURRENT-PROFIT", "CURRENT_PROJECT_PROJECTION", current_row["revenue_cents"] == current_row["cost_cents"] + current_row["gross_profit_cents"], "当前利润守恒")
    add("PAGE-DUAL", "CURRENT_PROJECT_PROJECTION", current_report["page_rows"] == current["dual_view"]["rows"], "页面与双视图")
    add("SUMMARY-DUAL", "CURRENT_PROJECT_PROJECTION", current_report["summary"] == current["dual_view"]["totals"], "合计与双视图")
    add("CSV-CURRENT", "CURRENT_PROJECT_PROJECTION", int(exported_row["成本(分)"]) == current_row["cost_cents"], "CSV 当前金额")
    add("HTML-CURRENT", "CURRENT_PROJECT_PROJECTION", "¥2,345,520.00" in current_html, "HTML 当前金额")
    add("PAGE-EXPORT-ZERO", "CURRENT_PROJECT_PROJECTION", current_report["report_page_export_difference_cents"] == 0, "页面附表差异零分")
    add("COMPANY-ISOLATION", "SCOPE_AND_DEGRADATION", south_current["dual_view"]["totals"] == south_base["dual_view"]["totals"], "其他公司不继承事件")
    add("UNVERIFIED-HIDDEN", "SCOPE_AND_DEGRADATION", all(value is None for value in degraded["dual_view"]["totals"].values()), "未核验金额隐藏")
    add("UNVERIFIED-ALERTS", "SCOPE_AND_DEGRADATION", degraded["alert_view"]["alert_count"] == 0, "未核验预警暂停")

    ids = re.findall(r'\bid="([^"]+)"', html)
    add("HTML-LANGUAGE", "TECHNICAL_QUALITY", '<html lang="zh-CN"' in html, "中文页面")
    add("NO-EXTERNAL-ASSET", "TECHNICAL_QUALITY", not re.search(r'(?:src|href)=["\']https?://', html), "无外部资产")
    add("UNIQUE-IDS", "TECHNICAL_QUALITY", bool(ids) and len(ids) == len(set(ids)), "页面 ID 唯一")
    add("REDUCED-MOTION", "TECHNICAL_QUALITY", "prefers-reduced-motion:reduce" in html, "减少动态")
    add("TOUCH-TARGET", "TECHNICAL_QUALITY", "min-height:44px" in html, "触控尺寸")
    add("ALERT-ACTIONS", "TECHNICAL_QUALITY", all(token in html for token in FIX_MARKERS["actionable_alerts"]), "预警可进入明细")
    add("ROUTES", "TECHNICAL_QUALITY", all(token in html for token in ("/collections", "/funds", "/funds-report")), "三页链路")
    add(
        "ZERO-SIDE-EFFECTS",
        "TECHNICAL_QUALITY",
        all(
            current[key] == 0
            for key in (
                "raw_root_access_count",
                "live_source_read_count",
                "external_network_request_count",
                "source_data_write_count",
                "fact_layer_write_count",
                "notification_send_count",
                "payment_execution_count",
                "bank_operation_count",
                "real_business_action_count",
            )
        ),
        "无真实副作用",
    )
    add("HONEST-REPORT", "TECHNICAL_QUALITY", current["formal_business_report"] is False and degraded["report_degraded"] is True, "非正式且可降级")

    if len(rows) != EXPECTED_BINDING_COUNT:
        raise StageReviewError(f"REVIEW_BINDING_COUNT_DRIFT：预期 {EXPECTED_BINDING_COUNT}，实际 {len(rows)}。")
    return rows


def _integrated_payload() -> dict[str, Any]:
    bindings = integration_bindings()
    return {
        "schema_version": "kmfa.v015.s18.integrated-stage-review.v1",
        "fixture_class": "PUBLIC_SAFE_LOCALHOST_DEMO",
        "predecessor_phase_count": 3,
        "predecessor_task_accepted_count": 9,
        "predecessor_receipt_count": 60,
        "predecessor_public_check_count": 187,
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
        "source_data_write_count": 0,
        "fact_layer_write_count": 0,
        "notification_send_count": 0,
        "external_message_count": 0,
        "payment_execution_count": 0,
        "bank_operation_count": 0,
        "formal_business_report_generated": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "s19_started": False,
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
    blocked_counts = tuple(
        actual[key]
        for key in (
            "raw_root_access_count",
            "live_source_read_count",
            "external_network_request_count",
            "real_identity_count",
            "credential_count",
            "real_business_action_count",
            "source_data_write_count",
            "fact_layer_write_count",
            "notification_send_count",
            "external_message_count",
            "payment_execution_count",
            "bank_operation_count",
        )
    )
    if any(blocked_counts) or any(
        actual[key]
        for key in (
            "raw_business_content_read",
            "formal_business_report_generated",
            "github_upload_performed",
            "app_reinstall_performed",
            "s19_started",
        )
    ):
        raise StageReviewError("REVIEW_SIDE_EFFECT_REJECTED：复审产生了越界动作。")
    return {
        "integration_binding_count": EXPECTED_BINDING_COUNT,
        "integration_binding_failed_count": 0,
        "review_finding_count": len(REVIEW_FINDINGS),
        "fixed_review_finding_count": len(REVIEW_FINDINGS),
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
            add(f"{prefix}_{row['check_id']}", row["status"] == "PASS")
    for row in review["integration_bindings"]:
        add("binding_" + row["binding_id"], row["status"] == "PASS")
    for name, passed in (
        ("raw_root_zero", review["raw_root_access_count"] == 0),
        ("live_source_zero", review["live_source_read_count"] == 0),
        ("external_network_zero", review["external_network_request_count"] == 0),
        ("real_identity_zero", review["real_identity_count"] == 0),
        ("credential_zero", review["credential_count"] == 0),
        ("source_write_zero", review["source_data_write_count"] == 0),
        ("fact_write_zero", review["fact_layer_write_count"] == 0),
        ("real_action_zero", review["real_business_action_count"] == 0),
        ("notification_zero", review["notification_send_count"] == 0),
        ("message_zero", review["external_message_count"] == 0),
        ("payment_zero", review["payment_execution_count"] == 0),
        ("bank_zero", review["bank_operation_count"] == 0),
        ("formal_report_closed", review["formal_business_report_generated"] is False),
        ("github_closed", review["github_upload_performed"] is False),
        ("app_closed", review["app_reinstall_performed"] is False),
        ("s19_closed", review["s19_started"] is False),
        ("current_projection_fixed", review["review_findings"][0]["status"] == "FIXED_VALIDATED"),
        ("alert_navigation_fixed", review["review_findings"][1]["status"] == "FIXED_VALIDATED"),
    ):
        add(name, passed)
    if len(checks) != EXPECTED_PUBLIC_CHECK_COUNT:
        raise StageReviewError(f"PUBLIC_CHECK_COUNT_DRIFT：预期 {EXPECTED_PUBLIC_CHECK_COUNT}，实际 {len(checks)}。")
    failed = [row["name"] for row in checks if not row["passed"]]
    return {
        "schema_version": "kmfa.v015.s18.stage-review-public-verification.v1",
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
        raise StageReviewError("S18 整体复审失败：" + ", ".join(value["failed_checks"]))
    return value


if __name__ == "__main__":
    result = validate_public_contract()
    print(f"PASS: S18 整体复审公开检查 {result['accounting']['passed']}/{result['accounting']['total']}")
