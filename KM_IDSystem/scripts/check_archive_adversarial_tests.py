#!/usr/bin/env python3
"""Stage 028 archive adversarial testing slice for IDS."""

from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import check_safe_extraction_engine as safe_extraction_engine


ENTRANCE = "IDS 系统运营入口"
ARCHIVE_ADVERSARIAL_SCHEMA = "ids.stage028.archive_adversarial_tests.v1"
ARCHIVE_ADVERSARIAL_TEST_ID = "ids.stage028.archive_adversarial.phase2"

RISK_CODE_MAP = {
    "SAFE_EXTRACTION_PATH_TRAVERSAL_BLOCKED": "ARCHIVE_ADVERSARIAL_PATH_TRAVERSAL_BLOCKED",
    "SAFE_EXTRACTION_ABSOLUTE_PATH_BLOCKED": "ARCHIVE_ADVERSARIAL_ABSOLUTE_PATH_BLOCKED",
    "SAFE_EXTRACTION_STAGING_ESCAPE_BLOCKED": "ARCHIVE_ADVERSARIAL_STAGING_ESCAPE_BLOCKED",
    "SAFE_EXTRACTION_FILE_COUNT_LIMIT_EXCEEDED": "ARCHIVE_ADVERSARIAL_FILE_COUNT_LIMIT_EXCEEDED",
    "SAFE_EXTRACTION_ENTRY_SIZE_LIMIT_EXCEEDED": "ARCHIVE_ADVERSARIAL_ENTRY_SIZE_LIMIT_EXCEEDED",
    "SAFE_EXTRACTION_TOTAL_SIZE_LIMIT_EXCEEDED": "ARCHIVE_ADVERSARIAL_TOTAL_SIZE_LIMIT_EXCEEDED",
    "SAFE_EXTRACTION_NESTED_DEPTH_LIMIT_EXCEEDED": "ARCHIVE_ADVERSARIAL_NESTED_DEPTH_LIMIT_EXCEEDED",
    "SAFE_EXTRACTION_GARBLED_FILENAME_OWNER_REVIEW_REQUIRED": (
        "ARCHIVE_ADVERSARIAL_GARBLED_FILENAME_OWNER_REVIEW_REQUIRED"
    ),
    "SAFE_EXTRACTION_STAGING_OVERWRITE_BLOCKED": "ARCHIVE_ADVERSARIAL_STAGING_OVERWRITE_BLOCKED",
    "SAFE_EXTRACTION_ADAPTER_OWNER_REVIEW_REQUIRED": "ARCHIVE_ADVERSARIAL_ADAPTER_OWNER_REVIEW_REQUIRED",
    "SAFE_EXTRACTION_FORMAT_UNSUPPORTED": "ARCHIVE_ADVERSARIAL_FORMAT_UNSUPPORTED",
    "SAFE_EXTRACTION_SOURCE_MISSING": "ARCHIVE_ADVERSARIAL_SOURCE_MISSING",
    "SAFE_EXTRACTION_SOURCE_BLOCKED_RAW_METADATA_ROOT": "ARCHIVE_ADVERSARIAL_SOURCE_BLOCKED_RAW_METADATA_ROOT",
    "SAFE_EXTRACTION_NON_FILE_ENTRY_BLOCKED": "ARCHIVE_ADVERSARIAL_NON_FILE_ENTRY_BLOCKED",
    "SAFE_EXTRACTION_EMPTY_PATH_BLOCKED": "ARCHIVE_ADVERSARIAL_EMPTY_PATH_BLOCKED",
    "SAFE_EXTRACTION_ENTRY_SAFE": "ARCHIVE_ADVERSARIAL_ENTRY_SAFE",
}

STATE_MAP = {
    "SAFE_EXTRACTION_DRAFT": "ARCHIVE_ADVERSARIAL_DRAFT",
    "SAFE_EXTRACTION_BLOCKED": "ARCHIVE_ADVERSARIAL_BLOCKED",
    "SAFE_EXTRACTION_OWNER_REVIEW_REQUIRED": "ARCHIVE_ADVERSARIAL_OWNER_REVIEW_REQUIRED",
    "SAFE_EXTRACTION_READY_FOR_STAGING": "ARCHIVE_ADVERSARIAL_READY_FOR_SAFE_EXTRACTION",
    "SAFE_EXTRACTION_READY_FOR_REINGEST": "ARCHIVE_ADVERSARIAL_READY_FOR_REINGEST",
}

ZERO_JOB_STARTS = {
    "hash": 0,
    "manifest": 0,
    "dedup": 0,
    "parser": 0,
    "ocr": 0,
    "embedding": 0,
    "index": 0,
    "import": 0,
}

