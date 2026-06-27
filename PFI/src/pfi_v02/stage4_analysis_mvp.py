from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Iterable

from pfi_v02.stage3_read_mvp import SIMPLE_STATUS_LANGUAGE, STAGE3_FX_TO_AUD, build_stage3_read_model


STAGE4_INVESTMENT_ATTRIBUTION_COMPONENTS = (
    "market",
    "active_decision",
    "fees",
    "fx",
    "cash_drag",
)

STAGE4_CONSUMPTION_SOURCES = ("alipay_daily", "cba_bank", "wechat_pay")


@dataclass(frozen=True)
class Stage4InvestmentPosition:
    instrument_id: str
    display_name: str
    asset_class: str
    account_id: str
    currency: str
    market_value: float
    cost_basis: float
    liquidity_days: int
    evidence_ref: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class Stage4InvestmentTrade:
    trade_id: str
    instrument_id: str
    side: str
    amount: float
    currency: str
    occurred_at: str
    holding_days_after_trade: int
    price_move_before_trade_pct: float
    evidence_ref: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class Stage4SpendingRecord:
    record_id: str
    source_id: str
    merchant: str
    category: str
    amount: float
    currency: str
    occurred_at: str
    confidence: float
    evidence_ref: str
    is_fixed: bool = False
    is_transfer: bool = False
    is_investment: bool = False
    recurring_hint: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def build_stage4_demo_positions() -> tuple[Stage4InvestmentPosition, ...]:
    return (
        Stage4InvestmentPosition("SPY", "SPY ETF", "ETF", "acct_moomoo_au", "USD", 12000.0, 11200.0, 2, "pos:moomoo:SPY"),
        Stage4InvestmentPosition("ALIPAY_FUND_001", "支付宝基金组合", "FUND", "acct_alipay_fund", "CNY", 11980.0, 11000.0, 3, "pos:alipay_fund:001"),
        Stage4InvestmentPosition("CN_EQ_001", "中国券商股票组合", "EQUITY", "acct_cn_broker", "CNY", 66000.0, 69000.0, 5, "pos:cn_broker:portfolio"),
        Stage4InvestmentPosition("ABC_GOLD", "ABC Bullion 黄金", "BULLION", "acct_abc_bullion", "AUD", 4200.0, 3900.0, 10, "pos:abc_bullion:gold"),
    )


def build_stage4_demo_trades() -> tuple[Stage4InvestmentTrade, ...]:
    return (
        Stage4InvestmentTrade("trade_spy_buy_001", "SPY", "BUY", 1200.0, "USD", "2026-06-24", 2, 4.2, "trade:moomoo:SPY:001"),
        Stage4InvestmentTrade("trade_cn_sell_001", "CN_EQ_001", "SELL", 3200.0, "CNY", "2026-06-20", 4, -5.6, "trade:cn_broker:001"),
        Stage4InvestmentTrade("trade_fund_buy_001", "ALIPAY_FUND_001", "BUY", 800.0, "CNY", "2026-06-27", 1, 1.8, "trade:alipay_fund:001"),
    )


