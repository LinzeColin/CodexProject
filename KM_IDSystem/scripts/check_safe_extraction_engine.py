#!/usr/bin/env python3
"""Stage 025 safe extraction engine wrapper for IDS."""

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

import check_archive_threat_model as archive_threat_model


ENTRANCE = "IDS 系统运营入口"
SAFE_EXTRACTION_ENGINE_ID = "ids.stage025.safe_extraction_engine"

RISK_CODE_MAP = {
    "ARCHIVE_PATH_TRAVERSAL_BLOCKED": "SAFE_EXTRACTION_PATH_TRAVERSAL_BLOCKED",
    "ARCHIVE_ABSOLUTE_PATH_BLOCKED": "SAFE_EXTRACTION_ABSOLUTE_PATH_BLOCKED",
    "ARCHIVE_STAGING_ESCAPE_BLOCKED": "SAFE_EXTRACTION_STAGING_ESCAPE_BLOCKED",
    "ARCHIVE_FILE_COUNT_LIMIT_EXCEEDED": "SAFE_EXTRACTION_FILE_COUNT_LIMIT_EXCEEDED",
    "ARCHIVE_ENTRY_SIZE_LIMIT_EXCEEDED": "SAFE_EXTRACTION_ENTRY_SIZE_LIMIT_EXCEEDED",
    "ARCHIVE_TOTAL_SIZE_LIMIT_EXCEEDED": "SAFE_EXTRACTION_TOTAL_SIZE_LIMIT_EXCEEDED",
    "ARCHIVE_NESTED_DEPTH_LIMIT_EXCEEDED": "SAFE_EXTRACTION_NESTED_DEPTH_LIMIT_EXCEEDED",
    "ARCHIVE_GARBLED_FILENAME_OWNER_REVIEW_REQUIRED": "SAFE_EXTRACTION_GARBLED_FILENAME_OWNER_REVIEW_REQUIRED",
    "ARCHIVE_STAGING_TARGET_EXISTS": "SAFE_EXTRACTION_STAGING_OVERWRITE_BLOCKED",
    "ARCHIVE_FORMAT_REQUIRES_EXTERNAL_ADAPTER": "SAFE_EXTRACTION_ADAPTER_OWNER_REVIEW_REQUIRED",
    "ARCHIVE_FORMAT_UNSUPPORTED": "SAFE_EXTRACTION_FORMAT_UNSUPPORTED",
    "ARCHIVE_SOURCE_MISSING": "SAFE_EXTRACTION_SOURCE_MISSING",
    "ARCHIVE_SOURCE_BLOCKED_RAW_METADATA_ROOT": "SAFE_EXTRACTION_SOURCE_BLOCKED_RAW_METADATA_ROOT",
    "ARCHIVE_NON_FILE_ENTRY_BLOCKED": "SAFE_EXTRACTION_NON_FILE_ENTRY_BLOCKED",
    "ARCHIVE_EMPTY_PATH_BLOCKED": "SAFE_EXTRACTION_EMPTY_PATH_BLOCKED",
    "ARCHIVE_ENTRY_SAFE": "SAFE_EXTRACTION_ENTRY_SAFE",
}

STATE_MAP = {
    "ARCHIVE_EXTRACTION_DRAFT": "SAFE_EXTRACTION_DRAFT",
    "ARCHIVE_EXTRACTION_BLOCKED": "SAFE_EXTRACTION_BLOCKED",
    "ARCHIVE_EXTRACTION_OWNER_REVIEW_REQUIRED": "SAFE_EXTRACTION_OWNER_REVIEW_REQUIRED",
    "ARCHIVE_EXTRACTION_READY_FOR_SAFE_STAGING": "SAFE_EXTRACTION_READY_FOR_STAGING",
    "ARCHIVE_EXTRACTION_READY_FOR_REINGEST": "SAFE_EXTRACTION_READY_FOR_REINGEST",
}


