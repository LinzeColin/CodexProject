#!/usr/bin/env python3
"""Fail-closed allocator for immutable Governance ID V2 records."""

from __future__ import annotations

import argparse
import copy
import fcntl
import hashlib
import json
import os
import re
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from governance_ids import (
    IDEMPOTENCY_KEY_RE,
    GovernanceIdError,
    load_registry,
    parse_identifier,
    registry_identifier_index,
    registry_sha256,
    resolve_registry_identifier,
    serialize_registry,
    validate_registry,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "governance" / "id_registry.json"
SEGMENT_RE = re.compile(r"^[A-Z][A-Za-z0-9]*$")


def _git(repo_root: Path, *args: str) -> str:
    process = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if process.returncode != 0:
        detail = (
            process.stderr.strip() or process.stdout.strip() or "git command failed"
        )
        raise GovernanceIdError(detail)
    return process.stdout.strip()


def _current_head(repo_root: Path) -> str:
    return _git(repo_root, "rev-parse", "HEAD")


def _lock_path(repo_root: Path) -> Path:
    value = Path(
        _git(repo_root, "rev-parse", "--git-path", "governance-id-allocator.lock")
    )
    return value if value.is_absolute() else repo_root / value


def _validate_paths(repo_root: Path, registry_path: Path) -> tuple[Path, Path]:
    root = repo_root.resolve()
    registry = registry_path.resolve()
    if not registry.is_relative_to(root):
        raise GovernanceIdError("registry path must remain inside the repository")
    if registry_path.is_symlink():
        raise GovernanceIdError("registry path must not be a symlink")
    return root, registry


def _existing_idempotent(
    payload: dict[str, Any],
    *,
    kind: str,
    project: str,
    program: str,
    idempotency_key: str,
) -> dict[str, Any] | None:
    matches = [
        item
        for item in payload.get("allocations", [])
        if item.get("idempotency_key") == idempotency_key
    ]
    if not matches:
        return None
    if len(matches) != 1:
        raise GovernanceIdError(f"ambiguous idempotency key: {idempotency_key}")
    allocation = matches[0]
    expected = (kind, project, program)
    actual = (
        allocation.get("kind"),
        allocation.get("project"),
        allocation.get("program"),
    )
    if actual != expected:
        raise GovernanceIdError(
            f"idempotency key {idempotency_key} is already bound to {actual}"
        )
    return allocation


def _plan_allocation(
    payload: dict[str, Any],
    *,
    kind: str,
    project: str,
    program: str,
    base_sha: str,
    idempotency_key: str,
    dependencies: Sequence[str],
    allocated_at: str,
) -> tuple[dict[str, Any], dict[str, Any], bool]:
    existing = _existing_idempotent(
        payload,
        kind=kind,
        project=project,
        program=program,
        idempotency_key=idempotency_key,
    )
    if existing is not None:
        return payload, existing, True

    if kind != "TSK" and dependencies:
        raise GovernanceIdError("dependencies are only valid when allocating a Task")
    if kind == "TSK":
        for dependency in dependencies:
            resolve_registry_identifier(
                dependency,
                kind="TSK",
                project=project,
                registry=payload,
            )

    next_payload = copy.deepcopy(payload)
    allocations = next_payload["allocations"]
    if kind == "PG":
        identifier = f"PG.{project}.{program}"
        if ("PG", identifier) in registry_identifier_index(next_payload):
            raise GovernanceIdError(
                f"goal identifier is already allocated: {identifier}"
            )
        allocation: dict[str, Any] = {
            "kind": kind,
            "identifier": identifier,
            "project": project,
            "program": program,
            "idempotency_key": idempotency_key,
            "allocated_from_base_sha": base_sha,
            "allocated_at": allocated_at,
            "source_ref": f"allocator:{idempotency_key}",
        }
    else:
        used = [
            int(item["sequence"])
            for item in allocations
            if item.get("kind") == kind
            and item.get("project") == project
            and item.get("program") == program
        ]
        sequence = max(used, default=0) + 1
        if sequence > 9999:
            raise GovernanceIdError(
                f"identifier namespace is exhausted: {kind}.{project}.{program}"
            )
        identifier = f"{kind}.{project}.{program}.{sequence:04d}"
        allocation = {
            "kind": kind,
            "identifier": identifier,
            "project": project,
            "program": program,
            "sequence": sequence,
            "idempotency_key": idempotency_key,
            "allocated_from_base_sha": base_sha,
            "allocated_at": allocated_at,
            "source_ref": f"allocator:{idempotency_key}",
        }
        if kind == "TSK":
            allocation["acceptance_id"] = f"ACC.{project}.{program}.{sequence:04d}"
            allocation["dependencies"] = list(dependencies)

    allocations.append(allocation)
    allocations.sort(
        key=lambda item: (
            item["project"],
            item["program"],
            item["kind"],
            item.get("sequence", 0),
        )
    )
    next_payload["registry_revision"] = int(next_payload["registry_revision"]) + 1
    next_payload["last_updated_at"] = allocated_at
    errors = validate_registry(next_payload)
    if errors:
        raise GovernanceIdError("planned allocation is invalid: " + "; ".join(errors))
    return next_payload, allocation, False


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o644)
        os.replace(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        temporary.unlink(missing_ok=True)


def allocate_identifier(
    *,
    repo_root: Path,
    registry_path: Path,
    kind: str,
    project: str,
    program: str,
    base_sha: str,
    idempotency_key: str,
    dependencies: Sequence[str] = (),
    apply: bool = False,
    expected_registry_sha256: str | None = None,
    allocated_at: str | None = None,
) -> dict[str, Any]:
    root, registry = _validate_paths(repo_root, registry_path)
    if kind not in {"TSK", "PG", "EVT"}:
        raise GovernanceIdError("kind must be TSK, PG, or EVT")
    for name, value in (("project", project), ("program", program)):
        if not SEGMENT_RE.fullmatch(value):
            raise GovernanceIdError(f"{name} must match {SEGMENT_RE.pattern}")
    if not IDEMPOTENCY_KEY_RE.fullmatch(idempotency_key):
        raise GovernanceIdError("invalid idempotency key")
    if _current_head(root) != base_sha:
        raise GovernanceIdError("base SHA does not match current HEAD")
    timestamp = allocated_at or datetime.now(timezone.utc).replace(
        microsecond=0
    ).isoformat().replace("+00:00", "Z")

    def execute_locked() -> dict[str, Any]:
        payload = load_registry(registry)
        errors = validate_registry(payload)
        if errors:
            raise GovernanceIdError("invalid registry: " + "; ".join(errors))
        current_digest = registry_sha256(payload)
        existing = _existing_idempotent(
            payload,
            kind=kind,
            project=project,
            program=program,
            idempotency_key=idempotency_key,
        )
        if existing is not None:
            return {
                "status": "PASS",
                "mode": "APPLY" if apply else "DRY_RUN",
                "mutated": False,
                "idempotent_replay": True,
                "registry_sha256": current_digest,
                "allocation": existing,
            }
        if apply and current_digest != expected_registry_sha256:
            raise GovernanceIdError(
                "registry SHA changed after dry-run; concurrent allocation lost single-flight"
            )
        next_payload, allocation, _ = _plan_allocation(
            payload,
            kind=kind,
            project=project,
            program=program,
            base_sha=base_sha,
            idempotency_key=idempotency_key,
            dependencies=dependencies,
            allocated_at=timestamp,
        )
        next_digest = registry_sha256(next_payload)
        if apply:
            _atomic_write(registry, serialize_registry(next_payload))
        return {
            "status": "PASS",
            "mode": "APPLY" if apply else "DRY_RUN",
            "mutated": apply,
            "idempotent_replay": False,
            "registry_sha256": current_digest,
            "next_registry_sha256": next_digest,
            "allocation": allocation,
        }

    if not apply:
        return execute_locked()
    if not expected_registry_sha256:
        raise GovernanceIdError("--expected-registry-sha256 is required with --apply")
    lock_path = _lock_path(root)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+", encoding="utf-8") as lock_handle:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
        if _current_head(root) != base_sha:
            raise GovernanceIdError("base SHA changed while waiting for allocator lock")
        return execute_locked()


def migrate_project_aliases(
    *,
    repo_root: Path,
    registry_path: Path,
    project: str,
    program: str,
    base_sha: str,
    task_aliases: Mapping[str, Sequence[str]],
    task_dependencies: Mapping[str, Sequence[str]],
    event_aliases: Sequence[str],
    canonical_events: Sequence[tuple[str, str]] = (),
    apply: bool = False,
    expected_registry_sha256: str | None = None,
    allocated_at: str | None = None,
) -> dict[str, Any]:
    """Atomically allocate a migrated project namespace and install aliases.

    ``task_aliases`` maps one legacy Task ID to its legacy Acceptance IDs.
    ``task_dependencies`` uses legacy or V2 Task IDs and is rewritten to V2 in
    the allocation ledger. Historical documents remain unchanged; readers use
    the immutable project-scoped aliases installed by this transaction.
    """

    root, registry = _validate_paths(repo_root, registry_path)
    for name, value in (("project", project), ("program", program)):
        if not SEGMENT_RE.fullmatch(value):
            raise GovernanceIdError(f"{name} must match {SEGMENT_RE.pattern}")
    if _current_head(root) != base_sha:
        raise GovernanceIdError("base SHA does not match current HEAD")
    timestamp = allocated_at or datetime.now(timezone.utc).replace(
        microsecond=0
    ).isoformat().replace("+00:00", "Z")

    legacy_tasks = sorted(task_aliases)
    legacy_events = sorted(set(event_aliases))
    if len(legacy_events) != len(event_aliases):
        raise GovernanceIdError("event_aliases must not contain duplicates")
    unknown_dependency_owners = sorted(set(task_dependencies) - set(legacy_tasks))
    if unknown_dependency_owners:
        raise GovernanceIdError(
            "task_dependencies contains unknown legacy tasks: "
            + ", ".join(unknown_dependency_owners)
        )

    acceptance_owners: dict[str, str] = {}
    for legacy_task in legacy_tasks:
        task = parse_identifier(legacy_task, "TSK")
        if task.generation != "v1":
            raise GovernanceIdError(
                f"task alias source must be legacy: {legacy_task}"
            )
        for legacy_acceptance in task_aliases[legacy_task]:
            acceptance = parse_identifier(legacy_acceptance, "ACC")
            if acceptance.generation != "v1":
                raise GovernanceIdError(
                    f"acceptance alias source must be legacy: {legacy_acceptance}"
                )
            previous = acceptance_owners.setdefault(legacy_acceptance, legacy_task)
            if previous != legacy_task:
                raise GovernanceIdError(
                    f"legacy acceptance alias has multiple task owners: "
                    f"{legacy_acceptance}"
                )
    for legacy_event in legacy_events:
        event = parse_identifier(legacy_event, "EVT")
        if event.generation != "v1":
            raise GovernanceIdError(
                f"event alias source must be legacy: {legacy_event}"
            )
    for event_program, idempotency_key in canonical_events:
        if not SEGMENT_RE.fullmatch(event_program):
            raise GovernanceIdError(
                f"canonical event program must match {SEGMENT_RE.pattern}"
            )
        if not IDEMPOTENCY_KEY_RE.fullmatch(idempotency_key):
            raise GovernanceIdError("canonical event idempotency key is invalid")

    def migration_key(kind: str, legacy_id: str) -> str:
        digest = hashlib.sha256(legacy_id.encode("utf-8")).hexdigest()[:24]
        return f"project-migration:{project}:{kind}:{digest}"

    def execute_locked() -> dict[str, Any]:
        payload = load_registry(registry)
        errors = validate_registry(payload)
        if errors:
            raise GovernanceIdError("invalid registry: " + "; ".join(errors))
        current_digest = registry_sha256(payload)
        if apply and current_digest != expected_registry_sha256:
            raise GovernanceIdError(
                "registry SHA changed after dry-run; migration lost single-flight"
            )

        next_payload = copy.deepcopy(payload)
        task_targets: dict[str, str] = {}
        task_replays: dict[str, bool] = {}
        for legacy_task in legacy_tasks:
            next_payload, allocation, replay = _plan_allocation(
                next_payload,
                kind="TSK",
                project=project,
                program=program,
                base_sha=base_sha,
                idempotency_key=migration_key("TSK", legacy_task),
                dependencies=(),
                allocated_at=timestamp,
            )
            task_targets[legacy_task] = str(allocation["identifier"])
            task_replays[legacy_task] = replay

        event_targets: dict[str, str] = {}
        for legacy_event in legacy_events:
            next_payload, allocation, _ = _plan_allocation(
                next_payload,
                kind="EVT",
                project=project,
                program=program,
                base_sha=base_sha,
                idempotency_key=migration_key("EVT", legacy_event),
                dependencies=(),
                allocated_at=timestamp,
            )
            event_targets[legacy_event] = str(allocation["identifier"])

        canonical_event_ids: list[str] = []
        for event_program, idempotency_key in canonical_events:
            next_payload, allocation, _ = _plan_allocation(
                next_payload,
                kind="EVT",
                project=project,
                program=event_program,
                base_sha=base_sha,
                idempotency_key=idempotency_key,
                dependencies=(),
                allocated_at=timestamp,
            )
            canonical_event_ids.append(str(allocation["identifier"]))

        desired_aliases: list[dict[str, str]] = []
        allocation_index = registry_identifier_index(next_payload)
        for legacy_task, target_id in task_targets.items():
            allocation = allocation_index[("TSK", target_id)]
            desired_aliases.append(
                {
                    "project": project,
                    "kind": "TSK",
                    "legacy_id": legacy_task,
                    "target_id": target_id,
                }
            )
            for legacy_acceptance in sorted(task_aliases[legacy_task]):
                desired_aliases.append(
                    {
                        "project": project,
                        "kind": "ACC",
                        "legacy_id": legacy_acceptance,
                        "target_id": str(allocation["acceptance_id"]),
                    }
                )
        for legacy_event, target_id in event_targets.items():
            desired_aliases.append(
                {
                    "project": project,
                    "kind": "EVT",
                    "legacy_id": legacy_event,
                    "target_id": target_id,
                }
            )

        existing_aliases = {
            (item.get("project"), item.get("kind"), item.get("legacy_id")): item
            for item in next_payload.get("aliases", [])
            if isinstance(item, dict)
        }
        aliases_added = 0
        for alias in desired_aliases:
            key = (alias["project"], alias["kind"], alias["legacy_id"])
            existing = existing_aliases.get(key)
            if existing is None:
                next_payload["aliases"].append(alias)
                existing_aliases[key] = alias
                aliases_added += 1
            elif existing.get("target_id") != alias["target_id"]:
                raise GovernanceIdError(
                    f"legacy alias target conflict: {key}"
                )
        next_payload["aliases"].sort(
            key=lambda item: (
                str(item["project"]),
                str(item["kind"]),
                str(item["legacy_id"]),
            )
        )

        migrated_projects = list(next_payload.get("migrated_projects", []))
        marker_added = project not in migrated_projects
        if marker_added:
            migrated_projects.append(project)
            migrated_projects.sort()
        next_payload["migrated_projects"] = migrated_projects

        allocation_index = registry_identifier_index(next_payload)
        for legacy_task, target_id in task_targets.items():
            resolved_dependencies: list[str] = []
            for dependency in task_dependencies.get(legacy_task, ()):
                if dependency in task_targets:
                    resolved = task_targets[dependency]
                else:
                    resolved = resolve_registry_identifier(
                        dependency,
                        kind="TSK",
                        project=project,
                        registry=next_payload,
                    )
                if resolved not in resolved_dependencies:
                    resolved_dependencies.append(resolved)
            allocation = allocation_index[("TSK", target_id)]
            existing_dependencies = list(allocation.get("dependencies", []))
            if task_replays[legacy_task] and existing_dependencies != resolved_dependencies:
                raise GovernanceIdError(
                    f"idempotent migration dependency drift for {legacy_task}"
                )
            allocation["dependencies"] = resolved_dependencies

        metadata_changed = aliases_added > 0 or marker_added
        if metadata_changed:
            next_payload["registry_revision"] = (
                int(next_payload["registry_revision"]) + 1
            )
            next_payload["last_updated_at"] = timestamp
        errors = validate_registry(next_payload)
        if errors:
            raise GovernanceIdError(
                "planned project migration is invalid: " + "; ".join(errors)
            )
        next_digest = registry_sha256(next_payload)
        mutated = next_digest != current_digest
        if apply and mutated:
            _atomic_write(registry, serialize_registry(next_payload))
        return {
            "status": "PASS",
            "mode": "APPLY" if apply else "DRY_RUN",
            "mutated": apply and mutated,
            "idempotent_replay": not mutated,
            "registry_sha256": current_digest,
            "next_registry_sha256": next_digest,
            "project": project,
            "program": program,
            "task_targets": task_targets,
            "event_targets": event_targets,
            "canonical_event_ids": canonical_event_ids,
            "alias_count": len(desired_aliases),
            "aliases_added": aliases_added,
            "migrated_project_marker_added": marker_added,
            "registry_revision": next_payload["registry_revision"],
        }

    if not apply:
        return execute_locked()
    if not expected_registry_sha256:
        raise GovernanceIdError(
            "--expected-registry-sha256 is required with migration apply"
        )
    lock_path = _lock_path(root)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+", encoding="utf-8") as lock_handle:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
        if _current_head(root) != base_sha:
            raise GovernanceIdError("base SHA changed while waiting for allocator lock")
        return execute_locked()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Allocate immutable Governance ID V2 records."
    )
    parser.add_argument("--kind", choices=("TSK", "PG", "EVT"), required=True)
    parser.add_argument("--project", required=True)
    parser.add_argument("--program", required=True)
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--idempotency-key", required=True)
    parser.add_argument("--dependency", action="append", default=[])
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--expected-registry-sha256")
    parser.add_argument(
        "--allocated-at", help="Test/replay timestamp; default is current UTC"
    )
    args = parser.parse_args()
    try:
        result = allocate_identifier(
            repo_root=args.repo_root,
            registry_path=args.registry,
            kind=args.kind,
            project=args.project,
            program=args.program,
            base_sha=args.base_sha,
            idempotency_key=args.idempotency_key,
            dependencies=args.dependency,
            apply=args.apply,
            expected_registry_sha256=args.expected_registry_sha256,
            allocated_at=args.allocated_at,
        )
    except GovernanceIdError as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
