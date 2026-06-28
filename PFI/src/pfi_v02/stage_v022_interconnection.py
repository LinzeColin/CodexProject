from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import date
from decimal import Decimal
from typing import Iterable


STAGE4_REQUIRED_EVENT_TYPES = (
    "ordinary_consumption",
    "investment_deposit",
    "fund_subscription",
    "bullion_purchase",
    "investment_buy",
    "investment_sell",
    "refund",
    "credit_card_repayment",
    "internal_transfer",
    "income",
    "fee",
    "fx_conversion",
)

STAGE4_MATRIX_FIELDS = (
    "event_type",
    "label_zh",
    "affects_total_consumption_outflow",
    "affects_living_consumption",
    "affects_investment",
    "affects_net_worth",
    "affects_cashflow",
    "homepage_display",
    "consumption_display",
    "investment_display",
    "cashflow_display",
    "report_display",
    "offset_rule_zh",
)


@dataclass(frozen=True)
class EventTypePolicy:
    event_type: str
    label_zh: str
    aliases: tuple[str, ...]
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
    offset_rule_zh: str
    investment_bucket: str | None = None
    cashflow_direction: str = "none"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class InterconnectionRecord:
    source_record_id: str
    source_id: str
    account_id: str
    event_date: date
    event_type: str
    amount_cny: Decimal
    direction: str
    economic_event_id: str
    interconnection_group_id: str
    offset_economic_event_id: str | None = None

    def normalized_event_type(self) -> str:
        return normalize_event_type(self.event_type)


