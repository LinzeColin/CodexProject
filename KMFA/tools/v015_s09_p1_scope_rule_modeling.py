#!/usr/bin/env python3
"""KMFA v1.5 S09-P1 scope-rule modeling controls.

This module defines one legal ledger with five explainable derived views, an
eight-type difference dictionary, and an append-only adjustment-event model.
It is deliberately storage-agnostic and uses synthetic fixtures only.  It does
not implement S09-P2 conversion or reconciliation execution.
"""

from __future__ import annotations

import copy
import json
from collections.abc import Mapping, Sequence
from datetime import date
from typing import Any


RUN_PHASE_ID = "V015_S09_P1_SCOPE_RULE_MODELING"
ROADMAP_PHASE_ID = "S09-P1"
TASK_ID = "KMFA-V015-S09-P1-SCOPE-RULE-MODELING-20260715"
ACCEPTANCE_ID = "ACC-KMFA-V015-S09-P1-SCOPE-RULE-MODELING"
VERSION = "1.5.0-dev-s09p1"
SCHEMA_VERSION = "kmfa.v015.s09p1.scope_rule_modeling.v1"

VIEW_IDS = (
    "STATUTORY_ACCOUNTING",
    "OPERATING_ANALYSIS",
    "PROJECT_REALITY",
    "FUNDS",
    "TAX_POLICY",
)
DIFFERENCE_TYPE_CODES = (
    "UNBILLED",
    "UNSETTLED",
    "UNALLOCATED",
    "ADVANCE_PAID",
    "RETENTION",
    "CROSS_PERIOD",
    "TAX_RATE",
    "BAD_DEBT",
)
DIFFERENCE_DIRECTIONS = (
    "INCREASE_DERIVED_VIEW",
    "DECREASE_DERIVED_VIEW",
    "TIMING_ONLY",
    "CONTEXT_DEPENDENT",
)
RISK_LEVELS = ("NORMAL", "HIGH")
EVENT_TYPES = (
    "ADJUSTMENT_PROPOSED",
    "ADJUSTMENT_APPROVED",
    "ADJUSTMENT_REVERSED",
)
APPROVER_ROLES = ("FINANCE_REVIEWER", "FINANCE_OWNER", "OWNER")
HIGH_RISK_APPROVER_ROLES = ("FINANCE_OWNER", "OWNER")


