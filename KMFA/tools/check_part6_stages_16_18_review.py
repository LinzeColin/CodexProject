#!/usr/bin/env python3
"""Validate KMFA post-S18 Part 6 review evidence for Stages 16-18."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


DEFAULT_MANIFEST = Path("KMFA/stage_artifacts/PART6_STAGES_16_18_REVIEW/machine/part6_review_manifest.json")

REQUIRED_STAGE_ARTIFACTS = (
    "KMFA/stage_artifacts/S16_GITHUB_UPLOAD/human/github_upload_record.md",
    "KMFA/stage_artifacts/S16_GITHUB_UPLOAD/machine/stage16_upload_manifest.json",
    "KMFA/stage_artifacts/S16_P1_subcontract_procurement_aggregation/human/s16_p1_completion_record.md",
    "KMFA/stage_artifacts/S16_P1_subcontract_procurement_aggregation/human/test_results.md",
    "KMFA/stage_artifacts/S16_P1_subcontract_procurement_aggregation/machine/s16_p1_manifest.json",
    "KMFA/stage_artifacts/S16_P2_project_status_lifecycle/human/s16_p2_completion_record.md",
    "KMFA/stage_artifacts/S16_P2_project_status_lifecycle/human/test_results.md",
    "KMFA/stage_artifacts/S16_P2_project_status_lifecycle/machine/s16_p2_manifest.json",
    "KMFA/stage_artifacts/S16_P3_customer_business_analysis/human/s16_p3_completion_record.md",
    "KMFA/stage_artifacts/S16_P3_customer_business_analysis/human/test_results.md",
    "KMFA/stage_artifacts/S16_P3_customer_business_analysis/machine/s16_p3_manifest.json",
    "KMFA/stage_artifacts/S16_STAGE_REVIEW/human/stage16_review_report.md",
    "KMFA/stage_artifacts/S16_STAGE_REVIEW/human/test_results.md",
    "KMFA/stage_artifacts/S16_STAGE_REVIEW/machine/stage16_review_manifest.json",
    "KMFA/stage_artifacts/S17_GITHUB_UPLOAD/human/github_upload_record.md",
    "KMFA/stage_artifacts/S17_GITHUB_UPLOAD/machine/stage17_upload_manifest.json",
    "KMFA/stage_artifacts/S17_P1_access_security/human/s17_p1_completion_record.md",
    "KMFA/stage_artifacts/S17_P1_access_security/human/test_results.md",
    "KMFA/stage_artifacts/S17_P1_access_security/machine/s17_p1_manifest.json",
    "KMFA/stage_artifacts/S17_P2_notification/human/s17_p2_completion_record.md",
    "KMFA/stage_artifacts/S17_P2_notification/human/test_results.md",
    "KMFA/stage_artifacts/S17_P2_notification/machine/s17_p2_manifest.json",
    "KMFA/stage_artifacts/S17_P3_operations_sop/human/s17_p3_completion_record.md",
    "KMFA/stage_artifacts/S17_P3_operations_sop/human/test_results.md",
    "KMFA/stage_artifacts/S17_P3_operations_sop/machine/s17_p3_manifest.json",
    "KMFA/stage_artifacts/S17_STAGE_REVIEW/human/stage17_review_report.md",
    "KMFA/stage_artifacts/S17_STAGE_REVIEW/human/test_results.md",
    "KMFA/stage_artifacts/S17_STAGE_REVIEW/machine/stage17_review_manifest.json",
    "KMFA/stage_artifacts/S18_GITHUB_UPLOAD/human/github_upload_record.md",
    "KMFA/stage_artifacts/S18_GITHUB_UPLOAD/machine/stage18_upload_manifest.json",
    "KMFA/stage_artifacts/S18_P1_precision_stress/human/html_sample_reading_record.md",
    "KMFA/stage_artifacts/S18_P1_precision_stress/human/s18_p1_completion_record.md",
    "KMFA/stage_artifacts/S18_P1_precision_stress/human/test_results.md",
    "KMFA/stage_artifacts/S18_P1_precision_stress/machine/s18_p1_manifest.json",
    "KMFA/stage_artifacts/S18_P2_full_regression_acceptance/human/go_no_go_report.md",
    "KMFA/stage_artifacts/S18_P2_full_regression_acceptance/human/html_ui_regression_record.md",
    "KMFA/stage_artifacts/S18_P2_full_regression_acceptance/human/s18_p2_completion_record.md",
    "KMFA/stage_artifacts/S18_P2_full_regression_acceptance/human/test_results.md",
    "KMFA/stage_artifacts/S18_P2_full_regression_acceptance/machine/s18_p2_manifest.json",
    "KMFA/stage_artifacts/S18_P3_integration_preparation/human/next_stage_backlog.md",
    "KMFA/stage_artifacts/S18_P3_integration_preparation/human/opme_entry_integration_plan.md",
    "KMFA/stage_artifacts/S18_P3_integration_preparation/human/read_only_connector_plan.md",
    "KMFA/stage_artifacts/S18_P3_integration_preparation/human/s18_p3_completion_record.md",
    "KMFA/stage_artifacts/S18_P3_integration_preparation/human/test_results.md",
    "KMFA/stage_artifacts/S18_P3_integration_preparation/machine/s18_p3_manifest.json",
    "KMFA/stage_artifacts/S18_STAGE_REVIEW/human/stage18_review_report.md",
    "KMFA/stage_artifacts/S18_STAGE_REVIEW/human/test_results.md",
    "KMFA/stage_artifacts/S18_STAGE_REVIEW/machine/stage18_review_manifest.json",
)

REQUIRED_BASELINE_REFS = (
    "KMFA/taskpack/v1_2/01_KMFA_Codex_TaskPack_v1_2_完整防遗漏_含HTML验收样板.md",
    "KMFA/taskpack/v1_2/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_2.md",
    "KMFA/tools/subcontract_procurement_aggregation.py",
    "KMFA/tools/check_s16_p1_subcontract_procurement.py",
    "KMFA/tests/test_subcontract_procurement_aggregation.py",
    "KMFA/tools/project_status_lifecycle.py",
    "KMFA/tools/check_s16_p2_project_status_lifecycle.py",
    "KMFA/tests/test_project_status_lifecycle.py",
    "KMFA/tools/customer_business_analysis.py",
    "KMFA/tools/check_s16_p3_customer_business_analysis.py",
    "KMFA/tests/test_customer_business_analysis.py",
    "KMFA/tools/check_s16_stage_review.py",
    "KMFA/tests/test_s16_stage_review.py",
    "KMFA/metadata/reports/subcontract_procurement_aggregation_manifest.json",
    "KMFA/metadata/reports/subcontract_procurement_source_lanes.jsonl",
    "KMFA/metadata/reports/subcontract_project_matches.jsonl",
    "KMFA/metadata/reports/subcontract_unallocated_cost_pool.jsonl",
    "KMFA/metadata/reports/subcontract_anomaly_candidates.jsonl",
    "KMFA/metadata/reports/project_status_lifecycle_manifest.json",
    "KMFA/metadata/reports/project_status_source_lanes.jsonl",
    "KMFA/metadata/reports/project_lifecycle_records.jsonl",
    "KMFA/metadata/reports/project_lifecycle_exception_items.jsonl",
    "KMFA/metadata/reports/project_lifecycle_handoff_guards.jsonl",
    "KMFA/metadata/reports/customer_business_analysis_manifest.json",
    "KMFA/metadata/reports/customer_analysis_source_lanes.jsonl",
    "KMFA/metadata/reports/customer_operating_summaries.jsonl",
    "KMFA/metadata/reports/customer_analysis_exception_items.jsonl",
    "KMFA/tools/access_security_policy.py",
    "KMFA/tools/check_s17_p1_access_security.py",
    "KMFA/tests/test_access_security_policy.py",
    "KMFA/tools/notification_reminders.py",
    "KMFA/tools/check_s17_p2_notifications.py",
    "KMFA/tests/test_notification_reminders.py",
    "KMFA/tools/operations_sop.py",
    "KMFA/tools/check_s17_p3_operations_sop.py",
    "KMFA/tests/test_operations_sop.py",
    "KMFA/tools/check_s17_stage_review.py",
    "KMFA/tests/test_s17_stage_review.py",
    "KMFA/metadata/security/access_security_policy_manifest.json",
    "KMFA/metadata/security/role_permission_matrix.jsonl",
    "KMFA/metadata/security/public_repo_sensitive_data_policy.jsonl",
    "KMFA/metadata/security/audit_log_policy.jsonl",
    "KMFA/metadata/notifications/notification_manifest.json",
    "KMFA/metadata/notifications/notification_rules.jsonl",
    "KMFA/metadata/notifications/notification_events.jsonl",
    "KMFA/metadata/notifications/notification_dispatch_log.jsonl",
    "KMFA/metadata/operations/operations_sop_manifest.json",
    "KMFA/metadata/operations/operations_runbooks.jsonl",
    "KMFA/metadata/operations/finance_sop_knowledge_index.jsonl",
    "KMFA/metadata/operations/error_backup_drill_log.jsonl",
    "KMFA/tools/precision_stress_validation.py",
    "KMFA/tools/check_s18_p1_precision_stress.py",
    "KMFA/tests/test_precision_stress_validation.py",
    "KMFA/tools/full_regression_acceptance.py",
    "KMFA/tools/check_s18_p2_full_regression_acceptance.py",
    "KMFA/tests/test_full_regression_acceptance.py",
    "KMFA/tools/integration_preparation.py",
    "KMFA/tools/check_s18_p3_integration_preparation.py",
    "KMFA/tests/test_integration_preparation.py",
    "KMFA/tools/check_s18_stage_review.py",
    "KMFA/tests/test_s18_stage_review.py",
    "KMFA/metadata/quality/precision_stress_manifest.json",
    "KMFA/metadata/quality/precision_stress_scenarios.jsonl",
    "KMFA/metadata/quality/precision_stress_import_runs.jsonl",
    "KMFA/metadata/quality/precision_stress_error_reports.jsonl",
    "KMFA/metadata/quality/full_regression_acceptance_manifest.json",
    "KMFA/metadata/quality/full_regression_check_results.jsonl",
    "KMFA/metadata/quality/stage_acceptance_evidence_index.jsonl",
    "KMFA/metadata/quality/go_no_go_report.json",
    "KMFA/metadata/quality/stage18_go_no_go_review.json",
    "KMFA/metadata/integration/integration_preparation_manifest.json",
    "KMFA/metadata/integration/read_only_connector_plan.jsonl",
    "KMFA/metadata/integration/opme_entry_integration_plan.json",
    "KMFA/metadata/integration/next_stage_backlog.jsonl",
)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            payload = json.loads(line)
            if not isinstance(payload, dict):
                raise ValueError(f"{path} contains non-object JSONL record")
            records.append(payload)
    return records


def _fail(message: str) -> None:
    raise ValueError(message)


def _require_equal(label: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        _fail(f"{label}: expected {expected!r}, got {actual!r}")


def _require_true(label: str, actual: Any) -> None:
    if actual is not True:
        _fail(f"{label}: expected true, got {actual!r}")


def _require_false(label: str, actual: Any) -> None:
    if actual is not False:
        _fail(f"{label}: expected false, got {actual!r}")


def _require_existing_refs(refs: Any) -> None:
    if not isinstance(refs, list) or not refs:
        _fail("evidence_refs: expected non-empty list")
    missing = [ref for ref in refs if not isinstance(ref, str) or not Path(ref).exists()]
    if missing:
        _fail("missing evidence refs: " + ", ".join(map(str, missing)))


def _require_false_flags(label: str, payload: dict[str, Any]) -> None:
    for key, value in payload.items():
        _require_false(f"{label}.{key}", value)


def _require_review_gate(
    label: str,
    payload: dict[str, Any],
    expected_status: str,
    next_scope_key: str | None = None,
) -> dict[str, Any]:
    _require_equal(f"{label}.status", payload.get("status"), expected_status)
    _require_equal(f"{label}.github_upload_status", payload.get("github_upload_status"), "not_pushed")
    _require_true(f"{label}.upload_allowed_after_review", payload.get("upload_allowed_after_review"))
    _require_false(f"{label}.github_upload_performed", payload.get("github_upload_performed"))
    _require_false(f"{label}.lineage_full_check_performed", payload.get("lineage_full_check_performed"))
    _require_false(f"{label}.formal_report_generated", payload.get("formal_report_generated"))
    _require_false(f"{label}.external_connector_included", payload.get("external_connector_included"))
    _require_false(f"{label}.business_decision_basis_allowed", payload.get("business_decision_basis_allowed"))
    _require_equal(f"{label}.report_grade_visible", payload.get("report_grade_visible"), "D")
    if next_scope_key:
        _require_false(f"{label}.{next_scope_key}", payload.get(next_scope_key))
    _require_equal(f"{label}.open_review_finding_count", payload.get("open_review_finding_count"), 0)
    _require_false_flags(f"{label}.public_repo_safety", payload.get("public_repo_safety", {}))
    _require_existing_refs(payload.get("evidence_refs"))

    phase_validators = payload.get("phase_validators_rerun")
    if not isinstance(phase_validators, dict):
        _fail(f"{label}.phase_validators_rerun: expected object")
    for key, value in phase_validators.items():
        _require_true(f"{label}.phase_validators_rerun.{key}", value)

    counts = payload.get("review_counts")
    if not isinstance(counts, dict):
        _fail(f"{label}.review_counts: expected object")
    return counts


def _require_stage_upload(label: str, payload: dict[str, Any]) -> None:
    _require_equal(f"{label}.schema_version", payload.get("schema_version"), "kmfa.github_upload_manifest.v1")
    _require_equal(f"{label}.project_id", payload.get("project_id"), "KMFA")
    _require_equal(f"{label}.status", payload.get("status"), "uploaded_to_github_main")
    boundary = payload.get("privacy_boundary") or payload.get("public_repo_safety")
    if not isinstance(boundary, dict) or not boundary:
        _fail(f"{label}: missing privacy/public safety boundary")
    _require_false_flags(f"{label}.upload_boundary", boundary)


def _require_metadata_counts() -> None:
    metadata_counts = {
        "subcontract_procurement_source_lanes": len(_read_jsonl(Path("KMFA/metadata/reports/subcontract_procurement_source_lanes.jsonl"))),
        "subcontract_project_matches": len(_read_jsonl(Path("KMFA/metadata/reports/subcontract_project_matches.jsonl"))),
        "subcontract_unallocated_cost_pool": len(_read_jsonl(Path("KMFA/metadata/reports/subcontract_unallocated_cost_pool.jsonl"))),
        "subcontract_anomaly_candidates": len(_read_jsonl(Path("KMFA/metadata/reports/subcontract_anomaly_candidates.jsonl"))),
        "project_status_source_lanes": len(_read_jsonl(Path("KMFA/metadata/reports/project_status_source_lanes.jsonl"))),
        "project_lifecycle_records": len(_read_jsonl(Path("KMFA/metadata/reports/project_lifecycle_records.jsonl"))),
        "project_lifecycle_exception_items": len(_read_jsonl(Path("KMFA/metadata/reports/project_lifecycle_exception_items.jsonl"))),
        "project_lifecycle_handoff_guards": len(_read_jsonl(Path("KMFA/metadata/reports/project_lifecycle_handoff_guards.jsonl"))),
        "customer_analysis_source_lanes": len(_read_jsonl(Path("KMFA/metadata/reports/customer_analysis_source_lanes.jsonl"))),
        "customer_operating_summaries": len(_read_jsonl(Path("KMFA/metadata/reports/customer_operating_summaries.jsonl"))),
        "customer_analysis_exception_items": len(_read_jsonl(Path("KMFA/metadata/reports/customer_analysis_exception_items.jsonl"))),
        "role_permission_matrix": len(_read_jsonl(Path("KMFA/metadata/security/role_permission_matrix.jsonl"))),
        "public_repo_sensitive_data_policy": len(_read_jsonl(Path("KMFA/metadata/security/public_repo_sensitive_data_policy.jsonl"))),
        "audit_log_policy": len(_read_jsonl(Path("KMFA/metadata/security/audit_log_policy.jsonl"))),
        "notification_rules": len(_read_jsonl(Path("KMFA/metadata/notifications/notification_rules.jsonl"))),
        "notification_events": len(_read_jsonl(Path("KMFA/metadata/notifications/notification_events.jsonl"))),
        "notification_dispatch_log": len(_read_jsonl(Path("KMFA/metadata/notifications/notification_dispatch_log.jsonl"))),
        "operations_runbooks": len(_read_jsonl(Path("KMFA/metadata/operations/operations_runbooks.jsonl"))),
        "finance_sop_knowledge_index": len(_read_jsonl(Path("KMFA/metadata/operations/finance_sop_knowledge_index.jsonl"))),
        "error_backup_drill_log": len(_read_jsonl(Path("KMFA/metadata/operations/error_backup_drill_log.jsonl"))),
        "precision_stress_scenarios": len(_read_jsonl(Path("KMFA/metadata/quality/precision_stress_scenarios.jsonl"))),
        "precision_stress_import_runs": len(_read_jsonl(Path("KMFA/metadata/quality/precision_stress_import_runs.jsonl"))),
        "precision_stress_error_reports": len(_read_jsonl(Path("KMFA/metadata/quality/precision_stress_error_reports.jsonl"))),
        "full_regression_check_results": len(_read_jsonl(Path("KMFA/metadata/quality/full_regression_check_results.jsonl"))),
        "stage_acceptance_evidence_index": len(_read_jsonl(Path("KMFA/metadata/quality/stage_acceptance_evidence_index.jsonl"))),
        "read_only_connector_plan": len(_read_jsonl(Path("KMFA/metadata/integration/read_only_connector_plan.jsonl"))),
        "next_stage_backlog": len(_read_jsonl(Path("KMFA/metadata/integration/next_stage_backlog.jsonl"))),
    }
    expected_counts = {
        "subcontract_procurement_source_lanes": 4,
        "subcontract_project_matches": 5,
        "subcontract_unallocated_cost_pool": 2,
        "subcontract_anomaly_candidates": 4,
        "project_status_source_lanes": 6,
        "project_lifecycle_records": 4,
        "project_lifecycle_exception_items": 3,
        "project_lifecycle_handoff_guards": 3,
        "customer_analysis_source_lanes": 5,
        "customer_operating_summaries": 4,
        "customer_analysis_exception_items": 4,
        "role_permission_matrix": 4,
        "public_repo_sensitive_data_policy": 15,
        "audit_log_policy": 5,
        "notification_rules": 3,
        "notification_events": 3,
        "notification_dispatch_log": 3,
        "operations_runbooks": 4,
        "finance_sop_knowledge_index": 2,
        "error_backup_drill_log": 2,
        "precision_stress_scenarios": 5,
        "precision_stress_import_runs": 3,
        "precision_stress_error_reports": 2,
        "full_regression_check_results": 5,
        "stage_acceptance_evidence_index": 18,
        "read_only_connector_plan": 3,
        "next_stage_backlog": 6,
    }
    for key, expected in expected_counts.items():
        _require_equal(f"metadata.{key}", metadata_counts[key], expected)


def _require_stage18_current_no_go() -> None:
    go_no_go = _read_json(Path("KMFA/metadata/quality/stage18_go_no_go_review.json"))
    _require_equal("stage18_go_no_go_review.decision", go_no_go.get("decision"), "NO_GO")
    _require_false("stage18_go_no_go_review.delivery_allowed", go_no_go.get("delivery_allowed"))
    _require_false("stage18_go_no_go_review.official_report_release_allowed", go_no_go.get("official_report_release_allowed"))
    _require_false("stage18_go_no_go_review.external_connector_allowed", go_no_go.get("external_connector_allowed"))
    _require_false("stage18_go_no_go_review.business_decision_basis_allowed", go_no_go.get("business_decision_basis_allowed"))
    _require_false("stage18_go_no_go_review.business_execution_allowed", go_no_go.get("business_execution_allowed"))
    _require_false("stage18_go_no_go_review.github_upload_performed", go_no_go.get("github_upload_performed"))
    _require_false("stage18_go_no_go_review.s18_p3_pending", go_no_go.get("s18_p3_pending"))
    _require_equal("stage18_go_no_go_review.blocker_count", len(go_no_go.get("blocker_ids", [])), 4)

    opme = _read_json(Path("KMFA/metadata/integration/opme_entry_integration_plan.json"))
    _require_equal("opme_entry_integration_plan.integration_mode", opme.get("integration_mode"), "entry_link_and_status_index_only")
    _require_equal("opme_entry_integration_plan.coupling_level", opme.get("coupling_level"), "light_entry_only")
    _require_equal("opme_entry_integration_plan.entry_surface_count", len(opme.get("entry_surfaces", [])), 4)
    _require_false("opme_entry_integration_plan.external_service_called", opme.get("external_service_called"))
    _require_false("opme_entry_integration_plan.deep_coupling_allowed", opme.get("deep_coupling_allowed"))
    _require_false("opme_entry_integration_plan.shared_database_allowed", opme.get("shared_database_allowed"))
    _require_false("opme_entry_integration_plan.github_upload_allowed", opme.get("github_upload_allowed"))
    _require_false("opme_entry_integration_plan.raw_business_data_committed", opme.get("raw_business_data_committed"))
    _require_false("opme_entry_integration_plan.field_plaintext_committed", opme.get("field_plaintext_committed"))
    _require_false("opme_entry_integration_plan.credential_committed", opme.get("credential_committed"))


def validate_part6_review(manifest_path: Path = DEFAULT_MANIFEST) -> dict[str, int]:
    manifest = _read_json(manifest_path)

    _require_equal("schema_version", manifest.get("schema_version"), "kmfa.part_review_manifest.v1")
    _require_equal("project_id", manifest.get("project_id"), "KMFA")
    _require_equal("part_id", manifest.get("part_id"), "PART6_STAGES_16_18")
    _require_equal("review_id", manifest.get("review_id"), "KMFA-PART6-STAGES-16-18-REVIEW-20260702")
    _require_equal("status", manifest.get("status"), "part_review_passed_local_only_no_go")
    _require_equal("stages", manifest.get("stages"), ["S16", "S17", "S18"])
    _require_equal("next_part_id", manifest.get("next_part_id"), "PROJECT_WIDE_FINAL_REVIEW")
    _require_true("part_review_performed", manifest.get("part_review_performed"))
    _require_false("github_upload_performed", manifest.get("github_upload_performed"))
    _require_false("formal_report_generated", manifest.get("formal_report_generated"))
    _require_false("lineage_full_check_performed", manifest.get("lineage_full_check_performed"))
    _require_false("business_execution_allowed", manifest.get("business_execution_allowed"))
    _require_false("delivery_allowed", manifest.get("delivery_allowed"))
    _require_false("live_connector_allowed", manifest.get("live_connector_allowed"))
    _require_false("opme_deep_coupling_allowed", manifest.get("opme_deep_coupling_allowed"))
    _require_equal("open_review_finding_count", manifest.get("open_review_finding_count"), 0)
    _require_equal("fixed_review_finding_count", manifest.get("fixed_review_finding_count"), 0)

    counts = manifest.get("review_counts")
    if not isinstance(counts, dict):
        _fail("review_counts: expected object")
    _require_equal("review_counts.stage_count", counts.get("stage_count"), 3)
    _require_equal("review_counts.phase_count", counts.get("phase_count"), 9)
    _require_equal("review_counts.required_stage_artifact_count", counts.get("required_stage_artifact_count"), len(REQUIRED_STAGE_ARTIFACTS))
    _require_equal("review_counts.required_baseline_ref_count", counts.get("required_baseline_ref_count"), len(REQUIRED_BASELINE_REFS))
    _require_equal("review_counts.part6_unit_tests", counts.get("part6_unit_tests"), 62)
    _require_equal("review_counts.full_kmfa_unit_tests", counts.get("full_kmfa_unit_tests"), 274)
    _require_equal("review_counts.s16_subcontract_source_lanes", counts.get("s16_subcontract_source_lanes"), 4)
    _require_equal("review_counts.s16_subcontract_project_matches", counts.get("s16_subcontract_project_matches"), 5)
    _require_equal("review_counts.s16_subcontract_unallocated_cost_pool", counts.get("s16_subcontract_unallocated_cost_pool"), 2)
    _require_equal("review_counts.s16_subcontract_anomaly_candidates", counts.get("s16_subcontract_anomaly_candidates"), 4)
    _require_equal("review_counts.s16_project_status_source_lanes", counts.get("s16_project_status_source_lanes"), 6)
    _require_equal("review_counts.s16_project_lifecycle_records", counts.get("s16_project_lifecycle_records"), 4)
    _require_equal("review_counts.s16_project_lifecycle_exception_items", counts.get("s16_project_lifecycle_exception_items"), 3)
    _require_equal("review_counts.s16_project_lifecycle_handoff_guards", counts.get("s16_project_lifecycle_handoff_guards"), 3)
    _require_equal("review_counts.s16_customer_analysis_source_lanes", counts.get("s16_customer_analysis_source_lanes"), 5)
    _require_equal("review_counts.s16_customer_operating_summaries", counts.get("s16_customer_operating_summaries"), 4)
    _require_equal("review_counts.s16_customer_analysis_exception_items", counts.get("s16_customer_analysis_exception_items"), 4)
    _require_equal("review_counts.s17_roles", counts.get("s17_roles"), 4)
    _require_equal("review_counts.s17_sensitive_policy_categories", counts.get("s17_sensitive_policy_categories"), 15)
    _require_equal("review_counts.s17_audit_actions", counts.get("s17_audit_actions"), 5)
    _require_equal("review_counts.s17_notification_rules", counts.get("s17_notification_rules"), 3)
    _require_equal("review_counts.s17_notification_events", counts.get("s17_notification_events"), 3)
    _require_equal("review_counts.s17_dispatch_logs", counts.get("s17_dispatch_logs"), 3)
    _require_equal("review_counts.s17_runbooks", counts.get("s17_runbooks"), 4)
    _require_equal("review_counts.s17_knowledge_items", counts.get("s17_knowledge_items"), 2)
    _require_equal("review_counts.s17_drill_logs", counts.get("s17_drill_logs"), 2)
    _require_equal("review_counts.s18_precision_scenarios", counts.get("s18_precision_scenarios"), 5)
    _require_equal("review_counts.s18_precision_import_runs", counts.get("s18_precision_import_runs"), 3)
    _require_equal("review_counts.s18_precision_error_reports", counts.get("s18_precision_error_reports"), 2)
    _require_equal("review_counts.s18_large_batch_files", counts.get("s18_large_batch_files"), 1200)
    _require_equal("review_counts.s18_regression_checks", counts.get("s18_regression_checks"), 5)
    _require_equal("review_counts.s18_stage_acceptance_evidence", counts.get("s18_stage_acceptance_evidence"), 18)
    _require_equal("review_counts.s18_read_only_connector_plans", counts.get("s18_read_only_connector_plans"), 3)
    _require_equal("review_counts.s18_opme_entry_surfaces", counts.get("s18_opme_entry_surfaces"), 4)
    _require_equal("review_counts.s18_next_stage_backlog", counts.get("s18_next_stage_backlog"), 6)
    _require_equal("review_counts.s18_go_no_go_blockers", counts.get("s18_go_no_go_blockers"), 4)
    _require_equal("review_counts.pending_reconciliation_count", counts.get("pending_reconciliation_count"), 12)
    _require_equal("review_counts.github_upload_count", counts.get("github_upload_count"), 0)
    _require_equal("review_counts.formal_report_count", counts.get("formal_report_count"), 0)
    _require_equal("review_counts.business_execution_count", counts.get("business_execution_count"), 0)
    _require_equal("review_counts.live_connector_count", counts.get("live_connector_count"), 0)
    _require_equal("review_counts.delivery_allowed_count", counts.get("delivery_allowed_count"), 0)

    validators = manifest.get("validators_rerun")
    if not isinstance(validators, dict):
        _fail("validators_rerun: expected object")
    for key, value in validators.items():
        _require_true(f"validators_rerun.{key}", value)

    _require_false_flags("public_repo_safety", manifest.get("public_repo_safety", {}))
    _require_existing_refs(manifest.get("evidence_refs"))

    required_paths = [Path(ref) for ref in REQUIRED_STAGE_ARTIFACTS + REQUIRED_BASELINE_REFS]
    missing = [str(path) for path in required_paths if not path.exists()]
    if missing:
        _fail("missing required Part 6 paths: " + ", ".join(missing))

    stage16 = _read_json(Path("KMFA/stage_artifacts/S16_STAGE_REVIEW/machine/stage16_review_manifest.json"))
    stage17 = _read_json(Path("KMFA/stage_artifacts/S17_STAGE_REVIEW/machine/stage17_review_manifest.json"))
    stage18 = _read_json(Path("KMFA/stage_artifacts/S18_STAGE_REVIEW/machine/stage18_review_manifest.json"))
    stage16_counts = _require_review_gate("S16 review", stage16, "review_passed_upload_ready_local_only", "s17_allowed")
    stage17_counts = _require_review_gate("S17 review", stage17, "review_passed_upload_ready_local_only", "s18_allowed")
    stage18_counts = _require_review_gate("S18 review", stage18, "review_passed_upload_ready_local_only_no_go")

    _require_stage_upload("S16 upload", _read_json(Path("KMFA/stage_artifacts/S16_GITHUB_UPLOAD/machine/stage16_upload_manifest.json")))
    _require_stage_upload("S17 upload", _read_json(Path("KMFA/stage_artifacts/S17_GITHUB_UPLOAD/machine/stage17_upload_manifest.json")))
    _require_stage_upload("S18 upload", _read_json(Path("KMFA/stage_artifacts/S18_GITHUB_UPLOAD/machine/stage18_upload_manifest.json")))

    _require_equal("S16.subcontract_source_lane_count", stage16_counts.get("subcontract_source_lane_count"), 4)
    _require_equal("S16.subcontract_project_match_count", stage16_counts.get("subcontract_project_match_count"), 5)
    _require_equal("S16.unallocated_cost_pool_count", stage16_counts.get("unallocated_cost_pool_count"), 2)
    _require_equal("S16.subcontract_anomaly_candidate_count", stage16_counts.get("subcontract_anomaly_candidate_count"), 4)
    _require_equal("S16.project_status_source_lane_count", stage16_counts.get("project_status_source_lane_count"), 6)
    _require_equal("S16.project_lifecycle_record_count", stage16_counts.get("project_lifecycle_record_count"), 4)
    _require_equal("S16.project_lifecycle_exception_item_count", stage16_counts.get("project_lifecycle_exception_item_count"), 3)
    _require_equal("S16.project_lifecycle_handoff_guard_count", stage16_counts.get("project_lifecycle_handoff_guard_count"), 3)
    _require_equal("S16.customer_analysis_source_lane_count", stage16_counts.get("customer_analysis_source_lane_count"), 5)
    _require_equal("S16.customer_operating_summary_count", stage16_counts.get("customer_operating_summary_count"), 4)
    _require_equal("S16.customer_analysis_exception_item_count", stage16_counts.get("customer_analysis_exception_item_count"), 4)
    _require_equal("S16.pending_reconciliation_count", stage16_counts.get("pending_reconciliation_count"), 12)
    _require_equal("S16.github_upload_count", stage16_counts.get("github_upload_count"), 0)

    _require_equal("S17.role_count", stage17_counts.get("role_count"), 4)
    _require_equal("S17.sensitive_policy_category_count", stage17_counts.get("sensitive_policy_category_count"), 15)
    _require_equal("S17.audit_action_type_count", stage17_counts.get("audit_action_type_count"), 5)
    _require_equal("S17.notification_rule_count", stage17_counts.get("notification_rule_count"), 3)
    _require_equal("S17.notification_event_count", stage17_counts.get("notification_event_count"), 3)
    _require_equal("S17.notification_dispatch_log_count", stage17_counts.get("notification_dispatch_log_count"), 3)
    _require_equal("S17.operation_runbook_count", stage17_counts.get("operation_runbook_count"), 4)
    _require_equal("S17.knowledge_item_count", stage17_counts.get("knowledge_item_count"), 2)
    _require_equal("S17.drill_log_count", stage17_counts.get("drill_log_count"), 2)
    _require_equal("S17.live_connector_count", stage17_counts.get("live_connector_count"), 0)
    _require_equal("S17.github_upload_count", stage17_counts.get("github_upload_count"), 0)

    _require_equal("S18.precision_scenario_count", stage18_counts.get("precision_scenario_count"), 5)
    _require_equal("S18.precision_import_run_count", stage18_counts.get("precision_import_run_count"), 3)
    _require_equal("S18.large_batch_file_count", stage18_counts.get("large_batch_file_count"), 1200)
    _require_equal("S18.full_regression_check_count", stage18_counts.get("full_regression_check_count"), 5)
    _require_equal("S18.stage_acceptance_evidence_count", stage18_counts.get("stage_acceptance_evidence_count"), 18)
    _require_equal("S18.read_only_connector_plan_count", stage18_counts.get("read_only_connector_plan_count"), 3)
    _require_equal("S18.opme_entry_surface_count", stage18_counts.get("opme_entry_surface_count"), 4)
    _require_equal("S18.next_stage_backlog_count", stage18_counts.get("next_stage_backlog_count"), 6)
    _require_equal("S18.stage18_go_no_go_blocker_count", stage18_counts.get("stage18_go_no_go_blocker_count"), 4)
    _require_equal("S18.delivery_allowed_count", stage18_counts.get("delivery_allowed_count"), 0)
    _require_equal("S18.live_connector_count", stage18_counts.get("live_connector_count"), 0)
    _require_equal("S18.github_upload_count", stage18_counts.get("github_upload_count"), 0)

    _require_false("S18.delivery_allowed", stage18.get("delivery_allowed"))
    _require_false("S18.official_report_release_allowed", stage18.get("official_report_release_allowed"))
    _require_false("S18.live_connector_allowed", stage18.get("live_connector_allowed"))
    _require_false("S18.opme_deep_coupling_allowed", stage18.get("opme_deep_coupling_allowed"))
    _require_false("S18.production_restore_allowed", stage18.get("production_restore_allowed"))
    _require_false("S18.business_execution_allowed", stage18.get("business_execution_allowed"))

    _require_metadata_counts()
    _require_stage18_current_no_go()

    return {
        "stage_count": counts["stage_count"],
        "phase_count": counts["phase_count"],
        "required_stage_artifact_count": counts["required_stage_artifact_count"],
        "required_baseline_ref_count": counts["required_baseline_ref_count"],
        "part6_unit_tests": counts["part6_unit_tests"],
        "full_kmfa_unit_tests": counts["full_kmfa_unit_tests"],
        "open_review_finding_count": manifest["open_review_finding_count"],
        "github_upload_count": counts["github_upload_count"],
        "delivery_allowed_count": counts["delivery_allowed_count"],
    }


def main() -> int:
    try:
        counts = validate_part6_review(DEFAULT_MANIFEST)
    except Exception as exc:  # pragma: no cover - CLI guard
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    print(
        "PASS: KMFA Part 6 Stage 16-18 review check passed "
        f"(stages={counts['stage_count']}, phases={counts['phase_count']}, "
        f"stage_artifacts={counts['required_stage_artifact_count']}, "
        f"baseline_refs={counts['required_baseline_ref_count']}, "
        f"part6_tests={counts['part6_unit_tests']}, full_tests={counts['full_kmfa_unit_tests']}, "
        f"github_upload={counts['github_upload_count']}, delivery_allowed={counts['delivery_allowed_count']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
