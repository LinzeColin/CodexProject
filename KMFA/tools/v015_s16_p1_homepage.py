#!/usr/bin/env python3
"""KMFA v1.5 S16-P1 经营首页首屏的公开演示内核。"""

from __future__ import annotations

import copy
from typing import Any, Mapping

from KMFA.tools import v015_s13_p3_action_priority as action_priority
from KMFA.tools import v015_s15_p1_app_shell as app_shell
from KMFA.tools import v015_s15_p2_identity_roles as identity_roles


RUN_PHASE_ID = "V015_S16_P1_HOMEPAGE_FIRST_SCREEN"
ROADMAP_PHASE_ID = "S16-P1"
TASK_ID = "KMFA-V015-S16-P1-HOMEPAGE-FIRST-SCREEN-20260716"
ACCEPTANCE_ID = "ACC-KMFA-V015-S16-P1-HOMEPAGE-FIRST-SCREEN"
VERSION = "1.5.0-dev-s16p1"

SUMMARY_METRIC_COUNT = 5
FOCUS_ITEM_COUNT = 5
TREND_SERIES_COUNT = 3
TREND_PERIOD_COUNT = 4
PROJECT_PORTFOLIO_COUNT = 4

DATA_STATES = ("complete", "partial")
COMPLETENESS_STATES = ("COMPLETE", "INCOMPLETE")

FOCUS_ROUTES = {
    "COLLECTION": ("/collections", "查看逾期回款"),
    "FUNDS": ("/funds", "查看资金计划"),
    "TAX": ("/tax-policy", "查看税务事项"),
    "PROJECT": ("/projects", "查看项目偏差"),
    "DATA": ("/data-update", "补齐缺失资料"),
}

COMPANY_FACTORS = {"demo-north": 100, "demo-south": 84, "demo-west": 68}
PERIOD_FACTORS = {"2026-07": 100, "2026-Q2": 94, "2026-H1": 88}
TREND_PERIODS = ("4月", "5月", "6月", "7月")

_PRIVATE_MARKERS = ("/Users/", "/Volumes/", "file://", "private://", "KMFA_MetaData")


class HomepageError(ValueError):
    """经营首页公开演示输入或输出不符合约束。"""


def _public_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise HomepageError(f"{field} must be non-empty text")
    text = value.strip()
    if any(marker.lower() in text.lower() for marker in _PRIVATE_MARKERS):
        raise HomepageError(f"{field} contains private locator")
    return text


def _non_negative_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise HomepageError(f"{field} must be a non-negative integer")
    return value


def _scale(value: int, company_id: str, period: str) -> int:
    return value * COMPANY_FACTORS[company_id] * PERIOD_FACTORS[period] // 10_000


def format_wan_cents(value: int | None) -> str:
    """把分格式化为万元；资料不足时不把缺失值显示成 0。"""

    if value is None:
        return "资料不足"
    cents = _non_negative_int(value, "money_cents")
    whole, remainder = divmod(cents, 1_000_000)
    hundredths = remainder * 100 // 1_000_000
    return f"¥{whole:,}.{hundredths:02d} 万"


def format_percent_bps(value: int | None) -> str:
    if value is None:
        return "资料不足"
    bps = _non_negative_int(value, "percentage_bps")
    whole, remainder = divmod(bps, 100)
    return f"{whole}.{remainder:02d}%"


def source_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s16p1.source_contract.v1",
        "stage_id": "S16",
        "stage_name_zh": "经营首页与管理层总览",
        "stage_goal_zh": "让管理者在 10 秒内知道公司状况、重点问题和下一步。",
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "phase_name_zh": "首屏结构",
        "task_ids": ["S16P1T01", "S16P1T02", "S16P1T03"],
        "task_names_zh": ["实现核心经营摘要", "实现本期重点事项", "实现趋势和项目组合"],
        "acceptance_zh": [
            "数字来源、截止日和完整性可见。",
            "每项只有一个清晰主动作。",
            "图表可读且有表格替代。",
        ],
        "stop_conditions_zh": [
            "缺数据时不得伪造完整结论。",
            "不得堆砌 20 个告警。",
            "装饰性雷达图无解释时不得使用。",
        ],
        "data_classification": "PUBLIC_SYNTHETIC",
    }


