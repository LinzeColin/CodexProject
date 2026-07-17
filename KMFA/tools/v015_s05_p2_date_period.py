#!/usr/bin/env python3
"""Deterministic date, timezone, period, and attribution kernel for S05-P2.

The kernel requires explicit timezone and rule identities.  It does not inspect
raw business files, infer ambiguous dates, or silently merge overlapping
periods.  Business-sensitive late-arrival cases degrade to manual confirmation.
"""

from __future__ import annotations

import calendar
import re
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable, Mapping, Optional, Sequence
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


RUN_PHASE_ID = "V015_S05_P2_DATE_PERIOD"
TASK_ID = "KMFA-V015-S05-P2-DATE-PERIOD-20260714"
ACCEPTANCE_ID = "ACC-KMFA-V015-S05-P2-DATE-PERIOD"
VERSION = "1.5.0-dev-s05p2"

QUALITY_QUEUE = "QUALITY_QUEUE"
MANUAL_CONFIRMATION = "MANUAL_CONFIRMATION"
BLOCK_CALCULATION = "BLOCK_CALCULATION"

DATE_SOURCE_KINDS = ("DATE", "TEXT_DATE", "DATETIME", "EXCEL_1900", "EXCEL_1904")
PERIOD_TYPES = ("WEEK", "MONTH", "QUARTER", "HALF_YEAR", "YEAR", "CUSTOM")
ATTRIBUTION_DOMAINS = ("CONTRACT", "COST", "INVOICE", "COLLECTION", "TAX")


class DatePeriodError(ValueError):
    """Stable fail-closed error carrying a machine action."""

    def __init__(self, code: str, message: str, action: str = BLOCK_CALCULATION) -> None:
        super().__init__(message)
        self.code = code
        self.action = action


def _zone(name: Optional[str], field: str) -> ZoneInfo:
    if not isinstance(name, str) or not name.strip():
        raise DatePeriodError("TIMEZONE_REQUIRED", f"{field} is required", MANUAL_CONFIRMATION)
    try:
        return ZoneInfo(name.strip())
    except ZoneInfoNotFoundError as error:
        raise DatePeriodError("TIMEZONE_INVALID", f"{field} is not registered", QUALITY_QUEUE) from error


def _strict_date(value: Any, field: str = "date") -> date:
    if isinstance(value, datetime):
        raise DatePeriodError("DATE_TYPE_INVALID", f"{field} must be a date without time", QUALITY_QUEUE)
    if isinstance(value, date):
        return value
    if not isinstance(value, str) or not value.strip():
        raise DatePeriodError("DATE_MISSING", f"{field} is required", QUALITY_QUEUE)
    text = value.strip()
    patterns = (
        (r"(\d{4})-(\d{1,2})-(\d{1,2})", "ISO_DASH"),
        (r"(\d{4})/(\d{1,2})/(\d{1,2})", "ISO_SLASH"),
        (r"(\d{4})年(\d{1,2})月(\d{1,2})日", "ZH_DATE"),
        (r"(\d{4})(\d{2})(\d{2})", "COMPACT"),
    )
    for pattern, _ in patterns:
        match = re.fullmatch(pattern, text)
        if match:
            try:
                return date(*(int(part) for part in match.groups()))
            except ValueError as error:
                raise DatePeriodError("DATE_INVALID", f"{field} is invalid", QUALITY_QUEUE) from error
    raise DatePeriodError("DATE_FORMAT_AMBIGUOUS", f"{field} format is not registered", QUALITY_QUEUE)


def _parse_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str) or not value.strip():
        raise DatePeriodError("DATETIME_MISSING", "datetime is required", QUALITY_QUEUE)
    try:
        return datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError as error:
        raise DatePeriodError("DATETIME_INVALID", "datetime must use ISO-8601", QUALITY_QUEUE) from error


