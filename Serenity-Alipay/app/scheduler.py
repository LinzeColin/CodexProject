from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo


SCHEDULE_SLOTS: dict[str, str] = {
    "R1": "08:30",
    "R2": "09:30",
    "R3": "10:30",
    "R4": "11:30",
    "R5": "12:30",
    "R6": "13:30",
    "R7": "14:30",
    "R8": "15:30",
    "R9": "16:30",
    "R10": "17:30",
}


@dataclass(frozen=True)
class SlotTimes:
    slot: str
    beijing: datetime
    secondary: datetime


def validate_slot(slot: str) -> str:
    slot = slot.upper()
    if slot not in SCHEDULE_SLOTS:
        allowed = ", ".join(SCHEDULE_SLOTS)
        raise ValueError(f"Unknown slot {slot!r}. Allowed slots: {allowed}")
    return slot


def slot_times(
    slot: str,
    run_date: date | None = None,
    primary_tz: str = "Asia/Shanghai",
    secondary_tz: str = "Australia/Sydney",
) -> SlotTimes:
    slot = validate_slot(slot)
    primary_zone = ZoneInfo(primary_tz)
    secondary_zone = ZoneInfo(secondary_tz)
    day = run_date or datetime.now(primary_zone).date()
    hour, minute = [int(part) for part in SCHEDULE_SLOTS[slot].split(":")]
    beijing_dt = datetime.combine(day, time(hour, minute), tzinfo=primary_zone)
    return SlotTimes(slot=slot, beijing=beijing_dt, secondary=beijing_dt.astimezone(secondary_zone))


def next_slot_after(current: datetime, primary_tz: str = "Asia/Shanghai") -> str | None:
    primary_now = current.astimezone(ZoneInfo(primary_tz))
    if not is_business_day(primary_now, primary_tz):
        return None
    for slot, hhmm in SCHEDULE_SLOTS.items():
        hour, minute = [int(part) for part in hhmm.split(":")]
        candidate = datetime.combine(primary_now.date(), time(hour, minute), tzinfo=ZoneInfo(primary_tz))
        if candidate > primary_now:
            return slot
    return None


def parse_datetime(value: str, default_tz: str = "Asia/Shanghai") -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=ZoneInfo(default_tz))
    return parsed


def is_business_day(current: datetime, primary_tz: str = "Asia/Shanghai") -> bool:
    primary_now = current.astimezone(ZoneInfo(primary_tz))
    return primary_now.weekday() < 5


def due_slot_at(
    current: datetime,
    tolerance_minutes: int = 3,
    primary_tz: str = "Asia/Shanghai",
    require_business_day: bool = True,
) -> str | None:
    primary_now = current.astimezone(ZoneInfo(primary_tz))
    if require_business_day and not is_business_day(primary_now, primary_tz):
        return None
    tolerance = timedelta(minutes=tolerance_minutes)
    for slot, hhmm in SCHEDULE_SLOTS.items():
        hour, minute = [int(part) for part in hhmm.split(":")]
        scheduled = datetime.combine(primary_now.date(), time(hour, minute), tzinfo=ZoneInfo(primary_tz))
        if abs(primary_now - scheduled) <= tolerance:
            return slot
    return None
