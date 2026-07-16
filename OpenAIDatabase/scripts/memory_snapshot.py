#!/usr/bin/env python3
"""Export, validate, query and atomically restore a memory-only snapshot."""

from __future__ import annotations

import argparse
import copy
import hashlib
import io
import json
import os
import re
import shutil
import stat
import subprocess
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Sequence


TASK_ID = "TSK.OpenAIDatabase.PAM1.0018"
ACCEPTANCE_ID = "ACC.OpenAIDatabase.PAM1.0018"
POLICY_SCHEMA = "openai_database.memory_snapshot_policy.v1"
MANIFEST_SCHEMA = "openai_database.memory_snapshot_manifest.v1"
SNAPSHOT_VERSION = "portable-agent-memory-v1"
DEFAULT_POLICY = Path("config/memory-snapshot-policy.json")
CANONICAL_MANIFEST = "data/memory/records/manifest.json"
SNAPSHOT_MANIFEST = "SNAPSHOT_MANIFEST.json"
SNAPSHOT_POLICY = "SNAPSHOT_POLICY.json"
PROJECT_PREFIX = "OpenAIDatabase"
PUBLIC_RELEASE_REPOSITORY = "LinzeColin/AgentDatabase"
PUBLIC_RELEASE_VISIBILITY = "public"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
MEMORY_ID_RE = re.compile(r"^mem_[A-Za-z0-9][A-Za-z0-9._-]{7,127}$")
MAX_BOOTSTRAP_ASSET_BYTES = 2 * 1024 * 1024
ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
CREDENTIAL_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}\b"),
)


class SnapshotError(RuntimeError):
    """Stable fail-closed error that never contains memory statement text."""


@dataclass(frozen=True)
class SnapshotValidation:
    result: dict[str, Any]
    manifest: dict[str, Any]
    policy: dict[str, Any]
    payloads: dict[str, bytes]
    records: tuple[dict[str, Any], ...]


def sha256_prefixed(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _reject_constant(_: str) -> None:
    raise SnapshotError("non_standard_json_number")


def _object_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise SnapshotError("duplicate_json_key")
        result[key] = value
    return result


def load_json_bytes(payload: bytes, label: str) -> Any:
    try:
        return json.loads(
            payload.decode("utf-8"),
            object_pairs_hook=_object_without_duplicates,
            parse_constant=_reject_constant,
        )
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise SnapshotError(f"{label}_json_invalid") from exc


def safe_relative_path(value: Any) -> str:
    if not isinstance(value, str) or not value or "\x00" in value or "\\" in value or ":" in value:
        raise SnapshotError("snapshot_path_invalid")
    raw_parts = value.split("/")
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or path == PurePosixPath(".")
        or any(part in {"", ".", ".."} for part in raw_parts)
    ):
        raise SnapshotError("snapshot_path_invalid")
    if len(path.parts) > 12:
        raise SnapshotError("snapshot_path_too_deep")
    return path.as_posix()


def _credential_shape_present(payload: bytes) -> bool:
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SnapshotError("snapshot_non_utf8_member") from exc
    return any(pattern.search(text) is not None for pattern in CREDENTIAL_PATTERNS)


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise SnapshotError(f"{label}_invalid")
    return value


