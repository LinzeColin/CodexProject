#!/usr/bin/env python3
"""Validate current KMFA v0.1.4 Stage 17 overall-review evidence."""

from __future__ import annotations

import argparse
import csv
import functools
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from KMFA.tools import v014_s17_post_remediation_stage_review as review
from KMFA.tools.check_v014_s17_p1_post_remediation_access_security import (
    validate_v014_s17_p1_post_remediation_access_security,
)
from KMFA.tools.check_v014_s17_p2_post_remediation_notification import (
    validate_v014_s17_p2_post_remediation_notification,
)
from KMFA.tools.check_v014_s17_p3_post_remediation_operations_sop import (
    validate_v014_s17_p3_post_remediation_operations_sop,
)
from KMFA.tools.check_v014_s17_stage_review import validate_v014_s17_stage_review as validate_historical_review


FORBIDDEN_PUBLIC_SUFFIXES = {".zip", ".xlsx", ".xls", ".pdf", ".db", ".sqlite"}
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
FORBIDDEN_PUBLIC_KEYS = {
    "raw_path_private",
    "raw_filename_private",
    "member_name_private",
    "sheet_name_private",
    "preview_rows_private",
    "raw_value",
    "normalized_value",
    "amount_cents",
    "amount_yuan",
    "payment_account",
    "bank_account_number",
    "contract_number",
    "invoice_number",
    "source_sha256",
    "backup_sha256",
    "restored_sha256",
}
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\b(?:sk|ghp|github_pat)_[A-Za-z0-9_=-]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"(?i)\b(password|secret|token)\s*[:=]\s*['\"]?[A-Za-z0-9_./+=-]{16,}"),
)


