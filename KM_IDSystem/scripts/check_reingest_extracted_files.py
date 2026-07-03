#!/usr/bin/env python3
"""Stage 027 in-memory re-ingest wrapper for safely extracted IDS files."""

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

import check_archive_manifest as archive_manifest
import check_import_idempotency as import_idempotency


ENTRANCE = "IDS 系统运营入口"
REINGEST_SCHEMA = "ids.stage027.reingest_extracted_files.v1"
REINGEST_PREFIX = "ids.stage027.reingest"
REQUIRED_PIPELINE = ["hash", "manifest", "dedup", "parser"]
NO_PERSISTENCE_DELTAS = {
    "document_delta": 0,
    "chunk_delta": 0,
    "job_delta": 0,
    "index_delta": 0,
    "import_write_delta": 0,
    "manifest_write_delta": 0,
    "duplicate_write_delta": 0,
    "reingest_write_delta": 0,
    "runtime_output_delta": 0,
    "import_queue_delta": 0,
}
ACTUAL_JOBS_STARTED = {"hash": 0, "manifest": 0, "dedup": 0, "parser": 0}


def _reingest_idempotency_key(*, manifest_id: str, import_key: str, source_uri: str) -> str:
    seed = {
        "archive_manifest_id": manifest_id,
        "import_idempotency_key": import_key,
        "source_uri": source_uri,
    }
    encoded = json.dumps(seed, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "ids-reingest-sha256-" + hashlib.sha256(encoded).hexdigest()


def _safe_entry_uri(entry: dict[str, Any]) -> str | None:
    for key in (
        "staging_uri",
        "extracted_file_uri",
        "safe_extracted_uri",
        "target_uri",
        "uri",
    ):
        value = entry.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def _safe_entries_by_uri(entries: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_uri: dict[str, dict[str, Any]] = {}
    for entry in entries:
        uri = _safe_entry_uri(entry)
        if uri is not None:
            by_uri[uri] = entry
    return by_uri


def _risk_code_from_archive(risk_code: str | None) -> str:
    if not risk_code:
        return "REINGEST_UNKNOWN_ARCHIVE_RISK"
    for prefix in ("ARCHIVE_MANIFEST_", "SAFE_EXTRACTION_", "ARCHIVE_"):
        if risk_code.startswith(prefix):
            return "REINGEST_" + risk_code.removeprefix(prefix)
    return "REINGEST_" + risk_code


def _risk_item_from_archive(item: dict[str, Any]) -> dict[str, Any]:
    risk = deepcopy(item)
    source_code = risk.get("risk_code")
    risk["source_risk_code"] = source_code
    risk["risk_code"] = _risk_code_from_archive(source_code if isinstance(source_code, str) else None)
    risk["reingest_routing_state"] = (
        "REINGEST_OWNER_REVIEW_REQUIRED"
        if risk["risk_code"].endswith("FORMAT_REQUIRES_EXTERNAL_ADAPTER")
        else "REINGEST_BLOCKED"
    )
    return risk


def _risk_item_from_import_rejection(item: dict[str, Any]) -> dict[str, Any]:
    import_state = item.get("import_state", "IMPORT_UNKNOWN")
    return {
        "risk_code": f"REINGEST_{import_state.removeprefix('IMPORT_')}",
        "source_import_state": import_state,
        "source_uri": item.get("source_uri"),
        "source_path": item.get("source_path"),
        "reason": item.get("reason"),
        "reingest_routing_state": "REINGEST_BLOCKED",
    }


def _record_state(import_state: str) -> str:
    if import_state in {"IMPORT_KEY_READY", "IMPORT_SINGLE_REPEAT"}:
        return "REINGEST_READY_FOR_IMPORT_QUEUE"
    if import_state in {"IMPORT_DUPLICATE_CONTENT", "IMPORT_KEY_CONFLICT"}:
        return "REINGEST_OWNER_REVIEW_REQUIRED"
    return "REINGEST_BLOCKED"


def _pipeline_stage_states(record_state: str) -> dict[str, str]:
    if record_state == "REINGEST_READY_FOR_IMPORT_QUEUE":
        return {
            "hash": "REINGEST_HASH_OBSERVED",
            "manifest": "REINGEST_MANIFEST_READY",
            "dedup": "REINGEST_DEDUP_READY",
            "parser": "REINGEST_PARSER_READY_FOR_HANDOFF",
        }
    if record_state == "REINGEST_OWNER_REVIEW_REQUIRED":
        return {
            "hash": "REINGEST_HASH_OBSERVED",
            "manifest": "REINGEST_MANIFEST_OWNER_REVIEW_REQUIRED",
            "dedup": "REINGEST_DEDUP_OWNER_REVIEW_REQUIRED",
            "parser": "REINGEST_PARSER_BLOCKED_OWNER_REVIEW",
        }
    return {
        "hash": "REINGEST_HASH_BLOCKED",
        "manifest": "REINGEST_MANIFEST_BLOCKED",
        "dedup": "REINGEST_DEDUP_BLOCKED",
        "parser": "REINGEST_PARSER_BLOCKED",
    }


def _reingest_record(
    *,
    import_record: dict[str, Any],
    safe_entry: dict[str, Any] | None,
    manifest_report: dict[str, Any],
) -> dict[str, Any]:
    import_state = str(import_record["import_state"])
    record_state = _record_state(import_state)
    source_uri = str(import_record["source_uri"])
    import_key = str(import_record["import_idempotency_key"])
    manifest_id = str(manifest_report["archive_manifest_id"])
    reingest_key = _reingest_idempotency_key(
        manifest_id=manifest_id,
        import_key=import_key,
        source_uri=source_uri,
    )
    entry_path = safe_entry.get("entry_path") if safe_entry else None
    normalized_entry_path = safe_entry.get("normalized_entry_path") if safe_entry else None
    return {
        "reingest_job_id": reingest_key.replace("ids-reingest-sha256-", f"{REINGEST_PREFIX}.job.", 1),
        "reingest_batch_id": f"{REINGEST_PREFIX}.batch.{manifest_id.rsplit('.', 1)[-1]}",
        "reingest_record_state": record_state,
        "extracted_file_ref": f"{manifest_id}:{normalized_entry_path or entry_path or source_uri}",
        "extracted_file_uri": source_uri,
        "extracted_file_sha256": import_record["sha256"],
        "extracted_file_size_bytes": import_record["file_size"],
        "archive_manifest_ref": manifest_id,
        "original_archive_ref": manifest_report.get("original_archive_ref"),
        "safe_extraction_ref": manifest_report.get("source_schema_version"),
        "archive_entry_path": entry_path,
        "normalized_entry_path": normalized_entry_path,
        "reingest_source_state": "REINGEST_SOURCE_SAFE_EXTRACTED",
        "reingest_idempotency_key": reingest_key,
        "reingest_duplicate_policy": "REINGEST_DEDUP_BEFORE_PARSER",
        "reingest_owner_decision_state": record_state,
        "import_state": import_state,
        "import_idempotency_key": import_key,
        "content_identity_id": import_record.get("content_identity_id"),
        "manifest_identity": import_record.get("manifest_identity"),
        "source_path": import_record.get("source_path"),
        "basename": import_record.get("basename"),
        "pipeline_stage_states": _pipeline_stage_states(record_state),
        "actual_jobs_started": dict(ACTUAL_JOBS_STARTED),
    }


def _decision_state(records: list[dict[str, Any]], risk_items: list[dict[str, Any]]) -> str:
    if risk_items and not records:
        return "REINGEST_BLOCKED"
    states = {record["reingest_record_state"] for record in records}
    if "REINGEST_BLOCKED" in states:
        return "REINGEST_BLOCKED"
    if "REINGEST_OWNER_REVIEW_REQUIRED" in states:
        return "REINGEST_OWNER_REVIEW_REQUIRED"
    if records:
        return "REINGEST_READY_FOR_IMPORT_QUEUE"
    return "REINGEST_BLOCKED"


def _no_safe_entry_risk(manifest_report: dict[str, Any]) -> dict[str, Any]:
    return {
        "risk_code": "REINGEST_NO_SAFE_EXTRACTED_ENTRIES",
        "source_archive_manifest_state": manifest_report.get("archive_manifest_decision_state"),
        "archive_source_uri": manifest_report.get("archive_source_uri"),
        "reingest_routing_state": "REINGEST_BLOCKED",
    }


def build_reingest_extracted_files(
    *,
    archive_uri: str,
    staging_area_uri: str,
    evaluated_at: str | None = None,
    archive_file_count_limit: int = archive_manifest.archive_threat_model.DEFAULT_ARCHIVE_FILE_COUNT_LIMIT,
    archive_total_size_limit_bytes: int = archive_manifest.archive_threat_model.DEFAULT_ARCHIVE_TOTAL_SIZE_LIMIT_BYTES,
    archive_single_file_size_limit_bytes: int = archive_manifest.archive_threat_model.DEFAULT_ARCHIVE_SINGLE_FILE_SIZE_LIMIT_BYTES,
    archive_nested_depth_limit: int = archive_manifest.archive_threat_model.DEFAULT_ARCHIVE_NESTED_DEPTH_LIMIT,
) -> dict[str, Any]:
    """Build an in-memory re-ingest plan from Stage 026 safe extracted files."""

    evaluated_at = evaluated_at or archive_manifest.archive_threat_model._utc_now()
    manifest_report = archive_manifest.build_archive_manifest(
        archive_uri=archive_uri,
        staging_area_uri=staging_area_uri,
        manifested_at=evaluated_at,
        archive_file_count_limit=archive_file_count_limit,
        archive_total_size_limit_bytes=archive_total_size_limit_bytes,
        archive_single_file_size_limit_bytes=archive_single_file_size_limit_bytes,
        archive_nested_depth_limit=archive_nested_depth_limit,
    )
    safe_entries = list(manifest_report.get("safe_extracted_entries", []))
    safe_entry_by_uri = _safe_entries_by_uri(safe_entries)
    source_uris = [uri for uri in (_safe_entry_uri(entry) for entry in safe_entries) if uri is not None]
    import_report = import_idempotency.evaluate_import_idempotency(
        source_uris=source_uris,
        batch_id=str(manifest_report["archive_manifest_id"]),
        first_seen_at=evaluated_at,
        import_checked_at=evaluated_at,
    )
    records = [
        _reingest_record(
            import_record=record,
            safe_entry=safe_entry_by_uri.get(record["source_uri"]),
            manifest_report=manifest_report,
        )
        for record in import_report["import_records"]
    ]
    risk_items = [_risk_item_from_archive(item) for item in manifest_report.get("archive_risk_items", [])]
    risk_items.extend(_risk_item_from_import_rejection(item) for item in import_report.get("rejected_inputs", []))
    if not records and not risk_items:
        risk_items.append(_no_safe_entry_risk(manifest_report))
    decision_state = _decision_state(records, risk_items)
    blocked_count = sum(1 for record in records if record["reingest_record_state"] == "REINGEST_BLOCKED")
    owner_review_count = sum(
        1 for record in records if record["reingest_record_state"] == "REINGEST_OWNER_REVIEW_REQUIRED"
    )
    if decision_state == "REINGEST_BLOCKED" and not records:
        blocked_count = max(1, len(risk_items))

    return {
        "schema_version": REINGEST_SCHEMA,
        "source_schema_version": manifest_report.get("schema_version"),
        "stage": "STAGE-027",
        "phase": "Phase 2",
        "task_id": "IDS-V0_1-STAGE027-P2",
        "acceptance_id": "ACC-STAGE-027",
        "entrance": ENTRANCE,
        "evaluated_at": evaluated_at,
        "archive_source_uri": archive_uri,
        "archive_staging_area_uri": staging_area_uri,
        "archive_manifest_ref": manifest_report["archive_manifest_id"],
        "original_archive_ref": manifest_report.get("original_archive_ref"),
        "source_archive_manifest_decision_state": manifest_report.get("archive_manifest_decision_state"),
        "source_import_idempotency_state": import_report.get("overall_state"),
        "reingest_decision_state": decision_state,
        "reingest_required_pipeline": list(REQUIRED_PIPELINE),
        "actual_jobs_started": dict(ACTUAL_JOBS_STARTED),
        "reingest_records": records,
        "reingest_record_count": len(records),
        "reingest_risk_items": risk_items,
        "reingest_risk_item_count": len(risk_items),
        "blocked_reingest_count": blocked_count,
        "owner_review_count": owner_review_count,
        "duplicate_content_count": int(import_report.get("duplicate_content_count", 0) or 0),
        "key_conflict_count": int(import_report.get("key_conflict_count", 0) or 0),
        "repeated_import_count": int(import_report.get("repeated_import_count", 0) or 0),
        "safe_extracted_file_count": int(manifest_report.get("safe_extracted_file_count", 0) or 0),
        "archive_risk_item_count": int(manifest_report.get("archive_blocked_entry_count", 0) or 0),
        "import_record_count": int(import_report.get("import_record_count", 0) or 0),
        "import_rejected_input_count": int(import_report.get("rejected_input_count", 0) or 0),
        "no_persistence_deltas": dict(NO_PERSISTENCE_DELTAS),
        "does_not_write_reingest_runtime_output": True,
        "does_not_create_import_queue": True,
        "does_not_create_documents_chunks_jobs": True,
        "does_not_write_database": True,
        "does_not_write_index": True,
        "does_not_read_raw_metadata": True,
        "does_not_start_processing_jobs": True,
        "does_not_use_fake_ids_business_data": True,
        "does_not_call_external_apis": True,
        "does_not_write_runtime_outputs": True,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build an in-memory STAGE-027 re-ingest plan.")
    parser.add_argument("--archive-uri", required=True)
    parser.add_argument("--staging-area-uri", required=True)
    parser.add_argument("--evaluated-at")
    parser.add_argument("--archive-file-count-limit", type=int, default=archive_manifest.archive_threat_model.DEFAULT_ARCHIVE_FILE_COUNT_LIMIT)
    parser.add_argument("--archive-total-size-limit-bytes", type=int, default=archive_manifest.archive_threat_model.DEFAULT_ARCHIVE_TOTAL_SIZE_LIMIT_BYTES)
    parser.add_argument("--archive-single-file-size-limit-bytes", type=int, default=archive_manifest.archive_threat_model.DEFAULT_ARCHIVE_SINGLE_FILE_SIZE_LIMIT_BYTES)
    parser.add_argument("--archive-nested-depth-limit", type=int, default=archive_manifest.archive_threat_model.DEFAULT_ARCHIVE_NESTED_DEPTH_LIMIT)
    args = parser.parse_args(argv)

    report = build_reingest_extracted_files(
        archive_uri=args.archive_uri,
        staging_area_uri=args.staging_area_uri,
        evaluated_at=args.evaluated_at,
        archive_file_count_limit=args.archive_file_count_limit,
        archive_total_size_limit_bytes=args.archive_total_size_limit_bytes,
        archive_single_file_size_limit_bytes=args.archive_single_file_size_limit_bytes,
        archive_nested_depth_limit=args.archive_nested_depth_limit,
    )
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