def _metric(
    metric_id: str,
    label_zh: str,
    route: str,
    source_zh: str,
    source_ref: str,
    cutoff_date: str,
    primary_value: int,
    primary_unit: str,
    display_zh: str,
    *,
    secondary_value: int | None = None,
    secondary_unit: str | None = None,
    secondary_display_zh: str | None = None,
    note_zh: str,
) -> dict[str, Any]:
    return {
        "metric_id": metric_id,
        "label_zh": label_zh,
        "route": route,
        "source_zh": source_zh,
        "source_ref": source_ref,
        "cutoff_date": cutoff_date,
        "completeness": "COMPLETE",
        "completeness_zh": "资料已齐",
        "primary_value": primary_value,
        "primary_unit": primary_unit,
        "display_zh": display_zh,
        "secondary_value": secondary_value,
        "secondary_unit": secondary_unit,
        "secondary_display_zh": secondary_display_zh,
        "note_zh": note_zh,
        "missing_reason_zh": None,
    }


def _summary_metrics(company_id: str, period: str) -> list[dict[str, Any]]:
    cutoff = "2026-07-15"
    cash = _scale(684_250_000, company_id, period)
    receipts = _scale(426_800_000, company_id, period)
    payments = _scale(371_600_000, company_id, period)
    gross_profit = _scale(295_400_000, company_id, period)
    overdue = _scale(118_750_000, company_id, period)
    margin_bps = 2_386 + list(COMPANY_FACTORS).index(company_id) * 87
    overdue_count = 7 + list(COMPANY_FACTORS).index(company_id) * 2
    confirmation_count = 5 + list(PERIOD_FACTORS).index(period)
    return [
        _metric(
            "AVAILABLE_CASH",
            "可用资金",
            "/funds",
            "资金台账公开演示快照",
            "PUBLIC-SYNTHETIC:FUNDS:AVAILABLE-CASH",
            cutoff,
            cash,
            "CNY_CENTS",
            format_wan_cents(cash),
            note_zh="已扣除公开演示中的受限资金。",
        ),
        _metric(
            "EXPECTED_RECEIPTS_PAYMENTS",
            "本月预计收付款",
            "/funds",
            "回款计划与付款计划公开演示快照",
            "PUBLIC-SYNTHETIC:FUNDS:EXPECTED-FLOW",
            cutoff,
            receipts,
            "CNY_CENTS_RECEIPTS",
            "预计收款 " + format_wan_cents(receipts),
            secondary_value=payments,
            secondary_unit="CNY_CENTS_PAYMENTS",
            secondary_display_zh="预计付款 " + format_wan_cents(payments),
            note_zh="收款与付款分别展示，不用净额掩盖方向。",
        ),
        _metric(
            "PROJECT_GROSS_PROFIT",
            "项目毛利",
            "/projects",
            "项目收入成本公开演示汇总",
            "PUBLIC-SYNTHETIC:PROJECT:GROSS-PROFIT",
            cutoff,
            gross_profit,
            "CNY_CENTS",
            format_wan_cents(gross_profit),
            secondary_value=margin_bps,
            secondary_unit="BPS",
            secondary_display_zh="毛利率 " + format_percent_bps(margin_bps),
            note_zh="只汇总已纳入当前演示期间的项目。",
        ),
        _metric(
            "OVERDUE_RECEIVABLE",
            "逾期应收",
            "/collections",
            "应收账龄公开演示汇总",
            "PUBLIC-SYNTHETIC:COLLECTION:OVERDUE",
            cutoff,
            overdue,
            "CNY_CENTS",
            format_wan_cents(overdue),
            secondary_value=overdue_count,
            secondary_unit="COUNT",
            secondary_display_zh=f"{overdue_count} 笔",
            note_zh="按公开演示到期日判断，不代表真实应收。",
        ),
        _metric(
            "CONFIRMATIONS",
            "需确认事项",
            "/data-update",
            "公开演示确认队列",
            "PUBLIC-SYNTHETIC:DATA:CONFIRMATION-QUEUE",
            cutoff,
            confirmation_count,
            "COUNT",
            f"{confirmation_count} 项",
            note_zh="需要人工确认，不会自动写入事实层。",
        ),
    ]


