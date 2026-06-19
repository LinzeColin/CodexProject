from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "automation.toml"
ALLOWED_CADENCES = {"manual", "daily", "4h"}


@dataclass(frozen=True)
class AutomationAuthorization:
    authorized: bool = False
    allow_recurring: bool = False
    allow_auto_betting: bool = False
    cadence: str = "manual"
    approved_at: str = ""
    approved_by: str = ""
    scope: str = "report_generation_only"
    source: str = "defaults"
    config_file: str = "automation.toml"
    warnings: tuple[str, ...] = ()

    @property
    def entry_authorized(self) -> bool:
        return self.authorized and self.allow_recurring and not self.allow_auto_betting and not self.blocking_reasons

    @property
    def blocking_reasons(self) -> tuple[str, ...]:
        reasons: list[str] = []
        if not self.authorized:
            reasons.append("user has not authorized recurring automation")
        if self.authorized and not self.allow_recurring:
            reasons.append("automation config does not allow recurring report generation")
        if self.allow_auto_betting:
            reasons.append("automation config attempts to allow auto betting, which is forbidden")
        if self.authorized and self.cadence not in ALLOWED_CADENCES:
            reasons.append(f"automation cadence is unsupported: {self.cadence}")
        if self.authorized and self.scope != "report_generation_only":
            reasons.append(f"automation scope is unsupported: {self.scope}")
        return tuple(reasons)

    def to_public_dict(self) -> Dict[str, Any]:
        return {
            "authorized": self.authorized,
            "allow_recurring": self.allow_recurring,
            "allow_auto_betting": self.allow_auto_betting,
            "cadence": self.cadence,
            "approved_at": self.approved_at,
            "approved_by": self.approved_by,
            "scope": self.scope,
            "source": self.source,
            "config_file": self.config_file,
            "entry_authorized": self.entry_authorized,
            "blocking_reasons": list(self.blocking_reasons),
            "warnings": list(self.warnings),
        }


def load_automation_authorization(config_path: Path | None = None) -> AutomationAuthorization:
    path = Path(config_path or DEFAULT_CONFIG_PATH)
    defaults = AutomationAuthorization(config_file=path.name)
    if not path.exists():
        return defaults
    try:
        payload = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        return AutomationAuthorization(
            source="invalid_config",
            config_file=path.name,
            warnings=(f"{type(exc).__name__}: {exc}",),
        )
    return automation_authorization_from_mapping(payload, config_file=path.name)


def automation_authorization_from_mapping(payload: Mapping[str, Any], config_file: str = "automation.toml") -> AutomationAuthorization:
    return AutomationAuthorization(
        authorized=as_bool(payload.get("authorized"), False),
        allow_recurring=as_bool(payload.get("allow_recurring"), False),
        allow_auto_betting=as_bool(payload.get("allow_auto_betting"), False),
        cadence=as_text(payload.get("cadence"), "manual"),
        approved_at=as_text(payload.get("approved_at"), ""),
        approved_by=as_text(payload.get("approved_by"), ""),
        scope=as_text(payload.get("scope"), "report_generation_only"),
        source="config",
        config_file=config_file,
    )


def as_bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def as_text(value: Any, default: str) -> str:
    if value is None:
        return default
    return str(value).strip()
