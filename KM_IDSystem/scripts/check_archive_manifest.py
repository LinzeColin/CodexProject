#!/usr/bin/env python3
"""Stage 026 archive manifest wrapper for IDS."""

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

import check_archive_threat_model as archive_threat_model
import check_safe_extraction_engine as safe_extraction_engine


ENTRANCE = "IDS 系统运营入口"
ARCHIVE_MANIFEST_SCHEMA = "ids.stage026.archive_manifest.v1"
ARCHIVE_MANIFEST_PREFIX = "ids.stage026.archive_manifest"

DECISION_STATE_MAP = {
    "SAFE_EXTRACTION_BLOCKED": "ARCHIVE_MANIFEST_BLOCKED",
    "SAFE_EXTRACTION_OWNER_REVIEW_REQUIRED": "ARCHIVE_MANIFEST_OWNER_REVIEW_REQUIRED",
    "SAFE_EXTRACTION_READY_FOR_STAGING": "ARCHIVE_MANIFEST_READY_FOR_STAGING",
    "SAFE_EXTRACTION_READY_FOR_REINGEST": "ARCHIVE_MANIFEST_READY_FOR_REINGEST",
}


def _uri_to_path(uri: str) -> Path:
    return archive_threat_model._uri_to_path(uri)


def _is_under_raw_metadata(path: Path) -> bool:
    return archive_threat_model._is_under_raw_metadata(path)


def _archive_type(path: Path) -> str:
    return archive_threat_model._archive_type(path)


def _map_archive_risk_code(risk_code: str | None) -> str | None:
    if risk_code is None:
        return None
    if risk_code.startswith("SAFE_EXTRACTION_"):
        return risk_code.replace("SAFE_EXTRACTION_", "ARCHIVE_MANIFEST_", 1)
    if risk_code.startswith("ARCHIVE_"):
        return f"ARCHIVE_MANIFEST_{risk_code.removeprefix('ARCHIVE_')}"
    return f"ARCHIVE_MANIFEST_{risk_code}"


def _map_archive_state(state: str | None) -> str | None:
    if state is None:
        return None
    if state.startswith("SAFE_EXTRACTION_"):
        return state.replace("SAFE_EXTRACTION_", "ARCHIVE_MANIFEST_", 1)
    if state.startswith("ARCHIVE_"):
        return f"ARCHIVE_MANIFEST_{state.removeprefix('ARCHIVE_')}"
    return f"ARCHIVE_MANIFEST_{state}"


def _hash_archive_if_allowed(*, archive_path: Path, staging_path: Path) -> str | None:
    if _is_under_raw_metadata(archive_path) or _is_under_raw_metadata(staging_path):
        return None
    if not archive_path.is_file():
        return None
    digest = hashlib.sha256()
    with archive_path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _archive_manifest_id(archive_hash_sha256: str | None, archive_uri: str) -> str:
    if archive_hash_sha256:
        return f"{ARCHIVE_MANIFEST_PREFIX}.{archive_hash_sha256[:16]}"
    uri_digest = hashlib.sha256(archive_uri.encode("utf-8")).hexdigest()
    return f"{ARCHIVE_MANIFEST_PREFIX}.unavailable.{uri_digest[:12]}"


def _nested_archive_depth(entry_path: str | None) -> int:
    if not entry_path:
        return 0
    parts = entry_path.lower().split("/")
    return sum(1 for part in parts if any(part.endswith(suffix) for suffix in archive_threat_model.ARCHIVE_SUFFIXES))


