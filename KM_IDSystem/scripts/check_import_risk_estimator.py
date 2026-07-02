#!/usr/bin/env python3
"""Metadata-only Stage 019 import risk estimate for IDS."""

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


def _load_preflight_module() -> Any:
    path = Path(__file__).with_name("check_import_preflight.py")
    spec = importlib.util.spec_from_file_location("stage018_import_preflight", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load Stage 018 preflight helper from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _cost_class(count: int) -> str:
    if count <= 0:
        return "none"
    if count <= 10:
        return "low"
    if count <= 100:
        return "medium"
    return "high"


def _operator_review_class(high_risk_count: int) -> str:
    if high_risk_count <= 0:
        return "none"
    if high_risk_count <= 2:
        return "low"
    if high_risk_count <= 10:
        return "medium"
    return "high"


def _storage_pressure(total_size: int) -> str:
    if total_size <= 0:
        return "none"
    if total_size < 100 * 1024 * 1024:
        return "low"
    if total_size < 5 * 1024 * 1024 * 1024:
        return "medium"
    return "high"


def _risk_score_band(risks: list[str]) -> str:
    blocking = {
        "RISK_SOURCE_NOT_CONFIGURED",
        "RISK_SOURCE_BLOCKED",
        "RISK_DRIVE_OFFLINE",
        "RISK_INSUFFICIENT_SPACE",
    }
    high = {
        "RISK_OVERSIZED_FILE_PRESENT",
        "RISK_SUSPICIOUS_ARCHIVE_PRESENT",
        "RISK_UNKNOWN_FORMAT_PRESENT",
    }
    if any(risk in risks for risk in blocking):
        return "blocked"
    if any(risk in risks for risk in high):
        return "high"
    if risks:
        return "medium"
    return "low"


def _priority_hint(risks: list[str], risk_score_band: str) -> str:
    if risk_score_band == "blocked":
        return "blocked"
    if "RISK_SUSPICIOUS_ARCHIVE_PRESENT" in risks:
        return "archive_review_first"
    if "RISK_OVERSIZED_FILE_PRESENT" in risks:
        return "split_large_files"
    if "RISK_LARGE_BATCH_PRESENT" in risks:
        return "split_large_files"
    if "RISK_UNKNOWN_FORMAT_PRESENT" in risks:
        return "skip_unknown_format"
    if risks:
        return "manual_review_first"
    return "low_risk_first"


def _state_from_band(risk_score_band: str) -> str:
    if risk_score_band == "blocked":
        return "RISK_BLOCKED"
    if risk_score_band in {"high", "medium"}:
        return "RISK_OWNER_REVIEW_REQUIRED"
    return "RISK_READY"


def _safe_record_ref(record: dict[str, Any], *, oversized: bool) -> dict[str, Any]:
    return {
        "source_uri": record.get("source_uri"),
        "source_path": record.get("source_path"),
        "basename": record.get("basename"),
        "extension": record.get("extension"),
        "file_size": record.get("file_size", 0),
        "risk_tags": [
            tag
            for tag, enabled in {
                "suspicious_archive": record.get("archive_candidate", False),
                "scanned_document": record.get("scanned_document_candidate", False),
                "unknown_format": record.get("unsupported_format", False),
                "oversized": oversized,
            }.items()
            if enabled
        ],
    }


def _human_product_entrance_payload(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": "导入风险估算器",
        "customer_visible": True,
        "summary_cards": [
            {"label": "文件数量", "value": report["file_count_estimate"]},
            {"label": "高风险文件", "value": report["high_risk_file_count"]},
            {"label": "超大文件", "value": report["oversized_file_count"]},
            {"label": "可疑压缩包", "value": report["suspicious_archive_count"]},
            {"label": "未知格式", "value": report["unknown_format_count"]},
            {"label": "空间不足风险", "value": report["insufficient_space_risk"]},
            {"label": "风险等级", "value": report["risk_score_band"]},
        ],
        "owner_actions": [
            "cancel_without_side_effects",
            "split_batch",
            "skip_high_risk",
            "review_later",
        ],
        "confirmation_required": True,
        "message": "这是导入前的元信息风险估算；确认前不会启动解析、OCR、Embedding、索引或实际导入。",
    }


def _is_high_risk_candidate(record: dict[str, Any]) -> bool:
    return bool(record.get("risk_tags"))


def _chunk_records(records: list[dict[str, Any]], batch_size: int) -> list[list[dict[str, Any]]]:
    if not records:
        return []
    size = max(1, batch_size)
    return [records[index : index + size] for index in range(0, len(records), size)]


def evaluate_import_risk_estimate(
    *,
    source_uris: list[str | None] | tuple[str | None, ...] | None,
    estimated_at: str | None = None,
    drive_state: str = "online",
    available_space_bytes: int | None = None,
    oversized_file_threshold_bytes: int = DEFAULT_OVERSIZED_FILE_THRESHOLD_BYTES,
) -> dict[str, Any]:
    """Build Stage 019 risk estimates from Stage 018 metadata-only preflight."""

    estimated_at = estimated_at or _utc_now()
    preflight = _load_preflight_module().evaluate_import_preflight(
        source_uris=source_uris,
        prechecked_at=estimated_at,
        drive_state=drive_state,
        available_space_bytes=available_space_bytes,
    )
    records = list(preflight.get("file_records", []))
    threshold = max(0, oversized_file_threshold_bytes)
    oversized_records = [record for record in records if int(record.get("file_size", 0)) > threshold]
    oversized_source_uris = {str(record.get("source_uri")) for record in oversized_records}
    suspicious_archive_records = [record for record in records if record.get("archive_candidate")]
    scanned_records = [record for record in records if record.get("scanned_document_candidate")]
    unknown_format_records = [record for record in records if record.get("unsupported_format")]
    high_risk_by_uri: dict[str, tuple[dict[str, Any], bool]] = {}
    for record in suspicious_archive_records + scanned_records + unknown_format_records + oversized_records:
        key = str(record.get("source_uri"))
        high_risk_by_uri[key] = (record, record in oversized_records)

    risk_items: list[str] = []
    preflight_state = preflight.get("overall_state")
    if preflight_state == "PREFLIGHT_NOT_CONFIGURED":
        risk_items.append("RISK_SOURCE_NOT_CONFIGURED")
    if preflight_state == "PREFLIGHT_SOURCE_BLOCKED":
        risk_items.append("RISK_SOURCE_BLOCKED")
    if preflight_state == "PREFLIGHT_DRIVE_OFFLINE":
        risk_items.append("RISK_DRIVE_OFFLINE")
    if suspicious_archive_records:
        risk_items.append("RISK_SUSPICIOUS_ARCHIVE_PRESENT")
    if scanned_records or high_risk_by_uri:
        risk_items.append("RISK_HIGH_RISK_FILE_PRESENT")
    if preflight.get("file_count_estimate", 0) > 100:
        risk_items.append("RISK_LARGE_BATCH_PRESENT")
    if oversized_records:
        risk_items.append("RISK_OVERSIZED_FILE_PRESENT")
    if unknown_format_records:
        risk_items.append("RISK_UNKNOWN_FORMAT_PRESENT")
    insufficient_space = "PREFLIGHT_INSUFFICIENT_SPACE" in preflight.get("risk_items", [])
    if insufficient_space:
        risk_items.append("RISK_INSUFFICIENT_SPACE")
    risk_items = list(dict.fromkeys(risk_items))
    band = _risk_score_band(risk_items)
    total_size = int(preflight.get("total_size_bytes_estimate", 0))
    high_risk_files = [
        _safe_record_ref(record, oversized=oversized)
        for _key, (record, oversized) in sorted(high_risk_by_uri.items())
    ]
    candidate_files = [
        _safe_record_ref(record, oversized=str(record.get("source_uri")) in oversized_source_uris)
        for record in sorted(records, key=lambda item: str(item.get("source_uri")))
    ]
    cost_items = {
        "local_metadata_review_class": _cost_class(preflight.get("file_count_estimate", 0)),
        "storage_pressure_class": _storage_pressure(total_size),
        "archive_review_class": _cost_class(len(suspicious_archive_records)),
        "ocr_workload_class": _cost_class(len(scanned_records)),
        "embedding_workload_class": _cost_class(preflight.get("estimated_embedding_units", 0)),
        "operator_review_class": _operator_review_class(len(high_risk_files)),
        "batch_split_hint": "split_required" if oversized_records or preflight.get("file_count_estimate", 0) > 100 else "not_required",
    }
    report: dict[str, Any] = {
        "schema_version": "ids.stage019.import_risk_estimator.v1",
        "stage": "STAGE-019",
        "phase": "Phase 2",
        "acceptance_id": "ACC-STAGE-019",
        "entrance": ENTRANCE,
        "customer_visible": True,
        "source_preflight_schema": preflight.get("schema_version"),
        "source_preflight_state": preflight_state,
        "estimated_at": estimated_at,
        "risk_estimation_mode": "dry_run_metadata_only",
        "confirmation_required": True,
        "file_count_estimate": preflight.get("file_count_estimate", 0),
        "total_size_bytes_estimate": total_size,
        "format_counts": preflight.get("format_counts", {}),
        "archive_candidate_count": preflight.get("archive_candidate_count", 0),
        "scanned_document_candidate_count": preflight.get("scanned_document_candidate_count", 0),
        "estimated_ocr_units": preflight.get("estimated_ocr_units", 0),
        "estimated_embedding_units": preflight.get("estimated_embedding_units", 0),
        "high_risk_file_count": len(high_risk_files),
        "oversized_file_count": len(oversized_records),
        "suspicious_archive_count": len(suspicious_archive_records),
        "unknown_format_count": len(unknown_format_records),
        "insufficient_space_risk": insufficient_space,
        "risk_score_band": band,
        "overall_state": _state_from_band(band),
        "confirmation_status": _state_from_band(band),
        "risk_items": risk_items,
        "cost_items": cost_items,
        "priority_hint": _priority_hint(risk_items, band),
        "candidate_files": candidate_files,
        "high_risk_files": high_risk_files,
        "rejected_inputs": preflight.get("rejected_inputs", []),
        "rejected_input_count": preflight.get("rejected_input_count", 0),
        "uncertainty_items": [
            "风险估算只基于显式 file:// 输入的元信息，不代表正文质量、页数或解析耗时。",
            "压缩包内部结构、扫描件页数、未知格式可读性和实际 OCR/Embedding 成本需要后续授权阶段确认。",
            "空间不足判断只比较传入 available_space_bytes 与估算体积，不替代系统级容量审计。",
        ],
        "no_persistence_deltas": dict(NO_PERSISTENCE_DELTAS),
    }
    report["human_product_entrance_payload"] = _human_product_entrance_payload(report)
    report.update(NO_SIDE_EFFECT_FLAGS)
    return report


def build_risk_operator_decision_plan(risk_report: dict[str, Any], *, batch_size: int = 50) -> dict[str, Any]:
    """Create an owner-decision plan without persisting or processing imports."""

    candidate_files = list(risk_report.get("candidate_files", []))
    high_risk_files = [record for record in candidate_files if _is_high_risk_candidate(record)]
    kept_files = [record for record in candidate_files if not _is_high_risk_candidate(record)]
    batches = _chunk_records(candidate_files, batch_size)
    serialized = json.dumps(risk_report, ensure_ascii=False, sort_keys=True)
    no_persistence = dict(NO_PERSISTENCE_DELTAS)
    return {
        "schema_version": "ids.stage019.import_risk_estimator.operator_decision.v1",
        "stage": "STAGE-019",
        "phase": "Phase 3",
        "acceptance_id": "ACC-STAGE-019",
        "entrance": ENTRANCE,
        "source_risk_state": risk_report.get("overall_state"),
        "supported_owner_actions": [
            "save_for_owner_review",
            "cancel_without_side_effects",
            "split_into_batches",
            "skip_high_risk_files",
        ],
        "save_contract": {
            "state": "RISK_RESULT_SERIALIZABLE",
            "can_save_result": True,
            "persisted_by_helper": False,
            "serialized_bytes": len(serialized.encode("utf-8")),
            "owner_selected_path_required": True,
        },
        "cancel_contract": {"state": "RISK_CANCEL_READY", **no_persistence},
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


def build_stage019_scenario_report(
    *,
    scenario_sources: dict[str, dict[str, Any]],
    estimated_at: str | None = None,
    batch_size: int = 50,
    oversized_file_threshold_bytes: int = DEFAULT_OVERSIZED_FILE_THRESHOLD_BYTES,
) -> dict[str, Any]:
    """Validate Stage 019 risk-estimator scenarios using metadata-only inputs."""

    estimated_at = estimated_at or _utc_now()
    scenario_results: dict[str, dict[str, Any]] = {}
    for scenario_id in sorted(scenario_sources):
        scenario = scenario_sources[scenario_id]
        risk_estimate = evaluate_import_risk_estimate(
            source_uris=scenario.get("source_uris"),
            estimated_at=estimated_at,
            drive_state=scenario.get("drive_state", "online"),
            available_space_bytes=scenario.get("available_space_bytes"),
            oversized_file_threshold_bytes=scenario.get(
                "oversized_file_threshold_bytes", oversized_file_threshold_bytes
            ),
        )
        scenario_results[scenario_id] = {
            "scenario_id": scenario_id,
            "risk_estimate": risk_estimate,
            "operator_decision_plan": build_risk_operator_decision_plan(
                risk_estimate, batch_size=batch_size
            ),
        }

    required_scenarios_covered = REQUIRED_PHASE3_SCENARIOS.issubset(set(scenario_results))
    report: dict[str, Any] = {
        "schema_version": "ids.stage019.import_risk_estimator.scenario_validation.v1",
        "stage": "STAGE-019",
        "phase": "Phase 3",
        "acceptance_id": "ACC-STAGE-019",
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


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a metadata-only Stage 019 import risk estimate.")
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
        help="Size threshold used only for dry-run risk classification.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    report = evaluate_import_risk_estimate(
        source_uris=args.source_uris,
        estimated_at=args.estimated_at,
        drive_state=args.drive_state,
        available_space_bytes=args.available_space_bytes,
        oversized_file_threshold_bytes=args.oversized_file_threshold_bytes,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
