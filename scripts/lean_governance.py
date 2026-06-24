#!/usr/bin/env python3
"""Single-entry Lean v2 governance CLI."""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import validate_project_governance as governance


sys.dont_write_bytecode = True

ROOT = governance.ROOT
PROJECTS_FILE = governance.PROJECTS_FILE
HUMAN_ENTRY_FILES = ["功能清单", "开发记录", "模型参数文件", "VERSION", "CHANGELOG.md"]
RENDER_VIEW_ALIASES = {
    "feature-list": "功能清单",
    "功能清单": "功能清单",
    "development-record": "开发记录",
    "开发记录": "开发记录",
    "model-parameters": "模型参数文件",
    "模型参数文件": "模型参数文件",
}
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


def roadmap_kind(roadmap: dict[str, Any]) -> str:
    return str(roadmap.get("roadmap_kind") or "product").strip()


def ensure_product_roadmap(roadmap: dict[str, Any], *, target: str) -> None:
    kind = roadmap_kind(roadmap)
    if kind != "product":
        raise ValueError(f"{target} requires roadmap_kind=product; got {kind}")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_adp_v7_1_lock(project_root: Path) -> dict[str, Any] | None:
    lock_path = project_root / "docs" / "pursuing_goal" / "v7_1" / "V7_1_ROOT_LOCK.yaml"
    if project_root.name != "arxiv-daily-push" or not lock_path.is_file():
        return None
    data = governance.load_yaml(lock_path)
    return data if isinstance(data, dict) else None


def v7_1_summary_lines(lock: dict[str, Any] | None) -> list[str]:
    if not lock:
        return []
    contract = lock.get("current_contract") if isinstance(lock.get("current_contract"), dict) else {}
    stage1 = lock.get("stage1_boundary") if isinstance(lock.get("stage1_boundary"), dict) else {}
    stage2 = lock.get("stage2_boundary") if isinstance(lock, dict) and isinstance(lock.get("stage2_boundary"), dict) else {}
    aliases = stage2.get("legacy_aliases") if isinstance(stage2.get("legacy_aliases"), dict) else {}
    alias_text = "; ".join(f"{key} -> {value}" for key, value in sorted(aliases.items())) or "NOT_APPLICABLE"
    forbidden = lock.get("forbidden_actions_until_integrated_gate")
    forbidden_items = []
    if isinstance(forbidden, dict):
        forbidden_items = [key for key, value in forbidden.items() if value is True]
    return [
        "",
        "## V7.1 当前根治理锁",
        "",
        f"- contract_version: `{text_or_na(contract.get('contract_version'))}`",
        f"- contract_lock: `docs/pursuing_goal/v7_1/V7_1_ROOT_LOCK.yaml`",
        f"- contract_sha256: `{text_or_na(contract.get('contract_sha256'))}`",
        f"- roadmap_version: `{text_or_na(contract.get('roadmap_version'))}`",
        f"- roadmap_sha256: `{text_or_na(contract.get('roadmap_sha256'))}`",
        f"- audit_version: `{text_or_na(contract.get('audit_version'))}`",
        f"- stage1_gate: `{text_or_na(stage1.get('maintained_gate') or stage1.get('accepted_gate'))}`",
        f"- stage2_current_task: `{text_or_na(stage2.get('current_task_id'))}`",
        f"- stage2_shadow_source_task: `{text_or_na(stage2.get('current_shadow_source_task'))}`",
        f"- legacy_alias: `{alias_text}`",
        f"- stage2_final_task: `{text_or_na(stage2.get('final_task'))}`",
        f"- stage2_stop_gate: `{text_or_na(stage2.get('stop_gate'))}`",
        f"- stage2_integrated_production_accepted: `{str(bool(stage2.get('production_accepted'))).lower()}`",
        f"- production_forbidden_until: `P0=0; P1=0; S2PMT07 independent review passed`",
        f"- forbidden_actions: `{text_or_na(forbidden_items)}`",
    ]


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


def active_count(items: list[dict[str, Any]]) -> int:
    return sum(1 for item in items if str(item.get("status") or "").lower() == "active")


def roadmap_tasks(roadmap: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        task
        for stage in governance.as_list(roadmap.get("stages"))
        if isinstance(stage, dict)
        for phase in governance.as_list(stage.get("phases"))
        if isinstance(phase, dict)
        for task in governance.as_list(phase.get("tasks"))
        if isinstance(task, dict)
    ]


