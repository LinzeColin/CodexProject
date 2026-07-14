#!/usr/bin/env python3
"""Generate KMFA v0.1.4 S18-P1 precision and stress evidence.

This phase replays the public-safe synthetic precision stress baseline and
locks the v0.1.4 Stage 18 P1 boundary. It does not read raw/private inbox
content, perform S18-P2 full regression, prepare S18-P3 integrations, run
Stage 18 review, upload to GitHub, release formal reports, restore production,
call external services, reinstall an app, or execute business actions.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.check_v014_s17_stage_review import validate_v014_s17_stage_review  # noqa: E402
from KMFA.tools.precision_stress_validation import (  # noqa: E402
    POLICY_VERSION as LEGACY_S18_P1_POLICY_VERSION,
    REQUIRED_SCENARIO_TYPES,
    build_default_precision_stress_suite,
    validate_precision_stress_artifacts,
)


TASK_ID = "KMFA-V014-S18-P1-PRECISION-STRESS-20260705"
ACCEPTANCE_ID = "ACC-V014-S18-P1-PRECISION-STRESS"
SCHEMA_VERSION = "kmfa.v014_s18_p1_precision_stress.v1"
PHASE_SCOPE = "v014_s18_p1_precision_stress_only"
POLICY_LOCK_VERSION = "LOCK-KMFA-V014-S18P1-PRECISION-STRESS-PUBLIC-SAFE-001"
FORMULA_ID = "FORM-KMFA-V014-S18P1-PRECISION-STRESS-001"
MAPPING_VERSION = "MAP-KMFA-V014-S18P1-PRECISION-STRESS-v1"
REQUIRED_V014_SCENARIO_TYPES = REQUIRED_SCENARIO_TYPES

OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_S18_P1_PRECISION_STRESS")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
METADATA_DIR = Path("KMFA/metadata/quality")

MANIFEST_PATH = MACHINE_DIR / "precision_stress_manifest.json"
SCENARIO_LOCK_PATH = MACHINE_DIR / "precision_stress_scenario_lock.jsonl"
IMPORT_RUN_LOCK_PATH = MACHINE_DIR / "import_consistency_run_lock.jsonl"
ERROR_REPORT_LOCK_PATH = MACHINE_DIR / "precision_stress_error_report_lock.jsonl"
METADATA_MANIFEST_PATH = METADATA_DIR / "v014_s18_p1_precision_stress_manifest.json"
METADATA_SCENARIOS_PATH = METADATA_DIR / "v014_s18_p1_precision_stress_scenarios.jsonl"
METADATA_IMPORT_RUNS_PATH = METADATA_DIR / "v014_s18_p1_import_consistency_runs.jsonl"
METADATA_ERROR_REPORTS_PATH = METADATA_DIR / "v014_s18_p1_precision_stress_error_reports.jsonl"

REPORT_PATH = HUMAN_DIR / "precision_stress_report.md"
HTML_READING_RECORD_PATH = HUMAN_DIR / "html_baseline_reading_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

V14_TASKPACK_PATH = Path("KMFA/taskpack/v1_4/taskpack/01_KMFA_Codex_TaskPack_v1_4_public_safe.md")
V14_ROADMAP_PATH = Path("KMFA/taskpack/v1_4/roadmap/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_4.md")
V14_HTML_BASELINE_REFS = (
    "KMFA/taskpack/v1_4/html_uiux/00_KMFA_HTML_human_flow_entry_v1_4.html",
    "KMFA/taskpack/v1_4/html_uiux/KMFA_HTML_human_flow_audit_report_v1_4.md",
    "KMFA/taskpack/v1_4/html_uiux/kmfa_html_human_flow_audit.py",
)
RAW_INBOX_REF = "operator-designated raw/private inbox outside repository"
NEXT_PHASE = "S18-P2"
NEXT_REQUIRED_STEP = (
    "Proceed to v0.1.4 S18-P2 full regression and acceptance as a separate run only after user instruction. "
    "Do not perform GitHub upload, Stage 18 review, S18-P3, lineage full check completion, formal report "
    "release, production restore, app reinstall, live connector calls, external services, raw inbox access, "
    "or business execution in S18-P1."
)

RAW_ACTION_KEYS = (
    "raw_inbox_read_by_this_phase",
    "raw_inbox_listed_by_this_phase",
    "raw_inbox_inventory_by_this_phase",
    "raw_inbox_stat_by_this_phase",
    "raw_inbox_hashed_by_this_phase",
    "raw_inbox_modified_by_this_phase",
    "raw_inbox_deleted_by_this_phase",
    "raw_inbox_moved_by_this_phase",
    "raw_inbox_renamed_by_this_phase",
    "raw_inbox_overwritten_by_this_phase",
    "raw_inbox_written_by_this_phase",
    "raw_inbox_mutated_by_this_phase",
)


def git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def sha256_json(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + sha256(encoded).hexdigest()


def validate_s17_stage_review_dependency() -> dict[str, Any]:
    result = validate_v014_s17_stage_review()
    if result.get("stage_id") != "S17" or result.get("stage_review_performed") is not True:
        raise RuntimeError("S18-P1 requires validated v0.1.4 Stage 17 review evidence")
    if result.get("next_phase") != "S18-P1":
        raise RuntimeError("Stage 17 review must route to S18-P1")
    if result.get("s18_p1_performed") is not False:
        raise RuntimeError("Stage 17 review dependency must not already include S18-P1")
    if result.get("github_upload_performed") is not False:
        raise RuntimeError("v1.4 GitHub upload must remain deferred")
    return result


def validate_historical_s18_p1_public_safe_baseline() -> tuple[
    dict[str, Any],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    artifacts = build_default_precision_stress_suite(generated_at="2026-07-01T23:59:59+10:00")
    validate_precision_stress_artifacts(*artifacts)
    return artifacts


def load_v14_taskpack_baseline() -> dict[str, Any]:
    taskpack_text = V14_TASKPACK_PATH.read_text(encoding="utf-8")
    roadmap_text = V14_ROADMAP_PATH.read_text(encoding="utf-8")
    html_stats = []
    for ref in V14_HTML_BASELINE_REFS:
        path = Path(ref)
        text = path.read_text(encoding="utf-8")
        html_stats.append({"ref": ref, "bytes": len(text.encode("utf-8")), "sha256": sha256(text.encode("utf-8")).hexdigest()})
    for token in (
        "精度与压力测试",
        "金额精度、零差异、重复导入、坏文件、缺字段极限测试",
        "连续三次导入生成结果一致",
        "大批量文件导入性能和错误报告测试",
    ):
        if token not in roadmap_text:
            raise RuntimeError(f"v1.4 roadmap missing S18-P1 marker {token}")
    for token in ("金额精度规则", "0.01元差异即失败", "S18 时", "FAIL = 0"):
        if token not in taskpack_text:
            raise RuntimeError(f"v1.4 taskpack missing S18-P1 marker {token}")
    return {
        "taskpack_read": True,
        "roadmap_read": True,
        "roadmap_includes_s18_p1_requirements": True,
        "taskpack_includes_precision_and_uiux_gate": True,
        "html_baseline_read": True,
        "html_baseline_ref_count": len(V14_HTML_BASELINE_REFS),
        "html_baseline_private_data": False,
        "html_baseline_stats": html_stats,
        "source_refs": {
            "taskpack": V14_TASKPACK_PATH.as_posix(),
            "roadmap": V14_ROADMAP_PATH.as_posix(),
            "html_refs": list(V14_HTML_BASELINE_REFS),
        },
    }


def _raw_boundary() -> dict[str, Any]:
    result: dict[str, Any] = {key: False for key in RAW_ACTION_KEYS}
    result.update(
        {
            "raw_inbox_read_required_by_this_phase": False,
            "raw_inbox_ref": RAW_INBOX_REF,
            "private_runtime_output_dir": "KMFA/.codex_private_runtime/",
        }
    )
    return result


def _public_repo_safety() -> dict[str, bool]:
    return {
        "protected_source_material_committed": False,
        "compressed_raw_package_committed": False,
        "office_workbook_committed": False,
        "source_document_committed": False,
        "raw_or_private_table_committed": False,
        "local_database_committed": False,
        "auth_material_committed": False,
        "connector_auth_material_committed": False,
        "field_plaintext_committed": False,
        "source_header_plaintext_committed": False,
        "raw_file_names_committed": False,
        "raw_file_hashes_committed": False,
        "source_record_material_committed": False,
        "normalized_source_values_committed": False,
        "business_amount_values_committed": False,
        "public_numeric_values_committed": False,
        "project_or_customer_plaintext_committed": False,
        "account_plaintext_committed": False,
        "formal_report_committed": False,
        "business_decision_basis_committed": False,
        "production_restore_artifact_committed": False,
        "external_service_artifact_committed": False,
        "live_connector_artifact_committed": False,
        "app_reinstall_artifact_committed": False,
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
        "blocking_error_reports_recorded": True,
        "metadata_only": True,
        "public_safe_synthetic_only": True,
        "html_baseline_read": True,
        "one_cent_difference_fails": True,
        "blank_dash_hash_not_zero": True,
        "integer_cents_or_decimal_only": True,
        "raw_business_data_used": False,
        "raw_inbox_read_by_this_phase": False,
        "raw_inbox_listed_by_this_phase": False,
        "raw_inbox_stat_by_this_phase": False,
        "raw_inbox_hashed_by_this_phase": False,
        "raw_inbox_mutated_by_this_phase": False,
        "true_money_used": False,
        "raw_file_committed": False,
        "raw_file_name_committed": False,
        "raw_file_hash_committed": False,
        "field_plaintext_committed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "lineage_full_check_completed": False,
        "s18_p2_scope_included": False,
        "s18_p3_scope_included": False,
        "stage18_review_allowed": False,
        "github_upload_allowed": False,
        "phase_completion_upload_allowed": False,
        "external_connector_allowed": False,
        "production_restore_allowed": False,
        "app_reinstall_allowed": False,
        "business_execution_allowed": False,
    }


def _phase_boundaries() -> dict[str, bool]:
    return {
        "s17_stage_review_dependency_reused": True,
        "legacy_s18_p1_public_safe_baseline_reused": True,
        "s18_p1_precision_stress_scope_included": True,
        "s18_p2_full_regression_scope_included": False,
        "s18_p3_integration_scope_included": False,
        "stage18_review_scope_included": False,
        "github_upload_scope_included": False,
        "lineage_full_check_scope_included": False,
        "formal_report_runtime_scope_included": False,
        "business_execution_scope_included": False,
        "raw_inbox_access_scope_included": False,
        "production_restore_scope_included": False,
        "external_connector_scope_included": False,
        "app_reinstall_scope_included": False,
    }


def _scenario_task_id(scenario_type: str) -> str:
    if scenario_type in set(REQUIRED_V014_SCENARIO_TYPES):
        return "S18P1T01"
    raise RuntimeError(f"unknown S18-P1 scenario type: {scenario_type}")


def _scenario_rows(legacy_scenarios: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in legacy_scenarios:
        scenario_type = str(row["scenario_type"])
        rows.append(
            {
                "record_type": "v014_s18_p1_precision_stress_scenario_lock",
                "project_id": "KMFA",
                "version": "0.1.4",
                "stage_id": "S18",
                "phase_id": "S18-P1",
                "task_id": _scenario_task_id(scenario_type),
                "scenario_id": f"v014_{row['scenario_id']}",
                "scenario_type": scenario_type,
                "fixture_mode": "public_safe_synthetic",
                "case_count": row["case_count"],
                "result_status": row["result_status"],
                "policy_lock_version": POLICY_LOCK_VERSION,
                "formula_id": FORMULA_ID,
                "mapping_version": MAPPING_VERSION,
                "metadata_target": METADATA_SCENARIOS_PATH.as_posix(),
                "evidence_ref": SCENARIO_LOCK_PATH.as_posix(),
                "raw_business_data_used": False,
                "true_money_used": False,
                "raw_file_committed": False,
                "field_plaintext_committed": False,
                "github_upload_allowed": False,
            }
        )
        current = rows[-1]
        for key in (
            "minimum_fail_difference_cents",
            "money_representation",
            "float_money_allowed",
            "blank_dash_hash_defaults_to_zero",
            "zero_delta_result",
            "mismatch_queue_on_failure",
            "report_grade_a_blocked_on_unresolved_difference",
            "idempotency_result",
            "dedupe_key",
            "duplicate_raw_file_write_allowed",
            "bad_file_detected",
            "missing_field_detected",
            "error_report_ref",
            "error_report_required",
            "silent_skip_allowed",
            "field_skipped_silently",
        ):
            if key in row:
                current[key] = row[key]
    return rows


def _error_report_rows(legacy_errors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in legacy_errors:
        rows.append(
            {
                "record_type": "v014_s18_p1_precision_stress_error_report_lock",
                "project_id": "KMFA",
                "version": "0.1.4",
                "stage_id": "S18",
                "phase_id": "S18-P1",
                "task_id": "S18P1T03",
                "error_report_id": f"v014_{row['error_report_id']}",
                "error_type": row["error_type"],
                "error_code": row["error_code"],
                "severity": "blocking",
                "impact_ref": row["impact_ref"],
                "operator_action_ref": row["operator_action_ref"],
                "policy_lock_version": POLICY_LOCK_VERSION,
                "metadata_target": METADATA_ERROR_REPORTS_PATH.as_posix(),
                "evidence_ref": ERROR_REPORT_LOCK_PATH.as_posix(),
                "raw_excerpt_committed": False,
                "private_file_path_committed": False,
                "raw_business_data_committed": False,
                "true_money_committed": False,
                "github_upload_allowed": False,
                "business_execution_allowed": False,
            }
        )
    return rows


def _import_run_rows(legacy_import_runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "record_type": "v014_s18_p1_import_consistency_run_lock",
            "project_id": "KMFA",
            "version": "0.1.4",
            "stage_id": "S18",
            "phase_id": "S18-P1",
            "task_id": "S18P1T02",
            "run_id": f"v014_{row['run_id']}",
            "run_sequence": row["run_sequence"],
            "input_mode": "public_safe_synthetic_metadata_only",
            "scenario_set_hash": row["scenario_set_hash"],
            "result_hash": row["result_hash"],
            "status": "passed",
            "metadata_target": METADATA_IMPORT_RUNS_PATH.as_posix(),
            "evidence_ref": IMPORT_RUN_LOCK_PATH.as_posix(),
            "raw_file_committed": False,
            "raw_business_data_used": False,
            "raw_inbox_accessed": False,
            "github_upload_allowed": False,
        }
        for row in legacy_import_runs
    ]


def write_test_results_placeholder() -> None:
    if TEST_RESULTS_PATH.exists():
        existing = TEST_RESULTS_PATH.read_text(encoding="utf-8")
        if "focused v0.1.4 S18-P1 unit test: PASS" in existing:
            return
    write_text(
        TEST_RESULTS_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 S18-P1 Precision Stress Test Results",
                "",
                "- generator: pending final validation replay",
                "- validator: pending final validation replay",
                "- focused_unittest: pending final validation replay",
                "- governance_validation: pending final validation replay",
                "- raw_secret_scan: pending final validation replay",
                "",
            ]
        ),
    )


def generate(*, generated_at: str | None = None) -> dict[str, Any]:
    generated_at = generated_at or datetime.now().astimezone().isoformat(timespec="seconds")
    s17_review = validate_s17_stage_review_dependency()
    legacy_manifest, legacy_scenarios, legacy_import_runs, legacy_errors = (
        validate_historical_s18_p1_public_safe_baseline()
    )
    v14_baseline = load_v14_taskpack_baseline()
    scenarios = _scenario_rows(legacy_scenarios)
    import_runs = _import_run_rows(legacy_import_runs)
    error_reports = _error_report_rows(legacy_errors)
    scenario_types = {row["scenario_type"] for row in scenarios}
    result_hashes = {row["result_hash"] for row in import_runs}
    amount_precision = next(row for row in scenarios if row["scenario_type"] == "amount_precision")
    large_batch = legacy_manifest["large_batch"]
    quality_gate = _quality_gate()
    raw_boundary = _raw_boundary()
    phase_boundaries = _phase_boundaries()
    content_hash = sha256_json(
        {
            "scenarios": scenarios,
            "import_runs": import_runs,
            "error_reports": error_reports,
            "large_batch": large_batch,
            "html_refs": list(V14_HTML_BASELINE_REFS),
        }
    )
    manifest: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "v014_s18_p1_precision_stress_manifest",
        "project_id": "KMFA",
        "version": "0.1.4",
        "stage_id": "S18",
        "phase_id": "S18-P1",
        "phase_scope": PHASE_SCOPE,
        "task_id": TASK_ID,
        "acceptance_ids": [ACCEPTANCE_ID],
        "completed_task_ids": ["S18P1T01", "S18P1T02", "S18P1T03"],
        "generated_at": generated_at,
        "git_head": git_output(["rev-parse", "HEAD"]),
        "branch": git_output(["branch", "--show-current"]),
        "status": "completed_validated_local_only_no_go_upload_deferred_precision_stress_locked",
        "s17_stage_review_dependency_validated": True,
        "s17_stage_review_dependency_ref": "KMFA/stage_artifacts/V014_S17_STAGE_REVIEW/machine/stage17_review_manifest.json",
        "historical_s18_p1_public_safe_baseline_validated": True,
        "historical_s18_p1_policy_version": LEGACY_S18_P1_POLICY_VERSION,
        "required_scenario_types": list(REQUIRED_V014_SCENARIO_TYPES),
        "precision_stress_summary": {
            "scenario_count": len(scenarios),
            "scenario_type_count": len(scenario_types),
            "consecutive_import_run_count": len(import_runs),
            "unique_import_result_hash_count": len(result_hashes),
            "large_batch_file_count": large_batch["synthetic_file_count"],
            "large_batch_elapsed_ms": large_batch["elapsed_ms"],
            "large_batch_performance_budget_ms": large_batch["performance_budget_ms"],
            "error_report_count": len(error_reports),
            "html_baseline_ref_count": v14_baseline["html_baseline_ref_count"],
            "minimum_fail_difference_cents": amount_precision["minimum_fail_difference_cents"],
            "report_grade_visible": "D",
        },
        "large_batch": {
            "test_mode": "public_safe_synthetic_metadata_probe",
            "synthetic_file_count": large_batch["synthetic_file_count"],
            "failed_file_count": len(error_reports),
            "elapsed_ms": large_batch["elapsed_ms"],
            "performance_budget_ms": large_batch["performance_budget_ms"],
            "performance_result": "passed",
        },
        "stage18_phase_progress": {
            "completed_phase_count": 1,
            "total_phase_count": 3,
            "derived_percent_bps": 3333,
            "derived_percent_label": "33.33%",
            "s18_p1_performed": True,
            "s18_p2_performed": False,
            "s18_p3_performed": False,
            "stage18_review_performed": False,
        },
        "quality_gate": quality_gate,
        "phase_boundaries": phase_boundaries,
        "raw_data_boundary": raw_boundary,
        "public_repo_safety": _public_repo_safety(),
        "v14_taskpack_baseline": v14_baseline,
        "metadata_outputs": {
            "manifest": METADATA_MANIFEST_PATH.as_posix(),
            "scenarios": METADATA_SCENARIOS_PATH.as_posix(),
            "import_runs": METADATA_IMPORT_RUNS_PATH.as_posix(),
            "error_reports": METADATA_ERROR_REPORTS_PATH.as_posix(),
        },
        "artifact_refs": {
            "manifest": MANIFEST_PATH.as_posix(),
            "scenario_lock": SCENARIO_LOCK_PATH.as_posix(),
            "import_run_lock": IMPORT_RUN_LOCK_PATH.as_posix(),
            "error_report_lock": ERROR_REPORT_LOCK_PATH.as_posix(),
            "report": REPORT_PATH.as_posix(),
            "html_baseline_reading_record": HTML_READING_RECORD_PATH.as_posix(),
            "test_results": TEST_RESULTS_PATH.as_posix(),
            "risk_register": RISK_REGISTER_PATH.as_posix(),
            "rollback_plan": ROLLBACK_PATH.as_posix(),
        },
        "validation_summary": {
            "py_compile": "PENDING_FINAL_VALIDATION",
            "focused_unit_test": "PENDING_FINAL_VALIDATION",
            "s17_stage_review_dependency_validator": "PASS",
            "historical_s18_p1_baseline_validator": "PASS",
            "s18_p1_validator": "PENDING_FINAL_VALIDATION",
            "governance_validator": "PENDING_FINAL_VALIDATION",
            "lean_governance_validator": "PENDING_FINAL_VALIDATION",
            "governance_sync_validator": "PENDING_FINAL_VALIDATION",
            "no_float_money_check": "PENDING_FINAL_VALIDATION",
            "no_omission_check": "PENDING_FINAL_VALIDATION",
            "structured_parse": "PENDING_FINAL_VALIDATION",
            "raw_private_suffix_scan": "PENDING_FINAL_VALIDATION",
            "high_signal_secret_scan": "PENDING_FINAL_VALIDATION",
            "public_artifact_boundary_scan": "PENDING_FINAL_VALIDATION",
            "diff_check": "PENDING_FINAL_VALIDATION",
        },
        "github_upload": {
            "github_upload_performed": False,
            "github_upload_status": "not_uploaded_deferred_until_v014_stage1_18_complete",
            "github_upload_deferred_until_v014_stage1_18_complete": True,
            "github_upload_ready_next_gate": False,
        },
        "next_phase": NEXT_PHASE,
        "next_required_step": NEXT_REQUIRED_STEP,
        "content_hash": content_hash,
    }
    write_json(MANIFEST_PATH, manifest)
    write_json(METADATA_MANIFEST_PATH, manifest)
    write_jsonl(SCENARIO_LOCK_PATH, scenarios)
    write_jsonl(METADATA_SCENARIOS_PATH, scenarios)
    write_jsonl(IMPORT_RUN_LOCK_PATH, import_runs)
    write_jsonl(METADATA_IMPORT_RUNS_PATH, import_runs)
    write_jsonl(ERROR_REPORT_LOCK_PATH, error_reports)
    write_jsonl(METADATA_ERROR_REPORTS_PATH, error_reports)
    write_text(
        REPORT_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 S18-P1 Precision Stress Report",
                "",
                f"- generated_at: `{generated_at}`",
                f"- task_id: `{TASK_ID}`",
                "- scope: `S18-P1 only`",
                f"- scenario_count: `{len(scenarios)}`",
                f"- consecutive_import_runs: `{len(import_runs)}`",
                f"- large_batch: `{large_batch['synthetic_file_count']}` synthetic files / `{large_batch['elapsed_ms']}ms`",
                f"- error_report_count: `{len(error_reports)}`",
                "- one_cent_difference_fails: `true`",
                "- duplicate_import_idempotency: `passed`",
                "- bad_file_and_missing_field: `blocking error reports recorded`",
                "- report_grade_visible: `D`",
                "- s18_p2_performed: `false`",
                "- s18_p3_performed: `false`",
                "- stage18_review_performed: `false`",
                "- github_upload_performed: `false`",
                "- raw_inbox_access_by_this_phase: `false`",
                "- formal_report_allowed: `false`",
                "- business_execution_allowed: `false`",
                "",
            ]
        ),
    )
    write_text(
        HTML_READING_RECORD_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 S18-P1 HTML Baseline Reading Record",
                "",
                "- reading_scope: `v1.4 human-flow baseline refs only`",
                "- html_audit_executed_by_this_phase: `false`",
                "- html_full_regression_deferred_to: `S18-P2`",
                *[f"- ref: `{ref}`" for ref in V14_HTML_BASELINE_REFS],
                "",
            ]
        ),
    )
    write_test_results_placeholder()
    write_text(
        RISK_REGISTER_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 S18-P1 Risk Register",
                "",
                "- R1: Synthetic stress evidence proves deterministic public-safe controls, not production throughput.",
                "- R2: S18-P1 does not close S18-P2 full regression, lineage completeness, UI audit, formal report or delivery gates.",
                "- R3: Any future raw-backed pressure run must remain read-only and keep diagnostics out of public Git.",
                "",
            ]
        ),
    )
    write_text(
        ROLLBACK_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 S18-P1 Rollback Plan",
                "",
                "- Remove `KMFA/stage_artifacts/V014_S18_P1_PRECISION_STRESS/`.",
                "- Remove `KMFA/metadata/quality/v014_s18_p1_*` metadata files.",
                "- Revert S18-P1 governance rows and version markers.",
                "",
            ]
        ),
    )
    return manifest


def main() -> int:
    manifest = generate()
    print(
        "PASS: generated KMFA v0.1.4 S18-P1 precision stress evidence "
        f"(scenarios={manifest['precision_stress_summary']['scenario_count']}, "
        f"runs={manifest['precision_stress_summary']['consecutive_import_run_count']}, "
        f"large_batch_files={manifest['precision_stress_summary']['large_batch_file_count']}, "
        f"errors={manifest['precision_stress_summary']['error_report_count']}, "
        "s18_p2=false, s18_p3=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
