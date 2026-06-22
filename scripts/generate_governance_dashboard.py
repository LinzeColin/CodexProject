#!/usr/bin/env python3
"""Generate Review 7 governance views from canonical machine sources."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import validate_project_governance as structural


sys.dont_write_bytecode = True

ROOT = structural.ROOT
GENERATOR_VERSION = "3.0.0"
COMPLETED_TASK_STATES = {"completed", "rejected", "deprecated"}
EXECUTABLE_TASK_STATES = {"ready", "in_progress"}
ASSURANCE_STATUSES = {"VERIFIED", "PARTIAL", "UNVERIFIED", "FAILED", "NOT_APPLICABLE"}
PROJECT_REPOSITORIES = {
    "Alpha": "https://github.com/LinzeColin/Alpha",
    "EEI": "https://github.com/LinzeColin/CodexProject/tree/main/EEI",
    "EVA_OS": "https://github.com/LinzeColin/EVA_OS",
    "FIFA": "https://github.com/LinzeColin/FIFA",
    "OpMe_System": "https://github.com/LinzeColin/OpMe_System",
    "OpenAIDatabase": "https://github.com/LinzeColin/CodexProject/tree/main/OpenAIDatabase",
    "PFI_BIG_DATA_SIMULATOR": "https://github.com/LinzeColin/CodexProject/tree/main/PFI/%E5%A4%A7%E6%95%B0%E6%8D%AE%E6%A8%A1%E6%8B%9F%E5%99%A8",
    "Serenity-Alipay": "https://github.com/LinzeColin/Serenity-Alipay",
    "whkmSalary": "https://github.com/LinzeColin/whkmSalary",
    "arxiv-daily-push": "https://github.com/LinzeColin/CodexProject/tree/main/arxiv-daily-push",
}


ASSURANCE_POLICY = {
    "Alpha": {
        "empirical": "unknown",
        "operational": "blocked",
        "readiness": "blocked",
        "decision": "是否提供生产数据、paper broker 与 live execution policy 证据，或继续保持 blocked。",
        "blockers": ["production validation evidence", "broker policy decision", "calibration evidence"],
    },
    "EEI": {
        "empirical": "partial",
        "operational": "partial",
        "readiness": "blocked",
        "decision": "是否继续 24 小时 operator soak；当前 4 小时证据只支持 partial。",
        "blockers": ["24h operator soak evidence", "historical event binding backlog"],
    },
    "EVA_OS": {
        "empirical": "unknown",
        "operational": "blocked",
        "readiness": "blocked",
        "decision": "是否投入 137 个 remaining parameter reviews 和来源/校准证据。",
        "blockers": ["parameter review backlog", "source and calibration evidence"],
    },
    "FIFA": {
        "empirical": "unknown",
        "operational": "blocked",
        "readiness": "conditional",
        "decision": "是否关闭 17 个 parser/validation 参数人工复核。",
        "blockers": ["17 active parameters need semantic review", "TAB production evidence not claimed"],
    },
    "OpMe_System": {
        "empirical": "unknown",
        "operational": "blocked",
        "readiness": "conditional",
        "decision": "是否补齐 calibration、prompt/provider policy 与 owner sign-off 证据。",
        "blockers": ["calibration evidence", "prompt/provider policy", "owner sign-off"],
    },
    "OpenAIDatabase": {
        "empirical": "unknown",
        "operational": "blocked",
        "readiness": "blocked",
        "decision": "是否继续补齐 memory routing 分支和 FORM-010 语义复核。",
        "blockers": ["remaining semantic review", "calibration/source evidence"],
    },
    "PFI_BIG_DATA_SIMULATOR": {
        "empirical": "unknown",
        "operational": "blocked",
        "readiness": "conditional",
        "decision": "是否关闭 PARAM-110/PARAM-111 或保留 human review required。",
        "blockers": ["two implementation parameters need review", "calibration evidence"],
    },
    "Serenity-Alipay": {
        "empirical": "unknown",
        "operational": "partial",
        "readiness": "conditional",
        "decision": "是否启动 empirical calibration evidence task；实现一致性已经 machine verified。",
        "blockers": ["empirical calibration unknown", "owner evidence decision"],
    },
    "whkmSalary": {
        "empirical": "unknown",
        "operational": "blocked",
        "readiness": "blocked",
        "decision": "是否提供一手政策、法域、生效日期、计税基础和舍入证据。",
        "blockers": ["policy source evidence", "jurisdiction/effective date evidence"],
    },
    "arxiv-daily-push": {
        "empirical": "partial",
        "operational": "partial",
        "readiness": "blocked",
        "decision": "是否启动生产 trial；当前只有本地两日模拟，生产启动和 30 天验收仍 blocked。",
        "blockers": ["production trial not started", "30-day acceptance absent", "historical event binding backlog"],
    },
}


def git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def current_commit() -> str:
    value = git_output(["rev-parse", "HEAD"])
    return value if re.fullmatch(r"[0-9a-f]{40}", value) else "0" * 40


def current_tree_hash() -> str:
    value = git_output(["rev-parse", "HEAD^{tree}"])
    return value if re.fullmatch(r"[0-9a-f]{40}", value) else "0" * 40


def configured_source_base() -> str | None:
    value = os.environ.get("GOVERNANCE_SOURCE_BASE_COMMIT", "").strip()
    return value if re.fullmatch(r"[0-9a-f]{40}", value) else None


def configured_source_tree() -> str | None:
    value = os.environ.get("GOVERNANCE_SOURCE_TREE_HASH", "").strip()
    return value if re.fullmatch(r"[0-9a-f]{40}", value) else None


def assurance_status(value: str | None) -> str:
    normalized = str(value or "unknown").strip().lower()
    mapping = {
        "pass": "VERIFIED",
        "verified": "VERIFIED",
        "machine_verified": "VERIFIED",
        "partial": "PARTIAL",
        "blocked": "FAILED",
        "failed": "FAILED",
        "unknown": "UNVERIFIED",
        "unverified": "UNVERIFIED",
        "not_applicable": "NOT_APPLICABLE",
        "not applicable": "NOT_APPLICABLE",
        "n/a": "NOT_APPLICABLE",
    }
    return mapping.get(normalized, "UNVERIFIED")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def canonical_input_paths(project_path: Path) -> list[Path]:
    candidates = [
        project_path / "VERSION",
        project_path / "CHANGELOG.md",
        project_path / "docs/governance/MODEL_SPEC.md",
        project_path / "docs/governance/model_registry.yaml",
        project_path / "docs/governance/formula_registry.yaml",
        project_path / "docs/governance/parameter_registry.csv",
        project_path / "docs/governance/DEVELOPMENT_LEDGER.md",
        project_path / "docs/governance/development_events.jsonl",
        project_path / "docs/governance/DELIVERY_PLAN.md",
        project_path / "docs/governance/delivery_tasks.yaml",
        project_path / "docs/governance/VERSION_MATRIX.yaml",
        project_path / "docs/governance/TRACEABILITY_MATRIX.csv",
        ROOT / "governance/projects.yaml",
    ]
    return [path for path in candidates if path.is_file()]


def source_snapshot_hash(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda item: rel(item)):
        digest.update(rel(path).encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes().replace(b"\r\n", b"\n"))
        digest.update(b"\0")
    return "sha256:" + digest.hexdigest()


def active_registry_counts(project_path: Path) -> dict[str, int]:
    parameters = read_csv(project_path / "docs/governance/parameter_registry.csv")
    active_params = [row for row in parameters if str(row.get("status") or "").lower() == "active"]
    checked_params = [
        row
        for row in active_params
        if row.get("source_selector") and row.get("extracted_value") not in {None, ""} and row.get("evidence_hash")
    ]
    formula_data = structural.load_yaml(project_path / "docs/governance/formula_registry.yaml")
    formulas = structural.as_list(formula_data.get("formulas")) if isinstance(formula_data, dict) else []
    active_formulas = [
        row for row in formulas if isinstance(row, dict) and str(row.get("status") or "").lower() == "active"
    ]
    checked_formulas = [
        row
        for row in active_formulas
        if row.get("implementation_refs") and row.get("implementation_fingerprint") and row.get("evidence_hash")
    ]
    return {
        "total_parameters": len(parameters),
        "active_parameters": len(active_params),
        "checked_parameters": len(checked_params),
        "total_formulas": len(formulas),
        "active_formulas": len(active_formulas),
        "checked_formulas": len(checked_formulas),
    }


def collect_unresolved_fact_ids(project_id: str, parsed: dict[str, Any], counts: dict[str, int]) -> list[str]:
    ids: set[str] = set()

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                if key in {"unknown_task_ids", "semantic_review_task_ids", "unresolved_fact_ids"}:
                    for ref in structural.as_list(item):
                        text = str(ref).strip()
                        if text:
                            ids.add(text)
                else:
                    visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    for key in ("models", "formulas", "parameters", "tasks", "traceability", "version_matrix"):
        visit(parsed.get(key))
    if counts["checked_parameters"] < counts["active_parameters"]:
        ids.add(f"FACT-{project_id}-IMPLEMENTATION-PARAMETER-REVIEW")
    if counts["checked_formulas"] < counts["active_formulas"]:
        ids.add(f"FACT-{project_id}-IMPLEMENTATION-FORMULA-REVIEW")
    policy = ASSURANCE_POLICY.get(project_id, {})
    if policy.get("empirical") in {"unknown", "partial"}:
        ids.add(f"FACT-{project_id}-EMPIRICAL-EVIDENCE")
    if policy.get("operational") in {"blocked", "partial", "unknown"}:
        ids.add(f"FACT-{project_id}-OPERATIONAL-EVIDENCE")
    return sorted(ids)


def load_events(project_path: Path) -> list[dict[str, Any]]:
    path = project_path / "docs/governance/development_events.jsonl"
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            events.append(value)
    return events


def event_time(event: dict[str, Any]) -> str:
    return str(event.get("timestamp") or event.get("date") or "")


def max_event_time(events: list[dict[str, Any]]) -> str:
    values = [event_time(event) for event in events if event_time(event)]
    return max(values) if values else "UNKNOWN"


def pending_event_count(events: list[dict[str, Any]]) -> int:
    count = 0
    for event in events:
        commit = str(event.get("result_commit") or event.get("git_commit") or "").upper()
        if commit in {"", "PENDING", "PENDING_CI"}:
            count += 1
    return count


def event_binding_counts(events: list[dict[str, Any]]) -> dict[str, int]:
    counts = {
        "tree_bound_events": 0,
        "commit_bound_events": 0,
        "legacy_unbound_events": 0,
        "precommit_pending_events": 0,
    }
    for event in events:
        binding = str(event.get("binding_status") or "").strip().lower()
        commit = str(event.get("result_commit") or event.get("git_commit") or "").strip()
        has_commit = bool(re.fullmatch(r"[0-9a-f]{7,40}", commit))
        if binding == "precommit_tree_bound":
            counts["tree_bound_events"] += 1
        elif has_commit or event.get("ci_attestation_ref"):
            counts["commit_bound_events"] += 1
        elif binding in {"pre_commit_pending", "precommit_pending"}:
            counts["precommit_pending_events"] += 1
        else:
            counts["legacy_unbound_events"] += 1
    return counts


def completed_task_ids(tasks: list[dict[str, Any]]) -> set[str]:
    return {
        str(task.get("task_id"))
        for task in tasks
        if isinstance(task, dict) and str(task.get("status") or "") in COMPLETED_TASK_STATES
    }


def select_next_task(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    completed = completed_task_ids(tasks)
    candidates: list[dict[str, Any]] = []
    for task in tasks:
        if not isinstance(task, dict):
            continue
        status = str(task.get("status") or "")
        if status not in EXECUTABLE_TASK_STATES:
            continue
        dependencies = [str(dep) for dep in structural.as_list(task.get("dependencies")) if str(dep)]
        unmet = [dep for dep in dependencies if dep not in completed]
        if unmet or not task.get("acceptance_ids") or not task.get("test_commands"):
            continue
        candidates.append(task)
    if not candidates:
        return {
            "task_id": "NONE",
            "status": "not_applicable",
            "reason": "No ready or in_progress task has completed dependencies, Acceptance IDs, and test commands.",
            "acceptance_ids": [],
            "owner": "project owner",
            "unblock_condition": "Unblock or define a ready/in_progress task with completed dependencies and evidence policy.",
        }
    candidates.sort(key=lambda task: (0 if str(task.get("status")) == "in_progress" else 1, str(task.get("task_id"))))
    task = candidates[0]
    return {
        "task_id": str(task.get("task_id") or "NONE"),
        "status": str(task.get("status") or ""),
        "reason": str(task.get("objective") or ""),
        "acceptance_ids": structural.as_list(task.get("acceptance_ids")),
        "owner": "Codex/governance runner",
        "unblock_condition": "Run the listed test commands and attach evidence.",
    }


def yaml_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if value is None:
        return "null"
    return json.dumps(str(value), ensure_ascii=False)


def dump_yaml(value: Any, indent: int = 0) -> list[str]:
    pad = " " * indent
    if isinstance(value, dict):
        lines: list[str] = []
        for key, item in value.items():
            if item == []:
                lines.append(f"{pad}{key}: []")
                continue
            if isinstance(item, (dict, list)):
                lines.append(f"{pad}{key}:")
                lines.extend(dump_yaml(item, indent + 2))
            else:
                lines.append(f"{pad}{key}: {yaml_scalar(item)}")
        return lines
    if isinstance(value, list):
        if not value:
            return [f"{pad}[]"]
        lines = []
        for item in value:
            if isinstance(item, (dict, list)):
                lines.append(f"{pad}-")
                lines.extend(dump_yaml(item, indent + 2))
            else:
                lines.append(f"{pad}- {yaml_scalar(item)}")
        return lines
    return [f"{pad}{yaml_scalar(value)}"]


def existing_assurance_base(project_path: Path) -> str | None:
    path = project_path / "docs/governance/ASSURANCE_STATUS.yaml"
    if not path.exists():
        return None
    match = re.search(r"(?m)^source_base_commit:\s*\"?([0-9a-f]{40})\"?\s*$", path.read_text(encoding="utf-8"))
    commit = match.group(1) if match else ""
    return commit if re.fullmatch(r"[0-9a-f]{40}", commit) else None


def existing_assurance_tree(project_path: Path) -> str | None:
    path = project_path / "docs/governance/ASSURANCE_STATUS.yaml"
    if not path.exists():
        return None
    match = re.search(r"(?m)^source_tree_hash:\s*\"?([0-9a-f]{40})\"?\s*$", path.read_text(encoding="utf-8"))
    tree = match.group(1) if match else ""
    return tree if re.fullmatch(r"[0-9a-f]{40}", tree) else None


def existing_root_base() -> str | None:
    for path in (ROOT / "GOVERNANCE_DASHBOARD.md", ROOT / "OWNER_PORTFOLIO.md", ROOT / "README.md"):
        if not path.exists():
            continue
        match = re.search(r"source_base_commit:\s*`?([0-9a-f]{40})`?", path.read_text(encoding="utf-8"))
        commit = match.group(1) if match else ""
        if re.fullmatch(r"[0-9a-f]{40}", commit):
            return commit
    return None


def existing_root_tree() -> str | None:
    for path in (ROOT / "GOVERNANCE_DASHBOARD.md", ROOT / "OWNER_PORTFOLIO.md", ROOT / "README.md"):
        if not path.exists():
            continue
        match = re.search(r"source_tree_hash:\s*`?([0-9a-f]{40})`?", path.read_text(encoding="utf-8"))
        tree = match.group(1) if match else ""
        if re.fullmatch(r"[0-9a-f]{40}", tree):
            return tree
    return None


def latest_manifest(project_id: str, events: list[dict[str, Any]]) -> dict[str, Any]:
    manifest_dir = ROOT / "governance/run_manifests"
    refs: list[str] = []
    if events:
        refs.extend(str(ref) for ref in structural.as_list(events[-1].get("evidence_refs")))
    refs.extend(str(path.relative_to(ROOT)) for path in sorted(manifest_dir.glob("*.json")))
    for ref in reversed(refs):
        path = ROOT / ref
        if path.suffix != ".json" or not path.is_file() or manifest_dir not in path.parents:
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if str(data.get("project_id") or "") == project_id:
            data["_path"] = rel(path)
            return data
    return {}


def load_project(project: dict[str, Any]) -> dict[str, Any]:
    project_id = structural.project_scope(project)
    project_path = ROOT / str(project.get("path") or "")
    parsed_validation = structural.Validation()
    parsed = structural.parse_project_governance(project_path, parsed_validation, True, project_id)
    tasks = [task for task in structural.as_list(parsed.get("tasks")) if isinstance(task, dict)]
    events = load_events(project_path)
    matrix = parsed.get("version_matrix") if isinstance(parsed.get("version_matrix"), dict) else {}
    counts = active_registry_counts(project_path)
    unresolved = collect_unresolved_fact_ids(project_id, parsed, counts)
    source_paths = canonical_input_paths(project_path)
    source_hash = source_snapshot_hash(source_paths)
    base_commit = configured_source_base() or existing_assurance_base(project_path) or current_commit()
    tree_hash = configured_source_tree() or existing_assurance_tree(project_path) or current_tree_hash()
    policy = ASSURANCE_POLICY.get(project_id, {})
    impl_status = (
        "NOT_APPLICABLE"
        if counts["active_parameters"] == 0 and counts["active_formulas"] == 0
        else "VERIFIED"
        if counts["checked_parameters"] == counts["active_parameters"]
        and counts["checked_formulas"] == counts["active_formulas"]
        else "PARTIAL"
    )
    parameter_source_status = "VERIFIED" if counts["checked_parameters"] == counts["active_parameters"] else "PARTIAL"
    event_counts = event_binding_counts(events)
    evidence_freshness_status = "PARTIAL" if event_counts["legacy_unbound_events"] else "VERIFIED"
    next_task = select_next_task(tasks)
    assurance = {
        "project_id": project_id,
        "as_of_event_id": str(events[-1].get("event_id") or events[-1].get("iteration_id") or "NONE") if events else "NONE",
        "source_snapshot_hash": source_hash,
        "source_base_commit": base_commit,
        "source_tree_hash": tree_hash,
        "snapshot_event_time": max_event_time(events),
        "generator_version": GENERATOR_VERSION,
        "final_commit_binding": "PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION",
        "dimensions": {
            "structural_completeness": {
                "status": "VERIFIED",
                "fact_level": "EXTRACTED",
                "evidence_refs": ["scripts/validate_project_governance.py"],
            },
            "implementation_congruence": {
                "status": impl_status,
                "machine_verified_means": "documented implementation values and fingerprints match extractable code/config sources only",
                "fact_level": "EXTRACTED",
                "checked_active_parameters": counts["checked_parameters"],
                "total_active_parameters": counts["active_parameters"],
                "checked_active_formulas": counts["checked_formulas"],
                "total_active_formulas": counts["active_formulas"],
                "unresolved_fact_ids": [
                    item for item in unresolved if "IMPLEMENTATION" in item or "PARAM" in item or "FORM" in item
                ],
                "evidence_refs": [
                    f"{project.get('path')}/docs/governance/parameter_registry.csv",
                    f"{project.get('path')}/docs/governance/formula_registry.yaml",
                ],
            },
            "parameter_source_quality": {
                "status": parameter_source_status,
                "fact_level": "EXTRACTED" if parameter_source_status == "VERIFIED" else "UNKNOWN",
                "checked_active_parameters": counts["checked_parameters"],
                "total_active_parameters": counts["active_parameters"],
                "evidence_refs": [f"{project.get('path')}/docs/governance/parameter_registry.csv"],
            },
            "empirical_validation": {
                "status": assurance_status(str(policy.get("empirical") or "unknown")),
                "fact_level": "UNKNOWN" if assurance_status(str(policy.get("empirical") or "unknown")) == "UNVERIFIED" else "EXTRACTED",
                "unresolved_fact_ids": [item for item in unresolved if "EMPIRICAL" in item],
                "evidence_refs": [f"{project.get('path')}/docs/governance/delivery_tasks.yaml"],
            },
            "operational_validation": {
                "status": assurance_status(str(policy.get("operational") or "unknown")),
                "fact_level": "UNKNOWN"
                if assurance_status(str(policy.get("operational") or "unknown")) == "UNVERIFIED"
                else "EXTRACTED",
                "unresolved_fact_ids": [item for item in unresolved if "OPERATIONAL" in item],
                "evidence_refs": [f"{project.get('path')}/docs/governance/development_events.jsonl"],
            },
            "delivery_evidence": {
                "status": assurance_status(str(policy.get("readiness") or "blocked")),
                "fact_level": "EXTRACTED",
                "evidence_refs": [f"{project.get('path')}/docs/governance/delivery_tasks.yaml"],
            },
            "evidence_freshness": {
                "status": evidence_freshness_status,
                "fact_level": "EXTRACTED",
                "tree_bound_events": event_counts["tree_bound_events"],
                "commit_bound_events": event_counts["commit_bound_events"],
                "legacy_unbound_events": event_counts["legacy_unbound_events"],
                "precommit_pending_events": event_counts["precommit_pending_events"],
                "evidence_refs": [f"{project.get('path')}/docs/governance/development_events.jsonl"],
            },
        },
        "delivery_readiness": {
            "status": assurance_status(str(policy.get("readiness") or "blocked")),
            "release_gate": str(matrix.get("current_gate") or "UNKNOWN"),
            "blocker_ids": unresolved[:8],
        },
        "next_executable_task": next_task,
        "owner_decision": {
            "required": True,
            "decision_id": f"DEC-{project_id}-REVIEW6-001",
            "question": str(policy.get("decision") or "Decide whether to continue evidence hardening."),
            "options": [
                "A: fund evidence hardening",
                "B: keep blocked/conditional and defer",
                "C: de-scope this project from delivery claims",
            ],
        },
    }
    return {
        "project_id": project_id,
        "path": str(project.get("path") or ""),
        "ci_mode": str(project.get("ci_mode") or ""),
        "product_version": str(matrix.get("product_version") or "UNKNOWN"),
        "current_iteration": str(matrix.get("current_iteration") or "UNKNOWN"),
        "current_phase": str(matrix.get("current_phase") or "UNKNOWN"),
        "current_gate": str(matrix.get("current_gate") or "UNKNOWN"),
        "counts": counts,
        "models": len(structural.as_list(parsed.get("models"))),
        "tasks": tasks,
        "events": events,
        "latest_event": events[-1] if events else {},
        "latest_manifest": latest_manifest(project_id, events),
        "pending_event_count": pending_event_count(events),
        "event_binding_counts": event_counts,
        "unresolved_fact_ids": unresolved,
        "policy_blockers": list(policy.get("blockers") or []),
        "assurance": assurance,
    }


def brief_list(values: list[str], limit: int = 3) -> str:
    if not values:
        return "none"
    text = ", ".join(values[:limit])
    if len(values) > limit:
        text += f", +{len(values) - limit}"
    return text


def render_readme(projects: list[dict[str, Any]], meta: dict[str, str]) -> str:
    rows = "\n".join(
        f"| `{item['project_id']}` | `{item['path']}` | {PROJECT_REPOSITORIES.get(item['project_id'], 'UNKNOWN')} |"
        for item in projects
    )
    return f"""# CodexProject

