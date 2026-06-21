#!/usr/bin/env python3
"""Generate human-readable governance status pages from machine sources."""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import validate_project_governance as structural
import validate_governance_sync as sync


sys.dont_write_bytecode = True

ROOT = structural.ROOT
OPEN_TASK_STATES = {"blocked", "in_progress", "ready", "planned", "proposed"}
COMPLETED_TASK_STATES = {"completed", "rejected", "deprecated"}
PHASE_ORDER = {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5}


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
    completed_task_ids = {str(task.get("task_id")) for task in tasks if str(task.get("status") or "") in COMPLETED_TASK_STATES}
    ledger_path = project_path / "docs" / "governance" / "DEVELOPMENT_LEDGER.md"
    blockers = "UNKNOWN"
    if ledger_path.exists():
        for line in ledger_path.read_text(encoding="utf-8").splitlines():
            if line.lower().lstrip("- ").startswith("blockers:"):
                blockers = line.split(":", 1)[1].strip() or "none"
                break
    unknown_count = count_unknowns(parsed)
    stale_evidence_count = sum(
        1
        for event in events
        if str(event.get("git_commit") or "").upper() == "PENDING"
        and str(event.get("result_commit") or "").upper() in {"", "PENDING"}
    )
    model_versions = matrix.get("model_versions") if isinstance(matrix, dict) else {}
    parameter_versions = matrix.get("parameter_profile_versions") if isinstance(matrix, dict) else {}
    latest_manifest = latest_run_manifest(structural.project_scope(project))
    current_phase = matrix.get("current_phase", "UNKNOWN") if isinstance(matrix, dict) else "UNKNOWN"
    next_task_info = select_next_task(tasks, completed_task_ids, str(current_phase))
    semantic_coverage = project.get("semantic_coverage") if isinstance(project.get("semantic_coverage"), dict) else {}
    return {
        "project_id": structural.project_scope(project),
        "path": str(project.get("path") or ""),
        "ci_mode": str(project.get("ci_mode") or ""),
        "product_version": matrix.get("product_version", "UNKNOWN") if isinstance(matrix, dict) else "UNKNOWN",
        "model_versions": model_versions if isinstance(model_versions, dict) else {},
        "parameter_versions": parameter_versions if isinstance(parameter_versions, dict) else {},
        "current_iteration": matrix.get("current_iteration", "UNKNOWN") if isinstance(matrix, dict) else "UNKNOWN",
        "current_phase": current_phase,
        "current_gate": matrix.get("current_gate", "UNKNOWN") if isinstance(matrix, dict) else "UNKNOWN",
        "latest_event": latest_event,
        "model_count": len(parsed.get("models", [])),
        "formula_count": len(parsed.get("formulas", [])),
        "parameter_count": len(parsed.get("parameters", [])),
        "task_count": len(tasks),
        "unbound_event_count": stale_evidence_count,
        "unknown_count": unknown_count,
        "stale_evidence_count": stale_evidence_count,
        "blockers": blockers,
        "next_task": next_task_info["task_id"],
        "next_task_info": next_task_info,
        "tasks": tasks,
        "latest_manifest": latest_manifest,
        "semantic_coverage": semantic_coverage,
        "semantic_coverage_status": semantic_coverage.get("status", "UNKNOWN") if isinstance(semantic_coverage, dict) else "UNKNOWN",
        "semantic_coverage_task": semantic_coverage.get("task_id", "UNKNOWN") if isinstance(semantic_coverage, dict) else "UNKNOWN",
        "semantic_coverage_target": semantic_coverage.get("target", "UNKNOWN") if isinstance(semantic_coverage, dict) else "UNKNOWN",
    }


def compact_versions(values: dict[str, Any], limit: int = 3) -> str:
    if not values:
        return "UNKNOWN"
    items = [f"{key}:{value}" for key, value in sorted(values.items())]
    if len(items) > limit:
        return ", ".join(items[:limit]) + f", +{len(items) - limit}"
    return ", ".join(items)


def value_text(value: Any, *, limit: int = 5) -> str:
    if value is None or value == "":
        return "UNKNOWN"
    if isinstance(value, dict):
        if not value:
            return "UNKNOWN"
        items = [f"{key}: {value_text(item, limit=2)}" for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))]
        if len(items) > limit:
            items = items[:limit] + [f"+{len(value) - limit} more"]
        return "; ".join(items)
    if isinstance(value, list):
        if not value:
            return "none"
        items = [value_text(item, limit=2) for item in value[:limit]]
        if len(value) > limit:
            items.append(f"+{len(value) - limit} more")
        return ", ".join(items)
    text = str(value).replace("\n", " ").strip()
    return text or "UNKNOWN"


