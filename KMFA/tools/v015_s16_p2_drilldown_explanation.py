#!/usr/bin/env python3
"""KMFA v1.5 S16-P2 指标下钻、来源解释和期间比较公开演示内核。"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from KMFA.tools import v015_s15_p1_app_shell as app_shell
from KMFA.tools import v015_s16_p1_homepage as homepage


RUN_PHASE_ID = "V015_S16_P2_DRILLDOWN_EXPLANATION"
ROADMAP_PHASE_ID = "S16-P2"
TASK_ID = "KMFA-V015-S16-P2-DRILLDOWN-EXPLANATION-20260716"
ACCEPTANCE_ID = "ACC-KMFA-V015-S16-P2-DRILLDOWN-EXPLANATION"
VERSION = "1.5.0-dev-s16p2"

METRIC_SLUGS = {
    "AVAILABLE_CASH": "available-cash",
    "EXPECTED_RECEIPTS_PAYMENTS": "expected-flow",
    "PROJECT_GROSS_PROFIT": "project-gross-profit",
    "OVERDUE_RECEIVABLE": "overdue-receivable",
    "CONFIRMATIONS": "confirmations",
}
SLUG_METRICS = {slug: metric_id for metric_id, slug in METRIC_SLUGS.items()}
COMPARISON_KINDS = ("MOM", "YOY", "BASELINE")
COMPARISON_STATES = ("exact", "basis_mismatch", "coverage_mismatch")
LINEAGE_STATES = ("complete", "missing")
DATA_STATES = homepage.DATA_STATES

COMPARISON_LABELS = {
    "MOM": "环比",
    "YOY": "同比",
    "BASELINE": "预算或基准",
}
COMPARISON_FACTORS_BPS = {"MOM": 9_600, "YOY": 8_800, "BASELINE": 10_300}
COMPARISON_PERIOD_LABELS = {
    "2026-07": {"MOM": "2026年6月", "YOY": "2025年7月", "BASELINE": "2026年7月公开基准"},
    "2026-Q2": {"MOM": "2026年第一季度", "YOY": "2025年第二季度", "BASELINE": "2026年第二季度公开基准"},
    "2026-H1": {"MOM": "2025年下半年", "YOY": "2025年上半年", "BASELINE": "2026年上半年公开基准"},
}

METRIC_SPECS: dict[str, dict[str, Any]] = {
    "AVAILABLE_CASH": {
        "detail_title_zh": "可用资金明细",
        "domain_zh": "资金",
        "domain_route": "/funds",
        "short_explanation_zh": "汇总当前公司和期间内可动用的公开演示账户余额，受限资金不计入。",
        "formula_zh": "可用资金 = 纳入当前范围的可用账户余额逐项合计；受限、冻结或主体不明的余额不计入。",
        "basis_id": "CASH-AVAILABLE-BASIS-PUBLIC-1",
        "row_names": ("经营账户", "项目专户", "备用账户"),
        "weights": (45, 35, 20),
    },
    "EXPECTED_RECEIPTS_PAYMENTS": {
        "detail_title_zh": "预计收付款明细",
        "domain_zh": "资金",
        "domain_route": "/funds",
        "short_explanation_zh": "预计收款与预计付款分别列示，保留方向，不使用净额掩盖资金安排。",
        "formula_zh": "预计收款 = 当前范围内已登记收款计划合计；预计付款 = 当前范围内已登记付款计划合计；两者分别展示。",
        "basis_id": "EXPECTED-FLOW-BASIS-PUBLIC-1",
        "row_names": ("合同节点计划", "已确认回款安排", "税费与供应安排"),
        "weights": (45, 35, 20),
        "secondary_weights": (38, 34, 28),
    },
    "PROJECT_GROSS_PROFIT": {
        "detail_title_zh": "项目毛利明细",
        "domain_zh": "项目",
        "domain_route": "/projects",
        "short_explanation_zh": "只比较当前范围内口径一致的项目收入和对应成本，并保留项目级明细。",
        "formula_zh": "项目毛利 = 同一项目、主体、期间和管理口径下的收入减对应成本；毛利率 = 项目毛利 ÷ 同口径收入。",
        "basis_id": "PROJECT-MARGIN-BASIS-PUBLIC-1",
        "row_names": ("示例厂房改造", "示例设备安装", "示例管网工程", "示例维护服务"),
        "weights": (31, 26, 24, 19),
        "secondary_weights": (34, 27, 23, 16),
    },
    "OVERDUE_RECEIVABLE": {
        "detail_title_zh": "逾期应收明细",
        "domain_zh": "回款",
        "domain_route": "/collections",
        "short_explanation_zh": "按当前截止日识别已到期但尚未确认回款的公开演示应收。",
        "formula_zh": "逾期应收 = 到期日早于或等于当前截止日且未确认回款的应收金额合计；笔数按唯一应收事项计数。",
        "basis_id": "OVERDUE-RECEIVABLE-BASIS-PUBLIC-1",
        "row_names": ("逾期 1—30 天", "逾期 31—90 天", "逾期 90 天以上"),
        "weights": (48, 33, 19),
        "secondary_weights": (4, 2, 1),
    },
    "CONFIRMATIONS": {
        "detail_title_zh": "需确认事项明细",
        "domain_zh": "数据与税务",
        "domain_route": "/data-update",
        "short_explanation_zh": "只统计仍需人工确认的事项，不把待确认内容写入经营事实。",
        "formula_zh": "需确认事项 = 当前公司和期间内状态为“需人工确认”的唯一事项数量；已关闭或重复事项不计入。",
        "basis_id": "CONFIRMATION-QUEUE-BASIS-PUBLIC-1",
        "row_names": ("项目归属确认", "回款来源确认", "税务资料确认", "期间归属确认"),
        "weights": (2, 1, 1, 1),
    },
}

_PRIVATE_MARKERS = ("/Users/", "/Volumes/", "file://", "private://", "KMFA_MetaData")


class DrilldownError(ValueError):
    """S16-P2 公开下钻输入或输出不符合约束。"""


def source_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s16p2.source_contract.v1",
        "stage_id": "S16",
        "stage_name_zh": "经营首页与管理层总览",
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "phase_name_zh": "下钻与解释",
        "task_ids": ["S16P2T01", "S16P2T02", "S16P2T03"],
        "task_names_zh": ["实现指标下钻", "实现来源与计算说明", "实现多期间比较"],
        "acceptance_zh": ["上下文和筛选保留。", "不让老板先看技术日志。", "比较口径和数据覆盖一致。"],
        "stop_conditions_zh": ["数字和明细不一致失败。", "来源不可追溯则阻塞。", "不同口径不得直接比较。"],
        "data_classification": "PUBLIC_SYNTHETIC",
    }


def detail_path(metric_id: str) -> str:
    if metric_id not in METRIC_SLUGS:
        raise DrilldownError("unsupported homepage metric")
    return "/overview/detail/" + METRIC_SLUGS[metric_id]


def metric_from_path(path: str) -> str | None:
    prefix = "/overview/detail/"
    return SLUG_METRICS.get(path[len(prefix) :]) if path.startswith(prefix) else None


def _option_allowed(key: str, value: str) -> bool:
    return any(option["value"] == value for option in app_shell.CONTEXT_OPTIONS[key])


def _option_label(key: str, value: str) -> str:
    return next(option["label"] for option in app_shell.CONTEXT_OPTIONS[key] if option["value"] == value)


def _allocate_exact(total: int, weights: Sequence[int]) -> list[int]:
    if isinstance(total, bool) or not isinstance(total, int) or total < 0:
        raise DrilldownError("detail total must be a non-negative integer")
    if not weights or any(isinstance(value, bool) or not isinstance(value, int) or value <= 0 for value in weights):
        raise DrilldownError("positive integer weights required")
    weight_total = sum(weights)
    values = [total * weight // weight_total for weight in weights[:-1]]
    values.append(total - sum(values))
    return values


def _format_count(value: int | None) -> str:
    return "资料不足" if value is None else f"{value} 项"


def _format_primary(metric: Mapping[str, Any], value: int | None) -> str:
    if value is None:
        return "资料不足"
    if metric["primary_unit"] == "COUNT":
        return _format_count(value)
    return homepage.format_wan_cents(value)


def _format_secondary(metric: Mapping[str, Any], value: int | None) -> str | None:
    unit = metric.get("secondary_unit")
    if unit is None:
        return None
    if value is None:
        return "资料不足"
    if unit == "BPS":
        return homepage.format_percent_bps(value)
    if unit == "COUNT":
        return f"{value} 笔"
    return homepage.format_wan_cents(value)


def _project_revenue_total(gross_profit_cents: int, margin_bps: int) -> int:
    if margin_bps <= 0:
        raise DrilldownError("positive project margin required")
    revenue = gross_profit_cents * 10_000 // margin_bps
    if gross_profit_cents * 10_000 // revenue != margin_bps:
        raise DrilldownError("project margin cannot be represented exactly")
    return revenue


def _breakdown(metric: Mapping[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    metric_id = str(metric["metric_id"])
    spec = METRIC_SPECS[metric_id]
    primary = metric.get("primary_value")
    if primary is None:
        return [], {
            "status": "BLOCKED_INCOMPLETE",
            "primary_detail_total": None,
            "primary_homepage_value": None,
            "primary_difference": None,
            "secondary_detail_total": None,
            "secondary_homepage_value": metric.get("secondary_value"),
            "secondary_difference": None,
        }

    primary_values = _allocate_exact(primary, spec["weights"])
    secondary_target = metric.get("secondary_value")
    secondary_values: list[int | None]
    if metric_id == "PROJECT_GROSS_PROFIT":
        secondary_target = _project_revenue_total(primary, int(metric["secondary_value"]))
        secondary_values = _allocate_exact(secondary_target, spec["secondary_weights"])
    elif secondary_target is not None:
        secondary_values = _allocate_exact(int(secondary_target), spec["secondary_weights"])
    else:
        secondary_values = [None] * len(primary_values)

    rows: list[dict[str, Any]] = []
    if not (len(spec["row_names"]) == len(primary_values) == len(secondary_values)):
        raise DrilldownError("detail row definitions must align")
    for index, (name, primary_value, secondary_value) in enumerate(
        zip(spec["row_names"], primary_values, secondary_values), start=1
    ):
        if metric_id == "PROJECT_GROSS_PROFIT":
            secondary_display = homepage.format_wan_cents(secondary_value)
            row_margin = primary_value * 10_000 // secondary_value if secondary_value else None
            row_extra = {
                "secondary_label_zh": "同口径收入",
                "secondary_display_zh": secondary_display,
                "gross_margin_bps": row_margin,
                "gross_margin_display_zh": homepage.format_percent_bps(row_margin),
            }
        elif metric_id == "EXPECTED_RECEIPTS_PAYMENTS":
            row_extra = {"secondary_label_zh": "预计付款", "secondary_display_zh": homepage.format_wan_cents(secondary_value)}
        elif metric_id == "OVERDUE_RECEIVABLE":
            row_extra = {"secondary_label_zh": "笔数", "secondary_display_zh": f"{secondary_value} 笔"}
        else:
            row_extra = {"secondary_label_zh": None, "secondary_display_zh": None}
        rows.append(
            {
                "detail_id": f"PUBLIC-DETAIL-{metric_id}-{index:02d}",
                "label_zh": name,
                "domain_zh": spec["domain_zh"],
                "domain_route": spec["domain_route"],
                "primary_value": primary_value,
                "primary_display_zh": _format_primary(metric, primary_value),
                "secondary_value": secondary_value,
                "status_zh": "已纳入当前汇总",
                "source_zh": f"{name}公开演示明细",
                "source_ref": f"PUBLIC-SYNTHETIC:DRILLDOWN:{metric_id}:{index:02d}",
                **row_extra,
            }
        )

    primary_total = sum(row["primary_value"] for row in rows)
    secondary_total = sum(row["secondary_value"] for row in rows if row["secondary_value"] is not None)
    secondary_homepage_value = metric.get("secondary_value")
    secondary_difference: int | None = None
    if metric_id == "PROJECT_GROSS_PROFIT":
        aggregate_margin = primary_total * 10_000 // secondary_total
        secondary_homepage_value = metric["secondary_value"]
        secondary_difference = aggregate_margin - int(metric["secondary_value"])
    elif secondary_homepage_value is not None:
        secondary_difference = secondary_total - int(secondary_homepage_value)
    return rows, {
        "status": "PASS",
        "primary_detail_total": primary_total,
        "primary_homepage_value": primary,
        "primary_difference": primary_total - primary,
        "secondary_detail_total": secondary_total if metric.get("secondary_value") is not None else None,
        "secondary_homepage_value": secondary_homepage_value,
        "secondary_difference": secondary_difference,
    }


def _lineage(
    metric: Mapping[str, Any],
    spec: Mapping[str, Any],
    context_labels: Mapping[str, str],
    lineage_state: str,
) -> dict[str, Any]:
    complete = lineage_state == "complete"
    nodes = [
        {
            "step": 1,
            "label_zh": "公开演示来源",
            "detail_zh": str(metric["source_zh"]),
            "source_ref": metric["source_ref"] if complete else None,
        },
        {
            "step": 2,
            "label_zh": "当前查看范围",
            "detail_zh": "、".join(
                (context_labels["company"], context_labels["period"], context_labels["project_status"], context_labels["report_version"])
            ),
            "source_ref": "PUBLIC-SYNTHETIC:CONTEXT:CURRENT" if complete else None,
        },
        {
            "step": 3,
            "label_zh": "计算规则",
            "detail_zh": str(spec["formula_zh"]),
            "source_ref": f"FORM-KMFA-V015-S16-P2-{metric['metric_id']}" if complete else None,
        },
        {
            "step": 4,
            "label_zh": "首页呈现",
            "detail_zh": f"汇总结果显示为{metric['display_zh']}，截止 {metric['cutoff_date']}。",
            "source_ref": f"PUBLIC-SYNTHETIC:HOMEPAGE:{metric['metric_id']}" if complete else None,
        },
    ]
    return {
        "lineage_complete": complete,
        "short_explanation_zh": spec["short_explanation_zh"],
        "formula_zh": spec["formula_zh"],
        "professional_mode_label_zh": "查看专业依据",
        "professional_lineage_nodes": nodes if complete else [],
        "professional_lineage_node_count": len(nodes) if complete else 0,
        "technical_log_default_visible": False,
        "technical_log_count": 0,
        "block_reason_zh": None if complete else "当前来源链不完整，已阻止下钻结论；请先补齐来源。",
    }


def _comparison(
    metric: Mapping[str, Any],
    spec: Mapping[str, Any],
    period: str,
    comparison_kind: str,
    comparison_state: str,
) -> dict[str, Any]:
    current = metric.get("primary_value")
    block_reason = None
    if current is None:
        block_reason = "当前资料不完整，不能进行期间比较。"
    elif comparison_state == "basis_mismatch":
        block_reason = "当前期间与比较期间的计算口径不同，已阻止直接比较。"
    elif comparison_state == "coverage_mismatch":
        block_reason = "当前期间与比较期间的数据覆盖范围不同，已阻止直接比较。"
    allowed = block_reason is None
    factor = COMPARISON_FACTORS_BPS[comparison_kind]
    comparison_value = current * factor // 10_000 if allowed else None
    delta = current - comparison_value if allowed else None
    delta_bps = delta * 10_000 // comparison_value if allowed and comparison_value else None
    secondary_current = metric.get("secondary_value")
    secondary_comparison = secondary_current * factor // 10_000 if allowed and secondary_current is not None else None
    secondary_delta = secondary_current - secondary_comparison if secondary_comparison is not None else None
    current_basis = spec["basis_id"]
    comparison_basis = current_basis if comparison_state != "basis_mismatch" else current_basis + "-MISMATCH"
    current_coverage = "PUBLIC-SYNTHETIC:CURRENT-SCOPE"
    comparison_coverage = current_coverage if comparison_state != "coverage_mismatch" else "PUBLIC-SYNTHETIC:DIFFERENT-SCOPE"
    return {
        "comparison_kind": comparison_kind,
        "comparison_label_zh": COMPARISON_LABELS[comparison_kind],
        "current_period_zh": _option_label("period", period),
        "comparison_period_zh": COMPARISON_PERIOD_LABELS[period][comparison_kind],
        "comparison_allowed": allowed,
        "block_reason_zh": block_reason,
        "current_basis_id": current_basis,
        "comparison_basis_id": comparison_basis,
        "basis_consistent": current_basis == comparison_basis,
        "current_coverage_ref": current_coverage,
        "comparison_coverage_ref": comparison_coverage,
        "coverage_consistent": current_coverage == comparison_coverage,
        "coverage_bps": 10_000 if allowed else None,
        "current_value": current,
        "current_display_zh": _format_primary(metric, current),
        "comparison_value": comparison_value,
        "comparison_display_zh": _format_primary(metric, comparison_value),
        "delta_value": delta,
        "delta_display_zh": _format_primary(metric, abs(delta)) if delta is not None else "不可比较",
        "delta_direction": "UP" if delta is not None and delta > 0 else "DOWN" if delta is not None and delta < 0 else "FLAT",
        "delta_bps": delta_bps,
        "delta_rate_display_zh": homepage.format_percent_bps(abs(delta_bps)) if delta_bps is not None else "不可比较",
        "secondary_current_value": secondary_current,
        "secondary_current_display_zh": _format_secondary(metric, secondary_current),
        "secondary_comparison_value": secondary_comparison,
        "secondary_comparison_display_zh": _format_secondary(metric, secondary_comparison),
        "secondary_delta_value": secondary_delta,
    }


def _contains_float(value: Any) -> bool:
    if isinstance(value, float):
        return True
    if isinstance(value, Mapping):
        return any(_contains_float(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_contains_float(item) for item in value)
    return False


def _validate_snapshot(payload: Mapping[str, Any]) -> None:
    if payload.get("data_classification") != "PUBLIC_SYNTHETIC":
        raise DrilldownError("drilldown payload must remain public synthetic")
    if _contains_float(payload):
        raise DrilldownError("float values are forbidden")
    if any(marker.lower() in str(payload).lower() for marker in _PRIVATE_MARKERS):
        raise DrilldownError("private locator is forbidden")
    if not payload.get("allowed"):
        if payload.get("detail_rows"):
            raise DrilldownError("denied response cannot contain detail rows")
        return
    context = payload.get("context", {})
    for key in ("company", "period", "project_status", "report_version"):
        if not _option_allowed(key, context.get(key, "")):
            raise DrilldownError("drilldown context is invalid")
    if payload.get("metric_id") not in METRIC_SPECS:
        raise DrilldownError("unsupported drilldown metric")
    lineage = payload.get("explanation", {})
    comparison = payload.get("comparison", {})
    consistency = payload.get("consistency", {})
    if lineage.get("technical_log_default_visible") is not False or lineage.get("technical_log_count") != 0:
        raise DrilldownError("technical logs cannot be the default explanation")
    if payload.get("detail_available"):
        if lineage.get("lineage_complete") is not True or not lineage.get("professional_lineage_nodes"):
            raise DrilldownError("traceable lineage is required for drilldown")
        if consistency.get("primary_difference") != 0 or consistency.get("secondary_difference") not in (None, 0):
            raise DrilldownError("homepage and detail totals differ")
        if not payload.get("detail_rows"):
            raise DrilldownError("available drilldown needs detail rows")
    if comparison.get("comparison_allowed"):
        if comparison.get("basis_consistent") is not True or comparison.get("coverage_consistent") is not True:
            raise DrilldownError("comparison scope must be exact")
        if comparison.get("coverage_bps") != 10_000:
            raise DrilldownError("comparison coverage must be complete")
    elif not comparison.get("block_reason_zh"):
        raise DrilldownError("blocked comparison needs a human reason")
    if any(row.get("domain_route") not in app_shell.KNOWN_ROUTES for row in payload.get("detail_rows", [])):
        raise DrilldownError("detail route is unknown")


def drilldown_snapshot(
    *,
    metric_id: str = "AVAILABLE_CASH",
    user_id: str = "demo-owner",
    role_id: str = "management",
    company: str = "demo-north",
    period: str = "2026-07",
    project_status: str = "all",
    report_version: str = "latest",
    data_state: str = "complete",
    lineage_state: str = "complete",
    comparison_kind: str = "MOM",
    comparison_state: str = "exact",
) -> dict[str, Any]:
    if metric_id not in METRIC_SPECS:
        raise DrilldownError("unsupported homepage metric")
    for key, value in (("company", company), ("period", period), ("project_status", project_status), ("report_version", report_version)):
        if not _option_allowed(key, value):
            raise DrilldownError(f"unsupported {key}")
    if data_state not in DATA_STATES:
        raise DrilldownError("unsupported data state")
    if lineage_state not in LINEAGE_STATES:
        raise DrilldownError("unsupported lineage state")
    if comparison_kind not in COMPARISON_KINDS:
        raise DrilldownError("unsupported comparison kind")
    if comparison_state not in COMPARISON_STATES:
        raise DrilldownError("unsupported comparison state")

    home = homepage.homepage_snapshot(
        user_id=user_id,
        role_id=role_id,
        company_id=company,
        period=period,
        data_state=data_state,
    )
    if not home.get("allowed"):
        denied = {
            "schema_version": "kmfa.v015.s16p2.drilldown_response.v1",
            "data_classification": "PUBLIC_SYNTHETIC",
            "allowed": False,
            "reason_code": home.get("reason_code"),
            "reason_zh": home.get("reason_zh"),
            "detail_rows": [],
        }
        _validate_snapshot(denied)
        return denied

    metric = next(row for row in home["summary_metrics"] if row["metric_id"] == metric_id)
    spec = METRIC_SPECS[metric_id]
    labels = {
        "company": _option_label("company", company),
        "period": _option_label("period", period),
        "project_status": _option_label("project_status", project_status),
        "report_version": _option_label("report_version", report_version),
    }
    rows, consistency = _breakdown(metric)
    explanation = _lineage(metric, spec, labels, lineage_state)
    comparison = _comparison(metric, spec, period, comparison_kind, comparison_state)
    detail_available = (
        metric.get("completeness") == "COMPLETE"
        and explanation["lineage_complete"]
        and consistency["status"] == "PASS"
    )
    if not detail_available and comparison["comparison_allowed"]:
        comparison.update(
            {
                "comparison_allowed": False,
                "block_reason_zh": explanation.get("block_reason_zh") or metric.get("missing_reason_zh") or "当前明细不完整，不能比较。",
                "coverage_bps": None,
                "current_value": metric.get("primary_value"),
                "comparison_value": None,
                "comparison_display_zh": "不可比较",
                "delta_value": None,
                "delta_display_zh": "不可比较",
                "delta_bps": None,
                "delta_rate_display_zh": "不可比较",
            }
        )
    payload = {
        "schema_version": "kmfa.v015.s16p2.drilldown_response.v1",
        "data_classification": "PUBLIC_SYNTHETIC",
        "allowed": True,
        "metric_id": metric_id,
        "metric_slug": METRIC_SLUGS[metric_id],
        "detail_path": detail_path(metric_id),
        "detail_title_zh": spec["detail_title_zh"],
        "domain_zh": spec["domain_zh"],
        "domain_route": spec["domain_route"],
        "context": {
            "user_id": user_id,
            "role_id": role_id,
            "company": company,
            "period": period,
            "project_status": project_status,
            "report_version": report_version,
        },
        "context_labels": labels,
        "context_preserved": True,
        "filter_count": 4,
        "as_of_date": metric["cutoff_date"],
        "metric": metric,
        "detail_available": detail_available,
        "detail_rows": rows if detail_available else [],
        "detail_row_count": len(rows) if detail_available else 0,
        "consistency": consistency,
        "explanation": explanation,
        "comparison": comparison,
        "homepage_return_path": "/overview",
        "real_business_conclusion_allowed": False,
        "fact_layer_write_count": 0,
        "raw_write_count": 0,
        "raw_root_access_count": 0,
        "live_source_read_count": 0,
        "external_network_request_count": 0,
        "real_business_action_count": 0,
    }
    _validate_snapshot(payload)
    return payload


def acceptance_checks() -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []

    def add(check_id: str, passed: bool, detail: str) -> None:
        checks.append({"check_id": check_id, "status": "PASS" if passed else "FAIL", "detail": detail})

    contract = source_contract()
    add("source_stage", contract["stage_id"] == "S16", "TaskPack S16")
    add("source_phase", contract["roadmap_phase_id"] == "S16-P2", "TaskPack S16-P2")
    add("source_tasks", contract["task_ids"] == ["S16P2T01", "S16P2T02", "S16P2T03"], "three exact tasks")
    snapshots = {metric_id: drilldown_snapshot(metric_id=metric_id) for metric_id in METRIC_SPECS}
    for metric_id, value in snapshots.items():
        add(f"{metric_id}_detail_available", value["detail_available"], "traceable detail")
        add(f"{metric_id}_context_preserved", value["context_preserved"] and value["filter_count"] == 4, "four filters")
        add(f"{metric_id}_rows_present", value["detail_row_count"] >= 3, str(value["detail_row_count"]))
        add(f"{metric_id}_primary_exact", value["consistency"]["primary_difference"] == 0, "zero difference")
        add(f"{metric_id}_secondary_exact", value["consistency"]["secondary_difference"] in (None, 0), "zero or n/a")
        add(f"{metric_id}_lineage_complete", value["explanation"]["lineage_complete"], "four lineage nodes")
        add(f"{metric_id}_plain_first", value["explanation"]["technical_log_default_visible"] is False, "plain Chinese first")
        add(f"{metric_id}_no_technical_log", value["explanation"]["technical_log_count"] == 0, "zero logs")
        add(f"{metric_id}_integer_only", not _contains_float(value), "no floats")
    for kind in COMPARISON_KINDS:
        value = drilldown_snapshot(metric_id="PROJECT_GROSS_PROFIT", comparison_kind=kind)
        add(f"comparison_{kind}_allowed", value["comparison"]["comparison_allowed"], "exact basis and coverage")
        add(f"comparison_{kind}_basis", value["comparison"]["basis_consistent"], "same basis")
        add(f"comparison_{kind}_coverage", value["comparison"]["coverage_consistent"], "same coverage")
    basis_mismatch = drilldown_snapshot(comparison_state="basis_mismatch")
    coverage_mismatch = drilldown_snapshot(comparison_state="coverage_mismatch")
    missing_lineage = drilldown_snapshot(lineage_state="missing")
    partial = drilldown_snapshot(metric_id="OVERDUE_RECEIVABLE", data_state="partial")
    add("basis_mismatch_blocked", not basis_mismatch["comparison"]["comparison_allowed"], "different basis blocked")
    add("basis_mismatch_reason", "口径不同" in basis_mismatch["comparison"]["block_reason_zh"], "human reason")
    add("coverage_mismatch_blocked", not coverage_mismatch["comparison"]["comparison_allowed"], "different coverage blocked")
    add("coverage_mismatch_reason", "覆盖范围不同" in coverage_mismatch["comparison"]["block_reason_zh"], "human reason")
    add("missing_lineage_blocked", not missing_lineage["detail_available"], "lineage required")
    add("missing_lineage_rows_hidden", missing_lineage["detail_rows"] == [], "no unsupported detail")
    add("missing_lineage_reason", "来源链不完整" in missing_lineage["explanation"]["block_reason_zh"], "human reason")
    add("partial_detail_blocked", not partial["detail_available"], "missing metric blocked")
    add("partial_comparison_blocked", not partial["comparison"]["comparison_allowed"], "missing comparison blocked")
    changed = drilldown_snapshot(company="demo-south", period="2026-Q2", project_status="attention", report_version="previous")
    add("context_company_preserved", changed["context"]["company"] == "demo-south", "company")
    add("context_period_preserved", changed["context"]["period"] == "2026-Q2", "period")
    add("context_project_status_preserved", changed["context"]["project_status"] == "attention", "project status")
    add("context_report_version_preserved", changed["context"]["report_version"] == "previous", "report version")
    denied = drilldown_snapshot(user_id="demo-finance", role_id="finance", company="demo-south")
    add("permission_denied", denied["allowed"] is False, "company permission")
    add("denied_payload_empty", denied["detail_rows"] == [], "no business rows")
    add("homepage_dependency_passed", homepage.build_contract()["public_check_failed_count"] == 0, "S16-P1 stable")
    add("real_conclusion_blocked", all(not value["real_business_conclusion_allowed"] for value in snapshots.values()), "public demo")
    add("fact_write_zero", all(value["fact_layer_write_count"] == 0 for value in snapshots.values()), "zero writes")
    add("raw_access_zero", all(value["raw_root_access_count"] == 0 for value in snapshots.values()), "zero raw")
    add("external_network_zero", all(value["external_network_request_count"] == 0 for value in snapshots.values()), "zero network")
    add("real_action_zero", all(value["real_business_action_count"] == 0 for value in snapshots.values()), "zero action")
    return checks


def build_contract() -> dict[str, Any]:
    checks = acceptance_checks()
    failed = [row for row in checks if row["status"] != "PASS"]
    if failed:
        raise DrilldownError("S16-P2 public checks failed: " + ", ".join(row["check_id"] for row in failed))
    default = drilldown_snapshot()
    return {
        "schema_version": "kmfa.v015.s16p2.public_contract.v1",
        "run_phase_id": RUN_PHASE_ID,
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "metric_count": len(METRIC_SPECS),
        "drilldown_route_count": len(METRIC_SLUGS),
        "preserved_filter_count": default["filter_count"],
        "default_lineage_node_count": default["explanation"]["professional_lineage_node_count"],
        "short_explanation_count": len(METRIC_SPECS),
        "technical_log_default_visible_count": 0,
        "technical_log_count": 0,
        "comparison_kind_count": len(COMPARISON_KINDS),
        "basis_mismatch_block_count": 1,
        "coverage_mismatch_block_count": 1,
        "homepage_detail_difference_cents": 0,
        "raw_root_access_count": 0,
        "live_source_read_count": 0,
        "external_network_request_count": 0,
        "real_business_action_count": 0,
        "public_check_total": len(checks),
        "public_check_pass_count": len(checks),
        "public_check_failed_count": 0,
        "checks": checks,
    }


if __name__ == "__main__":
    value = build_contract()
    print(f"PASS: {value['public_check_pass_count']}/{value['public_check_total']} public S16-P2 checks")
