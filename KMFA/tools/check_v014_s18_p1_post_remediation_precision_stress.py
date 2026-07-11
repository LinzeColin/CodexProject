#!/usr/bin/env python3
"""Validate current KMFA v0.1.4 S18-P1 precision and stress evidence."""

from __future__ import annotations

import argparse
import csv
import functools
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from KMFA.tools import v014_s18_p1_post_remediation_precision_stress as phase


FORBIDDEN_PUBLIC_SUFFIXES = {".zip", ".xlsx", ".xls", ".xlsm", ".pdf", ".db", ".sqlite", ".sqlite3"}
FORBIDDEN_PUBLIC_KEYS = {
    "raw_path_private",
    "raw_filename_private",
    "member_name_private",
    "sheet_name_private",
    "preview_rows_private",
    "raw_value",
    "normalized_value",
    "payment_account",
    "bank_account_number",
    "contract_number",
    "invoice_number",
    "source_sha256",
}
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\b(?:sk|ghp|github_pat)_[A-Za-z0-9_=-]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"(?i)\b(password|secret|token)\s*[:=]\s*['\"]?[A-Za-z0-9_./+=-]{16,}"),
)


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
        raise ValidationError(f"expected object: {path}")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise ValidationError(f"missing JSONL: {path}")
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not all(isinstance(row, dict) for row in rows):
        raise ValidationError(f"expected object rows: {path}")
    return rows


def _walk(value: Any, key: str = "") -> list[tuple[str, Any]]:
    rows: list[tuple[str, Any]] = []
    if isinstance(value, dict):
        for child_key, child_value in value.items():
            rows.append((str(child_key), child_value))
            rows.extend(_walk(child_value, str(child_key)))
    elif isinstance(value, list):
        for child in value:
            rows.extend(_walk(child, key))
    return rows


def _git_ignored(path: Path) -> bool:
    result = subprocess.run(["git", "check-ignore", "-q", path.as_posix()], check=False)
    return result.returncode == 0


def _git_tracked(path: Path) -> bool:
    result = subprocess.run(["git", "ls-files", "--error-unmatch", path.as_posix()], capture_output=True, check=False)
    return result.returncode == 0


def _public_files() -> tuple[Path, ...]:
    return (
        phase.MANIFEST_PATH,
        phase.SCENARIO_RESULTS_PATH,
        phase.IMPORT_RUN_RESULTS_PATH,
        phase.ERROR_REPORTS_PATH,
        phase.ACCEPTANCE_MATRIX_PATH,
        phase.GO_NO_GO_PATH,
        phase.REPORT_PATH,
        phase.TEST_RESULTS_PATH,
        phase.RISK_REGISTER_PATH,
        phase.ROLLBACK_PATH,
        phase.METADATA_MANIFEST_PATH,
        phase.METADATA_SCENARIOS_PATH,
        phase.METADATA_IMPORT_RUNS_PATH,
        phase.METADATA_ERROR_REPORTS_PATH,
        phase.METADATA_ACCEPTANCE_PATH,
        phase.METADATA_GO_NO_GO_PATH,
    )


def _scan_public_file(path: Path, errors: list[str]) -> None:
    _require(path.is_file(), f"missing public evidence: {path}", errors)
    if not path.is_file():
        return
    _require(path.suffix.lower() not in FORBIDDEN_PUBLIC_SUFFIXES, f"forbidden suffix: {path}", errors)
    text = path.read_text(encoding="utf-8")
    for token in phase.FORBIDDEN_PUBLIC_TEXT:
        _require(token not in text, f"forbidden public token in {path}: {token}", errors)
    for pattern in SECRET_PATTERNS:
        _require(pattern.search(text) is None, f"secret-like text in {path}", errors)
    if path.suffix in {".json", ".jsonl"}:
        payloads = [json.loads(line) for line in text.splitlines() if line.strip()] if path.suffix == ".jsonl" else [json.loads(text)]
        for payload in payloads:
            for key, value in _walk(payload):
                _require(key not in FORBIDDEN_PUBLIC_KEYS, f"forbidden public key in {path}: {key}", errors)
                _require(not isinstance(value, float), f"public float in {path}: {key}", errors)


