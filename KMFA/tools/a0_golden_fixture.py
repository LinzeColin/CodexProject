#!/usr/bin/env python3
"""Build the public-safe A0 field fixture projection.

Public fixture rows contain only opaque public references, the field contract,
format, quality state, and private-receipt status.  Raw/normalised value
digests and source anchors are deliberately confined to an explicitly supplied
private receipt path.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.amount_tools import AmountNormalizationError, normalize_amount_to_cents
from KMFA.tools.a0_file_register import (
    PUBLIC_CANDIDATE_SCHEMA,
    PUBLIC_FILE_SCHEMA,
    PUBLIC_SCHEMA as A0_REGISTRATION_SCHEMA,
    SOURCE_PACKAGE_REF,
    write_private_json_receipt,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_A0_FILE_MANIFEST = ROOT / "metadata" / "baseline" / "a0_file_manifest.json"
DEFAULT_A0_PROJECT_CANDIDATES = ROOT / "metadata" / "baseline" / "a0_project_candidates.jsonl"
DEFAULT_OUTPUT_MANIFEST = ROOT / "metadata" / "baseline" / "a0_golden_fixture_manifest.json"
DEFAULT_OUTPUT_CANDIDATES = ROOT / "metadata" / "baseline" / "a0_golden_fixture_candidates.jsonl"
DEFAULT_PRIVATE_RECEIPT = (
    ROOT / ".codex_private_runtime" / "a0_public_projection_v2" / "a0_fixture_private_binding_receipt.json"
)

PUBLIC_SCHEMA = "kmfa.a0_golden_fixture.public_projection.v2"
PUBLIC_RECORD_SCHEMA = "kmfa.a0_golden_fixture_candidate.public_projection.v2"
PRIVATE_RECEIPT_SCHEMA = "kmfa.private.a0_fixture_binding_receipt.v2"
OPAQUE_FIXTURE_RE = re.compile(r"^A0-FIX-PUB-V2-\d{3}-\d{2}$")
HEX_DIGEST_RE = re.compile(r"(?i)(?:sha(?:-?256)?[:=])?[a-f0-9]{64}")
PRIVATE_FIELD_COLUMNS = {
    "candidate_id",
    "field_key",
    "source_file_ref",
    "page_ref",
    "sheet_ref",
    "cell_ref",
    "raw_value",
    "unit",
}
FORBIDDEN_PUBLIC_KEYS = {
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


@dataclass(frozen=True)
class FieldSpec:
    field_key: str
    field_label: str
    value_kind: str
    required_for_a0: bool
    private_binding_required: bool


FIELD_SPECS = [
    FieldSpec("contract_amount", "合同额", "money_cents", True, True),
    FieldSpec("total_expense", "支出合计", "money_cents", True, True),
    FieldSpec("gross_profit", "毛利", "money_cents", True, True),
    FieldSpec("gross_margin", "毛利率", "ratio_basis_points", True, True),
    FieldSpec("cost_category", "成本分类", "category_string", True, True),
]
FIELD_KEYS = {item.field_key for item in FIELD_SPECS}


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


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


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or [])
        missing = sorted(PRIVATE_FIELD_COLUMNS - columns)
        if missing:
            raise ValueError("private field CSV missing columns: " + ", ".join(missing))
        return list(reader)


def normalize_ratio_to_basis_points(value: str) -> int:
    text = value.strip().replace(",", "").replace("，", "")
    if not text:
        raise ValueError("blank gross margin cannot be normalized")
    is_percent = text.endswith("%")
    if is_percent:
        text = text[:-1].strip()
    try:
        number = Decimal(text)
    except InvalidOperation as exc:
        raise ValueError(f"invalid gross margin value: {value!r}") from exc
    basis_points = number * (Decimal("100") if is_percent else Decimal("10000"))
    integral = basis_points.to_integral_value()
    if basis_points != integral:
        raise ValueError(f"gross margin cannot be represented as integer basis points: {value!r}")
    return int(integral)


def normalize_category(value: str) -> str:
    normalized = " ".join(value.strip().split())
    if not normalized:
        raise ValueError("blank cost category cannot be normalized")
    return normalized


def normalized_private_hash_source(field: FieldSpec, raw_value: str, unit: str | None) -> str:
    if field.value_kind == "money_cents":
        try:
            cents = normalize_amount_to_cents(raw_value, unit=unit or None)
        except AmountNormalizationError as exc:
            raise ValueError(f"{field.field_key} cannot be normalized to cents: {exc}") from exc
        return f"money_cents:{cents}"
    if field.value_kind == "ratio_basis_points":
        return f"ratio_basis_points:{normalize_ratio_to_basis_points(raw_value)}"
    if field.value_kind == "category_string":
        return "category_string:" + normalize_category(raw_value)
    raise ValueError(f"unsupported field value kind: {field.value_kind}")


def index_private_rows(path: Path | None, known_candidates: set[str]) -> dict[tuple[str, str], dict[str, str]]:
    if path is None:
        return {}
    indexed: dict[tuple[str, str], dict[str, str]] = {}
    for row in read_csv(path):
        candidate_id = row["candidate_id"].strip()
        field_key = row["field_key"].strip()
        if candidate_id not in known_candidates:
            raise ValueError(f"private field row references unknown candidate_id: {candidate_id}")
        if field_key not in FIELD_KEYS:
            raise ValueError(f"private field row references unknown field_key: {field_key}")
        key = (candidate_id, field_key)
        if key in indexed:
            raise ValueError(f"duplicate private field row: {candidate_id}/{field_key}")
        indexed[key] = {column: (row.get(column) or "").strip() for column in PRIVATE_FIELD_COLUMNS}
    return indexed


def _private_binding(
    *,
    candidate: dict[str, Any],
    file_record: dict[str, Any],
    field: FieldSpec,
    fixture_id: str,
    private_row: dict[str, str],
) -> dict[str, Any]:
    source_file_ref = private_row["source_file_ref"]
    if source_file_ref != file_record["source_file_ref"]:
        raise ValueError(f"private source_file_ref does not match public opaque source ref for {fixture_id}")
    raw_text = private_row["raw_value"]
    if not raw_text:
        raise ValueError(f"private field row missing raw value for {fixture_id}")
    anchor = {
        "page_ref": private_row.get("page_ref") or None,
        "sheet_ref": private_row.get("sheet_ref") or None,
        "cell_ref": private_row.get("cell_ref") or None,
    }
    if not any(anchor.values()):
        raise ValueError(f"private field row missing source anchor for {fixture_id}")
    normalized = normalized_private_hash_source(field, raw_text, private_row.get("unit"))
    return {
        "fixture_candidate_id": fixture_id,
        "candidate_id": candidate["candidate_id"],
        "a0_file_id": file_record["a0_file_id"],
        "source_file_ref": source_file_ref,
        "field_key": field.field_key,
        **anchor,
        "raw_value_sha256": sha256_text("raw:" + raw_text),
        "normalized_value_sha256": sha256_text(normalized),
        "normalized_value_kind": field.value_kind,
    }


def _write_private_receipt(path: Path, *, generated_at: str, bindings: list[dict[str, Any]]) -> None:
    payload = {
        "record_type": "a0_fixture_private_binding_receipt",
        "schema_version": PRIVATE_RECEIPT_SCHEMA,
        "classification": "private_sensitive_do_not_commit",
        "generated_at": generated_at,
        "binding_count": len(bindings),
        "bindings": bindings,
    }
    write_private_json_receipt(path, payload)


def field_contract() -> list[dict[str, Any]]:
    return [
        {
            "field_key": field.field_key,
            "field_label": field.field_label,
            "value_kind": field.value_kind,
            "required_for_a0": field.required_for_a0,
            "private_binding_required": field.private_binding_required,
            "public_value_committed_allowed": False,
        }
        for field in FIELD_SPECS
    ]


def build_a0_golden_fixture(
    *,
    a0_file_manifest: Path = DEFAULT_A0_FILE_MANIFEST,
    a0_project_candidates: Path = DEFAULT_A0_PROJECT_CANDIDATES,
    private_fields_csv: Path | None = None,
    private_receipt_path: Path | None = None,
    generated_at: str | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    a0_manifest = read_json(a0_file_manifest)
    project_candidates = read_jsonl(a0_project_candidates)
    if a0_manifest.get("schema_version") != A0_REGISTRATION_SCHEMA:
        raise ValueError("A0 fixture builder requires the v2 public registration projection")
    if any(item.get("schema_version") != PUBLIC_CANDIDATE_SCHEMA for item in project_candidates):
        raise ValueError("A0 fixture builder requires v2 public candidate projections")
    files_by_id = {item["a0_file_id"]: item for item in a0_manifest.get("files", [])}
    if any(item.get("schema_version") != PUBLIC_FILE_SCHEMA for item in files_by_id.values()):
        raise ValueError("A0 fixture builder requires v2 public file projections")
    known_candidate_ids = {item["candidate_id"] for item in project_candidates}
    private_rows = index_private_rows(private_fields_csv, known_candidate_ids)
    if private_rows and private_receipt_path is None:
        raise ValueError("private_receipt_path is required when private A0 fields are supplied")
    generated_timestamp = generated_at or datetime.now(timezone.utc).isoformat()

    fixture_records: list[dict[str, Any]] = []
    private_bindings: list[dict[str, Any]] = []
    for candidate_order, candidate in enumerate(project_candidates, start=1):
        a0_file_id = candidate["a0_file_id"]
        if a0_file_id not in files_by_id:
            raise ValueError(f"candidate references missing A0 file id: {a0_file_id}")
        file_record = files_by_id[a0_file_id]
        for field_order, field in enumerate(FIELD_SPECS, start=1):
            fixture_id = f"A0-FIX-PUB-V2-{candidate_order:03d}-{field_order:02d}"
            private_row = private_rows.get((candidate["candidate_id"], field.field_key))
            receipt_status = "required_not_verified"
            if private_row is not None:
                private_bindings.append(
                    _private_binding(
                        candidate=candidate,
                        file_record=file_record,
                        field=field,
                        fixture_id=fixture_id,
                        private_row=private_row,
                    )
                )
                receipt_status = "verified_private_receipt"
            fixture_records.append(
                {
                    "record_type": "a0_golden_fixture_candidate_public_projection",
                    "schema_version": PUBLIC_RECORD_SCHEMA,
                    "fixture_candidate_id": fixture_id,
                    "candidate_id": candidate["candidate_id"],
                    "a0_file_id": a0_file_id,
                    "field_key": field.field_key,
                    "field_label": field.field_label,
                    "field_required_for_a0": field.required_for_a0,
                    "source_binding": {
                        "source_package_ref": SOURCE_PACKAGE_REF,
                        "source_file_ref": file_record["source_file_ref"],
                        "source_file_format": file_record["file_format"],
                        "source_anchor_publication_status": "private_only_not_committed",
                        "private_binding_required": True,
                        "private_binding_receipt_status": receipt_status,
                    },
                    "value_binding": {
                        "normalized_value_kind": field.value_kind,
                        "private_binding_required": True,
                        "private_binding_receipt_status": receipt_status,
                        "raw_value_public_committed": False,
                        "normalized_value_public_committed": False,
                    },
                    "quality_state": {
                        "machine_candidate_quality_grade": "Q3",
                        "q4_human_confirmed": False,
                        "q4_human_confirmation_status": "pending_private_receipt_and_human_confirmation",
                        "q5_calculation_baseline_allowed": False,
                    },
                    "public_repo_safety": {
                        "raw_business_values_committed": False,
                        "normalized_business_values_committed": False,
                        "raw_file_committed": False,
                        "raw_or_normalized_digest_committed": False,
                        "source_anchor_plaintext_committed": False,
                    },
                    "next_required_phase": "S05-P3 authority baseline lock",
                }
            )

    if private_receipt_path is not None and private_rows:
        _write_private_receipt(private_receipt_path, generated_at=generated_timestamp, bindings=private_bindings)

    manifest = {
        "record_type": "a0_golden_fixture_public_projection",
        "schema_version": PUBLIC_SCHEMA,
        "project_id": "KMFA",
        "stage_phase": "S05-P2",
        "generated_at": generated_timestamp,
        "a0_registration_ref": "KMFA/metadata/baseline/a0_file_manifest.json",
        "a0_project_candidates_ref": "KMFA/metadata/baseline/a0_project_candidates.jsonl",
        "field_contract": field_contract(),
        "field_summary": {
            "a0_project_candidates": len(project_candidates),
            "required_fields_per_candidate": len(FIELD_SPECS),
            "fixture_candidate_count": len(fixture_records),
            "private_binding_verified_count": len(private_bindings),
            "private_binding_required_count": len(fixture_records),
        },
        "quality_policy": {
            "candidate_grade": "Q3",
            "q4_requires": "private binding receipt and human confirmation",
            "q5_requires": "private authority receipt and zero-delta validation",
            "formal_report_allowed": False,
        },
        "public_repo_safety": {
            "raw_business_values_committed": False,
            "normalized_business_values_committed": False,
            "raw_file_bytes_committed": False,
            "raw_or_normalized_digest_committed": False,
            "private_binding_may_not_be_claimed_without_private_receipt": True,
        },
    }
    validate_a0_golden_fixture(manifest, fixture_records)
    return manifest, fixture_records


def _walk_public(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_PUBLIC_KEYS:
                raise ValueError(f"forbidden public fixture key {key!r} at {path}")
            _walk_public(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _walk_public(child, f"{path}[{index}]")
    elif isinstance(value, str) and HEX_DIGEST_RE.search(value):
        raise ValueError(f"digest-like value is forbidden in public fixture projection at {path}")


def validate_private_value_receipt(path: Path, *, expected_count: int | None = None) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != PRIVATE_RECEIPT_SCHEMA:
        raise ValueError("invalid private A0 fixture binding receipt schema")
    if payload.get("classification") != "private_sensitive_do_not_commit":
        raise ValueError("private A0 fixture receipt classification is invalid")
    bindings = payload.get("bindings")
    if not isinstance(bindings, list) or payload.get("binding_count") != len(bindings):
        raise ValueError("private A0 fixture receipt count mismatch")
    if expected_count is not None and len(bindings) != expected_count:
        raise ValueError("private A0 fixture receipt is incomplete")
    for binding in bindings:
        for key in ("raw_value_sha256", "normalized_value_sha256"):
            if not re.fullmatch(r"[a-f0-9]{64}", str(binding.get(key, ""))):
                raise ValueError(f"invalid private fixture digest: {key}")
    return payload


def validate_a0_golden_fixture(
    manifest: dict[str, Any],
    fixture_records: list[dict[str, Any]],
    *,
    require_private_values: bool = False,
    private_receipt_path: Path | None = None,
) -> None:
    _walk_public(manifest)
    _walk_public(fixture_records)
    if manifest.get("schema_version") != PUBLIC_SCHEMA or manifest.get("stage_phase") != "S05-P2":
        raise ValueError("invalid A0 golden fixture public projection")
    if manifest.get("public_repo_safety", {}).get("raw_business_values_committed") is not False:
        raise ValueError("raw business values must not be committed")
    if manifest.get("quality_policy", {}).get("formal_report_allowed") is not False:
        raise ValueError("S05-P2 must not allow formal reports")
    if {item["field_key"] for item in manifest.get("field_contract", [])} != FIELD_KEYS:
        raise ValueError("field contract does not match required A0 fields")
    summary = manifest.get("field_summary") or {}
    expected_count = int(summary.get("a0_project_candidates", 0)) * len(FIELD_SPECS)
    if len(fixture_records) != expected_count or summary.get("fixture_candidate_count") != len(fixture_records):
        raise ValueError("fixture candidate count mismatch")

    seen: set[tuple[str, str]] = set()
    for record in fixture_records:
        if record.get("schema_version") != PUBLIC_RECORD_SCHEMA:
            raise ValueError("invalid fixture candidate public projection schema")
        if not OPAQUE_FIXTURE_RE.fullmatch(str(record.get("fixture_candidate_id", ""))):
            raise ValueError("fixture candidate ID must be an opaque v2 public reference")
        key = (str(record.get("candidate_id")), str(record.get("field_key")))
        if key in seen:
            raise ValueError(f"duplicate fixture candidate for {key[0]}/{key[1]}")
        seen.add(key)
        if record.get("field_key") not in FIELD_KEYS:
            raise ValueError(f"unknown fixture field_key: {record.get('field_key')}")
        source_binding = record.get("source_binding") or {}
        value_binding = record.get("value_binding") or {}
        if not source_binding.get("source_file_ref") or source_binding.get("source_package_ref") != SOURCE_PACKAGE_REF:
            raise ValueError("fixture candidate missing opaque source reference")
        if value_binding.get("raw_value_public_committed") is not False or value_binding.get("normalized_value_public_committed") is not False:
            raise ValueError("fixture values must not be committed")
        quality = record.get("quality_state") or {}
        if quality.get("q4_human_confirmed") is not False or quality.get("q5_calculation_baseline_allowed") is not False:
            raise ValueError("public projection cannot claim Q4/Q5 without private authority receipt")

    if require_private_values:
        if private_receipt_path is None:
            raise ValueError("private fixture receipt is required for private binding validation")
        validate_private_value_receipt(private_receipt_path, expected_count=len(fixture_records))
        if any(
            item.get("value_binding", {}).get("private_binding_receipt_status") != "verified_private_receipt"
            for item in fixture_records
        ):
            raise ValueError("public fixture projection records an incomplete private receipt")


def write_outputs(
    manifest: dict[str, Any], fixture_records: list[dict[str, Any]], output_manifest: Path, output_candidates: Path
) -> None:
    output_manifest.parent.mkdir(parents=True, exist_ok=True)
    output_candidates.parent.mkdir(parents=True, exist_ok=True)
    output_manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_candidates.write_text(
        "\n".join(json.dumps(item, ensure_ascii=False, sort_keys=True) for item in fixture_records) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build KMFA public-safe A0 fixture projection v2.")
    parser.add_argument("--a0-file-manifest", type=Path, default=DEFAULT_A0_FILE_MANIFEST)
    parser.add_argument("--a0-project-candidates", type=Path, default=DEFAULT_A0_PROJECT_CANDIDATES)
    parser.add_argument("--private-fields-csv", type=Path)
    parser.add_argument("--private-receipt", type=Path, default=DEFAULT_PRIVATE_RECEIPT)
    parser.add_argument("--output-manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--output-candidates", type=Path, default=DEFAULT_OUTPUT_CANDIDATES)
    parser.add_argument("--generated-at")
    parser.add_argument("--require-private-values", action="store_true")
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args(argv)

    manifest, fixture_records = build_a0_golden_fixture(
        a0_file_manifest=args.a0_file_manifest,
        a0_project_candidates=args.a0_project_candidates,
        private_fields_csv=args.private_fields_csv,
        private_receipt_path=args.private_receipt if args.private_fields_csv else None,
        generated_at=args.generated_at,
    )
    validate_a0_golden_fixture(
        manifest,
        fixture_records,
        require_private_values=args.require_private_values,
        private_receipt_path=args.private_receipt if args.private_fields_csv else None,
    )
    if not args.check_only:
        write_outputs(manifest, fixture_records, args.output_manifest, args.output_candidates)
    summary = manifest["field_summary"]
    print(
        "PASS: A0 fixture public projection v2 built "
        f"(candidates={summary['fixture_candidate_count']}, "
        f"private_binding_verified={summary['private_binding_verified_count']})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