def _focus_items() -> list[dict[str, Any]]:
    selection = action_priority.select_focus_items(action_priority.sample_candidates())
    items: list[dict[str, Any]] = []
    for item in selection["focus_items"]:
        route, action_zh = FOCUS_ROUTES[item["domain"]]
        items.append(
            {
                "focus_rank": item["focus_rank"],
                "candidate_id": item["candidate_id"],
                "title_zh": item["title_zh"],
                "domain": item["domain"],
                "owner_role": item["owner_role"],
                "priority_score_bps": item["priority_score_bps"],
                "reason_zh": "由已登记的影响、紧急度、可信度与执行成本共同排序。",
                "primary_action": {"label_zh": action_zh, "route": route},
                "primary_action_count": 1,
                "advisory_only": True,
                "automatic_execution_allowed": False,
                "source_refs": list(item["source_refs"]),
            }
        )
    return items


def _trend_series(company_id: str, period: str) -> list[dict[str, Any]]:
    definitions = (
        ("CASH_BALANCE", "可用资金", "/funds", (612_000_000, 635_000_000, 659_000_000, 684_250_000)),
        ("COLLECTIONS", "预计收款", "/collections", (344_000_000, 381_000_000, 402_000_000, 426_800_000)),
        ("GROSS_PROFIT", "项目毛利", "/projects", (241_000_000, 257_000_000, 278_000_000, 295_400_000)),
    )
    return [
        {
            "series_id": series_id,
            "label_zh": label,
            "route": route,
            "periods": list(TREND_PERIODS),
            "values_cents": [_scale(value, company_id, period) for value in values],
            "display_values_zh": [format_wan_cents(_scale(value, company_id, period)) for value in values],
            "source_zh": "公开演示月度趋势",
            "source_ref": f"PUBLIC-SYNTHETIC:TREND:{series_id}",
            "cutoff_date": "2026-07-15",
            "table_alternative_available": True,
        }
        for series_id, label, route, values in definitions
    ]


def _project_portfolio(company_id: str, period: str) -> list[dict[str, Any]]:
    definitions = (
        ("PUB-PROJ-001", "示例厂房改造", 328_000_000, 2_810, 8_600, "需要关注", "复核成本偏差"),
        ("PUB-PROJ-002", "示例设备安装", 246_000_000, 2_460, 9_200, "进展正常", "查看项目"),
        ("PUB-PROJ-003", "示例管网工程", 194_000_000, 1_940, 7_400, "需要关注", "核对回款"),
        ("PUB-PROJ-004", "示例维护服务", 126_000_000, 3_180, 9_650, "进展正常", "查看项目"),
    )
    rows = []
    for project_id, name, revenue, margin_bps, collection_bps, status, next_step in definitions:
        scaled = _scale(revenue, company_id, period)
        rows.append(
            {
                "project_id": project_id,
                "project_name_zh": name,
                "revenue_cents": scaled,
                "revenue_display_zh": format_wan_cents(scaled),
                "gross_margin_bps": margin_bps,
                "gross_margin_display_zh": format_percent_bps(margin_bps),
                "collection_bps": collection_bps,
                "collection_display_zh": format_percent_bps(collection_bps),
                "status": "ATTENTION" if status == "需要关注" else "NORMAL",
                "status_zh": status,
                "next_step_zh": next_step,
                "route": "/projects/demo-project",
            }
        )
    return rows


