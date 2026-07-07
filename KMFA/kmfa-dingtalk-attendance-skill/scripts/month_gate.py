#!/usr/bin/env python3
"""Resolve KMFA stage-2 eligibility for monthly attendance consensus.

Rules:
- Attendance timezone defaults to Asia/Shanghai.
- Stage-2 target month is previous natural month.
- Eligible only on day 1-5 of the following month.
- Eligible only for evening run slot.
"""
from __future__ import annotations

import argparse
import calendar
import json
import os
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class MonthGate:
    now_local: str
    timezone: str
    run_slot: str
    target_month: str
    target_month_start: str
    target_month_end: str
    month_completed: bool
    stage2_eligible: bool
    stage2_run_index: int | None
    reason: str


def parse_date_override(value: str | None, tz: ZoneInfo) -> datetime:
    if value:
        if len(value) == 10:
            y, m, d = map(int, value.split("-"))
            return datetime(y, m, d, 20, 0, 0, tzinfo=tz)
        return datetime.fromisoformat(value).astimezone(tz)
    return datetime.now(tz)


def previous_month_bounds(current: date) -> tuple[date, date]:
    first_current = current.replace(day=1)
    last_prev = first_current - timedelta(days=1)
    first_prev = last_prev.replace(day=1)
    return first_prev, last_prev


def resolve(run_slot: str, tz_name: str, today_override: str | None = None) -> MonthGate:
    tz = ZoneInfo(tz_name)
    now = parse_date_override(today_override, tz)
    local_date = now.date()
    first_prev, last_prev = previous_month_bounds(local_date)
    target_month = f"{first_prev.year:04d}{first_prev.month:02d}"
    month_completed = last_prev < local_date
    day = local_date.day
    eligible_day = 1 <= day <= 5
    eligible_slot = run_slot == "evening"
    eligible = month_completed and eligible_day and eligible_slot
    if not eligible_slot:
        reason = "run_slot_not_evening"
    elif not eligible_day:
        reason = "local_day_not_in_1_to_5"
    elif not month_completed:
        reason = "target_month_not_completed"
    else:
        reason = "eligible"
    return MonthGate(
        now_local=now.isoformat(),
        timezone=tz_name,
        run_slot=run_slot,
        target_month=target_month,
        target_month_start=first_prev.isoformat(),
        target_month_end=last_prev.isoformat(),
        month_completed=month_completed,
        stage2_eligible=eligible,
        stage2_run_index=day if eligible else None,
        reason=reason,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-slot", default=os.environ.get("KMFA_RUN_SLOT", "manual"), choices=["morning", "evening", "manual"])
    parser.add_argument("--timezone", default=os.environ.get("KMFA_ATTENDANCE_TZ", "Asia/Shanghai"))
    parser.add_argument("--today", default=os.environ.get("KMFA_TODAY_OVERRIDE"), help="YYYY-MM-DD or ISO datetime for deterministic tests")
    parser.add_argument("--print-json", action="store_true")
    args = parser.parse_args()
    gate = resolve(args.run_slot, args.timezone, args.today)
    print(json.dumps(asdict(gate), ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if args.print_json or gate.stage2_eligible else 0


if __name__ == "__main__":
    raise SystemExit(main())
