#!/usr/bin/env python3
"""Build KMFA S03-P2 source check matrix metadata records.

This tool works only with metadata records. It does not read or mutate raw
business files, raw extracted values, or source-system records.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.file_import_register import parse_received_at, sha256_bytes, slugify


ALLOWED_STATUSES = ("已就绪", "部分/阻塞", "失败/不适用", "已过期", "人工复核")
REQUIRED_DIMENSIONS = (
    "source_system",
    "business_segment",
    "source_package_ref",
    "entity_ref",
    "account_ref",
    "frequency",
)


def validate_status(status: str) -> str:
    if status not in ALLOWED_STATUSES:
        raise ValueError(f"invalid source check status: {status!r}; allowed={';'.join(ALLOWED_STATUSES)}")
    return status


def require_text(value: str, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field_name} is required")
    return text


def get_registration_parts(registration: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    import_run = registration.get("import_run")
    manifest = registration.get("raw_file_manifest")
    if not isinstance(import_run, dict) or not isinstance(manifest, dict):
        raise ValueError("registration must contain import_run and raw_file_manifest objects")
    for field in ("import_run_id", "source_id"):
        require_text(import_run.get(field, ""), f"import_run.{field}")
    for field in ("file_hash", "source_package_ref"):
        if field not in manifest:
            raise ValueError(f"raw_file_manifest.{field} is required")
    if not isinstance(manifest["source_package_ref"], dict):
        raise ValueError("raw_file_manifest.source_package_ref must be an object")
    return import_run, manifest


def build_matrix_id(parts: list[str]) -> str:
    return "SCM-" + sha256_bytes("|".join(parts).encode("utf-8"))[:16]


def build_source_matrix_row(
    registration: dict[str, Any],
    *,
    source_system: str,
    business_segment: str,
    entity_ref: str,
    account_ref: str,
    frequency: str,
    status: str,
    evidence_ref: str,
) -> dict[str, Any]:
    import_run, manifest = get_registration_parts(registration)
    source_package_ref = dict(manifest["source_package_ref"])
    source_system_value = slugify(require_text(source_system, "source_system"))
    business_segment_value = slugify(require_text(business_segment, "business_segment"))
    entity_ref_value = require_text(entity_ref, "entity_ref")
    account_ref_value = require_text(account_ref, "account_ref")
    frequency_value = slugify(require_text(frequency, "frequency"))
    status_value = validate_status(status)
    matrix_id = build_matrix_id(
        [
            import_run["source_id"],
            import_run["import_run_id"],
            source_system_value,
            business_segment_value,
            str(source_package_ref.get("source_package_hash", "")),
            entity_ref_value,
            account_ref_value,
            frequency_value,
        ]
    )
    return {
        "record_type": "source_check_matrix_row",
        "schema_version": "kmfa.source_check_matrix.v1",
        "stage_phase": "S03-P2",
        "matrix_id": matrix_id,
        "source_id": import_run["source_id"],
        "import_run_id": import_run["import_run_id"],
        "file_hash": manifest["file_hash"],
        "source_system": source_system_value,
        "business_segment": business_segment_value,
        "source_package_ref": source_package_ref,
        "entity_ref": entity_ref_value,
        "account_ref": account_ref_value,
        "frequency": frequency_value,
        "status": status_value,
        "allowed_statuses": list(ALLOWED_STATUSES),
        "raw_layer_write_allowed": False,
        "raw_source_mutation_allowed": False,
        "evidence_ref": require_text(evidence_ref, "evidence_ref"),
    }


def build_status_event(
    matrix_row: dict[str, Any],
    *,
    new_status: str,
    reason_code: str,
    actor_ref: str,
    event_time: str | None = None,
    evidence_ref: str,
) -> dict[str, Any]:
    previous_status = validate_status(str(matrix_row.get("status", "")))
    new_status_value = validate_status(new_status)
    timestamp = parse_received_at(event_time)
    event_id = "SSE-" + timestamp.strftime("%Y%m%d-%H%M%S") + "-" + sha256_bytes(
        f"{matrix_row.get('matrix_id')}:{previous_status}:{new_status_value}:{reason_code}".encode("utf-8")
    )[:12]
    return {
        "record_type": "source_status_event",
        "schema_version": "kmfa.source_status_event.v1",
        "stage_phase": "S03-P2",
        "event_id": event_id,
        "matrix_id": require_text(str(matrix_row.get("matrix_id", "")), "matrix_id"),
        "source_id": require_text(str(matrix_row.get("source_id", "")), "source_id"),
        "import_run_id": require_text(str(matrix_row.get("import_run_id", "")), "import_run_id"),
        "previous_status": previous_status,
        "new_status": new_status_value,
        "reason_code": slugify(require_text(reason_code, "reason_code")),
        "actor_ref": require_text(actor_ref, "actor_ref"),
        "event_time": timestamp.isoformat(),
        "target_layer": "metadata",
        "raw_layer_write_allowed": False,
        "raw_source_mutation_allowed": False,
        "evidence_ref": require_text(evidence_ref, "evidence_ref"),
    }


def append_status_event(path: str | Path, event: dict[str, Any]) -> None:
    validate_status(str(event.get("new_status", "")))
    if event.get("raw_layer_write_allowed") is not False:
        raise ValueError("source status events must not write raw layer")
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


def load_json(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("input JSON must be an object")
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build KMFA S03-P2 source check matrix metadata.")
    parser.add_argument("--registration-json", required=True)
    parser.add_argument("--source-system", required=True)
    parser.add_argument("--business-segment", required=True)
    parser.add_argument("--entity-ref", required=True)
    parser.add_argument("--account-ref", required=True)
    parser.add_argument("--frequency", required=True)
    parser.add_argument("--status", required=True, choices=ALLOWED_STATUSES)
    parser.add_argument("--evidence-ref", required=True)
    args = parser.parse_args(argv)

    row = build_source_matrix_row(
        load_json(args.registration_json),
        source_system=args.source_system,
        business_segment=args.business_segment,
        entity_ref=args.entity_ref,
        account_ref=args.account_ref,
        frequency=args.frequency,
        status=args.status,
        evidence_ref=args.evidence_ref,
    )
    print(json.dumps(row, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
