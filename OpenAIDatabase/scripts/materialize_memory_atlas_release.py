#!/usr/bin/env python3
"""Create and verify immutable Memory Atlas v1.2 release snapshots."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RELEASE_ROOT = Path("data/releases/memory_atlas/v1_2")
CURRENT_RELEASE_POINTER = Path("机器治理/发布快照/memory_atlas_current_release.json")
SOURCE_PACKAGE_MANIFEST = Path("docs/source_packages/memory_atlas_v1_2/SOURCE_MANIFEST.json")
DERIVED_SNAPSHOT = Path("data/derived/visualization/memory_atlas.json")
RELEASE_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


class ReleaseError(RuntimeError):
    pass


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ReleaseError(f"missing {label}") from exc
    except json.JSONDecodeError as exc:
        raise ReleaseError(f"invalid JSON in {label}") from exc
    if not isinstance(payload, dict):
        raise ReleaseError(f"{label} must be a JSON object")
    return payload


def json_text(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        temporary.write_text(json_text(payload), encoding="utf-8")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def validate_release_id(release_id: str) -> str:
    normalized = release_id.strip()
    if not RELEASE_ID_PATTERN.fullmatch(normalized):
        raise ReleaseError("release_id must use only letters, digits, dot, underscore, or hyphen")
    return normalized


def repository_file(database_dir: Path, path: Path, label: str) -> tuple[Path, str]:
    candidate = path.expanduser()
    if not candidate.is_absolute():
        candidate = database_dir / candidate
    resolved = candidate.resolve()
    try:
        relative = resolved.relative_to(database_dir)
    except ValueError as exc:
        raise ReleaseError(f"{label} must be inside the repository") from exc
    if not resolved.is_file():
        raise ReleaseError(f"missing {label}")
    return resolved, relative.as_posix()


def safe_relative_path(value: Any, label: str) -> Path:
    if not isinstance(value, str) or not value:
        raise ReleaseError(f"{label} must be repository-relative")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ReleaseError(f"{label} must be repository-relative")
    return path


def ensure_repository_path(database_dir: Path, path: Path, label: str) -> Path:
    try:
        path.resolve().relative_to(database_dir)
    except ValueError as exc:
        raise ReleaseError(f"{label} resolves outside repository") from exc
    return path


def snapshot_counts(snapshot: dict[str, Any]) -> dict[str, int]:
    overview = snapshot.get("overview")
    if not isinstance(overview, dict):
        raise ReleaseError("snapshot overview is missing")
    counts = {
        key: value
        for key, value in sorted(overview.items())
        if key.endswith("_count") and isinstance(value, int) and not isinstance(value, bool)
    }
    if not counts:
        raise ReleaseError("snapshot overview contains no integer counts")
    return counts


def source_package_records(database_dir: Path) -> dict[str, Any]:
    manifest_path, manifest_relative = repository_file(
        database_dir,
        SOURCE_PACKAGE_MANIFEST,
        "source package manifest",
    )
    payload = load_json_object(manifest_path, "source package manifest")
    rows = payload.get("files")
    if not isinstance(rows, list) or not rows:
        raise ReleaseError("source package manifest contains no files")

    package_root = manifest_path.parent
    files: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            raise ReleaseError("source package manifest contains an invalid file row")
        storage_path = safe_relative_path(row.get("storage_name"), "source package storage_name")
        candidate = (package_root / storage_path).resolve()
        try:
            relative = candidate.relative_to(database_dir)
            candidate.relative_to(package_root)
        except ValueError as exc:
            raise ReleaseError("source package file must stay inside its package directory") from exc
        if not candidate.is_file():
            raise ReleaseError("source package file is missing")
        actual_hash = sha256_file(candidate)
        actual_size = candidate.stat().st_size
        if row.get("sha256") != actual_hash or row.get("size") != actual_size:
            raise ReleaseError("source package hash or size does not match its manifest")
        files.append(
            {
                "original_name": str(row.get("original_name") or storage_path.name),
                "relative_path": relative.as_posix(),
                "sha256": actual_hash,
                "size_bytes": actual_size,
                "verified": True,
            }
        )
    return {
        "manifest_path": manifest_relative,
        "manifest_sha256": sha256_file(manifest_path),
        "manifest_size_bytes": manifest_path.stat().st_size,
        "files": files,
    }


def build_release_manifest(
    database_dir: Path,
    release_id: str,
    release_snapshot_relative: str,
    snapshot_path: Path,
    raw_manifest_path: Path,
    raw_manifest_relative: str,
) -> dict[str, Any]:
    snapshot = load_json_object(snapshot_path, "snapshot")
    return {
        "schema_version": "memory_atlas.release_manifest.v1",
        "release_id": release_id,
        "created_at": now_utc(),
        "snapshot": {
            "relative_path": release_snapshot_relative,
            "sha256": sha256_file(snapshot_path),
            "size_bytes": snapshot_path.stat().st_size,
            "counts": snapshot_counts(snapshot),
        },
        "raw_manifest": {
            "relative_path": raw_manifest_relative,
            "sha256": sha256_file(raw_manifest_path),
            "size_bytes": raw_manifest_path.stat().st_size,
        },
        "source_packages": source_package_records(database_dir),
    }


def immutable_inputs_match(existing: dict[str, Any], candidate: dict[str, Any]) -> bool:
    if set(existing) != set(candidate) or not isinstance(existing.get("created_at"), str):
        return False
    normalized_candidate = dict(candidate)
    normalized_candidate["created_at"] = existing["created_at"]
    return existing == normalized_candidate


def materialize_release(
    database_dir: Path,
    release_id: str,
    snapshot_path: Path,
    raw_manifest_path: Path,
) -> dict[str, Any]:
    database_dir = database_dir.expanduser().resolve()
    release_id = validate_release_id(release_id)
    snapshot_path, _snapshot_source_relative = repository_file(database_dir, snapshot_path, "snapshot")
    raw_manifest_path, raw_manifest_relative = repository_file(database_dir, raw_manifest_path, "raw manifest")

    release_dir_relative = RELEASE_ROOT / release_id
    release_dir = database_dir / release_dir_relative
    release_snapshot = release_dir / "memory_atlas.json"
    release_manifest_path = release_dir / "release_manifest.json"
    ensure_repository_path(database_dir, release_dir, "release directory")
    ensure_repository_path(database_dir, release_snapshot, "release snapshot path")
    ensure_repository_path(database_dir, release_manifest_path, "release_manifest_path")
    release_snapshot_relative = (release_dir_relative / "memory_atlas.json").as_posix()
    release_manifest_relative = (release_dir_relative / "release_manifest.json").as_posix()
    candidate_manifest = build_release_manifest(
        database_dir,
        release_id,
        release_snapshot_relative,
        snapshot_path,
        raw_manifest_path,
        raw_manifest_relative,
    )

    created = False
    if release_dir.exists():
        if not release_snapshot.is_file() or not release_manifest_path.is_file():
            raise ReleaseError("release ID already exists but is incomplete")
        existing_manifest = load_json_object(release_manifest_path, "release manifest")
        if release_manifest_path.read_text(encoding="utf-8") != json_text(existing_manifest):
            raise ReleaseError("release ID already exists with changed manifest bytes")
        if sha256_file(release_snapshot) != candidate_manifest["snapshot"]["sha256"]:
            raise ReleaseError("release ID already exists with different snapshot bytes")
        if not immutable_inputs_match(existing_manifest, candidate_manifest):
            raise ReleaseError("release ID already exists with different immutable inputs")
    else:
        release_dir.mkdir(parents=True, exist_ok=False)
        temporary_snapshot = release_dir / f".memory_atlas.json.{os.getpid()}.tmp"
        try:
            shutil.copyfile(snapshot_path, temporary_snapshot)
            os.replace(temporary_snapshot, release_snapshot)
            write_json_atomic(release_manifest_path, candidate_manifest)
        except Exception:
            temporary_snapshot.unlink(missing_ok=True)
            release_manifest_path.unlink(missing_ok=True)
            release_snapshot.unlink(missing_ok=True)
            if release_dir.exists() and not any(release_dir.iterdir()):
                release_dir.rmdir()
            raise
        created = True

    manifest = load_json_object(release_manifest_path, "release manifest")
    release_manifest_sha256 = sha256_file(release_manifest_path)
    pointer = {
        "schema_version": "memory_atlas.current_release.v1",
        "release_id": release_id,
        "release_manifest_path": release_manifest_relative,
        "release_manifest_sha256": release_manifest_sha256,
        "snapshot_path": release_snapshot_relative,
        "snapshot_sha256": manifest["snapshot"]["sha256"],
        "updated_at": now_utc(),
    }
    pointer_path = ensure_repository_path(
        database_dir,
        database_dir / CURRENT_RELEASE_POINTER,
        "current release pointer",
    )
    write_json_atomic(pointer_path, pointer)
    return {
        "status": "PASS",
        "release_id": release_id,
        "created": created,
        "release_manifest_path": release_manifest_relative,
        "release_manifest_sha256": release_manifest_sha256,
        "snapshot_path": release_snapshot_relative,
        "snapshot_sha256": manifest["snapshot"]["sha256"],
        "counts": manifest["snapshot"]["counts"],
    }


def validate_relative_manifest_paths(value: Any, errors: list[str]) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if key.endswith("_path"):
                try:
                    safe_relative_path(nested, key)
                except ReleaseError:
                    errors.append(f"{key} must be repository-relative")
            validate_relative_manifest_paths(nested, errors)
    elif isinstance(value, list):
        for nested in value:
            validate_relative_manifest_paths(nested, errors)


def verify_current_release(database_dir: Path) -> dict[str, Any]:
    database_dir = database_dir.expanduser().resolve()
    errors: list[str] = []
    try:
        pointer_path = ensure_repository_path(
            database_dir,
            database_dir / CURRENT_RELEASE_POINTER,
            "current release pointer",
        )
        pointer = load_json_object(pointer_path, "current release pointer")
        if pointer.get("schema_version") != "memory_atlas.current_release.v1":
            errors.append("current release pointer schema_version is invalid")
        release_id = validate_release_id(str(pointer.get("release_id") or ""))
        manifest_relative = safe_relative_path(pointer.get("release_manifest_path"), "release_manifest_path")
        snapshot_relative = safe_relative_path(pointer.get("snapshot_path"), "snapshot_path")
        expected_manifest = RELEASE_ROOT / release_id / "release_manifest.json"
        expected_snapshot = RELEASE_ROOT / release_id / "memory_atlas.json"
        if manifest_relative != expected_manifest:
            errors.append("release_manifest_path does not match release_id")
        if snapshot_relative != expected_snapshot:
            errors.append("snapshot_path does not match release_id")

        manifest_path = ensure_repository_path(
            database_dir,
            database_dir / manifest_relative,
            "release_manifest_path",
        )
        release_snapshot = ensure_repository_path(
            database_dir,
            database_dir / snapshot_relative,
            "snapshot_path",
        )
        manifest = load_json_object(manifest_path, "release manifest")
        if pointer.get("release_manifest_sha256") != sha256_file(manifest_path):
            errors.append("release manifest hash mismatch")
        validate_relative_manifest_paths(manifest, errors)
        if manifest.get("schema_version") != "memory_atlas.release_manifest.v1":
            errors.append("release manifest schema_version is invalid")
        if manifest.get("release_id") != release_id:
            errors.append("release manifest release_id mismatch")

        snapshot_record = manifest.get("snapshot")
        if not isinstance(snapshot_record, dict):
            raise ReleaseError("release manifest snapshot record is invalid")
        if snapshot_record.get("relative_path") != snapshot_relative.as_posix():
            errors.append("release manifest snapshot path mismatch")
        if not release_snapshot.is_file():
            errors.append("immutable release snapshot is missing")
        else:
            actual_snapshot_hash = sha256_file(release_snapshot)
            if snapshot_record.get("sha256") != actual_snapshot_hash:
                errors.append("immutable release snapshot hash mismatch")
            if snapshot_record.get("size_bytes") != release_snapshot.stat().st_size:
                errors.append("immutable release snapshot size mismatch")
            actual_counts = snapshot_counts(load_json_object(release_snapshot, "immutable release snapshot"))
            if snapshot_record.get("counts") != actual_counts:
                errors.append("immutable release snapshot counts mismatch")
            if pointer.get("snapshot_sha256") != actual_snapshot_hash:
                errors.append("current release pointer snapshot hash mismatch")

        raw_record = manifest.get("raw_manifest")
        if not isinstance(raw_record, dict):
            raise ReleaseError("release manifest raw manifest record is invalid")
        raw_relative = safe_relative_path(raw_record.get("relative_path"), "raw_manifest.relative_path")
        raw_path = ensure_repository_path(
            database_dir,
            database_dir / raw_relative,
            "raw_manifest.relative_path",
        )
        if not raw_path.is_file():
            errors.append("raw manifest is missing")
        else:
            if raw_record.get("sha256") != sha256_file(raw_path):
                errors.append("raw manifest hash mismatch")
            if raw_record.get("size_bytes") != raw_path.stat().st_size:
                errors.append("raw manifest size mismatch")

        current_sources = source_package_records(database_dir)
        if manifest.get("source_packages") != current_sources:
            errors.append("source package hashes do not match release manifest")
    except ReleaseError as exc:
        message = str(exc)
        if "must be repository-relative" in message:
            label = message.split(" must be", 1)[0]
            errors.append(f"{label} must be repository-relative")
        else:
            errors.append(message)

    errors = list(dict.fromkeys(errors))
    if errors:
        return {
            "status": "FAIL",
            "schema_version": "memory_atlas.release_verification.v1",
            "errors": errors,
        }
    return {
        "status": "PASS",
        "schema_version": "memory_atlas.release_verification.v1",
        "release_id": release_id,
        "release_manifest_path": manifest_relative.as_posix(),
        "release_manifest_sha256": sha256_file(manifest_path),
        "snapshot_path": snapshot_relative.as_posix(),
        "snapshot_sha256": manifest["snapshot"]["sha256"],
        "counts": manifest["snapshot"]["counts"],
        "raw_manifest_sha256": manifest["raw_manifest"]["sha256"],
        "source_package_hashes": [row["sha256"] for row in manifest["source_packages"]["files"]],
        "errors": [],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    materialize = subparsers.add_parser("materialize", help="create or idempotently select an immutable release")
    materialize.add_argument("--database-dir", type=Path, default=Path("."))
    materialize.add_argument("--release-id", required=True)
    materialize.add_argument("--snapshot", type=Path, default=DERIVED_SNAPSHOT)
    materialize.add_argument("--raw-manifest", type=Path, required=True)

    verify = subparsers.add_parser("verify", help="verify the current immutable release")
    verify.add_argument("--database-dir", type=Path, default=Path("."))
    verify.add_argument("--snapshot-path-only", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "materialize":
            result = materialize_release(args.database_dir, args.release_id, args.snapshot, args.raw_manifest)
        else:
            result = verify_current_release(args.database_dir)
    except ReleaseError as exc:
        result = {
            "status": "FAIL",
            "schema_version": "memory_atlas.release_verification.v1",
            "errors": [str(exc)],
        }

    if args.command == "verify" and args.snapshot_path_only and result["status"] == "PASS":
        print(result["snapshot_path"])
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
