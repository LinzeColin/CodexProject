#!/usr/bin/env python3
"""KMFA v1.5 S09-P2 conversion, reconciliation, and rerun kernel.

The kernel converts one immutable legal-ledger batch into versioned operating
facts, proves exact-cent conservation, records every project/financial
difference separately, reruns same-source inconsistencies, and routes genuine
cross-source conflicts to human confirmation.  It never writes a raw source.
"""

from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any

from KMFA.tools import v015_s07_p2_conflict_classification as s07p2
from KMFA.tools import v015_s09_p1_scope_rule_modeling as s09p1


RUN_PHASE_ID = "V015_S09_P2_CONVERSION_RECONCILIATION_ENGINE"
ROADMAP_PHASE_ID = "S09-P2"
TASK_ID = "KMFA-V015-S09-P2-CONVERSION-RECONCILIATION-ENGINE-20260715"
ACCEPTANCE_ID = "ACC-KMFA-V015-S09-P2-CONVERSION-RECONCILIATION-ENGINE"
VERSION = "1.5.0-dev-s09p2"

CONVERSION_SCHEMA = "kmfa.v015.s09p2.conversion_policy.v1"
SOURCE_BATCH_SCHEMA = "kmfa.v015.s09p2.legal_ledger_batch.v1"
OPERATING_FACT_SCHEMA = "kmfa.v015.s09p2.operating_fact.v1"
RECONCILIATION_SCHEMA = "kmfa.v015.s09p2.project_financial_reconciliation.v1"
RERUN_SCHEMA = "kmfa.v015.s09p2.rerun_confirmation.v1"

SOURCE_KINDS = ("ACCOUNTING_REVENUE", "ACCOUNTING_COST")
OPERATING_METRICS = ("OPERATING_REVENUE", "OPERATING_COST")
RECONCILIATION_SOURCE_KINDS = ("VOUCHER", "RECEIVABLE", "INVOICE", "BANK")
RERUN_CHAIN_LAYERS = (
    "CONVERSION",
    "OPERATING_FACT",
    "PROJECT_RECONCILIATION",
    "REPORT_REFERENCE",
)

SOURCE_DIFFERENCE_TYPES = {
    "VOUCHER": "CROSS_PERIOD",
    "RECEIVABLE": "UNSETTLED",
    "INVOICE": "UNBILLED",
    "BANK": "UNALLOCATED",
}


