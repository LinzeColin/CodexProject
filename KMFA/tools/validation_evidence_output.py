#!/usr/bin/env python3
"""KMFA S06-P3 public-safe validation evidence output utilities."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


class ValidationEvidenceError(ValueError):
    """Raised when S06-P3 validation evidence violates public-safe policy."""


MISMATCH_REPORT_COLUMNS = (
    "mismatch_id",
    "source_id",
    "file_hash",
    "field_path",
    "mapping_version",
    "formula_version",
    "status",
    "evidence_ref",
)

CLOSED_QUEUE_STATUSES = {"resolved"}
FORBIDDEN_OUTPUT_KEYS = {
    "field",
    "authoritative_value_cents",
    "system_value_cents",
    "pdf_value_cents",
    "excel_value_cents",
    "raw_value",
    "original_value",
    "plaintext_content",
    "full_file_text",
}


def _require_text(value: Any, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValidationEvidenceError(f"{field_name} is required")
    return text


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValidationEvidenceError(f"{path} must contain a JSON object")
    return data


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        record = json.loads(line)
        if not isinstance(record, dict):
            raise ValidationEvidenceError(f"{path}:{line_no} must contain a JSON object")
        records.append(record)
    return records


def _safe_hash(*parts: Any) -> str:
    return hashlib.sha256("|".join(str(part) for part in parts).encode("utf-8")).hexdigest()


def _field_ref(field_name: str) -> str:
    return f"field_ref:sha256:{_safe_hash('kmfa-s06-p3-field-ref', field_name)}"


def _safe_source_id(source_text: str) -> str:
    digest = _safe_hash("kmfa-s06-p3-source", source_text)
    return f"SRC-s06p3-zero-delta-{digest[:8]}"


def _mapping_version_for_source(source_id: str) -> str:
    return f"MAP-{source_id}-v0.1.0"


def _source_file_hash(source_text: str, evidence_ref: str) -> str:
    return f"sha256:{_safe_hash('kmfa-s06-p3-public-safe-evidence-ref', source_text, evidence_ref)}"


def _ensure_public_safe_record(record: dict[str, Any], label: str) -> None:
    if record.get("raw_business_data_used") is not False:
        raise ValidationEvidenceError(f"{label} must set raw_business_data_used=false")
    if record.get("public_safe_fixture_only") is not True:
        raise ValidationEvidenceError(f"{label} must set public_safe_fixture_only=true")


def _normalize_event_time(evidence_time: str | None) -> str:
    if evidence_time:
        return datetime.fromisoformat(evidence_time).replace(microsecond=0).isoformat()
    return datetime.now().astimezone().replace(microsecond=0).isoformat()


def _project_refs_from_mismatches(mismatches: list[dict[str, Any]]) -> set[str]:
    refs: set[str] = set()
    for mismatch in mismatches:
        refs.add(_require_text(mismatch.get("record_id"), "mismatch.record_id"))
    return refs


def _project_refs_from_queue(queue_items: list[dict[str, Any]]) -> set[str]:
    refs: set[str] = set()
    for item in queue_items:
        refs.add(_require_text(item.get("project_ref"), "queue_item.project_ref"))
    return refs


def _build_project_statuses(
    *,
    zero_delta_result: dict[str, Any],
    queue_items: list[dict[str, Any]],
    report_gate: dict[str, Any],
    evidence_refs: list[str],
    event_time: str,
) -> list[dict[str, Any]]:
    mismatches = zero_delta_result.get("mismatches")
    if not isinstance(mismatches, list):
        raise ValidationEvidenceError("zero_delta_result.mismatches must be a list")

    mismatch_projects = _project_refs_from_mismatches(mismatches)
    queue_projects = _project_refs_from_queue(queue_items)
    all_projects = sorted(mismatch_projects | queue_projects)
    if not all_projects:
        all_projects = ["SYN-PROJECT-S06P3-NO-DIFFERENCE"]

    statuses: list[dict[str, Any]] = []
    blocking_queue_items = [
        item
        for item in queue_items
        if item.get("status") not in CLOSED_QUEUE_STATUSES
    ]
    for project_ref in all_projects:
        hard_blocks: list[str] = []
        project_mismatch_count = sum(1 for mismatch in mismatches if mismatch.get("record_id") == project_ref)
        project_queue_count = sum(1 for item in blocking_queue_items if item.get("project_ref") == project_ref)
        if project_mismatch_count:
            hard_blocks.append("zero_delta_failed")
        if project_queue_count:
            hard_blocks.append("unresolved_critical_difference")

        q5_allowed = not hard_blocks and report_gate.get("report_grade_a_allowed") is True
        statuses.append(
            {
                "record_type": "project_validation_status",
                "schema_version": "kmfa.project_validation_status.v1",
                "stage_phase": "S06-P3",
                "project_ref": project_ref,
                "validation_status": "passed" if q5_allowed else "blocked",
                "quality_grade": "Q5" if q5_allowed else "Q4",
                "q5_allowed": q5_allowed,
                "report_grade_a_allowed": q5_allowed,
                "maximum_report_grade": "A" if q5_allowed else str(report_gate.get("maximum_report_grade") or "B"),
                "hard_blocks": hard_blocks,
                "zero_delta_passed": project_mismatch_count == 0,
                "mismatch_count": project_mismatch_count,
                "unresolved_difference_count": project_queue_count,
                "evidence_refs": evidence_refs,
                "event_time": event_time,
                "forbidden_plaintext": True,
                "raw_business_data_used": False,
                "public_safe_fixture_only": True,
            }
        )
    return statuses


def _build_mismatch_rows(mismatches: list[dict[str, Any]], source_mismatch_report_ref: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for mismatch in mismatches:
        record_id = _require_text(mismatch.get("record_id"), "mismatch.record_id")
        field_name = _require_text(mismatch.get("field"), "mismatch.field")
        source_text = _require_text(mismatch.get("source"), "mismatch.source")
        source_id = _safe_source_id(source_text)
        mismatch_id = f"MM-S06P3-{_safe_hash('kmfa-s06-p3-mismatch', record_id, field_name, source_text)[:16]}"
        rows.append(
            {
                "mismatch_id": mismatch_id,
                "source_id": source_id,
                "file_hash": _source_file_hash(source_text, source_mismatch_report_ref),
                "field_path": _field_ref(field_name),
                "mapping_version": _mapping_version_for_source(source_id),
                "formula_version": "FORM-KMFA-S06P3-VALIDATION-EVIDENCE-v0.1.0",
                "status": "zero_delta_failed",
                "evidence_ref": source_mismatch_report_ref,
            }
        )
    return rows


def _build_metadata_queue_records(queue_items: list[dict[str, Any]], source_queue_ref: str, event_time: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for item in queue_items:
        _ensure_public_safe_record(item, "queue_item")
        for flag in ("auto_correction_allowed", "averaging_allowed", "rounding_mask_allowed", "auto_selection_allowed"):
            if item.get(flag) is not False:
                raise ValidationEvidenceError(f"queue_item.{flag} must be false")
        if item.get("report_grade_a_allowed") is not False and item.get("status") not in CLOSED_QUEUE_STATUSES:
            raise ValidationEvidenceError("unresolved queue item must block report grade A")
        source_ids = [
            _require_text(source_ref.get("source_id"), "queue_item.source_ref.source_id")
            for source_ref in item.get("source_refs", [])
            if isinstance(source_ref, dict)
        ]
        source_anchor_refs = [
            _require_text(source_ref.get("source_anchor_ref"), "queue_item.source_ref.source_anchor_ref")
            for source_ref in item.get("source_refs", [])
            if isinstance(source_ref, dict)
        ]
        records.append(
            {
                "record_type": "source_difference_queue_item",
                "schema_version": "kmfa.source_difference_queue.v1",
                "stage_phase": "S06-P3",
                "queue_id": _require_text(item.get("queue_id"), "queue_item.queue_id"),
                "project_ref": _require_text(item.get("project_ref"), "queue_item.project_ref"),
                "field_path": _field_ref(_require_text(item.get("field"), "queue_item.field")),
                "source_ids": source_ids,
                "source_anchor_refs": source_anchor_refs,
                "difference_cents": int(item.get("difference_cents")),
                "status": _require_text(item.get("status"), "queue_item.status"),
                "resolution_policy": "manual_review_required",
                "auto_correction_allowed": False,
                "averaging_allowed": False,
                "rounding_mask_allowed": False,
                "auto_selection_allowed": False,
                "report_grade_a_allowed": False,
                "raw_layer_write_allowed": False,
                "raw_source_mutation_allowed": False,
                "target_layer": "metadata",
                "evidence_ref": source_queue_ref,
                "event_time": event_time,
                "forbidden_plaintext": True,
                "raw_business_data_used": False,
                "public_safe_fixture_only": True,
            }
        )
    return records


def _assert_no_forbidden_output_keys(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_OUTPUT_KEYS:
                raise ValidationEvidenceError(f"forbidden output key {key!r} at {path}")
            _assert_no_forbidden_output_keys(child, f"{path}.{key}")
    elif isinstance(value, list):
        for idx, child in enumerate(value):
            _assert_no_forbidden_output_keys(child, f"{path}[{idx}]")


def build_validation_evidence(
    *,
    zero_delta_result: dict[str, Any],
    queue_items: list[dict[str, Any]],
    report_gate: dict[str, Any],
    evidence_time: str | None,
    source_result_ref: str,
    source_mismatch_report_ref: str,
    source_queue_ref: str,
    source_gate_ref: str,
) -> dict[str, Any]:
    """Build public-safe S06-P3 validation evidence records."""

    _ensure_public_safe_record(zero_delta_result, "zero_delta_result")
    _ensure_public_safe_record(report_gate, "report_gate")
    if zero_delta_result.get("record_type") != "zero_delta_validation_result":
        raise ValidationEvidenceError("zero_delta_result record_type mismatch")
    if zero_delta_result.get("stage_phase") != "S06-P1":
        raise ValidationEvidenceError("zero_delta_result must come from S06-P1")
    if report_gate.get("stage_phase") != "S06-P2":
        raise ValidationEvidenceError("report_gate must come from S06-P2")

    mismatches = zero_delta_result.get("mismatches")
    if not isinstance(mismatches, list):
        raise ValidationEvidenceError("zero_delta_result.mismatches must be a list")
    if int(zero_delta_result.get("mismatch_count", -1)) != len(mismatches):
        raise ValidationEvidenceError("zero_delta_result mismatch_count does not match mismatches length")
    if any(not isinstance(item, dict) for item in queue_items):
        raise ValidationEvidenceError("queue_items must contain objects")

    event_time = _normalize_event_time(evidence_time)
    evidence_refs = [
        _require_text(source_result_ref, "source_result_ref"),
        _require_text(source_mismatch_report_ref, "source_mismatch_report_ref"),
        _require_text(source_queue_ref, "source_queue_ref"),
        _require_text(source_gate_ref, "source_gate_ref"),
    ]
    result_id = f"ZDR-S06P3-{_safe_hash('kmfa-s06-p3-result', source_result_ref, event_time)[:16]}"
    quality_result_id = f"DQR-S06P3-{_safe_hash('kmfa-s06-p3-data-quality', source_result_ref, event_time)[:16]}"
    project_statuses = _build_project_statuses(
        zero_delta_result=zero_delta_result,
        queue_items=queue_items,
        report_gate=report_gate,
        evidence_refs=evidence_refs,
        event_time=event_time,
    )
    mismatch_rows = _build_mismatch_rows(mismatches, source_mismatch_report_ref)
    metadata_queue_records = _build_metadata_queue_records(queue_items, source_queue_ref, event_time)

    zero_delta_output = {
        "record_type": "s06_p3_zero_delta_result",
        "schema_version": "kmfa.s06_p3.zero_delta_result.v1",
        "stage_phase": "S06-P3",
        "result_id": result_id,
        "status": str(zero_delta_result.get("status")),
        "zero_delta_passed": zero_delta_result.get("zero_delta_passed") is True,
        "zero_delta_cents": int(zero_delta_result.get("zero_delta_cents", 0)),
        "minimum_fail_difference_cents": int(zero_delta_result.get("minimum_fail_difference_cents", 1)),
        "mismatch_count": len(mismatch_rows),
        "project_status_count": len(project_statuses),
        "source_zero_delta_result_ref": source_result_ref,
        "source_mismatch_report_ref": source_mismatch_report_ref,
        "metadata_quality_target": "KMFA/metadata/quality",
        "event_time": event_time,
        "forbidden_plaintext": True,
        "raw_business_data_used": False,
        "public_safe_fixture_only": True,
    }
    zero_delta_metadata_record = {
        "record_type": "zero_delta_result",
        "schema_version": "kmfa.zero_delta_results.v1",
        "stage_phase": "S06-P3",
        "result_id": result_id,
        "status": zero_delta_output["status"],
        "zero_delta_passed": zero_delta_output["zero_delta_passed"],
        "mismatch_count": zero_delta_output["mismatch_count"],
        "project_status_count": zero_delta_output["project_status_count"],
        "result_ref": "KMFA/stage_artifacts/S06_P3_validation_evidence_output/machine/zero_delta_result.json",
        "mismatch_report_ref": "KMFA/stage_artifacts/S06_P3_validation_evidence_output/machine/mismatch_report.csv",
        "evidence_refs": evidence_refs,
        "event_time": event_time,
        "forbidden_plaintext": True,
        "raw_business_data_used": False,
        "public_safe_fixture_only": True,
    }
    data_quality_records = [
        {
            "record_type": "data_quality_result",
            "schema_version": "kmfa.data_quality_results.v1",
            "stage_phase": "S06-P3",
            "quality_result_id": f"{quality_result_id}-{idx:02d}",
            "project_ref": status["project_ref"],
            "validation_status": status["validation_status"],
            "quality_grade": status["quality_grade"],
            "q5_allowed": status["q5_allowed"],
            "report_grade_a_allowed": status["report_grade_a_allowed"],
            "maximum_report_grade": status["maximum_report_grade"],
            "hard_blocks": status["hard_blocks"],
            "zero_delta_result_id": result_id,
            "mismatch_count": status["mismatch_count"],
            "unresolved_difference_count": status["unresolved_difference_count"],
            "evidence_refs": evidence_refs,
            "event_time": event_time,
            "forbidden_plaintext": True,
            "raw_business_data_used": False,
            "public_safe_fixture_only": True,
        }
        for idx, status in enumerate(project_statuses, 1)
    ]

    evidence = {
        "zero_delta_result": zero_delta_output,
        "project_validation_statuses": project_statuses,
        "mismatch_rows": mismatch_rows,
        "metadata_zero_delta_records": [zero_delta_metadata_record],
        "metadata_data_quality_records": data_quality_records,
        "metadata_source_difference_records": metadata_queue_records,
    }
    _assert_no_forbidden_output_keys(evidence["zero_delta_result"])
    _assert_no_forbidden_output_keys(evidence["project_validation_statuses"])
    _assert_no_forbidden_output_keys(evidence["metadata_zero_delta_records"])
    _assert_no_forbidden_output_keys(evidence["metadata_data_quality_records"])
    _assert_no_forbidden_output_keys(evidence["metadata_source_difference_records"])
    return evidence


def _write_json(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )


def _read_existing_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return _load_jsonl(path)


def _append_unique_jsonl(path: Path, records: list[dict[str, Any]], identity_field: str) -> None:
    existing = _read_existing_jsonl(path)
    by_id = {
        record.get(identity_field): record
        for record in existing
        if isinstance(record, dict) and record.get(identity_field)
    }
    output = list(existing)
    changed = False
    for record in records:
        identity = _require_text(record.get(identity_field), identity_field)
        if identity in by_id:
            if by_id[identity] != record:
                raise ValidationEvidenceError(f"{path} already contains a different record for {identity}")
            continue
        output.append(record)
        changed = True
    if changed:
        _write_jsonl(path, output)


def _append_unique_mismatch_rows(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing_rows: list[dict[str, str]] = []
    normalize_line_endings = False
    if path.exists() and path.read_text(encoding="utf-8").strip():
        normalize_line_endings = b"\r\n" in path.read_bytes()
        with path.open(encoding="utf-8", newline="") as handle:
            existing_rows = list(csv.DictReader(handle))
    by_id = {row.get("mismatch_id"): row for row in existing_rows if row.get("mismatch_id")}
    output_rows = list(existing_rows)
    changed = False
    for row in rows:
        mismatch_id = _require_text(row.get("mismatch_id"), "mismatch_id")
        if mismatch_id in by_id:
            if by_id[mismatch_id] != row:
                raise ValidationEvidenceError(f"{path} already contains a different mismatch row for {mismatch_id}")
            continue
        output_rows.append(row)
        changed = True
    if changed or not path.exists() or normalize_line_endings:
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=MISMATCH_REPORT_COLUMNS, lineterminator="\n")
            writer.writeheader()
            writer.writerows(output_rows)


def write_validation_evidence_outputs(
    evidence: dict[str, Any],
    *,
    output_dir: Path,
    metadata_quality_dir: Path,
) -> None:
    """Write S06-P3 stage evidence and append public-safe metadata/quality records."""

    _write_json(output_dir / "zero_delta_result.json", evidence["zero_delta_result"])
    _write_jsonl(output_dir / "project_validation_status.jsonl", evidence["project_validation_statuses"])
    with (output_dir / "mismatch_report.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=MISMATCH_REPORT_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(evidence["mismatch_rows"])

    _append_unique_jsonl(
        metadata_quality_dir / "zero_delta_results.jsonl",
        evidence["metadata_zero_delta_records"],
        "result_id",
    )
    _append_unique_jsonl(
        metadata_quality_dir / "data_quality_results.jsonl",
        evidence["metadata_data_quality_records"],
        "quality_result_id",
    )
    _append_unique_jsonl(
        metadata_quality_dir / "source_difference_queue.jsonl",
        evidence["metadata_source_difference_records"],
        "queue_id",
    )
    _append_unique_mismatch_rows(metadata_quality_dir / "mismatch_report.csv", evidence["mismatch_rows"])


def build_from_paths(
    *,
    zero_delta_result_path: Path,
    source_mismatch_report_path: Path,
    difference_queue_path: Path,
    report_gate_path: Path,
    evidence_time: str | None,
) -> dict[str, Any]:
    if not source_mismatch_report_path.is_file():
        raise ValidationEvidenceError(f"source mismatch report not found: {source_mismatch_report_path}")
    return build_validation_evidence(
        zero_delta_result=_load_json(zero_delta_result_path),
        queue_items=_load_jsonl(difference_queue_path),
        report_gate=_load_json(report_gate_path),
        evidence_time=evidence_time,
        source_result_ref=str(zero_delta_result_path),
        source_mismatch_report_ref=str(source_mismatch_report_path),
        source_queue_ref=str(difference_queue_path),
        source_gate_ref=str(report_gate_path),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate KMFA S06-P3 public-safe validation evidence output.")
    parser.add_argument("--zero-delta-result", required=True, type=Path)
    parser.add_argument("--source-mismatch-report", required=True, type=Path)
    parser.add_argument("--difference-queue", required=True, type=Path)
    parser.add_argument("--report-gate", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--metadata-quality-dir", required=True, type=Path)
    parser.add_argument("--evidence-time")
    args = parser.parse_args(argv)

    evidence = build_from_paths(
        zero_delta_result_path=args.zero_delta_result,
        source_mismatch_report_path=args.source_mismatch_report,
        difference_queue_path=args.difference_queue,
        report_gate_path=args.report_gate,
        evidence_time=args.evidence_time,
    )
    write_validation_evidence_outputs(
        evidence,
        output_dir=args.output_dir,
        metadata_quality_dir=args.metadata_quality_dir,
    )
    print(
        json.dumps(
            {
                "zero_delta_passed": evidence["zero_delta_result"]["zero_delta_passed"],
                "mismatches": evidence["zero_delta_result"]["mismatch_count"],
                "project_statuses": len(evidence["project_validation_statuses"]),
                "metadata_quality_records": (
                    len(evidence["metadata_zero_delta_records"])
                    + len(evidence["metadata_data_quality_records"])
                    + len(evidence["metadata_source_difference_records"])
                ),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
