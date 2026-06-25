#!/usr/bin/env python3
"""Validate committed A209 operator soak evidence before release review."""
from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "artifacts/tests/a209/t1307_operator_soak_evidence_validation.json"

DEFAULT_BUDGETS = {
    "max_heap_growth_bytes": 8 * 1024 * 1024,
    "max_dom_growth_nodes": 12,
    "max_event_loop_lag_ms": 250,
}


@dataclass(frozen=True)
class SoakRequirement:
    label: str
    mode: str
    output_path: Path
    checkpoint_path: Path
    parameter_key: str
    coverage_key: str


REQUIRED_RUNS = (
    SoakRequirement(
        label="operator_4h",
        mode="operator_4h",
        output_path=ROOT / "artifacts/tests/a209/t1307_operator_soak_4h.json",
        checkpoint_path=ROOT / "artifacts/tests/a209/t1307_operator_soak_4h.checkpoints.jsonl",
        parameter_key="soak.short_duration_hours",
        coverage_key="covers_4h_target",
    ),
    SoakRequirement(
        label="operator_24h",
        mode="operator_24h",
        output_path=ROOT / "artifacts/tests/a209/t1307_operator_soak_24h.json",
        checkpoint_path=ROOT / "artifacts/tests/a209/t1307_operator_soak_24h.checkpoints.jsonl",
        parameter_key="soak.long_duration_hours",
        coverage_key="covers_24h_target",
    ),
)


def parse_csv_line(line: str) -> list[str]:
    values: list[str] = []
    current = ""
    quoted = False
    index = 0
    while index < len(line):
        char = line[index]
        next_char = line[index + 1] if index + 1 < len(line) else ""
        if char == '"' and quoted and next_char == '"':
            current += '"'
            index += 1
        elif char == '"':
            quoted = not quoted
        elif char == "," and not quoted:
            values.append(current)
            current = ""
        else:
            current += char
        index += 1
    values.append(current)
    return values


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def read_parameters(path: Path = ROOT / "data/parameter_catalog.csv") -> dict[str, float]:
    rows = list(csv.DictReader(path.open(encoding="utf-8-sig", newline="")))
    values: dict[str, float] = {}
    for row in rows:
        key = row["parameter_key"]
        if key.startswith("soak."):
            values[key] = float(row["default_value"])
    for key in (
        "soak.short_duration_hours",
        "soak.long_duration_hours",
        "soak.operator_window_seconds",
    ):
        if key not in values:
            raise AssertionError(f"missing soak parameter {key}")
    return values


def read_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None


def read_checkpoints(path: Path) -> list[dict[str, Any]] | None:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return None
    entries: list[dict[str, Any]] = []
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError as exc:
            message = f"{display_path(path)} line {line_number} is not JSON: {exc}"
            raise AssertionError(message) from exc
    return entries


def number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    return None


def successful_checkpoint_windows(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        entry
        for entry in entries
        if isinstance(entry.get("window"), dict) and entry["window"].get("status") == "PASS"
    ]


def failed_checkpoint_windows(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        entry
        for entry in entries
        if isinstance(entry.get("window"), dict) and entry["window"].get("status") == "FAIL"
    ]


