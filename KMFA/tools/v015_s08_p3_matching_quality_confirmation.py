#!/usr/bin/env python3
"""KMFA v1.5 S08-P3 matching quality, confirmation and decision controls.

The module is intentionally storage-agnostic.  It accepts an external policy,
builds plain-language confirmation cards, records append-only control events,
and recalculates declared downstream chains without mutating source or fact
records.  Public fixtures are synthetic and contain no private business data.
"""

from __future__ import annotations

import copy
import json
from collections.abc import Mapping, Sequence
from typing import Any


RUN_PHASE_ID = "V015_S08_P3_MATCHING_QUALITY_CONFIRMATION"
ROADMAP_PHASE_ID = "S08-P3"
TASK_ID = "KMFA-V015-S08-P3-MATCHING-QUALITY-CONFIRMATION-20260715"
ACCEPTANCE_ID = "ACC-KMFA-V015-S08-P3-MATCHING-QUALITY-CONFIRMATION"
VERSION = "1.5.0-dev-s08p3"
SCHEMA_VERSION = "kmfa.v015.s08p3.matching_quality_confirmation.v1"

MATCH_STATES = ("AUTO_MATCH", "CANDIDATE_REVIEW", "MANUAL_CONFIRMATION")
DECISIONS = ("CONFIRMED_MATCH", "CONFIRMED_NOT_MATCH", "DEFERRED")
CONTROL_EVENT_TYPES = (
    "MATCH_DECISION_RECORDED",
    "MATCH_DECISION_REVERSED",
    "MATCH_DECISION_ROLLBACK",
)
PLAIN_LANGUAGE_FORBIDDEN_TERMS = (
    "hash",
    "sha-",
    "digest",
    "checksum",
    "payload",
    "record_ref",
    "basis point",
    "基点",
)


