#!/usr/bin/env python3
"""Fail-closed DWS guard for the KMFA 钉钉考勤 skill."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from KMFA.tools.dingtalk_attendance.secrets_loader import merged_runtime_env


DWS_COMMAND_ALLOW_ENV = "KMFA_DINGTALK_ATTENDANCE_ALLOW_DWS_COMMANDS"
DWS_BROWSER_POLICY_PATH_ENV = "KMFA_DINGTALK_ATTENDANCE_DWS_BROWSER_POLICY_PATH"
# legacy_read_only environment aliases; new configuration must not write these keys.
LEGACY_DWS_COMMAND_ALLOW_ENV = "KMFA_S19_ALLOW_DWS_COMMANDS"
LEGACY_DWS_BROWSER_POLICY_PATH_ENV = "KMFA_S19_DWS_BROWSER_POLICY_PATH"
DWS_AUTH_REQUIRED = "DWS_AUTH_REQUIRED"
DWS_BROWSER_POLICY_REQUIRED = "DWS_BROWSER_POLICY_REQUIRED"
DWS_ENV_CONFLICT = "DWS_ENV_CONFLICT"
DEFAULT_DWS_BROWSER_POLICY_PATH = Path.home() / ".dws" / "pat_policy.json"
_TRUTHY = {"1", "true", "yes", "y", "on", "confirmed", "allow"}


class DwsEnvironmentConflictError(ValueError):
    """Raised when current and deprecated environment keys disagree."""


def migrated_env_value(
    values: Mapping[str, str],
    *,
    current_key: str,
    legacy_key: str,
) -> tuple[str, str]:
    current = str(values.get(current_key) or "").strip()
    legacy = str(values.get(legacy_key) or "").strip()
    if current and legacy and current != legacy:
        raise DwsEnvironmentConflictError(f"conflicting values for {current_key} and deprecated alias")
    if current:
        return current, "current"
    if legacy:
        return legacy, "legacy_read_only"
    return "", "missing"


def dws_command_safety_status(
    *,
    env: Mapping[str, str] | None = None,
    allow_override: bool = False,
) -> dict[str, Any]:
    values = merged_runtime_env() if env is None else dict(env)
    try:
        allow_value, allow_source = migrated_env_value(
            values,
            current_key=DWS_COMMAND_ALLOW_ENV,
            legacy_key=LEGACY_DWS_COMMAND_ALLOW_ENV,
        )
    except DwsEnvironmentConflictError as exc:
        return {
            "status": DWS_ENV_CONFLICT,
            "dws_commands_allowed": False,
            "required_env": DWS_COMMAND_ALLOW_ENV,
            "browser_popup_prevention": False,
            "failure_reason": str(exc),
        }
    allowed = allow_override or allow_value.lower() in _TRUTHY
    browser_policy = dws_browser_policy_status(env=values)
    if browser_policy["status"] == DWS_ENV_CONFLICT:
        return {
            "status": DWS_ENV_CONFLICT,
            "dws_commands_allowed": False,
            "required_env": DWS_COMMAND_ALLOW_ENV,
            "browser_popup_prevention": False,
            "browser_policy": browser_policy,
            "failure_reason": str(browser_policy["failure_reason"]),
        }
    if allowed:
        if browser_policy["status"] != "READY":
            return {
                "status": DWS_BROWSER_POLICY_REQUIRED,
                "dws_commands_allowed": False,
                "required_env": DWS_COMMAND_ALLOW_ENV,
                "browser_popup_prevention": False,
                "browser_policy": browser_policy,
                "failure_reason": (
                    "DWS commands are blocked because PAT browser policy is not locked to openBrowser=false. "
                    "Run `dws pat browser-policy --enabled=false --format json --yes` before live collection."
                ),
            }
        return {
            "status": "READY",
            "dws_commands_allowed": True,
            "required_env": DWS_COMMAND_ALLOW_ENV,
            "environment_key_source": allow_source,
            "browser_popup_prevention": True,
            "browser_policy": browser_policy,
        }
    return {
        "status": DWS_AUTH_REQUIRED,
        "dws_commands_allowed": False,
        "required_env": DWS_COMMAND_ALLOW_ENV,
        "environment_key_source": allow_source,
        "browser_popup_prevention": True,
        "browser_policy": browser_policy,
        "failure_reason": (
            "DWS commands are blocked until DingTalk authorization is explicitly confirmed. "
            f"Set {DWS_COMMAND_ALLOW_ENV}=1 only after confirming the authorization state."
        ),
    }


def dws_commands_allowed(*, env: Mapping[str, str] | None = None, allow_override: bool = False) -> bool:
    return bool(dws_command_safety_status(env=env, allow_override=allow_override)["dws_commands_allowed"])


def dws_browser_policy_status(*, env: Mapping[str, str] | None = None) -> dict[str, Any]:
    values = merged_runtime_env() if env is None else dict(env)
    try:
        policy_value, policy_source = migrated_env_value(
            values,
            current_key=DWS_BROWSER_POLICY_PATH_ENV,
            legacy_key=LEGACY_DWS_BROWSER_POLICY_PATH_ENV,
        )
    except DwsEnvironmentConflictError as exc:
        return {
            "status": DWS_ENV_CONFLICT,
            "path": "",
            "open_browser": None,
            "failure_reason": str(exc),
        }
    policy_path = Path(policy_value or DEFAULT_DWS_BROWSER_POLICY_PATH).expanduser()
    if not policy_path.exists():
        return {
            "status": "MISSING",
            "path": str(policy_path),
            "open_browser": None,
            "failure_reason": "DWS PAT browser policy file is missing.",
        }
    try:
        payload = json.loads(policy_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "status": "INVALID",
            "path": str(policy_path),
            "open_browser": None,
            "failure_reason": f"cannot read DWS PAT browser policy: {exc.__class__.__name__}",
        }
    default_policy = payload.get("default") if isinstance(payload, Mapping) else None
    open_browser = default_policy.get("openBrowser") if isinstance(default_policy, Mapping) else None
    if open_browser is False:
        return {
            "status": "READY",
            "path": str(policy_path),
            "open_browser": False,
            "environment_key_source": policy_source,
        }
    return {
        "status": "UNSAFE",
        "path": str(policy_path),
        "open_browser": open_browser,
        "failure_reason": "DWS PAT browser policy must set default.openBrowser=false.",
    }


def dws_subprocess_env(*, env: Mapping[str, str] | None = None) -> dict[str, str]:
    values = dict(os.environ if env is None else env)
    values["BROWSER"] = "/usr/bin/false"
    return values
