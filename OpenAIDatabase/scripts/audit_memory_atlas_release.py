#!/usr/bin/env python3
"""Audit the Memory Atlas static release before local install or Pages deploy."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
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
PUBLIC_RAW_PREFIX = "data/public_raw/"
PUBLIC_RAW_IGNORED_NAMES = {".DS_Store", ".gitkeep", "README.md"}
RAW_MANIFEST_DIR = Path("机器治理/证据与日志/raw_archive_manifests")
FAILED_SESSION_HISTORY_PART_COUNT = "0"
FAILED_SESSION_HISTORY_RISK_SCAN = "SENSITIVE_SCAN_BLOCKED"


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


def forbidden_name_pattern(relative: str, allow_public_raw_sessions: bool = False) -> re.Pattern[str] | None:
    for pattern in FORBIDDEN_NAME_PATTERNS:
        if (
            allow_public_raw_sessions
            and relative.startswith(PUBLIC_RAW_PREFIX)
            and pattern.pattern == r"sessions?"
        ):
            continue
        if pattern.search(relative):
            return pattern
    return None


def is_failed_zero_part_session_history_manifest(path: Path) -> bool:
    if path.name != "MANIFEST.txt":
        return False
    try:
        fields = dict(
            line.split("=", 1)
            for line in path.read_text(encoding="utf-8").splitlines()
            if "=" in line
        )
    except OSError:
        return False
    return (
        fields.get("part_count") == FAILED_SESSION_HISTORY_PART_COUNT
        and fields.get("risk_scan") == FAILED_SESSION_HISTORY_RISK_SCAN
    )


def _run_json_audit(command: list[str]) -> dict[str, Any]:
    try:
        completed = subprocess.run(command, text=True, capture_output=True, check=False)
        payload = json.loads(completed.stdout)
    except (OSError, json.JSONDecodeError) as exc:
        return {"status": "FAIL", "reason": f"audit command failed: {type(exc).__name__}"}
    if not isinstance(payload, dict):
        return {"status": "FAIL", "reason": "audit command returned a non-object result"}
    return payload


def audit_governed_public_raw(repo_root: Path) -> tuple[dict[str, Any], list[str]]:
    raw_root = repo_root / "data/public_raw"
    raw_files = (
        sorted(
            path
            for path in raw_root.rglob("*")
            if path.is_file()
            and path.name not in PUBLIC_RAW_IGNORED_NAMES
            and not any(part.startswith(".") for part in path.relative_to(raw_root).parts)
        )
        if raw_root.exists()
        else []
    )
    if not raw_files:
        return {"status": "NOT_APPLICABLE", "file_count": 0}, []

    scripts_dir = Path(__file__).resolve().parent
    content_audit = _run_json_audit(
        [
            sys.executable,
            str(scripts_dir / "audit_memory_atlas_public_raw.py"),
            "--database-dir",
            str(repo_root),
        ]
    )
    append_only_audit = _run_json_audit(
        [
            sys.executable,
            str(scripts_dir / "raw_archive_manifest.py"),
            "audit",
            "--database-dir",
            str(repo_root),
        ]
    )

    problems: list[str] = []
    if content_audit.get("status") != "PASS":
        problems.append("public raw content audit failed")
    if append_only_audit.get("status") != "PASS":
        problems.append("public raw append-only audit failed")
    if int(append_only_audit.get("new_raw_file_count", -1)) != 0:
        problems.append("public raw contains files missing from the hash ledger")
    if int(append_only_audit.get("current_raw_file_count", -1)) != len(raw_files):
        problems.append("public raw inventory count does not match the append-only audit")
    if int(append_only_audit.get("ledger_entry_count", -1)) != len(raw_files):
        problems.append("public raw hash ledger is not an exact current inventory")

    ledger_path = repo_root / RAW_MANIFEST_DIR / "raw_hash_ledger.jsonl"
    manifest_paths = sorted((repo_root / RAW_MANIFEST_DIR).glob("raw_manifest.*.jsonl"))
    matching_manifest = None
    if ledger_path.is_file():
        ledger_payload = ledger_path.read_bytes()
        matching_manifest = next(
            (path for path in manifest_paths if path.read_bytes() == ledger_payload),
            None,
        )
    if matching_manifest is None:
        problems.append("public raw has no immutable manifest matching the hash ledger")

    result = {
        "status": "PASS" if not problems else "FAIL",
        "file_count": len(raw_files),
        "content_audit": content_audit,
        "append_only_audit": append_only_audit,
        "matching_manifest": (
            matching_manifest.relative_to(repo_root).as_posix() if matching_manifest else None
        ),
    }
    return result, problems


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
        if forbidden_name_pattern(relative):
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

    # A rejected publish artifact cannot become safer by scanning the source tree.
    if problems:
        raise AuditError("\n".join(problems))

    tracked_problems = audit_tracked_files(repo_root)
    problems.extend(tracked_problems)
    public_raw_audit, public_raw_problems = audit_governed_public_raw(repo_root)
    problems.extend(public_raw_problems)

    if problems:
        raise AuditError("\n".join(problems))

    return {
        "status": "PASS",
        "publish_dir": str(publish_dir),
        "file_count": len(files),
        "atlas": str(atlas_path),
        "public_raw": public_raw_audit,
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
        if is_allowed_managed_session_history_file(line):
            if is_failed_zero_part_session_history_manifest(repo_root / line):
                problems.append(f"failed zero-part session history metadata: {line}")
            continue
        if line in ALLOWED_TRACKED_FILES:
            continue
        if forbidden_name_pattern(line, allow_public_raw_sessions=True):
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
        if is_allowed_managed_session_history_file(relative):
            if is_failed_zero_part_session_history_manifest(path):
                problems.append(f"failed zero-part session history metadata: {relative}")
            continue
        if relative in ALLOWED_TRACKED_FILES:
            continue
        if forbidden_name_pattern(relative, allow_public_raw_sessions=True):
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
