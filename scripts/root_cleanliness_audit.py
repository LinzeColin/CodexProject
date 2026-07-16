#!/usr/bin/env python3
"""Fail-closed audit for stable root entries, ownership, links, and context budgets."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Iterable
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = ROOT / "governance" / "root_cleanliness_budget.json"
DEFAULT_REGISTRY = ROOT / "governance" / "projects.yaml"
MARKDOWN_LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
README_PROJECT_ROW_RE = re.compile(
    r"^\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|",
    re.MULTILINE,
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )


def load_policy(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"policy must be a JSON object: {path}")
    return payload


def _load_validator_module(root: Path) -> ModuleType:
    path = root / "scripts" / "validate_project_governance.py"
    module_name = "_root_cleanliness_governance_loader"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import YAML loader: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def load_registry(path: Path, *, root: Path) -> dict[str, Any]:
    payload = _load_validator_module(root).load_yaml(path)
    if not isinstance(payload, dict):
        raise ValueError(f"registry must be a mapping: {path}")
    return payload


def as_dict_list(value: Any) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def validate_policy(policy: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if policy.get("schema_version") != 1:
        errors.append("policy.schema_version must equal 1")
    for field in ("policy_id", "owner", "task_id", "acceptance_id"):
        if not isinstance(policy.get(field), str) or not str(policy[field]).strip():
            errors.append(f"policy.{field} must be non-empty")

    budgets = policy.get("budgets")
    if not isinstance(budgets, dict):
        errors.append("policy.budgets must be an object")
        budgets = {}
    limits = {
        "agents_max_bytes": 4096,
        "readme_max_bytes": 8192,
        "initial_context_max_bytes": 12288,
        "initial_context_max_files": 5,
    }
    for field, maximum in limits.items():
        value = budgets.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or value < 1 or value > maximum:
            errors.append(f"policy.budgets.{field} must be 1..{maximum}")

    for field in (
        "entry_files",
        "active_project_entrypoints",
        "allowed_active_scope_exclusions",
        "agents_required_tokens",
        "readme_forbidden_patterns",
    ):
        value = policy.get(field)
        if not isinstance(value, list) or (field != "allowed_active_scope_exclusions" and not value):
            errors.append(f"policy.{field} must be a non-empty array")
            continue
        if any(not isinstance(item, str) or not item.strip() for item in value):
            errors.append(f"policy.{field} entries must be non-empty strings")
        if len(value) != len(set(value)):
            errors.append(f"policy.{field} entries must be unique")

    root_items = policy.get("owned_root_items")
    if not isinstance(root_items, list) or not root_items:
        errors.append("policy.owned_root_items must be a non-empty array")
        root_items = []
    seen_paths: set[str] = set()
    for index, item in enumerate(root_items):
        if not isinstance(item, dict):
            errors.append(f"policy.owned_root_items[{index}] must be an object")
            continue
        path = str(item.get("path") or "")
        if not path or "/" in path or path in {".", ".."}:
            errors.append(f"policy.owned_root_items[{index}].path must be one root component")
        if path in seen_paths:
            errors.append(f"duplicate owned root item: {path}")
        seen_paths.add(path)
        if item.get("kind") not in {"file", "directory"}:
            errors.append(f"policy.owned_root_items[{index}].kind invalid")
        for field in ("owner", "purpose"):
            if not isinstance(item.get(field), str) or not str(item[field]).strip():
                errors.append(f"policy.owned_root_items[{index}].{field} must be non-empty")

    for index, pattern in enumerate(policy.get("readme_forbidden_patterns") or []):
        try:
            re.compile(str(pattern))
        except re.error as exc:
            errors.append(f"policy.readme_forbidden_patterns[{index}] invalid: {exc}")
    return errors


def candidate_paths(root: Path) -> list[str]:
    result = _git(root, "ls-files", "--cached", "--others", "--exclude-standard", "-z")
    if result.returncode != 0:
        raise RuntimeError(f"git ls-files failed: {result.stderr.strip()}")
    return sorted({item for item in result.stdout.split("\0") if item})


def root_inventory(paths: Iterable[str]) -> dict[str, str]:
    inventory: dict[str, str] = {}
    for raw_path in paths:
        normalized = raw_path.replace("\\", "/").strip("/")
        if not normalized:
            continue
        first, separator, _ = normalized.partition("/")
        kind = "directory" if separator else "file"
        previous = inventory.get(first)
        if previous is not None and previous != kind:
            raise ValueError(f"root item has conflicting kinds: {first}")
        inventory[first] = kind
    return dict(sorted(inventory.items()))


def registry_findings(
    root: Path,
    registry: dict[str, Any],
    policy: dict[str, Any],
    actual_inventory: dict[str, str],
) -> tuple[list[str], dict[str, Any], set[str]]:
    errors: list[str] = []
    groups = {
        "active": as_dict_list(registry.get("projects")),
        "retired": as_dict_list(registry.get("retired_projects")),
        "migrated": as_dict_list(registry.get("migrated_projects")),
    }
    seen_ids: dict[str, str] = {}
    seen_paths: dict[str, str] = {}
    for group_name, entries in groups.items():
        for index, entry in enumerate(entries):
            project_id = str(entry.get("project_id") or "")
            path = str(entry.get("path") or "")
            label = f"{group_name}[{index}]"
            if not project_id or not path:
                errors.append(f"registry {label} missing project_id/path")
                continue
            if "/" in path or path in {".", ".."}:
                errors.append(f"registry {label} path must be one root component: {path}")
            if project_id in seen_ids:
                errors.append(f"duplicate registry project_id: {project_id} ({seen_ids[project_id]}, {group_name})")
            seen_ids[project_id] = group_name
            if path in seen_paths:
                errors.append(f"duplicate registry path: {path} ({seen_paths[path]}, {group_name})")
            seen_paths[path] = group_name

    entrypoints = [str(item) for item in policy.get("active_project_entrypoints") or []]
    for entry in groups["active"]:
        path = str(entry.get("path") or "")
        if actual_inventory.get(path) != "directory":
            errors.append(f"active project path missing from candidate tree: {path}")
        for filename in entrypoints:
            target = root / path / filename
            if not target.is_file():
                errors.append(f"active project entrypoint missing: {path}/{filename}")

    for entry in groups["retired"]:
        path = str(entry.get("path") or "")
        if actual_inventory.get(path) != "directory":
            errors.append(f"retired project history path missing: {path}")
    for entry in groups["migrated"]:
        path = str(entry.get("path") or "")
        if path in actual_inventory:
            errors.append(f"migrated project path unexpectedly present: {path}")

    root_governance = registry.get("root_governance")
    root_governance = root_governance if isinstance(root_governance, dict) else {}
    exclusions = {str(item) for item in root_governance.get("changed_scope_excluded_projects") or []}
    allowed = {str(item) for item in policy.get("allowed_active_scope_exclusions") or []}
    unexpected_exclusions = sorted(exclusions - allowed)
    if unexpected_exclusions:
        errors.append(f"unapproved active-scope exclusions: {unexpected_exclusions}")

    dynamic_owned = {
        str(entry.get("path") or "")
        for group_name in ("active", "retired")
        for entry in groups[group_name]
        if str(entry.get("path") or "")
    }
    metrics = {
        "active_project_count": len(groups["active"]),
        "retired_project_count": len(groups["retired"]),
        "migrated_project_count": len(groups["migrated"]),
        "unexpected_active_scope_exclusions": unexpected_exclusions,
    }
    return errors, metrics, dynamic_owned


def readme_project_findings(readme_text: str, registry: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
    expected = {
        (str(item.get("project_id") or ""), str(item.get("path") or ""))
        for item in as_dict_list(registry.get("projects"))
    }
    found = {
        (match.group(1), match.group(2))
        for match in README_PROJECT_ROW_RE.finditer(readme_text)
        if match.group(1) != "Project"
    }
    missing = sorted(expected - found)
    extra = sorted(found - expected)
    errors = [f"README active project table drift: missing={missing}; extra={extra}"] if missing or extra else []
    return errors, {"expected_rows": len(expected), "found_rows": len(found), "missing": missing, "extra": extra}


def local_markdown_link_findings(root: Path, entry_files: Iterable[str]) -> list[str]:
    errors: list[str] = []
    for relative in entry_files:
        source = root / relative
        if not source.is_file():
            errors.append(f"entry file missing: {relative}")
            continue
        text = source.read_text(encoding="utf-8")
        for raw_target in MARKDOWN_LINK_RE.findall(text):
            target = raw_target.strip().strip("<>").split(maxsplit=1)[0]
            parsed = urlsplit(target)
            if parsed.scheme or target.startswith("#"):
                continue
            decoded_path = unquote(parsed.path)
            if not decoded_path:
                continue
            resolved = (source.parent / decoded_path).resolve()
            try:
                resolved.relative_to(root.resolve())
            except ValueError:
                errors.append(f"entry link escapes repository: {relative} -> {target}")
                continue
            if not resolved.exists():
                errors.append(f"broken local entry link: {relative} -> {target}")
    return sorted(set(errors))


def temporary_state_findings(text: str, patterns: Iterable[str]) -> list[str]:
    return [str(pattern) for pattern in patterns if re.search(str(pattern), text)]


def audit_root(
    *,
    root: Path,
    policy: dict[str, Any],
    registry: dict[str, Any],
    paths: list[str] | None = None,
    policy_path: Path | None = None,
    registry_path: Path | None = None,
) -> dict[str, Any]:
    errors = validate_policy(policy)
    paths = candidate_paths(root) if paths is None else sorted(set(paths))
    inventory = root_inventory(paths)
    registry_errors, registry_metrics, dynamic_owned = registry_findings(root, registry, policy, inventory)
    errors.extend(registry_errors)

    declared_items = {
        str(item.get("path") or ""): str(item.get("kind") or "")
        for item in policy.get("owned_root_items") or []
        if isinstance(item, dict)
    }
    declared_missing = sorted(
        path for path, kind in declared_items.items() if inventory.get(path) != kind
    )
    unowned = sorted(set(inventory) - set(declared_items) - dynamic_owned)
    if declared_missing:
        errors.append(f"declared root items missing or wrong kind: {declared_missing}")
    if unowned:
        errors.append(f"unowned root items: {unowned}")

    entry_files = [str(item) for item in policy.get("entry_files") or []]
    sizes: dict[str, int] = {}
    for relative in entry_files:
        path = root / relative
        if path.is_file():
            sizes[relative] = len(path.read_bytes())
        else:
            errors.append(f"budget entry file missing: {relative}")
    budgets = policy.get("budgets") if isinstance(policy.get("budgets"), dict) else {}
    agents_bytes = sizes.get("AGENTS.md", 0)
    readme_bytes = sizes.get("README.md", 0)
    context_bytes = sum(sizes.values())
    if agents_bytes > int(budgets.get("agents_max_bytes") or 0):
        errors.append(f"AGENTS.md exceeds byte budget: {agents_bytes}")
    if readme_bytes > int(budgets.get("readme_max_bytes") or 0):
        errors.append(f"README.md exceeds byte budget: {readme_bytes}")
    if context_bytes > int(budgets.get("initial_context_max_bytes") or 0):
        errors.append(f"initial root context exceeds byte budget: {context_bytes}")
    if len(entry_files) > int(budgets.get("initial_context_max_files") or 0):
        errors.append(f"initial root context exceeds file-count budget: {len(entry_files)}")

    agents_text = (root / "AGENTS.md").read_text(encoding="utf-8") if (root / "AGENTS.md").is_file() else ""
    missing_tokens = [
        str(token)
        for token in policy.get("agents_required_tokens") or []
        if str(token) not in agents_text
    ]
    if missing_tokens:
        errors.append(f"AGENTS.md missing required tokens: {missing_tokens}")

    readme_text = (root / "README.md").read_text(encoding="utf-8") if (root / "README.md").is_file() else ""
    temporary_patterns = temporary_state_findings(readme_text, policy.get("readme_forbidden_patterns") or [])
    if temporary_patterns:
        errors.append(f"README.md contains temporary-state patterns: {temporary_patterns}")
    readme_errors, readme_metrics = readme_project_findings(readme_text, registry)
    errors.extend(readme_errors)
    link_errors = local_markdown_link_findings(root, entry_files)
    errors.extend(link_errors)

    head = _git(root, "rev-parse", "HEAD")
    result = {
        "schema_version": "codexproject.root_cleanliness.audit.v1",
        "policy_id": policy.get("policy_id"),
        "head_commit": head.stdout.strip() if head.returncode == 0 else "UNKNOWN",
        "policy_sha256": sha256_file(policy_path) if policy_path and policy_path.is_file() else "IN_MEMORY",
        "registry_sha256": sha256_file(registry_path) if registry_path and registry_path.is_file() else "IN_MEMORY",
        "budgets": {
            "agents_bytes": agents_bytes,
            "agents_max_bytes": budgets.get("agents_max_bytes"),
            "readme_bytes": readme_bytes,
            "readme_max_bytes": budgets.get("readme_max_bytes"),
            "initial_context_bytes": context_bytes,
            "initial_context_max_bytes": budgets.get("initial_context_max_bytes"),
            "initial_context_files": len(entry_files),
            "initial_context_max_files": budgets.get("initial_context_max_files"),
        },
        "root_inventory": {
            "item_count": len(inventory),
            "owned_item_count": len(inventory) - len(unowned),
            "unowned_item_count": len(unowned),
            "unowned_items": unowned,
            "declared_missing_items": declared_missing,
        },
        "registry": registry_metrics,
        "readme_projects": readme_metrics,
        "broken_local_link_count": len(link_errors),
        "missing_agents_token_count": len(missing_tokens),
        "temporary_readme_pattern_count": len(temporary_patterns),
        "errors": sorted(set(errors)),
    }
    result["pass"] = not result["errors"]
    return result


def resolve_under_root(root: Path, value: str, default: Path) -> Path:
    path = Path(value) if value else default
    return path if path.is_absolute() else root / path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--policy", default="governance/root_cleanliness_budget.json")
    parser.add_argument("--registry", default="governance/projects.yaml")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = Path(args.root).expanduser().resolve()
    policy_path = resolve_under_root(root, args.policy, DEFAULT_POLICY)
    registry_path = resolve_under_root(root, args.registry, DEFAULT_REGISTRY)
    try:
        policy = load_policy(policy_path)
        registry = load_registry(registry_path, root=root)
        result = audit_root(
            root=root,
            policy=policy,
            registry=registry,
            policy_path=policy_path,
            registry_path=registry_path,
        )
    except Exception as exc:  # fail closed at the CLI boundary
        result = {
            "schema_version": "codexproject.root_cleanliness.audit.v1",
            "pass": False,
            "errors": [f"audit_exception:{type(exc).__name__}:{exc}"],
        }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        state = "PASS" if result.get("pass") else "FAIL"
        inventory = result.get("root_inventory") if isinstance(result.get("root_inventory"), dict) else {}
        print(
            f"{state} root_items={inventory.get('item_count', 'UNKNOWN')} "
            f"unowned={inventory.get('unowned_item_count', 'UNKNOWN')} "
            f"broken_links={result.get('broken_local_link_count', 'UNKNOWN')}"
        )
        for error in result.get("errors") or []:
            print(f"- {error}", file=sys.stderr)
    return 0 if result.get("pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