def validate_policy(policy: Mapping[str, Any]) -> None:
    if (
        policy.get("schema_version") != POLICY_SCHEMA
        or policy.get("task_id") != TASK_ID
        or policy.get("acceptance_id") != ACCEPTANCE_ID
        or policy.get("snapshot_version") != SNAPSHOT_VERSION
        or policy.get("source_repository") != "LinzeColin/CodexProject"
    ):
        raise SnapshotError("snapshot_policy_identity_invalid")
    archive = _mapping(policy.get("archive"), "snapshot_policy_archive")
    restore = _mapping(policy.get("restore"), "snapshot_policy_restore")
    recovery = _mapping(policy.get("recovery"), "snapshot_policy_recovery")
    security = _mapping(policy.get("security"), "snapshot_policy_security")
    release = _mapping(policy.get("release"), "snapshot_policy_release")
    raw = _mapping(policy.get("raw"), "snapshot_policy_raw")
    if (
        archive.get("format") != "zip-stored-v1"
        or archive.get("asset_name_template") != "portable-agent-memory-v1-{commit}.zip"
        or archive.get("deterministic_timestamp") != "1980-01-01T00:00:00Z"
        or not isinstance(archive.get("max_asset_bytes"), int)
        or not 0 < int(archive["max_asset_bytes"]) <= MAX_BOOTSTRAP_ASSET_BYTES
        or not isinstance(archive.get("max_member_bytes"), int)
        or int(archive["max_member_bytes"]) > 921600
    ):
        raise SnapshotError("snapshot_archive_policy_invalid")
    required = policy.get("commit_required_paths")
    runtime = policy.get("runtime_files")
    if not isinstance(required, list) or not required or len(required) != len(set(required)):
        raise SnapshotError("snapshot_required_paths_invalid")
    if CANONICAL_MANIFEST not in required or not isinstance(runtime, list) or len(runtime) != 3:
        raise SnapshotError("snapshot_required_paths_invalid")
    for item in required:
        safe_relative_path(item)
    runtime_targets: set[str] = set()
    for descriptor in runtime:
        row = _mapping(descriptor, "snapshot_runtime_file")
        safe_relative_path(row.get("source"))
        target = safe_relative_path(row.get("snapshot_path"))
        if target in runtime_targets or row.get("category") not in {"runtime", "runbook", "policy"}:
            raise SnapshotError("snapshot_runtime_file_invalid")
        runtime_targets.add(target)
    if SNAPSHOT_POLICY not in runtime_targets:
        raise SnapshotError("snapshot_embedded_policy_missing")
    if (
        raw.get("allowed_root") != "data/public_raw"
        or raw.get("include_only_exact_record_source_refs") is not True
        or raw.get("require_public_repository_allowed") is not True
        or raw.get("external_or_opaque_origin_included") is not False
    ):
        raise SnapshotError("snapshot_raw_policy_invalid")
    if (
        restore.get("destination_must_not_exist") is not True
        or restore.get("atomic_directory_publish") is not True
        or restore.get("partial_restore_allowed") is not False
        or restore.get("history_rewrite_allowed") is not False
    ):
        raise SnapshotError("snapshot_restore_policy_invalid")
    if (
        recovery.get("rto_target_seconds") != 1800
        or recovery.get("canonical_hash_match_percent") != 100
        or recovery.get("required_negative_cases")
        != ["tampered_member", "missing_member", "wrong_expected_commit"]
    ):
        raise SnapshotError("snapshot_recovery_policy_invalid")
    if any(security.get(key) is not False for key in ("credential_or_access_material_allowed",)):
        raise SnapshotError("snapshot_security_policy_invalid")
    if any(
        security.get(key) is not False
        for key in (
            "absolute_or_parent_path_allowed",
            "symlink_member_allowed",
            "duplicate_member_allowed",
            "encrypted_member_allowed",
        )
    ):
        raise SnapshotError("snapshot_security_policy_invalid")
    if any(
        security.get(key) is not True
        for key in (
            "release_requires_all_members_from_source_commit",
            "release_requires_public_repository_allowed_records",
            "release_requires_redacted_summary_records",
        )
    ):
        raise SnapshotError("snapshot_public_release_policy_invalid")
    if (
        release.get("repository") != PUBLIC_RELEASE_REPOSITORY
        or release.get("visibility") != PUBLIC_RELEASE_VISIBILITY
        or release.get("publish_task_id") != "TSK.OpenAIDatabase.PAM1.0019"
        or release.get("disposition") != "public_safe_release_asset_only"
        or release.get("checksum") != "sha256"
        or release.get("authenticity_claim_allowed_without_signature") is not False
    ):
        raise SnapshotError("snapshot_release_policy_invalid")


def load_policy(path: Path) -> dict[str, Any]:
    value = load_json_bytes(path.read_bytes(), "snapshot_policy")
    if not isinstance(value, dict):
        raise SnapshotError("snapshot_policy_invalid")
    validate_policy(value)
    return value


def _git(repository_root: Path, *args: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(repository_root), *args],
        capture_output=True,
        check=False,
        env={
            **os.environ,
            "LC_ALL": "C",
            "TZ": "UTC",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
        },
    )
    if result.returncode != 0:
        raise SnapshotError("snapshot_git_read_failed")
    return result.stdout


def repository_context(database_dir: Path, source_commit: str) -> tuple[Path, str, str]:
    database = database_dir.expanduser().resolve(strict=True)
    root = Path(_git(database, "rev-parse", "--show-toplevel").decode("utf-8").strip()).resolve()
    try:
        project_relative = database.relative_to(root).as_posix()
    except ValueError as exc:
        raise SnapshotError("snapshot_database_outside_repository") from exc
    if project_relative != PROJECT_PREFIX:
        raise SnapshotError("snapshot_project_root_invalid")
    commit = _git(root, "rev-parse", "--verify", f"{source_commit}^{{commit}}").decode("ascii").strip()
    if SHA_RE.fullmatch(commit) is None:
        raise SnapshotError("snapshot_source_commit_invalid")
    committed_at = _git(root, "show", "-s", "--format=%cI", commit).decode("ascii").strip()
    return root, commit, committed_at


def _git_file(root: Path, commit: str, relative: str) -> bytes:
    path = safe_relative_path(relative)
    return _git(root, "show", f"{commit}:{PROJECT_PREFIX}/{path}")


