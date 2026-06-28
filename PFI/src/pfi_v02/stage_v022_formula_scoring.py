from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Mapping, Sequence


STAGE7_CONFIDENCE_WEIGHTS = {
    "field_completeness": 30,
    "amount_direction": 10,
    "rule_match": 20,
    "counterparty": 15,
    "interconnection": 15,
    "history_consistency": 10,
}

STAGE7_REVIEW_THRESHOLD = 70
STAGE7_CASHFLOW_WINDOWS_DAYS = (7, 21, 30, 60, 90, 180, 360)
STAGE7_REQUIRED_CASHFLOW_VISUALIZATIONS = (
    "现金流阶梯图",
    "现金流瀑布图",
    "储备金安全带",
    "未来大额流出时间轴",
    "消费-投资挤压图",
    "现金流窗口对比表",
)


def _d(value: object) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _rate(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def _clamp(value: Decimal, low: Decimal = Decimal("0"), high: Decimal = Decimal("100")) -> Decimal:
    return max(low, min(high, value))


def build_confidence_scoring_model() -> dict[str, object]:
    standards = {
        "field_completeness": {
            "bands": ("0分", "低分", "中分", "高分", "满分"),
            "zero_zh": "0-7 分：缺少关键来源、金额或时间字段，无法可靠入账。",
            "low_zh": "8-14 分：缺少关键字段之一，倾向人工复核。",
            "medium_zh": "15-20 分：描述、对手方或来源批次不完整，需要谨慎。",
            "high_zh": "21-26 分：缺少非关键字段，但能正常分析。",
            "full_zh": "27-30 分：核心字段完整，可追溯。",
        },
        "amount_direction": {
            "bands": ("0分", "低分", "中分", "高分", "满分"),
            "zero_zh": "0 分：金额方向未知。",
            "low_zh": "3 分：方向和描述存在冲突。",
            "medium_zh": "6 分：方向只能由来源类型推断。",
            "high_zh": "8 分：金额正负明确，但描述略模糊。",
            "full_zh": "10 分：借贷方向或正负金额明确。",
        },
        "rule_match": {
            "bands": ("0分", "低分", "中分", "高分", "满分"),
            "zero_zh": "0 分：没有规则命中。",
            "low_zh": "8 分：只命中弱 fallback 规则。",
            "medium_zh": "12 分：仅命中分类关键词。",
            "high_zh": "16 分：强关键词和账户角色同时匹配。",
            "full_zh": "20 分：精确命中明确规则。",
        },
        "counterparty": {
            "bands": ("0分", "低分", "中分", "高分", "满分"),
            "zero_zh": "0 分：商户或对手方缺失或不可识别。",
            "low_zh": "5 分：仅关键词匹配。",
            "medium_zh": "9 分：高置信模糊匹配。",
            "high_zh": "12 分：命中别名或归一化名称。",
            "full_zh": "15 分：精确匹配商户或对手方字典。",
        },
        "interconnection": {
            "bands": ("0分", "低分", "中分", "高分", "满分"),
            "zero_zh": "0 分：关联矛盾或重复使用同一记录。",
            "low_zh": "7 分：应该匹配但目前只有单边记录。",
            "medium_zh": "7 分：单边记录需要等待后续来源补齐。",
            "high_zh": "11 分：高概率匹配。",
            "full_zh": "15 分：不需要关联，或已精确双边匹配。",
        },
        "history_consistency": {
            "bands": ("0分", "低分", "中分", "高分", "满分"),
            "zero_zh": "0 分：与历史记录冲突。",
            "low_zh": "2 分：明显异常。",
            "medium_zh": "5 分：新模式但合理。",
            "high_zh": "8 分：历史出现类似商户或分类。",
            "full_zh": "10 分：历史多次出现同模式。",
        },
    }
    return {
        "schema": "PFIV022Stage7ConfidenceScoringModelV1",
        "total_score": 100,
        "weights": STAGE7_CONFIDENCE_WEIGHTS,
        "review_threshold": STAGE7_REVIEW_THRESHOLD,
        "threshold_policy": "single_global_threshold",
        "source_layered_thresholds_allowed": False,
        "standards": standards,
        "impossible_state_policy_zh": "出现持仓负数、核心金额重复计入等不可能状态时直接进入复核。",
    }


def calculate_confidence_score(record: Mapping[str, object]) -> dict[str, object]:
    score_maps = {
        "field_completeness": {"complete": 30, "minor_missing": 24, "partial": 17, "missing_key_field": 11, "unusable": 0},
        "amount_direction": {"clear": 10, "clear_but_blurry": 8, "inferred": 6, "conflict": 3, "unknown": 0},
        "rule_match": {"exact": 20, "strong_role_match": 16, "keyword": 12, "weak_fallback": 8, "none": 0},
        "counterparty": {"exact": 15, "alias": 12, "fuzzy_high": 9, "keyword_only": 5, "missing": 0},
        "interconnection": {"not_required_or_exact": 15, "high_probability": 11, "single_sided_should_match": 7, "conflict_or_duplicate": 0},
        "history_consistency": {"repeated_pattern": 10, "similar_history": 8, "new_but_reasonable": 5, "abnormal": 2, "conflict": 0},
    }
    if record.get("impossible_state"):
        return {"score": 0, "requires_review": True, "reason_zh": "出现不可能状态，直接进入复核。"}

    total = 0
    detail: dict[str, int] = {}
    for key, mapping in score_maps.items():
        value = str(record.get(key, "none"))
        points = mapping.get(value, 0)
        detail[key] = points
        total += points

    deduction_total = 0
    deductions = record.get("deductions", {})
    if isinstance(deductions, Mapping):
        deduction_total += min(int(deductions.get("blurry_description", 0) or 0), 15)
        deduction_total += min(int(deductions.get("duplicate_suspect", 0) or 0), 20)
        deduction_total += min(int(deductions.get("stale_fx_snapshot", 0) or 0), 10)
    final_score = max(0, min(100, total - deduction_total))
    return {
        "schema": "PFIV022Stage7ConfidenceScoreV1",
        "score": final_score,
        "requires_review": final_score < STAGE7_REVIEW_THRESHOLD,
        "review_threshold": STAGE7_REVIEW_THRESHOLD,
        "component_scores": detail,
        "deductions": deduction_total,
    }


def calculate_consumption_model_metrics(events: Sequence[Mapping[str, object]]) -> dict[str, Decimal]:
    gross_included = {"consumption", "ordinary_consumption", "investment_deposit", "fund_subscription", "bullion_purchase", "investment_buy", "fee"}
    living_included = {"consumption", "ordinary_consumption"}
    gross = Decimal("0")
    living = Decimal("0")
    refund_offset = Decimal("0")
    for event in events:
        amount = abs(_d(event.get("amount_cny", "0")))
        event_type = str(event.get("event_type", ""))
        if event_type in gross_included:
            gross += amount
        if event_type in living_included:
            living += amount
        if event_type == "refund":
            refund_offset += amount
    return {
        "gross_consumption_cny": _money(gross - refund_offset),
        "living_consumption_cny": _money(living - refund_offset),
        "refund_offset_cny": _money(refund_offset),
    }


def is_large_spend(*, amount_cny: Decimal, original_amount: Decimal, original_currency: str) -> bool:
    if abs(amount_cny) >= Decimal("2000"):
        return True
    return original_currency.upper() == "AUD" and abs(original_amount) >= Decimal("500")


def is_night_spend(local_time: str) -> bool:
    hour, minute = (int(part) for part in local_time.split(":", 1))
    minutes = hour * 60 + minute
    return minutes >= 22 * 60 or minutes < 6 * 60


def calculate_subscription_score(
    amount_similarity: Decimal,
    period_stability: Decimal,
    merchant_similarity: Decimal,
    historical_repeat: Decimal,
) -> Decimal:
    score = (
        amount_similarity * Decimal("40")
        + period_stability * Decimal("30")
        + merchant_similarity * Decimal("20")
        + historical_repeat * Decimal("10")
    )
    return _money(score)


def calculate_investment_model_metrics(
    *,
    holdings: Sequence[Mapping[str, object]],
    realized_trades: Sequence[Mapping[str, object]],
    behavior_trades: Sequence[Mapping[str, object]],
    average_market_value_cny: Decimal,
    idle_cash_cny: Decimal,
    benchmark_return_pct: Decimal,
) -> dict[str, object]:
    market_value = sum(
        _d(item.get("quantity", "0")) * _d(item.get("latest_price", "0")) * _d(item.get("fx_to_cny", "1"))
        for item in holdings
    )
    remaining_cost = sum(_d(item.get("remaining_cost_cny", "0")) for item in holdings)
    realized_pnl = sum(
        _d(item.get("sell_proceeds_cny", "0"))
        - _d(item.get("allocated_cost_cny", "0"))
        - _d(item.get("fees_cny", "0"))
        - _d(item.get("tax_cny", "0"))
        for item in realized_trades
    )
    total_fee = sum(_d(item.get("fees_cny", "0")) for item in realized_trades)
    total_tax = sum(_d(item.get("tax_cny", "0")) for item in realized_trades)
    total_trade_amount = sum(abs(_d(item.get("amount_cny", "0"))) for item in behavior_trades)
    turnover_rate = total_trade_amount / average_market_value_cny if average_market_value_cny else Decimal("0")
    unrealized = market_value - remaining_cost
    behavior = {
        "chase_candidate": any(str(item.get("side")) == "buy" and _d(item.get("pre_trade_return_pct", "0")) >= Decimal("0.03") for item in behavior_trades),
        "panic_sell_candidate": any(str(item.get("side")) == "sell" and _d(item.get("pre_trade_return_pct", "0")) <= Decimal("-0.05") for item in behavior_trades),
        "short_hold_candidate": any(int(item.get("holding_days", 9999)) <= 3 for item in behavior_trades),
        "frequent_trading": len(behavior_trades) >= 6 or turnover_rate >= Decimal("0.50"),
        "turnover_rate": _rate(turnover_rate),
    }
    return {
        "schema": "PFIV022Stage7InvestmentMetricsV1",
        "market_value_cny": _money(market_value),
        "remaining_cost_cny": _money(remaining_cost),
        "unrealized_pnl_cny": _money(unrealized),
        "realized_pnl_cny": _money(realized_pnl),
        "total_pnl_cny": _money(realized_pnl + unrealized),
        "fee_drag_rate": _rate(total_fee / total_trade_amount if total_trade_amount else Decimal("0")),
        "tax_drag_rate": _rate(total_tax / realized_pnl if realized_pnl else Decimal("0")),
        "idle_cash_drag_cny": _money(idle_cash_cny * benchmark_return_pct),
        "behavior": behavior,
        "xirr_policy_zh": "XIRR 口径：投资入金：负现金流；投资回流：正现金流；当前投资市值：最终正现金流。",
    }


def calculate_cashflow_projection(
    *,
    horizon_days: int,
    current_life_cash_cny: Decimal,
    expected_income_cny: Decimal,
    expected_refund_cny: Decimal,
    fixed_expense_cny: Decimal,
    flexible_expense_cny: Decimal,
    debt_repayment_cny: Decimal,
    planned_investment_deposit_cny: Decimal,
    planned_investment_return_cny: Decimal,
    user_min_reserve_cny: Decimal,
    average_monthly_fixed_expense_cny: Decimal,
    reserve_months: Decimal,
    income_uncertainty: Decimal,
    large_spend_pressure: Decimal,
) -> dict[str, object]:
    if horizon_days not in STAGE7_CASHFLOW_WINDOWS_DAYS:
        raise ValueError("现金流窗口必须是 7/21/30/60/90/180/360 天之一。")
    future_balance = (
        current_life_cash_cny
        + expected_income_cny
        + expected_refund_cny
        - fixed_expense_cny
        - flexible_expense_cny
        - debt_repayment_cny
        - planned_investment_deposit_cny
        + planned_investment_return_cny
    )
    reserve_floor = max(user_min_reserve_cny, average_monthly_fixed_expense_cny * reserve_months)
    reserve_coverage = future_balance / reserve_floor if reserve_floor else Decimal("1")
    incoming = expected_income_cny + expected_refund_cny
    fixed_cost_pressure = fixed_expense_cny / incoming if incoming else Decimal("1")
    pressure = _clamp(
        Decimal("100")
        - Decimal("50") * reserve_coverage
        + Decimal("20") * fixed_cost_pressure
        + Decimal("15") * income_uncertainty
        + Decimal("15") * large_spend_pressure
    )
    return {
        "schema": "PFIV022Stage7CashflowProjectionV1",
        "horizon_days": horizon_days,
        "future_cash_balance_cny": _money(future_balance),
        "reserve_floor_cny": _money(reserve_floor),
        "reserve_coverage": _rate(reserve_coverage),
        "cashflow_pressure_score": _money(pressure),
        "investment_deposit_squeezes_life_cash": planned_investment_deposit_cny > 0 and future_balance < reserve_floor,
    }


def build_stage7_formula_catalog() -> dict[str, object]:
    return {
        "schema": "PFIV022Stage7FormulaCatalogV1",
        "confidence": build_confidence_scoring_model(),
        "consumption_model": {
            "formula_ids": ("gross_consumption_cny", "living_consumption_cny", "subscription_score"),
            "thresholds": {
                "large_spend": {"cny_threshold": Decimal("2000"), "aud_original_threshold": Decimal("500")},
                "night_window": {"start": "22:00", "end": "06:00", "electronics_impulse_independent_rule": False},
                "subscription_score_threshold": Decimal("75"),
            },
            "formula_zh": {
                "gross_consumption_cny": "消费总流出金额 = 生活消费 + 投资入金 + 基金申购 + 黄金申购 + 投资买入 + 金融费用 - 退款抵消。",
                "living_consumption_cny": "生活消费金额 = 普通生活消费 - 已关联退款 - 已关联撤销。",
                "subscription_score": "订阅评分 = 金额相似度 ×40% + 扣费周期稳定性 ×30% + 商户相似度 ×20% + 历史重复次数 ×10%。",
            },
        },
        "investment_model": {
            "formula_ids": ("investment_market_value_cny", "remaining_cost_cny", "unrealized_pnl_cny", "realized_pnl_cny", "total_pnl_cny", "xirr"),
            "thresholds": {
                "chase_candidate": {"lookback_days": 5, "pre_buy_rise_pct": Decimal("0.03")},
                "panic_sell_candidate": {"lookback_days": 5, "pre_sell_drop_pct": Decimal("-0.05")},
                "short_hold_days": 3,
                "frequent_trade_count_30d": 6,
                "turnover_rate_pct": Decimal("0.50"),
                "concentration_watch_pct": Decimal("0.35"),
                "concentration_high_risk_pct": Decimal("0.50"),
            },
            "formula_zh": {
                "investment_market_value_cny": "投资组合市值_CNY = 投资现金_CNY + Σ(持仓数量 × 最新价格 × 原币兑 CNY 汇率)。",
                "realized_pnl_cny": "已实现收益_CNY = 卖出收入 - 分摊成本 - 卖出费用 - 税费。",
                "total_pnl_cny": "总收益_CNY = 已实现收益 + 未实现收益 + 分红 + 利息 - 总费用 - 总税费。",
            },
        },
        "cashflow": {
            "windows_days": STAGE7_CASHFLOW_WINDOWS_DAYS,
            "reserve_months_default": 3,
            "required_visualizations": STAGE7_REQUIRED_CASHFLOW_VISUALIZATIONS,
            "formula_zh": {
                "future_cash_balance": "未来现金余额 = 当前生活现金 + 预计收入 + 预计退款/报销 - 固定支出 - 弹性支出 - 信用卡/债务还款 - 计划投资入金 + 计划投资回流。",
                "reserve_floor": "储备金底线 = max(用户自定义最低储备金, 平均月固定支出 × 储备月份数)。",
                "cashflow_pressure_score": "现金流压力分 = clamp(0,100,100 - 50×储备覆盖率 + 20×固定成本压力 + 15×收入不确定性 + 15×大额消费压力)。",
            },
        },
    }


def build_stage7_contract_payload() -> dict[str, object]:
    catalog = build_stage7_formula_catalog()
    return {
        "formula_catalog": catalog,
        "confidence_weights": STAGE7_CONFIDENCE_WEIGHTS,
        "review_threshold": STAGE7_REVIEW_THRESHOLD,
        "cashflow_windows_days": STAGE7_CASHFLOW_WINDOWS_DAYS,
        "cashflow_visualizations": STAGE7_REQUIRED_CASHFLOW_VISUALIZATIONS,
    }
