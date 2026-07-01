#!/usr/bin/env python3
"""Validate KMFA Stage 14 review evidence and gates."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


DEFAULT_REVIEW_MANIFEST = Path("KMFA/stage_artifacts/S14_STAGE_REVIEW/machine/stage14_review_manifest.json")
DEFAULT_P1_MANIFEST = Path("KMFA/stage_artifacts/S14_P1_fund_cash_loan_plan/machine/s14_p1_manifest.json")
DEFAULT_P2_MANIFEST = Path("KMFA/stage_artifacts/S14_P2_invoice_tax_plan/machine/s14_p2_manifest.json")
DEFAULT_P3_MANIFEST = Path("KMFA/stage_artifacts/S14_P3_policy_evidence_plan/machine/s14_p3_manifest.json")

DEFAULT_P1_SOURCE_LANES = Path("KMFA/metadata/reports/fund_cash_loan_source_lanes.jsonl")
DEFAULT_P1_CASH_PRESSURE = Path("KMFA/metadata/reports/fund_cash_pressure_signals.jsonl")
DEFAULT_P1_LOAN_DUE_ALERTS = Path("KMFA/metadata/reports/loan_due_alerts.jsonl")
DEFAULT_P1_ACCOUNT_SUMMARIES = Path("KMFA/metadata/reports/account_balance_summaries.jsonl")
DEFAULT_P2_SOURCE_LANES = Path("KMFA/metadata/reports/invoice_tax_source_lanes.jsonl")
DEFAULT_P2_ISSUE_CANDIDATES = Path("KMFA/metadata/reports/invoice_tax_issue_candidates.jsonl")
DEFAULT_P2_CASH_SUMMARIES = Path("KMFA/metadata/reports/invoice_tax_cash_summaries.jsonl")
DEFAULT_P3_DIRECTORIES = Path("KMFA/metadata/reports/policy_evidence_directories.jsonl")
DEFAULT_P3_GAPS = Path("KMFA/metadata/reports/policy_evidence_gaps.jsonl")
DEFAULT_P3_RISK_TIPS = Path("KMFA/metadata/reports/policy_risk_tips.jsonl")

DEFAULT_P1_HTML = Path("KMFA/stage_artifacts/S14_P1_fund_cash_loan_plan/exports/html/fund_cash_loan_plan_overview.html")
DEFAULT_P2_HTML = Path("KMFA/stage_artifacts/S14_P2_invoice_tax_plan/exports/html/invoice_tax_plan_overview.html")
DEFAULT_P3_HTML = Path("KMFA/stage_artifacts/S14_P3_policy_evidence_plan/exports/html/policy_evidence_overview.html")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def fail(message: str) -> None:
    raise ValueError(message)


def require_equal(label: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        fail(f"{label}: expected {expected!r}, got {actual!r}")


def require_true(label: str, actual: Any) -> None:
    if actual is not True:
        fail(f"{label}: expected true, got {actual!r}")


def require_false(label: str, actual: Any) -> None:
    if actual is not False:
        fail(f"{label}: expected false, got {actual!r}")


def require_false_flags(label: str, payload: dict[str, Any], keys: tuple[str, ...]) -> None:
    for key in keys:
        require_false(f"{label}.{key}", payload.get(key))


def require_public_safety(label: str, payload: dict[str, Any]) -> None:
    public_safety = payload.get("public_repo_safety")
    if not isinstance(public_safety, dict):
        fail(f"{label}.public_repo_safety: expected object")
    for key, value in public_safety.items():
        require_false(f"{label}.public_repo_safety.{key}", value)


def require_phase_status(stage_phase_status: Any, phase: str) -> None:
    if not isinstance(stage_phase_status, dict):
        fail("stage_phase_status: expected object")
    status = stage_phase_status.get(phase)
    if not isinstance(status, str) or not status.startswith("completed_validated_local_only"):
        fail(f"stage_phase_status.{phase}: expected completed_validated_local_only*, got {status!r}")


def require_existing_refs(refs: Any) -> None:
    if not isinstance(refs, list) or not refs:
        fail("evidence_refs: expected non-empty list")
    for ref in refs:
        if not isinstance(ref, str):
            fail(f"evidence_refs: expected string ref, got {ref!r}")
        if not Path(ref).exists():
            fail(f"missing evidence ref: {ref}")


def validate_stage_review(
    review_manifest_path: Path = DEFAULT_REVIEW_MANIFEST,
    p1_manifest_path: Path = DEFAULT_P1_MANIFEST,
    p2_manifest_path: Path = DEFAULT_P2_MANIFEST,
    p3_manifest_path: Path = DEFAULT_P3_MANIFEST,
    p1_source_lanes_path: Path = DEFAULT_P1_SOURCE_LANES,
    p1_cash_pressure_path: Path = DEFAULT_P1_CASH_PRESSURE,
    p1_loan_due_alerts_path: Path = DEFAULT_P1_LOAN_DUE_ALERTS,
    p1_account_summaries_path: Path = DEFAULT_P1_ACCOUNT_SUMMARIES,
    p2_source_lanes_path: Path = DEFAULT_P2_SOURCE_LANES,
    p2_issue_candidates_path: Path = DEFAULT_P2_ISSUE_CANDIDATES,
    p2_cash_summaries_path: Path = DEFAULT_P2_CASH_SUMMARIES,
    p3_directories_path: Path = DEFAULT_P3_DIRECTORIES,
    p3_gaps_path: Path = DEFAULT_P3_GAPS,
    p3_risk_tips_path: Path = DEFAULT_P3_RISK_TIPS,
    p1_html_path: Path = DEFAULT_P1_HTML,
    p2_html_path: Path = DEFAULT_P2_HTML,
    p3_html_path: Path = DEFAULT_P3_HTML,
) -> dict[str, int]:
    required_paths = [
        review_manifest_path,
        p1_manifest_path,
        p2_manifest_path,
        p3_manifest_path,
        p1_source_lanes_path,
        p1_cash_pressure_path,
        p1_loan_due_alerts_path,
        p1_account_summaries_path,
        p2_source_lanes_path,
        p2_issue_candidates_path,
        p2_cash_summaries_path,
        p3_directories_path,
        p3_gaps_path,
        p3_risk_tips_path,
        p1_html_path,
        p2_html_path,
        p3_html_path,
        Path("KMFA/stage_artifacts/S14_STAGE_REVIEW/human/stage14_review_report.md"),
        Path("KMFA/stage_artifacts/S14_STAGE_REVIEW/human/test_results.md"),
    ]
    missing = [str(path) for path in required_paths if not path.exists()]
    if missing:
        fail("missing required evidence paths: " + ", ".join(missing))

    forbidden_upload_paths = [
        Path("KMFA/stage_artifacts/S14_STAGE_REVIEW/human/github_upload_record.md"),
        Path("KMFA/stage_artifacts/S14_STAGE_REVIEW/machine/stage14_upload_manifest.json"),
    ]
    unexpected = [str(path) for path in forbidden_upload_paths if path.exists()]
    if unexpected:
        fail("Stage 14 review must not contain upload evidence: " + ", ".join(unexpected))

    review_manifest = read_json(review_manifest_path)
    p1_manifest = read_json(p1_manifest_path)
    p2_manifest = read_json(p2_manifest_path)
    p3_manifest = read_json(p3_manifest_path)

    p1_source_lanes = read_jsonl(p1_source_lanes_path)
    p1_cash_pressure = read_jsonl(p1_cash_pressure_path)
    p1_loan_due_alerts = read_jsonl(p1_loan_due_alerts_path)
    p1_account_summaries = read_jsonl(p1_account_summaries_path)
    p2_source_lanes = read_jsonl(p2_source_lanes_path)
    p2_issue_candidates = read_jsonl(p2_issue_candidates_path)
    p2_cash_summaries = read_jsonl(p2_cash_summaries_path)
    p3_directories = read_jsonl(p3_directories_path)
    p3_gaps = read_jsonl(p3_gaps_path)
    p3_risk_tips = read_jsonl(p3_risk_tips_path)

    require_equal("stage", review_manifest.get("stage"), "S14")
    require_equal("status", review_manifest.get("status"), "review_passed_upload_ready_local_only")
    require_equal("github_upload_status", review_manifest.get("github_upload_status"), "not_pushed")
    require_true("upload_allowed_after_review", review_manifest.get("upload_allowed_after_review"))
    require_false("github_upload_performed", review_manifest.get("github_upload_performed"))
    require_false("s15_allowed", review_manifest.get("s15_allowed"))
    require_false("lineage_full_check_performed", review_manifest.get("lineage_full_check_performed"))
    require_false("formal_report_generated", review_manifest.get("formal_report_generated"))
    require_false("external_connector_included", review_manifest.get("external_connector_included"))
    require_false("business_decision_basis_allowed", review_manifest.get("business_decision_basis_allowed"))
    require_false("full_trusted_report_allowed", review_manifest.get("full_trusted_report_allowed"))
    require_equal("report_grade_visible", review_manifest.get("report_grade_visible"), "D")
    require_equal("pending_reconciliation_count", review_manifest.get("pending_reconciliation_count"), 12)
    require_equal("next_gate_id", review_manifest.get("next_gate_id"), "KMFA-S14-GITHUB-UPLOAD-GATE")
    require_equal("open_review_finding_count", review_manifest.get("open_review_finding_count"), 0)
    require_public_safety("review", review_manifest)

    for phase in ("S14-P1", "S14-P2", "S14-P3"):
        require_phase_status(review_manifest.get("stage_phase_status"), phase)
    require_existing_refs(review_manifest.get("evidence_refs"))

    require_equal("p1.stage_phase", p1_manifest.get("stage_phase"), "S14-P1")
    require_equal(
        "p1.runtime_status",
        p1_manifest.get("runtime_status"),
        "public_safe_fund_cash_loan_planning_signals_created_operations_blocked",
    )
    require_equal("p1.summary.source_lane_count", p1_manifest.get("summary", {}).get("source_lane_count"), 4)
    require_equal("p1.summary.cash_pressure_record_count", p1_manifest.get("summary", {}).get("cash_pressure_record_count"), 4)
    require_equal("p1.summary.loan_due_alert_count", p1_manifest.get("summary", {}).get("loan_due_alert_count"), 3)
    require_equal("p1.summary.account_balance_summary_count", p1_manifest.get("summary", {}).get("account_balance_summary_count"), 3)
    require_equal("p1.summary.pending_reconciliation_count", p1_manifest.get("summary", {}).get("pending_reconciliation_count"), 12)
    require_equal("p1.summary.report_grade_visible", p1_manifest.get("summary", {}).get("report_grade_visible"), "D")
    require_false_flags(
        "p1.quality_gate",
        p1_manifest.get("quality_gate", {}),
        (
            "bank_operation_allowed",
            "business_decision_basis_allowed",
            "complete_trusted_report_display_allowed",
            "formal_report_allowed",
            "github_upload_allowed",
            "invoice_issuance_allowed",
            "loan_management_action_allowed",
            "payment_approval_allowed",
            "payment_execution_allowed",
            "raw_layer_write_allowed",
            "s14_p2_allowed",
            "s14_p3_allowed",
            "stage14_review_allowed",
            "tax_filing_allowed",
        ),
    )
    require_public_safety("p1", p1_manifest)

    require_equal("p2.stage_phase", p2_manifest.get("stage_phase"), "S14-P2")
    require_equal(
        "p2.runtime_status",
        p2_manifest.get("runtime_status"),
        "public_safe_invoice_tax_candidates_created_tax_and_invoice_actions_blocked",
    )
    require_equal("p2.summary.source_lane_count", p2_manifest.get("summary", {}).get("source_lane_count"), 3)
    require_equal("p2.summary.issue_candidate_count", p2_manifest.get("summary", {}).get("issue_candidate_count"), 3)
    require_equal("p2.summary.cash_summary_count", p2_manifest.get("summary", {}).get("cash_summary_count"), 3)
    require_equal("p2.summary.pending_reconciliation_count", p2_manifest.get("summary", {}).get("pending_reconciliation_count"), 12)
    require_equal("p2.summary.report_grade_visible", p2_manifest.get("summary", {}).get("report_grade_visible"), "D")
    require_false_flags(
        "p2.quality_gate",
        p2_manifest.get("quality_gate", {}),
        (
            "bank_operation_allowed",
            "business_decision_basis_allowed",
            "complete_trusted_report_display_allowed",
            "formal_report_allowed",
            "github_upload_allowed",
            "invoice_api_call_allowed",
            "invoice_issuance_allowed",
            "invoice_operation_allowed",
            "loan_management_action_allowed",
            "payment_approval_allowed",
            "payment_execution_allowed",
            "raw_layer_write_allowed",
            "s14_p3_allowed",
            "stage14_review_allowed",
            "tax_declaration_generation_allowed",
            "tax_filing_allowed",
        ),
    )
    require_public_safety("p2", p2_manifest)

    require_equal("p3.stage_phase", p3_manifest.get("stage_phase"), "S14-P3")
    require_equal(
        "p3.runtime_status",
        p3_manifest.get("runtime_status"),
        "public_safe_policy_evidence_gaps_created_formal_policy_conclusions_blocked",
    )
    require_equal("p3.summary.policy_program_count", p3_manifest.get("summary", {}).get("policy_program_count"), 5)
    require_equal("p3.summary.evidence_directory_count", p3_manifest.get("summary", {}).get("evidence_directory_count"), 5)
    require_equal("p3.summary.evidence_gap_count", p3_manifest.get("summary", {}).get("evidence_gap_count"), 5)
    require_equal("p3.summary.risk_tip_count", p3_manifest.get("summary", {}).get("risk_tip_count"), 5)
    require_equal("p3.summary.pending_reconciliation_count", p3_manifest.get("summary", {}).get("pending_reconciliation_count"), 12)
    require_equal("p3.summary.report_grade_visible", p3_manifest.get("summary", {}).get("report_grade_visible"), "D")
    require_false_flags(
        "p3.quality_gate",
        p3_manifest.get("quality_gate", {}),
        (
            "bank_operation_allowed",
            "business_decision_basis_allowed",
            "complete_trusted_report_display_allowed",
            "external_connector_action_allowed",
            "formal_report_allowed",
            "github_upload_allowed",
            "invoice_issuance_allowed",
            "invoice_operation_allowed",
            "loan_management_action_allowed",
            "payment_approval_allowed",
            "payment_execution_allowed",
            "policy_application_submission_allowed",
            "policy_qualification_conclusion_allowed",
            "raw_layer_write_allowed",
            "stage14_review_allowed",
            "subsidy_application_allowed",
            "tax_declaration_generation_allowed",
            "tax_filing_allowed",
        ),
    )
    require_public_safety("p3", p3_manifest)

    counts = {
        "fund_cash_loan_source_lane_count": len(p1_source_lanes),
        "cash_pressure_record_count": len(p1_cash_pressure),
        "loan_due_alert_count": len(p1_loan_due_alerts),
        "account_balance_summary_count": len(p1_account_summaries),
        "invoice_tax_source_lane_count": len(p2_source_lanes),
        "invoice_tax_issue_candidate_count": len(p2_issue_candidates),
        "invoice_tax_cash_summary_count": len(p2_cash_summaries),
        "policy_evidence_directory_count": len(p3_directories),
        "policy_evidence_gap_count": len(p3_gaps),
        "policy_risk_tip_count": len(p3_risk_tips),
        "pending_reconciliation_count": int(p3_manifest.get("summary", {}).get("pending_reconciliation_count")),
        "html_export_count": sum(1 for path in (p1_html_path, p2_html_path, p3_html_path) if path.exists()),
    }
    for key, expected in {
        "fund_cash_loan_source_lane_count": 4,
        "cash_pressure_record_count": 4,
        "loan_due_alert_count": 3,
        "account_balance_summary_count": 3,
        "invoice_tax_source_lane_count": 3,
        "invoice_tax_issue_candidate_count": 3,
        "invoice_tax_cash_summary_count": 3,
        "policy_evidence_directory_count": 5,
        "policy_evidence_gap_count": 5,
        "policy_risk_tip_count": 5,
        "pending_reconciliation_count": 12,
        "html_export_count": 3,
    }.items():
        require_equal(key, counts[key], expected)

    review_counts = review_manifest.get("review_counts")
    if not isinstance(review_counts, dict):
        fail("review_counts: expected object")
    for key, expected in {
        "fund_cash_loan_source_lane_count": 4,
        "cash_pressure_record_count": 4,
        "loan_due_alert_count": 3,
        "account_balance_summary_count": 3,
        "invoice_tax_source_lane_count": 3,
        "invoice_tax_issue_candidate_count": 3,
        "invoice_tax_cash_summary_count": 3,
        "policy_evidence_directory_count": 5,
        "policy_evidence_gap_count": 5,
        "policy_risk_tip_count": 5,
        "pending_reconciliation_count": 12,
        "html_export_count": 3,
        "formal_report_count": 0,
        "business_decision_basis_count": 0,
        "payment_or_bank_operation_count": 0,
        "loan_management_action_count": 0,
        "tax_filing_count": 0,
        "invoice_issuance_count": 0,
        "policy_qualification_conclusion_count": 0,
        "policy_application_submission_count": 0,
        "lineage_full_check_count": 0,
        "github_upload_count": 0,
        "s15_scope_count": 0,
        "full_kmfa_unit_tests": 191,
    }.items():
        require_equal(f"review_counts.{key}", review_counts.get(key), expected)
    counts["full_kmfa_unit_tests"] = int(review_counts["full_kmfa_unit_tests"])

    return counts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA Stage 14 review evidence and gates.")
    parser.add_argument("--review-manifest", type=Path, default=DEFAULT_REVIEW_MANIFEST)
    parser.add_argument("--p1-manifest", type=Path, default=DEFAULT_P1_MANIFEST)
    parser.add_argument("--p2-manifest", type=Path, default=DEFAULT_P2_MANIFEST)
    parser.add_argument("--p3-manifest", type=Path, default=DEFAULT_P3_MANIFEST)
    args = parser.parse_args(argv)

    try:
        counts = validate_stage_review(
            args.review_manifest,
            args.p1_manifest,
            args.p2_manifest,
            args.p3_manifest,
        )
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"FAIL: KMFA S14 stage review check failed ({exc})", file=sys.stderr)
        return 1

    print(
        "PASS: KMFA S14 stage review check passed "
        f"(fund_lanes={counts['fund_cash_loan_source_lane_count']}, "
        f"cash_pressure={counts['cash_pressure_record_count']}, "
        f"invoice_tax_lanes={counts['invoice_tax_source_lane_count']}, "
        f"invoice_tax_issues={counts['invoice_tax_issue_candidate_count']}, "
        f"policy_directories={counts['policy_evidence_directory_count']}, "
        f"policy_gaps={counts['policy_evidence_gap_count']}, "
        f"risk_tips={counts['policy_risk_tip_count']}, "
        f"pending_reconciliation={counts['pending_reconciliation_count']}, "
        "upload_allowed_after_review=true, s15_allowed=false, github_upload_status=not_pushed)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
