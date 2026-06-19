from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .content_db import (
    external_reference_gap_summary,
    interpretation_items_for_run,
    pending_external_reference_gaps,
    queued_reports,
    report_timeline,
)
from .interpretation import (
    count_reference_items,
    interpretation_health_stats,
    reference_platforms,
)
from .quality_gates import build_quality_gate_status


def build_monitor_status(
    conn,
    data_dir: str | Path,
    analysis_mode: str,
    min_external_references: int = 5,
    min_external_platforms: int = 2,
    queue_limit: int = 12,
    quality_rules_file: str | Path | None = None,
) -> dict[str, Any]:
    latest_run = _latest_run(conn)
    latest_report_run = _latest_report_run(conn)
    report_run = latest_report_run or latest_run
    queue_items = queued_reports(conn, analysis_mode, limit=queue_limit)
    timeline_items = report_timeline(conn, limit=10)
    run_items: list[dict[str, Any]] = []
    if report_run:
        run_items = _decode_interpretation_metadata(
            interpretation_items_for_run(conn, str(report_run["run_id"]))
        )
    reference_count = count_reference_items(run_items)
    platforms = reference_platforms(run_items)
    health = interpretation_health_stats(run_items)
    gap_summary = external_reference_gap_summary(conn)
    gap_preview = pending_external_reference_gaps(conn, limit=10)
    report_path = str(report_run.get("report_path") or "") if report_run else ""
    status = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "overall_status": "unknown",
        "latest_run": latest_run or {},
        "latest_report_run": latest_report_run or {},
        "report": _report_status(report_path),
        "quality_gate": {
            "met": reference_count >= min_external_references
            and len(platforms) >= min_external_platforms,
            "external_reference_count": reference_count,
            "min_external_references": min_external_references,
            "external_platform_count": len(platforms),
            "min_external_platforms": min_external_platforms,
            "external_reference_deficit": max(0, min_external_references - reference_count),
            "external_platform_deficit": max(0, min_external_platforms - len(platforms)),
            "platforms": platforms,
        },
        "external_collection": health,
        "external_reference_gaps": {
            **gap_summary,
            "preview": [_gap_item_public(item) for item in gap_preview],
        },
        "queue": {
            "pending_count": _pending_count(conn, analysis_mode),
            "active_industry_rank": _active_industry_rank(queue_items),
            "active_industry_name": _active_industry_name(queue_items),
            "should_produce_early": bool(queue_items),
            "early_production_candidates": [_queue_item_public(item) for item in queue_items[:5]],
            "preview": [_queue_item_public(item) for item in queue_items],
        },
        "timeline": [_timeline_item_public(item) for item in timeline_items],
        "recent_errors": _recent_errors(Path(data_dir), latest_run),
        "alerts": [],
    }
    status["quality_gate_rules"] = build_quality_gate_status(
        rule_file=quality_rules_file,
        monitor_status=status,
    )
    status["alerts"] = _alerts(status)
    status["overall_status"] = "ok" if not status["alerts"] else "attention"
    return status


def write_monitor_status(
    conn,
    data_dir: str | Path,
    analysis_mode: str,
    min_external_references: int = 5,
    min_external_platforms: int = 2,
    quality_rules_file: str | Path | None = None,
) -> dict[str, Any]:
    status = build_monitor_status(
        conn,
        data_dir,
        analysis_mode,
        min_external_references=min_external_references,
        min_external_platforms=min_external_platforms,
        quality_rules_file=quality_rules_file,
    )
    path = Path(data_dir) / "monitor" / "latest_status.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    status["status_path"] = str(path)
    path.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    return status


def _latest_run(conn) -> dict[str, Any] | None:
    row = conn.execute(
        """
        SELECT *
        FROM pipeline_runs
        ORDER BY started_at DESC, run_id DESC
        LIMIT 1
        """
    ).fetchone()
    return dict(row) if row else None


def _latest_report_run(conn) -> dict[str, Any] | None:
    row = conn.execute(
        """
        SELECT *
        FROM pipeline_runs
        WHERE status = 'completed'
          AND report_path IS NOT NULL
          AND report_path != ''
        ORDER BY completed_at DESC, started_at DESC, run_id DESC
        LIMIT 1
        """
    ).fetchone()
    return dict(row) if row else None


def _pending_count(conn, analysis_mode: str) -> int:
    row = conn.execute(
        "SELECT COUNT(*) AS count FROM report_queue WHERE analysis_mode = ? AND status = 'pending'",
        (analysis_mode,),
    ).fetchone()
    return int(row["count"] if row else 0)