def _localize_strict(value: datetime, zone: ZoneInfo) -> datetime:
    if value.tzinfo is not None:
        return value
    candidates = []
    for fold in (0, 1):
        candidate = value.replace(tzinfo=zone, fold=fold)
        roundtrip = candidate.astimezone(timezone.utc).astimezone(zone).replace(tzinfo=None)
        if roundtrip == value:
            candidates.append(candidate)
    if not candidates:
        raise DatePeriodError("LOCAL_TIME_NONEXISTENT", "local datetime falls in a DST gap", QUALITY_QUEUE)
    offsets = {candidate.utcoffset() for candidate in candidates}
    if len(offsets) > 1:
        raise DatePeriodError("LOCAL_TIME_AMBIGUOUS", "local datetime falls in a DST fold", MANUAL_CONFIRMATION)
    return candidates[0]


def _decimal_serial(value: Any) -> Decimal:
    if isinstance(value, bool) or isinstance(value, float):
        raise DatePeriodError("EXCEL_SERIAL_TYPE_INVALID", "Excel serial must be integer, Decimal, or decimal text", QUALITY_QUEUE)
    try:
        serial = Decimal(str(value))
    except (InvalidOperation, ValueError) as error:
        raise DatePeriodError("EXCEL_SERIAL_INVALID", "Excel serial is invalid", QUALITY_QUEUE) from error
    if not serial.is_finite():
        raise DatePeriodError("EXCEL_SERIAL_INVALID", "Excel serial must be finite", QUALITY_QUEUE)
    return serial


def _excel_datetime(value: Any, system: str, source_timezone: Optional[str]) -> tuple[date, Optional[datetime]]:
    serial = _decimal_serial(value)
    whole = int(serial // 1)
    fraction = serial - Decimal(whole)
    if serial < 0 or (system == "EXCEL_1900" and whole < 1):
        raise DatePeriodError("EXCEL_SERIAL_OUT_OF_RANGE", "Excel serial is outside the registered range", QUALITY_QUEUE)
    if system == "EXCEL_1900" and whole == 60:
        raise DatePeriodError("EXCEL_1900_FICTIONAL_LEAP_DAY", "Excel serial 60 has no Gregorian date", QUALITY_QUEUE)
    if system == "EXCEL_1900":
        base = date(1899, 12, 31) if whole < 60 else date(1899, 12, 30)
    else:
        base = date(1904, 1, 1)
    result_date = base + timedelta(days=whole)
    if fraction == 0:
        return result_date, None
    micros = fraction * Decimal(86400 * 1_000_000)
    if micros != micros.to_integral_value():
        raise DatePeriodError("EXCEL_TIME_PRECISION_INVALID", "Excel time is not exact to a microsecond", QUALITY_QUEUE)
    source_zone = _zone(source_timezone, "source_timezone")
    naive = datetime.combine(result_date, time()) + timedelta(microseconds=int(micros))
    return result_date, _localize_strict(naive, source_zone)


@dataclass(frozen=True)
class NormalizedBusinessDate:
    canonical_date: date
    business_timezone: str
    source_kind: str
    instant_utc: Optional[datetime]

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "business_date": self.canonical_date.isoformat(),
            "business_timezone": self.business_timezone,
            "source_kind": self.source_kind,
            "instant_utc": self.instant_utc.isoformat().replace("+00:00", "Z") if self.instant_utc else None,
        }


def normalize_business_date(
    value: Any,
    *,
    source_kind: str,
    business_timezone: str,
    source_timezone: Optional[str] = None,
) -> NormalizedBusinessDate:
    """Normalize one explicitly typed source value to a business date."""

    business_zone = _zone(business_timezone, "business_timezone")
    if source_kind not in DATE_SOURCE_KINDS:
        raise DatePeriodError("DATE_SOURCE_KIND_INVALID", "source_kind is not registered", MANUAL_CONFIRMATION)
    instant: Optional[datetime] = None
    if source_kind == "DATE":
        canonical = _strict_date(value)
    elif source_kind == "TEXT_DATE":
        canonical = _strict_date(value)
    elif source_kind == "DATETIME":
        parsed = _parse_datetime(value)
        if parsed.tzinfo is None:
            parsed = _localize_strict(parsed, _zone(source_timezone, "source_timezone"))
        instant = parsed.astimezone(timezone.utc)
        canonical = instant.astimezone(business_zone).date()
    else:
        excel_date, parsed = _excel_datetime(value, source_kind, source_timezone)
        if parsed is None:
            canonical = excel_date
        else:
            instant = parsed.astimezone(timezone.utc)
            canonical = instant.astimezone(business_zone).date()
    return NormalizedBusinessDate(canonical, business_zone.key, source_kind, instant)


