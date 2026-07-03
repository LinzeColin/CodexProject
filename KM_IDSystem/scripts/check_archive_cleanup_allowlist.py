#!/usr/bin/env python3
"""Stage 029 archive cleanup allowlist slice for IDS."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import check_archive_adversarial_tests as archive_adversarial


ENTRANCE = "IDS 系统运营入口"
ARCHIVE_CLEANUP_SCHEMA = "ids.stage029.archive_cleanup_allowlist.v1"
ARCHIVE_CLEANUP_ALLOWLIST_ID_PREFIX = "ids.stage029.cleanup_allowlist"
REQUIRED_PIPELINE = ["hash", "manifest", "dedup", "parser"]
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
NO_PERSISTENCE_DELTAS = {
    "document_delta": 0,
    "chunk_delta": 0,
    "job_delta": 0,
    "index_delta": 0,
    "import_write_delta": 0,
    "manifest_write_delta": 0,
    "archive_manifest_write_delta": 0,
    "archive_cleanup_runtime_output_delta": 0,
    "cleanup_write_delta": 0,
    "deletion_delta": 0,
    "evidence_write_delta": 0,
    "audit_write_delta": 0,
    "report_write_delta": 0,
    "database_write_delta": 0,
    "runtime_output_delta": 0,
}
PROTECTED_CLASSES = {
    "PROTECTED_ORIGINAL_ARCHIVE",
    "PROTECTED_ORIGINAL_MATERIAL",
    "PROTECTED_ARCHIVE_MANIFEST",
    "PROTECTED_EVIDENCE_LEDGER",
    "PROTECTED_AUDIT_LOG",
    "PROTECTED_DELIVERED_REPORT",
    "PROTECTED_DATABASE_OR_INDEX",
    "PROTECTED_RAW_METADATA_ROOT",
}


def _stable_id(prefix: str, payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return f"{prefix}.{hashlib.sha256(encoded).hexdigest()[:24]}"


def _protected_refs(*, original_archive_ref: str, archive_manifest_ref: str) -> list[dict[str, Any]]:
    return [
        {
            "protected_class": "PROTECTED_ORIGINAL_ARCHIVE",
            "protected_ref": original_archive_ref,
            "cleanup_allowed": False,
        },
        {
            "protected_class": "PROTECTED_ORIGINAL_MATERIAL",
            "protected_ref": "original_material_ref",
            "cleanup_allowed": False,
        },
        {
            "protected_class": "PROTECTED_ARCHIVE_MANIFEST",
            "protected_ref": archive_manifest_ref,
            "cleanup_allowed": False,
        },
        {
            "protected_class": "PROTECTED_EVIDENCE_LEDGER",
            "protected_ref": "evidence://stage029/evidence-ledger",
            "cleanup_allowed": False,
        },
        {
            "protected_class": "PROTECTED_AUDIT_LOG",
            "protected_ref": "audit://stage029/audit-log",
            "cleanup_allowed": False,
        },
        {
            "protected_class": "PROTECTED_DELIVERED_REPORT",
            "protected_ref": "report://stage029/delivered-report",
            "cleanup_allowed": False,
        },
        {
            "protected_class": "PROTECTED_DATABASE_OR_INDEX",
            "protected_ref": "runtime://database-index-parser-output",
            "cleanup_allowed": False,
        },
        {
            "protected_class": "PROTECTED_RAW_METADATA_ROOT",
            "protected_ref": "/Users/linzezhang/Downloads/IDS_MetaData",
            "cleanup_allowed": False,
        },
    ]


def _is_protected_candidate(candidate: dict[str, Any], protected_refs: list[dict[str, Any]]) -> bool:
    candidate_class = str(candidate.get("cleanup_candidate_class") or candidate.get("cleanup_class") or "")
    candidate_uri = str(candidate.get("uri") or candidate.get("cleanup_candidate_uri") or "")
    if candidate_class in PROTECTED_CLASSES:
        return True
    protected_uris = {str(item["protected_ref"]) for item in protected_refs}
    if candidate_uri in protected_uris:
        return True
    raw_metadata_root = "/Users/linzezhang/Downloads/IDS_MetaData"
    return candidate_uri.startswith(raw_metadata_root) or candidate_uri.startswith(f"file://{raw_metadata_root}")


def _candidate_from_allowlist_item(
    *,
    item: dict[str, Any],
    protected_refs: list[dict[str, Any]],
) -> dict[str, Any]:
    uri = str(item["uri"])
    candidate_class = str(item.get("cleanup_class", "ARCHIVE_STAGING_TEMP_FILE"))
    protected = _is_protected_candidate(
        {"uri": uri, "cleanup_candidate_class": candidate_class},
        protected_refs,
    )
    decision_state = (
        "ARCHIVE_CLEANUP_BLOCKED_PROTECTED_REF"
        if protected
        else "ARCHIVE_CLEANUP_READY_FOR_TEMP_CLEANUP"
        if candidate_class == "ARCHIVE_STAGING_TEMP_FILE"
        else "ARCHIVE_CLEANUP_OWNER_REVIEW_REQUIRED"
    )
    return {
        "cleanup_candidate_id": _stable_id(
            "ids.stage029.cleanup_candidate",
            {"uri": uri, "class": candidate_class},
        ),
        "cleanup_candidate_uri": uri,
        "cleanup_candidate_class": candidate_class,
        "cleanup_allowlist_ref": ARCHIVE_CLEANUP_ALLOWLIST_ID_PREFIX,
        "cleanup_decision_state": decision_state,
        "cleanup_reason_code": (
            "CLEANUP_PROTECTED_REF_BLOCKED"
            if protected
            else "CLEANUP_STAGING_TEMP_FILE_ALLOWED"
            if candidate_class == "ARCHIVE_STAGING_TEMP_FILE"
            else "CLEANUP_OWNER_REVIEW_REQUIRED"
        ),
        "cleanup_protected_ref": uri if protected else None,
        "cleanup_executed": False,
        "delete_operation_started": False,
        "source_cleanup_record": deepcopy(item),
    }


def _candidate_from_additional(
    *,
    item: dict[str, Any],
    protected_refs: list[dict[str, Any]],
) -> dict[str, Any]:
    uri = str(item.get("uri") or item.get("cleanup_candidate_uri") or "")
    candidate_class = str(item.get("cleanup_candidate_class") or item.get("cleanup_class") or "UNKNOWN_CLEANUP_CANDIDATE")
    return _candidate_from_allowlist_item(
        item={"uri": uri, "cleanup_class": candidate_class, "source": "additional_cleanup_candidate"},
        protected_refs=protected_refs,
    )


def _map_risk_entry(entry: dict[str, Any]) -> dict[str, Any]:
    mapped = deepcopy(entry)
    risk_code = str(mapped.get("risk_code") or "")
    mapped["cleanup_routing_state"] = (
        "ARCHIVE_CLEANUP_QUARANTINE_REQUIRED"
        if "LIMIT" in risk_code or "PATH" in risk_code or "GARBLE" in risk_code
        else "ARCHIVE_CLEANUP_OWNER_REVIEW_REQUIRED"
    )
    mapped["cleanup_owner_review_state"] = "ARCHIVE_CLEANUP_OWNER_REVIEW_REQUIRED"
    mapped["cleanup_quarantine_state"] = "ARCHIVE_CLEANUP_QUARANTINE_REQUIRED"
    mapped["cleanup_executed"] = False
    mapped["delete_operation_started"] = False
    return mapped


def _manual_review_routing(risk_entries: list[dict[str, Any]]) -> dict[str, Any]:
    risk_codes = {str(entry.get("risk_code") or "") for entry in risk_entries}
    return {
        "state": (
            "ARCHIVE_CLEANUP_OWNER_REVIEW_OR_QUARANTINE_REQUIRED"
            if risk_entries
            else "ARCHIVE_CLEANUP_OWNER_REVIEW_NOT_REQUIRED"
        ),
        "failure_files_to_owner_review": bool(risk_entries),
        "risk_files_to_owner_review": bool(risk_entries),
        "over_limit_files_to_owner_review": any("LIMIT" in code for code in risk_codes),
        "quarantine_required": bool(risk_entries),
        "owner_review_entry_count": len(risk_entries),
        "quarantine_entry_count": len(risk_entries),
    }


def _reingest_validation(post_extract_reingest: dict[str, Any]) -> dict[str, Any]:
    queue = list(post_extract_reingest.get("reingest_queue", []))
    return {
        "state": (
            "ARCHIVE_CLEANUP_REINGEST_READY_FOR_PIPELINE"
            if queue
            else "ARCHIVE_CLEANUP_REINGEST_NOT_READY"
        ),
        "required_pipeline": list(REQUIRED_PIPELINE),
        "safe_extracted_file_count": len(queue),
        "pipeline_stage_states": {
            "hash": "ARCHIVE_CLEANUP_HASH_REQUIRED",
            "manifest": "ARCHIVE_CLEANUP_MANIFEST_REQUIRED",
            "dedup": "ARCHIVE_CLEANUP_DEDUP_REQUIRED",
            "parser": "ARCHIVE_CLEANUP_PARSER_REQUIRED",
        },
        "reingest_queue": queue,
        "actual_jobs_started": dict(ZERO_JOB_STARTS),
        "import_queue_created": False,
    }


def _cleanup_validation(
    *,
    candidates: list[dict[str, Any]],
    protected_refs: list[dict[str, Any]],
    original_archive_ref: str,
) -> dict[str, Any]:
    ready_candidates = [
        candidate
        for candidate in candidates
        if candidate["cleanup_decision_state"] == "ARCHIVE_CLEANUP_READY_FOR_TEMP_CLEANUP"
    ]
    blocked_candidates = [
        candidate
        for candidate in candidates
        if candidate["cleanup_decision_state"] == "ARCHIVE_CLEANUP_BLOCKED_PROTECTED_REF"
    ]
    ready_classes = {candidate["cleanup_candidate_class"] for candidate in ready_candidates}
    ready_uris = [candidate["cleanup_candidate_uri"] for candidate in ready_candidates]
    original_archive_in_cleanup = original_archive_ref in ready_uris
    protected_ref_uris = {str(item["protected_ref"]) for item in protected_refs}
    protected_ready = any(uri in protected_ref_uris for uri in ready_uris)
    temp_only = bool(ready_candidates) and ready_classes <= {"ARCHIVE_STAGING_TEMP_FILE"}
    protected_refs_preserved = not original_archive_in_cleanup and not protected_ready
    if blocked_candidates:
        state = "ARCHIVE_CLEANUP_ALLOWLIST_REVIEW_REQUIRED"
    elif temp_only and protected_refs_preserved:
        state = "ARCHIVE_CLEANUP_ALLOWLIST_VALIDATED"
    else:
        state = "ARCHIVE_CLEANUP_ALLOWLIST_REVIEW_REQUIRED"
    return {
        "state": state,
        "allowed_cleanup_classes": sorted(ready_classes),
        "cleanup_allowlist_uris": ready_uris,
        "cleanup_targets_are_staging_temp_files_only": temp_only,
        "original_archive_in_cleanup_allowlist": original_archive_in_cleanup,
        "protected_refs_preserved": protected_refs_preserved,
        "does_not_clean_original_archive": not original_archive_in_cleanup,
        "does_not_clean_fact_source_or_evidence": protected_refs_preserved,
        "blocked_protected_candidate_count": len(blocked_candidates),
    }


def _decision_state(
    *,
    candidates: list[dict[str, Any]],
    risk_entries: list[dict[str, Any]],
    cleanup_validation: dict[str, Any],
) -> str:
    if risk_entries or cleanup_validation["blocked_protected_candidate_count"]:
        return "ARCHIVE_CLEANUP_OWNER_REVIEW_REQUIRED"
    if candidates and cleanup_validation["state"] == "ARCHIVE_CLEANUP_ALLOWLIST_VALIDATED":
        return "ARCHIVE_CLEANUP_READY_FOR_TEMP_CLEANUP"
    return "ARCHIVE_CLEANUP_OWNER_REVIEW_REQUIRED"


def build_archive_cleanup_allowlist(
    *,
    archive_uri: str,
    staging_area_uri: str,
    evaluated_at: str | None = None,
    archive_file_count_limit: int = archive_adversarial.safe_extraction_engine.archive_threat_model.DEFAULT_ARCHIVE_FILE_COUNT_LIMIT,
    archive_total_size_limit_bytes: int = archive_adversarial.safe_extraction_engine.archive_threat_model.DEFAULT_ARCHIVE_TOTAL_SIZE_LIMIT_BYTES,
    archive_single_file_size_limit_bytes: int = (
        archive_adversarial.safe_extraction_engine.archive_threat_model.DEFAULT_ARCHIVE_SINGLE_FILE_SIZE_LIMIT_BYTES
    ),
    archive_nested_depth_limit: int = archive_adversarial.safe_extraction_engine.archive_threat_model.DEFAULT_ARCHIVE_NESTED_DEPTH_LIMIT,
    additional_cleanup_candidates: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build an in-memory cleanup allowlist and protected-ref routing plan."""

    archive_report = archive_adversarial.run_archive_adversarial_test(
        archive_uri=archive_uri,
        staging_area_uri=staging_area_uri,
        evaluated_at=evaluated_at,
        archive_file_count_limit=archive_file_count_limit,
        archive_total_size_limit_bytes=archive_total_size_limit_bytes,
        archive_single_file_size_limit_bytes=archive_single_file_size_limit_bytes,
        archive_nested_depth_limit=archive_nested_depth_limit,
    )
    original_archive_ref = str(archive_report.get("original_archive_ref") or archive_uri)
    archive_manifest_ref = str(archive_report.get("archive_manifest_ref") or "in_memory_stage029_archive_manifest")
    protected_refs = _protected_refs(
        original_archive_ref=original_archive_ref,
        archive_manifest_ref=archive_manifest_ref,
    )
    cleanup_candidates = [
        _candidate_from_allowlist_item(item=item, protected_refs=protected_refs)
        for item in archive_report.get("cleanup_allowlist", [])
    ]
    for item in additional_cleanup_candidates or []:
        cleanup_candidates.append(_candidate_from_additional(item=item, protected_refs=protected_refs))

    risk_entries = [_map_risk_entry(entry) for entry in archive_report.get("risk_entries", [])]
    post_extract_reingest = deepcopy(archive_report.get("post_extract_reingest", {}))
    post_extract_reingest["required_pipeline"] = list(REQUIRED_PIPELINE)
    reingest_validation = _reingest_validation(post_extract_reingest)
    cleanup_validation = _cleanup_validation(
        candidates=cleanup_candidates,
        protected_refs=protected_refs,
        original_archive_ref=original_archive_ref,
    )
    allowlist_id = _stable_id(
        ARCHIVE_CLEANUP_ALLOWLIST_ID_PREFIX,
        {
            "archive_uri": archive_uri,
            "staging_area_uri": staging_area_uri,
            "evaluated_at": archive_report.get("evaluated_at"),
        },
    )

    return {
        "schema_version": ARCHIVE_CLEANUP_SCHEMA,
        "source_schema_version": archive_report.get("schema_version"),
        "stage": "STAGE-029",
        "phase": "Phase 2",
        "task_id": "IDS-V0_1-STAGE029-P2",
        "acceptance_id": "ACC-STAGE-029",
        "entrance": ENTRANCE,
        "archive_cleanup_allowlist_id": allowlist_id,
        "archive_security_boundary_id": "ids.stage024.archive_security_boundary",
        "cleanup_request_ref": "owner-approved-future-cleanup-request",
        "evaluated_at": archive_report.get("evaluated_at"),
        "archive_type": archive_report.get("archive_type"),
        "archive_source_uri": archive_report.get("archive_source_uri"),
        "original_archive_ref": original_archive_ref,
        "archive_staging_area_uri": archive_report.get("archive_staging_area_uri"),
        "archive_manifest_ref": archive_manifest_ref,
        "safe_extraction_ref": archive_report.get("safe_extraction_ref"),
        "post_extract_reingest_ref": "in_memory_stage029_post_extract_reingest",
        "limits": dict(archive_report.get("limits", {})),
        "safe_extracted_entries": deepcopy(archive_report.get("safe_extracted_entries", [])),
        "safe_extracted_file_count": int(archive_report.get("safe_extracted_file_count", 0) or 0),
        "risk_entries": risk_entries,
        "owner_review_entries": risk_entries,
        "quarantine_entries": risk_entries,
        "blocked_entry_count": len(risk_entries),
        "owner_review_entry_count": len(risk_entries),
        "quarantine_entry_count": len(risk_entries),
        "manual_review_routing": _manual_review_routing(risk_entries),
        "post_extract_reingest": post_extract_reingest,
        "reingest_validation": reingest_validation,
        "cleanup_allowlist": [
            candidate
            for candidate in cleanup_candidates
            if candidate["cleanup_decision_state"] == "ARCHIVE_CLEANUP_READY_FOR_TEMP_CLEANUP"
        ],
        "cleanup_candidates": cleanup_candidates,
        "cleanup_candidate_count": len(cleanup_candidates),
        "protected_refs": protected_refs,
        "blocked_protected_candidate_count": cleanup_validation["blocked_protected_candidate_count"],
        "cleanup_validation": cleanup_validation,
        "cleanup_decision_state": _decision_state(
            candidates=cleanup_candidates,
            risk_entries=risk_entries,
            cleanup_validation=cleanup_validation,
        ),
        "processing_guard": dict(ZERO_JOB_STARTS),
        "no_persistence_deltas": dict(NO_PERSISTENCE_DELTAS),
        "cleanup_runner_executed": False,
        "does_not_delete_files": True,
        "does_not_clean_original_archive": cleanup_validation["does_not_clean_original_archive"],
        "does_not_clean_fact_source_or_evidence": cleanup_validation["does_not_clean_fact_source_or_evidence"],
        "does_not_clean_manifest_or_audit_outputs": True,
        "does_not_write_archive_cleanup_runtime_output": True,
        "does_not_write_archive_manifest_runtime_output": True,
        "does_not_write_database": True,
        "does_not_write_reports": True,
        "does_not_write_evidence_ledger": True,
        "does_not_write_audit_log": True,
        "does_not_write_index": True,
        "does_not_write_document_chunk_job_import_rows": True,
        "does_not_start_processing_jobs": True,
        "does_not_call_external_apis": True,
        "does_not_read_raw_metadata": archive_report.get("does_not_read_raw_metadata", True),
        "does_not_use_fake_ids_business_data": True,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run IDS Stage 029 archive cleanup allowlist checks.")
    parser.add_argument("--archive-uri", required=True)
    parser.add_argument("--staging-area-uri", required=True)
    parser.add_argument("--evaluated-at")
    parser.add_argument("--archive-file-count-limit", type=int, default=archive_adversarial.safe_extraction_engine.archive_threat_model.DEFAULT_ARCHIVE_FILE_COUNT_LIMIT)
    parser.add_argument("--archive-total-size-limit-bytes", type=int, default=archive_adversarial.safe_extraction_engine.archive_threat_model.DEFAULT_ARCHIVE_TOTAL_SIZE_LIMIT_BYTES)
    parser.add_argument(
        "--archive-single-file-size-limit-bytes",
        type=int,
        default=archive_adversarial.safe_extraction_engine.archive_threat_model.DEFAULT_ARCHIVE_SINGLE_FILE_SIZE_LIMIT_BYTES,
    )
    parser.add_argument("--archive-nested-depth-limit", type=int, default=archive_adversarial.safe_extraction_engine.archive_threat_model.DEFAULT_ARCHIVE_NESTED_DEPTH_LIMIT)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    report = build_archive_cleanup_allowlist(
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
