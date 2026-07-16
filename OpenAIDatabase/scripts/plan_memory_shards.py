#!/usr/bin/env python3
"""Plan and verify deterministic memory JSONL shards without writing data."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence


DEFAULT_CONTRACT = Path("config/memory.sharding.json")
DEFAULT_INPUT = Path("data/memory/active/active_memory.jsonl")
DEFAULT_MANIFEST = Path("data/memory/records/manifest.json")
MANIFEST_SCHEMA = "openai_database.memory_shard_manifest.v1"


class ShardingError(ValueError):
    """A stable fail-closed error code that never includes record content."""


@dataclass(frozen=True)
class Shard:
    sequence: int
    path: str
    payload: bytes
    record_count: int

    @property
    def byte_count(self) -> int:
        return len(self.payload)

    @property
    def sha256(self) -> str:
        return sha256_prefixed(self.payload)


@dataclass(frozen=True)
class ShardPlan:
    manifest: dict[str, Any]
    manifest_bytes: bytes
    shards: tuple[Shard, ...]

    @property
    def plan_sha256(self) -> str:
        return sha256_prefixed(self.manifest_bytes + b"".join(shard.payload for shard in self.shards))


def sha256_prefixed(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _reject_nonstandard_constant(_: str) -> None:
    raise ShardingError("non_standard_json_number")


def _object_without_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ShardingError("duplicate_json_key")
        result[key] = value
    return result


def normalize_json(value: Any) -> Any:
    if isinstance(value, float):
        raise ShardingError("floating_point_value_forbidden")
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, list):
        return [normalize_json(item) for item in value]
    if isinstance(value, dict):
        normalized: dict[str, Any] = {}
        for key, child in value.items():
            if not isinstance(key, str):
                raise ShardingError("non_string_json_object_key")
            normalized_key = unicodedata.normalize("NFC", key)
            if normalized_key in normalized:
                raise ShardingError("unicode_normalized_key_collision")
            normalized[normalized_key] = normalize_json(child)
        return {key: normalized[key] for key in sorted(normalized)}
    if value is None or isinstance(value, (bool, int)):
        return value
    raise ShardingError("unsupported_json_value")


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        normalize_json(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _normalized_records(records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    identifiers: set[str] = set()
    for value in records:
        record = normalize_json(dict(value))
        record_id = record.get("id")
        if not isinstance(record_id, str) or not record_id:
            raise ShardingError("record_id_missing_or_invalid")
        if record_id in identifiers:
            raise ShardingError("duplicate_record_id")
        identifiers.add(record_id)
        normalized.append(record)
    return sorted(normalized, key=lambda item: item["id"])


def canonical_record_line(record: Mapping[str, Any]) -> bytes:
    normalized = _normalized_records([record])[0]
    return canonical_json_bytes(normalized) + b"\n"


def parse_jsonl_bytes(payload: bytes) -> list[dict[str, Any]]:
    if not payload:
        return []
    if not payload.endswith(b"\n"):
        raise ShardingError("input_missing_final_lf")
    try:
        text = payload.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ShardingError("invalid_utf8") from exc

    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line:
            raise ShardingError(f"blank_jsonl_line:{line_number}")
        try:
            value = json.loads(
                line,
                object_pairs_hook=_object_without_duplicate_keys,
                parse_constant=_reject_nonstandard_constant,
            )
        except ShardingError as exc:
            raise ShardingError(f"invalid_json_line:{line_number}:{exc}") from exc
        except (json.JSONDecodeError, RecursionError) as exc:
            raise ShardingError(f"invalid_json_line:{line_number}") from exc
        if not isinstance(value, dict):
            raise ShardingError(f"non_object_json_line:{line_number}")
        records.append(value)
    try:
        return _normalized_records(records)
    except RecursionError as exc:
        raise ShardingError("json_nesting_too_deep") from exc


def resolve_repository_file(database_dir: Path, value: Path) -> Path:
    if value.is_absolute():
        raise ShardingError("absolute_path_forbidden")
    if any(part in {"", ".", ".."} for part in value.parts):
        raise ShardingError("path_traversal_forbidden")

    cursor = database_dir
    for part in value.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise ShardingError("symlink_input_forbidden")
    try:
        resolved = cursor.resolve(strict=True)
        resolved.relative_to(database_dir)
    except (FileNotFoundError, ValueError) as exc:
        raise ShardingError("repository_file_not_found_or_outside_root") from exc
    if not resolved.is_file():
        raise ShardingError("repository_input_not_file")
    return resolved


def load_contract(path: Path) -> dict[str, Any]:
    try:
        contract = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_object_without_duplicate_keys,
            parse_constant=_reject_nonstandard_constant,
        )
    except (OSError, json.JSONDecodeError, ShardingError) as exc:
        raise ShardingError("invalid_sharding_contract") from exc
    if not isinstance(contract, dict):
        raise ShardingError("invalid_sharding_contract")
    validate_contract(contract)
    return contract


def validate_contract(contract: Mapping[str, Any]) -> None:
    try:
        logical = contract["logical_dataset"]
        limits = contract["limits"]
        request_budget = contract["request_budget"]
        canonicalization = contract["canonicalization"]
        max_bytes = int(limits["max_shard_bytes"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ShardingError("invalid_sharding_contract") from exc

    required = {
        "schema_version": "openai_database.memory_sharding_contract.v1",
        "task_id": "TSK.OpenAIDatabase.PAM1.0002",
        "acceptance_id": "ACC.OpenAIDatabase.PAM1.0002",
        "mode": "ACTIVE_CANONICAL_SHARDING_AFTER_PAM1.0004",
    }
    if any(contract.get(key) != value for key, value in required.items()):
        raise ShardingError("invalid_sharding_contract_identity")
    if max_bytes != int(limits["kib_bytes"]) * int(limits["max_shard_kib"]):
        raise ShardingError("shard_limit_unit_drift")
    if max_bytes != 921600 or max_bytes >= int(limits["github_contents_conservative_comparison_bytes"]):
        raise ShardingError("shard_limit_drift")
    if logical.get("directory") != "data/memory/records":
        raise ShardingError("logical_dataset_path_drift")
    if logical.get("shard_name_template") != "records-{sequence:04d}.jsonl":
        raise ShardingError("shard_name_template_drift")
    if logical.get("discovery_path") != "data/memory/records/manifest.json":
        raise ShardingError("discovery_path_drift")
    if canonicalization.get("record_order") != "normalized_id_ascending":
        raise ShardingError("record_order_drift")
    if request_budget.get("default_discovery_object_count") != 1:
        raise ShardingError("default_discovery_budget_drift")
    if request_budget.get("recursive_tree_scan_required") is not False:
        raise ShardingError("recursive_tree_scan_drift")


def _shard_path(contract: Mapping[str, Any], sequence: int) -> str:
    logical = contract["logical_dataset"]
    name = str(logical["shard_name_template"]).format(sequence=sequence)
    return f"{logical['directory']}/{name}"


def build_shard_plan(records: Sequence[Mapping[str, Any]], contract: Mapping[str, Any]) -> ShardPlan:
    validate_contract(contract)
    try:
        ordered = _normalized_records(records)
    except RecursionError as exc:
        raise ShardingError("json_nesting_too_deep") from exc
    max_bytes = int(contract["limits"]["max_shard_bytes"])
    shards: list[Shard] = []
    current_lines: list[bytes] = []
    current_bytes = 0

    def close_current() -> None:
        nonlocal current_lines, current_bytes
        if not current_lines:
            return
        sequence = len(shards) + 1
        shards.append(
            Shard(
                sequence=sequence,
                path=_shard_path(contract, sequence),
                payload=b"".join(current_lines),
                record_count=len(current_lines),
            )
        )
        current_lines = []
        current_bytes = 0

    for record in ordered:
        line = canonical_json_bytes(record) + b"\n"
        if len(line) > max_bytes:
            raise ShardingError("single_record_exceeds_max_shard_bytes")
        if current_lines and current_bytes + len(line) > max_bytes:
            close_current()
        current_lines.append(line)
        current_bytes += len(line)
    close_current()

    dataset_payload = b"".join(shard.payload for shard in shards)
    manifest = {
        "schema_version": MANIFEST_SCHEMA,
        "logical_dataset": "data/memory/records/records-NNNN.jsonl",
        "discovery_path": contract["logical_dataset"]["discovery_path"],
        "canonicalization": contract["canonicalization"]["name"],
        "max_shard_bytes": max_bytes,
        "record_count": len(ordered),
        "shard_count": len(shards),
        "dataset_bytes": len(dataset_payload),
        "dataset_sha256": sha256_prefixed(dataset_payload),
        "default_discovery_objects": 1,
        "full_dataset_content_gets": 1 + len(shards),
        "recursive_tree_scan_required": False,
        "shards": [
            {
                "sequence": shard.sequence,
                "path": shard.path,
                "record_count": shard.record_count,
                "bytes": shard.byte_count,
                "sha256": shard.sha256,
            }
            for shard in shards
        ],
    }
    return ShardPlan(
        manifest=manifest,
        manifest_bytes=canonical_json_bytes(manifest) + b"\n",
        shards=tuple(shards),
    )


def verify_shard_set(
    manifest: Mapping[str, Any],
    payloads: Mapping[str, bytes],
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    try:
        entries = manifest["shards"]
    except KeyError as exc:
        raise ShardingError("manifest_missing_shards") from exc
    if not isinstance(entries, list):
        raise ShardingError("manifest_shards_not_array")
    expected_paths = [str(entry.get("path")) for entry in entries if isinstance(entry, dict)]
    if len(expected_paths) != len(entries) or set(payloads) != set(expected_paths):
        raise ShardingError("shard_set_membership_mismatch")

    records: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    max_bytes = int(contract["limits"]["max_shard_bytes"])
    for sequence, entry in enumerate(entries, start=1):
        if entry.get("sequence") != sequence or entry.get("path") != _shard_path(contract, sequence):
            raise ShardingError("manifest_shard_order_mismatch")
        payload = payloads[str(entry["path"])]
        if not payload or len(payload) > max_bytes:
            raise ShardingError("shard_size_invalid")
        if entry.get("bytes") != len(payload) or entry.get("sha256") != sha256_prefixed(payload):
            raise ShardingError("shard_integrity_mismatch")
        shard_records = parse_jsonl_bytes(payload)
        if entry.get("record_count") != len(shard_records):
            raise ShardingError("shard_record_count_mismatch")
        for record in shard_records:
            if record["id"] in seen_ids:
                raise ShardingError("duplicate_record_id")
            seen_ids.add(record["id"])
            records.append(record)

    rebuilt = build_shard_plan(records, contract)
    if rebuilt.manifest != dict(manifest):
        raise ShardingError("manifest_rebuild_mismatch")
    if any(payloads[expected.path] != expected.payload for expected in rebuilt.shards):
        raise ShardingError("shard_rebuild_mismatch")
    return {
        "status": "PASS",
        "record_count": rebuilt.manifest["record_count"],
        "shard_count": rebuilt.manifest["shard_count"],
        "dataset_bytes": rebuilt.manifest["dataset_bytes"],
        "dataset_sha256": rebuilt.manifest["dataset_sha256"],
    }


def load_manifest_records(
    database_dir: Path,
    manifest_path: Path,
    contract: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any], bytes]:
    resolved_manifest = resolve_repository_file(database_dir, manifest_path)
    raw = resolved_manifest.read_bytes()
    try:
        manifest = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_object_without_duplicate_keys,
            parse_constant=_reject_nonstandard_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ShardingError) as exc:
        raise ShardingError("invalid_canonical_manifest") from exc
    if not isinstance(manifest, dict):
        raise ShardingError("invalid_canonical_manifest")
    if raw != canonical_json_bytes(manifest) + b"\n":
        raise ShardingError("non_canonical_manifest_bytes")
    entries = manifest.get("shards")
    if not isinstance(entries, list):
        raise ShardingError("manifest_shards_not_array")
    payloads: dict[str, bytes] = {}
    records: list[dict[str, Any]] = []
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            raise ShardingError("invalid_manifest_shard_entry")
        relative = Path(entry["path"])
        shard_path = resolve_repository_file(database_dir, relative)
        payload = shard_path.read_bytes()
        payloads[entry["path"]] = payload
        records.extend(parse_jsonl_bytes(payload))
    verify_shard_set(manifest, payloads, contract)
    return records, manifest, raw


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-dir", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--input", type=Path)
    source.add_argument("--manifest", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    if args.input is None and args.manifest is None:
        args.manifest = DEFAULT_MANIFEST
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not args.dry_run:
        print(json.dumps({"status": "FAIL_CLOSED", "reason": "--dry-run is required", "writes_files": False}))
        return 2
    try:
        database_dir = args.database_dir.expanduser().resolve(strict=True)
        contract_path = resolve_repository_file(database_dir, args.contract)
        contract = load_contract(contract_path)
        if args.input is not None:
            input_path = resolve_repository_file(database_dir, args.input)
            input_payload = input_path.read_bytes()
            records = parse_jsonl_bytes(input_payload)
            input_label = args.input.as_posix()
            input_mode = "single_jsonl"
            input_bytes = len(input_payload)
            input_sha256 = sha256_prefixed(input_payload)
        else:
            records, source_manifest, input_payload = load_manifest_records(
                database_dir,
                args.manifest,
                contract,
            )
            input_label = args.manifest.as_posix()
            input_mode = "canonical_manifest"
            input_bytes = int(source_manifest["dataset_bytes"])
            input_sha256 = str(source_manifest["dataset_sha256"])
        first = build_shard_plan(records, contract)
        second = build_shard_plan(list(reversed(records)), contract)
        if first.plan_sha256 != second.plan_sha256 or first.manifest_bytes != second.manifest_bytes:
            raise ShardingError("repeat_build_drift")
        verify_shard_set(first.manifest, {shard.path: shard.payload for shard in first.shards}, contract)
        result = {
            "schema_version": "openai_database.memory_shard_dry_run.v1",
            "status": "PASS",
            "mode": "DRY_RUN",
            "writes_files": False,
            "canonical_data_writes": 0,
            "input": input_label,
            "input_mode": input_mode,
            "input_bytes": input_bytes,
            "input_sha256": input_sha256,
            "discovery_sha256": sha256_prefixed(first.manifest_bytes),
            "plan_sha256": first.plan_sha256,
            "repeat_build_identical": True,
            "manifest": first.manifest,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    except (OSError, ShardingError) as exc:
        reason = str(exc) if isinstance(exc, ShardingError) else "io_error"
        print(json.dumps({"status": "FAIL_CLOSED", "reason": reason, "writes_files": False}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
