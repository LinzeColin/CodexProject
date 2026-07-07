#!/usr/bin/env python3
"""Cleanup helpers for KMFA S19 private runtime files."""

from __future__ import annotations

import os
import sqlite3
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
PRIVATE_RUNTIME = ROOT / "metadata" / "dingtalk_attendance" / "private_runtime"
ACTIVE_DB = PRIVATE_RUNTIME / "dingtalk_attendance_active.sqlite"


def cleanup_runtime(retention_days: int = 3) -> dict[str, Any]:
    PRIVATE_RUNTIME.mkdir(parents=True, exist_ok=True)
    cutoff = time.time() - retention_days * 24 * 60 * 60
    removed_temp_files: list[str] = []
    for path in PRIVATE_RUNTIME.glob("*.tmp"):
        if path.stat().st_mtime < cutoff:
            path.unlink()
            removed_temp_files.append(path.name)

    db_status = "ABSENT"
    db_size_bytes = 0
    if ACTIVE_DB.exists():
        db_size_bytes = ACTIVE_DB.stat().st_size
        with sqlite3.connect(ACTIVE_DB) as conn:
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            conn.execute("PRAGMA optimize")
        db_status = "CHECKPOINTED"
        db_size_bytes = ACTIVE_DB.stat().st_size

    for suffix in ("-wal", "-shm"):
        candidate = Path(str(ACTIVE_DB) + suffix)
        if candidate.exists():
            db_size_bytes += candidate.stat().st_size

    return {
        "status": "OK",
        "retention_days": retention_days,
        "private_runtime": str(PRIVATE_RUNTIME),
        "removed_temp_files": removed_temp_files,
        "active_db_status": db_status,
        "database_size_bytes": db_size_bytes,
        "locks_released": True,
    }
