#!/usr/bin/env python3
"""Build Memory Atlas S08 P1 Codex/Agent collaboration quality report."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = Path("机器治理/行为智能模型/agent_collaboration_metrics.v1_2_s08_p1.json")
EVENTS_PATH = Path("data/derived/behavior_intelligence/events.json")
CLUSTERS_PATH = Path("data/derived/behavior_intelligence/clusters.json")
LOW_VALUE_LOOPS_PATH = Path("data/derived/behavior_intelligence/low_value_loops.json")
OPPORTUNITIES_PATH = Path("data/derived/behavior_intelligence/opportunities.json")
INFORMATION_ROI_PATH = Path("data/derived/information_roi/information_roi_gate.json")
OUTPUT_PATH = Path("data/derived/agent_collaboration/agent_collaboration_quality_report.json")
TASK_ID = "MA-V12-S08P1"
ACCEPTANCE_ID = "ACC-MA-V12-S08P1"
STATUS = "phase_s08_p1_collaboration_metrics_completed_pending_s08_p2"


class AgentCollaborationBuildError(RuntimeError):
    pass


def now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def load_json(path: Path, label: str) -> dict[str, Any]:
    if not path.exists():
        raise AgentCollaborationBuildError(f"{label} missing: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise AgentCollaborationBuildError(f"{label} must be a JSON object: {path}")
    return payload


def has_cjk(value: Any) -> bool:
    return any("\u3400" <= char <= "\u9fff" for char in str(value or ""))


def clamp_ratio(value: float) -> float:
    return max(0.0, min(1.0, value))


def clamp_score(value: float) -> int:
    return int(round(max(0.0, min(100.0, value))))


def ratio(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return clamp_ratio(numerator / denominator)


def validate_config(config: dict[str, Any]) -> None:
    if config.get("task_id") != TASK_ID or config.get("acceptance_id") != ACCEPTANCE_ID:
        raise AgentCollaborationBuildError("agent collaboration config identity mismatch")
    boundary = config.get("scope_boundary") or {}
    if boundary.get("raw_mutation") is not False:
        raise AgentCollaborationBuildError("agent collaboration config must not mutate raw")
    if boundary.get("multi_agent_system_implementation") is not False:
        raise AgentCollaborationBuildError("S08 P1 must not implement a multi-agent system")
    if boundary.get("complex_delegation_contract_ui") is not False:
        raise AgentCollaborationBuildError("S08 P1 must not implement complex Delegation Contract UI")
    if boundary.get("proposal_apply") is not False:
        raise AgentCollaborationBuildError("S08 P1 must not apply proposals")
    metrics = as_list(config.get("metrics"))
    required = {
        "planning_clarity",
        "execution_clarity",
        "review_burden",
        "rework_count",
        "scope_clarity",
        "testability",
        "rollbackability",
    }
    seen = {str(item.get("metric_key")) for item in metrics if isinstance(item, dict)}
    missing = sorted(required - seen)
    if missing:
        raise AgentCollaborationBuildError(f"agent collaboration config missing metrics: {', '.join(missing)}")
    params = config.get("parameters")
    if not isinstance(params, dict) or not params:
        raise AgentCollaborationBuildError("agent collaboration config missing parameters")
    for item in metrics:
        if not isinstance(item, dict):
            raise AgentCollaborationBuildError("invalid metric item")
        if not item.get("formula_id") or not has_cjk(item.get("expression_zh")) or not has_cjk(item.get("interpretation_zh")):
            raise AgentCollaborationBuildError(f"metric {item.get('metric_key')} missing formula or Chinese interpretation")
        for param_ref in as_list(item.get("parameter_refs")):
            if param_ref not in params:
                raise AgentCollaborationBuildError(f"metric {item.get('metric_key')} references unknown parameter {param_ref}")


def validate_inputs(events: dict[str, Any], clusters: dict[str, Any], loops: dict[str, Any], opportunities: dict[str, Any], information_roi: dict[str, Any]) -> None:
    expected = [
        (events, "MA-V12-S05P3", "ACC-MA-V12-S05P3", "events"),
        (clusters, "MA-V12-S06P1", "ACC-MA-V12-S06P1", "clusters"),
        (loops, "MA-V12-S06P2", "ACC-MA-V12-S06P2", "low-value loops"),
        (opportunities, "MA-V12-S06P3", "ACC-MA-V12-S06P3", "opportunities"),
        (information_roi, "MA-V12-S07P2", "ACC-MA-V12-S07P2", "information ROI"),
    ]
    for payload, task_id, acceptance_id, label in expected:
        if payload.get("task_id") != task_id or payload.get("acceptance_id") != acceptance_id:
            raise AgentCollaborationBuildError(f"{label} identity mismatch")


def source_type_for(source_id: str) -> str:
    if source_id == "chatgpt":
        return "chatgpt"
    if source_id == "codex":
        return "codex"
    return "other_agent"


def agent_name_for(source_id: str) -> str:
    if source_id == "chatgpt":
        return "ChatGPT"
    if source_id == "codex":
        return "Codex"
    if source_id in {"future_agent", "future-agent"}:
        return "Future agent template"
    return source_id.replace("_", " ").title() or "Other agent"


def item_sources(item: dict[str, Any]) -> set[str]:
    sources = set()
    for ref in as_list(item.get("evidence_refs")):
        if isinstance(ref, dict) and ref.get("source_id"):
            sources.add(str(ref["source_id"]))
    if item.get("source_id"):
        sources.add(str(item["source_id"]))
    if item.get("source"):
        sources.add(str(item["source"]))
    return sources


def belongs_to_source(item: dict[str, Any], source_id: str) -> bool:
    sources = item_sources(item)
    if source_id == "future_agent":
        return bool(sources & {"future_agent", "future-agent", "other_agent"})
    return source_id in sources


def unique_evidence_refs(items: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
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
    return refs


def doc_evidence(ref_id: str, path: str, source_id: str = "governance") -> dict[str, Any]:
    return {
        "evidence_level": "derived_governance_doc",
        "path": path,
        "ref_id": ref_id,
        "ref_type": "governance_doc",
        "source_id": source_id,
    }


def score_level(score: int) -> str:
    if score >= 80:
        return "strong"
    if score >= 60:
        return "usable"
    if score >= 40:
        return "needs_review"
    return "weak"


def source_items(items: list[dict[str, Any]], source_id: str) -> list[dict[str, Any]]:
    return [item for item in items if isinstance(item, dict) and belongs_to_source(item, source_id)]


def known_project(event: dict[str, Any]) -> bool:
    value = str(event.get("project") or "").strip()
    return bool(value and value not in {"未标注", "unknown", "None", "null"})


def known_task(event: dict[str, Any]) -> bool:
    value = str(event.get("task_type") or event.get("task") or "").strip()
    return bool(value and value not in {"未标注", "unknown", "None", "null"})


def known_output(event: dict[str, Any]) -> bool:
    value = str(event.get("output_type") or "").strip()
    return bool(value and value not in {"unknown", "None", "null"})


def opportunity_has_next_step(item: dict[str, Any]) -> bool:
    return has_cjk(item.get("next_step_zh"))


def opportunity_has_action_signal(item: dict[str, Any]) -> bool:
    return opportunity_has_next_step(item) or str(item.get("opportunity_type") or "") in {"automation", "template", "productization"}


def roi_has_action(item: dict[str, Any]) -> bool:
    return has_cjk(item.get("action_zh")) or has_cjk(item.get("decision_summary_zh"))


def cluster_has_validator_signal(item: dict[str, Any]) -> bool:
    text = json.dumps({
        "label": item.get("label_zh"),
        "summary": item.get("summary_zh"),
        "task": (item.get("filter_dimensions") or {}).get("task"),
    }, ensure_ascii=False).lower()
    return any(token in text for token in ["validator", "验证", "测试", "test", "gate", "门禁", "build"])


def loop_type_count(items: list[dict[str, Any]], loop_type: str) -> int:
    return sum(1 for item in items if item.get("loop_type") == loop_type)


def average_action_half_life(items: list[dict[str, Any]]) -> float:
    values = [float(item.get("action_half_life_days") or 0) for item in items if float(item.get("action_half_life_days") or 0) > 0]
    if not values:
        return 0.0
    return sum(values) / len(values)


def build_metric(
    *,
    key: str,
    name_zh: str,
    formula_id: str,
    score: int,
    raw_value: dict[str, Any],
    explanation_zh: str,
    evidence_refs: list[dict[str, Any]],
    formula_source: Path,
) -> dict[str, Any]:
    if not evidence_refs:
        raise AgentCollaborationBuildError(f"metric {key} has no evidence")
    return {
        "metric_key": key,
        "name_zh": name_zh,
        "formula_id": formula_id,
        "formula_source": formula_source.as_posix(),
        "score": score,
        "level": score_level(score),
        "direction": "higher_is_better",
        "raw_value": raw_value,
        "explanation_zh": explanation_zh,
        "evidence_refs": evidence_refs,
    }


def compute_metrics_for_scope(
    *,
    source_id: str,
    config: dict[str, Any],
    events: list[dict[str, Any]],
    clusters: list[dict[str, Any]],
    loops: list[dict[str, Any]],
    decision_debts: list[dict[str, Any]],
    action_half_life: list[dict[str, Any]],
    opportunities: list[dict[str, Any]],
    roi_items: list[dict[str, Any]],
    overall: bool = False,
) -> list[dict[str, Any]]:
    params = config["parameters"]
    limit = int(params["evidence_refs_per_metric"])
    event_count = len(events)
    opportunity_count = len(opportunities)
    cluster_count = len(clusters)
    roi_count = len(roi_items)

    project_labeled_ratio = ratio(sum(1 for event in events if known_project(event)), event_count)
    task_labeled_ratio = ratio(sum(1 for event in events if known_task(event)), event_count)
    known_output_ratio = ratio(sum(1 for event in events if known_output(event)), event_count)
    evidence_coverage_ratio = ratio(sum(1 for event in events if as_list(event.get("evidence_refs"))), event_count)
    evidence_gap_ratio = ratio(sum(1 for event in events if "evidence_gap" in as_list(event.get("friction"))), event_count)
    opportunity_next_step_ratio = ratio(sum(1 for item in opportunities if opportunity_has_next_step(item)), opportunity_count)
    opportunity_action_ratio = ratio(sum(1 for item in opportunities if opportunity_has_action_signal(item)), opportunity_count)
    roi_action_ratio = ratio(sum(1 for item in roi_items if roi_has_action(item)), roi_count)
    validator_signal_ratio = ratio(sum(1 for item in clusters if cluster_has_validator_signal(item)), cluster_count)
    roi_gate_ratio = ratio(sum(1 for item in roi_items if item.get("visual_roi_gate_pass") is True or item.get("p0_candidate") is True), roi_count)
    run_gate_contract_ratio = 1.0
    proposal_only_ratio = 1.0
    raw_no_mutation_ratio = 1.0

    planning_score = clamp_score(100 * (
        project_labeled_ratio * float(params["project_label_weight"])
        + task_labeled_ratio * float(params["task_label_weight"])
        + opportunity_next_step_ratio * float(params["next_step_weight"])
        + evidence_coverage_ratio * float(params["evidence_weight"])
    ))
    execution_score = clamp_score(100 * (
        known_output_ratio * float(params["output_weight"])
        + opportunity_action_ratio * float(params["action_weight"])
        + roi_action_ratio * float(params["roi_action_weight"])
    ))
    review_score = clamp_score(100 - min(
        float(params["review_burden_penalty_cap"]),
        len(loops) * float(params["loop_penalty"])
        + len(decision_debts) * float(params["decision_debt_penalty"])
        + evidence_gap_ratio * float(params["evidence_gap_penalty"]),
    ))
    repeated_rework_count = loop_type_count(loops, "repeated_rework")
    avg_half_life = average_action_half_life(action_half_life)
    rework_score = clamp_score(100 - min(
        float(params["rework_penalty_cap"]),
        repeated_rework_count * float(params["rework_loop_penalty"]) + avg_half_life * float(params["half_life_penalty"]),
    ))
    scope_creep_count = loop_type_count(loops, "scope_creep")
    scope_score = clamp_score(100 * (
        project_labeled_ratio * float(params["project_label_weight"])
        + task_labeled_ratio * float(params["task_label_weight"])
    ) - scope_creep_count * float(params["scope_creep_penalty"]))
    testability_score = clamp_score(100 * (
        validator_signal_ratio * float(params["validator_signal_weight"])
        + roi_gate_ratio * float(params["roi_gate_weight"])
        + opportunity_next_step_ratio * float(params["next_step_weight"])
    ))
    rollback_score = clamp_score(100 * (
        run_gate_contract_ratio * float(params["run_gate_weight"])
        + proposal_only_ratio * float(params["proposal_weight"])
        + raw_no_mutation_ratio * float(params["raw_boundary_weight"])
    ))

    scope_label = "整体协作样本" if overall else f"{agent_name_for(source_id)} 样本"
    general_evidence = unique_evidence_refs(events + opportunities + clusters + loops + decision_debts, limit)
    governance_evidence = [
        doc_evidence("s08p1_metric_config", CONFIG_PATH.as_posix()),
        doc_evidence("s08p1_run_gate", "机器治理/运行门禁/README.md"),
    ]
    if not general_evidence:
        general_evidence = governance_evidence

    return [
        build_metric(
            key="planning_clarity",
            name_zh="规划清晰度",
            formula_id="FORM-MA-V12-S08P1-001",
            score=planning_score,
            raw_value={
                "event_count": event_count,
                "project_labeled_ratio": round(project_labeled_ratio, 4),
                "task_labeled_ratio": round(task_labeled_ratio, 4),
                "opportunity_next_step_ratio": round(opportunity_next_step_ratio, 4),
                "evidence_coverage_ratio": round(evidence_coverage_ratio, 4),
            },
            explanation_zh=f"{scope_label}的规划清晰度来自项目/任务标注、下一步和证据覆盖率；低分表示需要人在交给 agent 前先补目标、范围或证据。",
            evidence_refs=unique_evidence_refs(events + opportunities, limit) or general_evidence,
            formula_source=CONFIG_PATH,
        ),
        build_metric(
            key="execution_clarity",
            name_zh="执行清晰度",
            formula_id="FORM-MA-V12-S08P1-002",
            score=execution_score,
            raw_value={
                "event_count": event_count,
                "known_output_ratio": round(known_output_ratio, 4),
                "opportunity_action_ratio": round(opportunity_action_ratio, 4),
                "roi_action_ratio": round(roi_action_ratio, 4),
            },
            explanation_zh=f"{scope_label}的执行清晰度由输出类型、机会下一步和 ROI action 支撑；它帮助判断任务是否能直接进入 Codex/agent 执行。",
            evidence_refs=unique_evidence_refs(events + opportunities + roi_items, limit) or general_evidence,
            formula_source=CONFIG_PATH,
        ),
        build_metric(
            key="review_burden",
            name_zh="复审负担健康度",
            formula_id="FORM-MA-V12-S08P1-003",
            score=review_score,
            raw_value={
                "loop_count": len(loops),
                "decision_debt_count": len(decision_debts),
                "evidence_gap_ratio": round(evidence_gap_ratio, 4),
            },
            explanation_zh=f"{scope_label}的复审负担健康度会被低价值循环、decision debt 和 evidence gap 拉低；高分才表示复审压力较低。",
            evidence_refs=unique_evidence_refs(loops + decision_debts + events, limit) or general_evidence,
            formula_source=CONFIG_PATH,
        ),
        build_metric(
            key="rework_count",
            name_zh="返工控制健康度",
            formula_id="FORM-MA-V12-S08P1-004",
            score=rework_score,
            raw_value={
                "repeated_rework_loop_count": repeated_rework_count,
                "avg_action_half_life_days": round(avg_half_life, 2),
                "action_half_life_count": len(action_half_life),
            },
            explanation_zh=f"{scope_label}的返工控制健康度保留 repeated rework 和 action half-life 原始计数；低分表示需要先收口完成标准。",
            evidence_refs=unique_evidence_refs(loops + action_half_life, limit) or general_evidence,
            formula_source=CONFIG_PATH,
        ),
        build_metric(
            key="scope_clarity",
            name_zh="范围清晰度",
            formula_id="FORM-MA-V12-S08P1-005",
            score=scope_score,
            raw_value={
                "project_labeled_ratio": round(project_labeled_ratio, 4),
                "task_labeled_ratio": round(task_labeled_ratio, 4),
                "scope_creep_loop_count": scope_creep_count,
            },
            explanation_zh=f"{scope_label}的范围清晰度由项目/任务标注和 scope creep 候选共同决定；它不是任务价值判断，只提示边界是否足够清楚。",
            evidence_refs=unique_evidence_refs(events + loops, limit) or general_evidence,
            formula_source=CONFIG_PATH,
        ),
        build_metric(
            key="testability",
            name_zh="可测试性",
            formula_id="FORM-MA-V12-S08P1-006",
            score=testability_score,
            raw_value={
                "cluster_count": cluster_count,
                "validator_signal_ratio": round(validator_signal_ratio, 4),
                "roi_gate_ratio": round(roi_gate_ratio, 4),
                "opportunity_next_step_ratio": round(opportunity_next_step_ratio, 4),
            },
            explanation_zh=f"{scope_label}的可测试性来自 validator/gate 线索、ROI gate 和清晰下一步；它用于判断是否适合继续交给 Codex 执行。",
            evidence_refs=unique_evidence_refs(clusters + roi_items + opportunities, limit) or general_evidence,
            formula_source=CONFIG_PATH,
        ),
        build_metric(
            key="rollbackability",
            name_zh="可回滚性",
            formula_id="FORM-MA-V12-S08P1-007",
            score=rollback_score,
            raw_value={
                "run_gate_contract_ratio": run_gate_contract_ratio,
                "proposal_only_ratio": proposal_only_ratio,
                "raw_no_mutation_ratio": raw_no_mutation_ratio,
            },
            explanation_zh=f"{scope_label}的可回滚性来自运行门禁、proposal-only 和 raw 不修改边界；S08 P1 只解释协作指标，不执行 apply。",
            evidence_refs=governance_evidence + general_evidence[: max(0, limit - len(governance_evidence))],
            formula_source=CONFIG_PATH,
        ),
    ]


def source_summary(
    source_id: str,
    *,
    events: list[dict[str, Any]],
    clusters: list[dict[str, Any]],
    loops: list[dict[str, Any]],
    decision_debts: list[dict[str, Any]],
    action_half_life: list[dict[str, Any]],
    opportunities: list[dict[str, Any]],
    roi_items: list[dict[str, Any]],
    config: dict[str, Any],
) -> dict[str, Any]:
    source_events = source_items(events, source_id)
    source_clusters = source_items(clusters, source_id)
    source_loops = source_items(loops, source_id)
    source_debts = source_items(decision_debts, source_id)
    source_half_life = source_items(action_half_life, source_id)
    source_opportunities = source_items(opportunities, source_id)
    source_roi_items = source_items(roi_items, source_id)
    observed = bool(source_events or source_clusters or source_loops or source_opportunities)
    metric_scores: list[dict[str, Any]] = []
    if observed:
        metric_scores = compute_metrics_for_scope(
            source_id=source_id,
            config=config,
            events=source_events,
            clusters=source_clusters,
            loops=source_loops,
            decision_debts=source_debts,
            action_half_life=source_half_life,
            opportunities=source_opportunities,
            roi_items=source_roi_items,
        )
    evidence_refs = unique_evidence_refs(source_events + source_clusters + source_loops + source_opportunities, int(config["parameters"]["evidence_refs_per_metric"]))
    return {
        "source_id": source_id,
        "source_type": source_type_for(source_id),
        "agent_name": agent_name_for(source_id),
        "observed": observed,
        "record_count": len(source_events),
        "cluster_count": len(source_clusters),
        "loop_count": len(source_loops),
        "opportunity_count": len(source_opportunities),
        "metric_scores": metric_scores,
        "evidence_refs": evidence_refs,
        "missing_reason": "" if observed else "no_registered_public_raw_or_derived_collaboration_evidence",
        "future_agent_field_contract_supported": source_type_for(source_id) == "other_agent" or source_id in {"chatgpt", "codex"},
    }


def metric_lookup(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["metric_key"]: item for item in as_list(config.get("metrics")) if isinstance(item, dict) and item.get("metric_key")}


def build_chinese_summary(overall_metrics: list[dict[str, Any]], source_summaries: list[dict[str, Any]]) -> dict[str, Any]:
    scores = {item["metric_key"]: item for item in overall_metrics}
    weakest = sorted(overall_metrics, key=lambda item: item["score"])[:3]
    strongest = sorted(overall_metrics, key=lambda item: item["score"], reverse=True)[:3]
    observed_sources = [item["agent_name"] for item in source_summaries if item["observed"]]
    return {
        "title_zh": "Codex/Agent 协作质量摘要",
        "summary_zh": (
            "本报告用 planning、execution、review、rework、scope、testability 和 rollbackability "
            "七类指标解释 ChatGPT/Codex/后续 agent 的协作质量。它只做证据化指标，不创建多 agent 系统，"
            "也不实现复杂 Delegation Contract UI。"
        ),
        "observed_sources_zh": "已观测来源：" + ("、".join(observed_sources) if observed_sources else "暂无"),
        "human_responsibility_zh": "人负责定义目标、范围、授权、是否 apply、是否接受商业/产品判断，以及无法由证据自动推出的取舍。",
        "agent_responsibility_zh": "Agent 负责在已授权边界内执行可验证任务、生成候选报告、运行 validator、保留证据和回滚路径。",
        "rework_sources_zh": "返工主要从 repeated rework、decision debt、scope creep、evidence gap 和 action half-life 中识别。",
        "agent_fit_zh": "适合继续交给 Codex/agent 的任务通常具备清晰下一步、可测试输出、可回滚边界和足够证据。",
        "human_judgment_zh": "必须人工判断的任务包括授权 apply、修改 active config、解释冲突证据、业务优先级和高风险范围扩张。",
        "weakest_metrics": [{"metric_key": item["metric_key"], "name_zh": item["name_zh"], "score": item["score"]} for item in weakest],
        "strongest_metrics": [{"metric_key": item["metric_key"], "name_zh": item["name_zh"], "score": item["score"]} for item in strongest],
        "headline_scores": {
            "planning_clarity": scores.get("planning_clarity", {}).get("score"),
            "execution_clarity": scores.get("execution_clarity", {}).get("score"),
            "testability": scores.get("testability", {}).get("score"),
            "rollbackability": scores.get("rollbackability", {}).get("score"),
        },
    }


def build_agent_collaboration_report(
    database_dir: Path,
    dry_run: bool = False,
    generated_at: str | None = None,
    config_path: Path = CONFIG_PATH,
    events_path: Path = EVENTS_PATH,
    clusters_path: Path = CLUSTERS_PATH,
    loops_path: Path = LOW_VALUE_LOOPS_PATH,
    opportunities_path: Path = OPPORTUNITIES_PATH,
    information_roi_path: Path = INFORMATION_ROI_PATH,
    output_path: Path = OUTPUT_PATH,
) -> dict[str, Any]:
    database_dir = database_dir.resolve()
    generated_at = generated_at or now_utc()
    config = load_json(database_dir / config_path, "agent collaboration metrics config")
    validate_config(config)
    events_payload = load_json(database_dir / events_path, "behavior events")
    clusters_payload = load_json(database_dir / clusters_path, "behavior clusters")
    loops_payload = load_json(database_dir / loops_path, "low-value loops")
    opportunities_payload = load_json(database_dir / opportunities_path, "opportunities")
    information_roi_payload = load_json(database_dir / information_roi_path, "information ROI")
    validate_inputs(events_payload, clusters_payload, loops_payload, opportunities_payload, information_roi_payload)

    events = [item for item in as_list(events_payload.get("events")) if isinstance(item, dict)]
    clusters = [
        item
        for item in as_list(clusters_payload.get("topic_clusters")) + as_list(clusters_payload.get("hierarchy_clusters"))
        if isinstance(item, dict)
    ]
    loops = [item for item in as_list(loops_payload.get("loop_clusters")) if isinstance(item, dict)]
    decision_debts = [item for item in as_list(loops_payload.get("decision_debt_ledger")) if isinstance(item, dict)]
    action_half_life = [item for item in as_list(loops_payload.get("action_half_life")) if isinstance(item, dict)]
    opportunities = [item for item in as_list(opportunities_payload.get("opportunity_clusters")) if isinstance(item, dict)]
    roi_items = [item for item in as_list(information_roi_payload.get("roi_items")) if isinstance(item, dict)]

    observed_source_ids = sorted(
        {str(item.get("source_id") or item.get("source")) for item in events if item.get("source_id") or item.get("source")}
        | {"chatgpt", "codex", "future_agent"}
    )
    source_summaries = [
        source_summary(
            source_id,
            events=events,
            clusters=clusters,
            loops=loops,
            decision_debts=decision_debts,
            action_half_life=action_half_life,
            opportunities=opportunities,
            roi_items=roi_items,
            config=config,
        )
        for source_id in observed_source_ids
    ]
    overall_metrics = compute_metrics_for_scope(
        source_id="all",
        config=config,
        events=events,
        clusters=clusters,
        loops=loops,
        decision_debts=decision_debts,
        action_half_life=action_half_life,
        opportunities=opportunities,
        roi_items=roi_items,
        overall=True,
    )
    source_counts = Counter(str(item.get("source_id") or item.get("source") or "unknown") for item in events)
    output: dict[str, Any] = {
        "schema_version": "memory_atlas_agent_collaboration_quality_report.v1_2_s08_p1",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "status": STATUS,
        "generated_at": generated_at,
        "dry_run": dry_run,
        "writes_files": not dry_run,
        "config_path": config_path.as_posix(),
        "input_paths": [
            events_path.as_posix(),
            clusters_path.as_posix(),
            loops_path.as_posix(),
            opportunities_path.as_posix(),
            information_roi_path.as_posix(),
        ],
        "output_path": output_path.as_posix(),
        "source_task_ids": {
            "events": events_payload.get("task_id"),
            "clusters": clusters_payload.get("task_id"),
            "low_value_loops": loops_payload.get("task_id"),
            "opportunities": opportunities_payload.get("task_id"),
            "information_roi": information_roi_payload.get("task_id"),
        },
        "collaboration_quality_summary": {
            "observed_event_count": len(events),
            "observed_source_counts": dict(sorted(source_counts.items())),
            "metric_count": len(overall_metrics),
            "source_summary_count": len(source_summaries),
            "average_metric_score": clamp_score(sum(item["score"] for item in overall_metrics) / max(1, len(overall_metrics))),
            "explanation_zh": "协作质量分数是内部 proxy，用于识别规划、执行、复审、返工、范围、测试和回滚的协作健康度。",
            "limitation_zh": "该报告不创建多 agent 系统，不实现复杂 Delegation Contract UI，不处理授权 apply，也不修改 raw。",
        },
        "metric_definitions": as_list(config.get("metrics")),
        "overall_metrics": overall_metrics,
        "source_summaries": source_summaries,
        "chinese_summary": build_chinese_summary(overall_metrics, source_summaries),
        "unsupported_scope": {
            "multi_agent_system_implementation": False,
            "complex_delegation_contract_ui": False,
            "authorization_apply_boundary": "deferred_to_s08_p2",
            "stage_flight_recorder": "deferred_to_s08_p3",
        },
        "phase_boundary": {
            "does_not_create_multi_agent_system": True,
            "does_not_implement_complex_delegation_contract_ui": True,
            "does_not_define_authorization_apply_boundary": True,
            "does_not_generate_stage_flight_recorder": True,
            "does_not_apply_proposals": True,
            "does_not_modify_raw": True,
            "next_phase": "S08 P2",
        },
    }
    validate_payload(output)
    if not dry_run:
        output_file = database_dir / output_path
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output


def validate_payload(payload: dict[str, Any]) -> None:
    if payload.get("task_id") != TASK_ID or payload.get("acceptance_id") != ACCEPTANCE_ID:
        raise AgentCollaborationBuildError("payload identity mismatch")
    if payload.get("status") != STATUS:
        raise AgentCollaborationBuildError("payload status mismatch")
    boundary = payload.get("phase_boundary") or {}
    if boundary.get("does_not_create_multi_agent_system") is not True:
        raise AgentCollaborationBuildError("payload must not create multi-agent system")
    if boundary.get("does_not_implement_complex_delegation_contract_ui") is not True:
        raise AgentCollaborationBuildError("payload must not implement complex Delegation Contract UI")
    if boundary.get("does_not_modify_raw") is not True:
        raise AgentCollaborationBuildError("payload must not mutate raw")
    if not has_cjk((payload.get("chinese_summary") or {}).get("summary_zh")):
        raise AgentCollaborationBuildError("payload missing Chinese collaboration summary")
    metric_keys = {item.get("metric_key") for item in as_list(payload.get("overall_metrics")) if isinstance(item, dict)}
    required = {
        "planning_clarity",
        "execution_clarity",
        "review_burden",
        "rework_count",
        "scope_clarity",
        "testability",
        "rollbackability",
    }
    missing = sorted(required - metric_keys)
    if missing:
        raise AgentCollaborationBuildError(f"payload missing metrics: {', '.join(missing)}")
    for metric in as_list(payload.get("overall_metrics")):
        if not metric.get("evidence_refs"):
            raise AgentCollaborationBuildError(f"metric {metric.get('metric_key')} has no evidence")
        if not has_cjk(metric.get("explanation_zh")):
            raise AgentCollaborationBuildError(f"metric {metric.get('metric_key')} missing Chinese explanation")
        if not 0 <= int(metric.get("score", -1)) <= 100:
            raise AgentCollaborationBuildError(f"metric {metric.get('metric_key')} score out of range")
    summaries = as_list(payload.get("source_summaries"))
    source_types = {item.get("source_type") for item in summaries if isinstance(item, dict)}
    if not {"chatgpt", "codex", "other_agent"}.issubset(source_types):
        raise AgentCollaborationBuildError("payload must support chatgpt, codex and other_agent source fields")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Memory Atlas S08 P1 agent collaboration quality builder.")
    parser.add_argument("--database-dir", type=Path, default=ROOT)
    parser.add_argument("--config", type=Path, default=CONFIG_PATH)
    parser.add_argument("--events", type=Path, default=EVENTS_PATH)
    parser.add_argument("--clusters", type=Path, default=CLUSTERS_PATH)
    parser.add_argument("--low-value-loops", type=Path, default=LOW_VALUE_LOOPS_PATH)
    parser.add_argument("--opportunities", type=Path, default=OPPORTUNITIES_PATH)
    parser.add_argument("--information-roi", type=Path, default=INFORMATION_ROI_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        payload = build_agent_collaboration_report(
            args.database_dir,
            dry_run=args.dry_run,
            config_path=args.config,
            events_path=args.events,
            clusters_path=args.clusters,
            loops_path=args.low_value_loops,
            opportunities_path=args.opportunities,
            information_roi_path=args.information_roi,
            output_path=args.output,
        )
    except AgentCollaborationBuildError as exc:
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
