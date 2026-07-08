#!/usr/bin/env python3
"""Build Memory Atlas S07 P1 Personal Economic Proxy from internal derived data."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
FORMULA_CONFIG_PATH = Path("机器治理/参数与公式/personal_economic_proxy.v1_2_s07_p1.json")
CLUSTERS_PATH = Path("data/derived/behavior_intelligence/clusters.json")
LOW_VALUE_PATH = Path("data/derived/behavior_intelligence/low_value_loops.json")
OPPORTUNITIES_PATH = Path("data/derived/behavior_intelligence/opportunities.json")
OUTPUT_PATH = Path("data/derived/economic_proxy/personal_economic_proxy.json")
TASK_ID = "MA-V12-S07P1"
ACCEPTANCE_ID = "ACC-MA-V12-S07P1"
STATUS = "phase_s07_p1_economic_proxy_completed_pending_s07_p2"


class EconomicProxyBuildError(RuntimeError):
    pass


def now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path, label: str) -> dict[str, Any]:
    if not path.exists():
        raise EconomicProxyBuildError(f"{label} missing: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise EconomicProxyBuildError(f"{label} must be a JSON object: {path}")
    return payload


def clamp_score(value: float) -> int:
    return int(round(max(0.0, min(100.0, value))))


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


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


def formula_by_key(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    formulas = {}
    for item in as_list(config.get("formulas")):
        if isinstance(item, dict) and item.get("score_key"):
            formulas[str(item["score_key"])] = item
    return formulas


def validate_formula_config(config: dict[str, Any]) -> None:
    required_keys = {
        "time_saved_proxy",
        "reuse_value_proxy",
        "rework_cost_proxy",
        "opportunity_score_proxy",
        "skill_compounding_proxy",
        "automation_enhancement_ratio_proxy",
    }
    formulas = formula_by_key(config)
    missing = sorted(required_keys - set(formulas))
    if config.get("task_id") != TASK_ID or config.get("acceptance_id") != ACCEPTANCE_ID:
        raise EconomicProxyBuildError("formula config identity mismatch")
    if missing:
        raise EconomicProxyBuildError(f"formula config missing score keys: {', '.join(missing)}")
    boundary = config.get("scope_boundary") or {}
    if boundary.get("external_economic_database_dependency") is not False:
        raise EconomicProxyBuildError("formula config must not depend on external economic database")
    if boundary.get("precise_income_prediction") is not False or boundary.get("financial_advice") is not False:
        raise EconomicProxyBuildError("formula config must not claim precise income prediction or financial advice")
    if not isinstance(config.get("parameters"), dict) or not config["parameters"]:
        raise EconomicProxyBuildError("formula config must define parameters")
    for key, formula in formulas.items():
        if not formula.get("formula_id") or not formula.get("expression_zh") or not formula.get("interpretation_zh"):
            raise EconomicProxyBuildError(f"formula {key} missing id, expression or interpretation")
        for param_ref in as_list(formula.get("parameter_refs")):
            if param_ref not in config["parameters"]:
                raise EconomicProxyBuildError(f"formula {key} references unknown parameter {param_ref}")


def load_inputs(
    database_dir: Path,
    formula_config_path: Path,
    clusters_path: Path,
    low_value_path: Path,
    opportunities_path: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    config = load_json(database_dir / formula_config_path, "formula config")
    validate_formula_config(config)
    clusters = load_json(database_dir / clusters_path, "clusters")
    low_value = load_json(database_dir / low_value_path, "low-value loops")
    opportunities = load_json(database_dir / opportunities_path, "opportunities")
    return config, clusters, low_value, opportunities


def all_clusters(clusters: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        item
        for item in [*as_list(clusters.get("topic_clusters")), *as_list(clusters.get("hierarchy_clusters"))]
        if isinstance(item, dict)
    ]


def observed_months(items: list[dict[str, Any]]) -> set[str]:
    months: set[str] = set()
    for item in items:
        range_payload = item.get("observed_time_range") or item.get("filter_dimensions", {}).get("time") or {}
        for month in as_list(range_payload.get("months")):
            months.add(str(month))
    return months


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def make_score_card(
    formula: dict[str, Any],
    *,
    score: int,
    raw_value: dict[str, Any],
    explanation_zh: str,
    evidence_refs: list[dict[str, Any]],
    formula_config_path: Path,
) -> dict[str, Any]:
    return {
        "score_key": formula["score_key"],
        "formula_id": formula["formula_id"],
        "name_zh": formula["name_zh"],
        "score": score,
        "raw_value": raw_value,
        "explanation_zh": explanation_zh,
        "formula_expression_zh": formula["expression_zh"],
        "formula_source": formula_config_path.as_posix(),
        "parameter_refs": as_list(formula.get("parameter_refs")),
        "evidence_refs": evidence_refs,
    }


def build_score_cards(
    config: dict[str, Any],
    clusters: dict[str, Any],
    low_value: dict[str, Any],
    opportunities: dict[str, Any],
    formula_config_path: Path,
) -> list[dict[str, Any]]:
    params = config["parameters"]
    formulas = formula_by_key(config)
    cluster_items = all_clusters(clusters)
    loop_items = [item for item in as_list(low_value.get("loop_clusters")) if isinstance(item, dict)]
    half_life_items = [item for item in as_list(low_value.get("action_half_life")) if isinstance(item, dict)]
    opportunity_items = [item for item in as_list(opportunities.get("opportunity_clusters")) if isinstance(item, dict)]
    opportunities_by_type: dict[str, list[dict[str, Any]]] = {}
    for item in opportunity_items:
        opportunities_by_type.setdefault(str(item.get("opportunity_type") or ""), []).append(item)

    automation_count = len(opportunities_by_type.get("automation", []))
    productization_count = len(opportunities_by_type.get("productization", []))
    template_count = len(opportunities_by_type.get("template", []))
    compounding_count = len(opportunities_by_type.get("compounding", []))
    reusable_count = productization_count + template_count + compounding_count
    high_evidence_clusters = [item for item in cluster_items if int(item.get("event_count") or 0) >= 5]
    average_loop_score = mean([float(item.get("score") or 0) for item in loop_items])
    average_half_life = mean([float(item.get("action_half_life_days") or 0) for item in half_life_items])
    average_opportunity_score = mean([float(item.get("score") or 0) for item in opportunity_items])
    average_opportunity_evidence = mean([float(len(as_list(item.get("evidence_refs")))) for item in opportunity_items])
    month_count = len(observed_months([*cluster_items, *loop_items, *opportunity_items]))
    automation_ratio_base = max(1, automation_count + productization_count + template_count + compounding_count)
    automation_ratio = automation_count / automation_ratio_base
    enhancement_ratio = 1 - automation_ratio
    proxy_hours = (
        automation_count * float(params["hours_per_automation_candidate"])
        + template_count * float(params["hours_per_template_candidate"])
        + productization_count * float(params["hours_per_productization_candidate"])
        + len(loop_items) * float(params["rework_avoidance_hours_per_loop"])
    )

    cluster_evidence = first_evidence_refs(high_evidence_clusters or cluster_items)
    loop_evidence = first_evidence_refs([*loop_items, *half_life_items])
    opportunity_evidence = first_evidence_refs(opportunity_items)
    cards = [
        make_score_card(
            formulas["time_saved_proxy"],
            score=clamp_score(proxy_hours * float(params["score_per_proxy_hour"])),
            raw_value={
                "proxy_hours": round(proxy_hours, 2),
                "automation_count": automation_count,
                "template_count": template_count,
                "productization_count": productization_count,
                "low_value_loop_count": len(loop_items),
            },
            explanation_zh="该分数估算自动化、模板化、产品化和减少返工可能节省的重复工作时间；它不是精确工时或收入预测。",
            evidence_refs=first_evidence_refs([*opportunity_items, *loop_items]),
            formula_config_path=formula_config_path,
        ),
        make_score_card(
            formulas["reuse_value_proxy"],
            score=clamp_score(
                len(high_evidence_clusters) * float(params["reuse_event_weight"])
                + reusable_count * float(params["reuse_opportunity_weight"])
            ),
            raw_value={
                "high_evidence_cluster_count": len(high_evidence_clusters),
                "reusable_opportunity_count": reusable_count,
            },
            explanation_zh="该分数衡量哪些主题簇和机会更适合变成复用资产，例如模板、脚本、validator 或稳定产品入口。",
            evidence_refs=cluster_evidence or opportunity_evidence,
            formula_config_path=formula_config_path,
        ),
        make_score_card(
            formulas["rework_cost_proxy"],
            score=clamp_score(
                average_loop_score * float(params["rework_loop_score_weight"])
                + average_half_life * float(params["rework_half_life_penalty_weight"])
            ),
            raw_value={
                "average_loop_score": round(average_loop_score, 2),
                "average_action_half_life_days": round(average_half_life, 2),
                "loop_count": len(loop_items),
            },
            explanation_zh="该分数表示低价值循环和行动半衰期带来的返工成本信号；分数高代表更需要收口边界和完成标准。",
            evidence_refs=loop_evidence,
            formula_config_path=formula_config_path,
        ),
        make_score_card(
            formulas["opportunity_score_proxy"],
            score=clamp_score(
                average_opportunity_score * float(params["opportunity_score_weight"])
                + average_opportunity_evidence * float(params["opportunity_evidence_weight"])
            ),
            raw_value={
                "average_opportunity_score": round(average_opportunity_score, 2),
                "average_evidence_ref_count": round(average_opportunity_evidence, 2),
                "opportunity_count": len(opportunity_items),
            },
            explanation_zh="该分数把 S06 的候选机会分和证据密度合成，用于判断哪些线索更值得进入后续 ROI gate。",
            evidence_refs=opportunity_evidence,
            formula_config_path=formula_config_path,
        ),
        make_score_card(
            formulas["skill_compounding_proxy"],
            score=clamp_score(
                compounding_count * float(params["skill_compounding_opportunity_weight"])
                + month_count * float(params["skill_compounding_month_weight"])
            ),
            raw_value={
                "compounding_opportunity_count": compounding_count,
                "observed_month_count": month_count,
            },
            explanation_zh="该分数衡量跨时间重复出现的能力或工作流是否值得固化为长期复利资产。",
            evidence_refs=first_evidence_refs([*opportunities_by_type.get("compounding", []), *cluster_items]),
            formula_config_path=formula_config_path,
        ),
        make_score_card(
            formulas["automation_enhancement_ratio_proxy"],
            score=clamp_score(automation_ratio * float(params["automation_ratio_weight"])),
            raw_value={
                "automation_ratio": round(automation_ratio, 4),
                "enhancement_ratio": round(enhancement_ratio, 4),
                "automation_count": automation_count,
                "augmentation_candidate_count": productization_count + template_count + compounding_count,
            },
            explanation_zh="该比例区分自动化候选和增强候选，避免把产品化、模板化、技能复利都误判成自动化。",
            evidence_refs=opportunity_evidence,
            formula_config_path=formula_config_path,
        ),
    ]
    return cards


def build_personal_economic_proxy(
    database_dir: Path,
    dry_run: bool = False,
    generated_at: str | None = None,
    formula_config_path: Path = FORMULA_CONFIG_PATH,
    clusters_path: Path = CLUSTERS_PATH,
    low_value_path: Path = LOW_VALUE_PATH,
    opportunities_path: Path = OPPORTUNITIES_PATH,
    output_path: Path = OUTPUT_PATH,
) -> dict[str, Any]:
    database_dir = database_dir.resolve()
    generated_at = generated_at or now_utc()
    config, clusters, low_value, opportunities = load_inputs(
        database_dir,
        formula_config_path,
        clusters_path,
        low_value_path,
        opportunities_path,
    )
    score_cards = build_score_cards(config, clusters, low_value, opportunities, formula_config_path)
    validate_score_cards(score_cards)
    overall_score = clamp_score(sum(card["score"] for card in score_cards) / len(score_cards))
    automation_card = next(card for card in score_cards if card["score_key"] == "automation_enhancement_ratio_proxy")
    payload: dict[str, Any] = {
        "schema_version": "memory_atlas_personal_economic_proxy.v1_2_s07_p1",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "status": STATUS,
        "generated_at": generated_at,
        "dry_run": dry_run,
        "writes_files": not dry_run,
        "input_paths": [clusters_path.as_posix(), low_value_path.as_posix(), opportunities_path.as_posix()],
        "formula_config_path": formula_config_path.as_posix(),
        "output_path": output_path.as_posix(),
        "source_task_ids": {
            "clusters": clusters.get("task_id"),
            "low_value_loops": low_value.get("task_id"),
            "opportunities": opportunities.get("task_id"),
        },
        "proxy_summary": {
            "personal_ai_economic_index_score": overall_score,
            "automation_ratio": automation_card["raw_value"]["automation_ratio"],
            "enhancement_ratio": automation_card["raw_value"]["enhancement_ratio"],
            "explanation_zh": "该指数是内部 proxy，用于帮助判断 AI 工作流的时间节省、复用、返工、机会和复利方向。",
            "limitation_zh": "它不是精确收入预测，不是财务建议，不接入外部经济数据库；后续 v2 可预留外部接口但本阶段不实现。",
        },
        "score_cards": score_cards,
        "formula_registry": config.get("formulas"),
        "parameters": config.get("parameters"),
        "external_economic_database": {
            "current_dependency": False,
            "v2_interface": "reserved_not_implemented",
            "allowed_future_scope": "only after explicit future-stage requirement and separate validation",
        },
        "phase_boundary": {
            "does_not_use_external_economic_database": True,
            "does_not_claim_precise_income_prediction": True,
            "does_not_modify_raw": True,
            "does_not_generate_information_roi_gate": True,
            "does_not_generate_what_if_ui": True,
            "next_phase": "S07 P2",
        },
    }
    validate_payload(payload)
    if not dry_run:
        output = database_dir / output_path
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def validate_score_cards(score_cards: list[dict[str, Any]]) -> None:
    required_keys = {
        "time_saved_proxy",
        "reuse_value_proxy",
        "rework_cost_proxy",
        "opportunity_score_proxy",
        "skill_compounding_proxy",
        "automation_enhancement_ratio_proxy",
    }
    keys = {card.get("score_key") for card in score_cards}
    if keys != required_keys:
        raise EconomicProxyBuildError(f"score card keys mismatch: {sorted(keys)}")
    for card in score_cards:
        card_id = card.get("score_key")
        if not card.get("formula_id") or not card.get("formula_source"):
            raise EconomicProxyBuildError(f"score card {card_id} missing formula source")
        if not card.get("explanation_zh") or not card.get("formula_expression_zh"):
            raise EconomicProxyBuildError(f"score card {card_id} missing Chinese explanation or expression")
        if not card.get("parameter_refs"):
            raise EconomicProxyBuildError(f"score card {card_id} missing parameter refs")
        if not card.get("evidence_refs"):
            raise EconomicProxyBuildError(f"score card {card_id} missing evidence refs")
        if not (0 <= int(card.get("score", -1)) <= 100):
            raise EconomicProxyBuildError(f"score card {card_id} score out of range")


def validate_payload(payload: dict[str, Any]) -> None:
    if payload.get("task_id") != TASK_ID or payload.get("acceptance_id") != ACCEPTANCE_ID:
        raise EconomicProxyBuildError("payload identity mismatch")
    if payload.get("status") != STATUS:
        raise EconomicProxyBuildError("payload status mismatch")
    if payload.get("external_economic_database", {}).get("current_dependency") is not False:
        raise EconomicProxyBuildError("payload must not depend on external economic database")
    boundary = payload.get("phase_boundary") or {}
    if boundary.get("does_not_use_external_economic_database") is not True:
        raise EconomicProxyBuildError("phase boundary must block external economic database")
    if boundary.get("does_not_claim_precise_income_prediction") is not True:
        raise EconomicProxyBuildError("phase boundary must block precise income prediction")
    if boundary.get("does_not_generate_information_roi_gate") is not True:
        raise EconomicProxyBuildError("S07 P1 must not implement S07 P2 information ROI gate")
    validate_score_cards(payload.get("score_cards") or [])


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Memory Atlas S07 P1 Personal Economic Proxy builder.")
    parser.add_argument("--database-dir", type=Path, default=ROOT)
    parser.add_argument("--formula-config", type=Path, default=FORMULA_CONFIG_PATH)
    parser.add_argument("--clusters", type=Path, default=CLUSTERS_PATH)
    parser.add_argument("--low-value", type=Path, default=LOW_VALUE_PATH)
    parser.add_argument("--opportunities", type=Path, default=OPPORTUNITIES_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        payload = build_personal_economic_proxy(
            args.database_dir,
            dry_run=args.dry_run,
            formula_config_path=args.formula_config,
            clusters_path=args.clusters,
            low_value_path=args.low_value,
            opportunities_path=args.opportunities,
            output_path=args.output,
        )
    except EconomicProxyBuildError as exc:
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
