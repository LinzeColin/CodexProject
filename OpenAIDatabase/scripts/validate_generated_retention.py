#!/usr/bin/env python3
"""Validate generated, retained, audit and local-transient storage policy."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any


DEFAULT_CONTRACT = Path("config/storage/generated_retention.json")
ACTIVE_SOURCE_SUFFIXES = {
    ".py", ".cjs", ".mjs", ".js", ".ts", ".tsx", ".json", ".toml", ".md",
}


def git_output(repo_root: Path, *args: str, text: bool = True) -> str | bytes:
    return subprocess.check_output(
        ["git", *args],
        cwd=repo_root,
        text=text,
        stderr=subprocess.DEVNULL,
    )


def tracked_project_paths(repo_root: Path, project_name: str) -> list[str]:
    raw = git_output(repo_root, "ls-files", "-z", project_name, text=False)
    assert isinstance(raw, bytes)
    prefix = f"{project_name}/"
    return sorted(
        item.decode("utf-8", "surrogateescape").removeprefix(prefix)
        for item in raw.split(b"\0")
        if item
    )


def matches_rule(path: str, rule: dict[str, Any]) -> bool:
    includes = [str(item) for item in rule.get("include") or []]
    excludes = [str(item) for item in rule.get("exclude") or []]
    return (
        any(fnmatch.fnmatchcase(path, pattern) for pattern in includes)
        and not any(fnmatch.fnmatchcase(path, pattern) for pattern in excludes)
    )


def is_target(path: str) -> bool:
    return path.startswith(
        ("data/derived/", "data/run_logs/", "session_history/", "token_usage/")
    ) or path in {
        "data/memory/AGENT_MEMORY.md",
        "data/memory/agent-memory.json",
    } or is_tracked_transient(path)


def is_tracked_transient(path: str) -> bool:
    lowered = path.lower()
    parts = set(Path(path).parts)
    name = Path(path).name.lower()
    return (
        lowered.startswith("apps/memory-atlas/dist/")
        or lowered.startswith("apps/memory-atlas/node_modules/")
        or "__pycache__" in parts
        or ".cache" in parts
        or name.endswith((".sqlite", ".sqlite3", ".sqlite-wal", ".sqlite-shm"))
        or name.endswith((".db", ".db-wal", ".db-shm"))
        or name.endswith((".log", ".tmp", ".tsbuildinfo"))
        or (
            lowered.startswith("data/run_logs/")
            and any(marker in name for marker in ("stdout", "stderr", "transcript"))
        )
    )


def base_fingerprint(
    repo_root: Path,
    project_name: str,
    base_sha: str,
    scope: str,
) -> dict[str, Any]:
    full_scope = f"{project_name}/{scope}"
    names_text = git_output(repo_root, "ls-tree", "-r", "--name-only", base_sha, "--", full_scope)
    assert isinstance(names_text, str)
    records: list[tuple[str, int, str]] = []
    for path in sorted(line for line in names_text.splitlines() if line):
        payload = git_output(repo_root, "show", f"{base_sha}:{path}", text=False)
        assert isinstance(payload, bytes)
        records.append((path, len(payload), hashlib.sha256(payload).hexdigest()))
    collection = "".join(
        f"{path}\0{size}\0{digest}\n" for path, size, digest in records
    ).encode("utf-8")
    return {
        "count": len(records),
        "bytes": sum(size for _, size, _ in records),
        "collection_sha256": hashlib.sha256(collection).hexdigest(),
    }


def iter_active_source_paths(database_dir: Path) -> list[Path]:
    roots = [
        database_dir / "AGENTS.md",
        database_dir / "README.md",
        database_dir / "apps",
        database_dir / "config",
        database_dir / "scripts",
        database_dir / "skills",
        database_dir / "tests",
    ]
    excluded = {
        database_dir / "config/storage/generated_retention.json",
        database_dir / "config/storage/directory_lifecycle.json",
    }
    paths: list[Path] = []
    for root in roots:
        if root.is_file():
            paths.append(root)
            continue
        for directory, dirnames, filenames in os.walk(root):
            dirnames[:] = sorted(
                name
                for name in dirnames
                if name not in {"node_modules", "dist", "__pycache__"}
            )
            paths.extend(
                Path(directory) / name
                for name in sorted(filenames)
                if (Path(directory) / name).suffix in ACTIVE_SOURCE_SUFFIXES
            )
    return [path for path in paths if path not in excluded]


def active_reference_paths(database_dir: Path, markers: list[str]) -> list[str]:
    hits: set[str] = set()
    for path in iter_active_source_paths(database_dir):
        source = path.read_text(encoding="utf-8", errors="ignore")
        if any(marker in source for marker in markers):
            hits.add(path.relative_to(database_dir).as_posix())
    return sorted(hits)


def validate(
    contract: dict[str, Any],
    database_dir: Path,
    repo_root: Path,
) -> dict[str, Any]:
    errors: list[str] = []
    project_name = database_dir.name
    tracked = tracked_project_paths(repo_root, project_name)
    tracked_set = set(tracked)
    target = [path for path in tracked if is_target(path)]
    rules = list(contract.get("retained_rules") or [])

    assignments: dict[str, list[str]] = {}
    for path in target:
        assignments[path] = [
            str(rule.get("rule_id"))
            for rule in rules
            if matches_rule(path, rule)
        ]
    unclassified = sorted(path for path, owners in assignments.items() if not owners)
    multiply_classified = sorted(path for path, owners in assignments.items() if len(owners) > 1)
    if unclassified:
        errors.append(f"unclassified target files: {unclassified}")
    if multiply_classified:
        errors.append(f"multiply classified target files: {multiply_classified}")

    transient = sorted(path for path in tracked if is_tracked_transient(path))
    if transient:
        errors.append(f"tracked transient files: {transient}")

    classification_counts: Counter[str] = Counter()
    rule_file_counts: dict[str, int] = {}
    missing_generator_bindings: list[str] = []
    missing_consumer_bindings: list[str] = []
    no_consumer_generated: list[str] = []
    for rule in rules:
        rule_id = str(rule.get("rule_id"))
        matched = [path for path, owners in assignments.items() if rule_id in owners]
        rule_file_counts[rule_id] = len(matched)
        classification_counts[str(rule.get("classification"))] += len(matched)
        if rule.get("generated"):
            generator_matches = [
                path
                for pattern in rule.get("generator_globs") or []
                for path in database_dir.glob(str(pattern))
                if path.is_file()
            ]
            if not generator_matches:
                missing_generator_bindings.append(rule_id)
            if not rule.get("consumer_bindings"):
                no_consumer_generated.append(rule_id)
        for binding in rule.get("consumer_bindings") or []:
            source_path = database_dir / str(binding.get("path"))
            marker = str(binding.get("marker") or "")
            if (
                not source_path.is_file()
                or not marker
                or marker not in source_path.read_text(encoding="utf-8", errors="ignore")
            ):
                missing_consumer_bindings.append(
                    f"{rule_id}:{binding.get('path')}:{marker}"
                )
    if missing_generator_bindings:
        errors.append(f"missing generator bindings: {missing_generator_bindings}")
    if missing_consumer_bindings:
        errors.append(f"missing consumer bindings: {missing_consumer_bindings}")
    if no_consumer_generated:
        errors.append(f"generated rules without consumers: {no_consumer_generated}")

    ignore_text = (database_dir / ".gitignore").read_text(encoding="utf-8")
    missing_ignore_markers: list[str] = []
    for rule in contract.get("local_transient_rules") or []:
        markers = list(rule.get("gitignore_markers") or [])
        if rule.get("gitignore_marker"):
            markers.append(str(rule["gitignore_marker"]))
        for marker in markers:
            if marker not in ignore_text:
                missing_ignore_markers.append(marker)
    if missing_ignore_markers:
        errors.append(f"missing .gitignore markers: {sorted(set(missing_ignore_markers))}")

    base_sha = str(contract.get("implementation_base_sha"))
    deletion_fingerprint_mismatches: list[str] = []
    deletion_remaining: list[str] = []
    active_deleted_refs: list[str] = []
    for deletion in contract.get("safe_deletions") or []:
        scope = str(deletion["scope"])
        observed = base_fingerprint(repo_root, project_name, base_sha, scope)
        expected = {
            "count": int(deletion["base_file_count"]),
            "bytes": int(deletion["base_bytes"]),
            "collection_sha256": str(deletion["base_collection_sha256"]),
        }
        if observed != expected:
            deletion_fingerprint_mismatches.append(scope)
        if any(
            path == scope or path.startswith(f"{scope}/")
            for path in tracked_set
        ):
            deletion_remaining.append(scope)
        markers = [str(item) for item in deletion.get("active_reference_markers") or []]
        if int(deletion.get("active_consumer_count_before", -1)) == 0 and markers:
            refs = active_reference_paths(database_dir, markers)
            active_deleted_refs.extend(f"{scope}:{path}" for path in refs)
    if deletion_fingerprint_mismatches:
        errors.append(f"safe-deletion base fingerprint mismatch: {deletion_fingerprint_mismatches}")
    if deletion_remaining:
        errors.append(f"safe-deletion paths remain tracked: {deletion_remaining}")
    if active_deleted_refs:
        errors.append(f"active references to zero-consumer deletions: {active_deleted_refs}")

    target_bytes = sum((database_dir / path).stat().st_size for path in target)
    retained_drift_count = (
        len(unclassified)
        + len(multiply_classified)
        + len(missing_generator_bindings)
        + len(missing_consumer_bindings)
        + len(deletion_fingerprint_mismatches)
    )
    metrics = {
        "target_tracked_file_count": len(target),
        "target_tracked_bytes": target_bytes,
        "tracked_transient_count": len(transient),
        "unclassified_target_count": len(unclassified),
        "multiply_classified_target_count": len(multiply_classified),
        "no_consumer_generated_count": len(no_consumer_generated),
        "missing_generator_binding_count": len(missing_generator_bindings),
        "missing_consumer_binding_count": len(missing_consumer_bindings),
        "missing_gitignore_marker_count": len(set(missing_ignore_markers)),
        "safe_deletion_fingerprint_mismatch_count": len(deletion_fingerprint_mismatches),
        "safe_deletion_remaining_count": len(deletion_remaining),
        "active_deleted_reference_count": len(active_deleted_refs),
        "retained_drift_count": retained_drift_count,
        "rule_file_counts": dict(sorted(rule_file_counts.items())),
        "classification_counts": dict(sorted(classification_counts.items())),
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
