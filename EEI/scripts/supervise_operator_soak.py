#!/usr/bin/env python3
"""Supervise the A209 24h operator soak without closing the release gate."""
from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
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
    build_progress_payload,
    write_payload,
)
from scripts.validate_operator_soak_evidence import ROOT, display_path  # noqa: E402

DEFAULT_STATE_OUTPUT = Path("/tmp/eei-a209-operator-soak-supervisor.json")
DEFAULT_NODE_BIN = os.environ.get("NODE_BIN", "node")
DEFAULT_PLAYWRIGHT_BROWSERS_PATH = "/private/tmp/eei-ms-playwright"
DEFAULT_TMPDIR = "/private/tmp"


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def command_for_resume(
    *,
    node_bin: str,
    output_path: Path,
    checkpoint_path: Path,
    quiet: bool,
    resume: bool,
) -> list[str]:
    command = [
        node_bin,
        "scripts/run_operator_soak.mjs",
        "--mode",
        "operator_24h",
        "--duration-hours",
        "24",
        "--window-seconds",
        "300",
        "--output",
        display_path(output_path),
        "--checkpoint",
        display_path(checkpoint_path),
    ]
    if resume:
        command.append("--resume")
    command.append("--fail-on-budget")
    if quiet:
        command.append("--quiet")
    return command


def shell_display(command: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)


def append_supervisor_log(log_path: Path, message: str) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(f"[a209-supervisor] {utc_now()} {message}\n")


def launch_detached_soak(
    *,
    command: list[str],
    pid_path: Path,
    log_path: Path,
    playwright_browsers_path: str,
    tmpdir: str,
) -> int:
    pid_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["PLAYWRIGHT_BROWSERS_PATH"] = playwright_browsers_path
    env["TMPDIR"] = tmpdir
    append_supervisor_log(log_path, f"launching: {shell_display(command)}")
    log_handle = log_path.open("ab")
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
    pid_path.write_text(f"{process.pid}\n", encoding="utf-8")
    return process.pid


def determine_action(progress: dict[str, Any], *, start_if_missing: bool) -> dict[str, Any]:
    status = progress["status"]
    process_status = progress["process"]["status"]
    windows_completed = progress["progress"]["windows_completed"]
    if status == "FAILED_WINDOW":
        return {
            "action": "operator_intervention_required",
            "reason": "at least one checkpoint window failed; inspect log before resume",
            "resume_allowed": False,
            "should_launch": False,
        }
    if process_status == "RUNNING":
        return {
            "action": "observe_existing_run",
            "reason": "24h soak process is already running",
            "resume_allowed": False,
            "should_launch": False,
        }
    if status == "PAUSED_RESUMABLE":
        return {
            "action": "resume_paused_run",
            "reason": "checkpoint has successful windows and no live process",
            "resume_allowed": True,
            "should_launch": True,
        }
    if status == "MISSING_OR_NOT_STARTED" and start_if_missing:
        return {
            "action": "start_missing_run",
            "reason": "no checkpoint exists and --start-if-missing was provided",
            "resume_allowed": False,
            "should_launch": True,
        }
    if status == "COMPLETE_SUMMARY_PENDING":
        return {
            "action": "wait_for_summary_or_validate",
            "reason": "checkpoint duration reached target; summary JSON is not present",
            "resume_allowed": False,
            "should_launch": False,
        }
    if status == "COMPLETE_READY_FOR_EVIDENCE_VALIDATION":
        return {
            "action": "validate_release_evidence",
            "reason": "24h summary and checkpoints appear complete",
            "resume_allowed": False,
            "should_launch": False,
        }
    return {
        "action": "manual_start_required",
        "reason": f"status {status} is not auto-started without --start-if-missing",
        "resume_allowed": windows_completed > 0,
        "should_launch": False,
    }


