from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal, cast

SavedViewIdentityMode = Literal["local", "trusted_gateway"]


@dataclass(frozen=True)
class Settings:
    app_name: str = "Enterprise Ecosystem Intelligence"
    product_name_zh: str = "商域图谱"
    environment: str = "local"
    database_url: str | None = None
    cors_allow_origins: tuple[str, ...] = (
        "http://127.0.0.1:3000",
        "http://localhost:3000",
    )
    saved_view_identity_mode: SavedViewIdentityMode = "local"
    saved_view_gateway_secret: str | None = None
    saved_view_signature_ttl_seconds: int = 300
    task_pack_version: str = "v4.2.0"
    product_version: str = "v0.1"


def _csv_setting(name: str, default: tuple[str, ...]) -> tuple[str, ...]:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return tuple(item.strip() for item in raw_value.split(",") if item.strip())


def _int_setting(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return int(raw_value)


def _saved_view_identity_mode(environment: str) -> SavedViewIdentityMode:
    raw_value = os.getenv("EEI_SAVED_VIEW_IDENTITY_MODE")
    if raw_value:
        normalized = raw_value.strip().lower()
    else:
        normalized = "trusted_gateway" if environment in {"prod", "production"} else "local"
    if normalized not in {"local", "trusted_gateway"}:
        raise ValueError("EEI_SAVED_VIEW_IDENTITY_MODE must be local or trusted_gateway")
    return cast(SavedViewIdentityMode, normalized)


def get_settings() -> Settings:
    environment = os.getenv("EEI_ENV", "local").strip().lower()
    return Settings(
        environment=environment,
        database_url=os.getenv("DATABASE_URL"),
        cors_allow_origins=_csv_setting(
            "EEI_CORS_ALLOW_ORIGINS",
            Settings.cors_allow_origins,
        ),
        saved_view_identity_mode=_saved_view_identity_mode(environment),
        saved_view_gateway_secret=os.getenv("EEI_SAVED_VIEW_GATEWAY_SECRET"),
        saved_view_signature_ttl_seconds=_int_setting(
            "EEI_SAVED_VIEW_SIGNATURE_TTL_SECONDS",
            Settings.saved_view_signature_ttl_seconds,
        ),
    )
