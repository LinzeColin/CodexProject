#!/usr/bin/env python3
"""KMFA v1.5 S04-P1 public-safe data-catalog contracts.

This module defines schemas and deterministic control logic only.  It never
opens the raw inbox and never publishes raw filenames, paths, values, or file
digests.  Actual import records, including ``file_hash``, belong to the private
metadata plane; public evidence exposes only aggregate verification results.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from typing import Any, Mapping, Sequence

from KMFA.tools.v015_s02_p2_lineage_contract import (
    DEFAULT_PUBLIC_SOURCE_TEMPLATE_CSV,
    parse_source_domain_csv,
)


RUN_PHASE_ID = "V015_S04_P1_DATA_CATALOG"
TASK_ID = "KMFA-V015-S04-P1-DATA-CATALOG-20260714"
ACCEPTANCE_ID = "ACC-KMFA-V015-S04-P1-DATA-CATALOG"
VERSION = "1.5.0-dev-s04p1"

CATALOG_HIERARCHY = (
    "source_system",
    "business_segment",
    "source_package",
    "entity",
    "bank",
    "account_or_report",
    "period",
    "version",
    "owner_role",
)

SOURCE_STATUS_LABELS = {
    "READY": "已就绪",
    "PARTIAL": "部分可用",
    "FAILED_OR_NOT_APPLICABLE": "失败/不适用",
    "OUTDATED": "已过期",
    "MANUAL_REVIEW": "需要确认",
}
SOURCE_STATUSES = tuple(SOURCE_STATUS_LABELS)

STATUS_AUTHORITIES = (
    "BACKEND_IMPORT",
    "QUALITY_ENGINE",
    "CONTROL_REVIEWER",
    "OWNER_APPROVAL",
)

ALLOWED_TRANSITIONS = {
    "READY": frozenset({"PARTIAL", "FAILED_OR_NOT_APPLICABLE", "OUTDATED", "MANUAL_REVIEW"}),
    "PARTIAL": frozenset({"READY", "FAILED_OR_NOT_APPLICABLE", "OUTDATED", "MANUAL_REVIEW"}),
    "FAILED_OR_NOT_APPLICABLE": frozenset({"READY", "PARTIAL", "OUTDATED", "MANUAL_REVIEW"}),
    "OUTDATED": frozenset({"READY", "PARTIAL", "FAILED_OR_NOT_APPLICABLE", "MANUAL_REVIEW"}),
    "MANUAL_REVIEW": frozenset({"READY", "PARTIAL", "FAILED_OR_NOT_APPLICABLE", "OUTDATED"}),
}

REQUIRED_IMPORT_FIELDS = (
    "source_id",
    "file_id",
    "import_run_id",
    "file_hash",
    "period",
    "parser_version",
)

SOURCE_ID_PATTERN = re.compile(r"^SRC-[a-z0-9-]{3,40}-[a-f0-9]{8}$")
FILE_ID_PATTERN = re.compile(r"^FILE-[a-z0-9-]{3,40}-[a-f0-9]{8}$")
IMPORT_RUN_ID_PATTERN = re.compile(r"^IMP-[0-9]{8}-[0-9]{6}-[a-z0-9-]{3,40}-[a-f0-9]{8}$")
FILE_HASH_PATTERN = re.compile(r"^sha256:[a-f0-9]{64}$")
PERIOD_PATTERN = re.compile(r"^[0-9]{4}(?:-(?:0[1-9]|1[0-2]))?$")
SEMVER_PATTERN = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")


class DataCatalogError(ValueError):
    """Raised when a catalog or state-machine contract fails closed."""


def _stable_suffix(*parts: str) -> str:
    payload = "|".join(parts).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:8]


def _require_text(value: Any, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise DataCatalogError(f"{field} is required")
    return text


def _iso_timestamp(value: Any) -> str:
    text = _require_text(value, "event_time")
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as error:
        raise DataCatalogError("event_time must be ISO-8601") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise DataCatalogError("event_time must include a timezone")
    return parsed.isoformat()


def build_catalog_records() -> list[dict[str, Any]]:
    """Build the exact 21-row public-safe TaskPack catalog template."""

    source_rows = parse_source_domain_csv(DEFAULT_PUBLIC_SOURCE_TEMPLATE_CSV)
    records: list[dict[str, Any]] = []
    for index, row in enumerate(source_rows, start=1):
        system_code = str(row["source_system_code"])
        segment = str(row["business_segment"])
        slug = system_code.lower().replace("_", "-")
        source_id = f"SRC-{slug}-{_stable_suffix(system_code, segment)}"
        records.append(
            {
                "catalog_record_id": f"CAT-S04P1-{index:03d}",
                "source_id": source_id,
                "source_system": {
                    "code": system_code,
                    "name": row["source_system_name"],
                },
                "business_segment": segment,
                "source_package": row["source_package_class"],
                "entity": "ENTITY::TO_BE_CONFIGURED",
                "bank": (
                    "BANK::TO_BE_CONFIGURED"
                    if system_code == "BANK"
                    else "NOT_APPLICABLE"
                ),
                "account_or_report": "ACCOUNT_OR_REPORT::TO_BE_CONFIGURED",
                "period": "PERIOD::TO_BE_BOUND_AT_IMPORT",
                "version": "VERSION::TO_BE_BOUND_AT_IMPORT",
                "owner_role": "ROLE::DATA_OWNER",
                "status": "PARTIAL",
                "status_label": SOURCE_STATUS_LABELS["PARTIAL"],
                "impact_surfaces": list(row["impact_surfaces"]),
                "business_line_ids": list(row["business_line_ids"]),
                "public_safe_template": True,
                "contains_raw_value": False,
                "contains_plaintext_filename": False,
                "contains_private_digest": False,
            }
        )
    validate_catalog_records(records)
    return records


def validate_catalog_records(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Validate hierarchy, source coverage, uniqueness, and report stop gate."""

    if len(records) != 21:
        raise DataCatalogError(f"catalog row count must be 21, got {len(records)}")
    record_ids: set[str] = set()
    source_ids: set[str] = set()
    systems: set[str] = set()
    placeholder_count = 0
    for record in records:
        missing = [level for level in CATALOG_HIERARCHY if level not in record]
        if missing:
            raise DataCatalogError(f"catalog hierarchy missing: {','.join(missing)}")
        record_id = _require_text(record.get("catalog_record_id"), "catalog_record_id")
        source_id = _require_text(record.get("source_id"), "source_id")
        if record_id in record_ids or source_id in source_ids:
            raise DataCatalogError("catalog identifiers must be unique")
        if not SOURCE_ID_PATTERN.fullmatch(source_id):
            raise DataCatalogError(f"invalid source_id: {source_id}")
        record_ids.add(record_id)
        source_ids.add(source_id)
        source_system = record.get("source_system")
        if not isinstance(source_system, Mapping):
            raise DataCatalogError("source_system must be an object")
        systems.add(_require_text(source_system.get("code"), "source_system.code"))
        status = _require_text(record.get("status"), "status")
        if status not in SOURCE_STATUS_LABELS:
            raise DataCatalogError(f"unsupported status: {status}")
        if record.get("status_label") != SOURCE_STATUS_LABELS[status]:
            raise DataCatalogError("status label mismatch")
        if any(record.get(field) is None for field in ("entity", "bank", "account_or_report", "period", "version", "owner_role")):
            raise DataCatalogError("catalog hierarchy values cannot be null")
        placeholder_count += sum(
            "TO_BE_" in str(record.get(field, ""))
            for field in ("entity", "bank", "account_or_report", "period", "version")
        )
        if not record.get("public_safe_template"):
            raise DataCatalogError("public catalog row must be marked public-safe")
        if any(
            record.get(flag)
            for flag in ("contains_raw_value", "contains_plaintext_filename", "contains_private_digest")
        ):
            raise DataCatalogError("public catalog row contains forbidden private detail")
    if len(systems) != 7:
        raise DataCatalogError(f"source system count must be 7, got {len(systems)}")
    return {
        "catalog_record_count": len(records),
        "source_system_count": len(systems),
        "hierarchy_level_count": len(CATALOG_HIERARCHY),
        "placeholder_binding_count": placeholder_count,
        "formal_report_allowed": placeholder_count == 0,
        "formal_report_stop_reason": (
            None if placeholder_count == 0 else "CORE_CATALOG_BINDINGS_INCOMPLETE"
        ),
    }


