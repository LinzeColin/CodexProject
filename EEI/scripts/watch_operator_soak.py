#!/usr/bin/env python3
"""Watch A209 24h operator soak progress and recover paused runs explicitly.

The watchdog is intentionally fail-closed:
- it never closes A209 or writes release-ready evidence;
- it observes live PIDs without replacing them;
- it resumes paused checkpoints only with --auto-resume and --execute;
- it reports stale live PIDs instead of killing them.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.monitor_operator_soak import (  # noqa: E402
    DEFAULT_24H_CHECKPOINT,
    DEFAULT_24H_LOG,
    DEFAULT_24H_OUTPUT,
    DEFAULT_24H_PID,
    write_payload,
)
from scripts.supervise_operator_soak import (  # noqa: E402
    DEFAULT_NODE_BIN,
    DEFAULT_PLAYWRIGHT_BROWSERS_PATH,
    DEFAULT_TMPDIR,
    build_supervisor_payload,
    shell_display,
)
from scripts.validate_operator_soak_evidence import ROOT, display_path  # noqa: E402

DEFAULT_WATCHDOG_OUTPUT = Path("/tmp/eei-a209-operator-soak-watchdog.json")
DEFAULT_WATCHDOG_PID = ROOT / "artifacts/tests/a209/t1307_operator_soak_watchdog.pid"
DEFAULT_WATCHDOG_LOG = ROOT / "artifacts/tests/a209/t1307_operator_soak_watchdog.log"
DEFAULT_INTERVAL_SECONDS = 300
DEFAULT_STALE_AFTER_SECONDS = 900


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_utc(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone(UTC)
    except ValueError:
        return None


def latest_window_age_seconds(progress: dict[str, Any]) -> float | None:
    latest = progress.get("latest_successful_window")
    if not isinstance(latest, dict):
        return None
    ended_at = parse_utc(str(latest.get("ended_at") or ""))
    if ended_at is None:
        return None
    return max(0.0, (datetime.now(UTC) - ended_at).total_seconds())


def watchdog_status(
    supervisor_payload: dict[str, Any],
    *,
    stale_after_seconds: int,
) -> tuple[str, bool, float | None]:
    progress = supervisor_payload.get("progress")
    if not isinstance(progress, dict):
        return "INVALID_SUPERVISOR_PAYLOAD", True, None
    age_seconds = latest_window_age_seconds(progress)
    process = supervisor_payload.get("process")
    process_status = process.get("status") if isinstance(process, dict) else None
    if (
        supervisor_payload.get("status") == "observe_existing_run"
        and process_status == "RUNNING"
        and age_seconds is not None
        and age_seconds > stale_after_seconds
    ):
        return "RUNNING_STALE_OPERATOR_INTERVENTION_REQUIRED", True, age_seconds

    launch_status = supervisor_payload.get("supervisor", {}).get("launch_status")
    status = str(supervisor_payload.get("status"))
    if status == "observe_existing_run":
        return "OBSERVING_RUNNING_SOAK", False, age_seconds
    if status == "resume_paused_run" and launch_status == "LAUNCHED":
        return "RESUMED_PAUSED_SOAK", False, age_seconds
    if status == "resume_paused_run":
        return "RESUME_AVAILABLE_DRY_RUN", False, age_seconds
    if status == "operator_intervention_required":
        return "OPERATOR_INTERVENTION_REQUIRED", True, age_seconds
    if status == "validate_release_evidence":
        return "COMPLETE_READY_FOR_EVIDENCE_VALIDATION", False, age_seconds
    if status == "wait_for_summary_or_validate":
        return "COMPLETE_SUMMARY_PENDING", False, age_seconds
    return "WATCHDOG_OBSERVED_NO_LAUNCH", False, age_seconds


def build_watchdog_cycle_payload(
    *,
    cycle_index: int,
    output_path: Path = DEFAULT_24H_OUTPUT,
    checkpoint_path: Path = DEFAULT_24H_CHECKPOINT,
    pid_path: Path = DEFAULT_24H_PID,
    soak_log_path: Path = DEFAULT_24H_LOG,
    auto_resume: bool = False,
    start_if_missing: bool = False,
    dry_run: bool = True,
    node_bin: str = DEFAULT_NODE_BIN,
    playwright_browsers_path: str = DEFAULT_PLAYWRIGHT_BROWSERS_PATH,
    tmpdir: str = DEFAULT_TMPDIR,
    stale_after_seconds: int = DEFAULT_STALE_AFTER_SECONDS,
) -> dict[str, Any]:
    supervisor_payload = build_supervisor_payload(
        output_path=output_path,
        checkpoint_path=checkpoint_path,
        pid_path=pid_path,
        log_path=soak_log_path,
        auto_resume=auto_resume,
        start_if_missing=start_if_missing,
        dry_run=dry_run,
        node_bin=node_bin,
        playwright_browsers_path=playwright_browsers_path,
        tmpdir=tmpdir,
    )
    status, intervention_required, age_seconds = watchdog_status(
        supervisor_payload,
        stale_after_seconds=stale_after_seconds,
    )
    return {
        "cycle_index": cycle_index,
        "generated_at": utc_now(),
        "status": status,
        "operator_intervention_required": intervention_required,
        "latest_window_age_seconds": (
            round(age_seconds, 3) if age_seconds is not None else None
        ),
        "stale_after_seconds": stale_after_seconds,
        "release_gate_closed_by_watchdog": False,
        "a209_task_status_required": "IN_PROGRESS",
        "supervisor": supervisor_payload,
    }


def summarize_cycles(
    cycles: list[dict[str, Any]],
    *,
    auto_resume: bool,
    start_if_missing: bool,
    dry_run: bool,
    interval_seconds: int,
) -> dict[str, Any]:
    latest = cycles[-1] if cycles else None
    return {
        "schema_version": "eei-a209-operator-soak-watchdog-v1",
        "system_name": "EEI",
        "task_id": "T1307",
        "acceptance_ids": ["A209"],
        "generated_at": utc_now(),
        "status": latest["status"] if latest else "NO_CYCLES",
        "release_gate_closed_by_watchdog": False,
        "a209_task_status_required": "IN_PROGRESS",
        "watchdog": {
            "auto_resume": auto_resume,
            "start_if_missing": start_if_missing,
            "dry_run": dry_run,
            "interval_seconds": interval_seconds,
            "cycles_completed": len(cycles),
            "double_start_prevention": "delegated to supervise_operator_soak.py",
            "stale_pid_policy": (
                "report operator intervention; do not kill or replace live PIDs"
            ),
        },
        "latest_cycle": latest,
        "cycles": cycles,
        "non_claims": [
            "This watchdog does not close A209.",
            "This watchdog does not replace validate_operator_soak_evidence.py.",
            "Partial checkpoints are runtime evidence only until the 24h summary validates.",
        ],
        "rollback": [
            "Stop only the watchdog PID if the watchdog was detached incorrectly.",
            "Keep valid operator soak checkpoints; do not delete partial evidence.",
            "Run supervise_operator_soak.py without --execute to inspect recovery state.",
        ],
    }


def run_watchdog(
    *,
    cycles: int,
    interval_seconds: int,
    write_output: Path,
    output_path: Path,
    checkpoint_path: Path,
    pid_path: Path,
    soak_log_path: Path,
    auto_resume: bool,
    start_if_missing: bool,
    dry_run: bool,
    node_bin: str,
    playwright_browsers_path: str,
    tmpdir: str,
    stale_after_seconds: int,
) -> dict[str, Any]:
    if cycles < 1:
        raise ValueError("cycles must be >= 1")
    cycle_payloads: list[dict[str, Any]] = []
    for cycle_index in range(1, cycles + 1):
        cycle = build_watchdog_cycle_payload(
            cycle_index=cycle_index,
            output_path=output_path,
            checkpoint_path=checkpoint_path,
            pid_path=pid_path,
            soak_log_path=soak_log_path,
            auto_resume=auto_resume,
            start_if_missing=start_if_missing,
            dry_run=dry_run,
            node_bin=node_bin,
            playwright_browsers_path=playwright_browsers_path,
            tmpdir=tmpdir,
            stale_after_seconds=stale_after_seconds,
        )
        cycle_payloads.append(cycle)
        payload = summarize_cycles(
            cycle_payloads,
            auto_resume=auto_resume,
            start_if_missing=start_if_missing,
            dry_run=dry_run,
            interval_seconds=interval_seconds,
        )
        write_payload(write_output, payload)
        if cycle_index < cycles:
            time.sleep(interval_seconds)
    return payload


def detach_command(args: argparse.Namespace) -> list[str]:
    command = [
        sys.executable,
        "scripts/watch_operator_soak.py",
        "--cycles",
        str(args.cycles),
        "--interval-seconds",
        str(args.interval_seconds),
        "--stale-after-seconds",
        str(args.stale_after_seconds),
        "--write-output",
        str(args.write_output),
        "--output-json",
        str(args.output_json),
        "--checkpoint",
        str(args.checkpoint),
        "--pid-file",
        str(args.pid_file),
        "--soak-log-file",
        str(args.soak_log_file),
        "--node-bin",
        str(args.node_bin),
        "--playwright-browsers-path",
        str(args.playwright_browsers_path),
        "--tmpdir",
        str(args.tmpdir),
    ]
    if args.auto_resume:
        command.append("--auto-resume")
    if args.start_if_missing:
        command.append("--start-if-missing")
    if args.execute:
        command.append("--execute")
    if args.quiet:
        command.append("--quiet")
    return command


def launch_detached_watchdog(args: argparse.Namespace) -> dict[str, Any]:
    args.watchdog_pid_file.parent.mkdir(parents=True, exist_ok=True)
    args.watchdog_log_file.parent.mkdir(parents=True, exist_ok=True)
    command = detach_command(args)
    env = os.environ.copy()
    env["PLAYWRIGHT_BROWSERS_PATH"] = str(args.playwright_browsers_path)
    env["TMPDIR"] = str(args.tmpdir)
    log_handle = args.watchdog_log_file.open("ab")
    try:
        process = subprocess.Popen(
            command,
            cwd=ROOT,
            env=env,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    finally:
        log_handle.close()
    args.watchdog_pid_file.write_text(f"{process.pid}\n", encoding="utf-8")
    return {
        "schema_version": "eei-a209-operator-soak-watchdog-launch-v1",
        "system_name": "EEI",
        "task_id": "T1307",
        "acceptance_ids": ["A209"],
        "generated_at": utc_now(),
        "status": "WATCHDOG_DETACHED",
        "release_gate_closed_by_watchdog": False,
        "a209_task_status_required": "IN_PROGRESS",
        "watchdog_pid": process.pid,
        "watchdog_pid_file": display_path(args.watchdog_pid_file),
        "watchdog_log_file": display_path(args.watchdog_log_file),
        "command": shell_display(command),
        "rollback": [
            "Stop only watchdog_pid to disable watchdog monitoring.",
            "Do not stop the operator soak PID unless explicit operator action is required.",
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cycles", type=int, default=1)
    parser.add_argument("--interval-seconds", type=int, default=DEFAULT_INTERVAL_SECONDS)
    parser.add_argument("--stale-after-seconds", type=int, default=DEFAULT_STALE_AFTER_SECONDS)
    parser.add_argument("--write-output", type=Path, default=DEFAULT_WATCHDOG_OUTPUT)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_24H_OUTPUT)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_24H_CHECKPOINT)
    parser.add_argument("--pid-file", type=Path, default=DEFAULT_24H_PID)
    parser.add_argument("--soak-log-file", type=Path, default=DEFAULT_24H_LOG)
    parser.add_argument("--watchdog-pid-file", type=Path, default=DEFAULT_WATCHDOG_PID)
    parser.add_argument("--watchdog-log-file", type=Path, default=DEFAULT_WATCHDOG_LOG)
    parser.add_argument("--node-bin", default=DEFAULT_NODE_BIN)
    parser.add_argument("--playwright-browsers-path", default=DEFAULT_PLAYWRIGHT_BROWSERS_PATH)
    parser.add_argument("--tmpdir", default=DEFAULT_TMPDIR)
    parser.add_argument("--auto-resume", action="store_true")
    parser.add_argument("--start-if-missing", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--detach", action="store_true")
    parser.add_argument(
        "--allow-operator-intervention-status",
        action="store_true",
        help=(
            "Return exit code 0 when the watchdog records an operator-intervention "
            "state. The payload still remains fail-closed and does not close A209."
        ),
    )
    parser.add_argument("--quiet", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.detach:
        payload = launch_detached_watchdog(args)
        write_payload(args.write_output, payload)
    else:
        payload = run_watchdog(
            cycles=args.cycles,
            interval_seconds=args.interval_seconds,
            write_output=args.write_output,
            output_path=args.output_json,
            checkpoint_path=args.checkpoint,
            pid_path=args.pid_file,
            soak_log_path=args.soak_log_file,
            auto_resume=args.auto_resume,
            start_if_missing=args.start_if_missing,
            dry_run=not args.execute,
            node_bin=args.node_bin,
            playwright_browsers_path=args.playwright_browsers_path,
            tmpdir=args.tmpdir,
            stale_after_seconds=args.stale_after_seconds,
        )
    if not args.quiet:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    intervention_status = payload.get("status") in {
        "OPERATOR_INTERVENTION_REQUIRED",
        "RUNNING_STALE_OPERATOR_INTERVENTION_REQUIRED",
    }
    return 2 if intervention_status and not args.allow_operator_intervention_status else 0


if __name__ == "__main__":
    raise SystemExit(main())
