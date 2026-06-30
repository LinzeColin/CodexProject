#!/usr/bin/env python3
"""Install the scheduled Codex data sync LaunchAgent for Memory Atlas.

The filename is kept for compatibility with existing docs and operator
commands. The installed LaunchAgent label is kept stable, while the schedule is
Monday, Wednesday, and Friday at 03:00 local time.
"""

from __future__ import annotations

import argparse
import json
import plistlib
import subprocess
from pathlib import Path
from typing import Any


LABEL = "com.linze.openai-database.codex-daily-sync"
LEGACY_LABEL = "com.linze.openai-database.codex-weekly-sync"
DEFAULT_PLIST = Path.home() / "Library/LaunchAgents" / f"{LABEL}.plist"
DEFAULT_LOG_DIR = Path.home() / "Library/Logs/OpenAIDatabase"
SCHEDULE = [
    {"Weekday": 1, "Hour": 3, "Minute": 0},
    {"Weekday": 3, "Hour": 3, "Minute": 0},
    {"Weekday": 5, "Hour": 3, "Minute": 0},
]
SCHEDULE_LABEL = "每周一、周三和周五 03:00 本地时间"


def write_plist(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = plistlib.dumps(data, sort_keys=True)
    if path.exists() and path.read_bytes() == payload:
        return
    path.write_bytes(payload)


def launchctl(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["launchctl", *args], text=True, capture_output=True, check=False)


def legacy_plist_for(plist_path: Path) -> Path:
    return plist_path.with_name(f"{LEGACY_LABEL}.plist")


def is_git_worktree(repo_root: Path) -> bool:
    proc = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "--is-inside-work-tree"],
        text=True,
        capture_output=True,
        check=False,
    )
    return proc.returncode == 0 and proc.stdout.strip() == "true"


def install_agent(repo_root: Path, plist_path: Path, *, load: bool) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    log_dir = DEFAULT_LOG_DIR
    log_dir.mkdir(parents=True, exist_ok=True)
    python_bin = "/usr/bin/python3"
    update_script = repo_root / "scripts/run_codex_memory_auto_update.py"
    if not update_script.exists():
        raise SystemExit(f"missing auto-update script: {update_script}")
    git_backup_enabled = is_git_worktree(repo_root)
    program_args = [
        python_bin,
        str(update_script),
        "--database-dir",
        str(repo_root),
        "--publish-runtime",
    ]
    if git_backup_enabled:
        program_args.extend(["--commit", "--push"])

    plist = {
        "Label": LABEL,
        "ProgramArguments": program_args,
        "RunAtLoad": False,
        "StartCalendarInterval": SCHEDULE,
        "StandardOutPath": str(log_dir / "codex-daily-sync.log"),
        "StandardErrorPath": str(log_dir / "codex-daily-sync.err.log"),
        "WorkingDirectory": str(repo_root),
    }
    write_plist(plist_path, plist)

    load_result = {"attempted": False, "returncode": None, "stdout": "", "stderr": ""}
    if load:
        uid = subprocess.check_output(["id", "-u"], text=True).strip()
        domain = f"gui/{uid}"
        unload = launchctl(["bootout", domain, str(plist_path)])
        legacy_plist = legacy_plist_for(plist_path)
        legacy_unload = {"attempted": False, "returncode": None, "stdout": "", "stderr": "", "plist_removed": False}
        if legacy_plist.exists():
            legacy_proc = launchctl(["bootout", domain, str(legacy_plist)])
            legacy_plist.unlink(missing_ok=True)
            legacy_unload = {
                "attempted": True,
                "returncode": legacy_proc.returncode,
                "stdout": legacy_proc.stdout.strip(),
                "stderr": legacy_proc.stderr.strip(),
                "plist_removed": not legacy_plist.exists(),
            }
        load_proc = launchctl(["bootstrap", domain, str(plist_path)])
        enable_proc = launchctl(["enable", f"{domain}/{LABEL}"])
        load_result = {
            "attempted": True,
            "returncode": load_proc.returncode,
            "stdout": load_proc.stdout.strip(),
            "stderr": load_proc.stderr.strip(),
            "bootout_returncode": unload.returncode,
            "enable_returncode": enable_proc.returncode,
            "uid": uid,
            "legacy_migration": legacy_unload,
        }

    return {
        "status": "PASS",
        "label": LABEL,
        "plist": str(plist_path),
        "schedule": SCHEDULE_LABEL,
        "program": plist["ProgramArguments"],
        "git_backup": {
            "enabled": git_backup_enabled,
            "reason": "database_dir_is_git_worktree" if git_backup_enabled else "database_dir_is_runtime_source_without_git",
        },
        "stdout_log": plist["StandardOutPath"],
        "stderr_log": plist["StandardErrorPath"],
        "loaded": load_result,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install Monday/Wednesday/Friday 03:00 Codex data sync LaunchAgent.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--plist", type=Path, default=DEFAULT_PLIST)
    parser.add_argument("--load", action="store_true", help="Load or reload the LaunchAgent after writing the plist.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = install_agent(args.repo_root, args.plist.expanduser(), load=args.load)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