Active Codex-related project hub for LinzeColin.

## Governance Entry

- Owner portfolio: [OWNER_PORTFOLIO.md](OWNER_PORTFOLIO.md)
- Engineering dashboard: [GOVERNANCE_DASHBOARD.md](GOVERNANCE_DASHBOARD.md)
- Project registry: [governance/projects.yaml](governance/projects.yaml)
- Standard: [docs/governance/STANDARD.md](docs/governance/STANDARD.md)

## Snapshot Metadata

- source_base_commit: `{meta['source_base_commit']}`
- source_tree_hash: `{meta['source_tree_hash']}`
- source_snapshot_hash: `{meta['source_snapshot_hash']}`
- generator_version: `{GENERATOR_VERSION}`
- final_commit_binding: `PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION`

## Assurance Vocabulary

- `structural_completeness`: required governance files parse and cross-reference.
- `implementation_congruence`: documented implementation values and fingerprints match extractable code/config sources.
- `parameter_source_quality`: active parameter values have source selectors or explicit unresolved tasks.
- `empirical_validation`: model claims are supported by calibration, backtest, fixture, or experiment evidence.
- `operational_validation`: runtime, CI, soak, or production-trial evidence exists.
- `delivery_evidence`: delivery gates and completed tasks have acceptance evidence.
- `evidence_freshness`: events are tree-bound, commit-bound, or honestly listed as legacy unbound.

