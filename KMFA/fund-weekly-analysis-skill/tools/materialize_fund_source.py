#!/usr/bin/env python3
"""Explicitly materialize verified private DWS source files into the configured hot folder.

This tool copies files from a private source candidate such as
`DWS_Archive/付款请示群` to `DWS_Outputs/付款请示群`. It never deletes, moves, or
overwrites source data. Dry-run is the default; `--apply` is required to copy.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable
from zoneinfo import ZoneInfo


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def iter_source_files(source_dir: Path) -> Iterable[Path]:
    for path in sorted(source_dir.rglob("*")):
        if path.is_file() and not path.name.startswith("."):
            yield path


def ensure_safe_paths(source_dir: Path, target_dir: Path) -> None:
    if source_dir == target_dir:
        raise ValueError("source_dir and target_dir must be different")
    if source_dir in target_dir.parents:
        raise ValueError("target_dir must not be inside source_dir")


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


def unreadable_item(source_path: Path, target_path: Path, relative_path: Path, error_type: str, error: str) -> dict:
    return {
        "relative_path": str(relative_path),
        "source_path": str(source_path),
        "target_path": str(target_path),
        "size_bytes": source_path.stat().st_size,
        "sha256": "",
        "target_exists": target_path.exists(),
        "action": "source_unreadable",
        "error_type": error_type,
        "error": error,
    }


def build_plan(source_dir: Path, target_dir: Path) -> tuple[list[dict], list[dict], list[dict]]:
    files: list[dict] = []
    conflicts: list[dict] = []
    unreadable: list[dict] = []
    for source_path in iter_source_files(source_dir):
        relative_path = source_path.relative_to(source_dir)
        target_path = target_dir / relative_path
        flag_text = macos_file_flags(source_path)
        if "dataless" in flag_text:
            item = unreadable_item(
                source_path,
                target_path,
                relative_path,
                "DatalessFile",
                f"macOS file flags indicate cloud-only content: {flag_text}",
            )
            files.append(item)
            unreadable.append(item)
            continue
        try:
            source_hash = sha256_file(source_path)
        except OSError as exc:
            item = unreadable_item(source_path, target_path, relative_path, type(exc).__name__, str(exc))
            files.append(item)
            unreadable.append(item)
            continue
        item = {
            "relative_path": str(relative_path),
            "source_path": str(source_path),
            "target_path": str(target_path),
            "size_bytes": source_path.stat().st_size,
            "sha256": source_hash,
            "target_exists": target_path.exists(),
            "action": "copy",
        }
        if target_path.exists():
            target_hash = sha256_file(target_path)
            item["target_sha256"] = target_hash
            if target_hash == source_hash:
                item["action"] = "skip_identical"
            else:
                item["action"] = "conflict"
                conflicts.append(item)
        files.append(item)
    return files, conflicts, unreadable


def write_csv(path: Path, files: list[dict]) -> None:
    fieldnames = [
        "relative_path",
        "source_path",
        "target_path",
        "size_bytes",
        "sha256",
        "target_exists",
        "action",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(files)


def write_manifest(run_dir: Path, manifest: dict, files: list[dict]) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "source_materialization_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_csv(run_dir / "source_materialization_files.csv", files)


def materialize(source_dir: Path, target_dir: Path, run_dir: Path, timezone: str, apply: bool) -> int:
    now = dt.datetime.now(ZoneInfo(timezone)).isoformat()
    if not source_dir.exists():
        manifest = {
            "status": "SOURCE_MISSING",
            "applied": False,
            "source_dir": str(source_dir),
            "target_dir": str(target_dir),
            "generated_at": now,
            "files": [],
            "conflicts": [],
            "error": "source_dir does not exist",
        }
        write_manifest(run_dir, manifest, [])
        print(json.dumps({"status": "SOURCE_MISSING", "run_dir": str(run_dir)}, ensure_ascii=False))
        return 2

    ensure_safe_paths(source_dir, target_dir)
    files, conflicts, unreadable = build_plan(source_dir, target_dir)
    copy_files = [item for item in files if item["action"] == "copy"]
    skipped = [item for item in files if item["action"] == "skip_identical"]

    if unreadable:
        manifest = {
            "status": "SOURCE_UNREADABLE",
            "applied": False,
            "source_dir": str(source_dir),
            "target_dir": str(target_dir),
            "generated_at": now,
            "planned_copy_count": len(copy_files),
            "skipped_identical_count": len(skipped),
            "unreadable_count": len(unreadable),
            "unreadable": unreadable,
            "conflict_count": len(conflicts),
            "conflicts": conflicts,
            "files": files,
        }
        write_manifest(run_dir, manifest, files)
        print(json.dumps({"status": "SOURCE_UNREADABLE", "run_dir": str(run_dir), "unreadable_count": len(unreadable)}, ensure_ascii=False))
        return 5

    if conflicts:
        manifest = {
            "status": "TARGET_CONFLICT",
            "applied": False,
            "source_dir": str(source_dir),
            "target_dir": str(target_dir),
            "generated_at": now,
            "planned_copy_count": len(copy_files),
            "skipped_identical_count": len(skipped),
            "conflict_count": len(conflicts),
            "conflicts": conflicts,
            "files": files,
        }
        write_manifest(run_dir, manifest, files)
        print(json.dumps({"status": "TARGET_CONFLICT", "run_dir": str(run_dir), "conflict_count": len(conflicts)}, ensure_ascii=False))
        return 3

    copied_count = 0
    if apply:
        for item in copy_files:
            target_path = Path(item["target_path"])
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item["source_path"], target_path)
            copied_count += 1

    status = "MATERIALIZED" if apply and copied_count else "ALREADY_CURRENT" if apply else "DRY_RUN"
    manifest = {
        "status": status,
        "applied": apply,
        "source_dir": str(source_dir),
        "target_dir": str(target_dir),
        "generated_at": now,
        "planned_copy_count": len(copy_files),
        "copied_count": copied_count,
        "skipped_identical_count": len(skipped),
        "conflict_count": 0,
        "conflicts": [],
        "files": files,
    }
    write_manifest(run_dir, manifest, files)
    print(json.dumps({"status": status, "run_dir": str(run_dir), "planned_copy_count": len(copy_files), "copied_count": copied_count}, ensure_ascii=False))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", default="/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Archive/付款请示群")
    parser.add_argument("--target-dir", default="/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs/付款请示群")
    parser.add_argument("--repo-root", default=os.environ.get("KMFA_REPO_ROOT", "."))
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--timezone", default="Australia/Sydney")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    timezone = ZoneInfo(args.timezone)
    run_id = args.run_id or dt.datetime.now(timezone).strftime("%Y%m%dT%H%M%S%z")
    run_dir = repo_root / "KMFA" / "metadata" / "fund_weekly_analysis" / "private_runtime" / "runs" / run_id
    source_dir = Path(args.source_dir).expanduser().resolve()
    target_dir = Path(args.target_dir).expanduser().resolve()
    try:
        return materialize(source_dir, target_dir, run_dir, args.timezone, args.apply)
    except ValueError as exc:
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "source_materialization_manifest.json").write_text(
            json.dumps({"status": "INVALID_PATHS", "applied": False, "error": str(exc)}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(json.dumps({"status": "INVALID_PATHS", "error": str(exc), "run_dir": str(run_dir)}, ensure_ascii=False))
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
