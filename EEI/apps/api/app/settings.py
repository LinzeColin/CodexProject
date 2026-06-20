from __future__ import annotations

import os
from dataclasses import dataclass


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
    task_pack_version: str = "v4.2.0"
    product_version: str = "v0.1"


def _csv_setting(name: str, default: tuple[str, ...]) -> tuple[str, ...]:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return tuple(item.strip() for item in raw_value.split(",") if item.strip())


def get_settings() -> Settings:
    return Settings(
        environment=os.getenv("EEI_ENV", "local"),
        database_url=os.getenv("DATABASE_URL"),
        cors_allow_origins=_csv_setting(
            "EEI_CORS_ALLOW_ORIGINS",
            Settings.cors_allow_origins,
        ),
    )
