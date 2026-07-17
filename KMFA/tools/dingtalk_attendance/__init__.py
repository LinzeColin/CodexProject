"""KMFA 钉钉考勤 skill runtime package."""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path

from KMFA.tools.dingtalk_attendance.identity import SKILL_ID

AUTOMATION_NAME = "每日早晚钉钉考勤检查"
TIMEZONE = "Asia/Shanghai"
ARCHIVE_ROOT_ENV = "KMFA_DINGTALK_ATTENDANCE_ARCHIVE_ROOT"
ARCHIVE_ROOT_REF = f"ENV::{ARCHIVE_ROOT_ENV}"
ONEDRIVE_ROOT = os.environ.get(
    ARCHIVE_ROOT_ENV,
    ARCHIVE_ROOT_REF,
)
OWNER_DINGTALK_USER_ID = os.environ.get(
    "KMFA_DINGTALK_OWNER_USER_ID",
    "CONFIG_REQUIRED",
)


class PrivateArchiveConfigError(RuntimeError):
    """Raised before private archive I/O when its environment binding is absent."""


def resolve_archive_root(
    value: str | Path | None = None,
    *,
    env: Mapping[str, str] | None = None,
) -> Path:
    values = os.environ if env is None else env
    raw = str(value or "").strip()
    if not raw or raw == ARCHIVE_ROOT_REF:
        raw = str(values.get(ARCHIVE_ROOT_ENV, "")).strip()
    if not raw or raw == ARCHIVE_ROOT_REF or raw == "CONFIG_REQUIRED":
        raise PrivateArchiveConfigError(
            f"PRIVATE_ARCHIVE_REF_UNRESOLVED: {ARCHIVE_ROOT_ENV} is required"
        )
    path = Path(raw).expanduser()
    if not path.is_absolute():
        raise PrivateArchiveConfigError(
            f"PRIVATE_ARCHIVE_REF_INVALID: {ARCHIVE_ROOT_ENV} must be absolute"
        )
    return path


def private_identifier_is_configured(value: object) -> bool:
    raw = str(value or "").strip()
    return bool(raw) and raw != "CONFIG_REQUIRED" and not raw.startswith("ENV::") and not (
        raw.startswith("<") and raw.endswith(">")
    )
