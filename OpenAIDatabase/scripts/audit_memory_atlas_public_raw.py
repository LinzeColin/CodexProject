#!/usr/bin/env python3
"""Audit every Memory Atlas public-raw JSON value without Git or size skips."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterator

from public_raw_sanitizer import (
    MAX_PUBLIC_RAW_FILE_BYTES,
    is_non_text_binary_string,
    sanitize_public_text,
)
from raw_archive_manifest import PUBLIC_RAW_ROOT, iter_public_raw_files


BINARY_MARKER_RE = re.compile(
    r"\[REDACTED_BINARY sha256=[0-9a-f]{64} bytes=[0-9]+ "
    r"reason=non_text_binary_not_transcript\]\Z"
)


def iter_json_values(value: Any) -> Iterator[str]:
    if isinstance(value, str):
        yield value
        return
    if isinstance(value, list):
        for item in value:
            yield from iter_json_values(item)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from iter_json_values(item)


def iter_structured_rows(path: Path) -> Iterator[Any]:
    if path.suffix == ".jsonl":
        with path.open("r", encoding="utf-8", errors="strict") as handle:
            for line_number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"invalid JSONL row {line_number}") from exc
        return
    if path.suffix == ".json":
        with path.open("r", encoding="utf-8", errors="strict") as handle:
            try:
                yield json.load(handle)
            except json.JSONDecodeError as exc:
                raise ValueError("invalid JSON document") from exc
        return
    raise ValueError("unsupported public-raw file extension")


def audit_public_raw(
    database_dir: Path,
    max_file_bytes: int = MAX_PUBLIC_RAW_FILE_BYTES,
) -> dict[str, Any]:
    database_dir = database_dir.resolve()
    raw_root = database_dir / PUBLIC_RAW_ROOT
    files = iter_public_raw_files(database_dir)
    violations: list[dict[str, Any]] = []
    total_bytes = 0
    binary_marker_count = 0
    private_text_files: set[str] = set()
    unmarked_binary_files: set[str] = set()
    invalid_marker_files: set[str] = set()
    invalid_json_files: set[str] = set()
    oversize_files: set[str] = set()

    for path in files:
        relative_path = path.relative_to(raw_root).as_posix()
        size_bytes = path.stat().st_size
        total_bytes += size_bytes
        if size_bytes > max_file_bytes:
            oversize_files.add(relative_path)
            violations.append(
                {
                    "relative_path": relative_path,
                    "violation": "file_size_limit_exceeded",
                    "size_bytes": size_bytes,
                    "max_file_bytes": max_file_bytes,
                }
            )
            continue

        file_categories: set[str] = set()
        file_has_unmarked_binary = False
        file_has_invalid_marker = False
        try:
            for row in iter_structured_rows(path):
                for value in iter_json_values(row):
                    if BINARY_MARKER_RE.fullmatch(value):
                        binary_marker_count += 1
                        continue
                    if value.startswith("[REDACTED_BINARY"):
                        file_has_invalid_marker = True
                        continue
                    if is_non_text_binary_string(value):
                        file_has_unmarked_binary = True
                        continue
                    _, counts = sanitize_public_text(value)
                    file_categories.update(counts)
        except (UnicodeError, ValueError, OSError):
            invalid_json_files.add(relative_path)
            violations.append(
                {
                    "relative_path": relative_path,
                    "violation": "invalid_public_raw_json",
                }
            )
            continue

        if file_categories:
            private_text_files.add(relative_path)
            violations.append(
                {
                    "relative_path": relative_path,
                    "violation": "credential_or_private_text",
                    "categories": sorted(file_categories),
                }
            )
        if file_has_unmarked_binary:
            unmarked_binary_files.add(relative_path)
            violations.append(
                {
                    "relative_path": relative_path,
                    "violation": "unmarked_binary_or_data_url",
                }
            )
        if file_has_invalid_marker:
            invalid_marker_files.add(relative_path)
            violations.append(
                {
                    "relative_path": relative_path,
                    "violation": "invalid_binary_marker",
                }
            )

    status = "PASS" if not violations else "FAIL"
    return {
        "status": status,
        "schema_version": "memory_atlas_public_raw_audit.v1",
        "raw_root": PUBLIC_RAW_ROOT.as_posix(),
        "file_count": len(files),
        "total_bytes": total_bytes,
        "max_file_bytes": max_file_bytes,
        "credential_or_private_text_file_count": len(private_text_files),
        "unmarked_binary_file_count": len(unmarked_binary_files),
        "invalid_binary_marker_file_count": len(invalid_marker_files),
        "invalid_json_file_count": len(invalid_json_files),
        "oversize_file_count": len(oversize_files),
        "binary_marker_count": binary_marker_count,
        "violations": violations,
        "audit_scope": "all_public_raw_files_independent_of_git_tracking",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-dir", type=Path, default=Path("."))
    parser.add_argument("--max-file-bytes", type=int, default=MAX_PUBLIC_RAW_FILE_BYTES)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = audit_public_raw(args.database_dir, args.max_file_bytes)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