POLICY_BY_EVENT_TYPE: dict[str, EventTypePolicy] = {
    "consumption": EventTypePolicy(
        event_type="consumption",
        label_zh="普通消费",
        aliases=("ordinary_consumption",),
        affects_total_consumption_outflow=True,
        affects_living_consumption=True,
        affects_investment=False,
        affects_net_worth=True,
        affects_cashflow=True,
        homepage_display="首页显示为本期支出和现金流压力来源。",
        consumption_display="计入消费总流出和生活消费。",
        investment_display="不计入投资资产。",
        cashflow_display="计入生活现金流出。",
        report_display="报告中作为普通生活消费展示。",
        offset_rule_zh="如后续发生退款，由 refund 事件抵消原消费。",
        cashflow_direction="outflow",
    ),
    "ordinary_consumption": EventTypePolicy(
        event_type="ordinary_consumption",
        label_zh="普通消费",
        aliases=("consumption",),
        affects_total_consumption_outflow=True,
        affects_living_consumption=True,
        affects_investment=False,
        affects_net_worth=True,
        affects_cashflow=True,
        homepage_display="首页显示为本期支出和现金流压力来源。",
        consumption_display="计入消费总流出和生活消费。",
        investment_display="不计入投资资产。",
        cashflow_display="计入生活现金流出。",
        report_display="报告中作为普通生活消费展示。",
        offset_rule_zh="如后续发生退款，由 refund 事件抵消原消费。",
        cashflow_direction="outflow",
    ),
    "investment_deposit": EventTypePolicy(
        event_type="investment_deposit",
        label_zh="投资入金",
        aliases=("transfer_to_investment",),
        affects_total_consumption_outflow=True,
        affects_living_consumption=False,
        affects_investment=True,
        affects_net_worth=False,
        affects_cashflow=True,
        homepage_display="首页可显示为投资现金增加和生活现金减少。",
        consumption_display="计入消费总流出，不计入生活消费。",
        investment_display="计入投资现金。",
        cashflow_display="计入生活现金流出和投资现金流入。",
        report_display="报告中作为投资性资金流出展示。",
        offset_rule_zh="银行侧和券商侧同属一个 interconnection_group，只按一个 economic_event_id 计算一次。",
        investment_bucket="investment_cash",
        cashflow_direction="outflow",
    ),
    "fund_subscription": EventTypePolicy(
        event_type="fund_subscription",
        label_zh="基金申购",
        aliases=(),
        affects_total_consumption_outflow=True,
        affects_living_consumption=False,
        affects_investment=True,
        affects_net_worth=False,
        affects_cashflow=True,
        homepage_display="首页可显示为基金资产增加。",
        consumption_display="计入消费总流出，不计入生活消费。",
        investment_display="计入基金资产。",
        cashflow_display="计入主钱包或基金平台现金流出。",
        report_display="报告中作为投资性资金流出展示。",
        offset_rule_zh="同一申购的支付记录和份额记录只按一个 economic_event_id 计算一次。",
        investment_bucket="fund_asset",
        cashflow_direction="outflow",
    ),
    "bullion_purchase": EventTypePolicy(
        event_type="bullion_purchase",
        label_zh="黄金申购",
        aliases=("gold_subscription",),
        affects_total_consumption_outflow=True,
        affects_living_consumption=False,
        affects_investment=True,
        affects_net_worth=False,
        affects_cashflow=True,
        homepage_display="首页可显示为贵金属资产增加。",
        consumption_display="计入消费总流出，不计入生活消费。",
        investment_display="计入贵金属资产。",
        cashflow_display="计入现金流出。",
        report_display="报告中作为贵金属投资流出展示。",
        offset_rule_zh="支付记录和贵金属持仓记录只按一个 economic_event_id 计算一次。",
        investment_bucket="bullion_asset",
        cashflow_direction="outflow",
    ),
    "investment_buy": EventTypePolicy(
        event_type="investment_buy",
        label_zh="投资买入",
        aliases=(),
        affects_total_consumption_outflow=True,
        affects_living_consumption=False,
        affects_investment=True,
        affects_net_worth=False,
        affects_cashflow=True,
        homepage_display="首页可显示为投资持仓增加。",
        consumption_display="计入消费总流出，不计入生活消费。",
        investment_display="计入投资持仓。",
        cashflow_display="计入投资账户现金流出。",
        report_display="报告中作为投资买入展示。",
        offset_rule_zh="现金减少和持仓增加同属一个 economic_event_id，不能重复计入总流出。",
        investment_bucket="investment_holding",
        cashflow_direction="outflow",
    ),
    "investment_sell": EventTypePolicy(
        event_type="investment_sell",
        label_zh="投资卖出",
        aliases=(),
        affects_total_consumption_outflow=False,
        affects_living_consumption=False,
        affects_investment=True,
        affects_net_worth=False,
        affects_cashflow=True,
        homepage_display="首页可显示为投资现金回流。",
        consumption_display="不计入消费。",
        investment_display="计入投资卖出和投资现金回流。",
        cashflow_display="计入投资账户现金流入。",
        report_display="报告中作为投资卖出展示。",
        offset_rule_zh="卖出资金回流不抵消生活消费，只影响投资现金和持仓。",
        investment_bucket="investment_proceeds",
        cashflow_direction="inflow",
    ),
    "refund": EventTypePolicy(
        event_type="refund",
        label_zh="退款",
        aliases=(),
        affects_total_consumption_outflow=True,
        affects_living_consumption=True,
        affects_investment=False,
        affects_net_worth=True,
        affects_cashflow=True,
        homepage_display="首页可显示为支出抵消或现金回流。",
        consumption_display="抵消原消费或对应总流出。",
        investment_display="通常不计入投资。",
        cashflow_display="计入现金流入。",
        report_display="报告中展示为退款抵消项。",
        offset_rule_zh="退款抵消原消费；有 offset_economic_event_id 时绑定原事件。",
        cashflow_direction="inflow",
    ),
    "credit_card_repayment": EventTypePolicy(
        event_type="credit_card_repayment",
        label_zh="信用卡还款",
        aliases=(),
        affects_total_consumption_outflow=False,
        affects_living_consumption=False,
        affects_investment=False,
        affects_net_worth=False,
        affects_cashflow=True,
        homepage_display="首页可显示为现金流还款压力。",
        consumption_display="不重复计入生活消费，可在还款分析单列。",
        investment_display="不计入投资。",
        cashflow_display="计入生活现金流出。",
        report_display="报告中单列还款，不重复增加消费。",
        offset_rule_zh="信用卡还款不重复计入生活消费；原消费已在账单发生时计算。",
        cashflow_direction="outflow",
    ),
    "internal_transfer": EventTypePolicy(
        event_type="internal_transfer",
        label_zh="内部转账",
        aliases=(),
        affects_total_consumption_outflow=False,
        affects_living_consumption=False,
        affects_investment=False,
        affects_net_worth=False,
        affects_cashflow=True,
        homepage_display="首页可显示为账户间调拨。",
        consumption_display="不计入消费。",
        investment_display="不计入投资资产变化。",
        cashflow_display="只计内部现金移动。",
        report_display="报告中作为内部转账展示。",
        offset_rule_zh="转出和转入记录必须归入同一 interconnection_group，核心金额不重复计算。",
        cashflow_direction="internal",
    ),
    "income": EventTypePolicy(
        event_type="income",
        label_zh="收入",
        aliases=(),
        affects_total_consumption_outflow=False,
        affects_living_consumption=False,
        affects_investment=False,
        affects_net_worth=True,
        affects_cashflow=True,
        homepage_display="首页显示为收入和现金流改善。",
        consumption_display="不计入消费。",
        investment_display="不计入投资。",
        cashflow_display="计入现金流入。",
        report_display="报告中作为收入展示。",
        offset_rule_zh="收入不抵消消费，单独进入现金流入。",
        cashflow_direction="inflow",
    ),
    "fee": EventTypePolicy(
        event_type="fee",
        label_zh="费用",
        aliases=(),
        affects_total_consumption_outflow=True,
        affects_living_consumption=False,
        affects_investment=False,
        affects_net_worth=True,
        affects_cashflow=True,
        homepage_display="首页可显示为费用拖累。",
        consumption_display="计入消费总流出，不计入生活消费。",
        investment_display="可作为投资费用或金融费用分析。",
        cashflow_display="计入现金流出。",
        report_display="报告中作为费用展示。",
        offset_rule_zh="费用不重复抵消，若退费则由 refund 事件抵消。",
        cashflow_direction="outflow",
    ),
    "fx_conversion": EventTypePolicy(
        event_type="fx_conversion",
        label_zh="汇率兑换",
        aliases=(),
        affects_total_consumption_outflow=False,
        affects_living_consumption=False,
        affects_investment=False,
        affects_net_worth=False,
        affects_cashflow=True,
        homepage_display="首页可显示为币种转换。",
        consumption_display="不计入消费。",
        investment_display="不计入投资资产变化。",
        cashflow_display="作为币种间现金移动展示。",
        report_display="报告中展示汇率快照和转换证据。",
        offset_rule_zh="兑换的买入卖出两侧必须归入同一 interconnection_group，CNY 主口径不重复计算。",
        cashflow_direction="internal",
    ),
}


