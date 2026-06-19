from datetime import date

from app.scheduler import SCHEDULE_SLOTS, slot_times


def test_schedule_slots_are_exact():
    assert list(SCHEDULE_SLOTS.items()) == [
        ("R1", "08:30"),
        ("R2", "09:30"),
        ("R3", "10:30"),
        ("R4", "11:30"),
        ("R5", "12:30"),
        ("R6", "13:30"),
        ("R7", "14:30"),
        ("R8", "15:30"),
        ("R9", "16:30"),
        ("R10", "17:30"),
    ]


def test_beijing_slot_converts_to_australia_sydney_with_zoneinfo():
    times = slot_times("R7", date(2026, 6, 12))
    assert times.beijing.isoformat(timespec="minutes") == "2026-06-12T14:30+08:00"
    assert times.secondary.isoformat(timespec="minutes") == "2026-06-12T16:30+10:00"
