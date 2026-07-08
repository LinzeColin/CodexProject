#!/usr/bin/env python3
"""Build Memory Atlas S06 P1 behavior clusters from S05 canonical events."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EVENTS_PATH = Path("data/derived/behavior_intelligence/events.json")
OUTPUT_PATH = Path("data/derived/behavior_intelligence/clusters.json")
TASK_ID = "MA-V12-S06P1"
ACCEPTANCE_ID = "ACC-MA-V12-S06P1"
STATUS = "phase_s06_p1_cluster_builder_completed_pending_s06_p2"
SUPPORTED_FILTERS = ["source", "time", "project", "task", "language"]


class ClusterBuildError(RuntimeError):
    pass


def now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def stable_hash(value: str, length: int = 12) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:length]


def normalize_text(value: Any, fallback: str = "未标注") -> str:
    text = str(value or "").strip()
    if not text or text.lower() in {"none", "null", "unknown", "nan"}:
        return fallback
    return re.sub(r"\s+", " ", text)


def event_month(value: str | None) -> str:
    if not value:
        return "unknown"
    return value[:7] if len(value) >= 7 else "unknown"


def top_values(events: list[dict[str, Any]], field: str, limit: int = 6) -> list[str]:
    counts = Counter(normalize_text(event.get(field), "未标注") for event in events)
    return [value for value, _ in counts.most_common(limit)]


def first_evidence_refs(events: list[dict[str, Any]], limit: int = 10) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    seen: set[str] = set()
    for event in events:
        for ref in event.get("evidence_refs") or []:
            if not isinstance(ref, dict):
                continue
            ref_id = str(ref.get("ref_id") or json.dumps(ref, ensure_ascii=False, sort_keys=True))
            if ref_id in seen:
                continue
            seen.add(ref_id)
            refs.append(ref)
            if len(refs) >= limit:
                return refs
    return refs


def representative_event_ids(events: list[dict[str, Any]], limit: int = 8) -> list[str]:
    return [str(event.get("event_id")) for event in events[:limit] if event.get("event_id")]


def time_range(events: list[dict[str, Any]]) -> dict[str, str | None]:
    values = sorted(str(event.get("occurred_at")) for event in events if event.get("occurred_at"))
    return {
        "start": values[0] if values else None,
        "end": values[-1] if values else None,
        "months": sorted({event_month(value) for value in values}),
    }


def detect_theme(event: dict[str, Any]) -> tuple[str, str, str]:
    project = normalize_text(event.get("project"), "")
    topic = normalize_text(event.get("topic"), "")
    task_type = normalize_text(event.get("task_type"), "")
    combined = f"{project} {topic} {task_type}".lower()

    if project:
        return f"project:{project.lower()}", f"项目：{project}", "project"

    rules = [
        ("ai_memory_agent", "AI 记忆与 agent 工作流", ["memory", "atlas", "codex", "agent", "notion", "ai", "记忆", "智能体"]),
        ("business_management", "经营与管理决策", ["业务", "转型", "盈利", "公司", "管理", "现金流", "合作", "经营"]),
        ("finance_value", "财务与价值分析", ["财务", "finance", "发票", "成本", "收益", "roi", "预算", "资金"]),
        ("automation_workflow", "自动化与流程治理", ["自动化", "workflow", "钉钉", "kmfa", "审批", "同步", "备份", "流程"]),
        ("risk_governance", "风险、合规与治理", ["风险", "合规", "政策", "凭证", "审计", "治理", "安全", "合同"]),
        ("product_visualization", "产品、设计与可视化", ["产品", "设计", "ui", "ux", "可视化", "看板", "dashboard", "visual"]),
        ("local_operations", "本地系统与运行维护", ["mac", "本机", "本地", "app", "缓存", "内存", "运行", "安装"]),
    ]
    for key, label, keywords in rules:
        if any(keyword in combined for keyword in keywords):
            return f"theme:{key}", label, "keyword_theme"

    if task_type:
        return f"task:{task_type.lower()}", f"任务类型：{task_type}", "task_type"

    topic_fallback = topic[:18] if topic else "未标注主题"
    return f"topic:{topic_fallback.lower()}", f"主题：{topic_fallback}", "topic"


def make_summary(label: str, events: list[dict[str, Any]]) -> str:
    sources = "、".join(top_values(events, "source", limit=3))
    tasks = "、".join(top_values(events, "task_type", limit=3))
    languages = "、".join(top_values(events, "language", limit=3))
    months = "、".join(time_range(events)["months"][:4]) or "未知时间"
    return (
        f"该行为簇基于 {len(events)} 条带证据引用的事件，主要围绕「{label}」。"
        f"来源包含 {sources}，时间覆盖 {months}，常见任务类型为 {tasks}，语言以 {languages} 为主。"
        "该摘要只描述事件聚合，不做个人状态判断或无证重大结论。"
    )


def make_filter_dimensions(events: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "source": top_values(events, "source"),
        "time": time_range(events),
        "project": top_values(events, "project"),
        "task": top_values(events, "task_type"),
        "language": top_values(events, "language"),
    }


def make_topic_cluster(key: str, label: str, label_source: str, events: list[dict[str, Any]]) -> dict[str, Any]:
    events = sorted(events, key=lambda event: (event.get("occurred_at") or "", event.get("event_id") or ""))
    evidence_refs = first_evidence_refs(events)
    if not evidence_refs:
        raise ClusterBuildError(f"cluster {label} has no evidence refs")
    cluster_id = f"topic_{stable_hash(key)}"
    return {
        "cluster_id": cluster_id,
        "cluster_type": "topic",
        "level": 1,
        "label_zh": label,
        "label_source": label_source,
        "summary_zh": make_summary(label, events),
        "event_count": len(events),
        "representative_event_ids": representative_event_ids(events),
        "evidence_refs": evidence_refs,
        "filter_dimensions": make_filter_dimensions(events),
        "source_breakdown": dict(Counter(normalize_text(event.get("source")) for event in events)),
        "task_type_breakdown": dict(Counter(normalize_text(event.get("task_type")) for event in events)),
    }


def make_hierarchy_cluster(
    parent_key: str,
    label: str,
    events: list[dict[str, Any]],
    child_cluster_ids: list[str],
) -> dict[str, Any]:
    events = sorted(events, key=lambda event: (event.get("occurred_at") or "", event.get("event_id") or ""))
    evidence_refs = first_evidence_refs(events)
    if not evidence_refs:
        raise ClusterBuildError(f"hierarchy cluster {label} has no evidence refs")
    return {
        "cluster_id": f"hierarchy_{stable_hash(parent_key)}",
        "cluster_type": "hierarchy",
        "level": 0,
        "label_zh": label,
        "summary_zh": (
            f"该层级簇把 {len(child_cluster_ids)} 个主题簇汇总到「{label}」下，"
            f"共覆盖 {len(events)} 条有证据事件。它用于按 source/project/task/language 交叉探索，"
            "不替代后续低价值循环或机会判断。"
        ),
        "event_count": len(events),
        "child_cluster_ids": child_cluster_ids,
        "representative_event_ids": representative_event_ids(events),
        "evidence_refs": evidence_refs,
        "filter_dimensions": make_filter_dimensions(events),
    }


def load_events(database_dir: Path, events_path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    path = database_dir / events_path
    if not path.exists():
        raise ClusterBuildError(f"events input missing: {events_path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    events = payload.get("events")
    if not isinstance(events, list):
        raise ClusterBuildError("events input must contain an events list")
    for event in events:
        if not isinstance(event, dict):
            raise ClusterBuildError("event rows must be JSON objects")
        if not event.get("event_id"):
            raise ClusterBuildError("event missing event_id")
        if not event.get("evidence_refs"):
            raise ClusterBuildError(f"event {event.get('event_id')} missing evidence_refs")
    return payload, events


def make_active_filters(args: argparse.Namespace) -> dict[str, str | None]:
    return {
        "source": args.source,
        "time_from": args.time_from,
        "time_to": args.time_to,
        "project": args.project,
        "task": args.task,
        "language": args.language,
    }


def empty_filters() -> dict[str, str | None]:
    return {
        "source": None,
        "time_from": None,
        "time_to": None,
        "project": None,
        "task": None,
        "language": None,
    }


def event_matches(event: dict[str, Any], filters: dict[str, str | None]) -> bool:
    if filters["source"] and normalize_text(event.get("source")) != filters["source"]:
        return False
    if filters["project"] and normalize_text(event.get("project")) != filters["project"]:
        return False
    if filters["task"] and normalize_text(event.get("task_type")) != filters["task"]:
        return False
    if filters["language"] and normalize_text(event.get("language")) != filters["language"]:
        return False
    occurred_at = str(event.get("occurred_at") or "")
    if filters["time_from"] and occurred_at and occurred_at < filters["time_from"]:
        return False
    if filters["time_to"] and occurred_at and occurred_at > filters["time_to"]:
        return False
    return True


def filter_index(events: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "source": sorted({normalize_text(event.get("source")) for event in events}),
        "project": sorted({normalize_text(event.get("project")) for event in events}),
        "task": sorted({normalize_text(event.get("task_type")) for event in events}),
        "language": sorted({normalize_text(event.get("language")) for event in events}),
        "time": time_range(events),
    }


def build_clusters(
    database_dir: Path,
    dry_run: bool = False,
    generated_at: str | None = None,
    output_path: Path = OUTPUT_PATH,
    events_path: Path = EVENTS_PATH,
    active_filters: dict[str, str | None] | None = None,
) -> dict[str, Any]:
    database_dir = database_dir.resolve()
    generated_at = generated_at or now_utc()
    source_payload, all_events = load_events(database_dir, events_path)
    filters = {**empty_filters(), **(active_filters or {})}
    events = [event for event in all_events if event_matches(event, filters)]

    topic_groups: dict[str, dict[str, Any]] = {}
    for event in events:
        key, label, label_source = detect_theme(event)
        group = topic_groups.setdefault(key, {"label": label, "label_source": label_source, "events": []})
        group["events"].append(event)

    topic_clusters = [
        make_topic_cluster(key, group["label"], group["label_source"], group["events"])
        for key, group in sorted(topic_groups.items(), key=lambda item: (-len(item[1]["events"]), item[0]))
    ]

    topic_cluster_id_by_key = {
        key: f"topic_{stable_hash(key)}"
        for key in topic_groups
    }
    topic_cluster_by_event: dict[str, str] = {}
    for key, group in topic_groups.items():
        cluster_id = topic_cluster_id_by_key[key]
        for event in group["events"]:
            topic_cluster_by_event[str(event.get("event_id"))] = cluster_id

    hierarchy_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        project = normalize_text(event.get("project"), "未标注项目")
        task = normalize_text(event.get("task_type"), "未标注任务")
        source = normalize_text(event.get("source"))
        language = normalize_text(event.get("language"))
        hierarchy_groups[f"{source}|{project}|{task}|{language}"].append(event)

    hierarchy_clusters = []
    for key, group_events in sorted(hierarchy_groups.items(), key=lambda item: (-len(item[1]), item[0])):
        source, project, task, language = key.split("|", 3)
        child_ids = sorted({
            topic_cluster_by_event.get(str(event.get("event_id")))
            for event in group_events
            if topic_cluster_by_event.get(str(event.get("event_id")))
        })
        if not child_ids:
            continue
        hierarchy_clusters.append(make_hierarchy_cluster(key, f"{source} / {project} / {task} / {language}", group_events, child_ids))

    evidence_ref_count = sum(len(cluster["evidence_refs"]) for cluster in [*topic_clusters, *hierarchy_clusters])
    payload: dict[str, Any] = {
        "schema_version": "memory_atlas_behavior_clusters.v1",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "status": STATUS,
        "generated_at": generated_at,
        "dry_run": dry_run,
        "writes_files": not dry_run,
        "input_path": events_path.as_posix(),
        "input_event_task_id": source_payload.get("task_id"),
        "input_event_count": len(all_events),
        "filtered_event_count": len(events),
        "output_path": output_path.as_posix(),
        "cluster_count": len(topic_clusters) + len(hierarchy_clusters),
        "topic_cluster_count": len(topic_clusters),
        "hierarchy_cluster_count": len(hierarchy_clusters),
        "evidence_ref_count": evidence_ref_count,
        "filter_contract": {
            "supported_filters": SUPPORTED_FILTERS,
            "active_filters": filters,
            "filter_index": filter_index(all_events),
        },
        "phase_boundary": {
            "does_not_modify_raw": True,
            "does_not_identify_low_value_loops": True,
            "does_not_generate_opportunity_cards": True,
            "does_not_output_psychological_diagnosis": True,
            "next_phase": "S06 P2",
        },
        "topic_clusters": topic_clusters,
        "hierarchy_clusters": hierarchy_clusters,
    }
    validate_payload(payload)
    if not dry_run:
        output = database_dir / output_path
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def validate_payload(payload: dict[str, Any]) -> None:
    if payload.get("task_id") != TASK_ID or payload.get("acceptance_id") != ACCEPTANCE_ID:
        raise ClusterBuildError("payload identity mismatch")
    if payload.get("filtered_event_count", 0) > 0:
        if payload.get("topic_cluster_count", 0) <= 0:
            raise ClusterBuildError("missing topic clusters")
        if payload.get("hierarchy_cluster_count", 0) <= 0:
            raise ClusterBuildError("missing hierarchy clusters")
    blocked = ["心理诊断", "人格诊断", "抑郁", "焦虑症"]
    for collection_name in ("topic_clusters", "hierarchy_clusters"):
        clusters = payload.get(collection_name)
        if not isinstance(clusters, list):
            raise ClusterBuildError(f"{collection_name} must be a list")
        for cluster in clusters:
            summary = str(cluster.get("summary_zh") or "")
            if not summary:
                raise ClusterBuildError(f"{collection_name} cluster missing summary_zh")
            if any(term in summary for term in blocked):
                raise ClusterBuildError(f"{collection_name} cluster summary contains blocked diagnostic language")
            if not cluster.get("evidence_refs"):
                raise ClusterBuildError(f"{collection_name} cluster missing evidence_refs")
            dimensions = cluster.get("filter_dimensions") or {}
            for field in SUPPORTED_FILTERS:
                if field not in dimensions:
                    raise ClusterBuildError(f"{collection_name} cluster missing filter dimension {field}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Memory Atlas S06 P1 cluster builder.")
    parser.add_argument("--database-dir", type=Path, default=ROOT)
    parser.add_argument("--events", type=Path, default=EVENTS_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--source")
    parser.add_argument("--time-from")
    parser.add_argument("--time-to")
    parser.add_argument("--project")
    parser.add_argument("--task")
    parser.add_argument("--language")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        payload = build_clusters(
            args.database_dir,
            dry_run=args.dry_run,
            output_path=args.output,
            events_path=args.events,
            active_filters=make_active_filters(args),
        )
    except ClusterBuildError as exc:
        print(json.dumps({
            "status": "FAIL",
            "task_id": TASK_ID,
            "acceptance_id": ACCEPTANCE_ID,
            "reason": str(exc),
            "writes_files": False,
        }, ensure_ascii=False, indent=2, sort_keys=True))
        return 2
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
