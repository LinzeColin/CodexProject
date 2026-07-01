#!/usr/bin/env python3
"""Validate KMFA post-S18 Part 5 review evidence for Stages 13-15."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


DEFAULT_MANIFEST = Path("KMFA/stage_artifacts/PART5_STAGES_13_15_REVIEW/machine/part5_review_manifest.json")

REQUIRED_STAGE_ARTIFACTS = (
    "KMFA/stage_artifacts/S13_GITHUB_UPLOAD/human/github_upload_record.md",
    "KMFA/stage_artifacts/S13_GITHUB_UPLOAD/machine/stage13_upload_manifest.json",
    "KMFA/stage_artifacts/S13_P1_financial_operating_report/exports/html/financial_operating_monthly_draft.html",
    "KMFA/stage_artifacts/S13_P1_financial_operating_report/exports/html/financial_operating_weekly_draft.html",
    "KMFA/stage_artifacts/S13_P1_financial_operating_report/human/s13_p1_completion_record.md",
    "KMFA/stage_artifacts/S13_P1_financial_operating_report/human/test_results.md",
    "KMFA/stage_artifacts/S13_P1_financial_operating_report/machine/s13_p1_manifest.json",
    "KMFA/stage_artifacts/S13_P2_collection_receivable_aging/exports/html/collection_receivable_aging_priority.html",
    "KMFA/stage_artifacts/S13_P2_collection_receivable_aging/human/s13_p2_completion_record.md",
    "KMFA/stage_artifacts/S13_P2_collection_receivable_aging/human/test_results.md",
    "KMFA/stage_artifacts/S13_P2_collection_receivable_aging/machine/s13_p2_manifest.json",
    "KMFA/stage_artifacts/S13_P3_cross_table_review/exports/html/cross_table_quality_report.html",
    "KMFA/stage_artifacts/S13_P3_cross_table_review/human/s13_p3_completion_record.md",
    "KMFA/stage_artifacts/S13_P3_cross_table_review/human/test_results.md",
    "KMFA/stage_artifacts/S13_P3_cross_table_review/machine/s13_p3_manifest.json",
    "KMFA/stage_artifacts/S13_STAGE_REVIEW/human/stage13_review_report.md",
    "KMFA/stage_artifacts/S13_STAGE_REVIEW/human/test_results.md",
    "KMFA/stage_artifacts/S13_STAGE_REVIEW/machine/stage13_review_manifest.json",
    "KMFA/stage_artifacts/S14_GITHUB_UPLOAD/human/github_upload_record.md",
    "KMFA/stage_artifacts/S14_GITHUB_UPLOAD/machine/stage14_upload_manifest.json",
    "KMFA/stage_artifacts/S14_P1_fund_cash_loan_plan/exports/html/fund_cash_loan_plan_overview.html",
    "KMFA/stage_artifacts/S14_P1_fund_cash_loan_plan/human/s14_p1_completion_record.md",
    "KMFA/stage_artifacts/S14_P1_fund_cash_loan_plan/human/test_results.md",
    "KMFA/stage_artifacts/S14_P1_fund_cash_loan_plan/machine/s14_p1_manifest.json",
    "KMFA/stage_artifacts/S14_P2_invoice_tax_plan/exports/html/invoice_tax_plan_overview.html",
    "KMFA/stage_artifacts/S14_P2_invoice_tax_plan/human/s14_p2_completion_record.md",
    "KMFA/stage_artifacts/S14_P2_invoice_tax_plan/human/test_results.md",
    "KMFA/stage_artifacts/S14_P2_invoice_tax_plan/machine/s14_p2_manifest.json",
    "KMFA/stage_artifacts/S14_P3_policy_evidence_plan/exports/html/policy_evidence_overview.html",
    "KMFA/stage_artifacts/S14_P3_policy_evidence_plan/human/s14_p3_completion_record.md",
    "KMFA/stage_artifacts/S14_P3_policy_evidence_plan/human/test_results.md",
    "KMFA/stage_artifacts/S14_P3_policy_evidence_plan/machine/s14_p3_manifest.json",
    "KMFA/stage_artifacts/S14_STAGE_REVIEW/human/stage14_review_report.md",
    "KMFA/stage_artifacts/S14_STAGE_REVIEW/human/test_results.md",
    "KMFA/stage_artifacts/S14_STAGE_REVIEW/machine/stage14_review_manifest.json",
    "KMFA/stage_artifacts/S15_GITHUB_UPLOAD/human/github_upload_record.md",
    "KMFA/stage_artifacts/S15_GITHUB_UPLOAD/machine/stage15_upload_manifest.json",
    "KMFA/stage_artifacts/S15_P1_performance_fact_fields/human/s15_p1_completion_record.md",
    "KMFA/stage_artifacts/S15_P1_performance_fact_fields/human/test_results.md",
    "KMFA/stage_artifacts/S15_P1_performance_fact_fields/machine/s15_p1_manifest.json",
    "KMFA/stage_artifacts/S15_P2_performance_review_list/human/s15_p2_completion_record.md",
    "KMFA/stage_artifacts/S15_P2_performance_review_list/human/test_results.md",
    "KMFA/stage_artifacts/S15_P2_performance_review_list/machine/s15_p2_manifest.json",
    "KMFA/stage_artifacts/S15_P3_salary_boundary/human/s15_p3_completion_record.md",
    "KMFA/stage_artifacts/S15_P3_salary_boundary/human/test_results.md",
    "KMFA/stage_artifacts/S15_P3_salary_boundary/machine/s15_p3_manifest.json",
    "KMFA/stage_artifacts/S15_STAGE_REVIEW/human/stage15_review_report.md",
    "KMFA/stage_artifacts/S15_STAGE_REVIEW/human/test_results.md",
    "KMFA/stage_artifacts/S15_STAGE_REVIEW/machine/stage15_review_manifest.json",
)

REQUIRED_BASELINE_REFS = (
    "KMFA/taskpack/v1_2/01_KMFA_Codex_TaskPack_v1_2_完整防遗漏_含HTML验收样板.md",
    "KMFA/taskpack/v1_2/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_2.md",
    "KMFA/tools/financial_operating_report.py",
    "KMFA/tools/check_s13_p1_financial_operating_report.py",
    "KMFA/tests/test_financial_operating_report.py",
    "KMFA/tools/collection_receivable_aging.py",
    "KMFA/tools/check_s13_p2_collection_receivable_aging.py",
    "KMFA/tests/test_collection_receivable_aging.py",
    "KMFA/tools/cross_table_review.py",
    "KMFA/tools/check_s13_p3_cross_table_review.py",
    "KMFA/tests/test_cross_table_review.py",
    "KMFA/tools/check_s13_stage_review.py",
    "KMFA/tests/test_s13_stage_review.py",
    "KMFA/metadata/reports/financial_operating_report_manifest.json",
    "KMFA/metadata/reports/financial_operating_report_source_lanes.jsonl",
    "KMFA/metadata/reports/financial_operating_report_drafts.jsonl",
    "KMFA/metadata/reports/collection_receivable_aging_manifest.json",
    "KMFA/metadata/reports/collection_receivable_aging_source_lanes.jsonl",
    "KMFA/metadata/reports/collection_receivable_aging_priority_items.jsonl",
    "KMFA/metadata/reports/collection_receivable_aging_responsibility_items.jsonl",
    "KMFA/metadata/reports/cross_table_review_manifest.json",
    "KMFA/metadata/reports/cross_table_review_checks.jsonl",
    "KMFA/metadata/reports/cross_table_difference_queue.jsonl",
    "KMFA/metadata/reports/operating_report_quality_report.json",
    "KMFA/tools/fund_cash_loan_plan.py",
    "KMFA/tools/check_s14_p1_fund_cash_loan_plan.py",
    "KMFA/tests/test_fund_cash_loan_plan.py",
    "KMFA/tools/invoice_tax_plan.py",
    "KMFA/tools/check_s14_p2_invoice_tax_plan.py",
    "KMFA/tests/test_invoice_tax_plan.py",
    "KMFA/tools/policy_evidence_plan.py",
    "KMFA/tools/check_s14_p3_policy_evidence_plan.py",
    "KMFA/tests/test_policy_evidence_plan.py",
    "KMFA/tools/check_s14_stage_review.py",
    "KMFA/tests/test_s14_stage_review.py",
    "KMFA/metadata/reports/fund_cash_loan_plan_manifest.json",
    "KMFA/metadata/reports/fund_cash_loan_source_lanes.jsonl",
    "KMFA/metadata/reports/fund_cash_pressure_signals.jsonl",
    "KMFA/metadata/reports/loan_due_alerts.jsonl",
    "KMFA/metadata/reports/account_balance_summaries.jsonl",
    "KMFA/metadata/reports/invoice_tax_plan_manifest.json",
    "KMFA/metadata/reports/invoice_tax_source_lanes.jsonl",
    "KMFA/metadata/reports/invoice_tax_issue_candidates.jsonl",
    "KMFA/metadata/reports/invoice_tax_cash_summaries.jsonl",
    "KMFA/metadata/reports/policy_evidence_plan_manifest.json",
    "KMFA/metadata/reports/policy_evidence_directories.jsonl",
    "KMFA/metadata/reports/policy_evidence_gaps.jsonl",
    "KMFA/metadata/reports/policy_risk_tips.jsonl",
    "KMFA/tools/performance_fact_fields.py",
    "KMFA/tools/check_s15_p1_performance_fact_fields.py",
    "KMFA/tests/test_performance_fact_fields.py",
    "KMFA/tools/performance_review_list.py",
    "KMFA/tools/check_s15_p2_performance_review_list.py",
    "KMFA/tests/test_performance_review_list.py",
    "KMFA/tools/performance_salary_boundary.py",
    "KMFA/tools/check_s15_p3_salary_boundary.py",
    "KMFA/tests/test_performance_salary_boundary.py",
    "KMFA/tools/check_s15_stage_review.py",
    "KMFA/tests/test_s15_stage_review.py",
    "KMFA/metadata/reports/performance_fact_fields_manifest.json",
    "KMFA/metadata/reports/performance_fact_field_definitions.jsonl",
    "KMFA/metadata/reports/performance_fact_field_bindings.jsonl",
    "KMFA/metadata/reports/performance_fact_manual_review_fields.jsonl",
    "KMFA/metadata/reports/performance_review_manifest.json",
    "KMFA/metadata/reports/performance_fact_table.jsonl",
    "KMFA/metadata/reports/performance_review_items.jsonl",
    "KMFA/metadata/reports/performance_salary_boundary_manifest.json",
    "KMFA/metadata/reports/performance_fact_output_interface_contract.json",
    "KMFA/metadata/reports/salary_system_readiness_draft.jsonl",
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


def _require_review_gate(label: str, payload: dict[str, Any], next_scope_key: str) -> dict[str, Any]:
    _require_equal(f"{label}.status", payload.get("status"), "review_passed_upload_ready_local_only")
    _require_equal(f"{label}.github_upload_status", payload.get("github_upload_status"), "not_pushed")
    _require_true(f"{label}.upload_allowed_after_review", payload.get("upload_allowed_after_review"))
    _require_false(f"{label}.github_upload_performed", payload.get("github_upload_performed"))
    _require_false(f"{label}.lineage_full_check_performed", payload.get("lineage_full_check_performed"))
    _require_false(f"{label}.formal_report_generated", payload.get("formal_report_generated"))
    _require_false(f"{label}.external_connector_included", payload.get("external_connector_included"))
    _require_false(f"{label}.business_decision_basis_allowed", payload.get("business_decision_basis_allowed"))
    _require_equal(f"{label}.report_grade_visible", payload.get("report_grade_visible"), "D")
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
    _require_false_flags(f"{label}.privacy_boundary", payload.get("privacy_boundary", {}))


def validate_part5_review(manifest_path: Path = DEFAULT_MANIFEST) -> dict[str, int]:
    manifest = _read_json(manifest_path)

    _require_equal("schema_version", manifest.get("schema_version"), "kmfa.part_review_manifest.v1")
    _require_equal("project_id", manifest.get("project_id"), "KMFA")
    _require_equal("part_id", manifest.get("part_id"), "PART5_STAGES_13_15")
    _require_equal("review_id", manifest.get("review_id"), "KMFA-PART5-STAGES-13-15-REVIEW-20260702")
    _require_equal("status", manifest.get("status"), "part_review_passed_local_only")
    _require_equal("stages", manifest.get("stages"), ["S13", "S14", "S15"])
    _require_equal("next_part_id", manifest.get("next_part_id"), "PART6_STAGES_16_18")
    _require_true("part_review_performed", manifest.get("part_review_performed"))
    _require_false("github_upload_performed", manifest.get("github_upload_performed"))
    _require_false("formal_report_generated", manifest.get("formal_report_generated"))
    _require_false("lineage_full_check_performed", manifest.get("lineage_full_check_performed"))
    _require_false("business_execution_allowed", manifest.get("business_execution_allowed"))
    _require_equal("open_review_finding_count", manifest.get("open_review_finding_count"), 0)
    _require_equal("fixed_review_finding_count", manifest.get("fixed_review_finding_count"), 0)

    counts = manifest.get("review_counts")
    if not isinstance(counts, dict):
        _fail("review_counts: expected object")
    _require_equal("review_counts.stage_count", counts.get("stage_count"), 3)
    _require_equal("review_counts.phase_count", counts.get("phase_count"), 9)
    _require_equal("review_counts.required_stage_artifact_count", counts.get("required_stage_artifact_count"), len(REQUIRED_STAGE_ARTIFACTS))
    _require_equal("review_counts.required_baseline_ref_count", counts.get("required_baseline_ref_count"), len(REQUIRED_BASELINE_REFS))
    _require_equal("review_counts.part5_unit_tests", counts.get("part5_unit_tests"), 56)
    _require_equal("review_counts.full_kmfa_unit_tests", counts.get("full_kmfa_unit_tests"), 273)
    _require_equal("review_counts.s13_financial_source_lanes", counts.get("s13_financial_source_lanes"), 4)
    _require_equal("review_counts.s13_financial_drafts", counts.get("s13_financial_drafts"), 2)
    _require_equal("review_counts.s13_collection_source_lanes", counts.get("s13_collection_source_lanes"), 5)
    _require_equal("review_counts.s13_collection_priority_items", counts.get("s13_collection_priority_items"), 4)
    _require_equal("review_counts.s13_collection_responsibility_items", counts.get("s13_collection_responsibility_items"), 4)
    _require_equal("review_counts.s13_cross_table_dimensions", counts.get("s13_cross_table_dimensions"), 4)
    _require_equal("review_counts.s13_cross_table_difference_items", counts.get("s13_cross_table_difference_items"), 4)
    _require_equal("review_counts.s13_quality_reports", counts.get("s13_quality_reports"), 1)
    _require_equal("review_counts.s14_fund_lanes", counts.get("s14_fund_lanes"), 4)
    _require_equal("review_counts.s14_cash_pressure_records", counts.get("s14_cash_pressure_records"), 4)
    _require_equal("review_counts.s14_loan_due_alerts", counts.get("s14_loan_due_alerts"), 3)
    _require_equal("review_counts.s14_account_summaries", counts.get("s14_account_summaries"), 3)
    _require_equal("review_counts.s14_invoice_tax_lanes", counts.get("s14_invoice_tax_lanes"), 3)
    _require_equal("review_counts.s14_invoice_tax_issues", counts.get("s14_invoice_tax_issues"), 3)
    _require_equal("review_counts.s14_invoice_tax_cash_summaries", counts.get("s14_invoice_tax_cash_summaries"), 3)
    _require_equal("review_counts.s14_policy_directories", counts.get("s14_policy_directories"), 5)
    _require_equal("review_counts.s14_policy_gaps", counts.get("s14_policy_gaps"), 5)
    _require_equal("review_counts.s14_policy_risk_tips", counts.get("s14_policy_risk_tips"), 5)
    _require_equal("review_counts.s15_field_definitions", counts.get("s15_field_definitions"), 6)
    _require_equal("review_counts.s15_field_bindings", counts.get("s15_field_bindings"), 6)
    _require_equal("review_counts.s15_manual_review_fields", counts.get("s15_manual_review_fields"), 4)
    _require_equal("review_counts.s15_performance_fact_rows", counts.get("s15_performance_fact_rows"), 4)
    _require_equal("review_counts.s15_review_items", counts.get("s15_review_items"), 16)
    _require_equal("review_counts.s15_interface_contracts", counts.get("s15_interface_contracts"), 1)
    _require_equal("review_counts.s15_salary_readiness_rows", counts.get("s15_salary_readiness_rows"), 4)
    _require_equal("review_counts.pending_reconciliation_count", counts.get("pending_reconciliation_count"), 12)
    _require_equal("review_counts.github_upload_count", counts.get("github_upload_count"), 0)
    _require_equal("review_counts.formal_report_count", counts.get("formal_report_count"), 0)
    _require_equal("review_counts.business_decision_basis_count", counts.get("business_decision_basis_count"), 0)
    _require_equal("review_counts.salary_calculation_count", counts.get("salary_calculation_count"), 0)
    _require_equal("review_counts.payroll_export_count", counts.get("payroll_export_count"), 0)

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
        _fail("missing required Part 5 paths: " + ", ".join(missing))

    stage13 = _read_json(Path("KMFA/stage_artifacts/S13_STAGE_REVIEW/machine/stage13_review_manifest.json"))
    stage14 = _read_json(Path("KMFA/stage_artifacts/S14_STAGE_REVIEW/machine/stage14_review_manifest.json"))
    stage15 = _read_json(Path("KMFA/stage_artifacts/S15_STAGE_REVIEW/machine/stage15_review_manifest.json"))
    stage13_counts = _require_review_gate("S13 review", stage13, "s14_allowed")
    stage14_counts = _require_review_gate("S14 review", stage14, "s15_allowed")
    stage15_counts = _require_review_gate("S15 review", stage15, "s16_allowed")

    _require_stage_upload("S13 upload", _read_json(Path("KMFA/stage_artifacts/S13_GITHUB_UPLOAD/machine/stage13_upload_manifest.json")))
    _require_stage_upload("S14 upload", _read_json(Path("KMFA/stage_artifacts/S14_GITHUB_UPLOAD/machine/stage14_upload_manifest.json")))
    _require_stage_upload("S15 upload", _read_json(Path("KMFA/stage_artifacts/S15_GITHUB_UPLOAD/machine/stage15_upload_manifest.json")))

    _require_equal("S13.financial_operating_source_lane_count", stage13_counts.get("financial_operating_source_lane_count"), 4)
    _require_equal("S13.financial_operating_draft_count", stage13_counts.get("financial_operating_draft_count"), 2)
    _require_equal("S13.collection_receivable_source_lane_count", stage13_counts.get("collection_receivable_source_lane_count"), 5)
    _require_equal("S13.collection_receivable_priority_item_count", stage13_counts.get("collection_receivable_priority_item_count"), 4)
    _require_equal("S13.collection_receivable_responsibility_item_count", stage13_counts.get("collection_receivable_responsibility_item_count"), 4)
    _require_equal("S13.cross_table_review_dimension_count", stage13_counts.get("cross_table_review_dimension_count"), 4)
    _require_equal("S13.cross_table_difference_queue_count", stage13_counts.get("cross_table_difference_queue_count"), 4)
    _require_equal("S13.operating_quality_report_count", stage13_counts.get("operating_quality_report_count"), 1)
    _require_equal("S13.pending_reconciliation_count", stage13_counts.get("pending_reconciliation_count"), 12)
    _require_equal("S13.formal_report_count", stage13_counts.get("formal_report_count"), 0)
    _require_equal("S13.business_decision_basis_count", stage13_counts.get("business_decision_basis_count"), 0)
    _require_equal("S13.lineage_full_check_count", stage13_counts.get("lineage_full_check_count"), 0)
    _require_equal("S13.github_upload_count", stage13_counts.get("github_upload_count"), 0)

    _require_equal("S14.fund_cash_loan_source_lane_count", stage14_counts.get("fund_cash_loan_source_lane_count"), 4)
    _require_equal("S14.cash_pressure_record_count", stage14_counts.get("cash_pressure_record_count"), 4)
    _require_equal("S14.loan_due_alert_count", stage14_counts.get("loan_due_alert_count"), 3)
    _require_equal("S14.account_balance_summary_count", stage14_counts.get("account_balance_summary_count"), 3)
    _require_equal("S14.invoice_tax_source_lane_count", stage14_counts.get("invoice_tax_source_lane_count"), 3)
    _require_equal("S14.invoice_tax_issue_candidate_count", stage14_counts.get("invoice_tax_issue_candidate_count"), 3)
    _require_equal("S14.invoice_tax_cash_summary_count", stage14_counts.get("invoice_tax_cash_summary_count"), 3)
    _require_equal("S14.policy_evidence_directory_count", stage14_counts.get("policy_evidence_directory_count"), 5)
    _require_equal("S14.policy_evidence_gap_count", stage14_counts.get("policy_evidence_gap_count"), 5)
    _require_equal("S14.policy_risk_tip_count", stage14_counts.get("policy_risk_tip_count"), 5)
    _require_equal("S14.pending_reconciliation_count", stage14_counts.get("pending_reconciliation_count"), 12)
    _require_equal("S14.formal_report_count", stage14_counts.get("formal_report_count"), 0)
    _require_equal("S14.business_decision_basis_count", stage14_counts.get("business_decision_basis_count"), 0)
    _require_equal("S14.payment_or_bank_operation_count", stage14_counts.get("payment_or_bank_operation_count"), 0)
    _require_equal("S14.loan_management_action_count", stage14_counts.get("loan_management_action_count"), 0)
    _require_equal("S14.tax_filing_count", stage14_counts.get("tax_filing_count"), 0)
    _require_equal("S14.invoice_issuance_count", stage14_counts.get("invoice_issuance_count"), 0)
    _require_equal("S14.policy_qualification_conclusion_count", stage14_counts.get("policy_qualification_conclusion_count"), 0)
    _require_equal("S14.policy_application_submission_count", stage14_counts.get("policy_application_submission_count"), 0)
    _require_equal("S14.lineage_full_check_count", stage14_counts.get("lineage_full_check_count"), 0)
    _require_equal("S14.github_upload_count", stage14_counts.get("github_upload_count"), 0)

    _require_equal("S15.field_definition_count", stage15_counts.get("field_definition_count"), 6)
    _require_equal("S15.field_binding_count", stage15_counts.get("field_binding_count"), 6)
    _require_equal("S15.manual_review_field_count", stage15_counts.get("manual_review_field_count"), 4)
    _require_equal("S15.performance_fact_row_count", stage15_counts.get("performance_fact_row_count"), 4)
    _require_equal("S15.abnormal_review_item_count", stage15_counts.get("abnormal_review_item_count"), 16)
    _require_equal("S15.fact_interface_contract_count", stage15_counts.get("fact_interface_contract_count"), 1)
    _require_equal("S15.future_salary_system_readiness_row_count", stage15_counts.get("future_salary_system_readiness_row_count"), 4)
    _require_equal("S15.pending_reconciliation_count", stage15_counts.get("pending_reconciliation_count"), 12)
    _require_equal("S15.salary_calculation_count", stage15_counts.get("salary_calculation_count"), 0)
    _require_equal("S15.wage_calculation_count", stage15_counts.get("wage_calculation_count"), 0)
    _require_equal("S15.bonus_approval_count", stage15_counts.get("bonus_approval_count"), 0)
    _require_equal("S15.payroll_export_count", stage15_counts.get("payroll_export_count"), 0)
    _require_equal("S15.final_compensation_decision_count", stage15_counts.get("final_compensation_decision_count"), 0)
    _require_equal("S15.payment_release_count", stage15_counts.get("payment_release_count"), 0)
    _require_equal("S15.formal_report_count", stage15_counts.get("formal_report_count"), 0)
    _require_equal("S15.business_decision_basis_count", stage15_counts.get("business_decision_basis_count"), 0)
    _require_equal("S15.lineage_full_check_count", stage15_counts.get("lineage_full_check_count"), 0)
    _require_equal("S15.github_upload_count", stage15_counts.get("github_upload_count"), 0)

    metadata_counts = {
        "financial_operating_source_lanes": len(_read_jsonl(Path("KMFA/metadata/reports/financial_operating_report_source_lanes.jsonl"))),
        "financial_operating_drafts": len(_read_jsonl(Path("KMFA/metadata/reports/financial_operating_report_drafts.jsonl"))),
        "collection_receivable_source_lanes": len(_read_jsonl(Path("KMFA/metadata/reports/collection_receivable_aging_source_lanes.jsonl"))),
        "collection_priority_items": len(_read_jsonl(Path("KMFA/metadata/reports/collection_receivable_aging_priority_items.jsonl"))),
        "collection_responsibility_items": len(_read_jsonl(Path("KMFA/metadata/reports/collection_receivable_aging_responsibility_items.jsonl"))),
        "cross_table_review_checks": len(_read_jsonl(Path("KMFA/metadata/reports/cross_table_review_checks.jsonl"))),
        "cross_table_difference_queue": len(_read_jsonl(Path("KMFA/metadata/reports/cross_table_difference_queue.jsonl"))),
        "fund_cash_loan_source_lanes": len(_read_jsonl(Path("KMFA/metadata/reports/fund_cash_loan_source_lanes.jsonl"))),
        "fund_cash_pressure_signals": len(_read_jsonl(Path("KMFA/metadata/reports/fund_cash_pressure_signals.jsonl"))),
        "loan_due_alerts": len(_read_jsonl(Path("KMFA/metadata/reports/loan_due_alerts.jsonl"))),
        "account_balance_summaries": len(_read_jsonl(Path("KMFA/metadata/reports/account_balance_summaries.jsonl"))),
        "invoice_tax_source_lanes": len(_read_jsonl(Path("KMFA/metadata/reports/invoice_tax_source_lanes.jsonl"))),
        "invoice_tax_issue_candidates": len(_read_jsonl(Path("KMFA/metadata/reports/invoice_tax_issue_candidates.jsonl"))),
        "invoice_tax_cash_summaries": len(_read_jsonl(Path("KMFA/metadata/reports/invoice_tax_cash_summaries.jsonl"))),
        "policy_evidence_directories": len(_read_jsonl(Path("KMFA/metadata/reports/policy_evidence_directories.jsonl"))),
        "policy_evidence_gaps": len(_read_jsonl(Path("KMFA/metadata/reports/policy_evidence_gaps.jsonl"))),
        "policy_risk_tips": len(_read_jsonl(Path("KMFA/metadata/reports/policy_risk_tips.jsonl"))),
        "performance_fact_field_definitions": len(_read_jsonl(Path("KMFA/metadata/reports/performance_fact_field_definitions.jsonl"))),
        "performance_fact_field_bindings": len(_read_jsonl(Path("KMFA/metadata/reports/performance_fact_field_bindings.jsonl"))),
        "performance_fact_manual_review_fields": len(_read_jsonl(Path("KMFA/metadata/reports/performance_fact_manual_review_fields.jsonl"))),
        "performance_fact_table": len(_read_jsonl(Path("KMFA/metadata/reports/performance_fact_table.jsonl"))),
        "performance_review_items": len(_read_jsonl(Path("KMFA/metadata/reports/performance_review_items.jsonl"))),
        "salary_system_readiness_draft": len(_read_jsonl(Path("KMFA/metadata/reports/salary_system_readiness_draft.jsonl"))),
    }
    expected_metadata_counts = {
        "financial_operating_source_lanes": 4,
        "financial_operating_drafts": 2,
        "collection_receivable_source_lanes": 5,
        "collection_priority_items": 4,
        "collection_responsibility_items": 4,
        "cross_table_review_checks": 4,
        "cross_table_difference_queue": 4,
        "fund_cash_loan_source_lanes": 4,
        "fund_cash_pressure_signals": 4,
        "loan_due_alerts": 3,
        "account_balance_summaries": 3,
        "invoice_tax_source_lanes": 3,
        "invoice_tax_issue_candidates": 3,
        "invoice_tax_cash_summaries": 3,
        "policy_evidence_directories": 5,
        "policy_evidence_gaps": 5,
        "policy_risk_tips": 5,
        "performance_fact_field_definitions": 6,
        "performance_fact_field_bindings": 6,
        "performance_fact_manual_review_fields": 4,
        "performance_fact_table": 4,
        "performance_review_items": 16,
        "salary_system_readiness_draft": 4,
    }
    for key, expected in expected_metadata_counts.items():
        _require_equal(f"metadata.{key}", metadata_counts[key], expected)

    _require_equal(
        "operating_report_quality_report.report_grade_visible",
        _read_json(Path("KMFA/metadata/reports/operating_report_quality_report.json")).get("report_grade_visible"),
        "D",
    )
    contract = _read_json(Path("KMFA/metadata/reports/performance_fact_output_interface_contract.json"))
    _require_false("performance_fact_output_interface_contract.live_read_enabled", contract.get("live_read_enabled"))
    _require_false("performance_fact_output_interface_contract.connector_enabled", contract.get("connector_enabled"))
    _require_false("performance_fact_output_interface_contract.external_write_enabled", contract.get("external_write_enabled"))
    _require_false("performance_fact_output_interface_contract.file_export_created", contract.get("file_export_created"))
    _require_false(
        "performance_fact_output_interface_contract.automatic_compensation_decision_allowed",
        contract.get("automatic_compensation_decision_allowed"),
    )

    return {
        "stage_count": counts["stage_count"],
        "phase_count": counts["phase_count"],
        "required_stage_artifact_count": counts["required_stage_artifact_count"],
        "required_baseline_ref_count": counts["required_baseline_ref_count"],
        "part5_unit_tests": counts["part5_unit_tests"],
        "full_kmfa_unit_tests": counts["full_kmfa_unit_tests"],
        "open_review_finding_count": manifest["open_review_finding_count"],
        "github_upload_count": counts["github_upload_count"],
    }


def main() -> int:
    try:
        counts = validate_part5_review(DEFAULT_MANIFEST)
    except Exception as exc:  # pragma: no cover - CLI guard
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    print(
        "PASS: KMFA Part 5 Stage 13-15 review check passed "
        f"(stages={counts['stage_count']}, phases={counts['phase_count']}, "
        f"stage_artifacts={counts['required_stage_artifact_count']}, "
        f"baseline_refs={counts['required_baseline_ref_count']}, "
        f"part5_tests={counts['part5_unit_tests']}, full_tests={counts['full_kmfa_unit_tests']}, "
        f"github_upload={counts['github_upload_count']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
