#!/usr/bin/env python3
"""Diff-driven and semantic governance validation for CodexProject.

This validator complements ``validate_project_governance.py``. The structural
validator proves that files parse and cross-reference. This module proves the
review-5 contract: meaningful code/config/test changes must travel with the
governance records that make those changes auditable.
"""

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
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import validate_project_governance as structural
import validate_semantic_extractors


sys.dont_write_bytecode = True

ROOT = structural.ROOT
PROJECTS_FILE = structural.PROJECTS_FILE
RUN_MANIFESTS_DIR = ROOT / "governance" / "run_manifests"
CI_ATTESTATIONS_DIR = ROOT / "governance" / "ci_attestations"
PENDING_CI_MAX_AGE = timedelta(hours=24)
RUN_MANIFEST_REQUIRED_FIELDS = {
    "schema_version",
    "run_id",
    "project_id",
    "task_id",
    "acceptance_ids",
    "iteration_id",
    "generated_at",
    "implementation_base_sha",
    "content_tree_hash",
    "changed_files_declared",
    "changed_files_actual",
    "required_governance_files",
    "updated_governance_files",
    "test_commands",
    "test_results",
    "evidence_refs",
    "binding_status",
    "ci_attestation_subject",
    "ci_run_reference",
}
RUN_MANIFEST_BINDING_STATUSES = {
    "PRECOMMIT_TREE_BOUND",
    "COMMIT_BOUND",
    "CI_ATTESTED",
    "LEGACY_UNBOUND",
}
ROOT_GOVERNANCE_PREFIXES = (
    ".agents/",
    ".codex/",
    ".github/workflows/project-governance.yml",
    "AGENTS.md",
    "README.md",
    "docs/governance/",
    "governance/",
    "scripts/generate_governance_dashboard.py",
    "scripts/governance_setup_doctor.py",
    "scripts/validate_information_quality.py",
    "scripts/validate_governance_sync.py",
    "scripts/validate_project_governance.py",
    "tests/governance/",
)
PROJECT_GOVERNANCE_FILES = {
    "MODEL_SPEC.md",
    "model_registry.yaml",
    "formula_registry.yaml",
    "parameter_registry.csv",
    "DEVELOPMENT_LEDGER.md",
    "development_events.jsonl",
    "DELIVERY_PLAN.md",
    "delivery_tasks.yaml",
    "VERSION_MATRIX.yaml",
    "TRACEABILITY_MATRIX.csv",
    "ASSURANCE_STATUS.yaml",
    "STATUS.md",
    "OWNER_STATUS.md",
    "events.jsonl",
    "evidence_index.yaml",
    "model_extraction.yaml",
    "owner_roa_review.yaml",
    "performance_report.yaml",
    "project.yaml",
    "rollback_test.yaml",
    "roadmap_draft.yaml",
    "roadmap.yaml",
}
PROJECT_GOVERNANCE_TOOL_FILES = {
    "scripts/manage_clean_room_release.py",
    "scripts/manage_release_artifacts.py",
    "tests/unit/test_clean_room_release_paths.py",
}
COMMON_REQUIRED_BY_CLASS = {
    "model_behavior_change": {
        "docs/governance/MODEL_SPEC.md",
        "docs/governance/model_registry.yaml",
        "docs/governance/formula_registry.yaml",
        "docs/governance/parameter_registry.csv",
        "docs/governance/DEVELOPMENT_LEDGER.md",
        "docs/governance/development_events.jsonl",
        "docs/governance/delivery_tasks.yaml",
        "docs/governance/TRACEABILITY_MATRIX.csv",
        "docs/governance/VERSION_MATRIX.yaml",
        "docs/governance/STATUS.md",
        "docs/governance/OWNER_STATUS.md",
        "CHANGELOG.md",
    },
    "parameter_or_config_change": {
        "docs/governance/parameter_registry.csv",
        "docs/governance/DEVELOPMENT_LEDGER.md",
        "docs/governance/development_events.jsonl",
        "docs/governance/delivery_tasks.yaml",
        "docs/governance/TRACEABILITY_MATRIX.csv",
        "docs/governance/VERSION_MATRIX.yaml",
        "docs/governance/STATUS.md",
        "docs/governance/OWNER_STATUS.md",
        "CHANGELOG.md",
    },
    "data_snapshot_change": {
        "docs/governance/DEVELOPMENT_LEDGER.md",
        "docs/governance/development_events.jsonl",
        "docs/governance/TRACEABILITY_MATRIX.csv",
        "docs/governance/VERSION_MATRIX.yaml",
        "docs/governance/STATUS.md",
        "docs/governance/OWNER_STATUS.md",
    },
    "test_or_evidence_change": {
        "docs/governance/DEVELOPMENT_LEDGER.md",
        "docs/governance/development_events.jsonl",
        "docs/governance/delivery_tasks.yaml",
        "docs/governance/TRACEABILITY_MATRIX.csv",
        "docs/governance/STATUS.md",
        "docs/governance/OWNER_STATUS.md",
    },
    "product_capability_change": {
        "docs/governance/DEVELOPMENT_LEDGER.md",
        "docs/governance/development_events.jsonl",
        "docs/governance/delivery_tasks.yaml",
        "docs/governance/TRACEABILITY_MATRIX.csv",
        "docs/governance/VERSION_MATRIX.yaml",
        "docs/governance/STATUS.md",
        "docs/governance/OWNER_STATUS.md",
        "CHANGELOG.md",
    },
}


