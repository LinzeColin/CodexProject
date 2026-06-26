#!/usr/bin/env python3
"""Single-entry Lean v2 governance CLI."""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any

import validate_project_governance as governance


sys.dont_write_bytecode = True
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

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
    "README.md",
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


def load_adp_v7_2_current(project_root: Path) -> dict[str, Any] | None:
    current_path = project_root / "docs" / "pursuing_goal" / "CURRENT.yaml"
    lock_path = project_root / "docs" / "pursuing_goal" / "v7_2" / "V7_2_ROOT_LOCK.yaml"
    if project_root.name != "arxiv-daily-push" or not current_path.is_file() or not lock_path.is_file():
        return None
    current = governance.load_yaml(current_path)
    lock = governance.load_yaml(lock_path)
    if not isinstance(current, dict) or not isinstance(lock, dict):
        return None
    return {"current": current, "lock": lock}


def v7_2_current_summary_lines(bundle: dict[str, Any] | None) -> list[str]:
    if not bundle:
        return []
    current = bundle.get("current") if isinstance(bundle.get("current"), dict) else {}
    lock = bundle.get("lock") if isinstance(bundle.get("lock"), dict) else {}
    contract = lock.get("current_contract") if isinstance(lock.get("current_contract"), dict) else {}
    current_contract = current.get("current_product_contract") if isinstance(current.get("current_product_contract"), dict) else {}
    previous = current.get("previous_read_only_contract") if isinstance(current.get("previous_read_only_contract"), dict) else {}
    context = current.get("current_pointer_registry") if isinstance(current.get("current_pointer_registry"), dict) else {}
    return [
        "",
        "## V7.2 CURRENT 产品合同",
        "",
        f"- contract_version: `{text_or_na(current_contract.get('version') or contract.get('contract_version'))}`",
        f"- root_lock: `{text_or_na(current_contract.get('root_lock'))}`",
        f"- product_contract: `{text_or_na(current_contract.get('product_contract'))}`",
        f"- contract_sha256: `{text_or_na(contract.get('contract_sha256'))}`",
        f"- roadmap_version: `{text_or_na(contract.get('roadmap_version'))}`",
        f"- roadmap_sha256: `{text_or_na(contract.get('roadmap_sha256'))}`",
        f"- migration_matrix_sha256: `{text_or_na(contract.get('migration_matrix_sha256'))}`",
        f"- final_review_sha256: `{text_or_na(contract.get('final_review_sha256'))}`",
        f"- previous_read_only_contract: `{text_or_na(previous.get('version'))}`",
        f"- previous_read_only_root_lock: `{text_or_na(previous.get('root_lock'))}`",
        f"- global_current_task: `{text_or_na(context.get('global_current_task'))}`",
        f"- email_v1_workstream_next: `{text_or_na(context.get('email_v1_workstream_next'))}`",
        f"- v7_contract_remediation_next: `{text_or_na(context.get('v7_contract_remediation_next'))}`",
        f"- shadow_source_next: `{text_or_na(context.get('shadow_source_next'))}`",
        f"- agent_revalidation_required: `{str(bool(current.get('agent_revalidation_required'))).lower()}`",
    ]


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
        "## V7.1 只读历史根治理锁",
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
        f"- production_forbidden_until: `inherited V7.1 P0=0; inherited V7.1 P1=0; S2PMT07 independent review passed`",
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


def stop_gate_field(gate: dict[str, Any], primary: str, fallback: str | None = None) -> str:
    value = gate.get(primary)
    if fallback and value in (None, "", []):
        value = gate.get(fallback)
    return text_or_na(value)


def stop_gate_failure_action(gate: dict[str, Any]) -> str:
    value = gate.get("failure_action")
    if value not in (None, "", []):
        return text_or_na(value)
    if gate:
        return "block gated claim/action until pass conditions and evidence are satisfied"
    return text_or_na(None)


def task_test_results(task: dict[str, Any]) -> str:
    value = task.get("test_results")
    if value not in (None, "", []):
        return text_or_na(value)
    status = str(task.get("status") or "")
    if status in {"planned", "proposed"}:
        return "not executed yet; planned task only"
    if status.startswith("blocked"):
        return "not executed yet; blocked until prerequisite gate"
    if governance.as_list(task.get("evidence_refs")):
        return "not duplicated in roadmap; see evidence_refs"
    return "not recorded in roadmap"


def task_risks(task: dict[str, Any]) -> str:
    value = task.get("risks")
    if value in (None, "", []):
        value = task.get("risk")
    return text_or_na(value)


def roadmap_fact_summary(project_facts: dict[str, Any], roadmap: dict[str, Any]) -> dict[str, Any]:
    use_contextual_fallbacks = str(roadmap.get("project_id") or project_facts.get("project_id") or "") == "arxiv-daily-push"
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
        for item in governance.as_list(
            gate.get("evidence") or (gate.get("evidence_refs") if use_contextual_fallbacks else None)
        )
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


def human_entry_text(value: Any) -> str:
    text = text_or_na(value)
    return (
        text.replace("compatibility indexes", "低可读索引页")
        .replace("compatibility index", "低可读索引页")
    )


def render_roadmap_body(roadmap: dict[str, Any]) -> list[str]:
    use_contextual_fallbacks = str(roadmap.get("project_id") or "") == "arxiv-daily-push"
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
                f"- stop_conditions: `{human_entry_text(stage.get('stop_conditions'))}`",
                f"- stop_gate: `{text_or_na(stage_gate.get('gate_id'))}`",
                f"- stop_gate_pass_criteria: `{stop_gate_field(stage_gate, 'pass_criteria', 'pass_conditions') if use_contextual_fallbacks else human_entry_text(stage_gate.get('pass_criteria'))}`",
                f"- stop_gate_evidence: `{stop_gate_field(stage_gate, 'evidence', 'evidence_refs') if use_contextual_fallbacks else text_or_na(stage_gate.get('evidence'))}`",
                f"- stop_gate_failure_action: `{stop_gate_failure_action(stage_gate) if use_contextual_fallbacks else text_or_na(stage_gate.get('failure_action'))}`",
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
                    f"- stop_conditions: `{human_entry_text(phase.get('stop_conditions'))}`",
                    f"- stop_gate: `{text_or_na(phase_gate.get('gate_id'))}`",
                    f"- stop_gate_pass_criteria: `{stop_gate_field(phase_gate, 'pass_criteria', 'pass_conditions') if use_contextual_fallbacks else human_entry_text(phase_gate.get('pass_criteria'))}`",
                    f"- stop_gate_evidence: `{stop_gate_field(phase_gate, 'evidence', 'evidence_refs') if use_contextual_fallbacks else text_or_na(phase_gate.get('evidence'))}`",
                    f"- stop_gate_failure_action: `{stop_gate_failure_action(phase_gate) if use_contextual_fallbacks else text_or_na(phase_gate.get('failure_action'))}`",
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
                        f"- {text_or_na(task.get('task_id'))} test_results: `{task_test_results(task) if use_contextual_fallbacks else text_or_na(task.get('test_results'))}`",
                        f"- {text_or_na(task.get('task_id'))} evidence_refs: `{text_or_na(task.get('evidence_refs'))}`",
                        f"- {text_or_na(task.get('task_id'))} risks: `{task_risks(task) if use_contextual_fallbacks else text_or_na(task.get('risks'))}`",
                        f"- {text_or_na(task.get('task_id'))} rollback: `{text_or_na(task.get('rollback'))}`",
                    ]
                )
            lines.append("")
    return lines