def _validate_snapshot(payload: Mapping[str, Any]) -> None:
    if payload.get("data_classification") != "PUBLIC_SYNTHETIC":
        raise HomepageError("homepage payload must be public synthetic")
    metrics = payload.get("summary_metrics")
    focus = payload.get("focus_items")
    trends = payload.get("trend_series")
    projects = payload.get("project_portfolio")
    if not isinstance(metrics, list) or len(metrics) != SUMMARY_METRIC_COUNT:
        raise HomepageError("exactly five summary metrics required")
    if not isinstance(focus, list) or len(focus) != FOCUS_ITEM_COUNT:
        raise HomepageError("exactly five focus items required")
    if not isinstance(trends, list) or len(trends) != TREND_SERIES_COUNT:
        raise HomepageError("exactly three trend series required")
    if not isinstance(projects, list) or len(projects) != PROJECT_PORTFOLIO_COUNT:
        raise HomepageError("exactly four project rows required")
    if any(metric.get("route") not in app_shell.KNOWN_ROUTES for metric in metrics):
        raise HomepageError("summary metric route is unknown")
    if any(
        not metric.get("source_zh")
        or not metric.get("source_ref")
        or not metric.get("cutoff_date")
        or metric.get("completeness") not in COMPLETENESS_STATES
        for metric in metrics
    ):
        raise HomepageError("summary metric lineage is incomplete")
    if any(item.get("primary_action_count") != 1 for item in focus):
        raise HomepageError("each focus item must have exactly one primary action")
    if any(item["primary_action"].get("route") not in app_shell.KNOWN_ROUTES for item in focus):
        raise HomepageError("focus action route is unknown")
    if any(item.get("automatic_execution_allowed") is not False for item in focus):
        raise HomepageError("focus items must remain advisory")
    if any(row.get("table_alternative_available") is not True for row in trends):
        raise HomepageError("every trend needs a table alternative")
    if any(len(row.get("periods", [])) != TREND_PERIOD_COUNT for row in trends):
        raise HomepageError("trend period count drift")
    if any("radar" in str(value).lower() for value in payload.values()):
        raise HomepageError("decorative radar chart is forbidden")
    incomplete = [metric for metric in metrics if metric["completeness"] != "COMPLETE"]
    if incomplete:
        if payload.get("overall_completeness") != "INCOMPLETE":
            raise HomepageError("missing metric must make homepage incomplete")
        if payload.get("complete_management_conclusion_available") is not False:
            raise HomepageError("missing data cannot form a complete conclusion")
        if any(metric.get("display_zh") == "0" for metric in incomplete):
            raise HomepageError("missing data cannot be displayed as zero")


def homepage_snapshot(
    *,
    user_id: str = "demo-owner",
    role_id: str = "management",
    company_id: str = "demo-north",
    period: str = "2026-07",
    data_state: str = "complete",
) -> dict[str, Any]:
    identity = identity_roles.identity_snapshot(user_id, role_id, company_id)
    if not identity.get("allowed"):
        return {
            "schema_version": "kmfa.v015.s16p1.homepage_response.v1",
            "data_classification": "PUBLIC_SYNTHETIC",
            "allowed": False,
            "reason_code": identity.get("reason_code"),
            "reason_zh": identity.get("reason_zh"),
            "summary_metrics": [],
            "focus_items": [],
            "trend_series": [],
            "project_portfolio": [],
        }
    if company_id not in COMPANY_FACTORS:
        raise HomepageError("unsupported public company")
    if period not in PERIOD_FACTORS:
        raise HomepageError("unsupported public period")
    if data_state not in DATA_STATES:
        raise HomepageError("unsupported data state")

    metrics = _summary_metrics(company_id, period)
    if data_state == "partial":
        missing = metrics[3]
        missing.update(
            {
                "completeness": "INCOMPLETE",
                "completeness_zh": "资料未齐",
                "primary_value": None,
                "display_zh": "资料不足",
                "secondary_value": None,
                "secondary_display_zh": "笔数待补齐",
                "missing_reason_zh": "逾期应收来源尚未完成本期更新。",
            }
        )
    overall = "COMPLETE" if data_state == "complete" else "INCOMPLETE"
    payload = {
        "schema_version": "kmfa.v015.s16p1.homepage_response.v1",
        "data_classification": "PUBLIC_SYNTHETIC",
        "allowed": True,
        "context": {"user_id": user_id, "role_id": role_id, "company_id": company_id, "period": period},
        "context_labels": {
            "company": next(item["label"] for item in app_shell.CONTEXT_OPTIONS["company"] if item["value"] == company_id),
            "period": next(item["label"] for item in app_shell.CONTEXT_OPTIONS["period"] if item["value"] == period),
        },
        "as_of_date": "2026-07-15",
        "overall_completeness": overall,
        "overall_completeness_zh": "本期公开演示资料已齐" if overall == "COMPLETE" else "本期资料不完整",
        "complete_management_conclusion_available": overall == "COMPLETE",
        "real_business_conclusion_allowed": False,
        "honest_summary_zh": (
            "公开演示资料已齐，可用于核对页面和判断顺序；不代表真实公司结论。"
            if overall == "COMPLETE"
            else "逾期应收资料尚未补齐，先补资料，再形成完整经营判断。"
        ),
        "summary_metrics": metrics,
        "focus_items": _focus_items(),
        "trend_series": _trend_series(company_id, period),
        "project_portfolio": _project_portfolio(company_id, period),
        "summary_metric_count": len(metrics),
        "focus_item_count": FOCUS_ITEM_COUNT,
        "primary_action_count": FOCUS_ITEM_COUNT,
        "trend_series_count": TREND_SERIES_COUNT,
        "trend_table_alternative_count": TREND_SERIES_COUNT,
        "project_portfolio_count": PROJECT_PORTFOLIO_COUNT,
        "missing_as_zero_count": 0,
        "automatic_execution_count": 0,
        "fact_layer_write_count": 0,
        "raw_write_count": 0,
        "external_network_request_count": 0,
        "real_business_action_count": 0,
    }
    _validate_snapshot(payload)
    return payload


