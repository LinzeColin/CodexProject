#!/usr/bin/env python3
"""Fast readiness gate for KMFA fund weekly source folders.

This preflight intentionally does not hash or read file bodies. It checks
existence, file counts, macOS/OneDrive cloud-only flags, and basic readability so
the 11:30 run can fail closed before expensive extraction starts.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
from pathlib import Path
from zoneinfo import ZoneInfo


def macos_file_flags(path: Path) -> str:
    if sys.platform != "darwin":
        return ""
    try:
        result = subprocess.run(
            ["/usr/bin/stat", "-f", "%Sf", str(path)],
            text=True,
            capture_output=True,
            check=False,
            timeout=2,
        )
    except Exception:
        return ""
    return result.stdout.strip()


def iter_files(root: Path):
    for path in sorted(root.rglob("*")):
        if path.is_file() and not path.name.startswith("."):
            yield path


def inspect_file(root: Path, path: Path) -> dict:
    flags = macos_file_flags(path)
    readable = os.access(path, os.R_OK)
    dataless = "dataless" in flags
    return {
        "relative_path": str(path.relative_to(root)),
        "size_bytes": path.stat().st_size,
        "flags": flags,
        "readable": readable,
        "dataless": dataless,
        "status": "SOURCE_UNREADABLE" if dataless or not readable else "READY",
    }


def inspect_path(path: Path, kind: str) -> dict:
    item = {
        "kind": kind,
        "path": str(path),
        "exists": path.exists(),
        "status": "SOURCE_MISSING",
        "file_count": 0,
        "unreadable_count": 0,
        "dataless_count": 0,
        "unreadable_examples": [],
    }
    if not path.exists():
        return item

    if path.is_file():
        flags = macos_file_flags(path)
        readable = os.access(path, os.R_OK)
        dataless = "dataless" in flags
        item.update({
            "file_count": 1,
            "size_bytes": path.stat().st_size,
            "mtime_iso": dt.datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
            "flags": flags,
            "unreadable_count": 1 if dataless or not readable else 0,
            "dataless_count": 1 if dataless else 0,
            "status": "SOURCE_UNREADABLE" if dataless or not readable else "READY",
        })
        if item["unreadable_count"]:
            item["unreadable_examples"] = [{
                "relative_path": path.name,
                "flags": flags,
                "readable": readable,
                "dataless": dataless,
                "status": "SOURCE_UNREADABLE",
            }]
        return item

    latest_mtime: float | None = None
    for source_file in iter_files(path):
        item["file_count"] += 1
        latest_mtime = max(latest_mtime or source_file.stat().st_mtime, source_file.stat().st_mtime)
        file_info = inspect_file(path, source_file)
        if file_info["dataless"]:
            item["dataless_count"] += 1
        if file_info["status"] == "SOURCE_UNREADABLE":
            item["unreadable_count"] += 1
            if len(item["unreadable_examples"]) < 20:
                item["unreadable_examples"].append(file_info)
    item["latest_file_mtime_iso"] = dt.datetime.fromtimestamp(latest_mtime).isoformat() if latest_mtime else None
    item["status"] = "SOURCE_UNREADABLE" if item["unreadable_count"] else "READY"
    return item


def source_candidates_for(target_dir: Path) -> list[dict]:
    group_name = target_dir.name
    one_drive_root = target_dir.parent.parent if target_dir.parent.name == "DWS_Outputs" else target_dir.parent
    return [
        inspect_path(one_drive_root / "DWS_Archive" / group_name, "dws_archive_group"),
        inspect_path(one_drive_root / "DWS_Outputs.zip", "dws_outputs_zip"),
    ]


def write_report(run_dir: Path, report: dict) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "source_readiness.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-dir", default="/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs/付款请示群")
    parser.add_argument("--repo-root", default=os.environ.get("KMFA_REPO_ROOT", "."))
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--timezone", default="Australia/Sydney")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    timezone = ZoneInfo(args.timezone)
    run_id = args.run_id or dt.datetime.now(timezone).strftime("%Y%m%dT%H%M%S%z")
    run_dir = repo_root / "KMFA" / "metadata" / "fund_weekly_analysis" / "private_runtime" / "runs" / run_id
    target_dir = Path(args.target_dir).expanduser().resolve()
    now = dt.datetime.now(timezone).isoformat()

    target = inspect_path(target_dir, "target_input_dir")
    if not target["exists"]:
        report = {
            "project_id": "KMFA",
            "skill_name": "fund-weekly-analysis-skill",
            "run_id": run_id,
            "timezone": args.timezone,
            "generated_at": now,
            "status": "SOURCE_MISSING",
            "target": target,
            "source_candidates": source_candidates_for(target_dir),
            "action": "Materialize a verified private candidate into the configured DWS_Outputs/付款请示群 folder before the daily run.",
        }
        write_report(run_dir, report)
        print(json.dumps({"run_id": run_id, "run_dir": str(run_dir), "status": "SOURCE_MISSING"}, ensure_ascii=False))
        return 2

    status = target["status"]
    report = {
        "project_id": "KMFA",
        "skill_name": "fund-weekly-analysis-skill",
        "run_id": run_id,
        "timezone": args.timezone,
        "generated_at": now,
        "status": status,
        "target": target,
        "source_candidates": [],
        "action": "Proceed to run_fund_weekly_analysis.py only when status is READY.",
    }
    write_report(run_dir, report)
    print(json.dumps({"run_id": run_id, "run_dir": str(run_dir), "status": status, "file_count": target["file_count"], "unreadable_count": target["unreadable_count"]}, ensure_ascii=False))
    return 0 if status == "READY" else 5


if __name__ == "__main__":
    raise SystemExit(main())
