from __future__ import annotations

from datetime import date, datetime, timedelta


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def week_bounds(day: date) -> tuple[date, date, str]:
    start = day - timedelta(days=day.weekday())
    end = start + timedelta(days=6)
    iso = day.isocalendar()
    return start, end, f"{iso.year}-W{iso.week:02d}"


def month_bounds(day: date) -> tuple[date, date, str]:
    start = date(day.year, day.month, 1)
    if day.month == 12:
        end = date(day.year, 12, 31)
    else:
        end = date(day.year, day.month + 1, 1) - timedelta(days=1)
    return start, end, f"{day.year}-{day.month:02d}"


def quarter_bounds(day: date) -> tuple[date, date, str]:
    quarter = (day.month - 1) // 3 + 1
    start_month = (quarter - 1) * 3 + 1
    start = date(day.year, start_month, 1)
    if quarter == 4:
        end = date(day.year, 12, 31)
    else:
        end = date(day.year, start_month + 3, 1) - timedelta(days=1)
    return start, end, f"{day.year}-Q{quarter}"


def half_bounds(day: date) -> tuple[date, date, str]:
    if day.month <= 6:
        return date(day.year, 1, 1), date(day.year, 6, 30), f"{day.year}-H1"
    return date(day.year, 7, 1), date(day.year, 12, 31), f"{day.year}-H2"


def year_bounds(day: date) -> tuple[date, date, str]:
    return date(day.year, 1, 1), date(day.year, 12, 31), str(day.year)


PERIODS = {
    "week": week_bounds,
    "month": month_bounds,
    "quarter": quarter_bounds,
    "half": half_bounds,
    "year": year_bounds,
}