def _map_risk_code(risk_code: str | None) -> str | None:
    if risk_code is None:
        return None
    return RISK_CODE_MAP.get(risk_code, f"SAFE_EXTRACTION_{risk_code.removeprefix('ARCHIVE_')}")


def _map_entry(entry: dict[str, Any]) -> dict[str, Any]:
    mapped = dict(entry)
    if "risk_code" in mapped:
        mapped["source_risk_code"] = mapped["risk_code"]
        mapped["risk_code"] = _map_risk_code(mapped["risk_code"])
    if "entry_state" in mapped and isinstance(mapped["entry_state"], str):
        mapped["source_entry_state"] = mapped["entry_state"]
        mapped["entry_state"] = mapped["entry_state"].replace("ARCHIVE_", "SAFE_EXTRACTION_")
    return mapped


def _map_archive_manifest(source_manifest: dict[str, Any]) -> dict[str, Any]:
    manifest = deepcopy(source_manifest)
    manifest["schema_version"] = "ids.stage025.archive_manifest.v1"
    manifest["source_schema_version"] = source_manifest.get("schema_version")
    manifest["safe_extraction_engine_id"] = SAFE_EXTRACTION_ENGINE_ID
    manifest["entries"] = [_map_entry(entry) for entry in source_manifest.get("entries", [])]
    return manifest


def _map_reingest_queue(queue: list[dict[str, Any]]) -> list[dict[str, Any]]:
    mapped_queue = []
    for item in queue:
        mapped = dict(item)
        mapped["safe_extraction_engine_id"] = SAFE_EXTRACTION_ENGINE_ID
        mapped["reingest_policy"] = "post_extract_hash_manifest_dedup_parser_required"
        mapped_queue.append(mapped)
    return mapped_queue