`machine_verified` is not a production claim. It only maps to implementation congruence when code/config extraction proves documented facts.

## Projects

| Project | Path | Repository |
|---|---|---|
{rows}

## Required Checks

```bash
python3 scripts/validate_project_governance.py --all --semantic --drift-report
python3 scripts/validate_information_quality.py --all --fast --fail-on-error
python3 scripts/generate_governance_dashboard.py --write
```

This repository is the source-level project hub. Each project directory must keep canonical governance files, assurance status, owner status, and traceability records synchronized with implementation evidence.
"""


def render_dashboard(projects: list[dict[str, Any]], meta: dict[str, str]) -> str:
    lines = [
        "# Governance Dashboard",
        "",
        f"- source_base_commit: `{meta['source_base_commit']}`",
        f"- source_tree_hash: `{meta['source_tree_hash']}`",
        f"- source_snapshot_hash: `{meta['source_snapshot_hash']}`",
        f"- snapshot_event_time: `{meta['snapshot_event_time']}`",
        f"- generator_version: `{GENERATOR_VERSION}`",
        "- final_commit_binding: `PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION`",
        "",
        "| Project | Version | Phase | Impl | Param Source | Empirical | Operational | Freshness | Readiness | Next |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for item in projects:
        assurance = item["assurance"]
        dims = assurance["dimensions"]
        next_task = assurance["next_executable_task"]["task_id"]
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{item['project_id']}`",
                    f"`{item['product_version']}`",
                    f"`{item['current_phase']}`",
                    f"`{dims['implementation_congruence']['status']}`",
                    f"`{dims['parameter_source_quality']['status']}`",
                    f"`{dims['empirical_validation']['status']}`",
                    f"`{dims['operational_validation']['status']}`",
                    f"`{dims['evidence_freshness']['status']}`",
                    f"`{assurance['delivery_readiness']['status']}`",
                    f"`{next_task}`",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Implementation congruence only means documented values and fingerprints match code/config sources.",
            "- Empirical validation and operational validation are separate dimensions and may remain UNVERIFIED, PARTIAL, or FAILED.",
            "- Branch protection details remain `UNVERIFIED` unless checked by authenticated GitHub API or UI evidence.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_owner_portfolio(projects: list[dict[str, Any]], meta: dict[str, str]) -> str:
    decision_projects = [item for item in projects if item["assurance"]["owner_decision"]["required"]]
    blockers: list[str] = []
    for item in projects:
        for blocker in item["policy_blockers"][:2]:
            blockers.append(f"{item['project_id']}: {blocker}")
    red = [item for item in projects if item["assurance"]["delivery_readiness"]["status"] == "FAILED"]
    yellow = [item for item in projects if item["assurance"]["delivery_readiness"]["status"] == "PARTIAL"]
    green = [
        item
        for item in projects
        if item["assurance"]["delivery_readiness"]["status"] in {"VERIFIED", "NOT_APPLICABLE"}
    ]
    next_task = next(
        (
            item["assurance"]["next_executable_task"]
            for item in projects
            if item["assurance"]["next_executable_task"]["task_id"] != "NONE"
        ),
        {"task_id": "NONE", "reason": "No executable governance task selected."},
    )
    lines = [
        "# OWNER_PORTFOLIO",
        "",
        "## 1. Overall Conclusion",
        "",
        "Review 7 governance is a portfolio control layer with automatic generated-view synchronization, full-repository read-only drift checks, and explicit evidence-binding backlog. It is not a production-readiness claim for every project.",
        "",
        "## 2. Immutable Snapshot",
        "",
        f"- source_base_commit: `{meta['source_base_commit']}`",
        f"- source_tree_hash: `{meta['source_tree_hash']}`",
        f"- source_snapshot_hash: `{meta['source_snapshot_hash']}`",
        f"- snapshot_event_time: `{meta['snapshot_event_time']}`",
        f"- generator_version: `{GENERATOR_VERSION}`",
        "- final_commit_binding: `PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION`",
        "- branch_protection: `UNVERIFIED` unless authenticated setup doctor evidence is attached",
        "",
        "## 3. Red Yellow Green",
        "",
        f"- red_FAILED: `{len(red)}`",
        f"- yellow_PARTIAL: `{len(yellow)}`",
        f"- green_VERIFIED_OR_NOT_APPLICABLE: `{len(green)}`",
        "",
        "## 4. Top 5 Blockers",
        "",
    ]
    for blocker in blockers[:5]:
        lines.append(f"- {blocker}")
    lines.extend(
        [
            "",
            "## 5. Owner Decisions",
            "",
            "| Decision | Default Recommendation | Option A | Option B | No Decision Consequence | Owner | Unblock Condition |",
            "|---|---|---|---|---|---|---|",
        ]
    )
    for item in decision_projects:
        decision = item["assurance"]["owner_decision"]
        task = item["assurance"]["next_executable_task"]
        lines.append(
            f"| `{decision['decision_id']}` | A: fund evidence hardening | {decision['options'][0]} | {decision['options'][1]} | remains `{item['assurance']['delivery_readiness']['status']}` | {task['owner']} | {task['unblock_condition']} |"
        )
    lines.extend(["", "## 6. Executable Tasks", ""])
    for item in projects:
        task = item["assurance"]["next_executable_task"]
        lines.append(f"- `{item['project_id']}`: `{task['task_id']}` - {task['reason']}")
    lines.extend(["", "## 7. Next Unique Governance Task", ""])
    lines.append(f"- `{next_task['task_id']}` - {next_task['reason']}")
    lines.extend(["", "## 8. Assurance Dimensions", ""])
    lines.append("| Project | Structural | Impl | Param Source | Empirical | Operational | Delivery | Freshness | Readiness | Owner action |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for item in projects:
        dims = item["assurance"]["dimensions"]
        lines.append(
            f"| `{item['project_id']}` | `{dims['structural_completeness']['status']}` | "
            f"`{dims['implementation_congruence']['status']}` | `{dims['parameter_source_quality']['status']}` | "
            f"`{dims['empirical_validation']['status']}` | `{dims['operational_validation']['status']}` | "
            f"`{dims['delivery_evidence']['status']}` | `{dims['evidence_freshness']['status']}` | "
            f"`{item['assurance']['delivery_readiness']['status']}` | {item['assurance']['owner_decision']['question']} |"
        )
    return "\n".join(lines) + "\n"


def render_status(item: dict[str, Any]) -> str:
    assurance = item["assurance"]
    dims = assurance["dimensions"]
    counts = item["counts"]
    return f"""# Project Governance Status

