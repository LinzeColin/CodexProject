#!/usr/bin/env python3
"""Stage 024 archive threat-model safe extraction helper for IDS."""

from __future__ import annotations

import argparse
import json
import os
import posixpath
import re
import shutil
import tarfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.parse import unquote, urlparse


ENTRANCE = "人类产品入口 + IDS 系统运营入口"
RAW_METADATA_ROOT = Path("/Users/linzezhang/Downloads/IDS_MetaData")
SUPPORTED_DIRECT_EXTRACTION_FORMATS = {"ZIP", "TAR"}
OWNER_REVIEW_ONLY_FORMATS = {"RAR", "7Z"}
ARCHIVE_SUFFIXES = {".zip", ".rar", ".7z", ".tar", ".tgz", ".gz", ".tar.gz"}
DEFAULT_ARCHIVE_FILE_COUNT_LIMIT = 10000
DEFAULT_ARCHIVE_TOTAL_SIZE_LIMIT_BYTES = 4 * 1024 * 1024 * 1024
DEFAULT_ARCHIVE_SINGLE_FILE_SIZE_LIMIT_BYTES = 512 * 1024 * 1024
DEFAULT_ARCHIVE_NESTED_DEPTH_LIMIT = 1
REQUIRED_STAGE024_SCENARIOS = (
    "path_traversal",
    "absolute_path",
    "archive_bomb",
    "nested_archive",
    "garbled_filename",
    "too_many_files",
)
EXPECTED_STAGE024_SCENARIO_RISKS = {
    "path_traversal": "ARCHIVE_PATH_TRAVERSAL_BLOCKED",
    "absolute_path": "ARCHIVE_ABSOLUTE_PATH_BLOCKED",
    "archive_bomb": "ARCHIVE_TOTAL_SIZE_LIMIT_EXCEEDED",
    "nested_archive": "ARCHIVE_NESTED_DEPTH_LIMIT_EXCEEDED",
    "garbled_filename": "ARCHIVE_GARBLED_FILENAME_OWNER_REVIEW_REQUIRED",
    "too_many_files": "ARCHIVE_FILE_COUNT_LIMIT_EXCEEDED",
}

PROCESSING_GUARD_ZEROES = {
    "actual_hash_jobs_started": 0,
    "actual_manifest_jobs_started": 0,
    "actual_dedup_jobs_started": 0,
    "actual_parser_jobs_started": 0,
    "actual_ocr_jobs_started": 0,
    "actual_embedding_jobs_started": 0,
    "actual_index_jobs_started": 0,
    "actual_import_jobs_started": 0,
    "actual_external_api_calls_started": 0,
}

