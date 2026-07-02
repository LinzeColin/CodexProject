#!/usr/bin/env python3
"""Metadata-only Stage 022 data priority queue for IDS."""

from __future__ import annotations

import argparse
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ENTRANCE = "人类产品入口 + IDS 系统运营入口"
DEFAULT_OVERSIZED_FILE_THRESHOLD_BYTES = 512 * 1024 * 1024
PROCESSING_GUARD_ZEROES = {
    "actual_parse_jobs_started": 0,
    "actual_ocr_jobs_started": 0,
    "actual_embedding_jobs_started": 0,
    "actual_index_jobs_started": 0,
    "actual_import_jobs_started": 0,
    "actual_external_api_calls_started": 0,
    "actual_priority_queue_jobs_started": 0,
}
NO_PERSISTENCE_DELTAS = {
    "document_delta": 0,
    "chunk_delta": 0,
    "job_delta": 0,
    "index_delta": 0,
    "import_write_delta": 0,
    "manifest_write_delta": 0,
    "evidence_write_delta": 0,
    "audit_write_delta": 0,
    "report_write_delta": 0,
    "database_write_delta": 0,
    "priority_queue_write_delta": 0,
}
NO_SIDE_EFFECT_FLAGS = {
    "does_not_scan_recursively": True,
    "does_not_parse_body_text": True,
    "does_not_start_ocr": True,
    "does_not_create_embeddings": True,
    "does_not_build_index": True,
    "does_not_start_import": True,
    "does_not_write_manifest_files": True,
    "does_not_write_database": True,
    "does_not_create_documents_chunks_jobs": True,
    "does_not_read_raw_metadata": True,
    "does_not_call_external_apis": True,
    "does_not_write_priority_queue": True,
}

