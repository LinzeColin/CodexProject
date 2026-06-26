from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RiskGateResult:
    status: str
    score: int
    reasons: list[str]
    actions: list[str]
    missing_evidence: list[str] = field(default_factory=list)


def evaluate_research_risk_gates(
    metrics: dict[str, Any] | None = None,
    stability: dict[str, Any] | None = None,
    train_test: dict[str, Any] | None = None,
    walk_forward: dict[str, Any] | None = None,
    data_quality_status: str | None = None,
    max_drawdown_limit: float = -0.25,
    max_cost_ratio: float = 0.08,
) -> RiskGateResult:
    metrics = metrics or {}
    stability = stability or {}
    train_test = train_test or {}
    walk_forward = walk_forward or {}
    reasons: list[str] = []
    actions: list[str] = []
    missing_evidence: list[str] = []
    score = 0

    total_return = _float(metrics.get("total_return", 0.0))
    max_drawdown = _float(metrics.get("max_drawdown", 0.0))
    cost_total = _float(metrics.get("cost_total", 0.0))
    ending_equity = _float(metrics.get("ending_equity", 0.0))
    cost_ratio = cost_total / ending_equity if ending_equity else 0.0

    if not data_quality_status:
        score += 2
        missing_evidence.append("数据质量检查")
        reasons.append("Data quality evidence is missing.")
        actions.append("补充数据质量检查后再把该结果作为交易前研究参考。")
    elif data_quality_status not in {"Pass", "Info"}:
        score += 3
        reasons.append(f"Data quality status is {data_quality_status}.")
        actions.append("暂停把该结果作为交易前研究参考，先复核数据质量。")

    if total_return <= 0:
        score += 3
        reasons.append("Total return is not positive.")
        actions.append("暂停使用该研究候选，重新验证收益来源。")

    if max_drawdown < max_drawdown_limit:
        score += 3
        reasons.append(f"Maximum drawdown {max_drawdown:.2%} breaches limit {max_drawdown_limit:.2%}.")
        actions.append("复核暴露纪律、回撤承受能力和失效条件。")

    if cost_ratio > max_cost_ratio:
        score += 2
        reasons.append(f"Modeled trading friction ratio {cost_ratio:.2%} is high.")
        actions.append("复核换手率、流动性、滑点和市场冲击假设。")

    stability_status = str(stability.get("stability_status", ""))
    if not stability_status:
        missing_evidence.append("参数稳定性验证")
        reasons.append("Parameter stability evidence is missing.")
        actions.append("补充参数扫描或稳定性验证，避免只依赖单一参数结果。")
    if stability_status in {"Fragile", "Review", "InsufficientData"}:
        score += 2
        reasons.append(f"Parameter stability status is {stability_status}.")
        actions.append("不要只依赖单一最佳参数，扩展鲁棒性验证。")

    train_test_status = str(train_test.get("validation_status", ""))
    if not train_test_status:
        missing_evidence.append("样本内/样本外验证")
        reasons.append("Train-test validation evidence is missing.")
        actions.append("补充样本外验证后再提高研究状态。")
    if train_test_status in {"Failed", "Review", "InsufficientData"}:
        score += 3
        reasons.append(f"Train-test validation status is {train_test_status}.")
        actions.append("暂停作为决策前研究参考，直到样本外证据改善。")
    elif train_test_status == "Watch":
        score += 1
        reasons.append("Train-test validation is Watch.")
        actions.append("补充更多验证后再提高研究状态。")

    walk_forward_status = str(walk_forward.get("validation_status", ""))
    if not walk_forward_status:
        missing_evidence.append("walk-forward 验证")
        reasons.append("Walk-forward validation evidence is missing.")
        actions.append("补充滚动样本外验证，检查规律是否跨时间段稳定。")
    if walk_forward_status in {"Failed", "Review", "InsufficientData"}:
        score += 6
        reasons.append(f"Walk-forward validation status is {walk_forward_status}.")
        actions.append("暂停使用该研究候选，直到滚动样本外表现改善。")
    elif walk_forward_status == "Watch":
        score += 2
        reasons.append("Walk-forward validation is Watch.")
        actions.append("保持观察，不要视为高置信研究证据。")

    status = _risk_status(score, missing_evidence)
    if not reasons:
        reasons.append("No major research risk gate was triggered.")
        actions.append("继续研究，并持续监控未来数据、成本和样本外证据。")
    return RiskGateResult(
        status=status,
        score=score,
        reasons=reasons,
        actions=actions,
        missing_evidence=missing_evidence,
    )


def _risk_status(score: int, missing_evidence: list[str] | None = None) -> str:
    if missing_evidence:
        return "NeedsMoreEvidence"
    if score >= 6:
        return "DoNotUse"
    if score >= 2:
        return "WatchOnly"
    return "ContinueResearch"


def _float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
