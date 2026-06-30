#!/usr/bin/env python3
"""Run the scheduled Codex memory sync and publish the latest Atlas runtime."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any


DEFAULT_RUNTIME_DIR = Path.home() / "Library/Application Support/OpenAIDatabase/MemoryAtlas/runtime"
SOURCE_MANIFEST = "memory_atlas_source_workspace.json"


class AutoUpdateError(RuntimeError):
    pass


def run_command(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(args, cwd=str(cwd), text=True, capture_output=True, check=False)
    if proc.returncode != 0:
        raise AutoUpdateError(
            json.dumps(
                {
                    "command": args,
                    "cwd": str(cwd),
                    "returncode": proc.returncode,
                    "stdout": proc.stdout[-4000:],
                    "stderr": proc.stderr[-4000:],
                },
                ensure_ascii=False,
            )
        )
    return proc


def current_git_commit(repo_root: Path) -> str | None:
    proc = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode == 0:
        commit = proc.stdout.strip()
        if commit:
            return commit
    return None


def installed_source_commit(repo_root: Path) -> str | None:
    manifest_path = repo_root / SOURCE_MANIFEST
    if not manifest_path.exists():
        return None
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    commit = manifest.get("installed_git_commit")
    return commit if isinstance(commit, str) and commit else None


def build_commit_id(repo_root: Path) -> str:
    return current_git_commit(repo_root) or installed_source_commit(repo_root) or "unknown"


def run_sync(database_dir: Path, codex_home: Path, *, commit: bool, push: bool) -> dict[str, Any]:
    script = database_dir / "scripts/sync_codex_memory_data.py"
    if not script.exists():
        raise AutoUpdateError(f"missing sync script: {script}")
    args = [
        sys.executable,
        str(script),
        "--database-dir",
        str(database_dir),
        "--codex-home",
        str(codex_home),
        "--build-atlas",
    ]
    if commit or push:
        args.append("--commit")
    if push:
        args.append("--push")
    proc = run_command(args, database_dir)
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"status": "PASS", "stdout": proc.stdout.strip()}


def should_export_session_history(now: datetime | None = None) -> bool:
    return (now or datetime.now()).isoweekday() == 1


def run_history_exports(database_dir: Path, codex_home: Path, *, include_session_history: bool) -> dict[str, Any]:
    script = database_dir / "scripts/export_codex_history_archives.py"
    if not script.exists():
        raise AutoUpdateError(f"missing history export script: {script}")
    args = [
        sys.executable,
        str(script),
        "--database-dir",
        str(database_dir),
        "--codex-home",
        str(codex_home),
        "--token-usage",
    ]
    if include_session_history:
        args.append("--session-history")
    proc = run_command(args, database_dir)
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"status": "PASS", "stdout": proc.stdout.strip()}


def write_runtime_build_info(repo_root: Path, runtime_dir: Path) -> dict[str, Any]:
    snapshot_path = runtime_dir / "memory_atlas.json"
    snapshot_generated_at = ""
    if snapshot_path.exists():
        try:
            snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            snapshot = {}
        overview = snapshot.get("overview") if isinstance(snapshot, dict) else None
        if isinstance(overview, dict):
            snapshot_generated_at = str(overview.get("generated_at") or "")
    payload = {
        "schema_version": "memory_atlas_build.v1",
        "git_commit": build_commit_id(repo_root),
        "built_at_epoch": int(time.time()),
        "snapshot_generated_at": snapshot_generated_at,
        "snapshot_mtime_epoch": int(snapshot_path.stat().st_mtime) if snapshot_path.exists() else None,
    }
    build_info_path = runtime_dir / "memory_atlas_build.json"
    build_info_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def publish_runtime_snapshot(database_dir: Path, runtime_dir: Path, *, run_audits: bool) -> dict[str, Any]:
    snapshot_path = database_dir / "data/derived/visualization/memory_atlas.json"
    if not snapshot_path.exists():
        raise AutoUpdateError(f"missing Atlas snapshot after sync: {snapshot_path}")
    if not runtime_dir.exists() or not (runtime_dir / "index.html").exists():
        return {
            "published": False,
            "reason": "runtime_missing_or_unprepared",
            "runtime_dir": str(runtime_dir),
            "source_snapshot": str(snapshot_path),
        }

    runtime_snapshot = runtime_dir / "memory_atlas.json"
    shutil.copy2(snapshot_path, runtime_snapshot)
    build_info = write_runtime_build_info(database_dir, runtime_dir)

    audits: list[dict[str, Any]] = []
    if run_audits:
        for script_name in ("audit_memory_atlas_release.py", "audit_memory_atlas_acceptance.py"):
            script = database_dir / "scripts" / script_name
            if script.exists():
                run_command([sys.executable, str(script), "--repo-root", str(database_dir), "--publish-dir", str(runtime_dir)], database_dir)
                audits.append({"script": script_name, "status": "PASS"})

    return {
        "published": True,
        "runtime_dir": str(runtime_dir),
        "runtime_snapshot": str(runtime_snapshot),
        "build_info": build_info,
        "audits": audits,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run scheduled Codex memory sync and publish Memory Atlas runtime snapshot.")
    parser.add_argument("--database-dir", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--codex-home", type=Path, default=Path.home() / ".codex")
    parser.add_argument("--runtime-dir", type=Path, default=DEFAULT_RUNTIME_DIR)
    parser.add_argument("--publish-runtime", action="store_true", help="Copy the rebuilt Atlas snapshot into the local runtime directory.")
    parser.add_argument("--skip-runtime-audit", action="store_true", help="Skip release and acceptance audits after publishing runtime snapshot.")
    parser.add_argument("--commit", action="store_true", help="Commit changed redacted Codex derived data when database-dir is a Git worktree.")
    parser.add_argument("--push", action="store_true", help="Push after committing. Implies --commit.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    database_dir = args.database_dir.expanduser().resolve()
    runtime_dir = args.runtime_dir.expanduser().resolve()
    result = {
        "status": "PASS",
        "database_dir": str(database_dir),
        "history_exports": run_history_exports(
            database_dir,
            args.codex_home,
            include_session_history=should_export_session_history(),
        ),
        "sync": run_sync(database_dir, args.codex_home, commit=args.commit or args.push, push=args.push),
        "runtime": {"published": False, "reason": "not_requested"},
    }
    if args.publish_runtime:
        result["runtime"] = publish_runtime_snapshot(database_dir, runtime_dir, run_audits=not args.skip_runtime_audit)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AutoUpdateError as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        raise SystemExit(1)