def build_stage4_demo_spending_records() -> tuple[Stage4SpendingRecord, ...]:
    return (
        Stage4SpendingRecord("spend_alipay_coffee_001", "alipay_daily", "本地咖啡", "餐饮", 18.50, "CNY", "2026-06-27T10:00:00", 0.95, "txn:alipay:coffee"),
        Stage4SpendingRecord("spend_wechat_transport_001", "wechat_pay", "地铁公交", "交通", 22.00, "CNY", "2026-06-27T18:20:00", 0.92, "txn:wechat:transport"),
        Stage4SpendingRecord("spend_cba_grocery_001", "cba_bank", "Woolworths", "食品日用", 86.40, "AUD", "2026-06-26T17:30:00", 0.97, "txn:cba:grocery"),
        Stage4SpendingRecord("spend_cba_rent_001", "cba_bank", "Rent", "住房", 2300.00, "AUD", "2026-06-01T09:00:00", 0.99, "txn:cba:rent", is_fixed=True),
        Stage4SpendingRecord("spend_cba_spotify_001", "cba_bank", "Spotify", "订阅", 18.99, "AUD", "2026-06-05T06:00:00", 0.98, "txn:cba:spotify", is_fixed=True, recurring_hint="monthly"),
        Stage4SpendingRecord("spend_cba_gym_001", "cba_bank", "Gym Membership", "订阅", 59.00, "AUD", "2026-06-07T06:00:00", 0.96, "txn:cba:gym", is_fixed=True, recurring_hint="monthly"),
        Stage4SpendingRecord("spend_alipay_night_001", "alipay_daily", "夜间外卖", "餐饮", 168.00, "CNY", "2026-06-27T23:48:00", 0.58, "txn:alipay:night_food"),
        Stage4SpendingRecord("spend_cba_duplicate_001", "cba_bank", "Online Store", "购物", 42.00, "AUD", "2026-06-25T21:00:00", 0.94, "txn:cba:online_store:1"),
        Stage4SpendingRecord("spend_cba_duplicate_002", "cba_bank", "Online Store", "购物", 42.00, "AUD", "2026-06-25T21:03:00", 0.94, "txn:cba:online_store:2"),
        Stage4SpendingRecord("spend_cba_electronics_001", "cba_bank", "Electronics Express", "购物", 950.00, "AUD", "2026-06-27T23:10:00", 0.90, "txn:cba:electronics"),
        Stage4SpendingRecord("xfer_cba_moomoo_001", "cba_bank", "CBA to Moomoo", "转账", 5000.00, "AUD", "2026-06-28T09:00:00", 0.99, "txn:cba:transfer", is_transfer=True),
        Stage4SpendingRecord("invest_alipay_fund_001", "alipay_daily", "支付宝基金申购", "投资", 800.00, "CNY", "2026-06-27T11:00:00", 0.98, "txn:alipay:fund_sub", is_investment=True),
    )


def build_stage4_analysis_model(
    *,
    stage3_dashboard: dict[str, object] | None = None,
    positions: tuple[Stage4InvestmentPosition, ...] | None = None,
    trades: tuple[Stage4InvestmentTrade, ...] | None = None,
    spending_records: tuple[Stage4SpendingRecord, ...] | None = None,
    now: datetime | None = None,
) -> dict[str, object]:
    stage3 = stage3_dashboard or build_stage3_read_model(now=now)
    position_rows = positions or build_stage4_demo_positions()
    trade_rows = trades or build_stage4_demo_trades()
    spending_rows = spending_records or build_stage4_demo_spending_records()
    generated_at = (now or datetime.now(timezone.utc)).isoformat(timespec="seconds")

    investment = {
        "summary": build_investment_summary(position_rows, stage3),
        "attribution": build_investment_attribution(position_rows, trade_rows),
        "risk": build_investment_risk(position_rows),
        "behavior": build_investment_behavior_review(trade_rows),
        "qbvs_compatibility": build_qbvs_compatibility_contract(),
    }
    consumption = {
        "summary": build_consumption_summary(spending_rows, stage3),
        "classification": build_consumption_classification(spending_rows),
        "recurring": build_recurring_subscription_detection(spending_rows),
        "anomalies": build_consumption_anomalies(spending_rows),
        "cashflow_forecast": build_cashflow_forecast(spending_rows, stage3),
    }
    return {
        "schema": "PFIV02Stage4AnalysisMVPV1",
        "stage": "PFI V0.2 Stage 4",
        "generated_at": generated_at,
        "stage3_schema": stage3.get("schema", ""),
        "investment_analysis": investment,
        "consumption_analysis": consumption,
        "metric_cards": _stage4_metric_cards(investment, consumption),
        "decision_rows": _stage4_decision_rows(investment, consumption),
        "compatibility": {
            "primary_entry_count": 8,
            "alpha_first_level_entry_added": False,
            "ralpha_first_level_entry_added": False,
            "system_first_level_entry_added": False,
            "qbvs_independent_system": True,
            "qbvs_owned_by_pfi": False,
            "qbvs_runtime_moved_out_of_pfi": True,
        },
        "status_language": SIMPLE_STATUS_LANGUAGE,
        "boundaries": (
            "synthetic_or_local_analysis_only",
            "no_trading_password",
            "no_broker_order_submission",
            "no_payment_submission",
            "no_precise_conclusion_when_data_insufficient",
            "transfers_and_investments_excluded_from_consumption",
        ),
    }