def normalize_event_type(event_type: str) -> str:
    clean = str(event_type).strip()
    if clean not in POLICY_BY_EVENT_TYPE:
        for policy in POLICY_BY_EVENT_TYPE.values():
            if clean in policy.aliases:
                return policy.event_type
        raise ValueError(f"unsupported Stage 4 event_type: {event_type}")
    return clean


def event_policy(event_type: str) -> EventTypePolicy:
    return POLICY_BY_EVENT_TYPE[normalize_event_type(event_type)]


def build_interconnection_matrix() -> tuple[dict[str, object], ...]:
    return tuple(POLICY_BY_EVENT_TYPE[event_type].to_dict() for event_type in ("consumption",) + STAGE4_REQUIRED_EVENT_TYPES)


def build_metric_dependency_graph() -> dict[str, object]:
    return {
        "schema": "PFIV022Stage4MetricDependencyGraphV1",
        "flow": (
            "source_record",
            "normalized_transaction",
            "interconnection_group_id",
            "economic_event_id",
            "ledger_event",
            "core_metrics",
            "homepage_consumption_investment_cashflow_report",
        ),
        "core_metrics": {
            "total_consumption_outflow_cny": (
                "consumption",
                "investment_deposit",
                "fund_subscription",
                "bullion_purchase",
                "investment_buy",
                "fee",
                "refund_offset",
            ),
            "living_consumption_cny": ("consumption", "refund_offset"),
            "investment_cash_cny": ("investment_deposit", "investment_sell"),
            "fund_asset_flow_cny": ("fund_subscription",),
            "investment_holding_flow_cny": ("investment_buy", "investment_sell"),
            "cashflow": ("income", "refund", "credit_card_repayment", "internal_transfer", "fx_conversion"),
        },
        "no_double_count_rule": "同一 economic_event_id 只进入核心金额一次；同一 interconnection_group 可多处展示但不得在同一指标口径重复计算。",
    }


