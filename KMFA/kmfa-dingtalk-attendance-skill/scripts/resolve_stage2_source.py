#!/usr/bin/env python3
"""Resolve a stage-2 source snapshot with live-safe fail-closed behavior."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def dws_safety_status(repo_root: Path) -> dict[str, Any]:
    sys.path.insert(0, str(repo_root.parent))
    from KMFA.tools.dingtalk_attendance.dws_auth_guard import dws_command_safety_status

    return dws_command_safety_status(env=os.environ)


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve KMFA stage-2 source snapshot.")
    parser.add_argument("--target-month", required=True)
    parser.add_argument("--run-index", required=True, type=int)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--source-mode", default=os.environ.get("KMFA_STAGE2_SOURCE_MODE", "auto"))
    parser.add_argument("--source-json", default=os.environ.get("KMFA_STAGE2_SOURCE_JSON", ""))
    parser.add_argument("--print-json", action="store_true")
    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    repo_root = Path(args.repo_root)
    source_json = str(args.source_json or "").strip()
    source_mode = str(args.source_mode or "auto").strip() or "auto"
    status_path = run_dir / "source_adapter_status.json"

    if source_json:
        source = Path(source_json)
        status = {
            "status": "READY",
            "source_mode": "replay_json",
            "source_json": str(source),
            "target_month": args.target_month,
            "stage2_run_index": args.run_index,
            "live_dws_performed": False,
            "database_mutation_performed": False,
        }
        if not source.is_file():
            status.update({
                "status": "STAGE2_ADAPTER_SOURCE_MISSING",
                "failure_reason": f"KMFA_STAGE2_SOURCE_JSON does not exist: {source}",
            })
            write_json(status_path, status)
            print(json.dumps(status, ensure_ascii=False, indent=2, sort_keys=True))
            return 2
        write_json(status_path, status)
        print(json.dumps(status, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    if source_mode == "dws_live":
        safety = dws_safety_status(repo_root)
        status = {
            "status": "STAGE2_ADAPTER_SOURCE_MISSING",
            "source_mode": "dws_live",
            "target_month": args.target_month,
            "stage2_run_index": args.run_index,
            "live_dws_performed": False,
            "database_mutation_performed": False,
            "dws_commands_allowed": bool(safety.get("dws_commands_allowed")),
            "dws_safety_status": safety.get("status"),
            "required_env": safety.get("required_env"),
            "failure_reason": (
                "DWS live stage-2 source adapter is fail-closed until explicit authorization "
                "and source snapshot materialization are implemented."
            ),
        }
        if not status["dws_commands_allowed"]:
            status["failure_reason"] = str(safety.get("failure_reason") or status["failure_reason"])
        write_json(status_path, status)
        print(json.dumps(status, ensure_ascii=False, indent=2, sort_keys=True))
        return 2

    status = {
        "status": "STAGE2_ADAPTER_SOURCE_MISSING",
        "source_mode": source_mode,
        "target_month": args.target_month,
        "stage2_run_index": args.run_index,
        "live_dws_performed": False,
        "database_mutation_performed": False,
        "failure_reason": "Set KMFA_STAGE2_SOURCE_JSON for replay or KMFA_STAGE2_SOURCE_MODE=dws_live after authorization.",
    }
    write_json(status_path, status)
    print(json.dumps(status, ensure_ascii=False, indent=2, sort_keys=True))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
