#!/usr/bin/env python3
"""Validate KMFA v1.4 S03-P3 source priority evidence."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from KMFA.tools.check_v014_s03_p2_source_check_matrix import validate_v014_s03_p2_source_check_matrix
from KMFA.tools.source_priority import SOURCE_PRIORITY_ORDER
from KMFA.tools.v014_s03_p1_raw_file_registration import RAW_INBOX
from KMFA.tools.v014_s03_p3_source_priority import (
    ACCEPTANCE_ID,
    DIFFERENCE_QUEUE_PATH,
    MANIFEST_PATH,
    PRIORITY_RECORDS_PATH,
    PROTOCOL_PATH,
    REPORT_PATH,
    RISK_REGISTER_PATH,
    ROLLBACK_PLAN_PATH,
    SAME_SOURCE_EVENTS_PATH,
    TASK_ID,
    TEST_RESULTS_PATH,
)


FORBIDDEN_EXTENSIONS = {".zip", ".xlsx", ".xls", ".xlsm", ".pdf", ".sqlite", ".sqlite3", ".db"}
PUBLIC_FORBIDDEN_TEXT = (
    "original_filename",
    "relative_path",
    "content_sha256",
    "member_path",
    "sheet_name",
    "source_header_text",
    "raw_value:",
    "normalized_value:",
    "cell_value:",
    "row_value:",
    "bank_statement:",
    "contract_full_text:",
    "salary_detail:",
    "tax_filing:",
    "connector_token:",
    "connector_password:",
    "api_key:",
    "private_key:",
    "-----" "BEGIN",
    "s" "k-",
)
PUBLIC_SAFETY_FALSE_KEYS = (
    "raw_business_data_committed",
    "raw_filenames_committed",
    "raw_hashes_committed",
    "directory_tree_plaintext_committed",
    "zip_member_names_committed",
    "field_or_header_plaintext_committed",
    "raw_or_normalized_values_committed",
    "business_values_committed",
    "zip_committed",
    "excel_workbook_committed",
    "pdf_committed",
    "private_csv_committed",
    "sqlite_or_db_committed",
    "credentials_committed",
)
PHASE_SCOPE_FALSE_KEYS = (
    "raw_root_read_performed_by_this_phase",
    "raw_root_list_performed_by_this_phase",
    "raw_root_hash_performed_by_this_phase",
    "raw_root_mutation_performed",
    "stage3_review_performed",
    "github_upload_performed",
    "raw_value_matching_performed",
    "field_mapping_performed",
    "formal_report_performed",
    "business_execution_performed",
    "next_phase_started",
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
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValidationError(f"{path}:{line_number} must contain a JSON object")
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


def check_public_safe_file(path: Path, errors: list[str]) -> None:
    require(path.exists(), f"missing evidence file: {path}", errors)
    if not path.exists():
        return
    require(path.suffix.lower() not in FORBIDDEN_EXTENSIONS, f"forbidden evidence extension: {path}", errors)
    if path.suffix.lower() in {".md", ".json", ".jsonl", ".csv", ".yaml", ".yml", ".py"}:
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        for forbidden in PUBLIC_FORBIDDEN_TEXT:
            require(forbidden.lower() not in text, f"forbidden public text {forbidden!r} in {path}", errors)


def validate_v014_s03_p3_source_priority(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []
    manifest = read_json(manifest_path)
    priority_records = read_jsonl(PRIORITY_RECORDS_PATH)
    same_source_events = read_jsonl(SAME_SOURCE_EVENTS_PATH)
    difference_queue = read_jsonl(DIFFERENCE_QUEUE_PATH)
    protocol = read_json(PROTOCOL_PATH)
    s03_p2 = validate_v014_s03_p2_source_check_matrix()

    require(manifest.get("schema_version") == "kmfa.v014_s03_p3_source_priority.v1", "schema mismatch", errors)
    require(manifest.get("project_id") == "KMFA", "project_id mismatch", errors)
    require(manifest.get("version") == "0.1.4", "version mismatch", errors)
    require(manifest.get("stage_id") == "S03", "stage_id must be S03", errors)
    require(manifest.get("phase_id") == "S03-P3", "phase_id must be S03-P3", errors)
    require(manifest.get("task_id") == TASK_ID, "task_id mismatch", errors)
    require(manifest.get("acceptance_id") == ACCEPTANCE_ID, "acceptance_id mismatch", errors)
    require(manifest.get("status") == "completed_validated_local_only_no_go_upload_deferred", "status mismatch", errors)

    dependency = manifest.get("dependency", {})
    require(dependency.get("required_phase") == "V014_S03_P2_SOURCE_CHECK_MATRIX", "dependency phase mismatch", errors)
    require(dependency.get("dependency_validated") is True, "dependency_validated must be true", errors)
    require(s03_p2.get("phase_id") == "S03-P2", "S03-P2 validator phase mismatch", errors)
    require(s03_p2.get("status") == "completed_validated_local_only_no_go_upload_deferred", "S03-P2 status mismatch", errors)

    phase_scope = manifest.get("phase_scope", {})
    require(phase_scope.get("current_phase_only") is True, "current_phase_only must be true", errors)
    require(phase_scope.get("source_priority_only") is True, "source_priority_only must be true", errors)
    require(phase_scope.get("uses_s03_p2_public_matrix_only") is True, "S03-P2 public matrix dependency missing", errors)
    require(phase_scope.get("next_phase") == "S03_STAGE_REVIEW", "next phase mismatch", errors)
    for key in PHASE_SCOPE_FALSE_KEYS:
        require(phase_scope.get(key) is False, f"phase_scope.{key} must be false", errors)

    summary = manifest.get("source_priority_summary", {})
    require(summary.get("source_priority_record_count") == len(priority_records) == 5, "priority record count mismatch", errors)
    require(summary.get("source_priority_order") == list(SOURCE_PRIORITY_ORDER), "source priority order mismatch", errors)
    require(summary.get("source_priority_order_count") == len(SOURCE_PRIORITY_ORDER) == 9, "priority order count mismatch", errors)
    require(summary.get("s03_p2_matrix_row_count") == 5, "S03-P2 matrix dependency count mismatch", errors)
    require(summary.get("s03_p2_status_event_count") == 5, "S03-P2 status dependency count mismatch", errors)
    require(summary.get("same_source_policy_event_count") == len(same_source_events) == 1, "same-source event count mismatch", errors)
    require(
        summary.get("same_source_inconsistency_actions") == ["invalidate_derived_cache", "request_rerun"],
        "same-source action mismatch",
        errors,
    )
    require(summary.get("same_source_cache_reuse_allowed") is False, "same-source cache reuse must be false", errors)
    require(
        summary.get("cross_source_difference_queue_item_count") == len(difference_queue) == 1,
        "difference queue count mismatch",
        errors,
    )
    require(summary.get("cross_source_resolution_policy") == "manual_review_required", "resolution policy mismatch", errors)
    require(summary.get("highest_priority_source_class_counts", {}).get("raw_upload") == 5, "raw upload priority count mismatch", errors)
    require(summary.get("processed_data_after_raw_or_authorized_count") == 5, "processed data priority boundary mismatch", errors)
    require(summary.get("manual_review_required_count") == 5, "manual review count mismatch", errors)
    require(summary.get("auto_selection_allowed") is False, "summary auto selection must be false", errors)
    require(summary.get("policy_fixture_only") is True, "policy fixture flag must be true", errors)
    require(summary.get("business_conflict_observed_count") == 0, "business conflict observed count must be zero", errors)

    seen_record_ids: set[str] = set()
    for record in priority_records:
        require(record.get("record_type") == "source_priority_record", "priority record_type mismatch", errors)
        require(record.get("schema_version") == "kmfa.v014_s03_p3.source_priority_record.v1", "priority schema mismatch", errors)
        require(record.get("stage_phase") == "S03-P3", "priority phase mismatch", errors)
        require(re.fullmatch(r"SPR-V014-S03P3-[a-f0-9]{16}", str(record.get("priority_record_id"))) is not None, "priority id mismatch", errors)
        require(record.get("priority_record_id") not in seen_record_ids, "duplicate priority record id", errors)
        seen_record_ids.add(str(record.get("priority_record_id")))
        require(record.get("source_check_status") == "人工复核", "source check status must remain manual review", errors)
        require(record.get("source_priority_order") == list(SOURCE_PRIORITY_ORDER), "record priority order mismatch", errors)
        candidates = record.get("candidate_refs", [])
        require(isinstance(candidates, list) and len(candidates) == 3, "candidate_refs must contain three public-safe refs", errors)
        candidate_classes = [item.get("source_class") for item in candidates if isinstance(item, dict)]
        require(candidate_classes == ["raw_upload", "authorized_export", "processed_data"], "candidate class order mismatch", errors)
        candidate_ranks = [item.get("priority_rank") for item in candidates if isinstance(item, dict)]
        require(candidate_ranks == [10, 20, 90], "candidate rank order mismatch", errors)
        require(record.get("highest_priority_source_class") == "raw_upload", "highest priority must be raw_upload", errors)
        require(record.get("priority_decision_status") == "priority_locked_manual_review_pending", "priority decision status mismatch", errors)
        require(record.get("processed_data_rank_after_raw_or_authorized") is True, "processed-data priority boundary false", errors)
        require(record.get("manual_review_required") is True, "manual review required must be true", errors)
        require(record.get("auto_selection_allowed") is False, "priority auto selection must be false", errors)
        require(record.get("target_layer") == "metadata", "priority target layer must be metadata", errors)
        for key in (
            "raw_root_read_performed_by_this_phase",
            "raw_layer_write_allowed",
            "raw_source_mutation_allowed",
            "raw_filename_committed",
            "raw_hash_committed",
            "field_or_header_plaintext_committed",
            "raw_or_normalized_value_committed",
            "business_value_committed",
        ):
            require(record.get(key) is False, f"priority record {key} must be false", errors)

    same_source = same_source_events[0] if same_source_events else {}
    require(same_source.get("record_type") == "source_priority_event", "same-source record type mismatch", errors)
    require(same_source.get("schema_version") == "kmfa.v014_s03_p3.same_source_rerun_event.v1", "same-source schema mismatch", errors)
    require(same_source.get("event_type") == "same_source_inconsistency", "same-source event type mismatch", errors)
    require(same_source.get("actions") == ["invalidate_derived_cache", "request_rerun"], "same-source actions mismatch", errors)
    require(same_source.get("cache_reuse_allowed") is False, "same-source cache reuse must be false", errors)
    require(same_source.get("target_layer") == "metadata", "same-source target layer must be metadata", errors)
    require(same_source.get("raw_layer_write_allowed") is False, "same-source raw write must be false", errors)
    require(same_source.get("raw_source_mutation_allowed") is False, "same-source raw mutation must be false", errors)
    require(same_source.get("policy_fixture_only") is True, "same-source policy fixture must be true", errors)
    require(same_source.get("business_conflict_observed") is False, "same-source business conflict observed must be false", errors)

    queue_item = difference_queue[0] if difference_queue else {}
    require(queue_item.get("record_type") == "source_difference_queue_item", "queue record type mismatch", errors)
    require(queue_item.get("schema_version") == "kmfa.v014_s03_p3.cross_source_difference_queue.v1", "queue schema mismatch", errors)
    require(queue_item.get("status") == "queued_for_manual_review", "queue status mismatch", errors)
    require(queue_item.get("resolution_policy") == "manual_review_required", "queue resolution mismatch", errors)
    require(queue_item.get("auto_selection_allowed") is False, "queue auto selection must be false", errors)
    require(queue_item.get("auto_selected_source_id") is None, "queue auto selected source must be null", errors)
    require(queue_item.get("target_layer") == "metadata", "queue target layer must be metadata", errors)
    require(queue_item.get("raw_layer_write_allowed") is False, "queue raw write must be false", errors)
    require(queue_item.get("raw_source_mutation_allowed") is False, "queue raw mutation must be false", errors)
    require(queue_item.get("policy_fixture_only") is True, "queue policy fixture must be true", errors)
    require(queue_item.get("business_conflict_observed") is False, "queue business conflict observed must be false", errors)
    require(
        [ref.get("source_class") for ref in queue_item.get("source_refs", [])] == ["raw_upload", "authorized_export"],
        "queue source refs must be sorted by source priority",
        errors,
    )

    require(protocol.get("schema_version") == "kmfa.source_priority.v1_4.s03_p3", "protocol schema mismatch", errors)
    require(protocol.get("source_priority_order") == list(SOURCE_PRIORITY_ORDER), "protocol source priority order mismatch", errors)
    require(protocol.get("raw_or_authorized_priority_over_processed_data") is True, "protocol priority boundary mismatch", errors)
    require(protocol.get("policy_fixture_only") is True, "protocol fixture flag mismatch", errors)
    require(protocol.get("business_conflict_observed_count") == 0, "protocol conflict count mismatch", errors)
    same_source_policy = protocol.get("same_source_inconsistency_policy", {})
    require(same_source_policy.get("actions") == ["invalidate_derived_cache", "request_rerun"], "protocol same-source actions mismatch", errors)
    require(same_source_policy.get("cache_reuse_allowed") is False, "protocol cache reuse must be false", errors)
    cross_source_policy = protocol.get("cross_source_conflict_policy", {})
    require(cross_source_policy.get("difference_queue") is True, "protocol queue flag mismatch", errors)
    require(cross_source_policy.get("manual_review_required") is True, "protocol manual review flag mismatch", errors)
    require(cross_source_policy.get("auto_selection_allowed") is False, "protocol auto selection must be false", errors)
    require(cross_source_policy.get("auto_correction_allowed") is False, "protocol auto correction must be false", errors)
    protocol_non_scope = protocol.get("non_scope", {})
    for key in (
        "stage3_review_performed",
        "github_upload_performed",
        "raw_value_matching_performed",
        "field_mapping_performed",
        "formal_report_performed",
        "business_execution_performed",
    ):
        require(protocol_non_scope.get(key) is False, f"protocol.non_scope.{key} must be false", errors)

    raw_boundary = manifest.get("raw_data_boundary", {})
    require(raw_boundary.get("local_raw_data_dir") == str(RAW_INBOX), "raw inbox path mismatch", errors)
    require(raw_boundary.get("codex_read_performed_by_this_phase") is False, "raw read performed flag must be false", errors)
    for key in (
        "codex_modify_allowed",
        "codex_delete_allowed",
        "codex_move_allowed",
        "codex_rename_allowed",
        "codex_overwrite_allowed",
        "codex_generate_inside_allowed",
        "github_commit_allowed",
    ):
        require(raw_boundary.get(key) is False, f"raw_data_boundary.{key} must be false", errors)

    for safety in (manifest.get("public_repo_safety", {}), protocol.get("public_repo_safety", {})):
        for key in PUBLIC_SAFETY_FALSE_KEYS:
            require(safety.get(key) is False, f"public_repo_safety.{key} must be false", errors)

    release = manifest.get("release_state", {})
    require(release.get("current_data_quality_grade") == "Q2", "quality grade must be Q2", errors)
    require(release.get("current_report_grade") == "D", "report grade must be D", errors)
    require(release.get("current_go_no_go") == "NO_GO", "Go/No-Go must be NO_GO", errors)
    require(release.get("release_permission") == "blocked", "release permission must be blocked", errors)
    for key in (
        "delivery_allowed",
        "formal_report_allowed",
        "business_decision_basis_allowed",
        "business_execution_allowed",
        "github_main_upload_allowed",
    ):
        require(release.get(key) is False, f"release_state.{key} must be false", errors)

    require(manifest.get("next_recommended_phase") == "S03_STAGE_REVIEW", "next recommended phase mismatch", errors)
    for path in (
        MANIFEST_PATH,
        PRIORITY_RECORDS_PATH,
        SAME_SOURCE_EVENTS_PATH,
        DIFFERENCE_QUEUE_PATH,
        PROTOCOL_PATH,
        REPORT_PATH,
        TEST_RESULTS_PATH,
        RISK_REGISTER_PATH,
        ROLLBACK_PLAN_PATH,
    ):
        check_public_safe_file(path, errors)

    tracked_files = git_output(["ls-files", "KMFA"]).splitlines()
    forbidden_tracked = [
        path for path in tracked_files if path.lower().endswith(tuple(FORBIDDEN_EXTENSIONS)) or ".codex_private_runtime/" in path
    ]
    require(not forbidden_tracked, f"forbidden tracked raw/private files: {forbidden_tracked}", errors)
    require("codex/kmfa" in git_output(["status", "--short", "--branch"]), "git status must be on codex/kmfa", errors)

    validation = manifest.get("validation_summary", {})
    for key in (
        "s03_p2_dependency",
        "v014_s03_p3_validator",
        "focused_unit_test",
        "governance_validator",
        "raw_private_scan",
        "public_raw_leak_scan",
        "secret_scan",
        "diff_check",
    ):
        require(validation.get(key) in {"PENDING", "PASS"}, f"validation_summary.{key} must be PENDING or PASS", errors)

    if errors:
        raise ValidationError("\n".join(errors))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v1.4 S03-P3 source priority evidence.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args()
    try:
        manifest = validate_v014_s03_p3_source_priority(args.manifest)
    except ValidationError as exc:
        print("FAIL: KMFA v1.4 S03-P3 validation failed")
        print(exc)
        return 1
    summary = manifest["source_priority_summary"]
    print(
        "PASS: KMFA v1.4 S03-P3 source priority validated "
        f"(records={summary['source_priority_record_count']}, priority_order={summary['source_priority_order_count']}, "
        f"same_source_events={summary['same_source_policy_event_count']}, "
        f"difference_queue={summary['cross_source_difference_queue_item_count']}, raw_read=false, "
        f"github_upload=false, next={manifest['next_recommended_phase']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
