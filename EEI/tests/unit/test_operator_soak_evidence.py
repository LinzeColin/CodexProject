from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from scripts.monitor_operator_soak import build_progress_payload
from scripts.record_operator_soak_heartbeat import (
    build_heartbeat_payload,
    validate_heartbeat_payload,
)
from scripts.supervise_operator_soak import build_supervisor_payload
from scripts.validate_operator_soak_evidence import SoakRequirement, build_validation_payload
from scripts.watch_operator_soak import build_watchdog_cycle_payload, summarize_cycles
from scripts.watch_operator_soak import main as watchdog_main

PARAMETERS = {
    "soak.short_duration_hours": 4.0,
    "soak.long_duration_hours": 24.0,
    "soak.operator_window_seconds": 300.0,
}


def requirement(tmp_path: Path, label: str, hours_key: str, coverage_key: str) -> SoakRequirement:
    return SoakRequirement(
        label=label,
        mode=label,
        output_path=tmp_path / f"{label}.json",
        checkpoint_path=tmp_path / f"{label}.checkpoints.jsonl",
        parameter_key=hours_key,
        coverage_key=coverage_key,
    )


def write_run(
    requirement: SoakRequirement,
    *,
    target_seconds: int,
    completed_seconds: int,
    elapsed_wall_seconds: int | None = None,
) -> None:
    windows = [
        {
            "index": 1,
            "status": "PASS",
            "child_status": "PARTIAL",
            "requested_duration_seconds": target_seconds,
            "measured_duration_seconds": completed_seconds,
            "elapsed_wall_seconds": elapsed_wall_seconds or completed_seconds,
            "browser_heap_growth_bytes": 1000,
            "browser_dom_node_growth": 0,
            "worker_jobs_completed": 12,
            "worker_jobs_total": 12,
            "worker_event_loop_lag_p95_ms": 2.0,
        }
    ]
    payload = {
        "schema_version": "eei-operator-soak-runner-v1",
        "system_name": "EEI",
        "task_id": "T1307",
        "acceptance_ids": ["A209"],
        "status": "PASS",
        "mode": requirement.mode,
        "runner": {
            "requested_duration_seconds": target_seconds,
            "completed_duration_seconds": completed_seconds,
            "windows_completed": 1,
            "windows_failed": 0,
            "checkpoint_path": str(requirement.checkpoint_path),
            "output_path": str(requirement.output_path),
        },
        "coverage": {
            "browser_soak_measured": True,
            "worker_soak_measured": True,
            "checkpoint_resume_supported": True,
            "covers_4h_target": completed_seconds >= 4 * 3600,
            "covers_24h_target": completed_seconds >= 24 * 3600,
            "worker_supervisor_binding_available": True,
        },
        "a209_release_gate": {"release_gate_closed_by_runner": False},
        "worker_supervisor_binding": {"status": "PASS", "process_manager": "docker_compose"},
        "windows": windows,
    }
    checkpoint = {
        "window": windows[0],
        "child_payload": {
            "budgets": {
                "max_heap_growth_bytes": 8 * 1024 * 1024,
                "max_dom_growth_nodes": 12,
                "max_event_loop_lag_ms": 250,
            }
        },
    }
    requirement.output_path.write_text(json.dumps(payload), encoding="utf-8")
    requirement.checkpoint_path.write_text(json.dumps(checkpoint) + "\n", encoding="utf-8")


