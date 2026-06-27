#!/usr/bin/env python3
"""Record and validate the A209 background 24h operator-soak heartbeat.

This artifact is runtime progress evidence only. It keeps A209 open until the
full 24h output JSON and checkpoint JSONL pass validate_operator_soak_evidence.
"""
from __future__ import annotations

import argparse
import json
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
    process_status,
    write_payload,
)
from scripts.supervise_operator_soak import build_supervisor_payload  # noqa: E402
from scripts.validate_operator_soak_evidence import ROOT, display_path  # noqa: E402
from scripts.watch_operator_soak import DEFAULT_WATCHDOG_OUTPUT, DEFAULT_WATCHDOG_PID  # noqa: E402

DEFAULT_OUTPUT = ROOT / "artifacts/tests/a209/t1307_operator_soak_background_progress.json"

HEARTBEAT_SCHEMA_VERSION = "eei-a209-operator-soak-background-heartbeat-v1"
VALID_PROGRESS_STATUSES = {
    "RUNNING_PARTIAL",
    "PAUSED_RESUMABLE",
    "COMPLETE_SUMMARY_PENDING",
    "COMPLETE_READY_FOR_EVIDENCE_VALIDATION",
    "MISSING_OR_NOT_STARTED",
    "FAILED_WINDOW",
}


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{display_path(path)} must contain a JSON object")
    return payload


