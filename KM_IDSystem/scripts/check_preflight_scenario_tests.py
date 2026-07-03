#!/usr/bin/env python3
"""Metadata-only Stage 023 preflight scenario-test payload for IDS."""

from __future__ import annotations

import argparse
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ENTRANCE = "人类产品入口 + IDS 系统运营入口"
DEFAULT_OVERSIZED_FILE_THRESHOLD_BYTES = 512 * 1024 * 1024
REQUIRED_SCENARIOS = {
    "empty_directory",
    "small_directory",
    "large_directory",
    "offline_drive",
    "bad_file",
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
    "actual_scenario_runner_jobs_started": 0,
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
    "scenario_result_write_delta": 0,
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
    "does_not_write_scenario_results": True,
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


def _is_bad_file_candidate(record: dict[str, Any]) -> bool:
    basename = str(record.get("basename", "")).lower()
    extension = str(record.get("extension", "")).lower()
    return (
        int(record.get("file_size", 0)) == 0
        or extension in {".bad", ".corrupt", ".broken"}
        or "bad" in basename
        or "corrupt" in basename
        or "broken" in basename
    )


def _scenario_risk_items(cost_report: dict[str, Any], bad_file_count: int) -> list[str]:
    mapping = {
        "COST_SOURCE_NOT_CONFIGURED": "SCENARIO_SOURCE_NOT_CONFIGURED",
        "COST_SOURCE_BLOCKED": "SCENARIO_SOURCE_BLOCKED",
        "COST_DRIVE_OFFLINE": "SCENARIO_OFFLINE_DRIVE",
        "COST_ARCHIVE_REVIEW_REQUIRED": "SCENARIO_ARCHIVE_REVIEW_REQUIRED",
        "COST_HIGH_RISK_FILE_PRESENT": "SCENARIO_HIGH_RISK_FILE_PRESENT",
        "COST_LARGE_BATCH_PRESENT": "SCENARIO_LARGE_DIRECTORY_REVIEW_REQUIRED",
        "COST_OVERSIZED_FILE_PRESENT": "SCENARIO_OVERSIZED_FILE_PRESENT",
        "COST_UNKNOWN_FORMAT_PRESENT": "SCENARIO_UNKNOWN_FORMAT_PRESENT",
        "COST_INSUFFICIENT_SPACE": "SCENARIO_INSUFFICIENT_SPACE",
        "COST_LOCAL_SPACE_BLOCKED": "SCENARIO_LOCAL_SPACE_BLOCKED",
        "COST_LOCAL_SPACE_PRESSURE_HIGH": "SCENARIO_LOCAL_SPACE_PRESSURE_HIGH",
    }
    items = [mapping[item] for item in cost_report.get("risk_items", []) if item in mapping]
    if bad_file_count:
        items.append("SCENARIO_BAD_FILE_PRESENT")
    if int(cost_report.get("file_count_estimate", 0)) == 0 and not cost_report.get("rejected_inputs"):
        items.append("SCENARIO_EMPTY_DIRECTORY")
    return list(dict.fromkeys(items))


def _confirmation_status(cost_report: dict[str, Any], scenario_risks: list[str]) -> str:
    if cost_report.get("overall_state") == "COST_BLOCKED" or cost_report.get("cost_score_band") == "blocked":
        return "PREFLIGHT_SCENARIO_BLOCKED"
    if scenario_risks:
        return "PREFLIGHT_SCENARIO_OWNER_REVIEW_REQUIRED"
    return "PREFLIGHT_SCENARIO_READY"


def _priority_suggestion(status: str, scenario_risks: list[str]) -> str:
    if status == "PREFLIGHT_SCENARIO_BLOCKED":
        return "blocked"
    if any(item in scenario_risks for item in {"SCENARIO_BAD_FILE_PRESENT", "SCENARIO_UNKNOWN_FORMAT_PRESENT", "SCENARIO_ARCHIVE_REVIEW_REQUIRED"}):
        return "split_or_skip_risk_items"
    if scenario_risks:
        return "owner_review_required"
    return "low_risk_first"


def _scenario_summary(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "scenario_test_state": report["overall_state"],
        "priority_suggestion": report["priority_suggestion"],
        "required_scenarios": report["required_scenarios"],
        "file_count": report["file_count_estimate"],
        "format_count": len(report["format_counts"]),
        "archive_candidate_count": report["archive_candidate_count"],
        "scanned_document_candidate_count": report["scanned_document_candidate_count"],
        "bad_file_candidate_count": report["bad_file_candidate_count"],
        "owner_review_required": report["confirmation_status"] != "PREFLIGHT_SCENARIO_READY",
        "next_processing_policy": "owner 确认后才进入批量处理",
    }


def _human_product_entrance_payload(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": "预检场景测试",
        "customer_visible": True,
        "confirmation_required": report["confirmation_status"] != "PREFLIGHT_SCENARIO_READY",
        "summary_cards": [
            {"label": "文件数量", "value": report["file_count_estimate"]},
            {"label": "格式种类", "value": len(report["format_counts"])},
            {"label": "估算总大小", "value": report["total_size_bytes_estimate"]},
            {"label": "压缩包候选", "value": report["archive_candidate_count"]},
            {"label": "扫描件候选", "value": report["scanned_document_candidate_count"]},
            {"label": "坏文件候选", "value": report["bad_file_candidate_count"]},
            {"label": "预计 OCR 页数", "value": report["ocr_page_estimate"]["high"]},
            {"label": "预计 Embedding token", "value": report["embedding_token_estimate"]["high"]},
            {"label": "预计索引体积", "value": report["index_size_estimate"]["high_bytes"]},
            {"label": "确认状态", "value": report["confirmation_status"]},
        ],
        "risk_items": report["risk_items"],
        "cost_items": report["cost_items"],
        "owner_actions": [
            "review_preflight_scenario_tests",
            "approve_preflight_scenarios",
            "pause_without_side_effects",
            "split_batch",
            "skip_high_risk_files",
            "cancel_without_side_effects",
        ],
        "message": "这是导入前的元信息预检场景测试；确认前不会启动解析、OCR、Embedding、索引或实际导入。",
    }


def _ids_operations_payload(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": "IDS 预检场景测试状态",
        "state": report["overall_state"],
        "confirmation_status": report["confirmation_status"],
        "priority_suggestion": report["priority_suggestion"],
        "source_cost_state": report["source_cost_state"],
        "source_cost_score_band": report["source_cost_score_band"],
        "processing_guard": dict(PROCESSING_GUARD_ZEROES),
        "no_persistence_deltas": dict(NO_PERSISTENCE_DELTAS),
    }


def _ui_component_contract() -> dict[str, Any]:
    return {
        "component_name": "PreflightScenarioTestsPanel",
        "props_contract": {
            "summary_cards": "array<{label: string, value: string|number|boolean}>",
            "risk_items": "string[]",
            "cost_items": "object",
            "owner_actions": "string[]",
            "required_scenarios": "string[]",
            "message": "string",
        },
        "display_entrance": ENTRANCE,
        "requires_owner_confirmation_before_processing": True,
    }


def evaluate_preflight_scenario_tests(
    *,
    source_uris: list[str | None] | tuple[str | None, ...] | None,
    evaluated_at: str | None = None,
    drive_state: str = "online",
    available_space_bytes: int | None = None,
    oversized_file_threshold_bytes: int = DEFAULT_OVERSIZED_FILE_THRESHOLD_BYTES,
) -> dict[str, Any]:
    """Build a metadata-only owner-visible preflight scenario-test payload."""

    evaluated_at = evaluated_at or _utc_now()
    cost_report = _load_stage020_module().evaluate_import_cost_estimate(
        source_uris=source_uris,
        estimated_at=evaluated_at,
        drive_state=drive_state,
        available_space_bytes=available_space_bytes,
        oversized_file_threshold_bytes=oversized_file_threshold_bytes,
    )
    candidate_files = list(cost_report.get("candidate_files", []))
    bad_file_count = sum(1 for record in candidate_files if _is_bad_file_candidate(record))
    scenario_risks = _scenario_risk_items(cost_report, bad_file_count)
    status = _confirmation_status(cost_report, scenario_risks)
    report: dict[str, Any] = {
        "schema_version": "ids.stage023.preflight_scenario_tests.v1",
        "stage": "STAGE-023",
        "phase": "Phase 2",
        "task_id": "IDS-V0_1-STAGE023-P2",
        "acceptance_id": "ACC-STAGE-023",
        "entrance": ENTRANCE,
        "customer_visible": True,
        "source_preflight_schema": cost_report.get("source_preflight_schema"),
        "source_risk_schema": cost_report.get("source_risk_schema"),
        "source_cost_schema": cost_report.get("schema_version"),
        "source_cost_state": cost_report.get("overall_state"),
        "source_cost_score_band": cost_report.get("cost_score_band"),
        "evaluated_at": evaluated_at,
        "preflight_scenario_mode": "dry_run_metadata_only",
        "overall_state": status,
        "confirmation_status": status,
        "confirmation_required": status != "PREFLIGHT_SCENARIO_READY",
        "priority_suggestion": _priority_suggestion(status, scenario_risks),
        "required_scenarios": sorted(REQUIRED_SCENARIOS),
        "file_count_estimate": cost_report.get("file_count_estimate", 0),
        "total_size_bytes_estimate": cost_report.get("total_size_bytes_estimate", 0),
        "format_counts": cost_report.get("format_counts", {}),
        "archive_candidate_count": cost_report.get("archive_candidate_count", 0),
        "scanned_document_candidate_count": cost_report.get("scanned_document_candidate_count", 0),
        "unknown_format_count": cost_report.get("unknown_format_count", 0),
        "oversized_file_count": cost_report.get("oversized_file_count", 0),
        "high_risk_file_count": cost_report.get("high_risk_file_count", 0),
        "bad_file_candidate_count": bad_file_count,
        "embedding_token_estimate": cost_report.get("embedding_token_estimate", {}),
        "external_api_cost_estimate": cost_report.get("external_api_cost_estimate", {}),
        "ocr_page_estimate": cost_report.get("ocr_page_estimate", {}),
        "index_size_estimate": cost_report.get("index_size_estimate", {}),
        "local_space_pressure": cost_report.get("local_space_pressure"),
        "risk_items": scenario_risks,
        "cost_items": dict(cost_report.get("cost_items", {})),
        "candidate_files": candidate_files,
        "candidate_file_count": len(candidate_files),
        "rejected_inputs": cost_report.get("rejected_inputs", []),
        "rejected_input_count": cost_report.get("rejected_input_count", 0),
        "uncertainty_items": [
            "Scenario-test payload uses file metadata, Stage 020 estimates, and bad-file indicators only.",
            "Bad-file detection is metadata-only: zero-byte, known bad extensions, or filename hints; no body parse is performed.",
            "OCR, Embedding, external API, and index estimates are inherited from Stage 020 and are not executed here.",
            "Required scenarios define future validation coverage; this Phase 2 does not run Phase 3 scenario validation.",
        ],
        "no_persistence_deltas": dict(NO_PERSISTENCE_DELTAS),
        "processing_guard": dict(PROCESSING_GUARD_ZEROES),
        "ui_component_contract": _ui_component_contract(),
    }
    report["scenario_validation_summary"] = _scenario_summary(report)
    report["human_product_entrance_payload"] = _human_product_entrance_payload(report)
    report["ids_operations_entrance_payload"] = _ids_operations_payload(report)
    report.update(NO_SIDE_EFFECT_FLAGS)
    return report


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a metadata-only Stage 023 preflight scenario-test payload.")
    parser.add_argument(
        "--source-uri",
        action="append",
        dest="source_uris",
        help="Explicit file:// source root or file URI. Repeat for multiple approved roots.",
    )
    parser.add_argument("--evaluated-at", default=None, help="Optional UTC timestamp for deterministic evidence.")
    parser.add_argument("--drive-state", default="online", help="Source drive state: online, offline, disconnected.")
    parser.add_argument("--available-space-bytes", type=int, default=None, help="Optional local free-space estimate.")
    parser.add_argument(
        "--oversized-file-threshold-bytes",
        type=int,
        default=DEFAULT_OVERSIZED_FILE_THRESHOLD_BYTES,
        help="Metadata-only oversized file threshold.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    report = evaluate_preflight_scenario_tests(
        source_uris=args.source_uris,
        evaluated_at=args.evaluated_at,
        drive_state=args.drive_state,
        available_space_bytes=args.available_space_bytes,
        oversized_file_threshold_bytes=args.oversized_file_threshold_bytes,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