def write_declared_failed_run(requirement: SoakRequirement) -> None:
    pass_windows = [
        {
            "index": index,
            "status": "PASS",
            "child_status": "PARTIAL",
            "requested_duration_seconds": 300,
            "measured_duration_seconds": 300,
            "elapsed_wall_seconds": 301,
            "browser_heap_growth_bytes": 1000,
            "browser_dom_node_growth": 0,
            "worker_jobs_completed": 12,
            "worker_jobs_total": 12,
            "worker_event_loop_lag_p95_ms": 2.0,
        }
        for index in range(1, 7)
    ]
    failed_window = {
        "index": 7,
        "status": "FAIL",
        "child_status": "NO_OUTPUT",
        "requested_duration_seconds": 300,
        "measured_duration_seconds": 0,
        "elapsed_wall_seconds": 301,
        "output_path": "/private/tmp/eei-operator-soak-test-7.json",
        "browser_heap_growth_bytes": None,
        "browser_dom_node_growth": None,
        "worker_jobs_completed": None,
        "worker_jobs_total": None,
        "worker_event_loop_lag_p95_ms": None,
    }
    windows = pass_windows + [failed_window]
    payload = {
        "schema_version": "eei-operator-soak-runner-v1",
        "system_name": "EEI",
        "task_id": "T1307",
        "acceptance_ids": ["A209"],
        "status": "FAIL",
        "mode": requirement.mode,
        "runner": {
            "requested_duration_seconds": 24 * 3600,
            "completed_duration_seconds": 6 * 300,
            "windows_completed": 6,
            "windows_failed": 1,
            "checkpoint_path": str(requirement.checkpoint_path),
            "output_path": str(requirement.output_path),
        },
        "coverage": {
            "browser_soak_measured": True,
            "worker_soak_measured": True,
            "checkpoint_resume_supported": True,
            "covers_4h_target": False,
            "covers_24h_target": False,
            "worker_supervisor_binding_available": True,
        },
        "a209_release_gate": {"release_gate_closed_by_runner": False},
        "worker_supervisor_binding": {"status": "PASS", "process_manager": "docker_compose"},
        "windows": windows,
    }
    checkpoints = [
        {
            "window": window,
            "child_harness": {
                "exit_status": 0 if window["status"] == "PASS" else 1,
                "stderr_tail": ""
                if window["status"] == "PASS"
                else "page.evaluate: Target page, context or browser has been closed",
            },
            "child_payload": {
                "budgets": {
                    "max_heap_growth_bytes": 8 * 1024 * 1024,
                    "max_dom_growth_nodes": 12,
                    "max_event_loop_lag_ms": 250,
                }
            }
            if window["status"] == "PASS"
            else None,
        }
        for window in windows
    ]
    requirement.output_path.write_text(json.dumps(payload), encoding="utf-8")
    requirement.checkpoint_path.write_text(
        "".join(json.dumps(checkpoint) + "\n" for checkpoint in checkpoints),
        encoding="utf-8",
    )


def test_missing_operator_soak_evidence_is_explicit_not_release_ready(tmp_path: Path) -> None:
    reqs = (
        requirement(tmp_path, "operator_4h", "soak.short_duration_hours", "covers_4h_target"),
        requirement(tmp_path, "operator_24h", "soak.long_duration_hours", "covers_24h_target"),
    )
    payload = build_validation_payload(parameters=PARAMETERS, required_runs=reqs)
    assert payload["status"] == "MISSING_OPERATOR_EVIDENCE"
    assert payload["release_gate_closed_by_validator"] is False
    assert {result["status"] for result in payload["results"]} == {"MISSING"}


def test_insufficient_operator_soak_duration_fails_closed(tmp_path: Path) -> None:
    req_4h = requirement(tmp_path, "operator_4h", "soak.short_duration_hours", "covers_4h_target")
    req_24h = requirement(tmp_path, "operator_24h", "soak.long_duration_hours", "covers_24h_target")
    write_run(req_4h, target_seconds=4 * 3600, completed_seconds=60)
    payload = build_validation_payload(parameters=PARAMETERS, required_runs=(req_4h, req_24h))
    assert payload["status"] == "FAIL"
    assert "completed duration is below target" in payload["results"][0]["errors"]


def test_declared_failed_operator_soak_is_governance_valid_not_release_ready(
    tmp_path: Path,
) -> None:
    req_4h = requirement(tmp_path, "operator_4h", "soak.short_duration_hours", "covers_4h_target")
    req_24h = requirement(tmp_path, "operator_24h", "soak.long_duration_hours", "covers_24h_target")
    write_run(req_4h, target_seconds=4 * 3600, completed_seconds=4 * 3600)
    write_declared_failed_run(req_24h)

    payload = build_validation_payload(parameters=PARAMETERS, required_runs=(req_4h, req_24h))

    assert payload["status"] == "FAILED_OPERATOR_EVIDENCE"
    assert payload["failed_operator_evidence_accepted_as_release_ready"] is False
    assert payload["release_gate_closed_by_validator"] is False
    assert payload["results"][1]["status"] == "FAILED_RUN"
    assert payload["results"][1]["windows_failed"] == 1
    assert payload["results"][1]["failed_windows"][0]["child_status"] == "NO_OUTPUT"


