#!/usr/bin/env python3
"""Validate the KMFA v0.1.4 Stage 9 post-remediation review."""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from KMFA.tools import check_v014_global_residual_difference_queue_replay_or_authoritative_exclusion as global_check
from KMFA.tools import check_v014_remaining_eleven_residual_difference_source_trace_or_final_acceptance as residual_check
from KMFA.tools import v014_remaining_eleven_residual_difference_source_trace_or_final_acceptance as residual_phase
from KMFA.tools.check_no_float_money import scan_paths
from KMFA.tools.check_v014_s09_p1_project_cost_fact_layer import validate_v014_s09_p1_project_cost_fact_layer
from KMFA.tools.check_v014_s09_p2_margin_cash_margin import validate_v014_s09_p2_margin_cash_margin
from KMFA.tools.check_v014_s09_p3_scope_reconciliation import validate_v014_s09_p3_scope_reconciliation
from KMFA.tools.check_v014_s09_stage_review import validate_v014_s09_stage_review
from KMFA.tools import v014_s09_post_remediation_stage_review as phase


FORBIDDEN_PUBLIC_SUFFIXES = {".zip", ".xls", ".xlsx", ".pdf", ".db", ".sqlite", ".sqlite3"}
RAW_INBOX_TOKEN = "KMFA" + "_MetaData"
LOCAL_DOWNLOADS_PATTERN = re.compile(r"/Users/[^\s\"'`]+/Downloads/[^\s\"'`]+")
SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)(?:password|passwd|api[_-]?key|access[_-]?token|client[_-]?secret)\s*[:=]\s*[\"'][^\"'\r\n]{8,}[\"']"),
)
FORBIDDEN_PUBLIC_KEYS = {
    "raw_value",
    "normalized_value",
    "original_value",
    "business_value",
    "row_value",
    "cell_value",
    "sheet_name",
    "member_name",
    "original_filename",
    "file_hash",
    "field_key",
    "field_label",
    "source_header_text",
    "project_name_plaintext",
    "customer_name_plaintext",
    "authoritative_value_cents",
    "system_value_cents",
}


class ValidationError(Exception):
    pass


