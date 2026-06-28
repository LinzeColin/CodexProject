from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal
from typing import Iterable, Mapping

from pfi_v02.stage_v022_interconnection import (
    InterconnectionRecord,
    aggregate_core_metrics,
    event_policy,
)


STAGE5_LEDGER_EVENT_TYPES = (
    "consumption",
    "investment_deposit",
    "fund_subscription",
    "bullion_purchase",
    "investment_buy",
    "investment_sell",
    "refund",
    "fee",
    "credit_card_repayment",
    "internal_transfer",
    "income",
    "valuation",
    "fx_conversion",
)

STAGE5_TAXONOMY_LIMITS = {
    "max_l1_categories": 12,
    "max_l2_per_l1": 5,
    "max_l2_total": 50,
    "primary_category_per_transaction": 1,
    "future_merge_target_max_l1": 10,
    "multi_dimensional_analysis_uses_tags": True,
}


@dataclass(frozen=True)
class Stage5LedgerEventTypePolicy:
    event_type: str
    label_zh: str
    affects_total_consumption_outflow: bool
    affects_living_consumption: bool
    affects_investment: bool
    affects_net_worth: bool
    affects_cashflow: bool
    homepage_display: str
    consumption_display: str
    investment_display: str
    cashflow_display: str
    report_display: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _stage4_policy_payload(event_type: str) -> Stage5LedgerEventTypePolicy:
    policy = event_policy(event_type)
    return Stage5LedgerEventTypePolicy(
        event_type=policy.event_type,
        label_zh=policy.label_zh,
        affects_total_consumption_outflow=policy.affects_total_consumption_outflow,
        affects_living_consumption=policy.affects_living_consumption,
        affects_investment=policy.affects_investment,
        affects_net_worth=policy.affects_net_worth,
        affects_cashflow=policy.affects_cashflow,
        homepage_display=policy.homepage_display,
        consumption_display=policy.consumption_display,
        investment_display=policy.investment_display,
        cashflow_display=policy.cashflow_display,
        report_display=policy.report_display,
    )


def build_stage5_ledger_event_type_table() -> tuple[dict[str, object], ...]:
    """Return the Stage 5 event table used by ledger and double-consumption rules."""
    rows: list[dict[str, object]] = []
    for event_type in STAGE5_LEDGER_EVENT_TYPES:
        if event_type == "valuation":
            rows.append(
                Stage5LedgerEventTypePolicy(
                    event_type="valuation",
                    label_zh="估值",
                    affects_total_consumption_outflow=False,
                    affects_living_consumption=False,
                    affects_investment=True,
                    affects_net_worth=True,
                    affects_cashflow=False,
                    homepage_display="首页可展示资产估值变化，但不作为现金流出。",
                    consumption_display="不计入消费。",
                    investment_display="计入投资资产估值变化。",
                    cashflow_display="不影响现金流。",
                    report_display="报告中作为资产估值或价格变动展示。",
                ).to_dict()
            )
            continue
        rows.append(_stage4_policy_payload(event_type).to_dict())
    return tuple(rows)


def build_stage5_double_consumption_dashboard(
    records: Iterable[InterconnectionRecord],
) -> dict[str, object]:
    metrics = aggregate_core_metrics(records)
    gross = metrics["total_consumption_outflow_cny"]
    living = metrics["living_consumption_cny"]
    if not isinstance(gross, Decimal) or not isinstance(living, Decimal):
        raise TypeError("Stage 5 metrics must be Decimal values")
    difference = (
        "消费总流出包含生活消费、投资入金、基金申购、黄金申购、投资买入和金融费用；"
        "生活消费只保留普通生活支出，排除投资入金、基金申购、黄金申购、投资买入、内部转账和信用卡还款。"
    )
    surface_payload = {
        "gross_consumption_label_zh": "消费总流出",
        "living_consumption_label_zh": "生活消费",
        "gross_consumption_cny": gross,
        "living_consumption_cny": living,
        "currency": "CNY",
        "difference_explanation_zh": difference,
    }
    return {
        "schema": "PFIV022Stage5DoubleConsumptionDashboardV1",
        "metrics": {
            "gross_consumption_cny": gross,
            "living_consumption_cny": living,
            "difference_cny": gross - living,
        },
        "surfaces": {
            "homepage": dict(surface_payload),
            "consumption_page": dict(surface_payload),
            "report": dict(surface_payload),
        },
    }


def _l2_items(l1_key: str, labels: tuple[str, ...]) -> tuple[dict[str, str], ...]:
    return tuple({"l2_key": f"{l1_key}_{index:02d}", "label_zh": label} for index, label in enumerate(labels, 1))