def build_investment_summary(
    positions: tuple[Stage4InvestmentPosition, ...],
    stage3_dashboard: dict[str, object],
) -> dict[str, object]:
    total_market_value = sum(_to_aud(row.market_value, row.currency) for row in positions)
    total_cost_basis = sum(_to_aud(row.cost_basis, row.currency) for row in positions)
    unrealized_pnl = total_market_value - total_cost_basis
    allocation = _allocation_by(positions, lambda item: item.asset_class)
    investment_cash = _stage3_investment_cash_position(stage3_dashboard)
    return {
        "total_market_value_aud": round(total_market_value, 2),
        "total_unrealized_pnl_aud": round(unrealized_pnl, 2),
        "total_return_pct": round((unrealized_pnl / total_cost_basis) * 100, 2) if total_cost_basis else 0.0,
        "asset_allocation_pct": allocation,
        "cash_position_aud": round(investment_cash, 2),
        "evidence_refs": tuple(row.evidence_ref for row in positions),
        "excluded_event_types": ("consumption", "transfer", "credit_card_repayment"),
        "stop_condition_check": "投资分析只读取投资持仓/账户，不混入消费流水。",
    }


def build_investment_attribution(
    positions: tuple[Stage4InvestmentPosition, ...],
    trades: tuple[Stage4InvestmentTrade, ...],
) -> dict[str, object]:
    total_pnl = sum(_to_aud(row.market_value - row.cost_basis, row.currency) for row in positions)
    components = (
        _component("market", total_pnl * 0.52, ("pos:market_proxy",), "市场 beta 代理分解，非精确归因。"),
        _component("active_decision", total_pnl * 0.31, tuple(row.evidence_ref for row in trades), "主动买卖和持仓选择贡献估计。"),
        _component("fees", -18.40, ("fees:brokerage_fixture",), "费用为本地 fixture，真实费用需导入后复核。"),
        _component("fx", total_pnl * 0.11, ("fx:stage3_fixture",), "使用 Stage 3 本地汇率 fixture，不是实时汇率。"),
        _component("cash_drag", -42.00, ("cash:investment_idle",), "现金仓位拖累估计。"),
    )
    return {
        "components": components,
        "component_order": STAGE4_INVESTMENT_ATTRIBUTION_COMPONENTS,
        "precision_policy": "insufficient_data_blocks_exact_conclusion",
        "status": "需要复核",
        "summary": "收益归因为本地可解释估计；真实市场、费用和 FX 数据不足时不输出精确结论。",
    }


def build_investment_risk(positions: tuple[Stage4InvestmentPosition, ...]) -> dict[str, object]:
    total = sum(_to_aud(row.market_value, row.currency) for row in positions)
    largest = max((_to_aud(row.market_value, row.currency), row) for row in positions)
    currency = _allocation_by(positions, lambda item: item.currency)
    liquidity_weighted_days = (
        sum(_to_aud(row.market_value, row.currency) * row.liquidity_days for row in positions) / total
        if total
        else 0.0
    )
    return {
        "concentration": {
            "largest_instrument_id": largest[1].instrument_id,
            "largest_weight_pct": round(largest[0] / total * 100, 2) if total else 0.0,
            "status": "需要复核" if total and largest[0] / total > 0.35 else "正常",
            "evidence_refs": (largest[1].evidence_ref,),
        },
        "drawdown": {
            "max_drawdown_pct": -8.40,
            "status": "有建议",
            "evidence_refs": ("risk:drawdown_fixture",),
        },
        "currency_exposure_pct": currency,
        "liquidity": {
            "weighted_liquidity_days": round(liquidity_weighted_days, 2),
            "slowest_position_days": max((row.liquidity_days for row in positions), default=0),
            "status": "有建议" if liquidity_weighted_days > 5 else "正常",
            "evidence_refs": tuple(row.evidence_ref for row in positions),
        },
    }


def build_investment_behavior_review(trades: Iterable[Stage4InvestmentTrade]) -> dict[str, object]:
    trade_rows = tuple(trades)
    if not trade_rows:
        return {
            "status": "需要同步",
            "trade_count": 0,
            "tags": (),
            "conclusions": (),
            "evidence_refs": (),
            "data_requirement": "缺少交易数据时不得生成追涨、杀跌或频繁交易结论。",
        }
    tags: list[dict[str, object]] = []
    for trade in trade_rows:
        if trade.side == "BUY" and trade.price_move_before_trade_pct >= 3.0:
            tags.append(_behavior_tag("追涨", trade.trade_id, trade.evidence_ref, "买入前短期涨幅超过 3%。"))
        if trade.side == "SELL" and trade.price_move_before_trade_pct <= -5.0:
            tags.append(_behavior_tag("杀跌", trade.trade_id, trade.evidence_ref, "卖出前短期跌幅超过 5%。"))
        if trade.holding_days_after_trade <= 3:
            tags.append(_behavior_tag("持有周期过短", trade.trade_id, trade.evidence_ref, "交易后持有周期不超过 3 天。"))
    if len(trade_rows) >= 3:
        tags.append(_behavior_tag("频繁交易", "trade_window_202606", "trades:stage4_fixture", "样本窗口内交易次数达到复核阈值。"))
    return {
        "status": "有建议" if tags else "正常",
        "trade_count": len(trade_rows),
        "tags": tuple(tags),
        "conclusions": tuple(tag["label"] for tag in tags),
        "evidence_refs": tuple(row.evidence_ref for row in trade_rows),
        "data_requirement": "行为复盘只在存在交易证据时生成标签。",
    }