## Snapshot Metadata

- source_base_commit: `{assurance['source_base_commit']}`
- source_tree_hash: `{assurance['source_tree_hash']}`
- source_snapshot_hash: `{assurance['source_snapshot_hash']}`
- snapshot_event_time: `{assurance['snapshot_event_time']}`
- generator_version: `{GENERATOR_VERSION}`
- final_commit_binding: `PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION`

## Current State

- Project: `{item['project_id']}`
- Path: `{item['path']}`
- Product version: `{item['product_version']}`
- Phase/Gate: `{item['current_phase']} / {item['current_gate']}`
- Models/Formulas/Parameters total: `{item['models']} / {counts['total_formulas']} / {counts['total_parameters']}`
- Active formulas/parameters: `{counts['active_formulas']} / {counts['active_parameters']}`
- Machine checked formulas/parameters: `{counts['checked_formulas']} / {counts['checked_parameters']}`

## Assurance

| Dimension | Status | Evidence |
|---|---|---|
| structural_completeness | `{dims['structural_completeness']['status']}` | `{brief_list(dims['structural_completeness']['evidence_refs'])}` |
| implementation_congruence | `{dims['implementation_congruence']['status']}` | `{brief_list(dims['implementation_congruence']['evidence_refs'])}` |
| parameter_source_quality | `{dims['parameter_source_quality']['status']}` | `{brief_list(dims['parameter_source_quality']['evidence_refs'])}` |
| empirical_validation | `{dims['empirical_validation']['status']}` | `{brief_list(dims['empirical_validation']['evidence_refs'])}` |
| operational_validation | `{dims['operational_validation']['status']}` | `{brief_list(dims['operational_validation']['evidence_refs'])}` |
| delivery_evidence | `{dims['delivery_evidence']['status']}` | `{brief_list(dims['delivery_evidence']['evidence_refs'])}` |
| evidence_freshness | `{dims['evidence_freshness']['status']}` | `{brief_list(dims['evidence_freshness']['evidence_refs'])}` |

