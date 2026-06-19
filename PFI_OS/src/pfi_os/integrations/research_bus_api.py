from __future__ import annotations

import hashlib
import json
import re
import shutil
import sqlite3
import subprocess
import tempfile
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from pfi_os.config import DATA_DIR
from pfi_os.integrations.external_systems import holding_columns
from pfi_os.integrations.holdings_book import (
    HOLDINGS_IMPORT_DIR,
    HOLDINGS_BOOK_PATH,
    canonical_holdings_frame,
    export_holdings_csv,
    load_holdings_book,
    save_holdings_book,
)
from pfi_os.integrations.independent_validation import run_independent_validation
from pfi_os.integrations.system_orchestrator import (
    orchestrate_child_system,
    orchestration_runs_frame,
    register_default_systems,
    sync_default_system_artifacts,
    system_artifacts_frame,
    system_registry_frame,
)
from pfi_os.integrations.research_bus import (
    benchmark_for_market,
    extract_symbols,
    holding_symbol_mappings_frame,
    load_default_portfolio_transactions,
    infer_market,
    initialize_research_bus,
    research_bus_db_path,
    sync_all_research_bus,
    sync_holding_symbol_mappings_to_bus,
    sync_holdings_to_bus,
    sync_industry_reports_to_bus,
    sync_portfolio_transactions_to_bus,
    sync_pfi_os_results_to_bus,
)


API_STATUSES = {"Pending", "Processing", "Completed", "Failed", "Skipped"}
CHAT_CLASSIFICATIONS = {"validation_task", "holding_update", "sync_request", "independent_validation", "orchestration", "system_update", "general_note"}
CHAT_DROPBOX_DIR = DATA_DIR / "researchBus" / "chatInbox"
CHAT_DROPBOX_PROCESSED_DIR = CHAT_DROPBOX_DIR / "processed"
CHAT_DROPBOX_FAILED_DIR = CHAT_DROPBOX_DIR / "failed"
CHAT_DROPBOX_SUFFIXES = {".txt", ".md", ".json"}
STRUCTURED_ATTACHMENT_SUFFIXES = {".csv", ".json", ".xlsx", ".xls", ".txt", ".md"}
UNSTRUCTURED_MEDIA_SUFFIXES = {".png", ".jpg", ".jpeg", ".heic", ".webp", ".mp4", ".mov", ".m4v", ".avi"}
CONFIRMED_HOLDING_CANDIDATES_PATH = HOLDINGS_IMPORT_DIR / "confirmed_holding_candidates.csv"
CONFIRMED_PORTFOLIO_TRANSACTIONS_PATH = HOLDINGS_IMPORT_DIR / "confirmed_portfolio_transactions.csv"


@dataclass(frozen=True)
class BusApiRequest:
    request_id: str
    source_system: str
    target_system: str
    request_type: str
    status: str
    priority: int
    payload: dict[str, Any]
    response: dict[str, Any]
    error_message: str
    created_at: str
    updated_at: str
    processed_at: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["payload_json"] = payload.pop("payload")
        payload["response_json"] = payload.pop("response")
        return payload


def submit_bus_request(
    request_type: str,
    payload: dict[str, Any] | None = None,
    *,
    source_system: str = "ExternalChat",
    target_system: str = "ResearchBus",
    priority: int = 5,
    db_path: Path | str | None = None,
) -> BusApiRequest:
    target_db = initialize_research_bus(db_path)
    now = _now()
    if payload is not None and not isinstance(payload, dict):
        raise ValueError("Bus request payload must be a JSON object.")
    clean_payload = payload or {}
    request_id = _stable_id("busRequest", source_system, target_system, request_type, _json_dumps(clean_payload), now)
    request = BusApiRequest(
        request_id=request_id,
        source_system=source_system,
        target_system=target_system,
        request_type=request_type,
        status="Pending",
        priority=int(priority),
        payload=clean_payload,
        response={},
        error_message="",
        created_at=now,
        updated_at=now,
        processed_at="",
    )
    with _connect(target_db) as conn:
        _upsert_request(conn, request)
        _write_outbox(
            conn,
            source_system="ResearchBus",
            target_system=target_system,
            message_type="ApiRequestSubmitted",
            payload={"request_id": request_id, "request_type": request_type, "source_system": source_system},
        )
    return request


def submit_chat_input(
    content_text: str,
    *,
    source_system: str = "ExternalChat",
    author: str = "",
    channel: str = "chat",
    attachments: list[dict[str, Any]] | None = None,
    db_path: Path | str | None = None,
) -> dict[str, Any]:
    target_db = initialize_research_bus(db_path)
    text = str(content_text or "").strip()
    if not text:
        raise ValueError("content_text cannot be empty.")
    classification = classify_chat_input(text)
    payload = {"content_text": text, "attachments": attachments or [], "classification": classification}
    target_system, request_type = _route_chat_input(classification, text)
    request = submit_bus_request(
        request_type=request_type,
        payload=payload,
        source_system=source_system,
        target_system=target_system,
        db_path=target_db,
    )
    input_id = _stable_id("chatInput", source_system, channel, author, text, request.request_id)
    now = _now()
    created_tasks = 0
    with _connect(target_db) as conn:
        conn.execute(
            """
            INSERT INTO bus_chat_inputs(
                input_id, source_system, author, channel, content_text, attachments_json,
                classification, linked_request_id, status, payload_json, created_at, processed_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(input_id) DO UPDATE SET
                status=excluded.status,
                payload_json=excluded.payload_json,
                processed_at=excluded.processed_at
            """,
            (
                input_id,
                source_system,
                author,
                channel,
                text,
                _json_dumps(attachments or []),
                classification,
                request.request_id,
                "Pending",
                _json_dumps(payload),
                now,
                "",
            ),
        )
        if classification == "validation_task":
            created_tasks = _insert_validation_tasks_from_chat(conn, input_id, text, source_system)
        _write_outbox(
            conn,
            source_system="ResearchBus",
            target_system=target_system,
            message_type="ChatInputReceived",
            payload={"input_id": input_id, "classification": classification, "created_validation_tasks": created_tasks},
        )
    return {
        "input_id": input_id,
        "classification": classification,
        "linked_request_id": request.request_id,
        "target_system": target_system,
        "request_type": request_type,
        "created_validation_tasks": created_tasks,
    }


def submit_webhook_payload(
    payload: dict[str, Any] | str,
    *,
    source_system: str = "LocalWebhook",
    db_path: Path | str | None = None,
) -> dict[str, Any]:
    if isinstance(payload, str):
        return {"kind": "chat", **submit_chat_input(payload, source_system=source_system, channel="webhook", db_path=db_path)}
    if not isinstance(payload, dict):
        raise ValueError("Webhook payload must be a JSON object or text string.")
    request_type = str(payload.get("request_type") or payload.get("type") or "").strip()
    if request_type:
        request_payload = payload.get("payload", {})
        if not isinstance(request_payload, dict):
            request_payload = {"value": request_payload}
        request = submit_bus_request(
            request_type,
            request_payload,
            source_system=str(payload.get("source_system") or source_system),
            target_system=str(payload.get("target_system") or "ResearchBus"),
            priority=int(payload.get("priority") or 5),
            db_path=db_path,
        )
        return {"kind": "request", "request": request.to_dict()}
    text = str(payload.get("content_text") or payload.get("text") or payload.get("message") or "").strip()
    if not text:
        raise ValueError("Webhook payload must include content_text, text, message, or request_type.")
    attachments = payload.get("attachments", [])
    if not isinstance(attachments, list):
        attachments = []
    return {
        "kind": "chat",
        **submit_chat_input(
            text,
            source_system=str(payload.get("source_system") or source_system),
            author=str(payload.get("author") or ""),
            channel=str(payload.get("channel") or "webhook"),
            attachments=attachments,
            db_path=db_path,
        ),
    }