def test_serialized_wall_clock_soak_window_fails_closed(tmp_path: Path) -> None:
    req_4h = requirement(tmp_path, "operator_4h", "soak.short_duration_hours", "covers_4h_target")
    write_run(
        req_4h,
        target_seconds=4 * 3600,
        completed_seconds=4 * 3600,
        elapsed_wall_seconds=8 * 3600,
    )
    payload = build_validation_payload(parameters=PARAMETERS, required_runs=(req_4h,))
    assert payload["status"] == "FAIL"
    assert any(
        "elapsed_wall_seconds exceeds parallel window budget" in error
        for error in payload["results"][0]["errors"]
    )


def test_complete_operator_soak_evidence_is_ready_for_release_review(tmp_path: Path) -> None:
    req_4h = requirement(tmp_path, "operator_4h", "soak.short_duration_hours", "covers_4h_target")
    req_24h = requirement(tmp_path, "operator_24h", "soak.long_duration_hours", "covers_24h_target")
    write_run(req_4h, target_seconds=4 * 3600, completed_seconds=4 * 3600)
    write_run(req_24h, target_seconds=24 * 3600, completed_seconds=24 * 3600)
    payload = build_validation_payload(parameters=PARAMETERS, required_runs=(req_4h, req_24h))
    assert payload["status"] == "EVIDENCE_READY_FOR_RELEASE_MANAGER_REVIEW"
    assert {result["status"] for result in payload["results"]} == {"PASS"}
    assert payload["a209_task_status_required"] == "IN_PROGRESS"


def write_checkpoint(path: Path, *, index: int, status: str = "PASS") -> None:
    window = {
        "index": index,
        "status": status,
        "child_status": "PARTIAL",
        "requested_duration_seconds": 300,
        "measured_duration_seconds": 300,
        "elapsed_wall_seconds": 301,
        "browser_heap_growth_bytes": 1000,
        "browser_dom_node_growth": 0,
        "worker_jobs_completed": 12,
        "worker_jobs_total": 12,
        "worker_event_loop_lag_p95_ms": 2.0,
    }
    path.write_text(json.dumps({"window": window}) + "\n", encoding="utf-8")


def test_operator_soak_progress_monitor_reports_missing_gate_open(tmp_path: Path) -> None:
    payload = build_progress_payload(
        output_path=tmp_path / "missing.json",
        checkpoint_path=tmp_path / "missing.checkpoints.jsonl",
        pid_path=tmp_path / "missing.pid",
        log_path=tmp_path / "missing.log",
        parameters=PARAMETERS,
    )
    assert payload["status"] == "MISSING_OR_NOT_STARTED"
    assert payload["release_gate_closed_by_monitor"] is False
    assert payload["progress"]["completion_percent"] == 0.0
    assert payload["a209_task_status_required"] == "IN_PROGRESS"


def test_operator_soak_progress_monitor_reports_paused_resume_command(tmp_path: Path) -> None:
    checkpoint = tmp_path / "operator_24h.checkpoints.jsonl"
    write_checkpoint(checkpoint, index=1)
    payload = build_progress_payload(
        output_path=tmp_path / "operator_24h.json",
        checkpoint_path=checkpoint,
        pid_path=tmp_path / "operator_24h.pid",
        log_path=tmp_path / "operator_24h.log",
        parameters=PARAMETERS,
    )
    assert payload["status"] == "PAUSED_RESUMABLE"
    assert payload["progress"]["windows_completed"] == 1
    assert payload["progress"]["windows_remaining"] == 287
    assert "--resume" in payload["resume_command"]


