#!/usr/bin/env python3
"""Fail-closed validation for OpenAIDatabase directory ownership and migration."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any


DEFAULT_CONTRACT = Path("config/storage/directory_lifecycle.json")


def git_output(repo_root: Path, args: list[str]) -> bytes:
    return subprocess.check_output(["git", *args], cwd=repo_root)


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def current_project_paths(repo_root: Path, project_id: str) -> list[str]:
    payload = git_output(
        repo_root,
        ["ls-files", "-z", "--cached", "--others", "--exclude-standard", "--", project_id],
    )
    return sorted(item.decode("utf-8") for item in payload.split(b"\0") if item)


def base_project_paths(repo_root: Path, project_id: str, base_ref: str) -> list[str]:
    payload = git_output(repo_root, ["ls-tree", "-rz", "--name-only", base_ref, "--", project_id])
    return sorted(item.decode("utf-8") for item in payload.split(b"\0") if item)


def path_directories(paths: list[str], project_id: str) -> set[str]:
    directories = {"."}
    prefix = f"{project_id}/"
    for path in paths:
        relative = path.removeprefix(prefix)
        parts = PurePosixPath(relative).parts[:-1]
        for index in range(1, len(parts) + 1):
            directories.add("/".join(parts[:index]))
    return directories


def base_file(repo_root: Path, base_ref: str, path: str) -> bytes:
    return git_output(repo_root, ["show", f"{base_ref}:{path}"])


def collection_fingerprint(entries: list[tuple[str, bytes]]) -> tuple[int, int, str]:
    digest = hashlib.sha256()
    total_bytes = 0
    for path, payload in sorted(entries):
        total_bytes += len(payload)
        digest.update(f"{path}\0{sha256(payload)}\0{len(payload)}\n".encode("utf-8"))
    return len(entries), total_bytes, digest.hexdigest()


def validate_contract(
    contract: dict[str, Any],
    database_dir: Path,
    repo_root: Path,
    base_ref: str,
) -> dict[str, Any]:
    errors: list[str] = []
    project_id = str(contract.get("project_id") or "")
    if project_id != database_dir.name:
        errors.append(f"project_id mismatch: {project_id!r} != {database_dir.name!r}")

    current_paths = current_project_paths(repo_root, project_id)
    base_paths = base_project_paths(repo_root, project_id, base_ref)
    current_set = set(current_paths)
    current_dirs = path_directories(current_paths, project_id)
    base_dirs = path_directories(base_paths, project_id)

    owner_rows = contract.get("ownership") or []
    owner_keys = [str(row.get("top_level")) for row in owner_rows if isinstance(row, dict)]
    owner_counts = Counter(owner_keys)
    duplicate_owner_keys = sorted(key for key, count in owner_counts.items() if count > 1)
    if duplicate_owner_keys:
        errors.append(f"duplicate ownership keys: {duplicate_owner_keys}")
    owner_set = set(owner_keys)
    unowned_dirs = sorted(
        directory
        for directory in current_dirs
        if ("." if directory == "." else directory.split("/", 1)[0]) not in owner_set
    )
    if unowned_dirs:
        errors.append(f"unowned directories: {unowned_dirs}")

    destinations = contract.get("destinations") or []
    destination_paths = [str(row.get("path")) for row in destinations if isinstance(row, dict)]
    destination_domains = [str(row.get("domain")) for row in destinations if isinstance(row, dict)]
    duplicate_destinations = sorted(
        path for path, count in Counter(destination_paths).items() if count > 1
    )
    duplicate_domains = sorted(
        domain for domain, count in Counter(destination_domains).items() if count > 1
    )
    if duplicate_destinations:
        errors.append(f"duplicate destinations: {duplicate_destinations}")
    if duplicate_domains:
        errors.append(f"duplicate destination domains: {duplicate_domains}")
    max_depth = int(contract.get("max_default_destination_depth") or 0)
    excessive_depth = sorted(
        path for path in destination_paths if len(PurePosixPath(path).parts) > max_depth
    )
    if excessive_depth:
        errors.append(f"destination depth exceeds {max_depth}: {excessive_depth}")

    forbidden_writer_count = 0
    missing_writer_count = 0
    for binding in contract.get("writer_bindings") or []:
        source = database_dir / str(binding["source"])
        if not source.is_file():
            errors.append(f"writer source missing: {binding['source']}")
            continue
        text = source.read_text(encoding="utf-8")
        for literal in binding.get("required_literals") or []:
            if str(literal) not in text:
                missing_writer_count += 1
                errors.append(f"writer {binding['source']} missing required literal: {literal}")
        for literal in binding.get("forbidden_literals") or []:
            count = text.count(str(literal))
            forbidden_writer_count += count
            if count:
                errors.append(f"writer {binding['source']} retains forbidden literal: {literal}")

    move_hash_mismatches = 0
    move_source_remaining = 0
    move_entries: list[tuple[str, bytes]] = []
    dual_write_count = 0
    for record in contract.get("move_records") or []:
        source_path = str(record["source"])
        destination_path = str(record["destination"])
        source_payload = base_file(repo_root, base_ref, source_path)
        destination = repo_root / destination_path
        if source_path in current_set or (repo_root / source_path).exists():
            move_source_remaining += 1
            errors.append(f"moved source remains: {source_path}")
        if (repo_root / source_path).exists() and destination.exists():
            dual_write_count += 1
        if not destination.is_file():
            move_hash_mismatches += 1
            errors.append(f"moved destination missing: {destination_path}")
            continue
        destination_payload = destination.read_bytes()
        expected_bytes = int(record["bytes"])
        expected_sha = str(record["sha256"])
        if (
            source_payload != destination_payload
            or len(destination_payload) != expected_bytes
            or sha256(destination_payload) != expected_sha
        ):
            move_hash_mismatches += 1
            errors.append(f"moved payload mismatch: {source_path} -> {destination_path}")
        move_entries.append((source_path, source_payload))

    move_count, move_bytes, move_sha = collection_fingerprint(move_entries)
    expected_move = contract.get("move_collection") or {}
    if (move_count, move_bytes, move_sha) != (
        int(expected_move.get("count") or -1),
        int(expected_move.get("bytes") or -1),
        str(expected_move.get("sha256") or ""),
    ):
        errors.append("move collection fingerprint mismatch")

    retired_remaining = 0
    retired_fingerprint_mismatches = 0
    for collection in contract.get("retired_collections") or []:
        prefix = str(collection["prefix"])
        listed = git_output(repo_root, ["ls-tree", "-rz", "--name-only", base_ref, "--", prefix])
        paths = [item.decode("utf-8") for item in listed.split(b"\0") if item]
        entries = [(path, base_file(repo_root, base_ref, path)) for path in paths]
        observed = collection_fingerprint(entries)
        expected = (
            int(collection["count"]),
            int(collection["bytes"]),
            str(collection["sha256"]),
        )
        if observed != expected:
            retired_fingerprint_mismatches += 1
            errors.append(f"retired collection fingerprint mismatch: {prefix}")
        remaining = [path for path in current_set if path == prefix or path.startswith(f"{prefix}/")]
        retired_remaining += len(remaining)
        if remaining:
            errors.append(f"retired paths remain under {prefix}: {len(remaining)}")

    topology = contract.get("topology") or {}
    current_top = {directory.split("/", 1)[0] for directory in current_dirs if directory != "."}
    base_top = {directory.split("/", 1)[0] for directory in base_dirs if directory != "."}
    observed_topology = {
        "base_file_count": len(base_paths),
        "current_file_count": len(current_paths),
        "base_directory_count_including_root": len(base_dirs),
        "current_directory_count_including_root": len(current_dirs),
        "base_top_level_count_including_root": len(base_top) + 1,
        "current_top_level_count_including_root": len(current_top) + 1,
    }
    for key in (
        "base_file_count",
        "base_directory_count_including_root",
        "base_top_level_count_including_root",
    ):
        observed = observed_topology[key]
        if int(topology.get(key) or -1) != observed:
            errors.append(f"topology {key}: expected {topology.get(key)}, observed {observed}")
    max_top_level = int(topology.get("max_current_top_level_count_including_root") or -1)
    if observed_topology["current_top_level_count_including_root"] > max_top_level:
        errors.append(
            "topology current_top_level_count_including_root exceeds "
            f"{max_top_level}: {observed_topology['current_top_level_count_including_root']}"
        )

    metrics = {
        **observed_topology,
        "owned_directory_count": len(current_dirs) - len(unowned_dirs),
        "unowned_directory_count": len(unowned_dirs),
        "duplicate_owner_count": len(duplicate_owner_keys),
        "destination_count": len(destination_paths),
        "duplicate_destination_count": len(duplicate_destinations),
        "duplicate_destination_domain_count": len(duplicate_domains),
        "excessive_destination_depth_count": len(excessive_depth),
        "missing_required_writer_literal_count": missing_writer_count,
        "forbidden_writer_literal_count": forbidden_writer_count,
        "moved_file_count": move_count,
        "moved_bytes": move_bytes,
        "moved_hash_mismatch_count": move_hash_mismatches,
        "moved_source_remaining_count": move_source_remaining,
        "dual_write_count": dual_write_count,
        "retired_path_remaining_count": retired_remaining,
        "retired_fingerprint_mismatch_count": retired_fingerprint_mismatches,
    }
    return {
        "status": "PASS" if not errors else "FAIL",
        "task_id": contract.get("task_id"),
        "acceptance_id": contract.get("acceptance_id"),
        "base_ref": base_ref,
        "metrics": metrics,
        "errors": errors,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database-dir", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--base-ref")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    database_dir = args.database_dir.expanduser().resolve()
    repo_root = database_dir.parent
    contract_path = args.contract
    if not contract_path.is_absolute():
        contract_path = database_dir / contract_path
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    base_ref = args.base_ref or str(contract["implementation_base_sha"])
    result = validate_contract(contract, database_dir, repo_root, base_ref)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
