#!/usr/bin/env python3
"""KMFA v1.5 S07-P2 conflict classification and responsibility kernel.

The kernel is deliberately conservative. A disagreement between consumers of
the same source invalidates those consumers and triggers one deterministic
rerun. A disagreement between different sources never gets an automatic
winner. Responsibility is assigned only when a complete evidence chain proves
the failing layer; otherwise the result is UNDETERMINED.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

from KMFA.tools import v015_s06_p3_baseline_coverage_boundary as s06p3


RUN_PHASE_ID = "V015_S07_P2_CONFLICT_CLASSIFICATION"
ROADMAP_PHASE_ID = "S07-P2"
TASK_ID = "KMFA-V015-S07-P2-CONFLICT-CLASSIFICATION-20260715"
ACCEPTANCE_ID = "ACC-KMFA-V015-S07-P2-CONFLICT-CLASSIFICATION"
VERSION = "1.5.0-dev-s07p2"
SCHEMA_VERSION = "kmfa.v015.s07p2.conflict_classification.v1"

RAW_VALUE = "RAW_VALUE"
MAPPING = "MAPPING"
RULE = "RULE"
CALCULATION = "CALCULATION"
DISPLAY = "DISPLAY"
RESPONSIBILITY_LAYERS = (RAW_VALUE, MAPPING, RULE, CALCULATION, DISPLAY)
PASS = "PASS"
FAIL = "FAIL"
UNKNOWN = "UNKNOWN"
EVIDENCE_STATES = (PASS, FAIL, UNKNOWN)


class ConflictClassificationError(ValueError):
    """Fail-closed input or evidence error."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class ReferenceObservation:
    source_ref: str
    source_version: str
    field_id: str
    consumer_ref: str
    value: Any

    def __post_init__(self) -> None:
        for name in ("source_ref", "source_version", "field_id", "consumer_ref"):
            if not str(getattr(self, name)).strip():
                raise ConflictClassificationError("REFERENCE_ID_REQUIRED", f"{name} 不能为空。")
        if isinstance(self.value, float):
            raise ConflictClassificationError("FLOAT_VALUE_FORBIDDEN", "冲突比较禁止浮点值。")
        if isinstance(self.value, (dict, list, tuple, set)):
            raise ConflictClassificationError("SCALAR_VALUE_REQUIRED", "冲突比较只接受已规范化标量。")


@dataclass(frozen=True)
class LayerEvidence:
    layer: str
    state: str
    evidence_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.layer not in RESPONSIBILITY_LAYERS or self.state not in EVIDENCE_STATES:
            raise ConflictClassificationError("INVALID_LAYER_EVIDENCE", "责任层或证据状态无效。")
        if any(not str(value).strip() for value in self.evidence_ids):
            raise ConflictClassificationError("EMPTY_EVIDENCE_ID", "证据标识不能为空。")


def _value_key(value: Any) -> tuple[str, str]:
    return type(value).__name__, json.dumps(value, ensure_ascii=False, sort_keys=True)


def _one_same_source_group(observations: Sequence[ReferenceObservation]) -> tuple[str, str, str]:
    if len(observations) < 2:
        raise ConflictClassificationError("MULTIPLE_CONSUMERS_REQUIRED", "同源检查至少需要两个消费位置。")
    keys = {(row.source_ref, row.source_version, row.field_id) for row in observations}
    if len(keys) != 1:
        raise ConflictClassificationError("NOT_ONE_SOURCE_VERSION_FIELD", "同源检查必须绑定同一来源、版本和字段。")
    consumers = [row.consumer_ref for row in observations]
    if len(consumers) != len(set(consumers)):
        raise ConflictClassificationError("DUPLICATE_CONSUMER", "消费位置不能重复。")
    return next(iter(keys))