def public_release_summary(records: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    for record in records:
        sensitivity = _mapping(record.get("sensitivity"), "record_sensitivity")
        if (
            sensitivity.get("public_repository_allowed") is not True
            or sensitivity.get("credential_present") is not False
            or sensitivity.get("handling") != "redacted_summary"
        ):
            raise SnapshotError("canonical_record_not_public_release_safe")
    count = len(records)
    return {
        "public_release_safe_record_count": count,
        "public_repository_allowed_record_count": count,
        "redacted_summary_record_count": count,
        "credential_present_record_count": 0,
    }


def _parse_canonical_payloads(
    payloads: Mapping[str, bytes],
    *,
    max_member_bytes: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    manifest_path = f"{PROJECT_PREFIX}/{CANONICAL_MANIFEST}"
    if manifest_path not in payloads:
        raise SnapshotError("canonical_manifest_missing")
    manifest_raw = payloads[manifest_path]
    manifest = load_json_bytes(manifest_raw, "canonical_manifest")
    if not isinstance(manifest, dict) or manifest_raw != canonical_json_bytes(manifest) + b"\n":
        raise SnapshotError("canonical_manifest_noncanonical")
    entries = manifest.get("shards")
    if not isinstance(entries, list) or not entries:
        raise SnapshotError("canonical_shards_invalid")
    records: list[dict[str, Any]] = []
    shard_payloads: list[bytes] = []
    expected_ids: list[str] = []
    for sequence, descriptor in enumerate(entries, start=1):
        row = _mapping(descriptor, "canonical_shard_descriptor")
        relative = safe_relative_path(row.get("path"))
        snapshot_path = f"{PROJECT_PREFIX}/{relative}"
        if row.get("sequence") != sequence or snapshot_path not in payloads:
            raise SnapshotError("canonical_shard_membership_invalid")
        raw = payloads[snapshot_path]
        if not raw or len(raw) > max_member_bytes:
            raise SnapshotError("canonical_shard_size_invalid")
        if row.get("bytes") != len(raw) or row.get("sha256") != sha256_prefixed(raw):
            raise SnapshotError("canonical_shard_hash_mismatch")
        lines = raw.splitlines(keepends=True)
        if not lines or any(not line.endswith(b"\n") or line == b"\n" for line in lines):
            raise SnapshotError("canonical_jsonl_invalid")
        if row.get("record_count") != len(lines):
            raise SnapshotError("canonical_shard_record_count_mismatch")
        for line in lines:
            value = load_json_bytes(line[:-1], "canonical_record")
            if not isinstance(value, dict) or line != canonical_json_bytes(value) + b"\n":
                raise SnapshotError("canonical_record_noncanonical")
            record_id = value.get("id")
            if not isinstance(record_id, str) or MEMORY_ID_RE.fullmatch(record_id) is None:
                raise SnapshotError("canonical_record_id_invalid")
            hash_value = _mapping(value.get("hash"), "canonical_record_hash")
            unhashed = copy.deepcopy(value)
            unhashed.pop("hash", None)
            if (
                hash_value.get("algorithm") != "sha256"
                or hash_value.get("canonicalization") != "openai-memory-json-v1"
                or hash_value.get("value") != sha256_prefixed(canonical_json_bytes(unhashed))
            ):
                raise SnapshotError("canonical_record_hash_mismatch")
            if _credential_shape_present(line):
                raise SnapshotError("credential_shape_detected")
            expected_ids.append(record_id)
            records.append(value)
        shard_payloads.append(raw)
    dataset = b"".join(shard_payloads)
    if (
        manifest.get("record_count") != len(records)
        or manifest.get("shard_count") != len(entries)
        or manifest.get("dataset_bytes") != len(dataset)
        or manifest.get("dataset_sha256") != sha256_prefixed(dataset)
        or expected_ids != sorted(expected_ids)
        or len(expected_ids) != len(set(expected_ids))
    ):
        raise SnapshotError("canonical_dataset_reconciliation_failed")
    active = [record for record in records if record.get("status") == "active"]
    active_keys: set[tuple[Any, Any, Any]] = set()
    for record in active:
        source = _mapping(record.get("source"), "active_record_source")
        valid_time = _mapping(record.get("valid_time"), "active_record_valid_time")
        verification = _mapping(record.get("verification"), "active_record_verification")
        conflict = _mapping(record.get("conflict"), "active_record_conflict")
        scope = _mapping(record.get("scope"), "active_record_scope")
        key = (record.get("memory_key"), scope.get("type"), scope.get("key"))
        if (
            not source.get("type")
            or not source.get("ref")
            or not valid_time.get("from")
            or verification.get("state") != "verified"
            or conflict.get("state") == "unresolved"
            or key in active_keys
            or source.get("type") == "model_inference"
        ):
            raise SnapshotError("active_record_quality_gate_failed")
        active_keys.add(key)
    public_release = public_release_summary(records)
    return records, {
        "record_count": len(records),
        "active_record_count": len(active),
        "shard_count": len(entries),
        "dataset_bytes": len(dataset),
        "dataset_sha256": manifest["dataset_sha256"],
        "schema_valid_percent": 100,
        "active_source_coverage_percent": 100,
        "active_valid_time_coverage_percent": 100,
        "active_model_inference_count": 0,
        "unresolved_active_duplicate_or_conflict_count": 0,
        "public_release": public_release,
    }


def _referenced_public_raw_paths(records: Sequence[Mapping[str, Any]], policy: Mapping[str, Any]) -> list[str]:
    raw_policy = _mapping(policy.get("raw"), "snapshot_raw_policy")
    allowed_root = str(raw_policy["allowed_root"]).rstrip("/") + "/"
    allowed_extensions = set(raw_policy.get("allowed_extensions") or [])
    paths: set[str] = set()
    for record in records:
        sensitivity = _mapping(record.get("sensitivity"), "record_sensitivity")
        source = _mapping(record.get("source"), "record_source")
        if sensitivity.get("public_repository_allowed") is not True:
            continue
        ref = source.get("ref")
        if not isinstance(ref, str):
            continue
        if ref.startswith(f"{PROJECT_PREFIX}/"):
            ref = ref.removeprefix(f"{PROJECT_PREFIX}/")
        if not ref.startswith(allowed_root):
            continue
        relative = safe_relative_path(ref)
        if Path(relative).suffix not in allowed_extensions:
            raise SnapshotError("referenced_raw_extension_forbidden")
        paths.add(relative)
    return sorted(paths)


def _category_for_commit_path(path: str) -> str:
    if path.startswith("data/memory/records/"):
        return "canonical"
    if path in {"data/memory/AGENT_MEMORY.md", "data/memory/agent-memory.json"}:
        return "generated"
    if path.startswith("data/public_raw/"):
        return "raw"
    return "schema_or_policy"


def collect_snapshot_payloads(
    database_dir: Path,
    policy: Mapping[str, Any],
    source_commit: str,
    *,
    release_candidate: bool = False,
) -> tuple[dict[str, bytes], dict[str, Any]]:
    validate_policy(policy)
    root, commit, committed_at = repository_context(database_dir, source_commit)
    required = [safe_relative_path(path) for path in policy["commit_required_paths"]]
    payloads: dict[str, bytes] = {}
    origins: dict[str, tuple[str, str]] = {}
    for relative in required:
        target = f"{PROJECT_PREFIX}/{relative}"
        payloads[target] = _git_file(root, commit, relative)
        origins[target] = (_category_for_commit_path(relative), "git_commit")
    canonical_manifest = load_json_bytes(
        payloads[f"{PROJECT_PREFIX}/{CANONICAL_MANIFEST}"],
        "canonical_manifest",
    )
    if not isinstance(canonical_manifest, dict) or not isinstance(canonical_manifest.get("shards"), list):
        raise SnapshotError("canonical_manifest_invalid")
    for descriptor in canonical_manifest["shards"]:
        relative = safe_relative_path(_mapping(descriptor, "canonical_shard_descriptor").get("path"))
        target = f"{PROJECT_PREFIX}/{relative}"
        payloads[target] = _git_file(root, commit, relative)
        origins[target] = ("canonical", "git_commit")
    records, canonical = _parse_canonical_payloads(
        payloads,
        max_member_bytes=int(policy["archive"]["max_member_bytes"]),
    )
    raw_paths = _referenced_public_raw_paths(records, policy)
    for relative in raw_paths:
        target = f"{PROJECT_PREFIX}/{relative}"
        raw = _git_file(root, commit, relative)
        if len(raw) > int(policy["archive"]["max_member_bytes"]):
            raise SnapshotError("referenced_raw_size_invalid")
        payloads[target] = raw
        origins[target] = ("raw", "git_commit")
    database = database_dir.expanduser().resolve(strict=True)
    for descriptor in policy["runtime_files"]:
        row = _mapping(descriptor, "snapshot_runtime_file")
        source = safe_relative_path(row["source"])
        target = safe_relative_path(row["snapshot_path"])
        if release_candidate:
            payloads[target] = _git_file(root, commit, source)
            origin = "git_commit"
        else:
            runtime_source = database / source
            if not runtime_source.is_file() or runtime_source.is_symlink():
                raise SnapshotError("snapshot_runtime_source_invalid")
            payloads[target] = runtime_source.read_bytes()
            origin = "export_runtime"
        origins[target] = (str(row["category"]), origin)
    for path, payload in payloads.items():
        if len(payload) > int(policy["archive"]["max_member_bytes"]):
            raise SnapshotError("snapshot_member_size_invalid")
        if _credential_shape_present(payload):
            raise SnapshotError("credential_shape_detected")
        safe_relative_path(path)
    active = [record for record in records if record.get("status") == "active"]
    if not active:
        raise SnapshotError("snapshot_smoke_record_missing")
    file_rows = [
        {
            "path": path,
            "category": origins[path][0],
            "origin": origins[path][1],
            "bytes": len(payloads[path]),
            "sha256": sha256_prefixed(payloads[path]),
        }
        for path in sorted(payloads)
    ]
    tree_material = b"".join(
        row["path"].encode("utf-8") + b"\0" + row["sha256"].encode("ascii") + b"\n"
        for row in file_rows
    )
    asset_name = str(policy["archive"]["asset_name_template"]).format(commit=commit)
    manifest = {
        "schema_version": MANIFEST_SCHEMA,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "snapshot_version": SNAPSHOT_VERSION,
        "asset_name": asset_name,
        "source_repository": policy["source_repository"],
        "source_commit": commit,
        "source_commit_time": committed_at,
        "archive_format": policy["archive"]["format"],
        "integrity": "sha256_per_file_plus_release_asset_checksum",
        "authenticity_claim": False,
        "payload_tree_sha256": sha256_prefixed(tree_material),
        "files": file_rows,
        "commit_file_count": sum(row["origin"] == "git_commit" for row in file_rows),
        "runtime_file_count": sum(row["origin"] == "export_runtime" for row in file_rows),
        "release_candidate": release_candidate,
        "all_members_from_source_commit": all(
            row["origin"] == "git_commit" for row in file_rows
        ),
        "raw": {
            "mode": "exact_referenced_public_text_only",
            "included_file_count": len(raw_paths),
            "included_paths": [f"{PROJECT_PREFIX}/{path}" for path in raw_paths],
            "external_or_opaque_origin_included_count": 0,
        },
        "canonical": canonical,
        "smoke_query_record_id": str(sorted(active, key=lambda row: str(row["id"]))[0]["id"]),
        "release": policy["release"],
    }
    return payloads, manifest


def _zip_info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, date_time=ZIP_TIMESTAMP)
    info.compress_type = zipfile.ZIP_STORED
    info.create_system = 3
    info.external_attr = (stat.S_IFREG | 0o644) << 16
    info.flag_bits = 0
    return info


def build_snapshot_bytes(payloads: Mapping[str, bytes], manifest: Mapping[str, Any]) -> bytes:
    members = dict(payloads)
    members[SNAPSHOT_MANIFEST] = canonical_json_bytes(manifest) + b"\n"
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_STORED) as archive:
        for name in sorted(members):
            archive.writestr(_zip_info(name), members[name])
    return buffer.getvalue()


