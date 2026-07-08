#!/usr/bin/env python3
"""Build Memory Atlas S06 P3 opportunity leads from clusters and low-value loops."""

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
LOW_VALUE_PATH = Path("data/derived/behavior_intelligence/low_value_loops.json")
OUTPUT_PATH = Path("data/derived/behavior_intelligence/opportunities.json")
TASK_ID = "MA-V12-S06P3"
ACCEPTANCE_ID = "ACC-MA-V12-S06P3"
STATUS = "phase_s06_p3_opportunity_discovery_completed_pending_s06_review"
OPPORTUNITY_TYPES = ["automation", "productization", "template", "compounding", "defer"]
MAX_OPPORTUNITIES = 12


class OpportunityBuildError(RuntimeError):
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


def load_inputs(
    database_dir: Path,
    events_path: Path,
    clusters_path: Path,
    low_value_path: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    events_full_path = database_dir / events_path
    clusters_full_path = database_dir / clusters_path
    low_value_full_path = database_dir / low_value_path
    for path, label in [
        (events_full_path, "events"),
        (clusters_full_path, "clusters"),
        (low_value_full_path, "low-value loops"),
    ]:
        if not path.exists():
            raise OpportunityBuildError(f"{label} input missing: {path.relative_to(database_dir)}")
    events_payload = json.loads(events_full_path.read_text(encoding="utf-8"))
    clusters_payload = json.loads(clusters_full_path.read_text(encoding="utf-8"))
    low_value_payload = json.loads(low_value_full_path.read_text(encoding="utf-8"))
    event_by_id: dict[str, dict[str, Any]] = {}
    for event in events_payload.get("events") or []:
        if not isinstance(event, dict) or not event.get("event_id"):
            raise OpportunityBuildError("events must contain event_id objects")
        event_by_id[str(event["event_id"])] = event
    cluster_by_id: dict[str, dict[str, Any]] = {}
    for collection in ("topic_clusters", "hierarchy_clusters"):
        for cluster in clusters_payload.get(collection) or []:
            if not cluster.get("evidence_refs"):
                raise OpportunityBuildError(f"cluster {cluster.get('cluster_id')} missing evidence_refs")
            cluster_by_id[str(cluster.get("cluster_id"))] = cluster
    if not low_value_payload.get("loop_clusters"):
        raise OpportunityBuildError("low-value input must contain loop_clusters")
    return events_payload, clusters_payload, low_value_payload, event_by_id, cluster_by_id


def loop_events(loop: dict[str, Any], event_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for event_id in loop.get("representative_event_ids") or []:
        event = event_by_id.get(str(event_id))
        if event:
            rows.append(event)
    return rows


def loop_tasks(loop: dict[str, Any]) -> list[str]:
    return [normalize_text(task) for task in loop.get("filter_dimensions", {}).get("task") or []]


def loop_months(loop: dict[str, Any]) -> list[str]:
    return [str(month) for month in loop.get("observed_time_range", {}).get("months") or []]


def output_types(events: list[dict[str, Any]]) -> set[str]:
    return {normalize_text(event.get("output_type")) for event in events}


def item_by_loop_id(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(item.get("loop_id")): item for item in items if item.get("loop_id")}


def signal_candidates(
    loop: dict[str, Any],
    debt: dict[str, Any] | None,
    half_life: dict[str, Any] | None,
    events: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    label = normalize_text(loop.get("label_zh"))
    label_lower = label.lower()
    tasks = loop_tasks(loop)
    months = loop_months(loop)
    outputs = output_types(events)
    event_count = int(loop.get("event_count") or len(events) or 1)
    loop_type = str(loop.get("loop_type") or "")
    half_life_days = int((half_life or {}).get("action_half_life_days") or 0)
    candidates: list[dict[str, Any]] = []

    def add(opportunity_type: str, reason: str, next_step: str, score: int, defer_reason: str | None = None) -> None:
        candidates.append({
            "opportunity_type": opportunity_type,
            "reason": reason,
            "next_step_zh": next_step,
            "score": max(1, min(100, score)),
            "defer_reason_zh": defer_reason,
            "opportunity_half_life_days": None if opportunity_type == "defer" else max(7, half_life_days or 14),
        })

    if (
        loop_type == "scope_creep"
        or "automation" in tasks
        or any(term in label for term in ["自动化", "同步", "流程", "门禁", "运行"])
        or any(term in label_lower for term in ["atlasctl", "backup", "sync"])
    ):
        add(
            "automation",
            "反复出现的跨任务或流程型工作，可先抽象成脚本、检查器或运行门禁候选",
            "选一个最小重复步骤，写成 dry-run 脚本或 validator，不做大范围平台化。",
            55 + event_count * 3 + len(tasks) * 4,
        )
    if (
        "Memory Atlas" in label
        or "OpenAIDatabase" in label
        or any(term in label for term in ["报告", "可视化", "入口", "看板"])
        or ("engineering" in tasks and event_count >= 3)
    ):
        add(
            "productization",
            "该簇已有明确对象和可交付形态，适合作为产品化入口或稳定功能候选",
            "先定义一个用户可见结果和验收命令，只产品化已反复验证的最小路径。",
            50 + event_count * 4,
        )
    if (
        loop_type in {"repeated_rework", "discussion_without_landing"}
        or any(term in label for term in ["说明", "报告", "复盘", "模板"])
        or outputs <= {"未标注"} | {"unknown"}
    ):
        add(
            "template",
            "重复返工或反复讨论说明可被模板、清单或 run contract 收口",
            "提炼一个固定模板：目标、证据、停止条件、下一步，先用于下一次同类任务。",
            48 + event_count * 4 + len(months) * 3,
        )
    if (
        loop_type == "repeated_rework"
        or len(months) >= 2
        or any(term in label for term in ["AI", "agent", "记忆", "知识", "工作流"])
    ):
        add(
            "compounding",
            "该簇跨时间重复出现，若形成可复用资产，会比单次处理更有复利价值",
            "把本次产物固化成可复跑的 validator、参数说明或恢复入口，而不是只写一次性总结。",
            46 + event_count * 3 + len(months) * 4,
        )
    if loop_type in {"over_optimization", "scope_creep", "discussion_without_landing"}:
        close_question = normalize_text((debt or {}).get("suggested_closure_question"), "先明确 owner、交付件和停止条件。")
        add(
            "defer",
            "当前证据显示仍有范围扩张、过度优化或讨论未落地信号，应先暂缓扩大投入",
            "先回答 Decision Debt 收口问题；未回答前只保留候选，不转成执行任务。",
            45 + event_count * 3,
            defer_reason=f"为什么不是现在：{close_question} 若没有明确答案，就先暂缓，不把候选机会变成压力清单。",
        )
    return candidates


def make_opportunity(
    loop: dict[str, Any],
    cluster: dict[str, Any] | None,
    debt: dict[str, Any] | None,
    half_life: dict[str, Any] | None,
    events: list[dict[str, Any]],
    candidate: dict[str, Any],
) -> dict[str, Any]:
    opportunity_type = candidate["opportunity_type"]
    label = normalize_text(loop.get("label_zh"))
    evidence_refs = first_evidence_refs([loop, debt or {}, half_life or {}, cluster or {}, *events])
    if not evidence_refs:
        raise OpportunityBuildError(f"opportunity source loop {loop.get('loop_id')} has no evidence_refs")
    opportunity_id = f"opp_{opportunity_type}_{stable_hash(str(loop.get('loop_id')) + opportunity_type)}"
    defer_reason = candidate.get("defer_reason_zh")
    half_life_days = candidate.get("opportunity_half_life_days")
    summary = (
        f"候选机会：{label}。依据低价值循环 {loop.get('loop_type')}、"
        f"{loop.get('event_count')} 条事件和 {len(evidence_refs)} 条证据引用，识别为"
        f" {opportunity_type} 方向。该线索只用于探索排序，不是必须执行任务。"
    )
    why_not_now_reason = defer_reason or (
        "为什么不是现在：先验证最小下一步是否能形成可复用产物；没有 owner、验收命令或明确收益前不扩大投入。"
    )
    result: dict[str, Any] = {
        "opportunity_id": opportunity_id,
        "opportunity_type": opportunity_type,
        "source_loop_id": loop.get("loop_id"),
        "source_cluster_id": loop.get("source_cluster_id"),
        "source_debt_id": (debt or {}).get("debt_id"),
        "label_zh": label,
        "summary_zh": summary,
        "evidence_reason": candidate["reason"],
        "next_step_zh": candidate["next_step_zh"],
        "score": candidate["score"],
        "confidence": "medium" if int(candidate["score"]) < 75 else "high",
        "pressure_control": "candidate_only_not_required_work",
        "representative_event_ids": loop.get("representative_event_ids") or [],
        "observed_time_range": loop.get("observed_time_range") or {},
        "evidence_refs": evidence_refs,
        "why_not_now_card": {
            "card_id": f"why_not_now_{stable_hash(opportunity_id)}",
            "reason_zh": why_not_now_reason,
            "defer_until_signal_zh": "出现明确 owner、最小交付件、验收命令和停止条件后再升级为执行项。",
            "not_pressure_list": True,
            "evidence_refs": evidence_refs[:5],
        },
    }
    if half_life_days:
        result["opportunity_half_life_days"] = half_life_days
    if defer_reason:
        result["defer_reason_zh"] = defer_reason
    return result


def select_opportunities(opportunities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sorted_items = sorted(opportunities, key=lambda item: (-int(item["score"]), item["opportunity_type"], item["opportunity_id"]))
    selected: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for required_type in OPPORTUNITY_TYPES:
        for item in sorted_items:
            if item["opportunity_type"] == required_type and item["opportunity_id"] not in seen_ids:
                selected.append(item)
                seen_ids.add(item["opportunity_id"])
                break
    for item in sorted_items:
        if len(selected) >= MAX_OPPORTUNITIES:
            break
        if item["opportunity_id"] in seen_ids:
            continue
        selected.append(item)
        seen_ids.add(item["opportunity_id"])
    return sorted(selected, key=lambda item: (-int(item["score"]), item["opportunity_type"], item["opportunity_id"]))


def build_opportunities(
    database_dir: Path,
    dry_run: bool = False,
    generated_at: str | None = None,
    output_path: Path = OUTPUT_PATH,
    events_path: Path = EVENTS_PATH,
    clusters_path: Path = CLUSTERS_PATH,
    low_value_path: Path = LOW_VALUE_PATH,
) -> dict[str, Any]:
    database_dir = database_dir.resolve()
    generated_at = generated_at or now_utc()
    events_payload, clusters_payload, low_value_payload, event_by_id, cluster_by_id = load_inputs(
        database_dir,
        events_path,
        clusters_path,
        low_value_path,
    )
    debt_by_loop = item_by_loop_id(low_value_payload.get("decision_debt_ledger") or [])
    half_life_by_loop = item_by_loop_id(low_value_payload.get("action_half_life") or [])
    opportunities: list[dict[str, Any]] = []
    for loop in low_value_payload.get("loop_clusters") or []:
        events = loop_events(loop, event_by_id)
        cluster = cluster_by_id.get(str(loop.get("source_cluster_id")))
        debt = debt_by_loop.get(str(loop.get("loop_id")))
        half_life = half_life_by_loop.get(str(loop.get("loop_id")))
        for candidate in signal_candidates(loop, debt, half_life, events):
            opportunities.append(make_opportunity(loop, cluster, debt, half_life, events, candidate))
    opportunities = select_opportunities(opportunities)
    payload: dict[str, Any] = {
        "schema_version": "memory_atlas_opportunities.v1",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "status": STATUS,
        "generated_at": generated_at,
        "dry_run": dry_run,
        "writes_files": not dry_run,
        "input_paths": [events_path.as_posix(), clusters_path.as_posix(), low_value_path.as_posix()],
        "input_event_task_id": events_payload.get("task_id"),
        "input_cluster_task_id": clusters_payload.get("task_id"),
        "input_low_value_task_id": low_value_payload.get("task_id"),
        "output_path": output_path.as_posix(),
        "opportunity_count": len(opportunities),
        "defer_card_count": sum(1 for item in opportunities if item.get("why_not_now_card")),
        "opportunity_types": sorted({item["opportunity_type"] for item in opportunities}),
        "selection_policy": {
            "max_opportunities": MAX_OPPORTUNITIES,
            "candidate_only_not_pressure_list": True,
        },
        "phase_boundary": {
            "does_not_use_external_economic_database": True,
            "does_not_output_psychological_diagnosis": True,
            "does_not_modify_raw": True,
            "does_not_create_infinite_pressure_list": True,
            "next_phase": "S06 Review",
        },
        "opportunity_clusters": opportunities,
    }
    validate_payload(payload)
    if not dry_run:
        output = database_dir / output_path
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def validate_payload(payload: dict[str, Any]) -> None:
    if payload.get("task_id") != TASK_ID or payload.get("acceptance_id") != ACCEPTANCE_ID:
        raise OpportunityBuildError("payload identity mismatch")
    blocked = ["心理诊断", "人格诊断", "抑郁", "焦虑症"]
    opportunity_types = set(payload.get("opportunity_types") or [])
    missing = [item for item in OPPORTUNITY_TYPES if item not in opportunity_types]
    if missing:
        raise OpportunityBuildError(f"missing opportunity types: {', '.join(missing)}")
    if int(payload.get("opportunity_count") or 0) > MAX_OPPORTUNITIES:
        raise OpportunityBuildError("opportunity output exceeds pressure-list cap")
    for item in payload.get("opportunity_clusters") or []:
        item_id = item.get("opportunity_id")
        summary = str(item.get("summary_zh") or "")
        if item.get("opportunity_type") not in OPPORTUNITY_TYPES:
            raise OpportunityBuildError(f"unknown opportunity_type: {item.get('opportunity_type')}")
        if "候选机会" not in summary:
            raise OpportunityBuildError(f"opportunity {item_id} summary must use candidate phrasing")
        if any(term in summary for term in blocked):
            raise OpportunityBuildError(f"opportunity {item_id} contains blocked diagnostic language")
        if not item.get("evidence_refs"):
            raise OpportunityBuildError(f"opportunity {item_id} missing evidence_refs")
        if not item.get("next_step_zh"):
            raise OpportunityBuildError(f"opportunity {item_id} missing next_step_zh")
        if int(item.get("opportunity_half_life_days") or 0) <= 0 and not item.get("defer_reason_zh"):
            raise OpportunityBuildError(f"opportunity {item_id} missing half-life or defer reason")
        card = item.get("why_not_now_card") or {}
        if not card.get("reason_zh") or card.get("not_pressure_list") is not True or not card.get("evidence_refs"):
            raise OpportunityBuildError(f"opportunity {item_id} has invalid why_not_now_card")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Memory Atlas S06 P3 opportunity discovery builder.")
    parser.add_argument("--database-dir", type=Path, default=ROOT)
    parser.add_argument("--events", type=Path, default=EVENTS_PATH)
    parser.add_argument("--clusters", type=Path, default=CLUSTERS_PATH)
    parser.add_argument("--low-value", type=Path, default=LOW_VALUE_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        payload = build_opportunities(
            args.database_dir,
            dry_run=args.dry_run,
            events_path=args.events,
            clusters_path=args.clusters,
            low_value_path=args.low_value,
            output_path=args.output,
        )
    except OpportunityBuildError as exc:
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