def roadmap_stop_gates(roadmap: dict[str, Any]) -> list[dict[str, Any]]:
    gates: list[dict[str, Any]] = []
    for stage in governance.as_list(roadmap.get("stages")):
        if not isinstance(stage, dict):
            continue
        stage_gate = stage.get("stop_gate")
        if isinstance(stage_gate, dict):
            gates.append(stage_gate)
        for phase in governance.as_list(stage.get("phases")):
            if not isinstance(phase, dict):
                continue
            phase_gate = phase.get("stop_gate")
            if isinstance(phase_gate, dict):
                gates.append(phase_gate)
    return gates


def task_label(task: dict[str, Any]) -> str:
    return f"{text_or_na(task.get('task_id'))} {text_or_na(task.get('name'))} ({text_or_na(task.get('status'))})"


def roadmap_blockers(roadmap: dict[str, Any]) -> list[str]:
    return [task_label(task) for task in roadmap_tasks(roadmap) if str(task.get("status") or "") == "blocked"]


def next_unique_task(roadmap: dict[str, Any]) -> str:
    terminal_states = {"completed", "rejected", "deprecated"}
    tasks = roadmap_tasks(roadmap)
    current_task_id = str(roadmap.get("current_task_id") or "")
    for task in tasks:
        if str(task.get("task_id") or "") == current_task_id and str(task.get("status") or "") not in terminal_states:
            return task_label(task)
    for task in tasks:
        if str(task.get("status") or "") not in terminal_states:
            return task_label(task)
    return "none"


def roadmap_fact_summary(project_facts: dict[str, Any], roadmap: dict[str, Any]) -> dict[str, Any]:
    tasks = roadmap_tasks(roadmap)
    gates = roadmap_stop_gates(roadmap)
    project_evidence = [
        item for item in governance.as_list(project_facts.get("evidence_refs")) if isinstance(item, dict)
    ]
    task_evidence_refs = {
        str(item)
        for task in tasks
        for item in governance.as_list(task.get("evidence_refs"))
        if item
    }
    gate_evidence_refs = {
        str(item)
        for gate in gates
        for item in governance.as_list(gate.get("evidence"))
        if item
    }
    test_commands = [
        item
        for task in tasks
        for item in governance.as_list(task.get("test_commands"))
        if item
    ]
    acceptance_ids = {
        str(item)
        for task in tasks
        for item in governance.as_list(task.get("acceptance_ids"))
        if item
    }
    blockers = roadmap_blockers(roadmap)
    return {
        "blockers": text_or_na(blockers) if blockers else "none",
        "next_unique_task": next_unique_task(roadmap),
        "roadmap_task_count": len(tasks),
        "roadmap_gate_count": len(gates),
        "roadmap_acceptance_count": len(acceptance_ids),
        "roadmap_test_command_count": len(test_commands),
        "roadmap_evidence_ref_count": len(task_evidence_refs | gate_evidence_refs),
        "project_evidence_ref_count": len(project_evidence),
    }


def render_roadmap_body(roadmap: dict[str, Any]) -> list[str]:
    totals = roadmap_totals(roadmap)
    lines: list[str] = ["Stage -> Phase -> Task", ""]
    for stage in [item for item in governance.as_list(roadmap.get("stages")) if isinstance(item, dict)]:
        stage_gate = stage.get("stop_gate") if isinstance(stage.get("stop_gate"), dict) else {}
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
                f"- stop_gate: `{text_or_na(stage_gate.get('gate_id'))}`",
                f"- stop_gate_pass_criteria: `{text_or_na(stage_gate.get('pass_criteria'))}`",
                f"- stop_gate_evidence: `{text_or_na(stage_gate.get('evidence'))}`",
                f"- stop_gate_failure_action: `{text_or_na(stage_gate.get('failure_action'))}`",
                "",
            ]
        )
        for phase in [item for item in governance.as_list(stage.get("phases")) if isinstance(item, dict)]:
            phase_gate = phase.get("stop_gate") if isinstance(phase.get("stop_gate"), dict) else {}
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
                    f"- stop_gate: `{text_or_na(phase_gate.get('gate_id'))}`",
                    f"- stop_gate_pass_criteria: `{text_or_na(phase_gate.get('pass_criteria'))}`",
                    f"- stop_gate_evidence: `{text_or_na(phase_gate.get('evidence'))}`",
                    f"- stop_gate_failure_action: `{text_or_na(phase_gate.get('failure_action'))}`",
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
            lines.extend(["", "Task detail fields:", ""])
            for task in [item for item in governance.as_list(phase.get("tasks")) if isinstance(item, dict)]:
                lines.extend(
                    [
                        f"- {text_or_na(task.get('task_id'))} test_commands: `{text_or_na(task.get('test_commands'))}`",
                        f"- {text_or_na(task.get('task_id'))} test_results: `{text_or_na(task.get('test_results'))}`",
                        f"- {text_or_na(task.get('task_id'))} evidence_refs: `{text_or_na(task.get('evidence_refs'))}`",
                        f"- {text_or_na(task.get('task_id'))} risks: `{text_or_na(task.get('risks'))}`",
                        f"- {text_or_na(task.get('task_id'))} rollback: `{text_or_na(task.get('rollback'))}`",
                    ]
                )
            lines.append("")
    return lines


