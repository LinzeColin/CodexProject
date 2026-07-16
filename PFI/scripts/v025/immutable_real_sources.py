#!/usr/bin/env python3
"""Read the reviewed v0.2.5 real source objects from one immutable Git lock."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess
from typing import Any


PFI_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = PFI_ROOT.parent
DEFAULT_LOCK_PATH = (
    PFI_ROOT / "config/sources/v025_immutable_real_source_lock.json"
)
EXPECTED_SCHEMA = "PFIV025ImmutableRealSourceLockV1"


class ImmutableRealSourceError(RuntimeError):
    """Raised when the pinned source commit or any reviewed blob drifts."""


def _git_bytes(repo_root: Path, *args: str) -> bytes:
    completed = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        cwd=repo_root,
        check=False,
        capture_output=True,
    )
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise ImmutableRealSourceError(f"Git object lookup failed: {detail}")
    return completed.stdout


def load_source_lock(lock_path: Path = DEFAULT_LOCK_PATH) -> dict[str, Any]:
    payload = json.loads(lock_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema") != EXPECTED_SCHEMA:
        raise ImmutableRealSourceError("immutable source lock schema mismatch")
    if payload.get("version") != "v0.2.5":
        raise ImmutableRealSourceError("immutable source lock version mismatch")
    commit = payload.get("source_commit")
    if not isinstance(commit, str) or re.fullmatch(r"[0-9a-f]{40}", commit) is None:
        raise ImmutableRealSourceError("immutable source commit must be a full SHA-1")
    source_tree = payload.get("source_tree")
    if not isinstance(source_tree, str) or not source_tree.startswith("MetaDatabase/PFI/"):
        raise ImmutableRealSourceError("immutable source tree is outside the reviewed PFI scope")
    objects = payload.get("objects")
    if not isinstance(objects, list) or len(objects) != payload.get("expected_blob_count"):
        raise ImmutableRealSourceError("immutable source object count mismatch")
    return payload


def load_locked_source_objects(
    *,
    repo_root: Path = REPO_ROOT,
    lock_path: Path = DEFAULT_LOCK_PATH,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    """Return verified bytes plus a filename-free public attestation."""

    lock = load_source_lock(lock_path)
    commit = str(lock["source_commit"])
    source_tree = str(lock["source_tree"])
    _git_bytes(repo_root, "cat-file", "-e", f"{commit}^{{commit}}")
    _git_bytes(repo_root, "merge-base", "--is-ancestor", commit, "HEAD")
    tree_rows = _git_bytes(repo_root, "ls-tree", "-r", commit, "--", source_tree)
    decoded_rows = tree_rows.decode("utf-8").splitlines()
    if len(decoded_rows) != lock["expected_blob_count"]:
        raise ImmutableRealSourceError("pinned source tree no longer has four blobs")

    expected_rows = sorted(lock["objects"], key=lambda row: row["source_index"])
    verified: list[dict[str, object]] = []
    public_rows: list[dict[str, object]] = []
    for expected, tree_row in zip(expected_rows, decoded_rows, strict=True):
        try:
            metadata, relative_path = tree_row.split("\t", 1)
            mode, object_type, object_id = metadata.split(" ", 2)
        except ValueError as exc:
            raise ImmutableRealSourceError("unexpected git ls-tree output") from exc
        if mode != "100644" or object_type != "blob" or not relative_path.endswith(".csv"):
            raise ImmutableRealSourceError("pinned source tree contains an unexpected object")
        if object_id != expected.get("git_blob_oid"):
            raise ImmutableRealSourceError("pinned source blob OID drift")
        content = _git_bytes(repo_root, "show", f"{commit}:{relative_path}")
        digest = hashlib.sha256(content).hexdigest()
        if len(content) != expected.get("byte_size") or digest != expected.get("sha256"):
            raise ImmutableRealSourceError("pinned source blob content drift")
        source_index = int(expected["source_index"])
        verified.append(
            {
                "source_index": source_index,
                "git_blob_oid": object_id,
                "content": content,
            }
        )
        public_rows.append(
            {
                "source_index": source_index,
                "git_blob_oid": object_id,
                "bytes": len(content),
                "sha256": digest,
            }
        )

    object_set_hash = hashlib.sha256(
        "\n".join(
            f"{row['source_index']}:{row['git_blob_oid']}:{row['bytes']}:{row['sha256']}"
            for row in public_rows
        ).encode("utf-8")
    ).hexdigest()
    attestation = {
        "schema": "PFIV025ImmutableRealSourceAttestationV1",
        "status": "pass",
        "source_kind": "real_alipay_csv_git_objects",
        "source_commit": commit,
        "source_commit_reachable_from_head": True,
        "source_tree": source_tree,
        "source_blob_count": len(public_rows),
        "source_bytes": sum(int(row["bytes"]) for row in public_rows),
        "source_object_set_hash": f"sha256:{object_set_hash}",
        "source_objects": public_rows,
        "raw_filenames_emitted": False,
        "financial_rows_emitted": False,
        "source_mutated": False,
    }
    return verified, attestation
