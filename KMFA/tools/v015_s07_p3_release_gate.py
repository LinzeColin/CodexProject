#!/usr/bin/env python3
"""KMFA v1.5 S07-P3 human-readable release and regression gate.

This module does not publish a report. It defines when a report candidate may
be used internally, when confirmation is still required, and when use must be
blocked. Difference closure is accepted only after corrective evidence,
recalculation, and review. Every change reruns every previously passed project.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

from KMFA.tools import v015_s07_p1_zero_delta_validator as s07p1
from KMFA.tools import v015_s07_p2_conflict_classification as s07p2


RUN_PHASE_ID = "V015_S07_P3_RELEASE_GATE"
ROADMAP_PHASE_ID = "S07-P3"
TASK_ID = "KMFA-V015-S07-P3-RELEASE-GATE-20260715"
ACCEPTANCE_ID = "ACC-KMFA-V015-S07-P3-RELEASE-GATE"
VERSION = "1.5.0-dev-s07p3"
SCHEMA_VERSION = "kmfa.v015.s07p3.release_gate.v1"

INTERNAL_USE_LABEL = "可内部使用"
CONFIRMATION_REQUIRED_LABEL = "需确认"
UNAVAILABLE_LABEL = "暂不可使用"
HUMAN_STATUS_LABELS = (
    INTERNAL_USE_LABEL,
    CONFIRMATION_REQUIRED_LABEL,
    UNAVAILABLE_LABEL,
)
TECHNICAL_ABBREVIATIONS = (
    "Q1", "Q2", "Q3", "Q4", "Q5", "NO_GO", "PASS", "FAIL",
)

HUMAN_CONFIRMATION = "HUMAN_CONFIRMATION"
RULE_CORRECTION = "RULE_CORRECTION"
SOURCE_FILE_CORRECTION = "SOURCE_FILE_CORRECTION"
SYSTEM_FIX = "SYSTEM_FIX"
CLOSURE_KINDS = (
    HUMAN_CONFIRMATION,
    RULE_CORRECTION,
    SOURCE_FILE_CORRECTION,
    SYSTEM_FIX,
)


class ReleaseGateError(ValueError):
    """Fail-closed release-gate input or evidence error."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class ReportGateInput:
    critical_difference_count: int
    unresolved_conflict_count: int
    unresolved_system_error_count: int
    undetermined_responsibility_count: int
    noncritical_confirmation_count: int
    recalculation_passed: bool
    review_passed: bool
    regression_passed: bool

    def __post_init__(self) -> None:
        counts = (
            self.critical_difference_count,
            self.unresolved_conflict_count,
            self.unresolved_system_error_count,
            self.undetermined_responsibility_count,
            self.noncritical_confirmation_count,
        )
        if any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in counts):
            raise ReleaseGateError("NONNEGATIVE_COUNTS_REQUIRED", "门禁计数必须是非负整数。")
        for value in (self.recalculation_passed, self.review_passed, self.regression_passed):
            if not isinstance(value, bool):
                raise ReleaseGateError("BOOLEAN_GATE_REQUIRED", "重算、复核和回归状态必须是布尔值。")


def _contains_technical_abbreviation(text: str) -> bool:
    return any(re.search(rf"(?<![A-Z0-9_]){re.escape(token)}(?![A-Z0-9_])", text) for token in TECHNICAL_ABBREVIATIONS)


