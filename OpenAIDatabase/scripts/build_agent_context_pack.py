#!/usr/bin/env python3
"""Build a fixed-path agent context pack from redacted derived memory data."""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any


DEFAULT_JSON_OUTPUT = Path("data/derived/agent_context/agent_context_pack.json")
DEFAULT_MARKDOWN_OUTPUT = Path("data/derived/agent_context/AGENT_CONTEXT.md")
CORE_PROFILE = Path("data/derived/profile/CORE_PROFILE.md")
CODEX_RECOMMENDATIONS = Path("data/derived/codex/codex_agent_recommendations.json")
CODEX_SNAPSHOT = Path("data/processed/codex/codex_activity_snapshot.json")
MEMORY_ATLAS = Path("data/derived/visualization/memory_atlas.json")
DATA_SOURCE_REGISTRY = Path("config/data_sources/source_registry.json")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def write_if_changed(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text(encoding="utf-8", errors="ignore") == payload:
        return
    tmp_path = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        tmp_path.write_text(payload, encoding="utf-8")
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def extract_core_profile_items(markdown: str) -> list[str]:
    items: list[str] = []
    in_section = False
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            in_section = stripped == "## High-weight Core Personalization"
            continue
        if in_section and line.startswith("- "):
            item = re.sub(r"\s+", " ", line[2:]).strip()
            if item:
                items.append(item)
    return items


def current_items(section: Any) -> list[dict[str, Any]]:
    if not isinstance(section, dict):
        return []
    return [item for item in section.get("current", []) if isinstance(item, dict)]


def changed_items(section: Any, key: str) -> list[dict[str, Any]]:
    if not isinstance(section, dict):
        return []
    rows = section.get(key, [])
    return rows if isinstance(rows, list) else []


def compact_recommendation(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(item.get("id") or ""),
        "title": str(item.get("title") or ""),
        "statement": str(item.get("statement") or ""),
        "source": str(item.get("source") or ""),
        "importance": str(item.get("importance") or ""),
        "confidence": str(item.get("confidence") or ""),
        "evidence_count": int(item.get("evidence_count") or 0),
        "reason": str(item.get("reason") or ""),
        "scope": str(item.get("scope") or ""),
    }


def compact_data_source(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(item.get("id") or ""),
        "label": str(item.get("label") or ""),
        "platform": str(item.get("platform") or ""),
        "status": str(item.get("status") or ""),
        "ingestion_status": str(item.get("ingestion_status") or ""),
        "agent_use": [str(value) for value in item.get("agent_use", [])[:6]] if isinstance(item.get("agent_use"), list) else [],
    }


def build_agent_context_pack(database_dir: Path) -> dict[str, Any]:
    database_dir = database_dir.resolve()
    core_profile_path = database_dir / CORE_PROFILE
    recommendations_path = database_dir / CODEX_RECOMMENDATIONS
    snapshot_path = database_dir / CODEX_SNAPSHOT
    atlas_path = database_dir / MEMORY_ATLAS
    registry_path = database_dir / DATA_SOURCE_REGISTRY

    core_profile_markdown = read_text(core_profile_path)
    core_profile_items = extract_core_profile_items(core_profile_markdown)
    recommendations = read_json(recommendations_path)
    snapshot = read_json(snapshot_path)
    atlas = read_json(atlas_path)
    registry = read_json(registry_path)
    overview = atlas.get("overview", {}) if isinstance(atlas.get("overview"), dict) else {}
    registry_sources = registry.get("sources", []) if isinstance(registry.get("sources"), list) else []
    data_sources = [compact_data_source(source) for source in registry_sources if isinstance(source, dict)]

    memory_current = [compact_recommendation(item) for item in current_items(recommendations.get("memory"))]
    meta_current = [compact_recommendation(item) for item in current_items(recommendations.get("meta_data"))]
    top_topics = recommendations.get("top_topics", [])
    if not isinstance(top_topics, list):
        top_topics = []

    return {
        "schema_version": "agent_context_pack.v1",
        "generated_at": recommendations.get("generated_at") or snapshot.get("generated_at") or overview.get("generated_at") or "",
        "source": "OpenAIDatabase redacted derived memory surfaces",
        "source_files": {
            "core_profile": str(CORE_PROFILE),
            "codex_recommendations": str(CODEX_RECOMMENDATIONS),
            "codex_snapshot": str(CODEX_SNAPSHOT),
            "memory_atlas": str(MEMORY_ATLAS),
            "data_source_registry": str(DATA_SOURCE_REGISTRY),
        },
        "read_order": [
            str(DEFAULT_MARKDOWN_OUTPUT),
            str(DEFAULT_JSON_OUTPUT),
            str(CORE_PROFILE),
            str(CODEX_RECOMMENDATIONS),
            str(MEMORY_ATLAS),
            str(DATA_SOURCE_REGISTRY),
        ],
        "memory": {
            "purpose": "给任意 ChatGPT / Codex / future agent 作为长期记忆和 RAG 入口。",
            "current": memory_current,
            "changes": {
                "added": changed_items(recommendations.get("memory"), "added"),
                "modified": changed_items(recommendations.get("memory"), "modified"),
                "deleted_or_demoted": changed_items(recommendations.get("memory"), "deleted"),
            },
        },
        "personalization": {
            "default_language": "中文；代码、API、库名、错误信息和专业术语可保留英文。",
            "core_profile_items": core_profile_items,
            "codex_memory_items": memory_current,
            "startup_instruction_zh": "新 agent 启动后先读取本文件、CORE_PROFILE 和 Memory Atlas，再生成适配用户的 profile、preference、project context、rules 和 history summary；不要依赖聊天上下文猜测。",
        },
        "profile": {
            "core_profile_path": str(CORE_PROFILE),
            "core_profile_item_count": len(core_profile_items),
            "core_profile_items": core_profile_items,
        },
        "preferences": {
            "items": memory_current,
            "top_topics": top_topics[:12],
        },
        "meta_data": {
            "purpose": "给 ChatGPT / Codex Agents.md / workflow 使用的行为规则、授权边界和安全边界。",
            "current": meta_current,
            "changes": {
                "added": changed_items(recommendations.get("meta_data"), "added"),
                "modified": changed_items(recommendations.get("meta_data"), "modified"),
                "deleted_or_demoted": changed_items(recommendations.get("meta_data"), "deleted"),
            },
        },
        "behavior": {
            "source": snapshot.get("source"),
            "backup_policy": snapshot.get("backup_policy"),
            "session_count": int(snapshot.get("session_count") or 0),
            "message_count": int(snapshot.get("message_count") or 0),
            "tool_call_count": int(snapshot.get("tool_call_count") or 0),
            "range_start": snapshot.get("range_start") or "",
            "range_end": snapshot.get("range_end") or "",
            "top_topics": snapshot.get("top_topics") or top_topics[:12],
            "atlas_nodes": int(overview.get("node_count") or 0),
            "atlas_edges": int(overview.get("edge_count") or 0),
        },
        "data_sources": {
            "registry_path": str(DATA_SOURCE_REGISTRY),
            "schema_version": registry.get("schema_version") or "",
            "contract_version": registry.get("contract_version") or "",
            "active": [source for source in data_sources if source.get("status") == "active"],
            "planned": [source for source in data_sources if source.get("status") == "planned"],
            "canonical_required_fields": registry.get("canonical_event_contract", {}).get("required_fields", [])
            if isinstance(registry.get("canonical_event_contract"), dict)
            else [],
            "compatibility_rule": "Add future platform ingestors by emitting canonical redacted derived events and registering the source here; do not create fake Memory Atlas nodes.",
        },
        "human_review": {
            "memory_atlas_runtime": "http://127.0.0.1:4177/",
            "weekly_pack_glob": "data/derived/weekly/*.weekly_memory_pack.md",
            "monthly_pack_glob": "data/derived/monthly/*.monthly_memory_pack.md",
            "codex_behavior_report": "data/derived/codex/codex_behavior_report.md",
        },
        "safety": {
            "raw_transcripts_included": False,
            "plaintext_high_risk_secrets_included": False,
            "local_absolute_paths_included": False,
            "writeback_policy": "proposal_only_with_agent_or_human_apply_and_git_rollback",
        },
    }


def markdown_lines(pack: dict[str, Any]) -> list[str]:
    behavior = pack["behavior"]
    lines = [
        "# Agent Context Pack",
        "",
        "固定入口：给任意 ChatGPT / Codex / future agent 启动时读取。",
        "",
        f"- 生成时间：{pack['generated_at']}",
        f"- 数据来源：{pack['source']}",
        f"- 覆盖 Codex：{behavior['range_start']} 至 {behavior['range_end']}，{behavior['session_count']} 个 session，{behavior['message_count']} 条消息，{behavior['tool_call_count']} 次工具调用。",
        f"- Memory Atlas：{behavior['atlas_nodes']} 个节点，{behavior['atlas_edges']} 条边。",
        f"- 数据源注册表：{pack['data_sources']['schema_version']}，当前 {len(pack['data_sources']['active'])} 个 active，{len(pack['data_sources']['planned'])} 个 planned。",
        "",
        "## Agent 启动规则",
        "",
        f"- {pack['personalization']['startup_instruction_zh']}",
        "- 默认中文输出；代码、API、库名、错误信息和专业术语可保留英文。",
        "- 使用真实数据和可验证证据；不要使用 mock、伪进度或只给概念演示。",
        "- 新增微信、小红书、抖音等平台数据时，先按数据源注册表输出脱敏派生事件；未接入真实数据前只能显示计划来源，不能生成假节点。",
        "- 写回长期记忆只能走 proposal / 人审 / agent apply / git rollback 流程。",
        "",
        "## Profile / Core Personalization",
        "",
    ]
    for item in pack["profile"]["core_profile_items"][:12]:
        lines.append(f"- {item}")
    if not pack["profile"]["core_profile_items"]:
        lines.append("- 暂无核心画像条目。")

    lines.extend(["", "## Memory（给 ChatGPT / Codex Personalization）", ""])
    for item in pack["memory"]["current"]:
        lines.append(f"- {item['title']}：{item['statement']}（证据 {item['evidence_count']}，置信度 {item['confidence']}）")
    if not pack["memory"]["current"]:
        lines.append("- 暂无。")

    lines.extend(["", "## Meta Data（给 ChatGPT / Codex Agents.md）", ""])
    for item in pack["meta_data"]["current"]:
        lines.append(f"- {item['title']}：{item['statement']}（证据 {item['evidence_count']}，置信度 {item['confidence']}）")
    if not pack["meta_data"]["current"]:
        lines.append("- 暂无。")

    lines.extend(["", "## Top Topics", ""])
    for topic in pack["behavior"]["top_topics"][:10]:
        if isinstance(topic, dict):
            lines.append(f"- {topic.get('label', '')}：{topic.get('count', 0)}")

    lines.extend(
        [
            "",
            "## Data Sources",
            "",
            "Active:",
            *[
                f"- {source['label']}（{source['id']} / {source['platform']}）：{source['ingestion_status']}"
                for source in pack["data_sources"]["active"]
            ],
            "Planned:",
            *[
                f"- {source['label']}（{source['id']} / {source['platform']}）：{source['ingestion_status']}"
                for source in pack["data_sources"]["planned"]
            ],
            "",
            "## Read Order",
            "",
            *[f"- `{path}`" for path in pack["read_order"]],
            "",
            "## Safety",
            "",
            "- 不包含原始 transcript、plaintext high-risk secrets、本地绝对路径。",
            "- 需要深度原文分析时，由授权本地 agent 临时读取原始数据；不要把原始数据提交到 GitHub。",
            "",
        ]
    )
    return lines


def write_pack(database_dir: Path, json_output: Path, markdown_output: Path) -> dict[str, Any]:
    database_dir = database_dir.resolve()
    pack = build_agent_context_pack(database_dir)
    json_path = json_output if json_output.is_absolute() else database_dir / json_output
    markdown_path = markdown_output if markdown_output.is_absolute() else database_dir / markdown_output
    write_if_changed(json_path, json.dumps(pack, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    write_if_changed(markdown_path, "\n".join(markdown_lines(pack)))
    return {"status": "PASS", "json": str(json_path), "markdown": str(markdown_path), "schema_version": pack["schema_version"]}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build fixed-path agent context pack from derived memory data.")
    parser.add_argument("--database-dir", type=Path, default=Path("."), help="OpenAIDatabase repository root.")
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = write_pack(args.database_dir, args.json_output, args.markdown_output)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
