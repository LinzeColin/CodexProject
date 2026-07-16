#!/usr/bin/env python3
"""Deterministic duplicate, conflict and bitemporal lifecycle rules."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping, MutableMapping, Sequence


TASK_ID = "TSK.OpenAIDatabase.PAM1.0010"
ACCEPTANCE_ID = "ACC.OpenAIDatabase.PAM1.0010"
POLICY_SCHEMA_VERSION = "openai_database.memory_lifecycle_policy.v1"
CLASSIFICATIONS = (
    "exact_duplicate",
    "normalized_duplicate",
    "overlapping_validity_conflict",
    "same_key_conflict",
)
STATUSES = {"candidate", "active", "disputed", "retired"}
RECORDED_BY = {"explicit_user", "automation_c", "importer", "migration"}
TRANSITION_OPERATIONS = {"update", "retire", "dispute"}
TRANSACTION_RE = re.compile(r"^mut_[a-f0-9]{20}$")
TRANSITION_KEYS = {
    "transaction_id",
    "operation",
    "recorded_at",
    "recorded_by",
    "from_status",
    "to_status",
    "valid_to_before",
    "valid_to_after",
    "reason",
}


class LifecycleError(ValueError):
    """Stable lifecycle failure code without statement content."""


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise LifecycleError(f"{label}_must_be_object")
    return value


def _no_duplicate_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key, value in pairs:
        if key in output:
            raise LifecycleError("lifecycle_policy_duplicate_json_key")
        output[key] = value
    return output


def load_policy(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_no_duplicate_object)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise LifecycleError("lifecycle_policy_invalid") from exc
    policy = dict(_mapping(value, "lifecycle_policy"))
    validate_policy(policy)
    return policy


def validate_policy(policy: Mapping[str, Any]) -> None:
    expected = {
        "schema_version",
        "task_id",
        "acceptance_id",
        "normalization",
        "classification_order",
        "identity_fields",
        "valid_time",
        "recorded_time",
        "settlement",
        "legacy",
    }
    if set(policy) != expected:
        raise LifecycleError("lifecycle_policy_fields_invalid")
    if (
        policy["schema_version"] != POLICY_SCHEMA_VERSION
        or policy["task_id"] != TASK_ID
        or policy["acceptance_id"] != ACCEPTANCE_ID
    ):
        raise LifecycleError("lifecycle_policy_identity_drift")
    normalization = _mapping(policy["normalization"], "normalization")
    if normalization != {
        "unicode": "NFKC",
        "case": "casefold",
        "whitespace": "collapse_unicode_whitespace",
        "punctuation": "preserve",
        "embedding_as_unique_decision": False,
    }:
        raise LifecycleError("lifecycle_normalization_policy_drift")
    if tuple(policy["classification_order"]) != CLASSIFICATIONS:
        raise LifecycleError("lifecycle_classification_order_drift")
    if policy["identity_fields"] != ["memory_key", "scope.type", "scope.key"]:
        raise LifecycleError("lifecycle_identity_policy_drift")
    valid_time = _mapping(policy["valid_time"], "valid_time_policy")
    recorded_time = _mapping(policy["recorded_time"], "recorded_time_policy")
    settlement = _mapping(policy["settlement"], "settlement_policy")
    if valid_time.get("interval") != "half_open" or valid_time.get("as_of_axis") != "valid_time":
        raise LifecycleError("lifecycle_valid_time_policy_drift")
    if (
        recorded_time.get("audit_axis") != "recorded_time"
        or recorded_time.get("transition_log") != "recorded_time.transitions"
        or recorded_time.get("recorded_as_of_requires_valid_as_of") is not True
    ):
        raise LifecycleError("lifecycle_recorded_time_policy_drift")
    if (
        settlement.get("active_duplicate_conflict_max") != 0
        or settlement.get("unresolved_conflict") != "block"
        or settlement.get("embedding_only_resolution") != "forbidden"
        or settlement.get("uncertain_resolution") != "abstain"
    ):
        raise LifecycleError("lifecycle_settlement_policy_drift")


def parse_rfc3339(value: Any, label: str = "timestamp") -> datetime:
    if not isinstance(value, str) or not value:
        raise LifecycleError(f"{label}_invalid")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise LifecycleError(f"{label}_invalid") from exc
    if parsed.tzinfo is None:
        raise LifecycleError(f"{label}_invalid")
    return parsed


def normalize_statement(value: Any) -> str:
    if not isinstance(value, str) or not value:
        raise LifecycleError("lifecycle_statement_invalid")
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return " ".join(normalized.split())


def statement_fingerprint(value: Any) -> str:
    return "sha256:" + hashlib.sha256(normalize_statement(value).encode("utf-8")).hexdigest()


def record_identity(record: Mapping[str, Any]) -> tuple[str, str, str]:
    scope = _mapping(record.get("scope"), "lifecycle_scope")
    return str(record.get("memory_key")), str(scope.get("type")), str(scope.get("key"))


def _valid_interval(record: Mapping[str, Any]) -> tuple[datetime, datetime | None]:
    valid_time = _mapping(record.get("valid_time"), "lifecycle_valid_time")
    start = parse_rfc3339(valid_time.get("from"), "lifecycle_valid_from")
    end_raw = valid_time.get("to")
    end = None if end_raw is None else parse_rfc3339(end_raw, "lifecycle_valid_to")
    if end is not None and end <= start:
        raise LifecycleError("lifecycle_valid_interval_invalid")
    return start, end


def intervals_overlap(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    left_start, left_end = _valid_interval(left)
    right_start, right_end = _valid_interval(right)
    return (right_end is None or left_start < right_end) and (left_end is None or right_start < left_end)


def _linked(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    left_id = str(left.get("id"))
    right_id = str(right.get("id"))
    left_supersession = _mapping(left.get("supersession"), "lifecycle_supersession")
    right_supersession = _mapping(right.get("supersession"), "lifecycle_supersession")
    left_conflict = _mapping(left.get("conflict"), "lifecycle_conflict")
    right_conflict = _mapping(right.get("conflict"), "lifecycle_conflict")
    return any(
        (
            right_id in left_supersession.get("supersedes", []),
            left_supersession.get("superseded_by") == right_id,
            left_id in right_supersession.get("supersedes", []),
            right_supersession.get("superseded_by") == left_id,
            right_id in left_conflict.get("with", []),
            left_id in right_conflict.get("with", []),
        )
    )


def classify_pair(left: Mapping[str, Any], right: Mapping[str, Any]) -> str | None:
    if str(left.get("id")) == str(right.get("id")) or record_identity(left) != record_identity(right):
        return None
    if not intervals_overlap(left, right):
        return None
    same_kind = left.get("kind") == right.get("kind")
    if same_kind and left.get("statement") == right.get("statement"):
        return "exact_duplicate"
    if same_kind and normalize_statement(left.get("statement")) == normalize_statement(right.get("statement")):
        return "normalized_duplicate"
    if _linked(left, right):
        return "overlapping_validity_conflict"
    return "same_key_conflict"


def _transition_rows(record: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    recorded = _mapping(record.get("recorded_time"), "lifecycle_recorded_time")
    value = recorded.get("transitions", [])
    if not isinstance(value, list):
        raise LifecycleError("lifecycle_transitions_invalid")
    return [_mapping(row, "lifecycle_transition") for row in value]


def _validate_transition_history(record: Mapping[str, Any]) -> None:
    start, current_end = _valid_interval(record)
    recorded = _mapping(record.get("recorded_time"), "lifecycle_recorded_time")
    created_at = parse_rfc3339(recorded.get("recorded_at"), "lifecycle_recorded_at")
    rows = _transition_rows(record)
    previous_at: datetime | None = None
    previous_status: str | None = None
    previous_end: Any = None
    for index, row in enumerate(rows):
        if set(row) != TRANSITION_KEYS:
            raise LifecycleError("lifecycle_transition_fields_invalid")
        transaction_id = row.get("transaction_id")
        operation = row.get("operation")
        from_status = row.get("from_status")
        to_status = row.get("to_status")
        if not isinstance(transaction_id, str) or TRANSACTION_RE.fullmatch(transaction_id) is None:
            raise LifecycleError("lifecycle_transition_transaction_invalid")
        if operation not in TRANSITION_OPERATIONS or from_status not in STATUSES or to_status not in STATUSES:
            raise LifecycleError("lifecycle_transition_state_invalid")
        if row.get("recorded_by") not in RECORDED_BY:
            raise LifecycleError("lifecycle_transition_actor_invalid")
        at = parse_rfc3339(row.get("recorded_at"), "lifecycle_transition_recorded_at")
        if at < created_at or (previous_at is not None and at <= previous_at):
            raise LifecycleError("lifecycle_transition_order_invalid")
        for name in ("valid_to_before", "valid_to_after"):
            value = row.get(name)
            if value is not None and parse_rfc3339(value, f"lifecycle_transition_{name}") <= start:
                raise LifecycleError("lifecycle_transition_validity_invalid")
        if index and (from_status != previous_status or row.get("valid_to_before") != previous_end):
            raise LifecycleError("lifecycle_transition_chain_invalid")
        if operation in {"update", "retire"} and to_status != "retired":
            raise LifecycleError("lifecycle_retirement_transition_invalid")
        if operation == "dispute" and to_status != "disputed":
            raise LifecycleError("lifecycle_dispute_transition_invalid")
        if not isinstance(row.get("reason"), str) or not row["reason"]:
            raise LifecycleError("lifecycle_transition_reason_invalid")
        previous_at = at
        previous_status = str(to_status)
        previous_end = row.get("valid_to_after")
    if rows and (previous_status != record.get("status") or previous_end != record["valid_time"]["to"]):
        raise LifecycleError("lifecycle_transition_final_state_drift")
    if current_end is not None and current_end <= start:
        raise LifecycleError("lifecycle_valid_interval_invalid")


def _validate_graph(records: Sequence[Mapping[str, Any]]) -> None:
    index = {str(record.get("id")): record for record in records}
    successor: dict[str, str] = {}
    for record in records:
        record_id = str(record.get("id"))
        supersession = _mapping(record.get("supersession"), "lifecycle_supersession")
        superseded_by = supersession.get("superseded_by")
        if superseded_by is not None:
            other = index.get(str(superseded_by))
            if other is None or record_id not in _mapping(other["supersession"], "lifecycle_supersession").get(
                "supersedes", []
            ):
                raise LifecycleError("lifecycle_supersession_not_bidirectional")
            if record_identity(record) != record_identity(other):
                raise LifecycleError("lifecycle_supersession_identity_drift")
            if record.get("status") != "retired" or record["valid_time"]["to"] != other["valid_time"]["from"]:
                raise LifecycleError("lifecycle_supersession_boundary_invalid")
            successor[record_id] = str(superseded_by)
        for old_id in supersession.get("supersedes", []):
            old = index.get(str(old_id))
            if old is None or _mapping(old["supersession"], "lifecycle_supersession").get(
                "superseded_by"
            ) != record_id:
                raise LifecycleError("lifecycle_supersession_not_bidirectional")
        conflict = _mapping(record.get("conflict"), "lifecycle_conflict")
        for other_id in conflict.get("with", []):
            other = index.get(str(other_id))
            if other is None or record_id not in _mapping(other["conflict"], "lifecycle_conflict").get("with", []):
                raise LifecycleError("lifecycle_conflict_not_bidirectional")
    for record_id in successor:
        seen: set[str] = set()
        cursor: str | None = record_id
        while cursor is not None:
            if cursor in seen:
                raise LifecycleError("lifecycle_supersession_cycle")
            seen.add(cursor)
            cursor = successor.get(cursor)


def assess_lifecycle(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    ordered = sorted(records, key=lambda row: str(row.get("id")))
    for index, left in enumerate(ordered):
        for right in ordered[index + 1 :]:
            classification = classify_pair(left, right)
            if classification is None:
                continue
            counts[classification] += 1
            findings.append(
                {
                    "classification": classification,
                    "record_ids": [str(left.get("id")), str(right.get("id"))],
                    "identity_sha256": "sha256:"
                    + hashlib.sha256("\0".join(record_identity(left)).encode("utf-8")).hexdigest(),
                    "statement_fingerprints": sorted(
                        {statement_fingerprint(left.get("statement")), statement_fingerprint(right.get("statement"))}
                    ),
                }
            )
    active_groups = Counter(record_identity(record) for record in ordered if record.get("status") == "active")
    active_duplicate_conflict_count = sum(max(0, count - 1) for count in active_groups.values())
    unresolved = sorted(
        str(record.get("id"))
        for record in ordered
        if _mapping(record.get("conflict"), "lifecycle_conflict").get("state") == "unresolved"
    )
    blocker_count = len(findings) + len(unresolved) + active_duplicate_conflict_count
    return {
        "schema_version": "openai_database.memory_lifecycle_assessment.v1",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "record_count": len(ordered),
        "classification_counts": {name: counts[name] for name in CLASSIFICATIONS},
        "active_duplicate_conflict_count": active_duplicate_conflict_count,
        "unresolved_conflict_ids": unresolved,
        "settlement_blocker_count": blocker_count,
        "settlement_allowed": blocker_count == 0,
        "embedding_decision_count": 0,
        "findings": findings,
    }


def validate_lifecycle_dataset(records: Sequence[Mapping[str, Any]]) -> None:
    for record in records:
        _validate_transition_history(record)
    _validate_graph(records)
    index = {str(record.get("id")): record for record in records}
    assessment = assess_lifecycle(records)
    for finding in assessment["findings"]:
        classification = finding["classification"]
        left, right = (index[record_id] for record_id in finding["record_ids"])
        if classification in {"exact_duplicate", "normalized_duplicate", "overlapping_validity_conflict"}:
            raise LifecycleError(f"lifecycle_{classification}")
        represented = (
            left.get("status") == right.get("status") == "disputed"
            and left["conflict"]["state"] == right["conflict"]["state"] == "unresolved"
            and str(right["id"]) in left["conflict"]["with"]
            and str(left["id"]) in right["conflict"]["with"]
        )
        if not represented:
            raise LifecycleError("lifecycle_same_key_conflict_unrepresented")


def append_transition(
    record: MutableMapping[str, Any],
    *,
    transaction_id: str,
    operation: str,
    recorded_at: str,
    recorded_by: str,
    to_status: str,
    valid_to_after: str | None,
    reason: str,
) -> None:
    recorded = record.get("recorded_time")
    if not isinstance(recorded, MutableMapping):
        raise LifecycleError("lifecycle_recorded_time_not_mutable")
    transitions = recorded.setdefault("transitions", [])
    if not isinstance(transitions, list):
        raise LifecycleError("lifecycle_transitions_invalid")
    transition = {
        "transaction_id": transaction_id,
        "operation": operation,
        "recorded_at": recorded_at,
        "recorded_by": recorded_by,
        "from_status": record["status"],
        "to_status": to_status,
        "valid_to_before": record["valid_time"]["to"],
        "valid_to_after": valid_to_after,
        "reason": reason,
    }
    transitions.append(transition)
    record["status"] = to_status
    record["valid_time"]["to"] = valid_to_after
    _validate_transition_history(record)


def project_record_at(
    record: Mapping[str, Any],
    *,
    recorded_as_of: datetime | None,
    record_index: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    recorded = _mapping(record.get("recorded_time"), "lifecycle_recorded_time")
    created_at = parse_rfc3339(recorded.get("recorded_at"), "lifecycle_recorded_at")
    if recorded_as_of is not None and recorded_as_of < created_at:
        return {"visible": False, "status": None, "valid_to": None, "audit_complete": True}
    status = str(record.get("status"))
    valid_to = record["valid_time"]["to"]
    rows = _transition_rows(record)
    if recorded_as_of is not None and rows:
        for row in reversed(rows):
            if parse_rfc3339(row["recorded_at"], "lifecycle_transition_recorded_at") > recorded_as_of:
                status = str(row["from_status"])
                valid_to = row["valid_to_before"]
    audit_complete = True
    if recorded_as_of is not None and not rows and status == "retired":
        successor_id = _mapping(record.get("supersession"), "lifecycle_supersession").get("superseded_by")
        successor = record_index.get(str(successor_id)) if successor_id is not None else None
        if successor is None:
            audit_complete = False
        else:
            successor_at = parse_rfc3339(
                successor["recorded_time"]["recorded_at"],
                "lifecycle_successor_recorded_at",
            )
            if recorded_as_of < successor_at:
                status = "active"
                valid_to = None
    return {"visible": True, "status": status, "valid_to": valid_to, "audit_complete": audit_complete}


def projection_is_effective(record: Mapping[str, Any], projection: Mapping[str, Any], valid_as_of: datetime) -> bool:
    start = parse_rfc3339(record["valid_time"]["from"], "lifecycle_valid_from")
    end_raw = projection.get("valid_to")
    end = None if end_raw is None else parse_rfc3339(end_raw, "lifecycle_valid_to")
    return bool(projection.get("visible")) and start <= valid_as_of and (end is None or valid_as_of < end)
