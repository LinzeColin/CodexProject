#!/usr/bin/env python3
"""Validate and run the canonical deterministic OpenAIDatabase test tiers."""

from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
import re
import subprocess
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


DATABASE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = DATABASE_DIR.parent
DEFAULT_POLICY = DATABASE_DIR / "config/quality/verification_policy.json"
EXECUTABLE_TIERS = ("fast", "unit", "security", "integration")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _test_function_digest(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    normalized = copy.deepcopy(node)
    normalized.name = "test_case"
    return hashlib.sha256(
        ast.dump(normalized, annotate_fields=True, include_attributes=False).encode("utf-8")
    ).hexdigest()


def _relative_files(root: Path, pattern: str) -> list[str]:
    return sorted(path.relative_to(root).as_posix() for path in root.glob(pattern) if path.is_file())


def validate_policy(database_dir: Path = DATABASE_DIR, policy_path: Path = DEFAULT_POLICY) -> dict[str, Any]:
    repo_root = database_dir.parent
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    metrics: dict[str, int] = {}

    tiers = policy.get("execution_tiers") or {}
    if list((tiers.get("full") or {}).get("includes") or []) != list(EXECUTABLE_TIERS):
        errors.append("full tier must aggregate fast, unit, security and integration exactly once")

    catalog: list[str] = []
    owner_errors: list[str] = []
    for tier in EXECUTABLE_TIERS:
        row = tiers.get(tier) or {}
        if not str(row.get("owner") or "").strip():
            owner_errors.append(tier)
        catalog.extend(str(value) for value in row.get("test_files") or [])
    duplicates = sorted(name for name, count in Counter(catalog).items() if count > 1)
    actual_tests = _relative_files(database_dir, "tests/test_*.py")
    missing_catalog = sorted(set(actual_tests) - set(catalog))
    stale_catalog = sorted(set(catalog) - set(actual_tests))
    if owner_errors:
        errors.append(f"tiers missing capability owner: {owner_errors}")
    if duplicates:
        errors.append(f"tests with multiple capability owners: {duplicates}")
    if missing_catalog:
        errors.append(f"tests without capability owner: {missing_catalog}")
    if stale_catalog:
        errors.append(f"catalog references missing tests: {stale_catalog}")

    semantic_hashes: dict[str, list[str]] = defaultdict(list)
    parse_errors: list[str] = []
    test_sources: dict[str, str] = {}
    for relative in actual_tests:
        source = (database_dir / relative).read_text(encoding="utf-8")
        test_sources[relative] = source
        try:
            tree = ast.parse(source)
        except SyntaxError as exc:
            parse_errors.append(f"{relative}:{exc.lineno}:{exc.msg}")
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test"):
                semantic_hashes[_test_function_digest(node)].append(f"{relative}:{node.name}")
    duplicate_test_groups = sorted(values for values in semantic_hashes.values() if len(values) > 1)
    if parse_errors:
        errors.append(f"test parse failures: {parse_errors}")
    if duplicate_test_groups:
        errors.append(f"duplicate test implementations: {duplicate_test_groups}")

    rules = policy.get("test_rules") or {}
    skip_hits: list[str] = []
    flaky_hits: list[str] = []
    for relative, source in test_sources.items():
        for pattern in rules.get("forbidden_skip_patterns") or []:
            if re.search(str(pattern), source):
                skip_hits.append(f"{relative}:{pattern}")
        for pattern in rules.get("forbidden_flaky_patterns") or []:
            if re.search(str(pattern), source):
                flaky_hits.append(f"{relative}:{pattern}")
    if skip_hits:
        errors.append(f"conditional or disabled tests are forbidden: {skip_hits}")
    if flaky_hits:
        errors.append(f"known flaky/retry mechanisms are forbidden: {flaky_hits}")

    unit_live_hits: list[str] = []
    unit_files = (tiers.get("unit") or {}).get("test_files") or []
    for relative in unit_files:
        source = test_sources.get(str(relative), "")
        for pattern in rules.get("unit_forbidden_live_or_nondeterministic_patterns") or []:
            if re.search(str(pattern), source):
                unit_live_hits.append(f"{relative}:{pattern}")
    if unit_live_hits:
        errors.append(f"unit tier has implicit live or nondeterministic side effects: {unit_live_hits}")

    frontend = policy.get("frontend") or {}
    package_path = database_dir / str(frontend.get("package_json"))
    lock_path = database_dir / str(frontend.get("lockfile"))
    package = json.loads(package_path.read_text(encoding="utf-8"))
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    command_owners: dict[str, list[str]] = defaultdict(list)
    referenced_scripts: set[str] = set()
    missing_script_targets: list[str] = []
    for name, command in (package.get("scripts") or {}).items():
        command_owners[str(command)].append(str(name))
        for relative in re.findall(r"(?:^|\s)(scripts/[^\s;&|]+)", str(command)):
            referenced_scripts.add(relative)
            if not (package_path.parent / relative).is_file():
                missing_script_targets.append(f"{name}:{relative}")
    duplicate_npm_commands = sorted(values for values in command_owners.values() if len(values) > 1)
    compatibility_alias_drift = [
        name
        for name, expected in (frontend.get("compatibility_aliases") or {}).items()
        if (package.get("scripts") or {}).get(name) != expected
    ]
    script_dir = database_dir / str(frontend.get("script_directory"))
    actual_frontend_scripts = {
        path.relative_to(package_path.parent).as_posix() for path in script_dir.iterdir() if path.is_file()
    }
    unowned_frontend_scripts = sorted(actual_frontend_scripts - referenced_scripts)
    if duplicate_npm_commands:
        errors.append(f"duplicate npm script commands: {duplicate_npm_commands}")
    if compatibility_alias_drift:
        errors.append(f"frontend compatibility alias drift: {compatibility_alias_drift}")
    if missing_script_targets:
        errors.append(f"npm scripts reference missing files: {missing_script_targets}")
    if unowned_frontend_scripts:
        errors.append(f"frontend validator files without package owner: {unowned_frontend_scripts}")

    lock_root = (lock.get("packages") or {}).get("") or {}
    lock_mismatch = [
        field
        for field in ("dependencies", "devDependencies")
        if (package.get(field) or {}) != (lock_root.get(field) or {})
    ]
    if lock.get("lockfileVersion") != 3:
        errors.append(f"package-lock must use version 3, observed {lock.get('lockfileVersion')}")
    if lock_mismatch:
        errors.append(f"package and lock root dependency drift: {lock_mismatch}")

    config_hashes: dict[str, list[str]] = defaultdict(list)
    for path in sorted((database_dir / "config").rglob("*")):
        if path.is_file() and path.suffix.lower() in {".json", ".yaml", ".yml", ".toml"}:
            config_hashes[_sha256(path)].append(path.relative_to(database_dir).as_posix())
    duplicate_config_groups = sorted(values for values in config_hashes.values() if len(values) > 1)
    if duplicate_config_groups:
        errors.append(f"exact duplicate configs: {duplicate_config_groups}")

    nested_workflows = sorted(
        path.relative_to(database_dir).as_posix()
        for path in database_dir.rglob("*")
        if path.is_file()
        and path.suffix.lower() in {".yml", ".yaml"}
        and ".github" in path.parts
        and "workflows" in path.parts
    )
    if nested_workflows:
        errors.append(f"nested workflows are forbidden: {nested_workflows}")

    ci = policy.get("ci") or {}
    workflow_path = repo_root / str(ci.get("workflow"))
    workflow = workflow_path.read_text(encoding="utf-8")
    missing_ci_tiers = [
        tier
        for tier in ci.get("required_tiers") or []
        if f"python3 scripts/run_verification.py --tier {tier}" not in workflow
    ]
    missing_ci_commands = [
        command
        for command in (frontend.get("required_install_command"), frontend.get("required_build_command"))
        if str(command) not in workflow
    ]
    forbidden_ci = [fragment for fragment in ci.get("forbidden_fragments") or [] if str(fragment) in workflow]
    reproducible_build_missing = int(str(ci.get("required_reproducible_build_fragment")) not in workflow)
    required_ci_order = [str(fragment) for fragment in ci.get("required_step_order") or []]
    ci_step_order_drift = [
        f"{before} must precede {after}"
        for before, after in zip(required_ci_order, required_ci_order[1:])
        if workflow.find(before) < 0
        or workflow.find(after) < 0
        or workflow.find(before) >= workflow.find(after)
    ]
    aggregate = ci.get("aggregate_audit") or {}
    aggregate_command_count = workflow.count(str(aggregate.get("command") or ""))
    duplicate_audit_commands = [
        command for command in aggregate.get("forbidden_duplicate_commands") or [] if str(command) in workflow
    ]
    aggregate_call_drift: list[str] = []
    for script_key, calls_key in (
        ("root_script", "root_required_calls"),
        ("acceptance_script", "acceptance_required_calls"),
    ):
        source = (database_dir / str(aggregate.get(script_key))).read_text(encoding="utf-8")
        aggregate_call_drift.extend(
            f"{aggregate.get(script_key)}:{call}"
            for call in aggregate.get(calls_key) or []
            if str(call) not in source
        )
    unpinned_actions = []
    for action in re.findall(r"^\s*-?\s*uses:\s*([^\s#]+)", workflow, re.M):
        if not action.startswith("./") and not re.search(r"@[0-9a-f]{40}$", action):
            unpinned_actions.append(action)
    if missing_ci_tiers:
        errors.append(f"root CI missing verification tiers: {missing_ci_tiers}")
    if missing_ci_commands:
        errors.append(f"root CI missing reproducible frontend commands: {missing_ci_commands}")
    if forbidden_ci:
        errors.append(f"root CI weakens gates: {forbidden_ci}")
    if reproducible_build_missing:
        errors.append("root CI does not bind data generation to the commit SOURCE_DATE_EPOCH")
    if ci_step_order_drift:
        errors.append(f"root CI clean-build/test order drift: {ci_step_order_drift}")
    if aggregate_command_count != 1:
        errors.append(f"root CI aggregate audit count must be 1, observed {aggregate_command_count}")
    if duplicate_audit_commands:
        errors.append(f"root CI repeats audits already owned by goal-completion: {duplicate_audit_commands}")
    if aggregate_call_drift:
        errors.append(f"aggregate audit delegation drift: {aggregate_call_drift}")
    if unpinned_actions:
        errors.append(f"root CI actions are not immutable: {unpinned_actions}")

    metrics.update(
        {
            "test_file_count": len(actual_tests),
            "test_capability_owner_count": len(catalog),
            "unowned_test_count": len(missing_catalog),
            "multi_owned_test_count": len(duplicates),
            "duplicate_test_group_count": len(duplicate_test_groups),
            "conditional_skip_count": len(skip_hits),
            "known_flaky_count": len(flaky_hits),
            "unit_live_side_effect_count": len(unit_live_hits),
            "npm_script_count": len(package.get("scripts") or {}),
            "duplicate_npm_command_count": len(duplicate_npm_commands),
            "compatibility_alias_drift_count": len(compatibility_alias_drift),
            "frontend_script_file_count": len(actual_frontend_scripts),
            "unowned_frontend_script_count": len(unowned_frontend_scripts),
            "missing_frontend_script_count": len(missing_script_targets),
            "lock_dependency_drift_count": len(lock_mismatch),
            "duplicate_config_group_count": len(duplicate_config_groups),
            "nested_workflow_count": len(nested_workflows),
            "missing_ci_tier_count": len(missing_ci_tiers),
            "missing_ci_command_count": len(missing_ci_commands),
            "forbidden_ci_fragment_count": len(forbidden_ci),
            "reproducible_build_missing_count": reproducible_build_missing,
            "ci_step_order_drift_count": len(ci_step_order_drift),
            "aggregate_audit_count": aggregate_command_count,
            "duplicate_ci_audit_count": len(duplicate_audit_commands),
            "aggregate_audit_delegation_drift_count": len(aggregate_call_drift),
            "unpinned_ci_action_count": len(unpinned_actions),
        }
    )
    return {
        "status": "PASS" if not errors else "FAIL",
        "task_id": policy.get("task_id"),
        "acceptance_id": policy.get("acceptance_id"),
        "metrics": metrics,
        "errors": errors,
    }


def run_test_tier(database_dir: Path, policy: dict[str, Any], tier: str) -> int:
    files = [str(database_dir / str(value)) for value in policy["execution_tiers"][tier]["test_files"]]
    result = subprocess.run(
        [sys.executable, "-m", "unittest", *files],
        cwd=database_dir.parent,
        check=False,
    )
    return result.returncode


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--tier", choices=(*EXECUTABLE_TIERS, "full"))
    group.add_argument("--list", action="store_true", help="Print the owned tier catalog without running tests.")
    parser.add_argument("--repeat", type=int, default=1, choices=(1, 2, 3))
    parser.add_argument("--database-dir", type=Path, default=DATABASE_DIR)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    database_dir = args.database_dir.expanduser().resolve()
    policy_path = args.policy if args.policy.is_absolute() else database_dir / args.policy
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    validation = validate_policy(database_dir, policy_path)
    print(json.dumps(validation, ensure_ascii=False, sort_keys=True))
    if validation["status"] != "PASS":
        return 1
    if args.list:
        catalog = {
            tier: {
                "owner": policy["execution_tiers"][tier]["owner"],
                "test_count": len(policy["execution_tiers"][tier]["test_files"]),
            }
            for tier in EXECUTABLE_TIERS
        }
        print(json.dumps({"status": "PASS", "tiers": catalog}, ensure_ascii=False, sort_keys=True))
        return 0

    selected = list(EXECUTABLE_TIERS) if args.tier == "full" else [args.tier]
    started = time.monotonic()
    for iteration in range(1, args.repeat + 1):
        for tier in selected:
            print(f"verification tier={tier} iteration={iteration}/{args.repeat}", flush=True)
            if run_test_tier(database_dir, policy, tier) != 0:
                return 1
    print(
        json.dumps(
            {
                "status": "PASS",
                "tier": args.tier,
                "repeat": args.repeat,
                "elapsed_seconds": round(time.monotonic() - started, 3),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
