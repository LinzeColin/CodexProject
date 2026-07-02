from __future__ import annotations

import os
from dataclasses import dataclass, replace
from pathlib import Path


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _float_env(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


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
    min_candidate_nav_history_months: int = 24
    min_candidate_nav_history_span_days: int = 730
    opend_auto_start_enabled: bool = True
    opend_keep_auto_started: bool = True
    opend_wait_seconds: float = 45.0
    candidate_universe_auto_expand_enabled: bool = True
    candidate_universe_live_fetch_enabled: bool = False
    candidate_universe_max_additions: int = 25
    candidate_universe_min_theme_score: int = 3
    candidate_universe_fetch_timeout_seconds: float = 8.0
    candidate_universe_nav_backfill_enabled: bool = False
    candidate_universe_max_nav_backfills: int = 8
    candidate_universe_rule_autofill_enabled: bool = True
    candidate_universe_max_rule_autofills: int = 8

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
            opend_auto_start_enabled=_bool_env("SERENITY_OPEND_AUTO_START", True),
            opend_keep_auto_started=_bool_env("SERENITY_OPEND_KEEP_AUTO_STARTED", True),
            opend_wait_seconds=_float_env("SERENITY_OPEND_WAIT_SECONDS", 45.0),
            candidate_universe_auto_expand_enabled=_bool_env("SERENITY_CANDIDATE_UNIVERSE_AUTO_EXPAND", True),
            candidate_universe_live_fetch_enabled=_bool_env("SERENITY_FUND_UNIVERSE_LIVE_FETCH", True),
            candidate_universe_max_additions=_int_env("SERENITY_FUND_UNIVERSE_MAX_ADDITIONS", 25),
            candidate_universe_min_theme_score=_int_env("SERENITY_FUND_UNIVERSE_MIN_THEME_SCORE", 3),
            candidate_universe_fetch_timeout_seconds=_float_env("SERENITY_FUND_UNIVERSE_FETCH_TIMEOUT_SECONDS", 8.0),
            candidate_universe_nav_backfill_enabled=_bool_env("SERENITY_FUND_UNIVERSE_NAV_BACKFILL", True),
            candidate_universe_max_nav_backfills=_int_env("SERENITY_FUND_UNIVERSE_MAX_NAV_BACKFILLS", 8),
            candidate_universe_rule_autofill_enabled=_bool_env("SERENITY_FUND_RULE_AUTOFILL", True),
            candidate_universe_max_rule_autofills=_int_env("SERENITY_FUND_RULE_AUTOFILLS", 8),
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

    def with_runtime_mail_intent(self, *, dry_run: bool, send_mail: bool) -> "Settings":
        if self.mail_send_enabled or dry_run or not send_mail:
            return self
        return replace(self, mail_send_enabled=True)


def load_settings() -> Settings:
    settings = Settings.load()
    settings.ensure_dirs()
    return settings