## Delivery

- Readiness: `{assurance['delivery_readiness']['status']}`
- Release gate: `{assurance['delivery_readiness']['release_gate']}`
- Next executable task: `{assurance['next_executable_task']['task_id']}`
- Pending/stale events: `{item['pending_event_count']}`
- Tree-bound events: `{item['event_binding_counts']['tree_bound_events']}`
- Commit-bound events: `{item['event_binding_counts']['commit_bound_events']}`
- Legacy unbound events: `{item['event_binding_counts']['legacy_unbound_events']}`
- Unresolved fact IDs: `{len(item['unresolved_fact_ids'])}`
"""


def render_owner_status(item: dict[str, Any]) -> str:
    assurance = item["assurance"]
    dims = assurance["dimensions"]
    counts = item["counts"]
    next_task = assurance["next_executable_task"]
    decision = assurance["owner_decision"]
    blockers = item["policy_blockers"][:3] or ["No blocker recorded."]
    option_a = decision["options"][0]
    option_b = decision["options"][1] if len(decision["options"]) > 1 else "B: defer"
    option_c = decision["options"][2] if len(decision["options"]) > 2 else "C: de-scope"
    return f"""# OWNER_STATUS

{item['project_id']} 当前治理结论：实现一致性为 `{dims['implementation_congruence']['status']}`，交付状态为 `{assurance['delivery_readiness']['status']}`；这不是生产上线声明。

