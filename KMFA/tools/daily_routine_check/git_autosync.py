from __future__ import annotations

import argparse
import subprocess
import time
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
ALLOWED_PREFIXES = [
    "KMFA/daily_routine_check_skill/",
    "KMFA/metadata/daily_routine_check/",
    "KMFA/tools/daily_routine_check/",
    "KMFA/tests/test_daily_routine_check.py",
]
BLOCKED_SUFFIXES = (".sqlite", ".db", ".jsonl", ".gz")
BLOCKED_PARTS = ("private_runtime", ".env.local", "DWS_Outputs")
VALIDATION_COMMANDS = [
    ["python3", "KMFA/daily_routine_check_skill/tools/validate_skill_package.py"],
    ["python3", "-m", "unittest", "KMFA.tests.test_daily_routine_check", "-q"],
    ["git", "diff", "--check"],
]


def run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    print("+", " ".join(cmd))
    return subprocess.run(cmd, cwd=REPO_ROOT, text=True, capture_output=False, check=check)


def get_changed_paths() -> list[str]:
    cp = subprocess.run(["git", "status", "--porcelain"], cwd=REPO_ROOT, text=True, capture_output=True, check=True)
    paths = []
    for line in cp.stdout.splitlines():
        if not line.strip():
            continue
        # porcelain: XY path or XY old -> new
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        paths.append(path)
    return paths


def is_allowed(path: str) -> bool:
    return any(path == p or path.startswith(p) for p in ALLOWED_PREFIXES)


def is_blocked(path: str) -> bool:
    return path.endswith(BLOCKED_SUFFIXES) or any(part in path for part in BLOCKED_PARTS)


def sync_once() -> int:
    branch = subprocess.check_output(["git", "branch", "--show-current"], cwd=REPO_ROOT, text=True).strip()
    if branch != "main":
        raise SystemExit(f"Refusing autosync on branch {branch!r}; main required")

    changed = get_changed_paths()
    if not changed:
        print("No changes to sync.")
        return 0
    disallowed = [p for p in changed if not is_allowed(p) or is_blocked(p)]
    if disallowed:
        raise SystemExit("Refusing autosync due to disallowed/blocked paths: " + ", ".join(disallowed))

    for cmd in VALIDATION_COMMANDS:
        run(cmd)

    run(["git", "fetch", "origin", "main"])
    run(["git", "pull", "--ff-only", "origin", "main"])
    run(["git", "add"] + ALLOWED_PREFIXES)
    message = "daily-routine-check: autosync validated changes " + datetime.now().strftime("%Y%m%d-%H%M%S")
    run(["git", "commit", "-m", message])
    run(["git", "push", "origin", "main"])
    run(["git", "fetch", "origin", "main"])
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True).strip()
    origin = subprocess.check_output(["git", "rev-parse", "origin/main"], cwd=REPO_ROOT, text=True).strip()
    if head != origin:
        raise SystemExit(f"Post-push parity failed: HEAD={head} origin/main={origin}")
    print(f"Autosync complete: {head}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--watch", action="store_true")
    ap.add_argument("--interval-seconds", type=int, default=60)
    args = ap.parse_args()
    if args.watch:
        while True:
            try:
                sync_once()
            except Exception as exc:
                print(f"autosync_error={exc}")
            time.sleep(args.interval_seconds)
    return sync_once()


if __name__ == "__main__":
    raise SystemExit(main())
