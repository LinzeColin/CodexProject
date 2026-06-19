import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./fifa_analysis.db")
    app_name: str = os.getenv("APP_NAME", "FIFA Football Analysis MVP")
    model_version: str = os.getenv("MODEL_VERSION", "rules-v1.0.0")
    refresh_interval_hours: float = float(os.getenv("REFRESH_INTERVAL_HOURS", "4"))
    enable_scheduler: bool = os.getenv("ENABLE_SCHEDULER", "true").lower() in {"1", "true", "yes", "on"}
    auto_seed_world_cup: bool = os.getenv("AUTO_SEED_WORLD_CUP_2026", "true").lower() in {"1", "true", "yes", "on"}


settings = Settings()
