#!/usr/bin/env python3
"""Validate KMFA v0.1.4 S16-P1 subcontract procurement evidence."""

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

from KMFA.tools.v014_s16_p1_subcontract_procurement import (  # noqa: E402
    ACCEPTANCE_ID,
    ANOMALY_CANDIDATE_LOCK_PATH,
    MANIFEST_PATH,
    NEXT_PHASE,
    NEXT_REQUIRED_STEP,
    PHASE_SCOPE,
    PROJECT_MATCH_LOCK_PATH,
    REPORT_PATH,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
    SCHEMA_VERSION,
    SOURCE_LANE_LOCK_PATH,
    TASK_ID,
    TEST_RESULTS_PATH,
    UNALLOCATED_POOL_LOCK_PATH,
    _phase_boundaries,
    _public_repo_safety,
    _quality_gate,
    _raw_boundary,
    load_v14_taskpack_baseline,
    validate_legacy_s16_p1_artifacts,
    validate_s15_stage_review_dependency,
)


PUBLIC_SAFETY_FALSE_KEYS = tuple(key for key, value in _public_repo_safety().items() if value is False)
RAW_BOUNDARY_FALSE_KEYS = tuple(key for key, value in _raw_boundary().items() if value is False)
QUALITY_FALSE_KEYS = tuple(key for key, value in _quality_gate().items() if value is False)
QUALITY_TRUE_KEYS = tuple(key for key, value in _quality_gate().items() if value is True)
PHASE_FALSE_KEYS = tuple(key for key, value in _phase_boundaries().items() if value is False)
PHASE_TRUE_KEYS = tuple(key for key, value in _phase_boundaries().items() if value is True)

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


def _check_lock_rows(rows: list[dict[str, Any]], expected_count: int, record_type: str, errors: list[str]) -> None:
    require(len(rows) == expected_count, f"{record_type} row count must be {expected_count}", errors)
    for row in rows:
        require(row.get("record_type") == record_type, f"{record_type} record_type mismatch", errors)
        require(row.get("project_id") == "KMFA", f"{record_type} project_id mismatch", errors)
        require(row.get("stage_id") == "S16", f"{record_type} stage_id mismatch", errors)
        require(row.get("phase_id") == "S16-P1", f"{record_type} phase_id mismatch", errors)
        _require_false_keys(
            row,
            (
                "raw_business_values_allowed",
                "public_numeric_values_allowed",
                "field_plaintext_allowed",
                "formal_report_allowed",
                "business_decision_basis_allowed",
                "procurement_execution_allowed",
                "payment_execution_allowed",
                "bank_operation_allowed",
            ),
            record_type,
            errors,
        )