def determine_report_status(value: ReportGateInput) -> dict[str, Any]:
    """Return a plain-Chinese UI status and a fail-closed release decision."""

    blockers: list[str] = []
    if value.critical_difference_count:
        blockers.append("仍有关键差异没有关闭。")
    if value.unresolved_conflict_count:
        blockers.append("仍有不同来源之间的冲突需要人工处理。")
    if value.unresolved_system_error_count:
        blockers.append("仍有系统错误没有修复。")
    if not value.recalculation_passed:
        blockers.append("更正后的重新计算尚未通过。")
    if not value.review_passed:
        blockers.append("更正后的复核尚未通过。")
    if not value.regression_passed:
        blockers.append("历史项目回归尚未全部通过。")

    if blockers:
        label = UNAVAILABLE_LABEL
        explanation = "；".join(blockers)
        internal_use_allowed = False
        release_candidate_allowed = False
    elif value.undetermined_responsibility_count or value.noncritical_confirmation_count:
        label = CONFIRMATION_REQUIRED_LABEL
        explanation = "没有关键阻断，但仍有事项需要人工确认后才能使用。"
        internal_use_allowed = False
        release_candidate_allowed = False
    else:
        label = INTERNAL_USE_LABEL
        explanation = "关键差异已关闭，重算、复核和历史项目回归均已通过。"
        internal_use_allowed = True
        release_candidate_allowed = True

    ui_payload = {
        "显示状态": label,
        "说明": explanation,
        "下一步": (
            "可以在内部使用，并继续遵守项目最终发布流程。"
            if internal_use_allowed else "按说明完成处理后重新计算、复核并再次运行门禁。"
        ),
    }
    ui_text = json.dumps(ui_payload, ensure_ascii=False, sort_keys=True)
    if _contains_technical_abbreviation(ui_text):
        raise ReleaseGateError("TECHNICAL_ABBREVIATION_IN_UI", "用户界面不得显示技术等级缩写。")
    return {
        "schema_version": SCHEMA_VERSION,
        "display_label_zh": label,
        "plain_language_reason_zh": explanation,
        "ui_payload": ui_payload,
        "ui_technical_abbreviation_count": 0,
        "internal_use_allowed": internal_use_allowed,
        "release_candidate_allowed": release_candidate_allowed,
        "formal_report_release_allowed": release_candidate_allowed,
        "blocking_reason_count": len(blockers),
        "blocking_reasons_zh": blockers,
    }


def close_difference(
    difference: Mapping[str, Any],
    closure: Mapping[str, Any],
) -> dict[str, Any]:
    """Close one difference only after correction, recalculation, and review."""

    difference_id = str(difference.get("difference_id") or "").strip()
    if not difference_id or difference.get("status") != "OPEN":
        raise ReleaseGateError("OPEN_DIFFERENCE_REQUIRED", "只能关闭有稳定标识的开放差异。")
    kind = str(closure.get("closure_kind") or "")
    if kind not in CLOSURE_KINDS:
        raise ReleaseGateError("CLOSURE_KIND_REQUIRED", "关闭方式必须是四种已登记流程之一。")

    required_by_kind = {
        HUMAN_CONFIRMATION: "human_confirmation_evidence_ref",
        RULE_CORRECTION: "corrected_rule_version_ref",
        SOURCE_FILE_CORRECTION: "corrected_source_version_ref",
        SYSTEM_FIX: "system_fix_version_ref",
    }
    specific_ref = str(closure.get(required_by_kind[kind]) or "").strip()
    recalculation_receipt = str(closure.get("recalculation_receipt_ref") or "").strip()
    review_receipt = str(closure.get("review_receipt_ref") or "").strip()
    post_count = closure.get("post_recalculation_difference_count")
    requested_status = closure.get("requested_status")
    if requested_status != "CLOSED":
        raise ReleaseGateError("CLOSED_STATUS_REQUIRED", "关闭流程必须明确请求关闭状态。")
    if not specific_ref:
        raise ReleaseGateError("CORRECTIVE_EVIDENCE_REQUIRED", "关闭必须提供对应更正或确认的证据。")
    if not recalculation_receipt or not review_receipt:
        raise ReleaseGateError("RECALCULATION_AND_REVIEW_REQUIRED", "关闭后必须有重算和复核记录。")
    if isinstance(post_count, bool) or not isinstance(post_count, int) or post_count != 0:
        raise ReleaseGateError("ZERO_POST_RECALCULATION_DIFFERENCE_REQUIRED", "重算后该差异必须为零。")
    return {
        "schema_version": SCHEMA_VERSION,
        "difference_id": difference_id,
        "previous_status": "OPEN",
        "status": "CLOSED",
        "closure_kind": kind,
        "corrective_evidence_ref": specific_ref,
        "recalculation_receipt_ref": recalculation_receipt,
        "review_receipt_ref": review_receipt,
        "post_recalculation_difference_count": 0,
        "status_only_closure": False,
        "recalculation_performed": True,
        "review_performed": True,
    }


