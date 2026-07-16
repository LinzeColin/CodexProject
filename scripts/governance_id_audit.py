#!/usr/bin/env python3
"""Repository-wide semantic audit for Governance ID V2 metadata."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from governance_ids import (
    POSITIONAL_TASK_RE,
    V2_PREFIX_RE,
    GovernanceIdError,
    load_registry,
    parse_identifier,
    resolve_registry_identifier,
    validate_registry,
    validate_registry_immutability,
)
from validate_project_governance import load_yaml


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "governance" / "id_registry.json"
POSITIONAL_TOKEN_RE = re.compile(
    r"(?<![A-Za-z0-9_.-])S[1-9][0-9]*P[A-Z]T[0-9]{2,}(?![A-Za-z0-9_.-])"
)
POSITIONAL_GIT_PATTERN = r"S[1-9][0-9]*P[A-Z]T[0-9][0-9]+"
FIELD_KIND = {
    "task_id": "TSK",
    "task_ids": "TSK",
    "roadmap_task_id": "TSK",
    "current_task_id": "TSK",
    "next_executable_task": "TSK",
    "unknown_task_id": "TSK",
    "unknown_task_ids": "TSK",
    "dependencies": "TSK",
    "blocked_by": "TSK",
    "acceptance_id": "ACC",
    "acceptance_ids": "ACC",
    "next_gate_id": "ACC",
    "event_id": "EVT",
    "goal_id": "PG",
    "pursuing_goal": "PG",
    "pursuing_goal_id": "PG",
}
CANONICAL_PROJECT_FILES = (
    "docs/governance/project.yaml",
    "docs/governance/roadmap.yaml",
    "docs/governance/delivery_tasks.yaml",
    "docs/governance/events.jsonl",
    "docs/governance/development_events.jsonl",
)


@dataclass(frozen=True)
class Reference:
    project: str
    kind: str
    value: str
    path: str
    field: str


def _string_values(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value.strip()
    elif isinstance(value, list):
        for item in value:
            yield from _string_values(item)


def collect_references(
    payload: Any,
    *,
    project: str,
    path: str,
) -> list[Reference]:
    references: list[Reference] = []

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            for field, child in value.items():
                kind = FIELD_KIND.get(str(field))
                if kind:
                    for raw in _string_values(child):
                        if raw:
                            references.append(
                                Reference(
                                    project=project,
                                    kind=kind,
                                    value=raw,
                                    path=path,
                                    field=str(field),
                                )
                            )
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(payload)
    return references


def audit_references(
    references: Iterable[Reference],
    registry: Mapping[str, Any],
) -> tuple[list[str], dict[str, int]]:
    errors: list[str] = []
    counters = {
        "references_observed": 0,
        "v2_references": 0,
        "v2_references_resolved": 0,
        "legacy_references_observed": 0,
        "legacy_references_resolved": 0,
        "strict_legacy_references_observed": 0,
        "strict_legacy_references_resolved": 0,
        "non_identifier_values_ignored": 0,
    }
    migrated_projects = set(registry.get("migrated_projects", []))
    for reference in references:
        counters["references_observed"] += 1
        try:
            parsed = parse_identifier(reference.value, reference.kind)
        except GovernanceIdError as exc:
            if V2_PREFIX_RE.match(reference.value):
                errors.append(
                    f"{reference.path}:{reference.field}: malformed V2 reference "
                    f"{reference.value!r}: {exc}"
                )
            else:
                counters["non_identifier_values_ignored"] += 1
            continue
        if parsed.generation == "v1":
            counters["legacy_references_observed"] += 1
            strict_alias_required = reference.project in migrated_projects
            if strict_alias_required:
                counters["strict_legacy_references_observed"] += 1
            aliases = [
                item
                for item in registry.get("aliases", [])
                if item.get("project") == reference.project
                and item.get("kind") == reference.kind
                and item.get("legacy_id") == parsed.raw
            ]
            if not aliases:
                if strict_alias_required:
                    errors.append(
                        f"{reference.path}:{reference.field}: migrated project "
                        f"legacy {reference.kind} reference {parsed.raw} has no alias "
                        f"in {reference.project}"
                    )
                else:
                    # Dual-read preserves the project-scoped legacy identity until a
                    # project migration installs its immutable V2 alias.
                    counters["legacy_references_resolved"] += 1
            elif len(aliases) == 1:
                try:
                    resolve_registry_identifier(
                        parsed.raw,
                        kind=reference.kind,
                        project=reference.project,
                        registry=registry,
                    )
                except GovernanceIdError as exc:
                    errors.append(f"{reference.path}:{reference.field}: {exc}")
                else:
                    counters["legacy_references_resolved"] += 1
                    if strict_alias_required:
                        counters["strict_legacy_references_resolved"] += 1
            else:
                errors.append(
                    f"{reference.path}:{reference.field}: legacy reference "
                    f"{parsed.raw} has {len(aliases)} aliases in {reference.project}"
                )
            continue
        counters["v2_references"] += 1
        try:
            resolve_registry_identifier(
                parsed.raw,
                kind=reference.kind,
                project=reference.project,
                registry=registry,
            )
        except GovernanceIdError as exc:
            errors.append(f"{reference.path}:{reference.field}: {exc}")
        else:
            counters["v2_references_resolved"] += 1
    return errors, counters


def new_positional_identifiers(
    current: set[tuple[str, str]],
    baseline: set[tuple[str, str]],
) -> set[tuple[str, str]]:
    """Compare identity sets, so Stage/Phase movement does not look like creation."""

    return current - baseline


def _load_jsonl_text(text: str) -> list[Any]:
    values: list[Any] = []
    for line_number, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        try:
            values.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise GovernanceIdError(f"invalid JSONL line {line_number}: {exc}") from exc
    return values


def _load_path(path: Path) -> Any:
    if path.suffix in {".yaml", ".yml"}:
        return load_yaml(path)
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".jsonl":
        return _load_jsonl_text(text)
    return json.loads(text)


def _project_entries(root: Path) -> list[dict[str, str]]:
    config = load_yaml(root / "governance" / "projects.yaml")
    projects = config.get("projects", []) if isinstance(config, dict) else []
    entries: list[dict[str, str]] = []
    for item in projects:
        if (
            isinstance(item, dict)
            and isinstance(item.get("project_id"), str)
            and isinstance(item.get("path"), str)
        ):
            entries.append({"project_id": item["project_id"], "path": item["path"]})
    return entries


def _metadata_documents(root: Path) -> tuple[list[tuple[Path, str, Any]], list[str]]:
    documents: list[tuple[Path, str, Any]] = []
    errors: list[str] = []
    for project in _project_entries(root):
        for relative in CANONICAL_PROJECT_FILES:
            path = root / project["path"] / relative
            if not path.exists():
                continue
            try:
                documents.append((path, project["project_id"], _load_path(path)))
            except (OSError, ValueError, GovernanceIdError) as exc:
                errors.append(f"cannot parse {path.relative_to(root)}: {exc}")
    for pattern in (
        "governance/run_manifests/*.json",
        "governance/run_receipts/*.json",
    ):
        for path in sorted(root.glob(pattern)):
            try:
                payload = _load_path(path)
            except (OSError, ValueError, GovernanceIdError) as exc:
                errors.append(f"cannot parse {path.relative_to(root)}: {exc}")
                continue
            project = (
                str(payload.get("project_id") or "root-governance")
                if isinstance(payload, dict)
                else "root-governance"
            )
            documents.append((path, project, payload))
    return documents, errors


def _git(
    root: Path, *args: str, allow_failure: bool = False
) -> subprocess.CompletedProcess[str]:
    process = subprocess.run(
        ["git", "-C", str(root), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if process.returncode != 0 and not allow_failure:
        detail = (
            process.stderr.strip() or process.stdout.strip() or "git command failed"
        )
        raise GovernanceIdError(detail)
    return process


def _baseline_registry(root: Path, base_ref: str) -> dict[str, Any] | None:
    process = _git(
        root,
        "show",
        f"{base_ref}:governance/id_registry.json",
        allow_failure=True,
    )
    if process.returncode != 0:
        return None
    try:
        payload = json.loads(process.stdout)
    except json.JSONDecodeError as exc:
        raise GovernanceIdError(f"baseline ID registry is invalid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise GovernanceIdError("baseline ID registry root must be an object")
    return payload


def _baseline_positional_keys(root: Path, base_ref: str) -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    for project in _project_entries(root):
        for relative in CANONICAL_PROJECT_FILES:
            path = f"{project['path']}/{relative}"
            process = _git(root, "show", f"{base_ref}:{path}", allow_failure=True)
            if process.returncode == 0:
                keys.update(
                    (project["project_id"], value)
                    for value in POSITIONAL_TOKEN_RE.findall(process.stdout)
                )
    process = _git(
        root,
        "grep",
        "-I",
        "-h",
        "-o",
        "-E",
        POSITIONAL_GIT_PATTERN,
        base_ref,
        "--",
        "governance/run_manifests",
        "governance/run_receipts",
        allow_failure=True,
    )
    if process.returncode not in {0, 1}:
        raise GovernanceIdError(
            process.stderr.strip() or "cannot inspect baseline positional IDs"
        )
    keys.update(("run-record", value) for value in process.stdout.splitlines() if value)
    return keys


def _current_positional_keys(references: Iterable[Reference]) -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    for reference in references:
        if reference.kind != "TSK" or not POSITIONAL_TASK_RE.fullmatch(reference.value):
            continue
        scope = (
            "run-record"
            if reference.path.startswith("governance/run_")
            else reference.project
        )
        keys.add((scope, reference.value))
    return keys


def audit_repository(
    *,
    root: Path,
    registry_path: Path,
    base_ref: str | None,
) -> dict[str, Any]:
    root = root.resolve()
    registry = load_registry(registry_path)
    errors = validate_registry(registry)
    documents, document_errors = _metadata_documents(root)
    errors.extend(document_errors)
    references: list[Reference] = []
    for path, project, payload in documents:
        references.extend(
            collect_references(
                payload,
                project=project,
                path=str(path.relative_to(root)),
            )
        )
    reference_errors, counters = audit_references(references, registry)
    errors.extend(reference_errors)

    current_positional = _current_positional_keys(references)
    baseline_positional: set[tuple[str, str]] = set()
    new_positional: set[tuple[str, str]] = set()
    immutability_checked = False
    if base_ref:
        _git(root, "rev-parse", "--verify", f"{base_ref}^{{commit}}")
        baseline = _baseline_registry(root, base_ref)
        if baseline is not None:
            immutability_checked = True
            errors.extend(validate_registry_immutability(registry, baseline))
        baseline_positional = _baseline_positional_keys(root, base_ref)
        new_positional = new_positional_identifiers(
            current_positional, baseline_positional
        )
        for project, identifier in sorted(new_positional):
            errors.append(
                f"new positional Task ID is forbidden in {project}: {identifier}"
            )

    allocations = registry.get("allocations", [])
    task_count = sum(item.get("kind") == "TSK" for item in allocations)
    event_count = sum(item.get("kind") == "EVT" for item in allocations)
    goal_count = sum(item.get("kind") == "PG" for item in allocations)
    summary: dict[str, Any] = {
        "status": "PASS" if not errors else "FAIL",
        "registry_revision": registry.get("registry_revision"),
        "allocations": len(allocations),
        "task_ids": task_count,
        "acceptance_ids": task_count,
        "goal_ids": goal_count,
        "event_ids": event_count,
        "aliases": len(registry.get("aliases", [])),
        "migrated_projects": sorted(registry.get("migrated_projects", [])),
        "metadata_files_scanned": len(documents),
        **counters,
        "identifier_references": counters["v2_references"]
        + counters["legacy_references_observed"],
        "identifier_references_resolved": counters["v2_references_resolved"]
        + counters["legacy_references_resolved"],
        "all_references_exactly_one": (
            counters["v2_references"] + counters["legacy_references_observed"]
            == counters["v2_references_resolved"]
            + counters["legacy_references_resolved"]
        ),
        "all_v2_references_exactly_one": counters["v2_references"]
        == counters["v2_references_resolved"],
        "immutability_checked": immutability_checked,
        "positional_ids_current": len(current_positional),
        "positional_ids_baseline": len(baseline_positional),
        "new_positional_ids": len(new_positional),
        "legacy_policy": "dual-read/project-scoped-alias/no-mass-rewrite",
        "errors": sorted(set(errors)),
    }
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit repository Governance ID V2 metadata."
    )
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--base-ref")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        summary = audit_repository(
            root=args.root,
            registry_path=args.registry,
            base_ref=args.base_ref,
        )
    except GovernanceIdError as exc:
        summary = {"status": "FAIL", "errors": [str(exc)]}
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    else:
        print(
            f"GOVERNANCE_ID_AUDIT={summary['status']} "
            f"tasks={summary.get('task_ids', 0)} "
            f"references={summary.get('v2_references', 0)} "
            f"errors={len(summary.get('errors', []))}"
        )
        for error in summary.get("errors", []):
            print(f"ERROR: {error}")
    return 0 if summary["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
