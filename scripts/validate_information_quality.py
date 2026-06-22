#!/usr/bin/env python3
"""Review 6 information-quality gate for CodexProject governance."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import validate_project_governance as structural
import generate_governance_dashboard as dashboard


sys.dont_write_bytecode = True

ROOT = structural.ROOT
EXPECTED_PROJECTS = {
    "Alpha": "Alpha",
    "EEI": "EEI",
    "EVA_OS": "EVA_OS",
    "FIFA": "FIFA",
    "OpMe_System": "OpMe_System",
    "OpenAIDatabase": "OpenAIDatabase",
    "PFI_BIG_DATA_SIMULATOR": "PFI/大数据模拟器",
    "Serenity-Alipay": "Serenity-Alipay",
    "whkmSalary": "whkmSalary",
    "arxiv-daily-push": "arxiv-daily-push",
}
PLACEHOLDERS = ("DETERMINISTIC_GENERATION", "CURRENT_CHECKOUT", "CURRENT_CHECKOUT_TREE")
DIMENSION_STATUSES = {
    "structural_validation": {"pass", "fail"},
    "implementation_congruence": {"machine_verified", "partial", "blocked", "not_applicable"},
    "empirical_validation": {"verified", "partial", "unknown", "not_applicable"},
    "operational_evidence": {"verified", "partial", "blocked", "unknown", "not_applicable"},
}


@dataclass
class Finding:
    severity: str
    code: str
    message: str
    path: str = ""
    project: str = ""


class Gate:
    def __init__(self) -> None:
        self.findings: list[Finding] = []

    def add(self, severity: str, code: str, message: str, path: str | Path = "", project: str = "") -> None:
        if isinstance(path, Path):
            try:
                path = str(path.relative_to(ROOT))
            except ValueError:
                path = str(path)
        self.findings.append(Finding(severity, code, message, str(path), project))

    @property
    def errors(self) -> list[Finding]:
        return [item for item in self.findings if item.severity == "ERROR"]


def project_config() -> list[dict[str, Any]]:
    data = structural.load_yaml(structural.PROJECTS_FILE)
    if not isinstance(data, dict):
        return []
    return [item for item in structural.as_list(data.get("projects")) if isinstance(item, dict)]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def active_counts(base: Path) -> dict[str, int]:
    params = read_csv(base / "docs/governance/parameter_registry.csv")
    active_params = [row for row in params if str(row.get("status") or "").lower() == "active"]
    checked_params = [
        row
        for row in active_params
        if row.get("source_selector") and row.get("extracted_value") not in {None, ""} and row.get("evidence_hash")
    ]
    formula_data = structural.load_yaml(base / "docs/governance/formula_registry.yaml")
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
        "total_active_parameters": len(active_params),
        "checked_active_parameters": len(checked_params),
        "total_active_formulas": len(active_formulas),
        "checked_active_formulas": len(checked_formulas),
    }


def parse_time(value: str) -> datetime | None:
    if not value:
        return None
    value = value.strip()
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def generated_paths(projects: list[dict[str, Any]]) -> list[Path]:
    paths = [ROOT / "README.md", ROOT / "GOVERNANCE_DASHBOARD.md", ROOT / "OWNER_PORTFOLIO.md"]
    for project in projects:
        base = ROOT / str(project.get("path")) / "docs/governance"
        paths.extend([base / "STATUS.md", base / "OWNER_STATUS.md"])
    return paths


def check_project_set(gate: Gate, projects: list[dict[str, Any]]) -> None:
    actual = {str(item.get("project_id")): str(item.get("path")) for item in projects}
    if actual != EXPECTED_PROJECTS:
        gate.add("ERROR", "PROJECT_SET", f"Expected {EXPECTED_PROJECTS!r}, got {actual!r}", "governance/projects.yaml")
    readme = (ROOT / "README.md").read_text(encoding="utf-8") if (ROOT / "README.md").exists() else ""
    for project_id, rel in EXPECTED_PROJECTS.items():
        if not (ROOT / rel).is_dir():
            gate.add("ERROR", "PROJECT_DIR", "Expected project directory is missing", rel, project_id)
        if project_id not in readme and rel not in readme:
            gate.add("ERROR", "README_PROJECT", "README omits project", "README.md", project_id)


def check_generated_views(gate: Gate, projects: list[dict[str, Any]]) -> None:
    for path in generated_paths(projects):
        if not path.exists():
            gate.add("ERROR", "GENERATED_MISSING", "Generated view is missing", path)
            continue
        text = path.read_text(encoding="utf-8")
        for token in PLACEHOLDERS:
            if token in text:
                gate.add("ERROR", "PLACEHOLDER", f"Generated view contains {token}", path)
        for key in ("source_base_commit", "source_snapshot_hash", "generator_version"):
            if key not in text:
                gate.add("ERROR", "METADATA", f"Generated view lacks {key}", path)
        for line_no, line in enumerate(text.splitlines(), 1):
            if len(line) > 500:
                gate.add("ERROR", "LONG_LINE", f"Line {line_no} exceeds 500 characters", path)


def check_assurance(gate: Gate, project: dict[str, Any]) -> None:
    project_id = str(project.get("project_id"))
    base = ROOT / str(project.get("path"))
    path = base / "docs/governance/ASSURANCE_STATUS.yaml"
    data = structural.load_yaml(path)
    if not isinstance(data, dict):
        gate.add("ERROR", "ASSURANCE_PARSE", "ASSURANCE_STATUS.yaml is missing or invalid", path, project_id)
        return
    if str(data.get("project_id")) != project_id:
        gate.add("ERROR", "ASSURANCE_PROJECT", "project_id mismatch", path, project_id)
    if not re.fullmatch(r"[0-9a-f]{40}", str(data.get("source_base_commit") or "")):
        gate.add("ERROR", "ASSURANCE_COMMIT", "source_base_commit is not a 40-hex commit", path, project_id)
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", str(data.get("source_snapshot_hash") or "")):
        gate.add("ERROR", "ASSURANCE_HASH", "source_snapshot_hash is not sha256:<64hex>", path, project_id)
    if str(data.get("generator_version") or "") != dashboard.GENERATOR_VERSION:
        gate.add("ERROR", "ASSURANCE_GENERATOR", "generator_version mismatch", path, project_id)
    dims = data.get("dimensions") if isinstance(data.get("dimensions"), dict) else {}
    for name, allowed in DIMENSION_STATUSES.items():
        value = dims.get(name) if isinstance(dims.get(name), dict) else {}
        status = str(value.get("status") or "")
        if status not in allowed:
            gate.add("ERROR", "DIMENSION_STATUS", f"{name} has invalid status {status!r}", path, project_id)
    impl = dims.get("implementation_congruence") if isinstance(dims.get("implementation_congruence"), dict) else {}
    counts = active_counts(base)
    for key, expected in counts.items():
        if impl.get(key) != expected:
            gate.add("ERROR", "ASSURANCE_COUNT", f"{key}={impl.get(key)!r}, expected {expected}", path, project_id)
    if impl.get("status") == "machine_verified" and (
        counts["checked_active_parameters"] != counts["total_active_parameters"]
        or counts["checked_active_formulas"] != counts["total_active_formulas"]
    ):
        gate.add("ERROR", "FALSE_MACHINE_VERIFIED", "machine_verified with incomplete active coverage", path, project_id)
    readiness = data.get("delivery_readiness") if isinstance(data.get("delivery_readiness"), dict) else {}
    if str(readiness.get("status") or "") not in {"ready", "conditional", "blocked"}:
        gate.add("ERROR", "READINESS_STATUS", "Invalid delivery_readiness status", path, project_id)
    check_next_task(gate, data, base, project_id)


def check_next_task(gate: Gate, assurance: dict[str, Any], base: Path, project_id: str) -> None:
    task_data = structural.load_yaml(base / "docs/governance/delivery_tasks.yaml")
    tasks = [item for item in structural.as_list(task_data.get("tasks")) if isinstance(item, dict)] if isinstance(task_data, dict) else []
    by_id = {str(task.get("task_id")): task for task in tasks}
    completed = {task_id for task_id, task in by_id.items() if str(task.get("status") or "") == "completed"}
    next_task = assurance.get("next_executable_task") if isinstance(assurance.get("next_executable_task"), dict) else {}
    task_id = str(next_task.get("task_id") or "")
    if task_id == "NONE":
        return
    task = by_id.get(task_id)
    if not task:
        gate.add("ERROR", "NEXT_TASK_MISSING", "next_executable_task does not exist", base, project_id)
        return
    status = str(task.get("status") or "")
    if status not in {"ready", "in_progress"}:
        gate.add("ERROR", "NEXT_TASK_STATUS", f"Task {task_id} has non-executable status {status}", base, project_id)
    unmet = [str(dep) for dep in structural.as_list(task.get("dependencies")) if str(dep) and str(dep) not in completed]
    if unmet:
        gate.add("ERROR", "NEXT_TASK_DEPS", f"Task {task_id} has unmet dependencies {unmet}", base, project_id)
    if not task.get("acceptance_ids"):
        gate.add("ERROR", "NEXT_TASK_ACCEPTANCE", f"Task {task_id} lacks acceptance_ids", base, project_id)
    if not task.get("test_commands"):
        gate.add("ERROR", "NEXT_TASK_TEST", f"Task {task_id} lacks test_commands", base, project_id)


def check_events(gate: Gate, project: dict[str, Any]) -> None:
    project_id = str(project.get("project_id"))
    path = ROOT / str(project.get("path")) / "docs/governance/development_events.jsonl"
    if not path.exists():
        gate.add("ERROR", "EVENT_FILE", "development_events.jsonl missing", path, project_id)
        return
    now = datetime.now(timezone.utc)
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            gate.add("ERROR", "EVENT_JSON", f"Line {lineno}: {exc}", path, project_id)
            continue
        dt = parse_time(str(event.get("timestamp") or event.get("date") or ""))
        if dt and dt > now + timedelta(minutes=5):
            gate.add("ERROR", "FUTURE_EVENT", f"Line {lineno} timestamp is in the future", path, project_id)
        commit = str(event.get("result_commit") or event.get("git_commit") or "").upper()
        if commit in {"", "PENDING", "PENDING_CI"}:
            binding = str(event.get("binding_status") or "")
            if binding not in {"pre_commit_pending", "ci_attested", "stale_unbound"}:
                gate.add("ERROR", "EVENT_BINDING", f"Line {lineno} pending event lacks binding_status", path, project_id)
            if dt and now - dt > timedelta(hours=24) and binding != "stale_unbound" and not event.get("ci_attestation_ref"):
                gate.add("ERROR", "STALE_PENDING", f"Line {lineno} stale pending event is not classified", path, project_id)


def check_hook_and_ci(gate: Gate) -> None:
    hook = ROOT / ".codex/hooks/governance_stop.py"
    workflow = ROOT / ".github/workflows/project-governance.yml"
    for path, code in ((hook, "HOOK_QUALITY"), (workflow, "CI_QUALITY")):
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        if "validate_information_quality.py" not in text or "--all" not in text or "--fast" not in text:
            gate.add("ERROR", code, "information-quality all-fast gate is not wired", path)
    if workflow.exists():
        text = workflow.read_text(encoding="utf-8")
        if "--all --semantic --drift-report" not in text:
            gate.add("ERROR", "CI_DRIFT", "all semantic drift check missing", workflow)
        if "OWNER_PORTFOLIO.md" not in text:
            gate.add("ERROR", "CI_PORTFOLIO", "OWNER_PORTFOLIO drift check missing", workflow)
        if re.search(r"(?m)^\s*continue-on-error\s*:", text):
            gate.add("ERROR", "CI_MASKING", "continue-on-error is not allowed", workflow)


def run(project_filter: str | None = None) -> dict[str, Any]:
    gate = Gate()
    projects = project_config()
    if project_filter:
        projects = [
            project
            for project in projects
            if project_filter in {str(project.get("project_id")), str(project.get("path"))}
        ]
        if not projects:
            gate.add("ERROR", "PROJECT_FILTER", f"No project matches {project_filter!r}")
    else:
        check_project_set(gate, projects)
    check_generated_views(gate, projects)
    check_hook_and_ci(gate)
    for project in projects:
        check_assurance(gate, project)
        check_events(gate, project)
    return {
        "status": "PASS" if not gate.errors else "FAIL",
        "errors": len(gate.errors),
        "warnings": sum(1 for item in gate.findings if item.severity == "WARNING"),
        "findings": [asdict(item) for item in gate.findings],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument("--all", action="store_true", help="Validate all registered projects.")
    scope.add_argument("--project", help="Project id or path.")
    parser.add_argument("--fast", action="store_true", help="Reserved for CI fast mode; all current checks are fast.")
    parser.add_argument("--fail-on-error", action="store_true", help="Return non-zero on errors.")
    parser.add_argument("--json-out", help="Write JSON result to a file.")
    args = parser.parse_args(argv)
    result = run(args.project)
    if args.json_out:
        out = Path(args.json_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if args.fail_on_error and result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
