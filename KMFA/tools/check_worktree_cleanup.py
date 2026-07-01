#!/usr/bin/env python3
"""Validate the local KMFA worktree cleanup evidence."""

from __future__ import annotations

import json
from pathlib import Path


BASE = Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject")
CANONICAL = BASE / "kmfa"
OLD_PATH = Path("/Users/linzezhang/Documents/KMFA v0.1")
MANIFEST = (
    Path(__file__).resolve().parents[1]
    / "stage_artifacts"
    / "WORKTREE_CLEANUP"
    / "machine"
    / "worktree_cleanup_manifest.json"
)


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def main() -> None:
    if not MANIFEST.exists():
        fail(f"missing manifest: {MANIFEST}")

    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if data.get("status") != "cleanup_complete_local":
        fail("manifest status must be cleanup_complete_local")

    if not CANONICAL.exists():
        fail(f"canonical KMFA worktree missing: {CANONICAL}")
    if OLD_PATH.exists():
        fail(f"stale old KMFA path still exists: {OLD_PATH}")

    kmfa_dirs = sorted(
        p for p in BASE.iterdir() if p.is_dir() and p.name.lower().startswith("kmfa")
    )
    if kmfa_dirs != [CANONICAL]:
        fail("non-canonical KMFA directory remains: " + ", ".join(map(str, kmfa_dirs)))

    deleted_paths = data.get("deleted_paths", [])
    if str(OLD_PATH) not in deleted_paths:
        fail("manifest does not record deleted old path")

    migration = data.get("migration_summary", {})
    forbidden_true = [
        "sensitive_or_raw_material_migrated",
        "raw_business_data_committed",
        "credentials_committed",
    ]
    for key in forbidden_true:
        if migration.get(key) is not False:
            fail(f"migration_summary.{key} must be false")

    if migration.get("migration_performed") is not True:
        fail("migration_performed must record this-run cleanup evidence migration")

    print(
        "PASS: KMFA worktree cleanup validated; only canonical kmfa remains and old path is removed."
    )


if __name__ == "__main__":
    main()