def test_operator_soak_progress_monitor_fails_on_failed_window(tmp_path: Path) -> None:
    checkpoint = tmp_path / "operator_24h.checkpoints.jsonl"
    write_checkpoint(checkpoint, index=1, status="FAIL")
    payload = build_progress_payload(
        output_path=tmp_path / "operator_24h.json",
        checkpoint_path=checkpoint,
        pid_path=tmp_path / "operator_24h.pid",
        log_path=tmp_path / "operator_24h.log",
        parameters=PARAMETERS,
    )
    assert payload["status"] == "FAILED_WINDOW"
    assert payload["progress"]["windows_failed"] == 1


def test_operator_soak_progress_monitor_reports_summary_pending(tmp_path: Path) -> None:
    checkpoint = tmp_path / "operator_24h.checkpoints.jsonl"
    checkpoint.write_text(
        "\n".join(
            json.dumps(
                {
                    "window": {
                        "index": index,
                        "status": "PASS",
                        "measured_duration_seconds": 300,
                    }
                }
            )
            for index in range(1, 289)
        )
        + "\n",
        encoding="utf-8",
    )
    payload = build_progress_payload(
        output_path=tmp_path / "operator_24h.json",
        checkpoint_path=checkpoint,
        pid_path=tmp_path / "operator_24h.pid",
        log_path=tmp_path / "operator_24h.log",
        parameters=PARAMETERS,
    )
    assert payload["status"] == "COMPLETE_SUMMARY_PENDING"
    assert payload["progress"]["windows_completed"] == 288
    assert payload["progress"]["completion_percent"] == 100.0


def test_operator_soak_supervisor_observes_existing_running_process(tmp_path: Path) -> None:
    checkpoint = tmp_path / "operator_24h.checkpoints.jsonl"
    pid_file = tmp_path / "operator_24h.pid"
    write_checkpoint(checkpoint, index=1)
    pid_file.write_text(f"{os.getpid()}\n", encoding="utf-8")
    payload = build_supervisor_payload(
        output_path=tmp_path / "operator_24h.json",
        checkpoint_path=checkpoint,
        pid_path=pid_file,
        log_path=tmp_path / "operator_24h.log",
    )
    assert payload["status"] == "observe_existing_run"
    assert payload["supervisor"]["launch_status"] == "NOT_REQUESTED"
    assert payload["release_gate_closed_by_supervisor"] is False


def test_operator_soak_supervisor_requires_explicit_auto_resume(tmp_path: Path) -> None:
    checkpoint = tmp_path / "operator_24h.checkpoints.jsonl"
    write_checkpoint(checkpoint, index=1)
    payload = build_supervisor_payload(
        output_path=tmp_path / "operator_24h.json",
        checkpoint_path=checkpoint,
        pid_path=tmp_path / "operator_24h.pid",
        log_path=tmp_path / "operator_24h.log",
        auto_resume=False,
    )
    assert payload["status"] == "resume_paused_run"
    assert payload["supervisor"]["launch_status"] == "DRY_RUN_REQUIRES_AUTO_RESUME"
    assert "--resume" in payload["resume_command"]


def test_operator_soak_supervisor_auto_resume_dry_run_keeps_release_gate_open(
    tmp_path: Path,
) -> None:
    checkpoint = tmp_path / "operator_24h.checkpoints.jsonl"
    write_checkpoint(checkpoint, index=1)
    payload = build_supervisor_payload(
        output_path=tmp_path / "operator_24h.json",
        checkpoint_path=checkpoint,
        pid_path=tmp_path / "operator_24h.pid",
        log_path=tmp_path / "operator_24h.log",
        auto_resume=True,
        dry_run=True,
    )
    assert payload["status"] == "resume_paused_run"
    assert payload["supervisor"]["launch_status"] == "DRY_RUN"
    assert payload["supervisor"]["launched_pid"] is None
    assert payload["a209_task_status_required"] == "IN_PROGRESS"


