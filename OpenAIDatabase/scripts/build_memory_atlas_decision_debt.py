#!/usr/bin/env python3
"""Build Memory Atlas S09 P3 Decision Debt Ledger."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = Path("机器治理/行为智能模型/decision_debt.v1_2_s09_p3.json")
LOW_VALUE_PATH = Path("data/derived/behavior_intelligence/low_value_loops.json")
SELF_ITERATION_PATH = Path("data/derived/behavior_intelligence/self_iteration_suggestions.json")
LATENT_PATH = Path("data/derived/behavior_intelligence/latent_signals.json")
OUTPUT_PATH = Path("data/derived/behavior_intelligence/decision_debt_ledger.json")
TASK_ID = "MA-V12-S09P3"
ACCEPTANCE_ID = "ACC-MA-V12-S09P3"
STATUS = "phase_s09_p3_decision_debt_completed_pending_s09_review"
REQUIRED_FIELDS = {
    "decision_debt_id",
    "source_debt_ids",
    "debt_type",
    "decision_area_zh",
    "repeated_discussion_signal_zh",
    "evidence_refs",
    "minimal_next_step",
    "linked_self_iteration_suggestion_ids",
    "confidence",
    "not_pressure_list",
}


class DecisionDebtBuildError(RuntimeError):
    pass


def now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def stable_hash(value: str, length: int = 12) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:length]


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def load_json(path: Path, label: str) -> dict[str, Any]:
    if not path.exists():
        raise DecisionDebtBuildError(f"{label} missing: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise DecisionDebtBuildError(f"{label} must be a JSON object: {path}")
    return payload


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
    return refs


def target_types_for_debt(debt_type: str) -> list[str]:
    if debt_type == "discussion_without_landing":
        return ["personalization", "style"]
    if debt_type == "repeated_rework":
        return ["config", "memory"]
    if debt_type == "scope_creep":
        return ["AGENTS", "config"]
    if debt_type == "over_optimization":
        return ["style", "config"]
    return ["config", "personalization"]


def linked_suggestions(debt_type: str, suggestions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    preferred = set(target_types_for_debt(debt_type))
    matches = [item for item in suggestions if item.get("target_type") in preferred]
    return (matches or suggestions)[:2]


def minimal_next_step_for(debt_type: str, decision_area: str, max_minutes: int) -> dict[str, Any]:
    if debt_type == "discussion_without_landing":
        step = f"为「{decision_area}」写一条最小交付件定义，并决定继续推进或归档。"
        artifact = "一条包含 owner、交付件、验收标准和归档条件的记录。"
        stop = "如果 30 分钟内无法写出交付件和验收标准，则标记为暂不推进。"
    elif debt_type == "repeated_rework":
        step = f"为「{decision_area}」补一条完成标准和复用入口，避免下一轮重复返工。"
        artifact = "一个可复用入口或完成标准片段。"
        stop = "如果找不到可复用入口，只保留一次性完成标准，不继续扩展。"
    elif debt_type == "scope_creep":
        step = f"把「{decision_area}」拆成一个主目标和一个后续 backlog。"
        artifact = "主目标、非目标和后续 backlog 各一条。"
        stop = "如果无法拆分，先保留主目标，其他内容进入后续 backlog。"
    elif debt_type == "over_optimization":
        step = f"为「{decision_area}」写一个质量上限，超过上限的优化先暂缓。"
        artifact = "一条质量上限和停止条件。"
        stop = "如果优化不能提高验收证据或决策价值，则不进入本轮。"
    else:
        step = f"为「{decision_area}」确认一个可验证的最小下一步。"
        artifact = "一条最小下一步和停止条件。"
        stop = "如果不能验证，先归档为候选。"
    return {
        "step_zh": step,
        "owner_role": "human_owner",
        "expected_artifact_zh": artifact,
        "effort_minutes_max": max(1, min(int(max_minutes), 30)),
        "stop_condition_zh": stop,
        "validation_zh": "下一轮只检查该最小交付件是否存在，不展开为压力清单。",
    }


def confidence_for(debt: dict[str, Any], evidence_refs: list[dict[str, Any]], max_confidence: float) -> float:
    base_by_type = {
        "discussion_without_landing": 0.68,
        "repeated_rework": 0.66,
        "scope_creep": 0.62,
        "over_optimization": 0.6,
    }
    base = base_by_type.get(str(debt.get("debt_type")), 0.58)
    evidence_bonus = min(len(evidence_refs), 5) * 0.01
    return round(min(float(max_confidence), base + evidence_bonus), 2)


def make_debt_item(
    *,
    debt: dict[str, Any],
    suggestions: list[dict[str, Any]],
    config: dict[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    debt_type = str(debt.get("debt_type") or "unknown")
    decision_area = str(debt.get("decision_area") or "未命名决策区域")
    linked = linked_suggestions(debt_type, suggestions)
    evidence_refs = unique_evidence_refs([debt] + linked, limit=8)
    if not evidence_refs:
        raise DecisionDebtBuildError(f"decision debt {debt.get('debt_id')} missing evidence refs")
    max_minutes = int(config["minimal_next_step_policy"]["effort_minutes_max"])
    max_confidence = float(config["confidence_policy"]["max_confidence"])
    source_debt_id = str(debt.get("debt_id"))
    return {
        "decision_debt_id": f"s09p3_debt_{stable_hash(source_debt_id + debt_type)}",
        "source_debt_ids": [source_debt_id],
        "source_loop_ids": [str(debt.get("loop_id"))],
        "debt_type": debt_type,
        "decision_area_zh": decision_area,
        "repeated_discussion_signal_zh": str(debt.get("debt_signal") or debt.get("suggested_closure_question") or ""),
        "evidence_summary_zh": f"来自 S06 低价值循环候选和 S09 自我迭代建议的交叉证据；当前只作为候选决策债。",
        "evidence_refs": evidence_refs,
        "minimal_next_step": minimal_next_step_for(debt_type, decision_area, max_minutes),
        "linked_self_iteration_suggestion_ids": [str(item.get("suggestion_id")) for item in linked if item.get("suggestion_id")],
        "linked_proposal_ids": [
            str(item.get("proposal", {}).get("proposal_id"))
            for item in linked
            if isinstance(item.get("proposal"), dict) and item.get("proposal", {}).get("proposal_id")
        ],
        "status": str(config["ledger_policy"].get("status") or "open_candidate"),
        "confidence": confidence_for(debt, evidence_refs, max_confidence),
        "not_pressure_list": True,
        "not_psychological_diagnosis": True,
        "not_personality_label": True,
        "not_applied": True,
        "why_not_pressure_list_zh": "只给一个最小下一步；未被采纳时降级或归档，不扩展成待办压力列表。",
        "closure_rule_zh": "如果最小下一步没有产出验收证据，下一轮优先归档而不是继续讨论。",
        "generated_at": generated_at,
    }


def validate_config(config: dict[str, Any]) -> None:
    if config.get("task_id") != TASK_ID or config.get("acceptance_id") != ACCEPTANCE_ID:
        raise DecisionDebtBuildError("decision debt config identity mismatch")
    configured_fields = set(as_list(config.get("required_debt_fields")))
    missing = sorted(REQUIRED_FIELDS - configured_fields)
    if missing:
        raise DecisionDebtBuildError(f"decision debt config missing fields: {', '.join(missing)}")
    if int(config.get("ledger_policy", {}).get("min_entries") or 0) <= 0:
        raise DecisionDebtBuildError("decision debt config min_entries must be positive")
    if config.get("ledger_policy", {}).get("pressure_list_allowed") is not False:
        raise DecisionDebtBuildError("S09 P3 must not allow pressure lists")
    if int(config.get("minimal_next_step_policy", {}).get("effort_minutes_max") or 0) <= 0:
        raise DecisionDebtBuildError("minimal next step effort must be positive")
    boundary = config.get("scope_boundary") if isinstance(config.get("scope_boundary"), dict) else {}
    if boundary.get("raw_mutation") is not False:
        raise DecisionDebtBuildError("S09 P3 must not mutate raw")
    if boundary.get("proposal_apply_execution") is not False:
        raise DecisionDebtBuildError("S09 P3 must not apply proposals")
    if boundary.get("stage_review") != "deferred_to_s09_review":
        raise DecisionDebtBuildError("S09 P3 must defer review to S09 Review")


def validate_inputs(low_value: dict[str, Any], self_iteration: dict[str, Any], latent: dict[str, Any]) -> None:
    if low_value.get("task_id") != "MA-V12-S06P2" or low_value.get("acceptance_id") != "ACC-MA-V12-S06P2":
        raise DecisionDebtBuildError("low-value loop input identity mismatch")
    if self_iteration.get("task_id") != "MA-V12-S09P2" or self_iteration.get("acceptance_id") != "ACC-MA-V12-S09P2":
        raise DecisionDebtBuildError("self-iteration input identity mismatch")
    if latent.get("task_id") != "MA-V12-S09P1" or latent.get("acceptance_id") != "ACC-MA-V12-S09P1":
        raise DecisionDebtBuildError("latent signal input identity mismatch")
    if not as_list(low_value.get("decision_debt_ledger")):
        raise DecisionDebtBuildError("low-value loop input has no decision debt candidates")
    if not as_list(self_iteration.get("self_iteration_suggestions")):
        raise DecisionDebtBuildError("self-iteration input has no suggestions")


def validate_payload(payload: dict[str, Any], config: dict[str, Any]) -> None:
    if payload.get("task_id") != TASK_ID or payload.get("acceptance_id") != ACCEPTANCE_ID:
        raise DecisionDebtBuildError("decision debt payload identity mismatch")
    if payload.get("status") != STATUS:
        raise DecisionDebtBuildError("decision debt payload status mismatch")
    ledger = [item for item in as_list(payload.get("decision_debt_ledger")) if isinstance(item, dict)]
    min_entries = int(config["ledger_policy"]["min_entries"])
    if len(ledger) < min_entries:
        raise DecisionDebtBuildError("decision debt payload has too few entries")
    bad_items: list[str] = []
    blocked = [str(term) for term in as_list(config.get("blocked_output_terms"))]
    max_confidence = float(config["confidence_policy"]["max_confidence"])
    max_effort = int(config["minimal_next_step_policy"]["effort_minutes_max"])
    for item in ledger:
        item_id = item.get("decision_debt_id")
        for field in REQUIRED_FIELDS:
            if item.get(field) in (None, "", []):
                bad_items.append(f"{item_id}:missing_{field}")
        if float(item.get("confidence") or 0) > max_confidence:
            bad_items.append(f"{item_id}:confidence_too_high")
        if item.get("not_pressure_list") is not True:
            bad_items.append(f"{item_id}:pressure_list_boundary_missing")
        if item.get("not_psychological_diagnosis") is not True:
            bad_items.append(f"{item_id}:psychological_boundary_missing")
        if item.get("not_personality_label") is not True:
            bad_items.append(f"{item_id}:personality_boundary_missing")
        step = item.get("minimal_next_step") if isinstance(item.get("minimal_next_step"), dict) else {}
        for field in ["step_zh", "expected_artifact_zh", "stop_condition_zh"]:
            if not str(step.get(field) or "").strip():
                bad_items.append(f"{item_id}:minimal_next_step_missing_{field}")
        if int(step.get("effort_minutes_max") or 0) <= 0 or int(step.get("effort_minutes_max") or 0) > max_effort:
            bad_items.append(f"{item_id}:minimal_next_step_invalid_effort")
        joined = " ".join(
            str(value)
            for value in [
                item.get("decision_area_zh"),
                item.get("repeated_discussion_signal_zh"),
                item.get("evidence_summary_zh"),
                step.get("step_zh"),
                step.get("stop_condition_zh"),
            ]
        )
        if any(term and term in joined for term in blocked):
            bad_items.append(f"{item_id}:blocked_term")
    boundary = payload.get("phase_boundary") if isinstance(payload.get("phase_boundary"), dict) else {}
    if boundary.get("does_not_generate_pressure_list") is not True:
        bad_items.append("phase_boundary:pressure_list_boundary_missing")
    if boundary.get("does_not_apply_proposals") is not True:
        bad_items.append("phase_boundary:proposal_apply_missing")
    if boundary.get("does_not_modify_raw") is not True:
        bad_items.append("phase_boundary:raw_mutation_missing")
    if boundary.get("next_phase") != "S09 Review":
        bad_items.append("phase_boundary:next_phase_not_s09_review")
    summary = payload.get("safety_summary") if isinstance(payload.get("safety_summary"), dict) else {}
    if summary.get("all_items_have_minimal_next_step") is not True:
        bad_items.append("safety_summary:minimal_next_step_not_true")
    if summary.get("pressure_list_created") is not False:
        bad_items.append("safety_summary:pressure_list_created")
    if bad_items:
        raise DecisionDebtBuildError("; ".join(bad_items))


def build_decision_debt_ledger(
    database_dir: Path,
    *,
    dry_run: bool = False,
    generated_at: str | None = None,
    output_path: Path = OUTPUT_PATH,
    config_path: Path = CONFIG_PATH,
    low_value_path: Path = LOW_VALUE_PATH,
    self_iteration_path: Path = SELF_ITERATION_PATH,
    latent_path: Path = LATENT_PATH,
) -> dict[str, Any]:
    database_dir = database_dir.resolve()
    generated_at = generated_at or now_utc()
    config = load_json(database_dir / config_path, "decision debt config")
    low_value = load_json(database_dir / low_value_path, "low-value loops")
    self_iteration = load_json(database_dir / self_iteration_path, "self-iteration suggestions")
    latent = load_json(database_dir / latent_path, "latent signals")
    validate_config(config)
    validate_inputs(low_value, self_iteration, latent)
    source_debts = [item for item in as_list(low_value.get("decision_debt_ledger")) if isinstance(item, dict)]
    priority = {"discussion_without_landing": 0, "repeated_rework": 1, "scope_creep": 2, "over_optimization": 3}
    source_debts = sorted(source_debts, key=lambda item: (priority.get(str(item.get("debt_type")), 9), str(item.get("debt_id"))))
    suggestions = [item for item in as_list(self_iteration.get("self_iteration_suggestions")) if isinstance(item, dict)]
    max_entries = int(config["ledger_policy"]["max_entries"])
    ledger = [
        make_debt_item(debt=debt, suggestions=suggestions, config=config, generated_at=generated_at)
        for debt in source_debts[:max_entries]
    ]
    payload: dict[str, Any] = {
        "schema_version": "memory_atlas_decision_debt_ledger.v1_2_s09_p3",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "status": STATUS,
        "generated_at": generated_at,
        "dry_run": dry_run,
        "writes_files": not dry_run,
        "config_path": config_path.as_posix(),
        "output_path": output_path.as_posix(),
        "input_paths": [low_value_path.as_posix(), self_iteration_path.as_posix(), latent_path.as_posix()],
        "input_task_ids": {
            "low_value_loops": low_value.get("task_id"),
            "self_iteration_suggestions": self_iteration.get("task_id"),
            "latent_signals": latent.get("task_id"),
        },
        "decision_debt_count": len(ledger),
        "decision_debt_types": sorted({str(item.get("debt_type")) for item in ledger}),
        "decision_debt_ledger": ledger,
        "safety_summary": {
            "all_items_have_minimal_next_step": all(bool(item.get("minimal_next_step", {}).get("step_zh")) for item in ledger),
            "pressure_list_created": False,
            "proposal_apply_execution": False,
            "raw_mutation": False,
            "psychological_diagnosis_output": False,
            "personality_label_output": False,
        },
        "phase_boundary": {
            "does_not_generate_pressure_list": True,
            "does_not_apply_proposals": True,
            "requires_human_approval_before_apply": True,
            "does_not_modify_raw": True,
            "does_not_upload_github_main": True,
            "does_not_output_psychological_diagnosis": True,
            "does_not_output_personality_label": True,
            "stage_review_deferred_to": "S09 Review",
            "next_phase": "S09 Review",
        },
    }
    validate_payload(payload, config)
    if not dry_run:
        output = database_dir / output_path
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Memory Atlas S09 P3 decision debt ledger builder.")
    parser.add_argument("--database-dir", type=Path, default=ROOT)
    parser.add_argument("--config", type=Path, default=CONFIG_PATH)
    parser.add_argument("--low-value", type=Path, default=LOW_VALUE_PATH)
    parser.add_argument("--self-iteration", type=Path, default=SELF_ITERATION_PATH)
    parser.add_argument("--latent", type=Path, default=LATENT_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        payload = build_decision_debt_ledger(
            args.database_dir,
            dry_run=args.dry_run,
            output_path=args.output,
            config_path=args.config,
            low_value_path=args.low_value,
            self_iteration_path=args.self_iteration,
            latent_path=args.latent,
        )
    except DecisionDebtBuildError as exc:
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
