#!/usr/bin/env python3
"""Codex Stop Hook for CodexProject governance validation."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


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
    )
    if result.returncode != 0:
        return None
    return Path(result.stdout.strip())


def main() -> int:
    payload = read_payload()

    # Avoid infinite repair loops. A second Stop pass should leave final hard
    # enforcement to GitHub CI and the explicit validator command.
    if payload.get("stop_hook_active"):
        emit({"continue": True})
        return 0

    cwd = Path(str(payload.get("cwd") or ".")).resolve()
    root = git_root(cwd)

    if root is None:
        emit({"continue": True})
        return 0

    marker = root / "governance" / "projects.yaml"
    validator = root / "scripts" / "validate_project_governance.py"

    if not marker.exists():
        emit({"continue": True})
        return 0

    if not validator.exists():
        emit(
            {
                "decision": "block",
                "reason": (
                    "Repository governance is enabled, but "
                    "scripts/validate_project_governance.py is missing. "
                    "Create or restore the validator before completion."
                ),
            }
        )
        return 0

    result = subprocess.run(
        [sys.executable, str(validator), "--changed-only"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )

    if result.returncode == 0:
        emit({"continue": True})
        return 0

    output = (result.stdout + "\n" + result.stderr).strip()[-6000:]
    emit(
        {
            "decision": "block",
            "reason": (
                "Project governance validation failed. Fix the focused "
                "findings, rerun the validator, and do not mark the task "
                "completed.\n\n" + output
            ),
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