def render_chinese_owner_preamble(
    title: str,
    project_facts: dict[str, Any],
    roadmap: dict[str, Any],
    summary: dict[str, Any],
    *,
    entry_name: str,
    focus: str,
) -> list[str]:
    project_id = text_or_na(project_facts.get("project_id"))
    current_stage = text_or_na(roadmap.get("current_stage_id"))
    current_phase = text_or_na(roadmap.get("current_phase_id"))
    current_task = text_or_na(roadmap.get("current_task_id"))
    next_gate = text_or_na(roadmap.get("next_gate_id"))
    evidence_status = text_or_na(project_facts.get("fact_level"))
    return [
        title,
        "",
        "中文优先，默认全局中文。用户可读优先。",
        "",
        "## 一句话结论",
        "",
        f"`{project_id}` 的{entry_name}先给 Owner 判断：能否继续、证据是否足够、风险在哪里、下一步做什么、出错如何回滚。{focus}",
        "",
        "## 中文瘦身原则",
        "",
        "- 本入口瘦身不是删除事实，而是把反复计算、英文键名解释和历史索引移到下方；第一屏只留下负责人当下要判断的状态、证据、风险、动作和回滚。",
        "- 后续执行者继续开发时，不应重新扫描全量治理目录；只取当前任务、下一门禁、必要证据和失败去向，避免上下文被重复材料消耗。",
        "- 需要复盘时再读取机器字段、路线图、事件、登记表和运行清单；这些材料仍是事实源，但不进入每一次小开发动作的默认输入。",
        "- 若为了变短而让负责人看不懂、让证据来源消失或让待定被写成完成，本次瘦身即视为失败，必须回滚入口或补证据。",
        "- 英文项目名、路径和命令只作定位；当英文数量变多时，必须用中文说明其业务含义、验收边界和开发影响。",
        "- 高频小任务只交付可执行中文判断；需要全量审计时再回到事实源重算，避免把全仓检查变成每次改动的固定成本。",
        "",
        "## 当前状态",
        "",
        f"- 当前阶段：`{current_stage}`；当前分段：`{current_phase}`；当前任务：`{current_task}`。",
        f"- 下一门禁：`{next_gate}`；证据状态：`{evidence_status}`；阻塞情况：`{summary['blockers']}`。",
        "",
        "## Owner 操作入口",
        "",
        "- 先读本页中文结论；继续开发时只带走当前任务、下一门禁、风险、回滚和必要证据。",
        "- 日常开发走变更范围快速门禁；完整治理计算放到计划任务或手动全量范围。",
        "",
        "## 证据与验证",
        "",
        "- 证据以仓库文件、治理事实、测试命令和运行结果为准；中文只解释事实，不替代事实。",
        "- 证据不足保持待定；中文结论和机器字段冲突时，先复核事实来源。",
        "",
        "## 风险与边界",
        "",
        "- 不把英文键名、任务编号和路径列表当成负责人结论。",
        "- 只移出重复治理计算，不删除可追溯治理真相。",
        "",
        "## 下一步",
        "",
        f"- 聚焦 `{summary['next_unique_task']}`；先补验收证据，再推进门禁。",
        "- 后续执行者必须保留中文优先和用户可读优先；新增字段放下方明细。",
        "",
        "## 回滚",
        "",
        "- 若入口误导 Owner，回滚入口文本，保留原始治理事实文件。",
        "- 若自动渲染变低可读，先修渲染器和校验器，再重渲染。",
        "",
        "## 中文验收",
        "",
        "- 第一屏能判断状态、证据、风险、下一步和回滚才合格；关键词堆叠不合格。",
        "- 中文判断在前，治理事实在后，验证命令可复核；不能为省上下文删除事实来源。",
        "",
        "## 摘要",
        "",
        f"- 项目 ID：`{project_id}`",
        f"- 当前阶段：`{current_stage}`",
        f"- 当前分段：`{current_phase}`",
        f"- 当前任务：`{current_task}`",
        f"- 阻塞情况：`{summary['blockers']}`",
        f"- 下一门禁：`{next_gate}`",
        f"- 下一唯一任务：`{summary['next_unique_task']}`",
        f"- 证据状态：`{evidence_status}`",
    ]


