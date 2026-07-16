#!/usr/bin/env python3
"""Pure admission and deterministic candidate planning for memory mutations."""

from __future__ import annotations

import copy
import hashlib
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

from migrate_memory_records import (
    RECORD_HASH_CANONICALIZATION,
    record_hash,
    validate_dataset,
    validate_record,
)
from memory_lifecycle import append_transition, assess_lifecycle, classify_pair, normalize_statement
from memory_forgetting import ForgettingError, validate_negative_boundary_payload
from plan_memory_shards import canonical_json_bytes, resolve_repository_file, sha256_prefixed
from privacy_guard import assert_no_credentials


ENVELOPE_SCHEMA_VERSION = "openai_database.memory_mutation.v1"
POLICY_SCHEMA_VERSION = "openai_database.memory_mutation_policy.v1"
TASK_ID = "TSK.OpenAIDatabase.PAM1.0009"
ACCEPTANCE_ID = "ACC.OpenAIDatabase.PAM1.0009"
OPERATIONS = ("add", "update", "retire", "dispute")
SOURCES = ("explicit_user", "repository_evidence", "raw_import", "model_inference")
BASE_SHA_RE = re.compile(r"^[a-f0-9]{40}$")
SHA256_RE = re.compile(r"^sha256:[a-f0-9]{64}$")
IDEMPOTENCY_RE = re.compile(r"^memory-mutation:[a-f0-9]{64}$")
RECORD_ID_RE = re.compile(r"^mem_[A-Za-z0-9][A-Za-z0-9._-]{7,127}$")
MEMORY_KEY_RE = re.compile(r"^[a-z0-9][a-z0-9._:/-]{2,255}$")
ACTOR_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
LOCAL_PATH_RE = re.compile(r"(?:^|\s)(?:[A-Za-z]:[\\/]|/(?:Users|home|private|tmp)/)")


class MutationAdmissionError(ValueError):
    """Stable fail-closed error code; never includes memory statement content."""


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise MutationAdmissionError(f"{label}_must_be_object")
    return value


def _require_keys(value: Mapping[str, Any], expected: set[str], label: str) -> None:
    if set(value) != expected:
        raise MutationAdmissionError(f"{label}_fields_invalid")


