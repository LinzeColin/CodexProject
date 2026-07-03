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
ARCHIVE_CLEANUP_SCENARIO_SCHEMA = "ids.stage029.archive_cleanup_allowlist.scenario_validation.v1"
ARCHIVE_CLEANUP_ALLOWLIST_ID_PREFIX = "ids.stage029.cleanup_allowlist"
REQUIRED_PIPELINE = ["hash", "manifest", "dedup", "parser"]
REQUIRED_STAGE029_SCENARIOS = (
    "path_traversal",
    "absolute_path",
    "archive_bomb",
    "nested_archive",
    "garbled_filename",
    "too_many_files",
)
EXPECTED_STAGE029_SCENARIO_RISKS = {
    "path_traversal": "ARCHIVE_ADVERSARIAL_PATH_TRAVERSAL_BLOCKED",
    "absolute_path": "ARCHIVE_ADVERSARIAL_ABSOLUTE_PATH_BLOCKED",
    "archive_bomb": "ARCHIVE_ADVERSARIAL_TOTAL_SIZE_LIMIT_EXCEEDED",
    "nested_archive": "ARCHIVE_ADVERSARIAL_NESTED_DEPTH_LIMIT_EXCEEDED",
    "garbled_filename": "ARCHIVE_ADVERSARIAL_GARBLED_FILENAME_OWNER_REVIEW_REQUIRED",
    "too_many_files": "ARCHIVE_ADVERSARIAL_FILE_COUNT_LIMIT_EXCEEDED",
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


def _flatten_scenario_reingest_queue(scenario_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    queue: list[dict[str, Any]] = []
    for result in scenario_results:
        for item in result["archive_cleanup_report"]["post_extract_reingest"].get("reingest_queue", []):
            queue.append({"scenario_id": result["scenario_id"], **deepcopy(item)})
    return queue


def _flatten_scenario_cleanup_allowlist(scenario_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cleanup_items: list[dict[str, Any]] = []
    for result in scenario_results:
        for item in result["archive_cleanup_report"].get("cleanup_allowlist", []):
            cleanup_items.append({"scenario_id": result["scenario_id"], **deepcopy(item)})
    return cleanup_items


def _build_scenario_reingest_validation(reingest_queue: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "state": "ARCHIVE_CLEANUP_REINGEST_VALIDATED" if reingest_queue else "ARCHIVE_CLEANUP_REINGEST_REVIEW_REQUIRED",
        "required_pipeline": list(REQUIRED_PIPELINE),
        "safe_extracted_file_count": len(reingest_queue),
        "reingest_queue": deepcopy(reingest_queue),
        "actual_jobs_started": dict(ZERO_JOB_STARTS),
        "import_queue_created": False,
    }


def _build_scenario_cleanup_validation(
    *,
    cleanup_allowlist: list[dict[str, Any]],
    scenario_results: list[dict[str, Any]],
) -> dict[str, Any]:
    cleanup_classes = {item.get("cleanup_candidate_class") for item in cleanup_allowlist}
    cleanup_uris = [item.get("cleanup_candidate_uri") for item in cleanup_allowlist]
    original_archive_refs = [result["archive_cleanup_report"]["original_archive_ref"] for result in scenario_results]
    original_archive_in_cleanup = any(ref in cleanup_uris for ref in original_archive_refs)
    temp_only = bool(cleanup_allowlist) and cleanup_classes <= {"ARCHIVE_STAGING_TEMP_FILE"}
    protected_refs_preserved = all(
        result["archive_cleanup_report"]["cleanup_validation"]["protected_refs_preserved"]
        and result["archive_cleanup_report"]["does_not_clean_original_archive"]
        and result["archive_cleanup_report"]["does_not_clean_fact_source_or_evidence"]
        for result in scenario_results
    )
    return {
        "state": (
            "ARCHIVE_CLEANUP_SCENARIO_ALLOWLIST_VALIDATED"
            if temp_only and protected_refs_preserved and not original_archive_in_cleanup
            else "ARCHIVE_CLEANUP_SCENARIO_ALLOWLIST_REVIEW_REQUIRED"
        ),
        "allowed_cleanup_classes": sorted(cleanup_classes),
        "cleanup_allowlist_uris": cleanup_uris,
        "cleanup_targets_are_staging_temp_files_only": temp_only,
        "original_archive_in_cleanup_allowlist": original_archive_in_cleanup,
        "protected_refs_preserved": protected_refs_preserved and not original_archive_in_cleanup,
        "does_not_clean_original_archive": not original_archive_in_cleanup,
        "does_not_clean_fact_source_or_evidence": protected_refs_preserved,
    }


def _build_scenario_manual_review_validation(scenario_results: list[dict[str, Any]]) -> dict[str, Any]:
    owner_review_entry_count = sum(result["archive_cleanup_report"]["owner_review_entry_count"] for result in scenario_results)
    quarantine_entry_count = sum(result["archive_cleanup_report"]["quarantine_entry_count"] for result in scenario_results)
    return {
        "state": (
            "ARCHIVE_CLEANUP_MANUAL_REVIEW_VALIDATED"
            if owner_review_entry_count and quarantine_entry_count
            else "ARCHIVE_CLEANUP_MANUAL_REVIEW_REVIEW_REQUIRED"
        ),
        "owner_review_entry_count": owner_review_entry_count,
        "quarantine_entry_count": quarantine_entry_count,
        "risk_files_to_owner_review": owner_review_entry_count > 0,
        "quarantine_required": quarantine_entry_count > 0,
    }


def _zero_persistence_deltas_for_reports(scenario_results: list[dict[str, Any]]) -> dict[str, int]:
    deltas = dict(NO_PERSISTENCE_DELTAS)
    for result in scenario_results:
        for key, value in result["archive_cleanup_report"].get("no_persistence_deltas", {}).items():
            deltas[key] = deltas.get(key, 0) + int(value or 0)
    return deltas


def build_stage029_scenario_report(
    *,
    scenario_archives: dict[str, dict[str, Any]],
    evaluated_at: str | None = None,
    required_scenarios: tuple[str, ...] = REQUIRED_STAGE029_SCENARIOS,
) -> dict[str, Any]:
    """Validate Stage 029 Phase 3 cleanup allowlist scenarios without persistence."""

    scenario_results: list[dict[str, Any]] = []
    required_scenario_set = set(required_scenarios)
    for scenario_id in required_scenarios:
        scenario_config = dict(scenario_archives[scenario_id])
        cleanup_report = build_archive_cleanup_allowlist(
            archive_uri=scenario_config["archive_uri"],
            staging_area_uri=scenario_config["staging_area_uri"],
            evaluated_at=evaluated_at,
            archive_file_count_limit=scenario_config.get(
                "archive_file_count_limit",
                archive_adversarial.safe_extraction_engine.archive_threat_model.DEFAULT_ARCHIVE_FILE_COUNT_LIMIT,
            ),
            archive_total_size_limit_bytes=scenario_config.get(
                "archive_total_size_limit_bytes",
                archive_adversarial.safe_extraction_engine.archive_threat_model.DEFAULT_ARCHIVE_TOTAL_SIZE_LIMIT_BYTES,
            ),
            archive_single_file_size_limit_bytes=scenario_config.get(
                "archive_single_file_size_limit_bytes",
                archive_adversarial.safe_extraction_engine.archive_threat_model.DEFAULT_ARCHIVE_SINGLE_FILE_SIZE_LIMIT_BYTES,
            ),
            archive_nested_depth_limit=scenario_config.get(
                "archive_nested_depth_limit",
                archive_adversarial.safe_extraction_engine.archive_threat_model.DEFAULT_ARCHIVE_NESTED_DEPTH_LIMIT,
            ),
        )
        risk_codes = [entry["risk_code"] for entry in cleanup_report["risk_entries"]]
        expected_risk_code = EXPECTED_STAGE029_SCENARIO_RISKS.get(scenario_id)
        expected_risk_observed = expected_risk_code is None or expected_risk_code in risk_codes
        scenario_results.append(
            {
                "scenario_id": scenario_id,
                "scenario_state": (
                    "ARCHIVE_CLEANUP_SCENARIO_VALIDATED"
                    if expected_risk_observed
                    else "ARCHIVE_CLEANUP_SCENARIO_REVIEW_REQUIRED"
                ),
                "expected_risk_code": expected_risk_code,
                "expected_risk_observed": expected_risk_observed,
                "risk_codes": risk_codes,
                "cleanup_decision_state": cleanup_report["cleanup_decision_state"],
                "safe_extracted_file_count": cleanup_report["safe_extracted_file_count"],
                "blocked_entry_count": cleanup_report["blocked_entry_count"],
                "quarantine_entry_count": cleanup_report["quarantine_entry_count"],
                "cleanup_candidate_count": cleanup_report["cleanup_candidate_count"],
                "cleanup_runner_executed": cleanup_report["cleanup_runner_executed"],
                "does_not_delete_files": cleanup_report["does_not_delete_files"],
                "archive_cleanup_report": cleanup_report,
            }
        )

    reingest_queue = _flatten_scenario_reingest_queue(scenario_results)
    cleanup_allowlist = _flatten_scenario_cleanup_allowlist(scenario_results)
    reingest_validation = _build_scenario_reingest_validation(reingest_queue)
    cleanup_validation = _build_scenario_cleanup_validation(
        cleanup_allowlist=cleanup_allowlist,
        scenario_results=scenario_results,
    )
    manual_review_validation = _build_scenario_manual_review_validation(scenario_results)
    required_scenarios_covered = required_scenario_set <= set(scenario_archives)
    scenarios_validated = all(
        result["scenario_state"] == "ARCHIVE_CLEANUP_SCENARIO_VALIDATED" for result in scenario_results
    )
    validation_passed = (
        required_scenarios_covered
        and scenarios_validated
        and reingest_validation["state"] == "ARCHIVE_CLEANUP_REINGEST_VALIDATED"
        and cleanup_validation["state"] == "ARCHIVE_CLEANUP_SCENARIO_ALLOWLIST_VALIDATED"
        and manual_review_validation["state"] == "ARCHIVE_CLEANUP_MANUAL_REVIEW_VALIDATED"
    )
    no_persistence_deltas = _zero_persistence_deltas_for_reports(scenario_results)
    return {
        "schema_version": ARCHIVE_CLEANUP_SCENARIO_SCHEMA,
        "source_schema_version": ARCHIVE_CLEANUP_SCHEMA,
        "stage": "STAGE-029",
        "phase": "Phase 3",
        "task_id": "IDS-V0_1-STAGE029-P3",
        "acceptance_id": "ACC-STAGE-029",
        "entrance": ENTRANCE,
        "evaluated_at": evaluated_at,
        "required_scenarios": list(required_scenarios),
        "scenario_count": len(scenario_results),
        "required_scenarios_covered": required_scenarios_covered,
        "validation_state": (
            "ARCHIVE_CLEANUP_SCENARIO_VALIDATION_PASSED"
            if validation_passed
            else "ARCHIVE_CLEANUP_SCENARIO_VALIDATION_REVIEW_REQUIRED"
        ),
        "scenario_results": scenario_results,
        "reingest_validation": reingest_validation,
        "cleanup_validation": cleanup_validation,
        "manual_review_validation": manual_review_validation,
        "processing_guard": dict(ZERO_JOB_STARTS),
        "no_persistence_deltas": no_persistence_deltas,
        "cleanup_runner_executed": False,
        "does_not_delete_files": True,
        "does_not_clean_original_archive": cleanup_validation["does_not_clean_original_archive"],
        "does_not_clean_fact_source_or_evidence": cleanup_validation["does_not_clean_fact_source_or_evidence"],
        "does_not_write_archive_cleanup_runtime_output": True,
        "does_not_write_archive_manifest_runtime_output": True,
        "does_not_read_raw_metadata": True,
        "does_not_use_fake_ids_business_data": True,
        "does_not_start_processing_jobs": True,
        "does_not_create_import_queue": True,
        "does_not_write_database": True,
        "does_not_write_reports": True,
        "does_not_write_evidence_ledger": True,
        "does_not_write_audit_log": True,
        "does_not_write_index": True,
        "does_not_write_document_chunk_job_import_rows": True,
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