## 1. Current Conclusion

- source_base_commit: `{assurance['source_base_commit']}`
- source_tree_hash: `{assurance['source_tree_hash']}`
- source_snapshot_hash: `{assurance['source_snapshot_hash']}`
- snapshot_event_time: `{assurance['snapshot_event_time']}`
- generator_version: `{GENERATOR_VERSION}`
- version: `{item['product_version']}`
- phase/gate: `{item['current_phase']} / {item['current_gate']}`

## 2. This Run Change

Generated owner-facing views now separate implementation congruence from parameter source quality, empirical validation, operational validation, delivery evidence, and evidence freshness.

## 3. Owner Impact

- structural_completeness: `{dims['structural_completeness']['status']}`
- implementation_congruence: `{dims['implementation_congruence']['status']}` ({counts['checked_parameters']}/{counts['active_parameters']} active parameters, {counts['checked_formulas']}/{counts['active_formulas']} active formulas)
- parameter_source_quality: `{dims['parameter_source_quality']['status']}`
- empirical_validation: `{dims['empirical_validation']['status']}`
- operational_validation: `{dims['operational_validation']['status']}`
- delivery_evidence: `{dims['delivery_evidence']['status']}`
- evidence_freshness: `{dims['evidence_freshness']['status']}`
- delivery_readiness: `{assurance['delivery_readiness']['status']}`

