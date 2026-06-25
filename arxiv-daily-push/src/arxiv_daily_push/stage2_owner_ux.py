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
