#!/usr/bin/env python3
"""Fail-closed audit for tracked large objects, archives, runtime noise, and backup producers."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path, PurePosixPath
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = ROOT / "governance" / "repository_hygiene_policy.json"
RULE_REQUIRED_TEXT = (
    "id",
    "owner",
    "purpose",
    "consumer",
    "retention",
    "recovery",
    "confidentiality",
    "change_policy",
)


def _git(root: Path, *args: str, binary: bool = False) -> subprocess.CompletedProcess[Any]:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        check=False,
        capture_output=True,
        text=not binary,
    )


def load_policy(path: Path = DEFAULT_POLICY) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"policy must be a JSON object: {path}")
    return payload


def validate_policy(policy: dict[str, Any], *, root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    if policy.get("schema_version") != 1:
        errors.append("schema_version must equal 1")
    for field in ("policy_id", "owner", "baseline_tree"):
        if not isinstance(policy.get(field), str) or not str(policy[field]).strip():
            errors.append(f"{field} must be non-empty")
    baseline = str(policy.get("baseline_tree") or "")
    if not re.fullmatch(r"[0-9a-f]{40}", baseline):
        errors.append("baseline_tree must be a 40-character Git tree OID")
    elif _git(root, "cat-file", "-e", f"{baseline}^{{tree}}").returncode != 0:
        errors.append(f"baseline_tree is not available: {baseline}")

    maximum = policy.get("regular_blob_max_bytes")
    if not isinstance(maximum, int) or maximum <= 0 or maximum > 1_048_576:
        errors.append("regular_blob_max_bytes must be between 1 and 1048576")

    rules = policy.get("retained_objects")
    if not isinstance(rules, list):
        errors.append("retained_objects must be an array")
        rules = []
    seen_ids: set[str] = set()
    for index, rule in enumerate(rules):
        if not isinstance(rule, dict):
            errors.append(f"retained_objects[{index}] must be an object")
            continue
        rule_id = str(rule.get("id") or "")
        if rule_id in seen_ids:
            errors.append(f"duplicate retained object rule id: {rule_id}")
        seen_ids.add(rule_id)
        for field in RULE_REQUIRED_TEXT:
            if not isinstance(rule.get(field), str) or not str(rule[field]).strip():
                errors.append(f"retained_objects[{index}].{field} must be non-empty")
        selectors = [name for name in ("path", "prefix") if isinstance(rule.get(name), str) and rule[name]]
        if len(selectors) != 1:
            errors.append(f"retained_objects[{index}] requires exactly one path or prefix")
        if "prefix" in selectors and not str(rule["prefix"]).endswith("/"):
            errors.append(f"retained_objects[{index}].prefix must end with /")
        kinds = rule.get("kinds")
        if not isinstance(kinds, list) or not kinds or not set(kinds) <= {"large", "archive"}:
            errors.append(f"retained_objects[{index}].kinds must contain large and/or archive")
        if rule.get("change_policy") != "baseline_oid_only":
            errors.append(f"retained_objects[{index}].change_policy must be baseline_oid_only")
        reviewed_oids = rule.get("reviewed_oids", [])
        if not isinstance(reviewed_oids, list) or any(
            not isinstance(oid, str) or re.fullmatch(r"[0-9a-f]{40}", oid) is None
            for oid in reviewed_oids
        ):
            errors.append(
                f"retained_objects[{index}].reviewed_oids must contain only 40-character Git blob OIDs"
            )
        elif len(reviewed_oids) != len(set(reviewed_oids)):
            errors.append(f"retained_objects[{index}].reviewed_oids must be unique")
        if not isinstance(rule.get("max_bytes"), int) or int(rule.get("max_bytes") or 0) <= 0:
            errors.append(f"retained_objects[{index}].max_bytes must be positive")

    hard_fail = policy.get("hard_fail")
    if not isinstance(hard_fail, dict):
        errors.append("hard_fail must be an object")
    else:
        for field in (
            "forbidden_names",
            "forbidden_directory_names",
            "forbidden_suffixes",
            "archive_suffixes",
        ):
            if not isinstance(hard_fail.get(field), list):
                errors.append(f"hard_fail.{field} must be an array")

    source_scan = policy.get("source_scan")
    if not isinstance(source_scan, dict):
        errors.append("source_scan must be an object")
    else:
        for field in ("extensions", "excluded_paths", "excluded_segments", "forbidden_regexes"):
            if not isinstance(source_scan.get(field), list):
                errors.append(f"source_scan.{field} must be an array")
        for expression in source_scan.get("forbidden_regexes") or []:
            try:
                re.compile(str(expression), re.IGNORECASE | re.MULTILINE)
            except re.error as exc:
                errors.append(f"invalid source_scan regex {expression!r}: {exc}")

    history = policy.get("history_rewrite")
    if not isinstance(history, dict):
        errors.append("history_rewrite must be an object")
    else:
        allowed = history.get("allowed_in_this_task")
        if allowed not in {True, False}:
            errors.append("history_rewrite.allowed_in_this_task must be boolean")
        expected_decision = "OWNER_AUTHORIZED_SECURITY_REMEDIATION" if allowed else "DEFERRED"
        if history.get("decision") != expected_decision:
            errors.append(f"history_rewrite.decision must be {expected_decision}")
        if allowed:
            for field in ("task_id", "acceptance_id", "authorized_at"):
                if not isinstance(history.get(field), str) or not str(history[field]).strip():
                    errors.append(f"history_rewrite.{field} must be non-empty")
            if not isinstance(history.get("target_paths"), list) or not history.get("target_paths"):
                errors.append("history_rewrite.target_paths must be a non-empty array")
        if not isinstance(history.get("future_preconditions"), list) or not history.get("future_preconditions"):
            errors.append("history_rewrite.future_preconditions must be a non-empty array")
    return errors


def tree_inventory(root: Path, treeish: str) -> dict[str, dict[str, Any]]:
    result = _git(root, "ls-tree", "-rlz", treeish, binary=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.decode("utf-8", errors="replace").strip())
    inventory: dict[str, dict[str, Any]] = {}
    for row in result.stdout.split(b"\0"):
        if not row:
            continue
        metadata, raw_path = row.split(b"\t", 1)
        _mode, kind, oid, raw_size = metadata.split(b" ", 3)
        if kind != b"blob" or raw_size == b"-":
            continue
        path = raw_path.decode("utf-8", errors="surrogateescape")
        inventory[path] = {"oid": oid.decode("ascii"), "size": int(raw_size), "source": "tree"}
    return inventory


def worktree_inventory(root: Path) -> dict[str, dict[str, Any]]:
    result = _git(root, "ls-files", "--cached", "--others", "--exclude-standard", "-z", binary=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.decode("utf-8", errors="replace").strip())
    inventory: dict[str, dict[str, Any]] = {}
    for raw_path in result.stdout.split(b"\0"):
        if not raw_path:
            continue
        path = raw_path.decode("utf-8", errors="surrogateescape")
        absolute = root / path
        if not absolute.exists() or not (absolute.is_file() or absolute.is_symlink()):
            continue
        inventory[path] = {"oid": None, "size": absolute.lstat().st_size, "source": "worktree"}
    return inventory


def _blob_oid(root: Path, path: str, record: dict[str, Any]) -> str:
    if record.get("oid"):
        return str(record["oid"])
    result = _git(root, "hash-object", "--no-filters", "--", path)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    record["oid"] = result.stdout.strip()
    return str(record["oid"])


def _matches(rule: dict[str, Any], path: str) -> bool:
    if rule.get("path"):
        return path == rule["path"]
    return path.startswith(str(rule.get("prefix") or ""))


def _archive(path: str, suffixes: list[str]) -> bool:
    lowered = path.casefold()
    return any(lowered.endswith(str(suffix).casefold()) for suffix in suffixes)


def _runtime_noise(path: str, hard_fail: dict[str, Any]) -> str | None:
    pure = PurePosixPath(path)
    if pure.name in set(hard_fail.get("forbidden_names") or []):
        return f"forbidden tracked name: {pure.name}"
    forbidden_directories = set(hard_fail.get("forbidden_directory_names") or [])
    directory_hit = next((part for part in pure.parts[:-1] if part in forbidden_directories), None)
    if directory_hit:
        return f"forbidden tracked runtime directory: {directory_hit}"
    lowered = path.casefold()
    suffix_hit = next(
        (suffix for suffix in hard_fail.get("forbidden_suffixes") or [] if lowered.endswith(str(suffix).casefold())),
        None,
    )
    return f"forbidden tracked runtime suffix: {suffix_hit}" if suffix_hit else None


def _source_excluded(path: str, scan: dict[str, Any]) -> bool:
    if path in set(scan.get("excluded_paths") or []):
        return True
    excluded_segments = set(scan.get("excluded_segments") or [])
    return any(part in excluded_segments for part in PurePosixPath(path).parts)


def _pack_bytes(root: Path) -> int | None:
    result = _git(root, "count-objects", "-v")
    if result.returncode != 0:
        return None
    values = {}
    for line in result.stdout.splitlines():
        if ": " in line:
            key, value = line.split(": ", 1)
            values[key] = value
    try:
        return int(values["size-pack"]) * 1024
    except (KeyError, ValueError):
        return None


def audit_repository(
    *,
    root: Path = ROOT,
    policy: dict[str, Any] | None = None,
    treeish: str | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    active_policy = policy or load_policy(root / "governance" / "repository_hygiene_policy.json")
    policy_errors = validate_policy(active_policy, root=root)
    if policy_errors:
        return {
            "schema_version": 1,
            "status": "FAIL",
            "mode": treeish or "worktree",
            "policy_errors": policy_errors,
            "violations": [],
        }

    baseline = tree_inventory(root, active_policy["baseline_tree"])
    current = tree_inventory(root, treeish) if treeish else worktree_inventory(root)
    rules = active_policy["retained_objects"]
    hard_fail = active_policy["hard_fail"]
    maximum = active_policy["regular_blob_max_bytes"]
    archive_suffixes = hard_fail["archive_suffixes"]
    violations: list[dict[str, str]] = []
    retained_usage: dict[str, set[str]] = defaultdict(set)
    large_count = 0
    large_bytes = 0
    archive_count = 0

    def retain(kind: str, path: str, record: dict[str, Any]) -> None:
        matches = [rule for rule in rules if kind in rule["kinds"] and _matches(rule, path)]
        if len(matches) != 1:
            violations.append(
                {
                    "code": f"{kind}_retention_rule_count",
                    "path": path,
                    "detail": f"expected exactly one retained-object rule, found {len(matches)}",
                }
            )
            return
        rule = matches[0]
        retained_usage[rule["id"]].add(path)
        if record["size"] > rule["max_bytes"]:
            violations.append(
                {
                    "code": f"{kind}_max_bytes",
                    "path": path,
                    "detail": f"{record['size']} exceeds rule maximum {rule['max_bytes']}",
                }
            )
        baseline_record = baseline.get(path)
        current_oid = _blob_oid(root, path, record)
        reviewed_oids = set(rule.get("reviewed_oids", []))
        if (baseline_record is None or current_oid != baseline_record["oid"]) and current_oid not in reviewed_oids:
            violations.append(
                {
                    "code": f"{kind}_new_or_modified",
                    "path": path,
                    "detail": "retained objects require the baseline OID or an exact reviewed migration OID",
                }
            )

    for path, record in sorted(current.items()):
        noise = _runtime_noise(path, hard_fail)
        if noise:
            violations.append({"code": "tracked_runtime_noise", "path": path, "detail": noise})
        if record["size"] > maximum:
            large_count += 1
            large_bytes += record["size"]
            retain("large", path, record)
        if _archive(path, archive_suffixes):
            archive_count += 1
            retain("archive", path, record)

    scan = active_policy["source_scan"]
    extensions = set(scan["extensions"])
    regexes = [re.compile(expression, re.IGNORECASE | re.MULTILINE) for expression in scan["forbidden_regexes"]]
    producer_findings = 0
    for path in sorted(current):
        if Path(path).suffix.casefold() not in extensions or _source_excluded(path, scan):
            continue
        absolute = root / path
        if not absolute.is_file():
            continue
        text = absolute.read_text(encoding="utf-8", errors="ignore")
        for expression in regexes:
            if expression.search(text):
                producer_findings += 1
                violations.append(
                    {
                        "code": "forbidden_repository_backup_producer",
                        "path": path,
                        "detail": f"source matches forbidden producer regex: {expression.pattern}",
                    }
                )

    retained_summary = [
        {"rule_id": rule["id"], "object_count": len(retained_usage.get(rule["id"], set()))}
        for rule in rules
        if retained_usage.get(rule["id"])
    ]
    return {
        "schema_version": 1,
        "status": "PASS" if not violations else "FAIL",
        "policy_id": active_policy["policy_id"],
        "mode": treeish or "worktree",
        "baseline_tree": active_policy["baseline_tree"],
        "metrics": {
            "tracked_object_count": len(current),
            "regular_blob_max_bytes": maximum,
            "retained_large_object_count": large_count,
            "retained_large_object_bytes": large_bytes,
            "retained_archive_count": archive_count,
            "tracked_runtime_noise_count": sum(v["code"] == "tracked_runtime_noise" for v in violations),
            "forbidden_backup_producer_count": producer_findings,
            "git_pack_bytes_current": _pack_bytes(root),
        },
        "retained_rule_usage": retained_summary,
        "history_rewrite": {
            "allowed_in_this_task": bool(
                active_policy["history_rewrite"]["allowed_in_this_task"]
            ),
            "decision": active_policy["history_rewrite"]["decision"],
        },
        "policy_errors": [],
        "violations": violations,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--policy", type=Path)
    parser.add_argument("--tree-ish", help="Audit a committed/staged tree instead of the current worktree.")
    parser.add_argument("--output", type=Path, help="Write the compact JSON result to this local artifact path.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = args.root.expanduser().resolve()
    policy_path = args.policy or root / "governance" / "repository_hygiene_policy.json"
    try:
        policy = load_policy(policy_path)
        result = audit_repository(root=root, policy=policy, treeish=args.tree_ish)
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        result = {
            "schema_version": 1,
            "status": "FAIL",
            "policy_errors": [str(exc)],
            "violations": [],
        }
    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        output = args.output.expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    sys.stdout.write(rendered)
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
