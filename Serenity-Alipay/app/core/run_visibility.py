from __future__ import annotations

from datetime import timedelta

from app.core.time_display import format_display_time
from app.core.time_display import parse_datetime


CONTROLLED_BACKFILL_GRACE_MINUTES = 10


def is_future_controlled_backfill(
    run_time_bj: str | None,
    created_at: str | None,
    *,
    grace_minutes: int = CONTROLLED_BACKFILL_GRACE_MINUTES,
) -> bool:
    run_time = parse_datetime(run_time_bj or "")
    created_time = parse_datetime(created_at or "")
    if not run_time or not created_time:
        return False
    return created_time + timedelta(minutes=grace_minutes) < run_time


def display_run_time_with_backfill_note(
    run_time_bj: str | None,
    created_at: str | None,  # Kept for call-site compatibility; user-facing labels show run time only.
    *,
    zone: str = "Asia/Shanghai",
) -> str:
    return format_display_time(run_time_bj, zone)
