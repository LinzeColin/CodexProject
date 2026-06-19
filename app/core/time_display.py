from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo


def parse_datetime(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def format_display_time(value: str | None, zone: str | None = None) -> str:
    if not value:
        return "-"
    parsed = parse_datetime(value)
    if not parsed:
        return value
    if zone:
        parsed = parsed.astimezone(ZoneInfo(zone))
    return parsed.strftime("%Y%m%d - %H:%M %Z")


def format_now_display(zone: str) -> str:
    return datetime.now(ZoneInfo(zone)).strftime("%Y%m%d - %H:%M %Z")
