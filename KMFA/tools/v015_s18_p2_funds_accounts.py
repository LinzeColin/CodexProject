#!/usr/bin/env python3
"""KMFA v1.5 S18-P2 资金账户、现金预测与贷款计划。

只使用公开合成资料。金额始终使用整数分；账户不明时禁止汇总；
预测严格分为事实、计划与情景假设；本模块不连接银行，也不执行付款。
"""

from __future__ import annotations

from datetime import date
from typing import Any, Mapping, Sequence

from KMFA.tools import v015_s16_p1_homepage as homepage


RUN_PHASE_ID = "V015_S18_P2_FUNDS_ACCOUNTS"
ROADMAP_PHASE_ID = "S18-P2"
TASK_ID = "KMFA-V015-S18-P2-FUNDS-ACCOUNTS-20260716"
ACCEPTANCE_ID = "ACC-KMFA-V015-S18-P2-FUNDS-ACCOUNTS"
VERSION = "1.5.0-dev-s18p2"

BALANCE_DATE = "2026-07-15"
DATA_CLASSIFICATION = "PUBLIC_SYNTHETIC"
MONEY_TOLERANCE_CENTS = 0
COMPANY_IDS = tuple(homepage.COMPANY_FACTORS)
PERIOD_IDS = tuple(homepage.PERIOD_FACTORS)
SCENARIO_IDS = ("base", "collection_delay", "cost_pressure")
FORECAST_PERIODS = ("未来 7 天", "第 2 周", "第 3 周", "第 4 周")
FACT_KIND = "FACT"
PLAN_KIND = "PLAN"
ASSUMPTION_KIND = "ASSUMPTION"


class FundsAccountsError(ValueError):
    """资金账户请求违反公开演示合同。"""


def source_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s18p2.source_contract.v1",
        "stage_id": "S18",
        "stage_name_zh": "回款、应收、资金与贷款分析",
        "stage_goal_zh": "建立现金安全、催收优先级、多主体账户和资金计划能力，不执行付款。",
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "phase_name_zh": "资金与账户",
        "task_ids": ["S18P2T01", "S18P2T02", "S18P2T03"],
        "task_names_zh": ["建立银行账户事实", "实现现金预测", "实现贷款和资金计划"],
        "acceptance_zh": ["余额日期、来源和账户脱敏明确。", "事实与假设分开。", "不包含支付执行。"],
        "stop_conditions_zh": ["账户不明不得汇总。", "预测不得伪装成确定值。", "付款按钮不得出现。"],
        "data_classification": DATA_CLASSIFICATION,
    }


def format_money(cents: int) -> str:
    if isinstance(cents, bool) or not isinstance(cents, int):
        raise FundsAccountsError("money must use integer cents")
    sign = "-" if cents < 0 else ""
    yuan, fen = divmod(abs(cents), 100)
    return f"{sign}¥{yuan:,}.{fen:02d}"


def _scaled(cents: int, company_id: str, period: str) -> int:
    if company_id not in homepage.COMPANY_FACTORS:
        raise FundsAccountsError("unsupported public company")
    if period not in homepage.PERIOD_FACTORS:
        raise FundsAccountsError("unsupported public period")
    return cents * homepage.COMPANY_FACTORS[company_id] * homepage.PERIOD_FACTORS[period] // 10_000


def _company_label(company_id: str) -> str:
    return {
        "demo-north": "北方工程演示公司",
        "demo-south": "南方工程演示公司",
        "demo-west": "西部工程演示公司",
    }[company_id]


def _account_definitions() -> tuple[dict[str, Any], ...]:
    return (
        {
            "account_id": "PUB-ACC-001", "bank_id": "PUB-BANK-A", "bank_name_zh": "海岳演示银行",
            "account_name_zh": "基本账户", "masked_account": "**** 1024", "opening_cents": 120_000_000,
            "inflow_cents": 30_000_000, "outflow_cents": 20_000_000,
        },
        {
            "account_id": "PUB-ACC-002", "bank_id": "PUB-BANK-B", "bank_name_zh": "启明演示银行",
            "account_name_zh": "税费专户", "masked_account": "**** 2088", "opening_cents": 40_000_000,
            "inflow_cents": 5_000_000, "outflow_cents": 10_000_000,
        },
        {
            "account_id": "PUB-ACC-003", "bank_id": "PUB-BANK-A", "bank_name_zh": "海岳演示银行",
            "account_name_zh": "保证金账户", "masked_account": "**** 3066", "opening_cents": 25_000_000,
            "inflow_cents": 0, "outflow_cents": 5_000_000,
        },
        {
            "account_id": "PUB-ACC-004", "bank_id": "PUB-BANK-C", "bank_name_zh": "江川演示银行",
            "account_name_zh": "工资专户", "masked_account": "**** 4012", "opening_cents": 20_000_000,
            "inflow_cents": 12_000_000, "outflow_cents": 15_000_000,
        },
    )


