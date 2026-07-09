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
EXPECTED_CONTRACT_FIELDS = {
    "rrule": "RRULE:FREQ=WEEKLY;BYDAY=MO,SA;BYHOUR=11;BYMINUTE=0",
    "timezone": "Australia/Sydney",
    "prompt_file": "automation/weekly_mon_sat_1100_sydney.prompt.md",
    "input_dir": "/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs/付款请示群",
    "source_readiness_gate": "tools/check_source_readiness.py",
    "branch_policy": "main_only_no_branch_no_pr_no_worktree",
}


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
    invalid_contract_fields = []
    for field, expected in EXPECTED_CONTRACT_FIELDS.items():
        actual = contract.get(field)
        if actual != expected:
            invalid_contract_fields.append({"field": field, "expected": expected, "actual": actual})
    if invalid_contract_fields:
        emit({
            "status": "CODEX_AUTOMATION_CONTRACT_INVALID",
            "automation_id": contract.get("id"),
            "contract_path": str(contract_path),
            "invalid_contract_fields": invalid_contract_fields,
        })
        return 3

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
    if live.get("timezone") is not None and live.get("timezone") != contract.get("timezone"):
        mismatches.append({"field": "timezone", "expected": contract.get("timezone"), "actual": live.get("timezone")})

    prompt_file = skill_root / contract["prompt_file"]
    if live.get("prompt") is not None and prompt_file.exists():
        expected_prompt = prompt_file.read_text(encoding="utf-8").strip()
        live_prompt = live["prompt"].strip()
        prompt_pointer_ok = (
            contract["prompt_file"] in live_prompt
            and "full execution contract" in live_prompt
            and prompt_file.exists()
        )
        if live_prompt != expected_prompt and not prompt_pointer_ok:
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
