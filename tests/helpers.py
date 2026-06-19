from __future__ import annotations

import shutil
from pathlib import Path

from app.config import Settings


def temp_settings(tmp_path: Path) -> Settings:
    root = tmp_path
    data = root / "data"
    settings = Settings(
        root_dir=root,
        data_dir=data,
        db_path=data / "serenity_daily.sqlite",
        imports_dir=data / "imports",
        manual_dir=data / "manual",
        reports_dir=data / "reports",
        notifications_dir=data / "notifications",
        exports_dir=data / "exports",
    )
    settings.ensure_dirs()
    return settings


def copy_sample_data(settings: Settings, workspace: Path) -> None:
    shutil.copytree(workspace / "data" / "manual", settings.manual_dir, dirs_exist_ok=True)
    shutil.copytree(workspace / "data" / "imports", settings.imports_dir, dirs_exist_ok=True)
    moomoo_source = workspace / "data" / "moomoo"
    if moomoo_source.exists():
        shutil.copytree(moomoo_source, settings.data_dir / "moomoo", dirs_exist_ok=True)