def _month_end(year: int, month: int) -> date:
    return date(year, month, calendar.monthrange(year, month)[1])


@dataclass(frozen=True)
class BusinessPeriod:
    period_id: str
    period_type: str
    start_date: date
    end_date: date
    cutoff_date: date
    calendar_id: str
    version: str
    closed_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        if self.period_type not in PERIOD_TYPES:
            raise DatePeriodError("PERIOD_TYPE_INVALID", "period_type is not registered")
        if self.end_date < self.start_date:
            raise DatePeriodError("PERIOD_RANGE_INVALID", "period end precedes period start")
        if not self.start_date <= self.cutoff_date <= self.end_date:
            raise DatePeriodError("PERIOD_CUTOFF_INVALID", "cutoff must fall inside the period")
        if not self.period_id or not self.calendar_id or not self.version:
            raise DatePeriodError("PERIOD_IDENTITY_MISSING", "period identity fields are required")
        if self.closed_at is not None and self.closed_at.tzinfo is None:
            raise DatePeriodError("PERIOD_CLOSE_TIMEZONE_REQUIRED", "closed_at must be timezone-aware")

    def contains(self, value: date) -> bool:
        return self.start_date <= value <= self.end_date

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "period_id": self.period_id,
            "period_type": self.period_type,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "cutoff_date": self.cutoff_date.isoformat(),
            "calendar_id": self.calendar_id,
            "version": self.version,
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
        }


