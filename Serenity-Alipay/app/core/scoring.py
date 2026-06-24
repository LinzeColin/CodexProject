from __future__ import annotations

from dataclasses import dataclass

from app.adapters.manual_sources import Candidate, FundRule
from app.config import Settings
from app.core.metrics import AssetMetrics, WINDOWS


CONSERVATIVE_KEYWORDS = ("bond", "money", "cash", "yuebao", "conservative", "fixed income")
BUY_LIMITED_STATUSES = {"limited", "restricted", "quota_limited", "large_purchase_limited"}
EXECUTABLE_REDEMPTION_STATUSES = {"open", "limited", "restricted"}
EXECUTION_CRITICAL_FIELDS = {
    "subscription_status",
    "redemption_status",
    "subscription_fee",
    "redemption_fee",
    "subscription_fee_schedule",
    "redemption_fee_schedule",
    "management_fee",
    "custody_fee",
}


@dataclass(frozen=True)
class ScoreResult:
    total_score: float
    data_score: float
    timeliness_score: float
    source_score: float
    return_score: float
    risk_score: float
    executable_score: float
    evidence_coverage: float
    grade: str
    hard_block_reason: str | None
    action_label: str
    trigger_reason: str
    manual_review_required: bool
    missing_fields: tuple[str, ...]


def _is_conservative(candidate: Candidate) -> bool:
    haystack = " ".join(
        [
            candidate.asset_name,
            candidate.asset_type,
            candidate.risk_level,
            candidate.theme,
            candidate.exclusion_reason,
        ]
    ).lower()
    return any(keyword in haystack for keyword in CONSERVATIVE_KEYWORDS)


def _grade_from_score(score: float) -> str:
    if score >= 85:
        return "Action-Ready"
    if score >= 70:
        return "Watch"
    if score >= 55:
        return "Manual Review"
    return "Block"


def _benchmark_win_count(
    metrics: AssetMetrics,
    shanghai: dict[str, float | None],
    sp500: dict[str, float | None],
) -> int:
    wins = 0
    for window in WINDOWS:
        value = metrics.returns.get(window)
        if value is None:
            continue
        sh_value = shanghai.get(window)
        sp_value = sp500.get(window)
        if sh_value is not None and value > sh_value:
            wins += 1
        if sp_value is not None and value > sp_value:
            wins += 1
    return wins


def _missing_penalty(field: str) -> float:
    if field in {"return_windows", "nav_history_24m"}:
        return 20.0
    return 8.0


def _status_key(value: str | None) -> str:
    return (value or "").strip().lower().replace(" ", "_").replace("-", "_")


def _has_execution_data_gap(missing: list[str]) -> bool:
    return bool(EXECUTION_CRITICAL_FIELDS.intersection(missing))


def _execution_score(rule: FundRule | None, missing: list[str]) -> tuple[float, str | None]:
    if rule is None:
        return 0.0, "missing"
    if _has_execution_data_gap(missing):
        return 0.0, "missing"

    subscription_status = _status_key(rule.subscription_status)
    redemption_status = _status_key(rule.redemption_status)
    if redemption_status not in EXECUTABLE_REDEMPTION_STATUSES:
        return 0.0, "closed"
    if subscription_status == "open":
        return (8.0, "limited") if redemption_status != "open" else (10.0, None)
    if subscription_status in BUY_LIMITED_STATUSES:
        return 7.0, "limited"
    return 0.0, "closed"


