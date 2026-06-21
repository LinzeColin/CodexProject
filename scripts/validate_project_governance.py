#!/usr/bin/env python3
"""Validate CodexProject root and project governance files."""

from __future__ import annotations

import argparse
import csv
import fnmatch
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
PROJECTS_FILE = ROOT / "governance" / "projects.yaml"

FACT_LEVELS = {"EXTRACTED", "RECONSTRUCTED", "PROPOSED", "UNKNOWN", "NOT_APPLICABLE"}
MODEL_STATES = {"active", "planned", "deprecated", "not_applicable"}
FORMULA_STATES = {"active", "planned", "deprecated", "not_applicable"}
PARAMETER_STATES = {"active", "planned", "deprecated", "not_applicable"}
TASK_STATES = {
    "proposed",
    "planned",
    "ready",
    "in_progress",
    "blocked",
    "completed",
    "rejected",
    "deprecated",
}
SEMANTIC_COVERAGE_STATES = {
    "machine_verified",
    "planned",
    "in_progress",
    "blocked",
    "not_applicable",
}
PROJECT_MARKERS = {
    "README.md",
    "AGENTS.md",
    "HANDOFF.md",
    "VERSION",
    "CHANGELOG.md",
    "package.json",
    "pyproject.toml",
    "requirements.txt",
}
INFRA_DIRS = {
    ".agents",
    ".codex",
    ".git",
    ".github",
    ".pytest_cache",
    ".venv",
    "artifacts",
    "backups",
    "docs",
    "generated-artifacts",
    "governance",
    "node_modules",
    "outputs",
    "scripts",
    "venv",
}
PARAMETER_REQUIRED_COLUMNS = [
    "parameter_id",
    "model_id",
    "formula_id",
    "symbol",
    "name",
    "category",
    "data_type",
    "unit",
    "default_value",
    "initial_or_prior_value",
    "active_value",
    "weight",
    "weight_group",
    "weight_group_target",
    "weight_group_tolerance",
    "min_value",
    "max_value",
    "formula_or_transform",
    "source_or_rationale",
    "calibration_method",
    "sensitivity",
    "code_ref",
    "config_ref",
    "test_ref",
    "status",
    "fact_level",
    "unknown_task_ids",
    "parameter_version",
    "last_updated",
]
TRACEABILITY_REQUIRED_COLUMNS = [
    "requirement_id",
    "model_id",
    "assumption_id",
    "formula_id",
    "parameter_id",
    "task_id",
    "acceptance_id",
    "code_ref",
    "config_ref",
    "test_ref",
    "evidence_ref",
    "status",
]


@dataclass
class Issue:
    level: str
    scope: str
    message: str


class Validation:
    def __init__(self) -> None:
        self.issues: list[Issue] = []

    def error(self, scope: str, message: str) -> None:
        self.issues.append(Issue("ERROR", scope, message))

    def warn(self, scope: str, message: str) -> None:
        self.issues.append(Issue("WARN", scope, message))

    def add(self, required: bool, scope: str, message: str) -> None:
        if required:
            self.error(scope, message)
        else:
            self.warn(scope, message)

    @property
    def errors(self) -> list[Issue]:
        return [issue for issue in self.issues if issue.level == "ERROR"]

    @property
    def warnings(self) -> list[Issue]:
        return [issue for issue in self.issues if issue.level == "WARN"]


def strip_comment(line: str) -> str:
    in_single = False
    in_double = False
    escaped = False
    for idx, char in enumerate(line):
        if char == "\\" and not escaped:
            escaped = True
            continue
        if char == "'" and not in_double and not escaped:
            in_single = not in_single
        elif char == '"' and not in_single and not escaped:
            in_double = not in_double
        elif char == "#" and not in_single and not in_double:
            return line[:idx].rstrip()
        escaped = False
    return line.rstrip()


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if value == "":
        return ""
    if value in {"[]", "null", "Null", "NULL", "~"}:
        return [] if value == "[]" else None
    if value in {"{}", "dict()"}:
        return {}
    if value in {"true", "True", "TRUE"}:
        return True
    if value in {"false", "False", "FALSE"}:
        return False
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [parse_scalar(part.strip()) for part in inner.split(",")]
    try:
        if re.fullmatch(r"-?\d+", value):
            return int(value)
        if re.fullmatch(r"-?\d+\.\d+", value):
            return float(value)
    except ValueError:
        pass
    return value