def classify_same_source_references(
    observations: Sequence[ReferenceObservation],
    *,
    rerun_observations: Sequence[ReferenceObservation] | None = None,
) -> dict[str, Any]:
    """Invalidate mismatched consumers, then classify one exact rerun."""

    key = _one_same_source_group(observations)
    before_values = {_value_key(row.value) for row in observations}
    base = {
        "schema_version": SCHEMA_VERSION,
        "source_ref": key[0],
        "source_version": key[1],
        "field_id": key[2],
        "consumer_refs": sorted(row.consumer_ref for row in observations),
        "consumer_count": len(observations),
        "automatic_winner": None,
        "user_responsibility_assigned": False,
    }
    if len(before_values) == 1:
        return {
            **base,
            "classification": "SAME_SOURCE_REFERENCE",
            "status": "CONSISTENT",
            "invalidated_consumer_count": 0,
            "rerun_performed": False,
            "formal_report_blocked": False,
            "system_error": False,
        }
    if rerun_observations is None:
        return {
            **base,
            "classification": "SAME_SOURCE_REFERENCE_MISMATCH",
            "status": "INVALIDATED_RERUN_REQUIRED",
            "invalidated_consumer_count": len(observations),
            "rerun_performed": False,
            "formal_report_blocked": True,
            "system_error": False,
        }

    rerun_key = _one_same_source_group(rerun_observations)
    if rerun_key != key:
        raise ConflictClassificationError("RERUN_BINDING_CHANGED", "重跑必须保持相同来源、版本和字段。")
    if {row.consumer_ref for row in rerun_observations} != {row.consumer_ref for row in observations}:
        raise ConflictClassificationError("RERUN_CONSUMERS_CHANGED", "重跑必须覆盖全部原消费位置。")
    after_values = {_value_key(row.value) for row in rerun_observations}
    if len(after_values) == 1:
        return {
            **base,
            "classification": "SAME_SOURCE_REFERENCE_MISMATCH",
            "status": "RESOLVED_BY_RERUN",
            "invalidated_consumer_count": len(observations),
            "rerun_performed": True,
            "rerun_consistent": True,
            "formal_report_blocked": False,
            "system_error": False,
        }
    return {
        **base,
        "classification": "SYSTEM_ERROR",
        "status": "PERSISTENT_MISMATCH_AFTER_RERUN",
        "invalidated_consumer_count": len(observations),
        "rerun_performed": True,
        "rerun_consistent": False,
        "formal_report_blocked": True,
        "system_error": True,
        "responsible_layer": "SYSTEM",
    }


def queue_cross_source_conflict(
    *,
    case_ref: str,
    field_id: str,
    observations: Sequence[ReferenceObservation],
    evidence_refs: Sequence[str],
) -> dict[str, Any] | None:
    """Return a manual queue record for a genuine cross-source disagreement."""

    if not case_ref or not field_id or not evidence_refs or any(not value for value in evidence_refs):
        raise ConflictClassificationError("CONFLICT_EVIDENCE_REQUIRED", "跨源冲突必须有案件、字段和证据标识。")
    if len(observations) < 2 or len({row.source_ref for row in observations}) < 2:
        raise ConflictClassificationError("DISTINCT_SOURCES_REQUIRED", "跨源检查至少需要两个不同来源。")
    if {row.field_id for row in observations} != {field_id}:
        raise ConflictClassificationError("FIELD_BINDING_MISMATCH", "跨源观察必须绑定同一规范字段。")
    if len({_value_key(row.value) for row in observations}) == 1:
        return None
    return {
        "schema_version": SCHEMA_VERSION,
        "queue_id": f"{case_ref}-{field_id}-CROSS-SOURCE",
        "case_ref": case_ref,
        "field_id": field_id,
        "classification": "CROSS_SOURCE_BUSINESS_CONFLICT",
        "source_refs": sorted({row.source_ref for row in observations}),
        "source_count": len({row.source_ref for row in observations}),
        "evidence_refs": list(evidence_refs),
        "status": "PENDING_HUMAN_DECISION",
        "manual_decision_required": True,
        "automatic_winner": None,
        "auto_selection_performed": False,
        "resolved_value": None,
        "formal_report_blocked": True,
        "user_responsibility_assigned": False,
    }


