#!/usr/bin/env python3
"""Validate KMFA v0.1.4 S12-P3 manual rerun mechanism evidence."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.manual_rerun_mechanism import REQUIRED_RERUN_CHAIN, validate_manual_rerun_mechanism_artifacts
from KMFA.tools.v014_s12_p3_manual_rerun_mechanism import (
    ACCEPTANCE_ID,
    CONSISTENCY_CHECKS_PATH,
    HTML_OUTPUT_PATH,
    INVALIDATIONS_PATH,
    MANIFEST_PATH,
    NEXT_REQUIRED_STEP,
    PHASE_SCOPE,
    REPORT_PATH,
    RERUN_STEPS_PATH,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
    S12_P1_EVENTS_PATH,
    S12_P2_PREVIEWS_PATH,
    SCHEMA_VERSION,
    TASK_ID,
    TEST_RESULTS_PATH,
    _phase_boundaries,
    _public_repo_safety,
    _quality_gate,
    _raw_boundary,
    load_v14_html_uiux_baseline,
    read_jsonl,
    validate_s12_p2_dependency,
)


PUBLIC_SAFETY_FALSE_KEYS = tuple(key for key, value in _public_repo_safety().items() if value is False)
PUBLIC_SAFETY_TRUE_KEYS = tuple(key for key, value in _public_repo_safety().items() if value is True)
RAW_BOUNDARY_FALSE_KEYS = tuple(key for key, value in _raw_boundary().items() if value is False)
QUALITY_FALSE_KEYS = tuple(key for key, value in _quality_gate().items() if value is False)
QUALITY_TRUE_KEYS = tuple(key for key, value in _quality_gate().items() if value is True)
PHASE_FALSE_KEYS = tuple(key for key, value in _phase_boundaries().items() if value is False)
PHASE_TRUE_KEYS = tuple(key for key, value in _phase_boundaries().items() if value is True)
REQUIRED_HARD_BLOCKS = (
    "stage12_review_not_performed",
    "report_grade_d_only",
    "pending_reconciliation_blocks_formal_report",
    "raw_data_mutation_forbidden",
    "protected_source_publication_forbidden",
    "field_header_plaintext_publication_forbidden",
    "formal_report_release_blocked",
    "business_decision_basis_blocked",
    "lineage_full_check_not_performed",
    "protected_source_matching_not_performed",
    "github_upload_deferred_until_v014_stage1_18_complete",
    "app_reinstall_not_performed",
    "business_execution_blocked",
)
FORBIDDEN_PUBLIC_TEXT = (
    "raw_value:",
    "normalized_value:",
    "source_header_text:",
    "original_filename",
    "member_sha256:",
    "actual_package_sha256",
    "authoritative_value_cents",
    "system_value_cents",
    "amount_cents:",
    "amount_yuan:",
    "sheet_name:",
    "row_value:",
    "cell_value:",
    "business_data:",
    "bank_statement",
    "contract_full_text",
    "salary_detail",
    "tax_filing",
    "connector_" + "token:",
    "connector_" + "password:",
    "api" + "_key:",
    "private" + "_key:",
    "-----" "BEGIN",
    "s" "k-",
    "project_name_plaintext",
    "customer_name_plaintext",
    "counterparty_plaintext",
    "company_entity_plaintext",
    "account_number:",
    "KMFA" "_MetaData",
    "/Users/linzezhang/Downloads",
    ".xlsx",
    ".xls",
    ".zip",
    ".pdf",
    ".sqlite",
    ".db",
)
STRICT_SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)(password|passwd|secret|api" + r"_key|token)\s*=\s*[^\s,;]{8,}"),
)


class ValidationError(Exception):
    pass


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ValidationError(f"missing JSON file: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValidationError(f"{path} must contain a JSON object")
    return value


def git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise ValidationError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def check_public_evidence_text(path: Path, errors: list[str]) -> None:
    require(path.exists(), f"missing public evidence: {path}", errors)
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8", errors="ignore")
    lower = text.lower()
    for forbidden in FORBIDDEN_PUBLIC_TEXT:
        require(forbidden.lower() not in lower, f"forbidden public evidence text {forbidden!r} in {path}", errors)
    for pattern in STRICT_SECRET_PATTERNS:
        require(pattern.search(text) is None, f"secret-like token found in {path}: {pattern.pattern}", errors)


def validate_v014_s12_p3_manual_rerun_mechanism(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []
    manifest = read_json(manifest_path)
    invalidations = read_jsonl(INVALIDATIONS_PATH)
    rerun_steps = read_jsonl(RERUN_STEPS_PATH)
    consistency_checks = read_jsonl(CONSISTENCY_CHECKS_PATH)
    source_events = read_jsonl(S12_P1_EVENTS_PATH)
    source_previews = read_jsonl(S12_P2_PREVIEWS_PATH)
    dependency = validate_s12_p2_dependency()
    baseline = load_v14_html_uiux_baseline()
    html_text = HTML_OUTPUT_PATH.read_text(encoding="utf-8") if HTML_OUTPUT_PATH.exists() else ""

    validate_manual_rerun_mechanism_artifacts(
        manifest,
        invalidations,
        rerun_steps,
        consistency_checks,
        {"html": {"kmfa_manual_rerun_mechanism": html_text}},
        source_events,
        source_previews,
    )

    require(manifest.get("schema_version") == SCHEMA_VERSION, "manifest schema mismatch", errors)
    require(manifest.get("project_id") == "KMFA", "project_id mismatch", errors)
    require(manifest.get("version") == "0.1.4", "version mismatch", errors)
    require(manifest.get("stage_id") == "S12", "stage_id must be S12", errors)
    require(manifest.get("phase_id") == "S12-P3", "phase_id must be S12-P3", errors)
    require(manifest.get("stage_phase") == "S12-P3", "stage_phase must be S12-P3", errors)
    require(manifest.get("phase_scope") == PHASE_SCOPE, "phase scope mismatch", errors)
    require(manifest.get("task_id") == TASK_ID, "task_id mismatch", errors)
    require(manifest.get("acceptance_ids") == [ACCEPTANCE_ID], "acceptance id mismatch", errors)
    require(
        manifest.get("completed_task_ids")
        == [
            "S12P1T01",
            "S12P1T02",
            "S12P1T03",
            "S12P2T01",
            "S12P2T02",
            "S12P2T03",
            "S12P3T01",
            "S12P3T02",
            "S12P3T03",
        ],
        "tasks mismatch",
        errors,
    )
    require(
        manifest.get("status") == "completed_validated_local_only_no_go_upload_deferred_manual_rerun_mechanism",
        "status mismatch",
        errors,
    )
    require(manifest.get("s12_p2_dependency_validated") is True, "S12-P2 dependency flag mismatch", errors)
    require(dependency.get("phase_id") == "S12-P2", "dependency did not validate S12-P2", errors)

    progress = manifest.get("stage12_phase_progress", {})
    require(progress.get("completed_phase_count") == 3, "completed phase count mismatch", errors)
    require(progress.get("total_phase_count") == 3, "total phase count mismatch", errors)
    require(progress.get("derived_percent_bps") == 10000, "derived percent bps mismatch", errors)
    require(progress.get("derived_percent_label") == "100.00%", "derived percent label mismatch", errors)
    require(progress.get("s12_p1_performed") is True, "S12-P1 must be true", errors)
    require(progress.get("s12_p2_performed") is True, "S12-P2 must be true", errors)
    require(progress.get("s12_p3_performed") is True, "S12-P3 must be true", errors)
    require(progress.get("stage12_review_performed") is False, "Stage 12 review must be false", errors)

    summary = manifest.get("manual_rerun_summary", {})
    expected_counts = {
        "source_event_count": 5,
        "source_preview_count": 5,
        "eligible_event_count": 2,
        "blocked_preview_count": 3,
        "cache_invalidation_count": 2,
        "rerun_step_count": 8,
        "same_source_consistency_check_count": 2,
        "rerun_chain_layer_count": 4,
        "old_version_retained_count": 8,
        "new_version_appended_count": 8,
        "raw_layer_write_count": 0,
        "source_mutation_count": 0,
        "business_plaintext_count": 0,
        "formal_report_count": 0,
        "business_decision_basis_count": 0,
        "report_grade_upgrade_count": 0,
        "stage12_review_count": 0,
        "github_upload_count": 0,
        "lineage_full_check_count": 0,
    }
    for key, expected in expected_counts.items():
        require(summary.get(key) == expected, f"summary.{key} mismatch", errors)
    require(summary == manifest.get("summary"), "legacy summary alias mismatch", errors)
    require(tuple(manifest.get("required_rerun_chain", [])) == REQUIRED_RERUN_CHAIN, "rerun chain mismatch", errors)

    record_counts = manifest.get("record_counts", {})
    require(record_counts.get("invalidations") == len(invalidations) == 2, "invalidation count mismatch", errors)
    require(record_counts.get("rerun_steps") == len(rerun_steps) == 8, "rerun step count mismatch", errors)
    require(
        record_counts.get("consistency_checks") == len(consistency_checks) == 2,
        "consistency count mismatch",
        errors,
    )

    eligible_event_ids = {record["source_event_id"] for record in invalidations}
    require(eligible_event_ids == {record["source_event_id"] for record in rerun_steps}, "rerun event set mismatch", errors)
    require(
        eligible_event_ids == {record["source_event_id"] for record in consistency_checks},
        "consistency event set mismatch",
        errors,
    )
    for step in rerun_steps:
        require(step.get("old_derived_version_ref") != step.get("new_derived_version_ref"), "version ref mismatch", errors)
        require(step.get("overwrite_old_version_allowed") is False, "old version overwrite mismatch", errors)
        require(step.get("append_only_version_record_required") is True, "append-only requirement mismatch", errors)

    v14 = manifest.get("v14_html_uiux_baseline", {})
    for key, expected in baseline.items():
        require(v14.get(key) == expected, f"v14 baseline {key} mismatch", errors)
    require(v14.get("audit_file_count") == 6, "v14 audit file count mismatch", errors)
    require(v14.get("audit_control_row_count") == 54, "v14 audit row count mismatch", errors)
    require(v14.get("audit_pass_count") == 54, "v14 audit pass count mismatch", errors)
    require(v14.get("audit_warn_count") == 0, "v14 audit warn count mismatch", errors)
    require(v14.get("audit_fail_count") == 0, "v14 audit fail count mismatch", errors)

    for required_text in (
        "KMFA 重跑机制",
        "派生缓存失效",
        "字段映射",
        "事实层",
        "指标",
        "报告引用",
        "同源引用一致性",
        "正式报告未生成",
    ):
        require(required_text in html_text, f"HTML missing required text {required_text}", errors)

    phase = manifest.get("phase_boundaries", {})
    for key in PHASE_TRUE_KEYS:
        require(phase.get(key) is True, f"phase boundary {key} must be true", errors)
    for key in PHASE_FALSE_KEYS:
        require(phase.get(key) is False, f"phase boundary {key} must be false", errors)

    quality = manifest.get("quality_gate", {})
    for key in QUALITY_TRUE_KEYS:
        require(quality.get(key) is True, f"quality gate {key} must be true", errors)
    for key in QUALITY_FALSE_KEYS:
        require(quality.get(key) is False, f"quality gate {key} must be false", errors)
    require(quality.get("current_data_quality_grade") == "Q4", "data quality grade mismatch", errors)
    require(quality.get("current_report_grade") == "D", "report grade mismatch", errors)
    require(quality.get("release_permission") == "blocked", "release permission mismatch", errors)
    require(quality.get("pending_reconciliation_count") == 12, "pending reconciliation mismatch", errors)

    raw = manifest.get("raw_data_boundary", {})
    for key in RAW_BOUNDARY_FALSE_KEYS:
        require(raw.get(key) is False, f"raw boundary {key} must be false", errors)
    require(raw.get("raw_inbox_read_allowed_only_when_phase_requires") is True, "raw read policy mismatch", errors)

    public_safety = manifest.get("public_repo_safety", {})
    for key in PUBLIC_SAFETY_FALSE_KEYS:
        require(public_safety.get(key) is False, f"public safety {key} must be false", errors)
    for key in PUBLIC_SAFETY_TRUE_KEYS:
        require(public_safety.get(key) is True, f"public safety {key} must be true", errors)

    upload = manifest.get("github_upload", {})
    require(upload.get("github_upload_ready_next_gate") is False, "GitHub upload ready must be false", errors)
    require(
        upload.get("github_upload_deferred_until_v014_stage1_18_complete") is True,
        "GitHub upload deferral mismatch",
        errors,
    )
    require(upload.get("github_upload_performed") is False, "GitHub upload must be false", errors)
    require(
        upload.get("github_upload_status") == "not_uploaded_deferred_until_v014_stage1_18_complete",
        "GitHub upload status mismatch",
        errors,
    )

    hard_blocks = set(manifest.get("hard_blocks", []))
    for block in REQUIRED_HARD_BLOCKS:
        require(block in hard_blocks, f"missing hard block {block}", errors)
    require(manifest.get("next_phase") == "S12-STAGE-REVIEW", "next phase mismatch", errors)
    require(manifest.get("next_required_step") == NEXT_REQUIRED_STEP, "next step mismatch", errors)
    for non_goal in (
        "Stage 12 overall review",
        "GitHub upload",
        "protected source matching",
        "lineage full check",
        "formal report release",
        "business execution",
    ):
        require(non_goal in manifest.get("non_goals", []), f"missing non-goal {non_goal}", errors)

    git_info = manifest.get("git", {})
    require(git_info.get("branch") == git_output(["branch", "--show-current"]), "git branch mismatch", errors)
    require(git_info.get("remote") == git_output(["remote", "get-url", "origin"]), "git remote mismatch", errors)
    require(re.fullmatch(r"[0-9a-f]{40}", str(git_info.get("head", ""))) is not None, "git head format mismatch", errors)

    for path in (
        REPORT_PATH,
        TEST_RESULTS_PATH,
        RISK_REGISTER_PATH,
        ROLLBACK_PATH,
        MANIFEST_PATH,
        INVALIDATIONS_PATH,
        RERUN_STEPS_PATH,
        CONSISTENCY_CHECKS_PATH,
        HTML_OUTPUT_PATH,
    ):
        check_public_evidence_text(path, errors)

    if errors:
        raise ValidationError("KMFA v0.1.4 S12-P3 validation failed:\n- " + "\n- ".join(errors))
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.4 S12-P3 manual rerun mechanism evidence.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args(argv)
    manifest = validate_v014_s12_p3_manual_rerun_mechanism(args.manifest)
    summary = manifest["manual_rerun_summary"]
    print(
        "PASS: KMFA v0.1.4 S12-P3 manual rerun mechanism validated "
        f"(eligible={summary['eligible_event_count']}, "
        f"blocked_previews={summary['blocked_preview_count']}, "
        f"invalidations={summary['cache_invalidation_count']}, "
        f"rerun_steps={summary['rerun_step_count']}, "
        f"consistency_checks={summary['same_source_consistency_check_count']}, "
        "stage12_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