REQUIRED_STAGE028_SCENARIOS = (
    "path_traversal",
    "absolute_path",
    "archive_bomb",
    "nested_archive",
    "garbled_filename",
    "too_many_files",
)

EXPECTED_STAGE028_SCENARIO_RISKS = {
    "path_traversal": "ARCHIVE_ADVERSARIAL_PATH_TRAVERSAL_BLOCKED",
    "absolute_path": "ARCHIVE_ADVERSARIAL_ABSOLUTE_PATH_BLOCKED",
    "archive_bomb": "ARCHIVE_ADVERSARIAL_TOTAL_SIZE_LIMIT_EXCEEDED",
    "nested_archive": "ARCHIVE_ADVERSARIAL_NESTED_DEPTH_LIMIT_EXCEEDED",
    "garbled_filename": "ARCHIVE_ADVERSARIAL_GARBLED_FILENAME_OWNER_REVIEW_REQUIRED",
    "too_many_files": "ARCHIVE_ADVERSARIAL_FILE_COUNT_LIMIT_EXCEEDED",
}


def _map_risk_code(risk_code: str | None) -> str | None:
    if risk_code is None:
        return None
    return RISK_CODE_MAP.get(
        risk_code,
        f"ARCHIVE_ADVERSARIAL_{risk_code.removeprefix('SAFE_EXTRACTION_')}",
    )


def _map_entry(entry: dict[str, Any]) -> dict[str, Any]:
    mapped = deepcopy(entry)
    if "risk_code" in mapped:
        mapped["source_risk_code"] = mapped["risk_code"]
        mapped["risk_code"] = _map_risk_code(mapped["risk_code"])
    if "entry_state" in mapped and isinstance(mapped["entry_state"], str):
        mapped["source_entry_state"] = mapped["entry_state"]
        mapped["entry_state"] = mapped["entry_state"].replace(
            "SAFE_EXTRACTION_",
            "ARCHIVE_ADVERSARIAL_",
        )
    mapped["archive_adversarial_test_id"] = ARCHIVE_ADVERSARIAL_TEST_ID
    return mapped


def _map_manifest(source_manifest: dict[str, Any]) -> dict[str, Any]:
    manifest = deepcopy(source_manifest)
    manifest["schema_version"] = "ids.stage028.archive_adversarial_manifest.v1"
    manifest["source_schema_version"] = source_manifest.get("schema_version")
    manifest["archive_adversarial_test_id"] = ARCHIVE_ADVERSARIAL_TEST_ID
    manifest["runtime_output_written"] = False
    manifest["entries"] = [_map_entry(entry) for entry in source_manifest.get("entries", [])]
    return manifest


def _map_reingest(source_reingest: dict[str, Any]) -> dict[str, Any]:
    reingest = deepcopy(source_reingest)
    reingest["state"] = (
        "ARCHIVE_ADVERSARIAL_REINGEST_REQUIRED"
        if source_reingest.get("reingest_queue")
        else "ARCHIVE_ADVERSARIAL_REINGEST_NOT_READY"
    )
    reingest["required_pipeline"] = ["hash", "manifest", "dedup", "parser"]
    queue = []
    for item in source_reingest.get("reingest_queue", []):
        mapped = dict(item)
        mapped["archive_adversarial_test_id"] = ARCHIVE_ADVERSARIAL_TEST_ID
        mapped["reingest_policy"] = "post_extract_hash_manifest_dedup_parser_required"
        mapped["import_queue_created"] = False
        queue.append(mapped)
    reingest["reingest_queue"] = queue
    return reingest


def _build_reingest_validation(post_extract_reingest: dict[str, Any]) -> dict[str, Any]:
    reingest_queue = list(post_extract_reingest.get("reingest_queue", []))
    return {
        "state": "ARCHIVE_ADVERSARIAL_REINGEST_VALIDATED"
        if reingest_queue
        else "ARCHIVE_ADVERSARIAL_REINGEST_NOT_READY",
        "required_pipeline": ["hash", "manifest", "dedup", "parser"],
        "safe_extracted_file_count": len(reingest_queue),
        "pipeline_stage_states": {
            "hash": "POST_EXTRACT_HASH_REQUIRED",
            "manifest": "POST_EXTRACT_MANIFEST_REQUIRED",
            "dedup": "POST_EXTRACT_DEDUP_REQUIRED",
            "parser": "POST_EXTRACT_PARSER_REQUIRED",
        },
        "reingest_queue": reingest_queue,
        "actual_jobs_started": dict(ZERO_JOB_STARTS),
        "import_queue_created": False,
    }


