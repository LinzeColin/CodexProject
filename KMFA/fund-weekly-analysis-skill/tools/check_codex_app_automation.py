#!/usr/bin/env python3
"""Validate the local Codex App automation against the tracked S21 contract."""
from __future__ import annotations

import argparse
import json
import os
import sys
import tomllib
from pathlib import Path


CHECK_FIELDS = [
    "id",
    "name",
    "kind",
    "status",
    "rrule",
    "execution_environment",
    "cwds",
    "model",
    "reasoning_effort",
]


def load_toml(path: Path) -> dict:
    return tomllib.loads(path.read_text(encoding="utf-8"))


def emit(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=os.environ.get("KMFA_REPO_ROOT", "."))
    parser.add_argument("--automation-root", default=str(Path.home() / ".codex" / "automations"))
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    skill_root = repo_root / "KMFA" / "fund-weekly-analysis-skill"
    contract_path = skill_root / "automation" / "codex_app_automation.contract.toml"
    if not contract_path.exists():
        emit({"status": "CODEX_AUTOMATION_CONTRACT_MISSING", "contract_path": str(contract_path)})
        return 2

    contract = load_toml(contract_path)
    automation_path = Path(args.automation_root).expanduser() / contract["id"] / "automation.toml"
    if not automation_path.exists():
        emit({
            "status": "CODEX_AUTOMATION_MISSING",
            "automation_id": contract["id"],
            "automation_path": str(automation_path),
        })
        return 2

    live = load_toml(automation_path)
    mismatches = []
    for field in CHECK_FIELDS:
        if live.get(field) != contract.get(field):
            mismatches.append({"field": field, "expected": contract.get(field), "actual": live.get(field)})

    prompt_file = skill_root / contract["prompt_file"]
    if live.get("prompt") is not None and prompt_file.exists():
        expected_prompt = prompt_file.read_text(encoding="utf-8").strip()
        if live["prompt"].strip() != expected_prompt:
            mismatches.append({"field": "prompt", "expected": str(prompt_file), "actual": "automation.toml prompt differs"})

    if mismatches:
        emit({
            "status": "CODEX_AUTOMATION_MISMATCH",
            "automation_id": contract["id"],
            "automation_path": str(automation_path),
            "mismatches": mismatches,
        })
        return 4

    emit({
        "status": "CODEX_AUTOMATION_READY",
        "automation_id": contract["id"],
        "automation_path": str(automation_path),
        "rrule": contract["rrule"],
        "cwd": contract["cwds"][0],
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