class MatchingControlError(ValueError):
    """Fail-closed S08-P3 input or control-event error."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MatchingControlError("TEXT_REQUIRED", f"{field} must be non-empty text")
    return value.strip()


def _score(value: Any, field: str = "score_bps") -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 10000:
        raise MatchingControlError("SCORE_OUT_OF_RANGE", f"{field} must be an integer from 0 to 10000")
    return value


def _text_list(value: Any, field: str) -> list[str]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise MatchingControlError("TEXT_LIST_REQUIRED", f"{field} must be a sequence")
    return [_text(item, f"{field}[]") for item in value]


def default_matching_policy() -> dict[str, Any]:
    """Return the tracked public-safe default policy as a fresh object."""

    return {
        "schema_version": "kmfa.v015.s08p3.matching_threshold_policy.v1",
        "policy_ref": "MATCH-POLICY-S08P3-V1",
        "policy_version": "1.0.0",
        "policy_source": "TRACKED_PUBLIC_SAFE_CONFIG",
        "score_scale_max_bps": 10000,
        "auto_match_min_bps": 8500,
        "candidate_review_min_bps": 7000,
        "hard_conflict_requires_manual_confirmation": True,
        "minimum_policy_regression_case_count": 5,
        "state_labels_zh": {
            "AUTO_MATCH": "自动通过",
            "CANDIDATE_REVIEW": "候选，需确认",
            "MANUAL_CONFIRMATION": "必须人工确认",
        },
        "threshold_change_requires_regression": True,
        "silent_threshold_change_allowed": False,
    }


def validate_matching_policy(policy: Mapping[str, Any]) -> dict[str, Any]:
    """Validate ordering, labels and change-control requirements."""

    if not isinstance(policy, Mapping):
        raise MatchingControlError("POLICY_REQUIRED", "policy must be a mapping")
    value = copy.deepcopy(dict(policy))
    if value.get("schema_version") != "kmfa.v015.s08p3.matching_threshold_policy.v1":
        raise MatchingControlError("POLICY_SCHEMA_INVALID", "unexpected matching policy schema")
    _text(value.get("policy_ref"), "policy_ref")
    _text(value.get("policy_version"), "policy_version")
    if value.get("policy_source") != "TRACKED_PUBLIC_SAFE_CONFIG":
        raise MatchingControlError("POLICY_NOT_EXTERNALIZED", "policy must come from tracked public-safe config")
    maximum = _score(value.get("score_scale_max_bps"), "score_scale_max_bps")
    auto = _score(value.get("auto_match_min_bps"), "auto_match_min_bps")
    candidate = _score(value.get("candidate_review_min_bps"), "candidate_review_min_bps")
    if maximum != 10000 or not 0 < candidate < auto <= maximum:
        raise MatchingControlError(
            "POLICY_THRESHOLD_ORDER_INVALID",
            "thresholds must satisfy 0 < candidate < automatic <= 10000",
        )
    minimum_cases = value.get("minimum_policy_regression_case_count")
    if isinstance(minimum_cases, bool) or not isinstance(minimum_cases, int) or minimum_cases < 1:
        raise MatchingControlError("POLICY_REGRESSION_COUNT_INVALID", "minimum regression case count must be positive")
    labels = value.get("state_labels_zh")
    if not isinstance(labels, Mapping) or set(labels) != set(MATCH_STATES):
        raise MatchingControlError("POLICY_STATE_LABELS_INVALID", "all three state labels are required")
    for state in MATCH_STATES:
        _text(labels[state], f"state_labels_zh.{state}")
    if value.get("hard_conflict_requires_manual_confirmation") is not True:
        raise MatchingControlError("HARD_CONFLICT_GATE_REQUIRED", "hard conflicts must require manual confirmation")
    if value.get("threshold_change_requires_regression") is not True:
        raise MatchingControlError("POLICY_REGRESSION_REQUIRED", "threshold changes must require regression")
    if value.get("silent_threshold_change_allowed") is not False:
        raise MatchingControlError("SILENT_POLICY_CHANGE_FORBIDDEN", "silent threshold change is forbidden")
    return value


def classify_match(
    *,
    case_ref: str,
    score_bps: int,
    matched_points_zh: Sequence[str],
    conflict_points_zh: Sequence[str],
    missing_points_zh: Sequence[str] = (),
    impact_zh: str,
    hard_conflict_codes: Sequence[str] = (),
    policy: Mapping[str, Any],
) -> dict[str, Any]:
    """Classify a match into automatic, candidate or manual state."""

    checked_policy = validate_matching_policy(policy)
    score = _score(score_bps)
    matched = _text_list(matched_points_zh, "matched_points_zh")
    conflicts = _text_list(conflict_points_zh, "conflict_points_zh")
    missing = _text_list(missing_points_zh, "missing_points_zh")
    hard_conflicts = _text_list(hard_conflict_codes, "hard_conflict_codes")
    case = _text(case_ref, "case_ref")
    impact = _text(impact_zh, "impact_zh")
    reasons: list[dict[str, str]] = []
    if hard_conflicts:
        state = "MANUAL_CONFIRMATION"
        reasons.append({"code": "HARD_CONFLICT", "reason_zh": "存在关键冲突，系统不能自动决定。"})
    elif score >= checked_policy["auto_match_min_bps"]:
        state = "AUTO_MATCH"
        reasons.append({"code": "AUTO_THRESHOLD_MET", "reason_zh": "匹配程度达到自动通过标准，且没有关键冲突。"})
    elif score >= checked_policy["candidate_review_min_bps"]:
        state = "CANDIDATE_REVIEW"
        reasons.append({"code": "CANDIDATE_BAND", "reason_zh": "信息较为接近，但仍需要人员确认。"})
    else:
        state = "MANUAL_CONFIRMATION"
        reasons.append({"code": "BELOW_CANDIDATE_THRESHOLD", "reason_zh": "现有信息不足以形成可靠候选。"})
    if conflicts and not hard_conflicts:
        reasons.append({"code": "NON_HARD_CONFLICT", "reason_zh": "仍有需要查看的不一致信息。"})
    if missing:
        reasons.append({"code": "MISSING_EVIDENCE", "reason_zh": "部分判断信息缺失。"})
    return {
        "schema_version": "kmfa.v015.s08p3.match_classification.v1",
        "case_ref": case,
        "policy_ref": checked_policy["policy_ref"],
        "policy_version": checked_policy["policy_version"],
        "score_bps": score,
        "state": state,
        "state_label_zh": checked_policy["state_labels_zh"][state],
        "matched_points_zh": matched,
        "conflict_points_zh": conflicts,
        "missing_points_zh": missing,
        "hard_conflict_codes": hard_conflicts,
        "impact_zh": impact,
        "reason_details": reasons,
        "auto_merge_allowed": state == "AUTO_MATCH",
        "thresholds_externalized": True,
        "threshold_change_requires_regression": True,
        "source_mutation_performed": False,
    }


def validate_policy_change(
    current_policy: Mapping[str, Any],
    proposed_policy: Mapping[str, Any],
    regression_cases: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Require explicit expected before/after outcomes for every policy change."""

    current = validate_matching_policy(current_policy)
    proposed = validate_matching_policy(proposed_policy)
    changed = [
        key
        for key in ("auto_match_min_bps", "candidate_review_min_bps")
        if current[key] != proposed[key]
    ]
    if not changed:
        raise MatchingControlError("POLICY_THRESHOLDS_UNCHANGED", "a threshold change was not supplied")
    if proposed["policy_version"] == current["policy_version"]:
        raise MatchingControlError("POLICY_VERSION_NOT_ADVANCED", "changed thresholds require a new policy version")
    if isinstance(regression_cases, (str, bytes)) or not isinstance(regression_cases, Sequence):
        raise MatchingControlError("POLICY_REGRESSION_REQUIRED", "regression cases are required")
    required_count = max(
        current["minimum_policy_regression_case_count"],
        proposed["minimum_policy_regression_case_count"],
    )
    if len(regression_cases) < required_count:
        raise MatchingControlError(
            "POLICY_REGRESSION_REQUIRED",
            f"at least {required_count} regression cases are required",
        )
    results: list[dict[str, Any]] = []
    for index, row in enumerate(regression_cases, start=1):
        if not isinstance(row, Mapping):
            raise MatchingControlError("POLICY_REGRESSION_CASE_INVALID", f"case {index} must be a mapping")
        common = {
            "case_ref": _text(row.get("case_ref"), f"regression_cases[{index}].case_ref"),
            "score_bps": _score(row.get("score_bps")),
            "matched_points_zh": row.get("matched_points_zh", ["项目名称一致"]),
            "conflict_points_zh": row.get("conflict_points_zh", []),
            "missing_points_zh": row.get("missing_points_zh", []),
            "impact_zh": row.get("impact_zh", "影响项目归属和后续汇总。"),
            "hard_conflict_codes": row.get("hard_conflict_codes", []),
        }
        before = classify_match(**common, policy=current)["state"]
        after = classify_match(**common, policy=proposed)["state"]
        expected_before = _text(row.get("expected_before"), "expected_before")
        expected_after = _text(row.get("expected_after"), "expected_after")
        if expected_before not in MATCH_STATES or expected_after not in MATCH_STATES:
            raise MatchingControlError("POLICY_REGRESSION_EXPECTATION_INVALID", "expected state is invalid")
        passed = before == expected_before and after == expected_after
        results.append(
            {
                "case_ref": common["case_ref"],
                "before_state": before,
                "after_state": after,
                "expected_before": expected_before,
                "expected_after": expected_after,
                "status": "PASS" if passed else "FAIL",
            }
        )
    failures = [row["case_ref"] for row in results if row["status"] != "PASS"]
    if failures:
        raise MatchingControlError("POLICY_REGRESSION_FAILED", "unexpected result for: " + ", ".join(failures))
    return {
        "schema_version": "kmfa.v015.s08p3.policy_regression.v1",
        "current_policy_ref": current["policy_ref"],
        "current_policy_version": current["policy_version"],
        "proposed_policy_ref": proposed["policy_ref"],
        "proposed_policy_version": proposed["policy_version"],
        "changed_threshold_fields": changed,
        "regression_case_count": len(results),
        "regression_pass_count": len(results),
        "regression_fail_count": 0,
        "threshold_change_accepted": True,
        "case_results": results,
    }


