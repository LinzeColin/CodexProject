#!/usr/bin/env python3
"""Validate the Agent Loop dual-plane Task Pack contract."""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import sys
from pathlib import Path


META_RE = re.compile(
    r"<!--\s*AGENT_LOOP_METADATA\s*(.*?)\s*END_AGENT_LOOP_METADATA\s*-->",
    re.DOTALL,
)

REQUIRED_KEYS = [
    "agent_loop_version",
    "source",
    "repository",
    "risk_tier",
    "auto_merge",
    "plan_required",
    "production_deploy",
    "project",
    "roadmap_task_id",
    "acceptance_id",
    "allowed_paths",
    "forbidden_paths",
    "validation_commands",
    "max_autofix_loops",
]

REQUIRED_SECTIONS = [
    "Human Summary",
    "Background",
    "Scope",
    "Files To Inspect",
    "Files Allowed To Modify",
    "Files Forbidden",
    "Implementation Requirements",
    "Acceptance Criteria",
    "Validation Tests",
    "Stop Conditions",
    "Review Requirements",
    "Rollback Plan",
    "Required Codex Result Pack",
]

SECRET_PATTERNS = [
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\b(?:sk|ghp|github_pat)_[A-Za-z0-9_=-]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"(?i)\b(password|secret|token)\s*[:=]\s*['\"]?[A-Za-z0-9_./+=-]{16,}"),
]


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def load_taskpack(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def extract_metadata(text: str) -> tuple[dict | None, list[str]]:
    errors: list[str] = []
    match = META_RE.search(text)
    if not match:
        return None, ["metadata wrapper missing"]
    raw = match.group(1).strip()
    try:
        metadata = json.loads(raw)
    except json.JSONDecodeError as exc:
        return None, [f"metadata JSON parse failed: {exc}"]
    if not isinstance(metadata, dict):
        return None, ["metadata must be a JSON object"]
    return metadata, errors


def section_body(text: str, heading: str) -> str:
    pattern = re.compile(rf"^##\s+{re.escape(heading)}\s*$", re.I | re.M)
    match = pattern.search(text)
    if not match:
        return ""
    start = match.end()
    next_heading = re.search(r"^##\s+", text[start:], re.M)
    end = start + next_heading.start() if next_heading else len(text)
    return text[start:end].strip()


def has_section(text: str, heading: str) -> bool:
    return bool(re.search(rf"^##\s+{re.escape(heading)}\s*$", text, re.I | re.M))


def list_value(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def is_ambiguous_project(value: object) -> bool:
    if not isinstance(value, str):
        return True
    project = value.strip()
    if not project:
        return True
    lowered = project.lower()
    placeholders = {
        "project",
        "unknown",
        "tbd",
        "todo",
        "multiple",
        "ambiguous",
        "project_or_governance_domain",
        "project-or-governance-domain",
    }
    if lowered in placeholders:
        return True
    if "," in project or re.search(r"\s+(or|and)\s+", lowered):
        return True
    return False


def contains_secret(text: str) -> bool:
    return any(pattern.search(text) for pattern in SECRET_PATTERNS)


def path_matches(path: str, pattern: str) -> bool:
    pattern = pattern.strip()
    if pattern.endswith("/**"):
        prefix = pattern[:-3]
        return path == prefix or path.startswith(prefix + "/")
    return fnmatch.fnmatch(path, pattern) or path == pattern


def validate(text: str, allow_production: bool = False) -> tuple[dict | None, list[str]]:
    errors: list[str] = []
    metadata, metadata_errors = extract_metadata(text)
    errors.extend(metadata_errors)
    if metadata is None:
        return None, errors

    for key in REQUIRED_KEYS:
        if key not in metadata:
            fail(errors, f"missing metadata key: {key}")

    if metadata.get("source") != "chatgpt-approved":
        fail(errors, "source must be chatgpt-approved")
    if metadata.get("repository") != "LinzeColin/CodexProject":
        fail(errors, "repository must be LinzeColin/CodexProject")
    if is_ambiguous_project(metadata.get("project")):
        fail(errors, "project must be present and unambiguous")
    if metadata.get("risk_tier") not in {"T1", "T2"}:
        fail(errors, "risk_tier must be T1 or T2")
    if metadata.get("auto_merge") is not True:
        fail(errors, "auto_merge must be true")
    if metadata.get("risk_tier") == "T2" and metadata.get("plan_required") is not True:
        fail(errors, "T2 must set plan_required true")
    if metadata.get("production_deploy") is not False and not allow_production:
        fail(errors, "production_deploy must remain false for this workflow")

    allowed = list_value(metadata.get("allowed_paths"))
    forbidden = list_value(metadata.get("forbidden_paths"))
    validations = list_value(metadata.get("validation_commands"))
    if not allowed:
        fail(errors, "allowed_paths must be a non-empty list")
    if not forbidden:
        fail(errors, "forbidden_paths must be a non-empty list")
    if any(path_matches(path, pattern) for path in allowed for pattern in forbidden):
        fail(errors, "allowed_paths and forbidden_paths overlap")
    if not isinstance(metadata.get("max_autofix_loops"), int) or metadata.get("max_autofix_loops", -1) < 0:
        fail(errors, "max_autofix_loops must be a non-negative integer")

    for section in REQUIRED_SECTIONS:
        if not has_section(text, section):
            fail(errors, f"missing Markdown section: {section}")
        elif not section_body(text, section):
            fail(errors, f"empty Markdown section: {section}")

    if not section_body(text, "Acceptance Criteria"):
        fail(errors, "acceptance criteria must exist")
    validation_body = section_body(text, "Validation Tests")
    if not validations and not re.search(r"(?i)\bN/A\b|not applicable|no runnable validation", validation_body):
        fail(errors, "validation tests must exist or include explicit N/A reason")
    if not section_body(text, "Stop Conditions"):
        fail(errors, "stop conditions must exist")
    if contains_secret(text):
        fail(errors, "obvious secret-like value detected")

    return metadata, errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--taskpack", required=True)
    parser.add_argument("--metadata-out")
    parser.add_argument("--allow-production", action="store_true")
    args = parser.parse_args()

    text = load_taskpack(args.taskpack)
    metadata, errors = validate(text, allow_production=args.allow_production)
    if args.metadata_out and metadata is not None:
        Path(args.metadata_out).write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    if errors:
        print("TASKPACK_VALIDATION=FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("TASKPACK_VALIDATION=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
