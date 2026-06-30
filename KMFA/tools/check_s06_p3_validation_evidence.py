#!/usr/bin/env python3
"""Validate KMFA S06-P3 public-safe validation evidence outputs."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
STAGE_DIR = ROOT / "stage_artifacts" / "S06_P3_validation_evidence_output"
MACHINE_DIR = STAGE_DIR / "machine"
METADATA_QUALITY_DIR = ROOT / "metadata" / "quality"

FORBIDDEN_TEXT = {
    "contract_amount_cents",
    "authoritative_value_cents",
    "system_value_cents",
    "pdf_value_cents",
    "excel_value_cents",
    "raw_value",
    "original_value",
    "plaintext_content",
}


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"{path.relative_to(ROOT)} invalid JSON: {exc}")
    if not isinstance(data, dict):
        fail(f"{path.relative_to(ROOT)} must be a JSON object")
    return data


def iter_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            fail(f"{path.relative_to(ROOT)}:{line_no} invalid JSONL: {exc}")
        if not isinstance(record, dict):
            fail(f"{path.relative_to(ROOT)}:{line_no} must be a JSON object")
        records.append(record)
    if not records:
        fail(f"{path.relative_to(ROOT)} must not be empty")
    return records


def check_public_safe_text(paths: list[Path]) -> None:
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for forbidden in FORBIDDEN_TEXT:
            if forbidden in text:
                fail(f"{path.relative_to(ROOT)} contains forbidden public output text: {forbidden}")


def require_false(record: dict[str, Any], key: str, label: str) -> None:
    if record.get(key) is not False:
        fail(f"{label}.{key} must be false")


def require_true(record: dict[str, Any], key: str, label: str) -> None:
    if record.get(key) is not True:
        fail(f"{label}.{key} must be true")


def check_stage_outputs() -> None:
    zero_delta_path = MACHINE_DIR / "zero_delta_result.json"
    mismatch_path = MACHINE_DIR / "mismatch_report.csv"
    status_path = MACHINE_DIR / "project_validation_status.jsonl"
    for path in [zero_delta_path, mismatch_path, status_path]:
        if not path.is_file():
            fail(f"missing S06-P3 stage output: {path.relative_to(ROOT)}")

    zero_delta = load_json(zero_delta_path)
    if zero_delta.get("record_type") != "s06_p3_zero_delta_result":
        fail("zero_delta_result.json record_type mismatch")
    if zero_delta.get("stage_phase") != "S06-P3":
        fail("zero_delta_result.json stage_phase mismatch")
    require_false(zero_delta, "raw_business_data_used", "zero_delta_result")
    require_true(zero_delta, "public_safe_fixture_only", "zero_delta_result")
    require_true(zero_delta, "forbidden_plaintext", "zero_delta_result")
    if "mismatches" in zero_delta:
        fail("zero_delta_result.json must not inline mismatch rows")

    statuses = iter_jsonl(status_path)
    for status in statuses:
        if status.get("record_type") != "project_validation_status":
            fail("project_validation_status.jsonl record_type mismatch")
        if status.get("stage_phase") != "S06-P3":
            fail("project_validation_status.jsonl stage_phase mismatch")
        require_false(status, "raw_business_data_used", "project_validation_status")
        require_true(status, "public_safe_fixture_only", "project_validation_status")
        require_true(status, "forbidden_plaintext", "project_validation_status")
        if status.get("quality_grade") == "Q5" and status.get("hard_blocks"):
            fail("blocked project status must not be Q5")

    with mismatch_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if zero_delta.get("mismatch_count") != len(rows):
        fail("stage mismatch_report.csv row count must match zero_delta_result.json mismatch_count")
    for row in rows:
        if not row.get("field_path", "").startswith("field_ref:sha256:"):
            fail("stage mismatch_report.csv field_path must be a hash/ref, not plaintext")

    check_public_safe_text([zero_delta_path, mismatch_path, status_path])


def check_metadata_quality_outputs() -> None:
    zero_delta_records = iter_jsonl(METADATA_QUALITY_DIR / "zero_delta_results.jsonl")
    data_quality_records = iter_jsonl(METADATA_QUALITY_DIR / "data_quality_results.jsonl")
    queue_records = iter_jsonl(METADATA_QUALITY_DIR / "source_difference_queue.jsonl")
    mismatch_path = METADATA_QUALITY_DIR / "mismatch_report.csv"

    s06p3_zero_delta = [record for record in zero_delta_records if record.get("stage_phase") == "S06-P3"]
    s06p3_quality = [record for record in data_quality_records if record.get("stage_phase") == "S06-P3"]
    s06p3_queue = [record for record in queue_records if record.get("stage_phase") == "S06-P3"]
    if not s06p3_zero_delta:
        fail("metadata/quality/zero_delta_results.jsonl missing S06-P3 zero_delta_result")
    if not s06p3_quality:
        fail("metadata/quality/data_quality_results.jsonl missing S06-P3 data_quality_result")
    if not s06p3_queue:
        fail("metadata/quality/source_difference_queue.jsonl missing S06-P3 queue record")

    for record in s06p3_zero_delta + s06p3_quality + s06p3_queue:
        require_false(record, "raw_business_data_used", record["record_type"])
        require_true(record, "public_safe_fixture_only", record["record_type"])
        require_true(record, "forbidden_plaintext", record["record_type"])
    for record in s06p3_queue:
        if record.get("auto_selection_allowed") is not False:
            fail("S06-P3 metadata queue record must forbid auto selection")
        if record.get("report_grade_a_allowed") is not False:
            fail("S06-P3 unresolved metadata queue record must block report grade A")
        if not str(record.get("field_path", "")).startswith("field_ref:sha256:"):
            fail("S06-P3 metadata queue field_path must be a hash/ref")

    with mismatch_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    s06p3_rows = [row for row in rows if row.get("formula_version") == "FORM-KMFA-S06P3-VALIDATION-EVIDENCE-v0.1.0"]
    if not s06p3_rows:
        fail("metadata/quality/mismatch_report.csv missing S06-P3 sanitized mismatch row")
    for row in s06p3_rows:
        if not row.get("field_path", "").startswith("field_ref:sha256:"):
            fail("S06-P3 metadata mismatch field_path must be a hash/ref")

    check_public_safe_text(
        [
            METADATA_QUALITY_DIR / "zero_delta_results.jsonl",
            METADATA_QUALITY_DIR / "data_quality_results.jsonl",
            METADATA_QUALITY_DIR / "source_difference_queue.jsonl",
            mismatch_path,
        ]
    )


def main() -> int:
    check_stage_outputs()
    check_metadata_quality_outputs()
    print("PASS: KMFA S06-P3 validation evidence check passed (metadata_quality_records=3+)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
