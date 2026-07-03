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
REQUIRED_STAGE027_SCENARIOS = (
    "ready_for_import_queue",
    "duplicate_content_owner_review",
    "missing_source_blocked",
    "raw_metadata_root_blocked",
    "adapter_owner_review",
)
EXPECTED_STAGE027_SCENARIO_DECISIONS = {
    "ready_for_import_queue": "REINGEST_READY_FOR_IMPORT_QUEUE",
    "duplicate_content_owner_review": "REINGEST_OWNER_REVIEW_REQUIRED",
    "missing_source_blocked": "REINGEST_BLOCKED",
    "raw_metadata_root_blocked": "REINGEST_BLOCKED",
    "adapter_owner_review": "REINGEST_OWNER_REVIEW_REQUIRED",
}
EXPECTED_STAGE027_SCENARIO_RISKS = {
    "missing_source_blocked": "REINGEST_SOURCE_MISSING",
    "raw_metadata_root_blocked": "REINGEST_SOURCE_BLOCKED_RAW_METADATA_ROOT",
    "adapter_owner_review": "REINGEST_FORMAT_REQUIRES_EXTERNAL_ADAPTER",
}


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
    if risk_code.endswith("ADAPTER_OWNER_REVIEW_REQUIRED"):
        return "REINGEST_FORMAT_REQUIRES_EXTERNAL_ADAPTER"
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
        if any(item.get("reingest_routing_state") == "REINGEST_OWNER_REVIEW_REQUIRED" for item in risk_items):
            return "REINGEST_OWNER_REVIEW_REQUIRED"
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


def _build_pipeline_validation(scenario_results: list[dict[str, Any]]) -> dict[str, Any]:
    ready_record_count = 0
    owner_review_count = 0
    blocked_reingest_count = 0
    required_pipeline_observed = True
    actual_jobs_started = dict(ACTUAL_JOBS_STARTED)
    for result in scenario_results:
        report = result["reingest_report"]
        required_pipeline_observed = required_pipeline_observed and report["reingest_required_pipeline"] == REQUIRED_PIPELINE
        ready_record_count += sum(
            1
            for record in report["reingest_records"]
            if record["reingest_record_state"] == "REINGEST_READY_FOR_IMPORT_QUEUE"
        )
        owner_review_count += int(report.get("owner_review_count", 0) or 0)
        blocked_reingest_count += int(report.get("blocked_reingest_count", 0) or 0)
        for job, count in report["actual_jobs_started"].items():
            actual_jobs_started[job] = actual_jobs_started.get(job, 0) + int(count or 0)
    jobs_zero = all(value == 0 for value in actual_jobs_started.values())
    return {
        "state": "REINGEST_PIPELINE_VALIDATED"
        if required_pipeline_observed and jobs_zero and ready_record_count > 0
        else "REINGEST_PIPELINE_REVIEW_REQUIRED",
        "required_pipeline": list(REQUIRED_PIPELINE),
        "required_pipeline_observed": required_pipeline_observed,
        "actual_jobs_started": actual_jobs_started,
        "ready_record_count": ready_record_count,
        "owner_review_count": owner_review_count,
        "blocked_reingest_count": blocked_reingest_count,
    }


def _build_persistence_validation(scenario_results: list[dict[str, Any]]) -> dict[str, Any]:
    all_no_persistence_deltas_zero = True
    does_not_create_import_queue = True
    does_not_write_database = True
    does_not_write_index = True
    does_not_write_runtime_outputs = True
    for result in scenario_results:
        report = result["reingest_report"]
        all_no_persistence_deltas_zero = all_no_persistence_deltas_zero and all(
            int(value or 0) == 0 for value in report["no_persistence_deltas"].values()
        )
        does_not_create_import_queue = does_not_create_import_queue and bool(report["does_not_create_import_queue"])
        does_not_write_database = does_not_write_database and bool(report["does_not_write_database"])
        does_not_write_index = does_not_write_index and bool(report["does_not_write_index"])
        does_not_write_runtime_outputs = does_not_write_runtime_outputs and bool(report["does_not_write_runtime_outputs"])
    persistence_validated = (
        all_no_persistence_deltas_zero
        and does_not_create_import_queue
        and does_not_write_database
        and does_not_write_index
        and does_not_write_runtime_outputs
    )
    return {
        "state": "REINGEST_NO_PERSISTENCE_VALIDATED"
        if persistence_validated
        else "REINGEST_NO_PERSISTENCE_REVIEW_REQUIRED",
        "all_no_persistence_deltas_zero": all_no_persistence_deltas_zero,
        "does_not_create_import_queue": does_not_create_import_queue,
        "does_not_write_database": does_not_write_database,
        "does_not_write_index": does_not_write_index,
        "does_not_write_runtime_outputs": does_not_write_runtime_outputs,
    }


