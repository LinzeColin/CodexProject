from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from pfi_os.risk.gates import RiskGateResult
from pfi_os.strategies.profiles import DEFAULT_STRATEGY_PROFILE, get_strategy_profile


RESEARCH_STATUSES = {"ContinueResearch", "WatchOnly", "NeedsMoreEvidence", "DoNotUse"}


@dataclass(frozen=True)
class DecisionQualityDimension:
    key: str
    label: str
    score: int
    status: str
    evidence: str


@dataclass(frozen=True)
class DecisionQualityResult:
    status: str
    score: int
    dimensions: list[DecisionQualityDimension]
    passed_items: list[str]
    missing_evidence: list[str]
    warnings: list[str]
    research_actions: list[str]
    simulated_exposure: dict[str, Any] = field(default_factory=dict)


def evaluate_decision_quality(
    result: Any | None = None,
    metrics: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
    trades: pd.DataFrame | None = None,
    positions: pd.DataFrame | None = None,
    risk_gate: RiskGateResult | None = None,
    data_quality_status: str | None = None,
    cross_validation_status: str | None = None,
    stability: dict[str, Any] | None = None,
    train_test: dict[str, Any] | None = None,
    walk_forward: dict[str, Any] | None = None,
) -> DecisionQualityResult:
    if result is not None:
        metrics = metrics or getattr(result, "metrics", None)
        metadata = metadata or getattr(result, "metadata", None)
        trades = trades if trades is not None else getattr(result, "trades", None)
        positions = positions if positions is not None else getattr(result, "positions", None)

    metrics = metrics or {}
    metadata = metadata or {}
    trades = _frame(trades)
    positions = _frame(positions)
    stability = stability or {}
    train_test = train_test or {}
    walk_forward = walk_forward or {}

    strategy_meta = metadata.get("strategy", {}) if isinstance(metadata, dict) else {}
    backtest_meta = metadata.get("backtest", {}) if isinstance(metadata, dict) else {}
    strategy_id = str(strategy_meta.get("strategy_id", "") or "")
    profile = get_strategy_profile(strategy_id) if strategy_id else DEFAULT_STRATEGY_PROFILE

    dimensions: list[DecisionQualityDimension] = []
    missing: list[str] = []
    warnings: list[str] = []

    def add_dimension(key: str, label: str, score: int, status: str, evidence: str, *, critical: bool = False) -> None:
        score_clamped = max(0, min(10, int(score)))
        dimensions.append(DecisionQualityDimension(key=key, label=label, score=score_clamped, status=status, evidence=evidence))
        if status == "缺失" and critical:
            missing.append(label)

    thesis_missing = profile.strategy_id == "unknown" or not _substantive(profile.thesis)
    add_dimension(
        "thesis_clarity",
        "Thesis 清晰度",
        4 if thesis_missing else 8,
        "缺失" if thesis_missing else "通过",
        profile.thesis,
        critical=True,
    )

    data_ok = data_quality_status in {"Pass", "Info"}
    cross_ok = cross_validation_status in {"Pass", "Info"}
    if not data_quality_status:
        evidence_status = "缺失"
        evidence_score = 3
        evidence_text = "缺少数据质量检查。"
        missing.append("数据质量检查")
    elif not cross_validation_status:
        evidence_status = "缺失"
        evidence_score = 4 if data_ok else 2
        evidence_text = f"数据质量：{data_quality_status}；缺少多源交叉校验。"
        missing.append("多源交叉校验")
    elif data_ok and cross_ok:
        evidence_status = "通过"
        evidence_score = 9
        evidence_text = f"数据质量：{data_quality_status}；多源校验：{cross_validation_status}。"
    else:
        evidence_status = "需复核"
        evidence_score = 5 if data_ok else 2
        evidence_text = f"数据质量：{data_quality_status}；多源校验：{cross_validation_status}。"
        warnings.append("数据或多源校验未完全通过。")
    add_dimension("evidence_quality", "证据质量", evidence_score, evidence_status, evidence_text, critical=evidence_status == "缺失")

    risk_status = risk_gate.status if risk_gate else ""
    risk_reason_count = len(risk_gate.reasons) if risk_gate else 0
    if not risk_gate:
        add_dimension("risk_identification", "风险识别", 4, "缺失", "缺少研究风险闸门结果。", critical=True)
        missing.append("研究风险闸门")
    else:
        risk_score = 9 if risk_status == "ContinueResearch" else 6 if risk_status in {"WatchOnly", "NeedsMoreEvidence"} else 3
        risk_dimension_status = "通过" if risk_status == "ContinueResearch" else "需复核"
        add_dimension(
            "risk_identification",
            "风险识别",
            risk_score,
            risk_dimension_status,
            f"研究状态：{risk_status}；触发原因：{risk_reason_count} 项。",
        )

    exit_missing = not _substantive(profile.failure)
    add_dimension(
        "exit_condition",
        "退出与停用条件",
        4 if exit_missing else 8,
        "缺失" if exit_missing else "通过",
        profile.failure,
        critical=True,
    )

    allow_short = bool(backtest_meta.get("allow_short", False))
    max_weight = _max_actual_weight(positions)
    if allow_short:
        discipline_score = 4
        discipline_status = "需复核"
        discipline_text = f"配置允许负持仓；最大历史暴露比例 {max_weight:.2%}。"
        warnings.append("当前配置允许负持仓，不符合只做多研究边界。")
    elif max_weight > 1.2:
        discipline_score = 5
        discipline_status = "需复核"
        discipline_text = f"最大历史暴露比例 {max_weight:.2%}，需要复核杠杆或现金约束。"
        warnings.append("历史模拟暴露比例偏高。")
    else:
        discipline_score = 9
        discipline_status = "通过"
        discipline_text = f"未启用负持仓；最大历史暴露比例 {max_weight:.2%}。"
    add_dimension("position_discipline", "暴露纪律", discipline_score, discipline_status, discipline_text)

    impulse_score = 6 if strategy_id in {"alipay", "alipay_enhanced"} else 7
    impulse_text = "需要用复盘记录检查 FOMO、恐慌、亏损补仓过快等情绪偏差；当前模块只基于回测与策略画像初筛。"
    add_dimension("emotional_impulse_risk", "情绪冲动风险", impulse_score, "需复核", impulse_text)
    warnings.append("情绪冲动风险需要通过复盘模块继续记录，不能仅靠回测判断。")

    counter_missing = not _substantive(profile.persistence) or not _substantive(profile.failure)
    add_dimension(
        "counterargument_quality",
        "反方观点质量",
        5 if counter_missing else 8,
        "缺失" if counter_missing else "需复核",
        f"长期存在理由：{profile.persistence}；失效环境：{profile.failure}",
        critical=counter_missing,
    )

    cost_total = _safe_float(metrics.get("cost_total", 0.0))
    ending_equity = _safe_float(metrics.get("ending_equity", 0.0))
    cost_ratio = cost_total / ending_equity if ending_equity else 0.0
    market_impact_bps = _safe_float(backtest_meta.get("market_impact_bps", 0.0))
    slippage_bps = _safe_float(backtest_meta.get("slippage_bps", 0.0))
    if market_impact_bps <= 0:
        liquidity_score = 5
        liquidity_status = "需复核"
        liquidity_text = f"已建模滑点 {slippage_bps:.2f} bps，但市场冲击成本为 {market_impact_bps:.2f} bps。"
        warnings.append("市场冲击成本未建模或为零。")
    elif cost_ratio > 0.08:
        liquidity_score = 3
        liquidity_status = "需复核"
        liquidity_text = f"累计交易摩擦占期末权益 {cost_ratio:.2%}，高于 8% 风险阈值。"
    else:
        liquidity_score = 8
        liquidity_status = "通过"
        liquidity_text = f"滑点 {slippage_bps:.2f} bps；市场冲击 {market_impact_bps:.2f} bps；成本占比 {cost_ratio:.2%}。"
    add_dimension("liquidity_risk", "流动性风险", liquidity_score, liquidity_status, liquidity_text)

    data_dimension_score = 9 if data_quality_status == "Pass" else 7 if data_quality_status == "Info" else 3 if data_quality_status else 2
    data_dimension_status = "通过" if data_quality_status in {"Pass", "Info"} else "缺失" if not data_quality_status else "需复核"
    add_dimension(
        "data_quality",
        "数据质量",
        data_dimension_score,
        data_dimension_status,
        f"数据质量状态：{data_quality_status or '缺失'}。",
        critical=not data_quality_status,
    )

    stability_status = str(stability.get("stability_status", "") or "")
    train_status = str(train_test.get("validation_status", "") or "")
    walk_status = str(walk_forward.get("validation_status", "") or "")
    missing_validation = []
    if not stability_status:
        missing_validation.append("参数稳定性")
    if not train_status:
        missing_validation.append("样本外验证")
    if not walk_status:
        missing_validation.append("walk-forward")
    if missing_validation:
        validation_status = "缺失"
        validation_score = 4
        validation_text = "缺少：" + "、".join(missing_validation)
        missing.extend(missing_validation)
    elif any(status in {"Failed", "Review", "InsufficientData"} for status in [stability_status, train_status, walk_status]):
        validation_status = "需复核"
        validation_score = 4
        validation_text = f"参数稳定性：{stability_status}；样本外：{train_status}；walk-forward：{walk_status}。"
        warnings.append("回测验证结果存在需复核项。")
    elif any(status == "Watch" for status in [stability_status, train_status, walk_status]):
        validation_status = "需复核"
        validation_score = 6
        validation_text = f"参数稳定性：{stability_status}；样本外：{train_status}；walk-forward：{walk_status}。"
    else:
        validation_status = "通过"
        validation_score = 9
        validation_text = f"参数稳定性：{stability_status}；样本外：{train_status}；walk-forward：{walk_status}。"
    add_dimension("backtest_validation", "回测验证充分度", validation_score, validation_status, validation_text, critical=validation_status == "缺失")

    score = round(sum(item.score for item in dimensions) / max(len(dimensions), 1) * 10)
    status = _decision_status(score, missing, risk_gate)
    passed_items = [item.label for item in dimensions if item.status == "通过"]
    research_actions = _research_actions(status, missing, warnings, risk_gate)
    simulated_exposure = simulated_exposure_summary(trades=trades, positions=positions, metadata=metadata)

    return DecisionQualityResult(
        status=status,
        score=score,
        dimensions=dimensions,
        passed_items=passed_items,
        missing_evidence=_unique(missing),
        warnings=_unique(warnings),
        research_actions=research_actions,
        simulated_exposure=simulated_exposure,
    )


