#!/usr/bin/env python3
"""Single-entry Lean v2 governance CLI."""

from __future__ import annotations

import argparse
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
    if args.command == "validate":
        return governance.main(build_validate_argv(args))
    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
