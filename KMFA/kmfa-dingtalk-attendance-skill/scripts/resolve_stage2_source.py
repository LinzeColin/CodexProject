#!/usr/bin/env python3
"""Resolve a stage-2 source snapshot with live-safe fail-closed behavior."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
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
    parser.add_argument("--raw-replay-day-fact-dir", default=os.environ.get("KMFA_STAGE2_RAW_REPLAY_DAY_FACT_DIR", ""))
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

    raw_replay_day_fact_dir = str(args.raw_replay_day_fact_dir or "").strip()
    if not raw_replay_day_fact_dir and source_mode == "auto":
        inferred_private_runtime = run_dir.parents[2] if len(run_dir.parents) >= 3 else None
        if inferred_private_runtime is not None:
            inferred = inferred_private_runtime / "raw_replay_day_fact" / args.target_month
            if inferred.is_dir():
                raw_replay_day_fact_dir = str(inferred)
    if source_mode in {"auto", "raw_replay_day_fact"} and raw_replay_day_fact_dir:
        source_out = run_dir / "stage2_source_snapshot.json"
        cmd = [
            sys.executable,
            str(Path(__file__).resolve().parent / "prepare_stage2_source_from_raw_replay.py"),
            "--raw-replay-day-fact-dir",
            raw_replay_day_fact_dir,
            "--target-month",
            args.target_month,
            "--out-json",
            str(source_out),
            "--print-json",
        ]
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if p.returncode != 0:
            status = {
                "status": "STAGE2_ADAPTER_SOURCE_MISSING",
                "source_mode": "raw_replay_day_fact",
                "target_month": args.target_month,
                "stage2_run_index": args.run_index,
                "live_dws_performed": False,
                "database_mutation_performed": False,
                "failure_reason": (p.stderr or p.stdout or "raw replay day-fact source materialization failed").strip(),
            }
            write_json(status_path, status)
            print(json.dumps(status, ensure_ascii=False, indent=2, sort_keys=True))
            return 2
        adapter_summary = json.loads(p.stdout) if p.stdout.strip() else {}
        status = {
            "status": "READY",
            "source_mode": "raw_replay_day_fact",
            "source_json": str(source_out),
            "target_month": args.target_month,
            "stage2_run_index": args.run_index,
            "adapter_summary": adapter_summary,
            "live_dws_performed": False,
            "database_mutation_performed": False,
        }
        write_json(status_path, status)
        print(json.dumps(status, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    if source_mode == "raw_replay_day_fact":
        status = {
            "status": "STAGE2_ADAPTER_SOURCE_MISSING",
            "source_mode": "raw_replay_day_fact",
            "target_month": args.target_month,
            "stage2_run_index": args.run_index,
            "live_dws_performed": False,
            "database_mutation_performed": False,
            "failure_reason": "Set KMFA_STAGE2_RAW_REPLAY_DAY_FACT_DIR or place raw_replay_day_fact/YYYYMM under private_runtime.",
        }
        write_json(status_path, status)
        print(json.dumps(status, ensure_ascii=False, indent=2, sort_keys=True))
        return 2

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