def status_machine_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.source_status_machine.v1",
        "statuses": [
            {"code": code, "label": SOURCE_STATUS_LABELS[code]}
            for code in SOURCE_STATUSES
        ],
        "authorities": list(STATUS_AUTHORITIES),
        "frontend_direct_transition_allowed": False,
        "frontend_raw_fact_mutation_allowed": False,
        "transition_requires": [
            "reason",
            "operator_role",
            "event_time",
            "affected_report_refs",
            "backend_fact_ref",
        ],
        "ready_requires_quality_fact": True,
        "allowed_transitions": {
            state: sorted(targets) for state, targets in ALLOWED_TRANSITIONS.items()
        },
        "event_storage": "APPEND_ONLY_METADATA",
        "raw_layer_write_allowed": False,
    }


def build_status_event(
    *,
    source_id: str,
    previous_status: str,
    new_status: str,
    reason: str,
    operator_role: str,
    authority: str,
    event_time: str,
    affected_report_refs: Sequence[str],
    backend_fact_ref: str,
    quality_fact_ref: str | None = None,
) -> dict[str, Any]:
    """Build an append-only status event; direct frontend authority is rejected."""

    if not SOURCE_ID_PATTERN.fullmatch(_require_text(source_id, "source_id")):
        raise DataCatalogError("invalid source_id")
    if previous_status not in SOURCE_STATUS_LABELS or new_status not in SOURCE_STATUS_LABELS:
        raise DataCatalogError("unknown source status")
    if new_status not in ALLOWED_TRANSITIONS[previous_status]:
        raise DataCatalogError("status transition is not allowed")
    if authority not in STATUS_AUTHORITIES:
        raise DataCatalogError("frontend or unknown authority cannot mutate source status")
    role = _require_text(operator_role, "operator_role")
    if not role.startswith("ROLE::"):
        raise DataCatalogError("operator_role must be a public role reference")
    report_refs = [_require_text(value, "affected_report_ref") for value in affected_report_refs]
    if not report_refs:
        raise DataCatalogError("affected_report_refs must not be empty")
    fact_ref = _require_text(backend_fact_ref, "backend_fact_ref")
    if not fact_ref.startswith("FACT::"):
        raise DataCatalogError("backend_fact_ref must be an opaque fact reference")
    quality_ref = None if quality_fact_ref is None else _require_text(quality_fact_ref, "quality_fact_ref")
    if new_status == "READY":
        if authority not in {"BACKEND_IMPORT", "QUALITY_ENGINE"}:
            raise DataCatalogError("READY can only be set from backend import or quality facts")
        if quality_ref is None or not quality_ref.startswith("QUALITY::"):
            raise DataCatalogError("READY requires an opaque quality fact reference")
    timestamp = _iso_timestamp(event_time)
    reason_text = _require_text(reason, "reason")
    event_suffix = _stable_suffix(source_id, previous_status, new_status, timestamp, reason_text)
    return {
        "schema_version": "kmfa.v015.source_status_event.v1",
        "event_id": f"STATUS-EVENT-{event_suffix}",
        "source_id": source_id,
        "previous_status": previous_status,
        "new_status": new_status,
        "new_status_label": SOURCE_STATUS_LABELS[new_status],
        "reason": reason_text,
        "operator_role": role,
        "authority": authority,
        "event_time": timestamp,
        "affected_report_refs": report_refs,
        "backend_fact_ref": fact_ref,
        "quality_fact_ref": quality_ref,
        "storage_mode": "APPEND_ONLY_METADATA",
        "raw_fact_mutation_allowed": False,
        "frontend_direct_transition_allowed": False,
    }