def simulated_exposure_summary(
    trades: pd.DataFrame | None,
    positions: pd.DataFrame | None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    trades = _frame(trades)
    positions = _frame(positions)
    metadata = metadata or {}
    backtest = metadata.get("backtest", {}) if isinstance(metadata, dict) else {}
    initial_cash = _safe_float(backtest.get("initial_cash", 0.0))

    exposure_increase = 0.0
    exposure_reduction = 0.0
    increase_count = 0
    reduction_count = 0
    if not trades.empty and "side" in trades.columns and "notional" in trades.columns:
        notional = pd.to_numeric(trades["notional"], errors="coerce").fillna(0.0).abs()
        side = trades["side"].astype(str).str.upper()
        exposure_increase = float(notional[side == "BUY"].sum())
        exposure_reduction = float(notional[side == "SELL"].sum())
        increase_count = int((side == "BUY").sum())
        reduction_count = int((side == "SELL").sum())

    ending_position_value = 0.0
    ending_equity = 0.0
    ending_exposure_ratio = 0.0
    if not positions.empty:
        last = positions.iloc[-1]
        ending_position_value = _safe_float(last.get("position_value", 0.0))
        ending_equity = _safe_float(last.get("equity", 0.0))
        ending_exposure_ratio = ending_position_value / ending_equity if ending_equity else 0.0

    return {
        "initial_cash": initial_cash,
        "simulated_exposure_increase_amount": exposure_increase,
        "simulated_exposure_increase_ratio": exposure_increase / initial_cash if initial_cash else 0.0,
        "simulated_exposure_reduction_amount": exposure_reduction,
        "simulated_exposure_reduction_ratio": exposure_reduction / initial_cash if initial_cash else 0.0,
        "simulated_exposure_increase_count": increase_count,
        "simulated_exposure_reduction_count": reduction_count,
        "ending_position_value": ending_position_value,
        "ending_equity": ending_equity,
        "ending_exposure_ratio": ending_exposure_ratio,
    }


def _decision_status(score: int, missing: list[str], risk_gate: RiskGateResult | None) -> str:
    if missing:
        return "NeedsMoreEvidence"
    if risk_gate and risk_gate.status == "DoNotUse":
        return "DoNotUse"
    if score >= 80:
        return "ContinueResearch"
    if score >= 60:
        return "WatchOnly"
    if score >= 40:
        return "NeedsMoreEvidence"
    return "DoNotUse"


def _research_actions(
    status: str,
    missing: list[str],
    warnings: list[str],
    risk_gate: RiskGateResult | None,
) -> list[str]:
    if status == "ContinueResearch":
        return ["继续研究，重点复核未来数据、成本压力和样本外稳定性。"]
    if status == "WatchOnly":
        return ["仅作为观察线索，等待更多验证结果改善后再升级研究状态。"]
    if status == "DoNotUse":
        return ["暂停使用该研究结论，先处理已触发的风险门禁。"]
    actions = ["补齐关键证据后重新评分。"]
    for item in _unique(missing):
        actions.append(f"补充：{item}。")
    if risk_gate and risk_gate.actions:
        actions.extend(risk_gate.actions[:3])
    elif warnings:
        actions.extend(warnings[:3])
    return _unique(actions)


def _frame(value: pd.DataFrame | None) -> pd.DataFrame:
    if isinstance(value, pd.DataFrame):
        return value
    return pd.DataFrame()


def _substantive(text: str | None) -> bool:
    if not text:
        return False
    stripped = str(text).strip()
    if not stripped:
        return False
    return "未显式定义" not in stripped and "not explicitly defined" not in stripped


def _max_actual_weight(positions: pd.DataFrame) -> float:
    if positions.empty:
        return 0.0
    if "actual_weight" in positions.columns:
        values = pd.to_numeric(positions["actual_weight"], errors="coerce").fillna(0.0)
        return float(values.abs().max())
    if {"position_value", "equity"}.issubset(positions.columns):
        value = pd.to_numeric(positions["position_value"], errors="coerce").fillna(0.0).abs()
        equity = pd.to_numeric(positions["equity"], errors="coerce").replace(0, pd.NA).abs()
        ratio = (value / equity).fillna(0.0)
        return float(ratio.max())
    return 0.0


def _safe_float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    unique_items: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            unique_items.append(item)
    return unique_items