def failed_window_summaries(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for entry in entries:
        window = entry.get("window") if isinstance(entry.get("window"), dict) else {}
        child_harness = (
            entry.get("child_harness") if isinstance(entry.get("child_harness"), dict) else {}
        )
        summaries.append(
            {
                "index": window.get("index"),
                "status": window.get("status"),
                "child_status": window.get("child_status"),
                "started_at": window.get("started_at"),
                "ended_at": window.get("ended_at"),
                "output_path": window.get("output_path"),
                "exit_status": child_harness.get("exit_status"),
                "stderr_tail": child_harness.get("stderr_tail"),
            }
        )
    return summaries


def is_declared_failed_operator_run(
    *,
    payload: dict[str, Any],
    runner: dict[str, Any],
    windows: list[dict[str, Any]],
    failed_checkpoints: list[dict[str, Any]],
    errors: list[str],
) -> bool:
    critical_errors = {
        "schema drift",
        "system name must stay EEI",
        "task_id must be T1307",
        "A209 acceptance missing",
        "mode mismatch",
        "runner must not close A209 release gate by itself",
        "worker binding status must be PASS",
        "worker binding process manager must be docker_compose",
        "runner output path mismatch",
        "runner checkpoint path mismatch",
    }
    if any(error in critical_errors for error in errors):
        return False
    failed_windows = [window for window in windows if window.get("status") == "FAIL"]
    return (
        payload.get("status") == "FAIL"
        and isinstance(runner.get("windows_failed"), int)
        and runner.get("windows_failed") > 0
        and len(failed_windows) == runner.get("windows_failed")
        and len(failed_checkpoints) == runner.get("windows_failed")
    )


def validate_window_metrics(
    *,
    errors: list[str],
    window: dict[str, Any],
    checkpoint: dict[str, Any] | None,
    index: int,
) -> None:
    budgets = DEFAULT_BUDGETS | (
        (checkpoint or {}).get("child_payload", {}).get("budgets", {})
        if isinstance((checkpoint or {}).get("child_payload"), dict)
        else {}
    )
    require(errors, window.get("status") == "PASS", f"window {index} status must be PASS")
    require(
        errors,
        window.get("child_status") in {"PASS", "PARTIAL"},
        f"window {index} child_status must be PASS or PARTIAL",
    )
    measured_duration = number(window.get("measured_duration_seconds"))
    require(
        errors,
        measured_duration is not None and measured_duration > 0,
        f"window {index} measured_duration_seconds must be positive",
    )
    elapsed_wall = number(window.get("elapsed_wall_seconds"))
    max_expected_wall = (
        measured_duration + max(60.0, measured_duration * 0.25)
        if measured_duration is not None
        else None
    )
    require(
        errors,
        elapsed_wall is not None
        and max_expected_wall is not None
        and elapsed_wall <= max_expected_wall,
        f"window {index} elapsed_wall_seconds exceeds parallel window budget",
    )
    heap_growth = number(window.get("browser_heap_growth_bytes"))
    dom_growth = number(window.get("browser_dom_node_growth"))
    lag_p95 = number(window.get("worker_event_loop_lag_p95_ms"))
    require(
        errors,
        heap_growth is not None and heap_growth <= float(budgets["max_heap_growth_bytes"]),
        f"window {index} browser_heap_growth_bytes exceeds budget",
    )
    require(
        errors,
        dom_growth is not None and dom_growth <= float(budgets["max_dom_growth_nodes"]),
        f"window {index} browser_dom_node_growth exceeds budget",
    )
    require(
        errors,
        lag_p95 is not None and lag_p95 <= float(budgets["max_event_loop_lag_ms"]),
        f"window {index} worker_event_loop_lag_p95_ms exceeds budget",
    )
    require(
        errors,
        window.get("worker_jobs_completed") == window.get("worker_jobs_total"),
        f"window {index} worker jobs must all complete",
    )


def validate_required_run(
    requirement: SoakRequirement,
    *,
    parameters: dict[str, float],
) -> dict[str, Any]:
    payload = read_json(requirement.output_path)
    checkpoints = read_checkpoints(requirement.checkpoint_path)
    target_seconds = parameters[requirement.parameter_key] * 3600
    result: dict[str, Any] = {
        "label": requirement.label,
        "mode": requirement.mode,
        "status": "MISSING",
        "target_seconds": target_seconds,
        "output_path": display_path(requirement.output_path),
        "checkpoint_path": display_path(requirement.checkpoint_path),
        "errors": [],
    }
    missing = []
    if payload is None:
        missing.append("output_json")
    if checkpoints is None:
        missing.append("checkpoint_jsonl")
    if missing:
        result["missing"] = missing
        return result

    assert checkpoints is not None
    assert payload is not None
    errors: list[str] = []
    runner = payload.get("runner", {}) if isinstance(payload.get("runner"), dict) else {}
    coverage = payload.get("coverage", {}) if isinstance(payload.get("coverage"), dict) else {}
    release_gate = (
        payload.get("a209_release_gate", {})
        if isinstance(payload.get("a209_release_gate"), dict)
        else {}
    )
    binding = (
        payload.get("worker_supervisor_binding", {})
        if isinstance(payload.get("worker_supervisor_binding"), dict)
        else {}
    )
    windows = payload.get("windows", []) if isinstance(payload.get("windows"), list) else []
    checkpoint_windows = successful_checkpoint_windows(checkpoints)
    failed_checkpoints = failed_checkpoint_windows(checkpoints)

    require(errors, payload.get("schema_version") == "eei-operator-soak-runner-v1", "schema drift")
    require(errors, payload.get("system_name") == "EEI", "system name must stay EEI")
    require(errors, payload.get("task_id") == "T1307", "task_id must be T1307")
    require(errors, "A209" in payload.get("acceptance_ids", []), "A209 acceptance missing")
    require(errors, payload.get("mode") == requirement.mode, "mode mismatch")
    require(errors, payload.get("status") == "PASS", "run status must be PASS")
    require(
        errors,
        number(runner.get("requested_duration_seconds")) is not None
        and float(runner["requested_duration_seconds"]) >= target_seconds,
        "requested duration is below target",
    )
    require(
        errors,
        number(runner.get("completed_duration_seconds")) is not None
        and float(runner["completed_duration_seconds"]) >= target_seconds,
        "completed duration is below target",
    )
    require(errors, runner.get("windows_failed") == 0, "windows_failed must be 0")
    require(
        errors,
        number(runner.get("windows_completed")) is not None
        and int(runner["windows_completed"]) > 0,
        "windows_completed must be positive",
    )
    require(errors, coverage.get("browser_soak_measured") is True, "browser soak not measured")
    require(errors, coverage.get("worker_soak_measured") is True, "worker soak not measured")
    require(
        errors,
        coverage.get("checkpoint_resume_supported") is True,
        "checkpoint resume support missing",
    )
    require(
        errors,
        coverage.get(requirement.coverage_key) is True,
        f"{requirement.coverage_key} false",
    )
    require(
        errors,
        coverage.get("worker_supervisor_binding_available") is True,
        "worker supervisor binding unavailable",
    )
    require(
        errors,
        release_gate.get("release_gate_closed_by_runner") is False,
        "runner must not close A209 release gate by itself",
    )
    require(errors, binding.get("status") == "PASS", "worker binding status must be PASS")
    require(
        errors,
        binding.get("process_manager") == "docker_compose",
        "worker binding process manager must be docker_compose",
    )
    require(
        errors,
        runner.get("output_path") == display_path(requirement.output_path),
        "runner output path mismatch",
    )
    require(
        errors,
        runner.get("checkpoint_path") == display_path(requirement.checkpoint_path),
        "runner checkpoint path mismatch",
    )
    completed_duration_from_windows = sum(
        number(window.get("measured_duration_seconds")) or 0 for window in windows
    )
    completed_duration_from_checkpoints = sum(
        number(entry["window"].get("measured_duration_seconds")) or 0
        for entry in checkpoint_windows
    )
    require(
        errors,
        completed_duration_from_windows >= target_seconds,
        "window duration sum below target",
    )
    require(
        errors,
        completed_duration_from_checkpoints >= target_seconds,
        "checkpoint duration sum below target",
    )
    require(
        errors,
        len(checkpoint_windows) >= int(runner.get("windows_completed") or 0),
        "checkpoint windows fewer than runner windows_completed",
    )
    checkpoints_by_index = {
        entry["window"].get("index"): entry for entry in checkpoint_windows if "window" in entry
    }
    for index, window in enumerate(windows, start=1):
        checkpoint = checkpoints_by_index.get(window.get("index"))
        validate_window_metrics(errors=errors, window=window, checkpoint=checkpoint, index=index)

    declared_failed_run = is_declared_failed_operator_run(
        payload=payload,
        runner=runner,
        windows=windows,
        failed_checkpoints=failed_checkpoints,
        errors=errors,
    )
    result_status = "FAILED_RUN" if declared_failed_run else "FAIL" if errors else "PASS"
    result |= {
        "status": result_status,
        "target_seconds": target_seconds,
        "completed_duration_seconds": runner.get("completed_duration_seconds"),
        "windows_completed": runner.get("windows_completed"),
        "windows_failed": runner.get("windows_failed"),
        "checkpoint_windows": len(checkpoint_windows),
        "failed_checkpoint_windows": len(failed_checkpoints),
        "failed_windows": failed_window_summaries(failed_checkpoints),
        "errors": errors,
    }
    return result


def build_validation_payload(
    *,
    parameters: dict[str, float],
    required_runs: tuple[SoakRequirement, ...] = REQUIRED_RUNS,
) -> dict[str, Any]:
    results = [
        validate_required_run(requirement, parameters=parameters) for requirement in required_runs
    ]
    statuses = {result["status"] for result in results}
    if "FAIL" in statuses:
        status = "FAIL"
    elif "FAILED_RUN" in statuses:
        status = "FAILED_OPERATOR_EVIDENCE"
    elif statuses == {"PASS"}:
        status = "EVIDENCE_READY_FOR_RELEASE_MANAGER_REVIEW"
    elif "PASS" in statuses:
        status = "PARTIAL_OPERATOR_EVIDENCE"
    else:
        status = "MISSING_OPERATOR_EVIDENCE"
    return {
        "schema_version": "eei-a209-operator-soak-evidence-validation-v1",
        "system_name": "EEI",
        "task_id": "T1307",
        "acceptance_ids": ["A209"],
        "status": status,
        "release_gate_closed_by_validator": False,
        "a209_task_status_required": "IN_PROGRESS",
        "failed_operator_evidence_accepted_as_release_ready": False,
        "configured_targets": {
            "short_duration_hours": parameters["soak.short_duration_hours"],
            "long_duration_hours": parameters["soak.long_duration_hours"],
            "operator_window_seconds": parameters["soak.operator_window_seconds"],
        },
        "window_wall_clock_policy": {
            "measurement_strategy": "parallel_browser_worker_v1",
            "max_elapsed_wall_seconds": (
                "measured_duration_seconds + max(60, measured_duration_seconds * 0.25)"
            ),
            "reason": (
                "browser and worker soak must be measured in the same operator window, "
                "not serialized into double wall-clock evidence."
            ),
        },
        "required_artifacts": [
            {
                "label": requirement.label,
                "output_path": display_path(requirement.output_path),
                "checkpoint_path": display_path(requirement.checkpoint_path),
            }
            for requirement in required_runs
        ],
        "results": results,
        "commands": {
            "validate": "python scripts/validate_operator_soak_evidence.py validate",
            "release_gate": (
                "python scripts/validate_operator_soak_evidence.py validate "
                "--require-release-ready"
            ),
            "operator_4h": (
                "node scripts/run_operator_soak.mjs --mode operator_4h --duration-hours 4 "
                "--window-seconds 300 --output artifacts/tests/a209/t1307_operator_soak_4h.json "
                "--checkpoint artifacts/tests/a209/t1307_operator_soak_4h.checkpoints.jsonl "
                "--fail-on-budget"
            ),
            "operator_24h": (
                "node scripts/run_operator_soak.mjs --mode operator_24h --duration-hours 24 "
                "--window-seconds 300 --output artifacts/tests/a209/t1307_operator_soak_24h.json "
                "--checkpoint artifacts/tests/a209/t1307_operator_soak_24h.checkpoints.jsonl "
                "--fail-on-budget"
            ),
        },
        "rollback": [
            "Remove invalid 4h/24h operator soak artifacts instead of promoting A209.",
            "Rerun the matching operator soak command with --resume against the same checkpoint.",
            "Keep T1307/A209 IN PROGRESS until this validator reports release-ready "
            "evidence and release evidence is regenerated.",
        ],
    }


def write_payload(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["generate", "validate"], nargs="?", default="validate")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--require-release-ready", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = build_validation_payload(parameters=read_parameters())
    output_path = Path(args.output)
    if args.command == "generate":
        write_payload(output_path, payload)
    if not args.quiet:
        print("A209 operator soak evidence validation:", payload["status"])
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    if payload["status"] == "FAIL":
        return 1
    if (
        args.require_release_ready
        and payload["status"] != "EVIDENCE_READY_FOR_RELEASE_MANAGER_REVIEW"
    ):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