def split_key_value(text: str) -> tuple[str, str | None]:
    if ":" not in text:
        return text.strip(), None
    key, value = text.split(":", 1)
    return key.strip(), value.strip()


def fallback_yaml_load(text: str) -> Any:
    lines: list[tuple[int, str]] = []
    for raw in text.splitlines():
        cleaned = strip_comment(raw)
        if not cleaned.strip():
            continue
        indent = len(cleaned) - len(cleaned.lstrip(" "))
        lines.append((indent, cleaned.strip()))
    if not lines:
        return {}

    def parse_block(index: int, indent: int) -> tuple[Any, int]:
        if index >= len(lines):
            return {}, index
        if lines[index][1].startswith("- "):
            result: list[Any] = []
            while index < len(lines) and lines[index][0] == indent and lines[index][1].startswith("- "):
                item_text = lines[index][1][2:].strip()
                index += 1
                if item_text == "":
                    child_indent = lines[index][0] if index < len(lines) else indent + 2
                    item, index = parse_block(index, child_indent)
                    result.append(item)
                    continue
                key, value = split_key_value(item_text)
                if value is None:
                    result.append(parse_scalar(item_text))
                    continue
                item_map: dict[str, Any] = {key: parse_scalar(value) if value != "" else {}}
                while index < len(lines) and lines[index][0] > indent:
                    child_indent, child_text = lines[index]
                    child_key, child_value = split_key_value(child_text)
                    if child_value is None:
                        break
                    if child_value == "":
                        next_index = index + 1
                        if next_index < len(lines) and lines[next_index][0] > child_indent:
                            child, index = parse_block(next_index, lines[next_index][0])
                            item_map[child_key] = child
                        else:
                            item_map[child_key] = {}
                            index += 1
                    else:
                        item_map[child_key] = parse_scalar(child_value)
                        index += 1
                result.append(item_map)
            return result, index

        result_map: dict[str, Any] = {}
        while index < len(lines) and lines[index][0] == indent and not lines[index][1].startswith("- "):
            key, value = split_key_value(lines[index][1])
            if value is None:
                raise ValueError(f"Invalid YAML line: {lines[index][1]}")
            if value == "":
                next_index = index + 1
                if next_index < len(lines) and lines[next_index][0] > indent:
                    child, index = parse_block(next_index, lines[next_index][0])
                    result_map[key] = child
                else:
                    result_map[key] = {}
                    index += 1
            else:
                result_map[key] = parse_scalar(value)
                index += 1
        return result_map, index

    parsed, end = parse_block(0, lines[0][0])
    if end != len(lines):
        raise ValueError(f"Could not parse YAML near line: {lines[end][1]}")
    return parsed


