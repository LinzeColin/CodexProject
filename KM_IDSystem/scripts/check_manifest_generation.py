#!/usr/bin/env python3
"""Metadata-only Stage 014 manifest generation preflight for IDS operations."""

from __future__ import annotations

import argparse
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


OPERATIONS_ENTRANCE = "IDS 系统运营入口"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _load_stage013_module() -> Any:
    path = Path(__file__).with_name("check_file_fingerprint.py")
    spec = importlib.util.spec_from_file_location("stage013_file_fingerprint", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load Stage 013 fingerprint module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _manifest_state(fingerprint_state: str) -> str:
    return {
        "FINGERPRINT_READY": "MANIFEST_READY",
        "FINGERPRINT_NOT_CONFIGURED": "MANIFEST_NOT_CONFIGURED",
        "FINGERPRINT_PATH_BLOCKED": "MANIFEST_SOURCE_BLOCKED",
        "FINGERPRINT_READ_BLOCKED": "MANIFEST_SOURCE_BLOCKED",
        "FINGERPRINT_HASH_CONFLICT": "MANIFEST_HASH_CONFLICT",
        "FINGERPRINT_DUPLICATE_CONTENT": "MANIFEST_DUPLICATE_CONTENT",
        "FINGERPRINT_MANIFEST_UNSAFE": "MANIFEST_SCHEMA_UNSAFE",
    }.get(fingerprint_state, "MANIFEST_UNKNOWN")


def _candidate_from_fingerprint(
    record: dict[str, Any],
    *,
    manifest_generated_at: str,
) -> dict[str, Any]:
    sha256 = record["sha256"]
    return {
        "manifest_state": "MANIFEST_READY",
        "manifest_id": f"ids-manifest-sha256-{sha256}",
        "source_uri": record["source_uri"],
        "source_path": record["source_path"],
        "sha256": sha256,
        "file_size": record["file_size"],
        "mtime": record["mtime"],
        "first_seen_at": record["first_seen_at"],
        "manifest_generated_at": manifest_generated_at,
    }


def _rejection_from_fingerprint(record: dict[str, Any]) -> dict[str, Any]:
    rejected: dict[str, Any] = {
        "manifest_state": _manifest_state(record["state"]),
        "source_uri": record.get("source_uri"),
        "fingerprint_state": record["state"],
    }
    if "source_path" in record:
        rejected["source_path"] = record["source_path"]
    if "reason" in record:
        rejected["reason"] = record["reason"]
    return rejected


def _overall_state(candidates: list[dict[str, Any]], rejected_inputs: list[dict[str, Any]]) -> str:
    if rejected_inputs:
        return rejected_inputs[0]["manifest_state"]
    if candidates:
        return "MANIFEST_READY"
    return "MANIFEST_NOT_CONFIGURED"


def evaluate_manifest_candidates(
    *,
    source_uris: list[str | None] | tuple[str | None, ...] | None,
    first_seen_at: str | None = None,
    manifest_generated_at: str | None = None,
) -> dict[str, Any]:
    """Build metadata-only manifest candidates without persistence side effects."""

    manifest_generated_at = manifest_generated_at or _utc_now()
    stage013 = _load_stage013_module()
    fingerprint_report = stage013.evaluate_file_fingerprints(
        source_uris=source_uris,
        first_seen_at=first_seen_at,
    )

    candidates: list[dict[str, Any]] = []
    rejected_inputs: list[dict[str, Any]] = []
    seen_manifest_ids: set[str] = set()
    duplicate_manifest_count = 0

    for record in fingerprint_report["records"]:
        if record["state"] == "FINGERPRINT_READY":
            candidate = _candidate_from_fingerprint(
                record,
                manifest_generated_at=manifest_generated_at,
            )
            if candidate["manifest_id"] in seen_manifest_ids:
                duplicate_manifest_count += 1
                continue
            seen_manifest_ids.add(candidate["manifest_id"])
            candidates.append(candidate)
        else:
            rejected_inputs.append(_rejection_from_fingerprint(record))

    duplicate_input_count = fingerprint_report["duplicate_input_count"] + duplicate_manifest_count
    overall_state = _overall_state(candidates, rejected_inputs)

    return {
        "schema_version": "ids.stage014.manifest_generation.v1",
        "stage": "STAGE-014",
        "phase": "Phase 2",
        "acceptance_id": "ACC-STAGE-014",
        "entrance": OPERATIONS_ENTRANCE,
        "customer_visible": False,
        "overall_state": overall_state,
        "safe_mode": overall_state != "MANIFEST_READY",
        "manifest_candidates": candidates,
        "rejected_inputs": rejected_inputs,
        "candidate_count": len(candidates),
        "manifest_record_count": len(candidates),
        "rejected_input_count": len(rejected_inputs),
        "duplicate_input_count": duplicate_input_count,
        "error_count": len(rejected_inputs),
        "document_delta": 0,
        "chunk_delta": 0,
        "job_delta": 0,
        "manifest_write_delta": 0,
        "fingerprint_overall_state": fingerprint_report["overall_state"],
        "does_not_scan_recursively": True,
        "does_not_move_originals": True,
        "does_not_delete_originals": True,
        "does_not_overwrite_originals": True,
        "does_not_write_manifest_files": True,
        "does_not_write_database": True,
        "does_not_create_documents_chunks_jobs": True,
        "does_not_read_raw_metadata": True,
        "does_not_call_external_apis": True,
    }


def _ready_candidates(report: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        candidate
        for candidate in report["manifest_candidates"]
        if candidate["manifest_state"] == "MANIFEST_READY"
    ]


def _same_name_different_hash(
    left_uri: str,
    right_uri: str,
    *,
    first_seen_at: str,
    manifest_generated_at: str,
) -> dict[str, Any]:
    report = evaluate_manifest_candidates(
        source_uris=[left_uri, right_uri],
        first_seen_at=first_seen_at,
        manifest_generated_at=manifest_generated_at,
    )
    candidates = _ready_candidates(report)
    conflict = (
        len(candidates) == 2
        and Path(candidates[0]["source_path"]).name == Path(candidates[1]["source_path"]).name
        and candidates[0]["sha256"] != candidates[1]["sha256"]
    )
    return {
        "scenario_id": "same_name_different_hash",
        "state": "MANIFEST_HASH_CONFLICT" if conflict else report["overall_state"],
        "valid": conflict,
        "conflict_count": 1 if conflict else 0,
        "candidate_count": report["candidate_count"],
        "manifest_write_delta": report["manifest_write_delta"],
    }


def _same_hash_different_path(
    left_uri: str,
    right_uri: str,
    *,
    first_seen_at: str,
) -> dict[str, Any]:
    stage013 = _load_stage013_module()
    fingerprint_report = stage013.evaluate_file_fingerprints(
        source_uris=[left_uri, right_uri],
        first_seen_at=first_seen_at,
    )
    records = [
        record
        for record in fingerprint_report["records"]
        if record["state"] == "FINGERPRINT_READY"
    ]
    duplicate = (
        len(records) == 2
        and records[0]["source_path"] != records[1]["source_path"]
        and records[0]["sha256"] == records[1]["sha256"]
    )
    return {
        "scenario_id": "same_hash_different_path",
        "state": "MANIFEST_DUPLICATE_CONTENT" if duplicate else _manifest_state(fingerprint_report["overall_state"]),
        "valid": duplicate,
        "duplicate_content_count": 1 if duplicate else 0,
        "fingerprint_record_count": fingerprint_report["record_count"],
        "manifest_write_delta": 0,
    }


def build_stage014_scenario_report(
    *,
    same_file_uri: str,
    same_name_left_uri: str,
    same_name_right_uri: str,
    same_hash_left_uri: str,
    same_hash_right_uri: str,
    first_seen_at: str | None = None,
    manifest_generated_at: str | None = None,
) -> dict[str, Any]:
    """Validate Phase 3 manifest scenarios without persistence side effects."""

    first_seen_at = first_seen_at or _utc_now()
    manifest_generated_at = manifest_generated_at or _utc_now()
    stage013 = _load_stage013_module()
    source_path = stage013._path_from_uri(same_file_uri)
    before_sha256 = stage013._hash_file(source_path)
    before_size = source_path.stat().st_size

    same_file = evaluate_manifest_candidates(
        source_uris=[same_file_uri, same_file_uri],
        first_seen_at=first_seen_at,
        manifest_generated_at=manifest_generated_at,
    )
    same_file_scenario = {
        "scenario_id": "same_file_same_hash",
        "state": same_file["overall_state"],
        "valid": (
            same_file["overall_state"] == "MANIFEST_READY"
            and same_file["duplicate_input_count"] == 1
            and same_file["candidate_count"] == 1
        ),
        "duplicate_input_count": same_file["duplicate_input_count"],
        "candidate_count": same_file["candidate_count"],
        "manifest_write_delta": same_file["manifest_write_delta"],
    }

    same_name = _same_name_different_hash(
        same_name_left_uri,
        same_name_right_uri,
        first_seen_at=first_seen_at,
        manifest_generated_at=manifest_generated_at,
    )
    same_hash = _same_hash_different_path(
        same_hash_left_uri,
        same_hash_right_uri,
        first_seen_at=first_seen_at,
    )
    duplicate_import = {
        "scenario_id": "duplicate_import_no_persistence",
        "state": same_file["overall_state"],
        "valid": (
            same_file_scenario["valid"]
            and same_file["document_delta"] == 0
            and same_file["chunk_delta"] == 0
            and same_file["job_delta"] == 0
            and same_file["manifest_write_delta"] == 0
        ),
        "document_delta": same_file["document_delta"],
        "chunk_delta": same_file["chunk_delta"],
        "job_delta": same_file["job_delta"],
        "manifest_write_delta": same_file["manifest_write_delta"],
        "candidate_count": same_file["candidate_count"],
        "duplicate_input_count": same_file["duplicate_input_count"],
    }

    after_sha256 = stage013._hash_file(source_path)
    after_size = source_path.stat().st_size
    hash_stable = {
        "scenario_id": "original_hash_stable",
        "state": "MANIFEST_READY" if before_sha256 == after_sha256 else "MANIFEST_UNKNOWN",
        "valid": before_sha256 == after_sha256 and before_size == after_size,
        "before_sha256": before_sha256,
        "after_sha256": after_sha256,
        "before_size": before_size,
        "after_size": after_size,
        "hash_unchanged": before_sha256 == after_sha256,
        "size_unchanged": before_size == after_size,
    }

    scenarios = [same_file_scenario, same_name, same_hash, duplicate_import, hash_stable]
    return {
        "schema_version": "ids.stage014.manifest_scenarios.v1",
        "stage": "STAGE-014",
        "phase": "Phase 3",
        "acceptance_id": "ACC-STAGE-014",
        "entrance": OPERATIONS_ENTRANCE,
        "overall_valid": all(scenario["valid"] for scenario in scenarios),
        "scenarios": scenarios,
        "does_not_scan_recursively": True,
        "does_not_move_originals": True,
        "does_not_delete_originals": True,
        "does_not_overwrite_originals": True,
        "does_not_write_manifest_files": True,
        "does_not_write_database": True,
        "does_not_create_documents_chunks_jobs": True,
        "does_not_read_raw_metadata": True,
        "does_not_call_external_apis": True,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a metadata-only Stage 014 manifest candidate report."
    )
    parser.add_argument(
        "--source-uri",
        action="append",
        dest="source_uris",
        help="Explicit file:// source URI. Repeat for multiple explicit files.",
    )
    parser.add_argument("--first-seen-at", help="UTC first-seen timestamp for deterministic runs.")
    parser.add_argument(
        "--manifest-generated-at",
        help="UTC manifest candidate timestamp for deterministic runs.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    report = evaluate_manifest_candidates(
        source_uris=args.source_uris,
        first_seen_at=args.first_seen_at,
        manifest_generated_at=args.manifest_generated_at,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
