#!/usr/bin/env python3
"""Validate KMFA Stage 18 review evidence and gates."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


DEFAULT_REVIEW_MANIFEST = Path("KMFA/stage_artifacts/S18_STAGE_REVIEW/machine/stage18_review_manifest.json")
DEFAULT_STAGE_GO_NO_GO = Path("KMFA/metadata/quality/stage18_go_no_go_review.json")
DEFAULT_P1_MANIFEST = Path("KMFA/stage_artifacts/S18_P1_precision_stress/machine/s18_p1_manifest.json")
DEFAULT_P2_MANIFEST = Path("KMFA/stage_artifacts/S18_P2_full_regression_acceptance/machine/s18_p2_manifest.json")
DEFAULT_P3_MANIFEST = Path("KMFA/stage_artifacts/S18_P3_integration_preparation/machine/s18_p3_manifest.json")

DEFAULT_PRECISION_SCENARIOS = Path("KMFA/metadata/quality/precision_stress_scenarios.jsonl")
DEFAULT_PRECISION_IMPORT_RUNS = Path("KMFA/metadata/quality/precision_stress_import_runs.jsonl")
DEFAULT_FULL_REGRESSION_CHECKS = Path("KMFA/metadata/quality/full_regression_check_results.jsonl")
DEFAULT_STAGE_ACCEPTANCE_INDEX = Path("KMFA/metadata/quality/stage_acceptance_evidence_index.jsonl")
DEFAULT_CONNECTOR_PLAN = Path("KMFA/metadata/integration/read_only_connector_plan.jsonl")
DEFAULT_OPME_PLAN = Path("KMFA/metadata/integration/opme_entry_integration_plan.json")
DEFAULT_NEXT_STAGE_BACKLOG = Path("KMFA/metadata/integration/next_stage_backlog.jsonl")


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


def _ensure_no_current_s18_p3_pending(stage_go_no_go: dict[str, Any]) -> None:
    blocker_ids = set(stage_go_no_go.get("blocker_ids", []))
    if "S18_P3_PENDING" in blocker_ids:
        fail("Stage 18 review Go/No-Go must clear S18_P3_PENDING")
    require_false("stage_go_no_go.s18_p3_pending", stage_go_no_go.get("s18_p3_pending"))
    require_equal("stage_go_no_go.next_required_gate", stage_go_no_go.get("next_required_gate"), "KMFA-S18-GITHUB-UPLOAD-GATE")


def validate_stage_review(
    review_manifest_path: Path = DEFAULT_REVIEW_MANIFEST,
    stage_go_no_go_path: Path = DEFAULT_STAGE_GO_NO_GO,
    p1_manifest_path: Path = DEFAULT_P1_MANIFEST,
    p2_manifest_path: Path = DEFAULT_P2_MANIFEST,
    p3_manifest_path: Path = DEFAULT_P3_MANIFEST,
) -> dict[str, int]:
    required_paths = [
        review_manifest_path,
        stage_go_no_go_path,
        p1_manifest_path,
        p2_manifest_path,
        p3_manifest_path,
        DEFAULT_PRECISION_SCENARIOS,
        DEFAULT_PRECISION_IMPORT_RUNS,
        DEFAULT_FULL_REGRESSION_CHECKS,
        DEFAULT_STAGE_ACCEPTANCE_INDEX,
        DEFAULT_CONNECTOR_PLAN,
        DEFAULT_OPME_PLAN,
        DEFAULT_NEXT_STAGE_BACKLOG,
        Path("KMFA/stage_artifacts/S18_STAGE_REVIEW/human/stage18_review_report.md"),
        Path("KMFA/stage_artifacts/S18_STAGE_REVIEW/human/test_results.md"),
    ]
    missing = [str(path) for path in required_paths if not path.exists()]
    if missing:
        fail("missing required evidence paths: " + ", ".join(missing))

    forbidden_upload_paths = [
        Path("KMFA/stage_artifacts/S18_STAGE_REVIEW/human/github_upload_record.md"),
        Path("KMFA/stage_artifacts/S18_STAGE_REVIEW/machine/stage18_upload_manifest.json"),
    ]
    unexpected = [str(path) for path in forbidden_upload_paths if path.exists()]
    if unexpected:
        fail("Stage 18 review must not contain upload evidence: " + ", ".join(unexpected))

    review_manifest = read_json(review_manifest_path)
    stage_go_no_go = read_json(stage_go_no_go_path)
    p1_manifest = read_json(p1_manifest_path)
    p2_manifest = read_json(p2_manifest_path)
    p3_manifest = read_json(p3_manifest_path)

    precision_scenarios = read_jsonl(DEFAULT_PRECISION_SCENARIOS)
    precision_import_runs = read_jsonl(DEFAULT_PRECISION_IMPORT_RUNS)
    full_regression_checks = read_jsonl(DEFAULT_FULL_REGRESSION_CHECKS)
    stage_acceptance_index = read_jsonl(DEFAULT_STAGE_ACCEPTANCE_INDEX)
    connector_plan = read_jsonl(DEFAULT_CONNECTOR_PLAN)
    opme_plan = read_json(DEFAULT_OPME_PLAN)
    next_stage_backlog = read_jsonl(DEFAULT_NEXT_STAGE_BACKLOG)

    require_equal("stage", review_manifest.get("stage"), "S18")
    require_equal("status", review_manifest.get("status"), "review_passed_upload_ready_local_only_no_go")
    require_equal("github_upload_status", review_manifest.get("github_upload_status"), "not_pushed")
    require_equal("next_gate_id", review_manifest.get("next_gate_id"), "KMFA-S18-GITHUB-UPLOAD-GATE")
    require_true("upload_allowed_after_review", review_manifest.get("upload_allowed_after_review"))
    require_true("stage18_review_performed", review_manifest.get("stage18_review_performed"))
    require_false("github_upload_performed", review_manifest.get("github_upload_performed"))
    require_false("delivery_allowed", review_manifest.get("delivery_allowed"))
    require_false("lineage_full_check_performed", review_manifest.get("lineage_full_check_performed"))
    require_false("formal_report_generated", review_manifest.get("formal_report_generated"))
    require_false("official_report_release_allowed", review_manifest.get("official_report_release_allowed"))
    require_false("external_connector_included", review_manifest.get("external_connector_included"))
    require_false("live_connector_allowed", review_manifest.get("live_connector_allowed"))
    require_false("opme_deep_coupling_allowed", review_manifest.get("opme_deep_coupling_allowed"))
    require_false("production_restore_allowed", review_manifest.get("production_restore_allowed"))
    require_false("business_decision_basis_allowed", review_manifest.get("business_decision_basis_allowed"))
    require_false("business_execution_allowed", review_manifest.get("business_execution_allowed"))
    require_false("procurement_execution_allowed", review_manifest.get("procurement_execution_allowed"))
    require_false("payment_approval_allowed", review_manifest.get("payment_approval_allowed"))
    require_false("payment_execution_allowed", review_manifest.get("payment_execution_allowed"))
    require_false("bank_operation_allowed", review_manifest.get("bank_operation_allowed"))
    require_false("site_construction_allowed", review_manifest.get("site_construction_allowed"))
    require_false("safety_signature_allowed", review_manifest.get("safety_signature_allowed"))
    require_false("technical_signature_allowed", review_manifest.get("technical_signature_allowed"))
    require_false("invoice_issuance_allowed", review_manifest.get("invoice_issuance_allowed"))
    require_false("collection_action_allowed", review_manifest.get("collection_action_allowed"))
    require_false("legal_collection_decision_allowed", review_manifest.get("legal_collection_decision_allowed"))
    require_false("salary_action_allowed", review_manifest.get("salary_action_allowed"))
    require_false("tax_formal_action_allowed", review_manifest.get("tax_formal_action_allowed"))
    require_equal("report_grade_visible", review_manifest.get("report_grade_visible"), "D")
    require_equal("pending_reconciliation_count", review_manifest.get("pending_reconciliation_count"), 12)
    require_equal("open_review_finding_count", review_manifest.get("open_review_finding_count"), 0)
    require_equal("fixed_review_finding_count", review_manifest.get("fixed_review_finding_count"), 1)
    require_public_safety("review", review_manifest)
    require_existing_refs(review_manifest.get("evidence_refs"))

    for phase in ("S18-P1", "S18-P2", "S18-P3"):
        require_phase_status(review_manifest.get("stage_phase_status"), phase)

    require_equal("stage_go_no_go.record_type", stage_go_no_go.get("record_type"), "s18_stage_review_go_no_go")
    require_equal("stage_go_no_go.decision", stage_go_no_go.get("decision"), "NO_GO")
    require_false("stage_go_no_go.delivery_allowed", stage_go_no_go.get("delivery_allowed"))
    require_true("stage_go_no_go.stage18_review_passed", stage_go_no_go.get("stage18_review_passed"))
    require_true("stage_go_no_go.github_upload_allowed_after_review", stage_go_no_go.get("github_upload_allowed_after_review"))
    require_false("stage_go_no_go.github_upload_performed", stage_go_no_go.get("github_upload_performed"))
    require_false("stage_go_no_go.official_report_release_allowed", stage_go_no_go.get("official_report_release_allowed"))
    require_false("stage_go_no_go.business_execution_allowed", stage_go_no_go.get("business_execution_allowed"))
    _ensure_no_current_s18_p3_pending(stage_go_no_go)

    require_equal("p1.stage_phase", p1_manifest.get("stage_phase"), "S18-P1")
    require_equal("p1.summary.scenario_count", p1_manifest.get("summary", {}).get("scenario_count"), 5)
    require_equal("p1.summary.consecutive_import_run_count", p1_manifest.get("summary", {}).get("consecutive_import_run_count"), 3)
    require_equal("p1.summary.large_batch_file_count", p1_manifest.get("summary", {}).get("large_batch_file_count"), 1200)
    require_true("p1.quality_gate.metadata_only", p1_manifest.get("quality_gate", {}).get("metadata_only"))
    require_false_flags(
        "p1.quality_gate",
        p1_manifest.get("quality_gate", {}),
        (
            "business_decision_basis_allowed",
            "business_execution_allowed",
            "external_connector_allowed",
            "formal_report_allowed",
            "github_upload_allowed",
            "lineage_full_check_allowed",
            "production_restore_allowed",
        ),
    )
    require_public_safety("p1", p1_manifest)

    require_equal("p2.stage_phase", p2_manifest.get("stage_phase"), "S18-P2")
    require_equal("p2.summary.check_category_count", p2_manifest.get("summary", {}).get("check_category_count"), 5)
    require_equal("p2.summary.stage_evidence_count", p2_manifest.get("summary", {}).get("stage_evidence_count"), 18)
    require_equal("p2.summary.go_no_go_decision", p2_manifest.get("summary", {}).get("go_no_go_decision"), "NO_GO")
    require_false_flags(
        "p2.quality_gate",
        p2_manifest.get("quality_gate", {}),
        (
            "business_decision_basis_allowed",
            "business_execution_allowed",
            "external_connector_allowed",
            "github_upload_allowed",
            "lineage_full_check_complete",
            "official_report_release_allowed",
            "production_restore_allowed",
        ),
    )
    require_public_safety("p2", p2_manifest)

    require_equal("p3.stage_phase", p3_manifest.get("stage_phase"), "S18-P3")
    require_equal("p3.summary.connector_plan_count", p3_manifest.get("summary", {}).get("connector_plan_count"), 3)
    require_equal("p3.summary.opme_entry_surface_count", p3_manifest.get("summary", {}).get("opme_entry_surface_count"), 4)
    require_equal("p3.summary.backlog_item_count", p3_manifest.get("summary", {}).get("backlog_item_count"), 6)
    require_false_flags(
        "p3.quality_gate",
        p3_manifest.get("quality_gate", {}),
        (
            "business_decision_basis_allowed",
            "business_execution_allowed",
            "credential_required_now",
            "delivery_allowed",
            "external_connector_allowed",
            "external_connector_called",
            "github_upload_allowed",
            "lineage_full_check_complete",
            "live_connector_called",
            "official_report_release_allowed",
            "production_restore_allowed",
            "source_mutation_allowed",
            "stage18_review_allowed_in_this_phase",
        ),
    )
    require_public_safety("p3", p3_manifest)

    expected_counts = {
        "precision_scenario_count": len(precision_scenarios),
        "precision_import_run_count": len(precision_import_runs),
        "large_batch_file_count": p1_manifest.get("summary", {}).get("large_batch_file_count"),
        "full_regression_check_count": len(full_regression_checks),
        "stage_acceptance_evidence_count": len(stage_acceptance_index),
        "read_only_connector_plan_count": len(connector_plan),
        "opme_entry_surface_count": len(opme_plan.get("entry_surfaces", [])),
        "next_stage_backlog_count": len(next_stage_backlog),
        "stage18_go_no_go_blocker_count": len(stage_go_no_go.get("blocker_ids", [])),
        "s18_p3_pending_current_count": 0,
        "delivery_allowed_count": 0,
        "official_report_count": 0,
        "live_connector_count": 0,
        "github_upload_count": 0,
        "business_execution_count": 0,
        "full_kmfa_unit_tests": 268,
    }
    counts = review_manifest.get("review_counts", {})
    for key, expected in expected_counts.items():
        require_equal(f"review_counts.{key}", counts.get(key), expected)

    return {key: int(value) for key, value in expected_counts.items()}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA Stage 18 review evidence.")
    parser.add_argument("--review-manifest", type=Path, default=DEFAULT_REVIEW_MANIFEST)
    parser.add_argument("--stage-go-no-go", type=Path, default=DEFAULT_STAGE_GO_NO_GO)
    args = parser.parse_args(argv)
    try:
        counts = validate_stage_review(args.review_manifest, args.stage_go_no_go)
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(
        "PASS: KMFA Stage 18 review check passed "
        f"(precision_scenarios={counts['precision_scenario_count']}, "
        f"regression_checks={counts['full_regression_check_count']}, "
        f"stage_evidence={counts['stage_acceptance_evidence_count']}, "
        f"connectors={counts['read_only_connector_plan_count']}, "
        f"backlog={counts['next_stage_backlog_count']}, "
        f"decision_blockers={counts['stage18_go_no_go_blocker_count']}, "
        f"github_upload={counts['github_upload_count']}, "
        f"full_tests={counts['full_kmfa_unit_tests']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
