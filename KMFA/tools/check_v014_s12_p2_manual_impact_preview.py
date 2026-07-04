#!/usr/bin/env python3
"""Validate KMFA v0.1.4 S12-P2 manual impact preview evidence."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from KMFA.tools.manual_impact_preview import REQUIRED_IMPACT_DOMAINS, validate_manual_impact_preview_artifacts
from KMFA.tools.v014_s12_p2_manual_impact_preview import (
    ACCEPTANCE_ID,
    HTML_OUTPUT_PATH,
    MANIFEST_PATH,
    NEXT_REQUIRED_STEP,
    PHASE_SCOPE,
    PREVIEWS_PATH,
    REPORT_PATH,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
    S12_P1_EVENTS_PATH,
    SCHEMA_VERSION,
    TASK_ID,
    TEST_RESULTS_PATH,
    _phase_boundaries,
    _public_repo_safety,
    _quality_gate,
    _raw_boundary,
    load_v14_html_uiux_baseline,
    validate_legacy_s12_p2_artifacts,
    validate_s12_p1_dependency,
)


PUBLIC_SAFETY_FALSE_KEYS = tuple(key for key, value in _public_repo_safety().items() if value is False)
PUBLIC_SAFETY_TRUE_KEYS = tuple(key for key, value in _public_repo_safety().items() if value is True)
RAW_BOUNDARY_FALSE_KEYS = tuple(key for key, value in _raw_boundary().items() if value is False)
QUALITY_FALSE_KEYS = tuple(key for key, value in _quality_gate().items() if value is False)
QUALITY_TRUE_KEYS = tuple(key for key, value in _quality_gate().items() if value is True)
PHASE_FALSE_KEYS = tuple(key for key, value in _phase_boundaries().items() if value is False)
PHASE_TRUE_KEYS = tuple(key for key, value in _phase_boundaries().items() if value is True)
REQUIRED_HARD_BLOCKS = (
    "s12_p3_rerun_not_performed",
    "stage12_review_not_performed",
    "report_grade_d_only",
    "pending_reconciliation_blocks_formal_report",
    "raw_data_mutation_forbidden",
    "protected_business_value_publication_forbidden",
    "field_header_plaintext_publication_forbidden",
    "formal_report_release_blocked",
    "business_decision_basis_blocked",
    "lineage_full_check_not_performed",
    "protected_business_value_matching_not_performed",
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


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise ValidationError(f"missing JSONL file: {path}")
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValidationError(f"{path} contains a non-object JSONL row")
        records.append(value)
    return records


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


def validate_v014_s12_p2_manual_impact_preview(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []
    manifest = read_json(manifest_path)
    previews = read_jsonl(PREVIEWS_PATH)
    source_events = read_jsonl(S12_P1_EVENTS_PATH)
    dependency = validate_s12_p1_dependency()
    legacy = validate_legacy_s12_p2_artifacts()
    baseline = load_v14_html_uiux_baseline()
    html_text = HTML_OUTPUT_PATH.read_text(encoding="utf-8") if HTML_OUTPUT_PATH.exists() else ""

    validate_manual_impact_preview_artifacts(
        manifest,
        previews,
        {"html": {"kmfa_manual_impact_preview": html_text}},
        source_events,
    )

    require(manifest.get("schema_version") == SCHEMA_VERSION, "manifest schema mismatch", errors)
    require(manifest.get("project_id") == "KMFA", "project_id mismatch", errors)
    require(manifest.get("version") == "0.1.4", "version mismatch", errors)
    require(manifest.get("stage_id") == "S12", "stage_id must be S12", errors)
    require(manifest.get("phase_id") == "S12-P2", "phase_id must be S12-P2", errors)
    require(manifest.get("stage_phase") == "S12-P2", "stage_phase must be S12-P2", errors)
    require(manifest.get("phase_scope") == PHASE_SCOPE, "phase scope mismatch", errors)
    require(manifest.get("task_id") == TASK_ID, "task_id mismatch", errors)
    require(manifest.get("acceptance_ids") == [ACCEPTANCE_ID], "acceptance id mismatch", errors)
    require(manifest.get("completed_task_ids") == ["S12P2T01", "S12P2T02", "S12P2T03"], "tasks mismatch", errors)
    require(
        manifest.get("status") == "completed_validated_local_only_no_go_upload_deferred_manual_impact_preview",
        "status mismatch",
        errors,
    )
    require(manifest.get("s12_p1_dependency_validated") is True, "S12-P1 dependency flag mismatch", errors)
    require(dependency.get("phase_id") == "S12-P1", "dependency did not validate S12-P1", errors)
    require(manifest.get("legacy_s12_p2_dependency_validated") is True, "legacy S12-P2 flag mismatch", errors)

    progress = manifest.get("stage12_phase_progress", {})
    require(progress.get("completed_phase_count") == 2, "completed phase count mismatch", errors)
    require(progress.get("total_phase_count") == 3, "total phase count mismatch", errors)
    require(progress.get("derived_percent_bps") == 6667, "derived percent bps mismatch", errors)
    require(progress.get("derived_percent_label") == "66.67%", "derived percent label mismatch", errors)
    require(progress.get("s12_p1_performed") is True, "S12-P1 must be true", errors)
    require(progress.get("s12_p2_performed") is True, "S12-P2 must be true", errors)
    require(progress.get("s12_p3_performed") is False, "S12-P3 must be false", errors)
    require(progress.get("stage12_review_performed") is False, "Stage 12 review must be false", errors)

    summary = manifest.get("manual_impact_preview_summary", {})
    expected_counts = {
        "source_event_count": 5,
        "impact_preview_count": 5,
        "affected_project_count": 8,
        "affected_metric_count": 11,
        "affected_report_count": 5,
        "high_risk_count": 3,
        "second_confirmation_required_count": 3,
        "blocked_publish_count": 3,
        "publish_allowed_count": 2,
        "raw_layer_write_count": 0,
        "source_mutation_count": 0,
        "business_plaintext_count": 0,
        "derived_rerun_count": 0,
        "formal_report_count": 0,
        "business_decision_basis_count": 0,
        "github_upload_count": 0,
    }
    for key, expected in expected_counts.items():
        require(summary.get(key) == expected, f"summary.{key} mismatch", errors)
    require(summary == manifest.get("summary"), "legacy summary alias mismatch", errors)
    for key in (
        "source_event_count",
        "impact_preview_count",
        "affected_project_count",
        "affected_metric_count",
        "affected_report_count",
        "high_risk_count",
        "second_confirmation_required_count",
        "blocked_publish_count",
        "publish_allowed_count",
    ):
        require(summary.get(key) == legacy[key], f"legacy {key} mismatch", errors)
    require(tuple(manifest.get("required_impact_domains", [])) == REQUIRED_IMPACT_DOMAINS, "impact domains mismatch", errors)
    require({preview["source_event_id"] for preview in previews} == {event["event_id"] for event in source_events}, "preview source coverage mismatch", errors)

    v14 = manifest.get("v14_html_uiux_baseline", {})
    for key, expected in baseline.items():
        if key in {
            "implementation_reflects_impact_preview",
            "implementation_reflects_second_confirmation_feedback",
            "implementation_reflects_no_raw_mutation",
        }:
            continue
        require(v14.get(key) == expected, f"v14 baseline {key} mismatch", errors)
    require(v14.get("audit_file_count") == 6, "v14 audit file count mismatch", errors)
    require(v14.get("audit_control_row_count") == 54, "v14 audit row count mismatch", errors)
    require(v14.get("audit_pass_count") == 54, "v14 audit pass count mismatch", errors)
    require(v14.get("audit_warn_count") == 0, "v14 audit warn count mismatch", errors)
    require(v14.get("audit_fail_count") == 0, "v14 audit fail count mismatch", errors)
    require(v14.get("implementation_reflects_impact_preview") is True, "impact preview reflection mismatch", errors)
    require(
        v14.get("implementation_reflects_second_confirmation_feedback") is True,
        "second confirmation reflection mismatch",
        errors,
    )
    require(v14.get("implementation_reflects_no_raw_mutation") is True, "no raw mutation reflection mismatch", errors)

    require("<button" in html_text, "HTML must expose actionable preview buttons", errors)
    require("aria-live=\"polite\"" in html_text, "HTML must expose visible feedback region", errors)
    require("addEventListener" in html_text, "HTML must include click feedback wiring", errors)
    for required_text in ("受影响项目", "受影响指标", "受影响报告", "高风险二次确认", "未通过预览不得发布", "重跑未执行"):
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
    require(manifest.get("next_phase") == "S12-P3", "next phase mismatch", errors)
    require(manifest.get("next_required_step") == NEXT_REQUIRED_STEP, "next step mismatch", errors)
    for non_goal in (
        "S12-P3 derived rerun",
        "Stage 12 overall review",
        "GitHub upload",
        "raw value matching",
        "lineage full check",
        "formal report release",
        "business execution",
    ):
        require(non_goal in manifest.get("non_goals", []), f"missing non-goal {non_goal}", errors)

    git_info = manifest.get("git", {})
    require(git_info.get("branch") == git_output(["branch", "--show-current"]), "git branch mismatch", errors)
    require(git_info.get("remote") == git_output(["remote", "get-url", "origin"]), "git remote mismatch", errors)
    manifest_head = str(git_info.get("head", ""))
    require(re.fullmatch(r"[0-9a-f]{40}", manifest_head) is not None, "git head format mismatch", errors)

    for path in (
        REPORT_PATH,
        TEST_RESULTS_PATH,
        RISK_REGISTER_PATH,
        ROLLBACK_PATH,
        MANIFEST_PATH,
        PREVIEWS_PATH,
        HTML_OUTPUT_PATH,
    ):
        check_public_evidence_text(path, errors)

    if errors:
        raise ValidationError("KMFA v0.1.4 S12-P2 validation failed:\n- " + "\n- ".join(errors))
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.4 S12-P2 manual impact preview evidence.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args(argv)
    manifest = validate_v014_s12_p2_manual_impact_preview(args.manifest)
    summary = manifest["manual_impact_preview_summary"]
    print(
        "PASS: KMFA v0.1.4 S12-P2 manual impact preview validated "
        f"(previews={summary['impact_preview_count']}, "
        f"projects={summary['affected_project_count']}, "
        f"metrics={summary['affected_metric_count']}, "
        f"reports={summary['affected_report_count']}, "
        f"high_risk={summary['high_risk_count']}, "
        f"blocked_publish={summary['blocked_publish_count']}, "
        "s12_p3=false, stage12_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
