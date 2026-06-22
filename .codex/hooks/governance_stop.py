#!/usr/bin/env python3
"""Codex Stop Hook for CodexProject governance validation."""

from __future__ import annotations

import json
import hashlib
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

MAX_ATTEMPTS = 3
STATE_FILE = Path(tempfile.gettempdir()) / "codexproject-governance-stop-hook-state.json"


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


def repo_state_key(root: Path) -> str:
    commands = (
        ["git", "rev-parse", "HEAD"],
        ["git", "-c", "core.quotePath=false", "status", "--porcelain=v1"],
    )
    digest = hashlib.sha256(str(root).encode("utf-8"))
    for command in commands:
        result = subprocess.run(
            command,
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
        digest.update(result.stdout.encode("utf-8", errors="replace"))
    return digest.hexdigest()


def read_state() -> dict[str, int]:
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return {str(key): int(value) for key, value in data.items() if isinstance(value, int)}


def write_state(state: dict[str, int]) -> None:
    STATE_FILE.write_text(json.dumps(state, sort_keys=True), encoding="utf-8")


def record_attempt(root: Path) -> int:
    state = read_state()
    key = repo_state_key(root)
    state[key] = state.get(key, 0) + 1
    write_state(state)
    return state[key]


def clear_attempt(root: Path) -> None:
    state = read_state()
    key = repo_state_key(root)
    if key in state:
        del state[key]
        write_state(state)


def main() -> int:
    payload = read_payload()

    cwd = Path(str(payload.get("cwd") or ".")).resolve()
    root = git_root(cwd)

    if root is None:
        emit({"continue": True})
        return 0

    marker = root / "governance" / "projects.yaml"
    validator = root / "scripts" / "validate_project_governance.py"
    quality_validator = root / "scripts" / "validate_information_quality.py"

    if not marker.exists():
        emit({"continue": True})
        return 0

    if not validator.exists() or not quality_validator.exists():
        emit(
            {
                "decision": "block",
                "reason": (
                    "Repository governance is enabled, but one required validator is missing. "
                    "Restore scripts/validate_project_governance.py and "
                    "scripts/validate_information_quality.py before completion."
                ),
            }
        )
        return 0

    commands = [
        [sys.executable, str(validator), "--changed-only", "--enforce-sync", "--semantic"],
        [sys.executable, str(quality_validator), "--all", "--fast", "--fail-on-error"],
    ]
    outputs: list[str] = []
    failed = False
    for command in commands:
        result = subprocess.run(
            command,
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
        label = " ".join(Path(part).name if idx == 1 else part for idx, part in enumerate(command))
        outputs.append(f"$ {label}\n{result.stdout}\n{result.stderr}".strip())
        if result.returncode != 0:
            failed = True

    if not failed:
        clear_attempt(root)
        emit({"continue": True})
        return 0

    attempt = record_attempt(root)
    output = "\n\n".join(outputs).strip()[-6000:]
    prefix = (
        f"Project governance validation failed on Stop Hook attempt {attempt}/{MAX_ATTEMPTS}. "
    )
    if payload.get("stop_hook_active"):
        prefix += "This is a recursive Stop pass, but governance is still rechecked. "
    if attempt >= MAX_ATTEMPTS:
        prefix += "Maximum automatic repair attempts reached; run the validator manually and continue only after it passes. "
    emit(
        {
            "decision": "block",
            "reason": (
                prefix
                + "Fix the focused "
                "findings, rerun the validator, and do not mark the task "
                "completed.\n\n" + output
            ),
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
