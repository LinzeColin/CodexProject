#!/usr/bin/env python3
"""Validate KMFA Stage 9 review evidence and gates."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


DEFAULT_REVIEW_MANIFEST = Path("KMFA/stage_artifacts/S09_STAGE_REVIEW/machine/stage9_review_manifest.json")
DEFAULT_P1_MANIFEST = Path("KMFA/stage_artifacts/S09_P1_project_cost_fact_layer/machine/s09_p1_manifest.json")
DEFAULT_P2_MANIFEST = Path("KMFA/stage_artifacts/S09_P2_margin_cash_margin/machine/s09_p2_manifest.json")
DEFAULT_P3_MANIFEST = Path("KMFA/stage_artifacts/S09_P3_scope_reconciliation/machine/s09_p3_manifest.json")

DEFAULT_FACT_RECORDS = Path("KMFA/metadata/lineage/project_cost_fact_records.jsonl")
DEFAULT_UNALLOCATED_POOL = Path("KMFA/metadata/lineage/unallocated_project_cost_pool.jsonl")
DEFAULT_MARGIN_RECORDS = Path("KMFA/metadata/lineage/project_margin_cash_margin_records.jsonl")
DEFAULT_SCOPE_DIFFERENCES = Path("KMFA/metadata/quality/scope_difference_summary.jsonl")
DEFAULT_RECONCILIATION_RECORDS = Path("KMFA/metadata/quality/scope_reconciliation_records.jsonl")
DEFAULT_DOMAIN_CONTROLS = Path("KMFA/metadata/quality/scope_reconciliation_domain_controls.jsonl")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl_count(path: Path) -> int:
    count = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        json.loads(line)
        count += 1
    return count


def fail(message: str) -> None:
    raise ValueError(message)


def require_equal(label: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        fail(f"{label}: expected {expected!r}, got {actual!r}")


def require_false(label: str, actual: Any) -> None:
    if actual is not False:
        fail(f"{label}: expected false, got {actual!r}")


def validate_stage_review(
    review_manifest_path: Path,
    p1_manifest_path: Path,
    p2_manifest_path: Path,
    p3_manifest_path: Path,
    fact_records_path: Path,
    unallocated_pool_path: Path,
    margin_records_path: Path,
    scope_differences_path: Path,
    reconciliation_records_path: Path,
    domain_controls_path: Path,
) -> dict[str, int]:
    required_paths = [
        review_manifest_path,
        p1_manifest_path,
        p2_manifest_path,
        p3_manifest_path,
        fact_records_path,
        unallocated_pool_path,
        margin_records_path,
        scope_differences_path,
        reconciliation_records_path,
        domain_controls_path,
    ]
    missing = [str(path) for path in required_paths if not path.exists()]
    if missing:
        fail("missing required evidence paths: " + ", ".join(missing))

    review_manifest = read_json(review_manifest_path)
    p1_manifest = read_json(p1_manifest_path)
    p2_manifest = read_json(p2_manifest_path)
    p3_manifest = read_json(p3_manifest_path)

    require_equal("stage", review_manifest.get("stage"), "S09")
    require_equal("status", review_manifest.get("status"), "pass_upload_ready_local_only")
    require_equal("github_upload_status", review_manifest.get("github_upload_status"), "not_pushed")
    if review_manifest.get("upload_allowed_after_review") is not True:
        fail("upload_allowed_after_review: expected true")
    require_false("upload_performed", review_manifest.get("upload_performed"))
    require_false("s10_allowed", review_manifest.get("s10_allowed"))
    require_false("lineage_full_check_performed", review_manifest.get("lineage_full_check_performed"))
    require_false("formal_report_generated", review_manifest.get("formal_report_generated"))
    require_false("external_connector_included", review_manifest.get("external_connector_included"))

    stage_phase_status = review_manifest.get("stage_phase_status")
    if not isinstance(stage_phase_status, dict):
        fail("stage_phase_status: expected object")
    for phase in ("S09-P1", "S09-P2", "S09-P3"):
        status = stage_phase_status.get(phase)
        if not isinstance(status, str) or not status.startswith("completed_validated_local_only"):
            fail(f"stage_phase_status.{phase}: expected completed_validated_local_only*, got {status!r}")

    for ref in review_manifest.get("evidence_refs", []):
        if not Path(ref).exists():
            fail(f"missing evidence ref: {ref}")

    require_equal("p1.stage_phase", p1_manifest.get("stage_phase"), "S09-P1")
    require_equal("p1.fact_record_count", p1_manifest.get("fact_record_count"), 4)
    require_equal("p1.cost_category_count", p1_manifest.get("cost_category_count"), 9)
    require_equal("p1.unallocated_pool_count", p1_manifest.get("unallocated_pool_count"), 9)
    require_equal("p1.manual_review_queue_count", p1_manifest.get("manual_review_queue_count"), 3)
    require_equal("p1.unresolved_difference_count", p1_manifest.get("unresolved_difference_count"), 1)
    require_false("p1.s09_p2_scope_included", p1_manifest.get("s09_p2_scope_included"))
    require_false("p1.s09_p3_scope_included", p1_manifest.get("s09_p3_scope_included"))
    require_false("p1.formal_report_allowed", p1_manifest.get("formal_report_allowed"))
    require_false("p1.github_upload_allowed", p1_manifest.get("github_upload_allowed"))

    require_equal("p2.stage_phase", p2_manifest.get("stage_phase"), "S09-P2")
    require_equal("p2.margin_record_count", p2_manifest.get("margin_record_count"), 4)
    require_equal("p2.difference_summary_count", p2_manifest.get("difference_summary_count"), 12)
    require_false("p2.s09_p3_scope_included", p2_manifest.get("s09_p3_scope_included"))
    require_false("p2.formal_report_allowed", p2_manifest.get("formal_report_allowed"))
    require_false("p2.github_upload_allowed", p2_manifest.get("github_upload_allowed"))

    require_equal("p3.stage_phase", p3_manifest.get("stage_phase"), "S09-P3")
    require_equal("p3.reconciliation_record_count", p3_manifest.get("reconciliation_record_count"), 12)
    require_equal("p3.domain_control_count", p3_manifest.get("domain_control_count"), 6)
    require_equal("p3.pending_resolution_count", p3_manifest.get("pending_resolution_count"), 12)
    require_equal("p3.confirmed_resolution_count", p3_manifest.get("confirmed_resolution_count"), 0)
    require_false("p3.derived_metric_rerun_allowed", p3_manifest.get("derived_metric_rerun_allowed"))
    require_false("p3.formal_report_allowed", p3_manifest.get("formal_report_allowed"))
    require_false("p3.github_upload_allowed", p3_manifest.get("github_upload_allowed"))
    require_false("p3.stage9_review_allowed", p3_manifest.get("stage9_review_allowed"))

    counts = {
        "project_cost_fact_records": read_jsonl_count(fact_records_path),
        "unallocated_project_cost_pool_records": read_jsonl_count(unallocated_pool_path),
        "project_margin_records": read_jsonl_count(margin_records_path),
        "scope_difference_summary_records": read_jsonl_count(scope_differences_path),
        "scope_reconciliation_records": read_jsonl_count(reconciliation_records_path),
        "scope_reconciliation_domain_controls": read_jsonl_count(domain_controls_path),
    }
    expected_counts = {
        "project_cost_fact_records": 4,
        "unallocated_project_cost_pool_records": 9,
        "project_margin_records": 4,
        "scope_difference_summary_records": 12,
        "scope_reconciliation_records": 12,
        "scope_reconciliation_domain_controls": 6,
    }
    for key, expected in expected_counts.items():
        require_equal(key, counts[key], expected)

    review_counts = review_manifest.get("review_counts")
    if not isinstance(review_counts, dict):
        fail("review_counts: expected object")
    for key, expected in {
        "project_cost_fact_records": 4,
        "cost_categories": 9,
        "unallocated_project_cost_pool_records": 9,
        "project_margin_records": 4,
        "scope_difference_summary_records": 12,
        "scope_reconciliation_records": 12,
        "scope_reconciliation_domain_controls": 6,
        "pending_owner_or_authorized_review_records": 12,
        "confirmed_reconciliation_records": 0,
        "full_kmfa_unit_tests": 100,
    }.items():
        require_equal(f"review_counts.{key}", review_counts.get(key), expected)

    return counts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA Stage 9 review evidence and gates.")
    parser.add_argument("--review-manifest", type=Path, default=DEFAULT_REVIEW_MANIFEST)
    parser.add_argument("--p1-manifest", type=Path, default=DEFAULT_P1_MANIFEST)
    parser.add_argument("--p2-manifest", type=Path, default=DEFAULT_P2_MANIFEST)
    parser.add_argument("--p3-manifest", type=Path, default=DEFAULT_P3_MANIFEST)
    parser.add_argument("--fact-records", type=Path, default=DEFAULT_FACT_RECORDS)
    parser.add_argument("--unallocated-pool", type=Path, default=DEFAULT_UNALLOCATED_POOL)
    parser.add_argument("--margin-records", type=Path, default=DEFAULT_MARGIN_RECORDS)
    parser.add_argument("--scope-differences", type=Path, default=DEFAULT_SCOPE_DIFFERENCES)
    parser.add_argument("--reconciliation-records", type=Path, default=DEFAULT_RECONCILIATION_RECORDS)
    parser.add_argument("--domain-controls", type=Path, default=DEFAULT_DOMAIN_CONTROLS)
    args = parser.parse_args(argv)

    try:
        counts = validate_stage_review(
            args.review_manifest,
            args.p1_manifest,
            args.p2_manifest,
            args.p3_manifest,
            args.fact_records,
            args.unallocated_pool,
            args.margin_records,
            args.scope_differences,
            args.reconciliation_records,
            args.domain_controls,
        )
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"FAIL: KMFA S09 stage review check failed ({exc})", file=sys.stderr)
        return 1

    print(
        "PASS: KMFA S09 stage review check passed "
        f"(project_cost_fact_records={counts['project_cost_fact_records']}, "
        f"project_margin_records={counts['project_margin_records']}, "
        f"scope_reconciliation_records={counts['scope_reconciliation_records']}, "
        "pending_owner_or_authorized_review_records=12, "
        "upload_allowed_after_review=true, s10_allowed=false, github_upload_status=not_pushed)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