@dataclass
class SyncIssue:
    level: str
    scope: str
    message: str


@dataclass
class ProjectChange:
    project: dict[str, Any]
    files: list[str] = field(default_factory=list)
    classifications: set[str] = field(default_factory=set)
    required_governance_files: set[str] = field(default_factory=set)
    updated_governance_files: set[str] = field(default_factory=set)


class SyncValidation:
    def __init__(self) -> None:
        self.issues: list[SyncIssue] = []

    def error(self, scope: str, message: str) -> None:
        self.issues.append(SyncIssue("ERROR", scope, message))

    def warn(self, scope: str, message: str) -> None:
        self.issues.append(SyncIssue("WARN", scope, message))

    @property
    def errors(self) -> list[SyncIssue]:
        return [issue for issue in self.issues if issue.level == "ERROR"]

    @property
    def warnings(self) -> list[SyncIssue]:
        return [issue for issue in self.issues if issue.level == "WARN"]


def git_output(args: list[str], *, default: str = "") -> str:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.stdout if result.returncode == 0 else default


def current_commit() -> str:
    return git_output(["rev-parse", "HEAD"]).strip()


def tree_hash(paths: list[str] | None = None) -> str:
    if paths:
        digest = hashlib.sha256()
        for path in sorted(paths):
            full = ROOT / path
            digest.update(path.encode("utf-8"))
            if full.exists() and full.is_file():
                digest.update(full.read_bytes())
        return digest.hexdigest()
    return git_output(["rev-parse", "HEAD^{tree}"]).strip()


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
    return bool(git_output(["rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"]).strip())


def merge_base(base_ref: str | None = None) -> str | None:
    explicit = explicit_base_ref(base_ref)
    if explicit:
        return explicit if git_ref_exists(explicit) else None
    candidates = []
    github_base_ref = os.environ.get("GITHUB_BASE_REF")
    if github_base_ref:
        candidates.append(f"origin/{github_base_ref}")
    candidates.append("origin/main")
    for candidate in candidates:
        value = git_output(["merge-base", candidate, "HEAD"]).strip()
        if value:
            return value
    return None


def changed_files_against_base(base: str | None) -> list[str]:
    changed: set[str] = set()
    if base:
        changed.update(
            line.strip()
            for line in git_output(["diff", "--name-only", f"{base}...HEAD"]).splitlines()
            if line.strip()
        )
    for command in (
        ["diff", "--name-only", "--cached"],
        ["diff", "--name-only"],
        ["ls-files", "--others", "--exclude-standard"],
    ):
        changed.update(line.strip() for line in git_output(command).splitlines() if line.strip())
    return sorted(path for path in changed if not is_ignored_changed_file(path))


def is_ignored_changed_file(path: str) -> bool:
    return path.startswith(("artifacts/", "outputs/", "generated-artifacts/", "backups/"))


def load_projects() -> dict[str, Any]:
    data = structural.load_yaml(PROJECTS_FILE)
    if not isinstance(data, dict):
        raise ValueError(f"{PROJECTS_FILE} did not parse to a mapping")
    return data


def project_scope(project: dict[str, Any]) -> str:
    return structural.project_scope(project)


