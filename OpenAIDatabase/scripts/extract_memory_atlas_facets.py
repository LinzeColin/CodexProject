#!/usr/bin/env python3
"""Extract canonical Memory Atlas behavior events for S05 P2.

The extractor consumes existing public raw, processed manifests and derived
summaries. Missing sources are recorded as source_status rows instead of fake
events. It never writes raw data.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = Path("机器治理/数据契约/facet_event_schema.v1_2_s05_p1.json")
OUTPUT_PATH = Path("data/derived/behavior_intelligence/events.json")
CHATGPT_RAW_ROOT = Path("data/public_raw/chatgpt")
CHATGPT_MANIFEST = Path("data/processed/conversations/conversation_manifest.jsonl")
CODEX_RAW_ROOT = Path("data/public_raw/codex")
CODEX_SESSION_MANIFEST = Path("data/processed/codex/codex_session_manifest.jsonl")
CODEX_SNAPSHOT_PATHS = [
    Path("data/derived/codex/codex_activity_snapshot.json"),
    Path("data/processed/codex/codex_activity_snapshot.json"),
]
FUTURE_AGENT_RAW_ROOT = Path("data/public_raw/agents")
FUTURE_AGENT_DERIVED_ROOT = Path("data/derived/agents")

TASK_ID = "MA-V12-S05P2"
ACCEPTANCE_ID = "ACC-MA-V12-S05P2"
STATUS = "phase_s05_p2_facet_extractor_completed_pending_s05_p3"
REQUIRED_FIELDS = [
    "source",
    "topic",
    "intent",
    "task_type",
    "project",
    "output_type",
    "language",
    "tool",
    "turn_count",
    "friction",
    "value_signal",
    "future_agent_source",
]


class FacetExtractionError(ValueError):
    pass


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise FacetExtractionError(f"invalid JSONL at {path}:{line_number}: {exc}") from exc
        if isinstance(row, dict):
            rows.append(row)
    return rows


def repo_rel(path: Path, database_dir: Path) -> str:
    try:
        return path.resolve().relative_to(database_dir.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def text_of(*values: Any) -> str:
    parts: list[str] = []
    for value in values:
        if value is None:
            continue
        if isinstance(value, list):
            parts.extend(str(item) for item in value)
        elif isinstance(value, dict):
            parts.extend(str(item) for item in value.values())
        else:
            parts.append(str(value))
    return " ".join(part for part in parts if part).strip()


def compact_text(value: Any, fallback: str = "unknown_topic") -> str:
    text = str(value or "").strip()
    text = re.sub(r"\s+", " ", text)
    return text[:160] if text else fallback


def detect_language(text: str) -> str:
    has_zh = bool(re.search(r"[\u4e00-\u9fff]", text))
    has_en = bool(re.search(r"[A-Za-z]", text))
    if has_zh and has_en:
        return "mixed"
    if has_zh:
        return "zh"
    if has_en:
        return "en"
    return "unknown" if not text.strip() else "other"


def first_topic(row: dict[str, Any], *fallbacks: Any) -> str:
    topics = row.get("topics")
    if isinstance(topics, list) and topics:
        first = topics[0]
        if isinstance(first, dict):
            return compact_text(first.get("label") or first.get("id"))
        return compact_text(first)
    return compact_text(text_of(*fallbacks))


def infer_project(text: str) -> str | None:
    lowered = text.lower()
    checks = [
        ("Memory Atlas", ["memory atlas", "openaidatabase", "记忆可视化", "长期记忆"]),
        ("CodexProject", ["codexproject", "github backup", "durable memory", "主仓库"]),
        ("Serenity", ["serenity"]),
        ("Alpha", ["alpha"]),
        ("KMFA", ["kmfa", "kaiming", "wuhan", "开明", "武汉"]),
        ("Finance", ["finance", "trading", "ledger", "金融", "交易"]),
        ("Notion", ["notion"]),
        ("macOS Operations", ["mac", "cleanup", "清理", "launchagent"]),
    ]
    for project, keywords in checks:
        if any(keyword in lowered for keyword in keywords):
            return project
    return None


def keyword_match(text: str, mapping: list[tuple[str, list[str]]], fallback: str) -> str:
    lowered = text.lower()
    for value, keywords in mapping:
        if any(keyword in lowered for keyword in keywords):
            return value
    return fallback


def infer_intent(text: str) -> str:
    return keyword_match(
        text,
        [
            ("debug", ["debug", "fix", "bug", "error", "fail", "失败", "修复", "排查"]),
            ("review", ["review", "audit", "复审", "审核", "验收", "检查"]),
            ("research", ["research", "调研", "研究", "scan"]),
            ("write", ["write", "doc", "文档", "说明", "报告", "总结"]),
            ("operate", ["sync", "backup", "run", "operate", "清理", "恢复", "执行", "同步", "备份"]),
            ("build", ["build", "implement", "code", "开发", "实现", "构建"]),
            ("plan", ["plan", "roadmap", "task pack", "计划", "规划"]),
            ("decide", ["decide", "decision", "判断", "决策"]),
            ("handoff", ["handoff", "交接", "移交"]),
        ],
        "unknown",
    )


def infer_task_type(text: str) -> str:
    return keyword_match(
        text,
        [
            ("design", ["ui", "visual", "three.js", "frontend", "设计", "可视化"]),
            ("automation", ["automation", "schedule", "sync", "backup", "自动", "同步", "备份"]),
            ("engineering", ["code", "script", "test", "validator", "cli", "build", "实现", "开发"]),
            ("data", ["data", "database", "memory", "rag", "manifest", "json", "数据", "记忆"]),
            ("research", ["research", "调研", "研究"]),
            ("writing", ["doc", "report", "write", "文档", "报告", "说明"]),
            ("governance", ["review", "audit", "gate", "policy", "验收", "治理", "门禁"]),
            ("operations", ["operate", "cleanup", "恢复", "运行", "清理"]),
            ("product", ["prd", "mvp", "product", "产品"]),
        ],
        "unknown",
    )


def infer_output_type(text: str) -> str:
    return keyword_match(
        text,
        [
            ("test", ["test", "validator", "验收", "测试"]),
            ("code", ["code", "script", "cli", "实现", "开发"]),
            ("report", ["report", "review", "audit", "报告", "复审"]),
            ("doc", ["doc", "文档", "说明"]),
            ("data", ["data", "json", "database", "manifest", "数据"]),
            ("ui", ["ui", "visual", "frontend", "可视化"]),
            ("config", ["config", "policy", "toml", "yaml", "配置"]),
            ("plan", ["plan", "roadmap", "task pack", "计划"]),
            ("decision", ["decision", "decide", "决策"]),
            ("handoff", ["handoff", "交接"]),
        ],
        "unknown",
    )


def infer_value_signals(text: str, row: dict[str, Any]) -> list[str]:
    lowered = text.lower()
    signals: list[str] = []
    checks = [
        ("durable_memory", ["github", "durable", "openaidatabase", "备份", "长期记忆"]),
        ("verifiability", ["test", "validator", "acceptance", "evidence", "验收", "证据"]),
        ("personalization", ["profile", "preference", "personalization", "偏好", "画像"]),
        ("decision_support", ["roi", "decision", "report", "决策", "报告"]),
        ("operational_efficiency", ["automation", "sync", "run", "自动", "同步"]),
        ("risk_reduction", ["secret", "credential", "privacy", "风险", "凭证", "安全"]),
        ("knowledge_reuse", ["memory", "rag", "context", "复用", "知识"]),
    ]
    for signal, keywords in checks:
        if any(keyword in lowered for keyword in keywords):
            signals.append(signal)
    activity_score = int(row.get("activity_score") or 0)
    if activity_score >= 1000:
        signals.append("high_work_volume")
    return sorted(set(signals))


def infer_friction(text: str, row: dict[str, Any], evidence_missing_reason: str | None) -> list[str]:
    lowered = text.lower()
    friction: list[str] = []
    if int(row.get("abort_count") or 0) > 0:
        friction.append("aborted_or_interrupted")
    if int(row.get("error_event_count") or 0) > 0 or int(row.get("decode_error_count") or 0) > 0:
        friction.append("errors_or_decode_issues")
    if any(keyword in lowered for keyword in ["bug", "error", "fail", "修复", "失败", "排查"]):
        friction.append("debugging_or_rework")
    if evidence_missing_reason:
        friction.append("evidence_gap")
    return sorted(set(friction))


def infer_risk_signals(text: str, row: dict[str, Any]) -> list[str]:
    lowered = text.lower()
    risks: list[str] = []
    if any(keyword in lowered for keyword in ["secret", "credential", "privacy", "password", "凭证", "安全"]):
        risks.append("credential_or_privacy_boundary")
    if int(row.get("abort_count") or 0) > 0:
        risks.append("completion_risk")
    if int(row.get("error_event_count") or 0) > 0:
        risks.append("runtime_error_risk")
    return sorted(set(risks))


def top_tool(row: dict[str, Any], default: str) -> str:
    tools = row.get("top_tools")
    if isinstance(tools, list) and tools:
        name = tools[0].get("name") if isinstance(tools[0], dict) else tools[0]
        if name in {"github", "browser", "terminal", "filesystem", "notion", "dingtalk"}:
            return str(name)
    return default


def tools_used(row: dict[str, Any]) -> list[str]:
    tools = row.get("top_tools")
    if not isinstance(tools, list):
        return []
    names: list[str] = []
    for tool in tools[:8]:
        if isinstance(tool, dict):
            name = str(tool.get("name") or "").strip()
        else:
            name = str(tool).strip()
        if name:
            names.append(name)
    return names


def build_event(
    *,
    source: str,
    record_id: str,
    title: str,
    row: dict[str, Any],
    default_tool: str,
    source_id: str | None = None,
    occurred_at: str | None = None,
    raw_ref: str | None = None,
    manifest_ref: str | None = None,
    derived_ref: str | None = None,
    evidence_missing_reason: str | None = None,
    future_agent_source: dict[str, Any] | None = None,
    agent_name: str | None = None,
) -> dict[str, Any]:
    context_text = text_of(title, row.get("thread_name"), row.get("cwd_label"), row.get("topics"), row.get("preference_signals"))
    event: dict[str, Any] = {
        "event_id": f"{source}_{stable_hash([source, record_id, raw_ref, manifest_ref, derived_ref])[:16]}",
        "source": source,
        "source_id": source_id or source,
        "record_id": record_id,
        "occurred_at": occurred_at or str(row.get("updated_at") or row.get("created_at") or row.get("generated_at") or ""),
        "topic": first_topic(row, title),
        "intent": infer_intent(context_text),
        "task_type": infer_task_type(context_text),
        "project": infer_project(context_text),
        "output_type": infer_output_type(context_text),
        "language": detect_language(context_text),
        "tool": top_tool(row, default_tool),
        "turn_count": int(row.get("user_message_count") or row.get("message_count") or 0),
        "friction": infer_friction(context_text, row, evidence_missing_reason),
        "value_signal": infer_value_signals(context_text, row),
        "future_agent_source": future_agent_source,
        "confidence": "medium" if evidence_missing_reason else "high",
        "risk_signal": infer_risk_signals(context_text, row),
        "tools_used": tools_used(row),
    }
    if agent_name:
        event["agent_name"] = agent_name
    if raw_ref:
        event["raw_ref"] = raw_ref
    if manifest_ref:
        event["manifest_ref"] = manifest_ref
    if derived_ref:
        event["derived_ref"] = derived_ref
    if evidence_missing_reason:
        event["evidence_missing_reason"] = evidence_missing_reason
    validate_event(event)
    return event


def validate_event(event: dict[str, Any]) -> None:
    missing = [field for field in REQUIRED_FIELDS if field not in event]
    if missing:
        raise FacetExtractionError(f"event {event.get('event_id')} missing required fields: {missing}")
    if event["source"] not in {"chatgpt", "codex", "future_agent", "other_agent"}:
        raise FacetExtractionError(f"invalid source: {event['source']}")
    if not isinstance(event["turn_count"], int) or event["turn_count"] < 0:
        raise FacetExtractionError(f"invalid turn_count for {event.get('event_id')}")
    if not isinstance(event["friction"], list) or not isinstance(event["value_signal"], list):
        raise FacetExtractionError(f"array fields invalid for {event.get('event_id')}")
    if not (event.get("raw_ref") or event.get("manifest_ref") or event.get("derived_ref") or event.get("evidence_missing_reason")):
        raise FacetExtractionError(f"event {event.get('event_id')} lacks evidence reference or missing reason")
    if event["source"] in {"future_agent", "other_agent"} and not event.get("future_agent_source"):
        raise FacetExtractionError(f"future agent event {event.get('event_id')} lacks future_agent_source")


def source_status(
    *,
    source_id: str,
    status: str,
    input_paths: list[str],
    event_count: int,
    evidence_level: str,
    missing_reason: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "source_id": source_id,
        "status": status,
        "input_paths": input_paths,
        "event_count": event_count,
        "evidence_level": evidence_level,
    }
    if missing_reason:
        payload["missing_reason"] = missing_reason
    return payload


def extract_chatgpt(database_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    events: list[dict[str, Any]] = []
    input_paths: list[str] = []
    raw_root = database_dir / CHATGPT_RAW_ROOT
    raw_files = sorted(raw_root.glob("*.json")) if raw_root.exists() else []
    if raw_files:
        for raw_file in raw_files:
            row = read_json(raw_file)
            if not isinstance(row, dict):
                continue
            record_id = str(row.get("conversation_id") or row.get("source_id") or raw_file.stem)
            events.append(
                build_event(
                    source="chatgpt",
                    source_id="chatgpt",
                    record_id=record_id,
                    title=compact_text(row.get("title")),
                    row=row,
                    default_tool="chatgpt",
                    occurred_at=str(row.get("updated_at") or row.get("created_at") or ""),
                    raw_ref=repo_rel(raw_file, database_dir),
                )
            )
        input_paths = [repo_rel(path, database_dir) for path in raw_files]
        return events, source_status(
            source_id="chatgpt",
            status="extracted_from_public_raw",
            input_paths=input_paths,
            event_count=len(events),
            evidence_level="raw",
        )

    manifest_path = database_dir / CHATGPT_MANIFEST
    rows = read_jsonl(manifest_path)
    if rows:
        manifest_ref = CHATGPT_MANIFEST.as_posix()
        for row in rows:
            record_id = str(row.get("conversation_id") or stable_hash(row)[:16])
            events.append(
                build_event(
                    source="chatgpt",
                    source_id="chatgpt",
                    record_id=record_id,
                    title=compact_text(row.get("title")),
                    row=row,
                    default_tool="chatgpt",
                    occurred_at=str(row.get("updated_at") or row.get("created_at") or ""),
                    manifest_ref=manifest_ref,
                    evidence_missing_reason="processed_manifest_without_public_raw_ref",
                )
            )
        return events, source_status(
            source_id="chatgpt",
            status="extracted_from_processed_manifest",
            input_paths=[manifest_ref],
            event_count=len(events),
            evidence_level="processed_manifest",
            missing_reason="public_raw_chatgpt_missing",
        )

    return events, source_status(
        source_id="chatgpt",
        status="missing",
        input_paths=[],
        event_count=0,
        evidence_level="none",
        missing_reason="no_chatgpt_public_raw_or_processed_manifest",
    )


def extract_codex(database_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    events: list[dict[str, Any]] = []
    raw_root = database_dir / CODEX_RAW_ROOT
    raw_files = sorted(raw_root.glob("*.json")) if raw_root.exists() else []
    if raw_files:
        for raw_file in raw_files:
            snapshot = read_json(raw_file)
            if not isinstance(snapshot, dict):
                continue
            rows = snapshot.get("sessions") if isinstance(snapshot.get("sessions"), list) else [snapshot]
            for row in rows:
                if not isinstance(row, dict):
                    continue
                record_id = str(row.get("session_id") or stable_hash(row)[:16])
                events.append(
                    build_event(
                        source="codex",
                        source_id="codex",
                        record_id=record_id,
                        title=compact_text(row.get("thread_name") or row.get("cwd_label") or "Codex activity"),
                        row=row,
                        default_tool="codex",
                        occurred_at=str(row.get("updated_at") or row.get("started_at") or snapshot.get("generated_at") or ""),
                        raw_ref=repo_rel(raw_file, database_dir),
                    )
                )
        return events, source_status(
            source_id="codex",
            status="extracted_from_public_raw",
            input_paths=[repo_rel(path, database_dir) for path in raw_files],
            event_count=len(events),
            evidence_level="raw",
        )

    manifest_path = database_dir / CODEX_SESSION_MANIFEST
    rows = read_jsonl(manifest_path)
    if rows:
        manifest_ref = CODEX_SESSION_MANIFEST.as_posix()
        for row in rows:
            record_id = str(row.get("session_id") or stable_hash(row)[:16])
            events.append(
                build_event(
                    source="codex",
                    source_id="codex",
                    record_id=record_id,
                    title=compact_text(row.get("thread_name") or row.get("cwd_label") or "Codex activity"),
                    row=row,
                    default_tool="codex",
                    occurred_at=str(row.get("updated_at") or row.get("started_at") or ""),
                    manifest_ref=manifest_ref,
                    evidence_missing_reason="processed_manifest_without_public_raw_ref",
                )
            )
        return events, source_status(
            source_id="codex",
            status="extracted_from_processed_manifest",
            input_paths=[manifest_ref],
            event_count=len(events),
            evidence_level="processed_manifest",
            missing_reason="public_raw_codex_missing",
        )

    for snapshot_rel in CODEX_SNAPSHOT_PATHS:
        snapshot_path = database_dir / snapshot_rel
        if not snapshot_path.exists():
            continue
        snapshot = read_json(snapshot_path)
        if not isinstance(snapshot, dict):
            continue
        record_id = str(snapshot.get("generated_at") or snapshot_rel.stem)
        events.append(
            build_event(
                source="codex",
                source_id="codex",
                record_id=record_id,
                title="Codex activity snapshot",
                row=snapshot,
                default_tool="codex",
                occurred_at=str(snapshot.get("generated_at") or ""),
                derived_ref=snapshot_rel.as_posix(),
                evidence_missing_reason="derived_snapshot_without_session_manifest_or_public_raw_ref",
            )
        )
        return events, source_status(
            source_id="codex",
            status="extracted_from_derived_snapshot",
            input_paths=[snapshot_rel.as_posix()],
            event_count=len(events),
            evidence_level="derived",
            missing_reason="public_raw_codex_and_session_manifest_missing",
        )

    return events, source_status(
        source_id="codex",
        status="missing",
        input_paths=[],
        event_count=0,
        evidence_level="none",
        missing_reason="no_codex_public_raw_processed_manifest_or_derived_snapshot",
    )


def extract_future_agents(database_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    events: list[dict[str, Any]] = []
    input_paths: list[str] = []
    raw_root = database_dir / FUTURE_AGENT_RAW_ROOT
    raw_files = sorted(raw_root.glob("*/*.json")) if raw_root.exists() else []
    for raw_file in raw_files:
        row = read_json(raw_file)
        if not isinstance(row, dict):
            continue
        agent_id = str(row.get("agent_id") or raw_file.parent.name)
        agent_name = str(row.get("agent_name") or agent_id)
        record_id = str(row.get("event_id") or row.get("id") or raw_file.stem)
        future_agent_source = {
            "agent_id": agent_id,
            "agent_name": agent_name,
            "source_type": "other_agent",
            "adapter_mode": row.get("adapter_mode") or "unknown",
        }
        events.append(
            build_event(
                source="future_agent",
                source_id="future-agent",
                record_id=record_id,
                title=compact_text(row.get("title") or "Future agent event"),
                row=row,
                default_tool="other",
                occurred_at=str(row.get("updated_at") or row.get("created_at") or ""),
                raw_ref=repo_rel(raw_file, database_dir),
                future_agent_source=future_agent_source,
                agent_name=agent_name,
            )
        )
        input_paths.append(repo_rel(raw_file, database_dir))

    if events:
        return events, source_status(
            source_id="future_agent",
            status="extracted_from_public_raw",
            input_paths=input_paths,
            event_count=len(events),
            evidence_level="raw",
        )

    derived_root = database_dir / FUTURE_AGENT_DERIVED_ROOT
    summary_files = sorted(derived_root.glob("*/agent_sync_summary.json")) if derived_root.exists() else []
    if summary_files:
        return events, source_status(
            source_id="future_agent",
            status="derived_summary_present_no_event_rows",
            input_paths=[repo_rel(path, database_dir) for path in summary_files],
            event_count=0,
            evidence_level="derived_summary",
            missing_reason="future_agent_raw_events_missing",
        )

    return events, source_status(
        source_id="future_agent",
        status="missing",
        input_paths=[],
        event_count=0,
        evidence_level="none",
        missing_reason="no_future_agent_public_raw_or_derived_summary",
    )


def validate_payload(payload: dict[str, Any]) -> None:
    if payload.get("task_id") != TASK_ID or payload.get("acceptance_id") != ACCEPTANCE_ID:
        raise FacetExtractionError("payload identity mismatch")
    events = payload.get("events")
    if not isinstance(events, list):
        raise FacetExtractionError("events must be a list")
    seen: set[str] = set()
    for event in events:
        if not isinstance(event, dict):
            raise FacetExtractionError("event rows must be objects")
        validate_event(event)
        event_id = str(event["event_id"])
        if event_id in seen:
            raise FacetExtractionError(f"duplicate event_id: {event_id}")
        seen.add(event_id)
    status = payload.get("source_status")
    if not isinstance(status, dict):
        raise FacetExtractionError("source_status must be an object")
    for source_id in ("chatgpt", "codex", "future_agent"):
        if source_id not in status:
            raise FacetExtractionError(f"source_status missing {source_id}")


def extract_facets(
    database_dir: Path,
    dry_run: bool = False,
    generated_at: str | None = None,
    output_path: Path = OUTPUT_PATH,
) -> dict[str, Any]:
    database_dir = database_dir.resolve()
    generated_at = generated_at or now_utc()
    chatgpt_events, chatgpt_status = extract_chatgpt(database_dir)
    codex_events, codex_status = extract_codex(database_dir)
    future_events, future_status = extract_future_agents(database_dir)
    events = sorted(
        [*chatgpt_events, *codex_events, *future_events],
        key=lambda event: (event["source"], event.get("occurred_at") or "", event["event_id"]),
    )
    payload: dict[str, Any] = {
        "schema_version": "memory_atlas_behavior_events.v1",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "status": STATUS,
        "generated_at": generated_at,
        "dry_run": dry_run,
        "writes_files": not dry_run,
        "schema_ref": SCHEMA_PATH.as_posix(),
        "output_path": output_path.as_posix(),
        "event_count": len(events),
        "required_fields": REQUIRED_FIELDS,
        "source_status": {
            "chatgpt": chatgpt_status,
            "codex": codex_status,
            "future_agent": future_status,
        },
        "phase_boundary": {
            "does_not_modify_raw": True,
            "does_not_generate_fake_records_for_missing_data": True,
            "does_not_change_first_screen_ui": True,
            "next_phase": "S05 P3 evidence refs and review",
        },
        "events": events,
    }
    validate_payload(payload)
    if not dry_run:
        output = database_dir / output_path
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Memory Atlas S05 P2 facet extractor.")
    parser.add_argument("--database-dir", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = extract_facets(args.database_dir, dry_run=args.dry_run, output_path=args.output)
    except FacetExtractionError as exc:
        print(json.dumps({
            "status": "FAIL",
            "task_id": TASK_ID,
            "acceptance_id": ACCEPTANCE_ID,
            "reason": str(exc),
            "writes_files": False,
        }, ensure_ascii=False, indent=2, sort_keys=True))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