def _risk_by_path(risk_entries: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    mapped: dict[str, dict[str, Any]] = {}
    for entry in risk_entries:
        path = entry.get("entry_path")
        if isinstance(path, str):
            mapped[path] = entry
    return mapped


def _manifest_entry(source_entry: dict[str, Any], risk_lookup: dict[str, dict[str, Any]]) -> dict[str, Any]:
    entry = deepcopy(source_entry)
    entry_path = entry.get("entry_path")
    source_risk = risk_lookup.get(entry_path) if isinstance(entry_path, str) else None
    if "risk_code" not in entry and source_risk:
        entry["risk_code"] = source_risk.get("risk_code")
    if "entry_state" not in entry and source_risk:
        entry["entry_state"] = source_risk.get("entry_state")
    entry["source_entry_state"] = entry.get("entry_state")
    entry["manifest_entry_state"] = _map_archive_state(entry.get("entry_state"))
    entry["source_risk_code"] = entry.get("risk_code")
    entry["risk_code"] = _map_archive_risk_code(entry.get("risk_code"))
    entry["nested_archive_depth"] = _nested_archive_depth(entry.get("normalized_entry_path") or entry_path)
    return entry


def _risk_item(source_entry: dict[str, Any]) -> dict[str, Any]:
    item = deepcopy(source_entry)
    item["source_entry_state"] = item.get("entry_state")
    item["source_risk_code"] = item.get("risk_code")
    item["risk_code"] = _map_archive_risk_code(item.get("risk_code"))
    item["manifest_entry_state"] = "ARCHIVE_MANIFEST_ENTRY_QUARANTINE_REQUIRED"
    item["manual_review_state"] = "ARCHIVE_MANIFEST_OWNER_REVIEW_REQUIRED"
    item["quarantine_state"] = "ARCHIVE_MANIFEST_ENTRY_QUARANTINE_REQUIRED"
    item["nested_archive_depth"] = _nested_archive_depth(item.get("normalized_entry_path") or item.get("entry_path"))
    return item


def _post_extract_reingest(source_reingest: dict[str, Any]) -> dict[str, Any]:
    reingest = deepcopy(source_reingest)
    if reingest.get("reingest_queue"):
        reingest["state"] = "POST_EXTRACT_REINGEST_REQUIRED"
    reingest.setdefault("required_pipeline", ["hash", "manifest", "dedup", "parser"])
    for item in reingest.get("reingest_queue", []):
        item["archive_manifest_schema"] = ARCHIVE_MANIFEST_SCHEMA
        item["archive_manifest_reentry_state"] = "POST_EXTRACT_REINGEST_REQUIRED"
    return reingest


def build_archive_manifest(
    *,
    archive_uri: str,
    staging_area_uri: str,
    manifested_at: str | None = None,
    archive_file_count_limit: int = archive_threat_model.DEFAULT_ARCHIVE_FILE_COUNT_LIMIT,
    archive_total_size_limit_bytes: int = archive_threat_model.DEFAULT_ARCHIVE_TOTAL_SIZE_LIMIT_BYTES,
    archive_single_file_size_limit_bytes: int = archive_threat_model.DEFAULT_ARCHIVE_SINGLE_FILE_SIZE_LIMIT_BYTES,
    archive_nested_depth_limit: int = archive_threat_model.DEFAULT_ARCHIVE_NESTED_DEPTH_LIMIT,
) -> dict[str, Any]:
    """Build a Stage 026 in-memory archive manifest from safe extraction results."""

    manifested_at = manifested_at or archive_threat_model._utc_now()
    archive_path = _uri_to_path(archive_uri)
    staging_path = _uri_to_path(staging_area_uri)
    safe_report = safe_extraction_engine.run_safe_extraction_engine(
        archive_uri=archive_uri,
        staging_area_uri=staging_area_uri,
        extracted_at=manifested_at,
        archive_file_count_limit=archive_file_count_limit,
        archive_total_size_limit_bytes=archive_total_size_limit_bytes,
        archive_single_file_size_limit_bytes=archive_single_file_size_limit_bytes,
        archive_nested_depth_limit=archive_nested_depth_limit,
    )
    archive_hash_sha256 = _hash_archive_if_allowed(
        archive_path=archive_path,
        staging_path=staging_path,
    )
    risk_entries = [_risk_item(entry) for entry in safe_report.get("risk_entries", [])]
    risk_lookup = _risk_by_path(safe_report.get("risk_entries", []))
    archive_entry_manifest = [
        _manifest_entry(entry, risk_lookup)
        for entry in safe_report.get("archive_manifest", {}).get("entries", [])
    ]
    safe_entries = safe_report.get("safe_extracted_entries", [])
    extracted_size_bytes = sum(int(entry.get("size_bytes", 0) or 0) for entry in safe_entries)
    max_nested_depth = 0
    for entry in archive_entry_manifest + risk_entries:
        max_nested_depth = max(max_nested_depth, int(entry.get("nested_archive_depth", 0) or 0))
    source_decision = safe_report.get("safe_extraction_decision_state", "SAFE_EXTRACTION_BLOCKED")

    return {
        "schema_version": ARCHIVE_MANIFEST_SCHEMA,
        "source_schema_version": safe_report.get("schema_version"),
        "stage": "STAGE-026",
        "phase": "Phase 2",
        "task_id": "IDS-V0_1-STAGE026-P2",
        "acceptance_id": "ACC-STAGE-026",
        "entrance": ENTRANCE,
        "archive_manifest_schema": ARCHIVE_MANIFEST_SCHEMA,
        "archive_manifest_id": _archive_manifest_id(archive_hash_sha256, archive_uri),
        "manifested_at": manifested_at,
        "archive_source_uri": archive_uri,
        "original_archive_ref": safe_report.get("original_archive_ref", archive_uri),
        "archive_staging_area_uri": staging_area_uri,
        "archive_type": safe_report.get("archive_type") or _archive_type(archive_path),
        "archive_hash_sha256": archive_hash_sha256,
        "limits": dict(safe_report.get("limits", {})),
        "archive_manifest_decision_state": DECISION_STATE_MAP.get(source_decision, "ARCHIVE_MANIFEST_BLOCKED"),
        "source_safe_extraction_decision_state": source_decision,
        "archive_entry_manifest": archive_entry_manifest,
        "archive_entry_count": len(archive_entry_manifest),
        "safe_extracted_entries": deepcopy(safe_entries),
        "safe_extracted_file_count": int(safe_report.get("safe_extracted_file_count", 0) or 0),
        "safe_extracted_total_size_bytes": extracted_size_bytes,
        "max_nested_archive_depth_observed": max_nested_depth,
        "archive_failed_items": deepcopy(risk_entries),
        "archive_risk_items": risk_entries,
        "archive_blocked_entry_count": int(safe_report.get("blocked_entry_count", len(risk_entries)) or 0),
        "archive_quarantine_entry_count": int(safe_report.get("quarantine_entry_count", len(risk_entries)) or 0),
        "post_extract_reingest": _post_extract_reingest(safe_report.get("post_extract_reingest", {})),
        "cleanup_allowlist": deepcopy(safe_report.get("cleanup_allowlist", [])),
        "cleanup_policy": dict(safe_report.get("cleanup_policy", {})),
        "manual_review_routing": {
            "failure_state": "ARCHIVE_MANIFEST_BLOCKED",
            "owner_review_state": "ARCHIVE_MANIFEST_OWNER_REVIEW_REQUIRED",
            "quarantine_state": "ARCHIVE_MANIFEST_ENTRY_QUARANTINE_REQUIRED",
            "over_limit_state": "ARCHIVE_MANIFEST_ENTRY_QUARANTINE_REQUIRED",
        },
        "processing_guard": dict(safe_report.get("processing_guard", archive_threat_model.PROCESSING_GUARD_ZEROES)),
        "no_persistence_deltas": dict(safe_report.get("no_persistence_deltas", archive_threat_model.NO_PERSISTENCE_DELTAS)),
        "original_archive_preserved": bool(safe_report.get("original_archive_preserved", True)),
        "does_not_overwrite_original_archive": bool(safe_report.get("does_not_overwrite_original_archive", True)),
        "does_not_write_outside_staging": bool(safe_report.get("does_not_write_outside_staging", True)),
        "does_not_read_raw_metadata": True,
        "does_not_write_archive_manifest_runtime_output": True,
        "does_not_fake_rar_7z_support": bool(safe_report.get("does_not_fake_rar_7z_support", True)),
        "does_not_start_processing_jobs": True,
        "does_not_write_runtime_outputs": True,
        "does_not_use_fake_ids_business_data": True,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build an in-memory IDS Stage 026 archive manifest.")
    parser.add_argument("--archive-uri", required=True, help="Owner-approved file:// archive URI.")
    parser.add_argument("--staging-area-uri", required=True, help="Owner-approved file:// staging root URI.")
    parser.add_argument("--manifested-at", default=None, help="Optional UTC timestamp for deterministic evidence.")
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
    manifest = build_archive_manifest(
        archive_uri=args.archive_uri,
        staging_area_uri=args.staging_area_uri,
        manifested_at=args.manifested_at,
        archive_file_count_limit=args.archive_file_count_limit,
        archive_total_size_limit_bytes=args.archive_total_size_limit_bytes,
        archive_single_file_size_limit_bytes=args.archive_single_file_size_limit_bytes,
        archive_nested_depth_limit=args.archive_nested_depth_limit,
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