class ConversionReconciliationError(ValueError):
    """Fail-closed S09-P2 input, conservation, or orchestration error."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


def _mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ConversionReconciliationError("MAPPING_REQUIRED", f"{field} 必须是对象。")
    return copy.deepcopy(dict(value))


def _sequence(value: Any, field: str) -> list[Any]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ConversionReconciliationError("SEQUENCE_REQUIRED", f"{field} 必须是列表。")
    return copy.deepcopy(list(value))


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConversionReconciliationError("TEXT_REQUIRED", f"{field} 不能为空。")
    return value.strip()


def _text_list(value: Any, field: str) -> list[str]:
    rows = [_text(item, f"{field}[]") for item in _sequence(value, field)]
    if len(rows) != len(set(rows)):
        raise ConversionReconciliationError("DUPLICATE_VALUE", f"{field} 不允许重复。")
    return rows


def _cents(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConversionReconciliationError("INTEGER_CENTS_REQUIRED", f"{field} 必须使用整数分。")
    return value


def _stable_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def default_conversion_policy() -> dict[str, Any]:
    """Return the registered one-ledger to operating-view conversion policy."""

    return {
        "schema_version": CONVERSION_SCHEMA,
        "policy_ref": "CONVERSION-POLICY-S09P2-V1",
        "policy_version": "1.0.0",
        "source_ledger_ref": "LEGAL-LEDGER-PRIMARY",
        "source_view_id": "STATUTORY_ACCOUNTING",
        "target_view_id": "OPERATING_ANALYSIS",
        "p1_ledger_policy_ref": "LEDGER-VIEW-POLICY-S09P1-V1",
        "p1_adjustment_protocol_ref": "ADJUSTMENT-EVENT-PROTOCOL-S09P1-V1",
        "exact_integer_cents_required": True,
        "each_input_must_match_exactly_one_rule": True,
        "silent_difference_sink_allowed": False,
        "source_mutation_allowed": False,
        "rules": [
            {
                "rule_ref": "CONVERSION-RULE-S09P2-REVENUE-V1",
                "rule_version": "1.0.0",
                "source_kind": "ACCOUNTING_REVENUE",
                "target_metric": "OPERATING_REVENUE",
                "amount_multiplier": 1,
                "lineage_required": True,
            },
            {
                "rule_ref": "CONVERSION-RULE-S09P2-COST-V1",
                "rule_version": "1.0.0",
                "source_kind": "ACCOUNTING_COST",
                "target_metric": "OPERATING_COST",
                "amount_multiplier": 1,
                "lineage_required": True,
            },
        ],
    }


def validate_conversion_policy(policy: Mapping[str, Any]) -> dict[str, Any]:
    value = _mapping(policy, "policy")
    if value.get("schema_version") != CONVERSION_SCHEMA:
        raise ConversionReconciliationError("CONVERSION_POLICY_SCHEMA_INVALID", "转换策略版本不正确。")
    for field in ("policy_ref", "policy_version", "source_ledger_ref"):
        _text(value.get(field), field)
    if value.get("source_view_id") != "STATUTORY_ACCOUNTING" or value.get("target_view_id") != "OPERATING_ANALYSIS":
        raise ConversionReconciliationError("VIEW_BINDING_INVALID", "转换必须从法定账务视图进入经营分析视图。")
    if value.get("p1_ledger_policy_ref") != "LEDGER-VIEW-POLICY-S09P1-V1":
        raise ConversionReconciliationError("P1_LEDGER_POLICY_BINDING_INVALID", "必须绑定 S09-P1 唯一账本规则。")
    if value.get("p1_adjustment_protocol_ref") != "ADJUSTMENT-EVENT-PROTOCOL-S09P1-V1":
        raise ConversionReconciliationError("P1_ADJUSTMENT_PROTOCOL_BINDING_INVALID", "必须绑定 S09-P1 调整协议。")
    required_true = ("exact_integer_cents_required", "each_input_must_match_exactly_one_rule")
    if any(value.get(field) is not True for field in required_true):
        raise ConversionReconciliationError("CONVERSION_SAFETY_GATE_REQUIRED", "精确金额和唯一规则门禁必须开启。")
    if value.get("silent_difference_sink_allowed") is not False or value.get("source_mutation_allowed") is not False:
        raise ConversionReconciliationError("CONVERSION_UNSAFE_POLICY", "禁止静默差异池和来源改写。")
    checked_rules: list[dict[str, Any]] = []
    for index, raw in enumerate(_sequence(value.get("rules"), "rules"), start=1):
        rule = _mapping(raw, f"rules[{index}]")
        for field in ("rule_ref", "rule_version"):
            _text(rule.get(field), f"rules[{index}].{field}")
        if rule.get("source_kind") not in SOURCE_KINDS or rule.get("target_metric") not in OPERATING_METRICS:
            raise ConversionReconciliationError("CONVERSION_RULE_KIND_INVALID", "转换来源或经营指标未登记。")
        if rule.get("amount_multiplier") != 1:
            raise ConversionReconciliationError("CONSERVATION_MULTIPLIER_INVALID", "本阶段只允许一比一金额归类。")
        if rule.get("lineage_required") is not True:
            raise ConversionReconciliationError("CONVERSION_LINEAGE_REQUIRED", "每条转换规则必须保留血缘。")
        checked_rules.append(rule)
    refs = [row["rule_ref"] for row in checked_rules]
    kinds = [row["source_kind"] for row in checked_rules]
    metrics = [row["target_metric"] for row in checked_rules]
    if len(refs) != len(set(refs)) or len(kinds) != len(set(kinds)) or len(metrics) != len(set(metrics)):
        raise ConversionReconciliationError("AMBIGUOUS_CONVERSION_RULE", "规则引用、来源和目标必须唯一。")
    if set(kinds) != set(SOURCE_KINDS) or set(metrics) != set(OPERATING_METRICS):
        raise ConversionReconciliationError("CONVERSION_RULE_COVERAGE_INVALID", "收入和成本转换规则必须完整。")
    value["rules"] = checked_rules
    return value


def _validate_source_batch(batch: Mapping[str, Any], *, ledger_ref: str) -> dict[str, Any]:
    value = _mapping(batch, "source_batch")
    if value.get("schema_version") != SOURCE_BATCH_SCHEMA or value.get("legal_ledger_ref") != ledger_ref:
        raise ConversionReconciliationError("SOURCE_BATCH_BINDING_INVALID", "来源批次必须绑定唯一合法账本。")
    for field in ("batch_ref", "source_version", "period_ref"):
        _text(value.get(field), field)
    rows: list[dict[str, Any]] = []
    for index, raw in enumerate(_sequence(value.get("rows"), "rows"), start=1):
        row = _mapping(raw, f"rows[{index}]")
        for field in ("row_ref", "project_ref", "source_kind", "source_evidence_ref"):
            _text(row.get(field), f"rows[{index}].{field}")
        if row["source_kind"] not in SOURCE_KINDS:
            raise ConversionReconciliationError("UNREGISTERED_SOURCE_KIND", "来源类型没有转换规则。")
        row["amount_cents"] = _cents(row.get("amount_cents"), f"rows[{index}].amount_cents")
        rows.append(row)
    refs = [row["row_ref"] for row in rows]
    if not rows or len(refs) != len(set(refs)):
        raise ConversionReconciliationError("SOURCE_ROW_SET_INVALID", "来源行必须非空且引用唯一。")
    value["rows"] = rows
    return value


def assert_conservation(
    *, input_total_cents: int, adjustment_total_cents: int, output_total_cents: int, explicit_difference_total_cents: int
) -> dict[str, Any]:
    """Prove input + approved adjustment = output + explicit differences."""

    inputs = _cents(input_total_cents, "input_total_cents")
    adjustments = _cents(adjustment_total_cents, "adjustment_total_cents")
    outputs = _cents(output_total_cents, "output_total_cents")
    differences = _cents(explicit_difference_total_cents, "explicit_difference_total_cents")
    residual = inputs + adjustments - outputs - differences
    if residual != 0:
        raise ConversionReconciliationError("CONVERSION_NOT_BALANCED", "输入、调整、输出和显式差异无法守恒。")
    return {
        "input_total_cents": inputs,
        "approved_adjustment_total_cents": adjustments,
        "output_total_cents": outputs,
        "explicit_difference_total_cents": differences,
        "residual_cents": residual,
        "conservation_passed": True,
    }


def convert_ledger_to_operating_facts(
    *,
    source_batch: Mapping[str, Any],
    adjustments: Sequence[Mapping[str, Any]] = (),
    policy: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Convert an immutable ledger batch and prove exact-cent conservation."""

    checked_policy = validate_conversion_policy(policy or default_conversion_policy())
    batch = _validate_source_batch(source_batch, ledger_ref=checked_policy["source_ledger_ref"])
    source_before = copy.deepcopy(batch)
    rules = {row["source_kind"]: row for row in checked_policy["rules"]}
    row_by_ref = {row["row_ref"]: row for row in batch["rows"]}

    adjustment_by_row: dict[str, int] = {ref: 0 for ref in row_by_ref}
    effective_adjustment_refs: list[str] = []
    ignored_adjustment_refs: list[str] = []
    seen_adjustments: set[str] = set()
    for index, raw in enumerate(_sequence(adjustments, "adjustments"), start=1):
        row = _mapping(raw, f"adjustments[{index}]")
        ref = _text(row.get("event_ref"), f"adjustments[{index}].event_ref")
        if ref in seen_adjustments:
            raise ConversionReconciliationError("DUPLICATE_ADJUSTMENT_EVENT", "调整事件引用不可重复。")
        seen_adjustments.add(ref)
        source_row_ref = _text(row.get("source_row_ref"), f"adjustments[{index}].source_row_ref")
        if source_row_ref not in row_by_ref:
            raise ConversionReconciliationError("ADJUSTMENT_SOURCE_ROW_UNKNOWN", "调整必须绑定本批次来源行。")
        amount = _cents(row.get("amount_delta_cents"), f"adjustments[{index}].amount_delta_cents")
        effective = row.get("effective") is True
        if effective and row.get("approval_status") != "APPROVED":
            raise ConversionReconciliationError("UNAPPROVED_ADJUSTMENT_EFFECTIVE", "未审批调整不得进入经营事实。")
        expected_metric = rules[row_by_ref[source_row_ref]["source_kind"]]["target_metric"]
        if row.get("target_metric") != expected_metric or row.get("affected_view_id") != "OPERATING_ANALYSIS":
            raise ConversionReconciliationError("ADJUSTMENT_SCOPE_MISMATCH", "调整目标必须与来源转换规则完全一致。")
        if effective:
            adjustment_by_row[source_row_ref] += amount
            effective_adjustment_refs.append(ref)
        else:
            ignored_adjustment_refs.append(ref)

    facts: list[dict[str, Any]] = []
    for row in batch["rows"]:
        rule = rules[row["source_kind"]]
        adjustment_cents = adjustment_by_row[row["row_ref"]]
        facts.append(
            {
                "schema_version": OPERATING_FACT_SCHEMA,
                "fact_ref": f"OPERATING-FACT-{row['row_ref']}",
                "project_ref": row["project_ref"],
                "period_ref": batch["period_ref"],
                "target_view_id": "OPERATING_ANALYSIS",
                "metric": rule["target_metric"],
                "base_amount_cents": row["amount_cents"],
                "approved_adjustment_cents": adjustment_cents,
                "amount_cents": row["amount_cents"] + adjustment_cents,
                "source_batch_ref": batch["batch_ref"],
                "source_version": batch["source_version"],
                "source_row_ref": row["row_ref"],
                "source_evidence_ref": row["source_evidence_ref"],
                "conversion_rule_ref": rule["rule_ref"],
                "conversion_rule_version": rule["rule_version"],
                "source_mutation_performed": False,
                "raw_source_mutation_performed": False,
            }
        )

    conservation = assert_conservation(
        input_total_cents=sum(row["amount_cents"] for row in batch["rows"]),
        adjustment_total_cents=sum(adjustment_by_row.values()),
        output_total_cents=sum(row["amount_cents"] for row in facts),
        explicit_difference_total_cents=0,
    )
    if source_before != batch:
        raise ConversionReconciliationError("SOURCE_MUTATION_DETECTED", "转换过程中来源批次发生变化。")
    return {
        "schema_version": "kmfa.v015.s09p2.conversion_result.v1",
        "policy_ref": checked_policy["policy_ref"],
        "policy_version": checked_policy["policy_version"],
        "source_batch_ref": batch["batch_ref"],
        "source_version": batch["source_version"],
        "source_snapshot_hash_before": _stable_hash(source_before),
        "source_snapshot_hash_after": _stable_hash(batch),
        "source_snapshot_unchanged": source_before == batch,
        "operating_facts": facts,
        "effective_adjustment_refs": effective_adjustment_refs,
        "ignored_adjustment_refs": ignored_adjustment_refs,
        "unapproved_effective_count": 0,
        "silent_difference_count": 0,
        "conservation": conservation,
        "status": "BALANCED",
    }


