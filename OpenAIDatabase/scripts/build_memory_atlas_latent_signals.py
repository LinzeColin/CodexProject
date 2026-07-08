#!/usr/bin/env python3
"""Build Memory Atlas S09 P1 falsifiable latent signals."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = Path("机器治理/行为智能模型/latent_signals.v1_2_s09_p1.json")
EVENTS_PATH = Path("data/derived/behavior_intelligence/events.json")
CLUSTERS_PATH = Path("data/derived/behavior_intelligence/clusters.json")
LOW_VALUE_PATH = Path("data/derived/behavior_intelligence/low_value_loops.json")
OPPORTUNITIES_PATH = Path("data/derived/behavior_intelligence/opportunities.json")
OUTPUT_PATH = Path("data/derived/behavior_intelligence/latent_signals.json")
TASK_ID = "MA-V12-S09P1"
ACCEPTANCE_ID = "ACC-MA-V12-S09P1"
STATUS = "phase_s09_p1_latent_signals_completed_pending_s09_p2"
REQUIRED_FIELDS = {
    "claim_zh",
    "supporting_evidence_refs",
    "contradicting_evidence_refs",
    "alternative_explanation_zh",
    "confidence",
    "evidence_strength_badge",
    "next_validation_zh",
}


class LatentSignalBuildError(RuntimeError):
    pass


def now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def stable_hash(value: str, length: int = 12) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:length]


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def load_json(path: Path, label: str) -> dict[str, Any]:
    if not path.exists():
        raise LatentSignalBuildError(f"{label} missing: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise LatentSignalBuildError(f"{label} must be a JSON object: {path}")
    return payload


def normalize_text(value: Any, fallback: str = "未标注") -> str:
    text = str(value or "").strip()
    if not text or text.lower() in {"none", "null", "unknown", "nan"}:
        return fallback
    return text


def unique_evidence_refs(items: list[dict[str, Any]], limit: int = 8) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in items:
        for ref in as_list(item.get("evidence_refs")):
            if not isinstance(ref, dict):
                continue
            ref_id = str(ref.get("ref_id") or json.dumps(ref, ensure_ascii=False, sort_keys=True))
            if ref_id in seen:
                continue
            seen.add(ref_id)
            refs.append(ref)
            if len(refs) >= limit:
                return refs
        why_card = item.get("why_not_now_card")
        if isinstance(why_card, dict):
            for ref in as_list(why_card.get("evidence_refs")):
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


def source_count(refs: list[dict[str, Any]]) -> int:
    return len({str(ref.get("source_id") or "unknown") for ref in refs if isinstance(ref, dict)})


def observed_month_count(items: list[dict[str, Any]]) -> int:
    months: set[str] = set()
    for item in items:
        observed = item.get("observed_time_range")
        if isinstance(observed, dict):
            months.update(str(month) for month in as_list(observed.get("months")))
        dimensions = item.get("filter_dimensions")
        if isinstance(dimensions, dict):
            time_info = dimensions.get("time")
            if isinstance(time_info, dict):
                months.update(str(month) for month in as_list(time_info.get("months")))
    return len(months)


def evidence_badge(support_refs: list[dict[str, Any]], supporting_items: list[dict[str, Any]]) -> str:
    if len(support_refs) >= 4 and source_count(support_refs) >= 2 and observed_month_count(supporting_items) >= 2:
        return "A"
    if len(support_refs) >= 3:
        return "B"
    if len(support_refs) >= 1:
        return "C"
    return "D"


def confidence_for_badge(badge: str, support_refs: list[dict[str, Any]], contradict_refs: list[dict[str, Any]], config: dict[str, Any]) -> float:
    max_by_badge = ((config.get("confidence_policy") or {}).get("badge_max_confidence") or {})
    cap = float(max_by_badge.get(badge, 0.45))
    base_by_badge = {"A": 0.68, "B": 0.58, "C": 0.42, "D": 0.25}
    value = base_by_badge.get(badge, 0.25) + min(0.1, len(support_refs) * 0.015) - min(0.08, len(contradict_refs) * 0.01)
    return round(max(0.1, min(cap, value)), 2)


def confidence_label(confidence: float) -> str:
    if confidence >= 0.75:
        return "medium_high"
    if confidence >= 0.55:
        return "medium"
    if confidence >= 0.35:
        return "low_medium"
    return "low"


def by_field(items: list[dict[str, Any]], field_name: str) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        value = normalize_text(item.get(field_name), "")
        if value:
            grouped.setdefault(value, []).append(item)
    return grouped


def loops_by_type(loops_payload: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    return by_field([item for item in as_list(loops_payload.get("loop_clusters")) if isinstance(item, dict)], "loop_type")


def opportunities_by_type(opportunities_payload: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    return by_field([item for item in as_list(opportunities_payload.get("opportunity_clusters")) if isinstance(item, dict)], "opportunity_type")


def top_items(items: list[dict[str, Any]], limit: int = 4) -> list[dict[str, Any]]:
    return sorted(items, key=lambda item: (-int(item.get("score") or 0), normalize_text(item.get("label_zh")), normalize_text(item.get("opportunity_id") or item.get("loop_id"))))[:limit]


def labels(items: list[dict[str, Any]], limit: int = 3) -> str:
    seen: list[str] = []
    for item in items:
        label = normalize_text(item.get("label_zh"))
        if label not in seen:
            seen.append(label)
        if len(seen) >= limit:
            break
    return "、".join(seen) if seen else "未标注主题"


def make_signal(
    *,
    signal_key: str,
    claim_type: str,
    claim_zh: str,
    supporting_items: list[dict[str, Any]],
    contradicting_items: list[dict[str, Any]],
    support_summary_zh: str,
    contradict_summary_zh: str,
    alternative_explanation_zh: str,
    next_validation_zh: str,
    config: dict[str, Any],
) -> dict[str, Any] | None:
    support_refs = unique_evidence_refs(supporting_items, limit=8)
    contradict_refs = unique_evidence_refs(contradicting_items, limit=5)
    if not support_refs or not contradict_refs:
        return None
    badge = evidence_badge(support_refs, supporting_items)
    confidence = confidence_for_badge(badge, support_refs, contradict_refs, config)
    signal_id = f"latent_{signal_key}_{stable_hash(claim_zh)}"
    return {
        "signal_id": signal_id,
        "claim_type": claim_type,
        "claim_zh": claim_zh,
        "supporting_evidence": {
            "summary_zh": support_summary_zh,
            "refs": support_refs,
        },
        "supporting_evidence_refs": support_refs,
        "contradicting_evidence": {
            "summary_zh": contradict_summary_zh,
            "refs": contradict_refs,
        },
        "contradicting_evidence_refs": contradict_refs,
        "alternative_explanation_zh": alternative_explanation_zh,
        "confidence": confidence,
        "confidence_label": confidence_label(confidence),
        "evidence_strength_badge": badge,
        "next_validation_zh": next_validation_zh,
        "not_psychological_diagnosis": True,
        "not_personality_label": True,
        "falsifiable": True,
    }


def candidate_signals(config: dict[str, Any], loops_payload: dict[str, Any], opportunities_payload: dict[str, Any]) -> list[dict[str, Any]]:
    loops = loops_by_type(loops_payload)
    opportunities = opportunities_by_type(opportunities_payload)
    automation = top_items(opportunities.get("automation", []), 4)
    compounding = top_items(opportunities.get("compounding", []), 4)
    productization = top_items(opportunities.get("productization", []), 4)
    templates = top_items(opportunities.get("template", []), 4)
    defer = top_items(opportunities.get("defer", []), 4)
    rework = top_items(loops.get("repeated_rework", []), 4)
    discussion = top_items(loops.get("discussion_without_landing", []), 4)
    over_optimization = top_items(loops.get("over_optimization", []), 4)
    scope_creep = top_items(loops.get("scope_creep", []), 4)

    raw_signals = [
        make_signal(
            signal_key="automation_reuse",
            claim_type="workflow_reuse_candidate",
            claim_zh=f"可能存在把「{labels(automation)}」收束为 dry-run 脚本、validator 或固定运行门禁的复用空间。",
            supporting_items=automation,
            contradicting_items=defer or discussion or scope_creep,
            support_summary_zh="automation 类型候选机会重复出现，并且已有最小下一步可落到脚本或 validator。",
            contradict_summary_zh="defer 或讨论未落地信号说明这些候选不应直接扩大为执行清单。",
            alternative_explanation_zh="这些重复也可能只是阶段性升级包带来的临时治理需求，而不是长期自动化对象。",
            next_validation_zh="下一轮只选一个最高分候选，验证是否能用一个 dry-run 命令减少重复操作；若不能，就降级为记录项。",
            config=config,
        ),
        make_signal(
            signal_key="discussion_artifact",
            claim_type="artifact_closure_candidate",
            claim_zh=f"可能存在把「{labels(discussion)}」先压缩成单个交付件、验收命令或停止条件的收口空间。",
            supporting_items=discussion,
            contradicting_items=productization or automation or templates,
            support_summary_zh="discussion_without_landing 循环显示多次讨论但交付形态不稳定。",
            contradict_summary_zh="productization、automation 或 template 机会说明部分讨论已经能被转成产物候选。",
            alternative_explanation_zh="讨论可能是在补齐需求边界，短期没有落地产物不一定代表价值低。",
            next_validation_zh="下次出现同类主题时，先要求一个可验收文件或命令；若无法定义，就归档为暂不推进候选。",
            config=config,
        ),
        make_signal(
            signal_key="scope_contract",
            claim_type="scope_boundary_candidate",
            claim_zh=f"可能存在「{labels(scope_creep)}」在多来源、多任务之间扩张时，需要更早锁定 run contract 的信号。",
            supporting_items=scope_creep,
            contradicting_items=automation or compounding or productization,
            support_summary_zh="scope_creep 循环跨任务或来源出现，提示范围边界需要提前固定。",
            contradict_summary_zh="automation、compounding 或 productization 机会也可能要求跨模块协同，不能简单视为范围问题。",
            alternative_explanation_zh="跨来源扩张可能是正常集成工作，而不是边界失控；需要用验收项验证。",
            next_validation_zh="下一次同类 run 开始前写出非目标列表；若新增需求不在非目标例外内，就进入下一 phase 而非本轮扩张。",
            config=config,
        ),
        make_signal(
            signal_key="asset_compounding",
            claim_type="reusable_asset_candidate",
            claim_zh=f"可能存在把「{labels(compounding)}」固化为可恢复资产的复利空间。",
            supporting_items=compounding,
            contradicting_items=over_optimization or defer,
            support_summary_zh="compounding 候选机会显示多次复用的知识、流程或运行证据可以沉淀为资产。",
            contradict_summary_zh="over_optimization 或 defer 信号说明过早沉淀可能增加维护负担。",
            alternative_explanation_zh="可复用资产的价值可能来自当前升级密度，后续频率下降时维护收益会变低。",
            next_validation_zh="只沉淀能被另一 agent 从 GitHub 恢复并运行的最小资产；无法复跑的说明先不扩写。",
            config=config,
        ),
        make_signal(
            signal_key="quality_ceiling",
            claim_type="quality_ceiling_candidate",
            claim_zh=f"可能存在「{labels(over_optimization)}」需要先设质量上限，而不是继续增加细节优化的信号。",
            supporting_items=over_optimization,
            contradicting_items=productization or templates or automation,
            support_summary_zh="over_optimization 循环提示局部质量细节可能占用过多迭代预算。",
            contradict_summary_zh="productization、template 或 automation 机会说明部分细节优化可能会转化成稳定复用价值。",
            alternative_explanation_zh="看似过度的细节处理可能是为了满足真实验收标准，不能只按迭代次数判断。",
            next_validation_zh="下一次同类优化前写明质量上限和停止条件；达到上限后只修阻断验收的问题。",
            config=config,
        ),
    ]
    return [signal for signal in raw_signals if signal]


def validate_config(config: dict[str, Any]) -> None:
    if config.get("task_id") != TASK_ID or config.get("acceptance_id") != ACCEPTANCE_ID:
        raise LatentSignalBuildError("latent signal config identity mismatch")
    configured_fields = set(as_list(config.get("required_signal_fields")))
    missing = sorted(REQUIRED_FIELDS - configured_fields)
    if missing:
        raise LatentSignalBuildError(f"latent signal config missing fields: {', '.join(missing)}")
    badges = {str(item.get("badge")) for item in as_list(config.get("evidence_strength_badges")) if isinstance(item, dict)}
    if badges != {"A", "B", "C", "D"}:
        raise LatentSignalBuildError("latent signal config must define Evidence Strength Badge A-D")
    boundary = config.get("scope_boundary") if isinstance(config.get("scope_boundary"), dict) else {}
    if boundary.get("raw_mutation") is not False:
        raise LatentSignalBuildError("S09 P1 must not mutate raw")
    if boundary.get("psychological_diagnosis") is not False:
        raise LatentSignalBuildError("S09 P1 must not output psychological diagnosis")
    if boundary.get("personality_label") is not False:
        raise LatentSignalBuildError("S09 P1 must not output personality labels")
    if boundary.get("self_iteration_suggestions") != "deferred_to_s09_p2":
        raise LatentSignalBuildError("S09 P1 must defer self iteration suggestions to S09 P2")
    if boundary.get("decision_debt_ledger") != "deferred_to_s09_p3":
        raise LatentSignalBuildError("S09 P1 must defer decision debt ledger to S09 P3")


def validate_inputs(events: dict[str, Any], clusters: dict[str, Any], loops: dict[str, Any], opportunities: dict[str, Any]) -> None:
    expected = [
        (events, "MA-V12-S05P3", "ACC-MA-V12-S05P3", "events"),
        (clusters, "MA-V12-S06P1", "ACC-MA-V12-S06P1", "clusters"),
        (loops, "MA-V12-S06P2", "ACC-MA-V12-S06P2", "low-value loops"),
        (opportunities, "MA-V12-S06P3", "ACC-MA-V12-S06P3", "opportunities"),
    ]
    for payload, task_id, acceptance_id, label in expected:
        if payload.get("task_id") != task_id or payload.get("acceptance_id") != acceptance_id:
            raise LatentSignalBuildError(f"{label} identity mismatch")


def validate_signal(signal: dict[str, Any], config: dict[str, Any]) -> list[str]:
    bad_items: list[str] = []
    signal_id = signal.get("signal_id")
    for field in REQUIRED_FIELDS:
        if signal.get(field) in (None, "", []):
            bad_items.append(f"{signal_id}:missing_{field}")
    if signal.get("evidence_strength_badge") not in {"A", "B", "C", "D"}:
        bad_items.append(f"{signal_id}:invalid_badge")
    confidence = float(signal.get("confidence") or 0)
    max_confidence = float(((config.get("confidence_policy") or {}).get("max_confidence") or 0.85))
    if confidence < 0 or confidence > max_confidence:
        bad_items.append(f"{signal_id}:confidence_out_of_range")
    if confidence >= 0.75 and signal.get("evidence_strength_badge") not in set((config.get("confidence_policy") or {}).get("high_confidence_requires_badge") or []):
        bad_items.append(f"{signal_id}:high_confidence_without_strong_badge")
    if not signal.get("supporting_evidence_refs") or not signal.get("contradicting_evidence_refs"):
        bad_items.append(f"{signal_id}:missing_two_sided_evidence")
    blocked_terms = [str(term) for term in as_list(config.get("blocked_output_terms"))]
    text_fields = [
        "claim_zh",
        "alternative_explanation_zh",
        "next_validation_zh",
        "claim_type",
    ]
    joined = " ".join(str(signal.get(field) or "") for field in text_fields)
    if any(term in joined for term in blocked_terms):
        bad_items.append(f"{signal_id}:blocked_term")
    if signal.get("not_psychological_diagnosis") is not True:
        bad_items.append(f"{signal_id}:psychological_boundary_missing")
    if signal.get("not_personality_label") is not True:
        bad_items.append(f"{signal_id}:personality_boundary_missing")
    if signal.get("falsifiable") is not True:
        bad_items.append(f"{signal_id}:not_falsifiable")
    return bad_items


def validate_payload(payload: dict[str, Any], config: dict[str, Any]) -> None:
    if payload.get("task_id") != TASK_ID or payload.get("acceptance_id") != ACCEPTANCE_ID:
        raise LatentSignalBuildError("latent signal payload identity mismatch")
    if payload.get("status") != STATUS:
        raise LatentSignalBuildError("latent signal payload status mismatch")
    signals = [item for item in as_list(payload.get("latent_signals")) if isinstance(item, dict)]
    if len(signals) < 4:
        raise LatentSignalBuildError("latent signal payload must contain at least four signals")
    bad_items: list[str] = []
    for signal in signals:
        bad_items.extend(validate_signal(signal, config))
    boundary = payload.get("phase_boundary") if isinstance(payload.get("phase_boundary"), dict) else {}
    if boundary.get("does_not_create_self_iteration_suggestions") is not True:
        bad_items.append("phase_boundary:self_iteration_not_deferred")
    if boundary.get("does_not_create_decision_debt_ledger") is not True:
        bad_items.append("phase_boundary:decision_debt_not_deferred")
    if boundary.get("does_not_modify_raw") is not True:
        bad_items.append("phase_boundary:raw_mutation_missing")
    if boundary.get("next_phase") != "S09 P2":
        bad_items.append("phase_boundary:next_phase_not_s09p2")
    if bad_items:
        raise LatentSignalBuildError("; ".join(bad_items))


def build_latent_signals(
    database_dir: Path,
    *,
    dry_run: bool = False,
    generated_at: str | None = None,
    output_path: Path = OUTPUT_PATH,
    config_path: Path = CONFIG_PATH,
    events_path: Path = EVENTS_PATH,
    clusters_path: Path = CLUSTERS_PATH,
    low_value_path: Path = LOW_VALUE_PATH,
    opportunities_path: Path = OPPORTUNITIES_PATH,
) -> dict[str, Any]:
    database_dir = database_dir.resolve()
    config = load_json(database_dir / config_path, "latent signal config")
    events = load_json(database_dir / events_path, "events")
    clusters = load_json(database_dir / clusters_path, "clusters")
    loops = load_json(database_dir / low_value_path, "low-value loops")
    opportunities = load_json(database_dir / opportunities_path, "opportunities")
    validate_config(config)
    validate_inputs(events, clusters, loops, opportunities)

    signals = candidate_signals(config, loops, opportunities)
    signals = sorted(signals, key=lambda item: (-float(item["confidence"]), item["signal_id"]))[:8]
    badge_counts: dict[str, int] = {}
    for signal in signals:
        badge = str(signal["evidence_strength_badge"])
        badge_counts[badge] = badge_counts.get(badge, 0) + 1
    payload: dict[str, Any] = {
        "schema_version": "memory_atlas_latent_signals.v1_2_s09_p1",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "status": STATUS,
        "generated_at": generated_at or now_utc(),
        "dry_run": dry_run,
        "writes_files": not dry_run,
        "config_path": config_path.as_posix(),
        "output_path": output_path.as_posix(),
        "input_paths": [
            events_path.as_posix(),
            clusters_path.as_posix(),
            low_value_path.as_posix(),
            opportunities_path.as_posix(),
        ],
        "input_task_ids": {
            "events": events.get("task_id"),
            "clusters": clusters.get("task_id"),
            "low_value_loops": loops.get("task_id"),
            "opportunities": opportunities.get("task_id"),
        },
        "signal_count": len(signals),
        "evidence_strength_badge_counts": badge_counts,
        "latent_signals": signals,
        "safety_audit": {
            "psychological_diagnosis_output_blocked": True,
            "personality_label_output_blocked": True,
            "high_confidence_without_evidence_blocked": True,
            "two_sided_evidence_required": True,
            "bad_items": [],
        },
        "phase_boundary": {
            "does_not_output_psychological_diagnosis": True,
            "does_not_output_personality_label": True,
            "does_not_modify_raw": True,
            "does_not_upload_github_main": True,
            "does_not_create_self_iteration_suggestions": True,
            "proposal_expiry_deferred_to": "S09 P2",
            "does_not_create_decision_debt_ledger": True,
            "decision_debt_ledger_deferred_to": "S09 P3",
            "next_phase": "S09 P2",
        },
    }
    validate_payload(payload, config)
    if not dry_run:
        output = database_dir / output_path
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Memory Atlas S09 P1 latent signal builder.")
    parser.add_argument("--database-dir", type=Path, default=ROOT)
    parser.add_argument("--config", type=Path, default=CONFIG_PATH)
    parser.add_argument("--events", type=Path, default=EVENTS_PATH)
    parser.add_argument("--clusters", type=Path, default=CLUSTERS_PATH)
    parser.add_argument("--low-value", type=Path, default=LOW_VALUE_PATH)
    parser.add_argument("--opportunities", type=Path, default=OPPORTUNITIES_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        payload = build_latent_signals(
            args.database_dir,
            dry_run=args.dry_run,
            output_path=args.output,
            config_path=args.config,
            events_path=args.events,
            clusters_path=args.clusters,
            low_value_path=args.low_value,
            opportunities_path=args.opportunities,
        )
    except LatentSignalBuildError as exc:
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
