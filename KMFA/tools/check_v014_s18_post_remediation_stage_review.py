#!/usr/bin/env python3
"""Validate current KMFA v0.1.4 Stage 18 overall-review evidence."""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools import v014_s18_post_remediation_stage_review as review  # noqa: E402


SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)(password|passwd|secret|api_key|token)\s*=\s*[^\s,;]{8,}"),
)


class ValidationError(ValueError):
    pass


def _require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        text=True,
        capture_output=True,
        check=False,
    )


def _public_paths() -> tuple[Path, ...]:
    return (
        review.SUMMARY_PATH,
        review.MANIFEST_PATH,
        review.PHASE_RESULTS_PATH,
        review.CONTRACT_MATRIX_PATH,
        review.ACCEPTANCE_MATRIX_PATH,
        review.GO_NO_GO_PATH,
        review.REPORT_PATH,
        review.FINDINGS_PATH,
        review.TEST_RESULTS_PATH,
        review.RISK_REGISTER_PATH,
        review.ROLLBACK_PATH,
        review.HUMAN_DIR / "go_no_go_record_zh.md",
        review.METADATA_SUMMARY_PATH,
        review.METADATA_MANIFEST_PATH,
        review.METADATA_PHASE_RESULTS_PATH,
        review.METADATA_CONTRACT_MATRIX_PATH,
        review.METADATA_ACCEPTANCE_MATRIX_PATH,
        review.METADATA_GO_NO_GO_PATH,
    )


def _check_public_text(path: Path, errors: list[str]) -> None:
    _require(path.is_file(), f"missing public evidence: {path}", errors)
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8", errors="strict")
    lower = text.lower()
    for token in review.FORBIDDEN_PUBLIC_TEXT:
        _require(token.lower() not in lower, f"forbidden public token {token!r}: {path}", errors)
    for pattern in SECRET_PATTERNS:
        _require(pattern.search(text) is None, f"secret-like material found in {path}", errors)


def _check_private_evidence(errors: list[str]) -> None:
    paths = (
        review.PRIVATE_RAW_BEFORE_PATH,
        review.PRIVATE_RAW_AFTER_PATH,
        review.PRIVATE_DIAGNOSTIC_PATH,
        review.PRIVATE_REVIEW_REPORT_PATH,
    )
    for path in paths:
        _require(path.is_file(), f"missing private evidence: {path}", errors)
        _require(_git(["check-ignore", "-q", path.as_posix()]).returncode == 0, f"private evidence not ignored: {path}", errors)
        _require(_git(["ls-files", "--error-unmatch", path.as_posix()]).returncode != 0, f"private evidence tracked: {path}", errors)
    if not all(path.is_file() for path in paths[:3]):
        return
    helper = review.p3.s18_p2.s18_p1.s17_review.p1.s16_review.p1.s15_review.p1.s14_review.p1.s13_review.p1.s12_review.p1.s11_project
    before = review._read_json(review.PRIVATE_RAW_BEFORE_PATH)
    after = review._read_json(review.PRIVATE_RAW_AFTER_PATH)
    prior = review._read_json(review.p3.PRIVATE_RAW_AFTER_PATH)
    diagnostic = review._read_json(review.PRIVATE_DIAGNOSTIC_PATH)
    current = helper._raw_snapshot("validate_v014_s18_post_remediation_stage_review")
    normalize = helper._normalize_raw
    _require(normalize(before) == normalize(after), "review raw before/after mismatch", errors)
    _require(normalize(before) == normalize(prior), "review raw differs from current S18-P3", errors)
    _require(normalize(before) == normalize(current), "review raw differs from fresh current raw", errors)
    _require(diagnostic.get("raw_phase_exact") is True, "private raw phase flag missing", errors)
    _require(diagnostic.get("raw_cross_phase_exact") is True, "private raw cross-phase flag missing", errors)
    _require(diagnostic.get("phase_focused_test_pass_count") == 30, "private phase test count mismatch", errors)
    _require(diagnostic.get("phase_strict_validator_pass_count") == 3, "private strict count mismatch", errors)
    _require(diagnostic.get("review_finding_count") == 12, "private finding count mismatch", errors)
    _require(diagnostic.get("open_review_finding_count") == 0, "private open finding count mismatch", errors)


def _expected_parameters() -> dict[str, str]:
    return {
        "PARAM-KMFA-1816": "3;30;30;3;3;12;3;9;0;18;0",
        "PARAM-KMFA-1817": "5;3;1200;2;5;18;54;0;false;3;4;6;0;0",
        "PARAM-KMFA-1818": "5;true;true;3;9;2;1;true;false;false;false;false;Q4;D;NO_GO",
    }


