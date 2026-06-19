from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

from src.config import ROOT
from src.reporting.paths import ARTIFACTS_HOME, REPORTS_HOME


DEFAULT_PFI_BUS_DB = ROOT.parents[2] / "data" / "researchBus" / "ResearchBus.sqlite"
BRIDGE_DIR = ROOT / "data" / "report_artifacts" / "research_bus_bridge"
REPORT_SUFFIXES = {".pdf", ".md", ".txt", ".docx", ".doc"}
SCHEMA_VERSION = "ResearchBusV1"
VALIDATION_KEYWORDS = (
    "验证",
    "回测",
    "趋势",
    "动量",
    "均线",
    "rsi",
    "macd",
    "估值",
    "财报",
    "公告",
    "催化",
    "政策",
    "行业",
    "需求",
    "价格",
    "放量",
    "回撤",
    "失效",
    "观察",
    "thesis",
    "signal",
    "backtest",
    "risk",
)


def research_bus_db_path(path: Path | str | None = None) -> Path:
    if path is not None:
        return Path(path).expanduser()
    configured = os.getenv("PFI_RESEARCH_BUS_DB", "").strip()
    if configured:
        return Path(configured).expanduser()
    return DEFAULT_PFI_BUS_DB


def sync_research_bus(
    db_path: Path | str | None = None,
    *,
    report_limit: int = 500,
    result_limit: int = 500,
) -> dict[str, Any]:
    target_db = initialize_research_bus(db_path)
    report_count = publish_ai_reports(target_db, limit=report_limit)
    pfi_os_results_path, pfi_os_result_count = pull_pfi_os_results(target_db, limit=result_limit)
    validation_tasks_path, validation_task_count = pull_validation_tasks(target_db, limit=result_limit)
    validation_runs_path, validation_run_count = pull_independent_validation_runs(target_db, limit=result_limit)
    consumer_state_path, consumer_state_count = pull_consumer_behavior_state(target_db, limit=result_limit)
    holdings_path, holdings_count = pull_holdings_master(target_db, limit=result_limit)
    holding_mappings_path, holding_mapping_count = pull_holding_symbol_mappings(target_db, limit=result_limit)
    portfolio_transactions_path, portfolio_transaction_count = pull_portfolio_transactions(target_db, limit=result_limit)
    holding_candidates_path, holding_candidate_count = pull_holding_update_candidates(target_db, limit=result_limit)
    with _connect(target_db) as conn:
        _upsert_system_state(
            conn,
            "AI-Research-System",
            "Ready",
            str(ROOT),
            {
                "published_reports": report_count,
                "pulled_pfi_os_results": pfi_os_result_count,
                "pulled_validation_tasks": validation_task_count,
                "pulled_independent_validation_runs": validation_run_count,
                "pulled_consumer_behavior_state": consumer_state_count,
                "pulled_holdings_master": holdings_count,
                "pulled_holding_symbol_mappings": holding_mapping_count,
                "pulled_portfolio_transactions": portfolio_transaction_count,
                "pulled_holding_update_candidates": holding_candidate_count,
                "bridge_dir": str(BRIDGE_DIR),
            },
        )
        _heartbeat_with_conn(
            conn,
            "AI-Research-System",
            status="Ready",
            capabilities=[
                "publish_reports",
                "pull_pfi_os_results",
                "pull_validation_tasks",
                "pull_independent_validation",
                "pull_holdings_master",
                "pull_holding_symbol_mappings",
                "pull_portfolio_transactions",
                "pull_holding_update_candidates",
            ],
        )
        _record_event(
            conn,
            "ai_research_bridge_sync",
            "AI-Research-System",
            "ResearchBus",
            "success",
            f"reports={report_count}; pfi_os_results={pfi_os_result_count}; validation_tasks={validation_task_count}; independent_validation_runs={validation_run_count}; consumer_behavior_state={consumer_state_count}; holdings={holdings_count}; holding_symbol_mappings={holding_mapping_count}; portfolio_transactions={portfolio_transaction_count}; holding_update_candidates={holding_candidate_count}",
        )
    return {
        "schema": SCHEMA_VERSION,
        "synced_at": _now(),
        "db_path": str(target_db),
        "published_reports": report_count,
        "pfi_os_results_path": str(pfi_os_results_path),
        "pfi_os_result_count": pfi_os_result_count,
        "validation_tasks_path": str(validation_tasks_path),
        "validation_task_count": validation_task_count,
        "independent_validation_runs_path": str(validation_runs_path),
        "independent_validation_run_count": validation_run_count,
        "consumer_behavior_state_path": str(consumer_state_path),
        "consumer_behavior_state_count": consumer_state_count,
        "holdings_master_path": str(holdings_path),
        "holdings_master_count": holdings_count,
        "holding_symbol_mappings_path": str(holding_mappings_path),
        "holding_symbol_mapping_count": holding_mapping_count,
        "portfolio_transactions_path": str(portfolio_transactions_path),
        "portfolio_transaction_count": portfolio_transaction_count,
        "holding_update_candidates_path": str(holding_candidates_path),
        "holding_update_candidate_count": holding_candidate_count,
    }