def import_registration_protocol() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.import_registration.v1",
        "required_fields": list(REQUIRED_IMPORT_FIELDS),
        "patterns": {
            "source_id": SOURCE_ID_PATTERN.pattern,
            "file_id": FILE_ID_PATTERN.pattern,
            "import_run_id": IMPORT_RUN_ID_PATTERN.pattern,
            "file_hash": FILE_HASH_PATTERN.pattern,
            "period": PERIOD_PATTERN.pattern,
            "parser_version": SEMVER_PATTERN.pattern,
        },
        "file_hash_plane": "PRIVATE_METADATA_ONLY",
        "missing_source_or_hash_action": "QUARANTINE",
        "exact_replay_action": "REUSE_EXISTING_REGISTRATION",
        "duplicate_detection_key": ["source_id", "file_hash"],
        "idempotency_key": ["source_id", "file_hash", "period", "parser_version"],
        "version_coexistence_key": ["source_id", "period", "parser_version", "file_hash"],
        "raw_fact_mutation_allowed": False,
    }


def _validate_registration(candidate: Mapping[str, Any]) -> dict[str, str]:
    normalized = {field: _require_text(candidate.get(field), field) for field in REQUIRED_IMPORT_FIELDS}
    patterns = {
        "source_id": SOURCE_ID_PATTERN,
        "file_id": FILE_ID_PATTERN,
        "import_run_id": IMPORT_RUN_ID_PATTERN,
        "file_hash": FILE_HASH_PATTERN,
        "period": PERIOD_PATTERN,
        "parser_version": SEMVER_PATTERN,
    }
    for field, pattern in patterns.items():
        if not pattern.fullmatch(normalized[field]):
            raise DataCatalogError(f"invalid {field}")
    return normalized


