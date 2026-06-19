from __future__ import annotations

import csv
import json
from dataclasses import asdict
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from app.adapters.manual_sources import Candidate, FundRule, PricePoint
from app.config import Settings
from app.core.metrics import WINDOWS, calculate_metrics
from app.core.scoring import score_candidate


def _now(settings: Settings) -> str:
    return datetime.now(ZoneInfo(settings.timezone_primary)).isoformat(timespec="seconds")


def _candidate(asset_code: str) -> Candidate:
    return Candidate(
        asset_id=asset_code,
        asset_code=asset_code,
        asset_name=f"{asset_code} synthetic aggressive regression fund",
        asset_type="off_platform_fund",
        market="CN/US",
        fund_company="Synthetic Regression",
        risk_level="high",
        theme="risk gate regression",
        is_off_platform_fund=True,
        is_excluded=False,
        exclusion_reason="",
        official_source_count=2,
        fallback_aggregated=False,
        evidence_level="Regression",
        source_name="synthetic regression fixture",
        source_type="test_fixture",
        source_url="outputs/tests/risk_gate_regression_latest.json",
        missing_nav_days=0,
        missing_holding_days=0,
        conflict_flag=False,
        as_of="2026-06-12",
    )


def _rule(asset_code: str) -> FundRule:
    return FundRule(
        asset_code=asset_code,
        subscription_status="open",
        redemption_status="open",
        cutoff_time="15:00",
        confirm_lag="T+1",
        redeem_lag="T+3",
        subscription_fee=0.001,
        redemption_fee=0.005,
        management_fee=0.012,
        custody_fee=0.002,
        sales_service_fee=0.0,
        min_purchase_amount=10.0,
        source_name="synthetic regression fixture",
        source_type="test_fixture",
        source_priority=0,
        url_or_path="outputs/tests/risk_gate_regression_latest.json",
        evidence_level="Regression",
        fallback_aggregated=False,
        as_of="2026-06-12",
        subscription_fee_schedule="M<100万元 0.10%",
        redemption_fee_schedule="N<7天 0.50%；N>=7天 0.00%",
        fee_schedule_as_of="2026-06-12",
        fee_schedule_note="synthetic regression fixture",
    )


def _benchmark_returns() -> dict[str, float | None]:
    return {window: 0.0 for window in WINDOWS}


def _mdd_points(asset_code: str) -> list[PricePoint]:
    start = date(2026, 1, 1)
    points: list[PricePoint] = []
    for offset in range(120):
        if offset <= 20:
            close = 100.0 + offset
        elif offset <= 70:
            close = 120.0 - ((offset - 20) * 1.1)
        else:
            close = 65.0 + ((offset - 70) * 0.15)
        points.append(PricePoint(asset_code, start + timedelta(days=offset), round(close, 4)))
    return points


def _recovery_points(asset_code: str) -> list[PricePoint]:
    start = date(2025, 1, 1)
    points: list[PricePoint] = []
    for offset in range(381):
        if offset <= 10:
            close = 100.0 - (offset * 2.0)
        elif offset < 375:
            close = 80.0 + (19.5 * ((offset - 10) / 364.0))
        else:
            close = 100.0 + ((offset - 375) * 0.02)
        points.append(PricePoint(asset_code, start + timedelta(days=offset), round(close, 4)))
    return points


def _case(
    *,
    settings: Settings,
    case_id: str,
    requirement: str,
    points: list[PricePoint],
) -> dict[str, object]:
    candidate = _candidate(points[0].asset_code)
    rule = _rule(points[0].asset_code)
    metrics = calculate_metrics(points)
    score = score_candidate(candidate, rule, metrics, _benchmark_returns(), _benchmark_returns(), settings)
    hard_block_reason = score.hard_block_reason or ""
    if case_id == "max_drawdown_block":
        passed = (
            metrics.max_drawdown is not None
            and metrics.max_drawdown >= settings.max_drawdown_block
            and score.grade == "Block"
            and score.action_label == "Clear"
            and score.manual_review_required
            and "max_drawdown" in hard_block_reason
        )
    elif case_id == "recovery_time_block":
        passed = (
            metrics.recovery_time_days is not None
            and metrics.recovery_time_days >= settings.recovery_time_block_days
            and score.grade in {"Block", "Manual Review"}
            and score.action_label == "Manual Review"
            and score.manual_review_required
            and "recovery_time_days" in hard_block_reason
        )
    else:
        passed = False

    return {
        "case_id": case_id,
        "requirement": requirement,
        "status": "pass" if passed else "fail",
        "points": len(points),
        "metrics": asdict(metrics),
        "score": asdict(score),
    }