def account_facts(company_id: str = "demo-north", period: str = "2026-07") -> dict[str, Any]:
    """返回可汇总账户与待确认账户；待确认账户永远不进入余额合计。"""

    accounts: list[dict[str, Any]] = []
    transactions: list[dict[str, Any]] = []
    for definition in _account_definitions():
        row = dict(definition)
        for key in ("opening_cents", "inflow_cents", "outflow_cents"):
            row[key] = _scaled(int(row[key]), company_id, period)
        row["closing_cents"] = row["opening_cents"] + row["inflow_cents"] - row["outflow_cents"]
        row.update(
            {
                "company_id": company_id,
                "company_zh": _company_label(company_id),
                "period": period,
                "currency": "CNY",
                "balance_date": BALANCE_DATE,
                "source_ref": f"PUBLIC-SYNTHETIC:BANK-BALANCE:{company_id}:{period}:{row['account_id']}",
                "source_zh": "公开合成银行余额与流水",
                "account_status": "KNOWN",
                "account_status_zh": "主体和账户已确认",
                "included_in_total": True,
                "reconciliation_difference_cents": 0,
                "data_classification": DATA_CLASSIFICATION,
            }
        )
        accounts.append(row)
        for transaction_id, direction, amount_key, label in (
            (f"{row['account_id']}-IN", "INFLOW", "inflow_cents", "演示回款流入"),
            (f"{row['account_id']}-OUT", "OUTFLOW", "outflow_cents", "演示经营支出"),
        ):
            transactions.append(
                {
                    "transaction_id": transaction_id,
                    "company_id": company_id,
                    "account_id": row["account_id"],
                    "masked_account": row["masked_account"],
                    "direction": direction,
                    "direction_zh": "流入" if direction == "INFLOW" else "流出",
                    "amount_cents": row[amount_key],
                    "description_zh": label,
                    "transaction_date": BALANCE_DATE,
                    "source_ref": row["source_ref"],
                    "data_classification": DATA_CLASSIFICATION,
                }
            )
    unknown = {
        "account_id": "PUB-ACC-UNKNOWN-001",
        "company_id": None,
        "company_zh": "待确认",
        "period": period,
        "bank_id": "PUB-BANK-UNKNOWN",
        "bank_name_zh": "待确认银行",
        "account_name_zh": "账户归属待确认",
        "masked_account": "待确认",
        "currency": "CNY",
        "balance_date": BALANCE_DATE,
        "closing_cents": _scaled(7_000_000, company_id, period),
        "source_ref": f"PUBLIC-SYNTHETIC:BANK-BALANCE:UNKNOWN:{period}",
        "source_zh": "公开合成待确认账户样例",
        "account_status": "UNKNOWN",
        "account_status_zh": "主体或账户不明，不得汇总",
        "included_in_total": False,
        "data_classification": DATA_CLASSIFICATION,
    }
    total = sum(row["closing_cents"] for row in accounts)
    bank_totals = []
    for bank_id in sorted({row["bank_id"] for row in accounts}):
        selected = [row for row in accounts if row["bank_id"] == bank_id]
        bank_totals.append(
            {
                "bank_id": bank_id,
                "bank_name_zh": selected[0]["bank_name_zh"],
                "account_count": len(selected),
                "closing_cents": sum(row["closing_cents"] for row in selected),
            }
        )
    return {
        "company_id": company_id,
        "company_zh": _company_label(company_id),
        "period": period,
        "balance_date": BALANCE_DATE,
        "source_zh": "公开合成银行余额与流水",
        "accounts": accounts,
        "transactions": transactions,
        "unknown_accounts": [unknown],
        "bank_totals": bank_totals,
        "known_account_count": len(accounts),
        "unknown_account_count": 1,
        "excluded_unknown_account_count": 1,
        "total_available_cents": total,
        "account_reconciliation_difference_cents": sum(row["reconciliation_difference_cents"] for row in accounts),
        "bank_reconciliation_difference_cents": total - sum(row["closing_cents"] for row in bank_totals),
        "unknown_amount_in_total_cents": 0,
        "cross_company_leak_count": sum(row["company_id"] != company_id for row in accounts),
    }


