from __future__ import annotations

import json
from pathlib import Path

from scripts.monitor_operator_soak import build_progress_payload
from scripts.validate_operator_soak_evidence import SoakRequirement, build_validation_payload

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
