#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path


PFI_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PFI_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

ISOLATED_CANDIDATE_NAMESPACE = "isolated_candidate_empty_data_v1"
ISOLATED_CANDIDATE_POLICY_SCHEMA = "PFIV025Stage1IsolatedCandidateCachePolicyV1"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def build_isolated_candidate_contract(
    manifest: dict[str, object],
    manifest_sha256: str,
) -> tuple[str, dict[str, object]]:
    if not isinstance(manifest, dict):
        raise ValueError("release manifest must be a JSON object")
    if manifest.get("product") != "PFI" or manifest.get("version") != "v0.2.5":
        raise ValueError("isolated candidate requires the PFI v0.2.5 release manifest")

    build_id = str(manifest.get("build_id") or "")
    git_commit = str(manifest.get("git_commit") or "")
    frontend_hash = str(manifest.get("frontend_bundle_hash") or "")
    backend_hash = str(manifest.get("backend_build_hash") or "")
    manifest_hash = str(manifest_sha256 or "")
    if not build_id:
        raise ValueError("release manifest build_id is required")
    if not HEX40.fullmatch(git_commit):
        raise ValueError("release manifest git_commit must be a lowercase 40-character hash")
    for label, value in (
        ("frontend_bundle_hash", frontend_hash),
        ("backend_build_hash", backend_hash),
        ("release_manifest_sha256", manifest_hash),
    ):
        if not HEX64.fullmatch(value):
            raise ValueError(f"{label} must be a lowercase 64-character SHA-256")

    release_identity = {
        "namespace": ISOLATED_CANDIDATE_NAMESPACE,
        "build_id": build_id,
        "git_commit": git_commit,
        "frontend_bundle_hash": frontend_hash,
        "backend_build_hash": backend_hash,
        "release_manifest_sha256": manifest_hash,
    }
    serialized = json.dumps(
        release_identity,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    cache_key = hashlib.sha256(serialized).hexdigest()
    return cache_key, {
        "schema": ISOLATED_CANDIDATE_POLICY_SCHEMA,
        **release_identity,
        "streamlit_cache_key": cache_key,
        "process_cache_key": cache_key,
        "persistent": False,
        "data_access": "disabled",
        "runtime_api": "disabled",
        "valid": True,
    }


def build_isolated_candidate_contract_from_project(
    project_root: Path,
) -> tuple[str, dict[str, object]]:
    manifest_path = project_root / "config" / "release_manifest.json"
    try:
        raw = manifest_path.read_bytes()
        manifest = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("release manifest is unavailable or invalid") from exc
    return build_isolated_candidate_contract(manifest, hashlib.sha256(raw).hexdigest())


def build_contract(
    project_root: Path,
    *,
    read_model_status: dict[str, object] | None = None,
) -> tuple[str, dict[str, object]]:
    from pfi_v02.stage_v021_runtime_api import (
        V025_RUNNING_BACKEND_SHA256,
        build_v025_release_asset_identity,
        build_v025_release_cache_context,
        build_v025_release_cache_policy_record,
        compute_v025_streamlit_cache_key,
    )

    context = build_v025_release_cache_context(
        project_root,
        read_model_status=read_model_status,
    )
    dimensions = context["dimensions"]
    cache_key = compute_v025_streamlit_cache_key(dimensions)
    asset_identity = build_v025_release_asset_identity(project_root)
    if not asset_identity.get("valid"):
        raise ValueError("release source hashes do not match release_manifest.json")
    policy = build_v025_release_cache_policy_record(
        dimensions,
        process_cache_key=cache_key,
        running_backend_hash=V025_RUNNING_BACKEND_SHA256,
        asset_identity_valid=True,
        dependency_snapshot=context["dependency_snapshot"],
    )
    if not policy.get("valid"):
        raise ValueError("release cache policy is not valid for this process")
    return cache_key, policy


def build_official_candidate_contract(
    project_root: Path,
) -> tuple[str, dict[str, object]]:
    from pfi_v02.stage_v021_runtime_api import (
        build_v025_stage1_candidate_read_model_status,
    )

    return build_contract(
        project_root,
        read_model_status=build_v025_stage1_candidate_read_model_status(),
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the public PFI v0.2.5 release cache contract")
    parser.add_argument("--project-root", type=Path, default=PFI_ROOT)
    parser.add_argument("--isolated-candidate", action="store_true")
    output = parser.add_mutually_exclusive_group(required=True)
    output.add_argument("--key-only", action="store_true")
    output.add_argument("--policy-json", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        project_root = args.project_root.expanduser().resolve()
        if args.isolated_candidate:
            cache_key, policy = build_isolated_candidate_contract_from_project(project_root)
        elif os.environ.get("PFI_STAGE1_CANDIDATE_MODE") == "1":
            cache_key, policy = build_official_candidate_contract(project_root)
        else:
            cache_key, policy = build_contract(project_root)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"PFI release cache contract unavailable: {exc}", file=sys.stderr)
        return 1
    if args.key_only:
        print(cache_key)
    else:
        print(json.dumps(policy, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