def build_supervisor_payload(
    *,
    output_path: Path = DEFAULT_24H_OUTPUT,
    checkpoint_path: Path = DEFAULT_24H_CHECKPOINT,
    pid_path: Path = DEFAULT_24H_PID,
    log_path: Path = DEFAULT_24H_LOG,
    auto_resume: bool = False,
    start_if_missing: bool = False,
    dry_run: bool = True,
    node_bin: str = DEFAULT_NODE_BIN,
    playwright_browsers_path: str = DEFAULT_PLAYWRIGHT_BROWSERS_PATH,
    tmpdir: str = DEFAULT_TMPDIR,
    quiet_child: bool = True,
) -> dict[str, Any]:
    progress = build_progress_payload(
        output_path=output_path,
        checkpoint_path=checkpoint_path,
        pid_path=pid_path,
        log_path=log_path,
    )
    action = determine_action(progress, start_if_missing=start_if_missing)
    resume = bool(action["resume_allowed"])
    command = command_for_resume(
        node_bin=node_bin,
        output_path=output_path,
        checkpoint_path=checkpoint_path,
        quiet=quiet_child,
        resume=resume,
    )
    launched_pid: int | None = None
    launch_status = "NOT_REQUESTED"
    should_launch = bool(action["should_launch"])
    if should_launch and not auto_resume:
        launch_status = "DRY_RUN_REQUIRES_AUTO_RESUME"
    elif should_launch and dry_run:
        launch_status = "DRY_RUN"
    elif should_launch:
        launched_pid = launch_detached_soak(
            command=command,
            pid_path=pid_path,
            log_path=log_path,
            playwright_browsers_path=playwright_browsers_path,
            tmpdir=tmpdir,
        )
        launch_status = "LAUNCHED"

    return {
        "schema_version": "eei-a209-operator-soak-supervisor-v1",
        "system_name": "EEI",
        "task_id": "T1307",
        "acceptance_ids": ["A209"],
        "generated_at": utc_now(),
        "status": action["action"],
        "release_gate_closed_by_supervisor": False,
        "a209_task_status_required": "IN_PROGRESS",
        "progress_status": progress["status"],
        "progress": progress["progress"],
        "process": progress["process"],
        "supervisor": {
            "auto_resume": auto_resume,
            "start_if_missing": start_if_missing,
            "dry_run": dry_run,
            "launch_status": launch_status,
            "launched_pid": launched_pid,
            "reason": action["reason"],
            "double_start_prevention": "existing RUNNING pid is never replaced",
            "failed_window_policy": "operator intervention required before resume",
        },
        "artifacts": progress["artifacts"],
        "resume_command": shell_display(command),
        "validate_command": progress["validate_command"],
        "release_gate_command": progress["release_gate_command"],
        "log_tail": progress["log_tail"],
        "rollback": [
            (
                "If a wrong process is launched, stop only that launched_pid "
                "and keep valid checkpoints."
            ),
            "Do not treat the supervisor output as A209 release-ready evidence.",
            "Run validate_operator_soak_evidence.py after the 24h summary JSON exists.",
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", default=str(DEFAULT_24H_OUTPUT))
    parser.add_argument("--checkpoint", default=str(DEFAULT_24H_CHECKPOINT))
    parser.add_argument("--pid-file", default=str(DEFAULT_24H_PID))
    parser.add_argument("--log-file", default=str(DEFAULT_24H_LOG))
    parser.add_argument("--write-output", default=str(DEFAULT_STATE_OUTPUT))
    parser.add_argument("--auto-resume", action="store_true")
    parser.add_argument("--start-if-missing", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--node-bin", default=DEFAULT_NODE_BIN)
    parser.add_argument("--playwright-browsers-path", default=DEFAULT_PLAYWRIGHT_BROWSERS_PATH)
    parser.add_argument("--tmpdir", default=DEFAULT_TMPDIR)
    parser.add_argument("--no-write", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = build_supervisor_payload(
        output_path=Path(args.output_json),
        checkpoint_path=Path(args.checkpoint),
        pid_path=Path(args.pid_file),
        log_path=Path(args.log_file),
        auto_resume=args.auto_resume,
        start_if_missing=args.start_if_missing,
        dry_run=not args.execute,
        node_bin=args.node_bin,
        playwright_browsers_path=args.playwright_browsers_path,
        tmpdir=args.tmpdir,
    )
    if not args.no_write:
        write_payload(Path(args.write_output), payload)
    if not args.quiet:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 2 if payload["status"] == "operator_intervention_required" else 0


if __name__ == "__main__":
    raise SystemExit(main())