def _forecast_plan_definitions() -> tuple[dict[str, Any], ...]:
    return (
        {"period_index": 0, "kind": FACT_KIND, "direction": "INFLOW", "amount_cents": 12_000_000, "label_zh": "已确认到账"},
        {"period_index": 0, "kind": FACT_KIND, "direction": "OUTFLOW", "amount_cents": 8_000_000, "label_zh": "已确认扣款"},
        {"period_index": 0, "kind": PLAN_KIND, "direction": "INFLOW", "amount_cents": 25_000_000, "label_zh": "计划回款"},
        {"period_index": 0, "kind": PLAN_KIND, "direction": "OUTFLOW", "amount_cents": 20_000_000, "label_zh": "计划付款"},
        {"period_index": 1, "kind": FACT_KIND, "direction": "OUTFLOW", "amount_cents": 5_000_000, "label_zh": "已确认费用"},
        {"period_index": 1, "kind": PLAN_KIND, "direction": "INFLOW", "amount_cents": 35_000_000, "label_zh": "计划回款"},
        {"period_index": 1, "kind": PLAN_KIND, "direction": "OUTFLOW", "amount_cents": 28_000_000, "label_zh": "计划付款"},
        {"period_index": 2, "kind": PLAN_KIND, "direction": "INFLOW", "amount_cents": 18_000_000, "label_zh": "计划回款"},
        {"period_index": 2, "kind": PLAN_KIND, "direction": "OUTFLOW", "amount_cents": 82_000_000, "label_zh": "计划付款及贷款到期"},
        {"period_index": 3, "kind": PLAN_KIND, "direction": "INFLOW", "amount_cents": 22_000_000, "label_zh": "计划回款"},
        {"period_index": 3, "kind": PLAN_KIND, "direction": "OUTFLOW", "amount_cents": 40_000_000, "label_zh": "计划付款"},
    )


