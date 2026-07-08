#!/usr/bin/env python3
"""Build Memory Atlas S07 P2 Information ROI and Visual ROI Gate outputs."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
FORMULA_CONFIG_PATH = Path("机器治理/参数与公式/information_roi.v1_2_s07_p2.json")
VISUAL_GATE_CONFIG_PATH = Path("机器治理/可视化配置/visual_roi_gate.v1_2_s07_p2.json")
VISUALIZATION_PATH = Path("data/derived/visualization/memory_atlas.json")
ECONOMIC_PROXY_PATH = Path("data/derived/economic_proxy/personal_economic_proxy.json")
OUTPUT_PATH = Path("data/derived/information_roi/information_roi_gate.json")
TASK_ID = "MA-V12-S07P2"
ACCEPTANCE_ID = "ACC-MA-V12-S07P2"
STATUS = "phase_s07_p2_information_roi_completed_pending_s07_p3"


class InformationRoiBuildError(RuntimeError):
    pass


def now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path, label: str) -> dict[str, Any]:
    if not path.exists():
        raise InformationRoiBuildError(f"{label} missing: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise InformationRoiBuildError(f"{label} must be a JSON object: {path}")
    return payload


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def clamp_score(value: float) -> int:
    return int(round(max(0.0, min(100.0, value))))


def has_cjk(value: Any) -> bool:
    return any("\u3400" <= char <= "\u9fff" for char in str(value or ""))


def validate_formula_config(config: dict[str, Any]) -> None:
    if config.get("task_id") != TASK_ID or config.get("acceptance_id") != ACCEPTANCE_ID:
        raise InformationRoiBuildError("information ROI formula config identity mismatch")
    boundary = config.get("scope_boundary") or {}
    if boundary.get("external_economic_database_dependency") is not False:
        raise InformationRoiBuildError("information ROI config must not depend on external economic database")
    if boundary.get("precise_income_prediction") is not False:
        raise InformationRoiBuildError("information ROI config must not claim precise income prediction")
    formulas = as_list(config.get("formulas"))
    score_keys = {str(item.get("score_key")) for item in formulas if isinstance(item, dict)}
    if {"information_roi_score", "visual_roi_gate"} - score_keys:
        raise InformationRoiBuildError("information ROI config missing required formulas")
    params = config.get("parameters")
    if not isinstance(params, dict) or not params:
        raise InformationRoiBuildError("information ROI config missing parameters")
    for item in formulas:
        if not isinstance(item, dict):
            raise InformationRoiBuildError("invalid information ROI formula item")
        if not item.get("formula_id") or not has_cjk(item.get("expression_zh")) or not has_cjk(item.get("interpretation_zh")):
            raise InformationRoiBuildError(f"formula {item.get('score_key')} missing Chinese expression or interpretation")
        for param_ref in as_list(item.get("parameter_refs")):
            if param_ref not in params:
                raise InformationRoiBuildError(f"formula {item.get('score_key')} references unknown parameter {param_ref}")


def validate_visual_gate_config(config: dict[str, Any]) -> None:
    if config.get("task_id") != TASK_ID or config.get("acceptance_id") != ACCEPTANCE_ID:
        raise InformationRoiBuildError("visual ROI gate config identity mismatch")
    boundary = config.get("scope_boundary") or {}
    if boundary.get("external_economic_database_dependency") is not False:
        raise InformationRoiBuildError("visual ROI gate must not depend on external economic database")
    visuals = as_list(config.get("p0_visuals"))
    if len(visuals) < 5:
        raise InformationRoiBuildError("visual ROI gate must define P0 visual candidates")
    for item in visuals:
        if not isinstance(item, dict) or not item.get("id") or not has_cjk(item.get("human_question")) or not has_cjk(item.get("action")):
            raise InformationRoiBuildError("each P0 visual must have id, Chinese human_question and action")


def evidence_strength(evidence_refs: list[dict[str, Any]]) -> tuple[str, float]:
    sources = {str(item.get("source_id") or "") for item in evidence_refs if isinstance(item, dict)}
    if len(evidence_refs) >= 8 and len(sources) >= 2:
        return "A", 1.0
    if len(evidence_refs) >= 3:
        return "B", 0.82
    if evidence_refs:
        return "C", 0.65
    return "D", 0.45


def information_roi_score(components: dict[str, float], params: dict[str, Any]) -> int:
    numerator = (
        components["decision_value"]
        * components["actionability"]
        * components["evidence_strength"]
        * components["freshness"]
        * components["reuse_value"]
    )
    denominator = max(
        components["reading_cost"]
        * components["navigation_cost"]
        * components["misleading_risk"]
        * components["maintenance_cost"],
        float(params["epsilon"]),
    )
    return clamp_score(100 * numerator / denominator)


def first_evidence_refs(items: list[dict[str, Any]], limit: int = 8) -> list[dict[str, Any]]:
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


def make_roi_item(
    *,
    item_id: str,
    item_type: str,
    source_kind: str,
    title_zh: str,
    decision_summary_zh: str,
    evidence_refs: list[dict[str, Any]],
    components: dict[str, float],
    formula_id: str,
    formula_source: Path,
    params: dict[str, Any],
    p0_candidate: bool = False,
    human_question: str = "",
    action_zh: str = "",
) -> dict[str, Any]:
    evidence_grade, evidence_score = evidence_strength(evidence_refs)
    components = {
        **components,
        "evidence_strength": evidence_score,
    }
    score = information_roi_score(components, params)
    gate_pass = (
        score >= float(params["p0_min_information_roi_score"])
        and components["decision_value"] >= float(params["p0_min_decision_value"])
        and components["actionability"] >= float(params["p0_min_actionability"])
        and components["evidence_strength"] >= float(params["p0_min_evidence_strength"])
        and bool(human_question or item_type != "chart")
        and bool(action_zh or item_type != "chart")
    )
    return {
        "item_id": item_id,
        "item_type": item_type,
        "source_kind": source_kind,
        "title_zh": title_zh,
        "decision_summary_zh": decision_summary_zh,
        "information_roi_score": score,
        "formula_id": formula_id,
        "formula_source": formula_source.as_posix(),
        "components": {key: round(value, 4) for key, value in components.items()},
        "evidence_strength_grade": evidence_grade,
        "human_question": human_question,
        "action_zh": action_zh,
        "p0_candidate": p0_candidate,
        "visual_roi_gate_pass": gate_pass if item_type == "chart" else None,
        "evidence_refs": evidence_refs,
    }


def build_insight_items(
    behavior: dict[str, Any],
    economic_proxy: dict[str, Any],
    params: dict[str, Any],
    formula_source: Path,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for card in as_list(economic_proxy.get("score_cards")):
        if not isinstance(card, dict):
            continue
        score = clamp(float(card.get("score") or 0) / 100)
        items.append(make_roi_item(
            item_id=f"insight_{card.get('score_key')}",
            item_type="insight",
            source_kind="economic_proxy.score_card",
            title_zh=str(card.get("name_zh") or card.get("score_key")),
            decision_summary_zh=str(card.get("explanation_zh") or ""),
            evidence_refs=[ref for ref in as_list(card.get("evidence_refs")) if isinstance(ref, dict)],
            components={
                "decision_value": clamp(0.55 + score * 0.35),
                "actionability": clamp(0.55 + score * 0.3),
                "freshness": 0.82,
                "reuse_value": clamp(0.5 + score * 0.42),
                "reading_cost": float(params["reading_cost_default"]),
                "navigation_cost": float(params["navigation_cost_default"]),
                "misleading_risk": float(params["misleading_risk_default"]),
                "maintenance_cost": float(params["maintenance_cost_default"]),
            },
            formula_id="FORM-MA-V12-S07P2-001",
            formula_source=formula_source,
            params=params,
        ))

    for source_key, label, id_field in [
        ("clusters", "主题簇 insight", "cluster_id"),
        ("low_value_loops", "低价值循环 insight", "loop_id"),
        ("opportunities", "候选机会 insight", "opportunity_id"),
    ]:
        for item in [entry for entry in as_list(behavior.get(source_key)) if isinstance(entry, dict)][:3]:
            item_score = clamp(float(item.get("score") or min(int(item.get("event_count") or 5), 100)) / 100)
            evidence = [ref for ref in as_list(item.get("evidence_refs")) if isinstance(ref, dict)]
            items.append(make_roi_item(
                item_id=f"insight_{item.get(id_field)}",
                item_type="insight",
                source_kind=f"behavior_intelligence.{source_key}",
                title_zh=str(item.get("label_zh") or label),
                decision_summary_zh=str(item.get("summary_zh") or item.get("next_step_zh") or ""),
                evidence_refs=evidence,
                components={
                    "decision_value": clamp(0.5 + item_score * 0.35),
                    "actionability": 0.7 if item.get("next_step_zh") else 0.62,
                    "freshness": 0.78,
                    "reuse_value": clamp(0.55 + min(len(evidence), 8) * 0.04),
                    "reading_cost": 1.05,
                    "navigation_cost": 1.0,
                    "misleading_risk": 1.0,
                    "maintenance_cost": 1.0,
                },
                formula_id="FORM-MA-V12-S07P2-001",
                formula_source=formula_source,
                params=params,
            ))
    return items


def build_card_items(behavior: dict[str, Any], params: dict[str, Any], formula_source: Path) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for item in [entry for entry in as_list(behavior.get("opportunities")) if isinstance(entry, dict)][:6]:
        card = item.get("why_not_now_card") if isinstance(item.get("why_not_now_card"), dict) else {}
        evidence = [ref for ref in as_list(item.get("evidence_refs")) if isinstance(ref, dict)]
        item_score = clamp(float(item.get("score") or 0) / 100)
        items.append(make_roi_item(
            item_id=f"card_{card.get('card_id') or item.get('opportunity_id')}",
            item_type="card",
            source_kind="behavior_intelligence.why_not_now_card",
            title_zh=str(item.get("label_zh") or "为什么不是现在"),
            decision_summary_zh=str(card.get("reason_zh") or item.get("summary_zh") or ""),
            evidence_refs=evidence,
            components={
                "decision_value": clamp(0.52 + item_score * 0.32),
                "actionability": 0.78 if item.get("next_step_zh") else 0.58,
                "freshness": 0.75,
                "reuse_value": 0.68,
                "reading_cost": 1.0,
                "navigation_cost": 1.0,
                "misleading_risk": 0.95 if card.get("not_pressure_list") is True else 1.15,
                "maintenance_cost": 1.0,
            },
            formula_id="FORM-MA-V12-S07P2-001",
            formula_source=formula_source,
            params=params,
        ))
    return items


def build_chart_items(
    visual_config: dict[str, Any],
    behavior: dict[str, Any],
    params: dict[str, Any],
    formula_source: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    support_evidence = first_evidence_refs(
        [
            *[entry for entry in as_list(behavior.get("clusters")) if isinstance(entry, dict)],
            *[entry for entry in as_list(behavior.get("low_value_loops")) if isinstance(entry, dict)],
            *[entry for entry in as_list(behavior.get("opportunities")) if isinstance(entry, dict)],
        ],
    )
    p0_items: list[dict[str, Any]] = []
    for item in as_list(visual_config.get("p0_visuals")):
        if not isinstance(item, dict):
            continue
        p0_items.append(make_roi_item(
            item_id=f"chart_{item.get('id')}",
            item_type="chart",
            source_kind="visual_roi_gate.p0_visuals",
            title_zh=str(item.get("id")),
            decision_summary_zh=f"{item.get('human_question')} -> {item.get('action')}",
            evidence_refs=support_evidence,
            human_question=str(item.get("human_question") or ""),
            action_zh=str(item.get("action") or ""),
            p0_candidate=True,
            components={
                "decision_value": float(item.get("decision_value") or 0),
                "actionability": float(item.get("actionability") or 0),
                "freshness": 0.74,
                "reuse_value": float(item.get("reuse_value") or 0),
                "reading_cost": float(item.get("reading_cost") or params["reading_cost_default"]),
                "navigation_cost": float(item.get("navigation_cost") or params["navigation_cost_default"]),
                "misleading_risk": float(item.get("misleading_risk") or params["misleading_risk_default"]),
                "maintenance_cost": float(item.get("maintenance_cost") or params["maintenance_cost_default"]),
            },
            formula_id="FORM-MA-V12-S07P2-001",
            formula_source=formula_source,
            params=params,
        ))

    excluded_items: list[dict[str, Any]] = []
    for item in as_list(visual_config.get("excluded_from_p0_examples")):
        if not isinstance(item, dict):
            continue
        excluded_items.append(make_roi_item(
            item_id=f"chart_{item.get('id')}",
            item_type="chart",
            source_kind="visual_roi_gate.excluded_from_p0_examples",
            title_zh=str(item.get("id")),
            decision_summary_zh=str(item.get("reason_zh") or ""),
            evidence_refs=support_evidence[:2],
            human_question="",
            action_zh="",
            p0_candidate=False,
            components={
                "decision_value": float(item.get("decision_value") or 0),
                "actionability": float(item.get("actionability") or 0),
                "freshness": 0.5,
                "reuse_value": 0.35,
                "reading_cost": 1.2,
                "navigation_cost": 1.2,
                "misleading_risk": 1.3,
                "maintenance_cost": 1.2,
            },
            formula_id="FORM-MA-V12-S07P2-001",
            formula_source=formula_source,
            params=params,
        ))
    return p0_items, excluded_items


def validate_payload(payload: dict[str, Any]) -> None:
    if payload.get("task_id") != TASK_ID or payload.get("acceptance_id") != ACCEPTANCE_ID:
        raise InformationRoiBuildError("payload identity mismatch")
    if payload.get("status") != STATUS:
        raise InformationRoiBuildError("payload status mismatch")
    boundary = payload.get("phase_boundary") or {}
    if boundary.get("does_not_use_external_economic_database") is not True:
        raise InformationRoiBuildError("payload must not use external economic database")
    if boundary.get("does_not_claim_precise_income_prediction") is not True:
        raise InformationRoiBuildError("payload must not claim precise income prediction")
    if boundary.get("does_not_generate_what_if_ui") is not True:
        raise InformationRoiBuildError("S07 P2 must not implement S07 P3 what-if UI")
    roi_items = as_list(payload.get("roi_items"))
    if not roi_items:
        raise InformationRoiBuildError("payload missing ROI items")
    item_types = {item.get("item_type") for item in roi_items if isinstance(item, dict)}
    if {"insight", "card", "chart"} - item_types:
        raise InformationRoiBuildError("payload must cover insight, card and chart ROI items")
    bad_items = []
    for item in roi_items:
        if not isinstance(item, dict):
            bad_items.append("invalid_roi_item")
            continue
        if not item.get("formula_id") or not item.get("formula_source"):
            bad_items.append(f"{item.get('item_id')}:missing_formula_source")
        if not has_cjk(item.get("decision_summary_zh")):
            bad_items.append(f"{item.get('item_id')}:missing_chinese_summary")
        if not item.get("evidence_refs"):
            bad_items.append(f"{item.get('item_id')}:missing_evidence_refs")
        if not (0 <= int(item.get("information_roi_score") or -1) <= 100):
            bad_items.append(f"{item.get('item_id')}:score_out_of_range")
        if item.get("item_type") == "chart" and item.get("p0_candidate") is True:
            if not item.get("human_question") or not item.get("action_zh") or item.get("visual_roi_gate_pass") is not True:
                bad_items.append(f"{item.get('item_id')}:invalid_p0_visual_gate")
    if bad_items:
        raise InformationRoiBuildError(f"invalid ROI items: {', '.join(bad_items[:20])}")
    gate = payload.get("visual_roi_gate") or {}
    if gate.get("failed_p0_count") != 0 or not gate.get("excluded_from_p0"):
        raise InformationRoiBuildError("visual ROI gate must have zero failed P0 charts and explicit excluded examples")


def build_information_roi(
    database_dir: Path,
    dry_run: bool = False,
    generated_at: str | None = None,
    formula_config_path: Path = FORMULA_CONFIG_PATH,
    visual_gate_config_path: Path = VISUAL_GATE_CONFIG_PATH,
    visualization_path: Path = VISUALIZATION_PATH,
    economic_proxy_path: Path = ECONOMIC_PROXY_PATH,
    output_path: Path = OUTPUT_PATH,
) -> dict[str, Any]:
    database_dir = database_dir.resolve()
    generated_at = generated_at or now_utc()
    formula_config = load_json(database_dir / formula_config_path, "information ROI formula config")
    visual_config = load_json(database_dir / visual_gate_config_path, "visual ROI gate config")
    atlas = load_json(database_dir / visualization_path, "Memory Atlas visualization output")
    economic_proxy = load_json(database_dir / economic_proxy_path, "Personal Economic Proxy output")
    validate_formula_config(formula_config)
    validate_visual_gate_config(visual_config)
    params = formula_config["parameters"]
    behavior = atlas.get("behavior_intelligence") if isinstance(atlas.get("behavior_intelligence"), dict) else {}

    insight_items = build_insight_items(behavior, economic_proxy, params, formula_config_path)
    card_items = build_card_items(behavior, params, formula_config_path)
    p0_chart_items, excluded_chart_items = build_chart_items(visual_config, behavior, params, formula_config_path)
    roi_items = [*insight_items, *card_items, *p0_chart_items]
    p0_failures = [item for item in p0_chart_items if item.get("visual_roi_gate_pass") is not True]
    payload: dict[str, Any] = {
        "schema_version": "memory_atlas_information_roi_gate.v1_2_s07_p2",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "status": STATUS,
        "generated_at": generated_at,
        "dry_run": dry_run,
        "writes_files": not dry_run,
        "input_paths": [
            visualization_path.as_posix(),
            economic_proxy_path.as_posix(),
            visual_gate_config_path.as_posix(),
        ],
        "formula_config_path": formula_config_path.as_posix(),
        "visual_gate_config_path": visual_gate_config_path.as_posix(),
        "output_path": output_path.as_posix(),
        "source_task_ids": {
            "behavior_intelligence": behavior.get("task_ids"),
            "economic_proxy": economic_proxy.get("task_id"),
        },
        "formula_registry": formula_config.get("formulas"),
        "parameters": params,
        "roi_summary": {
            "item_count": len(roi_items),
            "insight_count": len(insight_items),
            "card_count": len(card_items),
            "chart_count": len(p0_chart_items),
            "average_information_roi_score": clamp_score(sum(item["information_roi_score"] for item in roi_items) / max(1, len(roi_items))),
            "explanation_zh": "该输出为 insight、card 和 chart 提供信息 ROI，用于判断哪些内容值得进入 P0 决策视图。",
            "limitation_zh": "它是内部 proxy，不是精确收入预测，不接外部经济数据库，也不实现 S07 P3 what-if UI。",
        },
        "roi_items": roi_items,
        "visual_roi_gate": {
            "p0_candidate_count": len(p0_chart_items),
            "passed_p0_count": len(p0_chart_items) - len(p0_failures),
            "failed_p0_count": len(p0_failures),
            "p0_visuals": p0_chart_items,
            "excluded_from_p0": excluded_chart_items,
            "gate_rule_zh": "P0 图表必须有 human_question、action、公式来源、证据来源和足够 information ROI；没有决策价值的图表不进 P0。",
        },
        "external_economic_database": {
            "current_dependency": False,
            "v2_interface": "reserved_not_implemented",
        },
        "phase_boundary": {
            "does_not_use_external_economic_database": True,
            "does_not_claim_precise_income_prediction": True,
            "does_not_modify_raw": True,
            "does_not_generate_what_if_ui": True,
            "does_not_modify_runtime_ui": True,
            "next_phase": "S07 P3",
        },
    }
    validate_payload(payload)
    if not dry_run:
        output = database_dir / output_path
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Memory Atlas S07 P2 Information ROI builder.")
    parser.add_argument("--database-dir", type=Path, default=ROOT)
    parser.add_argument("--formula-config", type=Path, default=FORMULA_CONFIG_PATH)
    parser.add_argument("--visual-gate-config", type=Path, default=VISUAL_GATE_CONFIG_PATH)
    parser.add_argument("--visualization", type=Path, default=VISUALIZATION_PATH)
    parser.add_argument("--economic-proxy", type=Path, default=ECONOMIC_PROXY_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        payload = build_information_roi(
            args.database_dir,
            dry_run=args.dry_run,
            formula_config_path=args.formula_config,
            visual_gate_config_path=args.visual_gate_config,
            visualization_path=args.visualization,
            economic_proxy_path=args.economic_proxy,
            output_path=args.output,
        )
    except InformationRoiBuildError as exc:
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