def _require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValidationError(f"missing JSON: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValidationError(f"{path} must contain an object")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValidationError(f"{path} must contain objects")
            rows.append(value)
    return rows


def _walk_forbidden_keys(value: Any, errors: list[str], location: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_PUBLIC_KEYS:
                errors.append(f"forbidden public key {key!r} at {location}")
            _walk_forbidden_keys(child, errors, f"{location}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _walk_forbidden_keys(child, errors, f"{location}[{index}]")


def _check_public_file(path: Path, errors: list[str]) -> None:
    _require(path.is_file(), f"missing public artifact: {path}", errors)
    if not path.is_file():
        return
    _require(path.suffix.lower() not in FORBIDDEN_PUBLIC_SUFFIXES, f"forbidden public suffix: {path}", errors)
    text = path.read_text(encoding="utf-8", errors="ignore")
    _require(RAW_INBOX_TOKEN not in text, f"raw inbox token leaked in {path}", errors)
    _require(LOCAL_DOWNLOADS_PATTERN.search(text) is None, f"local Downloads path leaked in {path}", errors)
    for pattern in SECRET_PATTERNS:
        _require(pattern.search(text) is None, f"secret-like value in {path}", errors)
    if path.suffix.lower() == ".json":
        _walk_forbidden_keys(json.loads(text), errors)


def _git_check_ignore(path: Path) -> bool:
    result = subprocess.run(["git", "check-ignore", "-q", path.as_posix()], check=False)
    return result.returncode == 0


def _git_tracked(path: Path) -> bool:
    result = subprocess.run(["git", "ls-files", "--error-unmatch", path.as_posix()], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    return result.returncode == 0


def _command_passes(command: list[str]) -> bool:
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=False)
    return result.returncode == 0


def _validate_public_artifacts(errors: list[str]) -> dict[str, Any]:
    public_paths = [
        phase.SUMMARY_PATH,
        phase.MANIFEST_PATH,
        phase.GO_NO_GO_PATH,
        phase.MATRIX_PATH,
        phase.REPORT_PATH,
        phase.TEST_RESULTS_PATH,
        phase.RISK_REGISTER_PATH,
        phase.ROLLBACK_PATH,
        phase.METADATA_SUMMARY_PATH,
        phase.METADATA_MANIFEST_PATH,
        phase.METADATA_GO_NO_GO_PATH,
        phase.METADATA_MATRIX_PATH,
    ]
    for path in public_paths:
        _check_public_file(path, errors)

    summary = _read_json(phase.SUMMARY_PATH)
    manifest = _read_json(phase.MANIFEST_PATH)
    go_no_go = _read_json(phase.GO_NO_GO_PATH)
    matrix = _read_json(phase.MATRIX_PATH)
    _require(summary == _read_json(phase.METADATA_SUMMARY_PATH), "summary mirror drift", errors)
    _require(manifest == _read_json(phase.METADATA_MANIFEST_PATH), "manifest mirror drift", errors)
    _require(go_no_go == _read_json(phase.METADATA_GO_NO_GO_PATH), "go/no-go mirror drift", errors)
    _require(matrix == _read_json(phase.METADATA_MATRIX_PATH), "matrix mirror drift", errors)

    expected = {
        "stage_id": "S09",
        "phase_id": phase.PHASE_ID,
        "task_id": phase.TASK_ID,
        "acceptance_id": phase.ACCEPTANCE_ID,
        "review_scope": phase.REVIEW_SCOPE,
        "status": phase.STATUS,
        "decision": "NO_GO",
        "cost_category_count": 9,
        "cost_component_materialization_count": 8,
        "authority_system_overwrite_allowed_count": 0,
        "reconciliation_record_count": 12,
        "human_readable_reconciliation_count": 12,
        "queue_closed_or_excluded_count": 69,
        "open_final_difference_accepted_count": 3,
        "nonzero_delta_reconciliation_count": 9,
        "zero_delta_reconciliation_count": 2,
        "incomplete_reconciliation_count": 1,
        "forced_zero_materialization_count": 0,
        "dependency_validation_count": 8,
        "dependency_validation_pass_count": 8,
        "stage_status_normalized_record_count": 62,
        "stage_status_normalized_event_record_count": 8,
        "stage_status_normalized_stage_phase_record_count": 54,
        "fixed_review_finding_count": 11,
        "open_review_finding_count": 0,
        "full_regression_test_count": 1200,
        "full_regression_failure_count": 0,
        "full_regression_elapsed_seconds": "9556.914",
        "full_regression_result": "OK",
        "raw_source_file_count": 5,
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "release_permission": "blocked",
    }
    for key, value in expected.items():
        _require(summary.get(key) == value, f"summary {key} mismatch", errors)
    for key in (
        "travel_category_covered",
        "interest_category_covered",
        "original_stage_review_validated",
        "raw_snapshot_exact_match",
        "raw_cross_phase_snapshot_exact_match",
    ):
        _require(summary.get(key) is True, f"summary {key} must be true", errors)
    for key in (
        "s10_p1_performed",
        "github_upload_performed",
        "app_reinstall_performed",
        "business_execution_performed",
        "raw_business_data_committed",
        "private_runtime_committed",
    ):
        _require(summary.get(key) is False, f"summary {key} must be false", errors)
    _require(summary.get("phase_results") == {"S09-P1": "PASS", "S09-P2": "PASS", "S09-P3": "PASS"}, "phase results mismatch", errors)
    _require(matrix.get("check_count") == 24, "matrix count mismatch", errors)
    _require(matrix.get("check_pass_count") == 24, "matrix pass count mismatch", errors)
    _require(matrix.get("check_fail_count") == 0, "matrix contains failures", errors)
    _require(all(row.get("passed") is True for row in matrix.get("checks", [])), "matrix row failed", errors)
    _require(go_no_go.get("decision") == "NO_GO", "go/no-go decision mismatch", errors)
    _require(go_no_go.get("open_final_difference_accepted_count") == 3, "go/no-go open count mismatch", errors)

    findings = manifest.get("review_findings", [])
    _require(len(findings) == 11, "review finding count mismatch", errors)
    _require(all(item.get("status") == "fixed" for item in findings), "review finding remains open", errors)
    dependencies = manifest.get("dependency_results", [])
    _require(len(dependencies) == 8, "dependency result count mismatch", errors)
    _require(all(item.get("result") == "PASS" and item.get("exit_code") == 0 for item in dependencies), "dependency result failed", errors)
    safety = manifest.get("public_repo_safety", {})
    _require(safety.get("aggregate_only") is True, "public evidence must be aggregate-only", errors)
    _require(all(value is False for key, value in safety.items() if key != "aggregate_only"), "public safety flag changed", errors)
    return summary


def _validate_dependencies(errors: list[str], require_private_evidence: bool) -> None:
    p1 = validate_v014_s09_p1_project_cost_fact_layer()
    p2 = validate_v014_s09_p2_margin_cash_margin()
    p3 = validate_v014_s09_p3_scope_reconciliation()
    original = validate_v014_s09_stage_review()
    _require(p1.get("project_cost_fact_layer_summary", {}).get("cost_category_count") == 9, "S09-P1 category count changed", errors)
    _require(p2.get("authority_system_overwrite_allowed_count") == 0, "S09-P2 overwrite boundary changed", errors)
    _require(p3.get("reconciliation_record_count") == 12, "S09-P3 reconciliation count changed", errors)
    _require(original.get("stage_id") == "S09", "original Stage 9 review failed", errors)

    global_summary = global_check._validate_public_artifacts()
    residual_summary = residual_check._validate_public_artifacts()
    _require(global_summary.get("global_residual_queue_record_count") == 72, "global residual count changed", errors)
    _require(residual_summary.get("queue_closed_or_excluded_count") == 69, "residual closed count changed", errors)
    # Earlier private diagnostics bind to their phase-time source hashes. Later
    # phases may legitimately refresh those ignored sources, so this review
    # validates their immutable public summaries and owns a fresh private raw
    # before/after/prior/current comparison below.

    _require(not scan_paths([Path("KMFA")]), "full KMFA no-float scan failed", errors)
    _require(
        _command_passes([sys.executable, "KMFA/tools/no_omission_check.py"]),
        "no-omission check failed",
        errors,
    )


def _validate_stage_status_and_governance(errors: list[str]) -> None:
    stage_rows = _read_jsonl(phase.STAGE_STATUS_PATH)
    required = phase.REQUIRED_STAGE_STATUS_FIELDS
    _require(all(required <= set(row) for row in stage_rows), "stage status required fields remain incomplete", errors)
    normalized = [row for row in stage_rows if row.get("governance_normalized_by") == phase.NORMALIZATION_MARKER]
    _require(len(normalized) == 62, "normalized stage status count mismatch", errors)
    _require(sum(row.get("record_type") == "v014_phase_event" for row in normalized) == 8, "normalized event count mismatch", errors)
    _require(any(row.get("phase_id") == phase.PHASE_ID for row in stage_rows), "current stage review status missing", errors)

    events = _read_jsonl(phase.DEVELOPMENT_EVENTS_PATH)
    tasks = _read_jsonl(phase.TASK_STATUS_PATH)
    phase_events = [row for row in events if row.get("phase_id") == phase.PHASE_ID]
    _require(len(phase_events) == 1, "development event must be unique", errors)
    if phase_events:
        _require(phase_events[0].get("fixed_review_finding_count") == 11, "event finding count mismatch", errors)
        _require(phase_events[0].get("open_review_finding_count") == 0, "event open finding count mismatch", errors)
    _require(any(row.get("phase_id") == phase.PHASE_ID for row in tasks), "task status missing", errors)

    formula_text = Path("KMFA/docs/governance/formula_registry.yaml").read_text(encoding="utf-8")
    parameter_path = Path("KMFA/docs/governance/parameter_registry.csv")
    parameter_text = parameter_path.read_text(encoding="utf-8")
    model_text = Path("KMFA/docs/governance/model_registry.yaml").read_text(encoding="utf-8")
    _require(phase.FORMULA_ID in formula_text, "formula governance record missing", errors)
    _require("fixed_review_finding_count == 11" in formula_text, "formula finding count drift", errors)
    for parameter_id in phase.PARAMETER_IDS:
        _require(parameter_id in parameter_text, f"parameter governance record missing: {parameter_id}", errors)
    with parameter_path.open(encoding="utf-8", newline="") as handle:
        parameter_rows = {row["parameter_id"]: row for row in csv.DictReader(handle)}
    finding_parameter = parameter_rows.get("PARAM-KMFA-1693", {})
    expected_count_tuple = "9;8;0;12;12;69;3;9;2;1;62;8;11;0;5;NO_GO"
    for field in ("default_value", "initial_or_prior_value", "active_value", "extracted_value"):
        _require(finding_parameter.get(field) == expected_count_tuple, f"parameter finding count drift: {field}", errors)
    _require(phase.MODEL_REGISTRY_KEY in model_text, "phase model governance record missing", errors)


def _validate_private_evidence(errors: list[str]) -> None:
    private_paths = [phase.PRIVATE_RAW_BEFORE_PATH, phase.PRIVATE_RAW_AFTER_PATH, phase.PRIVATE_REVIEW_REPORT_PATH]
    for path in private_paths:
        _require(path.is_file(), f"private evidence missing: {path}", errors)
        _require(_git_check_ignore(path), f"private evidence is not ignored: {path}", errors)
        _require(not _git_tracked(path), f"private evidence is tracked: {path}", errors)
    if any(not path.is_file() for path in private_paths):
        return

    before = _read_json(phase.PRIVATE_RAW_BEFORE_PATH)
    after = _read_json(phase.PRIVATE_RAW_AFTER_PATH)
    prior = _read_json(phase.SOURCE_RESIDUAL_RAW_AFTER)
    current = residual_phase.prior_phase._raw_snapshot("validate_s09_post_remediation_review")
    normalize = residual_phase._normalize_snapshot
    _require(normalize(before) == normalize(after), "review raw before/after mismatch", errors)
    _require(normalize(before) == normalize(prior), "cross-phase raw snapshot mismatch", errors)
    _require(normalize(after) == normalize(current), "current raw snapshot mismatch", errors)
    _require(before.get("file_count") == 5 and after.get("file_count") == 5, "raw file count changed", errors)

    report = phase.PRIVATE_REVIEW_REPORT_PATH.read_text(encoding="utf-8")
    for token in ("原因、依据、责任与状态", "九条非零", "三条现金", "不推断、不平均、不补零"):
        _require(token in report, f"private Chinese report missing token: {token}", errors)


def validate_v014_s09_post_remediation_stage_review(require_private_evidence: bool = False) -> dict[str, Any]:
    errors: list[str] = []
    summary = _validate_public_artifacts(errors)
    _validate_dependencies(errors, require_private_evidence)
    _validate_stage_status_and_governance(errors)
    if require_private_evidence:
        _validate_private_evidence(errors)
    if errors:
        raise ValidationError("; ".join(errors))
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-private-evidence", action="store_true")
    args = parser.parse_args()
    try:
        summary = validate_v014_s09_post_remediation_stage_review(args.require_private_evidence)
    except (ValidationError, ValueError, KeyError, RuntimeError) as exc:
        print(f"FAIL: {exc}")
        return 1
    print(
        "PASS: Stage 9 post-remediation review "
        f"fixed={summary['fixed_review_finding_count']} open={summary['open_review_finding_count']} "
        f"closed_or_excluded={summary['queue_closed_or_excluded_count']} "
        f"open_final={summary['open_final_difference_accepted_count']} decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