def register_import(
    candidate: Mapping[str, Any],
    existing_records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Register metadata, recognize exact replay, and allow version coexistence."""

    missing_quarantine_reasons = []
    if not str(candidate.get("source_id") or "").strip():
        missing_quarantine_reasons.append("MISSING_SOURCE_ID")
    if not str(candidate.get("file_hash") or "").strip():
        missing_quarantine_reasons.append("MISSING_FILE_HASH")
    if missing_quarantine_reasons:
        return {
            "outcome": "QUARANTINED",
            "reason_codes": missing_quarantine_reasons,
            "record": None,
            "raw_fact_mutation_allowed": False,
        }

    normalized = _validate_registration(candidate)
    existing = [_validate_registration(record) for record in existing_records]
    exact_key = tuple(normalized[field] for field in ("source_id", "file_hash", "period", "parser_version"))
    for record in existing:
        record_key = tuple(record[field] for field in ("source_id", "file_hash", "period", "parser_version"))
        if record_key == exact_key:
            return {
                "outcome": "REUSED",
                "reason_codes": ["EXACT_IDEMPOTENT_REPLAY"],
                "record": dict(record),
                "new_record_created": False,
                "duplicate_file_detected": True,
                "raw_fact_mutation_allowed": False,
            }

    duplicate_file = any(
        record["source_id"] == normalized["source_id"]
        and record["file_hash"] == normalized["file_hash"]
        for record in existing
    )
    prior_version_count = sum(
        record["source_id"] == normalized["source_id"]
        and record["period"] == normalized["period"]
        for record in existing
    )
    return {
        "outcome": "REGISTERED_VERSION" if prior_version_count else "REGISTERED",
        "reason_codes": ["DUPLICATE_FILE_NEW_PARSER_VERSION"] if duplicate_file else [],
        "record": normalized,
        "new_record_created": True,
        "duplicate_file_detected": duplicate_file,
        "coexisting_prior_version_count": prior_version_count,
        "raw_fact_mutation_allowed": False,
    }


def public_verification_summary() -> dict[str, Any]:
    """Exercise the private-field contract using synthetic in-memory metadata."""

    digest_a = "sha256:" + hashlib.sha256(b"KMFA-S04-P1-SYNTHETIC-A").hexdigest()
    digest_b = "sha256:" + hashlib.sha256(b"KMFA-S04-P1-SYNTHETIC-B").hexdigest()
    base = {
        "source_id": "SRC-synthetic-ledger-5be21c67",
        "file_id": "FILE-synthetic-ledger-5be21c67",
        "import_run_id": "IMP-20260714-120000-synthetic-ledger-5be21c67",
        "file_hash": digest_a,
        "period": "2026-06",
        "parser_version": "1.0.0",
    }
    first = register_import(base, [])
    replay = register_import(base, [first["record"]])
    parser_v2 = dict(base, import_run_id="IMP-20260714-120100-synthetic-ledger-5be21c67", parser_version="1.1.0")
    coexist = register_import(parser_v2, [first["record"]])
    new_file = dict(
        base,
        file_id="FILE-synthetic-ledger-62900d1a",
        import_run_id="IMP-20260714-120200-synthetic-ledger-62900d1a",
        file_hash=digest_b,
        parser_version="1.1.0",
    )
    second = register_import(new_file, [first["record"], coexist["record"]])
    missing_source = register_import({**base, "source_id": ""}, [])
    missing_hash = register_import({**base, "file_hash": ""}, [])
    return {
        "schema_version": "kmfa.v015.s04p1.import_verification_summary.v1",
        "initial_registration_pass": first["outcome"] == "REGISTERED",
        "exact_replay_idempotent": replay["outcome"] == "REUSED" and not replay["new_record_created"],
        "duplicate_file_new_parser_detected": (
            coexist["outcome"] == "REGISTERED_VERSION" and coexist["duplicate_file_detected"]
        ),
        "different_file_version_coexists": second["outcome"] == "REGISTERED_VERSION",
        "missing_source_quarantined": missing_source["outcome"] == "QUARANTINED",
        "missing_hash_quarantined": missing_hash["outcome"] == "QUARANTINED",
        "required_field_count": len(REQUIRED_IMPORT_FIELDS),
        "private_file_hash_exposed": False,
        "raw_root_access_count": 0,
        "raw_fact_mutation_allowed": False,
    }


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