def render_feature_list(project_facts: dict[str, Any], roadmap: dict[str, Any]) -> str:
    features = [item for item in governance.as_list(project_facts.get("features")) if isinstance(item, dict)]
    evidence = [item for item in governance.as_list(project_facts.get("evidence_refs")) if isinstance(item, dict)]
    totals = roadmap_totals(roadmap)
    summary = roadmap_fact_summary(project_facts, roadmap)
    project_root = ROOT / str(project_facts.get("project_id") or "")
    v72 = load_adp_v7_2_current(project_root)
    lock = load_adp_v7_1_lock(project_root)
    lines = [
        "# 功能清单",
        "",
        "## 摘要",
        "",
        f"- 项目 ID：`{text_or_na(project_facts.get('project_id'))}`",
        f"- 产品版本：`{text_or_na(project_facts.get('version'))}`",
        f"- 当前阶段：`{text_or_na(roadmap.get('current_stage_id'))}`",
        f"- 当前分段：`{text_or_na(roadmap.get('current_phase_id'))}`",
        f"- 当前任务：`{text_or_na(roadmap.get('current_task_id'))}`",
        f"- 完成进度：`{pct(totals['completed'], totals['total'])}`",
        f"- 能力数量：`{len(features)}`",
        f"- 阻塞情况：`{summary['blockers']}`",
        f"- 下一门禁：`{text_or_na(roadmap.get('next_gate_id'))}`",
        f"- 下一唯一任务：`{summary['next_unique_task']}`",
        f"- 证据引用数：`{summary['project_evidence_ref_count']}`",
        f"- 测试命令数：`{summary['roadmap_test_command_count']}`",
        f"- 门禁数量：`{summary['roadmap_gate_count']}`",
        f"- 证据状态：`{text_or_na(project_facts.get('fact_level'))}`",
        "",
        "## 功能概览",
        "",
        "| 功能 ID | 名称 | 状态 | 说明 | 证据等级 |",
        "|---|---|---|---|---|",
    ]
    lines[2:2] = render_chinese_owner_preamble(
        "# 功能清单",
        project_facts,
        roadmap,
        summary,
        entry_name="功能清单",
        focus="功能判断要先回答这个项目现在能提供什么能力、这些能力是否已有证据支撑，以及哪些能力仍然只是待验证计划。",
    )[2:-10]
    for feature in features:
        lines.append(
            f"| {text_or_na(feature.get('feature_id'))} | {text_or_na(feature.get('name'))} | {text_or_na(feature.get('status'))} | {text_or_na(feature.get('description'))} | {text_or_na(feature.get('fact_level'))} |"
        )
    lines.extend(v7_2_current_summary_lines(v72))
    lines.extend(v7_1_summary_lines(lock))
    lines.extend(["", "## 证据", "", "| 证据 ID | 类型 | 引用 | 事实等级 |", "|---|---|---|---|"])
    for item in evidence:
        lines.append(
            f"| {text_or_na(item.get('evidence_id'))} | {text_or_na(item.get('kind'))} | {text_or_na(item.get('ref'))} | {text_or_na(item.get('fact_level'))} |"
        )
    lines.extend(["", "<!-- machine_tokens: project_id current_stage current_task evidence_status -->"])
    return "\n".join(lines).rstrip() + "\n"