def export_snapshot(
    database_dir: Path,
    policy: Mapping[str, Any],
    source_commit: str,
    output_dir: Path,
    *,
    release_candidate: bool = False,
) -> tuple[dict[str, Any], Path]:
    payloads, manifest = collect_snapshot_payloads(
        database_dir,
        policy,
        source_commit,
        release_candidate=release_candidate,
    )
    archive_bytes = build_snapshot_bytes(payloads, manifest)
    if len(archive_bytes) > int(policy["archive"]["max_asset_bytes"]):
        raise SnapshotError("snapshot_asset_size_invalid")
    database = database_dir.expanduser().resolve(strict=True)
    repository_root = Path(_git(database, "rev-parse", "--show-toplevel").decode("utf-8").strip()).resolve()
    output = output_dir.expanduser().resolve()
    if output == repository_root or repository_root in output.parents:
        raise SnapshotError("snapshot_output_inside_repository_forbidden")
    output.mkdir(parents=True, exist_ok=True)
    asset = output / str(manifest["asset_name"])
    asset_sha256 = sha256_prefixed(archive_bytes)
    if asset.exists():
        if not asset.is_file() or asset.read_bytes() != archive_bytes:
            raise SnapshotError("snapshot_asset_collision")
        return {
            "schema_version": MANIFEST_SCHEMA,
            "status": "PASS",
            "operation": "export",
            "writes_files": False,
            "idempotent": True,
            "asset_name": asset.name,
            "asset_bytes": len(archive_bytes),
            "asset_sha256": asset_sha256,
            "source_commit": manifest["source_commit"],
            "file_count": len(payloads),
            "release_candidate": manifest["release_candidate"],
            "all_members_from_source_commit": manifest[
                "all_members_from_source_commit"
            ],
        }, asset
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{asset.name}.", dir=output)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(archive_bytes)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, asset)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return {
        "schema_version": MANIFEST_SCHEMA,
        "status": "PASS",
        "operation": "export",
        "writes_files": True,
        "idempotent": False,
        "asset_name": asset.name,
        "asset_bytes": len(archive_bytes),
        "asset_sha256": asset_sha256,
        "source_commit": manifest["source_commit"],
        "file_count": len(payloads),
        "release_candidate": manifest["release_candidate"],
        "all_members_from_source_commit": manifest[
            "all_members_from_source_commit"
        ],
    }, asset