def build_stage5_consumption_taxonomy() -> tuple[dict[str, object], ...]:
    taxonomy = (
        ("food", "餐饮食品", ("外出就餐", "外卖", "咖啡饮品", "超市食品", "零食饮料"), "生活必要"),
        ("housing", "居住家庭", ("房租房贷", "水电燃气", "网络通讯", "家居维修"), "生活必要"),
        ("transport", "交通出行", ("公共交通", "打车网约", "车辆油电", "停车路桥", "长途交通"), "出行与成长"),
        ("shopping", "购物用品", ("日用百货", "服饰鞋包", "数码家电", "美妆个护", "家居用品"), "可选消费"),
        ("health", "医疗健康", ("门诊药品", "保险保障", "健身运动", "牙科眼科"), "生活必要"),
        ("education", "教育成长", ("课程培训", "书籍资料", "考试认证", "学习工具"), "出行与成长"),
        ("entertainment", "娱乐社交", ("影视游戏", "活动票务", "社交聚餐", "礼物红包", "休闲旅行"), "可选消费"),
        ("subscription", "订阅服务", ("影音会员", "软件工具", "云服务", "平台会员"), "可选消费"),
        ("financial_fee", "金融费用", ("银行费用", "支付手续费", "汇兑成本", "贷款利息", "税费罚款"), "金融成本"),
        ("investment_outflow", "投资资金流出", ("证券入金", "基金申购", "黄金申购", "其他投资入金"), "投资资金流"),
        ("family_responsibility", "家庭责任", ("家庭支持", "人情往来", "报销垫付"), "家庭责任"),
        ("adjustment_other", "调整其他", ("退款抵扣", "未分类其他"), "调整其他"),
    )
    return tuple(
        {
            "l1_key": l1_key,
            "l1_label_zh": label,
            "l2": _l2_items(l1_key, l2_labels),
            "future_merge_to": future_merge_to,
            "merge_candidate": future_merge_to,
            "primary_category_per_transaction": 1,
        }
        for l1_key, label, l2_labels, future_merge_to in taxonomy
    )


def validate_stage5_taxonomy_constraints(
    taxonomy: Iterable[Mapping[str, object]] | None = None,
) -> dict[str, object]:
    rows = tuple(build_stage5_consumption_taxonomy() if taxonomy is None else taxonomy)
    l2_counts = [len(tuple(row.get("l2", ()))) for row in rows]
    l2_total = sum(l2_counts)
    l1_count = len(rows)
    max_l1_ok = l1_count <= STAGE5_TAXONOMY_LIMITS["max_l1_categories"]
    max_l2_per_l1_ok = all(count <= STAGE5_TAXONOMY_LIMITS["max_l2_per_l1"] for count in l2_counts)
    max_l2_total_ok = l2_total <= STAGE5_TAXONOMY_LIMITS["max_l2_total"]
    future_merge_ready = all(row.get("future_merge_to") or row.get("merge_candidate") for row in rows)
    future_merge_groups = tuple(
        sorted({str(row.get("future_merge_to") or row.get("merge_candidate")) for row in rows if row.get("future_merge_to") or row.get("merge_candidate")})
    )
    future_merge_l1_count = len(future_merge_groups)
    future_merge_target_ok = future_merge_l1_count <= STAGE5_TAXONOMY_LIMITS["future_merge_target_max_l1"]
    primary_category_ok = all(
        row.get("primary_category_per_transaction") == STAGE5_TAXONOMY_LIMITS["primary_category_per_transaction"]
        for row in rows
    )
    violations: list[str] = []
    if not max_l1_ok:
        violations.append("max_l1_categories")
    if not max_l2_per_l1_ok:
        violations.append("max_l2_per_l1")
    if not max_l2_total_ok:
        violations.append("max_l2_total")
    if not future_merge_ready:
        violations.append("future_merge_to")
    if not future_merge_target_ok:
        violations.append("future_merge_target_max_l1")
    if not primary_category_ok:
        violations.append("primary_category_per_transaction")
    within_limits = not violations
    return {
        "schema": "PFIV022Stage5TaxonomyValidationV1",
        "status": "通过" if within_limits and future_merge_ready else "失败",
        "l1_count": l1_count,
        "max_l2_per_l1_actual": max(l2_counts) if l2_counts else 0,
        "l2_total": l2_total,
        "future_merge_ready": future_merge_ready,
        "future_merge_groups": future_merge_groups,
        "future_merge_l1_count": future_merge_l1_count,
        "future_merge_target_max_l1": STAGE5_TAXONOMY_LIMITS["future_merge_target_max_l1"],
        "primary_category_per_transaction": STAGE5_TAXONOMY_LIMITS["primary_category_per_transaction"],
        "primary_category_per_transaction_valid": primary_category_ok,
        "multi_dimensional_analysis_uses_tags": STAGE5_TAXONOMY_LIMITS["multi_dimensional_analysis_uses_tags"],
        "violations": tuple(violations),
        "limits": dict(STAGE5_TAXONOMY_LIMITS),
    }


def build_stage5_contract_payload() -> dict[str, object]:
    taxonomy = build_stage5_consumption_taxonomy()
    return {
        "ledger_event_type_table": build_stage5_ledger_event_type_table(),
        "taxonomy": taxonomy,
        "taxonomy_validation": validate_stage5_taxonomy_constraints(taxonomy),
        "double_consumption_surface_required": ("homepage", "consumption_page", "report"),
    }
