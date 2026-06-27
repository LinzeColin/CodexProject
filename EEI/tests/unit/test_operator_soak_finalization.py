from __future__ import annotations

import json
from pathlib import Path

from scripts.finalize_operator_soak_evidence import (
    build_preflight,
    validate_preflight,
)


def write_json(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def heartbeat(*, windows_completed: int, windows_failed: int = 0) -> dict:
    failed = windows_failed > 0
    return {
        "schema_version": "eei-a209-operator-soak-background-heartbeat-v1",
        "artifact_id": "t1307-a209-background-operator-soak-heartbeat",
        "system_name": "EEI",
        "task_id": "T1307",
        "acceptance_ids": ["A209"],
        "status": "BACKGROUND_SOAK_OPERATOR_INTERVENTION_REQUIRED"
        if failed
        else "BACKGROUND_SOAK_RUNNING_WITH_WATCHDOG",
        "progress_status": "RUNNING_PARTIAL"
        if windows_completed < 288 and not failed
        else "FAILED_WINDOW"
        if failed
        else "COMPLETE_READY_FOR_EVIDENCE_VALIDATION",
        "release_gate_closed_by_background_heartbeat": False,
        "a209_task_status_required": "IN_PROGRESS",
        "background_resolution_contract": {
            "operator_process_status": "NOT_RUNNING" if failed else "RUNNING",
            "operator_pid": 123,
            "watchdog_process_status": "RUNNING",
            "watchdog_pid": 456,
            "double_start_prevention": "observe live PID",
            "failed_window_policy": "operator intervention is required",
        },
        "progress": {
            "target_windows": 288,
            "windows_completed": windows_completed,
            "windows_failed": windows_failed,
            "windows_remaining": 288 - windows_completed,
            "completion_percent": round(windows_completed / 288 * 100, 2),
            "latest_successful_window": {"index": windows_completed}
            if windows_completed
            else None,
        },
        "non_closure": ["does_not_close_A209_24h_operator_soak"],
    }


def evidence(status: str) -> dict:
    failed_status = status in {"FAIL", "FAILED_OPERATOR_EVIDENCE"}
    return {
        "schema_version": "eei-a209-operator-soak-evidence-validation-v1",
        "system_name": "EEI",
        "task_id": "T1307",
        "acceptance_ids": ["A209"],
        "status": status,
        "release_gate_closed_by_validator": False,
        "a209_task_status_required": "IN_PROGRESS",
        "results": [
            {
                "label": "operator_4h",
                "status": "PASS",
                "windows_completed": 48,
                "checkpoint_windows": 48,
                "completed_duration_seconds": 14400,
                "errors": [],
            },
            {
                "label": "operator_24h",
                "status": "PASS"
                if status == "EVIDENCE_READY_FOR_RELEASE_MANAGER_REVIEW"
                else "FAILED_RUN"
                if status == "FAILED_OPERATOR_EVIDENCE"
                else "MISSING",
                "windows_completed": 288
                if status == "EVIDENCE_READY_FOR_RELEASE_MANAGER_REVIEW"
                else None,
                "checkpoint_windows": 288
                if status == "EVIDENCE_READY_FOR_RELEASE_MANAGER_REVIEW"
                else None,
                "completed_duration_seconds": 86400
                if status == "EVIDENCE_READY_FOR_RELEASE_MANAGER_REVIEW"
                else None,
                "errors": [] if not failed_status else ["window 2 status must be PASS"],
                "missing": [] if status != "PARTIAL_OPERATOR_EVIDENCE" else ["output_json"],
            },
        ],
    }


def test_finalization_blocks_running_partial_soak(tmp_path: Path) -> None:
    heartbeat_path = write_json(tmp_path / "heartbeat.json", heartbeat(windows_completed=110))
    evidence_path = write_json(
        tmp_path / "evidence.json",
        evidence("PARTIAL_OPERATOR_EVIDENCE"),
    )

    payload = build_preflight(
        heartbeat_path=heartbeat_path,
        evidence_path=evidence_path,
        generated_at="2026-06-24T00:00:00Z",
    )

    assert payload["status"] == "A209_FINALIZATION_BLOCKED_RUNNING_PARTIAL"
    assert payload["downstream_release_gate_refresh_allowed"] is False
    assert payload["release_gate_closed_by_finalizer"] is False
    assert payload["source_statuses"]["heartbeat"]["windows_completed"] == 110
    validate_preflight(payload, heartbeat_path=heartbeat_path, evidence_path=evidence_path)


def test_finalization_allows_downstream_regeneration_only_after_288_windows(
    tmp_path: Path,
) -> None:
    heartbeat_path = write_json(tmp_path / "heartbeat.json", heartbeat(windows_completed=288))
    evidence_path = write_json(
        tmp_path / "evidence.json",
        evidence("EVIDENCE_READY_FOR_RELEASE_MANAGER_REVIEW"),
    )

    payload = build_preflight(
        heartbeat_path=heartbeat_path,
        evidence_path=evidence_path,
        generated_at="2026-06-24T00:00:00Z",
    )

    assert payload["status"] == "A209_FINALIZATION_READY_FOR_RELEASE_GATE_REGEN"
    assert payload["a209_evidence_ready_for_release_manager"] is True
    assert payload["downstream_release_gate_refresh_allowed"] is True
    assert payload["release_gate_closed_by_finalizer"] is False
    validate_preflight(payload, heartbeat_path=heartbeat_path, evidence_path=evidence_path)


def test_finalization_requires_intervention_on_failed_evidence(tmp_path: Path) -> None:
    heartbeat_path = write_json(tmp_path / "heartbeat.json", heartbeat(windows_completed=288))
    evidence_path = write_json(tmp_path / "evidence.json", evidence("FAIL"))

    payload = build_preflight(
        heartbeat_path=heartbeat_path,
        evidence_path=evidence_path,
        generated_at="2026-06-24T00:00:00Z",
    )

    assert payload["status"] == "A209_FINALIZATION_OPERATOR_INTERVENTION_REQUIRED"
    assert "Inspect heartbeat_validation_errors" in payload["operator_next_actions"][0]
    assert payload["downstream_release_gate_refresh_allowed"] is False
    validate_preflight(payload, heartbeat_path=heartbeat_path, evidence_path=evidence_path)


def test_finalization_requires_intervention_on_failed_operator_evidence(
    tmp_path: Path,
) -> None:
    heartbeat_path = write_json(
        tmp_path / "heartbeat.json",
        heartbeat(windows_completed=6, windows_failed=1),
    )
    evidence_path = write_json(
        tmp_path / "evidence.json",
        evidence("FAILED_OPERATOR_EVIDENCE"),
    )

    payload = build_preflight(
        heartbeat_path=heartbeat_path,
        evidence_path=evidence_path,
        generated_at="2026-06-24T00:00:00Z",
    )

    assert payload["status"] == "A209_FINALIZATION_OPERATOR_INTERVENTION_REQUIRED"
    assert payload["downstream_release_gate_refresh_allowed"] is False
    assert payload["a209_evidence_ready_for_release_manager"] is False
    validate_preflight(payload, heartbeat_path=heartbeat_path, evidence_path=evidence_path)


def test_finalization_treats_historical_failed_evidence_as_running_partial_when_new_soak_runs(
    tmp_path: Path,
) -> None:
    heartbeat_path = write_json(tmp_path / "heartbeat.json", heartbeat(windows_completed=19))
    evidence_path = write_json(
        tmp_path / "evidence.json",
        evidence("FAILED_OPERATOR_EVIDENCE"),
    )

    payload = build_preflight(
        heartbeat_path=heartbeat_path,
        evidence_path=evidence_path,
        generated_at="2026-06-24T00:00:00Z",
    )

    assert payload["status"] == "A209_FINALIZATION_BLOCKED_RUNNING_PARTIAL"
    assert payload["source_statuses"]["evidence_validation"]["status"] == (
        "FAILED_OPERATOR_EVIDENCE"
    )
    assert payload["downstream_release_gate_refresh_allowed"] is False
    assert payload["a209_evidence_ready_for_release_manager"] is False
    validate_preflight(payload, heartbeat_path=heartbeat_path, evidence_path=evidence_path)