def validate_v014_s16_p1_subcontract_procurement(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []
    manifest = read_json(manifest_path)
    source_lane_locks = read_jsonl(SOURCE_LANE_LOCK_PATH)
    project_match_locks = read_jsonl(PROJECT_MATCH_LOCK_PATH)
    unallocated_pool_locks = read_jsonl(UNALLOCATED_POOL_LOCK_PATH)
    anomaly_candidate_locks = read_jsonl(ANOMALY_CANDIDATE_LOCK_PATH)

    s15_review = validate_s15_stage_review_dependency()
    legacy_manifest, legacy_lanes, legacy_matches, legacy_pool, legacy_anomalies = validate_legacy_s16_p1_artifacts()
    baseline = load_v14_taskpack_baseline()
    legacy_summary = legacy_manifest["summary"]

    require(manifest.get("schema_version") == SCHEMA_VERSION, "manifest schema mismatch", errors)
    require(manifest.get("project_id") == "KMFA", "project_id mismatch", errors)
    require(manifest.get("version") == "0.1.4", "version mismatch", errors)
    require(manifest.get("stage_id") == "S16", "stage_id must be S16", errors)
    require(manifest.get("phase_id") == "S16-P1", "phase_id must be S16-P1", errors)
    require(manifest.get("phase_scope") == PHASE_SCOPE, "phase scope mismatch", errors)
    require(manifest.get("task_id") == TASK_ID, "task id mismatch", errors)
    require(manifest.get("acceptance_ids") == [ACCEPTANCE_ID], "acceptance id mismatch", errors)
    require(manifest.get("completed_task_ids") == ["S16P1T01", "S16P1T02", "S16P1T03"], "tasks mismatch", errors)
    require(
        manifest.get("status") == "completed_validated_local_only_no_go_upload_deferred_subcontract_procurement_locked",
        "status mismatch",
        errors,
    )
    require(
        manifest.get("s15_stage_review_dependency_validated") is True,
        "Stage 15 review dependency flag mismatch",
        errors,
    )
    require(
        manifest.get("historical_s16_p1_public_safe_baseline_validated") is True,
        "historical S16-P1 baseline flag mismatch",
        errors,
    )
    require(s15_review.get("next_phase") == "S16-P1", "Stage 15 review did not route to S16-P1", errors)
    require(legacy_summary.get("source_lane_count") == 4, "legacy source lane count mismatch", errors)
    require(len(legacy_lanes) == 4, "legacy lane artifact count mismatch", errors)
    require(len(legacy_matches) == 5, "legacy match artifact count mismatch", errors)
    require(len(legacy_pool) == 2, "legacy pool artifact count mismatch", errors)
    require(len(legacy_anomalies) == 4, "legacy anomaly artifact count mismatch", errors)
    require(baseline.get("roadmap_includes_s16_p1_requirements") is True, "v1.4 roadmap baseline mismatch", errors)
    require(
        baseline.get("taskpack_includes_subcontract_procurement_payment_line") is True,
        "v1.4 taskpack baseline mismatch",
        errors,
    )

    progress = manifest.get("stage16_phase_progress", {})
    require(progress.get("completed_phase_count") == 1, "completed phase count mismatch", errors)
    require(progress.get("total_phase_count") == 3, "total phase count mismatch", errors)
    require(progress.get("derived_percent_bps") == 3333, "derived percent bps mismatch", errors)
    require(progress.get("derived_percent_label") == "33.33%", "derived percent label mismatch", errors)
    require(progress.get("s16_p1_performed") is True, "S16-P1 must be true", errors)
    require(progress.get("s16_p2_performed") is False, "S16-P2 must be false", errors)
    require(progress.get("s16_p3_performed") is False, "S16-P3 must be false", errors)
    require(progress.get("stage16_review_performed") is False, "Stage 16 review must be false", errors)

    expected_summary = {
        "source_lane_count": 4,
        "project_match_count": 5,
        "matched_to_project_count": 2,
        "cross_project_match_count": 1,
        "unmatched_project_count": 2,
        "unallocated_cost_pool_count": 2,
        "anomaly_candidate_count": 4,
        "duplicate_payment_candidate_count": 2,
        "cross_project_cost_candidate_count": 2,
        "pending_reconciliation_count": 12,
        "report_grade_visible": "D",
        "procurement_execution_count": 0,
        "payment_approval_count": 0,
        "payment_execution_count": 0,
        "bank_operation_count": 0,
        "formal_report_count": 0,
        "business_decision_basis_count": 0,
    }
    summary = manifest.get("subcontract_procurement_summary", {})
    for key, expected in expected_summary.items():
        require(summary.get(key) == expected, f"summary {key} must be {expected!r}", errors)

    quality = manifest.get("quality_gate", {})
    for key in QUALITY_TRUE_KEYS:
        require(quality.get(key) is True, f"quality_gate {key} must be true", errors)
    for key in QUALITY_FALSE_KEYS:
        require(quality.get(key) is False, f"quality_gate {key} must be false", errors)
    require(quality.get("current_report_grade") == "D", "current report grade mismatch", errors)
    require(quality.get("release_permission") == "blocked", "release permission mismatch", errors)

    boundaries = manifest.get("phase_boundaries", {})
    for key in PHASE_TRUE_KEYS:
        require(boundaries.get(key) is True, f"phase_boundaries {key} must be true", errors)
    for key in PHASE_FALSE_KEYS:
        require(boundaries.get(key) is False, f"phase_boundaries {key} must be false", errors)

    raw = manifest.get("raw_data_boundary", {})
    for key in RAW_BOUNDARY_FALSE_KEYS:
        require(raw.get(key) is False, f"raw boundary {key} must be false", errors)

    safety = manifest.get("public_repo_safety", {})
    for key in PUBLIC_SAFETY_FALSE_KEYS:
        require(safety.get(key) is False, f"public safety {key} must be false", errors)

    upload = manifest.get("github_upload", {})
    require(upload.get("github_upload_performed") is False, "GitHub upload must be false", errors)
    require(upload.get("github_upload_ready_next_gate") is False, "GitHub upload ready gate must be false", errors)
    require(
        upload.get("github_upload_deferred_until_v014_stage1_18_complete") is True,
        "GitHub upload deferral flag must be true",
        errors,
    )
    require(upload.get("github_upload_status") == "not_uploaded_deferred_until_v014_stage1_18_complete", "upload status mismatch", errors)
    require(manifest.get("next_phase") == NEXT_PHASE, "next phase mismatch", errors)
    require(manifest.get("next_required_step") == NEXT_REQUIRED_STEP, "next required step mismatch", errors)

    require(re.match(r"^[0-9a-f]{40}$", str(manifest.get("git_head"))), "git head must be a full SHA", errors)
    require(manifest.get("branch") == git_output(["branch", "--show-current"]), "branch mismatch", errors)

    _check_lock_rows(source_lane_locks, 4, "v014_s16_p1_source_lane_lock", errors)
    _check_lock_rows(project_match_locks, 5, "v014_s16_p1_project_match_lock", errors)
    _check_lock_rows(unallocated_pool_locks, 2, "v014_s16_p1_unallocated_pool_lock", errors)
    _check_lock_rows(anomaly_candidate_locks, 4, "v014_s16_p1_anomaly_candidate_lock", errors)

    for row in source_lane_locks:
        require(row.get("all_sources_readonly") is True, "source lanes must be readonly", errors)
        require(int(row.get("source_count", 0)) >= 1, "source lane source_count must be positive", errors)
        require(int(row.get("field_mapping_count", 0)) >= 1, "source lane field_mapping_count must be positive", errors)
    require(
        sum(1 for row in anomaly_candidate_locks if row.get("candidate_type") == "duplicate_payment_candidate") == 2,
        "duplicate candidate lock count mismatch",
        errors,
    )
    require(
        sum(1 for row in anomaly_candidate_locks if row.get("candidate_type") == "cross_project_cost_candidate") == 2,
        "cross project candidate lock count mismatch",
        errors,
    )

    for path in (
        MANIFEST_PATH,
        SOURCE_LANE_LOCK_PATH,
        PROJECT_MATCH_LOCK_PATH,
        UNALLOCATED_POOL_LOCK_PATH,
        ANOMALY_CANDIDATE_LOCK_PATH,
        REPORT_PATH,
        TEST_RESULTS_PATH,
        RISK_REGISTER_PATH,
        ROLLBACK_PATH,
    ):
        check_public_evidence_text(path, errors)

    if errors:
        raise ValidationError("; ".join(errors))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args()
    manifest = validate_v014_s16_p1_subcontract_procurement(args.manifest)
    summary = manifest["subcontract_procurement_summary"]
    print(
        "PASS: KMFA v0.1.4 S16-P1 subcontract procurement validated "
        f"(source_lanes={summary['source_lane_count']}, project_matches={summary['project_match_count']}, "
        f"unallocated_pool={summary['unallocated_cost_pool_count']}, "
        f"duplicate_payment_candidates={summary['duplicate_payment_candidate_count']}, "
        f"cross_project_candidates={summary['cross_project_cost_candidate_count']}, "
        f"report_grade={summary['report_grade_visible']}, payment_execution={summary['payment_execution_count']}, "
        f"bank_operation={summary['bank_operation_count']}, s16_p2={manifest['stage16_phase_progress']['s16_p2_performed']}, "
        f"s16_p3={manifest['stage16_phase_progress']['s16_p3_performed']}, "
        f"github_upload={manifest['github_upload']['github_upload_performed']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