def evaluate_regression_gate(
    *,
    change_ref: str,
    previously_passed_project_refs: Sequence[str],
    rerun_results: Mapping[str, bool],
) -> dict[str, Any]:
    """Require every previously passed project to rerun after every change."""

    if not change_ref.strip():
        raise ReleaseGateError("CHANGE_REF_REQUIRED", "每次变更必须有稳定标识。")
    project_refs = list(previously_passed_project_refs)
    if not project_refs or len(project_refs) != len(set(project_refs)) or any(not ref for ref in project_refs):
        raise ReleaseGateError("PASSED_PROJECT_SET_REQUIRED", "历史已通过项目集合不能为空或重复。")
    result_refs = set(rerun_results)
    expected_refs = set(project_refs)
    if result_refs != expected_refs:
        raise ReleaseGateError("ALL_PASSED_PROJECTS_MUST_RERUN", "变更后必须重跑全部历史已通过项目。")
    if any(not isinstance(value, bool) for value in rerun_results.values()):
        raise ReleaseGateError("BOOLEAN_REGRESSION_RESULT_REQUIRED", "回归结果必须是布尔值。")
    passed_count = sum(rerun_results.values())
    total = len(project_refs)
    all_passed = passed_count == total
    return {
        "schema_version": SCHEMA_VERSION,
        "change_ref": change_ref,
        "automatic_rerun_required": True,
        "previously_passed_project_count": total,
        "selected_for_rerun_count": total,
        "rerun_completed_count": len(rerun_results),
        "regression_pass_count": passed_count,
        "regression_fail_count": total - passed_count,
        "regression_pass_rate_bps": passed_count * 10000 // total,
        "historical_projects_100_percent_passed": all_passed,
        "merge_allowed": all_passed,
    }


def _closure_fixture(kind: str) -> dict[str, Any]:
    specific = {
        HUMAN_CONFIRMATION: ("human_confirmation_evidence_ref", "E-HUMAN"),
        RULE_CORRECTION: ("corrected_rule_version_ref", "RULE-V2"),
        SOURCE_FILE_CORRECTION: ("corrected_source_version_ref", "SOURCE-V2"),
        SYSTEM_FIX: ("system_fix_version_ref", "SYSTEM-V2"),
    }[kind]
    return {
        "closure_kind": kind,
        specific[0]: specific[1],
        "recalculation_receipt_ref": f"RECALC-{kind}",
        "review_receipt_ref": f"REVIEW-{kind}",
        "post_recalculation_difference_count": 0,
        "requested_status": "CLOSED",
    }


def synthetic_acceptance_cases() -> dict[str, Any]:
    usable = determine_report_status(ReportGateInput(0, 0, 0, 0, 0, True, True, True))
    confirm = determine_report_status(ReportGateInput(0, 0, 0, 1, 1, True, True, True))
    unavailable = determine_report_status(ReportGateInput(1, 1, 0, 0, 0, True, True, True))
    difference = {"difference_id": "SYN-DIFF-001", "status": "OPEN"}
    closures = [close_difference(difference, _closure_fixture(kind)) for kind in CLOSURE_KINDS]

    status_only_rejected = False
    try:
        close_difference(difference, {"closure_kind": HUMAN_CONFIRMATION, "requested_status": "CLOSED"})
    except ReleaseGateError:
        status_only_rejected = True

    missing_recalculation_rejected = False
    bad = _closure_fixture(SYSTEM_FIX)
    bad["recalculation_receipt_ref"] = ""
    try:
        close_difference(difference, bad)
    except ReleaseGateError:
        missing_recalculation_rejected = True

    passed = evaluate_regression_gate(
        change_ref="SYN-CHANGE-PASS",
        previously_passed_project_refs=("P-1", "P-2", "P-3"),
        rerun_results={"P-1": True, "P-2": True, "P-3": True},
    )
    failed = evaluate_regression_gate(
        change_ref="SYN-CHANGE-FAIL",
        previously_passed_project_refs=("P-1", "P-2", "P-3"),
        rerun_results={"P-1": True, "P-2": False, "P-3": True},
    )
    missing_project_rejected = False
    try:
        evaluate_regression_gate(
            change_ref="SYN-CHANGE-INCOMPLETE",
            previously_passed_project_refs=("P-1", "P-2", "P-3"),
            rerun_results={"P-1": True, "P-2": True},
        )
    except ReleaseGateError:
        missing_project_rejected = True
    return {
        "status_cases": [usable, confirm, unavailable],
        "status_label_count": len(HUMAN_STATUS_LABELS),
        "status_labels_zh": list(HUMAN_STATUS_LABELS),
        "ui_technical_abbreviation_count": sum(row["ui_technical_abbreviation_count"] for row in (usable, confirm, unavailable)),
        "critical_difference_blocked_count": int(not unavailable["formal_report_release_allowed"]),
        "closure_cases": closures,
        "closure_kind_count": len(CLOSURE_KINDS),
        "closure_success_count": sum(row["status"] == "CLOSED" for row in closures),
        "status_only_closure_rejected": status_only_rejected,
        "missing_recalculation_rejected": missing_recalculation_rejected,
        "passing_regression": passed,
        "failing_regression": failed,
        "missing_project_rerun_rejected": missing_project_rejected,
    }


