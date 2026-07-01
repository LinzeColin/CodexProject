#!/usr/bin/env python3
"""Validate KMFA Stage 13 review evidence and gates."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


DEFAULT_REVIEW_MANIFEST = Path("KMFA/stage_artifacts/S13_STAGE_REVIEW/machine/stage13_review_manifest.json")
DEFAULT_P1_MANIFEST = Path("KMFA/stage_artifacts/S13_P1_financial_operating_report/machine/s13_p1_manifest.json")
DEFAULT_P2_MANIFEST = Path("KMFA/stage_artifacts/S13_P2_collection_receivable_aging/machine/s13_p2_manifest.json")
DEFAULT_P3_MANIFEST = Path("KMFA/stage_artifacts/S13_P3_cross_table_review/machine/s13_p3_manifest.json")

DEFAULT_P1_SOURCE_LANES = Path("KMFA/metadata/reports/financial_operating_report_source_lanes.jsonl")
DEFAULT_P1_DRAFTS = Path("KMFA/metadata/reports/financial_operating_report_drafts.jsonl")
DEFAULT_P2_SOURCE_LANES = Path("KMFA/metadata/reports/collection_receivable_aging_source_lanes.jsonl")
DEFAULT_P2_PRIORITY_ITEMS = Path("KMFA/metadata/reports/collection_receivable_aging_priority_items.jsonl")
DEFAULT_P2_RESPONSIBILITY_ITEMS = Path("KMFA/metadata/reports/collection_receivable_aging_responsibility_items.jsonl")
DEFAULT_P3_REVIEW_CHECKS = Path("KMFA/metadata/reports/cross_table_review_checks.jsonl")
DEFAULT_P3_DIFFERENCE_QUEUE = Path("KMFA/metadata/reports/cross_table_difference_queue.jsonl")
DEFAULT_P3_QUALITY_REPORT = Path("KMFA/metadata/reports/operating_report_quality_report.json")

DEFAULT_P1_WEEKLY_HTML = Path("KMFA/stage_artifacts/S13_P1_financial_operating_report/exports/html/financial_operating_weekly_draft.html")
DEFAULT_P1_MONTHLY_HTML = Path("KMFA/stage_artifacts/S13_P1_financial_operating_report/exports/html/financial_operating_monthly_draft.html")
DEFAULT_P2_HTML = Path("KMFA/stage_artifacts/S13_P2_collection_receivable_aging/exports/html/collection_receivable_aging_priority.html")
DEFAULT_P3_HTML = Path("KMFA/stage_artifacts/S13_P3_cross_table_review/exports/html/cross_table_quality_report.html")


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
    p1_drafts_path: Path = DEFAULT_P1_DRAFTS,
    p2_source_lanes_path: Path = DEFAULT_P2_SOURCE_LANES,
    p2_priority_items_path: Path = DEFAULT_P2_PRIORITY_ITEMS,
    p2_responsibility_items_path: Path = DEFAULT_P2_RESPONSIBILITY_ITEMS,
    p3_review_checks_path: Path = DEFAULT_P3_REVIEW_CHECKS,
    p3_difference_queue_path: Path = DEFAULT_P3_DIFFERENCE_QUEUE,
    p3_quality_report_path: Path = DEFAULT_P3_QUALITY_REPORT,
    p1_weekly_html_path: Path = DEFAULT_P1_WEEKLY_HTML,
    p1_monthly_html_path: Path = DEFAULT_P1_MONTHLY_HTML,
    p2_html_path: Path = DEFAULT_P2_HTML,
    p3_html_path: Path = DEFAULT_P3_HTML,
) -> dict[str, int]:
    required_paths = [
        review_manifest_path,
        p1_manifest_path,
        p2_manifest_path,
        p3_manifest_path,
        p1_source_lanes_path,
        p1_drafts_path,
        p2_source_lanes_path,
        p2_priority_items_path,
        p2_responsibility_items_path,
        p3_review_checks_path,
        p3_difference_queue_path,
        p3_quality_report_path,
        p1_weekly_html_path,
        p1_monthly_html_path,
        p2_html_path,
        p3_html_path,
        Path("KMFA/stage_artifacts/S13_STAGE_REVIEW/human/stage13_review_report.md"),
        Path("KMFA/stage_artifacts/S13_STAGE_REVIEW/human/test_results.md"),
    ]
    missing = [str(path) for path in required_paths if not path.exists()]
    if missing:
        fail("missing required evidence paths: " + ", ".join(missing))

    forbidden_upload_paths = [
        Path("KMFA/stage_artifacts/S13_STAGE_REVIEW/human/github_upload_record.md"),
        Path("KMFA/stage_artifacts/S13_STAGE_REVIEW/machine/stage13_upload_manifest.json"),
    ]
    unexpected = [str(path) for path in forbidden_upload_paths if path.exists()]
    if unexpected:
        fail("Stage 13 review must not contain upload evidence: " + ", ".join(unexpected))

    review_manifest = read_json(review_manifest_path)
    p1_manifest = read_json(p1_manifest_path)
    p2_manifest = read_json(p2_manifest_path)
    p3_manifest = read_json(p3_manifest_path)
    quality_report = read_json(p3_quality_report_path)

    p1_source_lanes = read_jsonl(p1_source_lanes_path)
    p1_drafts = read_jsonl(p1_drafts_path)
    p2_source_lanes = read_jsonl(p2_source_lanes_path)
    p2_priority_items = read_jsonl(p2_priority_items_path)
    p2_responsibility_items = read_jsonl(p2_responsibility_items_path)
    p3_review_checks = read_jsonl(p3_review_checks_path)
    p3_difference_queue = read_jsonl(p3_difference_queue_path)

    require_equal("stage", review_manifest.get("stage"), "S13")
    require_equal("status", review_manifest.get("status"), "review_passed_upload_ready_local_only")
    require_equal("github_upload_status", review_manifest.get("github_upload_status"), "not_pushed")
    require_true("upload_allowed_after_review", review_manifest.get("upload_allowed_after_review"))
    require_false("github_upload_performed", review_manifest.get("github_upload_performed"))
    require_false("s14_allowed", review_manifest.get("s14_allowed"))
    require_false("lineage_full_check_performed", review_manifest.get("lineage_full_check_performed"))
    require_false("formal_report_generated", review_manifest.get("formal_report_generated"))
    require_false("external_connector_included", review_manifest.get("external_connector_included"))
    require_false("business_decision_basis_allowed", review_manifest.get("business_decision_basis_allowed"))
    require_false("full_trusted_report_allowed", review_manifest.get("full_trusted_report_allowed"))
    require_equal("report_grade_visible", review_manifest.get("report_grade_visible"), "D")
    require_equal("pending_reconciliation_count", review_manifest.get("pending_reconciliation_count"), 12)
    require_equal("next_gate_id", review_manifest.get("next_gate_id"), "KMFA-S13-GITHUB-UPLOAD-GATE")
    require_equal("open_review_finding_count", review_manifest.get("open_review_finding_count"), 0)
    require_public_safety("review", review_manifest)

    for phase in ("S13-P1", "S13-P2", "S13-P3"):
        require_phase_status(review_manifest.get("stage_phase_status"), phase)
    require_existing_refs(review_manifest.get("evidence_refs"))

    require_equal("p1.stage_phase", p1_manifest.get("stage_phase"), "S13-P1")
    require_equal("p1.status", p1_manifest.get("status"), "completed_validated_local_only")
    require_equal("p1.summary.source_lane_count", p1_manifest.get("summary", {}).get("source_lane_count"), 4)
    require_equal("p1.summary.draft_report_count", p1_manifest.get("summary", {}).get("draft_report_count"), 2)
    require_equal("p1.summary.html_draft_count", p1_manifest.get("summary", {}).get("html_draft_count"), 2)
    require_equal("p1.summary.pending_reconciliation_count", p1_manifest.get("summary", {}).get("pending_reconciliation_count"), 12)
    require_equal("p1.summary.report_grade_visible", p1_manifest.get("summary", {}).get("report_grade_visible"), "D")
    require_false_flags(
        "p1.quality_gate",
        p1_manifest.get("quality_gate", {}),
        (
            "business_decision_basis_allowed",
            "complete_trusted_report_display_allowed",
            "formal_report_allowed",
            "github_upload_allowed",
            "payment_or_bank_operation_allowed",
            "raw_layer_write_allowed",
            "stage13_review_allowed",
        ),
    )
    require_public_safety("p1", p1_manifest)

    require_equal("p2.stage_phase", p2_manifest.get("stage_phase"), "S13-P2")
    require_equal("p2.status", p2_manifest.get("status"), "completed_validated_local_only")
    require_equal("p2.summary.source_lane_count", p2_manifest.get("summary", {}).get("source_lane_count"), 5)
    require_equal("p2.summary.priority_item_count", p2_manifest.get("summary", {}).get("priority_item_count"), 4)
    require_equal("p2.summary.responsibility_item_count", p2_manifest.get("summary", {}).get("responsibility_item_count"), 4)
    require_equal("p2.summary.pending_reconciliation_count", p2_manifest.get("summary", {}).get("pending_reconciliation_count"), 12)
    require_equal("p2.summary.report_grade_visible", p2_manifest.get("summary", {}).get("report_grade_visible"), "D")
    require_false_flags(
        "p2.quality_gate",
        p2_manifest.get("quality_gate", {}),
        (
            "business_decision_basis_allowed",
            "complete_trusted_report_display_allowed",
            "formal_report_allowed",
            "github_upload_allowed",
            "legal_collection_decision_allowed",
            "payment_or_bank_operation_allowed",
            "raw_layer_write_allowed",
            "stage13_review_allowed",
        ),
    )
    require_public_safety("p2", p2_manifest)

    require_equal("p3.stage_phase", p3_manifest.get("stage_phase"), "S13-P3")
    require_equal(
        "p3.runtime_status",
        p3_manifest.get("runtime_status"),
        "public_safe_cross_table_review_completed_with_pending_difference_queue",
    )
    require_equal("p3.summary.review_dimension_count", p3_manifest.get("summary", {}).get("review_dimension_count"), 4)
    require_equal("p3.summary.difference_queue_count", p3_manifest.get("summary", {}).get("difference_queue_count"), 4)
    require_equal("p3.summary.quality_report_count", p3_manifest.get("summary", {}).get("quality_report_count"), 1)
    require_equal("p3.summary.pending_reconciliation_count", p3_manifest.get("summary", {}).get("pending_reconciliation_count"), 12)
    require_equal("p3.summary.report_grade_visible", p3_manifest.get("summary", {}).get("report_grade_visible"), "D")
    require_false_flags(
        "p3.quality_gate",
        p3_manifest.get("quality_gate", {}),
        (
            "business_decision_basis_allowed",
            "complete_trusted_report_display_allowed",
            "difference_auto_resolution_allowed",
            "formal_report_allowed",
            "github_upload_allowed",
            "legal_collection_decision_allowed",
            "payment_or_bank_operation_allowed",
            "raw_layer_write_allowed",
            "stage13_review_allowed",
        ),
    )
    require_public_safety("p3", p3_manifest)

    require_equal("quality_report.record_type", quality_report.get("record_type"), "operating_report_quality_report")
    require_equal("quality_report.review_dimension_count", quality_report.get("review_dimension_count"), 4)
    require_equal("quality_report.difference_queue_count", quality_report.get("difference_queue_count"), 4)
    require_equal("quality_report.pending_reconciliation_count", quality_report.get("pending_reconciliation_count"), 12)
    require_equal("quality_report.report_grade_visible", quality_report.get("report_grade_visible"), "D")
    require_false("quality_report.formal_report_allowed", quality_report.get("formal_report_allowed"))
    require_false("quality_report.business_decision_basis_allowed", quality_report.get("business_decision_basis_allowed"))
    require_false("quality_report.lineage_full_check_included", quality_report.get("lineage_full_check_included"))
    require_false("quality_report.github_upload_scope_included", quality_report.get("github_upload_scope_included"))

    counts = {
        "financial_operating_source_lane_count": len(p1_source_lanes),
        "financial_operating_draft_count": len(p1_drafts),
        "collection_receivable_source_lane_count": len(p2_source_lanes),
        "collection_receivable_priority_item_count": len(p2_priority_items),
        "collection_receivable_responsibility_item_count": len(p2_responsibility_items),
        "cross_table_review_dimension_count": len(p3_review_checks),
        "cross_table_difference_queue_count": len(p3_difference_queue),
        "operating_quality_report_count": 1 if quality_report else 0,
        "pending_reconciliation_count": int(p3_manifest.get("summary", {}).get("pending_reconciliation_count")),
        "html_export_count": sum(
            1 for path in (p1_weekly_html_path, p1_monthly_html_path, p2_html_path, p3_html_path) if path.exists()
        ),
    }
    for key, expected in {
        "financial_operating_source_lane_count": 4,
        "financial_operating_draft_count": 2,
        "collection_receivable_source_lane_count": 5,
        "collection_receivable_priority_item_count": 4,
        "collection_receivable_responsibility_item_count": 4,
        "cross_table_review_dimension_count": 4,
        "cross_table_difference_queue_count": 4,
        "operating_quality_report_count": 1,
        "pending_reconciliation_count": 12,
        "html_export_count": 4,
    }.items():
        require_equal(key, counts[key], expected)

    review_counts = review_manifest.get("review_counts")
    if not isinstance(review_counts, dict):
        fail("review_counts: expected object")
    for key, expected in {
        "financial_operating_source_lane_count": 4,
        "financial_operating_draft_count": 2,
        "collection_receivable_source_lane_count": 5,
        "collection_receivable_priority_item_count": 4,
        "collection_receivable_responsibility_item_count": 4,
        "cross_table_review_dimension_count": 4,
        "cross_table_difference_queue_count": 4,
        "operating_quality_report_count": 1,
        "pending_reconciliation_count": 12,
        "html_export_count": 4,
        "formal_report_count": 0,
        "business_decision_basis_count": 0,
        "lineage_full_check_count": 0,
        "github_upload_count": 0,
        "s14_scope_count": 0,
        "full_kmfa_unit_tests": 172,
    }.items():
        require_equal(f"review_counts.{key}", review_counts.get(key), expected)
    counts["full_kmfa_unit_tests"] = int(review_counts["full_kmfa_unit_tests"])

    return counts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA Stage 13 review evidence and gates.")
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
        print(f"FAIL: KMFA S13 stage review check failed ({exc})", file=sys.stderr)
        return 1

    print(
        "PASS: KMFA S13 stage review check passed "
        f"(financial_lanes={counts['financial_operating_source_lane_count']}, "
        f"drafts={counts['financial_operating_draft_count']}, "
        f"collection_lanes={counts['collection_receivable_source_lane_count']}, "
        f"priority_items={counts['collection_receivable_priority_item_count']}, "
        f"review_dimensions={counts['cross_table_review_dimension_count']}, "
        f"difference_queue={counts['cross_table_difference_queue_count']}, "
        f"quality_reports={counts['operating_quality_report_count']}, "
        f"pending_reconciliation={counts['pending_reconciliation_count']}, "
        "upload_allowed_after_review=true, s14_allowed=false, github_upload_status=not_pushed)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
