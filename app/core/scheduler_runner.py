from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from app.config import Settings
from app.core.pipeline import run_slot
from app.db import connect, init_db
from app.scheduler import due_slot_at, is_business_day, parse_datetime, slot_times


def _now_for_settings(settings: Settings) -> datetime:
    return datetime.now(ZoneInfo(settings.timezone_primary))


def _slot_already_ran(conn, slot: str, run_date: str) -> str | None:
    row = conn.execute(
        """
        SELECT run_id FROM run_log
        WHERE schedule_slot=? AND substr(run_time_bj, 1, 10)=?
        ORDER BY created_at DESC, rowid DESC LIMIT 1
        """,
        (slot, run_date),
    ).fetchone()
    return row["run_id"] if row else None


def scheduler_tick(
    settings: Settings,
    now: str | None = None,
    dry_run: bool = True,
    force_slot: str | None = None,
    allow_duplicate: bool = False,
    tolerance_minutes: int = 3,
) -> dict[str, object]:
    init_db(settings.db_path)
    current = parse_datetime(now, settings.timezone_primary) if now else _now_for_settings(settings)
    business_day = is_business_day(current, settings.timezone_primary)
    slot = force_slot or due_slot_at(current, tolerance_minutes, settings.timezone_primary)
    times = slot_times(slot, current.astimezone(ZoneInfo(settings.timezone_primary)).date()) if slot else None
    created_at = datetime.now(ZoneInfo("UTC")).isoformat(timespec="seconds")

    with connect(settings.db_path) as conn:
        if not slot or not times:
            action = "no_due_slot" if business_day else "non_business_day"
            conn.execute(
                """
                INSERT INTO automation_tick_log (
                  tick_time_bj, tick_time_au, due_slot, action, run_id, dry_run, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    current.astimezone(ZoneInfo(settings.timezone_primary)).isoformat(timespec="seconds"),
                    current.astimezone(ZoneInfo(settings.timezone_secondary)).isoformat(timespec="seconds"),
                    None,
                    action,
                    None,
                    int(dry_run),
                    created_at,
                ),
            )
            return {"action": action, "due_slot": None, "run_id": None}

        existing = _slot_already_ran(conn, slot, times.beijing.date().isoformat())
        if existing and not allow_duplicate:
            conn.execute(
                """
                INSERT INTO automation_tick_log (
                  tick_time_bj, tick_time_au, due_slot, action, run_id, dry_run, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    times.beijing.isoformat(timespec="seconds"),
                    times.secondary.isoformat(timespec="seconds"),
                    slot,
                    "skipped_duplicate",
                    existing,
                    int(dry_run),
                    created_at,
                ),
            )
            return {"action": "skipped_duplicate", "due_slot": slot, "run_id": existing}

    result = run_slot(settings, slot, dry_run=dry_run, run_date=times.beijing.date())
    with connect(settings.db_path) as conn:
        conn.execute(
            """
            INSERT INTO automation_tick_log (
              tick_time_bj, tick_time_au, due_slot, action, run_id, dry_run, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                times.beijing.isoformat(timespec="seconds"),
                times.secondary.isoformat(timespec="seconds"),
                slot,
                "ran",
                result["run_id"],
                int(dry_run),
                created_at,
            ),
        )
    return {"action": "ran", "due_slot": slot, "run_id": result["run_id"], "result": result}
