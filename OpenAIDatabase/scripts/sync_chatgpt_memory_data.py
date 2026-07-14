#!/usr/bin/env python3
"""Sync ChatGPT official exports into the public raw archive.

S04 P1 intentionally keeps the browser connector as a read-only contract. It
never logs in, never captures browser credentials and never mutates ChatGPT
state. The executable path in this phase is the official export fallback.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from privacy_guard import PrivacyViolation, assert_no_credentials
from public_raw_sanitizer import (
    PublicRawLimitError,
    PublicRawSanitizationError,
    merge_counts,
    require_public_raw_file_size,
    sanitize_public_value,
)


SOURCE_ID = "chatgpt"
RAW_ROOT = Path("data/public_raw/chatgpt")
PROCESSED_MANIFEST = Path("data/processed/conversations/conversation_manifest.jsonl")
DERIVED_SUMMARY = Path("data/derived/chatgpt/chatgpt_sync_summary.json")
SYNC_LOG_DIR = Path("data/run_logs/sync_runs")
FORBIDDEN_BROWSER_STATES = {"login_required", "password_required", "verification_required", "captcha_required"}
OFFICIAL_EXPORT_MODE = "official_export_fallback"


class AppendOnlyViolation(ValueError):
    pass


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def iso_from_value(value: Any) -> str:
    if value in (None, ""):
        return ""
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value), tz=timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    text = str(value).strip()
    if not text:
        return ""
    if text.endswith("Z"):
        return text
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return text
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def safe_filename(value: str) -> str:
    text = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    text = text.strip("._-")
    return text or stable_hash(value)[:16]


def write_if_changed(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        current = path.read_text(encoding="utf-8", errors="ignore")
        if current == payload:
            return
        raise AppendOnlyViolation(f"append-only raw target already exists with different content: {path}")
    tmp_path = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        tmp_path.write_text(payload, encoding="utf-8")
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def git_head(database_dir: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=database_dir,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "UNKNOWN_NO_GIT_HEAD"


def build_sync_log_row(
    database_dir: Path,
    generated_at: str,
    summary: dict[str, Any],
    export_sha256: str,
    redact_for_public_backup: bool,
) -> dict[str, Any]:
    head = git_head(database_dir)
    residual_risk = (
        "the authorized private export and omitted credentials remain outside GitHub"
    )
    return {
        "timestamp": generated_at,
        "category": "sync_runs",
        "task_id": "MA-V12-S04P1",
        "run_type": "sync_run",
        "status": "PASS",
        "task": "sync_chatgpt_memory_data",
        "source_id": SOURCE_ID,
        "mode": OFFICIAL_EXPORT_MODE,
        "dry_run": False,
        "conversation_count": summary["conversation_count"],
        "message_count": summary["message_count"],
        "export_sha256": export_sha256,
        "redact_for_public_backup": redact_for_public_backup,
        "redaction_counts": summary["redaction_counts"],
        "updated_targets": ["history", "pattern"],
        "source_files": ["authorized ChatGPT official export snapshot"],
        "output_files": [
            RAW_ROOT.as_posix(),
            PROCESSED_MANIFEST.as_posix(),
            DERIVED_SUMMARY.as_posix(),
        ],
        "context_used": [
            {
                "source": "authorized ChatGPT official export snapshot",
                "reason": "read-only fallback input for sanitized public transcript recovery",
            }
        ],
        "tools_used": [
            {
                "tool": "python",
                "operation": "sync_chatgpt_memory_data",
                "result": "success",
            }
        ],
        "tests_run": [
            {
                "command": "connector runtime does not execute test suites",
                "result": "NOT_RUN",
                "not_run_reason": "tests are executed by the surrounding R7 validation run",
            }
        ],
        "failure_recovery": [],
        "base_commit": head,
        "result_commit": head,
        "residual_risks": [residual_risk],
    }


def write_current_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows)
    tmp_path = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        tmp_path.write_text(payload, encoding="utf-8")
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def extract_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if not isinstance(content, dict):
        return ""
    parts = content.get("parts")
    if isinstance(parts, list):
        return "\n".join(str(part) for part in parts if isinstance(part, (str, int, float)))
    text = content.get("text") or content.get("value")
    return str(text) if text is not None else ""


def normalize_messages(conversation: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    mapping = conversation.get("mapping")
    if isinstance(mapping, dict):
        for node in mapping.values():
            if not isinstance(node, dict):
                continue
            message = node.get("message")
            if not isinstance(message, dict):
                continue
            text = extract_text(message.get("content"))
            if not text.strip():
                continue
            author = message.get("author") if isinstance(message.get("author"), dict) else {}
            rows.append(
                {
                    "message_id": str(message.get("id") or node.get("id") or stable_hash(message)[:16]),
                    "role": str(author.get("role") or "unknown"),
                    "created_at": iso_from_value(message.get("create_time")),
                    "text": text,
                }
            )
        return rows

    messages = conversation.get("messages")
    if isinstance(messages, list):
        for index, message in enumerate(messages):
            if not isinstance(message, dict):
                continue
            text = extract_text(message.get("content") or message.get("text"))
            if not text.strip():
                continue
            rows.append(
                {
                    "message_id": str(message.get("id") or f"message_{index + 1}"),
                    "role": str(message.get("role") or message.get("author") or "unknown"),
                    "created_at": iso_from_value(message.get("created_at") or message.get("create_time")),
                    "text": text,
                }
            )
    return rows


def conversation_payload(conversation: dict[str, Any]) -> dict[str, Any]:
    conversation_id = str(conversation.get("id") or conversation.get("conversation_id") or stable_hash(conversation)[:16])
    title = str(conversation.get("title") or "Untitled ChatGPT conversation")
    messages = normalize_messages(conversation)
    payload = {
        "schema_version": "memory_atlas_public_raw_chatgpt.v1",
        "source_id": SOURCE_ID,
        "conversation_id": conversation_id,
        "title": title,
        "created_at": iso_from_value(conversation.get("create_time") or conversation.get("created_at")),
        "updated_at": iso_from_value(conversation.get("update_time") or conversation.get("updated_at")),
        "message_count": len(messages),
        "messages": messages,
        "credential_boundary": "credentials_not_transcript",
        "sync_mode": OFFICIAL_EXPORT_MODE,
    }
    return payload


def assert_conversation_has_no_credentials(payload: dict[str, Any]) -> None:
    conversation_id = str(payload["conversation_id"])
    assert_no_credentials(str(payload.get("title") or ""), f"{SOURCE_ID}:{conversation_id}:title")
    for message in payload.get("messages") or []:
        assert_no_credentials(
            str(message.get("text") or ""),
            f"{SOURCE_ID}:{conversation_id}:{message.get('message_id')}",
        )


def normalize_conversation(conversation: dict[str, Any]) -> dict[str, Any]:
    payload = conversation_payload(conversation)
    assert_conversation_has_no_credentials(payload)
    return payload


def prepare_public_conversation(
    conversation: dict[str, Any],
    *,
    redact_for_public_backup: bool,
) -> tuple[dict[str, Any], dict[str, int]]:
    payload = conversation_payload(conversation)
    redaction_counts: dict[str, int] = {}
    if redact_for_public_backup:
        sanitized, redaction_counts = sanitize_public_value(payload)
        if not isinstance(sanitized, dict):
            raise PublicRawSanitizationError("sanitized ChatGPT conversation must remain an object")
        payload = sanitized
    else:
        assert_conversation_has_no_credentials(payload)
    payload["redact_for_public_backup"] = redact_for_public_backup
    payload["redaction_counts"] = redaction_counts
    payload["content_sha256"] = stable_hash(payload)
    return payload, redaction_counts


def coerce_conversation_list(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        conversations = payload.get("conversations")
        if isinstance(conversations, list):
            return [item for item in conversations if isinstance(item, dict)]
        if payload.get("mapping") or payload.get("messages"):
            return [payload]
    return []


def load_official_export(path: Path) -> list[dict[str, Any]]:
    if path.is_dir():
        candidates = sorted(path.glob("**/conversations*.json"))
        conversations: list[dict[str, Any]] = []
        for candidate in candidates:
            conversations.extend(coerce_conversation_list(json.loads(candidate.read_text(encoding="utf-8"))))
        return conversations

    if path.suffix.lower() == ".zip":
        conversations = []
        with zipfile.ZipFile(path) as archive:
            names = sorted(
                name for name in archive.namelist()
                if Path(name).name.startswith("conversations") and Path(name).suffix.lower() == ".json"
            )
            for name in names:
                with archive.open(name) as handle:
                    conversations.extend(coerce_conversation_list(json.loads(handle.read().decode("utf-8"))))
        return conversations

    return coerce_conversation_list(json.loads(path.read_text(encoding="utf-8")))


def official_export_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    if path.is_dir():
        candidates = sorted(path.glob("**/conversations*.json"))
        for candidate in candidates:
            relative = candidate.relative_to(path).as_posix().encode("utf-8")
            digest.update(len(relative).to_bytes(8, "big"))
            digest.update(relative)
            with candidate.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
        return digest.hexdigest()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_summary(
    rows: list[dict[str, Any]],
    generated_at: str,
    *,
    export_sha256: str = "",
    redaction_counts: dict[str, int] | None = None,
    redact_for_public_backup: bool = False,
) -> dict[str, Any]:
    return {
        "schema_version": "memory_atlas_chatgpt_sync_summary.v1",
        "source_id": SOURCE_ID,
        "generated_at": generated_at,
        "conversation_count": len(rows),
        "message_count": sum(int(row.get("message_count") or 0) for row in rows),
        "conversation_ids": [row["conversation_id"] for row in rows],
        "mode": OFFICIAL_EXPORT_MODE,
        "credential_boundary": "credentials_not_transcript",
        "export_sha256": export_sha256,
        "redact_for_public_backup": redact_for_public_backup,
        "redaction_counts": redaction_counts or {},
        "processed_manifest": PROCESSED_MANIFEST.as_posix(),
    }


def build_manifest_row(
    row: dict[str, Any],
    raw_path: Path,
    export_sha256: str,
    generated_at: str,
) -> dict[str, Any]:
    roles = [str(message.get("role") or "unknown") for message in row.get("messages") or []]
    return {
        "schema_version": "memory_atlas_conversation_manifest.v2",
        "conversation_id": row["conversation_id"],
        "title": row["title"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "message_count": row["message_count"],
        "user_message_count": roles.count("user"),
        "assistant_message_count": roles.count("assistant"),
        "content_sha256": row["content_sha256"],
        "export_sha256": export_sha256,
        "raw_ref": raw_path.as_posix(),
        "parsed_at": generated_at,
        "redaction_counts": row.get("redaction_counts") or {},
    }


def sync_official_export(
    database_dir: Path,
    export_path: Path,
    dry_run: bool,
    redact_for_public_backup: bool = False,
) -> dict[str, Any]:
    conversations = load_official_export(export_path)
    rows: list[dict[str, Any]] = []
    redaction_counts: dict[str, int] = {}
    for conversation in conversations:
        row, row_counts = prepare_public_conversation(
            conversation,
            redact_for_public_backup=redact_for_public_backup,
        )
        rows.append(row)
        redaction_counts = merge_counts(redaction_counts, row_counts)
    generated_at = now_utc()
    export_sha = official_export_sha256(export_path)
    raw_paths = [
        RAW_ROOT / f"{safe_filename(row['conversation_id'])}.{row['content_sha256'][:12]}.json"
        for row in rows
    ]
    raw_payloads = [json.dumps(row, ensure_ascii=False, indent=2, sort_keys=True) + "\n" for row in rows]
    for relative_path, payload in zip(raw_paths, raw_payloads):
        require_public_raw_file_size(payload, relative_path.as_posix())
    manifest_rows = [
        build_manifest_row(row, relative_path, export_sha, generated_at)
        for row, relative_path in zip(rows, raw_paths)
    ]

    if not dry_run:
        for relative_path, payload in zip(raw_paths, raw_payloads):
            write_if_changed(database_dir / relative_path, payload)
        write_current_jsonl(database_dir / PROCESSED_MANIFEST, manifest_rows)
        summary = build_summary(
            rows,
            generated_at,
            export_sha256=export_sha,
            redaction_counts=redaction_counts,
            redact_for_public_backup=redact_for_public_backup,
        )
        (database_dir / DERIVED_SUMMARY).parent.mkdir(parents=True, exist_ok=True)
        (database_dir / DERIVED_SUMMARY).write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        append_jsonl(
            database_dir / SYNC_LOG_DIR / f"{generated_at[:10]}.jsonl",
            build_sync_log_row(
                database_dir,
                generated_at,
                summary,
                export_sha,
                redact_for_public_backup,
            ),
        )

    return {
        "status": "PASS",
        "source_id": SOURCE_ID,
        "mode": OFFICIAL_EXPORT_MODE,
        "dry_run": dry_run,
        "browser_connector": "readonly_contract",
        "fallback": "official_export",
        "conversation_count": len(rows),
        "message_count": sum(int(row.get("message_count") or 0) for row in rows),
        "raw_paths": [path.as_posix() for path in raw_paths],
        "export_sha256": export_sha,
        "redact_for_public_backup": redact_for_public_backup,
        "redaction_counts": redaction_counts,
        "processed_manifest": PROCESSED_MANIFEST.as_posix(),
        "derived_summary": DERIVED_SUMMARY.as_posix(),
        "run_log_dir": SYNC_LOG_DIR.as_posix(),
        "writes_files": not dry_run,
        "append_only": True,
        "no_browser_mutation": True,
    }


def dry_run_contract(redact_for_public_backup: bool = False) -> dict[str, Any]:
    return {
        "status": "PASS",
        "source_id": SOURCE_ID,
        "mode": "browser_readonly_contract",
        "dry_run": True,
        "browser_connector": "readonly_contract",
        "fallback": "official_export",
        "conversation_count": 0,
        "message_count": 0,
        "writes_files": False,
        "append_only": True,
        "no_browser_mutation": True,
        "input_required_for_apply": True,
        "official_export_fallback": "official export ZIP/conversations.json fallback",
        "redact_for_public_backup": redact_for_public_backup,
        "processed_manifest": PROCESSED_MANIFEST.as_posix(),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Memory Atlas S04 P1 ChatGPT read-only sync.")
    parser.add_argument("--database-dir", type=Path, default=Path("."))
    parser.add_argument("--official-export", type=Path)
    parser.add_argument("--browser-state", choices=["ready", "not_configured", "login_required", "password_required", "verification_required", "captcha_required"], default="not_configured")
    parser.add_argument("--redact-for-public-backup", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.browser_state in FORBIDDEN_BROWSER_STATES:
        print(json.dumps({
            "status": "STOPPED",
            "source_id": SOURCE_ID,
            "reason": "browser_requires_human_authentication",
            "browser_state": args.browser_state,
            "dry_run": args.dry_run,
            "no_browser_mutation": True,
        }, ensure_ascii=False, indent=2, sort_keys=True))
        return 3

    try:
        if args.official_export:
            result = sync_official_export(
                args.database_dir.resolve(),
                args.official_export.resolve(),
                args.dry_run,
                redact_for_public_backup=args.redact_for_public_backup,
            )
        elif args.dry_run:
            result = dry_run_contract(args.redact_for_public_backup)
        else:
            result = {
                "status": "NEEDS_INPUT",
                "source_id": SOURCE_ID,
                "reason": "official_export_required_for_apply",
                "browser_connector": "readonly_contract",
                "fallback": "official_export",
                "no_browser_mutation": True,
            }
            print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
            return 2
    except PrivacyViolation as exc:
        print(json.dumps({
            "status": "FAIL",
            "source_id": SOURCE_ID,
            "reason": "credential_is_not_memory",
            "error": str(exc),
            "no_browser_mutation": True,
        }, ensure_ascii=False, indent=2, sort_keys=True))
        return 4
    except AppendOnlyViolation as exc:
        print(json.dumps({
            "status": "FAIL",
            "source_id": SOURCE_ID,
            "reason": "append_only_violation",
            "error": str(exc),
            "no_browser_mutation": True,
        }, ensure_ascii=False, indent=2, sort_keys=True))
        return 5
    except (PublicRawLimitError, PublicRawSanitizationError) as exc:
        print(json.dumps({
            "status": "FAIL",
            "source_id": SOURCE_ID,
            "reason": "public_raw_sanitization_failed",
            "error": str(exc),
            "no_browser_mutation": True,
        }, ensure_ascii=False, indent=2, sort_keys=True))
        return 6

    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