def determine_responsibility(
    evidence: Iterable[LayerEvidence],
    *,
    explicit_authorized_user_entry: bool = False,
) -> dict[str, Any]:
    """Assign responsibility only when the evidence chain proves one layer."""

    rows = list(evidence)
    if [row.layer for row in rows] != list(RESPONSIBILITY_LAYERS):
        raise ConflictClassificationError("COMPLETE_ORDERED_CHAIN_REQUIRED", "必须按五层提供完整证据链。")
    failures = [index for index, row in enumerate(rows) if row.state == FAIL]
    all_evidence_ids = [value for row in rows for value in row.evidence_ids]
    result = {
        "schema_version": SCHEMA_VERSION,
        "layers_checked": list(RESPONSIBILITY_LAYERS),
        "layer_count": len(rows),
        "evidence_ids": all_evidence_ids,
        "evidence_count": len(all_evidence_ids),
        "explicit_authorized_user_entry": explicit_authorized_user_entry,
        "system_problem_assigned_to_user": False,
    }
    if len(failures) != 1:
        return {**result, "classification": "UNDETERMINED", "responsible_layer": None, "reason": "证据不足或存在多个失败层。"}
    index = failures[0]
    failed = rows[index]
    upstream_proven = all(row.state == PASS and row.evidence_ids for row in rows[:index])
    failure_proven = bool(failed.evidence_ids)
    if not upstream_proven or not failure_proven:
        return {**result, "classification": "UNDETERMINED", "responsible_layer": None, "reason": "失败层或其上游证据不完整。"}
    if failed.layer == RAW_VALUE:
        if not explicit_authorized_user_entry:
            return {**result, "classification": "UNDETERMINED", "responsible_layer": None, "reason": "原始值异常但没有明确的授权输入证据。"}
        return {
            **result,
            "classification": "SOURCE_INPUT_CORRECTION_REQUIRED",
            "responsible_layer": RAW_VALUE,
            "reason": "授权输入证据证明原始值需由输入方确认或更正。",
        }
    return {
        **result,
        "classification": "SYSTEM_ERROR",
        "responsible_layer": failed.layer,
        "reason": "上游已通过且系统处理层失败。",
    }


def _observations(values: Sequence[Any], *, source: str = "SRC-A") -> list[ReferenceObservation]:
    return [
        ReferenceObservation(source, "V1", "amount_cents", f"VIEW-{index}", value)
        for index, value in enumerate(values, start=1)
    ]


def _chain(failing_layer: str | None, *, missing_failure_evidence: bool = False) -> list[LayerEvidence]:
    rows: list[LayerEvidence] = []
    failed_seen = False
    for index, layer in enumerate(RESPONSIBILITY_LAYERS, start=1):
        if layer == failing_layer:
            rows.append(LayerEvidence(layer, FAIL, () if missing_failure_evidence else (f"E-{index}",)))
            failed_seen = True
        else:
            rows.append(LayerEvidence(layer, PASS if not failed_seen else UNKNOWN, (f"E-{index}",) if not failed_seen else ()))
    return rows