def _read_snapshot_members(snapshot: Path) -> tuple[dict[str, bytes], str]:
    path = snapshot.expanduser().resolve(strict=True)
    if not path.is_file() or path.is_symlink() or path.stat().st_size > MAX_BOOTSTRAP_ASSET_BYTES:
        raise SnapshotError("snapshot_asset_invalid")
    members: dict[str, bytes] = {}
    try:
        with zipfile.ZipFile(path, "r") as archive:
            if archive.comment:
                raise SnapshotError("snapshot_member_security_invalid")
            for info in archive.infolist():
                name = safe_relative_path(info.filename)
                mode = (info.external_attr >> 16) & 0xFFFF
                if (
                    name in members
                    or info.is_dir()
                    or info.flag_bits & 0x1
                    or info.date_time != ZIP_TIMESTAMP
                    or info.create_system != 3
                    or info.extra
                    or info.comment
                    or stat.S_ISLNK(mode)
                    or not stat.S_ISREG(mode)
                    or stat.S_IMODE(mode) != 0o644
                    or info.file_size > 921600
                    or info.compress_type != zipfile.ZIP_STORED
                ):
                    raise SnapshotError("snapshot_member_security_invalid")
                members[name] = archive.read(info)
    except zipfile.BadZipFile as exc:
        raise SnapshotError("snapshot_zip_invalid") from exc
    return members, sha256_prefixed(path.read_bytes())


