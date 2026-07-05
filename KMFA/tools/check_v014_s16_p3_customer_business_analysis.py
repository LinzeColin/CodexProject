#!/usr/bin/env python3
"""Validate KMFA v0.1.4 S16-P3 customer business analysis evidence."""

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

from KMFA.tools.v014_s16_p3_customer_business_analysis import (  # noqa: E402
    ACCEPTANCE_ID,
    HANDOFF_GUARD_LOCK_PATH,
    MANIFEST_PATH,
    NEXT_PHASE,
    NEXT_REQUIRED_STEP,
    PHASE_SCOPE,
    PRIVATE_RUNTIME_REPORT_PATH,
    REPORT_PATH,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
    RISK_SIGNAL_LOCK_PATH,
    SCHEMA_VERSION,
    SOURCE_LANE_LOCK_PATH,
    SUMMARY_LOCK_PATH,
    TASK_ID,
    TEST_RESULTS_PATH,
    VALUE_SIGNAL_LOCK_PATH,
    _phase_boundaries,
    _public_repo_safety,
    _quality_gate,
    load_v14_taskpack_customer_line,
    validate_s16_p2_dependency,
    validate_upstream_public_safe_fact_dependencies,
)


PUBLIC_SAFETY_FALSE_KEYS = tuple(key for key, value in _public_repo_safety().items() if value is False)
QUALITY_FALSE_KEYS = tuple(key for key, value in _quality_gate().items() if value is False)
QUALITY_TRUE_KEYS = tuple(key for key, value in _quality_gate().items() if value is True)
PHASE_FALSE_KEYS = tuple(key for key, value in _phase_boundaries().items() if value is False)
PHASE_TRUE_KEYS = tuple(key for key, value in _phase_boundaries().items() if value is True)
RAW_ALIGNMENT_FALSE_KEYS = (
    "raw_inbox_modified_by_this_phase",
    "raw_inbox_deleted_by_this_phase",
    "raw_inbox_moved_by_this_phase",
    "raw_inbox_renamed_by_this_phase",
    "raw_inbox_overwritten_by_this_phase",
    "raw_inbox_written_by_this_phase",
    "raw_inbox_mutated_by_this_phase",
    "raw_business_values_committed",
    "raw_file_names_committed",
    "raw_hashes_committed",
    "field_header_plaintext_committed",
    "private_runtime_report_committed",
)
REQUIRED_HARD_BLOCKS = (
    "report_grade_d_only",
    "pending_reconciliation_blocks_formal_report",
    "raw_data_mutation_forbidden",
    "source_payload_publication_forbidden",
    "field_header_plaintext_publication_forbidden",
    "customer_plaintext_publication_forbidden",
    "business_amount_publication_forbidden",
    "formal_report_release_blocked",
    "business_decision_basis_blocked",
    "automatic_customer_ranking_blocked",
    "customer_contact_action_blocked",
    "collection_action_blocked",
    "legal_collection_decision_blocked",
    "payment_or_bank_operation_blocked",
    "invoice_operation_blocked",
    "tax_filing_blocked",
    "stage16_review_not_performed",
    "s17_not_performed",
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
    "tax_filing_material",
    "tax_filing_record",
    "connector_" + "token:",
    "connector_" + "pass" + "word:",
    "api" + "_key:",
    "private" + "_key:",
    "-----" "BEGIN",
    "s" "k-",
    "project_name_plaintext",
    "customer_name_plaintext",
    "counterparty_plaintext",
    "company_entity_plaintext",
    "supplier_name_plaintext",
    "payment_account",
    "account_number:",
    "invoice_number:",
    "tax_identifier:",
    "private_ref://",
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
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValidationError(f"{path} contains a non-object JSONL row")
        rows.append(value)
    return rows


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


def _require_false_keys(record: dict[str, Any], keys: tuple[str, ...], label: str, errors: list[str]) -> None:
    for key in keys:
        require(record.get(key) is False, f"{label}.{key} must be false", errors)


def _require_true_keys(record: dict[str, Any], keys: tuple[str, ...], label: str, errors: list[str]) -> None:
    for key in keys:
        require(record.get(key) is True, f"{label}.{key} must be true", errors)


def _check_rows(
    rows: list[dict[str, Any]],
    expected_count: int,
    record_type: str,
    errors: list[str],
) -> None:
    require(len(rows) == expected_count, f"{record_type} row count must be {expected_count}", errors)
    for row in rows:
        require(row.get("record_type") == record_type, f"{record_type} record_type mismatch", errors)
        require(row.get("project_id") == "KMFA", f"{record_type} project_id mismatch", errors)
        require(row.get("stage_id") == "S16", f"{record_type} stage_id mismatch", errors)
        require(row.get("phase_id") == "S16-P3", f"{record_type} phase_id mismatch", errors)
        _require_false_keys(
            row,
            (
                "raw_business_values_allowed",
                "formal_report_allowed",
                "business_decision_basis_allowed",
            ),
            record_type,
            errors,
        )


def _check_private_runtime_status(errors: list[str]) -> None:
    if PRIVATE_RUNTIME_REPORT_PATH.exists():
        result = subprocess.run(
            ["git", "check-ignore", "-q", PRIVATE_RUNTIME_REPORT_PATH.as_posix()],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        require(result.returncode == 0, "private runtime raw alignment report must stay git-ignored", errors)


def validate_v014_s16_p3_customer_business_analysis(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []
    manifest = read_json(manifest_path)
    source_lanes = read_jsonl(SOURCE_LANE_LOCK_PATH)
    value_signals = read_jsonl(VALUE_SIGNAL_LOCK_PATH)
    risk_signals = read_jsonl(RISK_SIGNAL_LOCK_PATH)
    customer_summaries = read_jsonl(SUMMARY_LOCK_PATH)
    handoff_guards = read_jsonl(HANDOFF_GUARD_LOCK_PATH)

    s16_p2 = validate_s16_p2_dependency()
    upstream = validate_upstream_public_safe_fact_dependencies()
    taskpack = load_v14_taskpack_customer_line()

    require(manifest.get("schema_version") == SCHEMA_VERSION, "manifest schema mismatch", errors)
    require(manifest.get("project_id") == "KMFA", "project_id mismatch", errors)
    require(manifest.get("version") == "0.1.4", "version mismatch", errors)
    require(manifest.get("stage_id") == "S16", "stage_id must be S16", errors)
    require(manifest.get("phase_id") == "S16-P3", "phase_id must be S16-P3", errors)
    require(manifest.get("phase_scope") == PHASE_SCOPE, "phase scope mismatch", errors)
    require(manifest.get("task_id") == TASK_ID, "task id mismatch", errors)
    require(manifest.get("acceptance_ids") == [ACCEPTANCE_ID], "acceptance id mismatch", errors)
    require(manifest.get("completed_task_ids") == ["S16P3T01", "S16P3T02", "S16P3T03"], "tasks mismatch", errors)
    require(
        manifest.get("status") == "completed_validated_local_only_no_go_upload_deferred_customer_business_analysis_locked",
        "status mismatch",
        errors,
    )
    require(manifest.get("s16_p2_dependency_validated") is True, "S16-P2 dependency flag mismatch", errors)
    require(s16_p2.get("next_phase") == "S16-P3", "S16-P2 did not route to S16-P3", errors)
    require(
        manifest.get("upstream_public_safe_fact_dependencies_validated") is True,
        "upstream public-safe dependency flag mismatch",
        errors,
    )
    require(
        manifest.get("v14_taskpack_customer_line_validated") is True,
        "v1.4 taskpack customer line flag mismatch",
        errors,
    )
    require(taskpack.get("roadmap_includes_s16_p3_requirements") is True, "v1.4 roadmap baseline mismatch", errors)
    require(
        taskpack.get("taskpack_includes_customer_business_analysis_line") is True,
        "v1.4 taskpack baseline mismatch",
        errors,
    )

    progress = manifest.get("stage16_phase_progress", {})
    require(progress.get("completed_phase_count") == 3, "completed phase count mismatch", errors)
    require(progress.get("total_phase_count") == 3, "total phase count mismatch", errors)
    require(progress.get("derived_percent_bps") == 10000, "derived percent bps mismatch", errors)
    require(progress.get("derived_percent_label") == "100.00%", "derived percent label mismatch", errors)
    require(progress.get("s16_p1_performed") is True, "S16-P1 must be true", errors)
    require(progress.get("s16_p2_performed") is True, "S16-P2 must be true", errors)
    require(progress.get("s16_p3_performed") is True, "S16-P3 must be true", errors)
    require(progress.get("stage16_review_performed") is False, "Stage 16 review must be false", errors)

    expected_summary = {
        "source_lane_count": 7,
        "customer_value_dimension_count": 4,
        "customer_value_signal_count": 4,
        "customer_risk_signal_count": 4,
        "customer_summary_count": 4,
        "handoff_guard_count": 4,
        "project_margin_signal_count": 4,
        "collection_quality_signal_count": 4,
        "aging_risk_signal_count": 4,
        "pending_reconciliation_count": 12,
        "report_grade_visible": "D",
        "formal_report_count": 0,
        "business_decision_basis_count": 0,
        "automatic_customer_ranking_count": 0,
        "customer_contact_action_count": 0,
        "collection_action_count": 0,
        "legal_collection_decision_count": 0,
        "invoice_issuance_count": 0,
        "tax_filing_count": 0,
        "payment_execution_count": 0,
        "bank_operation_count": 0,
        "customer_plaintext_count": 0,
        "public_amount_value_count": 0,
        "raw_publication_count": 0,
    }
    summary = manifest.get("customer_business_analysis_summary", {})
    for key, expected in expected_summary.items():
        require(summary.get(key) == expected, f"customer_business_analysis_summary.{key} mismatch", errors)
    require(
        summary.get("cross_table_review_dimension_count") == upstream["cross_table_review_dimension_count"],
        "cross table review dimension count mismatch",
        errors,
    )

    deps = manifest.get("upstream_public_safe_fact_dependencies", {})
    for key in (
        "s08_p2_entity_dependency_validated",
        "s09_p2_margin_dependency_validated",
        "s13_p2_receivable_dependency_validated",
        "s13_p3_cross_table_dependency_validated",
    ):
        require(deps.get(key) is True, f"upstream dependency {key} must be true", errors)
    require(deps.get("pending_reconciliation_count") == 12, "upstream pending reconciliation mismatch", errors)

    quality = manifest.get("quality_gate", {})
    _require_true_keys(quality, QUALITY_TRUE_KEYS, "quality_gate", errors)
    _require_false_keys(quality, QUALITY_FALSE_KEYS, "quality_gate", errors)
    boundaries = manifest.get("phase_boundaries", {})
    _require_true_keys(boundaries, PHASE_TRUE_KEYS, "phase_boundaries", errors)
    _require_false_keys(boundaries, PHASE_FALSE_KEYS, "phase_boundaries", errors)
    _require_false_keys(manifest.get("public_repo_safety", {}), PUBLIC_SAFETY_FALSE_KEYS, "public_repo_safety", errors)
    _require_false_keys(manifest.get("raw_private_alignment", {}), RAW_ALIGNMENT_FALSE_KEYS, "raw_private_alignment", errors)
    require(
        manifest.get("raw_private_alignment", {}).get("raw_private_alignment_attempted_by_this_phase") is True,
        "raw private alignment attempted flag mismatch",
        errors,
    )
    require(
        manifest.get("raw_private_alignment", {}).get("raw_inbox_readonly_contract_preserved") is True,
        "raw readonly contract flag mismatch",
        errors,
    )

    upload = manifest.get("github_upload", {})
    require(upload.get("github_upload_performed") is False, "GitHub upload must be false", errors)
    require(upload.get("github_upload_ready_next_gate") is False, "GitHub upload ready gate must be false", errors)
    require(
        upload.get("github_upload_deferred_until_v014_stage1_18_complete") is True,
        "GitHub upload deferral mismatch",
        errors,
    )
    require(manifest.get("next_phase") == NEXT_PHASE, "next phase mismatch", errors)
    require(manifest.get("next_required_step") == NEXT_REQUIRED_STEP, "next required step mismatch", errors)

    for required in REQUIRED_HARD_BLOCKS:
        require(required in manifest.get("hard_blocks", []), f"missing hard block: {required}", errors)

    _check_rows(source_lanes, 7, "customer_business_source_lane", errors)
    _check_rows(value_signals, 4, "customer_value_signal", errors)
    _check_rows(risk_signals, 4, "customer_risk_signal", errors)
    _check_rows(customer_summaries, 4, "customer_business_summary", errors)
    _check_rows(handoff_guards, 4, "customer_business_handoff_guard", errors)

    for row in value_signals:
        require(row.get("automatic_customer_ranking_allowed") is False, "value signal ranking must be false", errors)
        require(row.get("customer_plaintext_allowed") is False, "value signal customer plaintext must be false", errors)
    for row in risk_signals:
        require(row.get("collection_action_allowed") is False, "risk signal collection action must be false", errors)
        require(
            row.get("legal_collection_decision_allowed") is False,
            "risk signal legal decision must be false",
            errors,
        )
    for row in customer_summaries:
        require(row.get("customer_contact_action_allowed") is False, "summary customer contact must be false", errors)

    for path in (
        MANIFEST_PATH,
        SOURCE_LANE_LOCK_PATH,
        VALUE_SIGNAL_LOCK_PATH,
        RISK_SIGNAL_LOCK_PATH,
        SUMMARY_LOCK_PATH,
        HANDOFF_GUARD_LOCK_PATH,
        REPORT_PATH,
        TEST_RESULTS_PATH,
        RISK_REGISTER_PATH,
        ROLLBACK_PATH,
    ):
        check_public_evidence_text(path, errors)
    _check_private_runtime_status(errors)

    if errors:
        raise ValidationError("\n".join(errors))
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.4 S16-P3 customer business analysis evidence.")
    parser.parse_args(argv)
    try:
        manifest = validate_v014_s16_p3_customer_business_analysis()
    except ValidationError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    summary = manifest["customer_business_analysis_summary"]
    print(
        "PASS: KMFA v0.1.4 S16-P3 customer business analysis validated "
        f"(source_lanes={summary['source_lane_count']}, "
        f"value_signals={summary['customer_value_signal_count']}, "
        f"risk_signals={summary['customer_risk_signal_count']}, "
        f"summaries={summary['customer_summary_count']}, "
        f"handoff_guards={summary['handoff_guard_count']}, "
        f"report_grade={summary['report_grade_visible']}, "
        f"collection_action={summary['collection_action_count']}, "
        f"legal_decision={summary['legal_collection_decision_count']}, "
        f"stage16_review={manifest['stage16_phase_progress']['stage16_review_performed']}, "
        f"github_upload={manifest['github_upload']['github_upload_performed']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