## 4. Decision Needed

- decision_id: `{decision['decision_id']}`
- question: {decision['question']}

## 5. A/B/C Choice Matrix

| Decision Item | Current Recommendation | Choice A | Choice B | Choice C | No Decision Consequence |
|---|---|---|---|---|---|
| `{decision['decision_id']}` | A | {option_a} | {option_b} | {option_c} | remains `{assurance['delivery_readiness']['status']}` with unresolved evidence. |

## 6. Current Blockers

1. {blockers[0]}
2. {blockers[1] if len(blockers) > 1 else 'No second blocker recorded.'}
3. {blockers[2] if len(blockers) > 2 else 'No third blocker recorded.'}

## 7. Evidence Required To Unblock

- owner: {next_task['owner']}
- unblock_condition: {next_task['unblock_condition']}
- acceptance: {brief_list([str(x) for x in next_task.get('acceptance_ids', [])])}

## 8. Model Formula Parameter Change

- model_count: `{item['models']}`
- total_formulas: `{counts['total_formulas']}`
- active_formulas: `{counts['active_formulas']}`
- total_parameters: `{counts['total_parameters']}`
- active_parameters: `{counts['active_parameters']}`
- active_values_changed_by_this_view: `0`

## 9. Tests And Acceptance

- required_commands: `validate_project_governance --all --semantic --drift-report`; `generate_governance_dashboard --write`
- release_gate: `{assurance['delivery_readiness']['release_gate']}`

## 10. Evidence Freshness

- tree_bound_events: `{item['event_binding_counts']['tree_bound_events']}`
- commit_bound_events: `{item['event_binding_counts']['commit_bound_events']}`
- legacy_unbound_events: `{item['event_binding_counts']['legacy_unbound_events']}`
- precommit_pending_events: `{item['event_binding_counts']['precommit_pending_events']}`
- pending_or_stale_events: `{item['pending_event_count']}`

## 11. UNKNOWN

- unresolved_fact_ids: `{len(item['unresolved_fact_ids'])}`

## 12. Next Unique Task

