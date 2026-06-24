from __future__ import annotations

import fcntl
from datetime import datetime
from pathlib import Path
from typing import TextIO
from zoneinfo import ZoneInfo

from app.config import Settings
from app.core.application_portal import build_application_portal
from app.core.notification import notify_run
from app.core.preflight import run_preflight
from app.core.scheduler_runner import scheduler_tick
from app.scheduler import due_slot_at, parse_datetime


def _current_time(settings: Settings, now: str | None) -> datetime:
    if now:
        return parse_datetime(now, settings.timezone_primary)
    return datetime.now(ZoneInfo(settings.timezone_primary))


def _acquire_tick_lock(settings: Settings) -> TextIO | None:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    handle = (settings.data_dir / "automation_tick.lock").open("w", encoding="utf-8")
    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        handle.close()
        return None
    handle.write(datetime.now(ZoneInfo("UTC")).isoformat(timespec="seconds"))
    handle.flush()
    return handle


def _release_tick_lock(handle: TextIO) -> None:
    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    handle.close()


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
    lock_handle = _acquire_tick_lock(settings)
    if lock_handle is None:
        return {
            "action": "skipped_locked",
            "due_slot": None,
            "preflight": None,
            "effective_dry_run": True,
            "dry_run_forced_by_preflight": False,
            "scheduler": None,
            "notification": None,
        }
    try:
        return _automation_tick_locked(
            settings,
            now=now,
            dry_run=dry_run,
            force_slot=force_slot,
            allow_duplicate=allow_duplicate,
            tolerance_minutes=tolerance_minutes,
            scan_paths=scan_paths,
            send_mail=send_mail,
            local=local,
        )
    finally:
        _release_tick_lock(lock_handle)


def _automation_tick_locked(
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
    runtime_settings = settings.with_runtime_mail_intent(dry_run=dry_run, send_mail=send_mail)
    current = _current_time(settings, now)
    current_iso = current.astimezone(ZoneInfo(settings.timezone_primary)).isoformat(timespec="seconds")
    due_slot = force_slot or due_slot_at(current, tolerance_minutes, runtime_settings.timezone_primary)

    if not due_slot:
        scheduler_result = scheduler_tick(
            runtime_settings,
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

    preflight = run_preflight(runtime_settings, scan_paths=scan_paths or [])
    production_ready = bool(preflight["production_ready"])
    effective_dry_run = bool(dry_run or not production_ready)
    scheduler_result = scheduler_tick(
        runtime_settings,
        now=current_iso,
        dry_run=effective_dry_run,
        force_slot=force_slot,
        allow_duplicate=allow_duplicate,
        tolerance_minutes=tolerance_minutes,
    )

    notification = None
    application_portal = None
    if scheduler_result.get("action") == "ran" and scheduler_result.get("run_id"):
        notification = notify_run(
            runtime_settings,
            str(scheduler_result["run_id"]),
            dry_run=effective_dry_run,
            send_mail=send_mail,
            local=local,
        )
        application_portal = build_application_portal(runtime_settings, install_apps=False)

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
        "application_portal": application_portal,
    }