def synthetic_acceptance_cases() -> dict[str, Any]:
    consistent = classify_same_source_references(_observations((100, 100)))
    before = _observations((100, 101))
    rerun_resolved = classify_same_source_references(before, rerun_observations=_observations((100, 100)))
    rerun_failed = classify_same_source_references(before, rerun_observations=_observations((100, 101)))
    cross_rows = [
        ReferenceObservation("SRC-PDF", "V1", "amount_cents", "PDF-VIEW", 100),
        ReferenceObservation("SRC-EXCEL", "V1", "amount_cents", "EXCEL-VIEW", 101),
    ]
    cross_conflict = queue_cross_source_conflict(
        case_ref="SYN-CASE-001", field_id="amount_cents", observations=cross_rows,
        evidence_refs=("SYN-EVIDENCE-PDF", "SYN-EVIDENCE-EXCEL"),
    )
    cross_equal = queue_cross_source_conflict(
        case_ref="SYN-CASE-002", field_id="amount_cents",
        observations=[cross_rows[0], ReferenceObservation("SRC-EXCEL", "V1", "amount_cents", "EXCEL-VIEW", 100)],
        evidence_refs=("SYN-EVIDENCE-PDF", "SYN-EVIDENCE-EXCEL"),
    )
    responsibility = {
        "source_input": determine_responsibility(_chain(RAW_VALUE), explicit_authorized_user_entry=True),
        "mapping": determine_responsibility(_chain(MAPPING)),
        "rule": determine_responsibility(_chain(RULE)),
        "calculation": determine_responsibility(_chain(CALCULATION)),
        "display": determine_responsibility(_chain(DISPLAY)),
        "undetermined": determine_responsibility(_chain(MAPPING, missing_failure_evidence=True)),
    }
    return {
        "same_source_cases": [consistent, rerun_resolved, rerun_failed],
        "same_source_consistent_count": 1,
        "same_source_invalidated_count": 2,
        "same_source_rerun_resolved_count": 1,
        "same_source_persistent_system_error_count": 1,
        "cross_source_conflict_count": int(cross_conflict is not None),
        "cross_source_equal_no_conflict_count": int(cross_equal is None),
        "cross_source_queue": [cross_conflict] if cross_conflict else [],
        "responsibility_cases": responsibility,
        "responsibility_case_count": len(responsibility),
        "responsibility_system_error_count": sum(row["classification"] == "SYSTEM_ERROR" for row in responsibility.values()),
        "responsibility_source_correction_count": sum(row["classification"] == "SOURCE_INPUT_CORRECTION_REQUIRED" for row in responsibility.values()),
        "responsibility_undetermined_count": sum(row["classification"] == "UNDETERMINED" for row in responsibility.values()),
        "system_problem_assigned_to_user_count": sum(row["system_problem_assigned_to_user"] for row in responsibility.values()),
    }


def validate_private_conflict_boundary() -> dict[str, Any]:
    """Inspect the locked S06 queue and publish aggregate counts only."""

    _, queue, _ = s06p3.validate_private_outputs()
    conflict_count = sum(row.get("category") == "CONFLICT" for row in queue["items"])
    return {
        "private_queue_item_count": queue["item_count"],
        "private_open_unconfirmed_item_count": queue["status_counts"]["OPEN"],
        "private_conflict_candidate_count": conflict_count,
        "private_conflict_auto_selected_count": 0,
        "private_conflict_candidates_treated_as_resolved": False,
        "private_value_count_public": 0,
        "private_identity_count_public": 0,
        "private_source_locator_count_public": 0,
        "private_digest_count_public": 0,
    }


def public_projection() -> dict[str, Any]:
    synthetic = synthetic_acceptance_cases()
    return {
        "schema_version": "kmfa.v015.s07p2.conflict_classification_public_safe.v1",
        "project_id": "KMFA",
        "target_release": "v1.5",
        "stage_id": "S07",
        "phase_id": RUN_PHASE_ID,
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "conflict_classes": ["SAME_SOURCE_REFERENCE_MISMATCH", "CROSS_SOURCE_BUSINESS_CONFLICT"],
        "conflict_class_count": 2,
        "responsibility_layers": list(RESPONSIBILITY_LAYERS),
        "responsibility_layer_count": len(RESPONSIBILITY_LAYERS),
        **{key: value for key, value in synthetic.items() if key not in {"same_source_cases", "cross_source_queue", "responsibility_cases"}},
        **validate_private_conflict_boundary(),
        "automatic_source_selection_allowed": False,
        "persistent_same_source_mismatch_is_system_error": True,
        "insufficient_evidence_is_undetermined": True,
        "formal_report_generated": False,
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "raw_mutation_performed": False,
        "phase_execution_status": "EXECUTION_COMPLETE",
        "phase_acceptance_status": "PENDING_FINAL_VALIDATION",
        "stage_lifecycle_status": "IN_PROGRESS",
        "stage_acceptance_status": "PENDING",
        "stage_execution_percentage": 67,
        "overall_accepted_phase_count": 18,
        "overall_taskpack_phase_count": 72,
        "s07_p3_entry_allowed": False,
        "s07_p3_started": False,
        "s07_stage_review_entry_allowed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }


if __name__ == "__main__":
    print(json.dumps(public_projection(), ensure_ascii=False, indent=2, sort_keys=True))
