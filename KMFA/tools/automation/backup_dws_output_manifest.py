#!/usr/bin/env python3
"""Publish a public-safe DWS archive manifest to the CodexProject main branch."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any


TARGET = Path("KMFA/metadata/dws_outputs_backup")
COMMIT_PREFIX = "KMFA metadata: backup DWS output manifest "
SUMMARY_FIELDS = (
    "run_id",
    "automation_name",
    "run_source",
    "run_started",
    "run_ended",
    "success",
    "group_count",
    "downloads_temp_output_removed",
    "missing_total",
    "exhausted_total",
    "mirror_archive_size_bytes",
    "data_archive_size_before",
    "data_archive_size_after",
    "cold_archive_root",
)


class BackupError(RuntimeError):
    def __init__(self, status: str, message: str) -> None:
        super().__init__(message)
        self.status = status


def emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))


def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BackupError("INPUT_INVALID", f"Cannot read {label}: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise BackupError("INPUT_INVALID", f"{label} must contain a JSON object: {path}")
    return value


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ("git", "-C", str(repo), *args),
        text=True,
        capture_output=True,
        check=False,
    )
    if check and result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "unknown git error"
        raise BackupError("GIT_STATE_BLOCKED", f"git {' '.join(args)} failed: {detail}")
    return result


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_json_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def validate_inputs(
    dws_project: Path,
    source_package: Path,
    summary: dict[str, Any],
    validation: dict[str, Any],
) -> tuple[str, int]:
    if not dws_project.is_dir():
        raise BackupError("INPUT_INVALID", f"DWS project directory does not exist: {dws_project}")
    if not source_package.is_file():
        raise BackupError("INPUT_INVALID", f"DWS source package does not exist: {source_package}")
    run_id = summary.get("run_id")
    if not isinstance(run_id, str) or not run_id or not run_id.replace("T", "").isdigit():
        raise BackupError("INPUT_INVALID", "DWS summary has an invalid run_id")
    if summary.get("success") is not True:
        raise BackupError("VALIDATION_FAILED", "DWS summary does not report success=true")

    mirror = validation.get("mirror")
    cold_storage = validation.get("cold_storage")
    local_output_root = validation.get("local_output_root")
    groups = validation.get("groups")
    gates_ok = (
        validation.get("ok") is True
        and isinstance(mirror, dict)
        and mirror.get("ok") is True
        and isinstance(cold_storage, dict)
        and cold_storage.get("ok") is True
        and isinstance(local_output_root, dict)
        and local_output_root.get("ok") is True
        and isinstance(groups, list)
        and all(isinstance(group, dict) and group.get("ok") is True for group in groups)
    )
    if not gates_ok:
        raise BackupError("VALIDATION_FAILED", "DWS structure validation gates did not all pass")
    try:
        mirror_path = Path(str(mirror["path"])).expanduser().resolve(strict=True)
    except (KeyError, OSError) as exc:
        raise BackupError("VALIDATION_FAILED", "Validation mirror path is missing or unreadable") from exc
    if mirror_path != source_package.resolve(strict=True):
        raise BackupError("VALIDATION_FAILED", "Validated mirror is not the requested source package")
    file_count = mirror.get("file_count")
    if not isinstance(file_count, int) or file_count <= 0:
        raise BackupError("VALIDATION_FAILED", "Validated mirror file_count must be positive")
    return run_id, file_count


def ensure_main_ready(repo: Path) -> None:
    if git(repo, "rev-parse", "--is-inside-work-tree").stdout.strip() != "true":
        raise BackupError("GIT_STATE_BLOCKED", f"Not a Git worktree: {repo}")
    if git(repo, "branch", "--show-current").stdout.strip() != "main":
        raise BackupError("GIT_STATE_BLOCKED", "CodexProject must be checked out on main")
    tracked_dirty = git(repo, "status", "--porcelain", "--untracked-files=no").stdout.strip()
    if tracked_dirty:
        raise BackupError("GIT_STATE_BLOCKED", "Tracked or staged changes already exist")
    git(repo, "fetch", "origin", "main")
    counts = git(repo, "rev-list", "--left-right", "--count", "HEAD...origin/main").stdout.split()
    if len(counts) != 2:
        raise BackupError("GIT_STATE_BLOCKED", "Cannot compare local main with origin/main")
    ahead, behind = map(int, counts)
    if ahead and behind:
        raise BackupError("GIT_STATE_BLOCKED", "Local main and origin/main have diverged")
    if behind:
        git(repo, "merge", "--ff-only", "origin/main")
    if ahead:
        subjects = git(repo, "log", "--format=%s", "origin/main..HEAD").stdout.splitlines()
        changed = git(repo, "diff", "--name-only", "origin/main..HEAD").stdout.splitlines()
        if not subjects or any(not subject.startswith(COMMIT_PREFIX) for subject in subjects):
            raise BackupError("GIT_STATE_BLOCKED", "Local-only commits are not DWS manifest backup commits")
        target_prefix = TARGET.as_posix() + "/"
        if any(not name.startswith(target_prefix) for name in changed):
            raise BackupError("GIT_STATE_BLOCKED", "Local-only commits modify files outside the DWS manifest target")


def build_manifest(
    source_package: Path,
    summary: dict[str, Any],
    file_count: int,
    notion_status: str,
    timestamp: str,
) -> dict[str, Any]:
    safe_summary = {key: summary[key] for key in SUMMARY_FIELDS if key in summary}
    return {
        "schema_version": 1,
        "backup_type": "dws_outputs_manifest_only",
        "source_package": str(source_package),
        "raw_zip_committed": False,
        "raw_zip_commit_policy": "blocked_by_github_file_size_and_private_raw_data_boundary",
        "source_package_size_bytes": source_package.stat().st_size,
        "source_package_sha256": sha256(source_package),
        "source_package_file_count": file_count,
        "dws_run": safe_summary,
        "validation": {
            "validate_dws_output_structure": "pass",
            "mirror_file_count": file_count,
            "cold_storage_status": "ok",
        },
        "notion_sync": {
            "status": notion_status,
            "blocks_github_manifest_backup": False,
        },
        "updated_at": timestamp,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dws-project", required=True, type=Path)
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--source-package", required=True, type=Path)
    parser.add_argument("--summary-json", required=True, type=Path)
    parser.add_argument("--validation-json", required=True, type=Path)
    parser.add_argument("--notion-status", required=True, choices=("pending", "synced"))
    parser.add_argument("--timestamp", help="ISO-8601 manifest timestamp")
    parser.add_argument("--push", action="store_true", help="Push the manifest commit to origin/main")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        timestamp = args.timestamp or datetime.now().astimezone().isoformat(timespec="seconds")
        try:
            parsed_timestamp = datetime.fromisoformat(timestamp)
        except ValueError as exc:
            raise BackupError("INPUT_INVALID", "--timestamp must be ISO-8601") from exc
        repo = args.repo_root.expanduser().resolve()
        dws_project = args.dws_project.expanduser().resolve()
        source_package = args.source_package.expanduser().resolve()
        summary = load_json(args.summary_json.expanduser().resolve(), "DWS summary")
        validation = load_json(args.validation_json.expanduser().resolve(), "DWS validation")
        run_id, file_count = validate_inputs(dws_project, source_package, summary, validation)
        ensure_main_ready(repo)

        manifest = build_manifest(source_package, summary, file_count, args.notion_status, timestamp)
        latest_path = repo / TARGET / "latest" / "manifest.json"
        run_path = repo / TARGET / "runs" / f"{run_id}.json"
        atomic_json_write(latest_path, manifest)
        atomic_json_write(run_path, manifest)

        git(repo, "add", "--", TARGET.as_posix())
        staged = git(repo, "diff", "--cached", "--name-only").stdout.splitlines()
        target_prefix = TARGET.as_posix() + "/"
        if any(not name.startswith(target_prefix) for name in staged):
            raise BackupError("GIT_STATE_BLOCKED", "Staged changes escaped the DWS manifest target")

        committed = False
        if staged:
            message = COMMIT_PREFIX + parsed_timestamp.strftime("%Y-%m-%d %H%M")
            git(repo, "commit", "-m", message, "--", TARGET.as_posix())
            committed = True

        pushed = False
        if args.push:
            git(repo, "push", "origin", "main")
            pushed = True
        emit(
            {
                "status": "PUSHED" if pushed else ("COMMITTED" if committed else "NO_CHANGE"),
                "run_id": run_id,
                "committed": committed,
                "pushed": pushed,
                "notion_status": args.notion_status,
                "target": TARGET.as_posix(),
            }
        )
        return 0
    except BackupError as exc:
        emit({"status": exc.status, "error": str(exc), "committed": False, "pushed": False})
        return 1
    except Exception as exc:  # fail closed while keeping stdout machine-readable
        emit({"status": "BACKUP_FAILED", "error": str(exc), "committed": False, "pushed": False})
        return 1


if __name__ == "__main__":
    sys.exit(main())
