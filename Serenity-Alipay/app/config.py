from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    root_dir: Path
    data_dir: Path
    db_path: Path
    imports_dir: Path
    manual_dir: Path
    reports_dir: Path
    notifications_dir: Path
    exports_dir: Path
    timezone_primary: str = "Asia/Shanghai"
    timezone_secondary: str = "Australia/Sydney"
    recipient_email: str = "linzezhang35@gmail.com"
    model_profile: str = "Automation Using Model 5.4 Reasoning High"
    dry_run_default: bool = True
    fallback_aggregated_enabled: bool = True
    mail_send_enabled: bool = False
    secret_storage_enabled: bool = False
    max_drawdown_block: float = 0.40
    recovery_time_block_days: int = 365
    deviation_threshold: float = 0.01
    top5_change_rate_threshold: float = 0.20
    drawdown_7d_worsen_threshold: float = 0.05
    min_official_sources_action_ready: int = 2

    @classmethod
    def load(cls, root_dir: Path | None = None) -> "Settings":
        root = root_dir or Path(__file__).resolve().parents[1]
        data = root / "data"
        db_path = Path(os.getenv("SERENITY_DB_PATH", data / "serenity_daily.sqlite"))
        return cls(
            root_dir=root,
            data_dir=data,
            db_path=db_path,
            imports_dir=data / "imports",
            manual_dir=data / "manual",
            reports_dir=data / "reports",
            notifications_dir=data / "notifications",
            exports_dir=data / "exports",
            dry_run_default=_bool_env("SERENITY_DRY_RUN", True),
            fallback_aggregated_enabled=_bool_env("SERENITY_FALLBACK_AGGREGATED", True),
            mail_send_enabled=_bool_env("SERENITY_MAIL_SEND_ENABLED", False),
            secret_storage_enabled=_bool_env("SERENITY_SECRET_STORAGE_ENABLED", False),
        )

    def ensure_dirs(self) -> None:
        for path in [
            self.data_dir,
            self.imports_dir,
            self.manual_dir,
            self.reports_dir,
            self.notifications_dir,
            self.exports_dir,
        ]:
            path.mkdir(parents=True, exist_ok=True)


def load_settings() -> Settings:
    settings = Settings.load()
    settings.ensure_dirs()
    return settings
