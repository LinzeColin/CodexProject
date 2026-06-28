from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


STAGE10_REPORT_SECTIONS = {
    "monthly_report": ("消费总流出", "生活消费", "净资产", "现金流", "投资", "建议复盘"),
    "investment_report": ("收益", "成本", "费用", "汇率", "交易频率", "风格", "现金拖累"),
    "data_quality_report": ("未匹配转账", "重复候选", "低置信", "标签变更", "参数变更", "hash diff"),
}

STAGE10_ACTION_REVIEW_TASK_TYPES = (
    "数据修复建议",
    "消费复盘建议",
    "投资行为复盘建议",
    "现金流风险建议",
    "订阅优化建议",
    "参数调整建议",
)

STAGE10_REQUIRED_RECOMMENDATION_FIELDS = (
    "证据来源",
    "相关交易",
    "相关参数",
    "相关公式",
    "预期影响金额 CNY",
    "置信度",
    "是否需要人工复核",
    "用户决策状态",
    "效果复盘状态",
)

STAGE10_LIFECYCLE_STATUSES = (
    "pending",
    "accepted",
    "rejected",
    "snoozed",
    "reviewed",
    "effect_measured",
)

STAGE10_LIFECYCLE_TRANSITIONS = {
    "pending": ("accepted", "rejected", "snoozed"),
    "snoozed": ("pending", "accepted", "rejected"),
    "accepted": ("reviewed",),
    "reviewed": ("effect_measured",),
    "rejected": ("reviewed",),
    "effect_measured": (),
}

STAGE10_SCORING_WEIGHTS = {
    "financial_impact": 25,
    "risk_reduction": 20,
    "urgency": 15,
    "confidence": 15,
    "reversibility": 10,
    "execution_cost_inverse": 10,
    "learning_value": 5,
}

STAGE10_SCORING_COMPONENT_LABELS = {
    "financial_impact": "财务影响分",
    "risk_reduction": "风险降低分",
    "urgency": "紧急程度分",
    "confidence": "置信度分",
    "reversibility": "可逆性分",
    "execution_cost_inverse": "执行成本反比分",
    "learning_value": "学习价值分",
}


@dataclass(frozen=True)
class Stage10RecommendationInput:
    financial_impact: float
    risk_reduction: float
    urgency: float
    confidence: float
    reversibility: float
    execution_cost_inverse: float
    learning_value: float

    def as_mapping(self) -> dict[str, float]:
        return {
            "financial_impact": self.financial_impact,
            "risk_reduction": self.risk_reduction,
            "urgency": self.urgency,
            "confidence": self.confidence,
            "reversibility": self.reversibility,
            "execution_cost_inverse": self.execution_cost_inverse,
            "learning_value": self.learning_value,
        }


def score_action_review_recommendation(
    scores: Stage10RecommendationInput | Mapping[str, float],
    weights: Mapping[str, int] | None = None,
) -> float:
    """Return a 0-100 weighted score for an action-review recommendation."""
    score_mapping = scores.as_mapping() if isinstance(scores, Stage10RecommendationInput) else dict(scores)
    effective_weights = dict(weights or STAGE10_SCORING_WEIGHTS)
    if set(score_mapping) != set(effective_weights):
        missing = sorted(set(effective_weights) - set(score_mapping))
        extra = sorted(set(score_mapping) - set(effective_weights))
        raise ValueError(f"评分字段不完整 missing={missing} extra={extra}")
    total_weight = sum(effective_weights.values())
    if total_weight != 100:
        raise ValueError(f"行动建议评分权重必须合计 100，当前为 {total_weight}")
    for key, value in score_mapping.items():
        if value < 0 or value > 100:
            raise ValueError(f"{key} 分数必须在 0-100 之间")
    weighted = sum(score_mapping[key] * effective_weights[key] / 100 for key in effective_weights)
    return round(weighted, 2)


def build_stage10_report_suite(catalog: Mapping[str, object] | None = None) -> dict[str, object]:
    """Build local report contracts derived from the v0.2.2 read-model vocabulary."""
    return {
        "schema": "PFIV022Stage10ReportSuiteV1",
        "source_policy": {
            "source": "SQLite/read model 派生口径",
            "base_currency": "CNY",
            "requires_parameter_version": "v0.2.2",
            "catalog_schema": catalog.get("schema") if catalog else None,
        },
        "monthly_report": {
            "template_name": "PFI 月报 - 双消费口径",
            "required_sections": STAGE10_REPORT_SECTIONS["monthly_report"],
            "dual_consumption_metrics": {
                "total_consumption_outflow": {
                    "label_zh": "消费总流出",
                    "formula_source": "Stage 7 消费总流出公式",
                    "included_flows": ("生活消费", "投资入金", "基金申购", "黄金申购", "投资买入", "金融费用"),
                    "currency": "CNY",
                },
                "living_consumption": {
                    "label_zh": "生活消费",
                    "formula_source": "Stage 7 生活消费公式",
                    "excluded_flows": ("投资入金", "基金申购", "黄金申购", "投资买入", "内部转账", "信用卡还款"),
                    "currency": "CNY",
                },
            },
        },
        "investment_report": {
            "template_name": "PFI 投资报告 - 成本与行为",
            "required_sections": STAGE10_REPORT_SECTIONS["investment_report"],
            "metrics": {
                "return": "收益",
                "cost": "成本",
                "fees": "费用",
                "fx_effect": "汇率",
                "trading_frequency": "交易频率",
                "style": "风格",
                "cash_drag": "现金拖累",
            },
            "must_not_be_return_only": True,
        },
        "data_quality_report": {
            "template_name": "PFI 数据质量报告 - Interconnection 指标",
            "required_sections": STAGE10_REPORT_SECTIONS["data_quality_report"],
            "interconnection_metrics": {
                "unmatched_transfers": "未匹配转账",
                "duplicate_candidates": "重复候选",
                "low_confidence": "低置信",
                "tag_changes": "标签变更",
                "parameter_changes": "参数变更",
                "hash_diff": "hash diff",
            },
        },
    }


