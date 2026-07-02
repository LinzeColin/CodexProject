#!/usr/bin/env python3
"""Fail-closed ADP S3 DAILY_OPERATION enablement preflight.

This root tool is intentionally read-only. It combines the DAILY_OPERATION
readiness gate with the runtime boundary checks that must remain safe before a
future owner-authorized persistent enablement run. It never writes
authorization artifacts and never enables SMTP, scheduler, Release, or restore.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


AUTHORIZATION_ARTIFACT_REF = "FINAL_ACCEPTANCE_BUNDLE/daily_operation_persistent_enablement_authorization.json"
GITHUB_OPEN_PULLS_API_URL = "https://api.github.com/repos/LinzeColin/CodexProject/pulls?state=open&per_page=100"
REQUIRED_LAUNCHAGENTS = (
    "com.linzezhang.adp.daily",
    "com.linzezhang.adp.health",
    "com.linzezhang.adp.watchdog",
)
FALSE_LIKE_VALUES = {"", "0", "false", "no", "off", "unset", "none"}
BACKGROUND_PROCESS_MARKERS = (
    "arxiv_daily_push",
    "arxiv-daily-push",
)
BACKGROUND_RUN_MARKERS = (
    "local-runner",
    "local_runner",
    "run-local-daily",
    "run-scheduled-production",
    "scheduled-production",
    "watchdog",
)
OBSERVATION_TOOL_MARKERS = (
    "verify_daily_operation_enablement_preflight.py",
    "verify_daily_operation_readiness.py",
    "unittest",
    "pytest",
)


def _parse_bool(value: str, *, arg_name: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise argparse.ArgumentTypeError(f"{arg_name} must be true or false")


def _is_false_like(value: str | None) -> bool:
    raw = "UNSET" if value is None else value
    return raw.strip().lower() in FALSE_LIKE_VALUES


def _load_readiness_report(root: Path, generated_at: str | None) -> dict[str, Any]:
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from tools.verify_daily_operation_readiness import build_readiness_report  # noqa: PLC0415

    return build_readiness_report(root, generated_at=generated_at)


def _launchagent_is_disabled_or_not_loaded(label: str) -> tuple[bool, str | None]:
    launchctl = "/bin/launchctl"
    if not Path(launchctl).exists():
        return True, None
    uid = os.getuid()
    completed = subprocess.run(
        [launchctl, "print", f"gui/{uid}/{label}"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        return True, None
    output = completed.stdout.lower()
    if "disabled = true" in output or "disabled = 1" in output:
        return True, None
    return False, None


def _is_adp_background_process(command: str) -> bool:
    normalized = command.lower()
    if any(marker in normalized for marker in OBSERVATION_TOOL_MARKERS):
        return False
    if not any(marker in normalized for marker in BACKGROUND_PROCESS_MARKERS):
        return False
    return any(marker in normalized for marker in BACKGROUND_RUN_MARKERS)


def _observe_background_adp_process_count() -> tuple[int | None, str | None]:
    completed = subprocess.run(
        ["/bin/ps", "-axo", "pid=,command="],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        return None, "background_process_observation_failed"
    count = sum(1 for line in completed.stdout.splitlines() if _is_adp_background_process(line))
    return count, None


def observe_runtime_boundary() -> tuple[dict[str, bool], int | None, list[str]]:
    errors: list[str] = []
    launchagent_states: dict[str, bool] = {}
    for label in REQUIRED_LAUNCHAGENTS:
        disabled, error = _launchagent_is_disabled_or_not_loaded(label)
        launchagent_states[label] = disabled
        if error:
            errors.append(error)
    process_count, process_error = _observe_background_adp_process_count()
    if process_error:
        errors.append(process_error)
    return launchagent_states, process_count, _unique_reasons(errors)


def _observe_open_pr_count() -> tuple[int | None, list[str]]:
    curl = Path("/usr/bin/curl")
    if not curl.exists():
        return None, ["open_pr_count_observation_tool_missing"]
    try:
        completed = subprocess.run(
            [
                str(curl),
                "-sSfL",
                "-H",
                "Accept: application/vnd.github+json",
                "-H",
                "User-Agent: codex-adp-open-pr-check",
                GITHUB_OPEN_PULLS_API_URL,
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None, ["open_pr_count_observation_failed"]
    if completed.returncode != 0:
        return None, ["open_pr_count_observation_failed"]
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return None, ["open_pr_count_observation_json_invalid"]
    if not isinstance(payload, list):
        return None, ["open_pr_count_observation_payload_invalid"]
    return len(payload), []


def _unique_reasons(reasons: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for reason in reasons:
        if reason and reason not in seen:
            seen.add(reason)
            unique.append(reason)
    return unique


def build_enablement_preflight_report(
    root: Path,
    *,
    generated_at: str | None = None,
    open_pr_count: int | None = None,
    adp_allow_smtp_send: str | None = None,
    launchagent_disabled_states: dict[str, bool],
    background_adp_process_count: int | None = None,
    runtime_observation_mode: str = "provided",
    runtime_observation_errors: list[str] | None = None,
    open_pr_observation_mode: str = "provided",
    open_pr_observation_errors: list[str] | None = None,
) -> dict[str, Any]:
    generated = generated_at or datetime.now(timezone.utc).isoformat()
    readiness = _load_readiness_report(root, generated)
    environment_smtp_send = os.environ.get("ADP_ALLOW_SMTP_SEND", "UNSET")
    raw_smtp_send = environment_smtp_send if adp_allow_smtp_send is None else adp_allow_smtp_send
    runtime_flags = {
        "daily_operation_enabled": readiness.get("daily_operation_enabled") is True,
        "real_smtp_send_enabled": readiness.get("real_smtp_send_enabled") is True,
        "scheduler_install_enabled": readiness.get("scheduler_install_enabled") is True,
        "release_packaging_enabled": readiness.get("release_packaging_enabled") is True,
        "production_restore_enabled": readiness.get("production_restore_enabled") is True,
    }
    runtime_enablement_detected = readiness.get("runtime_enablement_detected") is True or any(runtime_flags.values())
    checks = {
        "daily_operation_readiness_passed": (
            readiness.get("status") == "PASS" and readiness.get("daily_operation_ready") is True
        ),
        "open_pr_count_zero": open_pr_count == 0,
        "adp_allow_smtp_send_false_like": _is_false_like(raw_smtp_send) and _is_false_like(environment_smtp_send),
        "launchagents_disabled": all(launchagent_disabled_states.get(label) is True for label in REQUIRED_LAUNCHAGENTS),
        "background_adp_process_count_zero": background_adp_process_count == 0,
        "runtime_enablement_absent": not runtime_enablement_detected,
    }

    blocking_reasons: list[str] = []
    if not checks["daily_operation_readiness_passed"]:
        blocking_reasons.extend(str(reason) for reason in readiness.get("blocking_reasons", []) if reason)
    if not checks["open_pr_count_zero"]:
        blocking_reasons.append("open_pr_count_not_zero_or_unknown")
    if not checks["adp_allow_smtp_send_false_like"]:
        blocking_reasons.append("adp_allow_smtp_send_truthy_or_unknown")
    if not checks["launchagents_disabled"]:
        blocking_reasons.append("launchagents_not_all_disabled_or_unknown")
    if not checks["background_adp_process_count_zero"]:
        blocking_reasons.append("background_adp_process_count_not_zero_or_unknown")
    if not checks["runtime_enablement_absent"]:
        blocking_reasons.append("runtime_enablement_detected")
    blocking_reasons = _unique_reasons(blocking_reasons or ["daily_operation_enablement_preflight_not_satisfied"])

    enablement_preflight_ready = all(checks.values())
    return {
        "status": "PASS" if enablement_preflight_ready else "FAIL",
        "scope": "adp_s3_daily_operation_enablement_preflight_fail_closed_no_runtime_enablement",
        "contract_id": "ADP-PRODUCT-CONTRACT-V7.2",
        "task_id": "S2PMT07-DAILY-OPERATION-ENABLEMENT-PREFLIGHT",
        "generated_at": generated,
        "enablement_preflight_ready": enablement_preflight_ready,
        "checks": checks,
        "blocking_reasons": [] if enablement_preflight_ready else blocking_reasons,
        "readiness_status": readiness.get("status"),
        "readiness_blocking_reasons": readiness.get("blocking_reasons", []),
        "daily_operation_ready": readiness.get("daily_operation_ready") is True,
        "persistent_daily_operation_authorized": readiness.get("persistent_daily_operation_authorized") is True,
        "authorization_artifact": readiness.get("authorization_artifact", AUTHORIZATION_ARTIFACT_REF),
        "next_required_step": readiness.get("next_required_step"),
        "next_executable_task": readiness.get("next_executable_task"),
        "open_pr_count": open_pr_count,
        "open_pr_observation_mode": open_pr_observation_mode,
        "open_pr_observation_errors": open_pr_observation_errors or [],
        "adp_allow_smtp_send_raw": raw_smtp_send,
        "adp_allow_smtp_send_environment_raw": environment_smtp_send,
        "launchagent_disabled_states": {label: launchagent_disabled_states.get(label) is True for label in REQUIRED_LAUNCHAGENTS},
        "background_adp_process_count": background_adp_process_count,
        "runtime_observation_mode": runtime_observation_mode,
        "runtime_observation_errors": runtime_observation_errors or [],
        "runtime_enablement_detected": runtime_enablement_detected,
        **runtime_flags,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="CodexProject repository root.")
    parser.add_argument("--generated-at", default=None, help="Optional timestamp for deterministic reports.")
    parser.add_argument(
        "--open-pr-count",
        type=int,
        default=None,
        help="Observed GitHub open PR count. Defaults to a read-only GitHub API observation.",
    )
    parser.add_argument(
        "--adp-allow-smtp-send",
        default=None,
        help="Observed raw ADP_ALLOW_SMTP_SEND value. Defaults to the current environment or UNSET.",
    )
    parser.add_argument(
        "--launchagent-daily-disabled",
        default=None,
        type=lambda value: _parse_bool(value, arg_name="--launchagent-daily-disabled"),
        help="Whether com.linzezhang.adp.daily is disabled or not loaded.",
    )
    parser.add_argument(
        "--launchagent-health-disabled",
        default=None,
        type=lambda value: _parse_bool(value, arg_name="--launchagent-health-disabled"),
        help="Whether com.linzezhang.adp.health is disabled or not loaded.",
    )
    parser.add_argument(
        "--launchagent-watchdog-disabled",
        default=None,
        type=lambda value: _parse_bool(value, arg_name="--launchagent-watchdog-disabled"),
        help="Whether com.linzezhang.adp.watchdog is disabled or not loaded.",
    )
    parser.add_argument(
        "--background-adp-process-count",
        type=int,
        default=None,
        help="Observed ADP runner/module/path background process count.",
    )
    args = parser.parse_args(argv)
    provided_states = {
        "com.linzezhang.adp.daily": args.launchagent_daily_disabled,
        "com.linzezhang.adp.health": args.launchagent_health_disabled,
        "com.linzezhang.adp.watchdog": args.launchagent_watchdog_disabled,
    }
    provided_complete = all(value is not None for value in provided_states.values()) and (
        args.background_adp_process_count is not None
    )
    observed_states: dict[str, bool] = {}
    observed_process_count: int | None = None
    observation_errors: list[str] = []
    if not provided_complete:
        observed_states, observed_process_count, observation_errors = observe_runtime_boundary()
    launchagent_states = {
        label: bool(value) if value is not None else observed_states.get(label, False)
        for label, value in provided_states.items()
    }
    process_count = (
        args.background_adp_process_count
        if args.background_adp_process_count is not None
        else observed_process_count
    )
    if provided_complete:
        observation_mode = "provided"
    elif all(value is None for value in provided_states.values()) and args.background_adp_process_count is None:
        observation_mode = "auto_observed"
    else:
        observation_mode = "mixed"
    if args.open_pr_count is None:
        open_pr_count, open_pr_errors = _observe_open_pr_count()
        open_pr_observation_mode = "auto_observed"
    else:
        open_pr_count = args.open_pr_count
        open_pr_errors = []
        open_pr_observation_mode = "provided"
    report = build_enablement_preflight_report(
        Path(args.root).resolve(),
        generated_at=args.generated_at,
        open_pr_count=open_pr_count,
        adp_allow_smtp_send=args.adp_allow_smtp_send,
        launchagent_disabled_states=launchagent_states,
        background_adp_process_count=process_count,
        runtime_observation_mode=observation_mode,
        runtime_observation_errors=observation_errors,
        open_pr_observation_mode=open_pr_observation_mode,
        open_pr_observation_errors=open_pr_errors,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