def build_period(
    period_type: str,
    *,
    anchor: Any,
    calendar_id: str = "STANDARD_CALENDAR",
    version: str = "1.0.0",
    custom_id: Optional[str] = None,
    custom_start: Any = None,
    custom_end: Any = None,
    cutoff_date: Any = None,
    closed_at: Optional[datetime] = None,
) -> BusinessPeriod:
    anchor_date = _strict_date(anchor, "anchor")
    if period_type == "WEEK":
        start = anchor_date - timedelta(days=anchor_date.weekday())
        end = start + timedelta(days=6)
        iso_year, iso_week, _ = anchor_date.isocalendar()
        period_id = f"{iso_year:04d}-W{iso_week:02d}"
    elif period_type == "MONTH":
        start = date(anchor_date.year, anchor_date.month, 1)
        end = _month_end(anchor_date.year, anchor_date.month)
        period_id = f"{anchor_date.year:04d}-{anchor_date.month:02d}"
    elif period_type == "QUARTER":
        quarter = ((anchor_date.month - 1) // 3) + 1
        start_month = (quarter - 1) * 3 + 1
        start = date(anchor_date.year, start_month, 1)
        end = _month_end(anchor_date.year, start_month + 2)
        period_id = f"{anchor_date.year:04d}-Q{quarter}"
    elif period_type == "HALF_YEAR":
        half = 1 if anchor_date.month <= 6 else 2
        start_month = 1 if half == 1 else 7
        start = date(anchor_date.year, start_month, 1)
        end = _month_end(anchor_date.year, start_month + 5)
        period_id = f"{anchor_date.year:04d}-H{half}"
    elif period_type == "YEAR":
        start = date(anchor_date.year, 1, 1)
        end = date(anchor_date.year, 12, 31)
        period_id = f"{anchor_date.year:04d}"
    elif period_type == "CUSTOM":
        if not custom_id:
            raise DatePeriodError("CUSTOM_PERIOD_ID_REQUIRED", "custom_id is required", MANUAL_CONFIRMATION)
        start = _strict_date(custom_start, "custom_start")
        end = _strict_date(custom_end, "custom_end")
        period_id = custom_id
    else:
        raise DatePeriodError("PERIOD_TYPE_INVALID", "period_type is not registered", MANUAL_CONFIRMATION)
    cutoff = _strict_date(cutoff_date, "cutoff_date") if cutoff_date is not None else end
    return BusinessPeriod(period_id, period_type, start, end, cutoff, calendar_id, version, closed_at)


class PeriodDimension:
    """Period registry that rejects duplicate and overlapping rows."""

    def __init__(self, periods: Iterable[BusinessPeriod] = ()) -> None:
        self._periods: list[BusinessPeriod] = []
        for period in periods:
            self.add(period)

    @property
    def periods(self) -> tuple[BusinessPeriod, ...]:
        return tuple(self._periods)

    def add(self, period: BusinessPeriod) -> None:
        for current in self._periods:
            if (
                current.calendar_id != period.calendar_id
                or current.version != period.version
                or current.period_type != period.period_type
            ):
                continue
            if current.period_id == period.period_id:
                raise DatePeriodError("PERIOD_DUPLICATE", "duplicate period must not be silently merged")
            if max(current.start_date, period.start_date) <= min(current.end_date, period.end_date):
                raise DatePeriodError("PERIOD_OVERLAP", "overlapping periods must not be silently merged")
        self._periods.append(period)
        self._periods.sort(key=lambda row: (row.start_date, row.period_id))

    def matching(self, value: date) -> tuple[BusinessPeriod, ...]:
        return tuple(period for period in self._periods if period.contains(value))


def freshness_days(*, as_of_date: Any, latest_data_date: Any) -> int:
    as_of = _strict_date(as_of_date, "as_of_date")
    latest = _strict_date(latest_data_date, "latest_data_date")
    if latest > as_of:
        raise DatePeriodError("FRESHNESS_DATE_IN_FUTURE", "latest data date exceeds as-of date", QUALITY_QUEUE)
    return (as_of - latest).days


@dataclass(frozen=True)
class AttributionRule:
    rule_id: str
    version: str
    domain: str
    basis_date_field: str
    period_type: str
    calendar_id: str
    period_version: str
    late_event_policy: str
    effective_from: date
    human_readable_rule: str

    def __post_init__(self) -> None:
        if self.domain not in ATTRIBUTION_DOMAINS:
            raise DatePeriodError("ATTRIBUTION_DOMAIN_INVALID", "attribution domain is not registered")
        if self.period_type not in PERIOD_TYPES:
            raise DatePeriodError("ATTRIBUTION_PERIOD_TYPE_INVALID", "attribution period type is not registered")
        if not self.calendar_id or not self.period_version:
            raise DatePeriodError("ATTRIBUTION_PERIOD_IDENTITY_MISSING", "attribution calendar and period version are required")
        if self.late_event_policy not in {"MANUAL_CONFIRMATION", "RETAIN_SOURCE_PERIOD", "NEXT_OPEN_PERIOD"}:
            raise DatePeriodError("LATE_EVENT_POLICY_INVALID", "late event policy is not registered")


def _rule(rule_id: str, domain: str, field: str, description: str) -> AttributionRule:
    return AttributionRule(
        rule_id=rule_id,
        version="1.0.0",
        domain=domain,
        basis_date_field=field,
        period_type="MONTH",
        calendar_id="STANDARD_CALENDAR",
        period_version="1.0.0",
        late_event_policy="MANUAL_CONFIRMATION",
        effective_from=date(2026, 1, 1),
        human_readable_rule=description,
    )


ATTRIBUTION_RULES = {
    (row.rule_id, row.version): row
    for row in (
        _rule("CONTRACT_SIGNED_DATE", "CONTRACT", "signed_date", "合同按已确认签署日归属；跨已关闭期间进入人工确认。"),
        _rule("COST_INCURRED_DATE", "COST", "incurred_date", "成本按已确认发生日归属；跨已关闭期间进入人工确认。"),
        _rule("INVOICE_ISSUE_DATE", "INVOICE", "invoice_date", "开票按已确认发票日期归属；跨已关闭期间进入人工确认。"),
        _rule("COLLECTION_RECEIPT_DATE", "COLLECTION", "receipt_date", "回款按已确认到账日归属；跨已关闭期间进入人工确认。"),
        _rule("TAX_POINT_DATE", "TAX", "tax_point_date", "税务按已确认纳税义务发生日归属；政策未确认或跨已关闭期间进入人工确认。"),
    )
}


@dataclass(frozen=True)
class AttributionResult:
    status: str
    domain: str
    rule_id: str
    rule_version: str
    source_date: date
    period_id: Optional[str]
    report_degraded: bool
    action: Optional[str]

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "domain": self.domain,
            "rule_id": self.rule_id,
            "rule_version": self.rule_version,
            "source_date": self.source_date.isoformat(),
            "period_id": self.period_id,
            "report_degraded": self.report_degraded,
            "action": self.action,
        }