def submit_bus_request(
    request_type: str,
    payload: dict[str, Any] | None = None,
    *,
    source_system: str = "AI-Research-System",
    target_system: str = "ResearchBus",
    priority: int = 5,
    db_path: Path | str | None = None,
) -> dict[str, Any]:
    target_db = initialize_research_bus(db_path)
    clean_payload = payload or {}
    request_id = _stable_id("busRequest", source_system, target_system, request_type, json.dumps(clean_payload, ensure_ascii=False, sort_keys=True), _now())
    now = _now()
    with _connect(target_db) as conn:
        conn.execute(
            """
            INSERT INTO bus_api_requests(
                request_id, source_system, target_system, request_type, status, priority,
                payload_json, response_json, error_message, created_at, updated_at, processed_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (request_id, source_system, target_system, request_type, "Pending", int(priority), json.dumps(clean_payload, ensure_ascii=False), "{}", "", now, now, ""),
        )
    return {"request_id": request_id, "source_system": source_system, "target_system": target_system, "request_type": request_type, "status": "Pending"}


def submit_chat_input(
    text: str,
    *,
    source_system: str = "AI-Research-Chat",
    author: str = "",
    channel: str = "chat",
    attachments: list[dict[str, Any]] | None = None,
    db_path: Path | str | None = None,
) -> dict[str, Any]:
    target_db = initialize_research_bus(db_path)
    content = str(text or "").strip()
    if not content:
        raise ValueError("text cannot be empty.")
    clean_attachments = _normalize_chat_attachments(attachments)
    classification = _classify_chat_input(content)
    request_type = _route_chat_request_type(classification, content)
    payload = _chat_payload(content, classification, attachments=clean_attachments)
    request = submit_bus_request(
        request_type,
        payload,
        source_system=source_system,
        target_system="ResearchBus",
        db_path=target_db,
    )
    input_id = _stable_id("chatInput", source_system, channel, author, content, request["request_id"])
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
                payload_json=excluded.payload_json
            """,
            (
                input_id,
                source_system,
                author,
                channel,
                content,
                json.dumps(clean_attachments, ensure_ascii=False),
                classification,
                request["request_id"],
                "Pending",
                json.dumps(payload, ensure_ascii=False),
                _now(),
                "",
            ),
        )
    return {"input_id": input_id, "classification": classification, "linked_request_id": request["request_id"], "request_type": request_type}