def process_chat_dropbox(
    inbox_dir: Path | str | None = None,
    *,
    db_path: Path | str | None = None,
    default_source_system: str = "ChatDropbox",
    min_age_seconds: float = 1.0,
    limit: int = 100,
) -> dict[str, Any]:
    inbox = Path(inbox_dir).expanduser() if inbox_dir is not None else CHAT_DROPBOX_DIR
    inbox.mkdir(parents=True, exist_ok=True)
    processed_dir = inbox / "processed"
    failed_dir = inbox / "failed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    failed_dir.mkdir(parents=True, exist_ok=True)

    processed: list[dict[str, Any]] = []
    failed: list[dict[str, Any]] = []
    now_ts = time.time()
    candidates = [
        path
        for path in sorted(inbox.iterdir())
        if path.is_file() and not path.name.startswith(".") and path.suffix.lower() in CHAT_DROPBOX_SUFFIXES
    ]
    for path in candidates[: max(0, int(limit))]:
        try:
            if min_age_seconds > 0 and now_ts - path.stat().st_mtime < min_age_seconds:
                continue
            payload = _chat_payload_from_file(path, default_source_system)
            result = submit_chat_input(
                payload["content_text"],
                source_system=payload["source_system"],
                author=payload["author"],
                channel=payload["channel"],
                attachments=payload["attachments"],
                db_path=db_path,
            )
            moved_to = _move_to_unique_dir(path, processed_dir)
            processed.append({"path": str(path), "moved_to": str(moved_to), **result})
        except Exception as exc:
            moved_to = _move_to_unique_dir(path, failed_dir)
            error_path = failed_dir / f"{moved_to.name}.error.json"
            error_path.write_text(_json_dumps({"source_path": str(path), "moved_to": str(moved_to), "error": str(exc)}), encoding="utf-8")
            failed.append({"path": str(path), "moved_to": str(moved_to), "error": str(exc), "error_path": str(error_path)})
    heartbeat_system(
        "ResearchBus",
        status="Ready" if not failed else "Warn",
        capabilities=["chat_dropbox"],
        payload={"processed_files": len(processed), "failed_files": len(failed), "inbox_dir": str(inbox)},
        db_path=db_path,
    )
    return {
        "inbox_dir": str(inbox),
        "processed_count": len(processed),
        "failed_count": len(failed),
        "processed": processed,
        "failed": failed,
    }


def process_pending_bus_requests(
    *,
    system_name: str = "ResearchBus",
    limit: int = 25,
    db_path: Path | str | None = None,
) -> dict[str, Any]:
    target_db = initialize_research_bus(db_path)
    requests = pending_bus_requests_frame(db_path=target_db, target_system=system_name, limit=limit)
    processed = 0
    failed = 0
    results: list[dict[str, Any]] = []
    for row in requests.to_dict("records"):
        request_id = str(row["request_id"])
        request_type = str(row["request_type"])
        payload = _loads(row.get("payload_json"), {})
        _mark_request_status(request_id, "Processing", db_path=target_db)
        try:
            response = _handle_request(request_type, payload, target_db, request_context=dict(row))
            complete_bus_request(request_id, response=response, db_path=target_db)
            processed += 1
            results.append({"request_id": request_id, "status": "Completed", "request_type": request_type, "response": response})
        except Exception as exc:
            complete_bus_request(request_id, response={}, error_message=str(exc), db_path=target_db)
            failed += 1
            results.append({"request_id": request_id, "status": "Failed", "request_type": request_type, "error": str(exc)})
    heartbeat_system(system_name, status="Ready", db_path=target_db, payload={"processed": processed, "failed": failed})
    return {"system_name": system_name, "processed": processed, "failed": failed, "results": results}


def complete_bus_request(
    request_id: str,
    *,
    response: dict[str, Any] | None = None,
    error_message: str = "",
    db_path: Path | str | None = None,
) -> None:
    target_db = initialize_research_bus(db_path)
    status = "Failed" if error_message else "Completed"
    now = _now()
    with _connect(target_db) as conn:
        conn.execute(
            """
            UPDATE bus_api_requests
            SET status=?, response_json=?, error_message=?, updated_at=?, processed_at=?
            WHERE request_id=?
            """,
            (status, _json_dumps(response or {}), error_message, now, now, request_id),
        )
        conn.execute(
            """
            UPDATE bus_chat_inputs
            SET status=?, processed_at=?
            WHERE linked_request_id=? AND status IN ('Pending', 'Processing')
            """,
            (status, now, request_id),
        )
        _write_outbox(
            conn,
            source_system="ResearchBus",
            target_system=_request_target(conn, request_id),
            message_type="ApiRequestCompleted" if not error_message else "ApiRequestFailed",
            payload={"request_id": request_id, "status": status, "error_message": error_message, "response": response or {}},
        )


def heartbeat_system(
    system_name: str,
    *,
    status: str = "Ready",
    capabilities: list[str] | None = None,
    payload: dict[str, Any] | None = None,
    db_path: Path | str | None = None,
) -> None:
    target_db = initialize_research_bus(db_path)
    with _connect(target_db) as conn:
        conn.execute(
            """
            INSERT INTO bus_heartbeats(system_name, status, capabilities_json, payload_json, last_seen_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(system_name) DO UPDATE SET
                status=excluded.status,
                capabilities_json=excluded.capabilities_json,
                payload_json=excluded.payload_json,
                last_seen_at=excluded.last_seen_at
            """,
            (system_name, status, _json_dumps(capabilities or []), _json_dumps(payload or {}), _now()),
        )


def pending_bus_requests_frame(
    *,
    db_path: Path | str | None = None,
    target_system: str = "ResearchBus",
    limit: int = 100,
) -> pd.DataFrame:
    target_db = initialize_research_bus(db_path)
    targets = [target_system, "ResearchBus", "All", "*"] if target_system != "ResearchBus" else [target_system, "All", "*"]
    placeholders = ",".join("?" for _ in targets)
    with _connect(target_db) as conn:
        rows = conn.execute(
            f"""
            SELECT *
            FROM bus_api_requests
            WHERE status='Pending' AND target_system IN ({placeholders})
            ORDER BY priority ASC, created_at ASC
            LIMIT ?
            """,
            (*targets, int(limit)),
        ).fetchall()
    return pd.DataFrame([dict(row) for row in rows])


def bus_api_requests_frame(db_path: Path | str | None = None, limit: int = 500) -> pd.DataFrame:
    target_db = initialize_research_bus(db_path)
    with _connect(target_db) as conn:
        rows = conn.execute("SELECT * FROM bus_api_requests ORDER BY updated_at DESC LIMIT ?", (int(limit),)).fetchall()
    return pd.DataFrame([dict(row) for row in rows])


def bus_chat_inputs_frame(db_path: Path | str | None = None, limit: int = 500) -> pd.DataFrame:
    target_db = initialize_research_bus(db_path)
    with _connect(target_db) as conn:
        rows = conn.execute("SELECT * FROM bus_chat_inputs ORDER BY created_at DESC LIMIT ?", (int(limit),)).fetchall()
    return pd.DataFrame([dict(row) for row in rows])


def workflow_inputs_frame(db_path: Path | str | None = None, limit: int = 500) -> pd.DataFrame:
    target_db = initialize_research_bus(db_path)
    columns = [
        "workflow_input_id",
        "input_type",
        "source_system",
        "author",
        "channel",
        "raw_input",
        "classification",
        "linked_request_id",
        "status",
        "created_at",
        "processed_at",
        "attachments_json",
        "payload_json",
    ]
    with _connect(target_db) as conn:
        chat_rows = conn.execute(
            """
            SELECT
                input_id AS workflow_input_id,
                'chat' AS input_type,
                source_system,
                author,
                channel,
                content_text AS raw_input,
                classification,
                linked_request_id,
                status,
                created_at,
                processed_at,
                attachments_json,
                payload_json
            FROM bus_chat_inputs
            """
        ).fetchall()
        request_rows = conn.execute(
            """
            SELECT
                request_id AS workflow_input_id,
                'api_request' AS input_type,
                source_system,
                '' AS author,
                'api' AS channel,
                request_type AS raw_input,
                request_type AS classification,
                request_id AS linked_request_id,
                status,
                created_at,
                processed_at,
                '[]' AS attachments_json,
                payload_json
            FROM bus_api_requests
            WHERE request_id NOT IN (
                SELECT linked_request_id FROM bus_chat_inputs WHERE linked_request_id != ''
            )
            """
        ).fetchall()
    rows = [dict(row) for row in [*chat_rows, *request_rows]]
    if not rows:
        return pd.DataFrame(columns=columns)
    frame = pd.DataFrame(rows)
    for column in columns:
        if column not in frame.columns:
            frame[column] = ""
    return frame.sort_values(["created_at", "workflow_input_id"], ascending=[False, True]).head(int(limit))[columns].reset_index(drop=True)