def _decode_interpretation_metadata(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    decoded = []
    for item in items:
        copied = dict(item)
        raw = copied.get("raw_metadata_json")
        if raw:
            try:
                copied["raw_metadata"] = json.loads(raw)
            except json.JSONDecodeError:
                copied["raw_metadata"] = {}
        decoded.append(copied)
    return decoded


def _report_status(report_path: str) -> dict[str, Any]:
    path = Path(report_path) if report_path else None
    exists = bool(path and path.exists())
    return {
        "path": report_path,
        "exists": exists,
        "size_bytes": path.stat().st_size if exists and path else 0,
        "html_path": str(path.with_suffix(".html")) if path else "",
        "markdown_path": str(path.with_suffix(".md")) if path else "",
        "dashboard_path": str(path.with_name(f"{path.stem}_dashboard.html")) if path else "",
    }


def _alerts(status: Mapping[str, Any]) -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []
    latest = status.get("latest_run") or {}
    latest_report = status.get("latest_report_run") or {}
    report = status.get("report") or {}
    quality = status.get("quality_gate") or {}
    external = status.get("external_collection") or {}
    gaps = status.get("external_reference_gaps") or {}
    if latest and latest.get("status") != "completed":
        alerts.append({"severity": "critical", "code": "latest_run_not_completed", "message": "最近一次流水线未完成。"})
    if latest_report and not report.get("exists"):
        alerts.append({"severity": "critical", "code": "report_missing", "message": "最近一次运行已完成，但报告文件不存在。"})
    if not quality.get("met"):
        alerts.append(
            {
                "severity": "warning",
                "code": "quality_gate_gap",
                "message": (
                    f"外部参考缺口 {quality.get('external_reference_deficit', 0)}，"
                    f"平台缺口 {quality.get('external_platform_deficit', 0)}。"
                ),
            }
        )
    if int(external.get("interpretation_missing_api_keys", 0) or 0) > 0:
        alerts.append({"severity": "warning", "code": "missing_search_api_keys", "message": "存在搜索 API key 缺口。"})
    if int(external.get("interpretation_auth_missing", 0) or 0) > 0:
        alerts.append({"severity": "warning", "code": "missing_platform_auth", "message": "存在未配置平台授权的来源。"})
    if int(external.get("interpretation_auth_parser_pending", 0) or 0) > 0:
        alerts.append({"severity": "info", "code": "platform_parser_pending", "message": "存在已授权但解析器尚未接入的平台。"})
    if int(gaps.get("pending_count", 0) or 0) > 0:
        alerts.append({"severity": "info", "code": "external_reference_gap_queue", "message": "外部参考缺口队列存在待处理项。"})
    if status.get("recent_errors"):
        alerts.append({"severity": "warning", "code": "recent_run_errors", "message": "最近运行日志中存在错误记录。"})
    return alerts


def _recent_errors(data_dir: Path, latest_run: Mapping[str, Any] | None) -> list[str]:
    if not latest_run:
        return []
    path = data_dir / "run_logs" / f"{latest_run.get('run_id')}.log"
    if not path.exists():
        return []
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return lines[-20:]


def _active_industry_rank(items: list[Mapping[str, Any]]) -> int:
    ranks = [int(item.get("industry_rank") or 999) for item in items if item.get("industry_rank") is not None]
    return min(ranks) if ranks else 0


def _active_industry_name(items: list[Mapping[str, Any]]) -> str:
    rank = _active_industry_rank(items)
    for item in items:
        if int(item.get("industry_rank") or 999) == rank:
            return str(item.get("primary_industry") or item.get("industry_bucket") or "")
    return ""


def _queue_item_public(item: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "document_id": item.get("document_id"),
        "title": item.get("title"),
        "source_name": item.get("source_name"),
        "industry": item.get("primary_industry") or item.get("industry_bucket"),
        "industry_rank": item.get("industry_rank"),
        "sort_time": item.get("sort_time") or item.get("published_date") or item.get("discovered_at"),
        "administrative_level": item.get("administrative_level"),
        "priority_score": item.get("priority_score"),
    }


def _timeline_item_public(item: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "event_type": item.get("event_type"),
        "created_at": item.get("created_at"),
        "document_id": item.get("document_id"),
        "title": item.get("title"),
        "source_name": item.get("source_name"),
        "report_path": item.get("report_path"),
        "industry": item.get("primary_industry"),
        "administrative_level": item.get("administrative_level"),
    }


def _gap_item_public(item: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "gap_id": item.get("gap_id"),
        "document_id": item.get("document_id"),
        "document_title": item.get("document_title"),
        "source_name": item.get("source_name"),
        "platform": item.get("platform"),
        "gap_type": item.get("gap_type"),
        "required_action": item.get("required_action"),
        "priority_score": item.get("priority_score"),
        "title": item.get("title"),
        "url": item.get("url"),
        "evidence_status": item.get("evidence_status"),
        "last_seen_run_id": item.get("last_seen_run_id"),
    }