class ScopeRuleError(ValueError):
    """Fail-closed S09-P1 policy, dictionary, or event error."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


def _mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ScopeRuleError("MAPPING_REQUIRED", f"{field} must be a mapping")
    return copy.deepcopy(dict(value))


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ScopeRuleError("TEXT_REQUIRED", f"{field} must be non-empty text")
    return value.strip()


def _text_list(value: Any, field: str) -> list[str]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ScopeRuleError("TEXT_LIST_REQUIRED", f"{field} must be a sequence")
    result = [_text(item, f"{field}[]") for item in value]
    if len(result) != len(set(result)):
        raise ScopeRuleError("DUPLICATE_VALUE", f"{field} must not contain duplicates")
    return result


def _integer_cents(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ScopeRuleError("INTEGER_CENTS_REQUIRED", f"{field} must be signed integer cents")
    if value == 0:
        raise ScopeRuleError("ZERO_DIFFERENCE_INVALID", f"{field} must be non-zero")
    return value


def _iso_date(value: Any, field: str) -> str:
    text = _text(value, field)
    try:
        date.fromisoformat(text)
    except ValueError as error:
        raise ScopeRuleError("ISO_DATE_REQUIRED", f"{field} must use YYYY-MM-DD") from error
    return text


def default_ledger_view_policy() -> dict[str, Any]:
    """Return the tracked one-ledger/five-view policy."""

    common = {
        "source_ledger_ref": "LEGAL-LEDGER-PRIMARY",
        "rule_version": "SCOPE-RULE-V1",
        "independent_ledger": False,
        "reconciliation_to_legal_ledger_required": True,
        "adjustments_must_use_control_events": True,
        "source_value_mutation_allowed": False,
    }
    views = [
        {
            **common,
            "view_id": "STATUTORY_ACCOUNTING",
            "label_zh": "法定账务视图",
            "purpose_zh": "保持依法入账、凭证、期间和法定报表口径，不接受管理调整覆盖。",
        },
        {
            **common,
            "view_id": "OPERATING_ANALYSIS",
            "label_zh": "经营分析视图",
            "purpose_zh": "通过有原因、有证据、有审批的调整事件解释经营期间和经营口径。",
        },
        {
            **common,
            "view_id": "PROJECT_REALITY",
            "label_zh": "项目真实视图",
            "purpose_zh": "按项目身份、履约和成本归属展示可追溯的项目经营事实。",
        },
        {
            **common,
            "view_id": "FUNDS",
            "label_zh": "资金视图",
            "purpose_zh": "展示已登记主体、账户、收支和资金占用，不执行支付。",
        },
        {
            **common,
            "view_id": "TAX_POLICY",
            "label_zh": "税务与政策视图",
            "purpose_zh": "展示税率、发票和政策证据差异，不替代申报或监管判断。",
        },
    ]
    return {
        "schema_version": "kmfa.v015.s09p1.ledger_view_policy.v1",
        "policy_ref": "LEDGER-VIEW-POLICY-S09P1-V1",
        "policy_version": "1.0.0",
        "legal_ledger_ref": "LEGAL-LEDGER-PRIMARY",
        "legal_ledger_count": 1,
        "secondary_ledger_allowed": False,
        "view_materialization_as_independent_ledger_allowed": False,
        "statutory_reconciliation_bypass_allowed": False,
        "regulatory_evasion_allowed": False,
        "source_value_mutation_allowed": False,
        "adjustment_control_event_required": True,
        "views": views,
    }


def validate_ledger_view_policy(policy: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the one-ledger boundary and every derived-view contract."""

    value = _mapping(policy, "policy")
    if value.get("schema_version") != "kmfa.v015.s09p1.ledger_view_policy.v1":
        raise ScopeRuleError("LEDGER_POLICY_SCHEMA_INVALID", "unexpected ledger-view policy schema")
    _text(value.get("policy_ref"), "policy_ref")
    _text(value.get("policy_version"), "policy_version")
    ledger_ref = _text(value.get("legal_ledger_ref"), "legal_ledger_ref")
    if value.get("legal_ledger_count") != 1:
        raise ScopeRuleError("SINGLE_LEDGER_REQUIRED", "exactly one legal ledger is required")
    required_false = (
        "secondary_ledger_allowed",
        "view_materialization_as_independent_ledger_allowed",
        "statutory_reconciliation_bypass_allowed",
        "regulatory_evasion_allowed",
        "source_value_mutation_allowed",
    )
    if any(value.get(field) is not False for field in required_false):
        raise ScopeRuleError("ILLEGAL_LEDGER_BOUNDARY", "parallel ledger, bypass, evasion, and source mutation are forbidden")
    if value.get("adjustment_control_event_required") is not True:
        raise ScopeRuleError("ADJUSTMENT_EVENT_REQUIRED", "all management adjustments require control events")
    views = value.get("views")
    if isinstance(views, (str, bytes)) or not isinstance(views, Sequence):
        raise ScopeRuleError("VIEW_LIST_REQUIRED", "views must be a sequence")
    checked_views: list[dict[str, Any]] = []
    for index, raw in enumerate(views, start=1):
        view = _mapping(raw, f"views[{index}]")
        view_id = _text(view.get("view_id"), f"views[{index}].view_id")
        _text(view.get("label_zh"), f"views[{index}].label_zh")
        _text(view.get("purpose_zh"), f"views[{index}].purpose_zh")
        _text(view.get("rule_version"), f"views[{index}].rule_version")
        if view.get("source_ledger_ref") != ledger_ref:
            raise ScopeRuleError("VIEW_LEDGER_BINDING_INVALID", f"{view_id} must derive from the one legal ledger")
        if view.get("independent_ledger") is not False:
            raise ScopeRuleError("PARALLEL_LEDGER_FORBIDDEN", f"{view_id} cannot be an independent ledger")
        if view.get("reconciliation_to_legal_ledger_required") is not True:
            raise ScopeRuleError("RECONCILIATION_REQUIRED", f"{view_id} must reconcile to the legal ledger")
        if view.get("adjustments_must_use_control_events") is not True:
            raise ScopeRuleError("ADJUSTMENT_EVENT_REQUIRED", f"{view_id} adjustments require control events")
        if view.get("source_value_mutation_allowed") is not False:
            raise ScopeRuleError("SOURCE_MUTATION_FORBIDDEN", f"{view_id} cannot mutate source values")
        checked_views.append(view)
    ids = [row["view_id"] for row in checked_views]
    if len(ids) != len(set(ids)) or set(ids) != set(VIEW_IDS):
        raise ScopeRuleError("VIEW_SET_INVALID", "the five required views must appear exactly once")
    value["views"] = checked_views
    return value


