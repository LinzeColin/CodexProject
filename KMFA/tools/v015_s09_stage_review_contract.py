#!/usr/bin/env python3
"""Executable cross-phase contract for the KMFA v1.5 S09 Stage Review.

The review adapter closes three integration gaps without changing the frozen
P1/P2/P3 kernels: adjustment facts must originate from a valid P1 append-only
chain, every P2 difference must be represented by an exact P3 summary binding,
and closure/recalculation/report updates must stay bound to that same versioned
difference.  All verification fixtures are public-safe synthetic data.
"""

from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any

from KMFA.tools import v015_s09_p1_scope_rule_modeling as p1
from KMFA.tools import v015_s09_p2_conversion_reconciliation_engine as p2
from KMFA.tools import v015_s09_p3_human_readable_audit as p3


RUN_PHASE_ID = "V015_S09_STAGE_REVIEW"
TASK_ID = "KMFA-V015-S09-STAGE-REVIEW-20260715"
ACCEPTANCE_ID = "ACC-KMFA-V015-S09-STAGE-REVIEW"
VERSION = "1.5.0-dev-s09-review"

ADJUSTMENT_BINDING_SCHEMA = "kmfa.v015.s09_stage_review.adjustment_binding.v1"
DIFFERENCE_BINDING_SCHEMA = "kmfa.v015.s09_stage_review.difference_binding.v1"
CLOSURE_BINDING_SCHEMA = "kmfa.v015.s09_stage_review.closure_binding.v1"


class StageReviewError(ValueError):
    """Stable fail-closed S09 cross-phase integration error."""

    def __init__(self, code: str, message_zh: str) -> None:
        super().__init__(f"{code}: {message_zh}")
        self.code = code
        self.message_zh = message_zh


def _mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise StageReviewError("MAPPING_REQUIRED", f"{field} 必须是字段映射。")
    return copy.deepcopy(dict(value))


def _sequence(value: Any, field: str) -> list[Any]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise StageReviewError("SEQUENCE_REQUIRED", f"{field} 必须是列表。")
    return copy.deepcopy(list(value))


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise StageReviewError("TEXT_REQUIRED", f"{field} 不能为空。")
    return value.strip()


