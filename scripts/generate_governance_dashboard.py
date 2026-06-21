#!/usr/bin/env python3
"""Generate human-readable governance status pages from machine sources."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import validate_project_governance as structural
import validate_governance_sync as sync


sys.dont_write_bytecode = True

ROOT = structural.ROOT


def git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else "UNKNOWN"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_project(project: dict[str, Any]) -> dict[str, Any]:
    project_path = ROOT / str(project.get("path") or "")
    parsed_validation = structural.Validation()
    parsed = structural.parse_project_governance(project_path, parsed_validation, True, structural.project_scope(project))
    matrix = parsed.get("version_matrix") if isinstance(parsed.get("version_matrix"), dict) else {}
    events = [event for event in parsed.get("events", []) if isinstance(event, dict)]
    tasks = [task for task in parsed.get("tasks", []) if isinstance(task, dict)]
    latest_event = events[-1] if events else {}
    open_tasks = [task for task in tasks if str(task.get("status") or "") in {"blocked", "in_progress", "ready", "planned"}]
    next_task = "UNKNOWN"
    for task in open_tasks:
        if str(task.get("status")) in {"blocked", "in_progress", "ready"}:
            next_task = str(task.get("task_id") or "UNKNOWN")
            break
    if next_task == "UNKNOWN" and open_tasks:
        next_task = str(open_tasks[0].get("task_id") or "UNKNOWN")
    ledger_path = project_path / "docs" / "governance" / "DEVELOPMENT_LEDGER.md"
    blockers = "UNKNOWN"
    if ledger_path.exists():
        for line in ledger_path.read_text(encoding="utf-8").splitlines():
            if line.lower().lstrip("- ").startswith("blockers:"):
                blockers = line.split(":", 1)[1].strip() or "none"
                break
    model_versions = matrix.get("model_versions") if isinstance(matrix, dict) else {}
    parameter_versions = matrix.get("parameter_profile_versions") if isinstance(matrix, dict) else {}
    return {
        "project_id": structural.project_scope(project),
        "path": str(project.get("path") or ""),
        "ci_mode": str(project.get("ci_mode") or ""),
        "product_version": matrix.get("product_version", "UNKNOWN") if isinstance(matrix, dict) else "UNKNOWN",
        "model_versions": model_versions if isinstance(model_versions, dict) else {},
        "parameter_versions": parameter_versions if isinstance(parameter_versions, dict) else {},
        "current_iteration": matrix.get("current_iteration", "UNKNOWN") if isinstance(matrix, dict) else "UNKNOWN",
        "current_phase": matrix.get("current_phase", "UNKNOWN") if isinstance(matrix, dict) else "UNKNOWN",
        "current_gate": matrix.get("current_gate", "UNKNOWN") if isinstance(matrix, dict) else "UNKNOWN",
        "latest_event": latest_event,
        "model_count": len(parsed.get("models", [])),
        "formula_count": len(parsed.get("formulas", [])),
        "parameter_count": len(parsed.get("parameters", [])),
        "task_count": len(tasks),
        "unbound_event_count": sum(
            1
            for event in events
            if str(event.get("git_commit") or "").upper() == "PENDING"
            and str(event.get("result_commit") or "").upper() in {"", "PENDING"}
        ),
        "blockers": blockers,
        "next_task": next_task,
    }


def compact_versions(values: dict[str, Any], limit: int = 3) -> str:
    if not values:
        return "UNKNOWN"
    items = [f"{key}:{value}" for key, value in sorted(values.items())]
    if len(items) > limit:
        return ", ".join(items[:limit]) + f", +{len(items) - limit}"
    return ", ".join(items)


def render_project_status(project_info: dict[str, Any], commit: str, generated_at: str) -> str:
    latest = project_info["latest_event"] if isinstance(project_info["latest_event"], dict) else {}
    model_delta = latest.get("model_delta") or latest.get("model_ids_changed") or "UNKNOWN"
    parameter_delta = latest.get("parameter_delta") or latest.get("parameter_ids_changed") or "UNKNOWN"
    tests = latest.get("tests_run") or "UNKNOWN"
    evidence = latest.get("evidence_refs") or "UNKNOWN"
    return f"""# Project Governance Status

Generated: `{generated_at}`
Commit: `{commit}`
Source: generated from machine governance registries, Git metadata, and validation results. Do not hand-edit counts here.

## Current State

