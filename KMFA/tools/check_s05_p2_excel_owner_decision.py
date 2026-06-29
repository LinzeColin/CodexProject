#!/usr/bin/env python3
"""Validate the KMFA S05-P2 Excel owner decision packet.

This checker verifies the public-safe owner decision packet for the remaining
Excel candidate. It does not read raw business files or private value CSVs.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PACKET = ROOT / "stage_artifacts" / "S05_P2_a0_golden_fixture" / "machine" / "excel_owner_decision_packet.json"
DEFAULT_FIXTURE_MANIFEST = ROOT / "metadata" / "baseline" / "a0_golden_fixture_manifest.json"
DEFAULT_FIXTURE_CANDIDATES = ROOT / "metadata" / "baseline" / "a0_golden_fixture_candidates.jsonl"
DEFAULT_RESOLUTION_EVENTS = ROOT / "metadata" / "approvals" / "resolution_events.jsonl"
DEFAULT_CONTROL_EVENTS = ROOT / "metadata" / "approvals" / "control_events.jsonl"

EXPECTED_DECISIONS = {
    "provide_private_field_mapping",
    "downgrade_to_cross_source_support",
    "keep_pending",
}
EXPECTED_PENDING_FIELDS = {
    "contract_amount",
    "total_expense",
    "gross_profit",
    "gross_margin",
    "cost_category",
}
EXPECTED_CANDIDATE_ID = "A0-CAND-70023EFC7305"
EXPECTED_FILE_ID = "A0-FILE-BAE6D90834C5"
EXPECTED_EVENT_ID = "RES-KMFA-20260630-S05P2-EXCEL-OWNER-DECISION-PACKET"
EXPECTED_CONTROL_EVENT_ID = "CTRL-KMFA-20260630-S05P2-EXCEL-OWNER-DECISION-PACKET"
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


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        fail(f"missing file: {path}")
    for line_no, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            fail(f"invalid JSONL in {path}:{line_no}: {exc}")
        if not isinstance(record, dict):
            fail(f"{path}:{line_no} must be a JSON object")
        records.append(record)
    if not records:
        fail(f"{path} must not be empty")
    return records


def walk_forbidden_keys(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_KEYS:
                fail(f"forbidden public metadata key {key!r} at {path}")
            walk_forbidden_keys(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            walk_forbidden_keys(child, f"{path}[{index}]")


def require_false(payload: dict[str, Any], key: str) -> None:
    if payload.get(key) is not False:
        fail(f"{key} must be false")


def validate_packet(packet: dict[str, Any]) -> None:
    walk_forbidden_keys(packet)
    if packet.get("record_type") != "s05_p2_excel_owner_decision_packet":
        fail("invalid owner decision packet record_type")
    if packet.get("schema_version") != "kmfa.s05_p2_excel_owner_decision_packet.v1":
        fail("invalid owner decision packet schema_version")
    if packet.get("project_id") != "KMFA":
        fail("owner decision packet project_id must be KMFA")
    if packet.get("stage_id") != "S05":
        fail("owner decision packet stage_id must be S05")
    if packet.get("current_gate") != "KMFA-S05-P2-EXCEL-RESOLUTION-GATE":
        fail("owner decision packet current_gate mismatch")
    if packet.get("resolution_status") != "awaiting_owner_or_authorized_decision":
        fail("owner decision packet must await owner or authorized decision")
    if packet.get("decision_required") is not True:
        fail("owner decision packet decision_required must be true")
    if packet.get("candidate_id") != EXPECTED_CANDIDATE_ID:
        fail("owner decision packet candidate_id mismatch")
    if packet.get("file_id") != EXPECTED_FILE_ID:
        fail("owner decision packet file_id mismatch")

    for key in (
        "business_plaintext_committed",
        "public_repo_raw_files_committed",
        "private_csv_public_committed",
        "placeholder_hashes_allowed",
    ):
        require_false(packet, key)

    if set(packet.get("allowed_decision_codes") or []) != EXPECTED_DECISIONS:
        fail("owner decision packet allowed_decision_codes mismatch")
    if set(packet.get("pending_field_keys") or []) != EXPECTED_PENDING_FIELDS:
        fail("owner decision packet pending_field_keys mismatch")

    required_inputs = packet.get("required_decision_inputs") or {}
    if set(required_inputs) != EXPECTED_DECISIONS:
        fail("owner decision packet required_decision_inputs mismatch")
    if "private_hash_refs" not in required_inputs["provide_private_field_mapping"]:
        fail("provide_private_field_mapping decision must require private_hash_refs")
    if "q5_exclusion_confirmed" not in required_inputs["downgrade_to_cross_source_support"]:
        fail("downgrade decision must require q5_exclusion_confirmed")
    if "next_review_trigger" not in required_inputs["keep_pending"]:
        fail("keep_pending decision must require next_review_trigger")


def validate_counts(packet: dict[str, Any], manifest: dict[str, Any], candidates: list[dict[str, Any]]) -> None:
    summary = manifest.get("field_summary") or {}
    current_counts = packet.get("current_counts") or {}
    count_pairs = {
        "fixture_candidate_count": "fixture_candidate_count",
        "private_field_hash_recorded_count": "private_value_hash_recorded_count",
        "private_field_pending_count": "private_value_pending_count",
        "source_anchor_recorded_count": "source_anchor_recorded_count",
        "source_anchor_pending_count": "source_anchor_pending_count",
    }
    for packet_key, manifest_key in count_pairs.items():
        if current_counts.get(packet_key) != summary.get(manifest_key):
            fail(f"owner decision packet current_counts.{packet_key} must match fixture manifest")

    pending_records = [
        item
        for item in candidates
        if item.get("candidate_id") == EXPECTED_CANDIDATE_ID and item.get("a0_file_id") == EXPECTED_FILE_ID
    ]
    if len(pending_records) != 5:
        fail("Excel candidate must have exactly 5 pending field records")
    if {item.get("field_key") for item in pending_records} != EXPECTED_PENDING_FIELDS:
        fail("Excel candidate pending field set mismatch")
    for record in pending_records:
        source = record.get("source_binding") or {}
        value = record.get("value_binding") or {}
        quality = record.get("quality_state") or {}
        if source.get("source_anchor_status") != "pending_private_source_unavailable":
            fail("Excel candidate source anchors must remain pending")
        if value.get("raw_value_hash") is not None or value.get("normalized_value_hash") is not None:
            fail("Excel candidate hashes must remain pending")
        if value.get("raw_value_status") != "pending_private_source_unavailable":
            fail("Excel candidate raw value status must remain pending")
        if value.get("normalized_value_status") != "pending_private_source_unavailable":
            fail("Excel candidate normalized value status must remain pending")
        if quality.get("q4_human_confirmed") is not False:
            fail("Excel candidate must not be Q4-confirmed")
        if quality.get("q5_calculation_baseline_allowed") is not False:
            fail("Excel candidate must not allow Q5 baseline")


def validate_events(resolution_events: list[dict[str, Any]], control_events: list[dict[str, Any]]) -> None:
    resolution = next((item for item in resolution_events if item.get("event_id") == EXPECTED_EVENT_ID), None)
    if resolution is None:
        fail("missing Excel owner decision resolution event")
    walk_forbidden_keys(resolution)
    if resolution.get("decision_status") != "awaiting_owner_or_authorized_decision":
        fail("Excel owner decision resolution event status mismatch")
    if set(resolution.get("field_keys") or []) != EXPECTED_PENDING_FIELDS:
        fail("Excel owner decision resolution event field_keys mismatch")
    if resolution.get("business_plaintext_committed") is not False:
        fail("Excel owner decision resolution event must not commit business plaintext")
    if resolution.get("source_layer_write_allowed") is not False:
        fail("Excel owner decision resolution event must not allow source layer writes")
    if resolution.get("forbidden_plaintext") is not True:
        fail("Excel owner decision resolution event must set forbidden_plaintext=true")

    control = next((item for item in control_events if item.get("event_id") == EXPECTED_CONTROL_EVENT_ID), None)
    if control is None:
        fail("missing Excel owner decision control event")
    walk_forbidden_keys(control)
    if control.get("target_ref") != EXPECTED_EVENT_ID:
        fail("Excel owner decision control event target_ref mismatch")
    if control.get("raw_layer_write_allowed") is not False:
        fail("Excel owner decision control event must forbid raw layer writes")
    if control.get("forbidden_plaintext") is not True:
        fail("Excel owner decision control event must set forbidden_plaintext=true")


def validate_excel_owner_decision(
    *,
    packet_path: Path,
    fixture_manifest_path: Path,
    fixture_candidates_path: Path,
    resolution_events_path: Path,
    control_events_path: Path,
) -> dict[str, Any]:
    packet = read_json(packet_path)
    manifest = read_json(fixture_manifest_path)
    candidates = read_jsonl(fixture_candidates_path)
    resolution_events = read_jsonl(resolution_events_path)
    control_events = read_jsonl(control_events_path)

    validate_packet(packet)
    validate_counts(packet, manifest, candidates)
    validate_events(resolution_events, control_events)
    return packet


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA S05-P2 Excel owner decision packet.")
    parser.add_argument("--packet", type=Path, default=DEFAULT_PACKET)
    parser.add_argument("--fixture-manifest", type=Path, default=DEFAULT_FIXTURE_MANIFEST)
    parser.add_argument("--fixture-candidates", type=Path, default=DEFAULT_FIXTURE_CANDIDATES)
    parser.add_argument("--resolution-events", type=Path, default=DEFAULT_RESOLUTION_EVENTS)
    parser.add_argument("--control-events", type=Path, default=DEFAULT_CONTROL_EVENTS)
    args = parser.parse_args(argv)

    packet = validate_excel_owner_decision(
        packet_path=args.packet,
        fixture_manifest_path=args.fixture_manifest,
        fixture_candidates_path=args.fixture_candidates,
        resolution_events_path=args.resolution_events,
        control_events_path=args.control_events,
    )
    print(
        "PASS: KMFA S05-P2 Excel owner decision check passed "
        f"(allowed_decisions={len(packet['allowed_decision_codes'])}, "
        f"pending_fields={len(packet['pending_field_keys'])}, "
        f"status={packet['resolution_status']})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
