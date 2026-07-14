#!/usr/bin/env python3
"""Audit exact snapshot-byte parity across all Memory Atlas release candidates."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from materialize_memory_atlas_release import DERIVED_SNAPSHOT, verify_current_release  # noqa: E402


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_snapshot_candidate(path: Path) -> Path:
    candidate = path.expanduser()
    if candidate.is_dir():
        return candidate / "memory_atlas.json"
    return candidate


def candidate_result(path: Path, expected_sha256: str) -> dict[str, Any]:
    candidate = resolve_snapshot_candidate(path)
    if not candidate.is_file():
        return {"status": "MISSING", "sha256": None, "size_bytes": None}
    try:
        actual_sha256 = sha256_file(candidate)
        size_bytes = candidate.stat().st_size
    except OSError:
        return {"status": "UNREADABLE", "sha256": None, "size_bytes": None}
    return {
        "status": "MATCH" if actual_sha256 == expected_sha256 else "MISMATCH",
        "sha256": actual_sha256,
        "size_bytes": size_bytes,
    }


def audit_snapshot_parity(
    database_dir: Path,
    local_runtime: Path,
    pages_candidate: Path,
) -> dict[str, Any]:
    database_dir = database_dir.expanduser().resolve()
    release = verify_current_release(database_dir)
    if release["status"] != "PASS":
        return {
            "status": "FAIL",
            "schema_version": "memory_atlas.snapshot_parity.v1",
            "release_verification": "FAIL",
            "errors": list(release.get("errors") or ["current release verification failed"]),
            "candidates": {},
            "missing_candidates": [],
            "mismatched_candidates": [],
        }

    expected_sha256 = str(release["snapshot_sha256"])
    paths = {
        "release": database_dir / release["snapshot_path"],
        "derived": database_dir / DERIVED_SNAPSHOT,
        "local_runtime": local_runtime,
        "pages": pages_candidate,
    }
    candidates = {
        role: candidate_result(path, expected_sha256)
        for role, path in paths.items()
    }
    missing = [
        role
        for role, result in candidates.items()
        if result["status"] in {"MISSING", "UNREADABLE"}
    ]
    mismatched = [
        role
        for role, result in candidates.items()
        if result["status"] == "MISMATCH"
    ]
    return {
        "status": "PASS" if not missing and not mismatched else "FAIL",
        "schema_version": "memory_atlas.snapshot_parity.v1",
        "release_verification": "PASS",
        "release_id": release["release_id"],
        "expected_sha256": expected_sha256,
        "candidates": candidates,
        "missing_candidates": missing,
        "mismatched_candidates": mismatched,
        "errors": [],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-dir", type=Path, default=Path("."))
    local_group = parser.add_mutually_exclusive_group(required=True)
    local_group.add_argument("--local-runtime", type=Path)
    local_group.add_argument(
        "--local-runtime-env",
        metavar="ENV_NAME",
        help="Read the local runtime candidate path from this environment variable.",
    )
    parser.add_argument("--pages-candidate", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.local_runtime_env:
        env_value = os.environ.get(args.local_runtime_env)
        if not env_value:
            result = {
                "status": "FAIL",
                "schema_version": "memory_atlas.snapshot_parity.v1",
                "errors": ["local runtime candidate environment variable is missing"],
                "candidates": {},
                "missing_candidates": ["local_runtime"],
                "mismatched_candidates": [],
            }
        else:
            result = audit_snapshot_parity(args.database_dir, Path(env_value), args.pages_candidate)
    else:
        result = audit_snapshot_parity(args.database_dir, args.local_runtime, args.pages_candidate)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