def build_action_review_definition() -> dict[str, object]:
    return {
        "label_zh": "行动建议与复盘",
        "legacy_label_policy": "推荐一律解释为行动建议与复盘。",
        "automatic_investment_advice_allowed": False,
        "automatic_buy_sell_instruction_allowed": False,
        "real_trade_submission_allowed": False,
        "allowed_task_types": STAGE10_ACTION_REVIEW_TASK_TYPES,
        "plain_language_definition": "行动建议与复盘是数据修复、消费复盘、投资行为复盘、现金流风险、订阅优化和参数调整任务；不是买入、卖出或自动下单指令。",
    }


def build_action_review_scoring_formula() -> dict[str, object]:
    return {
        "formula_id": "stage10_action_review_score",
        "name_zh": "行动建议评分",
        "weights": STAGE10_SCORING_WEIGHTS,
        "component_labels": STAGE10_SCORING_COMPONENT_LABELS,
        "execution_difficulty_policy": "执行难度以执行成本反比分表达：越容易执行，分数越高。",
        "formula_zh": "财务影响分×25% + 风险降低分×20% + 紧急程度分×15% + 置信度分×15% + 可逆性分×10% + 执行成本反比分×10% + 学习价值分×5%",
        "total_weight": sum(STAGE10_SCORING_WEIGHTS.values()),
    }


def build_action_review_lifecycle_model() -> dict[str, object]:
    return {
        "statuses": STAGE10_LIFECYCLE_STATUSES,
        "transitions": STAGE10_LIFECYCLE_TRANSITIONS,
        "effect_review_required": True,
        "terminal_status": "effect_measured",
        "can_measure_effect_after": ("reviewed",),
    }


def build_action_review_recommendations() -> tuple[dict[str, object], ...]:
    raw_items = (
        ("数据修复建议", "补齐低置信账单对手方", "tx_alipay_20260601_001", 1200, Stage10RecommendationInput(55, 90, 80, 70, 95, 80, 65)),
        ("消费复盘建议", "复盘本月大额生活消费", "tx_living_20260603_009", 860, Stage10RecommendationInput(65, 55, 60, 75, 90, 70, 80)),
        ("投资行为复盘建议", "复盘追涨买入后的现金拖累", "trade_moomoo_20260528_002", 2400, Stage10RecommendationInput(80, 75, 70, 68, 65, 55, 90)),
        ("现金流风险建议", "复核未来 21 天储备金安全带", "cashflow_window_21d", 1800, Stage10RecommendationInput(78, 82, 85, 72, 85, 65, 75)),
        ("订阅优化建议", "确认重复订阅是否仍需要", "tx_subscription_20260605_004", 168, Stage10RecommendationInput(35, 45, 40, 88, 98, 95, 55)),
        ("参数调整建议", "复核低置信阈值是否仍为 70 分", "param_confidence_review_threshold", 0, Stage10RecommendationInput(45, 70, 55, 75, 90, 60, 85)),
    )
    recommendations = []
    for task_type, title, evidence_id, impact_cny, score_input in raw_items:
        score = score_action_review_recommendation(score_input)
        recommendations.append(
            {
                "task_type": task_type,
                "title_zh": title,
                "score": score,
                "evidence_source": "PFI SQLite/read model",
                "related_transactions": (evidence_id,),
                "related_parameters": ("pfi_parameters.yaml",),
                "related_formulas": ("Stage 7 公式", "Stage 10 行动建议评分"),
                "expected_impact_amount_cny": impact_cny,
                "confidence": score_input.confidence,
                "requires_manual_review": True,
                "user_decision_status": "pending",
                "effect_review_status": "pending",
                "required_fields_zh": STAGE10_REQUIRED_RECOMMENDATION_FIELDS,
                "buy_sell_instruction": False,
            }
        )
    return tuple(sorted(recommendations, key=lambda item: item["score"], reverse=True))


def build_stage10_contract_payload(catalog: Mapping[str, object] | None = None) -> dict[str, object]:
    return {
        "schema": "PFIV022Stage10ReportAdviceReviewPayloadV1",
        "report_suite": build_stage10_report_suite(catalog),
        "action_review_definition": build_action_review_definition(),
        "scoring_formula": build_action_review_scoring_formula(),
        "lifecycle": build_action_review_lifecycle_model(),
        "recommendations": build_action_review_recommendations(),
    }