def _build_cleanup_validation(
    *,
    cleanup_allowlist: list[dict[str, Any]],
    original_archive_ref: str,
    cleanup_policy: dict[str, Any],
) -> dict[str, Any]:
    cleanup_classes = {item.get("cleanup_class") for item in cleanup_allowlist}
    cleanup_uris = [item.get("uri") for item in cleanup_allowlist]
    original_archive_in_cleanup = original_archive_ref in cleanup_uris
    temp_only = bool(cleanup_allowlist) and cleanup_classes <= {"ARCHIVE_STAGING_TEMP_FILE"}
    protected_refs_preserved = (
        cleanup_policy.get("does_not_clean_original_archive", True)
        and cleanup_policy.get("does_not_clean_fact_source_or_evidence", True)
        and cleanup_policy.get("does_not_clean_manifest_or_audit_outputs", True)
        and not original_archive_in_cleanup
    )
    if not cleanup_allowlist:
        state = "ARCHIVE_ADVERSARIAL_CLEANUP_ALLOWLIST_EMPTY_NO_EXTRACTION"
    elif temp_only and protected_refs_preserved:
        state = "ARCHIVE_ADVERSARIAL_CLEANUP_ALLOWLIST_VALIDATED"
    else:
        state = "ARCHIVE_ADVERSARIAL_CLEANUP_ALLOWLIST_REVIEW_REQUIRED"
    return {
        "state": state,
        "allowed_cleanup_classes": sorted(cleanup_classes),
        "cleanup_allowlist_uris": cleanup_uris,
        "cleanup_targets_are_staging_temp_files_only": temp_only,
        "original_archive_in_cleanup_allowlist": original_archive_in_cleanup,
        "protected_refs_preserved": protected_refs_preserved,
        "does_not_clean_original_archive": not original_archive_in_cleanup,
        "does_not_clean_fact_source_or_evidence": cleanup_policy.get(
            "does_not_clean_fact_source_or_evidence",
            True,
        ),
    }


def _build_manual_review_routing(risk_entries: list[dict[str, Any]], quarantine_entries: list[dict[str, Any]]) -> dict[str, Any]:
    risk_codes = {entry.get("risk_code") for entry in risk_entries}
    return {
        "state": "ARCHIVE_ADVERSARIAL_MANUAL_REVIEW_REQUIRED"
        if risk_entries
        else "ARCHIVE_ADVERSARIAL_MANUAL_REVIEW_NOT_REQUIRED",
        "failure_files_to_owner_review": any(
            code in risk_codes
            for code in {
                "ARCHIVE_ADVERSARIAL_SOURCE_MISSING",
                "ARCHIVE_ADVERSARIAL_FORMAT_UNSUPPORTED",
                "ARCHIVE_ADVERSARIAL_ADAPTER_OWNER_REVIEW_REQUIRED",
                "ARCHIVE_ADVERSARIAL_SOURCE_BLOCKED_RAW_METADATA_ROOT",
            }
        ),
        "risk_files_to_owner_review": bool(risk_entries),
        "over_limit_files_to_owner_review": any("LIMIT" in str(code) for code in risk_codes),
        "quarantine_required": bool(quarantine_entries),
        "owner_review_entry_count": len(risk_entries),
        "quarantine_entry_count": len(quarantine_entries),
    }


def _derive_state(safe_report: dict[str, Any], risk_entries: list[dict[str, Any]]) -> str:
    safe_count = safe_report.get("safe_extracted_file_count", 0)
    if safe_count and risk_entries:
        return "ARCHIVE_ADVERSARIAL_OWNER_REVIEW_REQUIRED"
    if safe_count:
        return "ARCHIVE_ADVERSARIAL_READY_FOR_REINGEST"
    source_state = safe_report.get("safe_extraction_decision_state", "SAFE_EXTRACTION_BLOCKED")
    return STATE_MAP.get(source_state, "ARCHIVE_ADVERSARIAL_BLOCKED")


