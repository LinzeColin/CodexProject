from __future__ import annotations

from dataclasses import dataclass

from app.adapters.manual_sources import Candidate, FundRule
from app.config import Settings
from app.core.metrics import AssetMetrics, WINDOWS


CONSERVATIVE_KEYWORDS = ("bond", "money", "cash", "yuebao", "conservative", "fixed income")


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


def score_candidate(
    candidate: Candidate,
    rule: FundRule | None,
    metrics: AssetMetrics,
    shanghai_returns: dict[str, float | None],
    sp500_returns: dict[str, float | None],
    settings: Settings,
) -> ScoreResult:
    missing: list[str] = []
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

    data_score = max(0.0, 25.0 - (8.0 * len(missing)))

    stale_days = max(candidate.missing_nav_days, candidate.missing_holding_days)
    timeliness_score = 15.0 if stale_days <= 2 else 0.0

    if candidate.official_source_count >= settings.min_official_sources_action_ready and not candidate.conflict_flag:
        source_score = 15.0
    elif candidate.official_source_count >= 1 and not candidate.conflict_flag:
        source_score = 7.5
    else:
        source_score = 0.0

    wins = _benchmark_win_count(metrics, shanghai_returns, sp500_returns)
    return_score = 15.0 * (wins / 6.0)

    risk_score = 0.0
    if metrics.max_drawdown is not None:
        if metrics.max_drawdown < settings.max_drawdown_block:
            risk_score = max(0.0, 20.0 - (metrics.max_drawdown * 20.0))
    if metrics.recovery_time_days is not None and metrics.recovery_time_days >= settings.recovery_time_block_days:
        risk_score = min(risk_score, 5.0)

    executable_score = 10.0
    if rule is None:
        executable_score = 0.0
    elif (
        rule.subscription_status.lower() != "open"
        or rule.redemption_status.lower() != "open"
        or "redemption_status" in missing
        or "subscription_fee" in missing
        or "redemption_fee" in missing
        or "subscription_fee_schedule" in missing
        or "redemption_fee_schedule" in missing
    ):
        executable_score = 0.0

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
    elif executable_score == 0.0:
        if grade == "Action-Ready":
            grade = "Watch"
        action = "Pause New"
        trigger = "fee/redemption/subscription status missing or closed"
        manual_review = True
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