def build_qbvs_compatibility_contract() -> dict[str, object]:
    return {
        "status": "正常",
        "target_entry": "独立系统：CodexProject/QBVS",
        "pfi_strategy_lab_entry": "投资管理 > PFI 策略实验室 / 大数据模拟器 / 盘感训练",
        "legacy_runtime_path": "QBVS/qbvs",
        "compatibility_smoke": "tests.test_s3pct02_lifecycle",
        "runtime_moved_out_of_pfi": True,
        "pfi_owns_qbvs": False,
        "preserved_pfi_features": ("策略回测", "参数扫描", "盘感训练", "大数据模拟器"),
        "external_qbvs_policy": "PFI does not cover QBVS. QBVS is a separate top-level system with its own tests and GitHub-visible files.",
    }


def build_consumption_summary(
    records: tuple[Stage4SpendingRecord, ...],
    stage3_dashboard: dict[str, object],
    *,
    monthly_budget_aud: float = 3600.0,
) -> dict[str, object]:
    spend_rows = _consumption_records(records)
    total_spend = sum(_to_aud(row.amount, row.currency) for row in spend_rows)
    fixed = sum(_to_aud(row.amount, row.currency) for row in spend_rows if row.is_fixed)
    flexible = total_spend - fixed
    transfer_total = sum(_to_aud(row.amount, row.currency) for row in records if row.is_transfer)
    investment_total = sum(_to_aud(row.amount, row.currency) for row in records if row.is_investment)
    return {
        "month_spend_aud": round(total_spend, 2),
        "monthly_budget_aud": monthly_budget_aud,
        "budget_remaining_aud": round(monthly_budget_aud - total_spend, 2),
        "fixed_spend_aud": round(fixed, 2),
        "flexible_spend_aud": round(flexible, 2),
        "source_count": len({row.source_id for row in spend_rows}),
        "source_ids": tuple(sorted({row.source_id for row in spend_rows})),
        "excluded_transfer_aud": round(transfer_total, 2),
        "excluded_investment_aud": round(investment_total, 2),
        "stage3_ledger_rows": len(stage3_dashboard.get("ledger", [])),
        "stop_condition_check": "转账、基金申购和投资买卖已排除在生活消费外。",
    }


def build_consumption_classification(records: tuple[Stage4SpendingRecord, ...]) -> dict[str, object]:
    rows = []
    review_queue = []
    for record in _consumption_records(records):
        status = "需要复核" if record.confidence < 0.70 else "正常"
        row = {
            "record_id": record.record_id,
            "source_id": record.source_id,
            "category": record.category,
            "confidence": record.confidence,
            "status": status,
            "evidence_ref": record.evidence_ref,
            "choices": ("A 接受分类", "B 改为转账", "C 改为投资", "D 保持待复核"),
        }
        rows.append(row)
        if status == "需要复核":
            review_queue.append(row)
    return {
        "covered_sources": tuple(sorted({row["source_id"] for row in rows})),
        "rows": tuple(rows),
        "review_queue": tuple(review_queue),
        "low_confidence_policy": "低置信度消费分类必须进入复核，不直接入账为确定分类。",
    }


def build_recurring_subscription_detection(records: tuple[Stage4SpendingRecord, ...]) -> dict[str, object]:
    candidates = []
    for record in _consumption_records(records):
        if record.recurring_hint or record.category == "订阅":
            candidates.append(
                {
                    "record_id": record.record_id,
                    "merchant": record.merchant,
                    "amount_aud": round(_to_aud(record.amount, record.currency), 2),
                    "cadence": record.recurring_hint or "suspected_monthly",
                    "status": "有建议",
                    "review_action": "确认保留 / 取消 / 暂缓复盘",
                    "evidence_ref": record.evidence_ref,
                }
            )
    return {
        "candidate_count": len(candidates),
        "candidates": tuple(candidates),
        "review_supported": True,
    }


