from __future__ import annotations

from calendar import monthcalendar, FRIDAY
from datetime import date, datetime, time

from .models import RoutineRule

TRIGGER_WINDOWS = {
    "morning_1135": "11:35",
    "evening_1705": "17:05",
}

WEEKDAY_MAP = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


def parse_time_hhmm(value: str) -> time:
    hour, minute = value.split(":", 1)
    return time(int(hour), int(minute))


def is_third_week_friday(d: date) -> bool:
    """Return True for the Friday in the third calendar week containing a Friday.

    The business phrase is 每月第三周周五前. This implementation chooses the
    third Friday of the natural month. Keep configurable if owner later defines
    第三周 differently.
    """
    fridays = []
    for week in monthcalendar(d.year, d.month):
        day = week[FRIDAY]
        if day:
            fridays.append(date(d.year, d.month, day))
    return len(fridays) >= 3 and d == fridays[2]


def is_rule_due_on(frequency: str, d: date, weekdays: tuple[str, ...] = ()) -> bool:
    if frequency == "daily":
        return True
    if frequency == "weekly":
        target_weekdays = {WEEKDAY_MAP[w] for w in weekdays}
        return d.weekday() in target_weekdays
    if frequency == "monthly_third_week_friday":
        return is_third_week_friday(d)
    return False


def has_due_time_passed(now: datetime, due_time: str) -> bool:
    return now.time() >= parse_time_hhmm(due_time)


def infer_trigger_window(now: datetime) -> str:
    """Choose the nearest supported automation window for manual runs."""
    if now.time() < parse_time_hhmm("14:00"):
        return "morning_1135"
    return "evening_1705"


def rules_for_trigger_window(
    rules: list[RoutineRule] | tuple[RoutineRule, ...],
    check_date: date,
    trigger_window: str,
) -> tuple[list[RoutineRule], list[RoutineRule]]:
    if trigger_window not in TRIGGER_WINDOWS:
        raise ValueError(f"unsupported trigger_window: {trigger_window}")

    evaluated: list[RoutineRule] = []
    skipped: list[RoutineRule] = []
    for rule in rules:
        is_due_today = is_rule_due_on(rule.frequency, check_date, rule.weekdays)
        if rule.trigger_window == trigger_window and is_due_today:
            evaluated.append(rule)
        else:
            skipped.append(rule)
    return evaluated, skipped
