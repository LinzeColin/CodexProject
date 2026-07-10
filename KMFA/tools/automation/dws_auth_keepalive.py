#!/usr/bin/env python3
"""Deterministic DWS access-token keepalive without interactive login."""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import shutil
import subprocess
import tempfile
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


AUTOMATION_DIR = Path(
    "/Users/linzezhang/.codex/automations/dws-auth-keepalive-2"
)
DEFAULT_PROFILE_CONFIG = AUTOMATION_DIR / "expected_profile.json"
DEFAULT_LEDGER_PATH = AUTOMATION_DIR / "memory.md"
DEFAULT_STATE_PATH = AUTOMATION_DIR / "state.json"
LEDGER_HEADER = "# DWS Auth Keepalive Memory v2\n"
MAX_LEDGER_RUNS = 24
MANUAL_AUTH_COMMAND = (
    "cd /Users/linzezhang/Documents/Codex/2026-07-04/"
    "392b1a986ba680338068ddc1c2a0fd0e-https-app-notion-com-p "
    "&& DWS_KEEPALIVE_PROFILE=$(python3 -c 'import json; "
    "print(json.load(open(\"/Users/linzezhang/.codex/automations/"
    "dws-auth-keepalive-2/expected_profile.json\"))[\"profile\"])') "
    "&& dws auth login --device --profile \"$DWS_KEEPALIVE_PROFILE\""
)


class CommandFailure(RuntimeError):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


def emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))


def run_json(command: list[str], timeout_seconds: float) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        raise CommandFailure("COMMAND_TIMEOUT") from exc
    except OSError as exc:
        raise CommandFailure("COMMAND_START_FAILED") from exc

    if completed.returncode != 0:
        raise CommandFailure(f"COMMAND_EXIT_{completed.returncode}")
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise CommandFailure("MALFORMED_JSON") from exc
    if not isinstance(payload, dict):
        raise CommandFailure("JSON_NOT_OBJECT")
    return payload


def secure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(path.parent, 0o700)


def atomic_write(path: Path, content: str) -> None:
    secure_parent(path)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        dir=str(path.parent),
        text=True,
    )
    temporary_path = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
        os.chmod(path, 0o600)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


@contextmanager
def exclusive_lock(path: Path) -> Iterator[None]:
    secure_parent(path)
    with path.open("a+", encoding="utf-8") as handle:
        os.chmod(path, 0o600)
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def load_expected_profile(path: Path) -> str:
    if not path.is_file():
        raise CommandFailure("PROFILE_CONFIG_MISSING")
    os.chmod(path, 0o600)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CommandFailure("PROFILE_CONFIG_INVALID") from exc
    if not isinstance(payload, dict):
        raise CommandFailure("PROFILE_CONFIG_INVALID")
    profile = payload.get("profile")
    if not isinstance(profile, str) or not profile.strip():
        raise CommandFailure("PROFILE_CONFIG_INVALID")
    return profile.strip()


def bootstrap_current_profile(
    dws_bin: str,
    profile_config: Path,
    command_timeout_seconds: float,
    dws_timeout_seconds: int,
) -> dict[str, Any]:
    payload = run_json(
        [
            dws_bin,
            "profile",
            "list",
            "--format",
            "json",
            "--timeout",
            str(dws_timeout_seconds),
        ],
        command_timeout_seconds,
    )
    current = payload.get("currentProfile")
    profiles = payload.get("profiles")
    if payload.get("success") is not True or not isinstance(current, str) or not current:
        raise CommandFailure("CURRENT_PROFILE_UNAVAILABLE")
    if not isinstance(profiles, list):
        raise CommandFailure("CURRENT_PROFILE_UNAVAILABLE")
    matching = [
        item
        for item in profiles
        if isinstance(item, dict)
        and item.get("corpId") == current
        and item.get("isCurrent") is True
    ]
    if len(matching) != 1:
        raise CommandFailure("CURRENT_PROFILE_UNAVAILABLE")
    atomic_write(
        profile_config,
        json.dumps({"version": 1, "profile": current}, sort_keys=True) + "\n",
    )
    return {
        "status": "profile_pinned",
        "profile_match": True,
        "next_action": "run_keepalive",
    }