def validate_private_regression_gate() -> dict[str, Any]:
    """Rerun the eight accepted private projects and expose aggregates only."""

    private = s07p1.validate_private_golden_scope()
    count = private["private_project_count"]
    project_refs = tuple(f"PRIVATE-GOLDEN-{index:03d}" for index in range(1, count + 1))
    result = evaluate_regression_gate(
        change_ref="S07P3-PRIVATE-REGRESSION",
        previously_passed_project_refs=project_refs,
        rerun_results={ref: private["private_zero_difference"] for ref in project_refs},
    )
    return {
        "private_historical_project_count": count,
        "private_selected_for_rerun_count": result["selected_for_rerun_count"],
        "private_regression_pass_count": result["regression_pass_count"],
        "private_regression_fail_count": result["regression_fail_count"],
        "private_regression_pass_rate_bps": result["regression_pass_rate_bps"],
        "private_historical_projects_100_percent_passed": result["historical_projects_100_percent_passed"],
        "private_merge_allowed": result["merge_allowed"],
        "private_open_unconfirmed_item_count": private["open_unconfirmed_item_count"],
        "private_identity_count_public": 0,
        "private_money_value_count_public": 0,
        "private_source_locator_count_public": 0,
        "private_digest_count_public": 0,
    }


def current_private_release_status() -> dict[str, Any]:
    private_conflicts = s07p2.validate_private_conflict_boundary()
    status = determine_report_status(ReportGateInput(
        critical_difference_count=private_conflicts["private_conflict_candidate_count"],
        unresolved_conflict_count=private_conflicts["private_conflict_candidate_count"],
        unresolved_system_error_count=0,
        undetermined_responsibility_count=0,
        noncritical_confirmation_count=private_conflicts["private_open_unconfirmed_item_count"],
        recalculation_passed=True,
        review_passed=True,
        regression_passed=True,
    ))
    return {
        "current_report_display_label_zh": status["display_label_zh"],
        "current_formal_report_release_allowed": status["formal_report_release_allowed"],
        "current_internal_use_allowed": status["internal_use_allowed"],
        "current_blocking_reason_count": status["blocking_reason_count"],
        "current_private_open_unconfirmed_item_count": private_conflicts["private_open_unconfirmed_item_count"],
        "current_private_conflict_candidate_count": private_conflicts["private_conflict_candidate_count"],
        "current_private_conflict_auto_selected_count": private_conflicts["private_conflict_auto_selected_count"],
    }


def public_projection() -> dict[str, Any]:
    synthetic = synthetic_acceptance_cases()
    return {
        "schema_version": "kmfa.v015.s07p3.release_gate_public_safe.v1",
        "project_id": "KMFA",
        "target_release": "v1.5",
        "stage_id": "S07",
        "phase_id": RUN_PHASE_ID,
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "status_label_count": synthetic["status_label_count"],
        "status_labels_zh": synthetic["status_labels_zh"],
        "ui_technical_abbreviation_count": synthetic["ui_technical_abbreviation_count"],
        "critical_difference_blocked_count": synthetic["critical_difference_blocked_count"],
        "closure_kind_count": synthetic["closure_kind_count"],
        "closure_success_count": synthetic["closure_success_count"],
        "status_only_closure_rejected": synthetic["status_only_closure_rejected"],
        "missing_recalculation_rejected": synthetic["missing_recalculation_rejected"],
        "synthetic_regression_pass_rate_bps": synthetic["passing_regression"]["regression_pass_rate_bps"],
        "synthetic_regression_failure_merge_allowed": synthetic["failing_regression"]["merge_allowed"],
        "missing_project_rerun_rejected": synthetic["missing_project_rerun_rejected"],
        **validate_private_regression_gate(),
        **current_private_release_status(),
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "raw_mutation_performed": False,
        "phase_execution_status": "EXECUTION_COMPLETE",
        "phase_acceptance_status": "PENDING_FINAL_VALIDATION",
        "stage_lifecycle_status": "IN_PROGRESS",
        "stage_acceptance_status": "PENDING",
        "stage_execution_percentage": 100,
        "overall_accepted_phase_count": 19,
        "overall_taskpack_phase_count": 72,
        "s07_stage_review_entry_allowed": False,
        "s07_stage_review_started": False,
        "s08_p1_entry_allowed": False,
        "formal_report_generated": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }


if __name__ == "__main__":
    print(json.dumps(public_projection(), ensure_ascii=False, indent=2, sort_keys=True))
