#!/usr/bin/env python3
"""Deterministic public-safe audit, recovery, and metadata-health kernel.

The kernel is intentionally in-memory and filesystem independent.  Synthetic
fixtures prove append-only events, approved-version recovery, and fail-closed
metadata health without reading raw data or claiming a production restore.
"""

from __future__ import annotations

import base64
import copy
import hashlib
import json
from collections import Counter
from typing import Any, Iterable, Mapping, Sequence


RUN_PHASE_ID = "V015_S04_P3_AUDIT_RECOVERY"
TASK_ID = "KMFA-V015-S04-P3-AUDIT-RECOVERY-20260714"
ACCEPTANCE_ID = "ACC-KMFA-V015-S04-P3-AUDIT-RECOVERY"
VERSION = "1.5.0-dev-s04p3"

ACTION_TYPES = (
    "IMPORT",
    "MAPPING",
    "HUMAN_CONFIRMATION",
    "PARAMETER_ADJUSTMENT",
    "RECALCULATION",
    "PUBLICATION",
)
SNAPSHOT_SUBJECT_TYPES = ("CRITICAL_FACT", "PUBLISHED_REPORT")
RESTORE_VALIDATION_DIMENSIONS = (
    "PAYLOAD_DIGEST_MATCH",
    "VERSION_IDENTITY_MATCH",
    "DEPENDENCY_SET_COMPLETE",
)
HEALTH_FINDING_TYPES = (
    "ORPHAN_RECORD",
    "BROKEN_LINK",
    "DUPLICATE_VERSION",
    "UNCLOSED_EVENT",
)


class AuditRecoveryError(ValueError):
    """Raised when an audit, restore, or health invariant fails closed."""


