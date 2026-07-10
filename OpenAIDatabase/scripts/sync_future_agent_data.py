#!/usr/bin/env python3
"""Minimal future-agent adapter for Memory Atlas S04 P2.

The adapter is intentionally small: it accepts a human-provided local JSON file
for a future agent source, blocks credential-like content, then writes public
raw records plus a derived summary and run log. It never connects to external
services or generates fake data when input is missing.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from privacy_guard import PrivacyViolation, assert_no_credentials
from public_raw_sanitizer import (
    PublicRawLimitError,
    PublicRawSanitizationError,
    merge_counts,
    require_public_raw_file_size,
    sanitize_public_value,
)


SOURCE_ID = "future-agent"
ADAPTER_MODE = "minimal_adapter"
RAW_ROOT = Path("data/public_raw/agents")
DERIVED_ROOT = Path("data/derived/agents")
SYNC_LOG_DIR = Path("data/run_logs/sync_runs")


class AppendOnlyViolation(ValueError):
    pass


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def safe_name(value: str) -> str:
    text = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    text = text.strip("._-")
    return text or stable_hash(value)[:16]


def write_if_changed(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        current = path.read_text(encoding="utf-8", errors="ignore")
        if current == payload:
            return
        raise AppendOnlyViolation(f"append-only public raw target already exists with different content: {path}")
    tmp_path = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        tmp_path.write_text(payload, encoding="utf-8")
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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
    safe_agent: str,
    summary: dict[str, Any],
    source_sha256: str,
) -> dict[str, Any]:
    head = git_head(database_dir)
    residual_risk = (
        "the authorized private agent source and omitted credentials remain outside GitHub"
    )
    return {
        "timestamp": generated_at,
        "category": "sync_runs",
        "task_id": "MA-V12-S04P2",
        "run_type": "sync_run",
        "status": "PASS",
        "task": "sync_future_agent_data",
        "source_id": SOURCE_ID,
        "agent_id": safe_agent,
        "adapter_mode": ADAPTER_MODE,
        "dry_run": False,
        "event_count": summary["event_count"],
        "message_count": summary["message_count"],
        "source_formats": summary["source_formats"],
        "redaction_counts": summary["redaction_counts"],
        "source_sha256": source_sha256,
        "updated_targets": ["history", "pattern"],
        "source_files": ["authorized future-agent report snapshot"],
        "output_files": [
            (RAW_ROOT / safe_agent).as_posix(),
            (DERIVED_ROOT / safe_agent / "agent_sync_summary.json").as_posix(),
        ],
        "context_used": [
            {
                "source": "authorized future-agent report snapshot",
                "reason": "minimal adapter input for sanitized public transcript recovery",
            }
        ],
        "tools_used": [
            {
                "tool": "python",
                "operation": "sync_future_agent_data",
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


def load_input(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        events = payload.get("events")
        if isinstance(events, list):
            return [item for item in events if isinstance(item, dict)]
        return [payload]
    return []


def message_text(message: Any) -> str:
    if isinstance(message, str):
        return message
    if not isinstance(message, dict):
        return ""
    text = message.get("text") or message.get("content") or ""
    return str(text)


def normalize_event(agent_id: str, event: dict[str, Any]) -> dict[str, Any]:
    event_id = str(event.get("event_id") or event.get("id") or stable_hash(event)[:16])
    title = str(event.get("title") or "Untitled future agent event")
    messages = []
    for index, message in enumerate(event.get("messages") or []):
        if not isinstance(message, (dict, str)):
            continue
        text = message_text(message)
        if not text.strip():
            continue
        role = str(message.get("role") if isinstance(message, dict) else "unknown")
        assert_no_credentials(text, f"{SOURCE_ID}:{agent_id}:{event_id}:message_{index + 1}")
        messages.append({
            "message_id": str(message.get("id") if isinstance(message, dict) else f"message_{index + 1}"),
            "role": role or "unknown",
            "text": text,
        })
    assert_no_credentials(title, f"{SOURCE_ID}:{agent_id}:{event_id}:title")
    row = {
        "schema_version": "memory_atlas_public_raw_future_agent.v1",
        "source_id": SOURCE_ID,
        "agent_id": agent_id,
        "adapter_mode": ADAPTER_MODE,
        "event_id": event_id,
        "title": title,
        "message_count": len(messages),
        "messages": messages,
        "credential_boundary": "credentials_not_transcript",
        "sync_mode": "manual_import",
        "source_format": "json_event",
        "redaction_counts": {},
    }
    row["content_sha256"] = stable_hash(row)
    return row


def markdown_title(text: str) -> str:
    for line in text.splitlines():
        candidate = line.strip()
        if candidate.startswith("#"):
            title = candidate.lstrip("#").strip()
            if title:
                return title
        if candidate:
            return candidate[:160]
    return "Untitled future agent Markdown report"


def normalize_markdown_event(agent_id: str, event_id: str, text: str) -> dict[str, Any]:
    if not text.strip():
        raise PublicRawSanitizationError("Markdown report must not be empty")
    row: dict[str, Any] = {
        "schema_version": "memory_atlas_public_raw_future_agent.v1",
        "source_id": SOURCE_ID,
        "agent_id": agent_id,
        "adapter_mode": ADAPTER_MODE,
        "event_id": event_id,
        "title": markdown_title(text),
        "message_count": 1,
        "messages": [
            {
                "message_id": f"{event_id}-report",
                "role": "assistant",
                "text": text,
            }
        ],
        "credential_boundary": "credentials_not_transcript",
        "sync_mode": "manual_markdown_import",
        "source_format": "markdown_report",
    }
    sanitized, redaction_counts = sanitize_public_value(row)
    if not isinstance(sanitized, dict):
        raise PublicRawSanitizationError("sanitized Markdown event must remain an object")
    sanitized["redaction_counts"] = redaction_counts
    sanitized["content_sha256"] = stable_hash(sanitized)
    return sanitized


def build_summary(agent_id: str, rows: list[dict[str, Any]], generated_at: str) -> dict[str, Any]:
    redaction_counts: dict[str, int] = {}
    for row in rows:
        redaction_counts = merge_counts(redaction_counts, row.get("redaction_counts") or {})
    return {
        "schema_version": "memory_atlas_future_agent_sync_summary.v1",
        "source_id": SOURCE_ID,
        "agent_id": agent_id,
        "adapter_mode": ADAPTER_MODE,
        "generated_at": generated_at,
        "event_count": len(rows),
        "message_count": sum(int(row.get("message_count") or 0) for row in rows),
        "event_ids": [row["event_id"] for row in rows],
        "credential_boundary": "credentials_not_transcript",
        "source_formats": sorted({str(row.get("source_format") or "json_event") for row in rows}),
        "redaction_counts": redaction_counts,
    }


def dry_run_contract(agent_id: str) -> dict[str, Any]:
    safe_agent = safe_name(agent_id)
    return {
        "status": "PASS",
        "source_id": SOURCE_ID,
        "agent_id": safe_agent,
        "adapter_mode": ADAPTER_MODE,
        "dry_run": True,
        "writes_files": False,
        "raw_root": f"data/public_raw/agents/{safe_agent}",
        "derived_summary": f"data/derived/agents/{safe_agent}/agent_sync_summary.json",
        "run_log_dir": SYNC_LOG_DIR.as_posix(),
        "input_required_for_apply": True,
        "append_only": True,
    }


def sync_rows(
    database_dir: Path,
    safe_agent: str,
    rows: list[dict[str, Any]],
    dry_run: bool,
    *,
    source_sha256: str = "",
) -> dict[str, Any]:
    generated_at = now_utc()
    raw_paths = [
        RAW_ROOT / safe_agent / f"{safe_name(row['event_id'])}.{row['content_sha256'][:12]}.json"
        for row in rows
    ]
    raw_payloads = [json.dumps(row, ensure_ascii=False, indent=2, sort_keys=True) + "\n" for row in rows]
    for relative_path, payload in zip(raw_paths, raw_payloads):
        require_public_raw_file_size(payload, relative_path.as_posix())
    summary = build_summary(safe_agent, rows, generated_at)

    if not dry_run:
        for relative_path, payload in zip(raw_paths, raw_payloads):
            write_if_changed(database_dir / relative_path, payload)
        summary_path = database_dir / DERIVED_ROOT / safe_agent / "agent_sync_summary.json"
        write_json(summary_path, summary)
        append_jsonl(
            database_dir / SYNC_LOG_DIR / f"{generated_at[:10]}.jsonl",
            build_sync_log_row(
                database_dir,
                generated_at,
                safe_agent,
                summary,
                source_sha256,
            ),
        )

    result = {
        "status": "PASS",
        "source_id": SOURCE_ID,
        "agent_id": safe_agent,
        "adapter_mode": ADAPTER_MODE,
        "dry_run": dry_run,
        "writes_files": not dry_run,
        "raw_root": (RAW_ROOT / safe_agent).as_posix(),
        "raw_paths": [path.as_posix() for path in raw_paths],
        "derived_summary": (DERIVED_ROOT / safe_agent / "agent_sync_summary.json").as_posix(),
        "run_log_dir": SYNC_LOG_DIR.as_posix(),
        "event_count": len(rows),
        "message_count": summary["message_count"],
        "append_only": True,
        "source_formats": summary["source_formats"],
        "redaction_counts": summary["redaction_counts"],
        "source_sha256": source_sha256,
    }
    if len(rows) == 1:
        result["event_id"] = rows[0]["event_id"]
        result["source_format"] = rows[0].get("source_format") or "json_event"
    return result


def sync_future_agent(database_dir: Path, agent_id: str, input_path: Path, dry_run: bool) -> dict[str, Any]:
    safe_agent = safe_name(agent_id)
    rows = [normalize_event(safe_agent, event) for event in load_input(input_path)]
    return sync_rows(database_dir, safe_agent, rows, dry_run)


def sync_markdown_report(
    database_dir: Path,
    agent_id: str,
    markdown_report: Path,
    event_id: str,
    dry_run: bool,
) -> dict[str, Any]:
    safe_agent = safe_name(agent_id)
    safe_event = safe_name(event_id)
    source_bytes = markdown_report.read_bytes()
    text = source_bytes.decode("utf-8", errors="replace")
    row = normalize_markdown_event(safe_agent, safe_event, text)
    return sync_rows(
        database_dir,
        safe_agent,
        [row],
        dry_run,
        source_sha256=hashlib.sha256(source_bytes).hexdigest(),
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Memory Atlas S04 P2 future-agent minimal adapter.")
    parser.add_argument("--database-dir", type=Path, default=Path("."))
    parser.add_argument("--agent-id", default="future-agent")
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--input", type=Path)
    source.add_argument("--markdown-report", type=Path)
    parser.add_argument("--event-id")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    database_dir = args.database_dir.resolve()
    try:
        if args.markdown_report:
            event_id = args.event_id or args.markdown_report.stem
            result = sync_markdown_report(
                database_dir,
                args.agent_id,
                args.markdown_report.resolve(),
                event_id,
                args.dry_run,
            )
        elif args.input:
            result = sync_future_agent(database_dir, args.agent_id, args.input.resolve(), args.dry_run)
        elif args.dry_run:
            result = dry_run_contract(args.agent_id)
        else:
            result = {
                "status": "NEEDS_INPUT",
                "source_id": SOURCE_ID,
                "agent_id": safe_name(args.agent_id),
                "reason": "future_agent_input_required_for_apply",
                "adapter_mode": ADAPTER_MODE,
                "writes_files": False,
            }
            print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
            return 2
    except PrivacyViolation as exc:
        print(json.dumps({
            "status": "FAIL",
            "source_id": SOURCE_ID,
            "reason": "credential_is_not_memory",
            "error": str(exc),
            "writes_files": False,
        }, ensure_ascii=False, indent=2, sort_keys=True))
        return 4
    except AppendOnlyViolation as exc:
        print(json.dumps({
            "status": "FAIL",
            "source_id": SOURCE_ID,
            "reason": "append_only_violation",
            "error": str(exc),
            "writes_files": False,
        }, ensure_ascii=False, indent=2, sort_keys=True))
        return 5
    except (PublicRawLimitError, PublicRawSanitizationError) as exc:
        print(json.dumps({
            "status": "FAIL",
            "source_id": SOURCE_ID,
            "reason": "public_raw_sanitization_failed",
            "error": str(exc),
            "writes_files": False,
        }, ensure_ascii=False, indent=2, sort_keys=True))
        return 6

    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