def _validate_public(errors: list[str]) -> dict[str, Any]:
    for path in _public_files():
        _scan_public_file(path, errors)
    if not phase.MANIFEST_PATH.is_file():
        return {}
    manifest = _read_json(phase.MANIFEST_PATH)
    summary = manifest.get("summary", {})
    scenarios = _read_jsonl(phase.SCENARIO_RESULTS_PATH)
    runs = _read_jsonl(phase.IMPORT_RUN_RESULTS_PATH)
    error_reports = _read_jsonl(phase.ERROR_REPORTS_PATH)
    matrix = _read_json(phase.ACCEPTANCE_MATRIX_PATH)
    go_no_go = _read_json(phase.GO_NO_GO_PATH)

    for key, expected in (
        ("phase_id", phase.PHASE_ID),
        ("roadmap_phase_id", phase.ROADMAP_PHASE_ID),
        ("task_id", phase.TASK_ID),
        ("acceptance_id", phase.ACCEPTANCE_ID),
        ("version", phase.VERSION),
        ("status", phase.STATUS),
        ("decision", phase.DECISION),
        ("formula_id", phase.FORMULA_ID),
        ("parameter_ids", list(phase.PARAMETER_IDS)),
        ("model_registry_key", phase.MODEL_REGISTRY_KEY),
    ):
        _require(manifest.get(key) == expected, f"manifest {key} drift", errors)
    _require(manifest.get("historical_s18_p1_structural_baseline_validated") is True, "historical baseline missing", errors)
    _require(manifest.get("historical_s18_p1_dynamic_state_authoritative") is False, "historical dynamic state active", errors)
    _require(manifest.get("phase_boundaries") == phase._phase_boundaries(), "phase boundary drift", errors)
    _require(manifest.get("public_repo_safety") == phase._public_repo_safety(), "public safety drift", errors)

    expected = {
        "scenario_count": 5,
        "scenario_pass_count": 5,
        "amount_case_count": 9,
        "amount_case_pass_count": 9,
        "amount_rejection_case_count": 9,
        "amount_rejection_pass_count": 9,
        "repository_no_float_scan_passed": True,
        "zero_delta_exact_passed": True,
        "one_cent_mismatch_rejected": True,
        "one_cent_mismatch_count": 1,
        "import_run_count": 3,
        "unique_final_state_hash_count": 1,
        "synthetic_batch_item_count": 1200,
        "valid_synthetic_record_count": 1198,
        "first_run_inserted_record_count": 1198,
        "later_run_duplicate_record_count": 2396,
        "blocking_error_report_count": 2,
        "performance_budget_ms": phase.PERFORMANCE_BUDGET_MS,
        "raw_source_file_count": 5,
        "raw_snapshot_exact_match": True,
        "raw_cross_phase_snapshot_exact_match": True,
        "tracked_forbidden_suffix_count": 0,
        "tracked_private_runtime_path_count": 0,
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
        "decision": "NO_GO",
    }
    for key, value in expected.items():
        _require(summary.get(key) == value, f"summary {key} drift", errors)
    _require(isinstance(summary.get("max_elapsed_ms"), int), "elapsed must be integer ms", errors)
    _require(1 <= summary.get("max_elapsed_ms", 0) <= phase.PERFORMANCE_BUDGET_MS, "performance budget failed", errors)
    _require(summary.get("max_elapsed_ms") == max(row.get("elapsed_ms", 0) for row in runs), "elapsed summary drift", errors)

    try:
        phase.validate_precision_stress_suite(
            {"summary": summary, "scenarios": scenarios, "import_runs": runs, "error_reports": error_reports}
        )
    except (KeyError, TypeError, ValueError) as exc:
        errors.append(f"suite validation failed: {exc}")
    _require(matrix == manifest.get("acceptance_matrix"), "acceptance mirror drift", errors)
    _require(matrix.get("check_count") == 19, "acceptance count drift", errors)
    _require(matrix.get("check_pass_count") == 19 and matrix.get("check_fail_count") == 0, "acceptance failed", errors)
    _require(go_no_go == manifest.get("go_no_go"), "go/no-go mirror drift", errors)
    _require(go_no_go.get("decision") == "NO_GO", "decision drift", errors)
    for key, value in go_no_go.items():
        if key.endswith("_allowed") or key.endswith("_allowed_in_this_run"):
            _require(value is False, f"downstream gate opened: {key}", errors)
    _require(manifest.get("next_phase") == "S18-P2", "next phase drift", errors)

    for path, expected_value in (
        (phase.METADATA_MANIFEST_PATH, manifest),
        (phase.METADATA_SCENARIOS_PATH, scenarios),
        (phase.METADATA_IMPORT_RUNS_PATH, runs),
        (phase.METADATA_ERROR_REPORTS_PATH, error_reports),
        (phase.METADATA_ACCEPTANCE_PATH, matrix),
        (phase.METADATA_GO_NO_GO_PATH, go_no_go),
    ):
        actual = _read_jsonl(path) if path.suffix == ".jsonl" else _read_json(path)
        _require(actual == expected_value, f"metadata mirror drift: {path}", errors)
    return manifest