def doctor_summary(
    dws_bin: str,
    profile: str,
    command_timeout_seconds: float,
    dws_timeout_seconds: int,
) -> dict[str, Any]:
    try:
        payload = run_json(
            [
                dws_bin,
                "doctor",
                "--json",
                "--profile",
                profile,
                "--timeout",
                str(dws_timeout_seconds),
            ],
            command_timeout_seconds,
        )
    except CommandFailure as exc:
        return {"status": "unavailable", "reason": exc.reason}
    summary = payload.get("summary")
    if not isinstance(summary, dict):
        return {"status": "unavailable", "reason": "DOCTOR_SUMMARY_MISSING"}
    counts = [summary.get(key) for key in ("pass", "warn", "fail")]
    if any(not isinstance(value, int) or isinstance(value, bool) for value in counts):
        return {"status": "unavailable", "reason": "DOCTOR_SUMMARY_INVALID"}
    pass_count, warn_count, fail_count = counts
    return {
        "status": "ok" if fail_count == 0 else "failed",
        "pass": pass_count,
        "warn": warn_count,
        "fail": fail_count,
    }


def parse_aware_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed


def expiry_gate(auth: dict[str, Any], now: datetime) -> str | None:
    access_expiry = parse_aware_timestamp(auth.get("expires_at"))
    refresh_expiry = parse_aware_timestamp(auth.get("refresh_expires_at"))
    if access_expiry is None:
        return "ACCESS_EXPIRY_INVALID"
    if refresh_expiry is None:
        return "REFRESH_EXPIRY_INVALID"
    if access_expiry <= now:
        return "ACCESS_EXPIRY_NOT_FUTURE"
    if refresh_expiry <= now:
        return "REFRESH_EXPIRY_NOT_FUTURE"
    return None


def next_action(status: str, reason: str | None) -> str:
    if status in {"auto_refresh_failed", "needs_manual_auth"}:
        return MANUAL_AUTH_COMMAND
    if reason in {"PROFILE_CONFIG_MISSING", "PROFILE_CONFIG_INVALID"}:
        return "pin_expected_profile"
    if reason == "PROFILE_MISMATCH":
        return "restore_expected_dws_profile"
    if reason and reason.startswith("DOCTOR_"):
        return "inspect_dws_doctor"
    if status == "blocked":
        return "inspect_dws_runtime"
    return "continue_monitoring"


def result_payload(
    status: str,
    auth: dict[str, Any],
    attempts_used: int,
    *,
    reason: str | None = None,
    doctor: dict[str, Any] | None = None,
    profile_match: bool | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "status": status,
        "authenticated": auth.get("authenticated") is True,
        "token_valid": auth.get("token_valid") is True,
        "refresh_token_valid": auth.get("refresh_token_valid") is True,
        "refreshed": auth.get("refreshed") is True,
        "profile_match": profile_match,
        "access_expires_at": auth.get("expires_at"),
        "refresh_expires_at": auth.get("refresh_expires_at"),
        "attempts_used": attempts_used,
        "doctor": doctor,
    }
    if reason:
        payload["reason"] = reason
    payload["next_action"] = next_action(status, reason)
    return payload