def evaluate_view_boundary(request: Mapping[str, Any], policy: Mapping[str, Any]) -> dict[str, Any]:
    """Evaluate a view request without implementing the later conversion engine."""

    checked = validate_ledger_view_policy(policy)
    row = _mapping(request, "request")
    operation = _text(row.get("operation"), "operation")
    if row.get("regulatory_evasion_intent") is True or operation == "BYPASS_STATUTORY_RECONCILIATION":
        raise ScopeRuleError("REGULATORY_EVASION_STOP", "regulatory or statutory bypass intent stops processing")
    if operation == "CREATE_PARALLEL_LEDGER":
        raise ScopeRuleError("PARALLEL_LEDGER_FORBIDDEN", "a derived view cannot become a second ledger")
    if operation == "MUTATE_SOURCE_FOR_VIEW":
        raise ScopeRuleError("SOURCE_MUTATION_FORBIDDEN", "view generation cannot mutate the legal ledger")
    if operation != "READ_DERIVED_VIEW":
        raise ScopeRuleError("VIEW_OPERATION_INVALID", "unsupported view operation")
    view_id = _text(row.get("view_id"), "view_id")
    view = next((item for item in checked["views"] if item["view_id"] == view_id), None)
    if view is None:
        raise ScopeRuleError("VIEW_UNKNOWN", "unknown view requires policy review")
    if row.get("rule_version") != view["rule_version"]:
        raise ScopeRuleError("VIEW_RULE_VERSION_REQUIRED", "the exact registered rule version is required")
    return {
        "schema_version": "kmfa.v015.s09p1.view_boundary_decision.v1",
        "operation": operation,
        "view_id": view_id,
        "decision": "ALLOWED_READ_ONLY_DERIVED_VIEW",
        "legal_ledger_ref": checked["legal_ledger_ref"],
        "rule_version": view["rule_version"],
        "independent_ledger_created": False,
        "source_value_mutation_performed": False,
        "regulatory_bypass_performed": False,
    }


def default_difference_dictionary() -> dict[str, Any]:
    """Return the eight required, human-readable difference types."""

    rows = [
        ("UNBILLED", "未开票", "TIMING_ONLY", "NORMAL", ("CONTRACT_OR_DELIVERY", "PERIOD_BASIS"), ("OPERATING_ANALYSIS", "PROJECT_REALITY", "TAX_POLICY"), "说明已履约但尚未开票的期间差异。"),
        ("UNSETTLED", "未结算", "CONTEXT_DEPENDENT", "NORMAL", ("CONTRACT_PROGRESS", "SETTLEMENT_STATUS"), ("OPERATING_ANALYSIS", "PROJECT_REALITY"), "说明合同进度与结算确认之间的差异。"),
        ("UNALLOCATED", "未归集", "INCREASE_DERIVED_VIEW", "NORMAL", ("SOURCE_RECORD", "ALLOCATION_BASIS"), ("OPERATING_ANALYSIS", "PROJECT_REALITY"), "未取得可靠归集依据时保持待确认。"),
        ("ADVANCE_PAID", "垫付", "CONTEXT_DEPENDENT", "NORMAL", ("PAYMENT_EVIDENCE", "RESPONSIBLE_PARTY"), ("PROJECT_REALITY", "FUNDS"), "说明垫付主体、责任方和资金影响。"),
        ("RETENTION", "质保金", "TIMING_ONLY", "NORMAL", ("CONTRACT_TERM", "RETENTION_STATUS"), ("OPERATING_ANALYSIS", "PROJECT_REALITY", "FUNDS"), "说明质保条款、到期时间和收付状态。"),
        ("CROSS_PERIOD", "跨期", "CONTEXT_DEPENDENT", "HIGH", ("OCCURRENCE_DATE", "ACCOUNTING_PERIOD", "BUSINESS_PERIOD_BASIS"), ("STATUTORY_ACCOUNTING", "OPERATING_ANALYSIS", "PROJECT_REALITY", "TAX_POLICY"), "跨期处理必须说明法定期间与经营期间，不得规避监管。"),
        ("TAX_RATE", "税率差异", "CONTEXT_DEPENDENT", "HIGH", ("TAX_EVIDENCE", "APPLICABLE_RULE_VERSION"), ("STATUTORY_ACCOUNTING", "OPERATING_ANALYSIS", "TAX_POLICY"), "税率差异只作复核提示，不替代申报判断。"),
        ("BAD_DEBT", "坏账", "DECREASE_DERIVED_VIEW", "HIGH", ("RECEIVABLE_EVIDENCE", "RECOVERY_ASSESSMENT", "APPROVAL_BASIS"), ("OPERATING_ANALYSIS", "PROJECT_REALITY", "FUNDS"), "坏账调整必须取得高风险审批并保留撤销路径。"),
    ]
    types = []
    for code, label, direction, risk, evidence, impacts, handling in rows:
        types.append(
            {
                "difference_type_code": code,
                "label_zh": label,
                "direction": direction,
                "risk_level": risk,
                "required_evidence_codes": list(evidence),
                "affected_view_ids": list(impacts),
                "handling_rule_zh": handling,
                "report_display_rule_zh": "经营报告只显示影响经营判断的中文摘要；证据不足时明确显示需要确认。",
                "unknown_or_incomplete_requires_confirmation": True,
                "silent_offset_allowed": False,
            }
        )
    return {
        "schema_version": "kmfa.v015.s09p1.difference_dictionary.v1",
        "dictionary_ref": "DIFFERENCE-DICTIONARY-S09P1-V1",
        "dictionary_version": "1.0.0",
        "unknown_type_route": "MANUAL_CONFIRMATION",
        "silent_offset_allowed": False,
        "types": types,
    }


