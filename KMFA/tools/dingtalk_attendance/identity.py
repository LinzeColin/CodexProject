#!/usr/bin/env python3
"""Canonical identity and legacy-read-only archive compatibility for the attendance skill."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any, Iterable


SKILL_ID = "kmfa-dingtalk-attendance-skill"
RUN_ID_PREFIX = "dingtalk_attendance_"
SEED_RUN_ID_PREFIX = "dingtalk_attendance_seed_"

# legacy_read_only: retained archives are never renamed or rewritten.
LEGACY_STAGE_IDS = frozenset({"S19", "KMFA-S19"})
LEGACY_RUN_ID_PREFIXES = ("s19_",)
LEGACY_SEED_RUN_ID_PREFIXES = ("s19_seed_",)

CURRENT_MANIFEST_GLOBS = ("dingtalk_attendance_*.manifest.json",)
CURRENT_RAW_GLOBS = (
    "dingtalk_attendance_*.raw.jsonl.gz",
    "dingtalk_attendance_*.raw.jsonl",
)
# legacy_read_only: old globs exist only in this centralized compatibility module.
LEGACY_MANIFEST_GLOBS = ("s19_*.manifest.json",)
LEGACY_RAW_GLOBS = ("s19_*.raw.jsonl.gz", "s19_*.raw.jsonl")


class IdentityConflictError(ValueError):
    """Raised when current and legacy identity fields cannot be reconciled safely."""


def build_run_id(run_type: str, timestamp: str) -> str:
    return f"{RUN_ID_PREFIX}{run_type}_{timestamp}"


def _run_id_body(run_id: str) -> tuple[str, str]:
    if run_id.startswith(RUN_ID_PREFIX):
        return run_id.removeprefix(RUN_ID_PREFIX), "current"
    for prefix in LEGACY_RUN_ID_PREFIXES:
        if run_id.startswith(prefix):
            return run_id.removeprefix(prefix), "legacy_read_only"
    return "", "unknown"


def run_type_from_run_id(run_id: str) -> str | None:
    body, _ = _run_id_body(str(run_id))
    parts = body.split("_")
    return parts[0] if parts and parts[0] in {"morning", "evening", "final"} else None


def work_date_from_run_id(run_id: str) -> str | None:
    body, _ = _run_id_body(str(run_id))
    parts = body.split("_")
    if len(parts) < 2 or len(parts[1]) != 8 or not parts[1].isdigit():
        return None
    value = parts[1]
    return f"{value[:4]}-{value[4:6]}-{value[6:8]}"


def is_seed_run_id(run_id: str) -> bool:
    return str(run_id).startswith((SEED_RUN_ID_PREFIX, *LEGACY_SEED_RUN_ID_PREFIXES))


def validate_manifest_identity(payload: Mapping[str, Any]) -> dict[str, str]:
    skill_id = str(payload.get("skill_id") or "").strip()
    legacy_stage_id = str(payload.get("stage_id") or "").strip()
    if skill_id:
        if skill_id != SKILL_ID:
            raise IdentityConflictError("manifest skill_id does not match the attendance skill")
        if legacy_stage_id and legacy_stage_id not in LEGACY_STAGE_IDS:
            raise IdentityConflictError("manifest current and legacy identity fields conflict")
        return {"skill_id": SKILL_ID, "identity_source": "skill_id"}
    if legacy_stage_id in LEGACY_STAGE_IDS:
        return {"skill_id": SKILL_ID, "identity_source": "legacy_read_only"}
    if legacy_stage_id:
        raise IdentityConflictError("manifest legacy stage_id is not recognized")
    raise IdentityConflictError("manifest identity is missing")


def _archive_paths(month_dir: Path, patterns: Iterable[str]) -> list[Path]:
    paths = {path for pattern in patterns for path in month_dir.glob(pattern) if path.is_file()}
    return sorted(paths)


def archive_manifest_paths(month_dir: Path) -> list[Path]:
    return _archive_paths(month_dir, (*CURRENT_MANIFEST_GLOBS, *LEGACY_MANIFEST_GLOBS))


def archive_raw_paths(month_dir: Path) -> list[Path]:
    return _archive_paths(month_dir, (*CURRENT_RAW_GLOBS, *LEGACY_RAW_GLOBS))


def current_archive_raw_paths(month_dir: Path) -> list[Path]:
    """Return only canonical attendance archives; legacy files remain audit-only."""
    return _archive_paths(month_dir, CURRENT_RAW_GLOBS)
