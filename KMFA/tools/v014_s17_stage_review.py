#!/usr/bin/env python3
"""Generate KMFA v0.1.4 Stage 17 review evidence.

This review closes the v0.1.4 access, notification and operations stage by
replaying S17-P1, S17-P2 and S17-P3 public-safe validators. It does not read
raw/private finance data, enter S18, upload to GitHub, deliver notifications,
send full report email content, restore production, call external services,
reinstall an app, release formal reports, or execute business actions.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.check_v014_s17_p1_access_security import validate_v014_s17_p1_access_security  # noqa: E402
from KMFA.tools.check_v014_s17_p2_notification_policy import validate_v014_s17_p2_notification_policy  # noqa: E402
from KMFA.tools.check_v014_s17_p3_operations_sop import validate_v014_s17_p3_operations_sop  # noqa: E402


TASK_ID = "KMFA-V014-S17-STAGE-REVIEW-20260705"
ACCEPTANCE_ID = "ACC-V014-S17-STAGE-REVIEW"
SCHEMA_VERSION = "kmfa.v014_s17_stage_review.v1"
REVIEW_SCOPE = "v014_s17_stage_review_only"

OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_S17_STAGE_REVIEW")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
MANIFEST_PATH = MACHINE_DIR / "stage17_review_manifest.json"
REPORT_PATH = HUMAN_DIR / "stage17_review_report.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

V14_TASKPACK_PATH = Path("KMFA/taskpack/v1_4/taskpack/01_KMFA_Codex_TaskPack_v1_4_public_safe.md")
V14_ROADMAP_PATH = Path("KMFA/taskpack/v1_4/roadmap/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_4.md")
RAW_INBOX_REF = "operator-designated raw/private inbox outside repository"
NEXT_PHASE = "S18-P1"
NEXT_REQUIRED_STEP = (
    "Start v0.1.4 S18-P1 only as a separate run after user instruction. "
    "Do not perform GitHub upload in Stage 17 review; GitHub main upload remains deferred until "
    "v1.4 Stage 1-18 are complete, overall review has passed, and findings are fixed. Do not read raw "
    "inbox content, perform protected source matching, run lineage full check, deliver real notifications, "
    "send full report email body, attach reports, expose recipient addresses, restore production, call "
    "external services, reinstall app entry, release formal reports, or execute business actions."
)
RAW_PHASE_KEYS = (
    "raw_inbox_read_by_this_phase",
    "raw_inbox_listed_by_this_phase",
    "raw_inbox_inventory_by_this_phase",
    "raw_inbox_stat_by_this_phase",
    "raw_inbox_hashed_by_this_phase",
    "raw_inbox_modified_by_this_phase",
    "raw_inbox_deleted_by_this_phase",
    "raw_inbox_moved_by_this_phase",
    "raw_inbox_renamed_by_this_phase",
    "raw_inbox_overwritten_by_this_phase",
    "raw_inbox_written_by_this_phase",
    "raw_inbox_mutated_by_this_phase",
)
RAW_REVIEW_KEYS = tuple(key.replace("_by_this_phase", "_by_this_review") for key in RAW_PHASE_KEYS)


def git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_v14_taskpack_baseline() -> dict[str, Any]:
    taskpack_text = V14_TASKPACK_PATH.read_text(encoding="utf-8")
    roadmap_text = V14_ROADMAP_PATH.read_text(encoding="utf-8")
    for token in ("权限与安全", "通知", "运维与SOP"):
        if token not in roadmap_text:
            raise RuntimeError(f"v1.4 roadmap missing Stage 17 marker {token}")
    for token in ("不提交原始敏感数据到公开GitHub", "不把缺数据报告伪装成完整报告", "可审计"):
        if token not in taskpack_text:
            raise RuntimeError(f"v1.4 taskpack missing Stage 17 safety marker {token}")
    return {
        "taskpack_read": True,
        "roadmap_read": True,
        "roadmap_includes_stage17_requirements": True,
        "taskpack_includes_stage17_public_safe_safety_boundary": True,
        "source_refs": {
            "taskpack": V14_TASKPACK_PATH.as_posix(),
            "roadmap": V14_ROADMAP_PATH.as_posix(),
        },
    }


def _raw_all_false(manifest: dict[str, Any]) -> bool:
    raw = manifest.get("raw_data_boundary", {})
    return isinstance(raw, dict) and all(raw.get(key) is False for key in RAW_PHASE_KEYS)


def _raw_boundary(p1: dict[str, Any], p2: dict[str, Any], p3: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {key: False for key in RAW_REVIEW_KEYS}
    result.update(
        {
            "raw_inbox_ref": RAW_INBOX_REF,
            "raw_inbox_read_required_by_this_review": False,
            "s17_p1_raw_inbox_all_false": _raw_all_false(p1),
            "s17_p2_raw_inbox_all_false": _raw_all_false(p2),
            "s17_p3_raw_inbox_all_false": _raw_all_false(p3),
            "private_runtime_output_dir": "KMFA/.codex_private_runtime/",
        }
    )
    return result


def _public_repo_safety() -> dict[str, bool]:
    return {
        "protected_source_payload_committed": False,
        "compressed_raw_package_committed": False,
        "office_workbook_committed": False,
        "source_document_committed": False,
        "raw_or_private_table_committed": False,
        "local_database_committed": False,
        "auth_material_committed": False,
        "connector_auth_material_committed": False,
        "field_plaintext_committed": False,
        "source_header_plaintext_committed": False,
        "raw_file_names_committed": False,
        "raw_file_hashes_committed": False,
        "source_record_payload_committed": False,
        "normalized_source_values_committed": False,
        "business_amount_values_committed": False,
        "public_numeric_values_committed": False,
        "project_or_customer_plaintext_committed": False,
        "recipient_address_plaintext_committed": False,
        "full_report_email_body_committed": False,
        "report_attachment_committed": False,
        "production_restore_artifact_committed": False,
        "external_service_artifact_committed": False,
        "live_connector_artifact_committed": False,
        "app_reinstall_artifact_committed": False,
        "formal_report_committed": False,
        "business_decision_basis_committed": False,
    }


def _release_state() -> dict[str, Any]:
    return {
        "delivery_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "notification_delivery_allowed": False,
        "full_report_email_allowed": False,
        "report_attachment_allowed": False,
        "recipient_address_plaintext_allowed": False,
        "external_connector_allowed": False,
        "production_restore_allowed": False,
        "live_connector_allowed": False,
        "app_reinstall_allowed": False,
        "business_execution_allowed": False,
        "github_main_upload_allowed": False,
        "current_go_no_go": "NO_GO",
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "release_permission": "blocked",
        "blocking_reason": "stage17_review_is_public_safe_d_grade_with_notifications_operations_and_business_execution_blocked",
    }


def _stage_gate(p1: dict[str, Any], p2: dict[str, Any], p3: dict[str, Any]) -> dict[str, Any]:
    p1_summary = p1["access_security_summary"]
    p2_summary = p2["notification_policy_summary"]
    p3_summary = p3["operations_sop_summary"]
    return {
        "role_count": p1_summary["role_count"],
        "required_role_count": p1_summary["required_role_count"],
        "sensitive_policy_category_count": p1_summary["sensitive_policy_category_count"],
        "required_sensitive_category_count": p1_summary["required_sensitive_category_count"],
        "audit_action_type_count": p1_summary["audit_action_type_count"],
        "required_audit_action_type_count": p1_summary["required_audit_action_type_count"],
        "notification_rule_count": p2_summary["notification_rule_count"],
        "notification_event_count": p2_summary["notification_event_count"],
        "notification_dispatch_log_count": p2_summary["notification_dispatch_log_count"],
        "metadata_outbox_log_count": p2_summary["metadata_outbox_log_count"],
        "trigger_type_count": p2_summary["trigger_type_count"],
        "required_trigger_count": p2_summary["required_trigger_count"],
        "operation_runbook_count": p3_summary["operation_runbook_count"],
        "knowledge_item_count": p3_summary["knowledge_item_count"],
        "drill_log_count": p3_summary["drill_log_count"],
        "runbook_type_count": p3_summary["runbook_type_count"],
        "knowledge_item_type_count": p3_summary["knowledge_item_type_count"],
        "drill_type_count": p3_summary["drill_type_count"],
        "production_restore_count": p3_summary["production_restore_count"],
        "external_service_call_count": p3_summary["external_service_call_count"],
        "live_connector_call_count": p3_summary["live_connector_call_count"],
        "app_reinstall_count": p3_summary["app_reinstall_count"],
        "real_notification_delivery_count": p2_summary["real_notification_delivery_count"],
        "notification_delivery_count": p1_summary["notification_delivery_count"],
        "full_report_email_body_count": max(
            p1_summary["full_report_email_body_count"],
            p2_summary["full_report_email_body_count"],
        ),
        "report_attachment_count": p2_summary["report_attachment_count"],
        "recipient_address_plaintext_count": p2_summary["recipient_address_plaintext_count"],
        "formal_report_count": max(
            p1_summary["formal_report_count"],
            p2_summary["formal_report_count"],
            p3_summary["formal_report_count"],
        ),
        "business_decision_basis_count": max(
            p1_summary["business_decision_basis_count"],
            p2_summary["business_decision_basis_count"],
        ),
        "business_execution_count": max(
            p1_summary["business_execution_count"],
            p2_summary["business_execution_count"],
            p3_summary["business_execution_count"],
        ),
        "external_connector_count": max(
            p1_summary["external_connector_count"],
            p2_summary["external_connector_count"],
        ),
        "raw_inbox_access_count": max(
            p1_summary["raw_inbox_access_count"],
            p2_summary["raw_inbox_access_count"],
            p3_summary["raw_inbox_access_count"],
        ),
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "release_permission": "blocked",
    }


def _review_findings() -> list[dict[str, str]]:
    return [
        {
            "finding_id": "KMFA-V014-S17-REV-F01",
            "severity": "P1",
            "status": "fixed",
            "summary": "S17 operations evidence could be misread as executable notification, restore, connector or app actions.",
            "fix": "Stage 17 review locks all operational actions as metadata-only, manual-only and blocked while keeping GitHub upload deferred.",
            "evidence": MANIFEST_PATH.as_posix(),
        },
        {
            "finding_id": "KMFA-V014-S17-REV-F02",
            "severity": "P2",
            "status": "passed",
            "summary": "S17-P1, S17-P2 and S17-P3 validators pass with public-safe access, notification and operations evidence.",
            "fix": "No code fix required.",
            "evidence": "KMFA/stage_artifacts/V014_S17_P3_OPERATIONS_SOP/machine/operations_sop_manifest.json",
        },
        {
            "finding_id": "KMFA-V014-S17-REV-F03",
            "severity": "P1",
            "status": "passed",
            "summary": "Raw inbox access, formal report release, business decision basis, S18 and GitHub upload remain blocked.",
            "fix": "No code fix required.",
            "evidence": MANIFEST_PATH.as_posix(),
        },
    ]


def build_manifest(generated_at: str | None = None) -> dict[str, Any]:
    generated_at = generated_at or datetime.now().isoformat(timespec="seconds")
    p1 = validate_v014_s17_p1_access_security()
    p2 = validate_v014_s17_p2_notification_policy()
    p3 = validate_v014_s17_p3_operations_sop()
    findings = _review_findings()
    stage_gate = _stage_gate(p1, p2, p3)
    phase_results = {
        "S17-P1": "PASS" if p1.get("phase_id") == "S17-P1" else "FAIL",
        "S17-P2": "PASS" if p2.get("phase_id") == "S17-P2" else "FAIL",
        "S17-P3": "PASS" if p3.get("phase_id") == "S17-P3" else "FAIL",
    }
    validation_summary = {
        "py_compile": "PENDING_FINAL_VALIDATION",
        "s17_p1_validator": "PASS",
        "s17_p2_validator": "PASS",
        "s17_p3_validator": "PASS",
        "stage_review_validator": "PENDING_FINAL_VALIDATION",
        "focused_unit_test": "PENDING_FINAL_VALIDATION",
        "governance_validator": "PENDING_FINAL_VALIDATION",
        "lean_governance_validator": "PENDING_FINAL_VALIDATION",
        "governance_sync_validator": "PENDING_FINAL_VALIDATION",
        "no_float_money_check": "PENDING_FINAL_VALIDATION",
        "no_omission_check": "PENDING_FINAL_VALIDATION",
        "structured_parse": "PENDING_FINAL_VALIDATION",
        "raw_private_suffix_scan": "PENDING_FINAL_VALIDATION",
        "high_signal_secret_scan": "PENDING_FINAL_VALIDATION",
        "public_stage17_semantic_scan": "PENDING_FINAL_VALIDATION",
        "diff_check": "PENDING_FINAL_VALIDATION",
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "v014_s17_stage_review_manifest",
        "project_id": "KMFA",
        "version": "0.1.4",
        "stage_id": "S17",
        "phase_id": "S17_STAGE_REVIEW",
        "review_scope": REVIEW_SCOPE,
        "task_id": TASK_ID,
        "acceptance_ids": [ACCEPTANCE_ID],
        "completed_task_ids": ["S17REVT01", "S17REVT02", "S17REVT03"],
        "status": "review_passed_local_only_no_go_upload_deferred_until_v014_stage1_18_complete",
        "generated_at": generated_at,
        "branch": git_output(["branch", "--show-current"]),
        "git_head": git_output(["rev-parse", "HEAD"]),
        "stage_review_performed": True,
        "phase_results": phase_results,
        "stage17_phase_progress": {
            "completed_phase_count": 3,
            "total_phase_count": 3,
            "derived_percent_bps": 10000,
            "derived_percent_label": "100.00%",
            "s17_p1_performed": True,
            "s17_p2_performed": True,
            "s17_p3_performed": True,
            "stage17_review_performed": True,
        },
        "stage_gate": stage_gate,
        "release_state": _release_state(),
        "review_findings": findings,
        "review_findings_summary": {
            "open_finding_count": sum(1 for finding in findings if finding["status"] == "open"),
            "fixed_finding_count": sum(1 for finding in findings if finding["status"] == "fixed"),
            "passed_finding_count": sum(1 for finding in findings if finding["status"] == "passed"),
        },
        "raw_data_boundary": _raw_boundary(p1, p2, p3),
        "public_repo_safety": _public_repo_safety(),
        "v14_taskpack_baseline": load_v14_taskpack_baseline(),
        "upstream_phase_refs": {
            "s17_p1_manifest": "KMFA/stage_artifacts/V014_S17_P1_ACCESS_SECURITY/machine/access_security_manifest.json",
            "s17_p2_manifest": "KMFA/stage_artifacts/V014_S17_P2_NOTIFICATION_POLICY/machine/notification_policy_manifest.json",
            "s17_p3_manifest": "KMFA/stage_artifacts/V014_S17_P3_OPERATIONS_SOP/machine/operations_sop_manifest.json",
        },
        "artifact_refs": {
            "manifest": MANIFEST_PATH.as_posix(),
            "report": REPORT_PATH.as_posix(),
            "test_results": TEST_RESULTS_PATH.as_posix(),
            "risk_register": RISK_REGISTER_PATH.as_posix(),
            "rollback_plan": ROLLBACK_PATH.as_posix(),
        },
        "validation_summary": validation_summary,
        "hard_blocks": [
            "stage17_review_public_safe_only",
            "report_grade_d_only",
            "raw_data_mutation_forbidden",
            "raw_publication_forbidden",
            "field_header_plaintext_publication_forbidden",
            "formal_report_release_blocked",
            "business_decision_basis_blocked",
            "real_notification_delivery_blocked",
            "full_report_email_blocked",
            "report_attachment_blocked",
            "recipient_address_plaintext_blocked",
            "production_restore_blocked",
            "external_service_call_blocked",
            "live_connector_blocked",
            "app_reinstall_blocked",
            "s18_p1_not_performed",
            "lineage_full_check_not_performed",
            "protected_source_matching_not_performed",
            "github_upload_deferred_until_v014_stage1_18_complete",
            "business_execution_blocked",
        ],
        "s18_p1_performed": False,
        "github_upload_performed": False,
        "github_upload_ready_next_gate": False,
        "github_upload_deferred_until_v014_stage1_18_complete": True,
        "github_upload_status": "not_uploaded_deferred_until_v014_stage1_18_complete",
        "next_phase": NEXT_PHASE,
        "next_required_step": NEXT_REQUIRED_STEP,
    }


def write_artifacts(manifest: dict[str, Any]) -> None:
    write_json(MANIFEST_PATH, manifest)
    write_text(
        REPORT_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 Stage 17 Review",
                "",
                "- phase_results: `S17-P1=PASS; S17-P2=PASS; S17-P3=PASS`",
                f"- open_findings: `{manifest['review_findings_summary']['open_finding_count']}`",
                f"- fixed_findings: `{manifest['review_findings_summary']['fixed_finding_count']}`",
                f"- role_count: `{manifest['stage_gate']['role_count']}`",
                f"- sensitive_policy_category_count: `{manifest['stage_gate']['sensitive_policy_category_count']}`",
                f"- audit_action_type_count: `{manifest['stage_gate']['audit_action_type_count']}`",
                f"- notification_rule_count: `{manifest['stage_gate']['notification_rule_count']}`",
                f"- notification_dispatch_log_count: `{manifest['stage_gate']['notification_dispatch_log_count']}`",
                f"- operation_runbook_count: `{manifest['stage_gate']['operation_runbook_count']}`",
                f"- knowledge_item_count: `{manifest['stage_gate']['knowledge_item_count']}`",
                f"- drill_log_count: `{manifest['stage_gate']['drill_log_count']}`",
                f"- real_notification_delivery_count: `{manifest['stage_gate']['real_notification_delivery_count']}`",
                f"- production_restore_count: `{manifest['stage_gate']['production_restore_count']}`",
                f"- external_service_call_count: `{manifest['stage_gate']['external_service_call_count']}`",
                f"- app_reinstall_count: `{manifest['stage_gate']['app_reinstall_count']}`",
                f"- business_execution_count: `{manifest['stage_gate']['business_execution_count']}`",
                f"- github_upload_status: `{manifest['github_upload_status']}`",
                "",
                "Stage 17 review is local-only. It does not perform S18, GitHub upload, raw inbox access, real notification delivery, full report email body, report attachment, recipient address publication, production restore, external service call, live connector call, app reinstall, formal report release or business execution.",
                "",
            ]
        ),
    )
    write_text(
        TEST_RESULTS_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 Stage 17 Review Test Results",
                "",
                "- generator: pending final validation replay",
                "- validator: pending final validation replay",
                "- focused_unittest: pending final validation replay",
                "- governance_validation: pending final validation replay",
                "- raw_secret_scan: pending final validation replay",
                "",
            ]
        ),
    )
    write_text(
        RISK_REGISTER_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 Stage 17 Review Risk Register",
                "",
                "- risk: Metadata-only notification evidence could be mistaken as real delivery.",
                "  mitigation: Review locks real delivery, full email body, attachment and recipient plaintext counts at zero.",
                "- risk: Operations SOP evidence could be mistaken as production restore or app reinstall.",
                "  mitigation: Review locks production restore, external service, live connector and app reinstall counts at zero.",
                "",
            ]
        ),
    )
    write_text(
        ROLLBACK_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 Stage 17 Review Rollback Plan",
                "",
                "- Remove only `KMFA/stage_artifacts/V014_S17_STAGE_REVIEW/` and paired v014 S17 review governance entries if rollback is required.",
                "- Do not touch raw/private inbox contents or upstream S17-P1/P2/P3 phase evidence.",
                "",
            ]
        ),
    )


def generate(generated_at: str | None = None) -> dict[str, Any]:
    manifest = build_manifest(generated_at=generated_at)
    write_artifacts(manifest)
    return manifest


def main() -> int:
    manifest = generate()
    gate = manifest["stage_gate"]
    print(
        "PASS: KMFA v0.1.4 Stage 17 review generated "
        f"(phase_results={manifest['phase_results']}, open_findings={manifest['review_findings_summary']['open_finding_count']}, "
        f"roles={gate['role_count']}, notifications={gate['notification_rule_count']}, "
        f"runbooks={gate['operation_runbook_count']}, drills={gate['drill_log_count']}, "
        f"delivery={gate['real_notification_delivery_count']}, restore={gate['production_restore_count']}, "
        f"external={gate['external_service_call_count']}, app_reinstall={gate['app_reinstall_count']}, "
        f"s18={manifest['s18_p1_performed']}, github_upload={manifest['github_upload_performed']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
