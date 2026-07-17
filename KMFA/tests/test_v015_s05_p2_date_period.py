from __future__ import annotations

import unittest
from datetime import date, datetime, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo

from KMFA.tools.v015_s05_p2_date_period import (
    ATTRIBUTION_RULES,
    BusinessPeriod,
    DatePeriodError,
    PeriodDimension,
    assign_period,
    build_period,
    freshness_days,
    normalize_business_date,
    public_contract_summary,
)


class V015S05P2DatePeriodTests(unittest.TestCase):
    def test_registered_text_formats_normalize_to_one_business_date(self) -> None:
        values = ("2026-07-14", "2026/7/14", "2026年7月14日", "20260714")
        actual = {
            normalize_business_date(value, source_kind="TEXT_DATE", business_timezone="Asia/Shanghai").canonical_date
            for value in values
        }
        self.assertEqual(actual, {date(2026, 7, 14)})

    def test_ambiguous_invalid_and_blank_text_dates_enter_quality_queue(self) -> None:
        for value in ("01/02/2026", "2026-02-29", ""):
            with self.subTest(value=value):
                with self.assertRaises(DatePeriodError) as context:
                    normalize_business_date(value, source_kind="TEXT_DATE", business_timezone="Asia/Shanghai")
                self.assertEqual(context.exception.action, "QUALITY_QUEUE")

    def test_excel_1900_boundary_and_fictional_day(self) -> None:
        cases = {1: date(1900, 1, 1), 59: date(1900, 2, 28), 61: date(1900, 3, 1)}
        for serial, expected in cases.items():
            with self.subTest(serial=serial):
                result = normalize_business_date(serial, source_kind="EXCEL_1900", business_timezone="Asia/Shanghai")
                self.assertEqual(result.canonical_date, expected)
        with self.assertRaises(DatePeriodError) as context:
            normalize_business_date(60, source_kind="EXCEL_1900", business_timezone="Asia/Shanghai")
        self.assertEqual(context.exception.code, "EXCEL_1900_FICTIONAL_LEAP_DAY")
        self.assertEqual(context.exception.action, "QUALITY_QUEUE")

    def test_excel_1904_and_fractional_serial_are_timezone_explicit(self) -> None:
        plain = normalize_business_date(Decimal("0"), source_kind="EXCEL_1904", business_timezone="Asia/Shanghai")
        self.assertEqual(plain.canonical_date, date(1904, 1, 1))
        fractional = normalize_business_date(
            Decimal("45291.75"),
            source_kind="EXCEL_1900",
            source_timezone="UTC",
            business_timezone="Asia/Shanghai",
        )
        self.assertEqual(fractional.canonical_date, date(2024, 1, 1))
        with self.assertRaises(DatePeriodError) as context:
            normalize_business_date(Decimal("45291.5"), source_kind="EXCEL_1900", business_timezone="Asia/Shanghai")
        self.assertEqual(context.exception.code, "TIMEZONE_REQUIRED")

    def test_same_instant_normalizes_consistently_per_explicit_business_timezone(self) -> None:
        left = normalize_business_date(
            "2026-07-14T00:30:00+08:00", source_kind="DATETIME", business_timezone="Asia/Shanghai"
        )
        right = normalize_business_date(
            "2026-07-13T16:30:00Z", source_kind="DATETIME", business_timezone="Asia/Shanghai"
        )
        self.assertEqual(left.to_public_dict(), right.to_public_dict())
        sydney = normalize_business_date(
            "2026-07-13T16:30:00Z", source_kind="DATETIME", business_timezone="Australia/Sydney"
        )
        self.assertEqual(sydney.canonical_date, date(2026, 7, 14))

    def test_timezone_must_be_registered_and_naive_datetime_needs_source_timezone(self) -> None:
        with self.assertRaises(DatePeriodError) as invalid:
            normalize_business_date("2026-07-14", source_kind="TEXT_DATE", business_timezone="Mars/Base")
        self.assertEqual(invalid.exception.action, "QUALITY_QUEUE")
        with self.assertRaises(DatePeriodError) as missing:
            normalize_business_date(datetime(2026, 7, 14, 1), source_kind="DATETIME", business_timezone="UTC")
        self.assertEqual(missing.exception.action, "MANUAL_CONFIRMATION")

    def test_dst_gap_and_fold_fail_closed(self) -> None:
        with self.assertRaises(DatePeriodError) as gap:
            normalize_business_date(
                datetime(2026, 10, 4, 2, 30), source_kind="DATETIME",
                source_timezone="Australia/Sydney", business_timezone="Australia/Sydney",
            )
        self.assertEqual(gap.exception.code, "LOCAL_TIME_NONEXISTENT")
        with self.assertRaises(DatePeriodError) as fold:
            normalize_business_date(
                datetime(2026, 4, 5, 2, 30), source_kind="DATETIME",
                source_timezone="Australia/Sydney", business_timezone="Australia/Sydney",
            )
        self.assertEqual(fold.exception.code, "LOCAL_TIME_AMBIGUOUS")
        self.assertEqual(fold.exception.action, "MANUAL_CONFIRMATION")

    def test_week_month_quarter_half_year_and_year_boundaries(self) -> None:
        cases = {
            "WEEK": ("2026-W01", date(2025, 12, 29), date(2026, 1, 4)),
            "MONTH": ("2024-02", date(2024, 2, 1), date(2024, 2, 29)),
            "QUARTER": ("2026-Q2", date(2026, 4, 1), date(2026, 6, 30)),
            "HALF_YEAR": ("2026-H2", date(2026, 7, 1), date(2026, 12, 31)),
            "YEAR": ("2026", date(2026, 1, 1), date(2026, 12, 31)),
        }
        anchors = {"WEEK": "2026-01-01", "MONTH": "2024-02-15", "QUARTER": "2026-05-01", "HALF_YEAR": "2026-07-14", "YEAR": "2026-07-14"}
        for period_type, expected in cases.items():
            with self.subTest(period_type=period_type):
                period = build_period(period_type, anchor=anchors[period_type])
                self.assertEqual((period.period_id, period.start_date, period.end_date), expected)
                self.assertEqual(period.cutoff_date, period.end_date)

    def test_custom_period_and_cutoff_are_explicit(self) -> None:
        period = build_period(
            "CUSTOM", anchor="2026-01-01", custom_id="FY26-P01",
            custom_start="2026-01-05", custom_end="2026-02-01", cutoff_date="2026-01-30",
        )
        self.assertEqual(period.to_public_dict()["period_id"], "FY26-P01")
        self.assertEqual(period.cutoff_date, date(2026, 1, 30))
        with self.assertRaises(DatePeriodError):
            build_period("CUSTOM", anchor="2026-01-01", custom_start="2026-01-01", custom_end="2026-01-31")

    def test_freshness_is_computable_and_future_data_is_rejected(self) -> None:
        self.assertEqual(freshness_days(as_of_date="2026-07-14", latest_data_date="2026-07-10"), 4)
        with self.assertRaises(DatePeriodError) as context:
            freshness_days(as_of_date="2026-07-14", latest_data_date="2026-07-15")
        self.assertEqual(context.exception.action, "QUALITY_QUEUE")

    def test_duplicate_and_overlapping_periods_never_merge_silently(self) -> None:
        january = build_period("MONTH", anchor="2026-01-15")
        dimension = PeriodDimension([january])
        with self.assertRaises(DatePeriodError) as duplicate:
            dimension.add(build_period("MONTH", anchor="2026-01-01"))
        self.assertEqual(duplicate.exception.code, "PERIOD_DUPLICATE")
        with self.assertRaises(DatePeriodError) as overlap:
            dimension.add(BusinessPeriod(
                "2026-01-OVERLAP", "MONTH", date(2026, 1, 15), date(2026, 2, 15),
                date(2026, 2, 15), "STANDARD_CALENDAR", "1.0.0",
            ))
        self.assertEqual(overlap.exception.code, "PERIOD_OVERLAP")

    def test_different_period_grains_can_coexist_without_false_overlap(self) -> None:
        dimension = PeriodDimension([
            build_period("MONTH", anchor="2026-07-14"),
            build_period("QUARTER", anchor="2026-07-14"),
            build_period("YEAR", anchor="2026-07-14"),
        ])
        self.assertEqual(len(dimension.periods), 3)

    def test_five_versioned_attribution_rules_use_human_readable_basis_dates(self) -> None:
        self.assertEqual(len(ATTRIBUTION_RULES), 5)
        self.assertEqual({rule.domain for rule in ATTRIBUTION_RULES.values()}, {"CONTRACT", "COST", "INVOICE", "COLLECTION", "TAX"})
        self.assertTrue(all(rule.version == "1.0.0" and rule.human_readable_rule for rule in ATTRIBUTION_RULES.values()))
        self.assertTrue(all(
            rule.period_type == "MONTH"
            and rule.calendar_id == "STANDARD_CALENDAR"
            and rule.period_version == "1.0.0"
            for rule in ATTRIBUTION_RULES.values()
        ))

    def test_cross_period_attribution_uses_the_registered_basis_field(self) -> None:
        periods = [build_period("MONTH", anchor="2026-06-15"), build_period("MONTH", anchor="2026-07-15")]
        result = assign_period(
            {"invoice_date": "2026-07-01"}, periods,
            rule_id="INVOICE_ISSUE_DATE", rule_version="1.0.0",
        )
        self.assertEqual(result.period_id, "2026-07")
        self.assertEqual(result.domain, "INVOICE")
        self.assertFalse(result.report_degraded)

    def test_unregistered_rule_or_missing_basis_never_calculates(self) -> None:
        periods = [build_period("MONTH", anchor="2026-07-15")]
        with self.assertRaises(DatePeriodError) as rule:
            assign_period({"invoice_date": "2026-07-01"}, periods, rule_id="MISSING", rule_version="1.0.0")
        self.assertEqual(rule.exception.action, "MANUAL_CONFIRMATION")
        with self.assertRaises(DatePeriodError) as basis:
            assign_period({}, periods, rule_id="INVOICE_ISSUE_DATE", rule_version="1.0.0")
        self.assertEqual(basis.exception.action, "QUALITY_QUEUE")

    def test_late_event_after_close_degrades_report_to_manual_confirmation(self) -> None:
        period = build_period(
            "MONTH", anchor="2026-06-15",
            closed_at=datetime(2026, 7, 3, 17, tzinfo=ZoneInfo("Asia/Shanghai")),
        )
        result = assign_period(
            {"receipt_date": "2026-06-30"}, [period],
            rule_id="COLLECTION_RECEIPT_DATE", rule_version="1.0.0",
            recorded_at=datetime(2026, 7, 4, 9, tzinfo=ZoneInfo("Asia/Shanghai")),
        )
        self.assertEqual(result.status, "DEGRADED_MANUAL_CONFIRMATION")
        self.assertIsNone(result.period_id)
        self.assertTrue(result.report_degraded)
        self.assertEqual(result.action, "MANUAL_CONFIRMATION")

    def test_attribution_rejects_ambiguous_periods_and_naive_recorded_time(self) -> None:
        periods = [
            build_period("MONTH", anchor="2026-07-15"),
            BusinessPeriod(
                "2026-07-OVERLAP", "MONTH", date(2026, 7, 1), date(2026, 7, 31),
                date(2026, 7, 31), "STANDARD_CALENDAR", "1.0.0",
            ),
        ]
        with self.assertRaises(DatePeriodError) as ambiguous:
            assign_period({"signed_date": "2026-07-14"}, periods, rule_id="CONTRACT_SIGNED_DATE", rule_version="1.0.0")
        self.assertEqual(ambiguous.exception.action, "MANUAL_CONFIRMATION")
        with self.assertRaises(DatePeriodError) as naive:
            assign_period(
                {"signed_date": "2026-07-14"}, [periods[0]],
                rule_id="CONTRACT_SIGNED_DATE", rule_version="1.0.0", recorded_at=datetime(2026, 7, 14, 1),
            )
        self.assertEqual(naive.exception.action, "QUALITY_QUEUE")

    def test_public_contract_is_phase_bounded_and_raw_free(self) -> None:
        summary = public_contract_summary()
        self.assertTrue(summary["business_timezone_required"])
        self.assertFalse(summary["ambiguous_date_guessing_allowed"])
        self.assertFalse(summary["excel_1900_serial_60_allowed"])
        self.assertEqual(summary["period_type_count"], 6)
        self.assertFalse(summary["period_overlap_merge_allowed"])
        self.assertTrue(summary["cross_grain_period_coexistence_allowed"])
        self.assertEqual(summary["attribution_domain_count"], 5)
        self.assertFalse(summary["unregistered_rule_calculation_allowed"])
        self.assertEqual(summary["raw_root_access_count"], 0)


if __name__ == "__main__":
    unittest.main()
