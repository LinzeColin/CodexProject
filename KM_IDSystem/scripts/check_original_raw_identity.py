#!/usr/bin/env python3
"""Read-only Stage 012 original-material identity preflight for IDS operations."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse


OPERATIONS_ENTRANCE = "IDS 系统运营入口"
IDS_METADATA_RAW_ROOT = Path("/Users/linzezhang/Downloads/IDS_MetaData")
OK_STATES = {"ORIGINAL_RAW_READY", "ORIGINAL_RAW_DUPLICATE_CONTENT"}
STATE_ORDER = [
    "ORIGINAL_RAW_NOT_CONFIGURED",
    "ORIGINAL_RAW_PATH_BLOCKED",
    "ORIGINAL_RAW_READ_BLOCKED",
    "ORIGINAL_RAW_HASH_CONFLICT",
    "ORIGINAL_RAW_MANIFEST_UNSAFE",
    "ORIGINAL_RAW_UNKNOWN",
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _mtime_utc(path: Path) -> str:
    return (
        datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _resolved(path: Path) -> Path:
    return path.expanduser().resolve(strict=False)


def _is_relative_to(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def _parse_source_uri(source_uri: str | None) -> tuple[str | None, Path | None, str | None]:
    if source_uri is None or not source_uri.strip():
        return "ORIGINAL_RAW_NOT_CONFIGURED", None, "source_uri is required."
    parsed = urlparse(source_uri.strip())
    if parsed.scheme != "file":
        return "ORIGINAL_RAW_PATH_BLOCKED", None, "source_uri must use the file:// scheme."
    if parsed.netloc not in {"", "localhost"}:
        return "ORIGINAL_RAW_PATH_BLOCKED", None, "source_uri must point to a local file path."
    if not parsed.path:
        return "ORIGINAL_RAW_PATH_BLOCKED", None, "source_uri path is missing."
    path = Path(unquote(parsed.path)).expanduser()
    if not path.is_absolute():
        return "ORIGINAL_RAW_PATH_BLOCKED", None, "source_uri must normalize to an absolute path."
    return None, _resolved(path), None


def _block_reason(path: Path) -> str | None:
    raw_root = _resolved(IDS_METADATA_RAW_ROOT)
    resolved = _resolved(path)
    if resolved == raw_root or _is_relative_to(resolved, raw_root):
        return "IDS_MetaData raw metadata content is outside the Stage 012 Phase 2 read scope."
    return None


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _record_for_source(source_uri: str | None, first_seen_at: str) -> dict[str, Any]:
    state, path, reason = _parse_source_uri(source_uri)
    base: dict[str, Any] = {"source_uri": source_uri, "state": state or "ORIGINAL_RAW_UNKNOWN"}
    if path is not None:
        base["source_path"] = str(path)
    if state is not None:
        base["reason"] = reason
        return base

    assert path is not None
    block_reason = _block_reason(path)
    if block_reason is not None:
        return {
            **base,
            "state": "ORIGINAL_RAW_PATH_BLOCKED",
            "reason": block_reason,
        }
    try:
        if not path.exists():
            return {
                **base,
                "state": "ORIGINAL_RAW_PATH_BLOCKED",
                "reason": "source path is absent.",
            }
        if not path.is_file():
            return {
                **base,
                "state": "ORIGINAL_RAW_PATH_BLOCKED",
                "reason": "source path must be an explicit file, not a directory.",
            }
        if not os.access(path, os.R_OK):
            return {
                **base,
                "state": "ORIGINAL_RAW_READ_BLOCKED",
                "reason": "source path is not readable.",
            }
        file_size = path.stat().st_size
        sha256 = _hash_file(path)
    except OSError as exc:
        return {
            **base,
            "state": "ORIGINAL_RAW_READ_BLOCKED",
            "reason": f"Unable to read source identity: {exc.__class__.__name__}",
        }

    return {
        **base,
        "state": "ORIGINAL_RAW_READY",
        "reason": "source identity observed with read-only metadata capture.",
        "source_uri": path.as_uri(),
        "source_path": str(path),
        "sha256": sha256,
        "file_size": file_size,
        "mtime": _mtime_utc(path),
        "first_seen_at": first_seen_at,
    }


def _overall_state(records: list[dict[str, Any]]) -> str:
    if not records:
        return "ORIGINAL_RAW_NOT_CONFIGURED"
    states = [record["state"] for record in records]
    failures = [state for state in states if state not in OK_STATES]
    if not failures:
        return "ORIGINAL_RAW_READY"
    for preferred in STATE_ORDER:
        if preferred in failures:
            return preferred
    return failures[0]


def evaluate_original_raw_identity(
    *,
    source_uris: list[str | None] | tuple[str | None, ...] | None,
    first_seen_at: str | None = None,
) -> dict[str, Any]:
    """Build metadata-only source identity records without writing manifests or databases."""

    first_seen_at = first_seen_at or _utc_now()
    records: list[dict[str, Any]] = []
    seen_keys: set[tuple[str | None, str | None]] = set()
    duplicate_input_count = 0

    for source_uri in source_uris or []:
        record = _record_for_source(source_uri, first_seen_at)
        key = (record.get("source_path"), record.get("sha256"))
        if record["state"] == "ORIGINAL_RAW_READY" and key in seen_keys:
            duplicate_input_count += 1
            continue
        if record["state"] == "ORIGINAL_RAW_READY":
            seen_keys.add(key)
        records.append(record)

    overall_state = _overall_state(records)
    manifest_records = [record for record in records if record["state"] == "ORIGINAL_RAW_READY"]

    return {
        "schema_version": "ids.stage012.original_raw_identity.v1",
        "stage": "STAGE-012",
        "phase": "Phase 2",
        "acceptance_id": "ACC-STAGE-012",
        "entrance": OPERATIONS_ENTRANCE,
        "customer_visible": False,
        "overall_state": overall_state,
        "safe_mode": overall_state != "ORIGINAL_RAW_READY",
        "records": records,
        "record_count": len(records),
        "manifest_record_count": len(manifest_records),
        "duplicate_input_count": duplicate_input_count,
        "error_count": sum(1 for record in records if record["state"] not in OK_STATES),
        "does_not_scan_recursively": True,
        "does_not_move_originals": True,
        "does_not_delete_originals": True,
        "does_not_overwrite_originals": True,
        "does_not_write_manifests": True,
        "does_not_write_database": True,
        "does_not_create_documents_chunks_jobs": True,
        "does_not_read_raw_metadata": True,
        "does_not_call_external_apis": True,
    }


def _ready_records(report: dict[str, Any]) -> list[dict[str, Any]]:
    return [record for record in report["records"] if record["state"] == "ORIGINAL_RAW_READY"]


def _same_name_different_hash(left_uri: str, right_uri: str, first_seen_at: str) -> dict[str, Any]:
    report = evaluate_original_raw_identity(
        source_uris=[left_uri, right_uri],
        first_seen_at=first_seen_at,
    )
    records = _ready_records(report)
    conflict = (
        len(records) == 2
        and Path(records[0]["source_path"]).name == Path(records[1]["source_path"]).name
        and records[0]["sha256"] != records[1]["sha256"]
    )
    return {
        "scenario_id": "same_name_different_hash",
        "state": "ORIGINAL_RAW_HASH_CONFLICT" if conflict else report["overall_state"],
        "valid": conflict,
        "conflict_count": 1 if conflict else 0,
        "record_count": report["record_count"],
        "manifest_record_count": report["manifest_record_count"],
    }


def _same_hash_different_path(left_uri: str, right_uri: str, first_seen_at: str) -> dict[str, Any]:
    report = evaluate_original_raw_identity(
        source_uris=[left_uri, right_uri],
        first_seen_at=first_seen_at,
    )
    records = _ready_records(report)
    duplicate = (
        len(records) == 2
        and records[0]["source_path"] != records[1]["source_path"]
        and records[0]["sha256"] == records[1]["sha256"]
    )
    return {
        "scenario_id": "same_hash_different_path",
        "state": "ORIGINAL_RAW_DUPLICATE_CONTENT" if duplicate else report["overall_state"],
        "valid": duplicate,
        "duplicate_content_count": 1 if duplicate else 0,
        "record_count": report["record_count"],
        "manifest_record_count": report["manifest_record_count"],
    }


def _path_from_uri(source_uri: str) -> Path:
    state, path, reason = _parse_source_uri(source_uri)
    if state is not None or path is None:
        raise ValueError(reason or "Invalid source_uri")
    return path


def build_stage012_scenario_report(
    *,
    same_file_uri: str,
    same_name_left_uri: str,
    same_name_right_uri: str,
    same_hash_left_uri: str,
    same_hash_right_uri: str,
    first_seen_at: str | None = None,
) -> dict[str, Any]:
    """Validate Phase 3 original-material identity scenarios without persistence."""

    first_seen_at = first_seen_at or _utc_now()
    source_path = _path_from_uri(same_file_uri)
    before_sha256 = _hash_file(source_path)
    before_size = source_path.stat().st_size

    same_file = evaluate_original_raw_identity(
        source_uris=[same_file_uri, same_file_uri],
        first_seen_at=first_seen_at,
    )
    same_file_scenario = {
        "scenario_id": "same_file_same_hash",
        "state": same_file["overall_state"],
        "valid": (
            same_file["overall_state"] == "ORIGINAL_RAW_READY"
            and same_file["duplicate_input_count"] == 1
            and same_file["manifest_record_count"] == 1
        ),
        "duplicate_input_count": same_file["duplicate_input_count"],
        "manifest_record_count": same_file["manifest_record_count"],
    }

    same_name = _same_name_different_hash(
        same_name_left_uri,
        same_name_right_uri,
        first_seen_at,
    )
    same_hash = _same_hash_different_path(
        same_hash_left_uri,
        same_hash_right_uri,
        first_seen_at,
    )
    duplicate_import = {
        "scenario_id": "duplicate_import_no_persistence",
        "state": same_file["overall_state"],
        "valid": same_file_scenario["valid"],
        "document_delta": 0,
        "chunk_delta": 0,
        "job_delta": 0,
        "manifest_record_count": same_file["manifest_record_count"],
        "duplicate_input_count": same_file["duplicate_input_count"],
    }

    after_sha256 = _hash_file(source_path)
    after_size = source_path.stat().st_size
    hash_stable = {
        "scenario_id": "original_hash_stable",
        "state": "ORIGINAL_RAW_READY" if before_sha256 == after_sha256 else "ORIGINAL_RAW_UNKNOWN",
        "valid": before_sha256 == after_sha256 and before_size == after_size,
        "before_sha256": before_sha256,
        "after_sha256": after_sha256,
        "before_file_size": before_size,
        "after_file_size": after_size,
        "hash_unchanged": before_sha256 == after_sha256,
        "file_size_unchanged": before_size == after_size,
    }

    scenarios = [same_file_scenario, same_name, same_hash, duplicate_import, hash_stable]
    return {
        "schema_version": "ids.stage012.original_raw_identity_scenarios.v1",
        "stage": "STAGE-012",
        "phase": "Phase 3",
        "acceptance_id": "ACC-STAGE-012",
        "entrance": OPERATIONS_ENTRANCE,
        "overall_valid": all(scenario["valid"] for scenario in scenarios),
        "scenarios": scenarios,
        "does_not_scan_recursively": True,
        "does_not_move_originals": True,
        "does_not_delete_originals": True,
        "does_not_overwrite_originals": True,
        "does_not_write_manifests": True,
        "does_not_write_database": True,
        "does_not_create_documents_chunks_jobs": True,
        "does_not_read_raw_metadata": True,
        "does_not_call_external_apis": True,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a metadata-only Stage 012 original-material identity report."
    )
    parser.add_argument(
        "--source-uri",
        action="append",
        dest="source_uris",
        help="Explicit file:// source URI. Repeat for multiple explicit files.",
    )
    parser.add_argument("--first-seen-at", help="UTC first-seen timestamp for deterministic runs.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    report = evaluate_original_raw_identity(
        source_uris=args.source_uris,
        first_seen_at=args.first_seen_at,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
