"""Stage 1 local runtime, recovery, and scheduler dry-run controls."""

from __future__ import annotations

import hashlib
import json
import os
import plistlib
import shutil
import socket
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping

from .config import DEFAULT_TIMEZONE, PROJECT_NAME
from .storage import inspect_database, validate_storage_report


STAGE1_RUNTIME_MODEL_ID = "adp-stage1-local-runtime-recovery-v1"
STAGE1_RUNTIME_SCHEMA_VERSION = 1
STAGE1_RUNTIME_ACCEPTANCE_ID = "ADP-ACC-S1-08-LOCAL-RUNTIME-RECOVERY"
STAGE1_RUNTIME_ACTIONS = (
    "runtime_audit",
    "tick",
    "watchdog",
    "backup",
    "restore",
    "scheduler_install",
    "scheduler_uninstall",
)
STAGE1_RUNTIME_MAX_BACKUP_BYTES = 104857600
STAGE1_RUNTIME_HEARTBEAT_FILENAME = "heartbeat.json"
STAGE1_RUNTIME_CHECKPOINT_FILENAME = "checkpoint.json"
STAGE1_RUNTIME_LOCK_FILENAME = "runtime.lock"
STAGE1_RUNTIME_STALE_AFTER_SECONDS = 5400
STAGE1_RUNTIME_LOCK_LEASE_SECONDS = STAGE1_RUNTIME_STALE_AFTER_SECONDS
STAGE1_RUNTIME_REQUIRED_DISABLED_FLAGS = (
    "ADP_PRODUCTION_ENABLED",
    "ADP_SCHEDULED_RUN_ENABLED",
    "ADP_ALLOW_SMTP_SEND",
    "ADP_ALLOW_RELEASE_UPLOAD",
)
STAGE1_RUNTIME_OS_TASKS = (
    {"name": "tick", "cadence": "PT30M", "offset_minutes": 0},
    {"name": "watchdog", "cadence": "PT30M", "offset_minutes": 5},
    {"name": "backup", "cadence": "P1D", "offset_minutes": 0},
)
STAGE1_RUNTIME_SUPPORTED_SCHEDULER_PLATFORMS = ("macos", "linux", "windows")


class Stage1RuntimeError(ValueError):
    """Raised when the Stage 1 local runtime contract cannot be satisfied."""


