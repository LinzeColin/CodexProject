from __future__ import annotations

from pathlib import Path

from pfi_v02.stage_v022_database_governance import (
    V022_STAGE11_TASK_IDS,
    build_v022_stage11_contract,
    load_v022_parameter_catalog,
)
from pfi_v02.stage_v022_test_validation import (
    STAGE11_FINANCIAL_CASE_IDS,
    STAGE11_SURFACE_NAMES,
    STAGE11_VISUALIZATION_CHART_IDS,
    build_stage11_contract_payload,
    build_stage11_cross_surface_consistency,
    build_stage11_financial_logic_cases,
    build_stage11_visualization_validation,
)


ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_stage11_contract_matches_roadmap_scope() -> None:
    contract = build_v022_stage11_contract()

    assert contract["stage"] == "Stage 11"
    assert contract["stage_name_zh"] == "测试与验证"
    assert contract["task_ids"] == V022_STAGE11_TASK_IDS
    assert contract["phases"]["Phase 11.1"] == (
        "金融逻辑单元测试",
        "S11-P1-T1",
        "S11-P1-T2",
        "S11-P1-T3",
        "S11-P1-T4",
    )
    assert contract["phases"]["Phase 11.2"] == (
        "跨板块一致性测试",
        "S11-P2-T1",
        "S11-P2-T2",
        "S11-P2-T3",
    )
    assert contract["phases"]["Phase 11.3"] == (
        "可视化一致性测试",
        "S11-P3-T1",
        "S11-P3-T2",
        "S11-P3-T3",
    )
    assert "Stage 12 文档同步与最终交付不在本轮实现。" in contract["non_goals"]
    assert "Stage 13 后置触发型复核不在本轮实现。" in contract["non_goals"]


def test_financial_logic_cases_cover_stage11_stop_conditions() -> None:
    cases = build_stage11_financial_logic_cases()
    assert tuple(case["case_id"] for case in cases) == STAGE11_FINANCIAL_CASE_IDS

    by_id = {case["case_id"]: case for case in cases}
    deposit = by_id["cba_to_moomoo_investment_deposit"]
    assert deposit["gross_consumption_delta_cny"] > 0
    assert deposit["living_consumption_delta_cny"] == 0
    assert deposit["investment_cash_delta_cny"] > 0
    assert deposit["stop_condition_triggered"] is False

    fund = by_id["alipay_fund_purchase"]
    assert fund["gross_consumption_delta_cny"] > 0
    assert fund["living_consumption_delta_cny"] == 0
    assert fund["investment_holding_delta_cny"] > 0
    assert fund["stop_condition_triggered"] is False

    refund = by_id["refund_offsets_original_consumption"]
    assert refund["original_living_consumption_cny"] > 0
    assert refund["refund_offset_cny"] == -refund["original_living_consumption_cny"]
    assert refund["net_living_consumption_cny"] == 0
    assert refund["investment_return_delta_cny"] == 0
    assert refund["refund_counted_as_income"] is False

    credit_card = by_id["credit_card_repayment_no_double_count"]
    assert credit_card["card_purchase_living_consumption_cny"] > 0
    assert credit_card["repayment_living_consumption_delta_cny"] == 0
    assert credit_card["net_living_consumption_cny"] == credit_card["card_purchase_living_consumption_cny"]
    assert credit_card["double_counted"] is False


def test_cross_surface_consistency_is_exact_and_traceable() -> None:
    consistency = build_stage11_cross_surface_consistency()

    consumption = consistency["consumption_total_outflow"]
    assert consumption["homepage_cny"] == consumption["consumption_page_cny"] == consumption["monthly_report_cny"]
    assert consumption["surfaces"] == STAGE11_SURFACE_NAMES["consumption"]

    investment = consistency["investment_assets"]
    assert investment["homepage_cny"] == investment["investment_page_cny"] == investment["investment_report_cny"]
    assert investment["surfaces"] == STAGE11_SURFACE_NAMES["investment"]

    cashflow = consistency["cashflow_traceability"]
    assert cashflow["can_trace_to_ledger_events"] is True
    assert cashflow["can_trace_to_plan_events"] is True
    assert cashflow["ledger_event_ids"]
    assert cashflow["plan_event_ids"]
    assert cashflow["unexplained_amount_cny"] == 0


