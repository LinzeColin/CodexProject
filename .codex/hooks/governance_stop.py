#!/usr/bin/env python3
"""Lightweight Codex Stop Hook for CodexProject governance hints.

The Stop Hook is intentionally outside the expensive governance proof path.
It must not generate files, write receipts, run semantic validators, or block a
turn because a derived dashboard or attestation needs recomputation.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


GOVERNANCE_PREFIXES = (
    ".codex/",
    ".github/workflows/project-governance.yml",
    "AGENTS.md",
    "docs/governance/",
    "governance/",
    "scripts/",
    "tests/governance/",
)


def emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False))


def read_payload() -> dict[str, Any]:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def git_root(cwd: Path) -> Path | None:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
        timeout=1.0,
    )
    if result.returncode != 0:
        return None
    return Path(result.stdout.strip())


def changed_files(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", "status", "--porcelain=v1"],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
        timeout=1.5,
    )
    if result.returncode != 0:
        return []
    files: list[str] = []
    for line in result.stdout.splitlines():
        if not line:
            continue
        path = line[3:] if len(line) > 3 else line
        if " -> " in path:
            path = path.rsplit(" -> ", 1)[1]
        files.append(path.replace("\\", "/"))
    return sorted(files)


def touches_governance(path: str) -> bool:
    return any(path == prefix.rstrip("/") or path.startswith(prefix) for prefix in GOVERNANCE_PREFIXES)


def main() -> int:
    payload = read_payload()
    cwd = Path(str(payload.get("cwd") or ".")).resolve()
    try:
        root = git_root(cwd)
    except (OSError, subprocess.SubprocessError):
        emit({"continue": True})
        return 0

    if root is None or not (root / "governance" / "projects.yaml").exists():
        emit({"continue": True})
        return 0

    try:
        files = changed_files(root)
    except (OSError, subprocess.SubprocessError):
        emit({"continue": True})
        return 0

    governance_files = [path for path in files if touches_governance(path)]
    hint: dict[str, Any] = {
        "mode": "advisory",
        "changed_files": len(files),
        "governance_changed_files": governance_files[:20],
        "message": (
            "Stop Hook is advisory only. Run explicit governance validation before PR, "
            "release, or high-risk governance changes."
        ),
    }
    if governance_files:
        hint["suggested_commands"] = [
            "python3 scripts/validate_project_governance.py --changed-only --enforce-sync --semantic",
            "python3 -m unittest discover -s tests/governance -p 'test_*.py' -q",
        ]

    emit({"continue": True, "governance_hint": hint})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