PRIORITY_BUCKET_ORDER = ["P0", "P1", "P2", "P3"]
CRITICAL_NAME_HINTS = {
    "critical",
    "drawing",
    "spec",
    "specification",
    "diagnostic",
    "repair",
    "work-order",
    "work_order",
    "plan",
    "accepted",
    "工程",
    "图纸",
    "规范",
    "诊断",
    "维修",
    "检修",
}
SUPPORTING_NAME_HINTS = {
    "meeting",
    "note",
    "photo",
    "scan",
    "support",
    "context",
    "reference-note",
    "会议",
    "照片",
    "扫描",
    "辅助",
}
ENGINEERING_EXTENSIONS = {
    ".md",
    ".txt",
    ".csv",
    ".json",
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _load_stage020_module() -> Any:
    path = Path(__file__).with_name("check_import_cost_estimator.py")
    spec = importlib.util.spec_from_file_location("stage020_import_cost_estimator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load Stage 020 cost helper from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _has_name_hint(record: dict[str, Any], hints: set[str]) -> bool:
    haystack = " ".join(
        str(record.get(key, "")).lower()
        for key in ("basename", "source_path", "source_uri")
    )
    return any(hint.lower() in haystack for hint in hints)


def _priority_for_record(record: dict[str, Any]) -> tuple[str, str, list[str]]:
    extension = str(record.get("extension") or "").lower()
    risk_tags = set(record.get("risk_tags", []))
    if risk_tags.intersection({"suspicious_archive", "unknown_format", "oversized"}):
        return (
            "P3_LOW_VALUE_OR_DEFERRED_DATA",
            "P3",
            ["PRIORITY_DEFERRED_RISK", "PRIORITY_OWNER_REVIEW_REQUIRED"],
        )
    if _has_name_hint(record, CRITICAL_NAME_HINTS) and extension in ENGINEERING_EXTENSIONS:
        return (
            "P0_CRITICAL_ENGINEERING_DATA",
            "P0",
            ["PRIORITY_CRITICAL_ENGINEERING", "PRIORITY_ACCEPTED_ENGINEERING_FORMAT"],
        )
    if _has_name_hint(record, SUPPORTING_NAME_HINTS) or "scanned_document" in risk_tags:
        return (
            "P2_SUPPORTING_ENGINEERING_DATA",
            "P2",
            ["PRIORITY_SUPPORTING_CONTEXT", "PRIORITY_OWNER_REVIEW_REQUIRED"],
        )
    if extension in ENGINEERING_EXTENSIONS:
        return (
            "P1_HIGH_VALUE_ENGINEERING_DATA",
            "P1",
            ["PRIORITY_HIGH_VALUE_ENGINEERING", "PRIORITY_ACCEPTED_ENGINEERING_FORMAT"],
        )
    return (
        "P3_LOW_VALUE_OR_DEFERRED_DATA",
        "P3",
        ["PRIORITY_LOW_CONFIDENCE", "PRIORITY_OWNER_REVIEW_REQUIRED"],
    )


def _empty_buckets() -> dict[str, dict[str, Any]]:
    return {
        "P0": {"priority_class": "P0_CRITICAL_ENGINEERING_DATA", "count": 0, "reason_codes": [], "files": []},
        "P1": {"priority_class": "P1_HIGH_VALUE_ENGINEERING_DATA", "count": 0, "reason_codes": [], "files": []},
        "P2": {"priority_class": "P2_SUPPORTING_ENGINEERING_DATA", "count": 0, "reason_codes": [], "files": []},
        "P3": {"priority_class": "P3_LOW_VALUE_OR_DEFERRED_DATA", "count": 0, "reason_codes": [], "files": []},
    }


def _bucket_records(records: list[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    buckets = _empty_buckets()
    queued_records: list[dict[str, Any]] = []
    for record in sorted(records, key=lambda item: str(item.get("source_uri"))):
        priority_class, bucket_id, reason_codes = _priority_for_record(record)
        queued = {
            "source_uri": record.get("source_uri"),
            "source_path": record.get("source_path"),
            "basename": record.get("basename"),
            "extension": record.get("extension"),
            "file_size": record.get("file_size", 0),
            "risk_tags": list(record.get("risk_tags", [])),
            "priority_bucket": bucket_id,
            "priority_class": priority_class,
            "priority_reason_codes": reason_codes,
        }
        buckets[bucket_id]["files"].append(queued)
        buckets[bucket_id]["count"] += 1
        buckets[bucket_id]["reason_codes"] = list(
            dict.fromkeys([*buckets[bucket_id]["reason_codes"], *reason_codes])
        )
        queued_records.append(queued)
    return buckets, queued_records


def _state_from_cost_report(cost_report: dict[str, Any], buckets: dict[str, dict[str, Any]]) -> str:
    if cost_report.get("overall_state") == "COST_BLOCKED" or cost_report.get("cost_score_band") == "blocked":
        return "PRIORITY_QUEUE_BLOCKED"
    if cost_report.get("risk_items") or buckets["P3"]["count"] > 0:
        return "PRIORITY_QUEUE_OWNER_REVIEW_REQUIRED"
    return "PRIORITY_QUEUE_READY"


def _priority_hint(state: str, buckets: dict[str, dict[str, Any]]) -> str:
    if state == "PRIORITY_QUEUE_BLOCKED":
        return "blocked"
    if state == "PRIORITY_QUEUE_OWNER_REVIEW_REQUIRED":
        if buckets["P0"]["count"] > 0:
            return "process_p0_first_with_owner_review"
        return "owner_review_required"
    if buckets["P0"]["count"] > 0:
        return "process_p0_first"
    if buckets["P1"]["count"] > 0:
        return "process_p1_first"
    return "review_priority_queue"


def _priority_queue_summary(report: dict[str, Any]) -> dict[str, Any]:
    buckets = report["priority_buckets"]
    return {
        "queue_state": report["overall_state"],
        "priority_hint": report["priority_hint"],
        "total_files": report["file_count_estimate"],
        "p0_count": buckets["P0"]["count"],
        "p1_count": buckets["P1"]["count"],
        "p2_count": buckets["P2"]["count"],
        "p3_count": buckets["P3"]["count"],
        "owner_review_required": report["confirmation_status"] != "PRIORITY_QUEUE_READY",
        "next_processing_policy": "owner 确认后才进入批量处理",
    }


def _human_product_entrance_payload(report: dict[str, Any]) -> dict[str, Any]:
    summary = report["priority_queue_summary"]
    return {
        "title": "数据优先级队列",
        "customer_visible": True,
        "confirmation_required": report["confirmation_status"] != "PRIORITY_QUEUE_READY",
        "summary_cards": [
            {"label": "文件数量", "value": report["file_count_estimate"]},
            {"label": "P0 关键工程资料", "value": summary["p0_count"]},
            {"label": "P1 高价值工程资料", "value": summary["p1_count"]},
            {"label": "P2 辅助资料", "value": summary["p2_count"]},
            {"label": "P3 延后或低置信资料", "value": summary["p3_count"]},
            {"label": "压缩包候选", "value": report["archive_candidate_count"]},
            {"label": "扫描件候选", "value": report["scanned_document_candidate_count"]},
            {"label": "预计 OCR 页数", "value": report["ocr_page_estimate"]["high"]},
            {"label": "预计 Embedding token", "value": report["embedding_token_estimate"]["high"]},
            {"label": "预计索引体积", "value": report["index_size_estimate"]["high_bytes"]},
            {"label": "确认状态", "value": report["confirmation_status"]},
        ],
        "owner_actions": [
            "review_priority_queue",
            "approve_priority_queue",
            "pause_without_side_effects",
            "split_batch",
            "defer_p3_items",
            "cancel_without_side_effects",
        ],
        "priority_bucket_order": list(PRIORITY_BUCKET_ORDER),
        "message": "这是导入前的数据优先级队列；确认前不会启动解析、OCR、Embedding、索引或实际导入。",
    }


def _ids_operations_payload(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": "IDS 数据优先级队列状态",
        "state": report["overall_state"],
        "confirmation_status": report["confirmation_status"],
        "priority_hint": report["priority_hint"],
        "source_cost_state": report["source_cost_state"],
        "source_cost_score_band": report["source_cost_score_band"],
        "priority_bucket_order": list(PRIORITY_BUCKET_ORDER),
        "processing_guard": dict(PROCESSING_GUARD_ZEROES),
        "no_persistence_deltas": dict(NO_PERSISTENCE_DELTAS),
    }


def _ui_component_contract() -> dict[str, Any]:
    return {
        "component_name": "DataPriorityQueuePanel",
        "props_contract": {
            "summary_cards": "array<{label: string, value: string|number|boolean}>",
            "priority_buckets": "Record<'P0'|'P1'|'P2'|'P3', {count: number, files: array}>",
            "risk_items": "string[]",
            "cost_items": "object",
            "owner_actions": "string[]",
            "message": "string",
        },
        "display_entrance": ENTRANCE,
        "requires_owner_confirmation_before_processing": True,
    }


def evaluate_data_priority_queue(
    *,
    source_uris: list[str | None] | tuple[str | None, ...] | None,
    queued_at: str | None = None,
    drive_state: str = "online",
    available_space_bytes: int | None = None,
    oversized_file_threshold_bytes: int = DEFAULT_OVERSIZED_FILE_THRESHOLD_BYTES,
) -> dict[str, Any]:
    """Build a metadata-only P0/P1/P2/P3 queue from Stage 020 cost estimates."""

    queued_at = queued_at or _utc_now()
    cost_report = _load_stage020_module().evaluate_import_cost_estimate(
        source_uris=source_uris,
        estimated_at=queued_at,
        drive_state=drive_state,
        available_space_bytes=available_space_bytes,
        oversized_file_threshold_bytes=oversized_file_threshold_bytes,
    )
    records = list(cost_report.get("candidate_files", []))
    buckets, queued_records = _bucket_records(records)
    state = _state_from_cost_report(cost_report, buckets)
    report: dict[str, Any] = {
        "schema_version": "ids.stage022.data_priority_queue.v1",
        "stage": "STAGE-022",
        "phase": "Phase 2",
        "acceptance_id": "ACC-STAGE-022",
        "entrance": ENTRANCE,
        "customer_visible": True,
        "source_preflight_schema": cost_report.get("source_preflight_schema"),
        "source_risk_schema": cost_report.get("source_risk_schema"),
        "source_cost_schema": cost_report.get("schema_version"),
        "source_cost_state": cost_report.get("overall_state"),
        "source_cost_score_band": cost_report.get("cost_score_band"),
        "queued_at": queued_at,
        "priority_queue_mode": "dry_run_metadata_only",
        "overall_state": state,
        "confirmation_status": state,
        "confirmation_required": state != "PRIORITY_QUEUE_READY",
        "priority_hint": _priority_hint(state, buckets),
        "priority_bucket_order": list(PRIORITY_BUCKET_ORDER),
        "file_count_estimate": cost_report.get("file_count_estimate", 0),
        "total_size_bytes_estimate": cost_report.get("total_size_bytes_estimate", 0),
        "format_counts": cost_report.get("format_counts", {}),
        "archive_candidate_count": cost_report.get("archive_candidate_count", 0),
        "scanned_document_candidate_count": cost_report.get("scanned_document_candidate_count", 0),
        "unknown_format_count": cost_report.get("unknown_format_count", 0),
        "oversized_file_count": cost_report.get("oversized_file_count", 0),
        "high_risk_file_count": cost_report.get("high_risk_file_count", 0),
        "embedding_token_estimate": cost_report.get("embedding_token_estimate", {}),
        "external_api_cost_estimate": cost_report.get("external_api_cost_estimate", {}),
        "ocr_page_estimate": cost_report.get("ocr_page_estimate", {}),
        "index_size_estimate": cost_report.get("index_size_estimate", {}),
        "local_space_pressure": cost_report.get("local_space_pressure"),
        "risk_items": list(cost_report.get("risk_items", [])),
        "cost_items": dict(cost_report.get("cost_items", {})),
        "priority_buckets": buckets,
        "queued_files": queued_records,
        "queued_file_count": len(queued_records),
        "rejected_inputs": cost_report.get("rejected_inputs", []),
        "rejected_input_count": cost_report.get("rejected_input_count", 0),
        "uncertainty_items": [
            "Priority queue uses filename, extension, risk, and cost metadata only; it does not parse body text.",
            "P0/P1/P2/P3 priority is advisory until owner confirmation.",
            "OCR, Embedding, external API, and index values are inherited estimates from Stage 020 and are not executed here.",
        ],
        "no_persistence_deltas": dict(NO_PERSISTENCE_DELTAS),
        "processing_guard": dict(PROCESSING_GUARD_ZEROES),
        "ui_component_contract": _ui_component_contract(),
    }
    report["priority_queue_summary"] = _priority_queue_summary(report)
    report["human_product_entrance_payload"] = _human_product_entrance_payload(report)
    report["ids_operations_entrance_payload"] = _ids_operations_payload(report)
    report.update(NO_SIDE_EFFECT_FLAGS)
    return report


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a metadata-only Stage 022 data priority queue.")
    parser.add_argument(
        "--source-uri",
        action="append",
        dest="source_uris",
        help="Explicit file:// source root or file URI. Repeat for multiple approved roots.",
    )
    parser.add_argument("--queued-at", default=None, help="Optional UTC timestamp for deterministic evidence.")
    parser.add_argument("--drive-state", default="online", help="Source drive state: online, offline, disconnected.")
    parser.add_argument("--available-space-bytes", type=int, default=None, help="Optional local free-space estimate.")
    parser.add_argument(
        "--oversized-file-threshold-bytes",
        type=int,
        default=DEFAULT_OVERSIZED_FILE_THRESHOLD_BYTES,
        help="Metadata-only threshold for oversized file classification.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    report = evaluate_data_priority_queue(
        source_uris=args.source_uris,
        queued_at=args.queued_at,
        drive_state=args.drive_state,
        available_space_bytes=args.available_space_bytes,
        oversized_file_threshold_bytes=args.oversized_file_threshold_bytes,
    )
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