- Project: `{project_info['project_id']}`
- Path: `{project_info['path']}`
- CI mode: `{project_info['ci_mode']}`
- Product version: `{project_info['product_version']}`
- Model versions: `{compact_versions(project_info['model_versions'])}`
- Parameter profile versions: `{compact_versions(project_info['parameter_versions'])}`
- Current iteration: `{project_info['current_iteration']}`
- Current phase: `{project_info['current_phase']}`
- Current gate: `{project_info['current_gate']}`
- Model count: `{project_info['model_count']}`
- Formula count: `{project_info['formula_count']}`
- Parameter count: `{project_info['parameter_count']}`
- Task count: `{project_info['task_count']}`
- Unbound event count: `{project_info['unbound_event_count']}`

## Latest Run

- Event: `{latest.get('event_id') or latest.get('iteration_id') or 'UNKNOWN'}`
- Task: `{latest.get('task_id') or latest.get('task_ids') or 'UNKNOWN'}`
- Summary: {latest.get('summary') or latest.get('objective') or 'UNKNOWN'}
- Model delta: `{model_delta}`
- Parameter delta: `{parameter_delta}`
- Tests: `{tests}`
- Evidence: `{evidence}`
- Result: `{latest.get('result') or 'UNKNOWN'}`
- Rollback: {latest.get('rollback') or 'UNKNOWN'}

## Current Blockers

{project_info['blockers']}

## Next Task

`{project_info['next_task']}`
"""


def render_dashboard(projects: list[dict[str, Any]], commit: str, generated_at: str) -> str:
    lines = [
        "# Governance Dashboard",
        "",
        f"Generated: `{generated_at}`",
        f"Commit: `{commit}`",
        "Tree hash: `CURRENT_CHECKOUT_TREE`",
        "Source: generated from machine governance registries and Git metadata. Do not hand-edit project counts here.",
        "",
        "| Project | Version | Model versions | Parameter versions | Iteration | Phase | Gate | Latest run | Model delta | Parameter delta | Blockers | Unbound events | CI | Next task |",
        "|---|---:|---|---|---|---|---|---|---|---|---|---:|---|---|",
    ]
    for project in projects:
        latest = project["latest_event"] if isinstance(project["latest_event"], dict) else {}
        latest_run = latest.get("event_id") or latest.get("iteration_id") or "UNKNOWN"
        model_delta = latest.get("model_delta") or latest.get("model_ids_changed") or "UNKNOWN"
        parameter_delta = latest.get("parameter_delta") or latest.get("parameter_ids_changed") or "UNKNOWN"
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{project['project_id']}`",
                    f"`{project['product_version']}`",
                    compact_versions(project["model_versions"], 2),
                    compact_versions(project["parameter_versions"], 2),
                    f"`{project['current_iteration']}`",
                    f"`{project['current_phase']}`",
                    f"`{project['current_gate']}`",
                    f"`{latest_run}`",
                    f"`{model_delta}`",
                    f"`{parameter_delta}`",
                    project["blockers"].replace("|", "\\|"),
                    str(project["unbound_event_count"]),
                    f"`{project['ci_mode']}`",
                    f"`{project['next_task']}`",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Audit Notes",
            "",
            "- `Unbound events` counts historical events that still use `git_commit: PENDING` without a concrete `result_commit`.",
            "- GitHub branch protection or ruleset status is an external repository setting. If it cannot be read with an authenticated API/UI check, report it as `UNVERIFIED` instead of claiming no-bypass enforcement.",
            "- Regenerate with `python3 scripts/generate_governance_dashboard.py --write`; verify determinism with `git diff --exit-code` after a second run.",
            "",
        ]
    )
    return "\n".join(lines)


def generate(write: bool) -> dict[str, Any]:
    config = structural.load_yaml(structural.PROJECTS_FILE)
    projects = [p for p in structural.as_list(config.get("projects")) if isinstance(p, dict)]
    # Do not embed the final commit SHA or wall-clock time in generated files:
    # both values change after committing and would make CI regeneration drift.
    commit = "CURRENT_CHECKOUT"
    generated_at = "DETERMINISTIC_GENERATION"
    project_infos = [load_project(project) for project in projects]
    outputs: list[str] = []
    dashboard = render_dashboard(project_infos, commit, generated_at)
    dashboard_path = ROOT / "GOVERNANCE_DASHBOARD.md"
    if write:
        dashboard_path.write_text(dashboard, encoding="utf-8")
    outputs.append(str(dashboard_path.relative_to(ROOT)))
    for info in project_infos:
        status_path = ROOT / info["path"] / "docs" / "governance" / "STATUS.md"
        text = render_project_status(info, commit, generated_at)
        if write:
            status_path.write_text(text, encoding="utf-8")
        outputs.append(str(status_path.relative_to(ROOT)))
    return {
        "status": "PASS",
        "write": write,
        "generated_at": generated_at,
        "commit": commit,
        "outputs": outputs,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Write dashboard and STATUS.md files.")
    args = parser.parse_args()
    print(json.dumps(generate(args.write), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
