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
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from privacy_guard import PrivacyViolation, assert_no_credentials


SOURCE_ID = "chatgpt"
RAW_ROOT = Path("data/public_raw/chatgpt")
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


def normalize_conversation(conversation: dict[str, Any]) -> dict[str, Any]:
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
    assert_no_credentials(title, f"{SOURCE_ID}:{conversation_id}:title")
    for message in messages:
        assert_no_credentials(str(message.get("text") or ""), f"{SOURCE_ID}:{conversation_id}:{message.get('message_id')}")
    return payload


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


def build_summary(rows: list[dict[str, Any]], generated_at: str) -> dict[str, Any]:
    return {
        "schema_version": "memory_atlas_chatgpt_sync_summary.v1",
        "source_id": SOURCE_ID,
        "generated_at": generated_at,
        "conversation_count": len(rows),
        "message_count": sum(int(row.get("message_count") or 0) for row in rows),
        "conversation_ids": [row["conversation_id"] for row in rows],
        "mode": OFFICIAL_EXPORT_MODE,
        "credential_boundary": "credentials_not_transcript",
    }


def sync_official_export(database_dir: Path, export_path: Path, dry_run: bool) -> dict[str, Any]:
    conversations = load_official_export(export_path)
    rows = [normalize_conversation(conversation) for conversation in conversations]
    generated_at = now_utc()
    raw_paths = [RAW_ROOT / f"{safe_filename(row['conversation_id'])}.json" for row in rows]

    if not dry_run:
        for row, relative_path in zip(rows, raw_paths):
            payload = json.dumps(row, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
            write_if_changed(database_dir / relative_path, payload)
        summary = build_summary(rows, generated_at)
        (database_dir / DERIVED_SUMMARY).parent.mkdir(parents=True, exist_ok=True)
        (database_dir / DERIVED_SUMMARY).write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        append_jsonl(database_dir / SYNC_LOG_DIR / f"{generated_at[:10]}.jsonl", {
            "source_id": SOURCE_ID,
            "status": "PASS",
            "mode": OFFICIAL_EXPORT_MODE,
            "dry_run": False,
            "conversation_count": len(rows),
            "message_count": summary["message_count"],
            "generated_at": generated_at,
        })

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
        "derived_summary": DERIVED_SUMMARY.as_posix(),
        "run_log_dir": SYNC_LOG_DIR.as_posix(),
        "writes_files": not dry_run,
        "append_only": True,
        "no_browser_mutation": True,
    }


def dry_run_contract() -> dict[str, Any]:
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
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Memory Atlas S04 P1 ChatGPT read-only sync.")
    parser.add_argument("--database-dir", type=Path, default=Path("."))
    parser.add_argument("--official-export", type=Path)
    parser.add_argument("--browser-state", choices=["ready", "not_configured", "login_required", "password_required", "verification_required", "captcha_required"], default="not_configured")
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
            result = sync_official_export(args.database_dir.resolve(), args.official_export.resolve(), args.dry_run)
        elif args.dry_run:
            result = dry_run_contract()
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

    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
