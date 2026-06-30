#!/usr/bin/env python3
"""Build KMFA S05-P3 public-safe A0 authority baseline lock metadata.

S05-P3 locks only field candidates that already have private value hashes and
source anchors. Candidates resolved by owner/authorized downgrade are retained
as explicit exclusions so unconfirmed fields cannot enter formal reports.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.a0_golden_fixture import DEFAULT_OUTPUT_CANDIDATES, FIELD_KEYS


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OWNER_DECISION = (
    ROOT
    / "stage_artifacts"
    / "S05_P2_a0_golden_fixture"
    / "machine"
    / "owner_decision_records"
    / "excel_owner_resolution_decision.json"
)
DEFAULT_OUTPUT_MANIFEST = ROOT / "metadata" / "baseline" / "a0_authority_baseline_manifest.json"
DEFAULT_OUTPUT_RECORDS = ROOT / "metadata" / "baseline" / "a0_authority_baseline_records.jsonl"

HASH_RE = re.compile(r"^sha256:[a-f0-9]{64}$")
FORBIDDEN_PUBLIC_KEYS = {
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
ALLOWED_LOCK_STATUSES = {
    "q5_locked_public_safe_hash_baseline",
    "excluded_cross_source_support_only",
}


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        payload = json.loads(line)
        if not isinstance(payload, dict):
            raise ValueError(f"{path}:{line_no} must contain a JSON object")
        records.append(payload)
    return records


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_payload(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def walk_forbidden_keys(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_PUBLIC_KEYS:
                raise ValueError(f"forbidden public metadata key {key!r} at {path}")
            walk_forbidden_keys(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            walk_forbidden_keys(child, f"{path}[{index}]")


def has_private_hashes_and_source_anchor(record: dict[str, Any]) -> bool:
    value_binding = record.get("value_binding") or {}
    source_binding = record.get("source_binding") or {}
    return (
        bool(value_binding.get("raw_value_hash"))
        and bool(value_binding.get("normalized_value_hash"))
        and source_binding.get("source_anchor_status") == "recorded_from_private_input"
    )


def validate_owner_downgrade(owner_decision: dict[str, Any]) -> tuple[str, str, list[str]]:
    walk_forbidden_keys(owner_decision)
    if owner_decision.get("decision_code") != "downgrade_to_cross_source_support":
        raise ValueError("S05-P3 lock currently requires downgrade_to_cross_source_support for excluded candidate")
    if owner_decision.get("candidate_role") != "cross_source_support_only":
        raise ValueError("downgraded candidate must be cross_source_support_only")
    if owner_decision.get("q5_exclusion_confirmed") is not True:
        raise ValueError("downgraded candidate must confirm q5 exclusion")
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
    field_keys = owner_decision.get("field_keys") or []
    if set(field_keys) != FIELD_KEYS:
        raise ValueError("owner_decision.field_keys must match S05 required fields")
    return str(owner_decision["candidate_id"]), str(owner_decision["file_id"]), list(field_keys)


def build_locked_record(
    record: dict[str, Any],
    *,
    locked_at: str,
    locked_by_role: str,
    locked_by_ref: str,
) -> dict[str, Any]:
    value_binding = record["value_binding"]
    source_binding = record["source_binding"]
    return {
        "record_type": "a0_authority_baseline_field_lock",
        "schema_version": "kmfa.a0_authority_baseline_field_lock.v1",
        "stage_phase": "S05-P3",
        "fixture_candidate_id": record["fixture_candidate_id"],
        "candidate_id": record["candidate_id"],
        "a0_file_id": record["a0_file_id"],
        "field_key": record["field_key"],
        "field_label": record.get("field_label"),
        "lock_status": "q5_locked_public_safe_hash_baseline",
        "locked_at": locked_at,
        "locked_by_role": locked_by_role,
        "locked_by_ref": locked_by_ref,
        "source_lock": {
            "source_file_ref": source_binding["source_file_ref"],
            "source_file_format": source_binding["source_file_format"],
            "source_package_hash": source_binding["source_package_hash"],
            "source_public_inventory_path_hash": source_binding["source_public_inventory_path_hash"],
            "source_anchor_status": source_binding["source_anchor_status"],
            "page_ref": source_binding.get("page_ref"),
            "sheet_ref": source_binding.get("sheet_ref"),
            "cell_ref": source_binding.get("cell_ref"),
        },
        "value_lock": {
            "raw_value_private_ref": value_binding["raw_value_private_ref"],
            "normalized_value_private_ref": value_binding["normalized_value_private_ref"],
            "raw_value_hash": value_binding["raw_value_hash"],
            "normalized_value_hash": value_binding["normalized_value_hash"],
            "normalized_value_kind": value_binding["normalized_value_kind"],
            "raw_value_public_committed": False,
            "normalized_value_public_committed": False,
        },
        "quality_state": {
            "machine_candidate_quality_grade": "Q3",
            "q4_human_confirmed": True,
            "q4_human_confirmation_status": "human_confirmed_public_safe_hash_lock",
            "q5_calculation_baseline_allowed": True,
            "formal_report_allowed": False,
        },
        "public_repo_safety": {
            "raw_business_values_committed": False,
            "normalized_business_values_committed": False,
            "raw_file_committed": False,
            "private_csv_committed": False,
        },
    }


def build_excluded_record(
    record: dict[str, Any],
    *,
    owner_decision: dict[str, Any],
    locked_at: str,
    locked_by_role: str,
    locked_by_ref: str,
) -> dict[str, Any]:
    return {
        "record_type": "a0_authority_baseline_field_lock",
        "schema_version": "kmfa.a0_authority_baseline_field_lock.v1",
        "stage_phase": "S05-P3",
        "fixture_candidate_id": record["fixture_candidate_id"],
        "candidate_id": record["candidate_id"],
        "a0_file_id": record["a0_file_id"],
        "field_key": record["field_key"],
        "field_label": record.get("field_label"),
        "lock_status": "excluded_cross_source_support_only",
        "locked_at": locked_at,
        "locked_by_role": locked_by_role,
        "locked_by_ref": locked_by_ref,
        "exclusion": {
            "decision_code": owner_decision["decision_code"],
            "decision_time": owner_decision["decision_time"],
            "actor_role": owner_decision["actor_role"],
            "actor_ref": owner_decision["actor_ref"],
            "candidate_role": "cross_source_support_only",
            "reason": "owner_authorized_downgrade_excludes_candidate_from_q5_baseline",
            "q5_exclusion_confirmed": True,
        },
        "quality_state": {
            "machine_candidate_quality_grade": "Q3",
            "q4_human_confirmed": False,
            "q4_human_confirmation_status": "excluded_by_owner_authorized_downgrade",
            "q5_calculation_baseline_allowed": False,
            "formal_report_allowed": False,
        },
        "public_repo_safety": {
            "raw_business_values_committed": False,
            "normalized_business_values_committed": False,
            "raw_file_committed": False,
            "private_csv_committed": False,
        },
    }


def build_authority_baseline_lock(
    *,
    fixture_records: list[dict[str, Any]],
    owner_decision: dict[str, Any],
    locked_at: str | None = None,
    locked_by_role: str = "authorized_delegate",
    locked_by_ref: str = "codex_s05p3_public_safe_authority_baseline_lock",
    baseline_version: str = "KMFA-A0-Q5-20260630-S05P3-PUBLIC-SAFE-HASH-LOCK",
    output_manifest: Path | None = None,
    output_records: Path | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    locked_timestamp = locked_at or datetime.now(timezone.utc).isoformat()
    excluded_candidate_id, excluded_file_id, excluded_fields = validate_owner_downgrade(owner_decision)
    baseline_records: list[dict[str, Any]] = []

    for record in fixture_records:
        walk_forbidden_keys(record)
        candidate_id = str(record.get("candidate_id"))
        field_key = str(record.get("field_key"))
        if candidate_id == excluded_candidate_id:
            if record.get("a0_file_id") != excluded_file_id or field_key not in excluded_fields:
                raise ValueError("excluded candidate record does not match owner decision")
            baseline_records.append(
                build_excluded_record(
                    record,
                    owner_decision=owner_decision,
                    locked_at=locked_timestamp,
                    locked_by_role=locked_by_role,
                    locked_by_ref=locked_by_ref,
                )
            )
            continue
        if has_private_hashes_and_source_anchor(record):
            baseline_records.append(
                build_locked_record(
                    record,
                    locked_at=locked_timestamp,
                    locked_by_role=locked_by_role,
                    locked_by_ref=locked_by_ref,
                )
            )
            continue
        raise ValueError(f"unresolved fixture field cannot enter S05-P3 baseline: {candidate_id}/{field_key}")

    locked_count = sum(1 for item in baseline_records if item["lock_status"] == "q5_locked_public_safe_hash_baseline")
    excluded_count = sum(1 for item in baseline_records if item["lock_status"] == "excluded_cross_source_support_only")
    manifest = {
        "record_type": "a0_authority_baseline_manifest",
        "schema_version": "kmfa.a0_authority_baseline.v1",
        "project_id": "KMFA",
        "stage_phase": "S05-P3",
        "baseline_version": baseline_version,
        "locked_at": locked_timestamp,
        "locked_by_role": locked_by_role,
        "locked_by_ref": locked_by_ref,
        "source_fixture_ref": "KMFA/metadata/baseline/a0_golden_fixture_candidates.jsonl",
        "owner_decision_ref": "KMFA/stage_artifacts/S05_P2_a0_golden_fixture/machine/owner_decision_records/excel_owner_resolution_decision.json",
        "baseline_content_hash": sha256_payload(baseline_records),
        "lock_summary": {
            "total_fixture_fields": len(fixture_records),
            "authority_records": len(baseline_records),
            "q5_locked_field_count": locked_count,
            "excluded_field_count": excluded_count,
            "q4_human_confirmed_count": locked_count,
            "q5_calculation_baseline_allowed_count": locked_count,
            "excluded_candidate_ids": sorted({excluded_candidate_id}),
            "formal_report_allowed": False,
            "stage5_review_completed": False,
            "github_upload_allowed": False,
        },
        "public_repo_safety": {
            "raw_business_values_committed": False,
            "normalized_business_values_committed": False,
            "raw_file_bytes_committed": False,
            "private_csv_committed": False,
        },
    }
    validate_authority_baseline_lock(manifest, baseline_records)
    if output_manifest is not None and output_records is not None:
        write_outputs(manifest, baseline_records, output_manifest, output_records)
    return manifest, baseline_records


def validate_authority_baseline_lock(manifest: dict[str, Any], records: list[dict[str, Any]]) -> None:
    walk_forbidden_keys(manifest)
    walk_forbidden_keys(records)
    if manifest.get("schema_version") != "kmfa.a0_authority_baseline.v1":
        raise ValueError("invalid authority baseline manifest schema_version")
    if manifest.get("stage_phase") != "S05-P3":
        raise ValueError("authority baseline manifest must be S05-P3")
    if manifest.get("baseline_content_hash") != sha256_payload(records):
        raise ValueError("authority baseline content hash mismatch")
    safety = manifest.get("public_repo_safety") or {}
    for key in (
        "raw_business_values_committed",
        "normalized_business_values_committed",
        "raw_file_bytes_committed",
        "private_csv_committed",
    ):
        if safety.get(key) is not False:
            raise ValueError(f"manifest public safety flag {key} must be false")
    summary = manifest.get("lock_summary") or {}
    if summary.get("formal_report_allowed") is not False:
        raise ValueError("S05-P3 lock alone must not allow formal report")
    if summary.get("stage5_review_completed") is not False:
        raise ValueError("S05-P3 must not claim Stage 5 review")
    if summary.get("github_upload_allowed") is not False:
        raise ValueError("S05-P3 must not allow GitHub upload")

    seen: set[tuple[str, str]] = set()
    locked_count = 0
    excluded_count = 0
    for record in records:
        if record.get("schema_version") != "kmfa.a0_authority_baseline_field_lock.v1":
            raise ValueError("invalid authority baseline record schema_version")
        if record.get("stage_phase") != "S05-P3":
            raise ValueError("authority baseline record must be S05-P3")
        key = (str(record.get("fixture_candidate_id")), str(record.get("field_key")))
        if key in seen:
            raise ValueError(f"duplicate authority baseline field lock: {key[0]}/{key[1]}")
        seen.add(key)
        if record.get("field_key") not in FIELD_KEYS:
            raise ValueError(f"unknown field_key: {record.get('field_key')}")
        if record.get("lock_status") not in ALLOWED_LOCK_STATUSES:
            raise ValueError(f"invalid lock_status: {record.get('lock_status')}")
        quality = record.get("quality_state") or {}
        if record["lock_status"] == "q5_locked_public_safe_hash_baseline":
            locked_count += 1
            value_lock = record.get("value_lock") or {}
            source_lock = record.get("source_lock") or {}
            for hash_key in ("raw_value_hash", "normalized_value_hash"):
                if not HASH_RE.match(str(value_lock.get(hash_key, ""))):
                    raise ValueError(f"locked record {hash_key} must be sha256:<64 hex>")
            if source_lock.get("source_anchor_status") != "recorded_from_private_input":
                raise ValueError("locked record must have recorded source anchor")
            if quality.get("q4_human_confirmed") is not True:
                raise ValueError("locked record must set q4_human_confirmed=true")
            if quality.get("q5_calculation_baseline_allowed") is not True:
                raise ValueError("locked record must allow q5 calculation baseline")
            if quality.get("formal_report_allowed") is not False:
                raise ValueError("locked record must not allow formal report")
        else:
            excluded_count += 1
            if record.get("exclusion", {}).get("q5_exclusion_confirmed") is not True:
                raise ValueError("excluded record must confirm q5 exclusion")
            if quality.get("q4_human_confirmed") is not False:
                raise ValueError("excluded record must not set q4 human confirmed")
            if quality.get("q5_calculation_baseline_allowed") is not False:
                raise ValueError("excluded record must not allow q5 calculation baseline")

    if summary.get("authority_records") != len(records):
        raise ValueError("manifest authority_records count mismatch")
    if summary.get("q5_locked_field_count") != locked_count:
        raise ValueError("manifest q5 locked count mismatch")
    if summary.get("excluded_field_count") != excluded_count:
        raise ValueError("manifest excluded count mismatch")


def write_outputs(manifest: dict[str, Any], records: list[dict[str, Any]], manifest_path: Path, records_path: Path) -> None:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    records_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    records_path.write_text(
        "\n".join(json.dumps(record, ensure_ascii=False, sort_keys=True) for record in records) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build KMFA S05-P3 authority baseline lock metadata.")
    parser.add_argument("--fixtures", type=Path, default=DEFAULT_OUTPUT_CANDIDATES)
    parser.add_argument("--owner-decision", type=Path, default=DEFAULT_OWNER_DECISION)
    parser.add_argument("--output-manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--output-records", type=Path, default=DEFAULT_OUTPUT_RECORDS)
    parser.add_argument("--locked-at")
    parser.add_argument("--locked-by-role", default="authorized_delegate")
    parser.add_argument("--locked-by-ref", default="codex_s05p3_public_safe_authority_baseline_lock")
    parser.add_argument("--baseline-version", default="KMFA-A0-Q5-20260630-S05P3-PUBLIC-SAFE-HASH-LOCK")
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args(argv)

    manifest, records = build_authority_baseline_lock(
        fixture_records=read_jsonl(args.fixtures),
        owner_decision=read_json(args.owner_decision),
        locked_at=args.locked_at,
        locked_by_role=args.locked_by_role,
        locked_by_ref=args.locked_by_ref,
        baseline_version=args.baseline_version,
    )
    if not args.check_only:
        write_outputs(manifest, records, args.output_manifest, args.output_records)
    summary = manifest["lock_summary"]
    print(
        "PASS: KMFA S05-P3 authority baseline lock built "
        f"(q5_locked_fields={summary['q5_locked_field_count']}, "
        f"excluded_fields={summary['excluded_field_count']}, "
        f"formal_report_allowed={summary['formal_report_allowed']})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