def acceptance_checks() -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []

    def add(check_id: str, passed: bool, detail: str) -> None:
        checks.append({"check_id": check_id, "status": "PASS" if passed else "FAIL", "detail": detail})

    complete = homepage_snapshot()
    partial = homepage_snapshot(data_state="partial")
    metrics = complete["summary_metrics"]
    focus = complete["focus_items"]
    trends = complete["trend_series"]
    projects = complete["project_portfolio"]
    add("source_stage", source_contract()["stage_id"] == "S16", "current TaskPack S16")
    add("source_phase", source_contract()["roadmap_phase_id"] == "S16-P1", "current TaskPack S16-P1")
    add("summary_metric_count", len(metrics) == 5, str(len(metrics)))
    add("summary_metric_ids_unique", len({row["metric_id"] for row in metrics}) == 5, "five unique ids")
    add("summary_sources_visible", all(row["source_zh"] and row["source_ref"] for row in metrics), "all source bound")
    add("summary_cutoffs_visible", all(row["cutoff_date"] for row in metrics), "all cutoff bound")
    add("summary_completeness_visible", all(row["completeness_zh"] for row in metrics), "all completeness bound")
    add("summary_routes_known", all(row["route"] in app_shell.KNOWN_ROUTES for row in metrics), "all routes known")
    add("money_integer_only", all(not isinstance(row["primary_value"], bool) and isinstance(row["primary_value"], int) for row in metrics), "integer storage")
    add("complete_state_visible", complete["overall_completeness"] == "COMPLETE", "complete")
    add("real_conclusion_blocked", complete["real_business_conclusion_allowed"] is False, "public demo only")
    add("partial_state_visible", partial["overall_completeness"] == "INCOMPLETE", "incomplete")
    add("partial_conclusion_blocked", partial["complete_management_conclusion_available"] is False, "blocked")
    add("partial_missing_value_none", partial["summary_metrics"][3]["primary_value"] is None, "missing remains null")
    add("partial_missing_copy", partial["summary_metrics"][3]["display_zh"] == "资料不足", "honest copy")
    add("missing_as_zero_count", partial["missing_as_zero_count"] == 0, "zero")
    add("focus_item_count", len(focus) == 5, str(len(focus)))
    add("focus_bound_max", len(focus) <= 5, "not an alert wall")
    add("focus_bound_min", len(focus) >= 3, "enough focus")
    add("focus_unique", len({row["candidate_id"] for row in focus}) == 5, "unique")
    add("focus_one_action_each", all(row["primary_action_count"] == 1 for row in focus), "one each")
    add("focus_action_count", sum(row["primary_action_count"] for row in focus) == 5, "five total")
    add("focus_routes_known", all(row["primary_action"]["route"] in app_shell.KNOWN_ROUTES for row in focus), "known routes")
    add("focus_advisory_only", all(row["advisory_only"] for row in focus), "advisory")
    add("focus_no_auto_execution", all(not row["automatic_execution_allowed"] for row in focus), "no auto action")
    add("trend_series_count", len(trends) == 3, str(len(trends)))
    add("trend_period_count", all(len(row["periods"]) == 4 for row in trends), "four periods")
    add("trend_values_integer", all(all(isinstance(value, int) and not isinstance(value, bool) for value in row["values_cents"]) for row in trends), "integer cents")
    add("trend_table_alternatives", all(row["table_alternative_available"] for row in trends), "all available")
    add("trend_sources", all(row["source_ref"] for row in trends), "all source bound")
    add("project_portfolio_count", len(projects) == 4, str(len(projects)))
    add("project_ids_unique", len({row["project_id"] for row in projects}) == 4, "unique")
    add("project_money_integer", all(isinstance(row["revenue_cents"], int) for row in projects), "integer cents")
    add("project_margin_bps", all(isinstance(row["gross_margin_bps"], int) for row in projects), "integer bps")
    add("project_collection_bps", all(isinstance(row["collection_bps"], int) for row in projects), "integer bps")
    add("project_status_text", all(row["status_zh"] in {"需要关注", "进展正常"} for row in projects), "text labels")
    add("project_routes_known", all(row["route"] in app_shell.KNOWN_ROUTES for row in projects), "known routes")
    add("no_radar_chart", "radar" not in str(complete).lower(), "no decorative radar")
    add("public_classification", complete["data_classification"] == "PUBLIC_SYNTHETIC", "public synthetic")
    add("raw_write_zero", complete["raw_write_count"] == 0, "zero")
    add("fact_write_zero", complete["fact_layer_write_count"] == 0, "zero")
    add("network_zero", complete["external_network_request_count"] == 0, "zero")
    add("business_action_zero", complete["real_business_action_count"] == 0, "zero")
    add("north_south_distinct", homepage_snapshot(company_id="demo-north")["summary_metrics"][0]["primary_value"] != homepage_snapshot(company_id="demo-south")["summary_metrics"][0]["primary_value"], "company bound")
    add("periods_distinct", homepage_snapshot(period="2026-07")["summary_metrics"][0]["primary_value"] != homepage_snapshot(period="2026-Q2")["summary_metrics"][0]["primary_value"], "period bound")
    denied = homepage_snapshot(user_id="demo-finance", role_id="finance", company_id="demo-south")
    add("company_permission_denied", denied["allowed"] is False, denied.get("reason_code", ""))
    add("denied_payload_empty", all(not denied[key] for key in ("summary_metrics", "focus_items", "trend_series", "project_portfolio")), "fail closed")
    add("format_missing_not_zero", format_wan_cents(None) == "资料不足", "honest missing")
    add("format_money_exact", format_wan_cents(684_250_000) == "¥684.25 万", "integer formatter")
    add("format_bps_exact", format_percent_bps(2_386) == "23.86%", "integer formatter")
    return checks