def _timestamp(value: Any, label: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise MutationAdmissionError(f"{label}_invalid")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise MutationAdmissionError(f"{label}_invalid") from exc
    if parsed.tzinfo is None:
        raise MutationAdmissionError(f"{label}_invalid")
    return parsed


def _portable_reference(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 512:
        raise MutationAdmissionError(f"{label}_invalid")
    if "\x00" in value or LOCAL_PATH_RE.search(value) or value.startswith(("/", "~")):
        raise MutationAdmissionError(f"{label}_not_portable")
    if not value.startswith(("https://", "http://")) and ".." in Path(value).parts:
        raise MutationAdmissionError(f"{label}_not_portable")
    return value


def _string_list(value: Any, label: str, maximum: int) -> list[str]:
    if not isinstance(value, list) or len(value) > maximum:
        raise MutationAdmissionError(f"{label}_invalid")
    if any(not isinstance(item, str) or not item or len(item) > 256 for item in value):
        raise MutationAdmissionError(f"{label}_invalid")
    if len(value) != len(set(value)):
        raise MutationAdmissionError(f"{label}_duplicate")
    return sorted(value)


def _json_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key, value in pairs:
        if key in output:
            raise MutationAdmissionError("duplicate_json_key")
        output[key] = value
    return output


def _reject_constant(value: str) -> None:
    raise MutationAdmissionError(f"nonstandard_json_constant_{value}")


def load_policy(database_dir: Path, relative_path: Path) -> dict[str, Any]:
    path = resolve_repository_file(database_dir, relative_path)
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_json_without_duplicates,
            parse_constant=_reject_constant,
        )
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise MutationAdmissionError("mutation_policy_invalid") from exc
    policy = dict(_mapping(value, "mutation_policy"))
    validate_policy(policy)
    return policy


def validate_policy(policy: Mapping[str, Any]) -> None:
    required = {
        "schema_version",
        "task_id",
        "acceptance_id",
        "operations",
        "source_operation_matrix",
        "source_requirements",
        "record_enums",
        "limits",
        "automation_c",
        "publication_boundary",
    }
    _require_keys(policy, required, "mutation_policy")
    if policy["schema_version"] != POLICY_SCHEMA_VERSION:
        raise MutationAdmissionError("mutation_policy_schema_drift")
    if policy["task_id"] != TASK_ID or policy["acceptance_id"] != ACCEPTANCE_ID:
        raise MutationAdmissionError("mutation_policy_identity_drift")
    if tuple(policy["operations"]) != OPERATIONS:
        raise MutationAdmissionError("mutation_operation_policy_drift")
    matrix = _mapping(policy["source_operation_matrix"], "source_operation_matrix")
    if set(matrix) != set(SOURCES):
        raise MutationAdmissionError("mutation_source_policy_drift")
    for source in SOURCES:
        row = _mapping(matrix[source], f"source_matrix_{source}")
        if set(row) != set(OPERATIONS):
            raise MutationAdmissionError("mutation_source_operation_matrix_drift")
    for source in ("raw_import", "model_inference"):
        if set(matrix[source].values()) != {"reject_persistence"}:
            raise MutationAdmissionError("non_persistent_source_policy_drift")
    automation = _mapping(policy["automation_c"], "automation_c")
    if (
        automation.get("base_branch") != "main"
        or automation.get("direct_main_write") is not False
        or automation.get("issue_mutations") != 0
        or automation.get("non_draft_pr_count") != 1
        or automation.get("same_repository_only") is not True
        or automation.get("branch_prefix") != "automation-c/memory-"
    ):
        raise MutationAdmissionError("automation_c_policy_drift")
    boundaries = _mapping(policy["publication_boundary"], "publication_boundary")
    if boundaries.get("candidate_transaction_only_until") != "TSK.OpenAIDatabase.PAM1.0017":
        raise MutationAdmissionError("mutation_publication_boundary_drift")


def load_envelope(database_dir: Path, relative_path: Path, policy: Mapping[str, Any]) -> dict[str, Any]:
    path = resolve_repository_file(database_dir, relative_path)
    payload = path.read_bytes()
    maximum = int(_mapping(policy["limits"], "limits")["envelope_max_bytes"])
    if not payload or len(payload) > maximum:
        raise MutationAdmissionError("mutation_envelope_size_invalid")
    try:
        text = payload.decode("utf-8")
        value = json.loads(
            text,
            object_pairs_hook=_json_without_duplicates,
            parse_constant=_reject_constant,
        )
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise MutationAdmissionError("mutation_envelope_json_invalid") from exc
    assert_no_credentials(text, "mutation_envelope")
    return dict(_mapping(value, "mutation_envelope"))


def expected_idempotency_key(envelope: Mapping[str, Any]) -> str:
    material = dict(envelope)
    material.pop("idempotency_key", None)
    return "memory-mutation:" + hashlib.sha256(canonical_json_bytes(material)).hexdigest()


def validate_envelope(
    envelope: Mapping[str, Any],
    policy: Mapping[str, Any],
    *,
    current_base_sha: str,
) -> None:
    _require_keys(
        envelope,
        {
            "schema_version",
            "operation",
            "idempotency_key",
            "base_commit_sha",
            "actor",
            "source",
            "authorization",
            "target",
            "payload",
            "valid_time",
            "sensitivity",
            "reason",
        },
        "mutation_envelope",
    )
    if envelope["schema_version"] != ENVELOPE_SCHEMA_VERSION:
        raise MutationAdmissionError("mutation_envelope_schema_drift")
    operation = envelope["operation"]
    if operation not in OPERATIONS:
        raise MutationAdmissionError("mutation_operation_invalid")
    if not isinstance(envelope["idempotency_key"], str) or IDEMPOTENCY_RE.fullmatch(envelope["idempotency_key"]) is None:
        raise MutationAdmissionError("mutation_idempotency_key_invalid")
    if envelope["idempotency_key"] != expected_idempotency_key(envelope):
        raise MutationAdmissionError("mutation_idempotency_key_content_mismatch")
    base = envelope["base_commit_sha"]
    if not isinstance(base, str) or BASE_SHA_RE.fullmatch(base) is None:
        raise MutationAdmissionError("mutation_base_sha_invalid")
    if base != current_base_sha:
        raise MutationAdmissionError("mutation_base_sha_mismatch")

    actor = _mapping(envelope["actor"], "actor")
    source = _mapping(envelope["source"], "source")
    authorization = _mapping(envelope["authorization"], "authorization")
    target = _mapping(envelope["target"], "target")
    valid_time = _mapping(envelope["valid_time"], "valid_time")
    sensitivity = _mapping(envelope["sensitivity"], "sensitivity")
    _require_keys(actor, {"type", "id"}, "actor")
    _require_keys(source, {"type", "ref", "observed_at", "evidence_hash"}, "source")
    _require_keys(authorization, {"mode", "ref", "authorized_at"}, "authorization")
    _require_keys(target, {"record_id", "memory_key", "scope"}, "target")
    _require_keys(valid_time, {"from", "to"}, "valid_time")
    _require_keys(
        sensitivity,
        {"classification", "handling", "credential_present", "public_repository_allowed"},
        "sensitivity",
    )

    source_type = source["type"]
    matrix = _mapping(policy["source_operation_matrix"], "source_operation_matrix")
    if source_type not in matrix or matrix[source_type][operation] == "reject_persistence":
        raise MutationAdmissionError("mutation_source_not_persistable")
    requirements = _mapping(policy["source_requirements"], "source_requirements")
    source_rule = _mapping(requirements[source_type], "source_requirement")
    if actor.get("type") != source_rule["actor_type"]:
        raise MutationAdmissionError("mutation_actor_not_authorized_for_source")
    if not isinstance(actor.get("id"), str) or ACTOR_ID_RE.fullmatch(actor["id"]) is None:
        raise MutationAdmissionError("mutation_actor_id_invalid")
    if authorization.get("mode") != source_rule["authorization_mode"]:
        raise MutationAdmissionError("mutation_authorization_missing_or_invalid")
    _portable_reference(source.get("ref"), "mutation_source_ref")
    _portable_reference(authorization.get("ref"), "mutation_authorization_ref")
    observed = _timestamp(source.get("observed_at"), "mutation_source_time")
    authorized = _timestamp(authorization.get("authorized_at"), "mutation_authorization_time")
    if authorized < observed:
        raise MutationAdmissionError("mutation_authorization_precedes_source")
    evidence_hash = source.get("evidence_hash")
    if evidence_hash is not None and (not isinstance(evidence_hash, str) or SHA256_RE.fullmatch(evidence_hash) is None):
        raise MutationAdmissionError("mutation_evidence_hash_invalid")
    if source_rule["evidence_hash_required"] and evidence_hash is None:
        raise MutationAdmissionError("mutation_evidence_hash_required")

    record_id = target.get("record_id")
    if record_id is not None and (not isinstance(record_id, str) or RECORD_ID_RE.fullmatch(record_id) is None):
        raise MutationAdmissionError("mutation_target_record_id_invalid")
    memory_key = target.get("memory_key")
    if not isinstance(memory_key, str) or MEMORY_KEY_RE.fullmatch(memory_key) is None:
        raise MutationAdmissionError("mutation_memory_key_invalid")
    scope = _mapping(target.get("scope"), "target_scope")
    _require_keys(scope, {"type", "key"}, "target_scope")
    if scope.get("type") not in source_rule["allowed_scopes"]:
        raise MutationAdmissionError("mutation_scope_not_authorized_for_source")
    if not isinstance(scope.get("key"), str) or not scope["key"] or len(scope["key"]) > 256:
        raise MutationAdmissionError("mutation_scope_key_invalid")
    if operation == "add" and record_id is not None:
        raise MutationAdmissionError("mutation_add_record_id_must_be_null")
    if operation != "add" and record_id is None:
        raise MutationAdmissionError("mutation_target_record_id_required")

    start = _timestamp(valid_time.get("from"), "mutation_valid_from")
    end_raw = valid_time.get("to")
    if end_raw is not None and _timestamp(end_raw, "mutation_valid_to") <= start:
        raise MutationAdmissionError("mutation_valid_time_order_invalid")
    payload = envelope["payload"]
    if operation in {"add", "update"}:
        body = _mapping(payload, "mutation_payload")
        _require_keys(
            body,
            {"kind", "statement", "confidence", "importance", "aliases", "tags", "negative_triggers"},
            "mutation_payload",
        )
        enums = _mapping(policy["record_enums"], "record_enums")
        if body.get("kind") not in enums["kind"]:
            raise MutationAdmissionError("mutation_kind_invalid")
        if body.get("confidence") not in enums["confidence"] or body.get("importance") not in enums["importance"]:
            raise MutationAdmissionError("mutation_rank_invalid")
        statement = body.get("statement")
        statement_max = int(_mapping(policy["limits"], "limits")["statement_max_bytes"])
        if not isinstance(statement, str) or not statement or len(statement.encode("utf-8")) > statement_max:
            raise MutationAdmissionError("mutation_statement_invalid")
        maximum = int(_mapping(policy["limits"], "limits")["list_items_max"])
        for key in ("aliases", "tags", "negative_triggers"):
            _string_list(body.get(key), f"mutation_{key}", maximum)
        try:
            validate_negative_boundary_payload(
                kind=body.get("kind"),
                source_type=source.get("type"),
                negative_triggers=body.get("negative_triggers"),
            )
        except ForgettingError as exc:
            raise MutationAdmissionError(str(exc)) from exc
    elif payload is not None:
        raise MutationAdmissionError("mutation_payload_must_be_null")

    classification = sensitivity.get("classification")
    if classification not in _mapping(policy["record_enums"], "record_enums")["sensitivity"]:
        raise MutationAdmissionError("mutation_sensitivity_invalid")
    expected_handling = "public_text" if classification == "public" else "redacted_summary"
    if (
        sensitivity.get("handling") != expected_handling
        or sensitivity.get("credential_present") is not False
        or sensitivity.get("public_repository_allowed") is not True
    ):
        raise MutationAdmissionError("mutation_sensitivity_boundary_invalid")
    if not isinstance(envelope["reason"], str) or not envelope["reason"] or len(envelope["reason"]) > 512:
        raise MutationAdmissionError("mutation_reason_invalid")
    assert_no_credentials(
        json.dumps(dict(envelope), ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        "mutation_envelope",
    )


def _rehash(record: dict[str, Any]) -> dict[str, Any]:
    record["hash"] = {
        "algorithm": "sha256",
        "canonicalization": RECORD_HASH_CANONICALIZATION,
        "value": record_hash(record),
    }
    validate_record(record)
    return record


def _new_record_id(idempotency_key: str) -> str:
    return "mem_" + hashlib.sha256(idempotency_key.encode("utf-8")).hexdigest()[:24]


def _transaction_id(idempotency_key: str) -> str:
    return "mut_" + hashlib.sha256(idempotency_key.encode("utf-8")).hexdigest()[:20]


def _new_record(envelope: Mapping[str, Any], policy: Mapping[str, Any], record_id: str) -> dict[str, Any]:
    source = dict(envelope["source"])
    authorization = dict(envelope["authorization"])
    payload = dict(envelope["payload"])
    source_rule = policy["source_requirements"][source["type"]]
    evidence_refs = sorted({source["ref"], authorization["ref"]})
    record = {
        "schema_version": "openai_database.memory_record.v2",
        "id": record_id,
        "memory_key": envelope["target"]["memory_key"],
        "kind": payload["kind"],
        "statement": payload["statement"],
        "status": "active",
        "scope": dict(envelope["target"]["scope"]),
        "source": source,
        "valid_time": dict(envelope["valid_time"]),
        "recorded_time": {
            "recorded_at": authorization["authorized_at"],
            "recorded_by": source_rule["recorded_by"],
            "transitions": [],
        },
        "supersession": {"supersedes": [], "superseded_by": None, "reason": envelope["reason"]},
        "conflict": {"state": "none", "with": [], "resolution": None},
        "confidence": payload["confidence"],
        "importance": payload["importance"],
        "verification": {
            "state": "verified",
            "method": source_rule["verification_method"],
            "evidence_refs": evidence_refs,
            "verified_at": authorization["authorized_at"],
            "rationale": envelope["reason"],
        },
        "aliases": sorted(payload["aliases"]),
        "tags": sorted(payload["tags"]),
        "negative_triggers": sorted(payload["negative_triggers"]),
        "sensitivity": dict(envelope["sensitivity"]),
        "hash": {},
    }
    return _rehash(record)


def _target(index: Mapping[str, dict[str, Any]], envelope: Mapping[str, Any]) -> dict[str, Any]:
    record_id = str(envelope["target"]["record_id"])
    if record_id not in index:
        raise MutationAdmissionError("mutation_target_not_found")
    record = index[record_id]
    if (
        record["memory_key"] != envelope["target"]["memory_key"]
        or record["scope"] != envelope["target"]["scope"]
    ):
        raise MutationAdmissionError("mutation_target_identity_mismatch")
    return record


def _require_later_than_target(envelope: Mapping[str, Any], target: Mapping[str, Any]) -> None:
    if _timestamp(envelope["valid_time"]["from"], "mutation_valid_from") <= _timestamp(
        target["valid_time"]["from"], "target_valid_from"
    ):
        raise MutationAdmissionError("mutation_valid_from_not_after_target")


def build_outcome(
    records: Sequence[Mapping[str, Any]],
    envelope: Mapping[str, Any],
    policy: Mapping[str, Any],
    *,
    current_base_sha: str,
) -> dict[str, Any]:
    validate_envelope(envelope, policy, current_base_sha=current_base_sha)
    candidate = [copy.deepcopy(dict(record)) for record in records]
    index = {str(record["id"]): record for record in candidate}
    operation = str(envelope["operation"])
    generated_id = _new_record_id(str(envelope["idempotency_key"]))
    transaction_id = _transaction_id(str(envelope["idempotency_key"]))
    changed_ids: list[str] = []
    idempotent = False

    if operation == "add":
        expected = _new_record(envelope, policy, generated_id)
        if generated_id in index:
            if index[generated_id] != expected:
                raise MutationAdmissionError("mutation_idempotency_record_collision")
            idempotent = True
        else:
            key = (expected["memory_key"], expected["scope"]["type"], expected["scope"]["key"])
            existing = next(
                (
                    record
                    for record in candidate
                    if record["status"] == "active"
                    and (record["memory_key"], record["scope"]["type"], record["scope"]["key"]) == key
                ),
                None,
            )
            if existing is not None:
                classification = classify_pair(existing, expected)
                if classification == "exact_duplicate":
                    raise MutationAdmissionError("mutation_exact_duplicate_use_existing")
                if classification == "normalized_duplicate":
                    raise MutationAdmissionError("mutation_normalized_duplicate_use_existing")
                raise MutationAdmissionError("mutation_active_target_exists_use_update")
            candidate.append(expected)
            changed_ids.append(generated_id)
    else:
        target = _target(index, envelope)
        target_id = str(target["id"])
        if operation == "update":
            expected = _new_record(envelope, policy, generated_id)
            if normalize_statement(expected["statement"]) == normalize_statement(target["statement"]):
                raise MutationAdmissionError("mutation_update_has_no_new_fact")
            expected["supersession"]["supersedes"] = [target_id]
            _rehash(expected)
            if generated_id in index:
                if (
                    index[generated_id] != expected
                    or target["status"] != "retired"
                    or target["supersession"]["superseded_by"] != generated_id
                    or not target["recorded_time"].get("transitions")
                    or target["recorded_time"]["transitions"][-1]["transaction_id"] != transaction_id
                ):
                    raise MutationAdmissionError("mutation_idempotency_record_collision")
                idempotent = True
            else:
                if target["status"] != "active":
                    raise MutationAdmissionError("mutation_update_target_not_active")
                _require_later_than_target(envelope, target)
                source_rule = policy["source_requirements"][envelope["source"]["type"]]
                append_transition(
                    target,
                    transaction_id=transaction_id,
                    operation="update",
                    recorded_at=envelope["authorization"]["authorized_at"],
                    recorded_by=source_rule["recorded_by"],
                    to_status="retired",
                    valid_to_after=envelope["valid_time"]["from"],
                    reason=envelope["reason"],
                )
                target["supersession"]["superseded_by"] = generated_id
                target["supersession"]["reason"] = envelope["reason"]
                _rehash(target)
                candidate.append(expected)
                changed_ids.extend([target_id, generated_id])
        elif operation == "retire":
            transitions = target["recorded_time"].get("transitions", [])
            if (
                target["status"] == "retired"
                and target["valid_time"]["to"] == envelope["valid_time"]["from"]
                and transitions
                and transitions[-1]["transaction_id"] == transaction_id
            ):
                idempotent = True
            else:
                if target["status"] == "retired":
                    raise MutationAdmissionError("mutation_target_already_retired")
                _require_later_than_target(envelope, target)
                source_rule = policy["source_requirements"][envelope["source"]["type"]]
                append_transition(
                    target,
                    transaction_id=transaction_id,
                    operation="retire",
                    recorded_at=envelope["authorization"]["authorized_at"],
                    recorded_by=source_rule["recorded_by"],
                    to_status="retired",
                    valid_to_after=envelope["valid_time"]["from"],
                    reason=envelope["reason"],
                )
                target["supersession"]["reason"] = envelope["reason"]
                _rehash(target)
                changed_ids.append(target_id)
        else:
            transitions = target["recorded_time"].get("transitions", [])
            if target["status"] == "disputed" and target["conflict"]["state"] == "unresolved":
                if transitions and transitions[-1]["transaction_id"] == transaction_id:
                    idempotent = True
                else:
                    raise MutationAdmissionError("mutation_target_already_disputed")
            else:
                if target["status"] == "retired":
                    raise MutationAdmissionError("mutation_dispute_target_retired")
                source_rule = policy["source_requirements"][envelope["source"]["type"]]
                append_transition(
                    target,
                    transaction_id=transaction_id,
                    operation="dispute",
                    recorded_at=envelope["authorization"]["authorized_at"],
                    recorded_by=source_rule["recorded_by"],
                    to_status="disputed",
                    valid_to_after=target["valid_time"]["to"],
                    reason=envelope["reason"],
                )
                target["conflict"] = {
                    "state": "unresolved",
                    "with": sorted(target["conflict"]["with"]),
                    "resolution": None,
                }
                _rehash(target)
                changed_ids.append(target_id)

    candidate = sorted(candidate, key=lambda record: str(record["id"]))
    for record in candidate:
        validate_record(record)
    validate_dataset(candidate)
    lifecycle = assess_lifecycle(candidate)
    envelope_sha256 = sha256_prefixed(canonical_json_bytes(envelope))
    statement = envelope["payload"]["statement"] if envelope["payload"] is not None else None
    statement_sha256 = None if statement is None else sha256_prefixed(statement.encode("utf-8"))
    pr_material = {
        "schema_version": "openai_database.memory_mutation_pr_plan.v1",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "transaction_id": transaction_id,
        "operation": operation,
        "idempotency_key": envelope["idempotency_key"],
        "base_commit_sha": envelope["base_commit_sha"],
        "actor": envelope["actor"],
        "source": envelope["source"],
        "authorization": envelope["authorization"],
        "target": envelope["target"],
        "valid_time": envelope["valid_time"],
        "envelope_sha256": envelope_sha256,
        "statement_sha256": statement_sha256,
    }
    automation = policy["automation_c"]
    details = {
        **pr_material,
        "record_id": generated_id if operation in {"add", "update"} else envelope["target"]["record_id"],
        "changed_record_ids": sorted(changed_ids),
        "candidate_record_count": len(candidate),
        "idempotent_replay": idempotent,
        "model_inference_persisted": 0,
        "manual_approval_required": False,
        "lifecycle": lifecycle,
        "automation_c": {
            "transaction_required": not idempotent,
            "branch": str(automation["branch_prefix"]) + transaction_id,
            "base_branch": automation["base_branch"],
            "same_repository_only": True,
            "non_draft_pr_count": 1,
            "issue_mutations": 0,
            "direct_main_write": False,
            "required_ci": automation["required_ci"],
            "settlement": automation["settlement"],
            "terminal_state": automation["terminal_state"],
            "pr_body_material_sha256": sha256_prefixed(canonical_json_bytes(pr_material)),
            "live_transaction_glue_task": policy["publication_boundary"]["candidate_transaction_only_until"],
            "settlement_allowed": lifecycle["settlement_allowed"],
            "lifecycle_acceptance_id": "ACC.OpenAIDatabase.PAM1.0010",
        },
    }
    return {"records": candidate, "details": details}


def validate_transaction_branch(database_dir: Path, expected_branch: str) -> None:
    result = subprocess.run(
        ["git", "-C", str(database_dir), "symbolic-ref", "--quiet", "--short", "HEAD"],
        text=True,
        capture_output=True,
        check=False,
    )
    branch = result.stdout.strip()
    if result.returncode != 0 or branch != expected_branch or branch == "main":
        raise MutationAdmissionError("mutation_apply_requires_exact_automation_c_branch")