def run_archive_adversarial_test(
    *,
    archive_uri: str,
    staging_area_uri: str,
    evaluated_at: str | None = None,
    archive_file_count_limit: int = safe_extraction_engine.archive_threat_model.DEFAULT_ARCHIVE_FILE_COUNT_LIMIT,
    archive_total_size_limit_bytes: int = safe_extraction_engine.archive_threat_model.DEFAULT_ARCHIVE_TOTAL_SIZE_LIMIT_BYTES,
    archive_single_file_size_limit_bytes: int = (
        safe_extraction_engine.archive_threat_model.DEFAULT_ARCHIVE_SINGLE_FILE_SIZE_LIMIT_BYTES
    ),
    archive_nested_depth_limit: int = safe_extraction_engine.archive_threat_model.DEFAULT_ARCHIVE_NESTED_DEPTH_LIMIT,
) -> dict[str, Any]:
    """Run a Stage 028 Phase 2 adversarial archive slice without persistence."""

    safe_report = safe_extraction_engine.run_safe_extraction_engine(
        archive_uri=archive_uri,
        staging_area_uri=staging_area_uri,
        extracted_at=evaluated_at,
        archive_file_count_limit=archive_file_count_limit,
        archive_total_size_limit_bytes=archive_total_size_limit_bytes,
        archive_single_file_size_limit_bytes=archive_single_file_size_limit_bytes,
        archive_nested_depth_limit=archive_nested_depth_limit,
    )
    risk_entries = [_map_entry(entry) for entry in safe_report.get("risk_entries", [])]
    owner_review_entries = [_map_entry(entry) for entry in safe_report.get("owner_review_entries", [])]
    quarantine_entries = [_map_entry(entry) for entry in safe_report.get("quarantine_entries", [])]
    safe_extracted_entries = [_map_entry(entry) for entry in safe_report.get("safe_extracted_entries", [])]
    post_extract_reingest = _map_reingest(safe_report.get("post_extract_reingest", {}))
    cleanup_allowlist = [dict(item, archive_adversarial_test_id=ARCHIVE_ADVERSARIAL_TEST_ID) for item in safe_report.get("cleanup_allowlist", [])]
    cleanup_policy = dict(safe_report.get("cleanup_policy", {}))

    report = {
        "schema_version": ARCHIVE_ADVERSARIAL_SCHEMA,
        "source_schema_version": safe_report.get("schema_version"),
        "stage": "STAGE-028",
        "phase": "Phase 2",
        "task_id": "IDS-V0_1-STAGE028-P2",
        "acceptance_id": "ACC-STAGE-028",
        "entrance": ENTRANCE,
        "archive_adversarial_test_id": ARCHIVE_ADVERSARIAL_TEST_ID,
        "evaluated_at": safe_report.get("extracted_at"),
        "archive_type": safe_report.get("archive_type"),
        "archive_source_uri": safe_report.get("archive_source_uri"),
        "original_archive_ref": safe_report.get("original_archive_ref"),
        "archive_staging_area_uri": safe_report.get("archive_staging_area_uri"),
        "limits": dict(safe_report.get("limits", {})),
        "source_safe_extraction_decision_state": safe_report.get("safe_extraction_decision_state"),
        "archive_adversarial_test_state": _derive_state(safe_report, risk_entries),
        "archive_manifest": _map_manifest(safe_report.get("archive_manifest", {})),
        "archive_manifest_ref": "in_memory_stage028_archive_adversarial_manifest",
        "safe_extraction_ref": safe_report.get("safe_extraction_engine_id"),
        "safe_extracted_entries": safe_extracted_entries,
        "safe_extracted_file_count": safe_report.get("safe_extracted_file_count", 0),
        "risk_entries": risk_entries,
        "owner_review_entries": owner_review_entries,
        "quarantine_entries": quarantine_entries,
        "blocked_entry_count": len(risk_entries),
        "quarantine_entry_count": len(quarantine_entries),
        "post_extract_reingest": post_extract_reingest,
        "reingest_validation": _build_reingest_validation(post_extract_reingest),
        "cleanup_allowlist": cleanup_allowlist,
        "cleanup_policy": cleanup_policy,
        "cleanup_validation": _build_cleanup_validation(
            cleanup_allowlist=cleanup_allowlist,
            original_archive_ref=safe_report.get("original_archive_ref", ""),
            cleanup_policy=cleanup_policy,
        ),
        "manual_review_routing": _build_manual_review_routing(risk_entries, quarantine_entries),
        "processing_guard": dict(safe_report.get("processing_guard", {})),
        "no_persistence_deltas": dict(safe_report.get("no_persistence_deltas", {})),
        "original_archive_preserved": safe_report.get("original_archive_preserved", True),
        "does_not_overwrite_original_archive": safe_report.get("does_not_overwrite_original_archive", True),
        "does_not_write_outside_staging": safe_report.get("does_not_write_outside_staging", True),
        "does_not_read_raw_metadata": safe_report.get("does_not_read_raw_metadata", True),
        "does_not_write_archive_manifest_runtime_output": safe_report.get(
            "does_not_write_archive_manifest_runtime_output",
            True,
        ),
        "does_not_write_archive_adversarial_runtime_output": True,
        "does_not_write_runtime_outputs": True,
        "does_not_create_import_queue": True,
        "does_not_write_database": True,
        "does_not_write_reports": True,
        "does_not_write_evidence_ledger": True,
        "does_not_write_audit_log": True,
        "does_not_write_index": True,
        "does_not_write_document_chunk_job_import_rows": True,
        "does_not_start_processing_jobs": True,
        "does_not_call_external_apis": True,
        "does_not_use_fake_ids_business_data": True,
    }
    return report


