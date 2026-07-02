#!/usr/bin/env python3
"""Metadata-only Stage 015 duplicate-file detection preflight for IDS operations."""

from __future__ import annotations

import argparse
import importlib.util
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


OPERATIONS_ENTRANCE = "IDS 系统运营入口"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _load_local_module(filename: str, module_name: str) -> Any:
    path = Path(__file__).with_name(filename)
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load local IDS module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_stage013_module() -> Any:
    return _load_local_module("check_file_fingerprint.py", "stage013_file_fingerprint")


def _load_stage014_module() -> Any:
    return _load_local_module("check_manifest_generation.py", "stage014_manifest_generation")


def _duplicate_state_from_fingerprint(fingerprint_state: str) -> str:
    return {
        "FINGERPRINT_READY": "DUPLICATE_READY",
        "FINGERPRINT_DUPLICATE_CONTENT": "DUPLICATE_SAME_HASH_DIFFERENT_PATH",
        "FINGERPRINT_NOT_CONFIGURED": "DUPLICATE_NOT_CONFIGURED",
        "FINGERPRINT_PATH_BLOCKED": "DUPLICATE_SOURCE_BLOCKED",
        "FINGERPRINT_READ_BLOCKED": "DUPLICATE_SOURCE_BLOCKED",
        "FINGERPRINT_HASH_CONFLICT": "DUPLICATE_SAME_NAME_DIFFERENT_HASH",
        "FINGERPRINT_MIME_UNKNOWN": "DUPLICATE_FINGERPRINT_MISSING",
        "FINGERPRINT_MIME_CONFLICT": "DUPLICATE_VERSION_CONFLICT",
        "FINGERPRINT_MANIFEST_UNSAFE": "DUPLICATE_WRITE_BLOCKED",
    }.get(fingerprint_state, "DUPLICATE_UNKNOWN")


def _identity_from_fingerprint(
    record: dict[str, Any],
    *,
    duplicate_checked_at: str,
) -> dict[str, Any]:
    sha256 = record["sha256"]
    source_path = Path(record["source_path"])
    return {
        "duplicate_state": "DUPLICATE_READY",
        "content_identity_id": f"ids-duplicate-sha256-{sha256}",
        "source_uri": record["source_uri"],
        "source_path": record["source_path"],
        "basename": source_path.name,
        "sha256": sha256,
        "file_size": record["file_size"],
        "mtime": record["mtime"],
        "first_seen_at": record["first_seen_at"],
        "duplicate_checked_at": duplicate_checked_at,
    }


def _rejection_from_fingerprint(record: dict[str, Any]) -> dict[str, Any]:
    rejected: dict[str, Any] = {
        "duplicate_state": _duplicate_state_from_fingerprint(record["state"]),
        "source_uri": record.get("source_uri"),
        "fingerprint_state": record["state"],
    }
    if "source_path" in record:
        rejected["source_path"] = record["source_path"]
    if "reason" in record:
        rejected["reason"] = record["reason"]
    return rejected


def _group_by(items: list[dict[str, Any]], key: str) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in items:
        groups[item[key]].append(item)
    return dict(groups)