def validate_difference_dictionary(dictionary: Mapping[str, Any]) -> dict[str, Any]:
    """Validate type coverage plus direction, evidence, handling, and display rules."""

    value = _mapping(dictionary, "dictionary")
    if value.get("schema_version") != "kmfa.v015.s09p1.difference_dictionary.v1":
        raise ScopeRuleError("DIFFERENCE_DICTIONARY_SCHEMA_INVALID", "unexpected difference dictionary schema")
    _text(value.get("dictionary_ref"), "dictionary_ref")
    _text(value.get("dictionary_version"), "dictionary_version")
    if value.get("unknown_type_route") != "MANUAL_CONFIRMATION":
        raise ScopeRuleError("UNKNOWN_TYPE_ROUTE_INVALID", "unknown types must route to manual confirmation")
    if value.get("silent_offset_allowed") is not False:
        raise ScopeRuleError("SILENT_OFFSET_FORBIDDEN", "differences may not be silently netted")
    rows = value.get("types")
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ScopeRuleError("DIFFERENCE_TYPES_REQUIRED", "difference types must be a sequence")
    checked: list[dict[str, Any]] = []
    for index, raw in enumerate(rows, start=1):
        row = _mapping(raw, f"types[{index}]")
        code = _text(row.get("difference_type_code"), f"types[{index}].difference_type_code")
        _text(row.get("label_zh"), f"types[{index}].label_zh")
        if row.get("direction") not in DIFFERENCE_DIRECTIONS:
            raise ScopeRuleError("DIFFERENCE_DIRECTION_INVALID", f"{code} direction is invalid")
        if row.get("risk_level") not in RISK_LEVELS:
            raise ScopeRuleError("DIFFERENCE_RISK_INVALID", f"{code} risk level is invalid")
        evidence = _text_list(row.get("required_evidence_codes"), f"types[{index}].required_evidence_codes")
        impacts = _text_list(row.get("affected_view_ids"), f"types[{index}].affected_view_ids")
        if not evidence or not impacts or not set(impacts).issubset(VIEW_IDS):
            raise ScopeRuleError("DIFFERENCE_REQUIREMENTS_INVALID", f"{code} evidence or view impact is invalid")
        _text(row.get("handling_rule_zh"), f"types[{index}].handling_rule_zh")
        _text(row.get("report_display_rule_zh"), f"types[{index}].report_display_rule_zh")
        if row.get("unknown_or_incomplete_requires_confirmation") is not True:
            raise ScopeRuleError("CONFIRMATION_GATE_REQUIRED", f"{code} must fail closed when evidence is incomplete")
        if row.get("silent_offset_allowed") is not False:
            raise ScopeRuleError("SILENT_OFFSET_FORBIDDEN", f"{code} may not be silently netted")
        checked.append(row)
    codes = [row["difference_type_code"] for row in checked]
    if len(codes) != len(set(codes)) or set(codes) != set(DIFFERENCE_TYPE_CODES):
        raise ScopeRuleError("DIFFERENCE_TYPE_SET_INVALID", "the eight required difference types must appear exactly once")
    value["types"] = checked
    return value


def classify_difference(
    *,
    difference_type_code: str,
    amount_delta_cents: int,
    evidence_codes: Sequence[str],
    dictionary: Mapping[str, Any],
) -> dict[str, Any]:
    """Classify a difference and fail closed for unknown or incomplete evidence."""

    checked = validate_difference_dictionary(dictionary)
    code = _text(difference_type_code, "difference_type_code")
    amount = _integer_cents(amount_delta_cents, "amount_delta_cents")
    supplied = _text_list(evidence_codes, "evidence_codes")
    rule = next((item for item in checked["types"] if item["difference_type_code"] == code), None)
    if rule is None:
        return {
            "schema_version": "kmfa.v015.s09p1.difference_classification.v1",
            "difference_type_code": code,
            "synthetic_amount_delta_cents": amount,
            "state": "UNKNOWN_REQUIRES_CONFIRMATION",
            "manual_confirmation_required": True,
            "adjustment_event_allowed": False,
            "silent_offset_allowed": False,
            "missing_evidence_codes": [],
        }
    missing = sorted(set(rule["required_evidence_codes"]) - set(supplied))
    if missing:
        state = "EVIDENCE_INCOMPLETE_REQUIRES_CONFIRMATION"
        event_allowed = False
    elif rule["risk_level"] == "HIGH":
        state = "KNOWN_HIGH_RISK_REQUIRES_APPROVAL"
        event_allowed = True
    else:
        state = "KNOWN_READY_FOR_REVIEW"
        event_allowed = True
    return {
        "schema_version": "kmfa.v015.s09p1.difference_classification.v1",
        "difference_type_code": code,
        "label_zh": rule["label_zh"],
        "synthetic_amount_delta_cents": amount,
        "direction": rule["direction"],
        "risk_level": rule["risk_level"],
        "state": state,
        "manual_confirmation_required": state != "KNOWN_READY_FOR_REVIEW",
        "adjustment_event_allowed": event_allowed,
        "silent_offset_allowed": False,
        "missing_evidence_codes": missing,
        "affected_view_ids": copy.deepcopy(rule["affected_view_ids"]),
        "handling_rule_zh": rule["handling_rule_zh"],
        "report_display_rule_zh": rule["report_display_rule_zh"],
    }