def validate_snapshot(snapshot: Path, expected_commit: str) -> SnapshotValidation:
    if SHA_RE.fullmatch(expected_commit) is None:
        raise SnapshotError("expected_commit_invalid")
    members, asset_sha256 = _read_snapshot_members(snapshot)
    if SNAPSHOT_MANIFEST not in members or SNAPSHOT_POLICY not in members:
        raise SnapshotError("snapshot_control_member_missing")
    manifest_raw = members.pop(SNAPSHOT_MANIFEST)
    manifest = load_json_bytes(manifest_raw, "snapshot_manifest")
    policy = load_json_bytes(members[SNAPSHOT_POLICY], "snapshot_policy")
    if not isinstance(manifest, dict) or not isinstance(policy, dict):
        raise SnapshotError("snapshot_control_member_invalid")
    if manifest_raw != canonical_json_bytes(manifest) + b"\n":
        raise SnapshotError("snapshot_manifest_noncanonical")
    validate_policy(policy)
    if (
        manifest.get("schema_version") != MANIFEST_SCHEMA
        or manifest.get("task_id") != TASK_ID
        or manifest.get("acceptance_id") != ACCEPTANCE_ID
        or manifest.get("snapshot_version") != SNAPSHOT_VERSION
        or manifest.get("source_repository") != policy["source_repository"]
        or manifest.get("source_commit") != expected_commit
        or manifest.get("archive_format") != "zip-stored-v1"
        or manifest.get("authenticity_claim") is not False
    ):
        raise SnapshotError("snapshot_manifest_identity_invalid")
    expected_name = str(policy["archive"]["asset_name_template"]).format(commit=expected_commit)
    if snapshot.name != expected_name or manifest.get("asset_name") != expected_name:
        raise SnapshotError("snapshot_asset_name_invalid")
    rows = manifest.get("files")
    if not isinstance(rows, list) or len(rows) != len(members):
        raise SnapshotError("snapshot_file_manifest_invalid")
    described: set[str] = set()
    tree_rows: list[dict[str, Any]] = []
    commit_count = 0
    runtime_count = 0
    for descriptor in rows:
        row = dict(_mapping(descriptor, "snapshot_file_descriptor"))
        path = safe_relative_path(row.get("path"))
        if path in described or path not in members:
            raise SnapshotError("snapshot_file_membership_invalid")
        payload = members[path]
        if row.get("bytes") != len(payload) or row.get("sha256") != sha256_prefixed(payload):
            raise SnapshotError("snapshot_file_hash_mismatch")
        if row.get("origin") == "git_commit":
            commit_count += 1
        elif row.get("origin") == "export_runtime":
            runtime_count += 1
        else:
            raise SnapshotError("snapshot_file_origin_invalid")
        if row.get("category") not in {"canonical", "generated", "schema_or_policy", "raw", "runtime", "runbook", "policy"}:
            raise SnapshotError("snapshot_file_category_invalid")
        if _credential_shape_present(payload):
            raise SnapshotError("credential_shape_detected")
        described.add(path)
        tree_rows.append(row)
    if described != set(members):
        raise SnapshotError("snapshot_file_membership_invalid")
    tree_material = b"".join(
        row["path"].encode("utf-8") + b"\0" + row["sha256"].encode("ascii") + b"\n"
        for row in sorted(tree_rows, key=lambda item: item["path"])
    )
    if (
        manifest.get("payload_tree_sha256") != sha256_prefixed(tree_material)
        or manifest.get("commit_file_count") != commit_count
        or manifest.get("runtime_file_count") != runtime_count
    ):
        raise SnapshotError("snapshot_payload_tree_mismatch")
    expected_commit_paths = {f"{PROJECT_PREFIX}/{path}" for path in policy["commit_required_paths"]}
    described_commit_paths = {row["path"] for row in tree_rows if row["origin"] == "git_commit"}
    if not expected_commit_paths.issubset(described_commit_paths):
        raise SnapshotError("snapshot_required_commit_file_missing")
    expected_runtime_paths = {row["snapshot_path"] for row in policy["runtime_files"]}
    described_runtime_paths = {
        row["path"]
        for row in tree_rows
        if row["category"] in {"runtime", "runbook", "policy"}
    }
    if expected_runtime_paths != described_runtime_paths:
        raise SnapshotError("snapshot_runtime_file_membership_invalid")
    records, canonical = _parse_canonical_payloads(
        members,
        max_member_bytes=int(policy["archive"]["max_member_bytes"]),
    )
    if manifest.get("canonical") != canonical:
        raise SnapshotError("snapshot_canonical_summary_mismatch")
    raw_summary = _mapping(manifest.get("raw"), "snapshot_raw_summary")
    raw_paths = sorted(row["path"] for row in tree_rows if row["category"] == "raw")
    if (
        raw_summary.get("included_file_count") != len(raw_paths)
        or raw_summary.get("included_paths") != raw_paths
        or raw_summary.get("external_or_opaque_origin_included_count") != 0
        or any(not path.startswith(f"{PROJECT_PREFIX}/data/public_raw/") for path in raw_paths)
    ):
        raise SnapshotError("snapshot_raw_membership_invalid")
    compact = members.get(f"{PROJECT_PREFIX}/data/memory/AGENT_MEMORY.md")
    machine = members.get(f"{PROJECT_PREFIX}/data/memory/agent-memory.json")
    if compact is None or machine is None:
        raise SnapshotError("snapshot_generated_entrypoint_invalid")
    handshake = load_json_bytes(machine, "agent_memory")
    handshake_canonical = _mapping(
        handshake.get("canonical") if isinstance(handshake, Mapping) else None,
        "agent_memory_canonical",
    )
    if (
        not isinstance(handshake, dict)
        or handshake.get("marker") != "LINZE_AGENT_MEMORY_V3"
        or handshake_canonical.get("dataset_sha256") != canonical["dataset_sha256"]
        or len(compact) > 24576
        or len(machine) > 262144
    ):
        raise SnapshotError("snapshot_generated_entrypoint_invalid")
    release_candidate = manifest.get("release_candidate")
    all_members_from_source_commit = manifest.get("all_members_from_source_commit")
    if (
        not isinstance(release_candidate, bool)
        or all_members_from_source_commit != (commit_count == len(members))
        or (release_candidate and all_members_from_source_commit is not True)
    ):
        raise SnapshotError("snapshot_release_candidate_invalid")
    result = {
        "schema_version": MANIFEST_SCHEMA,
        "status": "PASS",
        "operation": "validate",
        "writes_files": False,
        "asset_name": snapshot.name,
        "asset_bytes": snapshot.stat().st_size,
        "asset_sha256": asset_sha256,
        "source_commit": expected_commit,
        "file_count": len(members),
        "commit_file_count": commit_count,
        "runtime_file_count": runtime_count,
        "raw_file_count": len(raw_paths),
        "release_candidate": release_candidate,
        "all_members_from_source_commit": all_members_from_source_commit,
        "public_release": canonical["public_release"],
        "release_repository": policy["release"]["repository"],
        "release_visibility": policy["release"]["visibility"],
        "canonical": canonical,
        "smoke_query_record_id": manifest.get("smoke_query_record_id"),
        "integrity_verified": True,
        "authenticity_claim": False,
    }
    return SnapshotValidation(result, manifest, policy, members, tuple(records))