def build_runtime_audit(
    *,
    state_dir: str | Path,
    generated_at: str,
    db_path: str | Path | None = None,
    environment: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Inspect local runtime readiness without enabling production side effects."""

    env = dict(environment or os.environ)
    blocking_reasons = _disabled_flag_reasons(env)
    state = Path(state_dir)
    state_checks = {
        "state_dir": str(state),
        "exists": state.exists(),
        "is_directory": state.is_dir() if state.exists() else False,
        "heartbeat_exists": (state / STAGE1_RUNTIME_HEARTBEAT_FILENAME).exists(),
        "checkpoint_exists": (state / STAGE1_RUNTIME_CHECKPOINT_FILENAME).exists(),
        "lock_exists": (state / STAGE1_RUNTIME_LOCK_FILENAME).exists(),
    }
    if not state_checks["exists"]:
        blocking_reasons.append("state_dir does not exist")
    elif not state_checks["is_directory"]:
        blocking_reasons.append("state_dir is not a directory")

    storage_report: dict[str, Any] | None = None
    if db_path:
        storage_report = inspect_database(db_path)
        storage_errors = validate_storage_report(storage_report)
        if storage_errors or storage_report.get("status") != "pass":
            blocking_reasons.extend(storage_errors or storage_report.get("blocking_reasons") or ["database inspection did not pass"])

    return _base_report(
        action="runtime_audit",
        generated_at=generated_at,
        status="blocked" if blocking_reasons else "pass",
        blocking_reasons=blocking_reasons,
        state_dir=state,
        extra={
            "state_checks": state_checks,
            "storage_report": storage_report,
            "scheduler_controls": {
                "real_scheduler_install_allowed": False,
                "dry_run_templates_only": True,
                "supported_platforms": list(STAGE1_RUNTIME_SUPPORTED_SCHEDULER_PLATFORMS),
            },
        },
    )


def run_tick(*, state_dir: str | Path, generated_at: str, write: bool = True) -> dict[str, Any]:
    """Record a small heartbeat/checkpoint for the Stage 1 arXiv runtime."""

    state = Path(state_dir)
    blocking_reasons: list[str] = []
    runtime_lock = _runtime_lock_not_requested(state, action="tick")
    if write:
        with _runtime_lock(state, action="tick", generated_at=generated_at) as runtime_lock:
            blocking_reasons.extend(runtime_lock["blocking_reasons"])
            heartbeat = _tick_heartbeat(generated_at=generated_at, blocking_reasons=blocking_reasons)
            checkpoint = _tick_checkpoint(generated_at=generated_at, blocking_reasons=blocking_reasons)
            if not blocking_reasons:
                _write_json(state / STAGE1_RUNTIME_HEARTBEAT_FILENAME, heartbeat)
                _renew_runtime_lock(runtime_lock, generated_at=generated_at)
                _write_json(state / STAGE1_RUNTIME_CHECKPOINT_FILENAME, checkpoint)
    else:
        heartbeat = _tick_heartbeat(generated_at=generated_at, blocking_reasons=blocking_reasons)
        checkpoint = _tick_checkpoint(generated_at=generated_at, blocking_reasons=blocking_reasons)

    return _base_report(
        action="tick",
        generated_at=generated_at,
        status="blocked" if blocking_reasons else "pass",
        blocking_reasons=blocking_reasons,
        state_dir=state,
        extra={
            "write_enabled": write,
            "heartbeat_path": str(state / STAGE1_RUNTIME_HEARTBEAT_FILENAME),
            "checkpoint_path": str(state / STAGE1_RUNTIME_CHECKPOINT_FILENAME),
            "source_tasks": heartbeat["source_tasks"],
            "single_instance_lock_checked": True,
            "runtime_lock": runtime_lock,
        },
    )


def run_watchdog(*, state_dir: str | Path, generated_at: str) -> dict[str, Any]:
    """Check heartbeat freshness and lock state for the Stage 1 local runtime."""

    state = Path(state_dir)
    heartbeat_path = state / STAGE1_RUNTIME_HEARTBEAT_FILENAME
    lock_path = state / STAGE1_RUNTIME_LOCK_FILENAME
    blocking_reasons: list[str] = []
    heartbeat: dict[str, Any] | None = None
    heartbeat_age_seconds: int | None = None

    if not heartbeat_path.exists():
        blocking_reasons.append("heartbeat.json does not exist")
    else:
        heartbeat = _read_json(heartbeat_path)
        heartbeat_at = str(heartbeat.get("generated_at") or "")
        heartbeat_age_seconds = _age_seconds(heartbeat_at, generated_at)
        if heartbeat_age_seconds is None:
            blocking_reasons.append("heartbeat generated_at is not parseable")
        elif heartbeat_age_seconds > STAGE1_RUNTIME_STALE_AFTER_SECONDS:
            blocking_reasons.append("heartbeat is stale")
        if heartbeat.get("production_side_effects_enabled") is not False:
            blocking_reasons.append("heartbeat must not enable production side effects")

    lock_state = {"exists": lock_path.exists(), "stale": False, "age_seconds": None}
    if lock_path.exists():
        lock_age = _mtime_age_seconds(lock_path, generated_at)
        lock_state["age_seconds"] = lock_age
        if lock_age is None or lock_age > STAGE1_RUNTIME_STALE_AFTER_SECONDS:
            lock_state["stale"] = True
            blocking_reasons.append("runtime lock is stale")

    return _base_report(
        action="watchdog",
        generated_at=generated_at,
        status="blocked" if blocking_reasons else "pass",
        blocking_reasons=blocking_reasons,
        state_dir=state,
        extra={
            "heartbeat_path": str(heartbeat_path),
            "heartbeat_age_seconds": heartbeat_age_seconds,
            "lock_state": lock_state,
            "watchdog_policy": {
                "stale_after_seconds": STAGE1_RUNTIME_STALE_AFTER_SECONDS,
                "recovery_action": "rerun_tick_or_restore_from_backup_after_operator_review",
            },
        },
    )


def create_runtime_backup(
    *,
    db_path: str | Path,
    backup_dir: str | Path,
    generated_at: str,
    include_paths: Iterable[str | Path] = (),
) -> dict[str, Any]:
    """Create a small SQLite/config backup with SHA256 manifest evidence."""

    db = Path(db_path)
    root = Path(backup_dir)
    backup_id = _id("stage1-runtime-backup", generated_at)
    target_dir = root / backup_id
    blocking_reasons: list[str] = []
    if not db.exists():
        blocking_reasons.append("database file does not exist")
    storage_report = inspect_database(db) if db.exists() else None
    if storage_report:
        storage_errors = validate_storage_report(storage_report)
        if storage_errors or storage_report.get("status") != "pass":
            blocking_reasons.extend(storage_errors or storage_report.get("blocking_reasons") or ["database inspection did not pass"])
    small_paths = [Path(path) for path in include_paths]
    for path in small_paths:
        if not path.exists():
            blocking_reasons.append(f"include path does not exist: {path}")
    supporting_targets: dict[Path, Path] = {}
    seen_supporting_targets: set[Path] = set()
    for path in small_paths:
        if path.exists() and path.is_file():
            copied = target_dir / "files" / _supporting_file_backup_name(path)
            if copied in seen_supporting_targets:
                blocking_reasons.append(f"duplicate supporting file backup path: {copied.relative_to(target_dir)}")
            supporting_targets[path] = copied
            seen_supporting_targets.add(copied)
    total_input_size = (db.stat().st_size if db.exists() else 0) + sum(path.stat().st_size for path in small_paths if path.exists() and path.is_file())
    if total_input_size > STAGE1_RUNTIME_MAX_BACKUP_BYTES:
        blocking_reasons.append(f"backup input is {total_input_size} bytes, above {STAGE1_RUNTIME_MAX_BACKUP_BYTES}")
    if blocking_reasons:
        return _base_report(
            action="backup",
            generated_at=generated_at,
            status="blocked",
            blocking_reasons=blocking_reasons,
            state_dir=root,
            extra={"backup_id": backup_id, "storage_report": storage_report, "max_backup_bytes": STAGE1_RUNTIME_MAX_BACKUP_BYTES},
        )

    target_dir.mkdir(parents=True, exist_ok=True)
    backup_db = target_dir / "adp.sqlite3"
    source = sqlite3.connect(db)
    dest = sqlite3.connect(backup_db)
    try:
        source.backup(dest)
    finally:
        dest.close()
        source.close()

    files = [_manifest_file("database", backup_db, source_path=db)]
    for path in small_paths:
        if path.is_file():
            copied = supporting_targets[path]
            copied.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, copied)
            files.append(_manifest_file("supporting_file", copied, source_path=path))
    manifest = {
        "model_id": STAGE1_RUNTIME_MODEL_ID,
        "schema_version": STAGE1_RUNTIME_SCHEMA_VERSION,
        "backup_id": backup_id,
        "generated_at": generated_at,
        "acceptance_id": STAGE1_RUNTIME_ACCEPTANCE_ID,
        "files": files,
        "total_bytes": sum(int(file["size_bytes"]) for file in files),
        "production_side_effects_enabled": False,
    }
    manifest_path = target_dir / "backup_manifest.json"
    _write_json(manifest_path, manifest)
    return _base_report(
        action="backup",
        generated_at=generated_at,
        status="pass",
        blocking_reasons=[],
        state_dir=root,
        extra={
            "backup_id": backup_id,
            "backup_dir": str(target_dir),
            "backup_manifest_path": str(manifest_path),
            "manifest_sha256": _sha256_file(manifest_path),
            "files": files,
            "storage_report": storage_report,
        },
    )


def restore_runtime_backup(
    *,
    manifest_path: str | Path,
    target_db_path: str | Path,
    generated_at: str,
    confirm_restore: bool = False,
    allow_overwrite: bool = False,
) -> dict[str, Any]:
    """Restore a backed-up SQLite database to an explicit target path."""

    manifest_file = Path(manifest_path)
    target = Path(target_db_path)
    blocking_reasons: list[str] = []
    if not confirm_restore:
        blocking_reasons.append("confirm_restore is required")
    if not manifest_file.exists():
        blocking_reasons.append("backup manifest does not exist")
    manifest: dict[str, Any] | None = None
    database_entry: dict[str, Any] | None = None
    if manifest_file.exists():
        manifest = _read_json(manifest_file)
        if manifest.get("model_id") != STAGE1_RUNTIME_MODEL_ID:
            blocking_reasons.append("backup manifest model_id is invalid")
        for item in manifest.get("files") or []:
            if isinstance(item, dict) and item.get("role") == "database":
                database_entry = item
                break
        if not database_entry:
            blocking_reasons.append("backup manifest does not contain a database entry")
    if target.exists() and not allow_overwrite:
        blocking_reasons.append("target database already exists")
    backup_db: Path | None = None
    if database_entry:
        try:
            backup_db = _safe_manifest_backup_path(database_entry.get("path"), backup_root=manifest_file.parent)
        except Stage1RuntimeError as exc:
            blocking_reasons.append(str(exc))
    if database_entry and backup_db and not backup_db.exists():
        blocking_reasons.append("backup database file does not exist")
    if database_entry and backup_db and backup_db.exists() and _sha256_file(backup_db) != database_entry.get("sha256"):
        blocking_reasons.append("backup database sha256 does not match manifest")
    if blocking_reasons:
        return _base_report(
            action="restore",
            generated_at=generated_at,
            status="blocked",
            blocking_reasons=blocking_reasons,
            state_dir=target.parent,
            extra={"manifest_path": str(manifest_file), "target_db_path": str(target), "confirm_restore": confirm_restore},
        )

    target.parent.mkdir(parents=True, exist_ok=True)
    temp_target = target.with_name(f".{target.name}.{_id('restore-tmp', generated_at)}.tmp")
    previous_backup: Path | None = None
    storage_report: dict[str, Any] | None = None
    try:
        temp_target.unlink(missing_ok=True)
        shutil.copy2(backup_db, temp_target)
        _fsync_file(temp_target)
        if _sha256_file(temp_target) != database_entry.get("sha256"):
            blocking_reasons.append("copied restore database sha256 does not match manifest")
        else:
            try:
                storage_report = inspect_database(temp_target)
            except sqlite3.DatabaseError as exc:
                storage_report = {
                    "status": "blocked",
                    "blocking_reasons": [f"restored database inspection failed: {exc}"],
                }
                blocking_reasons.extend(storage_report["blocking_reasons"])
            else:
                storage_errors = validate_storage_report(storage_report)
                blocking_reasons.extend(storage_errors)
                if storage_report.get("status") != "pass":
                    blocking_reasons.extend(storage_report.get("blocking_reasons") or ["restored database inspection did not pass"])
        if not blocking_reasons:
            if target.exists():
                previous_backup = target.with_name(f".{target.name}.{_id('pre-restore', generated_at)}.bak")
                shutil.copy2(target, previous_backup)
                _fsync_file(previous_backup)
            os.replace(temp_target, target)
            _fsync_directory(target.parent)
    except OSError as exc:
        blocking_reasons.append(f"restore atomic switch failed: {exc}")
    finally:
        if blocking_reasons:
            temp_target.unlink(missing_ok=True)

    if storage_report is None and target.exists() and not blocking_reasons:
        storage_report = inspect_database(target)
    return _base_report(
        action="restore",
        generated_at=generated_at,
        status="blocked" if blocking_reasons else "pass",
        blocking_reasons=blocking_reasons,
        state_dir=target.parent,
        extra={
            "manifest_path": str(manifest_file),
            "target_db_path": str(target),
            "target_sha256": _sha256_file(target) if target.exists() else None,
            "previous_target_backup_path": str(previous_backup) if previous_backup else None,
            "restored_database_ready": not blocking_reasons,
            "storage_report": storage_report,
        },
    )


def build_scheduler_plan(
    *,
    action: str,
    platform: str,
    project_root: str | Path,
    state_dir: str | Path,
    generated_at: str,
    artifact_dir: str | Path | None = None,
    write: bool = False,
) -> dict[str, Any]:
    """Build dry-run scheduler install/uninstall templates without applying them."""

    normalized_action = action.replace("-", "_")
    normalized_platform = platform.lower()
    blocking_reasons: list[str] = []
    if normalized_action not in {"scheduler_install", "scheduler_uninstall"}:
        blocking_reasons.append("scheduler action must be scheduler_install or scheduler_uninstall")
    if normalized_platform not in STAGE1_RUNTIME_SUPPORTED_SCHEDULER_PLATFORMS:
        blocking_reasons.append("unsupported scheduler platform")
    templates = (
        _scheduler_templates(normalized_platform, Path(project_root), Path(state_dir), generated_at=generated_at, uninstall=normalized_action == "scheduler_uninstall")
        if not blocking_reasons
        else []
    )
    written_paths: list[str] = []
    if write and not blocking_reasons:
        if artifact_dir is None:
            blocking_reasons.append("artifact_dir is required when write is true")
        else:
            output_dir = Path(artifact_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            for template in templates:
                target = output_dir / str(template["filename"])
                target.write_text(str(template["content"]), encoding="utf-8")
                written_paths.append(str(target))
    return _base_report(
        action=normalized_action,
        generated_at=generated_at,
        status="blocked" if blocking_reasons else "pass",
        blocking_reasons=blocking_reasons,
        state_dir=state_dir,
        extra={
            "platform": normalized_platform,
            "project_root": str(project_root),
            "dry_run_only": True,
            "applied": False,
            "real_scheduler_install_allowed": False,
            "templates": templates,
            "written_paths": written_paths,
        },
    )


def validate_stage1_runtime_report(report: Mapping[str, Any]) -> list[str]:
    """Validate a Stage 1 runtime/recovery report."""

    errors: list[str] = []
    if report.get("model_id") != STAGE1_RUNTIME_MODEL_ID:
        errors.append("runtime report model_id must be adp-stage1-local-runtime-recovery-v1")
    if report.get("schema_version") != STAGE1_RUNTIME_SCHEMA_VERSION:
        errors.append("runtime report schema_version must be 1")
    if report.get("acceptance_id") != STAGE1_RUNTIME_ACCEPTANCE_ID:
        errors.append("runtime report acceptance_id must be ADP-ACC-S1-08-LOCAL-RUNTIME-RECOVERY")
    if report.get("action") not in STAGE1_RUNTIME_ACTIONS:
        errors.append("runtime report action is not recognized")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("runtime report status must be pass or blocked")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked runtime report requires blocking_reasons")
    if report.get("production_side_effects_enabled") is not False:
        errors.append("runtime report must keep production_side_effects_enabled false")
    if report.get("real_smtp_sent") is not False or report.get("real_release_uploaded") is not False:
        errors.append("runtime report must not claim SMTP or Release side effects")
    if report.get("real_scheduler_installed") is not False:
        errors.append("runtime report must not claim real scheduler installation")
    if report.get("action") in {"scheduler_install", "scheduler_uninstall"}:
        if report.get("dry_run_only") is not True:
            errors.append("scheduler reports must be dry_run_only")
        if report.get("applied") is not False:
            errors.append("scheduler reports must not be applied in S1-08")
    if report.get("action") == "restore" and report.get("status") == "pass" and report.get("restored_database_ready") is not True:
        errors.append("passing restore report requires restored_database_ready true")
    if report.get("action") == "backup" and report.get("status") == "pass" and not report.get("backup_manifest_path"):
        errors.append("passing backup report requires backup_manifest_path")
    return errors


def _base_report(
    *,
    action: str,
    generated_at: str,
    status: str,
    blocking_reasons: list[str],
    state_dir: str | Path,
    extra: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "model_id": STAGE1_RUNTIME_MODEL_ID,
        "schema_version": STAGE1_RUNTIME_SCHEMA_VERSION,
        "acceptance_id": STAGE1_RUNTIME_ACCEPTANCE_ID,
        "runtime_report_id": _id(action, generated_at),
        "project": PROJECT_NAME,
        "stage": "S1-A",
        "action": action,
        "generated_at": generated_at,
        "timezone": DEFAULT_TIMEZONE,
        "state_dir": str(state_dir),
        "status": status,
        "blocking_reasons": blocking_reasons,
        "production_side_effects_enabled": False,
        "real_scheduler_installed": False,
        "real_smtp_sent": False,
        "real_release_uploaded": False,
        "local_side_effect_scope": "explicit_state_or_artifact_paths_only",
        **dict(extra),
    }


def _disabled_flag_reasons(environment: Mapping[str, str]) -> list[str]:
    reasons: list[str] = []
    for key in STAGE1_RUNTIME_REQUIRED_DISABLED_FLAGS:
        if str(environment.get(key, "")).strip().lower() == "true":
            reasons.append(f"{key} must not be true during S1-08")
    return reasons


def _tick_heartbeat(*, generated_at: str, blocking_reasons: list[str]) -> dict[str, Any]:
    return {
        "model_id": STAGE1_RUNTIME_MODEL_ID,
        "generated_at": generated_at,
        "project": PROJECT_NAME,
        "timezone": DEFAULT_TIMEZONE,
        "status": "blocked" if blocking_reasons else "pass",
        "source_tasks": [
            {
                "board_id": "B1",
                "source_id": "SRC-ARXIV",
                "action": "build_stage1_arxiv_text_delivery_slice",
                "due": True,
                "reason": "Stage 1 Window A arXiv tick fixture",
            }
        ],
        "production_side_effects_enabled": False,
        "blocking_reasons": blocking_reasons,
    }


def _tick_checkpoint(*, generated_at: str, blocking_reasons: list[str]) -> dict[str, Any]:
    return {
        "checkpoint_id": _id("checkpoint", generated_at),
        "generated_at": generated_at,
        "last_completed_action": "tick",
        "next_action": "watchdog",
        "resumable": not blocking_reasons,
    }


@contextmanager
def _runtime_lock(state: Path, *, action: str, generated_at: str) -> Iterable[dict[str, Any]]:
    state.mkdir(parents=True, exist_ok=True)
    lock_path = state / STAGE1_RUNTIME_LOCK_FILENAME
    takeover = _take_over_stale_runtime_lock(lock_path, generated_at=generated_at)
    payload = _runtime_lock_payload(action=action, generated_at=generated_at)
    lock_state = {
        "path": str(lock_path),
        "requested": True,
        "acquired": False,
        "released": False,
        "payload": payload,
        "takeover": takeover,
        "renewals": [],
        "blocking_reasons": [],
    }
    try:
        try:
            fd = os.open(lock_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
        except FileExistsError:
            lock_state["blocking_reasons"].append("runtime lock already exists")
        else:
            lock_state["acquired"] = True
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, sort_keys=True)
        yield lock_state
    finally:
        if lock_state["acquired"]:
            lock_path.unlink(missing_ok=True)
            lock_state["released"] = True


def _runtime_lock_not_requested(state: Path, *, action: str) -> dict[str, Any]:
    return {
        "path": str(state / STAGE1_RUNTIME_LOCK_FILENAME),
        "requested": False,
        "acquired": False,
        "released": False,
        "payload": None,
        "takeover": {"attempted": False, "performed": False, "reason": "write disabled"},
        "renewals": [],
        "blocking_reasons": [],
        "action": action,
    }


def _runtime_lock_payload(*, action: str, generated_at: str) -> dict[str, Any]:
    host = socket.gethostname() or "unknown-host"
    pid = os.getpid()
    lease_until = _runtime_lock_lease_until(generated_at)
    owner_id = f"{host}:{pid}:{action}:{_id('runtime-lock-owner', generated_at)}"
    fencing_token = hashlib.sha256(f"{owner_id}|{lease_until}|{STAGE1_RUNTIME_MODEL_ID}".encode("utf-8")).hexdigest()[:24]
    return {
        "schema_version": STAGE1_RUNTIME_SCHEMA_VERSION,
        "model_id": STAGE1_RUNTIME_MODEL_ID,
        "action": action,
        "generated_at": generated_at,
        "owner_id": owner_id,
        "host": host,
        "pid": pid,
        "lease_seconds": STAGE1_RUNTIME_LOCK_LEASE_SECONDS,
        "lease_until": lease_until,
        "fencing_token": fencing_token,
    }


def _runtime_lock_lease_until(generated_at: str) -> str:
    base = _parse_datetime(generated_at) or datetime.now(timezone.utc)
    return (base + timedelta(seconds=STAGE1_RUNTIME_LOCK_LEASE_SECONDS)).isoformat()


def _renew_runtime_lock(lock_state: dict[str, Any], *, generated_at: str) -> None:
    if not lock_state.get("acquired"):
        return
    lock_path = Path(str(lock_state["path"]))
    payload = dict(lock_state["payload"])
    current = _read_runtime_lock_payload(lock_path)
    if current.get("fencing_token") != payload.get("fencing_token"):
        raise Stage1RuntimeError("runtime lock fencing token mismatch during renew")
    payload["lease_until"] = _runtime_lock_lease_until(generated_at)
    lock_path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    lock_state["payload"] = payload
    lock_state["renewals"].append({"renewed_at": generated_at, "lease_until": payload["lease_until"]})


def _take_over_stale_runtime_lock(lock_path: Path, *, generated_at: str) -> dict[str, Any]:
    takeover = {
        "attempted": lock_path.exists(),
        "performed": False,
        "reason": "no existing runtime lock",
        "previous_owner_id": None,
        "previous_pid": None,
        "previous_fencing_token": None,
    }
    if not lock_path.exists():
        return takeover
    previous = _read_runtime_lock_payload(lock_path)
    takeover.update(
        {
            "reason": "runtime lock is not safely takeable",
            "previous_owner_id": previous.get("owner_id"),
            "previous_pid": previous.get("pid"),
            "previous_fencing_token": previous.get("fencing_token"),
        }
    )
    if not _runtime_lock_is_stale(lock_path, previous, generated_at=generated_at):
        takeover["reason"] = "runtime lock lease has not expired"
        return takeover
    if _runtime_lock_process_alive(previous.get("pid")):
        takeover["reason"] = "runtime lock owner process is still alive"
        return takeover
    lock_path.unlink(missing_ok=True)
    takeover["performed"] = True
    takeover["reason"] = "stale runtime lock with dead owner was taken over"
    return takeover


def _read_runtime_lock_payload(lock_path: Path) -> dict[str, Any]:
    try:
        value = json.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if isinstance(value, dict):
        return value
    return {}


def _runtime_lock_is_stale(lock_path: Path, payload: Mapping[str, Any], *, generated_at: str) -> bool:
    now = _parse_datetime(generated_at)
    lease_until = _parse_datetime(str(payload.get("lease_until") or ""))
    if now is not None and lease_until is not None:
        return now >= lease_until
    lock_age = _mtime_age_seconds(lock_path, generated_at)
    return lock_age is None or lock_age > STAGE1_RUNTIME_STALE_AFTER_SECONDS


def _runtime_lock_process_alive(raw_pid: Any) -> bool:
    try:
        pid = int(raw_pid)
    except (TypeError, ValueError):
        return False
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return True
    return True


def _scheduler_templates(platform: str, project_root: Path, state_dir: Path, *, generated_at: str, uninstall: bool) -> list[dict[str, str]]:
    if platform == "macos":
        label = "com.linze.adp.stage1"
        if uninstall:
            content = f"launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/{label}.tick.plist\n"
            return [{"filename": "macos-uninstall.sh", "content": content, "task": "uninstall"}]
        content = _macos_launchd_tick_plist(label=label, project_root=project_root, state_dir=state_dir, generated_at=generated_at)
        return [{"filename": f"{label}.tick.plist", "content": content, "task": "tick"}]
    if platform == "linux":
        if uninstall:
            return [{"filename": "linux-uninstall.sh", "content": "systemctl --user disable --now adp-stage1.tick.timer\n", "task": "uninstall"}]
        env_path = "%h/.config/arxiv-daily-push/adp-stage1.env"
        service = _linux_systemd_tick_service(project_root=project_root, state_dir=state_dir, environment_file=env_path)
        env = _linux_systemd_environment(project_root=project_root, generated_at=generated_at)
        timer = "[Timer]\nOnBootSec=5min\nOnUnitActiveSec=30min\nPersistent=true\n"
        return [
            {"filename": "adp-stage1.env", "content": env, "task": "tick"},
            {"filename": "adp-stage1-tick.service", "content": service, "task": "tick"},
            {"filename": "adp-stage1-tick.timer", "content": timer, "task": "tick"},
        ]
    if uninstall:
        return [{"filename": "windows-uninstall.ps1", "content": "Unregister-ScheduledTask -TaskName 'ADP Stage1 Tick' -Confirm:$false\n", "task": "uninstall"}]
    ps = _windows_scheduler_tick_script(state_dir=state_dir)
    return [{"filename": "windows-install.ps1", "content": ps, "task": "tick"}]


def _macos_launchd_tick_plist(*, label: str, project_root: Path, state_dir: Path, generated_at: str) -> str:
    payload = {
        "Label": f"{label}.tick",
        "Disabled": True,
        "StartInterval": 1800,
        "WorkingDirectory": str(project_root),
        "EnvironmentVariables": {
            "PYTHONPATH": str(project_root / "arxiv-daily-push" / "src"),
        },
        "ProgramArguments": [
            "python3",
            "-m",
            "arxiv_daily_push",
            "tick",
            "--state-dir",
            str(state_dir),
            "--generated-at",
            generated_at,
            "--json",
        ],
    }
    return plistlib.dumps(payload, fmt=plistlib.FMT_XML, sort_keys=False).decode("utf-8")


def _linux_systemd_tick_service(*, project_root: Path, state_dir: Path, environment_file: str) -> str:
    args = [
        "/usr/bin/env",
        "python3",
        "-m",
        "arxiv_daily_push",
        "tick",
        "--state-dir",
        str(state_dir),
        "--generated-at",
        "${ADP_GENERATED_AT}",
        "--json",
    ]
    return "\n".join(
        [
            "[Unit]",
            "Description=ADP Stage 1 tick dry-run template",
            "",
            "[Service]",
            "Type=oneshot",
            f"WorkingDirectory={_systemd_unit_value(str(project_root))}",
            f"EnvironmentFile={_systemd_unit_value(environment_file)}",
            "ExecStart=" + " ".join(_systemd_exec_arg(arg) for arg in args),
            "",
        ]
    )


def _linux_systemd_environment(*, project_root: Path, generated_at: str) -> str:
    return "\n".join(
        [
            "# Dry-run template only; copy to ~/.config/arxiv-daily-push/adp-stage1.env before any real scheduler install.",
            f"PYTHONPATH={_systemd_env_value(str(project_root / 'arxiv-daily-push' / 'src'))}",
            f"ADP_GENERATED_AT={_systemd_env_value(generated_at)}",
            "",
        ]
    )


def _windows_scheduler_tick_script(*, state_dir: Path) -> str:
    args = [
        "-m",
        "arxiv_daily_push",
        "tick",
        "--state-dir",
        str(state_dir),
        "--generated-at",
        "$env:ADP_GENERATED_AT",
        "--json",
    ]
    arg_lines = "\n".join(
        f"  {_powershell_single_quote(arg)}{',' if index < len(args) - 1 else ''}"
        for index, arg in enumerate(args)
    )
    return "\n".join(
        [
            "function Join-CommandArgument([string[]]$Arguments) {",
            "  ($Arguments | ForEach-Object {",
            "    $escaped = $_ -replace '\"', '\\\"'",
            "    if ($escaped -match '[\\s;&\"]') { '\"' + $escaped + '\"' } else { $escaped }",
            "  }) -join ' '",
            "}",
            "$ArgumentList = @(",
            arg_lines,
            ")",
            "$Action = New-ScheduledTaskAction -Execute 'python3' -Argument (Join-CommandArgument $ArgumentList)",
            "$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 30)",
            "# Dry-run template only; do not register on the current low-resource machine.",
            "",
        ]
    )


def _systemd_unit_value(value: str) -> str:
    if not value or any(char.isspace() or char in {'"', '\\'} for char in value):
        return _systemd_exec_arg(value)
    return value


def _systemd_exec_arg(value: str) -> str:
    if value and not any(char.isspace() or char in {'"', '\\', ';', '&'} for char in value):
        return value
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _systemd_env_value(value: str) -> str:
    cleaned = value.replace("\n", "")
    if cleaned and not any(char.isspace() or char in {'"', '\\', ';', '&', '#'} for char in cleaned):
        return cleaned
    return '"' + cleaned.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _powershell_single_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _manifest_file(role: str, path: Path, *, source_path: Path) -> dict[str, Any]:
    return {
        "role": role,
        "path": str(path.relative_to(path.parent.parent if role == "supporting_file" else path.parent)),
        "source_path": str(source_path),
        "size_bytes": path.stat().st_size,
        "sha256": _sha256_file(path),
    }


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise Stage1RuntimeError(f"{path} must contain a JSON object")
    return value


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _supporting_file_backup_name(path: Path) -> str:
    source_key = str(path.resolve())
    digest = hashlib.sha256(source_key.encode("utf-8")).hexdigest()[:12]
    return f"{digest}-{path.name}"


def _safe_manifest_backup_path(raw_path: Any, *, backup_root: Path) -> Path:
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise Stage1RuntimeError("backup database path is empty or not a string")
    posix_path = PurePosixPath(raw_path)
    if posix_path.is_absolute() or any(part in {"", ".", ".."} for part in posix_path.parts):
        raise Stage1RuntimeError("backup database path traversal is not allowed")
    root = backup_root.resolve(strict=True)
    candidate = backup_root.joinpath(*posix_path.parts)
    if not candidate.exists():
        return candidate
    resolved = candidate.resolve(strict=True)
    if not resolved.is_relative_to(root):
        raise Stage1RuntimeError("backup database path escapes backup root")
    return resolved


def _fsync_file(path: Path) -> None:
    with path.open("rb") as handle:
        os.fsync(handle.fileno())


def _fsync_directory(path: Path) -> None:
    try:
        fd = os.open(path, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(fd)
    except OSError:
        pass
    finally:
        os.close(fd)


def _id(prefix: str, generated_at: str) -> str:
    digest = hashlib.sha256(f"{prefix}|{generated_at}|{STAGE1_RUNTIME_MODEL_ID}".encode("utf-8")).hexdigest()[:12]
    return f"{prefix}-{digest}"


def _age_seconds(older_iso: str, newer_iso: str) -> int | None:
    older = _parse_datetime(older_iso)
    newer = _parse_datetime(newer_iso)
    if older is None or newer is None:
        return None
    return max(0, int((newer - older).total_seconds()))


def _mtime_age_seconds(path: Path, newer_iso: str) -> int | None:
    newer = _parse_datetime(newer_iso)
    if newer is None:
        return None
    mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    return max(0, int((newer - mtime).total_seconds()))


def _parse_datetime(value: str) -> datetime | None:
    try:
        normalized = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)
