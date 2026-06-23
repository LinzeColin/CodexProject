#!/usr/bin/env python3
"""Single-entry Lean v2 governance CLI."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import validate_project_governance as governance


sys.dont_write_bytecode = True

ROOT = governance.ROOT
PROJECTS_FILE = governance.PROJECTS_FILE
HUMAN_ENTRY_FILES = ["功能清单", "开发记录", "模型参数文件", "VERSION", "CHANGELOG.md"]
LEAN_CANONICAL_FILES = [
    "docs/governance/project.yaml",
    "docs/governance/roadmap.yaml",
    "docs/governance/events.jsonl",
    "VERSION",
    "CHANGELOG.md",
]
ROOT_GOVERNANCE_PREFIXES = (
    ".agents/",
    ".codex/",
    ".github/workflows/project-governance.yml",
    "AGENTS.md",
    "docs/governance/",
    "governance/",
    "scripts/",
    "tests/governance/",
)


def file_state(root: Path, rel_path: str) -> dict[str, Any]:
    path = root / rel_path
    exists = path.exists()
    is_file = path.is_file()
    size = path.stat().st_size if is_file else 0
    return {
        "path": rel_path,
        "exists": exists,
        "nonempty": bool(is_file and size > 0),
        "bytes": size,
    }


def text_or_na(value: Any) -> str:
    if value is None or value == "":
        return "NOT_APPLICABLE"
    if isinstance(value, list):
        return ", ".join(text_or_na(item) for item in value) if value else "NOT_APPLICABLE"
    return str(value)


def pct(value: float, total: float) -> str:
    if total <= 0:
        return "0.00%"
    return f"{(value / total * 100):.2f}%"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def missing_paths(states: list[dict[str, Any]]) -> list[str]:
    return [str(item["path"]) for item in states if not item["exists"]]


def project_summary(root: Path, project: dict[str, Any], legacy_files: list[str]) -> dict[str, Any]:
    project_path = str(project.get("path") or "").replace("\\", "/").rstrip("/")
    project_root = root / project_path
    human = [file_state(project_root, path) for path in HUMAN_ENTRY_FILES]
    canonical = [file_state(project_root, path) for path in LEAN_CANONICAL_FILES]
    legacy = [file_state(project_root, path) for path in legacy_files]
    return {
        "project_id": str(project.get("project_id") or ""),
        "path": project_path,
        "path_exists": project_root.exists(),
        "ci_mode": str(project.get("ci_mode") or ""),
        "migration_version": str((project.get("migration") or {}).get("version") or ""),
        "human_entry": {
            "files": human,
            "missing": missing_paths(human),
        },
        "canonical": {
            "files": canonical,
            "missing": missing_paths(canonical),
        },
        "legacy_governance": {
            "files_total": len(legacy),
            "missing": missing_paths(legacy),
        },
    }


def build_baseline(root: Path = ROOT, projects_file: Path = PROJECTS_FILE) -> dict[str, Any]:
    config = governance.load_yaml(projects_file)
    if not isinstance(config, dict):
        raise ValueError(f"{governance.rel(projects_file)} must parse to a mapping")
    root_required = [str(item) for item in governance.as_list((config.get("root_governance") or {}).get("required_files"))]
    root_states = [file_state(root, path) for path in root_required]
    projects = [item for item in governance.as_list(config.get("projects")) if isinstance(item, dict)]
    legacy_files = [str(item) for item in governance.as_list(config.get("project_governance_files"))]
    project_summaries = [project_summary(root, project, legacy_files) for project in projects]
    return {
        "schema_version": 1,
        "command": "baseline",
        "scope": "all",
        "root": {
            "required_files_total": len(root_states),
            "required_files_missing": missing_paths(root_states),
        },
        "totals": {
            "projects": len(project_summaries),
            "project_paths_missing": sum(1 for item in project_summaries if not item["path_exists"]),
            "human_entry_missing": sum(len(item["human_entry"]["missing"]) for item in project_summaries),
            "canonical_missing": sum(len(item["canonical"]["missing"]) for item in project_summaries),
            "legacy_governance_missing": sum(len(item["legacy_governance"]["missing"]) for item in project_summaries),
        },
        "projects": project_summaries,
    }


def registered_project(config: dict[str, Any], project_selector: str) -> dict[str, Any]:
    for project in [item for item in governance.as_list(config.get("projects")) if isinstance(item, dict)]:
        if project_selector in {str(project.get("project_id") or ""), str(project.get("path") or "").replace("\\", "/")}:
            return project
    raise ValueError(f"Unknown project: {project_selector}")


def load_project_facts(project_root: Path) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    governance_root = project_root / "docs" / "governance"
    project_facts = governance.load_yaml(governance_root / "project.yaml")
    roadmap = governance.load_yaml(governance_root / "roadmap.yaml")
    events_path = governance_root / "events.jsonl"
    events = governance.load_jsonl(events_path) if events_path.exists() else []
    if not isinstance(project_facts, dict):
        raise ValueError("docs/governance/project.yaml must parse to a mapping")
    if not isinstance(roadmap, dict):
        raise ValueError("docs/governance/roadmap.yaml must parse to a mapping")
    return project_facts, roadmap, [event for event in events if isinstance(event, dict)]


def roadmap_totals(roadmap: dict[str, Any]) -> dict[str, float]:
    total = 0.0
    completed = 0.0
    for stage in governance.as_list(roadmap.get("stages")):
        if not isinstance(stage, dict):
            continue
        for phase in governance.as_list(stage.get("phases")):
            if not isinstance(phase, dict):
                continue
            for task in governance.as_list(phase.get("tasks")):
                if not isinstance(task, dict):
                    continue
                hours = float(task.get("estimated_hours") or 0)
                total += hours
                if str(task.get("status") or "") == "completed":
                    completed += hours
    return {"total": total, "completed": completed}


def render_roadmap_body(roadmap: dict[str, Any]) -> list[str]:
    totals = roadmap_totals(roadmap)
    lines: list[str] = ["Stage -> Phase -> Task", ""]
    for stage in [item for item in governance.as_list(roadmap.get("stages")) if isinstance(item, dict)]:
        stage_hours = sum(
            float(task.get("estimated_hours") or 0)
            for phase in governance.as_list(stage.get("phases"))
            if isinstance(phase, dict)
            for task in governance.as_list(phase.get("tasks"))
            if isinstance(task, dict)
        )
        lines.extend(
            [
                f"### {text_or_na(stage.get('stage_id'))} {text_or_na(stage.get('name'))}",
                "",
                f"- person_goal: `{text_or_na(stage.get('person_goal'))}`",
                f"- status: `{text_or_na(stage.get('status'))}`",
                f"- derived_hours: `{stage_hours:.2f}`",
                f"- derived_percent: `{pct(stage_hours, totals['total'])}`",
                f"- stop_conditions: `{text_or_na(stage.get('stop_conditions'))}`",
                f"- stop_gate: `{text_or_na((stage.get('stop_gate') or {}).get('gate_id'))}`",
                "",
            ]
        )
        for phase in [item for item in governance.as_list(stage.get("phases")) if isinstance(item, dict)]:
            phase_hours = sum(
                float(task.get("estimated_hours") or 0)
                for task in governance.as_list(phase.get("tasks"))
                if isinstance(task, dict)
            )
            lines.extend(
                [
                    f"#### {text_or_na(phase.get('phase_id'))} {text_or_na(phase.get('name'))}",
                    "",
                    f"- objective: `{text_or_na(phase.get('objective'))}`",
                    f"- status: `{text_or_na(phase.get('status'))}`",
                    f"- derived_hours: `{phase_hours:.2f}`",
                    f"- derived_percent: `{pct(phase_hours, totals['total'])}`",
                    f"- stop_conditions: `{text_or_na(phase.get('stop_conditions'))}`",
                    f"- stop_gate: `{text_or_na((phase.get('stop_gate') or {}).get('gate_id'))}`",
                    "",
                    "| Task | 名称 | 状态 | 工时 | 占比 | 依赖 | 验收 |",
                    "|---|---|---|---:|---:|---|---|",
                ]
            )
            for task in [item for item in governance.as_list(phase.get("tasks")) if isinstance(item, dict)]:
                hours = float(task.get("estimated_hours") or 0)
                lines.append(
                    f"| {text_or_na(task.get('task_id'))} | {text_or_na(task.get('name'))} | {text_or_na(task.get('status'))} | {hours:.2f} | {pct(hours, totals['total'])} | {text_or_na(task.get('dependencies'))} | {text_or_na(task.get('acceptance_ids'))} |"
                )
            lines.append("")
    return lines


def render_feature_list(project_facts: dict[str, Any], roadmap: dict[str, Any]) -> str:
    features = [item for item in governance.as_list(project_facts.get("features")) if isinstance(item, dict)]
    evidence = [item for item in governance.as_list(project_facts.get("evidence_refs")) if isinstance(item, dict)]
    totals = roadmap_totals(roadmap)
    lines = [
        "# 功能清单",
        "",
        "## 摘要",
        "",
        f"- project_id: `{text_or_na(project_facts.get('project_id'))}`",
        f"- product_version: `{text_or_na(project_facts.get('version'))}`",
        f"- current_stage: `{text_or_na(roadmap.get('current_stage_id'))}`",
        f"- current_phase: `{text_or_na(roadmap.get('current_phase_id'))}`",
        f"- current_task: `{text_or_na(roadmap.get('current_task_id'))}`",
        f"- progress: `{pct(totals['completed'], totals['total'])}`",
        f"- capability_count: `{len(features)}`",
        "- blockers: `NOT_APPLICABLE`",
        f"- next_gate: `{text_or_na(roadmap.get('next_gate_id'))}`",
        "- next_unique_task: `NOT_APPLICABLE`",
        f"- evidence_status: `{text_or_na(project_facts.get('fact_level'))}`",
        "",
        "## 功能概览",
        "",
        "| 功能 ID | 名称 | 状态 | 说明 | 证据等级 |",
        "|---|---|---|---|---|",
    ]
    for feature in features:
        lines.append(
            f"| {text_or_na(feature.get('feature_id'))} | {text_or_na(feature.get('name'))} | {text_or_na(feature.get('status'))} | {text_or_na(feature.get('description'))} | {text_or_na(feature.get('fact_level'))} |"
        )
    lines.extend(["", "## 证据", "", "| 证据 ID | 类型 | 引用 | 事实等级 |", "|---|---|---|---|"])
    for item in evidence:
        lines.append(
            f"| {text_or_na(item.get('evidence_id'))} | {text_or_na(item.get('kind'))} | {text_or_na(item.get('ref'))} | {text_or_na(item.get('fact_level'))} |"
        )
    return "\n".join(lines).rstrip() + "\n"


def render_development_record(project_facts: dict[str, Any], roadmap: dict[str, Any], events: list[dict[str, Any]]) -> str:
    totals = roadmap_totals(roadmap)
    lines = [
        "# 开发记录",
        "",
        "## 摘要",
        "",
        f"- project_id: `{text_or_na(project_facts.get('project_id'))}`",
        f"- product_version: `{text_or_na(project_facts.get('version'))}`",
        f"- current_stage: `{text_or_na(roadmap.get('current_stage_id'))}`",
        f"- current_phase: `{text_or_na(roadmap.get('current_phase_id'))}`",
        f"- current_task: `{text_or_na(roadmap.get('current_task_id'))}`",
        f"- total_hours: `{totals['total']:.2f}`",
        f"- completed_hours: `{totals['completed']:.2f}`",
        f"- progress: `{pct(totals['completed'], totals['total'])}`",
        "- blockers: `NOT_APPLICABLE`",
        f"- next_gate: `{text_or_na(roadmap.get('next_gate_id'))}`",
        "- next_unique_task: `NOT_APPLICABLE`",
        f"- evidence_status: `{text_or_na(project_facts.get('fact_level'))}`",
        "",
        "## Roadmap",
        "",
    ]
    lines.extend(render_roadmap_body(roadmap))
    lines.extend(["", "## 近期事件", "", "| 时间 | 类型 | 摘要 | 任务 | 事实等级 |", "|---|---|---|---|---|"])
    for event in events:
        lines.append(
            f"| {text_or_na(event.get('occurred_at'))} | {text_or_na(event.get('event_type'))} | {text_or_na(event.get('summary'))} | {text_or_na(event.get('task_id'))} | {text_or_na(event.get('fact_level'))} |"
        )
    return "\n".join(lines).rstrip() + "\n"


def render_model_parameters(project_facts: dict[str, Any], roadmap: dict[str, Any]) -> str:
    models = [item for item in governance.as_list(project_facts.get("models")) if isinstance(item, dict)]
    formulas = [item for item in governance.as_list(project_facts.get("formulas")) if isinstance(item, dict)]
    parameters = [item for item in governance.as_list(project_facts.get("parameters")) if isinstance(item, dict)]
    lines = [
        "# 模型参数文件",
        "",
        "## 摘要",
        "",
        f"- project_id: `{text_or_na(project_facts.get('project_id'))}`",
        f"- product_version: `{text_or_na(project_facts.get('version'))}`",
        f"- current_stage: `{text_or_na(roadmap.get('current_stage_id'))}`",
        f"- current_phase: `{text_or_na(roadmap.get('current_phase_id'))}`",
        f"- current_task: `{text_or_na(roadmap.get('current_task_id'))}`",
        f"- active_model_count: `{len(models)}`",
        f"- active_formula_count: `{len(formulas)}`",
        f"- active_parameter_count: `{len(parameters)}`",
        "- blockers: `NOT_APPLICABLE`",
        f"- next_gate: `{text_or_na(roadmap.get('next_gate_id'))}`",
        "- next_unique_task: `NOT_APPLICABLE`",
        f"- evidence_status: `{text_or_na(project_facts.get('fact_level'))}`",
        "",
        "## 模型",
    ]
    for model in models:
        lines.extend(
            [
                "",
                f"### {text_or_na(model.get('model_id'))} {text_or_na(model.get('name'))}",
                "",
                f"- purpose: `{text_or_na(model.get('purpose'))}`",
                f"- status: `{text_or_na(model.get('status'))}`",
                f"- fact_level: `{text_or_na(model.get('fact_level'))}`",
                f"- formula_refs: `{text_or_na(model.get('formula_ids'))}`",
                f"- parameter_refs: `{text_or_na(model.get('parameter_ids'))}`",
                f"- evidence_refs: `{text_or_na(model.get('evidence_refs'))}`",
            ]
        )
    lines.extend(["", "## 公式"])
    for formula in formulas:
        lines.extend(
            [
                "",
                f"### {text_or_na(formula.get('formula_id'))}",
                "",
                f"- model_id: `{text_or_na(formula.get('model_id'))}`",
                f"- expression_or_pseudocode: `{text_or_na(formula.get('expression'))}`",
                f"- evidence_refs: `{text_or_na(formula.get('evidence_refs'))}`",
            ]
        )
    lines.extend(["", "## 参数", "", "| 参数 ID | 符号 | 名称 | 当前值 | 来源 | 事实等级 |", "|---|---|---|---|---|---|"])
    for parameter in parameters:
        lines.append(
            f"| {text_or_na(parameter.get('parameter_id'))} | {text_or_na(parameter.get('symbol'))} | {text_or_na(parameter.get('name'))} | {text_or_na(parameter.get('value'))} | {text_or_na(parameter.get('source'))} | {text_or_na(parameter.get('fact_level'))} |"
        )
    return "\n".join(lines).rstrip() + "\n"


def render_project_files(project_root: Path, *, write: bool = False) -> dict[str, Any]:
    project_facts, roadmap, events = load_project_facts(project_root)
    rendered = {
        "功能清单": render_feature_list(project_facts, roadmap),
        "开发记录": render_development_record(project_facts, roadmap, events),
        "模型参数文件": render_model_parameters(project_facts, roadmap),
    }
    if write:
        for rel_path, text in rendered.items():
            (project_root / rel_path).write_text(text, encoding="utf-8", newline="\n")
    return {
        "write": write,
        "files": [
            {"path": path, "bytes": len(text.encode("utf-8")), "sha256": sha256_text(text)}
            for path, text in rendered.items()
        ],
    }


def render_registered_project(project_selector: str, *, write: bool, root: Path = ROOT, projects_file: Path = PROJECTS_FILE) -> dict[str, Any]:
    config = governance.load_yaml(projects_file)
    if not isinstance(config, dict):
        raise ValueError(f"{governance.rel(projects_file)} must parse to a mapping")
    project = registered_project(config, project_selector)
    project_path = str(project.get("path") or "").replace("\\", "/").rstrip("/")
    result = render_project_files(root / project_path, write=write)
    return {
        "schema_version": 1,
        "command": "render",
        "project_id": str(project.get("project_id") or ""),
        "path": project_path,
        **result,
    }


def build_validate_argv(args: argparse.Namespace) -> list[str]:
    validate_argv: list[str] = []
    if args.all:
        validate_argv.append("--all")
    elif args.project:
        validate_argv.extend(["--project", args.project])
    elif args.changed_only:
        validate_argv.append("--changed-only")
    else:
        validate_argv.append("--changed-only")
    if args.mode:
        validate_argv.extend(["--mode", args.mode])
    if args.base_ref:
        validate_argv.extend(["--base-ref", args.base_ref])
    if args.enforce_sync:
        validate_argv.append("--enforce-sync")
    if args.semantic:
        validate_argv.append("--semantic")
    if args.drift_report:
        validate_argv.append("--drift-report")
    return validate_argv


def is_root_governance_change(path: str, root_required: set[str]) -> bool:
    normalized = path.replace("\\", "/")
    return normalized in root_required or normalized.startswith(ROOT_GOVERNANCE_PREFIXES)


def build_changed_scope(base_ref: str | None = None, root: Path = ROOT, projects_file: Path = PROJECTS_FILE) -> dict[str, Any]:
    config = governance.load_yaml(projects_file)
    if not isinstance(config, dict):
        raise ValueError(f"{governance.rel(projects_file)} must parse to a mapping")
    changed = governance.git_changed_files(base_ref)
    projects = [item for item in governance.as_list(config.get("projects")) if isinstance(item, dict)]
    root_required = {
        str(item).replace("\\", "/")
        for item in governance.as_list((config.get("root_governance") or {}).get("required_files"))
    }
    root_changed = any(is_root_governance_change(path, root_required) for path in changed)
    selected = projects if root_changed else [project for project in projects if governance.project_matches_changed(project, changed)]
    return {
        "schema_version": 1,
        "command": "changed-scope",
        "base_ref": base_ref or "",
        "changed_files": changed,
        "root_governance_changed": root_changed,
        "all_projects_required": root_changed,
        "selected_projects": [
            {
                "project_id": str(project.get("project_id") or ""),
                "path": str(project.get("path") or "").replace("\\", "/").rstrip("/"),
                "ci_mode": str(project.get("ci_mode") or ""),
            }
            for project in selected
        ],
        "selected_project_count": len(selected),
        "total_project_count": len(projects),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    baseline = subparsers.add_parser("baseline", help="Print a read-only repository baseline summary.")
    baseline.add_argument("--all", action="store_true", help="Inspect root governance and all registered projects.")
    changed_scope = subparsers.add_parser("changed-scope", help="Print read-only changed project selection.")
    changed_scope.add_argument("--base-ref", help="Explicit base commit/ref for changed-scope diff selection.")
    render = subparsers.add_parser("render", help="Render one project's human entry files from Lean canonical facts.")
    render.add_argument("--project", required=True, help="Registered project_id or project path.")
    render.add_argument("--write", action="store_true", help="Write rendered files to the selected project root.")
    validate = subparsers.add_parser("validate", help="Run governance structure and semantic validation.")
    validate_scope = validate.add_mutually_exclusive_group()
    validate_scope.add_argument("--all", action="store_true", help="Validate root governance and all registered projects.")
    validate_scope.add_argument("--project", help="Validate one registered project by project_id or path.")
    validate_scope.add_argument("--changed-only", action="store_true", help="Validate root governance and changed project scopes.")
    validate.add_argument("--mode", choices=["advisory", "required"], help="Override project ci_mode.")
    validate.add_argument("--base-ref", help="Explicit base commit/ref for changed-only diff validation.")
    validate.add_argument("--enforce-sync", action="store_true", help="Enforce diff-driven governance update requirements.")
    validate.add_argument("--semantic", action="store_true", help="Run semantic drift checks.")
    validate.add_argument("--drift-report", action="store_true", help="Print a machine-readable semantic drift report.")
    args = parser.parse_args(argv)
    if args.command == "baseline":
        if not args.all:
            parser.error("baseline currently requires --all")
        summary = build_baseline(ROOT, PROJECTS_FILE)
        print(json.dumps(summary, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
        return 0
    if args.command == "changed-scope":
        summary = build_changed_scope(args.base_ref, ROOT, PROJECTS_FILE)
        print(json.dumps(summary, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
        return 0
    if args.command == "render":
        summary = render_registered_project(args.project, write=args.write, root=ROOT, projects_file=PROJECTS_FILE)
        print(json.dumps(summary, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
        return 0
    if args.command == "validate":
        return governance.main(build_validate_argv(args))
    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
