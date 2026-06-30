#!/usr/bin/env python3
"""Validate public-safe S05-P2 Excel owner decision intake records.

The intake contract lets KMFA validate a future owner or authorized decision
without reading raw business files or allowing raw values into public metadata.
It does not resolve the current S05-P2 pending fields by itself.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = (
    ROOT
    / "stage_artifacts"
    / "S05_P2_a0_golden_fixture"
    / "machine"
    / "excel_owner_decision_intake_contract.json"
)
DEFAULT_PACKET = (
    ROOT
    / "stage_artifacts"
    / "S05_P2_a0_golden_fixture"
    / "machine"
    / "excel_owner_decision_packet.json"
)

EXPECTED_CANDIDATE_ID = "A0-CAND-70023EFC7305"
EXPECTED_FILE_ID = "A0-FILE-BAE6D90834C5"
EXPECTED_GATE = "KMFA-S05-P2-EXCEL-RESOLUTION-GATE"
EXPECTED_DECISIONS = {
    "provide_private_field_mapping",
    "downgrade_to_cross_source_support",
    "keep_pending",
}
EXPECTED_FIELDS = {
    "contract_amount",
    "total_expense",
    "gross_profit",
    "gross_margin",
    "cost_category",
}
EXPECTED_ACTOR_ROLES = {"owner", "authorized_delegate"}
FALSE_REQUIRED_FLAGS = {
    "business_plaintext_committed",
    "raw_source_committed",
    "private_csv_committed",
    "q4_confirmation_claimed",
    "q5_baseline_claimed",
    "source_layer_write_allowed",
}
FORBIDDEN_KEYS = {
    "raw_value",
    "normalized_value",
    "original_value",
    "plaintext_content",
    "full_file_text",
    "raw_file_bytes",
    "bank_account_number",
    "identity_document_number",
    "password",
    "token",
    "api_key",
    "private_key",
}
SHA256_REF = re.compile(r"^sha256:[0-9a-f]{64}$")


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"missing file: {path}")
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON in {path}: {exc}")
    if not isinstance(payload, dict):
        fail(f"{path} must contain a JSON object")
    return payload


def walk_forbidden_keys(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_KEYS:
                fail(f"forbidden public metadata key {key!r} at {path}")
            walk_forbidden_keys(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            walk_forbidden_keys(child, f"{path}[{index}]")


def require_equal(payload: dict[str, Any], key: str, expected: Any, label: str) -> None:
    if payload.get(key) != expected:
        fail(f"{label}.{key} mismatch")


def require_false(payload: dict[str, Any], key: str, label: str) -> None:
    if payload.get(key) is not False:
        fail(f"{label}.{key} must be false")


def require_non_empty_string(payload: dict[str, Any], key: str, label: str) -> None:
    if not isinstance(payload.get(key), str) or not payload[key].strip():
        fail(f"{label}.{key} must be a non-empty string")


def validate_contract(contract: dict[str, Any], packet: dict[str, Any]) -> None:
    walk_forbidden_keys(contract)
    require_equal(contract, "record_type", "s05_p2_excel_owner_decision_intake_contract", "contract")
    require_equal(contract, "schema_version", "kmfa.s05_p2_excel_owner_decision_intake_contract.v1", "contract")
    require_equal(contract, "project_id", "KMFA", "contract")
    require_equal(contract, "stage_id", "S05", "contract")
    require_equal(contract, "phase_id", "S05-P2", "contract")
    require_equal(contract, "current_gate", EXPECTED_GATE, "contract")
    require_equal(contract, "candidate_id", EXPECTED_CANDIDATE_ID, "contract")
    require_equal(contract, "file_id", EXPECTED_FILE_ID, "contract")
    require_equal(contract, "readiness_status", "ready_for_owner_decision_record", "contract")
    require_equal(contract, "decision_record_status", "no_owner_decision_recorded", "contract")
    require_equal(contract, "accepted_record_type", "s05_p2_excel_owner_resolution_decision", "contract")

    for key in (
        "q4_confirmation_permitted_by_intake",
        "q5_baseline_permitted_by_intake",
        "raw_or_plaintext_allowed",
        "github_upload_allowed",
    ):
        require_false(contract, key, "contract")

    if set(contract.get("allowed_decision_codes") or []) != EXPECTED_DECISIONS:
        fail("contract.allowed_decision_codes mismatch")
    if set(contract.get("pending_field_keys") or []) != EXPECTED_FIELDS:
        fail("contract.pending_field_keys mismatch")
    if set(contract.get("allowed_actor_roles") or []) != EXPECTED_ACTOR_ROLES:
        fail("contract.allowed_actor_roles mismatch")
    if set(packet.get("allowed_decision_codes") or []) != EXPECTED_DECISIONS:
        fail("owner packet allowed_decision_codes mismatch")
    if set(packet.get("pending_field_keys") or []) != EXPECTED_FIELDS:
        fail("owner packet pending_field_keys mismatch")
    for key in ("candidate_id", "file_id", "current_gate"):
        if contract.get(key) != packet.get(key):
            fail(f"contract.{key} must match owner decision packet")


def validate_common_decision_fields(decision: dict[str, Any]) -> str:
    walk_forbidden_keys(decision)
    require_equal(decision, "record_type", "s05_p2_excel_owner_resolution_decision", "decision")
    require_equal(decision, "schema_version", "kmfa.s05_p2_excel_owner_resolution_decision.v1", "decision")
    require_equal(decision, "project_id", "KMFA", "decision")
    require_equal(decision, "stage_id", "S05", "decision")
    require_equal(decision, "phase_id", "S05-P2", "decision")
    require_equal(decision, "current_gate", EXPECTED_GATE, "decision")
    require_equal(decision, "candidate_id", EXPECTED_CANDIDATE_ID, "decision")
    require_equal(decision, "file_id", EXPECTED_FILE_ID, "decision")
    if set(decision.get("field_keys") or []) != EXPECTED_FIELDS:
        fail("decision.field_keys must match pending Excel fields")

    decision_code = decision.get("decision_code")
    if decision_code not in EXPECTED_DECISIONS:
        fail("decision.decision_code is not allowed")
    if decision.get("actor_role") not in EXPECTED_ACTOR_ROLES:
        fail("actor_role must be owner or authorized_delegate")
    require_non_empty_string(decision, "actor_ref", "decision")
    require_non_empty_string(decision, "decision_time", "decision")
    for key in FALSE_REQUIRED_FLAGS:
        require_false(decision, key, "decision")
    return str(decision_code)


def validate_hash_ref_map(decision: dict[str, Any], key: str) -> None:
    refs = decision.get(key)
    if not isinstance(refs, dict):
        fail(f"decision.{key} must be an object")
    if set(refs) != EXPECTED_FIELDS:
        fail(f"decision.{key} must include every pending field")
    for field_key, value in refs.items():
        if key == "private_hash_refs" and (not isinstance(value, str) or not SHA256_REF.match(value)):
            fail(f"decision.{key}.{field_key} must be a sha256 ref")
        if key == "source_anchor_refs" and (not isinstance(value, str) or not value.strip()):
            fail(f"decision.{key}.{field_key} must be non-empty")


def validate_decision(decision: dict[str, Any]) -> str:
    decision_code = validate_common_decision_fields(decision)
    private_hash_refs = decision.get("private_hash_refs")

    if decision_code == "provide_private_field_mapping":
        validate_hash_ref_map(decision, "private_hash_refs")
        validate_hash_ref_map(decision, "source_anchor_refs")
    elif decision_code == "downgrade_to_cross_source_support":
        if private_hash_refs:
            fail("downgrade decision must not supply private_hash_refs")
        require_equal(decision, "candidate_role", "cross_source_support_only", "decision")
        if decision.get("q5_exclusion_confirmed") is not True:
            fail("downgrade decision must set q5_exclusion_confirmed=true")
        require_non_empty_string(decision, "cross_source_support_scope", "decision")
    elif decision_code == "keep_pending":
        if private_hash_refs:
            fail("keep_pending decision must not supply private_hash_refs")
        require_non_empty_string(decision, "reason_pending", "decision")
        require_non_empty_string(decision, "next_review_trigger", "decision")
    return decision_code


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA S05-P2 Excel owner decision intake.")
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--owner-packet", type=Path, default=DEFAULT_PACKET)
    parser.add_argument("--decision", type=Path)
    args = parser.parse_args(argv)

    contract = read_json(args.contract)
    packet = read_json(args.owner_packet)
    validate_contract(contract, packet)

    decision_status = "no_decision_supplied"
    decision_code = "none"
    if args.decision is not None:
        decision = read_json(args.decision)
        decision_code = validate_decision(decision)
        decision_status = "validated_public_safe"

    print(
        "PASS: KMFA S05-P2 owner decision intake check passed "
        f"(contract_status={contract['readiness_status']}, "
        f"decision_status={decision_status}, "
        f"decision_code={decision_code})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