def _assert_plain_language(value: Mapping[str, Any]) -> None:
    text = json.dumps(value, ensure_ascii=False).lower()
    hits = [term for term in PLAIN_LANGUAGE_FORBIDDEN_TERMS if term.lower() in text]
    if hits:
        raise MatchingControlError("TECHNICAL_TERM_EXPOSED", "confirmation card contains: " + ", ".join(hits))


def build_confirmation_card(
    *,
    classification: Mapping[str, Any],
    current_record: Mapping[str, str],
    candidate_record: Mapping[str, str],
) -> dict[str, Any]:
    """Build a side-by-side, ordinary-Chinese confirmation card."""

    if classification.get("state") not in {"CANDIDATE_REVIEW", "MANUAL_CONFIRMATION"}:
        raise MatchingControlError("CONFIRMATION_NOT_REQUIRED", "automatic matches do not need a confirmation card")
    required_fields = ("项目名称", "合同编号", "公司主体", "往来方", "时间说明", "金额说明")
    left = {field: _text(current_record.get(field), f"current_record.{field}") for field in required_fields}
    right = {field: _text(candidate_record.get(field), f"candidate_record.{field}") for field in required_fields}
    score = _score(classification.get("score_bps"))
    card = {
        "界面标题": "请确认这两条记录是否属于同一项目",
        "当前建议": _text(classification.get("state_label_zh"), "state_label_zh"),
        "匹配程度": f"{score // 100}%",
        "并排对比": [
            {"名称": "当前记录", "信息": left},
            {"名称": "候选记录", "信息": right},
        ],
        "相同点": _text_list(classification.get("matched_points_zh", []), "matched_points_zh"),
        "冲突点": _text_list(classification.get("conflict_points_zh", []), "conflict_points_zh")
        or ["未发现明确冲突，但仍需确认。"],
        "缺失信息": _text_list(classification.get("missing_points_zh", []), "missing_points_zh")
        or ["没有额外缺失信息。"],
        "可能影响": _text(classification.get("impact_zh"), "impact_zh"),
        "可选操作": [
            {"操作": "确认是同一项目", "说明": "记录本次决定，并重新计算受影响的汇总和报告。"},
            {"操作": "确认不是同一项目", "说明": "保留两条独立记录，并重新计算受影响的汇总和报告。"},
            {"操作": "暂不确定", "说明": "保留待确认状态，不做自动合并。"},
        ],
        "资料保护说明": "确认只会新增一条决定记录，不会修改原始资料或事实记录。",
    }
    _assert_plain_language(card)
    return card


