#!/usr/bin/env python3
"""Validate KMFA Stage 16 review evidence and gates."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


DEFAULT_REVIEW_MANIFEST = Path("KMFA/stage_artifacts/S16_STAGE_REVIEW/machine/stage16_review_manifest.json")
DEFAULT_P1_MANIFEST = Path("KMFA/stage_artifacts/S16_P1_subcontract_procurement_aggregation/machine/s16_p1_manifest.json")
DEFAULT_P2_MANIFEST = Path("KMFA/stage_artifacts/S16_P2_project_status_lifecycle/machine/s16_p2_manifest.json")
DEFAULT_P3_MANIFEST = Path("KMFA/stage_artifacts/S16_P3_customer_business_analysis/machine/s16_p3_manifest.json")

DEFAULT_SUBCONTRACT_SOURCE_LANES = Path("KMFA/metadata/reports/subcontract_procurement_source_lanes.jsonl")
DEFAULT_SUBCONTRACT_PROJECT_MATCHES = Path("KMFA/metadata/reports/subcontract_project_matches.jsonl")
DEFAULT_SUBCONTRACT_UNALLOCATED_POOL = Path("KMFA/metadata/reports/subcontract_unallocated_cost_pool.jsonl")
DEFAULT_SUBCONTRACT_ANOMALIES = Path("KMFA/metadata/reports/subcontract_anomaly_candidates.jsonl")
DEFAULT_PROJECT_STATUS_SOURCE_LANES = Path("KMFA/metadata/reports/project_status_source_lanes.jsonl")
DEFAULT_PROJECT_LIFECYCLE_RECORDS = Path("KMFA/metadata/reports/project_lifecycle_records.jsonl")
DEFAULT_PROJECT_LIFECYCLE_EXCEPTIONS = Path("KMFA/metadata/reports/project_lifecycle_exception_items.jsonl")
DEFAULT_PROJECT_LIFECYCLE_HANDOFF_GUARDS = Path("KMFA/metadata/reports/project_lifecycle_handoff_guards.jsonl")
DEFAULT_CUSTOMER_SOURCE_LANES = Path("KMFA/metadata/reports/customer_analysis_source_lanes.jsonl")
DEFAULT_CUSTOMER_SUMMARIES = Path("KMFA/metadata/reports/customer_operating_summaries.jsonl")
DEFAULT_CUSTOMER_EXCEPTIONS = Path("KMFA/metadata/reports/customer_analysis_exception_items.jsonl")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


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
) -> dict[str, int]:
    required_paths = [
        review_manifest_path,
        p1_manifest_path,
        p2_manifest_path,
        p3_manifest_path,
        DEFAULT_SUBCONTRACT_SOURCE_LANES,
        DEFAULT_SUBCONTRACT_PROJECT_MATCHES,
        DEFAULT_SUBCONTRACT_UNALLOCATED_POOL,
        DEFAULT_SUBCONTRACT_ANOMALIES,
        DEFAULT_PROJECT_STATUS_SOURCE_LANES,
        DEFAULT_PROJECT_LIFECYCLE_RECORDS,
        DEFAULT_PROJECT_LIFECYCLE_EXCEPTIONS,
        DEFAULT_PROJECT_LIFECYCLE_HANDOFF_GUARDS,
        DEFAULT_CUSTOMER_SOURCE_LANES,
        DEFAULT_CUSTOMER_SUMMARIES,
        DEFAULT_CUSTOMER_EXCEPTIONS,
        Path("KMFA/stage_artifacts/S16_STAGE_REVIEW/human/stage16_review_report.md"),
        Path("KMFA/stage_artifacts/S16_STAGE_REVIEW/human/test_results.md"),
    ]
    missing = [str(path) for path in required_paths if not path.exists()]
    if missing:
        fail("missing required evidence paths: " + ", ".join(missing))

    forbidden_upload_paths = [
        Path("KMFA/stage_artifacts/S16_STAGE_REVIEW/human/github_upload_record.md"),
        Path("KMFA/stage_artifacts/S16_STAGE_REVIEW/machine/stage16_upload_manifest.json"),
    ]
    unexpected = [str(path) for path in forbidden_upload_paths if path.exists()]
    if unexpected:
        fail("Stage 16 review must not contain upload evidence: " + ", ".join(unexpected))

    review_manifest = read_json(review_manifest_path)
    p1_manifest = read_json(p1_manifest_path)
    p2_manifest = read_json(p2_manifest_path)
    p3_manifest = read_json(p3_manifest_path)

    subcontract_source_lanes = read_jsonl(DEFAULT_SUBCONTRACT_SOURCE_LANES)
    subcontract_matches = read_jsonl(DEFAULT_SUBCONTRACT_PROJECT_MATCHES)
    subcontract_unallocated = read_jsonl(DEFAULT_SUBCONTRACT_UNALLOCATED_POOL)
    subcontract_anomalies = read_jsonl(DEFAULT_SUBCONTRACT_ANOMALIES)
    project_source_lanes = read_jsonl(DEFAULT_PROJECT_STATUS_SOURCE_LANES)
    project_lifecycle_records = read_jsonl(DEFAULT_PROJECT_LIFECYCLE_RECORDS)
    project_exceptions = read_jsonl(DEFAULT_PROJECT_LIFECYCLE_EXCEPTIONS)
    project_handoff_guards = read_jsonl(DEFAULT_PROJECT_LIFECYCLE_HANDOFF_GUARDS)
    customer_source_lanes = read_jsonl(DEFAULT_CUSTOMER_SOURCE_LANES)
    customer_summaries = read_jsonl(DEFAULT_CUSTOMER_SUMMARIES)
    customer_exceptions = read_jsonl(DEFAULT_CUSTOMER_EXCEPTIONS)

    require_equal("stage", review_manifest.get("stage"), "S16")
    require_equal("status", review_manifest.get("status"), "review_passed_upload_ready_local_only")
    require_equal("github_upload_status", review_manifest.get("github_upload_status"), "not_pushed")
    require_true("upload_allowed_after_review", review_manifest.get("upload_allowed_after_review"))
    require_false("github_upload_performed", review_manifest.get("github_upload_performed"))
    require_false("s17_allowed", review_manifest.get("s17_allowed"))
    require_false("lineage_full_check_performed", review_manifest.get("lineage_full_check_performed"))
    require_false("formal_report_generated", review_manifest.get("formal_report_generated"))
    require_false("external_connector_included", review_manifest.get("external_connector_included"))
    require_false("business_decision_basis_allowed", review_manifest.get("business_decision_basis_allowed"))
    require_false("procurement_execution_allowed", review_manifest.get("procurement_execution_allowed"))
    require_false("payment_execution_allowed", review_manifest.get("payment_execution_allowed"))
    require_false("bank_operation_allowed", review_manifest.get("bank_operation_allowed"))
    require_false("site_construction_allowed", review_manifest.get("site_construction_allowed"))
    require_false("safety_signature_allowed", review_manifest.get("safety_signature_allowed"))
    require_false("technical_signature_allowed", review_manifest.get("technical_signature_allowed"))
    require_false("invoice_issuance_allowed", review_manifest.get("invoice_issuance_allowed"))
    require_false("collection_action_allowed", review_manifest.get("collection_action_allowed"))
    require_false("legal_collection_decision_allowed", review_manifest.get("legal_collection_decision_allowed"))
    require_equal("report_grade_visible", review_manifest.get("report_grade_visible"), "D")
    require_equal("pending_reconciliation_count", review_manifest.get("pending_reconciliation_count"), 12)
    require_equal("next_gate_id", review_manifest.get("next_gate_id"), "KMFA-S16-GITHUB-UPLOAD-GATE")
    require_equal("open_review_finding_count", review_manifest.get("open_review_finding_count"), 0)
    require_public_safety("review", review_manifest)

    for phase in ("S16-P1", "S16-P2", "S16-P3"):
        require_phase_status(review_manifest.get("stage_phase_status"), phase)
    require_existing_refs(review_manifest.get("evidence_refs"))

    require_equal("p1.stage_phase", p1_manifest.get("stage_phase"), "S16-P1")
    require_equal("p1.summary.source_lane_count", p1_manifest.get("summary", {}).get("source_lane_count"), 4)
    require_equal("p1.summary.project_match_count", p1_manifest.get("summary", {}).get("project_match_count"), 5)
    require_equal("p1.summary.unallocated_cost_pool_count", p1_manifest.get("summary", {}).get("unallocated_cost_pool_count"), 2)
    require_equal("p1.summary.anomaly_candidate_count", p1_manifest.get("summary", {}).get("anomaly_candidate_count"), 4)
    require_false_flags(
        "p1.quality_gate",
        p1_manifest.get("quality_gate", {}),
        (
            "procurement_execution_allowed",
            "payment_approval_allowed",
            "payment_execution_allowed",
            "bank_operation_allowed",
            "supplier_settlement_action_allowed",
            "business_decision_basis_allowed",
            "formal_report_allowed",
            "stage16_review_allowed",
            "github_upload_allowed",
        ),
    )
    require_public_safety("p1", p1_manifest)

    require_equal("p2.stage_phase", p2_manifest.get("stage_phase"), "S16-P2")
    require_equal("p2.summary.source_lane_count", p2_manifest.get("summary", {}).get("source_lane_count"), 6)
    require_equal("p2.summary.lifecycle_record_count", p2_manifest.get("summary", {}).get("lifecycle_record_count"), 4)
    require_equal("p2.summary.exception_item_count", p2_manifest.get("summary", {}).get("exception_item_count"), 3)
    require_equal("p2.summary.handoff_guard_count", p2_manifest.get("summary", {}).get("handoff_guard_count"), 3)
    require_false_flags(
        "p2.quality_gate",
        p2_manifest.get("quality_gate", {}),
        (
            "site_operation_allowed",
            "site_construction_instruction_allowed",
            "safety_signature_allowed",
            "technical_signature_allowed",
            "technical_acceptance_signature_allowed",
            "settlement_confirmation_allowed",
            "invoice_issuance_allowed",
            "collection_action_allowed",
            "payment_execution_allowed",
            "bank_operation_allowed",
            "business_decision_basis_allowed",
            "formal_report_allowed",
            "stage16_review_allowed",
            "github_upload_allowed",
        ),
    )
    require_public_safety("p2", p2_manifest)

    require_equal("p3.stage_phase", p3_manifest.get("stage_phase"), "S16-P3")
    require_equal("p3.summary.source_lane_count", p3_manifest.get("summary", {}).get("source_lane_count"), 5)
    require_equal("p3.summary.customer_summary_count", p3_manifest.get("summary", {}).get("customer_summary_count"), 4)
    require_equal("p3.summary.exception_item_count", p3_manifest.get("summary", {}).get("exception_item_count"), 4)
    require_false_flags(
        "p3.quality_gate",
        p3_manifest.get("quality_gate", {}),
        (
            "auto_customer_contact_allowed",
            "collection_action_allowed",
            "legal_collection_decision_allowed",
            "invoice_issuance_allowed",
            "payment_execution_allowed",
            "bank_operation_allowed",
            "business_decision_basis_allowed",
            "formal_report_allowed",
            "stage16_review_allowed",
            "github_upload_allowed",
            "s17_allowed",
        ),
    )
    require_public_safety("p3", p3_manifest)

    counts = review_manifest.get("review_counts", {})
    expected_counts = {
        "subcontract_source_lane_count": len(subcontract_source_lanes),
        "subcontract_project_match_count": len(subcontract_matches),
        "unallocated_cost_pool_count": len(subcontract_unallocated),
        "subcontract_anomaly_candidate_count": len(subcontract_anomalies),
        "project_status_source_lane_count": len(project_source_lanes),
        "project_lifecycle_record_count": len(project_lifecycle_records),
        "project_lifecycle_exception_item_count": len(project_exceptions),
        "project_lifecycle_handoff_guard_count": len(project_handoff_guards),
        "customer_analysis_source_lane_count": len(customer_source_lanes),
        "customer_operating_summary_count": len(customer_summaries),
        "customer_analysis_exception_item_count": len(customer_exceptions),
        "pending_reconciliation_count": 12,
        "formal_report_count": 0,
        "business_decision_basis_count": 0,
        "procurement_execution_count": 0,
        "payment_execution_count": 0,
        "bank_operation_count": 0,
        "site_construction_count": 0,
        "signature_operation_count": 0,
        "invoice_issuance_count": 0,
        "collection_action_count": 0,
        "legal_collection_decision_count": 0,
        "lineage_full_check_count": 0,
        "github_upload_count": 0,
        "s17_scope_count": 0,
        "full_kmfa_unit_tests": 227,
    }
    for key, expected in expected_counts.items():
        require_equal(f"review_counts.{key}", counts.get(key), expected)

    boundaries = review_manifest.get("scope_boundary", {})
    require_true("scope_boundary.stage16_review_scope_included", boundaries.get("stage16_review_scope_included"))
    require_false("scope_boundary.github_upload_scope_included", boundaries.get("github_upload_scope_included"))
    require_false("scope_boundary.s17_scope_included", boundaries.get("s17_scope_included"))
    require_false("scope_boundary.lineage_full_check_scope_included", boundaries.get("lineage_full_check_scope_included"))
    require_false("scope_boundary.formal_report_runtime_scope_included", boundaries.get("formal_report_runtime_scope_included"))
    require_false("scope_boundary.business_release_scope_included", boundaries.get("business_release_scope_included"))
    require_false("scope_boundary.external_connector_scope_included", boundaries.get("external_connector_scope_included"))

    return dict(counts)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA Stage 16 review evidence and gates.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_REVIEW_MANIFEST)
    args = parser.parse_args(argv)

    try:
        counts = validate_stage_review(args.manifest)
    except Exception as exc:
        print(f"FAIL: KMFA Stage 16 review check failed: {exc}", file=sys.stderr)
        return 1

    print(
        "PASS: KMFA Stage 16 review check passed "
        f"(subcontract_matches={counts['subcontract_project_match_count']}, "
        f"lifecycle_records={counts['project_lifecycle_record_count']}, "
        f"customer_summaries={counts['customer_operating_summary_count']}, "
        "formal_report=false, business_decision_basis=false, payment=false, bank=false, "
        "collection=false, legal=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