class ValidationError(Exception):
    pass


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValidationError(f"missing JSON: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValidationError(f"expected JSON object: {path}")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise ValidationError(f"missing JSONL: {path}")
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _git_ignored(path: Path) -> bool:
    return subprocess.run(
        ["git", "check-ignore", "-q", str(path)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode == 0


def _git_tracked(path: Path) -> bool:
    return subprocess.run(
        ["git", "ls-files", "--error-unmatch", str(path)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode == 0


def _walk(value: Any, key: str = "") -> list[tuple[str, Any]]:
    rows = [(key, value)]
    if isinstance(value, dict):
        for child_key, child in value.items():
            rows.extend(_walk(child, str(child_key)))
    elif isinstance(value, list):
        for child in value:
            rows.extend(_walk(child, key))
    return rows


def _public_paths() -> tuple[Path, ...]:
    return (
        review.SUMMARY_PATH,
        review.MANIFEST_PATH,
        review.PHASE_RESULTS_PATH,
        review.CONTRACT_MATRIX_PATH,
        review.MATRIX_PATH,
        review.GO_NO_GO_PATH,
        review.REPORT_PATH,
        review.TEST_RESULTS_PATH,
        review.RISK_REGISTER_PATH,
        review.ROLLBACK_PATH,
        review.METADATA_SUMMARY_PATH,
        review.METADATA_MANIFEST_PATH,
        review.METADATA_PHASE_RESULTS_PATH,
        review.METADATA_CONTRACT_MATRIX_PATH,
        review.METADATA_MATRIX_PATH,
        review.METADATA_GO_NO_GO_PATH,
        review.p1.MANIFEST_PATH,
        review.p1.AUDIT_CONTRACT_PATH,
        review.p2.MANIFEST_PATH,
        review.p2.OUTBOX_PATH,
        review.p3.MANIFEST_PATH,
        review.p3.RUNBOOK_PATH,
        review.p3.KNOWLEDGE_INDEX_PATH,
    )


def _scan_public(path: Path, errors: list[str]) -> None:
    _require(path.is_file(), f"public evidence missing: {path}", errors)
    if not path.is_file():
        return
    _require(path.suffix.lower() not in FORBIDDEN_PUBLIC_SUFFIXES, f"forbidden suffix: {path}", errors)
    data = path.read_bytes()
    _require(b"\x00" not in data, f"binary public evidence: {path}", errors)
    text = data.decode("utf-8")
    for token in FORBIDDEN_PUBLIC_TEXT:
        _require(token not in text, f"forbidden public text in {path}: {token}", errors)
    for pattern in SECRET_PATTERNS:
        _require(pattern.search(text) is None, f"secret-like text in {path}", errors)
    if path.suffix in {".json", ".jsonl"}:
        payloads = [json.loads(line) for line in text.splitlines() if line.strip()] if path.suffix == ".jsonl" else [json.loads(text)]
        for payload in payloads:
            for key, value in _walk(payload):
                _require(key not in FORBIDDEN_PUBLIC_KEYS, f"forbidden key in {path}: {key}", errors)
                if isinstance(value, float):
                    errors.append(f"public float value in {path}: {key}")


def _expected_summary() -> dict[str, Any]:
    return {
        "phase_results": {"S17-P1": "PASS", "S17-P2": "PASS", "S17-P3": "PASS"},
        "phase_count": 3,
        "phase_pass_count": 3,
        "phase_focused_test_count": 30,
        "phase_focused_test_pass_count": 30,
        "phase_strict_validator_count": 3,
        "phase_strict_validator_pass_count": 3,
        "historical_stage17_review_validated": True,
        "review_finding_count": 11,
        "fixed_review_finding_count": 7,
        "passed_review_finding_count": 4,
        "open_review_finding_count": 0,
        "canonical_role_count": 4,
        "audit_action_type_count": 5,
        "notification_recipient_role_match_count": 3,
        "notification_outbox_audit_contract_match_count": 3,
        "runbook_owner_role_match_count": 4,
        "knowledge_owner_role_match_count": 2,
        "runbook_audit_mapping_match_count": 4,
        "notification_delivery_scope_match_count": 1,
        "cross_phase_contract_mismatch_count": 0,
        "role_count": 4,
        "notification_rule_count": 3,
        "metadata_outbox_log_count": 3,
        "real_notification_delivery_count": 0,
        "full_report_body_count": 0,
        "operation_runbook_count": 4,
        "knowledge_item_count": 2,
        "error_drill_scenario_count": 2,
        "backup_restore_drill_count": 1,
        "production_restore_count": 0,
        "raw_copy_or_backup_count": 0,
        "external_service_call_count": 0,
        "persistent_business_write_count": 0,
        "business_execution_count": 0,
        "formal_report_count": 0,
        "raw_source_file_count": 5,
        "raw_snapshot_exact_match": True,
        "raw_cross_phase_snapshot_exact_match": True,
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "open_final_difference_accepted_count": 3,
        "nonzero_delta_reconciliation_count": 9,
        "zero_delta_reconciliation_count": 2,
        "incomplete_reconciliation_count": 1,
        **review._review_boundaries(),
    }


def _validate_phase_results(errors: list[str]) -> None:
    rows = _read_jsonl(review.PHASE_RESULTS_PATH)
    by_phase = {row.get("phase_id"): row for row in rows}
    expected_counts = {"S17-P1": 9, "S17-P2": 10, "S17-P3": 11}
    _require(len(rows) == 3 and set(by_phase) == set(expected_counts), "phase result set drift", errors)
    for phase_id, expected_count in expected_counts.items():
        row = by_phase.get(phase_id, {})
        _require(row.get("focused_test_count") == expected_count, f"focused test count drift: {phase_id}", errors)
        _require(row.get("focused_test_status") == "PASS", f"focused test status drift: {phase_id}", errors)
        _require(row.get("strict_validator_count") == 1, f"strict validator count drift: {phase_id}", errors)
        _require(row.get("strict_validator_status") == "PASS", f"strict validator status drift: {phase_id}", errors)
        _require(Path(str(row.get("manifest_ref"))).is_file(), f"phase manifest missing: {phase_id}", errors)


def _validate_contract_matrix(errors: list[str]) -> None:
    rows = _read_jsonl(review.CONTRACT_MATRIX_PATH)
    expected = {
        "notification_recipient_roles": 3,
        "notification_outbox_audit_contract": 3,
        "runbook_owner_roles": 4,
        "knowledge_owner_roles": 2,
        "runbook_audit_actions": 4,
        "notification_delivery_scope": 1,
    }
    by_type = {row.get("check_type"): row for row in rows}
    _require(len(rows) == 6 and set(by_type) == set(expected), "contract matrix set drift", errors)
    for check_type, expected_count in expected.items():
        row = by_type.get(check_type, {})
        _require(row.get("expected_count") == expected_count, f"contract expected drift: {check_type}", errors)
        _require(row.get("matched_count") == expected_count, f"contract match drift: {check_type}", errors)
        _require(row.get("mismatch_count") == 0, f"contract mismatch: {check_type}", errors)
        _require(row.get("status") == "PASS", f"contract status drift: {check_type}", errors)


def _validate_public(errors: list[str]) -> dict[str, Any]:
    for path in _public_paths():
        _scan_public(path, errors)
    if not review.MANIFEST_PATH.is_file():
        return {}
    manifest = _read_json(review.MANIFEST_PATH)
    summary = _read_json(review.SUMMARY_PATH)
    matrix = _read_json(review.MATRIX_PATH)
    go_no_go = _read_json(review.GO_NO_GO_PATH)
    for key, expected in (
        ("phase_id", review.PHASE_ID),
        ("roadmap_phase_id", review.ROADMAP_PHASE_ID),
        ("review_scope", review.REVIEW_SCOPE),
        ("task_id", review.TASK_ID),
        ("acceptance_id", review.ACCEPTANCE_ID),
        ("version", review.VERSION),
        ("status", review.STATUS),
        ("decision", review.DECISION),
        ("formula_id", review.FORMULA_ID),
        ("parameter_ids", list(review.PARAMETER_IDS)),
        ("model_registry_key", review.MODEL_REGISTRY_KEY),
    ):
        _require(manifest.get(key) == expected, f"manifest {key} drift", errors)
    _require(manifest.get("summary") == summary, "summary mirror drift", errors)
    _require(manifest.get("acceptance_matrix") == matrix, "matrix mirror drift", errors)
    _require(manifest.get("go_no_go") == go_no_go, "go/no-go mirror drift", errors)
    for key, expected in _expected_summary().items():
        _require(summary.get(key) == expected, f"summary {key} drift", errors)
    findings = manifest.get("review_findings", [])
    _require(len(findings) == 11 and len({row.get("finding_id") for row in findings}) == 11, "finding set drift", errors)
    _require(sum(row.get("status") == "fixed" for row in findings) == 7, "fixed finding count drift", errors)
    _require(sum(row.get("status") == "passed" for row in findings) == 4, "passed finding count drift", errors)
    _require(all(row.get("status") != "open" for row in findings), "open finding remains", errors)
    _require(manifest.get("historical_stage17_review_validated") is True, "historical review missing", errors)
    _require(manifest.get("historical_stage17_dynamic_state_is_authoritative") is False, "historical review active", errors)
    _require(manifest.get("quality_gate") == review._quality_gate(), "quality gate drift", errors)
    _require(manifest.get("review_boundaries") == review._review_boundaries(), "review boundary drift", errors)
    _require(manifest.get("public_repo_safety") == review._public_safety(), "public safety drift", errors)
    _require(manifest.get("repo_tracking_scan", {}).get("status") == "PASS", "repo tracking scan failed", errors)
    _require(matrix.get("check_count") == 16 and matrix.get("check_pass_count") == 16 and matrix.get("check_fail_count") == 0, "acceptance matrix failed", errors)
    _require(go_no_go.get("stage17_review_validated") is True, "review gate missing", errors)
    for key, value in go_no_go.items():
        if key.endswith("_allowed") or key.endswith("_allowed_in_this_run"):
            _require(value is False, f"go/no-go boundary opened: {key}", errors)
    _require(manifest.get("next_phase") == "S18-P1", "next phase drift", errors)
    for path, expected in (
        (review.METADATA_SUMMARY_PATH, summary),
        (review.METADATA_MANIFEST_PATH, manifest),
        (review.METADATA_MATRIX_PATH, matrix),
        (review.METADATA_GO_NO_GO_PATH, go_no_go),
    ):
        _require(_read_json(path) == expected, f"metadata mirror drift: {path}", errors)
    _require(_read_jsonl(review.METADATA_PHASE_RESULTS_PATH) == _read_jsonl(review.PHASE_RESULTS_PATH), "phase metadata mirror drift", errors)
    _require(_read_jsonl(review.METADATA_CONTRACT_MATRIX_PATH) == _read_jsonl(review.CONTRACT_MATRIX_PATH), "contract metadata mirror drift", errors)
    _validate_phase_results(errors)
    _validate_contract_matrix(errors)
    return manifest


def _validate_dependencies(errors: list[str]) -> None:
    p1_manifest = validate_v014_s17_p1_post_remediation_access_security(
        require_private_evidence=True,
        require_final_evidence=True,
    )
    p2_manifest = validate_v014_s17_p2_post_remediation_notification(
        require_private_evidence=True,
        require_final_evidence=True,
    )
    p3_manifest = validate_v014_s17_p3_post_remediation_operations_sop(
        require_private_evidence=True,
        require_final_evidence=True,
    )
    _require(p1_manifest.get("phase_id") == review.p1.PHASE_ID, "current S17-P1 identity drift", errors)
    _require(p2_manifest.get("phase_id") == review.p2.PHASE_ID, "current S17-P2 identity drift", errors)
    _require(p3_manifest.get("phase_id") == review.p3.PHASE_ID, "current S17-P3 identity drift", errors)
    _require(p1_manifest.get("next_phase") == "S17-P2", "S17-P1 route drift", errors)
    _require(p2_manifest.get("next_phase") == "S17-P3", "S17-P2 route drift", errors)
    _require(p3_manifest.get("next_phase") == "S17_STAGE_REVIEW", "S17-P3 route drift", errors)
    historical = validate_historical_review()
    _require(historical.get("phase_id") == "S17_STAGE_REVIEW", "historical review fixture drift", errors)
    _require(historical.get("phase_results") == {"S17-P1": "PASS", "S17-P2": "PASS", "S17-P3": "PASS"}, "historical phase result drift", errors)


def _expected_parameters() -> dict[str, str]:
    boundaries = ["true" if value else "false" for value in review._review_boundaries().values()]
    return {
        "PARAM-KMFA-1804": "3;3;30;30;3;3;11;7;4;0",
        "PARAM-KMFA-1805": "4;5;3;3;4;2;4;1;0;4;3;3;4;2;2;1;0;0;0;0",
        "PARAM-KMFA-1806": ";".join(["5", "true", "true", "3", "9", "2", "1", *boundaries, "Q4", "D", "NO_GO"]),
    }


def _validate_governance(manifest: dict[str, Any], errors: list[str]) -> None:
    for path in (review.DEVELOPMENT_EVENTS_PATH, review.STAGE_STATUS_PATH, review.TASK_STATUS_PATH):
        rows = [row for row in _read_jsonl(path) if row.get("phase_id") == review.PHASE_ID]
        _require(len(rows) == 1, f"governance JSONL row count drift: {path}", errors)
        if rows:
            _require(rows[0].get("status") == review.STATUS, f"governance status drift: {path}", errors)
    events = [row for row in _read_jsonl(review.DEVELOPMENT_EVENTS_PATH) if row.get("phase_id") == review.PHASE_ID]
    if events:
        _require(events[0].get("files_changed") == review._phase_public_files(), "event file list drift", errors)
        _require(events[0].get("fixed_review_finding_count") == 7, "event finding count drift", errors)
        _require(events[0].get("open_review_finding_count") == 0, "event open finding drift", errors)

    formula_text = Path("KMFA/docs/governance/formula_registry.yaml").read_text(encoding="utf-8")
    _require(review.FORMULA_ID in formula_text, "formula missing", errors)
    for token in (
        "phase_pass_count == 3",
        "phase_focused_test_pass_count == 30",
        "phase_strict_validator_pass_count == 3",
        "fixed_review_finding_count == 7",
        "open_review_finding_count == 0",
        "cross_phase_contract_mismatch_count == 0",
        "raw_exact == true",
        "current_grade == D",
        "decision == NO_GO",
    ):
        _require(token in formula_text, f"formula control missing: {token}", errors)
    for path in (Path("KMFA/docs/governance/model_registry.yaml"), Path("KMFA/metadata/model_registry.yaml")):
        text = path.read_text(encoding="utf-8")
        _require(review.MODEL_REGISTRY_KEY in text, f"model missing: {path}", errors)
        _require(review.FORMULA_ID in text, f"formula ref missing: {path}", errors)
        for parameter_id in review.PARAMETER_IDS:
            _require(parameter_id in text, f"parameter ref missing: {path}:{parameter_id}", errors)
    with Path("KMFA/docs/governance/parameter_registry.csv").open(encoding="utf-8", newline="") as handle:
        parameters = {row["parameter_id"]: row for row in csv.DictReader(handle)}
    for parameter_id, expected in _expected_parameters().items():
        row = parameters.get(parameter_id, {})
        _require(row.get("formula_id") == review.FORMULA_ID, f"parameter formula drift: {parameter_id}", errors)
        for field in ("default_value", "initial_or_prior_value", "active_value", "extracted_value"):
            _require(row.get(field) == expected, f"parameter drift: {parameter_id}:{field}", errors)
        _require(row.get("status") == "active", f"parameter status drift: {parameter_id}", errors)

    version_matrix = Path("KMFA/docs/governance/VERSION_MATRIX.yaml").read_text(encoding="utf-8")
    _require(review.MODEL_REGISTRY_KEY in version_matrix and review.VERSION in version_matrix, "VERSION_MATRIX profile missing", errors)
    current = f'current_phase: "{review.PHASE_ID}"' in version_matrix
    if current:
        _require(Path("KMFA/VERSION").read_text(encoding="utf-8").strip() == review.VERSION, "VERSION drift", errors)
        handoff = Path("KMFA/HANDOFF.md").read_text(encoding="utf-8")
        for token in (review.PHASE_ID, "下一步只能执行 S18-P1", "不得执行 S18-P2", "不得执行 GitHub upload"):
            _require(token in handoff, f"HANDOFF token missing: {token}", errors)
        agents = Path("KMFA/AGENTS.md").read_text(encoding="utf-8")
        _require(review.PHASE_ID in agents and "S18-P1" in agents, "AGENTS scope drift", errors)
    trace = Path("KMFA/docs/governance/TRACEABILITY_MATRIX.csv").read_text(encoding="utf-8")
    delivery = Path("KMFA/docs/governance/delivery_tasks.yaml").read_text(encoding="utf-8")
    assurance = Path("KMFA/docs/governance/ASSURANCE_STATUS.yaml").read_text(encoding="utf-8")
    _require(review.TASK_ID in trace and review.ACCEPTANCE_ID in trace, "traceability missing", errors)
    _require(review.TASK_ID in delivery and review.ACCEPTANCE_ID in delivery, "delivery task missing", errors)
    manifest_ref = review.MANIFEST_PATH.as_posix()
    report_ref = review.REPORT_PATH.as_posix()
    for path in (
        Path("KMFA/docs/governance/formula_registry.yaml"),
        Path("KMFA/docs/governance/TRACEABILITY_MATRIX.csv"),
        Path("KMFA/docs/governance/delivery_tasks.yaml"),
        Path("KMFA/docs/governance/DEVELOPMENT_LEDGER.md"),
        Path("KMFA/docs/governance/MODEL_SPEC.md"),
        Path("KMFA/开发记录.md"),
        Path("KMFA/docs/governance/parameter_registry.csv"),
    ):
        text = path.read_text(encoding="utf-8")
        _require(manifest_ref in text or report_ref in text, f"review evidence ref missing: {path}", errors)
    if current:
        _require(f'snapshot_event_time: "{manifest["generated_at"]}"' in assurance, "assurance time drift", errors)
    _require(review.FORMULA_ID in assurance, "assurance formula missing", errors)
    for parameter_id in review.PARAMETER_IDS:
        _require(parameter_id in assurance, f"assurance parameter missing: {parameter_id}", errors)
    for path, token in (
        (Path("KMFA/CHANGELOG.md"), review.VERSION),
        (Path("KMFA/docs/governance/DEVELOPMENT_LEDGER.md"), review.PHASE_ID),
        (Path("KMFA/docs/governance/MODEL_SPEC.md"), review.FORMULA_ID),
        (Path("KMFA/docs/governance/OWNER_STATUS.md"), review.PHASE_ID),
        (Path("KMFA/docs/governance/STATUS.md"), review.PHASE_ID),
        (Path("KMFA/功能清单.md"), "Stage 17 修补后整体复审"),
        (Path("KMFA/开发记录.md"), review.TASK_ID),
        (Path("KMFA/模型参数文件.md"), review.FORMULA_ID),
    ):
        _require(token in path.read_text(encoding="utf-8"), f"governance token missing: {path}", errors)


def _validate_private(errors: list[str]) -> None:
    paths = (review.PRIVATE_RAW_BEFORE_PATH, review.PRIVATE_RAW_AFTER_PATH, review.PRIVATE_REVIEW_REPORT_PATH)
    for path in paths:
        _require(path.is_file(), f"private evidence missing: {path}", errors)
        _require(_git_ignored(path), f"private evidence not ignored: {path}", errors)
        _require(not _git_tracked(path), f"private evidence tracked: {path}", errors)
    if not all(path.is_file() for path in paths):
        return
    before = _read_json(review.PRIVATE_RAW_BEFORE_PATH)
    after = _read_json(review.PRIVATE_RAW_AFTER_PATH)
    prior = _read_json(review.p3.PRIVATE_RAW_AFTER_PATH)
    helper = review.p1.s16_review.p1.s15_review.p1.s14_review.p1.s13_review.p1.s12_review.p1.s11_project
    current = helper._raw_snapshot("validate_v014_s17_post_remediation_stage_review")
    normalize = helper._normalize_raw
    _require(normalize(before) == normalize(after), "raw before/after mismatch", errors)
    _require(normalize(before) == normalize(prior) == normalize(current), "raw cross-phase mismatch", errors)
    _require(before.get("file_count") == 5, "raw file count drift", errors)
    scan = review.p1._repo_tracking_scan()
    _require(scan.get("tracked_forbidden_suffix_count") == 0, "current tracked forbidden suffix found", errors)
    _require(scan.get("tracked_private_runtime_path_count") == 0, "current tracked private runtime found", errors)
    report = review.PRIVATE_REVIEW_REPORT_PATH.read_text(encoding="utf-8")
    for token in (
        "review 前后快照：exact match",
        "与 S17-P3 快照：exact match",
        "phase tests/validators：30/30 / 3/3 PASS",
        "findings：7 fixed / 4 passed / 0 open",
        "全中文最终差异报告",
    ):
        _require(token in report, f"private report token missing: {token}", errors)


@functools.lru_cache(maxsize=8)
def validate_v014_s17_post_remediation_stage_review(
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
        for key in (
            "phase_focused_tests",
            "phase_strict_validators",
            "review_tests",
            "review_strict_validator",
            "cross_phase_contracts",
            "raw_alignment",
            "governance_and_safety_scans",
        ):
            _require(validation.get(key) == "PASS", f"final validation drift: {key}", errors)
    if errors:
        raise ValidationError("; ".join(errors))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-private-evidence", action="store_true")
    parser.add_argument("--require-final-evidence", action="store_true")
    args = parser.parse_args()
    manifest = validate_v014_s17_post_remediation_stage_review(
        require_private_evidence=args.require_private_evidence,
        require_final_evidence=args.require_final_evidence,
    )
    summary = manifest["summary"]
    print(
        "Stage 17 strict review PASS: "
        f"phases={summary['phase_pass_count']}/3 tests={summary['phase_focused_test_pass_count']}/30 "
        f"validators={summary['phase_strict_validator_pass_count']}/3 findings={summary['fixed_review_finding_count']}/0 "
        f"contracts={summary['cross_phase_contract_mismatch_count']} mismatch raw={summary['raw_snapshot_exact_match']} "
        f"grade={summary['current_report_grade']} decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
