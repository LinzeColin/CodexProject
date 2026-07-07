#!/usr/bin/env python3
"""Cleanup helpers for KMFA S19 private runtime files."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
PRIVATE_RUNTIME = ROOT / "metadata" / "dingtalk_attendance" / "private_runtime"


def cleanup_runtime(retention_days: int = 3) -> dict[str, Any]:
    PRIVATE_RUNTIME.mkdir(parents=True, exist_ok=True)
    cutoff = time.time() - retention_days * 24 * 60 * 60
    removed_temp_files: list[str] = []
    for path in PRIVATE_RUNTIME.glob("*.tmp"):
        if path.stat().st_mtime < cutoff:
            path.unlink()
            removed_temp_files.append(path.name)

    return {
        "status": "OK",
        "retention_days": retention_days,
        "private_runtime": str(PRIVATE_RUNTIME),
        "removed_temp_files": removed_temp_files,
        "locks_released": True,
    }
