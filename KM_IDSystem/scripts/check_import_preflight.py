#!/usr/bin/env python3
"""Metadata-only Stage 018 import preflight estimate for IDS."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse


ENTRANCE = "人类产品入口 + IDS 系统运营入口"
IDS_METADATA_RAW_ROOT = Path("/Users/linzezhang/Downloads/IDS_MetaData")
OFFLINE_DRIVE_STATES = {"offline", "disconnected", "missing", "unavailable"}
ARCHIVE_EXTENSIONS = {".zip", ".rar", ".7z", ".tar", ".gz", ".tgz", ".bz2", ".xz"}
SCANNED_HINT_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".heic", ".pdf"}
EMBEDDING_HINT_EXTENSIONS = {
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
SUPPORTED_EXTENSIONS = ARCHIVE_EXTENSIONS | SCANNED_HINT_EXTENSIONS | EMBEDDING_HINT_EXTENSIONS
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


def _resolved(path: Path) -> Path:
    return path.expanduser().resolve(strict=False)


def _is_relative_to(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def _parse_source_uri(source_uri: str | None) -> tuple[str | None, Path | None, str | None]:
    if source_uri is None or not source_uri.strip():
        return "PREFLIGHT_NOT_CONFIGURED", None, "source_uri is required."
    parsed = urlparse(source_uri.strip())
    if parsed.scheme != "file":
        return "PREFLIGHT_SOURCE_BLOCKED", None, "source_uri must use the file:// scheme."
    if parsed.netloc not in {"", "localhost"}:
        return "PREFLIGHT_SOURCE_BLOCKED", None, "source_uri must point to a local path."
    if not parsed.path:
        return "PREFLIGHT_SOURCE_BLOCKED", None, "source_uri path is missing."
    path = Path(unquote(parsed.path)).expanduser()
    if not path.is_absolute():
        return "PREFLIGHT_SOURCE_BLOCKED", None, "source_uri must normalize to an absolute path."
    return None, _resolved(path), None


def _raw_metadata_block_reason(path: Path) -> str | None:
    raw_root = _resolved(IDS_METADATA_RAW_ROOT)
    resolved = _resolved(path)
    if resolved == raw_root or _is_relative_to(resolved, raw_root):
        return "IDS_MetaData raw metadata content is outside the Stage 018 Phase 2 read scope."
    return None


def _cost_class(count: int) -> str:
    if count <= 0:
        return "none"
    if count <= 10:
        return "low"
    if count <= 100:
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


def _record_for_file(path: Path) -> dict[str, Any]:
    stat = path.stat()
    extension = path.suffix.lower() or "NO_EXTENSION"
    return {
        "source_uri": path.as_uri(),
        "source_path": str(path),
        "basename": path.name,
        "extension": extension,
        "file_size": stat.st_size,
        "mtime": (
            datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z")
        ),
        "archive_candidate": extension in ARCHIVE_EXTENSIONS,
        "scanned_document_candidate": extension in SCANNED_HINT_EXTENSIONS,
        "embedding_candidate": extension in EMBEDDING_HINT_EXTENSIONS and extension not in ARCHIVE_EXTENSIONS,
        "unsupported_format": extension == "NO_EXTENSION" or extension not in SUPPORTED_EXTENSIONS,
    }


def _candidate_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    if path.is_dir():
        return sorted(item for item in path.iterdir() if item.is_file())
    return []


def _source_records_for_uri(source_uri: str | None) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    state, path, reason = _parse_source_uri(source_uri)
    if state is not None:
        return [], {"source_uri": source_uri, "state": state, "reason": reason}
    assert path is not None
    block_reason = _raw_metadata_block_reason(path)
    if block_reason is not None:
        return [], {"source_uri": source_uri, "state": "PREFLIGHT_SOURCE_BLOCKED", "reason": block_reason}
    try:
        if not path.exists():
            return [], {"source_uri": source_uri, "state": "PREFLIGHT_SOURCE_BLOCKED", "reason": "source path is absent."}
        if not (path.is_file() or path.is_dir()):
            return [], {"source_uri": source_uri, "state": "PREFLIGHT_SOURCE_BLOCKED", "reason": "source path must be a file or directory."}
        if not os.access(path, os.R_OK):
            return [], {"source_uri": source_uri, "state": "PREFLIGHT_SOURCE_BLOCKED", "reason": "source path is not readable."}
        records = [_record_for_file(candidate) for candidate in _candidate_files(path)]
    except OSError as exc:
        return [], {
            "source_uri": source_uri,
            "state": "PREFLIGHT_SOURCE_BLOCKED",
            "reason": f"Unable to read source metadata: {exc.__class__.__name__}",
        }
    return records, None


def _state_from_risks(risks: list[str], rejected_inputs: list[dict[str, Any]]) -> str:
    rejected_states = {item["state"] for item in rejected_inputs}
    if "PREFLIGHT_DRIVE_OFFLINE" in rejected_states:
        return "PREFLIGHT_DRIVE_OFFLINE"
    if "PREFLIGHT_SOURCE_BLOCKED" in rejected_states:
        return "PREFLIGHT_SOURCE_BLOCKED"
    if "PREFLIGHT_NOT_CONFIGURED" in rejected_states:
        return "PREFLIGHT_NOT_CONFIGURED"
    if risks:
        return "PREFLIGHT_REVIEW_REQUIRED"
    return "PREFLIGHT_READY"


def _priority_hint(overall_state: str, risks: list[str]) -> str:
    if overall_state in {"PREFLIGHT_SOURCE_BLOCKED", "PREFLIGHT_NOT_CONFIGURED", "PREFLIGHT_DRIVE_OFFLINE"}:
        return "blocked"
    if "PREFLIGHT_LARGE_BATCH" in risks:
        return "small_batch_first"
    if risks:
        return "manual_review_first"
    return "low_risk_first"


def evaluate_import_preflight(
    *,
    source_uris: list[str | None] | tuple[str | None, ...] | None,
    prechecked_at: str | None = None,
    drive_state: str = "online",
    available_space_bytes: int | None = None,
) -> dict[str, Any]:
    """Build Stage 018 preflight estimates from bounded filesystem metadata only."""

    prechecked_at = prechecked_at or _utc_now()
    normalized_drive_state = (drive_state or "unknown").strip().lower()
    if normalized_drive_state in OFFLINE_DRIVE_STATES:
        report = _base_report(
            prechecked_at=prechecked_at,
            drive_state=normalized_drive_state,
            records=[],
            source_root_count=0,
            rejected_inputs=[
                {
                    "source_uri": source_uris[0] if source_uris else None,
                    "state": "PREFLIGHT_DRIVE_OFFLINE",
                    "reason": "source drive is offline; preflight must fail closed before source metadata evaluation.",
                }
            ],
            available_space_bytes=available_space_bytes,
        )
        return report

    records: list[dict[str, Any]] = []
    rejected_inputs: list[dict[str, Any]] = []
    source_root_count = 0
    for source_uri in source_uris or []:
        source_records, rejected = _source_records_for_uri(source_uri)
        records.extend(source_records)
        if rejected is not None:
            rejected_inputs.append(rejected)
        else:
            source_root_count += 1
    if not source_uris:
        rejected_inputs.append(
            {"source_uri": None, "state": "PREFLIGHT_NOT_CONFIGURED", "reason": "source_uri is required."}
        )
    return _base_report(
        prechecked_at=prechecked_at,
        drive_state=normalized_drive_state,
        records=records,
        source_root_count=source_root_count,
        rejected_inputs=rejected_inputs,
        available_space_bytes=available_space_bytes,
    )


def _is_high_risk_record(record: dict[str, Any]) -> bool:
    return bool(
        record.get("archive_candidate")
        or record.get("scanned_document_candidate")
        or record.get("unsupported_format")
    )


def _chunk_records(records: list[dict[str, Any]], batch_size: int) -> list[list[dict[str, Any]]]:
    if not records:
        return []
    size = max(1, batch_size)
    return [records[index : index + size] for index in range(0, len(records), size)]


def _record_summary(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_uri": record["source_uri"],
        "source_path": record["source_path"],
        "basename": record["basename"],
        "extension": record["extension"],
        "file_size": record["file_size"],
        "risk_tags": [
            tag
            for tag, enabled in {
                "archive": record.get("archive_candidate", False),
                "scanned_document": record.get("scanned_document_candidate", False),
                "unsupported_format": record.get("unsupported_format", False),
            }.items()
            if enabled
        ],
    }


def build_operator_decision_plan(preflight_report: dict[str, Any], *, batch_size: int = 50) -> dict[str, Any]:
    """Create a serializable owner-decision plan without persisting or processing data."""

    records = list(preflight_report.get("file_records", []))
    high_risk_records = [record for record in records if _is_high_risk_record(record)]
    kept_records = [record for record in records if not _is_high_risk_record(record)]
    batches = _chunk_records(records, batch_size)
    serialized = json.dumps(preflight_report, ensure_ascii=False, sort_keys=True)
    no_persistence = dict(NO_PERSISTENCE_DELTAS)
    return {
        "schema_version": "ids.stage018.import_preflight.operator_decision.v1",
        "stage": "STAGE-018",
        "phase": "Phase 3",
        "acceptance_id": "ACC-STAGE-018",
        "entrance": ENTRANCE,
        "source_preflight_state": preflight_report.get("overall_state"),
        "supported_owner_actions": [
            "save_for_owner_review",
            "cancel_without_side_effects",
            "split_into_batches",
            "skip_high_risk_files",
        ],
        "save_contract": {
            "state": "PREFLIGHT_RESULT_SERIALIZABLE",
            "can_save_result": True,
            "persisted_by_helper": False,
            "serialized_bytes": len(serialized.encode("utf-8")),
            "owner_selected_path_required": True,
        },
        "cancel_contract": {"state": "PREFLIGHT_CANCEL_READY", **no_persistence},
        "batch_plan": {
            "can_split": len(batches) > 1,
            "batch_size": max(1, batch_size),
            "batch_count": len(batches),
            "batches": [
                {
                    "batch_index": index + 1,
                    "file_count": len(batch),
                    "total_size_bytes": sum(record["file_size"] for record in batch),
                    "files": [_record_summary(record) for record in batch],
                }
                for index, batch in enumerate(batches)
            ],
        },
        "skip_high_risk_plan": {
            "can_skip_high_risk_files": True,
            "high_risk_file_count": len(high_risk_records),
            "kept_file_count": len(kept_records),
            "skipped_files": [_record_summary(record) for record in high_risk_records],
            "kept_files": [_record_summary(record) for record in kept_records],
        },
        "no_persistence_deltas": no_persistence,
    }


def build_stage018_scenario_report(
    *,
    scenario_sources: dict[str, dict[str, Any]],
    prechecked_at: str | None = None,
    batch_size: int = 50,
) -> dict[str, Any]:
    """Validate Stage 018 preflight scenarios using explicit metadata-only inputs."""

    prechecked_at = prechecked_at or _utc_now()
    scenario_results: dict[str, dict[str, Any]] = {}
    for scenario_id in sorted(scenario_sources):
        scenario = scenario_sources[scenario_id]
        preflight = evaluate_import_preflight(
            source_uris=scenario.get("source_uris"),
            prechecked_at=prechecked_at,
            drive_state=scenario.get("drive_state", "online"),
            available_space_bytes=scenario.get("available_space_bytes"),
        )
        scenario_results[scenario_id] = {
            "scenario_id": scenario_id,
            "preflight": preflight,
            "operator_decision_plan": build_operator_decision_plan(preflight, batch_size=batch_size),
        }

    required_scenarios_covered = REQUIRED_PHASE3_SCENARIOS.issubset(set(scenario_results))
    report: dict[str, Any] = {
        "schema_version": "ids.stage018.import_preflight.scenario_validation.v1",
        "stage": "STAGE-018",
        "phase": "Phase 3",
        "acceptance_id": "ACC-STAGE-018",
        "entrance": ENTRANCE,
        "customer_visible": True,
        "validation_state": (
            "SCENARIO_VALIDATION_PASSED" if required_scenarios_covered else "SCENARIO_VALIDATION_PARTIAL"
        ),
        "prechecked_at": prechecked_at,
        "scenario_count": len(scenario_results),
        "required_scenarios": sorted(REQUIRED_PHASE3_SCENARIOS),
        "required_scenarios_covered": required_scenarios_covered,
        "scenario_results": scenario_results,
        "processing_guard": dict(PROCESSING_GUARD_ZEROES),
        "no_persistence_deltas": dict(NO_PERSISTENCE_DELTAS),
    }
    report.update(NO_SIDE_EFFECT_FLAGS)
    return report


def build_owner_feedback_summary(
    preflight_report: dict[str, Any],
    operator_decision_plan: dict[str, Any],
    *,
    feedback_at: str | None = None,
) -> dict[str, Any]:
    """Build Phase 4 owner-facing Chinese feedback without persisting artifacts."""

    feedback_at = feedback_at or _utc_now()
    risks = list(preflight_report.get("risk_items", []))
    report_sample = {
        "schema_version": preflight_report.get("schema_version"),
        "overall_state": preflight_report.get("overall_state"),
        "confirmation_status": preflight_report.get("confirmation_status"),
        "file_count_estimate": preflight_report.get("file_count_estimate", 0),
        "total_size_bytes_estimate": preflight_report.get("total_size_bytes_estimate", 0),
        "format_counts": preflight_report.get("format_counts", {}),
        "archive_candidate_count": preflight_report.get("archive_candidate_count", 0),
        "scanned_document_candidate_count": preflight_report.get("scanned_document_candidate_count", 0),
        "estimated_ocr_units": preflight_report.get("estimated_ocr_units", 0),
        "estimated_embedding_units": preflight_report.get("estimated_embedding_units", 0),
        "risk_items": risks,
        "cost_items": preflight_report.get("cost_items", {}),
        "priority_hint": preflight_report.get("priority_hint"),
    }
    failure_explanations = {
        "PREFLIGHT_NOT_CONFIGURED": "未配置导入来源；请先选择 owner 批准的本地 file:// 输入。",
        "PREFLIGHT_SOURCE_BLOCKED": "来源不可用或越过安全边界；系统不会继续读取或推断该来源。",
        "PREFLIGHT_DRIVE_OFFLINE": "移动硬盘或来源盘处于离线状态；请重新接入后再做预检。",
        "PREFLIGHT_ARCHIVE_PRESENT": "发现压缩包候选；需要 owner 复核后再决定是否单独处理。",
        "PREFLIGHT_SCANNED_DOCUMENT_PRESENT": "发现扫描件候选；OCR 工作量只是估算，不代表已经启动 OCR。",
        "PREFLIGHT_LARGE_BATCH": "文件数量较多；建议先分批处理并保留人工确认点。",
        "PREFLIGHT_UNSUPPORTED_FORMAT": "发现不支持格式；建议跳过或转交人工处理。",
        "PREFLIGHT_INSUFFICIENT_SPACE": "目标空间不足；请释放空间或缩小批次后再继续。",
        "PREFLIGHT_REVIEW_REQUIRED": "预检发现需要人工确认的风险项；确认前不会进入批量处理。",
    }
    confirmation_flow_log = [
        "步骤 1：系统展示预检报告样例，owner 先查看数量、体积、格式、风险和成本。",
        "步骤 2：owner 可以选择保存预检结果；当前 helper 只提供可序列化内容，不自动落盘。",
        "步骤 3：owner 可以选择取消；取消后 document/chunk/job/index/import/manifest/database 写入均保持 0。",
        "步骤 4：owner 可以选择分批处理；系统只生成 metadata batch plan，不启动解析或导入。",
        "步骤 5：owner 可以选择跳过高风险文件；压缩包、扫描件和不支持格式会进入跳过候选清单。",
    ]
    uncertainty_notes = [
        "文件数量、大小和格式来自显式 file:// 输入的文件系统 metadata；目录不递归扫描。",
        "OCR 和 Embedding 工作量是候选数量估算，不代表已经解析正文或启动处理任务。",
        "压缩包内部文件数、扫描件页数、图片清晰度和未来解析耗时仍需后续授权阶段确认。",
        "可用空间判断只比较当前传入的 available_space_bytes 和估算输入体积，不替代系统级容量审计。",
    ]
    rollback_steps = [
        "回滚 Phase 4 时只撤销 owner feedback helper、测试、closeout evidence 和治理指针。",
        "回滚不得移动、删除、覆盖或重写原始资料。",
        "回滚不得清理 /Users/linzezhang/Downloads/IDS_MetaData 或任何 runtime database/report/output。",
    ]
    no_persistence = dict(NO_PERSISTENCE_DELTAS)
    summary: dict[str, Any] = {
        "schema_version": "ids.stage018.import_preflight.owner_feedback.v1",
        "stage": "STAGE-018",
        "phase": "Phase 4",
        "acceptance_id": "ACC-STAGE-018",
        "entrance": ENTRANCE,
        "customer_visible": True,
        "feedback_at": feedback_at,
        "report_sample": report_sample,
        "risk_checklist": risks,
        "confirmation_flow_log": confirmation_flow_log,
        "failure_explanations": failure_explanations,
        "uncertainty_notes": uncertainty_notes,
        "rollback_steps": rollback_steps,
        "sample_persistence": {
            "can_serialize_for_owner_review": operator_decision_plan.get("save_contract", {}).get(
                "can_save_result", False
            ),
            "persisted_by_helper": False,
            "owner_selected_path_required": True,
        },
        "no_persistence_deltas": no_persistence,
    }
    summary.update(NO_SIDE_EFFECT_FLAGS)
    return summary


def _base_report(
    *,
    prechecked_at: str,
    drive_state: str,
    records: list[dict[str, Any]],
    source_root_count: int,
    rejected_inputs: list[dict[str, Any]],
    available_space_bytes: int | None,
) -> dict[str, Any]:
    format_counts: dict[str, int] = {}
    for record in records:
        format_counts[record["extension"]] = format_counts.get(record["extension"], 0) + 1
    total_size = sum(record["file_size"] for record in records)
    archive_count = sum(1 for record in records if record["archive_candidate"])
    scanned_count = sum(1 for record in records if record["scanned_document_candidate"])
    embedding_count = sum(1 for record in records if record["embedding_candidate"])
    unsupported_count = sum(1 for record in records if record["unsupported_format"])
    risks: list[str] = []
    if archive_count:
        risks.append("PREFLIGHT_ARCHIVE_PRESENT")
    if scanned_count:
        risks.append("PREFLIGHT_SCANNED_DOCUMENT_PRESENT")
    if len(records) > 100:
        risks.append("PREFLIGHT_LARGE_BATCH")
    if unsupported_count:
        risks.append("PREFLIGHT_UNSUPPORTED_FORMAT")
    if available_space_bytes is not None and total_size > available_space_bytes:
        risks.append("PREFLIGHT_INSUFFICIENT_SPACE")
    overall_state = _state_from_risks(risks, rejected_inputs)
    cost_items = {
        "local_scan_time_class": _cost_class(len(records)),
        "storage_pressure_class": _storage_pressure(total_size),
        "ocr_workload_class": _cost_class(scanned_count),
        "embedding_workload_class": _cost_class(embedding_count),
        "operator_review_class": _cost_class(len(risks) + len(rejected_inputs)),
        "batch_split_hint": "split_required" if "PREFLIGHT_LARGE_BATCH" in risks else "not_required",
    }
    report: dict[str, Any] = {
        "schema_version": "ids.stage018.import_preflight.v1",
        "stage": "STAGE-018",
        "phase": "Phase 2",
        "acceptance_id": "ACC-STAGE-018",
        "entrance": ENTRANCE,
        "customer_visible": True,
        "overall_state": overall_state,
        "safe_mode": overall_state != "PREFLIGHT_READY",
        "prechecked_at": prechecked_at,
        "drive_state": drive_state,
        "precheck_mode": "dry_run_metadata_only",
        "confirmation_required": True,
        "confirmation_status": overall_state,
        "source_root_count": source_root_count,
        "file_records": records,
        "file_count_estimate": len(records),
        "total_size_bytes_estimate": total_size,
        "format_counts": dict(sorted(format_counts.items())),
        "archive_candidate_count": archive_count,
        "scanned_document_candidate_count": scanned_count,
        "estimated_ocr_units": scanned_count,
        "estimated_embedding_units": embedding_count,
        "unsupported_format_count": unsupported_count,
        "risk_items": risks,
        "cost_items": cost_items,
        "priority_hint": _priority_hint(overall_state, risks),
        "rejected_inputs": rejected_inputs,
        "rejected_input_count": len(rejected_inputs),
        "error_count": len(rejected_inputs),
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
    report.update(NO_SIDE_EFFECT_FLAGS)
    return report


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a metadata-only Stage 018 import preflight report.")
    parser.add_argument(
        "--source-uri",
        action="append",
        dest="source_uris",
        help="Explicit file:// source root or file URI. Repeat for multiple approved roots.",
    )
    parser.add_argument("--prechecked-at", help="UTC preflight timestamp for deterministic runs.")
    parser.add_argument("--drive-state", default="online", help="online, offline, disconnected, missing, or unavailable.")
    parser.add_argument("--available-space-bytes", type=int, help="Optional future target-space estimate.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    report = evaluate_import_preflight(
        source_uris=args.source_uris,
        prechecked_at=args.prechecked_at,
        drive_state=args.drive_state,
        available_space_bytes=args.available_space_bytes,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
