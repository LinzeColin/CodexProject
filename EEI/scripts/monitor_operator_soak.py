#!/usr/bin/env python3
"""Summarize A209 operator soak progress without promoting release readiness."""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.validate_operator_soak_evidence import (  # noqa: E402
    ROOT,
    display_path,
    number,
    read_checkpoints,
    read_json,
    read_parameters,
    successful_checkpoint_windows,
)

DEFAULT_OUTPUT = Path("/tmp/eei-a209-operator-soak-progress.json")
DEFAULT_24H_OUTPUT = ROOT / "artifacts/tests/a209/t1307_operator_soak_24h.json"
DEFAULT_24H_CHECKPOINT = ROOT / "artifacts/tests/a209/t1307_operator_soak_24h.checkpoints.jsonl"
DEFAULT_24H_PID = ROOT / "artifacts/tests/a209/t1307_operator_soak_24h.pid"
DEFAULT_24H_LOG = ROOT / "artifacts/tests/a209/t1307_operator_soak_24h.log"


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_text_if_present(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return None


def tail_lines(path: Path, limit: int = 20) -> list[str]:
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except FileNotFoundError:
        return []
    return lines[-limit:]


def process_status(pid_path: Path) -> dict[str, Any]:
    raw = read_text_if_present(pid_path)
    result: dict[str, Any] = {
        "pid_path": display_path(pid_path),
        "pid": None,
        "status": "MISSING_PID",
    }
    if not raw:
        return result
    try:
        pid = int(raw)
    except ValueError:
        result["status"] = "INVALID_PID"
        result["raw_pid"] = raw
        return result

    result["pid"] = pid
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        result["status"] = "NOT_RUNNING"
    except PermissionError:
        result["status"] = "UNKNOWN_PERMISSION_DENIED"
    else:
        result["status"] = "RUNNING"
    return result


def checkpoint_window(entry: dict[str, Any]) -> dict[str, Any]:
    window = entry.get("window")
    return window if isinstance(window, dict) else {}


def completed_duration_seconds(windows: list[dict[str, Any]]) -> float:
    return sum(number(window.get("measured_duration_seconds")) or 0 for window in windows)


def build_progress_payload(
    *,
    output_path: Path = DEFAULT_24H_OUTPUT,
    checkpoint_path: Path = DEFAULT_24H_CHECKPOINT,
    pid_path: Path = DEFAULT_24H_PID,
    log_path: Path = DEFAULT_24H_LOG,
    parameters: dict[str, float] | None = None,
) -> dict[str, Any]:
    parameters = parameters or read_parameters()
    target_seconds = parameters["soak.long_duration_hours"] * 3600
    window_seconds = parameters["soak.operator_window_seconds"]
    target_windows = int(math.ceil(target_seconds / window_seconds))
    checkpoints = read_checkpoints(checkpoint_path) or []
    successful_entries = successful_checkpoint_windows(checkpoints)
    successful_windows = [checkpoint_window(entry) for entry in successful_entries]
    failed_windows = [
        checkpoint_window(entry)
        for entry in checkpoints
        if checkpoint_window(entry).get("status") == "FAIL"
    ]
    completed_seconds = completed_duration_seconds(successful_windows)
    windows_completed = len(successful_windows)
    windows_remaining = max(0, target_windows - windows_completed)
    output_payload = read_json(output_path)
    pid = process_status(pid_path)

    if failed_windows:
        status = "FAILED_WINDOW"
    elif completed_seconds >= target_seconds and output_payload is None:
        status = "COMPLETE_SUMMARY_PENDING"
    elif (
        output_payload
        and output_payload.get("status") == "PASS"
        and completed_seconds >= target_seconds
    ):
        status = "COMPLETE_READY_FOR_EVIDENCE_VALIDATION"
    elif windows_completed > 0 and pid["status"] == "RUNNING":
        status = "RUNNING_PARTIAL"
    elif windows_completed > 0:
        status = "PAUSED_RESUMABLE"
    else:
        status = "MISSING_OR_NOT_STARTED"

    last_window = successful_windows[-1] if successful_windows else None
    return {
        "schema_version": "eei-a209-operator-soak-progress-v1",
        "system_name": "EEI",
        "task_id": "T1307",
        "acceptance_ids": ["A209"],
        "generated_at": utc_now(),
        "status": status,
        "release_gate_closed_by_monitor": False,
        "a209_task_status_required": "IN_PROGRESS",
        "progress": {
            "target_seconds": target_seconds,
            "target_windows": target_windows,
            "operator_window_seconds": window_seconds,
            "windows_completed": windows_completed,
            "windows_failed": len(failed_windows),
            "windows_remaining": windows_remaining,
            "completed_duration_seconds": completed_seconds,
            "completion_percent": round((completed_seconds / target_seconds) * 100, 2),
            "latest_successful_window": last_window,
        },
        "artifacts": {
            "output_path": display_path(output_path),
            "checkpoint_path": display_path(checkpoint_path),
            "pid_path": display_path(pid_path),
            "log_path": display_path(log_path),
            "summary_json_present": output_payload is not None,
            "checkpoint_jsonl_present": checkpoint_path.exists(),
        },
        "process": pid,
        "resume_command": (
            "node scripts/run_operator_soak.mjs --mode operator_24h --duration-hours 24 "
            "--window-seconds 300 --output artifacts/tests/a209/t1307_operator_soak_24h.json "
            "--checkpoint artifacts/tests/a209/t1307_operator_soak_24h.checkpoints.jsonl "
            "--resume --fail-on-budget --quiet"
        ),
        "validate_command": "python scripts/validate_operator_soak_evidence.py validate",
        "release_gate_command": (
            "python scripts/validate_operator_soak_evidence.py validate --require-release-ready"
        ),
        "log_tail": tail_lines(log_path),
        "rollback": [
            "Do not promote A209 from this progress monitor.",
            (
                "If a window failed, inspect log_tail and rerun with --resume "
                "against the same checkpoint."
            ),
            (
                "Only commit the 24h output and checkpoint after the evidence "
                "validator reports release-ready evidence."
            ),
        ],
    }


def write_payload(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", default=str(DEFAULT_24H_OUTPUT))
    parser.add_argument("--checkpoint", default=str(DEFAULT_24H_CHECKPOINT))
    parser.add_argument("--pid-file", default=str(DEFAULT_24H_PID))
    parser.add_argument("--log-file", default=str(DEFAULT_24H_LOG))
    parser.add_argument("--write-output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--no-write", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = build_progress_payload(
        output_path=Path(args.output_json),
        checkpoint_path=Path(args.checkpoint),
        pid_path=Path(args.pid_file),
        log_path=Path(args.log_file),
    )
    if not args.no_write:
        write_payload(Path(args.write_output), payload)
    if not args.quiet:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 1 if payload["status"] == "FAILED_WINDOW" else 0


if __name__ == "__main__":
    raise SystemExit(main())