def score_candidate(
    candidate: Candidate,
    rule: FundRule | None,
    metrics: AssetMetrics,
    shanghai_returns: dict[str, float | None],
    sp500_returns: dict[str, float | None],
    settings: Settings,
) -> ScoreResult:
    missing: list[str] = []
    min_history_span_days = settings.min_candidate_nav_history_span_days
    if metrics.history_span_days is None or metrics.history_span_days < min_history_span_days:
        missing.append("nav_history_24m")
    if any(metrics.returns.get(window) is None for window in WINDOWS):
        missing.append("return_windows")
    if metrics.max_drawdown is None:
        missing.append("max_drawdown")
    if rule is None:
        missing.extend(["subscription_status", "redemption_status", "fee_schedule"])
    else:
        for field, value in {
            "subscription_status": rule.subscription_status,
            "redemption_status": rule.redemption_status,
            "cutoff_time": rule.cutoff_time,
            "confirm_lag": rule.confirm_lag,
            "redeem_lag": rule.redeem_lag,
            "subscription_fee": rule.subscription_fee,
            "redemption_fee": rule.redemption_fee,
            "subscription_fee_schedule": rule.subscription_fee_schedule,
            "redemption_fee_schedule": rule.redemption_fee_schedule,
            "management_fee": rule.management_fee,
            "custody_fee": rule.custody_fee,
        }.items():
            if value in (None, ""):
                missing.append(field)

    data_score = max(0.0, 25.0 - sum(_missing_penalty(field) for field in set(missing)))

    stale_days = max(candidate.missing_nav_days, candidate.missing_holding_days)
    timeliness_score = 15.0 if stale_days <= 2 else 0.0

    if candidate.official_source_count >= settings.min_official_sources_action_ready and not candidate.conflict_flag:
        source_score = 15.0
    elif candidate.official_source_count >= 1 and not candidate.conflict_flag:
        source_score = 7.5
    else:
        source_score = 0.0

    wins = _benchmark_win_count(metrics, shanghai_returns, sp500_returns)
    benchmark_comparison_count = len(WINDOWS) * 2
    return_score = 15.0 * (wins / benchmark_comparison_count) if benchmark_comparison_count else 0.0

    risk_score = 0.0
    if metrics.max_drawdown is not None:
        if metrics.max_drawdown < settings.max_drawdown_block:
            risk_score = max(0.0, 20.0 - (metrics.max_drawdown * 20.0))
    if metrics.recovery_time_days is not None and metrics.recovery_time_days >= settings.recovery_time_block_days:
        risk_score = min(risk_score, 5.0)

    executable_score, execution_constraint = _execution_score(rule, missing)

    total = data_score + timeliness_score + source_score + return_score + risk_score + executable_score
    grade = _grade_from_score(total)
    hard_block_reason: str | None = None
    manual_review = grade == "Manual Review"
    action = "Maintain"
    trigger = "evidence confidence threshold"

    if candidate.is_excluded or _is_conservative(candidate):
        hard_block_reason = candidate.exclusion_reason or "conservative_or_excluded_asset"
        grade = "Block"
        action = "Block"
        trigger = hard_block_reason
    elif metrics.max_drawdown is not None and metrics.max_drawdown >= settings.max_drawdown_block:
        hard_block_reason = f"max_drawdown {metrics.max_drawdown:.2%} >= {settings.max_drawdown_block:.2%}"
        grade = "Block"
        action = "Clear"
        trigger = hard_block_reason
        manual_review = True
    elif metrics.recovery_time_days is not None and metrics.recovery_time_days >= settings.recovery_time_block_days:
        hard_block_reason = (
            f"recovery_time_days {metrics.recovery_time_days} >= {settings.recovery_time_block_days}"
        )
        grade = "Block" if return_score < 7.5 or missing else "Manual Review"
        action = "Manual Review"
        trigger = hard_block_reason
        manual_review = True
    elif "nav_history_24m" in missing:
        hard_block_reason = (
            f"nav_history_span_days {metrics.history_span_days or 0} "
            f"< {settings.min_candidate_nav_history_span_days}"
        )
        grade = "Block"
        action = "Block"
        trigger = (
            f"candidate NAV history < {settings.min_candidate_nav_history_months} months; "
            "not eligible for screening/action-ready pool"
        )
        manual_review = True
    elif stale_days > 2:
        grade = "Manual Review"
        action = "Manual Review"
        trigger = f"missing NAV/holding days {stale_days} > 2"
        manual_review = True
    elif candidate.conflict_flag:
        grade = "Manual Review"
        action = "Manual Review"
        trigger = "source conflict"
        manual_review = True
    elif candidate.official_source_count < settings.min_official_sources_action_ready:
        if grade == "Action-Ready":
            grade = "Watch"
        action = "Pause New"
        trigger = "official source count below Action-Ready threshold"
        manual_review = True
    elif candidate.fallback_aggregated or (rule and rule.fallback_aggregated):
        if grade == "Action-Ready":
            grade = "Watch"
        action = "Pause New"
        trigger = "aggregated fallback caps grade"
    elif execution_constraint == "limited":
        if grade == "Action-Ready":
            grade = "Watch"
        action = "Pause New"
        trigger = "申购或赎回存在限额/受限约束；费用与赎回规则已记录，新增前需确认支付宝或官方交易额度"
    elif executable_score == 0.0:
        if grade == "Action-Ready":
            grade = "Watch"
        action = "Pause New"
        if execution_constraint == "missing":
            trigger = "fee/redemption/subscription status missing or closed"
        else:
            trigger = "申购或赎回状态关闭/未知；暂停新增并等待平台状态恢复"
        manual_review = True
    elif missing:
        if grade == "Action-Ready":
            grade = "Watch"
        action = "Maintain"
        trigger = f"required data missing: {', '.join(sorted(set(missing)))}"
    elif return_score == 0.0:
        action = "Reduce"
        trigger = "underperformed Shanghai Composite and S&P 500 across windows"
    elif grade == "Action-Ready":
        action = "Increase"
        trigger = "serenity judgment supported by evidence confidence"
    elif grade == "Watch":
        action = "Maintain"
        trigger = "evidence confidence watch band"

    evidence_coverage = min(1.0, candidate.official_source_count / settings.min_official_sources_action_ready)
    if candidate.fallback_aggregated:
        evidence_coverage = min(evidence_coverage, 0.5)

    return ScoreResult(
        total_score=round(total, 4),
        data_score=round(data_score, 4),
        timeliness_score=round(timeliness_score, 4),
        source_score=round(source_score, 4),
        return_score=round(return_score, 4),
        risk_score=round(risk_score, 4),
        executable_score=round(executable_score, 4),
        evidence_coverage=round(evidence_coverage, 4),
        grade=grade,
        hard_block_reason=hard_block_reason,
        action_label=action,
        trigger_reason=trigger,
        manual_review_required=manual_review,
        missing_fields=tuple(sorted(set(missing))),
    )
