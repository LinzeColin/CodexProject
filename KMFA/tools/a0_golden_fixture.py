#!/usr/bin/env python3
"""Build KMFA S05-P2 A0 golden fixture candidate metadata.

S05-P2 needs field-level bindings for contract amount, total expense, gross
profit, gross margin, and cost category. Public GitHub output may keep field
contracts, hashes, source anchors, quality status, and private value refs. It
must not keep raw business values, normalized business values, PDFs, Excels, or
the source zip.
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


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_A0_FILE_MANIFEST = ROOT / "metadata" / "baseline" / "a0_file_manifest.json"
DEFAULT_A0_PROJECT_CANDIDATES = ROOT / "metadata" / "baseline" / "a0_project_candidates.jsonl"
DEFAULT_OUTPUT_MANIFEST = ROOT / "metadata" / "baseline" / "a0_golden_fixture_manifest.json"
DEFAULT_OUTPUT_CANDIDATES = ROOT / "metadata" / "baseline" / "a0_golden_fixture_candidates.jsonl"

HASH_RE = re.compile(r"^sha256:[a-f0-9]{64}$")
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
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or [])
        missing = sorted(PRIVATE_FIELD_COLUMNS - columns)
        if missing:
            raise ValueError("private field CSV missing columns: " + ", ".join(missing))
        return list(reader)


def stable_fixture_id(candidate_id: str, field_key: str) -> str:
    return f"A0-FIX-{sha256_text(candidate_id + ':' + field_key)[:12].upper()}"


def private_ref(fixture_id: str, kind: str) -> str:
    return f"private://KMFA/S05-P2/a0_golden_fixture/{fixture_id}/{kind}"


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
    integral_basis_points = basis_points.to_integral_value()
    if basis_points != integral_basis_points:
        raise ValueError(f"gross margin cannot be represented as integer basis points: {value!r}")
    return int(integral_basis_points)


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
        basis_points = normalize_ratio_to_basis_points(raw_value)
        return f"ratio_basis_points:{basis_points}"
    if field.value_kind == "category_string":
        category = normalize_category(raw_value)
        return "category_string:" + category
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


def build_value_binding(field: FieldSpec, fixture_id: str, private_row: dict[str, str] | None) -> dict[str, Any]:
    if private_row is None:
        return {
            "raw_value_private_ref": private_ref(fixture_id, "raw"),
            "normalized_value_private_ref": private_ref(fixture_id, "normalized"),
            "raw_value_status": "pending_private_source_unavailable",
            "normalized_value_status": "pending_private_source_unavailable",
            "raw_value_hash": None,
            "normalized_value_hash": None,
            "normalized_value_kind": field.value_kind,
            "raw_value_public_committed": False,
            "normalized_value_public_committed": False,
        }

    raw_text = private_row["raw_value"]
    if not raw_text:
        raise ValueError(f"private field row missing raw value for {fixture_id}")
    normalized_hash_source = normalized_private_hash_source(field, raw_text, private_row.get("unit"))
    return {
        "raw_value_private_ref": private_ref(fixture_id, "raw"),
        "normalized_value_private_ref": private_ref(fixture_id, "normalized"),
        "raw_value_status": "hash_recorded_from_private_input",
        "normalized_value_status": "hash_recorded_from_private_input",
        "raw_value_hash": f"sha256:{sha256_text('raw:' + raw_text)}",
        "normalized_value_hash": f"sha256:{sha256_text(normalized_hash_source)}",
        "normalized_value_kind": field.value_kind,
        "raw_value_public_committed": False,
        "normalized_value_public_committed": False,
    }


def build_source_binding(
    file_record: dict[str, Any],
    private_row: dict[str, str] | None,
) -> dict[str, Any]:
    source_file_ref = (private_row or {}).get("source_file_ref") or str(file_record["a0_file_id"])
    if source_file_ref != file_record["a0_file_id"]:
        raise ValueError(f"source_file_ref does not match A0 file id: {source_file_ref}")
    page_ref = (private_row or {}).get("page_ref") or None
    sheet_ref = (private_row or {}).get("sheet_ref") or None
    cell_ref = (private_row or {}).get("cell_ref") or None
    anchor_recorded = bool(page_ref or sheet_ref or cell_ref)
    return {
        "source_file_ref": source_file_ref,
        "source_file_format": file_record["file_format"],
        "source_package_hash": file_record["source_package_hash"],
        "source_public_inventory_path_hash": file_record["member_path_hash"],
        "page_ref": page_ref,
        "sheet_ref": sheet_ref,
        "cell_ref": cell_ref,
        "source_anchor_status": "recorded_from_private_input" if anchor_recorded else "pending_private_source_unavailable",
    }


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
    generated_at: str | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    a0_manifest = read_json(a0_file_manifest)
    project_candidates = read_jsonl(a0_project_candidates)
    files_by_id = {item["a0_file_id"]: item for item in a0_manifest.get("files", [])}
    known_candidate_ids = {item["candidate_id"] for item in project_candidates}
    private_rows = index_private_rows(private_fields_csv, known_candidate_ids)
    generated_timestamp = generated_at or datetime.now(timezone.utc).isoformat()

    fixture_records: list[dict[str, Any]] = []
    for candidate in project_candidates:
        candidate_id = candidate["candidate_id"]
        a0_file_id = candidate["a0_file_id"]
        if a0_file_id not in files_by_id:
            raise ValueError(f"candidate references missing A0 file id: {a0_file_id}")
        file_record = files_by_id[a0_file_id]
        for field in FIELD_SPECS:
            fixture_id = stable_fixture_id(candidate_id, field.field_key)
            private_row = private_rows.get((candidate_id, field.field_key))
            fixture_records.append(
                {
                    "record_type": "a0_golden_fixture_candidate",
                    "schema_version": "kmfa.a0_golden_fixture_candidate.v1",
                    "fixture_candidate_id": fixture_id,
                    "candidate_id": candidate_id,
                    "a0_file_id": a0_file_id,
                    "field_key": field.field_key,
                    "field_label": field.field_label,
                    "field_required_for_a0": field.required_for_a0,
                    "source_binding": build_source_binding(file_record, private_row),
                    "value_binding": build_value_binding(field, fixture_id, private_row),
                    "quality_state": {
                        "machine_candidate_quality_grade": "Q3",
                        "q4_human_confirmed": False,
                        "q4_human_confirmation_status": "pending_human_confirmation",
                        "q5_calculation_baseline_allowed": False,
                    },
                    "public_repo_safety": {
                        "raw_business_values_committed": False,
                        "normalized_business_values_committed": False,
                        "raw_file_committed": False,
                    },
                    "next_required_phase": "S05-P3 authority baseline lock",
                }
            )

    manifest = {
        "record_type": "a0_golden_fixture_manifest",
        "schema_version": "kmfa.a0_golden_fixture.v1",
        "project_id": "KMFA",
        "stage_phase": "S05-P2",
        "generated_at": generated_timestamp,
        "a0_registration_ref": display_path(a0_file_manifest),
        "a0_project_candidates_ref": display_path(a0_project_candidates),
        "field_contract": field_contract(),
        "field_summary": {
            "a0_project_candidates": len(project_candidates),
            "required_fields_per_candidate": len(FIELD_SPECS),
            "fixture_candidate_count": len(fixture_records),
            "private_value_hash_recorded_count": sum(
                1 for item in fixture_records if item["value_binding"]["raw_value_hash"]
            ),
            "private_value_pending_count": sum(
                1 for item in fixture_records if not item["value_binding"]["raw_value_hash"]
            ),
            "source_anchor_recorded_count": sum(
                1 for item in fixture_records if item["source_binding"]["source_anchor_status"] == "recorded_from_private_input"
            ),
            "source_anchor_pending_count": sum(
                1 for item in fixture_records if item["source_binding"]["source_anchor_status"] != "recorded_from_private_input"
            ),
        },
        "quality_policy": {
            "candidate_grade": "Q3",
            "q4_requires": "human confirmation against private source values in S05-P3",
            "q5_requires": "locked authoritative baseline plus zero-delta validation in later stages",
            "formal_report_allowed": False,
        },
        "public_repo_safety": {
            "raw_business_values_committed": False,
            "normalized_business_values_committed": False,
            "raw_file_bytes_committed": False,
            "private_values_may_be_pending_without_authorized_source": True,
        },
    }
    validate_a0_golden_fixture(manifest, fixture_records)
    return manifest, fixture_records


def walk_json(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_PUBLIC_KEYS:
                raise ValueError(f"forbidden public metadata key {key!r} at {path}")
            walk_json(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            walk_json(child, f"{path}[{index}]")


def validate_a0_golden_fixture(
    manifest: dict[str, Any],
    fixture_records: list[dict[str, Any]],
    *,
    require_private_values: bool = False,
) -> None:
    walk_json(manifest)
    walk_json(fixture_records)
    if manifest.get("schema_version") != "kmfa.a0_golden_fixture.v1":
        raise ValueError("invalid A0 golden fixture manifest schema_version")
    if manifest.get("stage_phase") != "S05-P2":
        raise ValueError("A0 golden fixture manifest must be S05-P2")
    if manifest.get("public_repo_safety", {}).get("raw_business_values_committed") is not False:
        raise ValueError("raw business values must not be committed")
    if manifest.get("quality_policy", {}).get("formal_report_allowed") is not False:
        raise ValueError("S05-P2 must not allow formal reports")

    contract_keys = {item["field_key"] for item in manifest.get("field_contract", [])}
    if contract_keys != FIELD_KEYS:
        raise ValueError("field contract does not match S05-P2 required fields")
    summary = manifest.get("field_summary") or {}
    expected_count = int(summary.get("a0_project_candidates", 0)) * len(FIELD_SPECS)
    if len(fixture_records) != expected_count:
        raise ValueError("fixture candidate count does not match candidate count times field count")
    if summary.get("fixture_candidate_count") != len(fixture_records):
        raise ValueError("field summary fixture_candidate_count mismatch")

    seen: set[tuple[str, str]] = set()
    for record in fixture_records:
        if record.get("schema_version") != "kmfa.a0_golden_fixture_candidate.v1":
            raise ValueError("invalid fixture candidate schema_version")
        key = (str(record.get("candidate_id")), str(record.get("field_key")))
        if key in seen:
            raise ValueError(f"duplicate fixture candidate for {key[0]}/{key[1]}")
        seen.add(key)
        if record.get("field_key") not in FIELD_KEYS:
            raise ValueError(f"unknown fixture field_key: {record.get('field_key')}")
        source_binding = record.get("source_binding") or {}
        if not source_binding.get("source_file_ref"):
            raise ValueError("fixture candidate missing source_file_ref")
        if not HASH_RE.match(str(source_binding.get("source_package_hash", ""))):
            raise ValueError("fixture candidate source_package_hash must be sha256:<64 hex>")
        value_binding = record.get("value_binding") or {}
        if value_binding.get("raw_value_public_committed") is not False:
            raise ValueError("raw value must not be committed")
        if value_binding.get("normalized_value_public_committed") is not False:
            raise ValueError("normalized value must not be committed")
        for hash_key in ("raw_value_hash", "normalized_value_hash"):
            hash_value = value_binding.get(hash_key)
            if hash_value and not HASH_RE.match(str(hash_value)):
                raise ValueError(f"{hash_key} must be sha256:<64 hex>")
        if require_private_values and not value_binding.get("raw_value_hash"):
            raise ValueError(f"missing private value hash for {record.get('fixture_candidate_id')}")
        if not value_binding.get("raw_value_hash") and value_binding.get("raw_value_status") != "pending_private_source_unavailable":
            raise ValueError("pending raw values must be explicitly marked pending_private_source_unavailable")
        quality = record.get("quality_state") or {}
        if quality.get("machine_candidate_quality_grade") != "Q3":
            raise ValueError("S05-P2 fixture candidates must remain Q3 until human confirmation")
        if quality.get("q4_human_confirmed") is not False:
            raise ValueError("S05-P2 must not mark Q4 human confirmation complete")
        if quality.get("q5_calculation_baseline_allowed") is not False:
            raise ValueError("S05-P2 must not allow Q5 calculation baseline")


def write_outputs(
    manifest: dict[str, Any],
    fixture_records: list[dict[str, Any]],
    output_manifest: Path,
    output_candidates: Path,
) -> None:
    output_manifest.parent.mkdir(parents=True, exist_ok=True)
    output_candidates.parent.mkdir(parents=True, exist_ok=True)
    output_manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_candidates.write_text(
        "\n".join(json.dumps(item, ensure_ascii=False, sort_keys=True) for item in fixture_records) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build KMFA S05-P2 A0 golden fixture candidate metadata.")
    parser.add_argument("--a0-file-manifest", type=Path, default=DEFAULT_A0_FILE_MANIFEST)
    parser.add_argument("--a0-project-candidates", type=Path, default=DEFAULT_A0_PROJECT_CANDIDATES)
    parser.add_argument("--private-fields-csv", type=Path)
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
        generated_at=args.generated_at,
    )
    validate_a0_golden_fixture(manifest, fixture_records, require_private_values=args.require_private_values)
    if not args.check_only:
        write_outputs(manifest, fixture_records, args.output_manifest, args.output_candidates)
    summary = manifest["field_summary"]
    print(
        "PASS: A0 golden fixture candidates built "
        f"(candidates={summary['fixture_candidate_count']}, fields_per_candidate={summary['required_fields_per_candidate']}, "
        f"private_value_hash_recorded={summary['private_value_hash_recorded_count']}, "
        f"private_value_pending={summary['private_value_pending_count']})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