def count_unknowns(parsed: dict[str, Any]) -> int:
    count = 0

    def visit(value: Any) -> None:
        nonlocal count
        if isinstance(value, dict):
            for item in value.values():
                visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)
        elif isinstance(value, str):
            if re.search(r"\bUNKNOWN\b|\bHUMAN_REVIEW_REQUIRED\b", value):
                count += 1

    for key in ("models", "formulas", "parameters", "tasks", "traceability", "version_matrix"):
        visit(parsed.get(key))
    return count


def task_status_score(task: dict[str, Any], completed_task_ids: set[str], current_phase: str) -> tuple[int, str]:
    status = str(task.get("status") or "")
    task_id = str(task.get("task_id") or "UNKNOWN")
    if status in COMPLETED_TASK_STATES:
        return (-10_000, "not selected: terminal status")
    score = {
        "blocked": 95,
        "in_progress": 90,
        "ready": 85,
        "planned": 60,
        "proposed": 40,
    }.get(status, 0)
    dependencies = [str(dep) for dep in structural.as_list(task.get("dependencies"))]
    unmet = [dep for dep in dependencies if dep and dep not in completed_task_ids]
    if unmet:
        score -= 30
    task_phase = str(task.get("phase") or "")
    phase_lag = PHASE_ORDER.get(str(current_phase), 0) - PHASE_ORDER.get(task_phase, 0)
    if phase_lag > 0 and status not in {"blocked"}:
        score -= 55 * phase_lag
    objective = f"{task.get('objective') or ''} {task.get('risk') or ''}".lower()
    for keyword, bonus in {
        "blocked": 18,
        "unknown": 16,
        "semantic": 15,
        "owner": 14,
        "evidence": 12,
        "calibration": 12,
        "required": 10,
        "validation": 8,
        "production": 6,
    }.items():
        if keyword in objective:
            score += bonus
    if task_id.endswith("-001"):
        score += 1
    reason = f"status={status}; phase={task_phase}; current_phase={current_phase}; unmet_dependencies={value_text(unmet, limit=3)}; score={score}"
    return score, reason


def select_next_task(tasks: list[dict[str, Any]], completed_task_ids: set[str], current_phase: str) -> dict[str, str]:
    candidates: list[tuple[int, str, dict[str, Any]]] = []
    for task in tasks:
        if not isinstance(task, dict):
            continue
        status = str(task.get("status") or "")
        if status not in OPEN_TASK_STATES:
            continue
        score, reason = task_status_score(task, completed_task_ids, current_phase)
        candidates.append((score, reason, task))
    if not candidates:
        return {
            "task_id": "UNKNOWN",
            "status": "UNKNOWN",
            "acceptance": "UNKNOWN",
            "objective": "No open task is registered.",
            "reason": "No non-terminal task found in delivery_tasks.yaml.",
            "blocked_owner": "Project owner",
            "unblock_condition": "Create or unblock a delivery task with acceptance criteria.",
        }
    score, reason, task = sorted(candidates, key=lambda item: (-item[0], str(item[2].get("task_id") or "")))[0]
    acceptance_ids = value_text(structural.as_list(task.get("acceptance_ids")), limit=3)
    dependencies = [str(dep) for dep in structural.as_list(task.get("dependencies"))]
    unmet = [dep for dep in dependencies if dep and dep not in completed_task_ids]
    status = str(task.get("status") or "UNKNOWN")
    return {
        "task_id": str(task.get("task_id") or "UNKNOWN"),
        "status": status,
        "acceptance": acceptance_ids,
        "objective": value_text(task.get("objective"), limit=3),
        "reason": reason,
        "blocked_owner": "Project owner" if status == "blocked" or unmet else "Codex/governance runner",
        "unblock_condition": f"Complete dependencies {value_text(unmet, limit=3)}" if unmet else f"Meet acceptance {acceptance_ids}",
    }


