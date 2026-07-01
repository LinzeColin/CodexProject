#!/usr/bin/env python3
"""Validate KMFA Stage 15 review evidence and gates."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


DEFAULT_REVIEW_MANIFEST = Path("KMFA/stage_artifacts/S15_STAGE_REVIEW/machine/stage15_review_manifest.json")
DEFAULT_P1_MANIFEST = Path("KMFA/stage_artifacts/S15_P1_performance_fact_fields/machine/s15_p1_manifest.json")
DEFAULT_P2_MANIFEST = Path("KMFA/stage_artifacts/S15_P2_performance_review_list/machine/s15_p2_manifest.json")
DEFAULT_P3_MANIFEST = Path("KMFA/stage_artifacts/S15_P3_salary_boundary/machine/s15_p3_manifest.json")

DEFAULT_FIELD_DEFINITIONS = Path("KMFA/metadata/reports/performance_fact_field_definitions.jsonl")
DEFAULT_FIELD_BINDINGS = Path("KMFA/metadata/reports/performance_fact_field_bindings.jsonl")
DEFAULT_MANUAL_REVIEW_FIELDS = Path("KMFA/metadata/reports/performance_fact_manual_review_fields.jsonl")
DEFAULT_FACT_TABLE = Path("KMFA/metadata/reports/performance_fact_table.jsonl")
DEFAULT_REVIEW_ITEMS = Path("KMFA/metadata/reports/performance_review_items.jsonl")
DEFAULT_INTERFACE_CONTRACT = Path("KMFA/metadata/reports/performance_fact_output_interface_contract.json")
DEFAULT_READINESS_DRAFT = Path("KMFA/metadata/reports/salary_system_readiness_draft.jsonl")


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
    field_definitions_path: Path = DEFAULT_FIELD_DEFINITIONS,
    field_bindings_path: Path = DEFAULT_FIELD_BINDINGS,
    manual_review_fields_path: Path = DEFAULT_MANUAL_REVIEW_FIELDS,
    fact_table_path: Path = DEFAULT_FACT_TABLE,
    review_items_path: Path = DEFAULT_REVIEW_ITEMS,
    interface_contract_path: Path = DEFAULT_INTERFACE_CONTRACT,
    readiness_draft_path: Path = DEFAULT_READINESS_DRAFT,
) -> dict[str, int]:
    required_paths = [
        review_manifest_path,
        p1_manifest_path,
        p2_manifest_path,
        p3_manifest_path,
        field_definitions_path,
        field_bindings_path,
        manual_review_fields_path,
        fact_table_path,
        review_items_path,
        interface_contract_path,
        readiness_draft_path,
        Path("KMFA/stage_artifacts/S15_STAGE_REVIEW/human/stage15_review_report.md"),
        Path("KMFA/stage_artifacts/S15_STAGE_REVIEW/human/test_results.md"),
    ]
    missing = [str(path) for path in required_paths if not path.exists()]
    if missing:
        fail("missing required evidence paths: " + ", ".join(missing))

    forbidden_upload_paths = [
        Path("KMFA/stage_artifacts/S15_STAGE_REVIEW/human/github_upload_record.md"),
        Path("KMFA/stage_artifacts/S15_STAGE_REVIEW/machine/stage15_upload_manifest.json"),
    ]
    unexpected = [str(path) for path in forbidden_upload_paths if path.exists()]
    if unexpected:
        fail("Stage 15 review must not contain upload evidence: " + ", ".join(unexpected))

    review_manifest = read_json(review_manifest_path)
    p1_manifest = read_json(p1_manifest_path)
    p2_manifest = read_json(p2_manifest_path)
    p3_manifest = read_json(p3_manifest_path)
    field_definitions = read_jsonl(field_definitions_path)
    field_bindings = read_jsonl(field_bindings_path)
    manual_review_fields = read_jsonl(manual_review_fields_path)
    fact_rows = read_jsonl(fact_table_path)
    review_items = read_jsonl(review_items_path)
    interface_contract = read_json(interface_contract_path)
    readiness_rows = read_jsonl(readiness_draft_path)

    require_equal("stage", review_manifest.get("stage"), "S15")
    require_equal("status", review_manifest.get("status"), "review_passed_upload_ready_local_only")
    require_equal("github_upload_status", review_manifest.get("github_upload_status"), "not_pushed")
    require_true("upload_allowed_after_review", review_manifest.get("upload_allowed_after_review"))
    require_false("github_upload_performed", review_manifest.get("github_upload_performed"))
    require_false("s16_allowed", review_manifest.get("s16_allowed"))
    require_false("lineage_full_check_performed", review_manifest.get("lineage_full_check_performed"))
    require_false("formal_report_generated", review_manifest.get("formal_report_generated"))
    require_false("external_connector_included", review_manifest.get("external_connector_included"))
    require_false("business_decision_basis_allowed", review_manifest.get("business_decision_basis_allowed"))
    require_false("salary_calculation_allowed", review_manifest.get("salary_calculation_allowed"))
    require_false("bonus_approval_allowed", review_manifest.get("bonus_approval_allowed"))
    require_false("payroll_export_allowed", review_manifest.get("payroll_export_allowed"))
    require_false("final_compensation_decision_allowed", review_manifest.get("final_compensation_decision_allowed"))
    require_equal("report_grade_visible", review_manifest.get("report_grade_visible"), "D")
    require_equal("pending_reconciliation_count", review_manifest.get("pending_reconciliation_count"), 12)
    require_equal("next_gate_id", review_manifest.get("next_gate_id"), "KMFA-S15-GITHUB-UPLOAD-GATE")
    require_equal("open_review_finding_count", review_manifest.get("open_review_finding_count"), 0)
    require_public_safety("review", review_manifest)

    for phase in ("S15-P1", "S15-P2", "S15-P3"):
        require_phase_status(review_manifest.get("stage_phase_status"), phase)
    require_existing_refs(review_manifest.get("evidence_refs"))

    require_equal("p1.stage_phase", p1_manifest.get("stage_phase"), "S15-P1")
    require_equal("p1.status", p1_manifest.get("status"), "completed_validated_local_only")
    require_equal("p1.summary.field_definition_count", p1_manifest.get("summary", {}).get("field_definition_count"), 6)
    require_equal("p1.summary.field_binding_count", p1_manifest.get("summary", {}).get("field_binding_count"), 6)
    require_equal("p1.summary.manual_review_field_count", p1_manifest.get("summary", {}).get("manual_review_field_count"), 4)
    require_false_flags(
        "p1.quality_gate",
        p1_manifest.get("quality_gate", {}),
        (
            "performance_fact_table_output_allowed",
            "salary_calculation_allowed",
            "bonus_approval_allowed",
            "payroll_export_allowed",
            "formal_report_allowed",
            "business_decision_basis_allowed",
            "s15_p2_allowed",
            "s15_p3_allowed",
            "stage15_review_allowed",
            "github_upload_allowed",
        ),
    )
    require_public_safety("p1", p1_manifest)

    require_equal("p2.stage_phase", p2_manifest.get("stage_phase"), "S15-P2")
    require_equal("p2.status", p2_manifest.get("status"), "completed_validated_local_only")
    require_equal("p2.summary.performance_fact_row_count", p2_manifest.get("summary", {}).get("performance_fact_row_count"), 4)
    require_equal("p2.summary.abnormal_review_item_count", p2_manifest.get("summary", {}).get("abnormal_review_item_count"), 16)
    require_equal("p2.summary.manual_review_field_count", p2_manifest.get("summary", {}).get("manual_review_field_count"), 4)
    require_false_flags(
        "p2.quality_gate",
        p2_manifest.get("quality_gate", {}),
        (
            "salary_calculation_allowed",
            "bonus_approval_allowed",
            "payroll_export_allowed",
            "final_compensation_decision_allowed",
            "formal_report_allowed",
            "business_decision_basis_allowed",
            "s15_p3_allowed",
            "stage15_review_allowed",
            "github_upload_allowed",
        ),
    )
    require_public_safety("p2", p2_manifest)

    require_equal("p3.stage_phase", p3_manifest.get("stage_phase"), "S15-P3")
    require_equal("p3.status", p3_manifest.get("status"), "completed_validated_local_only")
    require_equal("p3.summary.fact_interface_contract_count", p3_manifest.get("summary", {}).get("fact_interface_contract_count"), 1)
    require_equal("p3.summary.future_salary_system_readiness_row_count", p3_manifest.get("summary", {}).get("future_salary_system_readiness_row_count"), 4)
    require_equal("p3.summary.human_approval_boundary_count", p3_manifest.get("summary", {}).get("human_approval_boundary_count"), 4)
    require_true("p3.quality_gate.fact_output_interface_reserved", p3_manifest.get("quality_gate", {}).get("fact_output_interface_reserved"))
    require_true("p3.quality_gate.future_salary_system_read_draft_allowed", p3_manifest.get("quality_gate", {}).get("future_salary_system_read_draft_allowed"))
    require_true("p3.quality_gate.final_approval_must_be_human", p3_manifest.get("quality_gate", {}).get("final_approval_must_be_human"))
    require_true("p3.quality_gate.payment_release_must_be_human", p3_manifest.get("quality_gate", {}).get("payment_release_must_be_human"))
    require_false_flags(
        "p3.quality_gate",
        p3_manifest.get("quality_gate", {}),
        (
            "live_salary_system_integration_allowed",
            "api_endpoint_allowed",
            "connector_allowed",
            "file_export_allowed",
            "external_system_write_allowed",
            "salary_calculation_allowed",
            "wage_calculation_allowed",
            "bonus_approval_allowed",
            "payroll_export_allowed",
            "final_compensation_decision_allowed",
            "payment_execution_allowed",
            "formal_report_allowed",
            "business_decision_basis_allowed",
            "stage15_review_allowed",
            "github_upload_allowed",
        ),
    )
    require_public_safety("p3", p3_manifest)

    require_equal("field_definitions.count", len(field_definitions), 6)
    require_equal("field_bindings.count", len(field_bindings), 6)
    require_equal("manual_review_fields.count", len(manual_review_fields), 4)
    require_equal("fact_rows.count", len(fact_rows), 4)
    require_equal("review_items.count", len(review_items), 16)
    require_equal("interface_contract.record_type", interface_contract.get("record_type"), "performance_fact_output_interface_contract")
    require_equal("readiness_rows.count", len(readiness_rows), 4)

    counts = review_manifest.get("review_counts", {})
    require_equal("review_counts.field_definition_count", counts.get("field_definition_count"), len(field_definitions))
    require_equal("review_counts.field_binding_count", counts.get("field_binding_count"), len(field_bindings))
    require_equal("review_counts.manual_review_field_count", counts.get("manual_review_field_count"), len(manual_review_fields))
    require_equal("review_counts.performance_fact_row_count", counts.get("performance_fact_row_count"), len(fact_rows))
    require_equal("review_counts.abnormal_review_item_count", counts.get("abnormal_review_item_count"), len(review_items))
    require_equal("review_counts.fact_interface_contract_count", counts.get("fact_interface_contract_count"), 1)
    require_equal("review_counts.future_salary_system_readiness_row_count", counts.get("future_salary_system_readiness_row_count"), len(readiness_rows))
    require_equal("review_counts.pending_review_item_count", counts.get("pending_review_item_count"), 16)
    require_equal("review_counts.salary_calculation_count", counts.get("salary_calculation_count"), 0)
    require_equal("review_counts.bonus_approval_count", counts.get("bonus_approval_count"), 0)
    require_equal("review_counts.payroll_export_count", counts.get("payroll_export_count"), 0)
    require_equal("review_counts.final_compensation_decision_count", counts.get("final_compensation_decision_count"), 0)
    require_equal("review_counts.full_kmfa_unit_tests", counts.get("full_kmfa_unit_tests"), 207)

    boundaries = review_manifest.get("scope_boundary", {})
    require_true("scope_boundary.stage15_review_scope_included", boundaries.get("stage15_review_scope_included"))
    require_false("scope_boundary.github_upload_scope_included", boundaries.get("github_upload_scope_included"))
    require_false("scope_boundary.s16_scope_included", boundaries.get("s16_scope_included"))
    require_false("scope_boundary.lineage_full_check_scope_included", boundaries.get("lineage_full_check_scope_included"))
    require_false("scope_boundary.formal_report_runtime_scope_included", boundaries.get("formal_report_runtime_scope_included"))
    require_false("scope_boundary.salary_calculation_scope_included", boundaries.get("salary_calculation_scope_included"))
    require_false("scope_boundary.payroll_export_scope_included", boundaries.get("payroll_export_scope_included"))
    require_false("scope_boundary.external_connector_scope_included", boundaries.get("external_connector_scope_included"))

    return dict(counts)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA Stage 15 review evidence and gates.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_REVIEW_MANIFEST)
    args = parser.parse_args(argv)

    try:
        counts = validate_stage_review(args.manifest)
    except Exception as exc:
        print(f"FAIL: KMFA Stage 15 review check failed: {exc}", file=sys.stderr)
        return 1

    print(
        "PASS: KMFA Stage 15 review check passed "
        f"(fields={counts['field_definition_count']}, "
        f"bindings={counts['field_binding_count']}, "
        f"fact_rows={counts['performance_fact_row_count']}, "
        f"review_items={counts['abnormal_review_item_count']}, "
        f"interface_contracts={counts['fact_interface_contract_count']}, "
        f"readiness_rows={counts['future_salary_system_readiness_row_count']}, "
        "salary_calculation=false, bonus_approval=false, payroll_export=false, "
        "final_compensation=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