def render_feature_list(project_facts: dict[str, Any], roadmap: dict[str, Any]) -> str:
    features = [item for item in governance.as_list(project_facts.get("features")) if isinstance(item, dict)]
    evidence = [item for item in governance.as_list(project_facts.get("evidence_refs")) if isinstance(item, dict)]
    totals = roadmap_totals(roadmap)
    summary = roadmap_fact_summary(project_facts, roadmap)
    lock = load_adp_v7_1_lock(ROOT / str(project_facts.get("project_id") or ""))
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
        f"- blockers: `{summary['blockers']}`",
        f"- next_gate: `{text_or_na(roadmap.get('next_gate_id'))}`",
        f"- next_unique_task: `{summary['next_unique_task']}`",
        f"- evidence_ref_count: `{summary['project_evidence_ref_count']}`",
        f"- roadmap_test_command_count: `{summary['roadmap_test_command_count']}`",
        f"- roadmap_gate_count: `{summary['roadmap_gate_count']}`",
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
    lines.extend(v7_1_summary_lines(lock))
    lines.extend(["", "## 证据", "", "| 证据 ID | 类型 | 引用 | 事实等级 |", "|---|---|---|---|"])
    for item in evidence:
        lines.append(
            f"| {text_or_na(item.get('evidence_id'))} | {text_or_na(item.get('kind'))} | {text_or_na(item.get('ref'))} | {text_or_na(item.get('fact_level'))} |"
        )
    return "\n".join(lines).rstrip() + "\n"


def render_development_record(project_facts: dict[str, Any], roadmap: dict[str, Any], events: list[dict[str, Any]]) -> str:
    ensure_product_roadmap(roadmap, target="project development record")
    totals = roadmap_totals(roadmap)
    summary = roadmap_fact_summary(project_facts, roadmap)
    lock = load_adp_v7_1_lock(ROOT / str(project_facts.get("project_id") or ""))
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
        f"- blockers: `{summary['blockers']}`",
        f"- next_gate: `{text_or_na(roadmap.get('next_gate_id'))}`",
        f"- next_unique_task: `{summary['next_unique_task']}`",
        f"- roadmap_kind: `{roadmap_kind(roadmap)}`",
        f"- roadmap_task_count: `{summary['roadmap_task_count']}`",
        f"- roadmap_gate_count: `{summary['roadmap_gate_count']}`",
        f"- roadmap_acceptance_count: `{summary['roadmap_acceptance_count']}`",
        f"- roadmap_test_command_count: `{summary['roadmap_test_command_count']}`",
        f"- roadmap_evidence_ref_count: `{summary['roadmap_evidence_ref_count']}`",
        f"- evidence_status: `{text_or_na(project_facts.get('fact_level'))}`",
        "",
        "## Roadmap",
        "",
    ]
    lines.extend(render_roadmap_body(roadmap))
    lines.extend(v7_1_summary_lines(lock))
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
    summary = roadmap_fact_summary(project_facts, roadmap)
    lock = load_adp_v7_1_lock(ROOT / str(project_facts.get("project_id") or "")) or {}
    stage2 = lock.get("stage2_boundary") if isinstance(lock, dict) and isinstance(lock.get("stage2_boundary"), dict) else {}
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
        f"- active_model_count: `{active_count(models)}`",
        f"- active_formula_count: `{active_count(formulas)}`",
        f"- active_parameter_count: `{active_count(parameters)}`",
        f"- blockers: `{summary['blockers']}`",
        f"- next_gate: `{text_or_na(roadmap.get('next_gate_id'))}`",
        f"- next_unique_task: `{summary['next_unique_task']}`",
        f"- evidence_ref_count: `{summary['project_evidence_ref_count']}`",
        f"- roadmap_test_command_count: `{summary['roadmap_test_command_count']}`",
        f"- roadmap_gate_count: `{summary['roadmap_gate_count']}`",
        f"- evidence_status: `{text_or_na(project_facts.get('fact_level'))}`",
    ]
    lines.extend(v7_1_summary_lines(lock))
    if lock:
        lines.extend(
            [
                "",
                "## V7.1 根治理说明",
                "",
                "- V7.1 根治理锁是产品/治理合同，不新增 active model、formula 或 parameter。",
                "- `ARXIV_PRODUCTION_ACCEPTED_MAINTAINED` 只保持 Stage 1 arXiv 单源验收，不代表 Stage 2 已生产验收。",
                "- `INTEGRATED_PRODUCTION_ACCEPTED -> DAILY_OPERATION` 只允许在 P0/P1 清零且 `S2PMT07` 独立复审通过后声明。",
                f"- `{text_or_na(stage2.get('current_task_id'))}` 是当前 Stage2 任务；`{text_or_na(stage2.get('current_shadow_source_task'))}` 保留为已通过的来源 Shadow 线程任务。",
            ]
        )
    lines.extend(["", "## 模型"])
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


