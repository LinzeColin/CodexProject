#!/usr/bin/env python3
"""Validate KMFA v0.1.4 final overall-review evidence."""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from KMFA.tools import v014_final_overall_review as review


FORBIDDEN_PUBLIC_SUFFIXES = {".zip", ".xls", ".xlsx", ".xlsm", ".pdf", ".db", ".sqlite", ".sqlite3"}
SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(
        r"(?i)(?:password|passwd|api[_-]?key|access[_-]?token|client[_-]?secret)"
        r"\s*[:=]\s*[\"'][^\"'\r\n]{8,}[\"']"
    ),
)


class ValidationError(Exception):
    pass


def _require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _read_json(path: Path, errors: list[str]) -> dict[str, Any]:
    if not path.is_file():
        errors.append(f"missing JSON: {path}")
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"invalid JSON {path}: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"JSON must contain an object: {path}")
        return {}
    return value


def _read_jsonl(path: Path, errors: list[str]) -> list[dict[str, Any]]:
    if not path.is_file():
        errors.append(f"missing JSONL: {path}")
        return []
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"invalid JSONL {path}:{line_no}: {exc}")
            continue
        if not isinstance(value, dict):
            errors.append(f"JSONL row must be object: {path}:{line_no}")
            continue
        rows.append(value)
    return rows


def _git_check_ignore(path: Path) -> bool:
    return subprocess.run(["git", "check-ignore", "-q", path.as_posix()], check=False).returncode == 0


