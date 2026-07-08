#!/usr/bin/env python3
"""Generate and audit Memory Atlas public raw manifest/hash ledgers."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


PUBLIC_RAW_ROOT = Path("data/public_raw")
MANIFEST_ROOT = Path("机器治理/证据与日志/raw_archive_manifests")
HASH_LEDGER_FILE = "raw_hash_ledger.jsonl"
IGNORED_RAW_NAMES = {".DS_Store", ".gitkeep", "README.md"}


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_text_atomic(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        tmp_path.write_text(payload, encoding="utf-8")
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    payload = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows)
    write_text_atomic(path, payload)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            text = line.strip()
            if not text:
                continue
            try:
                row = json.loads(text)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSONL in {path}:{line_number}: {exc}") from exc
            if not isinstance(row, dict):
                raise ValueError(f"invalid JSONL row in {path}:{line_number}: expected object")
            rows.append(row)
    return rows


def should_include_raw_file(path: Path, raw_root: Path) -> bool:
    if not path.is_file() or path.name in IGNORED_RAW_NAMES:
        return False
    try:
        relative = path.relative_to(raw_root)
    except ValueError:
        return False
    return not any(part.startswith(".") for part in relative.parts)


def iter_public_raw_files(database_dir: Path) -> list[Path]:
    raw_root = database_dir / PUBLIC_RAW_ROOT
    if not raw_root.exists():
        return []
    return sorted(path for path in raw_root.rglob("*") if should_include_raw_file(path, raw_root))


def source_id_for(relative_path: Path) -> str:
    parts = relative_path.parts
    if not parts:
        return "unknown"
    if parts[0] in {"chatgpt", "codex"}:
        return parts[0]
    if parts[0] == "agents" and len(parts) >= 2:
        return f"agent:{parts[1]}"
    return parts[0]


def build_manifest_rows(database_dir: Path, imported_at: str) -> list[dict[str, Any]]:
    raw_root = database_dir / PUBLIC_RAW_ROOT
    rows: list[dict[str, Any]] = []
    for file_path in iter_public_raw_files(database_dir):
        relative_path = file_path.relative_to(raw_root)
        rows.append(
            {
                "source_id": source_id_for(relative_path),
                "relative_path": relative_path.as_posix(),
                "sha256": sha256_file(file_path),
                "imported_at": imported_at,
                "size_bytes": file_path.stat().st_size,
            }
        )
    return rows


def manifest_path_for(database_dir: Path, run_id: str) -> Path:
    safe_run_id = "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in run_id.strip())
    if not safe_run_id:
        raise ValueError("run_id must not be empty")
    return database_dir / MANIFEST_ROOT / f"raw_manifest.{safe_run_id}.jsonl"


def hash_ledger_path(database_dir: Path) -> Path:
    return database_dir / MANIFEST_ROOT / HASH_LEDGER_FILE


def generate_raw_manifest(database_dir: Path, run_id: str, imported_at: str | None = None) -> dict[str, Any]:
    database_dir = database_dir.resolve()
    imported_at = imported_at or now_utc()
    rows = build_manifest_rows(database_dir, imported_at)
    manifest_path = manifest_path_for(database_dir, run_id)
    ledger_path = hash_ledger_path(database_dir)
    write_jsonl(manifest_path, rows)
    write_jsonl(ledger_path, rows)
    return {
        "status": "PASS",
        "schema_version": "memory_atlas_raw_manifest.v1",
        "run_id": run_id,
        "generated_at": now_utc(),
        "imported_at": imported_at,
        "raw_root": PUBLIC_RAW_ROOT.as_posix(),
        "manifest_path": manifest_path.relative_to(database_dir).as_posix(),
        "hash_ledger_path": ledger_path.relative_to(database_dir).as_posix(),
        "raw_file_count": len(rows),
    }


def audit_raw_append_only(database_dir: Path) -> dict[str, Any]:
    database_dir = database_dir.resolve()
    ledger_path = hash_ledger_path(database_dir)
    ledger_rows = read_jsonl(ledger_path)
    current_rows = build_manifest_rows(database_dir, imported_at=now_utc())
    ledger_by_path = {str(row.get("relative_path") or ""): row for row in ledger_rows}
    current_by_path = {str(row.get("relative_path") or ""): row for row in current_rows}

    deleted = sorted(path for path in ledger_by_path if path and path not in current_by_path)
    changed = sorted(
        path
        for path, row in ledger_by_path.items()
        if path in current_by_path and str(row.get("sha256")) != str(current_by_path[path].get("sha256"))
    )
    added = sorted(path for path in current_by_path if path and path not in ledger_by_path)
    status = "PASS" if not deleted and not changed else "FAIL"
    return {
        "status": status,
        "schema_version": "memory_atlas_raw_append_only_audit.v1",
        "raw_root": PUBLIC_RAW_ROOT.as_posix(),
        "hash_ledger_path": ledger_path.relative_to(database_dir).as_posix(),
        "ledger_entry_count": len(ledger_rows),
        "current_raw_file_count": len(current_rows),
        "new_raw_file_count": len(added),
        "hash_drift_count": len(changed),
        "deleted_manifest_entry_count": len(deleted),
        "new_raw_files": added,
        "hash_drift_files": changed,
        "deleted_manifest_entries": deleted,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate = subparsers.add_parser("generate", help="generate raw manifest and hash ledger")
    generate.add_argument("--database-dir", default=".", help="OpenAIDatabase root")
    generate.add_argument("--run-id", required=True, help="manifest run id")
    generate.add_argument("--imported-at", default=None, help="stable imported_at timestamp")

    audit = subparsers.add_parser("audit", help="audit raw append-only/hash drift rules")
    audit.add_argument("--database-dir", default=".", help="OpenAIDatabase root")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "generate":
        result = generate_raw_manifest(Path(args.database_dir), args.run_id, args.imported_at)
    elif args.command == "audit":
        result = audit_raw_append_only(Path(args.database_dir))
    else:
        raise AssertionError(f"unhandled command: {args.command}")

    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
