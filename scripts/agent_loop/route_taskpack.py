#!/usr/bin/env python3
"""Route an Agent Loop Task Pack to one project domain.

The routing matrix in docs/governance/agent_loop/PROJECT_ROUTING_MATRIX.md is
the source of truth. This script never silently guesses: it either returns one
route, blocks with candidates, or asks for a split.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


META_RE = re.compile(
    r"<!--\s*AGENT_LOOP_METADATA\s*(.*?)\s*END_AGENT_LOOP_METADATA\s*-->",
    re.DOTALL,
)

MATRIX_RE = re.compile(
    r"<!--\s*AGENT_LOOP_ROUTING_MATRIX_JSON\s*(.*?)\s*END_AGENT_LOOP_ROUTING_MATRIX_JSON\s*-->",
    re.DOTALL,
)

BUSINESS_PROJECTS = {
    "Alpha",
    "EEI",
    "FIFA",
    "KMFA",
    "MetaDatabase",
    "OpenAIDatabase",
    "OpMe_System",
    "PFI",
    "QBVS",
    "Serenity-Alipay",
    "arxiv-daily-push",
    "whkmSalary",
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_matrix_path() -> Path:
    return repo_root() / "docs" / "governance" / "agent_loop" / "PROJECT_ROUTING_MATRIX.md"


def read_text(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8")


def load_matrix(path: str | Path) -> dict[str, Any]:
    text = read_text(path)
    match = MATRIX_RE.search(text)
    if not match:
        raise ValueError("routing matrix JSON block missing")
    matrix = json.loads(match.group(1))
    routes = matrix.get("routes")
    if not isinstance(routes, list) or not routes:
        raise ValueError("routing matrix routes must be a non-empty list")
    return matrix


def extract_metadata(text: str) -> tuple[dict[str, Any], str | None]:
    match = META_RE.search(text)
    if not match:
        return {}, "metadata wrapper missing"
    try:
        metadata = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        return {}, f"metadata JSON parse failed: {exc}"
    if not isinstance(metadata, dict):
        return {}, "metadata must be a JSON object"
    return metadata, None


def normalize(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value).lower())


def route_aliases(route: dict[str, Any]) -> set[str]:
    values = {str(route.get("project", ""))}
    values.update(str(item) for item in route.get("aliases", []) if str(item).strip())
    return {normalize(value) for value in values if normalize(value)}


def route_map(matrix: dict[str, Any]) -> dict[str, dict[str, Any]]:
    mapping: dict[str, dict[str, Any]] = {}
    for route in matrix["routes"]:
        for alias in route_aliases(route):
            mapping[alias] = route
    return mapping


def list_value(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def ambiguous_project(value: object) -> bool:
    if not isinstance(value, str):
        return True
    project = value.strip()
    if not project:
        return True
    lowered = project.lower()
    if lowered in {"project", "unknown", "tbd", "todo", "multiple", "ambiguous"}:
        return True
    if "," in project or "/" in project or re.search(r"\s+(and|or)\s+", lowered):
        return True
    return False


def explicit_project_route(metadata: dict[str, Any], matrix: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    project = metadata.get("project")
    if project is None or ambiguous_project(project):
        return None, None
    route = route_map(matrix).get(normalize(project))
    if route is None:
        return None, f"project not found in routing matrix: {project}"
    return route, None


def path_prefix(pattern: str) -> str:
    if pattern.endswith("/**"):
        return pattern[:-3]
    if pattern.endswith("/*"):
        return pattern[:-2]
    return pattern


def allowed_path_candidates(metadata: dict[str, Any], matrix: dict[str, Any]) -> set[str]:
    allowed = list_value(metadata.get("allowed_paths"))
    candidates: set[str] = set()
    for route in matrix["routes"]:
        project = str(route["project"])
        for route_pattern in route.get("default_allowed_paths", []):
            prefix = path_prefix(str(route_pattern)).lower()
            for item in allowed:
                lowered = item.lower()
                if prefix and (lowered == prefix or lowered.startswith(prefix.rstrip("*") + "/") or prefix.startswith(lowered.rstrip("*"))):
                    candidates.add(project)
    return candidates


def strip_metadata_and_forbidden(text: str) -> str:
    text = META_RE.sub("", text)
    pattern = re.compile(r"^##\s+Files Forbidden\s*$", re.I | re.M)
    match = pattern.search(text)
    if not match:
        return text
    start = match.end()
    next_heading = re.search(r"^##\s+", text[start:], re.M)
    end = start + next_heading.start() if next_heading else len(text)
    return text[:start] + "\n" + text[end:]


def human_candidates(text: str, matrix: dict[str, Any]) -> list[dict[str, Any]]:
    body = strip_metadata_and_forbidden(text)
    lowered = body.lower()
    scored: list[dict[str, Any]] = []
    for route in matrix["routes"]:
        project = str(route["project"])
        score = 0
        evidence: list[str] = []
        names = [project, *[str(item) for item in route.get("aliases", [])]]
        for pattern in route.get("default_allowed_paths", []):
            prefix = path_prefix(str(pattern))
            if prefix and re.search(rf"(^|[`'\"(/\s]){re.escape(prefix)}(/|\*\*|[`'\")\s]|$)", body, re.I):
                score += 4
                evidence.append(f"path:{prefix}")
        for name in names:
            if not name:
                continue
            if re.search(rf"\bproject\b[^\n]{{0,80}}\b{re.escape(name)}\b", lowered, re.I):
                score += 3
                evidence.append(f"project-field:{name}")
            elif re.search(rf"\b{re.escape(name.lower())}\b", lowered):
                score += 1
                evidence.append(f"mention:{name}")
        if score:
            scored.append({"project": project, "score": score, "evidence": sorted(set(evidence))})
    return sorted(scored, key=lambda item: (-int(item["score"]), str(item["project"])))


def missing_metadata_fields(metadata: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    if metadata.get("project") is None or ambiguous_project(metadata.get("project")):
        missing.append("project")
    if not list_value(metadata.get("allowed_paths")):
        missing.append("allowed_paths")
    if not list_value(metadata.get("forbidden_paths")):
        missing.append("forbidden_paths")
    if not list_value(metadata.get("validation_commands")):
        missing.append("validation_commands")
    return missing


def route_taskpack_text(text: str, matrix: dict[str, Any]) -> dict[str, Any]:
    metadata, metadata_error = extract_metadata(text)
    if metadata_error:
        return {
            "status": "BLOCKED",
            "reason": metadata_error,
            "project": None,
            "route": None,
            "candidates": [],
            "missing_metadata_fields": [],
        }

    explicit_route, explicit_error = explicit_project_route(metadata, matrix)
    allowed_candidates = allowed_path_candidates(metadata, matrix)
    human = human_candidates(text, matrix)
    missing = missing_metadata_fields(metadata)

    if explicit_error:
        return {
            "status": "BLOCKED",
            "reason": explicit_error,
            "project": None,
            "route": None,
            "candidates": human,
            "missing_metadata_fields": missing,
        }

    if explicit_route is not None:
        explicit_project = str(explicit_route["project"])
        business_allowed = {project for project in allowed_candidates if project in BUSINESS_PROJECTS}
        if len(business_allowed) > 1:
            return {
                "status": "SPLIT_REQUIRED",
                "reason": "allowed_paths point to multiple business projects",
                "project": None,
                "route": None,
                "candidates": sorted(
                    ({"project": project, "score": 5, "evidence": ["allowed_paths"]} for project in business_allowed),
                    key=lambda item: item["project"],
                ),
                "missing_metadata_fields": missing,
            }
        return {
            "status": "READY",
            "reason": "explicit metadata project matched routing matrix",
            "project": explicit_project,
            "route": explicit_route,
            "candidates": [{"project": explicit_project, "score": 10, "evidence": ["metadata.project"]}],
            "missing_metadata_fields": missing,
        }

    if len(allowed_candidates) == 1:
        project = next(iter(allowed_candidates))
        route = route_map(matrix)[normalize(project)]
        return {
            "status": "READY",
            "reason": "allowed_paths matched exactly one routing matrix project",
            "project": project,
            "route": route,
            "candidates": [{"project": project, "score": 8, "evidence": ["allowed_paths"]}],
            "missing_metadata_fields": missing,
        }
    if len(allowed_candidates) > 1:
        return {
            "status": "SPLIT_REQUIRED",
            "reason": "allowed_paths matched multiple projects",
            "project": None,
            "route": None,
            "candidates": sorted(
                ({"project": project, "score": 5, "evidence": ["allowed_paths"]} for project in allowed_candidates),
                key=lambda item: item["project"],
            ),
            "missing_metadata_fields": missing,
        }

    strong_human = [item for item in human if int(item["score"]) >= 4]
    if len(strong_human) == 1:
        project = str(strong_human[0]["project"])
        route = route_map(matrix)[normalize(project)]
        return {
            "status": "READY",
            "reason": "human plane strongly matched one project",
            "project": project,
            "route": route,
            "candidates": strong_human,
            "missing_metadata_fields": missing,
        }
    if len(strong_human) > 1:
        return {
            "status": "SPLIT_REQUIRED",
            "reason": "human plane strongly matched multiple projects",
            "project": None,
            "route": None,
            "candidates": strong_human,
            "missing_metadata_fields": missing,
        }

    return {
        "status": "BLOCKED",
        "reason": "project routing is ambiguous",
        "project": None,
        "route": None,
        "candidates": human[:5],
        "missing_metadata_fields": missing,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Route an Agent Loop Task Pack.")
    parser.add_argument("--taskpack", required=True)
    parser.add_argument("--matrix", default=str(default_matrix_path()))
    parser.add_argument("--output-json")
    args = parser.parse_args()

    text = read_text(args.taskpack)
    matrix = load_matrix(args.matrix)
    result = route_taskpack_text(text, matrix)
    output = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)
    if args.output_json:
        Path(args.output_json).write_text(output + "\n", encoding="utf-8")
    print(f"ROUTING_STATUS={result['status']}")
    if result.get("project"):
        print(f"PROJECT={result['project']}")
    if result.get("reason"):
        print(f"ROUTING_REASON={result['reason']}")
    print(output)
    return 0 if result["status"] == "READY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
