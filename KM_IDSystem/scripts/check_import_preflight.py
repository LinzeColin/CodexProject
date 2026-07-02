#!/usr/bin/env python3
"""Metadata-only Stage 018 import preflight estimate for IDS."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse


ENTRANCE = "人类产品入口 + IDS 系统运营入口"
IDS_METADATA_RAW_ROOT = Path("/Users/linzezhang/Downloads/IDS_MetaData")
OFFLINE_DRIVE_STATES = {"offline", "disconnected", "missing", "unavailable"}
ARCHIVE_EXTENSIONS = {".zip", ".rar", ".7z", ".tar", ".gz", ".tgz", ".bz2", ".xz"}
SCANNED_HINT_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".heic", ".pdf"}
EMBEDDING_HINT_EXTENSIONS = {
    ".md",
    ".txt",
    ".csv",
    ".json",
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
}
SUPPORTED_EXTENSIONS = ARCHIVE_EXTENSIONS | SCANNED_HINT_EXTENSIONS | EMBEDDING_HINT_EXTENSIONS
NO_SIDE_EFFECT_FLAGS = {
    "does_not_scan_recursively": True,
    "does_not_parse_body_text": True,
    "does_not_start_ocr": True,
    "does_not_create_embeddings": True,
    "does_not_build_index": True,
    "does_not_start_import": True,
    "does_not_write_manifest_files": True,
    "does_not_write_database": True,
    "does_not_create_documents_chunks_jobs": True,
    "does_not_read_raw_metadata": True,
    "does_not_call_external_apis": True,
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


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
        return "PREFLIGHT_NOT_CONFIGURED", None, "source_uri is required."
    parsed = urlparse(source_uri.strip())
    if parsed.scheme != "file":
        return "PREFLIGHT_SOURCE_BLOCKED", None, "source_uri must use the file:// scheme."
    if parsed.netloc not in {"", "localhost"}:
        return "PREFLIGHT_SOURCE_BLOCKED", None, "source_uri must point to a local path."
    if not parsed.path:
        return "PREFLIGHT_SOURCE_BLOCKED", None, "source_uri path is missing."
    path = Path(unquote(parsed.path)).expanduser()
    if not path.is_absolute():
        return "PREFLIGHT_SOURCE_BLOCKED", None, "source_uri must normalize to an absolute path."
    return None, _resolved(path), None


def _raw_metadata_block_reason(path: Path) -> str | None:
    raw_root = _resolved(IDS_METADATA_RAW_ROOT)
    resolved = _resolved(path)
    if resolved == raw_root or _is_relative_to(resolved, raw_root):
        return "IDS_MetaData raw metadata content is outside the Stage 018 Phase 2 read scope."
    return None


def _cost_class(count: int) -> str:
    if count <= 0:
        return "none"
    if count <= 10:
        return "low"
    if count <= 100:
        return "medium"
    return "high"


def _storage_pressure(total_size: int) -> str:
    if total_size <= 0:
        return "none"
    if total_size < 100 * 1024 * 1024:
        return "low"
    if total_size < 5 * 1024 * 1024 * 1024:
        return "medium"
    return "high"


def _record_for_file(path: Path) -> dict[str, Any]:
    stat = path.stat()
    extension = path.suffix.lower() or "NO_EXTENSION"
    return {
        "source_uri": path.as_uri(),
        "source_path": str(path),
        "basename": path.name,
        "extension": extension,
        "file_size": stat.st_size,
        "mtime": (
            datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z")
        ),
        "archive_candidate": extension in ARCHIVE_EXTENSIONS,
        "scanned_document_candidate": extension in SCANNED_HINT_EXTENSIONS,
        "embedding_candidate": extension in EMBEDDING_HINT_EXTENSIONS and extension not in ARCHIVE_EXTENSIONS,
        "unsupported_format": extension == "NO_EXTENSION" or extension not in SUPPORTED_EXTENSIONS,
    }


def _candidate_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    if path.is_dir():
        return sorted(item for item in path.iterdir() if item.is_file())
    return []


def _source_records_for_uri(source_uri: str | None) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    state, path, reason = _parse_source_uri(source_uri)
    if state is not None:
        return [], {"source_uri": source_uri, "state": state, "reason": reason}
    assert path is not None
    block_reason = _raw_metadata_block_reason(path)
    if block_reason is not None:
        return [], {"source_uri": source_uri, "state": "PREFLIGHT_SOURCE_BLOCKED", "reason": block_reason}
    try:
        if not path.exists():
            return [], {"source_uri": source_uri, "state": "PREFLIGHT_SOURCE_BLOCKED", "reason": "source path is absent."}
        if not (path.is_file() or path.is_dir()):
            return [], {"source_uri": source_uri, "state": "PREFLIGHT_SOURCE_BLOCKED", "reason": "source path must be a file or directory."}
        if not os.access(path, os.R_OK):
            return [], {"source_uri": source_uri, "state": "PREFLIGHT_SOURCE_BLOCKED", "reason": "source path is not readable."}
        records = [_record_for_file(candidate) for candidate in _candidate_files(path)]
    except OSError as exc:
        return [], {
            "source_uri": source_uri,
            "state": "PREFLIGHT_SOURCE_BLOCKED",
            "reason": f"Unable to read source metadata: {exc.__class__.__name__}",
        }
    return records, None


def _state_from_risks(risks: list[str], rejected_inputs: list[dict[str, Any]]) -> str:
    rejected_states = {item["state"] for item in rejected_inputs}
    if "PREFLIGHT_DRIVE_OFFLINE" in rejected_states:
        return "PREFLIGHT_DRIVE_OFFLINE"
    if "PREFLIGHT_SOURCE_BLOCKED" in rejected_states:
        return "PREFLIGHT_SOURCE_BLOCKED"
    if "PREFLIGHT_NOT_CONFIGURED" in rejected_states:
        return "PREFLIGHT_NOT_CONFIGURED"
    if risks:
        return "PREFLIGHT_REVIEW_REQUIRED"
    return "PREFLIGHT_READY"


def _priority_hint(overall_state: str, risks: list[str]) -> str:
    if overall_state in {"PREFLIGHT_SOURCE_BLOCKED", "PREFLIGHT_NOT_CONFIGURED", "PREFLIGHT_DRIVE_OFFLINE"}:
        return "blocked"
    if "PREFLIGHT_LARGE_BATCH" in risks:
        return "small_batch_first"
    if risks:
        return "manual_review_first"
    return "low_risk_first"


def evaluate_import_preflight(
    *,
    source_uris: list[str | None] | tuple[str | None, ...] | None,
    prechecked_at: str | None = None,
    drive_state: str = "online",
    available_space_bytes: int | None = None,
) -> dict[str, Any]:
    """Build Stage 018 preflight estimates from bounded filesystem metadata only."""

    prechecked_at = prechecked_at or _utc_now()
    normalized_drive_state = (drive_state or "unknown").strip().lower()
    if normalized_drive_state in OFFLINE_DRIVE_STATES:
        report = _base_report(
            prechecked_at=prechecked_at,
            drive_state=normalized_drive_state,
            records=[],
            source_root_count=0,
            rejected_inputs=[
                {
                    "source_uri": source_uris[0] if source_uris else None,
                    "state": "PREFLIGHT_DRIVE_OFFLINE",
                    "reason": "source drive is offline; preflight must fail closed before source metadata evaluation.",
                }
            ],
            available_space_bytes=available_space_bytes,
        )
        return report

    records: list[dict[str, Any]] = []
    rejected_inputs: list[dict[str, Any]] = []
    source_root_count = 0
    for source_uri in source_uris or []:
        source_records, rejected = _source_records_for_uri(source_uri)
        records.extend(source_records)
        if rejected is not None:
            rejected_inputs.append(rejected)
        else:
            source_root_count += 1
    if not source_uris:
        rejected_inputs.append(
            {"source_uri": None, "state": "PREFLIGHT_NOT_CONFIGURED", "reason": "source_uri is required."}
        )
    return _base_report(
        prechecked_at=prechecked_at,
        drive_state=normalized_drive_state,
        records=records,
        source_root_count=source_root_count,
        rejected_inputs=rejected_inputs,
        available_space_bytes=available_space_bytes,
    )


def _base_report(
    *,
    prechecked_at: str,
    drive_state: str,
    records: list[dict[str, Any]],
    source_root_count: int,
    rejected_inputs: list[dict[str, Any]],
    available_space_bytes: int | None,
) -> dict[str, Any]:
    format_counts: dict[str, int] = {}
    for record in records:
        format_counts[record["extension"]] = format_counts.get(record["extension"], 0) + 1
    total_size = sum(record["file_size"] for record in records)
    archive_count = sum(1 for record in records if record["archive_candidate"])
    scanned_count = sum(1 for record in records if record["scanned_document_candidate"])
    embedding_count = sum(1 for record in records if record["embedding_candidate"])
    unsupported_count = sum(1 for record in records if record["unsupported_format"])
    risks: list[str] = []
    if archive_count:
        risks.append("PREFLIGHT_ARCHIVE_PRESENT")
    if scanned_count:
        risks.append("PREFLIGHT_SCANNED_DOCUMENT_PRESENT")
    if len(records) > 100:
        risks.append("PREFLIGHT_LARGE_BATCH")
    if unsupported_count:
        risks.append("PREFLIGHT_UNSUPPORTED_FORMAT")
    if available_space_bytes is not None and total_size > available_space_bytes:
        risks.append("PREFLIGHT_INSUFFICIENT_SPACE")
    overall_state = _state_from_risks(risks, rejected_inputs)
    cost_items = {
        "local_scan_time_class": _cost_class(len(records)),
        "storage_pressure_class": _storage_pressure(total_size),
        "ocr_workload_class": _cost_class(scanned_count),
        "embedding_workload_class": _cost_class(embedding_count),
        "operator_review_class": _cost_class(len(risks) + len(rejected_inputs)),
        "batch_split_hint": "split_required" if "PREFLIGHT_LARGE_BATCH" in risks else "not_required",
    }
    report: dict[str, Any] = {
        "schema_version": "ids.stage018.import_preflight.v1",
        "stage": "STAGE-018",
        "phase": "Phase 2",
        "acceptance_id": "ACC-STAGE-018",
        "entrance": ENTRANCE,
        "customer_visible": True,
        "overall_state": overall_state,
        "safe_mode": overall_state != "PREFLIGHT_READY",
        "prechecked_at": prechecked_at,
        "drive_state": drive_state,
        "precheck_mode": "dry_run_metadata_only",
        "confirmation_required": True,
        "confirmation_status": overall_state,
        "source_root_count": source_root_count,
        "file_records": records,
        "file_count_estimate": len(records),
        "total_size_bytes_estimate": total_size,
        "format_counts": dict(sorted(format_counts.items())),
        "archive_candidate_count": archive_count,
        "scanned_document_candidate_count": scanned_count,
        "estimated_ocr_units": scanned_count,
        "estimated_embedding_units": embedding_count,
        "unsupported_format_count": unsupported_count,
        "risk_items": risks,
        "cost_items": cost_items,
        "priority_hint": _priority_hint(overall_state, risks),
        "rejected_inputs": rejected_inputs,
        "rejected_input_count": len(rejected_inputs),
        "error_count": len(rejected_inputs),
        "document_delta": 0,
        "chunk_delta": 0,
        "job_delta": 0,
        "index_delta": 0,
        "import_write_delta": 0,
        "manifest_write_delta": 0,
        "evidence_write_delta": 0,
        "audit_write_delta": 0,
        "report_write_delta": 0,
        "database_write_delta": 0,
    }
    report.update(NO_SIDE_EFFECT_FLAGS)
    return report


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a metadata-only Stage 018 import preflight report.")
    parser.add_argument(
        "--source-uri",
        action="append",
        dest="source_uris",
        help="Explicit file:// source root or file URI. Repeat for multiple approved roots.",
    )
    parser.add_argument("--prechecked-at", help="UTC preflight timestamp for deterministic runs.")
    parser.add_argument("--drive-state", default="online", help="online, offline, disconnected, missing, or unavailable.")
    parser.add_argument("--available-space-bytes", type=int, help="Optional future target-space estimate.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    report = evaluate_import_preflight(
        source_uris=args.source_uris,
        prechecked_at=args.prechecked_at,
        drive_state=args.drive_state,
        available_space_bytes=args.available_space_bytes,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
