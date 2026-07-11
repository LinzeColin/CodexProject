#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Strict validator for current KMFA S12-P3 rerun-mechanism evidence."""

from __future__ import annotations

import argparse
import csv
import functools
import json
import subprocess
from pathlib import Path
from typing import Any, Iterable

from KMFA.tools import check_v014_s12_p2_post_remediation_impact_preview as s12_p2_check
from KMFA.tools import v014_s12_p3_post_remediation_rerun_mechanism as phase
from KMFA.tools.check_v014_s12_p2_post_remediation_impact_preview import (
    validate_v014_s12_p2_post_remediation_impact_preview,
)


PUBLIC_FILES = (
    phase.SUMMARY_PATH,
    phase.MANIFEST_PATH,
    phase.PLANS_PATH,
    phase.GO_NO_GO_PATH,
    phase.HTML_PATH,
    phase.REPORT_PATH,
    phase.TEST_RESULTS_PATH,
    phase.RISK_REGISTER_PATH,
    phase.ROLLBACK_PATH,
    phase.METADATA_SUMMARY_PATH,
    phase.METADATA_MANIFEST_PATH,
    phase.METADATA_PLANS_PATH,
    phase.METADATA_GO_NO_GO_PATH,
)
FORBIDDEN_SUFFIXES = {
    ".zip",
    ".xls",
    ".xlsx",
    ".xlsm",
    ".pdf",
    ".db",
    ".sqlite",
    ".sqlite3",
    ".pem",
    ".key",
    ".p12",
    ".pfx",
}
FORBIDDEN_PUBLIC_TOKENS = (
    "/Users/",
    "KMFA_MetaData",
    "private_ref://",
    "original_filename",
    "source_header_text",
    "plaintext_value",
    "normalized_value",
    "raw_value",
    ".xlsx",
    ".xls",
    ".pdf",
    ".zip",
    ".sqlite",
    ".db",
    "api_key",
    "private_key",
    "password",
)


