#!/usr/bin/env python3
"""Migrate the frozen legacy-memory profile into the one canonical V2 dataset."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
import unicodedata
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from build_memory_migration_profile import (  # noqa: E402
    LOCAL_PATH_RE,
    ProfileError,
    contains_credential_shape,
    load_json_bytes,
    normalize_statement,
    record_sha256,
    safe_repo_path,
)
from memory_forgetting import ForgettingError, validate_forgetting_dataset  # noqa: E402
from memory_lifecycle import LifecycleError, validate_lifecycle_dataset  # noqa: E402
from plan_memory_shards import (  # noqa: E402
    ShardingError,
    ShardPlan,
    build_shard_plan,
    canonical_json_bytes,
    load_contract as load_sharding_contract,
    parse_jsonl_bytes,
    sha256_prefixed,
    verify_shard_set,
)


DEFAULT_CONTRACT = Path("config/memory.cutover.json")
DEFAULT_MANIFEST = Path("data/memory/records/manifest.json")
LEGACY_CANONICAL_WRITE_RETIRED = True
RECORD_SCHEMA_VERSION = "openai_database.memory_record.v2"
RECORD_HASH_CANONICALIZATION = "openai-memory-json-v1"
ID_RE = re.compile(r"^mem_[A-Za-z0-9][A-Za-z0-9._-]{7,127}$")
MEMORY_KEY_RE = re.compile(r"^[a-z0-9][a-z0-9._:/-]{2,255}$")
SHA256_RE = re.compile(r"^sha256:[a-f0-9]{64}$")
SOURCE_TYPE_MAP = {"openai_export": "raw_import", "codex_pack": "raw_import"}
IMPORTANCE_MAP = {"高": "high", "中": "medium", "低": "low"}
MIGRATED_DISPOSITIONS = {"migrate-active", "migrate-candidate", "retire"}
AUDIT_ONLY_DISPOSITIONS = {"raw-evidence-only"}
FORBIDDEN_DISPOSITIONS = {"prohibited", "owner-decision"}
STATUS_VALUES = {"candidate", "active", "disputed", "retired"}
KIND_VALUES = {
    "answering_rule",
    "preference",
    "decision",
    "project_context",
    "workflow",
    "security_boundary",
    "fact",
    "negative_trigger",
}
SOURCE_VALUES = {"explicit_user", "repository_evidence", "raw_import", "model_inference"}
SENSITIVITY_VALUES = {"public", "private", "sensitive"}


class CutoverError(RuntimeError):
    """A fail-closed error whose message never contains a record value."""


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def normalize_text(value: Any) -> str:
    return unicodedata.normalize("NFC", str(value)).strip()


def require_exact_file(database_dir: Path, descriptor: Mapping[str, Any]) -> tuple[Path, bytes]:
    path = safe_repo_path(database_dir, str(descriptor["path"]), must_exist=True)
    raw = path.read_bytes()
    if len(raw) != int(descriptor["bytes"]) or digest(raw) != str(descriptor["sha256"]):
        raise CutoverError("input baseline drift detected")
    return path, raw


def load_contract(database_dir: Path, relative_path: Path) -> dict[str, Any]:
    path = safe_repo_path(database_dir, relative_path.as_posix(), must_exist=True)
    value = load_json_bytes(path.read_bytes(), "cutover contract")
    if not isinstance(value, dict):
        raise CutoverError("invalid cutover contract")
    required = {
        "schema_version": "openai_database.memory_cutover_contract.v1",
        "task_id": "TSK.OpenAIDatabase.PAM1.0004",
        "acceptance_id": "ACC.OpenAIDatabase.PAM1.0004",
        "mode": "ONE_TIME_CANONICAL_CUTOVER_WITH_IDEMPOTENT_VERIFY",
    }
    if any(value.get(key) != expected for key, expected in required.items()):
        raise CutoverError("cutover contract identity drift")
    output = value.get("canonical_output")
    audit = value.get("audit_reconciliation")
    security = value.get("security")
    if not isinstance(output, dict) or not isinstance(audit, dict) or not isinstance(security, dict):
        raise CutoverError("cutover contract section missing")
    if output.get("directory") != "data/memory/records":
        raise CutoverError("canonical output directory drift")
    if output.get("manifest") != DEFAULT_MANIFEST.as_posix():
        raise CutoverError("canonical manifest path drift")
    if int(output.get("max_shard_bytes", 0)) != 921600:
        raise CutoverError("canonical shard limit drift")
    if security.get("partial_canonical_write_allowed") is not False:
        raise CutoverError("partial write policy drift")
    if security.get("credential_or_access_material_allowed") is not False:
        raise CutoverError("credential policy drift")
    if int(audit.get("unique_legacy_ids", 0)) != 278:
        raise CutoverError("legacy identity baseline drift")
    return value


def load_jsonl_objects(raw: bytes, label: str) -> list[dict[str, Any]]:
    if not raw or not raw.endswith(b"\n"):
        raise CutoverError(f"{label} is empty or missing final LF")
    output: list[dict[str, Any]] = []
    for line_number, line in enumerate(raw.splitlines(), start=1):
        if not line:
            raise CutoverError(f"blank line in {label}:{line_number}")
        value = load_json_bytes(line, f"{label}:{line_number}")
        if not isinstance(value, dict):
            raise CutoverError(f"non-object row in {label}:{line_number}")
        output.append(value)
    return output


def record_hash(record: Mapping[str, Any]) -> str:
    payload = copy.deepcopy(dict(record))
    payload.pop("hash", None)
    return sha256_prefixed(canonical_json_bytes(payload))


def is_rfc3339(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None


def require_keys(value: Mapping[str, Any], expected: set[str], label: str) -> None:
    if set(value) != expected:
        raise CutoverError(f"{label} fields do not match the V2 contract")


def validate_string_array(value: Any, label: str, *, non_empty: bool = False) -> None:
    if not isinstance(value, list) or (non_empty and not value):
        raise CutoverError(f"{label} must be a bounded string array")
    if any(not isinstance(item, str) or not item for item in value):
        raise CutoverError(f"{label} contains an invalid item")
    if len(value) != len(set(value)):
        raise CutoverError(f"{label} contains a duplicate item")


def validate_record(record: Mapping[str, Any]) -> None:
    require_keys(
        record,
        {
            "schema_version",
            "id",
            "memory_key",
            "kind",
            "statement",
            "status",
            "scope",
            "source",
            "valid_time",
            "recorded_time",
            "supersession",
            "conflict",
            "confidence",
            "importance",
            "verification",
            "aliases",
            "tags",
            "negative_triggers",
            "sensitivity",
            "hash",
        },
        "record",
    )
    if record["schema_version"] != RECORD_SCHEMA_VERSION:
        raise CutoverError("record schema version drift")
    if not isinstance(record["id"], str) or ID_RE.fullmatch(record["id"]) is None:
        raise CutoverError("record ID is invalid")
    if not isinstance(record["memory_key"], str) or MEMORY_KEY_RE.fullmatch(record["memory_key"]) is None:
        raise CutoverError("memory key is invalid")
    if record["kind"] not in KIND_VALUES or record["status"] not in STATUS_VALUES:
        raise CutoverError("record kind or status is invalid")
    if not isinstance(record["statement"], str) or not record["statement"]:
        raise CutoverError("record statement is empty")

    scope = record["scope"]
    require_keys(scope, {"type", "key"}, "scope")
    if scope["type"] not in {"global", "project", "task", "conversation"} or not scope["key"]:
        raise CutoverError("scope is invalid")

    source = record["source"]
    require_keys(source, {"type", "ref", "observed_at", "evidence_hash"}, "source")
    if source["type"] not in SOURCE_VALUES or not isinstance(source["ref"], str) or not source["ref"]:
        raise CutoverError("source is invalid")
    if LOCAL_PATH_RE.search(source["ref"]):
        raise CutoverError("absolute local source reference detected")
    if not is_rfc3339(source["observed_at"]):
        raise CutoverError("source observed_at is invalid")
    if source["evidence_hash"] is not None and SHA256_RE.fullmatch(str(source["evidence_hash"])) is None:
        raise CutoverError("source evidence hash is invalid")

    valid_time = record["valid_time"]
    require_keys(valid_time, {"from", "to"}, "valid_time")
    if not is_rfc3339(valid_time["from"]):
        raise CutoverError("valid_time.from is invalid")
    if valid_time["to"] is not None and not is_rfc3339(valid_time["to"]):
        raise CutoverError("valid_time.to is invalid")

    recorded = record["recorded_time"]
    if set(recorded) not in ({"recorded_at", "recorded_by"}, {"recorded_at", "recorded_by", "transitions"}):
        raise CutoverError("recorded_time fields do not match the V2 contract")
    if not is_rfc3339(recorded["recorded_at"]):
        raise CutoverError("recorded_time is invalid")
    if recorded["recorded_by"] not in {"explicit_user", "automation_c", "importer", "migration"}:
        raise CutoverError("recorded_by is invalid")

    supersession = record["supersession"]
    require_keys(supersession, {"supersedes", "superseded_by", "reason"}, "supersession")
    validate_string_array(supersession["supersedes"], "supersedes")
    if supersession["superseded_by"] is not None and ID_RE.fullmatch(str(supersession["superseded_by"])) is None:
        raise CutoverError("superseded_by is invalid")
    if not isinstance(supersession["reason"], str) or not supersession["reason"]:
        raise CutoverError("supersession reason is empty")

    conflict = record["conflict"]
    require_keys(conflict, {"state", "with", "resolution"}, "conflict")
    if conflict["state"] not in {"none", "unresolved", "resolved"}:
        raise CutoverError("conflict state is invalid")
    validate_string_array(conflict["with"], "conflict.with")
    if conflict["resolution"] is not None and not isinstance(conflict["resolution"], str):
        raise CutoverError("conflict resolution is invalid")

    if record["confidence"] not in {"high", "medium", "low"}:
        raise CutoverError("confidence is invalid")
    if record["importance"] not in {"high", "medium", "low"}:
        raise CutoverError("importance is invalid")

    verification = record["verification"]
    require_keys(
        verification,
        {"state", "method", "evidence_refs", "verified_at", "rationale"},
        "verification",
    )
    if verification["state"] not in {"verified", "unverified", "rejected"}:
        raise CutoverError("verification state is invalid")
    if verification["method"] not in {"explicit_confirmation", "repository_hash", "raw_evidence_hash", "none"}:
        raise CutoverError("verification method is invalid")
    validate_string_array(verification["evidence_refs"], "verification.evidence_refs", non_empty=True)
    if verification["state"] == "verified":
        if not is_rfc3339(verification["verified_at"]):
            raise CutoverError("verified record lacks verified_at")
    elif verification["verified_at"] is not None:
        raise CutoverError("unverified record has verified_at")
    if not isinstance(verification["rationale"], str) or not verification["rationale"]:
        raise CutoverError("verification rationale is empty")

    for name in ("aliases", "tags", "negative_triggers"):
        validate_string_array(record[name], name)

    sensitivity = record["sensitivity"]
    require_keys(
        sensitivity,
        {"classification", "handling", "credential_present", "public_repository_allowed"},
        "sensitivity",
    )
    if sensitivity["classification"] not in SENSITIVITY_VALUES:
        raise CutoverError("sensitivity classification is invalid")
    expected_handling = "public_text" if sensitivity["classification"] == "public" else "redacted_summary"
    if sensitivity["handling"] != expected_handling:
        raise CutoverError("sensitivity handling is invalid")
    if sensitivity["credential_present"] is not False or sensitivity["public_repository_allowed"] is not True:
        raise CutoverError("sensitivity boundary is invalid")

    hash_value = record["hash"]
    require_keys(hash_value, {"algorithm", "canonicalization", "value"}, "hash")
    if hash_value["algorithm"] != "sha256" or hash_value["canonicalization"] != RECORD_HASH_CANONICALIZATION:
        raise CutoverError("record hash contract drift")
    if hash_value["value"] != record_hash(record):
        raise CutoverError("record hash mismatch")
    if source["type"] == "model_inference" and record["status"] == "active":
        raise CutoverError("model inference cannot be active")
    if record["status"] == "active" and verification["state"] != "verified":
        raise CutoverError("active record is unverified")
    if record["status"] == "active" and conflict["state"] == "unresolved":
        raise CutoverError("active record has unresolved conflict")
    if contains_credential_shape(record):
        raise CutoverError("credential-shaped material detected")


def validate_dataset(records: Sequence[Mapping[str, Any]]) -> None:
    identifiers = [str(record["id"]) for record in records]
    if identifiers != sorted(identifiers) or len(identifiers) != len(set(identifiers)):
        raise CutoverError("canonical record identity order or uniqueness drift")
    active_keys = Counter(
        (record["memory_key"], record["scope"]["type"], record["scope"]["key"])
        for record in records
        if record["status"] == "active"
    )
    if any(count > 1 for count in active_keys.values()):
        raise CutoverError("duplicate unresolved active memory key and scope")
    known_ids = set(identifiers)
    for record in records:
        references = list(record["supersession"]["supersedes"])
        if record["supersession"]["superseded_by"]:
            references.append(record["supersession"]["superseded_by"])
        references.extend(record["conflict"]["with"])
        if any(reference not in known_ids for reference in references):
            raise CutoverError("unresolved canonical record reference")
    try:
        validate_lifecycle_dataset(records)
    except LifecycleError as exc:
        raise CutoverError(str(exc)) from exc
    try:
        validate_forgetting_dataset(records)
    except ForgettingError as exc:
        raise CutoverError(str(exc)) from exc


def hashed_reference(prefix: str, parts: Iterable[Any]) -> str:
    material = "\0".join(normalize_text(part) for part in parts)
    return prefix + digest(material.encode("utf-8"))


def legacy_evidence_refs(record: Mapping[str, Any], map_entry: Mapping[str, Any]) -> list[str]:
    fingerprints = map_entry["fingerprints"]
    references = {
        "legacy-id:" + str(record["id"]),
        "legacy-record-sha256:" + str(fingerprints["representative_record_sha256"]),
        "legacy-candidate-history-sha256:" + str(fingerprints["candidate_history_sha256"]),
    }
    if record.get("activation_run_id"):
        references.add("legacy-run:" + normalize_text(record["activation_run_id"]))
    if record.get("original_statement_hash"):
        references.add("legacy-statement-hash:" + normalize_text(record["original_statement_hash"]))
    for evidence in record.get("evidence") or []:
        if not isinstance(evidence, dict):
            raise CutoverError("legacy evidence shape is invalid")
        references.add(
            hashed_reference(
                "legacy-evidence-sha256:",
                (evidence.get("source", ""), evidence.get("conversation_id", ""), evidence.get("timestamp", "")),
            )
        )
    return sorted(references)


def legacy_tags(record: Mapping[str, Any], disposition: str) -> list[str]:
    tags = {
        "migration-disposition:" + disposition,
        "legacy-action:" + normalize_text(record["action"]),
        "legacy-category:" + normalize_text(record["category"]),
        "legacy-tier:" + normalize_text(record["memory_tier"]),
        "legacy-validity:" + normalize_text(record["validity"]),
        "legacy-source-kind:" + normalize_text(record["source_kind"]),
    }
    if record.get("title"):
        tags.add(hashed_reference("legacy-title-sha256:", (record["title"],)))
    return sorted(tags)


def migrate_record(record: Mapping[str, Any], map_entry: Mapping[str, Any]) -> dict[str, Any]:
    migration = map_entry.get("migration")
    if not isinstance(migration, dict):
        raise CutoverError("migration map entry is missing migration data")
    disposition = migration.get("disposition")
    plan = migration.get("target_plan")
    if disposition not in MIGRATED_DISPOSITIONS or not isinstance(plan, dict):
        raise CutoverError("non-migrated disposition reached record builder")
    if contains_credential_shape(record):
        raise CutoverError("credential-shaped material detected")
    if record_sha256(dict(record)) != map_entry["fingerprints"]["representative_record_sha256"]:
        raise CutoverError("legacy representative hash mismatch")
    source_kind = str(record.get("source_kind"))
    if source_kind not in SOURCE_TYPE_MAP:
        raise CutoverError("legacy source kind is unsupported")
    source_ref = normalize_text(record.get("source", ""))
    if not source_ref or LOCAL_PATH_RE.search(source_ref):
        raise CutoverError("legacy source reference is invalid")
    activated_at = record.get("activated_at")
    if not is_rfc3339(activated_at):
        raise CutoverError("legacy activated_at is invalid")
    valid_date = normalize_text(record.get("date", ""))
    if len(valid_date) != 10 or not is_rfc3339(valid_date + "T00:00:00Z"):
        raise CutoverError("legacy date is invalid")
    if record.get("activation_mode") != "user_authorized_full_flow":
        raise CutoverError("legacy activation mode is unsupported")
    importance = IMPORTANCE_MAP.get(str(record.get("importance")))
    if importance is None:
        raise CutoverError("legacy importance is unsupported")
    sensitivity = str(record.get("sensitivity"))
    if sensitivity not in SENSITIVITY_VALUES:
        raise CutoverError("legacy sensitivity is unsupported")

    rationale_parts = ["legacy migration " + str(disposition)]
    if record.get("reason"):
        rationale_parts.append(normalize_text(record["reason"]))
    if record.get("curation_reason"):
        rationale_parts.append(normalize_text(record["curation_reason"]))
    verification_state = str(plan.get("verification_state"))
    result: dict[str, Any] = {
        "schema_version": RECORD_SCHEMA_VERSION,
        "id": str(record["id"]),
        "memory_key": str(plan["memory_key"]),
        "kind": str(plan["kind"]),
        "statement": normalize_statement(str(record["statement"])),
        "status": str(plan["status"]),
        "scope": copy.deepcopy(plan["scope"]),
        "source": {
            "type": SOURCE_TYPE_MAP[source_kind],
            "ref": source_ref,
            "observed_at": str(activated_at),
            "evidence_hash": "sha256:" + str(map_entry["fingerprints"]["representative_record_sha256"]),
        },
        "valid_time": {"from": valid_date + "T00:00:00Z", "to": None},
        "recorded_time": {"recorded_at": str(activated_at), "recorded_by": "importer"},
        "supersession": {
            "supersedes": [],
            "superseded_by": None,
            "reason": "No supersession relation was evidenced at cutover.",
        },
        "conflict": {"state": "none", "with": [], "resolution": None},
        "confidence": str(record["confidence"]),
        "importance": importance,
        "verification": {
            "state": verification_state,
            "method": "raw_evidence_hash" if verification_state == "verified" else "none",
            "evidence_refs": legacy_evidence_refs(record, map_entry),
            "verified_at": str(activated_at) if verification_state == "verified" else None,
            "rationale": "; ".join(rationale_parts),
        },
        "aliases": [],
        "tags": legacy_tags(record, str(disposition)),
        "negative_triggers": (
            [normalize_text(record["do_not_use_for"])] if record.get("do_not_use_for") else []
        ),
        "sensitivity": {
            "classification": sensitivity,
            "handling": "public_text" if sensitivity == "public" else "redacted_summary",
            "credential_present": False,
            "public_repository_allowed": True,
        },
        "hash": {
            "algorithm": "sha256",
            "canonicalization": RECORD_HASH_CANONICALIZATION,
            "value": "",
        },
    }
    result["hash"]["value"] = record_hash(result)
    validate_record(result)
    return result


def validate_expected_output(plan: ShardPlan, contract: Mapping[str, Any]) -> None:
    expected = contract["canonical_output"]
    manifest = plan.manifest
    checks = {
        "record_count": manifest["record_count"],
        "shard_count": manifest["shard_count"],
        "dataset_bytes": manifest["dataset_bytes"],
        "dataset_sha256": manifest["dataset_sha256"],
        "manifest_sha256": sha256_prefixed(plan.manifest_bytes),
    }
    if any(expected.get(key) != actual for key, actual in checks.items()):
        raise CutoverError("canonical output baseline drift detected")
    expected_shards = expected.get("expected_shards")
    observed_shards = [
        {
            "path": shard.path,
            "record_count": shard.record_count,
            "bytes": shard.byte_count,
            "sha256": shard.sha256,
        }
        for shard in plan.shards
    ]
    if expected_shards != observed_shards:
        raise CutoverError("canonical shard baseline drift detected")


def build_cutover(database_dir: Path, contract: Mapping[str, Any]) -> tuple[list[dict[str, Any]], ShardPlan, dict[str, Any]]:
    inputs = contract["inputs"]
    _, active_raw = require_exact_file(database_dir, inputs["legacy_active"])
    _, map_raw = require_exact_file(database_dir, inputs["migration_map"])
    _, report_raw = require_exact_file(database_dir, inputs["quality_report"])
    require_exact_file(database_dir, inputs["record_schema"])

    active_rows = parse_jsonl_bytes(active_raw)
    map_rows = load_jsonl_objects(map_raw, "migration map")
    report = load_json_bytes(report_raw, "quality report")
    if not isinstance(report, dict) or report.get("status") != "PASS":
        raise CutoverError("quality report is not PASS")
    if len(active_rows) != int(inputs["legacy_active"]["record_count"]):
        raise CutoverError("legacy active record-count drift")
    if len(map_rows) != int(inputs["migration_map"]["record_count"]):
        raise CutoverError("migration map record-count drift")

    active_by_id = {str(row["id"]): row for row in active_rows}
    if len(active_by_id) != len(active_rows):
        raise CutoverError("duplicate legacy active ID")
    map_by_id: dict[str, dict[str, Any]] = {}
    disposition_counts = Counter()
    for entry in map_rows:
        legacy_id = entry.get("legacy_id")
        if not isinstance(legacy_id, str) or legacy_id in map_by_id:
            raise CutoverError("invalid or duplicate migration-map ID")
        map_by_id[legacy_id] = entry
        disposition_counts[str(entry.get("migration", {}).get("disposition"))] += 1
    if set(active_by_id) != set(map_by_id):
        raise CutoverError("legacy/map identity reconciliation failed")
    if disposition_counts.get("prohibited", 0) or disposition_counts.get("owner-decision", 0):
        raise CutoverError("unresolved or prohibited disposition blocks cutover")

    records = [
        migrate_record(active_by_id[legacy_id], map_by_id[legacy_id])
        for legacy_id in sorted(active_by_id)
        if map_by_id[legacy_id]["migration"]["disposition"] in MIGRATED_DISPOSITIONS
    ]
    validate_dataset(records)
    status_counts = Counter(str(record["status"]) for record in records)
    expected_audit = contract["audit_reconciliation"]
    expected_status = {key: int(value) for key, value in expected_audit["canonical_status_counts"].items()}
    observed_status = {key: status_counts.get(key, 0) for key in expected_status}
    if len(records) != int(expected_audit["canonical_record_count"]) or observed_status != expected_status:
        raise CutoverError("canonical record reconciliation drift")
    if disposition_counts.get("raw-evidence-only", 0) != int(expected_audit["raw_evidence_only_count"]):
        raise CutoverError("raw-evidence-only reconciliation drift")

    sharding_path = safe_repo_path(database_dir, str(inputs["sharding_contract"]), must_exist=True)
    sharding_contract = load_sharding_contract(sharding_path)
    plan = build_shard_plan(records, sharding_contract)
    verify_shard_set(plan.manifest, {shard.path: shard.payload for shard in plan.shards}, sharding_contract)
    validate_expected_output(plan, contract)
    summary = {
        "schema_version": "openai_database.memory_cutover_result.v1",
        "status": "PASS",
        "task_id": contract["task_id"],
        "acceptance_id": contract["acceptance_id"],
        "unique_legacy_ids": len(map_rows),
        "canonical_record_count": len(records),
        "audit_only_record_count": disposition_counts.get("raw-evidence-only", 0),
        "canonical_status_counts": observed_status,
        "disposition_counts": dict(sorted(disposition_counts.items())),
        "schema_valid_record_count": len(records),
        "source_ref_coverage_count": sum(bool(record["source"]["ref"]) for record in records),
        "legacy_row_hash_coverage_count": sum(
            any(ref.startswith("legacy-record-sha256:") for ref in record["verification"]["evidence_refs"])
            for record in records
        ),
        "record_hash_coverage_count": sum(bool(record["hash"]["value"]) for record in records),
        "shard_count": plan.manifest["shard_count"],
        "dataset_bytes": plan.manifest["dataset_bytes"],
        "dataset_sha256": plan.manifest["dataset_sha256"],
        "manifest_sha256": sha256_prefixed(plan.manifest_bytes),
        "max_shard_bytes": max((shard.byte_count for shard in plan.shards), default=0),
        "repeat_build_identical": True,
        "credential_or_secret_count": 0,
        "dual_write_count": 0,
        "legacy_files_modified": 0,
    }
    return records, plan, summary


def load_canonical_records(database_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    try:
        database_dir = database_dir.expanduser().resolve(strict=True)
        manifest_path = safe_repo_path(database_dir, DEFAULT_MANIFEST.as_posix(), must_exist=True)
        manifest_raw = manifest_path.read_bytes()
        manifest = load_json_bytes(manifest_raw, "canonical manifest")
        if not isinstance(manifest, dict):
            raise CutoverError("canonical manifest is invalid")
        if manifest_raw != canonical_json_bytes(manifest) + b"\n":
            raise CutoverError("canonical manifest bytes are non-deterministic")
        contract = load_sharding_contract(database_dir / "config/memory.sharding.json")
        entries = manifest.get("shards")
        if not isinstance(entries, list):
            raise CutoverError("canonical manifest shard list is invalid")
        payloads: dict[str, bytes] = {}
        records: list[dict[str, Any]] = []
        for entry in entries:
            if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
                raise CutoverError("canonical manifest shard entry is invalid")
            shard_path = safe_repo_path(database_dir, entry["path"], must_exist=True)
            payload = shard_path.read_bytes()
            payloads[entry["path"]] = payload
            records.extend(parse_jsonl_bytes(payload))
        verify_shard_set(manifest, payloads, contract)
        for record in records:
            validate_record(record)
        validate_dataset(records)
        return records, manifest
    except CutoverError:
        raise
    except (ProfileError, ShardingError, OSError, ValueError) as exc:
        raise CutoverError("canonical dataset validation failed") from exc


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-dir", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--write", action="store_true")
    return parser.parse_args(argv)


def run(argv: list[str] | None = None) -> dict[str, Any]:
    args = parse_args(argv)
    if args.write:
        raise CutoverError("legacy canonical writer retired; use scripts/memory.py apply")
    database_dir = args.database_dir.expanduser().resolve(strict=True)
    contract = load_contract(database_dir, args.contract)
    records, first, summary = build_cutover(database_dir, contract)
    _, second, _ = build_cutover(database_dir, contract)
    if first.manifest_bytes != second.manifest_bytes or any(
        left.payload != right.payload for left, right in zip(first.shards, second.shards, strict=True)
    ):
        raise CutoverError("repeat build drift detected")
    summary.update(
        {
            "mode": "DRY_RUN",
            "writes_files": False,
            "canonical_file_write_count": 0,
        }
    )
    return summary


def main(argv: list[str] | None = None) -> int:
    try:
        result = run(argv)
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    except (CutoverError, ProfileError, ShardingError, OSError, ValueError) as exc:
        reason = str(exc) if isinstance(exc, CutoverError) else "cutover_validation_error"
        print(
            json.dumps(
                {
                    "schema_version": "openai_database.memory_cutover_result.v1",
                    "status": "FAIL_CLOSED",
                    "reason": reason,
                    "writes_files": False,
                },
                sort_keys=True,
            )
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