class ImmutableLegalLedger:
    """Synthetic proof object that rejects direct source-ledger updates."""

    def __init__(self, records: Sequence[Mapping[str, Any]]) -> None:
        if isinstance(records, (str, bytes)) or not isinstance(records, Sequence):
            raise ScopeRuleError("LEDGER_RECORDS_REQUIRED", "records must be a sequence")
        self._records = [copy.deepcopy(dict(row)) for row in records]

    def snapshot(self) -> list[dict[str, Any]]:
        return copy.deepcopy(self._records)

    def update_record(self, *_: Any, **__: Any) -> None:
        raise ScopeRuleError("DIRECT_LEDGER_MUTATION_FORBIDDEN", "adjustments must be append-only control events")


class AdjustmentEventLedger:
    """Append-only adjustment protocol with deterministic replay."""

    def __init__(
        self,
        *,
        dictionary: Mapping[str, Any] | None = None,
        events: Sequence[Mapping[str, Any]] = (),
    ) -> None:
        self._dictionary = validate_difference_dictionary(dictionary or default_difference_dictionary())
        self._events: list[dict[str, Any]] = []
        for event in events:
            self._append_existing(event)

    @property
    def events(self) -> list[dict[str, Any]]:
        return copy.deepcopy(self._events)

    def _next_ref(self) -> str:
        return f"CTRL-EVENT-S09P1-{len(self._events) + 1:03d}"

    def _event(self, event_ref: str) -> dict[str, Any]:
        ref = _text(event_ref, "event_ref")
        match = next((row for row in self._events if row["event_ref"] == ref), None)
        if match is None:
            raise ScopeRuleError("TARGET_EVENT_NOT_FOUND", "target event does not exist")
        return match

    def _append_existing(self, event: Mapping[str, Any]) -> None:
        row = _mapping(event, "event")
        expected_sequence = len(self._events) + 1
        expected_ref = f"CTRL-EVENT-S09P1-{expected_sequence:03d}"
        previous_ref = self._events[-1]["event_ref"] if self._events else None
        if (
            row.get("schema_version") != "kmfa.v015.s09p1.adjustment_event.v1"
            or row.get("sequence") != expected_sequence
            or row.get("event_ref") != expected_ref
            or row.get("previous_event_ref") != previous_ref
            or row.get("event_type") not in EVENT_TYPES
            or row.get("control_event_recorded") is not True
            or row.get("source_ledger_mutation_performed") is not False
            or row.get("raw_source_mutation_performed") is not False
        ):
            raise ScopeRuleError("ADJUSTMENT_EVENT_CHAIN_INVALID", "event sequence or immutable boundary is invalid")
        adjustment_ref = _text(row.get("adjustment_ref"), "event.adjustment_ref")
        difference_code = _text(row.get("difference_type_code"), "event.difference_type_code")
        if difference_code not in DIFFERENCE_TYPE_CODES:
            raise ScopeRuleError("ADJUSTMENT_DIFFERENCE_TYPE_INVALID", "adjustment requires a registered difference type")
        actor_role = _text(row.get("actor_role"), "event.actor_role")
        _text(row.get("reason_zh"), "event.reason_zh")
        _text(row.get("recorded_at"), "event.recorded_at")
        evidence = _text_list(row.get("evidence_codes"), "event.evidence_codes")
        views = _text_list(row.get("affected_view_ids"), "event.affected_view_ids")
        if not evidence or not views or not set(views).issubset(VIEW_IDS):
            raise ScopeRuleError("ADJUSTMENT_EVENT_FIELDS_INVALID", "event evidence and affected views are required")
        amount = _integer_cents(row.get("amount_delta_cents"), "event.amount_delta_cents")
        valid_from = _iso_date(row.get("valid_from"), "event.valid_from")
        valid_to = _iso_date(row.get("valid_to"), "event.valid_to")
        if valid_from > valid_to:
            raise ScopeRuleError("ADJUSTMENT_VALIDITY_INVALID", "valid_from must not be after valid_to")
        risk = row.get("risk_level")
        if risk not in RISK_LEVELS:
            raise ScopeRuleError("ADJUSTMENT_RISK_INVALID", "event risk level is invalid")
        event_type = row["event_type"]
        target_ref = row.get("target_event_ref")
        if event_type == "ADJUSTMENT_PROPOSED":
            if target_ref is not None or row.get("approval_status") != "PENDING":
                raise ScopeRuleError("ADJUSTMENT_PROPOSAL_INVALID", "proposal must start pending without a target")
            if any(item["adjustment_ref"] == adjustment_ref and item["event_type"] == event_type for item in self._events):
                raise ScopeRuleError("ADJUSTMENT_REF_DUPLICATE", "each adjustment reference may be proposed once")
        else:
            target = self._event(_text(target_ref, "event.target_event_ref"))
            if target["adjustment_ref"] != adjustment_ref:
                raise ScopeRuleError("ADJUSTMENT_TARGET_MISMATCH", "target belongs to another adjustment")
            if event_type == "ADJUSTMENT_APPROVED":
                if target["event_type"] != "ADJUSTMENT_PROPOSED" or row.get("approval_status") != "APPROVED":
                    raise ScopeRuleError("ADJUSTMENT_APPROVAL_INVALID", "approval must target its proposal")
                if actor_role not in APPROVER_ROLES:
                    raise ScopeRuleError("APPROVER_ROLE_INVALID", "approval role is not authorized")
                if risk == "HIGH" and actor_role not in HIGH_RISK_APPROVER_ROLES:
                    raise ScopeRuleError("HIGH_RISK_APPROVAL_REQUIRED", "high-risk adjustment requires finance-owner or owner approval")
            elif event_type == "ADJUSTMENT_REVERSED":
                if target["event_type"] != "ADJUSTMENT_APPROVED" or row.get("approval_status") != "REVERSED":
                    raise ScopeRuleError("ADJUSTMENT_REVERSAL_INVALID", "reversal must target an approval")
                if actor_role not in HIGH_RISK_APPROVER_ROLES:
                    raise ScopeRuleError("REVERSAL_ROLE_INVALID", "reversal requires finance-owner or owner role")
        row["evidence_codes"] = evidence
        row["affected_view_ids"] = views
        row["amount_delta_cents"] = amount
        self._events.append(row)

    def _append(
        self,
        *,
        event_type: str,
        proposal: Mapping[str, Any],
        actor_role: str,
        recorded_at: str,
        target_event_ref: str | None,
        approval_status: str,
    ) -> dict[str, Any]:
        row = {
            "schema_version": "kmfa.v015.s09p1.adjustment_event.v1",
            "event_ref": self._next_ref(),
            "sequence": len(self._events) + 1,
            "previous_event_ref": self._events[-1]["event_ref"] if self._events else None,
            "event_type": event_type,
            "adjustment_ref": proposal["adjustment_ref"],
            "difference_type_code": proposal["difference_type_code"],
            "amount_delta_cents": proposal["amount_delta_cents"],
            "affected_view_ids": copy.deepcopy(proposal["affected_view_ids"]),
            "reason_zh": proposal["reason_zh"],
            "evidence_codes": copy.deepcopy(proposal["evidence_codes"]),
            "risk_level": proposal["risk_level"],
            "valid_from": proposal["valid_from"],
            "valid_to": proposal["valid_to"],
            "actor_role": _text(actor_role, "actor_role"),
            "recorded_at": _text(recorded_at, "recorded_at"),
            "target_event_ref": target_event_ref,
            "approval_status": approval_status,
            "control_event_recorded": True,
            "source_ledger_mutation_performed": False,
            "raw_source_mutation_performed": False,
        }
        self._append_existing(row)
        return copy.deepcopy(row)

    def propose(
        self,
        *,
        adjustment_ref: str,
        difference_type_code: str,
        amount_delta_cents: int,
        affected_view_ids: Sequence[str],
        reason_zh: str,
        evidence_codes: Sequence[str],
        valid_from: str,
        valid_to: str,
        actor_role: str,
        recorded_at: str,
    ) -> dict[str, Any]:
        classification = classify_difference(
            difference_type_code=difference_type_code,
            amount_delta_cents=amount_delta_cents,
            evidence_codes=evidence_codes,
            dictionary=self._dictionary,
        )
        if classification["adjustment_event_allowed"] is not True:
            raise ScopeRuleError("ADJUSTMENT_NOT_READY", "unknown or incomplete difference cannot create an adjustment")
        requested_views = _text_list(affected_view_ids, "affected_view_ids")
        if not requested_views or not set(requested_views).issubset(classification["affected_view_ids"]):
            raise ScopeRuleError("ADJUSTMENT_VIEW_SCOPE_INVALID", "affected views must stay within the difference rule")
        proposal = {
            "adjustment_ref": _text(adjustment_ref, "adjustment_ref"),
            "difference_type_code": classification["difference_type_code"],
            "amount_delta_cents": _integer_cents(amount_delta_cents, "amount_delta_cents"),
            "affected_view_ids": requested_views,
            "reason_zh": _text(reason_zh, "reason_zh"),
            "evidence_codes": _text_list(evidence_codes, "evidence_codes"),
            "risk_level": classification["risk_level"],
            "valid_from": _iso_date(valid_from, "valid_from"),
            "valid_to": _iso_date(valid_to, "valid_to"),
        }
        if proposal["valid_from"] > proposal["valid_to"]:
            raise ScopeRuleError("ADJUSTMENT_VALIDITY_INVALID", "valid_from must not be after valid_to")
        return self._append(
            event_type="ADJUSTMENT_PROPOSED",
            proposal=proposal,
            actor_role=actor_role,
            recorded_at=recorded_at,
            target_event_ref=None,
            approval_status="PENDING",
        )

    def approve(self, *, proposal_event_ref: str, actor_role: str, recorded_at: str) -> dict[str, Any]:
        proposal = self._event(proposal_event_ref)
        if proposal["event_type"] != "ADJUSTMENT_PROPOSED":
            raise ScopeRuleError("ADJUSTMENT_APPROVAL_INVALID", "approval target must be a proposal")
        return self._append(
            event_type="ADJUSTMENT_APPROVED",
            proposal=proposal,
            actor_role=actor_role,
            recorded_at=recorded_at,
            target_event_ref=proposal_event_ref,
            approval_status="APPROVED",
        )

    def reverse(self, *, approval_event_ref: str, actor_role: str, recorded_at: str) -> dict[str, Any]:
        approval = self._event(approval_event_ref)
        if approval["event_type"] != "ADJUSTMENT_APPROVED":
            raise ScopeRuleError("ADJUSTMENT_REVERSAL_INVALID", "reversal target must be an approval")
        return self._append(
            event_type="ADJUSTMENT_REVERSED",
            proposal=approval,
            actor_role=actor_role,
            recorded_at=recorded_at,
            target_event_ref=approval_event_ref,
            approval_status="REVERSED",
        )

    def effective_adjustment(self, *, adjustment_ref: str, on_date: str) -> dict[str, Any]:
        ref = _text(adjustment_ref, "adjustment_ref")
        day = _iso_date(on_date, "on_date")
        events = [row for row in self._events if row["adjustment_ref"] == ref]
        proposal = next((row for row in events if row["event_type"] == "ADJUSTMENT_PROPOSED"), None)
        if proposal is None:
            raise ScopeRuleError("ADJUSTMENT_NOT_FOUND", "adjustment does not exist")
        approvals = [row for row in events if row["event_type"] == "ADJUSTMENT_APPROVED"]
        if not approvals:
            status = "PENDING_APPROVAL"
            effective = False
        else:
            latest_approval = approvals[-1]
            reversed_refs = {
                row["target_event_ref"] for row in events if row["event_type"] == "ADJUSTMENT_REVERSED"
            }
            if latest_approval["event_ref"] in reversed_refs:
                status = "REVERSED"
                effective = False
            elif not proposal["valid_from"] <= day <= proposal["valid_to"]:
                status = "OUTSIDE_VALIDITY"
                effective = False
            else:
                status = "ACTIVE"
                effective = True
        return {
            "schema_version": "kmfa.v015.s09p1.adjustment_effective_state.v1",
            "adjustment_ref": ref,
            "on_date": day,
            "status": status,
            "effective": effective,
            "effective_amount_delta_cents": proposal["amount_delta_cents"] if effective else 0,
            "source_ledger_mutation_performed": False,
            "raw_source_mutation_performed": False,
        }

    def to_jsonl(self) -> str:
        return "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in self._events)