def process_pending_research_bus_requests(
    db_path: Path | str | None = None,
    *,
    system_name: str = "AI-Research-System",
    limit: int = 25,
) -> dict[str, Any]:
    target_db = initialize_research_bus(db_path)
    with _connect(target_db) as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM bus_api_requests
            WHERE status='Pending' AND target_system IN (?, 'All', '*')
            ORDER BY priority ASC, created_at ASC
            LIMIT ?
            """,
            (system_name, int(limit)),
        ).fetchall()
    processed = 0
    failed = 0
    results = []
    for row in rows:
        request_id = row["request_id"]
        request_type = row["request_type"]
        payload = _json_loads(row["payload_json"], {})
        _set_request_status(target_db, request_id, "Processing")
        try:
            response = _handle_ai_request(target_db, request_type, payload)
            _complete_request(target_db, request_id, response=response)
            processed += 1
            results.append({"request_id": request_id, "request_type": request_type, "status": "Completed", "response": response})
        except Exception as exc:
            _complete_request(target_db, request_id, response={}, error_message=str(exc))
            failed += 1
            results.append({"request_id": request_id, "request_type": request_type, "status": "Failed", "error": str(exc)})
    heartbeat_system(system_name, db_path=target_db, status="Ready", payload={"processed": processed, "failed": failed})
    return {"system_name": system_name, "processed": processed, "failed": failed, "results": results}


def heartbeat_system(
    system_name: str,
    *,
    db_path: Path | str | None = None,
    status: str = "Ready",
    capabilities: list[str] | None = None,
    payload: dict[str, Any] | None = None,
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
            (system_name, status, json.dumps(capabilities or [], ensure_ascii=False), json.dumps(payload or {}, ensure_ascii=False), _now()),
        )


def initialize_research_bus(path: Path | str | None = None) -> Path:
    db_path = research_bus_db_path(path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with _connect(db_path) as conn:
        _create_schema(conn)
    return db_path


def publish_ai_reports(db_path: Path | str | None = None, *, limit: int = 500) -> int:
    target_db = initialize_research_bus(db_path)
    report_paths = _report_paths(limit=limit)
    count = 0
    with _connect(target_db) as conn:
        for path in report_paths:
            payload = _report_payload(path)
            conn.execute(
                """
                INSERT INTO research_reports(
                    report_id, source_system, report_type, title, report_date, period, path, content_hash,
                    summary, symbols_json, topics_json, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(report_id) DO UPDATE SET
                    report_type=excluded.report_type,
                    title=excluded.title,
                    report_date=excluded.report_date,
                    period=excluded.period,
                    path=excluded.path,
                    content_hash=excluded.content_hash,
                    summary=excluded.summary,
                    symbols_json=excluded.symbols_json,
                    topics_json=excluded.topics_json,
                    updated_at=excluded.updated_at
                """,
                (
                    payload["report_id"],
                    "AI-Research-System",
                    payload["report_type"],
                    payload["title"],
                    payload["report_date"],
                    payload["period"],
                    payload["path"],
                    payload["content_hash"],
                    payload["summary"],
                    json.dumps(payload["symbols"], ensure_ascii=False),
                    json.dumps(payload["topics"], ensure_ascii=False),
                    payload["created_at"],
                    payload["updated_at"],
                ),
            )
            for task in _validation_tasks_from_report(payload):
                conn.execute(
                    """
                    INSERT INTO validation_tasks(
                        task_id, source_system, source_report_id, source_report_path, source_paragraph,
                        research_topic, symbol, market, signal_to_validate, sample_period,
                        cost_assumption, benchmark, status, validation_report_path, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(task_id) DO UPDATE SET
                        source_paragraph=excluded.source_paragraph,
                        research_topic=excluded.research_topic,
                        symbol=excluded.symbol,
                        market=excluded.market,
                        signal_to_validate=excluded.signal_to_validate,
                        sample_period=excluded.sample_period,
                        cost_assumption=excluded.cost_assumption,
                        benchmark=excluded.benchmark,
                        updated_at=excluded.updated_at
                    """,
                    (
                        task["task_id"],
                        "AI-Research-System",
                        task["source_report_id"],
                        task["source_report_path"],
                        task["source_paragraph"],
                        task["research_topic"],
                        task["symbol"],
                        task["market"],
                        task["signal_to_validate"],
                        task["sample_period"],
                        task["cost_assumption"],
                        task["benchmark"],
                        "待验证",
                        "",
                        task["created_at"],
                        task["updated_at"],
                    ),
                )
            count += 1
        _record_event(conn, "ai_reports_publish", "AI-Research-System", "ResearchBus", "success", f"reports={count}")
    return count


def pull_pfi_os_results(db_path: Path | str | None = None, *, limit: int = 500) -> tuple[Path, int]:
    target_db = initialize_research_bus(db_path)
    with _connect(target_db) as conn:
        rows = conn.execute(
            """
            SELECT result_id, report_path, metadata_path, strategy_id, symbol, market, total_return,
                   annualized_return, max_drawdown, sharpe, research_status, decision_quality_score,
                   data_quality_status, cross_validation_status, updated_at, payload_json
            FROM pfi_os_results
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    payload = {
        "schema": SCHEMA_VERSION,
        "exported_at": _now(),
        "source_system": "ResearchBus",
        "target_system": "AI-Research-System",
        "purpose": "行研系统读取 PFIOS 回测结论、决策质量、门禁状态和报告路径。",
        "results": [_row_to_payload(row) for row in rows],
    }
    path = BRIDGE_DIR / "PFIOSResultsFromBus.json"
    _atomic_write_json(path, payload)
    return path, len(rows)


def pull_validation_tasks(db_path: Path | str | None = None, *, limit: int = 500) -> tuple[Path, int]:
    target_db = initialize_research_bus(db_path)
    with _connect(target_db) as conn:
        rows = conn.execute(
            """
            SELECT task_id, source_report_path, source_paragraph, research_topic, symbol, market,
                   signal_to_validate, sample_period, cost_assumption, benchmark, status,
                   validation_report_path, updated_at
            FROM validation_tasks
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    payload = {
        "schema": SCHEMA_VERSION,
        "exported_at": _now(),
        "source_system": "ResearchBus",
        "target_system": "AI-Research-System",
        "purpose": "行研系统读取 PFIOS 自动生成和人工维护的待验证研究问题。",
        "validation_tasks": [_row_to_payload(row) for row in rows],
    }
    path = BRIDGE_DIR / "ValidationTasksFromBus.json"
    _atomic_write_json(path, payload)
    return path, len(rows)


def pull_independent_validation_runs(db_path: Path | str | None = None, *, limit: int = 500) -> tuple[Path, int]:
    target_db = initialize_research_bus(db_path)
    with _connect(target_db) as conn:
        rows = conn.execute(
            """
            SELECT run_id, source_system, status, mode, manifest_path, total_rows, shard_count,
                   started_at, completed_at, output_path, payload_json, updated_at
            FROM independent_validation_runs
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    payload = {
        "schema": SCHEMA_VERSION,
        "exported_at": _now(),
        "source_system": "ResearchBus",
        "target_system": "AI-Research-System",
        "purpose": "行研系统读取独立验证系统的大规模分片验证计划和运行状态。",
        "independent_validation_runs": [_row_to_payload(row) for row in rows],
    }
    path = BRIDGE_DIR / "IndependentValidationRunsFromBus.json"
    _atomic_write_json(path, payload)
    return path, len(rows)


def pull_consumer_behavior_state(db_path: Path | str | None = None, *, limit: int = 500) -> tuple[Path, int]:
    target_db = initialize_research_bus(db_path)
    with _connect(target_db) as conn:
        rows = conn.execute(
            """
            SELECT source_system, db_path, run_count, transaction_count, ledger_count,
                   latest_run_id, latest_generated_at, total_amount, manual_review_count,
                   summary_json, updated_at
            FROM consumer_behavior_state
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    payload = {
        "schema": SCHEMA_VERSION,
        "exported_at": _now(),
        "source_system": "ResearchBus",
        "target_system": "AI-Research-System",
        "purpose": "行研系统读取消费行为分析系统内部状态、交易统计和人工核对压力。",
        "consumer_behavior_state": [_row_to_payload(row) for row in rows],
    }
    path = BRIDGE_DIR / "ConsumerBehaviorStateFromBus.json"
    _atomic_write_json(path, payload)
    return path, len(rows)


def pull_holdings_master(db_path: Path | str | None = None, *, limit: int = 500) -> tuple[Path, int]:
    target_db = initialize_research_bus(db_path)
    with _connect(target_db) as conn:
        rows = conn.execute(
            """
            SELECT holding_id, source_system, account, symbol, name, market, asset_type,
                   quantity, cost_basis, position_value, unrealized_pnl, weight, as_of,
                   source_path, payload_json, updated_at
            FROM holdings_master
            ORDER BY updated_at DESC, position_value DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    payload = {
        "schema": SCHEMA_VERSION,
        "exported_at": _now(),
        "source_system": "ResearchBus",
        "target_system": "AI-Research-System",
        "purpose": "行研系统读取 PFIOS/消费系统/支付宝导入后的统一持仓主数据。",
        "holdings": [_row_to_payload(row) for row in rows],
    }
    path = BRIDGE_DIR / "HoldingsMasterFromBus.json"
    _atomic_write_json(path, payload)
    return path, len(rows)


def pull_holding_symbol_mappings(db_path: Path | str | None = None, *, limit: int = 500) -> tuple[Path, int]:
    target_db = initialize_research_bus(db_path)
    with _connect(target_db) as conn:
        rows = conn.execute(
            """
            SELECT mapping_id, source_system, holding_name, holding_market, original_symbol,
                   proxy_symbol, proxy_name, proxy_market, status, confidence, reason,
                   source, payload_json, updated_at
            FROM holding_symbol_mappings
            ORDER BY
                CASE status
                    WHEN 'ConfirmedSymbol' THEN 1
                    WHEN 'ProxyMapped' THEN 2
                    ELSE 3
                END,
                holding_name ASC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    payload = {
        "schema": SCHEMA_VERSION,
        "exported_at": _now(),
        "source_system": "ResearchBus",
        "target_system": "AI-Research-System",
        "purpose": "行研系统读取持仓名称到行情代码或 ETF/指数代理的映射；仅用于研究观察和情绪分析。",
        "holding_symbol_mappings": [_row_to_payload(row) for row in rows],
    }
    path = BRIDGE_DIR / "HoldingSymbolMappingsFromBus.json"
    _atomic_write_json(path, payload)
    return path, len(rows)


def pull_portfolio_transactions(db_path: Path | str | None = None, *, limit: int = 500) -> tuple[Path, int]:
    target_db = initialize_research_bus(db_path)
    with _connect(target_db) as conn:
        rows = conn.execute(
            """
            SELECT transaction_id, source_system, account, trade_date, order_time, timezone,
                   symbol, name, market, asset_type, side, order_type, order_amount,
                   confirmed_amount, confirmed_units, confirmed_nav, fee, status,
                   quality_status, source_path, evidence_frame, notes, payload_json, updated_at
            FROM portfolio_transactions
            ORDER BY trade_date DESC, order_time DESC, updated_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    payload = {
        "schema": SCHEMA_VERSION,
        "exported_at": _now(),
        "source_system": "ResearchBus",
        "target_system": "AI-Research-System",
        "purpose": "行研系统读取统一交易记录、待确认订单和视频候选交易证据。",
        "portfolio_transactions": [_row_to_payload(row) for row in rows],
    }
    path = BRIDGE_DIR / "PortfolioTransactionsFromBus.json"
    _atomic_write_json(path, payload)
    return path, len(rows)


def pull_holding_update_candidates(db_path: Path | str | None = None, *, limit: int = 500) -> tuple[Path, int]:
    target_db = initialize_research_bus(db_path)
    with _connect(target_db) as conn:
        rows = conn.execute(
            """
            SELECT candidate_id, source_system, account, candidate_type, status, quality_status,
                   content_text, attachments_json, extracted_symbols_json, source_request_id,
                   source_chat_input_id, payload_json, created_at, updated_at
            FROM holding_update_candidates
            ORDER BY updated_at DESC, created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    payload = {
        "schema": SCHEMA_VERSION,
        "exported_at": _now(),
        "source_system": "ResearchBus",
        "target_system": "AI-Research-System",
        "purpose": "行研系统读取任意聊天框上传的持仓/交易候选输入，供人工核对后再进入正式持仓。",
        "holding_update_candidates": [_row_to_payload(row) for row in rows],
    }
    path = BRIDGE_DIR / "HoldingUpdateCandidatesFromBus.json"
    _atomic_write_json(path, payload)
    return path, len(rows)


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


def _create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS system_state (
            system_name TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            root_path TEXT NOT NULL DEFAULT '',
            last_sync_at TEXT NOT NULL,
            summary_json TEXT NOT NULL DEFAULT '{}'
        );

        CREATE TABLE IF NOT EXISTS research_reports (
            report_id TEXT PRIMARY KEY,
            source_system TEXT NOT NULL,
            report_type TEXT NOT NULL DEFAULT '',
            title TEXT NOT NULL,
            report_date TEXT NOT NULL DEFAULT '',
            period TEXT NOT NULL DEFAULT '',
            path TEXT NOT NULL,
            content_hash TEXT NOT NULL DEFAULT '',
            summary TEXT NOT NULL DEFAULT '',
            symbols_json TEXT NOT NULL DEFAULT '[]',
            topics_json TEXT NOT NULL DEFAULT '[]',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS validation_tasks (
            task_id TEXT PRIMARY KEY,
            source_system TEXT NOT NULL,
            source_report_id TEXT NOT NULL DEFAULT '',
            source_report_path TEXT NOT NULL DEFAULT '',
            source_paragraph TEXT NOT NULL DEFAULT '',
            research_topic TEXT NOT NULL DEFAULT '',
            symbol TEXT NOT NULL DEFAULT '',
            market TEXT NOT NULL DEFAULT '',
            signal_to_validate TEXT NOT NULL DEFAULT '',
            sample_period TEXT NOT NULL DEFAULT '',
            cost_assumption TEXT NOT NULL DEFAULT '',
            benchmark TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT '待验证',
            validation_report_path TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS pfi_os_results (
            result_id TEXT PRIMARY KEY,
            report_path TEXT NOT NULL DEFAULT '',
            metadata_path TEXT NOT NULL DEFAULT '',
            strategy_id TEXT NOT NULL DEFAULT '',
            symbol TEXT NOT NULL DEFAULT '',
            market TEXT NOT NULL DEFAULT '',
            total_return REAL NOT NULL DEFAULT 0,
            annualized_return REAL NOT NULL DEFAULT 0,
            max_drawdown REAL NOT NULL DEFAULT 0,
            sharpe REAL NOT NULL DEFAULT 0,
            research_status TEXT NOT NULL DEFAULT '',
            decision_quality_score REAL NOT NULL DEFAULT 0,
            data_quality_status TEXT NOT NULL DEFAULT '',
            cross_validation_status TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            payload_json TEXT NOT NULL DEFAULT '{}'
        );

        CREATE TABLE IF NOT EXISTS holdings_master (
            holding_id TEXT PRIMARY KEY,
            source_system TEXT NOT NULL DEFAULT '',
            account TEXT NOT NULL DEFAULT '',
            symbol TEXT NOT NULL DEFAULT '',
            name TEXT NOT NULL DEFAULT '',
            market TEXT NOT NULL DEFAULT '',
            asset_type TEXT NOT NULL DEFAULT '',
            quantity REAL NOT NULL DEFAULT 0,
            cost_basis REAL NOT NULL DEFAULT 0,
            position_value REAL NOT NULL DEFAULT 0,
            unrealized_pnl REAL NOT NULL DEFAULT 0,
            weight REAL NOT NULL DEFAULT 0,
            as_of TEXT NOT NULL DEFAULT '',
            source_path TEXT NOT NULL DEFAULT '',
            payload_json TEXT NOT NULL DEFAULT '{}',
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS holding_symbol_mappings (
            mapping_id TEXT PRIMARY KEY,
            source_system TEXT NOT NULL DEFAULT 'PFIOS',
            holding_name TEXT NOT NULL DEFAULT '',
            holding_market TEXT NOT NULL DEFAULT '',
            original_symbol TEXT NOT NULL DEFAULT '',
            proxy_symbol TEXT NOT NULL DEFAULT '',
            proxy_name TEXT NOT NULL DEFAULT '',
            proxy_market TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT '',
            confidence TEXT NOT NULL DEFAULT '',
            reason TEXT NOT NULL DEFAULT '',
            source TEXT NOT NULL DEFAULT '',
            payload_json TEXT NOT NULL DEFAULT '{}',
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS portfolio_transactions (
            transaction_id TEXT PRIMARY KEY,
            source_system TEXT NOT NULL DEFAULT '',
            account TEXT NOT NULL DEFAULT '',
            trade_date TEXT NOT NULL DEFAULT '',
            order_time TEXT NOT NULL DEFAULT '',
            timezone TEXT NOT NULL DEFAULT '',
            symbol TEXT NOT NULL DEFAULT '',
            name TEXT NOT NULL DEFAULT '',
            market TEXT NOT NULL DEFAULT '',
            asset_type TEXT NOT NULL DEFAULT '',
            side TEXT NOT NULL DEFAULT '',
            order_type TEXT NOT NULL DEFAULT '',
            order_amount REAL NOT NULL DEFAULT 0,
            confirmed_amount REAL NOT NULL DEFAULT 0,
            confirmed_units REAL NOT NULL DEFAULT 0,
            confirmed_nav REAL NOT NULL DEFAULT 0,
            fee REAL NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT '',
            quality_status TEXT NOT NULL DEFAULT '',
            source_path TEXT NOT NULL DEFAULT '',
            evidence_frame TEXT NOT NULL DEFAULT '',
            notes TEXT NOT NULL DEFAULT '',
            payload_json TEXT NOT NULL DEFAULT '{}',
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS holding_update_candidates (
            candidate_id TEXT PRIMARY KEY,
            source_system TEXT NOT NULL DEFAULT '',
            account TEXT NOT NULL DEFAULT '',
            candidate_type TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'PendingReview',
            quality_status TEXT NOT NULL DEFAULT 'Candidate',
            content_text TEXT NOT NULL DEFAULT '',
            attachments_json TEXT NOT NULL DEFAULT '[]',
            extracted_symbols_json TEXT NOT NULL DEFAULT '[]',
            source_request_id TEXT NOT NULL DEFAULT '',
            source_chat_input_id TEXT NOT NULL DEFAULT '',
            payload_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS consumer_behavior_state (
            state_id TEXT PRIMARY KEY,
            source_system TEXT NOT NULL DEFAULT 'ConsumptionAnalysisSystem',
            db_path TEXT NOT NULL DEFAULT '',
            run_count INTEGER NOT NULL DEFAULT 0,
            transaction_count INTEGER NOT NULL DEFAULT 0,
            ledger_count INTEGER NOT NULL DEFAULT 0,
            latest_run_id TEXT NOT NULL DEFAULT '',
            latest_generated_at TEXT NOT NULL DEFAULT '',
            total_amount REAL NOT NULL DEFAULT 0,
            manual_review_count INTEGER NOT NULL DEFAULT 0,
            summary_json TEXT NOT NULL DEFAULT '{}',
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS sync_events (
            event_id TEXT PRIMARY KEY,
            event_type TEXT NOT NULL,
            source_system TEXT NOT NULL,
            target_system TEXT NOT NULL,
            status TEXT NOT NULL,
            message TEXT NOT NULL DEFAULT '',
            payload_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS independent_validation_runs (
            run_id TEXT PRIMARY KEY,
            source_system TEXT NOT NULL DEFAULT 'IndependentValidation',
            status TEXT NOT NULL DEFAULT '',
            mode TEXT NOT NULL DEFAULT '',
            manifest_path TEXT NOT NULL DEFAULT '',
            total_rows INTEGER NOT NULL DEFAULT 0,
            shard_count INTEGER NOT NULL DEFAULT 0,
            started_at TEXT NOT NULL DEFAULT '',
            completed_at TEXT NOT NULL DEFAULT '',
            output_path TEXT NOT NULL DEFAULT '',
            payload_json TEXT NOT NULL DEFAULT '{}',
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS independent_validation_shards (
            shard_id TEXT PRIMARY KEY,
            run_id TEXT NOT NULL,
            shard_index INTEGER NOT NULL DEFAULT 0,
            source_path TEXT NOT NULL DEFAULT '',
            start_row INTEGER NOT NULL DEFAULT 0,
            end_row INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT '',
            payload_json TEXT NOT NULL DEFAULT '{}',
            updated_at TEXT NOT NULL,
            FOREIGN KEY(run_id) REFERENCES independent_validation_runs(run_id)
        );

        CREATE TABLE IF NOT EXISTS bus_api_requests (
            request_id TEXT PRIMARY KEY,
            source_system TEXT NOT NULL DEFAULT '',
            target_system TEXT NOT NULL DEFAULT '',
            request_type TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'Pending',
            priority INTEGER NOT NULL DEFAULT 5,
            payload_json TEXT NOT NULL DEFAULT '{}',
            response_json TEXT NOT NULL DEFAULT '{}',
            error_message TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            processed_at TEXT NOT NULL DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS bus_chat_inputs (
            input_id TEXT PRIMARY KEY,
            source_system TEXT NOT NULL DEFAULT '',
            author TEXT NOT NULL DEFAULT '',
            channel TEXT NOT NULL DEFAULT '',
            content_text TEXT NOT NULL DEFAULT '',
            attachments_json TEXT NOT NULL DEFAULT '[]',
            classification TEXT NOT NULL DEFAULT '',
            linked_request_id TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'Pending',
            payload_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            processed_at TEXT NOT NULL DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS bus_system_outbox (
            message_id TEXT PRIMARY KEY,
            source_system TEXT NOT NULL DEFAULT '',
            target_system TEXT NOT NULL DEFAULT '',
            message_type TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'Pending',
            payload_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            delivered_at TEXT NOT NULL DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS bus_heartbeats (
            system_name TEXT PRIMARY KEY,
            status TEXT NOT NULL DEFAULT '',
            capabilities_json TEXT NOT NULL DEFAULT '[]',
            payload_json TEXT NOT NULL DEFAULT '{}',
            last_seen_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_holdings_symbol ON holdings_master(symbol, market);
        CREATE INDEX IF NOT EXISTS idx_holding_symbol_mappings_proxy ON holding_symbol_mappings(proxy_symbol, proxy_market);
        CREATE INDEX IF NOT EXISTS idx_holding_symbol_mappings_name ON holding_symbol_mappings(holding_name, status);
        CREATE INDEX IF NOT EXISTS idx_portfolio_transactions_date ON portfolio_transactions(trade_date, order_time);
        CREATE INDEX IF NOT EXISTS idx_portfolio_transactions_name ON portfolio_transactions(name, side);
        CREATE INDEX IF NOT EXISTS idx_holding_update_candidates_status ON holding_update_candidates(status, updated_at);
        """
    )


def _report_paths(*, limit: int) -> list[Path]:
    roots = [REPORTS_HOME, ARTIFACTS_HOME]
    seen: set[str] = set()
    paths: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*"), key=lambda item: item.stat().st_mtime if item.is_file() else 0, reverse=True):
            if not path.is_file() or path.suffix.lower() not in REPORT_SUFFIXES:
                continue
            key = str(path.resolve())
            if key in seen:
                continue
            seen.add(key)
            paths.append(path)
            if len(paths) >= limit:
                return paths
    return paths


def _report_payload(path: Path) -> dict[str, Any]:
    stat = path.stat()
    text = _read_report_text(path)
    content_hash = _hash_file(path)
    report_id = _stable_id("report", str(path.resolve()), content_hash)
    return {
        "report_id": report_id,
        "report_type": _report_type(path),
        "title": path.name,
        "report_date": _report_date(path),
        "period": _period(path),
        "path": str(path),
        "content_hash": content_hash,
        "summary": _summary(text, path.name),
        "symbols": _extract_symbols(text, path.name),
        "topics": _extract_topics(text, path.name),
        "text": text,
        "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
        "updated_at": _now(),
    }


def _read_report_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".md", ".txt"} and path.stat().st_size < 4_000_000:
        return path.read_text(encoding="utf-8", errors="ignore")
    if suffix == ".pdf":
        return _read_pdf_text(path)
    return ""


def _read_pdf_text(path: Path) -> str:
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        texts = []
        for page in reader.pages:
            text = page.extract_text() or ""
            if text.strip():
                texts.append(text.strip())
        return "\n".join(texts)
    except Exception:
        pass
    try:
        import fitz

        document = fitz.open(str(path))
        return "\n".join(page.get_text("text").strip() for page in document)
    except Exception:
        return ""


def _validation_tasks_from_report(payload: dict[str, Any]) -> list[dict[str, Any]]:
    text = str(payload.get("text", "") or "")
    symbols = payload.get("symbols", []) or _extract_symbols(text, str(payload.get("title", "")))
    paragraphs = _candidate_paragraphs(text)
    if not paragraphs and symbols:
        paragraphs = [f"{payload.get('title', '')} 提到 {', '.join(symbols[:6])}，需要独立验证系统和 PFIOS 校验。"]
    tasks = []
    for paragraph in paragraphs[:80]:
        paragraph_symbols = _extract_symbols(paragraph, "")
        active_symbols = paragraph_symbols or list(symbols)[:8] or [""]
        for symbol in active_symbols[:8]:
            market = _infer_market(symbol)
            task_id = _stable_id("validationTask", payload["report_id"], symbol, paragraph)
            tasks.append(
                {
                    "task_id": task_id,
                    "source_report_id": payload["report_id"],
                    "source_report_path": payload["path"],
                    "source_paragraph": paragraph[:800],
                    "research_topic": f"{payload.get('report_type', '行研报告')}：{paragraph[:80]}",
                    "symbol": symbol,
                    "market": market,
                    "signal_to_validate": paragraph[:280],
                    "sample_period": "由独立验证系统或 PFIOS 选择；建议覆盖完整市场周期。",
                    "cost_assumption": "必须披露佣金、滑点、冲击成本、汇率或申赎费用假设。",
                    "benchmark": {"CN": "沪深300", "HK": "恒生指数", "US": "标普500"}.get(market, "自定义基准"),
                    "created_at": _now(),
                    "updated_at": _now(),
                }
            )
    return tasks


def _candidate_paragraphs(text: str) -> list[str]:
    pieces = [piece.strip() for piece in re.split(r"(?:\n{2,}|[。！？!?]\s+)", text) if piece.strip()]
    candidates = []
    for piece in pieces:
        lowered = piece.lower()
        if len(piece) < 12:
            continue
        if any(keyword in lowered for keyword in VALIDATION_KEYWORDS) or _extract_symbols(piece, ""):
            candidates.append(re.sub(r"\s+", " ", piece).strip()[:900])
    return candidates


def _infer_market(symbol: str) -> str:
    text = str(symbol or "").upper().strip()
    if not text:
        return ""
    if text.endswith(".HK") or text.startswith("HK."):
        return "HK"
    if text.endswith(".SH") or text.endswith(".SZ") or text.endswith(".SS") or re.fullmatch(r"[036]\d{5}", text):
        return "CN"
    return "US"


def _upsert_system_state(conn: sqlite3.Connection, system_name: str, status: str, root_path: str, summary: dict[str, Any]) -> None:
    conn.execute(
        """
        INSERT INTO system_state(system_name, status, root_path, last_sync_at, summary_json)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(system_name) DO UPDATE SET
            status=excluded.status,
            root_path=excluded.root_path,
            last_sync_at=excluded.last_sync_at,
            summary_json=excluded.summary_json
        """,
        (system_name, status, root_path, _now(), json.dumps(summary, ensure_ascii=False, sort_keys=True)),
    )


def _record_event(conn: sqlite3.Connection, event_type: str, source_system: str, target_system: str, status: str, message: str) -> None:
    conn.execute(
        """
        INSERT INTO sync_events(event_id, event_type, source_system, target_system, status, message, payload_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (_stable_id("event", event_type, source_system, target_system, status, message, _now()), event_type, source_system, target_system, status, message, "{}", _now()),
    )


def _row_to_payload(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    for key in ["payload_json", "symbols_json", "topics_json", "summary_json"]:
        if key in payload:
            try:
                payload[key] = json.loads(payload[key])
            except (json.JSONDecodeError, TypeError):
                pass
    return payload


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _stable_id(prefix: str, *parts: object) -> str:
    raw = "\n".join(str(part) for part in parts)
    return f"{prefix}_{hashlib.sha1(raw.encode('utf-8')).hexdigest()[:20]}"


def _report_type(path: Path) -> str:
    name = path.name.lower()
    for keyword in ["盘前", "盘中", "盘后", "k线", "周报", "行业", "策略"]:
        if keyword.lower() in name:
            return keyword
    return "行研报告"


def _report_date(path: Path) -> str:
    text = " ".join([path.name, *path.parts[-4:]])
    for pattern in [r"(?<!\d)(\d{2})(\d{2})(20\d{2})(?!\d)", r"(?<!\d)(20\d{2})-(\d{2})-(\d{2})(?!\d)"]:
        match = re.search(pattern, text)
        if match and len(match.group(1)) == 2:
            day, month, year = match.groups()
            return f"{year}-{month}-{day}"
        if match:
            year, month, day = match.groups()
            return f"{year}-{month}-{day}"
    return datetime.fromtimestamp(path.stat().st_mtime).date().isoformat()


def _period(path: Path) -> str:
    for part in reversed(path.parts):
        if re.search(r"\d{4}|\d{2}\d{2}", part):
            return part
    return ""


def _summary(text: str, fallback: str) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    return compact[:360] if compact else f"已索引报告文件：{fallback}"


def _extract_symbols(text: str, fallback: str) -> list[str]:
    content = f"{text}\n{fallback}"
    symbols = set(re.findall(r"\b(?:SH|SZ)\.?\d{6}\b|\b\d{6}\.(?:SH|SZ|SS)\b|\b[036]\d{5}\b", content, flags=re.IGNORECASE))
    symbols.update(re.findall(r"\b(?:HK)\.?\d{4,5}\b|\b\d{4,5}\.HK\b", content, flags=re.IGNORECASE))
    return sorted(symbol.upper() for symbol in symbols)


def _extract_topics(text: str, fallback: str) -> list[str]:
    content = f"{text}\n{fallback}"
    topics = []
    for keyword in ["人工智能", "半导体", "银行", "黄金", "能源", "消费", "医药", "互联网", "地产", "新能源", "港股", "美股", "A股", "政策", "财报", "估值"]:
        if keyword.lower() in content.lower():
            topics.append(keyword)
    return topics


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f".{path.name}.tmp")
    temp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    temp_path.replace(path)
    return path


def _handle_ai_request(db_path: Path, request_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    if request_type in {"sync_all", "publish_ai_reports"}:
        return sync_research_bus(db_path)
    if request_type == "pull_pfi_os_results":
        path, count = pull_pfi_os_results(db_path, limit=int(payload.get("limit") or 500))
        return {"pfi_os_results_path": str(path), "pfi_os_result_count": count}
    if request_type == "pull_validation_tasks":
        path, count = pull_validation_tasks(db_path, limit=int(payload.get("limit") or 500))
        return {"validation_tasks_path": str(path), "validation_task_count": count}
    if request_type == "pull_independent_validation_runs":
        path, count = pull_independent_validation_runs(db_path, limit=int(payload.get("limit") or 500))
        return {"independent_validation_runs_path": str(path), "independent_validation_run_count": count}
    if request_type == "pull_consumer_behavior_state":
        path, count = pull_consumer_behavior_state(db_path, limit=int(payload.get("limit") or 500))
        return {"consumer_behavior_state_path": str(path), "consumer_behavior_state_count": count}
    if request_type == "pull_holdings_master":
        path, count = pull_holdings_master(db_path, limit=int(payload.get("limit") or 500))
        return {"holdings_master_path": str(path), "holdings_master_count": count}
    if request_type == "pull_holding_symbol_mappings":
        path, count = pull_holding_symbol_mappings(db_path, limit=int(payload.get("limit") or 500))
        return {"holding_symbol_mappings_path": str(path), "holding_symbol_mapping_count": count}
    if request_type == "pull_portfolio_transactions":
        path, count = pull_portfolio_transactions(db_path, limit=int(payload.get("limit") or 500))
        return {"portfolio_transactions_path": str(path), "portfolio_transaction_count": count}
    if request_type == "pull_holding_update_candidates":
        path, count = pull_holding_update_candidates(db_path, limit=int(payload.get("limit") or 500))
        return {"holding_update_candidates_path": str(path), "holding_update_candidate_count": count}
    if request_type in {"chat_general_note", "holding_update_candidate", "validation_task_from_chat"}:
        return {"status": "Recorded", "payload": payload}
    raise ValueError(f"Unsupported AI research bus request_type: {request_type}")


def _set_request_status(db_path: Path, request_id: str, status: str) -> None:
    with _connect(db_path) as conn:
        conn.execute("UPDATE bus_api_requests SET status=?, updated_at=? WHERE request_id=?", (status, _now(), request_id))


def _complete_request(db_path: Path, request_id: str, *, response: dict[str, Any], error_message: str = "") -> None:
    status = "Failed" if error_message else "Completed"
    now = _now()
    with _connect(db_path) as conn:
        conn.execute(
            """
            UPDATE bus_api_requests
            SET status=?, response_json=?, error_message=?, updated_at=?, processed_at=?
            WHERE request_id=?
            """,
            (status, json.dumps(response, ensure_ascii=False, sort_keys=True, default=str), error_message, now, now, request_id),
        )
        row = conn.execute("SELECT source_system FROM bus_api_requests WHERE request_id=?", (request_id,)).fetchone()
        target = str(row["source_system"]) if row else ""
        conn.execute(
            """
            INSERT INTO bus_system_outbox(message_id, source_system, target_system, message_type, status, payload_json, created_at, delivered_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                _stable_id("busOutbox", "AI-Research-System", target, request_id, status, now),
                "AI-Research-System",
                target,
                "ApiRequestCompleted" if not error_message else "ApiRequestFailed",
                "Pending",
                json.dumps({"request_id": request_id, "status": status, "response": response, "error_message": error_message}, ensure_ascii=False, default=str),
                now,
                "",
            ),
        )


def _heartbeat_with_conn(
    conn: sqlite3.Connection,
    system_name: str,
    *,
    status: str = "Ready",
    capabilities: list[str] | None = None,
    payload: dict[str, Any] | None = None,
) -> None:
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
        (system_name, status, json.dumps(capabilities or [], ensure_ascii=False), json.dumps(payload or {}, ensure_ascii=False), _now()),
    )


def _classify_chat_input(text: str) -> str:
    lowered = str(text or "").lower()
    scale_terms = ["百万", "千万", "亿", "million", "billion", "大数据", "数据测试", "scale test", "stress test"]
    validation_terms = ["独立验证", "independent validation", "manifest", "分片", "模拟", "校验", "rows"]
    if any(keyword in lowered for keyword in validation_terms) and any(keyword in lowered for keyword in scale_terms):
        return "independent_validation"
    if any(keyword in lowered for keyword in ["独立验证", "independent validation", "亿", "billion", "manifest", "分片"]):
        return "independent_validation"
    if any(keyword in lowered for keyword in ["持仓", "position", "holding", "仓位", "市值", "份额"]):
        return "holding_update"
    if any(keyword in lowered for keyword in ["同步", "sync", "刷新", "互通"]):
        return "sync_request"
    if any(keyword in lowered for keyword in ["验证", "回测", "pfi_os", "策略", "信号", "rsi", "macd", "均线", "估值"]):
        return "validation_task"
    return "general_note"


def _route_chat_request_type(classification: str, text: str) -> str:
    if classification == "sync_request":
        return "sync_all"
    if classification == "independent_validation":
        return "independent_validation_checksum" if _looks_like_checksum_request(text) else "independent_validation_dry_run"
    if classification == "holding_update":
        return "holding_update_candidate"
    if classification == "validation_task":
        return "validation_task_from_chat"
    return "chat_general_note"


def _chat_payload(text: str, classification: str, *, attachments: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"content_text": text, "classification": classification}
    if attachments:
        payload["attachments"] = attachments
    if classification == "independent_validation":
        payload.update(_parse_independent_validation_scale(text))
    return payload


def _normalize_chat_attachments(attachments: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    aliases = {"path", "file_path", "name", "filename", "media_type", "type", "source"}
    for raw in attachments or []:
        if not isinstance(raw, dict):
            continue
        item = {
            "path": str(raw.get("path") or raw.get("file_path") or "").strip(),
            "name": str(raw.get("name") or raw.get("filename") or "").strip(),
            "media_type": str(raw.get("media_type") or raw.get("type") or "").strip(),
            "source": str(raw.get("source") or "").strip(),
        }
        extra = {str(key): _attachment_value(value) for key, value in raw.items() if str(key) not in aliases}
        if extra:
            item["extra"] = extra
        if item["path"] or item["name"] or item["media_type"] or item["source"] or extra:
            normalized.append(item)
    return normalized


def _attachment_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, list):
        return [_attachment_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _attachment_value(item) for key, item in value.items()}
    return str(value)


def _looks_like_checksum_request(text: str) -> bool:
    lowered = str(text or "").lower()
    return any(keyword in lowered for keyword in ["checksum", "校验", "实际验证", "实际执行", "执行校验", "sha256"])


def _parse_independent_validation_scale(text: str) -> dict[str, int]:
    clean = _normalize_scale_text(text)
    synthetic_rows = _parse_total_rows(clean)
    rows_per_shard = _parse_rows_per_shard(clean)
    if synthetic_rows <= 0:
        synthetic_rows = 1_000_000_000
    if rows_per_shard <= 0:
        rows_per_shard = 100_000_000 if synthetic_rows >= 100_000_000 else 1_000_000
    return {"synthetic_rows": synthetic_rows, "rows_per_shard": rows_per_shard}


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
        multiplier = {"万": 10_000, "百万": 1_000_000, "千万": 10_000_000, "亿": 100_000_000, "亿万": 1_000_000_000}[unit]
        number = 1.0 if unit in {"百万", "千万", "亿万"} and not number_text else _parse_chinese_or_decimal_number(number_text or "1")
        candidates.append(int(number * multiplier))
    english_unit_pattern = re.compile(
        r"(?:(\d+(?:\.\d+)?|one|two|three|four|five|six|seven|eight|nine|ten|hundred)\s+)?(billion|million)"
    )
    for match in english_unit_pattern.finditer(text):
        number = _parse_english_number((match.group(1) or "1").strip())
        multiplier = 1_000_000_000 if match.group(2) == "billion" else 1_000_000
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


def _json_loads(value: object, default: Any) -> Any:
    try:
        return json.loads(str(value or ""))
    except json.JSONDecodeError:
        return default


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")