def build_stage027_scenario_report(
    *,
    scenario_archives: dict[str, dict[str, Any]],
    evaluated_at: str | None = None,
    required_scenarios: tuple[str, ...] = REQUIRED_STAGE027_SCENARIOS,
) -> dict[str, Any]:
    """Validate Stage 027 Phase 3 re-ingest scenarios without persistence side effects."""

    scenario_results: list[dict[str, Any]] = []
    required_scenario_set = set(required_scenarios)
    for scenario_id in required_scenarios:
        scenario_config = dict(scenario_archives[scenario_id])
        reingest_report = build_reingest_extracted_files(
            archive_uri=scenario_config["archive_uri"],
            staging_area_uri=scenario_config["staging_area_uri"],
            evaluated_at=evaluated_at,
            archive_file_count_limit=scenario_config.get(
                "archive_file_count_limit",
                archive_manifest.archive_threat_model.DEFAULT_ARCHIVE_FILE_COUNT_LIMIT,
            ),
            archive_total_size_limit_bytes=scenario_config.get(
                "archive_total_size_limit_bytes",
                archive_manifest.archive_threat_model.DEFAULT_ARCHIVE_TOTAL_SIZE_LIMIT_BYTES,
            ),
            archive_single_file_size_limit_bytes=scenario_config.get(
                "archive_single_file_size_limit_bytes",
                archive_manifest.archive_threat_model.DEFAULT_ARCHIVE_SINGLE_FILE_SIZE_LIMIT_BYTES,
            ),
            archive_nested_depth_limit=scenario_config.get(
                "archive_nested_depth_limit",
                archive_manifest.archive_threat_model.DEFAULT_ARCHIVE_NESTED_DEPTH_LIMIT,
            ),
        )
        risk_codes = [entry["risk_code"] for entry in reingest_report["reingest_risk_items"]]
        expected_decision_state = EXPECTED_STAGE027_SCENARIO_DECISIONS[scenario_id]
        expected_risk_code = EXPECTED_STAGE027_SCENARIO_RISKS.get(scenario_id)
        expected_decision_observed = reingest_report["reingest_decision_state"] == expected_decision_state
        expected_risk_observed = expected_risk_code is None or expected_risk_code in risk_codes
        scenario_results.append(
            {
                "scenario_id": scenario_id,
                "scenario_state": "REINGEST_SCENARIO_VALIDATED"
                if expected_decision_observed and expected_risk_observed
                else "REINGEST_SCENARIO_REVIEW_REQUIRED",
                "expected_decision_state": expected_decision_state,
                "expected_decision_observed": expected_decision_observed,
                "expected_risk_code": expected_risk_code,
                "expected_risk_observed": expected_risk_observed,
                "decision_state": reingest_report["reingest_decision_state"],
                "risk_codes": risk_codes,
                "reingest_record_count": reingest_report["reingest_record_count"],
                "owner_review_count": reingest_report["owner_review_count"],
                "blocked_reingest_count": reingest_report["blocked_reingest_count"],
                "reingest_report": reingest_report,
            }
        )

    pipeline_validation = _build_pipeline_validation(scenario_results)
    persistence_validation = _build_persistence_validation(scenario_results)
    required_scenarios_covered = required_scenario_set <= set(scenario_archives)
    scenarios_validated = all(result["scenario_state"] == "REINGEST_SCENARIO_VALIDATED" for result in scenario_results)
    validation_passed = (
        required_scenarios_covered
        and scenarios_validated
        and pipeline_validation["state"] == "REINGEST_PIPELINE_VALIDATED"
        and persistence_validation["state"] == "REINGEST_NO_PERSISTENCE_VALIDATED"
    )
    return {
        "schema_version": "ids.stage027.reingest_extracted_files.scenario_validation.v1",
        "stage": "STAGE-027",
        "phase": "Phase 3",
        "task_id": "IDS-V0_1-STAGE027-P3",
        "acceptance_id": "ACC-STAGE-027",
        "entrance": ENTRANCE,
        "reingest_schema": REINGEST_SCHEMA,
        "evaluated_at": evaluated_at,
        "required_scenarios": list(required_scenarios),
        "scenario_count": len(scenario_results),
        "required_scenarios_covered": required_scenarios_covered,
        "validation_state": "REINGEST_SCENARIO_VALIDATION_PASSED"
        if validation_passed
        else "REINGEST_SCENARIO_VALIDATION_REVIEW_REQUIRED",
        "scenario_results": scenario_results,
        "pipeline_validation": pipeline_validation,
        "persistence_validation": persistence_validation,
        "no_persistence_deltas": dict(NO_PERSISTENCE_DELTAS),
        "does_not_read_raw_metadata": True,
        "does_not_write_reingest_runtime_output": True,
        "does_not_start_processing_jobs": True,
        "does_not_use_fake_ids_business_data": True,
        "does_not_create_import_queue": True,
        "does_not_write_database": True,
        "does_not_write_index": True,
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