def _write_markdown(path: Path, result: dict[str, object]) -> None:
    lines = [
        "# Risk Gate Regression",
        "",
        f"- Generated at: {result['generated_at']}",
        f"- Status: {result['status']}",
        f"- Max drawdown block: {result['thresholds']['max_drawdown_block']:.2%}",
        f"- Recovery time block days: {result['thresholds']['recovery_time_block_days']}",
        "",
        "## Cases",
        "",
        "| Case | Status | MDD | Recovery days | Grade | Action | Reason |",
        "|---|---|---:|---:|---|---|---|",
    ]
    for case in result["cases"]:
        metrics = case["metrics"]
        score = case["score"]
        mdd = metrics.get("max_drawdown")
        mdd_text = f"{mdd:.2%}" if isinstance(mdd, float) else ""
        recovery = metrics.get("recovery_time_days")
        lines.append(
            "| {case_id} | {status} | {mdd} | {recovery} | {grade} | {action} | {reason} |".format(
                case_id=case["case_id"],
                status=case["status"],
                mdd=mdd_text,
                recovery="" if recovery is None else recovery,
                grade=score.get("grade", ""),
                action=score.get("action_label", ""),
                reason=str(score.get("hard_block_reason") or "").replace("|", "/"),
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_csv(path: Path, result: dict[str, object]) -> None:
    fieldnames = [
        "case_id",
        "status",
        "max_drawdown",
        "recovery_time_days",
        "grade",
        "action_label",
        "manual_review_required",
        "hard_block_reason",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for case in result["cases"]:
            metrics = case["metrics"]
            score = case["score"]
            writer.writerow(
                {
                    "case_id": case["case_id"],
                    "status": case["status"],
                    "max_drawdown": metrics.get("max_drawdown"),
                    "recovery_time_days": metrics.get("recovery_time_days"),
                    "grade": score.get("grade"),
                    "action_label": score.get("action_label"),
                    "manual_review_required": score.get("manual_review_required"),
                    "hard_block_reason": score.get("hard_block_reason"),
                }
            )


def run_risk_gate_regression(settings: Settings, *, write_output: bool = True) -> dict[str, object]:
    settings.ensure_dirs()
    cases = [
        _case(
            settings=settings,
            case_id="max_drawdown_block",
            requirement="MDD >= max_drawdown_block must create Block/Clear/manual-review evidence.",
            points=_mdd_points("RISK_MDD"),
        ),
        _case(
            settings=settings,
            case_id="recovery_time_block",
            requirement="Recovery time >= recovery_time_block_days must create Block or Manual Review evidence.",
            points=_recovery_points("RISK_RECOVERY"),
        ),
    ]
    result: dict[str, object] = {
        "generated_at": _now(settings),
        "status": "pass" if all(case["status"] == "pass" for case in cases) else "fail",
        "thresholds": {
            "max_drawdown_block": settings.max_drawdown_block,
            "recovery_time_block_days": settings.recovery_time_block_days,
        },
        "cases": cases,
    }
    if write_output:
        output_dir = settings.root_dir / "outputs" / "tests"
        output_dir.mkdir(parents=True, exist_ok=True)
        json_path = output_dir / "risk_gate_regression_latest.json"
        md_path = output_dir / "risk_gate_regression_latest.md"
        csv_path = output_dir / "risk_gate_regression_latest.csv"
        json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        _write_markdown(md_path, result)
        _write_csv(csv_path, result)
        result["json_path"] = str(json_path)
        result["markdown_path"] = str(md_path)
        result["csv_path"] = str(csv_path)
    return result