def rendered_project_texts(project_facts: dict[str, Any], roadmap: dict[str, Any], events: list[dict[str, Any]]) -> dict[str, str]:
    return {
        "功能清单": render_feature_list(project_facts, roadmap),
        "开发记录": render_development_record(project_facts, roadmap, events),
        "模型参数文件": render_model_parameters(project_facts, roadmap),
    }


def selected_rendered_texts(rendered: dict[str, str], view: str | None = None) -> dict[str, str]:
    if not view:
        return rendered
    selected = RENDER_VIEW_ALIASES.get(view)
    if not selected:
        allowed = ", ".join(sorted(RENDER_VIEW_ALIASES))
        raise ValueError(f"Unknown render view: {view}; expected one of {allowed}")
    return {selected: rendered[selected]}


def render_project_files(project_root: Path, *, write: bool = False, view: str | None = None) -> dict[str, Any]:
    project_facts, roadmap, events = load_project_facts(project_root)
    rendered = selected_rendered_texts(rendered_project_texts(project_facts, roadmap, events), view)
    file_results: list[dict[str, Any]] = []
    if write:
        for rel_path, text in rendered.items():
            path = project_root / rel_path
            previous = path.read_text(encoding="utf-8") if path.exists() else None
            changed = previous != text
            if changed:
                path.write_text(text, encoding="utf-8", newline="\n")
            file_results.append(
                {
                    "path": rel_path,
                    "bytes": len(text.encode("utf-8")),
                    "sha256": sha256_text(text),
                    "changed": changed,
                }
            )
    else:
        file_results = [
            {"path": path, "bytes": len(text.encode("utf-8")), "sha256": sha256_text(text)}
            for path, text in rendered.items()
        ]
    return {
        "write": write,
        "view": RENDER_VIEW_ALIASES.get(view, "all") if view else "all",
        "files": file_results,
        "updated_count": sum(1 for item in file_results if item.get("changed") is True),
        "unchanged_count": sum(1 for item in file_results if item.get("changed") is False),
    }


def collect_reference_issues(project_facts: dict[str, Any]) -> list[dict[str, str]]:
    evidence_ids = {
        str(item.get("evidence_id"))
        for item in governance.as_list(project_facts.get("evidence_refs"))
        if isinstance(item, dict) and item.get("evidence_id")
    }
    issues: list[dict[str, str]] = []
    for section in ("features", "models", "formulas", "parameters", "strategies", "validations"):
        for item in [value for value in governance.as_list(project_facts.get(section)) if isinstance(value, dict)]:
            subject = (
                item.get("feature_id")
                or item.get("model_id")
                or item.get("formula_id")
                or item.get("parameter_id")
                or item.get("strategy_id")
                or item.get("validation_id")
                or section
            )
            for evidence_id in [str(value) for value in governance.as_list(item.get("evidence_refs"))]:
                if evidence_id not in evidence_ids:
                    issues.append({"subject": str(subject), "kind": "missing_evidence_ref", "ref": evidence_id})
            for field in ("code_refs", "config_refs", "test_refs"):
                for ref in [str(value) for value in governance.as_list(item.get(field))]:
                    if not ref.strip():
                        issues.append({"subject": str(subject), "kind": f"empty_{field}", "ref": ref})
    return issues