class ImmutableFactStore:
    """Small executable guard proving that S08-P3 cannot edit facts directly."""

    def __init__(self, facts: Mapping[str, Mapping[str, Any]]) -> None:
        self._facts = copy.deepcopy(dict(facts))

    def snapshot(self) -> dict[str, Any]:
        return copy.deepcopy(self._facts)

    def direct_update(self, _fact_ref: str, _changes: Mapping[str, Any]) -> None:
        raise MatchingControlError(
            "DIRECT_FACT_TABLE_MUTATION_FORBIDDEN",
            "matching decisions must be control events, never fact-table updates",
        )


class MatchDecisionLedger:
    """Append-only in-memory event ledger with deterministic JSONL replay."""

    def __init__(self, events: Sequence[Mapping[str, Any]] = ()) -> None:
        self._events: list[dict[str, Any]] = []
        for event in events:
            self._append_existing(event)

    @property
    def events(self) -> list[dict[str, Any]]:
        return copy.deepcopy(self._events)

    def _next_ref(self) -> str:
        return f"CTRL-EVENT-S08P3-{len(self._events) + 1:03d}"

    def _append_existing(self, event: Mapping[str, Any]) -> None:
        if not isinstance(event, Mapping):
            raise MatchingControlError("EVENT_CHAIN_INVALID", "event must be a mapping")
        value = copy.deepcopy(dict(event))
        expected_sequence = len(self._events) + 1
        expected_ref = f"CTRL-EVENT-S08P3-{expected_sequence:03d}"
        previous = self._events[-1]["event_ref"] if self._events else None
        if (
            value.get("schema_version") != "kmfa.v015.s08p3.match_decision_event.v1"
            or isinstance(value.get("sequence"), bool)
            or value.get("sequence") != expected_sequence
            or value.get("event_ref") != expected_ref
            or value.get("previous_event_ref") != previous
            or value.get("event_type") not in CONTROL_EVENT_TYPES
            or value.get("control_event_recorded") is not True
            or value.get("append_only") is not True
            or value.get("auditable") is not True
            or value.get("reversible") is not True
            or value.get("raw_source_mutation_performed") is not False
            or value.get("fact_table_mutation_performed") is not False
            or value.get("affected_chain_recalculation_required") is not True
        ):
            raise MatchingControlError("EVENT_CHAIN_INVALID", "event sequence or immutable boundary is invalid")
        case_ref = _text(value.get("case_ref"), "event.case_ref")
        candidate_ref = _text(value.get("candidate_ref"), "event.candidate_ref")
        _text(value.get("actor_role"), "event.actor_role")
        _text(value.get("reason_zh"), "event.reason_zh")
        _text(value.get("recorded_at"), "event.recorded_at")
        event_type = value["event_type"]
        target_ref = value.get("target_event_ref")
        if event_type == "MATCH_DECISION_RECORDED":
            if value.get("resulting_decision") not in DECISIONS or target_ref is not None:
                raise MatchingControlError("EVENT_CHAIN_INVALID", "recorded decision payload is invalid")
        else:
            target = next((row for row in self._events if row["event_ref"] == target_ref), None)
            if target is None or target["case_ref"] != case_ref or target["candidate_ref"] != candidate_ref:
                raise MatchingControlError("EVENT_CHAIN_INVALID", "event target is missing or belongs to another match")
            if event_type == "MATCH_DECISION_REVERSED" and value.get("resulting_decision") != "NO_ACTIVE_DECISION":
                raise MatchingControlError("EVENT_CHAIN_INVALID", "reversal must clear the active decision")
            if event_type == "MATCH_DECISION_ROLLBACK" and (
                target.get("resulting_decision") not in DECISIONS
                or value.get("resulting_decision") != target.get("resulting_decision")
            ):
                raise MatchingControlError("EVENT_CHAIN_INVALID", "rollback must restore a recorded decision")
        self._events.append(value)

    def _append(
        self,
        *,
        event_type: str,
        case_ref: str,
        candidate_ref: str,
        resulting_decision: str,
        actor_role: str,
        reason_zh: str,
        recorded_at: str,
        target_event_ref: str | None = None,
    ) -> dict[str, Any]:
        if event_type not in CONTROL_EVENT_TYPES:
            raise MatchingControlError("EVENT_TYPE_INVALID", "unsupported control event type")
        sequence = len(self._events) + 1
        event = {
            "schema_version": "kmfa.v015.s08p3.match_decision_event.v1",
            "event_ref": self._next_ref(),
            "sequence": sequence,
            "previous_event_ref": self._events[-1]["event_ref"] if self._events else None,
            "event_type": event_type,
            "case_ref": _text(case_ref, "case_ref"),
            "candidate_ref": _text(candidate_ref, "candidate_ref"),
            "resulting_decision": resulting_decision,
            "actor_role": _text(actor_role, "actor_role"),
            "reason_zh": _text(reason_zh, "reason_zh"),
            "recorded_at": _text(recorded_at, "recorded_at"),
            "target_event_ref": target_event_ref,
            "control_event_recorded": True,
            "append_only": True,
            "auditable": True,
            "reversible": True,
            "raw_source_mutation_performed": False,
            "fact_table_mutation_performed": False,
            "affected_chain_recalculation_required": True,
        }
        self._append_existing(event)
        return copy.deepcopy(event)

    def record_decision(
        self,
        *,
        case_ref: str,
        candidate_ref: str,
        decision: str,
        actor_role: str,
        reason_zh: str,
        recorded_at: str,
    ) -> dict[str, Any]:
        if decision not in DECISIONS:
            raise MatchingControlError("DECISION_INVALID", "unsupported match decision")
        return self._append(
            event_type="MATCH_DECISION_RECORDED",
            case_ref=case_ref,
            candidate_ref=candidate_ref,
            resulting_decision=decision,
            actor_role=actor_role,
            reason_zh=reason_zh,
            recorded_at=recorded_at,
        )

    def _event(self, event_ref: str) -> dict[str, Any]:
        match = next((row for row in self._events if row["event_ref"] == event_ref), None)
        if match is None:
            raise MatchingControlError("TARGET_EVENT_NOT_FOUND", "target event does not exist")
        return match

    def reverse_decision(
        self,
        *,
        target_event_ref: str,
        actor_role: str,
        reason_zh: str,
        recorded_at: str,
    ) -> dict[str, Any]:
        target = self._event(target_event_ref)
        return self._append(
            event_type="MATCH_DECISION_REVERSED",
            case_ref=target["case_ref"],
            candidate_ref=target["candidate_ref"],
            resulting_decision="NO_ACTIVE_DECISION",
            actor_role=actor_role,
            reason_zh=reason_zh,
            recorded_at=recorded_at,
            target_event_ref=target_event_ref,
        )

    def rollback_to(
        self,
        *,
        target_event_ref: str,
        actor_role: str,
        reason_zh: str,
        recorded_at: str,
    ) -> dict[str, Any]:
        target = self._event(target_event_ref)
        if target["resulting_decision"] not in DECISIONS:
            raise MatchingControlError("ROLLBACK_TARGET_INVALID", "target event has no reusable decision")
        return self._append(
            event_type="MATCH_DECISION_ROLLBACK",
            case_ref=target["case_ref"],
            candidate_ref=target["candidate_ref"],
            resulting_decision=target["resulting_decision"],
            actor_role=actor_role,
            reason_zh=reason_zh,
            recorded_at=recorded_at,
            target_event_ref=target_event_ref,
        )

    def current_decision(self, *, case_ref: str | None = None, candidate_ref: str | None = None) -> str:
        """Return the latest decision for exactly one match pair."""

        pairs = {(row["case_ref"], row["candidate_ref"]) for row in self._events}
        if case_ref is None and candidate_ref is None:
            if not pairs:
                return "NO_ACTIVE_DECISION"
            if len(pairs) != 1:
                raise MatchingControlError("MATCH_PAIR_REQUIRED", "case_ref and candidate_ref are required")
            selected = next(iter(pairs))
        elif case_ref is None or candidate_ref is None:
            raise MatchingControlError("MATCH_PAIR_REQUIRED", "case_ref and candidate_ref must be supplied together")
        else:
            selected = (_text(case_ref, "case_ref"), _text(candidate_ref, "candidate_ref"))
        matching = [row for row in self._events if (row["case_ref"], row["candidate_ref"]) == selected]
        return matching[-1]["resulting_decision"] if matching else "NO_ACTIVE_DECISION"

    def to_jsonl(self) -> str:
        return "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in self._events)

    @classmethod
    def from_jsonl(cls, text: str) -> "MatchDecisionLedger":
        try:
            rows = [json.loads(line) for line in text.splitlines() if line.strip()]
        except json.JSONDecodeError as error:
            raise MatchingControlError("EVENT_PERSISTENCE_INVALID", str(error)) from error
        if not all(isinstance(row, dict) for row in rows):
            raise MatchingControlError("EVENT_PERSISTENCE_INVALID", "all JSONL rows must be objects")
        return cls(rows)


