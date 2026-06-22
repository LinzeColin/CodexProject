#!/usr/bin/env python3
"""Codex Stop Hook for CodexProject governance validation."""

from __future__ import annotations

import json
import hashlib
import subprocess
import sys
import tempfile
import os
from datetime import datetime, timezone
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


def git_output(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def changed_files(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", "status", "--porcelain=v1"],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    files: list[str] = []
    for line in result.stdout.splitlines():
        if not line:
            continue
        files.append(line[3:] if len(line) > 3 else line)
    return sorted(files)


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
        Path(temp_name).replace(path)
    except Exception:
        Path(temp_name).unlink(missing_ok=True)
        raise


def write_receipt(
    root: Path,
    payload: dict[str, Any],
    started_at: str,
    commands: list[dict[str, Any]],
    final_status: str,
) -> str:
    completed_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    run_id = "STOP-HOOK-" + completed_at.replace(":", "").replace("+", "Z").replace("-", "")
    receipt = {
        "schema_version": 1,
        "run_id": run_id,
        "task_id": str(payload.get("task_id") or payload.get("TASK_ID") or "UNKNOWN"),
        "repository": git_output(root, "remote", "get-url", "origin") or str(root),
        "workspace_root": str(root),
        "base_commit": git_output(root, "rev-parse", "HEAD"),
        "source_tree_hash": git_output(root, "rev-parse", "HEAD^{tree}"),
        "hook_started_at": started_at,
        "hook_completed_at": completed_at,
        "commands": commands,
        "return_codes": [item["return_code"] for item in commands],
        "final_status": final_status,
        "changed_projects": [],
        "generated_views": [
            "README.md",
            "GOVERNANCE_DASHBOARD.md",
            "OWNER_PORTFOLIO.md",
            "governance/binding_backlog.yaml",
            "**/docs/governance/ASSURANCE_STATUS.yaml",
            "**/docs/governance/STATUS.md",
            "**/docs/governance/OWNER_STATUS.md",
        ],
        "changed_files": changed_files(root),
        "fact_level": "EXTRACTED",
    }
    receipts_dir = root / "governance" / "run_receipts"
    path = receipts_dir / f"{run_id}.json"
    atomic_write_json(path, receipt)
    return str(path.relative_to(root))


def main() -> int:
    payload = read_payload()
    started_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    cwd = Path(str(payload.get("cwd") or ".")).resolve()
    root = git_root(cwd)

    if root is None:
        emit({"continue": True})
        return 0

    marker = root / "governance" / "projects.yaml"
    validator = root / "scripts" / "validate_project_governance.py"
    quality_validator = root / "scripts" / "validate_information_quality.py"
    generator = root / "scripts" / "generate_governance_dashboard.py"
    setup_doctor = root / "scripts" / "governance_setup_doctor.py"

    if not marker.exists():
        emit({"continue": True})
        return 0

    required_scripts = [validator, quality_validator, generator, setup_doctor]
    missing_scripts = [str(path.relative_to(root)) for path in required_scripts if not path.exists()]
    if missing_scripts:
        emit(
            {
                "decision": "block",
                "reason": (
                    "Repository governance is enabled, but required governance scripts are missing. "
                    "Restore these files before completion: " + ", ".join(missing_scripts)
                ),
            }
        )
        return 0

    commands = [
        [sys.executable, str(generator), "--write", "--changed-only"],
        [sys.executable, str(validator), "--changed-only", "--enforce-sync", "--semantic"],
        [sys.executable, str(quality_validator), "--changed-only", "--fast", "--fail-on-error"],
        [sys.executable, str(generator), "--write", "--changed-only"],
        [
            "git",
            "diff",
            "--exit-code",
            "--",
            "README.md",
            "GOVERNANCE_DASHBOARD.md",
            "OWNER_PORTFOLIO.md",
            "governance/binding_backlog.yaml",
            ":(glob)**/docs/governance/ASSURANCE_STATUS.yaml",
            ":(glob)**/docs/governance/STATUS.md",
            ":(glob)**/docs/governance/OWNER_STATUS.md",
        ],
        [sys.executable, str(setup_doctor), "--json"],
    ]
    outputs: list[str] = []
    command_records: list[dict[str, Any]] = []
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
        command_records.append(
            {
                "command": label,
                "argv": command,
                "return_code": result.returncode,
                "stdout_tail": result.stdout[-2000:],
                "stderr_tail": result.stderr[-2000:],
            }
        )
        if result.returncode != 0:
            failed = True

    if not failed:
        receipt_ref = write_receipt(root, payload, started_at, command_records, "PASS")
        clear_attempt(root)
        emit({"continue": True, "governance_receipt": receipt_ref})
        return 0

    receipt_ref = write_receipt(root, payload, started_at, command_records, "FAIL")
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
            "governance_receipt": receipt_ref,
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
