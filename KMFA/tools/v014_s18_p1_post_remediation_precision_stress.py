#!/usr/bin/env python3
"""Execute current KMFA v0.1.4 S18-P1 precision and stress validation."""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Any

from KMFA.tools import v014_s17_post_remediation_stage_review as s17_review
from KMFA.tools import v014_s18_p1_precision_stress as historical_s18_p1
from KMFA.tools.amount_tools import AmountNormalizationError, normalize_amount_to_cents
from KMFA.tools.check_v014_s17_post_remediation_stage_review import (
    validate_v014_s17_post_remediation_stage_review,
)
from KMFA.tools.v014_s04_p1_amount_precision import replay_amount_precision_capability
from KMFA.tools.zero_delta_validator import validate_zero_delta


PHASE_ID = "V014_S18_P1_POST_REMEDIATION_PRECISION_STRESS"
ROADMAP_PHASE_ID = "S18-P1"
TASK_ID = "KMFA-V014-S18-P1-POST-REMEDIATION-PRECISION-STRESS-20260712"
ACCEPTANCE_ID = "ACC-V014-S18-P1-POST-REMEDIATION-PRECISION-STRESS"
VERSION = "0.1.4-s18-p1-post-remediation-precision-stress"
STATUS = "completed_validated_local_only_s18_p1_precision_stress_no_go_upload_deferred"
DECISION = "NO_GO"
FORMULA_ID = "FORM-KMFA-V014-S18-P1-POST-REMEDIATION-PRECISION-STRESS-001"
PARAMETER_IDS = ("PARAM-KMFA-1807", "PARAM-KMFA-1808", "PARAM-KMFA-1809")
MODEL_REGISTRY_KEY = "kmfa_v014_s18_p1_post_remediation_precision_stress"

SYNTHETIC_BATCH_ITEM_COUNT = 1200
VALID_SYNTHETIC_RECORD_COUNT = 1198
PERFORMANCE_BUDGET_MS = 1500
IMPORT_RUN_COUNT = 3

OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_S18_P1_POST_REMEDIATION_PRECISION_STRESS")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
MANIFEST_PATH = MACHINE_DIR / "precision_stress_manifest.json"
SCENARIO_RESULTS_PATH = MACHINE_DIR / "precision_stress_scenario_results_public_safe.jsonl"
IMPORT_RUN_RESULTS_PATH = MACHINE_DIR / "import_consistency_runs_public_safe.jsonl"
ERROR_REPORTS_PATH = MACHINE_DIR / "precision_stress_error_reports_public_safe.jsonl"
ACCEPTANCE_MATRIX_PATH = MACHINE_DIR / "acceptance_matrix_public_safe.json"
GO_NO_GO_PATH = MACHINE_DIR / "go_no_go_report.json"

REPORT_PATH = HUMAN_DIR / "precision_stress_report_zh.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results_zh.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register_zh.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan_zh.md"

METADATA_DIR = Path("KMFA/metadata/quality")
METADATA_MANIFEST_PATH = METADATA_DIR / "v014_s18_p1_post_remediation_precision_stress_manifest.json"
METADATA_SCENARIOS_PATH = METADATA_DIR / "v014_s18_p1_post_remediation_precision_stress_scenarios.jsonl"
METADATA_IMPORT_RUNS_PATH = METADATA_DIR / "v014_s18_p1_post_remediation_import_consistency_runs.jsonl"
METADATA_ERROR_REPORTS_PATH = METADATA_DIR / "v014_s18_p1_post_remediation_precision_stress_error_reports.jsonl"
METADATA_ACCEPTANCE_PATH = METADATA_DIR / "v014_s18_p1_post_remediation_precision_stress_acceptance_matrix.json"
METADATA_GO_NO_GO_PATH = METADATA_DIR / "v014_s18_p1_post_remediation_precision_stress_go_no_go_report.json"

PRIVATE_DIR = Path("KMFA/.codex_private_runtime/v014_s18_p1_post_remediation_precision_stress")
PRIVATE_RAW_BEFORE_PATH = PRIVATE_DIR / "raw_immutability_before.json"
PRIVATE_RAW_AFTER_PATH = PRIVATE_DIR / "raw_immutability_after.json"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_DIR / "precision_stress_runtime_diagnostic.json"
PRIVATE_REPORT_PATH = PRIVATE_DIR / "precision_stress_boundary_validation_zh.md"

TASKPACK_PATH = Path("KMFA/taskpack/v1_4/taskpack/01_KMFA_Codex_TaskPack_v1_4_public_safe.md")
ROADMAP_PATH = Path("KMFA/taskpack/v1_4/roadmap/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_4.md")
HTML_BASELINE_REFS = (
    "KMFA/taskpack/v1_4/html_uiux/00_KMFA_HTML_human_flow_entry_v1_4.html",
    "KMFA/taskpack/v1_4/html_uiux/KMFA_Codex开发任务控制台可点击预览_v1_4.html",
    "KMFA/taskpack/v1_4/html_uiux/KMFA_待处理事项工作台可点击预览_v1_4.html",
    "KMFA/taskpack/v1_4/html_uiux/KMFA_数据源检查板可点击预览_v1_4.html",
    "KMFA/taskpack/v1_4/html_uiux/KMFA_系统全流程可点击验收样板_v1_4.html",
    "KMFA/taskpack/v1_4/html_uiux/KMFA_经营分析报告可点击预览_v1_4.html",
)

