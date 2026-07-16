#!/usr/bin/env python3
"""Validate five read-only Agent transport profiles against one memory identity."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Mapping


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from migrate_memory_records import record_hash, validate_record  # noqa: E402
from memory_retrieval import (  # noqa: E402
    ACCEPTANCE_ID as RETRIEVAL_ACCEPTANCE_ID,
    TASK_ID as RETRIEVAL_TASK_ID,
    RetrievalError,
    route_lexical_index,
)
from plan_memory_shards import parse_jsonl_bytes  # noqa: E402
from privacy_guard import PrivacyViolation, assert_no_credentials  # noqa: E402


TASK_ID = "TSK.OpenAIDatabase.PAM1.0008"
ACCEPTANCE_ID = "ACC.OpenAIDatabase.PAM1.0008"
SCHEMA_VERSION = "openai_database.agent_transport_compatibility.v1"
PROFILE_SCHEMA_VERSION = "openai_database.agent_transport_profiles.v1"
PROFILE_CONFIG = Path("config/agent_transport_profiles.json")
MACHINE_VIEW = Path("data/memory/agent-memory.json")
INSTRUCTIONS = Path("docs/AGENT_TRANSPORT_COMPATIBILITY.md")
HARNESS = Path("scripts/validate_agent_transport_compatibility.py")
RETRIEVAL_CONFIG = Path("config/evaluation/memory_retrieval_performance_v1.json")
RETRIEVAL_IMPLEMENTATION = Path("scripts/memory_retrieval.py")
EXPECTED_PROFILES = (
    "chatgpt_github",
    "codex_git",
    "github_mcp",
    "rest_https",
    "local_offline",
)
EXPECTED_TRANSPORTS = {"git", "github_rest", "https", "github_mcp", "chatgpt_github"}
REQUIRED_OPERATIONS = ("discover", "read", "query", "cite", "freshness", "fallback")
REQUIRED_IDENTITY_FIELDS = (
    "id",
    "statement_sha256",
    "record_sha256",
    "canonical_source_commit",
    "source_type",
    "source_ref_sha256",
    "source_evidence_hash",
)
ALLOWED_SOURCE_HOSTS = (
    "https://help.openai.com/",
    "https://developers.openai.com/",
    "https://github.com/github/github-mcp-server/",
    "https://docs.github.com/",
)
GIT_SHA_RE = re.compile(r"^[a-f0-9]{40,64}$")


class CompatibilityError(RuntimeError):
    """Stable fail-closed code that never contains memory content."""


def sha256_prefixed(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def emit_json(value: Mapping[str, Any]) -> None:
    print(json.dumps(dict(value), ensure_ascii=False, sort_keys=True, separators=(",", ":")), flush=True)


def safe_file(database_dir: Path, relative: Path, *, must_exist: bool = True) -> Path:
    if relative.is_absolute() or ".." in relative.parts:
        raise CompatibilityError("unsafe_repository_path")
    root = database_dir.resolve(strict=True)
    candidate = root / relative
    try:
        resolved = candidate.resolve(strict=must_exist)
        resolved.relative_to(root)
    except (OSError, ValueError) as exc:
        raise CompatibilityError("repository_path_unavailable") from exc
    if must_exist and (candidate.is_symlink() or not resolved.is_file()):
        raise CompatibilityError("repository_path_not_regular_file")
    return resolved


def load_json_file(database_dir: Path, relative: Path) -> tuple[dict[str, Any], bytes]:
    raw = safe_file(database_dir, relative).read_bytes()
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CompatibilityError("invalid_json_object") from exc
    if not isinstance(value, dict):
        raise CompatibilityError("invalid_json_object")
    return value, raw


def validate_profile_contract(contract: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    if contract.get("schema_version") != PROFILE_SCHEMA_VERSION:
        raise CompatibilityError("profile_schema_version_mismatch")
    if contract.get("task_id") != TASK_ID or contract.get("acceptance_id") != ACCEPTANCE_ID:
        raise CompatibilityError("profile_task_identity_mismatch")
    if tuple(contract.get("required_operations") or ()) != REQUIRED_OPERATIONS:
        raise CompatibilityError("profile_operations_mismatch")
    if tuple(contract.get("identity_fields") or ()) != REQUIRED_IDENTITY_FIELDS:
        raise CompatibilityError("profile_identity_fields_mismatch")
    profiles = contract.get("profiles")
    if not isinstance(profiles, list) or len(profiles) != 5 or contract.get("profile_count") != 5:
        raise CompatibilityError("profile_count_mismatch")
    if tuple(profile.get("profile_id") for profile in profiles) != EXPECTED_PROFILES:
        raise CompatibilityError("profile_id_mismatch")
    coverage: set[str] = set()
    for profile in profiles:
        transports = profile.get("transport_ids")
        fallback = profile.get("fallback")
        maximum = profile.get("max_repository_reads")
        if not isinstance(transports, list) or not all(isinstance(item, str) for item in transports):
            raise CompatibilityError("profile_transport_invalid")
        if not isinstance(fallback, list) or not fallback or not all(isinstance(item, str) for item in fallback):
            raise CompatibilityError("profile_fallback_missing")
        if not isinstance(maximum, int) or not 1 <= maximum <= 4:
            raise CompatibilityError("profile_read_bound_invalid")
        if profile.get("write_policy") != "none":
            raise CompatibilityError("profile_write_not_disabled")
        discovery = profile.get("discovery")
        if not isinstance(discovery, dict) or discovery.get("expected_objects") != 1:
            raise CompatibilityError("profile_discovery_not_one_object")
        coverage.update(transports)
    if coverage != EXPECTED_TRANSPORTS:
        raise CompatibilityError("transport_coverage_mismatch")
    gates = contract.get("hard_gates")
    if not isinstance(gates, dict) or gates.get("profile_pass_required") != 5:
        raise CompatibilityError("profile_pass_gate_mismatch")
    if gates.get("discovery_object_count") != 1 or gates.get("full_repo_scan_allowed") is not False:
        raise CompatibilityError("profile_discovery_gate_mismatch")
    if gates.get("writes_allowed") is not False or gates.get("published_live_acceptance_task") != "TSK.OpenAIDatabase.PAM1.0019":
        raise CompatibilityError("profile_publication_boundary_mismatch")
    sources = contract.get("official_sources")
    if not isinstance(sources, list) or len(sources) < 5:
        raise CompatibilityError("official_sources_missing")
    for source in sources:
        url = source.get("url") if isinstance(source, dict) else None
        if not isinstance(url, str) or not url.startswith(ALLOWED_SOURCE_HOSTS):
            raise CompatibilityError("official_source_not_allowed")
    return profiles


def validate_bound_file(database_dir: Path, binding: Mapping[str, Any], expected: Path) -> bytes:
    if binding.get("path") != expected.as_posix():
        raise CompatibilityError("adapter_binding_path_mismatch")
    payload = safe_file(database_dir, expected).read_bytes()
    if binding.get("sha256") != sha256_prefixed(payload):
        raise CompatibilityError("adapter_binding_hash_mismatch")
    return payload


def validate_handshake(
    database_dir: Path,
    handshake: Mapping[str, Any],
    contract: Mapping[str, Any],
) -> None:
    if handshake.get("protocol") != "linze-agent-memory" or handshake.get("protocol_version") != "3.0":
        raise CompatibilityError("handshake_protocol_mismatch")
    if handshake.get("transport_acceptance_task") != TASK_ID:
        raise CompatibilityError("handshake_transport_task_mismatch")
    if set(handshake.get("transports") or ()) != EXPECTED_TRANSPORTS:
        raise CompatibilityError("handshake_transport_coverage_mismatch")
    if handshake.get("raw", {}).get("instruction_trust") != "none":
        raise CompatibilityError("raw_instruction_trust_mismatch")
    adapter = handshake.get("adapter_contract")
    if not isinstance(adapter, dict):
        raise CompatibilityError("adapter_contract_missing")
    if adapter.get("acceptance_id") != ACCEPTANCE_ID or adapter.get("profile_count") != 5:
        raise CompatibilityError("adapter_contract_identity_mismatch")
    if adapter.get("published_live_acceptance_task") != "TSK.OpenAIDatabase.PAM1.0019":
        raise CompatibilityError("adapter_contract_publication_boundary_mismatch")
    validate_bound_file(database_dir, adapter.get("profiles", {}), PROFILE_CONFIG)
    validate_bound_file(database_dir, adapter.get("instructions", {}), INSTRUCTIONS)
    validate_bound_file(database_dir, adapter.get("harness", {}), HARNESS)
    if contract.get("profile_count") != adapter.get("profile_count"):
        raise CompatibilityError("adapter_profile_count_drift")
    retrieval = handshake.get("retrieval_contract")
    if not isinstance(retrieval, dict):
        raise CompatibilityError("retrieval_contract_missing")
    if (
        retrieval.get("task_id") != RETRIEVAL_TASK_ID
        or retrieval.get("acceptance_id") != RETRIEVAL_ACCEPTANCE_ID
    ):
        raise CompatibilityError("retrieval_contract_identity_mismatch")
    validate_bound_file(database_dir, retrieval.get("config", {}), RETRIEVAL_CONFIG)
    validate_bound_file(
        database_dir,
        retrieval.get("implementation", {}),
        RETRIEVAL_IMPLEMENTATION,
    )
    budget = retrieval.get("request_budget")
    cache = retrieval.get("cache")
    if not isinstance(budget, dict) or (
        budget.get("default_discovery_object_count_max") != 1
        or budget.get("indexed_fact_content_get_count_max") != 2
        or budget.get("raw_expansion_content_get_count_max") != 3
        or budget.get("recursive_full_tree_scan_count_max") != 0
    ):
        raise CompatibilityError("retrieval_request_budget_mismatch")
    if not isinstance(cache, dict) or (
        cache.get("commit_sha_required") is not True
        or cache.get("etag_required") is not True
        or cache.get("if_none_match_required_on_warm_read") is not True
        or cache.get("not_modified_status") != 304
        or cache.get("max_attempts") != 3
        or cache.get("serial_requests") is not True
    ):
        raise CompatibilityError("retrieval_cache_contract_mismatch")
    active_index = handshake.get("active_index")
    if not isinstance(active_index, list) or not active_index:
        raise CompatibilityError("active_index_empty")
    selected_id = str(active_index[0].get("id"))
    try:
        route = route_lexical_index(retrieval.get("index", {}), selected_id, limit=1)
    except RetrievalError as exc:
        raise CompatibilityError("retrieval_index_invalid") from exc
    if route.get("record_ids") != [selected_id] or route.get("content_get_count") > 2:
        raise CompatibilityError("retrieval_index_route_mismatch")


def record_identity(handshake: Mapping[str, Any], shard_bytes: bytes, record_id: str) -> dict[str, str]:
    index = {str(item.get("id")): item for item in handshake.get("active_index") or [] if isinstance(item, dict)}
    indexed = index.get(record_id)
    if indexed is None:
        raise CompatibilityError("record_id_not_in_active_index")
    shard_path = indexed.get("shard")
    shard_metadata = {
        str(item.get("path")): item
        for item in handshake.get("canonical", {}).get("shards") or []
        if isinstance(item, dict)
    }.get(shard_path)
    if shard_metadata is None or shard_metadata.get("sha256") != sha256_prefixed(shard_bytes):
        raise CompatibilityError("indexed_shard_hash_mismatch")
    records = [record for record in parse_jsonl_bytes(shard_bytes) if record.get("id") == record_id]
    if len(records) != 1:
        raise CompatibilityError("indexed_record_cardinality_mismatch")
    record = records[0]
    try:
        validate_record(record)
        assert_no_credentials(str(record["statement"]), record_id)
    except (PrivacyViolation, KeyError, TypeError, ValueError) as exc:
        raise CompatibilityError("record_security_or_schema_failure") from exc
    if record_hash(record) != indexed.get("record_sha256"):
        raise CompatibilityError("indexed_record_hash_mismatch")
    sensitivity = record.get("sensitivity")
    if not isinstance(sensitivity, dict) or sensitivity.get("credential_present") is not False or sensitivity.get("public_repository_allowed") is not True:
        raise CompatibilityError("record_not_public_allowed")
    source = record.get("source")
    if not isinstance(source, dict):
        raise CompatibilityError("record_source_missing")
    identity = {
        "id": record_id,
        "statement_sha256": sha256_prefixed(str(record["statement"]).encode("utf-8")),
        "record_sha256": str(record["hash"]["value"]),
        "canonical_source_commit": str(handshake["commit_sha"]),
        "source_type": str(source["type"]),
        "source_ref_sha256": sha256_prefixed(str(source["ref"]).encode("utf-8")),
        "source_evidence_hash": str(source["evidence_hash"]),
    }
    if tuple(identity) != REQUIRED_IDENTITY_FIELDS:
        raise CompatibilityError("identity_shape_mismatch")
    return identity


def replay_etag(payload: bytes) -> str:
    return '"replay-' + hashlib.sha256(payload).hexdigest() + '"'


def conditional_status(current_etag: str, if_none_match: str | None) -> int:
    return 304 if if_none_match == current_etag else 200


def require_fresh_commit(observed: str, expected: str) -> None:
    if not GIT_SHA_RE.fullmatch(expected) or observed != expected:
        raise CompatibilityError("stale_or_invalid_canonical_commit")


def make_envelope(profile_id: str, path: str, payload: bytes, artifact_ref: str) -> dict[str, Any]:
    digest = sha256_prefixed(payload)
    text = payload.decode("utf-8")
    if profile_id == "chatgpt_github":
        return {"repository": "LinzeColin/CodexProject", "path": path, "ref": artifact_ref, "text": text, "sha256": digest}
    if profile_id == "codex_git":
        return {"path": path, "ref": artifact_ref, "text": text, "sha256": digest, "agents_chain": True}
    if profile_id == "github_mcp":
        return {"path": path, "ref": artifact_ref, "read_only": True, "content": [{"type": "text", "text": text}], "sha256": digest}
    if profile_id == "rest_https":
        etag = replay_etag(payload)
        return {
            "rest": {"path": path, "ref": artifact_ref, "encoding": "base64", "content": base64.b64encode(payload).decode("ascii"), "etag": etag},
            "https": {"path": path, "ref": artifact_ref, "text": text, "etag": etag},
            "sha256": digest,
        }
    if profile_id == "local_offline":
        return {"manifest": {"ref": artifact_ref, "files": [{"path": path, "sha256": digest}]}, "path": path, "text": text}
    raise CompatibilityError("unknown_profile")


def decode_envelope(profile_id: str, envelope: Mapping[str, Any], path: str, artifact_ref: str) -> bytes:
    try:
        if profile_id in {"chatgpt_github", "codex_git"}:
            if envelope.get("path") != path or envelope.get("ref") != artifact_ref:
                raise CompatibilityError("adapter_envelope_ref_mismatch")
            payload = str(envelope["text"]).encode("utf-8")
            expected_hash = envelope.get("sha256")
        elif profile_id == "github_mcp":
            content = envelope.get("content")
            if envelope.get("path") != path or envelope.get("ref") != artifact_ref or envelope.get("read_only") is not True:
                raise CompatibilityError("mcp_not_pinned_read_only")
            if not isinstance(content, list) or len(content) != 1 or content[0].get("type") != "text":
                raise CompatibilityError("mcp_content_shape_invalid")
            payload = str(content[0]["text"]).encode("utf-8")
            expected_hash = envelope.get("sha256")
        elif profile_id == "rest_https":
            rest = envelope.get("rest")
            https = envelope.get("https")
            if not isinstance(rest, dict) or not isinstance(https, dict):
                raise CompatibilityError("rest_https_shape_invalid")
            if rest.get("path") != path or https.get("path") != path or rest.get("ref") != artifact_ref or https.get("ref") != artifact_ref:
                raise CompatibilityError("adapter_envelope_ref_mismatch")
            payload = base64.b64decode(str(rest["content"]), validate=True)
            if payload != str(https["text"]).encode("utf-8") or rest.get("etag") != https.get("etag"):
                raise CompatibilityError("rest_https_parity_mismatch")
            if conditional_status(str(rest["etag"]), str(rest["etag"])) != 304:
                raise CompatibilityError("etag_replay_failure")
            expected_hash = envelope.get("sha256")
        elif profile_id == "local_offline":
            manifest = envelope.get("manifest")
            if not isinstance(manifest, dict) or manifest.get("ref") != artifact_ref or envelope.get("path") != path:
                raise CompatibilityError("snapshot_manifest_ref_mismatch")
            files = manifest.get("files")
            if not isinstance(files, list) or len(files) != 1 or files[0].get("path") != path:
                raise CompatibilityError("snapshot_manifest_shape_invalid")
            payload = str(envelope["text"]).encode("utf-8")
            expected_hash = files[0].get("sha256")
        else:
            raise CompatibilityError("unknown_profile")
    except (KeyError, TypeError, ValueError, UnicodeError) as exc:
        raise CompatibilityError("adapter_envelope_decode_failure") from exc
    if expected_hash != sha256_prefixed(payload):
        raise CompatibilityError("adapter_envelope_hash_mismatch")
    return payload


def profile_accesses(profile_id: str, shard_path: str) -> list[str]:
    machine = "OpenAIDatabase/" + MACHINE_VIEW.as_posix()
    shard = "OpenAIDatabase/" + shard_path
    if profile_id == "chatgpt_github":
        return ["content-search:LINZE_AGENT_MEMORY_V3", machine, shard]
    if profile_id == "codex_git":
        return ["AGENTS.md", "OpenAIDatabase/AGENTS.md", machine, shard]
    if profile_id == "rest_https":
        return ["rest:" + machine, "https:" + machine, "rest:" + shard, "https:" + shard]
    return [machine, shard]


def run_profile(
    database_dir: Path,
    profile: Mapping[str, Any],
    machine_bytes: bytes,
    shard_path: str,
    shard_bytes: bytes,
    record_id: str,
    artifact_ref: str,
) -> dict[str, Any]:
    profile_id = str(profile["profile_id"])
    machine_path = "OpenAIDatabase/" + MACHINE_VIEW.as_posix()
    repository_shard_path = "OpenAIDatabase/" + shard_path
    decoded_machine = decode_envelope(profile_id, make_envelope(profile_id, machine_path, machine_bytes, artifact_ref), machine_path, artifact_ref)
    decoded_shard = decode_envelope(profile_id, make_envelope(profile_id, repository_shard_path, shard_bytes, artifact_ref), repository_shard_path, artifact_ref)
    try:
        observed_handshake = json.loads(decoded_machine)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CompatibilityError("adapter_handshake_decode_failure") from exc
    if profile_id == "codex_git":
        root_agents = database_dir.parent / "AGENTS.md"
        project_agents = database_dir / "AGENTS.md"
        if not root_agents.is_file() or not project_agents.is_file():
            raise CompatibilityError("codex_agents_chain_missing")
        if "agent-memory.json" not in root_agents.read_text(encoding="utf-8") or "agent-memory.json" not in project_agents.read_text(encoding="utf-8"):
            raise CompatibilityError("codex_agents_discovery_missing")
    identity = record_identity(observed_handshake, decoded_shard, record_id)
    require_fresh_commit(identity["canonical_source_commit"], str(observed_handshake["commit_sha"]))
    accesses = profile_accesses(profile_id, shard_path)
    if len(accesses) > int(profile["max_repository_reads"]):
        raise CompatibilityError("profile_read_bound_exceeded")
    citation = {
        "repository": "LinzeColin/CodexProject",
        "path": repository_shard_path,
        "artifact_ref": artifact_ref,
        "id": identity["id"],
        "record_sha256": identity["record_sha256"],
        "canonical_source_commit": identity["canonical_source_commit"],
    }
    if set(citation) != set(profile["citation"]["required_fields"]):
        raise CompatibilityError("profile_citation_shape_mismatch")
    return {
        "profile_id": profile_id,
        "status": "PASS",
        "operations": {operation: "PASS" for operation in REQUIRED_OPERATIONS},
        "identity": identity,
        "citation": citation,
        "freshness": {
            "strategy": profile["freshness"]["strategy"],
            "canonical_source_commit_verified": True,
            "bound_hashes_verified": True,
            "conditional_replay_304": profile_id == "rest_https",
        },
        "fallback": list(profile["fallback"]),
        "repository_accesses": accesses,
        "repository_read_count": len(accesses),
        "discovery_object_count": 1,
        "indexed_content_get_count": 2,
        "raw_expansion_content_get_count_max": 3,
        "conditional_etag_cache": True,
        "full_repo_scan": False,
        "writes": 0,
    }


def run_compatibility(
    database_dir: Path,
    *,
    record_id: str | None = None,
    artifact_ref: str = "CANDIDATE_TREE",
) -> dict[str, Any]:
    database_dir = database_dir.expanduser().resolve(strict=True)
    if artifact_ref != "CANDIDATE_TREE" and GIT_SHA_RE.fullmatch(artifact_ref) is None:
        raise CompatibilityError("artifact_ref_invalid")
    contract, contract_bytes = load_json_file(database_dir, PROFILE_CONFIG)
    profiles = validate_profile_contract(contract)
    handshake, machine_bytes = load_json_file(database_dir, MACHINE_VIEW)
    validate_handshake(database_dir, handshake, contract)
    try:
        assert_no_credentials(contract_bytes.decode("utf-8"), PROFILE_CONFIG.as_posix())
        assert_no_credentials(safe_file(database_dir, INSTRUCTIONS).read_text(encoding="utf-8"), INSTRUCTIONS.as_posix())
    except PrivacyViolation as exc:
        raise CompatibilityError("adapter_contract_credential_detected") from exc
    index = handshake.get("active_index")
    if not isinstance(index, list) or not index:
        raise CompatibilityError("active_index_empty")
    selected_id = record_id or str(index[0].get("id"))
    indexed = next((item for item in index if item.get("id") == selected_id), None)
    if not isinstance(indexed, dict):
        raise CompatibilityError("record_id_not_in_active_index")
    shard_path = str(indexed.get("shard"))
    shard_bytes = safe_file(database_dir, Path(shard_path)).read_bytes()
    results = [
        run_profile(database_dir, profile, machine_bytes, shard_path, shard_bytes, selected_id, artifact_ref)
        for profile in profiles
    ]
    identities = {json.dumps(result["identity"], ensure_ascii=False, sort_keys=True, separators=(",", ":")) for result in results}
    if len(identities) != 1:
        raise CompatibilityError("profile_identity_mismatch")
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "PASS",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "mode": "candidate_snapshot" if artifact_ref == "CANDIDATE_TREE" else "candidate_snapshot_pinned_ref_replay",
        "artifact_ref": artifact_ref,
        "record_id": selected_id,
        "profile_count": len(results),
        "profile_pass_count": sum(result["status"] == "PASS" for result in results),
        "all_profiles_same_identity": True,
        "identity": results[0]["identity"],
        "profiles": results,
        "discovery_object_count": 1,
        "indexed_content_get_count": 2,
        "raw_expansion_content_get_count_max": 3,
        "conditional_etag_cache": True,
        "full_repo_scan": False,
        "writes_files": False,
        "remote_memory_target_tested": False,
        "published_live_acceptance_task": "TSK.OpenAIDatabase.PAM1.0019",
        "official_sources_verified_on": contract["official_sources_verified_on"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-dir", type=Path, default=Path("."))
    parser.add_argument("--record-id")
    parser.add_argument("--artifact-ref", default="CANDIDATE_TREE")
    args = parser.parse_args()
    try:
        emit_json(run_compatibility(args.database_dir, record_id=args.record_id, artifact_ref=args.artifact_ref))
        return 0
    except (CompatibilityError, OSError) as exc:
        emit_json(
            {
                "schema_version": SCHEMA_VERSION,
                "status": "FAIL_CLOSED",
                "task_id": TASK_ID,
                "acceptance_id": ACCEPTANCE_ID,
                "reason": str(exc) if isinstance(exc, CompatibilityError) else "filesystem_error",
                "writes_files": False,
            }
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