def _query_records(records: Iterable[Mapping[str, Any]], record_id: str) -> dict[str, Any]:
    if MEMORY_ID_RE.fullmatch(record_id) is None:
        raise SnapshotError("query_record_id_invalid")
    matches = [record for record in records if record.get("id") == record_id]
    if len(matches) != 1 or matches[0].get("status") != "active":
        raise SnapshotError("query_active_record_not_found")
    record = matches[0]
    statement = record.get("statement")
    source = _mapping(record.get("source"), "query_source")
    if not isinstance(statement, str):
        raise SnapshotError("query_record_invalid")
    return {
        "schema_version": "openai_database.memory_snapshot_query.v1",
        "status": "PASS",
        "operation": "query",
        "writes_files": False,
        "offline": True,
        "network_request_count": 0,
        "record_id": record_id,
        "record_status": record["status"],
        "memory_key": record.get("memory_key"),
        "statement_sha256": sha256_prefixed(statement.encode("utf-8")),
        "source_type": source.get("type"),
        "source_ref_sha256": sha256_prefixed(str(source.get("ref")).encode("utf-8")),
    }


def query_snapshot(snapshot: Path, expected_commit: str, record_id: str | None = None) -> dict[str, Any]:
    validated = validate_snapshot(snapshot, expected_commit)
    selected = record_id or str(validated.manifest.get("smoke_query_record_id"))
    return _query_records(validated.records, selected)


