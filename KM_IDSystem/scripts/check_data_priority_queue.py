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
REQUIRED_PHASE3_SCENARIOS = {
    "empty_directory",
    "small_directory",
    "large_directory",
    "offline_drive",
    "archive_present",
    "insufficient_space",
}
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


def _is_high_risk_queue_candidate(record: dict[str, Any]) -> bool:
    high_risk_tags = {"suspicious_archive", "scanned_document", "unknown_format", "oversized"}
    return (
        record.get("priority_bucket") == "P3"
        or bool(high_risk_tags.intersection(set(record.get("risk_tags", []))))
        or "PRIORITY_OWNER_REVIEW_REQUIRED" in set(record.get("priority_reason_codes", []))
    )


def _chunk_records(records: list[dict[str, Any]], batch_size: int) -> list[list[dict[str, Any]]]:
    if not records:
        return []
    size = max(1, batch_size)
    return [records[index : index + size] for index in range(0, len(records), size)]


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


def build_priority_queue_owner_decision_plan(
    priority_queue_report: dict[str, Any], *, batch_size: int = 50
) -> dict[str, Any]:
    """Build a no-persistence owner decision plan for a priority queue report."""

    queued_files = list(priority_queue_report.get("queued_files", []))
    high_risk_files = [record for record in queued_files if _is_high_risk_queue_candidate(record)]
    kept_files = [record for record in queued_files if not _is_high_risk_queue_candidate(record)]
    batches = _chunk_records(queued_files, batch_size)
    serialized = json.dumps(priority_queue_report, ensure_ascii=False, sort_keys=True)
    no_persistence = dict(NO_PERSISTENCE_DELTAS)
    return {
        "schema_version": "ids.stage022.data_priority_queue.owner_decision.v1",
        "stage": "STAGE-022",
        "phase": "Phase 3",
        "acceptance_id": "ACC-STAGE-022",
        "entrance": ENTRANCE,
        "source_confirmation_status": priority_queue_report.get("confirmation_status"),
        "supported_owner_actions": [
            "save_for_owner_review",
            "pause_without_side_effects",
            "cancel_without_side_effects",
            "split_into_batches",
            "skip_high_risk_files",
        ],
        "save_contract": {
            "state": "PRIORITY_QUEUE_RESULT_SERIALIZABLE",
            "can_save_result": True,
            "persisted_by_helper": False,
            "serialized_bytes": len(serialized.encode("utf-8")),
            "owner_selected_path_required": True,
        },
        "pause_contract": {"state": "PRIORITY_QUEUE_PAUSE_READY", **no_persistence},
        "cancel_contract": {"state": "PRIORITY_QUEUE_CANCEL_READY", **no_persistence},
        "batch_plan": {
            "can_split": len(batches) > 1,
            "batch_size": max(1, batch_size),
            "batch_count": len(batches),
            "batches": [
                {
                    "batch_index": index + 1,
                    "file_count": len(batch),
                    "total_size_bytes": sum(int(record.get("file_size", 0)) for record in batch),
                    "priority_counts": {
                        bucket: sum(1 for record in batch if record.get("priority_bucket") == bucket)
                        for bucket in PRIORITY_BUCKET_ORDER
                    },
                    "files": batch,
                }
                for index, batch in enumerate(batches)
            ],
        },
        "skip_high_risk_plan": {
            "can_skip_high_risk_files": True,
            "high_risk_file_count": len(high_risk_files),
            "kept_file_count": len(kept_files),
            "skipped_files": high_risk_files,
            "kept_files": kept_files,
        },
        "no_persistence_deltas": no_persistence,
        "processing_guard": dict(PROCESSING_GUARD_ZEROES),
    }