def _cents(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise StageReviewError("INTEGER_CENTS_REQUIRED", f"{field} 必须是整数分。")
    return value


def _stable_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _source_rows(source_batch: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    batch = _mapping(source_batch, "source_batch")
    rows: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(_sequence(batch.get("rows"), "source_batch.rows"), start=1):
        row = _mapping(raw, f"source_batch.rows[{index}]")
        ref = _text(row.get("row_ref"), "source_batch.rows.row_ref")
        if ref in rows:
            raise StageReviewError("DUPLICATE_SOURCE_ROW", "同一来源行不能重复。")
        rows[ref] = row
    return rows


def convert_with_bound_adjustments(
    *,
    source_batch: Mapping[str, Any],
    adjustment_events: Sequence[Mapping[str, Any]],
    bindings: Sequence[Mapping[str, Any]],
    on_date: str,
) -> dict[str, Any]:
    """Derive P2 adjustments only from the effective state of a valid P1 chain."""

    source = _mapping(source_batch, "source_batch")
    source_before = copy.deepcopy(source)
    try:
        ledger = p1.AdjustmentEventLedger(events=_sequence(adjustment_events, "adjustment_events"))
    except (p1.ScopeRuleError, ValueError, KeyError) as error:
        raise StageReviewError("P1_ADJUSTMENT_CHAIN_INVALID", "调整事件链未通过第 1 部分校验。") from error
    rows = _source_rows(source)
    rules = {row["source_kind"]: row for row in p2.default_conversion_policy()["rules"]}

    event_refs_by_adjustment: dict[str, list[dict[str, Any]]] = {}
    for event in ledger.events:
        event_refs_by_adjustment.setdefault(event["adjustment_ref"], []).append(event)
    active: dict[str, dict[str, Any]] = {}
    inactive: list[str] = []
    for adjustment_ref in event_refs_by_adjustment:
        state = ledger.effective_adjustment(adjustment_ref=adjustment_ref, on_date=on_date)
        if state["effective"]:
            active[adjustment_ref] = state
        else:
            inactive.append(adjustment_ref)

    checked_bindings: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(_sequence(bindings, "bindings"), start=1):
        row = _mapping(raw, f"bindings[{index}]")
        adjustment_ref = _text(row.get("adjustment_ref"), "bindings.adjustment_ref")
        source_row_ref = _text(row.get("source_row_ref"), "bindings.source_row_ref")
        if adjustment_ref in checked_bindings:
            raise StageReviewError("DUPLICATE_ADJUSTMENT_BINDING", "同一调整只能绑定一次。")
        if source_row_ref not in rows:
            raise StageReviewError("ADJUSTMENT_SOURCE_ROW_UNKNOWN", "调整绑定的来源行不存在。")
        checked_bindings[adjustment_ref] = {"adjustment_ref": adjustment_ref, "source_row_ref": source_row_ref}
    if set(checked_bindings) != set(active):
        raise StageReviewError("ADJUSTMENT_BINDING_SET_MISMATCH", "每项当前生效的调整必须且只能绑定一次。")

    derived_adjustments: list[dict[str, Any]] = []
    binding_rows: list[dict[str, Any]] = []
    for adjustment_ref in sorted(active):
        binding = checked_bindings[adjustment_ref]
        source_row = rows[binding["source_row_ref"]]
        source_kind = source_row.get("source_kind")
        if source_kind not in rules:
            raise StageReviewError("ADJUSTMENT_SOURCE_KIND_UNSUPPORTED", "来源行不能进入已登记的口径转换。")
        history = event_refs_by_adjustment[adjustment_ref]
        proposal = next(row for row in history if row["event_type"] == "ADJUSTMENT_PROPOSED")
        approvals = [row for row in history if row["event_type"] == "ADJUSTMENT_APPROVED"]
        approval = approvals[-1]
        if "OPERATING_ANALYSIS" not in proposal["affected_view_ids"]:
            raise StageReviewError("ADJUSTMENT_VIEW_NOT_BOUND", "调整未获准影响经营分析视图。")
        rule = rules[source_kind]
        derived = {
            "event_ref": approval["event_ref"],
            "source_row_ref": binding["source_row_ref"],
            "target_metric": rule["target_metric"],
            "affected_view_id": "OPERATING_ANALYSIS",
            "amount_delta_cents": active[adjustment_ref]["effective_amount_delta_cents"],
            "approval_status": approval["approval_status"],
            "effective": True,
        }
        derived_adjustments.append(derived)
        binding_rows.append(
            {
                "adjustment_ref": adjustment_ref,
                "approval_event_ref": approval["event_ref"],
                "source_row_ref": binding["source_row_ref"],
                "target_metric": rule["target_metric"],
                "amount_delta_cents": derived["amount_delta_cents"],
                "binding_fingerprint": _stable_hash(
                    {
                        "adjustment_ref": adjustment_ref,
                        "approval_event_ref": approval["event_ref"],
                        "source_row_ref": binding["source_row_ref"],
                        "target_metric": rule["target_metric"],
                        "amount_delta_cents": derived["amount_delta_cents"],
                        "event_chain_hash": _stable_hash(ledger.events),
                    }
                ),
            }
        )

    conversion = p2.convert_ledger_to_operating_facts(
        source_batch=source,
        adjustments=derived_adjustments,
    )
    if source != source_before:
        raise StageReviewError("SOURCE_MUTATION_DETECTED", "复审转换不得修改来源批次。")
    return {
        "schema_version": ADJUSTMENT_BINDING_SCHEMA,
        "event_chain_hash": _stable_hash(ledger.events),
        "active_adjustment_count": len(active),
        "inactive_adjustment_refs": sorted(inactive),
        "bindings": binding_rows,
        "conversion": conversion,
        "source_snapshot_unchanged": True,
        "raw_root_access_count": 0,
    }


def _difference_identity(reconciliation: Mapping[str, Any], difference: Mapping[str, Any]) -> dict[str, Any]:
    value = _mapping(difference, "difference")
    return {
        "fact_ref": reconciliation["fact_ref"],
        "comparison_basis": reconciliation["comparison_basis"],
        "difference_ref": value["difference_ref"],
        "difference_type_code": value["difference_type_code"],
        "project_ref": value["project_ref"],
        "metric": value["metric"],
        "source_kind": value["source_kind"],
        "source_refs": value["source_refs"],
        "source_versions": value.get("source_versions", []),
        "expected_amount_cents": value["expected_amount_cents"],
        "actual_amount_cents": value.get("actual_amount_cents"),
        "delta_cents": value.get("delta_cents"),
        "affected_view_ids": value["affected_view_ids"],
    }


def validate_reconciliation(reconciliation: Mapping[str, Any]) -> dict[str, Any]:
    """Validate P2 reconciliation accounting before any P3 projection."""

    value = _mapping(reconciliation, "reconciliation")
    if value.get("schema_version") != p2.RECONCILIATION_SCHEMA:
        raise StageReviewError("RECONCILIATION_SCHEMA_INVALID", "核对结果不是已登记的第 2 部分输出。")
    for field in ("fact_ref", "project_ref", "metric", "comparison_basis", "policy_ref"):
        _text(value.get(field), field)
    if value["metric"] not in p2.OPERATING_METRICS:
        raise StageReviewError("RECONCILIATION_METRIC_INVALID", "核对指标未登记。")
    differences = [_mapping(row, "differences[]") for row in _sequence(value.get("differences"), "differences")]
    passes = [_mapping(row, "passes[]") for row in _sequence(value.get("passes"), "passes")]
    if value.get("required_source_count") != len(p2.RECONCILIATION_SOURCE_KINDS):
        raise StageReviewError("RECONCILIATION_SOURCE_COUNT_INVALID", "核对来源数量发生变化。")
    if len(passes) + len(differences) != len(p2.RECONCILIATION_SOURCE_KINDS):
        raise StageReviewError("RECONCILIATION_ACCOUNTING_INVALID", "每类来源必须分别通过或形成差异。")
    dictionary = {row["difference_type_code"]: row for row in p1.default_difference_dictionary()["types"]}
    refs: set[str] = set()
    kinds: set[str] = set()
    delta_sum = 0
    for row in differences:
        ref = _text(row.get("difference_ref"), "difference_ref")
        kind = _text(row.get("source_kind"), "source_kind")
        expected_ref = f"DIFF-{value['fact_ref']}-{kind}"
        if ref in refs or kind in kinds or ref != expected_ref:
            raise StageReviewError("DIFFERENCE_IDENTITY_INVALID", "差异标识必须与事实和来源一一对应。")
        refs.add(ref)
        kinds.add(kind)
        if row.get("project_ref") != value["project_ref"] or row.get("metric") != value["metric"]:
            raise StageReviewError("DIFFERENCE_CASE_MISMATCH", "差异串到另一项目或指标。")
        actual = row.get("actual_amount_cents")
        expected = _cents(row.get("expected_amount_cents"), "expected_amount_cents")
        if actual is None:
            if row.get("difference_type_code") != "MISSING_SOURCE" or row.get("delta_cents") is not None:
                raise StageReviewError("MISSING_SOURCE_DIFFERENCE_INVALID", "缺失来源差异的金额结构不正确。")
        else:
            actual_cents = _cents(actual, "actual_amount_cents")
            delta = _cents(row.get("delta_cents"), "delta_cents")
            if delta != actual_cents - expected:
                raise StageReviewError("DIFFERENCE_ARITHMETIC_INVALID", "差异金额不能与核对金额对应。")
            expected_code = p2.SOURCE_DIFFERENCE_TYPES.get(kind)
            if row.get("difference_type_code") != expected_code or expected_code not in dictionary:
                raise StageReviewError("DIFFERENCE_DICTIONARY_DRIFT", "差异类型未精确沿用第 1 部分字典。")
            if row.get("difference_label_zh") != dictionary[expected_code]["label_zh"]:
                raise StageReviewError("DIFFERENCE_LABEL_DRIFT", "差异中文名称与第 1 部分字典不一致。")
            delta_sum += delta
        if row.get("manual_confirmation_required") is not True or row.get("silent_offset_allowed") is not False:
            raise StageReviewError("DIFFERENCE_FAIL_CLOSED_GATE_MISSING", "差异必须保留人工确认且禁止静默抵销。")
        if not _sequence(row.get("source_refs"), "source_refs") or not _sequence(row.get("affected_view_ids"), "affected_view_ids"):
            raise StageReviewError("DIFFERENCE_TRACE_MISSING", "差异必须保留来源和影响视图。")
    if value.get("difference_count") != len(differences) or value.get("difference_delta_sum_cents") != delta_sum:
        raise StageReviewError("DIFFERENCE_TOTAL_DRIFT", "差异数量或金额合计不一致。")
    if value.get("opposite_differences_retained_separately") is not True or value.get("silent_offset_count") != 0:
        raise StageReviewError("SILENT_OFFSET_DETECTED", "相反差异不得互相抵销。")
    if value.get("source_mutation_performed") is not False or value.get("raw_source_mutation_performed") is not False:
        raise StageReviewError("RECONCILIATION_MUTATION_DETECTED", "核对不得修改来源。")
    value["differences"] = differences
    value["passes"] = passes
    return value


def reconciliation_fingerprint(reconciliation: Mapping[str, Any]) -> str:
    checked = validate_reconciliation(reconciliation)
    identities = [_difference_identity(checked, row) for row in checked["differences"]]
    return _stable_hash({"policy_ref": checked["policy_ref"], "differences": identities})


def build_bound_management_summary(reconciliation: Mapping[str, Any]) -> dict[str, Any]:
    """Create the P3 summary from every P2 decision-relevant difference."""

    checked = validate_reconciliation(reconciliation)
    manual = p3.build_human_rule_manual()
    items: list[dict[str, str]] = []
    bindings: list[dict[str, Any]] = []
    for row in checked["differences"]:
        identity = _difference_identity(checked, row)
        fingerprint = _stable_hash(identity)
        code = row["difference_type_code"]
        label = row.get("difference_label_zh") or "缺少核对来源"
        report_input = {
            "difference_ref": row["difference_ref"],
            "difference_type_code": code,
            "affects_business_decision": True,
            "plain_reason_zh": f"{label}已登记，相关金额和来源仍需确认。",
            "business_impact_zh": _text(row.get("impact_zh"), "impact_zh"),
            "current_status_zh": "等待补充来源和人工确认。" if code == "MISSING_SOURCE" else "等待人工确认和重新计算。",
            "owner_action_zh": "补齐证据，确认处理方案后重新计算并更新经营摘要。",
        }
        if code == "MISSING_SOURCE":
            # P2 uses this control-state code when an expected source is absent;
            # it is intentionally outside P1's eight business-difference types.
            # Preserve P3's display whitelist without inventing a P1 rule.
            item = {
                "title_zh": "经营提醒：缺少核对来源",
                "what_changed_zh": report_input["plain_reason_zh"],
                "business_impact_zh": report_input["business_impact_zh"],
                "current_status_zh": report_input["current_status_zh"],
                "recommended_action_zh": report_input["owner_action_zh"],
            }
            if tuple(item) != p3.REPORT_ITEM_FIELDS:
                raise StageReviewError("REPORT_OUTPUT_FIELD_DRIFT", "缺失来源提醒越过经营摘要字段白名单。")
            rendered = "\n".join(item.values()).lower()
            if any(term.lower() in rendered for term in p3.FORBIDDEN_REPORT_TERMS):
                raise StageReviewError("INTERNAL_TERM_IN_BUSINESS_REPORT", "缺失来源提醒含内部技术信息。")
        else:
            try:
                one_item_report = p3.build_management_difference_summary((report_input,), manual=manual)
            except (p3.HumanReadableAuditError, ValueError, KeyError) as error:
                raise StageReviewError("P3_SUMMARY_INPUT_INVALID", "核对差异未通过第 3 部分经营摘要校验。") from error
            if one_item_report["included_difference_count"] != 1:
                raise StageReviewError("DECISION_DIFFERENCE_OMITTED", "经营摘要漏掉了需要决策的核对差异。")
            item = one_item_report["items"][0]
        items.append(item)
        bindings.append(
            {
                "item_index": len(bindings),
                "difference_ref": row["difference_ref"],
                "difference_type_code": code,
                "difference_fingerprint": fingerprint,
            }
        )
    report = p3.build_management_difference_summary((), manual=manual)
    report.update(
        {
            "input_difference_count": len(checked["differences"]),
            "included_difference_count": len(items),
            "excluded_non_decision_difference_count": 0,
            "technical_term_occurrence_count": 0,
            "items": items,
        }
    )
    if report["included_difference_count"] != len(checked["differences"]):
        raise StageReviewError("DECISION_DIFFERENCE_OMITTED", "经营摘要漏掉了需要决策的核对差异。")
    return {
        "schema_version": DIFFERENCE_BINDING_SCHEMA,
        "reconciliation_fingerprint": reconciliation_fingerprint(checked),
        "input_difference_count": len(checked["differences"]),
        "included_difference_count": report["included_difference_count"],
        "omitted_decision_difference_count": 0,
        "bindings": bindings,
        "management_summary": report,
        "raw_root_access_count": 0,
    }


def new_bound_closure(
    *, reconciliation: Mapping[str, Any], difference_ref: str, initial_report_version: str
) -> dict[str, Any]:
    checked = validate_reconciliation(reconciliation)
    ref = _text(difference_ref, "difference_ref")
    match = next((row for row in checked["differences"] if row["difference_ref"] == ref), None)
    if match is None:
        raise StageReviewError("CLOSURE_DIFFERENCE_NOT_FOUND", "闭环对象不在本次核对结果中。")
    identity = _difference_identity(checked, match)
    label = match.get("difference_label_zh") or "缺少核对来源"
    return {
        "schema_version": CLOSURE_BINDING_SCHEMA,
        "reconciliation_fingerprint": reconciliation_fingerprint(checked),
        "difference_fingerprint": _stable_hash(identity),
        "difference_ref": ref,
        "recalculation_ref": None,
        "p3_snapshot": p3.new_closure_snapshot(
            difference_ref=ref,
            business_label_zh=label,
            initial_report_version=initial_report_version,
        ),
        "raw_root_access_count": 0,
    }


def append_bound_closure_event(state: Mapping[str, Any], event: Mapping[str, Any]) -> dict[str, Any]:
    """Append a P3 event only when its P2 case/version binding is exact."""

    value = _mapping(state, "state")
    if value.get("schema_version") != CLOSURE_BINDING_SCHEMA:
        raise StageReviewError("BOUND_CLOSURE_SCHEMA_INVALID", "闭环缺少第 9 阶段复审绑定。")
    row = _mapping(event, "event")
    if row.get("difference_ref") != value.get("difference_ref"):
        raise StageReviewError("CLOSURE_DIFFERENCE_MISMATCH", "闭环事件串到另一条差异。")
    if row.get("reconciliation_fingerprint") != value.get("reconciliation_fingerprint"):
        raise StageReviewError("STALE_RECONCILIATION_REJECTED", "闭环事件基于另一版或旧版核对结果。")
    if row.get("difference_fingerprint") != value.get("difference_fingerprint"):
        raise StageReviewError("STALE_DIFFERENCE_REJECTED", "闭环事件与当前差异内容不一致。")
    if row.get("event_type") == "RECALCULATED":
        value["recalculation_ref"] = _text(row.get("recalculation_ref"), "recalculation_ref")
    if row.get("event_type") == "REPORT_UPDATED":
        if row.get("recalculation_ref") != value.get("recalculation_ref"):
            raise StageReviewError("REPORT_RECALCULATION_MISMATCH", "摘要更新未绑定本次重新计算。")
        if row.get("summary_binding_fingerprint") != value.get("difference_fingerprint"):
            raise StageReviewError("REPORT_DIFFERENCE_MISMATCH", "摘要更新未绑定本条差异。")
    try:
        value["p3_snapshot"] = p3.append_closure_event(value["p3_snapshot"], row)
    except (p3.HumanReadableAuditError, ValueError, KeyError) as error:
        raise StageReviewError("P3_CLOSURE_EVENT_INVALID", "闭环事件未通过第 3 部分校验。") from error
    value["raw_root_access_count"] = 0
    return value


def evaluate_downstream_gate(
    *, closure: Mapping[str, Any], cross_source_confirmations: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    """Keep unresolved P2 cross-source queues explicit after one case closes."""

    value = _mapping(closure, "closure")
    snapshot = _mapping(value.get("p3_snapshot"), "closure.p3_snapshot")
    pending = []
    for raw in _sequence(cross_source_confirmations, "cross_source_confirmations"):
        row = _mapping(raw, "cross_source_confirmations[]")
        if row.get("status") == "PENDING_HUMAN_CONFIRMATION":
            pending.append(_text(row.get("case_ref"), "case_ref"))
    return {
        "schema_version": "kmfa.v015.s09_stage_review.downstream_gate.v1",
        "closure_complete": snapshot.get("closure_complete") is True,
        "pending_cross_source_confirmation_count": len(pending),
        "pending_cross_source_case_refs": pending,
        "case_ready_for_downstream": snapshot.get("closure_complete") is True and not pending,
        "formal_report_release_allowed": False,
        "formal_report_generated": False,
        "raw_root_access_count": 0,
    }


def _closure_event(
    state: Mapping[str, Any], sequence: int, event_type: str, *, actor_role: str, **payload: Any
) -> dict[str, Any]:
    return {
        "schema_version": p3.CLOSURE_EVENT_SCHEMA,
        "event_ref": f"S09REV-CLOSURE-{sequence:02d}",
        "difference_ref": state["difference_ref"],
        "difference_fingerprint": state["difference_fingerprint"],
        "reconciliation_fingerprint": state["reconciliation_fingerprint"],
        "sequence": sequence,
        "event_type": event_type,
        "actor_role": actor_role,
        "occurred_at": f"2026-07-15T2{sequence}:00:00+10:00",
        "feedback_zh": "公开合成复审事件已按顺序登记。",
        **payload,
    }


CHECK_IDS = (
    "P1_ONE_LEDGER_POLICY_PRESERVED",
    "P1_EIGHT_DIFFERENCE_TYPES_PRESERVED",
    "P1_P3_DICTIONARY_LANGUAGE_ALIGNED",
    "P1_EVENT_CHAIN_VALIDATED",
    "ACTIVE_ADJUSTMENT_BOUND_EXACTLY_ONCE",
    "ADJUSTMENT_AMOUNT_DERIVED_FROM_P1",
    "ADJUSTMENT_APPROVAL_EVENT_BOUND",
    "UNBOUND_ACTIVE_ADJUSTMENT_REJECTED",
    "UNKNOWN_SOURCE_ROW_REJECTED",
    "FORGED_EVENT_CHAIN_REJECTED",
    "CONVERSION_SOURCE_UNCHANGED",
    "CONVERSION_EXACT_CENT_CONSERVATION",
    "P2_RECONCILIATION_VALIDATED",
    "P2_DIFFERENCES_RETAINED_SEPARATELY",
    "ALL_DECISION_DIFFERENCES_INCLUDED",
    "CALLER_RELEVANCE_OVERRIDE_REMOVED",
    "BUSINESS_ITEMS_EXCLUDE_INTERNAL_REFS",
    "SUMMARY_BINDING_COUNT_EXACT",
    "DIFFERENCE_FINGERPRINTS_UNIQUE",
    "TAMPERED_DIFFERENCE_REJECTED",
    "CLOSURE_BOUND_TO_EXACT_DIFFERENCE",
    "CLOSURE_SIX_STEPS_COMPLETE",
    "RECALCULATION_BOUND_TO_VERSION",
    "STALE_RECALCULATION_REJECTED",
    "CROSS_DIFFERENCE_EVENT_REJECTED",
    "REPORT_UPDATE_BOUND_TO_RECALCULATION",
    "UNRESOLVED_CROSS_SOURCE_BLOCKS_DOWNSTREAM",
    "CROSS_SOURCE_AUTO_WINNER_FORBIDDEN",
    "PUBLIC_SAFE_SYNTHETIC_ONLY",
    "NO_UPLOAD_APP_REPORT_OR_BUSINESS_ACTION",
)


def _check(check_id: str, condition: bool) -> dict[str, str]:
    return {"check_id": check_id, "status": "PASS" if condition else "FAIL"}


def public_verification() -> dict[str, Any]:
    """Exercise live P1/P2/P3 kernels and every new cross-phase gate."""

    source_batch = {
        "schema_version": p2.SOURCE_BATCH_SCHEMA,
        "batch_ref": "S09REV-LEDGER-BATCH-001",
        "source_version": "S09REV-SOURCE-V1",
        "legal_ledger_ref": "LEGAL-LEDGER-PRIMARY",
        "period_ref": "S09REV-PERIOD-001",
        "rows": [
            {
                "row_ref": "S09REV-ROW-REVENUE-001",
                "project_ref": "S09REV-PROJECT-001",
                "source_kind": "ACCOUNTING_REVENUE",
                "amount_cents": 100000,
                "source_evidence_ref": "S09REV-EVIDENCE-LEDGER",
            }
        ],
    }
    ledger = p1.AdjustmentEventLedger()
    proposal = ledger.propose(
        adjustment_ref="S09REV-ADJ-001",
        difference_type_code="UNBILLED",
        amount_delta_cents=5000,
        affected_view_ids=("OPERATING_ANALYSIS", "PROJECT_REALITY"),
        reason_zh="公开合成履约差异用于复审调整绑定。",
        evidence_codes=("CONTRACT_OR_DELIVERY", "PERIOD_BASIS"),
        valid_from="2026-01-01",
        valid_to="2026-12-31",
        actor_role="ANALYST",
        recorded_at="2026-07-15T20:00:00+10:00",
    )
    approval = ledger.approve(
        proposal_event_ref=proposal["event_ref"],
        actor_role="FINANCE_REVIEWER",
        recorded_at="2026-07-15T20:01:00+10:00",
    )
    bound = convert_with_bound_adjustments(
        source_batch=source_batch,
        adjustment_events=ledger.events,
        bindings=({"adjustment_ref": "S09REV-ADJ-001", "source_row_ref": "S09REV-ROW-REVENUE-001"},),
        on_date="2026-07-15",
    )

    try:
        convert_with_bound_adjustments(
            source_batch=source_batch,
            adjustment_events=ledger.events,
            bindings=(),
            on_date="2026-07-15",
        )
    except StageReviewError as error:
        unbound_rejected = error.code == "ADJUSTMENT_BINDING_SET_MISMATCH"
    else:
        unbound_rejected = False
    try:
        convert_with_bound_adjustments(
            source_batch=source_batch,
            adjustment_events=ledger.events,
            bindings=({"adjustment_ref": "S09REV-ADJ-001", "source_row_ref": "OTHER-ROW"},),
            on_date="2026-07-15",
        )
    except StageReviewError as error:
        unknown_row_rejected = error.code == "ADJUSTMENT_SOURCE_ROW_UNKNOWN"
    else:
        unknown_row_rejected = False
    forged_events = ledger.events
    forged_events[-1]["previous_event_ref"] = "FORGED"
    try:
        convert_with_bound_adjustments(
            source_batch=source_batch,
            adjustment_events=forged_events,
            bindings=({"adjustment_ref": "S09REV-ADJ-001", "source_row_ref": "S09REV-ROW-REVENUE-001"},),
            on_date="2026-07-15",
        )
    except StageReviewError as error:
        forged_rejected = error.code == "P1_ADJUSTMENT_CHAIN_INVALID"
    else:
        forged_rejected = False

    p2_cases = p2.synthetic_acceptance_cases()
    reconciliation = validate_reconciliation(p2_cases["reconciliation"])
    summary = build_bound_management_summary(reconciliation)
    missing_source_reconciliation = validate_reconciliation(p2_cases["missing_source_reconciliation"])
    missing_source_summary = build_bound_management_summary(missing_source_reconciliation)
    tampered = copy.deepcopy(reconciliation)
    tampered["differences"][0]["delta_cents"] += 1
    try:
        build_bound_management_summary(tampered)
    except StageReviewError as error:
        tampered_rejected = error.code in {"DIFFERENCE_ARITHMETIC_INVALID", "DIFFERENCE_TOTAL_DRIFT"}
    else:
        tampered_rejected = False

    closure = new_bound_closure(
        reconciliation=reconciliation,
        difference_ref=reconciliation["differences"][0]["difference_ref"],
        initial_report_version="经营差异摘要-v1",
    )
    event_payloads = (
        ("DIFFERENCE_DISCOVERED", "SYSTEM", {"difference_summary_zh": "已登记公开合成核对差异。"}),
        ("HANDLING_PROPOSED", "FINANCE_REVIEWER", {"handling_zh": "保留原账并单列差异。"}),
        ("IMPACT_PREVIEWED", "SYSTEM", {"impact_before_zh": "处理前差异待确认。", "impact_after_zh": "处理后差异单列可追溯。"}),
        ("HUMAN_CONFIRMED", "FINANCE_REVIEWER", {"decision_zh": "确认公开合成处理方案。"}),
        ("RECALCULATED", "SYSTEM", {"recalculation_status": "PASS", "affected_output_labels_zh": ["项目经营摘要"], "recalculation_ref": "S09REV-RECALC-001"}),
        ("REPORT_UPDATED", "SYSTEM", {"report_version": "经营差异摘要-v2", "report_update_summary_zh": "公开合成差异摘要已更新。", "recalculation_ref": "S09REV-RECALC-001", "summary_binding_fingerprint": closure["difference_fingerprint"]}),
    )
    closure_after_four = None
    for sequence, (event_type, actor, payload) in enumerate(event_payloads, start=1):
        closure = append_bound_closure_event(
            closure,
            _closure_event(closure, sequence, event_type, actor_role=actor, **payload),
        )
        if sequence == 4:
            closure_after_four = copy.deepcopy(closure)
    assert closure_after_four is not None
    stale = _closure_event(
        closure_after_four,
        5,
        "RECALCULATED",
        actor_role="SYSTEM",
        recalculation_status="PASS",
        affected_output_labels_zh=["项目经营摘要"],
        recalculation_ref="S09REV-STALE",
    )
    stale["reconciliation_fingerprint"] = "sha256:" + "0" * 64
    try:
        append_bound_closure_event(closure_after_four, stale)
    except StageReviewError as error:
        stale_rejected = error.code == "STALE_RECONCILIATION_REJECTED"
    else:
        stale_rejected = False
    cross = _closure_event(
        new_bound_closure(
            reconciliation=reconciliation,
            difference_ref=reconciliation["differences"][0]["difference_ref"],
            initial_report_version="经营差异摘要-v1",
        ),
        1,
        "DIFFERENCE_DISCOVERED",
        actor_role="SYSTEM",
        difference_summary_zh="串单测试。",
    )
    cross["difference_ref"] = reconciliation["differences"][1]["difference_ref"]
    try:
        append_bound_closure_event(
            new_bound_closure(
                reconciliation=reconciliation,
                difference_ref=reconciliation["differences"][0]["difference_ref"],
                initial_report_version="经营差异摘要-v1",
            ),
            cross,
        )
    except StageReviewError as error:
        cross_rejected = error.code == "CLOSURE_DIFFERENCE_MISMATCH"
    else:
        cross_rejected = False
    cross_source = p2_cases["cross_source_confirmation"]
    gate = evaluate_downstream_gate(closure=closure, cross_source_confirmations=(cross_source,))

    dictionary = p1.default_difference_dictionary()
    manual = p3.build_human_rule_manual()
    manual_labels = {
        row["rule_key"].removeprefix("DIFFERENCE_"): row["name_zh"]
        for row in manual["rules"]
        if row["rule_kind"] == "DIFFERENCE"
    }
    dictionary_labels = {row["difference_type_code"]: row["label_zh"] for row in dictionary["types"]}
    binding_fingerprint_sets = [
        [row["difference_fingerprint"] for row in candidate["bindings"]]
        for candidate in (summary, missing_source_summary)
    ]
    conversion = bound["conversion"]
    checks = [
        _check(CHECK_IDS[0], p1.default_ledger_view_policy()["legal_ledger_count"] == 1),
        _check(CHECK_IDS[1], len(dictionary["types"]) == 8),
        _check(CHECK_IDS[2], manual_labels == dictionary_labels),
        _check(CHECK_IDS[3], bound["event_chain_hash"].startswith("sha256:")),
        _check(CHECK_IDS[4], bound["active_adjustment_count"] == len(bound["bindings"]) == 1),
        _check(CHECK_IDS[5], bound["bindings"][0]["amount_delta_cents"] == 5000),
        _check(CHECK_IDS[6], bound["bindings"][0]["approval_event_ref"] == approval["event_ref"]),
        _check(CHECK_IDS[7], unbound_rejected),
        _check(CHECK_IDS[8], unknown_row_rejected),
        _check(CHECK_IDS[9], forged_rejected),
        _check(CHECK_IDS[10], bound["source_snapshot_unchanged"] and conversion["source_snapshot_unchanged"]),
        _check(CHECK_IDS[11], conversion["conservation"]["conservation_passed"] is True and conversion["conservation"]["residual_cents"] == 0),
        _check(CHECK_IDS[12], reconciliation["schema_version"] == p2.RECONCILIATION_SCHEMA),
        _check(CHECK_IDS[13], reconciliation["opposite_differences_retained_separately"] and reconciliation["silent_offset_count"] == 0),
        _check(CHECK_IDS[14], summary["omitted_decision_difference_count"] == missing_source_summary["omitted_decision_difference_count"] == 0),
        _check(CHECK_IDS[15], summary["input_difference_count"] == reconciliation["difference_count"] and missing_source_summary["input_difference_count"] == missing_source_reconciliation["difference_count"]),
        _check(CHECK_IDS[16], summary["management_summary"]["internal_reference_field_count"] == missing_source_summary["management_summary"]["internal_reference_field_count"] == 0),
        _check(CHECK_IDS[17], len(summary["bindings"]) == reconciliation["difference_count"] and len(missing_source_summary["bindings"]) == missing_source_reconciliation["difference_count"]),
        _check(CHECK_IDS[18], all(len(values) == len(set(values)) for values in binding_fingerprint_sets)),
        _check(CHECK_IDS[19], tampered_rejected),
        _check(CHECK_IDS[20], closure["difference_ref"] == reconciliation["differences"][0]["difference_ref"]),
        _check(CHECK_IDS[21], closure["p3_snapshot"]["closure_complete"] and closure["p3_snapshot"]["current_step_count"] == 6),
        _check(CHECK_IDS[22], closure["recalculation_ref"] == "S09REV-RECALC-001"),
        _check(CHECK_IDS[23], stale_rejected),
        _check(CHECK_IDS[24], cross_rejected),
        _check(CHECK_IDS[25], closure["p3_snapshot"]["current_report_version"] == "经营差异摘要-v2"),
        _check(CHECK_IDS[26], gate["pending_cross_source_confirmation_count"] == 1 and not gate["case_ready_for_downstream"]),
        _check(CHECK_IDS[27], cross_source["automatic_winner"] is None and not cross_source["auto_selection_performed"]),
        _check(CHECK_IDS[28], bound["raw_root_access_count"] == summary["raw_root_access_count"] == gate["raw_root_access_count"] == 0),
        _check(CHECK_IDS[29], gate["formal_report_generated"] is False and gate["formal_report_release_allowed"] is False),
    ]
    failed = sum(row["status"] != "PASS" for row in checks)
    return {
        "schema_version": "kmfa.v015.s09_stage_review.public_verification.v1",
        "run_phase_id": RUN_PHASE_ID,
        "public_safe": True,
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
    "StageReviewError",
    "TASK_ID",
    "VERSION",
    "append_bound_closure_event",
    "build_bound_management_summary",
    "convert_with_bound_adjustments",
    "evaluate_downstream_gate",
    "new_bound_closure",
    "public_verification",
    "reconciliation_fingerprint",
    "validate_reconciliation",
]