def build_consumption_anomalies(records: tuple[Stage4SpendingRecord, ...]) -> dict[str, object]:
    spend_rows = _consumption_records(records)
    anomalies: list[dict[str, object]] = []
    seen: dict[tuple[str, float, str], Stage4SpendingRecord] = {}
    for record in spend_rows:
        amount_aud = _to_aud(record.amount, record.currency)
        hour = _hour(record.occurred_at)
        if amount_aud >= 500 and not record.is_fixed:
            anomalies.append(_anomaly("大额消费", record, f"AUD {amount_aud:.2f} 超过本地大额阈值。"))
        if hour >= 23 or hour < 5:
            anomalies.append(_anomaly("夜间消费", record, "交易发生在夜间复核窗口。"))
        if _is_weekend(record.occurred_at) and record.category in {"购物", "餐饮"}:
            anomalies.append(_anomaly("节假日/周末消费", record, "周末消费进入行为复盘。"))
        if record.merchant.lower().startswith("electronics") and amount_aud >= 300 and (hour >= 23 or hour < 5):
            anomalies.append(_anomaly("冲动型消费", record, "电子产品大额夜间消费需要复盘。"))
        duplicate_key = (record.merchant.lower(), round(amount_aud, 2), record.occurred_at[:10])
        if duplicate_key in seen:
            anomalies.append(_anomaly("重复扣费", record, f"疑似与 {seen[duplicate_key].record_id} 重复。"))
        else:
            seen[duplicate_key] = record
    return {
        "anomaly_count": len(anomalies),
        "anomalies": tuple(anomalies),
        "evidence_required": True,
    }


def build_cashflow_forecast(
    records: tuple[Stage4SpendingRecord, ...],
    stage3_dashboard: dict[str, object],
    *,
    monthly_income_aud: float = 7200.0,
    reserve_floor_aud: float = 5000.0,
) -> dict[str, object]:
    summary = build_consumption_summary(records, stage3_dashboard)
    monthly_spend = float(summary["month_spend_aud"])
    life_cash = _stage3_life_cash(stage3_dashboard)
    investment_cash = _stage3_investment_cash_position(stage3_dashboard)
    horizons = []
    for days, months in ((30, 1), (90, 3), (180, 6)):
        projected_spend = monthly_spend * months
        projected_income = monthly_income_aud * months
        investable = max(0.0, life_cash + projected_income - projected_spend - reserve_floor_aud)
        horizons.append(
            {
                "days": days,
                "projected_spend_aud": round(projected_spend, 2),
                "projected_income_aud": round(projected_income, 2),
                "available_to_invest_aud": round(investable, 2),
                "cashflow_pressure": "正常" if investable >= 1000 else "需要复核",
                "evidence_refs": ("cashflow:stage4_fixture", "stage3:accounts"),
            }
        )
    return {
        "life_cash_aud": round(life_cash, 2),
        "investment_cash_aud": round(investment_cash, 2),
        "reserve_floor_aud": reserve_floor_aud,
        "horizons": tuple(horizons),
        "cash_separation_policy": "生活现金和投资现金分开计算；可投资现金不得吞掉生活 reserve。",
    }


def _stage4_metric_cards(investment: dict[str, object], consumption: dict[str, object]) -> tuple[dict[str, str], ...]:
    inv_summary = investment["summary"]
    con_summary = consumption["summary"]
    cashflow = consumption["cashflow_forecast"]
    first_horizon = cashflow["horizons"][0]
    return (
        _card("investment_market_value", "投资市值", _money(inv_summary["total_market_value_aud"]), "投资持仓折算 AUD；消费流水不混入。"),
        _card("investment_pnl", "投资盈亏", _money(inv_summary["total_unrealized_pnl_aud"]), "未实现盈亏；归因仍需复核。"),
        _card("month_spend", "本月支出", _money(con_summary["month_spend_aud"]), "生活消费合计；转账和投资已排除。"),
        _card("budget_remaining", "预算剩余", _money(con_summary["budget_remaining_aud"]), "月预算减本月生活消费。"),
        _card("cashflow_pressure", "现金流压力", first_horizon["cashflow_pressure"], "30 天预测；生活现金和投资现金分开。"),
    )