def under_project(path: str, project: dict[str, Any]) -> bool:
    project_path = str(project.get("path") or "").rstrip("/")
    return bool(project_path) and (path == project_path or path.startswith(project_path + "/"))


def project_relative(path: str, project: dict[str, Any]) -> str:
    prefix = str(project.get("path") or "").rstrip("/") + "/"
    return path[len(prefix) :] if path.startswith(prefix) else path


def is_root_governance_change(path: str) -> bool:
    return any(path == prefix.rstrip("/") or path.startswith(prefix) for prefix in ROOT_GOVERNANCE_PREFIXES)


def is_project_governance_file(rel_path: str) -> bool:
    if rel_path in {"VERSION", "CHANGELOG.md"}:
        return True
    if not rel_path.startswith("docs/governance/"):
        return False
    name = rel_path.removeprefix("docs/governance/")
    return name in PROJECT_GOVERNANCE_FILES


def is_project_governance_tool_file(rel_path: str) -> bool:
    return rel_path in PROJECT_GOVERNANCE_TOOL_FILES


def is_generated_release_artifact(rel_path: str) -> bool:
    if rel_path in {"CHECKSUMS.sha256", "DIRECTORY_TREE.txt", "manifest.txt"}:
        return True
    if rel_path.startswith("artifacts/release_") and rel_path.endswith((".json", ".jsonl")):
        return True
    if rel_path.startswith("artifacts/tests/") and "clean_room_release" in rel_path:
        return True
    if rel_path.startswith("artifacts/tests/") and "clean_room" in rel_path and rel_path.endswith(".zip"):
        return True
    return False


def classify_project_file(project: dict[str, Any], path: str) -> set[str]:
    rel = project_relative(path, project)
    classes: set[str] = set()
    if is_project_governance_file(rel):
        classes.add("governance_only_change")
        return classes
    if is_project_governance_tool_file(rel):
        classes.add("governance_only_change")
        return classes
    if is_generated_release_artifact(rel):
        classes.add("generated_artifact_change")
        return classes
    lower = rel.lower()
    if lower.startswith(("tests/", "test/")) or "/tests/" in lower or lower.endswith(("_test.py", ".spec.ts", ".test.ts")):
        classes.add("test_or_evidence_change")
    if lower.startswith(("artifacts/", "evidence/", "outputs/")) or "evidence" in lower:
        classes.add("test_or_evidence_change")
    if lower.startswith(("data/", "datasets/")):
        classes.add("data_snapshot_change")
    if lower.startswith(("config/", "configs/")) or lower.endswith((".toml", ".yaml", ".yml", ".json", ".ini")):
        classes.add("parameter_or_config_change")
    behavior_keywords = (
        "scoring",
        "score",
        "weight",
        "threshold",
        "formula",
        "model",
        "strategy",
        "rule",
        "parameter",
        "rank",
        "risk",
        "salary",
        "backtest",
        "pipeline",
        "metrics",
    )
    if any(keyword in lower for keyword in behavior_keywords):
        classes.add("model_behavior_change")
    for pattern in structural.as_list(project.get("model_behavior_globs")):
        if fnmatch.fnmatch(rel, str(pattern)):
            classes.add("model_behavior_change")
            if not lower.startswith(("tests/", "docs/")):
                classes.add("product_capability_change")
    if lower.endswith((".py", ".ts", ".tsx", ".js", ".mjs", ".swift", ".go")) and not lower.startswith("tests/"):
        classes.add("product_capability_change")
    if not classes:
        classes.add("trivial_change")
    return classes


def classify_changes(config: dict[str, Any], changed: list[str]) -> tuple[list[ProjectChange], list[str]]:
    projects = [p for p in structural.as_list(config.get("projects")) if isinstance(p, dict)]
    by_project: list[ProjectChange] = []
    root_changes: list[str] = []
    for project in projects:
        change = ProjectChange(project=project)
        path = str(project.get("path") or "").rstrip("/")
        for filename in changed:
            if not under_project(filename, project):
                continue
            change.files.append(filename)
            rel = project_relative(filename, project)
            if is_project_governance_file(rel):
                change.updated_governance_files.add(rel)
            for classification in classify_project_file(project, filename):
                change.classifications.add(classification)
                change.required_governance_files.update(COMMON_REQUIRED_BY_CLASS.get(classification, set()))
        if change.files:
            by_project.append(change)
    for filename in changed:
        if is_root_governance_change(filename) and not any(under_project(filename, p) for p in projects):
            root_changes.append(filename)
    return by_project, sorted(set(root_changes))


