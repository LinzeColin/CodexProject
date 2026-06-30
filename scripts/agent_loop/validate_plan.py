#!/usr/bin/env python3
"""Validate Codex plan-first output for Agent Loop."""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import subprocess
from pathlib import Path


BUSINESS_DIRS = [
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
]

META_RE = re.compile(
    r"<!--\s*AGENT_LOOP_METADATA\s*(.*?)\s*END_AGENT_LOOP_METADATA\s*-->",
    re.DOTALL,
)


def load_metadata(taskpack: str) -> dict:
    text = Path(taskpack).read_text(encoding="utf-8")
    match = META_RE.search(text)
    if not match:
        raise ValueError("missing metadata wrapper")
    return json.loads(match.group(1))


def section_body(text: str, headings: list[str]) -> str:
    for heading in headings:
        pattern = re.compile(rf"^##\s+{re.escape(heading)}\s*$", re.I | re.M)
        match = pattern.search(text)
        if match:
            start = match.end()
            next_heading = re.search(r"^##\s+", text[start:], re.M)
            end = start + next_heading.start() if next_heading else len(text)
            return text[start:end].strip()
    return ""


def extract_paths(text: str) -> list[str]:
    paths = set(re.findall(r"`([^`\n]+)`", text))
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith(("-", "*")):
            candidate = stripped[1:].strip().split(":", 1)[0].strip()
            if "/" in candidate or candidate.endswith(".md") or candidate.endswith(".py"):
                paths.add(candidate.strip("`"))
    return sorted(path for path in paths if path and " " not in path)


def path_matches(path: str, pattern: str) -> bool:
    pattern = pattern.strip()
    if pattern.endswith("/**"):
        prefix = pattern[:-3]
        return path == prefix or path.startswith(prefix + "/")
    return fnmatch.fnmatch(path, pattern) or path == pattern


def allowed(path: str, patterns: list[str]) -> bool:
    return any(path_matches(path, pattern) for pattern in patterns)


def git_diff_empty() -> bool:
    result = subprocess.run(["git", "diff", "--quiet"], check=False)
    if result.returncode != 0:
        return False
    staged = subprocess.run(["git", "diff", "--cached", "--quiet"], check=False)
    return staged.returncode == 0


def is_automation_task(metadata: dict) -> bool:
    project = str(metadata.get("project", "")).lower()
    allowed_paths = " ".join(str(path) for path in metadata.get("allowed_paths", []))
    return any(word in project for word in ["agent-loop", "automation", "governance"]) or ".github/workflows" in allowed_paths


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", required=True)
    parser.add_argument("--taskpack", required=True)
    parser.add_argument("--skip-git-diff", action="store_true")
    args = parser.parse_args()

    plan_text = Path(args.plan).read_text(encoding="utf-8")
    metadata = load_metadata(args.taskpack)
    errors: list[str] = []

    lower = plan_text.lower()
    if not re.search(r"no files modified yet\s*:\s*(yes|true)", lower) and "no files modified" not in lower:
        errors.append("plan must explicitly say no files modified yet")
    if not args.skip_git_diff and not git_diff_empty():
        errors.append("git diff is not empty after plan")

    inspected = section_body(plan_text, ["Files Inspected"])
    proposed = section_body(plan_text, ["Proposed Files To Modify", "Files To Modify"])
    validations = section_body(plan_text, ["Validation Commands"])
    rollback = section_body(plan_text, ["Rollback", "Rollback Plan"])
    if not inspected:
        errors.append("files inspected section is missing or empty")
    if not proposed:
        errors.append("proposed files to modify section is missing or empty")
    if not validations:
        errors.append("validation commands section is missing or empty")
    if not rollback:
        errors.append("rollback section is missing or empty")

    proposed_paths = extract_paths(proposed)
    forbidden = [str(path) for path in metadata.get("forbidden_paths", [])]
    allowed_paths = [str(path) for path in metadata.get("allowed_paths", [])]

    for path in proposed_paths:
        if any(path_matches(path, pattern) for pattern in forbidden):
            errors.append(f"proposed forbidden path: {path}")
        if path == "AGENTS.md" and not allowed(path, allowed_paths):
            errors.append("root AGENTS.md proposed without explicit authorization")
        if path.startswith(".github/workflows/") and not is_automation_task(metadata):
            errors.append(f"workflow path proposed outside automation/governance task: {path}")
        for business_dir in BUSINESS_DIRS:
            if path == business_dir or path.startswith(business_dir + "/"):
                if not allowed(path, allowed_paths):
                    errors.append(f"business project path proposed without explicit scope: {path}")

    if metadata.get("risk_tier") == "T2":
        if metadata.get("plan_required") is not True:
            errors.append("T2 metadata must set plan_required true")
        if not section_body(plan_text, ["T2 Plan-First Evidence"]):
            errors.append("T2 plan-first evidence section is missing")

    if errors:
        print("PLAN_VALIDATION=FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PLAN_VALIDATION=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
