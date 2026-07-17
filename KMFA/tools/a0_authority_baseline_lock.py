#!/usr/bin/env python3
"""Build the A0 authority public projection without publishing private hashes.

Q5 may only be asserted when a complete ignored private fixture receipt is
present and validates.  Without it, every non-excluded record is emitted as a
fail-closed revalidation requirement.  Public records never contain value or
source digests, source anchors, filenames, or private paths.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.a0_golden_fixture import (
    DEFAULT_OUTPUT_CANDIDATES,
    FIELD_KEYS,
    PUBLIC_RECORD_SCHEMA as FIXTURE_PUBLIC_RECORD_SCHEMA,
    read_jsonl,
    validate_private_value_receipt,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OWNER_DECISION = (
    ROOT
    / "stage_artifacts"
    / "S05_P2_a0_golden_fixture"
    / "machine"
    / "owner_decision_records"
    / "excel_owner_resolution_decision.json"
)
DEFAULT_PRIVATE_FIXTURE_RECEIPT = (
    ROOT / ".codex_private_runtime" / "a0_public_projection_v2" / "a0_fixture_private_binding_receipt.json"
)
DEFAULT_OUTPUT_MANIFEST = ROOT / "metadata" / "baseline" / "a0_authority_baseline_manifest.json"
DEFAULT_OUTPUT_RECORDS = ROOT / "metadata" / "baseline" / "a0_authority_baseline_records.jsonl"

PUBLIC_SCHEMA = "kmfa.a0_authority_baseline.public_projection.v2"
PUBLIC_RECORD_SCHEMA = "kmfa.a0_authority_baseline_field.public_projection.v2"
DEFAULT_BASELINE_VERSION = "KMFA-A0-PUBLIC-PROJECTION-V2"
ALLOWED_LOCK_STATUSES = {
    "q5_locked_private_receipt_verified",
    "excluded_cross_source_support_only",
    "private_binding_revalidation_required",
}
HEX_DIGEST_RE = re.compile(r"(?i)(?:sha(?:-?256)?[:=])?[a-f0-9]{64}")
FORBIDDEN_PUBLIC_KEYS = {
    "baseline_content_hash",
    "cell_ref",
    "normalized_value",
    "normalized_value_hash",
    "normalized_value_private_ref",
    "page_ref",
    "plaintext_content",
    "raw_file_bytes",
    "raw_value",
    "raw_value_hash",
    "raw_value_private_ref",
    "sheet_ref",
    "source_package_hash",
    "source_public_inventory_path_hash",
}


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _walk_public(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_PUBLIC_KEYS:
                raise ValueError(f"forbidden public authority key {key!r} at {path}")
            _walk_public(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _walk_public(child, f"{path}[{index}]")
    elif isinstance(value, str) and HEX_DIGEST_RE.search(value):
        raise ValueError(f"digest-like value is forbidden in public authority projection at {path}")


def validate_owner_downgrade(owner_decision: dict[str, Any], known_candidates: set[str]) -> tuple[str, list[str]] | None:
    """Return an applicable v2 exclusion, or None for an unmappable legacy decision.

    A legacy filename-derived candidate ID cannot be mapped in public because
    publishing that mapping would recreate the disclosure.  Such a decision is
    retained only as an aggregate fail-closed status until a v2 private receipt
    and a v2 owner decision are supplied.
    """

    _walk_public(owner_decision)
    if owner_decision.get("decision_code") != "downgrade_to_cross_source_support":
        raise ValueError("authority projection only accepts downgrade_to_cross_source_support")
    if owner_decision.get("candidate_role") != "cross_source_support_only":
        raise ValueError("downgraded candidate must be cross_source_support_only")
    if owner_decision.get("q5_exclusion_confirmed") is not True:
        raise ValueError("downgraded candidate must confirm Q5 exclusion")
    for key in (
        "business_plaintext_committed",
        "raw_source_committed",
        "private_csv_committed",
        "q4_confirmation_claimed",
        "q5_baseline_claimed",
        "source_layer_write_allowed",
    ):
        if owner_decision.get(key) is not False:
            raise ValueError(f"owner_decision.{key} must be false")
    field_keys = list(owner_decision.get("field_keys") or [])
    if set(field_keys) != FIELD_KEYS:
        raise ValueError("owner_decision.field_keys must match required A0 fields")
    candidate_id = str(owner_decision.get("candidate_id", ""))
    if candidate_id not in known_candidates:
        return None
    return candidate_id, field_keys


def _public_record(
    fixture: dict[str, Any],
    *,
    lock_status: str,
    locked_at: str,
    locked_by_role: str,
    locked_by_ref: str,
) -> dict[str, Any]:
    source = fixture.get("source_binding") or {}
    value = fixture.get("value_binding") or {}
    q5_allowed = lock_status == "q5_locked_private_receipt_verified"
    excluded = lock_status == "excluded_cross_source_support_only"
    return {
        "record_type": "a0_authority_baseline_field_public_projection",
        "schema_version": PUBLIC_RECORD_SCHEMA,
        "stage_phase": "S05-P3",
        "fixture_candidate_id": fixture["fixture_candidate_id"],
        "candidate_id": fixture["candidate_id"],
        "a0_file_id": fixture["a0_file_id"],
        "field_key": fixture["field_key"],
        "field_label": fixture.get("field_label"),
        "lock_status": lock_status,
        "locked_at": locked_at,
        "locked_by_role": locked_by_role,
        "locked_by_ref": locked_by_ref,
        "source_status": {
            "source_file_ref": source.get("source_file_ref"),
            "source_file_format": source.get("source_file_format"),
            "source_anchor_publication_status": "private_only_not_committed",
            "private_binding_receipt_status": (
                "verified_private_receipt" if q5_allowed else "required_not_verified"
            ),
        },
        "value_status": {
            "normalized_value_kind": value.get("normalized_value_kind"),
            "private_binding_receipt_status": (
                "verified_private_receipt" if q5_allowed else "required_not_verified"
            ),
            "raw_or_normalized_digest_committed": False,
        },
        "exclusion_status": "confirmed_public_decision" if excluded else "not_applicable",
        "quality_state": {
            "machine_candidate_quality_grade": "Q3",
            "q4_human_confirmed": q5_allowed,
            "q4_human_confirmation_status": (
                "private_receipt_verified" if q5_allowed else "pending_private_receipt_revalidation"
            ),
            "q5_calculation_baseline_allowed": q5_allowed,
            "formal_report_allowed": False,
        },
        "public_repo_safety": {
            "raw_business_values_committed": False,
            "normalized_business_values_committed": False,
            "raw_file_committed": False,
            "private_csv_committed": False,
            "raw_or_normalized_digest_committed": False,
            "source_anchor_plaintext_committed": False,
        },
    }


def build_authority_baseline_lock(
    *,
    fixture_records: list[dict[str, Any]],
    owner_decision: dict[str, Any],
    private_fixture_receipt_path: Path | None = None,
    locked_at: str | None = None,
    locked_by_role: str = "authorized_delegate",
    locked_by_ref: str = "codex_s05p3_public_projection_v2",
    baseline_version: str = DEFAULT_BASELINE_VERSION,
    output_manifest: Path | None = None,
    output_records: Path | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    locked_timestamp = locked_at or datetime.now(timezone.utc).isoformat()
    if any(item.get("schema_version") != FIXTURE_PUBLIC_RECORD_SCHEMA for item in fixture_records):
        raise ValueError("authority builder requires v2 public fixture projections")
    known_candidates = {str(item.get("candidate_id")) for item in fixture_records}
    applicable_exclusion = validate_owner_downgrade(owner_decision, known_candidates)

    private_bindings: set[str] = set()
    private_receipt_verified = False
    if private_fixture_receipt_path is not None:
        receipt = validate_private_value_receipt(private_fixture_receipt_path, expected_count=len(fixture_records))
        private_bindings = {str(item.get("fixture_candidate_id")) for item in receipt["bindings"]}
        expected = {str(item.get("fixture_candidate_id")) for item in fixture_records}
        if private_bindings != expected:
            raise ValueError("private fixture receipt does not align with public fixture references")
        private_receipt_verified = True

    excluded_candidate_id = applicable_exclusion[0] if applicable_exclusion else None
    records: list[dict[str, Any]] = []
    for fixture in fixture_records:
        if fixture["candidate_id"] == excluded_candidate_id:
            status = "excluded_cross_source_support_only"
        elif private_receipt_verified and fixture["fixture_candidate_id"] in private_bindings:
            status = "q5_locked_private_receipt_verified"
        else:
            status = "private_binding_revalidation_required"
        records.append(
            _public_record(
                fixture,
                lock_status=status,
                locked_at=locked_timestamp,
                locked_by_role=locked_by_role,
                locked_by_ref=locked_by_ref,
            )
        )

    locked_count = sum(item["lock_status"] == "q5_locked_private_receipt_verified" for item in records)
    excluded_count = sum(item["lock_status"] == "excluded_cross_source_support_only" for item in records)
    pending_count = sum(item["lock_status"] == "private_binding_revalidation_required" for item in records)
    manifest = {
        "record_type": "a0_authority_baseline_public_projection",
        "schema_version": PUBLIC_SCHEMA,
        "project_id": "KMFA",
        "stage_phase": "S05-P3",
        "baseline_version": baseline_version,
        "locked_at": locked_timestamp,
        "locked_by_role": locked_by_role,
        "locked_by_ref": locked_by_ref,
        "source_fixture_ref": "KMFA/metadata/baseline/a0_golden_fixture_candidates.jsonl",
        "owner_decision_ref": "KMFA/stage_artifacts/S05_P2_a0_golden_fixture/machine/owner_decision_records/excel_owner_resolution_decision.json",
        "lock_summary": {
            "total_fixture_fields": len(fixture_records),
            "authority_records": len(records),
            "q5_locked_field_count": locked_count,
            "excluded_field_count": excluded_count,
            "private_binding_revalidation_required_count": pending_count,
            "q4_human_confirmed_count": locked_count,
            "q5_calculation_baseline_allowed_count": locked_count,
            "owner_decision_projection_status": (
                "applied_to_v2_opaque_candidate" if applicable_exclusion else "legacy_decision_unmappable_fail_closed"
            ),
            "private_fixture_receipt_status": (
                "verified_private_receipt" if private_receipt_verified else "required_not_verified"
            ),
            "formal_report_allowed": False,
            "stage5_review_completed": False,
            "github_upload_allowed": False,
        },
        "public_repo_safety": {
            "raw_business_values_committed": False,
            "normalized_business_values_committed": False,
            "raw_file_bytes_committed": False,
            "private_csv_committed": False,
            "raw_or_normalized_digest_committed": False,
            "source_anchor_plaintext_committed": False,
            "q5_claim_requires_complete_private_receipt": True,
        },
    }
    validate_authority_baseline_lock(manifest, records)
    if output_manifest is not None and output_records is not None:
        write_outputs(manifest, records, output_manifest, output_records)
    return manifest, records


def validate_authority_baseline_lock(manifest: dict[str, Any], records: list[dict[str, Any]]) -> None:
    _walk_public(manifest)
    _walk_public(records)
    if manifest.get("schema_version") != PUBLIC_SCHEMA or manifest.get("stage_phase") != "S05-P3":
        raise ValueError("invalid A0 authority public projection")
    summary = manifest.get("lock_summary") or {}
    if summary.get("formal_report_allowed") is not False or summary.get("stage5_review_completed") is not False:
        raise ValueError("authority projection must not claim stage review or formal report permission")
    if summary.get("github_upload_allowed") is not False:
        raise ValueError("authority projection must not allow GitHub upload")

    seen: set[tuple[str, str]] = set()
    counts = {status: 0 for status in ALLOWED_LOCK_STATUSES}
    for record in records:
        if record.get("schema_version") != PUBLIC_RECORD_SCHEMA or record.get("stage_phase") != "S05-P3":
            raise ValueError("invalid authority public record schema")
        key = (str(record.get("fixture_candidate_id")), str(record.get("field_key")))
        if key in seen:
            raise ValueError(f"duplicate authority field projection: {key[0]}/{key[1]}")
        seen.add(key)
        if record.get("field_key") not in FIELD_KEYS:
            raise ValueError(f"unknown authority field_key: {record.get('field_key')}")
        status = str(record.get("lock_status"))
        if status not in ALLOWED_LOCK_STATUSES:
            raise ValueError(f"invalid lock_status: {status}")
        counts[status] += 1
        quality = record.get("quality_state") or {}
        q5_expected = status == "q5_locked_private_receipt_verified"
        if quality.get("q4_human_confirmed") is not q5_expected:
            raise ValueError("Q4 confirmation must exactly follow verified private receipt lock status")
        if quality.get("q5_calculation_baseline_allowed") is not q5_expected:
            raise ValueError("Q5 permission must exactly follow verified private receipt lock status")
        if quality.get("formal_report_allowed") is not False:
            raise ValueError("authority field projection must not allow formal reports")

    if summary.get("authority_records") != len(records):
        raise ValueError("authority record count mismatch")
    if summary.get("q5_locked_field_count") != counts["q5_locked_private_receipt_verified"]:
        raise ValueError("Q5 locked count mismatch")
    if summary.get("excluded_field_count") != counts["excluded_cross_source_support_only"]:
        raise ValueError("excluded count mismatch")
    if summary.get("private_binding_revalidation_required_count") != counts["private_binding_revalidation_required"]:
        raise ValueError("private binding revalidation count mismatch")


def write_outputs(manifest: dict[str, Any], records: list[dict[str, Any]], manifest_path: Path, records_path: Path) -> None:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    records_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    records_path.write_text(
        "\n".join(json.dumps(record, ensure_ascii=False, sort_keys=True) for record in records) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build KMFA A0 authority public projection v2.")
    parser.add_argument("--fixtures", type=Path, default=DEFAULT_OUTPUT_CANDIDATES)
    parser.add_argument("--owner-decision", type=Path, default=DEFAULT_OWNER_DECISION)
    parser.add_argument("--private-fixture-receipt", type=Path)
    parser.add_argument("--output-manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--output-records", type=Path, default=DEFAULT_OUTPUT_RECORDS)
    parser.add_argument("--locked-at")
    parser.add_argument("--locked-by-role", default="authorized_delegate")
    parser.add_argument("--locked-by-ref", default="codex_s05p3_public_projection_v2")
    parser.add_argument("--baseline-version", default=DEFAULT_BASELINE_VERSION)
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args(argv)

    manifest, records = build_authority_baseline_lock(
        fixture_records=read_jsonl(args.fixtures),
        owner_decision=read_json(args.owner_decision),
        private_fixture_receipt_path=args.private_fixture_receipt,
        locked_at=args.locked_at,
        locked_by_role=args.locked_by_role,
        locked_by_ref=args.locked_by_ref,
        baseline_version=args.baseline_version,
        output_manifest=None if args.check_only else args.output_manifest,
        output_records=None if args.check_only else args.output_records,
    )
    summary = manifest["lock_summary"]
    print(
        "PASS: A0 authority public projection v2 built "
        f"(records={len(records)}, q5_locked={summary['q5_locked_field_count']}, "
        f"pending_private_revalidation={summary['private_binding_revalidation_required_count']})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
