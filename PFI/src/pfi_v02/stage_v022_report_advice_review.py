from __future__ import annotations

import csv
from collections import Counter
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Mapping

from pfi_v02.stage_v022_formula_scoring import load_stage7_alipay_formula_inputs_from_metadatabase
from pfi_v02.stage_v022_visualization_uiux import load_stage9_real_visualization_context


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

STAGE10_REAL_DATA_SOURCE = "MetaDatabase/PFI/alipay_daily/processed/alipay_transactions.csv"
STAGE10_REVIEW_RECORD_QUERY = "MetaDatabase/PFI/alipay_daily/processed/alipay_transactions.csv::review_state=NEEDS_REVIEW"
STAGE10_LARGE_SPEND_QUERY = "MetaDatabase/PFI/alipay_daily/processed/alipay_transactions.csv::event_type=ordinary_consumption::amount_cny>=2000"
STAGE10_CASHFLOW_QUERY = "MetaDatabase/PFI/alipay_daily/processed/alipay_transactions.csv::cashflow_projection_inputs"


def _resolve_stage10_roots(project_root: str | Path | None = None) -> tuple[Path, Path]:
    root = Path(project_root).expanduser().resolve() if project_root is not None else Path(__file__).resolve().parents[2]
    if root.name == "PFI":
        return root, root.parent
    if (root / "PFI").is_dir() and (root / "MetaDatabase").is_dir():
        return root / "PFI", root
    return root, root.parent