def _validate_dependencies(errors: list[str]) -> None:
    try:
        dependency = phase._stage17_dependency()
        _require(dependency.get("phase_id") == phase.s17_review.PHASE_ID, "Stage 17 dependency drift", errors)
        historical = phase._historical_baseline()
        _require(historical.get("dynamic_state_authoritative") is False, "historical baseline active", errors)
        contract = phase._taskpack_contract()
        _require(contract.get("roadmap_phase_id") == "S18-P1", "taskpack route drift", errors)
    except Exception as exc:  # validation boundary
        errors.append(f"dependency validation failed: {exc}")


def _expected_parameters() -> dict[str, str]:
    return {
        "PARAM-KMFA-1807": "5;5;9;9;9;9;2;2;true;true;3;1",
        "PARAM-KMFA-1808": "1200;1198;2;3;1;1198;2396;1500",
        "PARAM-KMFA-1809": "5;true;true;3;9;2;1;true;false;false;false;false;false;false;Q4;D;NO_GO",
    }


def _validate_governance(manifest: dict[str, Any], errors: list[str]) -> None:
    for path in (phase.DEVELOPMENT_EVENTS_PATH, phase.STAGE_STATUS_PATH, phase.TASK_STATUS_PATH):
        rows = [row for row in _read_jsonl(path) if row.get("phase_id") == phase.PHASE_ID]
        _require(len(rows) == 1, f"governance JSONL row count drift: {path}", errors)
        if rows:
            _require(rows[0].get("status") == phase.STATUS, f"governance status drift: {path}", errors)
    events = [row for row in _read_jsonl(phase.DEVELOPMENT_EVENTS_PATH) if row.get("phase_id") == phase.PHASE_ID]
    if events:
        _require(events[0].get("files_changed") == phase._phase_public_files(), "event file list drift", errors)
        _require(events[0].get("scenario_pass_count") == 5, "event scenario count drift", errors)

    formula_text = Path("KMFA/docs/governance/formula_registry.yaml").read_text(encoding="utf-8")
    _require(phase.FORMULA_ID in formula_text, "formula missing", errors)
    for token in (
        "scenario_pass_count == 5",
        "amount_case_pass_count == 9",
        "amount_rejection_pass_count == 9",
        "one_cent_mismatch_rejected == true",
        "import_run_count == 3",
        "unique_final_state_hash_count == 1",
        "synthetic_batch_item_count == 1200",
        "blocking_error_report_count == 2",
        "max_elapsed_ms <= performance_budget_ms",
        "raw_exact == true",
        "current_grade == D",
        "decision == NO_GO",
    ):
        _require(token in formula_text, f"formula control missing: {token}", errors)

    for path in (Path("KMFA/docs/governance/model_registry.yaml"), Path("KMFA/metadata/model_registry.yaml")):
        text = path.read_text(encoding="utf-8")
        _require(phase.MODEL_REGISTRY_KEY in text, f"model profile missing: {path}", errors)
        _require(phase.FORMULA_ID in text, f"model formula missing: {path}", errors)
        for parameter_id in phase.PARAMETER_IDS:
            _require(parameter_id in text, f"model parameter missing: {path}:{parameter_id}", errors)

    with Path("KMFA/docs/governance/parameter_registry.csv").open(encoding="utf-8", newline="") as handle:
        parameters = {row["parameter_id"]: row for row in csv.DictReader(handle)}
    for parameter_id, expected in _expected_parameters().items():
        row = parameters.get(parameter_id, {})
        _require(row.get("formula_id") == phase.FORMULA_ID, f"parameter formula drift: {parameter_id}", errors)
        for field in ("default_value", "initial_or_prior_value", "active_value", "extracted_value"):
            _require(row.get(field) == expected, f"parameter value drift: {parameter_id}:{field}", errors)
        _require(row.get("status") == "active", f"parameter status drift: {parameter_id}", errors)

    version_matrix = Path("KMFA/docs/governance/VERSION_MATRIX.yaml").read_text(encoding="utf-8")
    _require(phase.MODEL_REGISTRY_KEY in version_matrix and phase.VERSION in version_matrix, "VERSION_MATRIX profile missing", errors)
    current = f'current_phase: "{phase.PHASE_ID}"' in version_matrix
    if current:
        _require(Path("KMFA/VERSION").read_text(encoding="utf-8").strip() == phase.VERSION, "VERSION drift", errors)
        handoff = Path("KMFA/HANDOFF.md").read_text(encoding="utf-8")
        for token in (phase.PHASE_ID, "下一步只能执行 S18-P2", "不得执行 S18-P3", "不得执行 Stage 18 整体复审", "不得执行 GitHub upload"):
            _require(token in handoff, f"HANDOFF token missing: {token}", errors)
        agents = Path("KMFA/AGENTS.md").read_text(encoding="utf-8")
        _require(phase.PHASE_ID in agents and "S18-P2" in agents, "AGENTS scope drift", errors)

    trace = Path("KMFA/docs/governance/TRACEABILITY_MATRIX.csv").read_text(encoding="utf-8")
    delivery = Path("KMFA/docs/governance/delivery_tasks.yaml").read_text(encoding="utf-8")
    assurance = phase.ASSURANCE_STATUS_PATH.read_text(encoding="utf-8")
    _require(phase.TASK_ID in trace and phase.ACCEPTANCE_ID in trace, "traceability missing", errors)
    _require(phase.TASK_ID in delivery and phase.ACCEPTANCE_ID in delivery, "delivery task missing", errors)
    _require(phase.FORMULA_ID in assurance, "assurance formula missing", errors)
    if current:
        _require(f'snapshot_event_time: "{manifest["generated_at"]}"' in assurance, "assurance time drift", errors)
    for parameter_id in phase.PARAMETER_IDS:
        _require(parameter_id in assurance, f"assurance parameter missing: {parameter_id}", errors)
    for path, token in (
        (Path("KMFA/CHANGELOG.md"), phase.VERSION),
        (Path("KMFA/README.md"), phase.PHASE_ID),
        (Path("KMFA/docs/governance/DEVELOPMENT_LEDGER.md"), phase.PHASE_ID),
        (Path("KMFA/docs/governance/MODEL_SPEC.md"), phase.FORMULA_ID),
        (Path("KMFA/docs/governance/OWNER_STATUS.md"), phase.PHASE_ID),
        (Path("KMFA/docs/governance/STATUS.md"), phase.PHASE_ID),
        (Path("KMFA/功能清单.md"), "S18-P1 修补后精度与压力测试"),
        (Path("KMFA/开发记录.md"), phase.TASK_ID),
        (Path("KMFA/模型参数文件.md"), phase.FORMULA_ID),
    ):
        _require(token in path.read_text(encoding="utf-8"), f"governance token missing: {path}", errors)