def read_optional_json(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def status_from_supervisor(
    supervisor: dict[str, Any],
    watchdog: dict[str, Any],
    watchdog_payload: dict[str, Any] | None = None,
) -> str:
    progress_status = str(supervisor.get("progress_status"))
    supervisor_status = str(supervisor.get("status"))
    watchdog_status = str(watchdog.get("status"))
    watchdog_observation_status = (
        str(watchdog_payload.get("status")) if isinstance(watchdog_payload, dict) else ""
    )
    if progress_status == "FAILED_WINDOW" or supervisor_status == "operator_intervention_required":
        return "BACKGROUND_SOAK_OPERATOR_INTERVENTION_REQUIRED"
    if watchdog_observation_status in {
        "OPERATOR_INTERVENTION_REQUIRED",
        "RUNNING_STALE_OPERATOR_INTERVENTION_REQUIRED",
    }:
        return "BACKGROUND_SOAK_OPERATOR_INTERVENTION_REQUIRED"
    if progress_status == "COMPLETE_READY_FOR_EVIDENCE_VALIDATION":
        return "BACKGROUND_SOAK_COMPLETE_READY_FOR_EVIDENCE_VALIDATION"
    if progress_status == "COMPLETE_SUMMARY_PENDING":
        return "BACKGROUND_SOAK_COMPLETE_SUMMARY_PENDING"
    if supervisor_status == "observe_existing_run" and watchdog_status == "RUNNING":
        return "BACKGROUND_SOAK_RUNNING_WITH_WATCHDOG"
    if supervisor_status == "observe_existing_run":
        return "BACKGROUND_SOAK_RUNNING_WITHOUT_WATCHDOG"
    if supervisor_status == "resume_paused_run" and watchdog_status == "RUNNING":
        return "BACKGROUND_SOAK_PAUSED_WATCHDOG_CAN_RESUME"
    if supervisor_status == "resume_paused_run":
        return "BACKGROUND_SOAK_PAUSED_MANUAL_RESUME_AVAILABLE"
    return "BACKGROUND_SOAK_NOT_STARTED_OR_MANUAL_ACTION_REQUIRED"


def watchdog_payload_field(payload: dict[str, Any] | None, field: str) -> Any:
    if not isinstance(payload, dict):
        return None
    latest_cycle = payload.get("latest_cycle")
    if isinstance(latest_cycle, dict) and field in latest_cycle:
        return latest_cycle.get(field)
    return payload.get(field)


def build_heartbeat_payload(
    *,
    output_path: Path = DEFAULT_24H_OUTPUT,
    checkpoint_path: Path = DEFAULT_24H_CHECKPOINT,
    pid_path: Path = DEFAULT_24H_PID,
    log_path: Path = DEFAULT_24H_LOG,
    watchdog_pid_path: Path = DEFAULT_WATCHDOG_PID,
    watchdog_output_path: Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    supervisor = build_supervisor_payload(
        output_path=output_path,
        checkpoint_path=checkpoint_path,
        pid_path=pid_path,
        log_path=log_path,
        dry_run=True,
        auto_resume=False,
        start_if_missing=False,
    )
    watchdog = process_status(watchdog_pid_path)
    watchdog_payload = read_optional_json(watchdog_output_path)
    progress = supervisor["progress"]
    return {
        "schema_version": HEARTBEAT_SCHEMA_VERSION,
        "artifact_id": "t1307-a209-background-operator-soak-heartbeat",
        "system_name": "EEI",
        "system_en_name": "Enterprise Ecosystem Intelligence",
        "task_id": "T1307",
        "acceptance_ids": ["A209"],
        "generated_at": generated_at or utc_now(),
        "status": status_from_supervisor(supervisor, watchdog, watchdog_payload),
        "progress_status": supervisor["progress_status"],
        "release_gate_closed_by_background_heartbeat": False,
        "a209_task_status_required": "IN_PROGRESS",
        "background_resolution_contract": {
            "operator_process_status": supervisor["process"]["status"],
            "operator_pid": supervisor["process"]["pid"],
            "watchdog_process_status": watchdog["status"],
            "watchdog_pid": watchdog["pid"],
            "watchdog_pid_path": watchdog["pid_path"],
            "watchdog_observation_status": (
                watchdog_payload.get("status")
                if isinstance(watchdog_payload, dict)
                else None
            ),
            "watchdog_latest_window_age_seconds": watchdog_payload_field(
                watchdog_payload, "latest_window_age_seconds"
            ),
            "watchdog_stale_after_seconds": watchdog_payload_field(
                watchdog_payload, "stale_after_seconds"
            ),
            "auto_resume_expected": True,
            "double_start_prevention": (
                "supervisor observes live operator PID and never replaces it"
            ),
            "stale_pid_policy": "watchdog reports stale live PIDs; it does not kill them",
            "failed_window_policy": "operator intervention is required before any resume",
        },
        "progress": progress,
        "artifacts": {
            "operator_output_path": display_path(output_path),
            "operator_checkpoint_path": display_path(checkpoint_path),
            "operator_pid_path": display_path(pid_path),
            "operator_log_path": display_path(log_path),
            "watchdog_output_path": display_path(watchdog_output_path)
            if watchdog_output_path is not None
            else None,
            "background_heartbeat_path": display_path(DEFAULT_OUTPUT),
            "operator_summary_json_present": supervisor["artifacts"]["summary_json_present"],
            "operator_checkpoint_jsonl_present": supervisor["artifacts"][
                "checkpoint_jsonl_present"
            ],
            "watchdog_summary_json_present": watchdog_payload is not None,
        },
        "supervisor_snapshot": {
            "status": supervisor["status"],
            "launch_status": supervisor["supervisor"]["launch_status"],
            "release_gate_closed_by_supervisor": supervisor[
                "release_gate_closed_by_supervisor"
            ],
            "resume_command": supervisor["resume_command"],
            "validate_command": supervisor["validate_command"],
            "release_gate_command": supervisor["release_gate_command"],
        },
        "non_closure": [
            "does_not_close_A209_24h_operator_soak",
            "does_not_replace_validate_operator_soak_evidence",
            "does_not_replace_final_24h_summary_json",
            "does_not_replace_release_manager_activation",
        ],
        "rollback": [
            "Regenerate this heartbeat after the next supervisor check if stale.",
            "Do not stop or restart the operator soak from this heartbeat script.",
            "If validation reports operator intervention, inspect the checkpoint and log first.",
        ],
    }


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def validate_heartbeat_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    require(
        errors,
        payload.get("schema_version") == HEARTBEAT_SCHEMA_VERSION,
        "schema_version mismatch",
    )
    require(errors, payload.get("system_name") == "EEI", "system_name must stay EEI")
    require(errors, payload.get("task_id") == "T1307", "task_id must be T1307")
    require(errors, "A209" in payload.get("acceptance_ids", []), "A209 missing")
    require(
        errors,
        payload.get("release_gate_closed_by_background_heartbeat") is False,
        "heartbeat must not close A209",
    )
    require(
        errors,
        payload.get("a209_task_status_required") == "IN_PROGRESS",
        "heartbeat must require A209 IN_PROGRESS",
    )
    require(
        errors,
        payload.get("progress_status") in VALID_PROGRESS_STATUSES,
        "progress_status must be a known background state",
    )
    progress = payload.get("progress")
    require(errors, isinstance(progress, dict), "progress must be an object")
    if isinstance(progress, dict):
        target_windows = progress.get("target_windows")
        windows_completed = progress.get("windows_completed")
        windows_failed = progress.get("windows_failed")
        windows_remaining = progress.get("windows_remaining")
        progress_status = payload.get("progress_status")
        failed_window_intervention = progress_status == "FAILED_WINDOW"
        require(errors, target_windows == 288, "A209 heartbeat must target 288 windows")
        require(
            errors,
            (isinstance(windows_failed, int) and windows_failed > 0)
            if failed_window_intervention
            else windows_failed == 0,
            (
                "A209 intervention heartbeat must expose failed windows"
                if failed_window_intervention
                else "A209 heartbeat must have zero failed windows"
            ),
        )
        require(
            errors,
            isinstance(windows_completed, int) and 0 <= windows_completed <= 288,
            "windows_completed must be within 0..288",
        )
        require(
            errors,
            isinstance(windows_remaining, int) and windows_remaining == 288 - windows_completed,
            "windows_remaining must equal 288 - windows_completed",
        )
        latest = progress.get("latest_successful_window")
        if windows_completed and isinstance(latest, dict):
            require(
                errors,
                latest.get("index") == windows_completed,
                "latest_successful_window index must match windows_completed",
            )
    contract = payload.get("background_resolution_contract")
    require(errors, isinstance(contract, dict), "background_resolution_contract missing")
    if isinstance(contract, dict):
        require(
            errors,
            contract.get("double_start_prevention"),
            "double_start_prevention must be documented",
        )
        require(
            errors,
            contract.get("failed_window_policy"),
            "failed_window_policy must be documented",
        )
        if payload.get("status") == "BACKGROUND_SOAK_OPERATOR_INTERVENTION_REQUIRED":
            watchdog_stale_intervention = (
                contract.get("watchdog_observation_status")
                == "RUNNING_STALE_OPERATOR_INTERVENTION_REQUIRED"
            )
            require(
                errors,
                watchdog_stale_intervention or contract.get("operator_process_status") != "RUNNING",
                "intervention heartbeat must not claim the failed operator is still running",
            )
            if watchdog_stale_intervention:
                latest_age = contract.get("watchdog_latest_window_age_seconds")
                stale_after = contract.get("watchdog_stale_after_seconds")
                require(
                    errors,
                    isinstance(latest_age, int | float)
                    and isinstance(stale_after, int | float)
                    and latest_age > stale_after,
                    "stale intervention heartbeat must expose a stale watchdog age",
                )
    non_closure = payload.get("non_closure")
    require(errors, isinstance(non_closure, list), "non_closure must be a list")
    if isinstance(non_closure, list):
        require(
            errors,
            "does_not_close_A209_24h_operator_soak" in non_closure,
            "non_closure must explicitly keep A209 open",
        )
    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("generate", "validate"))
    parser.add_argument("--output-json", type=Path, default=DEFAULT_24H_OUTPUT)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_24H_CHECKPOINT)
    parser.add_argument("--pid-file", type=Path, default=DEFAULT_24H_PID)
    parser.add_argument("--log-file", type=Path, default=DEFAULT_24H_LOG)
    parser.add_argument("--watchdog-pid-file", type=Path, default=DEFAULT_WATCHDOG_PID)
    parser.add_argument("--watchdog-output", type=Path, default=DEFAULT_WATCHDOG_OUTPUT)
    parser.add_argument("--write-output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--input", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--quiet", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "generate":
        payload = build_heartbeat_payload(
            output_path=args.output_json,
            checkpoint_path=args.checkpoint,
            pid_path=args.pid_file,
            log_path=args.log_file,
            watchdog_pid_path=args.watchdog_pid_file,
            watchdog_output_path=args.watchdog_output,
        )
        write_payload(args.write_output, payload)
    else:
        payload = read_json(args.input)

    errors = validate_heartbeat_payload(payload)
    result = {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "input": display_path(args.input if args.command == "validate" else args.write_output),
        "release_gate_closed_by_background_heartbeat": False,
    }
    if not args.quiet:
        print(
            json.dumps(
                payload if args.command == "generate" else result,
                ensure_ascii=False,
                indent=2,
            )
        )
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