def _same_hash_different_path_groups(
    identities: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    groups = []
    for sha256, items in _group_by(identities, "sha256").items():
        source_paths = sorted({item["source_path"] for item in items})
        if len(source_paths) > 1:
            groups.append(
                {
                    "duplicate_state": "DUPLICATE_SAME_HASH_DIFFERENT_PATH",
                    "sha256": sha256,
                    "source_paths": source_paths,
                    "source_uris": sorted({item["source_uri"] for item in items}),
                    "count": len(source_paths),
                }
            )
    return groups


def _same_name_different_hash_groups(
    identities: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    groups = []
    for basename, items in _group_by(identities, "basename").items():
        hashes = sorted({item["sha256"] for item in items})
        if len(hashes) > 1:
            groups.append(
                {
                    "duplicate_state": "DUPLICATE_SAME_NAME_DIFFERENT_HASH",
                    "basename": basename,
                    "sha256_values": hashes,
                    "source_paths": sorted({item["source_path"] for item in items}),
                    "count": len(hashes),
                }
            )
    return groups


def _mark_conflict_identities(
    identities: list[dict[str, Any]],
    *,
    same_hash_groups: list[dict[str, Any]],
    same_name_groups: list[dict[str, Any]],
) -> None:
    same_name_basenames = {group["basename"] for group in same_name_groups}
    same_hashes = {group["sha256"] for group in same_hash_groups}
    for identity in identities:
        if identity["basename"] in same_name_basenames:
            identity["duplicate_state"] = "DUPLICATE_SAME_NAME_DIFFERENT_HASH"
        elif identity["sha256"] in same_hashes:
            identity["duplicate_state"] = "DUPLICATE_SAME_HASH_DIFFERENT_PATH"


def _overall_state(
    *,
    identities: list[dict[str, Any]],
    rejected_inputs: list[dict[str, Any]],
    same_hash_groups: list[dict[str, Any]],
    same_name_groups: list[dict[str, Any]],
    duplicate_input_count: int,
) -> str:
    if rejected_inputs:
        return rejected_inputs[0]["duplicate_state"]
    if same_name_groups:
        return "DUPLICATE_SAME_NAME_DIFFERENT_HASH"
    if same_hash_groups:
        return "DUPLICATE_SAME_HASH_DIFFERENT_PATH"
    if duplicate_input_count:
        return "DUPLICATE_BATCH_REPEAT"
    if identities:
        return "DUPLICATE_READY"
    return "DUPLICATE_NOT_CONFIGURED"


def evaluate_duplicate_files(
    *,
    source_uris: list[str | None] | tuple[str | None, ...] | None,
    first_seen_at: str | None = None,
    duplicate_checked_at: str | None = None,
) -> dict[str, Any]:
    """Build duplicate-file detection facts without persistence side effects."""

    duplicate_checked_at = duplicate_checked_at or _utc_now()
    stage013 = _load_stage013_module()
    stage014 = _load_stage014_module()
    fingerprint_report = stage013.evaluate_file_fingerprints(
        source_uris=source_uris,
        first_seen_at=first_seen_at,
    )
    manifest_report = stage014.evaluate_manifest_candidates(
        source_uris=source_uris,
        first_seen_at=first_seen_at,
        manifest_generated_at=duplicate_checked_at,
    )

    identities: list[dict[str, Any]] = []
    rejected_inputs: list[dict[str, Any]] = []
    for record in fingerprint_report["records"]:
        if record["state"] == "FINGERPRINT_READY":
            identities.append(
                _identity_from_fingerprint(record, duplicate_checked_at=duplicate_checked_at)
            )
        else:
            rejected_inputs.append(_rejection_from_fingerprint(record))

    same_hash_groups = _same_hash_different_path_groups(identities)
    same_name_groups = _same_name_different_hash_groups(identities)
    _mark_conflict_identities(
        identities,
        same_hash_groups=same_hash_groups,
        same_name_groups=same_name_groups,
    )

    duplicate_input_count = fingerprint_report["duplicate_input_count"]
    overall_state = _overall_state(
        identities=identities,
        rejected_inputs=rejected_inputs,
        same_hash_groups=same_hash_groups,
        same_name_groups=same_name_groups,
        duplicate_input_count=duplicate_input_count,
    )

    return {
        "schema_version": "ids.stage015.duplicate_detection.v1",
        "stage": "STAGE-015",
        "phase": "Phase 2",
        "acceptance_id": "ACC-STAGE-015",
        "entrance": OPERATIONS_ENTRANCE,
        "customer_visible": False,
        "overall_state": overall_state,
        "safe_mode": overall_state not in {"DUPLICATE_READY", "DUPLICATE_BATCH_REPEAT"},
        "duplicate_identities": identities,
        "rejected_inputs": rejected_inputs,
        "same_hash_different_path_groups": same_hash_groups,
        "same_name_different_hash_groups": same_name_groups,
        "identity_count": len(identities),
        "rejected_input_count": len(rejected_inputs),
        "error_count": len(rejected_inputs),
        "duplicate_input_count": duplicate_input_count,
        "repeated_batch_import_count": duplicate_input_count,
        "same_hash_different_path_count": len(same_hash_groups),
        "same_name_different_hash_count": len(same_name_groups),
        "version_conflict_count": len(same_name_groups),
        "document_delta": 0,
        "chunk_delta": 0,
        "job_delta": 0,
        "duplicate_write_delta": 0,
        "manifest_write_delta": manifest_report["manifest_write_delta"],
        "fingerprint_overall_state": fingerprint_report["overall_state"],
        "manifest_overall_state": manifest_report["overall_state"],
        "manifest_candidate_count": manifest_report["candidate_count"],
        "does_not_scan_recursively": True,
        "does_not_move_originals": True,
        "does_not_delete_originals": True,
        "does_not_overwrite_originals": True,
        "does_not_write_duplicate_ledger": True,
        "does_not_write_database": True,
        "does_not_create_documents_chunks_jobs": True,
        "does_not_read_raw_metadata": True,
        "does_not_call_external_apis": True,
    }


def _same_name_different_hash(
    left_uri: str,
    right_uri: str,
    *,
    first_seen_at: str,
    duplicate_checked_at: str,
) -> dict[str, Any]:
    report = evaluate_duplicate_files(
        source_uris=[left_uri, right_uri],
        first_seen_at=first_seen_at,
        duplicate_checked_at=duplicate_checked_at,
    )
    return {
        "scenario_id": "same_name_different_hash",
        "state": report["overall_state"],
        "valid": (
            report["overall_state"] == "DUPLICATE_SAME_NAME_DIFFERENT_HASH"
            and report["same_name_different_hash_count"] == 1
            and report["version_conflict_count"] == 1
        ),
        "same_name_different_hash_count": report["same_name_different_hash_count"],
        "version_conflict_count": report["version_conflict_count"],
        "identity_count": report["identity_count"],
        "duplicate_write_delta": report["duplicate_write_delta"],
    }


def _same_hash_different_path(
    left_uri: str,
    right_uri: str,
    *,
    first_seen_at: str,
    duplicate_checked_at: str,
) -> dict[str, Any]:
    report = evaluate_duplicate_files(
        source_uris=[left_uri, right_uri],
        first_seen_at=first_seen_at,
        duplicate_checked_at=duplicate_checked_at,
    )
    return {
        "scenario_id": "same_hash_different_path",
        "state": report["overall_state"],
        "valid": (
            report["overall_state"] == "DUPLICATE_SAME_HASH_DIFFERENT_PATH"
            and report["same_hash_different_path_count"] == 1
        ),
        "duplicate_content_count": report["same_hash_different_path_count"],
        "identity_count": report["identity_count"],
        "duplicate_write_delta": report["duplicate_write_delta"],
    }


def build_stage015_scenario_report(
    *,
    same_file_uri: str,
    same_name_left_uri: str,
    same_name_right_uri: str,
    same_hash_left_uri: str,
    same_hash_right_uri: str,
    first_seen_at: str | None = None,
    duplicate_checked_at: str | None = None,
) -> dict[str, Any]:
    """Validate Phase 3 duplicate scenarios without persistence side effects."""

    first_seen_at = first_seen_at or _utc_now()
    duplicate_checked_at = duplicate_checked_at or _utc_now()
    stage013 = _load_stage013_module()
    source_path = stage013._path_from_uri(same_file_uri)
    before_sha256 = stage013._hash_file(source_path)
    before_size = source_path.stat().st_size

    same_file = evaluate_duplicate_files(
        source_uris=[same_file_uri, same_file_uri],
        first_seen_at=first_seen_at,
        duplicate_checked_at=duplicate_checked_at,
    )
    same_file_scenario = {
        "scenario_id": "same_file_same_hash",
        "state": same_file["overall_state"],
        "valid": (
            same_file["overall_state"] == "DUPLICATE_BATCH_REPEAT"
            and same_file["duplicate_input_count"] == 1
            and same_file["identity_count"] == 1
        ),
        "duplicate_input_count": same_file["duplicate_input_count"],
        "identity_count": same_file["identity_count"],
        "duplicate_write_delta": same_file["duplicate_write_delta"],
    }

    same_name = _same_name_different_hash(
        same_name_left_uri,
        same_name_right_uri,
        first_seen_at=first_seen_at,
        duplicate_checked_at=duplicate_checked_at,
    )
    same_hash = _same_hash_different_path(
        same_hash_left_uri,
        same_hash_right_uri,
        first_seen_at=first_seen_at,
        duplicate_checked_at=duplicate_checked_at,
    )
    duplicate_import = {
        "scenario_id": "duplicate_import_no_persistence",
        "state": same_file["overall_state"],
        "valid": (
            same_file_scenario["valid"]
            and same_file["document_delta"] == 0
            and same_file["chunk_delta"] == 0
            and same_file["job_delta"] == 0
            and same_file["duplicate_write_delta"] == 0
            and same_file["manifest_write_delta"] == 0
        ),
        "document_delta": same_file["document_delta"],
        "chunk_delta": same_file["chunk_delta"],
        "job_delta": same_file["job_delta"],
        "duplicate_write_delta": same_file["duplicate_write_delta"],
        "manifest_write_delta": same_file["manifest_write_delta"],
        "identity_count": same_file["identity_count"],
        "duplicate_input_count": same_file["duplicate_input_count"],
    }

    after_sha256 = stage013._hash_file(source_path)
    after_size = source_path.stat().st_size
    hash_stable = {
        "scenario_id": "original_hash_stable",
        "state": "DUPLICATE_READY" if before_sha256 == after_sha256 else "DUPLICATE_UNKNOWN",
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
        "schema_version": "ids.stage015.duplicate_scenarios.v1",
        "stage": "STAGE-015",
        "phase": "Phase 3",
        "acceptance_id": "ACC-STAGE-015",
        "entrance": OPERATIONS_ENTRANCE,
        "overall_valid": all(scenario["valid"] for scenario in scenarios),
        "scenarios": scenarios,
        "does_not_scan_recursively": True,
        "does_not_move_originals": True,
        "does_not_delete_originals": True,
        "does_not_overwrite_originals": True,
        "does_not_write_duplicate_ledger": True,
        "does_not_write_database": True,
        "does_not_create_documents_chunks_jobs": True,
        "does_not_read_raw_metadata": True,
        "does_not_call_external_apis": True,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a metadata-only Stage 015 duplicate-file detection report."
    )
    parser.add_argument(
        "--source-uri",
        action="append",
        dest="source_uris",
        help="Explicit file:// source URI. Repeat for multiple explicit files.",
    )
    parser.add_argument("--first-seen-at", help="UTC first-seen timestamp for deterministic runs.")
    parser.add_argument(
        "--duplicate-checked-at",
        help="UTC duplicate check timestamp for deterministic runs.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    report = evaluate_duplicate_files(
        source_uris=args.source_uris,
        first_seen_at=args.first_seen_at,
        duplicate_checked_at=args.duplicate_checked_at,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
