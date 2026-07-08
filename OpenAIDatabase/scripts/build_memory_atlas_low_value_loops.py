#!/usr/bin/env python3
"""Build Memory Atlas S06 P2 low-value-loop candidates from S06 clusters."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EVENTS_PATH = Path("data/derived/behavior_intelligence/events.json")
CLUSTERS_PATH = Path("data/derived/behavior_intelligence/clusters.json")
OUTPUT_PATH = Path("data/derived/behavior_intelligence/low_value_loops.json")
TASK_ID = "MA-V12-S06P2"
ACCEPTANCE_ID = "ACC-MA-V12-S06P2"
STATUS = "phase_s06_p2_low_value_loops_completed_pending_s06_p3"
LOOP_TYPES = ["repeated_rework", "discussion_without_landing", "over_optimization", "scope_creep"]


class LowValueLoopBuildError(RuntimeError):
    pass


def now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def stable_hash(value: str, length: int = 12) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:length]


def normalize_text(value: Any, fallback: str = "未标注") -> str:
    text = str(value or "").strip()
    if not text or text.lower() in {"none", "null", "unknown", "nan"}:
        return fallback
    return text


def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def days_between(start: str | None, end: str | None) -> int:
    start_dt = parse_dt(start)
    end_dt = parse_dt(end)
    if not start_dt or not end_dt:
        return 0
    return max(0, (end_dt - start_dt).days)


def first_evidence_refs(items: list[dict[str, Any]], limit: int = 10) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in items:
        for ref in item.get("evidence_refs") or []:
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


def load_inputs(database_dir: Path, events_path: Path, clusters_path: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, dict[str, Any]]]:
    events_full_path = database_dir / events_path
    clusters_full_path = database_dir / clusters_path
    if not events_full_path.exists():
        raise LowValueLoopBuildError(f"events input missing: {events_path}")
    if not clusters_full_path.exists():
        raise LowValueLoopBuildError(f"clusters input missing: {clusters_path}")
    events_payload = json.loads(events_full_path.read_text(encoding="utf-8"))
    clusters_payload = json.loads(clusters_full_path.read_text(encoding="utf-8"))
    events = events_payload.get("events")
    if not isinstance(events, list):
        raise LowValueLoopBuildError("events input must contain an events list")
    event_by_id: dict[str, dict[str, Any]] = {}
    for event in events:
        if not isinstance(event, dict) or not event.get("event_id"):
            raise LowValueLoopBuildError("events must contain event_id objects")
        event_by_id[str(event["event_id"])] = event
    for cluster in (clusters_payload.get("topic_clusters") or []):
        if not cluster.get("evidence_refs"):
            raise LowValueLoopBuildError(f"cluster {cluster.get('cluster_id')} missing evidence_refs")
    return events_payload, clusters_payload, event_by_id


def event_rows(cluster: dict[str, Any], event_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for event_id in cluster.get("representative_event_ids") or []:
        event = event_by_id.get(str(event_id))
        if event:
            rows.append(event)
    return rows


def cluster_months(cluster: dict[str, Any]) -> list[str]:
    months = cluster.get("filter_dimensions", {}).get("time", {}).get("months") or []
    return [str(month) for month in months]


def cluster_tasks(cluster: dict[str, Any]) -> list[str]:
    return [normalize_text(task) for task in cluster.get("filter_dimensions", {}).get("task") or []]


def cluster_sources(cluster: dict[str, Any]) -> list[str]:
    return [normalize_text(source) for source in cluster.get("filter_dimensions", {}).get("source") or []]


def output_types(events: list[dict[str, Any]]) -> set[str]:
    return {normalize_text(event.get("output_type")) for event in events}


def score_signals(cluster: dict[str, Any], events: list[dict[str, Any]]) -> list[tuple[str, str, int]]:
    label = normalize_text(cluster.get("label_zh"), "")
    event_count = int(cluster.get("event_count") or len(events))
    months = cluster_months(cluster)
    tasks = cluster_tasks(cluster)
    sources = cluster_sources(cluster)
    outputs = output_types(events)
    label_lower = label.lower()
    signals: list[tuple[str, str, int]] = []

    if event_count >= 3 and (len(months) >= 2 or any(term in label for term in ["返工", "重做", "反复"])):
        signals.append(("repeated_rework", "多月多次出现，可能存在重复返工候选", min(95, 45 + event_count * 4 + len(months) * 5)))
    if event_count >= 3 and sources == ["chatgpt"] and outputs <= {"未标注"} | {"unknown"}:
        signals.append(("discussion_without_landing", "多次讨论但缺少代码、测试、报告或数据落地产物", min(90, 40 + event_count * 5 + len(months) * 5)))
    if event_count >= 3 and ("design" in tasks or "engineering" in tasks or "优化" in label or "optimization" in label_lower):
        signals.append(("over_optimization", "围绕设计或工程细节高频迭代，可能存在过度优化候选", min(88, 38 + event_count * 5 + len(tasks) * 4)))
    if event_count >= 3 and (len(tasks) >= 3 or len(sources) >= 2 or "scope" in label_lower or "范围" in label):
        signals.append(("scope_creep", "同一簇横跨多个任务或来源，可能存在 scope creep 候选", min(88, 35 + event_count * 4 + len(tasks) * 6 + len(sources) * 4)))
    return signals


def make_loop(cluster: dict[str, Any], events: list[dict[str, Any]], loop_type: str, reason: str, score: int) -> dict[str, Any]:
    label = normalize_text(cluster.get("label_zh"))
    time_info = cluster.get("filter_dimensions", {}).get("time", {})
    evidence_refs = first_evidence_refs([cluster, *events])
    if not evidence_refs:
        raise LowValueLoopBuildError(f"loop source cluster {cluster.get('cluster_id')} has no evidence_refs")
    loop_id = f"loop_{loop_type}_{stable_hash(str(cluster.get('cluster_id')))}"
    event_ids = [str(event.get("event_id")) for event in events if event.get("event_id")]
    summary = (
        f"候选低价值循环：{label}。依据 {cluster.get('event_count')} 条事件和"
        f" {len(evidence_refs)} 条证据引用，检测到 {reason}。"
        "该结论只用于工作流复盘，不做个人状态判断，也不生成无证重大结论。"
    )
    return {
        "loop_id": loop_id,
        "loop_type": loop_type,
        "source_cluster_id": cluster.get("cluster_id"),
        "label_zh": label,
        "summary_zh": summary,
        "evidence_reason": reason,
        "confidence": "medium" if score < 75 else "high",
        "score": score,
        "event_count": int(cluster.get("event_count") or len(events)),
        "representative_event_ids": event_ids[:8] or list(cluster.get("representative_event_ids") or [])[:8],
        "evidence_refs": evidence_refs,
        "filter_dimensions": cluster.get("filter_dimensions") or {},
        "observed_time_range": {
            "start": time_info.get("start"),
            "end": time_info.get("end"),
            "months": time_info.get("months") or [],
            "span_days": days_between(time_info.get("start"), time_info.get("end")),
        },
    }


def make_debt(loop: dict[str, Any]) -> dict[str, Any]:
    debt_id = f"debt_{stable_hash(loop['loop_id'])}"
    close_question_by_type = {
        "repeated_rework": "这组工作是否需要一次性定义完成标准、复用入口和停止条件？",
        "discussion_without_landing": "这组讨论是否需要明确 owner、交付件和最小下一步，否则归档为暂不推进？",
        "over_optimization": "这组优化是否已经超过当前决策价值，是否应设置质量上限？",
        "scope_creep": "这组范围是否需要拆回一个主目标和一个后续 backlog？",
    }
    return {
        "debt_id": debt_id,
        "loop_id": loop["loop_id"],
        "debt_type": loop["loop_type"],
        "decision_area": loop["label_zh"],
        "debt_signal": loop["evidence_reason"],
        "suggested_closure_question": close_question_by_type.get(loop["loop_type"], "是否需要明确下一步、owner 和停止条件？"),
        "status": "open_candidate",
        "evidence_refs": loop["evidence_refs"][:5],
    }


def half_life_days(loop: dict[str, Any]) -> int:
    span = int(loop.get("observed_time_range", {}).get("span_days") or 0)
    event_count = int(loop.get("event_count") or 1)
    if loop["loop_type"] == "discussion_without_landing":
        return max(7, min(45, span // max(event_count, 1) + 7))
    if loop["loop_type"] == "over_optimization":
        return max(3, min(21, span // max(event_count, 1) + 3))
    if loop["loop_type"] == "scope_creep":
        return max(7, min(30, span // 2 if span else 14))
    return max(7, min(60, span // 2 if span else 14))


def make_half_life(loop: dict[str, Any]) -> dict[str, Any]:
    days = half_life_days(loop)
    return {
        "half_life_id": f"half_life_{stable_hash(loop['loop_id'])}",
        "loop_id": loop["loop_id"],
        "loop_type": loop["loop_type"],
        "action_half_life_days": days,
        "interpretation_zh": (
            f"如果 {days} 天内没有形成明确交付件、owner 或停止条件，该候选循环的行动价值会快速衰减。"
        ),
        "last_evidence_at": loop.get("observed_time_range", {}).get("end"),
        "evidence_refs": loop["evidence_refs"][:5],
    }


def build_low_value_loops(
    database_dir: Path,
    dry_run: bool = False,
    generated_at: str | None = None,
    output_path: Path = OUTPUT_PATH,
    clusters_path: Path = CLUSTERS_PATH,
    events_path: Path = EVENTS_PATH,
) -> dict[str, Any]:
    database_dir = database_dir.resolve()
    generated_at = generated_at or now_utc()
    events_payload, clusters_payload, event_by_id = load_inputs(database_dir, events_path, clusters_path)
    loops: list[dict[str, Any]] = []
    for cluster in clusters_payload.get("topic_clusters") or []:
        rows = event_rows(cluster, event_by_id)
        for loop_type, reason, score in score_signals(cluster, rows):
            loops.append(make_loop(cluster, rows, loop_type, reason, score))
    loops = sorted(loops, key=lambda loop: (-loop["score"], loop["loop_type"], loop["loop_id"]))
    debt_ledger = [make_debt(loop) for loop in loops]
    half_life = [make_half_life(loop) for loop in loops]
    evidence_ref_count = sum(len(loop["evidence_refs"]) for loop in loops)
    payload: dict[str, Any] = {
        "schema_version": "memory_atlas_low_value_loops.v1",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "status": STATUS,
        "generated_at": generated_at,
        "dry_run": dry_run,
        "writes_files": not dry_run,
        "input_paths": [events_path.as_posix(), clusters_path.as_posix()],
        "input_event_task_id": events_payload.get("task_id"),
        "input_cluster_task_id": clusters_payload.get("task_id"),
        "output_path": output_path.as_posix(),
        "loop_cluster_count": len(loops),
        "decision_debt_count": len(debt_ledger),
        "action_half_life_count": len(half_life),
        "evidence_ref_count": evidence_ref_count,
        "loop_types": sorted({loop["loop_type"] for loop in loops}),
        "phase_boundary": {
            "does_not_generate_opportunity_cards": True,
            "does_not_rank_personal_traits": True,
            "does_not_output_psychological_diagnosis": True,
            "does_not_modify_raw": True,
            "next_phase": "S06 P3",
        },
        "loop_clusters": loops,
        "decision_debt_ledger": debt_ledger,
        "action_half_life": half_life,
    }
    validate_payload(payload)
    if not dry_run:
        output = database_dir / output_path
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def validate_payload(payload: dict[str, Any]) -> None:
    if payload.get("task_id") != TASK_ID or payload.get("acceptance_id") != ACCEPTANCE_ID:
        raise LowValueLoopBuildError("payload identity mismatch")
    blocked = ["心理诊断", "人格诊断", "抑郁", "焦虑症"]
    loop_ids = set()
    for loop in payload.get("loop_clusters") or []:
        loop_ids.add(loop.get("loop_id"))
        if loop.get("loop_type") not in LOOP_TYPES:
            raise LowValueLoopBuildError(f"unknown loop_type: {loop.get('loop_type')}")
        summary = str(loop.get("summary_zh") or "")
        if not summary or "候选" not in summary:
            raise LowValueLoopBuildError(f"loop {loop.get('loop_id')} summary must be candidate phrasing")
        if any(term in summary for term in blocked):
            raise LowValueLoopBuildError(f"loop {loop.get('loop_id')} contains blocked diagnostic language")
        if not loop.get("evidence_refs"):
            raise LowValueLoopBuildError(f"loop {loop.get('loop_id')} missing evidence_refs")
    for debt in payload.get("decision_debt_ledger") or []:
        if debt.get("loop_id") not in loop_ids:
            raise LowValueLoopBuildError(f"decision debt references unknown loop: {debt.get('loop_id')}")
        if not debt.get("evidence_refs") or not debt.get("suggested_closure_question"):
            raise LowValueLoopBuildError(f"decision debt {debt.get('debt_id')} missing evidence or closure question")
    for item in payload.get("action_half_life") or []:
        if item.get("loop_id") not in loop_ids:
            raise LowValueLoopBuildError(f"half-life references unknown loop: {item.get('loop_id')}")
        if int(item.get("action_half_life_days") or 0) <= 0 or not item.get("evidence_refs"):
            raise LowValueLoopBuildError(f"half-life {item.get('half_life_id')} missing days or evidence")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Memory Atlas S06 P2 low-value loop builder.")
    parser.add_argument("--database-dir", type=Path, default=ROOT)
    parser.add_argument("--clusters", type=Path, default=CLUSTERS_PATH)
    parser.add_argument("--events", type=Path, default=EVENTS_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        payload = build_low_value_loops(
            args.database_dir,
            dry_run=args.dry_run,
            clusters_path=args.clusters,
            events_path=args.events,
            output_path=args.output,
        )
    except LowValueLoopBuildError as exc:
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