def bus_heartbeats_frame(db_path: Path | str | None = None) -> pd.DataFrame:
    target_db = initialize_research_bus(db_path)
    with _connect(target_db) as conn:
        rows = conn.execute("SELECT * FROM bus_heartbeats ORDER BY last_seen_at DESC").fetchall()
    return pd.DataFrame([dict(row) for row in rows])


def research_bus_health_summary(
    *,
    db_path: Path | str | None = None,
    heartbeat_max_age_seconds: int = 180,
    inbox_dir: Path | str | None = None,
) -> dict[str, Any]:
    target_db = initialize_research_bus(db_path)
    inbox = Path(inbox_dir).expanduser() if inbox_dir is not None else CHAT_DROPBOX_DIR
    with _connect(target_db) as conn:
        request_rows = conn.execute("SELECT status, COUNT(*) AS count FROM bus_api_requests GROUP BY status").fetchall()
        chat_rows = conn.execute("SELECT classification, COUNT(*) AS count FROM bus_chat_inputs GROUP BY classification").fetchall()
        failed_requests = conn.execute("SELECT COUNT(*) AS count FROM bus_api_requests WHERE status='Failed'").fetchone()["count"]
        pending_requests = conn.execute("SELECT COUNT(*) AS count FROM bus_api_requests WHERE status='Pending'").fetchone()["count"]
        heartbeats = conn.execute("SELECT system_name, status, capabilities_json, payload_json, last_seen_at FROM bus_heartbeats").fetchall()
    now_ts = time.time()
    heartbeat_items = []
    stale_count = 0
    for row in heartbeats:
        age_seconds = _seconds_since(str(row["last_seen_at"]), now_ts)
        is_stale = age_seconds > heartbeat_max_age_seconds
        stale_count += 1 if is_stale else 0
        heartbeat_items.append(
            {
                "system_name": row["system_name"],
                "status": row["status"],
                "age_seconds": round(age_seconds, 2),
                "is_stale": is_stale,
                "capabilities": _loads(row["capabilities_json"], []),
                "payload": _loads(row["payload_json"], {}),
                "last_seen_at": row["last_seen_at"],
            }
        )
    inbox_pending = 0
    if inbox.exists():
        inbox_pending = sum(
            1
            for path in inbox.iterdir()
            if path.is_file() and not path.name.startswith(".") and path.suffix.lower() in CHAT_DROPBOX_SUFFIXES
        )
    status = "Ready"
    if failed_requests or stale_count:
        status = "Warn"
    return {
        "status": status,
        "db_path": str(target_db),
        "request_counts": {str(row["status"]): int(row["count"]) for row in request_rows},
        "chat_classification_counts": {str(row["classification"]): int(row["count"]) for row in chat_rows},
        "pending_request_count": int(pending_requests),
        "failed_request_count": int(failed_requests),
        "heartbeat_stale_count": int(stale_count),
        "heartbeats": heartbeat_items,
        "chat_inbox_dir": str(inbox),
        "chat_inbox_pending_files": int(inbox_pending),
    }


def classify_chat_input(text: str) -> str:
    lowered = str(text or "").lower()
    scale_terms = ["百万", "千万", "亿", "million", "billion", "大数据", "数据测试", "scale test", "stress test"]
    validation_terms = ["独立验证", "independent validation", "manifest", "分片", "模拟", "校验", "rows"]
    orchestration_terms = ["fifa", "tab", "世界杯", "政府文件", "政策系统", "政策解读", "source authority", "子系统", "母系统", "唤醒"]
    run_terms = ["运行", "启动", "检查", "体检", "health", "status", "orchestrate", "run", "start"]
    if any(keyword in lowered for keyword in orchestration_terms) and any(keyword in lowered for keyword in run_terms):
        return "orchestration"
    if any(keyword in lowered for keyword in validation_terms) and any(keyword in lowered for keyword in scale_terms):
        return "independent_validation"
    if any(keyword in lowered for keyword in ["独立验证", "independent validation", "亿", "billion", "manifest", "分片"]):
        return "independent_validation"
    if any(keyword in lowered for keyword in ["持仓", "position", "holding", "仓位", "市值", "份额"]):
        return "holding_update"
    if any(keyword in lowered for keyword in ["同步", "sync", "刷新", "互通"]):
        return "sync_request"
    if any(keyword in lowered for keyword in ["优化", "完善", "修改", "修复", "bug", "报错", "新增功能", "增加功能", "更新功能", "system update", "feature request"]):
        return "system_update"
    if any(keyword in lowered for keyword in ["验证", "回测", "pfi_os", "策略", "信号", "rsi", "macd", "均线", "估值"]):
        return "validation_task"
    return "general_note"