def check_render_project_files(project_root: Path, view: str | None = None) -> dict[str, Any]:
    project_facts, roadmap, events = load_project_facts(project_root)
    rendered = selected_rendered_texts(rendered_project_texts(project_facts, roadmap, events), view)
    drift: list[dict[str, Any]] = []
    for rel_path, expected in rendered.items():
        path = project_root / rel_path
        actual = path.read_text(encoding="utf-8") if path.exists() else ""
        if actual != expected:
            drift.append(
                {
                    "path": rel_path,
                    "exists": path.exists(),
                    "expected_sha256": sha256_text(expected),
                    "actual_sha256": sha256_text(actual) if path.exists() else "",
                }
            )
    reference_issues = collect_reference_issues(project_facts)
    return {
        "write": False,
        "view": RENDER_VIEW_ALIASES.get(view, "all") if view else "all",
        "drift": drift,
        "drift_count": len(drift),
        "reference_issues": reference_issues,
        "reference_issue_count": len(reference_issues),
    }


def render_registered_project(
    project_selector: str,
    *,
    write: bool,
    view: str | None = None,
    root: Path = ROOT,
    projects_file: Path = PROJECTS_FILE,
) -> dict[str, Any]:
    config = governance.load_yaml(projects_file)
    if not isinstance(config, dict):
        raise ValueError(f"{governance.rel(projects_file)} must parse to a mapping")
    project = registered_project(config, project_selector)
    project_path = str(project.get("path") or "").replace("\\", "/").rstrip("/")
    result = render_project_files(root / project_path, write=write, view=view)
    return {
        "schema_version": 1,
        "command": "render",
        "project_id": str(project.get("project_id") or ""),
        "path": project_path,
        **result,
    }


def check_render_registered_project(
    project_selector: str,
    *,
    view: str | None = None,
    root: Path = ROOT,
    projects_file: Path = PROJECTS_FILE,
) -> dict[str, Any]:
    config = governance.load_yaml(projects_file)
    if not isinstance(config, dict):
        raise ValueError(f"{governance.rel(projects_file)} must parse to a mapping")
    project = registered_project(config, project_selector)
    project_path = str(project.get("path") or "").replace("\\", "/").rstrip("/")
    result = check_render_project_files(root / project_path, view=view)
    return {
        "schema_version": 1,
        "command": "check-render",
        "project_id": str(project.get("project_id") or ""),
        "path": project_path,
        **result,
    }


def has_check_render_inputs(project_root: Path) -> bool:
    governance_root = project_root / "docs" / "governance"
    return (governance_root / "project.yaml").is_file() and (governance_root / "roadmap.yaml").is_file()