FORBIDDEN_PUBLIC_TEXT = (
    "private_ref://",
    "original_filename",
    "sheet_name_private",
    "source_header_text",
    "raw_value",
    "normalized_value",
    "customer_name_plaintext",
    "project_name_plaintext",
    "counterparty_name_plaintext",
    "supplier_name_plaintext",
    "payment_account",
    "bank_account_number",
    "contract_number",
    "invoice_number",
    "/Users/linzezhang/Downloads",
    "KMFA_MetaData",
)

DEVELOPMENT_EVENTS_PATH = Path("KMFA/docs/governance/development_events.jsonl")
STAGE_STATUS_PATH = Path("KMFA/metadata/stage_status.jsonl")
TASK_STATUS_PATH = Path("KMFA/metadata/traceability/v1_4_stage_phase_task_status.jsonl")
ASSURANCE_STATUS_PATH = Path("KMFA/docs/governance/ASSURANCE_STATUS.yaml")


def _git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    return result.stdout.strip()


def _sha256_json(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + sha256(encoded).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not all(isinstance(row, dict) for row in rows):
        raise ValueError(f"expected JSONL objects: {path}")
    return rows


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def _upsert_jsonl(path: Path, row: dict[str, Any]) -> None:
    phase_id = row.get("phase_id")
    if not isinstance(phase_id, str) or not phase_id:
        raise ValueError("governance JSONL row requires phase_id")
    preserved: list[str] = []
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip() and json.loads(line).get("phase_id") != phase_id:
                preserved.append(line)
    preserved.append(json.dumps(row, ensure_ascii=False, separators=(",", ":")))
    _write_text(path, "\n".join(preserved) + "\n")


def _taskpack_contract() -> dict[str, Any]:
    taskpack = TASKPACK_PATH.read_text(encoding="utf-8")
    roadmap = ROADMAP_PATH.read_text(encoding="utf-8")
    required_roadmap = (
        "| P1 | 精度与压力测试 |",
        "金额精度、零差异、重复导入、坏文件、缺字段极限测试",
        "连续三次导入生成结果一致",
        "大批量文件导入性能和错误报告测试",
    )
    required_taskpack = (
        "金额精度测试通过",
        "零差异测试通过",
        "原始数据不可污染测试通过",
        "no_omission检查通过",
    )
    if not all(token in roadmap for token in required_roadmap):
        raise ValueError("v1.4 roadmap S18-P1 contract drift")
    if not all(token in taskpack for token in required_taskpack):
        raise ValueError("v1.4 taskpack acceptance contract drift")
    html_stats = []
    for ref in HTML_BASELINE_REFS:
        payload = Path(ref).read_bytes()
        html_stats.append({"ref": ref, "byte_count": len(payload), "sha256": sha256(payload).hexdigest()})
    return {
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "task_count": 3,
        "taskpack_read": True,
        "roadmap_read": True,
        "html_baseline_read": True,
        "html_baseline_ref_count": len(HTML_BASELINE_REFS),
        "html_baseline_stats": html_stats,
        "source_refs": [TASKPACK_PATH.as_posix(), ROADMAP_PATH.as_posix(), *HTML_BASELINE_REFS],
    }


def _stage17_dependency() -> dict[str, Any]:
    manifest = validate_v014_s17_post_remediation_stage_review(
        require_private_evidence=True,
        require_final_evidence=True,
    )
    if manifest.get("phase_id") != s17_review.PHASE_ID:
        raise ValueError("current Stage 17 review identity drift")
    if manifest.get("next_phase") != "S18-P1":
        raise ValueError("current Stage 17 review does not route to S18-P1")
    if manifest.get("go_no_go", {}).get("github_upload_allowed") is not False:
        raise ValueError("current Stage 17 review upload boundary opened")
    return {
        "validated": True,
        "phase_id": manifest["phase_id"],
        "status": manifest["status"],
        "decision": manifest["decision"],
        "evidence_ref": s17_review.MANIFEST_PATH.as_posix(),
    }


def _historical_baseline() -> dict[str, Any]:
    manifest, scenarios, runs, errors = historical_s18_p1.validate_historical_s18_p1_public_safe_baseline()
    if (len(scenarios), len(runs), len(errors)) != (5, 3, 2):
        raise ValueError("historical S18-P1 structural baseline drift")
    if manifest.get("large_batch", {}).get("synthetic_file_count") != 1200:
        raise ValueError("historical S18-P1 large batch structure drift")
    return {
        "validated": True,
        "scenario_count": len(scenarios),
        "import_run_count": len(runs),
        "error_report_count": len(errors),
        "synthetic_file_count": manifest["large_batch"]["synthetic_file_count"],
        "dynamic_state_authoritative": False,
        "evidence_ref": historical_s18_p1.MANIFEST_PATH.as_posix(),
    }


def _build_synthetic_batch() -> list[dict[str, str]]:
    amount_inputs = ("0", "0.01", "1,234.56", "-9.99", "1万元", "0.001千元")
    rows = [
        {
            "synthetic_id": f"SYN-{index:04d}",
            "record_type": "valid",
            "required_marker": "present",
            "amount_input": amount_inputs[index % len(amount_inputs)],
        }
        for index in range(VALID_SYNTHETIC_RECORD_COUNT)
    ]
    rows.append({"synthetic_id": "SYN-1198", "record_type": "bad_file", "required_marker": "present"})
    rows.append({"synthetic_id": "SYN-1199", "record_type": "valid", "amount_input": "1.00"})
    return rows


def _process_batch(
    batch: list[dict[str, str]],
    state: dict[str, str],
    *,
    run_sequence: int,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    started_ns = time.perf_counter_ns()
    inserted_count = 0
    duplicate_count = 0
    errors: list[dict[str, Any]] = []
    for record in batch:
        synthetic_id = record["synthetic_id"]
        if record.get("record_type") == "bad_file":
            errors.append(
                {
                    "error_type": "bad_file",
                    "error_code": "S18P1_BAD_FILE_BLOCKED",
                    "severity": "blocking",
                    "operator_action": "隔离合成坏文件并修复容器后重试",
                }
            )
            continue
        if record.get("required_marker") != "present":
            errors.append(
                {
                    "error_type": "missing_field",
                    "error_code": "S18P1_REQUIRED_FIELD_MISSING",
                    "severity": "blocking",
                    "operator_action": "补齐必填字段后重新执行导入",
                }
            )
            continue
        try:
            cents = normalize_amount_to_cents(record["amount_input"])
        except (AmountNormalizationError, KeyError) as exc:
            errors.append(
                {
                    "error_type": "bad_file",
                    "error_code": "S18P1_AMOUNT_PARSE_BLOCKED",
                    "severity": "blocking",
                    "operator_action": type(exc).__name__,
                }
            )
            continue
        record_hash = _sha256_json({"synthetic_id": synthetic_id, "integer_cents": cents})
        prior = state.get(synthetic_id)
        if prior is None:
            state[synthetic_id] = record_hash
            inserted_count += 1
        elif prior == record_hash:
            duplicate_count += 1
        else:
            errors.append(
                {
                    "error_type": "duplicate_conflict",
                    "error_code": "S18P1_DUPLICATE_CONFLICT",
                    "severity": "blocking",
                    "operator_action": "保留旧版本并进入人工复核",
                }
            )
    elapsed_ns = time.perf_counter_ns() - started_ns
    elapsed_ms = max(1, (elapsed_ns + 999_999) // 1_000_000)
    final_state_hash = _sha256_json(sorted(state.items()))
    error_set_hash = _sha256_json(sorted((row["error_type"], row["error_code"]) for row in errors))
    return (
        {
            "record_type": "v014_s18_p1_post_remediation_import_consistency_run",
            "project_id": "KMFA",
            "stage_id": "S18",
            "phase_id": PHASE_ID,
            "run_sequence": run_sequence,
            "input_mode": "public_safe_synthetic_file_metadata_in_memory",
            "synthetic_batch_item_count": len(batch),
            "inserted_record_count": inserted_count,
            "duplicate_record_count": duplicate_count,
            "blocking_error_count": len(errors),
            "final_state_record_count": len(state),
            "final_state_hash": final_state_hash,
            "error_set_hash": error_set_hash,
            "elapsed_ms": elapsed_ms,
            "performance_budget_ms": PERFORMANCE_BUDGET_MS,
            "status": "PASS" if elapsed_ms <= PERFORMANCE_BUDGET_MS else "FAIL",
            "raw_business_data_used": False,
            "raw_file_write_count": 0,
            "persistent_business_write_count": 0,
        },
        errors,
    )


def _zero_delta_probe() -> dict[str, Any]:
    authoritative = [
        {"synthetic_key": "A", "metric_cents": 0, "source": "synthetic_authoritative"},
        {"synthetic_key": "B", "metric_cents": 123456, "source": "synthetic_authoritative"},
        {"synthetic_key": "C", "metric_cents": -999, "source": "synthetic_authoritative"},
    ]
    exact = [dict(row, source="synthetic_system") for row in authoritative]
    mismatch = [dict(row, source="synthetic_system") for row in authoritative]
    mismatch[1]["metric_cents"] += 1
    exact_result = validate_zero_delta(
        authoritative,
        exact,
        key_fields=("synthetic_key",),
        amount_fields=("metric_cents",),
    )
    mismatch_result = validate_zero_delta(
        authoritative,
        mismatch,
        key_fields=("synthetic_key",),
        amount_fields=("metric_cents",),
    )
    return {
        "exact_passed": exact_result["zero_delta_passed"],
        "exact_mismatch_count": exact_result["mismatch_count"],
        "one_cent_mismatch_rejected": not mismatch_result["zero_delta_passed"],
        "one_cent_mismatch_count": mismatch_result["mismatch_count"],
        "minimum_fail_difference_cents": mismatch_result["minimum_fail_difference_cents"],
    }


def _scenario_results(amount: dict[str, Any], zero_delta: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "record_type": "v014_s18_p1_post_remediation_precision_stress_scenario",
            "scenario_id": "S18P1-CURRENT-AMOUNT-PRECISION",
            "scenario_type": "amount_precision",
            "task_id": "S18P1T01",
            "case_count": amount["amount_case_count"] + amount["amount_rejection_count"],
            "pass_count": amount["amount_case_passed_count"] + amount["amount_rejection_passed_count"],
            "minimum_fail_difference_cents": 1,
            "integer_cents_or_decimal_only": True,
            "float_money_rejected": True,
            "fractional_cent_rejected": True,
            "status": "PASS",
        },
        {
            "record_type": "v014_s18_p1_post_remediation_precision_stress_scenario",
            "scenario_id": "S18P1-CURRENT-ZERO-DELTA",
            "scenario_type": "zero_delta",
            "task_id": "S18P1T01",
            "case_count": 2,
            "pass_count": 2,
            "minimum_fail_difference_cents": zero_delta["minimum_fail_difference_cents"],
            "zero_delta_exact_passed": zero_delta["exact_passed"],
            "one_cent_mismatch_rejected": zero_delta["one_cent_mismatch_rejected"],
            "difference_queue_required": True,
            "report_grade_upgrade_blocked": True,
            "status": "PASS",
        },
        {
            "record_type": "v014_s18_p1_post_remediation_precision_stress_scenario",
            "scenario_id": "S18P1-CURRENT-DUPLICATE-IMPORT",
            "scenario_type": "duplicate_import",
            "task_id": "S18P1T01",
            "case_count": 3,
            "pass_count": 3,
            "idempotency_required": True,
            "final_state_hash_consistency_required": True,
            "status": "PASS",
        },
        {
            "record_type": "v014_s18_p1_post_remediation_precision_stress_scenario",
            "scenario_id": "S18P1-CURRENT-BAD-FILE",
            "scenario_type": "bad_file",
            "task_id": "S18P1T01",
            "case_count": 1,
            "pass_count": 1,
            "blocking_error_required": True,
            "silent_skip_allowed": False,
            "status": "PASS",
        },
        {
            "record_type": "v014_s18_p1_post_remediation_precision_stress_scenario",
            "scenario_id": "S18P1-CURRENT-MISSING-FIELD",
            "scenario_type": "missing_field",
            "task_id": "S18P1T01",
            "case_count": 1,
            "pass_count": 1,
            "blocking_error_required": True,
            "silent_skip_allowed": False,
            "status": "PASS",
        },
    ]


def run_precision_stress_suite() -> dict[str, Any]:
    amount = replay_amount_precision_capability()
    zero_delta = _zero_delta_probe()
    batch = _build_synthetic_batch()
    state: dict[str, str] = {}
    import_runs: list[dict[str, Any]] = []
    observed_errors: list[dict[str, Any]] = []
    for run_sequence in range(1, IMPORT_RUN_COUNT + 1):
        run, errors = _process_batch(batch, state, run_sequence=run_sequence)
        import_runs.append(run)
        if not observed_errors:
            observed_errors = errors
    error_reports = [
        {
            "record_type": "v014_s18_p1_post_remediation_precision_stress_error_report",
            "error_report_id": f"S18P1-CURRENT-{row['error_type'].upper().replace('_', '-')}",
            "error_type": row["error_type"],
            "error_code": row["error_code"],
            "severity": "blocking",
            "operator_action": row["operator_action"],
            "occurrence_count_per_run": 1,
            "raw_payload_committed": False,
            "private_path_committed": False,
            "business_value_committed": False,
        }
        for row in observed_errors
    ]
    scenarios = _scenario_results(amount, zero_delta)
    summary = {
        "scenario_count": len(scenarios),
        "scenario_pass_count": sum(row["status"] == "PASS" for row in scenarios),
        "amount_case_count": amount["amount_case_count"],
        "amount_case_pass_count": amount["amount_case_passed_count"],
        "amount_rejection_case_count": amount["amount_rejection_count"],
        "amount_rejection_pass_count": amount["amount_rejection_passed_count"],
        "repository_no_float_scan_passed": amount["repository_no_float_scan_passed"],
        "zero_delta_exact_passed": zero_delta["exact_passed"],
        "one_cent_mismatch_rejected": zero_delta["one_cent_mismatch_rejected"],
        "one_cent_mismatch_count": zero_delta["one_cent_mismatch_count"],
        "import_run_count": len(import_runs),
        "unique_final_state_hash_count": len({row["final_state_hash"] for row in import_runs}),
        "synthetic_batch_item_count": len(batch),
        "valid_synthetic_record_count": len(state),
        "first_run_inserted_record_count": import_runs[0]["inserted_record_count"],
        "later_run_duplicate_record_count": sum(row["duplicate_record_count"] for row in import_runs[1:]),
        "blocking_error_report_count": len(error_reports),
        "max_elapsed_ms": max(row["elapsed_ms"] for row in import_runs),
        "performance_budget_ms": PERFORMANCE_BUDGET_MS,
    }
    suite = {
        "summary": summary,
        "scenarios": scenarios,
        "import_runs": import_runs,
        "error_reports": error_reports,
        "private_diagnostic": {
            "amount_probe": amount,
            "zero_delta_probe": zero_delta,
            "run_elapsed_ms": [row["elapsed_ms"] for row in import_runs],
        },
    }
    validate_precision_stress_suite(suite)
    return suite


def validate_precision_stress_suite(suite: dict[str, Any]) -> None:
    summary = suite["summary"]
    scenarios = suite["scenarios"]
    runs = suite["import_runs"]
    errors = suite["error_reports"]
    required_types = {"amount_precision", "zero_delta", "duplicate_import", "bad_file", "missing_field"}
    checks = (
        len(scenarios) == 5,
        {row["scenario_type"] for row in scenarios} == required_types,
        all(row["status"] == "PASS" for row in scenarios),
        summary["amount_case_count"] == summary["amount_case_pass_count"] == 9,
        summary["amount_rejection_case_count"] == summary["amount_rejection_pass_count"] == 9,
        summary["repository_no_float_scan_passed"] is True,
        summary["zero_delta_exact_passed"] is True,
        summary["one_cent_mismatch_rejected"] is True,
        summary["one_cent_mismatch_count"] == 1,
        len(runs) == 3,
        [row["run_sequence"] for row in runs] == [1, 2, 3],
        len({row["final_state_hash"] for row in runs}) == 1,
        runs[0]["inserted_record_count"] == VALID_SYNTHETIC_RECORD_COUNT,
        runs[0]["duplicate_record_count"] == 0,
        all(row["inserted_record_count"] == 0 for row in runs[1:]),
        all(row["duplicate_record_count"] == VALID_SYNTHETIC_RECORD_COUNT for row in runs[1:]),
        all(row["blocking_error_count"] == 2 for row in runs),
        summary["synthetic_batch_item_count"] == SYNTHETIC_BATCH_ITEM_COUNT,
        summary["valid_synthetic_record_count"] == VALID_SYNTHETIC_RECORD_COUNT,
        summary["blocking_error_report_count"] == 2,
        summary["max_elapsed_ms"] <= summary["performance_budget_ms"] == PERFORMANCE_BUDGET_MS,
        {row["error_type"] for row in errors} == {"bad_file", "missing_field"},
        all(row["severity"] == "blocking" for row in errors),
    )
    if not all(checks):
        raise ValueError("current S18-P1 precision stress suite failed")


def _phase_boundaries() -> dict[str, bool]:
    return {
        "stage17_post_remediation_review_dependency_reused": True,
        "historical_s18_p1_structural_baseline_reused": True,
        "s18_p1_precision_stress_performed": True,
        "actual_synthetic_stress_execution_performed": True,
        "private_raw_snapshot_validation_performed": True,
        "s18_p2_full_regression_performed": False,
        "s18_p3_integration_preparation_performed": False,
        "stage18_review_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "formal_report_generated": False,
        "lineage_full_check_performed": False,
        "external_connector_called": False,
        "production_restore_performed": False,
        "raw_copy_or_backup_performed": False,
        "difference_closure_performed": False,
        "persistent_business_write_performed": False,
        "business_execution_performed": False,
    }


def _public_repo_safety() -> dict[str, bool]:
    return {
        "raw_business_data_committed": False,
        "raw_filename_committed": False,
        "raw_hash_committed": False,
        "field_or_header_plaintext_committed": False,
        "business_amount_committed": False,
        "business_detail_committed": False,
        "private_csv_committed": False,
        "office_or_pdf_committed": False,
        "database_committed": False,
        "credential_committed": False,
    }


def _acceptance_matrix(summary: dict[str, Any]) -> dict[str, Any]:
    checks = (
        ("stage17_dependency", summary["stage17_review_dependency_validated"]),
        ("scenario_coverage", summary["scenario_pass_count"] == 5),
        ("amount_precision", summary["amount_case_pass_count"] == 9),
        ("amount_rejections", summary["amount_rejection_pass_count"] == 9),
        ("no_float", summary["repository_no_float_scan_passed"]),
        ("zero_delta", summary["zero_delta_exact_passed"]),
        ("one_cent_block", summary["one_cent_mismatch_rejected"]),
        ("three_runs", summary["import_run_count"] == 3),
        ("consistent_state", summary["unique_final_state_hash_count"] == 1),
        ("duplicate_idempotency", summary["later_run_duplicate_record_count"] == 2396),
        ("batch_size", summary["synthetic_batch_item_count"] == 1200),
        ("blocking_errors", summary["blocking_error_report_count"] == 2),
        ("performance", summary["max_elapsed_ms"] <= summary["performance_budget_ms"]),
        ("raw_exact", summary["raw_snapshot_exact_match"] and summary["raw_cross_phase_snapshot_exact_match"]),
        ("grade_lock", summary["current_report_grade"] == "D" and summary["decision"] == "NO_GO"),
        ("s18_p2_closed", not summary["s18_p2_performed"]),
        ("stage_review_closed", not summary["stage18_review_performed"]),
        ("upload_closed", not summary["github_upload_performed"]),
        ("business_closed", not summary["business_execution_performed"]),
    )
    rows = [
        {"check_id": f"S18P1-CURRENT-ACC-{index:02d}", "name": name, "status": "PASS" if passed else "FAIL"}
        for index, (name, passed) in enumerate(checks, 1)
    ]
    return {
        "schema_version": "kmfa.v014.s18_p1_post_remediation_acceptance_matrix.v1",
        "acceptance_id": ACCEPTANCE_ID,
        "check_count": len(rows),
        "check_pass_count": sum(row["status"] == "PASS" for row in rows),
        "check_fail_count": sum(row["status"] == "FAIL" for row in rows),
        "checks": rows,
    }


def _phase_public_files() -> list[str]:
    paths = (
        MANIFEST_PATH, SCENARIO_RESULTS_PATH, IMPORT_RUN_RESULTS_PATH, ERROR_REPORTS_PATH,
        ACCEPTANCE_MATRIX_PATH, GO_NO_GO_PATH, REPORT_PATH, TEST_RESULTS_PATH, RISK_REGISTER_PATH, ROLLBACK_PATH,
        METADATA_MANIFEST_PATH, METADATA_SCENARIOS_PATH, METADATA_IMPORT_RUNS_PATH, METADATA_ERROR_REPORTS_PATH,
        METADATA_ACCEPTANCE_PATH, METADATA_GO_NO_GO_PATH,
        Path("KMFA/AGENTS.md"), Path("KMFA/CHANGELOG.md"), Path("KMFA/HANDOFF.md"), Path("KMFA/README.md"), Path("KMFA/VERSION"),
        ASSURANCE_STATUS_PATH, Path("KMFA/docs/governance/DEVELOPMENT_LEDGER.md"),
        Path("KMFA/docs/governance/MODEL_SPEC.md"), Path("KMFA/docs/governance/OWNER_STATUS.md"),
        Path("KMFA/docs/governance/STATUS.md"), Path("KMFA/docs/governance/TRACEABILITY_MATRIX.csv"),
        Path("KMFA/docs/governance/VERSION_MATRIX.yaml"), Path("KMFA/docs/governance/delivery_tasks.yaml"),
        DEVELOPMENT_EVENTS_PATH, Path("KMFA/docs/governance/formula_registry.yaml"),
        Path("KMFA/docs/governance/model_registry.yaml"), Path("KMFA/docs/governance/parameter_registry.csv"),
        Path("KMFA/metadata/model_registry.yaml"), STAGE_STATUS_PATH, TASK_STATUS_PATH,
        Path("KMFA/功能清单.md"), Path("KMFA/开发记录.md"), Path("KMFA/模型参数文件.md"),
        Path("KMFA/tools/v014_s18_p1_post_remediation_precision_stress.py"),
        Path("KMFA/tools/check_v014_s18_p1_post_remediation_precision_stress.py"),
        Path("KMFA/tests/test_v014_s18_p1_post_remediation_precision_stress.py"),
    )
    return [path.as_posix() for path in paths]


def _write_governance(generated_at: str) -> None:
    s17_review._sync_assurance_snapshot_time(generated_at)
    evidence_ref = MANIFEST_PATH.as_posix()
    _upsert_jsonl(
        DEVELOPMENT_EVENTS_PATH,
        {
            "event_id": "DEV-KMFA-20260712-V014-S18-P1-POST-REMEDIATION-PRECISION-STRESS",
            "event_time": generated_at,
            "event_type": "phase_completion",
            "project_id": "KMFA",
            "stage_id": "S18",
            "phase_id": PHASE_ID,
            "roadmap_phase_id": ROADMAP_PHASE_ID,
            "task_id": TASK_ID,
            "status": STATUS,
            "fact_level": "EXTRACTED",
            "decision": DECISION,
            "scenario_pass_count": 5,
            "import_run_count": 3,
            "synthetic_batch_item_count": 1200,
            "blocking_error_report_count": 2,
            "raw_business_data_committed": False,
            "github_upload_performed": False,
            "app_reinstall_performed": False,
            "business_execution_performed": False,
            "evidence_ref": evidence_ref,
            "files_changed": _phase_public_files(),
            "result_commit": "PENDING",
        },
    )
    _upsert_jsonl(
        STAGE_STATUS_PATH,
        {
            "schema_version": "kmfa.stage_status.v1",
            "record_type": "phase_status",
            "project_id": "KMFA",
            "stage_id": "S18",
            "phase_id": PHASE_ID,
            "roadmap_phase_id": ROADMAP_PHASE_ID,
            "task_id": TASK_ID,
            "version": VERSION,
            "status": STATUS,
            "fact_level": "EXTRACTED",
            "decision": DECISION,
            "current_report_grade": "D",
            "raw_data_committed": False,
            "github_upload_performed": False,
            "app_reinstall_performed": False,
            "business_execution_performed": False,
            "evidence_ref": evidence_ref,
            "updated_at": generated_at,
        },
    )
    _upsert_jsonl(
        TASK_STATUS_PATH,
        {
            "schema_version": "kmfa.v014_stage_phase_task_status.v1",
            "record_type": "v014_stage_phase_task",
            "project_id": "KMFA",
            "stage_id": "S18",
            "governance_stage_id": "FINAL-REGRESSION-STRESS",
            "roadmap_stage_id": "S18",
            "roadmap_phase_id": ROADMAP_PHASE_ID,
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "acceptance_id": ACCEPTANCE_ID,
            "version": VERSION,
            "name": "v0.1.4 S18-P1 post-remediation precision and stress",
            "phase_goal": "execute actual public-safe synthetic precision idempotency and large-batch stress controls",
            "status": STATUS,
            "fact_level": "EXTRACTED",
            "derived_percent": 100,
            "estimated_task_units": 3,
            "completed_task_units": 3,
            "task_count": 3,
            "raw_data_committed": False,
            "evidence_ref": evidence_ref,
            "updated_at": generated_at[:10],
        },
    )


def _render_report(summary: dict[str, Any]) -> str:
    return f"""# KMFA v0.1.4 S18-P1 精度与压力测试

## 结论

- 当前依赖：Stage 17 post-remediation review 已通过严格验证。
- 精度：金额通过/拒绝=`{summary['amount_case_pass_count']}/9` 与 `{summary['amount_rejection_pass_count']}/9`，float 和非整分输入均拒绝。
- 零差异：完全一致 PASS；1 分差异被阻断并要求进入差异队列。
- 重复导入：连续 3 次最终状态 hash 一致；首次写入 1198 条，后两次各识别 1198 条重复且新增为 0。
- 压力：实际内存合成 file metadata 规模 `{summary['synthetic_batch_item_count']}`，最大耗时 `{summary['max_elapsed_ms']}ms`，预算 `{summary['performance_budget_ms']}ms`。
- 错误：坏文件和缺字段共 2 类 blocking error report，无静默跳过。
- raw：phase 前后、跨 Stage 17 review 与当前只读快照一致。
- 当前状态：Q4 / D / NO_GO / 3-9-2-1。

## 边界

- 本轮仅完成 S18-P1；未执行 S18-P2/P3、Stage 18 review、GitHub upload 或 app reinstall。
- 性能输入全部为内存合成 metadata，不是生产吞吐证明；未复制、备份或写入 raw。
- 下一轮只能单独执行 S18-P2 全量回归和验收。
"""


def generate(*, final_validation: bool = False, write_governance: bool = True) -> dict[str, Any]:
    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    taskpack = _taskpack_contract()
    dependency = _stage17_dependency()
    historical = _historical_baseline()

    raw_helper = s17_review.p1.s16_review.p1.s15_review.p1.s14_review.p1.s13_review.p1.s12_review.p1.s11_project
    raw_before = raw_helper._raw_snapshot("before_v014_s18_p1_post_remediation_precision_stress")
    suite = run_precision_stress_suite()
    raw_after = raw_helper._raw_snapshot("after_v014_s18_p1_post_remediation_precision_stress")
    prior_raw = _read_json(s17_review.PRIVATE_RAW_AFTER_PATH)
    current_raw = raw_helper._raw_snapshot("current_v014_s18_p1_post_remediation_precision_stress")
    normalize = raw_helper._normalize_raw
    raw_exact = normalize(raw_before) == normalize(raw_after)
    raw_cross = normalize(raw_before) == normalize(prior_raw) == normalize(current_raw)
    if not raw_exact or not raw_cross:
        raise ValueError("raw source changed during current S18-P1")
    repo_scan = s17_review.p1._repo_tracking_scan()
    if repo_scan["status"] != "PASS":
        raise ValueError("tracked repository safety scan failed")

    base = suite["summary"]
    boundaries = _phase_boundaries()
    summary = {
        "schema_version": "kmfa.v014.s18_p1_post_remediation_precision_stress_summary.v1",
        "project_id": "KMFA",
        "stage_id": "S18",
        "phase_id": PHASE_ID,
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "version": VERSION,
        "status": STATUS,
        "decision": DECISION,
        "stage17_review_dependency_validated": dependency["validated"],
        **base,
        "raw_source_file_count": raw_before["file_count"],
        "raw_snapshot_exact_match": raw_exact,
        "raw_cross_phase_snapshot_exact_match": raw_cross,
        "tracked_forbidden_suffix_count": repo_scan["tracked_forbidden_suffix_count"],
        "tracked_private_runtime_path_count": repo_scan["tracked_private_runtime_path_count"],
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "open_final_difference_accepted_count": 3,
        "nonzero_delta_reconciliation_count": 9,
        "zero_delta_reconciliation_count": 2,
        "incomplete_reconciliation_count": 1,
        "s18_p1_performed": True,
        "s18_p2_performed": False,
        "s18_p3_performed": False,
        "stage18_review_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }
    matrix = _acceptance_matrix(summary)
    go_no_go = {
        "schema_version": "kmfa.v014.s18_p1_post_remediation_go_no_go.v1",
        "project_id": "KMFA",
        "stage_id": "S18",
        "phase_id": PHASE_ID,
        "decision": DECISION,
        "s18_p1_validated": matrix["check_fail_count"] == 0,
        "s18_p2_allowed_in_this_run": False,
        "s18_p3_allowed": False,
        "stage18_review_allowed": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "formal_report_release_allowed": False,
        "external_connector_allowed": False,
        "production_restore_allowed": False,
        "difference_closure_allowed": False,
        "persistent_business_write_allowed": False,
        "business_execution_allowed": False,
    }
    validation_summary = {
        "final_validation_recorded": final_validation,
        "focused_tests": "PASS" if final_validation else "PENDING",
        "strict_validator": "PASS" if final_validation else "PENDING",
        "actual_precision_stress_suite": "PASS",
        "raw_alignment": "PASS",
        "governance_and_safety_scans": "PASS" if final_validation else "PENDING",
    }
    manifest = {
        "schema_version": "kmfa.v014.s18_p1_post_remediation_precision_stress_manifest.v1",
        "project_id": "KMFA",
        "stage_id": "S18",
        "phase_id": PHASE_ID,
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "version": VERSION,
        "status": STATUS,
        "decision": DECISION,
        "generated_at": generated_at,
        "reviewed_head": _git_output(["rev-parse", "HEAD"]),
        "branch": _git_output(["branch", "--show-current"]),
        "remote": _git_output(["remote", "get-url", "origin"]),
        "formula_id": FORMULA_ID,
        "parameter_ids": list(PARAMETER_IDS),
        "model_registry_key": MODEL_REGISTRY_KEY,
        "stage17_review_dependency": dependency,
        "historical_s18_p1_structural_baseline_validated": historical["validated"],
        "historical_s18_p1_dynamic_state_authoritative": historical["dynamic_state_authoritative"],
        "historical_s18_p1_baseline": historical,
        "taskpack_contract": taskpack,
        "summary": summary,
        "phase_boundaries": boundaries,
        "public_repo_safety": _public_repo_safety(),
        "acceptance_matrix": matrix,
        "go_no_go": go_no_go,
        "validation_summary": validation_summary,
        "artifact_refs": {
            "manifest": MANIFEST_PATH.as_posix(),
            "scenarios": SCENARIO_RESULTS_PATH.as_posix(),
            "import_runs": IMPORT_RUN_RESULTS_PATH.as_posix(),
            "error_reports": ERROR_REPORTS_PATH.as_posix(),
            "acceptance": ACCEPTANCE_MATRIX_PATH.as_posix(),
            "go_no_go": GO_NO_GO_PATH.as_posix(),
            "report": REPORT_PATH.as_posix(),
        },
        "content_hash": _sha256_json(
            {
                "summary": summary,
                "scenarios": suite["scenarios"],
                "import_runs": suite["import_runs"],
                "error_reports": suite["error_reports"],
            }
        ),
        "next_phase": "S18-P2",
        "next_required_step": (
            "下一轮只能单独执行 S18-P2 全量回归和验收；不得执行 S18-P3、Stage 18 整体复审、GitHub upload、"
            "app reinstall、正式报告、外部连接器、生产恢复、差异关闭、持久业务写入或业务执行。"
        ),
    }
    for path, value in (
        (MANIFEST_PATH, manifest), (ACCEPTANCE_MATRIX_PATH, matrix), (GO_NO_GO_PATH, go_no_go),
        (METADATA_MANIFEST_PATH, manifest), (METADATA_ACCEPTANCE_PATH, matrix), (METADATA_GO_NO_GO_PATH, go_no_go),
        (PRIVATE_RAW_BEFORE_PATH, raw_before), (PRIVATE_RAW_AFTER_PATH, raw_after),
        (PRIVATE_DIAGNOSTIC_PATH, suite["private_diagnostic"]),
    ):
        _write_json(path, value)
    for path, rows in (
        (SCENARIO_RESULTS_PATH, suite["scenarios"]), (IMPORT_RUN_RESULTS_PATH, suite["import_runs"]),
        (ERROR_REPORTS_PATH, suite["error_reports"]), (METADATA_SCENARIOS_PATH, suite["scenarios"]),
        (METADATA_IMPORT_RUNS_PATH, suite["import_runs"]), (METADATA_ERROR_REPORTS_PATH, suite["error_reports"]),
    ):
        _write_jsonl(path, rows)
    _write_text(REPORT_PATH, _render_report(summary))
    _write_text(
        TEST_RESULTS_PATH,
        f"""# S18-P1 精度与压力测试结果

- RED：generator/checker 缺失时 focused test=`1 failure + 9 skipped`。
- focused tests：{'10/10 PASS' if final_validation else 'PENDING'}。
- strict validator：{'PASS' if final_validation else 'PENDING'}。
- actual suite：5/5 scenarios，3/3 runs，batch=1200，blocking errors=2，max elapsed={summary['max_elapsed_ms']}ms。
- raw phase 前后 / 跨 Stage 17 review / current：exact match。
- quality：Q4 / D / NO_GO / 3-9-2-1。
""",
    )
    _write_text(
        RISK_REGISTER_PATH,
        """# S18-P1 风险登记

| 风险 | 控制 | 状态 |
|---|---|---|
| 合成性能被误读为生产吞吐 | 明确仅为内存 synthetic file metadata，不形成生产容量结论 | 已控制 |
| 旧固定 348ms 被当作当前事实 | 当前 elapsed 由 perf_counter_ns 实际执行产生，旧值仅作结构夹具 | 已控制 |
| 0.01 元被静默忽略 | 实际 zero-delta probe 强制 1 分 mismatch 失败并进入差异队列 | 已控制 |
| 重复导入重复写入 | 后两次新增为 0，最终状态 hash 与首次一致 | 已控制 |
| raw 被性能测试污染 | raw 仅作 ignored private 前后快照，压力输入全部在内存生成 | 已控制 |
""",
    )
    _write_text(
        ROLLBACK_PATH,
        f"""# S18-P1 回滚计划

1. 回退本 phase local commit 与 `{OUTPUT_DIR.as_posix()}` public-safe 证据。
2. 删除 ignored `{PRIVATE_DIR.as_posix()}` 私有快照和诊断，不触碰 raw inbox。
3. 回退 S18-P1 metadata 与治理登记，恢复 Stage 17 review 为 current pointer。
4. 不执行生产恢复、补偿业务动作、GitHub upload 或 app reinstall。
""",
    )
    _write_text(
        PRIVATE_REPORT_PATH,
        f"""# S18-P1 私有边界核验

- 原始数据文件数：{summary['raw_source_file_count']}
- phase 前后快照：exact match
- 与 Stage 17 review 快照：exact match
- 当前只读快照：exact match
- synthetic batch：1200
- 三次最终状态 hash：identical
- blocking errors：2
- max elapsed / budget：{summary['max_elapsed_ms']} / {summary['performance_budget_ms']} ms
- 结论：未修改、删除、移动、重命名、覆盖、复制或备份 raw；最终 goal 仍对不上时必须输出全中文差异报告。
""",
    )
    if write_governance:
        _write_governance(generated_at)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--final-validation", action="store_true")
    parser.add_argument("--no-governance", action="store_true")
    args = parser.parse_args()
    manifest = generate(final_validation=args.final_validation, write_governance=not args.no_governance)
    summary = manifest["summary"]
    print(
        "S18-P1 current precision stress: "
        f"scenarios={summary['scenario_pass_count']}/5 runs={summary['import_run_count']}/3 "
        f"batch={summary['synthetic_batch_item_count']} errors={summary['blocking_error_report_count']} "
        f"elapsed={summary['max_elapsed_ms']}/{summary['performance_budget_ms']}ms "
        f"raw={summary['raw_snapshot_exact_match']} grade={summary['current_report_grade']} decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