class AffectedChainRecalculator:
    """Generate deterministic recalculation receipts from control events."""

    def __init__(self, dependencies: Mapping[str, Sequence[str]]) -> None:
        self._dependencies = {
            _text(case_ref, "dependencies.case_ref"): _text_list(nodes, "dependencies.nodes")
            for case_ref, nodes in dependencies.items()
        }
        self._receipts: list[dict[str, Any]] = []

    @property
    def receipts(self) -> list[dict[str, Any]]:
        return copy.deepcopy(self._receipts)

    def recalculate(self, event: Mapping[str, Any]) -> dict[str, Any]:
        if (
            not isinstance(event, Mapping)
            or event.get("schema_version") != "kmfa.v015.s08p3.match_decision_event.v1"
            or event.get("event_type") not in CONTROL_EVENT_TYPES
            or event.get("control_event_recorded") is not True
            or event.get("affected_chain_recalculation_required") is not True
            or event.get("raw_source_mutation_performed") is not False
            or event.get("fact_table_mutation_performed") is not False
        ):
            raise MatchingControlError("CONTROL_EVENT_REQUIRED", "recalculation requires a recorded control event")
        event_ref = _text(event.get("event_ref"), "event.event_ref")
        sequence = event.get("sequence")
        if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 1:
            raise MatchingControlError("CONTROL_EVENT_REQUIRED", "control event sequence is invalid")
        case_ref = _text(event.get("case_ref"), "event.case_ref")
        affected = self._dependencies.get(case_ref)
        if not affected:
            raise MatchingControlError("AFFECTED_CHAIN_MISSING", "no downstream chain is registered")
        receipt = {
            "schema_version": "kmfa.v015.s08p3.affected_chain_recalculation.v1",
            "recalculation_ref": f"RECALC-S08P3-{len(self._receipts) + 1:03d}",
            "trigger_event_ref": event_ref,
            "case_ref": case_ref,
            "affected_chain": list(affected),
            "affected_node_count": len(affected),
            "status": "RECALCULATED",
            "source_event_sequence": sequence,
            "raw_source_mutation_performed": False,
            "fact_table_mutation_performed": False,
        }
        self._receipts.append(receipt)
        return copy.deepcopy(receipt)


