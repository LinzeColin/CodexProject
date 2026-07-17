#!/usr/bin/env python3
"""Fail-closed golden-baseline preparation and lock for KMFA v1.5 S06-P2.

Private source values, locators, reviewer identity, and locked baselines remain
inside the Git-ignored private runtime.  The tracked/public projection exposes
only aggregate gate state.  A golden version can be appended only after an
explicit, packet-bound human sign-off resolves every candidate and passes the
project arithmetic checks.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
from collections import Counter, defaultdict
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP, localcontext
from pathlib import Path
from typing import Any, Iterable


RUN_PHASE_ID = "V015_S06_P2_GOLDEN_BASELINE_LOCK"
ROADMAP_PHASE_ID = "S06-P2"
TASK_ID = "KMFA-V015-S06-P2-GOLDEN-BASELINE-LOCK-20260715"
ACCEPTANCE_ID = "ACC-KMFA-V015-S06-P2-GOLDEN-BASELINE-LOCK"
VERSION = "1.5.0-dev-s06p2"

PRIVATE_PACKET_SCHEMA = "kmfa.private.v015.s06p2.golden_candidate_packet.v1"
PRIVATE_SIGNOFF_SCHEMA = "kmfa.private.v015.s06p2.human_signoff.v1"
PRIVATE_AUTHORIZATION_SCHEMA = "kmfa.private.v015.s06p2.user_authorization.v1"
PRIVATE_VERSION_SCHEMA = "kmfa.private.v015.s06p2.golden_version.v1"
PUBLIC_SCHEMA = "kmfa.v015.s06p2.golden_lock_public_safe.v1"

P1_MANIFEST_PATH = Path(
    "KMFA/.codex_private_runtime/v015_s06_p1_authoritative_source_registration/"
    "private_authority_registration.json"
)
PRIVATE_OUTPUT_DIR = Path("KMFA/.codex_private_runtime/v015_s06_p2_golden_baseline_lock")
PRIVATE_PACKET_PATH = PRIVATE_OUTPUT_DIR / "private_candidate_reconciliation.json"
PRIVATE_SIGNOFF_TEMPLATE_PATH = PRIVATE_OUTPUT_DIR / "private_human_signoff_template.json"
PRIVATE_SIGNOFF_PATH = PRIVATE_OUTPUT_DIR / "private_human_signoff.json"
PRIVATE_AUTHORIZATION_PATH = PRIVATE_OUTPUT_DIR / "private_user_authorization.json"
PRIVATE_REVIEW_PATH = PRIVATE_OUTPUT_DIR / "private_human_review.md"
PRIVATE_VERSION_LEDGER_PATH = PRIVATE_OUTPUT_DIR / "private_golden_version_ledger.jsonl"

FIELD_FAMILIES = (
    "PROJECT_IDENTITY",
    "CONTRACT_AMOUNT",
    "TOTAL_EXPENDITURE",
    "GROSS_PROFIT",
    "GROSS_MARGIN",
    "COST_CATEGORY",
)
MONEY_FAMILIES = frozenset({
    "CONTRACT_AMOUNT", "TOTAL_EXPENDITURE", "GROSS_PROFIT", "COST_CATEGORY",
})
EXPECTED_UNITS = {
    "PROJECT_IDENTITY": "TEXT",
    "CONTRACT_AMOUNT": "CNY_CENT",
    "TOTAL_EXPENDITURE": "CNY_CENT",
    "GROSS_PROFIT": "CNY_CENT",
    "GROSS_MARGIN": "BASIS_POINT",
    "COST_CATEGORY": "CNY_CENT",
}
ALLOWED_TAX_STATUS = frozenset({
    "TAX_INCLUDED", "TAX_EXCLUDED", "SOURCE_NOT_STATED", "NOT_APPLICABLE",
})
AUTHORIZATION_STATEMENT = "I_CONFIRM_V015_S06_P2_GOLDEN_BASELINE"
AUTHORIZED_AGENT_IDENTITY = "CODEX_AGENT_ON_USER_AUTHORIZATION"
AUTHORIZED_AGENT_ROLE = "AUTHORIZED_AGENT"


class GoldenBaselineError(RuntimeError):
    """Stable fail-closed S06-P2 validation error."""


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")


def _dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _sha256(value: Any) -> str:
    payload = value if isinstance(value, bytes) else _canonical_bytes(value)
    return hashlib.sha256(payload).hexdigest()


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise GoldenBaselineError(f"private JSON unavailable or invalid: {path.name}") from error
    if not isinstance(value, dict):
        raise GoldenBaselineError(f"private JSON object required: {path.name}")
    return value


def _stat_snapshot(path: Path) -> dict[str, int]:
    value = path.stat()
    return {
        "device": value.st_dev,
        "inode": value.st_ino,
        "mode": stat.S_IMODE(value.st_mode),
        "size_bytes": value.st_size,
        "mtime_ns": value.st_mtime_ns,
        "ctime_ns": value.st_ctime_ns,
    }


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise GoldenBaselineError(message)


def _candidate_id(candidate: dict[str, Any]) -> str:
    binding = {
        "source_ref": candidate.get("source_ref"),
        "source_locator": candidate.get("source_locator"),
        "field_family": candidate.get("field_family"),
    }
    return "S06P2-CAND-" + _sha256(binding)[:24].upper()


def validate_p1_payload(payload: dict[str, Any]) -> None:
    _require(
        payload.get("schema_version")
        == "kmfa.private.v015.s06p1.authoritative_source_registration.v1",
        "S06-P1 private schema mismatch",
    )
    _require(payload.get("source_count") == 9, "S06-P1 source count mismatch")
    _require(payload.get("raw_mutation_performed") is False, "S06-P1 raw mutation invariant failed")
    _require(payload.get("golden_value_confirmed_count") == 0, "S06-P1 cannot contain golden facts")
    records = payload.get("source_records")
    _require(isinstance(records, list) and len(records) == 9, "S06-P1 source records missing")
    candidates = [
        candidate
        for source in records
        for candidate in source.get("inspection", {}).get("field_candidates", [])
    ]
    _require(bool(candidates), "S06-P1 candidate set is empty")
    _require(
        {candidate.get("field_family") for candidate in candidates} == set(FIELD_FAMILIES),
        "S06-P1 field-family coverage mismatch",
    )


def _raw_invariants(payload: dict[str, Any]) -> dict[str, bool]:
    raw_root = Path(str(payload.get("private_raw_root", "")))
    package = Path(str(payload.get("private_package_path", "")))
    _require(raw_root.is_dir(), "raw root unavailable")
    _require(package.is_file(), "authority package unavailable")
    before_root = _stat_snapshot(raw_root)
    before_package = _stat_snapshot(package)
    _require(before_root == payload.get("raw_root_after"), "raw root drifted since S06-P1")
    _require(before_package == payload.get("package_after"), "authority package drifted since S06-P1")
    after_root = _stat_snapshot(raw_root)
    after_package = _stat_snapshot(package)
    return {
        "raw_root_stat_unchanged": before_root == after_root,
        "package_stat_unchanged": before_package == after_package,
        "raw_mutation_performed": False,
    }


def build_candidate_packet(p1_payload: dict[str, Any]) -> dict[str, Any]:
    """Create a private, source-bound review packet without approving facts."""

    validate_p1_payload(p1_payload)
    invariants = _raw_invariants(p1_payload)
    candidates: list[dict[str, Any]] = []
    source_roles = {
        source["source_ref"]: source.get("source_role")
        for source in p1_payload["source_records"]
    }
    for source in p1_payload["source_records"]:
        for raw_candidate in source["inspection"].get("field_candidates", []):
            family = raw_candidate["field_family"]
            candidates.append({
                "candidate_id": _candidate_id(raw_candidate),
                "source_ref": raw_candidate["source_ref"],
                "source_role": source_roles.get(raw_candidate["source_ref"]),
                "source_locator": raw_candidate["source_locator"],
                "field_family": family,
                "raw_text": raw_candidate.get("raw_text"),
                "original_display_tokens": raw_candidate.get("original_display_tokens", []),
                "formula_text": raw_candidate.get("formula_text"),
                "cached_display_value": raw_candidate.get("cached_display_value"),
                "extraction_method": raw_candidate.get("extraction_method"),
                "candidate_role": raw_candidate.get("candidate_role"),
                "identity_component": raw_candidate.get("identity_component"),
                "source_header_raw_text": raw_candidate.get("source_header_raw_text"),
                "candidate_status": "PENDING_HUMAN_DECISION",
                "expected_canonical_unit": EXPECTED_UNITS[family],
                "required_confirmation_fields": [
                    "decision", "project_ref", "canonical_value", "unit", "tax_status",
                    "business_meaning", "confirmed_source_locator",
                ],
            })
    candidates.sort(key=lambda row: row["candidate_id"])
    _require(len({row["candidate_id"] for row in candidates}) == len(candidates), "candidate IDs collide")
    body = {
        "schema_version": PRIVATE_PACKET_SCHEMA,
        "project_id": "KMFA",
        "target_release": "v1.5",
        "phase_id": RUN_PHASE_ID,
        "source_phase_id": "V015_S06_P1_AUTHORITATIVE_SOURCE_REGISTRATION",
        "source_manifest_sha256": hashlib.sha256(P1_MANIFEST_PATH.read_bytes()).hexdigest(),
        "candidate_count": len(candidates),
        "field_family_counts": dict(sorted(Counter(row["field_family"] for row in candidates).items())),
        "candidate_records": candidates,
        "raw_root_stat_unchanged": invariants["raw_root_stat_unchanged"],
        "package_stat_unchanged": invariants["package_stat_unchanged"],
        "raw_mutation_performed": invariants["raw_mutation_performed"],
        "human_signoff_required": True,
        "golden_lock_allowed": False,
    }
    return {**body, "packet_digest": _sha256(body)}


def build_signoff_template(packet: dict[str, Any]) -> dict[str, Any]:
    validate_candidate_packet(packet)
    return {
        "schema_version": PRIVATE_SIGNOFF_SCHEMA,
        "project_id": "KMFA",
        "target_release": "v1.5",
        "phase_id": RUN_PHASE_ID,
        "packet_digest": packet["packet_digest"],
        "baseline_version": "S06P2-GOLDEN-0001",
        "previous_record_hash": None,
        "correction_reason": None,
        "confirmer": {
            "identity": None,
            "role": None,
            "confirmed_at": None,
            "basis": None,
        },
        "authorization_statement": None,
        "decision_rows": [
            {
                "candidate_id": row["candidate_id"],
                "decision": "PENDING",
                "project_ref": None,
                "canonical_value": None,
                "unit": None,
                "tax_status": None,
                "business_meaning": None,
                "confirmed_source_locator": None,
                "category_key": None,
                "rejection_reason": None,
            }
            for row in packet["candidate_records"]
        ],
    }


def validate_candidate_packet(packet: dict[str, Any]) -> None:
    _require(packet.get("schema_version") == PRIVATE_PACKET_SCHEMA, "candidate packet schema mismatch")
    records = packet.get("candidate_records")
    _require(isinstance(records, list) and bool(records), "candidate packet is incomplete")
    _require(packet.get("candidate_count") == len(records), "candidate packet count mismatch")
    _require(len({row.get("candidate_id") for row in records}) == len(records), "candidate IDs are not unique")
    _require(packet.get("raw_mutation_performed") is False, "raw mutation invariant failed")
    body = {key: value for key, value in packet.items() if key != "packet_digest"}
    _require(packet.get("packet_digest") == _sha256(body), "candidate packet digest mismatch")


def _parse_confirmed_at(value: Any) -> None:
    _require(isinstance(value, str) and value.strip(), "confirmer time is required")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as error:
        raise GoldenBaselineError("confirmer time must be ISO-8601") from error
    _require(parsed.tzinfo is not None and parsed.utcoffset() is not None, "confirmer time needs a timezone")


def validate_authorization_record(record: dict[str, Any]) -> str:
    """Validate the private record that delegates S06-P2 decisions to Codex."""

    _require(record.get("schema_version") == PRIVATE_AUTHORIZATION_SCHEMA, "authorization schema mismatch")
    _require(record.get("project_id") == "KMFA", "authorization project mismatch")
    _require(record.get("target_release") == "v1.5", "authorization release mismatch")
    _require(record.get("phase_id") == RUN_PHASE_ID, "authorization phase mismatch")
    _require(record.get("authorizer_type") == "USER", "authorization must originate from user")
    _require(record.get("decision_authority_granted") is True, "decision authority was not granted")
    _require(
        isinstance(record.get("source_thread_id"), str) and record["source_thread_id"].strip(),
        "authorization source thread is required",
    )
    _require(
        isinstance(record.get("user_message"), str) and record["user_message"].strip(),
        "authorization user message is required",
    )
    _parse_confirmed_at(record.get("received_at"))
    body = {key: value for key, value in record.items() if key != "record_digest"}
    digest = _sha256(body)
    _require(record.get("record_digest") == digest, "authorization record digest mismatch")
    return digest


def validate_signoff(signoff: dict[str, Any], packet: dict[str, Any]) -> list[dict[str, Any]]:
    """Validate explicit human sign-off and return accepted canonical fields."""

    validate_candidate_packet(packet)
    _require(signoff.get("schema_version") == PRIVATE_SIGNOFF_SCHEMA, "signoff schema mismatch")
    for key, expected in (
        ("project_id", "KMFA"), ("target_release", "v1.5"),
        ("phase_id", RUN_PHASE_ID), ("packet_digest", packet["packet_digest"]),
    ):
        _require(signoff.get(key) == expected, f"signoff {key} binding mismatch")
    _require(
        signoff.get("authorization_statement") == AUTHORIZATION_STATEMENT,
        "explicit S06-P2 authorization statement is missing",
    )
    confirmer = signoff.get("confirmer")
    _require(isinstance(confirmer, dict), "confirmer record is required")
    for key in ("identity", "role", "basis"):
        _require(isinstance(confirmer.get(key), str) and confirmer[key].strip(), f"confirmer {key} is required")
    _parse_confirmed_at(confirmer.get("confirmed_at"))
    if confirmer.get("role") == AUTHORIZED_AGENT_ROLE:
        _require(
            confirmer.get("identity") == AUTHORIZED_AGENT_IDENTITY,
            "authorized-agent identity mismatch",
        )
        authorization = _json(PRIVATE_AUTHORIZATION_PATH)
        authorization_digest = validate_authorization_record(authorization)
        _require(
            f"AUTHORIZATION_RECORD_DIGEST={authorization_digest}" in confirmer["basis"],
            "authorized signoff is not bound to the user authorization record",
        )

    candidates = {row["candidate_id"]: row for row in packet["candidate_records"]}
    decisions = signoff.get("decision_rows")
    _require(isinstance(decisions, list) and len(decisions) == len(candidates), "every candidate needs a decision")
    _require(len({row.get("candidate_id") for row in decisions}) == len(decisions), "decision IDs are not unique")
    _require(set(row.get("candidate_id") for row in decisions) == set(candidates), "decision scope differs from packet")

    accepted: list[dict[str, Any]] = []
    for decision in decisions:
        candidate = candidates[decision["candidate_id"]]
        status = decision.get("decision")
        _require(status in {"ACCEPT", "REJECT"}, "PENDING or unknown candidate decision remains")
        if status == "REJECT":
            _require(
                isinstance(decision.get("rejection_reason"), str) and decision["rejection_reason"].strip(),
                "rejected candidate needs a reason",
            )
            continue
        family = candidate["field_family"]
        _require(
            decision.get("confirmed_source_locator") == candidate["source_locator"],
            "accepted source locator does not match packet",
        )
        _require(
            isinstance(decision.get("project_ref"), str) and decision["project_ref"].strip(),
            "accepted field needs a project_ref",
        )
        _require(decision.get("unit") == EXPECTED_UNITS[family], "accepted field unit mismatch")
        _require(decision.get("tax_status") in ALLOWED_TAX_STATUS, "accepted field tax status is incomplete")
        _require(
            isinstance(decision.get("business_meaning"), str) and decision["business_meaning"].strip(),
            "accepted field business meaning is required",
        )
        value = decision.get("canonical_value")
        if family == "PROJECT_IDENTITY":
            _require(isinstance(value, str) and value.strip(), "identity value must be non-empty text")
            _require(decision["tax_status"] == "NOT_APPLICABLE", "identity tax status must be not applicable")
        elif family == "GROSS_MARGIN":
            _require(isinstance(value, int) and not isinstance(value, bool), "margin must be integer basis points")
            _require(decision["tax_status"] == "NOT_APPLICABLE", "margin tax status must be not applicable")
        else:
            _require(isinstance(value, int) and not isinstance(value, bool), "money must be integer cents")
        if family == "COST_CATEGORY":
            _require(
                isinstance(decision.get("category_key"), str) and decision["category_key"].strip(),
                "accepted cost category needs category_key",
            )
        accepted.append({
            "candidate_id": decision["candidate_id"],
            "source_ref": candidate["source_ref"],
            "source_locator": candidate["source_locator"],
            "field_family": family,
            "project_ref": decision["project_ref"],
            "canonical_value": value,
            "unit": decision["unit"],
            "tax_status": decision["tax_status"],
            "business_meaning": decision["business_meaning"],
            "category_key": decision.get("category_key"),
        })
    _require(accepted, "signoff accepts no authoritative fields")
    return accepted


def _one(rows: list[dict[str, Any]], family: str, project_ref: str) -> dict[str, Any]:
    matches = [row for row in rows if row["field_family"] == family]
    _require(len(matches) == 1, f"project {project_ref} needs exactly one {family} field")
    return matches[0]


def build_project_summaries(accepted: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build summaries from accepted fields and enforce exact cent consistency."""

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in accepted:
        grouped[row["project_ref"]].append(row)
    summaries: list[dict[str, Any]] = []
    for project_ref, rows in sorted(grouped.items()):
        identity = _one(rows, "PROJECT_IDENTITY", project_ref)
        revenue = _one(rows, "CONTRACT_AMOUNT", project_ref)
        expenditure = _one(rows, "TOTAL_EXPENDITURE", project_ref)
        gross_profit_rows = [row for row in rows if row["field_family"] == "GROSS_PROFIT"]
        gross_margin_rows = [row for row in rows if row["field_family"] == "GROSS_MARGIN"]
        _require(len(gross_profit_rows) <= 1, f"project {project_ref} has duplicate GROSS_PROFIT fields")
        _require(len(gross_margin_rows) <= 1, f"project {project_ref} has duplicate GROSS_MARGIN fields")
        categories = [row for row in rows if row["field_family"] == "COST_CATEGORY"]
        _require(categories, f"project {project_ref} needs at least one cost category")
        _require(
            len({row["category_key"] for row in categories}) == len(categories),
            f"project {project_ref} category keys must be unique",
        )
        revenue_cents = revenue["canonical_value"]
        expenditure_cents = expenditure["canonical_value"]
        gross_profit_cents = revenue_cents - expenditure_cents
        category_total_cents = sum(row["canonical_value"] for row in categories)
        _require(category_total_cents == expenditure_cents, f"project {project_ref} category total differs by cents")
        if gross_profit_rows:
            _require(
                gross_profit_rows[0]["canonical_value"] == gross_profit_cents,
                f"project {project_ref} gross profit differs by cents",
            )
        _require(revenue_cents != 0, f"project {project_ref} revenue cannot be zero")
        with localcontext() as context:
            context.prec = 80
            calculated_margin_bps = int(
                (Decimal(gross_profit_cents) * Decimal(10000) / Decimal(revenue_cents)).quantize(
                    Decimal("1"), rounding=ROUND_HALF_UP,
                )
            )
        if gross_margin_rows:
            _require(
                calculated_margin_bps == gross_margin_rows[0]["canonical_value"],
                f"project {project_ref} gross margin does not match accepted fields",
            )
        summaries.append({
            "project_ref": project_ref,
            "project_identity": identity["canonical_value"],
            "revenue_cents": revenue_cents,
            "total_cost_cents": expenditure_cents,
            "gross_profit_cents": gross_profit_cents,
            "gross_profit_basis": (
                "CONFIRMED_SOURCE_FIELD" if gross_profit_rows
                else "DERIVED_FROM_CONFIRMED_REVENUE_AND_COST"
            ),
            "gross_margin_basis_points": calculated_margin_bps,
            "gross_margin_basis": (
                "CONFIRMED_SOURCE_FIELD" if gross_margin_rows
                else "DERIVED_FROM_CONFIRMED_REVENUE_AND_COST"
            ),
            "category_costs": [
                {"category_key": row["category_key"], "amount_cents": row["canonical_value"]}
                for row in sorted(categories, key=lambda item: item["category_key"])
            ],
            "category_total_cents": category_total_cents,
            "money_difference_cents": 0,
        })
    return summaries


