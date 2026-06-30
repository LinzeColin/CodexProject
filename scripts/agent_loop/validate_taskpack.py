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

SECTION_ALIASES = {
    "human_summary": [
        "Human Summary",
        "人类摘要",
        "摘要",
        "任务摘要",
    ],
    "background": [
        "Background",
        "背景",
        "上下文",
    ],
    "scope": [
        "Scope",
        "范围",
        "任务范围",
    ],
    "files_to_inspect": [
        "Files To Inspect",
        "Files to Read",
        "允许读取的文件",
        "需要读取的文件",
        "读取范围",
    ],
    "files_allowed_to_modify": [
        "Files Allowed To Modify",
        "Allowed Files",
        "允许修改的文件",
        "可修改文件",
    ],
    "files_forbidden": [
        "Files Forbidden",
        "Forbidden Files",
        "禁止修改的文件",
        "禁止文件",
    ],
    "implementation_requirements": [
        "Implementation Requirements",
        "Requirements",
        "实现要求",
        "需求要求",
    ],
    "acceptance_criteria": [
        "Acceptance Criteria",
        "验收标准",
        "验收条件",
    ],
    "validation_tests": [
        "Validation Tests",
        "Validation Commands",
        "验证测试",
        "测试命令",
    ],
    "stop_conditions": [
        "Stop Conditions",
        "停止条件",
        "阻断条件",
    ],
    "review_requirements": [
        "Review Requirements",
        "复审要求",
        "审查要求",
    ],
    "rollback_plan": [
        "Rollback Plan",
        "回滚方案",
        "回滚计划",
    ],
    "required_codex_result_pack": [
        "Required Codex Result Pack",
        "Codex Result Pack",
        "Required Final Response",
        "Required Codex Final Response",
        "Codex 最终结果包",
    ],
}

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


def normalize_heading(title: str) -> str:
    title = title.strip()
    title = re.sub(r"\s+#+\s*$", "", title)
    title = re.sub(r"^\d+\s*[\.\)\-:：、]\s*", "", title)
    return title.strip().casefold()


def iter_level_two_headings(text: str) -> list[tuple[int, int, str]]:
    headings: list[tuple[int, int, str]] = []
    for match in re.finditer(r"^##\s+(.+?)\s*$", text, re.M):
        headings.append((match.start(), match.end(), match.group(1).strip()))
    return headings


def find_section_body(text: str, aliases: list[str]) -> str:
    accepted = {normalize_heading(alias) for alias in aliases}
    headings = iter_level_two_headings(text)
    for index, (_, end, title) in enumerate(headings):
        if normalize_heading(title) not in accepted:
            continue
        next_start = headings[index + 1][0] if index + 1 < len(headings) else len(text)
        return text[end:next_start].strip()
    return ""


def section_body(text: str, canonical_key: str) -> str:
    return find_section_body(text, SECTION_ALIASES[canonical_key])


def has_section(text: str, canonical_key: str) -> bool:
    accepted = {normalize_heading(alias) for alias in SECTION_ALIASES[canonical_key]}
    return any(normalize_heading(title) in accepted for _, _, title in iter_level_two_headings(text))


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

    for canonical_key in SECTION_ALIASES:
        if not has_section(text, canonical_key):
            fail(errors, f"missing Markdown section: {canonical_key}")
        elif not section_body(text, canonical_key):
            fail(errors, f"empty Markdown section: {canonical_key}")

    if not section_body(text, "acceptance_criteria"):
        fail(errors, "acceptance criteria must exist")
    validation_body = section_body(text, "validation_tests")
    if not validations and not re.search(r"(?i)\bN/A\b|not applicable|no runnable validation", validation_body):
        fail(errors, "validation tests must exist or include explicit N/A reason")
    if not section_body(text, "stop_conditions"):
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
