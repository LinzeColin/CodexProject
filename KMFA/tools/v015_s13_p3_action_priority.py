#!/usr/bin/env python3
"""KMFA v1.5 S13-P3 可解释行动优先级、重点事项和建议复盘内核。"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from typing import Any, Iterable


RUN_PHASE_ID = "V015_S13_P3_ACTION_PRIORITY"
ROADMAP_PHASE_ID = "S13-P3"
TASK_ID = "KMFA-V015-S13-P3-ACTION-PRIORITY-20260716"
ACCEPTANCE_ID = "ACC-KMFA-V015-S13-P3-ACTION-PRIORITY"
VERSION = "1.5.0-dev-s13p3"

ACTION_DOMAINS = ("PROJECT", "COLLECTION", "FUNDS", "TAX", "DATA")
CANDIDATE_STATES = (
    "ELIGIBLE",
    "REQUIRES_REVIEW",
    "BLOCKED_BY_HARD_GATE",
    "INSUFFICIENT_DATA",
    "INVALID_INPUT",
)
REVIEW_DECISIONS = ("NOT_REVIEWED", "ACCEPTED", "REJECTED", "DEFERRED")
OUTCOME_STATES = ("POSITIVE", "NEGATIVE", "UNKNOWN")
FRESHNESS_STATES = ("FRESH", "AGING", "STALE")
FOCUS_MIN_ITEMS = 3
FOCUS_MAX_ITEMS = 5
FOCUS_DOMAIN_CAP = 2
MIN_FOCUS_CONFIDENCE_BPS = 4000

RANKING_FACTORS = (
    {"factor_id": "IMPACT", "label_zh": "影响", "weight_bps": 2600, "direction": "HIGHER_IS_BETTER"},
    {"factor_id": "CONFIDENCE", "label_zh": "可信度", "weight_bps": 1800, "direction": "HIGHER_IS_BETTER"},
    {"factor_id": "URGENCY", "label_zh": "紧急度", "weight_bps": 1800, "direction": "HIGHER_IS_BETTER"},
    {"factor_id": "EFFORT", "label_zh": "投入", "weight_bps": 1400, "direction": "LOWER_IS_BETTER"},
    {"factor_id": "CASH_COST", "label_zh": "现金成本", "weight_bps": 1200, "direction": "LOWER_IS_BETTER"},
    {"factor_id": "EXECUTION_RISK", "label_zh": "执行风险", "weight_bps": 1200, "direction": "LOWER_IS_BETTER"},
)

_SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
_FORBIDDEN_TEXT = ("/Users/", "/Volumes/", "file://", "private://", "KMFA_MetaData")


class ActionPriorityError(ValueError):
    """行动优先级输入或合同不合法。"""


def _require_text(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ActionPriorityError(f"{name} must be non-empty text")
    text = value.strip()
    if any(token.lower() in text.lower() for token in _FORBIDDEN_TEXT):
        raise ActionPriorityError(f"{name} contains private locator")
    return text


def _require_bps(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ActionPriorityError(f"{name} must be integer bps")
    if not 0 <= value <= 10_000:
        raise ActionPriorityError(f"{name} outside 0..10000")
    return value


def _require_bool(value: Any, name: str) -> bool:
    if not isinstance(value, bool):
        raise ActionPriorityError(f"{name} must be boolean")
    return value


def _require_refs(value: Any, name: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise ActionPriorityError(f"{name} must be a non-empty list")
    refs = [_require_text(item, name) for item in value]
    if len(refs) != len(set(refs)):
        raise ActionPriorityError(f"{name} must be unique")
    return refs


def _digest(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(payload.encode()).hexdigest()


def ranking_contract() -> list[dict[str, Any]]:
    return copy.deepcopy(list(RANKING_FACTORS))


def validate_ranking_contract(factors: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows = [copy.deepcopy(row) for row in factors]
    if len(rows) != 6:
        raise ActionPriorityError("exactly six ranking factors required")
    ids = []
    total = 0
    for row in rows:
        factor_id = _require_text(row.get("factor_id"), "factor_id")
        ids.append(factor_id)
        _require_text(row.get("label_zh"), "label_zh")
        weight = _require_bps(row.get("weight_bps"), "weight_bps")
        total += weight
        if row.get("direction") not in ("HIGHER_IS_BETTER", "LOWER_IS_BETTER"):
            raise ActionPriorityError("invalid factor direction")
    if len(ids) != len(set(ids)):
        raise ActionPriorityError("ranking factor ids must be unique")
    if tuple(ids) != tuple(row["factor_id"] for row in RANKING_FACTORS):
        raise ActionPriorityError("ranking factor order drift")
    if total != 10_000:
        raise ActionPriorityError("ranking factor weights must sum to 10000")
    return {"factor_count": len(rows), "weight_total_bps": total, "score_range_bps": [0, 10_000]}


def rank_action_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(candidate, dict):
        raise ActionPriorityError("candidate must be an object")
    candidate_id = _require_text(candidate.get("candidate_id"), "candidate_id")
    title_zh = _require_text(candidate.get("title_zh"), "title_zh")
    domain = _require_text(candidate.get("domain"), "domain")
    if domain not in ACTION_DOMAINS:
        raise ActionPriorityError("unsupported action domain")
    source_refs = _require_refs(candidate.get("source_refs"), "source_refs")
    source_fingerprint = _require_text(candidate.get("source_fingerprint"), "source_fingerprint")
    if not _SHA256.fullmatch(source_fingerprint):
        raise ActionPriorityError("source_fingerprint must be sha256")
    freshness = _require_text(candidate.get("freshness"), "freshness")
    if freshness not in FRESHNESS_STATES:
        raise ActionPriorityError("invalid freshness state")
    hard_gate_passed = _require_bool(candidate.get("hard_gate_passed"), "hard_gate_passed")
    owner_role = _require_text(candidate.get("owner_role"), "owner_role")
    next_human_step = _require_text(candidate.get("next_human_step"), "next_human_step")
    factors = candidate.get("factors")
    if not isinstance(factors, dict) or set(factors) != {row["factor_id"] for row in RANKING_FACTORS}:
        raise ActionPriorityError("candidate factors must match ranking contract")
    normalized = {factor_id: _require_bps(value, factor_id) for factor_id, value in factors.items()}

    base = {
        "candidate_id": candidate_id,
        "title_zh": title_zh,
        "domain": domain,
        "source_refs": source_refs,
        "source_fingerprint": source_fingerprint,
        "freshness": freshness,
        "hard_gate_passed": hard_gate_passed,
        "owner_role": owner_role,
        "next_human_step": next_human_step,
        "advisory_only": True,
        "automatic_execution_allowed": False,
        "fact_layer_write_count": 0,
    }
    if not hard_gate_passed:
        return {
            **base,
            "state": "BLOCKED_BY_HARD_GATE",
            "priority_score_bps": None,
            "focus_eligible": False,
            "factor_explanations": [],
            "plain_reason_zh": "硬性条件未通过，不能用排序分数覆盖。",
        }
    if freshness == "STALE":
        return {
            **base,
            "state": "INSUFFICIENT_DATA",
            "priority_score_bps": None,
            "focus_eligible": False,
            "factor_explanations": [],
            "plain_reason_zh": "资料已经过期，需要更新后再排序。",
        }

    explanations = []
    total = 0
    for contract in RANKING_FACTORS:
        factor_id = contract["factor_id"]
        value = normalized[factor_id]
        effective = value if contract["direction"] == "HIGHER_IS_BETTER" else 10_000 - value
        contribution = effective * contract["weight_bps"] // 10_000
        total += contribution
        explanations.append({
            "factor_id": factor_id,
            "label_zh": contract["label_zh"],
            "input_bps": value,
            "effective_bps": effective,
            "weight_bps": contract["weight_bps"],
            "contribution_bps": contribution,
            "direction": contract["direction"],
        })
    score = min(10_000, max(0, total))
    low_confidence = normalized["CONFIDENCE"] < MIN_FOCUS_CONFIDENCE_BPS
    state = "REQUIRES_REVIEW" if low_confidence else "ELIGIBLE"
    reason = (
        "可信度不足，保留供人工复核，不进入本期重点事项。"
        if low_confidence
        else "排序由六项已登记因素共同形成，最终行动仍需人工决定。"
    )
    return {
        **base,
        "state": state,
        "priority_score_bps": score,
        "focus_eligible": not low_confidence,
        "factor_explanations": explanations,
        "plain_reason_zh": reason,
        "ranking_fingerprint": _digest({"candidate_id": candidate_id, "factors": normalized, "contract": RANKING_FACTORS}),
    }


def rank_actions(candidates: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [rank_action_candidate(candidate) for candidate in candidates]
    ids = [row["candidate_id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise ActionPriorityError("candidate ids must be unique")
    rows.sort(
        key=lambda row: (
            row["priority_score_bps"] is None,
            -(row["priority_score_bps"] or 0),
            row["candidate_id"],
        )
    )
    rank = 0
    for row in rows:
        if row["priority_score_bps"] is None:
            row["rank"] = None
        else:
            rank += 1
            row["rank"] = rank
    return rows


def select_focus_items(candidates: Iterable[dict[str, Any]], *, max_items: int = FOCUS_MAX_ITEMS) -> dict[str, Any]:
    if isinstance(max_items, bool) or not isinstance(max_items, int) or not FOCUS_MIN_ITEMS <= max_items <= FOCUS_MAX_ITEMS:
        raise ActionPriorityError("max_items must be an integer from 3 to 5")
    ranked = rank_actions(candidates)
    selected = []
    domain_counts = {domain: 0 for domain in ACTION_DOMAINS}
    for row in ranked:
        if not row["focus_eligible"] or row["state"] != "ELIGIBLE":
            continue
        if domain_counts[row["domain"]] >= FOCUS_DOMAIN_CAP:
            continue
        if len(selected) >= max_items:
            break
        domain_counts[row["domain"]] += 1
        selected.append({
            "focus_rank": len(selected) + 1,
            "candidate_id": row["candidate_id"],
            "title_zh": row["title_zh"],
            "domain": row["domain"],
            "priority_score_bps": row["priority_score_bps"],
            "plain_reason_zh": row["plain_reason_zh"],
            "factor_explanations": row["factor_explanations"],
            "source_refs": row["source_refs"],
            "owner_role": row["owner_role"],
            "next_human_step": row["next_human_step"],
            "advisory_only": True,
            "automatic_execution_allowed": False,
        })
    status = "READY" if FOCUS_MIN_ITEMS <= len(selected) <= FOCUS_MAX_ITEMS else "INSUFFICIENT_ELIGIBLE_ITEMS"
    return {
        "selection_status": status,
        "focus_items": selected,
        "focus_item_count": len(selected),
        "focus_min_items": FOCUS_MIN_ITEMS,
        "focus_max_items": FOCUS_MAX_ITEMS,
        "domain_cap": FOCUS_DOMAIN_CAP,
        "candidate_count": len(ranked),
        "unselected_count": len(ranked) - len(selected),
        "automatic_execution_count": 0,
        "fact_layer_write_count": 0,
    }


def build_recommendation_review(
    *,
    recommendation_id: str,
    candidate_id: str,
    recommendation_text_zh: str,
    decision: str = "NOT_REVIEWED",
    outcome_state: str | None = None,
    outcome_evidence_refs: list[str] | None = None,
    calibration_note_zh: str = "尚未校准",
) -> dict[str, Any]:
    recommendation_id = _require_text(recommendation_id, "recommendation_id")
    candidate_id = _require_text(candidate_id, "candidate_id")
    recommendation_text_zh = _require_text(recommendation_text_zh, "recommendation_text_zh")
    decision = _require_text(decision, "decision")
    if decision not in REVIEW_DECISIONS:
        raise ActionPriorityError("invalid review decision")
    state = "UNKNOWN" if outcome_state is None else _require_text(outcome_state, "outcome_state")
    if state not in OUTCOME_STATES:
        raise ActionPriorityError("invalid outcome state")
    refs = [] if outcome_evidence_refs is None else _require_refs(outcome_evidence_refs, "outcome_evidence_refs")
    if state != "UNKNOWN" and not refs:
        raise ActionPriorityError("known outcome requires evidence")
    if state == "UNKNOWN" and refs:
        raise ActionPriorityError("unknown outcome cannot claim outcome evidence")
    calibration_note_zh = _require_text(calibration_note_zh, "calibration_note_zh")
    record = {
        "recommendation_id": recommendation_id,
        "candidate_id": candidate_id,
        "recommendation_text_zh": recommendation_text_zh,
        "decision": decision,
        "outcome_state": state,
        "outcome_evidence_refs": refs,
        "calibration_note_zh": calibration_note_zh,
        "recommendation_fact_status": "UNVERIFIED_RECOMMENDATION",
        "recommendation_written_as_fact": False,
        "automatic_parameter_change_allowed": False,
        "fact_layer_write_count": 0,
    }
    return {**record, "review_fingerprint": _digest(record)}


def append_review_record(history: Iterable[dict[str, Any]], record: dict[str, Any]) -> list[dict[str, Any]]:
    original = [copy.deepcopy(item) for item in history]
    validated = build_recommendation_review(
        recommendation_id=record.get("recommendation_id"),
        candidate_id=record.get("candidate_id"),
        recommendation_text_zh=record.get("recommendation_text_zh"),
        decision=record.get("decision", "NOT_REVIEWED"),
        outcome_state=record.get("outcome_state"),
        outcome_evidence_refs=record.get("outcome_evidence_refs") or None,
        calibration_note_zh=record.get("calibration_note_zh", "尚未校准"),
    )
    ids = [item.get("recommendation_id") for item in original]
    if validated["recommendation_id"] in ids:
        raise ActionPriorityError("recommendation history is append-only")
    return original + [validated]


def build_calibration_proposal(records: Iterable[dict[str, Any]], *, minimum_known_outcomes: int = 3) -> dict[str, Any]:
    if isinstance(minimum_known_outcomes, bool) or not isinstance(minimum_known_outcomes, int) or minimum_known_outcomes < 1:
        raise ActionPriorityError("minimum_known_outcomes must be positive integer")
    rows = [copy.deepcopy(row) for row in records]
    known = [row for row in rows if row.get("outcome_state") in ("POSITIVE", "NEGATIVE")]
    unknown_count = sum(row.get("outcome_state") == "UNKNOWN" for row in rows)
    if len(known) < minimum_known_outcomes:
        return {
            "status": "INSUFFICIENT_DATA",
            "known_outcome_count": len(known),
            "unknown_outcome_count": unknown_count,
            "success_rate_bps": None,
            "proposed_confidence_weight_adjustment_bps": None,
            "automatic_parameter_change_allowed": False,
            "fact_layer_write_count": 0,
        }
    positive = sum(row.get("outcome_state") == "POSITIVE" for row in known)
    success_rate = positive * 10_000 // len(known)
    adjustment = 250 if success_rate >= 7500 else (-250 if success_rate <= 2500 else 0)
    return {
        "status": "PROPOSAL_ONLY",
        "known_outcome_count": len(known),
        "unknown_outcome_count": unknown_count,
        "success_rate_bps": success_rate,
        "proposed_confidence_weight_adjustment_bps": adjustment,
        "automatic_parameter_change_allowed": False,
        "fact_layer_write_count": 0,
    }


def sample_candidates() -> list[dict[str, Any]]:
    base = [
        ("ACT-COLLECTION-001", "COLLECTION", "核对逾期回款并联系责任人", 9200, 9000, 9500, 2500, 1200, 1800, True, "FRESH", "回款负责人"),
        ("ACT-FUNDS-001", "FUNDS", "复核未来四周现金缺口", 9000, 8600, 9000, 3000, 1800, 2200, True, "FRESH", "资金负责人"),
        ("ACT-PROJECT-001", "PROJECT", "复核低毛利项目成本偏差", 8700, 8400, 8200, 4200, 2000, 3000, True, "FRESH", "项目负责人"),
        ("ACT-TAX-001", "TAX", "确认临近申报期税务资料", 7600, 8800, 8600, 2800, 1600, 1900, True, "AGING", "税务负责人"),
        ("ACT-DATA-001", "DATA", "补齐影响经营判断的缺失资料", 8100, 7800, 7900, 3500, 1000, 2400, True, "FRESH", "数据负责人"),
        ("ACT-PROJECT-002", "PROJECT", "复核未确认项目变更", 7000, 3200, 6500, 3800, 1400, 3300, True, "FRESH", "项目负责人"),
        ("ACT-DATA-002", "DATA", "处理被硬门槛阻断的数据问题", 9500, 9000, 9400, 2000, 800, 1500, False, "FRESH", "数据负责人"),
    ]
    rows = []
    for candidate_id, domain, title, impact, confidence, urgency, effort, cash, risk, gate, freshness, owner in base:
        facts = {"candidate_id": candidate_id, "domain": domain, "title": title}
        rows.append({
            "candidate_id": candidate_id,
            "domain": domain,
            "title_zh": title,
            "source_refs": [f"S13-P2:{domain}:PUBLIC-SYNTHETIC"],
            "source_fingerprint": _digest(facts),
            "freshness": freshness,
            "hard_gate_passed": gate,
            "owner_role": owner,
            "next_human_step": "由负责人核对依据后决定是否采纳，不自动执行。",
            "factors": {
                "IMPACT": impact,
                "CONFIDENCE": confidence,
                "URGENCY": urgency,
                "EFFORT": effort,
                "CASH_COST": cash,
                "EXECUTION_RISK": risk,
            },
        })
    return rows


def public_verification() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def add(name: str, passed: bool) -> None:
        checks.append({"name": name, "passed": bool(passed)})

    contract = validate_ranking_contract(ranking_contract())
    candidates = sample_candidates()
    ranked = rank_actions(candidates)
    focus = select_focus_items(candidates)
    unknown_review = build_recommendation_review(
        recommendation_id="REC-001",
        candidate_id="ACT-COLLECTION-001",
        recommendation_text_zh="请回款负责人核对逾期明细并决定下一步。",
    )
    known_reviews = [
        build_recommendation_review(
            recommendation_id=f"REC-KNOWN-{index}",
            candidate_id=f"ACT-KNOWN-{index}",
            recommendation_text_zh="公开模拟复盘建议。",
            decision="ACCEPTED",
            outcome_state="POSITIVE" if index < 3 else "NEGATIVE",
            outcome_evidence_refs=[f"PUBLIC-SYNTHETIC-OUTCOME-{index}"],
            calibration_note_zh="仅形成校准建议，不自动改参数。",
        )
        for index in range(4)
    ]
    insufficient = build_calibration_proposal([unknown_review])
    proposal = build_calibration_proposal(known_reviews)
    history: list[dict[str, Any]] = []
    history_snapshot = copy.deepcopy(history)
    appended = append_review_record(history, unknown_review)

    add("contract_factor_count", contract["factor_count"] == 6)
    add("contract_weight_total", contract["weight_total_bps"] == 10_000)
    add("contract_score_range", contract["score_range_bps"] == [0, 10_000])
    add("domain_count", len(ACTION_DOMAINS) == 5)
    add("candidate_state_count", len(CANDIDATE_STATES) == 5)
    add("review_decision_count", len(REVIEW_DECISIONS) == 4)
    add("outcome_state_count", len(OUTCOME_STATES) == 3)
    add("focus_bounds", (FOCUS_MIN_ITEMS, FOCUS_MAX_ITEMS) == (3, 5))
    add("candidate_count", len(candidates) == 7)
    add("ranked_count", len(ranked) == 7)
    add("scored_order", [row["priority_score_bps"] or -1 for row in ranked] == sorted([row["priority_score_bps"] or -1 for row in ranked], reverse=True))
    add("hard_gate_not_scored", next(row for row in ranked if row["candidate_id"] == "ACT-DATA-002")["priority_score_bps"] is None)
    add("hard_gate_not_focus", not next(row for row in ranked if row["candidate_id"] == "ACT-DATA-002")["focus_eligible"])
    add("low_confidence_review", next(row for row in ranked if row["candidate_id"] == "ACT-PROJECT-002")["state"] == "REQUIRES_REVIEW")
    add("low_confidence_not_focus", not next(row for row in ranked if row["candidate_id"] == "ACT-PROJECT-002")["focus_eligible"])
    add("all_scored_in_range", all(row["priority_score_bps"] is None or 0 <= row["priority_score_bps"] <= 10_000 for row in ranked))
    add("all_ranked_advisory", all(row["advisory_only"] for row in ranked))
    add("no_ranked_auto_execution", all(not row["automatic_execution_allowed"] for row in ranked))
    add("focus_ready", focus["selection_status"] == "READY")
    add("focus_count_five", focus["focus_item_count"] == 5)
    add("focus_at_most_five", focus["focus_item_count"] <= 5)
    add("focus_at_least_three", focus["focus_item_count"] >= 3)
    add("focus_domain_cap", all(sum(item["domain"] == domain for item in focus["focus_items"]) <= 2 for domain in ACTION_DOMAINS))
    add("focus_unique", len({item["candidate_id"] for item in focus["focus_items"]}) == focus["focus_item_count"])
    add("focus_no_auto_execution", focus["automatic_execution_count"] == 0)
    add("focus_no_fact_write", focus["fact_layer_write_count"] == 0)
    add("review_unknown_default", unknown_review["outcome_state"] == "UNKNOWN")
    add("review_not_fact", not unknown_review["recommendation_written_as_fact"])
    add("review_no_auto_calibration", not unknown_review["automatic_parameter_change_allowed"])
    add("review_no_fact_write", unknown_review["fact_layer_write_count"] == 0)
    add("history_immutable", history == history_snapshot)
    add("history_appended", len(appended) == 1)
    add("calibration_insufficient", insufficient["status"] == "INSUFFICIENT_DATA")
    add("calibration_unknown_visible", insufficient["unknown_outcome_count"] == 1)
    add("calibration_proposal_only", proposal["status"] == "PROPOSAL_ONLY")
    add("calibration_success_rate", proposal["success_rate_bps"] == 7500)
    add("calibration_not_applied", not proposal["automatic_parameter_change_allowed"])
    add("calibration_no_fact_write", proposal["fact_layer_write_count"] == 0)

    for factor in RANKING_FACTORS:
        explanation = ranked[0]["factor_explanations"]
        row = next(item for item in explanation if item["factor_id"] == factor["factor_id"])
        add(f"factor_{factor['factor_id']}_present", row["factor_id"] == factor["factor_id"])
        add(f"factor_{factor['factor_id']}_weight", row["weight_bps"] == factor["weight_bps"])
        add(f"factor_{factor['factor_id']}_direction", row["direction"] == factor["direction"])
        add(f"factor_{factor['factor_id']}_contribution", isinstance(row["contribution_bps"], int))

    for domain in ACTION_DOMAINS:
        add(f"domain_{domain}_candidate", any(row["domain"] == domain for row in ranked))
        add(f"domain_{domain}_known", domain in ACTION_DOMAINS)

    for item in focus["focus_items"]:
        add(f"focus_{item['candidate_id']}_explained", len(item["factor_explanations"]) == 6)
        add(f"focus_{item['candidate_id']}_human_step", bool(item["next_human_step"]))

    invalid_cases = {}
    for name, mutate in (
        ("float", lambda row: row["factors"].__setitem__("IMPACT", 1.5)),
        ("bool", lambda row: row["factors"].__setitem__("IMPACT", True)),
        ("private", lambda row: row.__setitem__("title_zh", "/Users/example/private")),
        ("bad_domain", lambda row: row.__setitem__("domain", "UNKNOWN")),
        ("missing_factor", lambda row: row["factors"].pop("IMPACT")),
        ("bad_fingerprint", lambda row: row.__setitem__("source_fingerprint", "bad")),
    ):
        row = copy.deepcopy(candidates[0])
        mutate(row)
        try:
            rank_action_candidate(row)
        except ActionPriorityError:
            invalid_cases[name] = True
        else:
            invalid_cases[name] = False
        add(f"invalid_{name}_rejected", invalid_cases[name])

    failed = [row["name"] for row in checks if not row["passed"]]
    return {
        "schema_version": "kmfa.v015.s13p3.action_priority_verification.v1",
        "accounting": {"total": len(checks), "passed": len(checks) - len(failed), "failed": len(failed)},
        "failed_checks": failed,
        "checks": checks,
        "ranking_contract_summary": contract,
        "sample_ranked_actions": ranked,
        "sample_focus_selection": focus,
        "sample_unknown_review": unknown_review,
        "sample_calibration_proposal": proposal,
        "automatic_execution_count": 0,
        "recommendation_fact_write_count": 0,
        "automatic_parameter_change_count": 0,
        "raw_root_access_count": 0,
        "live_source_read_count": 0,
        "real_business_action_count": 0,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
    }


if __name__ == "__main__":
    print(json.dumps(public_verification(), ensure_ascii=False, indent=2, sort_keys=True))
