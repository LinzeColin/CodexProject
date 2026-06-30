#!/usr/bin/env python3
"""Audit the Memory Atlas static release before local install or Pages deploy."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any


ALLOWED_PUBLISH_SUFFIXES = {".html", ".css", ".js", ".json", ".svg", ".png", ".ico", ".txt", ".webmanifest"}
FORBIDDEN_PUBLISH_SUFFIXES = {".zip", ".sqlite", ".db", ".jsonl", ".md", ".pem", ".key", ".env", ".csv"}
FORBIDDEN_NAME_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"OpenAI-export\.zip",
        r"chatgpt_memory_vault",
        r"\.local_keys",
        r"\.env(?:\.|$)",
        r"cookies?",
        r"sessions?",
        r"auth\.json",
    ]
]
FORBIDDEN_TEXT_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"PRIVATE CORE DETAIL",
        r"SECRET DETAIL",
        r"sk-[A-Za-z0-9_-]{20,}",
        r"-----BEGIN (?:RSA |EC |OPENSSH |PRIVATE )?PRIVATE KEY-----",
        r"/Users/[A-Za-z0-9_.-]+/",
        r"OpenAI-export\.zip",
        r"chatgpt_memory_vault",
        r"\.local_keys",
    ]
]
FORBIDDEN_JSON_KEYS = {
    "evidence",
    "source_ref",
    "conversation_ref",
    "source_file",
    "record_hash",
    "source_snapshot_hash",
    "record_index",
    "json_pointer",
    "database_dir",
    "local_path",
    "absolute_path",
}
ALLOWED_TRACKED_FILES = {
    "data/processed/codex/codex_session_manifest.jsonl",
    "data/processed/codex/codex_daily_activity.jsonl",
    "data/processed/codex/codex_activity_snapshot.json",
    "data/derived/codex/codex_agent_recommendations.json",
    "data/derived/codex/codex_behavior_report.md",
}
SOURCE_SCAN_EXCLUDED_DIRS = {".git", ".local_keys", "node_modules", "dist", "__pycache__", ".pytest_cache", ".mypy_cache"}


class AuditError(RuntimeError):
    pass


def is_allowed_managed_session_history_file(relative: str) -> bool:
    """Allow explicit history archives without allowing live Codex state paths."""
    if not (relative == "session_history/README.md" or relative.startswith("session_history/")):
        return False
    relative_path = Path(relative)
    lower = relative.lower()
    if any(part.lower() in {".codex", "sessions", ".local_keys"} for part in relative_path.parts):
        return False
    if any(marker in lower for marker in ["openai-export.zip", "chatgpt_memory_vault", "cookie", "auth.json", ".env"]):
        return False
    if relative_path.suffix.lower() in {".app", ".key", ".pem", ".env"}:
        return False
    return True


def audit_release(repo_root: Path, publish_dir: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    publish_dir = publish_dir.resolve()
    if not publish_dir.exists():
        raise AuditError(f"publish directory does not exist: {publish_dir}")
    if not publish_dir.is_dir():
        raise AuditError(f"publish path is not a directory: {publish_dir}")

    files = [path for path in publish_dir.rglob("*") if path.is_file()]
    if not files:
        raise AuditError(f"publish directory is empty: {publish_dir}")

    problems: list[str] = []
    for path in files:
        relative = path.relative_to(publish_dir).as_posix()
        suffix = path.suffix.lower()
        if suffix in FORBIDDEN_PUBLISH_SUFFIXES:
            problems.append(f"forbidden publish suffix: {relative}")
        if suffix and suffix not in ALLOWED_PUBLISH_SUFFIXES:
            problems.append(f"unexpected publish suffix: {relative}")
        if any(pattern.search(relative) for pattern in FORBIDDEN_NAME_PATTERNS):
            problems.append(f"forbidden publish filename: {relative}")

        if suffix in {".html", ".css", ".js", ".json", ".svg", ".txt", ".webmanifest"}:
            text = path.read_text(encoding="utf-8", errors="replace")
            for pattern in FORBIDDEN_TEXT_PATTERNS:
                if pattern.search(text):
                    problems.append(f"forbidden text pattern {pattern.pattern!r}: {relative}")

    atlas_path = publish_dir / "memory_atlas.json"
    if not atlas_path.exists():
        problems.append("missing memory_atlas.json in publish directory")
    else:
        audit_memory_atlas_json(atlas_path, problems)

    tracked_problems = audit_tracked_files(repo_root)
    problems.extend(tracked_problems)

    if problems:
        raise AuditError("\n".join(problems))

    return {
        "status": "PASS",
        "publish_dir": str(publish_dir),
        "file_count": len(files),
        "atlas": str(atlas_path),
    }


def audit_memory_atlas_json(atlas_path: Path, problems: list[str]) -> None:
    try:
        payload = json.loads(atlas_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        problems.append(f"memory_atlas.json is invalid JSON: {exc}")
        return

    if payload.get("schema_version") != "memory_atlas.v1":
        problems.append("memory_atlas.json schema_version is not memory_atlas.v1")

    source_contract = payload.get("source_contract")
    if not isinstance(source_contract, dict):
        problems.append("memory_atlas.json missing source_contract")
        return

    if source_contract.get("mode") != "public_redacted_read_only_visualization":
        problems.append("source_contract.mode is not public_redacted_read_only_visualization")

    writeback_policy = source_contract.get("writeback_policy")
    if not isinstance(writeback_policy, dict):
        problems.append("missing writeback_policy")
    else:
        if writeback_policy.get("frontend_can_request_writeback") is not True:
            problems.append("writeback_policy.frontend_can_request_writeback must be true")
        if writeback_policy.get("writeback_must_use_proposals") is not True:
            problems.append("writeback_policy.writeback_must_use_proposals must be true")
        if writeback_policy.get("direct_frontend_mutation_of_active_memory") is not False:
            problems.append("writeback_policy.direct_frontend_mutation_of_active_memory must be false")

    scan_json(payload, "$", problems)


def scan_json(value: Any, path: str, problems: list[str]) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in FORBIDDEN_JSON_KEYS:
                problems.append(f"forbidden JSON key {key!r} at {path}")
            scan_json(nested, f"{path}.{key}", problems)
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            scan_json(nested, f"{path}[{index}]", problems)
    elif isinstance(value, str):
        for pattern in FORBIDDEN_TEXT_PATTERNS:
            if pattern.search(value):
                problems.append(f"forbidden JSON text pattern {pattern.pattern!r} at {path}")


def audit_tracked_files(repo_root: Path) -> list[str]:
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            cwd=str(repo_root),
            check=True,
            text=True,
            capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        if (repo_root / "memory_atlas_source_workspace.json").exists():
            return audit_source_workspace_files(repo_root)
        return [f"unable to inspect tracked files: {exc}"]

    problems: list[str] = []
    for line in result.stdout.splitlines():
        if line in ALLOWED_TRACKED_FILES or is_allowed_managed_session_history_file(line):
            continue
        if any(pattern.search(line) for pattern in FORBIDDEN_NAME_PATTERNS):
            problems.append(f"forbidden tracked filename: {line}")
        suffix = Path(line).suffix.lower()
        if suffix in {".app", ".key", ".pem", ".env"}:
            problems.append(f"forbidden tracked suffix: {line}")
    return problems


def audit_source_workspace_files(repo_root: Path) -> list[str]:
    problems: list[str] = []
    for path in repo_root.rglob("*"):
        if not path.is_file():
            continue
        relative_path = path.relative_to(repo_root)
        relative = relative_path.as_posix()
        if any(part in SOURCE_SCAN_EXCLUDED_DIRS for part in relative_path.parts):
            continue
        if relative in ALLOWED_TRACKED_FILES or is_allowed_managed_session_history_file(relative):
            continue
        if any(pattern.search(relative) for pattern in FORBIDDEN_NAME_PATTERNS):
            problems.append(f"forbidden source workspace filename: {relative}")
        suffix = path.suffix.lower()
        if suffix in {".app", ".key", ".pem", ".env"}:
            problems.append(f"forbidden source workspace suffix: {relative}")
    return problems


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit Memory Atlas static release output.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--publish-dir", type=Path, default=Path(__file__).resolve().parents[1] / "apps/memory-atlas/dist")
    return parser.parse_args()


def main(argv: list[str] | None = None) -> int:
    args = parse_args() if argv is None else parse_args_from(argv)
    try:
        result = audit_release(args.repo_root, args.publish_dir)
    except AuditError as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def parse_args_from(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit Memory Atlas static release output.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--publish-dir", type=Path, default=Path(__file__).resolve().parents[1] / "apps/memory-atlas/dist")
    return parser.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(main())