def assign_period(
    event: Mapping[str, Any],
    periods: Sequence[BusinessPeriod],
    *,
    rule_id: str,
    rule_version: str,
    recorded_at: Optional[datetime] = None,
) -> AttributionResult:
    rule = ATTRIBUTION_RULES.get((rule_id, rule_version))
    if rule is None:
        raise DatePeriodError("ATTRIBUTION_RULE_UNREGISTERED", "rule id/version requires confirmation", MANUAL_CONFIRMATION)
    if rule.basis_date_field not in event:
        raise DatePeriodError("ATTRIBUTION_DATE_MISSING", "rule basis date is missing", QUALITY_QUEUE)
    source_date = _strict_date(event[rule.basis_date_field], rule.basis_date_field)
    if source_date < rule.effective_from:
        raise DatePeriodError("ATTRIBUTION_RULE_NOT_EFFECTIVE", "rule is not effective for source date", MANUAL_CONFIRMATION)
    matches = [
        period for period in periods
        if period.period_type == rule.period_type
        and period.calendar_id == rule.calendar_id
        and period.version == rule.period_version
        and period.contains(source_date)
    ]
    if not matches:
        raise DatePeriodError("ATTRIBUTION_PERIOD_MISSING", "no period contains the basis date", QUALITY_QUEUE)
    if len(matches) != 1:
        raise DatePeriodError("ATTRIBUTION_PERIOD_AMBIGUOUS", "more than one period contains the basis date", MANUAL_CONFIRMATION)
    matched = matches[0]
    if recorded_at is not None:
        if recorded_at.tzinfo is None:
            raise DatePeriodError("RECORDED_AT_TIMEZONE_REQUIRED", "recorded_at must be timezone-aware", QUALITY_QUEUE)
        if matched.closed_at is not None and recorded_at > matched.closed_at:
            if rule.late_event_policy == "MANUAL_CONFIRMATION":
                return AttributionResult(
                    "DEGRADED_MANUAL_CONFIRMATION", rule.domain, rule.rule_id, rule.version,
                    source_date, None, True, MANUAL_CONFIRMATION,
                )
            if rule.late_event_policy == "RETAIN_SOURCE_PERIOD":
                return AttributionResult(
                    "ASSIGNED_LATE_RETAINED", rule.domain, rule.rule_id, rule.version,
                    source_date, matched.period_id, False, None,
                )
            later = sorted(
                (period for period in periods if period.start_date > matched.end_date and period.closed_at is None),
                key=lambda period: period.start_date,
            )
            if not later:
                raise DatePeriodError("NEXT_OPEN_PERIOD_MISSING", "late event has no open target period", MANUAL_CONFIRMATION)
            matched = later[0]
    return AttributionResult(
        "ASSIGNED", rule.domain, rule.rule_id, rule.version,
        source_date, matched.period_id, False, None,
    )


def public_contract_summary() -> dict[str, Any]:
    return {
        "phase_id": RUN_PHASE_ID,
        "date_source_kind_count": len(DATE_SOURCE_KINDS),
        "business_timezone_required": True,
        "ambiguous_date_guessing_allowed": False,
        "excel_1900_serial_60_allowed": False,
        "period_type_count": len(PERIOD_TYPES),
        "period_overlap_merge_allowed": False,
        "period_collision_scope": "SAME_CALENDAR_VERSION_AND_PERIOD_TYPE",
        "cross_grain_period_coexistence_allowed": True,
        "attribution_domain_count": len(ATTRIBUTION_DOMAINS),
        "attribution_rule_count": len(ATTRIBUTION_RULES),
        "unregistered_rule_calculation_allowed": False,
        "late_event_default_action": MANUAL_CONFIRMATION,
        "raw_root_access_count": 0,
    }