def _decimal(value: Decimal | int | str) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _signed_amount(record: InterconnectionRecord, policy: EventTypePolicy) -> Decimal:
    amount = abs(_decimal(record.amount_cny))
    if policy.event_type == "refund":
        return -amount
    if policy.cashflow_direction == "inflow" and record.direction == "inflow":
        return amount
    return amount


def _dedupe_records(records: Iterable[InterconnectionRecord]) -> tuple[InterconnectionRecord, ...]:
    by_event: dict[str, InterconnectionRecord] = {}
    for record in records:
        policy = event_policy(record.event_type)
        normalized = replace(record, event_type=policy.event_type, amount_cny=abs(_decimal(record.amount_cny)))
        current = by_event.get(normalized.economic_event_id)
        if current is None or abs(normalized.amount_cny) > abs(current.amount_cny):
            by_event[normalized.economic_event_id] = normalized
    return tuple(by_event.values())


def aggregate_core_metrics(records: Iterable[InterconnectionRecord]) -> dict[str, Decimal | int]:
    source_records = tuple(records)
    deduped = _dedupe_records(source_records)
    metrics: dict[str, Decimal | int] = {
        "source_record_count": len(source_records),
        "economic_event_count": len({record.economic_event_id for record in source_records}),
        "interconnection_group_count": len({record.interconnection_group_id for record in source_records}),
        "deduped_core_event_count": len(deduped),
        "total_consumption_outflow_cny": Decimal("0.00"),
        "living_consumption_cny": Decimal("0.00"),
        "investment_cash_cny": Decimal("0.00"),
        "fund_asset_flow_cny": Decimal("0.00"),
        "bullion_asset_flow_cny": Decimal("0.00"),
        "investment_holding_flow_cny": Decimal("0.00"),
        "investment_proceeds_cny": Decimal("0.00"),
        "refund_offset_cny": Decimal("0.00"),
        "credit_card_repayment_cny": Decimal("0.00"),
        "cashflow_outflow_cny": Decimal("0.00"),
        "cashflow_inflow_cny": Decimal("0.00"),
        "net_worth_delta_cny": Decimal("0.00"),
    }
    for record in deduped:
        policy = event_policy(record.event_type)
        amount = abs(_decimal(record.amount_cny))
        signed = _signed_amount(record, policy)

        if policy.affects_total_consumption_outflow:
            metrics["total_consumption_outflow_cny"] += signed
        if policy.affects_living_consumption:
            metrics["living_consumption_cny"] += signed
        if policy.event_type == "refund":
            metrics["refund_offset_cny"] += amount
        if policy.event_type == "credit_card_repayment":
            metrics["credit_card_repayment_cny"] += amount
        if policy.investment_bucket == "investment_cash":
            metrics["investment_cash_cny"] += amount
        elif policy.investment_bucket == "fund_asset":
            metrics["fund_asset_flow_cny"] += amount
        elif policy.investment_bucket == "bullion_asset":
            metrics["bullion_asset_flow_cny"] += amount
        elif policy.investment_bucket == "investment_holding":
            metrics["investment_holding_flow_cny"] += amount
        elif policy.investment_bucket == "investment_proceeds":
            metrics["investment_proceeds_cny"] += amount
            metrics["investment_cash_cny"] += amount
        if policy.affects_cashflow:
            if policy.cashflow_direction == "inflow" or signed < 0:
                metrics["cashflow_inflow_cny"] += abs(signed)
            elif policy.cashflow_direction == "outflow":
                metrics["cashflow_outflow_cny"] += amount
        if policy.affects_net_worth:
            if policy.event_type in {"consumption", "ordinary_consumption", "fee"}:
                metrics["net_worth_delta_cny"] -= amount
            elif policy.event_type in {"refund", "income"}:
                metrics["net_worth_delta_cny"] += amount
    return metrics


def build_stage4_interconnection_contract() -> dict[str, object]:
    return {
        "schema": "PFIV022Stage4InterconnectionContractV1",
        "required_event_types": STAGE4_REQUIRED_EVENT_TYPES,
        "matrix_fields": STAGE4_MATRIX_FIELDS,
        "interconnection_matrix": build_interconnection_matrix(),
        "metric_dependency_graph": build_metric_dependency_graph(),
        "single_count_rule_zh": "可多处展示，但只能按口径计算一次。",
    }