def _database_records(database_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    database = database_dir.expanduser().resolve(strict=True)
    policy_path = database.parent / SNAPSHOT_POLICY
    if not policy_path.is_file():
        raise SnapshotError("restored_snapshot_policy_missing")
    policy = load_policy(policy_path)
    manifest_path = database / CANONICAL_MANIFEST
    manifest = load_json_bytes(manifest_path.read_bytes(), "canonical_manifest")
    if not isinstance(manifest, dict) or not isinstance(manifest.get("shards"), list):
        raise SnapshotError("canonical_manifest_invalid")
    payloads = {f"{PROJECT_PREFIX}/{CANONICAL_MANIFEST}": manifest_path.read_bytes()}
    for descriptor in manifest["shards"]:
        relative = safe_relative_path(_mapping(descriptor, "canonical_shard_descriptor").get("path"))
        payloads[f"{PROJECT_PREFIX}/{relative}"] = (database / relative).read_bytes()
    return _parse_canonical_payloads(
        payloads,
        max_member_bytes=int(policy["archive"]["max_member_bytes"]),
    )


def query_database(database_dir: Path, record_id: str) -> dict[str, Any]:
    records, _ = _database_records(database_dir)
    return _query_records(records, record_id)


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def restore_snapshot(snapshot: Path, expected_commit: str, destination: Path) -> dict[str, Any]:
    validated = validate_snapshot(snapshot, expected_commit)
    target = destination.expanduser().resolve()
    if target.exists():
        raise SnapshotError("restore_destination_exists")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{target.name}.restore-", dir=target.parent))
    published = False
    try:
        all_members = dict(validated.payloads)
        all_members[SNAPSHOT_MANIFEST] = canonical_json_bytes(validated.manifest) + b"\n"
        for relative, payload in sorted(all_members.items()):
            path = temporary.joinpath(*PurePosixPath(safe_relative_path(relative)).parts)
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("xb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            path.chmod(0o644)
        for descriptor in validated.manifest["files"]:
            relative = descriptor["path"]
            restored = temporary.joinpath(*PurePosixPath(relative).parts).read_bytes()
            if descriptor["sha256"] != sha256_prefixed(restored):
                raise SnapshotError("restore_hash_reconciliation_failed")
        directories = sorted(
            (path for path in temporary.rglob("*") if path.is_dir()),
            key=lambda path: len(path.parts),
            reverse=True,
        )
        for directory in [*directories, temporary]:
            _fsync_directory(directory)
        if target.exists():
            raise SnapshotError("restore_destination_race")
        os.rename(temporary, target)
        published = True
        _fsync_directory(target.parent)
    finally:
        if not published:
            shutil.rmtree(temporary, ignore_errors=True)
    return {
        "schema_version": MANIFEST_SCHEMA,
        "status": "PASS",
        "operation": "restore",
        "writes_files": True,
        "atomic_publish": True,
        "source_commit": expected_commit,
        "restored_file_count": len(validated.payloads) + 1,
        "canonical_dataset_sha256": validated.result["canonical"]["dataset_sha256"],
        "partial_restore_count": 0,
    }


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    export = commands.add_parser("export", help="Export a deterministic commit-pinned snapshot.")
    export.add_argument("--database-dir", type=Path, default=Path(__file__).resolve().parents[1])
    export.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    export.add_argument("--source-commit", required=True)
    export.add_argument("--output-dir", required=True, type=Path)
    export.add_argument(
        "--release-candidate",
        action="store_true",
        help="Read every asset member from the exact source commit for public release.",
    )
    validate = commands.add_parser("validate", help="Validate every snapshot member and canonical hash.")
    validate.add_argument("--snapshot", required=True, type=Path)
    validate.add_argument("--expected-commit", required=True)
    restore = commands.add_parser("restore", help="Atomically restore into a new clean-room directory.")
    restore.add_argument("--snapshot", required=True, type=Path)
    restore.add_argument("--expected-commit", required=True)
    restore.add_argument("--destination", required=True, type=Path)
    query = commands.add_parser("query", help="Run an exact offline active-record smoke query.")
    source = query.add_mutually_exclusive_group(required=True)
    source.add_argument("--snapshot", type=Path)
    source.add_argument("--database-dir", type=Path)
    query.add_argument("--expected-commit")
    query.add_argument("--record-id")
    return parser.parse_args(argv)


def _resolve_policy(database_dir: Path, policy_path: Path) -> Path:
    path = policy_path if policy_path.is_absolute() else database_dir / policy_path
    resolved = path.expanduser().resolve(strict=True)
    database = database_dir.expanduser().resolve(strict=True)
    if database != resolved and database not in resolved.parents:
        raise SnapshotError("snapshot_policy_outside_database")
    return resolved


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.command == "export":
            database = args.database_dir.expanduser().resolve(strict=True)
            policy = load_policy(_resolve_policy(database, args.policy))
            result, _ = export_snapshot(
                database,
                policy,
                args.source_commit,
                args.output_dir,
                release_candidate=args.release_candidate,
            )
        elif args.command == "validate":
            result = validate_snapshot(args.snapshot, args.expected_commit).result
        elif args.command == "restore":
            result = restore_snapshot(args.snapshot, args.expected_commit, args.destination)
        else:
            if args.snapshot is not None:
                if args.expected_commit is None:
                    raise SnapshotError("expected_commit_required")
                result = query_snapshot(args.snapshot, args.expected_commit, args.record_id)
            else:
                if args.record_id is None:
                    raise SnapshotError("query_record_id_required")
                result = query_database(args.database_dir, args.record_id)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except (OSError, SnapshotError, zipfile.BadZipFile) as exc:
        reason = str(exc) if isinstance(exc, SnapshotError) else "snapshot_io_error"
        print(
            json.dumps(
                {
                    "schema_version": MANIFEST_SCHEMA,
                    "status": "FAIL_CLOSED",
                    "operation": args.command,
                    "writes_files": False,
                    "reason": reason,
                },
                sort_keys=True,
            )
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