def check_keepalive(
    dws_bin: str,
    expected_profile: str,
    attempts: int,
    backoff_seconds: float,
    command_timeout_seconds: float,
    dws_timeout_seconds: int,
    now: datetime,
) -> tuple[int, dict[str, Any]]:
    last_auth: dict[str, Any] = {}
    last_reason: str | None = None
    last_profile_match: bool | None = None

    for attempt in range(1, attempts + 1):
        try:
            auth = run_json(
                [
                    dws_bin,
                    "auth",
                    "status",
                    "--format",
                    "json",
                    "--profile",
                    expected_profile,
                    "--timeout",
                    str(dws_timeout_seconds),
                ],
                command_timeout_seconds,
            )
        except CommandFailure as exc:
            last_reason = exc.reason
            auth = {}
        else:
            last_reason = None
        last_auth = auth

        corp_id = auth.get("corp_id")
        if isinstance(corp_id, str) and corp_id:
            last_profile_match = corp_id == expected_profile
            if not last_profile_match:
                return 2, result_payload(
                    "blocked",
                    auth,
                    attempt,
                    reason="PROFILE_MISMATCH",
                    profile_match=False,
                )

        if auth.get("refresh_token_valid") is False:
            return 4, result_payload(
                "needs_manual_auth",
                auth,
                attempt,
                reason="REFRESH_TOKEN_INVALID",
                profile_match=last_profile_match,
            )

        if auth.get("token_valid") is True:
            if not all(
                auth.get(field) is True
                for field in ("success", "authenticated", "refresh_token_valid")
            ) or last_profile_match is not True:
                return 2, result_payload(
                    "blocked",
                    auth,
                    attempt,
                    reason="AUTH_STATUS_INCONSISTENT",
                    profile_match=last_profile_match,
                )
            expiry_reason = expiry_gate(auth, now)
            if expiry_reason:
                return 2, result_payload(
                    "blocked",
                    auth,
                    attempt,
                    reason=expiry_reason,
                    profile_match=True,
                )
            doctor = doctor_summary(
                dws_bin,
                expected_profile,
                command_timeout_seconds,
                dws_timeout_seconds,
            )
            if doctor.get("status") != "ok":
                doctor_reason = doctor.get("reason")
                reason = (
                    doctor_reason
                    if isinstance(doctor_reason, str) and doctor_reason
                    else "DOCTOR_FAILED"
                )
                return 2, result_payload(
                    "blocked",
                    auth,
                    attempt,
                    reason=reason,
                    doctor=doctor,
                    profile_match=True,
                )
            status = "refreshed" if auth.get("refreshed") is True else "healthy"
            return 0, result_payload(
                status,
                auth,
                attempt,
                doctor=doctor,
                profile_match=True,
            )

        if auth and (
            auth.get("success") is False or auth.get("authenticated") is False
        ):
            return 2, result_payload(
                "blocked",
                auth,
                attempt,
                reason="AUTH_STATUS_INCONSISTENT",
                profile_match=last_profile_match,
            )

        if attempt < attempts and backoff_seconds > 0:
            time.sleep(backoff_seconds)

    if last_auth.get("refresh_token_valid") is True:
        return 3, result_payload(
            "auto_refresh_failed",
            last_auth,
            attempts,
            reason=last_reason or "TOKEN_VALID_NOT_TRUE_AFTER_REFRESH_ATTEMPTS",
            profile_match=last_profile_match,
        )
    return 2, result_payload(
        "blocked",
        last_auth,
        attempts,
        reason=last_reason or "AUTH_STATUS_UNAVAILABLE",
        profile_match=last_profile_match,
    )


def reminder_window(refresh_expires_at: Any, now: datetime) -> tuple[str, int | None]:
    expiry = parse_aware_timestamp(refresh_expires_at)
    if expiry is None:
        return "unknown", None
    remaining = int((expiry - now).total_seconds())
    if remaining <= 0:
        return "expired", remaining
    if remaining <= 4 * 60 * 60:
        return "last_4h", remaining
    if remaining <= 24 * 60 * 60:
        return "within_24h", remaining
    return "none", remaining


def load_state(path: Path) -> tuple[dict[str, Any], bool]:
    if not path.exists():
        return {}, False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}, True
    if not isinstance(payload, dict):
        return {}, True
    return payload, False


def safe_run_record(payload: dict[str, Any], run_at: str) -> dict[str, Any]:
    allowed = (
        "status",
        "authenticated",
        "token_valid",
        "refresh_token_valid",
        "refreshed",
        "profile_match",
        "access_expires_at",
        "refresh_expires_at",
        "attempts_used",
        "doctor",
        "reason",
        "reminder_window",
        "reminder_due",
        "notification_required",
        "next_action",
    )
    record = {"run_at": run_at}
    record.update({key: payload.get(key) for key in allowed if key in payload})
    return record