def run_safe_extraction_engine(
    *,
    archive_uri: str,
    staging_area_uri: str,
    extracted_at: str | None = None,
    archive_file_count_limit: int = archive_threat_model.DEFAULT_ARCHIVE_FILE_COUNT_LIMIT,
    archive_total_size_limit_bytes: int = archive_threat_model.DEFAULT_ARCHIVE_TOTAL_SIZE_LIMIT_BYTES,
    archive_single_file_size_limit_bytes: int = archive_threat_model.DEFAULT_ARCHIVE_SINGLE_FILE_SIZE_LIMIT_BYTES,
    archive_nested_depth_limit: int = archive_threat_model.DEFAULT_ARCHIVE_NESTED_DEPTH_LIMIT,
) -> dict[str, Any]:
    """Run the Stage 025 safe extraction engine using the Stage 024 threat boundary."""

    threat_report = archive_threat_model.safe_extract_archive(
        archive_uri=archive_uri,
        staging_area_uri=staging_area_uri,
        extracted_at=extracted_at,
        archive_file_count_limit=archive_file_count_limit,
        archive_total_size_limit_bytes=archive_total_size_limit_bytes,
        archive_single_file_size_limit_bytes=archive_single_file_size_limit_bytes,
        archive_nested_depth_limit=archive_nested_depth_limit,
    )
    risk_entries = [_map_entry(entry) for entry in threat_report.get("risk_entries", [])]
    owner_review_entries = [_map_entry(entry) for entry in threat_report.get("owner_review_entries", [])]
    quarantine_entries = [_map_entry(entry) for entry in threat_report.get("quarantine_entries", [])]
    safe_extracted_entries = [_map_entry(entry) for entry in threat_report.get("safe_extracted_entries", [])]
    reingest = dict(threat_report.get("post_extract_reingest", {}))
    reingest["reingest_queue"] = _map_reingest_queue(reingest.get("reingest_queue", []))
    source_state = threat_report.get("extraction_state", "ARCHIVE_EXTRACTION_BLOCKED")

    return {
        "schema_version": "ids.stage025.safe_extraction_engine.v1",
        "source_schema_version": threat_report.get("schema_version"),
        "stage": "STAGE-025",
        "phase": "Phase 2",
        "task_id": "IDS-V0_1-STAGE025-P2",
        "acceptance_id": "ACC-STAGE-025",
        "entrance": ENTRANCE,
        "safe_extraction_engine_id": SAFE_EXTRACTION_ENGINE_ID,
        "extracted_at": threat_report.get("extracted_at"),
        "archive_type": threat_report.get("archive_type"),
        "archive_source_uri": threat_report.get("archive_source_uri"),
        "original_archive_ref": threat_report.get("original_archive_ref"),
        "archive_staging_area_uri": threat_report.get("archive_staging_area_uri"),
        "limits": dict(threat_report.get("limits", {})),
        "safe_extraction_decision_state": STATE_MAP.get(source_state, "SAFE_EXTRACTION_BLOCKED"),
        "source_extraction_state": source_state,
        "archive_manifest": _map_archive_manifest(threat_report.get("archive_manifest", {})),
        "safe_extracted_entries": safe_extracted_entries,
        "safe_extracted_file_count": threat_report.get("safe_extracted_file_count", 0),
        "risk_entries": risk_entries,
        "owner_review_entries": owner_review_entries,
        "quarantine_entries": quarantine_entries,
        "blocked_entry_count": len(risk_entries),
        "quarantine_entry_count": len(quarantine_entries),
        "post_extract_reingest": reingest,
        "cleanup_allowlist": list(threat_report.get("cleanup_allowlist", [])),
        "cleanup_policy": dict(threat_report.get("cleanup_policy", {})),
        "processing_guard": dict(threat_report.get("processing_guard", {})),
        "no_persistence_deltas": dict(threat_report.get("no_persistence_deltas", {})),
        "original_archive_preserved": threat_report.get("original_archive_preserved", True),
        "does_not_overwrite_original_archive": threat_report.get("does_not_overwrite_original_archive", True),
        "does_not_write_outside_staging": threat_report.get("does_not_write_outside_staging", True),
        "does_not_read_raw_metadata": threat_report.get("does_not_read_raw_metadata", True),
        "does_not_write_archive_manifest_runtime_output": threat_report.get(
            "does_not_write_archive_manifest_runtime_output",
            True,
        ),
        "does_not_fake_rar_7z_support": threat_report.get("does_not_fake_rar_7z_support", True),
        "does_not_start_processing_jobs": True,
        "does_not_write_runtime_outputs": True,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the IDS Stage 025 safe extraction engine.")
    parser.add_argument("--archive-uri", required=True, help="Owner-approved file:// archive URI.")
    parser.add_argument("--staging-area-uri", required=True, help="Owner-approved file:// staging root URI.")
    parser.add_argument("--extracted-at", default=None, help="Optional UTC timestamp for deterministic evidence.")
    parser.add_argument("--archive-file-count-limit", type=int, default=archive_threat_model.DEFAULT_ARCHIVE_FILE_COUNT_LIMIT)
    parser.add_argument(
        "--archive-total-size-limit-bytes",
        type=int,
        default=archive_threat_model.DEFAULT_ARCHIVE_TOTAL_SIZE_LIMIT_BYTES,
    )
    parser.add_argument(
        "--archive-single-file-size-limit-bytes",
        type=int,
        default=archive_threat_model.DEFAULT_ARCHIVE_SINGLE_FILE_SIZE_LIMIT_BYTES,
    )
    parser.add_argument("--archive-nested-depth-limit", type=int, default=archive_threat_model.DEFAULT_ARCHIVE_NESTED_DEPTH_LIMIT)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    report = run_safe_extraction_engine(
        archive_uri=args.archive_uri,
        staging_area_uri=args.staging_area_uri,
        extracted_at=args.extracted_at,
        archive_file_count_limit=args.archive_file_count_limit,
        archive_total_size_limit_bytes=args.archive_total_size_limit_bytes,
        archive_single_file_size_limit_bytes=args.archive_single_file_size_limit_bytes,
        archive_nested_depth_limit=args.archive_nested_depth_limit,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