def render_development_record(project_facts: dict[str, Any], roadmap: dict[str, Any], events: list[dict[str, Any]]) -> str:
    ensure_product_roadmap(roadmap, target="project development record")
    totals = roadmap_totals(roadmap)
    summary = roadmap_fact_summary(project_facts, roadmap)
    project_root = ROOT / str(project_facts.get("project_id") or "")
    v72 = load_adp_v7_2_current(project_root)
    lock = load_adp_v7_1_lock(project_root)
    lines = [
        "# 开发记录",
        "",
        "## 摘要",
        "",
        f"- 项目 ID：`{text_or_na(project_facts.get('project_id'))}`",
        f"- 产品版本：`{text_or_na(project_facts.get('version'))}`",
        f"- 当前阶段：`{text_or_na(roadmap.get('current_stage_id'))}`",
        f"- 当前分段：`{text_or_na(roadmap.get('current_phase_id'))}`",
        f"- 当前任务：`{text_or_na(roadmap.get('current_task_id'))}`",
        f"- 总工时：`{totals['total']:.2f}`",
        f"- 已完成工时：`{totals['completed']:.2f}`",
        f"- 完成进度：`{pct(totals['completed'], totals['total'])}`",
        f"- 阻塞情况：`{summary['blockers']}`",
        f"- 下一门禁：`{text_or_na(roadmap.get('next_gate_id'))}`",
        f"- 下一唯一任务：`{summary['next_unique_task']}`",
        f"- 路线图类型：`{roadmap_kind(roadmap)}`",
        f"- 任务数量：`{summary['roadmap_task_count']}`",
        f"- 门禁数量：`{summary['roadmap_gate_count']}`",
        f"- 验收项数量：`{summary['roadmap_acceptance_count']}`",
        f"- 测试命令数：`{summary['roadmap_test_command_count']}`",
        f"- 证据引用数：`{summary['roadmap_evidence_ref_count']}`",
        f"- 证据状态：`{text_or_na(project_facts.get('fact_level'))}`",
        "",
        "## Roadmap",
        "",
    ]
    lines[2:2] = render_chinese_owner_preamble(
        "# 开发记录",
        project_facts,
        roadmap,
        summary,
        entry_name="开发记录",
        focus="开发记录要先说明进度为什么可信、当前门禁在哪里、哪些证据已经落地、哪些阻塞仍会影响速度和质量。",
    )[2:-10]
    lines.extend(render_roadmap_body(roadmap))
    lines.extend(v7_2_current_summary_lines(v72))
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
    project_root = ROOT / str(project_facts.get("project_id") or "")
    v72 = load_adp_v7_2_current(project_root)
    lock = load_adp_v7_1_lock(project_root) or {}
    stage2 = lock.get("stage2_boundary") if isinstance(lock, dict) and isinstance(lock.get("stage2_boundary"), dict) else {}
    lines = [
        "# 模型参数文件",
        "",
        "## 摘要",
        "",
        f"- 项目 ID：`{text_or_na(project_facts.get('project_id'))}`",
        f"- 产品版本：`{text_or_na(project_facts.get('version'))}`",
        f"- 当前阶段：`{text_or_na(roadmap.get('current_stage_id'))}`",
        f"- 当前分段：`{text_or_na(roadmap.get('current_phase_id'))}`",
        f"- 当前任务：`{text_or_na(roadmap.get('current_task_id'))}`",
        f"- 当前模型数：`{active_count(models)}`",
        f"- 当前公式数：`{active_count(formulas)}`",
        f"- 当前参数数：`{active_count(parameters)}`",
        f"- 阻塞情况：`{summary['blockers']}`",
        f"- 下一门禁：`{text_or_na(roadmap.get('next_gate_id'))}`",
        f"- 下一唯一任务：`{summary['next_unique_task']}`",
        f"- 证据引用数：`{summary['project_evidence_ref_count']}`",
        f"- 测试命令数：`{summary['roadmap_test_command_count']}`",
        f"- 门禁数量：`{summary['roadmap_gate_count']}`",
        f"- 证据状态：`{text_or_na(project_facts.get('fact_level'))}`",
    ]
    lines[2:2] = render_chinese_owner_preamble(
        "# 模型参数文件",
        project_facts,
        roadmap,
        summary,
        entry_name="模型参数文件",
        focus="模型参数入口要先说明当前模型、公式和参数是否可用于决策，哪些值来自证据，哪些值仍需要复核或补充验证。",
    )[2:-10]
    lines.extend(v7_2_current_summary_lines(v72))
    lines.extend(v7_1_summary_lines(lock))
    if lock:
        lines.extend(
            [
                "",
                "## V7.1 只读历史根治理说明",
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
    lines.extend(["", "<!-- machine_tokens: active_model_count active_formula_count active_parameter_count -->"])
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


def git_status_has_error(status: list[str]) -> bool:
    return any(line.startswith("git_status_error:") or line.startswith("git_status_failed:") for line in status)


def status_line_paths(line: str) -> list[str]:
    if len(line) < 4 or line.startswith(("git_status_error:", "git_status_failed:")):
        return []
    body = line[3:].strip()
    if not body:
        return []
    if " -> " in body and line[:2].strip()[:1] in {"R", "C"}:
        old, new = body.split(" -> ", 1)
        return [old.strip(), new.strip()]
    return [body]


def status_snapshot_paths(status: list[str]) -> list[str]:
    paths: list[str] = []
    seen: set[str] = set()
    for line in status:
        for path in status_line_paths(line):
            normalized = path.replace("\\", "/")
            if normalized and normalized not in seen:
                seen.add(normalized)
                paths.append(normalized)
    return paths


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def git_diff_sha256(root: Path, rel_path: str, *, cached: bool) -> tuple[str | None, str | None]:
    argv = ["git", "diff", "--no-ext-diff", "--binary"]
    if cached:
        argv.append("--cached")
    argv.extend(["--", rel_path])
    try:
        result = subprocess.run(
            argv,
            cwd=root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=5.0,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return None, f"git_diff_error:{rel_path}:{exc}"
    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace").strip() or f"exit_{result.returncode}"
        return None, f"git_diff_failed:{rel_path}:{stderr}"
    return "sha256:" + hashlib.sha256(result.stdout).hexdigest(), None


def path_fingerprint(root: Path, rel_path: str) -> tuple[dict[str, Any] | None, str | None]:
    path = root / rel_path
    try:
        exists = path.exists() or path.is_symlink()
        if not exists:
            kind = "missing"
            fingerprint: dict[str, Any] = {"path": rel_path, "kind": kind}
        elif path.is_symlink():
            fingerprint = {
                "path": rel_path,
                "kind": "symlink",
                "symlink_target": os.readlink(path),
            }
        elif path.is_file():
            fingerprint = {
                "path": rel_path,
                "kind": "file",
                "file_sha256": file_sha256(path),
            }
        elif path.is_dir():
            fingerprint = {"path": rel_path, "kind": "directory"}
        else:
            fingerprint = {"path": rel_path, "kind": "other"}
    except OSError as exc:
        return None, f"path_snapshot_error:{rel_path}:{exc}"

    worktree_hash, error = git_diff_sha256(root, rel_path, cached=False)
    if error:
        return None, error
    index_hash, error = git_diff_sha256(root, rel_path, cached=True)
    if error:
        return None, error
    fingerprint["worktree_diff_sha256"] = worktree_hash
    fingerprint["index_diff_sha256"] = index_hash
    return fingerprint, None


def worktree_status_snapshot(root: Path, status: list[str]) -> dict[str, Any]:
    status_errors = [line for line in status if line.startswith(("git_status_error:", "git_status_failed:"))]
    if status_errors:
        return {
            "schema_version": 1,
            "ok": False,
            "mode": "content_snapshot",
            "status_lines": sorted(set(status)),
            "paths": {},
            "errors": status_errors,
        }
    paths = status_snapshot_paths(status)
    if not root.exists():
        return {
            "schema_version": 1,
            "ok": True,
            "mode": "status_only_missing_root",
            "status_lines": sorted(set(status)),
            "paths": {path: {"path": path, "status_only": True} for path in paths},
            "errors": [],
        }
    fingerprints: dict[str, Any] = {}
    errors: list[str] = []
    for rel_path in paths:
        fingerprint, error = path_fingerprint(root, rel_path)
        if error:
            errors.append(error)
        elif fingerprint is not None:
            fingerprints[rel_path] = fingerprint
    return {
        "schema_version": 1,
        "ok": not errors,
        "mode": "content_snapshot",
        "status_lines": sorted(set(status)),
        "paths": fingerprints,
        "errors": errors,
    }


def ci_clean_start_required() -> bool:
    return bool(os.environ.get("GITHUB_ACTIONS") or os.environ.get("CI"))


def worktree_write_delta(
    before_status: list[str],
    after_status: list[str],
    *,
    clean_start_required: bool,
    before_snapshot: dict[str, Any] | None = None,
    after_snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    before = sorted(set(before_status))
    after = sorted(set(after_status))
    new_status = sorted(set(after) - set(before))
    resolved_status = sorted(set(before) - set(after))
    status_errors = [line for line in before + after if line.startswith(("git_status_error:", "git_status_failed:"))]
    snapshot_errors = list((before_snapshot or {}).get("errors") or []) + list((after_snapshot or {}).get("errors") or [])
    before_paths = dict((before_snapshot or {}).get("paths") or {})
    after_paths = dict((after_snapshot or {}).get("paths") or {})
    content_changed_paths = sorted(
        path
        for path in set(before_paths) | set(after_paths)
        if before_paths.get(path) != after_paths.get(path)
    )
    clean_start_ok = not clean_start_required or not before
    clean = (
        not status_errors
        and not snapshot_errors
        and clean_start_ok
        and not new_status
        and not resolved_status
        and not content_changed_paths
    )
    return {
        "schema_version": 1,
        "mode": "pre_post_content_delta",
        "clean": clean,
        "clean_start_required": clean_start_required,
        "clean_start_ok": clean_start_ok,
        "preexisting_changed_count": len(before),
        "post_changed_count": len(after),
        "new_changed_count": len(new_status),
        "resolved_changed_count": len(resolved_status),
        "content_changed_count": len(content_changed_paths),
        "preexisting_changed_files": before[:20],
        "post_changed_files": after[:20],
        "new_changed_files": new_status[:20],
        "resolved_changed_files": resolved_status[:20],
        "content_changed_files": content_changed_paths[:20],
        "status_error": bool(status_errors),
        "status_errors": status_errors[:5],
        "snapshot_error": bool(snapshot_errors),
        "snapshot_errors": snapshot_errors[:5],
    }


def legacy_zero_diff_view(delta: dict[str, Any]) -> dict[str, Any]:
    return {
        "clean": bool(delta.get("clean", False)),
        "changed_count": int(delta.get("new_changed_count", 0)) + int(delta.get("content_changed_count", 0)),
        "changed_files": (list(delta.get("new_changed_files") or []) + list(delta.get("content_changed_files") or []))[:20],
        "preexisting_changed_count": int(delta.get("preexisting_changed_count", 0)),
        "post_changed_count": int(delta.get("post_changed_count", 0)),
        "clean_start_required": bool(delta.get("clean_start_required", False)),
        "clean_start_ok": bool(delta.get("clean_start_ok", True)),
        "status_error": bool(delta.get("status_error", False)),
        "snapshot_error": bool(delta.get("snapshot_error", False)),
    }


def run_validator_capture(validate_argv: list[str], *, changed_files: list[str] | None = None) -> dict[str, Any]:
    stdout = io.StringIO()
    original_git_changed_files = governance.git_changed_files
    if changed_files is not None:
        def _fixed_changed_files(base_ref: str | None = None) -> list[str]:
            return list(changed_files)

        governance.git_changed_files = _fixed_changed_files
    try:
        with contextlib.redirect_stdout(stdout):
            exit_code = governance.main(validate_argv)
    finally:
        governance.git_changed_files = original_git_changed_files
    return {
        "argv": validate_argv,
        "exit_code": exit_code,
        "output": [line for line in stdout.getvalue().splitlines() if line.strip()],
    }


def validator_checked_project_count(validation: dict[str, Any]) -> int | None:
    for line in validation.get("output", []):
        if not isinstance(line, str) or not line.startswith("projects checked: "):
            continue
        value = line.split(": ", 1)[1].strip()
        if value == "none":
            return 0
        return len([item for item in value.split(",") if item.strip()])
    return None


def compact_error(error_code: str, message: str, *, base_ref: str = "", command: str = "") -> dict[str, Any]:
    return {
        "owner_status_zh": f"治理检查停止：{message}",
        "schema_version": 1,
        "language": "zh-CN",
        "decision": "STOP",
        "command": command,
        "error_code": error_code,
        "base_ref": base_ref,
        "base_ref_status": "unresolved" if error_code == "UNRESOLVED_BASE" else "error",
        "candidate_report_only": True,
        "rollback_or_stop_condition": "保持 legacy-authoritative；修复错误后重跑 changed-only gate。",
    }


def compact_check_plan(summary: dict[str, Any]) -> dict[str, Any]:
    check_plan = summary.get("check_plan") if isinstance(summary.get("check_plan"), dict) else {}
    return {
        "selected_project_count": int(check_plan.get("selected_project_count", 0)),
        "changed_file_count": int(check_plan.get("changed_file_count", 0)),
        "root_governance_changed": bool(check_plan.get("root_governance_changed", False)),
        "escalation_reasons": list(check_plan.get("escalation_reasons") or [])[:5],
        "next_action_zh": check_plan.get("next_action_zh", "查看 full_evidence_ref。"),
    }


def evidence_directory(root: Path = ROOT) -> tuple[Path, str]:
    configured = os.environ.get("GOVERNANCE_EVIDENCE_DIR")
    if configured:
        return Path(configured), "ci_artifact" if os.environ.get("GITHUB_ACTIONS") else "configured"
    return root / ".git" / "codex-review" / "lean-governance", "local_only"


def write_full_evidence(summary: dict[str, Any], *, root: Path = ROOT) -> dict[str, Any]:
    evidence_dir, retention_scope = evidence_directory(root)
    payload = json.dumps(summary, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    evidence_dir.mkdir(parents=True, exist_ok=True)
    path = evidence_dir / f"ci-{int(time.time() * 1000)}-{os.getpid()}-{digest[:12]}-{uuid.uuid4().hex[:8]}.json"
    path.write_bytes(payload + b"\n")
    artifact = os.environ.get("GOVERNANCE_EVIDENCE_ARTIFACT", "")
    return {
        "evidence_id": digest[:12],
        "path_or_artifact_ref": artifact or str(path),
        "sha256": f"sha256:{digest}",
        "schema_version": summary.get("schema_version", 1),
        "retention_scope": retention_scope,
    }


def compact_ci_summary(summary: dict[str, Any], exit_code: int, full_evidence_ref: dict[str, Any]) -> dict[str, Any]:
    changed_scope = summary.get("changed_scope") if isinstance(summary.get("changed_scope"), dict) else {}
    validation = summary.get("validation") if isinstance(summary.get("validation"), dict) else {}
    zero_diff = summary.get("zero_diff") if isinstance(summary.get("zero_diff"), dict) else {}
    selector = summary.get("selector_parity") if isinstance(summary.get("selector_parity"), dict) else {}
    decision = "SHIP" if exit_code == 0 else "STOP"
    owner_status = "治理检查通过：legacy 结果仍为唯一权威，candidate 仅报告。" if exit_code == 0 else "治理检查停止：legacy 或候选保护发现阻塞。"
    evidence_ref = full_evidence_ref.get("path_or_artifact_ref", "")
    return {
        "owner_status_zh": owner_status,
        "schema_version": 1,
        "language": "zh-CN",
        "decision": decision,
        "command": "ci",
        "scope": summary.get("scope", "changed-only"),
        "legacy_exit_code": int(validation.get("exit_code", exit_code)),
        "process_exit_code": exit_code,
        "candidate_report_only": True,
        "base_ref_status": changed_scope.get("base_ref_status", "resolved"),
        "changed_file_count": len(changed_scope.get("changed_files") or []),
        "selected_project_count": int(changed_scope.get("selected_project_count", 0)),
        "validation_checked_project_count": selector.get("validation_checked_project_count"),
        "zero_tracked_write": bool(zero_diff.get("clean", False)),
        "stable_summary_hash": summary.get("stable_summary_hash", ""),
        "check_plan": compact_check_plan(summary),
        "timing_telemetry": summary.get("timing_telemetry", {}),
        "output_telemetry": summary.get("output_telemetry", {}),
        "acceptance_ids": ["M1-S2PC-PRE-S3", "S3PAT01", "S3PAT02", "S3PBT01", "S3PBT02", "S3PBT03", "S3PBT04"],
        "evidence_refs": [evidence_ref] if evidence_ref else [],
        "rollback_or_stop_condition": (
            "无 tracked 回滚；full evidence 见 full_evidence_ref。"
            if exit_code == 0
            else "停止推进；查看 full_evidence_ref 后修复阻塞再重跑。"
        ),
        "full_evidence_ref": full_evidence_ref,
    }


def compact_json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=False, separators=(",", ":")).encode("utf-8")


def attach_compact_stdout_bytes(payload: dict[str, Any]) -> dict[str, Any]:
    output_telemetry = payload.setdefault("output_telemetry", {})
    if not isinstance(output_telemetry, dict):
        output_telemetry = {}
        payload["output_telemetry"] = output_telemetry
    for _ in range(3):
        output_telemetry["compact_stdout_bytes"] = len(compact_json_bytes(payload))
    return payload


def stable_ci_projection(summary: dict[str, Any]) -> dict[str, Any]:
    changed_scope = summary.get("changed_scope") if isinstance(summary.get("changed_scope"), dict) else {}
    check_render = summary.get("check_render") if isinstance(summary.get("check_render"), dict) else {}
    check_render_report = check_render.get("report") if isinstance(check_render.get("report"), dict) else {}
    zero_write_delta = summary.get("zero_write_delta") if isinstance(summary.get("zero_write_delta"), dict) else {}
    validation = summary.get("validation") if isinstance(summary.get("validation"), dict) else {}
    return {
        "schema_version": summary.get("schema_version", 1),
        "command": summary.get("command", ""),
        "scope": summary.get("scope", ""),
        "base_ref": summary.get("base_ref", ""),
        "changed_scope": {
            "base_ref_status": changed_scope.get("base_ref_status", ""),
            "error_code": changed_scope.get("error_code", ""),
            "root_governance_changed": bool(changed_scope.get("root_governance_changed", False)),
            "unknown_changed_files": list(changed_scope.get("unknown_changed_files") or []),
            "full_scope_required": bool(changed_scope.get("full_scope_required", False)),
            "changed_files": list(changed_scope.get("changed_files") or []),
            "selected_project_count": int(changed_scope.get("selected_project_count", 0)),
            "selected_projects": list(changed_scope.get("selected_projects") or []),
        },
        "check_plan": summary.get("check_plan", {}),
        "validation": {
            "argv": list(validation.get("argv") or []),
            "exit_code": int(validation.get("exit_code", 1)),
            "checked_project_count": validator_checked_project_count(validation),
        },
        "check_render": {
            "checked_count": int(check_render.get("checked_count", 0)),
            "skipped_count": int(check_render.get("skipped_count", 0)),
            "skipped": list(check_render.get("skipped") or []),
            "report": {
                "drift_count": int(check_render_report.get("drift_count", 0)),
                "reference_issue_count": int(check_render_report.get("reference_issue_count", 0)),
                "error_count": int(check_render_report.get("error_count", 0)),
                "deferred_count": int(check_render_report.get("deferred_count", 0)),
                "blocking_required_exit": bool(check_render_report.get("blocking_required_exit", False)),
            },
        },
        "selector_parity": summary.get("selector_parity", {}),
        "zero_write_delta": {
            "clean": bool(zero_write_delta.get("clean", False)),
            "clean_start_required": bool(zero_write_delta.get("clean_start_required", False)),
            "clean_start_ok": bool(zero_write_delta.get("clean_start_ok", True)),
            "preexisting_changed_count": int(zero_write_delta.get("preexisting_changed_count", 0)),
            "new_changed_count": int(zero_write_delta.get("new_changed_count", 0)),
            "status_error": bool(zero_write_delta.get("status_error", False)),
        },
    }


def stable_ci_summary_hash(summary: dict[str, Any]) -> str:
    payload = json.dumps(
        stable_ci_projection(summary),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def with_stable_summary_hash(summary: dict[str, Any]) -> dict[str, Any]:
    summary["stable_summary_hash"] = stable_ci_summary_hash(summary)
    return summary


def build_check_plan(
    scope: dict[str, Any],
    validate_argv: list[str],
    *,
    selected_project_count: int,
    total_project_count: int,
) -> dict[str, Any]:
    changed_files = list(scope.get("changed_files") or [])
    escalation_reasons: list[str] = []
    if scope.get("root_governance_changed"):
        escalation_reasons.append("root_governance_fanout")
    if scope.get("unknown_changed_files"):
        escalation_reasons.append("unknown_path_full_scope")
    if scope.get("base_ref_status") != "resolved":
        escalation_reasons.append("base_ref_unresolved")
    if not changed_files:
        escalation_reasons.append("empty_diff")
    if int(scope.get("selected_required_project_count", selected_project_count)) < int(
        scope.get("required_project_count", selected_project_count)
    ):
        escalation_reasons.append("required_scope_gap")
    if not escalation_reasons:
        escalation_reasons.append("changed_project_scope")
    selected_projects = [
        {
            "project_id": str(project.get("project_id") or ""),
            "path": str(project.get("path") or ""),
            "ci_mode": str(project.get("ci_mode") or ""),
        }
        for project in scope.get("selected_projects", [])
    ]
    return {
        "schema_version": 1,
        "mode": "candidate-shadow-report-only",
        "legacy_authoritative": True,
        "candidate_report_only": True,
        "changed_file_count": len(changed_files),
        "selected_project_count": selected_project_count,
        "total_project_count": total_project_count,
        "root_governance_changed": bool(scope.get("root_governance_changed", False)),
        "unknown_changed_files": list(scope.get("unknown_changed_files") or []),
        "full_scope_required": bool(scope.get("full_scope_required", False)),
        "escalation_reasons": escalation_reasons,
        "commands": [
            {"name": "validate", "argv": validate_argv},
            {"name": "check-render", "project_count": selected_project_count},
        ],
        "selected_projects": selected_projects,
        "next_action_zh": "失败时先查看 full_evidence_ref；候选计划只报告，不替代 legacy 结果。",
    }


def run_changed_only_ci(base_ref: str | None = None, *, root: Path = ROOT, projects_file: Path = PROJECTS_FILE) -> tuple[int, dict[str, Any]]:
    started = time.perf_counter()
    timings: dict[str, float] = {}
    timing_start = time.perf_counter()
    baseline = build_baseline(root, projects_file)
    timings["baseline_seconds"] = round(time.perf_counter() - timing_start, 3)
    clean_start_required = ci_clean_start_required()
    before_status = git_status_porcelain(root)
    before_snapshot = worktree_status_snapshot(root, before_status)
    if git_status_has_error(before_status) or (clean_start_required and before_status):
        after_status = git_status_porcelain(root)
        after_snapshot = worktree_status_snapshot(root, after_status)
        zero_write_delta = worktree_write_delta(
            before_status,
            after_status,
            clean_start_required=clean_start_required,
            before_snapshot=before_snapshot,
            after_snapshot=after_snapshot,
        )
        status_message = (
            "git status failed; cannot prove read-only governance run"
            if git_status_has_error(before_status)
            else "CI clean-start required but repository was dirty before governance run"
        )
        summary = {
            "schema_version": 1,
            "command": "ci",
            "scope": "changed-only",
            "base_ref": base_ref or "",
            "write": False,
            "changed_scope": {
                "schema_version": 1,
                "command": "changed-scope",
                "base_ref": base_ref or "",
                "base_ref_status": "blocked",
                "error_code": "GIT_STATUS_FAILED" if git_status_has_error(before_status) else "DIRTY_CI_CLEAN_START",
                "error": status_message,
            },
            "validation": {"argv": [], "exit_code": 1, "output": [status_message]},
            "check_render": {"checked": [], "checked_count": 0, "skipped": [], "skipped_count": 0},
            "selector_parity": {
                "selected_project_count": 0,
                "validation_checked_project_count": None,
                "matches": False,
            },
            "check_plan": {
                "schema_version": 1,
                "mode": "candidate-shadow-report-only",
                "legacy_authoritative": True,
                "candidate_report_only": True,
                "changed_file_count": 0,
                "selected_project_count": 0,
                "total_project_count": baseline["totals"]["projects"],
                "root_governance_changed": False,
                "escalation_reasons": ["git_status_failed" if git_status_has_error(before_status) else "dirty_ci_clean_start"],
                "commands": [],
                "selected_projects": [],
                "next_action_zh": "修复 Git 状态后重跑；无法证明零写入时必须停止。",
            },
            "budget_telemetry": {
                "schema_version": 1,
                "mode": "changed-only-fast-gate",
                "unit": "project-scope-proxy",
                "selected_project_count": 0,
                "total_project_count": baseline["totals"]["projects"],
                "full_project_scan_avoided_count": 0,
                "semantic_scope": "changed-only",
                "write": False,
                "full_governance_location": "schedule_or_workflow_dispatch_all",
            },
            "zero_write_delta": zero_write_delta,
            "zero_diff": legacy_zero_diff_view(zero_write_delta),
            "timing_telemetry": {**timings, "total_seconds": round(time.perf_counter() - started, 3)},
            "output_telemetry": {"validator_output_line_count": 1, "validator_stdout_bytes": len(status_message.encode("utf-8"))},
            "duration_seconds": round(time.perf_counter() - started, 3),
        }
        return 1, with_stable_summary_hash(summary)
    try:
        timing_start = time.perf_counter()
        scope = build_changed_scope(base_ref, root, projects_file)
        timings["changed_scope_seconds"] = round(time.perf_counter() - timing_start, 3)
    except governance.GovernanceDiffError as exc:
        after_status = git_status_porcelain(root)
        after_snapshot = worktree_status_snapshot(root, after_status)
        zero_write_delta = worktree_write_delta(
            before_status,
            after_status,
            clean_start_required=clean_start_required,
            before_snapshot=before_snapshot,
            after_snapshot=after_snapshot,
        )
        summary = {
            "schema_version": 1,
            "command": "ci",
            "scope": "changed-only",
            "base_ref": base_ref or "",
            "write": False,
            "changed_scope": {
                "schema_version": 1,
                "command": "changed-scope",
                "base_ref": exc.base_ref or base_ref or "",
                "base_ref_status": "unresolved" if exc.error_code == "UNRESOLVED_BASE" else "error",
                "error_code": exc.error_code,
                "error": str(exc),
            },
            "validation": {"argv": [], "exit_code": 1, "output": [str(exc)]},
            "check_render": {"checked": [], "checked_count": 0, "skipped": [], "skipped_count": 0},
            "budget_telemetry": {
                "schema_version": 1,
                "mode": "changed-only-fast-gate",
                "unit": "project-scope-proxy",
                "selected_project_count": 0,
                "total_project_count": baseline["totals"]["projects"],
                "full_project_scan_avoided_count": 0,
                "semantic_scope": "changed-only",
                "write": False,
                "full_governance_location": "schedule_or_workflow_dispatch_all",
            },
            "selector_parity": {
                "selected_project_count": 0,
                "validation_checked_project_count": None,
                "matches": False,
            },
            "check_plan": {
                "schema_version": 1,
                "mode": "candidate-shadow-report-only",
                "legacy_authoritative": True,
                "candidate_report_only": True,
                "changed_file_count": 0,
                "selected_project_count": 0,
                "total_project_count": baseline["totals"]["projects"],
                "root_governance_changed": False,
                "escalation_reasons": ["base_ref_unresolved"],
                "commands": [],
                "selected_projects": [],
                "next_action_zh": "修复 base-ref 后重跑；diff 不可信时必须 fail-closed。",
            },
            "zero_write_delta": zero_write_delta,
            "zero_diff": legacy_zero_diff_view(zero_write_delta),
            "timing_telemetry": {**timings, "changed_scope_seconds": round(time.perf_counter() - started, 3), "total_seconds": round(time.perf_counter() - started, 3)},
            "output_telemetry": {"validator_output_line_count": 1, "validator_stdout_bytes": len(str(exc).encode("utf-8"))},
            "duration_seconds": round(time.perf_counter() - started, 3),
        }
        return 1, with_stable_summary_hash(summary)
    validate_argv = ["--changed-only", "--enforce-sync", "--semantic"]
    if base_ref:
        validate_argv.extend(["--base-ref", base_ref])
    timing_start = time.perf_counter()
    validation = run_validator_capture(validate_argv, changed_files=list(scope.get("changed_files") or []))
    timings["validation_seconds"] = round(time.perf_counter() - timing_start, 3)

    selected_project_count = int(scope.get("selected_project_count", len(scope["selected_projects"])))
    total_project_count = int(scope.get("total_project_count", baseline["totals"]["projects"]))
    defer_check_render = bool(scope.get("root_governance_changed") or scope.get("unknown_changed_files")) and selected_project_count > 1
    timing_start = time.perf_counter()
    check_render_results: list[dict[str, Any]] = []
    check_render_skipped: list[dict[str, str]] = []
    check_render_failed = False
    for project in scope["selected_projects"]:
        project_id = str(project.get("project_id") or "")
        project_path = str(project.get("path") or "").replace("\\", "/").rstrip("/")
        project_root = root / project_path
        if defer_check_render:
            check_render_skipped.append(
                {
                    "project_id": project_id,
                    "path": project_path,
                    "reason": "deferred_root_or_unknown_fanout",
                }
            )
            continue
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
    timings["check_render_seconds"] = round(time.perf_counter() - timing_start, 3)

    after_status = git_status_porcelain(root)
    after_snapshot = worktree_status_snapshot(root, after_status)
    zero_write_delta = worktree_write_delta(
        before_status,
        after_status,
        clean_start_required=clean_start_required,
        before_snapshot=before_snapshot,
        after_snapshot=after_snapshot,
    )
    validation_checked_project_count = validator_checked_project_count(validation)
    selector_matches = validation_checked_project_count is None or validation_checked_project_count == selected_project_count
    check_plan = build_check_plan(
        scope,
        validate_argv,
        selected_project_count=selected_project_count,
        total_project_count=total_project_count,
    )
    validation_stdout = "\n".join(str(line) for line in validation.get("output", []))
    check_render_report = {
        "report_only": True,
        "drift_count": sum(int(item.get("drift_count", 0)) for item in check_render_results),
        "reference_issue_count": sum(int(item.get("reference_issue_count", 0)) for item in check_render_results),
        "error_count": len([item for item in check_render_results if item.get("error")]),
        "deferred_count": len(
            [item for item in check_render_skipped if item.get("reason") == "deferred_root_or_unknown_fanout"]
        ),
        "blocking_required_exit": False,
    }
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
        "check_plan": check_plan,
        "validation": validation,
        "check_render": {
            "checked": check_render_results,
            "checked_count": len(check_render_results),
            "skipped": check_render_skipped,
            "skipped_count": len(check_render_skipped),
            "report": check_render_report,
        },
        "selector_parity": {
            "selected_project_count": selected_project_count,
            "validation_checked_project_count": validation_checked_project_count,
            "matches": selector_matches,
        },
        "budget_telemetry": {
            "schema_version": 1,
            "mode": "changed-only-fast-gate",
            "unit": "project-scope-proxy",
            "selected_project_count": selected_project_count,
            "validation_checked_project_count": validation_checked_project_count,
            "total_project_count": total_project_count,
            "full_project_scan_avoided_count": max(total_project_count - selected_project_count, 0),
            "semantic_scope": "changed-only",
            "check_render_checked_count": len(check_render_results),
            "check_render_skipped_count": len(check_render_skipped),
            "write": False,
            "full_governance_location": "schedule_or_workflow_dispatch_all",
        },
        "candidate_shadow_comparison": {
            "schema_version": 1,
            "legacy_exit_code": int(validation.get("exit_code", 1)),
            "candidate_report_only": True,
            "selector_parity_matches": selector_matches,
            "zero_write_delta_clean": bool(zero_write_delta.get("clean", False)),
            "required_exit_code_sources": ["legacy_validation", "read_only_guard", "selector_parity_guard"],
            "differences_report_only": (
                ["check_render_drift_or_reference_issue"] if check_render_failed else []
            ),
        },
        "zero_write_delta": zero_write_delta,
        "zero_diff": legacy_zero_diff_view(zero_write_delta),
        "timing_telemetry": {**timings, "total_seconds": round(time.perf_counter() - started, 3)},
        "output_telemetry": {
            "validator_output_line_count": len(validation.get("output", [])),
            "validator_stdout_bytes": len(validation_stdout.encode("utf-8")),
        },
        "duration_seconds": round(time.perf_counter() - started, 3),
    }
    exit_code = (
        0
        if validation["exit_code"] == 0
        and zero_write_delta.get("clean", False)
        and selector_matches
        else 1
    )
    return exit_code, with_stable_summary_hash(summary)


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
    selection = governance.changed_scope_selection(config, changed)
    selected = list(selection["projects"])
    return {
        "schema_version": 1,
        "command": "changed-scope",
        "base_ref": base_ref or "",
        "base_ref_status": "resolved",
        "changed_files": changed,
        "root_governance_changed": bool(selection["root_governance_changed"]),
        "unknown_changed_files": list(selection["unknown_changed_files"]),
        "full_scope_required": bool(selection["full_scope_required"]),
        "all_projects_required": bool(selection["all_required_projects_covered"]),
        "configured_root_scope_excluded_projects": list(selection["configured_root_scope_excluded_projects"]),
        "root_scope_excluded_projects": list(selection["root_scope_excluded_projects"]),
        "root_scope_configured_excluded_required_projects": list(
            selection["root_scope_configured_excluded_required_projects"]
        ),
        "required_project_count": int(selection["required_project_count"]),
        "selected_required_project_count": int(selection["selected_required_project_count"]),
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
        try:
            summary = build_changed_scope(args.base_ref, ROOT, PROJECTS_FILE)
        except governance.GovernanceDiffError as exc:
            print(
                json.dumps(
                    compact_error(exc.error_code, str(exc), base_ref=exc.base_ref or args.base_ref or "", command="changed-scope"),
                    ensure_ascii=False,
                    sort_keys=False,
                    separators=(",", ":"),
                )
            )
            return 1
        print(json.dumps(summary, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
        return 0
    if args.command == "render":
        try:
            summary = render_registered_project(
                args.project,
                write=args.write,
                view=args.view,
                root=ROOT,
                projects_file=PROJECTS_FILE,
            )
        except ValueError as exc:
            print(
                json.dumps(
                    compact_error("UNKNOWN_PROJECT", str(exc), command="render"),
                    ensure_ascii=False,
                    sort_keys=False,
                    separators=(",", ":"),
                )
            )
            return 1
        print(json.dumps(summary, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
        return 0
    if args.command == "check-render":
        try:
            summary = check_render_registered_project(args.project, view=args.view, root=ROOT, projects_file=PROJECTS_FILE)
        except ValueError as exc:
            print(
                json.dumps(
                    compact_error("UNKNOWN_PROJECT", str(exc), command="check-render"),
                    ensure_ascii=False,
                    sort_keys=False,
                    separators=(",", ":"),
                )
            )
            return 1
        print(json.dumps(summary, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
        return 0
    if args.command == "ci":
        exit_code, summary = run_changed_only_ci(args.base_ref, root=ROOT, projects_file=PROJECTS_FILE)
        try:
            full_evidence_ref = write_full_evidence(summary, root=ROOT)
            output = compact_ci_summary(summary, exit_code, full_evidence_ref)
        except OSError as exc:
            output = compact_error("EVIDENCE_WRITE_FAILED", str(exc), command="ci")
            exit_code = 1
        output = attach_compact_stdout_bytes(output)
        print(compact_json_bytes(output).decode("utf-8"))
        return exit_code
    if args.command == "validate":
        return governance.main(build_validate_argv(args))
    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
