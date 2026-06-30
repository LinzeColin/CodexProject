#!/usr/bin/env python3
"""Enforce Task Pack changed-files policy."""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import subprocess
from pathlib import Path


META_RE = re.compile(
    r"<!--\s*AGENT_LOOP_METADATA\s*(.*?)\s*END_AGENT_LOOP_METADATA\s*-->",
    re.DOTALL,
)

SECRET_PATTERNS = [
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\b(?:sk|ghp|github_pat)_[A-Za-z0-9_=-]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"(?i)\b(password|secret|token)\s*[:=]\s*['\"]?[A-Za-z0-9_./+=-]{16,}"),
]

DEPENDENCY_FILES = {
    "package.json",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "pyproject.toml",
    "poetry.lock",
    "requirements.txt",
    "Pipfile",
    "Pipfile.lock",
    "Gemfile",
    "Gemfile.lock",
}


def load_metadata(taskpack: str) -> dict:
    text = Path(taskpack).read_text(encoding="utf-8")
    match = META_RE.search(text)
    if not match:
        raise ValueError("missing metadata wrapper")
    return json.loads(match.group(1))


def path_matches(path: str, pattern: str) -> bool:
    pattern = pattern.strip()
    if pattern.endswith("/**"):
        prefix = pattern[:-3]
        return path == prefix or path.startswith(prefix + "/")
    return fnmatch.fnmatch(path, pattern) or path == pattern


def changed_files(base_ref: str) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{base_ref}...HEAD"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    return sorted(line.strip() for line in result.stdout.splitlines() if line.strip())


def is_allowed(path: str, patterns: list[str]) -> bool:
    return any(path_matches(path, pattern) for pattern in patterns)


def is_forbidden(path: str, patterns: list[str]) -> bool:
    return any(path_matches(path, pattern) for pattern in patterns)


def looks_like_env_or_secret_path(path: str) -> bool:
    name = Path(path).name
    if name == ".env" or name.startswith(".env."):
        return True
    return name.endswith((".pem", ".key", ".p12", ".pfx"))


def is_dependency_file(path: str) -> bool:
    return Path(path).name in DEPENDENCY_FILES


def is_production_deploy_file(path: str) -> bool:
    name = Path(path).name.lower()
    if path.startswith(".github/workflows/") and re.search(r"(deploy|production|release)", name):
        return True
    return "/deploy/" in path.lower() or "/production/" in path.lower()


def file_contains_secret(path: str) -> bool:
    file_path = Path(path)
    if not file_path.exists() or not file_path.is_file():
        return False
    try:
        text = file_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False
    return any(pattern.search(text) for pattern in SECRET_PATTERNS)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--taskpack", required=True)
    parser.add_argument("--base-ref", default="origin/main")
    parser.add_argument("--changed-file", action="append", default=[])
    args = parser.parse_args()

    metadata = load_metadata(args.taskpack)
    allowed_paths = [str(path) for path in metadata.get("allowed_paths", [])]
    forbidden_paths = [str(path) for path in metadata.get("forbidden_paths", [])]
    dependency_authorized = bool(metadata.get("dependency_changes_authorized", False))
    production_authorized = bool(metadata.get("production_deploy", False))

    files = sorted(args.changed_file) if args.changed_file else changed_files(args.base_ref)
    errors: list[str] = []

    for path in files:
        if not is_allowed(path, allowed_paths):
            errors.append(f"changed file outside allowed_paths: {path}")
        if is_forbidden(path, forbidden_paths):
            errors.append(f"changed forbidden path: {path}")
        if looks_like_env_or_secret_path(path):
            errors.append(f"secret/env-like file changed: {path}")
        if is_dependency_file(path) and not dependency_authorized:
            errors.append(f"dependency file changed without authorization: {path}")
        if is_production_deploy_file(path) and not production_authorized:
            errors.append(f"production/deploy file changed without authorization: {path}")
        if file_contains_secret(path):
            errors.append(f"secret-like value detected in changed file: {path}")

    print("CHANGED_FILES=" + json.dumps(files, ensure_ascii=False))
    if errors:
        print("CHANGED_FILES_POLICY=FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("CHANGED_FILES_POLICY=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