def _check_governance(manifest: dict[str, Any], errors: list[str]) -> None:
    for path in (review.DEVELOPMENT_EVENTS_PATH, review.STAGE_STATUS_PATH, review.TASK_STATUS_PATH):
        rows = review._read_jsonl(path)
        _require(sum(row.get("phase_id") == review.PHASE_ID for row in rows) == 1, f"review governance row count drift: {path}", errors)
        _require(sum(row.get("phase_id") == review.p3.PHASE_ID for row in rows) == 1, f"P3 governance history missing: {path}", errors)
    event_rows = [row for row in review._read_jsonl(review.DEVELOPMENT_EVENTS_PATH) if row.get("phase_id") == review.PHASE_ID]
    if event_rows:
        event = event_rows[0]
        _require(event.get("files_changed") == review._phase_public_files(), "review event file list drift", errors)
        _require(event.get("phase_focused_test_pass_count") == 30, "review event test count drift", errors)
        _require(event.get("fixed_review_finding_count") == 3, "review event finding count drift", errors)
        _require(event.get("open_review_finding_count") == 0, "review event open finding drift", errors)

    version_matrix = Path("KMFA/docs/governance/VERSION_MATRIX.yaml").read_text(encoding="utf-8")
    _require(f'current_phase: "{review.PHASE_ID}"' in version_matrix, "VERSION_MATRIX current review drift", errors)
    _require(review.MODEL_REGISTRY_KEY in version_matrix and review.VERSION in version_matrix, "VERSION_MATRIX review profile missing", errors)
    _require(Path("KMFA/VERSION").read_text(encoding="utf-8").strip() == review.VERSION, "VERSION review drift", errors)

    handoff = Path("KMFA/HANDOFF.md").read_text(encoding="utf-8")
    for token in (
        review.PHASE_ID,
        "下一步只能执行 v1.4 最终整体复审",
        "不得执行 GitHub upload",
        "不得执行 App 重装",
    ):
        _require(token in handoff, f"HANDOFF review token missing: {token}", errors)
    agents = Path("KMFA/AGENTS.md").read_text(encoding="utf-8")
    _require(review.PHASE_ID in agents and "最终整体复审" in agents, "AGENTS review scope drift", errors)

    trace = Path("KMFA/docs/governance/TRACEABILITY_MATRIX.csv").read_text(encoding="utf-8")
    delivery = Path("KMFA/docs/governance/delivery_tasks.yaml").read_text(encoding="utf-8")
    _require(review.TASK_ID in trace and review.ACCEPTANCE_ID in trace, "review traceability missing", errors)
    _require(review.TASK_ID in delivery and review.ACCEPTANCE_ID in delivery, "review delivery task missing", errors)

    formula_text = Path("KMFA/docs/governance/formula_registry.yaml").read_text(encoding="utf-8")
    for token in (
        review.FORMULA_ID,
        "phase_focused_test_pass_count == 30",
        "phase_strict_validator_pass_count == 3",
        "fixed_review_finding_count == 3",
        "open_review_finding_count == 0",
        "cross_phase_contract_mismatch_count == 0",
        "raw_exact == true",
        "lineage_full_check_complete == false",
        "final_overall_review_performed == false",
        "github_upload_performed == false",
        "decision == NO_GO",
    ):
        _require(token in formula_text, f"review formula control missing: {token}", errors)

    for path in (Path("KMFA/docs/governance/model_registry.yaml"), Path("KMFA/metadata/model_registry.yaml")):
        text = path.read_text(encoding="utf-8")
        _require(review.MODEL_REGISTRY_KEY in text, f"review model profile missing: {path}", errors)
        _require(review.FORMULA_ID in text, f"review model formula missing: {path}", errors)
        for parameter_id in review.PARAMETER_IDS:
            _require(parameter_id in text, f"review model parameter missing: {path}:{parameter_id}", errors)

    with Path("KMFA/docs/governance/parameter_registry.csv").open(encoding="utf-8", newline="") as handle:
        parameters = {row["parameter_id"]: row for row in csv.DictReader(handle)}
    for parameter_id, expected in _expected_parameters().items():
        row = parameters.get(parameter_id, {})
        _require(row.get("formula_id") == review.FORMULA_ID, f"review parameter formula drift: {parameter_id}", errors)
        for field in ("default_value", "initial_or_prior_value", "active_value", "extracted_value"):
            _require(row.get(field) == expected, f"review parameter value drift: {parameter_id}:{field}", errors)
        _require(row.get("status") == "active", f"review parameter status drift: {parameter_id}", errors)

    assurance = review.ASSURANCE_STATUS_PATH.read_text(encoding="utf-8")
    for token in (
        review.TASK_ID,
        review.ACCEPTANCE_ID,
        review.FORMULA_ID,
        f'snapshot_event_time: "{manifest["generated_at"]}"',
        "total_active_parameters: 1436",
        "total_active_formulas: 314",
    ):
        _require(token in assurance, f"review assurance token missing: {token}", errors)
    for parameter_id in review.PARAMETER_IDS:
        _require(parameter_id in assurance, f"review assurance parameter missing: {parameter_id}", errors)

    for path, token in (
        (Path("KMFA/CHANGELOG.md"), review.VERSION),
        (Path("KMFA/README.md"), review.PHASE_ID),
        (Path("KMFA/docs/governance/DEVELOPMENT_LEDGER.md"), review.PHASE_ID),
        (Path("KMFA/docs/governance/MODEL_SPEC.md"), review.FORMULA_ID),
        (Path("KMFA/docs/governance/OWNER_STATUS.md"), review.PHASE_ID),
        (Path("KMFA/docs/governance/STATUS.md"), review.PHASE_ID),
        (Path("KMFA/功能清单.md"), "Stage 18 修补后整体复审"),
        (Path("KMFA/开发记录.md"), review.TASK_ID),
        (Path("KMFA/模型参数文件.md"), review.FORMULA_ID),
    ):
        _require(token in path.read_text(encoding="utf-8"), f"review governance token missing: {path}", errors)


