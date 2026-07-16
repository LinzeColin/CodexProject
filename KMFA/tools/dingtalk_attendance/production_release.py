#!/usr/bin/env python3
"""Build and verify immutable KMFA attendance production releases."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


MANIFEST_NAME = "ATTENDANCE_PRODUCTION_RELEASE.json"
CURRENT_LINK_NAME = "current"
DEFAULT_RELEASE_ROOT = Path.home() / "Library/Application Support/Codex/KMFA/attendance-production"
STATIC_RELEASE_PATHS = (
    Path("KMFA/kmfa-dingtalk-attendance-skill/SKILL.md"),
    Path("KMFA/kmfa-dingtalk-attendance-skill/规则清单.md"),
    Path("KMFA/kmfa-dingtalk-attendance-skill/automation/morning_prompt.md"),
    Path("KMFA/kmfa-dingtalk-attendance-skill/automation/evening_prompt.md"),
    Path("KMFA/metadata/dingtalk_attendance/attendance_database_manifest.json"),
    Path("KMFA/metadata/dingtalk_attendance/codex_automation/morning_1035.prompt.md"),
    Path("KMFA/metadata/dingtalk_attendance/codex_automation/evening_2000.prompt.md"),
    Path("KMFA/metadata/dingtalk_attendance/notification_channel_manifest.json"),
    Path("KMFA/metadata/dingtalk_attendance/notification_policy.yaml"),
    Path("KMFA/metadata/dingtalk_attendance/notification_targets_manifest.json"),
    Path("KMFA/metadata/dingtalk_attendance/onedrive_storage_manifest.yaml"),
    Path("KMFA/metadata/dingtalk_attendance/report_policy.yaml"),
    Path("KMFA/metadata/dingtalk_attendance/retention_policy.yaml"),
    Path("KMFA/metadata/dingtalk_attendance/secrets_policy.md"),
)
FORBIDDEN_PARTS = frozenset({"private_runtime", "__pycache__"})
FORBIDDEN_SUFFIXES = (".sqlite", ".db", ".jsonl", ".jsonl.gz", ".raw.json", ".raw.jsonl", ".raw.jsonl.gz")
FORBIDDEN_NAMES = frozenset({".env", ".env.local"})


class ProductionReleaseError(RuntimeError):
    """Raised when a release cannot be built or verified safely."""


def release_relative_paths(source_root: Path) -> tuple[Path, ...]:
    tool_root = source_root / "KMFA/tools/dingtalk_attendance"
    tool_paths = tuple(
        sorted(
            (
                path.relative_to(source_root)
                for path in tool_root.rglob("*.py")
                if "__pycache__" not in path.parts
            ),
            key=lambda path: path.as_posix(),
        )
    )
    selected = tuple(sorted({*tool_paths, *STATIC_RELEASE_PATHS}, key=lambda path: path.as_posix()))
    for relative in selected:
        _validate_relative_path(relative)
        if not (source_root / relative).is_file():
            raise ProductionReleaseError(f"release source is missing: {relative.as_posix()}")
    return selected


def _validate_relative_path(relative: Path) -> None:
    if relative.is_absolute() or ".." in relative.parts:
        raise ProductionReleaseError(f"release path must be relative: {relative}")
    if FORBIDDEN_PARTS.intersection(relative.parts):
        raise ProductionReleaseError(f"forbidden release path: {relative.as_posix()}")
    if relative.name in FORBIDDEN_NAMES or relative.as_posix().endswith(FORBIDDEN_SUFFIXES):
        raise ProductionReleaseError(f"forbidden release file: {relative.as_posix()}")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _release_fingerprint(file_digests: Mapping[str, str]) -> str:
    digest = hashlib.sha256(b"kmfa-attendance-production-release-v1\0")
    for relative, file_digest in sorted(file_digests.items()):
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_digest.encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()


def verify_release(release_dir: Path) -> dict[str, Any]:
    resolved = release_dir.resolve(strict=True)
    manifest_path = resolved / MANIFEST_NAME
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProductionReleaseError("release manifest is missing or invalid") from exc
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1:
        raise ProductionReleaseError("release manifest schema is invalid")
    files = manifest.get("files")
    if not isinstance(files, dict) or not files:
        raise ProductionReleaseError("release file manifest is empty")
    expected: dict[str, str] = {}
    for raw_relative, raw_digest in files.items():
        relative = Path(str(raw_relative))
        _validate_relative_path(relative)
        path = resolved / relative
        if path.is_symlink() or not path.is_file():
            raise ProductionReleaseError(f"release file is missing or unsafe: {relative.as_posix()}")
        expected[relative.as_posix()] = str(raw_digest)
        actual_digest = _sha256(path)
        if actual_digest != raw_digest:
            raise ProductionReleaseError(f"release file checksum mismatch: {relative.as_posix()}")
    actual_files = {
        path.relative_to(resolved).as_posix()
        for path in resolved.rglob("*")
        if path.is_file() and path.name != MANIFEST_NAME
    }
    if actual_files != set(expected):
        raise ProductionReleaseError("release contains an unmanifested or missing file")
    fingerprint = _release_fingerprint(expected)
    if fingerprint != manifest.get("attendance_runtime_fingerprint"):
        raise ProductionReleaseError("release fingerprint mismatch")
    return {
        "status": "PASS",
        "release_dir": str(resolved),
        "attendance_runtime_fingerprint": fingerprint,
        "source_commit": str(manifest.get("source_commit") or ""),
        "file_count": len(expected),
    }


def build_release(
    *,
    source_root: Path,
    source_commit: str,
    release_root: Path = DEFAULT_RELEASE_ROOT,
    activate: bool = False,
) -> dict[str, Any]:
    source_root = source_root.resolve(strict=True)
    relative_paths = release_relative_paths(source_root)
    file_digests = {relative.as_posix(): _sha256(source_root / relative) for relative in relative_paths}
    fingerprint = _release_fingerprint(file_digests)
    release_root.mkdir(parents=True, exist_ok=True)
    os.chmod(release_root, 0o700)
    final_dir = release_root / fingerprint
    if not final_dir.exists():
        candidate = Path(tempfile.mkdtemp(prefix=".candidate-", dir=release_root))
        try:
            for relative in relative_paths:
                destination = candidate / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source_root / relative, destination)
            manifest = {
                "schema_version": 1,
                "kind": "KMFA_ATTENDANCE_PRODUCTION_RELEASE",
                "attendance_runtime_fingerprint": fingerprint,
                "source_commit": source_commit,
                "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "files": file_digests,
                "public_safety": {
                    "secrets_included": False,
                    "raw_attendance_included": False,
                    "sqlite_included": False,
                    "employee_report_data_included": False,
                },
            }
            (candidate / MANIFEST_NAME).write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            verify_release(candidate)
            for path in sorted(candidate.rglob("*"), key=lambda item: len(item.parts), reverse=True):
                os.chmod(path, 0o555 if path.is_dir() else 0o444)
            os.chmod(candidate, 0o555)
            os.replace(candidate, final_dir)
        except Exception:
            if candidate.exists():
                for path in candidate.rglob("*"):
                    try:
                        os.chmod(path, 0o700 if path.is_dir() else 0o600)
                    except OSError:
                        pass
                shutil.rmtree(candidate, ignore_errors=True)
            raise
    verification = verify_release(final_dir)
    if activate:
        activate_release(final_dir=final_dir, release_root=release_root)
    return {
        **verification,
        "current": str(release_root / CURRENT_LINK_NAME) if activate else None,
        "activated": activate,
    }


def activate_release(*, final_dir: Path, release_root: Path = DEFAULT_RELEASE_ROOT) -> None:
    verification = verify_release(final_dir)
    if final_dir.parent.resolve() != release_root.resolve():
        raise ProductionReleaseError("release is outside the configured production root")
    temporary_link = release_root / f".{CURRENT_LINK_NAME}-{uuid.uuid4().hex}"
    temporary_link.symlink_to(final_dir.name, target_is_directory=True)
    try:
        os.replace(temporary_link, release_root / CURRENT_LINK_NAME)
    finally:
        if temporary_link.exists() or temporary_link.is_symlink():
            temporary_link.unlink()
    current = verify_release(release_root / CURRENT_LINK_NAME)
    if current["attendance_runtime_fingerprint"] != verification["attendance_runtime_fingerprint"]:
        raise ProductionReleaseError("atomic current release readback mismatch")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build or verify an immutable KMFA attendance release.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    build_parser = subparsers.add_parser("build")
    build_parser.add_argument("--source-root", type=Path, required=True)
    build_parser.add_argument("--source-commit", required=True)
    build_parser.add_argument("--release-root", type=Path, default=DEFAULT_RELEASE_ROOT)
    build_parser.add_argument("--activate", action="store_true")
    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("--release", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "build":
            result = build_release(
                source_root=args.source_root,
                source_commit=args.source_commit,
                release_root=args.release_root,
                activate=args.activate,
            )
        else:
            result = verify_release(args.release)
    except (OSError, ValueError, ProductionReleaseError) as exc:
        print(json.dumps({"status": "FAILED", "error_code": exc.__class__.__name__, "detail": str(exc)}))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
