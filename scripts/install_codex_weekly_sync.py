#!/usr/bin/env python3
"""Install the weekly Codex data sync LaunchAgent for Memory Atlas."""

from __future__ import annotations

import argparse
import json
import plistlib
import subprocess
from pathlib import Path
from typing import Any


LABEL = "com.linze.openai-database.codex-weekly-sync"
DEFAULT_PLIST = Path.home() / "Library/LaunchAgents" / f"{LABEL}.plist"
DEFAULT_LOG_DIR = Path.home() / "Library/Logs/OpenAIDatabase"


def write_plist(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = plistlib.dumps(data, sort_keys=True)
    if path.exists() and path.read_bytes() == payload:
        return
    path.write_bytes(payload)


def launchctl(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["launchctl", *args], text=True, capture_output=True, check=False)


def install_agent(repo_root: Path, plist_path: Path, *, load: bool) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    log_dir = DEFAULT_LOG_DIR
    log_dir.mkdir(parents=True, exist_ok=True)
    python_bin = "/usr/bin/python3"
    sync_script = repo_root / "scripts/sync_codex_memory_data.py"
    if not sync_script.exists():
        raise SystemExit(f"missing sync script: {sync_script}")

    plist = {
        "Label": LABEL,
        "ProgramArguments": [
            python_bin,
            str(sync_script),
            "--database-dir",
            str(repo_root),
            "--build-atlas",
            "--commit",
            "--push",
        ],
        "RunAtLoad": False,
        "StartCalendarInterval": {
            "Weekday": 1,
            "Hour": 9,
            "Minute": 0,
        },
        "StandardOutPath": str(log_dir / "codex-weekly-sync.log"),
        "StandardErrorPath": str(log_dir / "codex-weekly-sync.err.log"),
        "WorkingDirectory": str(repo_root),
    }
    write_plist(plist_path, plist)

    load_result = {"attempted": False, "returncode": None, "stdout": "", "stderr": ""}
    if load:
        uid = subprocess.check_output(["id", "-u"], text=True).strip()
        domain = f"gui/{uid}"
        unload = launchctl(["bootout", domain, str(plist_path)])
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
        }

    return {
        "status": "PASS",
        "label": LABEL,
        "plist": str(plist_path),
        "schedule": "每周一 09:00 本地时间",
        "program": plist["ProgramArguments"],
        "stdout_log": plist["StandardOutPath"],
        "stderr_log": plist["StandardErrorPath"],
        "loaded": load_result,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install weekly Codex data sync LaunchAgent.")
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
