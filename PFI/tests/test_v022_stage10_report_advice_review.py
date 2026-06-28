from __future__ import annotations

from pathlib import Path

import pytest

from pfi_v02.stage_v022_database_governance import (
    V022_STAGE10_TASK_IDS,
    build_v022_stage10_contract,
    load_v022_parameter_catalog,
)
from pfi_v02.stage_v022_report_advice_review import (
    STAGE10_ACTION_REVIEW_TASK_TYPES,
    STAGE10_LIFECYCLE_STATUSES,
    STAGE10_REQUIRED_RECOMMENDATION_FIELDS,
    STAGE10_SCORING_WEIGHTS,
    Stage10RecommendationInput,
    build_action_review_lifecycle_model,
    build_stage10_contract_payload,
    build_stage10_report_suite,
    score_action_review_recommendation,
)


ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_stage10_contract_matches_roadmap_phase_task_scope() -> None:
    contract = build_v022_stage10_contract()

    assert contract["stage"] == "Stage 10"
    assert contract["stage_name_zh"] == "报告、建议与复盘"
    assert contract["task_ids"] == V022_STAGE10_TASK_IDS
    assert contract["phases"]["Phase 10.1"] == ("报告口径", "S10-P1-T1", "S10-P1-T2", "S10-P1-T3")
    assert contract["phases"]["Phase 10.2"] == ("行动建议与复盘", "S10-P2-T1", "S10-P2-T2", "S10-P2-T3")
    assert "Stage 11 测试与验证总门不在本轮实现。" in contract["non_goals"]
    assert "月报只显示一个消费口径。" in contract["stop_conditions"]
    assert "投资报告只有收益。" in contract["stop_conditions"]


def test_report_suite_contains_dual_consumption_investment_behavior_and_interconnection_quality() -> None:
    suite = build_stage10_report_suite(load_v022_parameter_catalog())

    monthly = suite["monthly_report"]
    dual_metrics = monthly["dual_consumption_metrics"]
    assert set(dual_metrics) == {"total_consumption_outflow", "living_consumption"}
    assert dual_metrics["total_consumption_outflow"]["label_zh"] == "消费总流出"
    assert dual_metrics["living_consumption"]["label_zh"] == "生活消费"
    assert "投资入金" in dual_metrics["total_consumption_outflow"]["included_flows"]
    assert "投资入金" in dual_metrics["living_consumption"]["excluded_flows"]

    investment = suite["investment_report"]
    for expected in ("收益", "成本", "费用", "汇率", "交易频率", "风格", "现金拖累"):
        assert expected in investment["required_sections"]
        assert expected in investment["metrics"].values()
    assert investment["must_not_be_return_only"] is True

    data_quality = suite["data_quality_report"]
    for expected in ("未匹配转账", "重复候选", "低置信", "标签变更", "参数变更", "hash diff"):
        assert expected in data_quality["required_sections"]
        assert expected in data_quality["interconnection_metrics"].values()


def test_action_review_definition_cannot_be_read_as_buy_sell_instruction() -> None:
    payload = build_stage10_contract_payload(load_v022_parameter_catalog())
    definition = payload["action_review_definition"]

    assert definition["label_zh"] == "行动建议与复盘"
    assert definition["automatic_investment_advice_allowed"] is False
    assert definition["automatic_buy_sell_instruction_allowed"] is False
    assert definition["real_trade_submission_allowed"] is False
    assert definition["allowed_task_types"] == STAGE10_ACTION_REVIEW_TASK_TYPES
    assert "不是买入、卖出或自动下单指令" in definition["plain_language_definition"]

    recommendations = payload["recommendations"]
    assert {item["task_type"] for item in recommendations} == set(STAGE10_ACTION_REVIEW_TASK_TYPES)
    assert all(item["buy_sell_instruction"] is False for item in recommendations)
    assert all(item["required_fields_zh"] == STAGE10_REQUIRED_RECOMMENDATION_FIELDS for item in recommendations)
    assert all(item["evidence_source"] for item in recommendations)
    assert all(item["related_transactions"] for item in recommendations)
    assert all(item["related_parameters"] for item in recommendations)
    assert all(item["related_formulas"] for item in recommendations)
    assert all("expected_impact_amount_cny" in item for item in recommendations)


