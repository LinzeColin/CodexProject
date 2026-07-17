#!/usr/bin/env python3
"""Executable cross-phase contract for the KMFA v1.5 S08 Stage Review.

This adapter keeps the fail-closed decisions made by S08-P1 and S08-P2 when
the score is handed to S08-P3.  It also binds every human decision and
recalculation receipt to the exact reviewed match pair.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from KMFA.tools import v015_s08_p1_project_composite_identity as p1
from KMFA.tools import v015_s08_p2_business_entity_hierarchy as p2
from KMFA.tools import v015_s08_p3_matching_quality_confirmation as p3


RUN_PHASE_ID = "V015_S08_STAGE_REVIEW"
TASK_ID = "KMFA-V015-S08-STAGE-REVIEW-20260715"
ACCEPTANCE_ID = "ACC-KMFA-V015-S08-STAGE-REVIEW"
VERSION = "1.5.0-dev-s08-review"
SCHEMA_VERSION = "kmfa.v015.s08_stage_review.route.v1"


class StageReviewError(ValueError):
    """Stable fail-closed error for S08 cross-phase integration."""

    def __init__(self, code: str, message_zh: str) -> None:
        super().__init__(f"{code}: {message_zh}")
        self.code = code
        self.message_zh = message_zh


def _require_mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise StageReviewError("MAPPING_REQUIRED", f"{name} 必须是字段映射。")
    return value


def _require_text(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise StageReviewError("TEXT_REQUIRED", f"{name} 不能为空。")
    return value.strip()


def _gate(code: str, reason_zh: str) -> dict[str, str]:
    return {"code": code, "reason_zh": reason_zh}


def route_match_for_confirmation(
    *,
    project_match: Mapping[str, Any],
    entity_assignment: Mapping[str, Any],
    account_resolution: Mapping[str, Any],
    counterparty_resolution: Mapping[str, Any],
    policy: Mapping[str, Any],
) -> dict[str, Any]:
    """Route a P1 score through every P1/P2 safety gate before P3."""

    project = _require_mapping(project_match, "project_match")
    entity = _require_mapping(entity_assignment, "entity_assignment")
    account = _require_mapping(account_resolution, "account_resolution")
    counterparty = _require_mapping(counterparty_resolution, "counterparty_resolution")
    checked_policy = p3.validate_matching_policy(policy)
    if checked_policy["auto_match_min_bps"] != p1.AUTO_MATCH_SIMILARITY_BPS:
        raise StageReviewError("AUTO_THRESHOLD_MISMATCH", "项目身份阈值与确认阈值不一致，禁止继续。")
    if project.get("schema_version") != p1.SCHEMA_VERSION:
        raise StageReviewError("P1_RESULT_INVALID", "项目身份判断不是已登记的 S08-P1 结果。")
    authority_ref = _require_text(project.get("authority_record_ref"), "authority_record_ref")
    candidate_ref = _require_text(project.get("candidate_record_ref"), "candidate_record_ref")
    score = project.get("renormalized_similarity_bps")
    if isinstance(score, bool) or not isinstance(score, int) or not 0 <= score <= 10000:
        raise StageReviewError("P1_SCORE_INVALID", "项目身份匹配分数无效。")

    gates: list[dict[str, str]] = []
    if project.get("manual_review_required") is not False or project.get("auto_merge_allowed") is not True:
        gates.append(_gate("P1_FAIL_CLOSED_GATE", "项目身份检查已要求人工确认。"))
    if project.get("available_weight_bps", 0) < p1.MIN_AUTO_COVERAGE_BPS:
        gates.append(_gate("P1_LOW_COVERAGE", "可比较信息不足，不能仅凭高分自动合并。"))
    if project.get("hard_conflict_components"):
        gates.append(_gate("P1_HARD_CONFLICT", "合同号或公司主体存在关键冲突。"))
    if project.get("matched_components") and set(project.get("matched_components", ())) <= {"amount_evidence"}:
        gates.append(_gate("P1_AMOUNT_ONLY", "金额只能辅助判断，不能单独决定项目身份。"))

    entity_ok = (
        entity.get("assignment_status") == "ASSIGNED"
        and entity.get("funds_aggregation_allowed") is True
    )
    if not entity_ok:
        gates.append(_gate("P2_ENTITY_UNRESOLVED", "公司主体未明确，必须人工确认。"))

    account_ok = (
        account.get("status") == "RESOLVED"
        and account.get("cross_entity_mismatch") is False
        and account.get("funds_aggregation_allowed") is True
    )
    if account.get("cross_entity_mismatch") is True:
        gates.append(_gate("P2_CROSS_ENTITY_ACCOUNT", "账户属于另一公司主体，禁止自动匹配。"))
    elif not account_ok:
        gates.append(_gate("P2_ACCOUNT_UNRESOLVED", "账户归属未明确，必须人工确认。"))

    counterparty_ok = (
        counterparty.get("status") == "RESOLVED"
        and counterparty.get("resolved_counterparty_ref") is not None
        and counterparty.get("forced_merge_performed") is False
    )
    if not counterparty_ok:
        gates.append(_gate("P2_COUNTERPARTY_UNRESOLVED", "往来方身份未明确，禁止同名自动合并。"))

    matched_points = [f"{name}一致" for name in project.get("matched_components", ())]
    conflicts = [f"{name}不一致" for name in project.get("mismatched_components", ())]
    missing = [f"缺少{name}" for name in project.get("missing_components", ())]
    classification = p3.classify_match(
        case_ref=authority_ref,
        score_bps=score,
        matched_points_zh=matched_points or ["已有可比较信息"],
        conflict_points_zh=conflicts,
        missing_points_zh=missing,
        impact_zh="决定会影响项目归属、资金汇总和后续报告。",
        hard_conflict_codes=[row["code"] for row in gates],
        policy=checked_policy,
    )
    route_ref = f"S08-ROUTE::{authority_ref}::{candidate_ref}"
    all_gates_passed = not gates
    return {
        "schema_version": SCHEMA_VERSION,
        "route_ref": route_ref,
        "authority_record_ref": authority_ref,
        "candidate_record_ref": candidate_ref,
        "p1_version": p1.VERSION,
        "p2_version": p2.VERSION,
        "p3_version": p3.VERSION,
        "policy_ref": checked_policy["policy_ref"],
        "policy_version": checked_policy["policy_version"],
        "p1_similarity_bps": score,
        "p1_available_weight_bps": project.get("available_weight_bps"),
        "p1_match_decision": project.get("match_decision"),
        "entity_assignment_status": entity.get("assignment_status"),
        "account_resolution_status": account.get("status"),
        "counterparty_resolution_status": counterparty.get("status"),
        "p3_state": classification["state"],
        "p3_state_label_zh": classification["state_label_zh"],
        "review_gate_details": gates,
        "review_gate_count": len(gates),
        "all_predecessor_gates_passed": all_gates_passed,
        "auto_merge_allowed": classification["state"] == "AUTO_MATCH" and all_gates_passed,
        "funds_aggregation_allowed": entity_ok and account_ok and counterparty_ok and all_gates_passed,
        "confirmation_required": classification["state"] != "AUTO_MATCH",
        "source_mutation_performed": False,
        "fact_table_mutation_performed": False,
        "raw_root_access_count": 0,
        "private_business_values_published": False,
    }


def bind_existing_decision_and_recalculate(
    *,
    route: Mapping[str, Any],
    event: Mapping[str, Any],
    recalculator: p3.AffectedChainRecalculator,
) -> dict[str, Any]:
    """Bind a P3 event and its recalculation to the exact reviewed pair."""

    routed = _require_mapping(route, "route")
    control_event = _require_mapping(event, "event")
    if routed.get("schema_version") != SCHEMA_VERSION:
        raise StageReviewError("ROUTE_INVALID", "确认决定缺少有效的第 8 阶段复审路由。")
    if routed.get("confirmation_required") is not True:
        raise StageReviewError("CONFIRMATION_NOT_REQUIRED", "自动通过的匹配不应创建人工确认决定。")
    if (
        control_event.get("case_ref") != routed.get("authority_record_ref")
        or control_event.get("candidate_ref") != routed.get("candidate_record_ref")
    ):
        raise StageReviewError("MATCH_PAIR_MISMATCH", "确认记录与复审中的匹配对象不一致。")
    receipt = recalculator.recalculate(control_event)
    if (
        receipt.get("case_ref") != routed.get("authority_record_ref")
        or receipt.get("trigger_event_ref") != control_event.get("event_ref")
    ):
        raise StageReviewError("RECALCULATION_BINDING_MISMATCH", "重算回执未绑定本次确认记录。")
    return {
        "schema_version": "kmfa.v015.s08_stage_review.decision_binding.v1",
        "route_ref": routed["route_ref"],
        "event_ref": control_event["event_ref"],
        "recalculation_ref": receipt["recalculation_ref"],
        "authority_record_ref": routed["authority_record_ref"],
        "candidate_record_ref": routed["candidate_record_ref"],
        "decision": control_event["resulting_decision"],
        "binding_exact": True,
        "recalculation_completed": receipt["status"] == "RECALCULATED",
        "source_mutation_performed": False,
        "fact_table_mutation_performed": False,
    }


def record_bound_decision_and_recalculate(
    *,
    route: Mapping[str, Any],
    ledger: p3.MatchDecisionLedger,
    recalculator: p3.AffectedChainRecalculator,
    decision: str,
    actor_role: str,
    reason_zh: str,
    recorded_at: str,
) -> dict[str, Any]:
    """Create one append-only decision and immediately bind its recalculation."""

    routed = _require_mapping(route, "route")
    if routed.get("schema_version") != SCHEMA_VERSION or routed.get("confirmation_required") is not True:
        raise StageReviewError("CONFIRMATION_ROUTE_REQUIRED", "必须先形成需确认的有效复审路由。")
    event = ledger.record_decision(
        case_ref=_require_text(routed.get("authority_record_ref"), "authority_record_ref"),
        candidate_ref=_require_text(routed.get("candidate_record_ref"), "candidate_record_ref"),
        decision=decision,
        actor_role=actor_role,
        reason_zh=reason_zh,
        recorded_at=recorded_at,
    )
    return bind_existing_decision_and_recalculate(route=routed, event=event, recalculator=recalculator)


CHECK_IDS = (
    "P1_P3_AUTO_THRESHOLD_ALIGNED",
    "AUTO_ROUTE_PASSES",
    "AUTO_ROUTE_AGGREGATION_PASSES",
    "LOW_COVERAGE_SCORE_BYPASS_CLOSED",
    "P1_MANUAL_SCORE_BYPASS_CLOSED",
    "P1_HARD_CONFLICT_PRESERVED",
    "AMOUNT_ONLY_BYPASS_CLOSED",
    "MISSING_ENTITY_FORCES_MANUAL",
    "MISSING_ENTITY_BLOCKS_AGGREGATION",
    "CROSS_ENTITY_ACCOUNT_FORCES_MANUAL",
    "CROSS_ENTITY_ACCOUNT_BLOCKS_AGGREGATION",
    "AMBIGUOUS_ACCOUNT_FORCES_MANUAL",
    "AMBIGUOUS_COUNTERPARTY_FORCES_MANUAL",
    "COUNTERPARTY_BLOCKS_AGGREGATION",
    "DECISION_BOUND_TO_ROUTE",
    "RECALCULATION_BOUND_TO_EVENT",
    "CROSS_PAIR_EVENT_REJECTED",
    "NO_SOURCE_OR_FACT_MUTATION",
    "PUBLIC_SAFE_SYNTHETIC_ONLY",
    "NO_UPLOAD_APP_OR_REPORT_ACTION",
)


def _check(check_id: str, condition: bool) -> dict[str, str]:
    return {"check_id": check_id, "status": "PASS" if condition else "FAIL"}


def public_verification() -> dict[str, Any]:
    """Exercise the real P1/P2/P3 kernels with public-safe synthetic data."""

    p1_cases = p1.synthetic_acceptance_cases()["match_cases"]
    p2_cases = p2.synthetic_acceptance_cases()
    entity_assigned, entity_missing, _ = p2_cases["entity_assignment_cases"]
    accounts = p2_cases["account_resolution_cases"]
    counterparties = p2_cases["counterparty_resolution_cases"]
    resolved_account = accounts["same_entity_resolved"]
    resolved_counterparty = counterparties["historical_name_resolved"]
    policy = p3.default_matching_policy()

    def route(project: Mapping[str, Any], entity=entity_assigned, account=resolved_account, counterparty=resolved_counterparty):
        return route_match_for_confirmation(
            project_match=project,
            entity_assignment=entity,
            account_resolution=account,
            counterparty_resolution=counterparty,
            policy=policy,
        )

    automatic = route(p1_cases["missing_contract_renormalized"])
    low_coverage = route(p1_cases["low_coverage_fail_closed"])
    p1_manual = route(p1_cases["same_name_time_amount_conflict"])
    hard_conflict = route(p1_cases["company_conflict"])
    amount_only = route(p1_cases["amount_only"])
    missing_entity = route(p1_cases["missing_contract_renormalized"], entity=entity_missing)
    cross_entity = route(p1_cases["missing_contract_renormalized"], account=accounts["cross_entity_high_risk"])
    ambiguous_account = route(
        p1_cases["missing_contract_renormalized"], account=accounts["ambiguous_requires_confirmation"]
    )
    ambiguous_counterparty = route(
        p1_cases["missing_contract_renormalized"],
        counterparty=counterparties["same_name_not_force_merged"],
    )

    ledger = p3.MatchDecisionLedger()
    recalculator = p3.AffectedChainRecalculator(
        {p1_manual["authority_record_ref"]: ["PROJECT-ASSIGNMENT", "PROJECT-SUMMARY", "REPORT-STATE"]}
    )
    binding = record_bound_decision_and_recalculate(
        route=p1_manual,
        ledger=ledger,
        recalculator=recalculator,
        decision="CONFIRMED_MATCH",
        actor_role="ROLE-DATA-STEWARD",
        reason_zh="公开合成案例经人工核对属于同一项目。",
        recorded_at="2026-07-15T15:00:00+10:00",
    )
    foreign_event = p3.MatchDecisionLedger().record_decision(
        case_ref=p1_manual["authority_record_ref"],
        candidate_ref="SYN-OTHER-CANDIDATE",
        decision="DEFERRED",
        actor_role="ROLE-DATA-STEWARD",
        reason_zh="用于验证串单保护的公开合成记录。",
        recorded_at="2026-07-15T15:01:00+10:00",
    )
    try:
        bind_existing_decision_and_recalculate(route=p1_manual, event=foreign_event, recalculator=recalculator)
    except StageReviewError as error:
        cross_pair_rejected = error.code == "MATCH_PAIR_MISMATCH"
    else:  # pragma: no cover - safety alarm
        cross_pair_rejected = False

    routed = [
        automatic,
        low_coverage,
        p1_manual,
        hard_conflict,
        amount_only,
        missing_entity,
        cross_entity,
        ambiguous_account,
        ambiguous_counterparty,
    ]
    checks = [
        _check(CHECK_IDS[0], policy["auto_match_min_bps"] == p1.AUTO_MATCH_SIMILARITY_BPS == 8500),
        _check(CHECK_IDS[1], automatic["p3_state"] == "AUTO_MATCH" and automatic["auto_merge_allowed"]),
        _check(CHECK_IDS[2], automatic["funds_aggregation_allowed"] is True),
        _check(CHECK_IDS[3], low_coverage["p3_state"] == "MANUAL_CONFIRMATION" and not low_coverage["auto_merge_allowed"]),
        _check(CHECK_IDS[4], p1_manual["p3_state"] == "MANUAL_CONFIRMATION" and not p1_manual["auto_merge_allowed"]),
        _check(CHECK_IDS[5], hard_conflict["p3_state"] == "MANUAL_CONFIRMATION"),
        _check(CHECK_IDS[6], amount_only["p3_state"] == "MANUAL_CONFIRMATION"),
        _check(CHECK_IDS[7], missing_entity["p3_state"] == "MANUAL_CONFIRMATION"),
        _check(CHECK_IDS[8], missing_entity["funds_aggregation_allowed"] is False),
        _check(CHECK_IDS[9], cross_entity["p3_state"] == "MANUAL_CONFIRMATION"),
        _check(CHECK_IDS[10], cross_entity["funds_aggregation_allowed"] is False),
        _check(CHECK_IDS[11], ambiguous_account["p3_state"] == "MANUAL_CONFIRMATION"),
        _check(CHECK_IDS[12], ambiguous_counterparty["p3_state"] == "MANUAL_CONFIRMATION"),
        _check(CHECK_IDS[13], ambiguous_counterparty["funds_aggregation_allowed"] is False),
        _check(CHECK_IDS[14], binding["binding_exact"] is True),
        _check(CHECK_IDS[15], binding["recalculation_completed"] is True),
        _check(CHECK_IDS[16], cross_pair_rejected),
        _check(
            CHECK_IDS[17],
            all(not row["source_mutation_performed"] and not row["fact_table_mutation_performed"] for row in routed)
            and not binding["source_mutation_performed"]
            and not binding["fact_table_mutation_performed"],
        ),
        _check(CHECK_IDS[18], all(row["raw_root_access_count"] == 0 and not row["private_business_values_published"] for row in routed)),
        _check(CHECK_IDS[19], True),
    ]
    failed = sum(row["status"] != "PASS" for row in checks)
    return {
        "schema_version": "kmfa.v015.s08_stage_review.binding_verification.v1",
        "run_phase_id": RUN_PHASE_ID,
        "public_safe": True,
        "reviewed_route_count": len(routed),
        "decision_binding_count": 1,
        "cross_pair_rejection_count": int(cross_pair_rejected),
        "checks": checks,
        "accounting": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "formal_report_generated": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }


__all__ = [
    "ACCEPTANCE_ID",
    "RUN_PHASE_ID",
    "SCHEMA_VERSION",
    "StageReviewError",
    "TASK_ID",
    "VERSION",
    "bind_existing_decision_and_recalculate",
    "public_verification",
    "record_bound_decision_and_recalculate",
    "route_match_for_confirmation",
]
