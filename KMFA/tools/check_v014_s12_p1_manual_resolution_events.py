#!/usr/bin/env python3
"""Validate KMFA v0.1.4 S12-P1 manual resolution event evidence."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from KMFA.tools.manual_resolution_events import REQUIRED_MANUAL_ACTION_KINDS
from KMFA.tools.v014_s12_p1_manual_resolution_events import (
    ACCEPTANCE_ID,
    EVENTS_PATH,
    HTML_OUTPUT_PATH,
    MANIFEST_PATH,
    NEXT_REQUIRED_STEP,
    PHASE_SCOPE,
    REPORT_PATH,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
    SCHEMA_VERSION,
    TASK_ID,
    TEST_RESULTS_PATH,
    _phase_boundaries,
    _public_repo_safety,
    _quality_gate,
    _raw_boundary,
    load_v14_html_uiux_baseline,
    validate_legacy_s12_p1_artifacts,
    validate_s11_stage_review_dependency,
)


PUBLIC_SAFETY_FALSE_KEYS = tuple(key for key, value in _public_repo_safety().items() if value is False)
PUBLIC_SAFETY_TRUE_KEYS = tuple(key for key, value in _public_repo_safety().items() if value is True)
RAW_BOUNDARY_FALSE_KEYS = tuple(key for key, value in _raw_boundary().items() if value is False)
QUALITY_FALSE_KEYS = tuple(key for key, value in _quality_gate().items() if value is False)
QUALITY_TRUE_KEYS = tuple(key for key, value in _quality_gate().items() if value is True)
PHASE_FALSE_KEYS = tuple(key for key, value in _phase_boundaries().items() if value is False)
PHASE_TRUE_KEYS = tuple(key for key, value in _phase_boundaries().items() if value is True)
REQUIRED_HARD_BLOCKS = (
    "impact_preview_not_performed",
    "derived_rerun_not_performed",
    "stage12_review_not_performed",
    "report_grade_d_only",
    "pending_reconciliation_blocks_formal_report",
    "raw_data_mutation_forbidden",
    "raw_value_publication_forbidden",
    "field_header_plaintext_publication_forbidden",
    "formal_report_release_blocked",
    "business_decision_basis_blocked",
    "lineage_full_check_not_performed",
    "raw_value_matching_not_performed",
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
    "pdf_value_cents",
    "excel_value_cents",
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


def validate_v014_s12_p1_manual_resolution_events(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []
    manifest = read_json(manifest_path)
    events = read_jsonl(EVENTS_PATH)
    stage11 = validate_s11_stage_review_dependency()
    legacy = validate_legacy_s12_p1_artifacts()
    baseline = load_v14_html_uiux_baseline()
    html_text = HTML_OUTPUT_PATH.read_text(encoding="utf-8") if HTML_OUTPUT_PATH.exists() else ""

    require(manifest.get("schema_version") == SCHEMA_VERSION, "manifest schema mismatch", errors)
    require(manifest.get("project_id") == "KMFA", "project_id mismatch", errors)
    require(manifest.get("version") == "0.1.4", "version mismatch", errors)
    require(manifest.get("stage_id") == "S12", "stage_id must be S12", errors)
    require(manifest.get("phase_id") == "S12-P1", "phase_id must be S12-P1", errors)
    require(manifest.get("phase_scope") == PHASE_SCOPE, "phase scope mismatch", errors)
    require(manifest.get("task_id") == TASK_ID, "task_id mismatch", errors)
    require(manifest.get("acceptance_ids") == [ACCEPTANCE_ID], "acceptance id mismatch", errors)
    require(manifest.get("completed_task_ids") == ["S12P1T01", "S12P1T02", "S12P1T03"], "tasks mismatch", errors)
    require(
        manifest.get("status") == "completed_validated_local_only_no_go_upload_deferred_manual_resolution_events",
        "status mismatch",
        errors,
    )
    require(manifest.get("s11_stage_review_dependency_validated") is True, "Stage 11 dependency flag mismatch", errors)
    require(stage11.get("next_phase") == "S12-P1", "Stage 11 review did not route to S12-P1", errors)
    require(manifest.get("legacy_s12_p1_dependency_validated") is True, "legacy S12-P1 flag mismatch", errors)

    progress = manifest.get("stage12_phase_progress", {})
    require(progress.get("completed_phase_count") == 1, "completed phase count mismatch", errors)
    require(progress.get("total_phase_count") == 3, "total phase count mismatch", errors)
    require(progress.get("derived_percent_bps") == 3333, "derived percent bps mismatch", errors)
    require(progress.get("derived_percent_label") == "33.33%", "derived percent label mismatch", errors)
    require(progress.get("s12_p1_performed") is True, "S12-P1 must be performed", errors)
    require(progress.get("s12_p2_performed") is False, "S12-P2 must be false", errors)
    require(progress.get("s12_p3_performed") is False, "S12-P3 must be false", errors)
    require(progress.get("stage12_review_performed") is False, "Stage 12 review must be false", errors)

    summary = manifest.get("manual_resolution_summary", {})
    require(summary.get("manual_event_count") == 5, "manual event count mismatch", errors)
    require(summary.get("manual_action_kind_count") == 4, "action kind count mismatch", errors)
    require(summary.get("event_type_count") == 4, "event type count mismatch", errors)
    require(summary.get("approved_event_count") == 1, "approved event count mismatch", errors)
    require(summary.get("reverse_event_count") == 1, "reverse event count mismatch", errors)
    require(summary.get("html_export_count") == 1, "HTML export count mismatch", errors)
    require(summary.get("field_mapping_event_present") is True, "field mapping event missing", errors)
    require(summary.get("project_matching_event_present") is True, "project matching event missing", errors)
    require(summary.get("difference_handling_event_present") is True, "difference handling event missing", errors)
    require(summary.get("note_event_present") is True, "note event missing", errors)
    require(summary.get("approved_event_reversal_chain_present") is True, "reverse chain missing", errors)
    for key in (
        "raw_layer_write_count",
        "source_mutation_count",
        "business_plaintext_count",
        "impact_preview_publish_count",
        "derived_rerun_count",
        "formal_report_count",
        "business_decision_basis_count",
        "github_upload_count",
    ):
        require(summary.get(key) == 0, f"summary.{key} must be 0", errors)
    require(events == legacy["events"], "v014 event records must replay legacy public-safe S12-P1 events", errors)
    require(summary.get("manual_event_count") == legacy["manual_event_count"], "legacy event count mismatch", errors)
    require(manifest.get("required_manual_action_kinds") == list(REQUIRED_MANUAL_ACTION_KINDS), "required action kinds mismatch", errors)

    v14 = manifest.get("v14_html_uiux_baseline", {})
    for key, expected in baseline.items():
        if key in {
            "implementation_reflects_manual_resolution_workbench",
            "implementation_reflects_visible_feedback",
            "implementation_reflects_no_raw_mutation",
        }:
            continue
        require(v14.get(key) == expected, f"v14 baseline {key} mismatch", errors)
    require(v14.get("taskpack_html_requirement_read") is True, "HTML requirement read mismatch", errors)
    require(v14.get("audit_file_count") == 6, "v14 audit file count mismatch", errors)
    require(v14.get("audit_control_row_count") == 54, "v14 audit row count mismatch", errors)
    require(v14.get("audit_pass_count") == 54, "v14 audit pass count mismatch", errors)
    require(v14.get("audit_warn_count") == 0, "v14 audit warn count mismatch", errors)
    require(v14.get("audit_fail_count") == 0, "v14 audit fail count mismatch", errors)
    require(
        v14.get("implementation_reflects_manual_resolution_workbench") is True,
        "manual workbench reflection mismatch",
        errors,
    )
    require(v14.get("implementation_reflects_visible_feedback") is True, "visible feedback reflection mismatch", errors)
    require(v14.get("implementation_reflects_no_raw_mutation") is True, "no raw mutation reflection mismatch", errors)

    require("<button" in html_text, "HTML must expose actionable buttons", errors)
    require("aria-live=\"polite\"" in html_text, "HTML must expose visible feedback region", errors)
    require("addEventListener" in html_text, "HTML must include click feedback wiring", errors)
    for required_text in ("字段映射", "项目匹配", "差异处理", "备注", "影响预览", "重跑链路", "禁止静默改写"):
        require(required_text in html_text, f"HTML missing required text {required_text}", errors)

    phase = manifest.get("phase_boundaries", {})
    for key in PHASE_TRUE_KEYS:
        require(phase.get(key) is True, f"phase_boundaries.{key} must be true", errors)
    for key in PHASE_FALSE_KEYS:
        require(phase.get(key) is False, f"phase_boundaries.{key} must be false", errors)

    quality = manifest.get("quality_gate", {})
    require(quality.get("current_data_quality_grade") == "Q4", "quality grade mismatch", errors)
    require(quality.get("current_report_grade") == "D", "report grade mismatch", errors)
    require(quality.get("release_permission") == "blocked", "release permission mismatch", errors)
    require(quality.get("pending_reconciliation_count") == 12, "pending reconciliation count mismatch", errors)
    require(quality.get("confirmed_resolution_count") == 0, "confirmed resolution count mismatch", errors)
    for key in QUALITY_TRUE_KEYS:
        require(quality.get(key) is True, f"quality_gate.{key} must be true", errors)
    for key in QUALITY_FALSE_KEYS:
        require(quality.get(key) is False, f"quality_gate.{key} must be false", errors)

    raw = manifest.get("raw_data_boundary", {})
    require(raw.get("raw_inbox_role") == "user_finance_raw_private_inbox", "raw role mismatch", errors)
    require(raw.get("raw_inbox_read_allowed_only_when_phase_requires") is True, "raw read policy mismatch", errors)
    for key in RAW_BOUNDARY_FALSE_KEYS:
        require(raw.get(key) is False, f"raw_data_boundary.{key} must be false", errors)

    public = manifest.get("public_repo_safety", {})
    for key in PUBLIC_SAFETY_FALSE_KEYS:
        require(public.get(key) is False, f"public_repo_safety.{key} must be false", errors)
    for key in PUBLIC_SAFETY_TRUE_KEYS:
        require(public.get(key) is True, f"public_repo_safety.{key} must be true", errors)

    upload = manifest.get("github_upload", {})
    require(upload.get("github_upload_ready_next_gate") is False, "upload ready must be false", errors)
    require(upload.get("github_upload_deferred_until_v014_stage1_18_complete") is True, "upload defer mismatch", errors)
    require(upload.get("github_upload_performed") is False, "upload performed must be false", errors)
    require(
        upload.get("github_upload_status") == "not_uploaded_deferred_until_v014_stage1_18_complete",
        "upload status mismatch",
        errors,
    )

    hard_blocks = set(manifest.get("hard_blocks", []))
    for block in REQUIRED_HARD_BLOCKS:
        require(block in hard_blocks, f"missing hard block: {block}", errors)
    require(manifest.get("next_phase") == "S12-P2", "next phase mismatch", errors)
    require(manifest.get("next_required_step") == NEXT_REQUIRED_STEP, "next instruction mismatch", errors)
    require("S12-P3 derived rerun" in manifest.get("non_goals", []), "S12-P3 non-goal missing", errors)
    require("GitHub upload" in manifest.get("non_goals", []), "GitHub upload non-goal missing", errors)
    require("business execution" in manifest.get("non_goals", []), "business execution non-goal missing", errors)

    for path in (REPORT_PATH, TEST_RESULTS_PATH, RISK_REGISTER_PATH, ROLLBACK_PATH, MANIFEST_PATH, EVENTS_PATH, HTML_OUTPUT_PATH):
        check_public_evidence_text(path, errors)

    branch = git_output(["branch", "--show-current"])
    remote = git_output(["remote", "get-url", "origin"])
    git_info = manifest.get("git", {})
    require(git_info.get("branch") == branch, "git branch mismatch", errors)
    manifest_head = str(git_info.get("head", ""))
    require(re.fullmatch(r"[0-9a-f]{40}", manifest_head) is not None, "git head format mismatch", errors)
    require(git_info.get("remote") == remote, "git remote mismatch", errors)

    if errors:
        raise ValidationError("\n".join(errors))
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.4 S12-P1 manual resolution events.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args(argv)
    manifest = validate_v014_s12_p1_manual_resolution_events(args.manifest)
    summary = manifest["manual_resolution_summary"]
    print(
        "PASS: KMFA v0.1.4 S12-P1 manual resolution events validated "
        f"(events={summary['manual_event_count']}, action_kinds={summary['manual_action_kind_count']}, "
        f"reverse_events={summary['reverse_event_count']}, html_exports={summary['html_export_count']}, "
        "s12_p2=false, s12_p3=false, stage12_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