def test_action_review_scoring_formula_is_weighted_and_rankable() -> None:
    assert sum(STAGE10_SCORING_WEIGHTS.values()) == 100
    assert STAGE10_SCORING_WEIGHTS == {
        "financial_impact": 25,
        "risk_reduction": 20,
        "urgency": 15,
        "confidence": 15,
        "reversibility": 10,
        "execution_cost_inverse": 10,
        "learning_value": 5,
    }

    high = Stage10RecommendationInput(90, 90, 80, 85, 80, 75, 70)
    low = Stage10RecommendationInput(30, 25, 20, 50, 40, 30, 20)
    assert score_action_review_recommendation(high) > score_action_review_recommendation(low)
    assert score_action_review_recommendation(high) == pytest.approx(84.25)

    with pytest.raises(ValueError):
        score_action_review_recommendation({"financial_impact": 100})


def test_lifecycle_supports_effect_measurement_after_review() -> None:
    lifecycle = build_action_review_lifecycle_model()

    assert lifecycle["statuses"] == STAGE10_LIFECYCLE_STATUSES
    assert lifecycle["transitions"]["pending"] == ("accepted", "rejected", "snoozed")
    assert lifecycle["transitions"]["accepted"] == ("reviewed",)
    assert lifecycle["transitions"]["reviewed"] == ("effect_measured",)
    assert lifecycle["terminal_status"] == "effect_measured"
    assert lifecycle["effect_review_required"] is True


def test_parameter_catalog_and_changelog_record_stage10_values() -> None:
    catalog = load_v022_parameter_catalog()
    params = catalog["parameters"]["report_advice_review"]

    assert catalog["schema"] == "PFIParametersV022Stage13"
    assert catalog["current_stage"] == "Stage 13 - 后置触发型复核"
    assert catalog["stage10_task_ids"] == list(V022_STAGE10_TASK_IDS)
    assert params["monthly_report_required_consumption_metrics"]["value"] == ["消费总流出", "生活消费"]
    assert params["investment_report_required_sections"]["value"] == ["收益", "成本", "费用", "汇率", "交易频率", "风格", "现金拖累"]
    assert params["data_quality_report_interconnection_metrics"]["value"] == ["未匹配转账", "重复候选", "低置信", "标签变更", "参数变更", "hash diff"]
    assert params["recommendation_label"]["value"] == "行动建议与复盘"
    assert params["automatic_investment_advice_allowed"]["value"] is False
    assert params["scoring_weights"]["value"] == STAGE10_SCORING_WEIGHTS
    assert params["lifecycle_statuses"]["value"] == list(STAGE10_LIFECYCLE_STATUSES)
    assert params["required_recommendation_fields"]["value"] == list(STAGE10_REQUIRED_RECOMMENDATION_FIELDS)

    changelog = read_text("config/parameter_changelog.md")
    for task_id in V022_STAGE10_TASK_IDS:
        assert task_id in changelog
    assert "report_advice_review.scoring_weights" in changelog
    assert "report_advice_review.lifecycle_statuses" in changelog


def test_stage10_docs_and_human_entry_files_are_chinese_complete() -> None:
    required_terms = (
        "Stage 10 - 报告、建议与复盘",
        "S10-P1-T1",
        "S10-P2-T3",
        "消费总流出",
        "生活消费",
        "收益",
        "成本",
        "费用",
        "汇率",
        "交易频率",
        "风格",
        "现金拖累",
        "未匹配转账",
        "重复候选",
        "低置信",
        "标签变更",
        "参数变更",
        "hash diff",
        "行动建议与复盘",
        "pending",
        "accepted",
        "rejected",
        "snoozed",
        "reviewed",
        "effect_measured",
    )
    for path in (
        "docs/pfi_v022/STAGE10_REPORT_ADVICE_REVIEW.md",
        "docs/pfi_v022/ROADMAP_LOCK.md",
        "README.md",
        "模型参数文件.md",
        "功能清单.md",
        "开发记录.md",
        "HANDOFF.md",
    ):
        text = read_text(path)
        for term in required_terms:
            assert term in text, f"{path} missing {term}"