def test_visualization_validation_has_sources_freshness_and_performance_status() -> None:
    validation = build_stage11_visualization_validation(record_count=12_000)

    assert tuple(chart["chart_id"] for chart in validation["charts"]) == STAGE11_VISUALIZATION_CHART_IDS
    for chart in validation["charts"]:
        assert chart["metric_id"]
        assert chart["formula_id"]
        assert chart["parameter_hash"]
        assert chart["data_hash"]
        assert chart["cache_status"] in {"updated", "needs_update", "cache_hit"}
        assert chart["compute_time_ms"] >= 0
        assert chart["compute_time_visible"] is True

    freshness = validation["freshness_after_data_change"]
    assert freshness["changed_dependency"] == "ledger_events_hash"
    assert freshness["affected_chart_ids"]
    assert all(status in {"needs_update", "updated"} for status in freshness["affected_statuses"].values())
    assert validation["performance"]["record_count"] == 12_000
    assert validation["performance"]["not_obviously_stuck"] is True
    assert validation["performance"]["compute_time_ms"] < validation["performance"]["max_allowed_ms"]


def test_stage11_parameter_catalog_and_docs_are_updated() -> None:
    catalog = load_v022_parameter_catalog()
    assert catalog["schema"] == "PFIParametersV022Stage11"
    assert catalog["current_stage"] == "Stage 11 - 测试与验证"
    assert catalog["stage11_task_ids"] == list(V022_STAGE11_TASK_IDS)
    validation_params = catalog["parameters"]["test_validation"]
    assert validation_params["financial_logic_case_ids"]["value"] == list(STAGE11_FINANCIAL_CASE_IDS)
    assert validation_params["cross_surface_required_equalities"]["value"] == [
        "首页消费总流出 = 消费页消费总流出 = 月报消费总流出",
        "首页投资资产 = 投资页投资资产 = 投资报告投资资产",
    ]
    assert validation_params["visualization_required_trace_fields"]["value"] == [
        "metric_id",
        "formula_id",
        "parameter_hash",
        "data_hash",
    ]

    docs = (
        "docs/pfi_v022/STAGE11_TEST_VALIDATION.md",
        "docs/pfi_v022/ROADMAP_LOCK.md",
        "README.md",
        "模型参数文件.md",
        "功能清单.md",
        "开发记录.md",
        "HANDOFF.md",
    )
    required_terms = (
        "Stage 11 - 测试与验证",
        "S11-P1-T1",
        "S11-P2-T3",
        "S11-P3-T3",
        "投资入金计入消费总流出",
        "基金申购计入消费总流出",
        "退款抵消",
        "信用卡还款不重复计入生活消费",
        "首页消费总流出 = 消费页消费总流出 = 月报消费总流出",
        "首页投资资产 = 投资页投资资产 = 投资报告投资资产",
        "metric_id",
        "formula_id",
        "parameter_hash",
        "data_hash",
        "compute time",
        "cache status",
    )
    for path in docs:
        text = read_text(path)
        for term in required_terms:
            assert term in text, f"{path} missing {term}"


def test_stage11_payload_exposes_all_validation_gates() -> None:
    payload = build_stage11_contract_payload(load_v022_parameter_catalog())

    assert payload["schema"] == "PFIV022Stage11TestValidationPayloadV1"
    assert len(payload["financial_logic_cases"]) == 4
    assert payload["cross_surface_consistency"]["cashflow_traceability"]["unexplained_amount_cny"] == 0
    assert payload["visualization_validation"]["performance"]["not_obviously_stuck"] is True
    assert payload["stage11_ready_for_stage12"] is True