def default_reconciliation_policy() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s09p2.project_financial_reconciliation_policy.v1",
        "policy_ref": "PROJECT-FINANCIAL-RECONCILIATION-S09P2-V1",
        "policy_version": "1.0.0",
        "required_source_kinds": list(RECONCILIATION_SOURCE_KINDS),
        "difference_type_by_source_kind": copy.deepcopy(SOURCE_DIFFERENCE_TYPES),
        "exact_integer_cents_required": True,
        "each_difference_kept_separately": True,
        "opposite_difference_netting_allowed": False,
        "missing_source_requires_confirmation": True,
        "source_mutation_allowed": False,
    }


def _difference_rule(code: str, dictionary: Mapping[str, Any]) -> dict[str, Any]:
    checked = s09p1.validate_difference_dictionary(dictionary)
    match = next((row for row in checked["types"] if row["difference_type_code"] == code), None)
    if match is None:
        raise ConversionReconciliationError("DIFFERENCE_RULE_MISSING", "核对差异未绑定 S09-P1 字典。")
    return match


def reconcile_project_financial_chain(
    *,
    project_fact: Mapping[str, Any],
    observations: Sequence[Mapping[str, Any]],
    policy: Mapping[str, Any] | None = None,
    difference_dictionary: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Cross-check one project metric against voucher/AR/invoice/bank evidence."""

    checked_policy = _mapping(policy or default_reconciliation_policy(), "policy")
    if checked_policy != default_reconciliation_policy():
        raise ConversionReconciliationError("RECONCILIATION_POLICY_DRIFT", "核对策略必须使用已登记版本。")
    dictionary = s09p1.validate_difference_dictionary(difference_dictionary or s09p1.default_difference_dictionary())
    fact = _mapping(project_fact, "project_fact")
    for field in ("fact_ref", "project_ref", "source_ref", "source_version", "comparison_basis"):
        _text(fact.get(field), field)
    if fact.get("metric") not in OPERATING_METRICS:
        raise ConversionReconciliationError("PROJECT_FACT_METRIC_INVALID", "项目事实指标必须是经营收入或经营成本。")
    fact["amount_cents"] = _cents(fact.get("amount_cents"), "project_fact.amount_cents")
    checked_observations: list[dict[str, Any]] = []
    for index, raw in enumerate(_sequence(observations, "observations"), start=1):
        row = _mapping(raw, f"observations[{index}]")
        for field in ("observation_ref", "source_ref", "source_version"):
            _text(row.get(field), f"observations[{index}].{field}")
        if row.get("source_kind") not in RECONCILIATION_SOURCE_KINDS:
            raise ConversionReconciliationError("RECONCILIATION_SOURCE_KIND_INVALID", "核对来源未登记。")
        if row.get("project_ref") != fact["project_ref"] or row.get("metric") != fact["metric"]:
            raise ConversionReconciliationError("PROJECT_RECONCILIATION_BINDING_MISMATCH", "核对来源串项目或串指标。")
        if row.get("comparison_basis") != fact["comparison_basis"]:
            raise ConversionReconciliationError("COMPARISON_BASIS_MISMATCH", "不同口径不能直接比较。")
        row["amount_cents"] = _cents(row.get("amount_cents"), f"observations[{index}].amount_cents")
        row["evidence_codes"] = _text_list(row.get("evidence_codes"), f"observations[{index}].evidence_codes")
        checked_observations.append(row)
    kinds = [row["source_kind"] for row in checked_observations]
    if len(kinds) != len(set(kinds)):
        raise ConversionReconciliationError("DUPLICATE_RECONCILIATION_SOURCE", "同类来源不得重复并静默汇总。")

    passes: list[dict[str, Any]] = []
    differences: list[dict[str, Any]] = []
    by_kind = {row["source_kind"]: row for row in checked_observations}
    for kind in RECONCILIATION_SOURCE_KINDS:
        row = by_kind.get(kind)
        if row is None:
            differences.append(
                {
                    "difference_ref": f"DIFF-{fact['fact_ref']}-{kind}",
                    "difference_type_code": "MISSING_SOURCE",
                    "status": "MISSING_SOURCE_REQUIRES_CONFIRMATION",
                    "project_ref": fact["project_ref"],
                    "metric": fact["metric"],
                    "source_kind": kind,
                    "source_refs": [fact["source_ref"]],
                    "expected_amount_cents": fact["amount_cents"],
                    "actual_amount_cents": None,
                    "delta_cents": None,
                    "affected_view_ids": ["OPERATING_ANALYSIS", "PROJECT_REALITY"],
                    "impact_zh": f"缺少{kind}来源，无法完成项目与财务全链路核对。",
                    "manual_confirmation_required": True,
                    "silent_offset_allowed": False,
                }
            )
            continue
        delta = row["amount_cents"] - fact["amount_cents"]
        if delta == 0:
            passes.append(
                {
                    "source_kind": kind,
                    "source_refs": [fact["source_ref"], row["source_ref"]],
                    "expected_amount_cents": fact["amount_cents"],
                    "actual_amount_cents": row["amount_cents"],
                    "delta_cents": 0,
                    "status": "EXACT_MATCH",
                }
            )
            continue
        difference_type = SOURCE_DIFFERENCE_TYPES[kind]
        rule = _difference_rule(difference_type, dictionary)
        classification = s09p1.classify_difference(
            difference_type_code=difference_type,
            amount_delta_cents=delta,
            evidence_codes=row["evidence_codes"],
            dictionary=dictionary,
        )
        differences.append(
            {
                "difference_ref": f"DIFF-{fact['fact_ref']}-{kind}",
                "difference_type_code": difference_type,
                "difference_label_zh": rule["label_zh"],
                "status": "DIFFERENCE_REQUIRES_CONFIRMATION",
                "classification_state": classification["state"],
                "project_ref": fact["project_ref"],
                "metric": fact["metric"],
                "source_kind": kind,
                "source_refs": [fact["source_ref"], row["source_ref"]],
                "source_versions": [fact["source_version"], row["source_version"]],
                "evidence_codes": copy.deepcopy(row["evidence_codes"]),
                "expected_amount_cents": fact["amount_cents"],
                "actual_amount_cents": row["amount_cents"],
                "delta_cents": delta,
                "affected_view_ids": copy.deepcopy(rule["affected_view_ids"]),
                "impact_zh": f"{kind}与{fact['metric']}相差{abs(delta)}分，影响项目经营事实和相关视图。",
                "manual_confirmation_required": True,
                "silent_offset_allowed": False,
            }
        )

    complete_chain = set(by_kind) == set(RECONCILIATION_SOURCE_KINDS)
    return {
        "schema_version": RECONCILIATION_SCHEMA,
        "policy_ref": checked_policy["policy_ref"],
        "fact_ref": fact["fact_ref"],
        "project_ref": fact["project_ref"],
        "metric": fact["metric"],
        "comparison_basis": fact["comparison_basis"],
        "required_source_count": len(RECONCILIATION_SOURCE_KINDS),
        "observed_source_count": len(checked_observations),
        "complete_chain": complete_chain,
        "exact_match_count": len(passes),
        "difference_count": len(differences),
        "passes": passes,
        "differences": differences,
        "difference_delta_sum_cents": sum(
            row["delta_cents"] for row in differences if isinstance(row.get("delta_cents"), int)
        ),
        "opposite_differences_retained_separately": True,
        "silent_offset_count": 0,
        "status": "RECONCILED" if complete_chain and not differences else "REQUIRES_CONFIRMATION",
        "source_mutation_performed": False,
        "raw_source_mutation_performed": False,
    }


def _reference_observations(rows: Sequence[Mapping[str, Any]]) -> list[s07p2.ReferenceObservation]:
    result: list[s07p2.ReferenceObservation] = []
    for index, raw in enumerate(_sequence(rows, "observations"), start=1):
        row = _mapping(raw, f"observations[{index}]")
        result.append(
            s07p2.ReferenceObservation(
                source_ref=_text(row.get("source_ref"), "source_ref"),
                source_version=_text(row.get("source_version"), "source_version"),
                field_id=_text(row.get("field_id"), "field_id"),
                consumer_ref=_text(row.get("consumer_ref"), "consumer_ref"),
                value=row.get("value"),
            )
        )
    return result


def orchestrate_same_source_rerun(
    *,
    source_snapshot: Mapping[str, Any],
    observations_before: Sequence[Mapping[str, Any]],
    observations_after: Sequence[Mapping[str, Any]],
    previous_versions: Mapping[str, str],
) -> dict[str, Any]:
    """Invalidate and rerun the complete derived chain without touching source."""

    source = _mapping(source_snapshot, "source_snapshot")
    before_hash = _stable_hash(source)
    old_versions = _mapping(previous_versions, "previous_versions")
    if set(old_versions) != set(RERUN_CHAIN_LAYERS):
        raise ConversionReconciliationError("RERUN_CHAIN_INCOMPLETE", "重跑必须覆盖完整派生链。")
    for layer, version in old_versions.items():
        _text(version, f"previous_versions.{layer}")
    try:
        classification = s07p2.classify_same_source_references(
            _reference_observations(observations_before),
            rerun_observations=_reference_observations(observations_after),
        )
    except s07p2.ConflictClassificationError as error:
        raise ConversionReconciliationError(error.code, str(error)) from error
    if classification["classification"] not in ("SAME_SOURCE_REFERENCE_MISMATCH", "SYSTEM_ERROR"):
        raise ConversionReconciliationError("RERUN_NOT_REQUIRED", "同源结果一致时不得制造新版本。")
    resolved = classification["status"] == "RESOLVED_BY_RERUN"
    chain_status = "ACTIVE" if resolved else "BLOCKED_SYSTEM_ERROR"
    version_events = []
    for order, layer in enumerate(RERUN_CHAIN_LAYERS, start=1):
        version_events.append(
            {
                "sequence": order,
                "layer": layer,
                "old_version_ref": old_versions[layer],
                "new_version_ref": f"{old_versions[layer]}-R1",
                "old_version_preserved": True,
                "old_version_overwritten": False,
                "new_version_status": chain_status,
                "source_write_performed": False,
                "raw_source_mutation_performed": False,
            }
        )
    after_hash = _stable_hash(source)
    if before_hash != after_hash:
        raise ConversionReconciliationError("SOURCE_MUTATION_DETECTED", "重跑不得修改来源快照。")
    return {
        "schema_version": RERUN_SCHEMA,
        "classification": classification["classification"],
        "status": "RERUN_RESOLVED" if resolved else "SYSTEM_ERROR_BLOCKED",
        "same_source": True,
        "rerun_performed": True,
        "full_chain_rerun": True,
        "chain_layer_count": len(version_events),
        "chain_state_consistent": len({row["new_version_status"] for row in version_events}) == 1,
        "version_events": version_events,
        "automatic_winner": None,
        "formal_report_blocked": not resolved,
        "source_snapshot_hash_before": before_hash,
        "source_snapshot_hash_after": after_hash,
        "source_snapshot_unchanged": before_hash == after_hash,
        "raw_source_mutation_performed": False,
    }


def queue_cross_source_confirmation(
    *, case_ref: str, field_id: str, observations: Sequence[Mapping[str, Any]], evidence_refs: Sequence[str]
) -> dict[str, Any] | None:
    """Route a genuine cross-source disagreement without choosing a winner."""

    try:
        queued = s07p2.queue_cross_source_conflict(
            case_ref=_text(case_ref, "case_ref"),
            field_id=_text(field_id, "field_id"),
            observations=_reference_observations(observations),
            evidence_refs=_text_list(evidence_refs, "evidence_refs"),
        )
    except s07p2.ConflictClassificationError as error:
        raise ConversionReconciliationError(error.code, str(error)) from error
    if queued is None:
        return None
    return {
        **queued,
        "schema_version": RERUN_SCHEMA,
        "status": "PENDING_HUMAN_CONFIRMATION",
        "automatic_winner": None,
        "auto_selection_performed": False,
        "resolved_value": None,
        "source_mutation_performed": False,
        "raw_source_mutation_performed": False,
    }


def synthetic_acceptance_cases() -> dict[str, Any]:
    """Execute public-safe deterministic acceptance cases for all three tasks."""

    source_batch = {
        "schema_version": SOURCE_BATCH_SCHEMA,
        "batch_ref": "SYNTHETIC-LEDGER-BATCH-001",
        "source_version": "SYNTHETIC-SOURCE-V1",
        "legal_ledger_ref": "LEGAL-LEDGER-PRIMARY",
        "period_ref": "SYNTHETIC-PERIOD-001",
        "rows": [
            {
                "row_ref": "SYN-ROW-REVENUE-001",
                "project_ref": "SYNTHETIC-PROJECT-001",
                "source_kind": "ACCOUNTING_REVENUE",
                "amount_cents": 100000,
                "source_evidence_ref": "SYN-EVIDENCE-LEDGER-REVENUE",
            },
            {
                "row_ref": "SYN-ROW-COST-001",
                "project_ref": "SYNTHETIC-PROJECT-001",
                "source_kind": "ACCOUNTING_COST",
                "amount_cents": -40000,
                "source_evidence_ref": "SYN-EVIDENCE-LEDGER-COST",
            },
        ],
    }
    source_snapshot = copy.deepcopy(source_batch)
    conversion = convert_ledger_to_operating_facts(
        source_batch=source_batch,
        adjustments=(
            {
                "event_ref": "CTRL-EVENT-SYN-APPROVED-001",
                "source_row_ref": "SYN-ROW-REVENUE-001",
                "target_metric": "OPERATING_REVENUE",
                "affected_view_id": "OPERATING_ANALYSIS",
                "amount_delta_cents": 5000,
                "approval_status": "APPROVED",
                "effective": True,
            },
            {
                "event_ref": "CTRL-EVENT-SYN-PENDING-001",
                "source_row_ref": "SYN-ROW-COST-001",
                "target_metric": "OPERATING_COST",
                "affected_view_id": "OPERATING_ANALYSIS",
                "amount_delta_cents": 2000,
                "approval_status": "PENDING",
                "effective": False,
            },
        ),
    )
    imbalance_blocked = False
    try:
        assert_conservation(
            input_total_cents=60000,
            adjustment_total_cents=5000,
            output_total_cents=64999,
            explicit_difference_total_cents=0,
        )
    except ConversionReconciliationError as error:
        imbalance_blocked = error.code == "CONVERSION_NOT_BALANCED"
    float_rejected = False
    try:
        assert_conservation(
            input_total_cents=json.loads("1.5"),
            adjustment_total_cents=0,
            output_total_cents=0,
            explicit_difference_total_cents=0,
        )
    except ConversionReconciliationError as error:
        float_rejected = error.code == "INTEGER_CENTS_REQUIRED"

    revenue_fact = next(row for row in conversion["operating_facts"] if row["metric"] == "OPERATING_REVENUE")
    project_fact = {
        "fact_ref": revenue_fact["fact_ref"],
        "project_ref": revenue_fact["project_ref"],
        "metric": revenue_fact["metric"],
        "amount_cents": revenue_fact["amount_cents"],
        "source_ref": revenue_fact["source_row_ref"],
        "source_version": revenue_fact["source_version"],
        "comparison_basis": "SYNTHETIC-ACCRUAL-BASIS-V1",
    }
    observations = [
        {
            "observation_ref": "OBS-VOUCHER-001",
            "project_ref": project_fact["project_ref"],
            "metric": project_fact["metric"],
            "source_kind": "VOUCHER",
            "source_ref": "SYN-SOURCE-VOUCHER",
            "source_version": "SYN-V1",
            "comparison_basis": project_fact["comparison_basis"],
            "amount_cents": 105000,
            "evidence_codes": ["OCCURRENCE_DATE", "ACCOUNTING_PERIOD", "BUSINESS_PERIOD_BASIS"],
        },
        {
            "observation_ref": "OBS-RECEIVABLE-001",
            "project_ref": project_fact["project_ref"],
            "metric": project_fact["metric"],
            "source_kind": "RECEIVABLE",
            "source_ref": "SYN-SOURCE-RECEIVABLE",
            "source_version": "SYN-V1",
            "comparison_basis": project_fact["comparison_basis"],
            "amount_cents": 104000,
            "evidence_codes": ["CONTRACT_PROGRESS", "SETTLEMENT_STATUS"],
        },
        {
            "observation_ref": "OBS-INVOICE-001",
            "project_ref": project_fact["project_ref"],
            "metric": project_fact["metric"],
            "source_kind": "INVOICE",
            "source_ref": "SYN-SOURCE-INVOICE",
            "source_version": "SYN-V1",
            "comparison_basis": project_fact["comparison_basis"],
            "amount_cents": 106000,
            "evidence_codes": ["CONTRACT_OR_DELIVERY", "PERIOD_BASIS"],
        },
        {
            "observation_ref": "OBS-BANK-001",
            "project_ref": project_fact["project_ref"],
            "metric": project_fact["metric"],
            "source_kind": "BANK",
            "source_ref": "SYN-SOURCE-BANK",
            "source_version": "SYN-V1",
            "comparison_basis": project_fact["comparison_basis"],
            "amount_cents": 105000,
            "evidence_codes": ["SOURCE_RECORD", "ALLOCATION_BASIS"],
        },
    ]
    reconciliation = reconcile_project_financial_chain(project_fact=project_fact, observations=observations)
    missing_source = reconcile_project_financial_chain(project_fact=project_fact, observations=observations[:-1])

    before_observations = (
        {
            "source_ref": "SYN-SOURCE-LEDGER",
            "source_version": "SYN-V1",
            "field_id": "OPERATING_REVENUE",
            "consumer_ref": "CONSUMER-OPERATING-FACT",
            "value": 105000,
        },
        {
            "source_ref": "SYN-SOURCE-LEDGER",
            "source_version": "SYN-V1",
            "field_id": "OPERATING_REVENUE",
            "consumer_ref": "CONSUMER-RECONCILIATION",
            "value": 104000,
        },
    )
    resolved_after = (
        {**before_observations[0]},
        {**before_observations[1], "value": 105000},
    )
    previous_versions = {layer: f"SYN-{layer}-V1" for layer in RERUN_CHAIN_LAYERS}
    rerun_resolved = orchestrate_same_source_rerun(
        source_snapshot=source_snapshot,
        observations_before=before_observations,
        observations_after=resolved_after,
        previous_versions=previous_versions,
    )
    rerun_persistent = orchestrate_same_source_rerun(
        source_snapshot=source_snapshot,
        observations_before=before_observations,
        observations_after=before_observations,
        previous_versions=previous_versions,
    )
    cross_source = queue_cross_source_confirmation(
        case_ref="SYN-CROSS-SOURCE-001",
        field_id="OPERATING_REVENUE",
        observations=(
            {**before_observations[0], "consumer_ref": "SOURCE-A", "source_ref": "SYN-SOURCE-A"},
            {**before_observations[1], "consumer_ref": "SOURCE-B", "source_ref": "SYN-SOURCE-B"},
        ),
        evidence_refs=("SYN-EVIDENCE-A", "SYN-EVIDENCE-B"),
    )

    return {
        "schema_version": "kmfa.v015.s09p2.synthetic_acceptance.v1",
        "conversion": conversion,
        "reconciliation": reconciliation,
        "missing_source_reconciliation": missing_source,
        "rerun_resolved": rerun_resolved,
        "rerun_persistent": rerun_persistent,
        "cross_source_confirmation": cross_source,
        "imbalance_blocked": imbalance_blocked,
        "float_money_rejected": float_rejected,
        "opposite_delta_values": sorted(
            row["delta_cents"] for row in reconciliation["differences"] if isinstance(row.get("delta_cents"), int)
        ),
        "source_snapshot_unchanged": source_snapshot == source_batch,
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "formal_report_generated": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }


if __name__ == "__main__":
    print(json.dumps(synthetic_acceptance_cases(), ensure_ascii=False, indent=2, sort_keys=True))
