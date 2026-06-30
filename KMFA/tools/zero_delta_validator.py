#!/usr/bin/env python3
"""KMFA S06-P1 zero-delta validator for integer-cent fields."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


class ZeroDeltaInputError(ValueError):
    """Raised when zero-delta input is not safe to compare."""


MISMATCH_REPORT_COLUMNS = (
    "record_id",
    "source",
    "field",
    "authoritative_value_cents",
    "system_value_cents",
    "difference_cents",
)


def _require_non_empty_text(value: Any, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ZeroDeltaInputError(f"{field_name} is required")
    return text


def _require_field_list(values: tuple[str, ...] | list[str], field_name: str) -> tuple[str, ...]:
    if not values:
        raise ZeroDeltaInputError(f"{field_name} must not be empty")
    fields = tuple(_require_non_empty_text(value, field_name) for value in values)
    if len(set(fields)) != len(fields):
        raise ZeroDeltaInputError(f"{field_name} contains duplicate entries")
    return fields


def _to_integer_cents(value: Any, field_name: str) -> int:
    if isinstance(value, bool):
        raise ZeroDeltaInputError(f"{field_name} must be integer cents, not boolean")
    if isinstance(value, float):
        raise ZeroDeltaInputError(f"{field_name} must be integer cents, not float")
    if isinstance(value, int):
        return value
    if isinstance(value, Decimal):
        integral = value.to_integral_value()
        if value != integral:
            raise ZeroDeltaInputError(f"{field_name} must be integer cents")
        return int(integral)
    if isinstance(value, str):
        text = value.strip()
        if not text or text in {"-", "--", "#"}:
            raise ZeroDeltaInputError(f"{field_name} must be integer cents")
        if text[0] in {"+", "-"}:
            sign = text[0]
            digits = text[1:]
        else:
            sign = ""
            digits = text
        if not digits.isdecimal():
            raise ZeroDeltaInputError(f"{field_name} must be integer cents")
        return int(f"{sign}{digits}")
    raise ZeroDeltaInputError(f"{field_name} has unsupported type: {type(value).__name__}")


def _record_key(record: dict[str, Any], key_fields: tuple[str, ...], label: str) -> tuple[str, ...]:
    key_values: list[str] = []
    for field_name in key_fields:
        if field_name not in record:
            raise ZeroDeltaInputError(f"{label} record missing key field: {field_name}")
        key_values.append(_require_non_empty_text(record[field_name], field_name))
    return tuple(key_values)


def _record_id_from_key(key: tuple[str, ...]) -> str:
    return "|".join(key)


def _index_records(
    records: list[dict[str, Any]],
    *,
    key_fields: tuple[str, ...],
    label: str,
) -> dict[tuple[str, ...], dict[str, Any]]:
    indexed: dict[tuple[str, ...], dict[str, Any]] = {}
    for record in records:
        if not isinstance(record, dict):
            raise ZeroDeltaInputError(f"{label} records must be objects")
        key = _record_key(record, key_fields, label)
        if key in indexed:
            raise ZeroDeltaInputError(f"{label} duplicate key: {_record_id_from_key(key)}")
        indexed[key] = record
    return indexed


def _record_source(record: dict[str, Any] | None, fallback: str) -> str:
    if not record:
        return fallback
    source = str(record.get("source") or "").strip()
    return source or fallback


def _build_mismatch(
    *,
    key: tuple[str, ...],
    field_name: str,
    authoritative_record: dict[str, Any] | None,
    system_record: dict[str, Any] | None,
    authoritative_value_cents: int | None,
    system_value_cents: int | None,
) -> dict[str, Any]:
    difference_cents = (
        None
        if authoritative_value_cents is None or system_value_cents is None
        else authoritative_value_cents - system_value_cents
    )
    return {
        "record_type": "zero_delta_mismatch",
        "schema_version": "kmfa.zero_delta_mismatch.v1",
        "record_id": _record_id_from_key(key),
        "source": f"{_record_source(authoritative_record, 'missing_authoritative_record')}=>{_record_source(system_record, 'missing_system_record')}",
        "field": field_name,
        "authoritative_value_cents": authoritative_value_cents,
        "system_value_cents": system_value_cents,
        "difference_cents": difference_cents,
    }


def validate_zero_delta(
    authoritative_records: list[dict[str, Any]],
    system_records: list[dict[str, Any]],
    *,
    key_fields: tuple[str, ...] | list[str],
    amount_fields: tuple[str, ...] | list[str],
) -> dict[str, Any]:
    """Compare authoritative and system records field-by-field in integer cents."""

    key_field_names = _require_field_list(key_fields, "key_fields")
    amount_field_names = _require_field_list(amount_fields, "amount_fields")
    authoritative_index = _index_records(
        authoritative_records,
        key_fields=key_field_names,
        label="authoritative",
    )
    system_index = _index_records(
        system_records,
        key_fields=key_field_names,
        label="system",
    )

    mismatches: list[dict[str, Any]] = []
    all_keys = sorted(set(authoritative_index) | set(system_index), key=_record_id_from_key)
    for key in all_keys:
        authoritative_record = authoritative_index.get(key)
        system_record = system_index.get(key)
        for field_name in amount_field_names:
            authoritative_value_cents = None
            system_value_cents = None
            authoritative_field_present = authoritative_record is not None and field_name in authoritative_record
            system_field_present = system_record is not None and field_name in system_record
            if authoritative_field_present:
                authoritative_value_cents = _to_integer_cents(authoritative_record[field_name], field_name)
            if system_field_present:
                system_value_cents = _to_integer_cents(system_record[field_name], field_name)
            if not authoritative_field_present or not system_field_present or authoritative_value_cents != system_value_cents:
                mismatches.append(
                    _build_mismatch(
                        key=key,
                        field_name=field_name,
                        authoritative_record=authoritative_record,
                        system_record=system_record,
                        authoritative_value_cents=authoritative_value_cents,
                        system_value_cents=system_value_cents,
                    )
                )

    zero_delta_passed = not mismatches
    return {
        "record_type": "zero_delta_validation_result",
        "schema_version": "kmfa.zero_delta_validation_result.v1",
        "stage_phase": "S06-P1",
        "status": "passed" if zero_delta_passed else "failed",
        "zero_delta_passed": zero_delta_passed,
        "zero_delta_cents": 0,
        "minimum_fail_difference_cents": 1,
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
        "raw_business_data_used": False,
        "public_safe_fixture_only": True,
    }


def write_mismatch_report(mismatches: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=MISMATCH_REPORT_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for mismatch in mismatches:
            writer.writerow(mismatch)


def validate_fixture_file(path: Path) -> dict[str, Any]:
    fixture = json.loads(path.read_text(encoding="utf-8"))
    return validate_zero_delta(
        fixture.get("authoritative_records", []),
        fixture.get("system_records", []),
        key_fields=fixture.get("key_fields", []),
        amount_fields=fixture.get("amount_fields", []),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate KMFA zero-delta integer-cent fixture records without raw business data."
    )
    parser.add_argument("--fixture", required=True, type=Path)
    parser.add_argument("--result-json", type=Path)
    parser.add_argument("--mismatch-report", type=Path)
    args = parser.parse_args(argv)

    result = validate_fixture_file(args.fixture)
    if args.result_json:
        args.result_json.parent.mkdir(parents=True, exist_ok=True)
        args.result_json.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    if args.mismatch_report:
        write_mismatch_report(result["mismatches"], args.mismatch_report)
    print(json.dumps({key: result[key] for key in ("status", "zero_delta_passed", "mismatch_count")}, ensure_ascii=False, sort_keys=True))
    return 0 if result["zero_delta_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