def _required_text(value: Any, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise AuditRecoveryError(f"{field} is required")
    return text


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _digest_token(value: Any) -> str:
    digest = hashlib.sha256(_canonical_bytes(value)).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def _event_digest(event: Mapping[str, Any]) -> str:
    return _digest_token({key: value for key, value in event.items() if key != "event_digest"})


class AppendOnlyEventLog:
    """In-memory event log with defensive copies and an integrity chain."""

    def __init__(self) -> None:
        self._events: list[dict[str, Any]] = []

    def append(
        self,
        *,
        action_type: str,
        occurred_at: str,
        actor_role: str,
        subject_ref: str,
        payload_ref: str,
        reason_code: str,
        correction_of_event_id: str | None = None,
        correction_reason: str | None = None,
        requires_closure: bool = False,
        closes_event_id: str | None = None,
    ) -> dict[str, Any]:
        if action_type not in ACTION_TYPES:
            raise AuditRecoveryError(f"unsupported action_type: {action_type}")
        if not _required_text(subject_ref, "subject_ref").startswith("SUBJECT::"):
            raise AuditRecoveryError("subject_ref must be an opaque SUBJECT reference")
        if not _required_text(payload_ref, "payload_ref").startswith("PAYLOAD::"):
            raise AuditRecoveryError("payload_ref must be an opaque PAYLOAD reference")
        existing = {event["event_id"]: event for event in self._events}
        if correction_of_event_id is not None:
            if correction_of_event_id not in existing:
                raise AuditRecoveryError("correction must reference an existing event")
            _required_text(correction_reason, "correction_reason")
        elif correction_reason is not None:
            raise AuditRecoveryError("correction_reason requires correction_of_event_id")
        if closes_event_id is not None:
            target = existing.get(closes_event_id)
            if target is None or target.get("requires_closure") is not True:
                raise AuditRecoveryError("closure must reference an open closure-required event")
            if any(event.get("closes_event_id") == closes_event_id for event in self._events):
                raise AuditRecoveryError("closure-required event is already closed")
        sequence = len(self._events) + 1
        event = {
            "schema_version": "kmfa.v015.s04p3.audit_event.v1",
            "event_id": f"EVENT-S04P3-SYN-{sequence:03d}",
            "sequence": sequence,
            "event_kind": "CORRECTION" if correction_of_event_id else "PRIMARY",
            "action_type": action_type,
            "occurred_at": _required_text(occurred_at, "occurred_at"),
            "actor_role": _required_text(actor_role, "actor_role"),
            "subject_ref": subject_ref,
            "payload_ref": payload_ref,
            "reason_code": _required_text(reason_code, "reason_code"),
            "correction_of_event_id": correction_of_event_id,
            "correction_reason": correction_reason,
            "requires_closure": bool(requires_closure),
            "closes_event_id": closes_event_id,
            "previous_event_digest": (
                self._events[-1]["event_digest"] if self._events else "GENESIS"
            ),
            "digest_algorithm": "SHA-256",
            "event_digest": "",
            "append_only": True,
            "in_place_update_allowed": False,
            "synthetic_fixture": True,
            "contains_raw_business_value": False,
        }
        event["event_digest"] = _event_digest(event)
        self._events.append(copy.deepcopy(event))
        return copy.deepcopy(event)

    def events(self) -> list[dict[str, Any]]:
        return copy.deepcopy(self._events)

    def replace_event(self, *_: Any, **__: Any) -> None:
        raise AuditRecoveryError("in-place event replacement is forbidden; append a correction event")


def validate_event_chain(events: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    if not events:
        raise AuditRecoveryError("event chain must not be empty")
    known_ids: set[str] = set()
    action_types: set[str] = set()
    correction_count = 0
    closure_targets: set[str] = set()
    closure_required: set[str] = set()
    previous_digest = "GENESIS"
    for expected_sequence, source in enumerate(events, start=1):
        event = dict(source)
        event_id = _required_text(event.get("event_id"), "event_id")
        if event_id in known_ids:
            raise AuditRecoveryError("event_id must be unique")
        if event.get("sequence") != expected_sequence:
            raise AuditRecoveryError("event sequence is not contiguous")
        if event.get("previous_event_digest") != previous_digest:
            raise AuditRecoveryError("event chain previous digest mismatch")
        if event.get("event_digest") != _event_digest(event):
            raise AuditRecoveryError("event digest mismatch")
        action_type = _required_text(event.get("action_type"), "action_type")
        if action_type not in ACTION_TYPES:
            raise AuditRecoveryError("event contains unsupported action type")
        action_types.add(action_type)
        if event.get("append_only") is not True or event.get("in_place_update_allowed") is not False:
            raise AuditRecoveryError("event append-only flags are invalid")
        if event.get("contains_raw_business_value") is not False:
            raise AuditRecoveryError("public audit events cannot contain raw business values")
        if not _required_text(event.get("subject_ref"), "subject_ref").startswith("SUBJECT::"):
            raise AuditRecoveryError("event subject_ref must be opaque")
        if not _required_text(event.get("payload_ref"), "payload_ref").startswith("PAYLOAD::"):
            raise AuditRecoveryError("event payload_ref must be opaque")
        correction_target = event.get("correction_of_event_id")
        if correction_target is not None:
            if correction_target not in known_ids:
                raise AuditRecoveryError("correction target must precede correction event")
            _required_text(event.get("correction_reason"), "correction_reason")
            if event.get("event_kind") != "CORRECTION":
                raise AuditRecoveryError("correction event kind mismatch")
            correction_count += 1
        elif event.get("event_kind") != "PRIMARY":
            raise AuditRecoveryError("primary event kind mismatch")
        if event.get("requires_closure") is True:
            closure_required.add(event_id)
        closes = event.get("closes_event_id")
        if closes is not None:
            if closes not in closure_required or closes in closure_targets:
                raise AuditRecoveryError("closure link is invalid or duplicated")
            closure_targets.add(str(closes))
        known_ids.add(event_id)
        previous_digest = str(event["event_digest"])
    return {
        "event_count": len(events),
        "action_type_count": len(action_types),
        "action_types_covered": sorted(action_types),
        "correction_event_count": correction_count,
        "closure_required_event_count": len(closure_required),
        "closed_event_count": len(closure_targets),
        "unclosed_event_ids": sorted(closure_required - closure_targets),
        "chain_valid": True,
        "in_place_update_allowed": False,
    }


def synthetic_event_log() -> list[dict[str, Any]]:
    log = AppendOnlyEventLog()
    common = {
        "actor_role": "ROLE::SYNTHETIC-CONTROL-OPERATOR",
        "subject_ref": "SUBJECT::SYNTHETIC-MANAGEMENT-REPORT",
    }
    log.append(
        action_type="IMPORT", occurred_at="2026-07-14T10:00:00+10:00",
        payload_ref="PAYLOAD::SYNTHETIC-IMPORT-V1", reason_code="SYNTHETIC_IMPORT", **common,
    )
    mapping = log.append(
        action_type="MAPPING", occurred_at="2026-07-14T10:01:00+10:00",
        payload_ref="PAYLOAD::SYNTHETIC-MAPPING-V1", reason_code="SYNTHETIC_MAPPING", **common,
    )
    log.append(
        action_type="HUMAN_CONFIRMATION", occurred_at="2026-07-14T10:02:00+10:00",
        payload_ref="PAYLOAD::SYNTHETIC-CONFIRMATION-V1", reason_code="SYNTHETIC_CONFIRMATION", **common,
    )
    log.append(
        action_type="PARAMETER_ADJUSTMENT", occurred_at="2026-07-14T10:03:00+10:00",
        payload_ref="PAYLOAD::SYNTHETIC-PARAMETER-V1", reason_code="SYNTHETIC_PARAMETER", **common,
    )
    recalculation = log.append(
        action_type="RECALCULATION", occurred_at="2026-07-14T10:04:00+10:00",
        payload_ref="PAYLOAD::SYNTHETIC-RECALCULATION-V1", reason_code="SYNTHETIC_RECALCULATION",
        requires_closure=True, **common,
    )
    log.append(
        action_type="PUBLICATION", occurred_at="2026-07-14T10:05:00+10:00",
        payload_ref="PAYLOAD::SYNTHETIC-PUBLICATION-V1", reason_code="SYNTHETIC_PUBLICATION",
        closes_event_id=recalculation["event_id"], **common,
    )
    log.append(
        action_type="MAPPING", occurred_at="2026-07-14T10:06:00+10:00",
        payload_ref="PAYLOAD::SYNTHETIC-MAPPING-CORRECTION-V2", reason_code="SYNTHETIC_CORRECTION",
        correction_of_event_id=mapping["event_id"], correction_reason="Replace the prior synthetic mapping by append-only correction.",
        **common,
    )
    events = log.events()
    summary = validate_event_chain(events)
    if summary["action_type_count"] != len(ACTION_TYPES) or summary["unclosed_event_ids"]:
        raise AuditRecoveryError("synthetic event fixture does not cover the complete event contract")
    return events


def build_snapshot(
    *,
    snapshot_id: str,
    subject_ref: str,
    subject_type: str,
    version_ref: str,
    approval_status: str,
    dependency_version_refs: Sequence[str],
    payload: Mapping[str, Any],
    captured_at: str,
) -> dict[str, Any]:
    if subject_type not in SNAPSHOT_SUBJECT_TYPES:
        raise AuditRecoveryError("unsupported snapshot subject type")
    if approval_status not in {"DRAFT", "APPROVED"}:
        raise AuditRecoveryError("unsupported snapshot approval status")
    dependencies = [_required_text(value, "dependency_version_ref") for value in dependency_version_refs]
    if not dependencies:
        raise AuditRecoveryError("snapshot dependency versions are required")
    return {
        "schema_version": "kmfa.v015.s04p3.snapshot.v1",
        "snapshot_id": _required_text(snapshot_id, "snapshot_id"),
        "subject_ref": _required_text(subject_ref, "subject_ref"),
        "subject_type": subject_type,
        "version_ref": _required_text(version_ref, "version_ref"),
        "approval_status": approval_status,
        "dependency_version_refs": dependencies,
        "payload_digest": _digest_token(payload),
        "digest_algorithm": "SHA-256",
        "captured_at": _required_text(captured_at, "captured_at"),
        "immutable": True,
        "synthetic_fixture": True,
        "contains_raw_business_value": False,
    }


def synthetic_snapshot_registry() -> dict[str, Any]:
    definitions = (
        ("SNAP-S04P3-FACT-V1", "SUBJECT::SYNTHETIC-CRITICAL-FACT", "CRITICAL_FACT", "FACT-VERSION::1.0.0", "APPROVED", ["SOURCE-VERSION::1.0.0"], {"fact_ref": "FACT::SYNTHETIC-V1"}),
        ("SNAP-S04P3-FACT-V2", "SUBJECT::SYNTHETIC-CRITICAL-FACT", "CRITICAL_FACT", "FACT-VERSION::2.0.0", "APPROVED", ["SOURCE-VERSION::2.0.0"], {"fact_ref": "FACT::SYNTHETIC-V2"}),
        ("SNAP-S04P3-REPORT-V1", "SUBJECT::SYNTHETIC-PUBLISHED-REPORT", "PUBLISHED_REPORT", "REPORT-VERSION::1.0.0", "APPROVED", ["FACT-VERSION::1.0.0", "RULE-VERSION::1.0.0"], {"report_ref": "REPORT::SYNTHETIC-V1"}),
        ("SNAP-S04P3-REPORT-DRAFT", "SUBJECT::SYNTHETIC-PUBLISHED-REPORT", "PUBLISHED_REPORT", "REPORT-VERSION::2.0.0", "DRAFT", ["FACT-VERSION::2.0.0", "RULE-VERSION::1.0.0"], {"report_ref": "REPORT::SYNTHETIC-DRAFT"}),
    )
    snapshots: list[dict[str, Any]] = []
    payloads: dict[str, dict[str, Any]] = {}
    for index, (snapshot_id, subject_ref, subject_type, version_ref, status, dependencies, payload) in enumerate(definitions):
        snapshots.append(
            build_snapshot(
                snapshot_id=snapshot_id,
                subject_ref=subject_ref,
                subject_type=subject_type,
                version_ref=version_ref,
                approval_status=status,
                dependency_version_refs=dependencies,
                payload=payload,
                captured_at=f"2026-07-14T11:0{index}:00+10:00",
            )
        )
        payloads[snapshot_id] = payload
    return {"snapshots": snapshots, "payloads": payloads}


def validate_snapshot_registry(snapshots: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    if not snapshots:
        raise AuditRecoveryError("snapshot registry must not be empty")
    snapshot_ids: set[str] = set()
    version_keys: set[tuple[str, str]] = set()
    subject_types: set[str] = set()
    approved_count = 0
    for snapshot in snapshots:
        snapshot_id = _required_text(snapshot.get("snapshot_id"), "snapshot_id")
        key = (
            _required_text(snapshot.get("subject_ref"), "subject_ref"),
            _required_text(snapshot.get("version_ref"), "version_ref"),
        )
        if snapshot_id in snapshot_ids or key in version_keys:
            raise AuditRecoveryError("snapshot ids and subject-version pairs must be unique")
        snapshot_ids.add(snapshot_id)
        version_keys.add(key)
        subject_type = _required_text(snapshot.get("subject_type"), "subject_type")
        if subject_type not in SNAPSHOT_SUBJECT_TYPES:
            raise AuditRecoveryError("unsupported snapshot subject type")
        subject_types.add(subject_type)
        if snapshot.get("immutable") is not True:
            raise AuditRecoveryError("snapshots must be immutable")
        if snapshot.get("contains_raw_business_value") is not False:
            raise AuditRecoveryError("public snapshots cannot contain raw business values")
        if not snapshot.get("dependency_version_refs"):
            raise AuditRecoveryError("snapshot dependencies must not be empty")
        if snapshot.get("approval_status") == "APPROVED":
            approved_count += 1
        elif snapshot.get("approval_status") != "DRAFT":
            raise AuditRecoveryError("snapshot approval status is invalid")
    if subject_types != set(SNAPSHOT_SUBJECT_TYPES):
        raise AuditRecoveryError("critical fact and published report snapshots are both required")
    return {
        "snapshot_count": len(snapshots),
        "approved_snapshot_count": approved_count,
        "draft_snapshot_count": len(snapshots) - approved_count,
        "snapshot_subject_type_count": len(subject_types),
        "unique_subject_version_count": len(version_keys),
    }


def restore_snapshot(
    snapshot: Mapping[str, Any],
    *,
    payload: Mapping[str, Any],
    expected_version_ref: str,
    available_version_refs: Iterable[str],
) -> dict[str, Any]:
    if snapshot.get("approval_status") != "APPROVED":
        raise AuditRecoveryError("only approved snapshots can be restored")
    if snapshot.get("immutable") is not True:
        raise AuditRecoveryError("mutable snapshots cannot be restored")
    if snapshot.get("payload_digest") != _digest_token(payload):
        raise AuditRecoveryError("restored payload digest does not match snapshot")
    version_ref = _required_text(snapshot.get("version_ref"), "version_ref")
    if version_ref != _required_text(expected_version_ref, "expected_version_ref"):
        raise AuditRecoveryError("restored version identity does not match requested version")
    available = {str(value) for value in available_version_refs}
    missing = sorted(set(map(str, snapshot.get("dependency_version_refs") or [])) - available)
    if missing:
        raise AuditRecoveryError("restore dependencies are incomplete: " + ",".join(missing))
    return {
        "snapshot_id": snapshot["snapshot_id"],
        "subject_ref": snapshot["subject_ref"],
        "restored_version_ref": version_ref,
        "restored_payload_digest": snapshot["payload_digest"],
        "validation_dimensions": list(RESTORE_VALIDATION_DIMENSIONS),
        "validation_pass_count": len(RESTORE_VALIDATION_DIMENSIONS),
        "status": "RESTORED_VERIFIED",
        "production_restore_performed": False,
        "synthetic_restore_drill": True,
    }


def run_synthetic_recovery_drill() -> dict[str, Any]:
    registry = synthetic_snapshot_registry()
    snapshots = registry["snapshots"]
    payloads = registry["payloads"]
    summary = validate_snapshot_registry(snapshots)
    available = {
        ref
        for snapshot in snapshots
        for ref in snapshot["dependency_version_refs"]
    }
    results = [
        restore_snapshot(
            snapshot,
            payload=payloads[snapshot["snapshot_id"]],
            expected_version_ref=snapshot["version_ref"],
            available_version_refs=available,
        )
        for snapshot in snapshots
        if snapshot["approval_status"] == "APPROVED"
    ]
    return {
        **summary,
        "approved_snapshot_recovery_case_count": len(results),
        "recovery_pass_count": sum(result["status"] == "RESTORED_VERIFIED" for result in results),
        "restore_validation_dimension_count": len(RESTORE_VALIDATION_DIMENSIONS),
        "arbitrary_approved_version_recovery_passed": len(results) == summary["approved_snapshot_count"],
        "results": results,
        "production_restore_performed": False,
    }


def _finding(
    finding_type: str,
    *,
    subject_ref: str,
    detail: str,
    severity: str,
    repair_path: str,
) -> dict[str, Any]:
    return {
        "finding_type": finding_type,
        "severity": severity,
        "subject_ref": subject_ref,
        "detail": detail,
        "repair_path": repair_path,
        "publication_blocking": severity == "CRITICAL",
    }


def inspect_metadata_health(
    *,
    events: Sequence[Mapping[str, Any]],
    snapshots: Sequence[Mapping[str, Any]],
    known_subject_refs: Iterable[str],
    known_version_refs: Iterable[str],
) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    known_subjects = {str(value) for value in known_subject_refs}
    known_versions = {str(value) for value in known_version_refs}

    orphan_refs = sorted(
        {
            str(record.get("subject_ref"))
            for record in [*events, *snapshots]
            if str(record.get("subject_ref")) not in known_subjects
        }
    )
    if orphan_refs:
        findings.append(_finding(
            "ORPHAN_RECORD", subject_ref=orphan_refs[0],
            detail=f"orphan_count={len(orphan_refs)}", severity="ERROR",
            repair_path="REGISTER_SUBJECT_OR_APPEND_QUARANTINE_EVENT",
        ))

    broken_details: list[str] = []
    try:
        validate_event_chain(events)
    except AuditRecoveryError as error:
        broken_details.append(str(error))
    missing_dependencies = sorted(
        {
            str(ref)
            for snapshot in snapshots
            for ref in snapshot.get("dependency_version_refs") or []
            if str(ref) not in known_versions
        }
    )
    if missing_dependencies:
        broken_details.append("missing_dependencies=" + ",".join(missing_dependencies))
    if broken_details:
        findings.append(_finding(
            "BROKEN_LINK", subject_ref="METADATA::EVENT-OR-SNAPSHOT-LINK",
            detail=";".join(broken_details), severity="CRITICAL",
            repair_path="RESTORE_LAST_APPROVED_SNAPSHOT_THEN_APPEND_CORRECTION_EVENT",
        ))

    version_counts = Counter(
        (str(snapshot.get("subject_ref")), str(snapshot.get("version_ref")))
        for snapshot in snapshots
    )
    duplicates = sorted(key for key, count in version_counts.items() if count > 1)
    if duplicates:
        findings.append(_finding(
            "DUPLICATE_VERSION", subject_ref="::".join(duplicates[0]),
            detail=f"duplicate_subject_version_count={len(duplicates)}", severity="ERROR",
            repair_path="APPEND_SUPERSESSION_EVENT_AND_QUARANTINE_DUPLICATE_VERSION",
        ))

    required_closure = {
        str(event.get("event_id"))
        for event in events
        if event.get("requires_closure") is True
    }
    closed = {
        str(event.get("closes_event_id"))
        for event in events
        if event.get("closes_event_id")
    }
    unclosed = sorted(required_closure - closed)
    if unclosed:
        findings.append(_finding(
            "UNCLOSED_EVENT", subject_ref=unclosed[0],
            detail=f"unclosed_event_count={len(unclosed)}", severity="CRITICAL",
            repair_path="APPEND_REQUIRED_CLOSURE_EVENT_BEFORE_PUBLICATION",
        ))

    finding_types = sorted({finding["finding_type"] for finding in findings})
    critical_count = sum(finding["severity"] == "CRITICAL" for finding in findings)
    return {
        "inspection_status": "PASS" if not findings else "FINDINGS_RECORDED",
        "finding_count": len(findings),
        "finding_type_count": len(finding_types),
        "finding_types": finding_types,
        "critical_finding_count": critical_count,
        "findings": findings,
        "all_findings_have_repair_path": all(finding["repair_path"] for finding in findings),
        "metadata_publication_gate_passed": critical_count == 0,
        "formal_report_allowed": False,
        "automatic_publication_allowed": False,
        "raw_root_access_count": 0,
    }


def synthetic_health_verification() -> dict[str, Any]:
    events = synthetic_event_log()
    registry = synthetic_snapshot_registry()
    snapshots = registry["snapshots"]
    known_subjects = {
        "SUBJECT::SYNTHETIC-MANAGEMENT-REPORT",
        "SUBJECT::SYNTHETIC-CRITICAL-FACT",
        "SUBJECT::SYNTHETIC-PUBLISHED-REPORT",
    }
    known_versions = {
        ref for snapshot in snapshots for ref in snapshot["dependency_version_refs"]
    }
    healthy = inspect_metadata_health(
        events=events,
        snapshots=snapshots,
        known_subject_refs=known_subjects,
        known_version_refs=known_versions,
    )

    faulty_events = copy.deepcopy([*events[:5], *events[6:]])
    faulty_events[1]["subject_ref"] = "SUBJECT::UNREGISTERED-SYNTHETIC"
    faulty_events[1]["event_digest"] = _event_digest(faulty_events[1])
    faulty_events[2]["previous_event_digest"] = "BROKEN-DIGEST-TOKEN"
    duplicate = copy.deepcopy(snapshots[0])
    duplicate["snapshot_id"] = "SNAP-S04P3-DUPLICATE-V1"
    faulty_snapshots = [*copy.deepcopy(snapshots), duplicate]
    faulty_snapshots[1]["dependency_version_refs"] = ["SOURCE-VERSION::MISSING"]
    faulty = inspect_metadata_health(
        events=faulty_events,
        snapshots=faulty_snapshots,
        known_subject_refs=known_subjects,
        known_version_refs=known_versions,
    )
    if set(faulty["finding_types"]) != set(HEALTH_FINDING_TYPES):
        raise AuditRecoveryError("faulty health fixture must cover all required finding classes")
    return {
        "healthy_case": healthy,
        "faulty_case": faulty,
        "required_finding_types": list(HEALTH_FINDING_TYPES),
        "critical_break_blocks_publication": (
            faulty["critical_finding_count"] > 0
            and not faulty["metadata_publication_gate_passed"]
            and not faulty["automatic_publication_allowed"]
        ),
        "all_findings_have_repair_path": faulty["all_findings_have_repair_path"],
        "production_metadata_repair_performed": False,
        "raw_root_access_count": 0,
    }
