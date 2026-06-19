#!/usr/bin/env python3
"""Build read-only data for the Memory Atlas visualization.

The visualization layer must not mutate the memory database. This script reads
reviewed memory surfaces and writes a derived JSON file that can be consumed by
the Vite/React frontend.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
from collections import Counter, defaultdict
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any, Iterable


DEFAULT_OUTPUT = Path("data/derived/visualization/memory_atlas.json")
ACTIVE_MEMORY_SOURCE = "data/memory/active/active_memory.jsonl"
DATA_SOURCE_REGISTRY_SOURCE = "config/data_sources/source_registry.json"
CODEX_SESSION_SOURCE = "data/processed/codex/codex_session_manifest.jsonl"
CODEX_DAILY_SOURCE = "data/processed/codex/codex_daily_activity.jsonl"
CODEX_RECOMMENDATION_SOURCE = "data/derived/codex/codex_agent_recommendations.json"
PROPOSAL_SCHEMA_VERSION = "memory_change_proposal.v1"
EDITABLE_MEMORY_FIELDS = [
    "statement",
    "title",
    "memory_tier",
    "category",
    "importance",
    "validity",
    "confidence",
    "retrieval_weight",
    "use_when",
    "do_not_use_for",
]
REDACTED_HASH_RE = re.compile(r"redacted_source_hash=([A-Za-z0-9_-]+)")
CANDIDATE_RUN_RE = re.compile(r"run_(\d{8}T\d{6}Z)\.memory_candidates\.jsonl$")

TIER_ORDER = {"核心画像": 0, "一般": 1, "临时": 2}
TIER_WEIGHT = {"核心画像": 1.0, "一般": 0.66, "临时": 0.28}
TIER_ALIASES = {"重要中长期": "一般", "一般短期": "临时"}
IMPORTANCE_WEIGHT = {"高": 1.0, "中": 0.62, "低": 0.32}
CONFIDENCE_WEIGHT = {"high": 1.0, "medium": 0.72, "low": 0.45}

THEMES: list[dict[str, Any]] = [
    {
        "id": "memory-rag-continuity",
        "label": "长期记忆库 / RAG / Agent 连续性",
        "keywords": ["OpenAIDatabase", "长期记忆", "记忆数据库", "记忆库", "RAG", "search/fetch", "MCP", "personalization"],
        "color": "#8fd3ff",
    },
    {
        "id": "codex-agent-workflow",
        "label": "Codex / Agent 工作流 / Token ROI",
        "keywords": ["Codex", "agent", "token", "workflow", "loop", "skill", "side chat", "CLI", "上下文"],
        "color": "#7ee8d4",
    },
    {
        "id": "learning-notion-nitrosend",
        "label": "学习系统 / Notion / 仪表盘",
        "keywords": ["学习计划", "Study Project", "Notion", "Nitrosend", "dashboard", "邮件", "推送", "PM", "架构师"],
        "color": "#48c7e8",
    },
    {
        "id": "rotary-kiln-industrial",
        "label": "回转窑 / 工业服务 / 动态测量调整",
        "keywords": ["回转窑", "动态测量", "工业", "巡检", "技术报告", "点检", "采购", "年包", "月包"],
        "color": "#6ea8ff",
    },
    {
        "id": "finance-trading-probability",
        "label": "金融 / 交易 / FIFA / 概率决策",
        "keywords": ["finance", "trading", "FIFA", "TAB", "下注", "bet", "概率", "资金", "broker", "交易"],
        "color": "#f48fb1",
    },
    {
        "id": "course-reporting",
        "label": "课程 / 公司报告 / 可持续报告",
        "keywords": ["ACCT", "Corporate Reporting", "Sustainability", "ISSB", "GRI", "SASB", "directors report", "remuneration"],
        "color": "#c7a7ff",
    },
    {
        "id": "ai-era-growth",
        "label": "AI 时代 / 社会影响 / 个人能力突破",
        "keywords": ["AI时代", "AI 的时代", "社会", "生产效率", "Ultimate Goal", "top1", "个人能力", "沟通"],
        "color": "#7ee8d4",
    },
    {
        "id": "formal-engineering-delivery",
        "label": "EVA OS / 系统开发 / Task Pack",
        "keywords": ["EVA", "Task Pack", "Run Contract", "PDF 报告", "部署", "系统", "开发流程"],
        "color": "#a5b4fc",
    },
]

CATEGORY_LABELS = {
    "answering_rule": "回答规则",
    "project_context": "项目背景",
    "preference": "偏好",
    "decision": "决策",
    "security_boundary": "安全边界",
    "workflow": "工作流",
    "temporary_or_sensitive": "敏感临时",
    "codex_development_record": "Codex开发",
    "codex_usage_record": "Codex使用",
    "codex_personalization": "个性化",
    "codex_agent_metadata": "Agent规则",
}

GENERIC_LABEL_TOKENS = {
    "静态图谱低敏摘要",
    "层级",
    "分类",
    "重要性",
    "有效期",
    "主题",
    "unknown",
    "private",
    "derived",
    "memory",
    "atlas",
    "codex",
    "agent",
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                rows.append(json.loads(stripped))
    return rows


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def load_data_source_registry(database_dir: Path) -> dict[str, Any]:
    registry = read_json(database_dir / DATA_SOURCE_REGISTRY_SOURCE)
    if registry.get("schema_version") != "memory_atlas_data_source_registry.v1":
        return {}
    sources = registry.get("sources")
    if not isinstance(sources, list):
        return {}
    registry["sources"] = [source for source in sources if isinstance(source, dict) and str(source.get("id") or "").strip()]
    return registry


def registry_source_map(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    sources = registry.get("sources")
    if not isinstance(sources, list):
        return {}
    return {str(source["id"]): source for source in sources if isinstance(source, dict) and str(source.get("id") or "").strip()}


def source_summary(
    source: dict[str, Any],
    *,
    node_count: int,
    activity_count: int,
    latest_date: str,
) -> dict[str, Any]:
    return {
        "id": str(source.get("id") or ""),
        "label": str(source.get("label") or source.get("id") or ""),
        "description": str(source.get("description") or ""),
        "platform": str(source.get("platform") or ""),
        "status": str(source.get("status") or "planned"),
        "ingestion_status": str(source.get("ingestion_status") or ""),
        "record_types": [str(item) for item in source.get("record_types", []) if str(item).strip()]
        if isinstance(source.get("record_types"), list)
        else [],
        "node_count": node_count,
        "activity_count": activity_count,
        "latest_date": latest_date,
    }


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") == payload:
        return
    tmp_path = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        tmp_path.write_text(payload, encoding="utf-8")
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_hash(value: str) -> int:
    return int(hashlib.sha256(value.encode("utf-8")).hexdigest()[:12], 16)


def stable_unit(value: str, salt: str) -> float:
    return (stable_hash(f"{salt}:{value}") % 1000000) / 1000000


def slugify(value: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "-", value.strip()).strip("-")
    return text.lower() or "unknown"


def parse_date(value: Any) -> date | None:
    if not value:
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value), UTC).date()
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text).date()
    except ValueError:
        try:
            return date.fromisoformat(text[:10])
        except ValueError:
            return None


def truncate_label(value: str, limit: int = 56) -> str:
    text = re.sub(r"\s+", " ", value).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def normalize_tier(value: Any) -> str:
    text = str(value or "临时")
    return TIER_ALIASES.get(text, text)


def normalize_memory_row(row: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(row)
    normalized["memory_tier"] = normalize_tier(normalized.get("memory_tier"))
    return normalized


def static_summary(row: dict[str, Any], themes: list[dict[str, Any]] | None = None) -> str:
    """Return a low-sensitive summary for committed visualization data."""

    statement = str(row.get("statement") or "")
    sensitivity = row.get("sensitivity")
    category = row.get("category")
    tier = normalize_tier(row.get("memory_tier") or "unknown")
    theme_text = "、".join(theme["label"] for theme in (themes or [])[:2]) or "未归类主题"
    base = (
        f"静态图谱低敏摘要：层级={tier}；分类={category or 'unknown'}；"
        f"重要性={row.get('importance') or 'unknown'}；有效期={row.get('validity') or 'unknown'}；主题={theme_text}。"
    )
    if sensitivity in {"sensitive", "secret"} or category == "temporary_or_sensitive":
        match = REDACTED_HASH_RE.search(statement)
        suffix = f" redacted_source_hash={match.group(1)}" if match else ""
        return f"{base} 敏感/临时资料已脱敏，详情需走受控 fetch/proposal。{suffix}".strip()
    if sensitivity == "private":
        return f"{base} 私有原文不进入前端静态 snapshot，完整内容需由授权 agent 读取长期记忆库。"
    if row.get("memory_tier") == "核心画像":
        return truncate_label(statement, 240)
    return truncate_label(statement, 180)


def public_node_label(row: dict[str, Any], memory_id: str, day: date | None, themes: list[dict[str, Any]]) -> str:
    _ = day
    return display_node_label(row, memory_id, themes)


def display_node_label(row: dict[str, Any], memory_id: str, themes: list[dict[str, Any]]) -> str:
    tier = normalize_tier(row.get("memory_tier") or "临时")
    theme_label = display_theme_label(themes)
    keywords = keyword_candidates(row, tier, theme_label, themes)[:2]
    keyword_text = " / ".join(keywords) if keywords else category_label(row.get("category")) or memory_id
    return truncate_label(f"{tier} · {theme_label} · {keyword_text}", 96)


def display_theme_label(themes: list[dict[str, Any]]) -> str:
    if not themes:
        return "其他主题"
    label = str(themes[0].get("label") or themes[0].get("id") or "其他主题")
    return label.split("/")[0].strip() or label


def category_label(value: Any) -> str:
    text = str(value or "").strip()
    return CATEGORY_LABELS.get(text, text or "记忆")


def normalize_compare(value: str) -> str:
    return re.sub(r"[\s/·:_\-，。；、|]+", "", value.lower())


def keyword_candidates(row: dict[str, Any], tier: str, theme_label: str, themes: list[dict[str, Any]]) -> list[str]:
    theme_words = " ".join(
        [theme_label]
        + [str(theme.get("label") or "") for theme in themes]
        + [str(keyword) for theme in themes for keyword in theme.get("keywords", [])]
    )
    banned = normalize_compare(f"{tier} {theme_words} {row.get('memory_tier') or ''}")
    generic_tokens = {normalize_compare(item) for item in GENERIC_LABEL_TOKENS}
    source = " ".join(str(row.get(field, "")) for field in ("title", "statement", "category", "use_when", "reason"))
    source = re.sub(r"redacted_source_hash=[A-Za-z0-9_-]+", " ", source)
    source = re.sub(r"PRIVATE CORE DETAIL|SECRET DETAIL", " ", source, flags=re.I)
    tokens = [
        token.strip()
        for token in re.split(r"[\s，。；、|/·:：;,()（）\[\]【】]+", source)
        if 2 <= len(token.strip()) <= 18
    ]
    tokens.append(category_label(row.get("category")))
    output: list[str] = []
    seen: set[str] = set()
    for token in tokens:
        key = normalize_compare(token)
        if not key or key in seen or key in generic_tokens:
            continue
        if key in banned or banned in key:
            continue
        if re.fullmatch(r"\d{4}(?:-\d{2}){0,2}", token):
            continue
        seen.add(key)
        output.append(token)
    return output


def keyword_regex(keywords: Iterable[str]) -> re.Pattern[str]:
    return re.compile("|".join(re.escape(keyword) for keyword in keywords), re.I)


THEME_PATTERNS = [(theme, keyword_regex(theme["keywords"])) for theme in THEMES]


def classify_themes(row: dict[str, Any]) -> list[dict[str, Any]]:
    haystack = " ".join(
        str(row.get(field, ""))
        for field in ("statement", "title", "category", "memory_tier", "reason", "use_when")
    )
    matches = [theme for theme, pattern in THEME_PATTERNS if pattern.search(haystack)]
    if matches:
        return matches
    return [
        {
            "id": "uncategorized",
            "label": "其他待人工归类主题",
            "keywords": [],
            "color": "#94a3b8",
        }
    ]


def memory_weight(row: dict[str, Any]) -> float:
    tier_score = TIER_WEIGHT.get(normalize_tier(row.get("memory_tier")), 0.25)
    importance_score = IMPORTANCE_WEIGHT.get(row.get("importance"), 0.35)
    confidence_score = CONFIDENCE_WEIGHT.get(row.get("confidence"), 0.6)
    return round((tier_score * 0.5) + (importance_score * 0.3) + (confidence_score * 0.2), 4)


def roi_metrics(row: dict[str, Any], day: date | None) -> dict[str, Any]:
    today = datetime.now(UTC).date()
    recency_days = (today - day).days if day else None
    sensitivity_penalty = 0.35 if row.get("sensitivity") in {"sensitive", "secret"} else 0.1
    staleness_status = "unknown"
    if recency_days is not None:
        if row.get("validity") == "临时" and recency_days > 30:
            staleness_status = "stale_short_term"
        elif recency_days > 180:
            staleness_status = "needs_review"
        else:
            staleness_status = "current"
    decision_impact = 1 if row.get("category") == "decision" else 0
    leverage_score = round(max(0.0, memory_weight(row) + decision_impact * 0.15 - sensitivity_penalty), 4)
    tier = normalize_tier(row.get("memory_tier"))
    if tier == "核心画像":
        recommended_action = "keep_high_weight"
    elif tier == "一般":
        recommended_action = "review_for_project_linkage"
    elif staleness_status in {"stale_short_term", "needs_review"}:
        recommended_action = "keep_low_weight_or_refresh"
    else:
        recommended_action = "keep_as_context"
    return {
        "staleness_status": staleness_status,
        "leverage_score": leverage_score,
        "recommended_action": recommended_action,
    }


def visual_position(memory_id: str, theme_index: int, weight: float) -> dict[str, float]:
    angle = (theme_index / max(len(THEMES), 1)) * math.tau
    cluster_radius = 80 + (theme_index % 3) * 24
    jitter_angle = stable_unit(memory_id, "angle") * math.tau
    jitter_radius = 16 + stable_unit(memory_id, "radius") * 48
    depth = (stable_unit(memory_id, "depth") - 0.5) * 52
    weight_pull = 1 - min(max(weight, 0), 1) * 0.28
    return {
        "x": round(math.cos(angle) * cluster_radius * weight_pull + math.cos(jitter_angle) * jitter_radius, 4),
        "y": round(math.sin(angle) * cluster_radius * weight_pull + math.sin(jitter_angle) * jitter_radius, 4),
        "z": round(depth, 4),
    }


def period_keys(day: date) -> dict[str, str]:
    iso = day.isocalendar()
    return {
        "day": day.isoformat(),
        "week": f"{iso.year}-W{iso.week:02d}",
        "month": f"{day.year}-{day.month:02d}",
        "year": str(day.year),
    }


def blank_activity(day_key: str) -> dict[str, Any]:
    return {
        "date": day_key,
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
        "codex_session_count": 0,
        "activity_score": 0,
    }


def add_activity_score(item: dict[str, Any]) -> None:
    item["activity_score"] = (
        item["conversation_count"] * 5
        + item["message_count"]
        + item["memory_count"] * 3
        + item["candidate_count"]
        + item["decision_count"] * 4
        + item.get("tool_call_count", 0) * 2
        + item.get("error_event_count", 0)
        + item.get("abort_count", 0) * 2
    )


def activity_level(score: int, max_score: int) -> int:
    if score <= 0 or max_score <= 0:
        return 0
    return max(1, min(5, math.ceil((score / max_score) * 5)))


def score_quantiles(rows: list[dict[str, Any]]) -> dict[str, int]:
    scores = sorted(int(row["activity_score"]) for row in rows)
    if not scores:
        return {"p50": 0, "p75": 0, "p90": 0, "p95": 0}

    def pick(percentile: float) -> int:
        index = min(len(scores) - 1, max(0, math.ceil(percentile * len(scores)) - 1))
        return scores[index]

    return {"p50": pick(0.5), "p75": pick(0.75), "p90": pick(0.9), "p95": pick(0.95)}


def fill_daily_range(daily: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    if not daily:
        return []
    days = [date.fromisoformat(day_key) for day_key in daily]
    current = min(days)
    end = max(days)
    rows: list[dict[str, Any]] = []
    while current <= end:
        key = current.isoformat()
        item = daily.setdefault(key, blank_activity(key))
        add_activity_score(item)
        rows.append(item)
        current += timedelta(days=1)
    max_score = max((int(item["activity_score"]) for item in rows), default=0)
    for item in rows:
        item["activity_level"] = activity_level(int(item["activity_score"]), max_score)
    return rows


def aggregate_periods(daily: dict[str, dict[str, Any]], period: str) -> list[dict[str, Any]]:
    buckets: dict[str, dict[str, Any]] = {}
    for day_key, item in daily.items():
        parsed = date.fromisoformat(day_key)
        period_key = period_keys(parsed)[period]
        bucket = buckets.setdefault(period_key, blank_activity(period_key))
        for key, value in item.items():
            if key not in {"date", "activity_level"} and isinstance(value, int):
                bucket[key] += value
    for item in buckets.values():
        add_activity_score(item)
    rows = sorted(buckets.values(), key=lambda row: row["date"])
    max_score = max((int(item["activity_score"]) for item in rows), default=0)
    for item in rows:
        item["activity_level"] = activity_level(int(item["activity_score"]), max_score)
    return rows


def build_contribution(
    active_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    conversations: list[dict[str, Any]],
    codex_daily_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    daily: dict[str, dict[str, Any]] = {}

    for row in conversations:
        day = parse_date(row.get("updated_at") or row.get("created_at"))
        if not day:
            continue
        item = daily.setdefault(day.isoformat(), blank_activity(day.isoformat()))
        item["conversation_count"] += 1
        item["message_count"] += int(row.get("message_count") or 0)
        item["user_message_count"] += int(row.get("user_message_count") or 0)
        item["assistant_message_count"] += int(row.get("assistant_message_count") or 0)

    for row in active_rows:
        day = parse_date(row.get("date"))
        if not day:
            continue
        item = daily.setdefault(day.isoformat(), blank_activity(day.isoformat()))
        item["memory_count"] += 1
        if row.get("category") == "decision":
            item["decision_count"] += 1
        tier = normalize_tier(row.get("memory_tier"))
        if tier == "核心画像":
            item["core_memory_count"] += 1
        elif tier == "一般":
            item["mid_long_memory_count"] += 1
        else:
            item["short_memory_count"] += 1

    for row in candidate_rows:
        day = parse_date(row.get("date"))
        if not day:
            continue
        item = daily.setdefault(day.isoformat(), blank_activity(day.isoformat()))
        item["candidate_count"] += 1

    for row in codex_daily_rows or []:
        day = parse_date(row.get("date"))
        if not day:
            continue
        item = daily.setdefault(day.isoformat(), blank_activity(day.isoformat()))
        item["conversation_count"] += int(row.get("conversation_count") or 0)
        item["message_count"] += int(row.get("message_count") or 0)
        item["user_message_count"] += int(row.get("user_message_count") or 0)
        item["assistant_message_count"] += int(row.get("assistant_message_count") or 0)
        item["tool_call_count"] += int(row.get("tool_call_count") or 0)
        item["error_event_count"] += int(row.get("error_event_count") or 0)
        item["abort_count"] += int(row.get("abort_count") or 0)
        item["codex_session_count"] += int(row.get("conversation_count") or 0)

    daily_rows = fill_daily_range(daily)
    max_score = max((int(item["activity_score"]) for item in daily_rows), default=0)
    return {
        "metric_note": "conversation_activity combines OpenAI export manifest and real local Codex redacted session summaries; memory_activity is a derived-memory increment proxy. It is not token usage or active screen time.",
        "score_version": "activity_score.v2",
        "range_start": daily_rows[0]["date"] if daily_rows else "",
        "range_end": daily_rows[-1]["date"] if daily_rows else "",
        "max_activity_score": max_score,
        "quantiles": score_quantiles(daily_rows),
        "daily": daily_rows,
        "weekly": aggregate_periods(daily, "week"),
        "monthly": aggregate_periods(daily, "month"),
        "yearly": aggregate_periods(daily, "year"),
    }


def build_nodes_and_edges(
    active_rows: list[dict[str, Any]],
    source_snapshot_hash: str | None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    timeline: list[dict[str, Any]] = []
    theme_counts: Counter[str] = Counter()
    category_counts: Counter[str] = Counter()
    tier_counts: Counter[str] = Counter()

    for index, theme in enumerate(THEMES + [{"id": "uncategorized", "label": "其他待人工归类主题", "color": "#94a3b8"}]):
        nodes.append(
            {
                "id": f"theme:{theme['id']}",
                "kind": "theme",
                "label": theme["label"],
                "theme_id": theme["id"],
                "visual": {
                    "color": theme["color"],
                    "position": visual_position(theme["id"], index, 1.0),
                    "size": 13,
                    "brightness": 0.88,
                },
            }
        )

    for tier in sorted(TIER_ORDER, key=TIER_ORDER.get):
        nodes.append(
            {
                "id": f"tier:{slugify(tier)}",
                "kind": "tier",
                "label": tier,
                "visual": {"color": "#e2e8f0", "size": 9, "brightness": TIER_WEIGHT[tier]},
            }
        )

    memory_nodes: list[dict[str, Any]] = []
    indexed_rows = sorted(
        enumerate(active_rows),
        key=lambda item: (TIER_ORDER.get(normalize_tier(item[1].get("memory_tier")), 99), item[1].get("date", ""), item[1].get("id", "")),
    )
    for record_index, row in indexed_rows:
        memory_id = str(row.get("id") or stable_hash(json.dumps(row, ensure_ascii=False)))
        themes = classify_themes(row)
        primary_theme = themes[0]
        theme_index = next((i for i, theme in enumerate(THEMES) if theme["id"] == primary_theme["id"]), len(THEMES))
        weight = memory_weight(row)
        tier = normalize_tier(row.get("memory_tier"))
        category = row.get("category") or "unknown"
        day = parse_date(row.get("date"))
        node_id = f"memory:{memory_id}"
        display_statement = static_summary(row, themes)
        label_text = public_node_label(row, memory_id, day, themes)
        node = {
            "id": node_id,
            "kind": "memory",
            "label": truncate_label(label_text),
            "memory_id": memory_id,
            "statement": display_statement,
            "date": day.isoformat() if day else "",
            "data_source": row.get("data_source") or "memory_atlas",
            "source_label": row.get("source_label") or "Memory Atlas / OpenAI Export 记忆库",
            "memory_tier": tier,
            "category": category,
            "importance": row.get("importance") or "",
            "validity": row.get("validity") or "",
            "confidence": row.get("confidence") or "",
            "visual": {
                "cluster": primary_theme["id"],
                "color": primary_theme["color"],
                "position": visual_position(memory_id, theme_index, weight),
                "size": round(4 + weight * 8, 3),
                "brightness": round(CONFIDENCE_WEIGHT.get(row.get("confidence"), 0.6), 3),
                "orbit_radius": round(30 + (1 - weight) * 76, 3),
                "sensitive": row.get("sensitivity") in {"sensitive", "secret"},
                "ring": row.get("validity") or "",
            },
            "metrics": {"weight_score": weight, "roi": roi_metrics(row, day)},
        }
        nodes.append(node)
        memory_nodes.append(node)

        tier_counts[tier] += 1
        category_counts[category] += 1
        for theme in themes:
            theme_counts[theme["id"]] += 1
            edges.append(
                {
                    "id": f"edge:{node_id}:theme:{theme['id']}",
                    "source": node_id,
                    "target": f"theme:{theme['id']}",
                    "kind": "belongs_to_theme",
                    "weight": round(weight, 4),
                }
            )
        edges.append(
            {
                "id": f"edge:{node_id}:tier:{slugify(tier)}",
                "source": node_id,
                "target": f"tier:{slugify(tier)}",
                "kind": "has_tier",
                "weight": round(weight, 4),
            }
        )
        category_node_id = f"category:{slugify(category)}"
        if not any(node["id"] == category_node_id for node in nodes):
            nodes.append(
                {
                    "id": category_node_id,
                    "kind": "category",
                    "label": category,
                    "visual": {"color": "#d1d5db", "size": 7, "brightness": 0.62},
                }
            )
        edges.append(
            {
                "id": f"edge:{node_id}:{category_node_id}",
                "source": node_id,
                "target": category_node_id,
                "kind": "has_category",
                "weight": 0.35,
            }
        )
        if day:
            timeline.append(
                {
                    "date": day.isoformat(),
                    "node_id": node_id,
                    "memory_id": memory_id,
                    "label": truncate_label(label_text, 90),
                    "memory_tier": tier,
                    "category": category,
                    "importance": row.get("importance") or "",
                }
            )

    summary_rows: list[dict[str, Any]] = []
    for theme in THEMES + [{"id": "uncategorized", "label": "其他待人工归类主题", "color": "#94a3b8"}]:
        summary_rows.append(
            {
                "theme_id": theme["id"],
                "label": theme["label"],
                "count": theme_counts.get(theme["id"], 0),
                "color": theme["color"],
            }
        )

    metrics = [
        {"kind": "tier", "values": dict(tier_counts)},
        {"kind": "category", "values": dict(category_counts)},
        {"kind": "theme", "values": {row["theme_id"]: row["count"] for row in summary_rows}},
    ]
    return nodes, edges, sorted(timeline, key=lambda row: (row["date"], row["node_id"])), metrics, memory_nodes


def ensure_category_node(nodes: list[dict[str, Any]], category: str) -> str:
    category_node_id = f"category:{slugify(category)}"
    if not any(node["id"] == category_node_id for node in nodes):
        nodes.append(
            {
                "id": category_node_id,
                "kind": "category",
                "label": category,
                "visual": {"color": "#d1d5db", "size": 7, "brightness": 0.62},
            }
        )
    return category_node_id


def add_memory_like_node(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    timeline: list[dict[str, Any]],
    memory_nodes: list[dict[str, Any]],
    row: dict[str, Any],
    *,
    source_file: str,
    proposal_actions: list[str] | None = None,
) -> None:
    memory_id = str(row.get("id") or stable_hash(json.dumps(row, ensure_ascii=False)))
    themes = classify_themes(row)
    primary_theme = themes[0]
    theme_index = next((i for i, theme in enumerate(THEMES) if theme["id"] == primary_theme["id"]), len(THEMES))
    weight = memory_weight(row)
    tier = normalize_tier(row.get("memory_tier"))
    category = row.get("category") or "unknown"
    day = parse_date(row.get("date"))
    node_id = f"memory:{memory_id}"
    if any(node["id"] == node_id for node in nodes):
        return
    label_text = public_node_label(row, memory_id, day, themes)
    node = {
        "id": node_id,
        "kind": "memory",
        "label": truncate_label(label_text),
        "memory_id": memory_id,
        "statement": static_summary(row, themes),
        "date": day.isoformat() if day else "",
        "data_source": row.get("data_source") or "memory_atlas",
        "source_label": row.get("source_label") or "Memory Atlas / OpenAI Export 记忆库",
        "memory_tier": tier,
        "category": category,
        "importance": row.get("importance") or "",
        "validity": row.get("validity") or "",
        "confidence": row.get("confidence") or "",
        "visual": {
            "cluster": primary_theme["id"],
            "color": primary_theme["color"],
            "position": visual_position(memory_id, theme_index, weight),
            "size": round(4 + weight * 8, 3),
            "brightness": round(CONFIDENCE_WEIGHT.get(row.get("confidence"), 0.6), 3),
            "orbit_radius": round(30 + (1 - weight) * 76, 3),
            "sensitive": row.get("sensitivity") in {"sensitive", "secret"},
            "ring": row.get("validity") or "",
        },
        "metrics": {
            "weight_score": weight,
            "roi": roi_metrics(row, day),
        },
    }
    nodes.append(node)
    memory_nodes.append(node)
    for theme in themes:
        edges.append(
            {
                "id": f"edge:{node_id}:theme:{theme['id']}",
                "source": node_id,
                "target": f"theme:{theme['id']}",
                "kind": "belongs_to_theme",
                "weight": round(weight, 4),
            }
        )
    edges.append(
        {
            "id": f"edge:{node_id}:tier:{slugify(tier)}",
            "source": node_id,
            "target": f"tier:{slugify(tier)}",
            "kind": "has_tier",
            "weight": round(weight, 4),
        }
    )
    category_node_id = ensure_category_node(nodes, category)
    edges.append(
        {
            "id": f"edge:{node_id}:{category_node_id}",
            "source": node_id,
            "target": category_node_id,
            "kind": "has_category",
            "weight": 0.35,
        }
    )
    if day:
        timeline.append(
            {
                "date": day.isoformat(),
                "node_id": node_id,
                "memory_id": memory_id,
                "label": truncate_label(label_text, 90),
                "memory_tier": tier,
                "category": category,
                "importance": row.get("importance") or "",
            }
        )


def codex_session_to_memory_row(row: dict[str, Any]) -> dict[str, Any]:
    topics = [str(item.get("label")) for item in row.get("topics", []) if item.get("label")]
    signals = [str(item.get("label")) for item in row.get("preference_signals", []) if item.get("label")]
    top_tools = [str(item.get("name")) for item in row.get("top_tools", [])[:5] if item.get("name")]
    activity = int(row.get("activity_score") or 0)
    importance = "高" if activity >= 120 or len(signals) >= 3 else "中" if activity >= 40 or signals else "低"
    tier = "一般" if importance in {"高", "中"} else "临时"
    title = f"Codex 会话 · {row.get('thread_name') or row.get('session_id')}"
    statement = (
        "真实 Codex 本地会话派生摘要："
        f"消息 {int(row.get('message_count') or 0)} 条，工具调用 {int(row.get('tool_call_count') or 0)} 次，"
        f"错误事件 {int(row.get('error_event_count') or 0)} 次；"
        f"主题：{'、'.join(topics[:5]) or '未检测到明确主题'}；"
        f"偏好信号：{'、'.join(signals[:5]) or '暂无'}；"
        f"常用工具：{'、'.join(top_tools) or '暂无'}。"
        "原始 transcript、明文 secret、cookies、session 文件和本地绝对路径不进入 GitHub 静态快照。"
    )
    return {
        "id": f"codex_session_{row.get('session_id') or stable_hash(json.dumps(row, ensure_ascii=False))}",
        "date": row.get("day") or row.get("updated_at") or row.get("started_at") or "",
        "title": title,
        "statement": statement,
        "memory_tier": tier,
        "category": "codex_development_record" if int(row.get("tool_call_count") or 0) else "codex_usage_record",
        "importance": importance,
        "validity": "项目结束前" if importance == "低" else "半年",
        "confidence": "high" if int(row.get("message_count") or 0) >= 10 else "medium",
        "sensitivity": "derived",
        "retrieval_weight": "high" if importance == "高" else "medium" if importance == "中" else "low",
        "evidence_count": int(row.get("message_count") or 0),
        "source_kind": "codex_local_session_redacted_summary",
        "data_source": "codex",
        "source_label": "Codex 本地数据",
        "use_when": "分析用户在 Codex 中的真实工作方式、交互强度、项目推进、工具偏好和交付标准。",
        "reason": "由本地 Codex session 派生摘要生成，不包含原始全文。",
        "usage": {
            "activity_score": activity,
            "message_count": int(row.get("message_count") or 0),
            "user_message_count": int(row.get("user_message_count") or 0),
            "assistant_message_count": int(row.get("assistant_message_count") or 0),
            "tool_call_count": int(row.get("tool_call_count") or 0),
            "error_event_count": int(row.get("error_event_count") or 0),
            "abort_count": int(row.get("abort_count") or 0),
        },
    }


def recommendation_to_memory_row(item: dict[str, Any], group: str) -> dict[str, Any]:
    title = str(item.get("title") or item.get("id") or "Codex 建议")
    return {
        "id": f"codex_recommendation_{group}_{item.get('id') or slugify(title)}",
        "date": datetime.now(UTC).date().isoformat(),
        "title": f"{'Memory' if group == 'memory' else 'Meta Data'} · {title}",
        "statement": str(item.get("statement") or ""),
        "memory_tier": "核心画像" if group == "memory" else "一般",
        "category": "codex_personalization" if group == "memory" else "codex_agent_metadata",
        "importance": item.get("importance") or "高",
        "validity": "长期",
        "confidence": item.get("confidence") or "medium",
        "sensitivity": "derived",
        "retrieval_weight": "high",
        "evidence_count": int(item.get("evidence_count") or 0),
        "source_kind": "codex_agent_recommendation",
        "data_source": "codex",
        "source_label": "Codex 本地数据",
        "use_when": item.get("scope") or "ChatGPT / Codex / future agents",
        "reason": item.get("reason") or "由 Codex 本地行为信号聚合生成。",
        "usage": {"evidence_count": int(item.get("evidence_count") or 0)},
    }


def add_codex_context(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    timeline: list[dict[str, Any]],
    memory_nodes: list[dict[str, Any]],
    codex_sessions: list[dict[str, Any]],
    codex_recommendations: dict[str, Any],
) -> None:
    for row in codex_sessions:
        add_memory_like_node(
            nodes,
            edges,
            timeline,
            memory_nodes,
            codex_session_to_memory_row(row),
            source_file=CODEX_SESSION_SOURCE,
        )
    for group_key in ("memory", "meta_data"):
        section = codex_recommendations.get(group_key, {})
        current = section.get("current", []) if isinstance(section, dict) else []
        for item in current:
            if isinstance(item, dict):
                add_memory_like_node(
                    nodes,
                    edges,
                    timeline,
                    memory_nodes,
                    recommendation_to_memory_row(item, "memory" if group_key == "memory" else "meta"),
                    source_file=CODEX_RECOMMENDATION_SOURCE,
                    proposal_actions=["propose_update", "propose_accept_recommendation", "propose_note"],
                )


def build_metrics_from_memory_nodes(memory_nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    tier_counts: Counter[str] = Counter()
    category_counts: Counter[str] = Counter()
    theme_counts: Counter[str] = Counter()
    for node in memory_nodes:
        tier_counts[normalize_tier(node.get("memory_tier"))] += 1
        category_counts[str(node.get("category") or "unknown")] += 1
        theme_counts[str(node.get("visual", {}).get("cluster") or "uncategorized")] += 1
    return [
        {"kind": "tier", "values": dict(tier_counts)},
        {"kind": "category", "values": dict(category_counts)},
        {"kind": "theme", "values": dict(theme_counts)},
    ]


def parse_markdown_headings(path: Path, kind: str, prefix: str, source_file: str) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    _ = source_file
    nodes: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
        match = re.match(r"^(#{2,3})\s+(.+?)\s*$", line)
        if not match:
            continue
        label = match.group(2).strip()
        if not label or label.lower() in {"project index", "decision log", "timeline"}:
            continue
        day = ""
        date_match = re.match(r"(\d{4}-\d{2}-\d{2})\s+-\s+(.+)", label)
        if date_match:
            day = date_match.group(1)
            label = date_match.group(2).strip()
        node_id = f"{prefix}:{slugify(label)[:90]}:{line_number}"
        nodes.append(
            {
                "id": node_id,
                "kind": kind,
                "label": truncate_label(label, 100),
                "date": day,
                "visual": {"color": "#f5d0fe", "size": 8, "brightness": 0.68},
            }
        )
    return nodes


def add_document_context(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    timeline: list[dict[str, Any]],
    memory_nodes: list[dict[str, Any]],
    database_dir: Path,
) -> None:
    specs = [
        ("project", "project", database_dir / "data/derived/project_index/PROJECT_INDEX.md", "project_membership"),
        ("decision", "decision", database_dir / "data/derived/decision_log/DECISION_LOG.md", "decision_related_to"),
        ("timeline_event", "event", database_dir / "data/derived/timeline/TIMELINE.md", "timeline_event_for"),
    ]
    theme_ids = {node["id"]: node for node in nodes if node.get("kind") == "theme"}
    for kind, prefix, path, edge_kind in specs:
        doc_nodes = parse_markdown_headings(path, kind, prefix, str(path.relative_to(database_dir)))
        nodes.extend(doc_nodes)
        for doc_node in doc_nodes:
            pseudo_row = {"statement": doc_node["label"], "title": doc_node["label"], "category": kind}
            themes = classify_themes(pseudo_row)
            for theme in themes:
                theme_id = f"theme:{theme['id']}"
                if theme_id in theme_ids:
                    edges.append(
                        {
                            "id": f"edge:{doc_node['id']}:{theme_id}",
                            "source": doc_node["id"],
                            "target": theme_id,
                            "kind": "mentions_topic",
                            "weight": 0.58,
                        }
                    )
            for memory_node in memory_nodes:
                if memory_node.get("visual", {}).get("cluster") in {theme["id"] for theme in themes}:
                    edges.append(
                        {
                            "id": f"edge:{memory_node['id']}:{doc_node['id']}",
                            "source": memory_node["id"],
                            "target": doc_node["id"],
                            "kind": edge_kind,
                            "weight": 0.32,
                        }
                    )
            if doc_node.get("date"):
                timeline.append(
                    {
                        "date": doc_node["date"],
                        "node_id": doc_node["id"],
                        "memory_id": "",
                        "label": doc_node["label"],
                        "memory_tier": kind,
                        "category": kind,
                        "importance": "中" if kind == "decision" else "低",
                    }
                )


def load_latest_candidates(database_dir: Path) -> list[dict[str, Any]]:
    candidate_dir = database_dir / "data/memory/candidates"
    if not candidate_dir.exists():
        return []
    candidates = sorted(
        candidate_dir.glob("*.memory_candidates.jsonl"),
        key=lambda path: CANDIDATE_RUN_RE.search(path.name).group(1) if CANDIDATE_RUN_RE.search(path.name) else "",
    )
    if not candidates:
        return []
    return read_jsonl(candidates[-1])


def build_memory_atlas(database_dir: Path) -> dict[str, Any]:
    active_path = database_dir / ACTIVE_MEMORY_SOURCE
    registry_path = database_dir / DATA_SOURCE_REGISTRY_SOURCE
    manifest_path = database_dir / "data/processed/conversations/conversation_manifest.jsonl"
    project_index_path = database_dir / "data/derived/project_index/PROJECT_INDEX.md"
    decision_log_path = database_dir / "data/derived/decision_log/DECISION_LOG.md"
    timeline_path = database_dir / "data/derived/timeline/TIMELINE.md"
    codex_session_path = database_dir / CODEX_SESSION_SOURCE
    codex_daily_path = database_dir / CODEX_DAILY_SOURCE
    codex_recommendation_path = database_dir / CODEX_RECOMMENDATION_SOURCE

    active_rows = [normalize_memory_row(row) for row in read_jsonl(active_path)]
    candidate_rows = [normalize_memory_row(row) for row in load_latest_candidates(database_dir)]
    conversations = read_jsonl(manifest_path)
    codex_sessions = read_jsonl(codex_session_path)
    codex_daily = read_jsonl(codex_daily_path)
    codex_recommendations = read_json(codex_recommendation_path)
    data_source_registry = load_data_source_registry(database_dir)
    registered_sources = registry_source_map(data_source_registry)
    active_source_hash = sha256_file(active_path)
    nodes, edges, memory_timeline, metric_rows, memory_node_rows = build_nodes_and_edges(active_rows, active_source_hash)
    add_document_context(nodes, edges, memory_timeline, memory_node_rows, database_dir)
    add_codex_context(nodes, edges, memory_timeline, memory_node_rows, codex_sessions, codex_recommendations)
    memory_timeline = sorted(memory_timeline, key=lambda row: (row["date"], row["node_id"]))
    metric_rows = build_metrics_from_memory_nodes(memory_node_rows)
    contribution = build_contribution(active_rows, candidate_rows, conversations, codex_daily)

    source_counts = Counter(str(node.get("data_source") or "memory_atlas") for node in memory_node_rows)
    source_latest: dict[str, str] = {}
    for node in memory_node_rows:
        source_id = str(node.get("data_source") or "memory_atlas")
        node_date = str(node.get("date") or "")
        if node_date and node_date > source_latest.get(source_id, ""):
            source_latest[source_id] = node_date
    fallback_sources = {
        "memory_atlas": {
            "id": "memory_atlas",
            "label": "ChatGPT",
            "description": "ChatGPT / OpenAI export 派生的长期记忆、项目索引、决策日志、时间线和对话记录摘要。",
            "platform": "openai_export_derived_memory",
            "status": "active",
            "ingestion_status": "active_redacted_derived_data",
            "record_types": ["active_memory", "candidate_memory", "decision", "project_context", "timeline_event"],
        },
        "codex": {
            "id": "codex",
            "label": "Codex",
            "description": "真实 Codex session、工具调用、偏好信号和 agent personalization 建议的脱敏派生摘要。",
            "platform": "codex_local_derived_behavior",
            "status": "active",
            "ingestion_status": "active_real_local_redacted_summary",
            "record_types": ["codex_session_summary", "daily_activity", "agent_recommendation", "behavior_signal"],
        },
    }
    source_activity_count = {
        "memory_atlas": len(conversations),
        "codex": len(codex_sessions),
    }
    ordered_source_ids = ["memory_atlas", "codex"]
    ordered_source_ids.extend(
        source_id
        for source_id, source in registered_sources.items()
        if source.get("status") == "active" and source_id not in ordered_source_ids
    )
    ordered_source_ids.extend(source_id for source_id, count in source_counts.items() if count > 0 and source_id not in ordered_source_ids)
    data_sources = [
        {
            "id": "all",
            "label": "总数据源",
            "description": "所有数据来源放在一起的合并视图。",
            "platform": "merged",
            "status": "active",
            "ingestion_status": "merged_redacted_derived_data",
            "record_types": [],
            "node_count": len(memory_node_rows),
            "activity_count": len(contribution["daily"]),
            "latest_date": contribution["range_end"],
        }
    ]
    for source_id in ordered_source_ids:
        source = registered_sources.get(source_id) or fallback_sources.get(source_id) or {
            "id": source_id,
            "label": source_id,
            "description": "自动识别的数据源；建议补充到 config/data_sources/source_registry.json。",
            "platform": "unregistered",
            "status": "active" if source_counts.get(source_id, 0) > 0 else "planned",
            "ingestion_status": "unregistered_derived_data",
            "record_types": [],
        }
        data_sources.append(
            source_summary(
                source,
                node_count=source_counts.get(source_id, 0),
                activity_count=source_activity_count.get(source_id, 0),
                latest_date=source_latest.get(source_id, ""),
            )
        )

    overview = {
        "active_memory_count": len(active_rows),
        "candidate_count_latest_snapshot": len(candidate_rows),
        "conversation_count": len(conversations),
        "codex_session_count": len(codex_sessions),
        "node_count": len(nodes),
        "edge_count": len(edges),
        "memory_node_count": sum(1 for node in nodes if node["kind"] == "memory"),
        "theme_node_count": sum(1 for node in nodes if node["kind"] == "theme"),
        "generated_at": datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
    }

    return {
        "schema_version": "memory_atlas.v1",
        "overview": overview,
        "source_contract": {
            "mode": "public_redacted_read_only_visualization",
            "export_profile": "access_preview",
            "source_files": {
                "active_memory": str(active_path.relative_to(database_dir)),
                "data_source_registry": str(registry_path.relative_to(database_dir)),
                "conversation_manifest": str(manifest_path.relative_to(database_dir)),
                "project_index": str(project_index_path.relative_to(database_dir)),
                "decision_log": str(decision_log_path.relative_to(database_dir)),
                "timeline": str(timeline_path.relative_to(database_dir)),
                "codex_session_manifest": str(codex_session_path.relative_to(database_dir)),
                "codex_daily_activity": str(codex_daily_path.relative_to(database_dir)),
                "codex_agent_recommendations": str(codex_recommendation_path.relative_to(database_dir)),
            },
            "data_source_registry": {
                "schema_version": data_source_registry.get("schema_version", ""),
                "contract_version": data_source_registry.get("contract_version", ""),
                "registered_source_count": len(registered_sources),
                "active_source_ids": [
                    source_id for source_id, source in registered_sources.items() if source.get("status") == "active"
                ],
                "planned_source_ids": [
                    source_id for source_id, source in registered_sources.items() if source.get("status") == "planned"
                ],
                "canonical_required_fields": data_source_registry.get("canonical_event_contract", {}).get("required_fields", []),
                "mock_policy": data_source_registry.get("canonical_event_contract", {})
                .get("privacy_contract", {})
                .get("mock_policy", ""),
            },
            "writeback_policy": {
                "frontend_can_request_writeback": True,
                "writeback_must_use_proposals": True,
                "proposal_dir": "data/memory/change_proposals",
                "history_dir": "data/memory/history",
                "rollback_unit": "git_commit_or_memory_version",
                "proposal_schema_version": PROPOSAL_SCHEMA_VERSION,
                "editable_fields": EDITABLE_MEMORY_FIELDS,
                "frontend_payload_contract": {
                    "target_ref": "memory_id",
                    "allowed_payload": ["action", "memory_id", "requested_changes", "reason", "client_note"],
                    "forbidden_payload": ["source paths", "record indexes", "client supplied conflict tokens"],
                },
                "conflict_detection": [
                    "controlled write layer reloads current active memory before applying a proposal",
                    "controlled write layer computes current target fingerprint internally",
                    "proposal application must create git/history rollback state before active memory changes",
                ],
                "direct_frontend_mutation_of_active_memory": False,
            },
        },
        "visual_layers": {
            "primary": "galaxy",
            "secondary": ["notion_map", "roi_dashboard", "obsidian_graph", "timeline", "contribution_grid", "summary_iteration"],
            "navigation": "left_sidebar",
        },
        "nodes": nodes,
        "edges": edges,
        "timeline": memory_timeline,
        "contribution": contribution,
        "data_sources": data_sources,
        "agent_recommendations": codex_recommendations
        or {
            "schema_version": "codex_agent_recommendations.empty",
            "memory": {"current": [], "added": [], "modified": [], "deleted": []},
            "meta_data": {"current": [], "added": [], "modified": [], "deleted": []},
        },
        "metrics": metric_rows,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build Memory Atlas visualization data.")
    parser.add_argument("--database-dir", type=Path, default=Path("."), help="OpenAIDatabase repository root.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Output JSON path, relative to database dir unless absolute.")
    args = parser.parse_args(argv)

    database_dir = args.database_dir.resolve()
    output_path = args.output if args.output.is_absolute() else database_dir / args.output
    atlas = build_memory_atlas(database_dir)
    write_json(output_path, atlas)
    print(
        json.dumps(
            {
                "status": "PASS",
                "output": str(output_path),
                "nodes": atlas["overview"]["node_count"],
                "edges": atlas["overview"]["edge_count"],
                "active_memory": atlas["overview"]["active_memory_count"],
                "conversation_count": atlas["overview"]["conversation_count"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