def test_operator_soak_supervisor_failed_window_blocks_resume(tmp_path: Path) -> None:
    checkpoint = tmp_path / "operator_24h.checkpoints.jsonl"
    write_checkpoint(checkpoint, index=1, status="FAIL")
    payload = build_supervisor_payload(
        output_path=tmp_path / "operator_24h.json",
        checkpoint_path=checkpoint,
        pid_path=tmp_path / "operator_24h.pid",
        log_path=tmp_path / "operator_24h.log",
        auto_resume=True,
    )
    assert payload["status"] == "operator_intervention_required"
    assert payload["supervisor"]["launch_status"] == "NOT_REQUESTED"


def test_operator_soak_watchdog_observes_running_process_without_launch(tmp_path: Path) -> None:
    checkpoint = tmp_path / "operator_24h.checkpoints.jsonl"
    pid_file = tmp_path / "operator_24h.pid"
    write_checkpoint(checkpoint, index=1)
    pid_file.write_text(f"{os.getpid()}\n", encoding="utf-8")

    payload = build_watchdog_cycle_payload(
        cycle_index=1,
        output_path=tmp_path / "operator_24h.json",
        checkpoint_path=checkpoint,
        pid_path=pid_file,
        soak_log_path=tmp_path / "operator_24h.log",
    )

    assert payload["status"] == "OBSERVING_RUNNING_SOAK"
    assert payload["release_gate_closed_by_watchdog"] is False
    assert payload["supervisor"]["supervisor"]["launch_status"] == "NOT_REQUESTED"


def test_operator_soak_watchdog_dry_run_reports_resume_available(tmp_path: Path) -> None:
    checkpoint = tmp_path / "operator_24h.checkpoints.jsonl"
    write_checkpoint(checkpoint, index=1)

    payload = build_watchdog_cycle_payload(
        cycle_index=1,
        output_path=tmp_path / "operator_24h.json",
        checkpoint_path=checkpoint,
        pid_path=tmp_path / "operator_24h.pid",
        soak_log_path=tmp_path / "operator_24h.log",
        auto_resume=True,
        dry_run=True,
    )

    assert payload["status"] == "RESUME_AVAILABLE_DRY_RUN"
    assert payload["operator_intervention_required"] is False
    assert payload["supervisor"]["supervisor"]["launch_status"] == "DRY_RUN"
    assert payload["a209_task_status_required"] == "IN_PROGRESS"


def test_operator_soak_watchdog_blocks_failed_window_resume(tmp_path: Path) -> None:
    checkpoint = tmp_path / "operator_24h.checkpoints.jsonl"
    write_checkpoint(checkpoint, index=1, status="FAIL")

    payload = build_watchdog_cycle_payload(
        cycle_index=1,
        output_path=tmp_path / "operator_24h.json",
        checkpoint_path=checkpoint,
        pid_path=tmp_path / "operator_24h.pid",
        soak_log_path=tmp_path / "operator_24h.log",
        auto_resume=True,
        dry_run=True,
    )

    assert payload["status"] == "OPERATOR_INTERVENTION_REQUIRED"
    assert payload["operator_intervention_required"] is True
    assert payload["supervisor"]["supervisor"]["launch_status"] == "NOT_REQUESTED"


