#!/usr/bin/env python3
"""Validate canonical command ownership, safe modes, CI routing and dead refs."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any


DEFAULT_CONTRACT = Path("config/command_ownership.json")
WRITE_COMMANDS = {
    "sync",
    "build-atlas",
    "analyze",
    "push",
    "generate-personalization-prompt",
    "chatgpt-deep-explore",
    "deep-explore",
    "proposals",
    "apply",
}
ACTIVE_SOURCE_SUFFIXES = {".py", ".cjs", ".mjs", ".js", ".ts", ".tsx", ".yml", ".yaml", ".md"}


def find_implicit_mode_callers(repo_root: Path) -> list[str]:
    roots = [
        repo_root / ".github",
        repo_root / "OpenAIDatabase/apps",
        repo_root / "OpenAIDatabase/scripts",
        repo_root / "OpenAIDatabase/tests",
        repo_root / "OpenAIDatabase/README.md",
        repo_root / "OpenAIDatabase/AGENTS.md",
    ]
    failures: set[str] = set()
    patterns = (
        re.compile(r"""\[[^\[\]]{0,1600}?[\'"]scripts/atlasctl\.py[\'"][^\[\]]{0,1600}?\]""", re.S),
        re.compile(r"[^\n]{0,120}atlasctl\.py[^\n]{0,300}"),
    )
    for root in roots:
        if root.is_file():
            paths = [root]
        else:
            paths = []
            for directory, dirnames, filenames in os.walk(root):
                dirnames[:] = sorted(
                    name for name in dirnames if name not in {"node_modules", "dist"}
                )
                paths.extend(Path(directory) / name for name in sorted(filenames))
        for path in paths:
            if (
                not path.is_file()
                or path.suffix not in ACTIVE_SOURCE_SUFFIXES
                or any(part in {"node_modules", "dist"} for part in path.parts)
            ):
                continue
            source = path.read_text(encoding="utf-8", errors="ignore")
            for pattern in patterns:
                for match in pattern.finditer(source):
                    candidate = re.sub(r"\s+", " ", match.group())
                    commands = [
                        command
                        for command in sorted(WRITE_COMMANDS)
                        if re.search(rf"(?<![\w-]){re.escape(command)}(?![\w-])", candidate)
                    ]
                    if commands and "--dry-run" not in candidate and "--apply" not in candidate:
                        line = source.count("\n", 0, match.start()) + 1
                        relative = path.relative_to(repo_root)
                        failures.add(f"{relative}:{line}:{','.join(commands)}")
    return sorted(failures)


def validate(contract: dict[str, Any], database_dir: Path, repo_root: Path) -> dict[str, Any]:
    errors: list[str] = []
    commands = contract.get("canonical_commands") or []
    capabilities = [str(row.get("capability")) for row in commands]
    duplicate_capabilities = sorted(
        key for key, count in Counter(capabilities).items() if count > 1
    )
    if duplicate_capabilities:
        errors.append(f"duplicate canonical capability owners: {duplicate_capabilities}")

    missing_implementations = []
    for row in commands:
        implementation = database_dir / str(row.get("implementation") or "")
        if not implementation.is_file():
            missing_implementations.append(str(row.get("implementation")))
    if missing_implementations:
        errors.append(f"missing command implementations: {missing_implementations}")

    atlasctl = database_dir / "scripts/atlasctl.py"
    missing_mode_flags: list[str] = []
    for row in contract.get("write_commands") or []:
        subcommand = str(row["subcommand"])
        result = subprocess.run(
            [sys.executable, str(atlasctl), subcommand, "--help"],
            cwd=database_dir,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            missing_mode_flags.append(f"{subcommand}:help_exit_{result.returncode}")
            continue
        for flag in row.get("required_modes") or []:
            if str(flag) not in result.stdout:
                missing_mode_flags.append(f"{subcommand}:{flag}")
    if missing_mode_flags:
        errors.append(f"write commands missing explicit modes: {missing_mode_flags}")

    implicit_mode_callers = find_implicit_mode_callers(repo_root)
    if implicit_mode_callers:
        errors.append(f"active write invocations missing explicit mode: {implicit_mode_callers}")

    source = atlasctl.read_text(encoding="utf-8")
    alias_errors = []
    for row in contract.get("deprecated_thin_aliases") or []:
        alias = str(row["alias"])
        canonical = str(row["canonical"])
        if alias not in source or canonical not in source or "DEPRECATED thin alias" not in source:
            alias_errors.append(alias)
        if int(row.get("business_logic_lines", -1)) != 0 or not row.get("removal_condition"):
            alias_errors.append(f"{alias}:invalid_contract")
    if alias_errors:
        errors.append(f"deprecated alias contract failures: {alias_errors}")

    workflow_path = repo_root / str((contract.get("ci_policy") or {}).get("workflow"))
    workflow = workflow_path.read_text(encoding="utf-8")
    missing_ci = [
        value
        for value in (contract.get("ci_policy") or {}).get("required_invocations") or []
        if str(value) not in workflow
    ]
    if missing_ci:
        errors.append(f"CI canonical invocations missing: {missing_ci}")
    direct_legacy = []
    for name in (contract.get("ci_policy") or {}).get("forbidden_direct_runtime_scripts") or []:
        pattern = re.compile(rf"^\s*run:\s+python(?:3)?\s+scripts/{re.escape(str(name))}(?:\s|$)", re.M)
        if pattern.search(workflow):
            direct_legacy.append(str(name))
    if direct_legacy:
        errors.append(f"CI directly invokes legacy implementation scripts: {direct_legacy}")

    allowed_dead_ref_paths = {
        "OpenAIDatabase/config/command_ownership.json",
        "OpenAIDatabase/scripts/validate_command_ownership.py",
        "OpenAIDatabase/tests/test_command_ownership.py",
        "OpenAIDatabase/CHANGELOG.md",
        "OpenAIDatabase/docs/governance/events.jsonl",
        "OpenAIDatabase/docs/governance/project.yaml",
        "OpenAIDatabase/docs/governance/roadmap.yaml",
        "OpenAIDatabase/功能清单.md",
        "OpenAIDatabase/开发记录.md",
    }
    active_dead_refs: list[str] = []
    for row in contract.get("dead_scripts") or []:
        relative = str(row["path"])
        if (database_dir / relative).exists():
            errors.append(f"dead script still exists: {relative}")
        basename = Path(relative).name
        result = subprocess.run(
            [
                "git",
                "grep",
                "-l",
                "--",
                basename,
                ".github",
                "OpenAIDatabase/apps",
                "OpenAIDatabase/config",
                "OpenAIDatabase/scripts",
                "OpenAIDatabase/tests",
                "OpenAIDatabase/AGENTS.md",
                "OpenAIDatabase/README.md",
            ],
            cwd=repo_root,
            text=True,
            capture_output=True,
            check=False,
        )
        for path in result.stdout.splitlines():
            if path in allowed_dead_ref_paths or path.startswith("governance/run_manifests/"):
                continue
            active_dead_refs.append(path)
    if active_dead_refs:
        errors.append(f"active deleted-script references remain: {active_dead_refs}")

    script_files = [
        path
        for path in (database_dir / "scripts").iterdir()
        if path.is_file() and path.suffix in {".py", ".cjs"}
    ]
    inventory = contract.get("inventory") or {}
    expected_count = int(
        inventory.get("top_level_script_entrypoints_current", inventory.get("top_level_script_entrypoints_after", -1))
    )
    if len(script_files) != expected_count:
        errors.append(f"top-level script entrypoints: expected {expected_count}, observed {len(script_files)}")

    metrics = {
        "canonical_capability_count": len(commands),
        "duplicate_canonical_owner_count": len(duplicate_capabilities),
        "missing_implementation_count": len(missing_implementations),
        "write_command_count": len(contract.get("write_commands") or []),
        "write_command_missing_mode_count": len(missing_mode_flags),
        "active_write_invocation_missing_mode_count": len(implicit_mode_callers),
        "deprecated_thin_alias_count": len(contract.get("deprecated_thin_aliases") or []),
        "ci_missing_canonical_invocation_count": len(missing_ci),
        "ci_direct_legacy_invocation_count": len(direct_legacy),
        "dead_script_remaining_count": sum(
            1 for row in contract.get("dead_scripts") or [] if (database_dir / str(row["path"])).exists()
        ),
        "deleted_active_reference_count": len(active_dead_refs),
        "top_level_script_entrypoint_count": len(script_files),
    }
    return {
        "status": "PASS" if not errors else "FAIL",
        "task_id": contract.get("task_id"),
        "acceptance_id": contract.get("acceptance_id"),
        "metrics": metrics,
        "errors": errors,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database-dir", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    database_dir = args.database_dir.expanduser().resolve()
    contract_path = args.contract if args.contract.is_absolute() else database_dir / args.contract
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    result = validate(contract, database_dir, database_dir.parent)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
