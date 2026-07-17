#!/usr/bin/env python3
"""Publish a public-safe DWS archive manifest to the CodexProject main branch."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any


TARGET = Path("KMFA/metadata/dws_outputs_backup")
COMMIT_PREFIX = "KMFA metadata: backup DWS output manifest "
SCHEMA_VERSION = "kmfa.dws_outputs_backup.public_safe.v2"
SOURCE_PACKAGE_REF = "SOURCE-PACKAGE-DWS-PRIVATE"
LOCAL_RESOURCE_REF = "LOCAL-RESOURCE-DWS-PRIVATE"
RUN_STATUS_FIELDS = (
    "run_id",
    "run_started",
    "run_ended",
    "success",
    "group_count",
    "downloads_temp_output_removed",
    "missing_total",
    "exhausted_total",
)
REQUIRED_RUN_STATUS_FIELDS = {"run_id", "run_started", "run_ended", "success"}
FORBIDDEN_PUBLIC_KEYS = {
    "auto_completed_project_groups",
    "cold_archive_root",
    "groups",
    "local_downloads_output_path",
    "mirror_archive_path",
    "mirror_archive_size_bytes",
    "output_root",
    "source_package",
    "source_package_sha256",
    "source_package_size_bytes",
}
ABSOLUTE_PATH_PATTERN = re.compile(r"(?<![A-Za-z0-9_])(?:/[A-Za-z0-9._~-]+){2,}")
WINDOWS_PATH_PATTERN = re.compile(r"\b[A-Za-z]:\\(?:[^\\\s]+\\)+[^\\\s]+")
SHA256_PATTERN = re.compile(r"(?i)(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])")


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
        raise BackupError("INPUT_INVALID", f"Cannot read {label}: {type(exc).__name__}") from exc
    if not isinstance(value, dict):
        raise BackupError("INPUT_INVALID", f"{label} must contain a JSON object")
    return value


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ("git", "-C", str(repo), *args),
        text=True,
        capture_output=True,
        check=False,
    )
    if check and result.returncode != 0:
        raise BackupError("GIT_STATE_BLOCKED", f"git {' '.join(args)} failed")
    return result


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
) -> str:
    if not dws_project.is_dir():
        raise BackupError("INPUT_INVALID", "DWS project directory does not exist")
    if not source_package.is_file():
        raise BackupError("INPUT_INVALID", "DWS source package does not exist")
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
    return run_id


def ensure_main_ready(repo: Path) -> None:
    if git(repo, "rev-parse", "--is-inside-work-tree").stdout.strip() != "true":
        raise BackupError("GIT_STATE_BLOCKED", "Repository root is not a Git worktree")
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


def _walk_public_values(value: Any, path: tuple[str, ...] = ()) -> list[tuple[tuple[str, ...], Any]]:
    rows: list[tuple[tuple[str, ...], Any]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            rows.append((path + (str(key),), child))
            rows.extend(_walk_public_values(child, path + (str(key),)))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            rows.extend(_walk_public_values(child, path + (str(index),)))
    return rows


def validate_public_manifest(manifest: dict[str, Any]) -> None:
    """Fail closed if a public manifest contains private-resource detail."""

    expected_top_level = {
        "schema_version",
        "record_type",
        "backup_type",
        "source_package_ref",
        "local_resource_ref",
        "private_receipt_required",
        "raw_resource_committed",
        "run_status",
        "validation_status",
        "notion_sync",
        "updated_at",
    }
    if set(manifest) != expected_top_level:
        raise BackupError("PUBLIC_SAFETY_BLOCKED", "Public manifest fields do not match the v2 allowlist")
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise BackupError("PUBLIC_SAFETY_BLOCKED", "Public manifest schema version is invalid")
    if manifest.get("record_type") != "dws_outputs_backup_public_summary":
        raise BackupError("PUBLIC_SAFETY_BLOCKED", "Public manifest record type is invalid")
    if manifest.get("backup_type") != "metadata_only":
        raise BackupError("PUBLIC_SAFETY_BLOCKED", "Public manifest backup type is invalid")
    if manifest.get("source_package_ref") != SOURCE_PACKAGE_REF:
        raise BackupError("PUBLIC_SAFETY_BLOCKED", "Source package reference is not the approved opaque token")
    if manifest.get("local_resource_ref") != LOCAL_RESOURCE_REF:
        raise BackupError("PUBLIC_SAFETY_BLOCKED", "Local resource reference is not the approved opaque token")
    if manifest.get("private_receipt_required") is not True:
        raise BackupError("PUBLIC_SAFETY_BLOCKED", "Private receipt requirement must remain explicit")
    if manifest.get("raw_resource_committed") is not False:
        raise BackupError("PUBLIC_SAFETY_BLOCKED", "Raw resources cannot be represented as committed")

    run_status = manifest.get("run_status")
    if not isinstance(run_status, dict):
        raise BackupError("PUBLIC_SAFETY_BLOCKED", "Run status must be an object")
    if not REQUIRED_RUN_STATUS_FIELDS.issubset(run_status) or not set(run_status).issubset(RUN_STATUS_FIELDS):
        raise BackupError("PUBLIC_SAFETY_BLOCKED", "Run status fields do not match the aggregate allowlist")
    run_id = run_status.get("run_id")
    if not isinstance(run_id, str) or not run_id.replace("T", "").isdigit():
        raise BackupError("PUBLIC_SAFETY_BLOCKED", "Run status identifier is invalid")
    for field in ("run_started", "run_ended", "updated_at"):
        value = manifest.get(field) if field == "updated_at" else run_status.get(field)
        if not isinstance(value, str):
            raise BackupError("PUBLIC_SAFETY_BLOCKED", f"{field} must be an ISO-8601 string")
        try:
            datetime.fromisoformat(value)
        except ValueError as exc:
            raise BackupError("PUBLIC_SAFETY_BLOCKED", f"{field} must be an ISO-8601 string") from exc
    if run_status.get("success") is not True:
        raise BackupError("PUBLIC_SAFETY_BLOCKED", "Only successful validated runs may be published")
    for field in ("group_count", "missing_total", "exhausted_total"):
        if field in run_status and (not isinstance(run_status[field], int) or isinstance(run_status[field], bool) or run_status[field] < 0):
            raise BackupError("PUBLIC_SAFETY_BLOCKED", f"{field} must be a non-negative integer")
    if "downloads_temp_output_removed" in run_status and not isinstance(
        run_status["downloads_temp_output_removed"], bool
    ):
        raise BackupError("PUBLIC_SAFETY_BLOCKED", "downloads_temp_output_removed must be boolean")

    if manifest.get("validation_status") != {
        "structure": "pass",
        "mirror": "pass",
        "cold_storage": "pass",
        "local_output": "pass",
        "group_checks": "pass",
    }:
        raise BackupError("PUBLIC_SAFETY_BLOCKED", "Validation status is not the approved aggregate projection")
    notion_sync = manifest.get("notion_sync")
    if not isinstance(notion_sync, dict) or set(notion_sync) != {"status", "blocks_manifest_backup"}:
        raise BackupError("PUBLIC_SAFETY_BLOCKED", "Notion status fields are invalid")
    if notion_sync.get("status") not in {"pending", "synced", "not_recorded"}:
        raise BackupError("PUBLIC_SAFETY_BLOCKED", "Notion status is invalid")
    if notion_sync.get("blocks_manifest_backup") is not False:
        raise BackupError("PUBLIC_SAFETY_BLOCKED", "Notion status cannot block manifest backup")

    for key_path, value in _walk_public_values(manifest):
        if key_path and key_path[-1] in FORBIDDEN_PUBLIC_KEYS:
            raise BackupError("PUBLIC_SAFETY_BLOCKED", "Public manifest contains a forbidden private-detail field")
        if isinstance(value, str) and (
            ABSOLUTE_PATH_PATTERN.search(value)
            or WINDOWS_PATH_PATTERN.search(value)
            or SHA256_PATTERN.search(value)
        ):
            raise BackupError("PUBLIC_SAFETY_BLOCKED", "Public manifest contains a path or private digest")


def build_manifest(summary: dict[str, Any], notion_status: str, timestamp: str) -> dict[str, Any]:
    safe_summary = {key: summary[key] for key in RUN_STATUS_FIELDS if key in summary}
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "dws_outputs_backup_public_summary",
        "backup_type": "metadata_only",
        "source_package_ref": SOURCE_PACKAGE_REF,
        "local_resource_ref": LOCAL_RESOURCE_REF,
        "private_receipt_required": True,
        "raw_resource_committed": False,
        "run_status": safe_summary,
        "validation_status": {
            "structure": "pass",
            "mirror": "pass",
            "cold_storage": "pass",
            "local_output": "pass",
            "group_checks": "pass",
        },
        "notion_sync": {
            "status": notion_status,
            "blocks_manifest_backup": False,
        },
        "updated_at": timestamp,
    }
    validate_public_manifest(manifest)
    return manifest


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
        repo = args.repo_root.expanduser().resolve()
        dws_project = args.dws_project.expanduser().resolve()
        source_package = args.source_package.expanduser().resolve()
        summary = load_json(args.summary_json.expanduser().resolve(), "DWS summary")
        validation = load_json(args.validation_json.expanduser().resolve(), "DWS validation")
        timestamp = args.timestamp or summary.get("run_ended")
        if not isinstance(timestamp, str) or not timestamp:
            raise BackupError("INPUT_INVALID", "DWS summary run_ended or --timestamp is required")
        try:
            parsed_timestamp = datetime.fromisoformat(timestamp)
        except ValueError as exc:
            raise BackupError("INPUT_INVALID", "manifest timestamp must be ISO-8601") from exc
        run_id = validate_inputs(dws_project, source_package, summary, validation)
        ensure_main_ready(repo)

        manifest = build_manifest(summary, args.notion_status, timestamp)
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
    except Exception:  # fail closed without echoing private runtime paths
        emit(
            {
                "status": "BACKUP_FAILED",
                "error": "Unexpected publisher failure; inspect private runtime logs",
                "committed": False,
                "pushed": False,
            }
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