def test_operator_soak_watchdog_cli_can_allow_intervention_status(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checkpoint = tmp_path / "operator_24h.checkpoints.jsonl"
    output = tmp_path / "watchdog.json"
    write_checkpoint(checkpoint, index=1, status="FAIL")
    monkeypatch.setattr(
        "sys.argv",
        [
            "watch_operator_soak.py",
            "--cycles",
            "1",
            "--checkpoint",
            str(checkpoint),
            "--output-json",
            str(tmp_path / "operator_24h.json"),
            "--pid-file",
            str(tmp_path / "operator_24h.pid"),
            "--soak-log-file",
            str(tmp_path / "operator_24h.log"),
            "--write-output",
            str(output),
            "--allow-operator-intervention-status",
            "--quiet",
        ],
    )

    assert watchdog_main() == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["status"] == "OPERATOR_INTERVENTION_REQUIRED"
    assert payload["release_gate_closed_by_watchdog"] is False


def test_operator_soak_watchdog_summary_keeps_a209_open(tmp_path: Path) -> None:
    checkpoint = tmp_path / "operator_24h.checkpoints.jsonl"
    write_checkpoint(checkpoint, index=1)
    cycle = build_watchdog_cycle_payload(
        cycle_index=1,
        output_path=tmp_path / "operator_24h.json",
        checkpoint_path=checkpoint,
        pid_path=tmp_path / "operator_24h.pid",
        soak_log_path=tmp_path / "operator_24h.log",
        auto_resume=True,
        dry_run=True,
    )

    summary = summarize_cycles(
        [cycle],
        auto_resume=True,
        start_if_missing=False,
        dry_run=True,
        interval_seconds=300,
    )

    assert summary["schema_version"] == "eei-a209-operator-soak-watchdog-v1"
    assert summary["release_gate_closed_by_watchdog"] is False
    assert summary["watchdog"]["cycles_completed"] == 1
    assert summary["status"] == "RESUME_AVAILABLE_DRY_RUN"
    assert "This watchdog does not close A209." in summary["non_claims"]


def test_operator_soak_heartbeat_records_background_watchdog_state(tmp_path: Path) -> None:
    checkpoint = tmp_path / "operator_24h.checkpoints.jsonl"
    pid_file = tmp_path / "operator_24h.pid"
    watchdog_pid = tmp_path / "operator_24h.watchdog.pid"
    write_checkpoint(checkpoint, index=1)
    pid_file.write_text(f"{os.getpid()}\n", encoding="utf-8")
    watchdog_pid.write_text(f"{os.getpid()}\n", encoding="utf-8")

    payload = build_heartbeat_payload(
        output_path=tmp_path / "operator_24h.json",
        checkpoint_path=checkpoint,
        pid_path=pid_file,
        log_path=tmp_path / "operator_24h.log",
        watchdog_pid_path=watchdog_pid,
        generated_at="2026-06-23T00:00:00Z",
    )

    assert payload["schema_version"] == "eei-a209-operator-soak-background-heartbeat-v1"
    assert payload["status"] == "BACKGROUND_SOAK_RUNNING_WITH_WATCHDOG"
    assert payload["progress"]["windows_completed"] == 1
    assert payload["progress"]["windows_remaining"] == 287
    assert payload["release_gate_closed_by_background_heartbeat"] is False
    assert payload["background_resolution_contract"]["operator_process_status"] == "RUNNING"
    assert payload["background_resolution_contract"]["watchdog_process_status"] == "RUNNING"
    assert validate_heartbeat_payload(payload) == []


def test_operator_soak_heartbeat_validation_fails_if_release_gate_is_closed(
    tmp_path: Path,
) -> None:
    checkpoint = tmp_path / "operator_24h.checkpoints.jsonl"
    write_checkpoint(checkpoint, index=1)
    payload = build_heartbeat_payload(
        output_path=tmp_path / "operator_24h.json",
        checkpoint_path=checkpoint,
        pid_path=tmp_path / "operator_24h.pid",
        log_path=tmp_path / "operator_24h.log",
        generated_at="2026-06-23T00:00:00Z",
    )
    payload["release_gate_closed_by_background_heartbeat"] = True

    errors = validate_heartbeat_payload(payload)

    assert "heartbeat must not close A209" in errors


def test_operator_soak_heartbeat_validation_accepts_intervention_state(
    tmp_path: Path,
) -> None:
    checkpoint = tmp_path / "operator_24h.checkpoints.jsonl"
    write_checkpoint(checkpoint, index=1, status="FAIL")

    payload = build_heartbeat_payload(
        output_path=tmp_path / "operator_24h.json",
        checkpoint_path=checkpoint,
        pid_path=tmp_path / "operator_24h.pid",
        log_path=tmp_path / "operator_24h.log",
        generated_at="2026-06-23T00:00:00Z",
    )

    assert payload["status"] == "BACKGROUND_SOAK_OPERATOR_INTERVENTION_REQUIRED"
    assert payload["progress_status"] == "FAILED_WINDOW"
    assert payload["progress"]["windows_failed"] == 1
    assert validate_heartbeat_payload(payload) == []
