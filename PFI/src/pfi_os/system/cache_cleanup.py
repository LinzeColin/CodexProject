from __future__ import annotations

import argparse
import json
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from pfi_os.config import PROJECT_ROOT


CACHE_DIR_NAMES = frozenset({"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".ipynb_checkpoints"})
SKIP_DIR_NAMES = frozenset({".git", ".venv", "venv", "node_modules"})
DISPOSABLE_FILE_NAMES = frozenset({".DS_Store"})
DISPOSABLE_FILE_SUFFIXES = frozenset({".pyc", ".pyo"})
ROOT_RUNTIME_CACHE_FILE_PATTERNS = ("*.log", "*.pid", "*.lock", "*.tmp")


@dataclass(frozen=True)
class DisposablePath:
    path: Path
    kind: str
    bytes_count: int
    file_count: int
    dir_count: int


def build_cache_cleanup_report(root: Path | None = None, *, dry_run: bool = True) -> dict:
    project_root = (root or PROJECT_ROOT).resolve()
    candidates = list(iter_disposable_paths(project_root))
    removed: list[str] = []
    failed: list[dict[str, str]] = []
    if not dry_run:
        for item in candidates:
            try:
                _remove_path(item.path)
                removed.append(_relative(item.path, project_root))
            except OSError as exc:
                failed.append({"path": _relative(item.path, project_root), "error": str(exc)})
    candidate_bytes = sum(item.bytes_count for item in candidates)
    return {
        "schema": "PFICacheCleanupReportV1",
        "mode": "dry_run" if dry_run else "delete",
        "root": str(project_root),
        "candidate_count": len(candidates),
        "candidate_file_count": sum(item.file_count for item in candidates),
        "candidate_dir_count": sum(item.dir_count for item in candidates),
        "candidate_bytes": candidate_bytes,
        "candidate_kb": round(candidate_bytes / 1024, 2),
        "removed_count": len(removed),
        "removed_paths": removed[:200],
        "failed_count": len(failed),
        "failed": failed,
        "candidates": [
            {
                "path": _relative(item.path, project_root),
                "kind": item.kind,
                "bytes": item.bytes_count,
                "files": item.file_count,
                "dirs": item.dir_count,
            }
            for item in candidates[:200]
        ],
        "safety_boundary": (
            "Only disposable local runtime artifacts are eligible: Python bytecode, test/tool cache "
            "directories, .DS_Store files, and root-level data/cache runtime logs. Reports, holdings, "
            "imports, source files, SQLite databases, and market bar caches are not deleted."
        ),
    }


def iter_disposable_paths(root: Path) -> Iterable[DisposablePath]:
    root = root.resolve()
    seen: set[Path] = set()
    for current, dirs, files in os.walk(root, topdown=True, followlinks=False):
        current_path = Path(current)
        dirs[:] = [name for name in dirs if name not in SKIP_DIR_NAMES]
        for dirname in list(dirs):
            if dirname in CACHE_DIR_NAMES:
                path = current_path / dirname
                resolved = path.resolve()
                if resolved not in seen:
                    seen.add(resolved)
                    yield _disposable_path(path, "cache_dir")
                dirs.remove(dirname)
        for filename in files:
            path = current_path / filename
            if filename in DISPOSABLE_FILE_NAMES or path.suffix in DISPOSABLE_FILE_SUFFIXES:
                resolved = path.resolve()
                if resolved not in seen:
                    seen.add(resolved)
                    yield _disposable_path(path, "cache_file")

    runtime_cache = root / "data" / "cache"
    if runtime_cache.exists():
        for pattern in ROOT_RUNTIME_CACHE_FILE_PATTERNS:
            for path in runtime_cache.glob(pattern):
                if path.is_file() and path.name != ".gitkeep":
                    resolved = path.resolve()
                    if resolved not in seen:
                        seen.add(resolved)
                        yield _disposable_path(path, "runtime_cache_file")


def format_cache_cleanup_report(report: dict) -> str:
    action = "would remove" if report["mode"] == "dry_run" else "removed"
    lines = [
        "PFI cache cleanup",
        f"Mode: {report['mode']}",
        f"Candidates: {report['candidate_count']} paths, {report['candidate_file_count']} files, "
        f"{report['candidate_dir_count']} directories, {report['candidate_kb']} KB",
        f"Result: {action} {report['removed_count']} paths",
        f"Failed: {report['failed_count']}",
        f"Boundary: {report['safety_boundary']}",
    ]
    return "\n".join(lines)


def _disposable_path(path: Path, kind: str) -> DisposablePath:
    bytes_count, file_count, dir_count = _path_stats(path)
    return DisposablePath(path=path, kind=kind, bytes_count=bytes_count, file_count=file_count, dir_count=dir_count)


def _path_stats(path: Path) -> tuple[int, int, int]:
    if path.is_dir() and not path.is_symlink():
        total = 0
        files = 0
        dirs = 1
        for child in path.rglob("*"):
            try:
                stat = child.lstat()
            except OSError:
                continue
            if child.is_dir() and not child.is_symlink():
                dirs += 1
            else:
                files += 1
                total += stat.st_size
        return total, files, dirs
    try:
        return path.lstat().st_size, 1, 0
    except OSError:
        return 0, 0, 0


def _remove_path(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink(missing_ok=True)


def _relative(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root))
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Safely preview or clean PFI runtime cache artifacts.")
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--dry-run", action="store_true", help="Preview candidates without deleting them.")
    parser.add_argument("--json", action="store_true", help="Write machine-readable JSON output.")
    args = parser.parse_args(argv)

    report = build_cache_cleanup_report(args.root, dry_run=args.dry_run)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(format_cache_cleanup_report(report))
    return 0 if report["failed_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