def git_status_porcelain(root: Path = ROOT) -> list[str]:
    try:
        result = subprocess.run(
            ["git", "-c", "core.quotePath=false", "status", "--porcelain=v1"],
            cwd=root,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=5.0,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return [f"git_status_error:{exc}"]
    if result.returncode != 0:
        stderr = result.stderr.strip() or f"exit_{result.returncode}"
        return [f"git_status_failed:{stderr}"]
    return [line for line in result.stdout.splitlines() if line.strip()]


def run_validator_capture(validate_argv: list[str]) -> dict[str, Any]:
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        exit_code = governance.main(validate_argv)
    return {
        "argv": validate_argv,
        "exit_code": exit_code,
        "output": [line for line in stdout.getvalue().splitlines() if line.strip()],
    }


def run_changed_only_ci(base_ref: str | None = None, *, root: Path = ROOT, projects_file: Path = PROJECTS_FILE) -> tuple[int, dict[str, Any]]:
    started = time.perf_counter()
    baseline = build_baseline(root, projects_file)
    scope = build_changed_scope(base_ref, root, projects_file)
    validate_argv = ["--changed-only", "--enforce-sync", "--semantic"]
    if base_ref:
        validate_argv.extend(["--base-ref", base_ref])
    validation = run_validator_capture(validate_argv)

    check_render_results: list[dict[str, Any]] = []
    check_render_skipped: list[dict[str, str]] = []
    check_render_failed = False
    for project in scope["selected_projects"]:
        project_id = str(project.get("project_id") or "")
        project_path = str(project.get("path") or "").replace("\\", "/").rstrip("/")
        project_root = root / project_path
        if not has_check_render_inputs(project_root):
            check_render_skipped.append(
                {
                    "project_id": project_id,
                    "path": project_path,
                    "reason": "missing_lean_canonical_facts",
                }
            )
            continue
        try:
            result = check_render_project_files(project_root)
        except Exception as exc:
            check_render_failed = True
            check_render_results.append(
                {
                    "project_id": project_id,
                    "path": project_path,
                    "error": str(exc),
                    "write": False,
                }
            )
            continue
        result = {
            "project_id": project_id,
            "path": project_path,
            **result,
        }
        if result["drift_count"] or result["reference_issue_count"]:
            check_render_failed = True
        check_render_results.append(result)

    dirty = git_status_porcelain(root)
    zero_diff = not dirty
    summary = {
        "schema_version": 1,
        "command": "ci",
        "scope": "changed-only",
        "base_ref": base_ref or "",
        "write": False,
        "baseline": {
            "projects": baseline["totals"]["projects"],
            "human_entry_missing": baseline["totals"]["human_entry_missing"],
            "canonical_missing": baseline["totals"]["canonical_missing"],
            "legacy_governance_missing": baseline["totals"]["legacy_governance_missing"],
        },
        "changed_scope": scope,
        "validation": validation,
        "check_render": {
            "checked": check_render_results,
            "checked_count": len(check_render_results),
            "skipped": check_render_skipped,
            "skipped_count": len(check_render_skipped),
        },
        "zero_diff": {
            "clean": zero_diff,
            "changed_count": len(dirty),
            "changed_files": dirty[:20],
        },
        "duration_seconds": round(time.perf_counter() - started, 3),
    }
    exit_code = 0 if validation["exit_code"] == 0 and not check_render_failed and zero_diff else 1
    return exit_code, summary


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


def root_changed_scope_excluded_projects(config: dict[str, Any]) -> set[str]:
    root_config = config.get("root_governance") if isinstance(config.get("root_governance"), dict) else {}
    return {str(item) for item in governance.as_list(root_config.get("changed_scope_excluded_projects")) if item}


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
    excluded = root_changed_scope_excluded_projects(config) if root_changed else set()
    selected = (
        [project for project in projects if str(project.get("project_id") or "") not in excluded]
        if root_changed
        else [project for project in projects if governance.project_matches_changed(project, changed)]
    )
    return {
        "schema_version": 1,
        "command": "changed-scope",
        "base_ref": base_ref or "",
        "changed_files": changed,
        "root_governance_changed": root_changed,
        "all_projects_required": bool(root_changed and not excluded),
        "root_scope_excluded_projects": sorted(excluded),
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
    render.add_argument("--view", help="Optional single view alias or human entry filename to render.")
    render.add_argument("--write", action="store_true", help="Write rendered files to the selected project root.")
    check_render = subparsers.add_parser("check-render", help="Compare rendered human files in memory without writing.")
    check_render.add_argument("--project", required=True, help="Registered project_id or project path.")
    check_render.add_argument("--view", help="Optional single view alias or human entry filename to check.")
    ci = subparsers.add_parser("ci", help="Run the read-only changed-only CI orchestration.")
    ci_scope = ci.add_mutually_exclusive_group(required=True)
    ci_scope.add_argument("--changed-only", action="store_true", help="Run the PR/main changed-only CI gate.")
    ci.add_argument("--base-ref", help="Explicit base commit/ref for changed-only CI.")
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
        summary = render_registered_project(
            args.project,
            write=args.write,
            view=args.view,
            root=ROOT,
            projects_file=PROJECTS_FILE,
        )
        print(json.dumps(summary, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
        return 0
    if args.command == "check-render":
        summary = check_render_registered_project(args.project, view=args.view, root=ROOT, projects_file=PROJECTS_FILE)
        print(json.dumps(summary, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
        return 0
    if args.command == "ci":
        exit_code, summary = run_changed_only_ci(args.base_ref, root=ROOT, projects_file=PROJECTS_FILE)
        print(json.dumps(summary, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
        return exit_code
    if args.command == "validate":
        return governance.main(build_validate_argv(args))
    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
