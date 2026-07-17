#!/usr/bin/env python3
"""Validate whether KMFA S05-P2 may be closed.

This gate is intentionally stricter than the S05-P2 helper validators. The
helper validators prove artifacts are public-safe; this gate decides whether the
phase has enough private evidence to move to S05-P3. Under public projection v2,
the gate remains blocked until a complete ignored private receipt is supplied
and validated; a legacy public decision cannot substitute for that receipt.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.a0_golden_fixture import (
    DEFAULT_OUTPUT_CANDIDATES,
    DEFAULT_OUTPUT_MANIFEST,
    PUBLIC_SCHEMA as PUBLIC_FIXTURE_SCHEMA,
    validate_private_value_receipt,
    validate_a0_golden_fixture,
)
from KMFA.tools.check_s05_p2_owner_decision_intake import validate_decision


EXPECTED_PENDING_CANDIDATE_ID = "A0-CAND-70023EFC7305"
EXPECTED_PENDING_FILE_ID = "A0-FILE-BAE6D90834C5"
RESOLVING_DECISIONS = {
    "provide_private_field_mapping": "owner_private_field_mapping",
    "downgrade_to_cross_source_support": "owner_downgrade_to_cross_source_support",
}


@dataclass(frozen=True)
class GateResult:
    ready: bool
    mode: str
    reason: str
    pending_fields: int
    decision_code: str


def load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"FAIL: missing file: {path}")
        raise SystemExit(1)
    except json.JSONDecodeError as exc:
        print(f"FAIL: invalid JSON in {path}: {exc}")
        raise SystemExit(1)
    if not isinstance(payload, dict):
        print(f"FAIL: {path} must contain a JSON object")
        raise SystemExit(1)
    return payload


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        print(f"FAIL: missing file: {path}")
        raise SystemExit(1)
    records: list[dict[str, Any]] = []
    for line_no, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            print(f"FAIL: invalid JSONL in {path}:{line_no}: {exc}")
            raise SystemExit(1)
        if not isinstance(payload, dict):
            print(f"FAIL: {path}:{line_no} must contain a JSON object")
            raise SystemExit(1)
        records.append(payload)
    return records


def count_pending_fields(records: list[dict[str, Any]]) -> int:
    pending = 0
    for record in records:
        value_binding = record.get("value_binding") or {}
        source_binding = record.get("source_binding") or {}
        if record.get("schema_version") == "kmfa.a0_golden_fixture_candidate.public_projection.v2":
            if value_binding.get("private_binding_receipt_status") != "verified_private_receipt":
                pending += 1
                continue
            if source_binding.get("private_binding_receipt_status") != "verified_private_receipt":
                pending += 1
            continue
        if not value_binding.get("raw_value_hash"):
            pending += 1
            continue
        if source_binding.get("source_anchor_status") != "recorded_from_private_input":
            pending += 1
    return pending


def validate_active_decision(path: Path | None) -> str:
    if path is None:
        return "none"
    decision = load_json(path)
    try:
        decision_code = validate_decision(decision)
    except SystemExit as exc:
        raise SystemExit(exc.code or 1) from None
    if decision.get("candidate_id") != EXPECTED_PENDING_CANDIDATE_ID:
        print("FAIL: decision.candidate_id does not match pending Excel candidate")
        raise SystemExit(1)
    if decision.get("file_id") != EXPECTED_PENDING_FILE_ID:
        print("FAIL: decision.file_id does not match pending Excel file")
        raise SystemExit(1)
    return decision_code


def evaluate_gate(
    manifest: dict[str, Any],
    candidates: list[dict[str, Any]],
    decision_code: str,
    private_receipt_path: Path | None = None,
) -> GateResult:
    validate_a0_golden_fixture(manifest, candidates)
    summary = manifest.get("field_summary") or {}
    pending_fields = count_pending_fields(candidates)
    if manifest.get("schema_version") == PUBLIC_FIXTURE_SCHEMA:
        summary_pending = int(summary.get("private_binding_required_count", 0)) - int(
            summary.get("private_binding_verified_count", 0)
        )
        source_pending = summary_pending
    else:
        summary_pending = int(summary.get("private_value_pending_count", pending_fields))
        source_pending = int(summary.get("source_anchor_pending_count", pending_fields))
    if pending_fields != summary_pending:
        print("FAIL: fixture pending count does not match manifest summary")
        raise SystemExit(1)
    if manifest.get("schema_version") == PUBLIC_FIXTURE_SCHEMA:
        receipt_verified = False
        if private_receipt_path is not None:
            validate_private_value_receipt(private_receipt_path, expected_count=len(candidates))
            receipt_verified = True
        if pending_fields == 0 and receipt_verified:
            return GateResult(
                ready=True,
                mode="complete_private_receipt_verified",
                reason="all_required_private_bindings_verified_outside_public_projection",
                pending_fields=0,
                decision_code=decision_code,
            )
        if decision_code == "keep_pending":
            reason = "keep_pending_decision_does_not_resolve_s05_p2"
        elif decision_code in RESOLVING_DECISIONS:
            reason = "v2_public_projection_requires_complete_private_receipt_revalidation"
        else:
            reason = "missing_complete_private_receipt_for_v2_public_projection"
        return GateResult(
            ready=False,
            mode="blocked",
            reason=reason,
            pending_fields=pending_fields,
            decision_code=decision_code,
        )
    if pending_fields == 0 and source_pending == 0:
        return GateResult(
            ready=True,
            mode="all_private_hashes_recorded",
            reason="all_required_field_hashes_and_source_anchors_recorded",
            pending_fields=0,
            decision_code=decision_code,
        )
    if decision_code in RESOLVING_DECISIONS:
        return GateResult(
            ready=True,
            mode=RESOLVING_DECISIONS[decision_code],
            reason="active_owner_or_authorized_decision_resolves_excel_candidate",
            pending_fields=pending_fields,
            decision_code=decision_code,
        )
    if decision_code == "keep_pending":
        reason = "keep_pending_decision_does_not_resolve_s05_p2"
    else:
        reason = "missing_full_private_hashes_or_resolving_owner_decision"
    return GateResult(
        ready=False,
        mode="blocked",
        reason=reason,
        pending_fields=pending_fields,
        decision_code=decision_code,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA S05-P2 completion gate.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--candidates", type=Path, default=DEFAULT_OUTPUT_CANDIDATES)
    parser.add_argument("--decision", type=Path)
    parser.add_argument("--private-receipt", type=Path)
    parser.add_argument("--expect-blocked", action="store_true")
    args = parser.parse_args(argv)

    manifest = load_json(args.manifest)
    candidates = load_jsonl(args.candidates)
    decision_code = validate_active_decision(args.decision)
    result = evaluate_gate(manifest, candidates, decision_code, args.private_receipt)

    details = (
        f"(mode={result.mode}, pending_fields={result.pending_fields}, "
        f"decision_code={result.decision_code}, reason={result.reason})"
    )
    if result.ready:
        print(f"PASS: KMFA S05-P2 completion gate ready {details}")
        return 0
    if args.expect_blocked:
        print(f"PASS: KMFA S05-P2 completion gate blocked as expected {details}")
        return 0
    print(f"BLOCKED: KMFA S05-P2 completion gate not satisfied {details}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
