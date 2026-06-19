from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class Candidate:
    asset_id: str
    asset_code: str
    asset_name: str
    asset_type: str
    market: str
    fund_company: str
    risk_level: str
    theme: str
    is_off_platform_fund: bool
    is_excluded: bool
    exclusion_reason: str
    official_source_count: int
    fallback_aggregated: bool
    evidence_level: str
    source_name: str
    source_type: str
    source_url: str
    missing_nav_days: int
    missing_holding_days: int
    conflict_flag: bool
    as_of: str


@dataclass(frozen=True)
class FundRule:
    asset_code: str
    subscription_status: str
    redemption_status: str
    cutoff_time: str
    confirm_lag: str
    redeem_lag: str
    subscription_fee: float | None
    redemption_fee: float | None
    management_fee: float | None
    custody_fee: float | None
    sales_service_fee: float | None
    min_purchase_amount: float | None
    source_name: str
    source_type: str
    source_priority: int
    url_or_path: str
    evidence_level: str
    fallback_aggregated: bool
    as_of: str
    subscription_fee_schedule: str = ""
    redemption_fee_schedule: str = ""
    fee_schedule_as_of: str = ""
    fee_schedule_note: str = ""
    alipay_trade_status: str = ""
    moomoo_trade_status: str = ""
    platform_trade_note: str = ""


@dataclass(frozen=True)
class PricePoint:
    asset_code: str
    date: date
    close: float


def _bool(raw: str) -> bool:
    return (raw or "").strip().lower() in {"1", "true", "yes", "y"}


def _float_or_none(raw: str) -> float | None:
    value = (raw or "").strip()
    return float(value) if value else None


def load_candidates(path: Path) -> list[Candidate]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    candidates: list[Candidate] = []
    for row in rows:
        asset_code = row["asset_code"].strip()
        candidates.append(
            Candidate(
                asset_id=asset_code,
                asset_code=asset_code,
                asset_name=row["asset_name"].strip(),
                asset_type=row["asset_type"].strip(),
                market=row.get("market", "").strip(),
                fund_company=row.get("fund_company", "").strip(),
                risk_level=row.get("risk_level", "").strip(),
                theme=row.get("theme", "").strip(),
                is_off_platform_fund=_bool(row.get("is_off_platform_fund", "true")),
                is_excluded=_bool(row.get("is_excluded", "false")),
                exclusion_reason=row.get("exclusion_reason", "").strip(),
                official_source_count=int(row.get("official_source_count", "0") or 0),
                fallback_aggregated=_bool(row.get("fallback_aggregated", "false")),
                evidence_level=row.get("evidence_level", "Needs checking").strip(),
                source_name=row.get("source_name", "").strip(),
                source_type=row.get("source_type", "").strip(),
                source_url=row.get("source_url", "").strip(),
                missing_nav_days=int(row.get("missing_nav_days", "0") or 0),
                missing_holding_days=int(row.get("missing_holding_days", "0") or 0),
                conflict_flag=_bool(row.get("conflict_flag", "false")),
                as_of=row.get("as_of", "").strip(),
            )
        )
    return candidates


def load_fund_rules(path: Path) -> dict[str, FundRule]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    rules: dict[str, FundRule] = {}
    for row in rows:
        asset_code = row["asset_code"].strip()
        rules[asset_code] = FundRule(
            asset_code=asset_code,
            subscription_status=row.get("subscription_status", "").strip(),
            redemption_status=row.get("redemption_status", "").strip(),
            cutoff_time=row.get("cutoff_time", "").strip(),
            confirm_lag=row.get("confirm_lag", "").strip(),
            redeem_lag=row.get("redeem_lag", "").strip(),
            subscription_fee=_float_or_none(row.get("subscription_fee", "")),
            redemption_fee=_float_or_none(row.get("redemption_fee", "")),
            management_fee=_float_or_none(row.get("management_fee", "")),
            custody_fee=_float_or_none(row.get("custody_fee", "")),
            sales_service_fee=_float_or_none(row.get("sales_service_fee", "")),
            min_purchase_amount=_float_or_none(row.get("min_purchase_amount", "")),
            source_name=row.get("source_name", "").strip(),
            source_type=row.get("source_type", "").strip(),
            source_priority=int(row.get("source_priority", "99") or 99),
            url_or_path=row.get("url_or_path", "").strip(),
            evidence_level=row.get("evidence_level", "Needs checking").strip(),
            fallback_aggregated=_bool(row.get("fallback_aggregated", "false")),
            as_of=row.get("as_of", "").strip(),
            subscription_fee_schedule=row.get("subscription_fee_schedule", "").strip(),
            redemption_fee_schedule=row.get("redemption_fee_schedule", "").strip(),
            fee_schedule_as_of=row.get("fee_schedule_as_of", "").strip(),
            fee_schedule_note=row.get("fee_schedule_note", "").strip(),
            alipay_trade_status=row.get("alipay_trade_status", "").strip(),
            moomoo_trade_status=row.get("moomoo_trade_status", "").strip(),
            platform_trade_note=row.get("platform_trade_note", "").strip(),
        )
    return rules


def load_price_history(path: Path) -> dict[str, list[PricePoint]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    history: dict[str, list[PricePoint]] = {}
    for row in rows:
        point = PricePoint(
            asset_code=row["asset_code"].strip(),
            date=date.fromisoformat(row["date"].strip()),
            close=float(row["close"]),
        )
        history.setdefault(point.asset_code, []).append(point)
    for asset_code in history:
        history[asset_code].sort(key=lambda point: point.date)
    return history