def validate_diff_contract(validation: SyncValidation, project_changes: list[ProjectChange]) -> None:
    for change in project_changes:
        scope = project_scope(change.project)
        actionable_classes = change.classifications - {"governance_only_change", "trivial_change"}
        if not actionable_classes:
            continue
        missing = sorted(change.required_governance_files - change.updated_governance_files)
        if missing:
            validation.error(
                scope,
                "Changed files classified as "
                + ", ".join(sorted(actionable_classes))
                + " but required governance files were not updated: "
                + ", ".join(missing),
            )


def base_file_text(base: str | None, path: str) -> str | None:
    if not base:
        return None
    result = subprocess.run(
        ["git", "show", f"{base}:{path}"],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.stdout if result.returncode == 0 else None


def validate_append_only(validation: SyncValidation, changed: list[str], base: str | None) -> None:
    for path in changed:
        if not path.endswith("docs/governance/development_events.jsonl"):
            continue
        new_path = ROOT / path
        if not new_path.exists():
            validation.error(path, "development_events.jsonl was deleted")
            continue
        old = base_file_text(base, path)
        if old is None:
            continue
        new = new_path.read_text(encoding="utf-8")
        if not new.startswith(old):
            if not binding_classification_only(old, new):
                validation.error(path, "development_events.jsonl is append-only; existing lines were modified or removed")


def binding_classification_only(old: str, new: str) -> bool:
    old_lines = [line for line in old.splitlines() if line.strip()]
    new_lines = [line for line in new.splitlines() if line.strip()]
    if len(new_lines) < len(old_lines):
        return False
    allowed_added = {
        "binding_status",
        "binding_rationale",
        "ci_attestation_ref",
        "original_timestamp",
        "stale_classification_reason",
        "timestamp_correction_rationale",
        "unresolved_fact_ids",
    }
    for idx, old_line in enumerate(old_lines):
        try:
            old_event = json.loads(old_line)
            new_event = json.loads(new_lines[idx])
        except json.JSONDecodeError:
            return False
        if not isinstance(old_event, dict) or not isinstance(new_event, dict):
            return False
        for key, value in old_event.items():
            if key == "timestamp" and new_event.get("original_timestamp") == value:
                continue
            if key == "binding_status" and value == "pre_commit_pending" and new_event.get(key) == "stale_unbound":
                continue
            if new_event.get(key) != value:
                return False
        if set(new_event) - set(old_event) - allowed_added:
            return False
    return True


def validate_event_files_changed(validation: SyncValidation, project_changes: list[ProjectChange]) -> None:
    for change in project_changes:
        event_path = "docs/governance/development_events.jsonl"
        if event_path not in change.updated_governance_files:
            continue
        project_path = ROOT / str(change.project.get("path") or "")
        full_event_path = project_path / event_path
        if not full_event_path.exists():
            continue
        try:
            events = structural.load_jsonl(full_event_path)
        except Exception as exc:
            validation.error(project_scope(change.project), f"Cannot parse latest development event for diff sync: {exc}")
            continue
        if not events or not isinstance(events[-1], dict):
            validation.error(project_scope(change.project), "development_events.jsonl must end with a JSON object event")
            continue
        recorded = {str(item) for item in structural.as_list(events[-1].get("files_changed"))}
        exclusions = {str(item) for item in structural.as_list(events[-1].get("files_changed_exclusions"))}
        actual = set(change.files)
        ignored_suffixes = {
            f"{change.project.get('path')}/docs/governance/development_events.jsonl",
        }
        actual_for_event = {item for item in actual if item not in ignored_suffixes and item not in exclusions}
        missing = sorted(actual_for_event - recorded)
        if missing:
            validation.error(
                project_scope(change.project),
                "Latest development event files_changed does not cover actual diff files: " + ", ".join(missing),
            )


def latest_event_iteration(events: list[Any]) -> str | None:
    latest: dict[str, Any] | None = None
    for event in events:
        if not isinstance(event, dict):
            continue
        if str(event.get("fact_level") or event.get("evidence_level") or "").upper() == "RECONSTRUCTED":
            continue
        latest = event
    if not latest:
        return None
    iteration_id = str(latest.get("iteration_id") or "").strip()
    if iteration_id:
        return iteration_id
    event_id = str(latest.get("event_id") or "").strip()
    return event_id if event_id.startswith("ITER-") else None


def count_confirmed_iterations(ledger_text: str) -> int | None:
    section_match = re.search(r"## Confirmed Iterations(?P<body>.*?)(?:\n## |\Z)", ledger_text, re.S)
    if not section_match:
        return None
    body = section_match.group("body")
    return len(re.findall(r"^###\s+`?ITER-", body, re.M))


def declared_confirmed_iterations(ledger_text: str) -> int | None:
    match = re.search(r"Confirmed iteration(?:s| count)?:\s*`?(\d+)`?", ledger_text, re.I)
    return int(match.group(1)) if match else None


def ref_to_path(ref: str, project_path: Path) -> Path | None:
    value = str(ref or "").strip().strip("`").strip()
    if not value or value.upper() in {"UNKNOWN", "NOT_APPLICABLE", "N/A", "NA", "PENDING", "NONE"}:
        return None
    if value.startswith(("http://", "https://", "GitHub Actions", "git ", "FOCUSED:", "BLOCKED:", "PASS:")):
        return None
    if " " in value and not value.startswith(("./", "../")):
        return None
    value = value.split("#", 1)[0]
    value = value.split("::", 1)[0]
    value = value.split(":", 1)[0]
    value = value.strip()
    if not value or "*" in value:
        return None
    path = ROOT / value if (ROOT / value).exists() else project_path / value
    return path


def iter_refs(value: Any) -> list[str]:
    refs: list[str] = []
    if isinstance(value, str):
        refs.extend(part.strip() for part in re.split(r"[;,|]", value) if part.strip())
    elif isinstance(value, list):
        for item in value:
            refs.extend(iter_refs(item))
    elif isinstance(value, dict):
        for key in ("path", "file", "ref", "source"):
            if key in value:
                refs.extend(iter_refs(value[key]))
    return refs


def validate_semantic_project(validation: SyncValidation, project: dict[str, Any]) -> dict[str, Any]:
    scope = project_scope(project)
    project_path = ROOT / str(project.get("path") or "")
    parsed_validation = structural.Validation()
    parsed = structural.parse_project_governance(project_path, parsed_validation, True, scope)
    summary = {
        "current_iteration": None,
        "latest_event_iteration": None,
        "confirmed_iterations_declared": None,
        "confirmed_iterations_actual": None,
        "unbound_event_count": 0,
        "semantic_parameters_checked": 0,
        "semantic_formulas_checked": 0,
    }
    matrix = parsed.get("version_matrix") or {}
    if isinstance(matrix, dict):
        summary["current_iteration"] = matrix.get("current_iteration")
    events = [event for event in parsed.get("events", []) if isinstance(event, dict)]
    latest_iter = latest_event_iteration(events)
    summary["latest_event_iteration"] = latest_iter
    if summary["current_iteration"] and latest_iter and str(summary["current_iteration"]) != latest_iter:
        validation.error(scope, f"VERSION_MATRIX.current_iteration={summary['current_iteration']} but latest event iteration is {latest_iter}")
    ledger = project_path / "docs" / "governance" / "DEVELOPMENT_LEDGER.md"
    if ledger.exists():
        text = ledger.read_text(encoding="utf-8")
        declared = declared_confirmed_iterations(text)
        actual = count_confirmed_iterations(text)
        summary["confirmed_iterations_declared"] = declared
        summary["confirmed_iterations_actual"] = actual
        if declared is not None and actual is not None and declared != actual:
            validation.error(scope, f"DEVELOPMENT_LEDGER confirmed iteration count {declared} does not match actual {actual}")
        if re.search(r"only confirmed\s+iteration", text, re.I) and declared and declared > 1:
            validation.error(scope, "DEVELOPMENT_LEDGER says only one confirmed iteration while declaring multiple iterations")
    for event in events:
        if str(event.get("git_commit") or "").upper() == "PENDING" and str(event.get("result_commit") or "").upper() in {"", "PENDING"}:
            summary["unbound_event_count"] += 1
    # Reference existence: this is machine-verifiable and safe to enforce.
    items: list[tuple[str, dict[str, Any]]] = []
    for key in ("models", "formulas", "parameters", "tasks", "traceability"):
        for row in parsed.get(key, []):
            if isinstance(row, dict):
                items.append((key, row))
    for group, row in items:
        identifier = (
            row.get("model_id")
            or row.get("formula_id")
            or row.get("parameter_id")
            or row.get("task_id")
            or row.get("requirement_id")
            or "<unknown>"
        )
        for field_name in ("code_refs", "code_ref", "config_ref", "test_refs", "test_ref"):
            for ref in iter_refs(row.get(field_name)):
                candidate = ref_to_path(ref, project_path)
                if candidate is not None and not candidate.exists():
                    validation.error(scope, f"{identifier}: {field_name} points to missing path {ref}")
    if bool(project.get("semantic_extractors")):
        extractor_issues, extractor_summary = validate_semantic_extractors.validate_project_semantics(project_path, scope)
        summary.update(extractor_summary)
        for issue in extractor_issues:
            if issue.level == "ERROR":
                validation.error(issue.scope, issue.message)
            else:
                validation.warn(issue.scope, issue.message)
    return summary


def validate_semantic(validation: SyncValidation, projects: list[dict[str, Any]]) -> dict[str, Any]:
    summaries: dict[str, Any] = {}
    for project in projects:
        summaries[project_scope(project)] = validate_semantic_project(validation, project)
    return summaries


def root_sync_requirements(validation: SyncValidation, root_changes: list[str], changed: list[str]) -> None:
    if not root_changes:
        return
    manifest_only = all(path.startswith("governance/run_manifests/") and path.endswith(".json") for path in root_changes)
    if manifest_only:
        return
    required_markers = {
        "run_manifest": any(path.startswith("governance/run_manifests/") and path.endswith(".json") for path in changed),
        "governance_tests": any(path.startswith("tests/governance/") for path in changed),
    }
    for label, present in required_markers.items():
        if not present:
            validation.error("root", f"Root governance change requires updated {label}")


def load_json_object(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def attested_manifest_ids() -> set[str]:
    ids: set[str] = set()
    for path in sorted(CI_ATTESTATIONS_DIR.glob("*.json")):
        data = load_json_object(path)
        if not data:
            continue
        bound = str(data.get("binds_run_manifest") or "").strip()
        conclusion = str(data.get("conclusion") or "").strip()
        if bound and conclusion == "success":
            ids.add(bound)
    return ids


def validate_pending_ci_bindings(validation: SyncValidation) -> None:
    attested = attested_manifest_ids()
    for path in sorted(RUN_MANIFESTS_DIR.glob("*.json")):
        data = load_json_object(path)
        if not data:
            validation.error("root", f"Cannot parse run manifest: {path.relative_to(ROOT)}")
            continue
        run_id = str(data.get("run_id") or path.stem)
        observed = [str(item) for item in structural.as_list(data.get("observed_results"))]
        pending = str(data.get("finished_at") or "").upper() == "PENDING_CI" or any(
            "PENDING_GITHUB_ACTIONS" in item for item in observed
        )
        if pending and run_id not in attested:
            started_raw = str(data.get("started_at") or "")
            stale = True
            try:
                started = datetime.fromisoformat(started_raw.replace("Z", "+00:00"))
                stale = datetime.now(started.tzinfo or timezone.utc) - started > PENDING_CI_MAX_AGE
            except ValueError:
                stale = True
            message = f"{path.relative_to(ROOT)} is PENDING_CI without a matching governance/ci_attestations binding"
            if stale:
                validation.error("root", message)
            else:
                validation.warn("root", message + " (within allowed binding window)")


def validate_run_manifests(validation: SyncValidation, changed: list[str], *, changed_only: bool = False) -> None:
    changed_set = set(changed)
    for path in sorted(RUN_MANIFESTS_DIR.glob("*.json")):
        relative = path.relative_to(ROOT).as_posix()
        if changed_only and relative not in changed_set:
            continue
        data = load_json_object(path)
        if not data:
            validation.error("root", f"Cannot parse run manifest: {path.relative_to(ROOT)}")
            continue
        schema_version = int(data.get("schema_version") or 1)
        if schema_version < 2:
            continue
        run_id = str(data.get("run_id") or path.stem)
        missing = sorted(field for field in RUN_MANIFEST_REQUIRED_FIELDS if not data.get(field))
        if missing:
            validation.error("root", f"{path.relative_to(ROOT)} missing Review7 required fields: {', '.join(missing)}")
        binding_status = str(data.get("binding_status") or "")
        if binding_status not in RUN_MANIFEST_BINDING_STATUSES:
            validation.error("root", f"{path.relative_to(ROOT)} invalid binding_status: {binding_status}")
        for field in ("result_commit", "finished_at", "ci_run_reference"):
            if str(data.get(field) or "").strip().upper() == "PENDING":
                validation.error("root", f"{path.relative_to(ROOT)} contains bare PENDING in {field}")
        declared = {str(item) for item in structural.as_list(data.get("changed_files_actual"))}
        if relative in changed_set:
            missing_changed = sorted(changed_set - declared)
            if missing_changed:
                validation.error(
                    "root",
                    f"{path.relative_to(ROOT)} changed_files_actual does not cover actual diff files: {', '.join(missing_changed[:20])}",
                )
        if str(data.get("content_tree_hash") or "").strip().upper() in {"", "PENDING", "UNKNOWN"}:
            validation.error("root", f"{path.relative_to(ROOT)} lacks content_tree_hash")


def build_drift_report(config: dict[str, Any], semantic_summaries: dict[str, Any]) -> dict[str, Any]:
    return {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "commit": current_commit(),
        "tree_hash": tree_hash(),
        "projects": semantic_summaries,
        "required_projects": [
            project_scope(p)
            for p in structural.as_list(config.get("projects"))
            if isinstance(p, dict) and structural.is_required(p)
        ],
    }


def print_summary(validation: SyncValidation, changed: list[str], project_changes: list[ProjectChange]) -> None:
    print("CodexProject governance sync validation")
    print("changed_files: " + (", ".join(changed) if changed else "none"))
    print("projects changed: " + (", ".join(project_scope(c.project) for c in project_changes) if project_changes else "none"))
    print(f"errors: {len(validation.errors)}")
    print(f"warnings: {len(validation.warnings)}")
    for issue in validation.issues:
        print(f"[{issue.level}] {issue.scope}: {issue.message}")


def validate(
    *,
    all_projects: bool = False,
    changed_only: bool = False,
    enforce_sync: bool = False,
    semantic: bool = False,
    drift_report: bool = False,
    base_ref: str | None = None,
) -> tuple[int, dict[str, Any]]:
    config = load_projects()
    explicit_base = explicit_base_ref(base_ref)
    base = merge_base(base_ref)
    changed = changed_files_against_base(base) if changed_only or enforce_sync else []
    project_changes, root_changes = classify_changes(config, changed)
    validation = SyncValidation()
    if enforce_sync and explicit_base and base is None:
        validation.error("root", f"Explicit governance diff base does not resolve to a commit: {explicit_base}")
    semantic_summaries: dict[str, Any] = {}
    if enforce_sync:
        validate_diff_contract(validation, project_changes)
        validate_append_only(validation, changed, base)
        validate_event_files_changed(validation, project_changes)
        root_sync_requirements(validation, root_changes, changed)
    if semantic or all_projects or drift_report:
        if all_projects or drift_report or not changed_only:
            semantic_projects = [p for p in structural.as_list(config.get("projects")) if isinstance(p, dict)]
            semantic_summaries = validate_semantic(validation, semantic_projects)
            validate_pending_ci_bindings(validation)
            validate_run_manifests(validation, changed)
        else:
            semantic_projects = [change.project for change in project_changes]
            semantic_summaries = validate_semantic(validation, semantic_projects)
            validate_run_manifests(validation, changed, changed_only=True)
    report = build_drift_report(config, semantic_summaries) if drift_report else {}
    print_summary(validation, changed, project_changes)
    if drift_report:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return (1 if validation.errors else 0), report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--all", action="store_true", help="Run semantic checks for all projects.")
    parser.add_argument("--changed-only", action="store_true", help="Inspect changed files against merge base and worktree.")
    parser.add_argument("--base-ref", help="Explicit base commit/ref for changed-only diff validation.")
    parser.add_argument("--enforce-sync", action="store_true", help="Fail when changed files are missing required governance updates.")
    parser.add_argument("--semantic", action="store_true", help="Run semantic consistency checks.")
    parser.add_argument("--drift-report", action="store_true", help="Print machine-readable drift report after validation.")
    args = parser.parse_args(argv)
    exit_code, _ = validate(
        all_projects=args.all,
        changed_only=args.changed_only,
        enforce_sync=args.enforce_sync,
        semantic=args.semantic,
        drift_report=args.drift_report,
        base_ref=args.base_ref,
    )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
