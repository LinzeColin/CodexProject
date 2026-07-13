from __future__ import annotations

from datetime import date

from apps.api.app.domain_repository import _parse_report_date, _report_period_bounds


def test_report_period_bounds_keep_document_and_report_time_semantics_separate() -> None:
    start, end = _report_period_bounds(
        ["2024-12-31", ""],
        [
            {"start": "2023-01-01", "end": "2023-12-31"},
            {"start": "2024-01-01", "end": "2024-12-31"},
            {"start": "2024-04-01", "end": "2024-06-30"},
        ],
    )

    assert start == date(2024, 1, 1)
    assert end == date(2024, 12, 31)


def test_report_period_bounds_ignore_invalid_or_missing_values() -> None:
    start, end = _report_period_bounds(
        ["not-a-date", None],
        [{"end": "2025-03-31"}, {"start": 123, "end": "invalid"}],
    )

    assert start is None
    assert end == date(2025, 3, 31)
    assert _parse_report_date("2025-02-30") is None