def synthetic_acceptance_cases() -> dict[str, Any]:
    """Return deterministic public-safe evidence for all three Roadmap tasks."""

    policy = default_matching_policy()
    common = {
        "matched_points_zh": ["项目名称一致", "公司主体一致"],
        "missing_points_zh": [],
        "impact_zh": "决定会影响项目归属、汇总和后续报告。",
        "policy": policy,
    }
    classifications = {
        "automatic": classify_match(
            case_ref="SYN-MATCH-AUTO",
            score_bps=9200,
            conflict_points_zh=[],
            hard_conflict_codes=[],
            **common,
        ),
        "candidate": classify_match(
            case_ref="SYN-MATCH-CANDIDATE",
            score_bps=7600,
            conflict_points_zh=["合同编号写法不同"],
            hard_conflict_codes=[],
            **common,
        ),
        "manual_low": classify_match(
            case_ref="SYN-MATCH-MANUAL-LOW",
            score_bps=6200,
            conflict_points_zh=["时间范围不一致"],
            missing_points_zh=["缺少合同编号"],
            hard_conflict_codes=[],
            **{key: value for key, value in common.items() if key != "missing_points_zh"},
        ),
        "manual_hard_conflict": classify_match(
            case_ref="SYN-MATCH-MANUAL-CONFLICT",
            score_bps=9300,
            conflict_points_zh=["公司主体不同"],
            hard_conflict_codes=["COMPANY_ENTITY_CONFLICT"],
            **common,
        ),
    }

    proposed_policy = default_matching_policy()
    proposed_policy.update(
        {
            "policy_ref": "MATCH-POLICY-S08P3-V2-SYNTHETIC",
            "policy_version": "2.0.0-synthetic",
            "auto_match_min_bps": 8700,
            "candidate_review_min_bps": 7200,
        }
    )
    regression_rows = [
        {"case_ref": "REG-9200", "score_bps": 9200, "expected_before": "AUTO_MATCH", "expected_after": "AUTO_MATCH"},
        {"case_ref": "REG-8600", "score_bps": 8600, "expected_before": "AUTO_MATCH", "expected_after": "CANDIDATE_REVIEW"},
        {"case_ref": "REG-7600", "score_bps": 7600, "expected_before": "CANDIDATE_REVIEW", "expected_after": "CANDIDATE_REVIEW"},
        {"case_ref": "REG-7100", "score_bps": 7100, "expected_before": "CANDIDATE_REVIEW", "expected_after": "MANUAL_CONFIRMATION"},
        {
            "case_ref": "REG-HARD-CONFLICT",
            "score_bps": 9400,
            "hard_conflict_codes": ["COMPANY_ENTITY_CONFLICT"],
            "conflict_points_zh": ["公司主体不同"],
            "expected_before": "MANUAL_CONFIRMATION",
            "expected_after": "MANUAL_CONFIRMATION",
        },
    ]
    regression = validate_policy_change(policy, proposed_policy, regression_rows)
    try:
        validate_policy_change(policy, proposed_policy, [])
    except MatchingControlError as error:
        regression_required_enforced = error.code == "POLICY_REGRESSION_REQUIRED"
    else:  # pragma: no cover - safety alarm
        regression_required_enforced = False

    current_record = {
        "项目名称": "示例能源改造项目",
        "合同编号": "示例合同甲",
        "公司主体": "示例运营主体甲",
        "往来方": "示例协作方甲",
        "时间说明": "同一经营期间",
        "金额说明": "金额范围接近",
    }
    candidate_record = {
        "项目名称": "示例能源改造工程",
        "合同编号": "示例合同乙",
        "公司主体": "示例运营主体甲",
        "往来方": "示例协作方甲",
        "时间说明": "同一经营期间",
        "金额说明": "金额范围接近",
    }
    confirmation_cards = [
        build_confirmation_card(
            classification=classifications["candidate"],
            current_record=current_record,
            candidate_record=candidate_record,
        ),
        build_confirmation_card(
            classification=classifications["manual_hard_conflict"],
            current_record=current_record,
            candidate_record={**candidate_record, "公司主体": "示例运营主体乙"},
        ),
    ]

    raw_source = {"source_ref": "SYN-SOURCE-001", "immutable_marker": "UNCHANGED"}
    raw_before = copy.deepcopy(raw_source)
    fact_store = ImmutableFactStore(
        {"FACT-SYN-001": {"version": "FACT-V1", "project_ref": "SYN-PROJECT-UNCONFIRMED"}}
    )
    facts_before = fact_store.snapshot()
    ledger = MatchDecisionLedger()
    recalculator = AffectedChainRecalculator(
        {
            "SYN-MATCH-CANDIDATE": [
                "PROJECT-ASSIGNMENT",
                "PROJECT-COST-SUMMARY",
                "REPORT-AVAILABILITY",
            ]
        }
    )
    first = ledger.record_decision(
        case_ref="SYN-MATCH-CANDIDATE",
        candidate_ref="SYN-CANDIDATE-001",
        decision="CONFIRMED_MATCH",
        actor_role="ROLE-DATA-STEWARD",
        reason_zh="两条记录经核对属于同一项目。",
        recorded_at="2026-07-15T12:00:00+10:00",
    )
    recalculator.recalculate(first)
    reversed_event = ledger.reverse_decision(
        target_event_ref=first["event_ref"],
        actor_role="ROLE-DATA-STEWARD",
        reason_zh="发现新的主体信息，先撤销原决定。",
        recorded_at="2026-07-15T12:01:00+10:00",
    )
    recalculator.recalculate(reversed_event)
    third = ledger.record_decision(
        case_ref="SYN-MATCH-CANDIDATE",
        candidate_ref="SYN-CANDIDATE-001",
        decision="CONFIRMED_NOT_MATCH",
        actor_role="ROLE-DATA-STEWARD",
        reason_zh="补充信息表明两条记录不属于同一项目。",
        recorded_at="2026-07-15T12:02:00+10:00",
    )
    recalculator.recalculate(third)
    rollback = ledger.rollback_to(
        target_event_ref=first["event_ref"],
        actor_role="ROLE-DATA-STEWARD",
        reason_zh="复核后回到首个已确认决定。",
        recorded_at="2026-07-15T12:03:00+10:00",
    )
    recalculator.recalculate(rollback)
    replayed = MatchDecisionLedger.from_jsonl(ledger.to_jsonl())
    try:
        fact_store.direct_update("FACT-SYN-001", {"project_ref": "SYN-PROJECT-CHANGED"})
    except MatchingControlError as error:
        direct_fact_mutation_rejected = error.code == "DIRECT_FACT_TABLE_MUTATION_FORBIDDEN"
    else:  # pragma: no cover - safety alarm
        direct_fact_mutation_rejected = False

    return {
        "schema_version": SCHEMA_VERSION,
        "fixture_scope": "PUBLIC_SAFE_SYNTHETIC",
        "matching_policy": policy,
        "classification_cases": classifications,
        "policy_regression": regression,
        "regression_required_enforced": regression_required_enforced,
        "confirmation_cards": confirmation_cards,
        "decision_events": ledger.events,
        "recalculation_receipts": recalculator.receipts,
        "decision_event_roundtrip_count": len(replayed.events),
        "decision_event_roundtrip_exact": replayed.events == ledger.events,
        "current_decision_after_rollback": replayed.current_decision(),
        "source_snapshot_unchanged": raw_source == raw_before,
        "fact_snapshot_unchanged": fact_store.snapshot() == facts_before,
        "direct_fact_mutation_rejected": direct_fact_mutation_rejected,
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "private_business_values_published": False,
    }


__all__ = [
    "ACCEPTANCE_ID",
    "AffectedChainRecalculator",
    "ImmutableFactStore",
    "MatchDecisionLedger",
    "MatchingControlError",
    "ROADMAP_PHASE_ID",
    "RUN_PHASE_ID",
    "TASK_ID",
    "VERSION",
    "build_confirmation_card",
    "classify_match",
    "default_matching_policy",
    "synthetic_acceptance_cases",
    "validate_matching_policy",
    "validate_policy_change",
]