def _require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def _walk_keys(value: Any) -> Iterable[str]:
    if isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from _walk_keys(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_keys(item)


def _git_check_ignore(path: Path) -> bool:
    return subprocess.run(
        ["git", "check-ignore", "-q", path.as_posix()], check=False
    ).returncode == 0


def _git_tracked(path: Path) -> bool:
    return subprocess.run(
        ["git", "ls-files", "--error-unmatch", path.as_posix()],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode == 0


def _phase_is_current(version_matrix_text: str) -> bool:
    return f'current_phase: "{phase.PHASE_ID}"' in version_matrix_text


def _check_public_file(path: Path, errors: list[str]) -> None:
    _require(path.is_file(), f"missing public artifact: {path}", errors)
    if not path.is_file():
        return
    _require(path.suffix.lower() not in FORBIDDEN_SUFFIXES, f"forbidden suffix: {path}", errors)
    text = path.read_text(encoding="utf-8")
    for token in FORBIDDEN_PUBLIC_TOKENS:
        _require(token not in text, f"forbidden public token {token!r}: {path}", errors)


def _validate_public(errors: list[str]) -> dict[str, Any]:
    for path in PUBLIC_FILES:
        _check_public_file(path, errors)
    if errors:
        return {}
    manifest = _read_json(phase.MANIFEST_PATH)
    summary = _read_json(phase.SUMMARY_PATH)
    plans = _read_json(phase.PLANS_PATH)
    go_no_go = _read_json(phase.GO_NO_GO_PATH)
    _require(manifest.get("summary") == summary, "manifest/summary mismatch", errors)
    _require(manifest.get("rerun_plan_definitions") == plans.get("plans"), "manifest/plans mismatch", errors)
    _require(_read_json(phase.METADATA_MANIFEST_PATH) == manifest, "metadata manifest mismatch", errors)
    _require(_read_json(phase.METADATA_SUMMARY_PATH) == summary, "metadata summary mismatch", errors)
    _require(_read_json(phase.METADATA_PLANS_PATH) == plans, "metadata plans mismatch", errors)
    _require(_read_json(phase.METADATA_GO_NO_GO_PATH) == go_no_go, "metadata gate mismatch", errors)
    return manifest


def _validate_summary(manifest: dict[str, Any], errors: list[str]) -> None:
    summary = manifest.get("summary", {})
    expected = {
        "project_id": "KMFA",
        "stage_id": "S12",
        "roadmap_phase_id": "S12-P3",
        "phase_id": phase.PHASE_ID,
        "task_id": phase.TASK_ID,
        "acceptance_id": phase.ACCEPTANCE_ID,
        "version": phase.VERSION,
        "status": phase.STATUS,
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "decision": "NO_GO",
        "source_pending_action_group_count": 6,
        "source_impact_preview_definition_count": 6,
        "rerun_plan_definition_count": 6,
        "planned_rerun_step_count": 24,
        "required_rerun_chain_layer_count": 4,
        "high_risk_rerun_plan_count": 5,
        "second_confirmation_required_count": 5,
        "current_session_cache_invalidation_count_at_rest": 0,
        "current_session_rerun_step_count_at_rest": 0,
        "current_session_consistency_check_count_at_rest": 0,
        "current_persistent_cache_invalidation_count": 0,
        "current_persistent_rerun_step_count": 0,
        "current_persistent_consistency_check_count": 0,
        "current_approved_business_event_count": 0,
        "current_published_business_event_count": 0,
        "open_final_difference_accepted_count": 3,
        "nonzero_delta_reconciliation_count": 9,
        "zero_delta_reconciliation_count": 2,
        "incomplete_reconciliation_count": 1,
        "hard_block_count": 12,
        "raw_source_file_count": 5,
        "raw_snapshot_exact_match": True,
        "raw_cross_phase_snapshot_exact_match": True,
        "formal_report_count": 0,
        "business_decision_basis_count": 0,
        "s12_p1_performed": True,
        "s12_p2_performed": True,
        "s12_p3_performed": True,
        "persistent_derived_rerun_performed": False,
        "stage12_review_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }
    for key, value in expected.items():
        _require(summary.get(key) == value, f"summary {key} mismatch", errors)
    _require("eligible_event_count" not in summary, "stale legacy eligible-event field present", errors)
    _require("pending_reconciliation_count" not in summary, "stale pending=12 field present", errors)
    _require(manifest.get("phase_id") == phase.PHASE_ID, "manifest phase mismatch", errors)
    _require(manifest.get("task_id") == phase.TASK_ID, "manifest task mismatch", errors)
    _require(manifest.get("version") == phase.VERSION, "manifest version mismatch", errors)
    _require(
        manifest.get("s12_p2_post_remediation_dependency_validated") is True,
        "S12-P2 dependency flag mismatch",
        errors,
    )
    _require(
        manifest.get("legacy_s12_p3_policy_fixture_validated") is True,
        "legacy S12-P3 policy flag mismatch",
        errors,
    )
    _require(manifest.get("next_phase") == "S12-STAGE-REVIEW", "next phase mismatch", errors)


def _validate_plans(manifest: dict[str, Any], errors: list[str]) -> None:
    plans = manifest.get("rerun_plan_definitions", [])
    _require(len(plans) == 6, "rerun plan count mismatch", errors)
    _require(len({row.get("plan_id") for row in plans}) == 6, "rerun plan ids not unique", errors)
    _require(len({row.get("source_preview_id") for row in plans}) == 6, "source preview coverage mismatch", errors)
    _require(sum(row.get("risk_level") == "high" for row in plans) == 5, "high-risk plan count mismatch", errors)
    _require(tuple(manifest.get("required_rerun_chain", ())) == phase.REQUIRED_RERUN_CHAIN, "required chain mismatch", errors)
    for row in plans:
        _require(row.get("project_attribution") == "unproven_or_not_applicable", "project attribution drift", errors)
        _require(
            row.get("project_scope_semantics") == "potential_impact_not_attribution",
            "project scope semantics drift",
            errors,
        )
        _require(
            row.get("eligibility_status") == "blocked_no_approved_published_event",
            "eligibility status drift",
            errors,
        )
        _require(row.get("session_rerun_simulation_allowed") is True, "session simulation blocked", errors)
        for key in (
            "persistent_cache_invalidation_allowed",
            "persistent_rerun_allowed",
            "raw_layer_write_allowed",
            "persistent_business_write_allowed",
            "business_value_committed",
        ):
            _require(row.get(key) is False, f"plan {key} must be false", errors)
        steps = row.get("rerun_steps", [])
        _require(len(steps) == 4, "plan step count mismatch", errors)
        _require(tuple(step.get("layer") for step in steps) == phase.REQUIRED_RERUN_CHAIN, "plan chain order mismatch", errors)
        _require(
            {step.get("source_anchor_id") for step in steps} == {row.get("source_anchor_id")},
            "same-source anchor mismatch",
            errors,
        )
        for step in steps:
            _require(step.get("old_version_retained") is True, "old version retention missing", errors)
            _require(step.get("new_version_append_required") is True, "append-only requirement missing", errors)
            _require(
                step.get("status") == "planned_session_simulation_only",
                "persistent rerun step detected",
                errors,
            )
            _require(step.get("persistent_write_performed") is False, "persistent write detected", errors)


def _validate_html(errors: list[str]) -> None:
    text = phase.HTML_PATH.read_text(encoding="utf-8")
    for token in (
        "data-rerun-search",
        "data-risk-filter",
        "data-select-plan",
        "data-preview-rerun",
        "data-high-risk-ack",
        "data-confirm-rerun",
        "data-run-simulation",
        "data-check-consistency",
        "data-check-persistent",
        "data-reset-session",
        "派生缓存失效",
        "字段映射",
        "事实层",
        "指标",
        "报告引用",
        "同源引用一致性",
        "Q4 / D · NO_GO",
    ):
        _require(token in text, f"HTML token missing: {token}", errors)
    for token in ("localStorage", "sessionStorage", "indexedDB", "fetch(", "XMLHttpRequest"):
        _require(token not in text, f"persistent/network HTML token present: {token}", errors)


def _validate_dependencies(errors: list[str]) -> None:
    try:
        dependency = validate_v014_s12_p2_post_remediation_impact_preview(
            require_private_evidence=True,
            require_browser_evidence=True,
            require_final_evidence=True,
        )
    except Exception as exc:  # pragma: no cover - surfaced as validation evidence
        errors.append(f"S12-P2 dependency validation failed: {exc}")
        return
    summary = dependency["summary"]
    _require(summary.get("impact_preview_definition_count") == 6, "S12-P2 preview count drift", errors)
    _require(summary.get("current_published_business_event_count") == 0, "published event drift", errors)
    _require(summary.get("decision") == "NO_GO", "S12-P2 decision drift", errors)


def _validate_boundaries(manifest: dict[str, Any], errors: list[str]) -> None:
    quality = manifest.get("quality_gate", {})
    expected_true = (
        "rerun_plan_generation_allowed",
        "session_only_rerun_simulation_allowed",
        "high_risk_second_confirmation_required",
        "same_source_reference_consistency_check_required",
        "append_only_derived_version_required",
    )
    expected_false = (
        "one_cent_difference_ignored",
        "persistent_cache_invalidation_allowed",
        "persistent_derived_rerun_allowed",
        "blocked_event_persistent_rerun_allowed",
        "old_version_overwrite_allowed",
        "current_business_event_approval_allowed",
        "current_business_event_publish_allowed",
        "report_grade_upgrade_allowed",
        "persistent_business_write_allowed",
        "raw_layer_write_allowed",
        "formal_report_allowed",
        "business_decision_basis_allowed",
        "stage12_review_allowed",
        "github_upload_allowed",
        "app_reinstall_allowed",
        "business_execution_allowed",
    )
    for key in expected_true:
        _require(quality.get(key) is True, f"quality gate {key} mismatch", errors)
    for key in expected_false:
        _require(quality.get(key) is False, f"quality gate {key} mismatch", errors)
    _require(quality.get("money_tolerance_minor_units") == 0, "money tolerance must be zero", errors)
    boundaries = manifest.get("phase_boundaries", {})
    for key, value in phase._phase_boundaries().items():
        _require(boundaries.get(key) is value, f"phase boundary {key} mismatch", errors)
    safety = manifest.get("public_repo_safety", {})
    _require(safety.get("aggregate_only") is True, "aggregate-only safety flag missing", errors)
    _require(
        all(value is False for key, value in safety.items() if key != "aggregate_only"),
        "sensitive public repo safety flag enabled",
        errors,
    )


def _validate_governance(errors: list[str]) -> None:
    matrix = phase.VERSION_MATRIX_PATH.read_text(encoding="utf-8")
    if not _phase_is_current(matrix):
        return
    for token in (phase.PHASE_ID, phase.VERSION, phase.STATUS, phase.TASK_ID, phase.ACCEPTANCE_ID):
        _require(token in matrix, f"version matrix token missing: {token}", errors)
    _require(Path("KMFA/VERSION").read_text(encoding="utf-8").strip() == phase.VERSION, "KMFA/VERSION mismatch", errors)
    governance_paths = (
        Path("KMFA/docs/governance/model_registry.yaml"),
        Path("KMFA/metadata/model_registry.yaml"),
    )
    for path in governance_paths:
        _require(phase.MODEL_REGISTRY_KEY in path.read_text(encoding="utf-8"), f"model registry key missing: {path}", errors)
    _require(
        phase.FORMULA_ID in Path("KMFA/docs/governance/formula_registry.yaml").read_text(encoding="utf-8"),
        "formula registry entry missing",
        errors,
    )
    parameter_text = Path("KMFA/docs/governance/parameter_registry.csv").read_text(encoding="utf-8")
    for parameter_id in phase.PARAMETER_IDS:
        _require(parameter_id in parameter_text, f"parameter registry entry missing: {parameter_id}", errors)
    traceability = Path("KMFA/docs/governance/TRACEABILITY_MATRIX.csv").read_text(encoding="utf-8")
    _require(phase.ACCEPTANCE_ID in traceability, "traceability acceptance missing", errors)
    for path in (phase.DEVELOPMENT_EVENTS_PATH, phase.STAGE_STATUS_PATH, phase.TASK_STATUS_PATH):
        records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        _require(any(row.get("phase_id") == phase.PHASE_ID for row in records), f"phase record missing: {path}", errors)
    for path in (
        Path("KMFA/开发记录.md"),
        Path("KMFA/功能清单.md"),
        Path("KMFA/模型参数文件.md"),
        Path("KMFA/HANDOFF.md"),
    ):
        _require(phase.PHASE_ID in path.read_text(encoding="utf-8"), f"governance doc phase missing: {path}", errors)


def _read_audit(path: Path, errors: list[str]) -> dict[str, int]:
    _require(path.is_file(), f"audit evidence missing: {path}", errors)
    if not path.is_file():
        return {"rows": 0, "pass": 0, "fail": 1}
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    statuses = [str(row.get("status", "")).upper() for row in rows]
    fail_count = sum(status == "FAIL" for status in statuses)
    _require(rows, f"audit evidence empty: {path}", errors)
    _require(fail_count == 0, f"audit FAIL rows present: {path}", errors)
    return {"rows": len(rows), "pass": sum(status == "PASS" for status in statuses), "fail": fail_count}


def _validate_private(errors: list[str], require_browser_evidence: bool) -> None:
    _require(_git_check_ignore(phase.PRIVATE_DIR), "private runtime is not gitignored", errors)
    _require(not _git_tracked(phase.PRIVATE_DIR), "private runtime is tracked", errors)
    for path in (phase.PRIVATE_RAW_BEFORE_PATH, phase.PRIVATE_RAW_AFTER_PATH):
        _require(path.is_file(), f"private raw evidence missing: {path}", errors)
    if not phase.PRIVATE_RAW_BEFORE_PATH.is_file() or not phase.PRIVATE_RAW_AFTER_PATH.is_file():
        return
    before = _read_json(phase.PRIVATE_RAW_BEFORE_PATH)
    after = _read_json(phase.PRIVATE_RAW_AFTER_PATH)
    previous = _read_json(s12_p2_private_raw_after_path())
    normalize = phase.s12_p2.s12_p1.s11_project._normalize_raw
    _require(before.get("file_count") == 5, "raw file count mismatch", errors)
    _require(before.get("files") == after.get("files"), "raw file facts changed in S12-P3", errors)
    _require(normalize(before) == normalize(after), "normalized raw snapshot drift", errors)
    _require(normalize(before) == normalize(previous), "cross-S12-P2 raw snapshot drift", errors)
    if not require_browser_evidence:
        return
    _require(phase.PRIVATE_BROWSER_PATH.is_file(), "browser evidence missing", errors)
    if not phase.PRIVATE_BROWSER_PATH.is_file():
        return
    browser = _read_json(phase.PRIVATE_BROWSER_PATH)
    _require(browser.get("status") == "PASS", "browser evidence status mismatch", errors)
    expected_counts = {
        "viewport_checks": 2,
        "search_checks": 2,
        "risk_filter_checks": 2,
        "medium_plan_checks": 2,
        "high_plan_checks": 2,
        "preconfirmation_block_checks": 2,
        "second_confirmation_checks": 2,
        "rerun_simulation_checks": 2,
        "consistency_checks": 2,
        "persistent_execution_block_checks": 2,
        "reload_reset_checks": 2,
        "return_link_http_checks": 4,
        "actual_navigation_checks": 4,
    }
    for key, count in expected_counts.items():
        rows = browser.get(key, [])
        _require(len(rows) == count, f"browser {key} count mismatch", errors)
        _require(all(row.get("passed") is True for row in rows), f"browser {key} failure", errors)
    _require(
        all(row.get("no_horizontal_overflow") is True for row in browser.get("viewport_checks", [])),
        "browser horizontal overflow",
        errors,
    )
    _require(
        all(row.get("console_error_count") == 0 for row in browser.get("viewport_checks", [])),
        "browser console error",
        errors,
    )
    _read_audit(phase.PRIVATE_BASELINE_AUDIT_PATH, errors)
    _read_audit(phase.PRIVATE_CURRENT_AUDIT_PATH, errors)
    for mode in ("desktop", "mobile"):
        for suffix in ("", "_high_simulated"):
            screenshot = phase.PRIVATE_SCREENSHOT_DIR / f"rerun_{mode}{suffix}.png"
            _require(screenshot.is_file(), f"browser screenshot missing: {screenshot}", errors)
            if screenshot.is_file():
                width, height = s12_p2_check._png_dimensions(screenshot)
                _require(width > 0 and height > 0, f"invalid screenshot dimensions: {screenshot}", errors)


def s12_p2_private_raw_after_path() -> Path:
    return phase.s12_p2.PRIVATE_RAW_AFTER_PATH


@functools.lru_cache(maxsize=None)
def validate_v014_s12_p3_post_remediation_rerun_mechanism(
    *,
    require_private_evidence: bool = False,
    require_browser_evidence: bool = False,
    require_final_evidence: bool = False,
) -> dict[str, Any]:
    errors: list[str] = []
    manifest = _validate_public(errors)
    if manifest:
        _validate_summary(manifest, errors)
        _validate_plans(manifest, errors)
        _validate_html(errors)
        _validate_dependencies(errors)
        _validate_boundaries(manifest, errors)
        _validate_governance(errors)
        if require_final_evidence:
            validation = manifest.get("validation_summary", {})
            _require(validation.get("final_validation_recorded") is True, "final validation not recorded", errors)
            for key in ("focused_tests", "strict_validator", "browser_desktop_mobile", "governance_and_safety_scans"):
                _require(validation.get(key) == "PASS", f"final validation {key} mismatch", errors)
    if require_private_evidence:
        _validate_private(errors, require_browser_evidence=require_browser_evidence)
    if errors:
        raise ValueError("S12-P3 validation failed:\n- " + "\n- ".join(errors))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-private-evidence", action="store_true")
    parser.add_argument("--require-browser-evidence", action="store_true")
    parser.add_argument("--require-final-evidence", action="store_true")
    args = parser.parse_args()
    try:
        manifest = validate_v014_s12_p3_post_remediation_rerun_mechanism(
            require_private_evidence=args.require_private_evidence,
            require_browser_evidence=args.require_browser_evidence,
            require_final_evidence=args.require_final_evidence,
        )
    except Exception as exc:
        print(f"FAIL: {exc}")
        return 1
    summary = manifest["summary"]
    print(
        "PASS: S12-P3 post-remediation rerun mechanism "
        f"plans={summary['rerun_plan_definition_count']} "
        f"planned_steps={summary['planned_rerun_step_count']} "
        f"persistent_steps={summary['current_persistent_rerun_step_count']} "
        f"grade={summary['current_report_grade']} decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
