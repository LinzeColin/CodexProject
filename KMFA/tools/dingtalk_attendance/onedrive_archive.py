#!/usr/bin/env python3
"""OneDrive archive path helpers for KMFA S19."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from KMFA.tools.dingtalk_attendance import ONEDRIVE_ROOT


def month_folder_for(value: datetime) -> str:
    return value.strftime("%Y%m")


def archive_paths_for_run(run_id: str, value: datetime) -> dict[str, str]:
    month_dir = Path(ONEDRIVE_ROOT) / month_folder_for(value)
    return {
        "month_dir": str(month_dir),
        "raw_jsonl_gz": str(month_dir / f"{run_id}.raw.jsonl.gz"),
        "management_report": str(month_dir / f"{run_id}.management.md"),
        "hr_report": str(month_dir / f"{run_id}.hr.md"),
        "dispatch_receipt": str(month_dir / f"{run_id}.dispatch.json"),
        "archive_manifest": str(month_dir / f"{run_id}.manifest.json"),
        "cleanup_audit": str(month_dir / f"{run_id}.cleanup.json"),
        "archive_db": str(month_dir / "dingtalk_attendance_archive.sqlite"),
        "archive_db_hash": str(month_dir / "dingtalk_attendance_archive.sqlite.sha256"),
    }
