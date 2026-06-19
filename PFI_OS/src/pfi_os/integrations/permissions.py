from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from pfi_os.config import PROJECT_ROOT


DEFAULT_PERMISSIONS_PATH = PROJECT_ROOT / "shared" / "security" / "system_permissions.json"

SYSTEM_ALIASES = {
    "ai-research-system": "industry_research",
    "airesearchsystem": "industry_research",
    "governmentpolicysystem": "policy_intelligence",
    "government-policy-system": "policy_intelligence",
    "consumptionanalysissystem": "finance_ledger",
    "consumption-analysis-system": "finance_ledger",
    "pfi_os": "PFI_OS",
    "researchbus": "PFI_OS",
    "research-bus": "PFI_OS",
}


def permissions_file_path(path: Path | str | None = None) -> Path:
    if path is not None:
        return Path(path).expanduser()
    override = os.environ.get("PFI_SYSTEM_PERMISSIONS_FILE", "").strip()
    return Path(override).expanduser() if override else DEFAULT_PERMISSIONS_PATH


def load_system_permissions(path: Path | str | None = None) -> dict[str, Any]:
    target = permissions_file_path(path)
    if not target.exists():
        return {
            "schema_version": "missing",
            "default": {"decision": "deny", "execute_requires_approval_id": True},
            "rules": [],
            "_load_error": f"permissions file missing: {target}",
        }
    return json.loads(target.read_text(encoding="utf-8"))


def authorize_system_action(
    source_system: str,
    target_system: str,
    scope: str,
    *,
    action: str = "read",
    execute: bool = False,
    approval_id: str = "",
    permissions_path: Path | str | None = None,
) -> dict[str, Any]:
    permissions = load_system_permissions(permissions_path)
    source = _canonical_system_name(source_system)
    target = _canonical_system_name(target_system)
    clean_scope = str(scope or "").strip()
    clean_action = str(action or "").strip().lower()
    default = permissions.get("default", {})

    if not clean_scope:
        return _deny(source, target, clean_scope, clean_action, "missing scope")
    if permissions.get("_load_error"):
        return _deny(source, target, clean_scope, clean_action, str(permissions["_load_error"]))
    if execute and default.get("execute_requires_approval_id", True) and not str(approval_id or "").strip():
        return _deny(source, target, clean_scope, clean_action, "execute=true requires approval_id")

    for rule in permissions.get("rules", []):
        if _canonical_system_name(str(rule.get("source_system", ""))) != source:
            continue
        if _canonical_system_name(str(rule.get("target_system", ""))) != target:
            continue
        if not _matches(clean_action, rule.get("actions", [])):
            continue
        if not _matches(clean_scope, rule.get("scopes", [])):
            continue
        if execute and not bool(rule.get("allow_execute", False)):
            return _deny(source, target, clean_scope, clean_action, "matching rule does not allow execute=true")
        return {
            "allowed": True,
            "reason": "allowed by explicit system permission rule",
            "source_system": source,
            "target_system": target,
            "scope": clean_scope,
            "action": clean_action,
            "execute": bool(execute),
            "rule_id": str(rule.get("id", "")),
        }

    reason = str(default.get("reason") or "no matching permission rule")
    return _deny(source, target, clean_scope, clean_action, reason)


def assert_system_permission(
    source_system: str,
    target_system: str,
    scope: str,
    *,
    action: str = "read",
    execute: bool = False,
    approval_id: str = "",
    permissions_path: Path | str | None = None,
) -> dict[str, Any]:
    decision = authorize_system_action(
        source_system,
        target_system,
        scope,
        action=action,
        execute=execute,
        approval_id=approval_id,
        permissions_path=permissions_path,
    )
    if not decision["allowed"]:
        raise PermissionError(
            "Permission denied: "
            f"{decision['source_system']} -> {decision['target_system']} "
            f"scope={decision['scope']} action={decision['action']}: {decision['reason']}"
        )
    return decision


def _canonical_system_name(value: str) -> str:
    clean = str(value or "").strip()
    key = clean.lower().replace("_", "-").replace(" ", "")
    return SYSTEM_ALIASES.get(key, clean)


def _matches(value: str, allowed_values: Any) -> bool:
    if isinstance(allowed_values, str):
        allowed = {allowed_values}
    else:
        allowed = {str(item) for item in allowed_values or []}
    return "*" in allowed or value in allowed


def _deny(source: str, target: str, scope: str, action: str, reason: str) -> dict[str, Any]:
    return {
        "allowed": False,
        "reason": reason,
        "source_system": source,
        "target_system": target,
        "scope": scope,
        "action": action,
    }
