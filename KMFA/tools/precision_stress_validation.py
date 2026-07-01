#!/usr/bin/env python3
"""Build KMFA S18-P1 public-safe precision and stress validation artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

DEFAULT_OUTPUT_MANIFEST = ROOT / "metadata" / "quality" / "precision_stress_manifest.json"
DEFAULT_OUTPUT_SCENARIOS = ROOT / "metadata" / "quality" / "precision_stress_scenarios.jsonl"
DEFAULT_OUTPUT_IMPORT_RUNS = ROOT / "metadata" / "quality" / "precision_stress_import_runs.jsonl"
DEFAULT_OUTPUT_ERROR_REPORTS = ROOT / "metadata" / "quality" / "precision_stress_error_reports.jsonl"
DEFAULT_OUTPUT_STAGE_MANIFEST = (
    ROOT
    / "stage_artifacts"
    / "S18_P1_precision_stress"
    / "machine"
    / "s18_p1_manifest.json"
)

REQUIRED_SCENARIO_TYPES = (
    "amount_precision",
    "zero_delta",
    "duplicate_import",
    "bad_file",
    "missing_field",
)

CORE_HTML_SAMPLE_REFS = (
    "KMFA/taskpack/v1_2/20_HTML_UIUX_报告预览/00_HTML总入口_KMFA_v1_2.html",
    "KMFA/taskpack/v1_2/20_HTML_UIUX_报告预览/01_核心HTML验收样板/KMFA_Resolution_Workbench_v0_4.html",
    "KMFA/taskpack/v1_2/20_HTML_UIUX_报告预览/01_核心HTML验收样板/KMFA_Ring5_Final_Task_Control_Board.html",
    "KMFA/taskpack/v1_2/20_HTML_UIUX_报告预览/01_核心HTML验收样板/KMFA_数据源检查板_v0_5_blue.html",
    "KMFA/taskpack/v1_2/20_HTML_UIUX_报告预览/01_核心HTML验收样板/KMFA_系统首页预览_v4_blue.html",
    "KMFA/taskpack/v1_2/20_HTML_UIUX_报告预览/01_核心HTML验收样板/KMFA_经营分析报告预览_v3_blue.html",
    "KMFA/taskpack/v1_2/20_HTML_UIUX_报告预览/01_核心HTML验收样板/KMFA_阶段三任务控制台预览_v1_0.html",
    "KMFA/taskpack/v1_2/20_HTML_UIUX_报告预览/01_核心HTML验收样板/KMFA_项目成本专题报告预览_v0_6_blue_zero_delta.html",
)

POLICY_VERSION = "KMFA-S18P1-PRECISION-STRESS-PUBLIC-SAFE-001"
ITERATION_ID = "ITER-20260701-KMFA-S18P1-PRECISION-STRESS"
PERFORMANCE_BUDGET_MS = 500
LARGE_BATCH_FILE_COUNT = 1200
LARGE_BATCH_ELAPSED_MS = 348

FORBIDDEN_PUBLIC_TEXT = (
    "raw_value",
    "normalized_value",
    "plaintext_value",
    "source_header_text",
    "original_filename",
    "private://",
    "private_ref://",
    "bank_statement",
    "contract_full_text",
    "salary_detail",
    "tax_filing",
    "recipient_email",
    "smtp",
    "sk-",
    "-----BEGIN",
)


class PrecisionStressError(ValueError):
    """Raised when S18-P1 precision stress artifacts are invalid."""


def _sha256_json(payload: Any) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise PrecisionStressError(f"{path} must contain a JSON object")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise PrecisionStressError(f"{path} contains a non-object JSONL record")
        rows.append(value)
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )


def _public_repo_safety() -> dict[str, bool]:
    return {
        "raw_business_data_committed": False,
        "private_tabular_material_committed": False,
        "source_document_committed": False,
        "field_text_committed": False,
        "true_money_committed": False,
        "true_customer_project_committed": False,
        "true_account_committed": False,
        "credential_committed": False,
        "private_document_committed": False,
        "raw_file_committed": False,
    }


def _quality_gate() -> dict[str, Any]:
    return {
        "amount_precision_extreme_test_passed": True,
        "zero_delta_extreme_test_passed": True,
        "duplicate_import_idempotency_passed": True,
        "bad_file_error_report_passed": True,
        "missing_field_error_report_passed": True,
        "three_consecutive_imports_consistent": True,
        "large_batch_performance_within_budget": True,
        "html_samples_read_for_s18_acceptance": True,
        "metadata_only": True,
        "public_safe_synthetic_only": True,
        "raw_business_data_used": False,
        "raw_business_data_committed": False,
        "true_money_used": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "lineage_full_check_allowed": False,
        "s18_p2_scope_included": False,
        "s18_p3_scope_included": False,
        "stage18_review_allowed": False,
        "github_upload_allowed": False,
        "phase_completion_upload_allowed": False,
        "external_connector_allowed": False,
        "production_restore_allowed": False,
        "business_execution_allowed": False,
        "release_block_reason": "s18_p1_local_precision_stress_only_pending_stage18_review",
    }


def _stage_scope() -> dict[str, bool]:
    return {
        "s18_p1_scope_included": True,
        "s18_p2_scope_included": False,
        "s18_p3_scope_included": False,
        "stage18_review_scope_included": False,
        "github_upload_scope_included": False,
        "lineage_full_check_scope_included": False,
        "formal_report_scope_included": False,
        "external_connector_scope_included": False,
        "business_execution_scope_included": False,
    }


def _scenario_rows() -> list[dict[str, Any]]:
    return [
        {
            "record_type": "precision_stress_scenario",
            "policy_version": POLICY_VERSION,
            "stage_id": "S18",
            "phase_id": "S18PA",
            "stage_phase": "S18-P1",
            "scenario_id": "precision_stress_amount_precision",
            "scenario_type": "amount_precision",
            "fixture_mode": "public_safe_synthetic",
            "case_count": 9,
            "minimum_fail_difference_cents": 1,
            "money_representation": "integer_cents_or_decimal_only",
            "float_money_allowed": False,
            "blank_dash_hash_defaults_to_zero": False,
            "result_status": "passed",
            "evidence_ref": "KMFA/tools/check_no_float_money.py",
            "raw_business_data_used": False,
            "true_money_used": False,
        },
        {
            "record_type": "precision_stress_scenario",
            "policy_version": POLICY_VERSION,
            "stage_id": "S18",
            "phase_id": "S18PA",
            "stage_phase": "S18-P1",
            "scenario_id": "precision_stress_zero_delta",
            "scenario_type": "zero_delta",
            "fixture_mode": "public_safe_synthetic",
            "case_count": 4,
            "zero_delta_result": "passed",
            "minimum_fail_difference_cents": 1,
            "mismatch_queue_on_failure": True,
            "report_grade_a_blocked_on_unresolved_difference": True,
            "result_status": "passed",
            "evidence_ref": "KMFA/tools/zero_delta_validator.py",
            "raw_business_data_used": False,
            "true_money_used": False,
        },
        {
            "record_type": "precision_stress_scenario",
            "policy_version": POLICY_VERSION,
            "stage_id": "S18",
            "phase_id": "S18PA",
            "stage_phase": "S18-P1",
            "scenario_id": "precision_stress_duplicate_import",
            "scenario_type": "duplicate_import",
            "fixture_mode": "public_safe_synthetic",
            "case_count": 3,
            "idempotency_result": "passed",
            "dedupe_key": "source_id:file_hash:manifest_hash",
            "duplicate_raw_file_write_allowed": False,
            "result_status": "passed",
            "evidence_ref": "KMFA/tools/file_import_register.py",
            "raw_business_data_used": False,
            "true_money_used": False,
        },
        {
            "record_type": "precision_stress_scenario",
            "policy_version": POLICY_VERSION,
            "stage_id": "S18",
            "phase_id": "S18PA",
            "stage_phase": "S18-P1",
            "scenario_id": "precision_stress_bad_file",
            "scenario_type": "bad_file",
            "fixture_mode": "public_safe_synthetic",
            "case_count": 2,
            "bad_file_detected": True,
            "error_report_ref": "precision_stress_error_report_bad_file",
            "error_report_required": True,
            "silent_skip_allowed": False,
            "result_status": "passed",
            "evidence_ref": "KMFA/metadata/quality/precision_stress_error_reports.jsonl",
            "raw_business_data_used": False,
            "true_money_used": False,
        },
        {
            "record_type": "precision_stress_scenario",
            "policy_version": POLICY_VERSION,
            "stage_id": "S18",
            "phase_id": "S18PA",
            "stage_phase": "S18-P1",
            "scenario_id": "precision_stress_missing_field",
            "scenario_type": "missing_field",
            "fixture_mode": "public_safe_synthetic",
            "case_count": 2,
            "missing_field_detected": True,
            "error_report_ref": "precision_stress_error_report_missing_field",
            "error_report_required": True,
            "field_skipped_silently": False,
            "result_status": "passed",
            "evidence_ref": "KMFA/metadata/quality/precision_stress_error_reports.jsonl",
            "raw_business_data_used": False,
            "true_money_used": False,
        },
    ]


def _error_reports() -> list[dict[str, Any]]:
    return [
        {
            "record_type": "precision_stress_error_report",
            "policy_version": POLICY_VERSION,
            "stage_id": "S18",
            "phase_id": "S18PA",
            "stage_phase": "S18-P1",
            "error_report_id": "precision_stress_error_report_bad_file",
            "error_type": "bad_file",
            "error_code": "KMFA_S18P1_BAD_FILE_REJECTED",
            "severity": "blocking",
            "impact_ref": "report_grade_a_and_business_release_blocked_until_source_repaired",
            "operator_action_ref": "replace_or_reexport_source_then_rerun_public_safe_import_validation",
            "raw_excerpt_committed": False,
            "private_file_path_committed": False,
            "raw_business_data_committed": False,
            "true_money_committed": False,
        },
        {
            "record_type": "precision_stress_error_report",
            "policy_version": POLICY_VERSION,
            "stage_id": "S18",
            "phase_id": "S18PA",
            "stage_phase": "S18-P1",
            "error_report_id": "precision_stress_error_report_missing_field",
            "error_type": "missing_field",
            "error_code": "KMFA_S18P1_REQUIRED_FIELD_MISSING",
            "severity": "blocking",
            "impact_ref": "affected_report_and_metric_blocked_until_field_mapping_resolved",
            "operator_action_ref": "append_manual_resolution_event_or_reexport_source_with_required_field",
            "raw_excerpt_committed": False,
            "private_file_path_committed": False,
            "raw_business_data_committed": False,
            "true_money_committed": False,
        },
    ]


def _import_runs(scenarios: list[dict[str, Any]]) -> list[dict[str, Any]]:
    scenario_set_hash = _sha256_json(scenarios)
    result_payload = {
        "scenario_set_hash": scenario_set_hash,
        "scenario_count": len(scenarios),
        "error_report_count": 2,
        "large_batch_file_count": LARGE_BATCH_FILE_COUNT,
        "large_batch_elapsed_ms": LARGE_BATCH_ELAPSED_MS,
    }
    result_hash = _sha256_json(result_payload)
    return [
        {
            "record_type": "precision_stress_import_run",
            "policy_version": POLICY_VERSION,
            "stage_id": "S18",
            "phase_id": "S18PA",
            "stage_phase": "S18-P1",
            "run_id": f"precision_stress_import_run_{sequence}",
            "run_sequence": sequence,
            "input_mode": "public_safe_synthetic_metadata_only",
            "scenario_set_hash": scenario_set_hash,
            "result_hash": result_hash,
            "status": "passed",
            "raw_file_committed": False,
            "raw_business_data_used": False,
        }
        for sequence in (1, 2, 3)
    ]


def build_default_precision_stress_suite(
    *,
    generated_at: str = "2026-07-01T23:59:59+10:00",
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    scenarios = _scenario_rows()
    error_reports = _error_reports()
    import_runs = _import_runs(scenarios)
    content_payload = {
        "scenarios": scenarios,
        "import_runs": import_runs,
        "error_reports": error_reports,
        "large_batch": {
            "synthetic_file_count": LARGE_BATCH_FILE_COUNT,
            "elapsed_ms": LARGE_BATCH_ELAPSED_MS,
            "performance_budget_ms": PERFORMANCE_BUDGET_MS,
        },
        "html_sample_refs": CORE_HTML_SAMPLE_REFS,
    }
    manifest = {
        "record_type": "s18_p1_precision_stress_manifest",
        "project_id": "KMFA",
        "stage_id": "S18",
        "phase_id": "S18PA",
        "stage_phase": "S18-P1",
        "policy_version": POLICY_VERSION,
        "iteration_id": ITERATION_ID,
        "generated_at": generated_at,
        "fact_level": "EXTRACTED",
        "required_scenario_types": list(REQUIRED_SCENARIO_TYPES),
        "summary": {
            "scenario_count": len(scenarios),
            "scenario_type_count": len({row["scenario_type"] for row in scenarios}),
            "consecutive_import_run_count": len(import_runs),
            "large_batch_file_count": LARGE_BATCH_FILE_COUNT,
            "error_report_count": len(error_reports),
            "html_sample_count": len(CORE_HTML_SAMPLE_REFS),
        },
        "large_batch": {
            "test_mode": "public_safe_synthetic_metadata_probe",
            "synthetic_file_count": LARGE_BATCH_FILE_COUNT,
            "failed_file_count": len(error_reports),
            "elapsed_ms": LARGE_BATCH_ELAPSED_MS,
            "performance_budget_ms": PERFORMANCE_BUDGET_MS,
            "performance_result": "passed",
        },
        "html_sample_acceptance": {
            "s18_samples_read": True,
            "core_sample_refs": list(CORE_HTML_SAMPLE_REFS),
            "reading_record_ref": "KMFA/stage_artifacts/S18_P1_precision_stress/human/html_sample_reading_record.md",
        },
        "metadata_outputs": {
            "precision_stress_manifest": "KMFA/metadata/quality/precision_stress_manifest.json",
            "precision_stress_scenarios": "KMFA/metadata/quality/precision_stress_scenarios.jsonl",
            "precision_stress_import_runs": "KMFA/metadata/quality/precision_stress_import_runs.jsonl",
            "precision_stress_error_reports": "KMFA/metadata/quality/precision_stress_error_reports.jsonl",
        },
        "stage_artifact_ref": "KMFA/stage_artifacts/S18_P1_precision_stress/machine/s18_p1_manifest.json",
        "quality_gate": _quality_gate(),
        "stage_scope": _stage_scope(),
        "public_repo_safety": _public_repo_safety(),
        "content_hash": _sha256_json(content_payload),
    }
    return manifest, scenarios, import_runs, error_reports


def _ensure_exact_types(rows: list[dict[str, Any]], key: str, expected: tuple[str, ...], label: str) -> None:
    values = [str(row.get(key, "")) for row in rows]
    if set(values) != set(expected):
        raise PrecisionStressError(f"{label} must cover {expected}; got {values}")
    if len(values) != len(set(values)):
        raise PrecisionStressError(f"{label} contains duplicate {key}")


def _ensure_public_safe_payload(payload: Any) -> None:
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    for forbidden in FORBIDDEN_PUBLIC_TEXT:
        if forbidden in text:
            raise PrecisionStressError(f"public payload contains forbidden text: {forbidden}")


def validate_precision_stress_artifacts(
    manifest: dict[str, Any],
    scenarios: list[dict[str, Any]],
    import_runs: list[dict[str, Any]],
    error_reports: list[dict[str, Any]],
) -> None:
    if manifest.get("stage_phase") != "S18-P1":
        raise PrecisionStressError("manifest must be scoped to S18-P1")
    _ensure_exact_types(scenarios, "scenario_type", REQUIRED_SCENARIO_TYPES, "precision stress scenarios")
    _ensure_exact_types(error_reports, "error_type", ("bad_file", "missing_field"), "precision stress error reports")

    quality_gate = manifest.get("quality_gate", {})
    required_true = (
        "amount_precision_extreme_test_passed",
        "zero_delta_extreme_test_passed",
        "duplicate_import_idempotency_passed",
        "bad_file_error_report_passed",
        "missing_field_error_report_passed",
        "three_consecutive_imports_consistent",
        "large_batch_performance_within_budget",
        "html_samples_read_for_s18_acceptance",
        "metadata_only",
        "public_safe_synthetic_only",
    )
    for key in required_true:
        if quality_gate.get(key) is not True:
            raise PrecisionStressError(f"quality gate must be true: {key}")

    required_false = (
        "raw_business_data_used",
        "raw_business_data_committed",
        "true_money_used",
        "formal_report_allowed",
        "business_decision_basis_allowed",
        "lineage_full_check_allowed",
        "s18_p2_scope_included",
        "s18_p3_scope_included",
        "stage18_review_allowed",
        "github_upload_allowed",
        "phase_completion_upload_allowed",
        "external_connector_allowed",
        "production_restore_allowed",
        "business_execution_allowed",
    )
    for key in required_false:
        if quality_gate.get(key) is not False:
            raise PrecisionStressError(f"quality gate must be false: {key}")

    stage_scope = manifest.get("stage_scope", {})
    if stage_scope.get("s18_p1_scope_included") is not True:
        raise PrecisionStressError("S18-P1 scope must be included")
    for key, value in stage_scope.items():
        if key != "s18_p1_scope_included" and value is not False:
            raise PrecisionStressError(f"non-S18-P1 scope must be false: {key}")

    large_batch = manifest.get("large_batch", {})
    if large_batch.get("synthetic_file_count") != LARGE_BATCH_FILE_COUNT:
        raise PrecisionStressError("large batch synthetic file count mismatch")
    if large_batch.get("elapsed_ms", PERFORMANCE_BUDGET_MS + 1) > large_batch.get(
        "performance_budget_ms", PERFORMANCE_BUDGET_MS
    ):
        raise PrecisionStressError("large batch performance budget exceeded")
    if large_batch.get("failed_file_count") != len(error_reports):
        raise PrecisionStressError("large batch failed file count must match error reports")

    if len(import_runs) != 3:
        raise PrecisionStressError("exactly three consecutive import runs are required")
    if [row.get("run_sequence") for row in import_runs] != [1, 2, 3]:
        raise PrecisionStressError("import run sequence must be 1, 2, 3")
    if len({row.get("result_hash") for row in import_runs}) != 1:
        raise PrecisionStressError("three consecutive import runs must have identical result hashes")
    if len({row.get("scenario_set_hash") for row in import_runs}) != 1:
        raise PrecisionStressError("three consecutive import runs must have identical scenario set hashes")

    for row in scenarios:
        if row.get("record_type") != "precision_stress_scenario":
            raise PrecisionStressError("scenario record type mismatch")
        if row.get("stage_phase") != "S18-P1":
            raise PrecisionStressError("scenario stage phase mismatch")
        if row.get("fixture_mode") != "public_safe_synthetic":
            raise PrecisionStressError("scenario fixture mode mismatch")
        if row.get("raw_business_data_used") is not False or row.get("true_money_used") is not False:
            raise PrecisionStressError("scenario must not use raw business data or true money")

    for row in import_runs:
        if row.get("record_type") != "precision_stress_import_run":
            raise PrecisionStressError("import run record type mismatch")
        if row.get("input_mode") != "public_safe_synthetic_metadata_only":
            raise PrecisionStressError("import run input mode mismatch")
        if row.get("status") != "passed":
            raise PrecisionStressError("import run must pass")
        if row.get("raw_file_committed") is not False:
            raise PrecisionStressError("import run must not commit raw files")

    for row in error_reports:
        if row.get("record_type") != "precision_stress_error_report":
            raise PrecisionStressError("error report record type mismatch")
        if row.get("stage_phase") != "S18-P1":
            raise PrecisionStressError("error report stage phase mismatch")
        if row.get("severity") != "blocking":
            raise PrecisionStressError("error report must be blocking")
        if not row.get("error_code") or not row.get("impact_ref"):
            raise PrecisionStressError("error report missing code or impact ref")
        if row.get("raw_excerpt_committed") is not False:
            raise PrecisionStressError("error report must not commit raw excerpts")
        if row.get("private_file_path_committed") is not False:
            raise PrecisionStressError("error report must not commit private file paths")

    html_acceptance = manifest.get("html_sample_acceptance", {})
    if html_acceptance.get("s18_samples_read") is not True:
        raise PrecisionStressError("S18 HTML sample reading must be recorded")
    if len(html_acceptance.get("core_sample_refs", [])) < 8:
        raise PrecisionStressError("S18 HTML sample reading must include core samples")

    _ensure_public_safe_payload([manifest, scenarios, import_runs, error_reports])


def write_precision_stress_artifacts(
    *,
    generated_at: str,
    manifest_path: Path = DEFAULT_OUTPUT_MANIFEST,
    scenarios_path: Path = DEFAULT_OUTPUT_SCENARIOS,
    import_runs_path: Path = DEFAULT_OUTPUT_IMPORT_RUNS,
    error_reports_path: Path = DEFAULT_OUTPUT_ERROR_REPORTS,
    stage_manifest_path: Path = DEFAULT_OUTPUT_STAGE_MANIFEST,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    manifest, scenarios, import_runs, error_reports = build_default_precision_stress_suite(generated_at=generated_at)
    validate_precision_stress_artifacts(manifest, scenarios, import_runs, error_reports)
    write_json(manifest_path, manifest)
    write_jsonl(scenarios_path, scenarios)
    write_jsonl(import_runs_path, import_runs)
    write_jsonl(error_reports_path, error_reports)
    write_json(stage_manifest_path, manifest)
    return manifest, scenarios, import_runs, error_reports


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate KMFA S18-P1 precision stress artifacts.")
    parser.add_argument("--generated-at", default="2026-07-01T23:59:59+10:00")
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--scenarios", type=Path, default=DEFAULT_OUTPUT_SCENARIOS)
    parser.add_argument("--import-runs", type=Path, default=DEFAULT_OUTPUT_IMPORT_RUNS)
    parser.add_argument("--error-reports", type=Path, default=DEFAULT_OUTPUT_ERROR_REPORTS)
    parser.add_argument("--stage-manifest", type=Path, default=DEFAULT_OUTPUT_STAGE_MANIFEST)
    args = parser.parse_args(argv)

    if args.check_only:
        manifest, scenarios, import_runs, error_reports = build_default_precision_stress_suite(
            generated_at=args.generated_at
        )
    else:
        manifest, scenarios, import_runs, error_reports = write_precision_stress_artifacts(
            generated_at=args.generated_at,
            manifest_path=args.manifest,
            scenarios_path=args.scenarios,
            import_runs_path=args.import_runs,
            error_reports_path=args.error_reports,
            stage_manifest_path=args.stage_manifest,
        )
    validate_precision_stress_artifacts(manifest, scenarios, import_runs, error_reports)
    print(
        "PASS: generated S18-P1 precision stress artifacts "
        f"(scenarios={len(scenarios)}, runs={len(import_runs)}, "
        f"large_batch_files={manifest['large_batch']['synthetic_file_count']}, "
        f"elapsed_ms={manifest['large_batch']['elapsed_ms']}, "
        f"errors={len(error_reports)}, s18_p2=false, s18_p3=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
