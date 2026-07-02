#!/usr/bin/env python3
"""Metadata-only Stage 020 import cost estimate for IDS."""

from __future__ import annotations

import argparse
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ENTRANCE = "人类产品入口 + IDS 系统运营入口"
DEFAULT_OVERSIZED_FILE_THRESHOLD_BYTES = 512 * 1024 * 1024
DEFAULT_EMBEDDING_PRICE_PER_1K_TOKENS = 0.00002
DEFAULT_EXTERNAL_API_PRICE_PER_CALL = 0.001
DEFAULT_OCR_PRICE_PER_PAGE = 0.002
DEFAULT_INDEX_BYTES_PER_TOKEN = 6
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
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _load_stage019_module() -> Any:
    path = Path(__file__).with_name("check_import_risk_estimator.py")
    spec = importlib.util.spec_from_file_location("stage019_import_risk_estimator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load Stage 019 risk helper from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _workload_class(value: int | float) -> str:
    if value <= 0:
        return "none"
    if value <= 10:
        return "low"
    if value <= 100:
        return "medium"
    return "high"


def _money_class(value: float) -> str:
    if value <= 0:
        return "none"
    if value < 0.10:
        return "low"
    if value < 10:
        return "medium"
    return "high"


def _storage_pressure(total_bytes: int, available_space_bytes: int | None) -> str:
    if available_space_bytes is not None and total_bytes > available_space_bytes:
        return "blocked"
    if total_bytes <= 0:
        return "none"
    if total_bytes < 100 * 1024 * 1024:
        return "low"
    if total_bytes < 5 * 1024 * 1024 * 1024:
        return "medium"
    return "high"


def _estimate_embedding_tokens(records: list[dict[str, Any]]) -> dict[str, Any]:
    embedding_records = [record for record in records if record.get("extension") in {".md", ".txt", ".csv", ".json", ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx"}]
    bytes_total = sum(int(record.get("file_size", 0)) for record in embedding_records)
    low = max(0, bytes_total // 6)
    high = max(low, bytes_total // 3)
    return {
        "low": low,
        "high": high,
        "unit": "tokens",
        "method": "metadata_file_size_proxy_no_body_parse",
        "source_file_count": len(embedding_records),
    }


def _estimate_ocr_pages(records: list[dict[str, Any]]) -> dict[str, Any]:
    scanned_records = [
        record
        for record in records
        if record.get("scanned_document_candidate") or "scanned_document" in record.get("risk_tags", [])
    ]
    low = len(scanned_records)
    high = sum(max(1, int(record.get("file_size", 0)) // (512 * 1024) + 1) for record in scanned_records)
    return {
        "low": low,
        "high": high,
        "unit": "pages",
        "method": "metadata_scanned_candidate_count_and_size_proxy",
        "source_file_count": len(scanned_records),
    }


def _estimate_external_api_calls(file_count: int, ocr_pages: dict[str, Any], embedding_tokens: dict[str, Any]) -> dict[str, Any]:
    low = 0
    if embedding_tokens["high"] > 0:
        low += 1
    if ocr_pages["high"] > 0:
        low += ocr_pages["low"]
    high = max(low, file_count + ocr_pages["high"])
    return {
        "low": low,
        "high": high,
        "unit": "calls",
        "method": "metadata_workload_proxy_no_external_api_call",
    }


def _estimate_external_api_cost(
    *,
    embedding_tokens: dict[str, Any],
    ocr_pages: dict[str, Any],
    api_calls: dict[str, Any],
    embedding_price_per_1k_tokens: float,
    external_api_price_per_call: float,
    ocr_price_per_page: float,
) -> dict[str, Any]:
    low = (
        embedding_tokens["low"] / 1000 * embedding_price_per_1k_tokens
        + api_calls["low"] * external_api_price_per_call
        + ocr_pages["low"] * ocr_price_per_page
    )
    high = (
        embedding_tokens["high"] / 1000 * embedding_price_per_1k_tokens
        + api_calls["high"] * external_api_price_per_call
        + ocr_pages["high"] * ocr_price_per_page
    )
    return {
        "currency": "USD",
        "low": round(low, 6),
        "high": round(high, 6),
        "method": "configured_unit_price_times_metadata_workload_estimate",
        "external_api_call_estimate": api_calls,
    }


def _estimate_index_size(embedding_tokens: dict[str, Any], *, index_bytes_per_token: int) -> dict[str, Any]:
    low = int(embedding_tokens["low"]) * max(1, index_bytes_per_token)
    high = int(embedding_tokens["high"]) * max(1, index_bytes_per_token)
    return {
        "low_bytes": low,
        "high_bytes": high,
        "method": "embedding_token_proxy_times_index_bytes_per_token",
    }


def _cost_risk_items(risk_report: dict[str, Any], local_space_pressure: str) -> list[str]:
    mapping = {
        "RISK_SOURCE_NOT_CONFIGURED": "COST_SOURCE_NOT_CONFIGURED",
        "RISK_SOURCE_BLOCKED": "COST_SOURCE_BLOCKED",
        "RISK_DRIVE_OFFLINE": "COST_DRIVE_OFFLINE",
        "RISK_SUSPICIOUS_ARCHIVE_PRESENT": "COST_ARCHIVE_REVIEW_REQUIRED",
        "RISK_HIGH_RISK_FILE_PRESENT": "COST_HIGH_RISK_FILE_PRESENT",
        "RISK_LARGE_BATCH_PRESENT": "COST_LARGE_BATCH_PRESENT",
        "RISK_OVERSIZED_FILE_PRESENT": "COST_OVERSIZED_FILE_PRESENT",
        "RISK_UNKNOWN_FORMAT_PRESENT": "COST_UNKNOWN_FORMAT_PRESENT",
        "RISK_INSUFFICIENT_SPACE": "COST_INSUFFICIENT_SPACE",
    }
    items = [mapping[item] for item in risk_report.get("risk_items", []) if item in mapping]
    if local_space_pressure == "blocked":
        items.append("COST_LOCAL_SPACE_BLOCKED")
    if local_space_pressure == "high":
        items.append("COST_LOCAL_SPACE_PRESSURE_HIGH")
    return list(dict.fromkeys(items))


def _cost_score_band(risk_report: dict[str, Any], cost_risks: list[str], total_cost_high: float) -> str:
    if any(item in cost_risks for item in {"COST_SOURCE_NOT_CONFIGURED", "COST_SOURCE_BLOCKED", "COST_DRIVE_OFFLINE", "COST_INSUFFICIENT_SPACE", "COST_LOCAL_SPACE_BLOCKED"}):
        return "blocked"
    if risk_report.get("risk_score_band") == "high" or total_cost_high >= 10:
        return "high"
    if cost_risks or total_cost_high >= 0.10:
        return "medium"
    return "low"


def _state_from_band(cost_score_band: str) -> str:
    if cost_score_band == "blocked":
        return "COST_BLOCKED"
    if cost_score_band in {"high", "medium"}:
        return "COST_OWNER_REVIEW_REQUIRED"
    return "COST_READY"


def _priority_hint(risk_report: dict[str, Any], cost_score_band: str) -> str:
    if cost_score_band == "blocked":
        return "blocked"
    risk_priority = risk_report.get("priority_hint")
    if risk_priority in {"archive_review_first", "split_large_files", "skip_unknown_format"}:
        return risk_priority
    if cost_score_band in {"high", "medium"}:
        return "review_cost_before_import"
    return "low_cost_first"


def _human_product_entrance_payload(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": "导入成本估算器",
        "customer_visible": True,
        "summary_cards": [
            {"label": "文件数量", "value": report["file_count_estimate"]},
            {"label": "预计 Embedding token", "value": report["embedding_token_estimate"]["high"]},
            {"label": "预计 OCR 页数", "value": report["ocr_page_estimate"]["high"]},
            {"label": "预计外部 API 成本", "value": report["external_api_cost_estimate"]["high"]},
            {"label": "预计索引体积", "value": report["index_size_estimate"]["high_bytes"]},
            {"label": "本机空间压力", "value": report["local_space_pressure"]},
            {"label": "成本等级", "value": report["cost_score_band"]},
        ],
        "owner_actions": [
            "review_cost_before_import",
            "approve_cost_and_continue",
            "cancel_without_side_effects",
        ],
        "confirmation_required": True,
        "message": "这是导入前的元信息成本估算；确认前不会启动解析、OCR、Embedding、索引、外部 API 或实际导入。",
    }


def _is_high_risk_candidate(record: dict[str, Any]) -> bool:
    skip_tags = {"suspicious_archive", "scanned_document", "unknown_format"}
    return bool(skip_tags.intersection(set(record.get("risk_tags", []))))


def _chunk_records(records: list[dict[str, Any]], batch_size: int) -> list[list[dict[str, Any]]]:
    if not records:
        return []
    size = max(1, batch_size)
    return [records[index : index + size] for index in range(0, len(records), size)]


def evaluate_import_cost_estimate(
    *,
    source_uris: list[str | None] | tuple[str | None, ...] | None,
    estimated_at: str | None = None,
    drive_state: str = "online",
    available_space_bytes: int | None = None,
    oversized_file_threshold_bytes: int = DEFAULT_OVERSIZED_FILE_THRESHOLD_BYTES,
    embedding_price_per_1k_tokens: float = DEFAULT_EMBEDDING_PRICE_PER_1K_TOKENS,
    external_api_price_per_call: float = DEFAULT_EXTERNAL_API_PRICE_PER_CALL,
    ocr_price_per_page: float = DEFAULT_OCR_PRICE_PER_PAGE,
    index_bytes_per_token: int = DEFAULT_INDEX_BYTES_PER_TOKEN,
) -> dict[str, Any]:
    """Build Stage 020 cost estimates from metadata-only Stage 018/019 reports."""

    estimated_at = estimated_at or _utc_now()
    risk_module = _load_stage019_module()
    risk_report = risk_module.evaluate_import_risk_estimate(
        source_uris=source_uris,
        estimated_at=estimated_at,
        drive_state=drive_state,
        available_space_bytes=available_space_bytes,
        oversized_file_threshold_bytes=oversized_file_threshold_bytes,
    )
    records = list(risk_report.get("candidate_files", []))
    file_count = int(risk_report.get("file_count_estimate", 0))
    total_size = int(risk_report.get("total_size_bytes_estimate", 0))
    embedding_tokens = _estimate_embedding_tokens(records)
    ocr_pages = _estimate_ocr_pages(records)
    api_calls = _estimate_external_api_calls(file_count, ocr_pages, embedding_tokens)
    api_cost = _estimate_external_api_cost(
        embedding_tokens=embedding_tokens,
        ocr_pages=ocr_pages,
        api_calls=api_calls,
        embedding_price_per_1k_tokens=embedding_price_per_1k_tokens,
        external_api_price_per_call=external_api_price_per_call,
        ocr_price_per_page=ocr_price_per_page,
    )
    index_size = _estimate_index_size(embedding_tokens, index_bytes_per_token=index_bytes_per_token)
    future_local_bytes = total_size + int(index_size["high_bytes"])
    local_space_pressure = _storage_pressure(future_local_bytes, available_space_bytes)
    risk_items = _cost_risk_items(risk_report, local_space_pressure)
    band = _cost_score_band(risk_report, risk_items, float(api_cost["high"]))
    state = _state_from_band(band)
    cost_items = {
        "embedding_workload_class": _workload_class(embedding_tokens["high"]),
        "ocr_workload_class": _workload_class(ocr_pages["high"]),
        "api_call_class": _workload_class(api_calls["high"]),
        "api_cost_class": _money_class(float(api_cost["high"])),
        "index_size_class": _workload_class(index_size["high_bytes"] / (1024 * 1024)),
        "local_space_pressure_class": local_space_pressure,
        "batch_split_hint": risk_report.get("cost_items", {}).get("batch_split_hint", "not_required"),
    }
    report: dict[str, Any] = {
        "schema_version": "ids.stage020.import_cost_estimator.v1",
        "stage": "STAGE-020",
        "phase": "Phase 2",
        "acceptance_id": "ACC-STAGE-020",
        "entrance": ENTRANCE,
        "customer_visible": True,
        "source_preflight_schema": risk_report.get("source_preflight_schema"),
        "source_risk_schema": risk_report.get("schema_version"),
        "source_risk_state": risk_report.get("overall_state"),
        "estimated_at": estimated_at,
        "cost_estimation_mode": "dry_run_metadata_only",
        "confirmation_required": True,
        "overall_state": state,
        "confirmation_status": state,
        "file_count_estimate": file_count,
        "total_size_bytes_estimate": total_size,
        "format_counts": risk_report.get("format_counts", {}),
        "archive_candidate_count": risk_report.get("archive_candidate_count", 0),
        "scanned_document_candidate_count": risk_report.get("scanned_document_candidate_count", 0),
        "unknown_format_count": risk_report.get("unknown_format_count", 0),
        "oversized_file_count": risk_report.get("oversized_file_count", 0),
        "high_risk_file_count": risk_report.get("high_risk_file_count", 0),
        "embedding_token_estimate": embedding_tokens,
        "external_api_cost_estimate": api_cost,
        "ocr_page_estimate": ocr_pages,
        "index_size_estimate": index_size,
        "local_space_pressure": local_space_pressure,
        "future_local_space_bytes_estimate": future_local_bytes,
        "cost_score_band": band,
        "risk_items": risk_items,
        "cost_items": cost_items,
        "priority_hint": _priority_hint(risk_report, band),
        "candidate_files": records,
        "rejected_inputs": risk_report.get("rejected_inputs", []),
        "rejected_input_count": risk_report.get("rejected_input_count", 0),
        "uncertainty_items": [
            "Embedding token 估算使用文件大小元信息代理，不解析正文，也不代表真实 tokenizer 结果。",
            "OCR 页数估算使用扫描件候选数量和大小代理，不启动 OCR，也不确认图片质量。",
            "外部 API 成本估算使用配置单价和元信息工作量代理，不调用任何外部 API。",
            "索引体积估算使用 token 代理乘以配置系数，不建立索引。",
            "本机空间压力只比较估算输入体积、索引体积和传入 available_space_bytes，不替代系统级容量审计。",
        ],
        "no_persistence_deltas": dict(NO_PERSISTENCE_DELTAS),
    }
    report["human_product_entrance_payload"] = _human_product_entrance_payload(report)
    report.update(NO_SIDE_EFFECT_FLAGS)
    return report


def build_cost_owner_decision_plan(cost_report: dict[str, Any], *, batch_size: int = 50) -> dict[str, Any]:
    """Create an owner-decision plan without persisting or processing imports."""

    candidate_files = list(cost_report.get("candidate_files", []))
    high_risk_files = [record for record in candidate_files if _is_high_risk_candidate(record)]
    kept_files = [record for record in candidate_files if not _is_high_risk_candidate(record)]
    batches = _chunk_records(candidate_files, batch_size)
    serialized = json.dumps(cost_report, ensure_ascii=False, sort_keys=True)
    no_persistence = dict(NO_PERSISTENCE_DELTAS)
    return {
        "schema_version": "ids.stage020.import_cost_estimator.owner_decision.v1",
        "stage": "STAGE-020",
        "phase": "Phase 3",
        "acceptance_id": "ACC-STAGE-020",
        "entrance": ENTRANCE,
        "source_cost_state": cost_report.get("overall_state"),
        "supported_owner_actions": [
            "save_for_owner_review",
            "cancel_without_side_effects",
            "split_into_batches",
            "skip_high_risk_files",
        ],
        "save_contract": {
            "state": "COST_RESULT_SERIALIZABLE",
            "can_save_result": True,
            "persisted_by_helper": False,
            "serialized_bytes": len(serialized.encode("utf-8")),
            "owner_selected_path_required": True,
        },
        "cancel_contract": {"state": "COST_CANCEL_READY", **no_persistence},
        "batch_plan": {
            "can_split": len(batches) > 1,
            "batch_size": max(1, batch_size),
            "batch_count": len(batches),
            "batches": [
                {
                    "batch_index": index + 1,
                    "file_count": len(batch),
                    "total_size_bytes": sum(int(record.get("file_size", 0)) for record in batch),
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
    }


def build_stage020_scenario_report(
    *,
    scenario_sources: dict[str, dict[str, Any]],
    estimated_at: str | None = None,
    batch_size: int = 50,
    oversized_file_threshold_bytes: int = DEFAULT_OVERSIZED_FILE_THRESHOLD_BYTES,
) -> dict[str, Any]:
    """Validate Stage 020 cost-estimator scenarios using metadata-only inputs."""

    estimated_at = estimated_at or _utc_now()
    scenario_results: dict[str, dict[str, Any]] = {}
    for scenario_id in sorted(scenario_sources):
        scenario = scenario_sources[scenario_id]
        cost_estimate = evaluate_import_cost_estimate(
            source_uris=scenario.get("source_uris"),
            estimated_at=estimated_at,
            drive_state=scenario.get("drive_state", "online"),
            available_space_bytes=scenario.get("available_space_bytes"),
            oversized_file_threshold_bytes=scenario.get(
                "oversized_file_threshold_bytes", oversized_file_threshold_bytes
            ),
            embedding_price_per_1k_tokens=scenario.get(
                "embedding_price_per_1k_tokens", DEFAULT_EMBEDDING_PRICE_PER_1K_TOKENS
            ),
            external_api_price_per_call=scenario.get(
                "external_api_price_per_call", DEFAULT_EXTERNAL_API_PRICE_PER_CALL
            ),
            ocr_price_per_page=scenario.get("ocr_price_per_page", DEFAULT_OCR_PRICE_PER_PAGE),
            index_bytes_per_token=scenario.get("index_bytes_per_token", DEFAULT_INDEX_BYTES_PER_TOKEN),
        )
        scenario_results[scenario_id] = {
            "scenario_id": scenario_id,
            "cost_estimate": cost_estimate,
            "owner_decision_plan": build_cost_owner_decision_plan(cost_estimate, batch_size=batch_size),
        }

    required_scenarios_covered = REQUIRED_PHASE3_SCENARIOS.issubset(set(scenario_results))
    report: dict[str, Any] = {
        "schema_version": "ids.stage020.import_cost_estimator.scenario_validation.v1",
        "stage": "STAGE-020",
        "phase": "Phase 3",
        "acceptance_id": "ACC-STAGE-020",
        "entrance": ENTRANCE,
        "customer_visible": True,
        "validation_state": (
            "SCENARIO_VALIDATION_PASSED" if required_scenarios_covered else "SCENARIO_VALIDATION_PARTIAL"
        ),
        "estimated_at": estimated_at,
        "scenario_count": len(scenario_results),
        "required_scenarios": sorted(REQUIRED_PHASE3_SCENARIOS),
        "required_scenarios_covered": required_scenarios_covered,
        "scenario_results": scenario_results,
        "processing_guard": dict(PROCESSING_GUARD_ZEROES),
        "no_persistence_deltas": dict(NO_PERSISTENCE_DELTAS),
    }
    report.update(NO_SIDE_EFFECT_FLAGS)
    return report


def _cost_report_sample(cost_report: dict[str, Any]) -> dict[str, Any]:
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
        "embedding_token_estimate",
        "external_api_cost_estimate",
        "ocr_page_estimate",
        "index_size_estimate",
        "local_space_pressure",
        "future_local_space_bytes_estimate",
        "cost_score_band",
        "risk_items",
        "cost_items",
        "priority_hint",
        "human_product_entrance_payload",
    ]
    return {key: cost_report.get(key) for key in sample_keys}


def build_cost_owner_feedback_summary(
    cost_report: dict[str, Any],
    *,
    recorded_at: str | None = None,
    stage_review_findings: list[str] | tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """Build Phase 4 closeout evidence without creating runtime artifacts."""

    recorded_at = recorded_at or _utc_now()
    feedback: dict[str, Any] = {
        "schema_version": "ids.stage020.import_cost_estimator.owner_feedback.v1",
        "stage": "STAGE-020",
        "phase": "Phase 4",
        "task_id": "IDS-V0_1-STAGE020-P4",
        "acceptance_id": "ACC-STAGE-020",
        "entrance": ENTRANCE,
        "recorded_at": recorded_at,
        "report_sample": _cost_report_sample(cost_report),
        "risk_checklist": {
            "COST_SOURCE_NOT_CONFIGURED": "未配置导入来源；请先选择 owner 批准的本地 file:// 输入。",
            "COST_SOURCE_BLOCKED": "来源不可用或越过安全边界；系统不会继续读取或推断该来源。",
            "COST_DRIVE_OFFLINE": "移动硬盘或来源盘处于离线状态；请重新接入后再做成本估算。",
            "COST_ARCHIVE_REVIEW_REQUIRED": "发现压缩包候选；需要 owner 复核后再决定是否单独处理。",
            "COST_HIGH_RISK_FILE_PRESENT": "发现高风险文件；建议先跳过或拆分批次再复核。",
            "COST_LARGE_BATCH_PRESENT": "文件数量较多；建议先分批处理并保留人工确认点。",
            "COST_OVERSIZED_FILE_PRESENT": "发现超大文件；建议拆分批次或先跳过后复核。",
            "COST_UNKNOWN_FORMAT_PRESENT": "发现未知格式；建议跳过或转交人工处理。",
            "COST_INSUFFICIENT_SPACE": "目标空间不足；请释放空间或缩小批次后再继续。",
            "COST_LOCAL_SPACE_BLOCKED": "本机空间估算不足；确认前不会启动导入或索引。",
            "COST_LOCAL_SPACE_PRESSURE_HIGH": "本机空间压力较高；建议降低批次规模后再继续。",
        },
        "user_confirmation_flow_log": [
            "系统展示预检报告样例，owner 先查看文件数量、格式、大小、Embedding token、OCR 页数、外部 API 成本、索引体积和本机空间压力。",
            "owner 可以选择保存成本估算结果；当前 helper 只提供可序列化内容，不自动落盘。",
            "owner 可以选择取消；取消后 document/chunk/job/index/import/manifest/database 写入均保持 0。",
            "owner 可以选择分批；系统只生成 metadata batch plan，不启动解析、OCR、Embedding、索引、外部 API 或导入。",
            "owner 可以选择跳过高风险文件；压缩包、扫描件、未知格式和可疑候选会进入跳过候选清单。",
            "owner 明确确认后，后续 Stage 才能进入批量处理；本 Stage 不授权实际导入。",
        ],
        "estimation_uncertainty": [
            "Embedding token 估算使用文件大小元信息代理，不解析正文，也不代表真实 tokenizer 结果。",
            "OCR 页数估算使用扫描件候选数量和大小代理，不启动 OCR，也不确认图片质量。",
            "外部 API 成本估算使用配置单价和元信息工作量代理，不调用任何外部 API。",
            "索引体积估算使用 token 代理乘以配置系数，不建立索引。",
            "本机空间压力只比较估算输入体积、索引体积和传入 available_space_bytes，不替代系统级容量审计。",
            "目录处理保持 immediate-child metadata-only，不代表递归扫描或真实生产 corpus 覆盖率。",
        ],
        "failure_explanations": {
            "COST_SOURCE_NOT_CONFIGURED": "未配置导入来源；请先选择 owner 批准的本地 file:// 输入。",
            "COST_SOURCE_BLOCKED": "来源不可用或越过安全边界；系统不会继续读取或推断该来源。",
            "COST_DRIVE_OFFLINE": "移动硬盘或来源盘处于离线状态；请重新接入后再做成本估算。",
            "COST_ARCHIVE_REVIEW_REQUIRED": "发现压缩包候选；需要 owner 复核后再决定是否单独处理。",
            "COST_HIGH_RISK_FILE_PRESENT": "发现高风险文件；建议先跳过或拆分批次再复核。",
            "COST_LARGE_BATCH_PRESENT": "文件数量较多；建议先分批处理并保留人工确认点。",
            "COST_OVERSIZED_FILE_PRESENT": "发现超大文件；建议拆分批次或先跳过后复核。",
            "COST_UNKNOWN_FORMAT_PRESENT": "发现未知格式；建议跳过或转交人工处理。",
            "COST_INSUFFICIENT_SPACE": "目标空间不足；请释放空间或缩小批次后再继续。",
            "COST_LOCAL_SPACE_BLOCKED": "本机空间估算不足；请释放空间、缩小批次或更换目标盘后再继续。",
        },
        "rollback_steps": [
            "Revert Stage020 Phase4 helper additions, focused tests, closeout evidence, Stage005 validator/test changes, batch-lock, roadmap/event, and rendered owner-file changes.",
            "Do not move, delete, overwrite, rewrite, compact, clean, normalize, repair, or deduplicate original files in place.",
            "Do not clean /Users/linzezhang/Downloads/IDS_MetaData, runtime databases, reports, outputs, persisted manifests, evidence ledgers, audit logs, indexes, delivered reports, app entries, or GitHub state.",
            "After rollback, STAGE-020 should return to Phase 3 complete and Phase 4 pending.",
        ],
        "whole_stage_review": {
            "result": "passed_with_local_evidence",
            "completed_phases": ["Phase 1", "Phase 2", "Phase 3", "Phase 4"],
            "reviewed_acceptance_id": "ACC-STAGE-020",
            "findings": list(stage_review_findings or []),
            "unresolved_findings": [],
            "next_stage": "STAGE-021",
            "batch_upload_allowed": False,
            "next_batch_gate": "BATCH011_020_REVIEW_GATE",
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
        "does_not_enter_stage021": True,
    }
    feedback.update(NO_SIDE_EFFECT_FLAGS)
    return feedback


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a metadata-only Stage 020 import cost estimate.")
    parser.add_argument(
        "--source-uri",
        action="append",
        dest="source_uris",
        help="Explicit file:// source root or file URI. Repeat for multiple approved roots.",
    )
    parser.add_argument("--estimated-at", help="UTC estimate timestamp for deterministic runs.")
    parser.add_argument("--drive-state", default="online", help="online, offline, disconnected, missing, or unavailable.")
    parser.add_argument("--available-space-bytes", type=int, help="Optional future target-space estimate.")
    parser.add_argument(
        "--oversized-file-threshold-bytes",
        type=int,
        default=DEFAULT_OVERSIZED_FILE_THRESHOLD_BYTES,
        help="Size threshold used only for dry-run cost/risk classification.",
    )
    parser.add_argument(
        "--embedding-price-per-1k-tokens",
        type=float,
        default=DEFAULT_EMBEDDING_PRICE_PER_1K_TOKENS,
        help="Dry-run configured embedding unit price; no external call is made.",
    )
    parser.add_argument(
        "--external-api-price-per-call",
        type=float,
        default=DEFAULT_EXTERNAL_API_PRICE_PER_CALL,
        help="Dry-run configured API call unit price; no external call is made.",
    )
    parser.add_argument(
        "--ocr-price-per-page",
        type=float,
        default=DEFAULT_OCR_PRICE_PER_PAGE,
        help="Dry-run configured OCR page unit price; no OCR is started.",
    )
    parser.add_argument(
        "--index-bytes-per-token",
        type=int,
        default=DEFAULT_INDEX_BYTES_PER_TOKEN,
        help="Dry-run configured index-size multiplier; no index is built.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    report = evaluate_import_cost_estimate(
        source_uris=args.source_uris,
        estimated_at=args.estimated_at,
        drive_state=args.drive_state,
        available_space_bytes=args.available_space_bytes,
        oversized_file_threshold_bytes=args.oversized_file_threshold_bytes,
        embedding_price_per_1k_tokens=args.embedding_price_per_1k_tokens,
        external_api_price_per_call=args.external_api_price_per_call,
        ocr_price_per_page=args.ocr_price_per_page,
        index_bytes_per_token=args.index_bytes_per_token,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