def build_stage022_scenario_report(
    *,
    scenario_sources: dict[str, dict[str, Any]],
    queued_at: str | None = None,
    batch_size: int = 50,
    oversized_file_threshold_bytes: int = DEFAULT_OVERSIZED_FILE_THRESHOLD_BYTES,
) -> dict[str, Any]:
    """Validate data priority queue scenarios using metadata-only inputs."""

    queued_at = queued_at or _utc_now()
    scenario_results: dict[str, dict[str, Any]] = {}
    for scenario_id in sorted(scenario_sources):
        scenario = scenario_sources[scenario_id]
        data_priority_queue = evaluate_data_priority_queue(
            source_uris=scenario.get("source_uris"),
            queued_at=queued_at,
            drive_state=scenario.get("drive_state", "online"),
            available_space_bytes=scenario.get("available_space_bytes"),
            oversized_file_threshold_bytes=scenario.get(
                "oversized_file_threshold_bytes", oversized_file_threshold_bytes
            ),
        )
        scenario_results[scenario_id] = {
            "scenario_id": scenario_id,
            "data_priority_queue": data_priority_queue,
            "owner_decision_plan": build_priority_queue_owner_decision_plan(
                data_priority_queue, batch_size=batch_size
            ),
        }

    required_scenarios_covered = REQUIRED_PHASE3_SCENARIOS.issubset(set(scenario_results))
    report: dict[str, Any] = {
        "schema_version": "ids.stage022.data_priority_queue.scenario_validation.v1",
        "stage": "STAGE-022",
        "phase": "Phase 3",
        "acceptance_id": "ACC-STAGE-022",
        "entrance": ENTRANCE,
        "customer_visible": True,
        "validation_state": (
            "SCENARIO_VALIDATION_PASSED" if required_scenarios_covered else "SCENARIO_VALIDATION_PARTIAL"
        ),
        "queued_at": queued_at,
        "scenario_count": len(scenario_results),
        "required_scenarios": sorted(REQUIRED_PHASE3_SCENARIOS),
        "required_scenarios_covered": required_scenarios_covered,
        "scenario_results": scenario_results,
        "processing_guard": dict(PROCESSING_GUARD_ZEROES),
        "no_persistence_deltas": dict(NO_PERSISTENCE_DELTAS),
    }
    report.update(NO_SIDE_EFFECT_FLAGS)
    return report


def _priority_queue_report_sample(priority_queue_report: dict[str, Any]) -> dict[str, Any]:
    sample_keys = [
        "schema_version",
        "overall_state",
        "confirmation_status",
        "file_count_estimate",
        "total_size_bytes_estimate",
        "format_counts",
        "archive_candidate_count",
        "scanned_document_candidate_count",
        "unknown_format_count",
        "oversized_file_count",
        "high_risk_file_count",
        "priority_bucket_order",
        "priority_buckets",
        "priority_queue_summary",
        "embedding_token_estimate",
        "external_api_cost_estimate",
        "ocr_page_estimate",
        "index_size_estimate",
        "local_space_pressure",
        "risk_items",
        "cost_items",
        "priority_hint",
        "human_product_entrance_payload",
        "ui_component_contract",
    ]
    return {key: priority_queue_report.get(key) for key in sample_keys}


