#!/usr/bin/env python3
"""Metadata-only Stage 016 import-idempotency preflight for IDS operations."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


OPERATIONS_ENTRANCE = "IDS 系统运营入口"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _load_stage015_module() -> Any:
    path = Path(__file__).with_name("check_duplicate_files.py")
    spec = importlib.util.spec_from_file_location("stage015_duplicate_detection", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load Stage 015 duplicate module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _import_state_from_duplicate(duplicate_state: str) -> str:
    return {
        "DUPLICATE_READY": "IMPORT_KEY_READY",
        "DUPLICATE_BATCH_REPEAT": "IMPORT_SINGLE_REPEAT",
        "DUPLICATE_SAME_HASH_DIFFERENT_PATH": "IMPORT_DUPLICATE_CONTENT",
        "DUPLICATE_SAME_NAME_DIFFERENT_HASH": "IMPORT_KEY_CONFLICT",
        "DUPLICATE_VERSION_CONFLICT": "IMPORT_KEY_CONFLICT",
        "DUPLICATE_NOT_CONFIGURED": "IMPORT_NOT_CONFIGURED",
        "DUPLICATE_SOURCE_BLOCKED": "IMPORT_SOURCE_BLOCKED",
        "DUPLICATE_FINGERPRINT_MISSING": "IMPORT_FINGERPRINT_MISSING",
        "DUPLICATE_WRITE_BLOCKED": "IMPORT_WRITE_BLOCKED",
    }.get(duplicate_state, "IMPORT_UNKNOWN")


def _record_from_duplicate_identity(
    identity: dict[str, Any],
    *,
    import_checked_at: str,
) -> dict[str, Any]:
    sha256 = identity["sha256"]
    import_state = _import_state_from_duplicate(identity["duplicate_state"])
    return {
        "import_state": import_state,
        "import_idempotency_key": f"ids-import-file-sha256-{sha256}",
        "content_identity_id": identity["content_identity_id"],
        "manifest_identity": f"ids-manifest-sha256-{sha256}",
        "source_uri": identity["source_uri"],
        "source_path": identity["source_path"],
        "basename": identity["basename"],
        "sha256": sha256,
        "file_size": identity["file_size"],
        "mtime": identity["mtime"],
        "first_seen_at": identity["first_seen_at"],
        "duplicate_state": identity["duplicate_state"],
        "import_checked_at": import_checked_at,
    }


def _rejection_from_duplicate(rejected: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "import_state": _import_state_from_duplicate(rejected["duplicate_state"]),
        "source_uri": rejected.get("source_uri"),
        "duplicate_state": rejected["duplicate_state"],
    }
    if "source_path" in rejected:
        result["source_path"] = rejected["source_path"]
    if "reason" in rejected:
        result["reason"] = rejected["reason"]
    return result


def _batch_key(batch_id: str | None, records: list[dict[str, Any]]) -> str | None:
    if not batch_id:
        return None
    seed = {
        "batch_id": batch_id,
        "import_idempotency_keys": sorted(record["import_idempotency_key"] for record in records),
    }
    encoded = json.dumps(seed, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "ids-import-batch-sha256-" + hashlib.sha256(encoded).hexdigest()


def _overall_state(
    *,
    duplicate_overall_state: str,
    records: list[dict[str, Any]],
    rejected_inputs: list[dict[str, Any]],
    duplicate_input_count: int,
    same_hash_different_path_count: int,
    same_name_different_hash_count: int,
) -> str:
    if rejected_inputs:
        return rejected_inputs[0]["import_state"]
    if same_name_different_hash_count:
        return "IMPORT_KEY_CONFLICT"
    if same_hash_different_path_count:
        return "IMPORT_DUPLICATE_CONTENT"
    if duplicate_input_count:
        return "IMPORT_SINGLE_REPEAT"
    if records:
        return "IMPORT_KEY_READY"
    return _import_state_from_duplicate(duplicate_overall_state)


def evaluate_import_idempotency(
    *,
    source_uris: list[str | None] | tuple[str | None, ...] | None,
    batch_id: str | None = None,
    first_seen_at: str | None = None,
    import_checked_at: str | None = None,
) -> dict[str, Any]:
    """Build import-idempotency facts without persistence side effects."""

    import_checked_at = import_checked_at or _utc_now()
    stage015 = _load_stage015_module()
    duplicate_report = stage015.evaluate_duplicate_files(
        source_uris=source_uris,
        first_seen_at=first_seen_at,
        duplicate_checked_at=import_checked_at,
    )

    records = [
        _record_from_duplicate_identity(identity, import_checked_at=import_checked_at)
        for identity in duplicate_report["duplicate_identities"]
    ]
    rejected_inputs = [
        _rejection_from_duplicate(rejected)
        for rejected in duplicate_report["rejected_inputs"]
    ]
    overall_state = _overall_state(
        duplicate_overall_state=duplicate_report["overall_state"],
        records=records,
        rejected_inputs=rejected_inputs,
        duplicate_input_count=duplicate_report["duplicate_input_count"],
        same_hash_different_path_count=duplicate_report["same_hash_different_path_count"],
        same_name_different_hash_count=duplicate_report["same_name_different_hash_count"],
    )
    batch_idempotency_key = _batch_key(batch_id, records)

    return {
        "schema_version": "ids.stage016.import_idempotency.v1",
        "stage": "STAGE-016",
        "phase": "Phase 2",
        "acceptance_id": "ACC-STAGE-016",
        "entrance": OPERATIONS_ENTRANCE,
        "customer_visible": False,
        "overall_state": overall_state,
        "safe_mode": overall_state not in {"IMPORT_KEY_READY", "IMPORT_SINGLE_REPEAT"},
        "batch_id": batch_id,
        "batch_idempotency_key": batch_idempotency_key,
        "import_records": records,
        "rejected_inputs": rejected_inputs,
        "import_record_count": len(records),
        "rejected_input_count": len(rejected_inputs),
        "error_count": len(rejected_inputs),
        "duplicate_input_count": duplicate_report["duplicate_input_count"],
        "repeated_import_count": duplicate_report["duplicate_input_count"],
        "duplicate_content_count": duplicate_report["same_hash_different_path_count"],
        "key_conflict_count": duplicate_report["same_name_different_hash_count"],
        "version_conflict_count": duplicate_report["version_conflict_count"],
        "document_delta": 0,
        "chunk_delta": 0,
        "job_delta": 0,
        "index_delta": 0,
        "import_write_delta": 0,
        "manifest_write_delta": duplicate_report["manifest_write_delta"],
        "duplicate_write_delta": duplicate_report["duplicate_write_delta"],
        "duplicate_overall_state": duplicate_report["overall_state"],
        "fingerprint_overall_state": duplicate_report["fingerprint_overall_state"],
        "manifest_overall_state": duplicate_report["manifest_overall_state"],
        "does_not_scan_recursively": True,
        "does_not_move_originals": True,
        "does_not_delete_originals": True,
        "does_not_overwrite_originals": True,
        "does_not_write_import_records": True,
        "does_not_write_manifest_files": True,
        "does_not_write_database": True,
        "does_not_write_index": True,
        "does_not_create_documents_chunks_jobs": True,
        "does_not_read_raw_metadata": True,
        "does_not_call_external_apis": True,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a metadata-only Stage 016 import-idempotency report."
    )
    parser.add_argument(
        "--source-uri",
        action="append",
        dest="source_uris",
        help="Explicit file:// source URI. Repeat for multiple explicit files.",
    )
    parser.add_argument("--batch-id", help="Optional approved batch identity.")
    parser.add_argument("--first-seen-at", help="UTC first-seen timestamp for deterministic runs.")
    parser.add_argument(
        "--import-checked-at",
        help="UTC import idempotency timestamp for deterministic runs.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    report = evaluate_import_idempotency(
        source_uris=args.source_uris,
        batch_id=args.batch_id,
        first_seen_at=args.first_seen_at,
        import_checked_at=args.import_checked_at,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
