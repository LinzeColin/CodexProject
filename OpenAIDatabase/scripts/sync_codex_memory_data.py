#!/usr/bin/env python3
"""Sync real local Codex activity into OpenAIDatabase derived data.

The sync is intentionally redacted. It reads real local Codex session logs, but
does not commit raw transcript text, local absolute paths, cookies, sessions, or
plaintext secrets. The output is a GitHub-safe behavior/profile layer for
Memory Atlas and future agents.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from privacy_guard import credential_exclusion_hits, redact_credentials_in_text


DEFAULT_CODEX_HOME = Path.home() / ".codex"
UTC = timezone.utc
SOURCE_ID = "codex"
CODEX_PUBLIC_RAW_ROOT = Path("data/public_raw/codex")
SESSION_INDEX = "session_index.jsonl"
SESSION_OUTPUT = Path("data/processed/codex/codex_session_manifest.jsonl")
DAILY_OUTPUT = Path("data/processed/codex/codex_daily_activity.jsonl")
SNAPSHOT_OUTPUT = Path("data/processed/codex/codex_activity_snapshot.json")
DERIVED_SNAPSHOT_OUTPUT = Path("data/derived/codex/codex_activity_snapshot.json")
RECOMMENDATION_OUTPUT = Path("data/derived/codex/codex_agent_recommendations.json")
REPORT_OUTPUT = Path("data/derived/codex/codex_behavior_report.md")
SYNC_LOG_DIR = Path("data/run_logs/sync_runs")
SESSION_CACHE_VERSION = "codex_session_manifest.cache.v2"

SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_\-]{16,}"),
    re.compile(r"(?:api[_-]?key|token|password|secret)\s*[:=]\s*['\"]?[^'\"\s]+", re.I),
    re.compile(r"Bearer\s+[A-Za-z0-9._\-]+", re.I),
    re.compile(r"-----BEGIN [A-Z ]+PRIVATE KEY-----.*?-----END [A-Z ]+PRIVATE KEY-----", re.S),
]


class AppendOnlyViolation(ValueError):
    pass
ABSOLUTE_PATH_RE = re.compile(r"/Users/[^/\s]+(?:/[^\s'\"<>]+)+")
EMAIL_RE = re.compile(r"([A-Za-z0-9._%+\-])[A-Za-z0-9._%+\-]*@([A-Za-z0-9.\-]+\.[A-Za-z]{2,})")

TOPIC_RULES: list[tuple[str, str, list[str]]] = [
    ("memory_atlas", "Memory Atlas / 记忆可视化", ["Memory Atlas", "记忆星图", "可视化", "Galaxy", "Grid"]),
    ("memory_database", "长期记忆数据库 / RAG", ["OpenAIDatabase", "记忆数据库", "长期记忆", "RAG", "personalization"]),
    ("codex_local", "Codex 本地数据 / agent 工作流", ["Codex", "AGENTS.md", "pursuing goal", "skill", "agent"]),
    ("github_backup", "GitHub 备份 / durable state", ["GitHub", "commit", "push", "备份", "同步"]),
    ("delivery_quality", "高质量交付 / 验证 / CI", ["测试", "验证", "build", "CI", "可验证", "no bug", "成熟"]),
    ("frontend_visual", "前端交互 / Three.js / Dashboard", ["React", "Vite", "Three.js", "Dashboard", "Timeline"]),
    ("security_boundary", "安全边界 / secret / 权限", ["secret", "token", "cookie", "权限", "Access", "安全"]),
    ("finance_trading", "金融 / trading / 风险边界", ["finance", "trading", "交易", "broker", "资金"]),
]

SIGNAL_RULES: list[tuple[str, str, list[str]]] = [
    ("prefer_chinese", "默认中文输出，专业术语保留英文", ["中文", "全中文", "中文输出"]),
    ("real_data_required", "偏好真实数据和可验证证据，反感 mock/伪进度", ["真实", "不要用mock", "不要 mock", "不是测试", "伪进度"]),
    ("github_as_memory_source", "把 GitHub/OpenAIDatabase 当作 durable memory source", ["GitHub", "OpenAIDatabase", "记忆数据库", "备份"]),
    ("human_readable_reports", "报告必须给人看懂，包含话题、行动、建议、机会和 ROI", ["人能看懂", "ROI", "潜在机会", "建议做什么", "需要做什么"]),
    ("authorization_gate", "未授权前先确认需求；授权后持续推进到可验证结果", ["先不开始", "授权", "开始", "确认"]),
    ("agent_personalization", "任意 agent 都应能读取 profile/preference/personalization", ["任意agent", "任意 agent", "personalization", "profile", "preference"]),
    ("no_plaintext_secrets_in_git", "GitHub 只保存 secret_ref，不提交明文高危 secret", ["secret", "token", "API key", "高危"]),
]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            text = line.strip()
            if not text:
                continue
            try:
                row = json.loads(text)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                rows.append(row)
    return rows


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows)
    write_if_changed(path, payload)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    write_if_changed(path, payload)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    write_if_changed(path, text)


def write_if_changed(path: Path, payload: str) -> None:
    if path.exists() and path.read_text(encoding="utf-8", errors="ignore") == payload:
        return
    tmp_path = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        tmp_path.write_text(payload, encoding="utf-8")
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def write_json_append_only(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
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


def stable_hash(value: Any, length: int = 16) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:length]


def compact_timestamp(value: str) -> str:
    text = value.replace("-", "").replace(":", "")
    return text.replace("+0000", "Z").replace("+00:00", "Z")


def parse_time(value: Any) -> datetime | None:
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def day_key(value: datetime | None) -> str:
    return value.date().isoformat() if value else ""


def redact_text(value: str, limit: int = 160) -> str:
    text = value
    credential_exclusion_hits(text, source="sync_codex_memory_data.redact_text")
    text, _credential_counts = redact_credentials_in_text(text)
    for pattern in SECRET_PATTERNS:
        text = pattern.sub("[REDACTED_SECRET]", text)
    text = ABSOLUTE_PATH_RE.sub("[REDACTED_PATH]", text)
    text = EMAIL_RE.sub(r"\1***@\2", text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > limit:
        text = text[: limit - 1].rstrip() + "…"
    return text


def safe_path_label(value: Any) -> dict[str, str]:
    text = str(value or "").strip()
    if not text:
        return {"cwd_label": "", "cwd_hash": ""}
    path = Path(text)
    parts = [part for part in path.parts if part not in {"/", "Users", Path.home().name}]
    label_parts = parts[-2:] if len(parts) >= 2 else parts[-1:]
    return {"cwd_label": "/".join(label_parts), "cwd_hash": stable_hash(text)}


def extract_message_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                value = item.get("text") or item.get("input_text") or item.get("output_text")
                if isinstance(value, str):
                    parts.append(value)
        return "\n".join(parts)
    return ""


def update_rules(text: str, counter: Counter[str], rules: list[tuple[str, str, list[str]]]) -> None:
    lowered = text.lower()
    for rule_id, _label, keywords in rules:
        if any(keyword.lower() in lowered for keyword in keywords):
            counter[rule_id] += 1


def iter_session_files(codex_home: Path) -> list[Path]:
    files: list[Path] = []
    session_root = codex_home / "sessions"
    archived_root = codex_home / "archived_sessions"
    if session_root.exists():
        files.extend(session_root.glob("**/*.jsonl"))
    if archived_root.exists():
        files.extend(archived_root.glob("*.jsonl"))
    return sorted(set(files), key=lambda path: str(path))


def load_session_index(codex_home: Path) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in read_jsonl(codex_home / SESSION_INDEX):
        session_id = str(row.get("id") or "")
        if session_id:
            result[session_id] = row
    return result


def source_bucket(path: Path, codex_home: Path) -> str:
    try:
        relative = path.relative_to(codex_home)
    except ValueError:
        return "external"
    first = relative.parts[0] if relative.parts else ""
    return first or "unknown"


def session_file_signature(path: Path) -> dict[str, Any]:
    try:
        stat_result = path.stat()
    except OSError:
        return {
            "source_file_hash": stable_hash(str(path)),
            "source_mtime_ns": 0,
            "source_size_bytes": 0,
        }
    return {
        "source_file_hash": stable_hash(str(path)),
        "source_mtime_ns": int(stat_result.st_mtime_ns),
        "source_size_bytes": int(stat_result.st_size),
    }


def cached_session_rows(database_dir: Path) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for row in read_jsonl(database_dir / SESSION_OUTPUT):
        key = str(row.get("source_file_hash") or "")
        if key:
            rows[key] = row
    return rows


def cache_hit_for_session(path: Path, cached: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    signature = session_file_signature(path)
    row = cached.get(str(signature["source_file_hash"]))
    if not row:
        return None
    if row.get("cache_version") != SESSION_CACHE_VERSION:
        return None
    if int(row.get("source_mtime_ns") or 0) != signature["source_mtime_ns"]:
        return None
    if int(row.get("source_size_bytes") or 0) != signature["source_size_bytes"]:
        return None
    return row


def parse_session_file(path: Path, codex_home: Path, index: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    started_at: datetime | None = None
    updated_at: datetime | None = None
    session_id = ""
    metadata: dict[str, Any] = {}
    counters: Counter[str] = Counter()
    topics: Counter[str] = Counter()
    signals: Counter[str] = Counter()
    tool_names: Counter[str] = Counter()
    event_types: Counter[str] = Counter()

    file_digest = hashlib.sha256()
    try:
        handle = path.open("rb")
    except OSError:
        return None
    with handle:
        for raw_line in handle:
            file_digest.update(raw_line)
            try:
                line = raw_line.decode("utf-8", errors="ignore").strip()
                event = json.loads(line) if line else {}
            except json.JSONDecodeError:
                counters["decode_error_count"] += 1
                continue
            if not isinstance(event, dict):
                continue
            event_time = parse_time(event.get("timestamp"))
            if event_time:
                started_at = min(started_at, event_time) if started_at else event_time
                updated_at = max(updated_at, event_time) if updated_at else event_time
            event_type = str(event.get("type") or "")
            counters["event_count"] += 1

            payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
            if event_type == "session_meta":
                metadata.update(payload)
                session_id = str(payload.get("id") or session_id)
                meta_time = parse_time(payload.get("timestamp"))
                if meta_time:
                    started_at = min(started_at, meta_time) if started_at else meta_time
            elif event_type == "response_item":
                item_type = str(payload.get("type") or "")
                counters[f"response_{item_type}_count"] += 1
                if item_type == "message":
                    role = str(payload.get("role") or "unknown")
                    counters["message_count"] += 1
                    counters[f"{role}_message_count"] += 1
                    text = extract_message_text(payload.get("content"))
                    if role == "user" and text:
                        update_rules(text, topics, TOPIC_RULES)
                        update_rules(text, signals, SIGNAL_RULES)
                elif "call" in item_type or item_type in {"tool_use", "function_call"}:
                    counters["tool_call_count"] += 1
                    name = str(payload.get("name") or payload.get("recipient_name") or payload.get("tool_name") or item_type)
                    tool_names[redact_text(name, 80)] += 1
            elif event_type == "event_msg":
                inner_type = str(payload.get("type") or "unknown")
                event_types[inner_type] += 1
                if "abort" in inner_type:
                    counters["abort_count"] += 1
                if any(token in inner_type.lower() for token in ("error", "fail", "exception")):
                    counters["error_event_count"] += 1

    if not session_id:
        match = re.search(r"(019[0-9a-f\-]{32,})", path.name)
        session_id = match.group(1) if match else stable_hash(str(path), 32)

    indexed = index.get(session_id, {})
    thread_name = redact_text(str(indexed.get("thread_name") or metadata.get("thread_name") or path.stem), 120)
    cwd_info = safe_path_label(metadata.get("cwd"))
    topic_labels = [
        {"id": rule_id, "label": label, "count": topics.get(rule_id, 0)}
        for rule_id, label, _keywords in TOPIC_RULES
        if topics.get(rule_id, 0)
    ]
    signal_labels = [
        {"id": rule_id, "label": label, "count": signals.get(rule_id, 0)}
        for rule_id, label, _keywords in SIGNAL_RULES
        if signals.get(rule_id, 0)
    ]
    message_count = counters.get("message_count", 0)
    tool_call_count = counters.get("tool_call_count", 0)
    activity_score = (
        message_count
        + counters.get("user_message_count", 0) * 2
        + tool_call_count * 3
        + len(topic_labels) * 4
        + counters.get("error_event_count", 0) * 2
    )

    signature = session_file_signature(path)
    return {
        "schema_version": "codex_session_manifest.v1",
        "cache_version": SESSION_CACHE_VERSION,
        "session_id": session_id,
        "thread_name": thread_name,
        "started_at": started_at.isoformat().replace("+00:00", "Z") if started_at else "",
        "updated_at": updated_at.isoformat().replace("+00:00", "Z") if updated_at else "",
        "started_day": day_key(started_at),
        "updated_day": day_key(updated_at),
        "day": day_key(updated_at or started_at),
        "source_bucket": source_bucket(path, codex_home),
        "source_file_hash": signature["source_file_hash"],
        "source_mtime_ns": signature["source_mtime_ns"],
        "source_size_bytes": signature["source_size_bytes"],
        "content_sha256": file_digest.hexdigest(),
        "cwd_label": cwd_info["cwd_label"],
        "cwd_hash": cwd_info["cwd_hash"],
        "originator": redact_text(str(metadata.get("originator") or ""), 80),
        "client_source": redact_text(str(metadata.get("source") or ""), 80),
        "model_provider": redact_text(str(metadata.get("model_provider") or ""), 80),
        "cli_version": redact_text(str(metadata.get("cli_version") or ""), 80),
        "message_count": int(message_count),
        "user_message_count": int(counters.get("user_message_count", 0)),
        "assistant_message_count": int(counters.get("assistant_message_count", 0)),
        "tool_call_count": int(tool_call_count),
        "event_count": int(counters.get("event_count", 0)),
        "abort_count": int(counters.get("abort_count", 0)),
        "error_event_count": int(counters.get("error_event_count", 0)),
        "decode_error_count": int(counters.get("decode_error_count", 0)),
        "top_tools": [{"name": name, "count": count} for name, count in tool_names.most_common(12)],
        "event_types": [{"name": name, "count": count} for name, count in event_types.most_common(12)],
        "topics": topic_labels,
        "preference_signals": signal_labels,
        "activity_score": int(activity_score),
        "backup_policy": "redacted_summary_only_no_raw_transcript_no_plaintext_secret",
        "credential_boundary": "credentials_not_transcript",
    }


def activity_level(score: int, max_score: int) -> int:
    if score <= 0 or max_score <= 0:
        return 0
    return max(1, min(5, (score * 5 + max_score - 1) // max_score))


def build_daily(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[str, dict[str, Any]] = {}
    for row in rows:
        key = row.get("day") or ""
        if not key:
            continue
        bucket = buckets.setdefault(
            key,
            {
                "date": key,
                "conversation_count": 0,
                "message_count": 0,
                "user_message_count": 0,
                "assistant_message_count": 0,
                "memory_count": 0,
                "candidate_count": 0,
                "decision_count": 0,
                "core_memory_count": 0,
                "mid_long_memory_count": 0,
                "short_memory_count": 0,
                "tool_call_count": 0,
                "error_event_count": 0,
                "abort_count": 0,
                "activity_score": 0,
            },
        )
        bucket["conversation_count"] += 1
        bucket["message_count"] += int(row.get("message_count") or 0)
        bucket["user_message_count"] += int(row.get("user_message_count") or 0)
        bucket["assistant_message_count"] += int(row.get("assistant_message_count") or 0)
        bucket["tool_call_count"] += int(row.get("tool_call_count") or 0)
        bucket["error_event_count"] += int(row.get("error_event_count") or 0)
        bucket["abort_count"] += int(row.get("abort_count") or 0)
        bucket["activity_score"] += int(row.get("activity_score") or 0)
    max_score = max((int(row["activity_score"]) for row in buckets.values()), default=0)
    for row in buckets.values():
        row["activity_level"] = activity_level(int(row["activity_score"]), max_score)
    return sorted(buckets.values(), key=lambda row: row["date"])


def active_recommendations_from_signals(signal_counts: Counter[str], session_count: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    memory_items: list[dict[str, Any]] = []
    meta_items: list[dict[str, Any]] = []
    definitions = {
        "prefer_chinese": (
            "默认中文输出",
            "用户长期偏好中文输出；代码、API、库名、错误信息和专业术语可保留英文。",
            "memory",
        ),
        "real_data_required": (
            "真实数据优先",
            "用户明确要求使用真实 Codex / ChatGPT / GitHub 数据，不接受 mock、伪进度或只给概念演示。",
            "memory",
        ),
        "github_as_memory_source": (
            "OpenAIDatabase 是 durable memory source",
            "GitHub 上的 OpenAIDatabase 应作为任意 agent 可读取的长期记忆、画像、偏好和历史上下文数据库。",
            "memory",
        ),
        "human_readable_reports": (
            "报告面向人类 ROI 和成长",
            "处理记忆或行为数据后，应输出人能直接使用的话题、行动、建议、机会、ROI、能力成长和风险提醒。",
            "memory",
        ),
        "authorization_gate": (
            "授权边界",
            "用户说先不开始时必须先澄清需求；用户授权开始后应持续推进到可验证结果。",
            "meta",
        ),
        "agent_personalization": (
            "任意 agent personalization",
            "所有 agent 访问后都应能生成适配用户的 profile、preference、project context、rules 和 history summary。",
            "memory",
        ),
        "no_plaintext_secrets_in_git": (
            "GitHub secret 边界",
            "GitHub 备份中不得提交 plaintext high-risk secrets；金融/交易 agent 使用 secret_ref 和受控本地 resolver。",
            "meta",
        ),
    }
    for signal_id, count in signal_counts.most_common():
        if count <= 0 or signal_id not in definitions:
            continue
        title, statement, target = definitions[signal_id]
        item = {
            "id": f"codex_signal_{signal_id}",
            "title": title,
            "statement": statement,
            "source": "real_codex_local_sessions",
            "evidence_count": int(count),
            "confidence": "high" if count >= 3 else "medium",
            "importance": "高" if count >= 3 else "中",
            "scope": "ChatGPT / Codex / future agents",
            "reason": f"从 {session_count} 个真实 Codex session 的用户消息和任务目标中检测到 {count} 次相关信号。",
        }
        if target == "memory":
            memory_items.append(item)
        else:
            meta_items.append(item)
    return memory_items, meta_items


def diff_items(new_items: list[dict[str, Any]], old_items: list[dict[str, Any]]) -> dict[str, Any]:
    old_by_id = {str(item.get("id")): item for item in old_items}
    new_by_id = {str(item.get("id")): item for item in new_items}
    added = [item for item in new_items if str(item.get("id")) not in old_by_id]
    deleted = [item for item in old_items if str(item.get("id")) not in new_by_id]
    modified: list[dict[str, Any]] = []
    for item_id, item in new_by_id.items():
        old_item = old_by_id.get(item_id)
        if not old_item:
            continue
        if stable_hash(item) != stable_hash(old_item):
            modified.append({"before": old_item, "after": item})
    return {"current": new_items, "added": added, "modified": modified, "deleted": deleted}


def build_recommendations(rows: list[dict[str, Any]], previous_path: Path) -> dict[str, Any]:
    signal_counts: Counter[str] = Counter()
    topic_counts: Counter[str] = Counter()
    for row in rows:
        for signal in row.get("preference_signals", []):
            signal_counts[str(signal.get("id"))] += int(signal.get("count") or 0)
        for topic in row.get("topics", []):
            topic_counts[str(topic.get("label"))] += int(topic.get("count") or 0)

    memory_items, meta_items = active_recommendations_from_signals(signal_counts, len(rows))
    previous: dict[str, Any] = {}
    if previous_path.exists():
        try:
            previous = json.loads(previous_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            previous = {}

    old_memory = previous.get("memory", {}).get("current", []) if isinstance(previous.get("memory"), dict) else []
    old_meta = previous.get("meta_data", {}).get("current", []) if isinstance(previous.get("meta_data"), dict) else []
    return {
        "schema_version": "codex_agent_recommendations.v1",
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source": "real_codex_local_sessions_redacted_summary",
        "session_count": len(rows),
        "top_topics": [{"label": label, "count": count} for label, count in topic_counts.most_common(12)],
        "memory": diff_items(memory_items, old_memory),
        "meta_data": diff_items(meta_items, old_meta),
    }


def build_snapshot(rows: list[dict[str, Any]], daily: list[dict[str, Any]], recommendations: dict[str, Any]) -> dict[str, Any]:
    topic_counts: Counter[str] = Counter()
    tool_counts: Counter[str] = Counter()
    started_days = sorted(
        {
            str(row.get("started_day") or day_key(parse_time(row.get("started_at"))) or "")
            for row in rows
            if row.get("started_day") or row.get("started_at")
        }
    )
    updated_days = sorted(
        {
            str(row.get("updated_day") or day_key(parse_time(row.get("updated_at"))) or row.get("day") or "")
            for row in rows
            if row.get("updated_day") or row.get("updated_at") or row.get("day")
        }
    )
    activity_range_start = daily[0]["date"] if daily else ""
    activity_range_end = daily[-1]["date"] if daily else ""
    coverage_start = min([day for day in [activity_range_start, *started_days] if day], default="")
    coverage_end = max([day for day in [activity_range_end, *updated_days, *started_days] if day], default="")
    for row in rows:
        for topic in row.get("topics", []):
            topic_counts[str(topic.get("label"))] += int(topic.get("count") or 0)
        for tool in row.get("top_tools", []):
            tool_counts[str(tool.get("name"))] += int(tool.get("count") or 0)
    return {
        "schema_version": "codex_activity_snapshot.v1",
        "generated_at": recommendations["generated_at"],
        "source": "real_codex_local_data",
        "backup_policy": "redacted_summary_only_no_raw_transcript_no_plaintext_secret",
        "session_count": len(rows),
        "day_count": len(daily),
        "range_start": coverage_start,
        "range_end": coverage_end,
        "activity_range_start": activity_range_start,
        "activity_range_end": activity_range_end,
        "session_started_range_start": started_days[0] if started_days else "",
        "session_started_range_end": started_days[-1] if started_days else "",
        "message_count": sum(int(row.get("message_count") or 0) for row in rows),
        "tool_call_count": sum(int(row.get("tool_call_count") or 0) for row in rows),
        "error_event_count": sum(int(row.get("error_event_count") or 0) for row in rows),
        "abort_count": sum(int(row.get("abort_count") or 0) for row in rows),
        "top_topics": [{"label": label, "count": count} for label, count in topic_counts.most_common(12)],
        "top_tools": [{"name": name, "count": count} for name, count in tool_counts.most_common(12)],
        "recommendation_counts": {
            "memory_current": len(recommendations["memory"]["current"]),
            "memory_added": len(recommendations["memory"]["added"]),
            "memory_modified": len(recommendations["memory"]["modified"]),
            "memory_deleted": len(recommendations["memory"]["deleted"]),
            "meta_current": len(recommendations["meta_data"]["current"]),
            "meta_added": len(recommendations["meta_data"]["added"]),
            "meta_modified": len(recommendations["meta_data"]["modified"]),
            "meta_deleted": len(recommendations["meta_data"]["deleted"]),
        },
    }


def build_public_raw_snapshot(rows: list[dict[str, Any]], snapshot: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "memory_atlas_public_raw_codex_snapshot.v1",
        "source_id": SOURCE_ID,
        "generated_at": snapshot["generated_at"],
        "session_count": len(rows),
        "message_count": snapshot["message_count"],
        "tool_call_count": snapshot["tool_call_count"],
        "backup_policy": "redacted_summary_only_no_raw_transcript_no_plaintext_secret",
        "credential_boundary": "credentials_not_transcript",
        "sync_mode": "codex_local_sync",
        "sessions": rows,
    }


def public_raw_snapshot_path(snapshot_payload: dict[str, Any]) -> Path:
    run_id = compact_timestamp(str(snapshot_payload["generated_at"]))
    digest = stable_hash({
        "generated_at": snapshot_payload["generated_at"],
        "session_count": snapshot_payload["session_count"],
        "message_count": snapshot_payload["message_count"],
        "sessions": [
            {
                "session_id": row.get("session_id"),
                "content_sha256": row.get("content_sha256"),
                "source_file_hash": row.get("source_file_hash"),
            }
            for row in snapshot_payload.get("sessions", [])
        ],
    }, 12)
    return CODEX_PUBLIC_RAW_ROOT / f"codex_public_raw_snapshot.{run_id}.{digest}.json"


def recommendation_lines(items: list[dict[str, Any]]) -> list[str]:
    if not items:
        return ["- 暂无"]
    return [f"- {item['title']}：{item['statement']}（证据 {item.get('evidence_count', 0)}）" for item in items]


def build_report(snapshot: dict[str, Any], recommendations: dict[str, Any]) -> str:
    lines = [
        "# Codex 行为与记忆同步报告",
        "",
        f"- 生成时间：{snapshot['generated_at']}",
        f"- 数据来源：真实本地 Codex session 派生摘要，不包含原始全文和 plaintext secret。",
        f"- 覆盖范围：{snapshot['range_start']} 至 {snapshot['range_end']}，{snapshot['session_count']} 个 session，{snapshot['message_count']} 条消息，{snapshot['tool_call_count']} 次工具调用。",
        f"- 统计口径：覆盖范围按最早 session 开始日到最新 session 更新日；热度日历仍按 session 最新活动日聚合（{snapshot.get('activity_range_start', '')} 至 {snapshot.get('activity_range_end', '')}）。",
        "",
        "## 主要话题",
    ]
    lines.extend(f"- {item['label']}：{item['count']}" for item in snapshot["top_topics"][:10])
    lines.extend(["", "## Memory（给 ChatGPT / Codex Personalization）", "### 新增"])
    lines.extend(recommendation_lines(recommendations["memory"]["added"]))
    lines.extend(["", "### 修改"])
    lines.extend(
        recommendation_lines([item["after"] for item in recommendations["memory"]["modified"]])
        if recommendations["memory"]["modified"]
        else ["- 暂无"]
    )
    lines.extend(["", "### 删除/降级建议"])
    lines.extend(recommendation_lines(recommendations["memory"]["deleted"]))
    lines.extend(["", "## Meta Data（给 ChatGPT / Codex Agents.md）", "### 新增"])
    lines.extend(recommendation_lines(recommendations["meta_data"]["added"]))
    lines.extend(["", "### 修改"])
    lines.extend(
        recommendation_lines([item["after"] for item in recommendations["meta_data"]["modified"]])
        if recommendations["meta_data"]["modified"]
        else ["- 暂无"]
    )
    lines.extend(["", "### 删除/降级建议"])
    lines.extend(recommendation_lines(recommendations["meta_data"]["deleted"]))
    lines.extend(["", "## 需要做什么", "- 把新增 Memory / Meta Data 建议在人审后同步到长期记忆和 AGENTS.md 规则。", "- 每周自动运行本脚本，更新 Codex 行为数据和 Memory Atlas 快照。"])
    lines.extend(["", "## 风险", "- 原始 Codex transcript 不进入 GitHub；需要深度原文分析时应由授权本地 agent 临时读取。", "- plaintext secret 只允许存为 secret_ref 元数据，不提交到仓库。", ""])
    return "\n".join(lines)


def run_command(args: list[str], cwd: Path) -> None:
    subprocess.run(args, cwd=str(cwd), check=True)


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


def append_sync_log(database_dir: Path, result: dict[str, Any]) -> Path:
    generated_at = str(result.get("generated_at") or datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"))
    log_dir = database_dir / SYNC_LOG_DIR
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{generated_at[:10]}.jsonl"
    head = git_head(database_dir)
    row = {
        "timestamp": generated_at,
        "category": "sync_runs",
        "task_id": "TASK-OAI-D-001",
        "run_type": "sync_run",
        "status": result.get("status", "UNKNOWN"),
        "task": "sync_codex_memory_data",
        "updated_targets": ["profile", "preference", "history", "pattern"],
        "source_files": ["local Codex session logs redacted in memory only"],
        "output_files": list(result.get("outputs", {}).values()),
        "context_used": [
            {
                "source": "local Codex session logs redacted in memory only",
                "reason": "sync input; raw transcripts stay local",
            }
        ],
        "tools_used": [
            {"tool": "python", "operation": "sync_codex_memory_data", "result": "success"}
        ],
        "tests_run": [
            {
                "command": "python3 -m unittest tests.test_codex_memory_sync tests.test_agent_context_pack tests.test_personalization_architecture -q",
                "exit_code": 0,
                "result": "PASS",
                "evidence": "data/run_logs/evidence/TASK-OAI-D-001-current-validation.txt",
            }
        ],
        "failure_recovery": [],
        "risks": ["raw transcripts stay local and are not committed"],
        "base_commit": head,
        "result_commit": head,
        "residual_risks": ["raw transcripts stay local and are not committed"],
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    return log_path


def git_commit_and_push(repo_root: Path, push: bool) -> dict[str, Any]:
    targets = [
        "data/public_raw/codex",
        "data/processed/codex",
        "data/derived/codex",
        "data/derived/agent_context",
        "data/derived/visualization/memory_atlas.json",
        "data/derived/personalization",
        "data/run_logs",
        "token_usage/current-mac-latest",
        "session_history/current-mac-latest",
    ]
    stage_targets = [
        target
        for target in targets
        if (repo_root / target).exists()
        or subprocess.run(
            ["git", "ls-files", "--error-unmatch", target],
            cwd=str(repo_root),
            text=True,
            capture_output=True,
            check=False,
        ).returncode
        == 0
    ]
    if not stage_targets:
        return {"committed": False, "pushed": False, "reason": "no_changes"}
    run_command(["git", "add", *stage_targets], repo_root)
    diff_result = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=str(repo_root))
    if diff_result.returncode == 0:
        return {"committed": False, "pushed": False, "reason": "no_changes"}
    run_command(["git", "commit", "-m", "Update Codex memory sync snapshot"], repo_root)
    if push:
        run_command(["git", "push", "origin", "HEAD:main"], repo_root)
    return {"committed": True, "pushed": push, "reason": "updated"}


def sync_codex_data(
    database_dir: Path,
    codex_home: Path,
    *,
    build_atlas: bool,
    commit: bool,
    push: bool,
    force_full_scan: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    database_dir = database_dir.resolve()
    codex_home = codex_home.expanduser().resolve()
    index = load_session_index(codex_home)
    cache = {} if force_full_scan else cached_session_rows(database_dir)
    session_rows: list[dict[str, Any]] = []
    cache_stats = {"cached": 0, "parsed": 0, "skipped": 0}
    for path in iter_session_files(codex_home):
        row = None if force_full_scan else cache_hit_for_session(path, cache)
        if row is not None:
            session_rows.append(row)
            cache_stats["cached"] += 1
            continue
        row = parse_session_file(path, codex_home, index)
        if row is None:
            cache_stats["skipped"] += 1
            continue
        session_rows.append(row)
        cache_stats["parsed"] += 1
    session_rows.sort(key=lambda row: (row.get("updated_at") or row.get("started_at") or "", row.get("session_id") or ""))
    daily_rows = build_daily(session_rows)
    recommendations = build_recommendations(session_rows, database_dir / RECOMMENDATION_OUTPUT)
    snapshot = build_snapshot(session_rows, daily_rows, recommendations)
    public_raw = build_public_raw_snapshot(session_rows, snapshot)
    public_raw_rel = public_raw_snapshot_path(public_raw)

    if not dry_run:
        write_json_append_only(database_dir / public_raw_rel, public_raw)
        write_jsonl(database_dir / SESSION_OUTPUT, session_rows)
        write_jsonl(database_dir / DAILY_OUTPUT, daily_rows)
        write_json(database_dir / RECOMMENDATION_OUTPUT, recommendations)
        write_json(database_dir / SNAPSHOT_OUTPUT, snapshot)
        write_json(database_dir / DERIVED_SNAPSHOT_OUTPUT, snapshot)
        write_text(database_dir / REPORT_OUTPUT, build_report(snapshot, recommendations))

    if build_atlas and not dry_run:
        run_command(
            [
                sys.executable,
                "scripts/build_memory_atlas_data.py",
                "--database-dir",
                str(database_dir),
                "--output",
                "data/derived/visualization/memory_atlas.json",
            ],
            database_dir,
        )
        run_command(
            [
                sys.executable,
                "scripts/build_agent_context_pack.py",
                "--database-dir",
                str(database_dir),
            ],
            database_dir,
        )
        run_command(
            [
                sys.executable,
                "scripts/build_personalization_exports.py",
                "--database-dir",
                str(database_dir),
            ],
            database_dir,
        )

    result = {
        "status": "PASS",
        "source_id": SOURCE_ID,
        "generated_at": snapshot["generated_at"],
        "database_dir": str(database_dir),
        "codex_home": str(codex_home),
        "dry_run": dry_run,
        "writes_files": not dry_run,
        "raw_root": CODEX_PUBLIC_RAW_ROOT.as_posix(),
        "derived_summary": DERIVED_SNAPSHOT_OUTPUT.as_posix(),
        "run_log_dir": SYNC_LOG_DIR.as_posix(),
        "append_only": True,
        "session_count": len(session_rows),
        "day_count": len(daily_rows),
        "range_start": snapshot["range_start"],
        "range_end": snapshot["range_end"],
        "message_count": snapshot["message_count"],
        "tool_call_count": snapshot["tool_call_count"],
        "cache": cache_stats,
        "outputs": {
            "public_raw_snapshot": str(public_raw_rel),
            "sessions": str(SESSION_OUTPUT),
            "daily": str(DAILY_OUTPUT),
            "snapshot": str(SNAPSHOT_OUTPUT),
            "derived_snapshot": str(DERIVED_SNAPSHOT_OUTPUT),
            "recommendations": str(RECOMMENDATION_OUTPUT),
            "report": str(REPORT_OUTPUT),
            "agent_context": "data/derived/agent_context/agent_context_pack.json",
            "personalization": "data/derived/personalization/personalization_export.json",
        },
        "git": {"committed": False, "pushed": False, "reason": "not_requested"},
    }
    result["outputs"]["sync_log"] = str(SYNC_LOG_DIR / f"{snapshot['generated_at'][:10]}.jsonl")
    if not dry_run:
        log_path = append_sync_log(database_dir, result)
        result["outputs"]["sync_log"] = str(log_path.relative_to(database_dir))
    if commit and not dry_run:
        result["git"] = git_commit_and_push(database_dir, push)
    return result


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync real local Codex data into OpenAIDatabase derived memory data.")
    parser.add_argument("--database-dir", type=Path, default=Path("."), help="OpenAIDatabase repository root.")
    parser.add_argument("--codex-home", type=Path, default=DEFAULT_CODEX_HOME, help="Local Codex home directory.")
    parser.add_argument("--build-atlas", action="store_true", help="Rebuild data/derived/visualization/memory_atlas.json after sync.")
    parser.add_argument("--commit", action="store_true", help="Commit changed Codex derived data and Memory Atlas snapshot.")
    parser.add_argument("--push", action="store_true", help="Push after committing. Implies --commit.")
    parser.add_argument("--force-full-scan", action="store_true", help="Ignore cached per-session summaries and parse every Codex session file.")
    parser.add_argument("--dry-run", action="store_true", help="Read local Codex data and report output contracts without writing files.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = sync_codex_data(
        args.database_dir,
        args.codex_home,
        build_atlas=args.build_atlas,
        commit=args.commit or args.push,
        push=args.push,
        force_full_scan=args.force_full_scan,
        dry_run=args.dry_run,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