def persist_sanitized_ledger(
    payload: dict[str, Any],
    ledger_path: Path,
    state_path: Path,
    now: datetime,
) -> dict[str, Any]:
    state, recovered = load_state(state_path)
    window, remaining = reminder_window(payload.get("refresh_expires_at"), now)
    refresh_expiry = payload.get("refresh_expires_at")
    marker = f"{refresh_expiry}|{window}"
    expiry_reminder_due = (
        window in {"within_24h", "last_4h", "expired"}
        and state.get("last_reminder_marker") != marker
    )
    failure_status = payload.get("status") in {
        "auto_refresh_failed",
        "needs_manual_auth",
        "blocked",
    }
    failure_reminder_due = failure_status and state.get("last_status") != payload.get(
        "status"
    )
    payload["reminder_window"] = window
    payload["refresh_remaining_seconds"] = remaining
    payload["reminder_due"] = expiry_reminder_due
    payload["notification_required"] = expiry_reminder_due or failure_reminder_due
    payload["ledger_recovered"] = recovered

    run_at = now.astimezone(timezone.utc).isoformat()
    recent_runs = state.get("recent_runs")
    if not isinstance(recent_runs, list):
        recent_runs = []
    recent_runs = [item for item in recent_runs if isinstance(item, dict)]
    recent_runs.append(safe_run_record(payload, run_at))
    recent_runs = recent_runs[-MAX_LEDGER_RUNS:]

    if ledger_path.exists():
        try:
            existing = ledger_path.read_text(encoding="utf-8")
        except OSError:
            existing = ""
        if existing and not existing.startswith(LEDGER_HEADER):
            legacy_path = ledger_path.with_name("memory.legacy-private.md")
            if not legacy_path.exists():
                atomic_write(legacy_path, existing)

    new_state: dict[str, Any] = {
        "version": 2,
        "last_status": payload.get("status"),
        "last_refresh_expires_at": refresh_expiry,
        "recent_runs": recent_runs,
    }
    if expiry_reminder_due:
        new_state["last_reminder_marker"] = marker
    elif isinstance(state.get("last_reminder_marker"), str):
        new_state["last_reminder_marker"] = state["last_reminder_marker"]

    atomic_write(
        state_path,
        json.dumps(new_state, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
    )
    ledger_lines = [LEDGER_HEADER.rstrip("\n"), ""]
    ledger_lines.extend(
        json.dumps(item, ensure_ascii=False, sort_keys=True) for item in recent_runs
    )
    atomic_write(ledger_path, "\n".join(ledger_lines) + "\n")
    payload["ledger_written"] = True
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dws-bin", default="dws")
    parser.add_argument("--attempts", type=int, default=3)
    parser.add_argument("--backoff-seconds", type=float, default=5.0)
    parser.add_argument("--command-timeout-seconds", type=float, default=25.0)
    parser.add_argument("--dws-timeout-seconds", type=int, default=20)
    parser.add_argument("--profile-config", type=Path, default=DEFAULT_PROFILE_CONFIG)
    parser.add_argument("--ledger-path", type=Path, default=DEFAULT_LEDGER_PATH)
    parser.add_argument("--state-path", type=Path, default=DEFAULT_STATE_PATH)
    parser.add_argument("--bootstrap-current-profile", action="store_true")
    args = parser.parse_args()

    if args.attempts < 1:
        parser.error("--attempts must be at least 1")
    if args.backoff_seconds < 0 or args.command_timeout_seconds <= 0:
        parser.error("timeouts must be positive and backoff must not be negative")
    if args.dws_timeout_seconds < 1:
        parser.error("--dws-timeout-seconds must be at least 1")
    if args.command_timeout_seconds <= args.dws_timeout_seconds:
        parser.error("outer command timeout must exceed the DWS HTTP timeout")

    dws_bin = args.dws_bin
    if not Path(dws_bin).exists() and shutil.which(dws_bin) is None:
        emit(
            result_payload(
                "blocked",
                {},
                0,
                reason="DWS_BINARY_MISSING",
            )
        )
        return 2

    now = datetime.now(timezone.utc)
    lock_path = args.state_path.with_suffix(args.state_path.suffix + ".lock")
    with exclusive_lock(lock_path):
        if args.bootstrap_current_profile:
            try:
                payload = bootstrap_current_profile(
                    dws_bin,
                    args.profile_config,
                    args.command_timeout_seconds,
                    args.dws_timeout_seconds,
                )
            except CommandFailure as exc:
                emit(
                    result_payload(
                        "blocked",
                        {},
                        0,
                        reason=exc.reason,
                    )
                )
                return 2
            emit(payload)
            return 0

        try:
            expected_profile = load_expected_profile(args.profile_config)
        except CommandFailure as exc:
            exit_code = 2
            payload = result_payload(
                "blocked",
                {},
                0,
                reason=exc.reason,
            )
        else:
            exit_code, payload = check_keepalive(
                dws_bin,
                expected_profile,
                args.attempts,
                args.backoff_seconds,
                args.command_timeout_seconds,
                args.dws_timeout_seconds,
                now,
            )

        try:
            payload = persist_sanitized_ledger(
                payload,
                args.ledger_path,
                args.state_path,
                now,
            )
        except OSError:
            payload["status"] = "blocked"
            payload["reason"] = "LEDGER_WRITE_FAILED"
            payload["next_action"] = "repair_keepalive_ledger_permissions"
            payload["ledger_written"] = False
            exit_code = 2

    emit(payload)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
