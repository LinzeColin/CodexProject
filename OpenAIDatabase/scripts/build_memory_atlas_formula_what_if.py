#!/usr/bin/env python3
"""Build Memory Atlas S07 P3 Formula What-if config preview outputs."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
WHAT_IF_CONFIG_PATH = Path("机器治理/参数与公式/formula_what_if_defaults.v1_2_s07_p3.json")
ECONOMIC_PROXY_PATH = Path("data/derived/economic_proxy/personal_economic_proxy.json")
INFORMATION_ROI_PATH = Path("data/derived/information_roi/information_roi_gate.json")
OUTPUT_PATH = Path("data/derived/economic_proxy/formula_what_if_preview.json")
TASK_ID = "MA-V12-S07P3"
ACCEPTANCE_ID = "ACC-MA-V12-S07P3"
STATUS = "phase_s07_p3_formula_what_if_completed_pending_s07_review"


class FormulaWhatIfBuildError(RuntimeError):
    pass


def now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path, label: str) -> dict[str, Any]:
    if not path.exists():
        raise FormulaWhatIfBuildError(f"{label} missing: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise FormulaWhatIfBuildError(f"{label} must be a JSON object: {path}")
    return payload


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def clamp_score(value: float, floor: float = 0.0, ceiling: float = 100.0) -> int:
    return int(round(max(floor, min(ceiling, value))))


def has_cjk(value: Any) -> bool:
    return any("\u3400" <= char <= "\u9fff" for char in str(value or ""))


def validate_config(config: dict[str, Any]) -> None:
    if config.get("task_id") != TASK_ID or config.get("acceptance_id") != ACCEPTANCE_ID:
        raise FormulaWhatIfBuildError("what-if config identity mismatch")
    if config.get("active_config_write") is not False or config.get("proposal_required_before_apply") is not True:
        raise FormulaWhatIfBuildError("what-if config must be proposal-only and must not write active config")
    boundary = config.get("scope_boundary") or {}
    if boundary.get("external_economic_database_dependency") is not False:
        raise FormulaWhatIfBuildError("what-if config must not depend on external economic database")
    if boundary.get("precise_income_prediction") is not False or boundary.get("financial_advice") is not False:
        raise FormulaWhatIfBuildError("what-if config must not claim precise prediction or financial advice")
    if boundary.get("active_config_mutation") is not False:
        raise FormulaWhatIfBuildError("what-if config must not mutate active formula config")
    params = config.get("parameters")
    if not isinstance(params, dict):
        raise FormulaWhatIfBuildError("what-if config missing parameters")
    required_weights = {
        "time_saved_weight",
        "reuse_value_weight",
        "opportunity_value_weight",
        "skill_compounding_weight",
        "automation_alignment_weight",
        "rework_cost_weight",
        "low_value_loop_penalty_weight",
    }
    default_weights = params.get("default_weights") if isinstance(params.get("default_weights"), dict) else {}
    bounds = params.get("adjustable_weight_bounds") if isinstance(params.get("adjustable_weight_bounds"), dict) else {}
    missing = sorted(required_weights - set(default_weights) | required_weights - set(bounds))
    if missing:
        raise FormulaWhatIfBuildError(f"what-if config missing adjustable weights: {', '.join(missing)}")
    formulas = as_list(config.get("formulas"))
    score_keys = {str(item.get("score_key")) for item in formulas if isinstance(item, dict)}
    if {"formula_what_if_proxy_score", "what_if_parameter_proposal"} - score_keys:
        raise FormulaWhatIfBuildError("what-if config missing formulas")
    for item in formulas:
        if not isinstance(item, dict) or not item.get("formula_id") or not has_cjk(item.get("expression_zh")):
            raise FormulaWhatIfBuildError("what-if formula missing id or Chinese expression")
    for scenario in as_list(config.get("scenarios")):
        if not isinstance(scenario, dict) or not scenario.get("scenario_id") or not has_cjk(scenario.get("name_zh")):
            raise FormulaWhatIfBuildError("invalid what-if scenario")
        for key, value in (scenario.get("weights") or {}).items():
            if key not in bounds:
                raise FormulaWhatIfBuildError(f"scenario {scenario.get('scenario_id')} references unknown weight {key}")
            minimum = float(bounds[key]["min"])
            maximum = float(bounds[key]["max"])
            if not minimum <= float(value) <= maximum:
                raise FormulaWhatIfBuildError(f"scenario {scenario.get('scenario_id')} weight {key} out of bounds")


def score_cards_by_key(economic_proxy: dict[str, Any]) -> dict[str, dict[str, Any]]:
    cards = {}
    for item in as_list(economic_proxy.get("score_cards")):
        if isinstance(item, dict) and item.get("score_key"):
            cards[str(item["score_key"])] = item
    required = {
        "time_saved_proxy",
        "reuse_value_proxy",
        "rework_cost_proxy",
        "opportunity_score_proxy",
        "skill_compounding_proxy",
        "automation_enhancement_ratio_proxy",
    }
    missing = sorted(required - set(cards))
    if missing:
        raise FormulaWhatIfBuildError(f"economic proxy missing score cards: {', '.join(missing)}")
    return cards


def merged_weights(default_weights: dict[str, Any], scenario: dict[str, Any]) -> dict[str, float]:
    weights = {key: float(value) for key, value in default_weights.items()}
    for key, value in (scenario.get("weights") or {}).items():
        weights[key] = float(value)
    return weights


def score_from_weights(cards: dict[str, dict[str, Any]], weights: dict[str, float], params: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    positive_parts = {
        "time_saved_proxy": ("time_saved_weight", float(cards["time_saved_proxy"]["score"])),
        "reuse_value_proxy": ("reuse_value_weight", float(cards["reuse_value_proxy"]["score"])),
        "opportunity_score_proxy": ("opportunity_value_weight", float(cards["opportunity_score_proxy"]["score"])),
        "skill_compounding_proxy": ("skill_compounding_weight", float(cards["skill_compounding_proxy"]["score"])),
        "automation_enhancement_ratio_proxy": ("automation_alignment_weight", float(cards["automation_enhancement_ratio_proxy"]["score"])),
    }
    weighted_total = sum(score * weights[weight_key] for weight_key, score in positive_parts.values())
    weight_total = max(sum(weights[weight_key] for weight_key, _score in positive_parts.values()), float(params["epsilon"]))
    weighted_positive_score = weighted_total / weight_total
    rework_score = float(cards["rework_cost_proxy"]["score"])
    rework_excess = max(0.0, rework_score - float(params["neutral_rework_score"]))
    rework_penalty = (
        rework_excess
        * weights["rework_cost_weight"]
        * weights["low_value_loop_penalty_weight"]
        * float(params["rework_penalty_scale"])
    )
    score = clamp_score(
        weighted_positive_score - rework_penalty,
        float(params["score_floor"]),
        float(params["score_ceiling"]),
    )
    components = {
        "weighted_positive_score": round(weighted_positive_score, 2),
        "rework_score": round(rework_score, 2),
        "rework_penalty": round(rework_penalty, 2),
        "signals": {
            key: {
                "score": round(score_value, 2),
                "weight": round(weights[weight_key], 4),
                "weighted_signal": round(score_value * weights[weight_key], 2),
            }
            for key, (weight_key, score_value) in positive_parts.items()
        },
    }
    return score, components


def top_parameter_impacts(
    cards: dict[str, dict[str, Any]],
    default_weights: dict[str, Any],
    scenario_weights: dict[str, float],
    params: dict[str, Any],
) -> list[dict[str, Any]]:
    baseline_score, _components = score_from_weights(cards, {key: float(value) for key, value in default_weights.items()}, params)
    impacts = []
    for key, value in scenario_weights.items():
        default_value = float(default_weights[key])
        if abs(value - default_value) < 0.0001:
            continue
        test_weights = {item_key: float(item_value) for item_key, item_value in default_weights.items()}
        test_weights[key] = value
        changed_score, _changed_components = score_from_weights(cards, test_weights, params)
        impacts.append({
            "parameter": key,
            "default": default_value,
            "scenario": value,
            "single_parameter_score_delta": changed_score - baseline_score,
        })
    return sorted(impacts, key=lambda item: abs(float(item["single_parameter_score_delta"])), reverse=True)


def build_scenarios(config: dict[str, Any], economic_proxy: dict[str, Any]) -> list[dict[str, Any]]:
    params = config["parameters"]
    default_weights = params["default_weights"]
    cards = score_cards_by_key(economic_proxy)
    baseline_weights = {key: float(value) for key, value in default_weights.items()}
    baseline_score, _baseline_components = score_from_weights(cards, baseline_weights, params)
    scenarios = []
    for scenario in as_list(config.get("scenarios")):
        weights = merged_weights(default_weights, scenario)
        score, components = score_from_weights(cards, weights, params)
        scenarios.append({
            "scenario_id": scenario["scenario_id"],
            "name_zh": scenario["name_zh"],
            "description_zh": scenario["description_zh"],
            "formula_id": "FORM-MA-V12-S07P3-001",
            "formula_source": WHAT_IF_CONFIG_PATH.as_posix(),
            "adjustable_weights": {key: round(value, 4) for key, value in weights.items()},
            "weighted_proxy_score": score,
            "score_delta_vs_baseline": score - baseline_score,
            "score_components": components,
            "top_parameter_impacts": top_parameter_impacts(cards, default_weights, weights, params),
            "parameter_change_proposal": {
                "formula_id": "FORM-MA-V12-S07P3-002",
                "target_active_config": config["active_formula_config_path"],
                "active_config_write": False,
                "proposal_required_before_apply": True,
                "proposed_weight_overrides": scenario.get("weights") or {},
                "explanation_zh": "这是 what-if 参数预览，不会直接修改 active formula config。若未来采纳，需要另走 proposal/apply gate。",
            },
        })
    return scenarios


def validate_inputs(economic_proxy: dict[str, Any], information_roi: dict[str, Any]) -> None:
    if economic_proxy.get("task_id") != "MA-V12-S07P1" or economic_proxy.get("acceptance_id") != "ACC-MA-V12-S07P1":
        raise FormulaWhatIfBuildError("economic proxy identity mismatch")
    if economic_proxy.get("external_economic_database", {}).get("current_dependency") is not False:
        raise FormulaWhatIfBuildError("economic proxy must not depend on external economic database")
    if information_roi.get("task_id") != "MA-V12-S07P2" or information_roi.get("acceptance_id") != "ACC-MA-V12-S07P2":
        raise FormulaWhatIfBuildError("information ROI identity mismatch")
    if information_roi.get("phase_boundary", {}).get("does_not_use_external_economic_database") is not True:
        raise FormulaWhatIfBuildError("information ROI must not depend on external economic database")


def build_formula_what_if(
    database_dir: Path,
    dry_run: bool = False,
    generated_at: str | None = None,
    config_path: Path = WHAT_IF_CONFIG_PATH,
    economic_proxy_path: Path = ECONOMIC_PROXY_PATH,
    information_roi_path: Path = INFORMATION_ROI_PATH,
    output_path: Path = OUTPUT_PATH,
) -> dict[str, Any]:
    database_dir = database_dir.resolve()
    generated_at = generated_at or now_utc()
    config = load_json(database_dir / config_path, "formula what-if config")
    validate_config(config)
    economic_proxy = load_json(database_dir / economic_proxy_path, "economic proxy output")
    information_roi = load_json(database_dir / information_roi_path, "information ROI output")
    validate_inputs(economic_proxy, information_roi)
    scenarios = build_scenarios(config, economic_proxy)
    payload: dict[str, Any] = {
        "schema_version": "memory_atlas_formula_what_if_preview.v1_2_s07_p3",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "status": STATUS,
        "generated_at": generated_at,
        "dry_run": dry_run,
        "writes_files": not dry_run,
        "simulator_mode": "config_preview_only",
        "config_path": config_path.as_posix(),
        "active_formula_config_path": config["active_formula_config_path"],
        "input_paths": [economic_proxy_path.as_posix(), information_roi_path.as_posix()],
        "output_path": output_path.as_posix(),
        "source_task_ids": {
            "economic_proxy": economic_proxy.get("task_id"),
            "information_roi": information_roi.get("task_id"),
        },
        "base_score": economic_proxy.get("proxy_summary", {}).get("personal_ai_economic_index_score"),
        "scenario_count": len(scenarios),
        "scenarios": scenarios,
        "formulas": config.get("formulas"),
        "parameters": config.get("parameters"),
        "human_readable_summary_zh": "Formula What-if Simulator 当前为配置预览：可查看时间节省、复用价值、长期复利、返工成本和低价值循环惩罚等权重变化，但不会直接修改 active formula config。",
        "phase_boundary": {
            "does_not_use_external_economic_database": True,
            "does_not_claim_precise_income_prediction": True,
            "does_not_provide_financial_advice": True,
            "does_not_modify_raw": True,
            "does_not_modify_runtime_ui": True,
            "does_not_mutate_active_formula_config": True,
            "requires_proposal_before_apply": True,
            "next_phase": "S07 Review",
        },
    }
    validate_payload(payload)
    if not dry_run:
        output = database_dir / output_path
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def validate_payload(payload: dict[str, Any]) -> None:
    if payload.get("task_id") != TASK_ID or payload.get("acceptance_id") != ACCEPTANCE_ID:
        raise FormulaWhatIfBuildError("payload identity mismatch")
    if payload.get("status") != STATUS:
        raise FormulaWhatIfBuildError("payload status mismatch")
    boundary = payload.get("phase_boundary") or {}
    if boundary.get("does_not_use_external_economic_database") is not True:
        raise FormulaWhatIfBuildError("payload must block external economic database")
    if boundary.get("does_not_claim_precise_income_prediction") is not True:
        raise FormulaWhatIfBuildError("payload must block precise income prediction")
    if boundary.get("does_not_provide_financial_advice") is not True:
        raise FormulaWhatIfBuildError("payload must block financial advice")
    if boundary.get("does_not_mutate_active_formula_config") is not True:
        raise FormulaWhatIfBuildError("payload must not mutate active formula config")
    scenarios = as_list(payload.get("scenarios"))
    if len(scenarios) < 4:
        raise FormulaWhatIfBuildError("payload must expose multiple what-if scenarios")
    required = {"time_saved_weight", "reuse_value_weight", "skill_compounding_weight"}
    mentioned = set()
    for scenario in scenarios:
        if not scenario.get("parameter_change_proposal", {}).get("proposal_required_before_apply"):
            raise FormulaWhatIfBuildError(f"scenario {scenario.get('scenario_id')} missing proposal gate")
        if scenario.get("parameter_change_proposal", {}).get("active_config_write") is not False:
            raise FormulaWhatIfBuildError(f"scenario {scenario.get('scenario_id')} writes active config")
        weights = scenario.get("adjustable_weights") if isinstance(scenario.get("adjustable_weights"), dict) else {}
        mentioned.update(weights)
        if not has_cjk(scenario.get("description_zh")):
            raise FormulaWhatIfBuildError(f"scenario {scenario.get('scenario_id')} missing Chinese description")
        if not 0 <= int(scenario.get("weighted_proxy_score", -1)) <= 100:
            raise FormulaWhatIfBuildError(f"scenario {scenario.get('scenario_id')} score out of range")
    if required - mentioned:
        raise FormulaWhatIfBuildError("payload missing required adjustable weight coverage")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Memory Atlas S07 P3 Formula What-if builder.")
    parser.add_argument("--database-dir", type=Path, default=ROOT)
    parser.add_argument("--config", type=Path, default=WHAT_IF_CONFIG_PATH)
    parser.add_argument("--economic-proxy", type=Path, default=ECONOMIC_PROXY_PATH)
    parser.add_argument("--information-roi", type=Path, default=INFORMATION_ROI_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        payload = build_formula_what_if(
            args.database_dir,
            dry_run=args.dry_run,
            config_path=args.config,
            economic_proxy_path=args.economic_proxy,
            information_roi_path=args.information_roi,
            output_path=args.output,
        )
    except FormulaWhatIfBuildError as exc:
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
