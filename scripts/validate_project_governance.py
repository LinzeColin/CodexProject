#!/usr/bin/env python3
"""Validate CodexProject root and project governance files."""

from __future__ import annotations

import argparse
import csv
import fnmatch
import hashlib
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


class GovernanceDiffError(RuntimeError):
    def __init__(self, error_code: str, message: str, *, base_ref: str | None = None) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.base_ref = base_ref or ""
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
PROJECT_REGISTRY_ALLOWED_FIELDS = {"project_id", "path", "ci_mode", "migration"}
PROJECT_REGISTRY_MIGRATION_VERSIONS = {
    "legacy-v1-pending-lean-v2",
    "lean-v2",
}
PRODUCT_ROADMAP_KIND = "product"
HUMAN_ENTRY_QUALITY_CONTRACTS = {
    "功能清单": {
        "title": "# 功能清单",
        "required_tokens": ("## 摘要", "project_id", "current_stage", "current_task", "evidence_status"),
    },
    "开发记录": {
        "title": "# 开发记录",
        "required_tokens": ("## 摘要", "Stage -> Phase -> Task", "stop_gate"),
    },
    "模型参数文件": {
        "title": "# 模型参数文件",
        "required_tokens": ("## 摘要", "active_model_count", "active_formula_count", "active_parameter_count"),
    },
}
HUMAN_ENTRY_FORBIDDEN_MARKERS = (
    "compatibility index",
    "compatibility indexes",
    "兼容索引",
    "详见 docs/governance",
    "see docs/governance",
    "link page",
)


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
    in_single = False
    in_double = False
    escaped = False
    for idx, char in enumerate(text):
        if char == "\\" and not escaped:
            escaped = True
            continue
        if char == "'" and not in_double and not escaped:
            in_single = not in_single
        elif char == '"' and not in_single and not escaped:
            in_double = not in_double
        elif char == ":" and not in_single and not in_double:
            return text[:idx].strip(), text[idx + 1 :].strip()
        escaped = False
    return text.strip(), None


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
        if lines[index][1].startswith("- ") or lines[index][1] == "-":
            result: list[Any] = []
            while index < len(lines) and lines[index][0] == indent and (
                lines[index][1].startswith("- ") or lines[index][1] == "-"
            ):
                item_text = lines[index][1][1:].strip()
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
        while index < len(lines) and lines[index][0] == indent and not (
            lines[index][1].startswith("- ") or lines[index][1] == "-"
        ):
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
    elif bool(project.get("semantic_extractors")) and status not in {"in_progress", "blocked"}:
        validation.add(required, scope, "semantic_extractors: true requires semantic_coverage.status to be in_progress, blocked, or machine_verified")
    if status == "not_applicable" and not value_present(coverage.get("evidence_ref")):
        validation.add(required, scope, "semantic_coverage.not_applicable requires evidence_ref")


def check_semantic_coverage_task_binding(
    validation: Validation,
    project: dict[str, Any],
    parsed: dict[str, Any],
    required: bool,
    scope: str,
) -> None:
    coverage = project.get("semantic_coverage")
    if not isinstance(coverage, dict):
        return
    task_id = str(coverage.get("task_id") or "").strip()
    acceptance_id = str(coverage.get("acceptance_id") or "").strip()
    status = str(coverage.get("status") or "").strip()
    if not task_id:
        return
    tasks = [task for task in parsed.get("tasks", []) if isinstance(task, dict)]
    task = next((item for item in tasks if str(item.get("task_id") or "") == task_id), None)
    if not task:
        validation.add(required, scope, f"semantic_coverage.task_id not found in delivery_tasks.yaml: {task_id}")
        return
    acceptance_ids = {str(item) for item in as_list(task.get("acceptance_ids")) if item}
    if acceptance_id and acceptance_id not in acceptance_ids:
        validation.add(required, scope, f"semantic_coverage.acceptance_id {acceptance_id} is not listed on task {task_id}")
    task_status = str(task.get("status") or "")
    if status == "machine_verified" and task_status != "completed":
        validation.add(required, scope, f"semantic_coverage.machine_verified requires task {task_id} to be completed")
    if status in {"planned", "in_progress", "blocked"} and task_status in {"completed", "rejected", "deprecated"}:
        validation.add(required, scope, f"semantic_coverage.{status} cannot point to terminal task {task_id} with status {task_status}")


