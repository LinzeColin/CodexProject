#!/usr/bin/env python3
"""Validate the current ADP task-pack contract from the repository root.

This is the stable root entrypoint required by the S2PMT07 final-command
contract.  It validates the active V7.2 ADP contract and project governance
without mutating production state.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


def _run_command(root: Path, command: list[str], *, env: dict[str, str] | None = None) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=root,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return {
        "command": " ".join(command),
        "exit_code": completed.returncode,
        "status": "pass" if completed.returncode == 0 else "blocked",
        "stdout_tail": completed.stdout.strip().splitlines()[-20:],
        "stderr_tail": completed.stderr.strip().splitlines()[-20:],
    }


def build_validation_report(root: Path) -> dict[str, Any]:
    project_root = root / "arxiv-daily-push"
    v7_2_root = project_root / "docs" / "pursuing_goal" / "v7_2"
    required_paths = {
        "adp_project_root": project_root,
        "current_contract_pointer": project_root / "docs" / "pursuing_goal" / "CURRENT.yaml",
        "v7_2_root_lock": v7_2_root / "V7_2_ROOT_LOCK.yaml",
        "v7_2_validator": v7_2_root / "tools" / "validate_v7_2_contract.py",
        "project_governance_validator": root / "scripts" / "validate_project_governance.py",
    }
    missing_paths = [label for label, path in required_paths.items() if not path.exists()]
    if missing_paths:
        return {
            "status": "FAIL",
            "scope": "adp_task_pack_root_validation_no_production_side_effects",
            "root": str(root),
            "missing_paths": missing_paths,
            "command_results": [],
            "production_acceptance_claimed": False,
            "integrated_production_accepted": False,
            "daily_operation_enabled": False,
            "real_smtp_send_enabled": False,
            "scheduler_install_enabled": False,
            "release_packaging_enabled": False,
            "production_restore_enabled": False,
        }

    pythonpath = str(project_root / "src")
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": pythonpath}
    command_results = [
        _run_command(
            root,
            [
                sys.executable,
                "arxiv-daily-push/docs/pursuing_goal/v7_2/tools/validate_v7_2_contract.py",
                "--root",
                "arxiv-daily-push/docs/pursuing_goal/v7_2",
            ],
            env=env,
        ),
        _run_command(
            root,
            [sys.executable, "scripts/validate_project_governance.py", "--project", "arxiv-daily-push"],
            env=env,
        ),
    ]
    status = "PASS" if all(result["exit_code"] == 0 for result in command_results) else "FAIL"
    return {
        "status": status,
        "scope": "adp_task_pack_root_validation_no_production_side_effects",
        "root": str(root),
        "contract_id": "ADP-PRODUCT-CONTRACT-V7.2",
        "task_id": "S2PMT07",
        "validated_paths": {label: str(path.relative_to(root)) for label, path in required_paths.items()},
        "missing_paths": [],
        "command_results": command_results,
        "production_acceptance_claimed": False,
        "integrated_production_accepted": False,
        "daily_operation_enabled": False,
        "real_smtp_send_enabled": False,
        "scheduler_install_enabled": False,
        "release_packaging_enabled": False,
        "production_restore_enabled": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="CodexProject repository root.")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    report = build_validation_report(root)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
