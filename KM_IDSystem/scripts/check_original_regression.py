#!/usr/bin/env python3
"""Metadata-only Stage 017 original-material regression preflight for IDS."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


OPERATIONS_ENTRANCE = "IDS 系统运营入口"
ZERO_DELTAS = {
    "document_delta": 0,
    "chunk_delta": 0,
    "job_delta": 0,
    "index_delta": 0,
    "import_write_delta": 0,
    "manifest_write_delta": 0,
    "duplicate_write_delta": 0,
    "evidence_write_delta": 0,
    "audit_write_delta": 0,
    "report_write_delta": 0,
    "database_write_delta": 0,
}
NO_SIDE_EFFECT_FLAGS = {
    "does_not_scan_recursively": True,
    "does_not_move_originals": True,
    "does_not_delete_originals": True,
    "does_not_overwrite_originals": True,
    "does_not_write_manifest_files": True,
    "does_not_write_database": True,
    "does_not_write_index": True,
    "does_not_create_documents_chunks_jobs": True,
    "does_not_read_raw_metadata": True,
    "does_not_call_external_apis": True,
}
OFFLINE_DRIVE_STATES = {"offline", "disconnected", "missing", "unavailable"}


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _load_stage016_module() -> Any:
    path = Path(__file__).with_name("check_import_idempotency.py")
    spec = importlib.util.spec_from_file_location("stage016_import_idempotency", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load Stage 016 import-idempotency module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _regression_state_from_import(import_state: str) -> str:
    return {
        "IMPORT_KEY_READY": "REGRESSION_READY",
        "IMPORT_SINGLE_REPEAT": "REGRESSION_REPEAT_SCAN",
        "IMPORT_DUPLICATE_CONTENT": "REGRESSION_DUPLICATE_REGISTRATION_BLOCKED",
        "IMPORT_KEY_CONFLICT": "REGRESSION_DUPLICATE_REGISTRATION_BLOCKED",
        "IMPORT_NOT_CONFIGURED": "REGRESSION_NOT_CONFIGURED",
        "IMPORT_SOURCE_BLOCKED": "REGRESSION_SOURCE_BLOCKED",
        "IMPORT_FINGERPRINT_MISSING": "REGRESSION_SOURCE_BLOCKED",
        "IMPORT_WRITE_BLOCKED": "REGRESSION_WRITE_BLOCKED",
    }.get(import_state, "REGRESSION_UNKNOWN")


def _resume_token_seed(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_uri": record["source_uri"],
        "sha256": record["sha256"],
        "file_size": record["file_size"],
        "mtime": record["mtime"],
        "manifest_identity": record["manifest_identity"],
        "import_idempotency_key": record["import_idempotency_key"],
    }


def _resume_token(record: dict[str, Any]) -> str:
    encoded = json.dumps(
        _resume_token_seed(record),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "ids-regression-resume-sha256-" + hashlib.sha256(encoded).hexdigest()


def _checkpoint_from_record(record: dict[str, Any], *, scan_checked_at: str) -> dict[str, Any]:
    return {
        "scan_checkpoint_id": f"ids-regression-checkpoint-sha256-{record['sha256']}",
        "resume_token": _resume_token(record),
        "source_uri": record["source_uri"],
        "sha256": record["sha256"],
        "file_size": record["file_size"],
        "mtime": record["mtime"],
        "manifest_identity": record["manifest_identity"],
        "import_idempotency_key": record["import_idempotency_key"],
        "created_at": scan_checked_at,
    }


def _record_from_import(record: dict[str, Any], *, scan_checked_at: str) -> dict[str, Any]:
    regression_state = _regression_state_from_import(record["import_state"])
    return {
        "regression_state": regression_state,
        "source_uri": record["source_uri"],
        "source_path": record["source_path"],
        "basename": record["basename"],
        "sha256": record["sha256"],
        "file_size": record["file_size"],
        "mtime": record["mtime"],
        "first_seen_at": record["first_seen_at"],
        "scan_checked_at": scan_checked_at,
        "manifest_identity": record["manifest_identity"],
        "duplicate_state": record["duplicate_state"],
        "import_state": record["import_state"],
        "import_idempotency_key": record["import_idempotency_key"],
        "content_identity_id": record["content_identity_id"],
    }


def _rejection_from_import(rejected: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "regression_state": _regression_state_from_import(rejected["import_state"]),
        "source_uri": rejected.get("source_uri"),
        "import_state": rejected["import_state"],
        "duplicate_state": rejected.get("duplicate_state"),
    }
    if "source_path" in rejected:
        result["source_path"] = rejected["source_path"]
    if "reason" in rejected:
        result["reason"] = rejected["reason"]
    return result


def _base_report(
    *,
    overall_state: str,
    source_uris: list[str | None] | tuple[str | None, ...] | None,
    scan_checked_at: str,
    scan_attempt_id: str | None,
    drive_state: str,
    resume_requested: bool,
    stage016_evaluated: bool,
    regression_records: list[dict[str, Any]] | None = None,
    rejected_inputs: list[dict[str, Any]] | None = None,
    checkpoint_candidates: list[dict[str, Any]] | None = None,
    checkpoint_comparison: dict[str, Any] | None = None,
    resume_valid: bool = False,
    checkpoint_error_count: int = 0,
    hash_drift_count: int = 0,
    import_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    regression_records = regression_records or []
    rejected_inputs = rejected_inputs or []
    checkpoint_candidates = checkpoint_candidates or []
    duplicate_input_count = 0
    duplicate_content_count = 0
    key_conflict_count = 0
    version_conflict_count = 0
    if import_report:
        duplicate_input_count = import_report["duplicate_input_count"]
        duplicate_content_count = import_report["duplicate_content_count"]
        key_conflict_count = import_report["key_conflict_count"]
        version_conflict_count = import_report["version_conflict_count"]
    duplicate_registration_blocked_count = (
        duplicate_input_count + duplicate_content_count + key_conflict_count
    )
    manifest_identities = {
        record["manifest_identity"]
        for record in regression_records
        if "manifest_identity" in record
    }
    report: dict[str, Any] = {
        "schema_version": "ids.stage017.original_regression.v1",
        "stage": "STAGE-017",
        "phase": "Phase 2",
        "acceptance_id": "ACC-STAGE-017",
        "entrance": OPERATIONS_ENTRANCE,
        "customer_visible": False,
        "overall_state": overall_state,
        "safe_mode": overall_state
        not in {"REGRESSION_READY", "REGRESSION_REPEAT_SCAN", "REGRESSION_RESUME_PENDING"},
        "scan_attempt_id": scan_attempt_id,
        "scan_checked_at": scan_checked_at,
        "drive_state": drive_state,
        "resume_requested": resume_requested,
        "resume_valid": resume_valid,
        "stage016_evaluated": stage016_evaluated,
        "regression_records": regression_records,
        "rejected_inputs": rejected_inputs,
        "checkpoint_candidates": checkpoint_candidates,
        "checkpoint_comparison": checkpoint_comparison or {"matches": None, "mismatched_fields": []},
        "source_uri_count": len(source_uris or []),
        "regression_record_count": len(regression_records),
        "rejected_input_count": len(rejected_inputs),
        "error_count": len(rejected_inputs) + checkpoint_error_count + hash_drift_count,
        "checkpoint_error_count": checkpoint_error_count,
        "hash_drift_count": hash_drift_count,
        "import_record_count": len(regression_records),
        "manifest_identity_count": len(manifest_identities),
        "duplicate_input_count": duplicate_input_count,
        "repeated_scan_count": duplicate_input_count,
        "duplicate_content_count": duplicate_content_count,
        "key_conflict_count": key_conflict_count,
        "version_conflict_count": version_conflict_count,
        "duplicate_registration_blocked_count": duplicate_registration_blocked_count,
        "stage016_overall_state": import_report["overall_state"] if import_report else None,
        "duplicate_overall_state": import_report["duplicate_overall_state"] if import_report else None,
        "fingerprint_overall_state": import_report["fingerprint_overall_state"] if import_report else None,
        "manifest_overall_state": import_report["manifest_overall_state"] if import_report else None,
    }
    report.update(ZERO_DELTAS)
    report.update(NO_SIDE_EFFECT_FLAGS)
    return report


def _drive_offline_report(
    *,
    source_uris: list[str | None] | tuple[str | None, ...] | None,
    scan_checked_at: str,
    scan_attempt_id: str | None,
    drive_state: str,
    resume_requested: bool,
) -> dict[str, Any]:
    return _base_report(
        overall_state="REGRESSION_DRIVE_OFFLINE",
        source_uris=source_uris,
        scan_checked_at=scan_checked_at,
        scan_attempt_id=scan_attempt_id,
        drive_state=drive_state,
        resume_requested=resume_requested,
        stage016_evaluated=False,
        rejected_inputs=[
            {
                "regression_state": "REGRESSION_DRIVE_OFFLINE",
                "source_uri": source_uris[0] if source_uris else None,
                "reason": "source drive is offline; recovery must fail closed before source identity evaluation.",
            }
        ],
    )


def _missing_checkpoint_report(
    *,
    source_uris: list[str | None] | tuple[str | None, ...] | None,
    scan_checked_at: str,
    scan_attempt_id: str | None,
    drive_state: str,
) -> dict[str, Any]:
    return _base_report(
        overall_state="REGRESSION_CHECKPOINT_MISSING",
        source_uris=source_uris,
        scan_checked_at=scan_checked_at,
        scan_attempt_id=scan_attempt_id,
        drive_state=drive_state,
        resume_requested=True,
        stage016_evaluated=False,
        rejected_inputs=[
            {
                "regression_state": "REGRESSION_CHECKPOINT_MISSING",
                "source_uri": source_uris[0] if source_uris else None,
                "reason": "resume_requested requires an approved metadata checkpoint.",
            }
        ],
        checkpoint_error_count=1,
    )


def _compare_checkpoint(
    checkpoint: dict[str, Any],
    record: dict[str, Any],
    *,
    resume_token: str | None,
) -> dict[str, Any]:
    fields = [
        "source_uri",
        "sha256",
        "file_size",
        "mtime",
        "manifest_identity",
        "import_idempotency_key",
    ]
    mismatched_fields = [
        field
        for field in fields
        if checkpoint.get(field) != record.get(field)
    ]
    expected_token = checkpoint.get("resume_token")
    if resume_token is not None and resume_token != expected_token:
        mismatched_fields.append("resume_token")
    return {
        "matches": not mismatched_fields,
        "mismatched_fields": sorted(set(mismatched_fields)),
        "scan_checkpoint_id": checkpoint.get("scan_checkpoint_id"),
    }


def evaluate_original_material_regression(
    *,
    source_uris: list[str | None] | tuple[str | None, ...] | None,
    first_seen_at: str | None = None,
    scan_checked_at: str | None = None,
    scan_attempt_id: str | None = None,
    resume_requested: bool = False,
    resume_checkpoint: dict[str, Any] | None = None,
    resume_token: str | None = None,
    drive_state: str = "online",
) -> dict[str, Any]:
    """Build Stage 017 regression facts without persistence side effects."""

    scan_checked_at = scan_checked_at or _utc_now()
    normalized_drive_state = (drive_state or "unknown").strip().lower()
    if normalized_drive_state in OFFLINE_DRIVE_STATES:
        return _drive_offline_report(
            source_uris=source_uris,
            scan_checked_at=scan_checked_at,
            scan_attempt_id=scan_attempt_id,
            drive_state=normalized_drive_state,
            resume_requested=resume_requested,
        )
    if resume_requested and not resume_checkpoint:
        return _missing_checkpoint_report(
            source_uris=source_uris,
            scan_checked_at=scan_checked_at,
            scan_attempt_id=scan_attempt_id,
            drive_state=normalized_drive_state,
        )

    stage016 = _load_stage016_module()
    import_report = stage016.evaluate_import_idempotency(
        source_uris=source_uris,
        first_seen_at=first_seen_at,
        import_checked_at=scan_checked_at,
    )
    regression_records = [
        _record_from_import(record, scan_checked_at=scan_checked_at)
        for record in import_report["import_records"]
    ]
    rejected_inputs = [
        _rejection_from_import(rejected)
        for rejected in import_report["rejected_inputs"]
    ]
    checkpoint_candidates = [
        _checkpoint_from_record(record, scan_checked_at=scan_checked_at)
        for record in regression_records
    ]
    overall_state = _regression_state_from_import(import_report["overall_state"])
    checkpoint_comparison: dict[str, Any] | None = None
    resume_valid = False
    checkpoint_error_count = 0
    hash_drift_count = 0

    if resume_requested and resume_checkpoint:
        if not regression_records:
            overall_state = "REGRESSION_CHECKPOINT_MISSING"
            checkpoint_error_count = 1
            checkpoint_comparison = {"matches": False, "mismatched_fields": ["source_identity"]}
        else:
            checkpoint_comparison = _compare_checkpoint(
                resume_checkpoint,
                regression_records[0],
                resume_token=resume_token,
            )
            if checkpoint_comparison["matches"]:
                overall_state = "REGRESSION_RESUME_PENDING"
                resume_valid = True
            else:
                overall_state = "REGRESSION_HASH_DRIFT"
                hash_drift_count = 1

    return _base_report(
        overall_state=overall_state,
        source_uris=source_uris,
        scan_checked_at=scan_checked_at,
        scan_attempt_id=scan_attempt_id,
        drive_state=normalized_drive_state,
        resume_requested=resume_requested,
        stage016_evaluated=True,
        regression_records=regression_records,
        rejected_inputs=rejected_inputs,
        checkpoint_candidates=checkpoint_candidates,
        checkpoint_comparison=checkpoint_comparison,
        resume_valid=resume_valid,
        checkpoint_error_count=checkpoint_error_count,
        hash_drift_count=hash_drift_count,
        import_report=import_report,
    )


def _same_file_same_hash(
    same_file_uri: str,
    *,
    first_seen_at: str,
    scan_checked_at: str,
) -> dict[str, Any]:
    report = evaluate_original_material_regression(
        source_uris=[same_file_uri, same_file_uri],
        first_seen_at=first_seen_at,
        scan_checked_at=scan_checked_at,
    )
    return {
        "scenario_id": "same_file_same_hash",
        "state": report["overall_state"],
        "valid": (
            report["overall_state"] == "REGRESSION_REPEAT_SCAN"
            and report["duplicate_input_count"] == 1
            and report["regression_record_count"] == 1
        ),
        "duplicate_input_count": report["duplicate_input_count"],
        "regression_record_count": report["regression_record_count"],
        "duplicate_registration_blocked_count": report["duplicate_registration_blocked_count"],
        "import_write_delta": report["import_write_delta"],
    }


def _same_name_different_hash(
    left_uri: str,
    right_uri: str,
    *,
    first_seen_at: str,
    scan_checked_at: str,
) -> dict[str, Any]:
    report = evaluate_original_material_regression(
        source_uris=[left_uri, right_uri],
        first_seen_at=first_seen_at,
        scan_checked_at=scan_checked_at,
    )
    return {
        "scenario_id": "same_name_different_hash",
        "state": report["overall_state"],
        "valid": (
            report["overall_state"] == "REGRESSION_DUPLICATE_REGISTRATION_BLOCKED"
            and report["key_conflict_count"] == 1
            and report["version_conflict_count"] == 1
        ),
        "key_conflict_count": report["key_conflict_count"],
        "version_conflict_count": report["version_conflict_count"],
        "regression_record_count": report["regression_record_count"],
        "import_write_delta": report["import_write_delta"],
    }


def _same_hash_different_path(
    left_uri: str,
    right_uri: str,
    *,
    first_seen_at: str,
    scan_checked_at: str,
) -> dict[str, Any]:
    report = evaluate_original_material_regression(
        source_uris=[left_uri, right_uri],
        first_seen_at=first_seen_at,
        scan_checked_at=scan_checked_at,
    )
    return {
        "scenario_id": "same_hash_different_path",
        "state": report["overall_state"],
        "valid": (
            report["overall_state"] == "REGRESSION_DUPLICATE_REGISTRATION_BLOCKED"
            and report["duplicate_content_count"] == 1
        ),
        "duplicate_content_count": report["duplicate_content_count"],
        "regression_record_count": report["regression_record_count"],
        "import_write_delta": report["import_write_delta"],
    }


def _matching_resume_checkpoint(
    same_file_uri: str,
    *,
    first_seen_at: str,
    scan_checked_at: str,
) -> dict[str, Any]:
    initial = evaluate_original_material_regression(
        source_uris=[same_file_uri],
        first_seen_at=first_seen_at,
        scan_checked_at=scan_checked_at,
    )
    checkpoint = initial["checkpoint_candidates"][0]
    report = evaluate_original_material_regression(
        source_uris=[same_file_uri],
        first_seen_at=first_seen_at,
        scan_checked_at=scan_checked_at,
        resume_requested=True,
        resume_checkpoint=checkpoint,
        resume_token=checkpoint["resume_token"],
    )
    return {
        "scenario_id": "matching_resume_checkpoint",
        "state": report["overall_state"],
        "valid": (
            report["overall_state"] == "REGRESSION_RESUME_PENDING"
            and report["resume_valid"]
            and report["checkpoint_comparison"]["matches"]
        ),
        "resume_valid": report["resume_valid"],
        "checkpoint_error_count": report["checkpoint_error_count"],
        "hash_drift_count": report["hash_drift_count"],
        "document_delta": report["document_delta"],
        "import_write_delta": report["import_write_delta"],
    }


def _offline_drive(same_file_uri: str, *, first_seen_at: str, scan_checked_at: str) -> dict[str, Any]:
    report = evaluate_original_material_regression(
        source_uris=[same_file_uri],
        first_seen_at=first_seen_at,
        scan_checked_at=scan_checked_at,
        drive_state="offline",
    )
    return {
        "scenario_id": "offline_drive",
        "state": report["overall_state"],
        "valid": (
            report["overall_state"] == "REGRESSION_DRIVE_OFFLINE"
            and not report["stage016_evaluated"]
            and report["regression_record_count"] == 0
        ),
        "stage016_evaluated": report["stage016_evaluated"],
        "regression_record_count": report["regression_record_count"],
        "rejected_input_count": report["rejected_input_count"],
    }


def _checkpoint_hash_drift(
    same_file_uri: str,
    *,
    first_seen_at: str,
    scan_checked_at: str,
) -> dict[str, Any]:
    initial = evaluate_original_material_regression(
        source_uris=[same_file_uri],
        first_seen_at=first_seen_at,
        scan_checked_at=scan_checked_at,
    )
    checkpoint = dict(initial["checkpoint_candidates"][0])
    checkpoint["sha256"] = "0" * 64
    report = evaluate_original_material_regression(
        source_uris=[same_file_uri],
        first_seen_at=first_seen_at,
        scan_checked_at=scan_checked_at,
        resume_requested=True,
        resume_checkpoint=checkpoint,
        resume_token=checkpoint["resume_token"],
    )
    return {
        "scenario_id": "checkpoint_hash_drift",
        "state": report["overall_state"],
        "valid": (
            report["overall_state"] == "REGRESSION_HASH_DRIFT"
            and not report["resume_valid"]
            and report["hash_drift_count"] == 1
        ),
        "resume_valid": report["resume_valid"],
        "hash_drift_count": report["hash_drift_count"],
        "mismatched_fields": report["checkpoint_comparison"]["mismatched_fields"],
        "document_delta": report["document_delta"],
        "index_delta": report["index_delta"],
    }


def _duplicate_import_no_persistence(same_file_uri: str, *, first_seen_at: str, scan_checked_at: str) -> dict[str, Any]:
    report = evaluate_original_material_regression(
        source_uris=[same_file_uri, same_file_uri],
        first_seen_at=first_seen_at,
        scan_checked_at=scan_checked_at,
    )
    deltas = {key: report[key] for key in ZERO_DELTAS}
    return {
        "scenario_id": "duplicate_import_no_persistence",
        "state": report["overall_state"],
        "valid": report["overall_state"] == "REGRESSION_REPEAT_SCAN"
        and all(value == 0 for value in deltas.values()),
        "regression_record_count": report["regression_record_count"],
        "duplicate_input_count": report["duplicate_input_count"],
        **deltas,
    }


def build_stage017_scenario_report(
    *,
    same_file_uri: str,
    same_name_left_uri: str,
    same_name_right_uri: str,
    same_hash_left_uri: str,
    same_hash_right_uri: str,
    first_seen_at: str | None = None,
    scan_checked_at: str | None = None,
) -> dict[str, Any]:
    """Validate Phase 3 original-material regression scenarios without side effects."""

    first_seen_at = first_seen_at or _utc_now()
    scan_checked_at = scan_checked_at or _utc_now()
    stage016 = _load_stage016_module()
    stage015 = stage016._load_stage015_module()
    stage013 = stage015._load_stage013_module()
    source_path = stage013._path_from_uri(same_file_uri)
    before_sha256 = stage013._hash_file(source_path)
    before_size = source_path.stat().st_size

    same_file = _same_file_same_hash(
        same_file_uri,
        first_seen_at=first_seen_at,
        scan_checked_at=scan_checked_at,
    )
    same_name = _same_name_different_hash(
        same_name_left_uri,
        same_name_right_uri,
        first_seen_at=first_seen_at,
        scan_checked_at=scan_checked_at,
    )
    same_hash = _same_hash_different_path(
        same_hash_left_uri,
        same_hash_right_uri,
        first_seen_at=first_seen_at,
        scan_checked_at=scan_checked_at,
    )
    resume = _matching_resume_checkpoint(
        same_file_uri,
        first_seen_at=first_seen_at,
        scan_checked_at=scan_checked_at,
    )
    offline = _offline_drive(
        same_file_uri,
        first_seen_at=first_seen_at,
        scan_checked_at=scan_checked_at,
    )
    drift = _checkpoint_hash_drift(
        same_file_uri,
        first_seen_at=first_seen_at,
        scan_checked_at=scan_checked_at,
    )
    no_persistence = _duplicate_import_no_persistence(
        same_file_uri,
        first_seen_at=first_seen_at,
        scan_checked_at=scan_checked_at,
    )

    after_sha256 = stage013._hash_file(source_path)
    after_size = source_path.stat().st_size
    hash_stable = {
        "scenario_id": "original_hash_stable",
        "state": "REGRESSION_HASH_STABLE" if before_sha256 == after_sha256 else "REGRESSION_HASH_DRIFT",
        "valid": before_sha256 == after_sha256 and before_size == after_size,
        "before_sha256": before_sha256,
        "after_sha256": after_sha256,
        "before_size": before_size,
        "after_size": after_size,
        "hash_unchanged": before_sha256 == after_sha256,
        "size_unchanged": before_size == after_size,
    }

    scenarios = [same_file, same_name, same_hash, resume, offline, drift, no_persistence, hash_stable]
    report: dict[str, Any] = {
        "schema_version": "ids.stage017.original_regression_scenarios.v1",
        "stage": "STAGE-017",
        "phase": "Phase 3",
        "acceptance_id": "ACC-STAGE-017",
        "entrance": OPERATIONS_ENTRANCE,
        "overall_valid": all(scenario["valid"] for scenario in scenarios),
        "scenarios": scenarios,
    }
    report.update(NO_SIDE_EFFECT_FLAGS)
    return report


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a metadata-only Stage 017 original-material regression report."
    )
    parser.add_argument(
        "--source-uri",
        action="append",
        dest="source_uris",
        help="Explicit file:// source URI. Repeat for multiple explicit files.",
    )
    parser.add_argument("--first-seen-at", help="UTC first-seen timestamp for deterministic runs.")
    parser.add_argument("--scan-checked-at", help="UTC regression-check timestamp.")
    parser.add_argument("--scan-attempt-id", help="Optional bounded scan attempt identity.")
    parser.add_argument("--drive-state", default="online", help="online, offline, disconnected, or missing.")
    parser.add_argument("--resume-requested", action="store_true", help="Evaluate bounded resume state.")
    parser.add_argument("--resume-token", help="Expected resume token for checkpoint comparison.")
    parser.add_argument(
        "--resume-checkpoint-json",
        help="JSON object containing a metadata-only checkpoint; no file is read.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    resume_checkpoint = None
    if args.resume_checkpoint_json:
        resume_checkpoint = json.loads(args.resume_checkpoint_json)
    report = evaluate_original_material_regression(
        source_uris=args.source_uris,
        first_seen_at=args.first_seen_at,
        scan_checked_at=args.scan_checked_at,
        scan_attempt_id=args.scan_attempt_id,
        resume_requested=args.resume_requested,
        resume_checkpoint=resume_checkpoint,
        resume_token=args.resume_token,
        drive_state=args.drive_state,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