def _stage4_decision_rows(investment: dict[str, object], consumption: dict[str, object]) -> tuple[dict[str, str], ...]:
    risk = investment["risk"]["concentration"]
    recurring = consumption["recurring"]
    anomalies = consumption["anomalies"]
    behavior = investment["behavior"]
    return (
        _decision("P1", "投资管理", ",".join(risk["evidence_refs"]), "复核最大持仓集中度", risk["status"]),
        _decision("P1", "消费管理", f"{anomalies['anomaly_count']} 条异常", "处理大额/重复/夜间消费", "需要复核" if anomalies["anomaly_count"] else "正常"),
        _decision("P2", "消费管理", f"{recurring['candidate_count']} 个订阅", "确认订阅保留或取消", "有建议" if recurring["candidate_count"] else "正常"),
        _decision("P2", "投资管理", f"{behavior['trade_count']} 条交易", "查看交易行为复盘", behavior["status"]),
    )


def _consumption_records(records: tuple[Stage4SpendingRecord, ...]) -> tuple[Stage4SpendingRecord, ...]:
    return tuple(row for row in records if not row.is_transfer and not row.is_investment)


def _allocation_by(
    positions: tuple[Stage4InvestmentPosition, ...],
    key_fn,
) -> tuple[dict[str, object], ...]:
    totals: dict[str, float] = {}
    total = 0.0
    for row in positions:
        value = _to_aud(row.market_value, row.currency)
        label = str(key_fn(row))
        totals[label] = totals.get(label, 0.0) + value
        total += value
    return tuple(
        {"bucket": key, "weight_pct": round(value / total * 100, 2), "market_value_aud": round(value, 2)}
        for key, value in sorted(totals.items())
    )


def _stage3_life_cash(stage3_dashboard: dict[str, object]) -> float:
    stage3_dashboard = _ensure_stage3_dashboard(stage3_dashboard)
    total = 0.0
    for account in stage3_dashboard.get("accounts", []):
        if not isinstance(account, dict):
            continue
        if account.get("category") in {"daily", "cash", "liability"}:
            total += _to_aud(float(account.get("ledger_balance", 0.0)), str(account.get("currency", "AUD")))
    return total


def _stage3_investment_cash_position(stage3_dashboard: dict[str, object]) -> float:
    stage3_dashboard = _ensure_stage3_dashboard(stage3_dashboard)
    total = 0.0
    for account in stage3_dashboard.get("accounts", []):
        if not isinstance(account, dict):
            continue
        if account.get("category") == "investment" and str(account.get("display_name", "")).lower().find("cash") >= 0:
            total += _to_aud(float(account.get("ledger_balance", 0.0)), str(account.get("currency", "AUD")))
    return total


def _ensure_stage3_dashboard(stage3_dashboard: dict[str, object]) -> dict[str, object]:
    if isinstance(stage3_dashboard, dict) and stage3_dashboard.get("accounts"):
        return stage3_dashboard
    return build_stage3_read_model()


def _component(name: str, value_aud: float, evidence_refs: tuple[str, ...], note: str) -> dict[str, object]:
    return {
        "component": name,
        "value_aud": round(value_aud, 2),
        "precision": "estimate",
        "evidence_refs": evidence_refs,
        "note": note,
    }


def _behavior_tag(label: str, trade_id: str, evidence_ref: str, reason: str) -> dict[str, str]:
    return {"label": label, "trade_id": trade_id, "evidence_ref": evidence_ref, "reason": reason}


def _anomaly(kind: str, record: Stage4SpendingRecord, reason: str) -> dict[str, object]:
    return {
        "kind": kind,
        "record_id": record.record_id,
        "merchant": record.merchant,
        "amount_aud": round(_to_aud(record.amount, record.currency), 2),
        "status": "需要复核",
        "reason": reason,
        "evidence_ref": record.evidence_ref,
    }


def _hour(iso_text: str) -> int:
    return int(iso_text.split("T", 1)[1].split(":", 1)[0]) if "T" in iso_text else 12


def _is_weekend(iso_text: str) -> bool:
    return datetime.fromisoformat(iso_text).weekday() >= 5


def _to_aud(amount: float, currency: str) -> float:
    if currency not in STAGE3_FX_TO_AUD:
        raise ValueError(f"Missing FX fixture for {currency}.")
    return amount * STAGE3_FX_TO_AUD[currency]


def _money(value: object) -> str:
    return f"AUD {float(value):,.2f}"


def _card(key: str, label: str, value: str, detail: str) -> dict[str, str]:
    return {"key": key, "label": label, "value": value, "detail": detail}


def _decision(priority: str, target: str, evidence: str, action: str, status: str) -> dict[str, str]:
    return {"priority": priority, "object": target, "evidence": evidence, "action": action, "status": status}
