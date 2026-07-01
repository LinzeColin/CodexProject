#!/usr/bin/env python3
"""Validate KMFA post-S18 Part 2 review evidence for Stages 4-6."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


DEFAULT_MANIFEST = Path("KMFA/stage_artifacts/PART2_STAGES_04_06_REVIEW/machine/part2_review_manifest.json")

REQUIRED_STAGE_ARTIFACTS = (
    "KMFA/stage_artifacts/S04_P1_amount_tools/human/s04_p1_completion_record.md",
    "KMFA/stage_artifacts/S04_P1_amount_tools/human/test_results.md",
    "KMFA/stage_artifacts/S04_P1_amount_tools/machine/s04_p1_manifest.json",
    "KMFA/stage_artifacts/S04_P2_field_standardization/human/s04_p2_completion_record.md",
    "KMFA/stage_artifacts/S04_P2_field_standardization/human/test_results.md",
    "KMFA/stage_artifacts/S04_P2_field_standardization/machine/s04_p2_manifest.json",
    "KMFA/stage_artifacts/S04_P3_basic_tool_tests/human/s04_p3_completion_record.md",
    "KMFA/stage_artifacts/S04_P3_basic_tool_tests/human/test_results.md",
    "KMFA/stage_artifacts/S04_P3_basic_tool_tests/human/tool_function_test_report.md",
    "KMFA/stage_artifacts/S04_P3_basic_tool_tests/machine/s04_p3_manifest.json",
    "KMFA/stage_artifacts/S04_STAGE_REVIEW/human/stage4_review_report.md",
    "KMFA/stage_artifacts/S04_STAGE_REVIEW/human/test_results.md",
    "KMFA/stage_artifacts/S04_STAGE_REVIEW/human/github_upload_record.md",
    "KMFA/stage_artifacts/S04_STAGE_REVIEW/machine/stage4_review_manifest.json",
    "KMFA/stage_artifacts/S04_STAGE_REVIEW/machine/stage4_upload_manifest.json",
    "KMFA/stage_artifacts/S05_P1_a0_file_registration/human/s05_p1_completion_record.md",
    "KMFA/stage_artifacts/S05_P1_a0_file_registration/human/test_results.md",
    "KMFA/stage_artifacts/S05_P1_a0_file_registration/machine/s05_p1_manifest.json",
    "KMFA/stage_artifacts/S05_P2_a0_golden_fixture/human/s05_p2_completion_record.md",
    "KMFA/stage_artifacts/S05_P2_a0_golden_fixture/human/test_results.md",
    "KMFA/stage_artifacts/S05_P2_a0_golden_fixture/human/owner_decision_record.md",
    "KMFA/stage_artifacts/S05_P2_a0_golden_fixture/machine/s05_p2_manifest.json",
    "KMFA/stage_artifacts/S05_P2_a0_golden_fixture/machine/excel_owner_decision_intake_contract.json",
    "KMFA/stage_artifacts/S05_P2_a0_golden_fixture/machine/owner_decision_records/excel_owner_resolution_decision.json",
    "KMFA/stage_artifacts/S05_P2_a0_golden_fixture/machine/owner_decision_records/excel_owner_decision_application_preview.json",
    "KMFA/stage_artifacts/S05_P3_authority_baseline_lock/human/s05_p3_completion_record.md",
    "KMFA/stage_artifacts/S05_P3_authority_baseline_lock/human/test_results.md",
    "KMFA/stage_artifacts/S05_P3_authority_baseline_lock/machine/s05_p3_manifest.json",
    "KMFA/stage_artifacts/S05_STAGE_REVIEW/human/stage5_review_report.md",
    "KMFA/stage_artifacts/S05_STAGE_REVIEW/human/test_results.md",
    "KMFA/stage_artifacts/S05_STAGE_REVIEW/human/github_upload_record.md",
    "KMFA/stage_artifacts/S05_STAGE_REVIEW/machine/stage5_review_manifest.json",
    "KMFA/stage_artifacts/S05_STAGE_REVIEW/machine/stage5_upload_manifest.json",
    "KMFA/stage_artifacts/S06_P1_zero_delta_validator/human/s06_p1_completion_record.md",
    "KMFA/stage_artifacts/S06_P1_zero_delta_validator/human/test_results.md",
    "KMFA/stage_artifacts/S06_P1_zero_delta_validator/machine/s06_p1_manifest.json",
    "KMFA/stage_artifacts/S06_P1_zero_delta_validator/machine/s06_p1_synthetic_zero_delta_result.json",
    "KMFA/stage_artifacts/S06_P1_zero_delta_validator/machine/s06_p1_synthetic_mismatch_report.csv",
    "KMFA/stage_artifacts/S06_P2_cross_source_difference_queue/human/s06_p2_completion_record.md",
    "KMFA/stage_artifacts/S06_P2_cross_source_difference_queue/human/test_results.md",
    "KMFA/stage_artifacts/S06_P2_cross_source_difference_queue/machine/s06_p2_manifest.json",
    "KMFA/stage_artifacts/S06_P2_cross_source_difference_queue/machine/s06_p2_report_grade_gate.json",
    "KMFA/stage_artifacts/S06_P2_cross_source_difference_queue/machine/s06_p2_synthetic_difference_queue.jsonl",
    "KMFA/stage_artifacts/S06_P3_validation_evidence_output/human/s06_p3_completion_record.md",
    "KMFA/stage_artifacts/S06_P3_validation_evidence_output/human/test_results.md",
    "KMFA/stage_artifacts/S06_P3_validation_evidence_output/machine/s06_p3_manifest.json",
    "KMFA/stage_artifacts/S06_P3_validation_evidence_output/machine/zero_delta_result.json",
    "KMFA/stage_artifacts/S06_P3_validation_evidence_output/machine/mismatch_report.csv",
    "KMFA/stage_artifacts/S06_P3_validation_evidence_output/machine/project_validation_status.jsonl",
    "KMFA/stage_artifacts/S06_STAGE_REVIEW/human/stage6_review_report.md",
    "KMFA/stage_artifacts/S06_STAGE_REVIEW/human/test_results.md",
    "KMFA/stage_artifacts/S06_STAGE_REVIEW/human/github_upload_record.md",
    "KMFA/stage_artifacts/S06_STAGE_REVIEW/machine/stage6_review_manifest.json",
    "KMFA/stage_artifacts/S06_STAGE_REVIEW/machine/stage6_upload_manifest.json",
)

REQUIRED_BASELINE_REFS = (
    "KMFA/taskpack/v1_2/01_KMFA_Codex_TaskPack_v1_2_完整防遗漏_含HTML验收样板.md",
    "KMFA/taskpack/v1_2/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_2.md",
    "KMFA/tools/amount_tools.py",
    "KMFA/tools/check_no_float_money.py",
    "KMFA/tools/field_standardization.py",
    "KMFA/tools/generate_tool_test_report.py",
    "KMFA/tools/a0_file_register.py",
    "KMFA/tools/check_a0_file_registration.py",
    "KMFA/tools/a0_golden_fixture.py",
    "KMFA/tools/check_a0_golden_fixture.py",
    "KMFA/tools/check_s05_p2_completion_gate.py",
    "KMFA/tools/check_a0_authority_baseline_lock.py",
    "KMFA/tools/zero_delta_validator.py",
    "KMFA/tools/cross_source_difference_queue.py",
    "KMFA/tools/check_s06_p2_difference_queue.py",
    "KMFA/tools/validation_evidence_output.py",
    "KMFA/tools/check_s06_p3_validation_evidence.py",
    "KMFA/tests/test_amount_tools.py",
    "KMFA/tests/test_field_standardization.py",
    "KMFA/tests/test_basic_tool_boundaries.py",
    "KMFA/tests/test_a0_file_register.py",
    "KMFA/tests/test_a0_golden_fixture.py",
    "KMFA/tests/test_s05_p3_authority_baseline_lock.py",
    "KMFA/tests/test_zero_delta_validator.py",
    "KMFA/tests/test_cross_source_difference_queue.py",
    "KMFA/tests/test_validation_evidence_output.py",
    "KMFA/metadata/baseline/a0_authority_baseline_manifest.json",
    "KMFA/metadata/quality/zero_delta_results.jsonl",
    "KMFA/metadata/quality/source_difference_queue.jsonl",
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


def validate_part2_review(manifest_path: Path = DEFAULT_MANIFEST) -> dict[str, int]:
    manifest = _read_json(manifest_path)

    _require_equal("schema_version", manifest.get("schema_version"), "kmfa.part_review_manifest.v1")
    _require_equal("project_id", manifest.get("project_id"), "KMFA")
    _require_equal("part_id", manifest.get("part_id"), "PART2_STAGES_04_06")
    _require_equal("review_id", manifest.get("review_id"), "KMFA-PART2-STAGES-04-06-REVIEW-20260702")
    _require_equal("status", manifest.get("status"), "part_review_passed_local_only")
    _require_equal("stages", manifest.get("stages"), ["S04", "S05", "S06"])
    _require_equal("next_part_id", manifest.get("next_part_id"), "PART3_STAGES_07_09")
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
    _require_equal("review_counts.part2_unit_tests", counts.get("part2_unit_tests"), 59)
    _require_equal("review_counts.full_kmfa_unit_tests", counts.get("full_kmfa_unit_tests"), 270)
    _require_equal("review_counts.s04_tool_boundary_cases", counts.get("s04_tool_boundary_cases"), 22)
    _require_equal("review_counts.s05_q5_locked_fields", counts.get("s05_q5_locked_fields"), 40)
    _require_equal("review_counts.s05_excluded_fields", counts.get("s05_excluded_fields"), 5)
    _require_equal("review_counts.s06_difference_queue_items", counts.get("s06_difference_queue_items"), 1)
    _require_equal("review_counts.s06_project_validation_statuses", counts.get("s06_project_validation_statuses"), 2)

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
        _fail("missing required Part 2 paths: " + ", ".join(missing))

    s04p1 = _read_json(Path("KMFA/stage_artifacts/S04_P1_amount_tools/machine/s04_p1_manifest.json"))
    s04p2 = _read_json(Path("KMFA/stage_artifacts/S04_P2_field_standardization/machine/s04_p2_manifest.json"))
    s04p3 = _read_json(Path("KMFA/stage_artifacts/S04_P3_basic_tool_tests/machine/s04_p3_manifest.json"))
    s04_review = _read_json(Path("KMFA/stage_artifacts/S04_STAGE_REVIEW/machine/stage4_review_manifest.json"))
    s05_review = _read_json(Path("KMFA/stage_artifacts/S05_STAGE_REVIEW/machine/stage5_review_manifest.json"))
    s05_lock = _read_json(Path("KMFA/stage_artifacts/S05_P3_authority_baseline_lock/machine/s05_p3_manifest.json"))
    s06_review = _read_json(Path("KMFA/stage_artifacts/S06_STAGE_REVIEW/machine/stage6_review_manifest.json"))
    s06_p2_gate = _read_json(Path("KMFA/stage_artifacts/S06_P2_cross_source_difference_queue/machine/s06_p2_report_grade_gate.json"))
    s06_p3 = _read_json(Path("KMFA/stage_artifacts/S06_P3_validation_evidence_output/machine/s06_p3_manifest.json"))
    project_statuses = _read_jsonl(Path("KMFA/stage_artifacts/S06_P3_validation_evidence_output/machine/project_validation_status.jsonl"))

    _require_equal("s04p1.stage", s04p1.get("stage"), "S04")
    _require_equal("s04p1.phase", s04p1.get("phase"), "S04-P1")
    _require_equal("s04p1.status", s04p1.get("status"), "completed_validated_local_only")
    _require_false("s04p1.private_or_raw_business_data_committed", s04p1.get("private_or_raw_business_data_committed"))
    _require_equal("s04p2.phase", s04p2.get("phase"), "S04-P2")
    _require_false("s04p2.github_upload_allowed", s04p2.get("github_upload_allowed"))
    _require_equal("s04p3.phase", s04p3.get("phase"), "S04-P3")
    _require_equal("s04p3.validation_summary.tool_boundary_cases_passed", s04p3.get("validation_summary", {}).get("tool_boundary_cases_passed"), 22)
    _require_false("s04p3.validation_summary.raw_business_data_used", s04p3.get("validation_summary", {}).get("raw_business_data_used"))
    _require_equal("s04_review.stage", s04_review.get("stage"), "S04")
    _require_equal("s04_review.status", s04_review.get("status"), "pass_upload_ready_local_only")
    _require_false("s04_review.raw_business_data_used", s04_review.get("raw_business_data_used"))

    _require_equal("s05_review.stage", s05_review.get("stage"), "S05")
    _require_equal("s05_review.status", s05_review.get("status"), "pass_upload_ready_local_only")
    _require_false("s05_review.raw_business_data_used", s05_review.get("raw_business_data_used"))
    _require_true("s05_review.upload_performed", s05_review.get("upload_performed"))
    _require_equal("s05_review.review_counts.q5_locked_fields", s05_review.get("review_counts", {}).get("q5_locked_fields"), 40)
    _require_equal("s05_review.review_counts.excluded_fields", s05_review.get("review_counts", {}).get("excluded_fields"), 5)
    _require_equal("s05_lock.q5_locked_field_count", s05_lock.get("q5_locked_field_count"), 40)
    _require_equal("s05_lock.excluded_field_count", s05_lock.get("excluded_field_count"), 5)
    _require_false("s05_lock.formal_report_allowed", s05_lock.get("formal_report_allowed"))
    _require_false("s05_lock.raw_business_values_committed", s05_lock.get("raw_business_values_committed"))
    _require_false("s05_lock.private_csv_committed", s05_lock.get("private_csv_committed"))

    _require_equal("s06_review.stage", s06_review.get("stage"), "S06")
    _require_equal("s06_review.status", s06_review.get("status"), "pass_upload_ready_local_only")
    _require_false("s06_review.raw_business_data_used", s06_review.get("raw_business_data_used"))
    _require_equal("s06_review.review_counts.zero_delta_mismatches", s06_review.get("review_counts", {}).get("zero_delta_mismatches"), 1)
    _require_equal("s06_review.review_counts.difference_queue_items", s06_review.get("review_counts", {}).get("difference_queue_items"), 1)
    _require_false("s06_p2_gate.report_grade_a_allowed", s06_p2_gate.get("report_grade_a_allowed"))
    _require_equal("s06_p3.project_validation_statuses", s06_p3.get("project_validation_statuses"), 2)
    _require_false("s06_p3.formal_report_allowed", s06_p3.get("formal_report_allowed"))
    _require_false("s06_p3.zero_delta_passed", s06_p3.get("zero_delta_passed"))
    _require_equal("s06_project_validation_status_count", len(project_statuses), 2)

    return {
        "stage_count": counts["stage_count"],
        "phase_count": counts["phase_count"],
        "required_stage_artifact_count": counts["required_stage_artifact_count"],
        "required_baseline_ref_count": counts["required_baseline_ref_count"],
        "part2_unit_tests": counts["part2_unit_tests"],
        "full_kmfa_unit_tests": counts["full_kmfa_unit_tests"],
        "open_review_finding_count": manifest["open_review_finding_count"],
        "github_upload_count": 1 if manifest["github_upload_performed"] else 0,
    }


def main() -> int:
    try:
        counts = validate_part2_review()
    except Exception as exc:  # pragma: no cover - CLI boundary
        print(f"FAIL: KMFA Part 2 Stage 4-6 review check failed: {exc}", file=sys.stderr)
        return 1
    print(
        "PASS: KMFA Part 2 Stage 4-6 review check passed "
        f"(stages={counts['stage_count']}, phases={counts['phase_count']}, "
        f"stage_artifacts={counts['required_stage_artifact_count']}, "
        f"baseline_refs={counts['required_baseline_ref_count']}, "
        f"part2_tests={counts['part2_unit_tests']}, "
        f"full_tests={counts['full_kmfa_unit_tests']}, "
        f"github_upload={counts['github_upload_count']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
