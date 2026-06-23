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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    baseline = subparsers.add_parser("baseline", help="Print a read-only repository baseline summary.")
    baseline.add_argument("--all", action="store_true", help="Inspect root governance and all registered projects.")
    args = parser.parse_args(argv)
    if args.command == "baseline":
        if not args.all:
            parser.error("baseline currently requires --all")
        summary = build_baseline(ROOT, PROJECTS_FILE)
        print(json.dumps(summary, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
        return 0
    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
