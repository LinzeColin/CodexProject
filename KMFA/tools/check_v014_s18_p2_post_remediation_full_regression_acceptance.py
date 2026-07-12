#!/usr/bin/env python3
"""Validate current KMFA v0.1.4 S18-P2 full-regression evidence."""

from __future__ import annotations

import argparse
import csv
import functools
import json
import re
import subprocess
from hashlib import sha256
from pathlib import Path
from typing import Any

from KMFA.tools import v014_s18_p2_post_remediation_full_regression_acceptance as phase


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


def _walk(value: Any) -> list[tuple[str, Any]]:
    rows: list[tuple[str, Any]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            rows.append((str(key), child))
            rows.extend(_walk(child))
    elif isinstance(value, list):
        for child in value:
            rows.extend(_walk(child))
    return rows


def _git_ignored(path: Path) -> bool:
    return subprocess.run(["git", "check-ignore", "-q", path.as_posix()], check=False).returncode == 0


def _git_tracked(path: Path) -> bool:
    return subprocess.run(
        ["git", "ls-files", "--error-unmatch", path.as_posix()], capture_output=True, check=False
    ).returncode == 0


def _public_files() -> tuple[Path, ...]:
    return (
        phase.MANIFEST_PATH,
        phase.CHECK_RESULTS_PATH,
        phase.STAGE_EVIDENCE_PATH,
        phase.HTML_AUDIT_CSV_PATH,
        phase.HTML_AUDIT_SUMMARY_PATH,
        phase.ACCEPTANCE_MATRIX_PATH,
        phase.GO_NO_GO_PATH,
        phase.REPORT_PATH,
        phase.HTML_AUDIT_RECORD_PATH,
        phase.GO_NO_GO_RECORD_PATH,
        phase.TEST_RESULTS_PATH,
        phase.RISK_REGISTER_PATH,
        phase.ROLLBACK_PATH,
        phase.METADATA_MANIFEST_PATH,
        phase.METADATA_CHECK_RESULTS_PATH,
        phase.METADATA_STAGE_EVIDENCE_PATH,
        phase.METADATA_HTML_AUDIT_SUMMARY_PATH,
        phase.METADATA_ACCEPTANCE_PATH,
        phase.METADATA_GO_NO_GO_PATH,
    )


def _scan_public_file(path: Path, errors: list[str]) -> None:
    _require(path.is_file(), f"missing public evidence: {path}", errors)
    if not path.is_file():
        return
    _require(path.suffix.lower() not in FORBIDDEN_PUBLIC_SUFFIXES, f"forbidden suffix: {path}", errors)
    text = path.read_text(encoding="utf-8-sig")
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
    if path.suffix == ".csv":
        rows = list(csv.DictReader(text.splitlines()))
        _require(bool(rows), f"empty public CSV: {path}", errors)


def _validate_public(errors: list[str]) -> dict[str, Any]:
    for path in _public_files():
        _scan_public_file(path, errors)
    if not phase.MANIFEST_PATH.is_file():
        return {}
    manifest = _read_json(phase.MANIFEST_PATH)
    summary = manifest.get("summary", {})
    checks = _read_jsonl(phase.CHECK_RESULTS_PATH)
    stage_evidence = _read_jsonl(phase.STAGE_EVIDENCE_PATH)
    html_audit = _read_json(phase.HTML_AUDIT_SUMMARY_PATH)
    acceptance = _read_json(phase.ACCEPTANCE_MATRIX_PATH)
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
    _require(manifest.get("historical_s18_p2_structural_baseline_validated") is True, "historical baseline missing", errors)
    _require(manifest.get("historical_s18_p2_dynamic_state_authoritative") is False, "historical dynamic state active", errors)
    _require(manifest.get("phase_boundaries") == phase._phase_boundaries(), "phase boundary drift", errors)
    _require(manifest.get("public_repo_safety") == phase._public_repo_safety(), "public safety drift", errors)

    expected_summary = {
        "check_category_count": 5,
        "executed_check_count": 5,
        "check_pass_count": 4,
        "safe_blocked_check_count": 1,
        "command_failure_count": 0,
        "no_omission_check_passed": True,
        "zero_delta_check_passed": True,
        "schema_check_passed": True,
        "lineage_check_ran": True,
        "lineage_full_check_complete": False,
        "ui_check_passed": True,
        "stage_evidence_count": 18,
        "stage_review_validated_count": 17,
        "stage_in_progress_count": 1,
        "stage_upload_evidence_ref_count": 0,
        "html_audit_file_count": 6,
        "html_audit_row_count": 54,
        "html_audit_pass_count": 54,
        "html_audit_warn_count": 0,
        "html_audit_fail_count": 0,
        "raw_source_file_count": 5,
        "raw_snapshot_exact_match": True,
        "raw_cross_phase_snapshot_exact_match": True,
        "tracked_forbidden_suffix_count": 0,
        "tracked_private_runtime_path_count": 0,
        "open_final_difference_accepted_count": 3,
        "nonzero_delta_reconciliation_count": 9,
        "zero_delta_reconciliation_count": 2,
        "incomplete_reconciliation_count": 1,
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "s18_p1_performed": True,
        "s18_p2_performed": True,
        "s18_p3_performed": False,
        "stage18_review_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "decision": "NO_GO",
    }
    for key, expected in expected_summary.items():
        _require(summary.get(key) == expected, f"summary {key} drift", errors)

    try:
        phase.validate_regression_bundle(
            {
                "summary": summary,
                "checks": checks,
                "stage_evidence": stage_evidence,
                "html_audit": html_audit,
                "go_no_go": go_no_go,
            }
        )
    except (KeyError, TypeError, ValueError) as exc:
        errors.append(f"bundle validation failed: {exc}")

    _require(html_audit == manifest.get("html_human_flow_audit"), "HTML audit mirror drift", errors)
    _require(acceptance == manifest.get("acceptance_matrix"), "acceptance mirror drift", errors)
    _require(acceptance.get("check_count") == 21, "acceptance count drift", errors)
    _require(acceptance.get("check_pass_count") == 21 and acceptance.get("check_fail_count") == 0, "acceptance failed", errors)
    _require(go_no_go == manifest.get("go_no_go"), "go/no-go mirror drift", errors)
    _require(manifest.get("next_phase") == "S18-P3", "next phase drift", errors)

    for path, expected in (
        (phase.METADATA_MANIFEST_PATH, manifest),
        (phase.METADATA_CHECK_RESULTS_PATH, checks),
        (phase.METADATA_STAGE_EVIDENCE_PATH, stage_evidence),
        (phase.METADATA_HTML_AUDIT_SUMMARY_PATH, html_audit),
        (phase.METADATA_ACCEPTANCE_PATH, acceptance),
        (phase.METADATA_GO_NO_GO_PATH, go_no_go),
    ):
        actual = _read_jsonl(path) if path.suffix == ".jsonl" else _read_json(path)
        _require(actual == expected, f"metadata mirror drift: {path}", errors)

    for row in stage_evidence[:17]:
        refs = row.get("evidence_refs", [])
        _require(len(refs) == 1 and Path(refs[0]).is_file(), f"stage evidence ref missing: {row.get('stage_id')}", errors)
        if len(refs) == 1 and Path(refs[0]).is_file():
            _require(
                row.get("public_manifest_sha256") == sha256(Path(refs[0]).read_bytes()).hexdigest(),
                f"stage manifest hash drift: {row.get('stage_id')}",
                errors,
            )
    s18_refs = stage_evidence[-1].get("evidence_refs", []) if stage_evidence else []
    _require(all(Path(ref).is_file() for ref in s18_refs), "current S18 evidence ref missing", errors)
    return manifest


def _validate_dependencies(errors: list[str]) -> None:
    try:
        dependency = phase._s18_p1_dependency()
        _require(dependency.get("phase_id") == phase.s18_p1.PHASE_ID, "S18-P1 dependency drift", errors)
        historical = phase._historical_baseline()
        _require(historical.get("dynamic_state_authoritative") is False, "historical S18-P2 active", errors)
        contract = phase._taskpack_contract()
        _require(contract.get("roadmap_phase_id") == "S18-P2", "taskpack route drift", errors)
    except Exception as exc:
        errors.append(f"dependency validation failed: {exc}")


def _expected_parameters() -> dict[str, str]:
    return {
        "PARAM-KMFA-1810": "5;5;4;1;0;0;0",
        "PARAM-KMFA-1811": "18;17;1;6;54;54;0;0",
        "PARAM-KMFA-1812": "5;false;3;9;2;1;true;false;false;false;false;false;false;Q4;D;NO_GO",
    }


def _validate_governance(manifest: dict[str, Any], errors: list[str]) -> None:
    for path in (phase.DEVELOPMENT_EVENTS_PATH, phase.STAGE_STATUS_PATH, phase.TASK_STATUS_PATH):
        rows = [row for row in _read_jsonl(path) if row.get("phase_id") == phase.PHASE_ID]
        _require(len(rows) == 1, f"governance JSONL row count drift: {path}", errors)
        if rows:
            _require(rows[0].get("status") == phase.STATUS, f"governance status drift: {path}", errors)
    events = [
        row for row in _read_jsonl(phase.DEVELOPMENT_EVENTS_PATH) if row.get("phase_id") == phase.PHASE_ID
    ]
    if events:
        _require(events[0].get("files_changed") == phase._phase_public_files(), "event file list drift", errors)
        _require(events[0].get("check_category_count") == 5, "event check count drift", errors)
        _require(events[0].get("stage_evidence_count") == 18, "event stage count drift", errors)

    formula_text = Path("KMFA/docs/governance/formula_registry.yaml").read_text(encoding="utf-8")
    _require(phase.FORMULA_ID in formula_text, "formula missing", errors)
    for token in (
        "executed_check_count == 5",
        "command_failure_count == 0",
        "zero_delta_check_passed == true",
        "lineage_full_check_complete == false",
        "stage_evidence_count == 18",
        "stage_review_validated_count == 17",
        "html_audit_fail_count == 0",
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
        for token in (
            phase.PHASE_ID,
            "下一步只能执行 S18-P3",
            "不得执行 Stage 18 整体复审",
            "不得执行 GitHub upload",
        ):
            _require(token in handoff, f"HANDOFF token missing: {token}", errors)
        agents = Path("KMFA/AGENTS.md").read_text(encoding="utf-8")
        _require(phase.PHASE_ID in agents and "S18-P3" in agents, "AGENTS scope drift", errors)

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
        (Path("KMFA/功能清单.md"), "S18-P2 修补后全量回归和验收"),
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
    prior = _read_json(phase.s18_p1.PRIVATE_RAW_AFTER_PATH)
    helper = phase.s18_p1.s17_review.p1.s16_review.p1.s15_review.p1.s14_review.p1.s13_review.p1.s12_review.p1.s11_project
    current = helper._raw_snapshot("validate_v014_s18_p2_post_remediation_full_regression_acceptance")
    normalize = helper._normalize_raw
    _require(normalize(before) == normalize(after), "raw before/after mismatch", errors)
    _require(normalize(before) == normalize(prior) == normalize(current), "raw cross-phase mismatch", errors)
    _require(before.get("file_count") == 5, "raw file count drift", errors)
    report = phase.PRIVATE_REPORT_PATH.read_text(encoding="utf-8")
    for token in (
        "phase 前后快照：exact match",
        "与 S18-P1 快照：exact match",
        "五类命令：全部执行",
        "未修改、删除、移动、重命名、覆盖、复制或备份 raw",
        "全中文差异报告",
    ):
        _require(token in report, f"private report token missing: {token}", errors)


@functools.lru_cache(maxsize=8)
def validate_v014_s18_p2_post_remediation_full_regression_acceptance(
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
        _require(validation.get("five_regression_commands") == "PASS", "regression commands not final", errors)
        _require(validation.get("governance_and_safety_scans") == "PASS", "safety scans not final", errors)
    if errors:
        raise ValidationError("; ".join(errors))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate current KMFA S18-P2 full-regression evidence")
    parser.add_argument("--require-private-evidence", action="store_true")
    parser.add_argument("--require-final-evidence", action="store_true")
    args = parser.parse_args()
    manifest = validate_v014_s18_p2_post_remediation_full_regression_acceptance(
        require_private_evidence=args.require_private_evidence,
        require_final_evidence=args.require_final_evidence,
    )
    summary = manifest["summary"]
    print(
        "S18-P2 strict PASS: "
        f"checks={summary['executed_check_count']}/5 stages={summary['stage_evidence_count']}/18 "
        f"html={summary['html_audit_pass_count']}/{summary['html_audit_row_count']} "
        f"lineage_full={summary['lineage_full_check_complete']} raw={summary['raw_snapshot_exact_match']} "
        f"grade={summary['current_report_grade']} decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
