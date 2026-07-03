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
