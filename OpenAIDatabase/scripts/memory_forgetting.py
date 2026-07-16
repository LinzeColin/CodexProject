#!/usr/bin/env python3
"""Fail-closed active retrieval, forgetting and abstention contracts."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
from typing import Any, Mapping, Sequence

from memory_lifecycle import parse_rfc3339


TASK_ID = "TSK.OpenAIDatabase.PAM1.0011"
ACCEPTANCE_ID = "ACC.OpenAIDatabase.PAM1.0011"
POLICY_SCHEMA_VERSION = "openai_database.memory_forgetting_policy.v1"
NEGATIVE_KIND = "negative_trigger"
NEGATIVE_AUTHORITY_SOURCES = ("explicit_user", "repository_evidence")
CURRENT_ANSWER_STATUSES = ("active",)
FAMA_MIN = Fraction(95, 100)
ABSTENTION_MIN = Fraction(90, 100)


class ForgettingError(ValueError):
    """Stable forgetting failure code without record content."""


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ForgettingError(f"{label}_must_be_object")
    return value


def _no_duplicate_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key, value in pairs:
        if key in output:
            raise ForgettingError("forgetting_policy_duplicate_json_key")
        output[key] = value
    return output


def load_policy(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_no_duplicate_object)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ForgettingError("forgetting_policy_invalid") from exc
    policy = dict(_mapping(value, "forgetting_policy"))
    validate_policy(policy)
    return policy


def validate_policy(policy: Mapping[str, Any]) -> None:
    expected = {
        "schema_version",
        "task_id",
        "acceptance_id",
        "current_answer",
        "historical_query",
        "abstention",
        "negative_memory",
        "metrics",
        "privacy",
        "canonical_business_record_rewrite_in_task",
    }
    if set(policy) != expected:
        raise ForgettingError("forgetting_policy_fields_invalid")
    if (
        policy["schema_version"] != POLICY_SCHEMA_VERSION
        or policy["task_id"] != TASK_ID
        or policy["acceptance_id"] != ACCEPTANCE_ID
    ):
        raise ForgettingError("forgetting_policy_identity_drift")

    current = _mapping(policy["current_answer"], "forgetting_current_answer")
    if current != {
        "eligible_statuses": list(CURRENT_ANSWER_STATUSES),
        "inactive_default": "exclude",
        "include_inactive_mode": "audit_only",
        "validity": "effective_at_execution_time",
        "critical_stale_use_max": 0,
    }:
        raise ForgettingError("forgetting_current_answer_policy_drift")

    historical = _mapping(policy["historical_query"], "forgetting_historical_query")
    if historical != {
        "explicit_as_of_required": True,
        "current_assertion_allowed": False,
        "preserve_recorded_history": True,
    }:
        raise ForgettingError("forgetting_historical_policy_drift")

    abstention = _mapping(policy["abstention"], "forgetting_abstention")
    if (
        abstention.get("knowledge_state") != "UNKNOWN"
        or abstention.get("action") != "abstain"
        or abstention.get("missing_conditions_required") is not True
        or abstention.get("reason_priority")
        != [
            "unresolved_conflict",
            "retired_or_expired",
            "candidate_or_unverified",
            "insufficient_evidence",
        ]
        or abstention.get("precision_min") != 0.9
        or abstention.get("recall_min") != 0.9
    ):
        raise ForgettingError("forgetting_abstention_policy_drift")

    negative = _mapping(policy["negative_memory"], "forgetting_negative_memory")
    if negative != {
        "kind": NEGATIVE_KIND,
        "authority_sources": list(NEGATIVE_AUTHORITY_SOURCES),
        "verification_state": "verified",
        "negative_triggers_min": 1,
        "valid_time_required": True,
        "infer_from_absence": False,
        "positive_assertion_allowed": False,
    }:
        raise ForgettingError("forgetting_negative_memory_policy_drift")

    metrics = _mapping(policy["metrics"], "forgetting_metrics")
    if metrics != {
        "fama_formula": "max(0,MPA-lambda*(1-FAA))",
        "lambda_formula": "N_forget/(N_presence+N_forget)",
        "fama_min": 0.95,
    }:
        raise ForgettingError("forgetting_metric_policy_drift")

    privacy = _mapping(policy["privacy"], "forgetting_privacy")
    if privacy != {
        "retirement_semantics": "retrieval_exclusion_not_history_deletion",
        "public_git_history_is_erasure": False,
        "history_rewrite_in_task": False,
    }:
        raise ForgettingError("forgetting_privacy_policy_drift")
    if policy["canonical_business_record_rewrite_in_task"] is not False:
        raise ForgettingError("forgetting_canonical_rewrite_policy_drift")


def _string_ids(value: Any, label: str) -> tuple[str, ...]:
    if (
        not isinstance(value, list)
        or any(not isinstance(item, str) or not item for item in value)
        or len(value) != len(set(value))
    ):
        raise ForgettingError(f"{label}_invalid")
    return tuple(value)


def validate_negative_boundary_payload(*, kind: Any, source_type: Any, negative_triggers: Any) -> None:
    if kind != NEGATIVE_KIND:
        return
    if source_type not in NEGATIVE_AUTHORITY_SOURCES:
        raise ForgettingError("negative_memory_authority_invalid")
    if len(_string_ids(negative_triggers, "negative_memory_triggers")) < 1:
        raise ForgettingError("negative_memory_triggers_required")


def validate_negative_memory_record(record: Mapping[str, Any]) -> None:
    if record.get("kind") != NEGATIVE_KIND:
        return
    source = _mapping(record.get("source"), "negative_memory_source")
    verification = _mapping(record.get("verification"), "negative_memory_verification")
    valid_time = _mapping(record.get("valid_time"), "negative_memory_valid_time")
    validate_negative_boundary_payload(
        kind=record.get("kind"),
        source_type=source.get("type"),
        negative_triggers=record.get("negative_triggers"),
    )
    if verification.get("state") != "verified":
        raise ForgettingError("negative_memory_not_verified")
    start = parse_rfc3339(valid_time.get("from"), "negative_memory_valid_from")
    end_raw = valid_time.get("to")
    if end_raw is not None and parse_rfc3339(end_raw, "negative_memory_valid_to") <= start:
        raise ForgettingError("negative_memory_valid_interval_invalid")


def _effective_at(record: Mapping[str, Any], at: datetime) -> bool:
    valid_time = _mapping(record.get("valid_time"), "forgetting_valid_time")
    start = parse_rfc3339(valid_time.get("from"), "forgetting_valid_from")
    end_raw = valid_time.get("to")
    end = None if end_raw is None else parse_rfc3339(end_raw, "forgetting_valid_to")
    return start <= at and (end is None or at < end)


def validate_forgetting_dataset(records: Sequence[Mapping[str, Any]]) -> None:
    for record in records:
        validate_negative_memory_record(record)


def assess_forgetting_dataset(
    records: Sequence[Mapping[str, Any]],
    *,
    execution_time: datetime | None = None,
) -> dict[str, Any]:
    at = execution_time or datetime.now(timezone.utc)
    if at.tzinfo is None:
        raise ForgettingError("forgetting_execution_time_invalid")
    validate_forgetting_dataset(records)
    statuses = Counter(str(record.get("status")) for record in records)
    eligible = [
        record
        for record in records
        if record.get("status") == "active" and _effective_at(record, at)
    ]
    negative = [record for record in eligible if record.get("kind") == NEGATIVE_KIND]
    return {
        "schema_version": "openai_database.memory_forgetting_assessment.v1",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "record_count": len(records),
        "status_counts": {status: statuses[status] for status in ("active", "candidate", "disputed", "retired")},
        "current_answer_eligible_count": len(eligible),
        "current_negative_boundary_count": len(negative),
        "inactive_answer_eligible_count": 0,
        "absence_inference_count": 0,
        "git_history_erasure_claim": False,
    }


def retrieval_decision(
    returned_records: Sequence[Mapping[str, Any]],
    trace: Mapping[str, Any],
    *,
    query_mode: str,
    include_inactive: bool,
) -> dict[str, Any]:
    historical = query_mode != "current"
    positive_count = 0
    negative_count = 0
    audit_only_count = 0
    for record in returned_records:
        query_state = _mapping(record.get("query_state"), "forgetting_query_state")
        eligible = query_state.get("retrieval_eligible") is True
        if not eligible:
            audit_only_count += 1
        elif record.get("kind") == NEGATIVE_KIND:
            negative_count += 1
        else:
            positive_count += 1

    if positive_count and negative_count:
        state = "mixed"
        knowledge_state = "VERIFIED_WITH_NEGATIVE_BOUNDARY"
        reason_code = "verified_records_and_negative_boundaries"
    elif positive_count:
        state = "historical" if historical else "answer"
        knowledge_state = "VERIFIED_HISTORICAL" if historical else "VERIFIED"
        reason_code = "explicit_historical_query" if historical else "verified_active_records"
    elif negative_count:
        state = "negative_boundary"
        knowledge_state = "VERIFIED_NEGATIVE"
        reason_code = "confirmed_negative_boundary"
    else:
        state = "abstain"
        knowledge_state = "UNKNOWN"
        excluded = _mapping(trace.get("excluded_counts", {}), "forgetting_excluded_counts")
        if int(excluded.get("unresolved_conflict", 0)):
            reason_code = "unresolved_conflict"
            missing_conditions = ["resolved_conflict", "verified_active_record"]
        elif int(excluded.get("retired_or_expired", 0)):
            reason_code = "retired_or_expired"
            missing_conditions = ["current_validity", "verified_active_record"]
        elif int(excluded.get("candidate_or_unverified", 0)):
            reason_code = "candidate_or_unverified"
            missing_conditions = ["verified_active_record"]
        else:
            reason_code = "insufficient_evidence"
            missing_conditions = ["verified_active_record"]
        return {
            "schema_version": "openai_database.memory_retrieval_decision.v1",
            "task_id": TASK_ID,
            "acceptance_id": ACCEPTANCE_ID,
            "state": state,
            "knowledge_state": knowledge_state,
            "reason_code": reason_code,
            "missing_conditions": missing_conditions,
            "positive_assertion_allowed": False,
            "confirmed_negative_assertion_allowed": False,
            "historical_assertion_only": historical,
            "inactive_answer_eligible": False,
            "include_inactive_mode": "audit_only" if include_inactive else "excluded",
            "eligible_positive_count": 0,
            "negative_boundary_count": 0,
            "audit_only_count": audit_only_count,
        }

    return {
        "schema_version": "openai_database.memory_retrieval_decision.v1",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "state": state,
        "knowledge_state": knowledge_state,
        "reason_code": reason_code,
        "missing_conditions": [],
        "positive_assertion_allowed": bool(positive_count and not historical),
        "confirmed_negative_assertion_allowed": bool(negative_count),
        "historical_assertion_only": historical,
        "inactive_answer_eligible": False,
        "include_inactive_mode": "audit_only" if include_inactive else "excluded",
        "eligible_positive_count": positive_count,
        "negative_boundary_count": negative_count,
        "audit_only_count": audit_only_count,
    }


def _fama_fraction(
    *,
    presence_total: int,
    presence_satisfied: int,
    forgetting_total: int,
    forgetting_satisfied: int,
) -> tuple[Fraction, Fraction, Fraction, Fraction]:
    if (
        presence_total < 0
        or forgetting_total < 0
        or not 0 <= presence_satisfied <= presence_total
        or not 0 <= forgetting_satisfied <= forgetting_total
        or presence_total + forgetting_total == 0
    ):
        raise ForgettingError("fama_counts_invalid")
    mpa = Fraction(presence_satisfied, presence_total) if presence_total else Fraction(1)
    faa = Fraction(forgetting_satisfied, forgetting_total) if forgetting_total else Fraction(1)
    weight = Fraction(forgetting_total, presence_total + forgetting_total)
    fama = max(Fraction(0), mpa - weight * (1 - faa))
    return mpa, faa, weight, fama


def fama_score(
    *,
    presence_total: int,
    presence_satisfied: int,
    forgetting_total: int,
    forgetting_satisfied: int,
) -> dict[str, float]:
    mpa, faa, weight, fama = _fama_fraction(
        presence_total=presence_total,
        presence_satisfied=presence_satisfied,
        forgetting_total=forgetting_total,
        forgetting_satisfied=forgetting_satisfied,
    )
    return {
        "memory_presence_accuracy": float(mpa),
        "forgetting_absence_accuracy": float(faa),
        "forgetting_weight": float(weight),
        "fama": float(fama),
    }


def _ratio(numerator: int, denominator: int) -> Fraction:
    return Fraction(numerator, denominator) if denominator else Fraction(1)


def evaluate_forgetting_cases(
    cases: Sequence[Mapping[str, Any]],
    policy: Mapping[str, Any],
) -> dict[str, Any]:
    validate_policy(policy)
    if not cases:
        raise ForgettingError("forgetting_cases_empty")
    case_ids: set[str] = set()
    fama_values: list[Fraction] = []
    critical_stale_use_count = 0
    true_abstain = 0
    false_abstain = 0
    missed_abstain = 0
    for case in cases:
        case_id = case.get("case_id")
        if not isinstance(case_id, str) or not case_id or case_id in case_ids:
            raise ForgettingError("forgetting_case_id_invalid")
        case_ids.add(case_id)
        expected = set(_string_ids(case.get("expected_record_ids"), "forgetting_expected_ids"))
        forbidden = set(_string_ids(case.get("forbidden_record_ids"), "forgetting_forbidden_ids"))
        returned = set(_string_ids(case.get("returned_record_ids"), "forgetting_returned_ids"))
        if expected & forbidden:
            raise ForgettingError("forgetting_case_criteria_overlap")
        if expected or forbidden:
            _, _, _, case_fama = _fama_fraction(
                presence_total=len(expected),
                presence_satisfied=len(expected & returned),
                forgetting_total=len(forbidden),
                forgetting_satisfied=len(forbidden - returned),
            )
            fama_values.append(case_fama)
        if case.get("critical") is True:
            critical_stale_use_count += len(forbidden & returned)
        should_abstain = case.get("should_abstain")
        decision_state = case.get("decision_state")
        if not isinstance(should_abstain, bool) or not isinstance(decision_state, str):
            raise ForgettingError("forgetting_case_decision_invalid")
        did_abstain = decision_state == "abstain"
        if should_abstain and did_abstain:
            true_abstain += 1
        elif not should_abstain and did_abstain:
            false_abstain += 1
        elif should_abstain and not did_abstain:
            missed_abstain += 1

    if not fama_values:
        raise ForgettingError("forgetting_cases_missing_fama_criteria")
    precision = _ratio(true_abstain, true_abstain + false_abstain)
    recall = _ratio(true_abstain, true_abstain + missed_abstain)
    fama = sum(fama_values, Fraction(0)) / len(fama_values)
    passed = (
        critical_stale_use_count == 0
        and fama >= FAMA_MIN
        and precision >= ABSTENTION_MIN
        and recall >= ABSTENTION_MIN
    )
    return {
        "schema_version": "openai_database.memory_forgetting_evaluation.v1",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "case_count": len(cases),
        "critical_stale_use_count": critical_stale_use_count,
        "fama": float(fama),
        "fama_min": float(FAMA_MIN),
        "abstention_precision": float(precision),
        "abstention_recall": float(recall),
        "abstention_min": float(ABSTENTION_MIN),
        "passed": passed,
    }