def synthetic_acceptance_cases() -> dict[str, Any]:
    """Execute deterministic public-safe acceptance cases for all three tasks."""

    policy = validate_ledger_view_policy(default_ledger_view_policy())
    boundary_results = [
        evaluate_view_boundary(
            {"operation": "READ_DERIVED_VIEW", "view_id": view["view_id"], "rule_version": view["rule_version"]},
            policy,
        )
        for view in policy["views"]
    ]
    negative_boundary_codes: list[str] = []
    for request in (
        {"operation": "CREATE_PARALLEL_LEDGER"},
        {"operation": "BYPASS_STATUTORY_RECONCILIATION"},
        {"operation": "READ_DERIVED_VIEW", "view_id": "OPERATING_ANALYSIS", "rule_version": "SCOPE-RULE-V1", "regulatory_evasion_intent": True},
        {"operation": "MUTATE_SOURCE_FOR_VIEW"},
    ):
        try:
            evaluate_view_boundary(request, policy)
        except ScopeRuleError as error:
            negative_boundary_codes.append(error.code)

    dictionary = validate_difference_dictionary(default_difference_dictionary())
    classification_results = []
    for index, rule in enumerate(dictionary["types"], start=1):
        classification_results.append(
            classify_difference(
                difference_type_code=rule["difference_type_code"],
                amount_delta_cents=index * 100,
                evidence_codes=rule["required_evidence_codes"],
                dictionary=dictionary,
            )
        )
    unknown = classify_difference(
        difference_type_code="NEW_UNREGISTERED_TYPE",
        amount_delta_cents=900,
        evidence_codes=("REVIEW_NOTE",),
        dictionary=dictionary,
    )
    incomplete = classify_difference(
        difference_type_code="BAD_DEBT",
        amount_delta_cents=-300,
        evidence_codes=("RECEIVABLE_EVIDENCE",),
        dictionary=dictionary,
    )
    float_rejected = False
    try:
        classify_difference(
            difference_type_code="UNBILLED",
            amount_delta_cents=json.loads("1.5"),  # type: ignore[arg-type]
            evidence_codes=("CONTRACT_OR_DELIVERY", "PERIOD_BASIS"),
            dictionary=dictionary,
        )
    except ScopeRuleError as error:
        float_rejected = error.code == "INTEGER_CENTS_REQUIRED"

    legal_ledger = ImmutableLegalLedger(
        ({"record_ref": "SYNTHETIC-LEDGER-001", "amount_cents": 10000, "period_ref": "SYNTHETIC-PERIOD"},)
    )
    source_before = legal_ledger.snapshot()
    direct_mutation_rejected = False
    try:
        legal_ledger.update_record("SYNTHETIC-LEDGER-001", amount_cents=11000)
    except ScopeRuleError as error:
        direct_mutation_rejected = error.code == "DIRECT_LEDGER_MUTATION_FORBIDDEN"

    ledger = AdjustmentEventLedger(dictionary=dictionary)
    normal_proposal = ledger.propose(
        adjustment_ref="ADJ-SYN-001",
        difference_type_code="UNBILLED",
        amount_delta_cents=12500,
        affected_view_ids=("OPERATING_ANALYSIS", "PROJECT_REALITY"),
        reason_zh="模拟履约事项已确认但尚未开票，仅用于验证调整协议。",
        evidence_codes=("CONTRACT_OR_DELIVERY", "PERIOD_BASIS"),
        valid_from="2026-01-01",
        valid_to="2026-12-31",
        actor_role="ANALYST",
        recorded_at="2026-07-15T17:00:00+10:00",
    )
    normal_before_approval = ledger.effective_adjustment(adjustment_ref="ADJ-SYN-001", on_date="2026-07-15")
    normal_approval = ledger.approve(
        proposal_event_ref=normal_proposal["event_ref"],
        actor_role="FINANCE_REVIEWER",
        recorded_at="2026-07-15T17:01:00+10:00",
    )
    normal_active = ledger.effective_adjustment(adjustment_ref="ADJ-SYN-001", on_date="2026-07-15")
    ledger.reverse(
        approval_event_ref=normal_approval["event_ref"],
        actor_role="FINANCE_OWNER",
        recorded_at="2026-07-15T17:02:00+10:00",
    )
    normal_reversed = ledger.effective_adjustment(adjustment_ref="ADJ-SYN-001", on_date="2026-07-15")

    high_proposal = ledger.propose(
        adjustment_ref="ADJ-SYN-002",
        difference_type_code="BAD_DEBT",
        amount_delta_cents=-3000,
        affected_view_ids=("OPERATING_ANALYSIS", "PROJECT_REALITY", "FUNDS"),
        reason_zh="模拟坏账风险用于验证高风险审批，不代表真实经营判断。",
        evidence_codes=("RECEIVABLE_EVIDENCE", "RECOVERY_ASSESSMENT", "APPROVAL_BASIS"),
        valid_from="2026-01-01",
        valid_to="2026-12-31",
        actor_role="ANALYST",
        recorded_at="2026-07-15T17:03:00+10:00",
    )
    high_before_approval = ledger.effective_adjustment(adjustment_ref="ADJ-SYN-002", on_date="2026-07-15")
    high_risk_unauthorized_rejected = False
    try:
        ledger.approve(
            proposal_event_ref=high_proposal["event_ref"],
            actor_role="FINANCE_REVIEWER",
            recorded_at="2026-07-15T17:04:00+10:00",
        )
    except ScopeRuleError as error:
        high_risk_unauthorized_rejected = error.code == "HIGH_RISK_APPROVAL_REQUIRED"
    high_approval = ledger.approve(
        proposal_event_ref=high_proposal["event_ref"],
        actor_role="FINANCE_OWNER",
        recorded_at="2026-07-15T17:05:00+10:00",
    )
    high_active = ledger.effective_adjustment(adjustment_ref="ADJ-SYN-002", on_date="2026-07-15")
    high_expired = ledger.effective_adjustment(adjustment_ref="ADJ-SYN-002", on_date="2027-01-01")

    replayed = AdjustmentEventLedger(dictionary=dictionary, events=ledger.events)
    return {
        "schema_version": SCHEMA_VERSION,
        "synthetic_fixture": True,
        "ledger_view_policy": policy,
        "boundary_results": boundary_results,
        "negative_boundary_codes": negative_boundary_codes,
        "difference_dictionary": dictionary,
        "difference_classification_results": classification_results,
        "unknown_difference_result": unknown,
        "incomplete_difference_result": incomplete,
        "float_money_rejected": float_rejected,
        "adjustment_events": ledger.events,
        "adjustment_event_roundtrip_exact": replayed.events == ledger.events,
        "normal_before_approval": normal_before_approval,
        "normal_active": normal_active,
        "normal_reversed": normal_reversed,
        "high_before_approval": high_before_approval,
        "high_risk_unauthorized_rejected": high_risk_unauthorized_rejected,
        "high_approval_event_ref": high_approval["event_ref"],
        "high_active": high_active,
        "high_expired": high_expired,
        "direct_ledger_mutation_rejected": direct_mutation_rejected,
        "source_snapshot_unchanged": legal_ledger.snapshot() == source_before,
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
    }