def _git_tracked(path: Path) -> bool:
    return subprocess.run(
        ["git", "ls-files", "--error-unmatch", path.as_posix()],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode == 0


def _check_public_file(path: Path, errors: list[str]) -> None:
    _require(path.is_file(), f"missing public artifact: {path}", errors)
    if not path.is_file():
        return
    _require(path.suffix.lower() not in FORBIDDEN_PUBLIC_SUFFIXES, f"forbidden public suffix: {path}", errors)
    text = path.read_text(encoding="utf-8", errors="ignore")
    lower = text.lower()
    for token in review.FORBIDDEN_PUBLIC_TEXT:
        _require(token.lower() not in lower, f"forbidden public text {token!r} in {path}", errors)
    for pattern in SECRET_PATTERNS:
        _require(pattern.search(text) is None, f"secret-like token in {path}: {pattern.pattern}", errors)


def _validate_public(errors: list[str]) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    public_paths = (
        review.SUMMARY_PATH,
        review.MANIFEST_PATH,
        review.STAGE_RESULTS_PATH,
        review.CONTRACT_MATRIX_PATH,
        review.ACCEPTANCE_MATRIX_PATH,
        review.GO_NO_GO_PATH,
        review.REPORT_PATH,
        review.FINDINGS_PATH,
        review.TEST_RESULTS_PATH,
        review.RISK_REGISTER_PATH,
        review.ROLLBACK_PATH,
        review.METADATA_SUMMARY_PATH,
        review.METADATA_MANIFEST_PATH,
        review.METADATA_STAGE_RESULTS_PATH,
        review.METADATA_CONTRACT_MATRIX_PATH,
        review.METADATA_ACCEPTANCE_MATRIX_PATH,
        review.METADATA_GO_NO_GO_PATH,
    )
    for path in public_paths:
        _check_public_file(path, errors)

    summary = _read_json(review.SUMMARY_PATH, errors)
    manifest = _read_json(review.MANIFEST_PATH, errors)
    stage_results = _read_jsonl(review.STAGE_RESULTS_PATH, errors)
    contracts = _read_jsonl(review.CONTRACT_MATRIX_PATH, errors)
    acceptance = _read_json(review.ACCEPTANCE_MATRIX_PATH, errors)
    go_no_go = _read_json(review.GO_NO_GO_PATH, errors)

    _require(_read_json(review.METADATA_SUMMARY_PATH, errors) == summary, "metadata summary mirror mismatch", errors)
    _require(_read_json(review.METADATA_MANIFEST_PATH, errors) == manifest, "metadata manifest mirror mismatch", errors)
    _require(_read_jsonl(review.METADATA_STAGE_RESULTS_PATH, errors) == stage_results, "metadata stage results mirror mismatch", errors)
    _require(_read_jsonl(review.METADATA_CONTRACT_MATRIX_PATH, errors) == contracts, "metadata contracts mirror mismatch", errors)
    _require(_read_json(review.METADATA_ACCEPTANCE_MATRIX_PATH, errors) == acceptance, "metadata acceptance mirror mismatch", errors)
    _require(_read_json(review.METADATA_GO_NO_GO_PATH, errors) == go_no_go, "metadata Go/No-Go mirror mismatch", errors)
    _require(manifest.get("summary") == summary, "manifest summary mismatch", errors)
    _require(manifest.get("acceptance_matrix") == acceptance, "manifest acceptance mismatch", errors)
    _require(manifest.get("go_no_go") == go_no_go, "manifest Go/No-Go mismatch", errors)
    return summary, manifest, stage_results, contracts, acceptance, go_no_go


def _validate_identity_and_results(
    summary: dict[str, Any],
    manifest: dict[str, Any],
    stage_results: list[dict[str, Any]],
    contracts: list[dict[str, Any]],
    acceptance: dict[str, Any],
    go_no_go: dict[str, Any],
    errors: list[str],
) -> None:
    _require(manifest.get("schema_version") == "kmfa.v014.final_overall_review_manifest.v1", "manifest schema drift", errors)
    _require(manifest.get("project_id") == "KMFA", "project_id drift", errors)
    _require(manifest.get("stage_id") == "S01-S18", "stage_id drift", errors)
    _require(manifest.get("phase_id") == review.PHASE_ID, "phase_id drift", errors)
    _require(manifest.get("roadmap_phase_id") == review.ROADMAP_PHASE_ID, "roadmap phase drift", errors)
    _require(manifest.get("review_scope") == review.REVIEW_SCOPE, "review scope drift", errors)
    _require(manifest.get("task_id") == review.TASK_ID, "task_id drift", errors)
    _require(manifest.get("acceptance_id") == review.ACCEPTANCE_ID, "acceptance_id drift", errors)
    _require(manifest.get("version") == review.VERSION, "version drift", errors)
    _require(manifest.get("status") == review.STATUS, "status drift", errors)
    _require(manifest.get("decision") == "NO_GO", "decision drift", errors)
    _require(manifest.get("formula_id") == review.FORMULA_ID, "formula id drift", errors)
    _require(manifest.get("parameter_ids") == list(review.PARAMETER_IDS), "parameter ids drift", errors)
    _require(manifest.get("model_registry_key") == review.MODEL_REGISTRY_KEY, "model registry key drift", errors)
    _require(manifest.get("next_phase") == review.NEXT_PHASE, "next phase drift", errors)

    _require(manifest.get("historical_overall_review_structural_baseline_validated") is True, "historical structural baseline missing", errors)
    _require(manifest.get("historical_overall_review_dynamic_state_authoritative") is False, "historical dynamic state must be non-authoritative", errors)
    _require(manifest.get("historical_overall_review_upload_state_authoritative") is False, "historical upload state must be non-authoritative", errors)
    _require(summary.get("current_stage_review_count") == 18, "current stage review count drift", errors)
    _require(summary.get("current_stage_review_pass_count") == 18, "current stage review pass count drift", errors)
    _require(summary.get("current_stage_validator_pass_count") == 18, "current stage validator pass count drift", errors)
    _require(summary.get("full_suite_test_count", 0) >= 1502, "full suite inventory shrank", errors)
    _require(summary.get("full_suite_test_pass_count") == summary.get("full_suite_test_count"), "full suite pass count drift", errors)
    _require(summary.get("review_finding_count") == 14, "review finding count drift", errors)
    _require(summary.get("fixed_review_finding_count") == 6, "fixed finding count drift", errors)
    _require(summary.get("passed_review_finding_count") == 8, "passed finding count drift", errors)
    _require(summary.get("open_review_finding_count") == 0, "open finding count must be zero", errors)
    findings = manifest.get("review_findings", [])
    _require(len(findings) == 14, "manifest finding count drift", errors)
    _require(sum(row.get("status") == "fixed" for row in findings) == 6, "manifest fixed findings drift", errors)
    _require(sum(row.get("status") == "open" for row in findings) == 0, "manifest contains open finding", errors)

    expected_stages = [f"S{i:02d}" for i in range(1, 19)]
    _require([row.get("stage_id") for row in stage_results] == expected_stages, "stage result order drift", errors)
    _require([row.get("review_kind") for row in stage_results] == ["original"] * 8 + ["post_remediation"] * 10, "current review selection drift", errors)
    _require(all(row.get("strict_validator_status") == "PASS" for row in stage_results), "stage validator result not fully PASS", errors)
    _require(all(row.get("historical_dynamic_state_authoritative") is False for row in stage_results), "historical stage state must be non-authoritative", errors)
    for stage_no, row in enumerate(stage_results, 1):
        post = stage_no >= 9
        expected_phase = (
            f"V014_S{stage_no:02d}_POST_REMEDIATION_STAGE_REVIEW"
            if post
            else f"V014_S{stage_no:02d}_STAGE_REVIEW"
        )
        _require(row.get("review_phase_id") == expected_phase, f"S{stage_no:02d} review phase drift", errors)
        ref = Path(str(row.get("manifest_ref", "")))
        stage_manifest = _read_json(ref, errors) if ref.as_posix() != "." else {}
        _require(stage_manifest.get("stage_id") == f"S{stage_no:02d}", f"S{stage_no:02d} manifest stage drift", errors)
        if post:
            _require(stage_manifest.get("phase_id") == expected_phase, f"S{stage_no:02d} manifest phase drift", errors)
        else:
            review_token = f"KMFA-V014-S{stage_no:02d}-STAGE-REVIEW-"
            _require(str(stage_manifest.get("review_id", "")).startswith(review_token), f"S{stage_no:02d} original review identity drift", errors)
            _require(stage_manifest.get("stage_review_performed") is True, f"S{stage_no:02d} original review not performed", errors)

    _require(len(contracts) >= 18, "cross-stage contract count too small", errors)
    _require(all(row.get("status") == "PASS" and row.get("mismatch_count") == 0 for row in contracts), "cross-stage contract mismatch", errors)
    _require(summary.get("cross_stage_contract_count") == len(contracts), "contract summary count drift", errors)
    _require(summary.get("cross_stage_contract_mismatch_count") == 0, "contract mismatch summary drift", errors)
    _require(acceptance.get("check_count", 0) >= 24, "acceptance check count too small", errors)
    _require(acceptance.get("check_pass_count") == acceptance.get("check_count"), "acceptance is not fully PASS", errors)
    _require(acceptance.get("check_fail_count") == 0, "acceptance contains failure", errors)

    _require(summary.get("raw_source_file_count") == 5, "raw source count drift", errors)
    _require(summary.get("raw_snapshot_exact_match") is True, "raw phase exactness failed", errors)
    _require(summary.get("raw_cross_phase_snapshot_exact_match") is True, "raw cross-phase exactness failed", errors)
    _require(summary.get("tracked_raw_filename_leak_count") == 0, "tracked raw filename leak remains", errors)
    _require([summary.get("html_audit_file_count"), summary.get("html_audit_row_count"), summary.get("html_audit_pass_count"), summary.get("html_audit_warn_count"), summary.get("html_audit_fail_count")] == [6, 54, 54, 0, 0], "HTML audit counts drift", errors)
    _require([summary.get("open_final_difference_accepted_count"), summary.get("nonzero_delta_reconciliation_count"), summary.get("zero_delta_reconciliation_count"), summary.get("incomplete_reconciliation_count")] == [3, 9, 2, 1], "difference tuple drift", errors)
    _require([summary.get("current_data_quality_grade"), summary.get("current_report_grade"), summary.get("decision")] == ["Q4", "D", "NO_GO"], "quality state drift", errors)
    _require(summary.get("lineage_full_check_complete") is False, "lineage full check must remain incomplete", errors)
    _require(summary.get("final_overall_review_performed") is True, "final overall review not recorded", errors)
    _require(summary.get("github_main_upload_ready") is True, "code upload readiness not recorded", errors)
    _require(summary.get("github_upload_performed") is False, "GitHub upload must not be performed", errors)
    _require(summary.get("app_reinstall_performed") is False, "App reinstall must not be performed", errors)
    _require(summary.get("business_execution_performed") is False, "business execution must not be performed", errors)

    _require(go_no_go.get("decision") == "NO_GO", "Go/No-Go decision drift", errors)
    _require(go_no_go.get("github_main_upload_ready") is True, "Go/No-Go code upload readiness drift", errors)
    _require(go_no_go.get("github_upload_performed") is False, "Go/No-Go upload performed drift", errors)
    _require("FINAL_OVERALL_REVIEW_PENDING" not in go_no_go.get("blocker_ids", []), "final review pending blocker not cleared", errors)
    _require("ONE_TIME_GITHUB_MAIN_UPLOAD_PENDING" in go_no_go.get("blocker_ids", []), "one-time upload pending blocker missing", errors)
    for key in (
        "app_reinstall_performed",
        "delivery_allowed",
        "official_report_release_allowed",
        "business_decision_basis_allowed",
        "persistent_business_write_allowed",
        "business_execution_allowed",
        "business_execution_performed",
        "lineage_full_check_complete",
    ):
        _require(go_no_go.get(key) is False, f"go_no_go.{key} must be false", errors)

    try:
        review.validate_review_bundle(
            {"summary": summary, "stage_results": stage_results, "contracts": contracts, "go_no_go": go_no_go}
        )
    except (KeyError, TypeError, ValueError) as exc:
        errors.append(f"review bundle validation failed: {exc}")


def _validate_private(errors: list[str]) -> None:
    for path in (
        review.PRIVATE_RAW_BEFORE_PATH,
        review.PRIVATE_RAW_AFTER_PATH,
        review.PRIVATE_DIAGNOSTIC_PATH,
        review.PRIVATE_DIFFERENCE_REPORT_PATH,
    ):
        _require(path.is_file(), f"missing private evidence: {path}", errors)
        _require(_git_check_ignore(path), f"private evidence is not ignored: {path}", errors)
        _require(not _git_tracked(path), f"private evidence is tracked: {path}", errors)
    if review.PRIVATE_RAW_BEFORE_PATH.is_file() and review.PRIVATE_RAW_AFTER_PATH.is_file():
        before = _read_json(review.PRIVATE_RAW_BEFORE_PATH, errors)
        after = _read_json(review.PRIVATE_RAW_AFTER_PATH, errors)
        _require(review.raw_helper._normalize_raw(before) == review.raw_helper._normalize_raw(after), "private raw before/after mismatch", errors)
    if review.PRIVATE_DIFFERENCE_REPORT_PATH.is_file():
        report = review.PRIVATE_DIFFERENCE_REPORT_PATH.read_text(encoding="utf-8")
        for token in ("差异报告", "三项最终接受未决", "九项非零差异", "一项未完成比较", "未关闭"):
            _require(token in report, f"private Chinese difference report missing token: {token}", errors)
    raw_root = Path("/Users/linzezhang/Downloads/KMFA_MetaData")
    raw_names = {path.name.encode("utf-8") for path in raw_root.rglob("*") if path.is_file()}
    _require(len(raw_names) == 5, "raw filename leak scan source inventory drift", errors)
    tracked = subprocess.run(
        ["git", "-c", "core.quotePath=false", "ls-files", "KMFA"],
        text=True,
        capture_output=True,
        check=True,
    ).stdout.splitlines()
    hits = [
        path
        for path_text in tracked
        if (path := Path(path_text)).is_file()
        for raw_name in raw_names
        if raw_name in path.read_bytes()
    ]
    _require(not hits, "actual raw filename remains in tracked KMFA files", errors)


def _validate_governance(summary: dict[str, Any], errors: list[str]) -> None:
    development_event: dict[str, Any] = {}
    for path in (review.DEVELOPMENT_EVENTS_PATH, review.STAGE_STATUS_PATH, review.TASK_STATUS_PATH):
        rows = _read_jsonl(path, errors)
        _require(sum(row.get("phase_id") == review.PHASE_ID for row in rows) == 1, f"governance row missing or duplicated: {path}", errors)
        if path == review.DEVELOPMENT_EVENTS_PATH:
            development_event = next((row for row in rows if row.get("phase_id") == review.PHASE_ID), {})

    changed_files = set(development_event.get("files_changed", []))
    required_remediation_files = {path.as_posix() for path in review.RAW_ALIAS_REMEDIATION_PUBLIC_FILES}
    _require(
        required_remediation_files.issubset(changed_files),
        "development event does not cover all raw-alias remediation files",
        errors,
    )
    _require(
        (review.HUMAN_DIR / "go_no_go_record_zh.md").as_posix() in changed_files,
        "development event omits final Go/No-Go record",
        errors,
    )

    _require(Path("KMFA/VERSION").read_text(encoding="utf-8").strip() == review.VERSION, "VERSION current value drift", errors)
    version_matrix = Path("KMFA/docs/governance/VERSION_MATRIX.yaml").read_text(encoding="utf-8")
    _require(f'current_phase: "{review.PHASE_ID}"' in version_matrix, "VERSION_MATRIX current phase drift", errors)
    _require(f'next_phase: "{review.NEXT_PHASE}"' in version_matrix, "VERSION_MATRIX next phase drift", errors)
    _require(f'{review.MODEL_REGISTRY_KEY}: "{review.VERSION}"' in version_matrix, "VERSION_MATRIX profile missing", errors)
    handoff = Path("KMFA/HANDOFF.md").read_text(encoding="utf-8")
    for token in (
        "下一步只能执行一次性 GitHub main upload",
        "本轮未执行 GitHub upload",
        "不得执行 App 重装",
    ):
        _require(token in handoff, f"HANDOFF token missing: {token}", errors)

    formula_text = Path("KMFA/docs/governance/formula_registry.yaml").read_text(encoding="utf-8")
    _require(review.FORMULA_ID in formula_text, "formula registry entry missing", errors)
    _require("github_main_upload_ready == true" in formula_text, "formula upload readiness gate missing", errors)
    _require("tracked_raw_filename_leak_count == 0" in formula_text, "formula raw filename safety gate missing", errors)
    with Path("KMFA/docs/governance/parameter_registry.csv").open(encoding="utf-8", newline="") as handle:
        rows = {row["parameter_id"]: row for row in csv.DictReader(handle)}
    expected_values = {
        "PARAM-KMFA-1819": f"18;18;18;{summary['full_suite_test_count']};{summary['full_suite_test_pass_count']};14;6;8;0;{summary['cross_stage_contract_count']};0;0",
        "PARAM-KMFA-1820": "5;true;true;6;54;54;0;0;3;9;2;1;Q4;D;NO_GO",
        "PARAM-KMFA-1821": "true;true;false;false;false;false;false;false;false;false;NO_GO",
    }
    for parameter_id, expected in expected_values.items():
        row = rows.get(parameter_id)
        _require(row is not None, f"parameter registry row missing: {parameter_id}", errors)
        if row is None:
            continue
        _require(row.get("formula_id") == review.FORMULA_ID, f"parameter formula drift: {parameter_id}", errors)
        _require(row.get("parameter_version") == review.VERSION, f"parameter version drift: {parameter_id}", errors)
        for field in ("default_value", "initial_or_prior_value", "active_value", "extracted_value"):
            _require(row.get(field) == expected, f"parameter value drift: {parameter_id}:{field}", errors)

    for path in (Path("KMFA/docs/governance/model_registry.yaml"), Path("KMFA/metadata/model_registry.yaml")):
        text = path.read_text(encoding="utf-8")
        _require(f"{review.MODEL_REGISTRY_KEY}:" in text, f"model registry profile missing: {path}", errors)
        _require(f'version: "{review.VERSION}"' in text, f"model registry version missing: {path}", errors)
        _require(review.FORMULA_ID in text, f"model registry formula missing: {path}", errors)
        for parameter_id in review.PARAMETER_IDS:
            _require(parameter_id in text, f"model registry parameter missing {parameter_id}: {path}", errors)

    assurance = Path("KMFA/docs/governance/ASSURANCE_STATUS.yaml").read_text(encoding="utf-8")
    _require(f"{review.MODEL_REGISTRY_KEY}:" in assurance, "ASSURANCE_STATUS profile missing", errors)
    _require("github_main_upload_ready: true" in assurance, "ASSURANCE_STATUS code upload readiness missing", errors)
    _require("github_upload_performed: false" in assurance, "ASSURANCE_STATUS upload boundary missing", errors)


def _validate_final_evidence(manifest: dict[str, Any], errors: list[str]) -> None:
    validation = manifest.get("validation_summary", {})
    _require(validation.get("final_validation_recorded") is True, "final validation not recorded", errors)
    for key in (
        "current_stage_validators",
        "full_suite",
        "focused_review_tests",
        "strict_review_validator",
        "review_findings_closed",
        "raw_alignment",
        "governance_and_safety_scans",
    ):
        _require(validation.get(key) == "PASS", f"final validation status mismatch: {key}", errors)


def _rerun_stage_validators(stage_results: list[dict[str, Any]], errors: list[str]) -> None:
    try:
        rerun = review._current_stage_review_manifests()
    except Exception as exc:  # pragma: no cover - surfaced by CLI
        errors.append(f"current Stage validator rerun failed: {exc}")
        return
    _require([row["stage_id"] for row in rerun] == [row.get("stage_id") for row in stage_results], "rerun stage identity mismatch", errors)
    _require([row["review_phase_id"] for row in rerun] == [row.get("review_phase_id") for row in stage_results], "rerun current review selection mismatch", errors)


def validate_v014_final_overall_review(
    *,
    require_private_evidence: bool = False,
    require_final_evidence: bool = False,
    rerun_stage_validators: bool = False,
) -> dict[str, Any]:
    errors: list[str] = []
    summary, manifest, stage_results, contracts, acceptance, go_no_go = _validate_public(errors)
    _validate_identity_and_results(summary, manifest, stage_results, contracts, acceptance, go_no_go, errors)
    _validate_governance(summary, errors)
    if require_private_evidence:
        _validate_private(errors)
    if require_final_evidence:
        _validate_final_evidence(manifest, errors)
    if rerun_stage_validators:
        _rerun_stage_validators(stage_results, errors)
    if errors:
        raise ValidationError("; ".join(errors))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.4 final overall-review evidence")
    parser.add_argument("--require-private-evidence", action="store_true")
    parser.add_argument("--require-final-evidence", action="store_true")
    parser.add_argument("--rerun-stage-validators", action="store_true")
    args = parser.parse_args()
    try:
        manifest = validate_v014_final_overall_review(
            require_private_evidence=args.require_private_evidence,
            require_final_evidence=args.require_final_evidence,
            rerun_stage_validators=args.rerun_stage_validators,
        )
    except (ValidationError, ValueError, KeyError, RuntimeError) as exc:
        print(f"FAIL: {exc}")
        return 1
    summary = manifest["summary"]
    print(
        "PASS: KMFA v0.1.4 final overall review "
        f"stages={summary['current_stage_validator_pass_count']}/18 "
        f"tests={summary['full_suite_test_pass_count']}/{summary['full_suite_test_count']} "
        f"findings={summary['fixed_review_finding_count']}/6 open={summary['open_review_finding_count']} "
        f"raw={summary['raw_snapshot_exact_match']} upload_ready={summary['github_main_upload_ready']} "
        f"upload_performed={summary['github_upload_performed']} decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