def _validate_private(errors: list[str]) -> None:
    paths = (
        phase.PRIVATE_RAW_BEFORE_PATH,
        phase.PRIVATE_RAW_AFTER_PATH,
        phase.PRIVATE_DIAGNOSTIC_PATH,
        phase.PRIVATE_REPORT_PATH,
    )
    for path in paths:
        _require(path.is_file(), f"private evidence missing: {path}", errors)
        _require(_git_ignored(path), f"private evidence not ignored: {path}", errors)
        _require(not _git_tracked(path), f"private evidence tracked: {path}", errors)
    if not all(path.is_file() for path in paths):
        return
    before = _read_json(phase.PRIVATE_RAW_BEFORE_PATH)
    after = _read_json(phase.PRIVATE_RAW_AFTER_PATH)
    prior = _read_json(phase.s17_review.PRIVATE_RAW_AFTER_PATH)
    helper = phase.s17_review.p1.s16_review.p1.s15_review.p1.s14_review.p1.s13_review.p1.s12_review.p1.s11_project
    current = helper._raw_snapshot("validate_v014_s18_p1_post_remediation_precision_stress")
    normalize = helper._normalize_raw
    _require(normalize(before) == normalize(after), "raw before/after mismatch", errors)
    _require(normalize(before) == normalize(prior) == normalize(current), "raw cross-phase mismatch", errors)
    _require(before.get("file_count") == 5, "raw file count drift", errors)
    report = phase.PRIVATE_REPORT_PATH.read_text(encoding="utf-8")
    for token in (
        "phase 前后快照：exact match",
        "与 Stage 17 review 快照：exact match",
        "三次最终状态 hash：identical",
        "未修改、删除、移动、重命名、覆盖、复制或备份 raw",
        "全中文差异报告",
    ):
        _require(token in report, f"private report token missing: {token}", errors)


