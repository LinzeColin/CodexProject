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
HUMAN_ENTRY_FILES = ["功能清单.md", "开发记录.md", "模型参数文件.md", "VERSION", "CHANGELOG.md"]
RENDER_VIEW_ALIASES = {
    "feature-list": "功能清单.md",
    "功能清单": "功能清单.md",
    "功能清单.md": "功能清单.md",
    "development-record": "开发记录.md",
    "开发记录": "开发记录.md",
    "开发记录.md": "开发记录.md",
    "model-parameters": "模型参数文件.md",
    "模型参数文件": "模型参数文件.md",
    "模型参数文件.md": "模型参数文件.md",
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
ORDINARY_CONTEXT_MAX_BYTES = 12 * 1024
ORDINARY_CONTEXT_MAX_FILES = 5
ORDINARY_CONTEXT_BOOTSTRAP_FILES = ("AGENTS.md", "README.md")
ORDINARY_CONTEXT_FORBIDDEN_DEFAULT_READS = (
    "scripts/lean_governance.py",
    "governance/run_manifests",
)
ORDINARY_CONTEXT_ESCALATION_TRIGGERS = (
    "T2_or_T3_risk",
    "root_governance_change",
    "release_or_production_gate",
    "manifest_or_evidence_ref",
    "project_specific_contract",
)
ADP_A020_PROJECT_PATH = "arxiv-daily-push"
ADP_A020_FAIL_CLOSED_FILES = ("AGENTS.md", "README.md")
ADP_A020_FAIL_CLOSED_PREFIXES = (
    ".codex/hooks/",
    ".github/workflows/",
    "docs/governance/",
    "governance/",
    "scripts/",
    "tests/governance/",
)
STAGE5_ACCEPTANCE_IDS = ("S5PAT01", "S5PBT01", "S5PBT02", "S5PCT01")
STAGE5_OWNER_ENTRY_FILES = ("功能清单.md", "开发记录.md", "模型参数文件.md")
STAGE5_P0_P1_FINDINGS = {
    "F-001": "根 AGENTS 与普通上下文预算已机械化验证",
    "F-002": "ADP A-020 gate 已 path-aware 且 fail-closed",
    "F-003": "zero-write / worktree 保护由 changed-only CI 和回归测试覆盖",
    "F-004": "普通路径禁止默认读取 lean_governance.py 全文和 run_manifests 全目录",
    "F-005": "MetaDatabase task id 与 QBVS identity 已修复",
    "F-006": "三中文入口保留，普通任务改走项目执行胶囊",
}
FINAL_REVIEW_STAGE_MANIFESTS = (
    {
        "stage": "S3",
        "manifest": "GOV-ROI-MINPATCH-S3-ROOT-HOTPATH-20260628.json",
        "acceptance_ids": ("S3PAT01", "S3PBT01", "S3PBT02", "S3PCT01", "S3PCT02"),
    },
    {
        "stage": "S4",
        "manifest": "GOV-ROI-MINPATCH-S4-PROJECT-INTERFACES-20260628.json",
        "acceptance_ids": ("S4PAT01", "S4PAT02", "S4PBT01", "S4PBT02", "S4PCT01"),
    },
    {
        "stage": "S5",
        "manifest": "GOV-ROI-MINPATCH-S5-ACCEPTANCE-ROI-ROLLBACK-20260628.json",
        "acceptance_ids": STAGE5_ACCEPTANCE_IDS,
    },
)
FINAL_REVIEW_ACCEPTANCE_IDS = (
    "FINAL-S3-S5-REQ-MATRIX",
    "FINAL-QUALITY-GUARDS",
    "FINAL-ROI-EVIDENCE",
    "FINAL-HANDOFF",
)
FINAL_REVIEW_PROJECT_CAPSULES = (
    "PFI",
    "arxiv-daily-push",
    "Alpha",
    "FIFA",
    "OpMe_System",
    "OpenAIDatabase",
    "Serenity-Alipay",
    "whkmSalary",
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


def ordinary_context_contract(root: Path = ROOT) -> dict[str, Any]:
    files = [file_state(root, rel_path) for rel_path in ORDINARY_CONTEXT_BOOTSTRAP_FILES]
    total_bytes = sum(int(item.get("bytes", 0)) for item in files)
    return {
        "schema_version": 1,
        "scope": "ordinary_t0_t1_initial_governance_context",
        "max_files": ORDINARY_CONTEXT_MAX_FILES,
        "max_bytes": ORDINARY_CONTEXT_MAX_BYTES,
        "default_files": files,
        "default_file_count": len(files),
        "default_total_bytes": total_bytes,
        "within_budget": len(files) <= ORDINARY_CONTEXT_MAX_FILES and total_bytes <= ORDINARY_CONTEXT_MAX_BYTES,
        "forbidden_default_reads": list(ORDINARY_CONTEXT_FORBIDDEN_DEFAULT_READS),
        "escalation_triggers": list(ORDINARY_CONTEXT_ESCALATION_TRIGGERS),
        "rule": "Compact is a read route for ordinary T0/T1 work, not a source of truth.",
    }


def text_or_na(value: Any) -> str:
    if value is None or value == "":
        return "NOT_APPLICABLE"
    if isinstance(value, list):
        return ", ".join(text_or_na(item) for item in value) if value else "NOT_APPLICABLE"
    return str(value)


def display_name_summary_lines(project_facts: dict[str, Any]) -> list[str]:
    display_name = str(project_facts.get("display_name") or "").strip()
    return [f"- display_name: `{text_or_na(display_name)}`"] if display_name else []


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
                f"- stop_conditions: `{text_or_na(stage.get('stop_conditions'))}`",
                f"- stop_gate: `{text_or_na(stage_gate.get('gate_id'))}`",
                f"- stop_gate_pass_criteria: `{stop_gate_field(stage_gate, 'pass_criteria', 'pass_conditions') if use_contextual_fallbacks else text_or_na(stage_gate.get('pass_criteria'))}`",
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
                    f"- stop_conditions: `{text_or_na(phase.get('stop_conditions'))}`",
                    f"- stop_gate: `{text_or_na(phase_gate.get('gate_id'))}`",
                    f"- stop_gate_pass_criteria: `{stop_gate_field(phase_gate, 'pass_criteria', 'pass_conditions') if use_contextual_fallbacks else text_or_na(phase_gate.get('pass_criteria'))}`",
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
        f"- project_id: `{text_or_na(project_facts.get('project_id'))}`",
        *display_name_summary_lines(project_facts),
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
    lines.extend(v7_2_current_summary_lines(v72))
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
    project_root = ROOT / str(project_facts.get("project_id") or "")
    v72 = load_adp_v7_2_current(project_root)
    lock = load_adp_v7_1_lock(project_root)
    lines = [
        "# 开发记录",
        "",
        "## 摘要",
        "",
        f"- project_id: `{text_or_na(project_facts.get('project_id'))}`",
        *display_name_summary_lines(project_facts),
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
        f"- project_id: `{text_or_na(project_facts.get('project_id'))}`",
        *display_name_summary_lines(project_facts),
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
    if str(project_facts.get("project_id") or "") == "arxiv-daily-push":
        lines.extend(
            [
                "",
                "## 评分和排序标准",
                "",
                "| 项目 | 当前口径 |",
                "|---|---|",
                "| 模型名称 | ROI 候选排序 |",
                "| 当前用户中心分数来源 | 历史账本分数读取 [CONTENT_LEDGER.csv](docs/owner/CONTENT_LEDGER.csv) 的 `current_score`；后续每日运行新候选使用 `adp-roi-semantic-rubric-v2` 生成六因子明细 |",
                "| 数据源与板块健康 | [数据源与板块健康](用户中心/数据源与板块健康.md) 是来源、板块、生产启用状态和影子来源边界的用户可读入口；来源或板块新增、删除、重命名、启用、停用时必须同步该页和相关测试 |",
                "| 实现入口 | [global_scan.py](src/arxiv_daily_push/global_scan.py) 的 `ROI_COMPONENT_WEIGHTS`、`ROI_SEMANTIC_RUBRIC`、`RUBRIC_KEYWORD_HIT_WEIGHT`、`_roi_signals`、`_candidate_from_source_item` |",
                "| 公式 | `roi_total_score = 相关性信号 x 15 + 学习价值信号 x 20 + 经济转化率信号 x 25 + ROI信号 x 20 + 跨学科价值信号 x 10 + 可解释性信号 x 10`；用户可读表头写成 15% / 20% / 25% / 10%，表示该因子占总分权重 |",
                "| 因子权重 | 相关性 15%；学习价值 20%；经济转化率 25%；ROI 20%；跨学科价值 10%；可解释性 10%；总和 100% |",
                "| 公开语义评分 rubric | 相关性看是否服务 ADP 关注的 AI agent、模型、决策、控制、风险、金融、市场、政策、仿真或统计主题；学习价值看方法、算法、数据集、基准、评估、理论或综述价值；经济转化率看成本、效率、自动化、金融、交易、组合、风险、隐私、安全、供应链、能源或健康等可转化场景；ROI 综合经济转化率、相关性、学习价值和可解释性；跨学科价值看 arXiv 分类组覆盖；可解释性看摘要是否适合人类复述和邮件讲解 |",
                "| 命中增量 | 相关性、学习价值、经济转化率三项使用公开语义 rubric 的证据命中；每命中一个公开证据项统一增加 7%，即 `RUBRIC_KEYWORD_HIT_WEIGHT = 0.07`；不再使用旧的 8% / 7% / 9% 三套增量 |",
                "| 信号计算 | 语义 rubric 的当前实现使用标题、摘要、主分类和副分类作为公开证据；学习价值和可解释性包含摘要长度奖励；跨学科价值来自分类组覆盖；ROI 因子由经济转化率、相关性、学习价值、可解释性加权合成 |",
                "| 逐项分公式 | 每个分项贡献 = 归一化信号 x 该因子权重；前20精选必须公开每篇文章的六个分项贡献、总分和账本核对状态 |",
                "| 入选资格 | 来源项结构有效；arXiv Atom 摘要和分类可读；来源标识、标题、链接和元数据可被验证；近期已选项按任务规则去重或避重 |",
                "| 空值处理 | 缺少来源项、摘要、分类、标题或无法生成 ROI 信号时不得补分；该项必须阻断或标为明细缺失，不得只展示总分 |",
                "| 非法值处理 | 评分信号必须为 0 到 1 的数字；权重合计必须为 100；不能用比例拆分总分来伪造分项 |",
                "| 同分排序规则 | `roi_total_score` 降序；同分时按 `source_id` 升序；用户中心前20再按论文标识去重 |",
                "| 用户可见解释 | 分数用于确定性排序和追踪，不是收益承诺；“高价值”必须同时给出总分、分项贡献、公式和证据链接 |",
                "| 前20精选解释 | 用户中心前20精选读取来源账本中的总分字段，同一论文标识去重后取最高分/稳定记录；页面必须展示六因子评分明细，不代表只剩 20 条候选 |",
                "| 旧八因子口径 | [ranking.py](src/arxiv_daily_push/ranking.py) 的前沿信号、证据可靠性、新颖性、迁移价值、问题重要性、分类优先级、等待时间、多样性仍保留为历史/底层审计口径，但不能被写成当前前20总分来源 |",
                "| 治理引用 | [parameter_registry.csv](docs/governance/parameter_registry.csv) 的 `ROI_COMPONENT_WEIGHTS`；[formula_registry.yaml](docs/governance/formula_registry.yaml) 的 ROI 排序表达式；[global_scan.py](src/arxiv_daily_push/global_scan.py) 的实现 |",
                "",
                "## S2PMT02 本地恢复安全门",
                "",
                "| 项目 | 当前口径 |",
                "|---|---|",
                "| 模型 | `MOD-ADP-110` / `adp-s2pmt02-restore-path-safety-a001-v1` |",
                "| 公式 | `FORM-ADP-112` |",
                "| 参数 | `PARAM-ADP-935` through `PARAM-ADP-939` |",
                "| A-001 专用门 | `restore_path_safety_verified`：Stage 1 restore 必须阻断 relative path traversal、absolute path escape、symlink escape，并在 invalid backup restore 被阻断时保留已有目标库 bytes；finding-level 独立技术复审 verdict 为 `PASS_WITH_NO_PRODUCTION_ACCEPTANCE`，但完整 P0 关闭包、S2PMT07 final signoff、S2PLT04、最终命令和生产验收仍阻断 |",
                "| A-002 专用门 | `restore_atomic_replacement_verified`：Stage 1 backup/restore 必须覆盖 valid new-target restore、valid overwrite with previous-target backup preservation、invalid overwrite target preservation，并清理 temporary restore files；finding-level 独立技术复审 verdict 为 `PASS_WITH_NO_PRODUCTION_ACCEPTANCE`，但完整 P0 关闭包、S2PMT07 final signoff、S2PLT04、最终命令和生产验收仍阻断 |",
                "| 禁止动作 | 不执行生产恢复、不改 schema/DB migration、不改队列、不安装/启用 scheduler、不发送 SMTP、不上传 Release |",
                "| 证据入口 | [PHASE_S2PMT02_RESTORE_PATH_SAFETY_A001.md](docs/phase_records/PHASE_S2PMT02_RESTORE_PATH_SAFETY_A001.md)；[ADP-S2PMT02-RESTORE-PATH-SAFETY-A001-20260627.json](../governance/run_manifests/ADP-S2PMT02-RESTORE-PATH-SAFETY-A001-20260627.json)；[ADP-S2PMT07-A001-INDEPENDENT-TECHNICAL-REVIEW-20260627.json](../governance/run_manifests/ADP-S2PMT07-A001-INDEPENDENT-TECHNICAL-REVIEW-20260627.json)；[PHASE_S2PMT02_RESTORE_ATOMIC_REPLACEMENT_A002.md](docs/phase_records/PHASE_S2PMT02_RESTORE_ATOMIC_REPLACEMENT_A002.md)；[ADP-S2PMT02-RESTORE-ATOMIC-REPLACEMENT-A002-20260627.json](../governance/run_manifests/ADP-S2PMT02-RESTORE-ATOMIC-REPLACEMENT-A002-20260627.json)；[ADP-S2PMT07-A002-INDEPENDENT-TECHNICAL-REVIEW-20260627.json](../governance/run_manifests/ADP-S2PMT07-A002-INDEPENDENT-TECHNICAL-REVIEW-20260627.json) |",
                "",
                "## S2PMT03 本地事务发件箱与消息 ID 门",
                "",
                "| 项目 | 当前口径 |",
                "|---|---|",
                "| 模型 | `MOD-ADP-112` / `adp-s2pmt03-outbox-delivery-a003-v1` |",
                "| 公式 | `FORM-ADP-114` |",
                "| 参数 | `PARAM-ADP-945` through `PARAM-ADP-949` |",
                "| A-003 专用门 | `transactional_outbox_verified`：同 revision 消息 ID 必须稳定；内容 revision/body 变化必须换 message ID；同一 outbox row 100 次 claim 必须 1 成功 / 99 阻断；`ACCEPTED_PENDING_COMMIT` 无 provider ref 必须 fail-closed；`BLOCKED`/`SENT` 且 `retry_safe=false` 的行即使 lease 过期也不能再次 claim；provider accept ref 只能本地 finalize，不触发真实 SMTP resend；finding-level 独立技术复审 verdict 为 `PASS_WITH_NO_PRODUCTION_ACCEPTANCE`，但完整 P0 关闭包、S2PMT07 final signoff、S2PLT04、最终命令和生产验收仍阻断 |",
                "| 禁止动作 | 不发送真实 SMTP、不安装/启用 scheduler、不上传 Release、不改 public schema/DB/queue/source/ranking、不改 CURRENT/V7 合同、不关闭 P0/P1 |",
                "| 证据入口 | [PHASE_S2PMT03_OUTBOX_DELIVERY_A003.md](docs/phase_records/PHASE_S2PMT03_OUTBOX_DELIVERY_A003.md)；[ADP-S2PMT03-OUTBOX-DELIVERY-A003-20260627.json](../governance/run_manifests/ADP-S2PMT03-OUTBOX-DELIVERY-A003-20260627.json)；[ADP-S2PMT07-A003-INDEPENDENT-TECHNICAL-REVIEW-20260627.json](../governance/run_manifests/ADP-S2PMT07-A003-INDEPENDENT-TECHNICAL-REVIEW-20260627.json)；[事务发件箱与消息ID扫描](用户中心/事务发件箱与消息ID扫描.md) |",
                "",
                "## S2PMT04 本地生命周期与缓存门",
                "",
                "| 项目 | 当前口径 |",
                "|---|---|",
                "| 模型 | `MOD-ADP-097` / `adp-s2pmt04-lifecycle-cache-cleanup-v1` |",
                "| 公式 | `FORM-ADP-099` |",
                "| 参数 | `PARAM-ADP-800` / `S2PMT04_REQUIRED_GATES` |",
                "| B-001 专用门 | `install_status_trigger_uninstall_lifecycle`：自动唤醒安装链路必须覆盖安装、状态、触发探针、卸载；外部 isolated launchd proof 已记录到 S2PMT07 reconciliation manifest，finding-level 独立技术复审 verdict 为 `PASS_WITH_NO_PRODUCTION_ACCEPTANCE`，但完整 P0 关闭包、S2PMT07 final signoff、S2PLT04、最终命令和生产验收仍阻断 |",
                "| B-002 专用门 | `lifecycle_interrupt_matrix`：每个生命周期状态均覆盖 `SIGTERM` / `SIGINT` |",
                "| B-005 专用门 | `cache_low_disk_degradation` |",
                "| 中断恢复约束 | 阻断新 work claim；不改队列；不允许数据丢失、重复副作用或不可控副作用；恢复结果必须为 `no_loss_no_duplicate_uncontrolled_side_effects` |",
                "| 低磁盘判定 | `free_disk_bytes < low_disk_threshold_bytes` |",
                "| 降载动作 | 低磁盘时阻断新下载、阻断可重建缓存写入、保留 durable evidence、保持 cleanup dry-run |",
                "| 禁止动作 | 不应用删除、不删除 durable evidence、不改队列、不安装/启用 scheduler、不发送 SMTP、不上传 Release |",
                "| 证据入口 | [PHASE_S2PMT04_INSTALL_LIFECYCLE_B001.md](docs/phase_records/PHASE_S2PMT04_INSTALL_LIFECYCLE_B001.md)；[ADP-S2PMT04-INSTALL-LIFECYCLE-B001-20260627.json](../governance/run_manifests/ADP-S2PMT04-INSTALL-LIFECYCLE-B001-20260627.json)；[PHASE_S2PMT04_PROCESS_LIFECYCLE_B002.md](docs/phase_records/PHASE_S2PMT04_PROCESS_LIFECYCLE_B002.md)；[ADP-S2PMT04-PROCESS-LIFECYCLE-B002-20260627.json](../governance/run_manifests/ADP-S2PMT04-PROCESS-LIFECYCLE-B002-20260627.json)；[PHASE_S2PMT04_CACHE_LOW_DISK_B005.md](docs/phase_records/PHASE_S2PMT04_CACHE_LOW_DISK_B005.md)；[ADP-S2PMT04-CACHE-LOW-DISK-B005-20260626.json](../governance/run_manifests/ADP-S2PMT04-CACHE-LOW-DISK-B005-20260626.json) |",
                "",
                "## S2PMT05 本地重复触发竞态门",
                "",
                "| 项目 | 当前口径 |",
                "|---|---|",
                "| 模型 | `MOD-ADP-098` / `adp-s2pmt05-stress-fault-time-e2e-v1` |",
                "| 公式 | `FORM-ADP-100` |",
                "| 参数 | `PARAM-ADP-812` / `S2PMT05_REQUIRED_MAIL_PRODUCTS`; `PARAM-ADP-814` / `S2PMT05_REQUIRED_GATES` |",
                "| 新增门 | `trigger_count_at_least_100`; `actor_sources_covered`; `mail_products_covered`; `one_active_revision_per_product`; `blocked_duplicate_attempts_conserved`; `blocked_attempts_have_reason_codes`; `lease_fencing_receipts_present`; `no_scheduler_side_effects` |",
                "| B-007 判定 | 重复触发证据必须覆盖 `github_schedule`、`local_launchd`、`manual_retry`、`restart_catchup` 四类触发来源；M1-M4 每个产品各 100 次尝试，合计 400 次；每个产品仅保留 1 个 active revision；396 次重复触发以 `MAIL_KEY_ALREADY_CLAIMED` 阻断；active 和 blocked 数量守恒；active revision 必须带 `mail_key`、`lease_owner`、`fencing_token`；补充多进程 runner-boundary 证明必须覆盖 4 个本地进程、400 次观测结果、4 个 active revision、396 个 blocked duplicate、worker exit code 全 0；scheduler 安装和启用标志必须为 false |",
                "| 禁止动作 | 不安装/启用 scheduler、不触发真实补跑、不发送 SMTP、不上传 Release、不改 schema/DB/queue/source/ranking、不关闭 P0/P1 |",
                "| 证据入口 | [PHASE_S2PMT05_DUPLICATE_TRIGGER_B007.md](docs/phase_records/PHASE_S2PMT05_DUPLICATE_TRIGGER_B007.md)；[ADP-S2PMT05-DUPLICATE-TRIGGER-B007-20260627.json](../governance/run_manifests/ADP-S2PMT05-DUPLICATE-TRIGGER-B007-20260627.json)；[PHASE_S2PMT07_B007_MULTIPROCESS_RACE_EVIDENCE.md](docs/phase_records/PHASE_S2PMT07_B007_MULTIPROCESS_RACE_EVIDENCE.md)；[ADP-S2PMT07-B007-MULTIPROCESS-RACE-EVIDENCE-20260627.json](../governance/run_manifests/ADP-S2PMT07-B007-MULTIPROCESS-RACE-EVIDENCE-20260627.json) |",
                "",
                "## S2PMT05 本地 SMTP 崩溃窗口门",
                "",
                "| 项目 | 当前口径 |",
                "|---|---|",
                "| 模型 | `MOD-ADP-098` / `adp-s2pmt05-stress-fault-time-e2e-v1` |",
                "| 公式 | `FORM-ADP-100` |",
                "| 参数 | `PARAM-ADP-814` / `S2PMT05_REQUIRED_GATES` |",
                "| 新增门 | `outbox_claimed_before_smtp`; `accepted_pending_commit_reproduced`; `idempotent_message_identity_stable`; `resend_without_provider_ref_blocked`; `provider_accept_ref_required_before_resolution`; `provider_accept_ref_finalizes_without_resend`; `no_real_smtp_side_effect` |",
                "| B-008 判定 | SMTP accepted-before-local-commit 证据必须先 claim outbox，再进入 `ACCEPTED_PENDING_COMMIT`；同一内容修订的 `message_id` 必须稳定，内容修订变化时 `message_id` 必须变化；缺少 durable `provider_accept_ref` 时必须阻断重发；出现 `smtp-accept://...` provider ref 后只能本地 finalization，不能再次发送真实 SMTP；补充 fake SMTP accept-after-kill runner-boundary 证明必须覆盖无 `provider_accept_ref` 阻断、有 durable fake provider ref 后 finalization、稳定 `mail_key`/`message_id`、禁止 duplicate resend、无真实 SMTP side effect |",
                "| 禁止动作 | 不发送真实 SMTP、不安装/启用 scheduler、不触发真实补跑、不上传 Release、不改 schema/DB/queue/source/ranking、不关闭 P0/P1 |",
                "| 证据入口 | [PHASE_S2PMT05_SMTP_CRASH_WINDOW_B008.md](docs/phase_records/PHASE_S2PMT05_SMTP_CRASH_WINDOW_B008.md)；[ADP-S2PMT05-SMTP-CRASH-WINDOW-B008-20260627.json](../governance/run_manifests/ADP-S2PMT05-SMTP-CRASH-WINDOW-B008-20260627.json)；[PHASE_S2PMT07_B008_FAKE_SMTP_CRASH_WINDOW_EVIDENCE.md](docs/phase_records/PHASE_S2PMT07_B008_FAKE_SMTP_CRASH_WINDOW_EVIDENCE.md)；[ADP-S2PMT07-B008-FAKE-SMTP-CRASH-WINDOW-EVIDENCE-20260627.json](../governance/run_manifests/ADP-S2PMT07-B008-FAKE-SMTP-CRASH-WINDOW-EVIDENCE-20260627.json) |",
                "",
                "## S2PMT05 本地容量基线门",
                "",
                "| 项目 | 当前口径 |",
                "|---|---|",
                "| 模型 | `MOD-ADP-098` / `adp-s2pmt05-stress-fault-time-e2e-v1` |",
                "| 公式 | `FORM-ADP-100` |",
                "| 参数 | `PARAM-ADP-910` / `S2PMT05_CAPACITY_BASELINE_MULTIPLIERS`; `PARAM-ADP-911` / `S2PMT05_CAPACITY_BASELINE_MAX_QUEUE_AGE_SECONDS`; `PARAM-ADP-912` / `S2PMT05_CAPACITY_BASELINE_MAX_ERROR_RATE` |",
                "| 新增门 | `capacity_baseline_model`; `load_stress_spike_soak_rows_present`; `required_multipliers_present`; `queue_age_bounded_and_recoverable`; `error_rate_within_budget` |",
                "| B-006 判定 | 容量基线必须有 load/stress/spike/soak 四类行，覆盖 1x/2x/5x，记录 throughput、latency、queue age、memory、disk、error rate，队列 1800 秒内有界可恢复，错误率不超过 0.001，并保留本地 24h 加速 soak 证据 |",
                "| 禁止动作 | 不运行真实生产压测、不发送 SMTP、不安装/启用 scheduler、不上传 Release、不改 schema/DB/queue/source/ranking、不关闭 P0/P1 |",
                "| 证据入口 | [PHASE_S2PMT05_CAPACITY_BASELINE_B006.md](docs/phase_records/PHASE_S2PMT05_CAPACITY_BASELINE_B006.md)；[ADP-S2PMT05-CAPACITY-BASELINE-B006-20260627.json](../governance/run_manifests/ADP-S2PMT05-CAPACITY-BASELINE-B006-20260627.json) |",
                "",
                "## S2PMT05 本地故障注入恢复门",
                "",
                "| 项目 | 当前口径 |",
                "|---|---|",
                "| 模型 | `MOD-ADP-098` / `adp-s2pmt05-stress-fault-time-e2e-v1` |",
                "| 公式 | `FORM-ADP-100` |",
                "| 参数 | `PARAM-ADP-913` / `S2PMT05_REQUIRED_FAULTS`; `PARAM-ADP-914` / `S2PMT05_REQUIRED_FAULT_RECOVERY_STATES` |",
                "| 新增门 | `required_faults_present`; `required_recovery_states_present`; `no_partial_artifact_commit`; `corrupt_pdf_rebuilds_from_source`; `backup_faults_block_restore_or_publish` |",
                "| B-009 判定 | 故障注入必须覆盖 ENOSPC、只读目录、SQLITE_BUSY、损坏 JSON 缓存、损坏 PDF 产物、损坏备份 manifest、备份路径冲突；每类故障必须 fail-closed，保留 durable evidence，不提交半成品，并给出明确恢复状态与动作 |",
                "| 禁止动作 | 不信任损坏产物、不提交 partial artifact、不执行生产 restore、不发布冲突备份、不发送 SMTP、不安装/启用 scheduler、不上传 Release、不改 schema/DB/queue/source/ranking、不关闭 P0/P1 |",
                "| 证据入口 | [PHASE_S2PMT05_FAULT_INJECTION_B009.md](docs/phase_records/PHASE_S2PMT05_FAULT_INJECTION_B009.md)；[ADP-S2PMT05-FAULT-INJECTION-B009-20260627.json](../governance/run_manifests/ADP-S2PMT05-FAULT-INJECTION-B009-20260627.json) |",
                "",
                "## S2PMT05 本地时间策略与补跑门",
                "",
                "| 项目 | 当前口径 |",
                "|---|---|",
                "| 模型 | `MOD-ADP-098` / `adp-s2pmt05-stress-fault-time-e2e-v1` |",
                "| 公式 | `FORM-ADP-100` |",
                "| 参数 | `PARAM-ADP-915` / `S2PMT05_SCHEDULE_LOCAL_TIME`; `PARAM-ADP-916` / `S2PMT05_MISFIRE_GRACE_SECONDS`; `PARAM-ADP-917` / `S2PMT05_SLEEP_MISFIRE_HOURS`; `PARAM-ADP-918` / `S2PMT05_CATCHUP_MAX_RUNS_PER_CYCLE`; `PARAM-ADP-919` / `S2PMT05_REQUIRED_TIME_POLICY_CASES` |",
                "| 新增门 | `required_time_policy_cases_present`; `structured_schedule_policy_present`; `dst_gap_runs_after_gap`; `misfire_within_grace_runs_once`; `sleep_8h_catchup_bounded`; `ntp_backward_within_tolerance_allows`; `ntp_forward_over_tolerance_blocks`; `no_duplicate_m4_watermark` |",
                "| B-010 判定 | 时间策略必须把 Australia/Sydney 05:00 本地日程、3600 秒 misfire grace、最多 1 次补跑、DST backward fold、DST forward gap、未来 heartbeat、NTP 向后/向前跳、休眠 8 小时补跑和 M4 去重水位组成可验证矩阵 |",
                "| 禁止动作 | 不安装/启用 scheduler、不发送 SMTP、不触发真实补跑、不改 schema/DB/queue/source/ranking、不关闭 P0/P1 |",
                "| 证据入口 | [PHASE_S2PMT05_TIME_POLICY_B010.md](docs/phase_records/PHASE_S2PMT05_TIME_POLICY_B010.md)；[ADP-S2PMT05-TIME-POLICY-B010-20260627.json](../governance/run_manifests/ADP-S2PMT05-TIME-POLICY-B010-20260627.json) |",
                "",
                "## S2PMT05 本地 35 日 E2E 审计包门",
                "",
                "| 项目 | 当前口径 |",
                "|---|---|",
                "| 模型 | `MOD-ADP-098` / `adp-s2pmt05-stress-fault-time-e2e-v1` |",
                "| 公式 | `FORM-ADP-100` |",
                "| 参数 | `PARAM-ADP-808` / `S2PMT05_REPLAY_DAYS_REQUIRED`; `PARAM-ADP-812` / `S2PMT05_REQUIRED_MAIL_PRODUCTS`; `PARAM-ADP-816` / `S2PMT05_REQUIRED_E2E_SECTIONS` |",
                "| 新增门 | `audit_bundle_present`; `section_artifacts_present`; `bundle_links_reachable`; `review_action_roi_links_reachable`; `deterministic_bundle_hash_present` |",
                "| B-012 判定 | 35 日本地 E2E 证据必须覆盖每日 3+1、周报、月报、复习、行动和 ROI；每日邮件数、复习/行动/ROI 记录数必须守恒；bundle 必须有 section artifact、artifact index、link graph 和 deterministic bundle hash；review/action/ROI 链接必须可达 |",
                "| 禁止动作 | 不执行真实 35 日生产 replay、不发送 SMTP、不安装/启用 scheduler、不上传 Release、不改 schema/DB/queue/source/ranking、不关闭 P0/P1 |",
                "| 证据入口 | [PHASE_S2PMT05_E2E_B012.md](docs/phase_records/PHASE_S2PMT05_E2E_B012.md)；[ADP-S2PMT05-E2E-B012-20260627.json](../governance/run_manifests/ADP-S2PMT05-E2E-B012-20260627.json) |",
                "",
                "## S2PMT05 本地结果有效性门",
                "",
                "| 项目 | 当前口径 |",
                "|---|---|",
                "| 模型 | `MOD-ADP-098` / `adp-s2pmt05-stress-fault-time-e2e-v1` |",
                "| 公式 | `FORM-ADP-100` |",
                "| 参数 | `PARAM-ADP-813` / `S2PMT05_REQUIRED_FINDINGS`; `PARAM-ADP-814` / `S2PMT05_REQUIRED_GATES` |",
                "| 新增门 | `result_validity_semantic_evidence` |",
                "| B-013 判定 | 结果不能只通过结构存在性；必须同时具备语义对齐、Claim Ledger 引用、证据引用、机制/行动具体性、非模板输出差异和 unsupported P0 负例阻断 |",
                "| 禁止动作 | 不发送 SMTP、不安装/启用 scheduler、不上传 Release、不改 schema/DB/queue/source/ranking、不关闭 P0/P1 |",
                "| 证据入口 | [PHASE_S2PMT05_RESULT_VALIDITY_B013.md](docs/phase_records/PHASE_S2PMT05_RESULT_VALIDITY_B013.md)；[ADP-S2PMT05-RESULT-VALIDITY-B013-20260626.json](../governance/run_manifests/ADP-S2PMT05-RESULT-VALIDITY-B013-20260626.json) |",
                "",
                "## S2PMT05 本地背压优先级门",
                "",
                "| 项目 | 当前口径 |",
                "|---|---|",
                "| 模型 | `MOD-ADP-098` / `adp-s2pmt05-stress-fault-time-e2e-v1` |",
                "| 公式 | `FORM-ADP-100` |",
                "| 参数 | `PARAM-ADP-908` / `S2PMT05_BACKPRESSURE_PEAK_MULTIPLIERS`; `PARAM-ADP-909` / `S2PMT05_BACKPRESSURE_HIGH_PRIORITY_SLO_SECONDS` |",
                "| 新增门 | `covers_2x_and_5x_peak_profiles`; `high_priority_slo_met`; `low_priority_delay_or_drop_has_reasons` |",
                "| B-014 判定 | 背压证据必须覆盖 2x 和 5x 峰值；高优先级工作必须在 600 秒 SLO 内完成；低优先级延后或丢弃必须有明确原因码；durable evidence 必须保留 |",
                "| 禁止动作 | 不发送 SMTP、不安装/启用 scheduler、不上传 Release、不改 schema/DB/queue/source/ranking、不关闭 P0/P1 |",
                "| 证据入口 | [PHASE_S2PMT05_BACKPRESSURE_B014.md](docs/phase_records/PHASE_S2PMT05_BACKPRESSURE_B014.md)；[ADP-S2PMT05-BACKPRESSURE-B014-20260627.json](../governance/run_manifests/ADP-S2PMT05-BACKPRESSURE-B014-20260627.json) |",
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
        "功能清单.md": render_feature_list(project_facts, roadmap),
        "开发记录.md": render_development_record(project_facts, roadmap, events),
        "模型参数文件.md": render_model_parameters(project_facts, roadmap),
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
    project_id = str(project_facts.get("project_id") or "")
    for rel_path, expected in rendered.items():
        path = project_root / rel_path
        actual = path.read_text(encoding="utf-8") if path.exists() else ""
        if project_id == "arxiv-daily-push" and rel_path in {"功能清单.md", "开发记录.md", "模型参数文件.md"}:
            # ADP keeps these three root files owner-readable in Chinese. They
            # may intentionally differ from the compact machine render, while
            # project validators still enforce traceability.
            readable_title = Path(rel_path).stem
            if actual.startswith(f"# {readable_title}") and "## 中文速读" in actual and "## 摘要" in actual:
                continue
        if project_id == "Serenity-Alipay" and rel_path in {"功能清单.md", "开发记录.md", "模型参数文件.md"}:
            # Serenity keeps these files as owner-facing Chinese documents.
            # Code identifiers remain in English, but prose must stay Chinese.
            readable_title = Path(rel_path).stem
            if actual.startswith(f"# {readable_title}") and "## 中文速读" in actual:
                continue
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
        "acceptance_ids": ["M1-S2PC-PRE-S3", "S3PAT01", "S3PBT01", "S3PBT02", "S3PCT01", "S3PCT02"],
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


def parse_git_name_only(output: str) -> set[str]:
    return {line.strip().replace("\\", "/") for line in output.splitlines() if line.strip()}


def git_name_only(args: list[str], *, root: Path = ROOT, error_code: str = "DIFF_FAILED") -> set[str]:
    try:
        output = subprocess.check_output(
            ["git", "-c", "core.quotePath=false", *args],
            cwd=root,
            text=True,
            encoding="utf-8",
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        detail = f": {stderr}" if stderr else ""
        raise governance.GovernanceDiffError(
            error_code,
            f"Git changed-file diff failed{detail}",
        ) from exc
    return parse_git_name_only(output)


def git_content_changed_files(base_ref: str | None = None, *, root: Path = ROOT) -> list[str]:
    """Return content-level changed paths without status-only noise."""

    explicit_base = governance.explicit_base_ref(base_ref)
    changed: set[str] = set()
    if explicit_base:
        if not governance.git_ref_exists(explicit_base):
            raise governance.GovernanceDiffError(
                "UNRESOLVED_BASE",
                f"Explicit governance diff base does not resolve to a commit: {explicit_base}",
                base_ref=explicit_base,
            )
        try:
            changed.update(git_name_only(["diff", "--name-only", explicit_base, "--"], root=root))
        except governance.GovernanceDiffError as exc:
            exc.base_ref = explicit_base
            raise
    else:
        changed.update(git_name_only(["diff", "--name-only", "--"], root=root, error_code="LOCAL_DIFF_FAILED"))
        changed.update(
            git_name_only(["diff", "--cached", "--name-only", "--"], root=root, error_code="LOCAL_DIFF_FAILED")
        )
    changed.update(
        git_name_only(["ls-files", "--others", "--exclude-standard"], root=root, error_code="LOCAL_DIFF_FAILED")
    )
    return sorted(changed)


def build_changed_scope(base_ref: str | None = None, root: Path = ROOT, projects_file: Path = PROJECTS_FILE) -> dict[str, Any]:
    config = governance.load_yaml(projects_file)
    if not isinstance(config, dict):
        raise ValueError(f"{governance.rel(projects_file)} must parse to a mapping")
    changed = git_content_changed_files(base_ref, root=root)
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


def normalize_repo_path(path: str) -> str:
    normalized = str(path).replace("\\", "/").strip()
    if normalized.startswith("./"):
        normalized = normalized[2:]
    while normalized.startswith("/"):
        normalized = normalized[1:]
    return normalized


def path_is_under(path: str, prefix: str) -> bool:
    normalized = normalize_repo_path(path)
    clean_prefix = normalize_repo_path(prefix).rstrip("/")
    return normalized == clean_prefix or normalized.startswith(f"{clean_prefix}/")


def registered_project_paths(config: dict[str, Any]) -> list[str]:
    return [
        normalize_repo_path(str(project.get("path") or "")).rstrip("/")
        for project in governance.as_list(config.get("projects"))
        if isinstance(project, dict) and project.get("path")
    ]


def adp_a020_gate_decision(
    changed_files: list[str],
    *,
    config: dict[str, Any],
    base_ref: str = "",
    base_ref_status: str = "resolved",
    error_code: str = "",
) -> dict[str, Any]:
    normalized = [normalize_repo_path(path) for path in changed_files if normalize_repo_path(path)]
    decision: dict[str, Any] = {
        "schema_version": 1,
        "gate": "ADP-A020",
        "run_gate": True,
        "reason": "",
        "base_ref": base_ref,
        "base_ref_status": base_ref_status,
        "error_code": error_code,
        "changed_file_count": len(normalized),
        "changed_files": normalized[:50],
        "matched_files": [],
        "roi_telemetry": {
            "before": "fixed_run_on_pull_request_push_changed_only",
            "after": "path_aware_fail_closed",
            "ci_substep": "Run ADP supply-chain A-020 gate",
        },
    }
    if base_ref_status != "resolved":
        decision["reason"] = "diff_untrusted_fail_closed"
        return decision
    if not normalized:
        decision["reason"] = "empty_diff_fail_closed"
        return decision

    root_matches = [
        path
        for path in normalized
        if path in ADP_A020_FAIL_CLOSED_FILES
        or any(path_is_under(path, prefix) for prefix in ADP_A020_FAIL_CLOSED_PREFIXES)
    ]
    if root_matches:
        decision["reason"] = "root_governance_or_ci_changed"
        decision["matched_files"] = root_matches[:20]
        return decision

    adp_matches = [path for path in normalized if path_is_under(path, ADP_A020_PROJECT_PATH)]
    if adp_matches:
        decision["reason"] = "adp_path_changed"
        decision["matched_files"] = adp_matches[:20]
        return decision

    project_roots = registered_project_paths(config)
    unknown = [
        path
        for path in normalized
        if not any(path_is_under(path, project_root) for project_root in project_roots)
    ]
    if unknown:
        decision["reason"] = "unknown_path_fail_closed"
        decision["matched_files"] = unknown[:20]
        return decision

    decision["run_gate"] = False
    decision["reason"] = "non_adp_registered_project_only"
    return decision


def adp_a020_gate_decision_from_git(base_ref: str | None = None, *, projects_file: Path = PROJECTS_FILE) -> dict[str, Any]:
    config = governance.load_yaml(projects_file)
    if not isinstance(config, dict):
        raise ValueError(f"{governance.rel(projects_file)} must parse to a mapping")
    try:
        changed = git_content_changed_files(base_ref, root=ROOT)
    except governance.GovernanceDiffError as exc:
        return adp_a020_gate_decision(
            [],
            config=config,
            base_ref=exc.base_ref or base_ref or "",
            base_ref_status="unresolved" if exc.error_code == "UNRESOLVED_BASE" else "error",
            error_code=exc.error_code,
        )
    return adp_a020_gate_decision(changed, config=config, base_ref=base_ref or "")


def contains_cjk(text: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in text)


def normalized_text_bytes(path: Path) -> int:
    if not path.is_file():
        return 0
    return len(path.read_text(encoding="utf-8").encode("utf-8"))


def git_blob_size(root: Path, rel_path: str) -> int | None:
    result = subprocess.run(
        ["git", "cat-file", "-s", f"HEAD:{rel_path}"],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode != 0:
        return None
    try:
        return int(result.stdout.strip())
    except ValueError:
        return None


def git_commit_count_since(base_ref: str | None, *, root: Path = ROOT) -> int | None:
    if not base_ref:
        return None
    result = subprocess.run(
        ["git", "rev-list", "--count", f"{base_ref}..HEAD"],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode != 0:
        return None
    try:
        return int(result.stdout.strip())
    except ValueError:
        return None


def load_stage_manifest(root: Path, name: str) -> dict[str, Any]:
    path = root / "governance" / "run_manifests" / name
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def stage5_owner_entry_file_review(path: Path, filename: str) -> dict[str, Any]:
    exists = path.is_file()
    text = path.read_text(encoding="utf-8") if exists else ""
    first_screen = "\n".join(text.splitlines()[:40])
    contract = governance.HUMAN_ENTRY_QUALITY_CONTRACTS.get(filename, {})
    required_tokens = list(contract.get("required_tokens") or [])
    forbidden_markers = [
        marker
        for marker in governance.HUMAN_ENTRY_FORBIDDEN_MARKERS
        if marker.lower() in first_screen.lower()
    ]
    missing_tokens = [token for token in required_tokens if token not in text]
    title = str(contract.get("title") or "")
    first_line = next((line.strip() for line in text.splitlines() if line.strip()), "")
    title_ok = first_line == title if title else bool(first_line)
    actionable_tokens = [
        token
        for token in ("## 摘要", "current_task", "next_unique_task", "evidence_status", "stop_gate", "active_model_count")
        if token in first_screen or token in text[:3000]
    ]
    passed = (
        exists
        and title_ok
        and contains_cjk(first_screen)
        and not forbidden_markers
        and not missing_tokens
        and len(actionable_tokens) >= 3
    )
    return {
        "path": path.as_posix(),
        "exists": exists,
        "bytes": path.stat().st_size if exists else 0,
        "title_ok": title_ok,
        "chinese_first_screen": contains_cjk(first_screen),
        "missing_required_tokens": missing_tokens,
        "forbidden_markers": forbidden_markers,
        "actionable_token_count": len(actionable_tokens),
        "pass": passed,
    }


def stage5_owner_readability_review(root: Path, projects_file: Path) -> dict[str, Any]:
    config = governance.load_yaml(projects_file)
    projects = [project for project in governance.as_list(config.get("projects")) if isinstance(project, dict)]
    project_results: list[dict[str, Any]] = []
    validation = governance.Validation()
    for project in projects:
        scope = governance.project_scope(project)
        project_root = root / str(project.get("path") or "")
        governance.check_human_entry_quality(validation, project_root, True, scope)
        scope_errors = [issue.message for issue in validation.errors if issue.scope == scope]
        files = [
            stage5_owner_entry_file_review(project_root / filename, filename)
            for filename in STAGE5_OWNER_ENTRY_FILES
        ]
        project_results.append(
            {
                "project_id": str(project.get("project_id") or ""),
                "path": str(project.get("path") or ""),
                "file_count": len(files),
                "files": files,
                "validator_errors": scope_errors,
                "pass": not scope_errors and all(item["pass"] for item in files),
            }
        )
    failed = [item["project_id"] for item in project_results if not item["pass"]]
    return {
        "schema_version": 1,
        "mode": "owner-readable-triad-review",
        "project_count": len(project_results),
        "passed_project_count": len(project_results) - len(failed),
        "failed_projects": failed,
        "projects": project_results,
        "pass": not failed,
    }


def stage5_static_quality_guards(root: Path, ci_summary: dict[str, Any]) -> dict[str, Any]:
    workflow_text = (root / ".github" / "workflows" / "project-governance.yml").read_text(encoding="utf-8")
    agents_text = (root / "AGENTS.md").read_text(encoding="utf-8")
    hook_path = root / ".codex" / "hooks" / "governance_stop.py"
    hook_text = hook_path.read_text(encoding="utf-8") if hook_path.is_file() else ""
    shadow = ci_summary.get("candidate_shadow_comparison") if isinstance(ci_summary.get("candidate_shadow_comparison"), dict) else {}
    required_sources = set(str(item) for item in governance.as_list(shadow.get("required_exit_code_sources")))
    guards = {
        "candidate_report_only": bool(shadow.get("candidate_report_only")),
        "legacy_validation_required": "legacy_validation" in required_sources,
        "read_only_guard_required": "read_only_guard" in required_sources,
        "selector_parity_guard_required": "selector_parity_guard" in required_sources,
        "t2_t3_root_rule_preserved": all(token in agents_text for token in ("T2", "T3", "Never let ordinary")),
        "full_governance_all_scope_preserved": "Validate all registered scopes" in workflow_text
        and "validate --all --semantic --drift-report" in workflow_text,
        "changed_only_rollback_switch_present": "GOVERNANCE_ROLLBACK_LEGACY_CHANGED_ONLY" in workflow_text,
        "adp_fail_closed_preflight_present": "preflight_error_fail_closed" in workflow_text
        and "steps.adp-a020-preflight.outputs.run_gate == 'true'" in workflow_text,
        "hook_advisory_only": '"mode": "advisory"' in hook_text
        and '"write": False' in hook_text
        and "import subprocess" not in hook_text
        and "check_output" not in hook_text,
    }
    guards["pass"] = all(guards.values())
    return guards


def stage5_roi_metrics(
    *,
    root: Path,
    base_ref: str | None,
    context_contract: dict[str, Any],
    ci_summary: dict[str, Any],
    ci_exit_code: int,
    adp_decision: dict[str, Any],
    adp_non_adp_fixture: dict[str, Any],
) -> dict[str, Any]:
    changed_scope = ci_summary.get("changed_scope") if isinstance(ci_summary.get("changed_scope"), dict) else {}
    changed_files = list(changed_scope.get("changed_files") or [])
    output_telemetry = ci_summary.get("output_telemetry") if isinstance(ci_summary.get("output_telemetry"), dict) else {}
    timing = ci_summary.get("timing_telemetry") if isinstance(ci_summary.get("timing_telemetry"), dict) else {}
    compact = attach_compact_stdout_bytes(
        compact_ci_summary(
            ci_summary,
            ci_exit_code,
            {
                "path_or_artifact_ref": "stage5-audit-no-write",
                "sha256": "stage5-audit-no-write",
                "schema_version": 1,
                "retention_scope": "none",
            },
        )
    )
    compact_output = compact.get("output_telemetry") if isinstance(compact.get("output_telemetry"), dict) else {}
    stage3 = load_stage_manifest(root, "GOV-ROI-MINPATCH-S3-ROOT-HOTPATH-20260628.json")
    stage3_roi = stage3.get("roi_results") if isinstance(stage3.get("roi_results"), dict) else {}
    manifest_files = sorted(path for path in changed_files if path.startswith("governance/run_manifests/"))
    root_agents_path = root / "AGENTS.md"
    root_agents_blob_size = git_blob_size(root, "AGENTS.md")
    root_agents_normalized_bytes = normalized_text_bytes(root_agents_path)
    after = {
        "ordinary_context_file_count": int(context_contract.get("default_file_count", 0)),
        "ordinary_context_bytes": int(context_contract.get("default_total_bytes", 0)),
        "root_agents_blob_bytes": root_agents_blob_size,
        "root_agents_normalized_bytes": root_agents_normalized_bytes,
        "ci_wall_time_seconds": float(timing.get("total_seconds") or 0),
        "stdout_bytes": int(compact_output.get("compact_stdout_bytes") or output_telemetry.get("validator_stdout_bytes") or 0),
        "changed_file_count": len(changed_files),
        "adp_gate_triggered_current_diff": bool(adp_decision.get("run_gate")),
        "adp_gate_non_adp_fixture_triggered": bool(adp_non_adp_fixture.get("run_gate")),
        "changed_manifest_count": len(manifest_files),
        "changed_manifest_files": manifest_files,
        "governance_sync_commit_count_since_base": git_commit_count_since(base_ref, root=root),
    }
    thresholds = {
        "ordinary_context_max_files": ORDINARY_CONTEXT_MAX_FILES,
        "ordinary_context_max_bytes": ORDINARY_CONTEXT_MAX_BYTES,
        "root_agents_max_blob_bytes": 4096,
        "compact_stdout_max_bytes": 2048,
        "changed_only_ci_target_seconds": 30,
    }
    pass_checks = {
        "ordinary_context_within_budget": bool(context_contract.get("within_budget")),
        "root_agents_under_4kb_blob": root_agents_blob_size is not None and root_agents_blob_size <= 4096,
        "compact_stdout_under_2kb": after["stdout_bytes"] <= thresholds["compact_stdout_max_bytes"],
        "changed_only_ci_under_30s": after["ci_wall_time_seconds"] <= thresholds["changed_only_ci_target_seconds"],
        "non_adp_fixture_skips_adp_gate": not after["adp_gate_non_adp_fixture_triggered"],
        "manifest_metrics_present": after["changed_manifest_count"] >= 1,
    }
    return {
        "schema_version": 1,
        "before": {
            "source": "GOV-ROI-MINPATCH-S3-ROOT-HOTPATH-20260628.json and TaskPack preliminary findings",
            "p0_p1_finding_count": len(STAGE5_P0_P1_FINDINGS),
            "root_agents_bytes": stage3_roi.get("root_agents_bytes"),
            "ordinary_context_file_count": stage3_roi.get("ordinary_context_default_file_count"),
            "ordinary_context_bytes": stage3_roi.get("ordinary_context_default_total_bytes"),
            "ci_wall_time_seconds": stage3_roi.get("changed_only_wall_time_seconds_before_manifest"),
            "stdout_bytes": stage3_roi.get("compact_stdout_bytes_before_manifest"),
            "adp_gate_policy": "fixed_run_on_pull_request_push_changed_only",
            "manifest_count": stage3_roi.get("changed_manifest_count", "not_recorded_in_stage3_manifest"),
        },
        "after": after,
        "thresholds": thresholds,
        "pass_checks": pass_checks,
        "pass": all(pass_checks.values()),
    }


def stage5_risk_closure(
    *,
    context_contract: dict[str, Any],
    roi_metrics: dict[str, Any],
    owner_review: dict[str, Any],
    adp_decision: dict[str, Any],
    adp_non_adp_fixture: dict[str, Any],
    root: Path,
) -> dict[str, Any]:
    metadatabase_text = (root / "MetaDatabase" / "docs" / "governance" / "roadmap.yaml").read_text(encoding="utf-8")
    qbvs_project_text = (root / "QBVS" / "docs" / "governance" / "project.yaml").read_text(encoding="utf-8")
    root_agents_text = (root / "AGENTS.md").read_text(encoding="utf-8")
    checks = {
        "F-001": bool(context_contract.get("within_budget"))
        and bool((roi_metrics.get("pass_checks") or {}).get("root_agents_under_4kb_blob")),
        "F-002": bool(adp_decision.get("run_gate"))
        and adp_decision.get("reason") in {"root_governance_or_ci_changed", "adp_path_changed", "diff_untrusted_fail_closed", "unknown_path_fail_closed"}
        and not bool(adp_non_adp_fixture.get("run_gate")),
        "F-003": "zero_write_delta" in root_agents_text or "zero tracked/source write" in root_agents_text,
        "F-004": "scripts/lean_governance.py" in governance.as_list(context_contract.get("forbidden_default_reads"))
        and "governance/run_manifests" in governance.as_list(context_contract.get("forbidden_default_reads")),
        "F-005": 'current_task_id: "S1PAT01"' in metadatabase_text
        and 'project_id: "QBVS"' in qbvs_project_text
        and "display_name" in qbvs_project_text,
        "F-006": bool(owner_review.get("pass")),
    }
    return {
        "schema_version": 1,
        "findings": [
            {
                "id": finding_id,
                "summary": STAGE5_P0_P1_FINDINGS[finding_id],
                "closed": bool(checks.get(finding_id)),
            }
            for finding_id in sorted(STAGE5_P0_P1_FINDINGS)
        ],
        "open_p0_p1_count": len([value for value in checks.values() if not value]),
        "pass": all(checks.values()),
    }


def stage5_rollback_readiness(root: Path, base_ref: str | None, quality_guards: dict[str, Any]) -> dict[str, Any]:
    workflow_text = (root / ".github" / "workflows" / "project-governance.yml").read_text(encoding="utf-8")
    legacy_command = "python -B scripts/lean_governance.py validate --changed-only --enforce-sync --semantic"
    if base_ref:
        legacy_command += f" --base-ref {base_ref}"
    workflow_stops_on_failure = (
        "set -o pipefail" in workflow_text
        and ("exit \"${exit_code}\"" in workflow_text or "exit ${exit_code}" in workflow_text or "exit 1" in workflow_text)
    )
    checks = {
        "rollback_switch_present": bool(quality_guards.get("changed_only_rollback_switch_present")),
        "rollback_legacy_command_defined": "validate --changed-only" in legacy_command,
        "failure_auto_stop": workflow_stops_on_failure and bool(quality_guards.get("adp_fail_closed_preflight_present")),
        "candidate_not_authoritative": bool(quality_guards.get("candidate_report_only")),
    }
    return {
        "schema_version": 1,
        "mode": "controlled-enable-and-rollback-rehearsal",
        "controlled_enable": "changed-only ci remains enabled only as legacy-authoritative fast gate; candidate is report-only",
        "rollback_switch": "GOVERNANCE_ROLLBACK_LEGACY_CHANGED_ONLY=1",
        "rollback_command": legacy_command,
        "adp_fail_closed_recovery": "preflight parse/error path writes run_gate=true and runs ADP A-020 gate",
        "checks": checks,
        "pass": all(checks.values()),
    }


def run_stage5_audit(base_ref: str | None = None, *, root: Path = ROOT, projects_file: Path = PROJECTS_FILE) -> tuple[int, dict[str, Any]]:
    started = time.perf_counter()
    config = governance.load_yaml(projects_file)
    if not isinstance(config, dict):
        raise ValueError(f"{governance.rel(projects_file)} must parse to a mapping")
    context_contract = ordinary_context_contract(root)
    ci_exit, ci_summary = run_changed_only_ci(base_ref, root=root, projects_file=projects_file)
    changed_scope = ci_summary.get("changed_scope") if isinstance(ci_summary.get("changed_scope"), dict) else {}
    changed_files = list(changed_scope.get("changed_files") or [])
    adp_decision = adp_a020_gate_decision(changed_files, config=config, base_ref=base_ref or "")
    adp_non_adp_fixture = adp_a020_gate_decision(["Alpha/README.md"], config=config, base_ref="stage5-fixture")
    owner_review = stage5_owner_readability_review(root, projects_file)
    quality_guards = stage5_static_quality_guards(root, ci_summary)
    roi_metrics = stage5_roi_metrics(
        root=root,
        base_ref=base_ref,
        context_contract=context_contract,
        ci_summary=ci_summary,
        ci_exit_code=ci_exit,
        adp_decision=adp_decision,
        adp_non_adp_fixture=adp_non_adp_fixture,
    )
    risk_closure = stage5_risk_closure(
        context_contract=context_contract,
        roi_metrics=roi_metrics,
        owner_review=owner_review,
        adp_decision=adp_decision,
        adp_non_adp_fixture=adp_non_adp_fixture,
        root=root,
    )
    rollback = stage5_rollback_readiness(root, base_ref, quality_guards)
    task_results = {
        "S5PAT01": {
            "name": "新旧验证链 shadow parity",
            "pass": ci_exit == 0 and quality_guards["pass"],
            "evidence": ["candidate_report_only", "legacy_validation_required", "T2/T3 preserved"],
        },
        "S5PBT01": {
            "name": "采集 before/after ROI 指标",
            "pass": bool(roi_metrics.get("pass")),
            "evidence": ["ci_wall_time_seconds", "stdout_bytes", "read_file_count", "changed_file_count", "manifest_count"],
        },
        "S5PBT02": {
            "name": "逐项目 owner-readable 验收复审",
            "pass": bool(owner_review.get("pass")),
            "evidence": ["三基首屏", "owner-readable tokens", "not link page"],
        },
        "S5PCT01": {
            "name": "受控启用和 rollback rehearsal",
            "pass": bool(rollback.get("pass")),
            "evidence": ["rollback_switch", "rollback_command", "failure_auto_stop"],
        },
    }
    stop_conditions = {
        "p0_p1_unclosed": int(risk_closure.get("open_p0_p1_count", 1)) > 0,
        "read_only_or_ci_wrote_repo": not bool((ci_summary.get("zero_diff") or {}).get("clean")),
        "t2_t3_gate_reduced": not bool(quality_guards.get("t2_t3_root_rule_preserved")),
        "owner_entries_degraded": not bool(owner_review.get("pass")),
        "rollback_missing": not bool(rollback.get("pass")),
    }
    blocking = [name for name, failed in stop_conditions.items() if failed]
    decision = "SHIP" if not blocking and all(item["pass"] for item in task_results.values()) else "STOP"
    summary = {
        "owner_status_zh": "Stage5 验收通过：新策略保持 shadow，ROI 有数据，三基可读，回滚可执行。"
        if decision == "SHIP"
        else "Stage5 验收停止：存在未满足 stop condition 或任务证据缺口。",
        "schema_version": 1,
        "language": "zh-CN",
        "command": "stage5-audit",
        "stage": "S5",
        "acceptance_ids": list(STAGE5_ACCEPTANCE_IDS),
        "base_ref": base_ref or "",
        "decision": decision,
        "candidate_report_only": True,
        "task_results": task_results,
        "risk_closure": risk_closure,
        "shadow_parity": {
            "ci_exit_code": ci_exit,
            "candidate_shadow_comparison": ci_summary.get("candidate_shadow_comparison", {}),
            "quality_guards": quality_guards,
            "adp_current_diff": adp_decision,
            "adp_non_adp_fixture": adp_non_adp_fixture,
        },
        "roi_metrics": roi_metrics,
        "owner_readability": owner_review,
        "rollback_rehearsal": rollback,
        "stop_conditions": stop_conditions,
        "blocking_reasons": blocking,
        "zero_tracked_write": bool((ci_summary.get("zero_diff") or {}).get("clean")),
        "timing_telemetry": {
            "stage5_audit_seconds": round(time.perf_counter() - started, 3),
            "changed_only_ci_seconds": (ci_summary.get("timing_telemetry") or {}).get("total_seconds"),
        },
        "rollback_or_stop_condition": "decision=SHIP 时保留当前 changed-only fast gate；失败时设置 GOVERNANCE_ROLLBACK_LEGACY_CHANGED_ONLY=1 并运行 rollback_command。",
    }
    return (0 if decision == "SHIP" else 1), summary


def manifest_has_pass_result(manifest: dict[str, Any]) -> bool:
    for item in governance.as_list(manifest.get("test_results")):
        result = str(item.get("result") if isinstance(item, dict) else item).upper()
        observed = str(item.get("observed") if isinstance(item, dict) else "").upper()
        if result.startswith("PASS") or "OK" in observed:
            return True
    return False


def review_stage_manifest(root: Path, spec: dict[str, Any]) -> dict[str, Any]:
    manifest_name = str(spec.get("manifest") or "")
    raw_expected_ids = spec.get("acceptance_ids")
    if isinstance(raw_expected_ids, (list, tuple, set)):
        expected_ids = tuple(str(item) for item in raw_expected_ids)
    else:
        expected_ids = tuple(str(item) for item in governance.as_list(raw_expected_ids))
    manifest_path = root / "governance" / "run_manifests" / manifest_name
    manifest = load_stage_manifest(root, manifest_name)
    acceptance_ids = set(str(item) for item in governance.as_list(manifest.get("acceptance_ids")))
    acceptance_results = manifest.get("acceptance_results") if isinstance(manifest.get("acceptance_results"), dict) else {}
    accounted_ids = acceptance_ids | {str(key) for key in acceptance_results}
    missing_ids = [item for item in expected_ids if item not in accounted_ids]
    test_commands = governance.as_list(manifest.get("test_commands"))
    test_results = governance.as_list(manifest.get("test_results"))
    evidence_refs = governance.as_list(manifest.get("evidence_refs"))
    changed_files_actual = governance.as_list(manifest.get("changed_files_actual"))
    checks = {
        "manifest_exists": manifest_path.is_file(),
        "manifest_is_mapping": bool(manifest),
        "binding_not_legacy_unbound": str(manifest.get("binding_status") or "") != "LEGACY_UNBOUND",
        "expected_acceptance_ids_present": not missing_ids,
        "test_commands_present": bool(test_commands),
        "test_results_present": bool(test_results),
        "test_pass_result_present": manifest_has_pass_result(manifest),
        "evidence_refs_present": bool(evidence_refs),
        "changed_files_actual_present": bool(changed_files_actual),
    }
    return {
        "stage": str(spec.get("stage") or ""),
        "manifest": manifest_name,
        "path": governance.rel(manifest_path),
        "expected_acceptance_ids": list(expected_ids),
        "manifest_acceptance_ids": sorted(acceptance_ids),
        "missing_acceptance_ids": missing_ids,
        "checks": checks,
        "failed_checks": [name for name, passed in checks.items() if not passed],
        "pass": all(checks.values()),
    }


def git_tracked_files(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode != 0:
        return []
    return [line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()]


def review_solution_boundaries(root: Path) -> dict[str, Any]:
    context_contract = ordinary_context_contract(root)
    root_agents_blob_size = git_blob_size(root, "AGENTS.md")
    tracked_files = git_tracked_files(root)
    forbidden_current_truth = sorted(
        path for path in tracked_files if Path(path).name in {"CURRENT.md", "SHIP.md"}
    )
    forbidden_default_reads = set(str(item) for item in governance.as_list(context_contract.get("forbidden_default_reads")))
    stage_manifest_paths = [
        f"governance/run_manifests/{spec['manifest']}"
        for spec in FINAL_REVIEW_STAGE_MANIFESTS
    ]
    checks = {
        "no_new_current_truth_markdown": not forbidden_current_truth,
        "stage_manifests_preserved": all((root / path).is_file() for path in stage_manifest_paths),
        "ordinary_context_within_budget": bool(context_contract.get("within_budget")),
        "ordinary_context_file_count_under_limit": int(context_contract.get("default_file_count", 999)) <= ORDINARY_CONTEXT_MAX_FILES,
        "ordinary_context_bytes_under_limit": int(context_contract.get("default_total_bytes", 999999)) <= ORDINARY_CONTEXT_MAX_BYTES,
        "root_agents_under_4kb_blob": root_agents_blob_size is not None and root_agents_blob_size <= 4096,
        "default_reads_do_not_include_governance_compute": ORDINARY_CONTEXT_FORBIDDEN_DEFAULT_READS[0] in forbidden_default_reads
        and ORDINARY_CONTEXT_FORBIDDEN_DEFAULT_READS[1] in forbidden_default_reads,
    }
    return {
        "schema_version": 1,
        "context_contract": context_contract,
        "root_agents_blob_bytes": root_agents_blob_size,
        "forbidden_current_truth_markdown": forbidden_current_truth,
        "stage_manifest_paths": stage_manifest_paths,
        "checks": checks,
        "failed_checks": [name for name, passed in checks.items() if not passed],
        "pass": all(checks.values()),
    }


def review_project_capsules(root: Path) -> dict[str, Any]:
    project_results: list[dict[str, Any]] = []
    for project in FINAL_REVIEW_PROJECT_CAPSULES:
        path = root / project / "AGENTS.md"
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        checks = {
            "agents_exists": path.is_file(),
            "s4_capsule_present": "S4" in text and "精简执行胶囊" in text,
            "ordinary_read_limit_present": "不得" in text,
            "model_parameters_escalation_present": "模型参数文件.md" in text,
            "governance_verify_present": "lean_governance.py" in text and ("验证" in text or "verify" in text.lower()),
        }
        if project == "arxiv-daily-push":
            checks.update(
                {
                    "ordinary_non_source_route_present": "普通非来源变更" in text and "不得默认读取完整 `用户中心/`" in text,
                    "source_full_gate_route_present": "来源、板块、scheduler、SMTP、storage、security、ranking" in text
                    and "完整特殊" in text,
                    "source_gate_tests_present": "test_security_boundary.py" in text and "test_source_registry.py" in text,
                }
            )
        project_results.append(
            {
                "project": project,
                "path": governance.rel(path),
                "checks": checks,
                "failed_checks": [name for name, passed in checks.items() if not passed],
                "pass": all(checks.values()),
            }
        )
    failed = [item["project"] for item in project_results if not item["pass"]]
    return {
        "schema_version": 1,
        "mode": "s4_project_execution_capsule_review",
        "project_count": len(project_results),
        "failed_projects": failed,
        "projects": project_results,
        "pass": not failed,
    }


def review_identity_repairs(root: Path) -> dict[str, Any]:
    metadatabase_roadmap = (root / "MetaDatabase" / "docs" / "governance" / "roadmap.yaml").read_text(encoding="utf-8")
    metadatabase_delivery = (root / "MetaDatabase" / "docs" / "governance" / "delivery_tasks.yaml").read_text(encoding="utf-8")
    qbvs_project = (root / "QBVS" / "docs" / "governance" / "project.yaml").read_text(encoding="utf-8")
    qbvs_readme = (root / "QBVS" / "README.md").read_text(encoding="utf-8")
    checks = {
        "metadatabase_current_task_id_legal": 'current_task_id: "S1PAT01"' in metadatabase_roadmap,
        "metadatabase_legacy_alias_retained": 'legacy_task_ids:' in metadatabase_delivery
        and '"TASK-MDB-S0-001"' in metadatabase_delivery,
        "qbvs_project_id_current": 'project_id: "QBVS"' in qbvs_project,
        "qbvs_display_name_present": 'display_name: "大数据模拟器' in qbvs_project,
        "qbvs_readme_identity_current": "QBVS" in qbvs_readme
        and "大数据模拟器" in qbvs_readme
        and "project_id: `PFI_BIG_DATA_SIMULATOR`" not in qbvs_readme,
    }
    return {
        "schema_version": 1,
        "mode": "s4_identity_repair_review",
        "checks": checks,
        "failed_checks": [name for name, passed in checks.items() if not passed],
        "pass": all(checks.values()),
    }


def run_roi_final_audit(base_ref: str | None = None, *, root: Path = ROOT, projects_file: Path = PROJECTS_FILE) -> tuple[int, dict[str, Any]]:
    started = time.perf_counter()
    stage5_exit, stage5 = run_stage5_audit(base_ref, root=root, projects_file=projects_file)
    stage_reviews = [review_stage_manifest(root, spec) for spec in FINAL_REVIEW_STAGE_MANIFESTS]
    boundaries = review_solution_boundaries(root)
    capsules = review_project_capsules(root)
    identity = review_identity_repairs(root)
    quality_guards = (
        (stage5.get("shadow_parity") or {}).get("quality_guards")
        if isinstance(stage5.get("shadow_parity"), dict)
        else {}
    )
    risk_closure = stage5.get("risk_closure") if isinstance(stage5.get("risk_closure"), dict) else {}
    owner_readability = stage5.get("owner_readability") if isinstance(stage5.get("owner_readability"), dict) else {}
    rollback = stage5.get("rollback_rehearsal") if isinstance(stage5.get("rollback_rehearsal"), dict) else {}
    roi_metrics = stage5.get("roi_metrics") if isinstance(stage5.get("roi_metrics"), dict) else {}
    task_results = {
        "FINAL-S3-S5-REQ-MATRIX": {
            "name": "S3/S4/S5 manifest 验收矩阵完整",
            "pass": all(item["pass"] for item in stage_reviews),
            "evidence": [item["manifest"] for item in stage_reviews],
        },
        "FINAL-QUALITY-GUARDS": {
            "name": "质量闸、T2/T3、全量治理、ADP fail-closed 和 hook advisory 保留",
            "pass": bool(quality_guards.get("pass")) and bool(stage5.get("zero_tracked_write")),
            "evidence": ["stage5.shadow_parity.quality_guards", "stage5.zero_tracked_write"],
        },
        "FINAL-ROI-EVIDENCE": {
            "name": "ROI 指标与普通上下文预算仍达标",
            "pass": bool(roi_metrics.get("pass")) and bool(boundaries.get("pass")),
            "evidence": ["stage5.roi_metrics", "ordinary_context_contract", "root_AGENTS_blob_bytes"],
        },
        "FINAL-HANDOFF": {
            "name": "项目胶囊、中文 owner 可读和 identity 修复可交接",
            "pass": bool(capsules.get("pass"))
            and bool(identity.get("pass"))
            and bool(owner_readability.get("pass"))
            and int(risk_closure.get("open_p0_p1_count", 1)) == 0
            and bool(rollback.get("pass")),
            "evidence": ["project AGENTS capsules", "owner_readability", "risk_closure", "rollback_rehearsal"],
        },
    }
    stop_conditions = {
        "stage_manifest_acceptance_gap": not task_results["FINAL-S3-S5-REQ-MATRIX"]["pass"],
        "stage5_audit_not_ship": stage5_exit != 0 or stage5.get("decision") != "SHIP",
        "quality_guard_missing": not task_results["FINAL-QUALITY-GUARDS"]["pass"],
        "roi_budget_or_boundary_broken": not task_results["FINAL-ROI-EVIDENCE"]["pass"],
        "owner_or_handoff_gap": not task_results["FINAL-HANDOFF"]["pass"],
        "new_current_truth_file_created": bool(boundaries.get("forbidden_current_truth_markdown")),
    }
    blocking = [name for name, failed in stop_conditions.items() if failed]
    decision = "SHIP" if not blocking and all(item["pass"] for item in task_results.values()) else "STOP"
    summary = {
        "owner_status_zh": "最终复审通过：S3-S5 证据闭环，治理真相保留，治理计算仍在显式 gate 中，不进入普通开发热路径。"
        if decision == "SHIP"
        else "最终复审停止：存在阶段证据、质量闸、ROI 预算或中文交接缺口。",
        "schema_version": 1,
        "language": "zh-CN",
        "command": "roi-final-audit",
        "acceptance_ids": list(FINAL_REVIEW_ACCEPTANCE_IDS),
        "base_ref": base_ref or "",
        "decision": decision,
        "stage_manifest_reviews": stage_reviews,
        "task_results": task_results,
        "solution_boundaries": boundaries,
        "project_capsules": capsules,
        "identity_repairs": identity,
        "stage5_audit": {
            "exit_code": stage5_exit,
            "decision": stage5.get("decision"),
            "owner_status_zh": stage5.get("owner_status_zh"),
            "risk_closure": risk_closure,
            "owner_readability": {
                "project_count": owner_readability.get("project_count"),
                "passed_project_count": owner_readability.get("passed_project_count"),
                "failed_projects": owner_readability.get("failed_projects"),
                "pass": owner_readability.get("pass"),
            },
            "quality_guards": quality_guards,
            "roi_metrics": roi_metrics,
            "rollback_rehearsal": rollback,
            "zero_tracked_write": stage5.get("zero_tracked_write"),
        },
        "stop_conditions": stop_conditions,
        "blocking_reasons": blocking,
        "timing_telemetry": {
            "final_audit_seconds": round(time.perf_counter() - started, 3),
            "stage5_audit_seconds": (stage5.get("timing_telemetry") or {}).get("stage5_audit_seconds")
            if isinstance(stage5.get("timing_telemetry"), dict)
            else None,
        },
        "rollback_or_stop_condition": "decision=SHIP 时仅保留显式审计命令；失败时先停，不合并/不继续开发，按 blocking_reasons 修复后重跑。",
    }
    return (0 if decision == "SHIP" else 1), summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    baseline = subparsers.add_parser("baseline", help="Print a read-only repository baseline summary.")
    baseline.add_argument("--all", action="store_true", help="Inspect root governance and all registered projects.")
    subparsers.add_parser("context-contract", help="Print the ordinary T0/T1 compact context contract.")
    changed_scope = subparsers.add_parser("changed-scope", help="Print read-only changed project selection.")
    changed_scope.add_argument("--base-ref", help="Explicit base commit/ref for changed-scope diff selection.")
    adp_a020_gate = subparsers.add_parser("adp-a020-gate", help="Decide whether the ADP A-020 gate must run.")
    adp_a020_gate.add_argument("--base-ref", help="Explicit base commit/ref for changed-file diff selection.")
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
    stage5_audit = subparsers.add_parser("stage5-audit", help="Run Stage5 ROI acceptance and rollback audit.")
    stage5_audit.add_argument("--base-ref", help="Explicit base commit/ref for Stage5 changed-only audit.")
    roi_final_audit = subparsers.add_parser("roi-final-audit", help="Run the final S3-S5 ROI cross-stage audit.")
    roi_final_audit.add_argument("--base-ref", help="Explicit base commit/ref for final ROI audit.")
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
    if args.command == "context-contract":
        print(json.dumps(ordinary_context_contract(ROOT), ensure_ascii=True, sort_keys=True, separators=(",", ":")))
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
    if args.command == "adp-a020-gate":
        summary = adp_a020_gate_decision_from_git(args.base_ref, projects_file=PROJECTS_FILE)
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
    if args.command == "stage5-audit":
        exit_code, summary = run_stage5_audit(args.base_ref, root=ROOT, projects_file=PROJECTS_FILE)
        print(json.dumps(summary, ensure_ascii=False, sort_keys=False, separators=(",", ":")))
        return exit_code
    if args.command == "roi-final-audit":
        exit_code, summary = run_roi_final_audit(args.base_ref, root=ROOT, projects_file=PROJECTS_FILE)
        print(json.dumps(summary, ensure_ascii=False, sort_keys=False, separators=(",", ":")))
        return exit_code
    if args.command == "validate":
        return governance.main(build_validate_argv(args))
    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