def load_yaml(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        return yaml.safe_load(text) or {}
    except ModuleNotFoundError:
        return fallback_yaml_load(text)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[Any]:
    rows: list[Any] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{line_no}: invalid JSONL: {exc}") from exc
    return rows


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if value == "":
        return []
    return [value]


def value_present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip() != ""
    if isinstance(value, list):
        return len(value) > 0
    if isinstance(value, dict):
        return len(value) > 0
    return True


def contains_unknown(value: Any) -> bool:
    if isinstance(value, str):
        return bool(re.search(r"\bUNKNOWN\b|\bTBD\b", value, re.IGNORECASE))
    if isinstance(value, list):
        return any(contains_unknown(item) for item in value)
    if isinstance(value, dict):
        return any(contains_unknown(item) for item in value.values())
    return False


def has_unknown_task_ref(item: dict[str, Any]) -> bool:
    for key in ("unknown_task_ids", "open_task_ids", "task_ids", "task_id"):
        if value_present(item.get(key)):
            return True
    for key in ("source_or_rationale", "evidence_refs", "notes"):
        value = item.get(key)
        if isinstance(value, str) and re.search(r"[A-Z]+-[0-9]{3,}|GOV-[A-Z0-9_.-]+", value):
            return True
        if isinstance(value, list) and any(re.search(r"[A-Z]+-[0-9]{3,}|GOV-[A-Z0-9_.-]+", str(v)) for v in value):
            return True
    return False


def is_required(project: dict[str, Any], mode: str | None = None) -> bool:
    if mode == "required":
        return True
    if mode == "advisory":
        return False
    return str(project.get("ci_mode") or "").lower() == "required"


def project_scope(project: dict[str, Any]) -> str:
    return str(project.get("project_id") or project.get("path") or "unknown-project")


def validate_semantic_coverage_config(
    validation: Validation,
    project: dict[str, Any],
    required: bool,
    scope: str,
) -> None:
    coverage = project.get("semantic_coverage")
    if not isinstance(coverage, dict):
        validation.add(required, scope, "Missing semantic_coverage rollout contract")
        return
    status = str(coverage.get("status") or "").strip()
    if status not in SEMANTIC_COVERAGE_STATES:
        validation.add(required, scope, f"Invalid semantic_coverage.status: {status or '<empty>'}")
        return
    for field in ("task_id", "acceptance_id", "target", "owner", "rationale"):
        if not value_present(coverage.get(field)):
            validation.add(required, scope, f"semantic_coverage.{field} is required")
    if status == "machine_verified":
        if not bool(project.get("semantic_extractors")):
            validation.add(required, scope, "semantic_coverage.status=machine_verified requires semantic_extractors: true")
        if not value_present(coverage.get("evidence_ref")):
            validation.add(required, scope, "semantic_coverage.machine_verified requires evidence_ref")
    elif bool(project.get("semantic_extractors")):
        validation.add(required, scope, "semantic_extractors: true requires semantic_coverage.status=machine_verified")
    if status == "not_applicable" and not value_present(coverage.get("evidence_ref")):
        validation.add(required, scope, "semantic_coverage.not_applicable requires evidence_ref")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def check_file_nonempty(validation: Validation, path: Path, required: bool, scope: str) -> bool:
    if not path.exists():
        validation.add(required, scope, f"Missing file: {rel(path)}")
        return False
    if path.is_file() and path.stat().st_size == 0:
        validation.add(required, scope, f"Empty file: {rel(path)}")
        return False
    return True


def check_unique(validation: Validation, items: Iterable[dict[str, Any]], key: str, scope: str, required: bool) -> None:
    seen: dict[str, int] = {}
    for idx, item in enumerate(items, start=1):
        identifier = str(item.get(key) or "").strip()
        if not identifier:
            validation.add(required, scope, f"Item #{idx} missing {key}")
            continue
        seen[identifier] = seen.get(identifier, 0) + 1
    for identifier, count in seen.items():
        if count > 1:
            validation.add(required, scope, f"Duplicate {key}: {identifier}")


def discover_project_dirs() -> list[str]:
    candidates: set[str] = set()
    for path in ROOT.iterdir():
        if not path.is_dir() or path.name in INFRA_DIRS:
            continue
        direct_marker = any((path / marker).exists() for marker in PROJECT_MARKERS)
        child_projects = [
            child
            for child in path.iterdir()
            if child.is_dir()
            and child.name not in INFRA_DIRS
            and any((child / marker).exists() for marker in PROJECT_MARKERS)
        ]
        if direct_marker:
            candidates.add(rel(path))
        if child_projects and not direct_marker:
            for child in child_projects:
                candidates.add(rel(child))
    return sorted(candidates)


def parse_project_governance(project_path: Path, validation: Validation, required: bool, scope: str) -> dict[str, Any]:
    docs = project_path / "docs" / "governance"
    parsed: dict[str, Any] = {
        "models": [],
        "assumptions": [],
        "formulas": [],
        "parameters": [],
        "tasks": [],
        "events": [],
        "traceability": [],
        "version_matrix": {},
        "parameter_fields": [],
        "traceability_fields": [],
    }
    files = {
        "model_registry": docs / "model_registry.yaml",
        "formula_registry": docs / "formula_registry.yaml",
        "parameter_registry": docs / "parameter_registry.csv",
        "delivery_tasks": docs / "delivery_tasks.yaml",
        "development_events": docs / "development_events.jsonl",
        "version_matrix": docs / "VERSION_MATRIX.yaml",
        "traceability_matrix": docs / "TRACEABILITY_MATRIX.csv",
    }
    try:
        if files["model_registry"].exists():
            data = load_yaml(files["model_registry"])
            if isinstance(data, dict):
                parsed["models"] = as_list(data.get("models"))
                parsed["assumptions"] = as_list(data.get("assumptions"))
            else:
                parsed["models"] = as_list(data)
        if files["formula_registry"].exists():
            data = load_yaml(files["formula_registry"])
            parsed["formulas"] = as_list(data.get("formulas") if isinstance(data, dict) else data)
        if files["parameter_registry"].exists():
            with files["parameter_registry"].open(newline="", encoding="utf-8") as handle:
                reader = csv.DictReader(handle)
                parsed["parameter_fields"] = reader.fieldnames or []
                parsed["parameters"] = list(reader)
        if files["delivery_tasks"].exists():
            data = load_yaml(files["delivery_tasks"])
            parsed["tasks"] = as_list(data.get("tasks") if isinstance(data, dict) else data)
        if files["development_events"].exists():
            parsed["events"] = load_jsonl(files["development_events"])
        if files["version_matrix"].exists():
            parsed["version_matrix"] = load_yaml(files["version_matrix"])
        if files["traceability_matrix"].exists():
            with files["traceability_matrix"].open(newline="", encoding="utf-8") as handle:
                reader = csv.DictReader(handle)
                parsed["traceability_fields"] = reader.fieldnames or []
                parsed["traceability"] = list(reader)
    except Exception as exc:
        validation.add(required, scope, f"Parse failure: {exc}")
    return parsed


def collect_assumption_ids(models: list[dict[str, Any]], root_assumptions: list[dict[str, Any]]) -> set[str]:
    assumption_ids: set[str] = set()
    for assumption in root_assumptions:
        if isinstance(assumption, dict) and assumption.get("assumption_id"):
            assumption_ids.add(str(assumption["assumption_id"]))
    for model in models:
        for assumption in as_list(model.get("assumptions")):
            if isinstance(assumption, dict) and assumption.get("assumption_id"):
                assumption_ids.add(str(assumption["assumption_id"]))
            elif isinstance(assumption, str) and assumption.startswith("ASM-"):
                assumption_ids.add(assumption)
        for assumption_id in as_list(model.get("assumption_ids")):
            if assumption_id:
                assumption_ids.add(str(assumption_id))
    return assumption_ids


def check_unknown_refs(validation: Validation, items: Iterable[dict[str, Any]], item_key: str, required: bool, scope: str) -> None:
    for item in items:
        identifier = str(item.get(item_key) or "<missing-id>")
        if contains_unknown(item) and not has_unknown_task_ref(item):
            validation.add(required, scope, f"{identifier}: UNKNOWN/TBD value lacks unresolved task reference")


def check_cross_references(validation: Validation, parsed: dict[str, Any], required: bool, scope: str) -> None:
    models = [m for m in parsed["models"] if isinstance(m, dict)]
    root_assumptions = [a for a in parsed["assumptions"] if isinstance(a, dict)]
    formulas = [f for f in parsed["formulas"] if isinstance(f, dict)]
    parameters = [p for p in parsed["parameters"] if isinstance(p, dict)]
    tasks = [t for t in parsed["tasks"] if isinstance(t, dict)]
    events = [e for e in parsed["events"] if isinstance(e, dict)]

    check_unique(validation, models, "model_id", scope, required)
    check_unique(validation, root_assumptions, "assumption_id", scope, required)
    check_unique(validation, formulas, "formula_id", scope, required)
    check_unique(validation, parameters, "parameter_id", scope, required)
    check_unique(validation, tasks, "task_id", scope, required)
    check_unique(validation, events, "event_id", scope, required)

    model_ids = {str(m.get("model_id")) for m in models if m.get("model_id")}
    formula_ids = {str(f.get("formula_id")) for f in formulas if f.get("formula_id")}
    parameter_ids = {str(p.get("parameter_id")) for p in parameters if p.get("parameter_id")}
    assumption_ids = collect_assumption_ids(models, root_assumptions)

    for model in models:
        model_id = str(model.get("model_id") or "<missing-model-id>")
        status = str(model.get("status") or "").lower()
        fact_level = model.get("fact_level")
        if status and status not in MODEL_STATES:
            validation.add(required, scope, f"{model_id}: invalid model status {status}")
        if fact_level and fact_level not in FACT_LEVELS:
            validation.add(required, scope, f"{model_id}: invalid fact_level {fact_level}")
        for formula_id in [str(item) for item in as_list(model.get("formula_ids"))]:
            if formula_id and formula_id not in formula_ids:
                validation.add(required, scope, f"{model_id}: missing formula reference {formula_id}")
        for parameter_id in [str(item) for item in as_list(model.get("parameter_ids"))]:
            if parameter_id and parameter_id not in parameter_ids:
                validation.add(required, scope, f"{model_id}: missing parameter reference {parameter_id}")
        if status == "active":
            if not value_present(model.get("formula_ids")) and model.get("fact_level") != "NOT_APPLICABLE":
                validation.add(required, scope, f"{model_id}: active model lacks formula_ids or NOT_APPLICABLE evidence")
            if not value_present(model.get("assumptions")) and not value_present(model.get("assumption_ids")):
                validation.add(required, scope, f"{model_id}: active model lacks assumptions")

    for assumption in root_assumptions:
        fact_level = assumption.get("fact_level")
        assumption_id = str(assumption.get("assumption_id") or "<missing-assumption-id>")
        if fact_level and fact_level not in FACT_LEVELS:
            validation.add(required, scope, f"{assumption_id}: invalid fact_level {fact_level}")

    for formula in formulas:
        formula_id = str(formula.get("formula_id") or "<missing-formula-id>")
        model_id = str(formula.get("model_id") or "")
        status = str(formula.get("status") or "").lower()
        if status and status not in FORMULA_STATES:
            validation.add(required, scope, f"{formula_id}: invalid formula status {status}")
        if model_id and model_ids and model_id not in model_ids:
            validation.add(required, scope, f"{formula_id}: formula references missing model {model_id}")
        for assumption_id in [str(item) for item in as_list(formula.get("assumption_ids"))]:
            if assumption_id and assumption_ids and assumption_id not in assumption_ids:
                validation.add(required, scope, f"{formula_id}: formula references missing assumption {assumption_id}")
        if status == "active":
            for field in ("expression", "variables", "constraints", "missing_policy", "output_range", "test_refs"):
                if not value_present(formula.get(field)):
                    validation.add(required, scope, f"{formula_id}: active formula missing {field}")
            variables = as_list(formula.get("variables"))
            for variable in variables:
                if not isinstance(variable, dict):
                    validation.add(required, scope, f"{formula_id}: variable must be an object")
                    continue
                for field in ("name", "unit", "input_domain"):
                    if not value_present(variable.get(field)):
                        validation.add(required, scope, f"{formula_id}: every variable requires {field}")
            if not value_present(formula.get("code_refs")):
                validation.add(required, scope, f"{formula_id}: active formula missing code_refs")

    for parameter in parameters:
        parameter_id = str(parameter.get("parameter_id") or "<missing-parameter-id>")
        status = str(parameter.get("status") or "").lower()
        fact_level = parameter.get("fact_level")
        model_id = str(parameter.get("model_id") or "")
        formula_id = str(parameter.get("formula_id") or "")
        if status and status not in PARAMETER_STATES:
            validation.add(required, scope, f"{parameter_id}: invalid parameter status {status}")
        if fact_level and fact_level not in FACT_LEVELS:
            validation.add(required, scope, f"{parameter_id}: invalid fact_level {fact_level}")
        if model_id and model_ids and model_id not in model_ids:
            validation.add(required, scope, f"{parameter_id}: parameter references missing model {model_id}")
        if formula_id and formula_ids and formula_id not in formula_ids and fact_level != "NOT_APPLICABLE":
            validation.add(required, scope, f"{parameter_id}: parameter references missing formula {formula_id}")
        if status == "active":
            for field in (
                "default_value",
                "initial_or_prior_value",
                "active_value",
                "source_or_rationale",
                "code_ref",
                "test_ref",
            ):
                if not value_present(parameter.get(field)):
                    validation.add(required, scope, f"{parameter_id}: active parameter missing {field}")

    for task in tasks:
        task_id = str(task.get("task_id") or "<missing-task-id>")
        status = str(task.get("status") or "")
        if status and status not in TASK_STATES:
            validation.add(required, scope, f"{task_id}: invalid task status {status}")
        if status == "completed":
            for field in ("acceptance_ids", "test_commands", "test_results", "evidence_refs"):
                if not value_present(task.get(field)):
                    validation.add(required, scope, f"{task_id}: completed task missing {field}")
            if not value_present(task.get("completed_version")) and not value_present(task.get("completed_commit")):
                validation.add(required, scope, f"{task_id}: completed task missing completed_version or completed_commit")

    check_unknown_refs(validation, models, "model_id", required, scope)
    check_unknown_refs(validation, root_assumptions, "assumption_id", required, scope)
    check_unknown_refs(validation, formulas, "formula_id", required, scope)
    check_unknown_refs(validation, parameters, "parameter_id", required, scope)
    check_unknown_refs(validation, tasks, "task_id", required, scope)


def check_csv_headers(validation: Validation, parsed: dict[str, Any], required: bool, scope: str) -> None:
    parameter_fields = parsed.get("parameter_fields") or []
    if parameter_fields:
        missing = [column for column in PARAMETER_REQUIRED_COLUMNS if column not in parameter_fields]
        if missing:
            validation.add(required, scope, "parameter_registry.csv missing columns: " + ", ".join(missing))
    traceability_fields = parsed.get("traceability_fields") or []
    if traceability_fields:
        missing = [column for column in TRACEABILITY_REQUIRED_COLUMNS if column not in traceability_fields]
        if missing:
            validation.add(required, scope, "TRACEABILITY_MATRIX.csv missing columns: " + ", ".join(missing))


def check_weight_groups(validation: Validation, parameters: list[dict[str, Any]], required: bool, scope: str) -> None:
    groups: dict[str, list[dict[str, Any]]] = {}
    for parameter in parameters:
        group = str(parameter.get("weight_group") or "").strip()
        if group:
            groups.setdefault(group, []).append(parameter)
    for group, rows in groups.items():
        total = 0.0
        expected = 1.0
        tolerance = 0.0001
        for row in rows:
            if value_present(row.get("weight_group_target")):
                expected = float(row["weight_group_target"])
            if value_present(row.get("weight_group_tolerance")):
                tolerance = float(row["weight_group_tolerance"])
            raw = row.get("weight") if value_present(row.get("weight")) else row.get("active_value")
            try:
                total += float(raw)
            except (TypeError, ValueError):
                validation.add(required, scope, f"{row.get('parameter_id')}: non-numeric weight value in group {group}")
        if abs(total - expected) > tolerance:
            validation.add(required, scope, f"weight_group {group} sums to {total}, expected {expected} +/- {tolerance}")


def check_versions(validation: Validation, project_path: Path, parsed: dict[str, Any], required: bool, scope: str) -> None:
    version_file = project_path / "VERSION"
    changelog = project_path / "CHANGELOG.md"
    ledger = project_path / "docs" / "governance" / "DEVELOPMENT_LEDGER.md"
    matrix = parsed.get("version_matrix") or {}
    if not isinstance(matrix, dict) or not matrix:
        return
    product_version = matrix.get("product_version")
    declared_version_file_value = matrix.get("version_file_value")
    allowed_version_file_values = {
        str(value)
        for value in (product_version, declared_version_file_value)
        if value_present(value)
    }
    for field in (
        "product_version",
        "product_version_status",
        "governance_spec_version",
        "schema_version",
        "model_versions",
        "parameter_profile_versions",
        "data_snapshot_version",
        "current_iteration",
        "current_phase",
        "current_gate",
    ):
        if not value_present(matrix.get(field)):
            validation.add(required, scope, f"VERSION_MATRIX.yaml missing {field}")
    if version_file.exists() and allowed_version_file_values:
        version_text = version_file.read_text(encoding="utf-8").strip()
        if version_text not in allowed_version_file_values:
            allowed = ", ".join(sorted(allowed_version_file_values))
            validation.add(required, scope, f"VERSION {version_text} not declared in VERSION_MATRIX ({allowed})")
    if product_version and changelog.exists():
        if str(product_version) not in changelog.read_text(encoding="utf-8"):
            validation.add(required, scope, f"CHANGELOG.md does not mention product_version {product_version}")
    if product_version and ledger.exists():
        if str(product_version) not in ledger.read_text(encoding="utf-8"):
            validation.add(required, scope, f"DEVELOPMENT_LEDGER.md does not mention product_version {product_version}")


def check_manual_counts(validation: Validation, project_path: Path, parsed: dict[str, Any], required: bool, scope: str) -> None:
    files = [
        project_path / "docs" / "governance" / "MODEL_SPEC.md",
        project_path / "docs" / "governance" / "DELIVERY_PLAN.md",
        project_path / "docs" / "governance" / "DEVELOPMENT_LEDGER.md",
    ]
    actual = {
        "model_count": len(parsed["models"]),
        "formula_count": len(parsed["formulas"]),
        "parameter_count": len(parsed["parameters"]),
        "task_count": len(parsed["tasks"]),
        "acceptance_count": len(
            {
                str(acceptance_id)
                for task in parsed["tasks"]
                if isinstance(task, dict)
                for acceptance_id in as_list(task.get("acceptance_ids"))
                if acceptance_id
            }
        ),
    }
    pattern = re.compile(
        r"\b(model_count|formula_count|parameter_count|task_count|acceptance_count)\s*:\s*(\d+)\b"
    )
    for path in files:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for name, value in pattern.findall(text):
            if actual[name] != int(value):
                validation.add(required, scope, f"{rel(path)} declares {name}={value}, actual={actual[name]}")


def validate_root(validation: Validation, config: dict[str, Any]) -> None:
    root_config = config.get("root_governance") if isinstance(config, dict) else {}
    if not isinstance(root_config, dict):
        validation.error("root", "root_governance must be a mapping")
        return
    if root_config.get("ci_mode") != "required":
        validation.error("root", "root_governance.ci_mode must be required")
    required_files = as_list(root_config.get("required_files"))
    for rel_path in required_files:
        check_file_nonempty(validation, ROOT / str(rel_path), True, "root")
    for schema in sorted((ROOT / "governance" / "schemas").glob("*.json")):
        try:
            load_json(schema)
        except Exception as exc:
            validation.error("root", f"Invalid JSON schema {rel(schema)}: {exc}")

    projects = [p for p in as_list(config.get("projects")) if isinstance(p, dict)]
    registered_paths = [str(project.get("path") or "").rstrip("/") for project in projects]
    registered_ids = [str(project.get("project_id") or "") for project in projects]
    actual_project_dirs = discover_project_dirs()
    missing = [path for path in actual_project_dirs if path not in registered_paths]
    if missing:
        validation.error("root", "Project registry does not cover actual project directories: " + ", ".join(missing))
    for project in projects:
        scope = project_scope(project)
        path = str(project.get("path") or "").rstrip("/")
        ci_mode = str(project.get("ci_mode") or "")
        if ci_mode not in {"required", "advisory"}:
            validation.error(scope, f"Invalid ci_mode: {ci_mode}")
        validate_semantic_coverage_config(validation, project, ci_mode == "required", scope)
        if path and not (ROOT / path).exists():
            validation.error(scope, f"Registered project path missing: {path}")
    for value, label in ((registered_paths, "project path"), (registered_ids, "project_id")):
        duplicates = sorted({item for item in value if item and value.count(item) > 1})
        for duplicate in duplicates:
            validation.error("root", f"Duplicate {label}: {duplicate}")


def validate_project(
    validation: Validation,
    project: dict[str, Any],
    project_files: list[str],
    mode: str | None,
) -> None:
    scope = project_scope(project)
    required = is_required(project, mode)
    project_path = ROOT / str(project.get("path") or "")
    if not project_path.exists():
        validation.add(required, scope, f"Project path missing: {rel(project_path)}")
        return
    for rel_path in project_files:
        check_file_nonempty(validation, project_path / rel_path, required, scope)
    parsed = parse_project_governance(project_path, validation, required, scope)
    check_csv_headers(validation, parsed, required, scope)
    check_cross_references(validation, parsed, required, scope)
    check_weight_groups(validation, [p for p in parsed["parameters"] if isinstance(p, dict)], required, scope)
    check_versions(validation, project_path, parsed, required, scope)
    check_manual_counts(validation, project_path, parsed, required, scope)


ZERO_SHA = "0" * 40


def explicit_base_ref(value: str | None = None) -> str | None:
    candidate = value or os.environ.get("GOVERNANCE_BASE_REF") or os.environ.get("GOVERNANCE_BASE_SHA")
    if not candidate:
        return None
    candidate = candidate.strip()
    if not candidate or candidate == ZERO_SHA:
        return None
    return candidate


def git_ref_exists(ref: str) -> bool:
    result = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def git_changed_files(base_ref: str | None = None) -> list[str]:
    commands = [
        ["git", "diff", "--name-only", "--cached"],
        ["git", "diff", "--name-only"],
        ["git", "ls-files", "--others", "--exclude-standard"],
    ]
    changed: set[str] = set()
    for command in commands:
        try:
            output = subprocess.check_output(["git", "-c", "core.quotePath=false", *command[1:]], cwd=ROOT, text=True)
        except subprocess.CalledProcessError:
            continue
        changed.update(line.strip() for line in output.splitlines() if line.strip())
    explicit_base = explicit_base_ref(base_ref)
    if explicit_base and git_ref_exists(explicit_base):
        try:
            output = subprocess.check_output(
                ["git", "-c", "core.quotePath=false", "diff", "--name-only", f"{explicit_base}...HEAD"],
                cwd=ROOT,
                text=True,
                stderr=subprocess.DEVNULL,
            )
            changed.update(line.strip() for line in output.splitlines() if line.strip())
        except subprocess.CalledProcessError:
            pass
    github_base_ref = os.environ.get("GITHUB_BASE_REF")
    if not explicit_base and github_base_ref:
        try:
            output = subprocess.check_output(
                ["git", "-c", "core.quotePath=false", "diff", "--name-only", f"origin/{github_base_ref}...HEAD"],
                cwd=ROOT,
                text=True,
                stderr=subprocess.DEVNULL,
            )
            changed.update(line.strip() for line in output.splitlines() if line.strip())
        except subprocess.CalledProcessError:
            pass
    return sorted(changed)


def project_matches_changed(project: dict[str, Any], changed: list[str]) -> bool:
    path = str(project.get("path") or "").rstrip("/")
    if not path:
        return False
    for filename in changed:
        if filename == path or filename.startswith(path + "/"):
            return True
        rel_name = filename[len(path) + 1 :] if filename.startswith(path + "/") else filename
        for pattern in as_list(project.get("model_behavior_globs")):
            if filename.startswith(path + "/") and fnmatch.fnmatch(rel_name, str(pattern)):
                return True
    return False


def select_projects(config: dict[str, Any], args: argparse.Namespace) -> list[dict[str, Any]]:
    projects = [p for p in as_list(config.get("projects")) if isinstance(p, dict)]
    if args.project:
        selected = [p for p in projects if p.get("project_id") == args.project or p.get("path") == args.project]
        if not selected:
            raise SystemExit(f"Unknown project: {args.project}")
        return selected
    if args.changed_only:
        changed = git_changed_files(getattr(args, "base_ref", None))
        root_governance_changed = any(
            filename.startswith(
                (
                    "docs/governance/",
                    "governance/",
                    "scripts/validate_project_governance.py",
                    ".agents/skills/project-governance/",
                    ".agents/skills/codex-dex/",
                    ".codex/",
                    ".github/workflows/project-governance.yml",
                )
            )
            or filename == "AGENTS.md"
            for filename in changed
        )
        if root_governance_changed:
            return projects
        selected = [p for p in projects if project_matches_changed(p, changed)]
        return selected
    return projects


def print_summary(validation: Validation, checked_projects: list[dict[str, Any]]) -> None:
    print("CodexProject governance validation")
    print("root: checked")
    print("projects checked: " + (", ".join(project_scope(p) for p in checked_projects) if checked_projects else "none"))
    print(f"errors: {len(validation.errors)}")
    print(f"warnings: {len(validation.warnings)}")
    for issue in validation.issues:
        print(f"[{issue.level}] {issue.scope}: {issue.message}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--all", action="store_true", help="Validate root governance and all registered projects.")
    group.add_argument("--project", help="Validate one registered project by project_id or path.")
    group.add_argument("--changed-only", action="store_true", help="Validate root governance and changed project scopes.")
    parser.add_argument("--mode", choices=["advisory", "required"], help="Override project ci_mode.")
    parser.add_argument("--base-ref", help="Explicit base commit/ref for changed-only diff validation.")
    parser.add_argument("--enforce-sync", action="store_true", help="Enforce diff-driven governance update requirements.")
    parser.add_argument("--semantic", action="store_true", help="Run semantic drift checks for current iterations, ledgers, and references.")
    parser.add_argument("--drift-report", action="store_true", help="Print a machine-readable semantic drift report.")
    args = parser.parse_args(argv)
    if not (args.all or args.project or args.changed_only):
        args.changed_only = True

    validation = Validation()
    try:
        config = load_yaml(PROJECTS_FILE)
    except Exception as exc:
        validation.error("root", f"Cannot parse {rel(PROJECTS_FILE)}: {exc}")
        print_summary(validation, [])
        return 1

    if not isinstance(config, dict):
        validation.error("root", f"{rel(PROJECTS_FILE)} must parse to a mapping")
        print_summary(validation, [])
        return 1

    validate_root(validation, config)
    project_files = [str(item) for item in as_list(config.get("project_governance_files"))]
    try:
        selected_projects = select_projects(config, args)
    except SystemExit as exc:
        validation.error("root", str(exc))
        print_summary(validation, [])
        return 1

    for project in selected_projects:
        validate_project(validation, project, project_files, args.mode)

    sync_exit_code = 0
    if args.enforce_sync or args.semantic or args.drift_report:
        import validate_governance_sync

        sync_exit_code, _ = validate_governance_sync.validate(
            all_projects=args.all,
            changed_only=args.changed_only,
            enforce_sync=args.enforce_sync,
            semantic=args.semantic or args.all,
            drift_report=args.drift_report,
            base_ref=args.base_ref,
        )

    print_summary(validation, selected_projects)
    return 1 if validation.errors or sync_exit_code else 0


if __name__ == "__main__":
    raise SystemExit(main())
