#!/usr/bin/env python3
"""KMFA S06-P2 PDF/Excel cross-source difference queue utilities."""

from __future__ import annotations

import argparse
import json
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.file_import_register import parse_received_at, sha256_bytes, slugify
from KMFA.tools.source_priority import rank_source_candidate


class CrossSourceDifferenceQueueError(ValueError):
    """Raised when S06-P2 queue input or output violates policy."""


REQUIRED_SOURCE_REF_FIELDS = ("source_id", "source_type", "source_class", "source_anchor_ref")
ALLOWED_QUEUE_STATUSES = {"queued_for_manual_review", "under_review", "resolved", "rejected"}
CLOSED_QUEUE_STATUSES = {"resolved"}


def _require_text(value: Any, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise CrossSourceDifferenceQueueError(f"{field_name} is required")
    return text


def _to_integer_cents(value: Any, field_name: str) -> int:
    if isinstance(value, bool):
        raise CrossSourceDifferenceQueueError(f"{field_name} must be integer cents, not boolean")
    if isinstance(value, float):
        raise CrossSourceDifferenceQueueError(f"{field_name} must be integer cents, not float")
    if isinstance(value, int):
        return value
    if isinstance(value, Decimal):
        integral = value.to_integral_value()
        if value != integral:
            raise CrossSourceDifferenceQueueError(f"{field_name} must be integer cents")
        return int(integral)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            raise CrossSourceDifferenceQueueError(f"{field_name} must be integer cents")
        sign = ""
        digits = text
        if text[0] in {"+", "-"}:
            sign = text[0]
            digits = text[1:]
        if not digits.isdecimal():
            raise CrossSourceDifferenceQueueError(f"{field_name} must be integer cents")
        return int(f"{sign}{digits}")
    raise CrossSourceDifferenceQueueError(f"{field_name} has unsupported type: {type(value).__name__}")


def _normalize_source_ref(source_ref: dict[str, Any], expected_type: str, label: str) -> dict[str, Any]:
    if not isinstance(source_ref, dict):
        raise CrossSourceDifferenceQueueError(f"{label} must be an object")
    missing = [field for field in REQUIRED_SOURCE_REF_FIELDS if field not in source_ref]
    if missing:
        raise CrossSourceDifferenceQueueError(f"{label} missing fields: {','.join(missing)}")

    normalized = {
        "source_id": _require_text(source_ref["source_id"], f"{label}.source_id"),
        "source_type": _require_text(source_ref["source_type"], f"{label}.source_type").lower(),
        "source_class": _require_text(source_ref["source_class"], f"{label}.source_class"),
        "source_anchor_ref": _require_text(source_ref["source_anchor_ref"], f"{label}.source_anchor_ref"),
    }
    if normalized["source_type"] != expected_type:
        raise CrossSourceDifferenceQueueError(f"{label}.source_type must be {expected_type}")
    ranked = rank_source_candidate(
        {
            "source_id": normalized["source_id"],
            "source_class": normalized["source_class"],
        }
    )
    normalized["priority_rank"] = ranked["priority_rank"]
    normalized["priority_label"] = ranked["priority_label"]
    return normalized


def _queue_id(*, project_ref: str, field: str, pdf_source_id: str, excel_source_id: str, event_time: str) -> str:
    timestamp = parse_received_at(event_time)
    suffix = sha256_bytes("|".join([project_ref, field, pdf_source_id, excel_source_id]).encode("utf-8"))[:12]
    return f"CDQ-{timestamp.strftime('%Y%m%d-%H%M%S')}-{suffix}"


def build_pdf_excel_difference_queue_item(
    *,
    project_ref: str,
    field: str,
    pdf_source_ref: dict[str, Any],
    excel_source_ref: dict[str, Any],
    pdf_value_cents: Any,
    excel_value_cents: Any,
    event_time: str,
    evidence_ref: str,
) -> dict[str, Any]:
    """Build a public-safe S06-P2 queue item for one PDF/Excel project-field conflict."""

    project_ref_value = _require_text(project_ref, "project_ref")
    field_value = _require_text(field, "field")
    pdf_ref = _normalize_source_ref(pdf_source_ref, "pdf", "pdf_source_ref")
    excel_ref = _normalize_source_ref(excel_source_ref, "excel", "excel_source_ref")
    pdf_cents = _to_integer_cents(pdf_value_cents, "pdf_value_cents")
    excel_cents = _to_integer_cents(excel_value_cents, "excel_value_cents")
    difference_cents = pdf_cents - excel_cents
    if difference_cents == 0:
        raise CrossSourceDifferenceQueueError("S06-P2 queue item requires a non-zero cross-source difference")
    timestamp = parse_received_at(event_time)
    queue_id = _queue_id(
        project_ref=project_ref_value,
        field=field_value,
        pdf_source_id=pdf_ref["source_id"],
        excel_source_id=excel_ref["source_id"],
        event_time=timestamp.isoformat(),
    )

    return {
        "record_type": "cross_source_difference_queue_item",
        "schema_version": "kmfa.cross_source_difference_queue.v1",
        "stage_phase": "S06-P2",
        "queue_id": queue_id,
        "project_ref": project_ref_value,
        "field": field_value,
        "conflict_scope": f"{project_ref_value}.{field_value}",
        "source_refs": [pdf_ref, excel_ref],
        "pdf_value_cents": pdf_cents,
        "excel_value_cents": excel_cents,
        "difference_cents": difference_cents,
        "reason_code": "pdf-excel-same-project-cross-source-conflict",
        "status": "queued_for_manual_review",
        "resolution_policy": "manual_review_required",
        "auto_correction_allowed": False,
        "averaging_allowed": False,
        "rounding_mask_allowed": False,
        "auto_selection_allowed": False,
        "auto_selected_source_id": None,
        "resolved_value_cents": None,
        "report_grade_a_allowed": False,
        "target_layer": "metadata",
        "event_time": timestamp.isoformat(),
        "raw_layer_write_allowed": False,
        "raw_source_mutation_allowed": False,
        "raw_business_data_used": False,
        "public_safe_fixture_only": True,
        "evidence_ref": _require_text(evidence_ref, "evidence_ref"),
    }


def evaluate_report_grade_gate(queue_items: list[dict[str, Any]]) -> dict[str, Any]:
    blocking = [
        _require_text(item.get("queue_id"), "queue_id")
        for item in queue_items
        if item.get("status") not in CLOSED_QUEUE_STATUSES
    ]
    report_grade_a_allowed = not blocking
    return {
        "record_type": "cross_source_difference_report_grade_gate",
        "schema_version": "kmfa.cross_source_difference_report_grade_gate.v1",
        "stage_phase": "S06-P2",
        "status": "passed" if report_grade_a_allowed else "blocked",
        "report_grade_a_allowed": report_grade_a_allowed,
        "maximum_report_grade": "A" if report_grade_a_allowed else "B",
        "hard_block_reason": None if report_grade_a_allowed else "unresolved_critical_difference",
        "blocking_queue_ids": blocking,
        "raw_business_data_used": False,
        "public_safe_fixture_only": True,
    }


def validate_queue_item(item: dict[str, Any]) -> None:
    if item.get("record_type") != "cross_source_difference_queue_item":
        raise CrossSourceDifferenceQueueError("queue item record_type mismatch")
    if item.get("stage_phase") != "S06-P2":
        raise CrossSourceDifferenceQueueError("queue item stage_phase mismatch")
    if item.get("status") not in ALLOWED_QUEUE_STATUSES:
        raise CrossSourceDifferenceQueueError("queue item status is not allowed")
    if {ref.get("source_type") for ref in item.get("source_refs", [])} != {"pdf", "excel"}:
        raise CrossSourceDifferenceQueueError("queue item must contain exactly PDF and Excel source types")
    for flag in ("auto_correction_allowed", "averaging_allowed", "rounding_mask_allowed", "auto_selection_allowed"):
        if item.get(flag) is not False:
            raise CrossSourceDifferenceQueueError(f"{flag} must be false")
    if item.get("auto_selected_source_id") is not None:
        raise CrossSourceDifferenceQueueError("auto_selected_source_id must be null")
    if item.get("status") not in CLOSED_QUEUE_STATUSES and item.get("report_grade_a_allowed") is not False:
        raise CrossSourceDifferenceQueueError("unclosed queue item must block report grade A")
    if item.get("raw_layer_write_allowed") is not False or item.get("raw_source_mutation_allowed") is not False:
        raise CrossSourceDifferenceQueueError("queue item must not write or mutate raw layer")


def write_queue_jsonl(queue_items: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for item in queue_items:
            validate_queue_item(item)
            handle.write(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n")


def build_queue_from_fixture(path: Path) -> list[dict[str, Any]]:
    fixture = json.loads(path.read_text(encoding="utf-8"))
    return [
        build_pdf_excel_difference_queue_item(
            project_ref=fixture["project_ref"],
            field=fixture["field"],
            pdf_source_ref=fixture["pdf_source_ref"],
            excel_source_ref=fixture["excel_source_ref"],
            pdf_value_cents=fixture["pdf_value_cents"],
            excel_value_cents=fixture["excel_value_cents"],
            event_time=fixture["event_time"],
            evidence_ref=fixture["evidence_ref"],
        )
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a KMFA S06-P2 public-safe PDF/Excel difference queue item.")
    parser.add_argument("--fixture", required=True, type=Path)
    parser.add_argument("--queue-jsonl", required=True, type=Path)
    parser.add_argument("--gate-json", required=True, type=Path)
    args = parser.parse_args(argv)

    queue_items = build_queue_from_fixture(args.fixture)
    gate = evaluate_report_grade_gate(queue_items)
    write_queue_jsonl(queue_items, args.queue_jsonl)
    args.gate_json.parent.mkdir(parents=True, exist_ok=True)
    args.gate_json.write_text(json.dumps(gate, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"queue_items": len(queue_items), "status": queue_items[0]["status"], "report_grade_a_allowed": gate["report_grade_a_allowed"]}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