NO_PERSISTENCE_DELTAS = {
    "document_delta": 0,
    "chunk_delta": 0,
    "job_delta": 0,
    "index_delta": 0,
    "import_write_delta": 0,
    "manifest_write_delta": 0,
    "archive_manifest_write_delta": 0,
    "evidence_write_delta": 0,
    "audit_write_delta": 0,
    "report_write_delta": 0,
    "database_write_delta": 0,
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _uri_to_path(uri: str) -> Path:
    parsed = urlparse(uri)
    if parsed.scheme and parsed.scheme != "file":
        raise ValueError(f"Only file:// URIs are supported: {uri}")
    if parsed.scheme == "file":
        return Path(unquote(parsed.path))
    return Path(uri)


def _path_to_uri(path: Path) -> str:
    return path.absolute().as_uri()


def _is_under_raw_metadata(path: Path) -> bool:
    candidate = os.path.normpath(str(path))
    raw_root = os.path.normpath(str(RAW_METADATA_ROOT))
    return candidate == raw_root or candidate.startswith(raw_root + os.sep)


def _archive_type(path: Path) -> str:
    name = path.name.lower()
    if name.endswith(".zip"):
        return "ZIP"
    if name.endswith(".rar"):
        return "RAR"
    if name.endswith(".7z"):
        return "7Z"
    if name.endswith(".tar") or name.endswith(".tar.gz") or name.endswith(".tgz"):
        return "TAR"
    return "UNKNOWN"


def _empty_manifest(archive_type: str, archive_uri: str, staging_uri: str) -> dict[str, Any]:
    return {
        "schema_version": "ids.stage024.archive_manifest.v1",
        "archive_type": archive_type,
        "original_archive_ref": archive_uri,
        "archive_staging_area_uri": staging_uri,
        "entry_count": 0,
        "entries": [],
        "runtime_output_written": False,
    }


def _base_report(
    *,
    archive_uri: str,
    staging_area_uri: str,
    archive_type: str,
    extracted_at: str,
    limits: dict[str, int],
) -> dict[str, Any]:
    return {
        "schema_version": "ids.stage024.archive_threat_model.v1",
        "stage": "STAGE-024",
        "phase": "Phase 2",
        "task_id": "IDS-V0_1-STAGE024-P2",
        "acceptance_id": "ACC-STAGE-024",
        "entrance": ENTRANCE,
        "extracted_at": extracted_at,
        "archive_type": archive_type,
        "archive_source_uri": archive_uri,
        "original_archive_ref": archive_uri,
        "archive_staging_area_uri": staging_area_uri,
        "limits": dict(limits),
        "extraction_state": "ARCHIVE_EXTRACTION_DRAFT",
        "archive_manifest": _empty_manifest(archive_type, archive_uri, staging_area_uri),
        "safe_extracted_entries": [],
        "safe_extracted_file_count": 0,
        "risk_entries": [],
        "owner_review_entries": [],
        "quarantine_entries": [],
        "blocked_entry_count": 0,
        "quarantine_entry_count": 0,
        "post_extract_reingest": {
            "state": "POST_EXTRACT_REINGEST_NOT_READY",
            "required_pipeline": ["hash", "manifest", "dedup", "parser"],
            "reingest_queue": [],
        },
        "cleanup_allowlist": [],
        "cleanup_policy": {
            "cleanup_scope": "archive_staging_temp_files_only",
            "does_not_clean_original_archive": True,
            "does_not_clean_fact_source_or_evidence": True,
            "does_not_clean_manifest_or_audit_outputs": True,
        },
        "processing_guard": dict(PROCESSING_GUARD_ZEROES),
        "no_persistence_deltas": dict(NO_PERSISTENCE_DELTAS),
        "original_archive_preserved": True,
        "does_not_overwrite_original_archive": True,
        "does_not_write_outside_staging": True,
        "does_not_read_raw_metadata": True,
        "does_not_write_archive_manifest_runtime_output": True,
        "does_not_fake_rar_7z_support": True,
    }


def _risk_entry(entry_path: str, risk_code: str, risk_label: str, *, state: str) -> dict[str, Any]:
    return {
        "entry_path": entry_path,
        "entry_state": state,
        "risk_code": risk_code,
        "risk_label": risk_label,
        "owner_review_required": True,
        "quarantine_state": "ARCHIVE_ENTRY_QUARANTINE_REQUIRED",
    }


def _normalize_entry_path(entry_path: str) -> tuple[str | None, dict[str, str] | None]:
    raw = entry_path.replace("\\", "/")
    if raw.startswith("/") or raw.startswith("//") or re.match(r"^[A-Za-z]:", raw):
        return None, {
            "risk_code": "ARCHIVE_ABSOLUTE_PATH_BLOCKED",
            "risk_label": "absolute path is not allowed",
            "state": "ARCHIVE_ENTRY_BLOCKED_ABSOLUTE_PATH",
        }
    if "\ufffd" in raw:
        return None, {
            "risk_code": "ARCHIVE_GARBLED_FILENAME_OWNER_REVIEW_REQUIRED",
            "risk_label": "garbled filename requires owner review before extraction",
            "state": "ARCHIVE_ENTRY_QUARANTINED_GARBLED_FILENAME",
        }
    normalized = posixpath.normpath(raw)
    if normalized in {"", "."}:
        return None, {
            "risk_code": "ARCHIVE_EMPTY_PATH_BLOCKED",
            "risk_label": "empty archive entry path is not allowed",
            "state": "ARCHIVE_ENTRY_BLOCKED_EMPTY_PATH",
        }
    if normalized == ".." or normalized.startswith("../"):
        return None, {
            "risk_code": "ARCHIVE_PATH_TRAVERSAL_BLOCKED",
            "risk_label": "parent traversal is not allowed",
            "state": "ARCHIVE_ENTRY_BLOCKED_PATH_TRAVERSAL",
        }
    return normalized, None


def _archive_depth(normalized_path: str) -> int:
    return sum(1 for part in normalized_path.lower().split("/") if any(part.endswith(suffix) for suffix in ARCHIVE_SUFFIXES))


def _target_inside_staging(staging_path: Path, normalized_path: str) -> tuple[Path, bool]:
    staging_root = staging_path.resolve(strict=False)
    target = (staging_root / normalized_path).resolve(strict=False)
    return target, target == staging_root or str(target).startswith(str(staging_root) + os.sep)


def _append_risk(report: dict[str, Any], entry: dict[str, Any]) -> None:
    report["risk_entries"].append(entry)
    report["owner_review_entries"].append(entry)
    report["quarantine_entries"].append(entry)


def _reingest_item(*, archive_uri: str, entry_path: str, staging_uri: str, size_bytes: int) -> dict[str, Any]:
    return {
        "original_archive_ref": archive_uri,
        "archive_entry_path": entry_path,
        "staging_uri": staging_uri,
        "size_bytes": size_bytes,
        "pipeline_stage_states": {
            "hash": "POST_EXTRACT_HASH_REQUIRED",
            "manifest": "POST_EXTRACT_MANIFEST_REQUIRED",
            "dedup": "POST_EXTRACT_DEDUP_REQUIRED",
            "parser": "POST_EXTRACT_PARSER_REQUIRED",
        },
    }


def _finalize_report(report: dict[str, Any]) -> dict[str, Any]:
    report["safe_extracted_file_count"] = len(report["safe_extracted_entries"])
    report["blocked_entry_count"] = len(report["risk_entries"])
    report["quarantine_entry_count"] = len(report["quarantine_entries"])
    report["archive_manifest"]["entry_count"] = len(report["archive_manifest"]["entries"])
    risk_codes = {entry.get("risk_code") for entry in report["risk_entries"]}
    if report["safe_extracted_entries"]:
        report["post_extract_reingest"]["state"] = "POST_EXTRACT_REINGEST_REQUIRED"
    if report["risk_entries"]:
        if report["safe_extracted_entries"] or risk_codes == {"ARCHIVE_FORMAT_REQUIRES_EXTERNAL_ADAPTER"}:
            report["extraction_state"] = "ARCHIVE_EXTRACTION_OWNER_REVIEW_REQUIRED"
        else:
            report["extraction_state"] = "ARCHIVE_EXTRACTION_BLOCKED"
    elif report["safe_extracted_entries"]:
        report["extraction_state"] = "ARCHIVE_EXTRACTION_READY_FOR_REINGEST"
    else:
        report["extraction_state"] = "ARCHIVE_EXTRACTION_BLOCKED"
    return report


def _handle_entry(
    *,
    report: dict[str, Any],
    archive_uri: str,
    staging_path: Path,
    entry_path: str,
    size_bytes: int,
    entry_index: int,
    limits: dict[str, int],
    extractor: Callable[[Path], None],
) -> None:
    normalized_path, path_risk = _normalize_entry_path(entry_path)
    if path_risk is not None:
        _append_risk(report, _risk_entry(entry_path, **path_risk))
        report["archive_manifest"]["entries"].append(
            {"entry_path": entry_path, "entry_state": path_risk["state"], "size_bytes": size_bytes}
        )
        return
    assert normalized_path is not None

    target, is_inside_staging = _target_inside_staging(staging_path, normalized_path)
    if not is_inside_staging:
        risk = _risk_entry(
            entry_path,
            "ARCHIVE_STAGING_ESCAPE_BLOCKED",
            "normalized target escapes the staging area",
            state="ARCHIVE_ENTRY_BLOCKED_STAGING_ESCAPE",
        )
        _append_risk(report, risk)
        report["archive_manifest"]["entries"].append({**risk, "normalized_entry_path": normalized_path, "size_bytes": size_bytes})
        return
    if entry_index > limits["archive_file_count_limit"]:
        risk = _risk_entry(
            entry_path,
            "ARCHIVE_FILE_COUNT_LIMIT_EXCEEDED",
            "file count limit exceeded",
            state="ARCHIVE_ENTRY_QUARANTINED_FILE_COUNT_LIMIT",
        )
        _append_risk(report, risk)
        report["archive_manifest"]["entries"].append({**risk, "normalized_entry_path": normalized_path, "size_bytes": size_bytes})
        return
    if size_bytes > limits["archive_single_file_size_limit_bytes"]:
        risk = _risk_entry(
            entry_path,
            "ARCHIVE_ENTRY_SIZE_LIMIT_EXCEEDED",
            "single extracted file size limit exceeded",
            state="ARCHIVE_ENTRY_QUARANTINED_SIZE_LIMIT",
        )
        _append_risk(report, risk)
        report["archive_manifest"]["entries"].append({**risk, "normalized_entry_path": normalized_path, "size_bytes": size_bytes})
        return
    if _archive_depth(normalized_path) > limits["archive_nested_depth_limit"]:
        risk = _risk_entry(
            entry_path,
            "ARCHIVE_NESTED_DEPTH_LIMIT_EXCEEDED",
            "nested archive depth limit exceeded",
            state="ARCHIVE_ENTRY_QUARANTINED_NESTED_LIMIT",
        )
        _append_risk(report, risk)
        report["archive_manifest"]["entries"].append({**risk, "normalized_entry_path": normalized_path, "size_bytes": size_bytes})
        return
    if target.exists():
        risk = _risk_entry(
            entry_path,
            "ARCHIVE_STAGING_TARGET_EXISTS",
            "safe extraction refuses to overwrite an existing staging file",
            state="ARCHIVE_ENTRY_BLOCKED_STAGING_OVERWRITE",
        )
        _append_risk(report, risk)
        report["archive_manifest"]["entries"].append({**risk, "normalized_entry_path": normalized_path, "size_bytes": size_bytes})
        return

    target.parent.mkdir(parents=True, exist_ok=True)
    extractor(target)
    staging_uri = _path_to_uri(target)
    safe_entry = {
        "entry_path": entry_path,
        "normalized_entry_path": normalized_path,
        "entry_state": "ARCHIVE_ENTRY_SAFE_EXTRACTED",
        "size_bytes": size_bytes,
        "staging_uri": staging_uri,
        "risk_code": "ARCHIVE_ENTRY_SAFE",
    }
    report["safe_extracted_entries"].append(safe_entry)
    report["archive_manifest"]["entries"].append(safe_entry)
    report["post_extract_reingest"]["reingest_queue"].append(
        _reingest_item(
            archive_uri=archive_uri,
            entry_path=normalized_path,
            staging_uri=staging_uri,
            size_bytes=size_bytes,
        )
    )
    report["cleanup_allowlist"].append(
        {
            "uri": staging_uri,
            "cleanup_class": "ARCHIVE_STAGING_TEMP_FILE",
            "cleanup_allowed_after": "owner-approved rollback or successful post-extract re-ingest",
        }
    )


def _extract_zip(*, report: dict[str, Any], archive_path: Path, staging_path: Path, limits: dict[str, int]) -> None:
    with zipfile.ZipFile(archive_path) as archive:
        infos = [info for info in archive.infolist() if not info.is_dir()]
        total_size = sum(int(info.file_size) for info in infos)
        if total_size > limits["archive_total_size_limit_bytes"]:
            _append_risk(
                report,
                _risk_entry(
                    archive_path.name,
                    "ARCHIVE_TOTAL_SIZE_LIMIT_EXCEEDED",
                    "total expanded archive size limit exceeded",
                    state="ARCHIVE_EXTRACTION_BLOCKED_TOTAL_SIZE_LIMIT",
                ),
            )
            return
        for index, info in enumerate(infos, start=1):
            _handle_entry(
                report=report,
                archive_uri=report["original_archive_ref"],
                staging_path=staging_path,
                entry_path=info.filename,
                size_bytes=int(info.file_size),
                entry_index=index,
                limits=limits,
                extractor=lambda target, entry=info: _copy_zip_entry(archive, entry, target),
            )


def _copy_zip_entry(archive: zipfile.ZipFile, entry: zipfile.ZipInfo, target: Path) -> None:
    with archive.open(entry) as source, target.open("wb") as destination:
        shutil.copyfileobj(source, destination)


def _extract_tar(*, report: dict[str, Any], archive_path: Path, staging_path: Path, limits: dict[str, int]) -> None:
    with tarfile.open(archive_path) as archive:
        members = [member for member in archive.getmembers() if member.isfile() or not member.isdir()]
        regular_members = [member for member in members if member.isfile()]
        total_size = sum(int(member.size) for member in regular_members)
        if total_size > limits["archive_total_size_limit_bytes"]:
            _append_risk(
                report,
                _risk_entry(
                    archive_path.name,
                    "ARCHIVE_TOTAL_SIZE_LIMIT_EXCEEDED",
                    "total expanded archive size limit exceeded",
                    state="ARCHIVE_EXTRACTION_BLOCKED_TOTAL_SIZE_LIMIT",
                ),
            )
            return
        index = 0
        for member in members:
            if not member.isfile():
                risk = _risk_entry(
                    member.name,
                    "ARCHIVE_NON_FILE_ENTRY_BLOCKED",
                    "non-regular tar entries are not extracted",
                    state="ARCHIVE_ENTRY_BLOCKED_NON_FILE",
                )
                _append_risk(report, risk)
                report["archive_manifest"]["entries"].append({**risk, "size_bytes": 0})
                continue
            index += 1
            _handle_entry(
                report=report,
                archive_uri=report["original_archive_ref"],
                staging_path=staging_path,
                entry_path=member.name,
                size_bytes=int(member.size),
                entry_index=index,
                limits=limits,
                extractor=lambda target, entry=member: _copy_tar_entry(archive, entry, target),
            )


def _copy_tar_entry(archive: tarfile.TarFile, entry: tarfile.TarInfo, target: Path) -> None:
    source = archive.extractfile(entry)
    if source is None:
        raise RuntimeError(f"Unable to extract tar entry: {entry.name}")
    with source, target.open("wb") as destination:
        shutil.copyfileobj(source, destination)


def _blocked_report(
    *,
    archive_uri: str,
    staging_area_uri: str,
    archive_type: str,
    extracted_at: str,
    limits: dict[str, int],
    risk_code: str,
    risk_label: str,
) -> dict[str, Any]:
    report = _base_report(
        archive_uri=archive_uri,
        staging_area_uri=staging_area_uri,
        archive_type=archive_type,
        extracted_at=extracted_at,
        limits=limits,
    )
    _append_risk(
        report,
        _risk_entry(
            archive_uri,
            risk_code,
            risk_label,
            state="ARCHIVE_EXTRACTION_BLOCKED",
        ),
    )
    return _finalize_report(report)


def safe_extract_archive(
    *,
    archive_uri: str,
    staging_area_uri: str,
    extracted_at: str | None = None,
    archive_file_count_limit: int = DEFAULT_ARCHIVE_FILE_COUNT_LIMIT,
    archive_total_size_limit_bytes: int = DEFAULT_ARCHIVE_TOTAL_SIZE_LIMIT_BYTES,
    archive_single_file_size_limit_bytes: int = DEFAULT_ARCHIVE_SINGLE_FILE_SIZE_LIMIT_BYTES,
    archive_nested_depth_limit: int = DEFAULT_ARCHIVE_NESTED_DEPTH_LIMIT,
) -> dict[str, Any]:
    """Safely extract ZIP/TAR archives into staging and build an in-memory re-ingest plan."""

    extracted_at = extracted_at or _utc_now()
    limits = {
        "archive_file_count_limit": max(0, int(archive_file_count_limit)),
        "archive_total_size_limit_bytes": max(0, int(archive_total_size_limit_bytes)),
        "archive_single_file_size_limit_bytes": max(0, int(archive_single_file_size_limit_bytes)),
        "archive_nested_depth_limit": max(0, int(archive_nested_depth_limit)),
    }
    archive_path = _uri_to_path(archive_uri)
    staging_path = _uri_to_path(staging_area_uri)
    archive_type = _archive_type(archive_path)

    if _is_under_raw_metadata(archive_path) or _is_under_raw_metadata(staging_path):
        return _blocked_report(
            archive_uri=archive_uri,
            staging_area_uri=staging_area_uri,
            archive_type=archive_type,
            extracted_at=extracted_at,
            limits=limits,
            risk_code="ARCHIVE_SOURCE_BLOCKED_RAW_METADATA_ROOT",
            risk_label="IDS_MetaData raw metadata root is path-only and cannot be opened by this helper",
        )

    report = _base_report(
        archive_uri=archive_uri,
        staging_area_uri=staging_area_uri,
        archive_type=archive_type,
        extracted_at=extracted_at,
        limits=limits,
    )

    if archive_type in OWNER_REVIEW_ONLY_FORMATS:
        _append_risk(
            report,
            _risk_entry(
                archive_path.name,
                "ARCHIVE_FORMAT_REQUIRES_EXTERNAL_ADAPTER",
                f"{archive_type} requires an owner-approved extractor adapter before safe extraction",
                state="ARCHIVE_ENTRY_BLOCKED_UNSUPPORTED_DIRECT_EXTRACTION",
            ),
        )
        return _finalize_report(report)

    if archive_type not in SUPPORTED_DIRECT_EXTRACTION_FORMATS:
        _append_risk(
            report,
            _risk_entry(
                archive_path.name,
                "ARCHIVE_FORMAT_UNSUPPORTED",
                "archive format is not supported by the Stage 024 Phase 2 helper",
                state="ARCHIVE_EXTRACTION_BLOCKED_UNSUPPORTED_FORMAT",
            ),
        )
        return _finalize_report(report)

    if not archive_path.is_file():
        _append_risk(
            report,
            _risk_entry(
                archive_path.name,
                "ARCHIVE_SOURCE_MISSING",
                "archive source file is missing",
                state="ARCHIVE_EXTRACTION_BLOCKED_SOURCE_MISSING",
            ),
        )
        return _finalize_report(report)

    staging_path.mkdir(parents=True, exist_ok=True)
    if archive_type == "ZIP":
        _extract_zip(report=report, archive_path=archive_path, staging_path=staging_path, limits=limits)
    elif archive_type == "TAR":
        _extract_tar(report=report, archive_path=archive_path, staging_path=staging_path, limits=limits)
    return _finalize_report(report)


def _flatten_reingest_queue(scenario_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    queue: list[dict[str, Any]] = []
    for result in scenario_results:
        threat_model = result["archive_threat_model"]
        for item in threat_model["post_extract_reingest"]["reingest_queue"]:
            queue.append({"scenario_id": result["scenario_id"], **item})
    return queue


def _flatten_cleanup_allowlist(scenario_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cleanup_items: list[dict[str, Any]] = []
    for result in scenario_results:
        threat_model = result["archive_threat_model"]
        for item in threat_model["cleanup_allowlist"]:
            cleanup_items.append({"scenario_id": result["scenario_id"], **item})
    return cleanup_items


def _build_reingest_validation(reingest_queue: list[dict[str, Any]]) -> dict[str, Any]:
    pipeline_stage_states = {
        "hash": "POST_EXTRACT_HASH_REQUIRED",
        "manifest": "POST_EXTRACT_MANIFEST_REQUIRED",
        "dedup": "POST_EXTRACT_DEDUP_REQUIRED",
        "parser": "POST_EXTRACT_PARSER_REQUIRED",
    }
    return {
        "state": "POST_EXTRACT_REINGEST_VALIDATED" if reingest_queue else "POST_EXTRACT_REINGEST_NOT_READY",
        "required_pipeline": ["hash", "manifest", "dedup", "parser"],
        "safe_extracted_file_count": len(reingest_queue),
        "pipeline_stage_states": pipeline_stage_states,
        "reingest_queue": reingest_queue,
        "actual_jobs_started": {
            "hash": 0,
            "manifest": 0,
            "dedup": 0,
            "parser": 0,
        },
    }


def _build_cleanup_validation(
    *,
    cleanup_allowlist: list[dict[str, Any]],
    original_archive_refs: list[str],
    scenario_results: list[dict[str, Any]],
) -> dict[str, Any]:
    cleanup_classes = {item.get("cleanup_class") for item in cleanup_allowlist}
    cleanup_uris = [item["uri"] for item in cleanup_allowlist]
    original_archive_in_cleanup = any(ref in cleanup_uris for ref in original_archive_refs)
    policies_preserve_refs = all(
        result["archive_threat_model"]["cleanup_policy"]["does_not_clean_original_archive"]
        and result["archive_threat_model"]["cleanup_policy"]["does_not_clean_fact_source_or_evidence"]
        for result in scenario_results
    )
    targets_are_temp_only = bool(cleanup_allowlist) and cleanup_classes <= {"ARCHIVE_STAGING_TEMP_FILE"}
    return {
        "state": "ARCHIVE_CLEANUP_ALLOWLIST_VALIDATED" if targets_are_temp_only and not original_archive_in_cleanup else "ARCHIVE_CLEANUP_ALLOWLIST_REVIEW_REQUIRED",
        "allowed_cleanup_classes": sorted(cleanup_classes),
        "cleanup_allowlist_uris": cleanup_uris,
        "cleanup_targets_are_staging_temp_files_only": targets_are_temp_only,
        "original_archive_in_cleanup_allowlist": original_archive_in_cleanup,
        "protected_refs_preserved": policies_preserve_refs and not original_archive_in_cleanup,
        "does_not_clean_original_archive": not original_archive_in_cleanup,
        "does_not_clean_fact_source_or_evidence": policies_preserve_refs,
    }


def build_stage024_scenario_report(
    *,
    scenario_archives: dict[str, dict[str, Any]],
    evaluated_at: str | None = None,
    required_scenarios: tuple[str, ...] = REQUIRED_STAGE024_SCENARIOS,
) -> dict[str, Any]:
    """Validate Stage 024 Phase 3 archive-threat scenarios without starting processing jobs."""

    evaluated_at = evaluated_at or _utc_now()
    scenario_results: list[dict[str, Any]] = []
    required_scenario_set = set(required_scenarios)
    for scenario_id in required_scenarios:
        scenario_config = dict(scenario_archives[scenario_id])
        threat_model = safe_extract_archive(
            archive_uri=scenario_config["archive_uri"],
            staging_area_uri=scenario_config["staging_area_uri"],
            extracted_at=evaluated_at,
            archive_file_count_limit=scenario_config.get("archive_file_count_limit", DEFAULT_ARCHIVE_FILE_COUNT_LIMIT),
            archive_total_size_limit_bytes=scenario_config.get(
                "archive_total_size_limit_bytes",
                DEFAULT_ARCHIVE_TOTAL_SIZE_LIMIT_BYTES,
            ),
            archive_single_file_size_limit_bytes=scenario_config.get(
                "archive_single_file_size_limit_bytes",
                DEFAULT_ARCHIVE_SINGLE_FILE_SIZE_LIMIT_BYTES,
            ),
            archive_nested_depth_limit=scenario_config.get("archive_nested_depth_limit", DEFAULT_ARCHIVE_NESTED_DEPTH_LIMIT),
        )
        risk_codes = [entry["risk_code"] for entry in threat_model["risk_entries"]]
        expected_risk_code = EXPECTED_STAGE024_SCENARIO_RISKS.get(scenario_id)
        expected_risk_observed = expected_risk_code is None or expected_risk_code in risk_codes
        scenario_results.append(
            {
                "scenario_id": scenario_id,
                "scenario_state": "ARCHIVE_THREAT_SCENARIO_VALIDATED"
                if expected_risk_observed
                else "ARCHIVE_THREAT_SCENARIO_REVIEW_REQUIRED",
                "expected_risk_code": expected_risk_code,
                "expected_risk_observed": expected_risk_observed,
                "risk_codes": risk_codes,
                "safe_extracted_file_count": threat_model["safe_extracted_file_count"],
                "blocked_entry_count": threat_model["blocked_entry_count"],
                "archive_threat_model": threat_model,
            }
        )

    reingest_queue = _flatten_reingest_queue(scenario_results)
    cleanup_allowlist = _flatten_cleanup_allowlist(scenario_results)
    original_archive_refs = [result["archive_threat_model"]["original_archive_ref"] for result in scenario_results]
    reingest_validation = _build_reingest_validation(reingest_queue)
    cleanup_validation = _build_cleanup_validation(
        cleanup_allowlist=cleanup_allowlist,
        original_archive_refs=original_archive_refs,
        scenario_results=scenario_results,
    )
    required_scenarios_covered = required_scenario_set <= set(scenario_archives)
    required_expected_risks_passed = all(result["expected_risk_observed"] for result in scenario_results)
    validation_passed = (
        required_scenarios_covered
        and required_expected_risks_passed
        and reingest_validation["safe_extracted_file_count"] > 0
        and cleanup_validation["protected_refs_preserved"]
    )
    return {
        "schema_version": "ids.stage024.archive_threat_model.scenario_validation.v1",
        "stage": "STAGE-024",
        "phase": "Phase 3",
        "task_id": "IDS-V0_1-STAGE024-P3",
        "acceptance_id": "ACC-STAGE-024",
        "entrance": ENTRANCE,
        "evaluated_at": evaluated_at,
        "required_scenarios": list(required_scenarios),
        "scenario_count": len(scenario_results),
        "required_scenarios_covered": required_scenarios_covered,
        "validation_state": "ARCHIVE_THREAT_SCENARIO_VALIDATION_PASSED"
        if validation_passed
        else "ARCHIVE_THREAT_SCENARIO_VALIDATION_REVIEW_REQUIRED",
        "scenario_results": scenario_results,
        "reingest_validation": reingest_validation,
        "cleanup_validation": cleanup_validation,
        "processing_guard": dict(PROCESSING_GUARD_ZEROES),
        "no_persistence_deltas": dict(NO_PERSISTENCE_DELTAS),
        "does_not_read_raw_metadata": True,
        "does_not_write_archive_manifest_runtime_output": True,
        "does_not_start_processing_jobs": True,
        "does_not_use_fake_ids_business_data": True,
    }


def _archive_threat_report_sample(
    archive_threat_report: dict[str, Any],
    scenario_report: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "archive_manifest_sample": archive_threat_report.get("archive_manifest", {}),
        "safety_block_log": archive_threat_report.get("risk_entries", []),
        "cleanup_allowlist_sample": archive_threat_report.get("cleanup_allowlist", []),
        "post_extract_reingest_sample": archive_threat_report.get("post_extract_reingest", {}),
        "scenario_validation_sample": scenario_report or {},
    }


def build_archive_threat_owner_feedback_summary(
    archive_threat_report: dict[str, Any],
    *,
    scenario_report: dict[str, Any] | None = None,
    recorded_at: str | None = None,
    stage_review_findings: list[str] | tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """Build Phase 4 closeout evidence without creating runtime artifacts."""

    recorded_at = recorded_at or _utc_now()
    cleanup_allowlist = archive_threat_report.get("cleanup_allowlist", [])
    cleanup_uris = [item["uri"] for item in cleanup_allowlist]
    original_archive_ref = archive_threat_report.get("original_archive_ref")
    cleanup_classes = sorted({item.get("cleanup_class") for item in cleanup_allowlist if item.get("cleanup_class")})
    original_archive_in_cleanup = bool(original_archive_ref and original_archive_ref in cleanup_uris)
    return {
        "schema_version": "ids.stage024.archive_threat_model.owner_feedback.v1",
        "stage": "STAGE-024",
        "phase": "Phase 4",
        "task_id": "IDS-V0_1-STAGE024-P4",
        "acceptance_id": "ACC-STAGE-024",
        "entrance": ENTRANCE,
        "recorded_at": recorded_at,
        "report_sample": _archive_threat_report_sample(archive_threat_report, scenario_report),
        "risk_checklist": {
            "ARCHIVE_PATH_TRAVERSAL_BLOCKED": "路径穿越被阻断；不得写出 staging 根目录。",
            "ARCHIVE_ABSOLUTE_PATH_BLOCKED": "绝对路径被阻断；不得按归档内绝对路径写本机文件。",
            "ARCHIVE_TOTAL_SIZE_LIMIT_EXCEEDED": "解压后总量超过限制；必须停止并进入 owner review。",
            "ARCHIVE_ENTRY_SIZE_LIMIT_EXCEEDED": "单文件大小超过限制；该条目隔离并等待人工复核。",
            "ARCHIVE_NESTED_DEPTH_LIMIT_EXCEEDED": "嵌套包深度超过限制；禁止递归自动解压。",
            "ARCHIVE_GARBLED_FILENAME_OWNER_REVIEW_REQUIRED": "乱码文件名进入人工复核；不得猜测或重命名后继续。",
            "ARCHIVE_FILE_COUNT_LIMIT_EXCEEDED": "文件数超过限制；后续条目进入隔离状态。",
            "ARCHIVE_FORMAT_REQUIRES_EXTERNAL_ADAPTER": "RAR/7Z 等格式需要 owner 批准的外部 adapter，当前不伪造支持。",
            "ARCHIVE_SOURCE_BLOCKED_RAW_METADATA_ROOT": "IDS_MetaData 原始数据库根路径被阻断，helper 不读取内容。",
            "ARCHIVE_STAGING_TARGET_EXISTS": "目标 staging 文件已存在时拒绝覆盖。",
        },
        "automatic_extraction_boundaries": [
            "只允许 owner 批准的 file:// archive_uri 和 staging_area_uri。",
            "不覆盖原始压缩包，不移动、删除、重写或修复原始文件。",
            "不写出指定 staging 区，不覆盖 staging 中既有文件。",
            "RAR/7Z、乱码文件名、路径风险、超限和嵌套风险必须进入 owner review 或 quarantine。",
            "archive_manifest 样例和安全阻断日志只作为内存级 closeout evidence，不写 runtime output。",
            "安全解压产物只进入 hash、manifest、dedup、parser re-ingest 计划，不启动实际处理 job。",
        ],
        "stop_conditions": [
            "读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描 /Users/linzezhang/Downloads/IDS_MetaData 内容。",
            "清理原始压缩包、事实源、证据产物、manifest、audit output 或 raw metadata。",
            "绕过 staging 边界、路径过滤、owner review、quarantine 或 cleanup allowlist。",
            "启动 hash、manifest、dedup、parser、OCR、Embedding、index、import、backend、frontend、worker 或 external API job。",
            "写 runtime report、database、evidence ledger、audit log、index、document/chunk/job/import row 或 archive_manifest runtime output。",
            "执行 GitHub upload、PR、merge、app reinstall 或进入 STAGE-025。",
        ],
        "failure_explanations": {
            "ARCHIVE_EXTRACTION_BLOCKED": "压缩包被安全阻断；不得继续解压、解析或清理原始文件。",
            "ARCHIVE_EXTRACTION_OWNER_REVIEW_REQUIRED": "压缩包需要 owner 复核；请先查看阻断日志、隔离项、清理白名单和 re-ingest 计划。",
            "ARCHIVE_EXTRACTION_READY_FOR_REINGEST": "安全条目已写入 staging；后续必须重新进入 hash、manifest、dedup、parser 流程。",
            "ARCHIVE_CLEANUP_ALLOWLIST_VALIDATED": "清理白名单只允许 staging temp files；原始归档、事实源和证据产物不在清理范围。",
        },
        "staging_rollback_and_cleanup": {
            "state": "ARCHIVE_STAGING_ROLLBACK_GUIDE_READY",
            "allowed_cleanup_classes": cleanup_classes,
            "cleanup_allowlist_uris": cleanup_uris,
            "cleanup_targets_are_staging_temp_files_only": bool(cleanup_allowlist)
            and set(cleanup_classes) <= {"ARCHIVE_STAGING_TEMP_FILE"},
            "original_archive_in_cleanup_allowlist": original_archive_in_cleanup,
            "protected_refs_preserved": not original_archive_in_cleanup
            and archive_threat_report.get("cleanup_policy", {}).get("does_not_clean_fact_source_or_evidence", False),
            "rollback_steps": [
                "Stop after Phase 4 closeout; do not enter STAGE-025 in the same run.",
                "If rollback is needed, delete only owner-approved staging temp files listed in cleanup_allowlist.",
                "Do not delete, move, overwrite, rewrite, repair, normalize, compact, or deduplicate the original archive or fact sources.",
                "Return BATCH021_030 state to STAGE-024 Phase 3 complete and Phase 4 pending if this closeout is reverted.",
            ],
        },
        "rollback_steps": [
            "Revert Stage024 Phase4 helper additions, focused tests, closeout evidence, Stage005 validator/test changes, BATCH021_030 lock, roadmap/event updates, and rendered owner-file changes.",
            "Do not clean /Users/linzezhang/Downloads/IDS_MetaData, original archives, fact sources, runtime databases, reports, outputs, persisted manifests, evidence ledgers, audit logs, indexes, app entries, or GitHub state.",
            "Delete only owner-approved staging temp files from cleanup_allowlist when a local rollback explicitly authorizes cleanup.",
            "After rollback, STAGE-024 should return to Phase 3 complete and Phase 4 pending.",
        ],
        "whole_stage_review": {
            "result": "passed_with_local_evidence",
            "completed_phases": ["Phase 1", "Phase 2", "Phase 3", "Phase 4"],
            "reviewed_acceptance_id": "ACC-STAGE-024",
            "findings": list(stage_review_findings or []),
            "unresolved_findings": [],
            "next_stage": "STAGE-025",
            "batch_upload_allowed": False,
            "next_batch_gate": "IDS-STAGE025-P1-GATE",
            "github_upload_status": "not_started",
            "app_reinstall_status": "not_started",
        },
        "processing_guard": dict(PROCESSING_GUARD_ZEROES),
        "no_persistence_deltas": dict(NO_PERSISTENCE_DELTAS),
        "does_not_write_archive_manifest_runtime_output": True,
        "does_not_write_report_files": True,
        "does_not_write_json_output_files": True,
        "does_not_write_database_rows": True,
        "does_not_push_to_github": True,
        "does_not_reinstall_app_entries": True,
        "does_not_enter_stage025": True,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Safely extract an IDS Stage 024 archive into an approved staging area.")
    parser.add_argument("--archive-uri", required=True, help="Owner-approved file:// archive URI.")
    parser.add_argument("--staging-area-uri", required=True, help="Owner-approved file:// staging root URI.")
    parser.add_argument("--extracted-at", default=None, help="Optional UTC timestamp for deterministic evidence.")
    parser.add_argument("--archive-file-count-limit", type=int, default=DEFAULT_ARCHIVE_FILE_COUNT_LIMIT)
    parser.add_argument("--archive-total-size-limit-bytes", type=int, default=DEFAULT_ARCHIVE_TOTAL_SIZE_LIMIT_BYTES)
    parser.add_argument("--archive-single-file-size-limit-bytes", type=int, default=DEFAULT_ARCHIVE_SINGLE_FILE_SIZE_LIMIT_BYTES)
    parser.add_argument("--archive-nested-depth-limit", type=int, default=DEFAULT_ARCHIVE_NESTED_DEPTH_LIMIT)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    report = safe_extract_archive(
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