def _read_ledger(path: Path = PRIVATE_VERSION_LEDGER_PATH) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            value = json.loads(line)
            _require(isinstance(value, dict), "golden ledger row must be an object")
            rows.append(value)
    previous: str | None = None
    for index, row in enumerate(rows, start=1):
        _require(row.get("version_sequence") == index, "golden ledger sequence is not append-only")
        _require(row.get("previous_record_hash") == previous, "golden ledger hash chain mismatch")
        body = {key: value for key, value in row.items() if key != "record_hash"}
        _require(row.get("record_hash") == _sha256(body), "golden ledger record hash mismatch")
        previous = row["record_hash"]
    return rows


def build_version_record(
    signoff: dict[str, Any], packet: dict[str, Any], prior_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    accepted = validate_signoff(signoff, packet)
    summaries = build_project_summaries(accepted)
    sequence = len(prior_rows) + 1
    previous_hash = prior_rows[-1]["record_hash"] if prior_rows else None
    expected_version = f"S06P2-GOLDEN-{sequence:04d}"
    _require(signoff.get("baseline_version") == expected_version, "baseline version is not the next append-only version")
    _require(signoff.get("previous_record_hash") == previous_hash, "previous version hash binding mismatch")
    if prior_rows:
        _require(
            isinstance(signoff.get("correction_reason"), str) and signoff["correction_reason"].strip(),
            "correction must state a reason and append a new version",
        )
    body = {
        "schema_version": PRIVATE_VERSION_SCHEMA,
        "project_id": "KMFA",
        "target_release": "v1.5",
        "phase_id": RUN_PHASE_ID,
        "baseline_version": expected_version,
        "version_sequence": sequence,
        "previous_record_hash": previous_hash,
        "packet_digest": packet["packet_digest"],
        "signoff_digest": _sha256(signoff),
        "confirmer": signoff["confirmer"],
        "authorization_statement": signoff["authorization_statement"],
        "correction_reason": signoff.get("correction_reason"),
        "accepted_field_count": len(accepted),
        "resolved_candidate_count": len(signoff["decision_rows"]),
        "project_count": len(summaries),
        "project_summaries": summaries,
        "money_difference_cents": 0,
        "locked": True,
        "history_overwrite_allowed": False,
    }
    return {**body, "record_hash": _sha256(body)}


def append_version(signoff: dict[str, Any], packet: dict[str, Any]) -> dict[str, Any]:
    PRIVATE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(PRIVATE_OUTPUT_DIR, 0o700)
    prior = _read_ledger()
    record = build_version_record(signoff, packet, prior)
    flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
    descriptor = os.open(PRIVATE_VERSION_LEDGER_PATH, flags, 0o600)
    try:
        os.write(descriptor, _canonical_bytes(record) + b"\n")
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    os.chmod(PRIVATE_VERSION_LEDGER_PATH, 0o600)
    _require(_read_ledger()[-1] == record, "appended golden version failed verification")
    return record


def public_projection(
    packet: dict[str, Any], signoff: dict[str, Any] | None = None,
    ledger_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Return an aggregate-only status projection safe for the tracked tree."""

    validate_candidate_packet(packet)
    ledger_rows = ledger_rows or []
    decision_counts = {"ACCEPT": 0, "REJECT": 0, "PENDING": packet["candidate_count"]}
    signoff_status = "MISSING"
    signoff_valid = False
    project_count = 0
    accepted_count = 0
    if signoff is not None:
        try:
            accepted = validate_signoff(signoff, packet)
            summaries = build_project_summaries(accepted)
        except GoldenBaselineError:
            signoff_status = "INVALID_OR_INCOMPLETE"
        else:
            signoff_status = "VALID"
            signoff_valid = True
            project_count = len(summaries)
            accepted_count = len(accepted)
            decision_counts = dict(Counter(row["decision"] for row in signoff["decision_rows"]))
    locked = bool(ledger_rows) and signoff_valid
    if not signoff_valid:
        blocking_reason = "MISSING_VALID_HUMAN_SIGNOFF"
        acceptance_status = "BLOCKED_BY_MISSING_SIGNOFF"
    elif not ledger_rows:
        blocking_reason = "GOLDEN_VERSION_NOT_APPENDED"
        acceptance_status = "PENDING_GOLDEN_VERSION_LOCK"
    else:
        blocking_reason = None
        acceptance_status = "PENDING_FINAL_VALIDATION"
    return {
        "schema_version": PUBLIC_SCHEMA,
        "project_id": "KMFA",
        "target_release": "v1.5",
        "stage_id": "S06",
        "phase_id": RUN_PHASE_ID,
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "candidate_count": packet["candidate_count"],
        "field_family_count": len(packet["field_family_counts"]),
        "field_family_counts": packet["field_family_counts"],
        "source_group_count": len({row["source_ref"] for row in packet["candidate_records"]}),
        "decision_counts": decision_counts,
        "human_signoff_required": True,
        "human_signoff_status": signoff_status,
        "human_signoff_valid": signoff_valid,
        "accepted_field_count": accepted_count,
        "project_summary_count": project_count,
        "money_storage": "SIGNED_INTEGER_CENTS",
        "money_tolerance_cents": 0,
        "project_summary_consistent": signoff_valid,
        "golden_version_count": len(ledger_rows),
        "golden_lock_allowed": signoff_valid,
        "golden_version_locked": locked,
        "append_only_history_required": True,
        "history_overwrite_allowed": False,
        "blocking_reason": blocking_reason,
        "phase_execution_status": "EXECUTION_COMPLETE_PENDING_OWNER_SIGNOFF" if not locked else "EXECUTION_COMPLETE",
        "phase_acceptance_status": acceptance_status,
        "s06_p3_entry_allowed": False,
        "raw_mutation_performed": False,
        "public_raw_name_count": 0,
        "public_raw_hash_count": 0,
        "public_raw_text_count": 0,
        "public_raw_value_count": 0,
        "public_source_locator_count": 0,
        "public_confirmer_identity_count": 0,
        "private_review_ui_available": True,
        "private_review_host_policy": "127.0.0.1_ONLY",
        "private_review_external_asset_count": 0,
        "private_review_draft_is_private": True,
        "private_review_source_filter_available": True,
        "private_review_stable_source_order": True,
        "private_review_automatic_inference": False,
        "final_signoff_overwrite_allowed": False,
        "formal_report_generated": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }


def _review_markdown(packet: dict[str, Any]) -> str:
    lines = [
        "# v1.5 S06-P2 私有人工确认清单",
        "",
        "此文件包含私有原始派生内容，只能在本机 private runtime 审阅。",
        "请复制 `private_human_signoff_template.json` 为 `private_human_signoff.json`，",
        "逐项填写 ACCEPT/REJECT、项目引用、规范值、单位、税口径、业务含义和定位确认。",
        f"所有 {packet['candidate_count']} 个候选必须完成决策；任何 PENDING 都会阻止黄金版本锁定。",
        "",
        "| candidate_id | family | source_ref | locator | raw/display candidate |",
        "|---|---|---|---|---|",
    ]
    for row in packet["candidate_records"]:
        display = str(row.get("raw_text") or row.get("cached_display_value") or "").replace("|", "\\|").replace("\n", " ")
        locator = str(row["source_locator"]).replace("|", "\\|")
        lines.append(
            f"| {row['candidate_id']} | {row['field_family']} | {row['source_ref']} | "
            f"{locator} | {display} |"
        )
    return "\n".join(lines) + "\n"


def prepare_private_outputs() -> dict[str, Any]:
    p1_payload = _json(P1_MANIFEST_PATH)
    packet = build_candidate_packet(p1_payload)
    template = build_signoff_template(packet)
    PRIVATE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(PRIVATE_OUTPUT_DIR, 0o700)
    for path, content in (
        (PRIVATE_PACKET_PATH, _dump(packet)),
        (PRIVATE_SIGNOFF_TEMPLATE_PATH, _dump(template)),
        (PRIVATE_REVIEW_PATH, _review_markdown(packet)),
    ):
        path.write_text(content, encoding="utf-8")
        os.chmod(path, 0o600)
    return packet


def current_public_projection() -> dict[str, Any]:
    packet = _json(PRIVATE_PACKET_PATH)
    signoff = _json(PRIVATE_SIGNOFF_PATH) if PRIVATE_SIGNOFF_PATH.exists() else None
    ledger = _read_ledger()
    return public_projection(packet, signoff, ledger)


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="KMFA v1.5 S06-P2 golden-baseline gate")
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--prepare", action="store_true")
    action.add_argument("--apply-signoff", type=Path)
    action.add_argument("--public-summary", action="store_true")
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.prepare:
        packet = prepare_private_outputs()
        print(f"PREPARED: {packet['candidate_count']} private candidates; golden lock remains closed")
        return 0
    if args.apply_signoff:
        packet = _json(PRIVATE_PACKET_PATH)
        signoff = _json(args.apply_signoff)
        record = append_version(signoff, packet)
        print(f"LOCKED: {record['baseline_version']} append-only private golden version")
        return 0
    print(_dump(current_public_projection()), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
