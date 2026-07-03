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
