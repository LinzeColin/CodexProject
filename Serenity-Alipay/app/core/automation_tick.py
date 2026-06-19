from __future__ import annotations

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from app.config import Settings
from app.core.notification import notify_run
from app.core.preflight import run_preflight
from app.core.scheduler_runner import scheduler_tick
from app.scheduler import due_slot_at, parse_datetime


def _current_time(settings: Settings, now: str | None) -> datetime:
    if now:
        return parse_datetime(now, settings.timezone_primary)
    return datetime.now(ZoneInfo(settings.timezone_primary))


def automation_tick(
    settings: Settings,
    *,
    now: str | None = None,
    dry_run: bool = True,
    force_slot: str | None = None,
    allow_duplicate: bool = False,
    tolerance_minutes: int = 3,
    scan_paths: list[Path] | None = None,
    send_mail: bool = False,
    local: bool = False,
) -> dict[str, object]:
    current = _current_time(settings, now)
    current_iso = current.astimezone(ZoneInfo(settings.timezone_primary)).isoformat(timespec="seconds")
    due_slot = force_slot or due_slot_at(current, tolerance_minutes, settings.timezone_primary)

    if not due_slot:
        scheduler_result = scheduler_tick(
            settings,
            now=current_iso,
            dry_run=True,
            force_slot=None,
            allow_duplicate=allow_duplicate,
            tolerance_minutes=tolerance_minutes,
        )
        return {
            "action": scheduler_result["action"],
            "due_slot": None,
            "preflight": None,
            "effective_dry_run": True,
            "dry_run_forced_by_preflight": False,
            "scheduler": scheduler_result,
            "notification": None,
        }

    preflight = run_preflight(settings, scan_paths=scan_paths or [])
    production_ready = bool(preflight["production_ready"])
    effective_dry_run = bool(dry_run or not production_ready)
    scheduler_result = scheduler_tick(
        settings,
        now=current_iso,
        dry_run=effective_dry_run,
        force_slot=force_slot,
        allow_duplicate=allow_duplicate,
        tolerance_minutes=tolerance_minutes,
    )

    notification = None
    if scheduler_result.get("action") == "ran" and scheduler_result.get("run_id"):
        notification = notify_run(
            settings,
            str(scheduler_result["run_id"]),
            dry_run=effective_dry_run,
            send_mail=send_mail,
            local=local,
        )

    return {
        "action": scheduler_result["action"],
        "due_slot": scheduler_result.get("due_slot"),
        "preflight": {
            "production_ready": preflight["production_ready"],
            "shadow_ready": preflight["shadow_ready"],
            "status": preflight["status"],
            "blockers": [
                {"name": blocker["name"], "message": blocker["message"]}
                for blocker in preflight.get("blockers", [])
            ],
            "warnings": [
                {"name": warning["name"], "message": warning["message"]}
                for warning in preflight.get("warnings", [])
            ],
            "json_path": preflight.get("json_path"),
            "markdown_path": preflight.get("markdown_path"),
        },
        "effective_dry_run": effective_dry_run,
        "dry_run_forced_by_preflight": bool(not dry_run and not production_ready),
        "scheduler": scheduler_result,
        "notification": notification,
    }
