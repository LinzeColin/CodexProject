#!/usr/bin/env python3
"""Select exactly one guarded STAGE-036 migration section for psql.

The runner never connects to PostgreSQL. It validates tracked contract bytes,
always blocks live up emission because v0.1 has no trusted signature/target
binding verifier, and emits rollback only inside an explicit transaction.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PURSUE_ROOT = ROOT / "docs" / "pursuing_goal" / "ids_v0_1"
QUALITY_ROOT = PURSUE_ROOT / "database_quality_constraints"
MIGRATION_PATH = QUALITY_ROOT / "002_database_quality_constraints.sql"
INDEX_PATH = QUALITY_ROOT / "stage036_database_quality_constraints_index.json"
PROFILE_QUERIES_PATH = QUALITY_ROOT / "stage036_quality_profile_queries.json"
RAW_METADATA_ROOT = Path("/Users/linzezhang/Downloads/IDS_MetaData")
EXPECTED_MIGRATION_SHA256 = (
    "52cd624f9e3bec197fa20a14405c7fe2ea149362115c33e9de0145b315dd455a"
)
EXPECTED_INDEX_SHA256 = (
    "016abaa478da1c6cc98513e432429a26402fde5b0b5ac050ec4ceb03aeb33271"
)
EXPECTED_PROFILE_QUERIES_SHA256 = (
    "ced8f7f68f43c98d10426a92fdc064b8dbec58f0fd30786fd21decd4ff282ea1"
)
EXPECTED_PROFILE_QUERY_SHA256 = {
    "uq_ids_chunks_document_ordinal": "b04c3c07c72c2c8cbef6df7c7327a1174a947e545471587dbb652648b9c9bc83",
    "chk_ids_metadata_sources_quality_v2": "8be22adcb663d4aa8ccd1adc8db756391e1f57975526a83efb10d4eedc058be3",
    "chk_ids_jobs_quality_v2": "aa3e0da5e3e5f6309c4012a65778c4f98c1a8f80614b0c92a97b4df62440b5b9",
    "chk_ids_documents_quality_v2": "12b9d678da2204b00bd1a497da568ba9b0da0d8f9b26bad55f05eecf023a2e28",
    "chk_ids_chunks_quality_v2": "866795bdfa33989140f3fada627423e86260ce66d880962fb75c953974790bde",
    "chk_ids_evidence_records_quality_v2": "ac3466a0af67d329bc3c6d3fbb6e51c8166860f31af09e259147d37f556ac92b",
    "chk_ids_audit_events_quality_v2": "1f6e72be87c55716806759f6d40c48d8b01e7744bbbd04057db084a3f0970711",
    "chk_ids_index_versions_quality_v2": "37c7f80f4ebc1336fdb375dbe4d35f0057d35851f9c612c2b4a5729ea9d31393",
    "chk_ids_schema_migrations_quality_v2": "d4775dbe8beb587b0618c96c1f5882d5602e38b51d7eb601da2e51e06e836d98",
}
UP_MARKER = "-- migrate:up"
DOWN_MARKER = "-- migrate:down"
AUTHORIZATION_ENV = "IDS_STAGE036_AUTHORIZATION_ENVELOPE"
AUTHORIZATION_SCHEMA_VERSION = "ids.stage036.migration_authorization.v1"
MIGRATION_ID = "ids_stage036_002_database_quality_constraints"
ACCEPTANCE_ID = "ACC-STAGE-036"


class SelectionError(ValueError):
    """Raised when the requested section cannot be selected safely."""


def _load_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise SelectionError(f"tracked migration source unavailable: {exc}") from exc


def _load_json_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SelectionError(f"authorization contract unavailable: {exc}") from exc
    if not isinstance(value, dict):
        raise SelectionError("authorization contract must be a JSON object")
    return value


def _parse_utc(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.endswith("Z"):
        return None
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return None
    return parsed.astimezone(timezone.utc)


def _safe_ref(value: object) -> bool:
    return (
        isinstance(value, str)
        and 1 <= len(value) <= 512
        and value.strip() == value
        and "\x00" not in value
        and "\n" not in value
        and re.search(r"(?i)(?:password|api[_-]?key|secret|token)\s*[:=]", value)
        is None
    )


def _zero_violation_count(value: object) -> bool:
    return type(value) is int and value == 0


def _authorization_values(
    envelope: dict[str, Any], index: dict[str, Any], *, now: datetime
) -> dict[str, str]:
    contract = index.get("authorization_envelope_contract")
    contract = contract if isinstance(contract, dict) else {}
    candidate_results = envelope.get("candidate_results")
    candidate_results = candidate_results if isinstance(candidate_results, list) else []
    expected_queries = contract.get("candidate_query_sha256")
    expected_queries = expected_queries if isinstance(expected_queries, dict) else {}
    results_by_id = {
        item.get("constraint_id"): item
        for item in candidate_results
        if isinstance(item, dict) and isinstance(item.get("constraint_id"), str)
    }
    approved_at = _parse_utc(envelope.get("approved_at_utc"))
    expires_at = _parse_utc(envelope.get("expires_at_utc"))
    required_refs = {
        field: envelope.get(field)
        for field in (
            "profile_evidence_ref",
            "backup_checkpoint_ref",
            "rollback_plan_ref",
            "owner_approval_ref",
            "source_database_identity_ref",
            "target_database_identity_ref",
            "schema_head_ref",
        )
    }
    candidate_shape_valid = (
        expected_queries == EXPECTED_PROFILE_QUERY_SHA256
        and len(expected_queries) == 9
        and set(results_by_id) == set(EXPECTED_PROFILE_QUERY_SHA256)
        and len(candidate_results) == len(EXPECTED_PROFILE_QUERY_SHA256)
        and all(
            set(item)
            == {
                "constraint_id",
                "query_sha256",
                "violation_count",
                "profile_evidence_ref",
                "verified_at_utc",
            }
            and item.get("query_sha256")
            == EXPECTED_PROFILE_QUERY_SHA256[constraint_id]
            and _zero_violation_count(item.get("violation_count"))
            and _safe_ref(item.get("profile_evidence_ref"))
            and _parse_utc(item.get("verified_at_utc")) is not None
            for constraint_id, item in results_by_id.items()
        )
    )
    valid = (
        set(envelope)
        == {
            "schema_version",
            "migration_id",
            "migration_sha256",
            "acceptance_id",
            "authorization_granted",
            "approved_at_utc",
            "expires_at_utc",
            "owner_approval_ref",
            "profile_evidence_ref",
            "backup_checkpoint_ref",
            "rollback_plan_ref",
            "source_database_identity_ref",
            "target_database_identity_ref",
            "schema_head_ref",
            "source_database_mutation_allowed",
            "destructive_migration_authorized",
            "secrets_in_envelope",
            "candidate_results",
        }
        and contract.get("schema_version") == AUTHORIZATION_SCHEMA_VERSION
        and contract.get("required") is True
        and contract.get("runtime_authorization_default") is False
        and contract.get("trusted_signature_verifier_available") is False
        and contract.get("target_binding_verifier_available") is False
        and contract.get("live_up_emission_allowed") is False
        and envelope.get("schema_version") == AUTHORIZATION_SCHEMA_VERSION
        and envelope.get("migration_id") == MIGRATION_ID
        and envelope.get("migration_sha256") == EXPECTED_MIGRATION_SHA256
        and envelope.get("acceptance_id") == ACCEPTANCE_ID
        and envelope.get("authorization_granted") is True
        and envelope.get("source_database_mutation_allowed") is False
        and envelope.get("destructive_migration_authorized") is False
        and envelope.get("secrets_in_envelope") is False
        and all(_safe_ref(value) for value in required_refs.values())
        and required_refs["source_database_identity_ref"]
        != required_refs["target_database_identity_ref"]
        and approved_at is not None
        and expires_at is not None
        and approved_at <= now < expires_at
        and candidate_shape_valid
    )
    if not valid:
        raise SelectionError(
            "owner-authorized migration envelope is missing, expired, or invalid"
        )
    return {
        "ids.owner_authorized_real_profile_ref": str(
            required_refs["profile_evidence_ref"]
        ),
        "ids.migration_backup_checkpoint_ref": str(
            required_refs["backup_checkpoint_ref"]
        ),
        "ids.migration_rollback_plan_ref": str(
            required_refs["rollback_plan_ref"]
        ),
    }


def _sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def select_migration_section(
    sql: str, section: str, *, session_refs: dict[str, str] | None = None
) -> str:
    if sql.count(UP_MARKER) != 1 or sql.count(DOWN_MARKER) != 1:
        raise SelectionError("migration must contain exactly one up and one down marker")
    up_start = sql.index(UP_MARKER)
    down_start = sql.index(DOWN_MARKER)
    if up_start >= down_start:
        raise SelectionError("migration markers are out of order")
    if section == "down":
        selected = sql[down_start:].rstrip()
        return f"\\set ON_ERROR_STOP on\nBEGIN;\n{selected}\nCOMMIT;\n"
    if section != "up":
        raise SelectionError(f"unsupported migration section: {section}")
    raise SelectionError(
        "live up emission is blocked: v0.1 has no trusted authorization "
        "signature or target-database binding verifier"
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Select one verified STAGE-036 migration section."
    )
    parser.add_argument("--section", choices=("up", "down"), required=True)
    parser.add_argument(
        "--authorization-envelope",
        type=Path,
        help=f"Owner authorization JSON path; may also use {AUTHORIZATION_ENV}.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        sql = _load_text(MIGRATION_PATH)
        if hashlib.sha256(sql.encode("utf-8")).hexdigest() != EXPECTED_MIGRATION_SHA256:
            raise SelectionError("tracked migration SHA-256 does not match the runner")
        session_refs = None
        if args.section == "up":
            envelope_path = args.authorization_envelope
            if envelope_path is None and os.environ.get(AUTHORIZATION_ENV):
                envelope_path = Path(os.environ[AUTHORIZATION_ENV])
            if envelope_path is None:
                raise SelectionError(
                    "owner-authorized migration envelope is required for up"
                )
            resolved_envelope = envelope_path.expanduser().resolve()
            try:
                inside_raw_root = resolved_envelope.is_relative_to(
                    RAW_METADATA_ROOT.resolve()
                )
            except (OSError, RuntimeError):
                inside_raw_root = True
            if inside_raw_root:
                raise SelectionError(
                    "authorization envelope must not be read from IDS_MetaData"
                )
            envelope = _load_json_object(resolved_envelope)
            index_text = _load_text(INDEX_PATH)
            if (
                hashlib.sha256(index_text.encode("utf-8")).hexdigest()
                != EXPECTED_INDEX_SHA256
            ):
                raise SelectionError("tracked index SHA-256 does not match the runner")
            try:
                index = json.loads(index_text)
            except json.JSONDecodeError as exc:
                raise SelectionError(f"tracked index is invalid JSON: {exc}") from exc
            if not isinstance(index, dict):
                raise SelectionError("tracked index must be a JSON object")
            profile_queries = _load_text(PROFILE_QUERIES_PATH)
            if (
                hashlib.sha256(profile_queries.encode("utf-8")).hexdigest()
                != EXPECTED_PROFILE_QUERIES_SHA256
            ):
                raise SelectionError(
                    "tracked profile-query SHA-256 does not match the runner"
                )
            session_refs = _authorization_values(
                envelope, index, now=datetime.now(timezone.utc)
            )
        selected = select_migration_section(
            sql, args.section, session_refs=session_refs
        )
    except SelectionError as exc:
        print(f"STAGE-036 migration runner blocked: {exc}", file=sys.stderr)
        return 2
    sys.stdout.write(selected)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
