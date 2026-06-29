#!/usr/bin/env python3
"""Build KMFA S03-P3 source priority metadata records.

The tool defines priority rules and conflict events only. It does not parse
business values, write raw data, or auto-resolve cross-source conflicts.
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


SOURCE_PRIORITY_ORDER = (
    "raw_upload",
    "authorized_export",
    "raw_extracted_value",
    "staging_structured_row",
    "canonical_fact",
    "derived_metric",
    "report_reference",
    "frontend_display",
    "processed_data",
)
SOURCE_PRIORITY_RANK = {
    "raw_upload": 10,
    "authorized_export": 20,
    "raw_extracted_value": 30,
    "staging_structured_row": 40,
    "canonical_fact": 50,
    "derived_metric": 60,
    "report_reference": 70,
    "frontend_display": 80,
    "processed_data": 90,
}
SOURCE_PRIORITY_LABELS = {
    "raw_upload": "original uploaded data",
    "authorized_export": "authorized source-system export",
    "raw_extracted_value": "raw extracted value from authorized source",
    "staging_structured_row": "staging structured row",
    "canonical_fact": "canonical fact",
    "derived_metric": "derived metric",
    "report_reference": "report reference",
    "frontend_display": "frontend display value",
    "processed_data": "generic processed data alias",
}


def require_text(value: str, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field_name} is required")
    return text


def validate_source_class(source_class: str) -> str:
    source_class_value = require_text(source_class, "source_class")
    if source_class_value not in SOURCE_PRIORITY_RANK:
        raise ValueError(
            f"invalid source_class: {source_class_value!r}; allowed={';'.join(SOURCE_PRIORITY_ORDER)}"
        )
    return source_class_value


def rank_source_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    source_id = require_text(str(candidate.get("source_id", "")), "source_id")
    source_class = validate_source_class(str(candidate.get("source_class", "")))
    ranked = dict(candidate)
    ranked.update(
        {
            "source_id": source_id,
            "source_class": source_class,
            "priority_rank": SOURCE_PRIORITY_RANK[source_class],
            "priority_label": SOURCE_PRIORITY_LABELS[source_class],
        }
    )
    return ranked


def sort_source_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ranked = [rank_source_candidate(candidate) for candidate in candidates]
    return sorted(ranked, key=lambda item: (item["priority_rank"], item["source_id"]))


def build_event_id(prefix: str, event_time: str, parts: list[str]) -> str:
    timestamp = parse_received_at(event_time)
    suffix = sha256_bytes("|".join(parts).encode("utf-8"))[:12]
    return f"{prefix}-{timestamp.strftime('%Y%m%d-%H%M%S')}-{suffix}"


def build_same_source_inconsistency_event(
    *,
    source_id: str,
    primary_ref: str,
    conflicting_ref: str,
    field_path: str,
    reason_code: str,
    event_time: str,
    evidence_ref: str,
) -> dict[str, Any]:
    source_id_value = require_text(source_id, "source_id")
    primary_ref_value = require_text(primary_ref, "primary_ref")
    conflicting_ref_value = require_text(conflicting_ref, "conflicting_ref")
    field_path_value = require_text(field_path, "field_path")
    reason_code_value = slugify(require_text(reason_code, "reason_code"))
    timestamp = parse_received_at(event_time)
    event_id = build_event_id(
        "SPE",
        timestamp.isoformat(),
        [source_id_value, primary_ref_value, conflicting_ref_value, field_path_value, reason_code_value],
    )
    return {
        "record_type": "source_priority_event",
        "schema_version": "kmfa.source_priority_event.v1",
        "stage_phase": "S03-P3",
        "event_id": event_id,
        "event_type": "same_source_inconsistency",
        "source_id": source_id_value,
        "primary_ref": primary_ref_value,
        "conflicting_ref": conflicting_ref_value,
        "field_path": field_path_value,
        "reason_code": reason_code_value,
        "actions": ["invalidate_derived_cache", "request_rerun"],
        "target_layer": "metadata",
        "event_time": timestamp.isoformat(),
        "raw_layer_write_allowed": False,
        "raw_source_mutation_allowed": False,
        "cache_reuse_allowed": False,
        "evidence_ref": require_text(evidence_ref, "evidence_ref"),
    }


def build_cross_source_difference_queue_item(
    *,
    conflict_scope: str,
    source_refs: list[dict[str, Any]],
    reason_code: str,
    event_time: str,
    evidence_ref: str,
) -> dict[str, Any]:
    if len(source_refs) < 2:
        raise ValueError("cross-source conflict requires at least two source_refs")
    ranked_refs = sort_source_candidates(source_refs)
    source_ids = {ref["source_id"] for ref in ranked_refs}
    if len(source_ids) < 2:
        raise ValueError("cross-source conflict requires at least two distinct source_id values")

    conflict_scope_value = require_text(conflict_scope, "conflict_scope")
    reason_code_value = slugify(require_text(reason_code, "reason_code"))
    timestamp = parse_received_at(event_time)
    queue_id = build_event_id(
        "SDQ",
        timestamp.isoformat(),
        [conflict_scope_value, reason_code_value, *[ref["source_id"] for ref in ranked_refs]],
    )
    return {
        "record_type": "source_difference_queue_item",
        "schema_version": "kmfa.source_difference_queue.v1",
        "stage_phase": "S03-P3",
        "queue_id": queue_id,
        "conflict_scope": conflict_scope_value,
        "source_refs": ranked_refs,
        "reason_code": reason_code_value,
        "status": "queued_for_manual_review",
        "resolution_policy": "manual_review_required",
        "auto_selection_allowed": False,
        "auto_selected_source_id": None,
        "target_layer": "metadata",
        "event_time": timestamp.isoformat(),
        "raw_layer_write_allowed": False,
        "raw_source_mutation_allowed": False,
        "evidence_ref": require_text(evidence_ref, "evidence_ref"),
    }


def append_metadata_record(path: str | Path, record: dict[str, Any]) -> None:
    if record.get("target_layer") != "metadata":
        raise ValueError("S03-P3 records must target metadata")
    if record.get("raw_layer_write_allowed") is not False:
        raise ValueError("S03-P3 records must not write raw layer")
    if record.get("raw_source_mutation_allowed") is not False:
        raise ValueError("S03-P3 records must not mutate raw sources")
    if record.get("auto_selection_allowed") is True:
        raise ValueError("S03-P3 records must not auto-select cross-source conflicts")
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def parse_source_ref(value: str) -> dict[str, str]:
    source_id, separator, source_class = value.partition(":")
    if not separator:
        raise ValueError("--source-ref must use source_id:source_class")
    return {"source_id": require_text(source_id, "source_ref.source_id"), "source_class": validate_source_class(source_class)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build KMFA S03-P3 source priority metadata.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    same_source = subparsers.add_parser("same-source-event")
    same_source.add_argument("--source-id", required=True)
    same_source.add_argument("--primary-ref", required=True)
    same_source.add_argument("--conflicting-ref", required=True)
    same_source.add_argument("--field-path", required=True)
    same_source.add_argument("--reason-code", required=True)
    same_source.add_argument("--event-time", required=True)
    same_source.add_argument("--evidence-ref", required=True)

    cross_source = subparsers.add_parser("cross-source-queue")
    cross_source.add_argument("--conflict-scope", required=True)
    cross_source.add_argument("--source-ref", action="append", required=True)
    cross_source.add_argument("--reason-code", required=True)
    cross_source.add_argument("--event-time", required=True)
    cross_source.add_argument("--evidence-ref", required=True)

    args = parser.parse_args(argv)
    if args.command == "same-source-event":
        record = build_same_source_inconsistency_event(
            source_id=args.source_id,
            primary_ref=args.primary_ref,
            conflicting_ref=args.conflicting_ref,
            field_path=args.field_path,
            reason_code=args.reason_code,
            event_time=args.event_time,
            evidence_ref=args.evidence_ref,
        )
    else:
        record = build_cross_source_difference_queue_item(
            conflict_scope=args.conflict_scope,
            source_refs=[parse_source_ref(value) for value in args.source_ref],
            reason_code=args.reason_code,
            event_time=args.event_time,
            evidence_ref=args.evidence_ref,
        )
    print(json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