def sha256_file(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    return hashlib.sha256(text.replace("\r\n", "\n").encode("utf-8")).hexdigest()


def count_audit_severities(path: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    for match in re.finditer(r"(?m)^  severity: (P[0-3])$", path.read_text(encoding="utf-8")):
        severity = match.group(1)
        counts[severity] = counts.get(severity, 0) + 1
    return counts


def validate_arxiv_daily_push_v7_root_lock(
    validation: Validation,
    project_path: Path,
    parsed: dict[str, Any],
    required: bool,
    scope: str,
) -> None:
    if project_path.name != "arxiv-daily-push":
        return

    v7_root = project_path / "docs" / "pursuing_goal" / "v7_1"
    files = {
        "lock": v7_root / "V7_1_ROOT_LOCK.yaml",
        "contract_hash": v7_root / "CONTRACT_HASH.txt",
        "product_contract": v7_root / "machine_readable" / "product_contract_v7.yaml",
        "decision_log": v7_root / "machine_readable" / "decision_log_v7.yaml",
        "requirements": v7_root / "machine_readable" / "requirements_v7.yaml",
        "stop_codes": v7_root / "machine_readable" / "stop_codes_v7.yaml",
        "audit_findings": v7_root / "machine_readable" / "audit_findings_v7_1.yaml",
        "merge_policy": v7_root / "machine_readable" / "merge_policy_v7_1.yaml",
        "lifecycle": v7_root / "machine_readable" / "operational_lifecycle_v7_1.yaml",
        "roadmap": v7_root / "ROADMAP" / "roadmap_v7.yaml",
        "roadmap_human": v7_root / "ROADMAP" / "ARXIV_DAILY_PUSH_ROADMAP_V7_1_CN.md",
    }
    missing = [name for name, path in files.items() if not check_file_nonempty(validation, path, required, scope)]
    if missing:
        return

    try:
        lock = load_yaml(files["lock"])
        hash_contract = files["contract_hash"].read_text(encoding="utf-8").strip()
    except Exception as exc:
        validation.add(required, scope, f"V7 root lock parse failure: {exc}")
        return

    if not isinstance(lock, dict):
        validation.add(required, scope, "V7_1_ROOT_LOCK.yaml must be a mapping")
        return
    if lock.get("status") != "repository_locked_pending_pr_ci":
        validation.add(required, scope, f"V7_ROOT_LOCK status is not repository_locked_pending_pr_ci: {lock.get('status')}")
    if lock.get("project_id") != "arxiv-daily-push":
        validation.add(required, scope, "V7_ROOT_LOCK project_id must be arxiv-daily-push")

    expected_contract_version = "ADP-PRODUCT-CONTRACT-V7.1"
    expected_roadmap_version = "ADP-ROADMAP-V7.1"
    contract = lock.get("current_contract") if isinstance(lock.get("current_contract"), dict) else {}
    product_hash = sha256_file(files["product_contract"])
    roadmap_hash = sha256_file(files["roadmap"])
    audit_hash = sha256_file(files["audit_findings"])
    audit_counts = count_audit_severities(files["audit_findings"])
    if audit_counts.get("P0") != 8 or audit_counts.get("P1") != 37:
        validation.add(required, scope, f"V7.1 inherited audit counts must remain P0=8/P1=37: {audit_counts}")
    if contract.get("contract_version") != expected_contract_version:
        validation.add(required, scope, "V7 lock contract_version mismatch")
    if contract.get("roadmap_version") != expected_roadmap_version:
        validation.add(required, scope, "V7 lock roadmap_version mismatch")
    if contract.get("contract_sha256") != product_hash:
        validation.add(required, scope, "V7 product_contract_sha256 does not match repository file")
    if contract.get("roadmap_sha256") != roadmap_hash:
        validation.add(required, scope, "V7 roadmap_sha256 does not match repository file")
    if contract.get("audit_version") != "ADP-PARALLEL-AUDIT-V7.1":
        validation.add(required, scope, "V7 lock audit_version mismatch")
    if contract.get("audit_findings_sha256") != audit_hash:
        validation.add(required, scope, "V7 audit_findings_sha256 does not match repository file")
    if isinstance(hash_contract, str):
        if hash_contract.strip() != product_hash:
            validation.add(required, scope, "CONTRACT_HASH.txt product hash does not match repository file")
    elif isinstance(hash_contract, dict):
        if hash_contract.get("product_contract_sha256") != product_hash:
            validation.add(required, scope, "CONTRACT_HASH.txt product hash does not match repository file")
    else:
        validation.add(required, scope, "CONTRACT_HASH.txt must be the product contract SHA256 or a mapping")

    product_text = files["product_contract"].read_text(encoding="utf-8")
    roadmap_text = files["roadmap"].read_text(encoding="utf-8")
    if f"contract_version: {expected_contract_version}" not in product_text:
        validation.add(required, scope, "product_contract_v7.yaml contract_version mismatch")
    if "stage2_continues_in_parallel: true" not in product_text:
        validation.add(required, scope, "V7 product contract must preserve stage2_continues_in_parallel=true")
    if f"roadmap_version: {expected_roadmap_version}" not in roadmap_text:
        validation.add(required, scope, "roadmap_v7.yaml roadmap_version mismatch")

    stage1 = lock.get("stage1_boundary") if isinstance(lock.get("stage1_boundary"), dict) else {}
    if stage1.get("accepted_gate") != "ARXIV_PRODUCTION_ACCEPTED" or stage1.get("status") != "maintained":
        validation.add(required, scope, "V7 lock must maintain ARXIV_PRODUCTION_ACCEPTED")
    if stage1.get("must_not_regress") is not True:
        validation.add(required, scope, "V7 lock must set stage1_boundary.must_not_regress=true")

    stage2 = lock.get("stage2_boundary") if isinstance(lock.get("stage2_boundary"), dict) else {}
    if stage2.get("stop_gate") != "INTEGRATED_PRODUCTION_ACCEPTED -> DAILY_OPERATION":
        validation.add(required, scope, "V7 lock Stage2 stop_gate mismatch")
    if stage2.get("production_accepted") is not False:
        validation.add(required, scope, "V7 lock must keep Stage2 production_accepted=false")
    if stage2.get("current_task_id") != "S2PCT01":
        validation.add(required, scope, "V7 lock current_task_id must be S2PCT01")
    if stage2.get("current_shadow_source_task") != "S2PBT01":
        validation.add(required, scope, "V7 lock current_shadow_source_task must be S2PBT01")
    if stage2.get("final_task") != "S2PMT07":
        validation.add(required, scope, "V7 lock final_task must be S2PMT07")
    aliases = stage2.get("legacy_aliases") if isinstance(stage2.get("legacy_aliases"), dict) else {}
    if aliases.get("S2PCT01") != "S2P2T01":
        validation.add(required, scope, "V7 lock must map S2PCT01 to legacy S2P2T01")
    if aliases.get("S2PBT01") != "S2P1T01":
        validation.add(required, scope, "V7 lock must map S2PBT01 to legacy S2P1T01")
    tasks = [task for task in parsed.get("tasks", []) if isinstance(task, dict)]
    s2pat05 = next((task for task in tasks if str(task.get("task_id") or "") == "S2PAT05"), None)
    if not s2pat05:
        validation.add(required, scope, "delivery_tasks.yaml must contain V7.1 task S2PAT05")
    else:
        acceptance_ids = {str(item) for item in as_list(s2pat05.get("acceptance_ids")) if item}
        if "ACC-S2PAT05-AUDIT-LOCK" not in acceptance_ids:
            validation.add(required, scope, "S2PAT05 missing ACC-S2PAT05-AUDIT-LOCK")
    s2pbt01 = next((task for task in tasks if str(task.get("task_id") or "") == "S2PBT01"), None)
    if not s2pbt01:
        validation.add(required, scope, "delivery_tasks.yaml must contain V7 task S2PBT01")
    else:
        if str(s2pbt01.get("status") or "") not in {"ready", "in_progress", "completed"}:
            validation.add(required, scope, "S2PBT01 must be ready, in_progress, or completed")
        acceptance_ids = {str(item) for item in as_list(s2pbt01.get("acceptance_ids")) if item}
        if "ACC-S2PBT01-BIORXIV-MEDRXIV" not in acceptance_ids:
            validation.add(required, scope, "S2PBT01 missing ACC-S2PBT01-BIORXIV-MEDRXIV")
    s2pct01 = next((task for task in tasks if str(task.get("task_id") or "") == "S2PCT01"), None)
    if not s2pct01:
        validation.add(required, scope, "delivery_tasks.yaml must contain V7.1 task S2PCT01")
    else:
        if str(s2pct01.get("status") or "") not in {"ready", "in_progress", "completed"}:
            validation.add(required, scope, "S2PCT01 must be ready, in_progress, or completed")
        acceptance_ids = {str(item) for item in as_list(s2pct01.get("acceptance_ids")) if item}
        if "ACC-S2PCT01-NATURE" not in acceptance_ids:
            validation.add(required, scope, "S2PCT01 missing ACC-S2PCT01-NATURE")

    root_agent = (ROOT / "AGENTS.md").read_text(encoding="utf-8") if (ROOT / "AGENTS.md").exists() else ""
    project_agent = (project_path / "AGENTS.md").read_text(encoding="utf-8") if (project_path / "AGENTS.md").exists() else ""
    for needle, text, label in (
        ("V*_ROOT_LOCK.yaml", root_agent, "root AGENTS.md"),
        ("docs/pursuing_goal/v7_1/V7_1_ROOT_LOCK.yaml", project_agent, "arxiv-daily-push/AGENTS.md"),
        ("INTEGRATED_PRODUCTION_ACCEPTED ->", project_agent, "arxiv-daily-push/AGENTS.md"),
        ("S2PCT01", project_agent, "arxiv-daily-push/AGENTS.md"),
        ("S2P2T01", project_agent, "arxiv-daily-push/AGENTS.md"),
        ("S2PBT01", project_agent, "arxiv-daily-push/AGENTS.md"),
    ):
        if needle not in text:
            validation.add(required, scope, f"{label} missing V7 reference: {needle}")

    for rel_path in ("功能清单", "开发记录", "模型参数文件"):
        text = (project_path / rel_path).read_text(encoding="utf-8") if (project_path / rel_path).exists() else ""
        for needle in ("ADP-PRODUCT-CONTRACT-V7.1", "V7_1_ROOT_LOCK.yaml", "ARXIV_PRODUCTION_ACCEPTED", "S2PCT01", "S2P2T01", "S2PBT01"):
            if needle not in text:
                validation.add(required, scope, f"{rel_path} missing V7 lock reference: {needle}")

    matrix = parsed.get("version_matrix") if isinstance(parsed.get("version_matrix"), dict) else {}
    if matrix.get("current_v7_contract_version") == "ADP-PRODUCT-CONTRACT-V7.1":
        if matrix.get("current_v7_task_id") != "S2PCT01":
            validation.add(required, scope, "VERSION_MATRIX.yaml current_v7_task_id must be S2PCT01 for V7.1")
    elif matrix.get("current_v7_contract_version") == "ADP-PRODUCT-CONTRACT-V7.2":
        if matrix.get("current_v7_task_id") != "S2PCT02":
            validation.add(required, scope, "VERSION_MATRIX.yaml current_v7_task_id must be S2PCT02 for V7.2")
    else:
        validation.add(required, scope, "VERSION_MATRIX.yaml missing supported current_v7_contract_version")
    if matrix.get("current_v7_shadow_source_task_id") != "S2PBT01":
        validation.add(required, scope, "VERSION_MATRIX.yaml current_v7_shadow_source_task_id must be S2PBT01")
    if matrix.get("current_v7_final_task_id") != "S2PMT07":
        validation.add(required, scope, "VERSION_MATRIX.yaml current_v7_final_task_id must be S2PMT07")
    if matrix.get("stage1_acceptance_gate") != "ARXIV_PRODUCTION_ACCEPTED_MAINTAINED":
        validation.add(required, scope, "VERSION_MATRIX.yaml must preserve ARXIV_PRODUCTION_ACCEPTED_MAINTAINED")

    v72_root = project_path / "docs" / "pursuing_goal" / "v7_2"
    v72_files = {
        "current": project_path / "docs" / "pursuing_goal" / "CURRENT.yaml",
        "lock": v72_root / "V7_2_ROOT_LOCK.yaml",
        "product": v72_root / "machine_readable" / "product_contract_v7_2.yaml",
        "roadmap": v72_root / "machine_readable" / "roadmap_v7_2.yaml",
        "migration": v72_root / "machine_readable" / "migration_matrix_v7_1_to_v7_2.yaml",
        "review": v72_root / "AUDIT" / "final_review_matrix.yaml",
        "handoff": v72_root / "HANDOFF" / "00_下一Agent先读.md",
    }
    missing_v72 = [name for name, path in v72_files.items() if not check_file_nonempty(validation, path, required, scope)]
    if missing_v72:
        return
    try:
        current = load_yaml(v72_files["current"])
        v72_lock = load_yaml(v72_files["lock"])
        v72_product = load_yaml(v72_files["product"])
        v72_migration = load_yaml(v72_files["migration"])
        v72_review = load_yaml(v72_files["review"])
        v72_roadmap = load_yaml(v72_files["roadmap"])
    except Exception as exc:
        validation.add(required, scope, f"V7.2 contract parse failure: {exc}")
        return
    if current.get("current_product_contract", {}).get("version") != "ADP-PRODUCT-CONTRACT-V7.2":
        validation.add(required, scope, "CURRENT.yaml must point to ADP-PRODUCT-CONTRACT-V7.2")
    if current.get("previous_read_only_contract", {}).get("version") != "ADP-PRODUCT-CONTRACT-V7.1":
        validation.add(required, scope, "CURRENT.yaml must preserve V7.1 as read-only previous contract")
    if current.get("agent_revalidation_required") is not True:
        validation.add(required, scope, "CURRENT.yaml must require Stage2 agent revalidation")
    v72_contract = v72_lock.get("current_contract") if isinstance(v72_lock.get("current_contract"), dict) else {}
    if v72_contract.get("contract_version") != "ADP-PRODUCT-CONTRACT-V7.2":
        validation.add(required, scope, "V7_2_ROOT_LOCK current contract_version mismatch")
    if v72_product.get("contract_version") != "ADP-PRODUCT-CONTRACT-V7.2":
        validation.add(required, scope, "product_contract_v7_2.yaml contract_version mismatch")
    if v72_product.get("parent_contract", {}).get("version") != "ADP-PRODUCT-CONTRACT-V7.1":
        validation.add(required, scope, "product_contract_v7_2.yaml must inherit V7.1")
    inherited = v72_product.get("production_stop_gate", {}).get("inherited_v7_1_open_findings", {})
    if inherited.get("P0") != 8 or inherited.get("P1") != 37:
        validation.add(required, scope, "product_contract_v7_2.yaml must preserve inherited V7.1 P0=8/P1=37")
    baseline = v72_product.get("production_stop_gate", {}).get("v7_2_baseline_migration_open_findings", {})
    if baseline.get("P0") != 0 or baseline.get("P1") != 0:
        validation.add(required, scope, "product_contract_v7_2.yaml V7.2 baseline blockers must be P0=0/P1=0")
    inherited_lock = v72_lock.get("inherited_v7_1_audit_blockers", {})
    if inherited_lock.get("open_p0_findings") != 8 or inherited_lock.get("open_p1_findings") != 37:
        validation.add(required, scope, "V7_2_ROOT_LOCK.yaml must preserve inherited V7.1 P0=8/P1=37")
    baseline_lock = v72_lock.get("v7_2_baseline_migration_blockers", {})
    if baseline_lock.get("open_p0_findings") != 0 or baseline_lock.get("open_p1_findings") != 0:
        validation.add(required, scope, "V7_2_ROOT_LOCK.yaml V7.2 baseline blockers must be P0=0/P1=0")
    for field, path in (
        ("contract_sha256", v72_files["product"]),
        ("roadmap_sha256", v72_files["roadmap"]),
        ("migration_matrix_sha256", v72_files["migration"]),
        ("final_review_sha256", v72_files["review"]),
    ):
        if v72_contract.get(field) != sha256_file(path):
            validation.add(required, scope, f"V7_2_ROOT_LOCK {field} does not match repository file")
    for section in (
        "v7_1_retained_requirements",
        "v7_1_replaced_requirements",
        "v1_1_new_requirements",
        "file_migration_matrix",
        "task_id_mapping",
        "stop_gate_migration",
        "rollback",
    ):
        if not v72_migration.get(section):
            validation.add(required, scope, f"V7.2 migration matrix missing {section}")
    agents = v72_review.get("agents") if isinstance(v72_review.get("agents"), dict) else {}
    for agent_id in ("A", "B", "C"):
        if agents.get(agent_id, {}).get("status") != "pass_with_required_controls":
            validation.add(required, scope, f"V7.2 final review agent {agent_id} did not pass")
    if v72_review.get("baseline_publication_verdict", {}).get("status") != "pass":
        validation.add(required, scope, "V7.2 final review verdict must pass")
    email_v1_merged_state = "EMAIL_LEARNING_V1_MERGED_TO_MAIN_NO_PRODUCTION_SIDE_EFFECTS"
    if v72_roadmap.get("global_current_task") != "S2PCT02":
        validation.add(required, scope, "V7.2 roadmap global_current_task must remain S2PCT02")
    if v72_roadmap.get("email_v1_workstream_next") != email_v1_merged_state:
        validation.add(required, scope, "V7.2 roadmap must record Email V1 as merged to main with no production side effects")
    if v72_lock.get("stage2_boundary", {}).get("email_v1_workstream_next") != email_v1_merged_state:
        validation.add(required, scope, "V7_2_ROOT_LOCK Email V1 workstream status mismatch")
    if matrix.get("v7_2_email_v1_workstream_next") != email_v1_merged_state:
        validation.add(required, scope, "VERSION_MATRIX Email V1 workstream status mismatch")
    email_required_tasks = {
        "S2PHT01V1.1-T00",
        "S2PHT01V1.1-T01",
        "S2PHT01V1.1-T02",
        "S2PHT01V1.1-T03",
        "S2PHT01V1.1-T04",
        "S2PHT01V1.1-T05",
    }
    baseline_workstream = next(
        (item for item in as_list(v72_roadmap.get("workstreams")) if item.get("workstream_id") == "V7_2_BASELINE_UPGRADE"),
        {},
    )
    if not email_required_tasks.issubset(set(as_list(baseline_workstream.get("completed_tasks")))):
        validation.add(required, scope, "V7.2 baseline completed_tasks must include Email V1 T00-T05")
    if baseline_workstream.get("next_task") != "S2PCT02":
        validation.add(required, scope, "V7.2 baseline next_task must remain S2PCT02")
    email_workstream = next(
        (item for item in as_list(v72_roadmap.get("workstreams")) if item.get("workstream_id") == "EMAIL_LEARNING_V1"),
        {},
    )
    if email_workstream.get("status") != "merged_to_main_no_production_side_effects":
        validation.add(required, scope, "EMAIL_LEARNING_V1 workstream must be merged_to_main_no_production_side_effects")
    email_task_status = {item.get("task_id"): item.get("status") for item in as_list(email_workstream.get("tasks"))}
    for task_id in sorted(email_required_tasks):
        if email_task_status.get(task_id) != "completed":
            validation.add(required, scope, f"EMAIL_LEARNING_V1 task {task_id} must be completed")
    strengthened = set(v72_migration.get("stop_gate_migration", {}).get("added_or_strengthened", []))
    if "SCOPE-ESCAPE" not in strengthened:
        validation.add(required, scope, "V7.2 migration matrix must include SCOPE-ESCAPE")
    if matrix.get("v7_open_p0_findings") != 8 or matrix.get("v7_open_p1_findings") != 37:
        validation.add(required, scope, "VERSION_MATRIX.yaml must preserve inherited V7.1 open P0=8/P1=37")
    if matrix.get("v7_2_baseline_open_p0_findings") != 0 or matrix.get("v7_2_baseline_open_p1_findings") != 0:
        validation.add(required, scope, "VERSION_MATRIX.yaml V7.2 baseline blockers must be P0=0/P1=0")
    s2pat06 = next((task for task in tasks if str(task.get("task_id") or "") == "S2PAT06"), None)
    if not s2pat06:
        validation.add(required, scope, "delivery_tasks.yaml must contain V7.2 task S2PAT06")
    else:
        acceptance_ids = {str(item) for item in as_list(s2pat06.get("acceptance_ids")) if item}
        if "ACC-S2PAT06-V7-2-CURRENT" not in acceptance_ids:
            validation.add(required, scope, "S2PAT06 missing ACC-S2PAT06-V7-2-CURRENT")

    current_tokens = (
        ("docs/pursuing_goal/CURRENT.yaml", project_agent, "arxiv-daily-push/AGENTS.md"),
        ("docs/pursuing_goal/v7_2/V7_2_ROOT_LOCK.yaml", project_agent, "arxiv-daily-push/AGENTS.md"),
        ("ADP-PRODUCT-CONTRACT-V7.2", (project_path / "功能清单").read_text(encoding="utf-8"), "功能清单"),
        ("ADP-PRODUCT-CONTRACT-V7.2", (project_path / "开发记录").read_text(encoding="utf-8"), "开发记录"),
        ("ADP-PRODUCT-CONTRACT-V7.2", (project_path / "模型参数文件").read_text(encoding="utf-8"), "模型参数文件"),
    )
    for needle, text, label in current_tokens:
        if needle not in text:
            validation.add(required, scope, f"{label} missing V7.2 current reference: {needle}")


def rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def check_file_nonempty(validation: Validation, path: Path, required: bool, scope: str) -> bool:
    if not path.exists():
        validation.add(required, scope, f"Missing file: {rel(path)}")
        return False
    if path.is_file() and path.stat().st_size == 0:
        validation.add(required, scope, f"Empty file: {rel(path)}")
        return False
    return True


def check_human_entry_quality(validation: Validation, project_path: Path, required: bool, scope: str) -> None:
    for filename, contract in HUMAN_ENTRY_QUALITY_CONTRACTS.items():
        path = project_path / filename
        if not path.exists() or not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        stripped = text.strip()
        entry_head = "\n".join(stripped.splitlines()[:12]).lower()
        if any(marker in entry_head for marker in HUMAN_ENTRY_FORBIDDEN_MARKERS):
            validation.add(required, scope, f"{filename} must be owner-readable content, not a compatibility index or link page")
        first_line = next((line.strip() for line in stripped.splitlines() if line.strip()), "")
        if first_line != contract["title"]:
            validation.add(required, scope, f"{filename} must start with {contract['title']}")
        for token in contract["required_tokens"]:
            if token not in text:
                validation.add(required, scope, f"{filename} missing owner-readable token: {token}")


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
        "roadmap": {},
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
        "roadmap": docs / "roadmap.yaml",
        "model_registry": docs / "model_registry.yaml",
        "formula_registry": docs / "formula_registry.yaml",
        "parameter_registry": docs / "parameter_registry.csv",
        "delivery_tasks": docs / "delivery_tasks.yaml",
        "development_events": docs / "development_events.jsonl",
        "version_matrix": docs / "VERSION_MATRIX.yaml",
        "traceability_matrix": docs / "TRACEABILITY_MATRIX.csv",
    }
    try:
        if files["roadmap"].exists():
            data = load_yaml(files["roadmap"])
            parsed["roadmap"] = data if isinstance(data, dict) else {}
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


def root_changed_scope_excluded_project_ids() -> set[str]:
    try:
        config = load_yaml(PROJECTS_FILE)
    except Exception:
        return set()
    if not isinstance(config, dict):
        return set()
    root_config = config.get("root_governance") if isinstance(config.get("root_governance"), dict) else {}
    return {str(item) for item in as_list(root_config.get("changed_scope_excluded_projects")) if item}


def check_product_roadmap_kind(validation: Validation, project: dict[str, Any], parsed: dict[str, Any], required: bool, scope: str) -> None:
    project_id = str(project.get("project_id") or "")
    if project_id in root_changed_scope_excluded_project_ids():
        return
    roadmap = parsed.get("roadmap") if isinstance(parsed.get("roadmap"), dict) else {}
    kind = str(roadmap.get("roadmap_kind") or "").strip()
    if kind != PRODUCT_ROADMAP_KIND:
        validation.add(required, scope, "docs/governance/roadmap.yaml roadmap_kind must be product for project human-entry rendering")


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


def project_registry_counts(project: dict[str, Any]) -> dict[str, int]:
    project_path = ROOT / str(project.get("path") or "")
    parsed_validation = Validation()
    parsed = parse_project_governance(project_path, parsed_validation, True, project_scope(project))
    parameters = [row for row in parsed.get("parameters", []) if isinstance(row, dict)]
    formulas = [row for row in parsed.get("formulas", []) if isinstance(row, dict)]
    models = [row for row in parsed.get("models", []) if isinstance(row, dict)]
    tasks = [row for row in parsed.get("tasks", []) if isinstance(row, dict)]
    events = [row for row in parsed.get("events", []) if isinstance(row, dict)]
    return {
        "models": len(models),
        "total_formulas": len(formulas),
        "active_formulas": len([row for row in formulas if str(row.get("status") or "").lower() == "active"]),
        "total_parameters": len(parameters),
        "active_parameters": len([row for row in parameters if str(row.get("status") or "").lower() == "active"]),
        "tasks": len(tasks),
        "events": len(events),
    }


def scalar_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        result: list[str] = []
        for item in value.values():
            result.extend(scalar_strings(item))
        return result
    if isinstance(value, list):
        result = []
        for item in value:
            result.extend(scalar_strings(item))
        return result
    return []


def validate_projects_yaml_count_claims(validation: Validation, projects: list[dict[str, Any]]) -> None:
    patterns = [
        (re.compile(r"\b(\d+)\s+active\s+parameters?\b", re.I), "active_parameters"),
        (re.compile(r"\b(\d+)\s+total\s+parameters?\b", re.I), "total_parameters"),
        (re.compile(r"\b(\d+)\s+parameters?\b", re.I), "total_parameters"),
        (re.compile(r"\b(\d+)\s+active\s+formulas?\b", re.I), "active_formulas"),
        (re.compile(r"\b(\d+)\s+total\s+formulas?\b", re.I), "total_formulas"),
        (re.compile(r"\b(\d+)\s+formulas?\b", re.I), "total_formulas"),
        (re.compile(r"\b(\d+)\s+models?\b", re.I), "models"),
        (re.compile(r"\b(\d+)\s+tasks?\b", re.I), "tasks"),
        (re.compile(r"\b(\d+)\s+events?\b", re.I), "events"),
    ]
    for project in projects:
        scope = project_scope(project)
        counts = project_registry_counts(project)
        for text in scalar_strings(project):
            for pattern, key in patterns:
                for match in pattern.finditer(text):
                    declared = int(match.group(1))
                    actual = counts[key]
                    if declared != actual:
                        validation.error(
                            scope,
                            f"governance/projects.yaml text declares {declared} {key}, actual={actual}: {text}",
                        )


def validate_project_registry_entry(validation: Validation, project: dict[str, Any], scope: str) -> None:
    for field in ("project_id", "path", "ci_mode"):
        if not value_present(project.get(field)):
            validation.error(scope, f"governance/projects.yaml project entry missing {field}")
    extra_fields = sorted(set(project) - PROJECT_REGISTRY_ALLOWED_FIELDS)
    if extra_fields:
        validation.error(
            scope,
            "governance/projects.yaml project entry carries non-registry fields: " + ", ".join(extra_fields),
        )
    migration = project.get("migration")
    if not isinstance(migration, dict):
        validation.error(scope, "governance/projects.yaml project entry missing migration.version")
        return
    version = str(migration.get("version") or "").strip()
    if version not in PROJECT_REGISTRY_MIGRATION_VERSIONS:
        validation.error(scope, f"Invalid migration.version: {version or '<empty>'}")
    extra_migration_fields = sorted(set(migration) - {"version"})
    if extra_migration_fields:
        validation.error(scope, "migration carries non-version fields: " + ", ".join(extra_migration_fields))


def validate_readme_project_list(validation: Validation, projects: list[dict[str, Any]]) -> None:
    readme = ROOT / "README.md"
    if not readme.exists():
        validation.error("root", "README.md missing")
        return
    text = readme.read_text(encoding="utf-8")
    expected = {str(project.get("project_id") or "") for project in projects}
    found = {
        match.group(1)
        for match in re.finditer(r"^\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|", text, re.M)
        if match.group(1) != "Project"
    }
    missing = sorted(expected - found)
    extra = sorted(found - expected)
    if missing or extra:
        validation.error("root", f"README project list drift: missing={missing}; extra={extra}")


def validate_assurance_status(validation: Validation, project: dict[str, Any]) -> None:
    scope = project_scope(project)
    project_path = ROOT / str(project.get("path") or "")
    path = project_path / "docs" / "governance" / "ASSURANCE_STATUS.yaml"
    if not path.exists():
        return
    data = load_yaml(path)
    if not isinstance(data, dict):
        validation.error(scope, f"{rel(path)} must be a mapping")
        return
    dimensions = data.get("dimensions")
    if not isinstance(dimensions, dict):
        validation.error(scope, f"{rel(path)} missing dimensions")
        return
    required_dimensions = {
        "structural_completeness",
        "implementation_congruence",
        "parameter_source_quality",
        "methodological_rationale",
        "empirical_validation",
        "operational_validation",
        "delivery_evidence",
        "evidence_freshness",
    }
    for dimension in sorted(required_dimensions):
        status = str((dimensions.get(dimension) or {}).get("status") or "")
        if status not in {"VERIFIED", "PARTIAL", "UNVERIFIED", "FAILED", "NOT_APPLICABLE"}:
            validation.error(scope, f"{rel(path)} {dimension}.status invalid: {status}")
    forbidden = {"machine_verified", "unknown", "partial", "blocked", "pass"}
    for dimension, payload in dimensions.items():
        status = str((payload or {}).get("status") or "")
        if status in forbidden:
            validation.error(scope, f"{rel(path)} {dimension}.status uses legacy status {status}")
    counts = project_registry_counts(project)
    impl = dimensions.get("implementation_congruence") or {}
    if int(impl.get("total_active_parameters") or -1) != counts["active_parameters"]:
        validation.error(scope, f"{rel(path)} active parameter count drift")
    if int(impl.get("total_active_formulas") or -1) != counts["active_formulas"]:
        validation.error(scope, f"{rel(path)} active formula count drift")


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
    validate_readme_project_list(validation, projects)
    validate_projects_yaml_count_claims(validation, projects)
    registered_paths = [str(project.get("path") or "").replace("\\", "/").rstrip("/") for project in projects]
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
        validate_project_registry_entry(validation, project, scope)
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
    check_human_entry_quality(validation, project_path, required, scope)
    parsed = parse_project_governance(project_path, validation, required, scope)
    check_product_roadmap_kind(validation, project, parsed, required, scope)
    check_csv_headers(validation, parsed, required, scope)
    check_cross_references(validation, parsed, required, scope)
    check_weight_groups(validation, [p for p in parsed["parameters"] if isinstance(p, dict)], required, scope)
    check_versions(validation, project_path, parsed, required, scope)
    check_manual_counts(validation, project_path, parsed, required, scope)
    validate_assurance_status(validation, project)
    check_semantic_coverage_task_binding(validation, project, parsed, required, scope)
    validate_arxiv_daily_push_v7_root_lock(validation, project_path, parsed, required, scope)


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


def parse_git_status_paths(output: str) -> set[str]:
    paths: set[str] = set()
    for line in output.splitlines():
        if not line.strip() or len(line) < 4:
            continue
        payload = line[3:].strip()
        if " -> " in payload:
            old_path, new_path = payload.split(" -> ", 1)
            if old_path.strip():
                paths.add(old_path.strip())
            if new_path.strip():
                paths.add(new_path.strip())
            continue
        paths.add(payload)
    return paths


def git_local_changed_files() -> set[str]:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", "status", "--porcelain=v1"],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        stderr = result.stderr.strip() or f"exit_{result.returncode}"
        raise GovernanceDiffError("STATUS_FAILED", f"Git status failed while collecting local changes: {stderr}")
    return parse_git_status_paths(result.stdout)


def git_changed_files(base_ref: str | None = None) -> list[str]:
    changed: set[str] = set(git_local_changed_files())
    explicit_base = explicit_base_ref(base_ref)
    if explicit_base:
        if not git_ref_exists(explicit_base):
            raise GovernanceDiffError(
                "UNRESOLVED_BASE",
                f"Explicit governance diff base does not resolve to a commit: {explicit_base}",
                base_ref=explicit_base,
            )
        try:
            output = subprocess.check_output(
                ["git", "-c", "core.quotePath=false", "diff", "--name-only", f"{explicit_base}...HEAD"],
                cwd=ROOT,
                text=True,
                encoding="utf-8",
                stderr=subprocess.PIPE,
            )
            changed.update(line.strip() for line in output.splitlines() if line.strip())
        except subprocess.CalledProcessError as exc:
            stderr = (exc.stderr or "").strip()
            detail = f": {stderr}" if stderr else ""
            raise GovernanceDiffError(
                "DIFF_FAILED",
                f"Explicit governance diff failed for base {explicit_base}{detail}",
                base_ref=explicit_base,
            ) from exc
    github_base_ref = os.environ.get("GITHUB_BASE_REF")
    if not explicit_base and github_base_ref:
        try:
            output = subprocess.check_output(
                ["git", "-c", "core.quotePath=false", "diff", "--name-only", f"origin/{github_base_ref}...HEAD"],
                cwd=ROOT,
                text=True,
                encoding="utf-8",
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


def root_required_files(config: dict[str, Any]) -> set[str]:
    root_config = config.get("root_governance") if isinstance(config.get("root_governance"), dict) else {}
    return {str(item).replace("\\", "/") for item in as_list(root_config.get("required_files"))}


def is_root_governance_change(path: str, root_required: set[str]) -> bool:
    normalized = path.replace("\\", "/")
    return normalized in root_required or any(
        normalized == prefix.rstrip("/") or normalized.startswith(prefix) for prefix in ROOT_GOVERNANCE_PREFIXES
    )


def project_id(project: dict[str, Any]) -> str:
    return str(project.get("project_id") or "")


def required_project_ids(projects: list[dict[str, Any]]) -> set[str]:
    return {project_id(project) for project in projects if str(project.get("ci_mode") or "") == "required"}


def root_changed_scope_configured_exclusions(config: dict[str, Any]) -> set[str]:
    root_config = config.get("root_governance") if isinstance(config.get("root_governance"), dict) else {}
    return {str(item) for item in as_list(root_config.get("changed_scope_excluded_projects")) if item}


def changed_scope_selection(config: dict[str, Any], changed: list[str]) -> dict[str, Any]:
    projects = [p for p in as_list(config.get("projects")) if isinstance(p, dict)]
    root_changed = any(is_root_governance_change(path, root_required_files(config)) for path in changed)
    configured_excluded = root_changed_scope_configured_exclusions(config) if root_changed else set()
    required_ids = required_project_ids(projects)
    effective_excluded = configured_excluded - required_ids
    unknown_changed = [
        path
        for path in changed
        if not is_root_governance_change(path, root_required_files(config))
        and not any(project_matches_changed(project, [path]) for project in projects)
    ]
    full_scope_required = root_changed or bool(unknown_changed)
    selected = (
        [project for project in projects if project_id(project) not in effective_excluded]
        if full_scope_required
        else [project for project in projects if project_matches_changed(project, changed)]
    )
    selected_required = {project_id(project) for project in selected if project_id(project) in required_ids}
    return {
        "changed_files": changed,
        "root_governance_changed": root_changed,
        "unknown_changed_files": unknown_changed,
        "full_scope_required": full_scope_required,
        "projects": selected,
        "configured_root_scope_excluded_projects": sorted(configured_excluded),
        "root_scope_excluded_projects": sorted(effective_excluded),
        "root_scope_configured_excluded_required_projects": sorted(configured_excluded & required_ids),
        "all_required_projects_covered": bool(full_scope_required and required_ids <= selected_required),
        "required_project_count": len(required_ids),
        "selected_required_project_count": len(selected_required),
    }


def select_projects(config: dict[str, Any], args: argparse.Namespace) -> list[dict[str, Any]]:
    projects = [p for p in as_list(config.get("projects")) if isinstance(p, dict)]
    if args.project:
        selected = [p for p in projects if p.get("project_id") == args.project or p.get("path") == args.project]
        if not selected:
            raise SystemExit(f"Unknown project: {args.project}")
        return selected
    if args.changed_only:
        changed = git_changed_files(getattr(args, "base_ref", None))
        return list(changed_scope_selection(config, changed)["projects"])
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
    except GovernanceDiffError as exc:
        validation.error("root", str(exc))
        print_summary(validation, [])
        return 1
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