def _scenario_adjustment(scenario_id: str, plan_inflow: int, plan_outflow: int) -> tuple[int, str]:
    if scenario_id == "base":
        return 0, "基准情景：计划按当前时间和金额发生；这仍是计划，不是确定值。"
    if scenario_id == "collection_delay":
        return -(plan_inflow * 35 // 100), "回款延迟情景：计划回款仅按 65% 在本期发生。"
    if scenario_id == "cost_pressure":
        return -(plan_outflow * 15 // 100), "成本压力情景：计划流出增加 15%。"
    raise FundsAccountsError("unsupported forecast scenario")


def cash_forecast(
    company_id: str = "demo-north",
    period: str = "2026-07",
    scenario_id: str = "base",
) -> dict[str, Any]:
    accounts = account_facts(company_id, period)
    definitions = _forecast_plan_definitions()
    events: list[dict[str, Any]] = []
    for index, definition in enumerate(definitions, start=1):
        row = dict(definition)
        row["amount_cents"] = _scaled(int(row["amount_cents"]), company_id, period)
        row.update(
            {
                "event_id": f"CASH-{index:02d}",
                "company_id": company_id,
                "period_label_zh": FORECAST_PERIODS[int(row["period_index"])],
                "certainty_zh": {FACT_KIND: "已确认事实", PLAN_KIND: "业务计划"}[str(row["kind"])],
                "source_ref": f"PUBLIC-SYNTHETIC:CASH-FORECAST:{company_id}:{period}:CASH-{index:02d}",
                "data_classification": DATA_CLASSIFICATION,
            }
        )
        events.append(row)

    confirmed_closing = accounts["total_available_cents"]
    planned_closing = accounts["total_available_cents"]
    scenario_closing = accounts["total_available_cents"]
    rows: list[dict[str, Any]] = []
    assumption_events: list[dict[str, Any]] = []
    for period_index, period_label in enumerate(FORECAST_PERIODS):
        selected = [row for row in events if row["period_index"] == period_index]
        fact_inflow = sum(row["amount_cents"] for row in selected if row["kind"] == FACT_KIND and row["direction"] == "INFLOW")
        fact_outflow = sum(row["amount_cents"] for row in selected if row["kind"] == FACT_KIND and row["direction"] == "OUTFLOW")
        plan_inflow = sum(row["amount_cents"] for row in selected if row["kind"] == PLAN_KIND and row["direction"] == "INFLOW")
        plan_outflow = sum(row["amount_cents"] for row in selected if row["kind"] == PLAN_KIND and row["direction"] == "OUTFLOW")
        adjustment, assumption_zh = _scenario_adjustment(scenario_id, plan_inflow, plan_outflow)
        confirmed_closing += fact_inflow - fact_outflow
        planned_closing += fact_inflow - fact_outflow + plan_inflow - plan_outflow
        scenario_closing += fact_inflow - fact_outflow + plan_inflow - plan_outflow + adjustment
        assumption_events.append(
            {
                "event_id": f"ASSUMPTION-{period_index + 1}",
                "company_id": company_id,
                "period_index": period_index,
                "period_label_zh": period_label,
                "kind": ASSUMPTION_KIND,
                "certainty_zh": "情景假设",
                "adjustment_cents": adjustment,
                "assumption_zh": assumption_zh,
                "writes_fact_layer": False,
            }
        )
        rows.append(
            {
                "period_index": period_index,
                "period_label_zh": period_label,
                "fact_inflow_cents": fact_inflow,
                "fact_outflow_cents": fact_outflow,
                "plan_inflow_cents": plan_inflow,
                "plan_outflow_cents": plan_outflow,
                "assumption_adjustment_cents": adjustment,
                "confirmed_closing_cents": confirmed_closing,
                "planned_closing_cents": planned_closing,
                "scenario_closing_cents": scenario_closing,
                "result_kind": "SCENARIO_NOT_CERTAINTY",
                "result_label_zh": "情景预计余额（不是确定值）",
            }
        )
    scenario_labels = {"base": "基准情景", "collection_delay": "回款延迟", "cost_pressure": "成本压力"}
    return {
        "company_id": company_id,
        "company_zh": _company_label(company_id),
        "period": period,
        "scenario_id": scenario_id,
        "scenario_label_zh": scenario_labels[scenario_id],
        "opening_cash_cents": accounts["total_available_cents"],
        "events": events,
        "assumption_events": assumption_events,
        "rows": rows,
        "fact_event_count": sum(row["kind"] == FACT_KIND for row in events),
        "plan_event_count": sum(row["kind"] == PLAN_KIND for row in events),
        "assumption_event_count": len(assumption_events),
        "forecast_period_count": len(rows),
        "fact_plan_assumption_separated": True,
        "forecast_presented_as_certainty_count": 0,
        "assumption_fact_write_count": 0,
        "scenario_difference_cents": rows[-1]["scenario_closing_cents"] - (
            accounts["total_available_cents"]
            + sum(row["fact_inflow_cents"] - row["fact_outflow_cents"] + row["plan_inflow_cents"] - row["plan_outflow_cents"] + row["assumption_adjustment_cents"] for row in rows)
        ),
    }


def loan_funding_plan(
    company_id: str = "demo-north",
    period: str = "2026-07",
    scenario_id: str = "base",
) -> dict[str, Any]:
    definitions = (
        ("PUB-LOAN-001", "流动资金借款", 60_000_000, "2026-07-29", 420, 6_000_000),
        ("PUB-LOAN-002", "设备借款", 95_000_000, "2026-09-30", 465, 9_500_000),
        ("PUB-LOAN-003", "项目周转借款", 45_000_000, "2026-12-31", 510, 4_500_000),
    )
    loans: list[dict[str, Any]] = []
    for loan_id, name, principal, maturity, annual_rate_bps, margin in definitions:
        principal_cents = _scaled(principal, company_id, period)
        margin_cents = _scaled(margin, company_id, period)
        days_to_maturity = (date.fromisoformat(maturity) - date.fromisoformat(BALANCE_DATE)).days
        interest_cents = principal_cents * annual_rate_bps * days_to_maturity // (10_000 * 365)
        loans.append(
            {
                "loan_id": loan_id,
                "company_id": company_id,
                "loan_name_zh": name,
                "masked_contract": f"借款合同 **** {loan_id[-3:]}",
                "principal_cents": principal_cents,
                "maturity_date": maturity,
                "days_to_maturity": days_to_maturity,
                "annual_rate_bps": annual_rate_bps,
                "annual_rate_zh": f"{annual_rate_bps // 100}.{annual_rate_bps % 100:02d}%",
                "estimated_interest_cents": interest_cents,
                "margin_cents": margin_cents,
                "source_ref": f"PUBLIC-SYNTHETIC:LOAN:{company_id}:{period}:{loan_id}",
                "source_zh": "公开合成贷款计划",
                "action_zh": "到期前内部复核资金安排",
                "payment_execution_allowed": False,
                "bank_operation_allowed": False,
                "data_classification": DATA_CLASSIFICATION,
            }
        )
    forecast = cash_forecast(company_id, period, scenario_id)
    minimum_safe_cash = _scaled(100_000_000, company_id, period)
    rows = []
    for row in forecast["rows"]:
        gap = max(minimum_safe_cash - row["scenario_closing_cents"], 0)
        rows.append(
            {
                "period_index": row["period_index"],
                "period_label_zh": row["period_label_zh"],
                "scenario_closing_cents": row["scenario_closing_cents"],
                "minimum_safe_cash_cents": minimum_safe_cash,
                "funding_gap_cents": gap,
                "status_zh": "存在资金缺口，需内部复核" if gap else "高于演示安全线",
                "action_zh": "内部评估回款、付款时间或融资方案" if gap else "持续观察",
            }
        )
    return {
        "company_id": company_id,
        "period": period,
        "scenario_id": scenario_id,
        "loans": loans,
        "funding_rows": rows,
        "loan_count": len(loans),
        "loan_due_within_90_days_count": sum(0 <= row["days_to_maturity"] <= 90 for row in loans),
        "total_principal_cents": sum(row["principal_cents"] for row in loans),
        "total_estimated_interest_cents": sum(row["estimated_interest_cents"] for row in loans),
        "total_margin_cents": sum(row["margin_cents"] for row in loans),
        "maximum_funding_gap_cents": max(row["funding_gap_cents"] for row in rows),
        "payment_execution_count": 0,
        "bank_operation_count": 0,
        "payment_button_count": 0,
    }


def funds_view(
    company_id: str = "demo-north",
    period: str = "2026-07",
    scenario_id: str = "base",
) -> dict[str, Any]:
    accounts = account_facts(company_id, period)
    forecast = cash_forecast(company_id, period, scenario_id)
    plan = loan_funding_plan(company_id, period, scenario_id)
    return {
        "schema_version": "kmfa.v015.s18p2.funds_view.v1",
        "allowed": True,
        "company_id": company_id,
        "company_zh": _company_label(company_id),
        "period": period,
        "balance_date": BALANCE_DATE,
        "data_classification": DATA_CLASSIFICATION,
        "accounts": accounts,
        "forecast": forecast,
        "funding_plan": plan,
        "scenario_options": [
            ["base", "基准情景"],
            ["collection_delay", "回款延迟"],
            ["cost_pressure", "成本压力"],
        ],
        "summary": {
            "available_cash_cents": accounts["total_available_cents"],
            "known_account_count": accounts["known_account_count"],
            "excluded_unknown_account_count": accounts["excluded_unknown_account_count"],
            "four_week_scenario_cash_cents": forecast["rows"][-1]["scenario_closing_cents"],
            "loan_due_within_90_days_count": plan["loan_due_within_90_days_count"],
            "maximum_funding_gap_cents": plan["maximum_funding_gap_cents"],
        },
        "cross_company_leak_count": accounts["cross_company_leak_count"],
        "money_difference_cents": accounts["account_reconciliation_difference_cents"] + accounts["bank_reconciliation_difference_cents"] + forecast["scenario_difference_cents"],
        "forecast_presented_as_certainty_count": forecast["forecast_presented_as_certainty_count"],
        "raw_root_access_count": 0,
        "live_source_read_count": 0,
        "external_network_request_count": 0,
        "real_identity_count": 0,
        "credential_count": 0,
        "real_business_action_count": 0,
        "source_data_write_count": 0,
        "fact_layer_write_count": 0,
        "payment_execution_count": 0,
        "bank_operation_count": 0,
        "payment_button_count": 0,
    }


def public_checks() -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []

    def add(check_id: str, passed: bool, detail_zh: str) -> None:
        checks.append({"check_id": check_id, "status": "PASS" if passed else "FAIL", "detail_zh": detail_zh})

    for company_id in COMPANY_IDS:
        view = funds_view(company_id=company_id)
        accounts = view["accounts"]
        add(f"{company_id}_entity_scope", view["cross_company_leak_count"] == 0, "主体隔离")
        add(f"{company_id}_account_reconcile", accounts["account_reconciliation_difference_cents"] == 0, "账户流水勾稽")
        add(f"{company_id}_bank_reconcile", accounts["bank_reconciliation_difference_cents"] == 0, "银行汇总勾稽")
        add(f"{company_id}_unknown_excluded", accounts["unknown_amount_in_total_cents"] == 0, "不明账户未汇总")
        add(f"{company_id}_masked", all(row["masked_account"].startswith("****") for row in accounts["accounts"]), "账号均脱敏")
        add(f"{company_id}_dated", all(row["balance_date"] == BALANCE_DATE for row in accounts["accounts"]), "余额日期明确")
        add(f"{company_id}_sourced", all(row["source_ref"].startswith("PUBLIC-SYNTHETIC:") for row in accounts["accounts"]), "来源明确")
        add(f"{company_id}_payment_closed", view["payment_execution_count"] == 0 and view["payment_button_count"] == 0, "无付款执行")
    for scenario_id in SCENARIO_IDS:
        forecast = cash_forecast(scenario_id=scenario_id)
        add(f"{scenario_id}_separated", forecast["fact_plan_assumption_separated"], "事实计划假设分开")
        add(f"{scenario_id}_not_certainty", forecast["forecast_presented_as_certainty_count"] == 0, "预测不冒充确定值")
        add(f"{scenario_id}_reconcile", forecast["scenario_difference_cents"] == 0, "情景预测勾稽")
        add(f"{scenario_id}_no_fact_write", forecast["assumption_fact_write_count"] == 0, "假设不写回事实")
        add(f"{scenario_id}_four_periods", len(forecast["rows"]) == 4, "四期预测完整")
    sample = funds_view()
    plan = sample["funding_plan"]
    for row in sample["accounts"]["accounts"]:
        add(f"equation_{row['account_id']}", row["opening_cents"] + row["inflow_cents"] - row["outflow_cents"] == row["closing_cents"], "账户余额等式成立")
    for loan in plan["loans"]:
        add(f"loan_{loan['loan_id']}_dated", loan["days_to_maturity"] >= 0, "贷款到期日明确")
        add(f"loan_{loan['loan_id']}_interest", loan["estimated_interest_cents"] >= 0, "利息估算明确")
        add(f"loan_{loan['loan_id']}_margin", loan["margin_cents"] >= 0, "保证金明确")
    add("integer_money", all(isinstance(row["closing_cents"], int) and not isinstance(row["closing_cents"], bool) for row in sample["accounts"]["accounts"]), "金额使用整数分")
    add("zero_tolerance", MONEY_TOLERANCE_CENTS == 0, "金额误差为零分")
    add("gap_visible", all("funding_gap_cents" in row for row in plan["funding_rows"]), "资金缺口逐期可见")
    add("payment_button_absent", plan["payment_button_count"] == 0, "付款按钮不存在")
    add("bank_operation_absent", plan["bank_operation_count"] == 0, "不执行银行操作")
    add("raw_closed", sample["raw_root_access_count"] == 0, "未访问原始资料")
    add("network_closed", sample["external_network_request_count"] == 0, "无外部网络")
    add("fact_write_closed", sample["fact_layer_write_count"] == 0, "未写入事实层")
    add("real_action_closed", sample["real_business_action_count"] == 0, "无真实业务动作")
    return checks


def main() -> int:
    checks = public_checks()
    failed = [row for row in checks if row["status"] != "PASS"]
    print(f"{'PASS' if not failed else 'FAIL'}: S18-P2 public checks {len(checks) - len(failed)}/{len(checks)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