@functools.lru_cache(maxsize=8)
def validate_v014_s18_p1_post_remediation_precision_stress(
    *,
    require_private_evidence: bool = False,
    require_final_evidence: bool = False,
) -> dict[str, Any]:
    errors: list[str] = []
    manifest = _validate_public(errors)
    _validate_dependencies(errors)
    if manifest:
        _validate_governance(manifest, errors)
    if require_private_evidence:
        _validate_private(errors)
    if require_final_evidence and manifest:
        validation = manifest.get("validation_summary", {})
        _require(validation.get("final_validation_recorded") is True, "final validation not recorded", errors)
        _require(validation.get("focused_tests") == "PASS", "focused tests not final", errors)
        _require(validation.get("strict_validator") == "PASS", "strict validator not final", errors)
        _require(validation.get("governance_and_safety_scans") == "PASS", "safety scans not final", errors)
    if errors:
        raise ValidationError("; ".join(errors))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-private-evidence", action="store_true")
    parser.add_argument("--require-final-evidence", action="store_true")
    args = parser.parse_args()
    manifest = validate_v014_s18_p1_post_remediation_precision_stress(
        require_private_evidence=args.require_private_evidence,
        require_final_evidence=args.require_final_evidence,
    )
    summary = manifest["summary"]
    print(
        "S18-P1 strict PASS: "
        f"scenarios={summary['scenario_pass_count']}/5 runs={summary['import_run_count']}/3 "
        f"batch={summary['synthetic_batch_item_count']} errors={summary['blocking_error_report_count']} "
        f"elapsed={summary['max_elapsed_ms']}/{summary['performance_budget_ms']}ms "
        f"raw={summary['raw_snapshot_exact_match']} grade={summary['current_report_grade']} decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