def build_data_priority_queue_owner_feedback_summary(
    priority_queue_report: dict[str, Any],
    *,
    recorded_at: str | None = None,
    stage_review_findings: list[str] | tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """Build Phase 4 closeout evidence without creating runtime artifacts."""

    recorded_at = recorded_at or _utc_now()
    feedback: dict[str, Any] = {
        "schema_version": "ids.stage022.data_priority_queue.owner_feedback.v1",
        "stage": "STAGE-022",
        "phase": "Phase 4",
        "task_id": "IDS-V0_1-STAGE022-P4",
        "acceptance_id": "ACC-STAGE-022",
        "entrance": ENTRANCE,
        "recorded_at": recorded_at,
        "report_sample": _priority_queue_report_sample(priority_queue_report),
        "risk_checklist": {
            "COST_SOURCE_NOT_CONFIGURED": "未配置导入来源；请先选择 owner 批准的本地 file:// 输入。",
            "COST_SOURCE_BLOCKED": "来源不可用或越过安全边界；系统不会继续读取或推断该来源。",
            "COST_DRIVE_OFFLINE": "移动硬盘或来源盘处于离线状态；请重新接入后再做优先级队列预检。",
            "COST_ARCHIVE_REVIEW_REQUIRED": "发现压缩包候选；需要 owner 复核后再决定是否单独处理。",
            "COST_HIGH_RISK_FILE_PRESENT": "发现高风险文件；建议先跳过或拆分批次再复核。",
            "COST_LARGE_BATCH_PRESENT": "文件数量较多；建议分批处理并保留人工确认点。",
            "COST_OVERSIZED_FILE_PRESENT": "发现超大文件；建议拆分批次或先跳过后复核。",
            "COST_UNKNOWN_FORMAT_PRESENT": "发现未知格式；建议跳过或转交人工处理。",
            "COST_INSUFFICIENT_SPACE": "目标空间不足；请释放空间或缩小批次后再继续。",
            "COST_LOCAL_SPACE_BLOCKED": "本机空间估算不足；确认前不会启动导入或索引。",
            "COST_LOCAL_SPACE_PRESSURE_HIGH": "本机空间压力较高；建议降低批次规模后再继续。",
        },
        "priority_feedback": {
            "P0_CRITICAL_ENGINEERING_DATA": "优先展示关键工程资料，owner 仍需确认后才允许后续批量处理。",
            "P1_HIGH_VALUE_ENGINEERING_DATA": "高价值工程资料可作为第二批候选，保留人工复核点。",
            "P2_SUPPORTING_ENGINEERING_DATA": "辅助资料用于补充上下文，不得抢占 P0/P1 处理顺序。",
            "P3_LOW_VALUE_OR_DEFERRED_DATA": "低置信、高风险、压缩包、未知格式或超大文件默认延后或跳过候选。",
        },
        "user_confirmation_flow_log": [
            "系统展示优先级队列报告样例，owner 先查看文件数量、格式、大小、P0/P1/P2/P3 分布、压缩包、扫描件、OCR/Embedding 估算、风险、成本和优先级。",
            "owner 可以优先确认 P0 关键工程资料；后续 Stage 仍必须保留独立授权，本 Stage 不启动实际导入。",
            "owner 可以选择保存优先级队列结果；当前 helper 只提供可序列化内容，不自动落盘。",
            "owner 可以选择取消；取消后 document/chunk/job/index/import/manifest/database/priority_queue 写入均保持 0。",
            "owner 可以选择分批；系统只生成 metadata batch plan，不启动解析、OCR、Embedding、索引、外部 API 或导入。",
            "owner 可以选择跳过高风险文件；P3、压缩包、扫描件、未知格式、超大文件和可疑候选会进入跳过候选清单。",
            "owner 明确确认后，后续 Stage 才能进入批量处理；本 Stage 不授权实际导入。",
        ],
        "estimation_uncertainty": [
            "P0/P1/P2/P3 使用文件名、扩展名、风险标签和成本元信息生成，不解析正文，也不代表最终业务价值判断。",
            "Embedding token 估算使用文件大小元信息代理，不解析正文，也不代表真实 tokenizer 结果。",
            "OCR 页数估算使用扫描件候选数量和大小代理，不启动 OCR，也不确认图片质量。",
            "外部 API 成本估算使用配置单价和元信息工作量代理，不调用任何外部 API。",
            "索引体积估算使用 token 代理乘以配置系数，不建立索引。",
            "本机空间压力只比较估算输入体积、索引体积和传入 available_space_bytes，不替代系统级容量审计。",
            "目录处理保持 immediate-child metadata-only，不代表递归扫描或真实生产 corpus 覆盖率。",
        ],
        "failure_explanations": {
            "PRIORITY_QUEUE_BLOCKED": "优先级队列被阻断；来源不可用、越过边界、空间不足或设备离线时，系统不会继续处理。",
            "PRIORITY_QUEUE_OWNER_REVIEW_REQUIRED": "优先级队列需要 owner 复核；请先查看 P0/P1/P2/P3、风险、成本、分批和跳过建议，再决定是否继续。",
            "PRIORITY_QUEUE_READY": "未发现必须阻断项；继续前仍需遵守后续 Stage 的独立授权和审计要求。",
            "COST_SOURCE_BLOCKED": "来源不可用或越过安全边界；系统不会继续读取或推断该来源。",
            "COST_LOCAL_SPACE_BLOCKED": "本机空间估算不足；请释放空间、缩小批次或更换目标盘后再继续。",
        },
        "rollback_steps": [
            "Revert Stage022 Phase4 helper additions, focused tests, closeout evidence, Stage005 validator/test changes, BATCH021_030 lock, roadmap/event updates, and rendered owner-file changes.",
            "Do not move, delete, overwrite, rewrite, compact, clean, normalize, repair, or deduplicate original files in place.",
            "Do not clean /Users/linzezhang/Downloads/IDS_MetaData, runtime databases, reports, outputs, persisted manifests, evidence ledgers, audit logs, indexes, app entries, or GitHub state.",
            "After rollback, STAGE-022 should return to Phase 3 complete and Phase 4 pending.",
        ],
        "whole_stage_review": {
            "result": "passed_with_local_evidence",
            "completed_phases": ["Phase 1", "Phase 2", "Phase 3", "Phase 4"],
            "reviewed_acceptance_id": "ACC-STAGE-022",
            "findings": list(stage_review_findings or []),
            "unresolved_findings": [],
            "next_stage": "STAGE-023",
            "batch_upload_allowed": False,
            "next_batch_gate": "IDS-STAGE023-P1-GATE",
            "github_upload_status": "not_started",
            "app_reinstall_status": "not_started",
        },
        "processing_guard": dict(PROCESSING_GUARD_ZEROES),
        "no_persistence_deltas": dict(NO_PERSISTENCE_DELTAS),
        "does_not_create_screenshots": True,
        "does_not_write_report_files": True,
        "does_not_write_json_output_files": True,
        "does_not_start_services": True,
        "does_not_install_dependencies": True,
        "does_not_push_to_github": True,
        "does_not_open_or_merge_pr": True,
        "does_not_reinstall_app_entries": True,
        "does_not_enter_stage023": True,
    }
    feedback.update(NO_SIDE_EFFECT_FLAGS)
    return feedback


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