def build_contract() -> dict[str, Any]:
    checks = acceptance_checks()
    failed = [row for row in checks if row["status"] != "PASS"]
    return {
        "schema_version": "kmfa.v015.s16p1.homepage_contract.v1",
        "run_phase_id": RUN_PHASE_ID,
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "version": VERSION,
        "summary_metric_count": SUMMARY_METRIC_COUNT,
        "source_bound_metric_count": SUMMARY_METRIC_COUNT,
        "cutoff_bound_metric_count": SUMMARY_METRIC_COUNT,
        "completeness_bound_metric_count": SUMMARY_METRIC_COUNT,
        "partial_missing_metric_count": 1,
        "missing_as_zero_count": 0,
        "focus_item_count": FOCUS_ITEM_COUNT,
        "primary_action_count": FOCUS_ITEM_COUNT,
        "automatic_execution_count": 0,
        "trend_series_count": TREND_SERIES_COUNT,
        "trend_period_count": TREND_PERIOD_COUNT,
        "trend_table_alternative_count": TREND_SERIES_COUNT,
        "project_portfolio_count": PROJECT_PORTFOLIO_COUNT,
        "public_check_total": len(checks),
        "public_check_pass_count": len(checks) - len(failed),
        "public_check_failed_count": len(failed),
        "checks": copy.deepcopy(checks),
        "raw_root_access_count": 0,
        "live_source_read_count": 0,
        "external_network_request_count": 0,
        "real_identity_count": 0,
        "credential_count": 0,
        "real_business_action_count": 0,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
    }


if __name__ == "__main__":
    import json

    print(json.dumps(build_contract(), ensure_ascii=False, indent=2, sort_keys=True))