- task_id: `{next_task['task_id']}`
- reason: {next_task['reason']}
"""


def render_binding_backlog(projects: list[dict[str, Any]], meta: dict[str, str]) -> str:
    payload = {
        "generated_by": "scripts/generate_governance_dashboard.py",
        "generator_version": GENERATOR_VERSION,
        "task_id": "GOV-REVIEW7-BINDING-BACKLOG-001",
        "source_base_commit": meta["source_base_commit"],
        "source_tree_hash": meta["source_tree_hash"],
        "source_snapshot_hash": meta["source_snapshot_hash"],
        "status": "open",
        "policy": "Legacy events are not rewritten. Future meaningful runs must be PRECOMMIT_TREE_BOUND before commit and commit-bound by CI attestation after merge.",
        "projects": [
            {
                "project_id": item["project_id"],
                "tree_bound_events": item["event_binding_counts"]["tree_bound_events"],
                "commit_bound_events": item["event_binding_counts"]["commit_bound_events"],
                "legacy_unbound_events": item["event_binding_counts"]["legacy_unbound_events"],
                "precommit_pending_events": item["event_binding_counts"]["precommit_pending_events"],
                "next_task": "GOV-REVIEW7-BINDING-BACKLOG-001"
                if item["event_binding_counts"]["legacy_unbound_events"]
                else "NOT_APPLICABLE",
            }
            for item in projects
        ],
    }
    return "\n".join(dump_yaml(payload)) + "\n"


ROOT_OUTPUT_REL_PATHS = [
    "README.md",
    "GOVERNANCE_DASHBOARD.md",
    "OWNER_PORTFOLIO.md",
    "governance/binding_backlog.yaml",
]


def select_projects(
    projects: list[dict[str, Any]], *, project_filter: str | None = None, changed_only: bool = False, base_ref: str | None = None
) -> tuple[list[dict[str, Any]], bool]:
    if project_filter:
        selected = [
            project
            for project in projects
            if project_filter in {str(project.get("project_id")), str(project.get("path"))}
        ]
        if not selected:
            raise SystemExit(f"Unknown project: {project_filter}")
        return selected, False
    if changed_only:
        changed = structural.git_changed_files(base_ref)
        selected = [project for project in projects if structural.project_matches_changed(project, changed)]
        include_root = any(path in changed for path in ROOT_OUTPUT_REL_PATHS)
        return selected, include_root
    return projects, True


def generate(write: bool, *, project_filter: str | None = None, changed_only: bool = False, base_ref: str | None = None) -> dict[str, Any]:
    config = structural.load_yaml(structural.PROJECTS_FILE)
    projects = [project for project in structural.as_list(config.get("projects")) if isinstance(project, dict)]
    selected_projects, include_root = select_projects(projects, project_filter=project_filter, changed_only=changed_only, base_ref=base_ref)
    infos = [load_project(project) for project in selected_projects]
    all_infos = [load_project(project) for project in projects] if include_root else infos
    portfolio_hash = source_snapshot_hash(
        [ROOT / "governance/projects.yaml"] + [ROOT / i["path"] / "docs/governance/parameter_registry.csv" for i in all_infos]
    )
    event_times = [info["assurance"]["snapshot_event_time"] for info in all_infos if info["assurance"]["snapshot_event_time"] != "UNKNOWN"]
    meta = {
        "source_base_commit": configured_source_base() or existing_root_base() or current_commit(),
        "source_tree_hash": configured_source_tree() or existing_root_tree() or current_tree_hash(),
        "source_snapshot_hash": portfolio_hash,
        "snapshot_event_time": max(event_times) if event_times else "UNKNOWN",
    }
    outputs: list[str] = []
    if include_root:
        root_outputs = {
            ROOT / "README.md": render_readme(all_infos, meta),
            ROOT / "GOVERNANCE_DASHBOARD.md": render_dashboard(all_infos, meta),
            ROOT / "OWNER_PORTFOLIO.md": render_owner_portfolio(all_infos, meta),
            ROOT / "governance" / "binding_backlog.yaml": render_binding_backlog(all_infos, meta),
        }
        for path, text in root_outputs.items():
            if write:
                path.write_text(text, encoding="utf-8")
            outputs.append(rel(path))
    for info in infos:
        base = ROOT / info["path"] / "docs/governance"
        assurance_path = base / "ASSURANCE_STATUS.yaml"
        assurance_text = "\n".join(dump_yaml(info["assurance"])) + "\n"
        status_path = base / "STATUS.md"
        owner_path = base / "OWNER_STATUS.md"
        if write:
            assurance_path.write_text(assurance_text, encoding="utf-8")
            status_path.write_text(render_status(info), encoding="utf-8")
            owner_path.write_text(render_owner_status(info), encoding="utf-8")
        outputs.extend([rel(assurance_path), rel(status_path), rel(owner_path)])
    return {
        "status": "PASS",
        "write": write,
        "source_base_commit": meta["source_base_commit"],
        "source_snapshot_hash": meta["source_snapshot_hash"],
        "snapshot_event_time": meta["snapshot_event_time"],
        "generator_version": GENERATOR_VERSION,
        "outputs": outputs,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Write generated governance views.")
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument("--all", action="store_true", help="Generate all root and project governance views.")
    scope.add_argument("--project", help="Generate governance views for one project id or path.")
    scope.add_argument("--changed-only", action="store_true", help="Generate governance views for changed projects only.")
    parser.add_argument("--base-ref", help="Optional base ref for --changed-only.")
    args = parser.parse_args()
    print(
        json.dumps(
            generate(args.write, project_filter=args.project, changed_only=args.changed_only, base_ref=args.base_ref),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