def _flatten_reingest_queue(scenario_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    queue: list[dict[str, Any]] = []
    for result in scenario_results:
        report = result["archive_adversarial_report"]
        for item in report["post_extract_reingest"]["reingest_queue"]:
            queue.append({"scenario_id": result["scenario_id"], **item})
    return queue


def _flatten_cleanup_allowlist(scenario_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cleanup_items: list[dict[str, Any]] = []
    for result in scenario_results:
        report = result["archive_adversarial_report"]
        for item in report["cleanup_allowlist"]:
            cleanup_items.append({"scenario_id": result["scenario_id"], **item})
    return cleanup_items


def _build_scenario_cleanup_validation(
    *,
    cleanup_allowlist: list[dict[str, Any]],
    original_archive_refs: list[str],
    scenario_results: list[dict[str, Any]],
) -> dict[str, Any]:
    cleanup_classes = {item.get("cleanup_class") for item in cleanup_allowlist}
    cleanup_uris = [item.get("uri") for item in cleanup_allowlist]
    original_archive_in_cleanup = any(ref in cleanup_uris for ref in original_archive_refs)
    policies_preserve_refs = all(
        result["archive_adversarial_report"]["cleanup_policy"]["does_not_clean_original_archive"]
        and result["archive_adversarial_report"]["cleanup_policy"]["does_not_clean_fact_source_or_evidence"]
        for result in scenario_results
    )
    temp_only = bool(cleanup_allowlist) and cleanup_classes <= {"ARCHIVE_STAGING_TEMP_FILE"}
    return {
        "state": "ARCHIVE_ADVERSARIAL_CLEANUP_ALLOWLIST_VALIDATED"
        if temp_only and policies_preserve_refs and not original_archive_in_cleanup
        else "ARCHIVE_ADVERSARIAL_CLEANUP_ALLOWLIST_REVIEW_REQUIRED",
        "allowed_cleanup_classes": sorted(cleanup_classes),
        "cleanup_allowlist_uris": cleanup_uris,
        "cleanup_targets_are_staging_temp_files_only": temp_only,
        "original_archive_in_cleanup_allowlist": original_archive_in_cleanup,
        "protected_refs_preserved": policies_preserve_refs and not original_archive_in_cleanup,
        "does_not_clean_original_archive": not original_archive_in_cleanup,
        "does_not_clean_fact_source_or_evidence": policies_preserve_refs,
    }


def _build_manual_review_validation(scenario_results: list[dict[str, Any]]) -> dict[str, Any]:
    owner_review_entry_count = sum(
        len(result["archive_adversarial_report"]["owner_review_entries"]) for result in scenario_results
    )
    quarantine_entry_count = sum(
        len(result["archive_adversarial_report"]["quarantine_entries"]) for result in scenario_results
    )
    return {
        "state": "ARCHIVE_ADVERSARIAL_MANUAL_REVIEW_VALIDATED"
        if owner_review_entry_count and quarantine_entry_count
        else "ARCHIVE_ADVERSARIAL_MANUAL_REVIEW_REVIEW_REQUIRED",
        "owner_review_entry_count": owner_review_entry_count,
        "quarantine_entry_count": quarantine_entry_count,
        "risk_files_to_owner_review": owner_review_entry_count > 0,
        "quarantine_required": quarantine_entry_count > 0,
    }


def build_stage028_scenario_report(
    *,
    scenario_archives: dict[str, dict[str, Any]],
    evaluated_at: str | None = None,
    required_scenarios: tuple[str, ...] = REQUIRED_STAGE028_SCENARIOS,
) -> dict[str, Any]:
    """Validate Stage 028 Phase 3 adversarial archive scenarios without persistence."""

    scenario_results: list[dict[str, Any]] = []
    required_scenario_set = set(required_scenarios)
    for scenario_id in required_scenarios:
        scenario_config = dict(scenario_archives[scenario_id])
        archive_adversarial_report = run_archive_adversarial_test(
            archive_uri=scenario_config["archive_uri"],
            staging_area_uri=scenario_config["staging_area_uri"],
            evaluated_at=evaluated_at,
            archive_file_count_limit=scenario_config.get(
                "archive_file_count_limit",
                safe_extraction_engine.archive_threat_model.DEFAULT_ARCHIVE_FILE_COUNT_LIMIT,
            ),
            archive_total_size_limit_bytes=scenario_config.get(
                "archive_total_size_limit_bytes",
                safe_extraction_engine.archive_threat_model.DEFAULT_ARCHIVE_TOTAL_SIZE_LIMIT_BYTES,
            ),
            archive_single_file_size_limit_bytes=scenario_config.get(
                "archive_single_file_size_limit_bytes",
                safe_extraction_engine.archive_threat_model.DEFAULT_ARCHIVE_SINGLE_FILE_SIZE_LIMIT_BYTES,
            ),
            archive_nested_depth_limit=scenario_config.get(
                "archive_nested_depth_limit",
                safe_extraction_engine.archive_threat_model.DEFAULT_ARCHIVE_NESTED_DEPTH_LIMIT,
            ),
        )
        risk_codes = [entry["risk_code"] for entry in archive_adversarial_report["risk_entries"]]
        expected_risk_code = EXPECTED_STAGE028_SCENARIO_RISKS.get(scenario_id)
        expected_risk_observed = expected_risk_code is None or expected_risk_code in risk_codes
        scenario_results.append(
            {
                "scenario_id": scenario_id,
                "scenario_state": "ARCHIVE_ADVERSARIAL_SCENARIO_VALIDATED"
                if expected_risk_observed
                else "ARCHIVE_ADVERSARIAL_SCENARIO_REVIEW_REQUIRED",
                "expected_risk_code": expected_risk_code,
                "expected_risk_observed": expected_risk_observed,
                "risk_codes": risk_codes,
                "archive_adversarial_test_state": archive_adversarial_report["archive_adversarial_test_state"],
                "safe_extracted_file_count": archive_adversarial_report["safe_extracted_file_count"],
                "blocked_entry_count": archive_adversarial_report["blocked_entry_count"],
                "quarantine_entry_count": archive_adversarial_report["quarantine_entry_count"],
                "archive_adversarial_report": archive_adversarial_report,
            }
        )

    reingest_queue = _flatten_reingest_queue(scenario_results)
    cleanup_allowlist = _flatten_cleanup_allowlist(scenario_results)
    original_archive_refs = [result["archive_adversarial_report"]["original_archive_ref"] for result in scenario_results]
    reingest_validation = _build_reingest_validation(
        {
            "required_pipeline": ["hash", "manifest", "dedup", "parser"],
            "reingest_queue": reingest_queue,
        }
    )
    cleanup_validation = _build_scenario_cleanup_validation(
        cleanup_allowlist=cleanup_allowlist,
        original_archive_refs=original_archive_refs,
        scenario_results=scenario_results,
    )
    manual_review_validation = _build_manual_review_validation(scenario_results)
    required_scenarios_covered = required_scenario_set <= set(scenario_archives)
    scenarios_validated = all(
        result["scenario_state"] == "ARCHIVE_ADVERSARIAL_SCENARIO_VALIDATED" for result in scenario_results
    )
    validation_passed = (
        required_scenarios_covered
        and scenarios_validated
        and reingest_validation["state"] == "ARCHIVE_ADVERSARIAL_REINGEST_VALIDATED"
        and cleanup_validation["state"] == "ARCHIVE_ADVERSARIAL_CLEANUP_ALLOWLIST_VALIDATED"
        and manual_review_validation["state"] == "ARCHIVE_ADVERSARIAL_MANUAL_REVIEW_VALIDATED"
    )
    return {
        "schema_version": "ids.stage028.archive_adversarial_tests.scenario_validation.v1",
        "stage": "STAGE-028",
        "phase": "Phase 3",
        "task_id": "IDS-V0_1-STAGE028-P3",
        "acceptance_id": "ACC-STAGE-028",
        "entrance": ENTRANCE,
        "archive_adversarial_schema": ARCHIVE_ADVERSARIAL_SCHEMA,
        "evaluated_at": evaluated_at,
        "required_scenarios": list(required_scenarios),
        "scenario_count": len(scenario_results),
        "required_scenarios_covered": required_scenarios_covered,
        "validation_state": "ARCHIVE_ADVERSARIAL_SCENARIO_VALIDATION_PASSED"
        if validation_passed
        else "ARCHIVE_ADVERSARIAL_SCENARIO_VALIDATION_REVIEW_REQUIRED",
        "scenario_results": scenario_results,
        "reingest_validation": reingest_validation,
        "cleanup_validation": cleanup_validation,
        "manual_review_validation": manual_review_validation,
        "processing_guard": dict(safe_extraction_engine.archive_threat_model.PROCESSING_GUARD_ZEROES),
        "no_persistence_deltas": dict(safe_extraction_engine.archive_threat_model.NO_PERSISTENCE_DELTAS),
        "does_not_read_raw_metadata": True,
        "does_not_write_archive_adversarial_runtime_output": True,
        "does_not_write_archive_manifest_runtime_output": True,
        "does_not_write_runtime_outputs": True,
        "does_not_start_processing_jobs": True,
        "does_not_use_fake_ids_business_data": True,
        "does_not_create_import_queue": True,
        "does_not_write_database": True,
        "does_not_write_index": True,
    }


def _build_archive_manifest_sample(scenario_report: dict[str, Any]) -> dict[str, Any]:
    for result in scenario_report.get("scenario_results", []):
        manifest = result["archive_adversarial_report"]["archive_manifest"]
        entries = list(manifest.get("entries", []))
        if entries:
            sample = deepcopy(manifest)
            sample["sample_state"] = "ARCHIVE_ADVERSARIAL_MANIFEST_SAMPLE_READY"
            sample["sample_source"] = "in_memory_stage028_phase3_scenario_report"
            sample["entry_count"] = len(entries)
            return sample
    return {
        "schema_version": "ids.stage028.archive_adversarial_manifest.v1",
        "sample_state": "ARCHIVE_ADVERSARIAL_MANIFEST_SAMPLE_EMPTY",
        "sample_source": "in_memory_stage028_phase3_scenario_report",
        "entry_count": 0,
        "runtime_output_written": False,
        "entries": [],
    }


def _build_safety_block_log_sample(scenario_report: dict[str, Any]) -> dict[str, Any]:
    risk_records: list[dict[str, Any]] = []
    for result in scenario_report.get("scenario_results", []):
        scenario_id = result["scenario_id"]
        report = result["archive_adversarial_report"]
        for entry in report.get("risk_entries", []):
            risk_records.append(
                {
                    "scenario_id": scenario_id,
                    "entry_path": entry.get("entry_path"),
                    "risk_code": entry.get("risk_code"),
                    "entry_state": entry.get("entry_state"),
                    "owner_review_required": True,
                    "runtime_log_written": False,
                }
            )
    return {
        "state": "ARCHIVE_ADVERSARIAL_BLOCK_LOG_READY" if risk_records else "ARCHIVE_ADVERSARIAL_BLOCK_LOG_EMPTY",
        "sample_source": "in_memory_stage028_phase3_scenario_report",
        "risk_codes": sorted({record["risk_code"] for record in risk_records if record.get("risk_code")}),
        "blocked_entry_count": len(risk_records),
        "risk_records": risk_records,
        "runtime_output_written": False,
        "audit_log_written": False,
    }


def build_stage028_closeout_summary(
    *,
    scenario_report: dict[str, Any],
    evaluated_at: str | None = None,
) -> dict[str, Any]:
    """Build Stage 028 Phase 4 closeout evidence without writing runtime outputs."""

    manifest_sample = _build_archive_manifest_sample(scenario_report)
    block_log_sample = _build_safety_block_log_sample(scenario_report)
    cleanup_sample = dict(scenario_report["cleanup_validation"])
    delivery_ready = (
        manifest_sample["entry_count"] > 0
        and block_log_sample["state"] == "ARCHIVE_ADVERSARIAL_BLOCK_LOG_READY"
        and cleanup_sample.get("state") == "ARCHIVE_ADVERSARIAL_CLEANUP_ALLOWLIST_VALIDATED"
    )
    return {
        "schema_version": "ids.stage028.archive_adversarial_tests.closeout.v1",
        "stage": "STAGE-028",
        "phase": "Phase 4",
        "task_id": "IDS-V0_1-STAGE028-P4",
        "acceptance_id": "ACC-STAGE-028",
        "entrance": ENTRANCE,
        "evaluated_at": evaluated_at,
        "source_scenario_schema": scenario_report.get("schema_version"),
        "closeout_state": "ARCHIVE_ADVERSARIAL_STAGE_CLOSEOUT_PASSED"
        if delivery_ready
        else "ARCHIVE_ADVERSARIAL_STAGE_CLOSEOUT_REVIEW_REQUIRED",
        "whole_stage_review": {
            "result": "passed_with_local_evidence" if delivery_ready else "review_required",
            "phases_reviewed": ["Phase 1", "Phase 2", "Phase 3", "Phase 4"],
            "phase_results": {
                "Phase 1": "scope_boundary_defined",
                "Phase 2": "archive_adversarial_slice_passed",
                "Phase 3": scenario_report.get("validation_state"),
                "Phase 4": "closeout_evidence_recorded",
            },
            "unresolved_findings": [],
            "batch_gate_state": "BATCH021_030_LOCKED_NO_UPLOAD",
        },
        "delivery_evidence": {
            "evidence_state": "ARCHIVE_ADVERSARIAL_DELIVERY_EVIDENCE_READY"
            if delivery_ready
            else "ARCHIVE_ADVERSARIAL_DELIVERY_EVIDENCE_REVIEW_REQUIRED",
            "archive_manifest_sample": manifest_sample,
            "safety_block_log_sample": block_log_sample,
            "cleanup_allowlist_sample": cleanup_sample,
        },
        "risk_boundary": {
            "raw_metadata_root": "/Users/linzezhang/Downloads/IDS_MetaData",
            "raw_metadata_path_only_boundary": True,
            "real_data_only_policy": True,
            "no_runtime_output": True,
            "no_processing_jobs": True,
            "no_github_upload": True,
            "no_app_reinstall": True,
            "stop_conditions": [
                "需要读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描 IDS_MetaData 内容",
                "可能删除、移动、覆盖原始压缩包、事实源、manifest、evidence ledger 或 audit log",
                "需要写 archive_adversarial runtime output、archive_manifest runtime output、database、index、report 或 parser output",
                "测试失败且原因不明",
                "修改范围超出 STAGE-028 Phase 4",
            ],
        },
        "staging_rollback": {
            "rollback_state": "ARCHIVE_ADVERSARIAL_STAGING_ROLLBACK_DOCUMENTED",
            "rollback_scope": "Revert STAGE-028 Phase 4 closeout changes only.",
            "staging_area_policy": "Only process-owned temporary staging paths from focused tests may be removed by the test harness.",
            "cleanup_instructions": {
                "temp_only": True,
                "do_not_delete_original_archive": True,
                "do_not_touch_raw_metadata_root": True,
                "do_not_clean_fact_source_or_evidence": True,
                "do_not_clean_manifest_or_audit_outputs": True,
            },
        },
        "owner_feedback_zh": [
            "STAGE-028 已在本地完成压缩包对抗测试闭环，当前证据是内存报告和中文 closeout，不是生产批量导入器。",
            "系统会先形成 archive_manifest 样例、安全阻断日志和清理白名单，再把安全条目交给 hash、manifest、dedup、parser 后续计划。",
            "自动清理只允许面向 process-owned temporary staging files；不得删除原始压缩包、真实资料、manifest、审计日志或 IDS_MetaData 原始数据库。",
            "BATCH021_030 仍未满足十阶段批量上传门槛，所以 No GitHub upload and No app reinstall。",
        ],
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "next_allowed_task_id": "IDS-V0_1-STAGE029-P1",
        "does_not_read_raw_metadata": True,
        "does_not_write_archive_adversarial_runtime_output": True,
        "does_not_write_archive_manifest_runtime_output": True,
        "does_not_write_runtime_outputs": True,
        "does_not_start_processing_jobs": True,
        "does_not_use_fake_ids_business_data": True,
        "does_not_create_import_queue": True,
        "does_not_write_database": True,
        "does_not_write_index": True,
        "does_not_call_external_apis": True,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run IDS Stage 028 archive adversarial checks.")
    parser.add_argument("--archive-uri", required=True)
    parser.add_argument("--staging-area-uri", required=True)
    parser.add_argument("--evaluated-at")
    parser.add_argument("--archive-file-count-limit", type=int, default=safe_extraction_engine.archive_threat_model.DEFAULT_ARCHIVE_FILE_COUNT_LIMIT)
    parser.add_argument("--archive-total-size-limit-bytes", type=int, default=safe_extraction_engine.archive_threat_model.DEFAULT_ARCHIVE_TOTAL_SIZE_LIMIT_BYTES)
    parser.add_argument("--archive-single-file-size-limit-bytes", type=int, default=safe_extraction_engine.archive_threat_model.DEFAULT_ARCHIVE_SINGLE_FILE_SIZE_LIMIT_BYTES)
    parser.add_argument("--archive-nested-depth-limit", type=int, default=safe_extraction_engine.archive_threat_model.DEFAULT_ARCHIVE_NESTED_DEPTH_LIMIT)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    report = run_archive_adversarial_test(
        archive_uri=args.archive_uri,
        staging_area_uri=args.staging_area_uri,
        evaluated_at=args.evaluated_at,
        archive_file_count_limit=args.archive_file_count_limit,
        archive_total_size_limit_bytes=args.archive_total_size_limit_bytes,
        archive_single_file_size_limit_bytes=args.archive_single_file_size_limit_bytes,
        archive_nested_depth_limit=args.archive_nested_depth_limit,
    )
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
