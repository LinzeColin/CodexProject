#!/usr/bin/env python3
"""Governance ID V2 parsing, resolution, registry, and immutability rules.

The module has no network or write side effects. Allocation writes are isolated in
``governance_id_allocator.py`` so validators can safely import this file in CI.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping


SEGMENT = r"[A-Z][A-Za-z0-9]*"
TASK_ID_RE = re.compile(
    rf"^TSK\.(?P<project>{SEGMENT})\.(?P<program>{SEGMENT})\."
    r"(?P<sequence>[0-9]{4})$"
)
ACCEPTANCE_ID_RE = re.compile(
    rf"^ACC\.(?P<project>{SEGMENT})\.(?P<program>{SEGMENT})\."
    r"(?P<sequence>[0-9]{4})$"
)
EVENT_ID_RE = re.compile(
    rf"^EVT\.(?P<project>{SEGMENT})\.(?P<program>{SEGMENT})\."
    r"(?P<sequence>[0-9]{4})$"
)
GOAL_ID_RE = re.compile(rf"^PG\.(?P<project>{SEGMENT})\.(?P<program>{SEGMENT})$")
POSITIONAL_TASK_RE = re.compile(r"^S[1-9][0-9]*P[A-Z]T[0-9]{2,}$")
V2_PREFIX_RE = re.compile(r"^(TSK|ACC|PG|EVT)\.")
LEGACY_ID_RE = re.compile(
    r"^(?!(?:TSK|ACC|AC|PG|EVT)\.)[A-Za-z0-9][A-Za-z0-9_.-]{1,127}$"
)
IDEMPOTENCY_KEY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9:._/-]{2,127}$")
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
UTC_TIMESTAMP_RE = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"
)
SUPPORTED_KINDS = ("TSK", "ACC", "PG", "EVT")


class GovernanceIdError(ValueError):
    """Raised when an identifier or registry violates the V2 contract."""


@dataclass(frozen=True)
class GovernanceId:
    raw: str
    kind: str
    generation: str
    project: str | None = None
    program: str | None = None
    sequence: str | None = None

    @property
    def suffix(self) -> str | None:
        if self.kind not in {"TSK", "ACC"} or self.generation != "v2":
            return None
        return f"{self.project}.{self.program}.{self.sequence}"


def _v2_pattern(kind: str) -> re.Pattern[str]:
    patterns = {
        "TSK": TASK_ID_RE,
        "ACC": ACCEPTANCE_ID_RE,
        "PG": GOAL_ID_RE,
        "EVT": EVENT_ID_RE,
    }
    try:
        return patterns[kind]
    except KeyError as exc:
        raise GovernanceIdError(f"unsupported identifier kind: {kind}") from exc


def parse_identifier(value: object, expected_kind: str) -> GovernanceId:
    """Parse a V2 identifier or a grandfathered legacy identifier.

    A malformed value carrying a V2 prefix never falls back to legacy parsing.
    """

    if expected_kind not in SUPPORTED_KINDS:
        raise GovernanceIdError(f"unsupported identifier kind: {expected_kind}")
    if not isinstance(value, str) or not value.strip():
        raise GovernanceIdError(
            f"{expected_kind} identifier must be a non-empty string"
        )
    raw = value.strip()
    match = _v2_pattern(expected_kind).fullmatch(raw)
    if match:
        return GovernanceId(
            raw=raw,
            kind=expected_kind,
            generation="v2",
            project=match.group("project"),
            program=match.group("program"),
            sequence=match.groupdict().get("sequence"),
        )
    if V2_PREFIX_RE.match(raw):
        actual_kind = raw.split(".", 1)[0]
        if actual_kind != expected_kind:
            raise GovernanceIdError(
                f"identifier kind mismatch: expected {expected_kind}, got {actual_kind}"
            )
        raise GovernanceIdError(f"invalid {expected_kind} V2 identifier: {raw}")
    if LEGACY_ID_RE.fullmatch(raw):
        return GovernanceId(raw=raw, kind=expected_kind, generation="v1")
    raise GovernanceIdError(f"invalid {expected_kind} identifier: {raw}")


def validate_task_acceptance_pair(
    task_id: object,
    acceptance_id: object,
) -> tuple[GovernanceId, GovernanceId]:
    task = parse_identifier(task_id, "TSK")
    acceptance = parse_identifier(acceptance_id, "ACC")
    if task.generation != acceptance.generation:
        raise GovernanceIdError(
            "mixed V1/V2 task and acceptance identifiers require an explicit "
            "project-scoped alias mapping"
        )
    if task.generation == "v2" and task.suffix != acceptance.suffix:
        raise GovernanceIdError(
            "V2 task and acceptance identifiers must have the same "
            "project/program/sequence suffix"
        )
    return task, acceptance


def resolve_task_id(
    value: object,
    *,
    project: str,
    aliases: Mapping[str, Mapping[str, str]],
) -> str:
    """Compatibility resolver for the bootstrap mapping shape."""

    task = parse_identifier(value, "TSK")
    if task.generation == "v2":
        return task.raw
    project_aliases = aliases.get(project, {})
    resolved = project_aliases.get(task.raw)
    if resolved is None:
        raise GovernanceIdError(
            f"legacy task ID {task.raw} has no alias in project scope {project}"
        )
    parsed = parse_identifier(resolved, "TSK")
    if parsed.generation != "v2" or parsed.project != project:
        raise GovernanceIdError(
            f"legacy task ID {task.raw} resolves outside project scope {project}"
        )
    return parsed.raw


def validate_unique_task_ids(values: list[object]) -> list[str]:
    parsed = [parse_identifier(value, "TSK").raw for value in values]
    duplicates = sorted(value for value, count in Counter(parsed).items() if count > 1)
    if duplicates:
        raise GovernanceIdError(f"duplicate task identifiers: {', '.join(duplicates)}")
    return parsed


def serialize_registry(payload: Mapping[str, Any]) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def registry_sha256(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(serialize_registry(payload)).hexdigest()


def load_registry(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GovernanceIdError(f"cannot load ID registry {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise GovernanceIdError("ID registry root must be an object")
    return payload


def _cycle_path(graph: Mapping[str, list[str]]) -> list[str] | None:
    state: dict[str, int] = {}
    stack: list[str] = []

    def visit(node: str) -> list[str] | None:
        state[node] = 1
        stack.append(node)
        for dependency in graph.get(node, []):
            if dependency not in graph:
                continue
            if state.get(dependency) == 1:
                start = stack.index(dependency)
                return [*stack[start:], dependency]
            if state.get(dependency, 0) == 0:
                found = visit(dependency)
                if found:
                    return found
        stack.pop()
        state[node] = 2
        return None

    for node in graph:
        if state.get(node, 0) == 0:
            found = visit(node)
            if found:
                return found
    return None


def registry_identifier_index(
    payload: Mapping[str, Any],
) -> dict[tuple[str, str], dict[str, Any]]:
    index: dict[tuple[str, str], dict[str, Any]] = {}
    for allocation in payload.get("allocations", []):
        if not isinstance(allocation, dict):
            continue
        kind = allocation.get("kind")
        identifier = allocation.get("identifier")
        if isinstance(kind, str) and isinstance(identifier, str):
            index[(kind, identifier)] = allocation
        acceptance_id = allocation.get("acceptance_id")
        if kind == "TSK" and isinstance(acceptance_id, str):
            index[("ACC", acceptance_id)] = allocation
    return index


def validate_registry(payload: Mapping[str, Any]) -> list[str]:
    """Return every registry violation; an empty list is a PASS."""

    errors: list[str] = []
    if payload.get("schema_version") != 2:
        errors.append("registry schema_version must equal 2")
    revision = payload.get("registry_revision")
    if not isinstance(revision, int) or revision < 1:
        errors.append("registry_revision must be an integer >= 1")
    if payload.get("repository") != "LinzeColin/CodexProject":
        errors.append("repository must equal LinzeColin/CodexProject")
    last_updated_at = payload.get("last_updated_at")
    if not isinstance(last_updated_at, str) or not UTC_TIMESTAMP_RE.fullmatch(
        last_updated_at
    ):
        errors.append("last_updated_at must be a whole-second UTC timestamp")
    bootstrap = payload.get("bootstrap")
    if not isinstance(bootstrap, dict):
        errors.append("bootstrap must be an object")
        bootstrap = {}
    if not isinstance(
        bootstrap.get("imported_at"), str
    ) or not UTC_TIMESTAMP_RE.fullmatch(str(bootstrap.get("imported_at", ""))):
        errors.append("bootstrap.imported_at must be a whole-second UTC timestamp")
    if not isinstance(
        bootstrap.get("implementation_base_sha"), str
    ) or not SHA1_RE.fullmatch(str(bootstrap.get("implementation_base_sha", ""))):
        errors.append("bootstrap.implementation_base_sha must be a 40-character SHA")
    for field in ("source_package_sha256", "task_registry_sha256", "roadmap_sha256"):
        value = bootstrap.get(field)
        if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
            errors.append(f"bootstrap.{field} must be a SHA256")
    allocations = payload.get("allocations")
    aliases = payload.get("aliases")
    migrated_projects = payload.get("migrated_projects", [])
    if not isinstance(allocations, list):
        return [*errors, "allocations must be an array"]
    if not isinstance(aliases, list):
        errors.append("aliases must be an array")
        aliases = []
    if not isinstance(migrated_projects, list) or not all(
        isinstance(value, str) and re.fullmatch(SEGMENT, value)
        for value in migrated_projects
    ):
        errors.append("migrated_projects must be an array of project segments")
        migrated_projects = []
    elif len(set(migrated_projects)) != len(migrated_projects):
        errors.append("migrated_projects must not contain duplicates")

    identifiers: list[str] = []
    acceptance_ids: list[str] = []
    idempotency_keys: list[str] = []
    occupied: list[tuple[object, ...]] = []
    graph: dict[str, list[str]] = {}

    for position, allocation in enumerate(allocations):
        label = f"allocations[{position}]"
        if not isinstance(allocation, dict):
            errors.append(f"{label} must be an object")
            continue
        kind = allocation.get("kind")
        identifier = allocation.get("identifier")
        project = allocation.get("project")
        program = allocation.get("program")
        idempotency_key = allocation.get("idempotency_key")
        base_sha = allocation.get("allocated_from_base_sha")
        source_ref = allocation.get("source_ref")
        if kind not in {"TSK", "PG", "EVT"}:
            errors.append(f"{label}.kind must be TSK, PG, or EVT")
            continue
        try:
            parsed = parse_identifier(identifier, kind)
        except GovernanceIdError as exc:
            errors.append(f"{label}.identifier: {exc}")
            continue
        if parsed.generation != "v2":
            errors.append(f"{label}.identifier must be V2")
        if parsed.project != project or parsed.program != program:
            errors.append(f"{label} project/program do not match identifier")
        if not isinstance(idempotency_key, str) or not IDEMPOTENCY_KEY_RE.fullmatch(
            idempotency_key
        ):
            errors.append(f"{label}.idempotency_key is invalid")
        else:
            idempotency_keys.append(idempotency_key)
        if not isinstance(base_sha, str) or not SHA1_RE.fullmatch(base_sha):
            errors.append(f"{label}.allocated_from_base_sha must be a 40-character SHA")
        if not isinstance(source_ref, str) or not source_ref.strip():
            errors.append(f"{label}.source_ref must be non-empty")

        identifiers.append(parsed.raw)
        if kind in {"TSK", "EVT"}:
            sequence = allocation.get("sequence")
            if not isinstance(sequence, int) or not 1 <= sequence <= 9999:
                errors.append(f"{label}.sequence must be an integer from 1 to 9999")
            elif parsed.sequence != f"{sequence:04d}":
                errors.append(f"{label}.sequence does not match identifier")
            occupied.append((kind, project, program, sequence))
        else:
            if "sequence" in allocation:
                errors.append(f"{label}.sequence is forbidden for PG")
            occupied.append((kind, project, program))

        dependencies = allocation.get("dependencies", [])
        if kind == "TSK":
            acceptance_id = allocation.get("acceptance_id")
            try:
                validate_task_acceptance_pair(identifier, acceptance_id)
            except GovernanceIdError as exc:
                errors.append(f"{label}.acceptance_id: {exc}")
            if isinstance(acceptance_id, str):
                acceptance_ids.append(acceptance_id)
            if not isinstance(dependencies, list) or not all(
                isinstance(value, str) for value in dependencies
            ):
                errors.append(f"{label}.dependencies must be an array of Task IDs")
                dependencies = []
            graph[parsed.raw] = list(dependencies)
        elif dependencies not in (None, []):
            errors.append(f"{label}.dependencies are only valid for TSK")

    for value, count in Counter(identifiers).items():
        if count > 1:
            errors.append(f"duplicate V2 identifier: {value}")
    for value, count in Counter(acceptance_ids).items():
        if count > 1:
            errors.append(f"duplicate V2 acceptance identifier: {value}")
    for value, count in Counter(idempotency_keys).items():
        if count > 1:
            errors.append(f"duplicate idempotency key: {value}")
    for value, count in Counter(occupied).items():
        if count > 1:
            errors.append(f"reused namespace slot: {value}")

    bootstrap_task_count = sum(
        isinstance(item, dict)
        and item.get("kind") == "TSK"
        and not str(item.get("source_ref", "")).startswith("allocator:")
        for item in allocations
    )
    if bootstrap.get("task_count") != bootstrap_task_count:
        errors.append(
            "bootstrap.task_count must equal the number of non-allocator Task imports"
        )

    task_ids = set(graph)
    for task_id, dependencies in graph.items():
        for dependency in dependencies:
            try:
                parsed_dependency = parse_identifier(dependency, "TSK")
            except GovernanceIdError as exc:
                errors.append(f"{task_id} dependency {dependency!r}: {exc}")
                continue
            if parsed_dependency.generation != "v2" or dependency not in task_ids:
                errors.append(f"{task_id} dependency is orphaned: {dependency}")
    cycle = _cycle_path(graph)
    if cycle:
        errors.append(f"dependency cycle: {' -> '.join(cycle)}")

    index = registry_identifier_index(payload)
    alias_keys: list[tuple[str, str, str]] = []
    for position, alias in enumerate(aliases):
        label = f"aliases[{position}]"
        if not isinstance(alias, dict):
            errors.append(f"{label} must be an object")
            continue
        project = alias.get("project")
        kind = alias.get("kind")
        legacy_id = alias.get("legacy_id")
        target_id = alias.get("target_id")
        if kind not in SUPPORTED_KINDS:
            errors.append(f"{label}.kind is unsupported")
            continue
        try:
            legacy = parse_identifier(legacy_id, kind)
        except GovernanceIdError as exc:
            errors.append(f"{label}.legacy_id: {exc}")
            continue
        if legacy.generation != "v1":
            errors.append(f"{label}.legacy_id must be legacy")
        try:
            target = parse_identifier(target_id, kind)
        except GovernanceIdError as exc:
            errors.append(f"{label}.target_id: {exc}")
            continue
        if target.generation != "v2" or target.project != project:
            errors.append(f"{label}.target_id must be V2 in project scope {project}")
        if (kind, target.raw) not in index:
            errors.append(f"{label}.target_id is orphaned: {target.raw}")
        alias_keys.append((str(project), kind, legacy.raw))
    for value, count in Counter(alias_keys).items():
        if count > 1:
            errors.append(f"ambiguous project-scoped alias: {value}")
    return errors


def resolve_registry_identifier(
    value: object,
    *,
    kind: str,
    project: str,
    registry: Mapping[str, Any],
) -> str:
    errors = validate_registry(registry)
    if errors:
        raise GovernanceIdError("invalid registry: " + "; ".join(errors))
    parsed = parse_identifier(value, kind)
    index = registry_identifier_index(registry)
    if parsed.generation == "v2":
        if (kind, parsed.raw) not in index:
            raise GovernanceIdError(f"orphaned V2 {kind} reference: {parsed.raw}")
        return parsed.raw
    matches = [
        alias.get("target_id")
        for alias in registry.get("aliases", [])
        if alias.get("project") == project
        and alias.get("kind") == kind
        and alias.get("legacy_id") == parsed.raw
    ]
    if len(matches) != 1:
        raise GovernanceIdError(
            f"legacy {kind} reference {parsed.raw} resolves {len(matches)} times "
            f"in project scope {project}"
        )
    return str(matches[0])


def validate_registry_immutability(
    current: Mapping[str, Any],
    baseline: Mapping[str, Any],
) -> list[str]:
    """Reject removals, renames, reuse, or alias retargeting from a baseline."""

    errors = [
        *(f"current: {error}" for error in validate_registry(current)),
        *(f"baseline: {error}" for error in validate_registry(baseline)),
    ]
    if errors:
        return errors

    def by_key(payload: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
        return {str(item["idempotency_key"]): item for item in payload["allocations"]}

    current_by_key = by_key(current)
    immutable_fields = (
        "kind",
        "identifier",
        "acceptance_id",
        "project",
        "program",
        "sequence",
    )
    for key, old in by_key(baseline).items():
        new = current_by_key.get(key)
        if new is None:
            errors.append(f"allocation removed for idempotency key: {key}")
            continue
        changed = [
            field for field in immutable_fields if old.get(field) != new.get(field)
        ]
        if changed:
            errors.append(
                f"immutable allocation changed for {key}: {', '.join(changed)}"
            )

    current_aliases = {
        (str(item["project"]), str(item["kind"]), str(item["legacy_id"])): item
        for item in current.get("aliases", [])
    }
    for old in baseline.get("aliases", []):
        key = (str(old["project"]), str(old["kind"]), str(old["legacy_id"]))
        new = current_aliases.get(key)
        if new is None:
            errors.append(f"legacy alias removed: {key}")
        elif old.get("target_id") != new.get("target_id"):
            errors.append(f"legacy alias retargeted: {key}")
    removed_migrations = sorted(
        set(baseline.get("migrated_projects", []))
        - set(current.get("migrated_projects", []))
    )
    for project in removed_migrations:
        errors.append(f"migrated project marker removed: {project}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate governance identifiers.")
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--acceptance-id", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        task, acceptance = validate_task_acceptance_pair(
            args.task_id, args.acceptance_id
        )
    except GovernanceIdError as exc:
        print(f"GOVERNANCE_ID_VALIDATION=FAIL: {exc}")
        return 1
    if args.json:
        print(
            json.dumps(
                {"acceptance": asdict(acceptance), "task": asdict(task)},
                ensure_ascii=False,
                sort_keys=True,
            )
        )
    else:
        print(f"GOVERNANCE_ID_VALIDATION=PASS generation={task.generation}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
