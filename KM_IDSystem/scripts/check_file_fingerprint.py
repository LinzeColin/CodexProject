#!/usr/bin/env python3
"""Read-only Stage 013 file-fingerprint preflight for IDS operations."""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse


OPERATIONS_ENTRANCE = "IDS 系统运营入口"
IDS_METADATA_RAW_ROOT = Path("/Users/linzezhang/Downloads/IDS_MetaData")
OK_STATES = {"FINGERPRINT_READY", "FINGERPRINT_DUPLICATE_CONTENT"}
STATE_ORDER = [
    "FINGERPRINT_NOT_CONFIGURED",
    "FINGERPRINT_PATH_BLOCKED",
    "FINGERPRINT_READ_BLOCKED",
    "FINGERPRINT_HASH_CONFLICT",
    "FINGERPRINT_MIME_UNKNOWN",
    "FINGERPRINT_MIME_CONFLICT",
    "FINGERPRINT_MANIFEST_UNSAFE",
    "FINGERPRINT_UNKNOWN",
]

mimetypes.add_type("text/markdown", ".md", strict=True)
mimetypes.add_type("text/markdown", ".md", strict=False)


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
        return "FINGERPRINT_NOT_CONFIGURED", None, "source_uri is required."
    parsed = urlparse(source_uri.strip())
    if parsed.scheme != "file":
        return "FINGERPRINT_PATH_BLOCKED", None, "source_uri must use the file:// scheme."
    if parsed.netloc not in {"", "localhost"}:
        return "FINGERPRINT_PATH_BLOCKED", None, "source_uri must point to a local file path."
    if not parsed.path:
        return "FINGERPRINT_PATH_BLOCKED", None, "source_uri path is missing."
    path = Path(unquote(parsed.path)).expanduser()
    if not path.is_absolute():
        return "FINGERPRINT_PATH_BLOCKED", None, "source_uri must normalize to an absolute path."
    return None, _resolved(path), None


def _block_reason(path: Path) -> str | None:
    raw_root = _resolved(IDS_METADATA_RAW_ROOT)
    resolved = _resolved(path)
    if resolved == raw_root or _is_relative_to(resolved, raw_root):
        return "IDS_MetaData raw metadata content is outside the Stage 013 Phase 2 read scope."
    return None


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _guess_mime(path: Path) -> str:
    return mimetypes.guess_type(path.name)[0] or "UNKNOWN"


def _record_for_source(source_uri: str | None, first_seen_at: str) -> dict[str, Any]:
    state, path, reason = _parse_source_uri(source_uri)
    base: dict[str, Any] = {"source_uri": source_uri, "state": state or "FINGERPRINT_UNKNOWN"}
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
            "state": "FINGERPRINT_PATH_BLOCKED",
            "reason": block_reason,
        }
    try:
        if not path.exists():
            return {
                **base,
                "state": "FINGERPRINT_PATH_BLOCKED",
                "reason": "source path is absent.",
            }
        if not path.is_file():
            return {
                **base,
                "state": "FINGERPRINT_PATH_BLOCKED",
                "reason": "source path must be an explicit file, not a directory.",
            }
        if not os.access(path, os.R_OK):
            return {
                **base,
                "state": "FINGERPRINT_READ_BLOCKED",
                "reason": "source path is not readable.",
            }
        size = path.stat().st_size
        sha256 = _hash_file(path)
    except OSError as exc:
        return {
            **base,
            "state": "FINGERPRINT_READ_BLOCKED",
            "reason": f"Unable to read source fingerprint: {exc.__class__.__name__}",
        }

    return {
        **base,
        "state": "FINGERPRINT_READY",
        "reason": "file fingerprint observed with read-only metadata capture.",
        "source_uri": path.as_uri(),
        "source_path": str(path),
        "sha256": sha256,
        "size": size,
        "file_size": size,
        "mtime": _mtime_utc(path),
        "extension": path.suffix.lower(),
        "mime": _guess_mime(path),
        "first_seen_at": first_seen_at,
    }


def _overall_state(records: list[dict[str, Any]]) -> str:
    if not records:
        return "FINGERPRINT_NOT_CONFIGURED"
    states = [record["state"] for record in records]
    failures = [state for state in states if state not in OK_STATES]
    if not failures:
        return "FINGERPRINT_READY"
    for preferred in STATE_ORDER:
        if preferred in failures:
            return preferred
    return failures[0]


def evaluate_file_fingerprints(
    *,
    source_uris: list[str | None] | tuple[str | None, ...] | None,
    first_seen_at: str | None = None,
) -> dict[str, Any]:
    """Build metadata-only file fingerprint records without writing persistence."""

    first_seen_at = first_seen_at or _utc_now()
    records: list[dict[str, Any]] = []
    seen_keys: set[tuple[str | None, str | None]] = set()
    duplicate_input_count = 0

    for source_uri in source_uris or []:
        record = _record_for_source(source_uri, first_seen_at)
        key = (record.get("source_path"), record.get("sha256"))
        if record["state"] == "FINGERPRINT_READY" and key in seen_keys:
            duplicate_input_count += 1
            continue
        if record["state"] == "FINGERPRINT_READY":
            seen_keys.add(key)
        records.append(record)

    overall_state = _overall_state(records)
    manifest_records = [record for record in records if record["state"] == "FINGERPRINT_READY"]

    return {
        "schema_version": "ids.stage013.file_fingerprint.v1",
        "stage": "STAGE-013",
        "phase": "Phase 2",
        "acceptance_id": "ACC-STAGE-013",
        "entrance": OPERATIONS_ENTRANCE,
        "customer_visible": False,
        "overall_state": overall_state,
        "safe_mode": overall_state != "FINGERPRINT_READY",
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


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a metadata-only Stage 013 file-fingerprint report."
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
    report = evaluate_file_fingerprints(
        source_uris=args.source_uris,
        first_seen_at=args.first_seen_at,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