def _handle_request(
    request_type: str,
    payload: dict[str, Any],
    db_path: Path,
    *,
    request_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if request_type == "sync_all":
        return sync_all_research_bus(db_path=db_path).to_dict()
    if request_type == "sync_industry_reports":
        return sync_industry_reports_to_bus(db_path=db_path, push_validation_queue=True).to_dict()
    if request_type == "sync_pfi_os_results":
        return sync_pfi_os_results_to_bus(db_path=db_path).to_dict()
    if request_type == "sync_holdings":
        return sync_holdings_to_bus(db_path=db_path).to_dict()
    if request_type == "sync_holding_symbol_mappings":
        return sync_holding_symbol_mappings_to_bus(db_path=db_path).to_dict()
    if request_type == "sync_system_registry":
        registry = register_default_systems(db_path)
        artifacts = sync_default_system_artifacts(db_path)
        return {"status": "Synced", **registry, **artifacts}
    if request_type == "sync_system_artifacts":
        return {"status": "Synced", **sync_default_system_artifacts(db_path)}
    if request_type == "orchestrate_system":
        return _run_orchestration_from_payload(payload, db_path, request_context=request_context or {}).to_dict()
    if request_type == "pull_system_registry":
        limit = int(payload.get("limit") or 500)
        frame = system_registry_frame(db_path).head(limit)
        return {"status": "Pulled", "system_count": int(len(frame)), "systems": frame.to_dict("records")}
    if request_type == "pull_system_artifacts":
        limit = int(payload.get("limit") or 500)
        frame = system_artifacts_frame(db_path, limit=limit)
        return {"status": "Pulled", "artifact_count": int(len(frame)), "artifacts": frame.to_dict("records")}
    if request_type == "pull_orchestration_runs":
        limit = int(payload.get("limit") or 500)
        frame = orchestration_runs_frame(db_path, limit=limit)
        return {"status": "Pulled", "run_count": int(len(frame)), "runs": frame.to_dict("records")}
    if request_type == "pull_holding_symbol_mappings":
        limit = int(payload.get("limit") or 500)
        frame = holding_symbol_mappings_frame(db_path).head(limit)
        return {
            "status": "Pulled",
            "holding_symbol_mapping_count": int(len(frame)),
            "holding_symbol_mappings": frame.to_dict("records"),
        }
    if request_type == "independent_validation_dry_run":
        result = _run_independent_validation_from_payload(payload, db_path, mode="dry_run")
        return result.to_dict()
    if request_type == "independent_validation_checksum":
        result = _run_independent_validation_from_payload(payload, db_path, mode="checksum")
        return result.to_dict()
    if request_type == "holding_update_candidate":
        return _record_holding_update_candidate(payload, db_path, request_context=request_context or {})
    if request_type == "confirm_holding_update_candidate":
        return confirm_holding_update_candidate(
            str(payload.get("candidate_id") or ""),
            db_path=db_path,
            holding_import_path=payload.get("holding_import_path"),
            transaction_import_path=payload.get("transaction_import_path"),
            holdings_book_path=payload.get("holdings_book_path"),
        )
    if request_type in {"record_note", "chat_general_note"}:
        return {"status": "Recorded", "payload": payload}
    if request_type == "system_update_request":
        return {"status": "QueuedForImplementationReview", "payload": payload}
    if request_type == "validation_task_from_chat":
        return {"status": "Queued", "payload": payload}
    raise ValueError(f"Unsupported request_type: {request_type}")


def _record_holding_update_candidate(
    payload: dict[str, Any],
    db_path: Path,
    *,
    request_context: dict[str, Any],
) -> dict[str, Any]:
    now = _now()
    content_text = str(payload.get("content_text") or payload.get("text") or "").strip()
    attachments = payload.get("attachments") if isinstance(payload.get("attachments"), list) else []
    request_id = str(request_context.get("request_id") or "")
    source_system = str(request_context.get("source_system") or payload.get("source_system") or "")
    enriched_payload, parser_reports = _enrich_payload_from_attachments(payload, attachments)
    structured_holding_count = len(_structured_rows(enriched_payload, "holdings", "positions"))
    structured_transaction_count = len(_structured_rows(enriched_payload, "portfolio_transactions", "transactions", "trades"))
    extracted_symbols = sorted(
        {
            *extract_symbols(content_text),
            *[
                str(row.get("symbol", "")).strip()
                for row in [
                    *_structured_rows(enriched_payload, "holdings", "positions"),
                    *_structured_rows(enriched_payload, "portfolio_transactions", "transactions", "trades"),
                ]
                if str(row.get("symbol", "")).strip()
            ],
            *[
                str(symbol).strip()
                for report in parser_reports
                for symbol in (report.get("extracted_symbols", []) if isinstance(report.get("extracted_symbols", []), list) else [])
                if str(symbol).strip()
            ],
        }
    )
    account = str(payload.get("account") or ("支付宝基金账户" if "支付宝" in content_text else "")).strip()
    candidate_type = "holding_structured_attachment" if structured_holding_count or structured_transaction_count else ("holding_attachment" if attachments else "holding_text")
    candidate_id = _stable_id("holdingCandidate", request_id or source_system, content_text, _json_dumps(attachments))
    with _connect(db_path) as conn:
        chat_row = conn.execute(
            "SELECT input_id FROM bus_chat_inputs WHERE linked_request_id=? ORDER BY created_at DESC LIMIT 1",
            (request_id,),
        ).fetchone()
        chat_input_id = str(chat_row["input_id"]) if chat_row else ""
        conn.execute(
            """
            INSERT INTO holding_update_candidates(
                candidate_id, source_system, account, candidate_type, status, quality_status,
                content_text, attachments_json, extracted_symbols_json, source_request_id,
                source_chat_input_id, payload_json, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(candidate_id) DO UPDATE SET
                status=excluded.status,
                quality_status=excluded.quality_status,
                content_text=excluded.content_text,
                attachments_json=excluded.attachments_json,
                extracted_symbols_json=excluded.extracted_symbols_json,
                source_request_id=excluded.source_request_id,
                source_chat_input_id=excluded.source_chat_input_id,
                payload_json=excluded.payload_json,
                updated_at=excluded.updated_at
            """,
            (
                candidate_id,
                source_system,
                account,
                candidate_type,
                "PendingReview",
                "Candidate",
                content_text,
                _json_dumps(attachments),
                _json_dumps(extracted_symbols),
                request_id,
                chat_input_id,
                _json_dumps(enriched_payload),
                now,
                now,
            ),
        )
        if chat_input_id:
            conn.execute(
                "UPDATE bus_chat_inputs SET status=?, processed_at=? WHERE input_id=?",
                ("PendingReview", now, chat_input_id),
            )
    return {
        "status": "QueuedForManualReview",
        "candidate_id": candidate_id,
        "candidate_type": candidate_type,
        "attachment_count": len(attachments),
        "structured_holding_count": structured_holding_count,
        "structured_transaction_count": structured_transaction_count,
        "parser_reports": parser_reports,
        "extracted_symbols": extracted_symbols,
        "message": "持仓更新已进入候选复核队列，未写入正式持仓。",
    }


def _enrich_payload_from_attachments(payload: dict[str, Any], attachments: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    enriched = dict(payload)
    parser_reports: list[dict[str, Any]] = []
    holdings: list[dict[str, Any]] = list(_structured_rows(enriched, "holdings", "positions"))
    transactions: list[dict[str, Any]] = list(_structured_rows(enriched, "portfolio_transactions", "transactions", "trades"))
    for attachment in attachments:
        parsed, report = _parse_holding_attachment(attachment)
        parser_reports.append(report)
        holdings.extend(parsed.get("holdings", []))
        transactions.extend(parsed.get("portfolio_transactions", []))
    if holdings:
        enriched["holdings"] = holdings
    if transactions:
        enriched["portfolio_transactions"] = transactions
    if parser_reports:
        enriched["attachment_parser_reports"] = parser_reports
    return enriched, parser_reports


def _parse_holding_attachment(attachment: dict[str, Any]) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    path = _attachment_path(attachment)
    report = {
        "path": str(path) if path else "",
        "name": str(attachment.get("name") or (path.name if path else "")),
        "status": "Skipped",
        "parser": "",
        "holding_count": 0,
        "transaction_count": 0,
        "message": "",
    }
    if path is None:
        report.update({"status": "MissingPath", "message": "附件缺少 path。"})
        return {"holdings": [], "portfolio_transactions": []}, report
    if not path.exists() or not path.is_file():
        report.update({"status": "MissingFile", "message": "附件文件不存在或不是文件。"})
        return {"holdings": [], "portfolio_transactions": []}, report
    suffix = path.suffix.lower()
    if suffix in UNSTRUCTURED_MEDIA_SUFFIXES:
        return _parse_media_attachment(path, report)
    if suffix not in STRUCTURED_ATTACHMENT_SUFFIXES:
        report.update({"status": "UnsupportedFile", "message": f"暂不支持的附件格式：{suffix}"})
        return {"holdings": [], "portfolio_transactions": []}, report
    try:
        parsed = _parse_structured_attachment(path)
    except Exception as exc:
        report.update({"status": "ParseFailed", "message": str(exc)})
        return {"holdings": [], "portfolio_transactions": []}, report
    report.update(
        {
            "status": "Parsed" if parsed["holdings"] or parsed["portfolio_transactions"] else "NoStructuredRows",
            "parser": suffix.lstrip(".") or "text",
            "holding_count": len(parsed["holdings"]),
            "transaction_count": len(parsed["portfolio_transactions"]),
            "message": "已解析结构化候选。" if parsed["holdings"] or parsed["portfolio_transactions"] else "文件已读取，但未识别出持仓或交易字段。",
        }
    )
    return parsed, report


def _parse_structured_attachment(path: Path) -> dict[str, list[dict[str, Any]]]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        return _structured_payload_from_json(payload)
    if suffix in {".txt", ".md"}:
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            return {"holdings": [], "portfolio_transactions": []}
        if text.startswith("{") or text.startswith("["):
            return _structured_payload_from_json(json.loads(text))
        return {"holdings": [], "portfolio_transactions": []}
    if suffix == ".csv":
        frame = pd.read_csv(path)
        return _structured_payload_from_frame(frame)
    if suffix in {".xlsx", ".xls"}:
        frame = pd.read_excel(path)
        return _structured_payload_from_frame(frame)
    return {"holdings": [], "portfolio_transactions": []}


def _parse_media_attachment(path: Path, report: dict[str, Any]) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix in {".mp4", ".mov", ".m4v", ".avi"}:
        return _parse_video_attachment(path, report)
    return _parse_image_attachment(path, report)


def _parse_image_attachment(path: Path, report: dict[str, Any]) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    runtime = _image_ocr_runtime_status()
    if not runtime["available"]:
        report.update(
            {
                "status": "NeedsRuntime",
                "parser": "image_ocr",
                "runtime": runtime,
                "message": "图片候选需要 OCR 运行环境；当前缺少依赖，已保留为候选复核。",
            }
        )
        return {"holdings": [], "portfolio_transactions": []}, report
    text = _ocr_image_text(path)
    parsed = _structured_payload_from_text(text)
    report.update(_media_report_fields(text, parsed, parser="image_ocr", runtime=runtime))
    return parsed, report


def _parse_video_attachment(path: Path, report: dict[str, Any]) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    runtime = _video_ocr_runtime_status()
    if not runtime["available"]:
        report.update(
            {
                "status": "NeedsRuntime",
                "parser": "video_frame_ocr",
                "runtime": runtime,
                "message": "视频候选需要 ffmpeg 和 OCR 运行环境；当前缺少依赖，已保留为候选复核。",
            }
        )
        return {"holdings": [], "portfolio_transactions": []}, report
    texts: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        pattern = str(Path(tmp) / "frame_%03d.png")
        command = [
            str(shutil.which("ffmpeg")),
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(path),
            "-vf",
            "fps=1/10",
            "-frames:v",
            "3",
            pattern,
        ]
        try:
            subprocess.run(command, check=True, capture_output=True, text=True, timeout=60)
        except Exception as exc:
            report.update(
                {
                    "status": "ParseFailed",
                    "parser": "video_frame_ocr",
                    "runtime": runtime,
                    "message": f"视频抽帧失败：{exc}",
                }
            )
            return {"holdings": [], "portfolio_transactions": []}, report
        for frame_path in sorted(Path(tmp).glob("frame_*.png")):
            text = _ocr_image_text(frame_path)
            if text:
                texts.append(text)
    text = "\n".join(texts)
    parsed = _structured_payload_from_text(text)
    report.update(_media_report_fields(text, parsed, parser="video_frame_ocr", runtime=runtime))
    report["sampled_frame_count"] = len(texts)
    return parsed, report


def _structured_payload_from_text(text: str) -> dict[str, list[dict[str, Any]]]:
    clean = str(text or "").strip()
    if not clean:
        return {"holdings": [], "portfolio_transactions": []}
    if clean.startswith("{") or clean.startswith("["):
        try:
            return _structured_payload_from_json(json.loads(clean))
        except json.JSONDecodeError:
            return {"holdings": [], "portfolio_transactions": []}
    return {"holdings": [], "portfolio_transactions": []}


def _media_report_fields(
    text: str,
    parsed: dict[str, list[dict[str, Any]]],
    *,
    parser: str,
    runtime: dict[str, Any],
) -> dict[str, Any]:
    holding_count = len(parsed.get("holdings", []))
    transaction_count = len(parsed.get("portfolio_transactions", []))
    status = "Parsed" if holding_count or transaction_count else ("OcrTextOnly" if text.strip() else "NoOcrText")
    message = "OCR 已解析出结构化候选。" if status == "Parsed" else ("OCR 提取到文本，但未识别出结构化持仓/交易字段。" if status == "OcrTextOnly" else "OCR 未提取到有效文本。")
    return {
        "status": status,
        "parser": parser,
        "runtime": runtime,
        "holding_count": holding_count,
        "transaction_count": transaction_count,
        "ocr_text_chars": len(text),
        "ocr_text_preview": text[:500],
        "extracted_symbols": extract_symbols(text),
        "message": message,
    }


def _ocr_image_text(path: Path) -> str:
    try:
        import pytesseract
        from PIL import Image

        with Image.open(path) as image:
            return str(pytesseract.image_to_string(image, lang="chi_sim+eng") or "").strip()
    except Exception:
        return ""


def _image_ocr_runtime_status() -> dict[str, Any]:
    try:
        import pytesseract  # noqa: F401
        from PIL import Image  # noqa: F401

        python_available = True
    except Exception:
        python_available = False
    tesseract_path = shutil.which("tesseract") or ""
    return {
        "available": bool(python_available and tesseract_path),
        "pillow_available": _module_available("PIL"),
        "pytesseract_available": _module_available("pytesseract"),
        "tesseract_path": tesseract_path,
    }


def _video_ocr_runtime_status() -> dict[str, Any]:
    image_runtime = _image_ocr_runtime_status()
    ffmpeg_path = shutil.which("ffmpeg") or ""
    return {
        **image_runtime,
        "available": bool(image_runtime["available"] and ffmpeg_path),
        "ffmpeg_path": ffmpeg_path,
    }


def _module_available(name: str) -> bool:
    try:
        __import__(name)
        return True
    except Exception:
        return False


def _structured_payload_from_json(payload: Any) -> dict[str, list[dict[str, Any]]]:
    if isinstance(payload, dict):
        holdings = _structured_rows(payload, "holdings", "positions")
        transactions = _structured_rows(payload, "portfolio_transactions", "transactions", "trades")
        if holdings or transactions:
            return {"holdings": holdings, "portfolio_transactions": transactions}
        return _structured_payload_from_frame(pd.DataFrame([payload]))
    if isinstance(payload, list):
        return _structured_payload_from_frame(pd.DataFrame([item for item in payload if isinstance(item, dict)]))
    return {"holdings": [], "portfolio_transactions": []}


def _structured_payload_from_frame(frame: pd.DataFrame) -> dict[str, list[dict[str, Any]]]:
    if frame.empty:
        return {"holdings": [], "portfolio_transactions": []}
    rows = frame.fillna("").to_dict("records")
    kind = _infer_structured_rows_kind(frame.columns)
    if kind == "transaction":
        return {"holdings": [], "portfolio_transactions": rows}
    if kind == "holding":
        return {"holdings": rows, "portfolio_transactions": []}
    return {"holdings": [], "portfolio_transactions": []}


def _infer_structured_rows_kind(columns: Any) -> str:
    names = {str(column).strip().lower() for column in columns}
    transaction_terms = {
        "side",
        "方向",
        "交易类型",
        "trade_date",
        "order_time",
        "order_amount",
        "confirmed_amount",
        "confirmed_units",
        "交易状态",
    }
    holding_terms = {
        "position_value",
        "持仓金额",
        "市值",
        "market_value",
        "quantity",
        "份额",
        "持仓数量",
        "unrealized_pnl",
        "持仓收益",
        "weight",
        "权重",
    }
    if names & {str(item).lower() for item in transaction_terms}:
        return "transaction"
    if names & {str(item).lower() for item in holding_terms}:
        return "holding"
    return "unknown"


def _attachment_path(attachment: dict[str, Any]) -> Path | None:
    raw = str(attachment.get("path") or attachment.get("file_path") or "").strip()
    if not raw:
        return None
    return Path(raw).expanduser()


def _normalize_attachment_paths(attachments: list[dict[str, Any]], base_dir: Path) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for attachment in attachments:
        if not isinstance(attachment, dict):
            continue
        item = dict(attachment)
        raw_path = str(item.get("path") or item.get("file_path") or "").strip()
        if raw_path:
            path = Path(raw_path).expanduser()
            if not path.is_absolute():
                path = (base_dir / path).resolve()
            item["path"] = str(path)
            item.setdefault("name", path.name)
        normalized.append(item)
    return normalized


def confirm_holding_update_candidate(
    candidate_id: str,
    *,
    db_path: Path | str | None = None,
    holding_import_path: Path | str | None = None,
    transaction_import_path: Path | str | None = None,
    holdings_book_path: Path | str | None = None,
) -> dict[str, Any]:
    target_db = initialize_research_bus(db_path)
    clean_candidate_id = str(candidate_id or "").strip()
    if not clean_candidate_id:
        raise ValueError("candidate_id cannot be empty.")
    with _connect(target_db) as conn:
        row = conn.execute(
            "SELECT * FROM holding_update_candidates WHERE candidate_id=?",
            (clean_candidate_id,),
        ).fetchone()
    if row is None:
        raise ValueError(f"holding_update_candidate not found: {clean_candidate_id}")
    candidate = dict(row)
    payload = _loads(candidate.get("payload_json"), {})
    if not isinstance(payload, dict):
        payload = {}
    content_payload = _loads(candidate.get("content_text"), {})
    if isinstance(content_payload, dict):
        payload = {**content_payload, **payload}
    holding_rows = _structured_rows(payload, "holdings", "positions")
    transaction_rows = _structured_rows(payload, "portfolio_transactions", "transactions", "trades")
    if not holding_rows and not transaction_rows:
        _update_holding_candidate_status(target_db, clean_candidate_id, "NeedsStructuredData", "Candidate")
        return {
            "status": "NeedsStructuredData",
            "candidate_id": clean_candidate_id,
            "message": "候选输入没有结构化 holdings 或 portfolio_transactions，仍需人工解析。",
        }

    now = _now()
    confirmed_holding_count = 0
    confirmed_transaction_count = 0
    holding_path = (
        Path(holding_import_path).expanduser()
        if holding_import_path
        else _scoped_default_file(target_db, CONFIRMED_HOLDING_CANDIDATES_PATH)
    )
    transaction_path = (
        Path(transaction_import_path).expanduser()
        if transaction_import_path
        else _scoped_default_file(target_db, CONFIRMED_PORTFOLIO_TRANSACTIONS_PATH)
    )
    book_path = Path(holdings_book_path).expanduser() if holdings_book_path else HOLDINGS_BOOK_PATH
    if holding_rows:
        holding_frame = _candidate_holdings_frame(
            holding_rows,
            candidate_id=clean_candidate_id,
            source_system=str(candidate.get("source_system") or "ResearchBus确认持仓"),
            now=now,
        )
        _append_csv_records(holding_path, holding_frame)
        existing = load_holdings_book(book_path, missing_ok=True)
        combined = pd.concat([existing, holding_frame], ignore_index=True)
        canonical = canonical_holdings_frame(combined)
        save_holdings_book(canonical, book_path)
        if book_path.resolve() == HOLDINGS_BOOK_PATH.resolve():
            export_holdings_csv(canonical)
        sync_holdings_to_bus(canonical, db_path=target_db)
        confirmed_holding_count = int(len(holding_frame))
    if transaction_rows:
        transaction_frame = _candidate_transactions_frame(
            transaction_rows,
            candidate_id=clean_candidate_id,
            source_system=str(candidate.get("source_system") or "ResearchBus确认交易"),
            now=now,
        )
        _append_csv_records(transaction_path, transaction_frame)
        sync_frame = load_default_portfolio_transactions(paths=(transaction_path,))
        sync_portfolio_transactions_to_bus(sync_frame, db_path=target_db)
        confirmed_transaction_count = int(len(transaction_frame))
    _update_holding_candidate_status(target_db, clean_candidate_id, "Applied", "ConfirmedApplied")
    return {
        "status": "Applied",
        "candidate_id": clean_candidate_id,
        "confirmed_holding_count": confirmed_holding_count,
        "confirmed_transaction_count": confirmed_transaction_count,
        "holding_import_path": str(holding_path) if holding_rows else "",
        "transaction_import_path": str(transaction_path) if transaction_rows else "",
        "holdings_book_path": str(book_path) if holding_rows else "",
    }


def _structured_rows(payload: dict[str, Any], *keys: str) -> list[dict[str, Any]]:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, list):
            return [dict(item) for item in value if isinstance(item, dict)]
        if isinstance(value, dict):
            return [dict(value)]
    return []


def _candidate_holdings_frame(rows: list[dict[str, Any]], *, candidate_id: str, source_system: str, now: str) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    for row in rows:
        symbol = str(_row_value(row, "symbol", "代码", "ticker")).strip()
        market = str(_row_value(row, "market", "市场")).strip() or infer_market(symbol)
        records.append(
            {
                "source_system": str(_row_value(row, "source_system")).strip() or source_system or "ResearchBus确认持仓",
                "source_file": f"holding_update_candidate/{candidate_id}",
                "symbol": symbol,
                "name": str(_row_value(row, "name", "名称", "标的名称")).strip(),
                "market": market,
                "quantity": _row_value(row, "quantity", "份额", "数量"),
                "cost_basis": _row_value(row, "cost_basis", "成本", "成本价"),
                "position_value": _row_value(row, "position_value", "市值", "持仓金额", "amount"),
                "unrealized_pnl": _row_value(row, "unrealized_pnl", "持仓收益", "浮动盈亏", "pnl"),
                "weight": _row_value(row, "weight", "权重", "比例"),
                "updated_at": str(_row_value(row, "updated_at", "日期", "date")).strip() or now,
                "source_modified_time": now,
            }
        )
    frame = pd.DataFrame(records)
    for column in holding_columns():
        if column not in frame.columns:
            frame[column] = ""
    return canonical_holdings_frame(frame[holding_columns()].copy())


def _candidate_transactions_frame(rows: list[dict[str, Any]], *, candidate_id: str, source_system: str, now: str) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    for row in rows:
        name = str(_row_value(row, "name", "名称", "基金名称", "标的名称")).strip()
        side = str(_row_value(row, "side", "方向", "交易类型")).strip()
        order_amount = _row_value(row, "order_amount", "金额", "amount")
        trade_date = str(_row_value(row, "trade_date", "日期", "date")).strip()
        order_time = str(_row_value(row, "order_time", "时间", "time")).strip()
        symbol = str(_row_value(row, "symbol", "代码", "ticker")).strip()
        transaction_id = str(_row_value(row, "transaction_id", "交易订单号", "id")).strip() or _stable_id(
            "candidateTxn",
            candidate_id,
            trade_date,
            order_time,
            name,
            side,
            order_amount,
        )
        records.append(
            {
                "transaction_id": transaction_id,
                "source_system": str(_row_value(row, "source_system")).strip() or source_system or "ResearchBus确认交易",
                "account": str(_row_value(row, "account", "账户")).strip() or "默认账户",
                "trade_date": trade_date,
                "order_time": order_time,
                "timezone": str(_row_value(row, "timezone", "时区")).strip() or "Asia/Shanghai",
                "symbol": symbol,
                "name": name,
                "market": str(_row_value(row, "market", "市场")).strip() or infer_market(symbol),
                "asset_type": str(_row_value(row, "asset_type", "资产类型")).strip() or "fund",
                "side": side,
                "order_type": str(_row_value(row, "order_type", "订单类型")).strip() or "manual",
                "order_amount": order_amount,
                "confirmed_amount": _row_value(row, "confirmed_amount", "确认金额"),
                "confirmed_units": _row_value(row, "confirmed_units", "确认份额"),
                "confirmed_nav": _row_value(row, "confirmed_nav", "确认净值"),
                "fee": _row_value(row, "fee", "手续费"),
                "status": str(_row_value(row, "status", "状态")).strip() or "ConfirmedByResearchBus",
                "quality_status": str(_row_value(row, "quality_status", "质量状态")).strip() or "Confirmed",
                "source_path": str(_row_value(row, "source_path", "源文件")).strip() or f"holding_update_candidate/{candidate_id}",
                "evidence_frame": str(_row_value(row, "evidence_frame", "证据帧")).strip(),
                "notes": str(_row_value(row, "notes", "备注")).strip(),
                "updated_at": str(_row_value(row, "updated_at", "更新时间")).strip() or now,
            }
        )
    columns = [
        "transaction_id",
        "source_system",
        "account",
        "trade_date",
        "order_time",
        "timezone",
        "symbol",
        "name",
        "market",
        "asset_type",
        "side",
        "order_type",
        "order_amount",
        "confirmed_amount",
        "confirmed_units",
        "confirmed_nav",
        "fee",
        "status",
        "quality_status",
        "source_path",
        "evidence_frame",
        "notes",
        "updated_at",
    ]
    frame = pd.DataFrame(records)
    for column in columns:
        if column not in frame.columns:
            frame[column] = ""
    return frame[columns].copy()


def _append_csv_records(path: Path, frame: pd.DataFrame) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = pd.read_csv(path) if path.exists() else pd.DataFrame()
    combined = pd.concat([existing, frame], ignore_index=True) if not existing.empty else frame.copy()
    combined = combined.drop_duplicates(keep="last")
    temp_path = path.with_suffix(f"{path.suffix}.tmp")
    combined.to_csv(temp_path, index=False)
    temp_path.replace(path)
    return path


def _row_value(row: dict[str, Any], *keys: str) -> object:
    normalized = {str(key).strip().lower(): value for key, value in row.items()}
    for key in keys:
        if key in row:
            return row[key]
        lower = key.strip().lower()
        if lower in normalized:
            return normalized[lower]
    return ""


def _update_holding_candidate_status(db_path: Path, candidate_id: str, status: str, quality_status: str) -> None:
    with _connect(db_path) as conn:
        conn.execute(
            """
            UPDATE holding_update_candidates
            SET status=?, quality_status=?, updated_at=?
            WHERE candidate_id=?
            """,
            (status, quality_status, _now(), candidate_id),
        )


def _route_chat_input(classification: str, text: str = "") -> tuple[str, str]:
    if classification == "sync_request":
        return "ResearchBus", "sync_all"
    if classification == "orchestration":
        return "ResearchBus", "orchestrate_system"
    if classification == "independent_validation":
        return "ResearchBus", "independent_validation_checksum" if _looks_like_checksum_request(text) else "independent_validation_dry_run"
    if classification == "holding_update":
        return "ResearchBus", "holding_update_candidate"
    if classification == "system_update":
        return "ResearchBus", "system_update_request"
    if classification == "validation_task":
        return "ResearchBus", "validation_task_from_chat"
    return "ResearchBus", "chat_general_note"


def _looks_like_checksum_request(text: str) -> bool:
    lowered = str(text or "").lower()
    return any(keyword in lowered for keyword in ["checksum", "校验", "实际验证", "实际执行", "执行校验", "sha256"])


def _run_independent_validation_from_payload(payload: dict[str, Any], db_path: Path, *, mode: str):
    synthetic_rows = int(payload.get("synthetic_rows") or payload.get("rows") or 0)
    rows_per_shard = int(payload.get("rows_per_shard") or 0)
    worker_count = int(payload.get("worker_count") or payload.get("workers") or 1)
    if synthetic_rows <= 0 or rows_per_shard <= 0:
        parsed_scale = _parse_independent_validation_scale(str(payload.get("content_text", "")))
        synthetic_rows = synthetic_rows if synthetic_rows > 0 else parsed_scale["synthetic_rows"]
        rows_per_shard = rows_per_shard if rows_per_shard > 0 else parsed_scale["rows_per_shard"]
        worker_count = worker_count if worker_count > 1 else parsed_scale.get("worker_count", 1)
    output_dir = payload.get("output_dir") or ""
    scoped_output_dir = Path(output_dir).expanduser() if str(output_dir).strip() else _scoped_default_dir(db_path, "independentValidation")
    return run_independent_validation(
        db_path=db_path,
        synthetic_rows=synthetic_rows,
        rows_per_shard=rows_per_shard,
        mode=mode,
        output_dir=scoped_output_dir,
        worker_count=worker_count,
    )


def _run_orchestration_from_payload(payload: dict[str, Any], db_path: Path, *, request_context: dict[str, Any] | None = None):
    text = str(payload.get("content_text") or payload.get("text") or "").strip()
    parsed = _parse_orchestration_request(text)
    system_name = str(payload.get("system_name") or payload.get("target_system_name") or parsed["system_name"]).strip()
    action = str(payload.get("action") or parsed["action"]).strip()
    execute = bool(payload.get("execute", parsed["execute"]))
    timeout_seconds = int(payload.get("timeout_seconds") or 120)
    requester_system = str(
        payload.get("requester_system")
        or payload.get("source_system")
        or (request_context or {}).get("source_system")
        or "ResearchBus"
    )
    approval_token = str(payload.get("approval_id") or payload.get("approval_token") or "")
    return orchestrate_child_system(
        system_name,
        action=action,
        execute=execute,
        db_path=db_path,
        timeout_seconds=timeout_seconds,
        requester_system=requester_system,
        approval_token=approval_token,
    )


def _parse_orchestration_request(text: str) -> dict[str, Any]:
    lowered = str(text or "").lower()
    if any(keyword in lowered for keyword in ["fifa", "tab", "世界杯"]):
        system_name = "FIFA-Research-System"
    elif any(keyword in lowered for keyword in ["政府文件", "政策系统", "政策解读", "source authority", "source-authority"]):
        system_name = "GovernmentPolicySystem"
    elif any(keyword in lowered for keyword in ["行研", "ai-research", "ai research"]):
        system_name = "AI-Research-System"
    elif any(keyword in lowered for keyword in ["独立验证", "independent validation"]):
        system_name = "IndependentValidation"
    else:
        system_name = "PFIOS"

    if any(keyword in lowered for keyword in ["检查", "体检", "health", "status", "状态"]):
        action = "health"
    elif any(keyword in lowered for keyword in ["同步", "sync", "refresh", "刷新"]):
        action = "sync"
    else:
        action = "standalone"

    execute = any(keyword in lowered for keyword in ["实际运行", "实际执行", "立即运行", "立即执行", "execute now"])
    return {"system_name": system_name, "action": action, "execute": execute}


def _scoped_default_file(db_path: Path | str, default_path: Path) -> Path:
    target_db = Path(db_path).expanduser()
    try:
        if target_db.resolve() != research_bus_db_path().resolve():
            return target_db.parent / default_path.name
    except Exception:
        return target_db.parent / default_path.name
    return default_path


def _scoped_default_dir(db_path: Path | str, dirname: str) -> Path | None:
    target_db = Path(db_path).expanduser()
    try:
        if target_db.resolve() != research_bus_db_path().resolve():
            return target_db.parent / dirname
    except Exception:
        return target_db.parent / dirname
    return None


def _parse_independent_validation_scale(text: str) -> dict[str, int]:
    clean = _normalize_scale_text(text)
    synthetic_rows = _parse_total_rows(clean)
    rows_per_shard = _parse_rows_per_shard(clean)
    worker_count = _parse_worker_count(clean)
    if synthetic_rows <= 0:
        synthetic_rows = 1_000_000_000
    if rows_per_shard <= 0:
        rows_per_shard = 100_000_000 if synthetic_rows >= 100_000_000 else 1_000_000
    return {"synthetic_rows": synthetic_rows, "rows_per_shard": rows_per_shard, "worker_count": worker_count}


def _parse_worker_count(clean: str) -> int:
    patterns = [
        r"(\d{1,3})\s*(?:个)?\s*(?:worker|workers|本机worker|工作进程|线程)",
        r"(?:worker|workers|本机worker|工作进程|线程)\s*[:=]?\s*(\d{1,3})",
    ]
    for pattern in patterns:
        match = re.search(pattern, clean, flags=re.IGNORECASE)
        if match:
            return max(1, min(64, int(match.group(1))))
    return 1


def _normalize_scale_text(text: str) -> str:
    return (
        str(text or "")
        .lower()
        .replace(",", "")
        .replace("，", ",")
        .replace("：", ":")
        .replace("；", ";")
        .replace("。", ".")
    )


def _parse_total_rows(clean: str) -> int:
    total_text = re.sub(
        r"(?:每片|每个分片|每分片|分片大小|rows_per_shard|rows per shard|per shard|shard)\s*[:=]?\s*[^,;.]+",
        " ",
        clean,
    )
    candidates = _scaled_number_candidates(total_text)
    explicit_rows = [int(match.group(1)) for match in re.finditer(r"(\d{7,})\s*(?:行|rows?)?", total_text)]
    return max(candidates + explicit_rows + [0])


def _parse_rows_per_shard(clean: str) -> int:
    context_pattern = re.compile(
        r"(?:每片|每个分片|每分片|分片大小|rows_per_shard|rows per shard|per shard|shard)\s*[:=]?\s*([^,;.]+)"
    )
    for match in context_pattern.finditer(clean):
        segment = match.group(1)
        scaled = _scaled_number_candidates(segment)
        if scaled:
            return max(scaled)
        explicit = re.search(r"(\d{5,})", segment)
        if explicit:
            return int(explicit.group(1))
    return 0


def _scaled_number_candidates(text: str) -> list[int]:
    candidates: list[int] = []
    chinese_unit_pattern = re.compile(r"(\d+(?:\.\d+)?|[一二两三四五六七八九十百点]+)?\s*(千万|百万|亿万|亿|万)")
    for match in chinese_unit_pattern.finditer(text):
        number_text = match.group(1) or ""
        unit = match.group(2)
        multiplier = {
            "万": 10_000,
            "百万": 1_000_000,
            "千万": 10_000_000,
            "亿": 100_000_000,
            "亿万": 1_000_000_000,
        }[unit]
        if unit in {"百万", "千万", "亿万"} and not number_text:
            number = 1.0
        else:
            number = _parse_chinese_or_decimal_number(number_text or "1")
        candidates.append(int(number * multiplier))
    english_unit_pattern = re.compile(
        r"(?:(\d+(?:\.\d+)?|one|two|three|four|five|six|seven|eight|nine|ten|hundred)\s+)?(billion|million)"
    )
    for match in english_unit_pattern.finditer(text):
        number_text = (match.group(1) or "1").strip()
        unit = match.group(2)
        number = _parse_english_number(number_text)
        multiplier = 1_000_000_000 if unit == "billion" else 1_000_000
        candidates.append(int(number * multiplier))
    return candidates


def _parse_chinese_or_decimal_number(text: str) -> float:
    clean = str(text or "").strip()
    if not clean:
        return 1.0
    if re.fullmatch(r"\d+(?:\.\d+)?", clean):
        return float(clean)
    if "点" in clean:
        integer_part, decimal_part = clean.split("点", 1)
        decimal_digits = "".join(str(_CHINESE_DIGITS.get(char, 0)) for char in decimal_part if char in _CHINESE_DIGITS)
        decimal = float(f"0.{decimal_digits}") if decimal_digits else 0.0
        return _parse_chinese_or_decimal_number(integer_part) + decimal
    if "百" in clean:
        left, _, right = clean.partition("百")
        hundreds = _CHINESE_DIGITS.get(left, 1) if left else 1
        return hundreds * 100 + _parse_chinese_or_decimal_number(right or "0")
    if "十" in clean:
        left, _, right = clean.partition("十")
        tens = _CHINESE_DIGITS.get(left, 1) if left else 1
        ones = _CHINESE_DIGITS.get(right, 0) if right else 0
        return tens * 10 + ones
    return float(_CHINESE_DIGITS.get(clean, 1))


def _parse_english_number(text: str) -> float:
    clean = str(text or "").strip().lower()
    if re.fullmatch(r"\d+(?:\.\d+)?", clean):
        return float(clean)
    return {
        "one": 1.0,
        "two": 2.0,
        "three": 3.0,
        "four": 4.0,
        "five": 5.0,
        "six": 6.0,
        "seven": 7.0,
        "eight": 8.0,
        "nine": 9.0,
        "ten": 10.0,
        "hundred": 100.0,
    }.get(clean, 1.0)


_CHINESE_DIGITS = {
    "零": 0,
    "〇": 0,
    "一": 1,
    "二": 2,
    "两": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
}


def _insert_validation_tasks_from_chat(conn: sqlite3.Connection, input_id: str, text: str, source_system: str) -> int:
    symbols = extract_symbols(text)
    if not symbols:
        symbols = [""]
    count = 0
    for symbol in symbols[:12]:
        market = infer_market(symbol)
        task_id = _stable_id("chatValidationTask", input_id, symbol, text)
        conn.execute(
            """
            INSERT INTO validation_tasks(
                task_id, source_system, source_report_id, source_report_path, source_paragraph,
                research_topic, symbol, market, signal_to_validate, sample_period, cost_assumption,
                benchmark, status, validation_report_path, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(task_id) DO UPDATE SET
                source_paragraph=excluded.source_paragraph,
                signal_to_validate=excluded.signal_to_validate,
                updated_at=excluded.updated_at
            """,
            (
                task_id,
                source_system,
                input_id,
                f"chat://{input_id}",
                _truncate(text, 800),
                _truncate(f"对话输入验证：{text}", 120),
                symbol,
                market,
                _truncate(text, 280),
                "由 PFIOS 或独立验证系统选择样本区间；正式报告必须记录样本范围。",
                "必须披露佣金、滑点、冲击成本、汇率或申赎费用假设。",
                benchmark_for_market(market),
                "待验证",
                "",
                _now(),
                _now(),
            ),
        )
        count += 1
    return count


def _upsert_request(conn: sqlite3.Connection, request: BusApiRequest) -> None:
    conn.execute(
        """
        INSERT INTO bus_api_requests(
            request_id, source_system, target_system, request_type, status, priority,
            payload_json, response_json, error_message, created_at, updated_at, processed_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(request_id) DO UPDATE SET
            status=excluded.status,
            priority=excluded.priority,
            payload_json=excluded.payload_json,
            updated_at=excluded.updated_at
        """,
        (
            request.request_id,
            request.source_system,
            request.target_system,
            request.request_type,
            request.status,
            request.priority,
            _json_dumps(request.payload),
            _json_dumps(request.response),
            request.error_message,
            request.created_at,
            request.updated_at,
            request.processed_at,
        ),
    )


def _chat_payload_from_file(path: Path, default_source_system: str) -> dict[str, Any]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("JSON chat input must be an object.")
        text = str(payload.get("content_text") or payload.get("text") or payload.get("message") or "").strip()
        if not text:
            raise ValueError("JSON chat input must include content_text, text, or message.")
        attachments = payload.get("attachments", [])
        if not isinstance(attachments, list):
            attachments = []
        attachments = _normalize_attachment_paths(attachments, path.parent)
        return {
            "content_text": text,
            "source_system": str(payload.get("source_system") or default_source_system),
            "author": str(payload.get("author") or ""),
            "channel": str(payload.get("channel") or "dropbox"),
            "attachments": attachments,
        }
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError("Chat input file is empty.")
    return {
        "content_text": text,
        "source_system": default_source_system,
        "author": "",
        "channel": f"dropbox:{suffix.lstrip('.')}",
        "attachments": [],
    }


def _move_to_unique_dir(path: Path, target_dir: Path) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / path.name
    if target.exists():
        target = target_dir / f"{path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hashlib.sha1(str(path).encode('utf-8')).hexdigest()[:8]}{path.suffix}"
    path.replace(target)
    return target


def _mark_request_status(request_id: str, status: str, *, db_path: Path | str | None = None) -> None:
    if status not in API_STATUSES:
        raise ValueError(f"Unsupported API status: {status}")
    target_db = initialize_research_bus(db_path)
    with _connect(target_db) as conn:
        conn.execute("UPDATE bus_api_requests SET status=?, updated_at=? WHERE request_id=?", (status, _now(), request_id))
        conn.execute(
            """
            UPDATE bus_chat_inputs
            SET status=?
            WHERE linked_request_id=? AND status IN ('Pending', 'Processing')
            """,
            (status, request_id),
        )


def _write_outbox(conn: sqlite3.Connection, source_system: str, target_system: str, message_type: str, payload: dict[str, Any]) -> None:
    message_id = _stable_id("busOutbox", source_system, target_system, message_type, _json_dumps(payload), _now())
    conn.execute(
        """
        INSERT INTO bus_system_outbox(message_id, source_system, target_system, message_type, status, payload_json, created_at, delivered_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (message_id, source_system, target_system, message_type, "Pending", _json_dumps(payload), _now(), ""),
    )


def _request_target(conn: sqlite3.Connection, request_id: str) -> str:
    row = conn.execute("SELECT source_system FROM bus_api_requests WHERE request_id=?", (request_id,)).fetchone()
    return str(row["source_system"]) if row else ""


@contextmanager
def _connect(path: Path | str):
    conn = sqlite3.connect(str(path), timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def _stable_id(prefix: str, *parts: object) -> str:
    raw = "\n".join(str(part) for part in parts)
    return f"{prefix}_{hashlib.sha1(raw.encode('utf-8')).hexdigest()[:20]}"


def _json_dumps(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)


def _loads(value: object, default: Any) -> Any:
    try:
        return json.loads(str(value or ""))
    except json.JSONDecodeError:
        return default


def _seconds_since(value: str, now_ts: float) -> float:
    try:
        normalized = value.replace("Z", "+00:00")
        then = datetime.fromisoformat(normalized)
        return max(0.0, now_ts - then.timestamp())
    except Exception:
        return float("inf")


def _truncate(text: str, limit: int) -> str:
    clean = str(text or "").strip()
    return clean if len(clean) <= limit else f"{clean[: limit - 1]}…"


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")
