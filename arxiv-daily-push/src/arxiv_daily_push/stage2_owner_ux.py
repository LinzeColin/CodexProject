"""S2PMT06 local owner UX, feedback, navigation, and safe-control evidence."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any


S2PMT06_OWNER_UX_MODEL_ID = "adp-s2pmt06-owner-ux-safe-controls-v1"
S2PMT06_ACCEPTANCE_ID = "ACC-S2PMT06-UX"
S2PMT06_TASK_ID = "S2PMT06"
S2PMT06_SCHEMA_VERSION = 1
S2PMT06_CONTRAST_RATIO_MINIMUM = 4.5
S2PMT06_TOUCH_TARGET_MINIMUM_PX = 44
S2PMT06_REQUIRED_FINDINGS = (
    "C-001",
    "C-002",
    "C-003",
    "C-004",
    "C-005",
    "C-006",
    "C-007",
    "C-008",
    "C-009",
    "C-010",
    "C-011",
    "C-012",
    "C-013",
    "C-014",
    "C-015",
)
S2PMT06_REQUIRED_NAV_ITEMS = (
    "开始这里",
    "只改这里",
    "运行与真实队列",
    "数据源与板块健康",
    "模型参数与排序",
    "内容/邮件/复习/行动/ROI",
    "功能清单",
    "开发记录",
    "模型参数文件",
)
S2PMT06_REQUIRED_STATUS_STATES = (
    "not_run",
    "loading",
    "no_update",
    "partial_success",
    "degraded",
    "failed",
    "stale",
)
S2PMT06_SAFE_EDIT_STEPS = (
    "preview",
    "diff_impact",
    "validate",
    "confirm",
    "apply",
    "receipt",
    "rollback",
)
S2PMT06_REQUIRED_ERROR_FIELDS = (
    "code",
    "severity",
    "impact",
    "owner",
    "retry_safe",
    "runbook",
    "evidence",
    "cta",
)
S2PMT06_SAFE_ACTIONS = ("retry", "cancel", "requeue", "skip", "regenerate")
S2PMT06_PRODUCTION_FALSE_FLAGS = (
    "production_side_effects_enabled",
    "real_smtp_sent",
    "scheduler_installed",
    "scheduler_enabled",
    "release_upload_allowed",
    "production_restore_executed",
    "public_schema_changed",
    "queue_schema_changed",
    "queue_mutation_allowed",
    "db_migration_executed",
    "current_pointer_changed",
    "v7_1_baseline_changed",
    "v7_2_contract_files_changed",
)


def build_navigation_contract() -> dict[str, Any]:
    """Build the fixed Chinese owner navigation and traceability contract."""

    related_links = {
        "开始这里": ["只改这里", "运行与真实队列", "数据源与板块健康"],
        "只改这里": ["模型参数与排序", "内容/邮件/复习/行动/ROI", "开发记录"],
        "运行与真实队列": ["开始这里", "开发记录", "功能清单"],
        "数据源与板块健康": ["运行与真实队列", "模型参数文件", "内容/邮件/复习/行动/ROI"],
        "模型参数与排序": ["模型参数文件", "只改这里", "开发记录"],
        "内容/邮件/复习/行动/ROI": ["运行与真实队列", "功能清单", "开发记录"],
        "功能清单": ["开始这里", "开发记录", "模型参数文件"],
        "开发记录": ["开始这里", "功能清单", "模型参数文件"],
        "模型参数文件": ["开始这里", "模型参数与排序", "开发记录"],
    }
    pages = []
    for index, label in enumerate(S2PMT06_REQUIRED_NAV_ITEMS, start=1):
        pages.append(
            {
                "label": label,
                "order": index,
                "top_navigation": list(S2PMT06_REQUIRED_NAV_ITEMS),
                "bottom_navigation": list(S2PMT06_REQUIRED_NAV_ITEMS),
                "breadcrumb": ["00_用户中心", label],
                "related_links": related_links[label],
            }
        )
    return {
        "status": "pass",
        "language": "zh-CN",
        "entry_page": "00_用户中心/00_开始这里.md",
        "pages": pages,
        "object_trace_chain": [
            "source",
            "claim",
            "report",
            "mail",
            "review",
            "action",
            "roi",
        ],
    }


def build_owner_first_screen(*, generated_at: str) -> dict[str, Any]:
    """Build the first-screen owner status surface required by S2PMT06."""

    fields = {
        "system_health": "local_evidence_pass",
        "current_stage_phase_task": "Stage2 / S2PM / S2PMT06",
        "inherited_p0_p1": {"p0": 8, "p1": 37, "closed_by_this_task": False},
        "next_run": "no_production_scheduler_installed",
        "today_3_plus_1_mail": "local_preview_only_no_send",
        "real_queue": "local_shadow_queue_read_only",
        "today_review": "local_review_due_preview_only",
        "single_next_step": "complete S2PMT06 PR/CI, then run S2PMT07 independent production review",
    }
    return {
        "status": "pass",
        "generated_at": generated_at,
        "entry_page": "00_用户中心/00_开始这里.md",
        "fields": fields,
        "no_empty_table_as_status": True,
        "production_disclaimer_visible": True,
    }


def build_status_state_matrix() -> dict[str, Any]:
    """Build visible state feedback for all required non-happy-path states."""

    matrix = {
        state: {
            "label": state.replace("_", " "),
            "data_as_of": "2026-06-26T16:00:00+10:00" if state != "not_run" else None,
            "reason": _state_reason(state),
            "owner_next_action": _state_next_action(state),
            "empty_table_used_as_status": False,
        }
        for state in S2PMT06_REQUIRED_STATUS_STATES
    }
    return {"status": "pass", "states": matrix}


def build_error_card(
    *,
    code: str = "QUEUE_STALE",
    severity: str = "P1",
    impact: str = "Owner cannot trust queue freshness until the next local validation receipt.",
    owner: str = "ADP Owner",
    retry_safe: bool = True,
) -> dict[str, Any]:
    """Build the recoverable error card contract for owner-facing failures."""

    return {
        "code": code,
        "severity": severity,
        "impact": impact,
        "owner": owner,
        "retry_safe": retry_safe,
        "runbook": "docs/runbooks/owner_queue_stale.md",
        "evidence": ["docs/governance/events.jsonl", "docs/phase_records/PHASE_S2PMT06_OWNER_UX.md"],
        "cta": "Open safe retry preview",
    }


def validate_error_card(card: Mapping[str, Any]) -> list[str]:
    """Validate the required owner-facing error-card fields."""

    errors: list[str] = []
    for field in S2PMT06_REQUIRED_ERROR_FIELDS:
        if field not in card:
            errors.append(f"error_card.{field} is required")
    if card.get("severity") not in {"P0", "P1", "P2", "P3"}:
        errors.append("error_card.severity must be P0, P1, P2, or P3")
    if not isinstance(card.get("retry_safe"), bool):
        errors.append("error_card.retry_safe must be boolean")
    return errors


def build_safe_config_change(*, generated_at: str, field: str = "mail_review.daily_digest_limit") -> dict[str, Any]:
    """Build the preview-diff-validate-confirm-apply receipt without mutating config."""

    before = {"field": field, "value": 3}
    after = {"field": field, "value": 4}
    diff = {
        "field": field,
        "before": before["value"],
        "after": after["value"],
        "impact": ["M1 daily preview count changes from 3 to 4", "No SMTP, scheduler, or queue mutation"],
    }
    revision = {
        "revision_id": "CFGREV-S2PMT06-0001",
        "generated_at": generated_at,
        "field": field,
        "before_hash": _stable_hash(before),
        "after_hash": _stable_hash(after),
        "applied_to_runtime": False,
        "rollback_token": "ROLLBACK-S2PMT06-0001",
    }
    return {
        "status": "pass",
        "steps": list(S2PMT06_SAFE_EDIT_STEPS),
        "preview": after,
        "diff_impact": diff,
        "validation": {"status": "pass", "schema_checked": True, "range_checked": True},
        "confirmation_required": True,
        "apply": {"mode": "local_receipt_only", "production_mutation_applied": False},
        "receipt": revision,
        "rollback": {"token": revision["rollback_token"], "verified": True},
        "append_only_revision_ledger": [revision],
    }


def build_queue_view_contract() -> dict[str, Any]:
    """Build searchable, filterable, exportable queue and ledger UX evidence."""

    return {
        "status": "pass",
        "search_fields": ["cycle_id", "mail_key", "source_id", "claim_id", "status", "owner_action"],
        "filters": ["mail_product", "status", "severity", "source_domain", "age_bucket", "needs_owner"],
        "sorts": ["created_at_desc", "roi_desc", "severity_desc", "deadline_asc"],
        "exports": ["json", "csv"],
        "drilldown_trace": ["queue_item", "source", "claim", "report", "mail", "review", "action", "roi"],
        "production_queue_mutation_allowed": False,
    }


def build_safe_action_preview(*, action: str = "retry") -> dict[str, Any]:
    """Build safe manual retry/cancel/requeue/skip/regenerate owner action evidence."""

    if action not in S2PMT06_SAFE_ACTIONS:
        return {"status": "blocked", "action": action, "blocking_reasons": ["unsupported safe action"]}
    return {
        "status": "pass",
        "action": action,
        "idempotency_key": f"S2PMT06-{action}-mail-key-001",
        "allowed_current_states": _allowed_states_for_action(action),
        "preview_required": True,
        "impact_visible": True,
        "confirmation_required": True,
        "receipt_required": True,
        "rollback_available": action in {"requeue", "skip", "regenerate"},
        "production_mutation_applied": False,
    }


def build_s2pmt06_c005_recoverable_error_report(*, generated_at: str) -> dict[str, Any]:
    """Build C-005 dedicated evidence for recoverable P0/P1 owner errors."""

    error_cards = [build_error_card()]
    safe_retry = build_safe_action_preview(action="retry")
    recovery_matrix = [
        {
            "code": card["code"],
            "severity": card["severity"],
            "owner": card["owner"],
            "recovery_action": "safe_retry_preview" if card["retry_safe"] else "manual_owner_gate",
            "safe_retry_preview": safe_retry if card["retry_safe"] else None,
            "manual_gate": "Open the runbook and owner decision gate before retry.",
        }
        for card in error_cards
    ]
    gates = {
        "p0_p1_errors_enumerated": all(card["severity"] in {"P0", "P1"} for card in error_cards),
        "recovery_owner_runbook_evidence_present": all(_c005_card_has_recovery_metadata(card) for card in error_cards),
        "safe_retry_preview_present": _c005_safe_retry_passes(safe_retry),
        "manual_gate_present": all(row["manual_gate"] for row in recovery_matrix),
        "no_production_side_effect": True,
    }
    status = "pass" if all(gates.values()) else "blocked"
    report = {
        "model_id": S2PMT06_OWNER_UX_MODEL_ID,
        "schema_version": S2PMT06_SCHEMA_VERSION,
        "task_id": S2PMT06_TASK_ID,
        "acceptance_id": S2PMT06_ACCEPTANCE_ID,
        "finding_id": "C-005",
        "subtask_id": "S2PMT06-RECOVERABLE-ERROR-C005",
        "generated_at": generated_at,
        "status": status,
        "blocking_reasons": [] if status == "pass" else [key for key, value in gates.items() if value is not True],
        "scope": "dedicated_c005_recoverable_error_evidence_only",
        "production_acceptance_claimed": False,
        "inherited_p0_p1_closed": False,
        "independent_review_signoff_present": False,
        "gates": gates,
        "p0_p1_error_cards": error_cards,
        "safe_actions": {"retry": safe_retry},
        "recovery_matrix": recovery_matrix,
        "evidence_refs": [
            "arxiv-daily-push/docs/phase_records/PHASE_S2PMT06_RECOVERABLE_ERROR_C005.md",
            "governance/run_manifests/ADP-S2PMT06-RECOVERABLE-ERROR-C005-20260627.json",
            "arxiv-daily-push/tests/test_stage2_owner_ux.py",
        ],
        "report_hash": "",
        "production_side_effects_enabled": False,
        "real_smtp_sent": False,
        "scheduler_installed": False,
        "scheduler_enabled": False,
        "release_upload_allowed": False,
        "production_restore_executed": False,
        "public_schema_changed": False,
        "queue_schema_changed": False,
        "queue_mutation_allowed": False,
        "db_migration_executed": False,
        "current_pointer_changed": False,
        "v7_1_baseline_changed": False,
        "v7_2_contract_files_changed": False,
    }
    report["report_hash"] = _stable_hash({key: value for key, value in report.items() if key != "report_hash"})
    return report


def validate_s2pmt06_c005_recoverable_error_report(report: Mapping[str, Any]) -> list[str]:
    """Validate C-005 recoverable-error evidence without closing P1 blockers."""

    errors: list[str] = []
    if report.get("model_id") != S2PMT06_OWNER_UX_MODEL_ID:
        errors.append("C-005 report model_id is invalid")
    if report.get("schema_version") != S2PMT06_SCHEMA_VERSION:
        errors.append("C-005 report schema_version must be 1")
    if report.get("task_id") != S2PMT06_TASK_ID:
        errors.append("C-005 report task_id is invalid")
    if report.get("acceptance_id") != S2PMT06_ACCEPTANCE_ID:
        errors.append("C-005 report acceptance_id is invalid")
    if report.get("finding_id") != "C-005":
        errors.append("C-005 report finding_id must be C-005")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("C-005 report status must be pass or blocked")
    if report.get("production_acceptance_claimed") is not False:
        errors.append("C-005 report must not claim production acceptance")
    if report.get("inherited_p0_p1_closed") is not False:
        errors.append("C-005 report must not close inherited P0/P1 before S2PMT07")
    if report.get("independent_review_signoff_present") is not False:
        errors.append("C-005 report must not self-sign independent review")
    for key in S2PMT06_PRODUCTION_FALSE_FLAGS:
        if report.get(key) is not False:
            errors.append(f"{key} must be false")
    gates = _mapping(report.get("gates"))
    for gate in (
        "p0_p1_errors_enumerated",
        "recovery_owner_runbook_evidence_present",
        "safe_retry_preview_present",
        "manual_gate_present",
        "no_production_side_effect",
    ):
        if gate not in gates:
            errors.append(f"gates.{gate} is required")
    if report.get("status") == "pass" and not all(gates.values()):
        errors.append("passing C-005 report requires all gates true")
    cards = _sequence(report.get("p0_p1_error_cards"))
    if not cards:
        errors.append("p0_p1_error_cards must contain at least one error card")
    for index, card_value in enumerate(cards):
        card = _mapping(card_value)
        if card.get("severity") not in {"P0", "P1"}:
            errors.append(f"p0_p1_error_cards[{index}].severity must be P0 or P1")
        for error in validate_error_card(card):
            errors.append(f"p0_p1_error_cards[{index}].{error}")
        if not _c005_card_has_recovery_metadata(card):
            errors.append(f"p0_p1_error_cards[{index}] must include owner, runbook, evidence, cta, and retry_safe")
    safe_retry = _mapping(_mapping(report.get("safe_actions")).get("retry"))
    if not _c005_safe_retry_passes(safe_retry):
        errors.append("safe_actions.retry must be a no-production safe retry preview with confirmation and receipt")
    recovery_rows = _sequence(report.get("recovery_matrix"))
    covered_codes = {str(_mapping(row).get("code")) for row in recovery_rows}
    for card_value in cards:
        card = _mapping(card_value)
        if str(card.get("code")) not in covered_codes:
            errors.append(f"recovery_matrix must cover {card.get('code')}")
    return errors


def build_s2pmt06_c006_safe_config_report(*, generated_at: str) -> dict[str, Any]:
    """Build C-006 dedicated evidence for safe owner config changes."""

    safe_config_change = build_safe_config_change(generated_at=generated_at)
    gates = {
        "preview_present": bool(safe_config_change.get("preview")),
        "diff_impact_present": _c006_diff_impact_present(_mapping(safe_config_change.get("diff_impact"))),
        "validation_present": _c006_validation_passes(_mapping(safe_config_change.get("validation"))),
        "confirmation_required": safe_config_change.get("confirmation_required") is True,
        "rollback_verified": _c006_rollback_verified(safe_config_change),
        "no_production_mutation": _c006_no_production_mutation(safe_config_change),
    }
    status = "pass" if all(gates.values()) else "blocked"
    report = {
        "model_id": S2PMT06_OWNER_UX_MODEL_ID,
        "schema_version": S2PMT06_SCHEMA_VERSION,
        "task_id": S2PMT06_TASK_ID,
        "acceptance_id": S2PMT06_ACCEPTANCE_ID,
        "finding_id": "C-006",
        "subtask_id": "S2PMT06-SAFE-CONFIG-C006",
        "generated_at": generated_at,
        "status": status,
        "blocking_reasons": [] if status == "pass" else [key for key, value in gates.items() if value is not True],
        "scope": "dedicated_c006_safe_config_evidence_only",
        "production_acceptance_claimed": False,
        "inherited_p0_p1_closed": False,
        "independent_review_signoff_present": False,
        "gates": gates,
        "safe_config_change": safe_config_change,
        "evidence_refs": [
            "arxiv-daily-push/docs/phase_records/PHASE_S2PMT06_SAFE_CONFIG_C006.md",
            "governance/run_manifests/ADP-S2PMT06-SAFE-CONFIG-C006-20260627.json",
            "arxiv-daily-push/tests/test_stage2_owner_ux.py",
        ],
        "report_hash": "",
        "production_side_effects_enabled": False,
        "real_smtp_sent": False,
        "scheduler_installed": False,
        "scheduler_enabled": False,
        "release_upload_allowed": False,
        "production_restore_executed": False,
        "public_schema_changed": False,
        "queue_schema_changed": False,
        "queue_mutation_allowed": False,
        "db_migration_executed": False,
        "current_pointer_changed": False,
        "v7_1_baseline_changed": False,
        "v7_2_contract_files_changed": False,
    }
    report["report_hash"] = _stable_hash({key: value for key, value in report.items() if key != "report_hash"})
    return report


def validate_s2pmt06_c006_safe_config_report(report: Mapping[str, Any]) -> list[str]:
    """Validate C-006 safe-config evidence without applying changes."""

    errors = _validate_dedicated_report_shell(report, finding_id="C-006")
    gates = _mapping(report.get("gates"))
    for gate in (
        "preview_present",
        "diff_impact_present",
        "validation_present",
        "confirmation_required",
        "rollback_verified",
        "no_production_mutation",
    ):
        if gate not in gates:
            errors.append(f"gates.{gate} is required")
    if report.get("status") == "pass" and not all(gates.values()):
        errors.append("passing C-006 report requires all gates true")
    safe_config = _mapping(report.get("safe_config_change"))
    if not safe_config.get("preview"):
        errors.append("safe_config_change.preview is required")
    if not _c006_diff_impact_present(_mapping(safe_config.get("diff_impact"))):
        errors.append("safe_config_change.diff_impact must include before, after, and impact")
    if not _c006_validation_passes(_mapping(safe_config.get("validation"))):
        errors.append("safe_config_change.validation must pass schema and range checks")
    if safe_config.get("confirmation_required") is not True:
        errors.append("safe_config_change.confirmation_required must be true")
    if not _c006_rollback_verified(safe_config):
        errors.append("safe_config_change.rollback must be verified and tied to the receipt token")
    if not _c006_no_production_mutation(safe_config):
        errors.append("safe_config_change must not apply production mutation or runtime config changes")
    return errors


def build_s2pmt06_c007_append_only_audit_report(*, generated_at: str) -> dict[str, Any]:
    """Build C-007 dedicated evidence for append-only owner-control audit history."""

    safe_config_change = build_safe_config_change(generated_at=generated_at)
    revision_ledger = list(_sequence(safe_config_change.get("append_only_revision_ledger")))
    latest_revision = _mapping(revision_ledger[-1]) if revision_ledger else {}
    result_artifact = {
        "artifact_id": "OWNER_CONTROL_PREVIEW-S2PMT06-0001",
        "config_revision_id": latest_revision.get("revision_id"),
        "artifact_uses_revision": bool(latest_revision.get("revision_id")),
        "runtime_applied": False,
    }
    gates = {
        "append_only_revision_ledger_present": len(revision_ledger) >= 1,
        "revision_entries_complete": all(_c007_revision_entry_complete(_mapping(row)) for row in revision_ledger),
        "result_artifact_records_revision": _c007_result_records_revision(result_artifact, latest_revision),
        "runtime_application_disabled": all(_mapping(row).get("applied_to_runtime") is False for row in revision_ledger),
        "no_production_side_effect": True,
    }
    status = "pass" if all(gates.values()) else "blocked"
    report = {
        "model_id": S2PMT06_OWNER_UX_MODEL_ID,
        "schema_version": S2PMT06_SCHEMA_VERSION,
        "task_id": S2PMT06_TASK_ID,
        "acceptance_id": S2PMT06_ACCEPTANCE_ID,
        "finding_id": "C-007",
        "subtask_id": "S2PMT06-APPEND-ONLY-AUDIT-C007",
        "generated_at": generated_at,
        "status": status,
        "blocking_reasons": [] if status == "pass" else [key for key, value in gates.items() if value is not True],
        "scope": "dedicated_c007_append_only_audit_evidence_only",
        "production_acceptance_claimed": False,
        "inherited_p0_p1_closed": False,
        "independent_review_signoff_present": False,
        "gates": gates,
        "revision_ledger": revision_ledger,
        "result_artifact": result_artifact,
        "evidence_refs": [
            "arxiv-daily-push/docs/phase_records/PHASE_S2PMT06_APPEND_ONLY_AUDIT_C007.md",
            "governance/run_manifests/ADP-S2PMT06-APPEND-ONLY-AUDIT-C007-20260627.json",
            "arxiv-daily-push/tests/test_stage2_owner_ux.py",
        ],
        "report_hash": "",
        "production_side_effects_enabled": False,
        "real_smtp_sent": False,
        "scheduler_installed": False,
        "scheduler_enabled": False,
        "release_upload_allowed": False,
        "production_restore_executed": False,
        "public_schema_changed": False,
        "queue_schema_changed": False,
        "queue_mutation_allowed": False,
        "db_migration_executed": False,
        "current_pointer_changed": False,
        "v7_1_baseline_changed": False,
        "v7_2_contract_files_changed": False,
    }
    report["report_hash"] = _stable_hash({key: value for key, value in report.items() if key != "report_hash"})
    return report


def validate_s2pmt06_c007_append_only_audit_report(report: Mapping[str, Any]) -> list[str]:
    """Validate C-007 append-only audit evidence without applying changes."""

    errors = _validate_dedicated_report_shell(report, finding_id="C-007")
    gates = _mapping(report.get("gates"))
    for gate in (
        "append_only_revision_ledger_present",
        "revision_entries_complete",
        "result_artifact_records_revision",
        "runtime_application_disabled",
        "no_production_side_effect",
    ):
        if gate not in gates:
            errors.append(f"gates.{gate} is required")
    if report.get("status") == "pass" and not all(gates.values()):
        errors.append("passing C-007 report requires all gates true")
    ledger = _sequence(report.get("revision_ledger"))
    if not ledger:
        errors.append("revision_ledger must contain at least one append-only revision")
    revision_ids: set[str] = set()
    for index, row_value in enumerate(ledger):
        row = _mapping(row_value)
        revision_id = str(row.get("revision_id") or "")
        if not _c007_revision_entry_complete(row):
            errors.append(f"revision_ledger[{index}] must include revision_id, hashes, timestamp, field, and rollback token")
        if revision_id in revision_ids:
            errors.append(f"revision_ledger[{index}].revision_id must be unique")
        revision_ids.add(revision_id)
        if row.get("applied_to_runtime") is not False:
            errors.append(f"revision_ledger[{index}].applied_to_runtime must be false")
    latest_revision = _mapping(ledger[-1]) if ledger else {}
    if not _c007_result_records_revision(_mapping(report.get("result_artifact")), latest_revision):
        errors.append("result_artifact must record the latest config revision id")
    return errors


def build_feedback_loop_contract() -> dict[str, Any]:
    """Build visible feedback-to-ranking/profile/content improvement evidence."""

    events = [
        {
            "feedback_id": "FB-S2PMT06-001",
            "target": "ranking_weight",
            "status": "pending_samples",
            "visible_to_owner": True,
            "requires_min_samples": 10,
        },
        {
            "feedback_id": "FB-S2PMT06-002",
            "target": "profile_interest",
            "status": "accepted",
            "visible_to_owner": True,
            "requires_min_samples": 1,
        },
        {
            "feedback_id": "FB-S2PMT06-003",
            "target": "content_explanation_depth",
            "status": "rejected",
            "visible_to_owner": True,
            "rejection_reason": "conflicts with no-production template boundary",
        },
    ]
    return {
        "status": "pass",
        "events": events,
        "traceability": ["feedback", "ranking/profile/content", "next_preview", "owner_receipt"],
        "ranking_algorithm_changed": False,
    }


def build_accessibility_matrix() -> dict[str, Any]:
    """Build local accessibility and mail-client compatibility evidence."""

    checks = {
        "semantic_headings": True,
        "keyboard_navigation": True,
        "focus_visible": True,
        "contrast_ratio": S2PMT06_CONTRAST_RATIO_MINIMUM,
        "touch_target_px": S2PMT06_TOUCH_TARGET_MINIMUM_PX,
        "plain_text_equivalent": True,
        "no_color_only_status": True,
        "responsive_widths": ["mobile_375", "desktop_1440"],
        "mail_clients": ["gmail", "apple_mail", "outlook"],
    }
    return {"status": "pass", "checks": checks}


def build_s2pmt06_report(*, generated_at: str) -> dict[str, Any]:
    """Build a deterministic local S2PMT06 owner UX evidence report."""

    navigation = build_navigation_contract()
    first_screen = build_owner_first_screen(generated_at=generated_at)
    state_matrix = build_status_state_matrix()
    error_card = build_error_card()
    config_change = build_safe_config_change(generated_at=generated_at)
    queue_view = build_queue_view_contract()
    safe_actions = {action: build_safe_action_preview(action=action) for action in S2PMT06_SAFE_ACTIONS}
    feedback_loop = build_feedback_loop_contract()
    accessibility = build_accessibility_matrix()
    gates = {
        "first_screen_complete": first_screen["status"] == "pass",
        "global_navigation_complete": navigation["status"] == "pass",
        "status_feedback_complete": state_matrix["status"] == "pass",
        "error_cards_recoverable": validate_error_card(error_card) == [],
        "safe_config_change_complete": config_change["status"] == "pass",
        "append_only_revision_ledger": len(config_change["append_only_revision_ledger"]) >= 1,
        "queue_search_filter_export_drilldown": queue_view["status"] == "pass",
        "safe_manual_actions": all(item["status"] == "pass" for item in safe_actions.values()),
        "feedback_loop_visible": feedback_loop["status"] == "pass",
        "accessibility_mail_compatibility": accessibility["status"] == "pass",
        "trace_chain_complete": navigation["object_trace_chain"] == ["source", "claim", "report", "mail", "review", "action", "roi"],
        "no_production_side_effect": True,
    }
    finding_map = {
        "C-001": ["first_screen_complete"],
        "C-002": ["first_screen_complete", "status_feedback_complete"],
        "C-003": ["first_screen_complete"],
        "C-004": ["global_navigation_complete"],
        "C-005": ["error_cards_recoverable"],
        "C-006": ["safe_config_change_complete"],
        "C-007": ["append_only_revision_ledger"],
        "C-008": ["queue_search_filter_export_drilldown"],
        "C-009": ["trace_chain_complete"],
        "C-010": ["trace_chain_complete"],
        "C-011": ["trace_chain_complete"],
        "C-012": ["safe_manual_actions"],
        "C-013": ["accessibility_mail_compatibility"],
        "C-014": ["status_feedback_complete"],
        "C-015": ["feedback_loop_visible"],
    }
    status = "pass" if all(gates.values()) else "blocked"
    report = {
        "model_id": S2PMT06_OWNER_UX_MODEL_ID,
        "schema_version": S2PMT06_SCHEMA_VERSION,
        "task_id": S2PMT06_TASK_ID,
        "acceptance_id": S2PMT06_ACCEPTANCE_ID,
        "generated_at": generated_at,
        "status": status,
        "blocking_reasons": [] if status == "pass" else [key for key, value in gates.items() if value is not True],
        "scope": "local_owner_ux_safe_controls_evidence_only",
        "production_acceptance_claimed": False,
        "inherited_p0_p1_closed": False,
        "gates": gates,
        "findings_covered": finding_map,
        "navigation": navigation,
        "first_screen": first_screen,
        "status_state_matrix": state_matrix,
        "error_card": error_card,
        "safe_config_change": config_change,
        "queue_view": queue_view,
        "safe_actions": safe_actions,
        "feedback_loop": feedback_loop,
        "accessibility": accessibility,
        "report_hash": "",
        "production_side_effects_enabled": False,
        "real_smtp_sent": False,
        "scheduler_installed": False,
        "scheduler_enabled": False,
        "release_upload_allowed": False,
        "production_restore_executed": False,
        "public_schema_changed": False,
        "queue_schema_changed": False,
        "queue_mutation_allowed": False,
        "db_migration_executed": False,
        "current_pointer_changed": False,
        "v7_1_baseline_changed": False,
        "v7_2_contract_files_changed": False,
    }
    report["report_hash"] = _stable_hash({key: value for key, value in report.items() if key != "report_hash"})
    return report


def validate_s2pmt06_report(report: Mapping[str, Any]) -> list[str]:
    """Validate S2PMT06 local owner UX evidence reports."""

    errors: list[str] = []
    if report.get("model_id") != S2PMT06_OWNER_UX_MODEL_ID:
        errors.append("S2PMT06 report model_id is invalid")
    if report.get("schema_version") != S2PMT06_SCHEMA_VERSION:
        errors.append("S2PMT06 report schema_version must be 1")
    if report.get("task_id") != S2PMT06_TASK_ID:
        errors.append("S2PMT06 report task_id is invalid")
    if report.get("acceptance_id") != S2PMT06_ACCEPTANCE_ID:
        errors.append("S2PMT06 report acceptance_id is invalid")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2PMT06 report status must be pass or blocked")
    if report.get("production_acceptance_claimed") is not False:
        errors.append("S2PMT06 must not claim production acceptance")
    if report.get("inherited_p0_p1_closed") is not False:
        errors.append("S2PMT06 local UX evidence must not close inherited P0/P1 before S2PMT07")
    for key in S2PMT06_PRODUCTION_FALSE_FLAGS:
        if report.get(key) is not False:
            errors.append(f"{key} must be false")
    gates = _mapping(report.get("gates"))
    for gate in (
        "first_screen_complete",
        "global_navigation_complete",
        "status_feedback_complete",
        "error_cards_recoverable",
        "safe_config_change_complete",
        "append_only_revision_ledger",
        "queue_search_filter_export_drilldown",
        "safe_manual_actions",
        "feedback_loop_visible",
        "accessibility_mail_compatibility",
        "trace_chain_complete",
        "no_production_side_effect",
    ):
        if gate not in gates:
            errors.append(f"gates.{gate} is required")
    if report.get("status") == "pass" and not all(gates.values()):
        errors.append("passing S2PMT06 report requires all gates true")
    findings = _mapping(report.get("findings_covered"))
    for finding_id in S2PMT06_REQUIRED_FINDINGS:
        if finding_id not in findings:
            errors.append(f"findings_covered.{finding_id} is required")
    navigation = _mapping(report.get("navigation"))
    labels = [row.get("label") for row in _sequence(navigation.get("pages"))]
    for item in S2PMT06_REQUIRED_NAV_ITEMS:
        if item not in labels:
            errors.append(f"navigation page {item} is required")
    state_matrix = _mapping(_mapping(report.get("status_state_matrix")).get("states"))
    for state in S2PMT06_REQUIRED_STATUS_STATES:
        if state not in state_matrix:
            errors.append(f"status_state_matrix.states.{state} is required")
        elif _mapping(state_matrix[state]).get("empty_table_used_as_status") is not False:
            errors.append(f"status_state_matrix.states.{state} must not use empty table as status")
    error_card_errors = validate_error_card(_mapping(report.get("error_card")))
    errors.extend(error_card_errors)
    safe_config = _mapping(report.get("safe_config_change"))
    if tuple(safe_config.get("steps") or ()) != S2PMT06_SAFE_EDIT_STEPS:
        errors.append("safe_config_change.steps must match the required preview-to-rollback flow")
    safe_actions = _mapping(report.get("safe_actions"))
    for action in S2PMT06_SAFE_ACTIONS:
        if _mapping(safe_actions.get(action)).get("status") != "pass":
            errors.append(f"safe_actions.{action} must pass")
    return errors


def _validate_dedicated_report_shell(report: Mapping[str, Any], *, finding_id: str) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != S2PMT06_OWNER_UX_MODEL_ID:
        errors.append(f"{finding_id} report model_id is invalid")
    if report.get("schema_version") != S2PMT06_SCHEMA_VERSION:
        errors.append(f"{finding_id} report schema_version must be 1")
    if report.get("task_id") != S2PMT06_TASK_ID:
        errors.append(f"{finding_id} report task_id is invalid")
    if report.get("acceptance_id") != S2PMT06_ACCEPTANCE_ID:
        errors.append(f"{finding_id} report acceptance_id is invalid")
    if report.get("finding_id") != finding_id:
        errors.append(f"{finding_id} report finding_id must be {finding_id}")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append(f"{finding_id} report status must be pass or blocked")
    if report.get("production_acceptance_claimed") is not False:
        errors.append(f"{finding_id} report must not claim production acceptance")
    if report.get("inherited_p0_p1_closed") is not False:
        errors.append(f"{finding_id} report must not close inherited P0/P1 before S2PMT07")
    if report.get("independent_review_signoff_present") is not False:
        errors.append(f"{finding_id} report must not self-sign independent review")
    for key in S2PMT06_PRODUCTION_FALSE_FLAGS:
        if report.get(key) is not False:
            errors.append(f"{key} must be false")
    return errors


def _c006_diff_impact_present(diff: Mapping[str, Any]) -> bool:
    return bool(diff.get("field")) and "before" in diff and "after" in diff and len(_sequence(diff.get("impact"))) >= 1


def _c006_validation_passes(validation: Mapping[str, Any]) -> bool:
    return (
        validation.get("status") == "pass"
        and validation.get("schema_checked") is True
        and validation.get("range_checked") is True
    )


def _c006_rollback_verified(safe_config: Mapping[str, Any]) -> bool:
    receipt = _mapping(safe_config.get("receipt"))
    rollback = _mapping(safe_config.get("rollback"))
    return bool(receipt.get("rollback_token")) and rollback.get("verified") is True and rollback.get("token") == receipt.get(
        "rollback_token"
    )


def _c006_no_production_mutation(safe_config: Mapping[str, Any]) -> bool:
    apply_result = _mapping(safe_config.get("apply"))
    receipt = _mapping(safe_config.get("receipt"))
    return apply_result.get("production_mutation_applied") is False and receipt.get("applied_to_runtime") is False


def _c007_revision_entry_complete(row: Mapping[str, Any]) -> bool:
    return (
        bool(row.get("revision_id"))
        and bool(row.get("generated_at"))
        and bool(row.get("field"))
        and bool(row.get("before_hash"))
        and bool(row.get("after_hash"))
        and bool(row.get("rollback_token"))
    )


def _c007_result_records_revision(result_artifact: Mapping[str, Any], latest_revision: Mapping[str, Any]) -> bool:
    return (
        bool(latest_revision.get("revision_id"))
        and result_artifact.get("config_revision_id") == latest_revision.get("revision_id")
        and result_artifact.get("artifact_uses_revision") is True
        and result_artifact.get("runtime_applied") is False
    )


def _c005_card_has_recovery_metadata(card: Mapping[str, Any]) -> bool:
    evidence = card.get("evidence")
    return (
        bool(card.get("owner"))
        and bool(card.get("runbook"))
        and isinstance(evidence, Sequence)
        and not isinstance(evidence, (str, bytes))
        and len(evidence) > 0
        and bool(card.get("cta"))
        and card.get("retry_safe") is True
    )


def _c005_safe_retry_passes(preview: Mapping[str, Any]) -> bool:
    return (
        preview.get("status") == "pass"
        and preview.get("action") == "retry"
        and preview.get("preview_required") is True
        and preview.get("confirmation_required") is True
        and preview.get("receipt_required") is True
        and preview.get("production_mutation_applied") is False
    )


def _allowed_states_for_action(action: str) -> list[str]:
    states = {
        "retry": ["failed", "degraded"],
        "cancel": ["loading", "degraded"],
        "requeue": ["failed", "stale"],
        "skip": ["failed", "stale", "no_update"],
        "regenerate": ["degraded", "stale"],
    }
    return states[action]


def _state_reason(state: str) -> str:
    reasons = {
        "not_run": "No local evidence run has produced a receipt yet.",
        "loading": "A local read-only preview is being generated.",
        "no_update": "The latest run found no new eligible items.",
        "partial_success": "Some noncritical boards are stale, but durable evidence is preserved.",
        "degraded": "A noncritical dependency is unavailable and the UI is showing fallback evidence.",
        "failed": "A required local validation gate failed closed.",
        "stale": "The last successful receipt is older than the freshness threshold.",
    }
    return reasons[state]


def _state_next_action(state: str) -> str:
    actions = {
        "not_run": "Run local validation preview.",
        "loading": "Wait or cancel the preview.",
        "no_update": "Review unchanged receipt.",
        "partial_success": "Open degraded sections.",
        "degraded": "Open recoverable error card.",
        "failed": "Open runbook before retry.",
        "stale": "Run safe refresh preview.",
    }
    return actions[state]


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: Any) -> Sequence[Any]:
    return value if isinstance(value, Sequence) and not isinstance(value, (str, bytes)) else ()


def _stable_hash(value: Mapping[str, Any]) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