def _money(value: object) -> Decimal:
    return Decimal(str(value or "0")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _score_value(value: object) -> float:
    return float(Decimal(str(value or "0")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _percent(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == 0:
        return Decimal("0")
    return min(Decimal("100"), (numerator / denominator * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


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


def load_stage10_real_report_advice_context(project_root: str | Path | None = None) -> dict[str, object]:
    pfi_root, repo_root = _resolve_stage10_roots(project_root)
    stage9_context = load_stage9_real_visualization_context(pfi_root)
    metadatabase_root = repo_root / "MetaDatabase" / "PFI" / "alipay_daily"
    transactions_path = repo_root / STAGE10_REAL_DATA_SOURCE

    total_amount_abs = Decimal("0")
    review_amount_abs = Decimal("0")
    review_confidence_sum = Decimal("0")
    review_record_count = 0
    review_state_counts: Counter[str] = Counter()
    if transactions_path.exists():
        with transactions_path.open(encoding="utf-8-sig", newline="") as file_obj:
            for row in csv.DictReader(file_obj):
                amount_abs = abs(Decimal(str(row.get("amount") or "0")))
                total_amount_abs += amount_abs
                review_state = str(row.get("review_state") or "").strip()
                review_state_counts[review_state] += 1
                if review_state == "NEEDS_REVIEW":
                    review_record_count += 1
                    review_amount_abs += amount_abs
                    review_confidence_sum += Decimal(str(row.get("confidence") or "0"))

    stage7_inputs = load_stage7_alipay_formula_inputs_from_metadatabase(metadatabase_root)
    consumption_events = tuple(stage7_inputs["consumption_events"])
    large_spend_events = tuple(
        event
        for event in consumption_events
        if str(event.get("event_type") or "") == "ordinary_consumption"
        and Decimal(str(event.get("amount_cny") or "0")) >= Decimal("2000")
    )
    large_spend_amount = sum((Decimal(str(event.get("amount_cny") or "0")) for event in large_spend_events), Decimal("0"))
    living_event_count = sum(1 for event in consumption_events if str(event.get("event_type") or "") == "ordinary_consumption")
    average_review_confidence = review_confidence_sum / Decimal(review_record_count) if review_record_count else Decimal("0")
    cashflow_inputs = dict(stage7_inputs["cashflow_projection_inputs"])

    return {
        "schema": "PFIV022Stage10RealReportAdviceContextV1",
        "real_data_source": STAGE10_REAL_DATA_SOURCE,
        "normalized_transaction_count": int(stage9_context["normalized_transaction_count"]),
        "raw_file_count": int(stage9_context["raw_file_count"]),
        "review_record_count": review_record_count,
        "review_amount_abs_cny": _money(review_amount_abs),
        "total_amount_abs_cny": _money(total_amount_abs),
        "review_state_counts": dict(review_state_counts),
        "average_review_confidence_pct": _score_value(average_review_confidence * Decimal("100")),
        "large_spend_record_count": len(large_spend_events),
        "large_spend_amount_cny": _money(large_spend_amount),
        "large_spend_record_ratio_pct": _score_value(_percent(Decimal(len(large_spend_events)), Decimal(max(living_event_count, 1)))),
        "gross_consumption_cny": stage9_context["gross_consumption_cny"],
        "living_consumption_cny": stage9_context["living_consumption_cny"],
        "cashflow_projection_inputs": cashflow_inputs,
        "planned_investment_deposit_cny": _money(cashflow_inputs.get("planned_investment_deposit_cny")),
        "investment_data_status_zh": stage9_context["investment_data_status_zh"],
        "interconnection_state_zh": stage9_context["interconnection_state_zh"],
        "subscription_candidate_status_zh": "暂无真实订阅候选文件或订阅规则运行结果，Stage 10 不生成订阅优化假建议。",
        "network_allowed": False,
        "recommendation_generation_policy_zh": "Stage 10 只生成真实数据触发的行动建议；缺少真实证据时返回中文真实空态。",
    }


def build_stage10_report_suite(
    catalog: Mapping[str, object] | None = None,
    *,
    context: Mapping[str, object] | None = None,
    project_root: str | Path | None = None,
) -> dict[str, object]:
    """Build local report contracts derived from the v0.2.2 read-model vocabulary."""
    active_context = context or load_stage10_real_report_advice_context(project_root)
    return {
        "schema": "PFIV022Stage10ReportSuiteV1",
        "source_policy": {
            "source": "真实 MetaDatabase + SQLite/read model 派生口径",
            "base_currency": "CNY",
            "requires_parameter_version": "v0.2.2",
            "catalog_schema": catalog.get("schema") if catalog else None,
            "real_data_source": active_context["real_data_source"],
            "normalized_transaction_count": active_context["normalized_transaction_count"],
        },
        "monthly_report": {
            "template_name": "PFI 月报 - 双消费口径",
            "required_sections": STAGE10_REPORT_SECTIONS["monthly_report"],
            "current_real_metrics_cny": {
                "消费总流出": active_context["gross_consumption_cny"],
                "生活消费": active_context["living_consumption_cny"],
            },
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
            "data_status_zh": active_context["investment_data_status_zh"],
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
            "current_real_metrics": {
                "待复核记录": active_context["review_record_count"],
                "待复核金额覆盖面_CNY": active_context["review_amount_abs_cny"],
                "大额生活消费记录": active_context["large_spend_record_count"],
                "Interconnection 状态": active_context["interconnection_state_zh"],
            },
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


def build_stage10_real_empty_states(context: Mapping[str, object] | None = None) -> dict[str, str]:
    active_context = context or load_stage10_real_report_advice_context()
    empty_states = {
        "投资行为复盘建议": str(active_context["investment_data_status_zh"]),
        "订阅优化建议": str(active_context["subscription_candidate_status_zh"]),
    }
    if int(active_context["review_record_count"]) == 0:
        empty_states["数据修复建议"] = "暂无真实待复核记录，Stage 10 不生成数据修复假建议。"
    if int(active_context["large_spend_record_count"]) == 0:
        empty_states["消费复盘建议"] = "暂无真实大额生活消费触发证据，Stage 10 不生成消费复盘假建议。"
    if Decimal(str(active_context["planned_investment_deposit_cny"])) <= 0:
        empty_states["现金流风险建议"] = "暂无真实投资入金或现金流风险触发证据，Stage 10 不生成现金流风险假建议。"
    return empty_states


def _recommendation(
    *,
    task_type: str,
    title_zh: str,
    evidence_source: str,
    related_transactions: tuple[str, ...],
    related_parameters: tuple[str, ...],
    related_formulas: tuple[str, ...],
    expected_impact_amount_cny: Decimal,
    score_input: Stage10RecommendationInput,
    score_basis_zh: str,
) -> dict[str, object]:
    score = score_action_review_recommendation(score_input)
    return {
        "task_type": task_type,
        "title_zh": title_zh,
        "score": score,
        "score_basis_zh": score_basis_zh,
        "evidence_source": evidence_source,
        "related_transactions": related_transactions,
        "related_parameters": related_parameters,
        "related_formulas": related_formulas,
        "expected_impact_amount_cny": _money(expected_impact_amount_cny),
        "confidence": score_input.confidence,
        "requires_manual_review": True,
        "user_decision_status": "pending",
        "effect_review_status": "pending",
        "required_fields_zh": STAGE10_REQUIRED_RECOMMENDATION_FIELDS,
        "buy_sell_instruction": False,
    }


def build_action_review_recommendations(
    context: Mapping[str, object] | None = None,
    *,
    project_root: str | Path | None = None,
) -> tuple[dict[str, object], ...]:
    active_context = context or load_stage10_real_report_advice_context(project_root)
    real_data_source = str(active_context["real_data_source"])
    recommendations = []

    normalized_count = Decimal(str(active_context["normalized_transaction_count"] or 0))
    total_amount_abs = Decimal(str(active_context["total_amount_abs_cny"] or 0))
    review_count = Decimal(str(active_context["review_record_count"] or 0))
    review_amount = Decimal(str(active_context["review_amount_abs_cny"] or 0))
    review_ratio_score = _percent(review_count * Decimal("10"), normalized_count)
    confidence_pct = Decimal(str(active_context["average_review_confidence_pct"] or 0))
    if review_count > 0:
        recommendations.append(
            _recommendation(
                task_type="数据修复建议",
                title_zh=f"复核 {int(review_count)} 条待复核支付宝流水",
                evidence_source=real_data_source,
                related_transactions=(STAGE10_REVIEW_RECORD_QUERY,),
                related_parameters=("confidence.review_threshold", "report_advice_review.required_recommendation_fields"),
                related_formulas=("Stage 7 置信度评分", "Stage 10 行动建议评分"),
                expected_impact_amount_cny=review_amount,
                score_input=Stage10RecommendationInput(
                    financial_impact=_score_value(_percent(review_amount, total_amount_abs)),
                    risk_reduction=_score_value(Decimal("100") - confidence_pct),
                    urgency=_score_value(review_ratio_score),
                    confidence=_score_value(confidence_pct),
                    reversibility=100,
                    execution_cost_inverse=_score_value(Decimal("100") - min(Decimal("100"), review_count / Decimal("10"))),
                    learning_value=_score_value(min(Decimal("100"), Decimal(len(active_context["review_state_counts"])) * Decimal("25"))),
                ),
                score_basis_zh="评分来自真实待复核记录数、待复核金额覆盖面、平均置信度和人工复核可逆性。",
            )
        )

    large_count = Decimal(str(active_context["large_spend_record_count"] or 0))
    large_amount = Decimal(str(active_context["large_spend_amount_cny"] or 0))
    gross_consumption = Decimal(str(active_context["gross_consumption_cny"] or 0))
    if large_count > 0:
        recommendations.append(
            _recommendation(
                task_type="消费复盘建议",
                title_zh=f"复盘 {int(large_count)} 条真实大额生活消费",
                evidence_source=real_data_source,
                related_transactions=(STAGE10_LARGE_SPEND_QUERY,),
                related_parameters=("consumption_model.large_spend_cny_threshold",),
                related_formulas=("Stage 7 生活消费公式", "Stage 10 行动建议评分"),
                expected_impact_amount_cny=large_amount,
                score_input=Stage10RecommendationInput(
                    financial_impact=_score_value(_percent(large_amount, gross_consumption)),
                    risk_reduction=_score_value(active_context["large_spend_record_ratio_pct"]),
                    urgency=_score_value(min(Decimal("100"), large_count / Decimal("2"))),
                    confidence=95,
                    reversibility=100,
                    execution_cost_inverse=_score_value(Decimal("100") - min(Decimal("100"), large_count / Decimal("5"))),
                    learning_value=80,
                ),
                score_basis_zh="评分来自真实大额生活消费记录数、金额覆盖面、阈值命中比例和人工复盘可逆性。",
            )
        )

    planned_investment_deposit = Decimal(str(active_context["planned_investment_deposit_cny"] or 0))
    if planned_investment_deposit > 0:
        recommendations.append(
            _recommendation(
                task_type="现金流风险建议",
                title_zh="补充真实生活现金账户快照后复核投资入金压力",
                evidence_source=real_data_source,
                related_transactions=(STAGE10_CASHFLOW_QUERY,),
                related_parameters=("cashflow.windows_days", "cashflow.reserve_months_default"),
                related_formulas=("Stage 7 现金流预测公式", "Stage 10 行动建议评分"),
                expected_impact_amount_cny=planned_investment_deposit,
                score_input=Stage10RecommendationInput(
                    financial_impact=_score_value(_percent(planned_investment_deposit, gross_consumption)),
                    risk_reduction=60,
                    urgency=65,
                    confidence=70,
                    reversibility=100,
                    execution_cost_inverse=90,
                    learning_value=75,
                ),
                score_basis_zh="评分来自真实支付宝历史流水中的投资入金规模；当前缺少真实生活现金快照，因此只生成复核任务，不生成现金结论。",
            )
        )

    if review_count > 0:
        recommendations.append(
            _recommendation(
                task_type="参数调整建议",
                title_zh="复核统一低置信阈值对待复核队列的影响",
                evidence_source=real_data_source,
                related_transactions=(STAGE10_REVIEW_RECORD_QUERY,),
                related_parameters=("confidence.review_threshold",),
                related_formulas=("Stage 7 置信度评分", "Stage 9 参数影响预览", "Stage 10 行动建议评分"),
                expected_impact_amount_cny=Decimal("0"),
                score_input=Stage10RecommendationInput(
                    financial_impact=0,
                    risk_reduction=_score_value(Decimal("100") - confidence_pct),
                    urgency=_score_value(review_ratio_score),
                    confidence=_score_value(confidence_pct),
                    reversibility=100,
                    execution_cost_inverse=70,
                    learning_value=90,
                ),
                score_basis_zh="评分来自真实待复核记录数量和平均置信度；该建议只要求人工复核阈值，不自动改参数。",
            )
        )

    return tuple(sorted(recommendations, key=lambda item: item["score"], reverse=True))


def build_stage10_contract_payload(
    catalog: Mapping[str, object] | None = None,
    *,
    context: Mapping[str, object] | None = None,
    project_root: str | Path | None = None,
) -> dict[str, object]:
    active_context = context or load_stage10_real_report_advice_context(project_root)
    return {
        "schema": "PFIV022Stage10ReportAdviceReviewPayloadV1",
        "report_suite": build_stage10_report_suite(catalog, context=active_context, project_root=project_root),
        "action_review_definition": build_action_review_definition(),
        "scoring_formula": build_action_review_scoring_formula(),
        "lifecycle": build_action_review_lifecycle_model(),
        "recommendations": build_action_review_recommendations(active_context, project_root=project_root),
        "real_context": active_context,
        "real_empty_states": build_stage10_real_empty_states(active_context),
    }