def latest_run_manifest(project_id: str) -> dict[str, Any]:
    manifest_dir = ROOT / "governance" / "run_manifests"
    manifests: list[dict[str, Any]] = []
    for path in sorted(manifest_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if str(data.get("project_id") or "") == project_id:
            data["_path"] = str(path.relative_to(ROOT))
            manifests.append(data)
    if not manifests:
        return {}
    return sorted(manifests, key=lambda item: str(item.get("started_at") or item.get("finished_at") or item.get("_path")), reverse=True)[0]


def confidence_label(project_info: dict[str, Any]) -> str:
    if project_info["ci_mode"] == "required" and project_info["unknown_count"] == 0 and project_info["stale_evidence_count"] == 0:
        return "High"
    if project_info["ci_mode"] == "required":
        return "Medium"
    return "Low"


def top_risks(project_info: dict[str, Any]) -> list[str]:
    risks: list[str] = []
    if project_info.get("semantic_coverage_status") != "machine_verified":
        risks.append(
            "Semantic extractor coverage is "
            f"{project_info.get('semantic_coverage_status', 'UNKNOWN')}; "
            f"rollout task {project_info.get('semantic_coverage_task', 'UNKNOWN')} remains open."
        )
    blockers = str(project_info.get("blockers") or "")
    if blockers and blockers.lower() not in {"none", "no blockers"}:
        risks.append(f"Blocker: {blockers}")
    if project_info.get("unknown_count", 0):
        risks.append(f"UNKNOWN/HUMAN_REVIEW_REQUIRED facts: {project_info['unknown_count']}")
    if project_info.get("stale_evidence_count", 0):
        risks.append(f"Unbound or stale evidence events: {project_info['stale_evidence_count']}")
    manifest = project_info.get("latest_manifest") if isinstance(project_info.get("latest_manifest"), dict) else {}
    for risk in structural.as_list(manifest.get("unresolved_risks")):
        risks.append(str(risk))
    while len(risks) < 3:
        risks.append("No additional machine risk recorded.")
    return risks[:3]


def render_project_status(project_info: dict[str, Any], commit: str, generated_at: str) -> str:
    latest = project_info["latest_event"] if isinstance(project_info["latest_event"], dict) else {}
    model_delta = latest.get("model_delta") or latest.get("model_ids_changed") or "UNKNOWN"
    parameter_delta = latest.get("parameter_delta") or latest.get("parameter_ids_changed") or "UNKNOWN"
    tests = latest.get("tests_run") or "UNKNOWN"
    evidence = latest.get("evidence_refs") or "UNKNOWN"
    next_task = project_info["next_task_info"] if isinstance(project_info.get("next_task_info"), dict) else {}
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
- UNKNOWN/HUMAN_REVIEW_REQUIRED count: `{project_info['unknown_count']}`
- Semantic coverage: `{project_info['semantic_coverage_status']}`
- Semantic rollout task: `{project_info['semantic_coverage_task']}`

## Latest Run

- Event: `{latest.get('event_id') or latest.get('iteration_id') or 'UNKNOWN'}`
- Task: `{latest.get('task_id') or latest.get('task_ids') or 'UNKNOWN'}`
- Summary: {latest.get('summary') or latest.get('objective') or 'UNKNOWN'}
- Model delta: {value_text(model_delta, limit=6)}
- Parameter delta: {value_text(parameter_delta, limit=6)}
- Tests: {value_text(tests, limit=6)}
- Evidence: {value_text(evidence, limit=6)}
- Result: `{latest.get('result') or 'UNKNOWN'}`
- Rollback: {latest.get('rollback') or 'UNKNOWN'}

## Current Blockers

{project_info['blockers']}

## Semantic Coverage

- Status: `{project_info['semantic_coverage_status']}`
- Target: {value_text(project_info['semantic_coverage_target'], limit=4)}
- Evidence/rollout: {value_text(project_info.get('semantic_coverage'), limit=6)}

## Next Task

`{project_info['next_task']}` - {next_task.get('objective', 'UNKNOWN')}

- Status: `{next_task.get('status', 'UNKNOWN')}`
- Acceptance: {next_task.get('acceptance', 'UNKNOWN')}
- Selection rationale: {next_task.get('reason', 'UNKNOWN')}
"""


def render_owner_status(project_info: dict[str, Any], commit: str, generated_at: str) -> str:
    latest = project_info["latest_event"] if isinstance(project_info["latest_event"], dict) else {}
    manifest = project_info["latest_manifest"] if isinstance(project_info.get("latest_manifest"), dict) else {}
    next_task = project_info["next_task_info"] if isinstance(project_info.get("next_task_info"), dict) else {}
    version_delta = manifest.get("version_delta") or {
        "product_version": project_info["product_version"],
        "current_iteration": project_info["current_iteration"],
        "current_phase": project_info["current_phase"],
        "current_gate": project_info["current_gate"],
    }
    formula_delta = manifest.get("formula_delta") or latest.get("model_delta") or latest.get("model_ids_changed") or "UNKNOWN"
    parameter_delta = manifest.get("parameter_delta") or latest.get("parameter_delta") or latest.get("parameter_ids_changed") or "UNKNOWN"
    risks = top_risks(project_info)
    freshness = "fresh" if project_info.get("stale_evidence_count", 0) == 0 else f"{project_info['stale_evidence_count']} unbound event(s)"
    conclusion = (
        f"{project_info['project_id']} 当前处于 {project_info['current_phase']} 阶段 / {project_info['current_gate']} gate；"
        f"CI 模式为 {project_info['ci_mode']}，机器事实源显示模型 {project_info['model_count']} 个、公式 {project_info['formula_count']} 个、参数 {project_info['parameter_count']} 个。"
    )
    return f"""# OWNER_STATUS

生成方式：由 `scripts/generate_governance_dashboard.py` 从机器事实源生成；不要手工编辑。

## 1. 当前结论

{conclusion}

## 2. 更新时间与 Commit

- 生成标记：`{generated_at}`
- 仓库提交：`{commit}`
- 最近事件时间：`{latest.get('timestamp') or latest.get('date') or 'UNKNOWN'}`
- 最近事件提交证据：`{latest.get('git_commit') or latest.get('result_commit') or 'UNKNOWN'}`

## 3. 本轮最重要变化

{value_text(latest.get('summary') or latest.get('objective') or 'UNKNOWN', limit=4)}

## 4. 模型、公式、参数旧值到新值

- 版本变化：{value_text(version_delta, limit=6)}
- 模型/公式变化：{value_text(formula_delta, limit=6)}
- 参数变化：{value_text(parameter_delta, limit=6)}

## 5. 为什么改变及证据等级

- 原因：{value_text(latest.get('summary') or latest.get('objective') or 'UNKNOWN', limit=4)}
- 证据等级：`{latest.get('fact_level') or latest.get('evidence_level') or 'UNKNOWN'}`
- 证据引用：{value_text(latest.get('evidence_refs') or manifest.get('evidence_refs') or 'UNKNOWN', limit=6)}

## 6. 对输出、风险和业务决策的影响

{value_text(manifest.get('model_delta') or latest.get('model_delta') or latest.get('model_ids_changed') or 'No runtime model delta recorded.', limit=6)}

## 7. 当前置信度和证据新鲜度

- 置信度：`{confidence_label(project_info)}`
- 证据新鲜度：`{freshness}`
- 语义覆盖：`{project_info['semantic_coverage_status']}`
- 语义覆盖任务：`{project_info['semantic_coverage_task']}`
- UNKNOWN/HUMAN_REVIEW_REQUIRED 数量：`{project_info['unknown_count']}`
- 未绑定事件数量：`{project_info['stale_evidence_count']}`

## 8. 需要项目所有者决定的事项

{next_task.get('objective', 'UNKNOWN')}

## 9. 当前前三风险

1. {risks[0]}
2. {risks[1]}
3. {risks[2]}

## 10. 下一项可执行任务及 Acceptance

- 下一任务：`{next_task.get('task_id', 'UNKNOWN')}`
- 状态：`{next_task.get('status', 'UNKNOWN')}`
- Acceptance：{next_task.get('acceptance', 'UNKNOWN')}
- 选择理由：{next_task.get('reason', 'UNKNOWN')}

## 11. 阻塞负责人和解除条件

- 负责人：{next_task.get('blocked_owner', 'UNKNOWN')}
- 解除条件：{next_task.get('unblock_condition', 'UNKNOWN')}

## 12. UNKNOWN 与过期证据数量

- UNKNOWN/HUMAN_REVIEW_REQUIRED：`{project_info['unknown_count']}`
- 过期或未绑定证据：`{project_info['stale_evidence_count']}`
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
        "| Project | Version | Model versions | Parameter versions | Semantic coverage | Iteration | Phase | Gate | Latest run | Model delta | Parameter delta | Blockers | Unbound events | CI | Next task |",
        "|---|---:|---|---|---|---|---|---|---|---|---|---|---:|---|---|",
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
                    f"`{project['semantic_coverage_status']}`",
                    f"`{project['current_iteration']}`",
                    f"`{project['current_phase']}`",
                    f"`{project['current_gate']}`",
                    f"`{latest_run}`",
                    value_text(model_delta, limit=3),
                    value_text(parameter_delta, limit=3),
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
        owner_path = ROOT / info["path"] / "docs" / "governance" / "OWNER_STATUS.md"
        owner_text = render_owner_status(info, commit, generated_at)
        if write:
            owner_path.write_text(owner_text, encoding="utf-8")
        outputs.append(str(owner_path.relative_to(ROOT)))
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