def validate_v014_s18_post_remediation_stage_review(
    manifest_path: Path = review.MANIFEST_PATH,
    *,
    require_private_evidence: bool = False,
    require_final_evidence: bool = False,
) -> dict[str, Any]:
    errors: list[str] = []
    _require(manifest_path.is_file(), f"missing review manifest: {manifest_path}", errors)
    if errors:
        raise ValidationError("\n".join(errors))

    manifest = review._read_json(manifest_path)
    summary = review._read_json(review.SUMMARY_PATH)
    phase_results = review._read_jsonl(review.PHASE_RESULTS_PATH)
    contracts = review._read_jsonl(review.CONTRACT_MATRIX_PATH)
    acceptance = review._read_json(review.ACCEPTANCE_MATRIX_PATH)
    go_no_go = review._read_json(review.GO_NO_GO_PATH)

    _require(review._read_json(review.METADATA_MANIFEST_PATH) == manifest, "review metadata manifest mismatch", errors)
    _require(review._read_json(review.METADATA_SUMMARY_PATH) == summary, "review metadata summary mismatch", errors)
    _require(review._read_jsonl(review.METADATA_PHASE_RESULTS_PATH) == phase_results, "review metadata phase results mismatch", errors)
    _require(review._read_jsonl(review.METADATA_CONTRACT_MATRIX_PATH) == contracts, "review metadata contract mismatch", errors)
    _require(review._read_json(review.METADATA_ACCEPTANCE_MATRIX_PATH) == acceptance, "review metadata acceptance mismatch", errors)
    _require(review._read_json(review.METADATA_GO_NO_GO_PATH) == go_no_go, "review metadata Go/No-Go mismatch", errors)

    identity = {
        "project_id": "KMFA",
        "stage_id": "S18",
        "phase_id": review.PHASE_ID,
        "roadmap_phase_id": review.ROADMAP_PHASE_ID,
        "review_scope": review.REVIEW_SCOPE,
        "task_id": review.TASK_ID,
        "acceptance_id": review.ACCEPTANCE_ID,
        "version": review.VERSION,
        "status": review.STATUS,
        "decision": "NO_GO",
        "formula_id": review.FORMULA_ID,
        "model_registry_key": review.MODEL_REGISTRY_KEY,
    }
    for key, value in identity.items():
        _require(manifest.get(key) == value, f"review manifest {key} mismatch", errors)
    _require(manifest.get("schema_version") == "kmfa.v014.s18_post_remediation_stage_review_manifest.v1", "review schema mismatch", errors)
    _require(manifest.get("parameter_ids") == list(review.PARAMETER_IDS), "review parameter ids mismatch", errors)
    _require(manifest.get("branch") == "codex/kmfa", "review branch mismatch", errors)
    _require(bool(re.fullmatch(r"[0-9a-f]{40}", str(manifest.get("git_head", "")))), "review git_head format mismatch", errors)
    _require(manifest.get("summary") == summary, "review manifest summary mismatch", errors)

    p1_manifest, p2_manifest, p3_manifest = review._current_chain()
    _require(p1_manifest.get("next_phase") == "S18-P2", "current P1 route mismatch", errors)
    _require(p2_manifest.get("next_phase") == "S18-P3", "current P2 route mismatch", errors)
    _require(p3_manifest.get("next_phase") == "S18_STAGE_REVIEW", "current P3 route mismatch", errors)
    historical = review._historical_baseline()
    _require(manifest.get("historical_stage18_review_structural_baseline_validated") is True, "historical review flag missing", errors)
    _require(manifest.get("historical_stage18_review_dynamic_state_authoritative") is False, "historical dynamic state must be false", errors)
    _require(manifest.get("historical_stage18_review_baseline") == historical, "historical review summary mismatch", errors)
    _require(manifest.get("taskpack_contract") == review._taskpack_contract(), "review taskpack contract mismatch", errors)

    expected_summary = {
        "phase_results": {"S18-P1": "PASS", "S18-P2": "PASS", "S18-P3": "PASS"},
        "phase_pass_count": 3,
        "phase_focused_test_count": 30,
        "phase_focused_test_pass_count": 30,
        "phase_strict_validator_count": 3,
        "phase_strict_validator_pass_count": 3,
        "review_finding_count": 12,
        "fixed_review_finding_count": 3,
        "passed_review_finding_count": 9,
        "open_review_finding_count": 0,
        "cross_phase_contract_count": 18,
        "cross_phase_contract_mismatch_count": 0,
        "historical_stage18_review_validated": True,
        "raw_source_file_count": 5,
        "raw_snapshot_exact_match": True,
        "raw_cross_phase_snapshot_exact_match": True,
        "fresh_raw_snapshot_validated": True,
        "open_final_difference_accepted_count": 3,
        "nonzero_delta_reconciliation_count": 9,
        "zero_delta_reconciliation_count": 2,
        "incomplete_reconciliation_count": 1,
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "s18_p1_performed": True,
        "s18_p2_performed": True,
        "s18_p3_performed": True,
        "stage18_review_performed": True,
        "final_overall_review_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "decision": "NO_GO",
    }
    for key, value in expected_summary.items():
        _require(summary.get(key) == value, f"review summary {key} mismatch", errors)

    _require([row.get("phase_id") for row in phase_results] == ["S18-P1", "S18-P2", "S18-P3"], "review phase result order mismatch", errors)
    _require(sum(row.get("focused_test_count", 0) for row in phase_results) == 30, "review focused test count mismatch", errors)
    _require(all(row.get("focused_test_status") == "PASS" for row in phase_results), "review focused test status mismatch", errors)
    _require(all(row.get("strict_validator_status") == "PASS" for row in phase_results), "review strict validator status mismatch", errors)
    _require(len(contracts) == 18, "review contract count mismatch", errors)
    _require(all(row.get("status") == "PASS" and row.get("mismatch_count") == 0 for row in contracts), "review contract mismatch", errors)

    findings = manifest.get("review_findings", [])
    _require(len(findings) == 12, "review finding count mismatch", errors)
    _require(sum(row.get("status") == "fixed" for row in findings) == 3, "review fixed finding mismatch", errors)
    _require(sum(row.get("status") == "passed" for row in findings) == 9, "review passed finding mismatch", errors)
    _require(sum(row.get("status") == "open" for row in findings) == 0, "review open finding mismatch", errors)
    _require(manifest.get("review_fix_checks") == review._review_fix_checks(), "review fix check mismatch", errors)
    _require(all(manifest.get("review_fix_checks", {}).values()), "review fix incomplete", errors)

    expected_gate = {
        "precision_scenario_count": 5,
        "consecutive_import_run_count": 3,
        "synthetic_batch_item_count": 1200,
        "blocking_error_report_count": 2,
        "regression_check_category_count": 5,
        "stage_evidence_count": 18,
        "html_audit_pass_count": 54,
        "html_audit_fail_count": 0,
        "lineage_full_check_complete": False,
        "connector_plan_count": 3,
        "read_only_connector_count": 3,
        "opme_entry_surface_count": 4,
        "backlog_item_count": 6,
        "live_connector_call_count": 0,
        "external_service_call_count": 0,
        "source_mutation_allowed_count": 0,
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "decision": "NO_GO",
    }
    _require(manifest.get("stage_gate") == expected_gate, "review stage gate mismatch", errors)
    _require(manifest.get("review_boundaries") == review._review_boundaries(), "review boundary mismatch", errors)
    _require(manifest.get("public_repo_safety") == review._public_safety(), "review public safety mismatch", errors)

    _require(manifest.get("go_no_go") == go_no_go, "review manifest Go/No-Go mismatch", errors)
    _require(go_no_go.get("decision") == "NO_GO", "review decision mismatch", errors)
    _require("STAGE18_REVIEW_PENDING" not in go_no_go.get("blocker_ids", []), "review pending blocker not resolved", errors)
    for blocker in (
        "LINEAGE_FULL_CHECK_NOT_COMPLETE",
        "OPEN_RECONCILIATION_REMAINS",
        "OFFICIAL_REPORT_RELEASE_NOT_ALLOWED",
        "FINAL_OVERALL_REVIEW_PENDING",
        "GITHUB_MAIN_UPLOAD_DEFERRED",
        "APP_REINSTALL_DEFERRED",
    ):
        _require(blocker in go_no_go.get("blocker_ids", []), f"review blocker missing: {blocker}", errors)
    for key, value in go_no_go.items():
        if key.endswith("_allowed"):
            _require(value is False, f"review go_no_go.{key} must be false", errors)
        if key.endswith("_performed") and key != "stage18_review_performed":
            _require(value is False, f"review go_no_go.{key} must be false", errors)
    _require(go_no_go.get("stage18_review_performed") is True, "review performed flag missing", errors)

    _require(manifest.get("acceptance_matrix") == acceptance, "review acceptance mirror mismatch", errors)
    _require(acceptance.get("check_count") == 31, "review acceptance count mismatch", errors)
    _require(acceptance.get("check_pass_count") == 31, "review acceptance pass mismatch", errors)
    _require(acceptance.get("check_fail_count") == 0, "review acceptance failure", errors)
    bundle = {"summary": summary, "phase_results": phase_results, "contracts": contracts, "go_no_go": go_no_go}
    try:
        review.validate_review_bundle(bundle)
    except ValueError as exc:
        errors.append(f"review bundle invalid: {exc}")
    _require(manifest.get("content_hash") == review._sha256_json(bundle), "review content hash mismatch", errors)
    _require(manifest.get("next_phase") == review.NEXT_PHASE, "review next phase mismatch", errors)

    validation = manifest.get("validation_summary", {})
    if require_final_evidence:
        for key in (
            "final_validation_recorded",
        ):
            _require(validation.get(key) is True, f"review final flag missing: {key}", errors)
        for key in (
            "phase_focused_tests",
            "phase_strict_validators",
            "review_focused_tests",
            "review_strict_validator",
            "review_findings_closed",
            "raw_alignment",
            "governance_and_safety_scans",
        ):
            _require(validation.get(key) == "PASS", f"review validation not final: {key}", errors)
    if require_private_evidence:
        _check_private_evidence(errors)

    for path in _public_paths():
        _check_public_text(path, errors)
    _check_governance(manifest, errors)

    human_phrases = {
        review.REPORT_PATH: ("Stage 18 整体复审", "30/30", "3 fixed / 9 passed / 0 open"),
        review.FINDINGS_PATH: ("复审 Findings", "V014-S18-REVIEW-F03"),
        review.TEST_RESULTS_PATH: ("29 PASS / 1 FAIL", "30/30 PASS", "31/31 PASS"),
        review.HUMAN_DIR / "go_no_go_record_zh.md": ("决策：NO_GO", "最终整体复审仍待执行"),
    }
    for path, phrases in human_phrases.items():
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            for phrase in phrases:
                _require(phrase in text, f"review human phrase missing {phrase!r}: {path}", errors)

    if errors:
        raise ValidationError("\n".join(errors))
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate current KMFA Stage 18 overall-review evidence")
    parser.add_argument("--manifest", type=Path, default=review.MANIFEST_PATH)
    parser.add_argument("--require-private-evidence", action="store_true")
    parser.add_argument("--require-final-evidence", action="store_true")
    args = parser.parse_args(argv)
    manifest = validate_v014_s18_post_remediation_stage_review(
        args.manifest,
        require_private_evidence=args.require_private_evidence,
        require_final_evidence=args.require_final_evidence,
    )
    summary = manifest["summary"]
    print(
        "Stage 18 review strict PASS: "
        f"phases={summary['phase_pass_count']}/3 tests={summary['phase_focused_test_pass_count']}/30 "
        f"validators={summary['phase_strict_validator_pass_count']}/3 findings={summary['fixed_review_finding_count']}/3 "
        f"open={summary['open_review_finding_count']} contracts={summary['cross_phase_contract_count']} "
        f"raw={summary['raw_snapshot_exact_match']} decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
