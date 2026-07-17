#!/usr/bin/env python3
"""OneDrive archive path helpers for the KMFA DingTalk attendance skill."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from KMFA.tools.dingtalk_attendance import resolve_archive_root


def month_folder_for(value: datetime) -> str:
    return value.strftime("%Y%m")


def archive_paths_for_run(
    run_id: str,
    value: datetime,
    *,
    onedrive_root: str | Path | None = None,
) -> dict[str, str]:
    month_dir = resolve_archive_root(onedrive_root) / month_folder_for(value)
    return {
        "month_dir": str(month_dir),
        "raw_jsonl_gz": str(month_dir / f"{run_id}.raw.jsonl.gz"),
        "management_report": str(month_dir / f"{run_id}.management.md"),
        "hr_report": str(month_dir / f"{run_id}.hr.md"),
        "dispatch_receipt": str(month_dir / f"{run_id}.dispatch.json"),
        "archive_manifest": str(month_dir / f"{run_id}.manifest.json"),
        "cleanup_audit": str(month_dir / f"{run_id}.cleanup.json"),
        "one_page_result": str(month_dir / f"{run_id}.one_page.md"),
    }


def private_archive_refs_for_run(run_id: str, value: datetime) -> dict[str, str]:
    """Return non-executable public refs before private root resolution."""
    month_ref = f"local-resource://DINGTALK_ATTENDANCE_ARCHIVE/{month_folder_for(value)}"
    return {
        "month_dir": month_ref,
        "raw_jsonl_gz": f"{month_ref}/{run_id}.raw.jsonl.gz",
        "management_report": f"{month_ref}/{run_id}.management.md",
        "hr_report": f"{month_ref}/{run_id}.hr.md",
        "dispatch_receipt": f"{month_ref}/{run_id}.dispatch.json",
        "archive_manifest": f"{month_ref}/{run_id}.manifest.json",
        "cleanup_audit": f"{month_ref}/{run_id}.cleanup.json",
        "one_page_result": f"{month_ref}/{run_id}.one_page.md",
    }
