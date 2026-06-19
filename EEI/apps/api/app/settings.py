from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_name: str = "Enterprise Ecosystem Intelligence"
    product_name_zh: str = "商域图谱"
    environment: str = os.getenv("EEI_ENV", "local")
    database_url: str | None = os.getenv("DATABASE_URL")
    task_pack_version: str = "v4.2.0"
    product_version: str = "v0.1"


def get_settings() -> Settings:
    return Settings()
