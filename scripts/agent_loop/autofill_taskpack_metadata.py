#!/usr/bin/env python3
"""Autofill safe Agent Loop Task Pack routing metadata."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import route_taskpack


META_RE = re.compile(
    r"<!--\s*AGENT_LOOP_METADATA\s*(.*?)\s*END_AGENT_LOOP_METADATA\s*-->",
    re.DOTALL,
)


def read_text(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8")


def extract_metadata(text: str) -> tuple[dict[str, Any] | None, str | None]:
    match = META_RE.search(text)
    if not match:
        return None, "metadata wrapper missing"
    try:
        metadata = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        return None, f"metadata JSON parse failed: {exc}"
    if not isinstance(metadata, dict):
        return None, "metadata must be a JSON object"
    return metadata, None


def list_value(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def ordered_unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def missing_or_ambiguous_project(metadata: dict[str, Any]) -> bool:
    return metadata.get("project") is None or route_taskpack.ambiguous_project(metadata.get("project"))


def replace_metadata(text: str, metadata: dict[str, Any]) -> str:
    normalized = json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True)
    replacement = f"<!-- AGENT_LOOP_METADATA\n{normalized}\nEND_AGENT_LOOP_METADATA -->"
    return META_RE.sub(lambda _: replacement, text, count=1)


def write_report(path: str | None, report: dict[str, Any]) -> None:
    if path:
        Path(path).write_text(
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


def blocked(reason: str, report_path: str | None, routing: dict[str, Any] | None = None) -> int:
    report = {
        "status": "BLOCKED",
        "reason": reason,
        "routing": routing or {},
    }
    write_report(report_path, report)
    print("AUTOFILL_STATUS=BLOCKED")
    print("ROUTING_STATUS=" + str((routing or {}).get("status", "BLOCKED")))
    print("AUTOFILL_REASON=" + reason)
    if routing:
        print(json.dumps(routing, ensure_ascii=False, indent=2, sort_keys=True))
    return 2


def main() -> int:
    parser = argparse.ArgumentParser(description="Autofill safe Task Pack routing metadata.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--matrix", default=str(route_taskpack.default_matrix_path()))
    parser.add_argument("--report")
    args = parser.parse_args()

    text = read_text(args.input)
    metadata, metadata_error = extract_metadata(text)
    if metadata_error or metadata is None:
        return blocked(str(metadata_error), args.report)

    matrix = route_taskpack.load_matrix(args.matrix)
    routing = route_taskpack.route_taskpack_text(text, matrix)
    if routing["status"] != "READY":
        return blocked(str(routing.get("reason") or "routing did not resolve"), args.report, routing)

    route = routing.get("route") or {}
    autofilled: list[str] = []
    normalized = dict(metadata)

    if missing_or_ambiguous_project(normalized):
        normalized["project"] = routing["project"]
        autofilled.append("project")

    if not list_value(normalized.get("allowed_paths")):
        normalized["allowed_paths"] = list_value(route.get("default_allowed_paths"))
        autofilled.append("allowed_paths")

    existing_forbidden = list_value(normalized.get("forbidden_paths"))
    route_forbidden = list_value(route.get("default_forbidden_paths"))
    merged_forbidden = ordered_unique(existing_forbidden + route_forbidden)
    if merged_forbidden != existing_forbidden:
        normalized["forbidden_paths"] = merged_forbidden
        autofilled.append("forbidden_paths")

    if not list_value(normalized.get("validation_commands")):
        route_commands = list_value(route.get("validation_commands"))
        if not route_commands:
            reason = "validation_commands missing and routing matrix has no runnable default command"
            return blocked(reason, args.report, routing)
        normalized["validation_commands"] = route_commands
        autofilled.append("validation_commands")

    output_text = replace_metadata(text, normalized)
    Path(args.output).write_text(output_text, encoding="utf-8")
    report = {
        "status": "PASS",
        "routing": routing,
        "autofilled_fields": autofilled,
        "output": args.output,
    }
    write_report(args.report, report)
    print("AUTOFILL_STATUS=PASS")
    print("ROUTING_STATUS=READY")
    print(f"PROJECT={routing['project']}")
    print("AUTOFILLED_FIELDS=" + ",".join(autofilled))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
